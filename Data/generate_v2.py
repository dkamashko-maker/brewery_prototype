"""DataVest Brew - synthetic dataset v2 (six-module MES prototype).

Deterministic (seed 42). Demo clock 2026-10-21 08:00 UTC, 90 days of history.
All physical models are simplified and illustrative; limits and rates are placeholders.
"""
import json, math, os, random, csv
from datetime import datetime, timedelta, timezone

random.seed(42)
OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(os.path.join(OUT, "json"), exist_ok=True)
os.makedirs(os.path.join(OUT, "timeseries"), exist_ok=True)

NOW = datetime(2026, 10, 21, 8, 0, tzinfo=timezone.utc)
START = NOW - timedelta(days=90)
STEP = timedelta(minutes=15)
def iso(t): return t.strftime("%Y-%m-%dT%H:%M:%SZ")
def steps(a, b):
    t = a
    while t < b:
        yield t
        t += STEP

# ---------------------------------------------------------------- master data
site = {"id": "site_ap", "name": "Alder & Pike Brewing", "time_zone": "Europe/Berlin",
        "excise_jurisdiction": "JUR-X (placeholder)", "units": "metric"}
users = [{"id": f"u_{r}", "name": n, "role": r} for r, n in [
    ("head_brewer", "Lena Fischer"), ("cellar_operator", "Tomas Weber"), ("lab_technician", "Mira Koch"),
    ("quality_manager", "Jonas Braun"), ("technologist", "Anna Schulz"), ("production_manager", "Paul Wagner"),
    ("finance", "Eva Hoffmann")]]
vessels = ([{"id": f"FV-{i:02d}", "name": f"Fermenter {i}", "type": "fermenter", "volume_hl": 60 if i <= 8 else 100} for i in range(1, 13)]
           + [{"id": f"BBT-{i:02d}", "name": f"Bright tank {i}", "type": "bright_tank", "volume_hl": 80} for i in range(1, 5)]
           + [{"id": "BH-01", "name": "Brewhouse", "type": "brewhouse", "volume_hl": 60},
              {"id": "PKG-01", "name": "Packaging line", "type": "packaging_line", "volume_hl": None}])
QWX_FV = [f"FV-{i:02d}" for i in range(1, 9)]

devices, tags = [], []
def add_device(did, vendor, model, protocol, vessel, params):
    devices.append({"id": did, "vendor": vendor, "model": model, "serial": f"SN{random.randint(100000, 999999)}",
                    "protocol": protocol, "vessel_id": vessel, "trust": 1.0})
    for p, unit, addr in params:
        tags.append({"id": f"{did}.{p}", "device_id": did, "parameter": p, "unit": unit, "address": addr})
for fv in QWX_FV:
    add_device(f"qwx_{fv}", "Endress+Hauser", "QWX43", "netilion", fv, [
        ("density", "g/cm3", "netilion:density"), ("viscosity", "mPa.s", "netilion:viscosity"),
        ("sound_velocity", "m/s", "netilion:sound_velocity"), ("temperature", "degC", "netilion:temperature"),
        ("apparent_extract", "degP", "netilion:apparent_extract"), ("real_extract", "degP", "netilion:real_extract"),
        ("alcohol_vol", "%vol", "netilion:alcohol_vol")])
for i in range(1, 13):
    fv = f"FV-{i:02d}"
    add_device(f"plc_{fv}", "Siemens", "S7-1500", "opcua", fv, [
        ("temperature", "degC", f"ns=3;s=FV{i:02d}.Temp"), ("setpoint", "degC", f"ns=3;s=FV{i:02d}.SP"),
        ("pressure", "bar", f"ns=3;s=FV{i:02d}.Press"), ("valve_open", "bool", f"ns=3;s=FV{i:02d}.Valve")])
for i in range(1, 5):
    add_device(f"plc_BBT-{i:02d}", "Schneider", "M580", "modbus", f"BBT-{i:02d}", [
        ("temperature", "degC", f"HR{400 + i * 10}"), ("pressure", "bar", f"HR{401 + i * 10}"), ("level", "%", f"HR{402 + i * 10}")])
add_device("plc_BH-01", "Siemens", "S7-1500 (Profinet via gateway)", "profinet", "BH-01", [
    ("mash_temperature", "degC", "PN:slot2/ch1"), ("kettle_temperature", "degC", "PN:slot2/ch2"), ("wort_flow", "hl/h", "PN:slot3/ch1")])
