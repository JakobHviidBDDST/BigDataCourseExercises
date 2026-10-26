#!/usr/bin/env python3
"""
Synthetic IT-incident dataset generator for Exercise 2-5.

Generates 50 semi-structured incident records (JSON Lines):

    {"ticket_id": "INC-001", "timestamp": "2026-10-18T03:41:00Z", "raw_text": "..."}

`raw_text` intentionally looks like a real ticket dump: log lines, stack
traces, metrics, outage chatter across interconnected micro-services
(checkout-service, auth-service, payment-gateway, redis-cluster-02,
postgres-orders, kafka-broker-01).

PLANTED CAUSAL CHAIN (the payload that makes Exercise 5 deterministic)
-----------------------------------------------------------------------
    INC-017  checkout-service  -> auth-service        CRITICAL  (504 timeouts)
    INC-043  auth-service      -> redis-cluster-02    MEDIUM    (pool exhausted)
    INC-042  redis-cluster-02  -> none                CRITICAL  (host OOM kill)

    * INC-042 never mentions "checkout-service" or "504" (pure redis-side
      logs), so a vector search for "checkout-service ... 504 ... root cause"
      cannot find it.
    * INC-043 mentions redis but never "checkout".
    * Three decoy tickets (INC-005, INC-023, INC-031) DO mention
      "checkout-service" without involving auth or redis, so they crowd out
      the top-K of a vector-only retrieval.

    => Vector-only RAG retrieves INC-017 + decoys but MISSES the root cause.
    => Hybrid Graph-RAG traverses checkout -> auth -> redis and FINDS INC-042.

The generator is fully deterministic (fixed seed, fixed planted texts), so
regenerating the file reproduces it byte-for-byte (see --check).
"""

import argparse
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

SEED = 42
OUTPUT = Path(__file__).parent / "sample_incidents.jsonl"

SERVICES = [
    "checkout-service",
    "auth-service",
    "payment-gateway",
    "redis-cluster-02",
    "postgres-orders",
    "kafka-broker-01",
]

# Reserved ticket ids for the planted chain + decoys (never reassigned).
PLANTED_IDS = {"INC-017", "INC-042", "INC-043"}
DECOY_IDS = {"INC-005", "INC-023", "INC-031"}
RESERVED = PLANTED_IDS | DECOY_IDS

# ---------------------------------------------------------------------------
# Planted multi-hop causal chain
# ---------------------------------------------------------------------------
PLANTED = [
    {
        "ticket_id": "INC-017",
        "timestamp": "2026-10-21T02:41:03Z",
        "raw_text": "\n".join(
            [
                "ERROR [checkout-service] 2026-10-21T02:41:03Z - 504 Gateway Timeout returned to client: token verification request to upstream auth-service exceeded deadline (10000ms), retry 1/3 failed",
                "WARN [checkout-service] circuit breaker OPEN after 17 consecutive failed calls to upstream auth-service, failing closed for /api/v2/checkout",
                'ERROR nginx[2211]: upstream timed out (110: Connection timed out) while reading response header, request: POST /api/v2/checkout HTTP/1.1, upstream: "http://auth-service:8080/token/verify", host: "shop.example.com", status 504',
                "INFO [checkout-service] user-facing error rate 96% since 02:38Z, on-call paged, checkout flow effectively down",
            ]
        ),
        # ground truth (not part of the emitted record): category=Auth, severity=CRITICAL
    },
    {
        "ticket_id": "INC-042",
        "timestamp": "2026-10-21T01:58:12Z",
        "raw_text": "\n".join(
            [
                "CRITICAL [redis-cluster-02] 2026-10-21T01:58:12Z - used_memory 6342844416 reached maxmemory 6442450944, eviction policy allkeys-lru evicting keys at 12k/s",
                "ERROR kernel: Out of memory: Killed process 8841 (redis-server) total-vm:6980212kB, anon-rss:6144320kB, oom_score_adj=100",
                "WARN [redis-cluster-02] replication backlog overflow, 2 replicas lagging 45s+, keyspace hit rate dropped to 31%",
                "INFO [redis-cluster-02] process restarted after SIGKILL, AOF replay 2.1GB completed in 96s, ephemeral session keys lost",
            ]
        ),
        # ground truth: category=Memory, severity=CRITICAL, no dependency edge
    },
    {
        "ticket_id": "INC-043",
        "timestamp": "2026-10-21T02:12:47Z",
        "raw_text": "\n".join(
            [
                "WARN [auth-service] 2026-10-21T02:12:47Z - request latency spike: p99 latency 4200ms (SLA 250ms), token-verify queue depth 512",
                "ERROR [auth-service] redis connection pool exhausted (32/32) for session store redis-cluster-02:6379, connection backlog growing",
                "WARN [auth-service] GET session:* against redis-cluster-02:6379 took 3100ms, MGET commands queuing, eviction storm suspected upstream",
            ]
        ),
        # ground truth: category=Auth, severity=MEDIUM
    },
]

