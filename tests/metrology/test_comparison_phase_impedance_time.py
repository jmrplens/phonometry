#  Copyright (c) 2026. Jose Manuel Requena Plens
"""IEC 61094-5:2016 and IEC 61094-8:2012: the phase of a comparison
calibration, the effect of different acoustic impedances, and the
time-selective processing of IEC 61094-8 Annex B.

None of the three prints a worked example. The phase is checked against the
equations it comes from: readings built from known phases, channel shifts
and field asymmetries by the phase form of Formulas (C.1) and (C.2), or by
the monitor ratios of IEC 61094-8 A.2, have to give back the phase they
define. The impedance ratio is checked against the circuits of IEC 61094-2
Formula (3) and of the "Microphone impedance" row of IEC 61094-5 Table D.1,
evaluated here independently, and the lumped equivalent volume against the
relations of IEC 61094-2 E.4. The time-selective processing is checked as
8.6 of IEC 61094-8 suggests, on simulated data with and without a
reflection, and Formula (B.10) is evaluated as printed (BS EN 61094-8:2012,
folio 28, PDF page 30).
"""

from __future__ import annotations

import math

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from phonometry import metrology
from phonometry.metrology import comparison_calibration as cc

_F = np.array([250.0, 1000.0, 2000.0, 4000.0, 8000.0])

#: A reference and a test microphone: sensitivity levels in dB re 1 V/Pa and
#: phases in degrees.
_L_REF = np.array([-38.02, -38.00, -37.98, -37.95, -38.10])
_L_TEST = np.array([-26.40, -26.35, -26.30, -26.10, -25.80])
_PHI_REF = np.array([-0.4, -1.5, -3.1, -6.4, -14.0])
_PHI_TEST = np.array([-0.9, -2.8, -5.7, -11.9, -25.5])

#: IEC 61094-1:2000 6.2.2, kappa_r p_s,r with kappa_r = 1,40.
_KAPPA_P = 1.40 * 101325.0


def _interchange_phases(
    phi_ref: np.ndarray = _PHI_REF,
    phi_test: np.ndarray = _PHI_TEST,
    shift_1: float = 4.0,
    shift_2: float = -7.0,
    asymmetry: float = 1.5,
) -> tuple[np.ndarray, np.ndarray]:
    """The phase form of (C.1) and (C.2): the phase of channel 1's reading re
    channel 2's, before and after the interchange, with channels of different
    phase shift and a field whose phase is not the same at the two positions.
    """
    at_a = asymmetry
    at_b = -asymmetry / 3.0
    source_1, source_2 = 25.0, -40.0
    first = (phi_ref + shift_1 + source_1 + at_a) - (
        phi_test + shift_2 + source_1 + at_b
    )
    second = (phi_test + shift_1 + source_2 + at_a) - (
        phi_ref + shift_2 + source_2 + at_b
    )
    return first, second


def _level_readings() -> tuple[np.ndarray, np.ndarray]:
    return (_L_REF + 0.7) - (_L_TEST - 1.3), (_L_TEST + 0.7) - (_L_REF - 1.3)


def _phase_calibration(
    pressure_phase_difference_deg: float | None = None,
) -> metrology.ComparisonCalibration:
    first, second = _level_readings()
    phi_1, phi_2 = _interchange_phases()
    return metrology.simultaneous_comparison(
        _F,
        _L_REF,
        first,
        second,
        phase=metrology.SimultaneousComparisonPhase(
            reference_sensitivity_phase_deg=_PHI_REF,
            channel_phase_difference_deg=phi_1,
            interchanged_channel_phase_difference_deg=phi_2,
            pressure_phase_difference_deg=pressure_phase_difference_deg,
        ),
    )


# --------------------------------------------------------------------------
# The phase of the sensitivity (IEC 61094-5 5.1.1, IEC 61094-8 5.1)
# --------------------------------------------------------------------------


def test_interchange_cancels_channel_phase_shifts_and_field_asymmetry() -> None:
    result = _phase_calibration()
    np.testing.assert_allclose(result.sensitivity_phase_deg, _PHI_TEST, atol=1e-9)
    np.testing.assert_allclose(result.sensitivity_level_db, _L_TEST, atol=1e-9)


def test_phases_either_side_of_half_a_turn_are_taken_into_one_turn() -> None:
    """A reference at 175° and a test microphone at -170°: 15° apart across
    the end of the interval, which the readings wrap round.
    """
    phi_ref = np.full(_F.size, 175.0)
    phi_test = np.full(_F.size, -170.0)
    phi_1, phi_2 = _interchange_phases(phi_ref, phi_test)
    first, second = _level_readings()
    result = metrology.simultaneous_comparison(
        _F,
        _L_REF,
        first,
        second,
        phase=metrology.SimultaneousComparisonPhase(
            reference_sensitivity_phase_deg=phi_ref,
            channel_phase_difference_deg=cc._wrapped_deg(phi_1),
            interchanged_channel_phase_difference_deg=cc._wrapped_deg(phi_2),
        ),
    )
    np.testing.assert_allclose(result.output_phase_difference_deg, 15.0, atol=1e-9)
    np.testing.assert_allclose(result.sensitivity_phase_deg, -170.0, atol=1e-9)


def test_a_channel_that_inverts_the_phase_is_taken_through_one_turn() -> None:
    """A channel 180° out of phase puts the two readings either side of
    ±180°, so their difference leaves the interval from -180° to 180°; it is
    taken into one turn before it is halved, or the test microphone's phase
    would come out half a turn wrong.
    """
    phi_1, phi_2 = _interchange_phases(shift_1=180.0, shift_2=0.0)
    first_phase, second_phase = cc._wrapped_deg(phi_1), cc._wrapped_deg(phi_2)
    assert np.any(np.abs(first_phase - second_phase) > 180.0)
    first, second = _level_readings()
    result = metrology.simultaneous_comparison(
        _F,
        _L_REF,
        first,
        second,
        phase=metrology.SimultaneousComparisonPhase(
            reference_sensitivity_phase_deg=_PHI_REF,
            channel_phase_difference_deg=first_phase,
            interchanged_channel_phase_difference_deg=second_phase,
        ),
    )
    np.testing.assert_allclose(result.sensitivity_phase_deg, _PHI_TEST, atol=1e-9)


