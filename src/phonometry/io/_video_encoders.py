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
frame size, and for VAAPI the device; a failure is not, because a GPU
encoder that failed for want of a free session works a second later.

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
import re
import shutil
import subprocess  # nosec B404 - only ffmpeg, found from matplotlib's rcParams, with an argument list and no shell
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, Literal

from .._internal.json_input import escaped
from .._internal.programs import past_the_working_directory
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

#: The library each CPU encoder comes from, as an install hint names it.
_CPU_LIBRARIES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "libsvtav1": "SVT-AV1",
        "libvpx-vp9": "libvpx",
        "libx265": "x265",
        "libx264": "x264",
    }
)

#: What each kind needs around the encoder: a filter that hands the frames
#: to the device, and the pixel format. VAAPI also needs its device named
#: before the input (:func:`video_arguments`).
_HARDWARE: Final[Mapping[Hardware, tuple[str | None, str | None]]] = MappingProxyType(
    {
        "cpu": (None, "yuv420p"),
        "nvenc": (None, "yuv420p"),
        "qsv": (None, "nv12"),
        "vaapi": ("format=nv12,hwupload", None),
        "videotoolbox": (None, "yuv420p"),
    }
)

#: The GPU device VAAPI encodes on unless ``VideoOptions.vaapi_device``
#: names another: the first GPU of a Linux machine.
DEFAULT_VAAPI_DEVICE: Final = "/dev/dri/renderD128"

#: Seconds a trial encode or a ``-version`` run may take.
_RUN_TIMEOUT_S: Final = 60.0

#: How many of the last characters ffmpeg wrote on stderr a message quotes.
_STDERR_TAIL_CHARS: Final = 400

#: Keeps a console window from flashing up for every ffmpeg run on Windows
#: (from a process with no console: pythonw, or a notebook kernel a GUI front
#: end started), as matplotlib's own movie writers do; the flag exists only
#: there, and is 0 elsewhere.
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
    """No encoder can write the video, ffmpeg cannot start or fails while writing it, or the directory or the disk does not take the file."""


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
_PASSED: set[tuple[str, str, str, int, int, str]] = set()


