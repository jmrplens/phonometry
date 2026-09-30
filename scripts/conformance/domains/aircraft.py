#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Aircraft and rotorcraft noise, from certification to airport contours.

The certification side: the ICAO Annex 16 effective perceived noise level
chain (noy conversion, tone correction, duration correction) and the IEC 61265
requirements on the equipment that measures it, with the SAE ARP 866B/5534
atmospheric absorption underneath.

The airport-contour side: the ECAC Doc 29 single-event chain - noise-power
-distance interpolation, the noise fraction of a finite segment, impedance and
directivity adjustments, event assembly - checked against the reference
workbook that ships with the document, and the ECAC Doc 32 rotorcraft chain
with the NORAH2 guidance values for ground plane, flow resistivity and
diffraction.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np

import phonometry as ph

from ..registry import Outcome, aircraft_test_data, count, numeric, register

if TYPE_CHECKING:
    from types import ModuleType

    from phonometry.aircraft import RotorcraftHemisphere

_AIRCRAFT = "Aircraft noise (ICAO Annex 16 / IEC 61265)"


@register(
    _AIRCRAFT,
    "ECAC Doc 29 noise fraction (half path)",
    "Finite-segment correction ΔF for a perpendicular foot at the segment start, dB",
)
def _chk_ecac_noise_fraction() -> Outcome:
    # A half-infinite segment (Sp at the start) receives half the energy: −3.01 dB.
    got = float(ph.aircraft.noise_fraction(0.0, 10_000.0, 100.0))
    return numeric(-10.0 * math.log10(2.0), got, 1e-3, unit="dB", places=4)


@register(
    _AIRCRAFT,
    "ECAC Doc 29 single-event chain",
    "SEL of a long level flyover vs the infinite-path limit LE∞ + ΔI − Λ, dB",
)
def _chk_ecac_event_level() -> Outcome:
    # A long straight level segment through the CPA reduces to the infinite-path
    # baseline plus the geometry corrections (ΔF → 0, ΔV = 0 at Vref).
    npd_p = [8000.0, 12000.0]
    npd_d = [60.0, 120.0, 240.0, 480.0, 960.0, 1920.0, 3840.0]
    sel = [
        [98.0, 92.0, 86.0, 80.0, 74.0, 68.0, 62.0],
        [102.0, 96.0, 90.0, 84.0, 78.0, 72.0, 66.0],
    ]
    lmax = [
        [94.0, 88.0, 82.0, 76.0, 70.0, 64.0, 58.0],
        [98.0, 92.0, 86.0, 80.0, 74.0, 68.0, 62.0],
    ]
    vref = 160.0 * 0.514444

    xs = np.linspace(-40000.0, 40000.0, 801)
    path = np.column_stack(
        [
            xs,
            np.zeros_like(xs),
            np.full_like(xs, 300.0),
            np.full_like(xs, 10000.0),
            np.full_like(xs, vref),
        ]
    )
    got = ph.aircraft.event_level(
        path, [0.0, 300.0, 0.0], npd_p, npd_d, sel, lmax, metric="exposure"
    ).level
    dp = math.hypot(300.0, 300.0)
    beta = math.degrees(math.acos(300.0 / dp))
    expected = (
        float(ph.aircraft.npd_level(npd_p, npd_d, sel, 10000.0, dp)[0])
        + ph.aircraft.impedance_adjustment()
        + ph.aircraft.engine_installation_correction(beta, "wing")
        - ph.aircraft.lateral_attenuation(beta, 300.0)
    )
    return numeric(expected, float(got), 1e-2, unit="dB", places=3)


@register(
    _AIRCRAFT,
    "ECAC Doc 29 impedance adjustment (standard atmosphere)",
    "Acoustic-impedance adjustment of NPD data at 15 °C / 101.325 kPa (Eq. 4-6/4-7), dB",
)
def _chk_ecac_impedance() -> Outcome:
    # ECAC Doc 29 Vol 2 §4.2.1 states the standard-atmosphere adjustment is
    # +0.074 dB (ρc = 416.86, reference impedance 409.81 N·s/m³).
    return numeric(
        0.074,
        float(ph.aircraft.impedance_adjustment()),
        5e-4,
        unit="dB",
        places=4,
    )


@register(
    _AIRCRAFT,
    "ECAC Doc 29 reference workbook (segment Λ)",
    "Lateral attenuation of a climbing segment vs the ECAC Vol 3 Part 1 workbook, dB",
)
def _chk_ecac_workbook_segment() -> Outcome:
    # ECAC Doc 29 5th ed. Vol 3 Part 1 reference workbook, sheet
    # B-2_Segment_Results, case JETFAC receptor R02 segment 1 (climbing): the
    # workbook lists β = 4.2226°, lateral displacement 81363.28 ft (24799.6 m)
    # and Λ = 6.3769 dB. Here we anchor the Λ(β, ℓ) formula to those reference
    # values (the β/φ geometry itself is validated in tests/test_airport_noise).
    beta_ref, lateral_m = 4.2225708673, 81363.2829 * 0.3048
    got = float(ph.aircraft.lateral_attenuation(beta_ref, lateral_m))
    return numeric(6.3768594165, got, 1e-2, unit="dB", places=4)


@register(
    _AIRCRAFT,
    "ECAC Doc 29 start-of-roll directivity (jet)",
    "ΔSOR behind a takeoff ground-roll segment vs the Vol 3 Part 1 workbook, dB",
)
def _chk_ecac_start_of_roll() -> Outcome:
    # ECAC Doc 29 5th ed. Vol 3 Part 1 workbook, case JETFDC: at ψ = 112.8895°,
    # dSOR = 217.09 m the turbofan directivity (Eq. 4-24a) is +0.3196 dB.
    got = float(ph.aircraft.start_of_roll_directivity(112.889545, 217.0934, "jet"))
    return numeric(0.31961, got, 1e-2, unit="dB", places=4)


