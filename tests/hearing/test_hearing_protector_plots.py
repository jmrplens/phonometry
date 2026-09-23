#  Copyright (c) 2026. Jose Manuel Requena Plens

"""What the ISO 4869-2 ``.plot()`` renderers draw.

Four figures for one protector. The assumed-protection figure exists to show
the gap Formula (1) opens between the mean attenuation and what most wearers
actually get, so the spread has to be drawn either side of the mean and the
assumed value below it. The HML figure is the two-segment line of Formulae
(16) and (17) over the reference noises it was fitted on, with the three
anchors on it. The SNR figure is the per-subject distribution the single
number was reduced from. The protected-level figure draws band results, which
only the octave-band method has: the other two answer from the C- and
A-weighted levels alone and must say so rather than draw an empty axis.

These are the content assertions. The generic plot contract lives in
``tests/test_result_plots.py``.
"""

from __future__ import annotations

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
import reference_data as ref

from phonometry import hearing


def _apv() -> hearing.AssumedProtectionResult:
    return hearing.assumed_protection_value(ref.ISO4869_2_ATTENUATION)


def test_assumed_protection_draws_the_mean_its_spread_and_the_value() -> None:
    result = _apv()
    ax = result.plot()
    # The mean is the first curve, the assumed protection the second, and the
    # spread is the shaded band between them.
    np.testing.assert_allclose(ax.lines[0].get_ydata(), result.mean_attenuation)
    np.testing.assert_allclose(ax.lines[1].get_ydata(), result.apv)
    assert len(ax.collections) >= 1
    # Every band of the assumed value sits a full standard deviation below the
    # mean, which is what alpha = 1 means.
    np.testing.assert_allclose(
        result.mean_attenuation - result.apv, result.standard_deviation
    )
    assert "84" in ax.get_title()
    plt.close("all")


def test_assumed_protection_names_the_performance_it_was_asked_for() -> None:
    ax = hearing.assumed_protection_value(
        ref.ISO4869_2_ATTENUATION, performance=98
    ).plot()
    assert "98" in ax.get_title()
    plt.close("all")


def test_hml_draws_two_segments_through_its_three_anchors() -> None:
    rating = hearing.hml_rating(ref.ISO4869_2_ATTENUATION)
    high, medium, low = rating.reported
    ax = rating.plot()
    # Two straight segments, then the anchors, then the reference cloud.
    left, right = ax.lines[0], ax.lines[1]
    assert left.get_xdata()[-1] == pytest.approx(2.0)
    assert right.get_xdata()[0] == pytest.approx(2.0)
    # They meet at the medium value, which is where M is defined.
    assert left.get_ydata()[-1] == pytest.approx(medium)
    assert right.get_ydata()[0] == pytest.approx(medium)
    anchors = ax.lines[2]
    np.testing.assert_allclose(anchors.get_xdata(), [-2.0, 2.0, 10.0])
    np.testing.assert_allclose(anchors.get_ydata(), [high, medium, low])
    for value in (high, medium, low):
        assert str(value) in ax.get_title()
    plt.close("all")


def test_hml_scatters_every_subject_of_every_reference_noise() -> None:
    rating = hearing.hml_rating(ref.ISO4869_2_ATTENUATION)
    ax = rating.plot()
    cloud = ax.lines[3]
    assert cloud.get_ydata().size == rating.predicted_reduction.size
    np.testing.assert_allclose(
        sorted(set(cloud.get_xdata())), sorted(hearing.HML_REFERENCE_C_MINUS_A)
    )
    plt.close("all")


def test_snr_draws_one_bar_per_subject_with_its_two_references() -> None:
    rating = hearing.snr_rating(ref.ISO4869_2_ATTENUATION)
    ax = rating.plot()
    heights = [patch.get_height() for patch in ax.patches]
    np.testing.assert_allclose(heights, rating.subject_snr)
    # The mean and the reported single number are drawn across them.
    horizontals = [line.get_ydata()[0] for line in ax.lines]
    assert rating.mean == pytest.approx(
        min(horizontals, key=lambda v: abs(v - rating.mean))
    )
    assert float(rating.reported) in horizontals
    plt.close("all")


