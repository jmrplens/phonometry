#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Which ffmpeg encoder writes a video, found by trying it (private).

ffmpeg lists the encoders it was built with (``-encoders``), and the list
says nothing about whether one can run here: ``av1_nvenc`` is compiled into
most Linux builds and fails on every machine without an NVIDIA GPU, and one
that has the GPU can still run out of encode sessions for a moment. So the
writer does not trust the list. Each candidate, in the order ``"auto"``
tries them (NVENC, Quick Sync, VAAPI, VideoToolbox, then the CPU), encodes
one black frame of the real frame size to ffmpeg's null muxer, and the first
that succeeds writes the video. A success is remembered for the rest of the
process, keyed by the ffmpeg binary and its version, the encoder and the
frame size; a failure is not, because a GPU encoder that failed for want of
a free session works a second later.

On the CPU the AV1 encoder is SVT-AV1; when it is absent a WebM gets VP9
(libvpx) and an MP4 HEVC (x265) or H.264 (x264). libaom, the reference AV1
encoder, is never chosen: it is built for coding experiments, not for speed.
No encoder is chosen for a GIF: ffmpeg's palette filter writes it on the
CPU, with no trial.

This module also owns the two errors of the video writer and the one place
its ffmpeg command line is assembled, for the trial and for the encode
alike.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess  # nosec B404 - only ffmpeg, found from matplotlib's rcParams, with an argument list and no shell
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, Literal

from ._video_quality import ENCODER_QUALITY, GIF_PALETTE, Quality

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

#: Where the video writer says which encoder it chose.
_LOG = logging.getLogger("phonometry.io")

#: Who encodes: ``"auto"`` tries every kind in :data:`AUTO_ORDER`.
Encoder = Literal["auto", "cpu", "nvenc", "qsv", "vaapi", "videotoolbox"]
#: One kind of encoder.
Hardware = Literal["cpu", "nvenc", "qsv", "vaapi", "videotoolbox"]
#: The video codec, where the container offers a choice.
Codec = Literal["av1", "vp9", "hevc", "h264"]
#: The file format, read from the path's suffix.
Container = Literal["webm", "mp4", "gif"]

#: The codecs each container holds, best first. A GIF has no codec choice.
CONTAINER_CODECS: Final[Mapping[Container, tuple[Codec, ...]]] = MappingProxyType(
    {"webm": ("av1", "vp9"), "mp4": ("av1", "hevc", "h264"), "gif": ()}
)

#: The order ``"auto"`` tries the kinds of encoder in.
AUTO_ORDER: Final[tuple[Hardware, ...]] = (
    "nvenc",
    "qsv",
    "vaapi",
    "videotoolbox",
    "cpu",
)

#: ffmpeg's name for each (kind, codec) it can encode. No libaom.
FFMPEG_NAMES: Final[Mapping[tuple[Hardware, Codec], str]] = MappingProxyType(
    {
        ("cpu", "av1"): "libsvtav1",
        ("cpu", "vp9"): "libvpx-vp9",
        ("cpu", "hevc"): "libx265",
        ("cpu", "h264"): "libx264",
        ("nvenc", "av1"): "av1_nvenc",
        ("nvenc", "hevc"): "hevc_nvenc",
        ("nvenc", "h264"): "h264_nvenc",
        ("qsv", "av1"): "av1_qsv",
        ("qsv", "vp9"): "vp9_qsv",
        ("qsv", "hevc"): "hevc_qsv",
        ("qsv", "h264"): "h264_qsv",
        ("vaapi", "av1"): "av1_vaapi",
        ("vaapi", "vp9"): "vp9_vaapi",
        ("vaapi", "hevc"): "hevc_vaapi",
        ("vaapi", "h264"): "h264_vaapi",
        ("videotoolbox", "hevc"): "hevc_videotoolbox",
        ("videotoolbox", "h264"): "h264_videotoolbox",
    }
)

#: What each kind needs around the encoder: options before the input, a
#: filter that hands the frames to the device, and the pixel format.
_HARDWARE: Final[Mapping[Hardware, tuple[tuple[str, ...], str | None, str | None]]] = (
    MappingProxyType(
        {
            "cpu": ((), None, "yuv420p"),
            "nvenc": ((), None, "yuv420p"),
            "qsv": ((), None, "nv12"),
            "vaapi": (
                ("-vaapi_device", "/dev/dri/renderD128"),
                "format=nv12,hwupload",
                None,
            ),
            "videotoolbox": ((), None, "yuv420p"),
        }
    )
)

