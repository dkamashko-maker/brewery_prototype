"""Build the lite data pack (repo layout) for the DataVest Brew Lovable prototype from dataset v2."""
import csv, json, math, os, shutil, statistics
from collections import defaultdict
from datetime import datetime, timedelta, timezone

SRC = "/home/claude/mock2/out"
DST = "/home/claude/pack/repo2"
shutil.rmtree(DST, ignore_errors=True)
J = lambda n: json.load(open(f"{SRC}/json/{n}.json"))
NOW = datetime(2026, 10, 21, 8, 0, tzinfo=timezone.utc)
START = NOW - timedelta(days=90)
LIVE_FROM = NOW - timedelta(days=14)
def P(*p):
    p = (("Data", "lite") + tuple(p[1:])) if p and p[0] == "data" else p; path = os.path.join(DST, *p); os.makedirs(os.path.dirname(path), exist_ok=True); return path
def dump(obj, *p):
    with open(P(*p), "w") as f: json.dump(obj, f, separators=(",", ":"), ensure_ascii=False)
def ts(s): return datetime.fromisoformat(s.replace("Z", "+00:00"))
def iso(t): return t.strftime("%Y-%m-%dT%H:%M:%SZ")

groups = {
    "master": ["site", "users", "vessels", "devices", "tags", "gateway", "tech_cards", "detergents", "raw_material_archive"],
    "production": ["batches", "vessel_occupancy", "raw_material_lots", "events", "cip_records", "production_tasks",
                   "packaging_releases", "quality_documents", "excise_declarations"],
    "lab": ["yeast_generations", "lab_results", "micro_tests", "tasting_panels"],
    "sensors": ["offset_records", "accuracy_checks"],
    "analytics": ["alerts", "forecasts", "assistant_answers"],
}
for g, names in groups.items():
    for n in names: dump(J(n), "data", g, f"{n}.json")

tags = J("tags"); devices = {d["id"]: d for d in J("devices")}
tag_vessel = {t["id"]: devices[t["device_id"]]["vessel_id"] for t in tags}
batches = J("batches"); B = {b["id"]: b for b in batches}