def test_wrapped_phase_lies_in_minus_half_turn_excluded_to_half_turn() -> None:
    wrapped = cc._wrapped_deg([180.0, -180.0, 190.0, -190.0, 540.0, 0.0])
    np.testing.assert_allclose(wrapped, [180.0, 180.0, -170.0, 170.0, 180.0, 0.0])


def test_determinations_either_side_of_half_a_turn_average_next_to_them() -> None:
    """Two determinations of arg R_V at 179° and at -179° average to 180°,
    not to 0°.
    """
    readings = np.vstack([_L_REF - _L_TEST, _L_REF - _L_TEST])
    phases = np.vstack([np.full(_F.size, -179.0), np.full(_F.size, 179.0)])
    result = metrology.simultaneous_comparison(
        _F,
        _L_REF,
        readings,
        field="free_field",
        phase=metrology.SimultaneousComparisonPhase(
            reference_sensitivity_phase_deg=0.0,
            channel_phase_difference_deg=phases,
        ),
    )
    rows = np.asarray(result.output_phase_differences_deg)
    np.testing.assert_allclose(rows, [[179.0] * _F.size, [-179.0] * _F.size])
    np.testing.assert_allclose(result.output_phase_difference_deg, 180.0)


def test_free_field_without_interchange_reads_the_channel_phase() -> None:
    result = metrology.simultaneous_comparison(
        _F,
        _L_REF,
        _L_REF - _L_TEST,
        field="free_field",
        phase=metrology.SimultaneousComparisonPhase(
            reference_sensitivity_phase_deg=_PHI_REF,
            channel_phase_difference_deg=_PHI_REF - _PHI_TEST,
        ),
    )
    np.testing.assert_allclose(result.sensitivity_phase_deg, _PHI_TEST, atol=1e-9)


def test_pressure_phase_is_subtracted() -> None:
    result = _phase_calibration(pressure_phase_difference_deg=2.5)
    np.testing.assert_allclose(result.sensitivity_phase_deg, _PHI_TEST - 2.5, atol=1e-9)


def test_a_calibration_without_phases_has_none() -> None:
    first, second = _level_readings()
    result = metrology.simultaneous_comparison(_F, _L_REF, first, second)
    assert result.sensitivity_phase_deg is None
    assert result.output_phase_difference_deg is None
    assert result.pressure_phase_difference_deg is None


def test_phase_inputs_are_named_not_positional() -> None:
    """The reference's phase and the readings are all in degrees, so they are
    taken by name only and cannot be swapped by position.
    """
    with pytest.raises(TypeError):
        metrology.SimultaneousComparisonPhase(_PHI_REF, _PHI_REF)  # type: ignore[misc]
    with pytest.raises(TypeError):
        metrology.SequentialComparisonPhase(_PHI_REF, _PHI_REF, _PHI_REF)  # type: ignore[misc]
    with pytest.raises(TypeError):
        metrology.MonitorReadings(80.0, 80.0)  # type: ignore[misc]


def test_phase_readings_follow_the_level_readings() -> None:
    first, second = _level_readings()
    phi_1, _ = _interchange_phases()
    phase = metrology.SimultaneousComparisonPhase(
        reference_sensitivity_phase_deg=_PHI_REF,
        channel_phase_difference_deg=phi_1,
    )
    with pytest.raises(ValueError, match="interchanged_channel_phase_difference_deg"):
        metrology.simultaneous_comparison(
            _F,
            _L_REF,
            first,
            second,
            phase=phase,
        )


def test_an_interchanged_phase_without_the_interchanged_level_is_refused() -> None:
    phi_1, phi_2 = _interchange_phases()
    phase = metrology.SimultaneousComparisonPhase(
        reference_sensitivity_phase_deg=_PHI_REF,
        channel_phase_difference_deg=phi_1,
        interchanged_channel_phase_difference_deg=phi_2,
    )
    with pytest.raises(ValueError, match="interchanged_channel_difference_db"):
        metrology.simultaneous_comparison(
            _F,
            _L_REF,
            _L_REF - _L_TEST,
            field="free_field",
            phase=phase,
        )


def test_phase_determinations_must_be_those_of_the_levels() -> None:
    first, second = _level_readings()
    phi_1, phi_2 = _interchange_phases()
    rows_1 = np.vstack([first, first, first])
    rows_2 = np.vstack([second, second, second])
    phase_rows_1 = np.vstack([phi_1, phi_1])
    phase_rows_2 = np.vstack([phi_2, phi_2])
    phase = metrology.SimultaneousComparisonPhase(
        reference_sensitivity_phase_deg=_PHI_REF,
        channel_phase_difference_deg=phase_rows_1,
        interchanged_channel_phase_difference_deg=phase_rows_2,
    )
    with pytest.raises(ValueError, match="determinations"):
        metrology.simultaneous_comparison(
            _F,
            _L_REF,
            rows_1,
            rows_2,
            phase=phase,
        )


def test_monitor_phases_cancel_a_source_that_drifts_in_phase() -> None:
    field_1 = np.array([10.0, 20.0, -30.0, 45.0, 90.0])
    field_2 = field_1 + np.array([3.0, -5.0, 8.0, 12.0, -20.0])
    monitor = 50.0
    result = metrology.sequential_comparison(
        _F,
        _L_REF,
        _L_REF + 94.0,
        _L_TEST + 94.0,
        monitor=metrology.MonitorReadings(
            reference_level_db=81.5,
            test_level_db=81.5,
            reference_phase_deg=monitor + field_1,
            test_phase_deg=monitor + field_2,
        ),
        field="free_field",
        phase=metrology.SequentialComparisonPhase(
            reference_sensitivity_phase_deg=_PHI_REF,
            reference_output_phase_deg=cc._wrapped_deg(_PHI_REF + field_1),
            test_output_phase_deg=cc._wrapped_deg(_PHI_TEST + field_2),
        ),
    )
    np.testing.assert_allclose(result.sensitivity_phase_deg, _PHI_TEST, atol=1e-9)
    np.testing.assert_allclose(result.sensitivity_level_db, _L_TEST, atol=1e-9)


def test_without_a_monitor_the_output_phases_are_differenced() -> None:
    result = metrology.sequential_comparison(
        _F,
        _L_REF,
        _L_REF + 94.0,
        _L_TEST + 94.0,
        phase=metrology.SequentialComparisonPhase(
            reference_sensitivity_phase_deg=_PHI_REF,
            reference_output_phase_deg=_PHI_REF + 33.0,
            test_output_phase_deg=_PHI_TEST + 33.0,
        ),
    )
    np.testing.assert_allclose(result.sensitivity_phase_deg, _PHI_TEST, atol=1e-9)


