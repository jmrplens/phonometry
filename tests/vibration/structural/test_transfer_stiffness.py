#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for ISO 10846 dynamic transfer stiffness of resilient elements.

Anchored on closed-form identities: the level ``L_k = 20 lg(|k|/k0)`` re
1 N/m, the direct-method ratio ``k2,1 = F2,b/u1``, the indirect-method inertia
relation ``k2,1 = -(2 pi f)^2 (m2+mf) T`` (Equation 1), the loss factor
``eta = Im/Re``, and the Annex-A / Table-A.2 FRF relations ``k = j omega Z =
-omega^2 m_eff``. The physically-grounded oracle is a massless Kelvin-Voigt
element (``k + j omega c``) loaded by a mass: its base transmissibility fed
back through the indirect relation recovers the element stiffness at ``T << 1``.
"""

from __future__ import annotations

import dataclasses
import math
import warnings

import numpy as np
import pytest

from phonometry import PhonometryWarning, vibration
from phonometry.vibration.structural.transfer_stiffness import TRANSMISSIBILITY_LIMIT


# ---------------------------------------------------------------------------
# Level (ISO 10846-2/-3, 3.17) — re k0 = 1 N/m
# ---------------------------------------------------------------------------
def test_level_reference_decade() -> None:
    assert vibration.transfer_stiffness_level(1.0) == pytest.approx(0.0)
    assert vibration.transfer_stiffness_level(1e6) == pytest.approx(120.0)
    assert vibration.transfer_stiffness_level(2e6) == pytest.approx(126.0206, abs=1e-3)


def test_level_uses_magnitude_of_complex() -> None:
    # |3+4j| = 5  ->  20 lg 5
    assert vibration.transfer_stiffness_level(3.0 + 4.0j) == pytest.approx(
        20.0 * math.log10(5.0)
    )


def test_level_custom_reference() -> None:
    assert vibration.transfer_stiffness_level(1e3, reference=1e3) == pytest.approx(0.0)


def test_level_rejects_non_positive_reference() -> None:
    with pytest.raises(ValueError, match=r"'reference' must be positive"):
        vibration.transfer_stiffness_level(1e6, reference=0.0)


def test_level_rejects_zero_stiffness() -> None:
    # A dead channel (|k| = 0) has no level; -inf must not propagate silently.
    with pytest.raises(ValueError, match=r"'stiffness' contains zero magnitudes"):
        vibration.transfer_stiffness_level(0.0)
    with pytest.raises(ValueError, match=r"'stiffness' contains zero magnitudes"):
        vibration.transfer_stiffness_level([1e6, 0.0 + 0.0j])


@pytest.mark.parametrize("bad", [complex("nan"), complex("inf")])
def test_level_says_non_finite_rather_than_dead_channel(bad: complex) -> None:
    """The two mistakes are told apart, so the diagnosis is true.

    A NaN compares False against the positivity bound, so folded into it a
    stiffness that was never measured was reported as a dead channel that
    read zero.
    """
    with pytest.raises(ValueError, match="non-finite magnitudes"):
        vibration.transfer_stiffness_level([1e6, bad])


# ---------------------------------------------------------------------------
# Loss factor (ISO 10846-1, 3.8)
# ---------------------------------------------------------------------------
def test_loss_factor_is_tan_phase() -> None:
    # k = k0 (1 + j eta)  ->  Im/Re = eta
    assert vibration.loss_factor(1e6 * (1.0 + 0.05j)) == pytest.approx(0.05)
    assert vibration.loss_factor(1e6 + 1j * 3e4) == pytest.approx(0.03)


def test_loss_factor_rejects_purely_imaginary_stiffness() -> None:
    # Re(k) = 0 -> eta = Im/Re is undefined, not inf.
    with pytest.raises(
        ValueError, match=r"'stiffness' contains purely imaginary values"
    ):
        vibration.loss_factor(1j * 1e6)
    with pytest.raises(
        ValueError, match=r"'stiffness' contains purely imaginary values"
    ):
        vibration.loss_factor([1e6 + 1e4j, 0.0 + 5e5j])


# ---------------------------------------------------------------------------
# Direct method (ISO 10846-2)
# ---------------------------------------------------------------------------
def test_direct_method_ratio() -> None:
    k = vibration.transfer_stiffness_direct(5.0 + 0j, 1e-6 + 0j)
    assert complex(k) == pytest.approx(5e6)


def test_direct_method_preserves_phase() -> None:
    # A phase lag in the force appears directly in k2,1.
    k = vibration.transfer_stiffness_direct(2.0 * np.exp(1j * 0.3), 1e-3 + 0j)
    assert np.angle(complex(k)) == pytest.approx(0.3)


def test_direct_method_rejects_zero_displacement() -> None:
    # A dead u1 channel must raise, not return an infinite stiffness.
    with pytest.raises(ValueError, match=r"'input_displacement' contains zeros"):
        vibration.transfer_stiffness_direct(5.0 + 0j, 0.0 + 0j)
    with pytest.raises(ValueError, match="dead input channel"):
        vibration.transfer_stiffness_direct([5.0, 4.0], [1e-6, 0.0])


# ---------------------------------------------------------------------------
# Indirect method (ISO 10846-3, Equation 1)
# ---------------------------------------------------------------------------
def test_indirect_matches_equation_1() -> None:
    f, m2, t = 500.0, 10.0, 0.01 + 0j
    expected = -((2.0 * math.pi * f) ** 2) * m2 * t
    assert complex(vibration.transfer_stiffness_indirect(f, t, m2)) == pytest.approx(
        expected
    )


def test_indirect_includes_flange_mass() -> None:
    f, t = 300.0, 0.02 + 0j
    k_no_flange = vibration.transfer_stiffness_indirect(f, t, 8.0)
    k_flange = vibration.transfer_stiffness_indirect(f, t, 8.0, flange_mass=2.0)
    assert complex(k_flange) == pytest.approx(complex(k_no_flange) * 10.0 / 8.0)


def test_indirect_recovers_kelvin_voigt_at_high_frequency() -> None:
    """A massless (k + jwc) element loaded by m: T -> indirect recovers k+jwc."""
    k, c, m = 1e6, 200.0, 5.0
    f0 = math.sqrt(k / m) / (2.0 * math.pi)
    f = 30.0 * f0  # well into T << 1
    t = vibration.base_transmissibility(f, m, k, c)
    k_rec = complex(vibration.transfer_stiffness_indirect(f, t, m))
    k_true = k + 1j * (2.0 * math.pi * f) * c
    assert k_rec == pytest.approx(k_true, rel=5e-3)


def test_indirect_rejects_bad_inputs() -> None:
    with pytest.raises(ValueError, match=r"'frequency' must be positive"):
        vibration.transfer_stiffness_indirect(0.0, 0.01 + 0j, 10.0)
    with pytest.raises(ValueError, match=r"'blocking_mass' must be positive"):
        vibration.transfer_stiffness_indirect(500.0, 0.01 + 0j, 0.0)


# ---------------------------------------------------------------------------
# Validity of the T << 1 approximation (ISO 10846-3, 6.1, Inequality 2)
# ---------------------------------------------------------------------------
def test_indirect_warns_above_transmissibility_limit() -> None:
    # |T| = 0.5 violates Inequality (2) (DeltaL1,2 < 20 dB): a warning fires.
    with pytest.warns(
        PhonometryWarning, match=r"ISO 10846-3 Inequality \(2\) is violated"
    ):
        vibration.transfer_stiffness_indirect(50.0, 0.5 + 0j, 10.0)


def test_indirect_silent_within_transmissibility_limit() -> None:
    # |T| = 0.05 satisfies Inequality (2): no PhonometryWarning is emitted.
    with warnings.catch_warnings():
        warnings.simplefilter("error", PhonometryWarning)
        vibration.transfer_stiffness_indirect(500.0, 0.05 + 0j, 10.0)
        vibration.transfer_stiffness_indirect(500.0, TRANSMISSIBILITY_LIMIT + 0j, 10.0)


def test_result_helper_warns_above_transmissibility_limit() -> None:
    f = np.array([100.0, 200.0])
    t = np.array([0.5 + 0j, 0.02 + 0j])
    with pytest.warns(
        PhonometryWarning, match=r"ISO 10846-3 Inequality \(2\) is violated"
    ):
        vibration.indirect_transfer_stiffness_result(f, t, blocking_mass=8.0)


def test_indirect_bias_at_the_validity_limit_is_within_1_db() -> None:
    """At |T| = 0.1 (DeltaL1,2 = 20 dB) the undamped mass-spring model gives
    k_indirect = 1.1 k: a 0.83 dB (10 %) bias, inside the 1 dB (12 %) bound.
    """
    k, m = 1e6, 1.0
    f = math.sqrt(11.0 * k / m) / (2.0 * math.pi)  # omega^2 m = 11 k -> T = -0.1
    t = complex(vibration.base_transmissibility(f, m, k))
    assert abs(t) == pytest.approx(TRANSMISSIBILITY_LIMIT)
    k_rec = complex(vibration.transfer_stiffness_indirect(f, t, m))
    assert abs(k_rec) / k == pytest.approx(1.1)
    bias_db = 20.0 * math.log10(abs(k_rec) / k)
    assert bias_db == pytest.approx(0.828, abs=0.001)
    assert bias_db <= 1.0
    assert abs(k_rec) / k - 1.0 <= 0.12


def test_linearity_criterion_10_db_step() -> None:
    """ISO 10846-2/-3, 7.6: input spectra 10 dB apart must give transfer-
    stiffness levels within 1.5 dB - exact equality for a linear element.
    """
    u_a, step = 1e-6 + 0j, 10.0 ** (-10.0 / 20.0)
    k = 1e6 + 3e4j
    lk_a = float(
        vibration.transfer_stiffness_level(
            vibration.transfer_stiffness_direct(k * u_a, u_a)
        )
    )
    u_b = u_a * step
    lk_b = float(
        vibration.transfer_stiffness_level(
            vibration.transfer_stiffness_direct(k * u_b, u_b)
        )
    )
    assert abs(lk_a - lk_b) <= 1.5
    assert lk_a == pytest.approx(lk_b, abs=1e-9)


def test_indirect_still_recovers_kelvin_voigt_below_the_warning() -> None:
    """The valid-range identity of Formula (1) is unchanged by the guard."""
    k, c, m = 1e6, 200.0, 5.0
    f = 30.0 * math.sqrt(k / m) / (2.0 * math.pi)  # T << 1
    with warnings.catch_warnings():
        warnings.simplefilter("error", PhonometryWarning)
        t = vibration.base_transmissibility(f, m, k, c)
        k_rec = complex(vibration.transfer_stiffness_indirect(f, t, m))
    assert k_rec == pytest.approx(k + 1j * (2.0 * math.pi * f) * c, rel=5e-3)


# ---------------------------------------------------------------------------
# Blocking-force approximation (ISO 10846-1, Equations 6 and 7)
# ---------------------------------------------------------------------------
def test_blocking_force_ratio_at_the_ten_percent_limit() -> None:
    """|k2,2/kt| = 0.1 gives F2/F2,b = 1/1.1 = 0.9091 - within 10 % (Eq. 7)."""
    ratio = complex(vibration.blocking_force_ratio(1e5, 1e6))
    assert ratio == pytest.approx(1.0 / 1.1)
    assert abs(abs(ratio) - 1.0) <= 0.10


def test_blocking_force_ratio_stiff_termination_is_unity() -> None:
    # An infinitely stiff receiver takes exactly the blocking force.
    assert complex(vibration.blocking_force_ratio(1e5, 1e12)) == pytest.approx(
        1.0, abs=1e-6
    )


def test_blocking_force_ratio_complex_and_validation() -> None:
    k22, kt = 1e5 + 1e4j, 2e6 + 5e5j
    assert complex(vibration.blocking_force_ratio(k22, kt)) == pytest.approx(
        1.0 / (1.0 + k22 / kt)
    )
    with pytest.raises(ValueError, match=r"'termination_stiffness' must be non-zero"):
        vibration.blocking_force_ratio(1e5, 0.0)


# ---------------------------------------------------------------------------
# Annex A / Table A.2 FRF relations (k = jwZ = -w^2 m_eff)
# ---------------------------------------------------------------------------
def test_stiffness_impedance_effective_mass_relations() -> None:
    f = 250.0
    w = 2.0 * math.pi * f
    k = 1e6 + 1j * 5e4
    z = vibration.convert_frf(k, f, "dynamic_stiffness", "impedance")
    m_eff = vibration.convert_frf(k, f, "dynamic_stiffness", "apparent_mass")
    assert complex(k) == pytest.approx(1j * w * complex(z))
    assert complex(k) == pytest.approx(-(w**2) * complex(m_eff))


# ---------------------------------------------------------------------------
# Result object
# ---------------------------------------------------------------------------
def test_result_bundle() -> None:
    f = np.array([100.0, 200.0, 400.0])
    t = np.array([0.05, 0.02, 0.008]) * np.exp(1j * 0.1)
    res = vibration.indirect_transfer_stiffness_result(f, t, blocking_mass=8.0)
    assert isinstance(res, vibration.TransferStiffnessResult)
    assert res.blocking_mass == 8.0
    # level is the level of the bundled stiffness
    assert np.allclose(
        res.levels, vibration.transfer_stiffness_level(res.transfer_stiffness)
    )
    # .to("impedance") = k/(jw)
    z = res.to("impedance")
    assert np.allclose(z, res.transfer_stiffness / (1j * 2.0 * np.pi * f))
    # loss factor of a constant-phase transmissibility is tan(0.1)
    assert np.allclose(res.loss_factor, math.tan(0.1))


def test_plot_returns_axes() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    f = np.logspace(1, 3, 50)
    t = vibration.base_transmissibility(f, 5.0, 1e6, 200.0)
    # The synthetic curve exceeds |T| = 0.1 near resonance, so the
    # ISO 10846-3 validity advisory is expected, as in the tests above.
    with pytest.warns(
        PhonometryWarning, match=r"ISO 10846-3 Inequality \(2\) is violated"
    ):
        res = vibration.indirect_transfer_stiffness_result(f, t, blocking_mass=5.0)
    assert res.plot() is not None


# ---------------------------------------------------------------------------
# One stiffness per frequency
# ---------------------------------------------------------------------------
def test_a_single_frequency_result_keeps_its_bare_numbers() -> None:
    """One frequency measured gives a result with no axis at all.

    The frequency pin exempts a result whose every field is nought-
    dimensional, and this call is what the exemption is for: a scalar
    frequency in, a scalar stiffness out, nothing to disagree about. Pin it
    from the accepting side too, or the exemption can be dropped without a
    single test noticing that the library stops answering its own call.
    """
    res = vibration.indirect_transfer_stiffness_result(500.0, 0.01, blocking_mass=8.0)
    assert res.frequencies.ndim == 0
    assert res.transfer_stiffness.ndim == 0
    assert complex(res.transfer_stiffness) == pytest.approx(
        complex(vibration.transfer_stiffness_indirect(500.0, 0.01, 8.0))
    )


def test_a_stiffness_short_of_its_frequencies_is_refused() -> None:
    """A spectrum one value short cannot be read against its own frequencies.

    Every reader that lays the two columns side by side refuses a short
    stiffness where it stands: ``.plot()`` and the ``.report()`` that embeds
    it inside matplotlib, ``.to()`` inside numpy's broadcast, each naming two
    shapes and neither field. The refusal here is raised at construction and
    says which column is short.
    """
    f = np.array([100.0, 200.0, 400.0])
    t = np.array([0.05, 0.02, 0.008]) * np.exp(1j * 0.1)
    res = vibration.indirect_transfer_stiffness_result(f, t, blocking_mass=8.0)
    short = res.transfer_stiffness[:-1]
    with pytest.raises(ValueError, match=rf"'transfer_stiffness' \({short.size}\)"):
        dataclasses.replace(res, transfer_stiffness=short)


def test_a_lone_frequency_beside_a_spectrum_is_refused() -> None:
    """The exemption is for all the fields at once, not for one of them.

    A bare number where the sibling carries a spectrum is the mixture the
    exemption deliberately leaves to the count: exempting each field on its
    own would let a one-frequency label sit under three stiffnesses.
    """
    res = vibration.indirect_transfer_stiffness_result(500.0, 0.01, blocking_mass=8.0)
    spectrum = np.full(3, complex(res.transfer_stiffness))
    with pytest.raises(ValueError, match="'frequencies' must have one axis"):
        dataclasses.replace(res, transfer_stiffness=spectrum)


def test_one_stiffness_under_a_swept_frequency_is_refused() -> None:
    """The one length numpy would stretch instead of rejecting.

    A stiffness of length one is the only mismatch that reaches an answer:
    ``.to()`` broadcasts it over the whole sweep and returns an impedance at
    every frequency, all of them from that single value, which is a plain
    ``1/f`` roll-off wearing the shape of a measured curve. Pin the count, or
    the exemption for a genuinely nought-dimensional result could be widened
    to cover this one and nothing would fail.
    """
    f = np.array([100.0, 200.0, 400.0])
    t = np.array([0.05, 0.02, 0.008]) * np.exp(1j * 0.1)
    res = vibration.indirect_transfer_stiffness_result(f, t, blocking_mass=8.0)
    lone = res.transfer_stiffness[:1]
    assert lone.ndim == 1
    with pytest.raises(ValueError, match="'transfer_stiffness' [(]1[)]"):
        dataclasses.replace(res, transfer_stiffness=lone)


@pytest.mark.parametrize("bad", [complex(2.0e6, math.nan), complex(2.0e6, math.inf)])
def test_a_stiffness_undetermined_only_in_its_phase_is_refused(bad: complex) -> None:
    r"""Half a measured stiffness is not a measured stiffness.

    ``k2,1`` is a phasor, and the imaginary axis is where ISO 10846-1 reads
    the damping: the loss factor (3.8) is ``Im/Re``. A band whose real part
    survived a bad bin while its imaginary part came back undetermined is
    therefore a band with no loss factor, and the direct method is where such
    a result is built, since it has no producer function of its own and the
    caller hands ``F2,b/u1`` to the constructor themselves.

    Admitted, it reached the readers as a number: ``.magnitude`` returned
    ``nan`` N/m for the band and ``.loss_factor`` a ``nan`` eta, both without
    a word, while ``.to("impedance")`` refused it as a *dead channel* that
    read zero, because ``abs(nan)`` compares False against the positivity
    bound exactly as a real zero does. Neither reader named the field, and
    the one diagnosis offered was the wrong one.
    """
    f = np.array([100.0, 200.0, 400.0])
    k = np.array([complex(1.0e6, 1.0e4), bad, complex(3.0e6, 3.0e4)])
    with pytest.raises(
        ValueError, match="'transfer_stiffness' must contain only finite values"
    ):
        vibration.TransferStiffnessResult(frequencies=f, transfer_stiffness=k)


# ---------------------------------------------------------------------------
# One-third-octave band average (ISO 10846-2 F(6), -3 F(7), -4 F(11), -5 F(6))
# ---------------------------------------------------------------------------
#: Five lines inside the 1 kHz band (891 Hz to 1122 Hz) and five inside the
#: 1250 Hz band (1122 Hz to 1413 Hz).
_TWO_BANDS_HZ = np.array([900.0, 950.0, 1000.0, 1050.0, 1100.0])
_TWO_BANDS_HZ = np.concatenate([_TWO_BANDS_HZ, _TWO_BANDS_HZ * 1.25])


def test_a_band_of_identical_lines_averages_to_itself() -> None:
    """Formula (11) is a mean of squares: n equal lines return that line."""
    k = np.full(_TWO_BANDS_HZ.size, 1.0e6 * (1.0 + 0.05j))
    bands = vibration.band_averaged_stiffness(_TWO_BANDS_HZ, k)
    assert bands.nominal_frequencies.tolist() == [1000.0, 1250.0]
    assert bands.line_counts.tolist() == [5, 5]
    assert bands.stiffness == pytest.approx(np.full(2, abs(k[0])), rel=1e-15)
    assert bands.levels == pytest.approx(np.full(2, 20.0 * math.log10(abs(k[0]))))


def test_the_band_average_is_the_root_mean_square_magnitude() -> None:
    """|k| = 1..5 MN/m in one band: k_av = sqrt((1+4+9+16+25)/5) = sqrt(11) MN/m."""
    k = 1.0e6 * np.array([1.0, 2.0j, -3.0, 4.0 + 0j, 5.0]) * np.exp(1j * 0.3)
    bands = vibration.band_averaged_stiffness(_TWO_BANDS_HZ[:5], k)
    assert float(bands.stiffness[0]) == pytest.approx(math.sqrt(11.0) * 1.0e6)


def test_a_line_belongs_to_the_base_ten_band_that_encloses_it() -> None:
    edge = 1000.0 * 10.0**0.05  # the 1 kHz / 1250 Hz band edge, 1122.02 Hz
    f = np.array(
        [900.0, 950.0, 1000.0, 1050.0, edge * (1.0 - 1e-9), edge * (1.0 + 1e-9)]
    )
    with pytest.warns(vibration.TransferStiffnessWarning, match=r"1250 Hz \(1\)"):
        bands = vibration.band_averaged_stiffness(f, np.full(f.size, 1.0e6))
    assert bands.line_counts.tolist() == [5, 1]


def test_a_band_of_four_lines_has_no_value_and_says_so() -> None:
    """Every part: "a minimum of n = 5 frequencies"; four determine nothing."""
    f = np.concatenate([_TWO_BANDS_HZ[:5], _TWO_BANDS_HZ[5:9]])
    k = np.full(f.size, 2.0e6)
    with pytest.warns(
        vibration.TransferStiffnessWarning,
        match=r"at least 5 frequencies.*1250 Hz \(4\)",
    ):
        bands = vibration.band_averaged_stiffness(f, k)
    assert bands.determined.tolist() == [True, False]
    assert math.isnan(float(bands.stiffness[1]))
    assert math.isnan(float(bands.levels[1]))


def test_lines_marked_invalid_are_left_out_of_the_average() -> None:
    k = np.full(_TWO_BANDS_HZ.size, 1.0e6)
    k[2] = 9.0e6  # an outlier the adequacy conditions refused
    valid = np.ones(k.size, dtype=bool)
    valid[2] = False
    with pytest.warns(vibration.TransferStiffnessWarning, match=r"1000 Hz \(4\)"):
        bands = vibration.band_averaged_stiffness(_TWO_BANDS_HZ, k, valid=valid)
    assert bands.line_counts.tolist() == [4, 5]
    assert float(bands.stiffness[1]) == pytest.approx(1.0e6)


def test_bands_beyond_the_outermost_valid_line_are_not_listed() -> None:
    valid = np.zeros(_TWO_BANDS_HZ.size, dtype=bool)
    valid[:5] = True
    bands = vibration.band_averaged_stiffness(
        _TWO_BANDS_HZ, np.full(_TWO_BANDS_HZ.size, 1.0e6), valid=valid
    )
    assert bands.nominal_frequencies.tolist() == [1000.0]


def test_a_band_whose_lines_were_all_excluded_is_undetermined_without_a_warning() -> (
    None
):
    """Lines refused by an adequacy condition were measured, not missing.

    Five lines in each of three bands, every line of the middle one marked
    not valid: the middle band has no value, and no warning, because the
    five-line rule is about how finely the sweep was resolved.
    """
    f = np.concatenate([_TWO_BANDS_HZ, _TWO_BANDS_HZ[:5] * 1.6])
    valid = np.ones(f.size, dtype=bool)
    valid[5:10] = False
    k = np.full(f.size, 1.0e6)
    with warnings.catch_warnings():
        warnings.simplefilter("error", vibration.TransferStiffnessWarning)
        bands = vibration.band_averaged_stiffness(f, k, valid=valid)
    assert bands.nominal_frequencies.tolist() == [1000.0, 1250.0, 1600.0]
    assert bands.line_counts.tolist() == [5, 0, 5]
    assert math.isnan(float(bands.stiffness[1]))
    assert bands.determined.tolist() == [True, False, True]


def test_the_band_average_refuses_a_repeated_line() -> None:
    f = np.array([900.0, 950.0, 950.0, 1000.0, 1050.0])
    k = np.full(f.size, 1.0e6)
    with pytest.raises(ValueError, match="must be distinct"):
        vibration.band_averaged_stiffness(f, k)


def test_the_band_average_refuses_a_mask_that_is_not_boolean() -> None:
    k = np.full(_TWO_BANDS_HZ.size, 1.0e6)
    mask = np.ones(k.size)
    with pytest.raises(ValueError, match="'valid' must be boolean"):
        vibration.band_averaged_stiffness(_TWO_BANDS_HZ, k, valid=mask)


def test_the_band_average_refuses_when_every_line_is_invalid() -> None:
    k = np.full(_TWO_BANDS_HZ.size, 1.0e6)
    mask = np.zeros(k.size, dtype=bool)
    with pytest.raises(ValueError, match="no valid line"):
        vibration.band_averaged_stiffness(_TWO_BANDS_HZ, k, valid=mask)


@pytest.mark.parametrize(
    ("stiffness", "counts"),
    [([1.0e6, 2.0e6], [5, 3]), ([1.0e6, math.nan], [5, 8])],
    ids=["value-beside-three-lines", "nan-beside-eight-lines"],
)
def test_a_band_value_exists_exactly_where_five_lines_were_averaged(
    stiffness: list[float], counts: list[int]
) -> None:
    f = np.array([1000.0, 1250.0])
    s = np.array(stiffness)
    n = np.array(counts)
    with pytest.raises(ValueError, match="exactly where a band holds at least 5"):
        vibration.BandAveragedStiffness(
            nominal_frequencies=f, center_frequencies=f, stiffness=s, line_counts=n
        )


def test_the_indirect_result_averages_only_where_the_transmissibility_is_small() -> (
    None
):
    """ISO 10846-3 Inequality (2): lines with |T| > 0,1 leave the band average."""
    f = np.geomspace(20.0, 2000.0, 400)
    t = vibration.base_transmissibility(f, 8.0, 1.0e6, 120.0)
    with pytest.warns(vibration.TransferStiffnessWarning, match="Inequality"):
        res = vibration.indirect_transfer_stiffness_result(f, t, blocking_mass=8.0)
    assert res.valid is not None
    assert res.valid.tolist() == (np.abs(t) <= TRANSMISSIBILITY_LIMIT).tolist()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", vibration.TransferStiffnessWarning)
        bands = res.band_average()
        by_hand = vibration.band_averaged_stiffness(
            f[res.valid], res.transfer_stiffness[res.valid]
        )
    assert bands.nominal_frequencies.tolist() == by_hand.nominal_frequencies.tolist()
    assert bands.line_counts.tolist() == by_hand.line_counts.tolist()
    np.testing.assert_allclose(bands.stiffness, by_hand.stiffness, rtol=1e-15)


def test_the_direct_result_averages_every_line_by_default() -> None:
    f = _TWO_BANDS_HZ
    k = np.full(f.size, 5.0e6 + 0j)
    res = vibration.TransferStiffnessResult(frequencies=f, transfer_stiffness=k)
    assert res.band_average().stiffness == pytest.approx([5.0e6, 5.0e6])


def test_a_result_refuses_validity_flags_that_are_not_boolean() -> None:
    f = _TWO_BANDS_HZ[:3]
    k = np.full(3, 1.0e6 + 0j)
    flags = np.array([1.0, 1.0, 0.0])
    with pytest.raises(ValueError, match="'valid' must be boolean"):
        vibration.TransferStiffnessResult(
            frequencies=f, transfer_stiffness=k, valid=flags
        )


def test_the_indirect_warning_is_the_transfer_stiffness_warning() -> None:
    with pytest.warns(vibration.TransferStiffnessWarning, match="Inequality"):
        vibration.transfer_stiffness_indirect(50.0, 0.5 + 0j, 10.0)
    assert issubclass(vibration.TransferStiffnessWarning, PhonometryWarning)


# ---------------------------------------------------------------------------
# Adequacy conditions: blocked output, unwanted input, output mass
# ---------------------------------------------------------------------------
def test_an_output_20_db_below_the_input_is_blocked() -> None:
    """The inequality is inclusive: 20 dB exactly holds, 19,9 dB does not."""
    f = np.array([100.0, 200.0])
    with pytest.warns(
        vibration.TransferStiffnessWarning, match="down to 19.9 dB at 200 Hz"
    ):
        check = vibration.check_blocked_output(f, [100.0, 100.0], [80.0, 80.1])
    assert check.holds.tolist() == [True, False]
    assert check.passes is False
    assert check.limit_db == pytest.approx(20.0)


def test_a_still_output_is_blocked_whatever_the_input() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", vibration.TransferStiffnessWarning)
        check = vibration.check_blocked_output([100.0], [60.0], [-math.inf])
    assert check.passes is True


def test_the_loudest_unwanted_direction_decides() -> None:
    f = np.array([100.0, 200.0])
    unwanted = np.array([[80.0, 90.0], [84.0, 70.0]])
    with pytest.warns(vibration.TransferStiffnessWarning, match="Inequality \\(2\\)"):
        check = vibration.check_unwanted_input(f, [100.0, 100.0], unwanted)
    assert check.difference_db.tolist() == [16.0, 10.0]
    assert check.holds.tolist() == [True, False]


def test_an_unwanted_direction_15_db_down_is_acceptable() -> None:
    """The inequality is inclusive: 15 dB exactly holds, 14,9 dB does not."""
    f = np.array([100.0, 200.0])
    with pytest.warns(
        vibration.TransferStiffnessWarning, match="down to 14.9 dB at 200 Hz"
    ):
        check = vibration.check_unwanted_input(f, [100.0, 100.0], [85.0, 85.1])
    assert check.holds.tolist() == [True, False]
    assert check.limit_db == pytest.approx(15.0)


def test_the_level_difference_curve_does_not_claim_the_verdict() -> None:
    """A difference that fails everywhere is labelled as what it is.

    The curve is the difference wherever it lies; only the markers carry the
    verdict, so a curve lying under its limit is never called "met".
    """
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    f = [63.0, 125.0, 250.0]
    with pytest.warns(vibration.TransferStiffnessWarning, match="unwanted directions"):
        check = vibration.check_unwanted_input(f, [100.0] * 3, [88.0] * 3)
    for language, curve, failed in (
        ("en", "level difference", "condition not met"),
        ("es", "diferencia de niveles", "condición no cumplida"),
    ):
        labels = check.plot(language=language).get_legend_handles_labels()[1]
        assert curve in labels
        assert failed in labels
        assert not any(
            label in {"condition met", "condición cumplida"} for label in labels
        )
    plt.close("all")


def test_a_level_difference_check_is_not_a_truth_value() -> None:
    check = vibration.check_blocked_output([100.0], [100.0], [50.0])
    with pytest.raises(TypeError, match="no truth value"):
        bool(check)


def test_the_output_mass_limit_is_six_percent_of_force_over_acceleration() -> None:
    """LF2 = 120 dB re 1 µN is 1 N, La2 = 100 dB re 1 µm/s² is 0,1 m/s²: 0,6 kg."""
    check = vibration.check_output_mass([100.0], 0.3, [120.0], [100.0])
    assert float(check.mass_limit_kg[0]) == pytest.approx(0.6, rel=1e-12)
    assert check.passes is True


def test_the_output_mass_on_its_limit_biases_the_force_by_half_a_decibel() -> None:
    """ISO 10846-4 NOTE 1: Inequality (3) is |L_Fb - L_F2| <= 0,5 dB.

    With m0 on the bound, the inertia force is 6 % of the measured one;
    Fb = F2 + m0 a2 moves the level by 20 lg 1,06 = 0,51 dB in phase and by
    -20 lg 0,94 = 0,54 dB in antiphase, both 0,5 dB to the tenth.
    """
    check = vibration.check_output_mass([100.0], 0.6, [120.0], [100.0])
    assert check.passes is True
    assert float(check.inertia_ratio[0]) == pytest.approx(0.06)
    worst = float(check.bias_bound_db[0])
    assert worst == pytest.approx(-20.0 * math.log10(0.94))
    f2 = 1.0
    for phase in (0.0, math.pi):
        fb = f2 + 0.6 * 0.1 * complex(math.cos(phase), math.sin(phase))
        bias = abs(20.0 * math.log10(abs(fb) / f2))
        assert round(bias, 1) == pytest.approx(0.5)
        assert bias <= worst + 1e-12


def test_a_heavy_output_mass_warns() -> None:
    """0,5 kg against limits of 0,6 kg (La2 = 100 dB) and 0,19 kg (La2 = 110 dB)."""
    with pytest.warns(vibration.TransferStiffnessWarning, match="NOTE 2"):
        check = vibration.check_output_mass(
            [100.0, 200.0], 0.5, [120.0, 120.0], [100.0, 110.0]
        )
    assert check.holds.tolist() == [True, False]
    assert check.passes is False


def test_an_output_mass_check_is_not_a_truth_value() -> None:
    check = vibration.check_output_mass([100.0], 0.1, [120.0], [100.0])
    with pytest.raises(TypeError, match="no truth value"):
        bool(check)


# ---------------------------------------------------------------------------
# Effective blocking mass (ISO 10846-4 Formula 6, ISO 10846-3 Formula 4)
# ---------------------------------------------------------------------------
def test_a_rigid_block_has_its_own_mass_and_no_upper_limit() -> None:
    f = np.geomspace(10.0, 5000.0, 50)
    m2 = 25.0
    force = np.full(f.size, 10.0 + 0j)
    a = force / m2
    em = vibration.effective_blocking_mass(f, force, a, a, blocking_mass_kg=m2)
    assert em.effective_mass_kg == pytest.approx(np.full(f.size, m2), rel=1e-15)
    assert em.upper_frequency_limit_hz is None
    assert bool(np.all(em.valid))


def test_formula_6_divides_twice_the_force_by_the_sum_of_the_two_accelerations() -> (
    None
):
    em = vibration.effective_blocking_mass(
        [100.0], [3.0 + 0j], [0.1 + 0.02j], [0.2 - 0.02j], blocking_mass_kg=20.0
    )
    assert float(em.effective_mass_kg[0]) == pytest.approx(20.0)


def test_f3_is_where_the_effective_mass_leaves_1_db() -> None:
    """m_eff = m2 (1 + (f/fc)^2) crosses 1 dB at fc sqrt(10^(1/20) - 1)."""
    fc, m2 = 3000.0, 20.0
    f = np.geomspace(40.0, 5000.0, 4000)
    m_eff = m2 * (1.0 + (f / fc) ** 2)
    ones = np.ones(f.size, dtype=complex)
    em = vibration.effective_blocking_mass(
        f, m_eff * ones, ones, ones, blocking_mass_kg=m2
    )
    expected = fc * math.sqrt(10.0**0.05 - 1.0)
    assert em.upper_frequency_limit_hz == pytest.approx(expected, rel=1e-5)
    assert bool(np.all(f[em.valid] < expected * 1.001))


def test_f3_is_interpolated_in_log_frequency_and_the_mask_ends_before_it() -> None:
    """On a coarse grid the crossing lies well inside a step of the sweep.

    The mask keeps exactly the lines before the first one outside 1 dB, and
    f3 is the crossing of the 1 dB margin interpolated linearly against the
    logarithm of frequency between that line and the one before it; on this
    grid a linear-in-f interpolation lands 0,3 Hz away.
    """
    fc, m2 = 3000.0, 20.0
    f = np.geomspace(40.0, 5000.0, 60)
    m_eff = m2 * (1.0 + (f / fc) ** 2)
    ones = np.ones(f.size, dtype=complex)
    em = vibration.effective_blocking_mass(
        f, m_eff * ones, ones, ones, blocking_mass_kg=m2
    )
    deviation = 20.0 * np.log10(m_eff / m2)
    first = int(np.flatnonzero(np.abs(deviation) > 1.0)[0])
    last = first - 1
    assert em.valid.tolist() == (f < f[first]).tolist()
    margin = 1.0 - np.abs(deviation)
    fraction = margin[last] / (margin[last] - margin[first])
    in_log_f = f[last] * (f[first] / f[last]) ** fraction
    in_f = f[last] + (f[first] - f[last]) * fraction
    f3 = em.upper_frequency_limit_hz
    assert f3 == pytest.approx(in_log_f, rel=1e-12)
    assert abs(float(in_f) - float(in_log_f)) > 0.1


def test_a_deviation_below_40_hz_does_not_set_f3() -> None:
    """ISO 10846-4 6.3.3.2: the mass-spring behaviour of the block on its supports."""
    f = np.array([10.0, 20.0, 40.0, 100.0, 1000.0])
    m_eff = np.array([30.0, 25.0, 20.0, 20.0, 20.0])
    ones = np.ones(f.size, dtype=complex)
    em = vibration.effective_blocking_mass(
        f, m_eff * ones, ones, ones, blocking_mass_kg=20.0
    )
    assert em.upper_frequency_limit_hz is None
    assert em.ignored_below_hz == pytest.approx(40.0)


def test_effective_mass_refuses_accelerations_that_cancel() -> None:
    ones = np.ones(2, dtype=complex)
    with pytest.raises(ValueError, match="sum to zero"):
        vibration.effective_blocking_mass(
            [100.0, 200.0], ones, ones, -ones, blocking_mass_kg=20.0
        )


def test_effective_mass_refuses_an_unsorted_sweep() -> None:
    ones = np.ones(2, dtype=complex)
    with pytest.raises(ValueError, match="must increase strictly"):
        vibration.effective_blocking_mass(
            [200.0, 100.0], ones, ones, ones, blocking_mass_kg=20.0
        )


# ---------------------------------------------------------------------------
# Driving-point method (ISO 10846-5)
# ---------------------------------------------------------------------------
#: The 0,2 Hz spacing of 7.5 up to 20 Hz, and on up to 400 Hz.
_SWEEP_HZ = np.arange(1.0, 400.0, 0.2)
_OMEGA = 2.0 * np.pi * _SWEEP_HZ


def _driven(stiffness: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Input force and acceleration of a 1 µm displacement into ``stiffness``."""
    u1 = 1.0e-6
    return stiffness * u1, -(_OMEGA**2) * u1 * np.ones(_SWEEP_HZ.size)


