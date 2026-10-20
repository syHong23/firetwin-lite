"""Symbolic validation of LLM answers against the knowledge graph.

The LLM must return the IDs of the things it talks about. Each ID is checked:
- does it exist in the graph at all?  (otherwise: invented entity)
- does it satisfy the question?       (otherwise: wrong entity)
- is anything missing?                (otherwise: incomplete answer)

Feedback is explained with the ontology: the validator says WHAT a wrong entity is
(e.g. "a fire compartment", "a room in Compartment A1 containing smoke detector SD_101"),
so that the LLM understands why it must be removed.
"""
from pathlib import Path

from rdflib import RDF, RDFS, Graph, Namespace, URIRef

ROOT = Path(__file__).resolve().parents[2]
VALIDATION_QUERIES = ROOT / "queries" / "validation"
BASE = "https://example.org/firetwin/building#"
BOT = Namespace("https://w3id.org/bot#")
FTL = Namespace("https://example.org/firetwin#")

# Most specific class first: the first match names the entity.
KINDS = [
    (FTL.Room, "room"), (FTL.Corridor, "corridor"), (FTL.Stairwell, "stairwell"),
    (FTL.FireCompartment, "fire compartment"), (FTL.EvacuationExit, "evacuation exit"),
    (FTL.FireDoor, "fire door"), (FTL.SmokeDetector, "smoke detector"),
    (FTL.HeatDetector, "heat detector"), (FTL.ManualCallPoint, "manual call point"),
    (BOT.Storey, "storey"), (BOT.Building, "building"),
]
SPACE_CLASSES = {FTL.Room, FTL.Corridor, FTL.Stairwell}


def node(entity_id: str) -> URIRef:
    return URIRef(BASE + entity_id)


def short(n) -> str:
    return str(n).replace(BASE, "")


def kind(g: Graph, n) -> str:
    types = set(g.objects(n, RDF.type))
    return next((name for cls, name in KINDS if cls in types), "entity")


def describe(g: Graph, entity_id: str) -> str:
    """Explain what an entity is, using the ontology and the building data."""
    n = node(entity_id)
    name = kind(g, n)
    article = "an" if name[0] in "aeiou" else "a"
    text = f"{entity_id} is {article} {name}"
    if set(g.objects(n, RDF.type)) & SPACE_CLASSES:
        comp = g.value(n, FTL.inCompartment)
        if comp is not None:
            text += f" in {g.value(comp, RDFS.label) or short(comp)}"
        equipment = sorted(f"{kind(g, e)} {short(e)}" for e in g.objects(n, BOT.containsElement))
        text += f" containing {', '.join(equipment)}" if equipment else " with no equipment"
    elif name == "evacuation exit":
        space = g.value(n, FTL.exitFrom)
        if space is not None:
            text += f" leading outside from {short(space)}"
    return text


def expected_ids(g: Graph, query_name: str | None) -> set[str]:
    """IDs that a correct answer must contain (empty for trap questions)."""
    if query_name is None:
        return set()
    text = (VALIDATION_QUERIES / f"{query_name}.rq").read_text(encoding="utf-8")
    return {short(row[0]) for row in g.query(text)}


def exists(g: Graph, entity_id: str) -> bool:
    return (node(entity_id), None, None) in g


def check(g: Graph, answer_ids: list[str], query_name: str | None) -> list[str]:
    """Return a list of problems; an empty list means the answer is valid."""
    expected = expected_ids(g, query_name)
    given = set(answer_ids)
    problems = []
    for entity_id in sorted(given - expected):
        if exists(g, entity_id):
            problems.append(f"{describe(g, entity_id)}, so it does not answer the question: remove it.")
        else:
            problems.append(f"{entity_id} does not exist in the building: remove it.")
    for entity_id in sorted(expected - given):
        problems.append(f"{describe(g, entity_id)}, and it is missing: add it.")
    return problems
