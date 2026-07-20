#  Copyright (c) 2026. Jose M. Requena-Plens
"""The example-report generator keeps producing valid one-page fiches.

The rendered PDFs (and their PNG previews) under ``.github/reports/`` are not
byte-checked (their vector plot differs by ~1 ULP across CPUs, and the raster
inherits it); this test only guards that ``scripts/generate_reports.py`` still
runs and writes a valid single-page PDF plus a valid PNG preview for every
registered example.
"""

from __future__ import annotations

import importlib.util
import pathlib

import pytest

pytest.importorskip("reportlab")
pytest.importorskip("svglib")
pytest.importorskip("pypdf")
pytest.importorskip("pypdfium2")

_SCRIPT = (
    pathlib.Path(__file__).resolve().parents[1] / "scripts" / "generate_reports.py"
)


def _load_generator():
    spec = importlib.util.spec_from_file_location("_generate_reports", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


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


def test_generate_reports_writes_png_previews(tmp_path) -> None:
    module = _load_generator()
    written = module.generate_reports(str(tmp_path))
    for path in written:
        preview = pathlib.Path(module.preview_path_for(path))
        assert preview.suffix == ".png"
        assert preview.is_file() and preview.stat().st_size > 0
        with open(preview, "rb") as handle:
            assert handle.read(8) == _PNG_MAGIC
