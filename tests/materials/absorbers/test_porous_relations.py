#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Completing a published specimen from the columns its table happened to print.

Four relations, each from a printed page, each filling a different hole in a
catalogue row: the porosity from the two densities, the airflow resistivity from
the bulk density and the fibre diameter, and the characteristic lengths from
either the three measured parameters or the fibre geometry.

The interesting part is not that the arithmetic is right, which is one line
each, but how far each one can be trusted, so that is what most of these tests
measure. Hopkins' two equations check each other on his own rock wool. Allard's
Eq. (5.25) is held against the twenty-three specimens his book prints with all
four columns, which is what the docstring's "factor of two" is, and the two
routes to the viscous length are made to disagree on purpose, because they are
different models and a caller who thinks otherwise will pick the wrong one.
"""

from __future__ import annotations

import math
import warnings

import pytest
import reference_data as ref

from phonometry.materials.absorbers.porous import (
    PUBLISHED_AIR,
    ROCK_WOOL_LATERAL_FIT,
    ROCK_WOOL_LONGITUDINAL_FIT,
    FibreResistivityFit,
    PorousAbsorberWarning,
    airflow_resistivity_from_bulk_density,
    fibre_characteristic_lengths,
    porosity_from_bulk_density,
    viscous_characteristic_length,
)

#: One row of :data:`reference_data.ALLARD_JCA_SPECIMENS`: the material, the
#: table, the PDF page, the printed folio, then the five numbers.
Specimen = tuple[str, str, int, int, float, float, float, float, float]

#: The fibre radius of Hopkins' rock wool, in metres: half the printed diameter.
_ROCK_WOOL_FIBRE_RADIUS_M = ref.HOPKINS_ROCK_WOOL_FIBRE_DIAMETER_UM / 2.0 * 1e-6


def _shape_factor(row: Specimen) -> float:
    """What ``c`` of Eq. (5.25) would make the estimate land on the table."""
    _, _, _, _, sigma, phi, alpha, printed_um, _ = row
    estimate_um = (
        math.sqrt(8.0 * ref.ALLARD_AIR_VISCOSITY_PA_S * alpha / (sigma * phi)) * 1e6
    )
    return estimate_um / printed_um


# ---------------------------------------------------------------------------
# Porosity: Hopkins Eq. (1.160)
# ---------------------------------------------------------------------------
def test_the_two_ends_of_the_printed_density_range_give_the_printed_porosities() -> (
    None
):
    """Eq. (1.160) and Eq. (1.165) are printed on facing pages and agree.

    The bulk-density range the resistivity fit was made over, put through the
    porosity relation at the stated fibre density, returns the porosity range
    the same page prints. Nothing forces that, so it is worth asserting.
    """
    low_density = ref.HOPKINS_ROCK_WOOL_LATERAL_FIT[2]
    high_density = ref.HOPKINS_ROCK_WOOL_LATERAL_FIT[3]
    highest_porosity, lowest_porosity = ref.HOPKINS_ROCK_WOOL_POROSITY_RANGE

    at_low = porosity_from_bulk_density(
        low_density, fibre_density_kg_m3=ref.HOPKINS_ROCK_WOOL_FIBRE_DENSITY
    )
    at_high = porosity_from_bulk_density(
        high_density, fibre_density_kg_m3=ref.HOPKINS_ROCK_WOOL_FIBRE_DENSITY
    )

    assert at_low == pytest.approx(highest_porosity, abs=0.005)
    assert at_high == pytest.approx(lowest_porosity, abs=0.005)


def test_a_denser_material_is_a_less_porous_one() -> None:
    """The one monotonicity the relation has, and the whole of its content."""
    fibre = ref.HOPKINS_ROCK_WOOL_FIBRE_DENSITY
    light = porosity_from_bulk_density(20.0, fibre_density_kg_m3=fibre)
    heavy = porosity_from_bulk_density(200.0, fibre_density_kg_m3=fibre)

    assert light > heavy


def test_a_bulk_density_at_the_fibre_density_is_refused() -> None:
    """Zero porosity is not a porous material, and neither is a negative one."""
    with pytest.raises(ValueError, match="fibre_density_kg_m3"):
        porosity_from_bulk_density(2600.0, fibre_density_kg_m3=2600.0)
    with pytest.raises(ValueError, match="fibre_density_kg_m3"):
        porosity_from_bulk_density(3000.0, fibre_density_kg_m3=2600.0)


@pytest.mark.parametrize("bad", [0.0, -1.0, float("nan")])
def test_both_porosity_densities_have_to_be_positive(bad: float) -> None:
    """A density of zero says nothing about a pore."""
    with pytest.raises(ValueError, match="bulk_density_kg_m3"):
        porosity_from_bulk_density(bad, fibre_density_kg_m3=2600.0)
    with pytest.raises(ValueError, match="fibre_density_kg_m3"):
        porosity_from_bulk_density(60.0, fibre_density_kg_m3=bad)


# ---------------------------------------------------------------------------
# Airflow resistivity: Hopkins Eq. (1.165)
# ---------------------------------------------------------------------------
def test_the_two_published_fits_carry_the_printed_coefficients() -> None:
    """The constants are the whole of what the page gives, so they are pinned."""
    lateral = ROCK_WOOL_LATERAL_FIT
    longitudinal = ROCK_WOOL_LONGITUDINAL_FIT
    assert (
        lateral.k1,
        lateral.k2,
        lateral.bulk_density_range_kg_m3[0],
        lateral.bulk_density_range_kg_m3[1],
    ) == ref.HOPKINS_ROCK_WOOL_LATERAL_FIT
    assert (
        longitudinal.k1,
        longitudinal.k2,
        longitudinal.bulk_density_range_kg_m3[0],
        longitudinal.bulk_density_range_kg_m3[1],
    ) == ref.HOPKINS_ROCK_WOOL_LONGITUDINAL_FIT
    assert lateral.fibre_diameter_um == ref.HOPKINS_ROCK_WOOL_FIBRE_DIAMETER_UM
    assert longitudinal.fibre_diameter_um == ref.HOPKINS_ROCK_WOOL_FIBRE_DIAMETER_UM


@pytest.mark.parametrize("density", [40.0, 60.0, 100.0, 150.0])
def test_the_wool_resists_more_through_the_sheet_than_across_it(density: float) -> None:
    """Mineral wool is anisotropic, which is why the page prints two fits.

    The fibres lie mostly in the plane, so a flow through the sheet crosses more
    of them than a flow along it. Both fits come from the same measurements and
    the ordering between them is the physical content of having two.
    """
    lateral = airflow_resistivity_from_bulk_density(density, fit=ROCK_WOOL_LATERAL_FIT)
    longitudinal = airflow_resistivity_from_bulk_density(
        density, fit=ROCK_WOOL_LONGITUDINAL_FIT
    )

    assert longitudinal > lateral


def test_the_resistivity_of_a_typical_wool_is_the_order_the_models_expect() -> None:
    """A 60 kg/m3 rock wool, the commonest slab there is, lands where it should.

    Delany-Bazley and Miki are fitted over roughly 1 to 100 kPa s/m2 and a wool
    of this density is squarely inside that, which is the sanity check that says
    the micrometre in the denominator was not read as a metre.
    """
    resistivity = airflow_resistivity_from_bulk_density(
        60.0, fit=ROCK_WOOL_LONGITUDINAL_FIT
    )

    assert 10_000.0 < resistivity < 40_000.0


def test_the_relation_grows_faster_than_the_density_does() -> None:
    """The exponent is ``1 + k2``, so doubling the density more than doubles it."""
    at_50 = airflow_resistivity_from_bulk_density(50.0, fit=ROCK_WOOL_LATERAL_FIT)
    at_100 = airflow_resistivity_from_bulk_density(100.0, fit=ROCK_WOOL_LATERAL_FIT)

    assert at_100 / at_50 == pytest.approx(2.0 ** (1.0 + ROCK_WOOL_LATERAL_FIT.k2))


def test_a_density_outside_the_fitted_range_is_announced() -> None:
    """It is a regression through measured points, not a law, and says so."""
    with pytest.warns(PorousAbsorberWarning, match="outside the 31 to 155"):
        airflow_resistivity_from_bulk_density(200.0, fit=ROCK_WOOL_LATERAL_FIT)
    with pytest.warns(PorousAbsorberWarning, match="lateral"):
        airflow_resistivity_from_bulk_density(10.0, fit=ROCK_WOOL_LATERAL_FIT)


@pytest.mark.parametrize("density", [31.0, 90.0, 155.0])
def test_a_density_inside_the_fitted_range_is_silent(density: float) -> None:
    """Including both ends of it, which are measured points and not guesses."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        airflow_resistivity_from_bulk_density(density, fit=ROCK_WOOL_LATERAL_FIT)


