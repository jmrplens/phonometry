#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The scripts the release workflow runs, held to what each one promises.

A release cannot be rehearsed against PyPI twice with the same version, so the
checks it runs on the way have to be right before they are needed: the notes
come from the changelog section and nowhere else, a built file the package is
missing stops the release, so does a built file that does not declare the
licence or carry its text, the SBOM names what ``pip install phonometry``
resolves and is one the SBOM attestation accepts, and the package the
verification imports is the installed wheel.
The build itself gives the same bytes on every Linux and macOS machine and
every day, and refuses Windows: the sdist keeps nothing of the builder's
clock, user or umask, the wheel is built from it, a setuptools plugin of
another package or a checkout that is not the commit stops it, a rebuild is
compared file by file with the checksum file or with PyPI, and every failure
it expects ends as one annotation rather than a traceback. Every file the
sdist carries from the checkout is one a checkout writes with LF whatever
the cloner's line-ending settings.
"""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
import pathlib
import re
import struct
import subprocess
import sys
import tarfile
import urllib.error
import zipfile
from importlib import metadata
from typing import Any

import child_process
import pytest
from special_files import SPECIAL_KINDS, make_special, raised_within

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import build_release
import check_installed_package
import check_release_artifacts as artifacts
import release_notes
import release_sbom

_CHANGELOG = """# Changelog

## [Unreleased]

### Added

- **Something not released yet.** Text.

## [2.0.0] - 2026-10-20

What this release is about, in one paragraph.

### Added

- **A first feature that has a title long enough to wrap onto the
  next line of the file.** Its description.
- **A second feature.** Its description,
  over two lines.

### Fixed

- **A fix.** Its description.

### Added

- **A feature merged later.** Its description.

## [1.0.0] - 2026-01-01

### Added

