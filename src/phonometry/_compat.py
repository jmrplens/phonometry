#  Copyright (c) 2026. Jose M. Requena-Plens
"""Deprecated module-path aliases for the phonometry 3.2 package layout.

The 3.2 release grouped the flat top-level modules into domain subpackages
(``phonometry.building``, ``phonometry.underwater``, ...). Every public module
path that moved stays importable for one deprecation cycle through the shims
registered here: ``import phonometry.<old>`` and
``from phonometry.<old> import name`` keep working, warn with the standard
rename notice on attribute access, and delegate to the relocated module.
Pickles produced by 3.1 (whose classes carry old ``__module__`` paths) resolve
the same way. The table and this module are removed in phonometry 4.0.

This generalizes the former ``phonometry.loudness`` PEP 562 shim (that module
file is gone; its entry lives in the table below with its original 3.1 wording
preserved).
"""

from __future__ import annotations

import sys
import types
from importlib import import_module
from typing import Any

from ._internal.warnings import _warn_renamed

#: Old public module path -> relocated module path. One row per moved module.
_MOVED: dict[str, str] = {
    "phonometry.utils": "phonometry._internal.utils",
    "phonometry._warnings": "phonometry._internal.warnings",
    "phonometry.calibration": "phonometry.metrology.calibration",
    "phonometry.compliance": "phonometry.metrology.compliance",
    "phonometry.core": "phonometry.metrology.core",
    "phonometry.filter_design": "phonometry.metrology.filter_design",
    "phonometry.frequencies": "phonometry.metrology.frequencies",
    "phonometry.levels": "phonometry.metrology.levels",
    "phonometry.parametric_filters": "phonometry.metrology.parametric_filters",
    "phonometry.uncertainty": "phonometry.metrology.uncertainty",
    "phonometry.fluctuation_strength": "phonometry.psychoacoustics.fluctuation_strength",
    "phonometry.loudness_contours": "phonometry.psychoacoustics.loudness_contours",
    "phonometry.loudness_ecma": "phonometry.psychoacoustics.loudness_ecma",
    "phonometry.loudness_moore_glasberg": "phonometry.psychoacoustics.loudness_moore_glasberg",
    "phonometry.loudness_moore_glasberg_time": "phonometry.psychoacoustics.loudness_moore_glasberg_time",
    "phonometry.loudness_zwicker": "phonometry.psychoacoustics.loudness_zwicker",
    "phonometry.psychoacoustic_annoyance": "phonometry.psychoacoustics.psychoacoustic_annoyance",
    "phonometry.roughness_ecma": "phonometry.psychoacoustics.roughness_ecma",
    "phonometry.sharpness": "phonometry.psychoacoustics.sharpness",
    "phonometry.tonality": "phonometry.psychoacoustics.tonality",
    "phonometry.tonality_ecma": "phonometry.psychoacoustics.tonality_ecma",
    "phonometry.tone_audibility": "phonometry.psychoacoustics.tone_audibility",
    # <migrate:auto>
}

#: Entries whose deprecation predates 3.2 keep their original wording.
_SINCE: dict[str, str] = {
    "phonometry.loudness": "3.1",
}

#: Renames that were already shimmed before 3.2 (target differs from a plain
#: package move). ``phonometry.loudness`` predates the reorganization.
_MOVED["phonometry.loudness"] = "phonometry.psychoacoustics.loudness_zwicker"


def _make_shim(old: str, new: str) -> types.ModuleType:
    shim = types.ModuleType(old)
    shim.__doc__ = f"Deprecated alias of :mod:`{new}` (removed in phonometry 4.0)."

    def __getattr__(name: str) -> Any:  # noqa: N807  (module-level protocol)
        target = import_module(new)
        try:
            attr = getattr(target, name)
        except AttributeError:
            raise AttributeError(
                f"module {old!r} has no attribute {name!r}"
            ) from None
        _warn_renamed(
            f"the '{old}' module", f"'{new}'", since=_SINCE.get(old, "3.2")
        )
        return attr

    def __dir__() -> list[str]:  # noqa: N807
        return dir(import_module(new))

    shim.__getattr__ = __getattr__  # type: ignore[method-assign]
    shim.__dir__ = __dir__  # type: ignore[method-assign]
    return shim


def _install() -> None:
    package = sys.modules["phonometry"]
    for old, new in _MOVED.items():
        if old in sys.modules:  # pragma: no cover - double-import guard
            continue
        shim = _make_shim(old, new)
        sys.modules[old] = shim
        # `import phonometry.utils` also binds the attribute on the package;
        # mirror that so `phonometry.utils` resolves without the import.
        attr = old.rsplit(".", 1)[1]
        if not hasattr(package, attr):
            setattr(package, attr, shim)


_install()
