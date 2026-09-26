#  Copyright (c) 2026. Jose Manuel Requena Plens
"""ISO 4869-3:2007: the insertion loss of an earmuff on an acoustic test fixture."""

from __future__ import annotations

import math

import numpy as np
import pytest
from reference_data import (
    ISO4869_3_B4_EXPANDED_DB,
    ISO4869_3_ISOLATION,
    ISO4869_3_TABLE_1,
    ISO4869_3_TABLE_A1,
    ISO4869_3_TABLE_B1_COMPONENTS_DB,
    ISO4869_3_TABLE_B1_U_DB,
)

from phonometry import hearing

_BANDS = len(hearing.EARMUFF_TEST_BANDS_HZ)
_SIX = ("front", "back", "left", "right", "up", "down")


def test_the_published_tables_are_the_printed_ones() -> None:
    assert hearing.RANDOM_INCIDENCE_VARIATION_LIMITS == ISO4869_3_TABLE_1
    assert dict(hearing.ATF_FRONT_TO_RANDOM_INDEX_DB) == ISO4869_3_TABLE_A1
    budget = hearing.EARMUFF_INSERTION_LOSS_UNCERTAINTY
    assert budget.components_db == ISO4869_3_TABLE_B1_COMPONENTS_DB


def test_table_b1_gives_its_combined_and_expanded_uncertainty() -> None:
    """u = 1,3 dB and U = 2u = 2,6 dB (B.3, B.4)."""
    budget = hearing.EARMUFF_INSERTION_LOSS_UNCERTAINTY
    assert round(budget.combined_db, 1) == ISO4869_3_TABLE_B1_U_DB
    assert round(budget.expanded_db, 1) == ISO4869_3_B4_EXPANDED_DB
    assert budget.combined_db == pytest.approx(math.sqrt(1.63))


def test_the_published_budget_cannot_be_changed() -> None:
    budget = hearing.EARMUFF_INSERTION_LOSS_UNCERTAINTY
    with pytest.raises(AttributeError, match="open_level_db"):
        budget.open_level_db = 0.0  # type: ignore[misc]


def test_a_budget_refuses_a_negative_component() -> None:
    with pytest.raises(ValueError, match="not negative"):
        hearing.InsertionLossUncertaintyBudget(0.5, 1.0, -0.3, 0.5, 0.2)


# ---------------------------------------------------------------------------
# The insertion loss (5.4, Annex B)
# ---------------------------------------------------------------------------


def _fittings() -> tuple[np.ndarray, np.ndarray]:
    """One open level and three fittings of an earmuff, 63 Hz to 8 kHz."""
    open_level = np.full(_BANDS, 85.0)
    loss = np.linspace(8.0, 38.0, _BANDS)
    occluded = np.vstack(
        [open_level - loss - 0.4, open_level - loss, open_level - loss + 0.4]
    )
    return open_level, occluded


def test_the_insertion_loss_is_the_open_level_less_the_occluded_one() -> None:
    open_level, occluded = _fittings()
    result = hearing.earmuff_insertion_loss(open_level, occluded)
    np.testing.assert_allclose(result.insertion_loss_db, np.linspace(8.0, 38.0, _BANDS))
    np.testing.assert_allclose(
        result.repetition_insertion_loss_db[0] - result.repetition_insertion_loss_db[2],
        0.8,
    )
    assert result.repetitions == 3
    assert result.repetitions_sufficient


def test_the_level_uncertainties_come_from_the_repetitions() -> None:
    """B.3: the standard deviation of the mean; one open reading takes 0,5 dB."""
    open_level, occluded = _fittings()
    result = hearing.earmuff_insertion_loss(open_level, occluded)
    np.testing.assert_allclose(result.occluded_uncertainty_db, 0.4 / math.sqrt(3.0))
    np.testing.assert_array_equal(result.open_uncertainty_db, 0.5)
    expected = math.sqrt(
        0.5**2 + (0.4 / math.sqrt(3.0)) ** 2 + 0.3**2 + 0.5**2 + 0.2**2
    )
    np.testing.assert_allclose(result.standard_uncertainty_db, expected)
    np.testing.assert_allclose(result.expanded_uncertainty_db, 2.0 * expected)
    budget = result.budget(1000.0)
    assert budget.combined_db == pytest.approx(expected)


def test_a_single_fitting_takes_the_typical_values_of_table_b1() -> None:
    open_level, occluded = _fittings()
    result = hearing.earmuff_insertion_loss(open_level, occluded[1])
    assert not result.repetitions_sufficient
    np.testing.assert_allclose(result.standard_uncertainty_db, math.sqrt(1.63))


