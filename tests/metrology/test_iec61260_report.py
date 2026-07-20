#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Tests for the IEC 61260-1 filter-class-compliance report (``.report()`` -> PDF).

The report is a rendering feature, so these tests assert only structural facts:
``filter_class_compliance`` carries the bank data and agrees with
``verify_filter_class``; a class-1 bank renders a valid single-page COMPLIES
fiche; unknown engines are rejected; the required-class verdict renders both
ways; and a non-compliant bank renders its non-compliance fiche. The class
verification itself is validated against the standard's Table 1 elsewhere
(tests/metrology/test_compliance.py).
"""

from __future__ import annotations

import os
import pickle

import pytest

pytest.importorskip("reportlab")

from phonometry import (  # noqa: E402
    OctaveFilterBank,
    ReportMetadata,
    filter_class_compliance,
    verify_filter_class,
)

_PDF_MAGIC = b"%PDF"


def _class1_bank() -> OctaveFilterBank:
    """A default Butterworth octave bank that meets IEC 61260-1:2014 class 1."""
    return OctaveFilterBank(fs=48000, fraction=1, order=6, limits=[125, 4000])


def _assert_one_page(path: str) -> None:
    from pypdf import PdfReader

    with open(path, "rb") as handle:
        assert handle.read(4) == _PDF_MAGIC
    assert os.path.getsize(path) > 0
    assert len(PdfReader(path).pages) == 1


def test_filter_class_compliance_carries_bank_data() -> None:
    """The result packages the bank data and agrees with verify_filter_class."""
    bank = OctaveFilterBank(fs=48000, fraction=1, order=6, limits=[500, 2000])
    result = filter_class_compliance(bank)
    verdict = verify_filter_class(bank)

    assert result.overall_class == verdict["overall_class"]
    assert len(result.bands) == bank.num_bands
    assert len(result.sos) == bank.num_bands
    assert result.band_frequencies.shape == (bank.num_bands,)
    assert result.factors == tuple(int(f) for f in bank.factor)
    assert result.fs == float(bank.fs)
    assert result.fraction == int(bank.fraction)
    assert result.edition == "2014"
    # The per-band margins survive the packaging unchanged.
    for stored, computed in zip(result.bands, verdict["bands"], strict=True):
        assert stored["margin_class1_db"] == pytest.approx(
            computed["margin_class1_db"]
        )
    # Frozen and picklable (like the other result dataclasses).
    pickle.loads(pickle.dumps(result))


def test_class1_bank_reports_complies(tmp_path) -> None:
    """A class-1 bank renders a valid one-page COMPLIES fiche."""
    result = filter_class_compliance(_class1_bank())
    assert result.overall_class == 1
    out = tmp_path / "iec.pdf"
    returned = result.report(str(out))
    assert returned == str(out)
    _assert_one_page(str(out))


def test_1995_edition_reports_class0(tmp_path) -> None:
    """The 1995 edition keeps class 0; a high-order bank renders a Class 0 fiche."""
    bank = OctaveFilterBank(fs=48000, fraction=1, order=8, limits=[250, 4000])
    result = filter_class_compliance(bank, edition="1995")
    assert result.edition == "1995"
    assert result.overall_class == 0
    assert 0 in result.available_classes()  # class 0 only exists in the 1995 mask
    out = tmp_path / "iec1995.pdf"
    result.report(str(out), metadata=ReportMetadata(
        measurement_standard="IEC 61260:1995", required_class=0))
    _assert_one_page(str(out))


def test_full_metadata_renders_one_page(tmp_path) -> None:
    """A populated ReportMetadata renders a one-page filter-compliance fiche."""
    result = filter_class_compliance(_class1_bank())
    md = ReportMetadata(
        specimen="1/1-octave filter bank",
        client="Acoustic Test Client Ltd.",
        manufacturer="Instrument Works Inc.",
        test_room="Electroacoustics laboratory H1",
        measurement_standard="IEC 61260-1:2014",
        test_date="2026-07-20",
        laboratory="Phonometry Reference Laboratory",
        operator="J. M. Requena-Plens",
        report_id="PHN-2026-61260",
        required_class=1,
    )
    out = tmp_path / "meta.pdf"
    result.report(str(out), metadata=md)
    _assert_one_page(str(out))


def test_unknown_engine_rejected(tmp_path) -> None:
    """An unknown rendering engine raises ``ValueError``."""
    result = filter_class_compliance(_class1_bank())  # hoisted out of raises (S5778)
    out = str(tmp_path / "x.pdf")
    with pytest.raises(ValueError, match="engine"):
        result.report(out, engine="weasyprint")


def test_required_class_pass_and_fail_both_render(tmp_path) -> None:
    """A PASS (class 1 meets required 1) and FAIL (misses strict 0) both render."""
    result = filter_class_compliance(_class1_bank())
    assert result.overall_class == 1
    passing = tmp_path / "pass.pdf"
    failing = tmp_path / "fail.pdf"
    result.report(str(passing), metadata=ReportMetadata(required_class=1))
    result.report(str(failing), metadata=ReportMetadata(required_class=0))
    _assert_one_page(str(passing))
    _assert_one_page(str(failing))


def test_non_compliant_bank_renders(tmp_path) -> None:
    """A low-order bank that meets no class renders its non-compliance fiche."""
    bank = OctaveFilterBank(fs=48000, fraction=1, order=1, limits=[500, 2000])
    result = filter_class_compliance(bank)
    assert result.overall_class is None
    out = tmp_path / "noncompliant.pdf"
    result.report(str(out))
    _assert_one_page(str(out))
