"""Stage 2 evaluation: compare three conditions on the same 30 questions.

  A. LLM only            : no building data
  B. Grounded            : facts from the knowledge graph in the prompt
  C. Grounded + validated: B, then symbolic validation and one feedback round

Because temperature is 0, the first attempt of C is the answer of B, so it is reused.
An answer is valid when its IDs are exactly the IDs returned by SPARQL.

Usage (Ollama running):  python -m firetwin.evaluate
Writes docs/eval_results.csv (one row per question and condition) and docs/eval_summary.md.
"""
import csv
import json
import time
from pathlib import Path

from firetwin.eval_questions import build_questions
from firetwin.facts import build_facts
from firetwin.kg import load_graph
from firetwin.llm import DEFAULT_MODEL, chat
from firetwin.validate import compare, ids_from_sparql

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"

FORMAT = """Reply in JSON with two keys:
"answer": one or two sentences,
"ids": the identifiers (the names in parentheses in the facts, e.g. Room103 or ExitMain)
of exactly the items the question asks for: rooms or spaces, or exits when the question is about exits.
Do not include compartments, storeys or other context. If nothing matches, use "ids": []."""

SYSTEM_PLAIN = "You answer questions about one specific office building.\n" + FORMAT
SYSTEM_GROUNDED = ("You answer questions about one specific office building.\nUse ONLY the facts below. "
                   + FORMAT + "\n\nFacts:\n{facts}")


def parse(reply: str) -> list[str]:
    try:
        return [str(i) for i in json.loads(reply).get("ids", [])]
    except (json.JSONDecodeError, AttributeError):
        return []


def run(messages: list[dict]) -> tuple[str, float, bool]:
    """Call the LLM. A timeout or connection error is recorded, not fatal."""
    start = time.perf_counter()
    try:
        reply, error = chat(messages, json_mode=True), False
    except (TimeoutError, OSError) as exc:
        print(f"    LLM error: {exc}")
        reply, error = "", True
    return reply, time.perf_counter() - start, error


def record(rows, q, condition, ids, result, seconds, error):
    rows.append({"id": q["id"], "category": q["category"], "question": q["question"],
                 "condition": condition, "ids": " ".join(ids),
                 "valid": not result["problems"] and not error, "invented": result["invented"],
                 "wrong": result["wrong"], "missing": result["missing"],
                 "seconds": round(seconds, 2), "error": error})


def summarise(rows) -> str:
    lines = [f"Model: {DEFAULT_MODEL}, temperature 0, {len({r['id'] for r in rows})} questions.\n",
             "| Condition | Valid (all) | Valid (answerable) | Valid (traps) | Invented IDs | Wrong IDs | Missing IDs | LLM errors | Mean time (s) |",
             "|---|---|---|---|---|---|---|---|---|"]
    for condition in ["A. LLM only", "B. Grounded", "C. Grounded + validated"]:
        rs = [r for r in rows if r["condition"] == condition]
        ans = [r for r in rs if r["category"] != "trap"]
        trap = [r for r in rs if r["category"] == "trap"]
        lines.append(f"| {condition} | {sum(r['valid'] for r in rs)}/{len(rs)} "
                     f"| {sum(r['valid'] for r in ans)}/{len(ans)} | {sum(r['valid'] for r in trap)}/{len(trap)} "
                     f"| {sum(r['invented'] for r in rs)} | {sum(r['wrong'] for r in rs)} "
                     f"| {sum(r['missing'] for r in rs)} | {sum(r['error'] for r in rs)} "
                     f"| {sum(r['seconds'] for r in rs) / len(rs):.1f} |")
    return "\n".join(lines)


def main() -> None:
    g = load_graph()
    grounded_system = SYSTEM_GROUNDED.format(facts=build_facts(load_graph(reason=False)))
    rows = []
    questions = build_questions()
    for n, q in enumerate(questions, 1):
        expected = ids_from_sparql(g, q["sparql"])

        reply, t, err = run([{"role": "system", "content": SYSTEM_PLAIN}, {"role": "user", "content": q["question"]}])
        ids = parse(reply)
        record(rows, q, "A. LLM only", ids, compare(g, ids, expected), t, err)

        messages = [{"role": "system", "content": grounded_system}, {"role": "user", "content": q["question"]}]
        reply, t, err = run(messages)
        ids = parse(reply)
        result = compare(g, ids, expected)
        record(rows, q, "B. Grounded", ids, result, t, err)

        total = t
        if result["problems"] or err:
            feedback = ("Your answer was checked against the building data and has errors:\n- "
                        + "\n- ".join(result["problems"])
                        + "\nReturn the complete corrected JSON: remove every wrong id and add every missing one.")
            messages += [{"role": "assistant", "content": reply}, {"role": "user", "content": feedback}]
            reply, t2, err = run(messages)
            total += t2
            ids = parse(reply)
            result = compare(g, ids, expected)
        record(rows, q, "C. Grounded + validated", ids, result, total, err)
        print(f"[{n}/{len(questions)}] {q['id']} done")

    DOCS.mkdir(exist_ok=True)
    with open(DOCS / "eval_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    summary = summarise(rows)
    (DOCS / "eval_summary.md").write_text("# Evaluation summary\n\n" + summary + "\n", encoding="utf-8")
    print("\n" + summary)


if __name__ == "__main__":
    main()
