#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Deterministic SVG generator for the experimental-setup diagrams used in the
documentation. Every diagram is emitted in a light and a dark variant
(``*_dark.svg``) with the same palette as the matplotlib figures, so the
docs can theme-switch them exactly like the PNG plots.

Run directly or via ``make graphs``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    suffix: str
    bg: str
    fg: str
    muted: str
    panel: str
    primary: str
    secondary: str
    accent: str


LIGHT = Theme(
    suffix="", bg="#ffffff", fg="#1a1a1a", muted="#666666", panel="#f0f2f5",
    primary="#1f77b4", secondary="#d62728", accent="#2ca02c",
)
DARK = Theme(
    suffix="_dark", bg="#0d1117", fg="#e6e6e6", muted="#9a9a9a", panel="#1c2128",
    primary="#4da3d8", secondary="#e46a6a", accent="#5abf5a",
)

_FONT = "Segoe UI, Helvetica, Arial, sans-serif"
_MONO = "Consolas, Menlo, monospace"


class SVG:
    """Tiny element accumulator with technical-drawing helpers."""

    def __init__(self, width: int, height: int, th: Theme) -> None:
        self.w, self.h, self.th = width, height, th
        self.parts: list[str] = []

    # -- primitives -------------------------------------------------------
    def add(self, fragment: str) -> None:
        self.parts.append(fragment)

    def rect(self, x: float, y: float, w: float, h: float, fill: str,
             stroke: str = "none", rx: float = 0.0, sw: float = 1.5,
             dash: str = "") -> None:
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
                 f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def line(self, x1: float, y1: float, x2: float, y2: float, stroke: str,
             sw: float = 1.5, dash: str = "") -> None:
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                 f'stroke="{stroke}" stroke-width="{sw}"{d} stroke-linecap="round"/>')

    def circle(self, cx: float, cy: float, r: float, fill: str,
               stroke: str = "none", sw: float = 1.5) -> None:
        self.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" '
                 f'stroke="{stroke}" stroke-width="{sw}"/>')

    def text(self, x: float, y: float, s: str, size: int = 13,
             fill: str = "", anchor: str = "middle", bold: bool = False,
             mono: bool = False, italic: bool = False) -> None:
        fill = fill or self.th.fg
        w = ' font-weight="600"' if bold else ""
        i = ' font-style="italic"' if italic else ""
        fam = _MONO if mono else _FONT
        self.add(f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{size}" '
                 f'fill="{fill}" text-anchor="{anchor}"{w}{i}>{s}</text>')

    def path(self, d: str, fill: str = "none", stroke: str = "none",
             sw: float = 1.5) -> None:
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" '
                 f'stroke-width="{sw}" stroke-linejoin="round"/>')

    # -- technical helpers -------------------------------------------------
    def arrow(self, x1: float, y1: float, x2: float, y2: float, stroke: str,
              sw: float = 1.6) -> None:
        """Straight arrow with a filled head at (x2, y2)."""
        import math
        ang = math.atan2(y2 - y1, x2 - x1)
        L, W = 9.0, 3.6
        bx, by = x2 - L * math.cos(ang), y2 - L * math.sin(ang)
        px, py = -math.sin(ang), math.cos(ang)
        self.line(x1, y1, bx, by, stroke, sw)
        self.path(f"M {x2:.1f} {y2:.1f} L {bx + W * px:.1f} {by + W * py:.1f} "
                  f"L {bx - W * px:.1f} {by - W * py:.1f} Z", fill=stroke)

    def dim(self, x1: float, y1: float, x2: float, y2: float, label: str,
            offset: float = 0.0, size: int = 12) -> None:
        """Dimension line with arrowheads on both ends and a centred label.
        Works for horizontal or vertical dimensions (pick by coordinates)."""
        th = self.th
        horizontal = abs(y2 - y1) < abs(x2 - x1)
        if horizontal:
            y = y1 + offset
            self.line(x1, y1, x1, y, th.muted, 0.9, dash="3,3")
            self.line(x2, y2, x2, y, th.muted, 0.9, dash="3,3")
            mid = (x1 + x2) / 2
            self.arrow(mid - 4, y, x1, y, th.muted, 1.2)
            self.arrow(mid + 4, y, x2, y, th.muted, 1.2)
            self.text(mid, y - 5, label, size, th.fg, "middle")
        else:
            x = x1 + offset
            self.line(x1, y1, x, y1, th.muted, 0.9, dash="3,3")
            self.line(x2, y2, x, y2, th.muted, 0.9, dash="3,3")
            mid = (y1 + y2) / 2
            self.arrow(x, mid - 4, x, y1, th.muted, 1.2)
            self.arrow(x, mid + 4, x, y2, th.muted, 1.2)
            self.text(x + 7, mid + 4, label, size, th.fg, "start")

    def mic(self, x: float, y: float, scale: float = 1.0,
            label: str = "") -> None:
        """Measurement microphone glyph pointing up: capsule + body + stand."""
        th, s = self.th, scale
        self.line(x, y, x, y + 46 * s, th.fg, 2.0)                    # stand
        self.line(x - 12 * s, y + 46 * s, x + 12 * s, y + 46 * s, th.fg, 2.0)
        self.rect(x - 4 * s, y - 26 * s, 8 * s, 26 * s, th.primary, rx=3 * s)  # body
        self.rect(x - 3 * s, y - 34 * s, 6 * s, 8 * s, th.fg, rx=2 * s)        # capsule
        if label:
            self.text(x, y + 62 * s, label, 12, self.th.muted)

    def person(self, x: float, y: float, h: float = 90.0, seated: bool = False) -> None:
        """Simple engineering-style human silhouette; (x, y) = feet."""
        th = self.th
        r = h * 0.10
        if not seated:
            self.circle(x, y - h + r, r, th.muted)
            self.line(x, y - h + 2 * r, x, y - h * 0.35, th.muted, 3)
            self.line(x, y - h * 0.75, x - h * 0.18, y - h * 0.5, th.muted, 2.4)
            self.line(x, y - h * 0.75, x + h * 0.18, y - h * 0.5, th.muted, 2.4)
            self.line(x, y - h * 0.35, x - h * 0.13, y, th.muted, 2.4)
            self.line(x, y - h * 0.35, x + h * 0.13, y, th.muted, 2.4)
        else:
            self.circle(x, y - h + r, r, th.muted)
            self.line(x, y - h + 2 * r, x, y - h * 0.45, th.muted, 3)       # torso
            self.line(x, y - h * 0.45, x + h * 0.30, y - h * 0.45, th.muted, 2.4)  # thigh
            self.line(x + h * 0.30, y - h * 0.45, x + h * 0.30, y, th.muted, 2.4)  # shin
            self.line(x, y - h * 0.70, x + h * 0.22, y - h * 0.55, th.muted, 2.4)  # arm

    def ground(self, y: float, x1: float, x2: float, hatch: int = 24) -> None:
        th = self.th
        self.line(x1, y, x2, y, th.fg, 2.2)
        x = x1
        while x < x2:
            self.line(x, y, x - 8, y + 9, th.muted, 1.1)
            x += hatch

    def render(self, title: str) -> str:
        th = self.th
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" '
                f'height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
                f'<rect width="{self.w}" height="{self.h}" fill="{th.bg}"/>'
                f'<text x="{self.w / 2}" y="30" font-family="{_FONT}" '
                f'font-size="17" font-weight="600" fill="{th.fg}" '
                f'text-anchor="middle">{title}</text>')
        return head + "".join(self.parts) + "</svg>"


