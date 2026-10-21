"""Stage 3, step 2: an evacuation agent (LangGraph ReAct agent with tool calling).

The LLM decides which tool to call and explains the result; the route itself
is computed by the symbolic tool from the knowledge graph.

Usage (Ollama running):  python -m firetwin.stage3_agent
"""
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

from firetwin.agent_tools import evacuation_route, space_info
from firetwin.llm import DEFAULT_MODEL

INSTRUCTIONS = """You are an evacuation assistant for one office building.
Never invent a route: always call the evacuation_route tool and report its result faithfully.
Identifiers look like Room103, Corridor1, CompB1 (fire compartments are CompA0, CompB0, CompA1, CompB1).
Answer in at most three short sentences."""

SCENARIOS = [
    "Fire in compartment CompB1. I am in Room103. How do I get out?",
    "Fire in compartment CompB1. I am in Room101. What should I do?",
    "Fire in compartment CompA0. I am in Room102. Where should I go?",
    "There is no fire. What is the way out from Room001?",
]


def build_agent():
    model = ChatOllama(model=DEFAULT_MODEL, temperature=0)
    return create_react_agent(model, [evacuation_route, space_info], state_modifier=INSTRUCTIONS)


def main() -> None:
    agent = build_agent()
    for scenario in SCENARIOS:
        print(f"\nUSER: {scenario}")
        result = agent.invoke({"messages": [("user", scenario)]})
        for message in result["messages"][1:]:
            for call in getattr(message, "tool_calls", []) or []:
                print(f"  TOOL CALL   {call['name']}({call['args']})")
            if message.type == "tool":
                print(f"  TOOL RESULT {message.content}")
        print(f"AGENT: {result['messages'][-1].content}")


if __name__ == "__main__":
    main()
