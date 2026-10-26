#!/usr/bin/env python3
"""
Exercise 3b - Stream processor: Kafka `raw-incidents` -> llama.cpp -> Kafka `enriched-incidents`.

This script is complete and runs as given - there is no Python for you to
write. Your task is to run it and understand WHY it is configured the way
it is: the two lessons below explain every non-default setting.

Two constrained-resource lessons are baked into this script:

1. Kafka rebalance timeouts vs. slow CPU inference
   A 0.5B model on 2 vCPUs needs ~1-3 s per request. If we polled 500 records
   (the `max_poll_records` default is 500) and then spent minutes calling the
   LLM, the broker would evict us from the consumer group long before the
   next poll: `max.poll.interval.ms` (default 300000) would be exceeded and
   the group would rebalance endlessly. Counter-measures below:
     * max_poll_records=4       -> a "batch" is only 4 messages of work
     * max_poll_interval_ms=300000 -> generous 5 min between polls
     * enable_auto_commit=False + commit AFTER producing the enriched record
       -> at-least-once semantics: a crash re-processes the batch, nothing lost.

2. Parallel slots (llama.cpp's concurrency feature)
   llama-server serves requests through a fixed number of context slots; with
   --parallel 4 (set in k8s/llama-cpp.yaml) it decodes up to 4 requests at the
   same time. One-at-a-time HTTP calls leave the other slots idle. We keep a
   small window of messages (the micro-batch polled from Kafka) and fire them
   at the server CONCURRENTLY (thread pool of 4), matching the slot count.
   Same wall-clock budget -> several times the throughput.

Run inside the interactive pod:
    python3 task3_kafka_llama_enricher.py            # runs until Ctrl-C
    python3 task3_kafka_llama_enricher.py --max-messages 50 --idle-timeout 20
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from kafka import KafkaConsumer, KafkaProducer

DEFAULT_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
DEFAULT_LLAMA_URL = os.environ.get("LLAMA_URL", "http://llama-cpp:8000")
DEFAULT_MODEL = os.environ.get("LLAMA_MODEL", "qwen2.5-0.5b-instruct-q8_0.gguf")
RAW_TOPIC = os.environ.get("RAW_TOPIC", "raw-incidents")
ENRICHED_TOPIC = os.environ.get("ENRICHED_TOPIC", "enriched-incidents")
ENCODING = "utf-8"

CATEGORIES = ["Network", "Database", "Auth", "Deployment", "Memory"]
SEVERITIES = ["LOW", "MEDIUM", "CRITICAL"]
SERVICES = [
    "checkout-service",
    "auth-service",
    "payment-gateway",
    "redis-cluster-02",
    "postgres-orders",
    "kafka-broker-01",
    "argocd",
]
TAG_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": CATEGORIES},
        "severity": {"type": "string", "enum": SEVERITIES},
        "source_service": {"type": "string", "enum": SERVICES},
        "target_dependency": {"type": "string", "enum": SERVICES + ["none"]},
    },
    "required": ["category", "severity", "source_service", "target_dependency"],
    "additionalProperties": False,
}
SYSTEM_PROMPT = (
    "You are an expert SRE triage assistant. Classify the incident log provided "
    "by the user. Rules: source_service is the service that reports the problem "
    "(the service that appears first in the logs); target_dependency is the "
    "service or component it was calling or failing against, or 'none' if no "
    "dependency is involved. Respond with JSON only."
)


def tag_text(llama_url: str, model: str, raw_text: str) -> dict:
    """Blocking LLM call (run inside the thread pool -> concurrent on server)."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": raw_text[:4000]},
        ],
        "max_tokens": 160,
        "temperature": 0.0,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "incident_tags", "schema": TAG_SCHEMA},
        },
    }
    req = urllib.request.Request(
        llama_url.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(payload).encode(ENCODING),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        body = json.loads(resp.read().decode(ENCODING))
    return json.loads(body["choices"][0]["message"]["content"])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--bootstrap", default=DEFAULT_BOOTSTRAP)
    ap.add_argument("--from-topic", default=RAW_TOPIC)
    ap.add_argument("--to-topic", default=ENRICHED_TOPIC)
    ap.add_argument("--group", default="llm-enricher")
    ap.add_argument("--llama-url", default=DEFAULT_LLAMA_URL)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--concurrency", type=int, default=4, help="in-flight LLM requests (micro-batch)")
    ap.add_argument("--max-messages", type=int, default=0, help="exit after N enrichments (0 = until idle/Ctrl-C)")
    ap.add_argument("--idle-timeout", type=float, default=60, help="exit after this many idle seconds")
    args = ap.parse_args()

    consumer = KafkaConsumer(
        args.from_topic,
        bootstrap_servers=args.bootstrap,
        group_id=args.group,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        max_poll_records=args.concurrency,
        max_poll_interval_ms=300_000,
        value_deserializer=lambda m: json.loads(m.decode(ENCODING)),
        key_deserializer=lambda k: k.decode(ENCODING) if k else None,
    )
    producer = KafkaProducer(bootstrap_servers=args.bootstrap)
    pool = ThreadPoolExecutor(max_workers=args.concurrency)

    print(f"consuming '{args.from_topic}' -> '{args.to_topic}' via {args.llama_url} "
          f"(micro-batch={args.concurrency}, max_poll_interval=300s)")

    processed = 0
    last_activity = time.monotonic()
    try:
        while True:
            batches = consumer.poll(timeout_ms=1000)
            if not batches:
                if time.monotonic() - last_activity > args.idle_timeout:
                    print("idle timeout reached, exiting cleanly")
                    break
                continue
            records = [m for msgs in batches.values() for m in msgs]
            last_activity = time.monotonic()

            started = time.monotonic()
            futures = [
                pool.submit(tag_text, args.llama_url, args.model, r.value["raw_text"])
                for r in records
            ]
            for record, future in zip(records, futures):
                event = dict(record.value)
                try:
                    tags = future.result()
                    latency_ms = int((time.monotonic() - started) * 1000 / len(records))
                    event["llm"] = {
                        **tags,
                        "model": args.model,
                        "latency_ms": latency_ms,
                        "enriched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    }
                    edge = f"{tags['source_service']} -> {tags['target_dependency']}"
                    print(f"[batch] {record.key}: {tags['severity']:<8} {tags['category']:<10} {edge}")
                except (urllib.error.URLError, json.JSONDecodeError, ValueError, RuntimeError) as exc:
                    event["llm"] = {"error": str(exc)[:300]}
                    print(f"[batch] {record.key}: LLM FAILED ({exc})", file=sys.stderr)
                producer.send(topic=args.to_topic, key=record.key.encode(ENCODING),
                              value=json.dumps(event).encode(ENCODING))
            producer.flush(timeout=30)
            consumer.commit()
            processed += len(records)
            print(f"  committed, {processed} records enriched "
                  f"({time.monotonic() - started:.1f}s for {len(records)} messages)")
            if args.max_messages and processed >= args.max_messages:
                print("max messages reached, exiting cleanly")
                break
    except KeyboardInterrupt:
        print("interrupted")
    finally:
        pool.shutdown(wait=False)
        producer.close()
        consumer.close()


if __name__ == "__main__":
    main()