def test_a_monitor_read_in_level_alone_leaves_the_output_phases_as_read() -> None:
    result = metrology.sequential_comparison(
        _F,
        _L_REF,
        _L_REF + 94.0,
        _L_TEST + 94.0,
        monitor=metrology.MonitorReadings(reference_level_db=80.0, test_level_db=80.0),
        phase=metrology.SequentialComparisonPhase(
            reference_sensitivity_phase_deg=_PHI_REF,
            reference_output_phase_deg=_PHI_REF + 33.0,
            test_output_phase_deg=_PHI_TEST + 33.0,
        ),
    )
    np.testing.assert_allclose(result.sensitivity_phase_deg, _PHI_TEST, atol=1e-9)


def test_one_monitor_phase_without_the_other_is_refused() -> None:
    with pytest.raises(ValueError, match="test_phase_deg"):
        metrology.MonitorReadings(
            reference_level_db=80.0, test_level_db=80.0, reference_phase_deg=0.0
        )


def test_monitor_phases_without_output_phases_are_refused() -> None:
    monitor = metrology.MonitorReadings(
        reference_level_db=80.0,
        test_level_db=80.0,
        reference_phase_deg=0.0,
        test_phase_deg=0.0,
    )
    with pytest.raises(ValueError, match="monitor phases"):
        metrology.sequential_comparison(
            _F,
            _L_REF,
            _L_REF + 94.0,
            _L_TEST + 94.0,
            monitor=monitor,
        )


def test_monitor_phase_determinations_must_be_those_of_the_outputs() -> None:
    monitor = metrology.MonitorReadings(
        reference_level_db=80.0,
        test_level_db=80.0,
        reference_phase_deg=np.zeros((2, _F.size)),
        test_phase_deg=np.zeros((2, _F.size)),
    )
    phase = metrology.SequentialComparisonPhase(
        reference_sensitivity_phase_deg=_PHI_REF,
        reference_output_phase_deg=np.zeros((3, _F.size)),
        test_output_phase_deg=np.zeros((3, _F.size)),
    )
    with pytest.raises(ValueError, match="determinations"):
        metrology.sequential_comparison(
            _F,
            _L_REF,
            _L_REF + 94.0,
            _L_TEST + 94.0,
            monitor=monitor,
            phase=phase,
        )


def test_calibration_built_directly_refuses_a_lone_pressure_phase() -> None:
    levels = _L_TEST - _L_REF
    zeros = np.zeros(_F.size)
    with pytest.raises(ValueError, match="pressure_phase_difference_deg"):
        metrology.ComparisonCalibration(
            frequencies_hz=_F,
            reference_sensitivity_level_db=_L_REF,
            output_level_differences_db=levels,
            pressure_level_difference_db=zeros,
            corrections_db={},
            field="pressure",
            excitation="sequential",
            pressure_phase_difference_deg=zeros,
        )


def test_calibration_built_directly_refuses_phase_rows_of_other_determinations() -> (
    None
):
    levels = np.vstack([_L_TEST - _L_REF] * 3)
    phases = np.vstack([_PHI_TEST - _PHI_REF] * 2)
    zeros = np.zeros(_F.size)
    with pytest.raises(ValueError, match="one row per determination"):
        metrology.ComparisonCalibration(
            frequencies_hz=_F,
            reference_sensitivity_level_db=_L_REF,
            output_level_differences_db=levels,
            pressure_level_difference_db=zeros,
            corrections_db={},
            field="pressure",
            excitation="sequential",
            reference_sensitivity_phase_deg=_PHI_REF,
            output_phase_differences_deg=phases,
        )


def test_phase_columns_are_read_only() -> None:
    result = _phase_calibration()
    for column in (
        result.reference_sensitivity_phase_deg,
        result.output_phase_differences_deg,
        result.pressure_phase_difference_deg,
    ):
        assert column is not None
        assert not column.flags.writeable


def test_phase_plot_draws_both_phases() -> None:
    result = _phase_calibration()
    fig, ax = plt.subplots()
    result.plot(ax, quantity="phase")
    np.testing.assert_allclose(ax.get_lines()[0].get_ydata(), _PHI_TEST, atol=1e-9)
    np.testing.assert_allclose(ax.get_lines()[1].get_ydata(), _PHI_REF, atol=1e-12)
    assert "IEC 61094-5" in ax.get_title()
    plt.close(fig)
    fig, ax = plt.subplots()
    result.plot(ax, quantity="phase", language="es")
    assert ax.get_title().startswith("Fase de la sensibilidad en presión")
    plt.close(fig)


def test_phase_plot_of_a_calibration_without_phases_is_refused() -> None:
    first, second = _level_readings()
    result = metrology.simultaneous_comparison(_F, _L_REF, first, second)
    with pytest.raises(ValueError, match="carries no phase"):
        result.plot(quantity="phase")


def test_plot_refuses_an_unknown_quantity() -> None:
    result = _phase_calibration()
    with pytest.raises(ValueError, match="quantity"):
        result.plot(quantity="modulus")


# --------------------------------------------------------------------------
# Different acoustic impedances (IEC 61094-5 7.4 and 7.5)
# --------------------------------------------------------------------------

_FI = metrology.exact_frequencies(1000, 20000, fraction=3)


def _microphone(
    volume: float, resonance: float, loss: float
) -> metrology.ReciprocityMicrophone:
    """A microphone of the lumped impedance of IEC 61094-2 E.4. The front
    cavity, that of an LS2aP in Table C.1, does not enter the equivalent
    volume.
    """
    return metrology.ReciprocityMicrophone(
        equivalent_volume_m3=volume,
        resonance_frequency_hz=resonance,
        loss_factor=loss,
        front_cavity_volume_m3=34e-9,
        front_cavity_depth_m=0.5e-3,
        front_cavity_diameter_m=9.3e-3,
    )


def _lumped_volume(
    frequencies: np.ndarray | list[float], volume: float, resonance: float, loss: float
) -> np.ndarray:
    """V_e of that microphone, from the model the reciprocity calibration owns."""
    return _microphone(volume, resonance, loss).complex_equivalent_volume_m3(
        frequencies
    )


