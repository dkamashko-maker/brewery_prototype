# Krausen — logo and brand basics

**Krausen** is a cloud MES for breweries. The descriptor is **Brewery MES**. Write the name as *Krausen* (capital K, no umlaut, never all caps).

## The mark

A cylindroconical fermenter with a golden foam cap rising over the top — the *krausen*, the sign of active fermentation. Inside the tank, a falling extract curve ends in a data point: fermentation measured, not guessed.

## Files

| File | Use |
| --- | --- |
| `krausen-logo-horizontal.svg` | Main logo on light backgrounds (app header, documents) |
| `krausen-logo-horizontal-dark.svg` | Main logo on dark backgrounds |
| `krausen-logo-descriptor.svg`, `-dark.svg` | Logo with “Brewery MES” (login screen, title slides) |
| `krausen-logo-stacked.svg` | Square spaces (splash screen, empty states) |
| `krausen-mark.svg`, `krausen-mark-dark.svg` | Mark alone, 40 px and larger |
| `krausen-app-icon.svg`, `favicon.svg` | App icon and browser tab (simplified mark on Stout) |
| `krausen-icon-{16,32,48,180,192,512}.png` | Favicon, Apple touch icon, PWA icons |
| `krausen-logo-horizontal@2x.png`, `-dark@2x.png` | Raster logo for slides and email |
| `krausen-logo-sheet.png` | Overview of all variants and colours |

All SVG text is converted to outlines, so the logo does not depend on installed fonts.

## Colours

| Name | Hex | Role | Contrast |
| --- | --- | --- | --- |
| Stout | `#13242B` | Text, dark backgrounds, app icon | 14.7:1 on Surface |
| Steel | `#1E6F73` | Tank, primary actions, links | 5.4:1 on Surface (AA) |
| Steel Light | `#3A9A9C` | Tank and accents on dark backgrounds | 4.8:1 on Stout (AA) |
| Krausen Gold | `#E8B23A` | Foam, highlights, active fermentation | 8.3:1 on Stout; 1.9:1 on white — never for text on light backgrounds |
| Foam | `#FFF4D6` | Curve on the tank, soft highlight fills | — |
| Surface | `#F3F6F6` | Light app background | — |

Status colours (device health, alert severity, release state) stay separate from brand colours and are defined in the design brief.

## Typography

- **Space Grotesk** (SemiBold 600) — the wordmark, headings and key numbers.
- **IBM Plex Sans** — interface and body text.

Both are free on Google Fonts.

## Rules

- **Clear space:** keep free space around the logo equal to the height of the largest foam circle.
- **Minimum size:** horizontal logo 120 px wide; mark alone 24 px; below 24 px use the app icon.
- **Backgrounds:** light variants on Surface or white; dark variants on Stout.
- **Don't:** recolour the foam, stretch or rotate the logo, add effects, or place the light logo on busy photos.

## Tokens for the prototype

```css
:root {
  --krausen-stout: #13242B;
  --krausen-steel: #1E6F73;
  --krausen-steel-light: #3A9A9C;
  --krausen-gold: #E8B23A;
  --krausen-foam: #FFF4D6;
  --krausen-surface: #F3F6F6;
  --font-display: "Space Grotesk", system-ui, sans-serif;
  --font-body: "IBM Plex Sans", system-ui, sans-serif;
}
```

In the Lovable project, place the files in `public/brand/` and set the favicon:

```html
<link rel="icon" type="image/svg+xml" href="/brand/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="/brand/krausen-icon-32.png">
<link rel="apple-touch-icon" href="/brand/krausen-icon-180.png">
```
