#!/usr/bin/env python3
"""
Exercise 4 - Scalable RAG indexing with PySpark: Embedders -> Qdrant + Graph.

This script is complete and runs as given - there is no Python for you to
write. Your task is to run it, then verify the vectors in Qdrant and the
adjacency tables it leaves on HDFS.

Reads the enriched incidents written by the Kafka Connect HDFS sink
(/topics/enriched-incidents) and produces two scalable structures:

  1. VECTOR store: a 384-dimensional embedding per incident, upserted into
     Qdrant (collection `incidents`) or, when QDRANT_URL is empty, written as
     Parquet + JSON to --vectors-out (local-development fallback).

  2. GRAPH (for Graph-RAG): a service-dependency knowledge graph derived from
     the LLM-extracted edges `source_service -> target_dependency`, saved as
     partitioned Parquet adjacency tables (vertices + edges) on HDFS.

WHY AN EMBEDDER AND NOT THE 0.5B GENERATIVE MODEL?
  * A decoder-only LLM produces token embeddings only for its own next-token
    loop; its hidden states are NOT trained as comparable similarity vectors.
  * A bi-encoder (Sentence-Transformers, 33-120M params) is trained with
    contrastive loss so that cos(v(a), v(b)) ranks semantic similarity - and
    it encodes a document in ONE forward pass instead of hundreds of
    autoregressive steps. On CPU that is ~100 docs/s vs. ~0.1 docs/s.
  * It runs where the data lives: inside Spark executors via mapInPandas
    (model loaded ONCE per partition, then batches of pandas rows).

Run on the cluster from the interactive pod:
    pip install sentence-transformers          # first time only
    spark-submit task4_spark_rag_indexer.py
Local development (hash embeddings, no downloads):
    SPARK_ENV=local EMBED_BACKEND=hash QDRANT_URL= \
        spark-submit task4_spark_rag_indexer.py --input ./local_enriched ...
"""

import argparse
import json
import os
import urllib.error
import urllib.request
import uuid

from pyspark.sql import functions as F
from pyspark.sql.types import (
    ArrayType,
    FloatType,
    StringType,
    StructField,
    StructType,
)

from embeddings import EMBED_BACKEND, EMBED_DIM, EMBED_MODEL, hash_embed
from utils import SPARK_ENV, get_spark_context

DEFAULT_INPUT = os.environ.get("ENRICHED_INPUT", "hdfs://namenode:9000/topics/enriched-incidents")
DEFAULT_VECTORS_OUT = os.environ.get("VECTORS_OUT", "hdfs://namenode:9000/rag/vectors")
DEFAULT_GRAPH_OUT = os.environ.get("GRAPH_OUT", "hdfs://namenode:9000/graph/services")
DEFAULT_QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
COLLECTION = os.environ.get("QDRANT_COLLECTION", "incidents")

OUTPUT_SCHEMA = StructType(
    [
        StructField("ticket_id", StringType(), False),
        StructField("timestamp", StringType(), True),
        StructField("raw_text", StringType(), True),
        StructField("category", StringType(), True),
        StructField("severity", StringType(), True),
        StructField("source_service", StringType(), True),
        StructField("target_dependency", StringType(), True),
        StructField("embedding", ArrayType(FloatType()), False),
    ]
)


# ---------------------------------------------------------------------------
# Embedding backends (module level -> initialised ONCE per Spark partition)
# ---------------------------------------------------------------------------
_MODEL = None


def get_model():
    global _MODEL
    if _MODEL is None and EMBED_BACKEND == "sbert":
        from sentence_transformers import SentenceTransformer

        _MODEL = SentenceTransformer(EMBED_MODEL, device="cpu")
    return _MODEL


def embed_partition(pdf_iter):
    """mapInPandas body: model loaded once per partition, rows in batches."""
    import pandas as pd

    model = get_model()
    for pdf in pdf_iter:
        texts = pdf["raw_text"].fillna("").tolist()
        if EMBED_BACKEND == "sbert":
            vectors = model.encode(texts, normalize_embeddings=True, batch_size=16).tolist()
        else:
            vectors = [hash_embed(t) for t in texts]
        pdf = pdf.assign(embedding=vectors)
        yield pdf[
            [
                "ticket_id", "timestamp", "raw_text", "category", "severity",
                "source_service", "target_dependency", "embedding",
            ]
        ]


# ---------------------------------------------------------------------------
# Qdrant via plain REST (urllib) - no client library needed
# ---------------------------------------------------------------------------
def qdrant_request(base: str, method: str, path: str, body=None):
    req = urllib.request.Request(
        base.rstrip("/") + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode() or "{}")


def qdrant_ensure_collection(base: str, recreate: bool = False) -> None:
    if recreate:
        qdrant_request(base, "DELETE", f"/collections/{COLLECTION}")
    status, _ = qdrant_request(base, "GET", f"/collections/{COLLECTION}")
    if status == 200:
        print(f"qdrant collection '{COLLECTION}' already exists")
        return
    status, body = qdrant_request(
        base, "PUT", f"/collections/{COLLECTION}",
        {"vectors": {"size": EMBED_DIM, "distance": "Cosine"}},
    )
    if status not in (200, 201):
        raise RuntimeError(f"cannot create qdrant collection: {status} {body}")
    print(f"created qdrant collection '{COLLECTION}' (size={EMBED_DIM}, distance=Cosine)")


def qdrant_point_id(ticket_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"incident://{ticket_id}"))


