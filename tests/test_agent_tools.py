"""The agent tools answer from the knowledge graph (no LLM needed)."""
from firetwin.agent_tools import evacuation_route, space_info


def test_route_tool_exit():
    assert evacuation_route.invoke({"space_id": "Room103", "fire_compartment": "CompB1"}) == (
        "EXIT: follow Room103 -> Corridor1 -> Stair1 -> Stair0 -> Corridor0, then leave the building.")


def test_route_tool_trapped():
    assert evacuation_route.invoke({"space_id": "Room101", "fire_compartment": "CompB1"}).startswith("TRAPPED")


def test_route_tool_refuge():
    assert evacuation_route.invoke({"space_id": "Room102", "fire_compartment": "CompA0"}).startswith("REFUGE")


def test_route_tool_rejects_unknown_space():
    assert evacuation_route.invoke({"space_id": "MeetingRoom"}).startswith("Unknown space")


def test_space_info_tool():
    assert space_info.invoke({"space_id": "Room103"}) == (
        "Room103 is a room in Compartment B1 (first, east) containing heat detector HD_103.")
