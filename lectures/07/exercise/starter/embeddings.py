"""
Shared embedding backends - single source of truth so the Spark indexer
(task4_spark_rag_indexer.py) and the query script (task5_hybrid_rag_query.py)
can never drift apart.

  * EMBED_BACKEND=sbert  -> BAAI/bge-small-en-v1.5 bi-encoder (384 dims,
    requires `pip install sentence-transformers`, one forward pass per doc)
  * EMBED_BACKEND=hash   -> deterministic md5 token-hash fallback (stdlib only,
    lexical similarity, no downloads) used for offline demos.
"""

import hashlib
import math
import os
import re

EMBED_DIM = 384
EMBED_BACKEND = os.environ.get("EMBED_BACKEND", "sbert")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "BAAI/bge-small-en-v1.5")

BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def hash_embed(text: str, dim: int = EMBED_DIM) -> list:
    """Deterministic lexical fallback embedding (md5 token hashing, L2-norm)."""
    vec = [0.0] * dim
    for token in re.findall(r"[a-z0-9]+", text.lower()):
        digest = hashlib.md5(token.encode("utf-8")).digest()
        vec[int.from_bytes(digest[:4], "big") % dim] += 1.0
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


_sbert_model = None


def embed(text: str, backend: str = None, query: bool = False) -> list:
    """Embed one text. backend defaults to the EMBED_BACKEND environment variable."""
    backend = backend or EMBED_BACKEND
    if backend == "hash":
        return hash_embed(text)
    global _sbert_model
    if _sbert_model is None:
        from sentence_transformers import SentenceTransformer

        _sbert_model = SentenceTransformer(EMBED_MODEL, device="cpu")
    payload = [BGE_QUERY_PREFIX + text] if query else [text]
    return _sbert_model.encode(payload, normalize_embeddings=True).tolist()[0]
