#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The two video writers as a node runs them, and what the client holds their bytes to (private).

On a node a writer runs as it runs here, with the run, the frame and the
video options the client sent, each rebuilt and checked again: the
simulation, the drawing and the encode, into a scratch directory of the
node's own, because a WebM is finished by seeking back into the file, which
a pipe cannot do. The node sends back the record's probe history, then the
video's bytes as the stream after it (``node.FUNCTIONS`` names both); the
scratch directory goes when the node closes the file, or just before the
node ends its process at once. The client takes no more of those bytes than
:func:`video_byte_cap` allows and none that do not begin as
:data:`CONTAINER_HEADS` says the container does.

A node that cannot draw (no matplotlib, or not the font every frame is drawn
in) refuses here before it steps; one that cannot encode (no ffmpeg, or no
encoder that writes this video at its size) is refused by the writer's own
check, also before it steps.
"""

from __future__ import annotations

import io
import shutil
import tempfile
import threading
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from .._internal.validation import require_choice
from .video import write_elastic_fdtd_animation, write_fdtd_animation

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from ..io._video import VideoOptions
    from ..io._video_encoders import Container
    from ._remote.node import NodeStream
    from .compute import Compute
    from .elastic_fdtd import ElasticFDTDResult, ElasticRun
    from .fdtd import FDTDResult, FDTDRun
    from .video import AnimationFrame

__all__ = [
    "CONTAINER_HEADS",
    "NodeCannotAnimateError",
    "remove_scratch_videos",
    "video_byte_cap",
    "write_elastic_fdtd_animation_on_node",
    "write_fdtd_animation_on_node",
]

#: The font matplotlib's default style draws every label in; it ships inside
#: matplotlib, so only a damaged install lacks it.
_FONT = "DejaVu Sans"

#: The containers a node writes.
_CONTAINERS: Final[tuple[Container, ...]] = ("webm", "mp4", "gif")

#: Where each container's own first bytes are, and what they are. A GIF says
#: which of its two versions it is.
CONTAINER_HEADS: Final[Mapping[Container, tuple[tuple[int, bytes], ...]]] = (
    MappingProxyType(
        {
            "webm": ((0, b"\x1a\x45\xdf\xa3"),),
            "mp4": ((4, b"ftyp"),),
            "gif": ((0, b"GIF87a"), (0, b"GIF89a")),
        }
    )
)

#: What a container may add around its frames, at most [bytes].
_CONTAINER_SLACK: Final = 1 << 20

#: The bytes a pixel of every frame, padded to even sides, that a video may
#: take when the library's presets alone decide its encode: above the 1.5 of
#: raw 4:2:0 frames and of a GIF of noise.
_PRESET_BYTES_PER_PIXEL: Final = 2

#: The same when the caller's options decide the encode: raw 16-bit RGBA, the
#: most a lossless encode of an 8-bit frame needs, at whatever bit depth the
#: caller asks for (on noise, about three at 8 bits and up to about seven and
#: a half at 10 or 12, x265 in 12-bit planar RGB).
_CALLER_BYTES_PER_PIXEL: Final = 8


#: The scratch directory of every video this node is writing or sending,
#: and the lock that guards it: the node's input watcher reads it from its own
#: thread when it ends the process at once.
_SCRATCH: set[Path] = set()
_SCRATCH_LOCK = threading.Lock()


class NodeCannotAnimateError(RuntimeError):
    """This node can simulate but cannot draw a video."""


def _forget_scratch(scratch: Path) -> None:
    """Remove *scratch* and stop tracking it."""
    shutil.rmtree(scratch, ignore_errors=True)
    with _SCRATCH_LOCK:
        _SCRATCH.discard(scratch)


def remove_scratch_videos() -> None:
    """Remove the scratch directory of every video this node is still writing or sending.

    For a node about to end its process at once (``os._exit``, which runs no
    ``finally``), so that a run stopped that way leaves no video behind. A
    file ffmpeg still holds open goes with its directory on POSIX; on
    Windows it cannot be removed while ffmpeg runs, and its directory stays.
    """
    with _SCRATCH_LOCK:
        scratches = tuple(_SCRATCH)
    for scratch in scratches:
        shutil.rmtree(scratch, ignore_errors=True)


class _ScratchVideo(io.BufferedReader):
    """The finished video as the node reads it back; closing it removes its scratch directory.

    The node copies it after the arrays, a chunk at a time, and closes it, so
    the directory lives exactly as long as its bytes are needed, on every
    system a node runs on.
    """

    def __init__(self, path: Path) -> None:
        super().__init__(io.FileIO(path, "rb"))
        self._scratch = path.parent

    def close(self) -> None:
        """Close the file, then remove the directory it was written in."""
        try:
            super().close()
        finally:
            _forget_scratch(self._scratch)


def _decided_by_caller(video: VideoOptions) -> bool:
    """Whether the caller's own options decide the encode, rather than the library's presets.

    They do with an ``ffmpeg_encoder`` of the caller's, and with any
    ``ffmpeg_options``, which come after the library's preset and pixel
    format and so win over them.
    """
    return video.ffmpeg_encoder is not None or len(video.ffmpeg_options) > 0


def video_byte_cap(
    n_frames: int, width: int, height: int, *, video: VideoOptions
) -> int:
    """The most bytes a video of these frames, encoded as *video* says, may take before the client refuses it.

    Two bytes a pixel of every frame, padded to even sides, when the
    library's presets alone decide the encode (an encoder the library chose,
    or a GIF, and no ``ffmpeg_options``): above the 1.5 of raw 4:2:0 frames,
    which the library's encoders do not exceed at their qualities, and above
    the 1.5 of a GIF whose every pixel takes a 12-bit code (noise), with
    room for its block lengths. Eight when the caller's options decide it
    (an ``ffmpeg_encoder`` of the caller's, or any ``ffmpeg_options``, which
    come after the library's preset and pixel format and so win over them):
    raw 16-bit RGBA, the most a lossless encode of the library's 8-bit
    frames needs, at whatever bit depth the caller asks for. On noise an
    8-bit lossless 4:4:4 encode takes about three, and one at 10 or 12 bits
    up to about seven and a half (x265 in 12-bit planar RGB). Plus 1 MiB for
    what a container adds. A node's video longer than this is refused before
    a byte of it is read. The bytes are written to disk as they arrive, so
    this bounds the disk, not the memory.
    """
    padded = (width + width % 2) * (height + height % 2)
    per_pixel = (
        _CALLER_BYTES_PER_PIXEL
        if _decided_by_caller(video)
        else _PRESET_BYTES_PER_PIXEL
    )
    return n_frames * padded * per_pixel + _CONTAINER_SLACK


def _check_font() -> None:
    """Refuse at once on a node without matplotlib or the font every frame is drawn in.

    :raises NodeCannotAnimateError: for either.
    """
    try:
        from matplotlib import font_manager
    except ImportError as exc:
        msg = (
            "this node has no matplotlib, so it cannot draw a video; rebuild the node "
            'image, or install "phonometry[plot]" in its Python'
        )
        raise NodeCannotAnimateError(msg) from exc
    try:
        font_manager.findfont(_FONT, fallback_to_default=False)
    except ValueError as exc:
        msg = (
            f"this node has no {_FONT}, the font every frame is drawn in; rebuild the "
            "node image, or reinstall matplotlib in its Python"
        )
        raise NodeCannotAnimateError(msg) from exc


def _encoded[R](container: object, write: Callable[[Path], R]) -> tuple[R, NodeStream]:
    """Run *write* into a scratch file of this node's own; its record and the file to send.

    :raises ValueError: for a container other than the three.
    :raises TypeError: for a container that is not a text.
    :raises NodeCannotAnimateError: without matplotlib or its font.
    """
    suffix = require_choice(container, "container", _CONTAINERS)
    _check_font()
    scratch = Path(tempfile.mkdtemp(prefix="phonometry-video-"))
    with _SCRATCH_LOCK:
        _SCRATCH.add(scratch)
    try:
        result = write(scratch / f"video.{suffix}")
        stream = _ScratchVideo(scratch / f"video.{suffix}")
    except BaseException:
        _forget_scratch(scratch)
        raise
    return result, ("video", stream)


def write_fdtd_animation_on_node(
    *,
    run: FDTDRun,
    frame: AnimationFrame,
    video: VideoOptions,
    container: Container,
    compute: Compute,
) -> tuple[FDTDResult, NodeStream]:
    """:func:`~phonometry.simulation.write_fdtd_animation` on this node, into a scratch file it sends back.

    The run, the frame and the video options are the client's, rebuilt here,
    and the writer checks them again; ``container`` is the file's,
    ``"webm"``, ``"mp4"`` or ``"gif"``.

    :return: The writer's record, and ``("video", file)``: the finished
        video, read from its start, whose closing removes its scratch
        directory.
    :raises TypeError: for a ``container`` that is not a text, and what the
        writer refuses as the wrong type.
    :raises ValueError: for a ``container`` other than the three, and what
        the writer refuses as the wrong value.
    :raises NodeCannotAnimateError: without matplotlib or its font, before
        any step.
    :raises FFmpegNotFoundError: when this node has no ffmpeg, before any step.
    :raises VideoEncoderError: when no encoder here writes the video (before
        any step), or ffmpeg fails while writing it.
    :raises ComputeImportError: when the device's library does not import here.
    :raises ComputeDeviceError: when the device is not present here.
    """
    return _encoded(
        container,
        lambda target: write_fdtd_animation(
            target, run, compute=compute, frame=frame, video=video
        ),
    )


def write_elastic_fdtd_animation_on_node(
    *,
    run: ElasticRun,
    frame: AnimationFrame,
    video: VideoOptions,
    container: Container,
    compute: Compute,
) -> tuple[ElasticFDTDResult, NodeStream]:
    """:func:`~phonometry.simulation.write_elastic_fdtd_animation` on this node, into a scratch file it sends back.

    As :func:`write_fdtd_animation_on_node`, for an elastic run.

    :return: The writer's record, and ``("video", file)``, as there.
    :raises TypeError: for a ``container`` that is not a text, and what the
        writer refuses as the wrong type.
    :raises ValueError: for a ``container`` other than the three, and what
        the writer refuses as the wrong value.
    :raises NodeCannotAnimateError: without matplotlib or its font, before
        any step.
    :raises FFmpegNotFoundError: when this node has no ffmpeg, before any step.
    :raises VideoEncoderError: when no encoder here writes the video (before
        any step), or ffmpeg fails while writing it.
    :raises ComputeImportError: when the device's library does not import here.
    :raises ComputeDeviceError: when the device is not present here.
    """
    return _encoded(
        container,
        lambda target: write_elastic_fdtd_animation(
            target, run, compute=compute, frame=frame, video=video
        ),
    )