# ---------------------------------------------------------------------------
# Decoys: mention checkout-service but are unrelated to the causal chain
# ---------------------------------------------------------------------------
DECOYS = [
    {
        "ticket_id": "INC-005",
        "timestamp": "2026-10-19T14:05:44Z",
        "raw_text": "\n".join(
            [
                "WARN [netmon] 14% TCP retransmission rate on flow checkout-service -> payment-gateway:7443, NIC CRC errors on switch port sw03-7",
                "WARN [checkout-service] payment calls degraded: p95 latency 850ms, mTLS handshakes retransmitting, throughput down 40%",
                "INFO [netmon] link sw03-sw07 flapping 6x in 10m, ticket opened to network team (unrelated to app releases)",
            ]
        ),
    },
    {
        "ticket_id": "INC-023",
        "timestamp": "2026-10-20T09:30:10Z",
        "raw_text": "\n".join(
            [
                "INFO [deploy] checkout-service v1.42.0 rollout complete, canary 10% -> 100%, error budget untouched",
                "INFO [deploy] canary metrics healthy: p99 118ms, error rate 0.02%, no rollback triggered",
            ]
        ),
    },
    {
        "ticket_id": "INC-031",
        "timestamp": "2026-10-20T19:48:31Z",
        "raw_text": "\n".join(
            [
                "WARN [checkout-service] slow query: SELECT * FROM orders WHERE customer_id=? took 2800ms on postgres-orders (seq scan, index orders_customer_idx missing)",
                "INFO [dba] index migration CONCURRENTLY CREATE INDEX orders_customer_idx scheduled, backlog of 3 tickets similar",
            ]
        ),
    },
]

