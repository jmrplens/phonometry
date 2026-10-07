#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The sheet the diagrams are drawn on: theme, canvas and the writing of files.

One subject because a builder never sees anything else. :class:`Theme`
fixes the palette, and the light and dark instances of it are the same
colours the matplotlib figures use, so the docs can theme-switch an SVG
exactly like a raster plot. :class:`SVG` is the element accumulator with
the technical-drawing helpers a setup diagram needs (dimension lines,
microphones on stands, people, hatched ground). :func:`_write` renders a
builder the four ways the documentation embeds it: English and Spanish,
each light and dark.

**The type scale is the face's.** Every ``size`` in a builder is px of
the face :mod:`diagrams.outline` sets, and that face changed: DejaVu
runs about 16 % wider than the Helvetica-metric face this corpus was
composed in, measured over all 6 552 labels of the corpus in both
languages. A px of the old face is therefore not a px of this one, and
the sizes were converted once, corpus-wide, at 0.86 with a floor of
10 px, which is the conversion the title had already taken on its own
when it went from 26 px to 22. Nothing else would do: a plate is a
hand-tuned composition where every label was measured into a box, a
column or a gap, and 16 % of extra advance on 6 552 labels is not a set
of local defects to patch but one metric to restore. Sizes stay
integers because the corpus's are, and the floor exists because 9 px of
caption is not a caption.

A size chosen for a new label is px of *this* face; do not convert it
again.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import generated_assets

from .i18n import lookup, visit
from .outline import (
    _COMBINING,
    GlyphStore,
    Run,
    assert_capabilities,
    emit_runs,
    measure,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence


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
    suffix="",
    bg="#ffffff",
    fg="#1a1a1a",
    muted="#666666",
    panel="#f0f2f5",
    primary="#1f77b4",
    secondary="#d62728",
    accent="#2ca02c",
)
DARK = Theme(
    suffix="_dark",
    bg="#0d1117",
    fg="#e6e6e6",
    muted="#9a9a9a",
    panel="#1c2128",
    primary="#4da3d8",
    secondary="#e46a6a",
    accent="#5abf5a",
)

