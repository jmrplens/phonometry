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

# Spanish variants of every user-visible string. Strings not in the table
# (numbers, unit-only labels, code identifiers) are shared between languages.
_ES: dict[str, str] = {
    "Calibration chain — from calibrator to physical units":
        "Cadena de calibración — del calibrador a unidades físicas",
    "Sound calibrator": "Calibrador acústico",
    "Microphone +": "Micrófono +",
    "preamplifier": "preamplificador",
    "Audio interface": "Interfaz de audio",
    "Pa per": "Pa por",
    "digital unit": "unidad digital",
    "Stability: |max − mean| and |min − mean| ≤ 0.07 dB":
        "Estabilidad: |máx − media| y |mín − media| ≤ 0,07 dB",
    "(IEC 60942:2017 Table 2, class 1) — else CalibrationWarning":
        "(IEC 60942:2017 Tabla 2, clase 1) — si no, CalibrationWarning",
    "Environmental noise measurement positions (ISO 1996-2)":
        "Posiciones de medida de ruido ambiental (ISO 1996-2)",
    "Building façade": "Fachada del edificio",
    "A — free field": "A — campo libre",
    "B — 2 m from façade": "B — a 2 m de la fachada",
    "C — flush-mounted": "C — enrasado en fachada",
    "4.0 ± 0.2 m": "4,0 ± 0,2 m",
    "Emission measurement positions (ECMA-74)":
        "Posiciones de medida de emisión (ECMA-74)",
    "Operator — seated (P2)": "Operador — sentado (P2)",
    "Bystanders — top view": "Observadores — vista en planta",
    "height 1.50 m": "altura 1,50 m",
    "0.25 m": "0,25 m",
    "1.20 m": "1,20 m",
    "1.00 m": "1,00 m",
    "phonometry processing chain": "Cadena de procesado de phonometry",
    "Signal": "Señal",
    "Calibrate": "Calibrar",
    "Weighting": "Ponderación",
    "Octave": "Octavas",
    "bands 1/b": "bandas 1/b",
    "Ballistics": "Temporal",
    "Metrics": "Métricas",
    "Multirate decimation in the octave filter bank":
        "Decimación multitasa en el banco de filtros de octava",
    "16 kHz band": "Banda de 16 kHz",
    "1 kHz band": "Banda de 1 kHz",
    "63 Hz band": "Banda de 63 Hz",
    "no decimation": "sin decimación",
    "Anti-alias": "Antialias",
    "Low bands are filtered at a decimated rate: the relative":
        "Las bandas graves se filtran a frecuencia decimada: el ancho",
    "bandwidth stays wide, so the SOS stays numerically healthy.":
        "relativo se mantiene amplio y las SOS siguen bien condicionadas.",
    "Two-microphone (p-p) intensity probe":
        "Sonda de intensidad p-p (dos micrófonos)",
    "measurement axis / intensity direction":
        "eje de medida / dirección de la intensidad",
    "u from the p2−p1 gradient": "u a partir del gradiente p2−p1",
    "STI measurement chain (IEC 60268-16)":
        "Cadena de medida STI (IEC 60268-16)",
    "Source": "Fuente",
    "STIPA signal": "Señal STIPA",
    "Room": "Sala",
    "reverberation + noise": "reverberación + ruido",
    "Microphone": "Micrófono",
    "Analysis": "Análisis",
    "m(F) drops": "m(F) cae",
    "Airborne sound insulation setup (ISO 16283-1)":
        "Montaje de aislamiento acústico aéreo (ISO 16283-1)",
    "Source room": "Recinto emisor",
    "Receiving room": "Recinto receptor",
    "Test partition": "Partición de ensayo",
    "Loudspeaker": "Altavoz",
    "microphone positions": "posiciones de micrófono",
    "≥ 1.0 m": "≥ 1,0 m",
    "≥ 0.7 m": "≥ 0,7 m",
    "≥ 0.5 m": "≥ 0,5 m",
    "7.6 a) ≥ 0.7 m between microphone positions":
        "7.6 a) ≥ 0,7 m entre posiciones de micrófono",
    "7.6 b) ≥ 0.5 m to room boundaries":
        "7.6 b) ≥ 0,5 m a los límites del recinto",
    "7.6 c) ≥ 1.0 m to the loudspeaker":
        "7.6 c) ≥ 1,0 m al altavoz",
    "7.2.2 ≥ 1.0 m loudspeaker to separating partition":
        "7.2.2 ≥ 1,0 m del altavoz a la partición separadora",
    "Impulse-response measurement chain (ISO 18233)":
        "Cadena de medición de la respuesta al impulso (ISO 18233)",
    "Excitation": "Excitación",
    "ESS sweep / MLS": "Barrido ESS / MLS",
    "Deconvolution": "Deconvolución",
    "correlation /": "correlación /",
    "inverse filter": "filtro inverso",
    "acoustic path": "trayecto acústico",
    "The room response h(t) is recovered by deconvolving the microphone signal.":
        "La respuesta de la sala h(t) se recupera deconvolucionando "
        "la señal del micrófono.",
}


