#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Writing a matplotlib animation to WebM, MP4 or GIF with ffmpeg (private).

:func:`write_video` draws every frame of the animation with Agg, as raw RGBA
bytes, and streams them into ffmpeg's stdin: no frame is written to disk, so
a long animation costs this process the memory of one frame. A GIF is the
exception inside ffmpeg, whose palette filter holds every frame until the
last one has arrived. The file appears at ``path`` only once ffmpeg has
finished it. Until then ffmpeg writes to a hidden partial file beside it, a
name of its own for each write, which is removed whatever fails (ffmpeg
exits, the disk fills, the animation's own drawing raises), so a failed
write never leaves a truncated video at ``path`` and never replaces a good
one; a partial file the system will not let go (a scanner holding it on
Windows) stays under its hidden name, and the error raised is still the
one that stopped the write. A finished video that the system will not let
take ``path``'s place (on Windows, while a player holds the old file open)
stays under its partial name, and the error says where.

How a video is encoded is one record, :class:`VideoOptions`, which checks
its fields when it is built; what depends on the file (the container its
suffix names, and the codecs that container holds) is checked once the
path is known, still before anything starts.

Every frame is saved under the same settings whatever the caller's matplotlib
configuration says: the standard bounding box (a ``"tight"`` box can change
size from one frame to the next, which no encoder accepts), the figure's own
dpi and its own facecolor, composited on white where it is transparent,
because a video has no alpha. A figure whose size in pixels is odd is padded
by one row or column of that colour, since the 4:2:0 pixel format every
browser plays halves the chroma.
"""

from __future__ import annotations

import contextlib
import io
import math
import os
import subprocess  # nosec B404 - frames piped to the ffmpeg find_ffmpeg resolved; no shell
import threading
import uuid
from collections import deque
from collections.abc import Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final, cast, get_args

import numpy as np

from .._internal.display import RichDisplay
from .._internal.validation import require_choice, require_positive, require_scalar
from ._video_encoders import (
    CONTAINER_CODECS,
    DEFAULT_VAAPI_DEVICE,
    FFMPEG_NAMES,
    NO_WINDOW,
    Codec,
    Container,
    Encoder,
    EncoderChoice,
    FFmpeg,
    FFmpegNotFoundError,
    VideoArguments,
    VideoEncoderError,
    choose,
    describe,
    ffmpeg_command,
    find_ffmpeg,
    gif_arguments,
    raw_arguments,
    video_arguments,
)
from ._video_quality import Quality

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

    from matplotlib.animation import AbstractMovieWriter, Animation
    from matplotlib.figure import Figure

__all__ = ["FFmpegNotFoundError", "VideoEncoderError", "VideoOptions", "write_video"]

_SUFFIXES: Final[Mapping[str, Container]] = MappingProxyType(
    {".webm": "webm", ".mp4": "mp4", ".gif": "gif"}
)
# Read from the Literal types, so a choice added there is accepted here.
_ENCODERS: Final[tuple[Encoder, ...]] = get_args(Encoder)
_CODECS: Final[tuple[Codec, ...]] = get_args(Codec)
_QUALITIES: Final[tuple[Quality, ...]] = get_args(Quality)

#: How many of ffmpeg's last stderr lines an error quotes.
_STDERR_LINES: Final = 20

#: Seconds ffmpeg may take to finish once its input is closed.
_EXIT_TIMEOUT_S: Final = 600.0

#: Seconds a stopped ffmpeg is given to exit, so that the files it held are
#: released before the caller removes them.
_STOP_TIMEOUT_S: Final = 5.0

#: Every ffmpeg this process is running for a video, and the lock that guards
#: them: a process about to end at once stops them from another thread
#: (:func:`stop_running_encoders`).
_RUNNING: set[subprocess.Popen[bytes]] = set()
_RUNNING_LOCK = threading.Lock()

_MATPLOTLIB_HINT = 'Writing a video requires matplotlib. Install it with: pip install "phonometry[plot]"'


@dataclass(frozen=True, kw_only=True)
class VideoOptions(RichDisplay):
    """How a video is encoded: by which encoder, in which codec, at what quality and rate.

    One record for every writer of a video (:func:`write_video` and the
    simulation writers), checked when it is built. What depends on the file,
    the container its suffix names and the codecs that container holds, is
    checked when the path is known, still before anything starts.

    :param encoder: ``"auto"`` (default: the GPU encoders first, NVENC,
        Quick Sync, VAAPI and VideoToolbox, each tried on one black frame of
        the video's size, then the CPU), ``"cpu"``, ``"nvenc"``, ``"qsv"``,
        ``"vaapi"`` or ``"videotoolbox"``. A GIF is always written on the CPU.
    :param codec: ``"av1"``, ``"vp9"``, ``"hevc"`` or ``"h264"``; ``None``
        (default) takes the best the container holds that the encoder
        writes, AV1 first. An ``encoder`` of your own must write it: NVENC
        writes no VP9, VideoToolbox only HEVC and H.264. A GIF has no codec.
    :param quality: ``"high"``, ``"standard"`` (default) or ``"small"``:
        each encoder's constant-quality setting, or a GIF's palette size and
        dither.
    :param fps: Frames per second; ``None`` (default) takes the animation's
        ``interval``, and a simulation video plays at 30.
    :param ffmpeg_encoder: An ffmpeg encoder name to use as it is, with
        ``ffmpeg_options``: no trial, no preset, no pixel format, and no
        check that the container holds what it writes. Not with a GIF, nor
        with an ``encoder`` or ``codec`` of your own.
    :param ffmpeg_options: More ffmpeg output options, as separate strings,
        written after the encoder's preset and pixel format (so a repeated
        one of those wins) and before the container's own options, which
        stay: an MP4's ``+faststart``, and its HEVC tag when the library
        chose HEVC (not for an ``ffmpeg_encoder`` of your own), and a GIF's
        endless loop; held as a tuple.
    :param vaapi_device: The GPU device a VAAPI encoder encodes on, as the
        path of its device file on the machine that encodes (the node's, for
        a video written on a node); ``"/dev/dri/renderD128"`` (default) is
        the first GPU of a Linux machine. Used whenever the library tries or
        uses a VAAPI encoder; an ``ffmpeg_encoder`` of your own takes none of
        the library's device setup.
    :raises TypeError: for an ``encoder``, ``codec`` or ``quality`` that is
        not a text, a ``fps`` that is not one number (a bool is not one), an
        ``ffmpeg_encoder`` that is not a text, ``ffmpeg_options`` that are
        not a sequence of separate texts, or a ``vaapi_device`` that is not a
        text.
    :raises ValueError: for a choice outside its options, a ``fps`` that is
        not a positive finite number, an ``ffmpeg_encoder`` that does not
        name an encoder, an empty ``vaapi_device``, an ``ffmpeg_encoder``,
        ``ffmpeg_options`` or ``vaapi_device`` that hold a NUL character,
        which no argument of a program can carry, an ``ffmpeg_encoder``
        together with an ``encoder`` or a ``codec`` of your own, or a
        ``codec`` that your ``encoder`` does not write.
    """

    encoder: Encoder = "auto"
    codec: Codec | None = None
    quality: Quality = "standard"
    fps: float | None = None
    ffmpeg_encoder: str | None = None
    ffmpeg_options: Sequence[str] = ()
    vaapi_device: str = DEFAULT_VAAPI_DEVICE

    def __post_init__(self) -> None:
        """Refuse a field of the wrong type, or outside its options, when the record is built."""
        encoder = require_choice(self.encoder, "encoder", _ENCODERS)
        codec = (
            None if self.codec is None else require_choice(self.codec, "codec", _CODECS)
        )
        quality = require_choice(self.quality, "quality", _QUALITIES)
        rate = None if self.fps is None else _frames_per_second(self.fps)
        raw, options = _raw_ffmpeg(self.ffmpeg_encoder, self.ffmpeg_options)
        if raw is not None and (encoder != "auto" or codec is not None):
            msg = (
                "'ffmpeg_encoder' names the encoder itself; leave 'encoder' at 'auto' "
                "and 'codec' at None"
            )
            raise ValueError(msg)
        _require_written(encoder, codec)
        _require_device(self.vaapi_device)
        # Held as plain values and a tuple, so a list handed in cannot change
        # the record after it is built, and a whole fps reads back as a float.
        object.__setattr__(self, "encoder", encoder)
        object.__setattr__(self, "codec", codec)
        object.__setattr__(self, "quality", quality)
        object.__setattr__(self, "fps", rate)
        object.__setattr__(self, "ffmpeg_encoder", raw)
        object.__setattr__(self, "ffmpeg_options", options)


def video_options(video: object) -> VideoOptions:
    """The options a writer was given: ``None`` is the default record.

    :raises TypeError: for anything but ``None`` or a :class:`VideoOptions`.
    """
    if video is None:
        return VideoOptions()
    if not isinstance(video, VideoOptions):
        msg = f"'video' must be a VideoOptions or None, got {type(video).__name__}"
        raise TypeError(msg)
    return video


@dataclass(frozen=True)
class VideoRequest:
    """A video to write: where, in which container, with which options; nothing started."""

    path: Path
    container: Container
    video: VideoOptions

    def new_partial(self) -> Path:
        """A hidden name beside ``path`` for the file being written, new on every call.

        Two writes to the same path at once (two test workers, two render
        lanes) each get their own, so neither overwrites the other's
        unfinished file. The file is not created here: ffmpeg, or the client
        of a node, creates it with the user's usual permissions.
        """
        return self.path.with_name(f".{self.path.name}.{uuid.uuid4().hex}.partial")


def _is_dir(path: Path) -> bool:
    """Whether *path* is a directory; ``False`` when its status cannot be read.

    Inside a directory this process cannot search, :meth:`Path.is_dir`
    raises :class:`PermissionError` on Python 3.12 and 3.13 and answers
    ``False`` on 3.14; every version answers ``False`` here. For ``path``
    itself, in its own directory, that leaves what the directory allows to
    :func:`require_writable`, which reports it as it reports any directory
    that refuses the video. A directory of ``path`` that cannot be reached
    (one inside a directory this process cannot search) reads as missing,
    since nothing can be written into it.
    """
    try:
        return path.is_dir()
    except OSError:
        return False


def _target(path: object) -> tuple[Path, Container]:
    """The output path and its container, refused before anything runs."""
    if not isinstance(path, (str, os.PathLike)):
        msg = f"'path' must be a str or an os.PathLike, got {type(path).__name__}"
        raise TypeError(msg)
    target = Path(path)
    container = _SUFFIXES.get(target.suffix.lower())
    if container is None:
        msg = (
            "'path' must end in .webm, .mp4 or .gif, the containers write_video "
            f"writes; got {target.suffix or 'no suffix'!r}"
        )
        raise ValueError(msg)
    if _is_dir(target):
        msg = f"'path' names a directory: {str(target)!r}"
        raise ValueError(msg)
    if not _is_dir(target.parent):
        msg = (
            "the directory of 'path' does not exist or cannot be reached: "
            f"{str(target.parent)!r}"
        )
        raise FileNotFoundError(msg)
    return target, container


def _frames_per_second(fps: object) -> float:
    """The caller's ``fps``, one positive finite number.

    :raises TypeError: for a bool, a text, an array or anything else that is
        not one number.
    :raises ValueError: for a number that is not positive and finite.
    """
    if isinstance(fps, bool | np.bool_):
        # float(True) is 1.0: read as a number it would be a frame a second.
        msg = f"'fps' must be one number, not a bool; got {fps!r}."
        raise TypeError(msg)
    require_scalar(fps, "fps")
    return require_positive(cast("float", fps), "fps")


def _without_nul(texts: tuple[str, ...], name: str) -> None:
    """Refuse a text that holds a NUL character, which no argument of a program can carry.

    :raises ValueError: naming *name*, for the first such text.
    """
    held = next((text for text in texts if "\0" in text), None)
    if held is not None:
        msg = (
            f"'{name}' cannot hold a NUL character, which no argument of a program "
            f"can carry; got {held!r}"
        )
        raise ValueError(msg)


def _require_device(vaapi_device: object) -> None:
    """Refuse a ``vaapi_device`` that is not a path ffmpeg can be handed.

    Whether the device exists is the trial's to find, on the machine that
    encodes.

    :raises TypeError: for anything but a text.
    :raises ValueError: for an empty text, or one that holds a NUL character.
    """
    if not isinstance(vaapi_device, str):
        msg = (
            "'vaapi_device' must be a str, the path of the GPU device VAAPI encodes "
            f"on, such as '/dev/dri/renderD128'; got {type(vaapi_device).__name__}"
        )
        raise TypeError(msg)
    if not vaapi_device:
        msg = (
            "'vaapi_device' must name the GPU device VAAPI encodes on, such as "
            "'/dev/dri/renderD128'; got ''"
        )
        raise ValueError(msg)
    _without_nul((vaapi_device,), "vaapi_device")


def _raw_ffmpeg(
    ffmpeg_encoder: object, ffmpeg_options: object
) -> tuple[str | None, tuple[str, ...]]:
    """The caller's own encoder name and options, checked as text."""
    if isinstance(ffmpeg_options, str) or not isinstance(ffmpeg_options, Sequence):
        msg = (
            "'ffmpeg_options' must be a sequence of separate arguments, such as "
            f"('-crf', '30'), got {ffmpeg_options!r}"
        )
        raise TypeError(msg)
    options = tuple(ffmpeg_options)
    strangers = [item for item in options if not isinstance(item, str)]
    if strangers:
        msg = f"every item of 'ffmpeg_options' must be a str, got {strangers[0]!r}"
        raise TypeError(msg)
    _without_nul(options, "ffmpeg_options")
    if ffmpeg_encoder is None:
        return None, options
    if not isinstance(ffmpeg_encoder, str):
        msg = f"'ffmpeg_encoder' must be a str, got {type(ffmpeg_encoder).__name__}"
        raise TypeError(msg)
    if not ffmpeg_encoder or ffmpeg_encoder.startswith("-"):
        msg = f"'ffmpeg_encoder' must name an encoder, such as 'libx264'; got {ffmpeg_encoder!r}"
        raise ValueError(msg)
    _without_nul((ffmpeg_encoder,), "ffmpeg_encoder")
    return ffmpeg_encoder, options


def _written_by(encoder: Encoder) -> tuple[Codec, ...]:
    """The codecs one kind of encoder writes, best first; none for ``"auto"``."""
    return tuple(codec for codec in _CODECS if (encoder, codec) in FFMPEG_NAMES)


def _require_written(encoder: Encoder, codec: Codec | None) -> None:
    """Refuse a codec that the caller's own kind of encoder does not write."""
    if encoder == "auto" or codec is None or codec in _written_by(encoder):
        return
    msg = (
        f"encoder={encoder!r} writes {', '.join(_written_by(encoder))}; got "
        f"codec={codec!r}. Choose one of those, or leave 'encoder' at 'auto' for "
        f"the first encoder that writes {codec}"
    )
    raise ValueError(msg)


def _require_encoder_fits(container: Container, encoder: Encoder) -> None:
    """Refuse a kind of encoder of the caller's that writes none of the container's codecs."""
    held = CONTAINER_CODECS[container]
    if encoder == "auto" or set(_written_by(encoder)) & set(held):
        return
    fitting = [kind for kind in _ENCODERS if set(_written_by(kind)) & set(held)]
    msg = (
        f".{container} holds {', '.join(held)}, and encoder={encoder!r} writes "
        f"{', '.join(_written_by(encoder))}; choose 'auto' or one of "
        f"{', '.join(repr(kind) for kind in fitting)} for a .{container}, or a "
        "container that holds what it writes"
    )
    raise ValueError(msg)


def _require_combination(container: Container, video: VideoOptions) -> None:
    """Refuse what the container rules out.

    For a GIF: any codec, raw encoder or GPU encoder. For a video: a codec the
    container does not hold, or a kind of encoder that writes none it holds.
    """
    if container == "gif":
        if video.codec is not None or video.ffmpeg_encoder is not None:
            msg = (
                "a GIF is written by ffmpeg's palette filter: it takes neither "
                "'codec' nor 'ffmpeg_encoder'"
            )
            raise ValueError(msg)
        if video.encoder not in ("auto", "cpu"):
            msg = f"a GIF is written on the CPU; got encoder={video.encoder!r}"
            raise ValueError(msg)
        return
    if video.codec is not None and video.codec not in CONTAINER_CODECS[container]:
        msg = (
            f".{container} holds {', '.join(CONTAINER_CODECS[container])}; "
            f"got codec={video.codec!r}"
        )
        raise ValueError(msg)
    _require_encoder_fits(container, video.encoder)


def video_request(path: object, video: VideoOptions) -> VideoRequest:
    """The path checked against the options, and nothing started.

    The simulation writers call it before their first step, so a path, or a
    choice its container rules out, is refused before a long run rather than
    after it.

    :raises TypeError: for a ``path`` that is neither a text nor a path.
    :raises ValueError: for a suffix other than the three, a path that names
        a directory, a codec the container does not hold, an ``encoder``
        that writes none of the codecs it holds, or, for a GIF, a codec, an
        ``ffmpeg_encoder`` or an encoder other than the CPU.
    :raises FileNotFoundError: when the directory of ``path`` does not exist
        or cannot be reached.
    """
    target, container = _target(path)
    _require_combination(container, video)
    return VideoRequest(path=target, container=container, video=video)


def _frame_rate(request: VideoRequest, animation: Animation) -> str:
    """The rate ffmpeg reads the frames at, as an exact fraction.

    Taken from ``fps``, or else from the animation's ``interval`` (in
    milliseconds), the attribute :meth:`Animation.save` reads for the same
    purpose. A fraction keeps 30000/1001 exact where a decimal would round it,
    and a rate under one frame a second takes a denominator as fine as keeps
    it positive and as near: a frame an hour is 1/3600, not 0/1.

    :raises TypeError: when the animation has no interval and no ``fps``.
    :raises ValueError: when its interval is not a positive finite number.
    """
    fps = request.video.fps
    if fps is None:
        interval = getattr(animation, "_interval", None)
        if not isinstance(interval, (int, float)):
            msg = "the animation has no interval to take a frame rate from; pass 'fps'"
            raise TypeError(msg)
        # An infinite interval would give a rate of zero, and NaN compares
        # false either way: both are refused with the rest.
        if not math.isfinite(interval) or interval <= 0:
            msg = (
                f"the animation's interval is not a positive finite number "
                f"({interval!r} ms); pass 'fps'"
            )
            raise ValueError(msg)
        fps = 1000.0 / interval
    exact = Fraction(fps)
    fraction = exact.limit_denominator(max(1001, math.ceil(1001 / exact)))
    return f"{fraction.numerator}/{fraction.denominator}"


def _pad_color(fig: Figure) -> str:
    """The figure's facecolor composited on white, as ``Animation.save`` does, at the level Agg draws it.

    The composite is computed in the order ``Animation.save`` computes it,
    and each channel is taken to eight bits as Agg takes it, rounding a
    half up: :func:`matplotlib.colors.to_hex` rounds a half to even, and
    would pad a half-transparent ``#336699`` with ``b2`` where the frames
    show ``b3``.
    """
    from matplotlib.colors import to_rgba

    red, green, blue, alpha = to_rgba(fig.get_facecolor())
    levels = (
        math.floor((alpha * channel + 1.0 - alpha) * 255.0 + 0.5)
        for channel in (red, green, blue)
    )
    return "#" + "".join(f"{level:02x}" for level in levels)


def _with_agg(fig: Figure) -> dict[str, str]:
    """What makes ``savefig`` draw *fig*'s RGBA frame with Agg.

    Nothing for a canvas whose RGBA writer is Agg's own (an Agg canvas, or a
    GUI one built on it), which keeps its renderer from one frame to the
    next; ``backend="agg"`` for any other, so that a canvas with an RGBA
    writer of its own (Cairo's) does not draw the frames.
    """
    from matplotlib.backends.backend_agg import FigureCanvasAgg

    own = getattr(type(fig.canvas), "print_rgba", None)
    return {} if own is FigureCanvasAgg.print_rgba else {"backend": "agg"}


class _FramePipe:
    """ffmpeg's side of the pipe: one process, one frame size, one output."""

    def __init__(
        self,
        request: VideoRequest,
        ffmpeg: FFmpeg,
        rate: str,
        *,
        output: Path,
        choice: EncoderChoice | None,
    ) -> None:
        self._request = request
        self._ffmpeg = ffmpeg
        self._rate = rate
        self._output = output
        self._choice = choice
        self.encoder_name = "gif" if request.container == "gif" else ""
        self._process: subprocess.Popen[bytes] | None = None
        self._tail: deque[str] = deque(maxlen=_STDERR_LINES)
        # The reader may outlive its wait (a program behind cmd.exe holding
        # the pipe open), so the tail is copied under the lock it appends under.
        self._tail_lock = threading.Lock()
        self._drain: threading.Thread | None = None
        self._inches = (0.0, 0.0)
        self._frame_bytes = 0
        self._frames = 0

    def open(self, fig: Figure) -> None:
        """Measure the frame, choose the encoder and start ffmpeg."""
        width, height = (int(side) for side in fig.bbox.size)
        inches = fig.get_size_inches()
        self._inches = (float(inches[0]), float(inches[1]))
        self._frame_bytes = width * height * 4
        command = ffmpeg_command(
            self._ffmpeg.path,
            width=width,
            height=height,
            rate=self._rate,
            video=self._arguments(fig, width, height),
            muxer=self._request.container,
            output=str(self._output),
        )
        try:
            self._process = subprocess.Popen(  # nosec B603 - an argument list to the ffmpeg find_ffmpeg resolved; no shell
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                creationflags=NO_WINDOW,
            )
            with _RUNNING_LOCK:
                _RUNNING.add(self._process)
            # Kept before it starts: an interrupt inside start() may come
            # when the reader already runs, and it is then waited for.
            self._drain = threading.Thread(target=self._read_stderr, daemon=True)
            self._drain.start()
        except (OSError, RuntimeError) as exc:
            # A thread that cannot start leaves ffmpeg running with nobody to
            # read it: it is stopped and its pipes closed.
            self.abort()
            msg = f"could not start {self._ffmpeg.path} to write {self._request.path}: {exc}"
            raise VideoEncoderError(msg) from exc
        except BaseException:
            # So does an interrupt between the two, which reaches the caller
            # as it is.
            self.abort()
            raise

    def _arguments(self, fig: Figure, width: int, height: int) -> VideoArguments:
        request = self._request
        options = request.video
        # The record holds a tuple already; the field is typed as the
        # sequence a caller may hand in.
        extra = tuple(options.ffmpeg_options)
        if request.container == "gif":
            return gif_arguments(quality=options.quality, options=extra)
        pad_color = _pad_color(fig)
        if options.ffmpeg_encoder is not None:
            self.encoder_name = options.ffmpeg_encoder
            return raw_arguments(
                options.ffmpeg_encoder,
                options=extra,
                container=request.container,
                width=width,
                height=height,
                pad_color=pad_color,
            )
        # An encoder the caller chose before a long run is not tried again.
        choice = self._choice or choose(
            self._ffmpeg,
            encoder=options.encoder,
            codec=options.codec,
            container=request.container,
            width=width,
            height=height,
            vaapi_device=options.vaapi_device,
        )
        self.encoder_name = choice.name
        return video_arguments(
            choice,
            quality=options.quality,
            options=extra,
            container=request.container,
            width=width,
            height=height,
            pad_color=pad_color,
            vaapi_device=options.vaapi_device,
        )

    def _read_stderr(self) -> None:
        process = self._process
        if process is None or process.stderr is None:
            return
        with self._tail_lock:
            # Closed by an abort that came before this reader started.
            if process.stderr.closed:
                return
        # Closed at the end of the stream, by the thread that reads it.
        with process.stderr:
            for line in process.stderr:
                text = line.decode(errors="replace").rstrip()
                with self._tail_lock:
                    self._tail.append(text)

    def write_frame(
        self, fig: Figure, dpi: float, savefig_kwargs: Mapping[str, Any]
    ) -> None:
        """Draw the figure as it stands and send its pixels to ffmpeg."""
        # Held at the size the stream was opened with, as matplotlib's own
        # writers hold it: an animation that resizes its figure would
        # otherwise shear every frame after.
        fig.set_size_inches(self._inches)
        buffer = io.BytesIO()
        # The format, the dpi and the renderer are the stream's: they win
        # over anything Animation.save hands on, rather than collide with it.
        frame_options = {
            **savefig_kwargs,
            "format": "rgba",
            "dpi": dpi,
            **_with_agg(fig),
        }
        fig.savefig(buffer, **frame_options)
        # Released however this ends: an error a caller keeps holds this
        # frame's locals, and a buffer still exported cannot be freed.
        with buffer.getbuffer() as frame:
            self._send(frame)
        self._frames += 1

    def _send(self, frame: memoryview) -> None:
        """Hand one frame's pixels to ffmpeg, once it is the size of the first."""
        if frame.nbytes != self._frame_bytes:
            msg = (
                f"frame {self._frames} of {self._request.path.name} has "
                f"{frame.nbytes} bytes where the first had {self._frame_bytes}"
            )
            raise VideoEncoderError(msg)
        process = self._process
        if process is None or process.stdin is None:
            msg = "the video stream was not opened"
            raise VideoEncoderError(msg)
        try:
            process.stdin.write(frame)
        except OSError as exc:
            reason = f"ffmpeg stopped reading at frame {self._frames}"
            raise self._failure(reason) from exc

    def close(self) -> None:
        """Let ffmpeg finish the file; raise with its words if it fails."""
        process = self._process
        if process is None or process.stdin is None:
            return
        try:
            process.stdin.close()
            code = process.wait(timeout=_EXIT_TIMEOUT_S)
        except (OSError, subprocess.TimeoutExpired) as exc:
            reason = "ffmpeg did not finish the file"
            raise self._failure(reason) from exc
        _forget(process)
        self._join()
        if code != 0:
            reason = f"ffmpeg exited with status {code}"
            raise self._failure(reason)

    def abort(self) -> None:
        """Stop ffmpeg now; the partial file is the caller's to remove."""
        process = self._process
        if process is None:
            return
        if process.poll() is None:
            process.kill()
        if process.stdin is not None:
            with contextlib.suppress(OSError):
                process.stdin.close()
        process.wait()
        _forget(process)
        self._join()

    def _join(self) -> None:
        """Wait for the reader of stderr, or close the pipe if it is not running."""
        drain, process = self._drain, self._process
        with self._tail_lock:
            # Decided under the reader's lock: a reader that starts after
            # this finds its pipe closed and leaves it alone.
            running = drain is not None and drain.is_alive()
            if not running and process is not None and process.stderr is not None:
                process.stderr.close()
        if running and drain is not None:
            drain.join(timeout=_EXIT_TIMEOUT_S)

    def _failure(self, reason: str) -> VideoEncoderError:
        """Stop ffmpeg; the error names the file, the encoder and what ffmpeg wrote last on stderr."""
        self.abort()
        with self._tail_lock:
            said = "\n".join(self._tail) or "(nothing on stderr)"
        # Named here because ffmpeg does not always name it: an option it
        # does not know is refused without a word of the encoder.
        encoder = f" with the encoder {self.encoder_name}" if self.encoder_name else ""
        return VideoEncoderError(
            f"{reason} while writing {self._request.path}{encoder}; ffmpeg said:\n{said}"
        )


def _forget(process: subprocess.Popen[bytes]) -> None:
    """Stop tracking *process*, which has exited."""
    with _RUNNING_LOCK:
        _RUNNING.discard(process)


def stop_running_encoders() -> None:
    """Stop every ffmpeg this process is still running for a video.

    For a process about to end at once (``os._exit``, which runs no
    ``finally``): an ffmpeg that has its last frame keeps encoding after its
    parent has gone, and on Windows the file it holds cannot be removed.
    Each is given a few seconds to exit, so that its files are released.
    """
    with _RUNNING_LOCK:
        running = tuple(_RUNNING)
    for process in running:
        with contextlib.suppress(OSError):
            process.kill()
        with contextlib.suppress(OSError, subprocess.TimeoutExpired):
            process.wait(timeout=_STOP_TIMEOUT_S)


def _movie_writer(pipe: _FramePipe) -> AbstractMovieWriter:
    """The movie writer :meth:`Animation.save` drives, built on the pipe.

    A class made here rather than at the top of the module, because importing
    phonometry must not import matplotlib.
    """
    from matplotlib.animation import AbstractMovieWriter

    class _PipeWriter(AbstractMovieWriter):
        def setup(
            self, fig: Figure, outfile: str | Path, dpi: float | None = None
        ) -> None:
            super().setup(fig, outfile, dpi)
            pipe.open(fig)

        def grab_frame(self, **savefig_kwargs: Any) -> None:
            pipe.write_frame(self.fig, self.dpi, savefig_kwargs)

        def finish(self) -> None:
            pipe.close()

        @contextmanager
        def saving(
            self,
            fig: Figure,
            outfile: str | Path,
            dpi: float | None,
            *args: Any,
            **kwargs: Any,
        ) -> Iterator[AbstractMovieWriter]:
            self.setup(fig, outfile, dpi, *args, **kwargs)
            finished = False
            try:
                yield self
                self.finish()
                finished = True
            finally:
                # Finishing waits for ffmpeg to write the file; whatever ends
                # the frames or that wait early (an error, an interrupt, the
                # generator closed) stops ffmpeg instead.
                if not finished:
                    pipe.abort()

    return _PipeWriter()


def settle(partial: Path, path: Path) -> None:
    """Put the finished video at *path*; if the system refuses, leave it at *partial* and say so.

    :raises VideoEncoderError: when *partial* cannot take the place of *path*
        (on Windows, while a player holds *path* open); the finished video
        stays at *partial*, which the message names, so the run it cost is
        not lost.
    """
    try:
        partial.replace(path)
    except OSError as exc:
        msg = (
            f"the video is finished but could not take the place of {path} ({exc}); "
            f"it is at {partial}"
        )
        raise VideoEncoderError(msg) from exc


def disk_failure(path: Path, exc: OSError) -> VideoEncoderError:
    """The error for this machine's disk refusing the video for *path*.

    It names *path* and gives the system's reason without the name the
    system was given, which is the hidden partial file's: the caller did
    not ask for that file and may not know it exists.
    """
    reason = exc.strerror or str(exc)
    return VideoEncoderError(f"could not write the video for {path}: {reason}")


def require_writable(request: VideoRequest) -> None:
    """Create and remove a hidden file beside ``path``, so a directory that does not take one fails now.

    ffmpeg would find it only once it runs, after the encoders have been
    tried, and for a simulation writer after a first pass has stepped the
    whole run to find the colour limit. Creating the file is the test: one
    the system then does not let go (a scanner holding it on Windows, a
    directory that takes files and lets none be removed) stays, hidden, and
    refuses nothing.

    :raises VideoEncoderError: when the directory does not take the file
        (the message names ``path``, never the hidden file).
    """
    probe = request.new_partial()
    try:
        with probe.open("xb"):
            pass  # Created, and closed empty: that is the whole test.
    except OSError as exc:
        raise disk_failure(request.path, exc) from exc
    finally:
        with contextlib.suppress(OSError):
            probe.unlink(missing_ok=True)


def encode(
    request: VideoRequest,
    animation: Animation,
    *,
    ffmpeg: FFmpeg | None = None,
    choice: EncoderChoice | None = None,
) -> str:
    """Write *animation* as *request* says; return the name of the encoder that wrote it.

    :param ffmpeg: An ffmpeg already found and described
        (:func:`~phonometry.io._video_encoders.describe`); ``None`` finds it.
    :param choice: An encoder already chosen for this video at its size,
        used without a second trial; ``None`` chooses one when the stream
        opens. Ignored for a GIF and for the caller's own ``ffmpeg_encoder``.
    :raises TypeError: when neither ``fps`` nor the animation gives a rate.
    :raises ValueError: when the animation's interval is not a positive
        finite number.
    :raises FFmpegNotFoundError: when ffmpeg is not found.
    :raises VideoEncoderError: when no encoder can write it, ffmpeg cannot be
        started or fails, or the finished file cannot take ``path``'s place.
    """
    import matplotlib as mpl

    rate = _frame_rate(request, animation)
    described = describe(find_ffmpeg()) if ffmpeg is None else ffmpeg
    # Absolute, so that ffmpeg reads it as a file: a relative "x:y/w.webm"
    # would be the protocol "x".
    partial = request.new_partial().absolute()
    pipe = _FramePipe(request, described, rate, output=partial, choice=choice)
    try:
        # Every frame is saved under these, whatever the caller's rcParams say.
        with mpl.rc_context(
            {
                "savefig.bbox": "standard",
                "savefig.dpi": "figure",
                "savefig.facecolor": "auto",
            }
        ):
            animation.save(str(partial), writer=_movie_writer(pipe))
    except BaseException:
        # The error that stopped the write is the one raised: an unfinished
        # file the system does not let go (a scanner holding it on Windows)
        # stays, hidden, rather than hide that error behind its own.
        with contextlib.suppress(OSError):
            partial.unlink(missing_ok=True)
        raise
    settle(partial, request.path)
    return pipe.encoder_name


def _require_animation(animation: object) -> None:
    """Refuse anything that is not a matplotlib animation."""
    try:
        from matplotlib.animation import Animation
    except ImportError as exc:  # pragma: no cover - the base install has no plot
        raise ImportError(_MATPLOTLIB_HINT) from exc
    if not isinstance(animation, Animation):
        msg = (
            "'animation' must be a matplotlib.animation.Animation, "
            f"got {type(animation).__name__}"
        )
        raise TypeError(msg)


def write_video(
    path: str | os.PathLike[str],
    animation: Animation,
    *,
    video: VideoOptions | None = None,
) -> None:
    """Write a matplotlib animation to a WebM, MP4 or GIF file with ffmpeg.

    The container is the suffix of ``path``: ``.webm`` holds AV1 or VP9,
    ``.mp4`` AV1, HEVC or H.264 (written to start playing before it has
    downloaded, an HEVC the library chose tagged so Apple's players open
    it), ``.gif`` a palette
    of up to 256 colours. Every frame is drawn with Agg and piped to ffmpeg,
    so this process holds one frame at a time; for a GIF, ffmpeg itself
    holds every frame until the last one has arrived, since the palette is
    computed from all of them. The file appears at ``path`` only when ffmpeg
    has finished it, so a failure leaves whatever was there before.

    ffmpeg is the program matplotlib's ``rcParams["animation.ffmpeg_path"]``
    names (``"ffmpeg"`` on ``PATH`` by default). How it encodes is ``video``,
    a :class:`VideoOptions`: by default the GPU encoders are tried first
    (NVENC, Quick Sync, VAAPI, VideoToolbox), each with one black frame of
    this size, and the CPU last: SVT-AV1, or without it VP9 in a WebM and
    x265 or x264 in an MP4. A GIF is written on the CPU, with no trial. The
    encoder chosen is logged on the ``phonometry.io`` logger.

    :param path: Where to write; its suffix picks the container.
    :param animation: Any :class:`matplotlib.animation.Animation`.
    :param video: How to encode it (:class:`VideoOptions`); ``None``
        (default) is ``VideoOptions()``: the first encoder that works, the
        best codec the container holds, the standard quality, and the
        animation's own frame rate.
    :raises TypeError: if ``path`` is neither a text nor a path, ``video`` is
        not a :class:`VideoOptions`, ``animation`` is not a matplotlib
        animation, or it has no interval and ``video`` no ``fps``.
    :raises ValueError: for a suffix other than ``.webm``, ``.mp4`` or
        ``.gif``, a path that names a directory, a codec the container does
        not hold, an ``encoder`` that writes none of the codecs it holds
        (VideoToolbox in a ``.webm``), for a GIF a codec, an
        ``ffmpeg_encoder`` or an encoder other than the CPU, or an animation
        interval that is not a positive finite number.
    :raises FileNotFoundError: if the directory of ``path`` does not exist
        or cannot be reached (it sits inside a directory this process cannot
        search).
    :raises FFmpegNotFoundError: if ffmpeg is not found, in Pyodide, or on
        Windows when it was found only in the working directory.
    :raises VideoEncoderError: if no encoder can write the video (the message
        lists the ones that can), the directory of ``path`` does not take the
        file (before the first frame is drawn; the message names ``path`` and the
        system's reason), ffmpeg cannot be started or fails while writing it
        (the message names the encoder and quotes the last lines ffmpeg wrote
        on stderr; a raw ``ffmpeg_encoder`` it lacks or ``ffmpeg_options`` it
        refuses fail within the first frames), or the finished video cannot
        take the place of ``path`` (on Windows, while a player holds the old
        file open; the message says where the video was left).
    :raises ImportError: if matplotlib is not installed.
    """
    options = video_options(video)
    request = video_request(path, options)
    _require_animation(animation)
    # The arguments and ffmpeg are checked before the directory is, as the
    # simulation writers do: a wrong argument, a missing ffmpeg or one that
    # does not run is reported as itself, and the probe file is made only for
    # a video that can be written.
    _frame_rate(request, animation)
    ffmpeg = describe(find_ffmpeg())
    require_writable(request)
    encode(request, animation, ffmpeg=ffmpeg)
