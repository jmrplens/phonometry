#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The tables of a caller's ANP export: what is read, how much, and what a cell holds.

``load_anp_database`` read every ``.csv`` of the directory with
``read_text``: a named pipe at a table's name kept it waiting for a writer, a
link to ``/dev/zero`` kept it reading without end, and a cell of ``nan`` or
``inf`` went into the NPD curves and the profiles as it was, to come out of an
event level as NaN with nothing to say where it came from. A table is now read
only from a regular file of at most 32 MiB, only when a keyword names it, and
every number in it is a finite one, refused otherwise with the table, the line
and the column.
"""

from __future__ import annotations

import re
import sys
from importlib.resources import files
from typing import TYPE_CHECKING

import pytest
from special_files import SPECIAL_KINDS, make_special, raised_within

from phonometry.aircraft import anp_fleet, load_anp_database

if TYPE_CHECKING:
    from pathlib import Path

#: The three tables an export must carry, as the package names them.
_REQUIRED = ("Aircraft.csv", "NPD_data.csv", "Default_fixed_point_profiles.csv")
#: The first SEL row of the bundled NPD table, line 14 of the file.
_SEL_ROW = "2CF650;SEL;A;10000.0;99.9;95.0;91.4;87.5;81.3;74.6;69.7;64.2;57.7;50.7"


def _export(root: Path, **replaced: str) -> Path:
    """The three tables of the bundled database in *root*, any of them replaced.

    :param replaced: Text for a table, keyed by its file name with the dots
        and the dashes turned into underscores (``NPD_data_csv``).
    """
    source = files("phonometry.aircraft.data.anp")
    for name in _REQUIRED:
        key = name.replace(".", "_")
        text = replaced.get(key, source.joinpath(name).read_text(encoding="utf-8"))
        (root / name).write_text(text, encoding="utf-8")
    return root


def _npd_with(cell: str) -> str:
    """The bundled NPD table with the first level of its first SEL row replaced."""
    text = files("phonometry.aircraft.data.anp").joinpath("NPD_data.csv").read_text()
    assert _SEL_ROW in text
    return text.replace(_SEL_ROW, _SEL_ROW.replace(";99.9;", f";{cell};", 1), 1)


@pytest.mark.parametrize("kind", SPECIAL_KINDS)
def test_a_table_that_is_no_regular_file_is_refused_before_it_is_opened(
    kind: str, tmp_path: Path
) -> None:
    """A pipe kept the read waiting, a device kept it reading without end."""
    root = _export(tmp_path)
    table = root / "NPD_data.csv"
    table.unlink()
    what = make_special(kind, table)
    error = raised_within(
        lambda: load_anp_database(root), pipe=table if kind == "pipe" else None
    )
    assert isinstance(error, ValueError)
    assert str(error) == (
        f"ANP table {table}: is {what}, and an ANP table is read only from a "
        "regular file"
    )


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX pipes")
def test_a_file_no_table_keyword_names_is_never_opened(tmp_path: Path) -> None:
    """Only the table a keyword resolves is read; a pipe beside them waits for no one."""
    root = _export(tmp_path)
    notes = root / "notes.csv"
    make_special("pipe", notes)
    error = raised_within(lambda: load_anp_database(root), pipe=notes)
    assert error is None


def test_a_table_past_32_mib_is_refused_before_it_is_read(tmp_path: Path) -> None:
    root = _export(tmp_path)
    table = root / "NPD_data.csv"
    with table.open("r+b") as handle:
        # A sparse file: the size is refused before a byte of it is read.
        handle.truncate(anp_fleet._MAX_TABLE_BYTES + 1)
    with pytest.raises(
        ValueError, match=r"is 33554433 bytes, and an ANP table is at most"
    ):
        load_anp_database(root)


def test_a_table_that_is_not_utf8_is_refused_naming_it(tmp_path: Path) -> None:
    root = _export(tmp_path)
    (root / "NPD_data.csv").write_bytes(b"NPD_ID;Noise Metric\n\xff\xfe;SEL\n")
    with pytest.raises(
        ValueError, match=r"NPD_data\.csv: is not UTF-8 text \(byte 20\)"
    ):
        load_anp_database(root)


@pytest.mark.parametrize("cell", ["nan", "NaN", "inf", "-Infinity", "1e999"])
def test_a_level_that_is_no_finite_number_is_refused_with_its_place(
    cell: str, tmp_path: Path
) -> None:
    """The level went into the NPD curve as it was, and every event level after it."""
    root = _export(tmp_path, NPD_data_csv=_npd_with(cell))
    refusal = (
        f"ANP table 'NPD_data.csv', line 14, column 'L_200ft': {cell!r} is not a "
        "finite number, and an ANP table holds finite numbers only"
    )
    with pytest.raises(ValueError, match=f"^{re.escape(refusal)}$"):
        load_anp_database(root)


def test_a_level_that_is_no_number_is_refused_with_its_place(tmp_path: Path) -> None:
    """It raised Python's own refusal, which named neither the table nor the line."""
    root = _export(tmp_path, NPD_data_csv=_npd_with("n/a"))
    with pytest.raises(
        ValueError,
        match=r"^ANP table 'NPD_data\.csv', line 14, column 'L_200ft': 'n/a' is not "
        r"a number$",
    ):
        load_anp_database(root)