add_device("eh_ph_BH-01", "Endress+Hauser", "Liquiline pH", "eh_system", "BH-01", [("ph", "pH", "eh:ph")])
add_device("eh_do_PKG-01", "Endress+Hauser", "Oxygen sensor", "eh_system", "PKG-01", [("dissolved_oxygen", "ppb", "eh:do")])
add_device("eh_co2_PKG-01", "Endress+Hauser", "CO2 sensor", "eh_system", "PKG-01", [("co2", "g/l", "eh:co2")])

gateway = {"id": "gw_ap_01", "site_id": "site_ap", "status": "online", "buffer_fill_pct": 0,
           "last_sync": iso(NOW - timedelta(minutes=1)),
           "feeds": [{"protocol": p, "status": "connected"} for p in ["opcua", "modbus", "profinet", "netilion", "eh_system"]]}

# recipes / tech cards: OG degP, apparent attenuation, stage profile (name, temp, hours, tolerance)
RECIPES = {
    "Pilsner":   dict(og=11.8, att=0.80, strain="lager", ibu=36, ebc=7, specs=dict(vdk_max=0.10, abv=(4.6, 5.2))),
    "Helles":    dict(og=11.5, att=0.79, strain="lager", ibu=20, ebc=8, specs=dict(vdk_max=0.10, abv=(4.5, 5.1))),
    "Pale Ale":  dict(og=12.5, att=0.78, strain="ale", ibu=38, ebc=14, specs=dict(vdk_max=0.10, abv=(5.0, 5.6))),
    "IPA":       dict(og=15.0, att=0.80, strain="ale", ibu=60, ebc=16, specs=dict(vdk_max=0.10, abv=(6.2, 7.0))),
    "Stout":     dict(og=13.5, att=0.72, strain="ale", ibu=35, ebc=80, specs=dict(vdk_max=0.10, abv=(4.8, 5.6))),
    "NA Lager":  dict(og=7.0,  att=0.10, strain="na", ibu=18, ebc=7, specs=dict(vdk_max=0.10, abv=(0.0, 0.5))),
}
def stages_for(name):
    lager = name in ("Pilsner", "Helles", "NA Lager")
    if lager:
        return [dict(name="primary", temp_c=11.0, duration_h=150, tolerance_c=0.8),
                dict(name="diacetyl_rest", temp_c=15.0, duration_h=48, tolerance_c=0.8),
                dict(name="crash", temp_c=1.0, duration_h=96, tolerance_c=1.0)]
    return [dict(name="primary", temp_c=19.0, duration_h=110, tolerance_c=0.8),
            dict(name="diacetyl_rest", temp_c=21.0, duration_h=36, tolerance_c=0.8),
            dict(name="crash", temp_c=2.0, duration_h=60, tolerance_c=1.0)]
tech_cards = []
for name, r in RECIPES.items():
    tech_cards.append({"id": f"tc_{name.lower().replace(' ', '_')}", "recipe": name, "version": 3,
                       "raw_material_norms": [
                           {"material": "Pilsner malt" if name != "Stout" else "Pale malt", "kg_per_hl": round(r["og"] * 1.45, 1)},
                           {"material": "Hops (bittering)", "g_per_hl": r["ibu"] * 4},
                           {"material": f"Yeast ({r['strain']} strain)", "l_per_hl": 0.5}],
                       "stages": stages_for(name),
                       "specs": {"og_degP": r["og"], "vdk_max_mg_l": r["specs"]["vdk_max"], "abv_range": r["specs"]["abv"],
                                 "ibu": r["ibu"], "colour_ebc": r["ebc"]},
                       "limit_profile": "non_alcoholic_0_5" if name == "NA Lager" else None})
TC = {t["recipe"]: t for t in tech_cards}

strains = {"lager": "W-34/70 lager", "ale": "US-05 ale", "na": "Maltose-negative NA strain"}
detergents = [{"id": f"det_{i}", "name": n, "qr": f"QR-DET-{i:03d}"} for i, n in
              enumerate(["Caustic 2% (NaOH)", "Acid 1% (HNO3/H3PO4)", "Peracetic acid sanitiser"], 1)]
