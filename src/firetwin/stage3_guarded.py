"""Stage 3, step 3: the evacuation agent inside a LangGraph graph with a guard node.

  agent node : the ReAct agent of stage3_agent (LLM + tools), with a limit on steps
  guard node : checks the final answer against the last tool result (firetwin.guard);
               if it is not faithful, the tool result is delivered instead
Every decision is appended to docs/audit_log.jsonl (question, tool calls, tool result,
LLM answer, problems, delivered answer).

Usage (Ollama running):  python -m firetwin.stage3_guarded
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph

from firetwin.guard import check_answer
from firetwin.stage3_agent import SCENARIOS, build_agent

ROOT = Path(__file__).resolve().parents[2]
AUDIT_LOG = ROOT / "docs" / "audit_log.jsonl"
MAX_AGENT_STEPS = 8  # stops endless tool calls
REACT_AGENT = build_agent()


class State(TypedDict, total=False):
    question: str
    tool_calls: list
    tool_result: str
    llm_answer: str
    problems: list
    delivered: str


def agent_node(state: State) -> State:
    calls, tool_result, answer = [], "", ""
    try:
        result = REACT_AGENT.invoke({"messages": [("user", state["question"])]},
                                    config={"recursion_limit": MAX_AGENT_STEPS})
        for message in result["messages"]:
            calls += [{"name": c["name"], "args": c["args"]} for c in getattr(message, "tool_calls", []) or []]
            if message.type == "tool" and message.name == "evacuation_route":
                tool_result = message.content
        answer = result["messages"][-1].content
    except GraphRecursionError:
        answer = "(the agent stopped: too many steps)"
    return {"tool_calls": calls, "tool_result": tool_result, "llm_answer": answer}


def guard_node(state: State) -> State:
    if not state["tool_result"]:
        problems = ["no route was computed by the tool"]
        delivered = "No verified route is available. Follow the fire alarm instructions and call the fire brigade (112)."
    else:
        problems = check_answer(state["tool_result"], state["llm_answer"])
        delivered = state["llm_answer"] if not problems else state["tool_result"]
    return {"problems": problems, "delivered": delivered}


def audit_node(state: State) -> State:
    AUDIT_LOG.parent.mkdir(exist_ok=True)
    entry = {"time": datetime.now(timezone.utc).isoformat(timespec="seconds"), **state,
             "faithful": not state["problems"]}
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return {}


def build_graph():
    graph = StateGraph(State)
    graph.add_node("agent", agent_node)
    graph.add_node("guard", guard_node)
    graph.add_node("audit", audit_node)
    graph.add_edge(START, "agent")
    graph.add_edge("agent", "guard")
    graph.add_edge("guard", "audit")
    graph.add_edge("audit", END)
    return graph.compile()


def main() -> None:
    app = build_graph()
    faithful = 0
    for scenario in SCENARIOS:
        state = app.invoke({"question": scenario})
        faithful += not state["problems"]
        print(f"\nUSER: {scenario}")
        print(f"  Tool result : {state['tool_result']}")
        print(f"  LLM answer  : {state['llm_answer']}")
        print(f"  Guard       : {'faithful' if not state['problems'] else state['problems']}")
        print(f"  DELIVERED   : {state['delivered']}")
    print(f"\nFaithful LLM answers: {faithful}/{len(SCENARIOS)}; delivered answers are all verified.")
    print(f"Audit log: {AUDIT_LOG}")


if __name__ == "__main__":
    main()
