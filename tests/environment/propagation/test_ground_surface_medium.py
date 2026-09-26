#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A ground row as the porous half-space of the outdoor models.

``GroundSurface.medium`` is the path from a row, published or read from a
catalogue file, to the three outdoor functions that take a ground impedance.
It adds no physics of its own: what these tests hold is that the medium is
the one each function would have worked out from the same resistivity, bit
for bit, that a cell the page does not print as one number is refused in the
page's terms rather than collapsed, and that a resistivity fitted with one
model never goes into another.
"""

from __future__ import annotations

import numpy as np
import pytest

from phonometry import environment, io, materials
from phonometry.environment.propagation import (
    PUBLISHED_GROUND,
    GroundSurface,
    linear_sound_speed_profile,
)
from phonometry.environment.propagation import ground_surfaces as module
from phonometry.fluids import Fluid

# The resistivities of real grounds put the lowest bands outside the range the
# two empirical models were fitted over, and each model says so with a
# warning; that is the models' business, not what these tests hold.
pytestmark = pytest.mark.filterwarnings("ignore::phonometry.PhonometryWarning")

BANDS = np.array([63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0])

#: Harmonoise class D, "normal uncompacted ground", as Bies prints it.
CLASS_D = PUBLISHED_GROUND["bies-2017-table-5-2/normal_uncompacted_ground"]
#: A sports field Cox prints three times, once per model it was fitted with.
FIELD_DB = PUBLISHED_GROUND["cox-2017-table-6-7/sports_field_delany_bazley"]
FIELD_SEMI = PUBLISHED_GROUND["cox-2017-table-6-7/sports_field_semi_phenomenological"]
FIELD_VARIABLE = PUBLISHED_GROUND["cox-2017-table-6-7/sports_field_variable_porosity"]


def test_the_medium_is_the_model_of_the_printed_resistivity() -> None:
    sigma = CLASS_D.printed("flow_resistivity_pa_s_m2")
    assert sigma == 200_000.0
    for model, function in (
        ("delany_bazley", materials.delany_bazley),
        ("miki", materials.miki),
    ):
        got = CLASS_D.medium(BANDS, model=model)
        want = function(BANDS, sigma)
        np.testing.assert_array_equal(
            got.normalized_impedance, want.normalized_impedance
        )
        np.testing.assert_array_equal(got.wavenumber, want.wavenumber)


@pytest.mark.parametrize(
    ("model", "function"),
    [("delany_bazley", materials.delany_bazley), ("miki", materials.miki)],
    ids=["delany_bazley", "miki"],
)
def test_the_medium_takes_the_air_it_is_given(model: str, function: object) -> None:
    cold = Fluid(
        temperature_c=0.0,
        static_pressure_pa=101_325.0,
        composition={},
        model="a test air",
        validity="",
        properties={"speed_of_sound": 331.3, "density": 1.29},
    )
    got = CLASS_D.medium(BANDS, model=model, fluid=cold)  # type: ignore[arg-type]
    want = function(BANDS, 200_000.0, fluid=cold)  # type: ignore[operator]
    np.testing.assert_array_equal(
        got.characteristic_impedance, want.characteristic_impedance
    )
    assert (got.speed_of_sound, got.air_density) == (331.3, 1.29)
    default = CLASS_D.medium(BANDS, model=model)  # type: ignore[arg-type]
    assert not np.allclose(
        got.characteristic_impedance, default.characteristic_impedance
    )


@pytest.mark.parametrize("model", ["delany_bazley", "miki"])
def test_ground_effect_takes_the_row_as_it_takes_the_resistivity(model: str) -> None:
    by_row = environment.ground_effect(
        BANDS, 1.5, 1.2, 50.0, impedance=CLASS_D.medium(BANDS, model=model)
    )
    by_number = environment.ground_effect(
        BANDS, 1.5, 1.2, 50.0, flow_resistivity=200_000.0, model=model
    )
    np.testing.assert_array_equal(
        by_row.excess_attenuation, by_number.excess_attenuation
    )
    np.testing.assert_array_equal(
        by_row.normalized_impedance, by_number.normalized_impedance
    )


def test_a_barrier_takes_the_row_as_its_ground() -> None:
    by_row = environment.barrier_insertion_loss(
        BANDS, 1.0, 20.0, 4.0, 60.0, 1.5, ground_impedance=CLASS_D.medium(BANDS)
    )
    by_number = environment.barrier_insertion_loss(
        BANDS, 1.0, 20.0, 4.0, 60.0, 1.5, ground_flow_resistivity=200_000.0
    )
    np.testing.assert_array_equal(by_row.insertion_loss, by_number.insertion_loss)


def test_the_parabolic_equation_takes_the_row_at_its_frequency() -> None:
    profile = linear_sound_speed_profile(1e-12, ground_speed=343.0, max_height=60.0)
    kwargs = {"source_height": 2.0, "max_range": 120.0, "max_height": 30.0}
    by_row = environment.atmospheric_parabolic_equation(
        500.0, profile, impedance=CLASS_D.medium([500.0]), **kwargs
    )
    by_number = environment.atmospheric_parabolic_equation(
        500.0, profile, flow_resistivity=200_000.0, **kwargs
    )
    np.testing.assert_array_equal(
        by_row.level_at_height(2.0), by_number.level_at_height(2.0)
    )


def test_an_interval_is_refused_in_the_pages_terms() -> None:
    lawn = PUBLISHED_GROUND["bies-2017-table-5-1/lawn"]
    assert lawn.ranges["flow_resistivity_pa_s_m2"] == (250_000.0, 400_000.0)
    with pytest.raises(
        ValueError,
        match=r"'Lawn' has no flow_resistivity_pa_s_m2, which 'delany_bazley' "
        r"needs: the page prints 250000 to 400000 and no value",
    ):
        lawn.medium(BANDS)


def test_an_unknown_model_is_refused() -> None:
    with pytest.raises(ValueError, match="'model' must be 'delany_bazley' or 'miki'"):
        CLASS_D.medium(BANDS, model="johnson_champoux_allard")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# A resistivity is the parameter of the model it was fitted with
# ---------------------------------------------------------------------------
def test_a_delany_bazley_fit_goes_into_delany_bazley() -> None:
    sigma = FIELD_DB.printed("flow_resistivity_pa_s_m2")
    got = FIELD_DB.medium(BANDS)
    want = materials.delany_bazley(BANDS, sigma)
    np.testing.assert_array_equal(got.normalized_impedance, want.normalized_impedance)


def test_a_delany_bazley_fit_is_refused_by_miki() -> None:
    with pytest.raises(
        ValueError,
        match=r"'Sports field' is the row the page marks “Fitted using Delany and Bazley "
        r"model” .* not of 'miki'; ask for model='delany_bazley'",
    ):
        FIELD_DB.medium(BANDS, model="miki")


@pytest.mark.parametrize("row", [FIELD_SEMI, FIELD_VARIABLE], ids=["semi", "variable"])
@pytest.mark.parametrize("model", ["delany_bazley", "miki"])
def test_a_fit_of_another_model_is_refused_by_both(
    row: GroundSurface, model: str
) -> None:
    with pytest.raises(
        ValueError,
        match=r"neither 'delany_bazley' nor 'miki' is that model, or take "
        r"row\.printed\('flow_resistivity_pa_s_m2'\)",
    ):
        row.medium(BANDS, model=model)  # type: ignore[arg-type]


#: The models each footnote under Cox & D'Antonio 3e Table 6.7 (PDF page 258,
#: printed p. 201) lets a row into: its own, when it is one of the two here.
FOOTNOTE_MODELS = {
    "Fitted using Delany and Bazley model": {"delany_bazley"},
    "Fitted using semi-phenomenological model": set(),
    "Fitted using variable porosity model": set(),
}

#: The rows no footnote marks but the text does: Sect. 6.6.3, PDF page 272
#: (printed p. 215), says the parameters Horoshenkov and Mohamed deduced for
#: their wetted sands are those of "the two-parameter model of Attenborough",
#: and the table prints those sands at four water contents each.
WET_SANDS = tuple(
    f"cox-2017-table-6-7/{sand}_water_{water}"
    for sand, waters in (
        ("coarse_sand_98um", (0, 11, 51, 95)),
        ("fine_sand_65um", (0, 15, 48, 95)),
    )
    for water in waters
)


@pytest.mark.parametrize("key", WET_SANDS)
@pytest.mark.parametrize("model", ["delany_bazley", "miki"])
def test_a_sand_the_text_ties_to_another_model_is_refused_by_both(
    key: str, model: str
) -> None:
    sand = PUBLISHED_GROUND[key]
    with pytest.raises(
        ValueError,
        match=r"whose parameters the text beside the table gives as those of "
        r"“the two-parameter model of Attenborough” \(Cox & D'Antonio 3e "
        r"Sect\. 6\.6\.3, PDF page 272, printed p\. 215\)",
    ):
        sand.medium(BANDS, model=model)  # type: ignore[arg-type]


def test_every_fit_a_published_row_names_is_one_the_method_knows() -> None:
    """A new table whose rows name a fit fails here until the fit is mapped."""
    named = {
        row.variant
        for row in PUBLISHED_GROUND.values()
        if row.variant.lower().startswith("fitted")
    }
    assert named == set(module._FITS) == set(FOOTNOTE_MODELS)
    tied = {
        (PUBLISHED_GROUND[key].table, PUBLISHED_GROUND[key].name) for key in WET_SANDS
    }
    assert tied == set(module._FITS_IN_TEXT)


@pytest.mark.parametrize("model", ["delany_bazley", "miki"])
def test_every_published_row_goes_only_into_the_models_its_page_allows(
    model: str,
) -> None:
    """Each row with one printed resistivity, whatever marks its fit or none."""
    for key, row in PUBLISHED_GROUND.items():
        try:
            row.printed("flow_resistivity_pa_s_m2")
        except ValueError:
            continue
        if row.variant in FOOTNOTE_MODELS:
            allowed = FOOTNOTE_MODELS[row.variant]
        elif key in WET_SANDS:
            allowed = set()
        else:
            allowed = {"delany_bazley", "miki"}
        try:
            row.medium(BANDS, model=model)  # type: ignore[arg-type]
        except ValueError:
            taken = False
        else:
            taken = True
        assert taken == (model in allowed), key


def test_a_row_that_names_no_fit_goes_into_either_model() -> None:
    assert CLASS_D.variant == ""
    for model in ("delany_bazley", "miki"):
        assert CLASS_D.medium(BANDS, model=model).normalized_impedance.shape == (6,)


# ---------------------------------------------------------------------------
# A ground of your own
# ---------------------------------------------------------------------------
def _site(*rows: dict[str, object]) -> io.Catalogue[GroundSurface]:
    return io.parse_catalogue(
        {
            "schema": "phonometry-catalogue",
            "schema_version": 1,
            "catalogue": "site-survey",
            "row_type": "GroundSurface",
            "about": "Effective flow resistivities fitted to a site's own measurements.",
            "provenance": {
                "kind": "measurement",
                "document": "Site survey 12",
                "version": None,
                "consulted": "2026-09-25",
                "laboratory": "Example Lab",
                "report": "26-051",
            },
            "basis": "measured",
            "rows": list(rows),
        },
        row_type=GroundSurface,
    )


def test_a_ground_of_your_own_goes_into_the_outdoor_models() -> None:
    site = _site(
        {"key": "pasture", "name": "Pasture", "flow_resistivity_kpa_s_m2": 180}
    )
    pasture = site["site-survey/pasture"]
    assert pasture.converted == {"flow_resistivity_pa_s_m2": ("180", "kPa s/m2")}
    by_row = environment.ground_effect(
        BANDS, 1.5, 1.2, 50.0, impedance=pasture.medium(BANDS)
    )
    by_number = environment.ground_effect(
        BANDS, 1.5, 1.2, 50.0, flow_resistivity=180_000.0
    )
    np.testing.assert_array_equal(
        by_row.excess_attenuation, by_number.excess_attenuation
    )


def test_a_declared_bound_of_your_own_is_refused() -> None:
    site = _site(
        {
            "key": "track",
            "name": "Gravel track",
            "ranges": {"flow_resistivity_kpa_s_m2": [500, None]},
            "bounded_below": ["flow_resistivity_kpa_s_m2"],
        }
    )
    track = site["site-survey/track"]
    with pytest.raises(
        ValueError,
        match=r"the measurement record prints a lower bound of 500 kPa s/m2 "
        r"\(500000 Pa s/m2\) and no value",
    ):
        track.medium(BANDS)