raw_archive = [{"id": f"rm_{i}", "material": m, "supplier": s, "qr": f"QR-RM-{i:03d}"} for i, (m, s) in
               enumerate([("Pilsner malt", "Weyermann"), ("Pale malt", "Crisp"), ("Roasted barley", "Weyermann"),
                          ("Hallertauer Tradition", "BarthHaas"), ("Citra", "Yakima Chief"), ("Saaz", "BarthHaas")], 1)]

# ---------------------------------------------------------------- physics helpers (illustrative)
def sg_from_plato(p): return 1 + p / (258.6 - (p / 258.2) * 227.1)
def v_water(t): return 1447 + 3.5 * (t - 10)
def logistic(t_h, lag_h, k, total):
    return total / (1 + math.exp(-k * (t_h - lag_h)))

# ---------------------------------------------------------------- schedule batches per fermenter
batches, occupancy, cip_records, events, lots = [], [], [], [], []
yeast_gen = {"lager": 0, "ale": 0, "na": 0}
yeast_rows = []
VIAB = {"lager": [96, 95, 93, 90, 87, 82, 80, 78], "ale": [97, 96, 95, 94, 92, 91, 89, 88], "na": [95, 94, 92, 91, 90, 88, 86, 85]}
recipe_cycle = {"FV-01": ["Pilsner", "Helles"], "FV-02": ["Pilsner"], "FV-03": ["Helles", "Pilsner"], "FV-04": ["Pale Ale", "IPA"],
                "FV-05": ["IPA", "Pale Ale"], "FV-06": ["Stout", "Pale Ale"], "FV-07": ["Helles", "Pilsner"], "FV-08": ["NA Lager"],
                "FV-09": ["Pilsner", "Helles"], "FV-10": ["Pale Ale", "Stout"], "FV-11": ["IPA"], "FV-12": ["NA Lager", "Helles"]}
bn = 2600
plans = {}
for fv, cyc in recipe_cycle.items():
    t = START + timedelta(hours=random.randint(0, 120))
    i = 0
    plans[fv] = []
    while t < NOW:
        name = cyc[i % len(cyc)]; i += 1
        st = stages_for(name)
        dur = sum(s["duration_h"] for s in st)
        plans[fv].append((name, t, dur))
        t += timedelta(hours=dur + 6 + 4 + random.randint(6, 30))  # transfer + CIP + idle

# anchors: force specific open batches
def force(fv, name, opened_hours_ago):
    plans[fv] = [p for p in plans[fv] if p[1] + timedelta(hours=p[2] + 10) < NOW - timedelta(hours=opened_hours_ago)]
    st = stages_for(name)
    plans[fv].append((name, NOW - timedelta(hours=opened_hours_ago), sum(s["duration_h"] for s in st)))
force("FV-07", "Helles", 190)   # A1 slow, open
force("FV-03", "Pilsner", 162)  # A2 in diacetyl rest (150-198 h)
force("FV-01", "Pilsner", 126)  # A10 forecast ready tomorrow
# FV-05 (A3): last batch transferred and CIP finished ~1.5 h ago
plans["FV-05"] = [p for p in plans["FV-05"] if p[1] + timedelta(hours=p[2]) < NOW - timedelta(hours=8)]
last = plans["FV-05"][-1]
plans["FV-05"][-1] = (last[0], NOW - timedelta(hours=last[2] + 6), last[2])

readings_path = os.path.join(OUT, "timeseries", "readings_15min.csv")
rf = open(readings_path, "w", newline=""); rw = csv.writer(rf)
rw.writerow(["ts", "tag_id", "value", "quality", "batch_id", "stage"])
lite_cut = NOW - timedelta(days=14)
lite_rows = []
def emit(ts, tag, val, q="good", bid="", stage=""):
    row = [iso(ts), tag, val if isinstance(val, str) else round(val, 4), q, bid, stage]
    rw.writerow(row)
    if ts >= lite_cut: lite_rows.append(row)

