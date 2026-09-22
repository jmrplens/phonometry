#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The frozen-constant gate, on modules built for the purpose.

``scripts/check_frozen_constants.py`` walks the installed package, so its own
run only says the tree is clean today. These tests fix what it must catch:
the flat ``dict`` behind a ``Mapping`` annotation, the ``dict`` inside a
proxy, the writeable array, the container kept in a frozen dataclass, and the
exemption that outlives the name it excused.
"""

from __future__ import annotations

import pathlib
import sys
import types
from dataclasses import dataclass

import numpy as np

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_frozen_constants as cfc

from phonometry._internal.frozen import read_only


@dataclass(frozen=True)
class _Row:
    name: str
    bands: object


def _module(**values: object) -> list[tuple[str, types.ModuleType]]:
    module = types.ModuleType("phonometry.thing")
    for name, value in values.items():
        setattr(module, name, value)
    return [("phonometry.thing", module)]


def _paths(**values: object) -> list[str]:
    found, _ = cfc.offenders(iter(_module(**values)), exempt={})
    return sorted(offence.path for offence in found)


def test_a_dict_is_caught() -> None:
    """The defect the gate exists for: a published table that takes writes."""
    assert _paths(TABLE={"a": 1.0}) == ["TABLE"]


def test_a_proxy_over_plain_values_passes() -> None:
    assert _paths(TABLE=types.MappingProxyType({"a": (1.0, 2.0)})) == []


def test_a_dict_inside_a_proxy_is_caught() -> None:
    """The outer proxy hands the inner dictionary out by reference."""
    table = types.MappingProxyType({"day": {"a_u": 0.1}, "night": {"a_u": 0.2}})
    assert _paths(TABLE=table) == ["TABLE['day']", "TABLE['night']"]


def test_a_writeable_array_is_caught_and_a_read_only_one_passes() -> None:
    assert _paths(BANDS=np.array([125.0, 250.0])) == ["BANDS"]
    assert _paths(BANDS=read_only(np.array([125.0, 250.0]))) == []


def test_an_array_inside_a_proxy_is_caught() -> None:
    table = types.MappingProxyType({"20C": np.array([0.1, 0.3])})
    assert _paths(AIR=table) == ["AIR['20C']"]


def test_a_container_kept_by_a_frozen_dataclass_is_caught() -> None:
    """``frozen=True`` stops rebinding the field, not writing into it."""
    assert _paths(ROW=_Row("cork", {"125": 0.1})) == ["ROW.bands"]
    assert _paths(ROW=_Row("cork", (0.1, 0.2))) == []


def test_a_list_inside_a_tuple_is_caught() -> None:
    assert _paths(ROWS=((1.0, 2.0), [3.0])) == ["ROWS[1]"]


def test_code_and_private_names_are_not_values() -> None:
    assert _paths(helper=_Row.__repr__, _CACHE={}, Row=_Row) == []


def test_one_object_published_under_two_names_is_reported_once() -> None:
    shared = {"a": 1.0}
    assert _paths(TABLE=shared, ALIAS=shared) == ["TABLE"]


def test_an_exemption_silences_its_name_and_goes_stale_without_it() -> None:
    modules = _module(TABLE={"a": 1.0})
    found, stale = cfc.offenders(
        iter(modules), exempt={("phonometry.thing", "TABLE"): "why"}
    )
    assert found == []
    assert stale == []
    found, stale = cfc.offenders(
        iter(modules), exempt={("phonometry.thing", "GONE"): "why"}
    )
    assert [offence.path for offence in found] == ["TABLE"]
    assert stale == [("phonometry.thing", "GONE")]
