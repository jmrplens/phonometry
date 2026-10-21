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
checked on a node first. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
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
        url, sha256 = newest
        found.append(
            f"a newer month-end build is out: FFMPEG_URL={url} FFMPEG_SHA256={sha256}; "
            "move the pin as docker/node/Dockerfile says, once a node shows its SVT-AV1 is 4"
        )
    return found


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "check", help="compare the pin with BtbN's releases; exit 1 when it should move"
    )
    parser.parse_args(argv)
    pinned = pin(DOCKERFILE.read_text(encoding="utf-8"))
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
