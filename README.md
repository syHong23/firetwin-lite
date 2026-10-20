# FireTwin-Lite

Ontology-grounded LLM agents for fire safety in a small building: a scaled-down prototype of neuro-symbolic decision support for building digital twins.

The idea: an LLM should not decide alone. Its answers about a building (where are the detectors? which exit is safe?) are grounded in a knowledge graph and **checked by symbolic rules before they are used**.

## Roadmap

- [x] **Stage 1 – Knowledge graph**: fire-safety ontology on top of BOT and SOSA, a two-storey building, SPARQL queries, OWL 2 RL reasoning, six SHACL rules
- [x] **Stage 2 – Grounded LLM**: local open-weight LLM (Ollama), grounding in knowledge-graph facts, ontology-aware symbolic validation of answers, evaluation (LLM only vs grounded vs grounded + validated)
- [ ] **Stage 3 – Agents and platform**: LangGraph agents (evacuation, maintenance), simulated detectors over MQTT, FastAPI, Docker Compose

## Stage 1: what it does

| File | Content |
|---|---|
| `ontology/firetwin.ttl` | Fire-safety classes (rooms, corridors, stairwells, compartments, smoke/heat detectors, call points, fire doors, exits) aligned with BOT and SOSA |
| `ontology/building.ttl` | A two-storey office building; Room 103 deliberately lacks a smoke detector |
| `queries/*.rq` | SPARQL questions about the building |
| `shapes/fire_rules.ttl` | Six simplified fire-safety rules in SHACL and SHACL-SPARQL |
| `src/firetwin/kg.py` | Load, reason (OWL 2 RL), query, validate |
| `tests/` | Tests that check the building and deliberately break it to confirm each rule catches the problem |

Reasoning matters: the data never states that a smoke detector is a `sosa:Sensor`; this is inferred from the ontology (162 triples before reasoning, 556 after).

### Rules

| # | Rule | Type |
|---|---|---|
| 1 | Every room contains a smoke detector | SHACL |
| 2 | Every storey has a manual call point | SHACL (property path) |
| 3 | A space belongs to at most one compartment | SHACL |
| 4 | Every stairwell (escape route) contains a smoke detector | SHACL |
| 5 | A fire compartment stays on one storey, except the protected stairwell | SHACL-SPARQL |
| 6 | Connected spaces in different compartments are separated by a fire door | SHACL-SPARQL |

### How the model was improved

The first version of the building was deliberately simple. Rules were then added one at a time, each revealing a modelling problem that was fixed in the data:

1. Stairwells had no compartment and no detector → modelled as a protected stairwell compartment with smoke detectors (rule 4).
2. Compartments spanned two storeys → split per storey; the stairwell is kept as a vertical exception (rule 5).
3. Compartments had no separation → fire doors added and linked to spaces with BOT's `bot:adjacentElement` (rule 6).

## Stage 2: evaluation

30 questions (24 answerable, 6 traps about things that do not exist), three conditions, `llama3.1:8b` via Ollama, temperature 0. An answer is valid when its IDs exactly match the IDs returned by SPARQL. Run with `python -m firetwin.evaluate`; results in `docs/eval_summary.md` and `docs/eval_results.csv`.

| Condition | Valid (all) | Valid (answerable) | Valid (traps) | Invented IDs | Wrong IDs | Missing IDs | Mean time (s) |
|---|---|---|---|---|---|---|---|
| A. LLM only | 5/30 | 1/24 | 4/6 | 22 | 11 | 48 | 5.2 |
| B. Grounded | 23/30 | 17/24 | 6/6 | 0 | 7 | 2 | 3.0 |
| C. Grounded + validated | 27/30 | 21/24 | 6/6 | 0 | 3 | 0 | 3.7 |

**Findings.** Without data, the LLM invented rooms such as "Meeting Room" and "Break Room". Grounding removed all invented entities but meaning errors remained. Ontology-aware validation with one feedback round fixed four more answers at a cost of 0.7 s per question.

**Remaining failures.** Confusing connection or storey with compartment membership (Q01), keeping a wrong item despite an explained correction (Q10), and confusing an exit with a room (Q24). Possible next steps: constrain outputs by ontology type, or let the LLM generate SPARQL instead of answers.

**Limitations.** One model, one run, one feedback round, a small synthetic building; ground truth and facts come from the same knowledge graph.

## Run

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m pip install -e .
python -m firetwin.stage1
pytest
```

Expected SHACL result: one violation, `Room103: Room without a smoke detector.` Tests: `8 passed`.

## Data and sources

**Building data is synthetic.** `ontology/building.ttl` describes a fictional two-storey office building created for this project to illustrate the approach. It does not come from a real building, BIM model or sensor installation.

**AI assistance.** The example building and the initial code scaffold were created with the assistance of an AI tool, then reviewed and extended by the author.

**Fire-safety rules are simplified.** `shapes/fire_rules.ttl` contains illustrative rules written for learning purposes. They are not taken from, and do not reproduce, EN 54 or NF S 61-93x.

**Standards reused** (namespaces as published by their maintainers):

| Standard | Maintainer | Namespace | Reference |
|---|---|---|---|
| BOT – Building Topology Ontology | W3C Linked Building Data Community Group | `https://w3id.org/bot#` | https://w3id.org/bot · Rasmussen, Lefrançois, Schneider et al., "BOT: the Building Topology Ontology of the W3C Linked Building Data Group", *Semantic Web*, 2021 |
| SOSA/SSN – Semantic Sensor Network Ontology | W3C & OGC (Spatial Data on the Web WG) | `http://www.w3.org/ns/sosa/` | W3C Recommendation, 19 October 2017: https://www.w3.org/TR/vocab-ssn/ |
| SHACL – Shapes Constraint Language | W3C (RDF Data Shapes WG) | `http://www.w3.org/ns/shacl#` | W3C Recommendation, 20 July 2017: https://www.w3.org/TR/shacl/ |

**Software:** rdflib (RDF and SPARQL), owlrl (OWL 2 RL reasoning), pySHACL (SHACL validation).

**Possible extension:** real building models in IFC format could be converted to BOT with the open-source IFCtoLBD converter (https://github.com/jyrkioraskari/IFCtoLBD).