def _lumped_impedance(
    frequencies: np.ndarray, volume: float, resonance: float, loss: float
) -> np.ndarray:
    """Z_a = r_a + j w m_a + 1/(j w c_a) from the relations of IEC 61094-2 E.4."""
    compliance = volume / _KAPPA_P
    mass = 1.0 / ((2.0 * np.pi * resonance) ** 2 * compliance)
    resistance = loss / (2.0 * np.pi * resonance * compliance)
    omega = 2.0 * np.pi * frequencies
    return resistance + 1j * omega * mass + 1.0 / (1j * omega * compliance)


def test_lumped_volume_is_the_e4_impedance_by_the_61094_1_definition() -> None:
    volume = _lumped_volume(_FI, 10e-9, 22000.0, 1.1)
    impedance = _lumped_impedance(_FI, 10e-9, 22000.0, 1.1)
    expected = _KAPPA_P / (1j * 2.0 * np.pi * _FI * impedance)
    np.testing.assert_allclose(volume, expected, rtol=1e-12)


def test_lumped_volume_tends_to_its_low_frequency_value() -> None:
    volume = _lumped_volume([1.0], 150e-9, 8500.0, 1.0)
    assert volume[0].real == pytest.approx(150e-9, rel=1e-6)
    assert abs(volume[0].imag) < 1e-3 * 150e-9


def test_the_impedance_has_no_imaginary_part_at_the_resonance() -> None:
    """E.4: "The resonance frequency is the frequency at which the imaginary
    part of the acoustic impedance Z_a is zero"; and the loss factor is
    r_a 2 pi f0 c_a.
    """
    volume = _lumped_volume([22000.0], 10e-9, 22000.0, 1.1)[0]
    impedance = _KAPPA_P / (1j * 2.0 * np.pi * 22000.0 * volume)
    assert abs(impedance.imag) < 1e-9 * abs(impedance.real)
    compliance = 10e-9 / _KAPPA_P
    assert impedance.real * 2.0 * np.pi * 22000.0 * compliance == pytest.approx(1.1)


def test_coupler_ratio_is_the_ratio_of_formula_3_sums() -> None:
    """IEC 61094-2 Formula (3): the pressure in a small coupler is the source
    volume velocity over j w (V/(kappa p_s) + sum of V_e/(kappa_r p_s,r)).
    """
    reference = _lumped_volume(_FI, 10e-9, 22000.0, 1.1)
    test = _lumped_volume(_FI, 30e-9, 14000.0, 0.5)
    gas_and_monitor = 450e-9 + 8e-9
    result = metrology.impedance_pressure_ratio(
        _FI,
        reference_equivalent_volume_m3=reference,
        test_equivalent_volume_m3=test,
        coupling_equivalent_volume_m3=gas_and_monitor,
    )
    omega = 2.0 * np.pi * _FI
    admittance_ref = 1j * omega * (gas_and_monitor + reference) / _KAPPA_P
    admittance_test = 1j * omega * (gas_and_monitor + test) / _KAPPA_P
    np.testing.assert_allclose(
        result.ratio, admittance_ref / admittance_test, rtol=1e-12
    )
    assert result.coupling == "coupler"


def test_series_ratio_is_each_microphone_behind_the_air_between_them() -> None:
    """IEC 61094-5 Table D.1: "The acoustical impedance of the microphone acts
    in series with that of the air in the space between the two microphones".
    """
    reference = _lumped_volume(_FI, 10e-9, 22000.0, 1.1)
    test = _lumped_volume(_FI, 25e-9, 16000.0, 0.8)
    series = 1j * 2.0 * np.pi * _FI * 40.0 + 2.0e5
    result = metrology.impedance_pressure_ratio(
        _FI,
        reference_equivalent_volume_m3=reference,
        test_equivalent_volume_m3=test,
        coupling_impedance_pa_s_m3=series,
    )
    omega = 2.0 * np.pi * _FI
    z_ref = _KAPPA_P / (1j * omega * reference)
    z_test = _KAPPA_P / (1j * omega * test)
    expected = (z_test / (z_test + series)) / (z_ref / (z_ref + series))
    np.testing.assert_allclose(result.ratio, expected, rtol=1e-12)
    assert result.coupling == "series"


def test_microphones_of_the_same_impedance_see_the_same_pressure() -> None:
    volume = _lumped_volume(_FI, 10e-9, 22000.0, 1.1)
    result = metrology.impedance_pressure_ratio(
        _FI,
        reference_equivalent_volume_m3=volume,
        test_equivalent_volume_m3=volume,
        coupling_equivalent_volume_m3=500e-9,
    )
    np.testing.assert_allclose(result.level_difference_db, 0.0, atol=1e-12)
    np.testing.assert_allclose(result.standard_uncertainty_db, 0.0, atol=1e-12)


def test_uncertainty_is_the_level_over_root_three_as_table_d1_takes_it() -> None:
    """Table D.1: a semi-range of 0,005 dB "is equivalent to a standard
    uncertainty of 0,005/sqrt(3) dB = 0,003 dB".
    """
    ratio = 10.0 ** (0.005 / 20.0)
    result = cc.ImpedancePressureRatio(
        frequencies_hz=np.array([2000.0]),
        ratio=np.array([ratio]),
        coupling="series",
        coupling_equivalent_volume_m3=np.array([1e-6]),
    )
    assert result.level_difference_db[0] == pytest.approx(0.005, rel=1e-9)
    assert round(float(result.standard_uncertainty_db[0]), 3) == pytest.approx(0.003)


def test_ratio_corrects_a_calibration_in_level_and_phase() -> None:
    reference = _lumped_volume(_F, 10e-9, 22000.0, 1.1)
    test = _lumped_volume(_F, 30e-9, 14000.0, 0.5)
    ratio = metrology.impedance_pressure_ratio(
        _F,
        reference_equivalent_volume_m3=reference,
        test_equivalent_volume_m3=test,
        coupling_equivalent_volume_m3=600e-9,
    )
    # The test microphone hears R_P times the reference's pressure.
    result = metrology.sequential_comparison(
        _F,
        _L_REF,
        _L_REF + 94.0,
        _L_TEST + 94.0 + ratio.level_difference_db,
        pressure_level_difference_db=ratio.level_difference_db,
        phase=metrology.SequentialComparisonPhase(
            reference_sensitivity_phase_deg=_PHI_REF,
            reference_output_phase_deg=_PHI_REF,
            test_output_phase_deg=_PHI_TEST + ratio.phase_difference_deg,
            pressure_phase_difference_deg=ratio.phase_difference_deg,
        ),
    )
    np.testing.assert_allclose(result.sensitivity_level_db, _L_TEST, atol=1e-9)
    np.testing.assert_allclose(result.sensitivity_phase_deg, _PHI_TEST, atol=1e-9)


