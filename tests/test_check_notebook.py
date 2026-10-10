#  Copyright (c) 2026. Jose Manuel Requena Plens
"""How ``scripts/check_notebook.py`` reads the outputs of the smoke notebook.

The script executes ``tests/notebooks/smoke.ipynb`` on an ipykernel, which
only the CI job ``notebook`` installs, and then reads each tagged cell's
outputs. The reading is plain Python over the output records nbformat keeps,
so these tests hand it outputs written for the purpose: for every tag, one
that passes and the ones it must refuse, and a notebook that lacks a tag.
"""

from __future__ import annotations

import base64
import pathlib
import sys
from typing import Any

import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_notebook as cn

_TABLE = '<div class="phonometry-record"><table><caption><strong>{}</strong>{}'
_PNG = base64.b64encode(b"\x89PNG\r\n\x1a\n" + bytes(16)).decode()


def _result(**data: str) -> dict[str, Any]:
    return {"output_type": "execute_result", "data": data, "metadata": {}}


def _stderr(text: str) -> dict[str, Any]:
    return {"output_type": "stream", "name": "stderr", "text": text}


#: For each tag, outputs its cell may put out.
_GOOD: dict[str, list[dict[str, Any]]] = {
    "import": [_result(**{"text/plain": "'4.0.0'"})],
    "rich-display": [
        _result(
            **{
                "text/html": _TABLE.format("OctaveFilterResult", ""),
                "text/plain": "OctaveFilterResult\n  levels  array 33 float64",
            }
        )
    ],
    "inline-plot": [
        {"output_type": "display_data", "data": {"image/png": _PNG}, "metadata": {}}
    ],
    "verdict": [
        _result(
            **{
                "text/html": _TABLE.format("LiningCuringCheck", "<span>FAIL</span>"),
                "text/plain": "LiningCuringCheck: FAIL\n  time_lag_days  1  d",
            }
        )
    ],
    "report": [_result(**{"text/plain": "b'%PDF-'"})],
    "warning": [
        _stderr("phonometry/x.py:1: PhonometryWarning: below the floor\n"),
        _result(**{"text/plain": "41.0"}),
    ],
}


def _cells(outputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [
        {"cell_type": "code", "metadata": {"tags": [tag]}, "outputs": cell}
        for tag, cell in outputs.items()
    ]


def test_a_notebook_that_showed_everything_passes_every_check() -> None:
    lines = cn.read(_cells(_GOOD))
    assert len(lines) == len(cn.CHECKS)
    assert lines[0] == "phonometry '4.0.0' imports in the kernel"
    assert lines[3] == "a verdict is displayed as FAIL"


@pytest.mark.parametrize(
    ("tag", "outputs", "message"),
    [
        ("import", [], "one displayed result expected, 0 found"),
        (
            "rich-display",
            [
                _result(
                    **{
                        "text/plain": "OctaveFilterResult(levels=array([1., 2.]))",
                    }
                )
            ],
            "the result was not displayed as its table",
        ),
        (
            "rich-display",
            [
                _result(
                    **{
                        "text/html": _TABLE.format("FilterDesign", ""),
                        "text/plain": "FilterDesign\n",
                    }
                )
            ],
            "the table does not name OctaveFilterResult",
        ),
        (
            "rich-display",
            [
                _result(
                    **{
                        "text/html": _TABLE.format("OctaveFilterResult", ""),
                        "text/plain": "OctaveFilterResult(levels=array([1., 2.]))",
                    }
                )
            ],
            "the plain text is not the table",
        ),
        ("inline-plot", [], "one inline PNG expected, 0 found"),
        (
            "inline-plot",
            [
                {
                    "output_type": "display_data",
                    "data": {"image/png": base64.b64encode(b"GIF89a").decode()},
                    "metadata": {},
                }
            ],
            "the inline figure is not a PNG",
        ),
        (
            "verdict",
            [
                _result(
                    **{
                        "text/html": _TABLE.format("LiningCuringCheck", ""),
                        "text/plain": "LiningCuringCheck: FAIL",
                    }
                )
            ],
            "the verdict does not show FAIL in its table",
        ),
        (
            "verdict",
            [
                _result(
                    **{
                        "text/html": _TABLE.format(
                            "LiningCuringCheck", "<span>FAIL</span>"
                        ),
                        "text/plain": "LiningCuringCheck(curing_time_days=2.9)",
                    }
                )
            ],
            "the plain text opens with",
        ),
        (
            "report",
            [_result(**{"text/plain": "b'<html'"})],
            "the fiche does not open as a PDF",
        ),
        ("warning", [_result(**{"text/plain": "41.0"})], "no PhonometryWarning"),
    ],
)
def test_each_check_refuses_an_output_that_is_not_what_its_tag_asks_for(
    tag: str, outputs: list[dict[str, Any]], message: str
) -> None:
    cells = _cells({**_GOOD, tag: outputs})
    with pytest.raises(cn.NotebookError, match=message):
        cn.read(cells)


def test_a_notebook_without_a_tagged_cell_is_refused() -> None:
    cells = _cells({tag: outputs for tag, outputs in _GOOD.items() if tag != "report"})
    with pytest.raises(cn.NotebookError, match="no cell tagged report"):
        cn.read(cells)
