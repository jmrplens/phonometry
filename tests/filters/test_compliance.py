#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the IEC 61260 filter class verifier (2014 classes 1/2 and the
1995 / ANSI S1.11-2004 edition that adds class 0).
"""

import numpy as np
import pytest
import reference_data as ref

from phonometry import filters
from phonometry.filters.compliance import (
    _PASSBAND_MAX_1995,
    _PASSBAND_MIN_1995,
    _STOPBAND_MIN_1995,
    class_limits,
)


def test_class_limits_table1_anchor_values() -> None:
    """Spot-check the transcription against BS EN 61260-1:2014 Table 1 (b=1)."""
    G = 10 ** (3 / 10)
    # Passband center: class 1 in [-0.4, +0.4]
    lo, hi = class_limits(1.0, 1, np.array([1.0]))
    assert lo[0] == pytest.approx(-0.4)
    assert hi[0] == pytest.approx(0.4)
    # Band edge (inside): max +5.3 (class 1)
    lo, hi = class_limits(1.0, 1, np.array([G**0.5 * 0.999999]))
    assert hi[0] == pytest.approx(5.3, abs=0.05)
    # Just outside the edge: minimum attenuation +1.2 (class 1)
    lo, hi = class_limits(1.0, 1, np.array([G**0.5 * 1.000001]))
    assert lo[0] == pytest.approx(1.2, abs=0.05)
    assert np.isinf(hi[0])
    # One octave out: minimum +16.6 (class 1) / +15.6 (class 2)
    lo1, _ = class_limits(1.0, 1, np.array([G]))
    lo2, _ = class_limits(1.0, 2, np.array([G]))
    assert lo1[0] == pytest.approx(16.6)
    assert lo2[0] == pytest.approx(15.6)
    # Far stopband: minimum +70 (class 1) / +60 (class 2)
    lo1, _ = class_limits(1.0, 1, np.array([G**5]))
    lo2, _ = class_limits(1.0, 2, np.array([G**5]))
    assert lo1[0] == pytest.approx(70.0)
    assert lo2[0] == pytest.approx(60.0)


def test_class_limits_low_side_is_reciprocal() -> None:
    """Formula (10): the low side mirrors the high side at 1/Omega."""
    omega = np.array([1.3, 2.0, 4.0])
    lo_h, hi_h = class_limits(3.0, 1, omega)
    lo_l, hi_l = class_limits(3.0, 1, 1.0 / omega)
    np.testing.assert_allclose(lo_l, lo_h)
    np.testing.assert_allclose(hi_l, hi_h, equal_nan=False)


def test_butter_order6_third_octave_meets_class1() -> None:
    bank = filters.OctaveFilterBank(fs=48000, fraction=3, order=6, limits=[100, 5000])
    result = filters.verify_filter_class(bank)
    assert result.overall_class == 1, result


def test_butter_order6_decimated_octave_bank_is_class1_on_every_requirement() -> None:
    """The multirate octave bank is class 1 on Table 1, 5.12 and 5.16.

    Each band is decimated only as far as leaves its processing Nyquist
    frequency sixteen times its upper band edge, where the bilinear transform
    no longer bends the skirts: every band sums its neighbours within 0.005 dB
    of the same band filtered at the full rate. Decimated to 1.25 times the
    edge, the bank summed to +0.94 dB, past the +0.8 dB of class 1.
    """
    limits = [125, 4000]
    bank = filters.OctaveFilterBank(fs=48000, fraction=1, order=6, limits=limits)
    result = filters.verify_filter_class(bank)
    assert any(f > 1 for f in bank.factor)
    assert result.requirement_class("relative_attenuation") == 1
    assert result.requirement_class("effective_bandwidth") == 1
    assert result.requirement_class("summation") == 1
    assert result.overall_class == 1, result
    full_rate = filters.verify_filter_class(
        filters.OctaveFilterBank(
            fs=48000,
            fraction=1,
            order=6,
            limits=limits,
            design=filters.FilterDesign(resample=False),
        )
    )
    for decimated, reference in zip(
        result.bands[1:-1], full_rate.bands[1:-1], strict=True
    ):
        for key in ("summation_max_db", "summation_min_db"):
            assert decimated[key] == pytest.approx(reference[key], abs=0.005)


def test_undecimated_octave_bank_meets_class1_on_every_requirement() -> None:
    """Without the decimation the octave bank sums within the class 1 limits."""
    bank = filters.OctaveFilterBank(
        fs=48000,
        fraction=1,
        order=6,
        limits=[125, 4000],
        design=filters.FilterDesign(resample=False),
    )
    result = filters.verify_filter_class(bank)
    assert result.overall_class == 1, result


def test_low_order_fails_class1() -> None:
    """A 1st-order bank cannot reach the class stopband attenuations."""
    bank = filters.OctaveFilterBank(fs=48000, fraction=1, order=1, limits=[500, 2000])
    result = filters.verify_filter_class(bank)
    assert result.overall_class is None


def test_result_has_per_band_details() -> None:
    bank = filters.OctaveFilterBank(fs=48000, fraction=1, order=6, limits=[500, 2000])
    result = filters.verify_filter_class(bank)
    assert len(result.bands) == bank.num_bands
    for band in result.bands:
        assert set(band) >= {"freq", "class", "margin_class1_db", "margin_class2_db"}
    # margins must be finite floats
    assert all(np.isfinite(b["margin_class1_db"]) for b in result.bands)


def test_stateful_bank_matches_stateless_design() -> None:
    """Stateful banks share the SOS design: verification must agree exactly."""
    stateful = filters.OctaveFilterBank(
        fs=48000,
        fraction=1,
        order=6,
        limits=[500, 2000],
        design=filters.FilterDesign(resample=False),
        block_processing=filters.BlockProcessing(stateful=True),
    )
    stateless = filters.OctaveFilterBank(
        fs=48000,
        fraction=1,
        order=6,
        limits=[500, 2000],
        design=filters.FilterDesign(resample=False),
    )
    r_stateful = filters.verify_filter_class(stateful)
    r_stateless = filters.verify_filter_class(stateless)
    assert r_stateful.overall_class == r_stateless.overall_class
    for a, b in zip(r_stateful.bands, r_stateless.bands, strict=True):
        assert a["margin_class1_db"] == pytest.approx(b["margin_class1_db"])


def test_coarse_grid_breakpoints_evaluated_exactly() -> None:
    """The Table 1 breakpoints are evaluated with sosfreqz at their exact
    frequencies, not interpolated off the grid: even the permitted 16-point
    floor reproduces the dense-grid verdict and binding margin (interpolation
    used to yield garbage margins around -190 dB there).
    """
    bank = filters.OctaveFilterBank(
        fs=48000,
        fraction=3,
        order=6,
        limits=[100, 5000],
        design=filters.FilterDesign(filter_type="butter"),
    )
    dense = filters.verify_filter_class(bank)
    coarse = filters.verify_filter_class(bank, num_points=16)
    assert coarse.overall_class == dense.overall_class == 1
    m_dense = min(b["margin_class1_db"] for b in dense.bands)
    m_coarse = min(b["margin_class1_db"] for b in coarse.bands)
    assert m_coarse == pytest.approx(m_dense, abs=0.05)


def test_invalid_inputs_raise() -> None:
    bank = filters.OctaveFilterBank(fs=48000, fraction=1, order=6, limits=[500, 2000])
    band_centre = np.array([1.0])
    with pytest.raises(ValueError, match=r"'num_points' must be at least"):
        filters.verify_filter_class(bank, num_points=4)
    with pytest.raises(
        ValueError, match=r"filter_class must be one of .* for edition '2014'"
    ):
        class_limits(1.0, 3, band_centre)
    with pytest.raises(ValueError, match=r"'fraction' must be positive"):
        class_limits(-1.0, 1, band_centre)


# ---------------------------------------------------------------------------
# IEC 61260:1995 / ANSI S1.11-2004 edition (adds class 0)
# ---------------------------------------------------------------------------


def test_1995_tables_match_reference_data() -> None:
    """The module's 1995 mask reproduces the shared reference_data transcription."""
    assert _PASSBAND_MIN_1995 == ref.IEC61260_1995_PASSBAND_MIN
    assert [tuple(r) for r in _PASSBAND_MAX_1995] == [
        tuple(r) for r in ref.IEC61260_1995_PASSBAND_MAX
    ]
    assert [tuple(r) for r in _STOPBAND_MIN_1995] == [
        tuple(r) for r in ref.IEC61260_1995_STOPBAND_MIN
    ]


