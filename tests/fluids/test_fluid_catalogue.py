#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The named fluid states, against the pages and the models behind them.

The catalogue's job is not to hold numbers, which already live beside the
models and the standards that fix them. Its job is to hold the states a book
prints as a table, so these tests are mostly about provenance: that each row
carries the page it was read on, that a blank column stays blank, and that the
catalogue does not quietly grow to hold the four airs of the tree, which
belong beside the documents that fix them.
"""

from __future__ import annotations

import pytest

from phonometry.building.prediction.detailed_model import EN_12354_AIR
from phonometry.fluids import PUBLISHED_FLUIDS, Fluid
from phonometry.materials.absorbers.airflow_resistance import ANNEX_A_AIR
from phonometry.materials.absorbers.porous import PUBLISHED_AIR
from phonometry.simulation.ntff import SIMULATION_AIR

#: Bies 5e Table C.1, PDF page 746 (printed p. 717), the three rows it prints
#: before its solids, read a second time off the rendered page: the
#: temperature is part of the printed material name, and the modulus and the
#: loss factor columns are blank for all three.
BIES_FLUIDS = (
    ("air", "Air", 20.0, 1.206, 343.0),
    ("fresh_water", "Fresh water", 20.0, 998.0, 1497.0),
    ("sea_water", "Sea water", 13.0, 1025.0, 1530.0),
)


# ---------------------------------------------------------------------------
# The transcription
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("key", "name", "temperature", "density", "speed"), BIES_FLUIDS
)
def test_each_printed_fluid_row_is_the_state_it_prints(
    key: str, name: str, temperature: float, density: float, speed: float
) -> None:
    state = PUBLISHED_FLUIDS[f"bies-2017-table-c1-fluids/{key}"]
    assert state.temperature_c == temperature
    assert state.density == density
    assert state.speed_of_sound == speed
    assert name in state.model


@pytest.mark.parametrize("key", [key for key, *_ in BIES_FLUIDS])
def test_a_transcribed_state_names_its_page(key: str) -> None:
    """The table is what produced it, so the table is what its model names."""
    model = PUBLISHED_FLUIDS[f"bies-2017-table-c1-fluids/{key}"].model
    assert "Bies 5e Table C.1" in model
    assert "PDF page 746 (printed p. 717)" in model


@pytest.mark.parametrize("key", [key for key, *_ in BIES_FLUIDS])
def test_a_transcribed_state_carries_the_books_own_hedge(key: str) -> None:
    """A density taken off that table arrives with what the book says about it."""
    validity = PUBLISHED_FLUIDS[f"bies-2017-table-c1-fluids/{key}"].validity
    assert "representative only" in validity


def test_a_transcribed_state_holds_only_what_the_page_printed() -> None:
    """Three blank columns stay blank, rather than being filled from elsewhere.

    The page leaves the modulus and the loss factor empty for all three fluids
    and prints a Poisson ratio only for the two waters, which is not a
    property of a fluid this library stores. A state that answered for a
    viscosity here would be answering out of another document.
    """
    water = PUBLISHED_FLUIDS["bies-2017-table-c1-fluids/fresh_water"]
    assert set(water.properties) == {"speed_of_sound", "density"}
    with pytest.raises(AttributeError):
        _ = water.viscosity


def test_the_pressure_of_a_transcribed_state_is_the_one_the_table_assumes() -> None:
    """A table of densities at a temperature and no pressure means one atmosphere."""
    for key, *_ in BIES_FLUIDS:
        state = PUBLISHED_FLUIDS[f"bies-2017-table-c1-fluids/{key}"]
        assert state.static_pressure_pa == 101325.0


# ---------------------------------------------------------------------------
# What the catalogue deliberately does not hold
# ---------------------------------------------------------------------------
def test_the_catalogue_holds_only_what_it_read_from_a_page() -> None:
    """The four airs of the tree are not gathered here, and that is the design.

    Each of them sits beside the model or the standard that fixes it, which is
    where it belongs, and gathering them would invert the dependency this
    package exists at the bottom of: a catalogue in the transverse toolbox that
    imported ``materials``, ``building`` and ``simulation`` to reach them would
    make the medium depend on three of the domains that stand on it. The
    comparison a reader wants is a documentation artefact and is built as one.
    """
    assert {key.split("/", 1)[0] for key in PUBLISHED_FLUIDS} == {
        "bies-2017-table-c1-fluids",
        "norton-karczub-2003-appendix-4bc",
    }
    assert {key for key in PUBLISHED_FLUIDS if key.startswith("bies-")} == {
        "bies-2017-table-c1-fluids/air",
        "bies-2017-table-c1-fluids/fresh_water",
        "bies-2017-table-c1-fluids/sea_water",
    }
    airs = (ANNEX_A_AIR, EN_12354_AIR, PUBLISHED_AIR, SIMULATION_AIR)
    assert not any(state is air for state in PUBLISHED_FLUIDS.values() for air in airs)


def test_the_four_airs_of_the_tree_still_disagree_the_way_their_documents_do() -> None:
    """The reason the site gathers them, asserted rather than described.

    Four parts of this library propagate sound through four different airs,
    and each is right in its own document: substituting one for another would
    change a number a standard prints. A change that let them converge would
    be erasing a real disagreement between committees, so it fails here.
    """
    assert ANNEX_A_AIR.speed_of_sound == 345.86652
    assert EN_12354_AIR.speed_of_sound == 340.0
    assert PUBLISHED_AIR.speed_of_sound == 343.0
    assert SIMULATION_AIR.speed_of_sound == 343.0
    densities = {
        air.density
        for air in (ANNEX_A_AIR, EN_12354_AIR, PUBLISHED_AIR, SIMULATION_AIR)
    }
    assert len(densities) == 4


def test_the_two_books_that_print_air_at_twenty_degrees_agree_to_a_tenth() -> None:
    """Bies prints 1,206 kg/m3 where the absorber models use 1,205.

    The same air at the same temperature, rounded by two authors, and the gap
    is one part in a thousand. Worth asserting because it is the size of
    agreement a reader should expect between books, against the 1,7 per cent
    that separates the building standard's air from the metrology annex's.
    """
    bies = PUBLISHED_FLUIDS["bies-2017-table-c1-fluids/air"]
    assert bies.temperature_c == 20.0
    assert bies.density == pytest.approx(PUBLISHED_AIR.density, rel=1e-3)
    assert bies.speed_of_sound == PUBLISHED_AIR.speed_of_sound

    gap = abs(ANNEX_A_AIR.speed_of_sound - EN_12354_AIR.speed_of_sound)
    assert gap / EN_12354_AIR.speed_of_sound > 1.5e-2


# ---------------------------------------------------------------------------
# The catalogue as an object
# ---------------------------------------------------------------------------
def test_every_entry_is_a_fluid_that_says_where_it_came_from() -> None:
    for key, state in PUBLISHED_FLUIDS.items():
        assert isinstance(state, Fluid), key
        assert state.model.strip(), key


def test_the_catalogue_cannot_be_edited() -> None:
    with pytest.raises(TypeError):
        PUBLISHED_FLUIDS["en-12354-annex-a/air"] = SIMULATION_AIR  # type: ignore[index]


def test_the_package_imports_on_its_own() -> None:
    """``fluids`` reaches nothing that reaches back, checked in a fresh process.

    The catalogue is built at import time, so a domain import smuggled into it
    would make ``import phonometry.fluids`` fail on a partially initialised
    package. In this interpreter everything is already loaded and the failure
    would not show.
    """
    import subprocess
    import sys

    result = subprocess.run(  # noqa: S603 - fixed argument list, no shell
        [
            sys.executable,
            "-c",
            "import phonometry.fluids as f; print(len(f.PUBLISHED_FLUIDS))",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == str(len(PUBLISHED_FLUIDS))