def test_exactly_one_coupling_is_required() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        metrology.impedance_pressure_ratio(
            _F, reference_equivalent_volume_m3=1e-8, test_equivalent_volume_m3=2e-8
        )


def test_both_couplings_are_refused() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        metrology.impedance_pressure_ratio(
            _F,
            reference_equivalent_volume_m3=1e-8,
            test_equivalent_volume_m3=2e-8,
            coupling_equivalent_volume_m3=1e-7,
            coupling_impedance_pa_s_m3=1e6,
        )


def test_a_series_impedance_of_zero_is_refused() -> None:
    with pytest.raises(ValueError, match="must not be zero"):
        metrology.impedance_pressure_ratio(
            _F,
            reference_equivalent_volume_m3=1e-8,
            test_equivalent_volume_m3=2e-8,
            coupling_impedance_pa_s_m3=0.0,
        )


def test_volumes_that_cancel_are_refused() -> None:
    with pytest.raises(ValueError, match="cancel"):
        metrology.impedance_pressure_ratio(
            _F,
            reference_equivalent_volume_m3=1e-8,
            test_equivalent_volume_m3=-1e-7,
            coupling_equivalent_volume_m3=1e-7,
        )


def test_a_volume_column_of_another_length_is_refused() -> None:
    with pytest.raises(ValueError, match="one value per frequency"):
        metrology.impedance_pressure_ratio(
            _F,
            reference_equivalent_volume_m3=[1e-8, 2e-8],
            test_equivalent_volume_m3=2e-8,
            coupling_equivalent_volume_m3=1e-7,
        )


@pytest.mark.parametrize(
    ("volume", "match"),
    [("ten", "must be numeric"), (np.nan, "must contain only finite values")],
)
def test_a_volume_that_is_not_a_finite_number_is_refused(
    volume: object, match: str
) -> None:
    with pytest.raises(ValueError, match=f"reference_equivalent_volume_m3' {match}"):
        metrology.impedance_pressure_ratio(
            _F,
            reference_equivalent_volume_m3=volume,  # type: ignore[arg-type]
            test_equivalent_volume_m3=2e-8,
            coupling_equivalent_volume_m3=1e-7,
        )


def test_impedance_ratio_columns_are_read_only() -> None:
    result = metrology.impedance_pressure_ratio(
        _F,
        reference_equivalent_volume_m3=1e-8,
        test_equivalent_volume_m3=2e-8,
        coupling_equivalent_volume_m3=1e-7,
    )
    assert not result.ratio.flags.writeable
    assert not result.coupling_equivalent_volume_m3.flags.writeable
    assert not result.frequencies_hz.flags.writeable


def test_impedance_plot_draws_the_level_and_its_uncertainty_or_the_phase() -> None:
    result = metrology.impedance_pressure_ratio(
        _FI,
        reference_equivalent_volume_m3=1e-8,
        test_equivalent_volume_m3=_lumped_volume(_FI, 3e-8, 1.4e4, 0.5),
        coupling_equivalent_volume_m3=6e-7,
    )
    fig, ax = plt.subplots()
    result.plot(ax)
    lines = ax.get_lines()
    np.testing.assert_allclose(lines[1].get_ydata(), result.level_difference_db)
    np.testing.assert_allclose(lines[2].get_ydata(), result.standard_uncertainty_db)
    assert "Formula (3)" in ax.get_title()
    plt.close(fig)
    fig, ax = plt.subplots()
    result.plot(ax, quantity="phase", language="es")
    np.testing.assert_allclose(
        ax.get_lines()[1].get_ydata(), result.phase_difference_deg
    )
    assert "fórmula (3)" in ax.get_title()
    plt.close(fig)


# --------------------------------------------------------------------------
# The direct impulse method (IEC 61094-8 B.6)
# --------------------------------------------------------------------------


def test_spectrum_is_formula_b10_as_printed() -> None:
    """X(f) = 2ab sin(2 pi f b)/(2 pi f b), with b half the duration."""
    a, b = 10.0, 2.5e-6
    pulse = metrology.rectangular_pulse(2.0 * b, amplitude_v=a)
    frequencies = np.array([1.0e3, 2.0e4, 5.0e4, 1.0e5, 1.5e5, 3.3e5])
    printed = (
        2 * a * b * np.sin(2 * np.pi * frequencies * b) / (2 * np.pi * frequencies * b)
    )
    np.testing.assert_allclose(pulse.spectrum_at(frequencies), printed, rtol=1e-12)
    assert pulse.spectrum_at([0.0])[0] == pytest.approx(2 * a * b)
    assert pulse.half_duration_s == pytest.approx(b)
    assert pulse.area_v_s == pytest.approx(2 * a * b)


def test_first_zero_is_at_one_over_2b() -> None:
    pulse = metrology.rectangular_pulse(5e-6)
    assert pulse.first_zero_hz == pytest.approx(1.0 / (2.0 * 2.5e-6))
    assert abs(pulse.spectrum_at([pulse.first_zero_hz])[0]) < 1e-12 * pulse.area_v_s


def test_an_order_of_magnitude_above_20_khz_is_a_few_microseconds() -> None:
    duration = metrology.rectangular_pulse_duration_s(20000.0)
    assert duration == pytest.approx(5e-6)
    pulse = metrology.rectangular_pulse(duration)
    assert pulse.half_duration_s == pytest.approx(2.5e-6)
    droop = float(pulse.level_db_at([20000.0])[0])
    assert droop == pytest.approx(
        20.0 * math.log10(math.sin(0.1 * math.pi) / (0.1 * math.pi))
    )
    assert round(droop, 2) == pytest.approx(-0.14)


def test_a_zero_ratio_of_one_or_less_is_refused() -> None:
    with pytest.raises(ValueError, match="above 1"):
        metrology.rectangular_pulse_duration_s(20000.0, zero_ratio=1.0)


