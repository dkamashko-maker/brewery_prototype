# design.md — DataVest Brew prototype

Version 1.0 · 16 October 2026 · Intetics SmartLab / DataVest

This file tells a designer or an AI coding tool how the DataVest Brew prototype should look, read and behave. It is grounded in an analysis of the Endress+Hauser (E+H) Netilion ecosystem, because the first commercial vehicle is a build partnership with E+H and the first users will already know Netilion.

**Precedence.** The *Prototype spec* (Part B of the architecture document) defines data, screens, rules and flows. This file defines look, interaction and wording. Where they conflict on data or behaviour, the Prototype spec wins; where they conflict on presentation, this file wins.

**Scope.** Web app on synthetic data (`datavest_brew_mock_dataset_v1`), twelve screens S01–S12, seven roles. No live connectors, no equipment control.

---

## 1. What E+H already ships — and what that changes

### 1.1 Correction to the gap analysis

The architecture document lists gap G1 as "no batch / recipe / vessel object in Netilion". That is only partly true. E+H ships **Netilion Fermentation**, a dedicated app for the QWX43 Fermentation Monitor (manual BA02162F, version 03.24) with these objects and pages:

| Netilion Fermentation page | What it does |
| --- | --- |
| Dashboard | Tanks in a grid view or a list view, with search; a tile opens Tank Details |
| Batch / Batch Details | All batches, create, edit, search, filter by golden batch; details show primary values, history, CSV export |
| Tank / Tank Details | Tank with assigned QWX43, four primary values, history chart, NE 107 status, assigned batches |
| Asset / Asset Details | The QWX43 device: serial number, status, all process values, unit changes, history |
| Recipe / Recipe Details | Beer type, limit values (thresholds), assigned batches |
| Automatic Batch Start/Stop Recognition | Batch starts when the tank gets filled; ends when the tank is empty or temperature falls below a set value |
| Thresholds (per recipe) | Description, measured value, threshold, tolerance, optional e-mail notification |
| Sample preparation adjustment | Toggle that switches the chart between "History" and "History Adjusted" (MEBAK lab-comparable values) |

**What the gap really is:** Netilion Fermentation's batch model covers only tanks with a QWX43, one device per tank, with four primary values and single-level recipe thresholds. It has no mixed sensor fleets, lab or QA linkage, lot genealogy, compliance evidence, multi-site comparison or forecasting. The architecture document's G1 and competitor table should be updated to say this.

**Design consequence:** brewers who own a QWX43 have seen tank tiles, batch pages, golden-batch overlays and automatic batch start. The prototype must feel like a **clear step up from Netilion Fermentation**, not a reinvention of it. Where E+H's pattern works, keep it recognisable. Where DataVest Brew goes further (trust, lab, lots, compliance, sites), make the extra visibly richer.

### 1.2 The Netilion family at a glance

| Service | Primary object | UX patterns worth noting |
| --- | --- | --- |
| Netilion Value | Tag (measuring point) | Tag details page with a *Latest values* section; four threshold levels (Low Low, Low, High, High High) set from that section; thresholds drawn on the history chart and toggled under the graph; e-mail to everyone with access when a threshold is crossed; dashboards; export |
| Netilion Health | Asset (device) | Health from the four NAMUR NE 107 status signals; overview page to see what to focus on first; clear-text *cause and remedy* per diagnostic; remote Heartbeat Verification with a passed / not passed result and a PDF report |
| Netilion Library | Asset | Asset created from manufacturer, serial number and product code; E+H product name and documentation filled in automatically from the serial number; user uploads with name and category |
| Netilion Analytics | Installed base | Plant structure down to tag and device; obsolescence and standardisation KPIs |
| Netilion Scanner / Operations app | Asset in the field | Photo, serial number or RFID / QR scan to register or identify a device |
| Netilion Network Insights (water) | Network KPIs | Vertical web-SCADA: customisable dashboard, time curves, tables, trend displays, weather-based forecasts |
| Netilion Fermentation | Tank, batch, recipe | See 1.1 |
| Firmware Update Scheduler | Asset | Red exclamation mark for available updates; pick version and date; green tick when done |

