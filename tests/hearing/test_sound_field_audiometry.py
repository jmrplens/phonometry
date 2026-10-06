#  Copyright (c) 2026. Jose Manuel Requena Plens
"""ISO 8253-2:2009: the sound field of an audiometric test room."""

from __future__ import annotations

import dataclasses
import math

import numpy as np
import pytest
from reference_data import (
    ISO8253_1_TABLE_4,
    ISO8253_2_BANDS_HZ,
    ISO8253_2_BINAURAL_OFFSET_DB,
    ISO8253_2_TABLE_1,
    ISO8253_2_TABLE_2,
    ISO8253_2_TABLE_B1,
    ISO8253_2_TABLE_B1_HZ,
)

from phonometry import hearing

_ELEVEN = 11
_SIX = ("front", "back", "left", "right", "up", "down")
_FOUR = ("left", "right", "up", "down")


def test_the_tables_are_the_printed_ones() -> None:
    assert hearing.SOUND_FIELD_AMBIENT_BANDS_HZ == ISO8253_2_BANDS_HZ
    for lowest, column in ISO8253_2_TABLE_2.items():
        np.testing.assert_array_equal(
            hearing.SOUND_FIELD_AMBIENT_LIMITS_DB[lowest], column
        )
    assert hearing.DIFFUSE_FIELD_VARIATION_LIMITS == ISO8253_2_TABLE_1
    assert hearing.INCIDENCE_CORRECTION_FREQUENCIES_HZ == ISO8253_2_TABLE_B1_HZ
    for angle, column in ISO8253_2_TABLE_B1.items():
        np.testing.assert_array_equal(hearing.INCIDENCE_CORRECTIONS_DB[angle], column)


def test_the_sound_field_limits_are_the_bone_limits_less_three_decibels() -> None:
    """Footnote a: derived from ISO 8253-1 for binaural listening."""
    shared = len(ISO8253_1_TABLE_4[125.0])
    for lowest, column in ISO8253_1_TABLE_4.items():
        np.testing.assert_array_equal(
            hearing.SOUND_FIELD_AMBIENT_LIMITS_DB[lowest][:shared],
            np.subtract(column, ISO8253_2_BINAURAL_OFFSET_DB),
        )


def test_table_b1_starts_at_125_hz() -> None:
    """The paragraph announces 200 Hz; the table prints 125 Hz and 160 Hz too."""
    corrections = hearing.incidence_correction([125.0, 160.0], incidence_angle_deg=45)
    np.testing.assert_array_equal(corrections, [0.5, 1.0])
    at_4k = hearing.incidence_correction(4000.0, incidence_angle_deg=90.0)
    np.testing.assert_array_equal(at_4k, [-0.5])