@register(
    _AIRCRAFT,
    "ECAC Doc 29 start-of-roll directivity (turboprop)",
    "ΔSOR behind a takeoff ground-roll segment (turboprop, Eq. 4-24b), dB",
)
def _chk_ecac_start_of_roll_prop() -> Outcome:
    # Same workbook, case PROPDC: at ψ = 128.1824°, dSOR = 254.44 m the turboprop
    # directivity (Eq. 4-24b) is +1.0943 dB.
    got = float(
        ph.aircraft.start_of_roll_directivity(128.182381, 254.4361, "turboprop")
    )
    return numeric(1.09434, got, 1e-2, unit="dB", places=4)


@register(
    _AIRCRAFT,
    "ECAC Doc 29 workbook event assembly (JETFDS/R03, behind SOR)",
    "Energy sum of the reference per-segment SELs vs the B-1 event total, dB",
)
def _chk_doc29_event_assembly() -> Outcome:
    # Doc 29 5th ed. Vol 3 Part 1 workbook, departure case JETFDS receptor R03
    # (centreline behind the start of roll): the Eq. 4-11 energy sum of the 29
    # reference segment SELs must reproduce the B-1 total 74.73 dB. No oracle
    # exists for per-event LAmax, non-zero bank angles or the Annex 16
    # bandsharing adjustment (no ETM worked example); registered gaps.
    workbook = aircraft_test_data("doc29_workbook_data")
    rows = workbook.SEGMENTS[("JETFDS", "R03")]
    total = 10.0 * math.log10(sum(10.0 ** (r[-1] / 10.0) for r in rows))
    return numeric(workbook.B1[("JETFDS", "R03")], total, 1e-2, unit="dB", places=3)


# ARP 5534 §3.2.2 splits the SAE Method at a mid-band attenuation of
# δ_t = 150 dB: Eq. 7 below it, Eq. 8 above. The library takes a path length
# rather than a δ_t, so the split is reached by scaling the path: one call at
# unit length returns α, and 150/α is the length at which δ_t lands exactly on
# the split. A hair either side of that length picks one branch or the other,
# and each is then judged against the *other* branch's printed formula, which
# is what continuity at the split means. At 10 kHz the split falls at a slant
# range of about 1,5 km, well inside the certification geometry.
_SPLIT_BAND_HZ = 10000.0


def _arp5534_at_split(offset: float) -> float:
    """Library δ_B (dB) at the path whose δ_t is ``150 (1 + offset)`` dB."""
    alpha = float(
        ph.aircraft.sae_band_attenuation([_SPLIT_BAND_HZ], 1.0).midband_attenuation[0]
    )
    res = ph.aircraft.sae_band_attenuation(
        [_SPLIT_BAND_HZ], 150.0 / alpha * (1.0 + offset)
    )
    return float(res.band_attenuation[0])


@register(
    _AIRCRAFT,
    "SAE ARP 5534 low branch at the split (Eq. 7)",
    "SAE-Method δ_B just below δ_t = 150 dB vs the printed Eq. 8 value there, dB",
)
def _chk_arp5534_continuity() -> Outcome:
    # Printed Eq. 8, 9,2 + 0,765 · 150 = 123,95 dB, against the library on its
    # Eq. 7 branch. The two printed branches do not meet to the digit: Eq. 7
    # gives 123,953 dB there, a step of 0,003 dB, which is the tolerance's
    # reason for being 0,01 dB rather than tighter.
    return numeric(
        9.2 + 0.765 * 150.0, _arp5534_at_split(-1e-9), 0.01, unit="dB", places=3
    )


@register(
    _AIRCRAFT,
    "SAE ARP 5534 high branch at the split (Eq. 8)",
    "SAE-Method δ_B just above δ_t = 150 dB vs the printed Eq. 7 value there, dB",
)
def _chk_arp5534_high_branch() -> Outcome:
    # The mirror of the row above: printed Eq. 7 at the split against the
    # library on its Eq. 8 branch, so a wrong constant in either printed
    # formula has a row that fails on it.
    a, b, c, d, e = 0.867942, 0.111761, 0.95824, 0.008191, 1.6
    eq7 = a * 150.0 * (1.0 + b * (c - d * 150.0)) ** e
    return numeric(eq7, _arp5534_at_split(1e-9), 0.01, unit="dB", places=3)


@register(
    _AIRCRAFT,
    "EASA ANP database round-trip",
    "Interpolated NPD level at a tabulated node vs the published ANP value, dB",
)
def _chk_anp_round_trip() -> Outcome:
    # Independent oracle: the EASA ANP database's own published NPD values
    # (curated subset shipped under aircraft/data/anp). At a tabulated
    # (power, distance) node the loader/interpolation must recover the
    # published value exactly. Boeing 747-100 (JT9DBD), departure SEL,
    # 28000 lb corrected net thrust, 2000 ft slant distance = 98.8 dB.
    curves = ph.aircraft.load_anp_database().npd_curves("747100", "departure", "SEL")
    got = float(curves.level(28000.0, 2000.0 * 0.3048)[0])
    return numeric(98.8, got, 1e-9, unit="dB", places=4)


@register(
    _AIRCRAFT,
    "ECAC Doc 29 NPD interpolation",
    "Log-linear NPD level at the log-midpoint distance (Eq. 4-4), dB",
)
def _chk_ecac_npd() -> Outcome:
    # Log-midpoint distance -> arithmetic mean of the bracketing node levels.
    p, d = [1000.0, 2000.0], [200.0, 400.0, 800.0, 1600.0]
    lv = [[100.0, 94.0, 88.0, 82.0], [110.0, 104.0, 98.0, 92.0]]
    got = float(ph.aircraft.npd_level(p, d, lv, 1000.0, math.sqrt(200.0 * 400.0))[0])
    return numeric(97.0, got, 1e-9, unit="dB", places=4)


_ROTORCRAFT = "Rotorcraft noise (ECAC Doc 32 / NORAH2)"


@register(
    _ROTORCRAFT,
    "ECAC Doc 32 atmospheric attenuation (Table 4)",
    "ΔLa over a 1 km excess path at 1 kHz vs the NORAH2 guidance Table 4, dB",
)
def _chk_doc32_atmospheric() -> Outcome:
    # NORAH2 guidance Table 4: 6.3 dB/km at 1 kHz (ICAO reference conditions).
    got = -float(ph.aircraft.atmospheric_adjustment([1000.0], 1000.0 + 60.0)[0])
    return numeric(6.3, got, 0.2, unit="dB", places=3)