**Object model underneath (Netilion Connect):** *nodes* (plant structure), *instrumentation* (a technical location whose identifier is the tag), and *assets* (physical devices). Events, documents, specifications and pictures attach to them. Assets and tags are distinct objects that can be re-assigned to each other over time.

### 1.3 NAMUR NE 107 — the shared health vocabulary

E+H devices, Netilion Health and Netilion Fermentation all report device health as one of four NE 107 signals. The QWX43 diagnostic table maps every code to one of them with a short text and a remedy.

| Signal | Letter | Meaning (NE 107) | Example QWX43 codes |
| --- | --- | --- | --- |
| Failure | F | Invalid signal due to a malfunction | 041 sensor defective; 400 cannot connect to cloud |
| Function check | C | Temporarily invalid signal (e.g. maintenance, loop test) | — |
| Out of specification | S | Device running outside its permissible range | 802 sensor uncovered; 843 too many bubbles |
| Maintenance required | M | Still valid, but needs attention soon | 168 deposits detected (clean tuning fork); 948 weak signal quality |

The prototype must use this vocabulary for **device** health, and must keep it visually distinct from **process** alerts (stall, temperature deviation) and **compliance** status. Netilion itself learned this: the SGC200 edge gateway used to push device status into Netilion Value as a cryptic integer; E+H moved it into Netilion Health because the number gave customers little value.

---

## 2. Pattern decisions

**Adopt** means keep it recognisable. **Adapt** means keep the idea and change the form. **Replace** means do something different on purpose.

| # | E+H pattern | Source | Decision | Prototype rule |
| --- | --- | --- | --- | --- |
| P1 | Grid view / list view toggle of tanks | Fermentation dashboard | Adopt | S01 offers grid (default) and list; the choice is remembered per user |
| P2 | Tile opens the tank / batch detail | Fermentation | Adopt | Clicking a vessel tile opens S02 for its current batch, or vessel history if empty |
| P3 | Four primary values per tank, more behind "More information" | Fermentation Tank Details | Adapt | Four **pinned values** per product class (beer: extract, ABV, temperature, forecast end; NA: ABV, extract, temperature, margin used; kombucha: pH, extract, temperature, ABV); everything else under "All values" |
| P4 | Golden batch filter and overlay | Fermentation | Adapt | The golden batch becomes the **recipe envelope** (mean ± band); the overlay is on by default in S02 and S08 |
| P5 | Automatic batch start/stop (tank filled; tank empty or below temperature) | Fermentation | Adopt and extend | Vessel settings show the same three triggers in E+H wording, plus "ERP fill event"; detected events are labelled "detected", never presented as user actions |
| P6 | Sample preparation adjustment toggle ("History" vs "History Adjusted") | Fermentation | Adopt | QWX43 charts in S02 offer "Lab-comparable values (MEBAK)"; when on, the chart title says so and lab points are compared against adjusted values |
| P7 | Thresholds Low Low / Low / High / High High on the tag, drawn on the chart | Value | Adapt | Limits live on the **recipe stage** and **compliance profile**, not the device; two levels (warning, critical) are drawn as dashed lines; the warning-margin line for NA profiles is labelled with its number |
| P8 | Threshold e-mail to everyone with access | Value, Fermentation | Replace | Alerts go to the roles that act on them (section 6.6), with severity and evidence; no "everyone" broadcasts |
| P9 | NE 107 status with cause and remedy text | Health, QWX43 diagnostics | Adopt | Device status chips use the NE 107 letters and colours; the device drawer shows the code, short text and remedy exactly as the vendor states it |
| P10 | Heartbeat Verification: passed / not passed + PDF | Health | Adapt | The same visual grammar (large verdict, short evidence list, PDF) is reused for **compliance certificates** (S04) and the calibration record |
| P11 | Asset from serial number with auto-filled product data | Library, Fermentation | Adopt | "Add device" asks for vendor and serial number first; E+H serials auto-fill model and photo (mocked) |
| P12 | Asset and tag as separate, re-assignable objects | Netilion object model | Adopt | Devices are assigned to vessels with validity dates (bitemporal); the device page shows its assignment history |
| P13 | Separate apps per service (Value, Health, Library, Fermentation) | Netilion portfolio | Replace | One workspace: device health, values, documents and batches are tabs and drawers of the same objects, not separate apps |
| P14 | CSV export of the chart's time window | Fermentation, Value | Adopt | Every chart has "Export CSV" for exactly what is on screen, including the units and adjustment state |
| P15 | Red exclamation for available update, green tick when done | Firmware Update Scheduler | Adopt for device lists | S12 uses the same convention for firmware and calibration due |
| P16 | Device-centric wording ("Asset Details", "process variable") | Netilion | Replace | Brewer wording first (section 7); vendor terms appear once in the device drawer for traceability |
| P17 | Freeform dashboards | Value, Network Insights | Replace | Opinionated screens built around the brewer's day; no widget builder in the prototype |

