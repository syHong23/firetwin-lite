"""Tests for the symbolic validator (no LLM needed)."""
from firetwin.kg import load_graph
from firetwin.validate import check, describe


def test_valid_answer_has_no_problem():
    assert check(load_graph(), ["Corridor1", "Room102", "Room103"], "spaces_in_compartment_b1") == []


def test_wrong_entity_is_caught_and_explained():
    # The error made by the LLM in the grounded experiment
    problems = check(load_graph(), ["Corridor1", "Room101", "Room102", "Room103"], "spaces_in_compartment_b1")
    assert len(problems) == 1
    assert problems[0].startswith("Room101 is a room in Compartment A1 (first, west)")
    assert problems[0].endswith("remove it.")


def test_context_entity_is_named_by_its_class():
    problems = check(load_graph(), ["CompB1", "Corridor1", "Room102", "Room103"], "spaces_in_compartment_b1")
    assert problems == ["CompB1 is a fire compartment, so it does not answer the question: remove it."]


def test_invented_entity_is_caught():
    problems = check(load_graph(), ["Room104"], "rooms_without_smoke_detector")
    assert "Room104 does not exist in the building: remove it." in problems


def test_missing_entity_is_caught():
    problems = check(load_graph(), [], "exits")
    assert problems == [
        "ExitEast is an evacuation exit leading outside from Corridor0, and it is missing: add it.",
        "ExitMain is an evacuation exit leading outside from Lobby, and it is missing: add it.",
    ]


def test_describe_lists_equipment():
    assert describe(load_graph(), "Room103") == "Room103 is a room in Compartment B1 (first, east) containing heat detector HD_103"


def test_trap_question_expects_no_entity():
    assert check(load_graph(), [], None) == []