# ---------------------------------------------------------------------------
# Filler incident templates. {s} = reporting service (mentioned FIRST),
# {t} = dependency service (mentioned second, if the template has one).
# ---------------------------------------------------------------------------
FILLER_TEMPLATES = [
    # (template lines, has_dependency, intended severity)
    (
        [
            "WARN [netmon] connection refused from {s} to {t}:3100, SYN retries 4, packet loss 11% on uplink sw03-sw07",
            "INFO [sre-bot] auto-reopened network ticket, interface error counters incrementing on spine switch",
        ],
        True,
        "MEDIUM",
    ),
    (
        [
            "ERROR [dns] {s} failed to resolve {t}.svc.cluster.local (SERVFAIL x3, 2100ms), stale cache entry used",
            "WARN [sre-bot] node-local dns cache pod restarting, watch for cascading resolution latency",
        ],
        True,
        "MEDIUM",
    ),
    (
        "WARN [postgres-orders] deadlock detected for transaction from {s}, statement rolled back, retrying txn (deadlock_rate 4/min)",
        None,
        "MEDIUM",
    ),
    (
        [
            "WARN [db-probe] {s} connection pool saturation while querying {t} primary (active 98/100), slow query 1900ms",
            "INFO [db-probe] long-running transactions listed in pg_stat_activity, oldest 42s",
        ],
        True,
        "MEDIUM",
    ),
    (
        "WARN [postgres-orders] autovacuum on orders_main deferred 14h, dead tuple ratio 31%, vacuum cost limit throttling against {s} traffic",
        None,
        "LOW",
    ),
    (
        [
            "WARN [iam-sidecar] {s} received HTTP 401 from identity provider: JWT signature mismatch, clock skew suspected (drift 3.2s)",
            "INFO [iam-sidecar] token refresh retried, request served after fallback to cached JWKS key id k-2026-10",
        ],
        True,
        "MEDIUM",
    ),
    (
        "WARN [auth-audit] {s} login attempts with revoked audience claim blocked 27x in 5m, client secret possibly stale in legacy SDK",
        None,
        "LOW",
    ),
    (
        [
            "ERROR [argocd] {s} rollout blocked: imagePullBackOff for sidecar proxy v2.3.1 from registry.internal (401 unauthorized, pull secret expired)",
            "INFO [argocd] previous revision kept serving traffic, rollback staged automatically",
        ],
        True,
        "MEDIUM",
    ),
    (
        "INFO [argocd] {s} config map hot-reload applied, 4/4 pods restarted sequentially, readiness green",
        None,
        "LOW",
    ),
    (
        [
            "WARN [kubelet] {s} container at 92% of memory limit while streaming batches from {t}, GC overhead elevated (full GC 900ms)",
            "WARN [kubelet] minor GC frequency up 6x, heap fragmentation suspected, ticket filed to owning team",
        ],
        True,
        "MEDIUM",
    ),
    (
        [
            "WARN [kafka-broker-01] consumer group {s} rebalancing: member left group (processing slot starvation on partition 2), lag 120k messages",
            "INFO [kafka-broker-01] group stabilized after 12s, offsets committed, fetch queue drained",
        ],
        True,
        "MEDIUM",
    ),
    (
        "INFO [capacity] nightly batch from {s} completed, backlog drained in 22m, disk headroom on data volume 38%",
        None,
        "LOW",
    ),
]


def make_filler(rng: random.Random) -> dict:
    """Create one filler incident with a plausible (source, target) pair."""
    lines, has_dep, severity = rng.choice(FILLER_TEMPLATES)

    source = rng.choice(SERVICES)
    # Keep the planted chain unique: redis-cluster-02 only appears as source in
    # INC-042, and auth-service only feeds redis-cluster-02 in INC-043.
    while source == "redis-cluster-02":
        source = rng.choice(SERVICES)

    target = None
    if has_dep:
        candidates = [s for s in SERVICES if s != source]
        if source == "auth-service":
            candidates = [c for c in candidates if c != "redis-cluster-02"]
        if source == "checkout-service":
            candidates = [c for c in candidates if c != "auth-service"]
        target = rng.choice(candidates)

    def render(text: str) -> str:
        text = text.replace("{s}", source)
        return text if target is None else text.replace("{t}", target)

    if isinstance(lines, str):
        lines = [lines]
    text = "\n".join(render(l) for l in lines)
    if target is not None:
        text += f"\nINFO [topology] reported dependency hop: {source} -> {target}"
    return {
        "_severity": severity,
        "_source": source,
        "_target": target or "none",
        "raw_text": text,
    }