class SVG:
    """Tiny element accumulator with technical-drawing helpers."""

    def __init__(self, width: int, height: int, th: Theme, lang: str = "en") -> None:
        self.w, self.h, self.th = width, height, th
        self.lang = lang
        self.parts: list[str] = []

    def tr(self, s: str) -> str:
        """Translate a user-visible string for the current language."""
        return _ES.get(s, s) if self.lang == "es" else s

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

    def text(self, x: float, y: float, s: str, size: int = 20,
             fill: str = "", anchor: str = "middle", bold: bool = False,
             mono: bool = False, italic: bool = False) -> None:
        s = self.tr(s)
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
            offset: float = 0.0, size: int = 18, label_side: str = "left") -> None:
        """Dimension between two measured points, drafting style.

        The dimension line is placed ``offset`` px away (perpendicular);
        dashed witness lines connect it to the measured points. With
        ``offset=0`` the caller is responsible for any witness lines.
        """
        th = self.th
        horizontal = abs(y2 - y1) < abs(x2 - x1)
        if horizontal:
            y = y1 + offset
            if offset:
                self.line(x1, y1, x1, y, th.muted, 0.9, dash="3,3")
                self.line(x2, y2, x2, y, th.muted, 0.9, dash="3,3")
            mid = (x1 + x2) / 2
            self.arrow(mid - 4, y, x1, y, th.muted, 1.2)
            self.arrow(mid + 4, y, x2, y, th.muted, 1.2)
            self.text(mid, y - 7, label, size, th.fg, "middle")
        else:
            x = x1 + offset
            if offset:
                self.line(x1, y1, x, y1, th.muted, 0.9, dash="3,3")
                self.line(x2, y2, x, y2, th.muted, 0.9, dash="3,3")
            mid = (y1 + y2) / 2
            self.arrow(x, mid - 4, x, y1, th.muted, 1.2)
            self.arrow(x, mid + 4, x, y2, th.muted, 1.2)
            # Label beside the line, on whichever side is clear of the
            # measured object (masts, people, furniture).
            if label_side == "right":
                self.text(x + 9, mid + 6, label, size, th.fg, "start")
            else:
                self.text(x - 9, mid + 6, label, size, th.fg, "end")

    def mic(self, x: float, capsule_top: float, ground: float,
            scale: float = 1.0) -> None:
        """Measurement microphone on a stand that reaches the ground.

        ``capsule_top`` is the y of the capsule tip (the measurement point).
        """
        th, s = self.th, scale
        cap_h, body_h = 12 * s, 34 * s
        self.rect(x - 4 * s, capsule_top, 8 * s, cap_h, th.fg, rx=2.5 * s)
        self.rect(x - 6 * s, capsule_top + cap_h, 12 * s, body_h, th.primary, rx=4 * s)
        self.line(x, capsule_top + cap_h + body_h, x, ground, th.fg, 2.2)
        self.line(x - 16 * s, ground, x + 16 * s, ground, th.fg, 2.2)

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
                f'font-size="26" font-weight="600" fill="{th.fg}" '
                f'text-anchor="middle">{self.tr(title)}</text>')
        return head + "".join(self.parts) + "</svg>"


