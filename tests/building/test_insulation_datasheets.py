#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The sound reduction and impact improvement rows of a laboratory report.

The oracles are the worked examples of the standards, shared with the rating
tests through ``reference_data``: ISO 717-1:2020 Annex C, Tables C.1 and C.2
(the element rated Rw(C;Ctr) = 30(-2;-3) dB, and over 50 Hz to 5 kHz with
C50-5000 = -2 dB and Ctr,50-5000 = -4 dB), and ISO 717-2:2020 Annex C,
Table C.2 (the covering rated to Delta Lw = 15 dB, with CI,Delta = -9 dB
from the Table 4 reference floor, see ``docs/ERRATA.md``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import matplotlib as mpl
import numpy as np
import pytest
import reference_data as ref

from phonometry import building

if TYPE_CHECKING:
    from collections.abc import Callable

mpl.use("Agg")

_BANDS = (50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000)
_BANDS += (1250, 1600, 2000, 2500, 3150, 4000, 5000)
_RATED = _BANDS[3:19]


def _reduction(
    values: list[float], bands: tuple[int, ...], **extra: Any
) -> building.SoundReductionSpectrum:
    cells = {
        f"sound_reduction_index_{band}_db": value
        for band, value in zip(bands, values, strict=True)
    }
    return building.SoundReductionSpectrum(
        name="Wall", source="A test", **cells, **extra
    )


def _improvement(**extra: Any) -> building.ImpactImprovementSpectrum:
    cells = {
        f"impact_improvement_{band}_db": value
        for band, value in zip(_RATED, ref.ISO717_2_ANNEX_C2_DELTA_L, strict=True)
    }
    return building.ImpactImprovementSpectrum(
        name="Covering", source="A test", **cells, **extra
    )


def test_the_sound_reduction_row_rates_as_table_c1_prints() -> None:
    rating = _reduction(ref.ISO717_1_ANNEX_C_R, _RATED).rating()
    expected = ref.ISO717_1_ANNEX_C_EXPECTED
    assert (rating.rating, rating.c, rating.ctr) == (
        expected["rw"],
        expected["c"],
        expected["ctr"],
    )
    assert rating.c_50_5000 is None
    assert rating.core.rating == expected["rw"]


def test_the_enlarged_range_is_rated_when_the_row_prints_it() -> None:
    rating = _reduction(ref.ISO717_1_ANNEX_C2_R_50_5000, _BANDS).rating()
    expected = ref.ISO717_1_ANNEX_C2_EXPECTED
    assert (rating.rating, rating.c, rating.ctr) == (30, -2, -3)
    assert rating.c_50_5000 == expected["c_50_5000"]
    assert rating.ctr_50_5000 == expected["ctr_50_5000"]
    assert rating.c_100_5000 is not None


def test_an_enlarged_term_with_a_band_missing_is_none() -> None:
    values = list(ref.ISO717_1_ANNEX_C2_R_50_5000)
    bands = _BANDS
    row = _reduction(values[1:], bands[1:])
    rating = row.rating()
    assert rating.c_50_5000 is None
    assert rating.c_50_3150 is None
    assert rating.c_100_5000 is not None


def test_a_missing_core_band_is_refused_with_what_the_report_had() -> None:
    values = list(ref.ISO717_1_ANNEX_C_R)
    row = _reduction(
        values[:5] + values[6:],
        _RATED[:5] + _RATED[6:],
        bounded_below={"sound_reduction_index_315_db"},
        ranges={"sound_reduction_index_315_db": (38.0, None)},
    )
    with pytest.raises(ValueError, match="sound_reduction_index_315_db"):
        row.rating()


def test_printed_ratings_that_follow_leave_no_note() -> None:
    row = _reduction(
        ref.ISO717_1_ANNEX_C2_R_50_5000,
        _BANDS,
        weighted_sound_reduction_index_db=30.0,
        spectrum_adaptation_term_db=-2.0,
        traffic_spectrum_adaptation_term_db=-3.0,
        spectrum_adaptation_term_50_5000_db=-2.0,
        traffic_spectrum_adaptation_term_50_5000_db=-4.0,
    )
    assert row._catalogue_notes() == ()


def test_a_printed_rating_that_does_not_follow_is_noted() -> None:
    row = _reduction(
        ref.ISO717_1_ANNEX_C2_R_50_5000,
        _BANDS,
        weighted_sound_reduction_index_db=31.0,
        traffic_spectrum_adaptation_term_50_5000_db=-5.0,
    )
    assert row._catalogue_notes() == (
        "Rw is printed as 31.0 and the bands give 30 (ISO 717-1 Clause 4.4); "
        "the printed value is kept as printed",
        "Ctr,50-5000 is printed as -5.0 and the bands give -4 (Annex B); the "
        "printed value is kept as printed",
    )


def test_no_note_without_the_rating_bands() -> None:
    row = _reduction([40.0, 41.0], (500, 1000), weighted_sound_reduction_index_db=99.0)
    assert row._catalogue_notes() == ()


def test_the_improvement_row_rates_as_table_c2_prints() -> None:
    rating = _improvement().rating()
    assert rating.delta_lw == ref.ISO717_2_ANNEX_C2_DELTA_LW
    assert rating.ci_delta == ref.ISO717_2_ANNEX_C2_CI_DELTA
    assert rating.ci_r == -11 - ref.ISO717_2_ANNEX_C2_CI_DELTA
    assert rating.band_centers.tolist() == [float(band) for band in _RATED]
    assert rating.improvement.tolist() == ref.ISO717_2_ANNEX_C2_DELTA_L


def test_the_improvement_notes_a_printed_term_that_does_not_follow() -> None:
    row = _improvement(
        weighted_impact_improvement_db=15.0,
        impact_improvement_adaptation_term_db=-9.0,
        reference_floor_adaptation_term_db=-3.0,
    )
    (note,) = row._catalogue_notes()
    assert note.startswith("CI,r is printed as -3.0 and the bands give -2")


def test_the_printed_delta_lw_reaches_the_prediction() -> None:
    """EN 12354-2 Formula 21 takes Delta Lw through printed()."""
    row = _improvement(weighted_impact_improvement_db=15.0)
    result = building.predicted_impact_insulation(
        ln_w_eq=78.0, delta_l_w=row.printed("weighted_impact_improvement_db")
    )
    assert result.l_prime_n_w == pytest.approx(63.0)
    empty = building.ImpactImprovementSpectrum(name="Mat", source="A test")
    with pytest.raises(ValueError, match="weighted_impact_improvement_db"):
        empty.printed("weighted_impact_improvement_db")


def test_the_rating_result_holds_its_terms_together() -> None:
    rating = _improvement().rating()
    with pytest.raises(ValueError, match="ci_r"):
        building.ImpactImprovementRatingResult(
            delta_lw=rating.delta_lw,
            ci_delta=rating.ci_delta,
            ci_r=rating.ci_r + 1,
            band_centers=rating.band_centers,
            improvement=rating.improvement,
        )
    with pytest.raises(ValueError, match="improvement"):
        building.ImpactImprovementRatingResult(
            delta_lw=15,
            ci_delta=-9,
            ci_r=-2,
            band_centers=rating.band_centers,
            improvement=rating.improvement[:5],
        )


@pytest.mark.parametrize("language", ["en", "es"])
def test_the_improvement_rating_plots_its_spectrum_and_numbers(language: str) -> None:
    import matplotlib.pyplot as plt

    rating = _improvement().rating()
    ax = rating.plot(language=language)
    (line,) = ax.get_lines()
    assert line.get_ydata().tolist() == ref.ISO717_2_ANNEX_C2_DELTA_L
    title = ax.get_title()
    assert title.startswith(r"ISO 717-2 $\Delta L_\mathrm{w}$")
    assert title.endswith(") = 15 dB")
    # The signs are the typographic minus of the other ISO 717 renderers.
    assert "$=−9;" in title
    assert "$=−2)" in title
    assert "-" not in title.removeprefix("ISO 717-2")
    fig = ax.figure
    fig.canvas.draw()
    extent = ax.title.get_window_extent()
    assert 0.0 <= extent.x0
    assert extent.x1 <= fig.bbox.width
    plt.close(fig)


def test_the_improvement_plot_keeps_a_negative_band_in_view() -> None:
    """A floating floor's resonance makes Delta L negative in its low bands."""
    import matplotlib.pyplot as plt

    values = [-4.0, -6.0, -2.0, 3.0, 8.0, 12.0, 16.0, 20.0, 24.0, 27.0, 30.0]
    values += [33.0, 35.0, 36.0, 37.0, 38.0]
    cells = {
        f"impact_improvement_{band}_db": value
        for band, value in zip(_RATED, values, strict=True)
    }
    row = building.ImpactImprovementSpectrum(name="Floating floor", source="s", **cells)
    rating = row.rating()
    assert (rating.delta_lw, rating.ci_delta, rating.ci_r) == (18, -13, 2)
    ax = rating.plot()
    bottom, top = ax.get_ylim()
    assert bottom < min(values)
    assert top > max(values)
    plt.close(ax.figure)


def test_the_ratings_read_a_spectrum_band_by_band() -> None:
    row = _reduction(ref.ISO717_1_ANNEX_C2_R_50_5000, _BANDS)
    assert building.weighted_rating(row.spectrum()).rating == 30
    assert building.weighted_rating(row.spectrum(), bands="octave").rating == (
        building.weighted_rating(
            [row.sound_reduction_index_db(b) for b in (125, 250, 500, 1000, 2000)]
        ).rating
    )
    improvement = _improvement().spectrum()
    assert building.weighted_impact_improvement(improvement) == 15
    assert building.impact_improvement_adaptation_term(improvement) == -9
    impact = dict(zip(_RATED, ref.ISO717_2_ANNEX_C1_LN, strict=True))
    assert (
        building.weighted_impact_rating(impact).rating
        == building.weighted_impact_rating(ref.ISO717_2_ANNEX_C1_LN).rating
    )


def test_an_octave_mapping_is_read_as_octaves() -> None:
    octaves = {125: 36.0, 250: 45.0, 500: 52.0, 1000: 55.0, 2000: 56.0, 4000: 60.0}
    by_band = building.weighted_rating(octaves)
    assert by_band.rating == building.weighted_rating(list(octaves.values())[:5]).rating
    assert by_band.band_centers is not None
    assert len(by_band.band_centers) == 5


@pytest.mark.parametrize(
    ("call", "missing"),
    [
        (building.weighted_rating, "160"),
        (building.weighted_impact_rating, "160"),
        (building.weighted_impact_improvement, "160"),
        (building.impact_improvement_adaptation_term, "160"),
    ],
    ids=["airborne", "impact", "improvement", "adaptation"],
)
def test_a_mapping_with_a_band_missing_is_refused(
    call: Callable[[dict[int, float]], object], missing: str
) -> None:
    values = {band: 40.0 for band in _RATED if band != int(missing)}
    with pytest.raises(ValueError, match=f"band of {missing} Hz"):
        call(values)


def test_a_float_keyed_mapping_is_read_like_an_integer_keyed_one() -> None:
    keyed = dict(zip(_RATED, ref.ISO717_1_ANNEX_C_R, strict=True))
    floats = {float(band): value for band, value in keyed.items()}
    assert building.weighted_rating(floats).rating == 30
    with pytest.raises(ValueError, match="'bands' must be"):
        building.weighted_rating(floats, bands="thirds")


def test_the_rows_refuse_a_frequency_that_is_no_band() -> None:
    row = _reduction(ref.ISO717_1_ANNEX_C2_R_50_5000, _BANDS)
    assert row.sound_reduction_index_db(5000) == pytest.approx(29.2)
    assert row.values_at(np.array([501.19])).tolist() == [
        row.sound_reduction_index_db(500)
    ]
    with pytest.raises(ValueError, match="one-third octave band"):
        row.sound_reduction_index_db(6300)
    improvement = _improvement()
    with pytest.raises(ValueError, match="impact_improvement_50_db"):
        improvement.impact_improvement_db(50)