def _write(output_dir: str, name: str, build: "callable", title: str) -> None:  # type: ignore[valid-type]
    for th in (LIGHT, DARK):
        svg = SVG(980, 520, th)
        build(svg, th)
        path = os.path.join(output_dir, f"{name}{th.suffix}.svg")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(svg.render(title))
    print(f"Generated {name}.svg (+dark)")


# ---------------------------------------------------------------------------
# d1 - Calibration chain (IEC 60942)
# ---------------------------------------------------------------------------

def _d1(s: SVG, th: Theme) -> None:
    gy = 440.0
    s.ground(gy, 40, 940)

    # Calibrator on top of the microphone (left column)
    mx = 170.0
    cal_y = 120.0
    s.rect(mx - 34, cal_y, 68, 74, th.panel, th.fg, rx=8, sw=2)      # calibrator body
    s.text(mx, cal_y + 30, "94.0 dB", 14, th.secondary, bold=True, mono=True)
    s.text(mx, cal_y + 50, "1 kHz", 12, th.muted, mono=True)
    s.rect(mx - 13, cal_y + 74, 26, 10, th.fg, rx=2)                 # coupler cavity
    s.text(mx, cal_y - 14, "Sound calibrator", 13, th.fg, bold=True)
    # microphone below, capsule inserted in the coupler
    cap_y = cal_y + 84
    s.rect(mx - 4, cap_y, 8, 10, th.fg, rx=2)                        # capsule
    s.rect(mx - 6, cap_y + 10, 12, 66, th.primary, rx=4)             # body
    s.line(mx, cap_y + 76, mx, gy, th.fg, 2.0)                       # stand
    s.line(mx - 16, gy, mx + 16, gy, th.fg, 2.0)
    s.text(mx, gy + 26, "Class 1 calibrator (IEC 60942)", 12, th.muted)
    s.text(mx, gy + 42, "coupled to the microphone", 12, th.muted)

    # Signal chain boxes to the right, aligned with the mic body
    boxes = [
        (370, "Microphone +", "preamplifier"),
        (560, "Audio interface", "(ADC)"),
        (750, "calculate_", "sensitivity()"),
    ]
    by, bw, bh = 180.0, 150.0, 64.0
    prev_x = mx + 40
    s.line(mx + 6, by + bh / 2, mx + 40, by + bh / 2, th.fg, 1.6)
    for bx, l1, l2 in boxes:
        mono = l1.startswith("calculate")
        s.rect(bx - bw / 2, by, bw, bh, th.panel, th.primary, rx=10, sw=2)
        s.text(bx, by + 27, l1, 13, th.fg, bold=not mono, mono=mono)
        s.text(bx, by + 46, l2, 13, th.fg, bold=not mono, mono=mono)
        s.arrow(prev_x, by + bh / 2, bx - bw / 2 - 6, by + bh / 2, th.fg)
        prev_x = bx + bw / 2 + 6
    s.arrow(prev_x, by + bh / 2, 868, by + bh / 2, th.accent, 2)
    s.text(872, by + bh / 2 - 6, "Pa per", 12, th.accent, "start", mono=True)
    s.text(872, by + bh / 2 + 12, "digital", 12, th.accent, "start", mono=True)
    s.text(872, by + bh / 2 + 28, "unit", 12, th.accent, "start", mono=True)

    # Stability annotation box
    s.rect(300, 300, 520, 92, "none", th.secondary, rx=10, dash="5,4")
    s.text(560, 326, "Stability check (IEC 60942:2017, 5.3.3)", 13, th.secondary, bold=True)
    s.text(560, 348, "|max − mean| and |min − mean| of the F-weighted level", 12, th.fg)
    s.text(560, 366, "must stay ≤ 0.07 dB (class 1, 160 Hz – 1.25 kHz),", 12, th.fg)
    s.text(560, 384, "otherwise a CalibrationWarning is raised", 12, th.fg)


