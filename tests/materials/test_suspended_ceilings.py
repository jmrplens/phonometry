#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the suspended-ceiling test code (EN 16487:2014).

The standard prints no worked example. Its oracles are the numbers it fixes:
the specimen geometry of 4.1.1, the air-absorption cap of 4.2.1, and Table 1,
the reproducibility of the round robin behind it.

The second half of this file pins the chain 4.2.1 hangs off, on printed pages
of four other documents and on three real laboratory reports. The numbers are
in ``tests/reference_data/suspended_ceilings.py``, each with its document, its
edition, its printed folio and its PDF page where one applies; the documents
themselves are not in the repository, and the reports are cited rather than
reproduced. The conformance rows in
``scripts/conformance/domains/suspended_ceilings.py`` read the same numbers.
"""

from __future__ import annotations

import math
import warnings
from typing import Any

import numpy as np
import pytest
from reference_data import suspended_ceilings as oracle

from phonometry import environment, materials
from phonometry.materials.absorbers.suspended_ceilings import (
    AIR_CORRECTION_LIMIT,
    CEILING_UNCERTAINTY,
    EN16487_COVERAGE_FACTOR,
    MAX_DEFLECTION_MM,
    MIN_FIXTURE_DENSITY_KG_M2,
    MIN_RELATIVE_HUMIDITY_PERCENT,
    MIN_ROOM_EDGE_ANGLE_DEG,
    MIN_SUPPORT_SPACING_M,
    MOUNTING_TYPES,
    SUBSTRUCTURE_LIMITS_MM,
    SUPPORT_SECTION_MM,
    TARGET_SPECIMEN_AREA_M2,
    TEST_OBJECT_SIZE_M,
    TYPE_E_DEPTH_MM,
    WEIGHTED_UNCERTAINTY,
    SuspendedCeilingWarning,
)


def test_the_table_one_figures_are_the_printed_ones() -> None:
    assert CEILING_UNCERTAINTY == {
        125.0: 0.23,
        250.0: 0.23,
        500.0: 0.11,
        1000.0: 0.10,
        2000.0: 0.10,
        4000.0: 0.13,
    }
    assert WEIGHTED_UNCERTAINTY == 0.08
    assert EN16487_COVERAGE_FACTOR == 2.8


def test_the_uncertainty_falls_with_frequency_until_four_kilohertz() -> None:
    got = materials.reproducibility_uncertainty()
    assert got.tolist() == [0.23, 0.23, 0.11, 0.10, 0.10, 0.13]
    assert got[0] > got[3]
    assert got[-1] > got[-2]


def test_one_band_can_be_asked_for_by_frequency() -> None:
    assert materials.reproducibility_uncertainty([500.0]).tolist() == [0.11]


def test_a_band_table_one_does_not_print_is_refused() -> None:
    with pytest.raises(ValueError, match="Table 1"):
        materials.reproducibility_uncertainty([63.0])


def test_the_uncertainty_is_a_coverage_factor_over_a_standard_deviation() -> None:
    """The note under Table 1: ISO 5725-6 with a coverage factor of 2,8."""
    sigma = CEILING_UNCERTAINTY[1000.0] / EN16487_COVERAGE_FACTOR
    assert sigma == pytest.approx(0.0357, abs=1e-4)


def test_the_air_correction_is_four_volumes_over_the_area() -> None:
    with pytest.warns(SuspendedCeilingWarning, match="4.2.1"):
        got = materials.air_absorption_correction(
            volume_m3=200.0,
            specimen_area_m2=10.8,
            attenuation_with=[0.01],
            attenuation_empty=[0.008],
        )
    assert got[0] == pytest.approx(4.0 * 200.0 * 0.002 / 10.8)


def test_a_dry_room_can_pass_the_cap_the_clause_sets() -> None:
    """A difference of 1e-4 per metre in a 200 m3 room is 0,0074, well under."""
    got = materials.air_absorption_correction(
        volume_m3=200.0,
        specimen_area_m2=10.8,
        attenuation_with=[0.0101],
        attenuation_empty=[0.0100],
    )
    assert abs(got[0]) < AIR_CORRECTION_LIMIT


def test_the_correction_is_zero_when_the_air_did_not_change() -> None:
    got = materials.air_absorption_correction(
        volume_m3=200.0,
        specimen_area_m2=10.8,
        attenuation_with=[0.01, 0.02],
        attenuation_empty=[0.01, 0.02],
    )
    assert np.allclose(got, 0.0)


def test_mismatched_attenuation_spectra_are_refused() -> None:
    with pytest.raises(ValueError, match="band for band"):
        materials.air_absorption_correction(
            volume_m3=200.0,
            specimen_area_m2=10.8,
            attenuation_with=[0.01, 0.02],
            attenuation_empty=[0.01],
        )


def test_the_printed_geometry_is_the_printed_geometry() -> None:
    assert TARGET_SPECIMEN_AREA_M2 == 10.80
    assert TEST_OBJECT_SIZE_M == (0.6, 0.6)
    assert MIN_ROOM_EDGE_ANGLE_DEG == 10.0
    assert MIN_FIXTURE_DENSITY_KG_M2 == 20.0
    assert TYPE_E_DEPTH_MM == 200.0
    assert MAX_DEFLECTION_MM == 5.0
    assert SUBSTRUCTURE_LIMITS_MM == (30.0, 50.0)
    assert MIN_RELATIVE_HUMIDITY_PERCENT == 50.0


def test_a_conforming_arrangement_passes() -> None:
    check = materials.check_ceiling_specimen(
        area_m2=10.8,
        depth_mm=200.0,
        deflection_mm=3.0,
        substructure_width_mm=25.0,
        substructure_height_mm=45.0,
    )
    assert check.satisfied is True
    assert check.ce_marking_depth is True
    assert check.area_error_m2 == pytest.approx(0.0)


def test_a_sagging_ceiling_fails_the_deflection_rule() -> None:
    with pytest.warns(SuspendedCeilingWarning, match="4.1.1.2.3.5"):
        check = materials.check_ceiling_specimen(
            area_m2=10.8, depth_mm=200.0, deflection_mm=8.0
        )
    assert check.deflection_ok is False
    assert check.satisfied is False


def test_a_deep_substructure_fails_its_own_rule() -> None:
    with pytest.warns(SuspendedCeilingWarning, match="substructure"):
        check = materials.check_ceiling_specimen(
            area_m2=10.8, depth_mm=200.0, substructure_height_mm=70.0
        )
    assert check.substructure_ok is False


def test_a_light_mounting_fixture_fails() -> None:
    with pytest.warns(SuspendedCeilingWarning, match="4.1.1.1.6"):
        check = materials.check_ceiling_specimen(
            area_m2=10.8, depth_mm=200.0, fixture_density_kg_m2=8.0
        )
    assert check.fixture_ok is False


def test_another_depth_is_allowed_but_is_not_the_ce_marking_one() -> None:
    """4.1.1.2.3.1, printed folio 9 (PDF page 11): another depth still passes.

    200 mm is "recommended", and it "shall be used for the compilation of data
    for CE marking". Another depth is inside the test code, so the warning says
    what the depth is not and stops there.
    """
    with pytest.warns(SuspendedCeilingWarning, match="CE marking") as caught:
        check = materials.check_ceiling_specimen(area_m2=10.8, depth_mm=400.0)
    assert check.satisfied is True
    assert check.ce_marking_depth is False
    assert all("outside EN 16487" not in str(entry.message) for entry in caught)


def test_a_limit_left_and_another_depth_are_told_apart_in_one_warning() -> None:
    with pytest.warns(SuspendedCeilingWarning) as caught:
        check = materials.check_ceiling_specimen(
            area_m2=10.8, depth_mm=400.0, deflection_mm=8.0
        )
    (message,) = [str(entry.message) for entry in caught]
    _, _, after = message.partition("outside EN 16487: ")
    outside, _, rest = after.partition(". ")
    assert outside == "the specimen deflects 8 mm, over the 5 mm of 4.1.1.2.3.5"
    assert "CE marking" in rest
    assert "outside" not in rest
    assert check.satisfied is False


def test_supports_inside_the_printed_section_and_spacing_pass() -> None:
    """4.1.1.2.3.6, printed folio 10 (PDF page 12), both bounds met exactly."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", SuspendedCeilingWarning)
        check = materials.check_ceiling_specimen(
            area_m2=10.8,
            depth_mm=200.0,
            support_width_mm=50.0,
            support_height_mm=50.0,
            support_centre_distance_m=1.2,
        )
    assert check.supports_ok is True
    assert check.satisfied is True


