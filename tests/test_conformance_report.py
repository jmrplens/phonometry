#  Copyright (c) 2026. Jose M. Requena-Plens
"""Smoke test for the CI numerical conformance harness.

Guarantees the registry runs end to end and that every registered
(standard, quantity) check passes on the current tree, so a regression in
any conformance-covered quantity fails the suite as well as the PR comment.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import conformance_report as cr  # noqa: E402


def test_registry_is_populated() -> None:
    assert len(cr.CHECKS) >= 26
    # Every domain has at least one check.
    assert len(cr._domains()) >= 6


def test_block_a_psychoacoustics_checks_registered() -> None:
    """The ECMA-418-2 and ISO 532-2/3 calibration checks are wired."""
    standards = {c.standard for c in cr.CHECKS}
    assert "ECMA-418-2:2025 Clause 5.1.8" in standards  # HMS loudness
    assert "ECMA-418-2:2025 Clause 6.2.8" in standards  # HMS tonality
    assert "ECMA-418-2:2025 Clause 7" in standards  # HMS roughness
    assert "ISO 532-2:2017 Clause 3.17 / Annex B.1" in standards
    assert "ISO 532-3:2023 Annex C.1" in standards


def test_filter_binding_detail_matches_library_margin() -> None:
    """The report re-derives the binding measured value and limit with the
    public ``class_limits``; guard that its class-1 margin never diverges from
    the authoritative ``verify_filter_class`` (single source of truth)."""
    from phonometry import OctaveFilterBank
    from phonometry.compliance import verify_filter_class

    for arch in cr._FILTER_ARCHS:
        fc = cr._filter_class(arch, 3)
        bank = OctaveFilterBank(
            48000, fraction=3, order=6, limits=[100, 10000], filter_type=arch
        )
        bands = verify_filter_class(bank)["bands"]
        lib_min = min(b["margin_class1_db"] for b in bands)
        assert fc.min_margin1 == pytest.approx(lib_min, abs=1e-9)
        # The binding measured value must sit on the reported side of the limit.
        if fc.bind_side in ("floor", "stop"):
            assert fc.bind_measured_db - fc.bind_limit_db == pytest.approx(
                lib_min, abs=1e-3
            )


@pytest.mark.parametrize("check", cr.CHECKS, ids=lambda c: f"{c.standard} :: {c.quantity}")
def test_every_check_passes(check: "cr.Check") -> None:
    outcome = check.run()
    assert outcome.passed, (
        f"{check.standard} / {check.quantity}: expected {outcome.expected}, "
        f"computed {outcome.computed} (delta {outcome.delta})"
    )


def test_render_markdown_is_well_formed() -> None:
    markdown, passed, total = cr.render_markdown()
    assert passed == total == len(cr.CHECKS)
    assert "## Numerical conformance report" in markdown
    assert "Numerical validation - filters &amp; weightings" in markdown
    assert f"{passed}/{total} conformance checks pass" in markdown
    # One table header per domain plus the two numerical-validation tables.
    assert markdown.count("|:---") >= len(cr._domains())
    # The redesigned filters table labels non-compliant architectures as
    # "By design" (not a scary "none") and shows the measured value vs limit.
    assert "By design" in markdown
    assert "none" not in markdown
    assert "Measured rel. atten." in markdown
    assert "Class-1 limit" in markdown
    # The weightings table separates the informational max deviation from the
    # binding-frequency compliance margin.
    assert "Max dev. from nominal (info)" in markdown
    assert "Binding freq" in markdown