def _write(output_dir: str, name: str, build: "callable", title: str,  # type: ignore[valid-type]
           height: int = 560) -> None:
    for lang, lang_suffix in (("en", ""), ("es", "_es")):
        for th in (LIGHT, DARK):
            svg = SVG(900, height, th, lang)
            build(svg, th)
            path = os.path.join(output_dir, f"{name}{lang_suffix}{th.suffix}.svg")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(svg.render(title))
    print(f"Generated {name}.svg (+dark, +es, +es_dark)")


# ---------------------------------------------------------------------------
# d1 - Calibration chain (IEC 60942)
# ---------------------------------------------------------------------------

def _d1(s: SVG, th: Theme) -> None:
    gy = 470.0
    s.ground(gy, 40, 860)

    # Calibrator on top of the microphone (left column)
    mx = 150.0
    cal_y = 110.0
    s.text(mx, cal_y - 22, "Sound calibrator", 22, th.fg, bold=True)
    s.rect(mx - 62, cal_y, 124, 86, th.panel, th.fg, rx=10, sw=2)
    s.text(mx, cal_y + 38, "94.0 dB", 26, th.secondary, bold=True, mono=True)
    s.text(mx, cal_y + 66, "1 kHz", 20, th.muted, mono=True)
    s.rect(mx - 15, cal_y + 86, 30, 12, th.fg, rx=3)   # coupler cavity
    s.mic(mx, cal_y + 98, gy, 1.3)

    # Signal chain
    boxes = [(400, "Microphone +", "preamplifier"), (650, "Audio interface", "(ADC)")]
    by, bw, bh = 176.0, 210.0, 78.0
    prev_x = mx + 62
    for bx, l1, l2 in boxes:
        s.rect(bx - bw / 2, by, bw, bh, th.panel, th.primary, rx=12, sw=2)
        s.text(bx, by + 33, l1, 22, th.fg, bold=True)
        s.text(bx, by + 60, l2, 22, th.fg, bold=True)
        s.arrow(prev_x, by + bh / 2, bx - bw / 2 - 6, by + bh / 2, th.fg, 2)
        prev_x = bx + bw / 2 + 6
    s.arrow(prev_x, by + bh / 2, 862, by + bh / 2, th.accent, 2.4)
    s.text(796, by + bh / 2 + 34, "Pa per", 20, th.accent, mono=True)
    s.text(796, by + bh / 2 + 58, "digital unit", 20, th.accent, mono=True)

    # Stability annotation, clearly separated below the chain
    s.rect(250, 340, 560, 96, "none", th.secondary, rx=12, dash="6,5")
    s.text(530, 376, "Stability: |max − mean| and |min − mean| ≤ 0.07 dB", 22, th.secondary, bold=True)
    s.text(530, 408, "(IEC 60942:2017 Table 2, class 1) — else CalibrationWarning", 20, th.fg)


# ---------------------------------------------------------------------------
# d2 - Environmental noise microphone positions (ISO 1996-2)
# ---------------------------------------------------------------------------