def test_the_printed_support_limits_are_the_printed_ones() -> None:
    assert SUPPORT_SECTION_MM == (50.0, 50.0)
    assert MIN_SUPPORT_SPACING_M == 1.2


@pytest.mark.parametrize(
    ("field", "value"),
    [("support_width_mm", 60.0), ("support_height_mm", 50.5)],
)
def test_a_support_over_the_printed_section_fails(field: str, value: float) -> None:
    """4.1.1.2.3.6, printed folio 10 (PDF page 12), on each side in turn.

    "The cross section of the support units shall be <= 50 mm x 50 mm".
    """
    dimension: dict[str, Any] = {field: value}
    with pytest.warns(SuspendedCeilingWarning, match=r"4\.1\.1\.2\.3\.6"):
        check = materials.check_ceiling_specimen(
            area_m2=10.8, depth_mm=200.0, **dimension
        )
    assert check.supports_ok is False
    assert check.satisfied is False


def test_supports_closer_than_the_printed_spacing_fail() -> None:
    """4.1.1.2.3.6: support units "at centre distances of >= 1,2 m"."""
    with pytest.warns(SuspendedCeilingWarning, match=r"1\.2 m of 4\.1\.1\.2\.3\.6"):
        check = materials.check_ceiling_specimen(
            area_m2=10.8,
            depth_mm=200.0,
            support_width_mm=40.0,
            support_height_mm=40.0,
            support_centre_distance_m=1.0,
        )
    assert check.supports_ok is False
    assert check.satisfied is False