- **The first release.** Text.
"""


# ==========================================================================
# Release notes
# ==========================================================================
def test_the_section_of_a_version_is_its_text_between_two_headings() -> None:
    body = release_notes.section(_CHANGELOG, "2.0.0")
    assert body.startswith("What this release is about")
    assert "A feature merged later" in body
    assert "The first release" not in body
    assert "Something not released yet" not in body


def test_the_last_section_runs_to_the_end_of_the_file() -> None:
    assert release_notes.section(_CHANGELOG, "1.0.0").endswith("Text.")


def test_a_version_without_a_section_is_refused() -> None:
    with pytest.raises(KeyError, match=r"3\.0\.0"):
        release_notes.section(_CHANGELOG, "3.0.0")


def test_an_undated_heading_is_refused() -> None:
    with pytest.raises(ValueError, match="carries no release date"):
        release_notes.section(_CHANGELOG, "Unreleased")


def test_an_empty_section_is_refused() -> None:
    text = "## [2.0.0] - 2026-10-20\n\n## [1.0.0] - 2026-01-01\n\nText.\n"
    with pytest.raises(ValueError, match="is empty"):
        release_notes.section(text, "2.0.0")


def test_the_summary_keeps_every_title_once_under_its_heading() -> None:
    summary = release_notes.summary(release_notes.section(_CHANGELOG, "2.0.0"))
    assert summary.startswith("What this release is about")
    assert summary.count("### Added") == 1
    assert (
        "- A first feature that has a title long enough to wrap onto the next line of the file."
        in summary
    )
    assert "- A second feature." in summary
    assert "- A feature merged later." in summary
    assert summary.index("### Added") < summary.index("### Fixed")
    assert "Its description" not in summary


def test_a_section_that_fits_is_published_whole() -> None:
    notes = release_notes.notes(_CHANGELOG, "2.0.0")
    assert "Its description,\n  over two lines." in notes
    assert notes.rstrip().endswith(
        "(https://github.com/jmrplens/phonometry/blob/v2.0.0/CHANGELOG.md)."
    )


def test_a_section_too_long_for_a_release_is_published_as_its_titles() -> None:
    body = release_notes.section(_CHANGELOG, "2.0.0")
    limit = len(release_notes.summary(body)) + 1
    assert limit < len(body)
    notes = release_notes.notes(_CHANGELOG, "2.0.0", limit=limit)
    assert "Its description" not in notes
    assert "- A second feature." in notes
    assert "each one is described in full in the [changelog]" in notes


def test_a_summary_still_too_long_is_cut_at_a_whole_line() -> None:
    notes = release_notes.notes(_CHANGELOG, "2.0.0", limit=60)
    assert "\n- ...\n" in notes
    assert notes.endswith("CHANGELOG.md).\n")


def test_the_notes_are_written_and_a_missing_section_fails_the_preflight(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(_CHANGELOG, encoding="utf-8")
    out = tmp_path / "notes.md"
    assert (
        release_notes.main(
            ["--version", "2.0.0", "--changelog", str(changelog), "--output", str(out)]
        )
        == 0
    )
    assert out.read_text(encoding="utf-8").startswith("What this release is about")
    assert (
        release_notes.main(
            ["--version", "3.0.0", "--changelog", str(changelog), "--output", str(out)]
        )
        == 1
    )
    assert "has no section '## [3.0.0] - <date>'" in capsys.readouterr().err


# ==========================================================================
# The built files against git
# ==========================================================================
_TRACKED = [
    "phonometry/__init__.py",
    "phonometry/py.typed",
    "phonometry/building/data/ashrae-2019-table-40.json",
]

#: The licence text the built files carry: the repository's.
_LICENSE = (_ROOT / "LICENSE").read_bytes()

#: The licence headers setuptools writes from ``pyproject.toml``.
_LICENSE_HEADERS = "License-Expression: MIT\nLicense-File: LICENSE\n"


def _metadata(version: str, license_headers: str) -> str:
    return f"Metadata-Version: 2.4\nName: phonometry\nVersion: {version}\n{license_headers}"


def _wheel(
    path: pathlib.Path,
    version: str,
    names: list[str],
    *,
    metadata_version: str | None = None,
    license_headers: str = _LICENSE_HEADERS,
    license_text: bytes | None = _LICENSE,
) -> None:
    dist_info = f"phonometry-{version}.dist-info/"
    with zipfile.ZipFile(path, "w") as archive:
        for name in names:
            archive.writestr(name, "x")
        archive.writestr(
            f"{dist_info}METADATA",
            _metadata(metadata_version or version, license_headers),
        )
        if license_text is not None:
            archive.writestr(f"{dist_info}licenses/LICENSE", license_text)


def _sdist(
    path: pathlib.Path,
    version: str,
    names: list[str],
    *,
    license_headers: str = _LICENSE_HEADERS,
) -> None:
    top = f"phonometry-{version}/"
    with tarfile.open(path, "w:gz") as archive:
        for name in names:
            if name == "PKG-INFO":
                data = _metadata(version, license_headers).encode()
            elif name == "LICENSE":
                data = _LICENSE
            else:
                data = b"x"
            info = tarfile.TarInfo(top + name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))


def _good_dist(tmp_path: pathlib.Path, version: str = "2.0.0") -> pathlib.Path:
    dist = tmp_path / "dist"
    dist.mkdir()
    _wheel(dist / f"phonometry-{version}-py3-none-any.whl", version, _TRACKED)
    _sdist(
        dist / f"phonometry-{version}.tar.gz",
        version,
        [
            "PKG-INFO",
            *artifacts.SDIST_SUPPORT,
            *artifacts.LICENSE_FILES,
            *(f"src/{path}" for path in _TRACKED),
        ],
    )
    return dist


@pytest.mark.git_checkout
def test_a_build_that_holds_the_package_passes(tmp_path: pathlib.Path) -> None:
    assert artifacts.dist_problems(_good_dist(tmp_path), "2.0.0", _TRACKED) == []


def test_a_data_file_the_wheel_left_behind_is_reported(tmp_path: pathlib.Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    _wheel(dist / "phonometry-2.0.0-py3-none-any.whl", "2.0.0", _TRACKED[:2])
    assert artifacts.wheel_problems(
        dist / "phonometry-2.0.0-py3-none-any.whl", "2.0.0", _TRACKED
    ) == ["the wheel lacks phonometry/building/data/ashrae-2019-table-40.json"]


def test_a_file_git_does_not_track_is_reported_in_the_wheel(
    tmp_path: pathlib.Path,
) -> None:
    wheel = tmp_path / "phonometry-2.0.0-py3-none-any.whl"
    _wheel(
        wheel, "2.0.0", [*_TRACKED, "tests/test_x.py", "phonometry/__pycache__/x.pyc"]
    )
    problems = artifacts.wheel_problems(wheel, "2.0.0", _TRACKED)
    assert len(problems) == 2
    assert all("which git does not track" in problem for problem in problems)


def test_a_file_git_does_not_track_is_reported_in_the_sdist(
    tmp_path: pathlib.Path,
) -> None:
    """setuptools packs a test module or a module an ignore rule hides all the same.

    What it writes itself, ``PKG-INFO``, ``setup.cfg`` and the ``.egg-info``
    directory, is no checkout's and passes.
    """
    root = _repository(
        tmp_path,
        {"pyproject.toml": "", "src/phonometry/__init__.py": "", "tests/test_a.py": ""},
    )
    sdist = tmp_path / "phonometry-2.0.0.tar.gz"
    _sdist(
        sdist,
        "2.0.0",
        [
            "PKG-INFO",
            "setup.cfg",
            "pyproject.toml",
            "src/phonometry/__init__.py",
            "src/phonometry.egg-info/SOURCES.txt",
            "tests/test_a.py",
            "tests/test_local.py",
            "src/phonometry/__pycache__/x.cpython-313.pyc",
        ],
    )
    assert artifacts.untracked_sdist_problems(sdist, "2.0.0", root) == [
        "the sdist carries src/phonometry/__pycache__/x.cpython-313.pyc, "
        "which git does not track",
        "the sdist carries tests/test_local.py, which git does not track",
    ]


@pytest.mark.git_checkout
@pytest.mark.parametrize("member", ["tests/test_packaging.py", "setup.py"])
def test_a_file_setuptools_packs_by_default_is_reported(
    tmp_path: pathlib.Path, member: str
) -> None:
    """setuptools packs the top-level ``tests/test*.py`` and ``setup.py`` by default.

    Without the conftest and the helpers they import, an unpacked sdist could
    not even collect the test modules, and a ``setup.py`` would change how the
    wheel is built without ``SDIST_SUPPORT`` naming it. Either one is a file
    git tracks, so ``untracked_sdist_problems`` does not see it and only this
    check stops it.
    """
    dist = _good_dist(tmp_path)
    sdist = dist / "phonometry-2.0.0.tar.gz"
    _sdist(
        sdist,
        "2.0.0",
        [
            "PKG-INFO",
            *artifacts.SDIST_SUPPORT,
            *artifacts.LICENSE_FILES,
            *(f"src/{path}" for path in _TRACKED),
            "README.md",
            member,
        ],
    )
    problem = (
        f"the sdist carries {member}, which is neither the package nor a file "
        "building it needs"
    )
    assert artifacts.stray_sdist_problems(sdist, "2.0.0") == [problem]
    assert problem in artifacts.dist_problems(dist, "2.0.0", _TRACKED)


def test_a_wheel_of_another_version_is_reported(tmp_path: pathlib.Path) -> None:
    wheel = tmp_path / "phonometry-2.0.0-py3-none-any.whl"
    _wheel(wheel, "2.0.0", _TRACKED, metadata_version="2.0.0rc1")
    assert artifacts.wheel_problems(wheel, "2.0.0", _TRACKED) == [
        "the wheel's METADATA says version 2.0.0rc1, not 2.0.0"
    ]


def test_an_sdist_that_cannot_rebuild_the_wheel_is_reported(
    tmp_path: pathlib.Path,
) -> None:
    sdist = tmp_path / "phonometry-2.0.0.tar.gz"
    _sdist(
        sdist,
        "2.0.0",
        [
            "PKG-INFO",
            "pyproject.toml",
            "LICENSE",
            "README_PYPI.md",
            "src/phonometry/__init__.py",
        ],
    )
    assert artifacts.sdist_problems(sdist, "2.0.0", _TRACKED) == [
        "the sdist lacks phonometry-2.0.0/VERSION",
        "the sdist lacks phonometry-2.0.0/src/phonometry/py.typed",
        "the sdist lacks phonometry-2.0.0/src/phonometry/building/data/ashrae-2019-table-40.json",
    ]


@pytest.mark.parametrize(
    ("license_headers", "license_text", "expected"),
    [
        pytest.param(
            "License-File: LICENSE\n",
            _LICENSE,
            "License-Expression is missing, expected 'MIT'. "
            'Declare license = "MIT" in pyproject.toml.',
            id="no-expression",
        ),
        pytest.param(
            "License-Expression: Apache-2.0\nLicense-File: LICENSE\n",
            _LICENSE,
            "License-Expression is ['Apache-2.0'], expected 'MIT'.",
            id="another-expression",
        ),
        pytest.param(
            "License-Expression: MIT\n",
            _LICENSE,
            "License-File is missing, expected ['LICENSE'].",
            id="no-license-file",
        ),
        pytest.param(
            _LICENSE_HEADERS,
            None,
            "phonometry-2.0.0.dist-info/licenses/LICENSE is missing.",
            id="no-license-text",
        ),
    ],
)
def test_a_wheel_that_does_not_declare_or_carry_the_licence_is_reported(
    tmp_path: pathlib.Path,
    license_headers: str,
    license_text: bytes | None,
    expected: str,
) -> None:
    """What PyOctaveBand 2.2.0 shipped, one part at a time, in phonometry's wheel.

    Each can happen to phonometry. A build of this repository without
    ``license = "MIT"`` in ``pyproject.toml`` declares no expression, and one
    with ``license-files = []`` declares no licence file and carries none;
    setuptools builds both without a word.
    """
    wheel = tmp_path / "phonometry-2.0.0-py3-none-any.whl"
    _wheel(
        wheel,
        "2.0.0",
        _TRACKED,
        license_headers=license_headers,
        license_text=license_text,
    )
    problems = artifacts.wheel_problems(wheel, "2.0.0", _TRACKED)
    assert len(problems) == 1, problems
    assert problems[0].startswith(f"{wheel.name}: ")
    assert expected in problems[0]


@pytest.mark.parametrize(
    ("license_headers", "names", "expected"),
    [
        pytest.param(
            "License-File: LICENSE\n",
            ["LICENSE"],
            "License-Expression is missing, expected 'MIT'.",
            id="no-expression",
        ),
        pytest.param(
            "License-Expression: MIT\n",
            ["LICENSE"],
            "License-File is missing, expected ['LICENSE'].",
            id="no-license-file",
        ),
        pytest.param(
            _LICENSE_HEADERS,
            [],
            "phonometry-2.0.0/LICENSE is missing.",
            id="no-license-text",
        ),
    ],
)
def test_an_sdist_that_does_not_declare_or_carry_the_licence_is_reported(
    tmp_path: pathlib.Path,
    license_headers: str,
    names: list[str],
    expected: str,
) -> None:
    sdist = tmp_path / "phonometry-2.0.0.tar.gz"
    _sdist(
        sdist,
        "2.0.0",
        [
            "PKG-INFO",
            *artifacts.SDIST_SUPPORT,
            *names,
            *(f"src/{path}" for path in _TRACKED),
        ],
        license_headers=license_headers,
    )
    problems = artifacts.sdist_problems(sdist, "2.0.0", _TRACKED)
    assert len(problems) == 1, problems
    assert problems[0].startswith(f"{sdist.name}: ")
    assert expected in problems[0]


@pytest.mark.git_checkout
def test_a_stray_file_in_the_build_directory_is_reported(
    tmp_path: pathlib.Path,
) -> None:
    dist = _good_dist(tmp_path)
    (dist / "phonometry-1.9.0-py3-none-any.whl").write_bytes(b"")
    problems = artifacts.dist_problems(dist, "2.0.0", _TRACKED)
    assert len(problems) == 1
    assert (
        "not exactly phonometry-2.0.0.tar.gz and phonometry-2.0.0-py3-none-any.whl"
        in problems[0]
    )


@pytest.mark.parametrize("kind", SPECIAL_KINDS)
def test_a_build_file_that_is_no_regular_file_is_reported(
    tmp_path: pathlib.Path, kind: str
) -> None:
    """At the sdist's name, a pipe, a device or a directory passed as no problem.

    The listing of the directory matched, and the sdist's checks, which run
    on a regular file, were skipped, so the check said the release was right.
    """
    dist = _good_dist(tmp_path)
    sdist = dist / "phonometry-2.0.0.tar.gz"
    sdist.unlink()
    make_special(kind, sdist)
    assert artifacts.dist_problems(dist, "2.0.0", _TRACKED) == [
        f"{dist} holds {sdist.name}, which is not a regular file"
    ]


@pytest.mark.git_checkout
def test_git_tracks_the_package_data_the_wheel_has_to_carry() -> None:
    tracked = artifacts.tracked_package_files()
    assert "phonometry/__init__.py" in tracked
    assert "phonometry/py.typed" in tracked
    assert all(path.startswith("phonometry/") for path in tracked)


# ==========================================================================
# The SBOM
# ==========================================================================
def _sbom() -> dict[str, object]:
    """An SBOM shaped as ``cyclonedx-py --output-reproducible`` wrote 4.0.0's.

    The keys are the ones of ``phonometry-4.0.0.cdx.json`` as the release
    workflow wrote it, in its order: no ``serialNumber``, which that option
    leaves out, and no ``version`` or ``purl`` on the root component, which
    the tool cannot read from a dynamic version.
    """
    return {
        "components": [
            {"name": "numpy", "version": "2.5.4"},
            {"name": "scipy", "version": "1.18.1"},
            {"name": "pip", "version": "25.1"},
        ],
        "dependencies": [],
        "metadata": {"component": {"name": "phonometry", "type": "library"}},
        "version": 1,
        "$schema": "http://cyclonedx.org/schema/bom-1.6.schema.json",
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
    }


def _attest_accepts(document: object) -> bool:
    """Whether ``actions/attest-sbom`` takes ``document`` as an SBOM.

    The predicate of ``src/sbom.ts`` in ``actions/attest``, which
    ``attest-sbom@v4`` runs: a document is SPDX when ``spdxVersion`` and
    ``SPDXID`` are both truthy, CycloneDX when ``bomFormat``,
    ``serialNumber`` and ``specVersion`` all are, and anything else fails the
    step with "Unsupported SBOM format. Must be valid SPDX or CycloneDX
    JSON.", as it failed the GitHub Release job of 4.0.0. The fields are
    strings, whose truth is the same in JavaScript and in Python.
    """
    if not isinstance(document, dict):
        return False
    spdx = bool(document.get("spdxVersion")) and bool(document.get("SPDXID"))
    cyclonedx = all(
        bool(document.get(key)) for key in ("bomFormat", "serialNumber", "specVersion")
    )
    return spdx or cyclonedx


def _uuid5_url(name: str) -> str:
    """RFC 9562 section 5.5 by hand: the SHA-1 UUID of ``name`` among URLs."""
    namespace = bytes.fromhex("6ba7b8119dad11d180b400c04fd430c8")
    digest = bytearray(hashlib.sha1(namespace + name.encode()).digest()[:16])
    digest[6] = (digest[6] & 0x0F) | 0x50
    digest[8] = (digest[8] & 0x3F) | 0x80
    text = digest.hex()
    return f"{text[:8]}-{text[8:12]}-{text[12:16]}-{text[16:20]}-{text[20:]}"


def test_the_sbom_names_the_release_and_drops_the_installer() -> None:
    sbom = _sbom()
    assert release_sbom.finish(sbom, "2.0.0", ["numpy", "scipy"]) == []
    root = sbom["metadata"]["component"]  # type: ignore[index]
    assert root["version"] == "2.0.0"
    assert root["purl"] == "pkg:pypi/phonometry@2.0.0"
    assert [c["name"] for c in sbom["components"]] == ["numpy", "scipy"]  # type: ignore[attr-defined]


def test_the_attestation_refuses_the_sbom_the_tool_writes() -> None:
    """The document as cyclonedx-py writes it is the one 4.0.0 attested in vain."""
    assert not _attest_accepts(_sbom())


def test_the_finished_sbom_is_one_the_attestation_accepts(
    tmp_path: pathlib.Path,
) -> None:
    """The file the script writes, read back as the attestation reads it."""
    path = tmp_path / "phonometry-4.0.0.cdx.json"
    path.write_text(json.dumps(_sbom()), encoding="utf-8")
    assert release_sbom.main([str(path), "--version", "4.0.0"]) == 0
    assert _attest_accepts(json.loads(path.read_text(encoding="utf-8")))


def test_the_serial_number_names_the_release_and_the_document() -> None:
    """Version 5 UUID, by RFC 9562, of the package URL and the document's hash.

    The hash is the SHA-256 of the finished document without its serial
    number, written with its keys sorted, appended to the package URL after
    a ``#``; the UUID is the one of that name in the URL namespace.
    """
    sbom = _sbom()
    assert release_sbom.finish(sbom, "4.0.0", ["numpy", "scipy"]) == []
    content = {key: value for key, value in sbom.items() if key != "serialNumber"}
    digest = hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()
    expected = "urn:uuid:" + _uuid5_url(f"pkg:pypi/phonometry@4.0.0#{digest}")
    assert sbom["serialNumber"] == expected
    assert re.fullmatch(
        r"urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        expected,
    )


def test_the_sbom_of_a_release_is_written_to_the_same_bytes(
    tmp_path: pathlib.Path,
) -> None:
    """One document of one release is written to one file, serial number and all."""
    written = []
    for name in ("first.cdx.json", "second.cdx.json"):
        path = tmp_path / name
        path.write_text(json.dumps(_sbom()), encoding="utf-8")
        assert release_sbom.main([str(path), "--version", "4.0.0"]) == 0
        written.append(path.read_bytes())
    assert written[0] == written[1]
    assert b'"serialNumber": "urn:uuid:' in written[0]


def test_two_releases_have_two_serial_numbers() -> None:
    first, second = _sbom(), _sbom()
    release_sbom.finish(first, "4.0.0", ["numpy", "scipy"])
    release_sbom.finish(second, "4.0.1", ["numpy", "scipy"])
    assert first["serialNumber"] != second["serialNumber"]


def test_two_sboms_of_one_release_have_two_serial_numbers() -> None:
    """A rehearsal run again after numpy publishes a release writes another SBOM.

    The CycloneDX schema asks every BOM for a serial number of its own, and a
    reader takes the serial number and the BOM version (1 here) as the name
    of the document: two documents that list different components never
    share them.
    """
    first, later = _sbom(), _sbom()
    later["components"][0]["version"] = "2.6.0"  # type: ignore[index]
    assert release_sbom.finish(first, "4.0.0", ["numpy", "scipy"]) == []
    assert release_sbom.finish(later, "4.0.0", ["numpy", "scipy"]) == []
    assert first["version"] == later["version"]
    assert first["serialNumber"] != later["serialNumber"]


def test_a_serial_number_the_tool_wrote_is_replaced() -> None:
    """A random one would make every writing of the release's SBOM differ."""
    written, without = _sbom(), _sbom()
    written["serialNumber"] = "urn:uuid:3e671687-395b-41f5-a30f-a58921a69b79"
    assert release_sbom.finish(written, "4.0.0", ["numpy", "scipy"]) == []
    assert release_sbom.finish(without, "4.0.0", ["numpy", "scipy"]) == []
    assert written["serialNumber"] == without["serialNumber"]