def test_1995_class0_anchor_values() -> None:
    """class_limits reproduces the Table 1 class-0 anchors (octave band)."""
    g = 10 ** (3 / 10)
    lo, hi = class_limits(1.0, 0, np.array([1.0]), edition="1995")
    assert (lo[0], hi[0]) == (-0.15, 0.15)  # Omega = 1
    lo, hi = class_limits(1.0, 0, np.array([g**0.5 * 0.999999]), edition="1995")
    assert hi[0] == pytest.approx(4.5, abs=1e-3)  # pass-band edge max
    lo, _ = class_limits(1.0, 0, np.array([g**0.5 * 1.000001]), edition="1995")
    assert lo[0] == pytest.approx(2.3, abs=1e-3)  # stop-band edge min
    lo, _ = class_limits(1.0, 0, np.array([g]), edition="1995")
    assert lo[0] == pytest.approx(18.0, abs=1e-6)  # G**1 min


def test_1995_class0_is_strictest() -> None:
    """At every breakpoint class 0 <= class 1 <= class 2 max, and min ordering."""
    g = 10 ** (3 / 10)
    omega = g ** np.linspace(0, 1.5, 40)
    lo0, hi0 = class_limits(1.0, 0, omega, edition="1995")
    lo1, hi1 = class_limits(1.0, 1, omega, edition="1995")
    lo2, hi2 = class_limits(1.0, 2, omega, edition="1995")
    # Tighter class => smaller (or equal) maximum allowance in the pass-band.
    pb = omega <= g**0.5
    assert np.all(hi0[pb] <= hi1[pb] + 1e-9)
    assert np.all(hi1[pb] <= hi2[pb] + 1e-9)
    # ...and a larger (or equal) minimum: the corridor floor rises with strictness.
    assert np.all(lo0[pb] >= lo1[pb] - 1e-9)
    assert np.all(lo1[pb] >= lo2[pb] - 1e-9)


