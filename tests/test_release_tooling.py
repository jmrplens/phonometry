#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The scripts the release workflow runs, held to what each one promises.

A release cannot be rehearsed against PyPI twice with the same version, so the
checks it runs on the way have to be right before they are needed: the notes
come from the changelog section and nowhere else, a built file the package is
missing stops the release, the SBOM names what ``pip install phonometry``
resolves, and the package the verification imports is the installed wheel.
"""

from __future__ import annotations

import io
import json
import pathlib
import sys
import tarfile
import zipfile

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

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
    "phonometry/building/data/rows.json",
]


def _wheel(
    path: pathlib.Path,
    version: str,
    names: list[str],
    *,
    metadata_version: str | None = None,
) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name in names:
            archive.writestr(name, "x")
        archive.writestr(
            f"phonometry-{version}.dist-info/METADATA",
            f"Metadata-Version: 2.4\nName: phonometry\nVersion: {metadata_version or version}\n",
        )


def _sdist(path: pathlib.Path, version: str, names: list[str]) -> None:
    top = f"phonometry-{version}/"
    with tarfile.open(path, "w:gz") as archive:
        for name in names:
            data = (
                f"Metadata-Version: 2.4\nName: phonometry\nVersion: {version}\n"
                if name == "PKG-INFO"
                else "x"
            ).encode()
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
        ["PKG-INFO", *artifacts.SDIST_SUPPORT, *(f"src/{path}" for path in _TRACKED)],
    )
    return dist


def test_a_build_that_holds_the_package_passes(tmp_path: pathlib.Path) -> None:
    assert artifacts.dist_problems(_good_dist(tmp_path), "2.0.0", _TRACKED) == []


def test_a_data_file_the_wheel_left_behind_is_reported(tmp_path: pathlib.Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    _wheel(dist / "phonometry-2.0.0-py3-none-any.whl", "2.0.0", _TRACKED[:2])
    assert artifacts.wheel_problems(
        dist / "phonometry-2.0.0-py3-none-any.whl", "2.0.0", _TRACKED
    ) == ["the wheel lacks phonometry/building/data/rows.json"]


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
        "the sdist lacks phonometry-2.0.0/src/phonometry/building/data/rows.json",
    ]


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


def test_git_tracks_the_package_data_the_wheel_has_to_carry() -> None:
    tracked = artifacts.tracked_package_files()
    assert "phonometry/__init__.py" in tracked
    assert "phonometry/py.typed" in tracked
    assert all(path.startswith("phonometry/") for path in tracked)


# ==========================================================================
# The SBOM
# ==========================================================================
def _sbom() -> dict[str, object]:
    return {
        "bomFormat": "CycloneDX",
        "metadata": {"component": {"name": "phonometry", "type": "library"}},
        "components": [
            {"name": "numpy", "version": "2.5.4"},
            {"name": "scipy", "version": "1.18.1"},
            {"name": "pip", "version": "25.1"},
        ],
    }


def test_the_sbom_names_the_release_and_drops_the_installer() -> None:
    sbom = _sbom()
    assert release_sbom.finish(sbom, "2.0.0", ["numpy", "scipy"]) == []
    root = sbom["metadata"]["component"]  # type: ignore[index]
    assert root["version"] == "2.0.0"
    assert root["purl"] == "pkg:pypi/phonometry@2.0.0"
    assert [c["name"] for c in sbom["components"]] == ["numpy", "scipy"]  # type: ignore[attr-defined]


def test_an_sbom_without_a_declared_dependency_is_reported() -> None:
    assert release_sbom.finish(_sbom(), "2.0.0", ["numpy", "scipy", "matplotlib"]) == [
        "the SBOM does not list matplotlib, which phonometry depends on"
    ]


def test_the_declared_dependencies_are_read_from_pyproject() -> None:
    assert release_sbom.declared_dependencies() == ["numpy", "scipy"]


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