# ---- read readings once
live = defaultdict(lambda: defaultdict(dict))   # vessel -> tag -> idx -> value
hourly = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))  # vessel -> tag -> hour idx -> [values]
stage_live = defaultdict(dict)                  # vessel -> idx -> (batch, stage)
quality_flags = []
n_live = int((NOW - LIVE_FROM).total_seconds() // 900)
n_hours = int((NOW - START).total_seconds() // 3600)
extract_by_batch = defaultdict(dict)            # batch -> hours since fill -> apparent extract
with open(f"{SRC}/timeseries/readings_15min.csv") as f:
    for r in csv.DictReader(f):
        t = ts(r["ts"]); v = float(r["value"]); vessel = tag_vessel[r["tag_id"]]; tag = r["tag_id"]
        h = int((t - START).total_seconds() // 3600)
        if 0 <= h < n_hours: hourly[vessel][tag][h].append(v)
        if t >= LIVE_FROM:
            i = int((t - LIVE_FROM).total_seconds() // 900)
            live[vessel][tag][i] = v
            if tag.startswith("plc_FV") and tag.endswith(".temperature"):
                stage_live[vessel][i] = (r["batch_id"] or None, r["stage"] or None)
        if r["quality"] != "good": quality_flags.append({"ts": r["ts"], "tag_id": tag, "quality": r["quality"]})
        if tag.endswith(".apparent_extract") and r["batch_id"]:
            b = B[r["batch_id"]]; hs = int((t - ts(b["opened_at"])).total_seconds() // 3600)
            extract_by_batch[r["batch_id"]].setdefault(hs, v)

def r3(x): return None if x is None else round(x, 3)
index = {"live": {}, "history": {}}
for vessel in sorted(set(list(live) + list(hourly))):
    ltags = sorted(live[vessel])
    stg = stage_live.get(vessel, {})
    dump({"vessel_id": vessel, "start": iso(LIVE_FROM), "step_minutes": 15, "points": n_live,
          "tags": {tg: [r3(live[vessel][tg].get(i)) for i in range(n_live)] for tg in ltags},
          "batch_id": [stg.get(i, (None, None))[0] for i in range(n_live)] if stg else None,
          "stage": [stg.get(i, (None, None))[1] for i in range(n_live)] if stg else None},
         "data", "timeseries", "live_14d", f"{vessel}.json")
    index["live"][vessel] = f"Data/lite/timeseries/live_14d/{vessel}.json"
    htags = sorted(hourly[vessel])
    dump({"vessel_id": vessel, "start": iso(START), "step_minutes": 60, "points": n_hours,
          "tags": {tg: [r3(statistics.fmean(hourly[vessel][tg][h])) if hourly[vessel][tg].get(h) else None for h in range(n_hours)] for tg in htags}},
         "data", "timeseries", "history_90d_hourly", f"{vessel}.json")
    index["history"][vessel] = f"Data/lite/timeseries/history_90d_hourly/{vessel}.json"
dump(quality_flags, "data", "timeseries", "quality_flags.json")

# ---- derived: recipe envelopes (apparent extract p10/p50/p90 by hour since fill, closed batches)
env = {}
for recipe in sorted({b["recipe"] for b in batches}):
    series = [extract_by_batch[b["id"]] for b in batches if b["recipe"] == recipe and b["status"] == "transferred" and b["id"] in extract_by_batch]
    if len(series) < 2: continue
    maxh = min(max(s) for s in series)
    pts = []
    for h in range(0, maxh + 1, 2):
        vals = sorted(s[h] for s in series if h in s)
        if len(vals) < 2: continue
        q = lambda p: vals[min(len(vals) - 1, max(0, int(round(p * (len(vals) - 1)))))]
        pts.append({"h": h, "p10": r3(q(0.1)), "p50": r3(q(0.5)), "p90": r3(q(0.9))})
    env[recipe] = {"recipe": recipe, "batches_used": len(series), "parameter": "apparent_extract", "unit": "degP", "points": pts}
dump(env, "data", "analytics", "recipe_envelopes.json")

# ---- derived: forecast curves for open batches with QWX43
curves = []
for fc in J("forecasts"):
    b = B[fc["batch_id"]]; ex = extract_by_batch.get(b["id"])
    if not ex: continue
    tc = next(t for t in J("tech_cards") if t["id"] == b["tech_card_id"])
    og = tc["specs"]["og_degP"]
    fg = og * (1 - {"Pilsner": .80, "Helles": .79, "Pale Ale": .78, "IPA": .80, "Stout": .72, "NA Lager": .10}[b["recipe"]])
    h_now = int((NOW - ts(b["opened_at"])).total_seconds() // 3600)
    cur = ex[max(k for k in ex if k <= h_now)]
    if b["vessel_id"] == "FV-07": fg = cur - 0.4
    end_h = int((ts(fc["end_ts"]) - ts(b["opened_at"])).total_seconds() // 3600)
    span = max(end_h - h_now, 1); pts = []
    for h in range(h_now, end_h + 1, 2):
        frac = 1 - math.exp(-3 * (h - h_now) / span)
        mid = cur - (cur - fg) * frac
        w = (0.15 + 0.5 * (h - h_now) / span) * (2.0 if h_now < 50 or b["vessel_id"] == "FV-07" else 1.0)
        pts.append({"h": h, "ts": iso(ts(b["opened_at"]) + timedelta(hours=h)), "mid": r3(mid), "low": r3(mid - w), "high": r3(mid + w)})
    curves.append({"batch_id": b["id"], "vessel_id": b["vessel_id"], "parameter": "apparent_extract", "points": pts})
dump(curves, "data", "analytics", "forecast_curves.json")

# ---- derived: trust history (weekly) and unmapped tags for the mapping wizard
trust = []
for d in J("devices"):
    if d["model"] != "QWX43": continue
    for w in range(13):
        day = START + timedelta(days=7 * w)
        val = 1.0
        if d["id"] == "qwx_FV-02" and day > NOW - timedelta(days=17): val = 0.8
        trust.append({"device_id": d["id"], "week_start": iso(day), "trust": val})
dump(trust, "data", "sensors", "trust_history.json")
unmapped = [{"feed": "opcua", "address": f"ns=3;s=FV{i:02d}.{p}", "data_type": dt, "suggested_parameter": sp}
            for i in (1, 7, 12) for p, dt, sp in [("Level", "Float", "level"), ("CoolingValvePct", "Float", "cooling_valve_pct"), ("AgitatorOn", "Boolean", None)]]
unmapped += [{"feed": "modbus", "address": f"HR{450 + i}", "data_type": "Int16", "suggested_parameter": None} for i in range(4)]
unmapped += [{"feed": "profinet", "address": "PN:slot4/ch1", "data_type": "Float", "suggested_parameter": "lauter_turbidity"}]
dump(unmapped, "data", "sensors", "unmapped_tags.json")

# ---- meta / manifest
files = []
for root, _, fs in os.walk(os.path.join(DST, "Data", "lite")):
    for fn in fs:
        p = os.path.join(root, fn); files.append({"path": os.path.relpath(p, DST), "bytes": os.path.getsize(p)})
meta = {"dataset": "DataVest Brew synthetic v2 (lite)", "demo_clock": iso(NOW), "display_time_zone": "Europe/Berlin",
        "history_start": iso(START), "live_window_start": iso(LIVE_FROM), "generated_from": "datavest_brew_mock_dataset_v2",
        "base_url_raw": "https://raw.githubusercontent.com/dkamashko-maker/brewery_prototype/main/",
        "timeseries_index": index, "files": sorted(files, key=lambda x: x["path"])}
dump(meta, "data", "meta.json")
tot = sum(f["bytes"] for f in files)
print("files", len(files), "total MB", round(tot / 1e6, 2))
for f in sorted(files, key=lambda x: -x["bytes"])[:8]: print(f)
print("envelopes", list(env), "curves", [c["vessel_id"] for c in curves])