def test_a_pulse_of_no_duration_is_refused() -> None:
    with pytest.raises(ValueError, match="duration_s"):
        metrology.rectangular_pulse(0.0)


def test_pulse_plot_marks_the_first_zero_and_the_upper_limit() -> None:
    pulse = metrology.rectangular_pulse(5e-6, amplitude_v=10.0)
    fig, ax = plt.subplots()
    pulse.plot(ax, upper_frequency_hz=20000.0)
    labels = [text.get_text() for text in ax.get_legend().get_texts()]
    assert labels[1] == "First zero, $1/(2b)$ = 200 kHz"
    assert labels[2] == "Upper limit of interest, 20 kHz: \u22120.14 dB"
    assert "Formula (B.10)" in ax.get_title()
    plt.close(fig)
    fig, ax = plt.subplots()
    pulse.plot(ax, language="es")
    assert "fórmula (B.10)" in ax.get_title()
    assert len(ax.get_legend().get_texts()) == 2
    plt.close(fig)


# --------------------------------------------------------------------------
# Time-selective processing (IEC 61094-8 B.1.3 and B.2)
# --------------------------------------------------------------------------

_FS = 96000.0
_FT = np.array([500.0, 1000.0, 2000.0, 5000.0, 10000.0, 20000.0])


def _direct_and_reflection(
    t0: float = 0.003, t1: float = 0.0065, gain: float = 0.3, samples: int = 4800
) -> np.ndarray:
    """A direct impulse of unit area at t0 and a reflection at t1, sampled."""
    response = np.zeros(samples)
    response[round(t0 * _FS)] = _FS
    response[round(t1 * _FS)] = gain * _FS
    return response


def test_window_keeps_the_direct_sound_and_drops_the_reflection() -> None:
    """IEC 61094-8 8.6: simulated with and without the reflection, the
    windowed response is the same, and is that of the direct sound. The
    direct sound arrives 289 samples in, a delay whose phase is not a whole
    number of half turns at any of the frequencies, so a transform of the
    wrong sign would not pass.
    """
    with_reflection = metrology.time_selective_response(
        _direct_and_reflection(t0=0.00301),
        _FS,
        window_start_s=0.0025,
        window_end_s=0.006,
    )
    without = metrology.time_selective_response(
        _direct_and_reflection(t0=0.00301, gain=0.0),
        _FS,
        window_start_s=0.0025,
        window_end_s=0.006,
    )
    delay = round(0.00301 * _FS) / _FS
    assert np.all(np.abs(np.exp(-2j * np.pi * _FT * delay).imag) > 0.01)
    expected = np.exp(-2j * np.pi * _FT * delay)
    np.testing.assert_allclose(with_reflection.response_at(_FT), expected, atol=1e-12)
    np.testing.assert_allclose(without.response_at(_FT), expected, atol=1e-12)
    np.testing.assert_allclose(with_reflection.level_db_at(_FT), 0.0, atol=1e-10)
    record = np.abs(with_reflection.record_response_at(_FT))
    assert np.max(np.abs(20.0 * np.log10(record))) > 1.0


def test_phase_is_that_of_the_delay_from_the_start_of_the_record() -> None:
    result = metrology.time_selective_response(
        _direct_and_reflection(t0=0.00301),
        _FS,
        window_start_s=0.0025,
        window_end_s=0.006,
    )
    delay = round(0.00301 * _FS) / _FS
    np.testing.assert_allclose(
        result.phase_deg_at(_FT),
        cc._wrapped_deg(-360.0 * _FT * delay),
        atol=1e-9,
    )


@pytest.mark.parametrize("shape", ["tukey", "hann", "hamming", "rectangular"])
def test_window_shape_is_zero_outside_the_window(shape: str) -> None:
    result = metrology.time_selective_response(
        _direct_and_reflection(),
        _FS,
        window_start_s=0.0025,
        window_end_s=0.006,
        window_shape=shape,
    )
    window = result.window
    first, last = round(0.0025 * _FS), round(0.006 * _FS)
    assert np.all(window[:first] == 0.0)
    assert np.all(window[last + 1 :] == 0.0)
    assert window[first : last + 1].max() == pytest.approx(1.0, abs=1e-3)


def _rising_cosine(position: np.ndarray, edge: float) -> np.ndarray:
    """A taper of ``edge`` samples rising from 0 to 1 by half a cosine, and 1
    beyond it.
    """
    taper = 0.5 * (1.0 - np.cos(np.pi * np.minimum(position, edge) / edge))
    return np.asarray(taper, dtype=np.float64)


@pytest.mark.parametrize("taper", [0.2, None])
def test_tukey_window_tapers_half_the_fraction_at_each_edge(
    taper: float | None,
) -> None:
    """The default taper of 0,25 puts an eighth of the window in each edge,
    each a half cosine from 0 to 1, flat between them.
    """
    options = {} if taper is None else {"taper_fraction": taper}
    result = metrology.time_selective_response(
        _direct_and_reflection(),
        _FS,
        window_start_s=0.0025,
        window_end_s=0.006,
        **options,  # type: ignore[arg-type]
    )
    fraction = 0.25 if taper is None else taper
    assert result.taper_fraction == pytest.approx(fraction)
    first, last = round(0.0025 * _FS), round(0.006 * _FS)
    k = np.arange(last - first + 1, dtype=np.float64)
    edge = 0.5 * fraction * k[-1]
    expected = np.minimum(_rising_cosine(k, edge), _rising_cosine(k[::-1], edge))
    np.testing.assert_allclose(result.window[first : last + 1], expected, atol=1e-12)


@pytest.mark.parametrize(
    ("shape", "edge_value"),
    [("hann", 0.0), ("hamming", 0.08), ("rectangular", 1.0)],
)
def test_window_shapes_are_their_closed_forms(shape: str, edge_value: float) -> None:
    """Hann, 0,5 - 0,5 cos(2 pi k/(N - 1)); Hamming, 0,54 - 0,46 cos(2 pi
    k/(N - 1)), 0,08 at its edges; rectangular, 1 throughout.
    """
    result = metrology.time_selective_response(
        _direct_and_reflection(),
        _FS,
        window_start_s=0.0025,
        window_end_s=0.006,
        window_shape=shape,
    )
    first, last = round(0.0025 * _FS), round(0.006 * _FS)
    k = np.arange(last - first + 1, dtype=np.float64)
    cosine = np.cos(2.0 * np.pi * k / k[-1])
    expected = {
        "hann": 0.5 - 0.5 * cosine,
        "hamming": 0.54 - 0.46 * cosine,
        "rectangular": np.ones(k.size),
    }[shape]
    window = result.window[first : last + 1]
    np.testing.assert_allclose(window, expected, atol=1e-12)
    assert window[0] == pytest.approx(edge_value)
    assert window[-1] == pytest.approx(edge_value)