@register(
    _ROTORCRAFT,
    "ECAC Doc 32 spherical spreading",
    "ΔLs at ten times the 60 m hemisphere reference distance (Eq. 24), dB",
)
def _chk_doc32_spreading() -> Outcome:
    return numeric(
        -20.0,
        float(ph.aircraft.spherical_spreading_adjustment(600.0)),
        1e-9,
        unit="dB",
        places=3,
    )


@register(
    _ROTORCRAFT,
    "ECAC Doc 32 ground effect (rigid limit)",
    "ΔLg over a rigid surface at grazing incidence tends to +6 dB (Eq. 29), dB",
)
def _chk_doc32_ground() -> Outcome:
    # Over a near-rigid surface (Zs -> inf), coherent reflection at a small path
    # difference reinforces the direct ray towards the +6.02 dB pressure-doubling
    # limit. A low frequency and near-grazing geometry approaches it.
    got = float(
        ph.aircraft.ground_effect_adjustment(
            [20.0], 50.0, 1.2, 400.0, flow_resistivity="H"
        )[0]
    )
    return numeric(6.0, got, 1.0, unit="dB", places=2)


@register(
    _ROTORCRAFT,
    "ECAC Doc 32 propagation chain (NORAH2 prototype)",
    "LA of a single-hemisphere emission vs the NORAH2 prototype single-event"
    " history (R22 approach, 223.66 m slant), dB(A)",
)
def _chk_doc32_chain() -> Outcome:
    # NORAH2 prototype ARP Case 4 (R22_H1_APP_STD2_NE, mic at the origin,
    # hr = 0.2 m, sigma = 1e6 Pa·s/m2), row t = 831.26 s: the nearest-hemisphere
    # source spectrum propagated with dLs + dLa + dLg and A-weighted reproduces
    # the tabulated LA = 55.87 dB(A). Spectrum: R22_Approach_53kts_12deg at
    # (phi, theta) = (-88.70, 108.43) deg (EASA.2020.FC.06, (c) EASA).
    bands = np.array(
        [
            10.0,
            12.5,
            16.0,
            20.0,
            25.0,
            31.5,
            40.0,
            50.0,
            63.0,
            80.0,
            100.0,
            125.0,
            160.0,
            200.0,
            250.0,
            315.0,
            400.0,
            500.0,
            630.0,
            800.0,
            1000.0,
            1250.0,
            1600.0,
            2000.0,
            2500.0,
            3150.0,
            4000.0,
            5000.0,
            6300.0,
            8000.0,
            10000.0,
        ]
    )
    spec = np.array(
        [
            35.8,
            52.2,
            70.0,
            63.6,
            48.4,
            59.2,
            53.1,
            63.3,
            61.2,
            74.6,
            68.7,
            61.8,
            65.7,
            59.7,
            59.7,
            63.6,
            57.9,
            57.7,
            58.6,
            61.0,
            61.9,
            64.7,
            65.7,
            65.6,
            64.1,
            61.6,
            57.9,
            55.8,
            56.4,
            53.4,
            52.9,
        ]
    )
    f1, f2, f3, f4 = 20.598997, 107.65265, 737.86223, 12194.217

    def _ra(x: np.ndarray) -> np.ndarray:
        return (f4**2 * x**4) / (
            (x**2 + f1**2) * np.sqrt((x**2 + f2**2) * (x**2 + f3**2)) * (x**2 + f4**2)
        )

    level = (
        spec
        + float(ph.aircraft.spherical_spreading_adjustment(223.66))
        + ph.aircraft.atmospheric_adjustment(bands, 223.66)
        + ph.aircraft.ground_effect_adjustment(
            bands, 5.0, 0.2, 223.607, flow_resistivity=1.0e6
        )
        + 20.0 * np.log10(_ra(bands) / _ra(np.array(1000.0)))
    )
    got = float(10.0 * np.log10(np.sum(10.0 ** (level / 10.0))))
    return numeric(55.87, got, 0.1, unit="dB(A)", places=3)


def _uniform_hemisphere(
    level: float, bands: list[float] | None = None
) -> RotorcraftHemisphere:
    """A synthetic hemisphere with one uniform level on the standard 10° grid."""
    freqs = np.asarray(bands if bands is not None else [50.0], dtype=np.float64)
    az = np.arange(-90.0, 91.0, 10.0)
    po = np.arange(0.0, 181.0, 10.0)
    return ph.aircraft.RotorcraftHemisphere(
        freqs, az, po, np.full((az.size, po.size, freqs.size), level)
    )


@register(
    _ROTORCRAFT,
    "NORAH2 guidance §A.3.5 ring derivation (constant φ)",
    "Hemisphere rim bin (φ, θ) = (+90°, 150°) vs the ring level at +150°, dB",
)
def _chk_doc32_hover_ring() -> Outcome:
    # Table 3, Approaches 2/3: the in-ground-hover ring extends to the
    # hemisphere assuming constant directivity in phi, so the starboard rim
    # bin at theta = 150 reads the ring at +150 deg. Ring level = 60 +
    # bearing/10 dB -> 75 dB by hand.
    brg = np.arange(-180.0, 151.0, 30.0)
    h = ph.aircraft.hover_ring_hemisphere([500.0], brg, (60.0 + brg / 10.0)[:, None])
    got = float(ph.aircraft.hemisphere_source_level(h, 90.0, 150.0)[0])
    return numeric(75.0, got, 1e-9, unit="dB", places=3)


@register(
    _ROTORCRAFT,
    "NORAH2 guidance §A.3.5 Table 3 (Approach 3 HOGE offset)",
    "Out-of-ground-hover minus in-ground-hover level of a derived bin, dB",
)
def _chk_doc32_hover_offset() -> Outcome:
    # Table 3, Approach 3: LA_HOGE(theta) = LA_HIGE(theta) + 12 dB from the
    # in-ground-hover disk. A uniform 80 dB ring derives to 92 dB everywhere;
    # the bin under the aircraft is compared.
    hige = ph.aircraft.hover_ring_hemisphere(
        [500.0], np.arange(-180.0, 151.0, 30.0), np.full((12, 1), 80.0)
    )
    hoge = ph.aircraft.hover_derived_hemisphere(hige, "out_of_ground_hover")
    got = float(
        ph.aircraft.hemisphere_source_level(hoge, 0.0, 90.0)[0]
        - ph.aircraft.hemisphere_source_level(hige, 0.0, 90.0)[0]
    )
    return numeric(12.0, got, 1e-9, unit="dB", places=3)