#: Seconds a trial encode or a ``-version`` run may take.
_RUN_TIMEOUT_S: Final = 60.0

#: Keeps a console window from flashing up for every ffmpeg run on Windows
#: (from a notebook or pythonw), as matplotlib's own movie writers do; the
#: flag exists only there, and is 0 elsewhere.
NO_WINDOW: Final[int] = getattr(subprocess, "CREATE_NO_WINDOW", 0)

_INSTALL_HINT = (
    "install ffmpeg (conda install ffmpeg, apt install ffmpeg, brew install "
    "ffmpeg, winget install ffmpeg) or point that rcParam at it"
)

#: A line of ``ffmpeg -encoders`` that names a video encoder.
_ENCODER_LINE = re.compile(r"^\s*V[A-Z.]{5}\s+([A-Za-z0-9_-]+)\s")


class FFmpegNotFoundError(FileNotFoundError):
    """ffmpeg is not where matplotlib looks for it, or cannot run here."""


class VideoEncoderError(RuntimeError):
    """No encoder can write the video, or ffmpeg failed while writing it."""


@dataclass(frozen=True)
class EncoderChoice:
    """One encoder: its kind, the codec it writes and ffmpeg's name for it."""

    hardware: Hardware
    codec: Codec
    name: str


@dataclass(frozen=True)
class FFmpeg:
    """One ffmpeg binary: where it is, its version line, its encoders."""

    path: str
    version: str
    encoders: frozenset[str]


@dataclass(frozen=True)
class VideoArguments:
    """The parts of an ffmpeg command line that depend on the encoder."""

    before_input: tuple[str, ...]
    filters: tuple[str, ...]
    codec_arguments: tuple[str, ...]
    muxer_options: tuple[str, ...]


_LOCK = threading.Lock()
_DESCRIBED: dict[tuple[str, int, int], FFmpeg] = {}
_PASSED: set[tuple[str, str, str, int, int]] = set()


def _outside_the_working_directory(named: str, found: str) -> None:
    """Refuse, on Windows, an ffmpeg found only because Windows looks in the working directory first.

    A bare name such as ``"ffmpeg"`` is looked up there before ``PATH``, so
    an ``ffmpeg.exe`` or ``ffmpeg.bat`` left in a notebook's folder would run
    in place of the one the user installed. A name with a directory, or a
    working directory that ``PATH`` itself lists, is the user's own choice.

    :raises FFmpegNotFoundError: for such an ffmpeg.
    """
    if sys.platform != "win32" or Path(named).name != named:
        return
    here = Path.cwd().resolve()
    listed = {
        Path(entry).resolve()
        for entry in os.environ.get("PATH", "").split(os.pathsep)
        if entry
    }
    if Path(found).resolve().parent == here and here not in listed:
        msg = (
            f"ffmpeg was found only in the working directory ({found}), which Windows "
            "searches before PATH; phonometry does not run a program from there. "
            "Put ffmpeg on PATH, or name it by its full path in "
            "rcParams['animation.ffmpeg_path']"
        )
        raise FFmpegNotFoundError(msg)


def find_ffmpeg() -> str:
    """The ffmpeg matplotlib would run: ``rcParams["animation.ffmpeg_path"]``.

    :raises FFmpegNotFoundError: when that name is not on ``PATH``, in
        Pyodide, which cannot start a program, or on Windows when it was
        found only in the working directory.
    :raises ImportError: when matplotlib is not installed.
    """
    if sys.platform == "emscripten":
        msg = (
            "Pyodide cannot start programs, so it cannot run ffmpeg; write the "
            "video from Python on a desktop, a server or a node"
        )
        raise FFmpegNotFoundError(msg)
    try:
        import matplotlib as mpl
    except ImportError as exc:  # pragma: no cover - the base install has no plot
        msg = 'Writing a video requires matplotlib. Install it with: pip install "phonometry[plot]"'
        raise ImportError(msg) from exc
    named = str(mpl.rcParams["animation.ffmpeg_path"])
    found = shutil.which(named)
    if found is None:
        msg = (
            f"ffmpeg was not found: {named!r}, the program "
            f"rcParams['animation.ffmpeg_path'] names, is not on PATH; {_INSTALL_HINT}"
        )
        raise FFmpegNotFoundError(msg)
    _outside_the_working_directory(named, found)
    return found