def test_butter_meets_class0_1995() -> None:
    """The default order-6 Butterworth bank clears the strict 1995 class 0.

    On Table 1, alias images included, on the filter integrated response of
    4.5.3 and on the summation of 4.9, each band carrying its margins to the
    three classes on all three.
    """
    bank = filters.OctaveFilterBank(fs=48000, fraction=3, order=6)
    result = filters.verify_filter_class(bank, edition="1995")
    assert result.overall_class == 0, result
    assert result.requirements == (
        "relative_attenuation",
        "effective_bandwidth",
        "summation",
    )
    band = result.bands[0]
    margins = {
        f"{kind}margin_class{c}_db"
        for kind in ("", "bandwidth_", "summation_")
        for c in (0, 1, 2)
    }
    assert set(band) == {
        "freq",
        "class",
        "checked_to_omega",
        "bandwidth_deviation_db",
        "summation_min_db",
        "summation_max_db",
        *margins,
    }
    # A class-0 band must clear class 1 and class 2 by at least as much.
    for b in result.bands:
        assert b["margin_class0_db"] <= b["margin_class1_db"] + 1e-9
        assert b["margin_class1_db"] <= b["margin_class2_db"] + 1e-9


def test_2014_default_unaffected_by_edition_support() -> None:
    """The default edition still reports only classes 1/2 (no class-0 key),
    now with the 5.12 and 5.16 requirements of IEC 61260-2 beside Table 1.
    """
    bank = filters.OctaveFilterBank(fs=48000, fraction=3, order=6)
    result = filters.verify_filter_class(bank)
    assert result.overall_class == 1
    assert set(result.bands[0]) == {
        "freq",
        "class",
        "checked_to_omega",
        "margin_class1_db",
        "margin_class2_db",
        "bandwidth_deviation_db",
        "bandwidth_margin_class1_db",
        "bandwidth_margin_class2_db",
        "summation_min_db",
        "summation_max_db",
        "summation_margin_class1_db",
        "summation_margin_class2_db",
    }


