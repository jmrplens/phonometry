#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A published catalogue joined with yours keeps its row class, for mypy too.

``PUBLISHED_POROUS | mine`` goes straight into a lookup's ``catalogue=``, and
the join is typed so that it is accepted there: the union of the two sides'
row classes, which for two catalogues of one class is that class. The
suite checks the join at run time; this file holds the typing, and it only
holds it because CI type checks every file in this directory alongside
``src`` and ``scripts``. A join typed back to a mapping of ``CatalogueRow``
still runs, and fails here.

The manufacturer here is fictitious, as in every example of the repository.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, assert_type

from phonometry import io, materials

_EXAMPLE: dict[str, Any] = {
    "schema": "phonometry-catalogue",
    "schema_version": 1,
    "catalogue": "example-foams",
    "row_type": "PorousMaterial",
    "about": "One foam from a fictitious data sheet.",
    "provenance": {
        "kind": "datasheet",
        "document": "Example foam data sheet",
        "publisher": "Example Acoustics Ltd",
        "version": "Rev. 2",
        "consulted": "2026-09-25",
    },
    "rows": [{"key": "grey", "name": "Foam", "variant": "grey", "porosity": 0.98}],
}


def test_a_join_either_way_round_is_a_mapping_of_the_row_class() -> None:
    mine = io.parse_catalogue(_EXAMPLE, row_type=materials.PorousMaterial)
    assert_type(mine, io.Catalogue[materials.PorousMaterial])

    both = materials.PUBLISHED_POROUS | mine
    assert_type(both, Mapping[str, materials.PorousMaterial])
    reversed_join = mine | materials.PUBLISHED_POROUS
    assert_type(reversed_join, Mapping[str, materials.PorousMaterial])

    found = materials.porous_materials_named("Foam", catalogue=both)
    assert_type(found, tuple[materials.PorousMaterial, ...])
    grey = mine["example-foams/grey"]
    assert found[-1] is grey
    first = materials.porous_materials_named("Foam", catalogue=reversed_join)[0]
    assert first is grey
