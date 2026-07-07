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
    assert len(cr.CHECKS) >= 15
    # Every domain has at least one check.
    assert len(cr._domains()) >= 6


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