def test_an_sbom_larger_than_the_attestation_reads_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """``actions/attest`` refuses a file over 16 MiB before it reads a field.

    The script writes nothing then, and says why, as for a missing field.
    """
    sbom = _sbom()
    sbom["metadata"]["properties"] = [  # type: ignore[index]
        {"name": "padding", "value": "x" * (17 * 1024 * 1024)}
    ]
    path = tmp_path / "phonometry-4.0.0.cdx.json"
    original = json.dumps(sbom)
    path.write_text(original, encoding="utf-8")
    assert release_sbom.main([str(path), "--version", "4.0.0"]) == 1
    assert path.read_text(encoding="utf-8") == original


def test_the_size_the_attestation_reads_is_held_to_the_byte() -> None:
    """``stats.size > MAX_SBOM_SIZE_BYTES`` in ``src/sbom.ts``: 16 MiB passes."""
    limit = 16 * 1024 * 1024
    assert release_sbom.size_problems(b"x" * limit) == []
    assert release_sbom.size_problems(b"x" * (limit + 1)) == [
        f"the SBOM is {limit + 1} bytes, over the {limit} the SBOM attestation reads"
    ]


@pytest.mark.parametrize(
    ("key", "problem"),
    [
        ("bomFormat", "the SBOM gives bomFormat None, not 'CycloneDX'"),
        ("specVersion", "the SBOM gives no specVersion"),
    ],
)
def test_an_sbom_the_attestation_would_refuse_is_reported(
    key: str, problem: str
) -> None:
    sbom = _sbom()
    del sbom[key]
    assert release_sbom.finish(sbom, "4.0.0", ["numpy", "scipy"]) == [problem]
    assert not _attest_accepts(sbom)


