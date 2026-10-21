-- DataVest Brew synthetic dataset v2: PostgreSQL schema (TimescaleDB optional for readings)
CREATE TABLE site (id text PRIMARY KEY, name text, time_zone text, excise_jurisdiction text, units text);
CREATE TABLE users (id text PRIMARY KEY, name text, role text);
CREATE TABLE vessels (id text PRIMARY KEY, name text, type text, volume_hl numeric);
CREATE TABLE devices (id text PRIMARY KEY, vendor text, model text, serial text, protocol text, vessel_id text REFERENCES vessels(id), trust numeric);
CREATE TABLE tags (id text PRIMARY KEY, device_id text REFERENCES devices(id), parameter text, unit text, address text);
CREATE TABLE gateway (id text PRIMARY KEY, site_id text REFERENCES site(id), status text, buffer_fill_pct numeric, last_sync timestamptz, feeds jsonb);
CREATE TABLE tech_cards (id text PRIMARY KEY, recipe text, version int, raw_material_norms jsonb, stages jsonb, specs jsonb, limit_profile text);
CREATE TABLE detergents (id text PRIMARY KEY, name text, qr text);
CREATE TABLE raw_material_archive (id text PRIMARY KEY, material text, supplier text, qr text);
CREATE TABLE batches (id text PRIMARY KEY, number text, tech_card_id text REFERENCES tech_cards(id), recipe text, vessel_id text REFERENCES vessels(id),
  status text, opened_at timestamptz, opened_by text, closed_at timestamptz, volume_hl numeric, yeast_strain text, yeast_generation int);
CREATE TABLE vessel_occupancy (id text PRIMARY KEY, batch_id text REFERENCES batches(id), vessel_id text REFERENCES vessels(id),
  valid_from timestamptz, valid_to timestamptz, recorded_at timestamptz);
CREATE TABLE raw_material_lots (id text PRIMARY KEY, material text, supplier text, supplier_lot text, quantity numeric, unit text, batch_id text REFERENCES batches(id));
CREATE TABLE events (id text PRIMARY KEY, type text, vessel_id text REFERENCES vessels(id), batch_id text REFERENCES batches(id), ts timestamptz, source text);
CREATE TABLE cip_records (id text PRIMARY KEY, vessel_id text REFERENCES vessels(id), start timestamptz, "end" timestamptz, media_detected jsonb,
  detergent text REFERENCES detergents(id), operator text REFERENCES users(id), status text, source text);
CREATE TABLE yeast_generations (id text PRIMARY KEY, strain text, generation int, cell_count_mio_ml numeric, viability_pct numeric,
  source_batch_id text REFERENCES batches(id), measured_at timestamptz);
CREATE TABLE lab_results (id text PRIMARY KEY, batch_id text REFERENCES batches(id), parameter text, value numeric, unit text, method text,
  spec_min numeric, spec_max numeric, measured_at timestamptz);
CREATE TABLE micro_tests (id text PRIMARY KEY, batch_id text REFERENCES batches(id), type text, organism text, result text, tested_at timestamptz);
CREATE TABLE tasting_panels (id text PRIMARY KEY, batch_id text REFERENCES batches(id), blind boolean, scores jsonb, off_flavours jsonb, aggregate numeric);
CREATE TABLE packaging_releases (id text PRIMARY KEY, batch_id text REFERENCES batches(id), checks jsonb, decision text, reason text,
  signer text REFERENCES users(id), ts timestamptz);
CREATE TABLE quality_documents (id text PRIMARY KEY, batch_id text REFERENCES batches(id), type text, footer text, created_at timestamptz, limit_profile text);
CREATE TABLE offset_records (id text PRIMARY KEY, device_id text REFERENCES devices(id), date timestamptz, wort_composition jsonb, lab_values jsonb, correction jsonb);
CREATE TABLE accuracy_checks (id text PRIMARY KEY, device_id text REFERENCES devices(id), medium text, result text, tolerance text, date timestamptz, due_next timestamptz);
CREATE TABLE alerts (id text PRIMARY KEY, rule text, severity text, target text, vessel_id text REFERENCES vessels(id), evidence jsonb, state text,
  raised_at timestamptz, resolved_at timestamptz);
CREATE TABLE production_tasks (id text PRIMARY KEY, type text, target text, assignee text REFERENCES users(id), due timestamptz, status text);
CREATE TABLE excise_declarations (id text PRIMARY KEY, period text, jurisdiction text, lines jsonb, total numeric, status text);
CREATE TABLE forecasts (batch_id text PRIMARY KEY REFERENCES batches(id), vessel_id text REFERENCES vessels(id), end_ts timestamptz,
  band_low timestamptz, band_high timestamptz, model text, generated_at timestamptz);
CREATE TABLE assistant_answers (q text PRIMARY KEY, a text, cites jsonb);
CREATE TABLE readings (ts timestamptz NOT NULL, tag_id text NOT NULL REFERENCES tags(id), value text, quality text,
  batch_id text REFERENCES batches(id), stage text);
CREATE INDEX readings_tag_ts ON readings (tag_id, ts);
-- Optional with TimescaleDB: SELECT create_hypertable('readings', 'ts');
