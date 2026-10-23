#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The node image's ffmpeg pin, and the monthly check that says when it should move."""

from __future__ import annotations

import hashlib
import io
import os
import shutil
import sys
import tarfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_ROOT / "scripts"))

import node_ffmpeg

_SHA = "a" * 64
_BASE = "https://github.com/BtbN/FFmpeg-Builds/releases/download"
_GPL_9 = "ffmpeg-n9.0.2-17-g2a571b6068-linux64-gpl-9.0.tar.xz"
_GPL_8 = "ffmpeg-n8.1.3-9-g29e619e767-linux64-gpl-8.1.tar.xz"
_OTHERS = (
    "ffmpeg-n9.0.2-17-g2a571b6068-linux64-gpl-shared-9.0.tar.xz",
    "ffmpeg-N-127021-ge0c94b2d1c-linux64-gpl.tar.xz",
    "ffmpeg-n9.0.2-17-g2a571b6068-win64-gpl-9.0.zip",
)


def _release(tag: str, *names: str) -> dict[str, object]:
    return {
        "tag_name": tag,
        "assets": [
            {
                "name": name,
                "browser_download_url": f"{_BASE}/{tag}/{name}",
                "digest": f"sha256:{_SHA}",
            }
            for name in names
        ],
    }


_RELEASES = [
    _release("latest", _GPL_9),
    _release("autobuild-2026-10-20-13-08", _GPL_9, *_OTHERS),
    _release("autobuild-2026-10-19-13-06", _GPL_9),
    _release("autobuild-2026-09-30-13-08", _GPL_8, _GPL_9, *_OTHERS),
    _release("autobuild-2026-08-31-13-27", _GPL_9),
]
_PINNED = node_ffmpeg.Pin(f"{_BASE}/autobuild-2026-09-30-13-08/{_GPL_9}", _SHA)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "ARG FFMPEG_URL=https://example.org/ffmpeg.tar.xz\n",
        f"ARG FFMPEG_URL=http://example.org/ffmpeg.tar.xz\nARG FFMPEG_SHA256={_SHA}\n",
        "ARG FFMPEG_URL=https://example.org/ffmpeg.tar.xz\nARG FFMPEG_SHA256=abc\n",
    ],
)
def test_a_dockerfile_without_a_well_formed_pin_is_refused(text: str) -> None:
    with pytest.raises(ValueError, match="FFMPEG_SHA256"):
        node_ffmpeg.pin(text)


def test_the_newest_month_end_build_is_the_last_release_of_the_newest_ended_month() -> (
    None
):
    assert node_ffmpeg.newest_month_end(_RELEASES) == (_PINNED.url, _SHA)


def test_a_build_made_at_a_release_tag_is_found() -> None:
    """A build at the tag itself has no ``-<commits>-g<hash>`` in its name."""
    at_tag = "ffmpeg-n9.0.3-linux64-gpl-9.0.tar.xz"
    releases = [
        _release("autobuild-2026-10-01-13-00", _GPL_9),
        _release("autobuild-2026-09-30-13-08", _GPL_8, at_tag, *_OTHERS),
    ]
    assert node_ffmpeg.newest_month_end(releases) == (
        f"{_BASE}/autobuild-2026-09-30-13-08/{at_tag}",
        _SHA,
    )


def test_a_pin_at_the_newest_month_end_build_that_downloads_is_quiet() -> None:
    assert node_ffmpeg.problems(_PINNED, _RELEASES, answers=lambda url: True) == []


def test_a_newer_month_end_build_is_named_with_its_url_and_sha256() -> None:
    older = node_ffmpeg.Pin(f"{_BASE}/autobuild-2026-08-31-13-27/{_GPL_9}", _SHA)
    (problem,) = node_ffmpeg.problems(older, _RELEASES, answers=lambda url: True)
    assert f"FFMPEG_URL={_PINNED.url}" in problem
    assert f"FFMPEG_SHA256={_SHA}" in problem
    assert "build of ffmpeg n9.0 is out" in problem


def test_a_build_of_a_lower_release_line_is_never_offered_as_newer() -> None:
    """A month-end release that lacks the pinned line is named, and its lower line is not offered."""
    older = node_ffmpeg.Pin(f"{_BASE}/autobuild-2026-08-31-13-27/{_GPL_9}", _SHA)
    releases = [
        _release("autobuild-2026-10-20-13-08", _GPL_9),
        _release("autobuild-2026-09-30-13-08", _GPL_8, *_OTHERS),
        _release("autobuild-2026-08-31-13-27", _GPL_9),
    ]
    (problem,) = node_ffmpeg.problems(older, releases, answers=lambda url: True)
    assert "no build of the pinned ffmpeg n9.0" in problem
    assert "only of ffmpeg n8.1" in problem
    assert "FFMPEG_URL=" not in problem


def test_an_older_month_end_build_is_not_offered() -> None:
    """Before a new month's first release, the newest ended month is the one before the pin's."""
    assert node_ffmpeg.problems(_PINNED, _RELEASES[3:], answers=lambda url: True) == []