def test_the_report_rounds_to_a_tenth_of_a_decibel() -> None:
    open_level = np.full(_BANDS, 85.0)
    occluded = open_level - np.linspace(10.04, 10.25, _BANDS)
    reported = hearing.earmuff_insertion_loss(open_level, occluded).reported_db
    assert reported[0] == pytest.approx(10.0)
    assert reported[-1] == pytest.approx(10.3)


def test_the_isolation_cup_must_read_ten_decibels_lower() -> None:
    """5.3: exactly 10 dB lower is enough, 9,9 dB lower is not."""
    open_level, occluded = _fittings()
    cup = occluded.mean(axis=0) - 12.0
    cup[0] = occluded.mean(axis=0)[0] - 10.0
    cup[-1] = occluded.mean(axis=0)[-1] - 9.9
    result = hearing.earmuff_insertion_loss(
        open_level, occluded, isolation_cup_levels_db=cup
    )
    assert result.floor_adequate is not None
    assert np.all(result.floor_adequate[:-1])
    assert not result.floor_adequate[-1]
    bare = hearing.earmuff_insertion_loss(open_level, occluded)
    assert bare.floor_adequate is None
    assert bare.floor_margin_db is None


def test_the_signal_must_stay_steady_and_its_response_smooth() -> None:
    _open_level, occluded = _fittings()
    drifting = np.vstack([np.full(_BANDS, 85.0), np.full(_BANDS, 86.5)])
    result = hearing.earmuff_insertion_loss(drifting, occluded)
    assert not np.any(result.level_stable)
    np.testing.assert_allclose(result.level_drift_db, 1.5)
    assert result.response_smooth
    stepped = np.full(_BANDS, 85.0)
    stepped[10:] = 91.0
    assert not hearing.earmuff_insertion_loss(stepped, occluded).response_smooth


