"""Stage 1 building blocks: load the knowledge graph, reason, query and validate."""
from pathlib import Path

import owlrl
from pyshacl import validate
from rdflib import Graph

ROOT = Path(__file__).resolve().parents[2]
ONTOLOGY = ROOT / "ontology" / "firetwin.ttl"
BUILDING = ROOT / "ontology" / "building.ttl"
SHAPES = ROOT / "shapes" / "fire_rules.ttl"
QUERIES = ROOT / "queries"


def load_graph(reason: bool = True) -> Graph:
    """Load ontology + building data. With reason=True, apply OWL 2 RL inference
    (e.g. a SmokeDetector is also a sosa:Sensor)."""
    g = Graph()
    g.parse(ONTOLOGY)
    g.parse(BUILDING)
    if reason:
        owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)
    return g


def run_query(g: Graph, name: str) -> list[tuple]:
    """Run a SPARQL query stored in queries/<name>.rq and return rows as tuples of strings."""
    text = (QUERIES / f"{name}.rq").read_text(encoding="utf-8")
    return [tuple(str(v) for v in row) for row in g.query(text)]


def check_rules(g: Graph) -> tuple[bool, list[str]]:
    """Validate the graph against the SHACL fire-safety rules.
    Returns (conforms, list of 'focus node: message')."""
    shapes = Graph().parse(SHAPES)
    conforms, report, _ = validate(g, shacl_graph=shapes, inference="none")
    query = """
    PREFIX sh: <http://www.w3.org/ns/shacl#>
    SELECT ?node ?msg WHERE { ?r a sh:ValidationResult ; sh:focusNode ?node ; sh:resultMessage ?msg . }
    ORDER BY ?node
    """
    problems = [f"{node.split('#')[-1]}: {msg}" for node, msg in report.query(query)]
    return conforms, problems
