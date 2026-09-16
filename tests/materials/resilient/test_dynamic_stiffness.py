#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for EN 29052-1:1992 dynamic stiffness of resilient materials.

Anchored on hand-computed closed-form values of the resonance relations
(Formulae 2-4) and on the standard's own worked NOTE for the enclosed-gas term
(``s'a = 111 / d`` MN/m3 for ``p0 = 0,1 MPa``, ``epsilon = 0,9``, clause 8.2) --
a genuine published numeric oracle.
"""

from __future__ import annotations

import dataclasses
import inspect
import math

import numpy as np
import pytest
import reference_data as ref

from phonometry import materials
from phonometry.materials.resilient.dynamic_stiffness import DynamicStiffnessWarning


# ---------------------------------------------------------------------------
# Apparent dynamic stiffness (Formula 4) and its resonance inverse (Formula 3)
# ---------------------------------------------------------------------------
def test_apparent_stiffness_hand_value() -> None:
    """s't = 4 pi^2 m't fr^2: 4 pi^2 * 200 * 25^2 = 4.934802 MN/m3."""
    st = materials.apparent_dynamic_stiffness(25.0, 200.0)
    assert st == pytest.approx(4_934_802.200545, rel=1e-9)
    assert st == pytest.approx(4.0 * math.pi**2 * 200.0 * 25.0**2, rel=1e-12)


def test_apparent_stiffness_inverts_the_resonance() -> None:
    """Recovering fr from s't via Formula 3 returns the input frequency."""
    st = materials.apparent_dynamic_stiffness(25.0, 200.0)
    assert materials.natural_frequency(st, 200.0) == pytest.approx(25.0, rel=1e-12)


def test_apparent_stiffness_vectorised() -> None:
    st = materials.apparent_dynamic_stiffness([20.0, 25.0, 30.0], 200.0)
    assert isinstance(st, np.ndarray)
    assert st.shape == (3,)
    assert np.all(np.diff(st) > 0.0)  # rises with fr^2


# ---------------------------------------------------------------------------
# Enclosed-gas stiffness (Formula 7) -- standard's 111/d NOTE oracle
# ---------------------------------------------------------------------------
def test_enclosed_gas_matches_standard_note() -> None:
    """s'a = p0/(d eps); with p0=0,1 MPa, eps=0,9 the NOTE gives ~111/d MN/m3.

    The closed form yields 100000/(0,9) = 111.11.../d MN/m3 (d in mm); the
    standard rounds the printed coefficient to 111.
    """
    for d_mm in (10.0, 20.0, 50.0):
        sa = materials.enclosed_gas_stiffness(d_mm / 1000.0, 0.9)  # thickness in metres
        assert sa == pytest.approx(1.0e5 / ((d_mm / 1000.0) * 0.9), rel=1e-12)
        # cross-check against the standard's printed 111/d relationship
        assert sa / 1e6 == pytest.approx(111.0 / d_mm, rel=2e-3)


def test_enclosed_gas_true_atmosphere() -> None:
    """A real 101 325 Pa can be passed instead of the standard's 0,1 MPa."""
    sa = materials.enclosed_gas_stiffness(0.02, 0.9, atmospheric_pressure_pa=101_325.0)
    assert sa == pytest.approx(101_325.0 / (0.02 * 0.9), rel=1e-12)


def test_enclosed_gas_bad_porosity_raises() -> None:
    with pytest.raises(ValueError, match=r"'porosity' must be in the range"):
        materials.enclosed_gas_stiffness(0.02, 0.0)
    with pytest.raises(ValueError, match=r"'porosity' must be in the range"):
        materials.enclosed_gas_stiffness(0.02, 1.5)


# ---------------------------------------------------------------------------
# Natural frequency (Formula 2)
# ---------------------------------------------------------------------------
def test_natural_frequency_hand_value() -> None:
    """f0 = (1/2pi) sqrt(s'/m'): sqrt(10e6/100)/(2pi) = 50.329 Hz."""
    assert materials.natural_frequency(10.0e6, 100.0) == pytest.approx(
        50.3292121, rel=1e-6
    )


def test_natural_frequency_scales() -> None:
    """f0 scales with sqrt(s') and 1/sqrt(m')."""
    base = float(materials.natural_frequency(10.0e6, 100.0))
    assert materials.natural_frequency(40.0e6, 100.0) == pytest.approx(
        2.0 * base, rel=1e-9
    )
    assert materials.natural_frequency(10.0e6, 400.0) == pytest.approx(
        base / 2.0, rel=1e-9
    )


# ---------------------------------------------------------------------------
# Airflow-resistivity combination (clause 8.2)
# ---------------------------------------------------------------------------
def test_high_resistivity_uses_apparent_only() -> None:
    assert materials.installed_dynamic_stiffness(20e6, 150.0, gas_stiffness=3e6) == 20e6


def test_intermediate_resistivity_adds_gas() -> None:
    assert materials.installed_dynamic_stiffness(20e6, 50.0, gas_stiffness=3e6) == 23e6
    # boundary at 10 kPa.s/m2 is inclusive of the intermediate branch
    assert materials.installed_dynamic_stiffness(20e6, 10.0, gas_stiffness=3e6) == 23e6


def test_low_resistivity_negligible_gas_warns_and_uses_apparent() -> None:
    with pytest.warns(
        DynamicStiffnessWarning,
        match=r"s' is taken as s't with the enclosed-gas term disregarded",
    ):
        s = materials.installed_dynamic_stiffness(
            20e6, 5.0, gas_stiffness=1e6
        )  # 5 % of s't
    assert s == 20e6


def test_low_resistivity_significant_gas_is_unresolvable() -> None:
    with pytest.warns(
        DynamicStiffnessWarning,
        match=r"non-negligible enclosed-gas stiffness, EN 29052-1 cannot resolve",
    ):
        s = materials.installed_dynamic_stiffness(
            20e6, 5.0, gas_stiffness=5e6
        )  # 25 % of s't
    assert math.isnan(s)


# ---------------------------------------------------------------------------
# Full chain
# ---------------------------------------------------------------------------
def test_floating_floor_resonance_chain() -> None:
    res = materials.floating_floor_resonance(
        25.0, 200.0, 100.0, airflow_resistivity=50.0, thickness=0.02, porosity=0.9
    )
    assert isinstance(res, materials.DynamicStiffnessResult)
    assert res.apparent_stiffness == pytest.approx(4_934_802.2, rel=1e-6)
    assert res.gas_stiffness == pytest.approx(1.0e5 / (0.02 * 0.9), rel=1e-9)
    assert res.dynamic_stiffness == pytest.approx(
        res.apparent_stiffness + res.gas_stiffness, rel=1e-12
    )
    assert res.natural_frequency == pytest.approx(
        math.sqrt(res.dynamic_stiffness / 100.0) / (2.0 * math.pi), rel=1e-9
    )


def test_chain_high_resistivity_ignores_gas() -> None:
    """With r >= 100 kPa.s/m2 the gas term is not needed."""
    res = materials.floating_floor_resonance(25.0, 200.0, 100.0)  # default r = inf
    assert res.gas_stiffness == 0.0
    assert res.dynamic_stiffness == res.apparent_stiffness


def test_chain_requires_gas_inputs_below_100() -> None:
    with pytest.raises(
        ValueError,
        match=r"'thickness' and 'porosity' are required for the enclosed-gas term",
    ):
        materials.floating_floor_resonance(25.0, 200.0, 100.0, airflow_resistivity=50.0)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def test_non_positive_inputs_raise() -> None:
    with pytest.raises(ValueError, match=r"'resonant_frequency' must be positive"):
        materials.apparent_dynamic_stiffness(0.0, 200.0)
    with pytest.raises(ValueError, match=r"'total_mass_per_area' must be positive"):
        materials.apparent_dynamic_stiffness(25.0, 0.0)
    with pytest.raises(ValueError, match=r"'mass_per_area' must be positive"):
        materials.natural_frequency(10e6, 0.0)
    with pytest.raises(ValueError, match=r"'airflow_resistivity' must be positive"):
        materials.installed_dynamic_stiffness(20e6, 0.0)


@pytest.mark.parametrize(
    ("field_name", "message"),
    [
        ("apparent_stiffness", "'apparent_stiffness' must be positive"),
        ("resonant_frequency", "'resonant_frequency' must be positive"),
        ("floor_mass_per_area", "'floor_mass_per_area' must be positive"),
        ("gas_stiffness", "'gas_stiffness' must be non-negative"),
    ],
)
def test_a_determined_quantity_left_non_finite_is_refused(
    field_name: str, message: str
) -> None:
    """The fiche prints these four unconditionally, headline included.

    A NaN ``apparent_stiffness`` becomes the BOXED ``s't = nan MN/m3`` of a
    fully rendered accredited page and a NaN ``resonant_frequency`` prints
    ``fr = nan Hz`` in the metrics table beside it. The one producer,
    :func:`floating_floor_resonance`, computes the apparent stiffness from a
    positive resonance and load mass and pins the floor mass positive, so the
    method never leaves any of the four undetermined.
    """
    import dataclasses

    res = materials.floating_floor_resonance(25.0, 200.0, 100.0)
    with pytest.raises(ValueError, match=message):
        dataclasses.replace(res, **{field_name: float("nan")})


def test_the_unresolved_installed_stiffness_is_kept_not_refused() -> None:
    """Clause 8.2 c) cannot resolve ``s'`` for an airy specimen, and says so.

    Below 10 kPa.s/m2 with a non-negligible enclosed-gas term the method has
    no answer, so the producer hands back ``nan`` for ``s'`` and for the
    natural frequency it derives from it. That NaN is the library's own
    output, not a caller's mistake: refusing it at construction would refuse
    a real measurement outcome, so both fields stay unpinned and the fiche's
    metrics table renders the em dash for ``s'`` and omits the ``f0`` row.
    """
    with pytest.warns(DynamicStiffnessWarning):
        res = materials.floating_floor_resonance(
            25.0,
            200.0,
            100.0,
            airflow_resistivity=5.0,
            thickness=0.02,
            porosity=0.9,
        )
    assert math.isnan(res.dynamic_stiffness)
    assert math.isnan(res.natural_frequency)


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------
def test_plot_returns_axes() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    res = materials.floating_floor_resonance(25.0, 200.0, 100.0)
    assert res.plot() is not None


# ---------------------------------------------------------------------------
# Floating-floor natural frequency — Vigran's published outcomes
# ---------------------------------------------------------------------------

# Vigran, Building Acoustics (2008), Sec. 8.4.4 "Examples" pp. 317-318,
# prints the constructions and the resulting natural frequencies (~40 Hz and
# ~90 Hz); the numeric inputs below are reconstructed from the same section:
# the total dynamic stiffness s' = 8.0 MPa/m of the 25 mm mineral-wool layer
# follows from the Table 8.3 dynamic E-modulus plus the enclosed-air
# stiffness, and the plate masses per unit area are nominal values for the
# stated build-ups.


def test_natural_frequency_vigran_concrete_floating_floor() -> None:
    # 50 mm concrete floating slab (nominal m' ~ 115 kg/m2) on the
    # s' = 8.0 MPa/m layer: the book publishes f0 ~= 40 Hz, rounded to the
    # nearest 10 Hz (the reconstruction gives 42.0 Hz exactly), so 3 Hz
    # covers the rounding plus the nominal slab mass.
    assert materials.natural_frequency(8.0e6, 115.0) == pytest.approx(40.0, abs=3.0)


def test_natural_frequency_vigran_lightweight_floating_floor() -> None:
    # Same layer under a lightweight top plate of 22 mm chipboard + 13 mm
    # plasterboard (nominal m' ~ 16.7 + 11.2 ~ 28 kg/m2): the book publishes
    # f0 ~= 90 Hz, rounded to the nearest 10 Hz (the reconstruction gives
    # 85.1 Hz), so 5.5 Hz covers the rounding plus the nominal plate masses.
    assert materials.natural_frequency(8.0e6, 28.0) == pytest.approx(90.0, abs=5.5)


# ---------------------------------------------------------------------------
# The published resilient layers: the printed digits, the conversion, and what
# publishing them is not
# ---------------------------------------------------------------------------
class TestResilientLayerStiffness:
    """``PUBLISHED_RESILIENT_LAYERS`` against Hopkins Table A3 as printed.

    The printed digits live once, in ``tests/reference_data``, in the MN/m3 the
    book prints; the N/m3 values live once, in ``src``. These assertions are
    what makes the two one copy and what pins the factor of 1e6 between them.
    """

    def test_every_printed_row_ships_once(self) -> None:
        assert len(materials.PUBLISHED_RESILIENT_LAYERS) == len(
            ref.HOPKINS_TABLE_A3_MN_PER_M3
        )

    def test_each_row_is_the_printed_row_converted(self) -> None:
        """s' in N/m3 is the printed MN/m3 times 1e6; the rest is as printed."""
        rows = zip(
            materials.PUBLISHED_RESILIENT_LAYERS.values(),
            ref.HOPKINS_TABLE_A3_MN_PER_M3,
            strict=True,
        )
        for layer, (name, density, thickness, stiffness_mn) in rows:
            assert layer.name == name
            assert layer.density_kg_m3 == density
            assert layer.thickness_mm == thickness
            assert layer.dynamic_stiffness_n_m3 == pytest.approx(
                stiffness_mn * 1.0e6, rel=1e-12
            )

    def test_the_key_says_which_specimen_the_row_is(self) -> None:
        """``<material>_<density>_<thickness>``, because the print does not.

        Four rock-wool rows and four glass-wool rows differ only by those two
        numbers, and the printed table separates them by position in a merged
        cell.
        """
        for key, layer in materials.PUBLISHED_RESILIENT_LAYERS.items():
            assert key.endswith(
                f"_{int(layer.density_kg_m3)}_{int(layer.thickness_mm)}"
            ), key
        assert len(set(materials.PUBLISHED_RESILIENT_LAYERS)) == len(
            materials.PUBLISHED_RESILIENT_LAYERS
        )

    def test_second_level_attribution_is_a_field_not_a_name(self) -> None:
        """Eleven rows are the book's own; the four rebond rows are credited."""
        credited = [
            layer
            for layer in materials.PUBLISHED_RESILIENT_LAYERS.values()
            if layer.attributed_to
        ]
        first_hand = len(materials.PUBLISHED_RESILIENT_LAYERS) - len(credited)
        assert first_hand == ref.HOPKINS_TABLE_A3_FIRST_HAND_ROWS
        assert {layer.attributed_to for layer in credited} == {
            "Hopkins and Hall (2006)"
        }
        assert all(layer.name.startswith("Rebond foam") for layer in credited)
        # The attribution is out of the name, which is what lets the key exist.
        assert not any(
            "Hopkins" in layer.name
            for layer in materials.PUBLISHED_RESILIENT_LAYERS.values()
        )

    def test_every_row_cites_document_table_page_and_folio(self) -> None:
        for key, layer in materials.PUBLISHED_RESILIENT_LAYERS.items():
            assert layer.source == (
                "Hopkins (2007) Table A3, PDF page 637 (printed p. 610)"
            ), key

    def test_natural_frequency_is_formula_2_on_the_stored_stiffness(self) -> None:
        layer = materials.PUBLISHED_RESILIENT_LAYERS["mineral_wool_rock_60_30"]
        expected = materials.natural_frequency(layer.dynamic_stiffness_n_m3, 100.0)
        assert layer.natural_frequency(100.0) == pytest.approx(expected, rel=1e-12)
        # 10 MN/m3 under 100 kg/m2: f0 = sqrt(1e7/100)/(2 pi) = 50,3 Hz.
        assert layer.natural_frequency(100.0) == pytest.approx(50.33, abs=0.01)

    def test_lookup_accepts_a_key_or_a_layer(self) -> None:
        layer = materials.resilient_layer("mineral_wool_glass_75_40")
        assert layer.dynamic_stiffness_n_m3 == pytest.approx(7.0e6)
        assert materials.resilient_layer(layer) is layer

    def test_lookup_names_the_keys_there_are(self) -> None:
        with pytest.raises(ValueError, match=r"Unknown resilient layer 'rockwool'"):
            materials.resilient_layer("rockwool")
        with pytest.raises(ValueError, match=r"mineral_wool_rock_60_30"):
            materials.resilient_layer("rockwool")

    def test_the_layers_are_frozen(self) -> None:
        layer = materials.PUBLISHED_RESILIENT_LAYERS["expanded_polystyrene_14_50"]
        with pytest.raises(dataclasses.FrozenInstanceError):
            layer.dynamic_stiffness_n_m3 = 1.0  # type: ignore[misc]

    def test_no_function_defaults_to_a_published_layer(self) -> None:
        """Removing the table costs no capability (the removal policy)."""
        for function in (
            materials.natural_frequency,
            materials.installed_dynamic_stiffness,
            materials.floating_floor_resonance,
        ):
            defaults = [
                parameter.default
                for parameter in inspect.signature(function).parameters.values()
                if parameter.default is not inspect.Parameter.empty
            ]
            assert not any(
                isinstance(default, materials.ResilientLayer) for default in defaults
            ), function.__name__

    def test_table_a4_next_door_keeps_its_own_dimension(self) -> None:
        """One key, one dimension: A3 is N/m3 per unit area, A4 is N/m per tie.

        The two tables sit on the same printed folio and are two quantities, so
        they are two names and neither is expressed in the other's unit.
        """
        from phonometry import building

        assert set(building.WALL_TIE_STIFFNESS) == {
            "butterfly",
            "double_triangle",
            "vertical_twist",
            "vertical_twist_100mm",
        }
        a3 = {
            layer.dynamic_stiffness_n_m3
            for layer in materials.PUBLISHED_RESILIENT_LAYERS.values()
        }
        a4 = {stiffness for _, stiffness in building.WALL_TIE_STIFFNESS.values()}
        assert not (a3 & a4)