def test_formula_3_turns_force_and_acceleration_into_force_over_displacement() -> None:
    k = 1.0e6 * (1.0 + 0.04j)
    force, accel = _driven(np.full(_SWEEP_HZ.size, k))
    res = vibration.driving_point_stiffness(_SWEEP_HZ, force, accel)
    assert res.driving_point_stiffness == pytest.approx(np.full(_SWEEP_HZ.size, k))
    assert res.loss_factor == pytest.approx(np.full(_SWEEP_HZ.size, 0.04))


def test_a_massless_spring_has_a_flat_stiffness_and_no_upper_limit() -> None:
    """The closed-form anchor: |k1,1| = |k2,1| everywhere, so f_UL is never reached."""
    force, accel = _driven(np.full(_SWEEP_HZ.size, 1.0e6 + 0j))
    res = vibration.driving_point_stiffness(_SWEEP_HZ, force, accel)
    assert res.low_frequency_level_db == pytest.approx(120.0)
    assert res.upper_limiting_frequency_hz is None
    assert bool(np.all(res.valid))
    bands = res.band_average()
    assert bands.levels[bands.determined] == pytest.approx(120.0)


def test_f_ul_of_a_mass_loaded_spring_is_its_closed_form() -> None:
    """k1,1 = k - w^2 m0 falls 2 dB below its 1-20 Hz average at a known frequency."""
    k, m0 = 1.0e6, 2.0
    force, accel = _driven(k - _OMEGA**2 * m0)
    res = vibration.driving_point_stiffness(_SWEEP_HZ, force, accel)
    lines = (_SWEEP_HZ >= 1.0) & (_SWEEP_HZ <= 20.0)
    low = 10.0 * math.log10(float(np.mean((k - _OMEGA[lines] ** 2 * m0) ** 2)))
    assert res.low_frequency_level_db == pytest.approx(low, abs=1e-12)
    target = 10.0 ** ((low - 2.0) / 20.0)
    expected = math.sqrt((k - target) / m0) / (2.0 * math.pi)
    assert res.upper_limiting_frequency_hz == pytest.approx(expected, abs=0.01)
    assert float(_SWEEP_HZ[res.valid].max()) < expected