@register(
    _ROTORCRAFT,
    "ECAC Doc 32 flight-condition interpolation (NORAH2 Eq. 8)",
    "Distance-scaled triangle blend of three uniform hemispheres, hand-checked, dB",
)
def _chk_doc32_flight_condition() -> Outcome:
    # Conditions (V, gamma) = (50, 0), (70, 0), (60, 10); query (60, 2.5).
    # Normalised (Eq. 3-6, Ffc = 2, spans 20 kt / 10 deg): points (2.5, 0),
    # (3.5, 0), (3.0, 2), query (3.0, 0.5) -> deltas sqrt(0.5), sqrt(0.5), 1.5
    # (Eq. 7) -> weights 0.404629, 0.404629, 0.190743 (Eq. 8). Uniform levels
    # 100 / 90 / 95 dB blend to 10*lg(sum w*10^(L/10)) = 97.0367 dB by hand.
    hems = [
        _uniform_hemisphere(100.0),
        _uniform_hemisphere(90.0),
        _uniform_hemisphere(95.0),
    ]
    got = float(
        ph.aircraft.interpolated_source_level(
            hems, [50.0, 70.0, 60.0], [0.0, 0.0, 10.0], 60.0, 2.5, 0.0, 90.0
        )[0]
    )
    return numeric(97.0367, got, 1e-3, unit="dB", places=4)


@register(
    _ROTORCRAFT,
    "ECAC Doc 32 flight-path kinematics (Eq. 17)",
    "Airspeed of a straight climbing track, 40 m/s ground speed at a 5° path angle, m/s",
)
def _chk_doc32_kinematics() -> Outcome:
    # Constant-velocity track: Vg = 40 m/s at heading 30 deg, path angle 5 deg
    # -> VA = 40/cos(5 deg) = 40.152786 m/s (Eq. 16/17), by hand.
    t = np.arange(0.0, 10.5, 0.5)
    vg, gamma = 40.0, np.radians(5.0)
    heading = np.radians(30.0)
    pos = np.column_stack(
        [
            vg * np.sin(heading) * t,
            vg * np.cos(heading) * t,
            100.0 + vg * np.tan(gamma) * t,
        ]
    )
    kin = ph.aircraft.flight_path_kinematics(t, pos)
    return numeric(40.152786, float(kin.airspeed[10]), 1e-4, unit="m/s", places=5)


@register(
    _ROTORCRAFT,
    "ECAC Doc 32 retarded time (Eq. 22)",
    "Recorded-time delay at 100 m slant distance, r/c with c = 346.1 m/s, s",
)
def _chk_doc32_retarded_time() -> Outcome:
    # Level flyover directly over the receiver: at the closest-approach step the
    # slant distance is 101.2 - (0 + 1.2) = 100.0 m and t_r - t_e = 100/346.1
    # = 0.288934 s, by hand.
    t = np.arange(0.0, 20.5, 0.5)
    pos = np.column_stack([np.zeros_like(t), 50.0 * (t - 10.0), np.full_like(t, 101.2)])
    res = ph.aircraft.rotorcraft_event_level(
        [_uniform_hemisphere(100.0)],
        [50.0],
        [0.0],
        t,
        pos,
        (0.0, 0.0),
        ground=ph.aircraft.RotorcraftGround(receiver_height=1.2, flow_resistivity="H"),
    )
    k = int(np.argmin(res.distances))
    return numeric(
        0.288934, float(res.times[k] - res.emission_times[k]), 1e-5, unit="s", places=6
    )


@register(
    _ROTORCRAFT,
    "ECAC Doc 32 single event (Eq. 27)",
    "SEL − LASmax of a constant-speed level flyover, 10·lg(π·d/V) closed form, dB",
)
def _chk_doc32_event_sel() -> Outcome:
    # Single 31.5 Hz band over class-H ground with a 0.1 m receiver: dLg stays
    # within 0.03 dB of the +6 dB pressure doubling along the whole path, so the
    # exposure integral is the Lorentzian closed form SEL - LASmax =
    # 10·lg(pi*d/V) = 7.982 dB for d = 100 m and V = 50 m/s (truncation and
    # absorption stay below 0.1 dB with the track spanning +-6 km).
    t = np.arange(0.0, 240.1, 0.5)
    pos = np.column_stack(
        [np.zeros_like(t), 50.0 * (t - 120.0), np.full_like(t, 100.1)]
    )
    res = ph.aircraft.rotorcraft_event_level(
        [_uniform_hemisphere(100.0, [31.5])],
        [50.0],
        [0.0],
        t,
        pos,
        (0.0, 0.0),
        ground=ph.aircraft.RotorcraftGround(receiver_height=0.1, flow_resistivity="H"),
    )
    return numeric(7.982, res.sel - res.la_max, 0.1, unit="dB", places=3)


@register(
    _ROTORCRAFT,
    "NORAH2 guidance mean ground plane (Eq. 36-40)",
    "Intercept of the plane fitted to a symmetric 20 m roofline, hand-checked, m",
)
def _chk_doc32_mean_plane() -> Outcome:
    # Roof (0,0)-(100,20)-(200,0): by symmetry the continuous least-squares
    # line is horizontal at the mean height, area/span = 2000/200 = 10 m.
    res = ph.aircraft.mean_ground_plane([0.0, 100.0, 200.0], [0.0, 20.0, 0.0])
    return numeric(10.0, res.intercept, 1e-6, unit="m", places=4)


@register(
    _ROTORCRAFT,
    "NORAH2 guidance mean flow resistivity (Eq. 41)",
    "Log-average of equal 1e4 and 1e6 Pa·s/m2 halves, hand-checked, Pa·s/m2",
)
def _chk_doc32_mean_sigma() -> Outcome:
    # Equal lengths: sigma_bar = 10^((log 1e4 + log 1e6)/2) = 1e5 by hand.
    got = ph.aircraft.mean_flow_resistivity([120.0, 120.0], [1.0e4, 1.0e6])
    return numeric(1.0e5, got, 1e-3, unit="Pa·s/m²", places=1)


