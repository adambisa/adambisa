"""Builds assets/header.svg: the portfolio's CRT mark beside a boxed name plate.

The mark is copied from moj-web-redesign/web/public/brand/mark-crt-anim.svg (glitch
every 3.2s, blinking block). The subtitle types itself out once, then a cursor blinks.
"""

from pathlib import Path
from xml.sax.saxutils import escape

INK = "#0d0d0d"
PAPER = "#ecebe6"
ACCENT = "#ff4a1c"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"

NAME = "ADAM BISA"
SUBTITLE = "SOFTWARE ENGINEER / ML / AI / DATA"
TYPE_START = 0.4
TYPE_STEP = 0.045

W, H = 840, 200
OUT = Path(__file__).resolve().parent.parent / "assets" / "header.svg"


def mark_glyph(fill: str, ast: str, cursor_blink: bool) -> str:
    cursor_anim = (
        '<animate attributeName="opacity" values="1;0" dur="1s" calcMode="discrete" repeatCount="indefinite"/>'
        if cursor_blink
        else ""
    )
    spokes = "".join(
        f'<rect x="-1.6" y="-7" width="3.2" height="14" rx="1.6" transform="rotate({r})"/>' for r in (0, 60, -60)
    )
    return (
        f'<circle cx="15" cy="35" r="7" fill="none" stroke="{fill}" stroke-width="5"/>'
        f'<rect x="20" y="25.5" width="5" height="19" fill="{fill}"/>'
        f'<g transform="translate(34 26)" fill="{ast}">{spokes}</g>'
        f'<rect x="43" y="22" width="12" height="22.5" fill="{fill}">{cursor_anim}</rect>'
    )


def scanlines(fill: str) -> str:
    return "".join(f'<rect x="0" y="{y}" width="64" height="1.2" fill="{fill}" opacity=".55"/>' for y in range(2, 64, 4))


def mark(x: int, y: int, size: int) -> str:
    glitch_times = 'keyTimes="0;.88;.9;.93;.95;1" dur="3.2s" calcMode="discrete" repeatCount="indefinite"'
    return f"""<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 64 64">
  <defs><clipPath id="mark-clip"><rect width="64" height="64" rx="14"/></clipPath></defs>
  <g clip-path="url(#mark-clip)">
    <rect width="64" height="64" fill="{INK}"/>
    <rect width="64" height="64" rx="14" fill="none" stroke="#2a2a28" stroke-width="2"/>
    <g opacity="0">
      <g transform="translate(3 0)">{mark_glyph(ACCENT, ACCENT, False)}{scanlines(ACCENT)}</g>
      <animate attributeName="opacity" values="0;0;.8;0;.8;0" {glitch_times}/>
    </g>
    <g>
      {mark_glyph(PAPER, ACCENT, True)}{scanlines(INK)}
      <animateTransform attributeName="transform" type="translate" values="0 0;0 0;-2 0;2 1;-1 0;0 0" {glitch_times}/>
    </g>
  </g>
</svg>"""


def typed(text: str) -> str:
    """One tspan per character, hidden until its turn; renderers without SMIL just show the full line."""
    spans = []
    for i, ch in enumerate(text):
        begin = TYPE_START + i * TYPE_STEP
        spans.append(f'<tspan>{escape(ch)}<set attributeName="opacity" to="0" begin="0s" end="{begin:.3f}s"/></tspan>')
    done = TYPE_START + len(text) * TYPE_STEP
    spans.append(
        f'<tspan fill="{ACCENT}">█'
        f'<set attributeName="opacity" to="0" begin="0s" end="{done:.3f}s"/>'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1s" begin="{done:.3f}s" repeatCount="indefinite"/>'
        "</tspan>"
    )
    return "".join(spans)


def build() -> str:
    frame = 14
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{NAME}, {SUBTITLE}">
  <title>{NAME} / {SUBTITLE}</title>
  <rect width="{W}" height="{H}" fill="{INK}"/>
  <rect x="{frame}" y="{frame}" width="{W - 2 * frame}" height="{H - 2 * frame}" fill="none" stroke="{PAPER}" stroke-width="6"/>
  <rect x="{frame + 10}" y="{frame + 10}" width="{W - 2 * frame - 20}" height="{H - 2 * frame - 20}" fill="none" stroke="{PAPER}" stroke-width="1.5" stroke-dasharray="2 4"/>
  {mark(52, 44, 112)}
  <rect x="196" y="50" width="2" height="100" fill="{PAPER}" opacity=".35"/>
  <text x="226" y="96" fill="{PAPER}" font-family="{MONO}" font-size="44" font-weight="800" letter-spacing="3">{NAME}</text>
  <text x="228" y="134" fill="{PAPER}" font-family="{MONO}" font-size="19" font-weight="600" letter-spacing="1.5">{typed(SUBTITLE)}</text>
  <rect x="{W - frame - 120}" y="{frame + 18}" width="88" height="18" fill="{ACCENT}"/>
  <text x="{W - frame - 76}" y="{frame + 31}" fill="{INK}" font-family="{MONO}" font-size="11" font-weight="700" text-anchor="middle" letter-spacing="1">ON AIR</text>
</svg>
"""


if __name__ == "__main__":
    OUT.write_text(build())
    print(f"wrote {OUT}")