@pytest.mark.parametrize("value", [0.0, -1.2, float("nan"), float("inf")])
def test_a_non_positive_support_spacing_is_refused(value: float) -> None:
    with pytest.raises(ValueError, match="support_centre_distance_m"):
        materials.check_ceiling_specimen(
            area_m2=10.8, depth_mm=200.0, support_centre_distance_m=value
        )


def test_a_dry_room_fails_the_humidity_floor() -> None:
    """4.2.2, printed folio 12 (PDF page 14), on the SRL room at 41 % and 44 %.

    "The relative humidity in the room shall be at least 50 %", and 4.2.3,
    printed folio 13 (PDF page 15), has it checked for each measurement.
    """
    with pytest.warns(SuspendedCeilingWarning, match=r"41 %.*50 % of 4\.2\.2"):
        check = materials.check_ceiling_specimen(
            area_m2=10.8, depth_mm=200.0, relative_humidity_percent=[41.0, 44.0]
        )
    assert check.humidity_ok is False
    assert check.satisfied is False


@pytest.mark.parametrize("humidity", [[62.0, 58.0], [50.0, 50.0], 55.0])
def test_a_room_at_or_over_the_floor_passes(humidity: float | list[float]) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", SuspendedCeilingWarning)
        check = materials.check_ceiling_specimen(
            area_m2=10.8, depth_mm=200.0, relative_humidity_percent=humidity
        )
    assert check.humidity_ok is True
    assert check.satisfied is True


def test_one_dry_measurement_among_humid_ones_fails() -> None:
    with pytest.warns(SuspendedCeilingWarning, match="4.2.2"):
        check = materials.check_ceiling_specimen(
            area_m2=10.8, depth_mm=200.0, relative_humidity_percent=[62.0, 49.0, 58.0]
        )
    assert check.humidity_ok is False


def test_an_omitted_humidity_is_not_judged() -> None:
    check = materials.check_ceiling_specimen(area_m2=10.8, depth_mm=200.0)
    assert check.humidity_ok is None
    assert check.supports_ok is True
    assert check.satisfied is True


@pytest.mark.parametrize(
    "humidity",
    [[62.0, float("nan")], [], [[60.0, 60.0]], [-1.0], [101.0], "humid"],
)
def test_a_humidity_that_is_not_one_is_refused(humidity: object) -> None:
    with pytest.raises(ValueError, match="relative_humidity_percent"):
        materials.check_ceiling_specimen(
            area_m2=10.8,
            depth_mm=200.0,
            relative_humidity_percent=humidity,  # type: ignore[arg-type]
        )


def test_the_ce_marking_depth_belongs_to_the_type_e_mounting_alone() -> None:
    """4.1.1.2.3.1 fixes 200 mm for type E, so type A cannot reach it."""
    check = materials.check_ceiling_specimen(
        area_m2=10.8, mounting="A", depth_mm=TYPE_E_DEPTH_MM
    )
    assert check.ce_marking_depth is False
    assert check.satisfied is True


def test_a_type_e_arrangement_without_a_depth_is_refused() -> None:
    with pytest.raises(ValueError, match="depth_mm"):
        materials.check_ceiling_specimen(area_m2=10.8)


def test_the_four_mountings_are_the_admitted_ones() -> None:
    assert sorted(MOUNTING_TYPES) == ["A", "B", "E", "J"]
    assert "air space" in materials.mounting_type("E")
    assert "3 mm" in materials.mounting_type("B")


