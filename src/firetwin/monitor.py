"""Monitor of detector readings: fire alarms and predictive maintenance.

The decision logic (class Monitor) is independent of MQTT, so it can be tested
without a broker. The main() function connects it to the MQTT broker.

- Fire alarm: a detector above its alarm threshold for 2 consecutive readings.
  The knowledge graph gives the detector's space and compartment; evacuation
  decisions for every room are computed symbolically (no LLM).
- Sensor drift: a slow, steady rise of a detector that never reaches the alarm
  threshold (slope over the last readings), reported as a maintenance need.
  An early fire also rises, but fast: a reading jump larger than MAX_DRIFT_STEP
  rules out drift, so a starting fire is never filed as maintenance.
Every event is appended to docs/audit_log.jsonl.

Usage:  python -m firetwin.monitor     (needs an MQTT broker, see docker-compose.yml)
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from rdflib import RDF

from firetwin.evacuation import FTL, route
from firetwin.kg import load_graph
from firetwin.sensors import ALARM_THRESHOLD, BASELINE, MQTT_HOST, MQTT_PORT, TOPIC_PREFIX, detectors

ROOT = Path(__file__).resolve().parents[2]
AUDIT_LOG = ROOT / "docs" / "audit_log.jsonl"
CONSECUTIVE = 2       # readings above threshold before an alarm
DRIFT_WINDOW = 12     # readings used to estimate the slope
DRIFT_SLOPE = {"smoke": 0.12, "heat": 0.4}   # rise per reading that indicates drift
# A fire also starts with a rise, but a fast one: drift must stay gradual at every step.
MAX_DRIFT_STEP = {"smoke": 0.6, "heat": 2.0}


def slope(values: list[float]) -> float:
    """Least-squares slope of values against their index."""
    n = len(values)
    mean_x, mean_y = (n - 1) / 2, sum(values) / n
    num = sum((i - mean_x) * (v - mean_y) for i, v in enumerate(values))
    den = sum((i - mean_x) ** 2 for i in range(n))
    return num / den if den else 0.0


class Monitor:
    def __init__(self, graph=None):
        self.g = graph if graph is not None else load_graph()
        self.detectors = detectors(self.g)
        self.rooms = sorted(str(r).split("#")[-1] for r in self.g.subjects(RDF.type, FTL.Room))
        self.history: dict[str, list[float]] = {d: [] for d in self.detectors}
        self.burning: set[str] = set()
        self.drift_reported: set[str] = set()

    def process(self, reading: dict) -> list[dict]:
        """Take one reading, return the events it triggers (possibly none)."""
        det, value = reading["detector"], float(reading["value"])
        info = self.detectors.get(det)
        if info is None:
            return [{"type": "unknown_detector", "detector": det}]
        values = self.history[det]
        values.append(value)
        events = []

        above = values[-CONSECUTIVE:]
        if (len(above) == CONSECUTIVE and all(v >= ALARM_THRESHOLD[info["kind"]] for v in above)
                and info["compartment"] not in self.burning):
            comp = info["compartment"]
            self.burning.add(comp)
            decisions = {room: route(self.g, room, comp) for room in self.rooms}
            events.append({"type": "fire_alarm", "detector": det, "space": info["space"],
                           "compartment": comp, "value": value, "step": reading.get("step"),
                           "decisions": decisions})

        window = values[-DRIFT_WINDOW:]
        if (len(window) == DRIFT_WINDOW and det not in self.drift_reported
                and max(window) < ALARM_THRESHOLD[info["kind"]]
                and slope(window) >= DRIFT_SLOPE[info["kind"]]
                and max(b - a for a, b in zip(window, window[1:])) <= MAX_DRIFT_STEP[info["kind"]]):
            self.drift_reported.add(det)
            events.append({"type": "maintenance", "detector": det, "space": info["space"],
                           "reason": f"steady rise of {slope(window):.2f} per reading without fire "
                                     f"(baseline {BASELINE[info['kind']]}, now {value:.1f}): possible sensor drift",
                           "step": reading.get("step")})
        return events


def log_event(event: dict) -> None:
    AUDIT_LOG.parent.mkdir(exist_ok=True)
    entry = {"time": datetime.now(timezone.utc).isoformat(timespec="seconds"), **event}
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def show(event: dict) -> None:
    if event["type"] == "fire_alarm":
        print(f"\nFIRE ALARM  {event['detector']} in {event['space']} -> compartment {event['compartment']} is on fire")
        for room, d in event["decisions"].items():
            print(f"  {room:8s} {d['status'].upper():8s} {' -> '.join(d['path'])}")
    elif event["type"] == "maintenance":
        print(f"\nMAINTENANCE {event['detector']} in {event['space']}: {event['reason']}")
    else:
        print(f"\nWARNING {event}")


def main() -> None:
    import paho.mqtt.client as mqtt

    monitor = Monitor()

    def on_connect(client, userdata, flags, reason_code, properties):
        print(f"Connected to MQTT broker {MQTT_HOST}:{MQTT_PORT}, listening to {TOPIC_PREFIX}/#")
        client.subscribe(f"{TOPIC_PREFIX}/#")

    def on_message(client, userdata, message):
        for event in monitor.process(json.loads(message.payload)):
            show(event)
            log_event(event)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT)
    client.loop_forever()


if __name__ == "__main__":
    main()