@pytest.mark.parametrize(
    ("serial", "problem"),
    [
        (None, "the SBOM has no serialNumber"),
        ("", "the SBOM has no serialNumber"),
        (
            "3e671687-395b-41f5-a30f-a58921a69b79",
            "the SBOM's serialNumber '3e671687-395b-41f5-a30f-a58921a69b79'"
            " is not urn:uuid: and a UUID",
        ),
        (
            "urn:uuid:3E671687-395B-41F5-A30F-A58921A69B79",
            "the SBOM's serialNumber 'urn:uuid:3E671687-395B-41F5-A30F-A58921A69B79'"
            " is not urn:uuid: and a UUID",
        ),
    ],
)
def test_a_serial_number_out_of_form_is_reported(
    serial: str | None, problem: str
) -> None:
    sbom = _sbom()
    if serial is not None:
        sbom["serialNumber"] = serial
    assert release_sbom.format_problems(sbom) == [problem]


def _written_by(**versions: str) -> dict[str, Any]:
    """An SBOM whose ``metadata.tools`` names the tools as 4.0.0's did."""
    sbom = _sbom()
    sbom["metadata"]["tools"] = {  # type: ignore[index]
        "components": [
            {"group": "CycloneDX", "name": name, "type": "application", "version": v}
            for name, v in versions.items()
        ]
    }
    return sbom


def test_the_sbom_of_4_0_0_was_written_by_a_tool_nothing_pinned() -> None:
    """4.0.0's SBOM names cyclonedx-python-lib 11.12.0, which only a range bounded.

    cyclonedx-bom 8.0.1 asks for ``cyclonedx-python-lib>=8,<12``; the
    library writes its own version into the document, so the SBOM of one
    release written again a week later could differ by that line alone.
    """
    sbom = _written_by(**{"cyclonedx-py": "8.0.1", "cyclonedx-python-lib": "11.12.0"})
    assert release_sbom.tool_problems(sbom, {"cyclonedx-bom": "8.0.1"}) == [
        "the SBOM was written by cyclonedx-python-lib 11.12.0, which"
        " requirements-release.txt does not pin"
    ]


def test_the_tools_that_write_the_sbom_are_the_pinned_ones() -> None:
    pins = release_sbom.pinned_tools()
    written = {
        "cyclonedx-py": pins["cyclonedx-bom"],
        "cyclonedx-python-lib": pins["cyclonedx-python-lib"],
    }
    assert release_sbom.tool_problems(_written_by(**written), pins) == []
    written["cyclonedx-python-lib"] = "11.11.0"
    assert release_sbom.tool_problems(_written_by(**written), pins) == [
        "the SBOM was written by cyclonedx-python-lib 11.11.0, and"
        f" requirements-release.txt pins {pins['cyclonedx-python-lib']}"
    ]


def test_a_tool_the_sbom_names_is_refused_when_unpinned(tmp_path: pathlib.Path) -> None:
    """The script writes nothing when the tool is not the pinned one."""
    path = tmp_path / "phonometry-4.0.0.cdx.json"
    original = json.dumps(_written_by(**{"cyclonedx-py": "0.0.1"}))
    path.write_text(original, encoding="utf-8")
    assert release_sbom.main([str(path), "--version", "4.0.0"]) == 1
    assert path.read_text(encoding="utf-8") == original


def test_the_pins_are_read_by_their_normalised_names(tmp_path: pathlib.Path) -> None:
    requirements = tmp_path / "requirements-release.txt"
    requirements.write_text(
        "# a comment\nboolean.py==5.0\nPy_Serializable==2.2.0  # why\n\n",
        encoding="utf-8",
    )
    assert release_sbom.pinned_tools(requirements) == {
        "boolean-py": "5.0",
        "py-serializable": "2.2.0",
    }


def test_an_sbom_without_a_declared_dependency_is_reported() -> None:
    assert release_sbom.finish(_sbom(), "2.0.0", ["numpy", "scipy", "matplotlib"]) == [
        "the SBOM does not list matplotlib, which phonometry depends on"
    ]


def test_the_declared_dependencies_are_read_from_pyproject() -> None:
    assert release_sbom.declared_dependencies() == ["numpy", "scipy"]