def test_band_averages_below_f_ul_are_within_2_db_of_the_transfer_stiffness() -> None:
    """Formula (7): every valid band of k1,1 is within 2 dB of k2,1 = k."""
    k, m0 = 1.0e6, 2.0
    force, accel = _driven(k - _OMEGA**2 * m0)
    res = vibration.driving_point_stiffness(_SWEEP_HZ, force, accel)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", vibration.TransferStiffnessWarning)
        bands = res.band_average()
    levels = bands.levels[bands.determined]
    assert levels.size > 0
    assert bool(np.all(np.abs(levels - 120.0) <= 2.0))


def test_the_band_average_is_quiet_about_the_short_bands_below_20_hz() -> None:
    """7.5: 0,2 Hz spacing up to 20 Hz leaves the lowest bands short of five."""
    force, accel = _driven(np.full(_SWEEP_HZ.size, 1.0e6 + 0j))
    res = vibration.driving_point_stiffness(_SWEEP_HZ, force, accel)
    with warnings.catch_warnings():
        warnings.simplefilter("error", vibration.TransferStiffnessWarning)
        bands = res.band_average()
    assert not bool(bands.determined[0])


def test_lines_where_the_output_is_not_blocked_are_excluded() -> None:
    force, accel = _driven(np.full(_SWEEP_HZ.size, 1.0e6 + 0j))
    output = accel * 1.0e-3  # 60 dB down: blocked
    output[_SWEEP_HZ > 300.0] = accel[_SWEEP_HZ > 300.0] * 0.2  # 14 dB down
    with pytest.warns(vibration.TransferStiffnessWarning, match="not blocked"):
        res = vibration.driving_point_stiffness(
            _SWEEP_HZ, force, accel, output_acceleration_m_s2=output
        )
    assert res.adequate is not None
    assert res.adequate.tolist() == (_SWEEP_HZ <= 300.0).tolist()
    assert not bool(np.any(res.valid[_SWEEP_HZ > 300.0]))


