"""Stage 2, step 1: ask the LLM about OUR building without giving it any data.

The LLM has never seen this building, so any specific answer is a guess.
Each answer is printed next to the ground truth from the knowledge graph.

Usage (from the project root, with Ollama running):  python -m firetwin.stage2_llm_only
"""
import time

from firetwin.kg import load_graph, run_query
from firetwin.llm import ask

QUESTIONS = [
    ("Which rooms in the office building have no smoke detector?", "rooms_without_smoke_detector"),
    ("Which spaces are in fire compartment B1 of the office building?", "spaces_in_compartment"),
    ("Where are the evacuation exits of the office building?", "exits"),
]


def main() -> None:
    g = load_graph()
    for question, query in QUESTIONS:
        start = time.perf_counter()
        answer = ask(question)
        seconds = time.perf_counter() - start
        truth = [" | ".join(v.split("#")[-1] for v in row) for row in run_query(g, query)]
        print(f"\nQ: {question}")
        print(f"LLM ({seconds:.1f} s): {answer.strip()}")
        print(f"Knowledge graph: {truth}")


if __name__ == "__main__":
    main()
