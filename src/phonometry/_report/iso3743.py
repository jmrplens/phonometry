#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Small-source test-room sound power fiches (reportlab, ISO 3743-1 and -2).

Renders the two ISO 3743 determinations to the one-page sound-power test sheet
the other sound-power methods print (:mod:`._sound_power_fiche`):

* a
  :class:`~phonometry.emission.sound_power_hard_walled.HardWalledSoundPowerResult`
  (ISO 3743-1:2010, the comparison with a reference sound source in a
  hard-walled test room), for the sound power level of Eq. 14 or the sound
  energy level of a burst of Eq. 20;
* a
  :class:`~phonometry.emission.sound_power_special_room.SpecialRoomSoundPowerResult`
  (ISO 3743-2:2018, the direct method of Formula 9 or the comparison method of
  Formula 10 in a special reverberation test room).

Both parts are engineering methods of accuracy grade 2. The sheet carries what
clauses 10.5 of Part 1 and 12.5 of Part 2 ask the record to hold: the
octave-band levels of the source (and of the reference sound source where
there is one), the determined levels in octave bands and A-weighted, the
expanded uncertainty with its coverage factor and, marked in the table and
stated beneath it, the bands whose background noise requirement was not met,
which 8.1.3 of Part 1 and 9.8 of Part 2 require a report to say in words.
Part 1 rounds the levels to 0,1 dB (10.5 g); Part 2 asks for the corrected
band levels to the nearest one-half decibel (12.5 d), so its band column is
tabulated that way, while its A-weighted level, for which 12.5 c) sets no
rounding, keeps 0,1 dB. Of the Part 1 bands that fail the requirement, only
those where the source under test's own margin fell short are named upper
bounds, as 8.1.3 has it; a short margin of the reference sound source lowers
the level instead, and such a band is named only as failing 4.5. The
quantity-independent skeleton lives in :mod:`._layout`; reportlab, matplotlib
and svglib are soft dependencies imported lazily.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np

from ._i18n import format_number, t
from ._sound_power_fiche import (
    FicheCopy,
    band_labels,
    d1,
    energy_sum,
    fraction_caption,
    level_limit_verdict,
    power_statement,
    power_value_table,
    power_verdict,
    range_str,
    render_sound_power_fiche,
)

if TYPE_CHECKING:
    from reportlab.platypus import Table

    from ..emission.sound_power_hard_walled import HardWalledSoundPowerResult
    from ..emission.sound_power_special_room import SpecialRoomSoundPowerResult
    from .metadata import ReportMetadata


#: Band-frequency column heading of the per-band table (translated by ``t``).
_COL_FREQUENCY = "f [Hz]"
#: Band sound-power level column heading (mini-HTML for reportlab).
_COL_LW = "L<sub>W</sub> [dB]"
#: Band sound-energy level column heading.
_COL_LJ = "L<sub>J</sub> [dB]"
#: The marker of a band 8.1.3 of Part 1 makes an upper bound; in Part 2, of
#: any band whose background requirement is not shown to be met.
_UPPER_BOUND_MARK = "*"
#: The marker of a Part 1 band that fails 4.5 without being an upper bound (a
#: short margin of the reference sound source, or no background measured).
_NOT_MET_MARK = "\N{DAGGER}"
#: Reference sound energy for the sound energy level, 1 pJ = 10^-12 J.
_ENERGY_REFERENCE = "1 pJ"
#: Total width of the per-band table in millimetres (the fiche text width).
_TABLE_WIDTH_MM = 174.0
#: Size of the embedded spectrum in inches. Shallower than the shared default:
#: the sheet also carries the reference sound source's columns and the
#: uncertainty and background statements the standard asks for.
_FIGSIZE = (9.2, 2.6)
#: The two coverage factors both parts print: 95 % two-sided (9.1 of Part 1,
#: 11.1 of Part 2) and 95 % one-sided, for a comparison with a limit.
_COVERAGE_TWO_SIDED = 2.0
_COVERAGE_ONE_SIDED = 1.6


def _widths(columns: int) -> list[float]:
    """Equal column widths filling the fiche text width."""
    return [_TABLE_WIDTH_MM / columns] * columns


def _marked(values: np.ndarray, marks: list[str], language: str) -> list[str]:
    """One decimal per band, followed by the band's background marker."""
    return [
        d1(float(value), language) + (f" {mark}" if mark else "")
        for value, mark in zip(values, marks, strict=True)
    ]