#: The letter runs a sub/superscript sets upright: the descriptive
#: subscripts of the corpus, printed in roman by the standards that define
#: them -- weightings, averages and exposure (Aeq, eq, EQ, EX), extremes
#: and bounds (max, MAX, min, upper, lower, low, high, limit), qualifiers
#: (ref, rms, tot, TOT, eff, mod, norm, spec, inst, cal, tab, cum, ss,
#: shadow, co, tr, diff, ff, ax, SN, CS, MS), the reference sound source
#: and the source under test of the ISO 3740 series (RSS, ST, printed
#: upright in ISO 3747:2010, Equation (11)), the indicated value and the
#: input of ISO 8041-1, Formulae (9) and (12) (ind, in, both printed
#: upright there beside an italic f and w), the hand-arm/whole-body
#: vibration axes of ISO 5349 and ISO 2631 (hv, hwx, hwy, hwz, wx, wy, wz),
#: the seat and platform weighted accelerations of ISO 10326-1 (wS, wP),
#: the parts of a room and of a building element the building plates name
#: (obj and air of EN 12354-6 Formulae 2 to 4, the wall/win mnemonics of
#: its take-off inset, perp for the ⊥ of EN 12354-1 Annex E Formula E.3),
#: the mid-frequency average of ANSI/ASA S12.2 Annex D (MF), the
#: level-difference paths of E DIN 45672-3:2023-02, Formulae (1) and (2)
#: (BB, FB, DF, DB, spelled out under Formula (2) as Boden, Fundament and
#: Decke, and printed upright there beside an italic v), the KB
#: indications of DIN 45669-1:2010-09, 3.10.1.2 to 3.10.1.5 (Fmax, FTm,
#: where F abbreviates "Fast", the standard's own name for τ = 0,125 s, T
#: the clock duration and m the averaging duration, so all three letters
#: describe rather than stand for a quantity), the assessment vibration
#: severity of DIN 4150-2:1999-06, 6.4.1, Formulae (4a) and (4b) (FTr, whose
#: r is the "Beurteilung" of the assessment time T_r and is printed upright
#: there and in E DIN 4150-2:2023-08, Formula (6), as the F and the T
#: are), the test track and the train
#: of DIN 45672-1:2009-12, the note to 7.3.1 (MG for Messgleis, Z for Zug,
#: both printed upright there), the train category the railway clause of
#: E DIN 4150-2:2023-08, 6.5.3.2, groups the passages into (Zug, written
#: out and printed upright in KBFTm,Zug, KBFmax,Zug, nZug and αZug), the
#: saturation vapour pressure of IEC 61094-2 Annex F (sv), the Helmholtz
#: resonator and the slit of the slow-sound absorber in Z_HR and Δl_slit
#: (HR, slit: an abbreviation and a word, both set upright by the
#: metamaterial-absorbers guide), and the Spanish twin the i18n table sets
#: beside them (sup for upper).
#:
#: The single letters come from holding every diagram against the prose,
#: run by run, once the prose had settled which subscripts are descriptive:
#: the critical, sampling, resonance, lower and upper frequencies (c, s, r,
#: l, u), the Sabine and weighted absorption and the weighted ratings (s,
#: w), the source and receiver geometry (s, r, m, h), the impact and
#: coupling terms (C, D, E, F, G, K, L, P, R, T), the character penalties
#: of RD 1367/2007 (f, t), the gate and ground times (g), the situation of
#: ISO 12999-1 (situ), the energy sum of the impact levels that
#: ISO 717-2:2020, Formula (A.3), prints upright in $L_{n,sum}$ (sum), the
#: corner and low-frequency levels of ISO 16283
#: (Corner, LF, a word and an abbreviation all three parts print upright,
#: which also sets the early lateral energy fraction $J_{LF}$ of ISO 3382-1
#: upright, as its guide writes it), the airborne descriptors (AF, AFmax,
#: ASmax, AS, Cpeak, sa) and the upper guide value of DIN 4150-2:1999-06, 6.2
#: (o for "oberer", the adjective the clause spells out beside the letter,
#: as it does the "unterer" of the u already here, both printed upright
#: there in $A_u$ and $A_o$).
#:
#: The words and the abbreviations that no plate uses as an index came in
#: with the pass that held every plate against the page that embeds it: the
#: room, the cabin and the measurements with and without the enclosure of
#: ISO 11957 (room, cabin, with, without, which the guide writes in
#: ``\text``), the nominal reverberation time of the small-room method
#: (nom, ``T_\mathrm{nom}`` on its guide), the daily dose of ISO 2631-5
#: (zd, ``D_\mathrm{zd}``), the standardized impact level of ISO 16283-2
#: (nT, ``L'_\mathrm{nT}``) and the A-weighted Slow level beside the AF of
#: IEC 61672-1 (AS).
#:
#: The last words came in with the labels that the plates used to draw as
#: plain text because their subscript was missing here: the path lengths,
#: the meteorological correction and the barrier of ISO 9613-2 (sr beside
#: the ss already here, met, bar), the closest point of approach and the
#: data window of ISO 17208-1 (CPA, DW), the static stress and the age term
#: of ISO 2631-5, Annex C (stat, age), the median of ISO 7029 (md), the line
#: source of the CNOSSOS-EU road emission (line), the Hearing Model of
#: Sottek of ECMA-418-2 (HMS) and the threshold in quiet of ISO 532-1 (TQ).
#:
#: This set is keyed on the letter run alone and knows nothing of the
#: symbol it belongs to, so a run in it is upright everywhere or nowhere.
#: Ten runs the prose sets upright somewhere are therefore deliberately
#: absent, because the same run has to stay italic elsewhere: ``i`` and ``n``
#: (indices in $S_i$, $L_i$, $H_n$), ``d`` and ``r`` (the direct and
#: reflected path lengths $r_d$ and $r_r$ of the echo geometry, neither
#: expanded anywhere), ``p`` ($L_p$), ``v`` ($L_v$), ``S`` ($w_S$), ``a``
#: ($L_{a1}$, $L_{a2}$), ``I`` ($L_{I0}$, the residual intensity level)
#: and ``B``, which DIN 4150-1:2001-06, Formula (3), prints upright in
#: $f_B$, $k_B$ and $m_B$ for "Bauwerk", but which also names the second
#: of the two positions of ISO 10847, Formula (1) ($L_{ref,B}$, $L_{r,B}$),
#: where it pairs with an ``A`` this set cannot romanise, so romanising it
#: would set the two halves of one formula in two styles. Romanising those
#: here would romanise a quantity symbol or an index, which is the error the
#: whole policy exists to avoid, so they keep the italic default and the
#: label where one of them is descriptive says so itself (below).
#: Every other letter run inside a script is an index and is set in italic
#: ($K_{ij}$, $η_{ij}$); extend this set only for a subscript that
#: abbreviates a word, never for letter-indices.
#:
#: Those runs are set upright where they are descriptive by the call that
#: draws them, not here: :meth:`SVG.text` takes ``upright`` keys that name
#: the symbol and the run (``"S_p"``, ``"L′_n"``, ``"h_r"``), so the plant
#: area of ISO 8297 and the receiver height of ISO 9613-2 are upright on
#: their plates while $L_i$ stays an italic index on the next one. That is
#: what brings the plates under the file-level rule the prose follows,
#: where a symbol is set by what it means in the guide that carries it and
#: two files may legitimately disagree (CONTRIBUTING.md, "Setting a
#: subscript"): a plate is set as the page that embeds it is, and
#: ``scripts/check_subscript_slope.py`` reads the plates beside the page's
#: own mathematics to keep it so. The ``sloped`` keys are the other
#: direction, for the source that prints a letter of this set italic, as
#: ISO 3747 prints the f of $ΔL_f$.
_ROMAN_SCRIPTS = frozenset(
    (
        "Aeq",
        "eq",
        "EQ",
        "EX",
        "max",
        "MAX",
        "min",
        "upper",
        "lower",
        "sup",
        "low",
        "high",
        "limit",
        "ref",
        # rd/RI: the reference direction and the random incidence of
        # IEC 61183:1994, printed upright in L_rd, G_RI and G_RI,ref.
        "rd",
        "RI",
        # FF/RM: the free field and the reference microphone of IEC 62585:2012,
        # printed upright in C_FF,RM.
        "FF",
        "RM",
        # test/mon: the microphone under test of IEC 61094-5:2016 D.2, printed
        # upright in M_test, and the monitor microphone of IEC 61094-8:2012.
        "test",
        "mon",
        "rms",
        "tot",
        "TOT",
        "eff",
        "mod",
        "norm",
        "spec",
        "inst",
        "ind",
        "in",
        "out",
        "cal",
        "tab",
        "cum",
        "ss",
        "sv",
        "HR",
        "slit",
        "shadow",
        "co",
        "tr",
        "diff",
        "ff",
        "ax",
        "SN",
        "CS",
        "MS",
        "RSS",
        "ST",
        "hv",
        "hwx",
        "hwy",
        "hwz",
        "wx",
        "wy",
        "wz",
        # wS/wP: the seat and platform weighted accelerations of
        # ISO 10326-1, printed upright.
        "wS",
        "wP",
        "obj",
        "air",
        "wall",
        "win",
        "perp",
        "MF",
        "BB",
        "FB",
        "DF",
        "DB",
        "AF",
        "AFmax",
        "ASmax",
        "Cpeak",
        "sa",
        "situ",
        "sum",
        "Corner",
        "LF",
        # room/cabin/with/without: ISO 11957, written in \text on the guide.
        "room",
        "cabin",
        "with",
        "without",
        # nom: the nominal reverberation time of the small-room method.
        "nom",
        # zd: the daily dose of ISO 2631-5, D_zd.
        "zd",
        # nT: the standardized impact level of ISO 16283-2, L'_nT.
        "nT",
        # AS: A-weighted, time weighting S, beside the AF of IEC 61672-1.
        "AS",
        # sr/met/bar: the second edge to the receiver, the meteorological
        # correction and the barrier of ISO 9613-2:1996, 7.4, printed upright
        # in d_sr, K_met and A_bar (Equations (12), (14) and (16), p. 9).
        "sr",
        "met",
        "bar",
        # CPA/DW: the closest point of approach and the data window of
        # ISO 17208-1:2016, printed upright in d_CPA and l_DW (3.3, 3.6, p. 2).
        "CPA",
        "DW",
        # stat/age: the static stress and the age term of ISO 2631-5:2018,
        # printed upright in S_stat,i and S_age (Formulae (C.3), (C.4)).
        "stat",
        "age",
        # md: the median of ISO 7029:2017, printed upright in ΔH_md,Y (4.2).
        "md",
        # line: the line source of the CNOSSOS-EU road emission, upright in
        # L'_W,eq,line,i as the guide that carries the plate writes it.
        "line",
        # HMS: the Hearing Model of Sottek of ECMA-418-2, in Bark_HMS,
        # tu_HMS and vacil_HMS.
        "HMS",
        # TQ: the threshold in quiet of ISO 532-1:2017, printed upright in
        # L_TQ (A.2 and Table A.6).
        "TQ",
        # Ar: the A-weighted rating level L_Ar,T of NT ACOU 112:2002, clause
        # 8, Note 1, upright on its guide as the Aeq beside it is. Keq: the
        # corrected equivalent level L_Keq,T of RD 1367/2007, Annex I, upright
        # on its guide for the same reason (K for "corregido"). Both
        # documents set every subscript in one face, italic in the Nordtest
        # method and upright in the BOE, so the guides decide by meaning.
        "Ar",
        "Keq",
        "Fmax",
        "FTm",
        "FTr",
        "MG",
        "Z",
        "Zug",
        "C",
        "D",
        "E",
        "F",
        "G",
        "K",
        "L",
        "P",
        "R",
        "T",
        "c",
        "e",
        "f",
        "g",
        "h",
        "l",
        "m",
        "o",
        "s",
        "t",
        "u",
        "w",
    )
)