def _d2(s: SVG, th: Theme) -> None:
    gy = 470.0
    s.ground(gy, 40, 860)

    # Building facade (right)
    fx = 700.0
    s.rect(fx, 120, 160, gy - 120, th.panel, th.fg, sw=2)
    for wy in range(158, int(gy) - 50, 78):
        s.rect(fx + 24, wy, 38, 46, th.bg, th.muted, rx=3, sw=1.2)
        s.rect(fx + 96, wy, 38, 46, th.bg, th.muted, rx=3, sw=1.2)
    s.text(fx + 80, 104, "Building façade", 22, th.fg, bold=True)

    # Source (left): car on a road
    s.rect(60, gy - 9, 140, 9, th.muted)
    s.path(f"M 88 {gy - 30} L 106 {gy - 48} L 146 {gy - 48} L 164 {gy - 30} Z", fill=th.secondary)
    s.rect(80, gy - 32, 96, 14, th.secondary, rx=5)
    s.circle(102, gy - 13, 9, th.fg)
    s.circle(156, gy - 13, 9, th.fg)
    for r in (44, 76, 108):
        s.path(f"M {168 + r * 0.5} {gy - 34 - r * 0.55} "
               f"A {r} {r} 0 0 1 {168 + r * 0.87} {gy - 34 + r * 0.1}",
               stroke=th.accent, sw=1.6)

    # Position A: free field, capsule 4 m above ground
    ax = 330.0
    a_cap = gy - 230.0
    s.mic(ax, a_cap, gy, 1.15)
    s.dim(ax, gy, ax, a_cap, "4.0 ± 0.2 m", offset=-60, size=20)
    s.text(ax - 20, a_cap - 58, "A — free field", 22, th.fg, bold=True)
    s.text(ax - 20, a_cap - 30, "0 dB", 22, th.accent, bold=True, mono=True)

    # Position B: 2 m in front of the facade, dimension at capsule height
    bx = fx - 108.0
    b_cap = gy - 230.0
    s.mic(bx, b_cap, gy, 1.15)
    s.dim(bx, b_cap + 6, fx, b_cap + 6, "2 m", offset=-14, size=20)
    s.text(bx - 30, b_cap - 58, "B — 2 m from façade", 22, th.fg, bold=True)
    s.text(bx - 30, b_cap - 30, "−3 dB", 22, th.secondary, bold=True, mono=True)

    # Position C: flush-mounted on the facade, below B's dimension zone
    cy = gy - 120.0
    s.circle(fx + 3, cy, 7, th.fg)
    # The leader crosses mic B's mast (plain line crossing, standard
    # drafting); the label itself sits in the clear zone between masts.
    s.line(fx - 2, cy + 5, 470, cy + 60, th.muted, 1.4)
    s.text(462, cy + 84, "C — flush-mounted", 22, th.fg, bold=True)
    s.text(462, cy + 110, "−6 dB", 22, th.secondary, bold=True, mono=True)


# ---------------------------------------------------------------------------
# d3 - Operator / bystander microphone positions (ECMA-74, clause 8.6)
# ---------------------------------------------------------------------------

