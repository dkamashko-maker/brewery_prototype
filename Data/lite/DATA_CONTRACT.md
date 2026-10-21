# Data contract

All timestamps are ISO 8601 UTC strings. Display them in `meta.display_time_zone`. IDs are stable strings.

```ts
// Data/lite/meta.json
interface Meta {
  dataset: string; demo_clock: string; display_time_zone: string;
  history_start: string; live_window_start: string; base_url_raw: string;
  timeseries_index: { live: Record<VesselId, string>; history: Record<VesselId, string> };
  files: { path: string; bytes: number }[];
}
type VesselId = string; // "FV-01".."FV-12", "BBT-01".."BBT-04", "BH-01", "PKG-01"

// Data/lite/timeseries/*/<vessel>.json  (columnar)
interface SeriesFile {
  vessel_id: VesselId; start: string; step_minutes: 15 | 60; points: number;
  tags: Record<TagId, (number | null)[]>;          // index i => start + i*step
  batch_id?: (string | null)[] | null;             // fermenters, live window only
  stage?: (string | null)[] | null;                // primary | diacetyl_rest | crash | cip_water | cip_caustic | cip_acid | idle
}
type TagId = string; // e.g. "qwx_FV-01.apparent_extract", "plc_FV-01.temperature"

// master
interface Site { id: string; name: string; time_zone: string; excise_jurisdiction: string; units: string }
interface User { id: string; name: string; role: "head_brewer"|"cellar_operator"|"lab_technician"|"quality_manager"|"technologist"|"production_manager"|"finance" }
interface Vessel { id: VesselId; name: string; type: "fermenter"|"bright_tank"|"brewhouse"|"packaging_line"; volume_hl: number | null }
interface Device { id: string; vendor: string; model: string; serial: string; protocol: "netilion"|"eh_system"|"opcua"|"modbus"|"profinet"; vessel_id: VesselId; trust: number }
interface Tag { id: TagId; device_id: string; parameter: string; unit: string; address: string }
interface Gateway { id: string; site_id: string; status: "online"|"degraded"|"offline"; buffer_fill_pct: number; last_sync: string; feeds: { protocol: Device["protocol"]; status: string }[] }
interface TechCard { id: string; recipe: string; version: number;
  raw_material_norms: { material: string; kg_per_hl?: number; g_per_hl?: number; l_per_hl?: number }[];
  stages: { name: "primary"|"diacetyl_rest"|"crash"; temp_c: number; duration_h: number; tolerance_c: number }[];
  specs: { og_degP: number; vdk_max_mg_l: number; abv_range: [number, number]; ibu: number; colour_ebc: number };
  limit_profile: string | null }
interface Detergent { id: string; name: string; qr: string }
interface RawMaterialArchiveItem { id: string; material: string; supplier: string; qr: string }

// production
interface Batch { id: string; number: string; tech_card_id: string; recipe: string; vessel_id: VesselId;
  status: "fermenting"|"transferred"; opened_at: string; opened_by: "detected"|string; closed_at: string | null;
  volume_hl: number; yeast_strain: string; yeast_generation: number }
interface VesselOccupancy { id: string; batch_id: string; vessel_id: VesselId; valid_from: string; valid_to: string | null; recorded_at: string }
interface RawMaterialLot { id: string; material: string; supplier: string; supplier_lot: string; quantity: number; unit: string; batch_id: string }
interface Event { id: string; type: "fill"|"transfer"; vessel_id: VesselId; batch_id: string; ts: string; source: "detected"|string }
interface CipRecord { id: string; vessel_id: VesselId; start: string; end: string; media_detected: string[];
  detergent: string | null; operator: string | null; status: "confirmed"|"unconfirmed"; source: "detected" }
interface ProductionTask { id: string; type: string; target: string; assignee: string; due: string; status: "open"|"done" }
interface PackagingRelease { id: string; batch_id: string; checks: { name: string; ok: boolean }[];
  decision: "released"|"blocked"; reason: string | null; signer: string | null; ts: string }
interface QualityDocument { id: string; batch_id: string; type: "quality_document"; footer: string; created_at: string; limit_profile: string | null }
interface ExciseDeclaration { id: string; period: string; jurisdiction: string; status: "filed"|"draft"; total: number;
  lines: { batch_id: string; volume_hl: number; plato: number; rate: number; amount: number }[] }

// lab
interface YeastGeneration { id: string; strain: string; generation: number; cell_count_mio_ml: number; viability_pct: number; source_batch_id: string; measured_at: string }
interface LabResult { id: string; batch_id: string; parameter: "og"|"abv"|"ph"|"ibu"|"colour"|"haze"|"co2"|"dissolved_oxygen"|"vdk";
  value: number; unit: string; method: string; spec_min: number | null; spec_max: number | null; measured_at: string }
interface MicroTest { id: string; batch_id: string; type: "plating"|"pcr"; organism: string; result: "negative"|"positive"; tested_at: string }
interface TastingPanel { id: string; batch_id: string; blind: boolean; scores: { taster: string; attribute: string; score: number }[]; off_flavours: string[]; aggregate: number }

// sensors
interface OffsetRecord { id: string; device_id: string; date: string; wort_composition: Record<string, string | number>; lab_values: Record<string, number>; correction: Record<string, number> }
interface AccuracyCheck { id: string; device_id: string; medium: "air"|"water"; result: string; tolerance: string; date: string; due_next: string }
interface TrustPoint { device_id: string; week_start: string; trust: number }
interface UnmappedTag { feed: "opcua"|"modbus"|"profinet"; address: string; data_type: string; suggested_parameter: string | null }

// analytics
interface Alert { id: string; rule: string; severity: "info"|"warning"|"critical"; target: string; vessel_id: VesselId | null;
  evidence: string[]; state: "open"|"resolved"; raised_at: string; resolved_at?: string }
interface Forecast { batch_id: string; vessel_id: VesselId; end_ts: string; band_low: string; band_high: string; model: string; generated_at: string }
interface ForecastCurve { batch_id: string; vessel_id: VesselId; parameter: "apparent_extract";
  points: { h: number; ts: string; mid: number; low: number; high: number }[] }  // h = hours since batch opened_at
type RecipeEnvelopes = Record<string, { recipe: string; batches_used: number; parameter: "apparent_extract"; unit: "degP";
  points: { h: number; p10: number; p50: number; p90: number }[] }>   // h = hours since fill
interface AssistantAnswer { q: string; a: string; cites: string[] }
```

## Derived rules the prototype applies

| Rule | Logic (placeholder thresholds) |
| --- | --- |
| Current value on the tank board | Last non-null value in the live file for the tag |
| Stage | `stage` array of the fermenter live file |
| Degree of fermentation | (OG − apparent extract) / OG, OG from the tech card |
| Temperature in plan | Compare `plc_FV-xx.temperature` with the tech-card stage `temp_c ± tolerance_c`; inside → no alert |
| Accuracy check overdue | `due_next` < demo clock |
| Release blocked | Any `lab_results` value outside `spec_min`/`spec_max`, or a positive micro test |
| Yeast viability | Warning < 90%, critical < 85% |
