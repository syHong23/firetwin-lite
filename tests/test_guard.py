"""The guard compares an agent answer with the tool result (no LLM needed).
The unfaithful answers below are the ones produced by llama3.1:8b in the first agent run."""
from firetwin.guard import check_answer

REFUGE = "REFUGE: no safe exit. Go Room102 -> Corridor1 -> Stair1 (protected stairwell) and wait for the fire brigade."
TRAPPED = "TRAPPED: no safe route from Room101. Stay in Room101, keep the fire door closed and call for rescue."
EXIT = "EXIT: follow Room001 -> Corridor0, then leave the building."


def test_faithful_copy_passes():
    assert check_answer(EXIT, EXIT) == []


def test_faithful_paraphrase_passes():
    assert check_answer(EXIT, "Go from Room001 to Corridor0 and leave the building.") == []


def test_invented_all_clear_is_rejected():
    problems = check_answer(REFUGE, "The fire has been extinguished. You can return to Room102.")
    assert "forbidden claim: 'extinguished'" in problems
    assert "missing space Stair1 of the route" in problems


def test_missing_instruction_is_rejected():
    problems = check_answer(TRAPPED, "The situation has not changed.")
    assert "missing instruction 'stay' for the TRAPPED decision" in problems
