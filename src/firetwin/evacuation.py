"""Evacuation routes computed from the knowledge graph (no LLM).

Spaces are nodes, ftl:connectsTo links are edges. When a fire compartment is on fire,
its spaces are avoided, unless the occupant starts inside it: then the occupant
must be allowed to move through it to get out. Fire doors are not modelled as obstacles:
a closed fire door is crossed normally by occupants.

Result for one occupant:
  "exit"    : a route to a space with an evacuation exit, avoiding the fire
  "refuge"  : no safe exit, but a route to the protected stairwell (wait for rescue)
  "trapped" : neither is reachable without crossing the fire
"""
import networkx as nx
from rdflib import RDF, Graph, Namespace

FTL = Namespace("https://example.org/firetwin#")
BASE = "https://example.org/firetwin/building#"
REFUGE_COMPARTMENT = "CompStair"


def short(n) -> str:
    return str(n).replace(BASE, "")


def space_network(g: Graph) -> nx.Graph:
    """Undirected graph of spaces; each node knows its compartment."""
    net = nx.Graph()
    for a, b in g.subject_objects(FTL.connectsTo):
        net.add_edge(short(a), short(b))
    for space, comp in g.subject_objects(FTL.inCompartment):
        if short(space) in net:
            net.nodes[short(space)]["compartment"] = short(comp)
    return net


def exit_spaces(g: Graph) -> set[str]:
    return {short(s) for e in g.subjects(RDF.type, FTL.EvacuationExit) for s in g.objects(e, FTL.exitFrom)}


def route(g: Graph, start: str, fire_compartment: str | None = None) -> dict:
    """Safest route from a space, given the compartment on fire (or None)."""
    net = space_network(g)
    inside_fire = net.nodes[start].get("compartment") == fire_compartment
    blocked = set() if inside_fire else {
        n for n, d in net.nodes(data=True) if d.get("compartment") == fire_compartment}
    safe = net.subgraph(n for n in net if n not in blocked)
    exits = exit_spaces(g) - blocked
    refuges = {n for n, d in safe.nodes(data=True) if d.get("compartment") == REFUGE_COMPARTMENT}

    for status, targets in (("exit", exits), ("refuge", refuges)):
        paths = [nx.shortest_path(safe, start, t) for t in targets if t in safe and nx.has_path(safe, start, t)]
        if paths:
            return {"status": status, "path": min(paths, key=len)}
    return {"status": "trapped", "path": [start]}
