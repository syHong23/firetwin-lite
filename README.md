# FireTwin-Lite

Ontology-grounded LLM agents for fire safety in a small building: a scaled-down prototype of neuro-symbolic decision support for building digital twins.

The idea: an LLM should not decide alone. Its answers about a building (where are the detectors? which exit is safe?) are grounded in a knowledge graph and **checked by symbolic rules before they are used**.

## Roadmap

- [x] **Stage 1 – Knowledge graph**: fire-safety ontology on top of BOT and SOSA, a two-storey building, SPARQL queries, OWL 2 RL reasoning, SHACL rules
- [ ] **Stage 2 – Grounded LLM**: local open-weight LLM (Ollama), knowledge-graph RAG, symbolic validation of answers, evaluation (LLM only vs RAG vs RAG + validation)
- [ ] **Stage 3 – Agents and platform**: LangGraph agents (evacuation, maintenance), simulated detectors over MQTT, FastAPI, Docker Compose

## Stage 1: what it does

| File | Content |
|---|---|
| `ontology/firetwin.ttl` | Fire-safety classes (rooms, compartments, smoke/heat detectors, call points, exits) aligned with BOT and SOSA |
| `ontology/building.ttl` | A two-storey office building; Room 103 deliberately lacks a smoke detector |
| `queries/*.rq` | SPARQL questions about the building |
| `shapes/fire_rules.ttl` | Simplified fire-safety rules in SHACL (not the text of any standard) |
| `src/firetwin/kg.py` | Load, reason (OWL 2 RL), query, validate |

Reasoning matters: the data never states that a smoke detector is a `sosa:Sensor`; this is inferred from the ontology (131 triples before reasoning, 473 after).

## Run

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m pip install -e .
python -m firetwin.stage1
pytest
```

Expected SHACL result: one violation, `Room103: Room without a smoke detector.`

## Standards used

- BOT – Building Topology Ontology (W3C Linked Building Data CG): https://w3id.org/bot
- SOSA/SSN – Semantic Sensor Network Ontology (W3C): http://www.w3.org/ns/sosa/
- SHACL – Shapes Constraint Language (W3C)