# ---------------------------------------------------------------------------
# d2 - Environmental noise microphone positions (ISO 1996-2)
# ---------------------------------------------------------------------------

def _d2(s: SVG, th: Theme) -> None:
    gy = 430.0
    s.ground(gy, 40, 940)

    # Building facade (right)
    fx = 760.0
    s.rect(fx, 120, 150, gy - 120, th.panel, th.fg, sw=2)
    for wy in range(160, int(gy) - 40, 70):
        s.rect(fx + 22, wy, 34, 40, th.bg, th.muted, rx=2, sw=1)
        s.rect(fx + 86, wy, 34, 40, th.bg, th.muted, rx=2, sw=1)
    s.text(fx + 75, 108, "Building façade", 13, th.fg, bold=True)

    # Source (left): road with car glyph
    s.rect(60, gy - 8, 150, 8, th.muted)
    s.path(f"M 90 {gy - 26} L 110 {gy - 44} L 150 {gy - 44} L 170 {gy - 26} Z",
           fill=th.secondary)
    s.rect(84, gy - 28, 96, 12, th.secondary, rx=4)
    s.circle(104, gy - 12, 8, th.fg)
    s.circle(160, gy - 12, 8, th.fg)
    s.text(132, gy + 26, "Noise source (road traffic)", 12, th.muted)
    # Sound propagation arcs
    for r in (40, 70, 100):
        s.path(f"M {170 + r * 0.5} {gy - 30 - r * 0.55} "
               f"A {r} {r} 0 0 1 {170 + r * 0.87} {gy - 30 + r * 0.1}",
               stroke=th.accent, sw=1.4)

    # Position A: free field mic, 4.0 m height (general mapping)
    ax = 420.0
    amy = gy - 190
    s.mic(ax, amy, 1.1, "A")
    s.dim(ax - 46, gy, ax - 46, amy - 30, "4.0 ± 0.2 m", offset=0)
    s.text(ax, amy - 60, "A — free field (mapping)", 13, th.fg, bold=True)
    s.text(ax, amy - 44, "correction: 0 dB", 12, th.accent, mono=True)

    # Position B: 2 m in front of facade
    bx = fx - 90.0
    bmy = gy - 190
    s.mic(bx, bmy, 1.1, "B")
    s.dim(bx, bmy + 30, fx, bmy + 30, "2 m", offset=0)
    s.text(bx - 30, bmy - 78, "B — 2 m in front of façade", 13, th.fg, bold=True)
    s.text(bx - 30, bmy - 60, "correction: −3 dB", 12, th.secondary, mono=True)

    # Position C: flush-mounted on the facade
    cy = gy - 160
    s.circle(fx + 3, cy, 6, th.fg)
    s.line(fx + 3, cy, fx - 34, cy + 34, th.muted, 1.1)
    s.text(fx - 38, cy + 44, "C — flush-mounted", 13, th.fg, "end", bold=True)
    s.text(fx - 38, cy + 62, "correction: −6 dB", 12, th.secondary, "end", mono=True)

    s.text(490, 492, "Free-field levels are the regulatory reference: measured levels at B and C "
                     "include the façade reflection and are corrected as shown (ISO 1996-2:2017, "
                     "clause 9 and Annex B).", 12, th.muted)


