#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The node image's ffmpeg pin: read it, and check it against BtbN's releases.

docker/node/Dockerfile pins a static ffmpeg build of BtbN's FFmpeg-Builds by
URL and SHA-256 (``FFMPEG_URL``, ``FFMPEG_SHA256``). Dependabot cannot move a
URL, so ``python scripts/node_ffmpeg.py check``, which the workflow
node-ffmpeg.yml runs each month, says when the pinned file no longer
downloads, when GitHub lists another SHA-256 for it, or when a newer
month-end build of the same variant is out, with its URL and SHA-256. BtbN
keeps month-end releases for about two years and daily ones for two weeks,
so only a month-end release is offered. The pin is moved by hand, as the
Dockerfile's comment says, because the SVT-AV1 inside a new build has to be
checked on a node first. ``python scripts/node_ffmpeg.py fetch`` downloads
the pinned build for a CPU render of the documentation clips on this
machine, checks it and prints the directory of its ffmpeg and ffprobe, or
says in one line why it could not and exits 1. Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

ROOT = Path(__file__).resolve().parent.parent

#: The Dockerfile that holds the pin.
DOCKERFILE = ROOT / "docker" / "node" / "Dockerfile"

#: BtbN's releases, newest first: two weeks of daily ones and about two years
#: of month-end ones fit in one page.
RELEASES = "https://api.github.com/repos/BtbN/FFmpeg-Builds/releases?per_page=100"

_ARG = re.compile(r"^ARG (FFMPEG_URL|FFMPEG_SHA256)=(\S+)$", re.MULTILINE)
_SHA256 = re.compile(r"[0-9a-f]{64}")
_TAG = re.compile(r"^autobuild-(\d{4}-\d{2})-\d{2}-\d{2}-\d{2}$")
#: A release line's static GPL build for linux64, as
#: ``ffmpeg-n9.0.2-17-g2a571b6068-linux64-gpl-9.0.tar.xz``, or
#: ``ffmpeg-n9.0.3-linux64-gpl-9.0.tar.xz`` when the build is the release tag
#: itself.
_ASSET = re.compile(
    r"^ffmpeg-n(\d+)\.(\d+)(?:\.(\d+))?(?:-\d+-g[0-9a-f]+)?-linux64-gpl-\d+\.\d+\.tar\.xz$"
)


class Pin(NamedTuple):
    """Where the node image's ffmpeg is downloaded from, and its SHA-256."""

    url: str
    sha256: str


def pin(dockerfile: str) -> Pin:
    """The ffmpeg pin of *dockerfile*.

    :raises ValueError: when either value is missing or malformed.
    """
    found = dict(_ARG.findall(dockerfile))
    url, sha256 = found.get("FFMPEG_URL", ""), found.get("FFMPEG_SHA256", "")
    if not url.startswith("https://") or not _SHA256.fullmatch(sha256):
        msg = (
            "docker/node/Dockerfile must pin ffmpeg before its first FROM as "
            "ARG FFMPEG_URL=https://... and ARG FFMPEG_SHA256=<64 hex digits>"
        )
        raise ValueError(msg)
    return Pin(url, sha256)


def _sha256_of(asset: Mapping[str, Any]) -> str | None:
    """The SHA-256 GitHub lists for *asset*, or ``None`` when it lists none."""
    digest = str(asset.get("digest") or "")
    sha256 = digest.removeprefix("sha256:")
    return (
        sha256 if digest.startswith("sha256:") and _SHA256.fullmatch(sha256) else None
    )


def newest_month_end(releases: Sequence[Mapping[str, Any]]) -> tuple[str, str] | None:
    """The newest month-end build in *releases*, as its URL and SHA-256.

    A month-end release is the last ``autobuild-`` release of a month that has
    ended, that is, of a month before the newest release's. Its build is the
    static GPL linux64 asset of the highest ffmpeg release line. ``None`` when
    there is none, or GitHub gives no SHA-256 for it.
    """
    by_month: dict[str, Mapping[str, Any]] = {}
    for release in releases:
        tag = str(release.get("tag_name", ""))
        match = _TAG.match(tag)
        if match and tag > str(by_month.get(match[1], {}).get("tag_name", "")):
            by_month[match[1]] = release
    if len(by_month) < 2:
        return None
    builds: list[tuple[tuple[int, ...], str, str]] = []
    for asset in by_month[sorted(by_month)[-2]].get("assets", []):
        match = _ASSET.match(str(asset.get("name", "")))
        sha256 = _sha256_of(asset)
        if match and sha256 is not None:
            line = tuple(int(part or 0) for part in match.groups())
            builds.append((line, str(asset["browser_download_url"]), sha256))
    if not builds:
        return None
    _, url, sha256 = max(builds)
    return url, sha256