def test_a_finer_fibre_resists_more(recwarn: pytest.WarningsRecorder) -> None:
    """The diameter is squared in the denominator, so it is the strongest lever."""
    coarse = FibreResistivityFit(
        k1=353.0,
        k2=0.63,
        fibre_diameter_um=9.5,
        bulk_density_range_kg_m3=(31.0, 155.0),
        direction="lateral",
        source="a doubled fibre diameter, to halve nothing else",
    )

    fine = airflow_resistivity_from_bulk_density(60.0, fit=ROCK_WOOL_LATERAL_FIT)
    blunt = airflow_resistivity_from_bulk_density(60.0, fit=coarse)

    assert fine / blunt == pytest.approx(4.0)
    assert not recwarn.list


@pytest.mark.parametrize("bad", [0.0, -1.0, float("nan")])
def test_the_resistivity_density_has_to_be_positive(bad: float) -> None:
    """A slab of nothing has no resistivity to compute."""
    with pytest.raises(ValueError, match="bulk_density_kg_m3"):
        airflow_resistivity_from_bulk_density(bad, fit=ROCK_WOOL_LATERAL_FIT)


# ---------------------------------------------------------------------------
# Viscous length: Allard & Atalla Eq. (5.25), and what it is worth
# ---------------------------------------------------------------------------
def test_the_estimate_is_within_a_factor_of_two_for_most_of_the_printed_corpus() -> (
    None
):
    """The docstring says eighteen of twenty-three; this is what holds it there.

    The count is the claim. If a future edition of the viscosity, or a change to
    the default fluid, moves any specimen across the factor of two, the number in
    the docstring stops being true and this fails.
    """
    factors = [_shape_factor(row) for row in ref.ALLARD_JCA_SPECIMENS]
    within = [c for c in factors if 0.5 <= c <= 2.0]

    assert len(factors) == 23
    assert len(within) == 18


