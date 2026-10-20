"""Stage 2, step 2: give the LLM the facts of OUR building (grounding).

Each question is asked twice: without facts (LLM only) and with the facts
extracted from the knowledge graph. Two trap questions ask about things that
do not exist in the building (an elevator, sprinklers).

Usage (from the project root, with Ollama running):  python -m firetwin.stage2_grounded
"""
import time

from firetwin.facts import build_facts
from firetwin.kg import load_graph, run_query
from firetwin.llm import ask

SYSTEM = """You answer questions about one specific building.
Use ONLY the facts below. If the facts do not contain the answer, reply exactly: Not in the building data.
Do not add general safety advice. Answer in one or two sentences.

Facts:
{facts}"""

# (question, SPARQL query giving the truth, or a fixed truth for trap questions)
QUESTIONS = [
    ("Which rooms in the office building have no smoke detector?", "rooms_without_smoke_detector"),
    ("Which spaces are in fire compartment B1 of the office building?", "spaces_in_compartment"),
    ("Where are the evacuation exits of the office building?", "exits"),
    ("Can occupants use the elevator to evacuate the office building?", "TRAP: there is no elevator"),
    ("Which rooms of the office building have a sprinkler?", "TRAP: there are no sprinklers"),
]


def timed(question: str, system: str | None = None) -> tuple[str, float]:
    start = time.perf_counter()
    answer = ask(question, system=system)
    return answer.strip(), time.perf_counter() - start


def main() -> None:
    g = load_graph()
    system = SYSTEM.format(facts=build_facts(load_graph(reason=False)))
    for question, truth_source in QUESTIONS:
        if truth_source.startswith("TRAP"):
            truth = truth_source
        else:
            truth = [" | ".join(v.split("#")[-1] for v in row) for row in run_query(g, truth_source)]
        plain, t1 = timed(question)
        grounded, t2 = timed(question, system)
        print(f"\nQ: {question}")
        print(f"  LLM only  ({t1:.1f} s): {plain[:300]}")
        print(f"  Grounded  ({t2:.1f} s): {grounded}")
        print(f"  Knowledge graph: {truth}")


if __name__ == "__main__":
    main()