def find_ffmpeg() -> str:
    """The ffmpeg matplotlib would run: ``rcParams["animation.ffmpeg_path"]``, by the path it was found at.

    On Windows, which looks a bare name up in the working directory before
    ``PATH``, an ffmpeg there is passed over for the one on ``PATH``, and the
    log says so at INFO on ``phonometry.io``; one found nowhere else is
    refused. An ffmpeg named with a directory, or found in a working
    directory that ``PATH`` itself lists, is the user's own choice, and runs
    as found.

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
    installed = past_the_working_directory(named, found)
    if installed is None:
        msg = (
            f"ffmpeg was found only in the working directory ({escaped(found)}), which Windows "
            "searches before PATH; phonometry does not run a program from there. "
            "Put ffmpeg on PATH, or name it by its full path in "
            "rcParams['animation.ffmpeg_path']"
        )
        raise FFmpegNotFoundError(msg)
    if installed != found:
        _LOG.info(
            "running %s from PATH, not %s from the working directory, which "
            "Windows searches first",
            escaped(installed),
            escaped(found),
        )
    return installed


def _run(
    command: list[str], *, stdin: bytes | None = None
) -> subprocess.CompletedProcess[bytes]:
    """Run ffmpeg once and wait, with a timeout, from an argument list rather than through a shell.

    An ffmpeg that is a batch file (``.bat`` or ``.cmd``) is the exception:
    Windows runs one through ``cmd.exe``, which reads the arguments by its
    own rules.

    ffmpeg reads *stdin*, or nothing: it never inherits this process's own
    input. On Windows a program started on a pipe that another thread of
    this process is reading (a node's input watcher) blocks as it starts,
    until that read ends; elsewhere ffmpeg would read what the caller's
    input holds.
    """
    return subprocess.run(  # nosec B603 - an argument list to the ffmpeg find_ffmpeg resolved; no shell
        command,
        input=stdin,
        stdin=subprocess.DEVNULL if stdin is None else None,
        capture_output=True,
        timeout=_RUN_TIMEOUT_S,
        check=False,
        creationflags=NO_WINDOW,
    )


def _tail(stderr: bytes) -> str:
    """The last of what ffmpeg wrote on stderr, as text, for a message or the log.

    Its control characters and marks that reorder text are written as their
    escapes (:func:`escaped`), so that quoting it cannot move the caller's
    terminal.
    """
    return escaped(stderr.decode(errors="replace")[-_STDERR_TAIL_CHARS:].strip())


def _listed(path: str, flag: str) -> bytes:
    """What the ffmpeg at *path* writes on stdout for *flag*, ``-version`` or ``-encoders``.

    :raises VideoEncoderError: when it does not start, does not finish in
        time, or exits with an error; the message quotes that run's own
        stderr.
    """
    try:
        done = _run([path, "-hide_banner", flag])
    except (OSError, subprocess.TimeoutExpired) as exc:
        msg = f"{escaped(str(path))} did not run: {exc}"
        raise VideoEncoderError(msg) from exc
    if done.returncode:
        said = _tail(done.stderr) or "nothing on stderr"
        msg = f"{escaped(str(path))} did not run: {said} ({flag} exited with status {done.returncode})"
        raise VideoEncoderError(msg)
    return done.stdout


def describe(path: str) -> FFmpeg:
    """The version line and the compiled encoders of the ffmpeg at *path*.

    Read once per binary and process: the key is the path with the file's
    modification time and size, so an ffmpeg replaced on disk is read again.
    The encoders are listed only once ``-version`` has succeeded.

    :raises VideoEncoderError: when that ffmpeg is gone, cannot be read, or
        does not run (the message names *path*, and quotes the stderr of the
        run that failed).
    """
    try:
        status = Path(path).stat()
    except OSError as exc:
        msg = f"{escaped(str(path))} did not run: {exc}"
        raise VideoEncoderError(msg) from exc
    key = (path, status.st_mtime_ns, status.st_size)
    with _LOCK:
        known = _DESCRIBED.get(key)
    if known is not None:
        return known
    version = _listed(path, "-version")
    listing = _listed(path, "-encoders")
    lines = version.decode(errors="replace").splitlines()
    matches = (
        _ENCODER_LINE.match(line)
        for line in listing.decode(errors="replace").splitlines()
    )
    found = FFmpeg(
        path=path,
        version=lines[0] if lines else "",
        encoders=frozenset(match.group(1) for match in matches if match),
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


def _pad(width: int, height: int, pad_color: str) -> str | None:
    """The filter that pads an odd frame to even sides (``yuv420p`` halves the chroma).

    ``None`` for a frame whose sides are both even, which needs no padding.
    """
    if width % 2 == 0 and height % 2 == 0:
        return None
    return f"pad=ceil(iw/2)*2:ceil(ih/2)*2:color={pad_color}"


def _filters(*steps: str | None) -> tuple[str, ...]:
    """The filter chain: the steps given, in their order, without the absent ones."""
    return tuple(step for step in steps if step)


def video_arguments(
    choice: EncoderChoice,
    *,
    quality: Quality,
    options: tuple[str, ...],
    container: Container,
    width: int,
    height: int,
    pad_color: str,
    vaapi_device: str,
) -> VideoArguments:
    """The encoder part of the command for an encoder the library chose.

    A VAAPI encoder encodes on *vaapi_device*; the others take no device.
    """
    upload, pixel_format = _HARDWARE[choice.hardware]
    pixels = () if pixel_format is None else ("-pix_fmt", pixel_format)
    before = ("-vaapi_device", vaapi_device) if choice.hardware == "vaapi" else ()
    return VideoArguments(
        before_input=before,
        filters=_filters(_pad(width, height, pad_color), upload),
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
        filters=_filters(_pad(width, height, pad_color)),
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


def trial(
    ffmpeg: FFmpeg, choice: EncoderChoice, *, width: int, height: int, vaapi_device: str
) -> bool:
    """Whether *choice* encodes one black frame of this size here, now.

    A VAAPI encoder is tried on *vaapi_device*, and its success is
    remembered for that device only. A failure is logged at DEBUG on
    ``phonometry.io``, with the last of what ffmpeg wrote on stderr.
    """
    device = vaapi_device if choice.hardware == "vaapi" else ""
    key = (ffmpeg.path, ffmpeg.version, choice.name, width, height, device)
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
        vaapi_device=vaapi_device,
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
    except (OSError, subprocess.TimeoutExpired) as exc:
        _LOG.debug("%s failed its trial at %dx%d: %s", choice.name, width, height, exc)
        return False
    if done.returncode != 0:
        # Why a GPU encoder was passed over (no device, no free session, a
        # driver too old) is in its words, for whoever turns DEBUG on.
        _LOG.debug(
            "%s failed its trial at %dx%d (status %d): %s",
            choice.name,
            width,
            height,
            done.returncode,
            _tail(done.stderr),
        )
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
    vaapi_device: str,
) -> EncoderChoice:
    """The first encoder that passes its trial, logged on ``phonometry.io``.

    A VAAPI encoder is tried on *vaapi_device*.

    :raises VideoEncoderError: when none does; for an explicit ``encoder``
        the message lists the encoders that pass here.
    """
    tried = []
    for choice in _candidates(
        ffmpeg, encoder=encoder, codec=codec, container=container
    ):
        tried.append(choice.name)
        if trial(ffmpeg, choice, width=width, height=height, vaapi_device=vaapi_device):
            _LOG.info(
                "writing %s with %s (%s, %s)",
                container,
                choice.name,
                choice.hardware,
                choice.codec,
            )
            return choice
    codecs = CONTAINER_CODECS[container] if codec is None else (codec,)
    msg = (
        f"encoder={encoder!r} cannot write {'/'.join(codecs)} into .{container} with "
        f"{escaped(ffmpeg.path)} ({escaped(ffmpeg.version)}); "
        f"tried {', '.join(tried) or 'nothing it has'}."
    )
    if encoder != "auto":
        working = [
            c.name
            for c in _candidates(
                ffmpeg, encoder="auto", codec=codec, container=container
            )
            if trial(ffmpeg, c, width=width, height=height, vaapi_device=vaapi_device)
        ]
        msg += f" Working here: {', '.join(working) or 'none'}."
    else:
        msg += f" Install an ffmpeg built with {_cpu_libraries(codecs)}."
    raise VideoEncoderError(msg)


def _cpu_libraries(codecs: tuple[Codec, ...]) -> str:
    """The libraries whose CPU encoders write *codecs*, best first: ``"SVT-AV1 or libvpx"``."""
    libraries = [_CPU_LIBRARIES[FFMPEG_NAMES["cpu", codec]] for codec in codecs]
    *rest, last = libraries or [""]
    return f"{', '.join(rest)} or {last}" if rest else last