alerts, forecasts = [], []
for fv, plist in plans.items():
    has_qwx = fv in QWX_FV
    occ_end_prev = START
    timeline = []  # (start, end, kind, payload)
    for idx, (name, t0, dur) in enumerate(plist):
        r = RECIPES[name]; strain = r["strain"]
        yeast_gen[strain] = yeast_gen[strain] % 8 + 1
        gen = yeast_gen[strain]
        bn += 1
        bid = f"bat_{bn}"
        open_now = t0 + timedelta(hours=dur) > NOW
        anchor_slow = (fv == "FV-07" and open_now)
        if anchor_slow: gen = 6
        viab = VIAB[strain][gen - 1] + random.uniform(-0.6, 0.6)
        yeast_rows.append({"id": f"yg_{bn}", "strain": strains[strain], "generation": gen,
                           "cell_count_mio_ml": round(random.uniform(14, 18) if not anchor_slow else 11.5, 1),
                           "viability_pct": round(viab, 1), "source_batch_id": bid, "measured_at": iso(t0 - timedelta(hours=3))})
        t_end = t0 + timedelta(hours=dur)
        b = {"id": bid, "number": f"AP-{bn}", "tech_card_id": TC[name]["id"], "recipe": name, "vessel_id": fv,
             "status": "fermenting" if open_now else "transferred", "opened_at": iso(t0), "opened_by": "detected",
             "closed_at": None if open_now else iso(t_end), "volume_hl": next(v["volume_hl"] for v in vessels if v["id"] == fv) * 0.9,
             "yeast_strain": strains[strain], "yeast_generation": gen}
        batches.append(b)
        occupancy.append({"id": f"occ_{bn}", "batch_id": bid, "vessel_id": fv, "valid_from": iso(t0),
                          "valid_to": None if open_now else iso(t_end), "recorded_at": iso(t0 + timedelta(minutes=12))})
        events.append({"id": f"ev_fill_{bn}", "type": "fill", "vessel_id": fv, "batch_id": bid, "ts": iso(t0), "source": "detected"})
        for j, (m, qty, unit) in enumerate([(TC[name]["raw_material_norms"][0]["material"], round(r["og"] * 1.45 * b["volume_hl"]), "kg"),
                                            ("Hallertauer Tradition" if name in ("Pilsner", "Helles", "NA Lager") else "Citra", round(r["ibu"] * 4 * b["volume_hl"] / 1000, 1), "kg")]):
            lots.append({"id": f"lot_{bn}_{j}", "material": m, "supplier": "Weyermann" if j == 0 else "BarthHaas",
                         "supplier_lot": f"L{random.randint(10000, 99999)}", "quantity": qty, "unit": unit, "batch_id": bid})
        timeline.append((t0, t_end, "batch", (bid, name, gen, anchor_slow)))
        if not open_now:
            events.append({"id": f"ev_xfer_{bn}", "type": "transfer", "vessel_id": fv, "batch_id": bid, "ts": iso(t_end), "source": "detected"})
            c0 = t_end + timedelta(hours=1.5); c1 = c0 + timedelta(hours=3)
            cid = f"cip_{bn}"
            unconfirmed = (fv == "FV-05" and c1 > NOW - timedelta(hours=3))
            cip_records.append({"id": cid, "vessel_id": fv, "start": iso(c0), "end": iso(c1),
                                "media_detected": ["water", "caustic", "water", "acid", "water"],
                                "detergent": None if unconfirmed else "det_1", "operator": None if unconfirmed else "u_cellar_operator",
                                "status": "unconfirmed" if unconfirmed else "confirmed", "source": "detected"})
            timeline.append((c0, c1, "cip", cid))
    # ---- emit series for this fermenter
    tl_iter = sorted(timeline, key=lambda x: x[0])
    for ts in steps(START, NOW):
        seg = next((s for s in tl_iter if s[0] <= ts < s[1]), None)
        if seg and seg[2] == "batch":
            bid, name, gen, slow = seg[3]
            r = RECIPES[name]; st = stages_for(name)
            th = (ts - seg[0]).total_seconds() / 3600
            acc = 0; stage = st[-1]
            for s in st:
                if th < acc + s["duration_h"]: stage = s; break
                acc += s["duration_h"]
            sp = stage["temp_c"]
            temp = sp + random.gauss(0, 0.15)
            lag, k = (24, 0.06) if name not in ("Pale Ale", "IPA", "Stout") else (14, 0.09)
            total_drop = r["og"] * r["att"]
            if slow:
                lag, k, total_drop = 55, 0.05, r["og"] * r["att"] * 0.62
            drop = logistic(th, lag, k, total_drop) - logistic(0, lag, k, total_drop)
            ae = max(r["og"] - drop, 0.4)
            abv = max((r["og"] - ae) * 0.53, 0)
            re_ = 0.1808 * r["og"] + 0.8192 * ae
            dens = sg_from_plato(ae) * 0.9982
            visc = 1.25 + 0.075 * re_ + 0.03 * (12 - temp)
            sv = v_water(temp) + 3.8 * re_ + 6.0 * abv
            q = "good"
            if has_qwx:
                did = f"qwx_{fv}"
                for p, v in [("density", dens), ("viscosity", visc), ("sound_velocity", sv), ("temperature", temp),
                             ("apparent_extract", ae), ("real_extract", re_), ("alcohol_vol", abv)]:
                    emit(ts, f"{did}.{p}", v + (random.gauss(0, 0.002) if p in ("apparent_extract", "real_extract") else 0), q, bid, stage["name"])
            for p, v in [("temperature", temp + random.gauss(0, 0.05)), ("setpoint", sp), ("pressure", 0.8 + 0.4 * min(abv, 5) / 5),
                         ("valve_open", 1 if temp > sp + 0.1 else 0)]:
                emit(ts, f"plc_{fv}.{p}", v, "good", bid, stage["name"])
            last_state = (bid, name, th, ae, abv, lag, k, total_drop, r)
        elif seg and seg[2] == "cip":
            ph = (ts - seg[0]).total_seconds() / (seg[1] - seg[0]).total_seconds()
            medium = ["water", "caustic", "water", "acid", "water"][min(int(ph * 5), 4)]
            temp = {"water": 20.0, "caustic": 75.0, "acid": 40.0}[medium]
            sv = v_water(min(temp, 40)) + {"water": 0, "caustic": 35, "acid": 15}[medium]
            if has_qwx:
                emit(ts, f"qwx_{fv}.sound_velocity", sv, "good", "", f"cip_{medium}")
                emit(ts, f"qwx_{fv}.temperature", temp, "good", "", f"cip_{medium}")
            emit(ts, f"plc_{fv}.temperature", temp, "good", "", f"cip_{medium}")
        else:
            emit(ts, f"plc_{fv}.temperature", 16 + random.gauss(0, 0.3), "good", "", "idle")
    # forecasts for open batches
    if has_qwx and plist and plist[-1][1] + timedelta(hours=plist[-1][2]) > NOW:
        bid = batches[-1]["id"]
        name, t0, dur = plist[-1]
        th_now = (NOW - t0).total_seconds() / 3600
        if fv == "FV-01":
            end = NOW + timedelta(hours=28)  # tomorrow ~noon
        elif fv == "FV-07":
            end = NOW + timedelta(hours=96)
        else:
            end = t0 + timedelta(hours=sum(s["duration_h"] for s in stages_for(name)[:2]))
            if end < NOW: end = NOW + timedelta(hours=random.randint(10, 60))
        band = 6 if th_now > 50 else 20
        if fv == "FV-07": band = 30
        forecasts.append({"batch_id": bid, "vessel_id": fv, "end_ts": iso(end), "band_low": iso(end - timedelta(hours=band)),
                          "band_high": iso(end + timedelta(hours=band)), "model": "logistic-v1", "generated_at": iso(NOW)})

