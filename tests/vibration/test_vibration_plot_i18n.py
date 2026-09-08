#  Copyright (c) 2026. Jose Manuel Requena Plens
"""EN/ES language option of the vibration ``.plot()`` renderers."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from phonometry import vibration


def _result() -> vibration.MobilityResult:
    return vibration.sdof_mobility_result(np.linspace(1.0, 50.0, 200), 2.0, 8000.0, 5.0)


def test_spanish_labels() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    res = _result()

    ax_en = res.plot(language="en")
    assert ax_en.get_xlabel() == "Frequency [Hz]"
    assert ax_en.get_title() == "ISO 7626-1 mechanical mobility"

    ax_es = res.plot(language="es")
    assert ax_es.get_xlabel() == "Frecuencia [Hz]"
    assert ax_es.get_title() == "ISO 7626-1 movilidad mecánica"


def test_rigid_mass_spanish_labels() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    f = np.array([20.0, 100.0, 500.0])
    res = vibration.rigid_mass_calibration_check([0.100, 0.102, 0.097], f, mass=10.0)

    axes_en = res.plot(language="en")
    assert axes_en[0].get_title() == "ISO 7626-2 rigid-mass calibration check (PASS)"
    assert axes_en[1].get_ylabel() == "Deviation [%]"

    axes_es = res.plot(language="es")
    assert axes_es[0].get_title() == (
        "ISO 7626-2 verificación de calibración con masa rígida (CORRECTO)"
    )
    assert axes_es[1].get_ylabel() == "Desviación [%]"
    assert axes_es[1].get_xlabel() == "Frecuencia [Hz]"


def test_multiple_shock_spanish_title_translates_sex() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    from phonometry.vibration.human.multiple_shock import (
        MZ_MALE,
        RISK_THRESHOLDS_MALE,
        MultipleShockResult,
        compression_dose,
        dose_from_peaks,
        injury_probability,
        injury_risk,
    )

    peaks = np.full(5, 40.0)
    dz = dose_from_peaks(peaks)
    sd = compression_dose(dz, mz=MZ_MALE)
    r = injury_risk(sd, start_age=20.0, years=20, days_per_year=120.0, sex="male")
    res = MultipleShockResult(
        sex="male",
        acceleration_dose=dz,
        daily_dose=dz,
        compression_dose=sd,
        risk=r,
        probability=float(injury_probability(r, sex="male")),
        start_age=20.0,
        years=20,
        days_per_year=120.0,
        peaks=peaks,
        risk_thresholds=RISK_THRESHOLDS_MALE,
    )
    ax_en = res.plot(language="en")
    assert ax_en.get_title() == "ISO 2631-5 injury probability — male"
    ax_es = res.plot(language="es")
    assert ax_es.get_title() == "ISO 2631-5 probabilidad de lesión — hombre"


def test_unknown_language_raises() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    result = _result()
    with pytest.raises(ValueError, match="Unknown language"):
        result.plot(language="xx")


def test_fault_frequency_overlay_labels() -> None:
    """The fault-line overlay localises its axes, title and family legend."""
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")

    res = vibration.bearing_fault_frequencies(
        2000.0, 15, 6.0, 34.0, contact_angle_deg=12.96
    )

    ax_en = res.plot()
    assert ax_en.get_xlabel() == "Frequency [Hz]"
    assert "rolling-contact bearing" in ax_en.get_title()
    assert ax_en.get_ylabel() == "Predicted fault line"
    labels_en = [t.get_text() for t in ax_en.get_legend().get_texts()]
    assert {"shaft", "bearing"} <= set(labels_en)

    ax_es = res.plot(language="es")
    assert ax_es.get_xlabel() == "Frecuencia [Hz]"
    assert "rodamiento de contacto rodante" in ax_es.get_title()
    labels_es = [t.get_text() for t in ax_es.get_legend().get_texts()]
    assert {"eje", "rodamiento"} <= set(labels_es)

    with pytest.raises(ValueError, match="Unknown language"):
        res.plot(language="xx")


def test_fault_frequency_overlay_on_a_measured_spectrum() -> None:
    """With a spectrum the curve is drawn underneath and named."""
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    from phonometry import signals

    res = vibration.bearing_fault_frequencies(
        2000.0, 15, 6.0, 34.0, contact_angle_deg=12.96
    )
    fs = 8192.0
    t = np.arange(int(fs)) / fs
    signal = (1.0 + 0.5 * np.cos(2.0 * np.pi * res["BPFO"] * t)) * np.cos(
        2.0 * np.pi * 2000.0 * t
    )
    spectrum = signals.envelope_spectrum(signal, fs)

    ax = res.plot(spectrum=spectrum, max_frequency=600.0)
    assert ax.get_ylabel() == "Envelope amplitude"
    assert ax.get_xlim() == (0.0, 600.0)
    labels = [t_.get_text() for t_ in ax.get_legend().get_texts()]
    assert "envelope spectrum" in labels

    empty = res.within(1.0e6, 2.0e6)
    with pytest.raises(ValueError, match="no fault lines"):
        empty.plot()


def _measured_envelope_spectrum() -> object:
    """An envelope spectrum of a modulated carrier, as the overlay is fed one."""
    from phonometry import signals

    fs = 8192.0
    t = np.arange(int(fs)) / fs
    signal = (1.0 + 0.5 * np.cos(2.0 * np.pi * 207.0 * t)) * np.cos(
        2.0 * np.pi * 2000.0 * t
    )
    return signals.envelope_spectrum(signal, fs)


@pytest.mark.parametrize("field", ["frequencies", "amplitude"])
def test_a_non_finite_measured_spectrum_is_refused_by_field(field: str) -> None:
    """Both vectors of ``spectrum`` scale an axis, so a NaN in either ends the figure.

    The frequency axis runs to the top of the measured one and the amplitude
    axis to its peak, taken with ``np.max``, so one non-finite sample becomes
    the whole limit and matplotlib stops the render with "Axis limits cannot
    be NaN or Inf", naming neither the argument nor the field inside it.
    ``spectrum`` is a structural contract, anything exposing the two vectors,
    so there is no construction of ours to pin it at and the refusal is where
    the caller's parameter is named. No producer emits one:
    :func:`phonometry.signals.envelope.envelope_spectrum` refuses a non-finite
    record before it transforms it.
    """
    pytest.importorskip("matplotlib")
    import dataclasses

    import matplotlib as mpl

    mpl.use("Agg")

    res = vibration.bearing_fault_frequencies(
        2000.0, 15, 6.0, 34.0, contact_angle_deg=12.96
    )
    spectrum = _measured_envelope_spectrum()
    corrupt = np.asarray(getattr(spectrum, field)).copy()
    corrupt[100] = np.nan
    bad = dataclasses.replace(spectrum, **{field: corrupt})  # type: ignore[type-var]
    with pytest.raises(
        ValueError, match=f"'spectrum.{field}' must contain only finite"
    ):
        res.plot(spectrum=bad)


def test_a_measured_spectrum_of_two_lengths_is_refused_by_the_overlay() -> None:
    """One amplitude per frequency bin, named where the caller's parameter is.

    The curve is drawn from ``frequencies <= max_frequency`` applied to both
    vectors, so an amplitude shorter than its own axis is indexed by a mask
    built on the longer one and numpy ends the render with "boolean index did
    not match indexed array along axis 0", naming neither ``spectrum`` nor the
    field inside it. Every sample here is finite, so the non-finite guard
    beside this one does not cover the mistake.

    ``EnvelopeSpectrumResult`` pins the pair when it is built, which is why the
    mismatch is assembled here as a loose object: the structural contract of
    ``spectrum`` is the only way in.
    """
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")

    res = vibration.bearing_fault_frequencies(
        2000.0, 15, 6.0, 34.0, contact_angle_deg=12.96
    )
    measured = _measured_envelope_spectrum()
    frequencies = np.asarray(measured.frequencies)  # type: ignore[attr-defined]
    amplitude = np.asarray(measured.amplitude)[:-1]  # type: ignore[attr-defined]
    assert np.all(np.isfinite(frequencies))
    assert np.all(np.isfinite(amplitude))
    mismatched = SimpleNamespace(frequencies=frequencies, amplitude=amplitude)
    with pytest.raises(
        ValueError,
        match=(
            r"'spectrum\.frequencies' \(\d+,\), 'spectrum\.amplitude' \(\d+,\) "
            r"must all have the same shape"
        ),
    ):
        res.plot(spectrum=mismatched)


@pytest.mark.parametrize(
    ("label", "shape"),
    [("empty", (0,)), ("bare numbers", ()), ("a grid", (3, 2))],
)
def test_a_spectrum_that_is_not_a_run_of_bins_is_refused(
    label: str, shape: tuple[int, ...]
) -> None:
    """What the equal-shape pin beside this one cannot see.

    That pin compares the two shapes against each other, so a pair that
    agrees walks past it whatever the shape is: two bare numbers agree on the
    empty shape and two grids agree on both of theirs. Only the empty pair
    announced itself, and anonymously, as numpy's "zero-size array to
    reduction operation maximum which has no identity" from the axis scaling.
    The other two drew: the numbers as a single point under limits matplotlib
    widened for being singular, the grid as one line per column over an axis
    that was never measured on them.
    """
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")

    res = vibration.bearing_fault_frequencies(
        2000.0, 15, 6.0, 34.0, contact_angle_deg=12.96
    )
    malformed = SimpleNamespace(frequencies=np.zeros(shape), amplitude=np.zeros(shape))
    with pytest.raises(
        ValueError,
        match=r"'spectrum\.frequencies' must be a non-empty one-dimensional",
    ):
        res.plot(spectrum=malformed)


def test_the_overlay_scales_its_amplitude_axis_to_the_measured_peak() -> None:
    """The refusal sits in front of the measurement, which still sets the axis.

    The y limit is the peak of the drawn part of the curve, lifted by the
    strip the rotated line names are laid out in, so the check above cannot
    have replaced ``np.max`` with a NaN-tolerant reading of a corrupt curve.
    """
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")

    res = vibration.bearing_fault_frequencies(
        2000.0, 15, 6.0, 34.0, contact_angle_deg=12.96
    )
    spectrum = _measured_envelope_spectrum()
    ax = res.plot(spectrum=spectrum, max_frequency=600.0, annotate=False)
    kept = np.asarray(spectrum.frequencies) <= 600.0  # type: ignore[attr-defined]
    peak = float(np.max(np.asarray(spectrum.amplitude)[kept]))  # type: ignore[attr-defined]
    assert ax.get_ylim() == pytest.approx((0.0, 1.03 * peak))


def test_crowded_fault_labels_do_not_overlap() -> None:
    """Names of nearby lines are pushed apart instead of stacking up.

    On a wide axis the low-frequency bearing lines (FTF 13,8 Hz, FTF_rel
    19,5 Hz and the 33,3 Hz shaft) fall within a few points of each other and
    their rotated labels used to be drawn on top of one another.
    """
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    from phonometry._plot.vibration import _LABEL_WIDTH_PT, _label_offsets

    res = vibration.bearing_fault_frequencies(
        2000.0, 15, 6.0, 34.0, contact_angle_deg=12.96
    )
    ax = res.plot(max_frequency=1200.0)
    assert len(ax.texts) == len(res.lines)

    # Every label must clear the previous one across the axis.
    width_pt, f_max = 450.0, 1200.0
    freqs = [line.frequency for line in res.lines]
    offsets = _label_offsets(freqs, f_max, width_pt)
    placed = sorted(f * width_pt / f_max + offsets[i] for i, f in enumerate(freqs))
    assert min(np.diff(placed)) >= _LABEL_WIDTH_PT - 1e-9
    # An isolated line keeps its label where it was: BPFI has no near neighbour.
    assert offsets[freqs.index(res["BPFI"])] == pytest.approx(2.0)


def test_power_injection_labels() -> None:
    """The SEA loss-factor budget localises its axes and title."""
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")

    f = np.array([250.0, 500.0, 1000.0])
    res = vibration.power_injection_clf(f, 0.087, 0.013, 4.4e-3, 2.4e-3, 0.557, 0.606)

    ax_en = res.plot()
    assert ax_en.get_xlabel() == "Frequency [Hz]"
    assert ax_en.get_ylabel() == "Loss factor"
    assert "single-drive" in ax_en.get_title()

    ax_es = res.plot(language="es")
    assert ax_es.get_xlabel() == "Frecuencia [Hz]"
    assert ax_es.get_ylabel() == "Factor de pérdidas"
    assert "excitación única" in ax_es.get_title()

    with pytest.raises(ValueError, match="Unknown language"):
        res.plot(language="xx")


def test_seat_transmission_draws_every_run_and_both_means() -> None:
    """The bars are the runs themselves, and the lines the means the SEAT is of."""
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")

    seat_runs = (0.72, 0.70, 0.71)
    platform_runs = (1.02, 1.00, 0.99)
    res = vibration.seat_transmission(seat_runs, platform_runs)

    ax = res.plot()
    bars = [patch.get_height() for patch in ax.patches]
    assert bars == pytest.approx([*platform_runs, *seat_runs])
    # Platform and seat sit on either side of the run number, never on top.
    centres = [patch.get_x() + patch.get_width() / 2 for patch in ax.patches]
    assert centres[:3] == pytest.approx([0.82, 1.82, 2.82])
    assert centres[3:] == pytest.approx([1.18, 2.18, 3.18])
    assert list(ax.get_xticks()) == pytest.approx([1.0, 2.0, 3.0])

    means = sorted(line.get_ydata()[0] for line in ax.lines)
    assert means == pytest.approx(
        sorted((res.seat_acceleration, res.platform_acceleration))
    )

    assert ax.get_xlabel() == "Test run"
    assert ax.get_ylabel() == "Weighted r.m.s. acceleration [m/s²]"
    assert ax.get_title() == "Seat transmission (ISO 10326-1): SEAT = 0.71"
    # Each mean is listed right after the set it averages.
    labels = [text.get_text() for text in ax.get_legend().get_texts()]
    assert labels == [
        "platform $a_\\mathrm{wP}$",
        "mean 1.00",
        "seat $a_\\mathrm{wS}$",
        "mean 0.71",
    ]


def test_seat_transmission_spanish_labels() -> None:
    """Every string of the figure, including the two means, crosses over."""
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")

    res = vibration.seat_transmission((0.72, 0.70, 0.71), (1.02, 1.00, 0.99))

    ax = res.plot(language="es")
    assert ax.get_xlabel() == "Pasada"
    assert ax.get_ylabel() == "Aceleración eficaz ponderada [m/s²]"
    assert ax.get_title() == "Transmisión del asiento (ISO 10326-1): SEAT = 0,71"
    labels = [text.get_text() for text in ax.get_legend().get_texts()]
    assert labels == [
        "plataforma $a_\\mathrm{wP}$",
        "media 1,00",
        "asiento $a_\\mathrm{wS}$",
        "media 0,71",
    ]

    with pytest.raises(ValueError, match="Unknown language"):
        res.plot(language="xx")


def test_seat_transmission_forwards_kwargs_to_the_seat_bars() -> None:
    """The seat set is the one a caller restyles; the platform stays put."""
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")

    res = vibration.seat_transmission((0.72, 0.70, 0.71), (1.02, 1.00, 0.99))
    ax = res.plot(color="#123456", label="cushion")

    assert [patch.get_facecolor()[:3] for patch in ax.patches[3:]] == [
        pytest.approx((0x12 / 255, 0x34 / 255, 0x56 / 255))
    ] * 3
    labels = [text.get_text() for text in ax.get_legend().get_texts()]
    assert labels[2] == "cushion"
    assert labels[0] == "platform $a_\\mathrm{wP}$"


def test_the_damage_assessment_draws_the_table_it_was_read_against() -> None:
    """A top-floor reading is not drawn against the foundation curves.

    Table 1 at the foundation is a function of frequency; in the topmost
    floor plane, and in the whole of Table 3, it is one number per building
    class. Showing the frequency curves for a reading judged against those
    would put a criterion on the page that did not apply to it.
    """
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")

    at_a_frequency = vibration.assess_building_vibration(
        4.0, building_class="residential", frequency_hz=30.0
    )
    ax = at_a_frequency.plot()
    assert ax.get_title() == "Guideline values at the foundation (DIN 4150-3 Table 1)"
    assert ax.get_xlabel() == "Frequency [Hz]"
    # The three Table 1 curves, plus the reading.
    assert len(ax.lines) == 4
    assert not ax.patches
    assert "measured 4 mm/s at 30 Hz" in [
        t.get_text() for t in ax.get_legend().get_texts()
    ]

    flat = vibration.assess_building_vibration(
        12.0, building_class="residential", location="top_floor"
    )
    ax = flat.plot()
    assert ax.get_title() == (
        "Guideline values in the topmost floor plane (DIN 4150-3 Table 1)"
    )
    assert ax.get_xlabel() == "Building class"
    # One bar per class, the assessed one at full opacity, and no curve.
    assert [patch.get_height() for patch in ax.patches] == pytest.approx(
        [40.0, 15.0, 8.0]
    )
    assert [patch.get_alpha() for patch in ax.patches] == [0.45, 1.0, 0.45]
    assert [t.get_text() for t in ax.get_legend().get_texts()] == ["measured 12 mm/s"]
    # The reading sits on its own class, not on a frequency.
    assert ax.lines[0].get_xdata() == pytest.approx([1.0])
    assert ax.lines[0].get_ydata() == pytest.approx([12.0])

    long_term = vibration.assess_building_vibration(
        2.0, building_class="residential", location="top_floor", duration="long_term"
    )
    ax = long_term.plot(language="es")
    assert ax.get_title() == (
        "Valores de referencia de larga duración en el plano de la última planta "
        "(DIN 4150-3, tabla 3)"
    )
    assert [patch.get_height() for patch in ax.patches] == pytest.approx(
        [10.0, 5.0, 2.5]
    )
    assert [t.get_text() for t in ax.get_legend().get_texts()] == ["medido 2 mm/s"]


@pytest.mark.parametrize(
    ("given", "defaulted"),
    [
        ({"c": "#654321"}, "color"),
        ({"linestyle": "-"}, "ls"),
        ({"ms": 12}, "markersize"),
    ],
)
def test_the_damage_reading_keeps_the_spelling_the_caller_used(
    given: dict[str, object], defaulted: str
) -> None:
    """A style given under either alias must not meet the renderer's default.

    Matplotlib refuses a call that carries both spellings of one property
    ("Got both 'color' and 'c', which are aliases of one another"), so
    injecting a default under the spelling the caller did not use turns a
    styled plot into a ``TypeError``.
    """
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    res = vibration.assess_building_vibration(
        4.0, building_class="residential", frequency_hz=30.0
    )

    ax = res.plot(**given)  # type: ignore[arg-type]

    reading = ax.lines[-1]
    if defaulted == "color":
        assert reading.get_color() == "#654321"
    elif defaulted == "ls":
        assert reading.get_linestyle() == "-"
    else:
        assert reading.get_markersize() == 12


def test_bild_1_refuses_an_assessment_that_has_no_frequency() -> None:
    """A hand-built foundation assessment without one is not on the figure.

    ``assess_building_vibration`` cannot produce it, but ``DamageAssessment``
    is public and can be constructed directly. Parking the point at the axis
    limit and labelling it "at 100 Hz" would report a frequency nobody
    measured, which is the defect the other branch already refuses.
    """
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    from phonometry.vibration.structural.building_damage import DamageAssessment

    orphan = DamageAssessment(
        velocity_mm_s=4.0,
        guideline_mm_s=10.0,
        building_class="residential",
        location="foundation",
        duration="short_term",
        frequency_hz=None,
    )
    with pytest.raises(ValueError, match=r"carries none"):
        orphan.plot()


def test_the_building_frequency_figure_puts_the_estimate_beside_the_fit() -> None:
    """Figure D.1 is the fit, its ± 50 % band and the one estimate on it."""
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    res = vibration.estimate_fundamental_frequency("height", height_m=40.0)

    ax = res.plot()
    fit, point = ax.lines
    # The fit is drawn as f against h, so the frequency is the x coordinate.
    assert fit.get_xdata()[0] * fit.get_ydata()[0] == pytest.approx(46.0)
    assert point.get_xdata() == pytest.approx([res.frequency_hz])
    assert point.get_ydata() == pytest.approx([40.0])
    assert (ax.get_xscale(), ax.get_yscale()) == ("log", "log")

    labels = [text.get_text() for text in ax.get_legend().get_texts()]
    assert labels == [
        "$f = 46/h$",
        "$\\pm$50 %, which D.3 calls not uncommon",
        "height model: 1.14 Hz at 40 m",
    ]
    assert ax.get_ylabel() == "Building height $h$ [m]"

    labels_es = [
        text.get_text() for text in res.plot(language="es").get_legend().get_texts()
    ]
    assert labels_es[0] == "$f = 46/h$"
    assert labels_es[2] == "modelo de altura: 1,14 Hz a 40 m"

    with pytest.raises(ValueError, match="Unknown language"):
        res.plot(language="xx")


@pytest.mark.parametrize(
    ("given", "reads"),
    [
        ({"c": "#654321"}, "color"),
        ({"linestyle": "-"}, "ls"),
        ({"ms": 12}, "markersize"),
    ],
)
def test_the_frequency_estimate_keeps_the_spelling_the_caller_used(
    given: dict[str, object], reads: str
) -> None:
    """The same alias trap as the damage reading, on the other new figure."""
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    res = vibration.estimate_fundamental_frequency("height", height_m=40.0)

    point = res.plot(**given).lines[-1]  # type: ignore[arg-type]

    if reads == "color":
        assert point.get_color() == "#654321"
    elif reads == "ls":
        assert point.get_linestyle() == "-"
    else:
        assert point.get_markersize() == 12


def test_the_meter_verification_draws_the_band_it_was_judged_against() -> None:
    """The band comes from Table 5, so it widens where the standard widens it."""
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    from phonometry.vibration.human.instrumentation import TRANSITION_FREQUENCIES_HZ

    f = np.array([0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 31.5, 63.0, 80.0])
    design = np.asarray(vibration.weighting_factors("Wk", f))
    res = vibration.verify_weighting("Wk", f, design)

    ax = res.plot()
    assert ax.get_title() == "Wk weighting against ISO 8041-1: PASS"
    assert ax.get_ylabel() == "Weighting factor"
    assert (ax.get_xscale(), ax.get_yscale()) == ("log", "log")
    labels = [text.get_text() for text in ax.get_legend().get_texts()]
    assert labels == ["ISO 8041-1 tolerance", "design goal", "within tolerance"]

    # The band is the Table 5 one, not a fixed number of decibels: at 16 Hz,
    # inside the central region, it is +12 % / -11 % of the design goal.
    band = ax.collections[0].get_paths()[0].vertices
    _, ft2, ft3, _ = TRANSITION_FREQUENCIES_HZ["Wk"]
    assert ft2 < 16.0 < ft3
    at_16 = [y for x, y in band if x == pytest.approx(16.0)]
    design_16 = float(design[list(f).index(16.0)])
    assert (min(at_16), max(at_16)) == pytest.approx(
        (design_16 * 0.89, design_16 * 1.12)
    )

    # And at 0,5 Hz, past ft1 and inside the lower skirt, it opens to
    # +26 % / -21 %.
    ft1 = TRANSITION_FREQUENCIES_HZ["Wk"][0]
    assert ft1 < 0.5 < ft2
    at_half = [y for x, y in band if x == pytest.approx(0.5)]
    design_half = float(design[0])
    assert (min(at_half), max(at_half)) == pytest.approx(
        (design_half * 0.79, design_half * 1.26)
    )

    # A failing point is drawn apart from the ones inside.
    off = design.copy()
    off[5] *= 1.2
    failing = vibration.verify_weighting("Wk", f, off).plot()
    assert "FAIL" in failing.get_title()
    assert [t.get_text() for t in failing.get_legend().get_texts()][-1] == (
        "outside tolerance"
    )
    assert failing.lines[-1].get_xdata() == pytest.approx([16.0])


def test_the_meter_verification_speaks_spanish() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    f = np.array([1.0, 8.0, 80.0])
    design = np.asarray(vibration.weighting_factors("Wd", f))
    res = vibration.verify_weighting("Wd", f, design)

    ax = res.plot(language="es")
    assert ax.get_title() == "Ponderación Wd frente a ISO 8041-1: CUMPLE"
    assert ax.get_ylabel() == "Factor de ponderación"
    assert ax.get_xlabel() == "Frecuencia [Hz]"
    labels = [text.get_text() for text in ax.get_legend().get_texts()]
    assert labels == [
        "tolerancia de ISO 8041-1",
        "objetivo de diseño",
        "dentro de tolerancia",
    ]

    with pytest.raises(ValueError, match="Unknown language"):
        res.plot(language="xx")


def _phase_verdict(weighting: str, offset_deg: float) -> object:
    """A phase response sitting ``offset_deg`` from the design goal."""
    f = np.array([10.0 ** (n / 10.0) for n in range(-10, 27)])
    response = vibration.frequency_weighting(weighting, f).response
    design = np.degrees(np.unwrap(np.angle(response)))
    return vibration.verify_phase_response(weighting, f, design + offset_deg)


def test_the_phase_verification_draws_the_band_it_was_judged_against() -> None:
    """The band is the Table 5 phase column, which is a limit on a modulus.

    So it is drawn from the axis floor up to the limit rather than around a
    line, and the two tails, where the standard sets no limit at all, are
    filled to the top of the axes instead of to infinity.
    """
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    from phonometry.vibration.human.instrumentation import TRANSITION_FREQUENCIES_HZ

    res = _phase_verdict("Wk", 3.0)
    ax = res.plot()
    assert (
        ax.get_title() == "Wk characteristic phase deviation against ISO 8041-1: PASS"
    )
    assert ax.get_ylabel() == "Characteristic phase deviation [deg]"
    assert ax.get_xscale() == "log"
    labels = [text.get_text() for text in ax.get_legend().get_texts()]
    assert labels == ["ISO 8041-1 tolerance", "within tolerance"]

    band = ax.collections[0].get_paths()[0].vertices
    _, ft2, ft3, _ = TRANSITION_FREQUENCIES_HZ["Wk"]
    at_16 = [y for x, y in band if x == pytest.approx(15.848931924611133)]
    assert ft2 < 15.85 < ft3
    assert (min(at_16), max(at_16)) == pytest.approx((0.0, 6.0))
    ceiling = ax.get_ylim()[1]
    at_tail = [y for x, y in band if x == pytest.approx(0.1)]
    assert max(at_tail) == pytest.approx(ceiling)

    failing = _phase_verdict("Wk", 8.0).plot()
    assert "FAIL" in failing.get_title()
    assert [t.get_text() for t in failing.get_legend().get_texts()][-1] == (
        "outside tolerance"
    )


def test_the_phase_verification_speaks_spanish() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    res = _phase_verdict("Wd", 3.0)

    ax = res.plot(language="es")
    assert ax.get_title() == (
        "Desviación característica de fase de Wd frente a ISO 8041-1: CUMPLE"
    )
    assert ax.get_ylabel() == "Desviación característica de fase [grados]"
    assert ax.get_xlabel() == "Frecuencia [Hz]"
    labels = [text.get_text() for text in ax.get_legend().get_texts()]
    assert labels == ["tolerancia de ISO 8041-1", "dentro de tolerancia"]

    with pytest.raises(ValueError, match="Unknown language"):
        res.plot(language="xx")


def test_the_meter_figure_draws_the_band_the_verdict_actually_uses() -> None:
    """With a laboratory uncertainty, the accepted band is not the printed one.

    13.1 and 14.1 subtract the laboratory's expanded uncertainty from both
    limits, so a measurement can sit inside the Table 5 band and still fail.
    Drawing only the printed band put a red X on a point inside the shaded
    region with nothing on the axes to explain it.
    """
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")

    design = float(np.asarray(vibration.weighting_factors("Wk", [16.0]))[0])
    result = vibration.verify_weighting(
        "Wk", [16.0], [design * 1.115], expanded_uncertainty_percent=1.0
    )
    assert not result.passes

    ax = result.plot()
    bands = [
        (
            min(y for _, y in c.get_paths()[0].vertices),
            max(y for _, y in c.get_paths()[0].vertices),
        )
        for c in ax.collections
    ]
    assert len(bands) == 2
    printed, accepted = bands
    assert printed == pytest.approx((design * 0.89, design * 1.12))
    assert accepted == pytest.approx((design * 0.90, design * 1.11))
    # The measurement sits inside the printed band and outside the accepted one.
    assert printed[0] < design * 1.115 < printed[1]
    assert design * 1.115 > accepted[1]

    labels = [text.get_text() for text in ax.get_legend().get_texts()]
    assert "accepted with U = 1 %" in labels
    assert "aceptado con U = 1 %" in [
        t.get_text() for t in result.plot(language="es").get_legend().get_texts()
    ]


def test_the_meter_figure_draws_one_band_when_no_uncertainty_is_given() -> None:
    """Without one the printed band is the accepted band, so there is one."""
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")

    f = np.array([1.0, 8.0, 80.0])
    design = np.asarray(vibration.weighting_factors("Wk", f))
    ax = vibration.verify_weighting("Wk", f, design).plot()
    assert len(ax.collections) == 1
    assert "accepted with U" not in " ".join(
        t.get_text() for t in ax.get_legend().get_texts()
    )