def test_lines_with_unwanted_input_motion_are_excluded() -> None:
    force, accel = _driven(np.full(_SWEEP_HZ.size, 1.0e6 + 0j))
    unwanted = np.vstack([accel * 0.01, accel * 0.01])
    unwanted[1, _SWEEP_HZ < 5.0] = accel[_SWEEP_HZ < 5.0] * 0.5
    with pytest.warns(vibration.TransferStiffnessWarning, match="unwanted directions"):
        res = vibration.driving_point_stiffness(
            _SWEEP_HZ, force, accel, unwanted_acceleration_m_s2=unwanted
        )
    assert not bool(np.any(res.valid[_SWEEP_HZ < 5.0]))


def test_a_line_exactly_on_the_threshold_is_f_ul_and_is_kept() -> None:
    """8.3: "If f <= fUL", so the line at f_UL itself is evaluated.

    Levels of 120 dB up to 20 Hz, then exactly 118 dB at 30 Hz: the 30 Hz
    line sits on the 2 dB threshold, is f_UL, and stays valid; 40 Hz does not.
    """
    f = np.array([1.0, 5.0, 10.0, 20.0, 30.0, 40.0])
    k = 10.0 ** (np.array([120.0, 120.0, 120.0, 120.0, 118.0, 117.0]) / 20.0)
    w = 2.0 * np.pi * f
    res = vibration.driving_point_stiffness(f, k * 1.0e-6, -(w**2) * 1.0e-6)
    assert res.threshold_level_db == pytest.approx(118.0, abs=1e-12)
    assert res.upper_limiting_frequency_hz == pytest.approx(30.0, abs=1e-12)
    assert res.valid.tolist() == [True, True, True, True, True, False]


