#!/usr/bin/env python3
#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every published clip is AV1 in WebM, written by the encoder its manifest names.

The renderer records which ffmpeg encoder wrote each clip's WebM, AV1 NVENC
on a GPU or SVT-AV1 on a CPU, in the third column of
``scripts/animation_fingerprints.txt``. This reads the four WebM variants of
every clip in the assets checkout with ffprobe and names any that is not
AV1, or whose stream says another encoder wrote it: ffmpeg tags the stream it
writes with its own version and the encoder's name, and
:func:`phonometry.io.write_video` keeps that tag. CI never fetches the clips,
so this runs where they are, after a render and before publishing::

    make clip-codecs

The ffprobe on ``PATH`` reads the files; ``make -s clip-ffmpeg`` prints the
directory of the pinned build, to put first there (the Makefile shows how).
Standard library only.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from typing import TYPE_CHECKING, Any

_SCRIPTS = pathlib.Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import animation_fingerprint as fp
import assets_dir
import check_animation_freshness

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping

#: How long ffprobe may take to read the header of one clip [s].
PROBE_TIMEOUT_S = 120


def probe(
    path: pathlib.Path, *, run: Callable[..., Any] = subprocess.run
) -> tuple[str, str]:
    """The codec of *path*'s first video stream, and the encoder its tags name.

    Either is ``""`` when ffprobe reports none; a tag of blanks names none.

    :raises subprocess.CalledProcessError: when ffprobe cannot read *path*.
    :raises subprocess.TimeoutExpired: when ffprobe takes longer than
        :data:`PROBE_TIMEOUT_S`.
    :raises FileNotFoundError: when there is no ffprobe on ``PATH``.
    :raises ValueError: when ffprobe prints something that is not JSON.
    """
    out = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name:stream_tags=encoder",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=PROBE_TIMEOUT_S,
    ).stdout
    streams = json.loads(out).get("streams", [])
    if not streams:
        return "", ""
    tags = {key.lower(): value for key, value in streams[0].get("tags", {}).items()}
    return str(streams[0].get("codec_name", "")), str(tags.get("encoder", "")).strip()


def _stream_problem(name: str, codec: str, tag: str, expected: str) -> str | None:
    """What is wrong with the WebM *name* ffprobe read as *codec* by *tag*, or ``None``.

    ffmpeg writes the tag as its library version and the encoder's name, so
    the encoder is the tag's last word.
    """
    if codec != "av1":
        return f"{name}: {codec or 'no video stream'}, not AV1"
    if not tag:
        return f"{name}: its stream names no encoder; the manifest says {expected}"
    if tag.split()[-1] != expected:
        return f"{name}: written by {tag!r}; the manifest says {expected}"
    return None


def _unreadable(
    error: subprocess.CalledProcessError | subprocess.TimeoutExpired,
) -> str:
    """Why ffprobe could not read a file, on one line: what it said, or that it ran out of time."""
    if isinstance(error, subprocess.TimeoutExpired):
        return f"ffprobe did not finish in {PROBE_TIMEOUT_S} s"
    lines = [line.strip() for line in str(error.stderr or "").splitlines()]
    return (
        "; ".join(line for line in lines if line) or f"exit status {error.returncode}"
    )


def _clip_problems(
    clips_dir: pathlib.Path, clip: str, expected: str, run: Callable[..., Any]
) -> list[str]:
    """What is wrong with the four WebM variants of *clip*, written by *expected*.

    A file ffprobe cannot read, or does not finish reading in
    :data:`PROBE_TIMEOUT_S`, is named with the reason, on one line.

    :raises FileNotFoundError: when there is no ffprobe on ``PATH``.
    :raises ValueError: when ffprobe prints something that is not JSON.
    """
    found: list[str] = []
    for name in check_animation_freshness.outputs(clip):
        path = clips_dir / name
        if path.suffix != ".webm":
            continue
        if not path.is_file():
            found.append(f"{name}: missing")
            continue
        try:
            codec, tag = probe(path, run=run)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            found.append(f"{name}: ffprobe cannot read it ({_unreadable(error)})")
            continue
        if (problem := _stream_problem(name, codec, tag, expected)) is not None:
            found.append(problem)
    return found


def problems(
    clips_dir: pathlib.Path,
    clips: Iterable[str],
    encoders: Mapping[str, str],
    *,
    run: Callable[..., Any] = subprocess.run,
) -> list[str]:
    """What is wrong with the WebM variants of *clips* in *clips_dir*; empty when nothing is.

    *encoders* is the manifest's encoder column (:func:`animation_fingerprint.read_encoders`).

    :raises FileNotFoundError: when there is no ffprobe on ``PATH``.
    :raises ValueError: when ffprobe prints something that is not JSON.
    """
    found: list[str] = []
    for clip in sorted(clips):
        if clip not in encoders:
            found.append(f"{clip}: no encoder recorded in the manifest")
            continue
        found.extend(_clip_problems(clips_dir, clip, encoders[clip], run))
    return found


def main(argv: list[str] | None = None) -> int:
    """Name every clip whose WebM is not AV1 from its recorded encoder; 1 when any is.

    :raises FileNotFoundError: when there is no ffprobe on ``PATH``, or when a
        clip steps an FDTD engine and there is no ``engine-digests.json``.
    :raises ValueError: when ffprobe prints something that is not JSON, or
        when a clip steps an FDTD engine and ``engine-digests.json`` does not
        hold the engines' digests.
    """
    argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0]).parse_args(
        argv
    )
    clips = fp.fingerprints(_SCRIPTS.parent)
    found = problems(assets_dir.clips_dir(), clips, fp.read_encoders())
    for line in found:
        sys.stdout.write(f"::error::{line}\n")
    if not found:
        sys.stdout.write(
            f"All {len(clips)} clips are AV1, from the encoder their manifest names.\n"
        )
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
