"""Krausen logo kit generator: SVG variants (text converted to paths) + PNG exports."""
import os
import cairosvg
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

OUT = "/home/claude/logo/out"
os.makedirs(OUT, exist_ok=True)

C = {
    "ink": "#13242B",        # stout
    "steel": "#1E6F73",      # stainless-steel teal (tank)
    "steel_dark_bg": "#3A9A9C",
    "gold": "#E8B23A",       # krausen foam
    "foam": "#FFF4D6",       # curve on tank
    "surface": "#F3F6F6",    # cool light background
}

font = TTFont("/home/claude/logo/SpaceGrotesk-SemiBold.ttf")
gs = font.getGlyphSet(); cmap = font.getBestCmap(); upm = font["head"].unitsPerEm
cap = font["OS/2"].sCapHeight or 700

def text_path(text, size, x0, baseline, tracking=0.0):
    """Return SVG path data for text, left-aligned at x0, baseline at y."""
    s = size / upm; x = x0; d = []
    for ch in text:
        g = cmap[ord(ch)]
        pen = SVGPathPen(gs)
        tp = TransformPen(pen, (s, 0, 0, -s, x, baseline))
        gs[g].draw(tp)
        d.append(pen.getCommands())
        x += gs[g].width * s + tracking * size
    return " ".join(d), x - tracking * size

def mark(fill_tank, fill_foam, curve, simplified=False):
    """Krausen mark on a 64x64 grid: cylindroconical tank, krausen foam cap, falling extract curve."""
    tank = "M20 29 Q20 26 23 26 H41 Q44 26 44 29 V44 L34.6 55.5 V58.5 H29.4 V55.5 L20 44 Z"
    foam = [(25.2, 24.2, 5.6), (32.4, 20.2, 7.0), (39.6, 23.8, 5.8)]
    bubbles = [] if simplified else [(46.2, 14.2, 2.1), (50.2, 9.2, 1.4)]
    parts = [f'<path d="{tank}" fill="{fill_tank}"/>']
    parts += [f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill_foam}"/>' for x, y, r in foam + bubbles]
    if not simplified:
        parts.append(f'<path d="M24 32.5 C26.8 37.6 31 40.2 38.6 40.6" fill="none" stroke="{curve}" stroke-width="2.3" stroke-linecap="round"/>')
        parts.append(f'<circle cx="39.4" cy="40.6" r="1.9" fill="{curve}"/>')
    return "".join(parts)

def svg(w, h, body, bg=None, title="Krausen"):
    bgr = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{title}">'
            f'<title>{title}</title>{bgr}{body}</svg>')

def horizontal(dark=False, descriptor=False):
    ink = C["surface"] if dark else C["ink"]
    tank = C["steel_dark_bg"] if dark else C["steel"]
    size = 25.0 / (cap / upm)          # cap height 25 units
    baseline = 47.0
    word, xend = text_path("Krausen", size, 56, baseline, tracking=-0.012)
    body = f'<g>{mark(tank, C["gold"], C["foam"])}</g><path d="{word}" fill="{ink}"/>'
    w = int(xend + 8); h = 64
    if descriptor:
        dsize = size * 0.34
        dword, _ = text_path("Brewery MES", dsize, 57, baseline + 13, tracking=0.04)
        body += f'<path d="{dword}" fill="{tank}"/>'
        h = 66
    return w, h, body

def stacked(dark=False):
    ink = C["surface"] if dark else C["ink"]
    tank = C["steel_dark_bg"] if dark else C["steel"]
    size = 22.0 / (cap / upm)
    word, xend = text_path("Krausen", size, 0, 0, tracking=-0.012)
    w = max(int(xend) + 16, 120); mx = (w - 64) / 2
    tx = (w - xend) / 2
    word, _ = text_path("Krausen", size, tx, 92, tracking=-0.012)
    body = f'<g transform="translate({mx},2)">{mark(tank, C["gold"], C["foam"])}</g><path d="{word}" fill="{ink}"/>'
    return w, 104, body

def write(name, content):
    p = os.path.join(OUT, name)
    open(p, "w").write(content)
    return p

