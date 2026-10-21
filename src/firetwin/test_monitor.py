"""Monitor logic on the simulated scenario (no MQTT broker needed)."""
from firetwin.monitor import Monitor, slope
from firetwin.simulate import scenario


def run_scenario(steps=40):
    monitor, events = Monitor(), []
    for r in scenario(steps):
        events += monitor.process(r)
    return events


def test_slope():
    assert slope([0, 1, 2, 3]) == 1.0


def test_fire_alarm_in_room_102():
    alarms = [e for e in run_scenario() if e["type"] == "fire_alarm"]
    assert len(alarms) == 1   # one alarm per burning compartment, not one per reading
    alarm = alarms[0]
    assert alarm["space"] == "Room102" and alarm["compartment"] == "CompB1"
    assert alarm["decisions"]["Room101"]["status"] == "trapped"
    assert alarm["decisions"]["Room103"]["status"] == "exit"


def test_drift_detected_as_maintenance_not_fire():
    events = run_scenario()
    maintenance = [e for e in events if e["type"] == "maintenance"]
    assert [e["detector"] for e in maintenance] == ["SD_C0"]
    assert not any(e["type"] == "fire_alarm" and e["detector"] == "SD_C0" for e in events)


def test_starting_fire_is_not_mistaken_for_drift():
    events = run_scenario()
    assert not any(e["type"] == "maintenance" and e["space"] == "Room102" for e in events)


def test_no_event_without_fire_or_drift():
    events = run_scenario(steps=5)
    assert events == []


def test_unknown_detector_is_reported():
    assert Monitor().process({"detector": "SD_999", "value": 1.0}) == [{"type": "unknown_detector", "detector": "SD_999"}]