def test_range_limited_flag_reports_unverifiable_stopband() -> None:
    """The verdict flags a mask that runs on past half the input rate.

    The octave-band stop-band mask runs to G^4 = 15.85 f_m. Every band, a
    decimated one with its alias images included, is graded up to half the
    48 kHz input rate: that is 190.6 f_m for the 125 Hz band but 12 f_m and
    6 f_m for the 2 kHz and 4 kHz bands, so their G^2..G^4 rows cannot be
    demonstrated, and the verdict must say so instead of claiming full
    Table 1 conformance.
    """
    bank = filters.OctaveFilterBank(fs=48000, fraction=1, order=6, limits=[125, 4000])
    result = filters.verify_filter_class(bank)
    assert result.range_limited is True
    assert max(bank.factor) > 1
    for band in result.bands:
        assert band["checked_to_omega"] * band["freq"] == pytest.approx(24000.0)
    top = result.bands[-1]["checked_to_omega"]
    # The checked range covers the band edge but not the G^4 mask end.
    assert 10**0.15 < top < 10 ** (0.3 * 4)


def test_a_bank_whose_mask_ends_below_half_the_rate_is_not_range_limited() -> None:
    """Every band's G^4 breakpoint below fs / 2: the whole mask is demonstrated.

    The 1 kHz band of a 48 kHz bank is graded to 24 f_m, past the 15.85 f_m
    where its octave mask ends, and the lower bands further still.
    """
    bank = filters.OctaveFilterBank(fs=48000, fraction=1, order=6, limits=[125, 1000])
    result = filters.verify_filter_class(bank)
    assert result.range_limited is False
    assert min(b["checked_to_omega"] for b in result.bands) > 10 ** (0.3 * 4)


def test_1995_rejects_out_of_range_class_and_bad_edition() -> None:
    band_centre = np.array([1.0])
    with pytest.raises(
        ValueError, match=r"filter_class must be one of .* for edition '1995'"
    ):
        class_limits(1.0, 3, band_centre, edition="1995")
    with pytest.raises(
        ValueError, match=r"filter_class must be one of .* for edition '2014'"
    ):
        class_limits(1.0, 0, band_centre)  # class 0 invalid for 2014
    with pytest.raises(ValueError, match=r"edition must be '2014'"):
        class_limits(1.0, 1, band_centre, edition="2020")
    bank = filters.OctaveFilterBank(fs=48000, fraction=1, order=6, limits=[500, 2000])
    with pytest.raises(ValueError, match=r"edition must be '2014'"):
        filters.verify_filter_class(bank, edition="2020")


def test_map_breakpoint_reproduces_table_f1() -> None:
    """IEC 61260-1:2014 Table F.1: the Formula (9) mapping reproduces every
    printed one-third-octave (b = 3) breakpoint and reciprocal to the five
    printed decimals.
    """
    from reference_data import IEC61260_TABLE_F1

    from phonometry.filters.compliance import _map_breakpoint

    for exponent, (omega, reciprocal) in IEC61260_TABLE_F1.items():
        got = _map_breakpoint(exponent, 3)
        assert got == pytest.approx(omega, abs=5e-6), exponent
        assert 1.0 / got == pytest.approx(reciprocal, abs=5e-6), exponent


# --------------------------------------------------------------------------
# Per-band entries that do not agree
# --------------------------------------------------------------------------
def _octave_verdict() -> filters.FilterComplianceResult:
    """A class 1 octave bank from 500 Hz to 16 kHz, as the tests below take it."""
    from phonometry.filters.core import OctaveFilterBank

    return filters.verify_filter_class(
        OctaveFilterBank(fs=48000, fraction=1, order=4, limits=[500, 16000])
    )