def test_a_line_must_pass_both_inequalities_and_counts_nowhere_if_it_fails() -> None:
    """Inequalities (1) and (2) are both required, for f_UL and the 1-20 Hz value.

    A flat 1 MN/m element with a 3 dB dip at 9,9 Hz to 10,5 Hz, where the
    output is only 10,5 dB down (Inequality (1) fails, (2) holds), and an
    unwanted direction 6 dB down at 30 Hz to 31 Hz only. With both given the
    dip is excluded: no f_UL, and the low-frequency value is the flat 120 dB.
    """
    k = np.full(_SWEEP_HZ.size, 1.0e6 + 0j)
    dip = (_SWEEP_HZ > 9.85) & (_SWEEP_HZ < 10.55)
    k[dip] *= 10.0 ** (-3.0 / 20.0)
    force, accel = _driven(k)
    output = accel * 1.0e-3
    output[dip] = accel[dip] * 0.3
    unwanted = accel * 0.01
    loud = (_SWEEP_HZ > 29.95) & (_SWEEP_HZ < 31.05)
    unwanted[loud] = accel[loud] * 0.5
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", vibration.TransferStiffnessWarning)
        res = vibration.driving_point_stiffness(
            _SWEEP_HZ,
            force,
            accel,
            output_acceleration_m_s2=output,
            unwanted_acceleration_m_s2=unwanted,
        )
    assert res.adequate is not None
    assert res.adequate.tolist() == (~dip & ~loud).tolist()
    assert res.upper_limiting_frequency_hz is None
    assert res.low_frequency_level_db == pytest.approx(120.0, abs=1e-9)


