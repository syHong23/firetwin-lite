"""Detectors of the building, read from the knowledge graph, and the MQTT topic layout.

Topic:   firetwin/detectors/<detector id>      e.g. firetwin/detectors/SD_102
Payload: {"detector": "SD_102", "kind": "smoke", "value": 1.2, "step": 7}
Smoke values are in % obscuration per metre, heat values in degrees Celsius.
Thresholds are illustrative values for this prototype, not taken from a standard.
"""
import os

from rdflib import RDF, Graph, Namespace

BOT = Namespace("https://w3id.org/bot#")
FTL = Namespace("https://example.org/firetwin#")
BASE = "https://example.org/firetwin/building#"

MQTT_HOST = os.environ.get("MQTT_HOST", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
TOPIC_PREFIX = "firetwin/detectors"

BASELINE = {"smoke": 0.5, "heat": 21.0}
ALARM_THRESHOLD = {"smoke": 8.0, "heat": 57.0}


def short(n) -> str:
    return str(n).replace(BASE, "")


def detectors(g: Graph) -> dict[str, dict]:
    """Every smoke and heat detector with its kind, space and compartment."""
    found = {}
    for cls, kind in ((FTL.SmokeDetector, "smoke"), (FTL.HeatDetector, "heat")):
        for d in g.subjects(RDF.type, cls):
            space = next(g.subjects(BOT.containsElement, d), None)
            comp = g.value(space, FTL.inCompartment) if space is not None else None
            found[short(d)] = {"kind": kind, "space": short(space) if space is not None else None,
                               "compartment": short(comp) if comp is not None else None}
    return dict(sorted(found.items()))