def _hard_walled_marks(result: HardWalledSoundPowerResult) -> list[str]:
    """``*`` on the upper bounds of 8.1.3, ``†`` on the other failing bands."""
    return [
        "" if bool(ok) else (_UPPER_BOUND_MARK if bool(upper) else _NOT_MET_MARK)
        for ok, upper in zip(
            result.background_requirement_met, result.upper_bound, strict=True
        )
    ]


def _nearest_half(values: np.ndarray) -> np.ndarray:
    """The levels to the nearest one-half decibel (ISO 3743-2:2018, 12.5 d)."""
    return np.asarray(np.round(2.0 * np.asarray(values, dtype=np.float64)) / 2.0)


def _coverage_sentence(k: float, language: str) -> str:
    """What the coverage factor of the sheet gives, as 9.1 of Part 1 and 11.1
    of Part 2 print it: 95 % two-sided for ``k`` = 2, 95 % one-sided for a
    comparison with a limit for ``k`` = 1,6, and the factor alone otherwise.
    """
    value = format_number(float(k), language, decimals=1, trim=True)
    if math.isclose(k, _COVERAGE_TWO_SIDED):
        return t("k = 2 gives a coverage probability of 95 %.", language)
    if math.isclose(k, _COVERAGE_ONE_SIDED):
        return t(
            "k = {k} gives a coverage probability of 95 % for a one-sided "
            "comparison with a limit.",
            language,
        ).format(k=value)
    return t("the coverage factor is k = {k}.", language).format(k=value)


def _uncertainty_term(
    result: HardWalledSoundPowerResult | SpecialRoomSoundPowerResult, language: str
) -> str | None:
    """The expanded uncertainty of the headline level with its coverage factor."""
    value = float(result.expanded_uncertainty_a)
    if not math.isfinite(value):
        return None
    return t(
        "Expanded uncertainty U = {value} dB, coverage factor k = {k}", language
    ).format(
        value=d1(value, language),
        k=format_number(float(result.coverage_factor), language, decimals=1, trim=True),
    )


def _closing_strip(
    result: HardWalledSoundPowerResult | SpecialRoomSoundPowerResult,
    table: str,
    a_weighting: str,
    language: str,
) -> str:
    """How the expanded uncertainty was formed, then the A-weighting basis.

    The two travel as one paragraph so that the sheet, which also carries the
    reference sound source's columns and the background statement the
    standard asks for, still fits its one page.
    """
    sigma_omc = float(result.sigma_omc)
    if not math.isfinite(sigma_omc):
        uncertainty = t(
            "No expanded uncertainty is stated: &#963;<sub>omc</sub> was not supplied.",
            language,
        )
    else:
        uncertainty = t(
            "U = k &#963;<sub>tot</sub>, &#963;<sub>tot</sub> = "
            "&#8730;(&#963;<sub>R0</sub><super>2</super> + "
            "&#963;<sub>omc</sub><super>2</super>) with &#963;<sub>R0</sub> = "
            "{sr0} dB ({table}, A-weighted) and &#963;<sub>omc</sub> = {omc} dB; "
            "{coverage}",
            language,
        ).format(
            sr0=d1(float(result.sigma_r0_a), language),
            table=table,
            omc=d1(sigma_omc, language),
            coverage=_coverage_sentence(float(result.coverage_factor), language),
        )
    return f"{uncertainty} {a_weighting}"


# --- ISO 3743-1 ----------------------------------------------------------------


def _hard_walled_energy(result: HardWalledSoundPowerResult) -> bool:
    """``True`` for a sound energy determination (Eq. 20), ``False`` for power."""
    return result.quantity == "energy"


def _hard_walled_basis(result: HardWalledSoundPowerResult, language: str) -> str:
    """The standard-basis line of an ISO 3743-1 sheet."""
    grade = t("engineering method, accuracy grade 2", language)
    if _hard_walled_energy(result):
        return t(
            "Determination of the sound energy level of a source emitting "
            "bursts by comparison with a reference sound source in a "
            "hard-walled test room (ISO 3743-1:2010, {grade}).",
            language,
        ).format(grade=grade)
    return t(
        "Determination of the sound power level by comparison with a "
        "reference sound source in a hard-walled test room (ISO 3743-1:2010, "
        "{grade}).",
        language,
    ).format(grade=grade)