# ---------------------------------------------------------------------------
# d3 - Operator / bystander microphone positions (ECMA-74, clause 8.6)
# ---------------------------------------------------------------------------

def _d3(s: SVG, th: Theme) -> None:
    gy = 420.0
    s.ground(gy, 40, 940)

    # --- Left scene: seated operator with table-top equipment -------------
    tx = 110.0
    table_y = gy - 140.0
    # table
    s.line(tx + 16, gy, tx + 16, table_y, th.fg, 3)
    s.line(tx + 244, gy, tx + 244, table_y, th.fg, 3)
    s.line(tx, table_y, tx + 260, table_y, th.fg, 4)
    # equipment (reference box) on the table
    s.rect(tx + 20, table_y - 70, 110, 70, th.panel, th.primary, rx=6, sw=2)
    s.text(tx + 75, table_y - 30, "EUT", 13, th.primary, bold=True)
    s.text(tx + 75, table_y - 80, "reference box", 11, th.muted)
    eut_front = tx + 130.0

    # microphone: capsule at 1.20 m above the floor, 0.25 m from the box
    mx = eut_front + 62.0
    cap = gy - 235.0  # capsule height (1.20 m)
    s.rect(mx - 3, cap, 6, 8, th.fg, rx=2)
    s.rect(mx - 4, cap + 8, 8, 24, th.primary, rx=3)
    s.line(mx, cap + 32, mx, table_y, th.fg, 1.8)
    s.line(mx - 11, table_y, mx + 11, table_y, th.fg, 1.8)
    s.dim(eut_front, cap - 18, mx, cap - 18, "0.25 ± 0.03 m", offset=0)
    s.dim(mx + 52, gy, mx + 52, cap, "1.20 ± 0.03 m", offset=0)

    # seated operator on a chair, head near the microphone height
    px = mx + 130.0
    seat_y = gy - 105.0
    s.line(px - 26, seat_y, px + 30, seat_y, th.muted, 3)        # seat
    s.line(px - 22, seat_y, px - 22, gy, th.muted, 2.4)          # chair legs
    s.line(px + 26, seat_y, px + 26, gy, th.muted, 2.4)
    s.line(px + 30, seat_y, px + 30, seat_y - 78, th.muted, 2.4) # backrest
    s.circle(px, gy - 218, 13, th.muted)                          # head
    s.line(px, gy - 205, px + 6, seat_y, th.muted, 3.2)           # torso
    s.line(px + 6, seat_y, px - 34, seat_y - 2, th.muted, 2.6)    # thigh
    s.line(px - 34, seat_y - 2, px - 34, gy, th.muted, 2.6)       # shin
    s.line(px - 2, gy - 185, px - 40, gy - 160, th.muted, 2.4)    # arm
    s.text(px + 4, gy - 244, "operator", 11, th.muted)

    s.text(tx + 190, 70, "Operator's position — seated (P2)", 14, th.fg, bold=True)
    s.text(tx + 190, 90, "standing: height 1.50 ± 0.03 m (P1)", 12, th.muted)

    # --- Right scene: bystander positions, top view -----------------------
    cx, cyv = 760.0, 250.0
    s.text(cx, 70, "Bystander positions — top view", 14, th.fg, bold=True)
    s.text(cx, 90, "height 1.50 ± 0.03 m, ≥ 4 positions", 12, th.muted)
    s.rect(cx - 55, cyv - 40, 110, 80, th.panel, th.primary, rx=6, sw=2)
    s.text(cx, cyv + 5, "EUT", 13, th.primary, bold=True)
    for pxx, pyy, lab in [(cx, cyv - 110, "front"), (cx, cyv + 110, "rear"),
                          (cx - 160, cyv, "left"), (cx + 160, cyv, "right")]:
        s.circle(pxx, pyy, 7, th.secondary)
        s.circle(pxx, pyy, 2.4, th.bg)
        s.text(pxx, pyy + 24 if pyy >= cyv else pyy - 16, lab, 11, th.muted)
    s.dim(cx + 55, cyv + 62, cx + 160, cyv + 62, "1.00 ± 0.03 m", offset=0)

    s.text(490, 492, "ECMA-74 (22nd ed.), 8.6.2–8.6.3: hand-held equipment uses 1.0 m height and "
                     "0.125 m distance; boxes longer than 2 m add bystander positions at 1 m intervals.",
           12, th.muted)


