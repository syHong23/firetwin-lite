"""Turn the knowledge graph into short plain-English facts for an LLM prompt.

The building is small, so all facts fit in one prompt. For a large building,
only the facts relevant to the question would be retrieved (that is RAG).
"""
from rdflib import RDF, RDFS, Graph, Namespace

BOT = Namespace("https://w3id.org/bot#")
FTL = Namespace("https://example.org/firetwin#")

SPACE_TYPES = {FTL.Room: "room", FTL.Corridor: "corridor", FTL.Stairwell: "stairwell"}
ELEMENT_NAMES = {
    FTL.SmokeDetector: "smoke detector",
    FTL.HeatDetector: "heat detector",
    FTL.ManualCallPoint: "manual call point",
    FTL.EvacuationExit: "evacuation exit",
}


def short(node) -> str:
    """Local name of an IRI, e.g. ...#SD_101 -> SD_101."""
    return str(node).split("#")[-1]


def label(g: Graph, node) -> str:
    value = g.value(node, RDFS.label)
    return str(value) if value else short(node)


def build_facts(g: Graph) -> str:
    """Describe storeys, spaces, equipment, fire doors and exits, one fact per line.
    Use the graph WITHOUT reasoning, so that each element keeps its most specific type."""
    lines = []
    for building in g.subjects(RDF.type, BOT.Building):
        storeys = sorted(label(g, s) for s in g.objects(building, BOT.hasStorey))
        lines.append(f"Building: {label(g, building)}. Storeys: {', '.join(storeys)}.")

    for storey in sorted(g.subjects(RDF.type, BOT.Storey), key=str):
        for space in sorted(g.objects(storey, BOT.hasSpace), key=lambda s: label(g, s)):
            kind = next((SPACE_TYPES[t] for t in g.objects(space, RDF.type) if t in SPACE_TYPES), "space")
            comp = g.value(space, FTL.inCompartment)
            fact = f"- {label(g, space)} ({short(space)}) is a {kind} on the {label(g, storey)}"
            fact += f", in {label(g, comp)} ({short(comp)})." if comp else "."
            equipment = []
            for element in sorted(g.objects(space, BOT.containsElement), key=str):
                name = next((ELEMENT_NAMES[t] for t in g.objects(element, RDF.type) if t in ELEMENT_NAMES), "element")
                equipment.append(f"{name} {short(element)}")
            fact += f" Contains: {', '.join(equipment)}." if equipment else " Contains no equipment."
            neighbours = set(g.objects(space, FTL.connectsTo)) | set(g.subjects(FTL.connectsTo, space))
            fact += f" Connected to: {', '.join(sorted(label(g, n) for n in neighbours))}."
            lines.append(fact)

    for door in sorted(g.subjects(RDF.type, FTL.FireDoor), key=str):
        spaces = sorted(label(g, s) for s in g.subjects(BOT.adjacentElement, door))
        lines.append(f"- Fire door {short(door)} separates {' and '.join(spaces)}.")
    for exit_ in sorted(g.subjects(RDF.type, FTL.EvacuationExit), key=str):
        lines.append(f"- {label(g, exit_)} ({short(exit_)}) leads outside from {label(g, g.value(exit_, FTL.exitFrom))}.")
    lines.append("Only the spaces and equipment listed above exist in this building.")
    return "\n".join(lines)