@register(
    _ROTORCRAFT,
    "NORAH2 guidance diffraction at grazing (Eq. 42)",
    "Pure diffraction with the edge on the line of sight, 10·lg 3, dB",
)
def _chk_doc32_diffraction_grazing() -> Outcome:
    got = float(ph.aircraft.diffraction_attenuation([1000.0], 0.0, edge_height=10.0)[0])
    return numeric(4.7712, got, 1e-4, unit="dB", places=4)


@register(
    _ROTORCRAFT,
    "NORAH2 guidance screening path difference (§A.4.5)",
    "Rubber-band delta over a 40 m hill, hand-checked geometry, m",
)
def _chk_doc32_screening_delta() -> Outcome:
    # Source (0, 20), receiver (400, 1.2), single edge at (200, 40):
    # delta = SO + OR - SR = sqrt(200^2+20^2) + sqrt(200^2+38.8^2)
    #         - sqrt(400^2+18.8^2) = 4.28480 m by hand.
    res = ph.aircraft.terrain_screening_adjustment(
        [500.0],
        (0.0, 20.0),
        (400.0, 1.2),
        [0.0, 190.0, 200.0, 210.0, 400.0],
        [0.0, 0.0, 40.0, 0.0, 0.0],
    )
    expected = np.hypot(200.0, 20.0) + np.hypot(200.0, 38.8) - np.hypot(400.0, 18.8)
    return numeric(float(expected), res.path_difference, 1e-9, unit="m", places=5)


def _arp5534_saturation_ratio(temperature_k: float) -> float:
    """ARP 5534 Eqs. 5-6 as page 8 of the 2021 reaffirmation prints them."""
    t01 = 273.16
    v = (
        10.79586 * (1.0 - t01 / temperature_k)
        - 5.02808 * math.log10(temperature_k / t01)
        + 1.50474e-4 * (1.0 - 10.0 ** (-8.29692 * (temperature_k / t01 - 1.0)))
        + 0.42873e-3 * (-1.0 + 10.0 ** (4.76955 * (1.0 - t01 / temperature_k)))
        - 2.2195983
    )
    return float(10.0**v)


@register(
    _AIRCRAFT,
    "SAE ARP 5534 pure-tone coefficient (Eqs. 1-6)",
    "Mid-band α at 1 kHz, 25 °C, 70 % RH, 101.325 kPa, dB/m",
)
def _chk_arp5534_coefficient() -> Outcome:
    # ARP 5534 §3.1 repeats the ISO 9613-1 coefficient in Eqs. 1-3 and writes
    # the saturation vapour pressure in its own form, Eqs. 5-6. ISO 9613-1
    # evaluated at the humidity that gives the molar concentration of Eq. 4
    # with that pressure is therefore the ARP 5534 coefficient.
    t_k = 298.15
    iso_annex_b = 10.0 ** (-6.8346 * (273.16 / t_k) ** 1.261 + 4.6151)
    same_h = 70.0 * _arp5534_saturation_ratio(t_k) / iso_annex_b
    expected = float(
        ph.environment.air_attenuation(
            1000.0,
            temperature_c=25.0,
            relative_humidity_percent=same_h,
            atmospheric_pressure_kpa=101.325,
            exact_midband=True,
        )
    )
    res = ph.aircraft.sae_band_attenuation(
        [1000.0], 1000.0, temperature_c=25.0, relative_humidity_percent=70.0
    )
    return numeric(expected, float(res.coefficient[0]), 1e-9, unit="dB/m", places=6)


# ICAO Doc 9501 ETM Vol. I (2018) Table 3-7 turbofan spectrum (bands 1-2 blank).
_ETM_SPL_37 = [
    -999.0,
    -999.0,
    70.0,
    62.0,
    70.0,
    80.0,
    82.0,
    83.0,
    76.0,
    80.0,
    80.0,
    79.0,
    78.0,
    80.0,
    78.0,
    76.0,
    79.0,
    85.0,
    79.0,
    78.0,
    71.0,
    60.0,
    54.0,
    45.0,
]
# ICAO Doc 9501 ETM Vol. I (2018) Table 4-4 integrated-method EPNL example.
_ETM_PNLTR_44 = [
    84.62,
    85.84,
    85.37,
    88.57,
    88.82,
    88.03,
    88.76,
    87.06,
    86.92,
    90.39,
    89.89,
    91.00,
    90.08,
    89.71,
    89.61,
    90.21,
    91.14,
    92.10,
    93.68,
    94.89,
    95.87,
    97.06,
    97.40,
    96.23,
    94.73,
    92.30,
    88.75,
    86.96,
    85.41,
    83.88,
    83.01,
]
_ETM_DTR_44 = [
    0.3950,
    0.3950,
    0.3951,
    0.3951,
    0.3952,
    0.3953,
    0.3954,
    0.3956,
    0.3957,
    0.3960,
    0.3963,
    0.3967,
    0.3973,
    0.3981,
    0.3992,
    0.4009,
    0.4033,
    0.4066,
    0.4108,
    0.4153,
    0.4196,
    0.4231,
    0.4256,
    0.4273,
    0.4285,
    0.4294,
    0.4299,
    0.4304,
    0.4307,
    0.4309,
    0.4311,
]


@register(
    _AIRCRAFT,
    "ICAO Annex 16 Vol. I App. 2 Table A2-3",
    "Perceived noisiness at SPL(b), 1 kHz band, in noys",
)
def _chk_ac_noy() -> Outcome:
    spl = np.full(24, -999.0)
    spl[13] = 40.0  # 1000 Hz, SPL(b) -> n = 1
    return numeric(1.0, float(ph.aircraft.perceived_noisiness(spl)[13]), 1e-6, places=4)


@register(
    _AIRCRAFT,
    "ICAO Doc 9501 ETM Vol. I Table 3-7",
    "Tone correction of the turbofan example, dB",
)
def _chk_ac_tone() -> Outcome:
    return numeric(2.0, ph.aircraft.tone_correction(_ETM_SPL_37), 1e-6, places=4)


