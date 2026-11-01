"""
Step 4a — Ingest: load documents, split into chunks, embed, store in pgvector.

Run:  docker compose exec app python step4/ingest.py
Re-run it whenever you add or change files in step4/docs/.
"""
from pathlib import Path

from rag_common import EMBED_DIM, connect, embed

DOCS = Path(__file__).parent / "docs"
CHUNK_SIZE = 500     # max characters per chunk
OVERLAP = 100        # characters repeated from the previous chunk


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    """Split by paragraphs, packing them into chunks of up to `size` characters.
    Each new chunk starts with the tail of the previous one, so a sentence
    that falls on a boundary still appears whole in at least one chunk."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, current = [], ""
    for p in paragraphs:
        if current and len(current) + len(p) + 2 > size:
            chunks.append(current)
            tail = current[-overlap:]
            tail = tail[tail.find(" ") + 1:]          # don't start mid-word
            current = f"{tail}\n\n{p}"
        else:
            current = f"{current}\n\n{p}" if current else p
    if current:
        chunks.append(current)
    return chunks


def main() -> None:
    conn = connect()

    # Start fresh every time (fine for learning; real systems update incrementally)
    conn.execute("DROP TABLE IF EXISTS chunks")
    conn.execute(f"""
        CREATE TABLE chunks (
            id          bigserial PRIMARY KEY,
            source      text,
            chunk_index int,
            content     text,
            embedding   vector({EMBED_DIM})
        )
    """)

    files = sorted(p for p in DOCS.rglob("*") if p.suffix in {".md", ".txt"})
    if not files:
        raise SystemExit(f"No .md or .txt files found in {DOCS}")

    total = 0
    for f in files:
        chunks = chunk_text(f.read_text())
        vectors = embed(chunks)
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO chunks (source, chunk_index, content, embedding) VALUES (%s, %s, %s, %s)",
                [(f.name, i, c, v) for i, (c, v) in enumerate(zip(chunks, vectors))],
            )
        print(f"{f.name}: {len(chunks)} chunks")
        total += len(chunks)

    print(f"\nStored {total} chunks from {len(files)} files.")


if __name__ == "__main__":
    main()