def test_a_filter_verdict_refuses_per_band_entries_that_disagree() -> None:
    """The fiche prints one row per band under the bank's overall class.

    A band list short of an entry gives a sheet whose verdict covers a band
    that is nowhere in its table.
    """
    import dataclasses

    result = _octave_verdict()
    short = result.band_margins[:-1]
    # Every field of the result is named whichever one is short, so the count
    # is the only part that says it was 'band_margins'. This test set that count.
    with pytest.raises(ValueError, match=rf"'band_margins' \({len(short)}\)"):
        dataclasses.replace(result, band_margins=short)


@pytest.mark.parametrize("name", ["bands", "overall_class", "range_limited"])
def test_a_filter_verdict_reads_its_classes_from_the_margins(name: str) -> None:
    """The per-band classes, the bank's class and the range are not fields.

    They used to be, pinned against one another when the verdict was built:
    a class the bands did not derive, a class over a band that met none, a
    class that was no designation or one stated over no bands. All of them
    are read from the margins and the edition's Table 1 now.
    """
    import dataclasses

    result = _octave_verdict()
    assert name not in {field.name for field in dataclasses.fields(result)}
    stated = {name: getattr(result, name)}
    with pytest.raises(TypeError, match=name):
        dataclasses.replace(result, **stated)


def test_a_band_margin_row_that_states_a_class_is_refused() -> None:
    """A row carries what the band was measured to, and the class is read from it."""
    import dataclasses

    result = _octave_verdict()
    rows = tuple({**band, "class": 1} for band in result.band_margins)
    with pytest.raises(ValueError, match=r"'band_margins' must not state a class"):
        dataclasses.replace(result, band_margins=rows)


def test_a_band_that_misses_class_1_takes_the_bank_to_class_2() -> None:
    """The boxed class restates the per-band classes under it, by construction.

    Built by hand, the fiche once boxed ``Class 1 - COMPLIES (margin
    -0.35 dB)`` above a table whose 1 kHz row read ``Class 2 (-0.35 dB)``.
    A band that misses class 1 by a hair and meets class 2 now reads class 2,
    and so does the bank.
    """
    import dataclasses

    from phonometry.filters.core import OctaveFilterBank

    result = filters.verify_filter_class(
        OctaveFilterBank(fs=48000, fraction=3, order=4, limits=[500, 2000])
    )
    assert result.overall_class == 1
    rows = tuple(dict(band) for band in result.band_margins)
    rows[1]["margin_class1_db"] = -0.35
    lowered = dataclasses.replace(result, band_margins=rows)
    assert lowered.bands[1]["class"] == 2
    assert lowered.overall_class == 2


def test_a_band_that_meets_no_class_leaves_the_bank_without_one() -> None:
    """A bank is no better than its worst band: one row meeting no class reads ``None``."""
    import dataclasses

    result = _octave_verdict()
    rows = tuple(dict(band) for band in result.band_margins)
    for cls in result.available_classes():
        rows[1][f"margin_class{cls}_db"] = -1.0
    failed = dataclasses.replace(result, band_margins=rows)
    assert failed.bands[1]["class"] is None
    assert failed.overall_class is None


def test_a_filter_verdict_over_no_bands_states_no_class() -> None:
    """A bank with no bands in range is a real outcome, and it attests nothing.

    A class stated over zero bands would print an accredited verdict box
    above a table reportlab then refuses to build.
    """
    import dataclasses

    import numpy as np

    result = _octave_verdict()
    empty = dataclasses.replace(
        result,
        band_margins=(),
        sos=(),
        band_frequencies=np.asarray([], dtype=float),
        factors=(),
    )
    assert empty.bands == ()
    assert empty.overall_class is None


def test_a_filter_verdict_refuses_an_edition_that_disagrees_with_its_bands() -> None:
    """A 2014 verdict relabelled 1995 would silently draw the other
    edition's corridor under the same title.
    """
    import dataclasses

    result = _octave_verdict()
    with pytest.raises(ValueError, match=r"'edition' \('1995'\) defines classes"):
        dataclasses.replace(result, edition="1995")