def _run(
    command: list[str], *, stdin: bytes | None = None
) -> subprocess.CompletedProcess[bytes]:
    """Run ffmpeg once and wait, with a timeout; never through a shell."""
    return subprocess.run(  # nosec B603 - an argument list to the ffmpeg find_ffmpeg resolved; no shell
        command,
        input=stdin,
        capture_output=True,
        timeout=_RUN_TIMEOUT_S,
        check=False,
        creationflags=NO_WINDOW,
    )


def describe(path: str) -> FFmpeg:
    """The version line and the compiled encoders of the ffmpeg at *path*.

    Read once per binary and process: the key is the path with the file's
    modification time and size, so an ffmpeg replaced on disk is read again.

    :raises VideoEncoderError: when that ffmpeg does not run.
    """
    status = Path(path).stat()
    key = (path, status.st_mtime_ns, status.st_size)
    with _LOCK:
        known = _DESCRIBED.get(key)
    if known is not None:
        return known
    try:
        version = _run([path, "-hide_banner", "-version"])
        listing = _run([path, "-hide_banner", "-encoders"])
    except (OSError, subprocess.TimeoutExpired) as exc:
        msg = f"{path} did not run: {exc}"
        raise VideoEncoderError(msg) from exc
    if version.returncode or listing.returncode:
        msg = f"{path} did not run: {(version.stderr or listing.stderr).decode(errors='replace')[-400:]}"
        raise VideoEncoderError(msg)
    lines = version.stdout.decode(errors="replace").splitlines()
    found = FFmpeg(
        path=path,
        version=lines[0] if lines else "",
        encoders=frozenset(
            match.group(1)
            for line in listing.stdout.decode(errors="replace").splitlines()
            if (match := _ENCODER_LINE.match(line))
        ),
    )
    with _LOCK:
        _DESCRIBED[key] = found
    return found


def _container_options(container: Container, codec: Codec | None) -> tuple[str, ...]:
    """What the muxer needs: HEVC tagged ``hvc1`` and a front-loaded MP4."""
    if container != "mp4":
        return ()
    tag = ("-tag:v", "hvc1") if codec == "hevc" else ()
    return (*tag, "-movflags", "+faststart")


def _pad(width: int, height: int, pad_color: str) -> tuple[str, ...]:
    """Pad an odd frame to even sides (``yuv420p`` halves the chroma)."""
    if width % 2 == 0 and height % 2 == 0:
        return ()
    return (f"pad=ceil(iw/2)*2:ceil(ih/2)*2:color={pad_color}",)


def video_arguments(
    choice: EncoderChoice,
    *,
    quality: Quality,
    options: tuple[str, ...],
    container: Container,
    width: int,
    height: int,
    pad_color: str,
) -> VideoArguments:
    """The encoder part of the command for an encoder the library chose."""
    before, upload, pixel_format = _HARDWARE[choice.hardware]
    pixels = () if pixel_format is None else ("-pix_fmt", pixel_format)
    return VideoArguments(
        before_input=before,
        filters=(*_pad(width, height, pad_color), *((upload,) if upload else ())),
        codec_arguments=(
            "-c:v",
            choice.name,
            *ENCODER_QUALITY[choice.name, quality],
            *pixels,
            *options,
        ),
        muxer_options=_container_options(container, choice.codec),
    )


def raw_arguments(
    name: str,
    *,
    options: tuple[str, ...],
    container: Container,
    width: int,
    height: int,
    pad_color: str,
) -> VideoArguments:
    """The encoder part of the command for an encoder the caller named.

    Passed through as given: no preset, no pixel format, no check that the
    container holds what the encoder writes. The even-size pad stays, since
    every 4:2:0 encoder needs it, and so does an MP4's ``+faststart``.
    """
    return VideoArguments(
        before_input=(),
        filters=_pad(width, height, pad_color),
        codec_arguments=("-c:v", name, *options),
        muxer_options=_container_options(container, None),
    )