# ---------------------------------------------------------------------------
# d4 - Library signal chain
# ---------------------------------------------------------------------------

def _d4(s: SVG, th: Theme) -> None:
    stages = [
        ("Signal", "x, fs", th.fg),
        ("Calibration", "sensitivity", th.primary),
        ("Freq. weighting", "A / C / G / Z", th.primary),
        ("Filter bank", "1/1, 1/3, 1/b", th.primary),
        ("Time weighting", "F / S / I", th.primary),
        ("Metrics", "Leq, LN, SEL…", th.accent),
    ]
    bw, bh, gap = 138.0, 78.0, 18.0
    total = len(stages) * bw + (len(stages) - 1) * gap
    x = (980 - total) / 2
    y = 160.0
    for i, (title, sub, color) in enumerate(stages):
        s.rect(x, y, bw, bh, th.panel, color, rx=10, sw=2)
        s.text(x + bw / 2, y + 32, title, 13, th.fg, bold=True)
        s.text(x + bw / 2, y + 54, sub, 11, color, mono=True)
        if i < len(stages) - 1:
            s.arrow(x + bw, y + bh / 2, x + bw + gap - 2, y + bh / 2, th.fg)
        x += bw + gap

    notes = [
        (170, "WAV / stream /", "NumPy array"),
        (330, "digital units → Pa", "(IEC 60942 check)"),
        (487, "IEC 61672-1", "class 1 verified"),
        (644, "IEC 61260-1", "class 1 verified"),
        (800, "IEC 61672-1", "ballistics"),
    ]
    for nx, l1, l2 in notes:
        s.text(nx, 278, l1, 11, th.muted)
        s.text(nx, 293, l2, 11, th.muted)

    s.text(490, 360, "Every stage is available standalone; conformance is enforced by the test "
                     "suite against the tolerance tables of each standard.", 12, th.muted)
    s.text(490, 382, "Block/streaming variants keep filter state across calls "
                     "(OctaveFilterBank, WeightingFilter(stateful=True)).", 12, th.muted)


DIAGRAMS = {
    "diagram_calibration_setup": (_d1, "Calibration chain — from calibrator to physical units"),
    "diagram_env_measurement": (_d2, "Environmental noise measurement positions (ISO 1996-2)"),
    "diagram_tonality_positions": (_d3, "Emission measurement positions (ECMA-74)"),
    "diagram_signal_chain": (_d4, "phonometry processing chain"),
}


def generate_all(output_dir: str = ".github/images") -> None:
    for name, (builder, title) in DIAGRAMS.items():
        _write(output_dir, name, builder, title)


if __name__ == "__main__":
    generate_all()
