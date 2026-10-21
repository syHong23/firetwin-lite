"""Safety guard for agent answers: the final answer must faithfully report the tool result.

Symbolic checks, no LLM:
- the answer must keep the decision of the tool (exit / refuge / trapped),
- every space of the route must appear in the answer,
- some claims are forbidden because no tool can produce them (e.g. "the fire is out").
If a check fails, the tool result is delivered instead of the LLM answer.
"""
import re

FORBIDDEN = ["extinguished", "fire is out", "return to", "safe to go back", "situation has not changed"]
REQUIRED_WORDS = {"EXIT": ["leave"], "REFUGE": ["wait"], "TRAPPED": ["stay"]}


def parse_tool_result(tool_result: str) -> tuple[str, list[str]]:
    """Return the status (EXIT, REFUGE, TRAPPED) and the spaces named in the tool result."""
    status = tool_result.split(":", 1)[0].strip()
    spaces = re.findall(r"\b(?:Room|Corridor|Stair|Lobby)\w*", tool_result)
    return status, list(dict.fromkeys(spaces))


def check_answer(tool_result: str, answer: str) -> list[str]:
    """Problems found in the answer; an empty list means it is faithful."""
    status, spaces = parse_tool_result(tool_result)
    text = answer.lower()
    problems = [f"forbidden claim: '{p}'" for p in FORBIDDEN if p in text]
    problems += [f"missing space {s} of the route" for s in spaces if s.lower() not in text]
    problems += [f"missing instruction '{w}' for the {status} decision"
                 for w in REQUIRED_WORDS.get(status, []) if w not in text]
    return problems