def _d3(s: SVG, th: Theme) -> None:
    gy = 470.0
    s.ground(gy, 40, 860)

    # --- Left: seated operator at table-top equipment (side view) ---------
    s.text(240, 72, "Operator — seated (P2)", 24, th.fg, bold=True)
    tx = 80.0
    table_y = gy - 150.0
    s.line(tx + 18, gy, tx + 18, table_y, th.fg, 3)
    s.line(tx + 232, gy, tx + 232, table_y, th.fg, 3)
    s.line(tx, table_y, tx + 250, table_y, th.fg, 4)
    s.rect(tx + 16, table_y - 76, 118, 76, th.panel, th.primary, rx=8, sw=2)
    s.text(tx + 75, table_y - 32, "EUT", 22, th.primary, bold=True)
    eut_front = tx + 134.0

    # microphone: capsule tip at 1.20 m, 0.25 m from the EUT front face
    mx = eut_front + 76.0
    cap = gy - 268.0
    s.mic(mx, cap, table_y, 1.1)
    s.line(mx - 18, table_y, mx + 18, table_y, th.fg, 2.2)
    s.dim(eut_front, table_y - 76, mx, cap, "0.25 m", offset=-36, size=20)
    s.dim(mx + 210, gy, mx + 210, cap, "1.20 m", offset=0, size=20, label_side="right")
    s.line(mx + 10, cap, mx + 210, cap, th.muted, 0.9, dash="3,3")  # witness to capsule

    # seated operator on a chair, clear of both dimensions
    px = mx + 120.0
    seat_y = gy - 115.0
    s.line(px - 28, seat_y, px + 32, seat_y, th.muted, 3)
    s.line(px - 24, seat_y, px - 24, gy, th.muted, 2.6)
    s.line(px + 28, seat_y, px + 28, gy, th.muted, 2.6)
    s.line(px + 32, seat_y, px + 32, seat_y - 86, th.muted, 2.6)
    s.circle(px, gy - 240, 15, th.muted)
    s.line(px, gy - 225, px + 6, seat_y, th.muted, 3.4)
    s.line(px + 6, seat_y, px - 34, seat_y - 2, th.muted, 2.8)
    s.line(px - 34, seat_y - 2, px - 34, gy, th.muted, 2.8)
    s.line(px - 1, gy - 205, px - 38, gy - 178, th.muted, 2.6)

    # --- Right: bystander positions (top view), equal face distances ------
    cx, cyv = 700.0, 270.0
    s.text(cx, 72, "Bystanders — top view", 24, th.fg, bold=True)
    s.text(cx, 100, "height 1.50 m", 20, th.muted)
    s.rect(cx - 52, cyv - 40, 104, 80, th.panel, th.primary, rx=8, sw=2)
    s.text(cx, cyv + 8, "EUT", 22, th.primary, bold=True)
    g = 92.0  # face-to-microphone distance, equal on all four sides
    for pxx, pyy in [(cx, cyv - 40 - g), (cx, cyv + 40 + g),
                     (cx - 52 - g, cyv), (cx + 52 + g, cyv)]:
        s.circle(pxx, pyy, 8, th.secondary)
        s.circle(pxx, pyy, 2.8, th.bg)
    s.dim(cx + 52, cyv - 20, cx + 52 + g, cyv, "1.00 m", offset=-44, size=20)


# ---------------------------------------------------------------------------
# d4 - Library signal chain
# ---------------------------------------------------------------------------

def _d4(s: SVG, th: Theme) -> None:
    stages = [
        ("Signal", "x, fs", th.fg),
        ("Calibrate", "→ Pa", th.primary),
        ("Weighting", "A/C/G/Z", th.primary),
        ("Octave", "bands 1/b", th.primary),
        ("Ballistics", "F / S / I", th.primary),
        ("Metrics", "Leq, LN…", th.accent),
    ]
    bw, bh, gap = 136.0, 92.0, 12.0
    total = len(stages) * bw + (len(stages) - 1) * gap
    x = (900 - total) / 2
    y = 170.0
    for i, (title, sub, color) in enumerate(stages):
        s.rect(x, y, bw, bh, th.panel, color, rx=12, sw=2)
        s.text(x + bw / 2, y + 40, title, 22, th.fg, bold=True)
        s.text(x + bw / 2, y + 68, sub, 19, color, mono=True)
        if i < len(stages) - 1:
            s.arrow(x + bw + 1, y + bh / 2, x + bw + gap - 2, y + bh / 2, th.fg, 2)
        x += bw + gap




# ---------------------------------------------------------------------------
# d5 - Multirate decimation inside the filter bank
# ---------------------------------------------------------------------------