files = {}
w, h, b = horizontal(); files["krausen-logo-horizontal.svg"] = write("krausen-logo-horizontal.svg", svg(w, h, b))
w, h, b = horizontal(dark=True); files["krausen-logo-horizontal-dark.svg"] = write("krausen-logo-horizontal-dark.svg", svg(w, h, b))
w, h, b = horizontal(descriptor=True); files["krausen-logo-descriptor.svg"] = write("krausen-logo-descriptor.svg", svg(w, h, b))
w, h, b = horizontal(dark=True, descriptor=True); files["krausen-logo-descriptor-dark.svg"] = write("krausen-logo-descriptor-dark.svg", svg(w, h, b))
w, h, b = stacked(); files["krausen-logo-stacked.svg"] = write("krausen-logo-stacked.svg", svg(w, h, b))
files["krausen-mark.svg"] = write("krausen-mark.svg", svg(64, 64, mark(C["steel"], C["gold"], C["foam"])))
files["krausen-mark-dark.svg"] = write("krausen-mark-dark.svg", svg(64, 64, mark(C["steel_dark_bg"], C["gold"], C["foam"])))
# app icon / favicon: simplified mark on ink rounded square
icon_body = (f'<rect width="64" height="64" rx="14" fill="{C["ink"]}"/>'
             f'<g transform="translate(32,33) scale(1.12) translate(-33,-36)">{mark(C["steel_dark_bg"], C["gold"], C["foam"], simplified=True)}</g>')
files["krausen-app-icon.svg"] = write("krausen-app-icon.svg", svg(64, 64, icon_body))
files["favicon.svg"] = write("favicon.svg", svg(64, 64, icon_body))

# PNG exports
for size in (16, 32, 48, 180, 192, 512):
    cairosvg.svg2png(url=files["krausen-app-icon.svg"], write_to=os.path.join(OUT, f"krausen-icon-{size}.png"), output_width=size, output_height=size)
cairosvg.svg2png(url=files["krausen-logo-horizontal.svg"], write_to=os.path.join(OUT, "krausen-logo-horizontal@2x.png"), scale=4)
cairosvg.svg2png(url=files["krausen-logo-horizontal-dark.svg"], write_to=os.path.join(OUT, "krausen-logo-horizontal-dark@2x.png"), scale=4)

# preview sheet
def embed(path, x, y, scale=1.0):
    inner = open(path).read()
    inner = inner[inner.index(">") + 1: inner.rindex("</svg>")]
    return f'<g transform="translate({x},{y}) scale({scale})">{inner}</g>'
sheet = (f'<rect width="900" height="620" fill="#FFFFFF"/>'
         f'<rect x="0" y="0" width="900" height="300" fill="{C["surface"]}"/>'
         f'<rect x="0" y="300" width="900" height="200" fill="{C["ink"]}"/>'
         + embed(files["krausen-logo-horizontal.svg"], 40, 40, 2.6)
         + embed(files["krausen-logo-descriptor.svg"], 40, 200, 1.3)
         + embed(files["krausen-logo-stacked.svg"], 700, 40, 1.4)
         + embed(files["krausen-logo-horizontal-dark.svg"], 40, 330, 2.0)
         + embed(files["krausen-logo-descriptor-dark.svg"], 520, 350, 1.3)
         + embed(files["krausen-app-icon.svg"], 40, 520, 1.25)
         + embed(files["krausen-app-icon.svg"], 140, 536, 0.75)
         + embed(files["krausen-app-icon.svg"], 200, 548, 0.375)
         + embed(files["krausen-app-icon.svg"], 236, 556, 0.25)
         + "".join(f'<rect x="{420 + i * 95}" y="530" width="80" height="50" rx="8" fill="{c}" stroke="#D5DCDD"/>'
                   for i, c in enumerate([C["ink"], C["steel"], C["gold"], C["foam"], C["surface"]])))
write("krausen-logo-sheet.svg", svg(900, 620, sheet, title="Krausen logo sheet"))
cairosvg.svg2png(url=os.path.join(OUT, "krausen-logo-sheet.svg"), write_to=os.path.join(OUT, "krausen-logo-sheet.png"), scale=1.5)
print(sorted(os.listdir(OUT)))
