"""Symbolic validation of LLM answers against the knowledge graph.

The LLM must return the IDs of the things it talks about. Each ID is checked:
- does it exist in the graph at all?  (otherwise: invented entity)
- does it satisfy the question?       (otherwise: wrong entity)
- is anything missing?                (otherwise: incomplete answer)
"""
from pathlib import Path

from rdflib import Graph, URIRef

ROOT = Path(__file__).resolve().parents[2]
VALIDATION_QUERIES = ROOT / "queries" / "validation"
BASE = "https://example.org/firetwin/building#"


def expected_ids(g: Graph, query_name: str | None) -> set[str]:
    """IDs that a correct answer must contain (empty for trap questions)."""
    if query_name is None:
        return set()
    text = (VALIDATION_QUERIES / f"{query_name}.rq").read_text(encoding="utf-8")
    return {str(row[0]).replace(BASE, "") for row in g.query(text)}


def exists(g: Graph, entity_id: str) -> bool:
    return (URIRef(BASE + entity_id), None, None) in g


def check(g: Graph, answer_ids: list[str], query_name: str | None) -> list[str]:
    """Return a list of problems; an empty list means the answer is valid."""
    expected = expected_ids(g, query_name)
    given = set(answer_ids)
    problems = []
    for entity_id in sorted(given - expected):
        if exists(g, entity_id):
            problems.append(f"{entity_id} does not satisfy the question.")
        else:
            problems.append(f"{entity_id} does not exist in the building.")
    for entity_id in sorted(expected - given):
        problems.append(f"{entity_id} is missing from the answer.")
    return problems
