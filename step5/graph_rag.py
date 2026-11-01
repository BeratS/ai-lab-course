"""
Step 5 — RAG as a LangGraph workflow

Same RAG as Step 4, but now as a graph with decisions:

    rewrite_query -> retrieve -> grade_chunks --(relevant found)--> generate
         ^                          |
         +------(nothing relevant, |--(still nothing after retries)--> give_up
                 try again)--------+

Run:  docker compose exec app python step5/graph_rag.py "How much is shipping to Kosovo?"
  or: docker compose exec app python step5/graph_rag.py        (interactive)

Needs the Step 4 database: run step4/ingest.py first.
"""
import os
import sys
from pathlib import Path
from typing import TypedDict

# Reuse the database + embeddings from Step 4
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "step4"))
from rag_common import connect, embed  # noqa: E402

from anthropic import Anthropic  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from langgraph.graph import END, START, StateGraph  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

load_dotenv()
client = Anthropic()

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
TOP_K = 6            # retrieve more than we need; the grader filters
MAX_ATTEMPTS = 2     # how many different search queries to try

_conn = None


def get_conn():
    global _conn
    if _conn is None:
        _conn = connect()
    return _conn


# ---------- 1. The state: data that flows through the graph ----------

class Chunk(TypedDict):
    source: str
    content: str
    distance: float


class RAGState(TypedDict):
    question: str          # the user's original question
    search_query: str      # what we actually search for
    chunks: list[Chunk]    # what retrieval found
    relevant: list[Chunk]  # what the grader kept
    answer: str
    attempts: int
    trace: list[str]       # a log of decisions, for you to read


# ---------- 2. LLM helper: structured outputs + Pydantic (like Step 2) ----------

def ask_structured(system: str, prompt: str, schema: type[BaseModel]) -> BaseModel:
    # parse() sends the Pydantic schema to the API, which guarantees JSON
    # in that shape, and returns it already validated as a Pydantic object
    response = client.messages.parse(
        model=MODEL,
        max_tokens=500,
        system=system,
        messages=[{"role": "user", "content": prompt}],
        output_format=schema,
    )
    return response.parsed_output


class SearchQuery(BaseModel):
    query: str = Field(description="A short search query with the key terms")


class Grades(BaseModel):
    relevant_ids: list[int] = Field(description="IDs of the chunks that help answer the question")
    reason: str = Field(description="One short sentence explaining the choice")


# ---------- 3. The nodes: each one reads the state and returns updates ----------

def rewrite_query(state: RAGState) -> dict:
    attempts = state["attempts"] + 1
    if attempts == 1:
        instruction = ("Rewrite the user's question as a short search query containing the key terms. "
                       "Keep the language of the question.")
    else:
        instruction = (f"A previous search for {state['search_query']!r} found nothing relevant. "
                       "Write a DIFFERENT search query: use synonyms, or translate the key terms "
                       "into English, Albanian or Macedonian.")
    result = ask_structured(instruction, f"Question: {state['question']}", SearchQuery)
    return {
        "search_query": result.query,
        "attempts": attempts,
        "trace": state["trace"] + [f"rewrite #{attempts}: {result.query!r}"],
    }


def retrieve(state: RAGState) -> dict:
    vector = embed([state["search_query"]])[0]
    rows = get_conn().execute(
        "SELECT source, content, embedding <=> %s AS distance FROM chunks ORDER BY distance LIMIT %s",
        (vector, TOP_K),
    ).fetchall()
    chunks = [Chunk(source=s, content=c, distance=float(d)) for s, c, d in rows]
    return {
        "chunks": chunks,
        "trace": state["trace"] + [f"retrieve: {len(chunks)} chunks from "
                                   f"{sorted({c['source'] for c in chunks})}"],
    }


def grade_chunks(state: RAGState) -> dict:
    numbered = "\n\n".join(
        f'<chunk id="{i}" file="{c["source"]}">\n{c["content"]}\n</chunk>'
        for i, c in enumerate(state["chunks"])
    )
    grades = ask_structured(
        "You check which text chunks contain information that helps answer the question. "
        "Chunks may be in English, Albanian or Macedonian. Be strict: return an empty list "
        "if none of them actually help.",
        f"{numbered}\n\nQuestion: {state['question']}",
        Grades,
    )
    valid_ids = [i for i in grades.relevant_ids if 0 <= i < len(state["chunks"])]
    relevant = [state["chunks"][i] for i in valid_ids]
    return {
        "relevant": relevant,
        "trace": state["trace"] + [f"grade: kept {valid_ids} of {len(state['chunks'])} ({grades.reason})"],
    }


def generate(state: RAGState) -> dict:
    sources = "\n\n".join(
        f'<source id="{i}" file="{c["source"]}">\n{c["content"]}\n</source>'
        for i, c in enumerate(state["relevant"], start=1)
    )
    response = client.messages.create(
        model=MODEL,
        max_tokens=800,
        system=("You answer customer questions for Studio Lumi using ONLY the sources provided. "
                "Cite sources like [1]. If something is not in the sources, say so. "
                "Answer in the same language as the question."),
        messages=[{"role": "user", "content": f"{sources}\n\nQuestion: {state['question']}"}],
    )
    # The reply can start with a "thinking" block, so collect only the text blocks
    text = "".join(b.text for b in response.content if b.type == "text")
    return {"answer": text,
            "trace": state["trace"] + [f"generate: used {len(state['relevant'])} chunks"]}


def give_up(state: RAGState) -> dict:
    return {"answer": "Sorry, I couldn't find that information in our documents.",
            "trace": state["trace"] + [f"give_up after {state['attempts']} attempts"]}


# ---------- 4. The routing decision after grading ----------

def route_after_grading(state: RAGState) -> str:
    if state["relevant"]:
        return "generate"
    if state["attempts"] < MAX_ATTEMPTS:
        return "rewrite_query"
    return "give_up"


# ---------- 5. Wire it together ----------

def build_graph():
    graph = StateGraph(RAGState)
    graph.add_node("rewrite_query", rewrite_query)
    graph.add_node("retrieve", retrieve)
    graph.add_node("grade_chunks", grade_chunks)
    graph.add_node("generate", generate)
    graph.add_node("give_up", give_up)

    graph.add_edge(START, "rewrite_query")
    graph.add_edge("rewrite_query", "retrieve")
    graph.add_edge("retrieve", "grade_chunks")
    graph.add_conditional_edges("grade_chunks", route_after_grading,
                                {"generate": "generate",
                                 "rewrite_query": "rewrite_query",
                                 "give_up": "give_up"})
    graph.add_edge("generate", END)
    graph.add_edge("give_up", END)
    return graph.compile()


app = build_graph()


def run(question: str) -> str:
    start: RAGState = {"question": question, "search_query": "", "chunks": [], "relevant": [],
                       "answer": "", "attempts": 0, "trace": []}
    answer = ""
    # stream() yields after each node, so you can watch the graph move
    for update in app.stream(start, stream_mode="updates"):
        for node, changes in update.items():
            print(f"  [{node}] {changes['trace'][-1]}")
            answer = changes.get("answer", answer)
    print(f"\nAnswer:\n{answer}")
    return answer


if __name__ == "__main__":
    # Save a diagram of the graph (open it at mermaid.live, or with a Mermaid extension in VS Code)
    diagram = Path(__file__).parent / "graph.mmd"
    diagram.write_text(app.get_graph().draw_mermaid())

    if len(sys.argv) > 1:
        run(" ".join(sys.argv[1:]))
    else:
        while (q := input("\nQuestion (or 'exit'): ").strip()) not in ("exit", "quit"):
            if q:
                run(q)