def _published_sha256(url: str, releases: Sequence[Mapping[str, Any]]) -> str | None:
    """The SHA-256 GitHub lists for the asset at *url*, or ``None``."""
    for release in releases:
        for asset in release.get("assets", []):
            if asset.get("browser_download_url") == url:
                return _sha256_of(asset)
    return None


def _release_of(url: str) -> str:
    """The release tag in a download URL of BtbN's, or ``""``."""
    match = re.search(r"/releases/download/([^/]+)/", url)
    return match[1] if match else ""


def problems(
    pinned: Pin,
    releases: Sequence[Mapping[str, Any]],
    *,
    answers: Callable[[str], bool],
) -> list[str]:
    """What is wrong with *pinned*: gone, changed, or behind the newest month-end build.

    A build is offered only from a release later than the pinned one: before
    the first release of a new month, the newest ended month is the one
    before the pin's, and its build is older.
    """
    found: list[str] = []
    if not answers(pinned.url):
        found.append(f"the pinned ffmpeg no longer downloads: {pinned.url}")
    published = _published_sha256(pinned.url, releases)
    if published is not None and published != pinned.sha256:
        found.append(
            f"GitHub lists the SHA-256 of the pinned ffmpeg as {published}, where "
            f"docker/node/Dockerfile pins {pinned.sha256}: the file changed under its "
            "name, and the image does not build until the pin is checked again"
        )
    newest = newest_month_end(releases)
    if newest is None:
        found.append(
            "no month-end release with a static GPL linux64 build and its SHA-256 "
            "was found among BtbN's releases"
        )
    elif newest[0] != pinned.url and _release_of(newest[0]) > _release_of(pinned.url):
        found.append(_offer(pinned, *newest))
    return found


def _line_of(url: str) -> tuple[int, int] | None:
    """The ffmpeg release line of the build at *url*, as ``(9, 0)``, or ``None``."""
    match = _ASSET.match(url.rpartition("/")[2])
    return (int(match[1]), int(match[2])) if match else None


def _named(line: tuple[int, int] | None) -> str:
    """A release line as messages write it."""
    return (
        "ffmpeg of an unknown release line"
        if line is None
        else f"ffmpeg n{line[0]}.{line[1]}"
    )


def _offer(pinned: Pin, url: str, sha256: str) -> str:
    """What the check says of *url*, a month-end build from a release after the pin's.

    A build of a lower release line than the pinned one is never offered as
    newer: the release then lacks the pinned line, which is a problem of its
    own, and moving the pin to it would take ffmpeg back a release line.
    """
    line, pinned_line = _line_of(url), _line_of(pinned.url)
    if line is not None and pinned_line is not None and line < pinned_line:
        return (
            f"the newest month-end release has no build of the pinned "
            f"{_named(pinned_line)} or a later line with its SHA-256, only of "
            f"{_named(line)} ({url}): keep the pin, and see whether BtbN still "
            "builds that line"
        )
    return (
        f"a newer month-end build of {_named(line)} is out: FFMPEG_URL={url} "
        f"FFMPEG_SHA256={sha256}; move the pin as docker/node/Dockerfile says, once "
        "a node shows its SVT-AV1 is 4"
    )


def _request(url: str, method: str = "GET") -> urllib.request.Request:
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN", "")
    # The token goes to GitHub's API only, never to the host a download
    # redirects to.
    if token and url.startswith("https://api.github.com/"):
        headers["Authorization"] = f"Bearer {token}"
    return urllib.request.Request(url, method=method, headers=headers)


def _releases() -> list[dict[str, Any]]:
    with urllib.request.urlopen(_request(RELEASES), timeout=60) as response:
        return list(json.load(response))


def _answers(url: str) -> bool:
    try:
        with urllib.request.urlopen(_request(url, "HEAD"), timeout=60) as response:
            status: int = response.status
    except OSError:
        return False
    return status == 200


#: The programs ``fetch`` keeps from the build.
_PROGRAMS = ("ffmpeg", "ffprobe")


def _download(url: str, target: Path) -> None:
    """Write the file at *url* to *target*.

    :raises OSError: when the download fails (``urllib.error.URLError`` is one).
    """
    with urllib.request.urlopen(url, timeout=600) as response, target.open("wb") as out:
        shutil.copyfileobj(response, out)


def _complete(bin_dir: Path) -> bool:
    return all((bin_dir / name).is_file() for name in _PROGRAMS)


def _bin_dir(pinned: Pin, cache: Path) -> Path:
    """Where the ``ffmpeg`` and ``ffprobe`` of *pinned* are kept under *cache*."""
    return cache / pinned.sha256 / "bin"