#: Subscripts that are part quantity symbol and part word, letter by letter:
#: ``"v"`` for the italic of a quantity, ``"u"`` for the upright of an
#: abbreviation. :data:`_ROMAN_SCRIPTS` cannot express these, because it sets a
#: whole run one way. The two members so far are the force exposure level of
#: JIS A 1418-2, ``L_FE = 10 lg[(1/T_ref) int F(t)^2/F_0^2 dt]``, whose F is the
#: force the formula integrates, so it is italic like every other quantity in
#: the corpus, while its E abbreviates "exposure" and is upright -- set roman
#: whole, as it was, the plate drew the same F upright that the figures and the
#: library both draw italic -- and the clock maxima of DIN 45669-1:2010-09,
#: Formula (2), ``KB_FTi``, whose F and T describe the Fast time constant and
#: the clock duration, as Fmax and FTm do above, while its i is the index that
#: counts the clock intervals and stays italic, the one letter the note on
#: :data:`_ROMAN_SCRIPTS` refuses to romanise anywhere. The prints set that i
#: upright inside the KB subscript too, as they set the whole subscript, but
#: set the same index italic under the sum it runs over, so the plates keep
#: it the index it is.
#:
#: The emission levels split the same way, and are the largest family here: the
#: first letter is the quantity the level is of, italic (``W`` sound power,
#: ``p`` sound pressure, ``v`` vibratory velocity), and the rest of the run
#: describes it and is upright (``A`` the frequency weighting, ``d`` for
#: "declared"). ISO 4871:1996 prints $L_{WA}$, $L_{WAd}$, $K_{WA}$, $L_{pA}$ and
#: $K_{pA}$ that way, ISO/TS 7849-1:2009 prints $L_{vA}$ that way, and the guides
#: that explain them write ``L_{W\mathrm{A}}`` throughout, so a whole-run slope
#: would leave the plates the only place in the corpus setting the A italic.
#:
#: The intensity levels of ISO 15186 follow the same rule: the normal
#: intensity level ``L_In`` of all three parts and the surface pressure level
#: ``L_pS`` of Part 3. I and p are the quantities and stay italic, while n
#: abbreviates "normal" and S "surface", and the three parts print both
#: upright. The guide already writes ``L_{I\mathrm{n}}`` and ``L_{p\mathrm{S}}``,
#: so the plate follows it. A bare ``I_n`` cannot be keyed here: its run is the
#: single letter n, the index the note on :data:`_ROMAN_SCRIPTS` keeps italic.
#:
#: The spectrum adaptation term of ISO 717-1:2020, Formulae (1) and (2), splits
#: the other way round: in ``X_Aj`` the A is the A-weighting and printed
#: upright, while the j counts the source spectra and stays italic.
#:
#: The same split covers the rest of the quantity-and-descriptor runs the
#: guides write that way: the G-weighted level ``L_{p\mathrm{G}}`` of
#: ISO 7196, the A-weighted Fast level ``L_{p\mathrm{AF}}`` of the Nordtest
#: method, the pressure-intensity indicator ``F_{pI_\mathrm{n}}`` of ISO 9614
#: (p and I the two quantities it compares, n the normal), the structure-borne power and blocked force of EN 15657
#: (``L_{W\mathrm{s}}``, ``L_{W\mathrm{sn}}``, ``L_{F\mathrm{b,eq}}``), the
#: levels of the equipment and the reference source of the small-room
#: comparison method (``L_{W\mathrm{e}}``, ``L_{W\mathrm{r}}``,
#: ``L_{p\mathrm{e}}``, ``L_{p\mathrm{r}}``), and two that split the other
#: way: the A-weighted sound exposure level of IEC 61672-1:2013, Equation
#: (4), ``L_{AE}``, whose E is the sound exposure, a quantity, printed
#: italic there beside an upright A, and the effective A-weighted level of
#: ISO 4869-2:2018, Formula (23), ``L'_{p,Ax}``, whose x counts the
#: protection levels and is printed italic beside the same upright A.
#:
#: So does the end correction of a slit mouth, ``Δl`` (Jiménez et al. 2017,
#: Sci. Rep. 7:5389, Eq. (5)), in ``M_Δl`` and ``Z_Δl``: the Δ is an operator and
#: upright at every level, the ``l`` is the length it qualifies and italic, and
#: :data:`_ROMAN_SCRIPTS` holds a bare ``l`` for the upright abbreviations, so
#: without the entry the plate draws a bare vertical stroke no reader can tell
#: from a capital I. A key that opens with a capital Greek letter is read whole
#: in :func:`_math_tokens`, where the letter scan would otherwise stop at the
#: change of script.
_MIXED_SCRIPTS: dict[str, str] = {
    "AE": "uv",
    "Aj": "uv",
    "Ax": "uv",
    "FE": "vu",
    "FTi": "uuv",
    "Fb": "vu",
    "In": "vu",
    "WA": "vu",
    "WAd": "vuu",
    "We": "vu",
    "Wr": "vu",
    "Ws": "vu",
    "Wsn": "vuu",
    "pA": "vu",
    "pAF": "vuu",
    "pG": "vu",
    "pIn": "vvu",
    "pS": "vu",
    "pe": "vu",
    "pr": "vu",
    "vA": "vu",
    "Δl": "uv",
}

#: Whole subscripts that run through a digit and are printed upright from end
#: to end. The letter scan of :func:`_math_tokens` stops at a digit, so in
#: ``ind3a`` it would read ``ind`` against :data:`_ROMAN_SCRIPTS` and leave the
#: trailing ``a`` alone, a single letter it sets italic as an index. IEC
#: 62585:2012 prints the readings of the comparison coupler, ``L_ind3a`` and
#: ``L_ind3b``, upright throughout (Figure E.1, Table I.1), and so do the
#: guide and the budget plot.
_ROMAN_SCRIPT_RUNS = frozenset({"ind3a", "ind3b"})

#: The primes a symbol may carry before its subscript (``L′_n``, ``R″``):
#: part of the symbol the script hangs from, as its combining marks are.
_PRIMES = "′″‴"

#: Script metrics of the ``$...$`` composer, as fractions of the font size:
#: how far a subscript drops, how far a superscript rises, and the glyph
#: scale of both.
_SUB_DROP = 0.22
_SUP_RISE = -0.38
_SCRIPT_SCALE = 0.70