# ---- bright tanks (Modbus), brewhouse (Profinet), E+H sensors
outage0 = NOW - timedelta(hours=20); outage1 = outage0 + timedelta(minutes=40)
for ts in steps(START, NOW):
    for i in range(1, 5):
        emit(ts, f"plc_BBT-{i:02d}.temperature", 1.0 + random.gauss(0, 0.1))
        emit(ts, f"plc_BBT-{i:02d}.pressure", 1.1 + random.gauss(0, 0.03))
        emit(ts, f"plc_BBT-{i:02d}.level", max(0, 60 + 30 * math.sin((ts - START).total_seconds() / 86400 / 3 + i)))
    q = "backfilled" if outage0 <= ts < outage1 else "good"
    brewing = ts.hour in range(6, 14)
    emit(ts, "plc_BH-01.mash_temperature", (64 + random.gauss(0, 0.3)) if brewing else 25.0, q)
    emit(ts, "plc_BH-01.kettle_temperature", (99.5 + random.gauss(0, 0.2)) if brewing else 30.0, q)
    emit(ts, "plc_BH-01.wort_flow", (55 + random.gauss(0, 2)) if ts.hour in (12, 13) else 0.0, q)
    emit(ts, "eh_ph_BH-01.ph", (5.35 + random.gauss(0, 0.03)) if brewing else 7.0)
    pk = ts.weekday() < 5 and ts.hour in range(7, 16)
    emit(ts, "eh_do_PKG-01.dissolved_oxygen", (35 + random.gauss(0, 8)) if pk else 0.0)
    emit(ts, "eh_co2_PKG-01.co2", (5.0 + random.gauss(0, 0.05)) if pk else 0.0)
