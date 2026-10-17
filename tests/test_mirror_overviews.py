#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The mirror checker answers for the anchors a page declares itself.

A page can pin a short, stable anchor with ``<a id="n4"></a>`` above a heading,
so a link survives a reworded heading. GitHub honours it; the checker must too,
or every link to such an anchor reads as broken.
"""

from __future__ import annotations

import pathlib
import sys

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import mirror_overviews as mo


def test_an_explicit_anchor_is_a_fragment(tmp_path: pathlib.Path) -> None:
    page = tmp_path / "page.md"
    page.write_text('<a id="n4"></a>\n### N4. A rule\n\ntext\n', encoding="utf-8")
    assert {"n4", "n4-a-rule"} <= mo._fragments(page)


def test_an_anchor_inside_a_fence_is_not_a_fragment(tmp_path: pathlib.Path) -> None:
    page = tmp_path / "page.md"
    page.write_text('# Title\n\n```html\n<a id="x1"></a>\n```\n', encoding="utf-8")
    assert "x1" not in mo._fragments(page)
