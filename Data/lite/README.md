# DataVest Brew — lite data for the browser prototype

Synthetic data for the DataVest Brew clickable prototype (MES for breweries). It is a lite cut of dataset v2: all reference and transactional collections in full, sensor time series reduced to a 14-day live window (15 min) and a 90-day hourly history.

All values are synthetic; physics, limits and rates are illustrative placeholders.

## How the prototype reads the data

The repository is public, and GitHub serves raw files with `Access-Control-Allow-Origin: *`, so a browser app can load them directly:

```
https://raw.githubusercontent.com/dkamashko-maker/brewery_prototype/main/Data/lite/meta.json
```

Start with `Data/lite/meta.json`: it holds the demo clock, display time zone, the time-series index per vessel and the full file list.

- **Demo clock:** 2026-10-21 08:00 UTC; display in Europe/Berlin. The app treats this as "now".
- **Time series:** columnar. Each file has `start`, `step_minutes`, `points` and `tags` (tag id → array of values; `null` = no reading). Fermenter live files also carry per-point `batch_id` and `stage`.

## Layout

| Path | Content |
| --- | --- |
| `Data/lite/meta.json` | Demo clock, time zone, time-series index, file list |
| `Data/lite/master/` | site, users, vessels, devices, tags, gateway, tech_cards, detergents, raw_material_archive |
| `Data/lite/production/` | batches, vessel_occupancy, raw_material_lots, events, cip_records, production_tasks, packaging_releases, quality_documents, excise_declarations |
| `Data/lite/lab/` | yeast_generations, lab_results, micro_tests, tasting_panels |
| `Data/lite/sensors/` | offset_records, accuracy_checks, trust_history, unmapped_tags |
| `Data/lite/analytics/` | alerts, forecasts, forecast_curves, recipe_envelopes, assistant_answers |
| `Data/lite/timeseries/live_14d/` | One file per vessel, 15-minute values for the last 14 days |
| `Data/lite/timeseries/history_90d_hourly/` | One file per vessel, hourly means for 90 days |
| `Data/lite/timeseries/quality_flags.json` | Readings marked `backfilled` (Profinet outage) |
| `Data/lite/DATA_CONTRACT.md` | Field definitions and TypeScript types |

## Demo anchors

| ID | Situation | Data |
| --- | --- | --- |
| A1 | FV-07 Helles running long: extract nearly flat for 3 days; lager yeast gen 6 at 82% | `analytics/alerts.json` (`al_slow_fv07`), FV-07 time series |
| A2 | FV-03 Pilsner in a programmed diacetyl rest (11 → 15 °C); no alert | FV-03 `stage` = `diacetyl_rest`, tech card stages |
| A3 | FV-05 CIP detected today, detergent unconfirmed | `production/cip_records.json` (`unconfirmed`), task `tk_1` |
| A4 | QWX43 on FV-02: accuracy check overdue, Offset 125 days old, trust 0.8 | `sensors/accuracy_checks.json`, `sensors/offset_records.json` |
| A5 | Lager strain viability 96% → 82% over generations 1–6 | `lab/yeast_generations.json` |
| A6 | Pale Ale `bat_2678`: VDK 0.16 mg/l > 0.10; release blocked | `production/packaging_releases.json`, `lab/lab_results.json` |
| A7 | Brewhouse Profinet feed offline 40 min yesterday; data backfilled | `timeseries/quality_flags.json`, alert `al_gw_bh` |
| A8 | NA Lager `bat_2661`: alcohol 0.38%, released, quality document ready | `production/quality_documents.json` |
| A9 | Excise: August filed, September draft | `production/excise_declarations.json` |
| A10 | FV-01 Pilsner forecast to finish 2026-10-22 12:00 UTC, with range | `analytics/forecasts.json`, `analytics/forecast_curves.json` |

Forecasts and forecast curves exist only for fermenters with a QWX43 (FV-01 to FV-08).

## Source

Generated from `datavest_brew_mock_dataset_v2` (seed 42) with `Data/lite/build_pack.py`; the full dataset is in `Data/json` and `Data/timeseries`.
