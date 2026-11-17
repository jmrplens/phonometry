#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The anchors GitHub gives a hand-written page, as ``scripts/markdown_anchors.py`` reads them.

A page can pin a short, stable anchor with ``<a id="n4"></a>`` above a heading,
so a link survives a reworded heading. GitHub honours it; the reader must too,
or every link to such an anchor reads as broken.
"""

from __future__ import annotations

import pathlib
import sys

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import markdown_anchors


def test_an_explicit_anchor_is_a_fragment(tmp_path: pathlib.Path) -> None:
    page = tmp_path / "page.md"
    page.write_text('<a id="n4"></a>\n### N4. A rule\n\ntext\n', encoding="utf-8")
    assert {"n4", "n4-a-rule"} <= markdown_anchors.fragments(page)


def test_an_anchor_inside_a_fence_is_not_a_fragment(tmp_path: pathlib.Path) -> None:
    page = tmp_path / "page.md"
    page.write_text('# Title\n\n```html\n<a id="x1"></a>\n```\n', encoding="utf-8")
    assert "x1" not in markdown_anchors.fragments(page)


def test_a_repeated_heading_takes_the_next_number(tmp_path: pathlib.Path) -> None:
    page = tmp_path / "page.md"
    page.write_text("# A\n\n## Notes\n\n## Notes\n\n## Notes\n", encoding="utf-8")
    assert markdown_anchors.fragments(page) == {"a", "notes", "notes-1", "notes-2"}


def test_a_heading_that_is_a_link_anchors_on_its_label(tmp_path: pathlib.Path) -> None:
    page = tmp_path / "page.md"
    page.write_text(
        "## [Absorbers](i.md)\n\n## Report metadata (`ReportMetadata`)\n",
        encoding="utf-8",
    )
    assert markdown_anchors.fragments(page) == {
        "absorbers",
        "report-metadata-reportmetadata",
    }