@register(
    _AIRCRAFT,
    "ICAO Doc 9501 ETM Vol. I Table 4-4",
    "Integrated-method reference EPNL, EPNdB",
)
def _chk_ac_epnl() -> Outcome:
    epnl, _, _, _ = ph.aircraft.epnl_from_pnlt(
        np.array(_ETM_PNLTR_44), np.array(_ETM_DTR_44)
    )
    return numeric(92.61892, epnl, 1e-2, unit="EPNdB", places=3)


@register(
    _AIRCRAFT,
    "IEC 61265:1995 Table 1",
    "Directional-response tolerance at 4 kHz / 90°, dB",
)
def _chk_ac_iec61265() -> Outcome:
    from phonometry.aircraft.measurement_system import (
        _iec61265_directional_limit,
    )

    return numeric(
        2.0, _iec61265_directional_limit(4000.0, 90.0), 1e-9, unit="dB", places=1
    )


def _doc29_reference_jet() -> ph.aircraft.PerformanceAircraft:
    """The JETW reference turbofan of ECAC Doc 29 5th ed. Vol 3 Part 2.

    A hypothetical two-engine aeroplane invented for that volume's worked
    examples, with the coefficients its sheets C-1 to C-4 publish. Built here
    rather than read from a file because the volume is not redistributable, and
    carried whole -- the three C-2 thrust ratings and all eight C-4 flap
    configurations -- because a partial set does not fail: a procedure whose
    flap is missing would have to be flown in some other configuration, and the
    profile would no longer be the one the reference case names.
    """
    return ph.aircraft.PerformanceAircraft(
        aircraft_id="JETW",
        engines=2,
        max_static_thrust_lb=25000.0,
        max_landing_weight_lb=159222.0,
        jet_coefficients={
            "MaxTakeoff": ph.aircraft.JetEngineCoefficients(
                25000.0, -25.0, 0.3, 1e-5, 0.0
            ),
            "MaxClimb": ph.aircraft.JetEngineCoefficients(
                16000.0, -4.0, 0.4, -1e-5, 0.0
            ),
            "IdleApproach": ph.aircraft.JetEngineCoefficients(
                1100.0, -6.5, 0.17, -1e-5, 0.0
            ),
        },
        # Sheet C-4, in its own order: drag ratio R, then the ground-roll
        # coefficient B of Eq. B-16 and the speed coefficient C/D of Eq. B-15
        # or Eq. B-75 where the sheet prints one rather than a dash.
        aerodynamic_coefficients={
            ("A", "5"): ph.aircraft.AerodynamicCoefficients(0.07),
            ("A", "15"): ph.aircraft.AerodynamicCoefficients(0.075),
            ("A", "25"): ph.aircraft.AerodynamicCoefficients(0.1, None, 0.375),
            ("A", "30"): ph.aircraft.AerodynamicCoefficients(0.12, None, 0.35),
            ("A", "ZERO"): ph.aircraft.AerodynamicCoefficients(0.055),
            ("D", "1"): ph.aircraft.AerodynamicCoefficients(0.06),
            ("D", "5"): ph.aircraft.AerodynamicCoefficients(0.07, 0.0075, 0.4),
            ("D", "ZERO"): ph.aircraft.AerodynamicCoefficients(0.055),
        },
    )


@register(
    _AIRCRAFT,
    "ECAC Doc 29 Appendix B take-off ground roll",
    "Equivalent take-off distance of reference case 6 (Eq. B-15/B-16), ft",
)
def _chk_doc29_takeoff_roll() -> Outcome:
    # Doc 29 5th ed. Vol 3 Part 2 workbook, sheet D2-(Departure_Results), case 6
    # (JETW, ICAO_A, sea level, 15 degC, 8 kt headwind): point 2 sits at
    # 4897.5 ft, the equivalent take-off distance of Eq. B-16 at the rotation
    # speed of Eq. B-15.
    profile = ph.aircraft.departure_profile(
        _doc29_reference_jet(),
        [ph.aircraft.DepartureStep("Takeoff", "MaxTakeoff", "5")],
        weight_lb=165347.0,
        aerodrome=ph.aircraft.Aerodrome(
            elevation_ft=0.0, temperature_c=15.0, headwind_kt=8.0
        ),
    )
    return numeric(4897.5, profile.points[1].distance_ft, 0.05, unit="ft", places=1)


@register(
    _AIRCRAFT,
    "ECAC Doc 29 Appendix B approach thrust",
    "Corrected net thrust at the top of reference case 2A (Eq. B-40/B-48), lb",
)
def _chk_doc29_approach_thrust() -> Outcome:
    # Same workbook, sheet D1-(Arrival_Results), case 2A (JETW, Descend
    # procedure, sea level, 15 degC, no wind): point 1 is 533.1 lb per engine,
    # the descent thrust of Eq. B-40 after the non-standard-headwind correction
    # of Eq. B-48. The whole approach is solved backwards from the Land step,
    # so this number also checks that anchor.
    #
    # The eight steps are sheet C-6.2's Descend rows for JETW, each parameter
    # taken to the one decimal that sheet prints it to.
    steps = [
        ph.aircraft.ApproachStep(
            "Descend",
            "ZERO",
            start_altitude_ft=6000.0,
            start_calibrated_airspeed_kt=250.0,
            descent_angle_deg=2.8,
        ),
        ph.aircraft.ApproachStep(
            "Descend",
            "5",
            start_altitude_ft=3000.0,
            start_calibrated_airspeed_kt=180.0,
            descent_angle_deg=3.0,
        ),
        ph.aircraft.ApproachStep(
            "Descend",
            "25",
            start_altitude_ft=1500.0,
            start_calibrated_airspeed_kt=150.0,
            descent_angle_deg=3.0,
        ),
        ph.aircraft.ApproachStep(
            "Descend",
            "30",
            start_altitude_ft=1000.0,
            start_calibrated_airspeed_kt=135.0,
            descent_angle_deg=3.0,
        ),
        ph.aircraft.ApproachStep(
            "Descend",
            "30",
            start_altitude_ft=49.9,
            start_calibrated_airspeed_kt=135.0,
            descent_angle_deg=3.0,
        ),
        ph.aircraft.ApproachStep("Land", "30", touchdown_roll_ft=304.1),
        ph.aircraft.ApproachStep(
            "Decelerate",
            "-NONE-",
            start_calibrated_airspeed_kt=129.6,
            distance_ft=3937.0,
            start_thrust_percent=40.0,
        ),
        ph.aircraft.ApproachStep(
            "Decelerate",
            "-NONE-",
            start_calibrated_airspeed_kt=27.0,
            distance_ft=0.0,
            start_thrust_percent=10.0,
        ),
    ]
    profile = ph.aircraft.approach_profile(
        _doc29_reference_jet(),
        steps,
        aerodrome=ph.aircraft.Aerodrome(
            elevation_ft=0.0, temperature_c=15.0, headwind_kt=0.0
        ),
    )
    return numeric(
        533.1, profile.points[0].corrected_net_thrust_lb, 0.05, unit="lb", places=1
    )