@pytest.mark.parametrize(
    ("frequencies", "angle", "match"),
    [([1000.0], 30.0, "45 or 90"), ([1100.0], 45.0, "1100 Hz")],
)
def test_the_corrections_refuse_what_table_b1_does_not_print(
    frequencies: list[float], angle: float, match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        hearing.incidence_correction(frequencies, incidence_angle_deg=angle)


# ---------------------------------------------------------------------------
# The diffuse sound field (5.3)
# ---------------------------------------------------------------------------


def _diffuse(deviation: float = 1.0, *, right: float | None = None) -> dict:
    positions = {name: [deviation] * _ELEVEN for name in _SIX}
    if right is not None:
        positions["right"] = [right] * _ELEVEN
    return positions


def test_a_diffuse_field_passes_when_both_conditions_hold() -> None:
    directional = [[0.0] * _ELEVEN, [4.5] * _ELEVEN]
    check = hearing.check_diffuse_sound_field(
        _diffuse(),
        [0.0] * _ELEVEN,
        directional_levels_db=directional,
        front_to_random_index_db=5.0,
    )
    assert check.passes
    assert check.directionality_judged
    # Below 500 Hz the directional test does not apply.
    assert math.isnan(check.directional_variation_db[0])
    np.testing.assert_array_equal(check.allowable_variation_db[2:], 5.0)


def test_table_1_limits_the_variation_by_the_index() -> None:
    """An index of 4,5 dB allows 4,5 dB, and 4,7 dB still only 4,5 dB."""
    directional = [[0.0] * _ELEVEN, [4.8] * _ELEVEN]
    for index in (4.5, 4.7):
        check = hearing.check_diffuse_sound_field(
            _diffuse(),
            [0.0] * _ELEVEN,
            directional_levels_db=directional,
            front_to_random_index_db=index,
        )
        assert not check.passes
        np.testing.assert_array_equal(check.allowable_variation_db[2:], 4.5)


def test_the_six_positions_and_the_ear_sides_are_judged() -> None:
    directional = [[0.0] * _ELEVEN, [1.0] * _ELEVEN]
    loose = hearing.check_diffuse_sound_field(
        _diffuse(2.6),
        [0.0] * _ELEVEN,
        directional_levels_db=directional,
        front_to_random_index_db=5.0,
    )
    assert not np.any(loose.uniform)
    assert not loose.passes
    lopsided = hearing.check_diffuse_sound_field(
        _diffuse(-1.5, right=1.6),
        [0.0] * _ELEVEN,
        directional_levels_db=directional,
        front_to_random_index_db=5.0,
    )
    assert np.all(lopsided.uniform)
    assert not np.any(lopsided.balanced)
    assert not lopsided.passes


def test_without_the_directional_test_the_field_does_not_pass() -> None:
    check = hearing.check_diffuse_sound_field(_diffuse(), [0.0] * _ELEVEN)
    assert np.all(check.uniform)
    assert np.all(check.balanced)
    assert not check.directionality_judged
    assert not check.passes


def test_a_band_where_the_microphone_is_unsuitable_is_not_judged() -> None:
    index = np.full(_ELEVEN, 6.0)
    index[5] = 3.5
    index[6] = math.nan
    check = hearing.check_diffuse_sound_field(
        _diffuse(),
        [0.0] * _ELEVEN,
        directional_levels_db=[[0.0] * _ELEVEN, [1.0] * _ELEVEN],
        front_to_random_index_db=index,
    )
    assert not check.directional_judged[5]
    assert not check.directional_judged[6]
    assert not check.passes


@pytest.mark.parametrize(
    ("positions", "kwargs", "match"),
    [
        ({name: [0.0] * _ELEVEN for name in _FOUR}, {}, "front, back"),
        (None, {"directional_levels_db": [[0.0] * _ELEVEN] * 2}, "together"),
        (
            None,
            {
                "directional_levels_db": [[0.0] * _ELEVEN] * 2,
                "front_to_random_index_db": 3.9,
            },
            "not suitable",
        ),
        (
            None,
            {
                "directional_levels_db": [[0.0] * _ELEVEN],
                "front_to_random_index_db": 5.0,
            },
            "at least two finite readings",
        ),
        (None, {"frequencies": [1000.0] * _ELEVEN}, "increasing"),
    ],
)
def test_the_diffuse_check_refuses_what_5_3_cannot_judge(
    positions: dict | None, kwargs: dict[str, object], match: str
) -> None:
    given = _diffuse() if positions is None else positions
    with pytest.raises(ValueError, match=match):
        hearing.check_diffuse_sound_field(given, [0.0] * _ELEVEN, **kwargs)  # type: ignore[arg-type]


def test_the_diffuse_check_has_no_truth_value() -> None:
    check = hearing.check_diffuse_sound_field(_diffuse(), [0.0] * _ELEVEN)
    with pytest.raises(TypeError, match="passes"):
        bool(check)


# ---------------------------------------------------------------------------
# The free and quasi-free sound fields (5.2, 5.4)
# ---------------------------------------------------------------------------


def _free(
    deviation: float, distance: float, offset: float
) -> tuple[dict[str, list[float]], list[float], list[float], list[float]]:
    """A field whose axial pair follows the inverse distance law exactly."""
    law = 20.0 * math.log10((distance + offset) / (distance - offset))
    lateral = {name: [deviation] * _ELEVEN for name in _FOUR}
    return lateral, [0.0] * _ELEVEN, [law / 2] * _ELEVEN, [-law / 2] * _ELEVEN


def test_the_axial_pair_is_judged_against_the_inverse_distance_law() -> None:
    lateral, reference, front, back = _free(0.5, 1.5, 0.15)
    check = hearing.check_free_sound_field(
        lateral,
        reference,
        front_levels_db=front,
        back_levels_db=back,
        loudspeaker_distance_m=1.5,
    )
    assert check.inverse_distance_difference_db == pytest.approx(
        20.0 * math.log10(1.65 / 1.35)
    )
    np.testing.assert_allclose(check.inverse_distance_deviation_db, 0.0, atol=1e-12)
    assert check.passes


def test_the_axial_offset_and_the_law_are_read_from_the_field() -> None:
    """ISO 8253-2:2009 5.2 c) and 5.4 c): 0,15 m and 0,10 m, as printed.

    PDF pages 12 and 13, printed folios 6 and 7. Neither the offset nor the
    inverse distance difference is a field, so a check cannot be judged
    against another offset or another law.
    """
    lateral, reference, front, back = _free(0.0, 1.5, 0.15)
    check = hearing.check_free_sound_field(
        lateral,
        reference,
        front_levels_db=front,
        back_levels_db=back,
        loudspeaker_distance_m=1.5,
    )
    names = {f.name for f in dataclasses.fields(check)}
    assert not names & {"axis_offset_m", "inverse_distance_difference_db"}
    assert check.axis_offset_m == pytest.approx(0.15)
    quasi = dataclasses.replace(check, field="quasi-free")
    assert quasi.axis_offset_m == pytest.approx(0.10)
    assert quasi.inverse_distance_difference_db == pytest.approx(
        20.0 * math.log10(1.6 / 1.4)
    )


def test_a_field_the_clause_does_not_name_is_refused() -> None:
    lateral, reference, front, back = _free(0.0, 1.5, 0.15)
    check = hearing.check_free_sound_field(
        lateral,
        reference,
        front_levels_db=front,
        back_levels_db=back,
        loudspeaker_distance_m=1.5,
    )
    with pytest.raises(ValueError, match="'field' must be one of"):
        dataclasses.replace(check, field="diffuse")


def test_the_free_field_tolerance_widens_above_4_khz() -> None:
    """±1 dB up to and including 4 kHz, ±2 dB above (5.2 b))."""
    lateral, reference, front, back = _free(1.5, 2.0, 0.15)
    check = hearing.check_free_sound_field(
        lateral,
        reference,
        front_levels_db=front,
        back_levels_db=back,
        loudspeaker_distance_m=2.0,
    )
    np.testing.assert_array_equal(check.usable_frequencies, [6000.0, 8000.0])
    assert not check.passes
    at_4k = list(check.frequencies).index(4000.0)
    assert check.lateral_tolerance_db[at_4k] == 1.0


def test_the_ear_sides_of_a_free_field_are_limited_above_4_khz_only() -> None:
    lateral, reference, front, back = _free(0.0, 2.0, 0.15)
    lateral["left"] = [-0.9] * 9 + [-1.8] * 2
    lateral["right"] = [0.9] * 9 + [1.8] * 2
    check = hearing.check_free_sound_field(
        lateral,
        reference,
        front_levels_db=front,
        back_levels_db=back,
        loudspeaker_distance_m=2.0,
    )
    assert np.all(check.balanced[:9])
    assert not np.any(check.balanced[9:])


def test_a_loudspeaker_nearer_than_one_metre_fails_the_field() -> None:
    lateral, reference, front, back = _free(0.0, 0.8, 0.15)
    check = hearing.check_free_sound_field(
        lateral,
        reference,
        front_levels_db=front,
        back_levels_db=back,
        loudspeaker_distance_m=0.8,
    )
    assert np.all(check.compliant)
    assert not check.distance_adequate
    assert not check.passes


def test_the_quasi_free_field_uses_its_own_offsets_and_tolerance() -> None:
    lateral, reference, front, back = _free(1.9, 1.2, 0.10)
    check = hearing.check_quasi_free_sound_field(
        lateral,
        reference,
        front_levels_db=front,
        back_levels_db=back,
        loudspeaker_distance_m=1.2,
    )
    assert check.field == "quasi-free"
    assert check.axis_offset_m == 0.10
    assert check.passes
    np.testing.assert_array_equal(check.usable_frequencies, check.frequencies)


def test_a_quasi_free_field_off_the_law_narrows_its_usable_range() -> None:
    lateral, reference, front, back = _free(0.0, 1.2, 0.10)
    off = np.asarray(front, dtype=float)
    off[:3] += 1.5
    check = hearing.check_quasi_free_sound_field(
        lateral,
        reference,
        front_levels_db=off,
        back_levels_db=back,
        loudspeaker_distance_m=1.2,
    )
    assert check.usable_frequencies[0] == 750.0
    assert not check.passes


@pytest.mark.parametrize(
    ("distance", "match"), [(0.1, "larger than the 0.15 m"), (math.inf, "finite")]
)
def test_the_free_check_refuses_an_impossible_distance(
    distance: float, match: str
) -> None:
    lateral, reference, front, back = _free(0.0, 2.0, 0.15)
    with pytest.raises(ValueError, match=match):
        hearing.check_free_sound_field(
            lateral,
            reference,
            front_levels_db=front,
            back_levels_db=back,
            loudspeaker_distance_m=distance,
        )


def test_the_free_check_needs_the_frequencies_of_other_bands() -> None:
    lateral = {name: [0.0] * 3 for name in _FOUR}
    with pytest.raises(ValueError, match="needs 'frequencies'"):
        hearing.check_free_sound_field(
            lateral,
            [0.0] * 3,
            front_levels_db=[1.0] * 3,
            back_levels_db=[0.0] * 3,
            loudspeaker_distance_m=2.0,
        )


def test_the_free_check_has_no_truth_value() -> None:
    lateral, reference, front, back = _free(0.0, 2.0, 0.15)
    check = hearing.check_free_sound_field(
        lateral,
        reference,
        front_levels_db=front,
        back_levels_db=back,
        loudspeaker_distance_m=2.0,
    )
    with pytest.raises(TypeError, match="passes"):
        bool(check)
