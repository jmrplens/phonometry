#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Published worked examples for the insulation of an enclosure (ISO 11546-1).

ISO 11546-1:1995 prints no worked example of its own, so every number asserted
here was read on the printed page of a document that does, and each test says
which page. What a borrowed example can pin is the arithmetic the standard
shares with it: the band subtraction of Equations (1) and (3), the A-weighted
summation of Equations (2) and (4), the estimate of Annex C, the ISO 717-1
rating clause 7.4 delegates to, the rounding of clause 9.4 and the leak ratio
of definition 3.16. It pins nothing about the measurement procedure, the
applicability of Table 1 or the test environment, and no test here claims
otherwise.

The five sources, with the page each value was read on:

* Barron, R. F., *Industrial Noise Control and Acoustics*, Marcel Dekker, New
  York, 2003 (ISBN 0-8247-0701-X), 7.6.2, Example 7-8. Table 7-5 "Solution for
  Example 7-8" on PDF page 320, printed folio 308; the two A-weighted levels
  in the running text on PDF pages 321 and 323, printed folios 309 and 311.
* Harris, D. A. (ed.), *Noise Control Manual*, Noise Control Association, Van
  Nostrand Reinhold, 1991 (Springer reprint, ISBN 978-1-4757-6011-8), Appendix
  3. Figure A3-2 on PDF page 135, printed folio 125; Figure A3-8 on PDF page
  141, printed folio 131; the pairwise addition method on PDF page 130,
  printed folio 120.
* ISO 717-1:2020, Annex C, Table C.1, PDF page 23, printed folio 17.
* ISO 80000-1:2009, Annex B, B.2 and B.3 Rule A with its examples on PDF page
  43, printed folio 35, and the remark that Rule A is generally preferable on
  PDF page 44, printed folio 36.
* Suva, W. Lips, *Lärmbekämpfung durch Kapselungen*, Bestellnummer 66026.d,
  revised edition March 2010, 6.2.1, PDF page 17, printed folio 15.
* Schirmer, W. and Hübelt, J. (eds.), *Technischer Lärmschutz*, 3rd edition,
  Springer Vieweg, 2023, chapter 10, 10.8.1, PDF pages 517 and 518, printed
  folios 499 and 500.

