#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Railway rolling stock noise and its reference track: ISO 3095, EN 15610, EN 15461.

ISO 3095:2013 prints no worked pass-by, but it sets numbers beside its figures:
the roughness limit of Figure 2 as a label on every point, the decay-rate
limits of Figure 3 as a table beside the curves, and the microphone positions
of four units dimensioned in Figure 10. EN 15610:2009 prints the same roughness
limit a second time, as the table its Annex B listing types in, and prints the
lengths of Method B (2 m discarded at either end, 5 m, 15 m) in 7.4.3 and the
bands it filters in the listing; the filters of Method B are held to the
class 0 limits EN 61260:1995 prints in its Table 1. Annex G works
one uncertainty budget, Table G.2, to 55,68 dB, 0,83 dB and 1,66 dB, and
Figure G.1 draws its shares in an order the budget has to reproduce.

Everything else is anchored in closed forms: the transit exposure level of
ISO 3095:2005 against its own Formulae 9 and 10, a steady tone and a sinusoidal
roughness that read their own levels, the decay rate of an exponential
response, and the Annex C chain at the speed where a band of wavelength falls
exactly on a band of frequency.
"""

from __future__ import annotations

import math

import numpy as np
from reference_data import rolling_stock_noise as ref

import phonometry as ph

from ..registry import Outcome, count, numeric, record, register

_ROLLING_STOCK = "Railway rolling stock noise and its reference track (ISO 3095)"

#: At 10 m/s a base-ten band of wavenumber k lands exactly on band k + 10 of
#: frequency.
_ALIGNED_SPEED_KMH = 36.0

_NOISE_BANDS_HZ = (
    31.5, 40.0, 50.0, 63.0, 80.0, 100.0, 125.0, 160.0, 200.0, 250.0, 315.0,
    400.0, 500.0, 630.0, 800.0, 1000.0, 1250.0, 1600.0, 2000.0, 2500.0,
    3150.0, 4000.0, 5000.0, 6300.0, 8000.0,
)  # fmt: skip


def _table_g2() -> ph.environment.PassByUncertainty:
    """The budget of Table G.2 from its printed rows."""
    return ph.environment.pass_by_uncertainty(
        ref.TABLE_G2_READING_DB,
        [ph.metrology.Quantity(v, u, name=n) for n, v, u in ref.TABLE_G2_ROWS],
    )


@register(
    _ROLLING_STOCK,
    "ISO 3095:2013 Figure 2",
    "Default upper limit of the one-third octave band rail roughness, the 22 "
    "levels printed beside the points, 40 cm to 0,315 cm, dB re 1 µm",
)
def _chk_roughness_limit() -> Outcome:
    published = ph.environment.REFERENCE_TRACK_ROUGHNESS_LIMIT_DB
    cells = list(zip(ref.FIGURE_2_WAVELENGTHS_CM, ref.FIGURE_2_LIMIT_DB, strict=True))
    matching = sum(
        1
        for wavelength_cm, level in cells
        if math.isclose(published.get(wavelength_cm / 100.0, math.nan), level)
    )
    return count(matching, len(cells), subject="printed levels")


@register(
    _ROLLING_STOCK,
    "EN 15610:2009 Annex B.9.2",
    "The roughness limit as the listing types it, 22 wavelengths and levels, "
    "against the published Figure 2 limit, dB re 1 µm",
)
def _chk_roughness_limit_listing() -> Outcome:
    published = ph.environment.REFERENCE_TRACK_ROUGHNESS_LIMIT_DB
    bands = {round(-10.0 * math.log10(w)): v for w, v in published.items()}
    cells = list(
        zip(
            ref.EN15610_LISTING_WAVELENGTHS_M, ref.EN15610_LISTING_LIMIT_DB, strict=True
        )
    )
    matching = sum(
        1
        for wavelength, level in cells
        if math.isclose(
            bands.get(round(-10.0 * math.log10(wavelength)), math.nan), level
        )
    )
    return count(matching, len(cells), subject="listed levels")


@register(
    _ROLLING_STOCK,
    "ISO 3095:2013 Figure 3",
    "Default lower limits of the vertical and lateral track decay rates, the "
    "table beside the curves, 250 Hz to 5 kHz, dB/m",
)
def _chk_decay_limits() -> Outcome:
    published = ph.environment.REFERENCE_TRACK_DECAY_LIMITS_DB_PER_M
    cells = [
        (float(published[direction].get(f, math.nan)), float(v))
        for direction, printed in (
            ("vertical", ref.FIGURE_3_VERTICAL_DB_PER_M),
            ("lateral", ref.FIGURE_3_LATERAL_DB_PER_M),
        )
        for f, v in zip(ref.FIGURE_3_FREQUENCIES_HZ, printed, strict=True)
    ]
    matching = sum(1 for got, want in cells if math.isclose(got, want))
    return count(matching, len(cells), subject="printed cells")


@register(
    _ROLLING_STOCK,
    "ISO 3095:2013 7.5.1.1, Figure 10",
    "Microphone positions of the maximum level starting test for the 42, 54, "
    "87 and 108 m units drawn, m behind the front of the unit",
)
def _chk_starting_positions() -> Outcome:
    expected = {
        f"{length:g} m, position {i + 1}": value
        for length, positions in ref.FIGURE_10_POSITIONS_M.items()
        for i, value in enumerate(positions)
    }
    computed: dict[str, float] = {}
    for length in ref.FIGURE_10_POSITIONS_M:
        for i, value in enumerate(ph.environment.acceleration_test_positions(length)):
            computed[f"{length:g} m, position {i + 1}"] = round(float(value), 6)
    return record(expected, computed, unit="m")


@register(
    _ROLLING_STOCK,
    "ISO 3095:2013 Table G.2",
    "Result of the standstill budget, the reading plus the mean value corrections, dB",
)
def _chk_table_g2_level() -> Outcome:
    return numeric(
        ref.TABLE_G2_LEVEL_DB, _table_g2().level_db, 0.005, unit="dB", places=3
    )


@register(
    _ROLLING_STOCK,
    "ISO 3095:2013 Table G.2",
    "Combined standard uncertainty of the standstill budget, Formula G.5, dB",
)
def _chk_table_g2_combined() -> Outcome:
    return numeric(
        ref.TABLE_G2_COMBINED_UNCERTAINTY_DB,
        _table_g2().combined_uncertainty_db,
        0.005,
        unit="dB",
        places=3,
    )


@register(
    _ROLLING_STOCK,
    "ISO 3095:2013 Table G.2",
    "Expanded uncertainty of the standstill budget, k = 2, Formula G.6, dB",
)
def _chk_table_g2_expanded() -> Outcome:
    return numeric(
        ref.TABLE_G2_EXPANDED_UNCERTAINTY_DB,
        _table_g2().expanded_uncertainty_db,
        0.005,
        unit="dB",
        places=3,
    )


@register(
    _ROLLING_STOCK,
    "ISO 3095:2013 Figure G.1",
    "Order of the bars by share of the variance: the nine distinct shares of "
    "the thirteen inputs, largest first, each with its inputs (seven inputs tie "
    "in three groups, which the figure draws in Table G.2 order)",
)
def _chk_figure_g1_order() -> Outcome:
    shares = _table_g2().variance_ratios

    def share_groups(order: tuple[str, ...]) -> list[frozenset[str]]:
        """Consecutive inputs of equal share, as the bars stand in ``order``."""
        groups: list[set[str]] = []
        for name in order:
            if groups and math.isclose(
                shares[name], shares[next(iter(groups[-1]))], rel_tol=1e-9
            ):
                groups[-1].add(name)
            else:
                groups.append({name})
        return [frozenset(group) for group in groups]

    printed = share_groups(ref.FIGURE_G1_ORDER)
    ranked = share_groups(tuple(sorted(shares, key=lambda name: -shares[name])))
    matching = sum(1 for got, want in zip(ranked, printed, strict=False) if got == want)
    return count(matching, max(len(printed), len(ranked)), subject="share groups")


@register(
    _ROLLING_STOCK,
    "ISO 3095:2013 Table G.1",
    "Standard uncertainty a/√3 (Formula G.2) of the eighteen rectangular rows "
    "whose print it gives, to the printed two decimals, dB",
)
def _chk_table_g1_rows() -> Outcome:
    matching = sum(
        1
        for name, half_width, printed in ref.TABLE_G1_RECTANGULAR_ROWS
        if math.isclose(
            round(ph.metrology.rectangular(0.0, half_width, name).uncertainty, 2),
            printed,
        )
    )
    return count(matching, len(ref.TABLE_G1_RECTANGULAR_ROWS), subject="rows")


@register(
    _ROLLING_STOCK,
    "ISO 3095:2005 3.14, Formulae 9 and 10",
    "Transit exposure level of a 12 s record at 84 dB over a 5 s pass-by: "
    "SEL + 10 lg(T0/Tp) against the library's L_Aeq,T + 10 lg(T/Tp), dB",
)
def _chk_transit_exposure_level() -> Outcome:
    level, duration, passing = 84.0, 12.0, 5.0
    sel = level + 10.0 * math.log10(duration)
    expected = sel + 10.0 * math.log10(1.0 / passing)
    computed = ph.environment.transit_exposure_level(
        level, measurement_time_s=duration, pass_by_time_s=passing
    )
    return numeric(expected, computed, 1e-12, unit="dB", places=6)


@register(
    _ROLLING_STOCK,
    "ISO 3095:2013 3.14 and 6.5",
    "L_pAeq,T of a steady 1 kHz tone of 1 Pa amplitude, where A-weighting is "
    "0 dB: 10 lg(1/2/p0²), dB",
)
def _chk_tone_level() -> Outcome:
    fs = 48000
    t = np.arange(10 * fs) / fs
    record_ = ph.environment.pass_by_measurement(
        np.sin(2.0 * np.pi * 1000.0 * t), fs, start_s=2.0, end_s=8.0
    )
    expected = 10.0 * math.log10(0.5 / 2.0e-5**2)
    return numeric(expected, record_.equivalent_level_db, 0.02, unit="dB", places=3)


@register(
    _ROLLING_STOCK,
    "EN 15610:2009 3.3 and 7.4.2",
    "Band level of a 3 µm sinusoidal roughness of 1 cm wavelength on a Fourier "
    "line, Method A: 10 lg(A²/2), dB re 1 µm",
)
def _chk_sinusoid_roughness() -> Outcome:
    x = np.arange(0.0, 15.0, 1.0e-3)
    spectrum = ph.environment.acoustic_roughness_spectrum(
        3.0 * np.cos(2.0 * np.pi * 100.0 * x),
        sample_spacing_m=1.0e-3,
        spike_removal=False,
        curvature_processing=False,
    )
    return numeric(
        10.0 * math.log10(4.5), spectrum.level_at(0.01), 1e-9, unit="dB", places=6
    )


@register(
    _ROLLING_STOCK,
    "EN 15610:2009 7.4.3 and EN 61260:1995 Table 1",
    "Bands of the Method B filter bank at 1 mm sampling within the class 0 "
    "limits of Table 1 on relative attenuation, graded up to the Nyquist "
    "wavenumber of the record, 0,5 m to 2,5 mm",
)
def _chk_method_b_filter_class() -> Outcome:
    bank = ph.environment.roughness_filter_bank(sample_spacing_m=1.0e-3)
    result = ph.filters.verify_filter_class(bank, edition="1995")
    nyquist = bank.fs / 2.0
    class_0 = sum(
        1
        for band, centre, factor in zip(
            result.bands, bank.freq, bank.factor, strict=True
        )
        if band["class"] == 0
        and int(factor) == 1
        and band["checked_to_omega"] * float(centre) >= nyquist * (1.0 - 1e-9)
    )
    return count(class_0, bank.num_bands, subject="bands")


@register(
    _ROLLING_STOCK,
    "EN 15610:2009 7.4.3 and EN 61260:1995 4.8 and Table 1",
    "Unit sinusoids run through the Method B bank on a 40 m record sampled "
    "every millimetre, at the normalized frequencies G⁴ and G⁻⁴ map to "
    "(equation 10) about every band and at the two wavenumbers a decimated "
    "bank lets through (74,773 and 88,202 per metre): band outputs at and "
    "beyond them at least the +75 dB of class 0 below the midband tone",
)
def _chk_method_b_alias_rejection() -> Outcome:
    bank = ph.environment.roughness_filter_bank(sample_spacing_m=1.0e-3)
    x = np.arange(40_000) * 1.0e-3
    # Every filter has rung out over the first 25 m; the last 15 m are steady.
    steady = slice(25_000, None)
    g = 10.0**0.3
    omega_h = 1.0 + (g ** (1.0 / 6.0) - 1.0) / (g**0.5 - 1.0) * (g**4 - 1.0)
    centres = [float(f) for f in bank.freq]

    def outputs(wavenumber: float) -> list[float]:
        tone = np.cos(2.0 * np.pi * wavenumber * x + 0.4)
        result = bank.filter(tone, sigbands=True, calculate_level=False, detrend=False)
        return [
            float(np.mean(np.asarray(y)[steady] ** 2)) for y in result.require_bands()
        ]

    midband = [outputs(f)[index] for index, f in enumerate(centres)]
    tones = sorted(
        {k for f in centres for k in (f * omega_h, f / omega_h) if k < bank.fs / 2.0}
        | {74.773, 88.202}
    )
    held = judged = 0
    for wavenumber in tones:
        for f, reference, level in zip(
            centres, midband, outputs(wavenumber), strict=True
        ):
            if 1.0 / omega_h < wavenumber / f < omega_h:
                continue
            judged += 1
            if (
                10.0 * math.log10(reference / level)
                >= ref.EN61260_1995_CLASS_0_BEYOND_G4_DB
            ):
                held += 1
    return count(held, judged, subject="band outputs")


@register(
    _ROLLING_STOCK,
    "EN 15610:2009 Annex B.9.2",
    "Bands Method B reports on a 19 m record sampled every millimetre, against "
    "wl_d, the 24 band centres the listing filters, 0,5 m to 2,5 mm",
)
def _chk_method_b_bands() -> Outcome:
    x = np.arange(0.0, 19.0, 1.0e-3)
    spectrum = ph.environment.filtered_roughness_spectrum(
        np.cos(2.0 * np.pi * 40.0 * x),
        sample_spacing_m=1.0e-3,
        spike_removal=False,
        curvature_processing=False,
    )
    listed = ref.EN15610_LISTING_FILTER_WAVELENGTHS_M
    reported = [float(w) for w in spectrum.wavelengths_m]
    matching = sum(
        1
        for printed, computed in zip(listed, reported, strict=False)
        if math.isclose(printed, computed)
    )
    return count(matching, max(len(listed), len(reported)), subject="bands")


@register(
    _ROLLING_STOCK,
    "EN 15610:2009 7.4.3 and EN 61260:1995 Table 1",
    "Band level of a 3 µm sinusoidal roughness at the 1 cm band centre, Method B: "
    "10 lg(A²/2) within the ±0,15 dB of class 0 at the midband, dB re 1 µm",
)
def _chk_method_b_sinusoid() -> Outcome:
    x = np.arange(0.0, 20.0, 1.0e-3)
    spectrum = ph.environment.filtered_roughness_spectrum(
        3.0 * np.cos(2.0 * np.pi * 100.0 * x),
        sample_spacing_m=1.0e-3,
        spike_removal=False,
        curvature_processing=False,
    )
    return numeric(
        10.0 * math.log10(4.5), spectrum.level_at(0.01), 0.15, unit="dB", places=6
    )


@register(
    _ROLLING_STOCK,
    "EN 15610:2009 7.4.3",
    "Length analysed by Method B in a 20 m record, once 2 m are discarded at "
    "either end after filtering: 20 - 2 × 2, m",
)
def _chk_method_b_length() -> Outcome:
    x = np.arange(0.0, 20.0, 1.0e-3)
    spectrum = ph.environment.filtered_roughness_spectrum(
        np.cos(2.0 * np.pi * 40.0 * x), sample_spacing_m=1.0e-3
    )
    expected = 20.0 - 2.0 * ref.EN15610_FILTER_TRANSIENT_M
    return numeric(expected, float(spectrum.record_length_m or 0.0), 1e-9, unit="m")


@register(
    _ROLLING_STOCK,
    "EN 15610:2009 7.4.3 NOTE 1",
    "The shortest record Method B analyses, 5 m: a 5 m record is analysed and "
    "one a millimetre shorter is refused",
)
def _chk_method_b_shortest_record() -> Outcome:
    shortest = ref.EN15610_SHORTEST_FILTERED_RECORD_M
    record_ = np.cos(2.0 * np.pi * 40.0 * np.arange(0.0, shortest, 1.0e-3))
    verdicts = []
    for candidate, accepted in ((record_, True), (record_[:-1], False)):
        try:
            ph.environment.filtered_roughness_spectrum(
                candidate, sample_spacing_m=1.0e-3
            )
        except ValueError:
            verdicts.append(not accepted)
        else:
            verdicts.append(accepted)
    return count(sum(verdicts), len(verdicts), subject="records")


@register(
    _ROLLING_STOCK,
    "EN 15610:2009 7.4.3",
    "A line analysed by Method B needs 15 m of record once 2 m are discarded at "
    "either end of each: a 15 m line holds, a 14,9 m one does not",
)
def _chk_method_b_total_length() -> Outcome:
    limit = ph.environment.REFERENCE_TRACK_ROUGHNESS_LIMIT_DB
    wavelengths = sorted(limit, reverse=True)
    total = ref.EN15610_FILTERED_TOTAL_M
    verdicts = []
    for length_m, holds in ((total, True), (total - 0.1, False)):
        line = ph.environment.AcousticRoughnessSpectrum(
            np.array(wavelengths),
            np.array([limit[w] - 2.0 for w in wavelengths]),
            record_length_m=length_m,
            method="B",
        )
        check = ph.environment.check_reference_track([line], [], speed_kmh=160.0)
        condition = next(c for c in check.conditions if c.clause == "EN 15610 7.4.3")
        verdicts.append(condition.holds is holds)
    return count(sum(verdicts), len(verdicts), subject="lines")


@register(
    _ROLLING_STOCK,
    "EN 15610:2009 7.3",
    "Curvature processing of an 11 mm pit 50 µm deep: the 0,375 m circle rests "
    "on its rims 6 mm from its middle, µm",
)
def _chk_curvature_pit() -> Outcome:
    record_ = np.zeros(2001)
    record_[995:1006] = -50.0
    processed = ph.environment.curvature_processed_roughness(
        record_, sample_spacing_m=1.0e-3
    )
    radius_um = 0.375e6
    expected = -(radius_um - math.sqrt(radius_um**2 - 6.0e3**2))
    return numeric(expected, float(processed[1000]), 1e-9, unit="µm", places=6)


@register(
    _ROLLING_STOCK,
    "EN 15461:2008+A1:2010 Formula 1 and Annex A",
    "Decay rate of a response A(0) exp(-βx) sampled every millimetre over "
    "150 m, against 20 lg e^β, dB/m",
)
def _chk_exponential_decay() -> Outcome:
    distances = np.arange(0.0, 150.0, 1.0e-3)
    beta = 0.23
    rate = ph.environment.track_decay_rate(
        np.exp(-beta * distances)[:, None],
        frequencies_hz=[500.0],
        distances_m=distances,
    )
    expected = 20.0 * math.log10(math.e) * beta
    return numeric(
        expected,
        float(rate.decay_rates_db_per_m[0]),
        2e-4,
        rel=True,
        unit="dB/m",
        places=4,
    )


@register(
    _ROLLING_STOCK,
    "ISO 3095:2013 Annex C",
    "Effect of a 3 dB exceedance in the 4 cm band at 36 km/h, carried whole "
    "onto 250 Hz, on a flat 25-band spectrum: 10 lg 25 - 10 lg(24 + 10^-0,3), dB",
)
def _chk_annex_c() -> Outcome:
    limit = ph.environment.REFERENCE_TRACK_ROUGHNESS_LIMIT_DB
    wavelengths = sorted(limit, reverse=True)
    levels = [limit[w] - 1.0 for w in wavelengths]
    levels[wavelengths.index(0.04)] = limit[0.04] + 3.0
    verdict = ph.environment.check_small_roughness_deviations(
        ph.environment.AcousticRoughnessSpectrum(
            np.array(wavelengths), np.array(levels)
        ),
        np.full(len(_NOISE_BANDS_HZ), 70.0),
        frequencies_hz=_NOISE_BANDS_HZ,
        speed_kmh=_ALIGNED_SPEED_KMH,
    )
    bands = len(_NOISE_BANDS_HZ)
    expected = 10.0 * math.log10(bands) - 10.0 * math.log10(bands - 1 + 10.0**-0.3)
    return numeric(expected, verdict.impact_db, 1e-9, unit="dB", places=6)


@register(
    _ROLLING_STOCK,
    "ISO 3095:2013 Annex D, Formula D.1",
    "Level increase of 60 dB measured over a 55 dB background, dB",
)
def _chk_background() -> Outcome:
    expected = 60.0 - 10.0 * math.log10(10.0**6.0 - 10.0**5.5)
    computed = float(ph.environment.background_level_increase(60.0, 55.0))
    return numeric(expected, computed, 1e-12, unit="dB", places=6)