def test_the_carpets_are_the_rows_the_relation_is_not_for() -> None:
    """A pile is not a cylindrical pore, and the arithmetic says so loudly."""
    carpets = [
        _shape_factor(row)
        for row in ref.ALLARD_JCA_SPECIMENS
        if row[0] in ref.ALLARD_JCA_CARPET_ROWS
    ]

    assert len(carpets) == 2
    assert all(c > 7.0 for c in carpets)


@pytest.mark.parametrize(
    "row", ref.ALLARD_JCA_SPECIMENS, ids=lambda r: f"{r[1]} {r[0]}"
)
def test_every_printed_specimen_reproduces_through_its_own_shape_factor(
    row: Specimen,
) -> None:
    """Whatever ``c`` a specimen wants, passing it back returns the table.

    This is the algebra of Eq. (5.25) rather than its accuracy, and it is the
    part that has to be exact: the shape factor divides, it does not multiply,
    and getting that backwards would pass every accuracy test above.
    """
    _, _, _, _, sigma, phi, alpha, printed_um, _ = row
    shape = _shape_factor(row)

    got = viscous_characteristic_length(
        sigma, porosity=phi, tortuosity=alpha, shape_factor=shape
    )

    assert got * 1e6 == pytest.approx(printed_um, rel=1e-9)


def test_the_default_fluid_is_the_air_the_book_states() -> None:
    """Allard's viscosity and the library's published air are the same number."""
    assert PUBLISHED_AIR.viscosity == pytest.approx(ref.ALLARD_AIR_VISCOSITY_PA_S)


def test_a_more_resistive_material_has_a_narrower_pore() -> None:
    """The one direction the relation fixes, and the reason it exists."""
    loose = viscous_characteristic_length(5_000.0, porosity=0.98, tortuosity=1.0)
    tight = viscous_characteristic_length(500_000.0, porosity=0.98, tortuosity=1.0)

    assert loose > tight


def test_a_porosity_above_one_is_refused() -> None:
    """More open volume than volume is not a material."""
    with pytest.raises(ValueError, match="porosity"):
        viscous_characteristic_length(20_000.0, porosity=1.2, tortuosity=1.0)


def test_a_tortuosity_below_one_is_refused() -> None:
    """A path through a pore cannot be shorter than the straight line."""
    with pytest.raises(ValueError, match="tortuosity"):
        viscous_characteristic_length(20_000.0, porosity=0.98, tortuosity=0.9)


@pytest.mark.parametrize("bad", [0.0, -1.0, float("nan")])
def test_the_resistivity_and_the_shape_factor_have_to_be_positive(bad: float) -> None:
    """Both are divisors, and a zero divisor is not a material property."""
    with pytest.raises(ValueError, match="flow_resistivity_pa_s_m2"):
        viscous_characteristic_length(bad, porosity=0.98, tortuosity=1.0)
    with pytest.raises(ValueError, match="shape_factor"):
        viscous_characteristic_length(
            20_000.0, porosity=0.98, tortuosity=1.0, shape_factor=bad
        )