---

## 3. Use-case handling: E+H today vs DataVest Brew

| Use case | How E+H handles it today | How the prototype handles it | Why the difference matters |
| --- | --- | --- | --- |
| Commission a sensor | QWX43 hotspot, web page at 10.10.0.1, setup wizard; then create the asset in Netilion by serial number and assign a tank | S12 "Add device": vendor → serial or QR → vessel → test reading; Tilt, iSpindel and PLC tags use the same three steps | One flow for every brand is the core of the vendor-neutral value path (G2) |
| Start a batch | Automatic start on tank filled, or manual "Create batch" with recipe and tank | Automatic from fill signal or ERP event, bound to recipe and ERP batch ID; manual create stays available | Same mental model as Netilion Fermentation, plus ERP identity |
| Watch fermentation | Tank tile; four primary values; history chart; golden batch overlay | Vessel tile with stage, envelope deviation, forecast with band and trust; curve with envelope, events, lab points | Adds stage, forecast and trust, which E+H does not show |
| Get alerted | Recipe threshold with tolerance; e-mail when reached | Rule-based alerts with evidence drawer and suggested checks; routed by role; acknowledge / snooze / note | Moves from "a number crossed" to "what happened and what to check" |
| Diagnose a device | NE 107 status on Tank Details; diagnostic code with remedy; LEDs on device | Device status chip on tile and in S12; drawer with code, cause and remedy; trust score and drift residual next to it | Device health and data trust are shown together, so a bad sensor cannot pass as a process problem |
| Verify a device | Heartbeat Verification remotely: passed / not passed, PDF | Calibration record and drift check against lab values; verdict layout borrowed from Heartbeat | Floating hydrometers have no Heartbeat; lab residuals fill that role |
| Compare to the best batch | Golden batch overlay per tank | Recipe envelope across all batches and sites, time-aligned; outlier ranking | Cross-site comparison is a lead scenario (S3) |
| Prove compliance | Not addressed | Compliance board, continuous trace against limit, lab confirmation, signed certificate | Lead scenarios S1 and S2 |
| Trace a lot | Not addressed | Trace explorer from any raw-material, yeast or packaged lot; recall scope report | Lead scenario S4 |
| Export data | CSV of the chart; asset history | CSV of the chart window; batch report, certificate and recall scope as PDF | Same habit, more outputs |

---

## 4. Information architecture

### 4.1 Navigation

Left navigation, grouped by the brewer's intent, never by data source:

```
Operate     Tank board (S01) · Alerts (S07)
Assure      Compliance (S03) · Trace (S05) · Lab results (S06)
Analyse     Compare sites (S08) · Reports (S10) · Assistant (S09)
Configure   Recipes and limits (S11) · Devices (S12)
```

Header, left to right: organisation and site selector · global search (vessel, batch code, lot code, device serial) · units toggle (°P/SG, °C/°F, hL/bbl) · role switcher (prototype only) · Alerts bell with open count.

S02 (batch) and S04 (certificate) are reached from other screens, not from the navigation.

### 4.2 Object pages share one anatomy

Every object page (batch, vessel, device, lot, recipe) uses the same structure, because Netilion users already expect it from Tank Details and Asset Details:

```
┌────────────────────────────────────────────────────────────────────────┐
│ Identity row   [batch badge] PI-2665 · Pike IPA · Riverside FV-07       │
│                status chips: Stage · Alert count · Device status (NE107)│
├────────────────────────────────────────────────────────────────────────┤
│ Pinned values  four tiles, last valid value + time + provenance marker │
├────────────────────────────────────────────────────────────────────────┤
│ Main chart     time range · series toggles under the graph · export    │
├───────────────────────────────────────┬────────────────────────────────┤
│ Tabs: Events · Lab and QA · Alerts ·   │ Side panel: actions log        │
│ Lots · Compliance                      │ (who did what, when)           │
└───────────────────────────────────────┴────────────────────────────────┘
```

