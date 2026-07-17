"""Summarize the included asynchronous ThingSpeak sample without dependencies."""

import csv
from datetime import datetime
from pathlib import Path
from statistics import median

DATA = Path(__file__).resolve().parents[1] / "data" / "sample_operational_window.csv"

flows = []
states = []
first_ts = None
last_ts = None

with DATA.open(newline="", encoding="utf-8") as handle:
    for row in csv.DictReader(handle):
        ts = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
        first_ts = ts if first_ts is None else min(first_ts, ts)
        last_ts = ts if last_ts is None else max(last_ts, ts)
        if row["field3"]:
            try:
                q = float(row["field3"])
                if 0.0 <= q <= 60.0:
                    flows.append(q)
            except ValueError:
                pass
        if row["field6"]:
            try:
                states.append((ts, int(float(row["field6"]))))
            except ValueError:
                pass

collapsed = []
for item in states:
    if not collapsed or item[1] != collapsed[-1][1]:
        collapsed.append(item)

hp_events = 0
compliant = 0
delays = []
for index, (ts, code) in enumerate(collapsed):
    if code != 6:
        continue
    hp_events += 1
    if index > 0 and collapsed[index - 1][1] == 3:
        compliant += 1
        delays.append((ts - collapsed[index - 1][0]).total_seconds())

positive = [q for q in flows if q > 0]
print("Sample:", DATA)
print("Window:", first_ts, "to", last_ts)
print("Valid flow observations:", len(flows))
print("Positive-flow median (L/min):", median(positive) if positive else "n/a")
print("Collapsed state sequence:", [code for _, code in collapsed])
print("High-pressure activations:", hp_events)
print("Low-pressure-before-high-pressure:", compliant)
print("Transition delays (s):", delays)
