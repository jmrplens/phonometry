#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Silencers, screens and barriers measured where they stand.

ISO 11820:1996, ISO 11821:1997 and ISO 10847:1997 measure three different
things in the field and none of them prints a worked example. What they do
print is tables and thresholds, what their equations offer is identities, and
what closes the gap is other people's worked examples and campaigns, so every
row here says which of those it rests on.

**Printed tables and thresholds.** Table 1 of ISO 11820 and Tables 1 and 3 of
ISO 10847, cell by cell; the twenty installations of Figure 1 of ISO 11820 with
the area rule clause 9 gives each; the window and the repeat rules of
ISO 11821.

**Closed form.** The Sabine area of Equations (6), (10) and (12), the two
measurement distances of Equations (15) and (16), the gas density of Equation
(29), the temperature field correction of Equations (20) and (22), the boxed
background formula of ISO 11821 5.7 at the two ends of its window, and the
divergence rates definition 3.10 of ISO 10847 states.

**Algebraic identity.** The strongest oracle any of the three offers is in
ISO 10847: the indirect method reduces exactly to the direct one when the
receiver is of the same kind in both campaigns, and moves by exactly 6 dB when
it is not. Beside it are the source-normalisation invariance of the reference
position and the level-shift invariance of the two ISO 11820 losses.

**Three rules for one correction.** The three documents correct for the
background three different ways, and the rows say so: a stepped table that
takes off 0,5 dB at a 9 dB margin, a stepped table that takes off 1 dB at the
same margin, and the energy subtraction itself.

**Printed numbers for ISO 11820, from elsewhere.** Annex B of ISO 14163:1998
works the one-third-octave to octave conversion of 9.1.5 through three spectra
and prints the answer, which is the only worked example of an ISO 11820
quantity printed by ISO. Beside it are a 2014 master's thesis at the
Universidad Politecnica de Madrid, which measured three splitter silencers to
UNE-EN ISO 11820 and printed the whole reduction, and the textbook and
guideline examples of the closed forms ISO 11820 shares with the rest of the
field: the energy mean, the background subtraction, the Sabine area, the area
and field-correction terms of a sound power, the ideal gas law and the area
scaling of a flow velocity. Those rows compare against
``tests/reference_data/silencer_in_situ.py``, which carries the citation of
every number and the two readings deliberately left out of it.

**A printed level pair, from outside the standard.** Clauses 5.8 and 5.9 of
ISO 11821 are a subtraction, and the standard prints no pair to subtract.
Published worked examples do, and the rows that use them say where each one
sits: Barron's Example 7-9 is an outdoor barrier, which the Introduction of
ISO 11821 sends to ISO 10847, and Hansen's Example 6.23 is an open-plan office
screen, which it sends to ISO 10053. Barron's Example 7-10 is the one in
scope, a screen indoors at one operator position, and even that is a
prediction rather than a measurement. So what these rows anchor is the
band-by-band difference, the A-weighted one, the integer rounding of 7.4 c)
and the background subtraction of 5.7, on numbers this project did not choose;
they anchor no physics, because clause 5.8 contains none.

The documents are Randall F. Barron, Industrial Noise Control and Acoustics,
Marcel Dekker, New York, 2003; Colin H. Hansen, Noise Control: From Concept to
Application, Taylor & Francis, first published 2005 and republished the same
year in the Taylor & Francis e-Library, which is the edition of the copy read
here; Sound Research Laboratories Ltd, Noise Control in Industry, third
edition, E. & F.N. Spon, London, 1991; and Laermschutz-Arbeitsblatt
IFA-LSA 01-234, Raumakustik in industriellen Arbeitsraeumen, IFA and DGUV,
second edition, April 2020. Barron prints the folio only in the text layer of
its electronic edition, so the folios cited for it are the book's own
pagination rather than ink on the page; Hansen prints its folio in the running
head of every page, and that is the folio cited.

**Campaigns measured against ISO 10847.** The standard prints no example, but
the people who followed it published theirs, and five documents carry a barrier
measurement all the way from the printed levels to the printed insertion loss.
The strongest is a 1985 road-barrier study whose tables give the reference and
the receiver level for every run of both methods; beside it are a Spanish
demonstration that prints all four levels of two cases, a Lithuanian highway
campaign, an outboard-motor screen measured with no reference microphone at
all, and the arithmetic example the United States highway administration prints
in its own measurement manual. None of them is a substitute for the procedure:
each row says which part of clause 8.2 its numbers reach and which part they
leave untouched, because a campaign that agrees with the subtraction says
nothing about the wind classes, the background table or the receiver
correction.