def test_the_protected_level_figure_draws_the_band_results() -> None:
    result = hearing.octave_band_protected_level(
        ref.ISO4869_2_ANNEX_B_NOISE, ref.ISO4869_2_APV84_PRINTED
    )
    ax = result.plot()
    assert result.band_levels is not None
    np.testing.assert_allclose(
        [patch.get_height() for patch in ax.patches], result.band_levels
    )
    assert str(result.reported_level) in ax.get_title()
    plt.close("all")


@pytest.mark.parametrize("method", ["HML", "SNR"])
def test_a_rating_method_result_has_no_spectrum_to_draw(method: str) -> None:
    """Refuse rather than draw an empty axis: these never see a spectrum."""
    attenuation = ref.ISO4869_2_ATTENUATION
    if method == "HML":
        result = hearing.hml_protected_level(
            104.0, 103.0, hearing.hml_rating(attenuation)
        )
    else:
        result = hearing.snr_protected_level(
            hearing.snr_rating(attenuation), l_p_c=103.0
        )
    assert result.band_levels is None
    with pytest.raises(ValueError, match="no spectrum to draw"):
        result.plot()
    plt.close("all")


@pytest.mark.parametrize(
    "factory",
    [
        lambda: hearing.assumed_protection_value(ref.ISO4869_2_ATTENUATION),
        lambda: hearing.hml_rating(ref.ISO4869_2_ATTENUATION),
        lambda: hearing.snr_rating(ref.ISO4869_2_ATTENUATION),
        lambda: hearing.octave_band_protected_level(
            ref.ISO4869_2_ANNEX_B_NOISE, ref.ISO4869_2_APV84_PRINTED
        ),
    ],
    ids=["apv", "hml", "snr", "octave"],
)
def test_every_protector_figure_speaks_spanish(factory: object) -> None:
    english = factory().plot()
    spanish = factory().plot(language="es")
    assert spanish.get_title() != english.get_title()
    assert spanish.get_ylabel() != ""
    labels = [str(t.get_text()) for t in spanish.get_legend().get_texts()]
    assert labels
    plt.close("all")


def test_the_protected_level_figure_labels_the_bands_it_was_given() -> None:
    result = hearing.octave_band_protected_level(
        ref.ISO4869_2_ANNEX_B_NOISE[1:], ref.ISO4869_2_APV84_PRINTED[1:]
    )
    ax = result.plot()
    assert [t.get_text() for t in ax.get_xticklabels()] == [
        f"{f:g}" for f in hearing.PROTECTOR_OCTAVE_BANDS[1:]
    ]
    plt.close("all")


def test_the_two_hml_segments_are_styled_as_one_line() -> None:
    """A corner, not two curves: every option reaches both halves.

    Only the label is withheld from the second segment, so the reader gets one
    legend entry for what looks like one line.
    """
    rating = hearing.hml_rating(ref.ISO4869_2_ATTENUATION)
    ax = rating.plot(linestyle="--", alpha=0.6, color="#123456", linewidth=3.0)
    left, right = ax.lines[0], ax.lines[1]
    for read in ("get_linestyle", "get_alpha", "get_color", "get_linewidth"):
        assert getattr(left, read)() == getattr(right, read)(), read
    labels = [str(line.get_label()) for line in (left, right)]
    assert labels[0].startswith("$PNR$")
    assert labels[1].startswith("_")
    plt.close("all")


# ---------------------------------------------------------------------------
# ISO 4869-1: the measurement the grid comes from
# ---------------------------------------------------------------------------


def _reat() -> hearing.RealEarAttenuationResult:
    return hearing.real_ear_attenuation(ref.ISO4869_1_TABLE_A3)


def test_the_mean_attenuation_points_downwards_on_the_iec_60263_grid() -> None:
    """Clause 6 l): increasing values downwards, 50 dB to one decade."""
    result = _reat()
    ax = result.plot()
    mean_line = next(line for line in ax.lines if line.get_marker() == "o")
    np.testing.assert_allclose(mean_line.get_ydata(), result.mean_db)
    bottom, top = ax.get_ylim()
    assert bottom > top, "attenuation is not drawn increasing downwards"
    left, right = ax.get_xlim()
    expected = ((bottom - top) / 50.0) / np.log10(right / left)
    assert ax.get_box_aspect() == pytest.approx(expected)
    # One faint line per subject behind the mean, one legend entry for them.
    faint = [line for line in ax.lines if line.get_marker() in ("None", "", None)]
    assert len(faint) == result.subjects
    assert "16" in ax.get_title()
    plt.close("all")