def test_a_distance_heading_that_is_no_finite_number_is_refused(tmp_path: Path) -> None:
    """An infinite last distance passed the check that the distances increase."""
    npd = files("phonometry.aircraft.data.anp").joinpath("NPD_data.csv").read_text()
    root = _export(tmp_path, NPD_data_csv=npd.replace("L_25000ft", "L_infft", 1))
    with pytest.raises(
        ValueError,
        match=r"ANP table 'NPD_data\.csv', line 1, column 'L_infft': 'inf' is not "
        r"a finite number",
    ):
        load_anp_database(root)


def test_a_profile_point_that_is_no_finite_number_is_refused(tmp_path: Path) -> None:
    profiles = (
        files("phonometry.aircraft.data.anp")
        .joinpath("Default_fixed_point_profiles.csv")
        .read_text()
    )
    first = profiles.splitlines()[1]
    broken = first.replace(";6000.0;", ";nan;", 1)
    assert broken != first
    root = _export(
        tmp_path,
        Default_fixed_point_profiles_csv=profiles.replace(first, broken, 1),
    )
    with pytest.raises(
        ValueError,
        match=r"'Default_fixed_point_profiles\.csv', line 2, column 'Altitude AFE "
        r"\(ft\)': 'nan' is not a finite number",
    ):
        load_anp_database(root)


def test_an_aircraft_number_is_checked_when_the_table_is_read(tmp_path: Path) -> None:
    """It was read only when an aircraft was asked for, and int(nan) raised then."""
    aircraft = (
        files("phonometry.aircraft.data.anp").joinpath("Aircraft.csv").read_text()
    )
    first = aircraft.splitlines()[1]
    broken = first.replace(";Turboprop;2;", ";Turboprop;nan;", 1)
    assert broken != first
    root = _export(tmp_path, Aircraft_csv=aircraft.replace(first, broken, 1))
    with pytest.raises(
        ValueError,
        match=r"'Aircraft\.csv', line 2, column 'Number Of Engines': 'nan' is not a "
        r"finite number",
    ):
        load_anp_database(root)


def test_the_bundled_database_reads_as_it_did(tmp_path: Path) -> None:
    """The same tables from a caller's directory give the same database."""
    from_package = load_anp_database()
    from_directory = load_anp_database(_export(tmp_path))
    assert from_directory.aircraft_ids == from_package.aircraft_ids
    assert from_directory.aircraft("747100") == from_package.aircraft("747100")
    curves = from_directory.npd_curves("727200", "arrival", "SEL")
    expected = from_package.npd_curves("727200", "arrival", "SEL")
    assert (curves.levels == expected.levels).all()