#: How many script levels the composer sets: a script, and a script of that
#: script (the subscripted level inside an exponent). Each level drops or
#: rises by the fractions above of its parent's size and is set at
#: :data:`_SCRIPT_SCALE` of it.
_SCRIPT_DEPTH = 2

#: Font sizes :meth:`SVG.render` will set the title across the top at,
#: largest first, the first that leaves :data:`_TITLE_MARGIN` of white at
#: each sheet edge winning. 22 px is the corpus title size, the other two
#: are its steps down.
#:
#: The title is the one label of a plate whose width nobody chose. Every
#: other label is written into a box, a column or a gap the builder knows
#: the size of; the title is a sentence centred on the sheet, and the
#: sheet edge is the only thing holding it. Half the corpus is written
#: right up to that edge, so a single fixed size makes the whole set
#: hostage to the longest sentence the two languages produce -- and it is
#: the Spanish twin that is longest almost every time.
#:
#: Stepping down is what the plates already do wherever a label has to
#: clear something it did not choose -- a stage-box title measures itself
#: against its box and drops a step -- and this is that decision taken
#: against the sheet. Two steps are enough: 245 titles keep the top size,
#: 39 take one step and 12 take two, and none in either language reaches
#: the floor, so a title that does is a composition to rewrite and the
#: fit gate in :meth:`_emit_text` is what catches one.
#:
#: The ``$...$`` composer scales scripts against the size the element is
#: given, so a stepped-down title carries its subscripts down with it.
_TITLE_SIZES = (22, 21, 20)

#: White the title has to keep at each sheet edge, in px.
#:
#: The measure is a margin and not "does it overflow" because the failure
#: this catches is not an overflowing title, which the fit gate would
#: refuse anyway: it is a title whose first and last letters sit on the
#: sheet border while the drawing under it keeps 50 px on a median plate,
#: so the title alone reads as having run off the page. 30 px is well
#: inside that and still leaves the longest sentence of the corpus a size
#: it can be set at.
_TITLE_MARGIN = 30


def signed(value: float, spec: str = "") -> str:
    """*value* formatted with *spec*, its sign written as the minus sign U+2212.

    A plate sets exactly the characters it is given, and ``format`` signs a
    negative number with the hyphen-minus: a shorter, lower glyph than the
    "−" every other label of the corpus carries, the plates' hand-typed ones
    included. A number a plate formats goes through here. Only the leading
    sign is rewritten, because the hyphen of an exponent belongs to the
    number, which is the rule the figures' ``_fmt_minus`` follows too.
    """
    text = format(value, spec)
    return "\u2212" + text[1:] if text.startswith("-") else text


def _esc(s: str) -> str:
    """Escape XML metacharacters so labels may contain <, > and & literally.

    Serves the root ``<title>`` and the source-string comments beside each
    outlined label; the librsvg space-collapse workaround it once covered
    is now handled by the explicit collapse in :func:`_label_runs`.
    """
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _comment(s: str) -> str:
    """An XML comment carrying a label's source string.

    Keeps the outlined artwork greppable and keeps every label in the
    structural half of ``check_figures``, so a changed word still fails
    with a readable diff. ``--`` is illegal inside a comment and is
    sanitised to a U+2010 pair; no label contains one today.
    """
    return f"<!-- {_esc(s).replace('--', '‐‐')} -->"


def _script_base(run: str, end: int) -> str:
    """The symbol a script at *end* of a math run hangs from, as it is written.

    The letters before the ``_`` together with their combining marks and
    primes, so ``L′_{n,w}`` hangs from ``L′``, ``ΔL_a`` from ``ΔL`` and
    ``KB_{FTr}`` from ``KB``: the symbol a reader names, which is what the
    ``upright`` keys of :meth:`SVG.text` are spelled against.
    """
    k = end
    while k > 0 and (
        run[k - 1].isalpha() or run[k - 1] in _COMBINING or run[k - 1] in _PRIMES
    ):
        k -= 1
    return run[k:end]


def _script_table(keys: Iterable[str], kind: str) -> dict[str, frozenset[str]]:
    """Parse the ``upright`` or ``sloped`` keys of one call into ``{base: runs}``.

    A key is ``"<base>_<letter run>"`` (``"S_p"``, ``"L′_n"``, ``"ΔL_f"``):
    the symbol as the label writes it and the run of Latin letters in its
    subscript. Anything else raises, because a key that cannot match is a
    typo that would publish the slope it was written to change.
    """
    table: dict[str, set[str]] = {}
    for key in keys:
        base, sep, letters = key.partition("_")
        if not (sep and base and letters.isascii() and letters.isalpha()):
            msg = (
                f"{kind} key {key!r} is not '<base>_<letters>': name the "
                "symbol as the label writes it and the letter run of its "
                "subscript, as 'S_p' or 'L′_n'"
            )
            raise ValueError(msg)
        table.setdefault(base, set()).add(letters)
    return {base: frozenset(runs) for base, runs in table.items()}


def _close_brace(run: str, opening: int) -> int:
    """The index of the ``}`` that closes the ``{`` at *opening*, or -1.

    Counted, not searched: ``10^{L_{i}/10}`` closes its exponent at the last
    brace, where the first ``}`` after the opening one is the subscript's.
    """
    depth = 0
    for index in range(opening, len(run)):
        if run[index] == "{":
            depth += 1
        elif run[index] == "}":
            depth -= 1
            if depth == 0:
                return index
    return -1


