"""Tests for stage 1: the knowledge graph, OWL reasoning and the SHACL rules.

The first tests check the building as it is (only Room 103 breaks a rule).
The rule tests deliberately break the data and check that each rule catches it.
"""
import owlrl
from rdflib import Namespace, RDF

from firetwin.kg import check_rules, load_graph, run_query

BOT = Namespace("https://w3id.org/bot#")
FTL = Namespace("https://example.org/firetwin#")
B = Namespace("https://example.org/firetwin/building#")


def reason(g):
    """Apply OWL 2 RL reasoning to a graph that was modified by a test."""
    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)
    return g


# ---------- The building as it is ----------

def test_room_without_smoke_detector_is_found():
    rows = run_query(load_graph(), "rooms_without_smoke_detector")
    assert [label for _, label in rows] == ["Room 103"]


def test_reasoning_infers_sensors():
    assert run_query(load_graph(reason=False), "all_sensors") == []
    assert len(run_query(load_graph(reason=True), "all_sensors")) == 11


def test_shacl_flags_only_room_103():
    conforms, problems = check_rules(load_graph())
    assert not conforms
    assert problems == ["Room103: Room without a smoke detector."]


# ---------- Each rule catches a deliberately broken building ----------

def test_rule2_storey_without_call_point():
    g = load_graph(reason=False)
    g.remove((B.Corridor1, BOT.containsElement, B.MCP_1))
    _, problems = check_rules(reason(g))
    assert "S1: Storey without a manual call point." in problems


def test_rule4_stairwell_without_smoke_detector():
    g = load_graph(reason=False)
    g.remove((B.Stair0, BOT.containsElement, B.SD_S0))
    _, problems = check_rules(reason(g))
    assert "Stair0: Stairwell without a smoke detector." in problems


def test_rule5_compartment_spanning_storeys():
    g = load_graph(reason=False)
    g.remove((B.Room101, FTL.inCompartment, B.CompA1))
    g.add((B.Room101, FTL.inCompartment, B.CompA0))  # first-floor room in a ground-floor compartment
    _, problems = check_rules(reason(g))
    assert "CompA0: Fire compartment spans several storeys." in problems


def test_rule5_ignores_the_protected_stairwell():
    _, problems = check_rules(load_graph())
    assert not any(p.startswith("CompStair") for p in problems)


def test_rule6_missing_fire_door():
    g = load_graph(reason=False)
    g.remove((B.FD_101, RDF.type, FTL.FireDoor))
    _, problems = check_rules(reason(g))
    assert "Corridor1: Connection to Room101 crosses compartments without a fire door." in problems