def _unpack(archive: Path, staged: Path) -> None:
    """``<top>/bin/ffmpeg`` and ``<top>/bin/ffprobe`` of *archive*, into *staged*.

    :raises ValueError: when the archive holds no ``bin/ffmpeg`` or no
        ``bin/ffprobe``.
    """
    staged.mkdir()
    with tarfile.open(archive, "r:xz") as tar:
        for member in tar.getmembers():
            parts = PurePosixPath(member.name).parts
            source = tar.extractfile(member) if member.isfile() else None
            if (
                source is None
                or len(parts) != 3
                or parts[1] != "bin"
                or parts[2] not in _PROGRAMS
            ):
                continue
            with source, (staged / parts[2]).open("wb") as out:
                shutil.copyfileobj(source, out)
            (staged / parts[2]).chmod(0o755)
    missing = [f"bin/{name}" for name in _PROGRAMS if not (staged / name).is_file()]
    if missing:
        msg = f"the pinned ffmpeg build holds no {', '.join(missing)}"
        raise ValueError(msg)


def fetch(
    pinned: Pin, cache: Path, *, download: Callable[[str, Path], None] = _download
) -> Path:
    """The ``bin`` directory of the pinned build under *cache*, downloaded once.

    The archive is checked against the pin's SHA-256 before anything in it is
    unpacked, and only ``ffmpeg`` and ``ffprobe`` are kept, in a directory
    named by that SHA-256, which appears whole or not at all.

    :raises ValueError: when the download's SHA-256 is not the pin's, or the
        build lacks one of the two programs; nothing is left behind.
    :raises OSError: when the download fails, or the build cannot take its
        place in *cache*.
    """
    bin_dir = _bin_dir(pinned, cache)
    if _complete(bin_dir):
        return bin_dir
    cache.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=cache) as scratch:
        archive = Path(scratch) / "ffmpeg.tar.xz"
        download(pinned.url, archive)
        with archive.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        if digest != pinned.sha256:
            msg = f"the download of {pinned.url} has SHA-256 {digest}, not the pinned {pinned.sha256}"
            raise ValueError(msg)
        staged = Path(scratch) / "bin"
        _unpack(archive, staged)
        bin_dir.parent.mkdir(exist_ok=True)
        try:
            staged.rename(bin_dir)
        except OSError:
            if not _complete(bin_dir):  # another fetch did not put it there first
                raise
    return bin_dir


def _cache() -> Path:
    base = os.environ.get("XDG_CACHE_HOME", "")
    root = Path(base) if base and Path(base).is_absolute() else Path.home() / ".cache"
    return root / "phonometry" / "ffmpeg"


def _linux_x86_64() -> bool:
    """Whether this machine runs the pinned build: Linux on x86_64."""
    return sys.platform == "linux" and platform.machine() == "x86_64"


def _fetch_here(pinned: Pin) -> int:
    """Fetch *pinned* into the user's cache and print its ``bin`` directory.

    Stderr says what happened: the build was downloaded and checked against
    the pin's SHA-256, or served from the cache, which holds it only once
    checked. A fetch that fails (:func:`fetch`'s ``ValueError`` or
    ``OSError``) says why in one line, prints no directory and returns 1, as
    it does off Linux on x86_64, so that
    ``ffmpeg_dir="$(make -s clip-ffmpeg)" && PATH="$ffmpeg_dir:$PATH" ...``
    stops there.
    """
    if not _linux_x86_64():
        sys.stderr.write(
            "The pinned ffmpeg is BtbN's build for Linux on x86_64. Here, render the clips "
            "with an ffmpeg whose SVT-AV1 is 4.x, or on a node.\n"
        )
        return 1
    cache = _cache()
    cached = _complete(_bin_dir(pinned, cache))
    try:
        bin_dir = fetch(pinned, cache)
    except (ValueError, OSError) as exc:
        sys.stderr.write(
            f"error: the pinned ffmpeg ({pinned.url}) could not be fetched into "
            f"{cache}: {exc}\n"
        )
        return 1
    if cached:
        sys.stderr.write(
            f"ffmpeg served from the cache, checked against SHA-256 {pinned.sha256} "
            f"when it was downloaded from {pinned.url}\n"
        )
    else:
        sys.stderr.write(
            f"ffmpeg downloaded from {pinned.url} and checked against SHA-256 "
            f"{pinned.sha256}\n"
        )
    sys.stdout.write(f"{bin_dir}\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "check", help="compare the pin with BtbN's releases; exit 1 when it should move"
    )
    commands.add_parser(
        "fetch",
        help="download the pinned build here, check it, and print its bin directory",
    )
    args = parser.parse_args(argv)
    pinned = pin(DOCKERFILE.read_text(encoding="utf-8"))
    if args.command == "fetch":
        return _fetch_here(pinned)
    found = problems(pinned, _releases(), answers=_answers)
    for line in found:
        sys.stdout.write(f"::error::{line}\n")
    if not found:
        sys.stdout.write(
            f"The pinned ffmpeg is the newest month-end build, and it downloads: {pinned.url}\n"
        )
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