def _math_tokens(
    run: str,
    s: str,
    *,
    depth: int = 0,
    superscript: bool = False,
    upright: frozenset[str] = frozenset(),
    sloped: frozenset[str] = frozenset(),
    matched: set[str] | None = None,
) -> list[tuple[str, str, str]]:
    r"""Split one math run into ``(kind, text)`` chunks.

    ``var`` is set in italic: at the baseline a single letter -- Latin or
    lowercase Greek, with any combining marks -- and at script level
    (*depth* 1 or 2, tokenizing the payload of a ``_``/``^``) also letter
    runs, which there are indices (``$K_{ij}$``), unless the run is one of
    the descriptive subscripts of :data:`_ROMAN_SCRIPTS` (``$L_{Aeq}$``).
    Those descriptive runs are subscripts by nature, so the curated sets are
    read in a subscript only: in a superscript (*superscript* true) a letter
    is an exponent's variable, the order ``m`` of ``2^m − 1`` or the level
    ``L`` of ``10^{L/10}``, and keeps the italic default.
    ``up`` stays upright: digits, operators, primes, brackets, capital
    Greek letters at every level (``Δ``, ``Φ``: operators and descriptors
    per the roman Δ of ISO 80000-2, the ``Δ_SOR`` print of ECAC Doc 29 and
    the upright ``\Delta`` mathtext sets in the matplotlib figures), and
    at the baseline runs of two or more Latin letters, which are operator
    names and acronyms (log, grad, CN), never products; a product of two
    symbols is written with an explicit space or middle dot between them. A
    whole script of :data:`_ROMAN_SCRIPT_RUNS` (``ind3a``) is one upright
    run, though it runs through a digit. ``sub`` and ``sup``
    carry the payload of ``_``/``^``, braced or single character, to be
    tokenized again at script size, and the third element of their token is
    the symbol the script hangs from (:func:`_script_base`); the other
    tokens carry an empty one. *upright* is the set of letter runs one call
    asks for upright in this script, beside those of :data:`_ROMAN_SCRIPTS`,
    and *sloped* the set it asks for italic although :data:`_ROMAN_SCRIPTS`
    holds them; each run either sets is added to *matched*. A run of
    :data:`_MIXED_SCRIPTS` keeps its letter-by-letter styles and is never
    matched.

    Malformed markup raises :class:`ValueError` naming the whole string *s*
    and the offending piece, so a typo breaks the generation instead of
    publishing a silently mis-set diagram: a multi-character script written
    without braces (``f_max`` sets only the f-m pair and pushes "ax" back to
    the baseline), a comma glued to an unbraced script (``L_p,s`` would push
    ",s" back to the baseline; spaced-off commas as in ``a_x , a_y`` stay
    legal), a script marker with an empty payload (``L_``, ``L_{}``), an
    unclosed script brace, and a third script level (``a^{b_{c_d}}``), which
    the composer cannot set. Two levels it does set: the subscripted level
    inside an exponent, ``10^{L_i/10}``, is how the energy sums of the
    standards are printed.
    """
    script = depth > 0
    words = script and not superscript
    if words and run in _ROMAN_SCRIPT_RUNS:
        return [("up", run, "")]
    out: list[tuple[str, str, str]] = []
    i = 0
    while i < len(run):
        ch = run[i]
        if ch in "_^":
            if depth >= _SCRIPT_DEPTH:
                msg = (
                    f"nested script {run[i:]!r} inside a script of a script "
                    f"of {s!r}: the composer sets {_SCRIPT_DEPTH} script levels"
                )
                raise ValueError(msg)
            kind = "sub" if ch == "_" else "sup"
            base = _script_base(run, i)
            if i + 1 == len(run):
                msg = f"empty script {ch!r} at the end of a math run in {s!r}"
                raise ValueError(msg)
            if run[i + 1] == "{":
                end = _close_brace(run, i + 1)
                if end < 0:
                    msg = f"unclosed script brace {run[i:]!r} in {s!r}"
                    raise ValueError(msg)
                if end == i + 2:
                    msg = f"empty script {run[i : end + 1]!r} in {s!r}"
                    raise ValueError(msg)
                out.append((kind, run[i + 2 : end], base))
                i = end + 1
            else:
                nxt = run[i + 2 : i + 3]
                if nxt == "(":
                    msg = (
                        f"ambiguous script {run[i : i + 2]!r} before '(' in "
                        f"{s!r}: brace the script and keep the argument "
                        f"outside, as {ch}{{{run[i + 1]}}}(...)"
                    )
                    raise ValueError(msg)
                if nxt.isalnum():
                    j = i + 2
                    while j < len(run) and run[j].isalnum():
                        j += 1
                    msg = (
                        f"ambiguous script {run[i:j]!r} in {s!r}: only "
                        f"{run[i + 1]!r} would attach to {ch!r}, brace the "
                        f"whole script as {ch}{{...}}"
                    )
                    raise ValueError(msg)
                if nxt == "," and i + 3 < len(run) and run[i + 3].isalnum():
                    j = i + 3
                    while j < len(run) and (run[j].isalnum() or run[j] == ","):
                        j += 1
                    msg = (
                        f"ambiguous comma {run[i:j]!r} in {s!r}: glued to "
                        f"the script it reads as part of the subscript, "
                        f"write {ch}{{{run[i + 1]},...}} or space the "
                        "comma off"
                    )
                    raise ValueError(msg)
                out.append((kind, run[i + 1 : i + 2], base))
                i += 2
        elif ch.isalpha():
            latin = ch.isascii()
            j = i + 1
            while j < len(run) and (
                run[j] in _COMBINING
                or (latin and run[j].isascii() and run[j].isalpha())
            ):
                j += 1
            mixed = _MIXED_SCRIPTS.get(run[i:j]) if words else None
            if mixed is None and words and not latin and ch.isupper():
                # A script that opens with a capital Greek letter and runs
                # on in Latin is one name, though the scan above stops at
                # the change of script: read it whole before the
                # capital-Greek rule below sets the Greek on its own and
                # leaves the Latin to _ROMAN_SCRIPTS.
                k = j
                while k < len(run) and run[k].isascii() and run[k].isalpha():
                    k += 1
                mixed = _MIXED_SCRIPTS.get(run[i:k])
                if mixed is not None:
                    j = k
            if mixed is not None:
                # A subscript that is part quantity and part word: emit one
                # token per letter so each takes its own type style. The
                # loop's own bookkeeping continues from j, so the run is
                # consumed exactly once either way.
                for letter, letter_kind in zip(run[i:j], mixed, strict=True):
                    out.append(("up" if letter_kind == "u" else "var", letter, ""))
                i = j
                continue
            if not latin and ch.isupper():
                # Capital Greek is upright at every level: in this corpus
                # it is an operator or a descriptor, never an index.
                kind = "up"
            elif script:
                name = run[i:j]
                if matched is not None and (name in upright or name in sloped):
                    matched.add(name)
                roman = (words and name in _ROMAN_SCRIPTS) or name in upright
                kind = "up" if roman and name not in sloped else "var"
            else:
                letters = sum(1 for c in run[i:j] if c not in _COMBINING)
                kind = "var" if letters == 1 else "up"
            out.append((kind, run[i:j], ""))
            i = j
        else:
            j = i
            while j < len(run) and run[j] not in "_^" and not run[j].isalpha():
                j += 1
            out.append(("up", run[i:j], ""))
            i = j
    return out


