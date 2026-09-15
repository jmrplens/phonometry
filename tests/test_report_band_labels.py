#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A Spanish fiche numbers its band column the way it numbers everything else.

The band centre that opens a row is a number, and on a Spanish sheet every
other number in that row already carried a decimal comma. The centre did not:
the helper that wrote it took no language at all, so ``31.5`` sat beside
``60,0`` in the same row of a rendered sheet, in the room-criterion fiche and
in the whole sound-power family, which shares one helper across ISO 3741,
ISO 3744, ISO 7849, ISO 9614, EN 12354-5, EN 15657 and the enclosure, silencer
and HVAC sheets.

A guard that indexes helpers which TAKE a language cannot see a helper that
never had one, which is why these read the rendered PDF instead: the text a
reader would copy out of the sheet.

The band labels are also read back as numbers in one place, the ISO 9614-3
table of reproducibility standard deviations. That path takes the centres from
``nominal_bands`` rather than parsing the printed label, and the last test is
what holds it there: a localised label is no longer a number ``float`` accepts,
and the column would have gone quietly to em dashes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from phonometry.emission import (
    sound_power_pressure,
    sound_power_reverberation,
)
from phonometry.room import noise_criterion

if TYPE_CHECKING:
    from pathlib import Path

pytest.importorskip("reportlab")
pytest.importorskip("pypdfium2")

_THIRDS = np.array(
    [
        25.0,
        31.5,
        40.0,
        50.0,
        63.0,
        80.0,
        100.0,
        125.0,
        160.0,
        200.0,
        250.0,
        315.0,
        400.0,
        500.0,
        630.0,
        800.0,
        1000.0,
    ]
)


def _text(path: Path) -> str:
    """The text of the first page, as a reader would copy it out."""
    import pypdfium2 as pdfium

    document = pdfium.PdfDocument(str(path))
    try:
        return document[0].get_textpage().get_text_range()
    finally:
        document.close()


def _room_criterion_sheet(tmp_path: Path, language: str) -> str:
    result = noise_criterion(
        [62.0, 60.0, 57.0, 54.0, 50.0, 47.0, 45.0, 43.0, 41.0, 39.0]
    )
    out = tmp_path / f"nc_{language}.pdf"
    result.report(str(out), language=language)
    return _text(out)


def _sound_power_sheet(tmp_path: Path, language: str) -> str:
    result = sound_power_reverberation(
        [70.0, 72.0, 74.0, 75.0, 73.0, 71.0, 68.0, 65.0, 60.0],
        2.0,
        volume=200.0,
        surface_area=240.0,
        frequencies=[31.5, 63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0],
        temperature_c=20.0,
        static_pressure_kpa=101.325,
    )
    out = tmp_path / f"sp_{language}.pdf"
    result.report(str(out), language=language)
    return _text(out)


def test_the_room_criterion_band_column_reaches_spanish(tmp_path: Path) -> None:
    """``31.5 60,0`` was one row of the rendered ANSI/ASA S12.2 sheet."""
    text = _room_criterion_sheet(tmp_path, "es")
    assert "31,5" in text
    assert "31.5" not in text


def test_the_room_criterion_band_column_is_unchanged_in_english(
    tmp_path: Path,
) -> None:
    text = _room_criterion_sheet(tmp_path, "en")
    assert "31.5" in text
    assert "31,5" not in text


def test_the_sound_power_band_column_reaches_spanish(tmp_path: Path) -> None:
    """One helper writes this column for nine sheets, so one test reaches them."""
    text = _sound_power_sheet(tmp_path, "es")
    assert "31,5" in text
    assert "31.5" not in text


def test_the_sound_power_band_column_is_unchanged_in_english(tmp_path: Path) -> None:
    text = _sound_power_sheet(tmp_path, "en")
    assert "31.5" in text
    assert "31,5" not in text


def test_a_result_without_band_frequencies_names_its_bands_in_spanish(
    tmp_path: Path,
) -> None:
    """A directly measured level has no centre to print, so it is numbered.

    That number was written ``Band 1`` on a Spanish sheet, in a column headed
    in Spanish.
    """
    levels = np.tile(np.array([80.0, 100.0, 90.0]), (10, 1))
    result = sound_power_pressure(levels, surface="hemisphere", radius=4.0)
    out = tmp_path / "bands_es.pdf"
    result.report(str(out), language="es")
    text = _text(out)
    assert "Banda 1" in text
    assert "Band 1" not in text


def test_a_result_without_band_frequencies_is_unchanged_in_english(
    tmp_path: Path,
) -> None:
    levels = np.tile(np.array([80.0, 100.0, 90.0]), (10, 1))
    result = sound_power_pressure(levels, surface="hemisphere", radius=4.0)
    out = tmp_path / "bands_en.pdf"
    result.report(str(out), language="en")
    assert "Band 1" in _text(out)


def test_the_uncertainty_column_reads_the_centres_and_not_the_labels() -> None:
    """The ISO 9614-3 standard deviations are looked up by band centre.

    Reading them back off the printed label would work in English and return
    nothing but em dashes in Spanish, because ``float("31,5")`` raises and the
    lookup swallows it as a band outside Table 1.
    """
    from phonometry._report._sound_power_fiche import band_labels, nominal_bands

    centres, fraction = nominal_bands(_THIRDS)
    assert centres is not None
    assert fraction == 3  # noqa: PLR2004 - the one-third-octave designator
    assert all(isinstance(float(centre), float) for centre in centres)
    spanish, _ = band_labels(_THIRDS, _THIRDS.size, "es")
    assert "31,5" in spanish
    with pytest.raises(ValueError, match="could not convert"):
        float(spanish[spanish.index("31,5")])