Those documents are W. Lindeman, "Comparison of Noise Barrier Insertion-Loss
Methodologies", Transportation Research Record 1033, Transportation Research
Board, 1985; R. Cordero and others, "Metodologia experimental para medida
perdidas por insercion de pantallas acusticas de carretera", 41 Congreso
Nacional de Acustica, Leon, 2010, paper AAM_026; A. Jagniatinskis, B. Fiks and
M. Mickaitis, "Determination of Insertion Loss of Acoustic Barriers under
Specific Conditions", Procedia Engineering 187, 2017; L. Rodino and F. Masson,
"Diseno e implementacion de una barrera acustica para motores fuera de borda",
XIII Congreso Argentino de Acustica, Buenos Aires, 2015, paper AdAA2015-A009;
and C. S. Y. Lee and G. G. Fleming, Measurement of Highway-Related Noise,
FHWA-PD-96-046, Federal Highway Administration, May 1996. Two further
documents corroborate constants ISO 10847 prints without an example of its
own: CEN/TS 16272-7:2015 reprints the background table and the wind classes,
and D. A. Bies, C. H. Hansen and C. Q. Howard, Engineering Noise Control, fifth
edition, CRC Press, 2017, prints the pressure doubling the receiver correction
is.
"""

from __future__ import annotations

import math
import warnings

import numpy as np
from reference_data import silencer_in_situ as oracle

import phonometry as ph
from phonometry.environment.propagation.barrier_in_situ import (
    ISO10847_BACKGROUND_CORRECTIONS_DB,
    RECEIVER_CORRECTIONS_DB,
    ReceiverType,
)
from phonometry.noise_control.silencer_in_situ import (
    INSTALLATION_CASES,
    ISO11820_BACKGROUND_CORRECTIONS_DB,
    ISO11820_SOUND_SPEED_M_S,
    SABINE_AREA_COEFFICIENT,
)

from ..registry import Outcome, count, numeric, record, register

_IN_SITU = "In-situ measurement of silencers, screens and barriers"

#: An octave spectrum to put the identities on, in decibels.
_BANDS = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0])
_SOURCE = np.array([95.0, 96.0, 97.0, 95.0, 92.0, 88.0])
_RECEIVER = np.array([70.0, 68.0, 65.0, 60.0, 55.0, 51.0])


@register(
    _IN_SITU,
    "ISO 11820:1996 Table 1",
    "The stepped background correction, dB to subtract, over the eight printed rows",
)
def _chk_iso11820_table_one() -> Outcome:
    printed = {
        "3 dB": 3.0,
        "4 dB": 2.0,
        "5 dB": 2.0,
        "6 dB": 1.0,
        "7 dB": 1.0,
        "8 dB": 1.0,
        "9 dB": 0.5,
        "10 dB": 0.5,
    }
    computed = {
        f"{margin} dB": float(
            ph.noise_control.silencer_background_correction_db([float(margin)])[0]
        )
        for margin in ISO11820_BACKGROUND_CORRECTIONS_DB
    }
    return record(printed, computed, unit="dB")


@register(
    _IN_SITU,
    "ISO 11820:1996 Table 1",
    "The printed table is a rounded version of the logarithmic subtraction "
    "and departs from it by under 0,35 dB",
)
def _chk_iso11820_table_against_the_formula() -> Outcome:
    margins = np.arange(3, 11, dtype=float)
    table = ph.noise_control.silencer_background_correction_db(margins)
    exact = -10.0 * np.log10(1.0 - 10.0 ** (-0.1 * margins))
    worst = float(np.max(np.abs(table - exact)))
    return numeric(
        0.0,
        worst,
        0.35,
        unit="dB",
        expected_label="under 0,35 dB over the eight rows",
        computed_label=f"largest departure {worst:.3f} dB",
    )


@register(
    _IN_SITU,
    "ISO 11820:1996 Eq. (19)",
    "The transmission loss is unmoved by a level shift common to both sides "
    "of the silencer",
)
def _chk_iso11820_level_shift_invariance() -> Outcome:
    plain = ph.noise_control.in_situ_transmission_loss(
        _SOURCE, _RECEIVER, source_area_m2=2.0, receiver_area_m2=1.0
    )
    shifted = ph.noise_control.in_situ_transmission_loss(
        _SOURCE + 6.5, _RECEIVER + 6.5, source_area_m2=2.0, receiver_area_m2=1.0
    )
    worst = float(np.max(np.abs(plain.loss_db - shifted.loss_db)))
    return numeric(
        0.0,
        worst,
        1e-12,
        unit="dB",
        computed_label=f"max absolute difference {worst:.3f} dB over 6 bands",
    )


@register(
    _IN_SITU,
    "ISO 11820:1996 Eqs. (20) and (22)",
    "The temperature field correction is 5 lg of the ratio of the two "
    "absolute temperatures, and vanishes when they agree",
)
def _chk_iso11820_temperature_correction() -> Outcome:
    printed = {
        "20 C both sides": 0.0,
        "20 C and 200 C": 5.0 * math.log10(293.0 / 473.0),
    }
    computed = {
        "20 C both sides": ph.noise_control.temperature_field_correction_db(
            receiver_temperature_c=20.0, source_temperature_c=20.0
        ),
        "20 C and 200 C": ph.noise_control.temperature_field_correction_db(
            receiver_temperature_c=20.0, source_temperature_c=200.0
        ),
    }
    worst = max(abs(printed[k] - computed[k]) for k in printed)
    return numeric(0.0, worst, 1e-12, unit="dB")


@register(
    _IN_SITU,
    "ISO 11820:1996 Eqs. (6), (10) and (12)",
    "A quarter of the Sabine absorption as an area, 6 ln 10 V / (c T), at "
    "the printed c = 340 m/s",
)
def _chk_iso11820_sabine_area() -> Outcome:
    volume, time = 300.0, 1.2
    expected = SABINE_AREA_COEFFICIENT * volume / (ISO11820_SOUND_SPEED_M_S * time)
    computed = float(ph.noise_control.reverberant_surface_area_m2(volume, [time])[0])
    return numeric(expected, computed, 1e-9, unit="m2", places=4)


@register(
    _IN_SITU,
    "ISO 11820:1996 Eqs. (15) and (16)",
    "The upstream distance is 1,5 equivalent diameters and the downstream "
    "one is 12 sqrt(S_d) less 10 sqrt(S_f)",
)
def _chk_iso11820_measurement_distances() -> Outcome:
    printed = {
        "upstream, S_u = 0,25 m2": 1.5 * math.sqrt(4.0 * 0.25 / math.pi),
        "downstream, S_d = 0,25 m2 and S_f = 0,09 m2": 12.0 * 0.5 - 10.0 * 0.3,
    }
    computed = {
        "upstream, S_u = 0,25 m2": ph.noise_control.measurement_distance_upstream_m(
            0.25
        ),
        "downstream, S_d = 0,25 m2 and S_f = 0,09 m2": (
            ph.noise_control.measurement_distance_downstream_m(0.25, 0.09)
        ),
    }
    worst = max(abs(printed[k] - computed[k]) for k in printed)
    return numeric(0.0, worst, 1e-9, unit="m")


@register(
    _IN_SITU,
    "ISO 11820:1996 Eq. (29)",
    "The gas density with the printed R/M = 287 for air and p_amb = 100 kPa",
)
def _chk_iso11820_gas_density() -> Outcome:
    expected = 100_000.0 / (287.0 * 293.0)
    computed = ph.noise_control.gas_density_kg_m3(temperature_c=20.0)
    return numeric(expected, computed, 1e-9, unit="kg/m3", places=4)


@register(
    _IN_SITU,
    "ISO 11820:1996 Figure 1 and 9.1.3",
    "The twenty installations, sixteen for transmission and four for "
    "insertion, with the area rule each of them takes",
)
def _chk_iso11820_installation_cases() -> Outcome:
    matches = 0
    for number, case in INSTALLATION_CASES.items():
        wanted_quantity = "transmission" if number <= 16 else "insertion"  # noqa: PLR2004 - Figure 1 splits there
        if case.quantity != wanted_quantity:
            continue
        if number <= 4:  # noqa: PLR2004 - the clause groups cases 1 to 4
            ok = "measurement surface" in case.source_area_rule
        elif number <= 8:  # noqa: PLR2004 - and cases 5 to 8
            ok = "one-quarter" in case.source_area_rule
        elif number <= 16:  # noqa: PLR2004 - and cases 9 to 16
            ok = "one-half" in case.source_area_rule
        elif number <= 18:  # noqa: PLR2004 - 17 and 18 name their run
            ok = "without the silencer" in case.source_area_rule
        else:
            ok = "aperture" in case.source_area_rule and (
                "open end" in case.receiver_area_rule
            )
        matches += int(ok)
    return count(matches, len(INSTALLATION_CASES), subject="installations")


@register(
    _IN_SITU,
    "ISO 11820:1996 9.1.5",
    "The permitted conversion folds three one-third-octave levels into "
    "their octave on the energy, and is not the fold of a level difference",
)
def _chk_iso11820_octave_fold() -> Outcome:
    thirds = [30.0, 30.0, 5.0]
    permitted = float(ph.noise_control.octave_levels_from_third_octave_db(thirds)[0])
    expected = 10.0 * math.log10(sum(10.0 ** (0.1 * v) for v in thirds))
    forbidden = float(ph.noise_control.octave_insertion_loss(thirds)[0])
    agrees = abs(permitted - expected) < 1e-9 and abs(permitted - forbidden) > 1.0
    return count(
        int(agrees),
        1,
        subject="readings of 9.1.5",
        expected_label="the energy fold, distinct from the ISO 11691 one",
    )


# ---------------------------------------------------------------------------
# ISO 11820:1996, against printed numbers from outside the standard
# ---------------------------------------------------------------------------
# The rows above are the standard read against itself. These are the standard
# read against pages other people printed: the worked conversion of Annex B of
# ISO 14163, a 2014 measurement campaign that reduced three silencers to
# UNE-EN ISO 11820, and the textbook and guideline examples of the closed forms
# ISO 11820 shares with the rest of the field. Every number they compare
# against, with the document, the edition, the PDF page and the printed folio
# it was read on, is in ``tests/reference_data/silencer_in_situ.py``.

#: The carrier level the Barron background table is swept on, in decibels.
#: Equations (17) and (18) at one measuring point reduce to L_p less a
#: correction that depends on the margin alone, so the carrier cancels and any
#: value gives the same answer.
_CARRIER_DB = 90.0

#: ISO 11820 3.3 defines S as a quarter of the Sabine equivalent absorption
#: area A, which is why its Equations (6), (10) and (12) carry 6 ln 10 where
#: the two books below print 55,26 = 24 ln 10. The books print A, so a
#: comparison with them is against four times what this library returns.
_SABINE_QUARTERS = 4.0

#: Equation (15) as printed: the upstream measurement surface stands one and a
#: half equivalent diameters away. Re-typed here rather than imported from the
#: library, because the library's own constant is half of what the row is
#: checking and an oracle may not borrow it.
_PRINTED_UPSTREAM_DIAMETERS = 1.5

#: The two worked background subtractions, as (level, background, printed
#: result) in decibels.
_WORKED_SUBTRACTIONS = {
    "Bies 1.4, 92,0 dB over 88,0 dB": oracle.BIES_EXAMPLE_1_4_DB,
    "Barron 3-6, 83 dB over 77 dB": oracle.BARRON_EXAMPLE_3_6_DB,
}


def _folded_octave_level(third_octave_db: tuple[float, ...]) -> float:
    """One octave level out of its three one-third octaves, 9.1.5."""
    return float(
        ph.noise_control.octave_levels_from_third_octave_db(third_octave_db)[0]
    )


def _background_correction_db(margin_db: float) -> float:
    """What Equations (17) and (18) take off at a single measuring point."""
    with warnings.catch_warnings():
        # Barron tabulates margins down to 1 dB, where ISO 11820 caps the
        # correction at 3 dB and refuses to call the level determined. The cap
        # governs what may be reported; this row is about the arithmetic under
        # it, which the module returns uncapped either way.
        warnings.simplefilter("ignore", ph.noise_control.SilencerInSituWarning)
        corrected, _ = ph.noise_control.extraneous_corrected_mean_level_db(
            [_CARRIER_DB], [_CARRIER_DB - margin_db]
        )
    return _CARRIER_DB - corrected


def _holgado_insertion_loss(table: dict[float, oracle.HolgadoRow]) -> float:
    """The worst departure from one printed insertion-loss column, in decibels.

    The measurement is case 18 of Figure 1, a duct on the source side and a
    diffuse room on the receiver side, so both areas are a quarter of the room
    absorption and both move band by band with the reverberation time.
    :func:`in_situ_insertion_loss` takes its two areas as scalars, which is why
    this drives it one band at a time.
    """
    worst = 0.0
    for frequency, row in table.items():
        time_without, level_without, time_with, level_with, printed = row
        areas = ph.noise_control.reverberant_surface_area_m2(
            oracle.HOLGADO_ROOM_VOLUME_M3, [time_without, time_with]
        )
        result = ph.noise_control.in_situ_insertion_loss(
            [level_without],
            [level_with],
            area_without_m2=float(areas[0]),
            area_with_m2=float(areas[1]),
            frequencies=[frequency],
            field_correction_difference_db=0.0,
            case=18,
        )
        worst = max(worst, abs(float(result.loss_db[0]) - printed))
    return worst


def _sabine_absorption_m2(volume_m3: float, time_s: float, speed_m_s: float) -> float:
    """The Sabine absorption area the books print, four times our own."""
    area = ph.noise_control.reverberant_surface_area_m2(
        volume_m3, [time_s], speed_of_sound=speed_m_s
    )
    return _SABINE_QUARTERS * float(area[0])


@register(
    _IN_SITU,
    "ISO 11820:1996 9.1.5 / ISO 14163:1998 Table B.1, PDF page 47, folio 47",
    "The three spectra of the sister standard's worked conversion fold to the "
    "63 Hz octave levels it prints",
)
def _chk_iso14163_octave_levels() -> Outcome:
    worst = 0.0
    for name, sides in oracle.ISO14163_TABLE_B1_THIRD_OCTAVE_DB.items():
        printed = oracle.ISO14163_TABLE_B1_OCTAVE_DB[name]
        for side, want in zip(sides, printed, strict=True):
            worst = max(worst, abs(_folded_octave_level(side) - want))
    return numeric(
        0.0,
        worst,
        0.5,
        unit="dB",
        expected_label="six octave levels inside the half decibel the printed "
        "integers allow",
        computed_label=f"worst departure {worst:.3f} dB",
    )


@register(
    _IN_SITU,
    "ISO 11820:1996 9.1.5 / ISO 14163:1998 Table B.1, PDF page 47, folio 47",
    "The printed octave attenuation of each spectrum, which is the difference "
    "of the two folded levels and not the fold of the difference",
)
def _chk_iso14163_octave_attenuation() -> Outcome:
    # The three spectra share one one-third-octave attenuation, 3, 12 and
    # 21 dB, so the operation 9.1.5 forbids has nothing to vary with and
    # answers 7 dB for all three. Folding the levels on each side first and
    # subtracting afterwards, which is what the clause permits, gives 7, 12
    # and 5 dB. That gap is the whole reason the prohibition exists.
    computed = {}
    for name, sides in oracle.ISO14163_TABLE_B1_THIRD_OCTAVE_DB.items():
        source, attenuated = (round(_folded_octave_level(side)) for side in sides)
        computed[name] = float(source - attenuated)
    printed = dict(oracle.ISO14163_TABLE_B1_OCTAVE_ATTENUATION_DB)
    return record(printed, computed, unit="dB")


@register(
    _IN_SITU,
    "ISO 11820:1996 Eq. (2) / Holgado Palacios (2014) Tabla XL, PDF page 149, "
    "folio 121",
    "The energy mean of six microphone positions, over the twenty-one bands "
    "of a measured silencer test",
)
def _chk_holgado_mean_level() -> Outcome:
    worst = 0.0
    for positions, printed in oracle.HOLGADO_TABLE_XL.values():
        computed = ph.noise_control.mean_sound_pressure_level_db(positions)
        worst = max(worst, abs(computed - printed))
    return numeric(
        0.0,
        worst,
        0.05,
        unit="dB",
        expected_label="all 21 bands inside the 0,05 dB the printed tenth allows",
        computed_label=f"worst departure {worst:.3f} dB",
    )


@register(
    _IN_SITU,
    "ISO 11820:1996 Eq. (21) / Holgado Palacios (2014) Tablas LXIV to LXVI, "
    "PDF pages 173, 176 and 178, folios 145, 148 and 150",
    "The insertion loss of three silencers measured in place, sixty-three "
    "bands of the level difference and the area term",
)
def _chk_holgado_insertion_loss() -> Outcome:
    worst = max(
        _holgado_insertion_loss(table)
        for table in oracle.HOLGADO_INSERTION_TESTS.values()
    )
    # Not the 0,05 dB the printed tenth would suggest. The thesis computed
    # its insertion loss from unrounded position means and printed the inputs
    # rounded to 0,1 dB and 0,01 s, and that rounding alone reaches about
    # 0,13 dB. The three silencers are one campaign in one room, so this is
    # one oracle of sixty-three bands rather than three of twenty-one.
    return numeric(
        0.0,
        worst,
        0.15,
        unit="dB",
        expected_label="all 63 bands inside the rounding of the printed inputs",
        computed_label=f"worst departure {worst:.3f} dB",
    )


@register(
    _IN_SITU,
    "ISO 11820:1996 Eqs. (17) and (18) / Barron (2003) Table 3-4, PDF page 84, "
    "folio 72",
    "The energy subtraction at one measuring point, over the twenty-two "
    "printed margins from 1 dB to 20 dB",
)
def _chk_barron_background_table() -> Outcome:
    worst = max(
        abs(_background_correction_db(margin) - printed)
        for margin, printed in oracle.BARRON_TABLE_3_4_DB.items()
    )
    return numeric(
        0.0,
        worst,
        0.05,
        unit="dB",
        expected_label="all 22 rows inside the 0,05 dB the printed tenth allows",
        computed_label=f"worst departure {worst:.3f} dB",
    )


@register(
    _IN_SITU,
    "ISO 11820:1996 Eqs. (17) and (18) / Bies, Hansen and Howard (2017) "
    "Example 1.4, PDF page 65, folio 36, and Barron (2003) Example 3-6, "
    "PDF page 85, folio 73",
    "Two worked background subtractions at a single point, each printed to "
    "the tenth of a decibel",
)
def _chk_worked_background_subtractions() -> Outcome:
    printed = {name: values[2] for name, values in _WORKED_SUBTRACTIONS.items()}
    computed = {
        name: round(
            ph.noise_control.extraneous_corrected_mean_level_db(
                [values[0]], [values[1]]
            )[0],
            1,
        )
        for name, values in _WORKED_SUBTRACTIONS.items()
    }
    return record(printed, computed, unit="dB")


@register(
    _IN_SITU,
    "ISO 11820:1996 Eqs. (2) and (5) / Barron (2003) Example 3-4, "
    "PDF pages 77 and 78, folios 65 and 66",
    "The energy mean of nine levels on a measurement surface, and the "
    "10 lg (S/S0) of the 24,56 m2 that surface encloses",
)
def _chk_barron_mean_and_area_term() -> Outcome:
    mean_label = "mean of nine levels"
    area_label = "10 lg (S/S0) at 24,56 m2"
    printed = {
        mean_label: oracle.BARRON_EXAMPLE_3_4_MEAN_DB,
        area_label: oracle.BARRON_EXAMPLE_3_4_AREA_TERM_DB,
    }
    computed = {
        mean_label: round(
            ph.noise_control.mean_sound_pressure_level_db(
                oracle.BARRON_EXAMPLE_3_4_LEVELS_DB
            ),
            1,
        ),
        area_label: round(
            float(
                ph.noise_control.sound_power_level_db(
                    [0.0], area_m2=[oracle.BARRON_EXAMPLE_3_4_AREA_M2]
                )[0]
            ),
            2,
        ),
    }
    return record(printed, computed, unit="dB")


@register(
    _IN_SITU,
    "ISO 11820:1996 Eq. (5) / Barron (2003) Example 3-3, PDF pages 72 to 74, "
    "folios 60 to 62",
    "A sound power from a mean level, a measurement area and a field "
    "correction, all three terms together",
)
def _chk_barron_sound_power() -> Outcome:
    mean = ph.noise_control.mean_sound_pressure_level_db(
        oracle.BARRON_EXAMPLE_3_3_LEVELS_DB
    )
    # The third term of the book's Eq. (3-30) is the characteristic impedance
    # of the room air, -10 lg(rho c / 400), which is the K of Equation (5) for
    # this measurement. Dropping it leaves 90,5 dB and misses the printed
    # answer, so the row does exercise the term and not just the first two.
    correction = -10.0 * math.log10(oracle.BARRON_EXAMPLE_3_3_IMPEDANCE_RAYL / 400.0)
    level = float(
        ph.noise_control.sound_power_level_db(
            [mean],
            area_m2=[oracle.BARRON_EXAMPLE_3_3_AREA_M2],
            field_correction_db=[correction],
        )[0]
    )
    return numeric(
        oracle.BARRON_EXAMPLE_3_3_SOUND_POWER_DB, level, 0.05, unit="dB", places=2
    )


@register(
    _IN_SITU,
    "ISO 11820:1996 Eqs. (6), (10) and (12) / Ver and Beranek (2006) "
    "Example 4.2, PDF pages 95 and 96, folios 90 and 91",
    "A quarter of the printed Sabine absorption area of a 200 m3 room at "
    "21,4 C, where the speed of sound is 344 m/s",
)
def _chk_ver_beranek_absorption_area() -> Outcome:
    absorption = _sabine_absorption_m2(
        oracle.VER_BERANEK_EXAMPLE_4_2_VOLUME_M3,
        oracle.VER_BERANEK_EXAMPLE_4_2_REVERBERATION_TIME_S,
        oracle.VER_BERANEK_EXAMPLE_4_2_SPEED_M_S,
    )
    return numeric(
        oracle.VER_BERANEK_EXAMPLE_4_2_ABSORPTION_M2,
        absorption,
        0.05,
        unit="m2",
        places=4,
    )


@register(
    _IN_SITU,
    "ISO 11820:1996 Eq. (5) / Ver and Beranek (2006) Example 4.2, "
    "PDF page 96, folio 91",
    "The decibel term that absorption area becomes, printed as the first of "
    "the five the example adds",
)
def _chk_ver_beranek_area_term() -> Outcome:
    absorption = _sabine_absorption_m2(
        oracle.VER_BERANEK_EXAMPLE_4_2_VOLUME_M3,
        oracle.VER_BERANEK_EXAMPLE_4_2_REVERBERATION_TIME_S,
        oracle.VER_BERANEK_EXAMPLE_4_2_SPEED_M_S,
    )
    term = float(ph.noise_control.sound_power_level_db([0.0], area_m2=[absorption])[0])
    return numeric(
        oracle.VER_BERANEK_EXAMPLE_4_2_AREA_TERM_DB, term, 0.05, unit="dB", places=2
    )


@register(
    _IN_SITU,
    "ISO 11820:1996 Eqs. (6), (10) and (12) / Barron (2003) Example 7-2, "
    "PDF pages 297 to 299, folios 285 to 287",
    "The same area at another room and another speed of sound, against two "
    "absorption areas the example reaches by two unrelated routes",
)
def _chk_barron_absorption_area() -> Outcome:
    worst = max(
        abs(
            _sabine_absorption_m2(
                oracle.BARRON_EXAMPLE_7_2_VOLUME_M3,
                time_s,
                oracle.BARRON_EXAMPLE_7_2_SPEED_M_S,
            )
            - printed
        )
        for time_s, printed in oracle.BARRON_EXAMPLE_7_2_ABSORPTION_M2.items()
    )
    # The example prints its reverberation times to three figures and its
    # absorption areas to four, so the residual is the rounding of the time
    # rather than the arithmetic: 40,41 m2 needs T = 0,458 709 s, which is
    # what the printed 0,459 s rounds from.
    return numeric(
        0.0,
        worst,
        0.03,
        unit="m2",
        expected_label="both areas inside the rounding of the printed time",
        computed_label=f"worst departure {worst:.4f} m2",
    )


@register(
    _IN_SITU,
    "ISO 11820:1996 Eq. (29) / Barron (2003) Examples 8-11 and 8-10, "
    "PDF pages 399 and 392, folios 387 and 380",
    "The density of the air flowing through a muffler, at two temperatures "
    "and two ambient pressures away from the defaults",
)
def _chk_barron_gas_density() -> Outcome:
    printed = {
        name: values[2] for name, values in oracle.BARRON_MUFFLER_GAS_DENSITY.items()
    }
    computed = {
        name: round(
            ph.noise_control.gas_density_kg_m3(
                temperature_c=values[0], ambient_pressure_pa=values[1]
            ),
            3,
        )
        for name, values in oracle.BARRON_MUFFLER_GAS_DENSITY.items()
    }
    return record(printed, computed, unit="kg/m3")


@register(
    _IN_SITU,
    "ISO 11820:1996 Eq. (28) / INSHT NTP 668 (2004) Ec. 2 and Ec. 3, PDF pages 3 and 4",
    "The flow velocity a velocity pressure stands for, against the two "
    "coefficients a national guide prints for it",
)
def _chk_ntp668_flow_velocity() -> Outcome:
    printed = {
        name: values[1] for name, values in oracle.NTP668_VELOCITY_COEFFICIENTS.items()
    }
    computed = {
        name: round(
            float(
                ph.noise_control.flow_velocity_m_s(
                    [oracle.MILLIMETRE_WATER_COLUMN_PA], values[0]
                )[0]
            ),
            2,
        )
        for name, values in oracle.NTP668_VELOCITY_COEFFICIENTS.items()
    }
    return record(printed, computed, unit="m/s")


@register(
    _IN_SITU,
    "ISO 11820:1996 Eq. (31) / VDI 2081 Blatt 2:2005-05 Tabelle 1, "
    "PDF page 12, folio 12",
    "The mean velocity in the passages of a splitter silencer carrying "
    "16 000 m3/h, from the face velocity and the area ratio",
)
def _chk_vdi2081_gap_velocity() -> Outcome:
    face_velocity = (
        oracle.VDI2081_SPLITTER_VOLUME_FLOW_M3_H
        / 3600.0
        / oracle.VDI2081_SPLITTER_HOUSING_AREA_M2
    )
    velocity = ph.noise_control.silencer_flow_velocity_m_s(
        face_velocity,
        upstream_area_m2=oracle.VDI2081_SPLITTER_HOUSING_AREA_M2,
        free_area_m2=oracle.VDI2081_SPLITTER_FREE_AREA_M2,
    )
    # Driven from the volume flow rather than from the printed face velocity
    # of 4,94 m/s: that figure is itself rounded, and feeding it back gives
    # 14,82 m/s against the printed 14,81.
    return numeric(
        oracle.VDI2081_SPLITTER_GAP_VELOCITY_M_S,
        velocity,
        0.005,
        unit="m/s",
        places=3,
    )


@register(
    _IN_SITU,
    "ISO 11820:1996 Eq. (31) / Fuchs (2013) Table 13.4, PDF page 588, folio 574",
    "Twelve printed airway velocities of two splitter designs, at three flow "
    "rates and three housing cross-sections",
)
def _chk_fuchs_airway_velocity() -> Outcome:
    matching = 0
    total = 0
    ratios = tuple(oracle.FUCHS_BLOCKAGE_RATIOS.values())
    for flow_m3_h, housing_m2, *velocities in oracle.FUCHS_TABLE_13_4:
        for printed, ratio in zip(velocities, ratios, strict=True):
            total += 1
            free_m2 = housing_m2 / (1.0 + ratio)
            computed = ph.noise_control.silencer_flow_velocity_m_s(
                flow_m3_h / 3600.0 / housing_m2,
                upstream_area_m2=housing_m2,
                free_area_m2=free_m2,
            )
            # The table truncates towards zero rather than rounding, which is
            # visible where 66,67 m/s prints as 66 and 16,67 m/s as 16.
            matching += int(math.floor(computed) == printed)
    return count(matching, total, subject="printed airway velocities")


@register(
    _IN_SITU,
    "ISO 11820:1996 Eq. (15) / Barron (2003) Example 5-7, PDF page 215, folio 203",
    "The area-equivalent diameter inside the upstream distance, for the "
    "0,810 m2 cross-section of a 900 mm square duct",
)
def _chk_barron_equivalent_diameter() -> Outcome:
    distance = ph.noise_control.measurement_distance_upstream_m(
        oracle.BARRON_EXAMPLE_5_7_AREA_M2
    )
    # Half an oracle, and it says so: what Barron prints is the root
    # sqrt(4 S / pi) = 1,016 m, and the 1,5 diameters in front of it are
    # ISO 11820's own coefficient, read on the printed page of Equation (15)
    # and nowhere on his. The tolerance is what his four printed figures
    # propagate to: 1,016 m carries half a millimetre of rounding, and the
    # 1,5 of Equation (15) scales that to 0,75 mm. The printed area is the
    # exact 0,9 m squared, so it adds nothing.
    expected = (
        _PRINTED_UPSTREAM_DIAMETERS * oracle.BARRON_EXAMPLE_5_7_EQUIVALENT_DIAMETER_M
    )
    return numeric(
        expected,
        distance,
        _PRINTED_UPSTREAM_DIAMETERS * 0.0005,
        unit="m",
        places=5,
    )


@register(
    _IN_SITU,
    "ISO 11821:1997 5.7",
    "The background correction at the two ends of the 6 dB to 10 dB window",
)
def _chk_iso11821_background_window() -> Outcome:
    printed = {"margin 6 dB": 1.2563, "margin 10 dB": 0.4576}
    computed = {
        "margin 6 dB": 80.0
        - float(ph.noise_control.background_corrected_level_db([80.0], [74.0])[0]),
        "margin 10 dB": 80.0
        - float(ph.noise_control.background_corrected_level_db([80.0], [70.0])[0]),
    }
    worst = max(abs(printed[k] - computed[k]) for k in printed)
    return numeric(
        0.0,
        worst,
        5e-4,
        unit="dB",
        expected_label="1,2563 dB at 6 dB and 0,4576 dB at 10 dB",
        computed_label=(
            f"{computed['margin 6 dB']:.4f} dB and {computed['margin 10 dB']:.4f} dB"
        ),
    )


@register(
    _IN_SITU,
    "ISO 11821:1997 5.5.2",
    "The four microphone distances are a quarter, a half, once and twice "
    "the screen height, with a floor of 1 m",
)
def _chk_iso11821_microphone_distances() -> Outcome:
    printed = {"h/4": 2.0, "h/2": 4.0, "h": 8.0, "2h": 16.0}
    computed = dict(
        zip(printed, ph.noise_control.microphone_distances_m(8.0).tolist(), strict=True)
    )
    return record(printed, computed, unit="m")


@register(
    _IN_SITU,
    "ISO 11821:1997 3.10 and 5.2.2",
    "The directivity index is the logarithmic mean of twelve positions less "
    "the position, so a position under the mean reads positive",
)
def _chk_iso11821_directivity_index() -> Outcome:
    levels = np.full(12, 80.0)
    levels[0] = 70.0
    index = ph.noise_control.directivity_index_db(levels)
    mean = 10.0 * math.log10((11.0 * 10.0**8.0 + 10.0**7.0) / 12.0)
    expected = mean - 70.0
    return numeric(expected, float(index[0]), 1e-9, unit="dB")


@register(
    _IN_SITU,
    "ISO 11821:1997 5.6.2.1 and clause 6",
    "The impulse repeat rules and the one uncertainty number the document prints",
)
def _chk_iso11821_thresholds() -> Outcome:
    printed = {"repeats": 3.0, "repeat again": 3.0, "invalid": 5.0, "deviation": 2.0}
    computed = {
        "repeats": float(ph.noise_control.IMPULSE_REPEATS),
        "repeat again": ph.noise_control.IMPULSE_REPEAT_DEVIATION_DB,
        "invalid": ph.noise_control.IMPULSE_INVALID_DEVIATION_DB,
        "deviation": ph.noise_control.ENGINEERING_STANDARD_DEVIATION_DB,
    }
    return record(printed, computed)


# ---------------------------------------------------------------------------
# ISO 11821: the level pairs the standard does not print itself
# ---------------------------------------------------------------------------

#: Barron (2003) Table 7-6 on folio 316: the octave band centres of Example
#: 7-9, in hertz, and the two rows printed under them, in decibels, without
#: the barrier and with it.
_BARRON_BANDS_HZ = (63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0)
_BARRON_UNSCREENED_DB = (71.6, 75.6, 69.6, 65.6, 65.6, 59.6, 54.6, 48.6)
_BARRON_SCREENED_DB = (64.0, 66.3, 57.9, 51.2, 48.2, 39.2, 31.2, 24.4)

#: Folio 317: the only two band reductions the example works out in prose,
#: in decibels. The other six follow from the two rows above by subtraction
#: and are nowhere on the page, so they are not claimed as printed.
_BARRON_PRINTED_REDUCTIONS_DB = {"63 Hz": 7.6, "8000 Hz": 24.2}

#: Folios 315 and 317: the A-weighted pair, in decibels, and the reduction
#: printed between them.
_BARRON_A_WEIGHTED_DB = (69.6, 55.3)
_BARRON_PRINTED_A_REDUCTION_DB = 14.3

#: Folio 314: the receiver stands 30 m from the transformer and the barrier
#: 10 m from it, so the position is this far from the barrier, in metres.
_BARRON_SCREEN_DISTANCE_M = 20.0

#: Barron (2003) Table 3-4 on folio 72, the rows that fall inside the 6 dB to
#: 10 dB window of ISO 11821 5.7: the margin and the correction to subtract,
#: both in decibels. The rows under 6 dB are outside the clause, which calls
#: the environmental conditions unacceptable there rather than correcting.
_BARRON_TABLE_3_4_DB = (
    (6.0, 1.3),
    (6.5, 1.1),
    (7.0, 1.0),
    (7.5, 0.9),
    (8.0, 0.7),
    (9.0, 0.6),
    (10.0, 0.5),
)

#: Barron (2003) Table 3-2 on folio 61: the ten levels measured around a motor
#: in a semi-anechoic room, in decibels, positions 2 to 4 being the ring at
#: 41.4 degrees from the vertical.
_BARRON_MOTOR_LEVELS_DB = (
    86.0,
    81.5,
    82.4,
    81.3,
    70.9,
    72.9,
    68.0,
    79.3,
    78.5,
    80.1,
)

#: IFA-LSA 01-234 (2020) Tab. 4.4 on folio 17: the levels measured at the four
#: positions of the worked example, in decibels, by octave band centre in
#: hertz, from the nearest position outwards.
_IFA_LEVELS_DB = {
    500: (79.2, 74.4, 70.2, 67.1),
    1000: (81.9, 77.1, 73.0, 69.8),
    2000: (80.4, 75.3, 71.0, 67.4),
    4000: (84.3, 78.5, 73.2, 69.3),
}

#: Tab. 4.5 on folio 18: the difference printed between each pair of
#: neighbouring positions, in decibels, in the same band order.
_IFA_PRINTED_DIFFERENCES_DB = {
    "Lp1 - Lp2": (4.8, 4.8, 5.1, 5.8),
    "Lp2 - Lp3": (4.2, 4.1, 4.7, 5.3),
    "Lp3 - Lp4": (3.1, 3.2, 3.6, 3.9),
}

#: The one cell of Tab. 4.5 that its own Tab. 4.4 does not support: 75,3 dB
#: less 71,0 dB is 4,3 dB and the table prints 4,7 dB. It is left out of the
#: tally rather than papered over, and the 4,3 dB is pinned in the test suite.
_IFA_MISPRINT = ("Lp2 - Lp3", 2000)


@register(
    _IN_SITU,
    "ISO 11821:1997 5.8 / Barron (2003) Table 7-6, PDF page 328, folio 316",
    "D_p from a printed level pair, at the two octave bands the worked "
    "example prints a reduction for",
)
def _chk_iso11821_printed_band_pair() -> Outcome:
    result = ph.noise_control.screen_attenuation(
        _BARRON_UNSCREENED_DB,
        _BARRON_SCREENED_DB,
        frequencies=_BARRON_BANDS_HZ,
        source_kind="actual",
        distance_m=_BARRON_SCREEN_DISTANCE_M,
    )
    computed = {
        "63 Hz": float(result.attenuation_db[0]),
        "8000 Hz": float(result.attenuation_db[-1]),
    }
    worst = max(
        abs(_BARRON_PRINTED_REDUCTIONS_DB[key] - computed[key]) for key in computed
    )
    return numeric(
        0.0,
        worst,
        1e-12,
        unit="dB",
        expected_label="7.6 dB at 63 Hz and 24.2 dB at 8000 Hz",
        computed_label=(f"{computed['63 Hz']:.1f} dB and {computed['8000 Hz']:.1f} dB"),
    )


@register(
    _IN_SITU,
    "ISO 11821:1997 5.9 / Barron (2003) Example 7-9, PDF pages 327 and 329, "
    "folios 315 and 317",
    "D_pA from the printed A-weighted pair, 69.6 dBA without the barrier and "
    "55.3 dBA with it",
)
def _chk_iso11821_printed_a_weighted_pair() -> Outcome:
    result = ph.noise_control.screen_attenuation(
        _BARRON_UNSCREENED_DB,
        _BARRON_SCREENED_DB,
        frequencies=_BARRON_BANDS_HZ,
        source_kind="actual",
        a_weighted_unscreened_level_db=_BARRON_A_WEIGHTED_DB[0],
        a_weighted_screened_level_db=_BARRON_A_WEIGHTED_DB[1],
        distance_m=_BARRON_SCREEN_DISTANCE_M,
    )
    weighted = result.a_weighted_attenuation_db
    computed = math.nan if weighted is None else float(weighted)
    return numeric(
        _BARRON_PRINTED_A_REDUCTION_DB, computed, 1e-12, unit="dBA", places=1
    )


@register(
    _IN_SITU,
    "ISO 11821:1997 5.8 / Barron (2003) Example 7-10, PDF pages 331 to 333, "
    "folios 319 to 321",
    "D_p for a screen standing indoors: 92.3 dB falls to 84.0 dB in the "
    "1000 Hz octave at the operator position",
)
def _chk_iso11821_indoor_screen_pair() -> Outcome:
    # The barrier stands 1,00 m from the machine and the operator 3,00 m from
    # it, so the position is 2 m from the screen. Both levels are Barron's own
    # prediction, which is why this anchors the subtraction and not a method.
    result = ph.noise_control.screen_attenuation(
        [92.3],
        [84.0],
        frequencies=[1000.0],
        source_kind="actual",
        distance_m=2.0,
    )
    return numeric(8.3, float(result.attenuation_db[0]), 1e-12, unit="dB", places=1)


@register(
    _IN_SITU,
    "ISO 11821:1997 5.8 / Hansen (2005) Example 6.23, PDF pages 325 and 326, "
    "folios 317 and 318",
    "D_p over three octave bands, rounded to the whole decibel 7.4 c) reports it in",
)
def _chk_iso11821_printed_rounded_reductions() -> Outcome:
    result = ph.noise_control.screen_attenuation(
        [48.8, 55.1, 52.9],
        [39.0, 39.9, 33.3],
        frequencies=[500.0, 1000.0, 2000.0],
        distance_m=2.0,
    )
    printed = {"500 Hz": 10.0, "1000 Hz": 15.0, "2000 Hz": 20.0}
    # 7.4 c) asks for the nearest integer and the library returns the raw
    # difference, 9,8 / 15,2 / 19,6 dB, so the rounding is done here.
    computed = dict(zip(printed, np.round(result.attenuation_db).tolist(), strict=True))
    return record(printed, computed, unit="dB")


@register(
    _IN_SITU,
    "ISO 11821:1997 5.8 / Noise Control in Industry 3e (1991), PDF page 188, folio 177",
    "D_p from the 80 dB / 71 dB pair the worked example prints, and from the "
    "three single-path levels printed beside it",
)
def _chk_iso11821_path_level_pair() -> Outcome:
    # The 71 dB is the book's own decibel-addition rule of thumb rather than
    # the energy sum of the three paths, which is 71,687 dB and would make the
    # reduction 8,3 dB. The pair is used exactly as printed.
    printed = {"screen": 9.0, "path 1": 15.0, "path 2": 10.0, "path 3": 18.0}
    result = ph.noise_control.screen_attenuation(
        [80.0, 80.0, 80.0, 80.0], [71.0, 65.0, 70.0, 62.0]
    )
    computed = dict(zip(printed, result.attenuation_db.tolist(), strict=True))
    return record(printed, computed, unit="dB")


@register(
    _IN_SITU,
    "ISO 11821:1997 5.8 / IFA-LSA 01-234 (2020) Tab. 4.5, PDF page 18, folio 18",
    "The differences printed between neighbouring positions, band by band, "
    "less the one cell the document misprints",
)
def _chk_iso11821_ifa_printed_differences() -> Outcome:
    bands = tuple(_IFA_LEVELS_DB)
    matching, total = 0, 0
    for step, (row, printed) in enumerate(_IFA_PRINTED_DIFFERENCES_DB.items()):
        result = ph.noise_control.screen_attenuation(
            [_IFA_LEVELS_DB[band][step] for band in bands],
            [_IFA_LEVELS_DB[band][step + 1] for band in bands],
            frequencies=[float(band) for band in bands],
            # A test sound source, so 5.9 forbids the A-weighted difference.
            source_kind="artificial",
        )
        values = result.attenuation_db.tolist()
        for band, published, value in zip(bands, printed, values, strict=True):
            if (row, band) == _IFA_MISPRINT:
                continue
            total += 1
            matching += int(round(float(value), 1) == published)
    return count(matching, total, subject="cells of Tab. 4.5")


@register(
    _IN_SITU,
    "ISO 11821:1997 5.7 / Barron (2003) Example 3-6, PDF page 85, folio 73",
    "The corrected level at the lower edge of the window: 83 dB measured over "
    "a 77 dB background",
)
def _chk_iso11821_background_worked_example() -> Outcome:
    corrected = ph.noise_control.background_corrected_level_db([83.0], [77.0])
    return numeric(81.7, float(corrected[0]), 0.05, unit="dB", places=4)


@register(
    _IN_SITU,
    "ISO 11821:1997 5.7 / Barron (2003) Table 3-4, PDF page 84, folio 72",
    "The seven rows of the printed correction table that fall inside the 6 dB "
    "to 10 dB window, to the 0.1 dB the table prints",
)
def _chk_iso11821_background_printed_table() -> Outcome:
    printed = {f"{margin:g} dB": value for margin, value in _BARRON_TABLE_3_4_DB}
    computed: dict[str, float] = {}
    for margin, _ in _BARRON_TABLE_3_4_DB:
        level = 83.0
        corrected = ph.noise_control.background_corrected_level_db(
            [level], [level - margin]
        )
        computed[f"{margin:g} dB"] = round(level - float(corrected[0]), 1)
    return record(printed, computed, unit="dB")


@register(
    _IN_SITU,
    "ISO 11821:1997 5.7 / Hansen (2005) Example 3.25, PDF pages 154 and 155, "
    "folios 146 and 147",
    "The corrected level at a margin of exactly 10 dB, the upper edge of the "
    "window, and at a 6.6 dB one",
)
def _chk_iso11821_background_at_the_upper_edge() -> Outcome:
    corrected = ph.noise_control.background_corrected_level_db(
        [90.0, 86.6], [80.0, 80.0]
    )
    printed = (89.5, 85.5)
    worst = max(
        abs(value - float(level))
        for value, level in zip(printed, corrected, strict=True)
    )
    return numeric(
        0.0,
        worst,
        0.05,
        unit="dB",
        expected_label="89.5 dB at a 10 dB margin and 85.5 dB at a 6.6 dB one",
        computed_label=f"{corrected[0]:.3f} dB and {corrected[1]:.3f} dB",
    )


@register(
    _IN_SITU,
    "ISO 11821:1997 5.7 / ISO 140-3:1995 6.5, PDF page 13, folio 7",
    "The 1,3 dB that ISO 140-3 and ISO 3744:2010 8.2.3 both print for a 6 dB "
    "margin, which is where the window of 5.7 opens",
)
def _chk_iso11821_background_sibling_value() -> Outcome:
    # Neither sibling reads the margin the way 5.7 does: both apply 1,3 dB as
    # a floor below 6 dB, where ISO 11821 refuses the measurement instead. The
    # value is borrowed for the boundary, not the rule around it.
    corrected = ph.noise_control.background_corrected_level_db([70.0], [64.0])
    return numeric(1.3, 70.0 - float(corrected[0]), 0.05, unit="dB", places=4)


@register(
    _IN_SITU,
    "ISO 11821:1997 3.10 / Barron (2003) Example 3-5, PDF pages 80 and 81, "
    "folios 68 and 69",
    "The logarithmic mean under the directivity index: 80.6 dB over ten "
    "printed levels and 81.8 dB over three of them",
)
def _chk_iso11821_directivity_mean() -> Outcome:
    # Ten positions on a hemisphere, where 3.10 reads twelve on a horizontal
    # circle, so directivity_index_db refuses this set as printed. What the
    # mean itself is worth is checked through the entry point that publishes
    # it, which shares the helper the directivity index calls.
    printed = {"ten positions": 80.6, "ring of three": 81.8}
    computed = {
        "ten positions": float(
            ph.building.energy_average_level(_BARRON_MOTOR_LEVELS_DB)
        ),
        "ring of three": float(
            ph.building.energy_average_level(_BARRON_MOTOR_LEVELS_DB[1:4])
        ),
    }
    worst = max(abs(printed[k] - computed[k]) for k in printed)
    return numeric(
        0.0,
        worst,
        0.05,
        unit="dB",
        expected_label="80.6 dB over ten positions and 81.8 dB over the ring",
        computed_label=(
            f"{computed['ten positions']:.4f} dB and {computed['ring of three']:.4f} dB"
        ),
    )


@register(
    _IN_SITU,
    "ISO 10847:1997 Table 3",
    "The background correction to add, over the two printed rows",
)
def _chk_iso10847_table_three() -> Outcome:
    printed = {
        "4 dB": -2.0,
        "5 dB": -2.0,
        "6 dB": -1.0,
        "7 dB": -1.0,
        "8 dB": -1.0,
        "9 dB": -1.0,
    }
    computed = {
        f"{margin} dB": float(
            ph.environment.barrier_background_correction_db([float(margin)])[0]
        )
        for margin in ISO10847_BACKGROUND_CORRECTIONS_DB
    }
    return record(printed, computed, unit="dB")


@register(
    _IN_SITU,
    "ISO 11820:1996 Table 1 / ISO 10847:1997 Table 3",
    "The two stepped tables disagree at a 9 dB margin, so they are two "
    "tables and not one helper",
)
def _chk_two_background_tables() -> Outcome:
    silencer = float(ph.noise_control.silencer_background_correction_db([9.0])[0])
    barrier = float(ph.environment.barrier_background_correction_db([9.0])[0])
    printed = {"ISO 11820 subtracts": 0.5, "ISO 10847 adds": -1.0}
    computed = {"ISO 11820 subtracts": silencer, "ISO 10847 adds": barrier}
    return record(printed, computed, unit="dB")


@register(
    _IN_SITU,
    "ISO 10847:1997 8.2.1 and 8.2.2",
    "The indirect method returns exactly what the direct one returns when "
    "the receiver is of the same kind in both campaigns",
)
def _chk_iso10847_methods_agree() -> Outcome:
    reference_before = np.array([70.0, 72.0, 74.0, 73.0, 70.0, 66.0])
    reference_after = reference_before + 1.5
    receiver_before = np.array([60.0, 62.0, 63.0, 62.0, 59.0, 55.0])
    receiver_after = receiver_before - np.array([3.0, 5.0, 8.0, 11.0, 14.0, 16.0]) + 1.5
    direct = ph.environment.measured_insertion_loss_direct(
        reference_before, reference_after, receiver_before, receiver_after
    )
    worst = 0.0
    kinds: tuple[ReceiverType, ...] = ("hemi_free_field", "reflecting_surface")
    for kind in kinds:
        indirect = ph.environment.measured_insertion_loss_indirect(
            reference_before,
            reference_after,
            receiver_before,
            receiver_after,
            receiver_type_before=kind,
            receiver_type_after=kind,
        )
        worst = max(
            worst,
            float(
                np.max(np.abs(indirect.insertion_loss_db - direct.insertion_loss_db))
            ),
        )
    return numeric(
        0.0,
        worst,
        1e-12,
        unit="dB",
        computed_label=f"max absolute difference {worst:.3f} dB over both receiver kinds",
    )


@register(
    _IN_SITU,
    "ISO 10847:1997 8.2.2",
    "Mixing a hemi-free-field receiver with a facade one moves the answer "
    "by exactly the 6 dB of the pressure doubling",
)
def _chk_iso10847_receiver_correction() -> Outcome:
    reference_before = np.array([70.0, 72.0, 74.0])
    reference_after = reference_before
    receiver_before = np.array([60.0, 62.0, 63.0])
    receiver_after = receiver_before - 10.0
    direct = ph.environment.measured_insertion_loss_direct(
        reference_before, reference_after, receiver_before, receiver_after
    )
    mixed = ph.environment.measured_insertion_loss_indirect(
        reference_before,
        reference_after,
        receiver_before,
        receiver_after,
        receiver_type_after="reflecting_surface",
    )
    shift = float(np.max(mixed.insertion_loss_db - direct.insertion_loss_db))
    return numeric(
        RECEIVER_CORRECTIONS_DB["reflecting_surface"], shift, 1e-12, unit="dB"
    )


@register(
    _IN_SITU,
    "ISO 10847:1997 8.2.1",
    "A source that changed output between the two campaigns is normalised "
    "away by the reference position",
)
def _chk_iso10847_source_normalisation() -> Outcome:
    reference_before = np.array([70.0, 72.0, 74.0])
    receiver_before = np.array([60.0, 62.0, 63.0])
    attenuation = np.array([5.0, 8.0, 11.0])
    plain = ph.environment.measured_insertion_loss_direct(
        reference_before,
        reference_before,
        receiver_before,
        receiver_before - attenuation,
    )
    louder = ph.environment.measured_insertion_loss_direct(
        reference_before,
        reference_before + 4.0,
        receiver_before,
        receiver_before - attenuation + 4.0,
    )
    worst = float(np.max(np.abs(plain.insertion_loss_db - louder.insertion_loss_db)))
    return numeric(
        0.0,
        worst,
        1e-12,
        unit="dB",
        computed_label=f"max absolute difference {worst:.3f} dB for a 4 dB source gain",
    )


@register(
    _IN_SITU,
    "ISO 10847:1997 Table 1",
    "The wind classes, with the upwind one existing only over short "
    "distances and read as negative",
)
def _chk_iso10847_wind_classes() -> Outcome:
    readings = {
        "+3 m/s": ph.environment.wind_class(3.0),
        "0 m/s": ph.environment.wind_class(0.0),
        "-3 m/s, long": ph.environment.wind_class(-3.0),
        "-3 m/s, short": ph.environment.wind_class(-3.0, short_distance=True),
    }
    printed = {
        "+3 m/s": "downwind",
        "0 m/s": "calm",
        "-3 m/s, long": None,
        "-3 m/s, short": "upwind",
    }
    matching = sum(1 for key in printed if readings[key] == printed[key])
    return count(matching, len(printed), subject="readings of Table 1")


@register(
    _IN_SITU,
    "ISO 10847:1997 6.3.1",
    "The short-distance ratio is strict at 0,1, and the after case needs "
    "both of its two inequalities",
)
def _chk_iso10847_short_distance() -> Outcome:
    at_the_ratio, _ = ph.environment.is_short_distance(
        source_height_m=1.0,
        receiver_height_m=1.0,
        barrier_height_m=4.0,
        source_to_barrier_m=10.0,
        barrier_to_receiver_m=10.0,
    )
    _, one_half_fails = ph.environment.is_short_distance(
        source_height_m=1.0,
        receiver_height_m=1.0,
        barrier_height_m=1.0,
        source_to_barrier_m=10.0,
        barrier_to_receiver_m=100.0,
    )
    agrees = at_the_ratio is False and one_half_fails is False
    return count(
        int(agrees),
        1,
        subject="readings of 6.3.1",
        expected_label="0,1 exactly is not short, and both halves must hold",
    )


@register(
    _IN_SITU,
    "ISO 10847:1997 7.2.2 and 8.1.2 a)",
    "The reference microphone clears the barrier top by 1,5 m, or takes the "
    "10 degree rule for a source under 15 m away",
)
def _chk_iso10847_geometry() -> Outcome:
    # What 7.2.2 and 8.1.2 a) print is a clearance of 1,5 m, an increment of
    # 10 degrees, a threshold of 15 m and a limit of 30 m or twice the
    # barrier-to-receiver distance. No distance and no resulting height is
    # printed with them, so these four are the printed rules applied at
    # geometries this row chose, not values read off a page. The 10 degree
    # entry pins which branch fires at 10 m; what the increment means is a
    # separate row, because restating the formula here would prove nothing.
    close = 10.0 * math.tan(math.atan(4.0 / 10.0) + math.radians(10.0))
    from_the_printed_rules = {
        "clearance": 5.5,
        "10 degree rule": close,
        "hemi free field at 5 m": 10.0,
        "hemi free field at 20 m": 30.0,
    }
    computed = {
        "clearance": ph.environment.reference_microphone_height_m(4.0),
        "10 degree rule": ph.environment.reference_microphone_height_m(
            4.0, source_to_barrier_m=10.0
        ),
        "hemi free field at 5 m": ph.environment.hemi_free_field_distance_m(5.0),
        "hemi free field at 20 m": ph.environment.hemi_free_field_distance_m(20.0),
    }
    worst = max(
        abs(from_the_printed_rules[k] - computed[k]) for k in from_the_printed_rules
    )
    return numeric(0.0, worst, 1e-9, unit="m")


@register(
    _IN_SITU,
    "ISO 10847:1997 3.10",
    "The far field falls 6 dB per doubling for a point source and 3 dB for "
    "an incoherent line source",
)
def _chk_iso10847_divergence() -> Outcome:
    printed = {"point": 20.0 * math.log10(2.0), "line": 10.0 * math.log10(2.0)}
    computed = {
        "point": ph.environment.POINT_SOURCE_DIVERGENCE_DB,
        "line": ph.environment.LINE_SOURCE_DIVERGENCE_DB,
    }
    worst = max(abs(printed[k] - computed[k]) for k in printed)
    return numeric(
        0.0,
        worst,
        0.021,
        unit="dB",
        expected_label="6,02 dB and 3,01 dB, printed rounded to 6 and 3",
        computed_label="6 dB and 3 dB",
    )


# The campaigns below are other people's, and every number in them was read off
# the printed page. They are what ISO 10847 does not carry: four measured levels
# and the insertion loss those four levels give. Each row says which part of
# clause 8.2 its numbers reach, because agreeing with the subtraction says
# nothing about the wind classes, the background table or the receiver
# correction.

#: Half the last digit these campaigns print. They report to 0,1 dB, so a
#: value that agrees to better than this agrees to everything the page states.
_PRINTED_TENTH_DB = 0.05

#: Cordero and others (2010), Tabla 1 "Niveles equivalentes de los puntos de
#: evaluacion", printed folio 5 (PDF page 5): the four A-weighted levels of
#: each case, in the argument order of ``measured_insertion_loss_direct``, that
#: is (L_ref,B, L_ref,A, L_r,B, L_r,A). "Antes" is the window open and
#: "despues" the window closed, so the two roles of 8.2.1 are filled by a
#: window rather than by a barrier: what these numbers anchor is the
#: subtraction and the reporting rule, not the procedure. The second case is
#: the same campaign with the background deliberately raised at the
#: measurement point alone.
_CORDERO_LEVELS_DBA: dict[str, tuple[float, float, float, float]] = {
    "sin ruido": (61.0, 64.3, 55.6, 46.1),
    "con ruido": (61.2, 63.7, 56.0, 49.0),
}


def _cordero(case: str) -> tuple[float, int]:
    """One printed case of that campaign, before and after the rounding."""
    reference_before, reference_after, receiver_before, receiver_after = (
        _CORDERO_LEVELS_DBA[case]
    )
    result = ph.environment.measured_insertion_loss_direct(
        [reference_before], [reference_after], [receiver_before], [receiver_after]
    )
    return float(result.insertion_loss_db[0]), int(result.rounded()[0])


@register(
    _IN_SITU,
    "Cordero et al. (2010) Tablas 1 and 2, printed folios 5 and 6 (PDF pages 5 and 6)",
    "A campaign that prints all four levels: the two insertion losses it "
    "reports to the nearest decibel, 13 dBA and 10 dBA",
)
def _chk_cordero_reported_insertion_loss() -> Outcome:
    computed = {case: float(_cordero(case)[1]) for case in _CORDERO_LEVELS_DBA}
    return record({"sin ruido": 13.0, "con ruido": 10.0}, computed, unit="dBA")


@register(
    _IN_SITU,
    "Cordero et al. (2010) Tablas 1 and 2, printed folios 5 and 6 (PDF pages 5 and 6)",
    "The one value that campaign prints before rounding, 9,5 dBA, for the "
    "case with the background raised at the receiver alone",
)
def _chk_cordero_before_rounding() -> Outcome:
    return numeric(9.5, _cordero("con ruido")[0], _PRINTED_TENTH_DB, unit="dBA")


#: Lindeman (1985) TABLE 8 "Calculations for Insertion Loss Based on Direct
#: Method Test at Site 1", printed folio 39 (PDF page 7): the runs whose four
#: levels are all printed, in the same argument order, in dBA. Runs 4 and 5
#: print no "before" reference level and no insertion loss. Run 1 is left out
#: of this row: column (7) prints 6,2 dB where its own four levels give
#: 5,8 dB, and TABLES 4 and 5 on folio 37 reach those same two levels a second
#: time through their own arithmetic, so what is defective is the printed
#: insertion loss and not a level. The note's mean, 7,5 dBA, is the mean of
#: the defective column and is left out with it.
_LINDEMAN_DIRECT_DBA: dict[str, tuple[float, float, float, float]] = {
    "run 2": (64.5, 67.1, 58.5, 53.6),
    "run 3": (63.1, 65.5, 57.3, 51.0),
}

#: TABLE 8 column (7), "Insertion Loss", for those two runs.
_LINDEMAN_DIRECT_PRINTED_DBA: dict[str, float] = {"run 2": 7.5, "run 3": 8.7}


@register(
    _IN_SITU,
    "Lindeman (1985) Table 8, printed folio 39 (PDF page 7)",
    "A barrier measured before it stood and after, by the direct method: the "
    "runs whose four levels are printed give the printed insertion loss",
)
def _chk_lindeman_direct() -> Outcome:
    matching = 0
    worst = 0.0
    for run, levels in _LINDEMAN_DIRECT_DBA.items():
        reference_before, reference_after, receiver_before, receiver_after = levels
        computed = float(
            ph.environment.measured_insertion_loss_direct(
                [reference_before],
                [reference_after],
                [receiver_before],
                [receiver_after],
            ).insertion_loss_db[0]
        )
        departure = abs(computed - _LINDEMAN_DIRECT_PRINTED_DBA[run])
        matching += int(departure <= _PRINTED_TENTH_DB)
        worst = max(worst, departure)
    return count(
        matching,
        len(_LINDEMAN_DIRECT_DBA),
        subject="runs within the 0,1 dB the table prints to",
        expected_label=f"2/2 (worst departure {worst:.3f} dBA)",
    )


#: Lindeman (1985) TABLE 13 "Calculations Based on Indirect Measured Method",
#: printed folio 41 (PDF page 9): five runs, with the equivalent site as the
#: "before" pair (MIC 3 the reference, MIC 4 the receiver) and the barrier
#: site as the "after" one (MIC 1 and MIC 2), all in dBA. Run 4 takes its
#: "before" receiver level from TABLE 12 on the same folio, which prints 61,1
#: where column (2) of TABLE 13 repeats run 3's 60,2. The table contradicts
#: itself there rather than leaving the choice open: its own column (3) prints
#: 7,7 for that run, and 68,8 - 60,2 is 8,6. Both receivers stand in the open,
#: so C_r and C'_r are zero and this exercises the site pairing of 8.2.2
#: rather than the facade branch.
_LINDEMAN_INDIRECT_DBA: dict[str, list[float]] = {
    "reference before": [66.7, 72.2, 66.1, 68.8, 67.4],
    "reference after": [65.4, 67.1, 65.5, 65.9, 66.9],
    "receiver before": [61.2, 65.3, 60.2, 61.1, 62.4],
    "receiver after": [53.0, 53.6, 51.0, 54.6, 52.7],
}

#: TABLE 13 column (7) run by run, and the mean its note reports.
_LINDEMAN_INDIRECT_PRINTED_DBA = (6.9, 6.6, 8.6, 3.6, 9.2)
_LINDEMAN_INDIRECT_MEAN_DBA = 7.0


@register(
    _IN_SITU,
    "Lindeman (1985) Tables 12 and 13, printed folio 41 (PDF page 9)",
    "The same barrier by the indirect method, five runs against an equivalent "
    "site, and the mean insertion loss of 7,0 dBA the table reports",
)
def _chk_lindeman_indirect() -> Outcome:
    result = ph.environment.measured_insertion_loss_indirect(
        _LINDEMAN_INDIRECT_DBA["reference before"],
        _LINDEMAN_INDIRECT_DBA["reference after"],
        _LINDEMAN_INDIRECT_DBA["receiver before"],
        _LINDEMAN_INDIRECT_DBA["receiver after"],
    )
    departures = np.abs(
        result.insertion_loss_db - np.array(_LINDEMAN_INDIRECT_PRINTED_DBA)
    )
    mean = abs(float(np.mean(result.insertion_loss_db)) - _LINDEMAN_INDIRECT_MEAN_DBA)
    matching = int(np.count_nonzero(departures <= _PRINTED_TENTH_DB)) + int(
        mean <= _PRINTED_TENTH_DB
    )
    worst = max(float(np.max(departures)), mean)
    return count(
        matching,
        len(_LINDEMAN_INDIRECT_PRINTED_DBA) + 1,
        subject="printed values, the five runs and their mean",
        expected_label=f"6/6 (worst departure {worst:.3f} dBA)",
    )


#: FHWA-PD-96-046 clause 6.6.3 "Insertion Loss", printed folio 84 (PDF page
#: 101), and the same example again in FHWA-HEP-18-065 on printed folios 108
#: and 109: the levels its worked example lists, in decibels. L_edge is an
#: FHWA reflections and edge-diffraction adjustment defined in clause 6.6.2,
#: with no counterpart anywhere in ISO 10847, so it is applied outside the
#: function under test rather than fed to it. The example contradicts itself,
#: and that is the whole of the difference between its two published answers:
#: the list gives a receiver level of 56,3 dB, the expression under it types
#: 56,2 dB, and the FHWA Noise Barrier Design Handbook prints 8,7 dB for the
#: first where these two manuals print 8,8 dB for the second.
_FHWA_REFERENCE_BEFORE_DB = 77.7
_FHWA_REFERENCE_AFTER_DB = 78.2
_FHWA_RECEIVER_BEFORE_DB = 65.0
_FHWA_EDGE_DB = -0.5
_FHWA_PRINTED_DB: dict[str, tuple[float, float]] = {
    "as the expression types it": (56.2, 8.8),
    "as the list gives it": (56.3, 8.7),
}


@register(
    _IN_SITU,
    "FHWA-PD-96-046 clause 6.6.3, printed folio 84 (PDF page 101)",
    "The insertion loss worked through with every level printed, 8,8 dB and "
    "8,7 dB, once the off-model edge adjustment is applied outside",
)
def _chk_fhwa_worked_example() -> Outcome:
    worst = 0.0
    for receiver_after, printed in _FHWA_PRINTED_DB.values():
        computed = (
            float(
                ph.environment.measured_insertion_loss_direct(
                    [_FHWA_REFERENCE_BEFORE_DB],
                    [_FHWA_REFERENCE_AFTER_DB],
                    [_FHWA_RECEIVER_BEFORE_DB],
                    [receiver_after],
                ).insertion_loss_db[0]
            )
            + _FHWA_EDGE_DB
        )
        worst = max(worst, abs(computed - printed))
    return numeric(
        0.0,
        worst,
        _PRINTED_TENTH_DB,
        unit="dB",
        expected_label="8,8 dB from the 56,2 dB typed, 8,7 dB from the 56,3 dB listed",
        computed_label=f"largest departure {worst:.3f} dB",
    )


@register(
    _IN_SITU,
    "ISO 80000-1:2009 Annex B, B.3 Rule A, printed folios 35 and 36 (PDF pages 43 and 44)",
    "The tie-break clause 10 c) of ISO 10847 leaves open: an exact half is "
    "reported as the even whole decibel, the rule Annex B calls preferable",
)
def _chk_iso10847_rounding_tie_break() -> Outcome:
    # Annex B prints its ties at a rounding range of 10, where 1 225,0 becomes
    # 1 220 and 1 235,0 becomes 1 240. Divided by that range they are the two
    # exact halves 122,5 and 123,5 at the 1 dB rounding range clause 10 c)
    # asks for, and both are exact in binary, which the ties of the printed
    # 0,1 range are not. Rule B, the other convention in use, would print
    # 1 230 for the first of the two, so the pair discriminates.
    result = ph.environment.measured_insertion_loss_direct(
        [0.0, 0.0], [122.5, 123.5], [0.0, 0.0], [0.0, 0.0]
    )
    reported = result.rounded()
    computed = {
        "1 225,0": float(reported[0]) * 10.0,
        "1 235,0": float(reported[1]) * 10.0,
    }
    return record({"1 225,0": 1220.0, "1 235,0": 1240.0}, computed)


#: FHWA-PD-96-046 Table 3 "Classes of wind conditions", printed folio 35 (PDF
#: page 52): the three printed intervals of the source-to-receiver vector
#: component of the wind, in metres per second. The upwind row prints as an
#: interval, "-1 to -5", where ISO 10847 Table 1 prints "+ 1 to - 5"; that is
#: the corroboration the errata entry rests on. FHWA prints one flat set of
#: classes with no distance split, so it is read here against the
#: short-distance table, the only one of the two in ISO 10847 that offers an
#: upwind class at all. The endpoints are left alone because both documents
#: print intervals that share them, and neither says which class a component
#: of exactly -1 m/s or +1 m/s belongs to.
_FHWA_WIND_CLASSES_M_S: dict[str, tuple[float, float]] = {
    "upwind": (-5.0, -1.0),
    "calm": (-1.0, 1.0),
    "downwind": (1.0, 5.0),
}


@register(
    _IN_SITU,
    "FHWA-PD-96-046 Table 3, printed folio 35 (PDF page 52)",
    "A second document classing the wind the same way, with the upwind class "
    "printed as an interval running from -1 m/s to -5 m/s",
)
def _chk_fhwa_wind_classes() -> Outcome:
    matching = 0
    total = 0
    for printed, (low, high) in _FHWA_WIND_CLASSES_M_S.items():
        for fraction in (0.25, 0.5, 0.75):
            component = low + fraction * (high - low)
            total += 1
            matching += int(
                ph.environment.wind_class(component, short_distance=True) == printed
            )
    return count(matching, total, subject="readings inside the printed intervals")


def _refuses_a_margin_under_four() -> bool:
    """Whether a margin under the printed floor is refused as invalid."""
    try:
        ph.environment.barrier_background_correction_db([3.9])
    except ValueError:
        return True
    else:
        return False


@register(
    _IN_SITU,
    "CEN/TS 16272-7:2015 Table 4 and 7.3.7, printed folio 14 (PDF page 15)",
    "A second committee reprinting the same background correction: the two "
    "grouped rows, the 4 dB floor and the 10 dB margin its prose asks for",
)
def _chk_cen_ts_background_table() -> Outcome:
    corrections = ph.environment.barrier_background_correction_db(
        [4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
    )
    readings = (
        # The table prints two rows and not six: "4 and 5" against -2 dB, then
        # "6, 7, 8, 9" against -1 dB, so the grouping is part of what it says.
        bool(np.all(corrections[:2] == -2.0)),
        bool(np.all(corrections[2:] == -1.0)),
        _refuses_a_margin_under_four(),
        ph.environment.ISO10847_PREFERRED_BACKGROUND_MARGIN_DB == 10.0,
    )
    return count(
        sum(readings), len(readings), subject="readings of Table 4 and its clause"
    )


#: Jagniatinskis and others (2017), Table 1 on printed folio 293 (PDF page 5)
#: and the conclusion on folio 294: three A-weighted results, each as the
#: level at the reference point, the level at the site point and the
#: "environment correction" the paper prints, in dBA and with the minus sign
#: the table prints it with, then the insertion loss it reports. That
#: correction is the "before" difference of 8.2.1 printed as a single number
#: with its sign reversed, 76,0 - 56,3 - 9,1 = 10,6 dBA being how the table
#: closes, so the two levels behind it are free; the row runs three
#: unrelated splits of it and the answer does not move, which is the proof
#: that only the difference reaches the result. The third entry is the same
#: site read from its total level instead of the residual one, which is where
#: the 8,0 dBA of folio 294 comes from. The residual levels themselves were
#: reached through an ISO 1996 extraction of the connected-road traffic, which
#: is not the background treatment of ISO 10847 6.4 and is not exercised here.
_JAGNIATINSKIS_DBA: dict[str, tuple[float, float, float, float]] = {
    "site 1, residual": (76.0, 56.3, -9.1, 10.6),
    "site 2, residual": (75.4, 55.0, -6.9, 13.5),
    "site 1, total": (76.0, 58.9, -9.1, 8.0),
}

#: Offsets applied to the free "before" pair, in decibels.
_JAGNIATINSKIS_SPLITS_DB = (0.0, 6.0, -13.25)


@register(
    _IN_SITU,
    "Jagniatinskis et al. (2017) Table 1, printed folios 293 and 294 "
    "(PDF pages 5 and 6)",
    "Three insertion losses from a highway campaign that prints its before "
    "difference as one number, read at three unrelated splits of it",
)
def _chk_jagniatinskis_campaign() -> Outcome:
    matching = 0
    total = 0
    worst = 0.0
    for (
        reference_after,
        receiver_after,
        correction,
        printed,
    ) in _JAGNIATINSKIS_DBA.values():
        for offset in _JAGNIATINSKIS_SPLITS_DB:
            reference_before = reference_after + offset
            computed = float(
                ph.environment.measured_insertion_loss_direct(
                    [reference_before],
                    [reference_after],
                    [reference_before + correction],
                    [receiver_after],
                ).insertion_loss_db[0]
            )
            total += 1
            departure = abs(computed - printed)
            matching += int(departure <= _PRINTED_TENTH_DB)
            worst = max(worst, departure)
    return count(
        matching,
        total,
        subject="readings, three printed results at three splits each",
        expected_label=f"9/9 (worst departure {worst:.3f} dBA)",
    )


#: Rodino and Masson (2015), Tabla 2 on printed folio 7 (PDF page 7): the
#: level at the crew position without the screen and with it, for three engine
#: settings, unweighted and A-weighted, in decibels, with the insertion loss
#: the table reports. No reference microphone was used at all, so 8.2.1
#: degenerates to the plain difference of the two receiver levels and the
#: reference pair the row feeds is a constant this project chose, not a
#: measurement. What that anchors is the sign, which is positive for a screen
#: that works, and the degenerate reduction itself; it reaches nothing else,
#: and the paper cites ISO 14509 rather than ISO 10847.
_RODINO_LEVELS_DB: dict[str, tuple[float, float, float]] = {
    "Z, motor 100%": (117.6, 111.9, 5.7),
    "Z, motor 75%": (106.5, 104.0, 2.5),
    "Z, punto muerto": (73.8, 73.3, 0.5),
    "A, motor 100%": (89.0, 87.9, 1.1),
    "A, motor 75%": (81.5, 80.0, 1.5),
    "A, punto muerto": (55.4, 53.7, 1.7),
}


@register(
    _IN_SITU,
    "Rodino & Masson (2015) Tabla 2, printed folio 7 (PDF page 7)",
    "Six printed insertion losses of a screen measured with no reference "
    "microphone, where 8.2.1 degenerates to the plain level difference",
)
def _chk_rodino_degenerate_case() -> Outcome:
    matching = 0
    worst = 0.0
    for without, with_screen, printed in _RODINO_LEVELS_DB.values():
        computed = float(
            ph.environment.measured_insertion_loss_direct(
                [0.0], [0.0], [without], [with_screen]
            ).insertion_loss_db[0]
        )
        departure = abs(computed - printed)
        matching += int(departure <= _PRINTED_TENTH_DB)
        worst = max(worst, departure)
    return count(
        matching,
        len(_RODINO_LEVELS_DB),
        subject="printed insertion losses, unweighted and A-weighted",
        expected_label=f"6/6 (worst departure {worst:.3f} dB)",
    )


@register(
    _IN_SITU,
    "Bies 5e §4.9.2 (printed folio 201, PDF page 230)",
    "The 6 dB of C'_r read off a page outside the standard: the pressure "
    "doubling at a receiver held against a reflecting surface",
)
def _chk_iso10847_receiver_correction_is_a_pressure_doubling() -> Outcome:
    reference = np.array([70.0, 72.0, 74.0])
    receiver = np.array([60.0, 62.0, 63.0])
    open_field = ph.environment.measured_insertion_loss_direct(
        reference, reference, receiver, receiver - 10.0
    )
    with warnings.catch_warnings():
        # The clause prefers two receivers of one kind and the library says so;
        # mixing them is the point here, since that is what moves the answer.
        warnings.simplefilter("ignore")
        facade = ph.environment.measured_insertion_loss_indirect(
            reference,
            reference,
            receiver,
            receiver - 10.0,
            receiver_type_after="reflecting_surface",
        )
    shift = float(np.max(facade.insertion_loss_db - open_field.insertion_loss_db))
    return numeric(
        6.0,
        shift,
        1e-12,
        unit="dB",
        expected_label="6 dB, the 20 lg 2 of a pressure doubling as the page prints it",
    )


#: Geometries for the NOTE to 7.2.2, as (source-to-barrier distance, barrier
#: height) in metres, all of them inside the 15 m under which the NOTE applies.
_TEN_DEGREE_GEOMETRIES_M = ((5.0, 3.0), (10.0, 4.0), (12.0, 2.5), (14.999, 5.0))


@register(
    _IN_SITU,
    "ISO 10847:1997 7.2.2, NOTE",
    "The close-source height puts the reference microphone 10 degrees above "
    "the angle to the barrier top, and not 10 degrees above the ground",
)
def _chk_iso10847_ten_degree_increment() -> Outcome:
    # No document prints the height this yields, so what can be checked is the
    # angle the NOTE names: the elevation from the near end of the source
    # region to the microphone, less the elevation to the top of the barrier.
    # Reading it back off the returned height is not the formula run twice; it
    # is what separates this reading from the FHWA one, which raises the
    # microphone to 10 degrees over the ground plane instead and would put it
    # under the barrier top for a 4 m barrier 10 m from the source.
    worst = 0.0
    for distance, barrier in _TEN_DEGREE_GEOMETRIES_M:
        height = ph.environment.reference_microphone_height_m(
            barrier, source_to_barrier_m=distance
        )
        to_the_top = math.degrees(math.atan(barrier / distance))
        to_the_microphone = math.degrees(math.atan(height / distance))
        worst = max(worst, abs((to_the_microphone - to_the_top) - 10.0))
    return numeric(
        0.0,
        worst,
        1e-9,
        unit="deg",
        expected_label="10 degrees over the angle to the top, at four geometries",
        computed_label=f"largest departure {worst:.2e} deg",
    )
