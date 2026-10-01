#  Copyright (c) 2026. Jose Manuel Requena Plens
"""What the audiometric test-method figures draw, in both languages."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from phonometry import hearing

if TYPE_CHECKING:
    from collections.abc import Iterator

    from matplotlib.axes import Axes

pytest.importorskip("matplotlib")


@pytest.fixture(autouse=True)
def _agg() -> Iterator[None]:
    import matplotlib as mpl

    mpl.use("Agg")
    yield
    import matplotlib.pyplot as plt

    plt.close("all")


def _labels(ax: Axes) -> list[str]:
    return ax.get_legend_handles_labels()[1]


def _line(ax: Axes, label: str):  # noqa: ANN202 - a matplotlib Line2D
    return next(line for line in ax.lines if line.get_label() == label)


def test_the_room_figure_marks_only_the_bands_over_their_limit() -> None:
    levels = np.asarray(hearing.AIR_CONDUCTION_AMBIENT_LIMITS_DB[125.0]) - 1.0
    levels[[3, 20]] += 4.0
    ax = hearing.check_audiometric_ambient_noise(levels).plot()
    crosses = _line(ax, "exceeds the limit")
    np.testing.assert_array_equal(crosses.get_xdata(), [63.0, 3150.0])
    assert (
        ax.get_title()
        == "ISO 8253-1 test room, air conduction (supra-aural): does not qualify"
    )
    quiet = hearing.check_audiometric_ambient_noise(
        np.full(27, -5.0), presentation="sound field"
    ).plot(language="es")
    assert "exceeds the limit" not in _labels(quiet)
    assert quiet.get_title() == "ISO 8253-2 sala de ensayo, campo sonoro: cumple"


def test_the_ascending_figure_rings_the_end_of_every_ascent() -> None:
    result = hearing.ascending_method_threshold(
        presentation_levels_db=[20, 25, 30, 20, 25, 30, 20, 25, 30],
        responses=[0, 0, 1, 0, 0, 1, 0, 0, 1],
    )
    ax = result.plot()
    ends = _line(ax, "end of an ascent")
    np.testing.assert_array_equal(ends.get_xdata(), [3, 6, 9])
    assert "threshold 30 dB" in _labels(ax)
    assert ax.get_title() == "ISO 8253-1 ascending method: threshold 30 dB"
    pending = hearing.ascending_method_threshold([30.0]).plot(language="es")
    assert pending.get_title() == "ISO 8253-1 método ascendente: aún sin determinar"


def test_the_automatic_figure_greys_the_ignored_reversals() -> None:
    result = hearing.automatic_audiometry_threshold(
        [30, 20, 30, 28, 30, 20, 30, 20, 30, 20]
    )
    ax = result.plot()
    ignored = _line(ax, "ignored reversal")
    np.testing.assert_array_equal(ignored.get_xdata(), [1, 3, 4, 5])
    assert ax.get_title() == "ISO 8253-1 automatic recording: threshold 25 dB"


def test_the_sweep_figure_draws_hearing_level_downwards() -> None:
    result = hearing.sweep_audiometry_threshold(
        np.geomspace(500.0, 4000.0, 12), [30.0, 20.0] * 6
    )
    ax = result.plot(language="es")
    assert ax.yaxis_inverted()
    assert ax.get_ylabel() == "Nivel de audición [dB]"
    squares = _line(ax, "umbral en la frecuencia")
    np.testing.assert_array_equal(squares.get_ydata(), result.threshold_db)


def test_the_budget_figure_draws_one_bar_per_component() -> None:
    ax = hearing.audiometric_uncertainty(1000.0).plot(language="es")
    heights = [patch.get_height() for patch in ax.patches]
    np.testing.assert_allclose(
        heights, hearing.audiometric_uncertainty(1000.0).components_db
    )
    # A.6 reports U rounded to the nearest full decibel: Table A.2's 10 dB.
    assert ax.get_title() == "ISO 8253-1 anexo A: $u$ = 4,9 dB, $U$ = 10 dB"
    assert hearing.audiometric_uncertainty(1000.0).plot().get_title() == (
        "ISO 8253-1 Annex A: $u$ = 4.9 dB, $U$ = 10 dB"
    )
    il = hearing.EARMUFF_INSERTION_LOSS_UNCERTAINTY.plot()
    assert len(il.patches) == 5
    assert il.get_title() == "ISO 4869-3 Annex B: $u$ = 1.3 dB, $U$ = 2.6 dB"


def test_the_free_field_figure_limits_the_ear_sides_above_4_khz_only() -> None:
    check = hearing.check_free_sound_field(
        dict.fromkeys(("left", "right", "up", "down"), [0.5] * 11),
        [0.0] * 11,
        front_levels_db=[1.3] * 11,
        back_levels_db=[0.0] * 11,
        loudspeaker_distance_m=2.0,
    )
    ax = check.plot()
    limit = _line(ax, "3 dB limit")
    np.testing.assert_array_equal(limit.get_xdata(), [6000.0, 8000.0])
    quasi = hearing.check_quasi_free_sound_field(
        dict.fromkeys(("left", "right", "up", "down"), [0.5] * 11),
        [0.0] * 11,
        front_levels_db=[1.3] * 11,
        back_levels_db=[0.0] * 11,
        loudspeaker_distance_m=2.0,
    ).plot(language="es")
    assert "límite de 3 dB" not in _labels(quasi)
    assert quasi.get_title().startswith("ISO 8253-2 campo cuasi libre")


def test_the_diffuse_figure_says_when_the_directional_test_is_missing() -> None:
    check = hearing.check_diffuse_sound_field(
        dict.fromkeys(("front", "back", "left", "right", "up", "down"), [0.5] * 11),
        [0.0] * 11,
    )
    ax = check.plot()
    assert ax.get_title() == "ISO 8253-2 diffuse field: not judged in every band"
    assert "directional variation" not in _labels(ax)
    assert check.plot(language="es").get_title() == (
        "ISO 8253-2 campo difuso: bandas sin evaluar"
    )


def test_the_insertion_loss_grows_downwards() -> None:
    result = hearing.earmuff_insertion_loss(
        np.full(22, 90.0), np.full((3, 22), 70.0) + np.arange(3)[:, None]
    )
    ax = result.plot(language="es")
    assert ax.yaxis_inverted()
    assert ax.get_title() == "ISO 4869-3 pérdida por inserción: 3 colocaciones"
    faint = [line for line in ax.lines if line.get_alpha() == pytest.approx(0.6)]
    assert len(faint) == 3


def _db_per_decade(ax: Axes) -> float:
    """How many decibels of the vertical axis span one decade of frequency."""
    low, high = sorted(ax.get_ylim())
    left, right = ax.get_xlim()
    return (high - low) / (float(ax.get_box_aspect()) * np.log10(right / left))


def test_the_insertion_loss_keeps_fifty_decibels_per_decade_on_given_axes() -> None:
    """ISO 4869-3 Clause 6: the 50 dB per decade scale on every graph."""
    import matplotlib.pyplot as plt

    result = hearing.earmuff_insertion_loss(
        np.full(22, 90.0), np.full((3, 22), 70.0) + np.arange(3)[:, None]
    )
    _fig, (left, _right) = plt.subplots(1, 2, figsize=(13.5, 5.6))
    result.plot(left)
    assert _db_per_decade(left) == pytest.approx(50.0)
    assert _db_per_decade(result.plot()) == pytest.approx(50.0)


def test_the_isolation_figure_marks_the_bands_that_fall_short() -> None:
    open_levels = np.full(22, 120.0)
    cup = np.full(22, 60.0)
    ax = hearing.verify_fixture_isolation(open_levels, cup).plot()
    short = _line(ax, "below the requirement")
    assert np.all(np.asarray(short.get_xdata()) >= 315.0)
    assert np.all(np.asarray(short.get_xdata()) <= 4000.0)
    plane = hearing.check_plane_progressive_wave([[80.0] * 22, [80.5] * 22]).plot()
    assert "facing the source less facing away" not in _labels(plane)


def test_a_quasi_free_field_names_its_usable_range() -> None:
    """ISO 8253-2 5.4: the range within which the requirements are met."""
    lateral = dict.fromkeys(("left", "right", "up", "down"), [3.0, 3.0] + [0.5] * 9)
    check = hearing.check_quasi_free_sound_field(
        lateral,
        [0.0] * 11,
        front_levels_db=[1.743] * 11,
        back_levels_db=[0.0] * 11,
        loudspeaker_distance_m=1.0,
    )
    ax = check.plot()
    assert (
        ax.get_title() == "ISO 8253-2 quasi-free field: usable from 500 Hz to 8000 Hz"
    )
    crosses = _line(ax, "band outside the field")
    np.testing.assert_array_equal(crosses.get_xdata(), [125.0, 250.0])
    es = check.plot(language="es")
    assert (
        es.get_title() == "ISO 8253-2 campo cuasi libre: utilizable de 500 Hz a 8000 Hz"
    )


def test_the_room_title_names_the_earphone_of_the_limits() -> None:
    levels = np.full(25, 5.0)
    insert = hearing.check_audiometric_ambient_noise(levels, earphone="ER-3A")
    assert insert.earphone == "ER-3A"
    assert "(ER-3A)" in insert.plot().get_title()
    own = hearing.check_audiometric_ambient_noise(
        levels, earphone_attenuation_db=np.full(25, 30.0)
    )
    assert "(atenuación propia)" in own.plot(language="es").get_title()
    bone = hearing.check_audiometric_ambient_noise(levels, presentation="bone")
    assert bone.earphone is None


def test_the_fixture_site_is_titled_as_its_standard_names_it() -> None:
    """ISO 4869-3 5.2.2 calls the field a random-incidence field."""
    check = hearing.check_random_incidence_field(
        dict.fromkeys(("front", "back", "left", "right", "up", "down"), [0.5] * 22),
        [0.0] * 22,
    )
    assert check.plot().get_title() == (
        "ISO 4869-3 random-incidence field: not judged in every band"
    )
    es = check.plot(language="es")
    assert es.get_title() == (
        "ISO 4869-3 campo de incidencia aleatoria: bandas sin evaluar"
    )
    # The longest title of these figures stays inside a default figure.
    figure = es.figure
    figure.canvas.draw()
    extent = es.title.get_window_extent()
    assert extent.x0 >= 0.0
    assert extent.x1 <= figure.bbox.width


def test_a_free_field_band_is_crossed_on_the_requirement_it_fails() -> None:
    """Lateral deviations inside ±2 dB above 4 kHz, the ear sides 3,4 dB and
    3,7 dB apart: the crosses sit on the right-left difference.
    """
    lateral = {
        "left": [0.2] * 9 + [0.0, 0.0],
        "right": [0.2] * 9 + [1.8, 1.9],
        "up": [0.2] * 11,
        "down": [0.2] * 11,
    }
    lateral["left"][9:] = [-1.6, -1.8]
    law = 20.0 * np.log10(2.15 / 1.85)
    check = hearing.check_free_sound_field(
        lateral,
        [0.0] * 11,
        front_levels_db=[law] * 11,
        back_levels_db=[0.0] * 11,
        loudspeaker_distance_m=2.0,
    )
    assert np.all(check.uniform)
    ax = check.plot()
    crosses = _line(ax, "band outside the field")
    np.testing.assert_array_equal(crosses.get_xdata(), [6000.0, 8000.0])
    np.testing.assert_allclose(crosses.get_ydata(), [3.4, 3.7])


def test_the_retest_figure_draws_the_band_of_agreement() -> None:
    check = hearing.check_retest_agreement(25.0, 35.0)
    ax = check.plot()
    measured = _line(ax, "hearing threshold level")
    np.testing.assert_array_equal(measured.get_ydata(), [25.0, 35.0])
    band = next(p for p in ax.patches if p.get_label() == "agreement to 5 dB")
    assert (band.get_y(), band.get_height()) == (20.0, 10.0)
    assert ax.get_title() == (
        "ISO 8253-1 repeat at 1000 Hz: retest further frequencies"
    )
    es = hearing.check_retest_agreement(25.0, 30.0).plot(language="es")
    assert es.get_title() == "ISO 8253-1 repetición a 1000 Hz: concuerda"


def test_the_cautions_figure_crosses_the_flagged_levels() -> None:
    cautions = hearing.audiogram_cautions(
        [250.0, 500.0, 1000.0, 2000.0],
        air_conduction_db=[20.0, 30.0, 40.0, 50.0],
        bone_conduction_db=[40.0, 25.0, 30.0, 45.0],
    )
    ax = cautions.plot()
    assert ax.yaxis_inverted()
    crosses = _line(ax, "calls for caution")
    np.testing.assert_array_equal(crosses.get_xdata(), [1000.0, 2000.0, 250.0])
    np.testing.assert_array_equal(crosses.get_ydata(), [40.0, 50.0, 40.0])
    tactile = _line(ax, "vibrotactile threshold")
    np.testing.assert_array_equal(tactile.get_ydata(), [40.0, 60.0, 70.0])
    assert ax.get_title() == (
        "ISO 8253-1 audiogram: cross-hearing and vibrotactile caution"
    )
    quiet = hearing.audiogram_cautions(
        [250.0, 1000.0], air_conduction_db=[10.0, 15.0]
    ).plot(language="es")
    assert "pide precaución" not in _labels(quiet)
    assert quiet.get_title() == "ISO 8253-1 audiograma: ningún nivel pide precaución"