def test_a_dependency_with_a_floor_per_python_is_declared_once(
    tmp_path: pathlib.Path,
) -> None:
    """One floor per Python is one dependency the SBOM has to list, not three."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[project]\n"
        "dependencies = [\n"
        "    \"numpy>=2.0.2; python_version<'3.13'\",\n"
        "    \"numpy>=2.1.0; python_version>='3.13'\",\n"
        '    "SciPy>=1.14.0",\n'
        "]\n",
        encoding="utf-8",
    )
    assert release_sbom.declared_dependencies(pyproject) == ["numpy", "scipy"]


def test_the_sbom_script_rewrites_the_file(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "sbom.json"
    path.write_text(json.dumps(_sbom()), encoding="utf-8")
    assert release_sbom.main([str(path), "--version", "2.0.0"]) == 0
    assert (
        json.loads(path.read_text(encoding="utf-8"))["metadata"]["component"]["version"]
        == "2.0.0"
    )


# ==========================================================================
# The installed package
# ==========================================================================
@pytest.mark.git_checkout
def test_the_checkout_is_not_taken_for_the_installed_wheel() -> None:
    """Here phonometry comes from src, which is exactly what the check refuses.

    Every module imports and every data file is found through the package,
    so the one problem is where the package came from.
    """
    version = (_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    problems, count = check_installed_package.problems(
        version, artifacts.tracked_package_files()
    )
    assert count > 100
    assert len(problems) == 1
    assert problems[0].startswith("phonometry was imported from the checkout")


# ==========================================================================
# Line endings of what the sdist carries
# ==========================================================================
_GIT_S = 60.0


def _git(root: pathlib.Path, *args: str, **options: Any) -> None:
    child_process.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=Tests",
            "-c",
            "user.email=tests@example.org",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        timeout=_GIT_S,
        check=True,
        capture_output=True,
        **options,
    )


def _repository(tmp_path: pathlib.Path, files: dict[str, str]) -> pathlib.Path:
    """A repository holding *files*, committed at :data:`_EPOCH`.

    ``core.autocrlf`` is off, as the release and SECURITY.md clone a tag: Git
    for Windows turns it on for every repository, and an export of the
    commit would then write CRLF into every file that no attribute pins.
    """
    root = tmp_path / "repository"
    root.mkdir()
    _git(root, "init", "--quiet")
    _git(root, "config", "core.autocrlf", "false")
    for name, text in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text, encoding="utf-8", newline="\n")
    _git(root, "add", *files)
    stamp = f"{_EPOCH} +0000"
    _git(
        root,
        "commit",
        "--quiet",
        "-m",
        "The commit a release is built from",
        env={**os.environ, "GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp},
    )
    return root


def test_a_tracked_file_a_checkout_could_write_with_crlf_is_reported(
    tmp_path: pathlib.Path,
) -> None:
    """Only the tracked files without ``eol=lf`` are named, not what setuptools writes."""
    root = _repository(
        tmp_path,
        {
            ".gitattributes": "/README.md text eol=lf\n",
            "README.md": "readme\n",
            "LICENSE": "licence\n",
        },
    )
    sdist = tmp_path / "phonometry-2.0.0.tar.gz"
    _sdist(sdist, "2.0.0", ["PKG-INFO", "README.md", "LICENSE"])
    assert artifacts.line_ending_problems(sdist, "2.0.0", root) == [
        "the sdist carries LICENSE, which .gitattributes does not check out "
        "with LF on every platform"
    ]


@pytest.mark.git_checkout
def test_what_setuptools_packs_beside_the_package_is_checked_out_with_lf(
    tmp_path: pathlib.Path,
) -> None:
    """setuptools adds the readme and ``MANIFEST.in`` to the sdist by default.

    A clone made with ``core.autocrlf`` on, which writes CRLF on Linux and
    macOS too, would give each of them CRLF, and a rebuild from it would pack
    bytes PyPI does not hold, unless the repository's ``.gitattributes`` pins
    them to LF as it pins the package. Every file the sdist may carry beside
    the package is asked about.
    """
    carried = [
        "PKG-INFO",
        *artifacts.SDIST_BESIDE,
        *artifacts.SDIST_SUPPORT,
        *artifacts.LICENSE_FILES,
        *(f"src/{path}" for path in artifacts.tracked_package_files()),
    ]
    sdist = tmp_path / "phonometry-2.0.0.tar.gz"
    _sdist(sdist, "2.0.0", carried)
    assert artifacts.line_ending_problems(sdist, "2.0.0") == []


# ==========================================================================
# Rebuilding a release
# ==========================================================================
#: The commit time every rebuild below is stamped with.
_EPOCH = 1_793_322_334
_TOP = "phonometry-2.0.0"
#: An sdist's members: a directory, two files and one its owner can execute.
_MEMBERS: list[tuple[str, int, bytes | None]] = [
    (_TOP, 0o755, None),
    (f"{_TOP}/PKG-INFO", 0o644, b"Metadata-Version: 2.4\nName: phonometry\n"),
    (f"{_TOP}/src/phonometry/__init__.py", 0o644, b"x = 1\n"),
    (f"{_TOP}/tool.sh", 0o755, b"#!/bin/sh\n"),
]


def _builder_sdist(
    path: pathlib.Path,
    members: list[tuple[str, int, bytes | None]],
    *,
    mtime: float,
    owner: tuple[int, str],
    gzip_mtime: int,
    file_type: bytes = tarfile.REGTYPE,
) -> None:
    """An sdist as setuptools writes one on a builder's machine.

    The members carry the builder's clock (with a fraction of a second, which
    the pax format keeps), user and modes, a file is of *file_type*, and the
    gzip header carries the time of the build and the file's name.
    """
    tar = io.BytesIO()
    with tarfile.open(fileobj=tar, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for name, mode, data in members:
            info = tarfile.TarInfo(name)
            info.mtime = mtime
            info.uid = info.gid = owner[0]
            info.uname = info.gname = owner[1]
            info.mode = mode
            if data is None:
                info.type = tarfile.DIRTYPE
                archive.addfile(info)
            else:
                info.type = file_type
                info.size = len(data)
                archive.addfile(info, io.BytesIO(data))
    with (
        path.open("wb") as raw,
        gzip.GzipFile(
            filename=f"{_TOP}.tar", mode="wb", fileobj=raw, mtime=gzip_mtime
        ) as compressed,
    ):
        compressed.write(tar.getvalue())


def test_two_builders_sdists_of_one_commit_become_the_same_bytes(
    tmp_path: pathlib.Path,
) -> None:
    """Another clock, user, umask and member order; the same file once rewritten."""
    first, second = tmp_path / "first.tar.gz", tmp_path / "second.tar.gz"
    _builder_sdist(
        first,
        _MEMBERS,
        mtime=1_800_000_000.25,
        owner=(1001, "runner"),
        gzip_mtime=1_800_000_001,
    )
    _builder_sdist(
        second,
        [(name, mode | 0o020, data) for name, mode, data in reversed(_MEMBERS)],
        mtime=1_800_000_321.5,
        owner=(501, "someone"),
        gzip_mtime=1_800_000_400,
        file_type=tarfile.AREGTYPE,
    )
    assert first.read_bytes() != second.read_bytes()
    for path in (first, second):
        build_release.normalise_sdist(path, _EPOCH)
    assert first.read_bytes() == second.read_bytes()


def test_a_normalised_sdist_keeps_its_contents_and_nothing_of_the_builder(
    tmp_path: pathlib.Path,
) -> None:
    sdist = tmp_path / "phonometry-2.0.0.tar.gz"
    _builder_sdist(
        sdist, _MEMBERS, mtime=1_800_000_000.25, owner=(1001, "runner"), gzip_mtime=7
    )
    build_release.normalise_sdist(sdist, _EPOCH)
    header = sdist.read_bytes()[:10]
    assert struct.unpack("<I", header[4:8])[0] == _EPOCH
    assert not header[3] & 0x08, "the gzip header still names a file"
    with tarfile.open(sdist) as archive:
        members = archive.getmembers()
        assert [member.name for member in members] == sorted(
            name for name, _, _ in _MEMBERS
        )
        assert {
            (member.mtime, member.uid, member.gid, member.uname, member.gname)
            for member in members
        } == {(_EPOCH, 0, 0, "", "")}
        assert {member.name: member.mode for member in members} == {
            name: mode for name, mode, _ in _MEMBERS
        }
        assert {member.type for member in members} == {
            tarfile.DIRTYPE,
            tarfile.REGTYPE,
        }
        assert not any(member.pax_headers for member in members)
        for name, _, data in _MEMBERS:
            if data is not None:
                handle = archive.extractfile(name)
                assert handle is not None
                assert handle.read() == data


def test_an_sdist_holding_a_link_has_no_normal_form(tmp_path: pathlib.Path) -> None:
    sdist = tmp_path / "phonometry-2.0.0.tar.gz"
    with tarfile.open(sdist, "w:gz") as archive:
        link = tarfile.TarInfo(f"{_TOP}/README")
        link.type = tarfile.SYMTYPE
        link.linkname = "README.md"
        archive.addfile(link)
    with pytest.raises(ValueError, match="README, which is neither a file nor a dir"):
        build_release.normalise_sdist(sdist, _EPOCH)


def _current_umask() -> int:
    mask = os.umask(0)
    os.umask(mask)
    return mask


class _Builder:
    """Stands in for ``python -m build``: writes what it would, records how it ran."""

    def __init__(self, outdir: pathlib.Path, *, extra: str | None = None) -> None:
        self.outdir = outdir
        self.extra = extra
        self.calls: list[list[str]] = []
        self.epochs: list[str] = []
        self.umasks: list[int] = []
        #: The files of the directory each sdist was built from, by name.
        self.sources: list[dict[str, bytes]] = []
        self.wheel_from_normalised_sdist = False

    def __call__(
        self, command: list[str], *, check: bool, env: dict[str, str], timeout: float
    ) -> None:
        assert check
        assert timeout > 0
        self.calls.append(command)
        self.epochs.append(env["SOURCE_DATE_EPOCH"])
        self.umasks.append(_current_umask())
        if "--sdist" in command:
            source = pathlib.Path(command[-1])
            self.sources.append(
                {
                    path.relative_to(source).as_posix(): path.read_bytes()
                    for path in source.rglob("*")
                    if path.is_file()
                }
            )
            self.outdir.mkdir(parents=True, exist_ok=True)
            _builder_sdist(
                self.outdir / f"{_TOP}.tar.gz",
                _MEMBERS,
                mtime=1_800_000_000.25,
                owner=(1001, "runner"),
                gzip_mtime=1_800_000_001,
            )
            return
        with tarfile.open(command[-1]) as archive:
            self.wheel_from_normalised_sdist = {
                member.mtime for member in archive.getmembers()
            } == {_EPOCH}
        (self.outdir / f"{_TOP}-py3-none-any.whl").write_bytes(b"wheel")
        if self.extra is not None:
            (self.outdir / self.extra).write_bytes(b"")


def _checkout(tmp_path: pathlib.Path) -> pathlib.Path:
    """A checkout of a commit that holds the version file and nothing else."""
    return _repository(tmp_path, {"VERSION": "2.0.0\n"})


def test_the_wheel_is_built_from_the_normalised_sdist_under_the_commit_time(
    tmp_path: pathlib.Path,
) -> None:
    outdir = tmp_path / "dist"
    builder = _Builder(outdir)
    root = _checkout(tmp_path)
    built = build_release.build(
        outdir, version="2.0.0", epoch=_EPOCH, root=root, run=builder
    )
    sdist = outdir / f"{_TOP}.tar.gz"
    assert built == [sdist, outdir / f"{_TOP}-py3-none-any.whl"]
    front_end = [sys.executable, "-m", "build", "--no-isolation"]
    exported = pathlib.Path(builder.calls[0][-1])
    assert builder.calls == [
        [*front_end, "--sdist", "--outdir", str(outdir), str(exported)],
        [*front_end, "--wheel", "--outdir", str(outdir), str(sdist)],
    ]
    assert exported != root
    assert not exported.exists(), "the export of the commit was left behind"
    assert builder.sources == [{"VERSION": b"2.0.0\n"}]
    assert builder.epochs == [str(_EPOCH)] * 2
    assert builder.wheel_from_normalised_sdist


def test_the_sdist_is_built_from_the_commit_and_nothing_else_the_checkout_holds(
    tmp_path: pathlib.Path,
) -> None:
    """setuptools packs a file the checkout holds even when ``git status`` hides it.

    A test module the builder's own excludes file hides, a ``setup.cfg``,
    which setuptools reads and merges into the sdist's, and a stale file in
    the ``.egg-info`` directory, which it grafts whole, all reached the sdist
    of a checkout ``git status`` called the commit. An attribute file the
    checkout holds beside the commit's changes no line ending either.
    """
    committed = {
        ".gitignore": "*.egg-info/\n",
        "VERSION": "2.0.0\n",
        "src/phonometry/__init__.py": "x = 1\n",
        "tests/test_release.py": "def test_release():\n    pass\n",
    }
    root = _repository(tmp_path, committed)
    hidden = {
        "tests/test_local.py": "def test_local():\n    pass\n",
        "setup.cfg": "[metadata]\nname = something-else\n",
        "src/phonometry.egg-info/stale.txt": "left by an older build\n",
        "src/.gitattributes": "* text eol=crlf\n",
    }
    with (root / ".git" / "info" / "exclude").open("a", encoding="utf-8") as rules:
        rules.write("tests/test_local.py\nsetup.cfg\nsrc/.gitattributes\n")
    for name, text in hidden.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text, encoding="utf-8", newline="\n")
    assert build_release.checkout_changes(root) == []
    builder = _Builder(tmp_path / "dist")
    build_release.build(
        tmp_path / "dist", version="2.0.0", epoch=_EPOCH, root=root, run=builder
    )
    assert builder.sources == [
        {name: text.encode() for name, text in committed.items()}
    ]


@pytest.mark.skipif(
    os.name != "posix", reason="a Windows umask holds the write bit and nothing else"
)
def test_both_builds_run_under_umask_022_and_the_callers_is_given_back(
    tmp_path: pathlib.Path,
) -> None:
    """setuptools writes each module into the wheel with a mode the umask decides."""
    builder = _Builder(tmp_path / "dist")
    previous = os.umask(0o002)
    try:
        build_release.build(
            tmp_path / "dist",
            version="2.0.0",
            epoch=_EPOCH,
            root=_checkout(tmp_path),
            run=builder,
        )
        assert _current_umask() == 0o002
    finally:
        os.umask(previous)
    assert builder.umasks == [0o022, 0o022]


def test_a_build_into_a_directory_that_holds_files_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    outdir = tmp_path / "dist"
    outdir.mkdir()
    (outdir / f"{_TOP}-py3-none-any.whl").write_bytes(b"an older wheel")
    builder = _Builder(outdir)
    root = _checkout(tmp_path)
    with pytest.raises(ValueError, match="already holds files"):
        build_release.build(
            outdir, version="2.0.0", epoch=_EPOCH, root=root, run=builder
        )
    assert builder.calls == []


def test_a_build_that_leaves_another_file_is_refused(tmp_path: pathlib.Path) -> None:
    outdir = tmp_path / "dist"
    builder = _Builder(outdir, extra=f"{_TOP}-cp313-cp313-linux_x86_64.whl")
    root = _checkout(tmp_path)
    with pytest.raises(ValueError, match="cp313"):
        build_release.build(
            outdir, version="2.0.0", epoch=_EPOCH, root=root, run=builder
        )


def test_a_checksum_file_is_read_as_sha256sum_writes_it() -> None:
    sdist, wheel = "1" * 64, "a" * 64
    text = f"{sdist}  {_TOP}.tar.gz\n{wheel} *{_TOP}-py3-none-any.whl\n\n"
    assert build_release.read_checksums(text) == {
        f"{_TOP}.tar.gz": sdist,
        f"{_TOP}-py3-none-any.whl": wheel,
    }
    with pytest.raises(ValueError, match="line 2 of the checksum file"):
        build_release.read_checksums(f"{sdist}  {_TOP}.tar.gz\nnot a digest\n")


def test_a_checksum_file_that_lists_a_file_twice_is_refused() -> None:
    """Keeping the last digest would pass a wheel listed wrong, then right.

    ``sha256sum --check`` checks every line and fails on the first; the
    rebuild compares one digest per file, so it refuses the file instead,
    whether the two digests differ or not.
    """
    wrong, right = "0" * 64, "a" * 64
    wheel = f"{_TOP}-py3-none-any.whl"
    for first in (wrong, right):
        with pytest.raises(
            ValueError, match=f"line 3 of the checksum file lists '{wheel}' again"
        ):
            build_release.read_checksums(
                f"{'1' * 64}  {_TOP}.tar.gz\n{first}  {wheel}\n{right} *{wheel}\n"
            )


def test_a_rebuild_is_compared_file_by_file() -> None:
    built = {"a.tar.gz": "1" * 64, "a.whl": "2" * 64}
    assert build_release.mismatches(built, dict(built), "SUMS") == []
    assert build_release.mismatches(
        built, {"a.tar.gz": "1" * 64, "a.whl": "3" * 64, "b.whl": "4" * 64}, "PyPI"
    ) == [
        f"a.whl rebuilds to SHA-256 {'2' * 64}, and PyPI lists {'3' * 64}",
        "PyPI lists b.whl, which the build did not make",
    ]
    assert build_release.mismatches(built, {"a.whl": "2" * 64}, "SUMS") == [
        "SUMS does not list a.tar.gz"
    ]


def _pypi_answer(*names: str) -> bytes:
    return json.dumps(
        {
            "urls": [
                {"filename": name, "digests": {"sha256": "5" * 64}} for name in names
            ]
        }
    ).encode()


def test_pypi_is_asked_again_until_it_lists_both_files() -> None:
    """Its JSON lags an upload: first no version, then the sdist alone."""
    sdist, wheel = build_release.built_names("2.0.0")
    answers: list[bytes | Exception] = [
        urllib.error.URLError("HTTP Error 404: Not Found"),
        _pypi_answer(sdist),
        _pypi_answer(sdist, wheel),
    ]
    asked: list[str] = []
    waits: list[float] = []

    def fetch(url: str) -> bytes:
        asked.append(url)
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    digests = build_release.pypi_digests(
        "2.0.0", fetch=fetch, sleep=waits.append, attempts=5, wait_s=0.5
    )
    assert digests == {sdist: "5" * 64, wheel: "5" * 64}
    assert asked == ["https://pypi.org/pypi/phonometry/2.0.0/json"] * 3
    assert waits == [0.5, 0.5]


def test_pypi_is_given_up_on_after_the_last_attempt() -> None:
    waits: list[float] = []

    def fetch(url: str) -> bytes:
        return b"<html>not json</html>"

    with pytest.raises(RuntimeError, match="after 3 attempts"):
        build_release.pypi_digests(
            "2.0.0", fetch=fetch, sleep=waits.append, attempts=3, wait_s=0.5
        )
    assert waits == [0.5, 0.5]


def _distribution(
    root: pathlib.Path, name: str, entry_points: str
) -> metadata.Distribution:
    info = root / f"{name}-1.0.dist-info"
    info.mkdir()
    (info / "METADATA").write_text(
        f"Metadata-Version: 2.1\nName: {name}\nVersion: 1.0\n", encoding="utf-8"
    )
    (info / "entry_points.txt").write_text(entry_points, encoding="utf-8")
    return metadata.PathDistribution(info)


def test_a_setuptools_plugin_of_another_package_is_reported(
    tmp_path: pathlib.Path,
) -> None:
    """setuptools-scm's file finder would pack every file git tracks; cffi's keyword is idle."""
    installed = [
        _distribution(
            tmp_path,
            "setuptools",
            "[setuptools.finalize_distribution_options]\n"
            "keywords = setuptools.dist:Distribution._finalize_setup_keywords\n",
        ),
        _distribution(
            tmp_path,
            "cffi",
            "[distutils.setup_keywords]\ncffi_modules = cffi.setuptools_ext:cffi_modules\n",
        ),
        _distribution(
            tmp_path,
            "setuptools-scm",
            "[setuptools.file_finders]\nscm = setuptools_scm._file_finders:find_files\n",
        ),
    ]
    assert build_release.foreign_plugins(installed) == [
        "setuptools-scm installs the setuptools plugin 'scm' "
        "(setuptools.file_finders), which can change what the build packs"
    ]


def test_the_commit_time_stamps_the_build_and_the_checkout_must_be_the_commit(
    tmp_path: pathlib.Path,
) -> None:
    root = _repository(tmp_path, {".gitignore": "dist/\n", "VERSION": "2.0.0\n"})
    assert build_release.commit_time(root) == _EPOCH
    assert build_release.checkout_changes(root) == []
    (root / "dist").mkdir()
    (root / "dist" / "left-over.whl").write_bytes(b"")
    assert build_release.checkout_changes(root) == []
    (root / "VERSION").write_text("2.0.1\n", encoding="utf-8")
    (root / "stray.py").write_text("", encoding="utf-8")
    assert build_release.checkout_changes(root) == [" M VERSION", "?? stray.py"]


#: ``main`` refuses Windows before it reads its arguments, so a test that
#: drives it past that point runs on the platforms a release rebuilds on.
_REBUILDS_HERE = pytest.mark.skipif(
    os.name == "nt", reason="scripts/build_release.py refuses to build on Windows"
)


def _fake_build(
    monkeypatch: pytest.MonkeyPatch, *, changes: list[str]
) -> dict[str, str]:
    """Make :func:`build_release.main` build two known files; return their digests."""
    version = (_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    names = build_release.built_names(version)

    def build(target: pathlib.Path, *, version: str, epoch: int) -> list[pathlib.Path]:
        assert epoch == _EPOCH
        target.mkdir()
        for name in names:
            (target / name).write_bytes(name.encode())
        return [target / name for name in names]

    monkeypatch.setattr(build_release, "foreign_plugins", list)
    monkeypatch.setattr(build_release, "checkout_changes", lambda: changes)
    monkeypatch.setattr(build_release, "commit_time", lambda: _EPOCH)
    monkeypatch.setattr(build_release, "build", build)
    return {name: hashlib.sha256(name.encode()).hexdigest() for name in names}


@_REBUILDS_HERE
def test_a_rebuild_that_matches_the_checksum_file_passes(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    digests = _fake_build(monkeypatch, changes=[])
    sums = tmp_path / "phonometry.sha256"
    sums.write_text(
        "".join(f"{digest}  {name}\n" for name, digest in digests.items()),
        encoding="utf-8",
    )
    outdir = str(tmp_path / "rebuilt")
    assert build_release.main(["--outdir", outdir, "--check", str(sums)]) == 0
    assert "rebuild to the files phonometry.sha256 lists" in capsys.readouterr().out


@_REBUILDS_HERE
def test_a_rebuild_that_differs_from_pypi_fails(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    digests = _fake_build(monkeypatch, changes=[])
    sdist, wheel = sorted(digests, key=lambda name: not name.endswith(".tar.gz"))
    published = {sdist: digests[sdist], wheel: "0" * 64}
    monkeypatch.setattr(build_release, "pypi_digests", lambda version: published)
    outdir = str(tmp_path / "rebuilt")
    assert build_release.main(["--outdir", outdir, "--check-pypi"]) == 1
    assert (
        f"{wheel} rebuilds to SHA-256 {digests[wheel]}, and PyPI lists {'0' * 64}"
        in (capsys.readouterr().err)
    )


@_REBUILDS_HERE
def test_a_checkout_that_is_not_its_commit_is_not_built(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _fake_build(monkeypatch, changes=[" M src/phonometry/__init__.py"])
    outdir = tmp_path / "rebuilt"
    assert build_release.main(["--outdir", str(outdir)]) == 1
    assert not outdir.exists()
    assert (
        "the checkout differs from its commit:  M src/phonometry/__init__.py"
        in capsys.readouterr().err
    )


def test_a_build_on_windows_is_refused_before_anything_else(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """zipfile, the wheel's modes and setuptools' text files depend on Windows.

    The refusal comes before the arguments are read, so nothing else runs.
    """

    def fail(*args: object, **kwargs: object) -> None:
        pytest.fail("the script went on after refusing Windows")

    for name in ("foreign_plugins", "checkout_changes", "commit_time", "build"):
        monkeypatch.setattr(build_release, name, fail)
    monkeypatch.setattr(os, "name", "nt")
    status = build_release.main(["--outdir", "rebuilt"])
    monkeypatch.undo()
    assert status == 1
    err = capsys.readouterr().err
    assert err == f"::error::{build_release.WINDOWS_REFUSAL}\n"
    assert "Linux and macOS" in err
    assert "not under /mnt/c" in err


@_REBUILDS_HERE
@pytest.mark.parametrize(
    ("text", "message"),
    [
        (None, "No such file or directory"),
        ("", "lists no file"),
        ("not a digest  phonometry-2.0.0.tar.gz\n", "line 1 of the checksum file"),
        (b"\xff\xfe", "can't decode"),
        (
            f"{'0' * 64}  phonometry-2.0.0.tar.gz\n{'1' * 64}  phonometry-2.0.0.tar.gz\n",
            "lists 'phonometry-2.0.0.tar.gz' again",
        ),
    ],
    ids=["missing", "empty", "malformed", "not-utf-8", "a-file-twice"],
)
def test_a_checksum_file_that_cannot_be_used_is_refused_before_the_build(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    text: str | bytes | None,
    message: str,
) -> None:
    """A missing, empty or malformed checksum file costs no build to find.

    So does one that lists a file twice.
    """
    _fake_build(monkeypatch, changes=[])

    def build(*args: object, **kwargs: object) -> None:
        pytest.fail("the script built before reading the checksum file")

    monkeypatch.setattr(build_release, "build", build)
    sums = tmp_path / "phonometry.sha256"
    if isinstance(text, str):
        sums.write_text(text, encoding="utf-8")
    elif isinstance(text, bytes):
        sums.write_bytes(text)
    outdir = tmp_path / "rebuilt"
    assert build_release.main(["--outdir", str(outdir), "--check", str(sums)]) == 1
    err = capsys.readouterr().err
    assert err.startswith("::error::")
    assert message in err
    assert "Traceback" not in err


@_REBUILDS_HERE
@pytest.mark.parametrize("kind", SPECIAL_KINDS)
def test_a_checksum_file_that_is_no_regular_file_is_refused_before_it_is_opened(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    kind: str,
) -> None:
    """A named pipe no one writes to kept the open waiting, and a device a read going.

    Neither ended, and neither said a word; a directory raised whatever the
    open met first. Each is now named in one annotation, within seconds.
    """
    _fake_build(monkeypatch, changes=[])

    def build(*args: object, **kwargs: object) -> None:
        pytest.fail("the script built before reading the checksum file")

    monkeypatch.setattr(build_release, "build", build)
    sums = tmp_path / "phonometry.sha256"
    what = make_special(kind, sums)
    outdir = tmp_path / "rebuilt"
    statuses: list[int] = []
    error = raised_within(
        lambda: statuses.append(
            build_release.main(["--outdir", str(outdir), "--check", str(sums)])
        ),
        pipe=sums if kind == "pipe" else None,
    )
    assert error is None
    assert statuses == [1]
    assert capsys.readouterr().err == (
        f"::error::the checksum file {sums} is {what}, and a checksum file is "
        "read only from a regular file\n"
    )


@_REBUILDS_HERE
def test_pypi_giving_up_ends_as_an_annotation(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The likeliest failure of the rebuild after a release: PyPI lagging past the last try."""
    _fake_build(monkeypatch, changes=[])

    def pypi_digests(version: str) -> dict[str, str]:
        msg = (
            f"PyPI does not list the sdist and the wheel of {version} after 10 attempts"
        )
        raise RuntimeError(msg)

    monkeypatch.setattr(build_release, "pypi_digests", pypi_digests)
    outdir = str(tmp_path / "rebuilt")
    assert build_release.main(["--outdir", outdir, "--check-pypi"]) == 1
    captured = capsys.readouterr()
    assert "::error::PyPI does not list the sdist and the wheel of" in captured.err
    assert "after 10 attempts" in captured.err
    assert "rebuild to the files" not in captured.out


