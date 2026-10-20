"""Stage 2, step 3 (v2): grounded answers checked by the knowledge graph.

The LLM answers in JSON with the IDs it refers to. The validator checks the IDs
with SPARQL. If there are problems, the LLM gets the problems as feedback and
one more attempt.

Usage (from the project root, with Ollama running):  python -m firetwin.stage2_validated
"""
import json

from firetwin.facts import build_facts
from firetwin.kg import load_graph
from firetwin.llm import chat
from firetwin.validate import check

SYSTEM = """You answer questions about one specific building.
Use ONLY the facts below. Reply in JSON with two keys:
"answer": one or two sentences,
"ids": the identifiers (the names in parentheses in the facts, e.g. Room103 or ExitMain)
of exactly the items the question asks for: rooms or spaces, or exits when the question is about exits.
Do not include compartments, storeys or other context. If nothing matches, use "ids": [].

Facts:
{facts}"""

# (question, validation query; None means a trap question whose correct answer is empty)
QUESTIONS = [
    ("Which rooms in the office building have no smoke detector?", "rooms_without_smoke_detector"),
    ("Which spaces are in fire compartment B1 of the office building?", "spaces_in_compartment_b1"),
    ("Where are the evacuation exits of the office building?", "exits"),
    ("Can occupants use the elevator to evacuate the office building?", None),
    ("Which rooms of the office building have a sprinkler?", None),
]


def parse(reply: str) -> tuple[str, list[str]]:
    """Read the JSON reply; a malformed reply counts as an answer with no IDs."""
    try:
        data = json.loads(reply)
        return str(data.get("answer", "")), [str(i) for i in data.get("ids", [])]
    except (json.JSONDecodeError, AttributeError):
        return reply, []


def main() -> None:
    g = load_graph()
    system = SYSTEM.format(facts=build_facts(load_graph(reason=False)))
    valid_first = valid_final = 0
    for question, query in QUESTIONS:
        messages = [{"role": "system", "content": system}, {"role": "user", "content": question}]
        reply = chat(messages, json_mode=True)
        answer, ids = parse(reply)
        problems = check(g, ids, query)
        print(f"\nQ: {question}")
        print(f"  Attempt 1: {answer}  ids={ids}")
        print(f"  Validation: {'OK' if not problems else problems}")
        valid_first += not problems
        if problems:
            feedback = ("Your answer was checked against the building data and has errors:\n- "
                        + "\n- ".join(problems) + "\nReturn the complete corrected JSON: remove every wrong id and add every missing one.")
            messages += [{"role": "assistant", "content": reply}, {"role": "user", "content": feedback}]
            answer, ids = parse(chat(messages, json_mode=True))
            problems = check(g, ids, query)
            print(f"  Attempt 2: {answer}  ids={ids}")
            print(f"  Validation: {'OK' if not problems else problems}")
        valid_final += not problems
    print(f"\nValid answers: {valid_first}/{len(QUESTIONS)} at first attempt, "
          f"{valid_final}/{len(QUESTIONS)} after validation feedback")


if __name__ == "__main__":
    main()
