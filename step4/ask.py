"""
Step 4b — Ask: retrieve the most relevant chunks, then let the model answer from them.

Run:  docker compose exec app python step4/ask.py "How much is shipping to Kosovo?"
  or: docker compose exec app python step4/ask.py      (interactive)
"""
import os
import sys

from anthropic import Anthropic
from dotenv import load_dotenv

from rag_common import connect, embed

load_dotenv()
client = Anthropic()
conn = connect()

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
TOP_K = 4            # how many chunks to give the model

SYSTEM = """You answer customer questions for Studio Lumi using ONLY the sources provided.
- Cite the sources you used like [1] or [2].
- If the answer is not in the sources, say you don't know. Never invent facts.
- Answer in the same language as the question, even if the sources are in another language."""


def retrieve(question: str, k: int = TOP_K) -> list[tuple]:
    """R in RAG: find the k chunks whose meaning is closest to the question."""
    question_vector = embed([question])[0]
    return conn.execute(
        """
        SELECT source, chunk_index, content, embedding <=> %s AS distance
        FROM chunks
        ORDER BY distance
        LIMIT %s
        """,
        (question_vector, k),
    ).fetchall()


def answer(question: str) -> None:
    rows = retrieve(question)

    print("\nRetrieved chunks (smaller distance = more similar):")
    for i, (source, idx, content, distance) in enumerate(rows, start=1):
        preview = content.replace("\n", " ")[:80]
        print(f"  [{i}] {distance:.3f}  {source}#{idx}  {preview}...")

    # A in RAG: augment the prompt with the retrieved text
    sources = "\n\n".join(
        f'<source id="{i}" file="{source}">\n{content}\n</source>'
        for i, (source, _, content, _) in enumerate(rows, start=1)
    )
    prompt = f"{sources}\n\nQuestion: {question}"

    # G in RAG: generate the answer
    response = client.messages.create(
        model=MODEL,
        max_tokens=800,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    print(f"\nAnswer:\n{response.content[0].text}")
    print(f"\n[tokens in: {response.usage.input_tokens}, out: {response.usage.output_tokens}]")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        answer(" ".join(sys.argv[1:]))
    else:
        while (q := input("\nQuestion (or 'exit'): ").strip()) not in ("exit", "quit"):
            if q:
                answer(q)