def test_axes_handed_in_keep_their_shape() -> None:
    _fig, ax = plt.subplots()
    _reat().plot(ax=ax)
    assert ax.get_box_aspect() is None
    plt.close("all")


def test_the_annex_b_figure_hatches_only_the_significant_band() -> None:
    result = hearing.assess_attenuation_difference(
        _reat(),
        ref.ISO4869_1_TABLE_B1_MEAN_2,
        second_expanded_uncertainty_db=ref.ISO4869_1_TABLE_B1_U95_2,
    )
    ax = result.plot()
    hatched = [bool(bar.get_hatch()) for bar in ax.patches]
    assert hatched == [False] * 6 + [True]
    np.testing.assert_allclose(
        [bar.get_height() for bar in ax.patches], result.difference_db
    )
    assert "8000 Hz" in ax.get_title()
    # The hatch is explained in the legend, and the bands read as the other
    # frequency axes of the library do.
    legend = ax.get_legend()
    assert legend is not None
    assert "significant" in [text.get_text() for text in legend.get_texts()]
    assert [tick.get_text() for tick in ax.get_xticklabels()][-4:] == [
        "1k",
        "2k",
        "4k",
        "8k",
    ]
    plt.close("all")


def test_the_annex_b_figure_writes_a_spanish_band_with_a_comma() -> None:
    result = hearing.assess_attenuation_difference(
        [20.0, 30.0],
        [30.0, 30.5],
        first_expanded_uncertainty_db=1.0,
        second_expanded_uncertainty_db=1.0,
        frequencies=[31.5, 63.0],
    )
    ax = result.plot(language="es")
    assert "31,5 Hz" in ax.get_title()
    assert ax.get_xticklabels()[0].get_text() == "31,5"
    legend = ax.get_legend()
    assert legend is not None
    assert "significativa" in [text.get_text() for text in legend.get_texts()]
    plt.close("all")


_SIX = ("front", "back", "left", "right", "up", "down")
_ROTATION = {
    "rotation_levels_db": [[0.0] * 7, [4.0] * 7],
    "free_field_rejection_db": 17.0,
}


def test_the_sound_field_figure_names_its_verdict() -> None:
    passing = hearing.check_reat_sound_field(
        dict.fromkeys(_SIX, [0.0] * 7), [0.0] * 7, **_ROTATION
    )
    failing = hearing.check_reat_sound_field(
        {**dict.fromkeys(_SIX, [0.0] * 7), "up": [3.0] * 7}, [0.0] * 7
    )
    assert passing.plot().get_title().endswith("qualifies")
    assert failing.plot().get_title().endswith("does not qualify")
    plt.close("all")


def test_the_sound_field_figure_says_when_b_was_not_judged() -> None:
    """Without the rotation the title does not claim the room qualifies."""
    unjudged = hearing.check_reat_sound_field(dict.fromkeys(_SIX, [0.0] * 7), [0.0] * 7)
    assert unjudged.plot().get_title().endswith("a) met, b) not judged")
    assert unjudged.plot(language="es").get_title().endswith("b) sin evaluar")
    plt.close("all")


def test_the_sound_field_figure_draws_the_left_right_difference_undirected() -> None:
    """The curve is |right - left| and its label does not claim a direction."""
    check = hearing.check_reat_sound_field(
        {**dict.fromkeys(_SIX, [0.0] * 7), "right": [-1.2] * 7, "left": [1.1] * 7},
        [0.0] * 7,
        **_ROTATION,
    )
    ax = check.plot()
    line = next(
        line
        for line in ax.lines
        if line.get_label() == "difference between right and left"
    )
    np.testing.assert_allclose(line.get_ydata(), 2.3)
    plt.close("all")