Related objects appear as linked rows (assigned batches on a vessel, assigned device on a batch), the way Netilion lists assigned batches and the assigned asset at the bottom of Tank Details.

### 4.3 Terminology map

| Netilion term | DataVest Brew term (UI) | Note |
| --- | --- | --- |
| Asset | Device | "Asset" appears once in the device drawer as "Netilion asset ID" |
| Instrumentation / tag | Measuring point | Shown as "FV-07 · gravity"; rarely needed by brewers |
| Tank | Vessel | Vessel type shown (fermenter, unitank, BBT) |
| Recipe (beer type) | Recipe | Same |
| Batch | Batch | Same |
| Golden batch | Recipe envelope | Tooltip: "Mean and normal range of past batches of this recipe" |
| Primary values (PV, SV, TV, QV) | Pinned values | Up to four |
| Thresholds | Limits (recipe) · Compliance limit (profile) | Alerts are what limits produce |
| History Adjusted / sample preparation adjustment | Lab-comparable values (MEBAK) | |
| NE 107 status | Device status | F, C, S, M with names |
| Cause and remedy | Cause and remedy | Same, verbatim from vendor |
| Heartbeat Verification | Device verification | Only for devices that support it |

---

## 5. Visual design

### 5.1 Direction

The subject is a working fermentation cellar seen through instruments: steel vessels, glycol jackets, wort turning to beer, lab sheets. The design should feel like a well-made **instrument panel for brewers**: calm, precise and dense where it needs to be, and warm in exactly one place, the product itself.

It must not look like a recoloured Netilion. In the vendor-neutral vehicle it carries DataVest identity. In the E+H partner vehicle, colour and logo tokens are swapped through the theme layer (section 5.7), only with E+H-approved brand values. Do not invent or copy E+H brand colours.

The one memorable element is the **vessel glyph** on the tank board (section 5.5). Everything around it stays quiet.

### 5.2 Colour tokens

Base palette (light theme). The teal must be replaced with the exact value from the DataVest "Interface Node" logo file before release.

| Token | Hex | Role |
| --- | --- | --- |
| `--surface` | `#F4F7F7` | App background (cool, slightly steel) |
| `--panel` | `#FFFFFF` | Cards, tables, drawers |
| `--ink` | `#13252B` | Primary text (deep blue-green, not black) |
| `--ink-muted` | `#56686E` | Secondary text, axis labels |
| `--rule` | `#D5DFE0` | Borders, gridlines |
| `--accent` | `#0F7F7A` | DataVest teal: primary actions, focus, selection |
| `--wort` | `#B9782A` | Product colour: extract curve, vessel glyph fill, golden accents in charts only |

Dark theme (tablet in a dim cellar or a control room):

| Token | Hex |
| --- | --- |
| `--surface` | `#0E1A1E` |
| `--panel` | `#15252B` |
| `--ink` | `#E3ECEC` |
| `--ink-muted` | `#93A6AA` |
| `--rule` | `#2A3D43` |
| `--accent` | `#34B3AA` |
| `--wort` | `#D69A45` |

**Status colours** come in three independent families. Each family pairs colour with an icon and a word, never colour alone.

| Family | State | Hex | Icon idea | Label |
| --- | --- | --- | --- | --- |
| Device status (NE 107) | Failure (F) | `#C8322B` | Filled square with cross | "Failure" |
| | Function check (C) | `#D9771E` | Triangle with wrench | "Function check" |
| | Out of specification (S) | `#C9A20F` | Triangle with question mark | "Out of spec" |
| | Maintenance required (M) | `#2E6DB0` | Circle with oil can | "Maintenance" |
| | OK | `#2F8A5B` | Check | "OK" |
| Alert severity | Critical | `#C8322B` | Filled circle with ! | "Critical" |
| | Warning | `#C9A20F` | Outlined triangle | "Warning" |
| | Info | `#56686E` | Outlined circle with i | "Info" |
| Compliance | Compliant | `#2F8A5B` | Shield with check | "Compliant" |
| | At risk | `#C9A20F` | Shield with clock | "At risk" |
| | Breach | `#C8322B` | Shield with cross | "Breach" |
| | Hold | `#56686E` | Lock | "On hold" |
| | Pending lab | outline only | Flask | "Pending lab" |