def test_a_filter_verdict_refuses_a_later_band_short_of_a_margin_key() -> None:
    """The margin keys are read off every band, not only the first.

    ``verify_filter_class`` fills each entry from the same list of classes, so
    a band list whose entries disagree among themselves is one no bank
    produced. Accepting it on the strength of the first band alone left the
    ``KeyError`` for the reader: the fiche's per-band table and the plot's
    worst-band search read ``margin_class<c>_db`` out of every band, for the
    reference class. The key dropped here is that one, so the band list is
    exactly the one that used to construct and then die mid-figure.
    """
    import dataclasses

    result = _octave_verdict()
    # The producer's own bands all carry the same margin keys, so the guard
    # cannot refuse a verdict a bank emitted.
    assert len({frozenset(band) for band in result.band_margins}) == 1
    bands = tuple(dict(band) for band in result.band_margins)
    dropped = result.reference_class()
    kept = [c for c in result.available_classes() if c != dropped]
    del bands[1][f"margin_class{dropped}_db"]
    with pytest.raises(
        ValueError,
        match=rf"entry of 'band_margins' carries margins for classes \{kept}",
    ):
        dataclasses.replace(result, band_margins=bands)


def test_a_filter_verdict_refuses_a_non_finite_per_band_value() -> None:
    """Every margin is a ``min`` over the measured attenuation against the
    Table 1 mask, so no bank emits a NaN; one smuggled in prints
    ``Class 1 (+nan dB)`` in the per-band table.
    """
    import dataclasses

    result = _octave_verdict()
    bands = tuple(dict(band) for band in result.band_margins)
    bands[0][f"margin_class{result.reference_class()}_db"] = float("nan")
    with pytest.raises(ValueError, match=r"'band_margins' must carry finite per-band"):
        dataclasses.replace(result, band_margins=bands)


def test_a_filter_verdict_refuses_an_unknown_edition() -> None:
    """The edition is a pinned tag, refused by name at construction."""
    import dataclasses

    result = _octave_verdict()
    with pytest.raises(ValueError, match="'edition' must be one of"):
        dataclasses.replace(result, edition="2003")


# ---------------------------------------------------------------------------
# The rows a class is read from are the result's own, and read-only
# ---------------------------------------------------------------------------
def test_a_filter_verdict_row_cannot_be_written_into() -> None:
    result = filters.verify_filter_class(
        filters.OctaveFilterBank(fs=48000, fraction=1, order=6, limits=[125, 4000])
    )
    row = result.band_margins[0]
    with pytest.raises(TypeError, match="does not support item assignment"):
        row["margin_class1_db"] = -50.0  # type: ignore[index]
    assert result.overall_class == 1


def test_a_filter_verdict_keeps_a_copy_of_the_callers_rows() -> None:
    """A write into the dictionaries a result was built from does not reach it."""
    import dataclasses

    result = filters.verify_filter_class(
        filters.OctaveFilterBank(fs=48000, fraction=1, order=6, limits=[125, 4000])
    )
    rows = [dict(band) for band in result.band_margins]
    again = dataclasses.replace(result, band_margins=tuple(rows))
    for row in rows:
        row["margin_class1_db"] = -50.0
        row["margin_class2_db"] = -50.0
    assert again.overall_class == 1
    assert all(band["class"] == 1 for band in again.bands)


def test_a_weighting_verdict_row_and_sweep_cannot_be_written_into() -> None:
    result = filters.verify_weighting_class(
        filters.WeightingFilter(fs=48000, curve="A")
    )
    row = result.band_margins[0]
    with pytest.raises(TypeError, match="does not support item assignment"):
        row["margin_class1_db"] = -50.0  # type: ignore[index]
    sweep = result.between_nominals
    assert sweep is not None
    with pytest.raises(TypeError, match="does not support item assignment"):
        sweep["margin_class1_db"] = -50.0  # type: ignore[index]
    assert result.overall_class == 1


def test_a_weighting_verdict_survives_a_round_trip_through_pickle() -> None:
    import pickle

    result = filters.verify_weighting_class(
        filters.WeightingFilter(fs=48000, curve="A")
    )
    again = pickle.loads(pickle.dumps(result))  # noqa: S301 - our own bytes
    assert again.overall_class == result.overall_class
    assert again.bands == result.bands
