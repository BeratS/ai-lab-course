"""
Step 7b — Run the Step 6 evals with tracing, one trace per eval case.

Run:  docker compose exec app python step7/traced_evals.py v3-traced
Then open http://localhost:6006 and click the project "ai-lab-evals".
A failing case is now one click away from its full trace: every prompt, every response.
"""
import sys
from pathlib import Path

from tracing import setup_tracing

tracer, provider = setup_tracing("ai-lab-evals")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "step6"))
import run_evals  # noqa: E402

original_run_case = run_evals.run_case


def traced_run_case(case: dict) -> dict:
    with tracer.start_as_current_span(f"eval:{case['id']}", openinference_span_kind="chain") as span:
        span.set_attribute("input.value", case["question"])
        result = original_run_case(case)
        span.set_attribute("output.value", result["answer"])
        # Custom attributes: filter and search by these in the dashboard
        span.set_attribute("eval.passed", result["passed"])
        span.set_attribute("eval.faithful", bool(result["faithful"]))
        span.set_attribute("eval.reason", result["reason"])
    return result


# Swap in the traced version; main() looks up run_case at call time, so it uses ours
run_evals.run_case = traced_run_case

if __name__ == "__main__":
    try:
        run_evals.main(sys.argv[1] if len(sys.argv) > 1 else "traced")
    finally:
        provider.force_flush()
        print("\nTraces sent. Open http://localhost:6006 -> project 'ai-lab-evals'")
