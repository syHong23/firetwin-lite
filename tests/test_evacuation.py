"""Evacuation routes on the example building (no LLM)."""
from firetwin.evacuation import exit_spaces, route
from firetwin.kg import load_graph


def test_exit_spaces():
    assert exit_spaces(load_graph()) == {"Lobby", "Corridor0"}


def test_no_fire_takes_shortest_route():
    assert route(load_graph(), "Room103") == {
        "status": "exit", "path": ["Room103", "Corridor1", "Stair1", "Stair0", "Corridor0"]}


def test_fire_in_b1_occupant_leaves_its_own_compartment():
    # Room 103 is inside the burning compartment: it may cross it to get out
    result = route(load_graph(), "Room103", fire_compartment="CompB1")
    assert result == {"status": "exit", "path": ["Room103", "Corridor1", "Stair1", "Stair0", "Corridor0"]}


def test_fire_in_b1_room101_is_cut_off():
    # Room 101 is only connected to Corridor 1, which is on fire
    assert route(load_graph(), "Room101", fire_compartment="CompB1") == {"status": "trapped", "path": ["Room101"]}


def test_fire_in_a0_room002_is_cut_off():
    # Room 002 (compartment B0) only opens onto Corridor 0, which is on fire
    assert route(load_graph(), "Room002", fire_compartment="CompA0")["status"] == "trapped"


def test_fire_in_a0_both_exits_are_lost():
    # Both exits are in compartment A0: first-floor occupants can only reach the protected stairwell
    result = route(load_graph(), "Room102", fire_compartment="CompA0")
    assert result == {"status": "refuge", "path": ["Room102", "Corridor1", "Stair1"]}