rf.close()
with open(os.path.join(OUT, "timeseries", "readings_demo_lite.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["ts", "tag_id", "value", "quality", "batch_id", "stage"]); w.writerows(lite_rows)

# ---------------------------------------------------------------- lab, micro, panels, releases
lab_results, micro, panels, releases, docs, tasks = [], [], [], [], [], []
closed = [b for b in batches if b["status"] == "transferred"]
pale_block = max((b for b in closed if b["recipe"] == "Pale Ale"), key=lambda b: b["closed_at"])
na_ok = max((b for b in closed if b["recipe"] == "NA Lager"), key=lambda b: b["closed_at"])
for b in closed:
    r = RECIPES[b["recipe"]]
    abv = round(r["og"] * r["att"] * 0.53 + random.gauss(0, 0.05), 2)
    if b is na_ok: abv = 0.38
    vdk = round(random.uniform(0.04, 0.08), 3)
    if b is pale_block: vdk = 0.16
    vals = [("og", r["og"] + random.gauss(0, 0.1), "degP"), ("abv", abv, "%vol"), ("ph", 4.4 + random.gauss(0, 0.05), "pH"),
            ("ibu", r["ibu"] + random.gauss(0, 1.5), "IBU"), ("colour", r["ebc"] + random.gauss(0, 0.5), "EBC"),
            ("haze", random.uniform(0.3, 0.9), "EBC"), ("co2", random.uniform(4.8, 5.3), "g/l"),
            ("dissolved_oxygen", random.uniform(20, 60), "ppb"), ("vdk", vdk, "mg/l")]
    for p, v, u in vals:
        smax = r["specs"]["vdk_max"] if p == "vdk" else (r["specs"]["abv"][1] if p == "abv" else None)
        smin = r["specs"]["abv"][0] if p == "abv" else None
        lab_results.append({"id": f"lr_{b['id']}_{p}", "batch_id": b["id"], "parameter": p, "value": round(v, 3), "unit": u,
                            "method": "MEBAK" if p in ("og", "abv", "vdk") else "in-house", "spec_min": smin, "spec_max": smax,
                            "measured_at": b["closed_at"]})
    micro.append({"id": f"mt_{b['id']}", "batch_id": b["id"], "type": "plating", "organism": "Lactobacillus/Pediococcus",
                  "result": "negative", "tested_at": b["closed_at"]})
    if random.random() < 0.3:
        micro.append({"id": f"pcr_{b['id']}", "batch_id": b["id"], "type": "pcr", "organism": "beer-spoilage panel",
                      "result": "negative", "tested_at": b["closed_at"]})
    attrs = ["appearance", "aroma", "taste", "bitterness", "body", "sweetness", "carbonation", "aftertaste", "true_to_style"]
    scores = [{"taster": f"T{t}", "attribute": a, "score": round(min(5, max(1, random.gauss(4.0, 0.4))), 1)} for t in range(1, 6) for a in attrs]
    off = ["buttery"] if b is pale_block else []
    panels.append({"id": f"tp_{b['id']}", "batch_id": b["id"], "blind": True, "scores": scores, "off_flavours": off,
                   "aggregate": round(sum(s["score"] for s in scores) / len(scores), 2)})
    blocked = b is pale_block
    rel = {"id": f"rel_{b['id']}", "batch_id": b["id"],
           "checks": [{"name": "lab within spec", "ok": not blocked}, {"name": "micro negative", "ok": True}, {"name": "tasting panel", "ok": not blocked}],
           "decision": "blocked" if blocked else "released", "reason": "VDK 0.16 mg/l above spec max 0.10" if blocked else None,
           "signer": None if blocked else "u_quality_manager", "ts": b["closed_at"]}
    releases.append(rel)
    if not blocked:
        docs.append({"id": f"qd_{b['id']}", "batch_id": b["id"], "type": "quality_document",
                     "footer": "Prepared by DataVest Brew · Released by Jonas Braun", "created_at": b["closed_at"],
                     "limit_profile": "non_alcoholic_0_5" if b["recipe"] == "NA Lager" else None})

# Offset records and accuracy checks (A4)
offsets, checks = [], []
for fv in QWX_FV:
    did = f"qwx_{fv}"
    last_off = NOW - timedelta(days=125 if fv == "FV-02" else random.randint(20, 80))
    offsets.append({"id": f"off_{fv}", "device_id": did, "date": iso(last_off),
                    "wort_composition": {"og_degP": 12.0, "malt": "Pilsner malt", "lab_extract_degP": 12.02},
                    "lab_values": {"apparent_extract": 2.41, "alcohol_vol": 5.02}, "correction": {"alcohol_vol": round(random.uniform(-0.03, 0.03), 3)}})
    last_chk = NOW - timedelta(days=47 if fv == "FV-02" else random.randint(3, 25))
    for medium in ("air", "water"):
        checks.append({"id": f"chk_{fv}_{medium}", "device_id": did, "medium": medium, "result": "within tolerance",
                       "tolerance": "placeholder", "date": iso(last_chk), "due_next": iso(last_chk + timedelta(days=30))})
for d in devices:
    if d["id"] == "qwx_FV-02": d["trust"] = 0.8

# Alerts and tasks
fv7 = next(b for b in batches if b["vessel_id"] == "FV-07" and b["status"] == "fermenting")
alerts += [
    {"id": "al_slow_fv07", "rule": "slow_fermentation", "severity": "critical", "target": fv7["id"], "vessel_id": "FV-07",
     "evidence": ["qwx_FV-07.apparent_extract", f"yg_{fv7['number'][3:]}", "similar: last 3 Helles batches"], "state": "open", "raised_at": iso(NOW - timedelta(hours=10))},
    {"id": "al_acc_fv02", "rule": "accuracy_check_overdue", "severity": "warning", "target": "qwx_FV-02", "vessel_id": "FV-02",
     "evidence": ["chk_FV-02_air", "off_FV-02"], "state": "open", "raised_at": iso(NOW - timedelta(days=17))},
    {"id": "al_cip_fv05", "rule": "cip_detergent_unconfirmed", "severity": "info", "target": next(c["id"] for c in cip_records if c["status"] == "unconfirmed"),
     "vessel_id": "FV-05", "evidence": ["qwx_FV-05.sound_velocity"], "state": "open", "raised_at": iso(NOW - timedelta(hours=1))},
    {"id": "al_gw_bh", "rule": "feed_offline", "severity": "warning", "target": "plc_BH-01", "vessel_id": "BH-01",
     "evidence": ["gw_ap_01", "40 min outage; buffered readings backfilled"], "state": "resolved", "raised_at": iso(outage0 + timedelta(minutes=5)), "resolved_at": iso(outage1)},
    {"id": "al_vdk_pale", "rule": "release_blocked", "severity": "critical", "target": pale_block["id"], "vessel_id": pale_block["vessel_id"],
     "evidence": [f"lr_{pale_block['id']}_vdk"], "state": "open", "raised_at": pale_block["closed_at"]},
    {"id": "al_yeast_lager", "rule": "yeast_viability_low", "severity": "warning", "target": "W-34/70 lager", "vessel_id": None,
     "evidence": ["viability gen 6 below 85%"], "state": "open", "raised_at": iso(NOW - timedelta(days=8))},
]
tasks += [
    {"id": "tk_1", "type": "confirm_cip_detergent", "target": "FV-05", "assignee": "u_cellar_operator", "due": iso(NOW + timedelta(hours=2)), "status": "open"},
    {"id": "tk_2", "type": "accuracy_check", "target": "qwx_FV-02", "assignee": "u_technologist", "due": iso(NOW + timedelta(days=1)), "status": "open"},
    {"id": "tk_3", "type": "check_original_gravity_and_pitch", "target": "FV-07", "assignee": "u_head_brewer", "due": iso(NOW + timedelta(hours=4)), "status": "open"},
    {"id": "tk_4", "type": "re_test_vdk", "target": pale_block["id"], "assignee": "u_lab_technician", "due": iso(NOW + timedelta(days=1)), "status": "open"},
]

# Excise (A9): placeholder rate per hl x degP
RATE = 0.787  # placeholder currency units per hl*degP
excise = []
for month, status in [(8, "filed"), (9, "draft")]:
    lines = []
    for b in closed:
        rel = next(r for r in releases if r["batch_id"] == b["id"])
        if rel["decision"] != "released": continue
        cd = datetime.fromisoformat(b["closed_at"].replace("Z", "+00:00"))
        if cd.year == 2026 and cd.month == month:
            og = RECIPES[b["recipe"]]["og"]
            lines.append({"batch_id": b["id"], "volume_hl": b["volume_hl"], "plato": og, "rate": RATE, "amount": round(b["volume_hl"] * og * RATE, 2)})
    excise.append({"id": f"exc_2026_{month:02d}", "period": f"2026-{month:02d}", "jurisdiction": "JUR-X (placeholder)",
                   "lines": lines, "total": round(sum(l["amount"] for l in lines), 2), "status": status})

fc9 = next(f for f in forecasts if f["vessel_id"] == "FV-01")
assistant = [
    {"q": "Why is FV-07 slow?", "a": "Slow start (lag about 60 h vs 24 h typical), lager strain at generation 6 with 82% viability, extract flat for 3 days. Check original gravity and pitch rate.", "cites": ["al_slow_fv07", f"yg_{fv7['number'][3:]}", "qwx_FV-07.apparent_extract"]},
    {"q": "When will FV-01 be ready?", "a": f"Forecast end {fc9['end_ts']} (range {fc9['band_low']} to {fc9['band_high']}).", "cites": [fc9["batch_id"]]},
    {"q": "Which sensors need an accuracy check?", "a": "QWX43 on FV-02: air/water check overdue by 17 days; Offset last done 125 days ago.", "cites": ["chk_FV-02_air", "off_FV-02"]},
    {"q": "How is the lager strain doing?", "a": "Viability fell from 96% at generation 1 to 82% at generation 6; consider a fresh pitch.", "cites": ["al_yeast_lager"]},
    {"q": "Why is the Pale Ale batch blocked?", "a": f"VDK 0.16 mg/l above the 0.10 specification; buttery off-flavour in the panel.", "cites": [f"lr_{pale_block['id']}_vdk", f"tp_{pale_block['id']}"]},
    {"q": "What happened to the brewhouse data yesterday?", "a": "The Profinet feed was offline for 40 minutes; the gateway buffered and backfilled the data.", "cites": ["al_gw_bh", "gw_ap_01"]},
    {"q": "Show last month's excise.", "a": f"September 2026 draft total {excise[1]['total']} (placeholder rate).", "cites": ["exc_2026_09"]},
    {"q": "Which tanks were cleaned today?", "a": "FV-05, detected CIP, detergent not yet confirmed.", "cites": [c["id"] for c in cip_records if c["status"] == "unconfirmed"]},
]

def dump(name, obj):
    with open(os.path.join(OUT, "json", f"{name}.json"), "w") as f: json.dump(obj, f, indent=1, ensure_ascii=False)
for n, o in [("site", site), ("users", users), ("vessels", vessels), ("devices", devices), ("tags", tags), ("gateway", gateway),
             ("tech_cards", tech_cards), ("detergents", detergents), ("raw_material_archive", raw_archive), ("batches", batches),
             ("vessel_occupancy", occupancy), ("raw_material_lots", lots), ("events", events), ("cip_records", cip_records),
             ("yeast_generations", yeast_rows), ("lab_results", lab_results), ("micro_tests", micro), ("tasting_panels", panels),
             ("packaging_releases", releases), ("quality_documents", docs), ("offset_records", offsets), ("accuracy_checks", checks),
             ("alerts", alerts), ("production_tasks", tasks), ("excise_declarations", excise), ("forecasts", forecasts),
             ("assistant_answers", assistant)]:
    dump(n, o)
print("batches", len(batches), "open", sum(b["status"] == "fermenting" for b in batches), "cip", len(cip_records),
      "lab", len(lab_results), "panels", len(panels), "releases", len(releases), "alerts", len(alerts))
print("pale_block", pale_block["id"], "na_ok", na_ok["id"], "excise", [(e["period"], e["total"]) for e in excise])
