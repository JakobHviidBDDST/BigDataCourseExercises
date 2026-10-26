#!/usr/bin/env python3
"""
Exercise 2 - Tag incidents with the micro-LLM (terminal output).

You do NOT have to write any Python for this exercise: this script is
complete and runnable as given. Your single task (TODO student 2.1) is to
write the SYSTEM_PROMPT below.

Why that is the whole exercise: llama.cpp's guided decoding already
guarantees the model returns schema-valid JSON - but a schema only defines
the SHAPE of the answer, not its semantics. A 0.5B model only knows that a
"log about a rollout" is category=Deployment or that the first service
mentioned in a log is the reporting one if your system prompt says so.

Loop: write the prompt -> run -> inspect the table -> refine -> repeat.
When you are happy with your result, open ../solution/task2_tag_terminal.py,
compare its SYSTEM_PROMPT with yours and run it to compare the tag tables.

Run (interactive pod, llama.cpp deployed from ../k8s/llama-cpp.yaml):
    python3 task2_tag_terminal.py
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_LLAMA_URL = os.environ.get("LLAMA_URL", "http://llama-cpp:8000")
DEFAULT_MODEL = os.environ.get("LLAMA_MODEL", "qwen2.5-0.5b-instruct-q8_0.gguf")
DEFAULT_INPUT = Path(__file__).resolve().parent.parent / "data" / "sample_incidents.jsonl"

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
        "source_service": {"type": "string", "enum": SERVICES,
                           "description": "Service reporting the incident"},
        "target_dependency": {
            "type": "string",
            "enum": SERVICES + ["none"],
            "description": "Dependency the source failed against, or 'none'",
        },
    },
    "required": ["category", "severity", "source_service", "target_dependency"],
    "additionalProperties": False,
}

# TODO(student 2.1): replace this placeholder with YOUR system prompt.
# Tell the model how to decide the value of each field:
#   - category: what kind of problem belongs in Network / Database / Auth / Deployment / Memory?
#   - severity: what warrants LOW vs MEDIUM vs CRITICAL?
#   - incident logs mention many service names: what rule identifies the
#     reporting service (source_service) vs the dependency that failed
#     (target_dependency)? When should target_dependency be "none"?
# There is no single right answer - grade yourself by the tag table it
# produces, then compare with the solution's prompt afterwards.
SYSTEM_PROMPT = "You are Classify the incident log."

def chat_completion(
    llama_url: str,
    model: str,
    messages: list,
    max_tokens: int = 160,
    temperature: float = 0.0,
    response_format: dict = None,
    timeout: int = 180,
) -> str:
    """One call to the OpenAI-compatible /v1/chat/completions endpoint."""
    url = llama_url.rstrip("/") + "/v1/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if response_format is not None:
        payload["response_format"] = response_format
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"]


def validate_tags(tags: dict) -> dict:
    if tags.get("category") not in CATEGORIES:
        raise ValueError(f"invalid category: {tags.get('category')!r}")
    if tags.get("severity") not in SEVERITIES:
        raise ValueError(f"invalid severity: {tags.get('severity')!r}")
    for key in ("source_service", "target_dependency"):
        if not isinstance(tags.get(key), str) or not tags[key]:
            raise ValueError(f"missing {key}")
    return tags


def tag_incident(llama_url: str, model: str, raw_text: str) -> dict:
    """Ask the LLM for the tags of ONE incident log."""
    content = chat_completion(
        llama_url=llama_url,
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": raw_text[:4000]},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "incident_tags", "schema": TAG_SCHEMA},
        },
    )
    return validate_tags(json.loads(content))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--llama-url", default=DEFAULT_LLAMA_URL)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--limit", type=int, default=0, help="tag only the first N records (0 = all)")
    args = ap.parse_args()

    records = [json.loads(l) for l in args.input.read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.limit:
        records = records[: args.limit]

    print(f"tagging {len(records)} incidents via {args.llama_url} (model={args.model})\n")
    header = f"{'ticket_id':<10} {'category':<10} {'severity':<9} {'source_service':<18} target_dependency"
    print(header)
    print("-" * len(header))

    failures = 0
    for rec in records:
        try:
            tags = tag_incident(args.llama_url, args.model, rec["raw_text"])
        except (urllib.error.URLError, json.JSONDecodeError, ValueError) as exc:
            failures += 1
            print(f"{rec['ticket_id']:<10} ERROR: {exc}", file=sys.stderr)
            continue
        print(
            f"{rec['ticket_id']:<10} {tags['category']:<10} {tags['severity']:<9} "
            f"{tags['source_service']:<18} {tags['target_dependency']}"
        )

    print(f"\ndone: {len(records) - failures} tagged, {failures} failed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
