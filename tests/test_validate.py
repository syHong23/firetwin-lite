"""Tests for the symbolic validator (no LLM needed)."""
from firetwin.kg import load_graph
from firetwin.validate import check


def test_valid_answer_has_no_problem():
    assert check(load_graph(), ["Corridor1", "Room102", "Room103"], "spaces_in_compartment_b1") == []


def test_wrong_entity_is_caught():
    # The error made by the LLM in the grounded experiment
    problems = check(load_graph(), ["Corridor1", "Room101", "Room102", "Room103"], "spaces_in_compartment_b1")
    assert problems == ["Room101 does not satisfy the question."]


def test_invented_entity_is_caught():
    problems = check(load_graph(), ["Room104"], "rooms_without_smoke_detector")
    assert "Room104 does not exist in the building." in problems


def test_missing_entity_is_caught():
    assert check(load_graph(), [], "exits") == [
        "ExitEast is missing from the answer.", "ExitMain is missing from the answer."]


def test_trap_question_expects_no_entity():
    assert check(load_graph(), [], None) == []