**Trust** is shown as a dot next to a value: good = filled `--ink-muted`, fair = half-filled, poor = hollow with the value struck through in charts. No extra colour, so it never competes with status.

**Recipe colours** (batch badges, series in comparison charts) come from the recipe records in the dataset (`recipes.json`). Never reuse a status colour for a recipe.

### 5.3 Typography

| Role | Face | Size / weight | Notes |
| --- | --- | --- | --- |
| Display numbers (pinned values, big verdicts) | Space Grotesk | 28–40 px / 500 | Matches the DataVest wordmark; tabular figures on |
| Headings | Space Grotesk | 22 / 18 / 15 px, weight 600 | Sentence case |
| Body and UI | IBM Plex Sans | 14 px / 400, line-height 1.45 | 13 px in dense tables |
| Data tables and axis labels | IBM Plex Sans | 12–13 px, `font-variant-numeric: tabular-nums` | Never monospace for labels |
| Vendor codes and serials | IBM Plex Sans | 12 px, tabular, letter-spacing 0.02em | e.g. "QWX43 · S7035925195" |

Rules: sentence case everywhere, no all-caps labels, no eyebrow labels above headings, no single-word accent colouring in headings. Line length ≤ 80 characters in prose (help text, remedies, assistant answers).

**Number formatting:**
- Extract: 1 decimal (°P) or 3 decimals (SG).
- Temperature: 1 decimal.
- ABV: 1 decimal for beer; **2 decimals for NA and kombucha** profiles, where 0.45 vs 0.50 matters.
- pH: 2 decimals.
- Durations: "in 2 d 4 h" with a band such as "± 9 h".
- Units always visible next to the value, in `--ink-muted`.

### 5.4 Layout and density

- 12-column grid, 24 px gutters on desktop; 8 px spacing scale (4, 8, 12, 16, 24, 32, 48).
- Corner radius by hierarchy, not one value everywhere: 2 px on chips and table cells, 6 px on cards and tiles, 10 px on drawers and modals.
- Elevation only for things that float (drawers, menus, toasts). Cards on the board are separated by `--rule` borders, not shadows.
- Left-aligned content throughout; centre only the verdict on S04.
- Dense by default for desktop tables (36 px rows); comfortable on tablet (48 px rows, 44 px touch targets).

### 5.5 The vessel glyph (signature element)

Each tile on S01 has a small vertical vessel silhouette (conical fermenter or flat BBT, by vessel type) that encodes the batch at a glance:

- **Fill height:** attenuation progress, from OE (empty) to FE (full). It answers "how far along is it?" without reading numbers. Kombucha uses sugar consumed instead.
- **Fill colour:** `--wort` at an opacity that deepens with the stage. In conditioning and crash the fill turns cooler, using the accent tint.
- **Inside the glyph:** a thin line for the recipe envelope position. If the batch is outside the envelope, the line sits outside the fill edge.
- **Status corner:** the top-right holds at most one marker, in priority order: device Failure > critical alert > compliance breach > warning. The others are counted in the tile footer.

```
┌──────────────────────────────┐
│ FV-07          [PI-2665]  ▲1 │   vessel code · batch badge · alert count
│  ╭─╮                          │
│  │ │   Active · 96 h          │   stage · hours from pitch
│  │▓│   6.5 °P   ↘ stalled     │   pinned value 1 + trend word
│  │▓│   19.0 °C                │   pinned value 2
│  ╰▽╯   End: unknown  ± 48 h   │   forecast with band
│ Tilt ◐ fair · PLC ● ok        │   devices with trust/status
└──────────────────────────────┘
```

No gauges, donuts or speedometers anywhere in the product.

### 5.6 Charts

The main chart (S02) follows Netilion's habits and adds brewing context:

1. **Time axis:** hours from pitch by default; toggle to clock time. Netilion uses clock time; brewers reason in hours from pitch.
2. **Series:** at most four at once, chosen with toggles under the graph. This follows the Netilion Fermentation precedent of four series, and keeps the chart readable.
3. **Envelope:** recipe mean as a thin line and the normal range as a 12% `--wort` band behind the data.
4. **Limits:** dashed lines with the value printed at the right end. The NA warning margin and limit are both drawn.
5. **Events:** vertical ticks with small icons at the top (pitch, dry hop, temperature change, crash, transfer, dealcoholisation, packaging, CIP). Hovering shows who or what recorded it.
6. **Lab points:** hollow circles on the matching series, with inline vs lab difference on hover.
7. **Trust:** poor-trust segments are dashed and greyed, with the reason on hover.
8. **Forecast:** a hatched band from now to the forecast end. While the lag phase is uncertain, the band is wider and labelled "Early estimate".
9. **Adjusted values:** when MEBAK adjustment is on, the chart title reads "Lab-comparable values (MEBAK)".
10. **Export:** "Export CSV" exports exactly the visible window and series.

Comparison chart (S08): recipe envelope band, one thin line per batch in its recipe colour, outliers drawn heavier with a label at the line end. No legend box; label lines directly.

### 5.7 Theme layer

All colours, the logo slot and the product name are CSS variables, so the E+H partner vehicle can be re-themed without touching components:

```css
:root {
  --surface: #F4F7F7; --panel: #FFFFFF; --ink: #13252B; --ink-muted: #56686E;
  --rule: #D5DFE0; --accent: #0F7F7A; --wort: #B9782A;
  --ne107-f: #C8322B; --ne107-c: #D9771E; --ne107-s: #C9A20F; --ne107-m: #2E6DB0; --ok: #2F8A5B;
  --radius-chip: 2px; --radius-card: 6px; --radius-float: 10px;
  --font-display: "Space Grotesk", "IBM Plex Sans", system-ui, sans-serif;
  --font-ui: "IBM Plex Sans", system-ui, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --surface: #0E1A1E; --panel: #15252B; --ink: #E3ECEC; --ink-muted: #93A6AA;
    --rule: #2A3D43; --accent: #34B3AA; --wort: #D69A45;
  }
}
:root[data-theme="dark"] { /* same values as the media query block */ }
[data-brand="partner"] { /* --accent, logo and product name from the partner's approved brand kit */ }
```

Tailwind users: map these variables in `theme.extend.colors` (for example `accent: 'var(--accent)'`) instead of using Tailwind's default palette.

### 5.8 Motion

One deliberate moment: when a new reading arrives on S01, the value cross-fades and the glyph fill eases to its new height over 400 ms. Nothing else moves on its own.

Motion that answers an action is welcome: drawers slide in, an acknowledged alert collapses into the history list. Respect `prefers-reduced-motion` by switching to instant changes.

---

## 6. Components and interaction rules

### 6.1 Core components

| Component | States | Notes |
| --- | --- | --- |
| Batch badge | default, selected, shared (brand-owner view) | Compact: recipe colour stripe + batch code; never a large card |
| Status chip | NE 107 (F/C/S/M/OK), alert severity, compliance state, stage | Icon + word; colour from its family only |
| Pinned value tile | live, stale (> 3× interval), poor trust, adjusted | Value, unit, time since, provenance marker (device-derived ◇ / platform-estimated ○) |
| Vessel tile | active, empty, CIP, offline | See 5.5 |
| Evidence drawer | — | Opens from any alert, compliance line or assistant citation; shows the exact window or record |
| Device drawer | — | Vendor, model, serial, Netilion asset ID, NE 107 status, cause and remedy, calibration, trust, assignment history |
| Verdict panel | passed, not passed, pending lab | Large verdict, evidence list, signer, PDF; used on S04 and for calibration |
| Trace graph | — | Left-to-right columns: raw material → brew → batch → packaged; node drawer with evidence |
| Actions log | — | Chronological list of user and system actions on the object |

### 6.2 Device health vs process alerts vs compliance

These are three different questions and must never be merged into one status:

- **Device status (NE 107):** "Can I trust this instrument?"
  - Lives on: device chip, device drawer, S12.
- **Alert:** "Is the process or data doing something I must react to?"
  - Lives on: S07, alert count on tiles, evidence drawer.
- **Compliance:** "Can this batch or lot be released against its legal limit?"
  - Lives on: S03, S04, compliance tab on S02.

