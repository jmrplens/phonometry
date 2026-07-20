#  Copyright (c) 2026. Jose M. Requena-Plens
"""The example-report generator keeps producing valid one-page fiches.

The rendered PDFs under ``.github/reports/`` are not byte-checked (their vector
plot differs by ~1 ULP across CPUs); this test only guards that
``scripts/generate_reports.py`` still runs and writes a valid single-page PDF
for every registered example.
"""

from __future__ import annotations

import importlib.util
import pathlib

import pytest

pytest.importorskip("reportlab")
pytest.importorskip("svglib")
pytest.importorskip("pypdf")

_SCRIPT = (
    pathlib.Path(__file__).resolve().parents[1] / "scripts" / "generate_reports.py"
)


def _load_generator():
    spec = importlib.util.spec_from_file_location("_generate_reports", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generate_reports_writes_one_page_pdfs(tmp_path) -> None:
    from pypdf import PdfReader

    module = _load_generator()
    written = module.generate_reports(str(tmp_path))
    assert written, "the generator registered no examples"
    for path in written:
        p = pathlib.Path(path)
        assert p.is_file() and p.stat().st_size > 0
        with open(p, "rb") as handle:
            assert handle.read(4) == b"%PDF"
        assert len(PdfReader(str(p)).pages) == 1
