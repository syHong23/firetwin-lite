"""API tests for the symbolic endpoints (no LLM needed)."""
from fastapi.testclient import TestClient

from firetwin.api import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_space_description():
    response = client.get("/spaces/Room103")
    assert response.status_code == 200
    assert response.json()["description"].startswith("Room103 is a room")


def test_unknown_space_is_404():
    assert client.get("/spaces/MeetingRoom").status_code == 404


def test_route_with_fire():
    body = client.get("/route", params={"space": "Room102", "fire": "CompA0"}).json()
    assert body["status"] == "refuge"
    assert body["path"] == ["Room102", "Corridor1", "Stair1"]


def test_rules_report_room_103():
    assert client.get("/rules").json() == {"conforms": False, "problems": ["Room103: Room without a smoke detector."]}