def test_an_unknown_mounting_letter_is_refused() -> None:
    with pytest.raises(ValueError, match="mounting"):
        materials.check_ceiling_specimen(area_m2=10.8, mounting="Z", depth_mm=200.0)


@pytest.mark.parametrize(
    "field",
    [
        "deflection_mm",
        "substructure_width_mm",
        "substructure_height_mm",
        "support_width_mm",
        "support_height_mm",
        "fixture_density_kg_m2",
    ],
)
def test_a_negative_geometry_is_refused_rather_than_judged(field: str) -> None:
    """An upper bound alone would let a negative length pass as conforming."""
    negative: dict[str, Any] = {field: -1.0}
    with pytest.raises(ValueError, match=field):
        materials.check_ceiling_specimen(area_m2=10.8, depth_mm=200.0, **negative)


@pytest.mark.parametrize("value", [float("-inf"), float("inf"), float("nan")])
def test_a_non_finite_geometry_is_refused(value: float) -> None:
    with pytest.raises(ValueError, match="deflection_mm"):
        materials.check_ceiling_specimen(
            area_m2=10.8, depth_mm=200.0, deflection_mm=value
        )


def test_an_area_away_from_the_target_is_reported_and_not_warned_about() -> None:
    # 4.1.1.1.1 asks for an area "as close to 10,80 m2 as possible", which is a
    # target and not a tolerance: the difference is reported, and nothing in the
    # clause makes one number of it a failure.
    with warnings.catch_warnings():
        warnings.simplefilter("error", SuspendedCeilingWarning)
        check = materials.check_ceiling_specimen(area_m2=9.6, depth_mm=200.0)
    assert check.area_error_m2 == pytest.approx(-1.2)
    assert check.satisfied is True


def test_an_air_correction_over_the_cap_is_warned_about() -> None:
    with pytest.warns(SuspendedCeilingWarning, match="4.2.1"):
        correction = materials.air_absorption_correction(
            volume_m3=200.0,
            specimen_area_m2=10.8,
            attenuation_with=[0.0005, 0.0230],
            attenuation_empty=[0.0004, 0.0210],
        )
    assert float(correction[-1]) > materials.AIR_CORRECTION_LIMIT


def test_a_correction_inside_the_cap_is_silent() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", SuspendedCeilingWarning)
        correction = materials.air_absorption_correction(
            volume_m3=200.0,
            specimen_area_m2=10.8,
            attenuation_with=[0.0011, 0.0035],
            attenuation_empty=[0.0010, 0.0030],
        )
    assert float(max(correction)) < materials.AIR_CORRECTION_LIMIT


# ---------------------------------------------------------------------------
# Printed oracles for the chain EN 16487 4.2.1 hangs off
# ---------------------------------------------------------------------------

#: EN ISO 354:2003, 8.1.2.1, printed folio 10 (PDF page 20): the relation
#: ``m = alpha / (10 lg(e))``, evaluated here with the standard library so the
#: expected side of the correction tests owes nothing to the module under test.
_TEN_LG_E = 10.0 * math.log10(math.e)


def _m_from_printed_alpha(
    *, temperature_c: float, humidity: float, bands: tuple[float, ...]
) -> np.ndarray:
    """``m`` in 1/m from the printed ISO 9613-1 row, without the library."""
    column = oracle.ISO9613_1_TABLE_1_DB_PER_KM[(temperature_c, humidity)]
    alpha = np.array([column[band] for band in bands], dtype=float)
    return alpha / 1000.0 / _TEN_LG_E


def _library_m(
    *, temperature_c: float, humidity: float, bands: tuple[float, ...]
) -> np.ndarray:
    """The same ``m``, through the library's own EN ISO 354 conversion."""
    column = oracle.ISO9613_1_TABLE_1_DB_PER_KM[(temperature_c, humidity)]
    alpha = np.array([column[band] for band in bands], dtype=float)
    return np.asarray(materials.attenuation_from_alpha(alpha / 1000.0))


def test_the_weighted_row_of_table_one_is_printed_too() -> None:
    """Table 1, printed folio 14: six bands and the weighted rating."""
    printed = tuple(oracle.EN16487_TABLE_1_UNCERTAINTY.values())
    assert tuple(materials.reproducibility_uncertainty().tolist()) == printed
    assert WEIGHTED_UNCERTAINTY == oracle.EN16487_TABLE_1_WEIGHTED_UNCERTAINTY