def _hard_walled_table(
    result: HardWalledSoundPowerResult, *, verbose: bool, language: str
) -> Table:
    """The per-band table of the comparison: both sources and the result.

    The default is ``f | L'(ST) | L'p(RSS) | LW(RSS) | LW`` (``LJ`` and the
    single event level for an energy determination); ``verbose`` adds the mean
    background level and the two background corrections of Eq. 13.
    """
    energy = _hard_walled_energy(result)
    level = result.sound_energy_level if energy else result.sound_power_level
    n = level.size
    labels, fraction = band_labels(result.frequencies, n, language)
    source_head = (
        "L&#8242;<sub>E</sub>(ST) [dB]" if energy else "L&#8242;<sub>p</sub>(ST) [dB]"
    )
    header = [
        t(_COL_FREQUENCY, language),
        source_head,
        "L&#8242;<sub>p</sub>(RSS) [dB]",
    ]
    if verbose:
        header += [
            "L<sub>p</sub>(B) [dB]",
            "K<sub>1</sub> [dB]",
            "K<sub>1</sub>(RSS) [dB]",
        ]
    header += ["L<sub>W</sub>(RSS) [dB]", _COL_LJ if energy else _COL_LW]
    marked = _marked(level, _hard_walled_marks(result), language)
    rows: list[list[str]] = []
    for i in range(n):
        row = [
            labels[i],
            d1(result.mean_source_level[i], language),
            d1(result.mean_reference_level[i], language),
        ]
        if verbose:
            row += [
                d1(result.mean_background_level[i], language),
                d1(result.background_correction[i], language),
                d1(result.background_correction_ref[i], language),
            ]
        row += [d1(result.reference_power_level[i], language), marked[i]]
        rows.append(row)
    return power_value_table(header, rows, _widths(len(header)), fraction)


def _hard_walled_statement(
    result: HardWalledSoundPowerResult, language: str
) -> tuple[str, list[str], float]:
    """The boxed result, its extended terms and the A-weighted headline."""
    if _hard_walled_energy(result):
        lja = float(result.sound_energy_level_a)
        statement = t(
            "Sound energy level L<sub>JA</sub> = <b>{value} dB(A)</b> re {ref}",
            language,
        ).format(value=d1(lja, language), ref=_ENERGY_REFERENCE)
        total = energy_sum(result.sound_energy_level)
        extended = [
            t("Total L<sub>J</sub> = {value} dB re {ref}", language).format(
                value=d1(total, language), ref=_ENERGY_REFERENCE
            ),
            t(
                "Determination method: comparison with a reference sound "
                "source (Eq. 20)",
                language,
            ),
        ]
        headline = lja
    else:
        statement, extended = power_statement(result, language)
        extended.append(
            t(
                "Determination method: comparison with a reference sound "
                "source (Eq. 14)",
                language,
            )
        )
        headline = float(result.sound_power_level_a)
    uncertainty = _uncertainty_term(result, language)
    if uncertainty is not None:
        extended.append(uncertainty)
    return statement, extended, headline


def _hard_walled_corrections(result: HardWalledSoundPowerResult, language: str) -> str:
    """The Eq. 10 to 14 (or 18 to 20) chain with the corrections it applied."""
    values = {
        "k1": range_str(result.background_correction, language),
        "k1r": range_str(result.background_correction_ref, language),
        "c2": format_number(float(result.c2), language, decimals=2),
    }
    if _hard_walled_energy(result):
        return t(
            "The mean levels L&#8242;<sub>E</sub>(ST) (the single event level "
            "of one event, Eq. 15 to 18), L&#8242;<sub>p</sub>(RSS) and "
            "L<sub>p</sub>(B) are energy averages over the microphone "
            "positions; the background correction is applied to the means "
            "(Eq. 19), K1 = {k1} dB and K1(RSS) = {k1r} dB; L<sub>J</sub> = "
            "L<sub>W</sub>(RSS) &#8722; L&#8242;<sub>p</sub>(RSS) + "
            "L&#8242;<sub>E</sub>(ST) + K1(RSS) &#8722; K1 (Eq. 20). The levels "
            "are at the meteorological conditions of the test; C2 = {c2} dB "
            "(Annex A) carries them to the reference conditions.",
            language,
        ).format(**values)
    return t(
        "The mean levels L&#8242;<sub>p</sub>(ST), L&#8242;<sub>p</sub>(RSS) and "
        "L<sub>p</sub>(B) are energy averages over the microphone positions "
        "(Eq. 10 to 12); the background correction is applied to the means "
        "(Eq. 13), K1 = {k1} dB and K1(RSS) = {k1r} dB; L<sub>W</sub> = "
        "L<sub>W</sub>(RSS) &#8722; L&#8242;<sub>p</sub>(RSS) + "
        "L&#8242;<sub>p</sub>(ST) + K1(RSS) &#8722; K1 (Eq. 14). The levels are "
        "at the meteorological conditions of the test; C2 = {c2} dB (Annex A) "
        "carries them to the reference conditions.",
        language,
    ).format(**values)


