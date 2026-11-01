"""
Step 6 — Evals: score your Step 5 RAG graph on a fixed test set.

Run:  docker compose exec app python step6/run_evals.py
      docker compose exec app python step6/run_evals.py strict-grader   (label this run)

Each run is saved in step6/results/, so you can compare versions with numbers.
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

# Evaluate YOUR current Step 5 graph (whatever you changed in it)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "step5"))
import graph_rag  # noqa: E402

HERE = Path(__file__).parent
DATASET = HERE / "dataset.json"
RESULTS = HERE / "results"


# ---------- 1. The LLM judge ----------

class Verdict(BaseModel):
    correct: bool = Field(description="Does the answer state the expected facts (or, for unanswerable "
                                      "questions, clearly say the information is not available)?")
    faithful: bool = Field(description="Is every claim in the answer supported by the sources shown? "
                                       "False if it invents anything.")
    reason: str = Field(description="One short sentence explaining the verdict")


JUDGE_SYSTEM = """You are a strict evaluator of a customer-support RAG system.
You compare the system's answer with the expected facts and with the sources it was given.
Wording does not matter; facts and language requirements do.
For unanswerable questions, the answer is correct only if it clearly says the information is not
available and does not invent facts."""


def judge(case: dict, answer: str, chunks: list) -> Verdict:
    sources = "\n\n".join(f'<source file="{c["source"]}">\n{c["content"]}\n</source>' for c in chunks)
    prompt = (
        "<system_context>The assistant works for the shop 'Studio Lumi'. Its system prompt gives it "
        "this name, so mentioning 'Studio Lumi' is expected and is NOT an unsupported claim."
        "</system_context>\n"
        f"<question>{case['question']}</question>\n"
        f"<answerable>{case['answerable']}</answerable>\n"
        f"<expected_facts>{case['expected_facts']}</expected_facts>\n"
        f"<sources_given_to_system>\n{sources or '(none)'}\n</sources_given_to_system>\n"
        f"<system_answer>{answer}</system_answer>"
    )
    return graph_rag.ask_structured(JUDGE_SYSTEM, prompt, Verdict)


# ---------- 2. Cheap deterministic checks (no LLM needed) ----------

def keywords_ok(answer: str, must_contain: list[list[str]]) -> bool | None:
    """Each inner list is a group of alternatives; at least one per group must appear."""
    if not must_contain:
        return None
    text = answer.lower()
    return all(any(alt.lower() in text for alt in group) for group in must_contain)


def sources_ok(case: dict, chunks: list) -> bool | None:
    """Did the grader keep chunks from every expected document?"""
    if not case["answerable"]:
        return None
    used = {c["source"] for c in chunks}
    return all(s in used for s in case["sources"])


# ---------- 3. Run one case ----------

def run_case(case: dict) -> dict:
    start_state = {"question": case["question"], "search_query": "", "chunks": [], "relevant": [],
                   "answer": "", "attempts": 0, "trace": []}
    t0 = time.perf_counter()
    final = graph_rag.app.invoke(start_state)
    seconds = time.perf_counter() - t0

    answer = final["answer"]
    relevant = final["relevant"]
    verdict = judge(case, answer, relevant)
    kw = keywords_ok(answer, case["must_contain"])

    passed = verdict.correct and verdict.faithful and kw is not False
    return {
        "id": case["id"],
        "passed": passed,
        "correct": verdict.correct,
        "faithful": verdict.faithful,
        "keywords_ok": kw,
        "sources_ok": sources_ok(case, relevant),
        "attempts": final["attempts"],
        "seconds": round(seconds, 1),
        "reason": verdict.reason,
        "answer": answer,
        "trace": final["trace"],
    }


# ---------- 4. Run everything, print a report, save results ----------

def fmt(value) -> str:
    return {True: "yes", False: "NO", None: "-"}[value]


def rate(results: list, key: str) -> str:
    values = [r[key] for r in results if r.get(key) is not None]
    if not values:
        return "-"
    return f"{sum(values)}/{len(values)} ({100 * sum(values) / len(values):.0f}%)"


def main(label: str) -> None:
    cases = json.loads(DATASET.read_text())
    print(f"Running {len(cases)} eval cases (label: {label})\n")
    print(f"{'id':<24}{'pass':<6}{'correct':<9}{'faithful':<10}{'keywords':<10}{'sources':<9}{'tries':<7}{'sec':>5}")

    results = []
    for case in cases:
        try:
            r = run_case(case)
        except Exception as e:  # one broken case shouldn't stop the whole run
            r = {"id": case["id"], "passed": False, "correct": None, "faithful": None,
                 "keywords_ok": None, "sources_ok": None, "attempts": 0, "seconds": 0,
                 "reason": f"ERROR: {type(e).__name__}: {e}", "answer": "", "trace": []}
        results.append(r)
        print(f"{r['id']:<24}{fmt(r['passed']):<6}{fmt(r['correct']):<9}{fmt(r['faithful']):<10}"
              f"{fmt(r['keywords_ok']):<10}{fmt(r['sources_ok']):<9}{r['attempts']:<7}{r['seconds']:>5}")

    print("\nFailures:")
    for r in results:
        if not r["passed"]:
            print(f"  - {r['id']}: {r['reason']}")
    if all(r["passed"] for r in results):
        print("  (none)")

    avg_seconds = sum(r["seconds"] for r in results) / len(results)
    summary = {
        "label": label,
        "pass_rate": rate(results, "passed"),
        "correct": rate(results, "correct"),
        "faithful": rate(results, "faithful"),
        "keywords": rate(results, "keywords_ok"),
        "sources": rate(results, "sources_ok"),
        "avg_seconds": round(avg_seconds, 1),
    }
    print("\nSummary:")
    for k, v in summary.items():
        print(f"  {k:<12} {v}")

    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / f"{datetime.now():%Y%m%d-%H%M%S}-{label}.json"
    out.write_text(json.dumps({"summary": summary, "results": results}, indent=2, ensure_ascii=False))
    print(f"\nSaved to {out.relative_to(HERE.parent)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "baseline")