def upsert_partition(iterator) -> None:
    """foreachPartition body: one HTTP client per partition, batches of 64."""
    base = DEFAULT_QDRANT_URL
    buffer = []

    def flush():
        if not buffer:
            return
        qdrant_request(base, "PUT", f"/collections/{COLLECTION}/points?wait=false",
                       {"points": list(buffer)})
        buffer.clear()

    for row in iterator:
        buffer.append(
            {
                "id": qdrant_point_id(row["ticket_id"]),
                "vector": [float(x) for x in row["embedding"]],
                "payload": {
                    "ticket_id": row["ticket_id"],
                    "timestamp": row["timestamp"],
                    "category": row["category"],
                    "severity": row["severity"],
                    "source_service": row["source_service"],
                    "target_dependency": row["target_dependency"],
                    "raw_text": (row["raw_text"] or "")[:800],
                },
            }
        )
        if len(buffer) >= 64:
            flush()
    flush()


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------
def build_graph(embedded):
    edges = (
        embedded.select("source_service", "target_dependency")
        .where(F.col("target_dependency").isNotNull())
        .where((F.col("target_dependency") != "none") & (F.col("target_dependency") != ""))
        .where(F.col("target_dependency") != F.col("source_service"))
        .groupBy("source_service", "target_dependency")
        .agg(F.count(F.lit(1)).alias("occurrences"))
    )
    sources = embedded.select(
        F.col("source_service").alias("service"),
        F.lit(1).alias("as_source"),
        F.lit(0).alias("as_dependency"),
    )
    targets = embedded.where(F.col("target_dependency").isNotNull()) \
        .where((F.col("target_dependency") != "none") & (F.col("target_dependency") != "")) \
        .select(
            F.col("target_dependency").alias("service"),
            F.lit(0).alias("as_source"),
            F.lit(1).alias("as_dependency"),
        )
    vertices = (
        sources.union(targets)
        .groupBy("service")
        .agg(F.sum("as_source").alias("incidents_as_source"),
             F.sum("as_dependency").alias("incidents_as_dependency"))
    )
    return vertices, edges


def write_both(df, base_path: str, partition_by: str = None) -> None:
    """Parquet (canonical, partitioned) + JSON copy (stdlib-readable mirror)."""
    writer = df.write.mode("overwrite")
    if partition_by:
        writer = writer.partitionBy(partition_by)
    writer.parquet(base_path)
    df.coalesce(1).write.mode("overwrite").json(base_path + "_json")


# ---------------------------------------------------------------------------
def read_incidents(spark, path: str):
    """Read JSON-lines anywhere the HDFS sink or a local dir put them."""
    last_err = None
    for pattern in (f"{path}/**/*.json", f"{path}/**/*.jsonl", path):
        try:
            df = spark.read.json(pattern)
            if "ticket_id" in df.columns:
                print(f"reading incidents from {pattern}")
                return df
        except Exception as exc:
            last_err = exc
    raise RuntimeError(f"no incidents found under {path}: {last_err}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--input", default=DEFAULT_INPUT)
    ap.add_argument("--vectors-out", default=DEFAULT_VECTORS_OUT)
    ap.add_argument("--graph-out", default=DEFAULT_GRAPH_OUT)
    ap.add_argument("--qdrant-url", default=DEFAULT_QDRANT_URL)
    ap.add_argument("--partitions", type=int, default=4, help="repartition before embedding")
    ap.add_argument("--recreate-collection", action="store_true")
    args = ap.parse_args()

    env = SPARK_ENV.LOCAL if os.environ.get("SPARK_ENV", "k8s").lower() == "local" else SPARK_ENV.K8S
    spark = get_spark_context(app_name="task4-rag-indexer", config=env)
    try:
        raw = read_incidents(spark, args.input)
        flat = raw.select(
            F.col("ticket_id"),
            F.col("timestamp"),
            F.col("raw_text"),
            F.col("llm.category").alias("category"),
            F.col("llm.severity").alias("severity"),
            F.col("llm.source_service").alias("source_service"),
            F.col("llm.target_dependency").alias("target_dependency"),
        ).where(F.col("ticket_id").isNotNull() & F.col("category").isNotNull())

        total_in = raw.count()
        embedded = (
            flat.repartition(args.partitions)
            .mapInPandas(embed_partition, schema=OUTPUT_SCHEMA)
            .cache()
        )
        n = embedded.count()
        print(f"embedded {n}/{total_in} incidents with backend={EMBED_BACKEND} "
              f"(model={EMBED_MODEL if EMBED_BACKEND == 'sbert' else 'md5-token-hash'})")
        if n == 0:
            raise SystemExit("nothing embedded - did you run the enricher + HDFS sink first?")

        # ---- 1) vector store ------------------------------------------------
        if args.qdrant_url:
            qdrant_ensure_collection(args.qdrant_url, recreate=args.recreate_collection)
            embedded.foreachPartition(upsert_partition)
            print(f"upserted {n} points into qdrant at {args.qdrant_url}")
        else:
            write_both(embedded, args.vectors_out)
            print(f"wrote vector parquet + json mirror under {args.vectors_out}")

        # ---- 2) service dependency graph (Graph-RAG substrate) --------------
        vertices, edges = build_graph(embedded)
        write_both(vertices, f"{args.graph_out}/vertices")
        write_both(edges, f"{args.graph_out}/edges", partition_by="source_service")
        edge_rows = edges.collect()
        vertex_rows = vertices.collect()
        print(f"graph: {len(vertex_rows)} service vertices, {len(edge_rows)} dependency edges")
        for row in sorted(edge_rows, key=lambda r: (r["source_service"], r["target_dependency"]))[:12]:
            print(f"  {row['source_service']:>18} -> {row['target_dependency']:<18} x{row['occurrences']}")
        print(f"saved adjacency tables under {args.graph_out}/{{vertices,edges}} (+_json mirrors)")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