# ECAC Doc 29 5th ed. Vol. 2 Appendix D: the worked example recalculates the SEL
# NPD data of the JETW reference aeroplane for 10 degC, 80 % and 101.325 kPa
# with the spectral classes 103 and 205 of the shipped ANP database, by SAE ARP
# 5534 and by SAE ARP 866A, and prints every intermediate table. The tables are
# transcribed in tests/aircraft/doc29_appendix_d_data.py (PDF pages 128 to 133,
# folios D-4 to D-9) and each row below holds one of them, cell by cell, at the
# precision it is printed to: half a unit of the last digit either way.

#: The atmosphere of the worked example.
_APPENDIX_D_AIR = {"temperature_c": 10.0, "relative_humidity_percent": 80.0}
#: Half a unit of the last printed digit of the attenuation and level tables,
#: with a hair for binary rounding.
_HALF_MILLI_DB = 0.0005 + 1e-9
_HALF_DECI_DB = 0.05 + 1e-9


def _appendix_d_tables() -> ModuleType:
    """The transcription module of the printed Appendix D tables."""
    return aircraft_test_data("doc29_appendix_d_data")


def _appendix_d_increment(
    class_id: int, absorption: str
) -> ph.aircraft.NpdAtmosphereIncrement:
    database = ph.aircraft.load_anp_database()
    return ph.aircraft.npd_atmosphere_increment(
        database.spectral_class(class_id), absorption=absorption, **_APPENDIX_D_AIR
    )


def _cells_within(got: object, printed: object, tolerance: object) -> int:
    """How many cells of a table sit within their tolerance of the print."""
    deviation = np.abs(np.asarray(got) - np.asarray(printed))
    return int(np.count_nonzero(deviation <= np.asarray(tolerance)))


@register(
    _AIRCRAFT,
    "ECAC Doc 29 Appendix D Table D-2",
    "Spectral classes 103 and 205 corrected back to the source (Eq. D-1), cells",
)
def _chk_doc29_table_d2() -> Outcome:
    printed = np.asarray(_appendix_d_tables().TABLE_D2)
    got = np.column_stack(
        [
            _appendix_d_increment(103, "arp5534").source_spectrum_db,
            _appendix_d_increment(205, "arp5534").source_spectrum_db,
        ]
    )
    matching = _cells_within(got, printed[:, 2:], _HALF_DECI_DB)
    return count(matching, got.size, subject="cells of Table D-2 at source")


@register(
    _AIRCRAFT,
    "ECAC Doc 29 Appendix D Table D-3a",
    "SAE AIR-1845 attenuation of Table D-1 over the ten NPD distances, cells",
)
def _chk_doc29_table_d3a() -> Outcome:
    printed = np.asarray(_appendix_d_tables().TABLE_D3A)
    got = _appendix_d_increment(103, "arp5534").reference_attenuation_db
    matching = _cells_within(got, printed, _HALF_MILLI_DB)
    return count(matching, printed.size, subject="cells of Table D-3a")


@register(
    _AIRCRAFT,
    "ECAC Doc 29 Appendix D Table D-3b",
    "SAE ARP 866A attenuation at 10 °C, 80 % over the NPD distances, cells",
)
def _chk_doc29_table_d3b() -> Outcome:
    # ISO 3891:1978 Annex A.2 with eta interpolated linearly in its Table 1.
    # 208 cells agree to the last printed digit; the other 32 are the longest
    # paths at the highest frequencies, which the page prints about 6 ppm
    # below the formula (0.0045 dB of 745 dB at most). A common factor between
    # 0.9999934 and 0.9999942 on the formula reproduces all 240, which points
    # at a units constant of the program that printed the table rather than at
    # the absorption model; SAE ARP 866A itself is not available to settle it,
    # so the tolerance is widened by 7 ppm of the printed value and says so.
    printed = np.asarray(_appendix_d_tables().TABLE_D3B)
    got = _appendix_d_increment(103, "arp866a").specified_attenuation_db
    matching = _cells_within(got, printed, _HALF_MILLI_DB + 7e-6 * printed)
    return count(
        matching,
        printed.size,
        subject="cells of Table D-3b",
        expected_label=(
            f"{printed.size}/{printed.size} cells of Table D-3b within half a "
            "unit of the last digit plus 7 ppm"
        ),
    )


@register(
    _AIRCRAFT,
    "ECAC Doc 29 Appendix D Table D-3c",
    "SAE ARP 5534 attenuation at 10 °C, 80 %, 101.325 kPa over the NPD distances, cells",
)
def _chk_doc29_table_d3c() -> Outcome:
    # Every cell to the last digit, which takes the saturation vapour pressure
    # of ARP 5534 Eqs. 5-6: the ISO 9613-1 Annex B form leaves 57 cells up to
    # 0.036 dB off.
    printed = np.asarray(_appendix_d_tables().TABLE_D3C)
    got = _appendix_d_increment(103, "arp5534").specified_attenuation_db
    matching = _cells_within(got, printed, _HALF_MILLI_DB)
    return count(matching, printed.size, subject="cells of Table D-3c")


def _appendix_d_levels(absorption: str) -> np.ndarray:
    """``LA,ref``, ``LA,atm`` and the increment for 103 then 205, as printed."""
    columns = []
    for class_id in (103, 205):
        inc = _appendix_d_increment(class_id, absorption)
        columns += [
            inc.reference_levels_dba,
            inc.specified_levels_dba,
            inc.increment_db,
        ]
    return np.column_stack(columns)