def _hard_walled_background(
    result: HardWalledSoundPowerResult, language: str
) -> str | None:
    """The sentences that name the failing bands, when there are any.

    8.1.3 calls a band an upper bound only on the source under test's own
    margin, and asks the report to say so together with the requirement not
    fulfilled; a band where the reference sound source's margin is short is
    named as failing 4.5, and why it is no upper bound.
    """
    if bool(np.all(result.background_requirement_met)):
        return None
    if not bool(np.any(np.isfinite(result.mean_background_level))):
        return t(
            "\N{DAGGER} No background noise was measured, so the background noise "
            "requirements of ISO 3743-1:2010 are not shown to be fulfilled in "
            "any band (4.5).",
            language,
        )
    sentences: list[str] = []
    upper = np.asarray(result.upper_bound, dtype=bool)
    if bool(np.any(upper)):
        sentences.append(
            t(
                "* Upper bound: the background noise margin of the source under "
                "test is below 6 dB in this band, so the level is an upper bound "
                "and the background noise requirements of ISO 3743-1:2010 are "
                "not fulfilled in it (4.5, 8.1.3).",
                language,
            )
        )
    if bool(np.any(~np.asarray(result.background_requirement_met) & ~upper)):
        sentences.append(
            t(
                "\N{DAGGER} The background noise margin of the reference sound "
                "source is below 6 dB in this band, so the background noise "
                "requirements of ISO 3743-1:2010 are not fulfilled in it (4.5); "
                "its capped K1(RSS) lowers the level, which is therefore no "
                "upper bound (8.1.4).",
                language,
            )
        )
    return " ".join(sentences)


def _hard_walled_a_weighting(result: HardWalledSoundPowerResult, language: str) -> str:
    """The Annex B citation line."""
    if _hard_walled_energy(result):
        return t(
            "The A-weighted sound energy level L<sub>JA</sub> combines the "
            "octave-band levels with the corrections of ISO 3743-1:2010 "
            "Annex B (Table B.1, Eq. B.2). Levels are referenced to the "
            "reference sound energy 1 pJ.",
            language,
        )
    return t(
        "The A-weighted sound power level L<sub>WA</sub> combines the "
        "octave-band levels with the corrections of ISO 3743-1:2010 Annex B "
        "(Table B.1, Eq. B.1). Levels are referenced to the reference sound "
        "power 1 pW.",
        language,
    )


def render_hard_walled_power_report(
    result: HardWalledSoundPowerResult,
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    verbose: bool = False,
    language: str = "en",
) -> str:
    """Render an ISO 3743-1 hard-walled test room fiche to ``path``.

    :param result: The determination, a sound power (Eq. 14) or a sound energy
        (Eq. 20) level.
    :param path: Destination path of the PDF file.
    :param metadata: Optional :class:`ReportMetadata`; a ``requirement`` is
        read as a declared A-weighted limit, lower is better.
    :param verbose: Add the mean background level and ``K1``/``K1(RSS)`` to
        the per-band table.
    :param language: ``"en"`` (default) or ``"es"``.
    :return: The written ``path`` as a :class:`str`.
    """
    statement, extended, headline = _hard_walled_statement(result, language)
    energy = _hard_walled_energy(result)
    verdict = None
    if metadata is not None and metadata.requirement is not None:
        verdict = (
            level_limit_verdict(
                headline, metadata.requirement, "L<sub>JA</sub>", language
            )
            if energy
            else power_verdict(result, metadata.requirement, language)
        )
    strips = [_hard_walled_corrections(result, language)]
    background = _hard_walled_background(result, language)
    if background is not None:
        strips.append(background)
    strips.append(
        _closing_strip(
            result,
            t("Table 3", language),
            _hard_walled_a_weighting(result, language),
            language,
        )
    )
    caption = (
        t("Octave-band sound energy levels", language)
        if energy
        else fraction_caption(result, language)
    )
    return render_sound_power_fiche(
        result,
        path,
        copy=FicheCopy(
            title=t(
                "Sound energy determination" if energy else "Sound power determination",
                language,
            ),
            basis=_hard_walled_basis(result, language),
            caption=caption,
            statement=statement,
            extended=extended,
            basis_strips=strips,
        ),
        value_table=_hard_walled_table(result, verbose=verbose, language=language),
        metadata=metadata,
        language=language,
        verdict=verdict,
        figsize=_FIGSIZE,
    )