def test_the_two_coverage_factors_are_not_interchanged() -> None:
    """2,8 in the NOTE of Table 1, 2,0 in ISO 12999-2:2020 Table 3 at 95 %.

    EN 16487 prints no reproducibility standard deviation anywhere, so its 2,8
    cannot be checked by dividing Table 1 by it and multiplying back: that is
    an identity and it holds for any pair of numbers. What is checkable is that
    each document's own factor is the one the library uses for that document.
    """
    assert EN16487_COVERAGE_FACTOR == oracle.EN16487_TABLE_1_COVERAGE_FACTOR
    assert (
        materials.absorption_coverage_factor(0.95)
        == oracle.ISO12999_2_TABLE_3_COVERAGE_FACTOR_95
    )


def test_the_printed_attenuation_of_iso9613_table_one() -> None:
    """Twenty cells of Table 1(i) and 1(j), to half their last printed digit.

    Note 5 of clause 6.4 says the table was evaluated at the exact
    one-third-octave midbands, so the flag that reproduces it is set. At the
    nominal 4 kHz the same call returns 29,67 dB/km against a printed
    2,94 x 10, which no rounding of three figures covers.
    """
    for (temperature_c, humidity), row in oracle.ISO9613_1_TABLE_1_DB_PER_KM.items():
        bands = list(row)
        computed = (
            environment.air_attenuation(
                bands,
                temperature_c=temperature_c,
                relative_humidity_percent=humidity,
                atmospheric_pressure_kpa=101.325,
                exact_midband=True,
            )
            * 1000.0
        )
        for band, got in zip(bands, computed.tolist(), strict=True):
            printed = row[band]
            half_digit = 10.0 ** (math.floor(math.log10(printed)) - 2) / 2.0
            assert got == pytest.approx(printed, abs=half_digit), (
                f"{temperature_c} degC, {humidity} %, {band} Hz"
            )


def test_the_conversion_factor_between_alpha_and_m_is_the_printed_one() -> None:
    """Vigran, Building Acoustics (2008), Eq. (4.41), printed page 122.

    EN ISO 354:2003 8.1.2.1 gives ``m = alpha / (10 lg(e))`` and never works
    the factor out; Vigran prints it as 4,343.
    """
    assert 1.0 / float(materials.attenuation_from_alpha(1.0)) == pytest.approx(
        oracle.VIGRAN_EQ_4_41_TEN_LG_E, abs=5e-4
    )


def test_the_air_term_carries_the_factor_of_four_the_example_prints() -> None:
    """Vigran, Building Acoustics (2008), the Example on printed page 123.

    A 100 m3 room with ``m`` = 0,05 1/m at 8 kHz: "The air absorption alone
    then gives an absorption area of 20 m2". EN 16487 4.2.1 spreads that same
    ``4V(m2 - m1)`` over the specimen, so multiplying back by the area returns
    the printed figure. The arrangement is a classroom rather than a
    reverberation-room test, so the clause reports its cap, which is expected
    here and not the point of the check.
    """
    with pytest.warns(SuspendedCeilingWarning, match="4.2.1"):
        correction = materials.air_absorption_correction(
            volume_m3=oracle.VIGRAN_EXAMPLE_VOLUME_M3,
            specimen_area_m2=TARGET_SPECIMEN_AREA_M2,
            attenuation_with=[oracle.VIGRAN_EXAMPLE_M_PER_M],
            attenuation_empty=[0.0],
        )
    assert float(correction[0]) * TARGET_SPECIMEN_AREA_M2 == pytest.approx(
        oracle.VIGRAN_EXAMPLE_AIR_ABSORPTION_M2
    )


def test_the_printed_air_absorption_constant_of_cox_table_four_two() -> None:
    """Cox & D'Antonio 3e (2017), Table 4.2, printed page 104.

    A second printed table of ``m`` itself, so the ISO 9613-1 attenuation and
    the EN ISO 354 conversion are checked together against a source that owes
    nothing to either. The book evaluates at the nominal octave centres, so no
    midband snapping is asked for; the rows below 50 % relative humidity are
    left out because 4.2.2 does not allow a room that dry.
    """
    for humidity, row in oracle.COX_TABLE_4_2_M_MILLI.items():
        computed = (
            environment.air_attenuation_m(
                oracle.COX_TABLE_4_2_BANDS_HZ,
                temperature_c=20.0,
                relative_humidity_percent=humidity,
                atmospheric_pressure_kpa=101.325,
            )
            * 1e3
        )
        for band, printed, got in zip(
            oracle.COX_TABLE_4_2_BANDS_HZ, row, computed.tolist(), strict=True
        ):
            decimals = len(f"{printed!r}".partition(".")[2])
            assert got == pytest.approx(printed, abs=0.5 * 10.0**-decimals), (
                f"{humidity} %, {band} Hz"
            )


