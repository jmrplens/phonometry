#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The gate on public records a notebook would show as their raw ``repr``.

``scripts/check_record_display.py`` reads every public record of the package
and asks that it inherit ``RichDisplay``, itself or through a class of the
package (``OwnsArrays``, for one, while it extends it), and leave the two display
methods to it; a named tuple defines them as calls to the mechanism. Its own
run only says the tree is clean today; these tests fix what it must catch,
on small packages written for the purpose, and what it must let through.
"""

from __future__ import annotations

import pathlib
import sys
import textwrap

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import ast_scan
import check_record_display as crd

#: The mechanism, as the package spells it.
_DISPLAY = """
class RichDisplay:
    def _repr_html_(self):
        return record_html(self)

    def _repr_pretty_(self, printer, cycle):
        record_pretty(self, printer, cycle)

def record_html(record):
    return ""

def record_pretty(record, printer, cycle):
    pass
"""

_FROZEN = """
from .display import RichDisplay

class OwnsArrays(RichDisplay):
    pass
"""


def _package(
    tmp_path: pathlib.Path, *, frozen: str = _FROZEN, **modules: str
) -> pathlib.Path:
    """Write ``pkg`` with the mechanism and *modules*, and return it."""
    root = tmp_path / "pkg"
    files = {
        "__init__.py": "",
        "_internal/__init__.py": "",
        "_internal/display.py": _DISPLAY,
        "_internal/frozen.py": frozen,
        **{f"{name}.py": source for name, source in modules.items()},
    }
    for name, source in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(source), encoding="utf-8")
    return root


def _refused(
    tmp_path: pathlib.Path, *, frozen: str = _FROZEN, **modules: str
) -> dict[str, str]:
    """The public records refused, by qualified name, with the reason."""
    root = _package(tmp_path, frozen=frozen, **modules)
    found = crd.records_without_display(sorted(root.rglob("*.py")), root)
    return {finding.function: finding.sink for finding in found}


def test_a_record_without_the_mechanism_is_refused(tmp_path: pathlib.Path) -> None:
    refused = _refused(
        tmp_path,
        results="""
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class Bare:
            level_db: float
        """,
    )
    assert refused == {"Bare": "Bare does not inherit RichDisplay"}


def test_owns_arrays_gives_the_table_only_while_it_extends_the_mechanism(
    tmp_path: pathlib.Path,
) -> None:
    """``OwnsArrays`` counts for what it extends, not for its name."""
    results = """
    from dataclasses import dataclass

    import numpy as np

    from ._internal.frozen import OwnsArrays

    @dataclass(frozen=True)
    class Copies(OwnsArrays):
        levels_db: np.ndarray
    """
    assert _refused(tmp_path / "a", results=results) == {}
    refused = _refused(
        tmp_path / "b", frozen="class OwnsArrays:\n    pass\n", results=results
    )
    assert refused == {"Copies": "Copies does not inherit RichDisplay"}


def test_every_way_of_inheriting_the_mechanism_is_accepted(
    tmp_path: pathlib.Path,
) -> None:
    refused = _refused(
        tmp_path,
        results="""
        from dataclasses import dataclass

        import numpy as np

        from ._internal.display import RichDisplay
        from ._internal.frozen import OwnsArrays

        class _Drawable(RichDisplay):
            pass

        @dataclass(frozen=True)
        class Direct(RichDisplay):
            level_db: float

        @dataclass(frozen=True)
        class Copies(OwnsArrays):
            levels_db: np.ndarray

        @dataclass(frozen=True)
        class ThroughAPlainBase(_Drawable):
            depth_m: float

        @dataclass(frozen=True)
        class ThroughARecord(Direct):
            extra: float
        """,
    )
    assert refused == {}


def test_a_record_with_a_display_of_its_own_is_refused(tmp_path: pathlib.Path) -> None:
    refused = _refused(
        tmp_path,
        results="""
        from dataclasses import dataclass

        from ._internal.display import RichDisplay

        @dataclass(frozen=True)
        class Own(RichDisplay):
            level_db: float

            def _repr_html_(self):
                return "<p>mine</p>"
        """,
    )
    assert refused == {"Own": "Own defines its own _repr_html_"}


def test_a_named_tuple_must_call_the_mechanism(tmp_path: pathlib.Path) -> None:
    refused = _refused(
        tmp_path,
        results="""
        from typing import NamedTuple

        from ._internal.display import record_html, record_pretty

        class Bare(NamedTuple):
            k1: float

        class Half(NamedTuple):
            k1: float

            def _repr_html_(self):
                return record_html(self)

        class Own(NamedTuple):
            k1: float

            def _repr_html_(self):
                return "<p>mine</p>"

            def _repr_pretty_(self, printer, cycle):
                record_pretty(self, printer, cycle)

        class Shared(NamedTuple):
            k1: float

            def _repr_html_(self):
                return record_html(self)

            def _repr_pretty_(self, printer, cycle):
                record_pretty(self, printer, cycle)
        """,
    )
    assert refused == {
        "Bare": (
            "Bare is a named tuple whose _repr_html_ and _repr_pretty_ are not "
            "the mechanism's"
        ),
        "Half": "Half is a named tuple whose _repr_pretty_ is not the mechanism's",
        "Own": "Own is a named tuple whose _repr_html_ is not the mechanism's",
    }


def test_a_private_record_is_held_only_once_a_public_module_lists_it(
    tmp_path: pathlib.Path,
) -> None:
    source = """
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class Hidden:
        level_db: float
    """
    assert _refused(tmp_path / "a", _results=source) == {}
    exported = {
        "_results": source,
        "public": 'from ._results import Hidden\n__all__ = ["Hidden"]\n',
    }
    assert set(_refused(tmp_path / "b", **exported)) == {"Hidden"}


def test_an_exemption_silences_its_class_and_goes_stale_without_it(
    tmp_path: pathlib.Path,
) -> None:
    root = _package(
        tmp_path,
        results="""
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class Bare:
            level_db: float
        """,
    )
    found = crd.records_without_display(sorted(root.rglob("*.py")), root)
    key = (found[0].path, "Bare")
    left, stale = ast_scan.exempted(found, {key: "reason"})
    assert (left, stale) == ([], [])
    left, stale = ast_scan.exempted([], {key: "reason"})
    assert stale == [key]


def test_the_package_shows_every_public_record_as_a_table() -> None:
    files = sorted(crd.SOURCE.rglob("*.py"))
    assert crd.records_without_display(files, crd.SOURCE) == []
    assert crd.EXEMPT == {}
