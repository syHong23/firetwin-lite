"""REST API for FireTwin-Lite (FastAPI).

Symbolic endpoints (no LLM): /health, /spaces/{id}, /route, /rules
Agent endpoint (needs Ollama): POST /ask  -> guarded agent with audit log

Run:  uvicorn firetwin.api:app --reload      then open http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from firetwin.evacuation import route
from firetwin.kg import check_rules, load_graph
from firetwin.validate import describe, exists

app = FastAPI(title="FireTwin-Lite", version="0.3.0",
              description="Ontology-grounded fire-safety assistant for a small building.")
GRAPH = load_graph()


class Question(BaseModel):
    question: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "triples": len(GRAPH)}


@app.get("/spaces/{space_id}")
def space(space_id: str) -> dict:
    if not exists(GRAPH, space_id):
        raise HTTPException(status_code=404, detail=f"{space_id} does not exist in the building")
    return {"id": space_id, "description": describe(GRAPH, space_id)}


@app.get("/route")
def evacuation_route(space: str, fire: str | None = None) -> dict:
    """Safest route from a space, avoiding the compartment on fire (computed, not generated)."""
    if not exists(GRAPH, space):
        raise HTTPException(status_code=404, detail=f"{space} does not exist in the building")
    if fire and not exists(GRAPH, fire):
        raise HTTPException(status_code=404, detail=f"{fire} does not exist in the building")
    return {"space": space, "fire_compartment": fire, **route(GRAPH, space, fire)}


@app.get("/rules")
def rules() -> dict:
    """Validate the building against the SHACL fire-safety rules."""
    conforms, problems = check_rules(GRAPH)
    return {"conforms": conforms, "problems": problems}


@app.post("/ask")
def ask(body: Question) -> dict:
    """Ask the guarded evacuation agent (requires Ollama). Every call is written to the audit log."""
    from firetwin.stage3_guarded import build_graph  # imported here: only this endpoint needs the LLM
    state = build_graph().invoke({"question": body.question})
    return {"answer": state["delivered"], "faithful_llm_answer": not state["problems"],
            "problems": state["problems"], "tool_result": state["tool_result"],
            "llm_answer": state["llm_answer"]}