def _math_runs(
    s: str,
    upright: Iterable[str] = (),
    sloped: Iterable[str] = (),
    hits: set[str] | None = None,
) -> list[tuple[str, bool, float, float]]:
    r"""Chunk a translated ``$...$`` string into styled runs.

    Each run is ``(text, italic, shift, scale)``: the glyphs, whether they
    are italicised, how far the baseline drops (positive) or rises
    (negative) as a fraction of the font size, and the glyph scale
    (:data:`_SCRIPT_SCALE` inside a script). Adjacent chunks of identical
    style merge into one run -- that merge is a shaping-boundary decision,
    not an optimisation: ``CN = `` kerns and shapes as a single run only
    if it stays whole. Prose outside the ``$...$`` spans stays upright at
    the baseline; inside them variables are italicised and ``_``/``^``
    scripts are dropped or raised at reduced size. Radicals keep the house
    spelling ``√(...)``; there are no commands, every glyph is literal,
    and a backslash in a math run is an error -- the LaTeX commands of
    the matplotlib figures do not exist here.

    Script policy: inside a ``_``/``^`` script, letters are indices and are
    set in italic (``$K_{ij}$``, ``$η_{ij}$``), except the descriptive
    subscripts curated in :data:`_ROMAN_SCRIPTS`, which are abbreviations
    of words and stay upright as the standards print them (``$L_{Aeq}$``,
    ``$f_{max}$``); an exponent's letters are variables and keep the italic.
    A script may carry one script of its own, placed and scaled against it,
    which is how ``$10^{L_i/10}$`` sets the level inside an energy sum. At the baseline the opposite rule holds: a run of two
    or more Latin letters is an operator name or an acronym (log, grad,
    CN, TL) and stays upright, single letters are italic variables. Greek
    letters split by case at every level: lowercase are italic variables
    (``$θ$``, ``$η_{ij}$``) and capitals are upright (``$ΔL_s$``,
    ``$Δ_{SOR}$``, ``$Φ$``) -- in this corpus a capital Greek letter is an
    operator or a descriptor, matching the roman Δ of difference of ISO
    80000-2, the ``Δ_SOR`` print of ECAC Doc 29 §4.5.7 and the upright
    ``\Delta`` matplotlib's mathtext sets in the figures. The
    grid steps ``dx``/``dt`` follow that baseline rule inside a formula
    (upright, per the roman d of ISO 80000-2); in plain prose ("dt from
    the Courant number") they are not mathematics and take no ``$...$``.

    *upright* adds, for this string alone, the subscripts that the curated
    set cannot hold because the same letters are an index or a quantity
    somewhere else, and *sloped* takes out of it the runs a source prints
    italic though the same letters abbreviate a word elsewhere
    (:meth:`SVG.text` explains the keys). Each key that sets a run is added
    to *hits*, so the canvas can refuse a key that matched nothing.
    """
    segments = s.split("$")
    if len(segments) % 2 == 0:
        msg = f"unbalanced $ markup in {s!r}"
        raise ValueError(msg)
    table = _script_table(upright, "upright")
    table_sloped = _script_table(sloped, "sloped")
    chunks: list[tuple[str, bool, float, float]] = []

    def add(
        text: str, *, italic: bool = False, shift: float = 0.0, scale: float = 1.0
    ) -> None:
        if not text:
            return
        if chunks and chunks[-1][1:] == (italic, shift, scale):
            chunks[-1] = (chunks[-1][0] + text, italic, shift, scale)
        else:
            chunks.append((text, italic, shift, scale))

    def script(
        kind: str, payload: str, base: str, shift: float, scale: float, depth: int
    ) -> None:
        # A script drops or rises by a fraction of the size of what it hangs
        # from and is set at a fraction of that size, so a script of a script
        # is placed against its parent script, not against the baseline.
        shift += scale * (_SUB_DROP if kind == "sub" else _SUP_RISE)
        scale *= _SCRIPT_SCALE
        empty: frozenset[str] = frozenset()
        wanted = table.get(base, empty) if kind == "sub" else empty
        unwanted = table_sloped.get(base, empty) if kind == "sub" else empty
        matched: set[str] = set()
        for kind2, payload2, base2 in _math_tokens(
            payload,
            s,
            depth=depth,
            superscript=kind == "sup",
            upright=wanted,
            sloped=unwanted,
            matched=matched,
        ):
            if kind2 in ("sub", "sup"):
                script(kind2, payload2, base2, shift, scale, depth + 1)
            else:
                add(payload2, italic=kind2 == "var", shift=shift, scale=scale)
        if hits is not None:
            hits.update(f"{base}_{letters}" for letters in matched)

    for k, segment in enumerate(segments):
        if k % 2 == 0:
            add(segment)
            continue
        if "\\" in segment:
            msg = (
                f"backslash in math run {segment!r} of {s!r}: there are no "
                "commands here, write the glyph itself (θ, √, ·, …)"
            )
            raise ValueError(msg)
        for kind, payload, base in _math_tokens(segment, s):
            if kind in ("var", "up"):
                add(payload, italic=kind == "var")
            else:
                script(kind, payload, base, 0.0, 1.0, 1)
    return chunks


#: The XML whitespace collapse the viewers applied to the live-text
#: plates, reproduced explicitly now that the glyphs are baked. ASCII
#: only, never ``str.split()``, which would also eat the NBSPs the
#: labels use to keep quantities on their units.
_WS_RUN = re.compile(r"[ \t\r\n]+")


def _label_runs(
    s: str,
    *,
    mono: bool = False,
    bold: bool = False,
    italic: bool = False,
    upright: Iterable[str] = (),
    sloped: Iterable[str] = (),
    hits: set[str] | None = None,
) -> list[Run]:
    """Compose a translated label into the styled runs the engine sets.

    A ``$...$`` label takes the composer's runs, with the call's ``bold``
    styling the italic variable runs into BoldItalic and its ``upright`` and
    ``sloped`` keys setting the named subscripts upright or italic (keys that
    set one are added to *hits*); ``mono`` and
    whole-string ``italic`` cannot coexist with markup and are refused
    (silently dropping either published a mis-set label). A plain label
    is one run of the requested face, after the ASCII whitespace collapse
    the viewer applied to the live-text plates; a label that collapses to
    nothing composes to no runs at all.
    """
    if "$" in s:
        if mono:
            msg = (
                f"mono cannot carry composed mathematics: {s!r} would "
                "drop its $...$ styling; write the label without mono "
                "or without markup"
            )
            raise ValueError(msg)
        if italic:
            msg = (
                f"whole-string italic cannot carry composed mathematics: "
                f"{s!r} styles its own italics run by run; drop the italic "
                "or the markup"
            )
            raise ValueError(msg)
        return [
            Run(text, (False, bold, run_italic), shift, scale)
            for text, run_italic, shift, scale in _math_runs(s, upright, sloped, hits)
        ]
    s = _WS_RUN.sub(" ", s).strip(" ")
    if not s:
        return []
    return [Run(s, (mono, bold, italic), 0.0, 1.0)]