def _d5(s: SVG, th: Theme) -> None:
    # Input on the left
    s.rect(36, 150, 136, 70, th.panel, th.fg, rx=10, sw=2)
    s.text(104, 180, "Signal", 22, th.fg, bold=True)
    s.text(104, 205, "fs = 48 kHz", 18, th.muted, mono=True)

    rows = [
        (120.0, "16 kHz band", "fs", "no decimation", th.secondary),
        (230.0, "1 kHz band", "fs / 8", "6 kHz", th.primary),
        (340.0, "63 Hz band", "fs / 64", "750 Hz", th.accent),
    ]
    for y, band, rate, eff, color in rows:
        bx = 455.0
        if "no" not in eff:
            s.arrow(172, 185, 240, y + 35, th.fg, 1.6)
            s.rect(250, y, 150, 70, th.panel, th.muted, rx=10, sw=1.6)
            s.text(325, y + 30, "Anti-alias", 20, th.fg)
            s.text(325, y + 54, "LPF + \u2193M", 18, th.muted, mono=True)
            s.arrow(400, y + 35, 448, y + 35, th.fg, 1.6)
        else:
            s.arrow(172, 185, 448, y + 35, th.fg, 1.6)
        s.rect(bx, y, 190, 70, th.panel, color, rx=10, sw=2)
        s.text(bx + 95, y + 30, band, 20, th.fg, bold=True)
        s.text(bx + 95, y + 54, f"SOS @ {rate}", 18, color, mono=True)
        s.text(660, y + 40, eff, 18, th.muted, "start", mono=True)

    s.text(450, 480, "Low bands are filtered at a decimated rate: the relative", 20, th.fg)
    s.text(450, 508, "bandwidth stays wide, so the SOS stays numerically healthy.", 20, th.fg)


# ---------------------------------------------------------------------------
# d6 - Two-microphone (p-p) intensity probe (IEC 61043)
# ---------------------------------------------------------------------------

def _d6(s: SVG, th: Theme) -> None:
    ay = 232.0  # probe axis height

    # Measurement axis / intensity direction (drawn first, under the probe)
    s.line(70, ay, 820, ay, th.accent, 1.4, dash="10,4,2,4")
    s.arrow(820, ay, 852, ay, th.accent, 1.8)
    s.text(450, 305, "measurement axis / intensity direction", 18, th.accent)

    # Two opposed capsules facing each other with a spacer between the tips
    for side in (-1, 1):
        # bodies: 180..320 and 580..720; capsules: 320..400 / 500..580;
        # tips (grilles): 400..414 / 486..500; gap 414..486 = Δr
        bx = 180.0 if side < 0 else 580.0
        cx = 320.0 if side < 0 else 500.0
        tx = 400.0 if side < 0 else 486.0
        s.rect(bx, ay - 28, 140, 56, th.panel, th.primary, rx=10, sw=2)
        s.rect(cx, ay - 20, 80, 40, th.fg, rx=4)
        s.rect(tx, ay - 16, 14, 32, th.muted, rx=2)
    s.rect(414, ay - 6, 72, 12, th.panel, th.muted, rx=4, sw=1.2)  # spacer

    s.text(360, ay - 38, "p1", 20, th.fg, mono=True, bold=True)
    s.text(540, ay - 38, "p2", 20, th.fg, mono=True, bold=True)

    # Δr dimension between the capsule tips, drafting style
    s.dim(414, ay - 16, 486, ay - 16, "Δr = 12 mm", offset=-66, size=18)

    # p-p estimator notes near the capsules
    s.text(280, 365, "u from the p2−p1 gradient", 19, th.muted, mono=True)
    s.text(620, 365, "p = (p1+p2)/2", 19, th.muted, mono=True)


# ---------------------------------------------------------------------------
# d7 - STI measurement chain (IEC 60268-16)
# ---------------------------------------------------------------------------

def _d7(s: SVG, th: Theme) -> None:
    stages = [
        ("Source", "STIPA signal", th.fg),
        ("Room", "reverberation + noise", th.secondary),
        ("Microphone", "", th.primary),
        ("Analysis", "MTF → TI → STI", th.accent),
    ]
    bw, bh, gap = 192.0, 96.0, 20.0
    total = len(stages) * bw + (len(stages) - 1) * gap
    x = (900 - total) / 2
    y = 150.0
    for i, (title, sub, color) in enumerate(stages):
        s.rect(x, y, bw, bh, th.panel, color, rx=12, sw=2)
        if sub:
            s.text(x + bw / 2, y + 42, title, 22, th.fg, bold=True)
            if "→" in sub:
                s.text(x + bw / 2, y + 70, sub, 18, color, mono=True)
            else:
                s.text(x + bw / 2, y + 70, sub, 18, color)
        else:
            s.text(x + bw / 2, y + bh / 2 + 7, title, 22, th.fg, bold=True)
        if i == 1:  # the room degrades the modulation transfer function
            cx = x + bw / 2
            s.line(cx, y + bh, cx, y + bh + 18, th.muted, 1.2, dash="3,3")
            s.text(cx, y + bh + 40, "m(F) drops", 18, th.muted, italic=True)
        if i < len(stages) - 1:
            s.arrow(x + bw + 1, y + bh / 2, x + bw + gap - 2, y + bh / 2, th.fg, 2)
        x += bw + gap