def test_lines_below_1_hz_neither_set_f_ul_nor_enter_the_result() -> None:
    """The method starts at 1 Hz (clause 1): a dip below it is not judged."""
    f = np.arange(0.2, 400.0, 0.2)
    w = 2.0 * np.pi * f
    k = np.full(f.size, 1.0e6 + 0j)
    below = f < 0.95
    k[below] *= 10.0 ** (-3.0 / 20.0)
    res = vibration.driving_point_stiffness(f, k * 1.0e-6, -(w**2) * 1.0e-6)
    assert res.upper_limiting_frequency_hz is None
    assert res.low_frequency_level_db == pytest.approx(120.0, abs=1e-9)
    assert not bool(np.any(res.valid[below]))
    assert bool(np.all(res.valid[~below]))


def test_short_bands_are_quiet_up_to_20_hz_and_no_further() -> None:
    """7.5 asks for five lines a band only above 20 Hz.

    Lines every hertz from 1 Hz leave the 6,3 Hz to 16 Hz bands with two or
    three lines and the 20 Hz band with five: nothing warns. The same short
    bands above 20 Hz do warn.
    """
    f = np.arange(1.0, 400.0, 1.0)
    w = 2.0 * np.pi * f
    res = vibration.driving_point_stiffness(
        f, np.full(f.size, 1.0) + 0j, -(w**2) * 1.0e-6
    )
    with warnings.catch_warnings():
        warnings.simplefilter("error", vibration.TransferStiffnessWarning)
        bands = res.band_average()
    counts = dict(
        zip(bands.nominal_frequencies.tolist(), bands.line_counts.tolist(), strict=True)
    )
    assert counts[6.3] == 2
    assert counts[16.0] == 3
    assert counts[20.0] == 5
    sparse = np.concatenate([np.arange(1.0, 20.1, 0.2), [25.0, 26.0, 27.0]])
    w = 2.0 * np.pi * sparse
    short = vibration.driving_point_stiffness(
        sparse, np.full(sparse.size, 1.0) + 0j, -(w**2) * 1.0e-6
    )
    with pytest.warns(vibration.TransferStiffnessWarning, match=r"25 Hz \(3\)"):
        short.band_average()


