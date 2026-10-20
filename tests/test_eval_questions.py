"""Check the evaluation questions themselves (no LLM needed)."""
from firetwin.eval_questions import build_questions
from firetwin.kg import load_graph
from firetwin.validate import ids_from_sparql


def test_thirty_questions_with_unique_ids():
    questions = build_questions()
    assert len(questions) == 30
    assert len({q["id"] for q in questions}) == 30


def test_traps_have_no_query_and_others_do():
    for q in build_questions():
        assert (q["sparql"] is None) == (q["category"] == "trap")


def test_every_query_runs():
    g = load_graph()
    for q in build_questions():
        ids_from_sparql(g, q["sparql"])  # raises if a query is malformed


def test_known_answers():
    g = load_graph()
    by_text = {q["question"]: q for q in build_questions()}
    assert ids_from_sparql(g, by_text["Which spaces are in fire compartment B1?"]["sparql"]) == {"Corridor1", "Room102", "Room103"}
    assert ids_from_sparql(g, by_text["Which rooms contain an evacuation exit?"]["sparql"]) == {"Lobby"}