class SVG:
    """Tiny element accumulator with technical-drawing helpers."""

    def __init__(self, width: int, height: int, th: Theme, lang: str = "en") -> None:
        self.w, self.h, self.th = width, height, th
        self.lang = lang
        self.parts: list[str] = []
        self._glyphs = GlyphStore()
        # The ``upright`` and ``sloped`` keys the builder asked for and those
        # a label used, held against each other when the plate is rendered.
        self._upright_asked: set[str] = set()
        self._upright_hit: set[str] = set()

    def tr(self, s: str) -> str:
        """Translate a user-visible string for the current language."""
        return lookup(s, translate=self.lang == "es")

    # -- primitives -------------------------------------------------------
    def add(self, fragment: str) -> None:
        self.parts.append(fragment)

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: str,
        stroke: str = "none",
        rx: float = 0.0,
        sw: float = 1.5,
        dash: str = "",
    ) -> None:
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>'
        )

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        stroke: str,
        sw: float = 1.5,
        dash: str = "",
    ) -> None:
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{stroke}" stroke-width="{sw}"{d} stroke-linecap="round"/>'
        )

    def circle(
        self,
        cx: float,
        cy: float,
        r: float,
        fill: str,
        stroke: str = "none",
        sw: float = 1.5,
    ) -> None:
        self.add(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"/>'
        )

    def ellipse(
        self,
        cx: float,
        cy: float,
        rx: float,
        ry: float,
        fill: str = "none",
        stroke: str = "none",
        sw: float = 1.5,
        dash: str = "",
    ) -> None:
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>'
        )

    def text_width(
        self,
        s: str,
        size: float,
        *,
        bold: bool = False,
        mono: bool = False,
        italic: bool = False,
        upright: Iterable[str] = (),
        sloped: Iterable[str] = (),
    ) -> float:
        """Pen advance the label ``s`` will occupy, in the sheet's language.

        The same translate-compose-measure the emission runs, stopping one
        step short of drawing, so a caller that has to fit a label into a
        box decides on what the reader will actually see rather than on the
        length of the English string. A label that composes to nothing
        occupies nothing. ``upright`` and ``sloped`` are the key sets of
        :meth:`text`.
        """
        runs = self._runs(
            self.tr(s),
            mono=mono,
            bold=bold,
            italic=italic,
            upright=upright,
            sloped=sloped,
        )
        return measure(runs, size) if runs else 0.0

    def _runs(
        self,
        s: str,
        *,
        mono: bool,
        bold: bool,
        italic: bool,
        upright: Iterable[str],
        sloped: Iterable[str] = (),
    ) -> list[Run]:
        """:func:`_label_runs`, keeping the account of the slope keys."""
        up, down = tuple(upright), tuple(sloped)
        self._upright_asked.update(up, down)
        return _label_runs(
            s,
            mono=mono,
            bold=bold,
            italic=italic,
            upright=up,
            sloped=down,
            hits=self._upright_hit,
        )

    def fit_size(
        self,
        labels: Sequence[str],
        sizes: Sequence[int],
        width: float,
        *,
        bold: bool = False,
        mono: bool = False,
        italic: bool = False,
        upright: Iterable[str] = (),
        sloped: Iterable[str] = (),
    ) -> int:
        """The first of ``sizes`` at which every label fits ``width``.

        The body counterpart of :meth:`title_size`, and the same decision
        the plates kept making by hand: try the size the design wants, drop
        to the next when the Spanish runs longer than the English, and take
        the last as the floor. Passing several labels sizes a row on its
        longest member, so the panels of that row stay set alike rather
        than each shrinking on its own.

        ``sizes`` is read in preference order, largest first by convention;
        the last is returned when none fits, because a plate that overflows
        its box is still better than one that raises here.
        """
        for size in sizes:
            if all(
                self.text_width(
                    s,
                    size,
                    bold=bold,
                    mono=mono,
                    italic=italic,
                    upright=upright,
                    sloped=sloped,
                )
                <= width
                for s in labels
            ):
                return size
        return sizes[-1]

    def title_size(self, t: str) -> int:
        """The largest of :data:`_TITLE_SIZES` the title keeps its margin at.

        Takes the title *already translated*, so the string measured is
        the one the sheet will draw -- the Spanish of a plate runs about a
        quarter longer than its English, and it is the caller that holds
        the single translation the whole pipeline runs on. Returns the
        floor when nothing fits, leaving the fit gate to name the
        composition that has to be rewritten.
        """
        runs = _label_runs(t, bold=True)
        for size in _TITLE_SIZES:
            if measure(runs, size) <= self.w - 2 * _TITLE_MARGIN:
                return size
        return _TITLE_SIZES[-1]

    def text(
        self,
        x: float,
        y: float,
        s: str,
        size: int = 17,
        fill: str = "",
        anchor: str = "middle",
        *,
        bold: bool = False,
        mono: bool = False,
        italic: bool = False,
        upright: Iterable[str] = (),
        sloped: Iterable[str] = (),
    ) -> None:
        """Draw the label ``s`` at ``(x, y)``, translated for the sheet.

        ``upright`` names subscripts this label sets upright although the
        letters are not in :data:`_ROMAN_SCRIPTS`, each as ``"<base>_<letter
        run>"``: ``("S_p",)`` for the plant area of ISO 8297, ``("L′_n",)``
        for a normalized level. The set is keyed on the letters alone, so it
        cannot romanise a letter that is an index or a quantity somewhere
        else (the i of $L_i$, the p of $L_p$); this sets the descriptive one
        where it is drawn and leaves the index italic everywhere else. A key
        is matched against the symbol it is spelled with, so a call may pass
        one set to every label of a list and each label takes what is its own;
        a key no label of the plate uses is a typo, and :meth:`render`
        refuses it. ``sloped`` is the other direction, for the rarer source
        that prints a letter of the curated set italic (the f of $ΔL_f$ in
        ISO 3747, where RD 1367 sets the f of $K_f$ upright).
        """
        if anchor not in ("start", "middle", "end"):
            msg = f"'anchor' must be one of ('start', 'middle', 'end'); got {anchor!r}."
            raise ValueError(msg)
        s = self.tr(s)
        fragment = self._emit_text(
            x,
            y,
            s,
            size,
            fill or self.th.fg,
            anchor,
            bold=bold,
            mono=mono,
            italic=italic,
            upright=upright,
            sloped=sloped,
        )
        if fragment:
            self.add(fragment)

    def _emit_text(
        self,
        x: float,
        y: float,
        s: str,
        size: int,
        fill: str,
        anchor: str,
        *,
        bold: bool = False,
        mono: bool = False,
        italic: bool = False,
        upright: Iterable[str] = (),
        sloped: Iterable[str] = (),
    ) -> str:
        """The emission core of :meth:`text`: one already-translated label.

        The caller translates; this composes, measures and outlines. The
        pipeline is strictly tr -> compose -> measure -> outline, and the
        split is what lets the title of :meth:`render` share the exact
        same emission as every body label. The label is anchored at draw
        time from its measured width, checked against the sheet (the fit
        gate; ``PHONO_DIAGRAM_FIT=report`` downgrades the error to a
        stderr record so one run collects the full worklist), and written
        as ``<use>`` groups behind an XML comment carrying the source
        string. A label that composes to nothing emits nothing.
        """
        runs = self._runs(
            s, mono=mono, bold=bold, italic=italic, upright=upright, sloped=sloped
        )
        if not runs:
            return ""
        width = measure(runs, size)
        x0 = x - {"start": 0.0, "middle": width / 2, "end": width}[anchor]
        if x0 < -0.5 or x0 + width > self.w + 0.5:
            message = (
                f"label {s!r} spans {x0:.0f}..{x0 + width:.0f} on a {self.w} px sheet"
            )
            if os.environ.get("PHONO_DIAGRAM_FIT") == "report":
                print(f"fit: {message}", file=sys.stderr)
            else:
                raise ValueError(message)
        return _comment(s) + emit_runs(self._glyphs, runs, x0, y, size, fill)

    def path(
        self,
        d: str,
        fill: str = "none",
        stroke: str = "none",
        sw: float = 1.5,
        dash: str = "",
    ) -> None:
        dd = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(
            f'<path d="{d}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{sw}" stroke-linejoin="round"{dd}/>'
        )

    # -- technical helpers -------------------------------------------------
    def arrow(
        self, x1: float, y1: float, x2: float, y2: float, stroke: str, sw: float = 1.6
    ) -> None:
        """Straight arrow with a filled head at (x2, y2)."""
        import math

        ang = math.atan2(y2 - y1, x2 - x1)
        L, W = 9.0, 3.6
        bx, by = x2 - L * math.cos(ang), y2 - L * math.sin(ang)
        px, py = -math.sin(ang), math.cos(ang)
        self.line(x1, y1, bx, by, stroke, sw)
        self.path(
            f"M {x2:.1f} {y2:.1f} L {bx + W * px:.1f} {by + W * py:.1f} "
            f"L {bx - W * px:.1f} {by - W * py:.1f} Z",
            fill=stroke,
        )

    def dim(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        label: str,
        offset: float = 0.0,
        size: int = 15,
        label_side: str = "left",
        *,
        upright: Iterable[str] = (),
        sloped: Iterable[str] = (),
    ) -> None:
        """Dimension between two measured points, drafting style.

        The dimension line is placed ``offset`` px away (perpendicular);
        dashed witness lines connect it to the measured points. With
        ``offset=0`` the caller is responsible for any witness lines.
        ``upright`` and ``sloped`` are the key sets of :meth:`text`.
        """
        if label_side not in ("left", "right"):
            msg = f"'label_side' must be one of ('left', 'right'); got {label_side!r}."
            raise ValueError(msg)
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
            self.text(
                mid, y - 7, label, size, th.fg, "middle", upright=upright, sloped=sloped
            )
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
                self.text(
                    x + 9,
                    mid + 6,
                    label,
                    size,
                    th.fg,
                    "start",
                    upright=upright,
                    sloped=sloped,
                )
            else:
                self.text(
                    x - 9,
                    mid + 6,
                    label,
                    size,
                    th.fg,
                    "end",
                    upright=upright,
                    sloped=sloped,
                )

    def mic(
        self, x: float, capsule_top: float, ground: float, scale: float = 1.0
    ) -> None:
        """Measurement microphone on a stand that reaches the ground.

        ``capsule_top`` is the y of the capsule tip (the measurement point).
        """
        th, s = self.th, scale
        cap_h, body_h = 12 * s, 34 * s
        self.rect(x - 4 * s, capsule_top, 8 * s, cap_h, th.fg, rx=2.5 * s)
        self.rect(x - 6 * s, capsule_top + cap_h, 12 * s, body_h, th.primary, rx=4 * s)
        self.line(x, capsule_top + cap_h + body_h, x, ground, th.fg, 2.2)
        self.line(x - 16 * s, ground, x + 16 * s, ground, th.fg, 2.2)

    def person(
        self, x: float, y: float, h: float = 90.0, *, seated: bool = False
    ) -> None:
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
            self.line(x, y - h + 2 * r, x, y - h * 0.45, th.muted, 3)  # torso
            self.line(
                x, y - h * 0.45, x + h * 0.30, y - h * 0.45, th.muted, 2.4
            )  # thigh
            self.line(
                x + h * 0.30, y - h * 0.45, x + h * 0.30, y, th.muted, 2.4
            )  # shin
            self.line(x, y - h * 0.70, x + h * 0.22, y - h * 0.55, th.muted, 2.4)  # arm

    def ground(self, y: float, x1: float, x2: float, hatch: int = 24) -> None:
        th = self.th
        self.line(x1, y, x2, y, th.fg, 2.2)
        x = x1
        while x < x2:
            self.line(x, y, x - 8, y + 9, th.muted, 1.1)
            x += hatch

    def render(self, title: str) -> str:
        """Assemble the document: canvas, accessible title, atlas, artwork.

        The visible title routes through :meth:`_emit_text`, so the
        loudest string on every plate takes the same translation-once,
        measurement, fit gate, comment and outlining as every body label;
        the root ``<title>`` keeps a direct open accessible while the MDX
        alt text stays the site's accessible name. Its size comes from
        :meth:`title_size`, measured on that one translation. The
        ``<defs>`` atlas is assembled after the artwork, but its ids are
        content-derived, so document order stays deterministic either way.
        """
        th = self.th
        unused = sorted(self._upright_asked - self._upright_hit)
        if unused:
            msg = (
                f"slope keys {unused} set no subscript on the plate "
                f"{title!r}: spell each as the label writes the symbol, "
                "'<base>_<letter run>'"
            )
            raise ValueError(msg)
        t = self.tr(title)
        title_fragment = self._emit_text(
            self.w / 2, 30, t, self.title_size(t), th.fg, "middle", bold=True
        )
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" '
            f'height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
            f'<rect width="{self.w}" height="{self.h}" fill="{th.bg}"/>'
            f"<title>{_esc(t)}</title>"
            f"<defs>{self._glyphs.defs()}</defs>"
            + title_fragment
            + "".join(self.parts)
            + "</svg>"
        )


def _write(
    output_dir: str,
    name: str,
    build: Callable[[SVG, Theme], None],
    title: str,
    height: int = 560,
) -> None:
    assert_capabilities()
    for lang, lang_suffix in (("en", ""), ("es", "_es")):
        for th in (LIGHT, DARK):
            visit(name, lang)
            svg = SVG(900, height, th, lang)
            build(svg, th)
            path = Path(output_dir) / f"{name}{lang_suffix}{th.suffix}.svg"
            with path.open("w", encoding="utf-8") as fh:
                # The same pass the matplotlib figures take (see
                # generated_assets.compact_svg): this renderer already writes
                # short numbers and no indentation, so it changes little here,
                # and one rule over the whole corpus is what keeps the
                # comparison in check_figures.py the same for every file.
                fh.write(generated_assets.compact_svg(svg.render(title)))
    print(f"Generated {name}.svg (+dark, +es, +es_dark)")