def test_a_ten_point_humidity_swing_busts_the_cap_of_the_clause() -> None:
    """EN 16487:2014 4.2.1 on the room SRL certificate 13441 prints.

    V = 300 m3 and S = 10,7 m2 from the certificate, the two climates from two
    printed columns of ISO 9613-1 Table 1(i) at 20 degC. The correction itself
    is printed nowhere, so the expected side is this file's own arithmetic on
    the printed relation of EN ISO 354 8.1.2.1: what the test holds the library
    to is the dB/km to 1/m path, the sign of ``m2 - m1``, the factor of four
    and the cap being judged on the absolute value.
    """
    bands = (500.0, 1000.0, 2000.0, 4000.0)
    printed_side = (
        4.0
        * oracle.SRL_13441_VOLUME_M3
        * (
            _m_from_printed_alpha(temperature_c=20.0, humidity=60.0, bands=bands)
            - _m_from_printed_alpha(temperature_c=20.0, humidity=50.0, bands=bands)
        )
        / oracle.SRL_13441_AREA_M2
    )
    assert printed_side.tolist() == pytest.approx(
        [0.0015494, 0.00361527, -0.01575226, -0.10329354], abs=5e-8
    )
    attenuation_with = _library_m(temperature_c=20.0, humidity=60.0, bands=bands)
    attenuation_empty = _library_m(temperature_c=20.0, humidity=50.0, bands=bands)
    with pytest.warns(SuspendedCeilingWarning, match="4.2.1"):
        got = materials.air_absorption_correction(
            volume_m3=oracle.SRL_13441_VOLUME_M3,
            specimen_area_m2=oracle.SRL_13441_AREA_M2,
            attenuation_with=attenuation_with,
            attenuation_empty=attenuation_empty,
        )
    assert got.tolist() == pytest.approx(printed_side.tolist(), abs=5e-9)
    assert float(np.max(np.abs(got))) > AIR_CORRECTION_LIMIT


def test_a_humid_room_stays_inside_the_cap_at_every_band() -> None:
    """EN 16487:2014 4.2.1 on the room SP report P302808 prints.

    V = 200 m3 and S = 10,8 m2 from the report. Its printed climates are
    20 degC / 90 % empty and 24 degC / 89 % on the object; Table 1 is tabulated
    on a 5 degC grid with humidity columns every ten points, so the 25 degC /
    90 % cell stands in for the second of them. At 90 % the printed attenuation
    rises with temperature from 500 Hz to 4 kHz and falls at 125 Hz and 250 Hz,
    so the substitution overstates the correction in the four bands where it is
    positive, 2 kHz the largest of them, and the overstated figure is still
    0,033 against a cap of 0,05.
    """
    bands = (125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0)
    printed_side = (
        4.0
        * oracle.SP_P302808_VOLUME_M3
        * (
            _m_from_printed_alpha(temperature_c=25.0, humidity=90.0, bands=bands)
            - _m_from_printed_alpha(temperature_c=20.0, humidity=90.0, bands=bands)
        )
        / oracle.SP_P302808_AREA_M2
    )
    assert printed_side.tolist() == pytest.approx(
        [-0.00063108, -0.00153506, 0.00153506, 0.01944405, 0.033089, 0.01023371],
        abs=5e-8,
    )
    with warnings.catch_warnings():
        warnings.simplefilter("error", SuspendedCeilingWarning)
        got = materials.air_absorption_correction(
            volume_m3=oracle.SP_P302808_VOLUME_M3,
            specimen_area_m2=oracle.SP_P302808_AREA_M2,
            attenuation_with=_library_m(temperature_c=25.0, humidity=90.0, bands=bands),
            attenuation_empty=_library_m(
                temperature_c=20.0, humidity=90.0, bands=bands
            ),
        )
    assert got.tolist() == pytest.approx(printed_side.tolist(), abs=5e-9)
    assert float(np.max(np.abs(got))) < AIR_CORRECTION_LIMIT


