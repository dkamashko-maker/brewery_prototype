# DataVest Brew — synthetic dataset v2

Synthetic data for the clickable prototype described in the **Prototype spec** tab. It covers all six modules: batches and tech cards, sensors and integration, laboratory (LIMS), production (MES), analytics and AI, reports and compliance.

All physical models, limits and rates are simplified and illustrative. The data is deterministic (seed 42); `generate_v2.py` rebuilds it.

## Demo clock and history

- Demo clock: **2026-10-21 08:00 UTC**.
- History: 90 days from 2026-07-23.
- Reading resolution: 15 minutes.

## Demo tenant

| Item | Content |
| --- | --- |
| Brewery | Alder & Pike Brewing, one site |
| Vessels | FV-01…FV-12 (fermenters), BBT-01…BBT-04 (bright tanks), BH-01 (brewhouse), PKG-01 (packaging line) |
| QWX43 (Netilion feed) | FV-01…FV-08: density, viscosity, sound velocity, temperature, apparent and real extract, alcohol |
| OPC UA | All fermenters: temperature, setpoint, pressure, valve state |
| Modbus TCP | Bright tanks: temperature, pressure, level |
| Profinet (via gateway) | Brewhouse: mash and kettle temperature, wort flow |
| E+H system | pH (brewhouse), dissolved oxygen and CO₂ (packaging line) |
| Tech cards | Pilsner, Helles, Pale Ale, IPA, Stout, NA Lager, with stage temperature profiles |
| Yeast | 3 strains, generations 1–8 with viability |
| Excise | Jurisdiction placeholder, rate per hl × °P (placeholder) |

## Volumes

| Collection | Rows |
| --- | --- |
| Batches | 95 (8 open) |
| CIP records | 87 |
| Lab results | 783 |
| Micro tests | about 115 |
| Tasting panels | 87 (5 tasters × 9 attributes) |
| Packaging releases | 87 (1 blocked) |
| Readings, full | about 957,000 (`timeseries/readings_15min.csv`) |
| Readings, last 14 days | about 150,000 (`timeseries/readings_demo_lite.csv`) |

## Demo anchors

| ID | Situation | Where to find it |
| --- | --- | --- |
| A1 | FV-07 Helles running long: slow start, extract nearly flat for 3 days (drop about 0.2 °P), lager strain gen 6 at 82% viability | `alerts.json` (`al_slow_fv07`), QWX43 series for FV-07 |
| A2 | FV-03 Pilsner in its programmed diacetyl rest (11 → 15 °C); no alert | readings with stage `diacetyl_rest`, tech card stages |
| A3 | FV-05 CIP detected 03:30–06:30 today; detergent unconfirmed | `cip_records.json` (status `unconfirmed`), task `tk_1` |
| A4 | QWX43 on FV-02: accuracy check overdue since 2026-10-04; last Offset 125 days ago; trust 0.8 | `accuracy_checks.json`, `offset_records.json`, `devices.json` |
| A5 | Lager strain viability 96% → 82% from generation 1 to 6 | `yeast_generations.json` |
| A6 | Pale Ale batch `bat_2678`: VDK 0.16 mg/l above 0.10; release blocked; buttery off-flavour in the panel | `packaging_releases.json`, `lab_results.json`, `tasting_panels.json` |
| A7 | Brewhouse Profinet feed offline 40 minutes yesterday; readings backfilled | readings with quality `backfilled`, alert `al_gw_bh` |
| A8 | NA Lager `bat_2661`: alcohol 0.38% (lab), released, quality document ready | `packaging_releases.json`, `quality_documents.json` |
| A9 | Excise declarations: August filed, September draft | `excise_declarations.json` |
| A10 | FV-01 Pilsner forecast to finish 2026-10-22 12:00 UTC, with range (forecasts exist only for QWX43 tanks) | `forecasts.json` |

## Files

- `json/` — 27 collections (site, users, vessels, devices, tags, gateway, tech cards, detergents, raw-material archive, batches, occupancy, raw-material lots, events, CIP records, yeast generations, lab results, micro tests, tasting panels, packaging releases, quality documents, Offset records, accuracy checks, alerts, production tasks, excise declarations, forecasts, assistant answers).
- `timeseries/` — readings in long format: `ts, tag_id, value, quality, batch_id, stage`. Stage values include fermentation stages, `cip_water`, `cip_caustic`, `cip_acid` and `idle`.
- `schema.sql` — PostgreSQL schema with foreign keys; TimescaleDB hypertable optional.
- `load_to_postgres.py` — loader (`python load_to_postgres.py <dsn> [--lite]`).
- `generate_v2.py` — the generator.

## Notes on the physics (illustrative)

- Extract follows a logistic curve per tech card; the A1 batch uses a longer lag and a lower plateau.
- Alcohol ≈ 0.53 × (original extract − apparent extract); real extract = 0.1808 × OE + 0.8192 × AE.
- Sound velocity rises with temperature, real extract and alcohol; CIP media shift it by fixed offsets so that media changes are detectable.
- All limits (VDK, alcohol, viability, check intervals) and the excise rate are placeholders.