def generate() -> list[dict]:
    """Return the deterministic 50-record dataset (planted + decoys + fillers)."""
    rng = random.Random(SEED)

    reserved = RESERVED
    specials = PLANTED + DECOYS

    # Filler timestamps spread over Oct 18 - Oct 21 2026.
    base = datetime(2026, 10, 18, 0, 0, 0, tzinfo=timezone.utc)
    fillers = []
    for _ in range(50 - len(specials)):
        f = make_filler(rng)
        ts = base + timedelta(minutes=rng.randrange(0, 3 * 24 * 60))
        f["timestamp"] = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        fillers.append(f)

    all_records = [
        {
            "ticket_id": p["ticket_id"],
            "timestamp": p["timestamp"],
            "raw_text": p["raw_text"],
        }
        for p in specials
    ] + [
        {"ticket_id": None, "timestamp": f["timestamp"], "raw_text": f["raw_text"]}
        for f in fillers
    ]

    # Stable order by timestamp, then assign free ids in order to fillers.
    all_records.sort(key=lambda r: r["timestamp"])
    free_ids = [f"INC-{n:03d}" for n in range(1, 51) if f"INC-{n:03d}" not in reserved]
    fi = 0
    for r in all_records:
        if r["ticket_id"] is None:
            r["ticket_id"] = free_ids[fi]
            fi += 1

    # Determinism check: sort by ticket id for a stable file.
    all_records.sort(key=lambda r: r["ticket_id"])
    assert len(all_records) == 50, "dataset must contain exactly 50 records"
    return all_records


def write_dataset(path: Path) -> None:
    records = generate()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(records)} records -> {path}")


def check(path: Path) -> int:
    """Validate the dataset invariants used by the exercises. Returns exit code."""
    errors = []
    records = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()]

    by_id = {r["ticket_id"]: r for r in records}
    if len(records) != 50:
        errors.append(f"expected 50 records, found {len(records)}")
    if len(by_id) != len(records):
        errors.append("duplicate ticket_ids")
    for r in records:
        if set(r) != {"ticket_id", "timestamp", "raw_text"}:
            errors.append(f"{r.get('ticket_id')}: unexpected field set {set(r)}")

    # Planted chain present with its signatures.
    chain_checks = {
        "INC-017": ["504", "checkout-service", "auth-service"],
        "INC-043": ["auth-service", "redis-cluster-02", "pool exhausted"],
        "INC-042": ["redis-cluster-02", "Out of memory"],
    }
    for tid, needles in chain_checks.items():
        text = by_id.get(tid, {}).get("raw_text", "")
        for needle in needles:
            if needle not in text:
                errors.append(f"{tid}: expected signature '{needle}' missing")

    # The root-cause ticket must NOT leak the query terms (that's the lesson).
    for forbidden in ("checkout", "504", "auth-service"):
        if forbidden in by_id["INC-042"]["raw_text"]:
            errors.append(f"INC-042 must not mention '{forbidden}'")
    for forbidden in ("checkout", "504"):
        if forbidden in by_id["INC-043"]["raw_text"]:
            errors.append(f"INC-043 must not mention '{forbidden}'")

    # Decoys mention checkout-service but never auth/redis.
    for tid in sorted(DECOY_IDS):
        text = by_id[tid]["raw_text"]
        if "checkout-service" not in text:
            errors.append(f"decoy {tid} must mention checkout-service")
        if "auth-service" in text or "redis-cluster-02" in text:
            errors.append(f"decoy {tid} must not touch auth-service/redis-cluster-02")

    # Filler hygiene: no filler may create the planted edges or leak 504/OOM.
    planted_edges = {("checkout-service", "auth-service"), ("auth-service", "redis-cluster-02")}
    for r in records:
        if r["ticket_id"] in RESERVED:
            continue
        text = r["raw_text"]
        if "504" in text or "Out of memory" in text:
            errors.append(f"filler {r['ticket_id']} contains a chain keyword")
        for src, tgt in planted_edges:
            if f"hop: {src} -> {tgt}" in text:
                errors.append(f"filler {r['ticket_id']} duplicates planted edge {src}->{tgt}")

    if errors:
        print("DATASET CHECK FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"dataset check OK: {len(records)} records, planted chain + decoys intact")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--output", type=Path, default=OUTPUT)
    ap.add_argument("--check", action="store_true", help="validate the existing file")
    args = ap.parse_args()

    if args.check:
        sys.exit(check(args.output))
    write_dataset(args.output)
    sys.exit(check(args.output))


if __name__ == "__main__":
    main()