def test_a_pin_that_no_longer_downloads_is_named() -> None:
    (problem,) = node_ffmpeg.problems(_PINNED, _RELEASES, answers=lambda url: False)
    assert "no longer downloads" in problem


def test_a_pinned_file_github_lists_another_sha256_for_is_named() -> None:
    moved = node_ffmpeg.Pin(_PINNED.url, "b" * 64)
    (problem,) = node_ffmpeg.problems(moved, _RELEASES, answers=lambda url: True)
    assert f"SHA-256 of the pinned ffmpeg as {_SHA}" in problem


def test_releases_without_a_month_end_build_are_a_problem_not_silence() -> None:
    (problem,) = node_ffmpeg.problems(_PINNED, _RELEASES[:3], answers=lambda url: True)
    assert "no month-end release" in problem


def test_the_check_of_the_dockerfile_s_pin_at_its_month_end_is_quiet(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The check reads the Dockerfile's own pin, and knows its build for what it is."""
    pinned = node_ffmpeg.pin(node_ffmpeg.DOCKERFILE.read_text(encoding="utf-8"))
    tag, name = pinned.url.split("/")[-2:]
    published = {
        "tag_name": tag,
        "assets": [
            {
                "name": name,
                "browser_download_url": pinned.url,
                "digest": f"sha256:{pinned.sha256}",
            }
        ],
    }
    monkeypatch.setattr(
        node_ffmpeg,
        "_releases",
        lambda: [_release("autobuild-2099-01-01-13-00", _GPL_9), published],
    )
    monkeypatch.setattr(node_ffmpeg, "_answers", lambda url: url == pinned.url)
    assert node_ffmpeg.main(["check"]) == 0
    assert (
        capsys.readouterr().out
        == f"The pinned ffmpeg is the newest month-end build, and it downloads: {pinned.url}\n"
    )


def test_the_check_names_each_problem_and_fails(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(node_ffmpeg, "_releases", lambda: _RELEASES[:3])
    monkeypatch.setattr(node_ffmpeg, "_answers", lambda url: False)
    assert node_ffmpeg.main(["check"]) == 1
    lines = capsys.readouterr().out.splitlines()
    assert [line.startswith("::error::") for line in lines] == [True, True]
    assert "no longer downloads" in lines[0]
    assert "no month-end release" in lines[1]


def _archive(
    tmp_path: Path, names: tuple[str, ...] = ("ffmpeg", "ffprobe")
) -> tuple[Path, str]:
    """A small build laid out as BtbN's: ``<top>/bin/<program>``, a licence, the docs."""
    source = tmp_path / "build.tar.xz"
    with tarfile.open(source, "w:xz") as tar:
        for name in (
            *(f"bin/{program}" for program in names),
            "LICENSE.txt",
            "doc/ffmpeg.html",
        ):
            data = f"#!/bin/sh\necho {name}\n".encode()
            info = tarfile.TarInfo(
                f"ffmpeg-n9.0.2-17-g2a571b6068-linux64-gpl-9.0/{name}"
            )
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return source, hashlib.sha256(source.read_bytes()).hexdigest()


def _copy_from(source: Path, calls: list[str]) -> Callable[[str, Path], None]:
    def download(url: str, target: Path) -> None:
        calls.append(url)
        shutil.copyfile(source, target)

    return download


def test_the_pinned_build_is_fetched_once_checked_and_cut_to_its_two_programs(
    tmp_path: Path,
) -> None:
    source, sha256 = _archive(tmp_path)
    pinned = node_ffmpeg.Pin("https://example.org/ffmpeg.tar.xz", sha256)
    calls: list[str] = []
    bin_dir = node_ffmpeg.fetch(
        pinned, tmp_path / "cache", download=_copy_from(source, calls)
    )
    assert bin_dir == tmp_path / "cache" / sha256 / "bin"
    assert sorted(path.name for path in bin_dir.iterdir()) == ["ffmpeg", "ffprobe"]
    assert all(os.access(path, os.X_OK) for path in bin_dir.iterdir())
    assert (
        node_ffmpeg.fetch(
            pinned, tmp_path / "cache", download=_copy_from(source, calls)
        )
        == bin_dir
    )
    assert calls == [pinned.url]


def test_a_download_with_another_sha256_is_refused_and_leaves_nothing(
    tmp_path: Path,
) -> None:
    source, _ = _archive(tmp_path)
    pinned = node_ffmpeg.Pin("https://example.org/ffmpeg.tar.xz", "0" * 64)
    download = _copy_from(source, [])
    with pytest.raises(ValueError, match=r"not the pinned 0{64}"):
        node_ffmpeg.fetch(pinned, tmp_path / "cache", download=download)
    assert list((tmp_path / "cache").iterdir()) == []


def test_a_build_without_ffprobe_is_refused(tmp_path: Path) -> None:
    source, sha256 = _archive(tmp_path, ("ffmpeg",))
    pinned = node_ffmpeg.Pin("https://example.org/ffmpeg.tar.xz", sha256)
    download = _copy_from(source, [])
    with pytest.raises(ValueError, match=r"bin/ffprobe"):
        node_ffmpeg.fetch(pinned, tmp_path / "cache", download=download)
    assert list((tmp_path / "cache").iterdir()) == []