The values themselves are in ``tests/reference_data/enclosure_cabin_insulation.py``
and ``tests/reference_data/rounding.py``, each beside its citation, and the
conformance rows read the same objects; the last test pins that they do.
"""

from __future__ import annotations

import math
import pathlib
import sys

import numpy as np
import pytest
import reference_data as ref
from reference_data import enclosure_cabin_insulation as oracle
from reference_data import rounding

from phonometry import noise_control
from phonometry.noise_control.enclosure_insulation import _a_weighted_total

_SCRIPTS = str(pathlib.Path(__file__).resolve().parents[2] / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from conformance.domains import enclosure_cabin_insulation as rows

#: The six octave bands both enclosure examples are worked in, in hertz, which
#: are exactly the mandatory octave range of clause 6.2 of ISO 11546-1.
OCTAVES_HZ = np.array(oracle.BARRON_TABLE_7_5_OCTAVES_HZ)

# Barron, Table 7-5, printed folio 308. Machine sound power, the power
# radiated once the enclosure is in place, the insertion loss, and the sound
# pressure levels at the operator 3 m away with and without the enclosure.
BARRON_LW_DB = np.array(oracle.BARRON_TABLE_7_5_LW_DB)
BARRON_LW_OUT_DB = np.array(oracle.BARRON_TABLE_7_5_LW_OUT_DB)
BARRON_IL_DB = np.array(oracle.BARRON_TABLE_7_5_IL_DB)
BARRON_POWER_RATIO = np.array(oracle.BARRON_TABLE_7_5_POWER_RATIO)
BARRON_LP_WITHOUT_DB = np.array(oracle.BARRON_TABLE_7_5_LP_WITHOUT_DB)
BARRON_LP_WITH_DB = np.array(oracle.BARRON_TABLE_7_5_LP_WITH_DB)

# Folio 309: "L_A = 108.4 dBA (without the enclosure)". Folio 311: "L_A = 89.8
# dBA (with the enclosure)". Their difference is D_pA; the book never prints
# it, and it is formed here from the two printed totals.
BARRON_LPA_WITHOUT_DBA = oracle.BARRON_EXAMPLE_7_8_LPA_WITHOUT_DBA
BARRON_LPA_WITH_DBA = oracle.BARRON_EXAMPLE_7_8_LPA_WITH_DBA

# Harris, Figures A3-2 and A3-8: the octave levels at the worker's station
# before any treatment, the A-weighted level the figures print for them, and
# the four cases of the two figures.
HARRIS_BEFORE_DB = np.array(oracle.HARRIS_BEFORE_DB)
HARRIS_BEFORE_DBA = oracle.HARRIS_BEFORE_DBA
HARRIS_CASES = oracle.HARRIS_CASES

# ISO 717-1:2020 Table C.1, the sound reduction index column over the sixteen
# one-third-octave rating bands, read as an insulation spectrum because
# clause 7.4 of ISO 11546-1 rates D_W exactly the way ISO 717-1 rates R.
ISO717_TABLE_C1_DB = ref.ISO717_1_ANNEX_C_R

# Suva 6.2.1: the manufacturer's octave sound power levels of a converter set,
# of which the guide says "Diese Werte ergeben L_WA = 104 dB".
SUVA_OCTAVES_HZ = np.array(oracle.SUVA_OCTAVES_HZ)
SUVA_LW_DB = np.array(oracle.SUVA_LW_DB)
SUVA_LWA_DB = oracle.SUVA_LWA_DB

# Schirmer, 10.8.1: the opening, the 96 m2 of walls and roof with the opening
# counted in and the floor left out, and the opening fraction q it prints.
SCHIRMER_OPENING_M2 = oracle.SCHIRMER_OPENING_M2
SCHIRMER_SURFACE_M2 = oracle.SCHIRMER_SURFACE_M2
SCHIRMER_LEAK_RATIO = oracle.SCHIRMER_LEAK_RATIO


def _barron_pressure() -> noise_control.EnclosureInsulationResult:
    """Equations (3) and (4) on the two printed sound pressure spectra."""
    return noise_control.sound_pressure_insulation(
        BARRON_LP_WITHOUT_DB,
        BARRON_LP_WITH_DB,
        frequencies=OCTAVES_HZ,
        base_standard="ISO 11201",
        band_fraction=1,
    )


def test_barron_example_7_8_band_insulation() -> None:
    """Equation (3) reproduces the printed insertion loss row, band by band.

    The difference of the two printed sound pressure spectra is the insertion
    loss column of Table 7-5 in all six bands, to the 0.1 dB the book prints.
    """
    got = _barron_pressure().insulation
    assert got == pytest.approx(BARRON_IL_DB, abs=1e-9)


def test_barron_example_7_8_a_weighted_insulation() -> None:
    """Equation (4) lands on the difference of the two printed totals.

    The book prints 108.4 dBA without the enclosure and 89.8 dBA with it, so
    D_pA is 18.6 dB. Each total is printed to a tenth, so their difference is
    good to a tenth and is asserted to that. The library's own totals round to
    the printed pair, and their difference sits 0.02 dB from it.
    """
    result = _barron_pressure()
    assert result.a_weighted_insulation is not None
    assert result.a_weighted_insulation == pytest.approx(
        BARRON_LPA_WITHOUT_DBA - BARRON_LPA_WITH_DBA, abs=0.1
    )
    without = _a_weighted_total(BARRON_LP_WITHOUT_DB, OCTAVES_HZ)
    with_enclosure = _a_weighted_total(BARRON_LP_WITH_DB, OCTAVES_HZ)
    assert round(without, 1) == BARRON_LPA_WITHOUT_DBA
    assert round(with_enclosure, 1) == BARRON_LPA_WITH_DBA


def test_barron_example_7_8_annex_c_estimate() -> None:
    """Annex C, fed the unenclosed spectrum and the printed insertion loss.

    The estimate is the same difference of A-weighted totals that Equation (4)
    forms, so it must agree with it to the last bit and with the printed pair
    to the tenth the book prints. That equality is what pins the sign of the
    A-weighting term the annex prints as an attenuation.
    """
    estimate = noise_control.estimated_a_weighted_insulation(
        BARRON_LP_WITHOUT_DB, BARRON_IL_DB, frequencies=OCTAVES_HZ
    )
    assert estimate == _barron_pressure().a_weighted_insulation
    assert estimate == pytest.approx(
        BARRON_LPA_WITHOUT_DBA - BARRON_LPA_WITH_DBA, abs=0.1
    )


def test_barron_example_7_8_sound_power_insulation() -> None:
    """Equation (1) on the printed sound power rows, minus the 2 kHz band.

    D_W is the difference of the two sound power determinations, which is the
    same subtraction the book writes as its Equation (7-76). Five of the six
    bands reproduce the printed insertion loss exactly; the sixth is the band
    the table itself is inconsistent in, and the test below says how.
    """
    keep = OCTAVES_HZ != oracle.BARRON_TABLE_7_5_INCONSISTENT_BAND_HZ
    result = noise_control.sound_power_insulation(
        BARRON_LW_DB[keep],
        BARRON_LW_OUT_DB[keep],
        frequencies=OCTAVES_HZ[keep],
        base_standard="ISO 3744",
        band_fraction=1,
    )
    assert result.insulation == pytest.approx(BARRON_IL_DB[keep], abs=1e-9)
    assert result.quantity == "sound_power"


def test_barron_table_7_5_is_a_tenth_out_at_2_khz() -> None:
    """Why the 2 kHz band is left out of the Equation (1) comparison.

    The oracle checked against itself before it is used. Every band of Table
    7-5 closes on 10 lg(W/W_out) except 2 000 Hz, where the printed L_W,out of
    94.2 dB does not follow from the printed insertion loss of 18.9 dB, and
    the table's own sound pressure level of 83.9 dB follows 94.1 dB instead.
    So it is L_W,out that is a tenth high there, not the insertion loss. A slip
    in a textbook is not an erratum of a standard, which is why it is recorded
    here and not in docs/ERRATA.md.
    """
    from_ratio = 10.0 * np.log10(BARRON_POWER_RATIO)
    assert np.round(from_ratio, 1) == pytest.approx(BARRON_IL_DB)

    band = int(
        np.flatnonzero(OCTAVES_HZ == oracle.BARRON_TABLE_7_5_INCONSISTENT_BAND_HZ)[0]
    )
    printed = BARRON_LW_DB[band] - BARRON_LW_OUT_DB[band]
    assert printed == pytest.approx(18.8, abs=1e-9)
    assert BARRON_IL_DB[band] == 18.9
    consistent = BARRON_LW_DB[band] - from_ratio[band]
    assert round(float(consistent), 1) == 94.1
    # The room term of the table is -10.3 dB at 2 kHz and the table carries a
    # further +0.1 dB, which reproduces the printed 83.9 dB from 94.1 and not
    # from 94.2.
    assert round(float(consistent) - 10.3 + 0.1, 1) == BARRON_LP_WITH_DB[band]


@pytest.mark.parametrize("case", list(HARRIS_CASES))
def test_harris_estimated_reduction(case: str) -> None:
    """The Annex C estimate against four hand-computed enclosure cases.

    Harris adds bands pairwise from a difference table rather than by an
    energy sum, which costs about 0.7 dB at worst, so the comparison is on the
    reduction and carries a decibel. It is never on the rounded total: Example
    1(a) prints 94 dBA where its own pairwise chain lands on 94.5 and an
    energy sum gives 94.7, so a test phrased on the rounded total would be red
    for a correct implementation.

    Example 3 is a personnel enclosure, nearer ISO 11957 in subject, and its
    reduction is the printed room adjustment plus the printed transmission
    loss. That sum is exact arithmetic on the printed lines, but it is a
    construction rather than a quotation.
    """
    reduction_db, printed_dba = HARRIS_CASES[case]
    estimate = noise_control.estimated_a_weighted_insulation(
        HARRIS_BEFORE_DB, reduction_db, frequencies=OCTAVES_HZ
    )
    assert estimate == pytest.approx(HARRIS_BEFORE_DBA - printed_dba, abs=1.0), case


def test_harris_example_1a_is_the_loose_case() -> None:
    """The one case where the book's own addition is more than half a decibel.

    Recorded so that the decibel of tolerance above is attributed: it is the
    pairwise chain of Figure A3-1, not the A-weighting table and not the
    formula. The other three cases sit inside half a decibel.
    """
    loose = "Example 1(a), plywood"
    departures = {}
    for case, (reduction, printed) in HARRIS_CASES.items():
        estimate = noise_control.estimated_a_weighted_insulation(
            HARRIS_BEFORE_DB, reduction, frequencies=OCTAVES_HZ
        )
        departures[case] = abs(estimate - (HARRIS_BEFORE_DBA - printed))
    assert departures[loose] > 0.5
    assert max(value for case, value in departures.items() if case != loose) < 0.5


def test_iso717_calculation_example_through_clause_7_4() -> None:
    """Clause 7.4 rates D_W the way ISO 717-1 rates R, and here is that rating.

    The printed calculation example of Annex C, fed in as an insulation
    spectrum. It exercises the delegation and the rating bands, not any
    enclosure physics, because clause 7.4 contains none: the same table backs
    the rating rows of the building domain.
    """
    rated = noise_control.weighted_insulation(
        ISO717_TABLE_C1_DB, quantity="sound_power", band_fraction=3
    )
    assert (rated.rating, rated.c, rated.ctr) == (30, -2, -3)
    assert rated.unfavourable_sum == pytest.approx(31.8, abs=0.05)
    assert rated.unfavourable_sum < 32.0
    assert rated.quantity == "sound_power"
    assert rated.band_centres_hz[0] == 100.0
    assert rated.band_centres_hz[-1] == 3150.0
    assert rated.band_centres_hz.size == len(ISO717_TABLE_C1_DB)


def test_clause_9_4_rounding_is_rule_a_of_iso_80000_1() -> None:
    """The rounding of clause 9.4, against the printed examples of Annex B.

    Clause 9.4 asks for decibels rounded to the nearest integer and names no
    rule. Annex B names two: Rule A takes the even multiple and Rule B the
    greater in magnitude, and the annex calls Rule A generally preferable.
    Each printed number is divided by its printed rounding range, which B.1
    defines as the interval between the multiples being rounded to, so what is
    left is a rounding to the nearest integer.

    The ties printed at rounding range 0,1 are deliberately absent: 12,35 has
    no exact double, so the tie is gone before any code sees it and the
    comparison would test the binary representation rather than the rule. The
    two ties at rounding range 10 are exact and are the pair that decides.
    """
    printed = {
        name: (number / scale, multiples)
        for name, (number, scale, multiples) in (
            rounding.ISO80000_1_ANNEX_B_ROUNDINGS.items()
        )
    }
    given = [multiple for multiple, _ in printed.values()]
    rounded = noise_control.sound_power_insulation(given, [0.0] * len(given)).rounded()
    for got, (name, (_, want)) in zip(rounded.tolist(), printed.items(), strict=True):
        assert got == want, name

    # Where the two rules part, the library follows Rule A: Rule B would send
    # 1 225,0 to 1 230 rather than to 1 220. Where they agree, so does it.
    rule_b = [math.floor(abs(value) + 0.5) for value in given]
    assert rounded.tolist()[-2] != rule_b[-2]
    assert rounded.tolist()[-1] == rule_b[-1]


def test_suva_a_weighted_sound_power_total() -> None:
    """The A-weighted total Equation (2) forms, against a printed integer.

    The A-weighting correction is zero at 1 kHz by definition, so a reference
    spectrum whose energy sits in that band alone has an A-weighted total
    equal to its band level. Putting that level at 0 dB makes Equation (2)
    return the A-weighted total of the other spectrum, which is the only
    quantity the guide prints.

    The guide prints the integer alone, so this pins the total to half a
    decibel and no better. It is enough to fix the sign of the band
    corrections and the use of an energy sum: a sign flip gives 120 dB and an
    unweighted sum 107 dB, both far outside the rounding window.
    """
    reference = np.full(SUVA_LW_DB.size, -300.0)
    reference[SUVA_OCTAVES_HZ == 1000.0] = 0.0
    result = noise_control.sound_power_insulation(
        SUVA_LW_DB,
        reference,
        frequencies=SUVA_OCTAVES_HZ,
        base_standard="ISO 3744",
        band_fraction=1,
    )
    assert result.a_weighted_insulation is not None
    assert round(result.a_weighted_insulation) == SUVA_LWA_DB
    assert result.a_weighted_insulation == pytest.approx(SUVA_LWA_DB, abs=0.5)
    assert result.a_weighted_insulation == pytest.approx(
        _a_weighted_total(SUVA_LW_DB, SUVA_OCTAVES_HZ), abs=1e-9
    )


def test_schirmer_leak_ratio() -> None:
    """Definition 3.16 on a printed enclosure, where the book calls it q.

    The denominator is the interior surface with the openings counted in,
    which is the one place a convention could be the wrong way round. The 96 m²
    is the book's own modelling choice, walls and roof with the floor left
    out, so it is passed in as a printed input rather than derived; the
    cross-check below only confirms the reading of the geometry.

    Definition 3.16 of part 1 and 3.14 of part 2 are the same definition in
    the same words, and the conformance row for this division is registered
    against the second edition of the same chapter. The numbers here were read
    on the third edition, and both editions print q = 2,6e-3.
    """
    got = noise_control.leak_ratio(SCHIRMER_OPENING_M2, SCHIRMER_SURFACE_M2)
    assert got == pytest.approx(SCHIRMER_LEAK_RATIO, abs=5e-5)
    assert f"{got:.1e}" == "2.6e-03"
    walls_and_roof = 2 * (6.0 * 3.0) + 2 * (5.0 * 3.0) + 6.0 * 5.0
    assert walls_and_roof == pytest.approx(SCHIRMER_SURFACE_M2)
    assert SCHIRMER_SURFACE_M2 - SCHIRMER_OPENING_M2 == pytest.approx(95.75)
    assert noise_control.seal_ratio(got) == pytest.approx(
        1.0 / SCHIRMER_LEAK_RATIO, rel=0.01
    )


def test_the_conformance_rows_read_the_same_printed_values() -> None:
    """One transcription, read by the tests and by the conformance rows alike.

    The rows used to carry a copy of these tables of their own. They read
    ``tests/reference_data`` now, so a correction lands in both at once; this
    pins that they still do, and that the band they drop from the sound power
    comparison is the one the table is inconsistent in.
    """
    assert rows.oracle is oracle
    assert rows.rounding is rounding
    assert rows._BOOK_OCTAVES_HZ.tolist() == OCTAVES_HZ.tolist()
    assert rows._BARRON_LW_DB.tolist() == BARRON_LW_DB.tolist()
    assert rows._BARRON_LW_OUT_DB.tolist() == BARRON_LW_OUT_DB.tolist()
    assert rows._BARRON_IL_DB.tolist() == BARRON_IL_DB.tolist()
    assert rows._BARRON_LP_WITHOUT_DB.tolist() == BARRON_LP_WITHOUT_DB.tolist()
    assert rows._BARRON_LP_WITH_DB.tolist() == BARRON_LP_WITH_DB.tolist()
    assert rows._BARRON_POWER_BANDS.tolist() == (OCTAVES_HZ != 2000.0).tolist()