@_REBUILDS_HERE
@pytest.mark.parametrize(
    "error",
    [
        subprocess.CalledProcessError(1, [sys.executable, "-m", "build"]),
        subprocess.TimeoutExpired([sys.executable, "-m", "build"], 900.0),
    ],
    ids=["failed", "timed-out"],
)
def test_a_build_that_fails_or_hangs_ends_as_an_annotation(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    error: subprocess.SubprocessError,
) -> None:
    _fake_build(monkeypatch, changes=[])

    def build(*args: object, **kwargs: object) -> None:
        raise error

    monkeypatch.setattr(build_release, "build", build)
    assert build_release.main(["--outdir", str(tmp_path / "rebuilt")]) == 1
    err = capsys.readouterr().err
    assert err == f"::error::{error}\n"


@_REBUILDS_HERE
def test_an_output_directory_that_is_a_file_ends_as_an_annotation(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(build_release, "foreign_plugins", list)
    monkeypatch.setattr(build_release, "checkout_changes", list)
    monkeypatch.setattr(build_release, "commit_time", lambda: _EPOCH)
    outdir = tmp_path / "rebuilt"
    outdir.write_bytes(b"")
    assert build_release.main(["--outdir", str(outdir)]) == 1
    err = capsys.readouterr().err
    assert err.startswith("::error::")
    assert "Not a directory" in err
