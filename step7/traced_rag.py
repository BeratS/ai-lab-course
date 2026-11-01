"""
Step 7a — Your Step 5 RAG graph, with tracing.

Run:  docker compose exec app python step7/traced_rag.py "How much is shipping to Kosovo?"
Then open http://localhost:6006 and click the project "ai-lab".
"""
import sys
from pathlib import Path

from tracing import setup_tracing

# 1. Turn tracing on FIRST, so the instrumentation is in place before any calls happen
tracer, provider = setup_tracing("ai-lab")

# 2. Now import the app code (unchanged Step 5 graph)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "step5"))
import graph_rag  # noqa: E402


def ask(question: str) -> str:
    # 3. One top-level span per user request: everything inside nests under it
    with tracer.start_as_current_span("rag_request", openinference_span_kind="chain") as span:
        span.set_attribute("input.value", question)
        answer = graph_rag.run(question)
        span.set_attribute("output.value", answer)
    return answer


if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            ask(" ".join(sys.argv[1:]))
        else:
            while (q := input("\nQuestion (or 'exit'): ").strip()) not in ("exit", "quit"):
                if q:
                    ask(q)
    finally:
        # Spans are sent in batches: flush before exiting or the last ones are lost
        provider.force_flush()
        print("\nTraces sent. Open http://localhost:6006 -> project 'ai-lab'")
