"""Shared helpers for Step 4: database connection and embeddings."""
import os
from functools import lru_cache
from pathlib import Path

import psycopg
from fastembed import TextEmbedding
from pgvector.psycopg import register_vector

# "db" is the name of the database service in docker-compose.yml
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ai:ai@db:5432/ailab")

# Free, local, multilingual embedding model (supports Albanian, Macedonian, English).
# Downloaded once (~220 MB) on first use, then cached in ai-lab/.cache/
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBED_DIM = 384
CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache" / "fastembed"


@lru_cache
def get_embedder() -> TextEmbedding:
    return TextEmbedding(EMBED_MODEL, cache_dir=str(CACHE_DIR))


def embed(texts: list[str]) -> list:
    """Turn each text into a vector of 384 numbers that captures its meaning."""
    return list(get_embedder().embed(texts))


def connect() -> psycopg.Connection:
    conn = psycopg.connect(DATABASE_URL, autocommit=True)
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(conn)
    return conn