A device Failure on a tank raises one alert, "Device failure on FV-03 gravity". The tile shows the device chip, not a process-severity colour.

### 6.3 Cause and remedy

When a device reports a diagnostic code, show it as Netilion does: code, short text, remedy, NE 107 letter. Add one DataVest line underneath saying what this means for the batch, for example "Gravity readings since 14:20 are excluded from the forecast."

### 6.4 Detected vs entered

Automatic batch start and stop, stage changes and transfers that the system detects are labelled "detected" with the rule that triggered them (for example "Detected: tank filled"). User-entered events show the user. This mirrors the Automatic Batch Start/Stop Recognition logic and keeps the actions log honest.

### 6.5 Never control equipment

There are no setpoint, valve, start, stop or "send to PLC" controls anywhere. Setpoints appear only as a read-only reference series. Vessel settings that look like E+H's tank configuration (for example the maximum head pressure the QWX43 needs) are **reference values for calculation**, labelled as such.

### 6.6 Alert routing and actions

| Severity | Default recipients | Channels (prototype shows settings only) |
| --- | --- | --- |
| Critical | Head brewer, operator on shift, compliance lead (if a compliance rule) | In-app + push + e-mail |
| Warning | Head brewer, operator | In-app + push |
| Info | Head brewer | In-app digest |

Actions keep the same names through the flow:

| Action | Resulting state | Toast |
| --- | --- | --- |
| Acknowledge | Acknowledged | "Alert acknowledged" |
| Snooze | Snoozed | "Snoozed until 14:00" |
| Add note | — | — |
| Resolve | Resolved | — |

### 6.7 Empty, loading, error

- **Empty vessel:** shows last batch, CIP status and "Waiting for fill". No blank tile.
- **No data from a device:** "No readings from Tilt T-112 since 09:12. Check the gateway power and range." Never "Something went wrong".
- **Loading:** skeleton shapes in the final layout; no spinners over charts.

### 6.8 Accessibility

- WCAG 2.2 AA contrast for text and status icons on both themes.
- Status never by colour alone (icon + word).
- Visible focus ring in `--accent`, 2 px, offset 2 px.
- All charts have a table view ("View as table") with the same window.
- Touch targets ≥ 44 px on tablet layouts (S01, S02, S07).

---

## 7. Voice and copy

- Brewer language first: vessel, batch, gravity, attenuation, pitch, crash, dry hop, bright tank. Vendor and protocol terms appear only in device and integration views.
- Plain, active, specific. "Extract has dropped 0.1 °P in 12 h. Fermentation may have stalled." Not "Anomaly detected".
- Errors say what happened and what to do, in the interface's voice, without apologising.
- Buttons say what happens: "Sign certificate", "Generate recall scope", "Export CSV", "Add device".
- Compliance copy never claims legal certification: "Prepared by DataVest Brew · Released by Daniel Price".
- Forecasts always carry their uncertainty: "Ready in about 2 days (± 9 h)". Never a bare date.

---

## 8. Screen notes (S01–S12)

| Screen | E+H patterns kept | What makes it a step up | Design notes |
| --- | --- | --- | --- |
| S01 Tank board | Grid/list toggle; tile → detail; search | Vessel glyph, stage, forecast band, trust, single priority marker | Sort: open critical → decision due → nominal; site filter in header |
| S02 Batch detail | Primary values; history; golden batch; MEBAK toggle; CSV export | Envelope, events, lab points, forecast, trust segments, actions log, compliance tab | Object page anatomy (4.2); "Ask about this batch" opens S09 with context |
| S03 Compliance board | — (not in E+H) | Continuous record vs limit, margin used, lab confirmed, certificate state | Table first; kombucha projection column with a mini sparkline |
| S04 Certificate | Heartbeat verdict grammar | Lot-level evidence, signer, inline vs lab difference | Centred verdict, evidence list left-aligned below; "Sign certificate" only for compliance lead with lab confirmation |
| S05 Trace explorer | Library's asset + documents idea | One-up/one-down lot graph with evidence | Columns by lot type; selected path highlighted; "Generate recall scope" |
| S06 Lab results | Library uploads with categories | Column mapping, spec status, auto-attach by batch code | Show the parsed preview before saving; out-of-spec rows flagged in-line |
| S07 Alerts | Threshold e-mails (replaced) | Evidence drawer, suggested checks, routing, actions | Group by vessel; critical pinned on top |
| S08 Compare sites | Golden batch overlay | Time-aligned trajectories across sites and partners, share-grant aware | Direct labels on lines; outlier table beside the chart |
| S09 Assistant | — | Answers with numbered citations to records | Separate page; context chip at the top; citations open the evidence drawer |
| S10 Reports | CSV export | Batch report, compliance summary, recall scope, comparison | List of generated documents with type, period, author |
| S11 Recipes and limits | Recipe page; recipe thresholds with tolerance | Stage plan, envelope, specs, compliance profiles | Limits shown on a mini chart while editing; read-mostly in the prototype |
| S12 Devices | Asset list; NE 107 status; cause and remedy; firmware scheduler marks; add asset by serial | Mixed-brand fleet, trust, drift residuals vs lab, calibration due | "Add device" flow: vendor → serial / QR → vessel → test reading |