def test_an_accredited_certificate_reproduces_from_its_printed_inputs() -> None:
    """EN ISO 354:2003 Formulae (8) and (9), as 4.2.1 uses them.

    SRL certificate 13441 prints the room, the specimen, both climates with
    their own barometric pressures, and per band the two reverberation times
    beside the coefficient the laboratory derived from them. Nothing else is
    given to the library, and the six octave centres come back at the 0,01 the
    certificate prints.
    """
    empty_temperature_c, empty_humidity, empty_pressure_mbar = oracle.SRL_13441_EMPTY
    temperature_c, humidity, pressure_mbar = oracle.SRL_13441_WITH_SPECIMEN
    got = materials.absorption_coefficient(
        oracle.SRL_13441_T1_S,
        oracle.SRL_13441_T2_S,
        oracle.SRL_13441_VOLUME_M3,
        oracle.SRL_13441_AREA_M2,
        temperature1_c=empty_temperature_c,
        temperature2_c=temperature_c,
        m1=environment.air_attenuation_m(
            oracle.SRL_13441_BANDS_HZ,
            temperature_c=empty_temperature_c,
            relative_humidity_percent=empty_humidity,
            atmospheric_pressure_kpa=empty_pressure_mbar / 10.0,
        ),
        m2=environment.air_attenuation_m(
            oracle.SRL_13441_BANDS_HZ,
            temperature_c=temperature_c,
            relative_humidity_percent=humidity,
            atmospheric_pressure_kpa=pressure_mbar / 10.0,
        ),
    )
    assert got.tolist() == pytest.approx(list(oracle.SRL_13441_ALPHA_S), abs=0.005)


def test_the_air_term_is_what_makes_that_certificate_reproduce() -> None:
    """Dropping ``m`` misses three of the six bands, by 0,016 at 4 kHz.

    The reason the test above is a check of the chain 4.2.1 governs rather than
    of Sabine arithmetic: the certificate's own 41 % and 44 % relative humidity
    put enough air absorption in the room to move the answer past the digit the
    certificate prints.
    """
    without_air = materials.absorption_coefficient(
        oracle.SRL_13441_T1_S,
        oracle.SRL_13441_T2_S,
        oracle.SRL_13441_VOLUME_M3,
        oracle.SRL_13441_AREA_M2,
        temperature1_c=oracle.SRL_13441_EMPTY[0],
        temperature2_c=oracle.SRL_13441_WITH_SPECIMEN[0],
    )
    missed = [
        band
        for band, value, printed in zip(
            oracle.SRL_13441_BANDS_HZ,
            without_air.tolist(),
            oracle.SRL_13441_ALPHA_S,
            strict=True,
        )
        if abs(value - printed) > 0.005
    ]
    assert missed == [250.0, 2000.0, 4000.0]


def test_real_arrangements_against_the_printed_geometry() -> None:
    """4.1.1.1.1 and 4.1.1.2.3.1, printed folios 6 and 9, on real specimens.

    Two accredited laboratories, a third that names this test code on its face
    as prEN 16487, and the reverberation room of G. van Hout, The Acoustic
    Performance of Suspended Ceiling Systems, master of engineering thesis,
    University of Canterbury, 2016, whose E-400 mounting and 3 600 mm by
    3 000 mm, 10,8 m2 specimen are printed on page 27 (PDF page 45). The area is a target and not a tolerance, so the
    0,30 m2 the CSTB specimen falls short by is reported and not failed.
    """
    # Report -> (area in m2, overall depth in mm) and the two printed
    # consequences: the departure from 10,80 m2, and whether the arrangement
    # is the one the CE marking data rests on.
    arrangements = {
        "SRL 13441, E-200": (
            (oracle.SRL_13441_AREA_M2, oracle.SRL_13441_DEPTH_MM),
            (-0.10, True),
        ),
        "SP P302808, 200 mm": (
            (oracle.SP_P302808_AREA_M2, oracle.SP_P302808_DEPTH_MM),
            (0.00, True),
        ),
        "CSTB AC14-26051052/10, E-50": (
            (oracle.CSTB_AC14_AREA_M2, oracle.CSTB_AC14_DEPTH_MM),
            (-0.30, False),
        ),
        "van Hout 2016, E-400": (
            (oracle.VAN_HOUT_AREA_M2, oracle.VAN_HOUT_DEPTH_MM),
            (0.00, False),
        ),
    }
    for report, (
        (area_m2, depth_mm),
        (area_error_m2, ce_marking),
    ) in arrangements.items():
        with warnings.catch_warnings():
            # A depth other than 200 mm is reported by the clause, which is the
            # verdict under test rather than a surprise.
            warnings.simplefilter("ignore", SuspendedCeilingWarning)
            got = materials.check_ceiling_specimen(
                area_m2=area_m2, mounting="E", depth_mm=depth_mm
            )
        assert got.area_error_m2 == pytest.approx(area_error_m2, abs=5e-9), report
        assert got.ce_marking_depth is ce_marking, report
        assert got.satisfied is True, report


