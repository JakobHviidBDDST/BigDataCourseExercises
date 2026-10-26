#!/usr/bin/env python3
"""
Exercise 3a - Publish the raw incident dataset to Kafka (`raw-incidents`).

This script is complete and runs as given - there is no Python for you to
write. Your task is to run it and watch the tickets arrive on the topic.

Conventions (same as lecture 03):
  * bootstrap server `kafka:9092` (Bitnami helm release `kafka`)
  * one logical key per record: the ticket id -> all messages with the same
    ticket land on the same partition
  * value: the raw JSON line, compact-encoded

Topic config recommended in the Redpanda console: 3 partitions, RF 3 (or RF 1
on the shared cluster), retention ~7 days. The script also *tries* to create
the topic via the admin API and simply continues if that is not permitted.

Run inside the interactive pod:
    python3 task3_produce_raw.py
"""

import argparse
import json
import os
from pathlib import Path

from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic

DEFAULT_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
DEFAULT_TOPIC = os.environ.get("RAW_TOPIC", "raw-incidents")
DEFAULT_INPUT = Path(__file__).resolve().parent.parent / "data" / "sample_incidents.jsonl"
ENCODING = "utf-8"


def try_create_topic(bootstrap: str, topic: str, partitions: int = 3, replication: int = 1) -> None:
    """Best-effort topic creation (students may have created it in Redpanda)."""
    try:
        admin = KafkaAdminClient(bootstrap_servers=bootstrap)
        admin.create_topics([NewTopic(topic, num_partitions=partitions, replication_factor=replication)])
        admin.close()
        print(f"created topic {topic} ({partitions} partitions)")
    except Exception as exc:
        print(f"skip topic creation ({exc.__class__.__name__})")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--bootstrap", default=DEFAULT_BOOTSTRAP)
    ap.add_argument("--topic", default=DEFAULT_TOPIC)
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = ap.parse_args()

    try_create_topic(args.bootstrap, args.topic)

    producer = KafkaProducer(bootstrap_servers=args.bootstrap)
    count = 0
    for line in args.input.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        future = producer.send(
            topic=args.topic,
            key=record["ticket_id"].encode(ENCODING),
            value=json.dumps(record).encode(ENCODING),
        )
        count += 1
        if count % 10 == 0:
            print(f"sent {count} records...")
    producer.flush(timeout=30)
    producer.close()
    print(f"produced {count} records to topic '{args.topic}' on {args.bootstrap}")


if __name__ == "__main__":
    main()
