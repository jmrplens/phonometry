#  Copyright (c) 2026. Jose Manuel Requena Plens
"""``scripts/check_stub_metadata.py``, held to what it refuses in a built stub.

The script reads the files ``python -m build stub/`` writes, so every case here
writes a wheel and an sdist laid out the way setuptools lays them out and
changes one thing. The bad cases are the defects the stub has actually shipped
or nearly shipped: the uncapped pin 2.1.1 replaced, and the 2.2.0 files that
declared the licence only by a classifier and carried no licence text at all.
"""

from __future__ import annotations

import io
import pathlib
import sys
import tarfile
import zipfile

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_stub_metadata

_LICENSE = (_ROOT / "LICENSE").read_bytes()
_NAME = "pyoctaveband-2.2.1"

#: The metadata the fixed stub builds with, one header per line.
_GOOD_HEADERS = (
    "Metadata-Version: 2.4",
    "Name: PyOctaveBand",
    "Version: 2.2.1",
    "License-Expression: MIT",
    "License-File: LICENSE",
    "Requires-Dist: phonometry<4,>=3.0.0",
)

#: What PyOctaveBand 2.2.0 declared instead, read off the files on PyPI.
_CLASSIFIER_ONLY = (
    "Metadata-Version: 2.4",
    "Name: PyOctaveBand",
    "Version: 2.2.0",
    "Classifier: License :: OSI Approved :: MIT License",
    "Requires-Dist: phonometry<4,>=3.0.0",
)


def _metadata(headers: tuple[str, ...]) -> bytes:
    return ("\n".join(headers) + "\n\nThe long description.\n").encode()


def _write_wheel(
    dist: pathlib.Path, headers: tuple[str, ...], licence: bytes | None
) -> None:
    with zipfile.ZipFile(dist / f"{_NAME}-py3-none-any.whl", "w") as archive:
        archive.writestr("pyoctaveband/__init__.py", "")
        archive.writestr(f"{_NAME}.dist-info/METADATA", _metadata(headers))
        if licence is not None:
            archive.writestr(f"{_NAME}.dist-info/licenses/LICENSE", licence)


def _write_sdist(
    dist: pathlib.Path, headers: tuple[str, ...], licence: bytes | None
) -> None:
    members = {
        "PKG-INFO": _metadata(headers),
        "src/pyoctaveband/__init__.py": b"",
    }
    if licence is not None:
        members["LICENSE"] = licence
    with tarfile.open(dist / f"{_NAME}.tar.gz", "w:gz") as archive:
        for name, data in members.items():
            info = tarfile.TarInfo(f"{_NAME}/{name}")
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))


def _check(
    tmp_path: pathlib.Path,
    *,
    wheel: tuple[tuple[str, ...], bytes | None] = (_GOOD_HEADERS, _LICENSE),
    sdist: tuple[tuple[str, ...], bytes | None] = (_GOOD_HEADERS, _LICENSE),
    capsys: pytest.CaptureFixture[str],
) -> tuple[int, str]:
    _write_wheel(tmp_path, *wheel)
    _write_sdist(tmp_path, *sdist)
    code = check_stub_metadata.main(["--dist", str(tmp_path)])
    return code, capsys.readouterr().err


def _without(headers: tuple[str, ...], prefix: str) -> tuple[str, ...]:
    return tuple(line for line in headers if not line.startswith(prefix))


def _replaced(
    headers: tuple[str, ...], prefix: str, replacement: str
) -> tuple[str, ...]:
    return tuple(replacement if line.startswith(prefix) else line for line in headers)


def test_the_stub_as_it_now_builds_passes(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, errors = _check(tmp_path, capsys=capsys)
    assert (code, errors) == (0, "")


def test_the_published_2_2_0_files_are_refused_on_every_licence_count(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A classifier and no text, in the wheel and the sdist alike."""
    code, errors = _check(
        tmp_path,
        wheel=(_CLASSIFIER_ONLY, None),
        sdist=(_CLASSIFIER_ONLY, None),
        capsys=capsys,
    )
    assert code == 1
    for label in (f"{_NAME}-py3-none-any.whl", f"{_NAME}.tar.gz"):
        assert f"{label}: License-Expression is missing" in errors
        assert f"{label}: License-File is missing" in errors
    assert f"{_NAME}.dist-info/licenses/LICENSE is missing" in errors
    assert f"{_NAME}/LICENSE is missing" in errors


def test_another_licence_expression_is_refused(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    headers = _replaced(
        _GOOD_HEADERS, "License-Expression", "License-Expression: BSD-3-Clause"
    )
    code, errors = _check(tmp_path, wheel=(headers, _LICENSE), capsys=capsys)
    assert code == 1
    assert "License-Expression is ['BSD-3-Clause'], expected 'MIT'" in errors


def test_a_licence_file_left_undeclared_is_refused(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The text is there, but nothing in the metadata points at it."""
    headers = _without(_GOOD_HEADERS, "License-File")
    code, errors = _check(tmp_path, sdist=(headers, _LICENSE), capsys=capsys)
    assert code == 1
    assert f"{_NAME}.tar.gz: License-File is missing, expected ['LICENSE']" in errors


def test_a_declared_licence_file_the_wheel_lacks_is_refused(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Declared in the metadata and missing from where PEP 639 puts it."""
    code, errors = _check(tmp_path, wheel=(_GOOD_HEADERS, None), capsys=capsys)
    assert code == 1
    assert f"{_NAME}.dist-info/licenses/LICENSE is missing" in errors
    assert f"{_NAME}/LICENSE is missing" not in errors


def test_a_declared_licence_file_the_sdist_lacks_is_refused(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """At the root of the sdist, where a License-File path is resolved."""
    code, errors = _check(tmp_path, sdist=(_GOOD_HEADERS, None), capsys=capsys)
    assert code == 1
    assert f"{_NAME}/LICENSE is missing" in errors
    assert "licenses/LICENSE is missing" not in errors


def test_a_licence_file_with_another_text_is_refused(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A stale copy in stub/ ships a licence that is not the project's."""
    stale = _LICENSE.replace(b"2020-2026", b"2020-2025")
    assert stale != _LICENSE
    code, errors = _check(tmp_path, wheel=(_GOOD_HEADERS, stale), capsys=capsys)
    assert code == 1
    assert (
        f"{_NAME}.dist-info/licenses/LICENSE is not the repository's LICENSE" in errors
    )


def test_an_uncapped_pin_is_still_refused(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The check the script was written for survives the licence checks."""
    headers = _replaced(
        _GOOD_HEADERS, "Requires-Dist", "Requires-Dist: phonometry>=3.0.0"
    )
    code, errors = _check(tmp_path, wheel=(headers, _LICENSE), capsys=capsys)
    assert code == 1
    assert "admits phonometry 4.0.0 (the next major)" in errors


def test_an_empty_build_directory_is_refused(tmp_path: pathlib.Path) -> None:
    with pytest.raises(SystemExit, match="no built artifacts"):
        check_stub_metadata.main(["--dist", str(tmp_path)])