@register(
    _AIRCRAFT,
    "ECAC Doc 29 Appendix D Table D-4",
    "A-weighted levels and increment ΔL with SAE ARP 5534 (Eq. D-4), cells",
)
def _chk_doc29_table_d4() -> Outcome:
    printed = np.asarray(_appendix_d_tables().TABLE_D4)
    matching = _cells_within(_appendix_d_levels("arp5534"), printed, _HALF_DECI_DB)
    return count(matching, printed.size, subject="cells of Table D-4")


@register(
    _AIRCRAFT,
    "ECAC Doc 29 Appendix D Table D-5",
    "A-weighted levels and increment ΔL with SAE ARP 866A (Eq. D-4), cells",
)
def _chk_doc29_table_d5() -> Outcome:
    printed = np.asarray(_appendix_d_tables().TABLE_D5)
    matching = _cells_within(_appendix_d_levels("arp866a"), printed, _HALF_DECI_DB)
    return count(matching, printed.size, subject="cells of Table D-5")


def _appendix_d_revised(absorption: str) -> tuple[np.ndarray, np.ndarray]:
    """The JETW NPD data of Table D-6a revised by one route, and Table D-6a's rows."""
    tables = _appendix_d_tables()
    database = ph.aircraft.load_anp_database()
    distances = np.asarray(tables.DISTANCES_FT) * 0.3048
    revised = []
    for operation, class_id in (("A", 205), ("D", 103)):
        rows = [r for r in tables.TABLE_D6A if r[0] == operation]
        curves = ph.aircraft.AnpNpdCurves(
            aircraft_id="JETW",
            npd_id="JETW",
            metric="SEL",
            operation=operation,
            power_parameter="CNT (lb)",
            powers=np.array([r[1] for r in rows]),
            distances=distances,
            levels=np.array([r[2] for r in rows]),
        )
        revised.append(
            ph.aircraft.revise_npd_curves(
                curves,
                database.spectral_class(class_id),
                absorption=absorption,
                **_APPENDIX_D_AIR,
            ).revised.levels
        )
    return np.vstack(revised), np.asarray([r[2] for r in tables.TABLE_D6A])


@register(
    _AIRCRAFT,
    "ECAC Doc 29 Appendix D Table D-6b",
    "JETW SEL NPD data revised end to end with SAE ARP 5534, cells",
)
def _chk_doc29_table_d6b() -> Outcome:
    got, _ = _appendix_d_revised("arp5534")
    printed = np.asarray([r[2] for r in _appendix_d_tables().TABLE_D6B])
    matching = _cells_within(got, printed, _HALF_DECI_DB)
    return count(matching, printed.size, subject="cells of Table D-6b")


@register(
    _AIRCRAFT,
    "ECAC Doc 29 Appendix D Table D-6c",
    "JETW SEL NPD data revised end to end with SAE ARP 866A, cells",
)
def _chk_doc29_table_d6c() -> Outcome:
    # The last row (departure, 22 500 lb) is printed as a copy of the last row
    # of Table D-6b, and eight of its ten cells are not what Table D-6a plus
    # the Table D-5 increments give; it is in docs/ERRATA.md and left out here.
    got, _ = _appendix_d_revised("arp866a")
    printed = np.asarray([r[2] for r in _appendix_d_tables().TABLE_D6C])
    matching = _cells_within(got[:-1], printed[:-1], _HALF_DECI_DB)
    total = printed[:-1].size
    return count(
        matching,
        total,
        subject="cells of Table D-6c",
        expected_label=(
            f"{total}/{total} cells of Table D-6c outside its misprinted last row"
        ),
    )


@register(
    _AIRCRAFT,
    "ISO 3891:1978 Annex C",
    "Tone correction worked example: background and excess F in 22 bands, fields",
)
def _chk_iso3891_annex_c() -> Outcome:
    # The same spectrum as ICAO ETM Table 3-7, whose row checks the correction
    # C = 2 alone. This one checks every step the example prints: the smoothed
    # background and the excess in each of the 22 bands. ISO 3891 step 9 has
    # no 1.5 dB threshold where ICAO Annex 16 has one; the largest correction,
    # F = 6 dB at 2 500 Hz, is F/3 = 2 under both.
    # The printed columns (PDF page 26, printed p. 23) are read from the test
    # suite's transcription, in thirds of a decibel as the page prints them.
    from phonometry.aircraft.certification import _tone_background

    example = aircraft_test_data("iso3891_annex_c_data")
    background, excess = _tone_background([0.0, 0.0, *example.LEVELS_DB])
    fields = [
        *zip(background[2:], example.BACKGROUND_THIRDS, strict=True),
        *zip(np.maximum(excess[2:], 0.0), example.EXCESS_THIRDS, strict=True),
    ]
    matching = sum(1 for got, thirds in fields if abs(got - thirds / 3.0) <= 1e-9)
    return count(matching, len(fields), subject="printed background and excess values")


@register(
    _AIRCRAFT,
    "ISO 3891:1978 Annex A Table 10",
    "SAE ARP 866A coefficient at 80 % from -10 °C to 40 °C, 50 Hz to 10 kHz, cells",
)
def _chk_iso3891_table_10() -> Outcome:
    # The formula of A.2 with eta read from Table 1 by the three-point
    # quadratic of arp866a_attenuation, against the table ISO 3891 prints from
    # it (PDF page 19, printed p. 16), to its one decimal. Linear interpolation
    # misses 11 of the 264 cells. The 12 500 Hz row the table also prints has
    # no evaluation frequency in Table 2 and is not a band of the function.
    tables = aircraft_test_data("iso3891_tables_data")
    printed = np.asarray(tables.TABLE_10)
    got = np.column_stack(
        [
            ph.aircraft.arp866a_attenuation(
                tables.FREQUENCIES_HZ,
                temperature_c=t,
                relative_humidity_percent=80.0,
            ).coefficient_db_per_100m
            for t in tables.TEMPERATURES_C
        ]
    )
    matching = _cells_within(got, printed, _HALF_DECI_DB)
    return count(matching, printed.size, subject="cells of Table 10")