# --- ISO 3743-2 ----------------------------------------------------------------


def _special_comparison(result: SpecialRoomSoundPowerResult) -> bool:
    """``True`` for Formula 10, ``False`` for the direct Formula 9."""
    return result.method == "comparison"


def _special_basis(result: SpecialRoomSoundPowerResult, language: str) -> str:
    """The standard-basis line of an ISO 3743-2 sheet."""
    grade = t("engineering method, accuracy grade 2", language)
    if _special_comparison(result):
        return t(
            "Determination of the sound power level in a special reverberation "
            "test room, comparison method using a reference sound source "
            "(ISO 3743-2:2018, {grade}).",
            language,
        ).format(grade=grade)
    return t(
        "Determination of the sound power level from the mean sound pressure "
        "level in a special reverberation test room, direct method "
        "(ISO 3743-2:2018, {grade}).",
        language,
    ).format(grade=grade)


def _special_table(
    result: SpecialRoomSoundPowerResult, *, verbose: bool, language: str
) -> Table:
    """The per-band table: the mean level, the reference source and ``LW``.

    The direct method prints ``f | Lp | LW``, the comparison method
    ``f | Lpe | Lpr | LWr | LW``; ``verbose`` adds the per-band shift of the
    Table 4 background corrections.
    """
    n = result.sound_power_level.size
    labels, fraction = band_labels(result.frequencies, n, language)
    comparison = _special_comparison(result)
    header = [t(_COL_FREQUENCY, language)]
    header.append("L<sub>pe</sub> [dB]" if comparison else "L<sub>p</sub> [dB]")
    if comparison:
        header.append("L<sub>pr</sub> [dB]")
    if verbose:
        header.append(t("Background corr. [dB]", language))
    if comparison:
        header.append("L<sub>Wr</sub> [dB]")
    header.append(_COL_LW)
    # 12.5 d) tabulates the corrected band levels to the nearest one-half
    # decibel; 9.8 names a failing band without calling it an upper bound.
    marked = _marked(
        _nearest_half(result.sound_power_level),
        [
            "" if bool(ok) else _UPPER_BOUND_MARK
            for ok in result.background_requirement_met
        ],
        language,
    )
    rows: list[list[str]] = []
    for i in range(n):
        row = [labels[i], d1(result.mean_pressure_level[i], language)]
        if comparison:
            row.append(d1(result.mean_reference_level[i], language))
        if verbose:
            row.append(d1(result.background_correction[i], language))
        if comparison:
            row.append(d1(result.reference_power_level[i], language))
        row.append(marked[i])
        rows.append(row)
    return power_value_table(header, rows, _widths(len(header)), fraction)


def _special_headline(result: SpecialRoomSoundPowerResult) -> float | None:
    """The A-weighted level the sheet boxes, when it is not the band total.

    Clause 4 reads the A-weighted level of the direct method from the
    A-weighted sound pressure levels (Formula 9); where they were measured,
    that is the boxed level and the Annex F band total is stated beside it.
    """
    direct = float(result.sound_power_level_a_direct)
    return direct if math.isfinite(direct) else None


def _special_statement(
    result: SpecialRoomSoundPowerResult, language: str
) -> tuple[str, list[str]]:
    """The boxed result and its extended terms."""
    level_a = _special_headline(result)
    statement, extended = power_statement(result, language, level_a=level_a)
    if level_a is not None and math.isfinite(float(result.sound_power_level_a)):
        extended.append(
            t(
                "From the octave bands (Annex F): L<sub>WA</sub> = {value} dB(A)",
                language,
            ).format(value=d1(float(result.sound_power_level_a), language))
        )
    if _special_comparison(result):
        extended.append(
            t("Determination method: comparison method (Formula 10)", language)
        )
    else:
        extended.append(
            t(
                "Determination method: direct method (Formula 9), V = {volume} "
                "m<super>3</super>, T<sub>nom</sub> = {tnom} s",
                language,
            ).format(
                volume=format_number(float(result.volume_m3), language, decimals=1),
                tnom=format_number(
                    float(result.nominal_reverberation_time_s), language, decimals=2
                ),
            )
        )
    uncertainty = _uncertainty_term(result, language)
    if uncertainty is not None:
        extended.append(uncertainty)
    return statement, extended


