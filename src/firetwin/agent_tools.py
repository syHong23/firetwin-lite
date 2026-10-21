"""Tools that LLM agents may call. Every answer comes from the knowledge graph,
never from the LLM itself."""
from langchain_core.tools import tool

from firetwin.evacuation import route
from firetwin.kg import load_graph
from firetwin.validate import describe, exists

GRAPH = load_graph()


@tool
def evacuation_route(space_id: str, fire_compartment: str = "") -> str:
    """Compute the safest evacuation route for an occupant.

    space_id: identifier of the occupant's space, e.g. Room103 or Corridor1.
    fire_compartment: identifier of the compartment on fire, e.g. CompB1 or CompA0;
    empty string if there is no fire.
    """
    if not exists(GRAPH, space_id):
        return f"Unknown space {space_id}. Use identifiers such as Room103."
    result = route(GRAPH, space_id, fire_compartment or None)
    path = " -> ".join(result["path"])
    if result["status"] == "exit":
        return f"EXIT: follow {path}, then leave the building."
    if result["status"] == "refuge":
        return f"REFUGE: no safe exit. Go {path} (protected stairwell) and wait for the fire brigade."
    return f"TRAPPED: no safe route from {space_id}. Stay in {space_id}, keep the fire door closed and call for rescue."


@tool
def space_info(space_id: str) -> str:
    """Describe a space or element of the building: its type, compartment and equipment.

    space_id: identifier such as Room103, Corridor1, CompB1 or ExitMain.
    """
    if not exists(GRAPH, space_id):
        return f"{space_id} does not exist in the building."
    return describe(GRAPH, space_id) + "."