def gif_arguments(*, quality: Quality, options: tuple[str, ...]) -> VideoArguments:
    """A GIF: the palette is computed and applied in one run of ffmpeg.

    ``split`` hands every frame to ``palettegen``, which waits for the last
    one, and to ``paletteuse``, which ffmpeg holds back until the palette
    exists; the frames come through the pipe once, but ffmpeg keeps every
    one of them in memory until the last has arrived, so a long GIF at a
    large size costs ffmpeg the memory of all its frames.
    """
    colors, dither = GIF_PALETTE[quality]
    graph = (
        f"split[a][b];[a]palettegen=max_colors={colors}:stats_mode=diff[p];"
        f"[b][p]paletteuse=dither={dither}"
    )
    return VideoArguments(
        before_input=(),
        filters=(graph,),
        codec_arguments=options,
        muxer_options=("-loop", "0"),
    )


def ffmpeg_command(
    ffmpeg: str,
    *,
    width: int,
    height: int,
    rate: str,
    video: VideoArguments,
    muxer: str,
    output: str,
    frames: int | None = None,
) -> list[str]:
    """The whole command: raw RGBA frames on stdin, one video out."""
    command = [
        ffmpeg,
        "-hide_banner",
        "-nostats",
        "-loglevel",
        "error",
        "-y",
        *video.before_input,
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgba",
        "-s",
        f"{width}x{height}",
        "-r",
        rate,
        "-i",
        "-",
    ]
    if frames is not None:
        command += ["-frames:v", str(frames)]
    if video.filters:
        command += ["-vf", ",".join(video.filters)]
    return [
        *command,
        *video.codec_arguments,
        "-an",
        *video.muxer_options,
        "-f",
        muxer,
        output,
    ]


def trial(ffmpeg: FFmpeg, choice: EncoderChoice, *, width: int, height: int) -> bool:
    """Whether *choice* encodes one black frame of this size here, now."""
    key = (ffmpeg.path, ffmpeg.version, choice.name, width, height)
    with _LOCK:
        if key in _PASSED:
            return True
    video = video_arguments(
        choice,
        quality="standard",
        options=(),
        container="webm",
        width=width,
        height=height,
        pad_color="black",
    )
    command = ffmpeg_command(
        ffmpeg.path,
        width=width,
        height=height,
        rate="1",
        video=video,
        muxer="null",
        output="-",
        frames=1,
    )
    try:
        done = _run(command, stdin=bytes(width * height * 4))
    except (OSError, subprocess.TimeoutExpired):
        return False
    if done.returncode != 0:
        return False
    with _LOCK:
        _PASSED.add(key)
    return True


def _candidates(
    ffmpeg: FFmpeg, *, encoder: Encoder, codec: Codec | None, container: Container
) -> Iterator[EncoderChoice]:
    """The compiled-in encoders to try, in order."""
    kinds = AUTO_ORDER if encoder == "auto" else (encoder,)
    codecs = CONTAINER_CODECS[container] if codec is None else (codec,)
    for kind in kinds:
        for each in codecs:
            name = FFMPEG_NAMES.get((kind, each))
            if name is not None and name in ffmpeg.encoders:
                yield EncoderChoice(kind, each, name)


def choose(
    ffmpeg: FFmpeg,
    *,
    encoder: Encoder,
    codec: Codec | None,
    container: Container,
    width: int,
    height: int,
) -> EncoderChoice:
    """The first encoder that passes its trial, logged on ``phonometry.io``.

    :raises VideoEncoderError: when none does; for an explicit ``encoder``
        the message lists the encoders that pass here.
    """
    tried = []
    for choice in _candidates(
        ffmpeg, encoder=encoder, codec=codec, container=container
    ):
        tried.append(choice.name)
        if trial(ffmpeg, choice, width=width, height=height):
            _LOG.info(
                "writing %s with %s (%s, %s)",
                container,
                choice.name,
                choice.hardware,
                choice.codec,
            )
            return choice
    wanted = "/".join(CONTAINER_CODECS[container] if codec is None else (codec,))
    msg = (
        f"encoder={encoder!r} cannot write {wanted} into .{container} with "
        f"{ffmpeg.path} ({ffmpeg.version}); tried {', '.join(tried) or 'nothing it has'}."
    )
    if encoder != "auto":
        working = [
            c.name
            for c in _candidates(
                ffmpeg, encoder="auto", codec=codec, container=container
            )
            if trial(ffmpeg, c, width=width, height=height)
        ]
        msg += f" Working here: {', '.join(working) or 'none'}."
    else:
        msg += " Install an ffmpeg built with SVT-AV1, libvpx or x264."
    raise VideoEncoderError(msg)