def test_tukey_window_is_flat_between_its_tapers() -> None:
    result = metrology.time_selective_response(
        _direct_and_reflection(),
        _FS,
        window_start_s=0.0025,
        window_end_s=0.006,
        taper_fraction=0.2,
    )
    window = result.window
    first, last = round(0.0025 * _FS), round(0.006 * _FS)
    span = last - first
    middle = window[first + int(0.11 * span) : last - int(0.11 * span)]
    np.testing.assert_allclose(middle, 1.0)
    assert window[first] == pytest.approx(0.0)
    assert result.window_length_s == pytest.approx(0.0035)
    assert result.frequency_resolution_hz == pytest.approx(1.0 / 0.0035)


def test_region_of_the_window_runs_from_the_arrival_to_its_end() -> None:
    result = metrology.time_selective_response(
        _direct_and_reflection(), _FS, window_start_s=0.0025, window_end_s=0.006
    )
    region = result.free_field_region(1.0, 0.003)
    assert region.window_time_s == pytest.approx(0.003)
    assert region.major_axis_m == pytest.approx(1.0 + 0.003 * region.speed_of_sound)


def test_an_arrival_after_the_window_is_refused() -> None:
    result = metrology.time_selective_response(
        _direct_and_reflection(), _FS, window_start_s=0.0025, window_end_s=0.006
    )
    with pytest.raises(ValueError, match="not before the window"):
        result.free_field_region(1.0, 0.007)


def test_reflection_free_window_inverts_formula_b1() -> None:
    window = metrology.reflection_free_window_s(1.0, 2.2)
    region = metrology.free_field_region(1.0, window)
    assert region.major_axis_m == pytest.approx(2.2, rel=1e-12)


def test_a_reflection_shorter_than_the_direct_path_is_refused() -> None:
    with pytest.raises(ValueError, match="not longer than the direct one"):
        metrology.reflection_free_window_s(1.0, 1.0)


@pytest.mark.parametrize(
    ("start", "end", "match"),
    [
        (0.006, 0.0025, "begin before it ends"),
        (0.0025, 0.06, "end within the record"),
        (0.0025, 0.0025 + 0.5 / _FS, "at least 2 samples"),
    ],
)
def test_a_window_outside_the_record_or_too_short_is_refused(
    start: float, end: float, match: str
) -> None:
    response = _direct_and_reflection()
    with pytest.raises(ValueError, match=match):
        metrology.time_selective_response(
            response, _FS, window_start_s=start, window_end_s=end
        )


def test_an_unknown_window_shape_is_refused() -> None:
    response = _direct_and_reflection()
    with pytest.raises(ValueError, match="window_shape"):
        metrology.time_selective_response(
            response,
            _FS,
            window_start_s=0.0025,
            window_end_s=0.006,
            window_shape="gauss",
        )


@pytest.mark.parametrize("taper", [0.0, 1.5])
def test_a_taper_outside_zero_to_one_is_refused(taper: float) -> None:
    response = _direct_and_reflection()
    with pytest.raises(ValueError, match="taper_fraction"):
        metrology.time_selective_response(
            response,
            _FS,
            window_start_s=0.0025,
            window_end_s=0.006,
            taper_fraction=taper,
        )


def test_a_response_that_is_not_one_value_per_sample_is_refused() -> None:
    response = np.zeros((2, 100))
    with pytest.raises(ValueError, match="'impulse_response' must be a non-empty 1-D"):
        metrology.time_selective_response(
            response, _FS, window_start_s=0.0, window_end_s=0.0005
        )


def test_a_response_of_one_sample_is_refused() -> None:
    response = np.zeros(1)
    with pytest.raises(ValueError, match="one value per sample, at least two"):
        metrology.time_selective_response(
            response, _FS, window_start_s=0.0, window_end_s=0.0005
        )


def test_a_pulse_is_divided_out_of_a_direct_impulse_measurement() -> None:
    """B.6: a rectangular pulse of 5 us drives a source whose response is a
    delay of 3 ms; dividing the windowed spectrum by the pulse's gives the
    delay back. The samples stand for the pulse by the midpoint rule, so the
    pulse they hold begins half a sample before its first sample.
    """
    rate = 1.0e7
    duration = 5e-6
    recording = np.zeros(int(0.008 * rate))
    start = round(0.003 * rate)
    recording[start : start + round(duration * rate)] = 10.0
    pulse = metrology.rectangular_pulse(duration, amplitude_v=10.0)
    result = metrology.time_selective_response(
        recording, rate, window_start_s=0.0025, window_end_s=0.006, excitation=pulse
    )
    frequencies = np.array([1000.0, 5000.0, 20000.0])
    expected = np.exp(-2j * np.pi * frequencies * (start - 0.5) / rate)
    np.testing.assert_allclose(result.response_at(frequencies), expected, atol=1e-5)


def test_response_plot_of_a_pulse_measurement_stays_below_the_first_zero() -> None:
    """With a pulse, the default range stops a tenth of the way to the first
    zero of its spectrum (B.6.1), where a quarter of the sample rate would be
    past it and the division refused.
    """
    rate = 1.0e7
    duration = 5e-6
    recording = np.zeros(int(0.008 * rate))
    start = round(0.003 * rate)
    recording[start : start + round(duration * rate)] = 10.0
    pulse = metrology.rectangular_pulse(duration, amplitude_v=10.0)
    result = metrology.time_selective_response(
        recording, rate, window_start_s=0.0025, window_end_s=0.006, excitation=pulse
    )
    fig, ax = plt.subplots()
    result.plot(ax, quantity="response")
    top = float(ax.get_lines()[0].get_xdata()[-1])
    plt.close(fig)
    assert top == pytest.approx(pulse.first_zero_hz / 10.0, rel=1e-12)
    assert top < 0.25 * rate


def test_time_selective_columns_are_read_only() -> None:
    result = metrology.time_selective_response(
        _direct_and_reflection(), _FS, window_start_s=0.0025, window_end_s=0.006
    )
    assert not result.impulse_response.flags.writeable