def test_the_humidity_floor_against_real_room_climates() -> None:
    """4.2.2, printed folio 12: "at least 50 %", on three printed rooms.

    None of the three is an EN 16487 report, so the dry one is an illustration
    of the clause rather than a defect anyone reported: a UKAS laboratory
    measured a suspended ceiling at 41 % and 44 %, under conditions this test
    code would not accept.
    """
    # Report -> (area in m2, overall depth in mm) and the two printed climates,
    # so each climate is judged together with the arrangement it was measured on.
    climates = {
        "SRL 13441": (
            (oracle.SRL_13441_AREA_M2, oracle.SRL_13441_DEPTH_MM),
            (oracle.SRL_13441_EMPTY[1], oracle.SRL_13441_WITH_SPECIMEN[1]),
        ),
        "CSTB AC14-26051052/10": (
            (oracle.CSTB_AC14_AREA_M2, oracle.CSTB_AC14_DEPTH_MM),
            (oracle.CSTB_AC14_EMPTY[1], oracle.CSTB_AC14_WITH_SPECIMEN[1]),
        ),
        "SP P302808": (
            (oracle.SP_P302808_AREA_M2, oracle.SP_P302808_DEPTH_MM),
            (oracle.SP_P302808_EMPTY[1], oracle.SP_P302808_WITH_SPECIMEN[1]),
        ),
    }
    below_the_floor = {"SRL 13441"}
    for report, ((area_m2, depth_mm), printed) in climates.items():
        with warnings.catch_warnings():
            # The dry room, and the depth of the E-50, are reported by the
            # clause, which is the verdict under test rather than a surprise.
            warnings.simplefilter("ignore", SuspendedCeilingWarning)
            got = materials.check_ceiling_specimen(
                area_m2=area_m2,
                mounting="E",
                depth_mm=depth_mm,
                relative_humidity_percent=printed,
            )
        assert got.humidity_ok is (report not in below_the_floor), report
        assert got.satisfied is (report not in below_the_floor), report


@pytest.mark.parametrize(
    ("report", "alpha_p", "alpha_w", "indicator", "absorption_class"),
    [
        ("SP P302808", oracle.SP_P302808_ALPHA_P, *oracle.SP_P302808_RATING),
        ("CSTB AC14-26051052/10", oracle.CSTB_AC14_ALPHA_P, *oracle.CSTB_AC14_RATING),
    ],
)
def test_the_printed_rating_of_a_real_suspended_ceiling(
    report: str,
    alpha_p: tuple[float, ...],
    alpha_w: float,
    indicator: str,
    absorption_class: str,
) -> None:
    """EN 16487 Table 1 footnote b, through EN ISO 11654:1997 4.2.

    Footnote b qualifies the weighted figure as "calculated without any
    rounding in the calculation chain in EN ISO 11654", so the chain is named
    by this test code. The CSTB case is the discriminating one: both
    high-frequency bands sit exactly 0,25 above the shifted curve, so a strict
    comparison prints M where the page prints MH, and the accepted shift leaves
    an unfavourable sum of exactly 0,10, so a strict comparison there gives
    0,65 where the page prints 0,70.
    """
    got = materials.weighted_absorption(list(alpha_p))
    assert got.alpha_w == pytest.approx(alpha_w, abs=5e-4), report
    assert got.shape_indicator == indicator, report
    assert got.absorption_class == absorption_class, report


def test_the_one_third_octave_step_of_the_rating_on_a_real_certificate() -> None:
    """EN ISO 11654:1997 4.1 and 4.2 on SRL certificate 13441.

    The certificate prints the fifteen one-third-octave coefficients, the five
    octave ones it formed from them, and the rating: alpha_w = 0,95, class A,
    with no shape indicator.
    """
    alpha_p = materials.practical_absorption_coefficient(
        oracle.SRL_13441_THIRD_OCTAVE_ALPHA_S
    )
    assert alpha_p.tolist() == pytest.approx(list(oracle.SRL_13441_ALPHA_P), abs=5e-4)
    rated = materials.weighted_absorption_from_third_octave(
        oracle.SRL_13441_THIRD_OCTAVE_ALPHA_S
    )
    alpha_w, indicator, absorption_class = oracle.SRL_13441_RATING
    assert rated.alpha_w == pytest.approx(alpha_w, abs=5e-4)
    assert rated.shape_indicator == indicator
    assert rated.absorption_class == absorption_class