@pytest.mark.parametrize(
    ("open_level", "occluded", "kwargs", "match"),
    [
        (np.full(5, 85.0), np.full((3, 6), 60.0), {}, "share their bands"),
        (np.full(5, 85.0), np.full((3, 5), 60.0), {}, "needs 'frequencies'"),
        (np.full(22, math.nan), np.full(22, 60.0), {}, "open_levels_db"),
        (
            np.full(22, 85.0),
            np.full(22, 60.0),
            {"isolation_cup_levels_db": np.zeros(3)},
            "isolation_cup_levels_db",
        ),
        (
            np.full(22, 85.0),
            np.full(22, 60.0),
            {"fixture_uncertainty_db": -0.1},
            "delta",
        ),
    ],
)
def test_the_insertion_loss_refuses_inconsistent_data(
    open_level: np.ndarray, occluded: np.ndarray, kwargs: dict[str, object], match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        hearing.earmuff_insertion_loss(open_level, occluded, **kwargs)  # type: ignore[arg-type]


def test_the_budget_of_a_band_the_measurement_lacks_is_refused() -> None:
    open_level, occluded = _fittings()
    result = hearing.earmuff_insertion_loss(open_level, occluded)
    with pytest.raises(ValueError, match="700 Hz"):
        result.budget(700.0)


# ---------------------------------------------------------------------------
# The test site (5.2)
# ---------------------------------------------------------------------------


def _positions(deviation: float = 1.0) -> dict[str, list[float]]:
    return {name: [deviation] * _BANDS for name in _SIX}


def test_the_random_incidence_field_uses_its_own_table_1() -> None:
    """An index of 4,5 dB allows 4 dB here, where ISO 8253-2 allows 4,5 dB."""
    directional = [[0.0] * _BANDS, [4.2] * _BANDS]
    here = hearing.check_random_incidence_field(
        _positions(),
        [0.0] * _BANDS,
        directional_levels_db=directional,
        front_to_random_index_db=4.5,
    )
    assert not here.passes
    np.testing.assert_array_equal(here.allowable_variation_db[9:], 4.0)
    assert here.standard == "ISO 4869-3 5.2.2"


def test_an_index_of_exactly_five_decibels_allows_five() -> None:
    """The text's 'at least 5 dB' over the table's '> 5'."""
    check = hearing.check_random_incidence_field(
        _positions(),
        [0.0] * _BANDS,
        directional_levels_db=[[0.0] * _BANDS, [5.0] * _BANDS],
        front_to_random_index_db=5.0,
    )
    assert check.passes


def test_the_fixture_serves_as_the_microphone_where_its_index_allows() -> None:
    """Annex A: the ATF reaches 4 dB at 1,25 kHz to 3,15 kHz and above 6 kHz."""
    freqs = hearing.EARMUFF_TEST_BANDS_HZ
    index = [hearing.ATF_FRONT_TO_RANDOM_INDEX_DB.get(f, math.nan) for f in freqs]
    check = hearing.check_random_incidence_field(
        _positions(),
        [0.0] * _BANDS,
        directional_levels_db=[[0.0] * _BANDS, [3.0] * _BANDS],
        front_to_random_index_db=index,
    )
    judged = [
        f
        for f, ok in zip(freqs, check.directional_judged, strict=True)
        if ok and f >= 500
    ]
    assert judged == [1250.0, 1600.0, 2000.0, 2500.0, 3150.0, 6300.0, 8000.0]
    assert not check.passes


def test_the_plane_wave_needs_matched_end_faces_and_a_directional_margin() -> None:
    faces = [[80.0] * _BANDS, [81.5] * _BANDS]
    check = hearing.check_plane_progressive_wave(
        faces,
        facing_levels_db=[80.0] * _BANDS,
        facing_away_levels_db=[68.0] * _BANDS,
        front_to_rear_index_db=18.0,
    )
    assert check.passes
    np.testing.assert_allclose(check.end_face_difference_db, 1.5)
    assert math.isnan(check.front_to_back_db[0])


def test_a_plane_wave_read_with_a_poor_microphone_is_not_judged() -> None:
    faces = [[80.0] * _BANDS, [80.0] * _BANDS]
    check = hearing.check_plane_progressive_wave(
        faces,
        facing_levels_db=[80.0] * _BANDS,
        facing_away_levels_db=[68.0] * _BANDS,
        front_to_rear_index_db=15.0,
    )
    assert not check.directionality_judged
    assert not check.passes
    unread = hearing.check_plane_progressive_wave(faces)
    assert not unread.passes


def test_a_plane_wave_that_folds_back_fails() -> None:
    faces = [[80.0] * _BANDS, [83.0] * _BANDS]
    check = hearing.check_plane_progressive_wave(
        faces,
        facing_levels_db=[80.0] * _BANDS,
        facing_away_levels_db=[75.0] * _BANDS,
        front_to_rear_index_db=20.0,
    )
    assert not np.any(check.end_faces_matched)
    assert not np.any(check.progressive[9:])


@pytest.mark.parametrize(
    ("faces", "kwargs", "match"),
    [
        ([[80.0] * _BANDS] * 3, {}, r"\(2, bands\)"),
        ([[80.0] * _BANDS] * 2, {"facing_levels_db": [80.0] * _BANDS}, "together"),
        (
            [[80.0] * _BANDS] * 2,
            {
                "facing_levels_db": [80.0] * 3,
                "facing_away_levels_db": [70.0] * 3,
                "front_to_rear_index_db": 20.0,
            },
            "one value per band",
        ),
    ],
)
def test_the_plane_wave_check_refuses_inconsistent_data(
    faces: list[list[float]], kwargs: dict[str, object], match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        hearing.check_plane_progressive_wave(faces, **kwargs)  # type: ignore[arg-type]


def test_the_fixture_isolation_follows_the_three_ranges_of_5_1_4() -> None:
    freqs = np.asarray(hearing.EARMUFF_TEST_BANDS_HZ)
    check = hearing.verify_fixture_isolation(
        np.full(_BANDS, 120.0), np.full(_BANDS, 60.0)
    )
    for first, last, least in ISO4869_3_ISOLATION:
        band = (freqs >= first) & (freqs <= last)
        np.testing.assert_array_equal(check.required_db[band], least)
    assert not check.passes
    np.testing.assert_array_equal(check.sufficient, check.required_db <= 60.0)


def test_the_fixture_isolation_asks_nothing_below_63_hz() -> None:
    freqs = [50.0, 63.0, 5000.0]
    check = hearing.verify_fixture_isolation(
        [120.0] * 3, [80.0, 60.0, 60.0], frequencies=freqs
    )
    assert math.isnan(check.required_db[0])
    assert check.passes


def test_the_fixture_isolation_refuses_mismatched_spectra() -> None:
    with pytest.raises(ValueError, match="one spectrum each"):
        hearing.verify_fixture_isolation(
            np.full((2, _BANDS), 120.0), np.full(_BANDS, 60.0)
        )


def test_the_site_checks_have_no_truth_value() -> None:
    plane = hearing.check_plane_progressive_wave([[80.0] * _BANDS] * 2)
    isolation = hearing.verify_fixture_isolation(
        np.full(_BANDS, 120.0), np.full(_BANDS, 50.0)
    )
    for verdict in (plane, isolation):
        with pytest.raises(TypeError, match="passes"):
            bool(verdict)