# ---------------------------------------------------------------------------
# Both lengths from the fibre: Allard & Atalla Eqs. (5.29) and (5.30)
# ---------------------------------------------------------------------------
def test_the_thermal_length_is_twice_the_viscous_one() -> None:
    """Eq. (5.30) is Eq. (5.29) without the 2, so the ratio is the model."""
    lengths = fibre_characteristic_lengths(
        _ROCK_WOOL_FIBRE_RADIUS_M,
        bulk_density_kg_m3=60.0,
        fibre_density_kg_m3=ref.HOPKINS_ROCK_WOOL_FIBRE_DENSITY,
    )

    assert lengths.thermal_length_m == pytest.approx(2.0 * lengths.viscous_length_m)


def test_eliminating_the_fibre_length_reproduces_the_printed_equation() -> None:
    """The substitution is arithmetic on a definition, so it is checked as one.

    Eq. (5.29) is written in the total fibre length per unit volume, ``L``. Take
    an ``L``, build the bulk density a cylinder bundle of that ``L`` would have,
    and the function has to return ``1 / (2 pi L R)`` with nothing left over.
    """
    radius = 3.0e-6
    fibre_length_per_m3 = 4.0e9
    fibre_density = ref.HOPKINS_ROCK_WOOL_FIBRE_DENSITY
    bulk = fibre_density * math.pi * radius**2 * fibre_length_per_m3

    got = fibre_characteristic_lengths(
        radius, bulk_density_kg_m3=bulk, fibre_density_kg_m3=fibre_density
    )

    printed = 1.0 / (2.0 * math.pi * fibre_length_per_m3 * radius)
    assert got.viscous_length_m == pytest.approx(printed, rel=1e-12)


def test_a_wool_of_the_usual_density_has_pores_of_the_usual_size() -> None:
    """Tens of micrometres, which is the range every published table prints."""
    lengths = fibre_characteristic_lengths(
        _ROCK_WOOL_FIBRE_RADIUS_M,
        bulk_density_kg_m3=60.0,
        fibre_density_kg_m3=ref.HOPKINS_ROCK_WOOL_FIBRE_DENSITY,
    )

    assert 20e-6 < lengths.viscous_length_m < 200e-6


@pytest.mark.parametrize(("density", "expected"), [(38.0, 1.42), (155.0, 1.94)])
def test_the_two_routes_to_the_viscous_length_drift_apart_with_density(
    density: float, expected: float
) -> None:
    """The docstring's 1,4 and 1,9, measured rather than asserted.

    Both routes are given the same rock wool: the resistivity and the porosity
    from Hopkins' two equations, the geometry from his fibre diameter and fibre
    density. They are different models, the cylinder bundle is the lower one
    throughout, and the gap widens as the wool gets denser. A caller who takes
    them for two estimates of one quantity should see this table first.
    """
    resistivity = airflow_resistivity_from_bulk_density(
        density, fit=ROCK_WOOL_LONGITUDINAL_FIT
    )
    porosity = porosity_from_bulk_density(
        density, fibre_density_kg_m3=ref.HOPKINS_ROCK_WOOL_FIBRE_DENSITY
    )
    from_parameters = viscous_characteristic_length(
        resistivity, porosity=porosity, tortuosity=1.0
    )
    from_geometry = fibre_characteristic_lengths(
        _ROCK_WOOL_FIBRE_RADIUS_M,
        bulk_density_kg_m3=density,
        fibre_density_kg_m3=ref.HOPKINS_ROCK_WOOL_FIBRE_DENSITY,
    ).viscous_length_m

    assert from_parameters / from_geometry == pytest.approx(expected, abs=0.01)


@pytest.mark.parametrize("bad", [0.0, -1.0, float("nan")])
def test_the_three_fibre_inputs_have_to_be_positive(bad: float) -> None:
    """A radius or a density of zero leaves no geometry to compute from."""
    fibre = ref.HOPKINS_ROCK_WOOL_FIBRE_DENSITY
    with pytest.raises(ValueError, match="fibre_radius_m"):
        fibre_characteristic_lengths(
            bad, bulk_density_kg_m3=60.0, fibre_density_kg_m3=fibre
        )
    with pytest.raises(ValueError, match="bulk_density_kg_m3"):
        fibre_characteristic_lengths(
            _ROCK_WOOL_FIBRE_RADIUS_M,
            bulk_density_kg_m3=bad,
            fibre_density_kg_m3=fibre,
        )
    with pytest.raises(ValueError, match="fibre_density_kg_m3"):
        fibre_characteristic_lengths(
            _ROCK_WOOL_FIBRE_RADIUS_M,
            bulk_density_kg_m3=60.0,
            fibre_density_kg_m3=bad,
        )