def test_time_selective_plot_draws_the_window_or_the_two_responses() -> None:
    result = metrology.time_selective_response(
        _direct_and_reflection(), _FS, window_start_s=0.0025, window_end_s=0.006
    )
    fig, ax = plt.subplots()
    result.plot(ax)
    lines = ax.get_lines()
    np.testing.assert_allclose(lines[1].get_ydata(), result.window)
    assert lines[1].get_label() == "Time window, Tukey, 3.50 ms"
    plt.close(fig)
    fig, ax = plt.subplots()
    result.plot(ax, quantity="response", frequencies_hz=_FT, language="es")
    lines = ax.get_lines()
    np.testing.assert_allclose(lines[1].get_ydata(), 0.0, atol=1e-9)
    assert lines[0].get_label() == "Registro completo, con las reflexiones"
    plt.close(fig)


# --------------------------------------------------------------------------
# The stepped-sine method (IEC 61094-8 B.2)
# --------------------------------------------------------------------------


def _stepped_sine(step: float, top: float) -> tuple[np.ndarray, np.ndarray]:
    frequencies = np.arange(0.0, top + step / 2.0, step)
    response = np.exp(-2j * np.pi * frequencies * 0.00301) + 0.3 * np.exp(
        -2j * np.pi * frequencies * 0.0065
    )
    return frequencies, response


def test_formula_b3_and_b2_round_trip_through_the_window() -> None:
    """A stepped-sine measurement of a direct sound and a reflection, taken to
    the time domain by (B.3), windowed and taken back by (B.2), is the direct
    sound alone. At 3,01 ms its phase is not a whole number of half turns at
    any of the frequencies, so (B.2) or (B.3) of the wrong sign would not
    pass.
    """
    frequencies, response = _stepped_sine(50.0, 100000.0)
    impulse = metrology.stepped_sine_impulse_response(frequencies, response)
    result = metrology.time_selective_response(
        impulse.impulse_response,
        impulse.sample_rate_hz,
        window_start_s=0.0025,
        window_end_s=0.006,
    )
    expected = np.exp(-2j * np.pi * _FT * 0.00301)
    np.testing.assert_allclose(result.response_at(_FT), expected, atol=1e-4)


def test_inverse_transform_of_a_flat_response_is_an_impulse_at_zero() -> None:
    frequencies = np.arange(0.0, 1000.0 + 1.0, 10.0)
    impulse = metrology.stepped_sine_impulse_response(
        frequencies, np.ones(frequencies.size)
    )
    assert impulse.impulse_response[0] == pytest.approx(impulse.sample_rate_hz)
    np.testing.assert_allclose(impulse.impulse_response[1:], 0.0, atol=1e-9)


def test_impulse_response_lasts_the_inverse_of_the_frequency_step() -> None:
    """B.2.2: "the length of the impulse response will be the inverse of the
    size of the frequency step"; 120 Hz in a small anechoic room "because the
    primary reflections all occur before 8 ms".
    """
    frequencies, response = _stepped_sine(120.0, 24000.0)
    impulse = metrology.stepped_sine_impulse_response(frequencies, response)
    assert impulse.duration_s == pytest.approx(1.0 / 120.0)
    assert impulse.duration_s > 0.008
    assert impulse.impulse_response.size / impulse.sample_rate_hz == pytest.approx(
        impulse.duration_s
    )
    assert impulse.time_s[-1] < impulse.duration_s


def test_stepped_sine_refuses_an_axis_that_does_not_start_at_zero() -> None:
    frequencies = np.arange(50.0, 1000.0, 50.0)
    response = np.ones(frequencies.size)
    with pytest.raises(ValueError, match="start at 0 Hz"):
        metrology.stepped_sine_impulse_response(frequencies, response)


def test_stepped_sine_refuses_an_unequal_step() -> None:
    frequencies = np.array([0.0, 50.0, 100.0, 160.0])
    response = np.ones(frequencies.size)
    with pytest.raises(ValueError, match="equally spaced"):
        metrology.stepped_sine_impulse_response(frequencies, response)


def test_stepped_sine_refuses_a_single_frequency() -> None:
    frequencies = np.array([0.0])
    response = np.ones(1)
    with pytest.raises(ValueError, match="at least two frequencies, from 0 Hz"):
        metrology.stepped_sine_impulse_response(frequencies, response)


def test_stepped_sine_response_of_one_sample_is_refused() -> None:
    response = np.zeros(1)
    with pytest.raises(ValueError, match="one value per sample, at least two"):
        metrology.SteppedSineImpulseResponse(
            frequency_step_hz=50.0, impulse_response=response
        )


def test_stepped_sine_refuses_a_response_of_another_length() -> None:
    frequencies = np.arange(0.0, 500.0, 50.0)
    response = np.ones(frequencies.size + 1)
    with pytest.raises(ValueError, match="one value per frequency"):
        metrology.stepped_sine_impulse_response(frequencies, response)


def test_stepped_sine_plot_names_the_step_and_the_length() -> None:
    frequencies, response = _stepped_sine(120.0, 24000.0)
    impulse = metrology.stepped_sine_impulse_response(frequencies, response)
    fig, ax = plt.subplots()
    impulse.plot(ax)
    assert "= 120 Hz" in ax.get_title()
    assert "8.33 ms" in ax.get_title()
    plt.close(fig)
    fig, ax = plt.subplots()
    impulse.plot(ax, language="es")
    assert "8,33 ms" in ax.get_title()
    plt.close(fig)


def test_stepped_sine_leaves_the_measured_response_as_it_was() -> None:
    frequencies = np.arange(0.0, 500.0, 50.0)
    response = np.full(frequencies.size, 1.0 + 0.5j)
    metrology.stepped_sine_impulse_response(frequencies, response)
    assert response[0] == 1.0 + 0.5j


def test_frequencies_at_the_first_zero_of_the_pulse_are_refused() -> None:
    pulse = metrology.rectangular_pulse(1e-3)
    result = metrology.time_selective_response(
        _direct_and_reflection(),
        _FS,
        window_start_s=0.0025,
        window_end_s=0.006,
        excitation=pulse,
    )
    frequencies = np.array([500.0, 1000.0])
    with pytest.raises(ValueError, match="first zero"):
        result.response_at(frequencies)