# ---------------------------------------------------------------------------
# d8 - Airborne sound insulation setup (ISO 16283-1)
# ---------------------------------------------------------------------------

def _d8(s: SVG, th: Theme) -> None:
    top, bot = 90.0, 470.0

    # Two rooms in plan view separated by the test partition.
    s.rect(70, top, 375, bot - top, th.panel, th.fg, rx=6, sw=3)
    s.rect(465, top, 365, bot - top, th.panel, th.fg, rx=6, sw=3)
    s.rect(445, top, 20, bot - top, th.secondary, th.fg, sw=2)  # partition (S)
    s.text(455, 80, "Test partition", 20, th.secondary, bold=True)

    s.text(90, top + 32, "Source room", 22, th.fg, bold=True, anchor="start")
    s.text(90, top + 58, "L₁", 20, th.muted, anchor="start")
    s.text(486, top + 32, "Receiving room", 22, th.fg, bold=True, anchor="start")
    s.text(486, top + 58, "L₂ , T", 20, th.muted, anchor="start")

    # Loudspeaker in a corner of the source room (bottom-left).
    lsx, lsy = 150.0, 405.0
    for r in (40, 66, 92):
        s.path(f"M {lsx + r * 0.22:.1f} {lsy - r:.1f} "
               f"A {r} {r} 0 0 1 {lsx + r:.1f} {lsy - r * 0.22:.1f}",
               stroke=th.accent, sw=1.6)
    s.rect(lsx - 26, lsy - 30, 52, 60, th.panel, th.primary, rx=6, sw=2)
    s.circle(lsx, lsy - 10, 12, th.primary)
    s.circle(lsx, lsy - 10, 5, th.bg)
    s.circle(lsx, lsy + 16, 7, th.primary)
    s.text(lsx, lsy + 52, "Loudspeaker", 20, th.fg, bold=True)

    # Microphone positions (five per room, in the central zone).
    src_mics = [(150, 315), (255, 250), (360, 300), (300, 360), (390, 205)]
    rec_mics = [(590, 160), (653, 160), (560, 290), (690, 380), (785, 300)]
    for mics in (src_mics, rec_mics):
        for mx, my in mics:
            s.circle(mx, my, 8, th.fg)
            s.circle(mx, my, 3, th.bg)
    s.text(268, 172, "microphone positions", 18, th.muted)
    s.text(636, 430, "microphone positions", 18, th.muted)

    # Normative minimum separations (ISO 16283-1, 7.6 and 7.2.2).
    s.dim(150, 395, 150, 317, "≥ 1.0 m", offset=-42, size=20)          # 7.6c
    s.dim(178, 405, 443, 405, "≥ 1.0 m", offset=0, size=20)            # 7.2.2
    s.dim(590, 160, 653, 160, "≥ 0.7 m", offset=42, size=20)           # 7.6a
    s.dim(785, 300, 830, 300, "≥ 0.5 m", offset=-46, size=20)          # 7.6b

    # Clause legend.
    for y, txt in (
        (505, "7.6 a) ≥ 0.7 m between microphone positions"),
        (531, "7.6 b) ≥ 0.5 m to room boundaries"),
        (557, "7.6 c) ≥ 1.0 m to the loudspeaker"),
        (583, "7.2.2 ≥ 1.0 m loudspeaker to separating partition"),
    ):
        s.text(80, y, txt, 18, th.fg, anchor="start")


