#!/usr/bin/env python3
"""
Exercise 5 - Hybrid retrieval: Vector RAG vs. Hybrid Graph-RAG, side by side.

This script is complete and runs as given - there is no Python for you to
write. Your task is to run the experiments below and explain why the two
answers differ.

Pipeline for one user question:

  5a Vector RAG    embed the query with the SAME bi-encoder as Exercise 4 and
                   ask Qdrant (or the local vector mirror) for the top-K
                   semantically similar incidents.
                   -> finds INC-017 (checkout-service 504 on auth-service)
                      but MISSES INC-042 (the redis-cluster-02 OOM), because
                      that ticket never mentions checkout-service.

  5b Graph-RAG     take the service nodes from the vector hits and follow
                   DEPENDENCY EDGES (failing service -> its failed dependency)
                   in the graph built by Exercise 4, 1-2 hops deep:
                   checkout-service -> auth-service -> redis-cluster-02,
                   recovering the linked CRITICAL incidents.

  5c Generation    send both contexts to the llama.cpp CPU endpoint and print the
                   Vector-Only answer vs. the Hybrid answer side by side.

Cluster usage (interactive pod):
    python3 task5_hybrid_rag_query.py --query "Why is checkout-service returning 504 timeouts?"
"""

import argparse
import glob
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from embeddings import embed

DEFAULT_LLAMA_URL = os.environ.get("LLAMA_URL", "http://llama-cpp:8000")
DEFAULT_MODEL = os.environ.get("LLAMA_MODEL", "qwen2.5-0.5b-instruct-q8_0.gguf")
DEFAULT_QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
COLLECTION = os.environ.get("QDRANT_COLLECTION", "incidents")
DEFAULT_QUERY = (
    "Why is checkout-service returning 504 timeouts, and what underlying "
    "infrastructure component is the root cause?"
)
SEVERITY_RANK = {"CRITICAL": 0, "MEDIUM": 1, "LOW": 2}