def _special_corrections(result: SpecialRoomSoundPowerResult, language: str) -> str:
    """Formula 8 with Table 4, and Formula 9 or 10."""
    c2 = format_number(float(result.c2), language, decimals=2)
    if _special_comparison(result):
        return t(
            "The mean levels L<sub>pe</sub> of the source and L<sub>pr</sub> of "
            "the reference sound source are energy averages over the microphone "
            "positions (Formula 8), each level corrected for background noise "
            "by Table 4 at its own position (9.8); L<sub>We</sub> = "
            "L<sub>pe</sub> + (L<sub>Wr</sub> &#8722; L<sub>pr</sub>) (Formula "
            "10). The levels are at the meteorological conditions of the test; "
            "C2 = {c2} dB (Annex E) carries them to the reference conditions.",
            language,
        ).format(c2=c2)
    return t(
        "The mean level L<sub>p</sub> is the energy average over the "
        "microphone positions and source locations (Formula 8), each level "
        "corrected for background noise by Table 4 at its own position (9.8); "
        "L<sub>W</sub> = L<sub>p</sub> &#8722; 10 lg(T<sub>nom</sub>/"
        "T<sub>0</sub>) + 10 lg(V/V<sub>0</sub>) &#8722; 13 dB (Formula 9). "
        "The levels are at the meteorological conditions of the test; C2 = "
        "{c2} dB (Annex E) carries them to the reference conditions.",
        language,
    ).format(c2=c2)


def _special_rounding(language: str) -> str:
    """The sentence that says how the band column of Part 2 is rounded."""
    return t(
        "The band levels L<sub>W</sub> are tabulated to the nearest one-half "
        "decibel (12.5 d).",
        language,
    )


def _special_a_weighting(result: SpecialRoomSoundPowerResult, language: str) -> str:
    """The clause 4 / Annex F citation line."""
    if _special_headline(result) is not None:
        return t(
            "The A-weighted sound power level L<sub>WA</sub> is Formula (9) "
            "applied to the mean A-weighted sound pressure level (clause 4); "
            "the octave-band total combines the band levels with the "
            "corrections of ISO 3743-2:2018 Annex F (Table F.1, Formula F.1). "
            "Levels are referenced to the reference sound power 1 pW.",
            language,
        )
    return t(
        "The A-weighted sound power level L<sub>WA</sub> combines the "
        "octave-band levels with the corrections of ISO 3743-2:2018 Annex F "
        "(Table F.1, Formula F.1). Levels are referenced to the reference "
        "sound power 1 pW.",
        language,
    )


def render_special_room_power_report(
    result: SpecialRoomSoundPowerResult,
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    verbose: bool = False,
    language: str = "en",
) -> str:
    """Render an ISO 3743-2 special reverberation test room fiche to ``path``.

    :param result: The determination by the direct (Formula 9) or the
        comparison (Formula 10) method.
    :param path: Destination path of the PDF file.
    :param metadata: Optional :class:`ReportMetadata`; a ``requirement`` is
        read as a declared A-weighted limit, lower is better, and is compared
        with the boxed level.
    :param verbose: Add the per-band Table 4 background corrections to the
        table.
    :param language: ``"en"`` (default) or ``"es"``.
    :return: The written ``path`` as a :class:`str`.
    """
    statement, extended = _special_statement(result, language)
    verdict = None
    if metadata is not None and metadata.requirement is not None:
        verdict = power_verdict(
            result, metadata.requirement, language, level_a=_special_headline(result)
        )
    strips = [f"{_special_corrections(result, language)} {_special_rounding(language)}"]
    if not bool(np.all(result.background_requirement_met)):
        strips.append(
            t(
                "* The background noise requirements of ISO 3743-2:2018 are "
                "not shown to be fulfilled in this band: a margin is below 4 dB "
                "at a microphone position, or no background noise was measured "
                "(6.5, 9.8).",
                language,
            )
        )
    strips.append(
        _closing_strip(
            result,
            t("Table 5", language),
            _special_a_weighting(result, language),
            language,
        )
    )
    return render_sound_power_fiche(
        result,
        path,
        copy=FicheCopy(
            title=t("Sound power determination", language),
            basis=_special_basis(result, language),
            caption=fraction_caption(result, language),
            statement=statement,
            extended=extended,
            basis_strips=strips,
        ),
        value_table=_special_table(result, verbose=verbose, language=language),
        metadata=metadata,
        language=language,
        verdict=verdict,
        figsize=_FIGSIZE,
    )
