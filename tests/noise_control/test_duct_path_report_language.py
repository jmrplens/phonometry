#  Copyright (c) 2026. Jose Manuel Requena Plens

"""Every number the duct-path sheet writes by hand follows the sheet's language.

The room-criterion designation, the band headings, the verdict band and the
design target are assembled as text rather than through a localised table
cell, so a Spanish sheet keeps an English decimal point wherever one of them is
not handed the language. The NC family of ANSI/ASA S12.2-2019 Table 1 starts at
16 Hz, so a 31,5 Hz band on the sheet, or as the governing band of the
designation, is an ordinary case and not a contrived one.
"""

from __future__ import annotations

import numpy as np
import pytest

from phonometry._report.duct_path import (
    _band_header,
    _rating_designation,
    _rating_statement,
    _verdict,
)
from phonometry.noise_control.duct_path import DuctElement, DuctPathResult, duct_path
from phonometry.room import noise_criteria

_BANDS = np.array([31.5, 63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0])


def _interpolated_nc_at_31_5() -> noise_criteria.NCResult:
    """An NC-40 spectrum raised 10 dB at 31,5 Hz: an interpolated tangency there."""
    levels = noise_criteria.nc_curve(40.0).copy()
    levels[list(noise_criteria.OCTAVE_BANDS).index(31.5)] += 10.0
    rating = noise_criteria.noise_criterion(levels)
    assert rating.out_of_range is None
    assert rating.governing_frequency == pytest.approx(31.5)
    return rating


def _path(source_level: np.ndarray) -> DuctPathResult:
    return duct_path(
        _BANDS,
        source_level,
        [DuctElement("Duct, 6 m, 25 mm lining", 3.0, code="2")],
        room_effect=0.0,
        source_label="Fan",
        criterion="NC",
        target=30.0,
    )


def _nc_30_on_the_bands() -> np.ndarray:
    return noise_criteria.nc_curve(30.0)[np.isin(noise_criteria.OCTAVE_BANDS, _BANDS)]


def test_the_designation_reaches_spanish() -> None:
    rating = _interpolated_nc_at_31_5()
    assert _rating_designation(rating, language="es") == "NC-58,3 (31,5 Hz)"


def test_the_designation_is_unchanged_in_english() -> None:
    rating = _interpolated_nc_at_31_5()
    assert _rating_designation(rating) == "NC-58.3 (31.5 Hz)"
    assert _rating_designation(rating, language="en") == "NC-58.3 (31.5 Hz)"


def test_an_out_of_range_designation_reaches_spanish() -> None:
    # 30 dB over NC-30 at 31,5 Hz puts the spectrum above the whole family.
    result = _path(_nc_30_on_the_bands() + np.array([30.0, 5, 5, 5, 5, 5, 5, 5]))
    assert result.rating.out_of_range == "above"
    assert _rating_designation(result.rating, language="es") == ">NC-70 (31,5 Hz)"
    assert _rating_designation(result.rating) == ">NC-70 (31.5 Hz)"


def test_the_boxed_statement_hands_its_language_to_the_designation() -> None:
    # An interpolated in-family rating, so the designation carries a decimal.
    result = _path(np.array([84.0, 80.0, 76.0, 73.0, 71.0, 69.0, 65.0, 55.0]))
    spanish, _ = _rating_statement(result, "es")
    english, _ = _rating_statement(result, "en")
    assert spanish == "Criterio de recinto <b>NC-65,8 (1000 Hz)</b>"
    assert english == "Room criterion <b>NC-65.8 (1000 Hz)</b>"


def test_the_verdict_band_reaches_spanish() -> None:
    result = _path(_nc_30_on_the_bands() + np.array([30.0, 5, 5, 5, 5, 5, 5, 5]))
    spanish = _verdict(result, "es")
    english = _verdict(result, "en")
    assert spanish is not None
    assert english is not None
    assert spanish[0].endswith("a 31,5 Hz"), spanish
    assert english[0].endswith("at 31.5 Hz"), english


def test_the_band_headings_reach_spanish() -> None:
    assert _band_header(_BANDS, "es")[2:] == [
        "31,5",
        "63",
        "125",
        "250",
        "500",
        "1k",
        "2k",
        "4k",
    ]
    assert _band_header(_BANDS, "en")[2] == "31.5"