def test_the_driving_point_method_needs_lines_from_1_to_20_hz() -> None:
    f = np.arange(25.0, 400.0, 1.0)
    w = 2.0 * np.pi * f
    force = np.full(f.size, 1.0 + 0j)
    accel = -(w**2) * 1.0e-6
    with pytest.raises(
        ValueError, match="no adequate line lies between 1 Hz and 20 Hz"
    ):
        vibration.driving_point_stiffness(f, force, accel)


def test_the_driving_point_method_refuses_a_still_input() -> None:
    force = np.ones(_SWEEP_HZ.size, dtype=complex)
    accel = np.zeros(_SWEEP_HZ.size, dtype=complex)
    with pytest.raises(ValueError, match="contains zeros"):
        vibration.driving_point_stiffness(_SWEEP_HZ, force, accel)


# ---------------------------------------------------------------------------
# Measurement uncertainty (ISO 10846-5 Annex B)
# ---------------------------------------------------------------------------
def test_the_annex_b_defaults_are_the_expressions_b3_prints() -> None:
    u = vibration.driving_point_uncertainty(120.0, repeatability_range_db=0.0)
    expected = [
        0.3,
        0.5,
        0.0,
        1.0 / (2.0 * math.sqrt(3.0)),
        2.0 / math.sqrt(3.0),
        1.5 / (2.0 * math.sqrt(3.0)),
    ]
    assert u.budget.contributions == pytest.approx(expected, abs=1e-12)
    combined = math.sqrt(sum(c * c for c in expected))
    assert u.combined_uncertainty_db == pytest.approx(combined, abs=1e-12)
    assert u.combined_uncertainty_db == pytest.approx(1.3943, abs=5e-5)
    assert u.coverage_factor == pytest.approx(2.0)
    assert u.expanded_uncertainty_db == pytest.approx(2.0 * combined, abs=1e-12)
    assert u.band_level_db == pytest.approx(120.0)