---

## 9. Design definition of done

- [ ] A Netilion Fermentation user recognises S01 and S02 within a minute: grid/list toggle, tile → detail, four pinned values, envelope overlay, MEBAK toggle and CSV export are all present.
- [ ] Device status (NE 107), alerts and compliance use separate visual families and never share a single indicator.
- [ ] Every status shows icon + word; every chart has a table view.
- [ ] No control of equipment anywhere; setpoints are read-only reference lines.
- [ ] All numbers use tabular figures and the formatting rules in 5.3; NA and kombucha ABV show two decimals.
- [ ] Forecasts always show a band; early estimates are labelled.
- [ ] Light and dark themes pass AA contrast; the partner theme can be applied by changing CSS variables only.
- [ ] The vessel glyph is the only decorative element on S01; nothing else animates on its own.
- [ ] Copy follows section 7: brewer language, active verbs, specific errors, no legal claims.

---

## 10. Sources

- E+H, *Operating Instructions Fermentation Monitor QWX43*, BA02162F/00/EN/03.24 — Netilion Fermentation pages, automatic batch start/stop, recipe thresholds, sample preparation adjustment, NE 107 diagnostics. https://bdih-download.endress.com/file/005056A5E3831EEFA9FE73CC28DBB974/BA02162FEN_0324-00.pdf
- Netilion Help: *How to set thresholds* (Netilion Value). https://help.netilion.endress.com/hc/en-us/articles/360020853819-How-to-set-thresholds
- Netilion Help: *How to use remote Heartbeat Verification with Netilion Health*. https://help.netilion.endress.com/hc/en-us/articles/5898705691036-How-to-use-remote-Heartbeat-Verification-with-Netilion-Health
- Netilion Help: *Get started with Library*. https://help.netilion.endress.com/hc/en-us/articles/360015891119-Get-started-with-Library
- Netilion Help: *The difference between Assets and Tags*. https://help.netilion.endress.com/hc/en-us/articles/360005117440-The-difference-between-Assets-and-Tags-in-the-Netilion-Ecosystem
- Netilion Help: *SGC200 Field Device Status*. https://help.netilion.endress.com/hc/en-us/articles/20021243500444-SGC200-Field-Device-Status
- Netilion developer docs: *Netilion Objects*. https://developer.netilion.endress.com/development/netilion_objects/
- Netilion blog: *NAMUR NE 107 in less than 5 minutes*. https://netilion.endress.com/blog/namur-ne-107-videos
- E+H: *Monitoring the asset health status* (cause and remedy). https://www.be.endress.com/en/industry-expertise/process-solutions/monitoring-asset-health-status
- Netilion Value product page. https://netilion.endress.com/value
- Netilion Scanner (App Store listing). https://apps.apple.com/app/id1327266657
- E+H: *Smart water network solutions* (Netilion Network Insights). https://endress.com/en/solutions-lowering-costs/water-network-insights
- Internal: Brewery Process Intelligence Platform — Solution architecture and Prototype spec (Intetics, October 2026); DataVest brand decisions (logo "Interface Node", Space Grotesk, teal accent).

UI descriptions of E+H products are taken from E+H's public manuals and help pages. Screens were not inspected in a live Netilion account; validate in a Netilion trial before the E+H conversation.