# ---------------------------------------------------------------------------
# d9 - ISO 18233 indirect impulse-response measurement chain
# ---------------------------------------------------------------------------

def _d9(s: SVG, th: Theme) -> None:
    bw, bh = 200.0, 96.0
    xs = (120.0, 350.0, 580.0)
    y1, y2 = 110.0, 300.0

    def box(x: float, y: float, title: str, subs: list[str], color: str,
            mono: bool) -> None:
        s.rect(x, y, bw, bh, th.panel, color, rx=12, sw=2)
        t_size = 20 if len(title) > 11 else 22
        if subs:
            s.text(x + bw / 2, y + 38, title, t_size, th.fg, bold=True)
            if len(subs) == 1:
                s.text(x + bw / 2, y + 66, subs[0], 18, color,
                       mono=mono, italic=mono)
            else:
                s.text(x + bw / 2, y + 62, subs[0], 18, color)
                s.text(x + bw / 2, y + 82, subs[1], 18, color)
        else:
            s.text(x + bw / 2, y + bh / 2 + 7, title, t_size, th.fg, bold=True)

    # Row 1 (left to right): the physical excitation path.
    box(xs[0], y1, "Excitation", ["ESS sweep / MLS"], th.primary, False)
    box(xs[1], y1, "Loudspeaker", [], th.fg, False)
    box(xs[2], y1, "Room", ["h(t)"], th.secondary, True)
    s.arrow(xs[0] + bw, y1 + bh / 2, xs[1] - 2, y1 + bh / 2, th.fg, 2)
    s.arrow(xs[1] + bw, y1 + bh / 2, xs[2] - 2, y1 + bh / 2, th.fg, 2)

    # Serpentine connector: the acoustic field couples Room -> Microphone.
    cx = xs[2] + bw / 2
    s.arrow(cx, y1 + bh, cx, y2 - 2, th.muted, 2)
    s.text(cx - 12, (y1 + bh + y2) / 2 + 5, "acoustic path", 18, th.muted,
           anchor="end", italic=True)

    # Row 2 (right to left): recover the impulse response by deconvolution.
    box(xs[2], y2, "Microphone", [], th.primary, False)
    box(xs[1], y2, "Deconvolution", ["correlation /", "inverse filter"],
        th.accent, False)
    box(xs[0], y2, "IR", ["ĥ(t)"], th.accent, True)
    s.arrow(xs[2], y2 + bh / 2, xs[1] + bw + 2, y2 + bh / 2, th.fg, 2)
    s.arrow(xs[1], y2 + bh / 2, xs[0] + bw + 2, y2 + bh / 2, th.fg, 2)

    s.text(450, 425,
           "The room response h(t) is recovered by deconvolving the "
           "microphone signal.", 18, th.fg)


DIAGRAMS = {
    "diagram_calibration_setup": (_d1, "Calibration chain — from calibrator to physical units", 560),
    "diagram_env_measurement": (_d2, "Environmental noise measurement positions (ISO 1996-2)", 560),
    "diagram_tonality_positions": (_d3, "Emission measurement positions (ECMA-74)", 560),
    "diagram_signal_chain": (_d4, "phonometry processing chain", 400),
    "diagram_multirate": (_d5, "Multirate decimation in the octave filter bank", 560),
    "diagram_pp_probe": (_d6, "Two-microphone (p-p) intensity probe", 460),
    "diagram_sti_chain": (_d7, "STI measurement chain (IEC 60268-16)", 400),
    "diagram_insulation_setup": (
        _d8, "Airborne sound insulation setup (ISO 16283-1)", 600),
    "diagram_ir_measurement": (
        _d9, "Impulse-response measurement chain (ISO 18233)", 440),
}


def generate_all(output_dir: str = ".github/images") -> None:
    os.makedirs(output_dir, exist_ok=True)
    for name, (builder, title, height) in DIAGRAMS.items():
        _write(output_dir, name, builder, title, height)


if __name__ == "__main__":
    generate_all()
