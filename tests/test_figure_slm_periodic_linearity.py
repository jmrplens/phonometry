#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The level linearity steps the periodic tests figure draws.

``slm_periodic_linearity`` draws the Clause 16 steps of IEC 61672-3:2013 as
the library reads them off the record of the periodic tests guide
(``figures.metrology._slm_periodic_verification``), and an inset with the
record short of its first 1 dB step. These tests hold that reading from the
print, from the guide and from the verdict.

The expected steps are derived here from the print, not from the record:
16.3 (BS EN 61672-3:2013, page 14) asks for "5 dB steps of increasing input
signal level from the starting point up to within 5 dB of the upper
boundary", "then at 1 dB steps of increasing input signal level up to, but
not including, the first indication of overload", and the same with
decreasing level down to the first indication of under-range. For the
guide's record (range 40 dB to 120 dB, starting point 94 dB, overload first
indicated at 123 dB, under-range at 37 dB) that is 99 to 119 in fives and 120
to 122 in ones on the way up, 89 to 44 in fives and 43 to 38 in ones on the
way down.
"""

from __future__ import annotations

import pathlib
import re
import sys
from typing import TYPE_CHECKING

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from figures import metrology as figures

if TYPE_CHECKING:
    from collections.abc import Sequence

    from phonometry.metrology import SoundLevelMeterPeriodicVerification

# The figure tooling is tied to the pinned figure stack its plates are drawn
# with, so the minimum-versions job deselects this module.
pytestmark = pytest.mark.pinned_stack

#: The guide whose record the figure draws, in its two languages.
_GUIDES = tuple(
    _ROOT / "site/src/content/docs" / prefix / "signals/metrology"
    "/sound-level-meter-periodic-tests.mdx"
    for prefix in ("", "es")
)

#: The steps of 16.3 for the guide's record, derived from the print above.
_RISING = (99, 104, 109, 114, 119, 120, 121, 122)
_FALLING = (89, 84, 79, 74, 69, 64, 59, 54, 49, 44, 43, 42, 41, 40, 39, 38)


def _record_field(page: str, name: str) -> list[float]:
    """The numbers a field of the guide's record is given, in order."""
    found = re.search(rf"\b{name}=(\[[^\]]*\]|[-\d.]+)", page)
    assert found is not None, name
    return [float(number) for number in re.findall(r"-?\d+(?:\.\d+)?", found[1])]


@pytest.fixture(scope="module")
def verification() -> SoundLevelMeterPeriodicVerification:
    return figures._slm_periodic_verification()


def _levels(values: Sequence[float] | None) -> list[float]:
    """The numbers of a record field the guide's record gives."""
    assert values is not None
    return [float(v) for v in values]


def test_the_figure_reads_the_steps_the_print_asks_for(
    verification: SoundLevelMeterPeriodicVerification,
) -> None:
    m = verification.measurements
    assert m.linearity_starting_level is not None
    rising, falling = figures._linearity_runs(
        _levels(m.linearity_levels), float(m.linearity_starting_level)
    )
    assert rising == _RISING
    assert falling == _FALLING


def test_the_record_holds_no_gap_in_clause_16(
    verification: SoundLevelMeterPeriodicVerification,
) -> None:
    assert [why for clause, why in verification.incomplete if clause == "16"] == []


def test_the_inset_is_the_gap_the_verdict_names(
    verification: SoundLevelMeterPeriodicVerification,
) -> None:
    before, left_out, after, verdict = figures._linearity_gap_record(verification)
    assert (before, left_out, after) == (119.0, 120.0, 121.0)
    short = [why for clause, why in verdict.incomplete if clause == "16"]
    assert len(short) == 1
    assert short[0].startswith("the steps go from 119 dB to 121 dB")


@pytest.mark.parametrize("guide", _GUIDES, ids=("en", "es"))
def test_the_figure_draws_the_record_the_guide_grades(
    guide: pathlib.Path, verification: SoundLevelMeterPeriodicVerification
) -> None:
    page = guide.read_text(encoding="utf-8")
    m = verification.measurements
    assert _record_field(page, "linearity_levels") == _levels(m.linearity_levels)
    assert _record_field(page, "linear_operating_range_db") == _levels(
        m.linear_operating_range_db
    )
    for name in (
        "linearity_starting_level",
        "linearity_overload_level",
        "linearity_under_range_level",
    ):
        assert _record_field(page, name) == [float(getattr(m, name))], name
