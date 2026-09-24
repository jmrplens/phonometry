#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Fiches for the measuring and reproducing hardware itself.

What an instrument is rated at and whether it meets its class: the octave-band
filter class of IEC 61260-1 in both its editions, the class of a p-p intensity
chain (IEC 61043), the rated characteristics a loudspeaker (IEC 60268-5) and a
microphone (IEC 60268-4) are declared with, and the free-field corrections of a
sound level meter with the uncertainty they are judged on (IEC 62585).
"""

from __future__ import annotations

import numpy as np

import phonometry as ph
from phonometry import ReportMetadata


def _filter_class_example() -> tuple[object, ReportMetadata, str]:
    """Filter-compliance fiche: an IEC 61260-1 octave-band class verification.

    The default Butterworth order-6 octave bank from 125 Hz to 4 kHz, each
    band decimated, clears class 1 on the Table 1 mask, the effective
    bandwidth deviation of 5.12 and the summation of 5.16, so the fiche boxes
    a Class 1 COMPLIES result and passes the required-class-1 verdict.
    """
    bank = ph.filters.OctaveFilterBank(
        fs=48000, fraction=1, order=6, limits=[125, 4000]
    )
    result = ph.filters.verify_filter_class(bank)
    metadata = ReportMetadata(
        specimen="1/1-octave filter bank",
        client="Example client",
        manufacturer="Example instruments",
        test_room="Electroacoustics laboratory (example)",
        measurement_standard="IEC 61260-1:2014",
        test_date="2026-07-20",
        laboratory="Phonometry reference example",
        operator="phonometry",
        report_id="EXAMPLE-61260",
        required_class=1,
    )
    return result, metadata, "iec61260_filter_example.pdf"


def _filter_class_1995_example() -> tuple[object, ReportMetadata, str]:
    """Filter-compliance fiche under the 1995 edition, which keeps class 0.

    IEC 61260-1:2014 dropped class 0; the older IEC 61260:1995 /
    ANSI S1.11-2004 retains it. Selecting ``edition="1995"`` verifies against
    that mask, and the default (order 6) octave bank clears the stricter
    class 0, so the fiche boxes a Class 0 COMPLIES result.
    """
    bank = ph.filters.OctaveFilterBank(
        fs=48000, fraction=1, order=6, limits=[250, 4000]
    )
    result = ph.filters.verify_filter_class(bank, edition="1995")
    metadata = ReportMetadata(
        specimen="1/1-octave filter bank",
        client="Example client",
        manufacturer="Example instruments",
        test_room="Electroacoustics laboratory (example)",
        measurement_standard="IEC 61260:1995",
        test_date="2026-07-20",
        laboratory="Phonometry reference example",
        operator="phonometry",
        report_id="EXAMPLE-61260-1995",
        required_class=0,
    )
    return result, metadata, "iec61260_filter_1995_example.pdf"


def _intensity_class_example() -> tuple[object, ReportMetadata, str]:
    """IEC 61043 fiche: class verification of a p-p intensity chain.

    A complete instrument fitted with the common 12 mm spacer. The measured
    index follows the physics behind Table 2: a residual channel phase
    mismatch ``phi_s`` reads as ``delta_pI0 = 10 lg(kd/phi_s)``, so a mismatch
    that is constant in degrees already climbs 10 dB per decade (the slope of
    the requirement below 250 Hz) and levels off above 1 kHz where the
    mismatch of a real chain grows with frequency. A vent resonance of the
    capsules costs 4 dB around 100 Hz, the one band that drops out of class 1,
    so the fiche boxes a Class 2 COMPLIES result and fails the
    required-class-1 verdict, showing both halves of the layout at once.
    """
    spacing = 0.012
    freqs, _, _ = ph.emission.residual_index_limits("instrument", spacing=spacing)
    phase_mismatch = 0.05 * np.maximum(1.0, freqs / 1000.0)  # degrees
    measured = ph.emission.residual_index_from_phase_mismatch(
        phase_mismatch, freqs, spacing
    )
    measured = measured - 4.0 * np.exp(-((np.log(freqs / 100.0) / 0.25) ** 2))
    result = ph.emission.verify_intensity_class(measured, freqs, spacing=spacing)
    metadata = ReportMetadata(
        specimen="p-p sound intensity probe and analyser, 12 mm spacer",
        client="Example client",
        manufacturer="Example instruments",
        test_room="Electroacoustics laboratory (example)",
        measurement_standard="IEC 61043:1993",
        test_date="2026-07-20",
        laboratory="Phonometry reference example",
        operator="phonometry",
        report_id="EXAMPLE-61043",
        required_class=1,
    )
    return result, metadata, "iec61043_intensity_example.pdf"


def _loudspeaker_example() -> tuple[object, ReportMetadata, str]:
    """IEC 60268-5 fiche: the rated characteristics of a two-way loudspeaker.

    A synthetic on-axis response of an 8 ohm bookshelf loudspeaker: a flat
    passband near 87 dB with a gentle ripple, a low-frequency roll-off below
    50 Hz and a high-frequency roll-off above 16 kHz, so the effective frequency
    range (IEC 60268-5 21.2) sits inside the measured band. The characteristic
    sensitivity is referred to 1 W into 8 ohm at 1 m (the default 2,83 V drive),
    and the impedance modulus, the total-harmonic-distortion curve and a baffled
    circular-piston directivity feed the impedance, THD and polar panels. The
    requirement is a characteristic sensitivity the example clears.
    """
    freqs = np.geomspace(30.0, 24000.0, 320)
    reference = 87.0
    spl = reference + 1.2 * np.sin(2.0 * np.log2(freqs / 900.0))
    spl -= 10.0 * np.log10(1.0 + (50.0 / freqs) ** 6)  # LF roll-off
    spl -= 10.0 * np.log10(1.0 + (freqs / 16000.0) ** 7)  # HF roll-off

    imp_freqs = np.geomspace(20.0, 20000.0, 260)
    impedance = (
        6.6
        + 24.0 * np.exp(-((np.log2(imp_freqs / 52.0)) ** 2) / 0.12)  # resonance peak
        + 5.0 * (imp_freqs / 20000.0) ** 1.5  # voice-coil rise
    )

    thd_freqs = np.geomspace(50.0, 5000.0, 140)
    thd_percent = 0.3 + 2.6 * np.exp(-((np.log2(thd_freqs / 70.0)) ** 2) / 0.45)

    angles = np.radians(np.linspace(0.0, 90.0, 46))
    directivity = ph.electroacoustics.radiating_piston(
        0.075, np.array([1000.0, 2000.0, 4000.0]), angles_rad=angles
    )

    result = ph.electroacoustics.loudspeaker_characteristics(
        freqs,
        spl,
        8.0,
        sensitivity_band=(200.0, 4000.0),
        tolerance_db=3.0,
        impedance=(imp_freqs, impedance),
        distortion=(thd_freqs, thd_percent),
        directivity=ph.electroacoustics.LoudspeakerDirectivity(
            piston=directivity, frequency=2000.0
        ),
        ratings=ph.electroacoustics.LoudspeakerRatings(
            frequency_range=(45.0, 22000.0),
            noise_power=80.0,
            sinusoidal_power=120.0,
            resonance_frequency=52.0,
        ),
    )
    metadata = ReportMetadata(
        specimen="Two-way bookshelf loudspeaker, 165 mm woofer",
        client="Example client",
        manufacturer="Example audio",
        test_room="Anechoic chamber (example)",
        mounting="Free field, on the tweeter axis at 1 m",
        measurement_standard="IEC 60268-5",
        temperature_c=21.0,
        relative_humidity_percent=45.0,
        static_pressure_kpa=101.3,
        test_date="2026-07-20",
        laboratory="Phonometry reference example",
        operator="phonometry",
        report_id="EXAMPLE-60268-5",
        requirement=84.0,
    )
    return result, metadata, "iec60268_5_loudspeaker_example.pdf"


def _microphone_example() -> tuple[object, ReportMetadata, str]:
    """IEC 60268-4 fiche: the rated characteristics of a cardioid condenser mic.

    A synthetic free-field response of a phantom-powered studio condenser
    microphone: flat around the 1 kHz reference with a gentle +2 dB presence
    region near 9 kHz, a low-frequency roll-off crossing -3 dB near 30 Hz and a
    high-frequency roll-off crossing -3 dB near 19 kHz, so the effective
    frequency range (IEC 60268-4 12.2) sits inside the measured band. The rated
    free-field sensitivity of 12,5 mV/Pa gives a sensitivity level of
    20 lg 0,0125 = -38,1 dB re 1 V/Pa (11.1); the A-weighted inherent-noise
    voltage yields the equivalent noise level (17.2); the ideal-cardioid
    directional pattern at 1 kHz yields a directivity index of 10 lg 3 = 4,8 dB
    (13.2.2); and the distortion-against-level curve places the overload sound
    pressure level at the 0,5 % THD limit (15.2). The requirement is a maximum
    equivalent noise level the example clears.
    """
    freqs = np.geomspace(20.0, 20000.0, 400)
    response = (
        -10.0 * np.log10(1.0 + (30.0 / freqs) ** 4)  # LF roll-off
        - 10.0 * np.log10(1.0 + (freqs / 19000.0) ** 8)  # HF roll-off
        + 2.0 * np.exp(-((np.log2(freqs / 9000.0)) ** 2) / 0.3)  # presence
    )

    angles = np.linspace(0.0, 179.0, 359)
    cardioid_db = 20.0 * np.log10((1.0 + np.cos(np.radians(angles))) / 2.0)

    thd_spl = np.linspace(100.0, 140.0, 81)
    thd_percent = 0.5 * 10.0 ** ((thd_spl - 130.0) * 0.08)

    noise_freqs = np.geomspace(20.0, 20000.0, 31)
    noise_levels = (
        18.0 - 5.4 * np.log2(noise_freqs / 20.0) + 1.5 * np.sin(np.log2(noise_freqs))
    )

    result = ph.electroacoustics.microphone_characteristics(
        freqs,
        response,
        12.5,
        tolerance_db=3.0,
        directivity=ph.electroacoustics.MicrophoneDirectivity(
            polar=(angles, cardioid_db),
            frequency=1000.0,
        ),
        noise=ph.electroacoustics.MicrophoneNoise(
            voltage=1.25e-6,
            spectrum=(noise_freqs, noise_levels),
        ),
        overload=ph.electroacoustics.MicrophoneOverload(
            distortion=(thd_spl, thd_percent),
            thd_percent=0.5,
        ),
        electrical=ph.electroacoustics.MicrophoneElectrical(
            rated_impedance=150.0,
            minimum_load_impedance=1000.0,
            powering="Phantom P48 (IEC 61938)",
            supply_current_ma=3.1,
        ),
    )
    metadata = ReportMetadata(
        specimen="Cardioid condenser microphone, 25 mm capsule",
        client="Example client",
        manufacturer="Example audio",
        test_room="Anechoic chamber (example)",
        mounting="Free field, reference axis towards the source at 1 m",
        measurement_standard="IEC 60268-4",
        temperature_c=21.0,
        relative_humidity_percent=45.0,
        static_pressure_kpa=101.3,
        test_date="2026-07-20",
        laboratory="Phonometry reference example",
        operator="phonometry",
        report_id="EXAMPLE-60268-4",
        requirement=16.0,
    )
    return result, metadata, "iec60268_4_microphone_example.pdf"


def _free_field_correction_example() -> tuple[object, ReportMetadata, str]:
    """IEC 62585 fiche: a meter's corrections on its calibrator, clause 12.

    The synthetic class 1 meter of the guide signals/metrology/
    free-field-corrections, measured at the nine exact octaves from 63 Hz to
    16 kHz with three microphones by Formula (D.7), each frequency given a
    budget with the 15 components of Table I.1: the values of Table I.2 up
    to 1 kHz, and a free-field correction of the reference, a field and
    mountings and a repeatability that grow above it. Every expanded
    uncertainty, and the range over the three microphones, is within the
    maximum of clause 12, so the fiche states the corrections usable.
    """
    f = ph.metrology.exact_frequencies(63, 16000, fraction=1)
    x = f / 1000
    c_ff_rm = 0.05 * x**1.3
    free = 0.1 * np.sin(np.log(x)) - 0.05 * x**1.2
    pressure = -0.1 * x**1.5
    spread = np.array([[0.0], [0.02], [-0.03]]) * x**0.8
    correction = ph.metrology.sound_calibrator_correction(
        f,
        94.0 + free + spread,
        94.0 + c_ff_rm,
        94.0 + pressure + spread / 2,
        94.0,
        reference_free_field_correction_db=c_ff_rm,
    )
    table_i2 = {
        "a1": 0.005,
        "a2": 0.005,
        "a3": 0.005,
        "a4": 0.005,
        "a5": 0.05,
        "a6": 0.0,
        "a7": 0.06,
        "a8": 0.025,
        "a9": 0.025,
        "a10": 0.029,
        "a11": 0.013,
        "a12": 0.013,
        "a13": 0.0,
        "a14": 0.005,
        "a15": 0.03,
    }
    a7 = (0.06, 0.06, 0.06, 0.06, 0.06, 0.08, 0.10, 0.17, 0.30)
    a11 = (0.013, 0.013, 0.013, 0.013, 0.013, 0.03, 0.06, 0.104, 0.18)
    a15 = (0.03, 0.03, 0.03, 0.03, 0.03, 0.04, 0.05, 0.06, 0.09)
    budgets = [
        ph.metrology.correction_uncertainty_budget(
            {**table_i2, "a7": u7, "a11": u11, "a12": u11, "a15": u15},
            repeatability_dof=2,
            frequency_hz=frequency,
            correction_db=value,
        )
        for frequency, u7, u11, u15, value in zip(
            f, a7, a11, a15, correction.correction_db, strict=True
        )
    ]
    result = ph.metrology.verify_correction_uncertainty(
        f,
        [b.expanded_uncertainty_db for b in budgets],
        clause=correction.clause,
        correction_db=correction.correction_db,
        coverage_factor=[b.coverage_factor for b in budgets],
        correction_range_db=correction.range_db,
    )
    metadata = ReportMetadata(
        specimen="Class 1 sound level meter with its multi-frequency calibrator",
        client="Example client",
        manufacturer="Example instruments",
        test_room="Free-field room (example)",
        measurement_standard="IEC 62585:2012 Annex D",
        test_date="2026-09-24",
        laboratory="Phonometry reference example",
        operator="phonometry",
        report_id="EXAMPLE-62585",
    )
    return result, metadata, "iec62585_free_field_correction_example.pdf"