def test_the_table_b1_values_are_the_three_rectangular_terms_rounded_up() -> None:
    """Table B.1 prints 0,3, 1,2 and 0,5: each expression rounded up to a tenth.

    Rounding up is the conservative rounding an uncertainty may take (GUM
    7.2.6); to the nearest tenth the linearity term 0,433 would read 0,4.
    """
    u = vibration.driving_point_uncertainty(120.0, repeatability_range_db=0.0)
    rig, dps, lin = (float(c) for c in u.budget.contributions[3:])
    assert [math.ceil(10.0 * c) / 10.0 for c in (rig, dps, lin)] == pytest.approx(
        [0.3, 1.2, 0.5]
    )
    assert round(lin, 1) == pytest.approx(0.4)


def test_the_repeatability_spread_enters_as_p_over_root_3() -> None:
    u = vibration.driving_point_uncertainty(120.0, repeatability_range_db=1.2)
    assert float(u.budget.contributions[2]) == pytest.approx(0.6 / math.sqrt(3.0))


def test_the_printed_table_b1_values_can_be_used_instead() -> None:
    u = vibration.driving_point_uncertainty(
        120.0,
        repeatability_range_db=0.0,
        test_rig_uncertainty_db=0.3,
        discrepancy_uncertainty_db=1.2,
        linearity_uncertainty_db=0.5,
    )
    assert u.combined_uncertainty_db == pytest.approx(math.sqrt(2.12))


def test_the_budget_refuses_a_negative_spread() -> None:
    with pytest.raises(ValueError, match="repeatability_range_db"):
        vibration.driving_point_uncertainty(120.0, repeatability_range_db=-1.0)


# ---------------------------------------------------------------------------
# What the figures of the new results say
# ---------------------------------------------------------------------------
def test_the_driving_point_figure_marks_f_ul_and_the_threshold() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    k, m0 = 1.0e6, 2.0
    force, accel = _driven(k - _OMEGA**2 * m0)
    res = vibration.driving_point_stiffness(_SWEEP_HZ, force, accel)
    ax = res.plot()
    f_ul = res.upper_limiting_frequency_hz
    assert f_ul is not None
    vertical = [line for line in ax.lines if len(set(line.get_xdata())) == 1]
    assert any(float(line.get_xdata()[0]) == pytest.approx(f_ul) for line in vertical)
    horizontal = [
        float(line.get_ydata()[0])
        for line in ax.lines
        if len(set(line.get_ydata())) == 1
    ]
    assert any(y == pytest.approx(res.threshold_level_db) for y in horizontal)
    assert "f_\\mathrm{UL}" in " ".join(ax.get_legend_handles_labels()[1])
    plt.close("all")


def test_the_budget_figure_carries_one_bar_per_input_and_the_expanded_line() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    u = vibration.driving_point_uncertainty(120.0, repeatability_range_db=0.6)
    ax = u.plot(language="es")
    assert len(ax.patches) == 6
    assert "Anexo B" in ax.get_title()
    labels = ax.get_legend_handles_labels()[1]
    assert any(label.startswith("$U = 2u$") for label in labels)
    plt.close("all")


def test_the_band_figure_marks_the_undetermined_bands() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    f = np.concatenate([_TWO_BANDS_HZ[:5], _TWO_BANDS_HZ[5:8]])
    with pytest.warns(vibration.TransferStiffnessWarning, match=r"1250 Hz \(3\)"):
        bands = vibration.band_averaged_stiffness(f, np.full(f.size, 1.0e6))
    ax = bands.plot()
    assert "fewer than five lines" in ax.get_legend_handles_labels()[1]
    plt.close("all")


def test_a_band_figure_with_no_band_determined_says_so() -> None:
    """No level to draw: the y ticks go, and a note says why."""
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    f = np.geomspace(20.0, 2000.0, 60)
    with pytest.warns(vibration.TransferStiffnessWarning, match="left undetermined"):
        bands = vibration.band_averaged_stiffness(f, np.full(f.size, 1.0e6))
    assert not bool(np.any(bands.determined))
    ax = bands.plot(language="es")
    texts = [text.get_text() for text in ax.texts]
    assert "ninguna banda reúne cinco líneas válidas" in texts
    assert ax.yaxis.get_tick_params()["labelleft"] is False
    plt.close("all")


@pytest.mark.parametrize("language", ["en", "es"])
def test_the_band_figure_legend_leaves_every_marker_clear(language: str) -> None:
    """The Spanish legend is wider; it must still clear the 4 Hz marker's edge.

    Drawn on the caller's default axes, where no layout pass moves anything
    afterwards: there ``loc="best"`` put the Spanish box over the edge of the
    4 Hz marker.
    """
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    k, m0 = 1.0e6 * (1.0 + 0.05j), 2.0
    f = np.arange(1.0, 200.0, 0.2)
    w = 2.0 * np.pi * f
    res = vibration.driving_point_stiffness(
        f, (k - w**2 * m0) * 1.0e-6, -(w**2) * 1.0e-6
    )
    fig, ax = plt.subplots()
    res.band_average().plot(ax=ax, language=language)
    fig.canvas.draw()
    legend = ax.get_legend().get_window_extent()
    curve = ax.lines[0]
    radius = curve.get_markersize() * fig.dpi / 72.0 / 2.0
    points = ax.transData.transform(np.column_stack(curve.get_data()))
    points = points[np.all(np.isfinite(points), axis=1)]
    x, y = points[:, 0], points[:, 1]
    covered = (
        (x >= legend.x0 - radius)
        & (x <= legend.x1 + radius)
        & (y >= legend.y0 - radius)
        & (y <= legend.y1 + radius)
    )
    assert not bool(np.any(covered))
    plt.close("all")


def test_a_spanish_title_fits_the_default_figure() -> None:
    """The output-mass title stays inside a default 6,4 in figure in Spanish."""
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    check = vibration.check_output_mass(
        [20.0, 63.0, 125.0], 0.1, [120.0] * 3, [100.0, 104.0, 106.0]
    )
    ax = check.plot(language="es")
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    width, height = fig.bbox.width, fig.bbox.height
    for artist in (ax.title, ax.xaxis.label, ax.yaxis.label):
        box = artist.get_window_extent(renderer)
        assert box.x0 >= 0.0, artist.get_text()
        assert box.x1 <= width, artist.get_text()
        assert box.y0 >= 0.0, artist.get_text()
        assert box.y1 <= height, artist.get_text()
    plt.close("all")


def test_the_transfer_stiffness_figure_draws_the_excluded_lines_apart() -> None:
    """Lines with |T| > 0,1 are not drawn as part of the result."""
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    f = np.arange(90.0, 1120.0, 2.0)
    t = vibration.base_transmissibility(f, mass=8.0, stiffness=1.0e6, damping=120.0)
    with pytest.warns(vibration.TransferStiffnessWarning, match="Inequality \\(2\\)"):
        res = vibration.indirect_transfer_stiffness_result(f, t, blocking_mass=8.0)
    assert res.valid is not None
    ax = res.plot()
    valid_curve, excluded_curve = ax.lines[0], ax.lines[1]
    assert excluded_curve.get_label() == "excluded: adequacy condition not met"
    drawn = np.isfinite(np.asarray(valid_curve.get_ydata(), dtype=float))
    assert drawn.tolist() == res.valid.tolist()
    muted = np.isfinite(np.asarray(excluded_curve.get_ydata(), dtype=float))
    assert bool(np.all(muted[~res.valid]))
    plt.close("all")
