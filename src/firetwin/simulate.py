"""Simulated detectors publishing readings over MQTT.

Scenario (reproducible, fixed random seed):
- every detector sends small noisy values around its baseline,
- from step 15, a fire starts in Room 102: its smoke and heat detectors rise fast,
- from step 5, smoke detector SD_C0 in Corridor 0 drifts slowly upwards (sensor ageing).

Usage:  python -m firetwin.simulate [--steps 40] [--interval 0.5]
"""
import argparse
import json
import random
import time

from firetwin.kg import load_graph
from firetwin.sensors import BASELINE, MQTT_HOST, MQTT_PORT, TOPIC_PREFIX, detectors

FIRE_START, FIRE_DETECTORS = 15, {"SD_102": 2.5, "HD_102": 6.0}   # rise per step
DRIFT_START, DRIFT_DETECTOR, DRIFT_RATE = 5, "SD_C0", 0.2


def reading(det: str, kind: str, step: int, rng: random.Random) -> float:
    value = BASELINE[kind] + rng.gauss(0, 0.1 if kind == "smoke" else 0.3)
    if det in FIRE_DETECTORS and step >= FIRE_START:
        value += FIRE_DETECTORS[det] * (step - FIRE_START + 1)
    if det == DRIFT_DETECTOR and step >= DRIFT_START:
        value += DRIFT_RATE * (step - DRIFT_START + 1)
    return round(value, 2)


def scenario(steps: int, seed: int = 42):
    """Yield the readings of every detector at every step."""
    rng = random.Random(seed)
    dets = detectors(load_graph())
    for step in range(steps):
        for det, info in dets.items():
            yield {"detector": det, "kind": info["kind"], "value": reading(det, info["kind"], step, rng), "step": step}


def main() -> None:
    import paho.mqtt.client as mqtt

    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=40)
    parser.add_argument("--interval", type=float, default=0.5, help="seconds between steps")
    args = parser.parse_args()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(MQTT_HOST, MQTT_PORT)
    client.loop_start()
    current = -1
    for r in scenario(args.steps):
        if r["step"] != current:
            current = r["step"]
            print(f"step {current}")
            time.sleep(args.interval)
        client.publish(f"{TOPIC_PREFIX}/{r['detector']}", json.dumps(r))
    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":
    main()