# ---------------------------------------------------------------------------
# Data loading: Qdrant REST, local JSON mirrors, or HDFS via WebHDFS
# ---------------------------------------------------------------------------
def rest(url: str, method: str = "POST", body=None):
    req = urllib.request.Request(
        url, data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json"}, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode() or "{}")


def webhdfs_read_dir(json_dir: str) -> list:
    """Read all part-*.json of a HDFS directory through the NameNode WebHDFS API."""
    parsed = urllib.parse.urlparse(json_dir)
    webhdfs = f"http://{parsed.hostname}:9870/webhdfs/v1{parsed.path}?op=LISTSTATUS"
    listing = rest(webhdfs, "GET")["FileStatuses"]["FileStatus"]
    rows = []
    for entry in listing:
        if entry["type"] != "FILE" or entry["pathSuffix"].startswith("_"):
            continue
        open_url = (f"http://{parsed.hostname}:9870/webhdfs/v1{parsed.path}/"
                    f"{entry['pathSuffix']}?op=OPEN")
        with urllib.request.urlopen(open_url, timeout=60) as resp:
            rows += [json.loads(l) for l in resp.read().decode().splitlines() if l.strip()]
    return rows


def load_json_rows(local_dir: str, hdfs_dir: str = None) -> list:
    p = Path(local_dir)
    files = sorted(glob.glob(str(p / "*.json"))) + sorted(glob.glob(str(p / "*.jsonl")))
    if files:
        rows = []
        for f in files:
            rows += [json.loads(l) for l in Path(f).read_text(encoding="utf-8").splitlines() if l.strip()]
        return rows
    if hdfs_dir:
        return webhdfs_read_dir(hdfs_dir)
    raise FileNotFoundError(f"no json part files in {local_dir} (and no HDFS fallback given)")


def load_incidents_from_qdrant(base: str) -> list:
    """Scroll the whole (small, course-sized) collection to get graph payloads."""
    rows, offset = [], None
    while True:
        body = {"limit": 256, "with_payload": True, "with_vector": False}
        if offset:
            body["offset"] = offset
        result = rest(f"{base.rstrip('/')}/collections/{COLLECTION}/points/scroll", "POST", body)["result"]
        rows += [p["payload"] for p in result["points"]]
        offset = result.get("next_page_offset")
        if not offset:
            return rows


def vector_search_qdrant(base: str, vector: list, k: int) -> list:
    result = rest(
        f"{base.rstrip('/')}/collections/{COLLECTION}/points/search", "POST",
        {"vector": vector, "limit": k, "with_payload": True},
    )["result"]
    return [{**hit["payload"], "score": hit["score"]} for hit in result]


def vector_search_files(rows: list, vector: list, k: int) -> list:
    scored = [
        {**r, "score": sum(a * b for a, b in zip(vector, r["embedding"]))}
        for r in rows
    ]
    scored.sort(key=lambda r: -r["score"])
    return scored[:k]


# ---------------------------------------------------------------------------
# Graph-RAG: BFS over the service-dependency graph
# ---------------------------------------------------------------------------
def norm_service(name: str) -> str:
    """Canonical service name for graph traversal.

    A real micro-LLM sometimes emits FQDN variants like
    "postgres-orders.svc.cluster.local" or "redis-cluster-02:6379"; without
    stripping the domain suffix / port these become separate graph nodes and
    dependency chains silently break.
    """
    return (name or "").strip().lower().split(".")[0].split(":")[0]


def graph_expand(all_incidents: list, seeds: list, hops: int) -> list:
    """BFS along DEPENDENCY EDGES (directed, causally correct).

    The frontier holds services known to be failing (both endpoints of the
    seed tickets: the reporter AND the dependency it failed against). A ticket
    is discovered when its REPORTER (source_service) is in the frontier, and
    its target_dependency - the failing dependency - joins the next frontier.
    That walks the real RCA chain: "my dependency is failing, and ITS
    dependency is failing" (checkout-service -> auth-service -> redis).

    Expanding undirectionally instead would make hop 1 swallow the whole
    7-service graph (vector seeds already cover most of it), so hop 2 - where
    the root cause INC-042 lives - would never exist.

    Traversal always walks ALL incidents (the frontier grows through the
    MEDIUM INC-043 to reach redis); callers filter which of the discovered
    tickets enter the LLM context via min_severity/graph_limit.
    """
    frontier = set()
    for hit in seeds:
        frontier.add(norm_service(hit["source_service"]))
        if hit.get("target_dependency") and hit["target_dependency"] != "none":
            frontier.add(norm_service(hit["target_dependency"]))
    seen = {hit["ticket_id"] for hit in seeds}
    discovered = []

    for hop in range(1, hops + 1):
        new_frontier = set()
        for inc in all_incidents:
            if inc["ticket_id"] in seen:
                continue
            src = norm_service(inc.get("source_service"))
            tgt = norm_service(inc.get("target_dependency")) or "none"
            if src in frontier:
                seen.add(inc["ticket_id"])
                discovered.append({**inc, "_hop": hop, "_via": src})
                if tgt != "none":
                    new_frontier.add(tgt)
        frontier = new_frontier
        if not frontier:
            break
    return discovered


def fmt_row(inc: dict, score=None, mark="") -> str:
    sev = inc.get("severity", "?")
    edge = f"{inc.get('source_service', '?')} -> {inc.get('target_dependency', 'none')}"
    score_s = f" score={score:.2f}" if score is not None else ""
    return (f"  {inc['ticket_id']:<9} {sev:<8} {inc.get('category', '?'):<10} "
            f"{edge:<40}{score_s}{mark}")


def build_prompt(question: str, context: list) -> list:
    context_json = json.dumps(
        [
            {
                "ticket_id": c["ticket_id"],
                "severity": c.get("severity"),
                "category": c.get("category"),
                "source_service": c.get("source_service"),
                "target_dependency": c.get("target_dependency"),
                "excerpt": (c.get("raw_text") or "")[:150],
            }
            for c in context
        ],
        separators=(",", ":"),
    )
    return [
        {"role": "system",
         "content": "You are an SRE analyst. Answer ONLY using the provided incident "
                    "context and cite ticket ids. If the context is insufficient, say so."},
        {"role": "user",
         "content": f"Question: {question}\n\nIncident context (JSON):\n{context_json}\n\n"
                    f"Explain the most likely root cause chain and the remediation priority."},
    ]


def generate(llama_url: str, model: str, messages: list) -> tuple:
    """One generation call. Returns (answer, finish_reason)."""
    # 448: a concise root-cause answer fits, and it stays inside the slot
    # window (--ctx-size / --parallel) even with the full hybrid context.
    payload = {"model": model, "messages": messages, "max_tokens": 448, "temperature": 0.0}
    try:
        result = rest(llama_url.rstrip("/") + "/v1/chat/completions", "POST", payload)
        choice = result["choices"][0]
        answer = choice["message"]["content"]
        finish = choice.get("finish_reason")
        if finish == "length":
            answer += ("\n[answer cut off: hit max_tokens or the server's context "
                       "window - raise --ctx-size in k8s/llama-cpp.yaml, or reduce "
                       "--k/--graph-limit]")
        return answer, finish
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        return f"[LLM HTTP {exc.code}: {body}]", None
    except (urllib.error.URLError, KeyError) as exc:
        return f"[LLM generation unavailable: {exc}]", None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--query", default=DEFAULT_QUERY)
    ap.add_argument("--k", type=int, default=4, help="vector top-K")
    ap.add_argument("--hops", type=int, default=2, help="graph traversal depth")
    ap.add_argument("--graph-min-severity", default="CRITICAL", choices=["CRITICAL", "MEDIUM", "LOW"],
                    help="only incidents at least this severe enter the graph context "
                         "(BFS still traverses everything; default CRITICAL keeps the demo crisp)")
    ap.add_argument("--graph-limit", type=int, default=6, help="max graph-recovered tickets in context")
    ap.add_argument("--offline", action="store_true",
                    help="read vector/graph mirrors from disk instead of Qdrant")
    ap.add_argument("--vectors-dir", default=None, help="dir with vector rows (json part files)")
    ap.add_argument("--graph-dir", default=None, help="dir with adjacency json mirror (optional)")
    ap.add_argument("--embed-backend", default=None, choices=["sbert", "hash"],
                    help="default: hash when offline, else EMBED_BACKEND/sbert")
    ap.add_argument("--llama-url", default=DEFAULT_LLAMA_URL)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--qdrant-url", default=DEFAULT_QDRANT_URL)
    ap.add_argument("--no-llm", action="store_true", help="skip the generation step")
    args = ap.parse_args()

    backend = args.embed_backend or os.environ.get("EMBED_BACKEND") or ("hash" if args.offline else "sbert")

    # ---- load corpus -------------------------------------------------------
    if args.offline:
        if not args.vectors_dir:
            ap.error("--offline requires --vectors-dir")
        all_incidents = load_json_rows(args.vectors_dir)
        qdrant = None
    else:
        qdrant = args.qdrant_url
        all_incidents = load_incidents_from_qdrant(qdrant)

    # ---- 5a vector search ---------------------------------------------------
    qvec = embed(args.query, backend=backend, query=True)
    if qdrant:
        vector_hits = vector_search_qdrant(qdrant, qvec, args.k)
    else:
        vector_hits = vector_search_files(all_incidents, qvec, args.k)

    # ---- 5b graph expansion -------------------------------------------------
    discovered = graph_expand(all_incidents, vector_hits, args.hops)
    severity_floor = SEVERITY_RANK[args.graph_min_severity]
    graph_hits = [h for h in discovered if SEVERITY_RANK.get(h.get("severity"), 3) <= severity_floor]
    graph_hits.sort(key=lambda h: (SEVERITY_RANK.get(h.get("severity"), 3), h["_hop"], h["ticket_id"]))
    # Round-robin across hops within each severity band before truncating.
    # A real micro-LLM over-assigns CRITICAL, so plain (severity, hop) order
    # lets hop-1 noise tickets fill the whole --graph-limit and squeeze out
    # the deeper-hop discoveries that are Graph-RAG's whole point (INC-042
    # sits at hop 2). Interleaving guarantees every hop is represented.
    by_sev: dict = {}
    for h in graph_hits:
        by_sev.setdefault(SEVERITY_RANK.get(h.get("severity"), 3), []).append(h)
    ordered = []
    for sev_rank in sorted(by_sev):
        hop_queues: dict = {}
        for h in by_sev[sev_rank]:
            hop_queues.setdefault(h["_hop"], []).append(h)
        while any(hop_queues.values()):
            for hop in sorted(hop_queues):
                if hop_queues[hop]:
                    ordered.append(hop_queues[hop].pop(0))
    graph_hits = ordered[: args.graph_limit]

    hybrid = sorted(vector_hits, key=lambda h: -h.get("score", 0)) + graph_hits
    vector_only_ids = [h["ticket_id"] for h in vector_hits]
    graph_only_ids = [h["ticket_id"] for h in graph_hits]

    print("=" * 78)
    print(f"QUESTION: {args.query}")
    print(f"backend={backend}  k={args.k}  hops={args.hops}  corpus={len(all_incidents)} incidents")
    print("=" * 78)

    print("\n===== VECTOR-ONLY RAG (semantic top-K) =====")
    for hit in vector_hits:
        print(fmt_row(hit, score=hit.get("score")))

    print(f"\n===== GRAPH-RAG EXPANSION ({args.hops}-hop over service graph; "
          f"{len(discovered)} traversed, {len(graph_hits)} kept at >={args.graph_min_severity}) =====")
    if not graph_hits:
        print("  (no new incidents reached from the graph)")
    for hit in graph_hits:
        print(fmt_row(hit, mark=f"  [graph hop {hit['_hop']} via {hit['_via']}]"))

    vector_missed = [t for t in graph_only_ids if t not in vector_only_ids]
    print("\n===== VERDICT =====")
    print(f"  vector-only tickets : {', '.join(vector_only_ids) or '-'}")
    print(f"  graph-recovered     : {', '.join(graph_only_ids) or '-'}")
    if vector_missed:
        critical = [h for h in graph_hits if h.get("severity") == "CRITICAL"]
        print(f"  >> Vector-only RAG MISSES {', '.join(vector_missed)};"
              f" Graph-RAG recovers them{' (incl. CRITICAL root cause!)' if critical else ''}.")

    # ---- 5c side-by-side generation ----------------------------------------
    if not args.no_llm:
        ans_vec, _ = generate(args.llama_url, args.model, build_prompt(args.query, vector_hits))
        ans_hyb, _ = generate(args.llama_url, args.model, build_prompt(args.query, hybrid))
        print("\n" + "=" * 37 + " VECTOR-ONLY ANSWER " + "=" * 37)
        print(ans_vec)
        print("\n" + "=" * 37 + "  HYBRID GRAPH-RAG ANSWER " + "=" * 37)
        print(ans_hyb)

    # ---- optional adjacency inspection (built by task4) ---------------------
    if args.graph_dir:
        try:
            mirror = args.graph_dir.rstrip("/") + "/edges_json"
            edges = load_json_rows(mirror)
            print("\n" + "=" * 78)
            print("SERVICE DEPENDENCY GRAPH (adjacency table from Exercise 4):")
            for e in sorted(edges, key=lambda e: (e["source_service"], e["target_dependency"])):
                print(f"  {e['source_service']:>18} -> {e['target_dependency']:<18} x{e['occurrences']}")
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    main()
