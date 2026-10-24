#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Writing an FDTD run straight to a video file.

:func:`write_fdtd_animation` steps the run
:func:`~phonometry.simulation.fdtd_simulation` steps, an
:class:`~phonometry.simulation.FDTDRun` checked when it was built, and draws
the pressure into a video as it is computed, through the encoders of
:func:`phonometry.io.write_video`, and :func:`write_elastic_fdtd_animation`
does the same for :func:`~phonometry.simulation.elastic_fdtd_simulation` and
an :class:`~phonometry.simulation.ElasticRun`, drawing the field
``ElasticRecording.snapshot_field`` names, with the colour limit of
:class:`AnimationFrame` in that field's unit. No snapshot is stored: a long run on a
large grid writes a long video in the memory one frame takes here (a GIF
apart, whose palette ffmpeg computes from every frame it holds). The run's
result comes back with its probes and times and without snapshots.

How each frame is drawn is one record, :class:`AnimationFrame` (the labels'
language, the size in pixels, the colour limit); how the video is encoded is
another, :class:`phonometry.io.VideoOptions`, the one
:func:`phonometry.io.write_video` takes. Before the first step ffmpeg is
found and run, and the encoder that will write the video is chosen by a real
one-frame encode at the frame's size, so neither a missing ffmpeg nor an
encoder that cannot write the video costs a run.

The frames show what the snapshot plot of the simulation function's result
(:meth:`~phonometry.simulation.FDTDResult.plot` with ``kind="snapshot"``)
shows: the same field on the same colormap, symmetric about zero, with the
same marks and labels, the limit of the scale being the video's own (fixed
for the whole video, given or found, as the next paragraph says); a
writer's own result holds no snapshots to plot. A frame is laid
out once for the whole run, for the widest title it shows (the time of its
last frame) and the labels of its axes and colour scale, so that no text
leaves the frame and nothing moves from one frame to the next; the title is
centred over the frame. Every text keeps its own size: a frame is at least
479 by 245 pixels, the smallest in which every text, at its own size, stays
clear of the frame's margin and covers no other, with the field still in
view, on every matplotlib version the library is tested with. An axis too
short for the numbers matplotlib would write along it keeps fewer of them,
never one over another: a tall grid's narrow field may show a single number
under it. That holds for a run of up to ten seconds; a longer one writes more
digits in its title's time, and needs a frame about 10.6 pixels wider for
each digit past four before the point in milliseconds: a narrower one is
refused before the run starts, with the width it needs. The frames are drawn
once and then updated in place, under matplotlib's default style whatever
the caller's settings say, so a video written here and one written on
another machine look alike. One frame is drawn every
``run.recording.snapshot_every`` steps, at the decimation
``run.recording.snapshot_decimation`` gives.

The colour scale is fixed for the whole video. With a limit given, each
frame is drawn as the run computes it. Without one the run steps twice: a
first pass finds, on the device, the largest magnitude the drawn field
reaches outside the source cells, the plane-wave injection lines and the
absorbing layer, where the field is what the source or the sponge makes it
rather than the wave the video shows, and the second pass draws with that
limit. Neither pass stores a snapshot.

With a ``host`` in ``compute`` the run is computed, drawn and encoded on
that node, named in the hosts file (see the guide on remote nodes), and only
the result and the video's bytes come back. Every argument is checked here
first, so a call refused here never starts ssh, and ffmpeg is found and run
on the node: this machine runs it only when a node that failed falls back
to it (``fallback=True``). The bytes go, as they arrive, into a hidden file
beside ``path``, created before ssh starts so that a directory that does not
take it fails first: never more of them than the frames can take, and none
that do not begin as the container ``path`` names. That file takes
``path``'s place once the node's whole answer has been read and checked, and
is removed if anything fails before (or stays, hidden, if the system does
not let it go, which hides no error).
"""

from __future__ import annotations

import contextlib
import math
from collections import deque
from dataclasses import dataclass, replace
from fractions import Fraction
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, TypedDict

import numpy as np

# Language at run time: AnimationFrame is a published record, whose field
# annotations resolve from this module's globals.
from .._i18n import Language, check_language
from .._internal.display import RichDisplay
from .._internal.validation import require_count, require_positive, require_scalar
from .compute import Compute, _requested
from .elastic_fdtd import (
    ElasticFDTDResult,
    ElasticRun,
    ExplosionSource,
    _elastic_engine,
    _elastic_march,
)
from .fdtd import (
    FDTDResult,
    FDTDRun,
    PlaneWaveSource,
    _acoustic_engine,
    _march,
    _placement_here,
)

if TYPE_CHECKING:
    import os
    from collections.abc import Callable, Generator, Iterable, Mapping
    from typing import BinaryIO

    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from matplotlib.image import AxesImage
    from numpy.typing import NDArray

    from ..io._video import VideoOptions, VideoRequest
    from ..io._video_encoders import EncoderChoice, FFmpeg, VideoEncoderError
    from ._backends import Backend, DeviceArray
    from ._remote.client import RemoteFunction
    from .compute import RunProvenance
    from .elastic_fdtd import ElasticFDTD2D, ElasticSource, _ElasticChecks
    from .fdtd import FDTD2D, AnySource, _AcousticChecks

__all__ = ["AnimationFrame", "write_elastic_fdtd_animation", "write_fdtd_animation"]

#: Frames per second of a simulation video unless ``VideoOptions.fps`` says otherwise.
_DEFAULT_FPS: Final = 30.0

#: Dots per inch of the figure a frame is drawn on. The frame is set in
#: pixels; at 100 the library's default font sizes read well at 960 x 540.
_DPI: Final = 100.0

#: The smallest frame, in pixels, a simulation video is drawn at: its width
#: and its height. From 479 by 245 every text of a frame keeps the size
#: matplotlib's default style gives it and lies inside the frame, clear of
#: the margin the layout keeps at its edges and over no other text, and the
#: field shows at least 14 pixels on its narrow side: for both writers'
#: fields, in English and Spanish, on grids from ten times wider than tall
#: to ten times taller than wide, for a run of up to ten seconds (four digits
#: before the point in milliseconds; a longer run needs a wider frame, see
#: _DIGIT_WIDTH), with matplotlib 3.10 as with 3.11. Measured a pixel at a
#: time over those frames with both: one pixel narrower, the widest title
#: (the Spanish one of an elastic pressure field) reaches into the margin at
#: the sides with either. The height is 3.10's, which sets every text in a
#: box 2 to 6 pixels taller than 3.11 does (a title 23 to 25 pixels high,
#: against 18 or 19): one pixel lower, a field ten times taller than wide is
#: under 14 pixels wide there, where 3.11 holds every frame down to 239
#: pixels. The numbers are those of the text each matplotlib sets with the
#: FreeType and the DejaVu Sans it bundles: a change to either moves them,
#: and the tests of the floor go red until they are measured again.
_MIN_WIDTH: Final = 479
_MIN_HEIGHT: Final = 245

#: The digits before the point of a title's time, in milliseconds, that a
#: frame :data:`_MIN_WIDTH` wide holds.
_FLOOR_DIGITS: Final = 4

#: The width, in pixels, each digit more than :data:`_FLOOR_DIGITS` adds to
#: the frame a run needs: DejaVu Sans's digits share one advance, 0.636 of
#: its size, 10.6 pixels at the title's 12 points. Measured on the widest
#: title for every count from five to thirteen digits, the frame its text
#: needs to stay clear of the margin is 479 plus this times the digits past
#: four, rounded up (490, 501 and 511 pixels for five, six and seven).
#: Measured with matplotlib 3.11; with matplotlib 3.10 six digits need 500,
#: so there the rule is conservative.
_DIGIT_WIDTH: Final = Fraction(53, 5)

#: What every message that finds no colour scale asks for.
_LIMIT_HINT: Final = "give the limit as AnimationFrame(color_limit=...)"

#: What drives or damps an acoustic run's pressure, where a first pass does
#: not look for the colour limit.
_ACOUSTIC_COVERING: Final = "the sources, the injection lines and the absorbing layer"

#: What drives or damps an elastic run's field: it has no injection lines.
_ELASTIC_COVERING: Final = "the sources and the absorbing layer"

#: The band of cells an absorbing layer of width ``w`` covers on each side.
_SIDE_BANDS: Final[Mapping[str, Callable[[int], tuple[slice, slice]]]] = (
    MappingProxyType(
        {
            "left": lambda w: (slice(None), slice(0, w)),
            "right": lambda w: (slice(None), slice(-w, None)),
            "top": lambda w: (slice(0, w), slice(None)),
            "bottom": lambda w: (slice(-w, None), slice(None)),
        }
    )
)


def _frame_pixels(size: object) -> tuple[int, int]:
    """The frame's width and height, whole numbers of pixels, at least 479 by 245."""
    if not isinstance(size, (tuple, list)):
        msg = f"'size' must be a pair (width, height) in pixels, got {size!r}"
        raise TypeError(msg)
    # The length of a fixed-size argument, not a quantity.
    if len(size) != 2:  # noqa: PLR2004
        msg = f"'size' must be a pair (width, height) in pixels, got {size!r}"
        raise ValueError(msg)
    width, height = (require_count(side, "size", at_least=None) for side in size)
    if width < _MIN_WIDTH or height < _MIN_HEIGHT:
        msg = (
            f"'size' must be at least {_MIN_WIDTH} by {_MIN_HEIGHT} pixels, the "
            "smallest frame in which every text, at its own size, stays clear "
            f"of the frame's margin, got {size!r}"
        )
        raise ValueError(msg)
    return width, height


@dataclass(frozen=True, kw_only=True)
class AnimationFrame(RichDisplay):
    """How each frame of a simulation video is drawn: in which language, at what size, on what scale.

    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param size: ``(width, height)`` of a frame in pixels, at least 479 by
        245, the smallest frame in which every text, at its own size, stays
        clear of the frame's margin and the field still shows, on every
        matplotlib version the library is tested with (default
        ``(960, 540)``).
        That is for a run of up to ten seconds: a longer run needs a wider
        frame for the time its last title writes, which the writers ask for
        before the run starts.
    :param color_limit: The value at either end of the colour scale, fixed
        for the whole video, in the unit of the field drawn: pascals for an
        acoustic run (:func:`write_fdtd_animation`), and for an elastic one
        (:func:`write_elastic_fdtd_animation`) the unit of
        ``ElasticRecording.snapshot_field``, pascals for ``"p"`` and metres
        per second for ``"vx"`` and ``"vy"``. ``None`` (default) finds it in
        a first pass over the run.
    :raises TypeError: for a ``size`` that is not a pair or holds something
        other than numbers, or a ``color_limit`` that is not one number.
    :raises ValueError: for a ``language`` other than ``"en"`` and ``"es"``,
        a ``size`` of more or fewer than two sides, with a side that is not
        a whole number, or narrower than 479 or lower than 245 pixels, or a
        ``color_limit`` that is not a positive finite number.
    """

    language: Language = "en"
    size: tuple[int, int] = (960, 540)
    color_limit: float | None = None

    def __post_init__(self) -> None:
        """Refuse a field of the wrong type or value when the record is built."""
        language = check_language(self.language)
        size = _frame_pixels(self.size)
        limit = None
        if self.color_limit is not None:
            require_scalar(self.color_limit, "color_limit")
            limit = require_positive(self.color_limit, "color_limit")
        # Held as a tuple of ints and a float, so a list handed in cannot
        # change the record after it is built, and a whole float reads back
        # as the pixel count it is.
        object.__setattr__(self, "language", language)
        object.__setattr__(self, "size", size)
        object.__setattr__(self, "color_limit", limit)


@dataclass(frozen=True)
class _Encoding:
    """The ffmpeg that will write a video, and the encoder found to run there.

    ``choice`` is ``None`` for a GIF (ffmpeg's palette filter, on the CPU)
    and for an encoder the caller named, which is passed through as given.
    """

    ffmpeg: FFmpeg
    choice: EncoderChoice | None


def _frame_or_default(frame: object) -> AnimationFrame:
    """The frame a writer was given: ``None`` is the default record.

    :raises TypeError: for anything but ``None`` or an :class:`AnimationFrame`.
    """
    if frame is None:
        return AnimationFrame()
    if not isinstance(frame, AnimationFrame):
        msg = f"'frame' must be an AnimationFrame or None, got {type(frame).__name__}"
        raise TypeError(msg)
    return frame


def _require_run[R](run: object, kind: type[R]) -> R:
    """The run a writer was given, of the kind it writes.

    :raises TypeError: for anything else, the other engine's run included.
    """
    if not isinstance(run, kind):
        msg = f"'run' must be an {kind.__name__}, got {type(run).__name__}"
        raise TypeError(msg)
    return run


def _preflight(request: VideoRequest, size: tuple[int, int]) -> _Encoding:
    """Find ffmpeg, run it and choose its encoder at the frame's size, before the first step.

    The choice is the trial encode :func:`~phonometry.io.write_video` makes,
    made here so that a missing ffmpeg, one that does not run, or an encoder
    that cannot write this video is refused before the run rather than
    after it; the encode then uses that encoder without a second trial.

    :raises FFmpegNotFoundError: when ffmpeg is not found.
    :raises VideoEncoderError: when it does not run, has no encoder that
        writes this video at this size, or lacks the encoder the caller named.
    """
    from ..io._video_encoders import VideoEncoderError, choose, describe, find_ffmpeg

    options = request.video
    ffmpeg = describe(find_ffmpeg())
    if request.container == "gif":
        return _Encoding(ffmpeg, None)
    if options.ffmpeg_encoder is not None:
        if options.ffmpeg_encoder not in ffmpeg.encoders:
            msg = f"{ffmpeg.path} ({ffmpeg.version}) has no encoder {options.ffmpeg_encoder!r}"
            raise VideoEncoderError(msg)
        return _Encoding(ffmpeg, None)
    width, height = size
    choice = choose(
        ffmpeg,
        encoder=options.encoder,
        codec=options.codec,
        container=request.container,
        width=width,
        height=height,
        vaapi_device=options.vaapi_device,
    )
    return _Encoding(ffmpeg, choice)


def _frame_cadence(snapshot_every: int | None) -> int:
    """The steps between two frames, which a video cannot do without."""
    if snapshot_every is None:
        msg = (
            "a video needs run.recording.snapshot_every, the number of steps "
            "between two frames; this run records no snapshots"
        )
        raise ValueError(msg)
    return snapshot_every


def _last_frame_time(checks: _AcousticChecks | _ElasticChecks, every: int) -> float:
    """The time, in seconds, of a run's last frame, one drawn every *every* steps."""
    return (checks.steps // every) * (every * checks.dt)


def _shown_time(time_s: float, language: Language) -> str:
    """A time as a video's title writes it: in milliseconds, two decimals, in the language's notation."""
    from .._i18n import format_number

    return format_number(float(time_s) * 1000.0, language, decimals=2)


def _width_for(last_time_s: float, language: Language) -> int:
    """The width, in pixels, of the narrowest frame whose title shows *last_time_s* clear of the margin.

    The title writes the time in milliseconds with two decimals; each digit
    before the point past :data:`_FLOOR_DIGITS` widens it by
    :data:`_DIGIT_WIDTH`, and the frame with it.
    """
    shown = _shown_time(last_time_s, language)
    digits = len(shown) - len(shown.lstrip("0123456789"))
    return _MIN_WIDTH + max(0, math.ceil(_DIGIT_WIDTH * (digits - _FLOOR_DIGITS)))


def _require_width(frame: AnimationFrame, last_time_s: float) -> None:
    """Refuse a frame too narrow for the title of a run's last frame, at *last_time_s*.

    :raises ValueError: when the frame is narrower than :func:`_width_for`
        asks; the message gives the caller's frame at the width it needs.
    """
    width, height = frame.size
    need = _width_for(last_time_s, frame.language)
    if width < need:
        wider = replace(frame, size=(need, height))
        msg = (
            "the title of this run's last frame, at "
            f"{_shown_time(last_time_s, frame.language)} ms, needs a frame "
            f"at least {need} pixels wide to stay clear of the frame's margin, "
            f"and 'frame' is {width} pixels wide: give {wider!r}"
        )
        raise ValueError(msg)


def _sponge_cells(keep: NDArray[np.bool_], sides: Iterable[str], width: int) -> None:
    """Leave out, in *keep*, the absorbing layer of width *width* on each side."""
    for side in sides:
        keep[_SIDE_BANDS[side](width)] = False


def _peak(
    frames: Generator[DeviceArray, None, None],
    backend: Backend,
    keep: NDArray[np.bool_],
) -> float:
    """The largest magnitude the yielded fields reach where *keep* is true.

    Found on the device, frame by frame, into one device scalar that comes to
    the host once, at the end: no frame crosses. The march is closed however
    the loop ends, so an interrupt does not leave it suspended inside its
    device context, and it is closed before this function leaves its own:
    the march's scope was entered inside this one, so it is left first, and
    the device that was current before the pass is current after it.
    """
    xp = backend.xp
    with backend.context(), contextlib.closing(frames):
        weight = backend.asarray(keep)
        peak = backend.zeros(())
        for field in frames:
            peak = xp.maximum(peak, xp.max(xp.abs(field) * weight))
    return backend.scalar(peak)


def _ran(provenance: RunProvenance) -> Compute:
    """Where a first pass actually stepped, as a request the second can repeat.

    After a fallback this is NumPy, so the second pass neither looks for the
    device again nor warns a second time.
    """
    return Compute(
        device=provenance.device,
        device_index=provenance.device_index,
        dtype=provenance.dtype,
    )


def _host(backend: Backend, field: DeviceArray) -> NDArray[np.float64]:
    """A float64 host copy of one yielded field (the engine's own array moves on)."""
    return np.array(backend.to_host(field), dtype=np.float64, copy=True)


def _frame_figure(size: tuple[int, int]) -> Figure:
    """The figure a video's frames are drawn on: *size* pixels, on an Agg canvas, with no layout engine.

    No engine moves anything at a draw: the frame's set-up places its parts
    once for the whole run (:func:`phonometry._plot.simulation.lay_out_frame`).
    """
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    width, height = size
    # Half a pixel more than asked: matplotlib truncates the size in pixels,
    # and w / _DPI times _DPI can land a hair below w.
    figure = Figure(
        figsize=((width + 0.5) / _DPI, (height + 0.5) / _DPI), dpi=_DPI, layout=None
    )
    FigureCanvasAgg(figure)
    return figure


def _render(
    request: VideoRequest,
    encoding: _Encoding,
    frame: AnimationFrame,
    *,
    frames: Generator[DeviceArray, None, None],
    backend: Backend,
    n_frames: int,
    frame_dt: float,
    setup: Callable[[Axes, NDArray[np.float64]], AxesImage],
    title: Callable[[float], str],
) -> str:
    """Draw every yielded field into one figure, piped frame by frame to ffmpeg.

    The figure (:func:`_frame_figure`) is built and saved under matplotlib's
    default style, at the frame's size, and played at ``request.video.fps``,
    or 30 frames per second without one. The first field sets the figure up,
    and *setup* lays it out for the whole run; each later one is drawn into
    it as the animation asks for it, which is when the engine steps to it.
    Once the last frame is drawn, and before ffmpeg finishes the file, the
    generator is drained: the steps after that frame still belong to the
    run, whose probes record them, and a run that fails there fails before
    the video takes the place of what was at the path. However the encode ends
    (ffmpeg failing, the caller's interrupt), the generator is closed, so it
    does not stay suspended inside its device context until the garbage
    collector finds it.

    :return: The name of the encoder that wrote the video.
    """
    from matplotlib import style
    from matplotlib.animation import FuncAnimation

    from .._plot import simulation as plot
    from ..io._video import encode

    fps = _DEFAULT_FPS if request.video.fps is None else request.video.fps
    with contextlib.closing(frames), style.context("default"):
        fig = _frame_figure(frame.size)
        image = setup(fig.add_subplot(), _host(backend, next(frames)))

        def update(k: int) -> tuple[AxesImage]:
            if k:
                plot._update_snapshot(
                    image, _host(backend, next(frames)), title(k * frame_dt)
                )
            if k == n_frames - 1:
                deque(frames, maxlen=0)
            return (image,)

        animation = FuncAnimation(
            fig,
            update,
            frames=n_frames,
            init_func=lambda: (image,),
            interval=1000.0 / fps,
            blit=False,
            cache_frame_data=False,
            repeat=False,
        )
        return encode(
            request, animation, ffmpeg=encoding.ffmpeg, choice=encoding.choice
        )


@dataclass(frozen=True)
class _Call[R: (FDTDRun, ElasticRun)]:
    """What a writer was asked for, checked: the run, its frames, where it runs and the video.

    ``placement`` is the request resolved (the argument, :func:`use`, the
    environment, NumPy); with a host the writer runs on that node.
    ``scale`` is the colour limit the frame gave, or else the cells a first
    pass reads it from.
    """

    run: R
    drawn: AnimationFrame
    placement: Compute
    every: int
    request: VideoRequest
    scale: float | NDArray[np.bool_]


def _checked_call[R: (FDTDRun, ElasticRun)](
    path: str | os.PathLike[str],
    run: object,
    kind: type[R],
    *,
    compute: Compute | None,
    frame: AnimationFrame | None,
    video: VideoOptions | None,
    scale: Callable[[R, float | None], float | NDArray[np.bool_]],
) -> _Call[R]:
    """A writer's arguments, checked in the order every route checks them.

    The run's kind, the frame record's, the placement, the frame cadence,
    the frame's width against the title of the run's last frame, the video
    record's kind and the path against it, and last the colour limit or the
    cells a first pass reads it from (*scale*, the kind's own): all before
    ffmpeg runs, ssh starts or the run takes a step.

    :raises TypeError: for a run of another kind, a frame, video or
        ``compute`` record of another type, or a path neither a text nor a
        path.
    :raises ValueError: for a run that records no snapshots, a malformed
        ``PHONOMETRY_COMPUTE``, a frame too narrow for the title of the run's
        last frame, a path whose container rules out the options, or nothing
        to find the colour scale by.
    :raises FileNotFoundError: when the directory of *path* does not exist
        or cannot be reached.
    """
    from ..io._video import video_options, video_request

    checked = _require_run(run, kind)
    drawn = _frame_or_default(frame)
    # A compute of another type, or a malformed PHONOMETRY_COMPUTE, is
    # refused here, before ffmpeg runs or ssh starts.
    placement = _requested(compute)
    # What the run checked when it was built; its recording is kept as
    # given, None included, so the cadence is read here, resolved.
    every = _frame_cadence(checked._checked.snapshot_every)
    _require_width(drawn, _last_frame_time(checked._checked, every))
    request = video_request(path, video_options(video))
    limit = scale(checked, drawn.color_limit)
    return _Call(checked, drawn, placement, every, request, limit)


def _kept(
    checks: _AcousticChecks | _ElasticChecks,
    driven: Iterable[tuple[int | slice, int | slice]],
    covering: str,
) -> NDArray[np.bool_]:
    """True where the drawn field may set the colour scale, false on *driven* cells and in the sponge.

    Cut to the cells a frame keeps, as the march cuts the field. A mask of
    booleans, an eighth of the memory a float mask of the grid takes: the
    first pass reads it onto the device in the run's own dtype.

    :raises ValueError: when *covering*, the parts of the run that drive or
        damp the field, leave no cell, asking for
        ``AnimationFrame(color_limit=...)``.
    """
    keep = np.ones(checks.grid, dtype=np.bool_)
    _sponge_cells(keep, checks.absorbing_sides, checks.sponge_width)
    for cells in driven:
        keep[cells] = False
    d = checks.snapshot_decimation
    kept = np.ascontiguousarray(keep[::d, ::d])
    if not kept.any():
        msg = (
            f"{covering} cover every cell a frame keeps, so there is nothing "
            f"to set the colour scale by; {_LIMIT_HINT}"
        )
        raise ValueError(msg)
    return kept


def _found_limit(
    sim: FDTD2D | ElasticFDTD2D,
    frames: Generator[DeviceArray, None, None],
    keep: NDArray[np.bool_],
    covering: str,
) -> tuple[float, Compute]:
    """The colour limit a first pass over *frames* finds, and where *sim* really stepped.

    *covering* names what *keep* leaves out, the parts of the run that
    drive or damp the field, for the message when the field stays zero
    everywhere else.

    :raises ValueError: when the field is not finite, or stays zero wherever
        *keep* is true.
    """
    found = _peak(frames, sim._backend, keep)
    if not math.isfinite(found):
        msg = (
            "the field is not finite in some frame, so there is no colour scale "
            f"to find; check the sources, or {_LIMIT_HINT}"
        )
        raise ValueError(msg)
    if found <= 0.0:
        msg = (
            f"the field stays zero outside {covering} for the whole run, so "
            f"there is no colour scale to find; {_LIMIT_HINT}"
        )
        raise ValueError(msg)
    return found, _ran(sim.provenance)


def _encoding_and_limit[R: (FDTDRun, ElasticRun)](
    call: _Call[R],
    compute: Compute | None,
    first_pass: Callable[[R, Compute | None, NDArray[np.bool_]], tuple[float, Compute]],
) -> tuple[_Encoding, float, Compute | None]:
    """The encoder, chosen before any step; then the colour limit, and where the run steps.

    A limit the frame gave is taken as it is, and the run steps where
    *compute* asks. Without one, *first_pass* (the kind's own) steps the run
    to find it, and the run then steps where that pass really stepped.

    :raises FFmpegNotFoundError: when ffmpeg is not found.
    :raises VideoEncoderError: when it does not run, has no encoder that
        writes this video, or the directory of ``path`` does not take a file.
    :raises ValueError: when the first pass finds nothing to scale by.
    """
    from ..io._video import require_writable

    encoding = _preflight(call.request, call.drawn.size)
    require_writable(call.request)
    if isinstance(call.scale, float):
        return encoding, call.scale, compute
    limit, ran = first_pass(call.run, compute, call.scale)
    return encoding, limit, ran


class _PartialFile:
    """The hidden file beside ``path`` a node's video goes into, before it takes ``path``'s place.

    A failure of this machine's disk, to create the file, to write the bytes
    or to close it (a directory that refuses files, a full disk, a quota), is
    a :class:`~phonometry.io.VideoEncoderError` naming ``path``, as ffmpeg's
    is on this machine; it never names the hidden file, which the caller
    did not ask for.
    """

    def __init__(self, request: VideoRequest) -> None:
        self.path = request.new_partial()
        self._target = request.path
        self._handle: BinaryIO | None = None

    def _failure(self, exc: OSError) -> VideoEncoderError:
        from ..io._video import disk_failure

        return disk_failure(self._target, exc)

    def _opened(self) -> BinaryIO:
        if self._handle is None:
            try:
                self._handle = self.path.open("xb")
            except OSError as exc:
                raise self._failure(exc) from exc
        return self._handle

    def open(self) -> None:
        """Create the file now, never over another.

        :raises VideoEncoderError: when the directory does not take it.
        """
        self._opened()

    def write(self, data: bytes) -> int:
        """Write *data*, creating the file first if it is not yet.

        :raises VideoEncoderError: when the disk does not take them.
        """
        handle = self._opened()
        try:
            return handle.write(data)
        except OSError as exc:
            raise self._failure(exc) from exc

    def close(self) -> None:
        """Close the file, if it is open, writing out what it still holds.

        :raises VideoEncoderError: when the disk does not take that.
        """
        handle, self._handle = self._handle, None
        if handle is None:
            return
        try:
            handle.close()
        except OSError as exc:
            raise self._failure(exc) from exc

    def discard(self) -> None:
        """Close and remove the file: the run failed, or falls back to this machine.

        The file is removed even when closing it fails, and that failure is
        the one raised. A file the system does not let go (a scanner holding
        it on Windows, a directory that takes files and lets none be removed)
        stays, hidden: it was created, so the directory takes the video, and
        nothing the caller asked for depends on its going.

        :raises VideoEncoderError: when closing the file fails.
        """
        try:
            self.close()
        finally:
            with contextlib.suppress(OSError):
                self.path.unlink(missing_ok=True)


def _node_video[R: (FDTDRun, ElasticRun), T](
    function: RemoteFunction,
    call: _Call[R],
    history: tuple[str, tuple[int, ...]],
    result: Callable[[R, NDArray[np.float64], RunProvenance], T],
) -> T | None:
    """Run a writer on the node ``call.placement`` names; its video takes ``path``'s place here.

    The node computes, draws and encodes, with the records this machine has
    already checked. Its probe history, named and shaped as *history* says,
    is read into an array here, from which *result* (the kind's own) builds
    the record. Its video's bytes are written, as they arrive, into a hidden
    file beside ``path``: never more of them than
    :func:`~._video_job.video_byte_cap` allows, and none at all unless they
    begin as the container ``path`` names (an empty video is refused before
    a byte is read). That file takes ``path``'s place only once the node's
    whole answer has been read and checked; whatever stops the run before
    (the node, the connection, the caller's interrupt), it is removed, and
    ``path`` is left as it was.

    :return: The writer's record, its provenance naming the host; ``None``
        when the node failed and ``fallback=True`` asked to write here
        instead, after :func:`~._remote.client.run_remote` raised the one
        :class:`ComputeFallbackWarning`.
    """
    from ..io._video import settle
    from ..io._video_encoders import VideoEncoderError
    from ._remote.client import ArraySpec, Expected, StreamSpec, run_remote
    from ._video_job import CONTAINER_HEADS, video_byte_cap

    request = call.request
    width, height = call.drawn.size
    n_frames = call.run._checked.steps // call.every + 1
    name, shape = history
    record = np.zeros(shape, dtype=np.float64)
    stream = StreamSpec(
        "video",
        max_bytes=video_byte_cap(n_frames, width, height, video=request.video),
        heads=CONTAINER_HEADS[request.container],
    )
    expected = Expected(arrays=(ArraySpec(name, "float64", shape),), stream=stream)
    sent = {
        "run": call.run,
        "frame": call.drawn,
        "video": request.video,
        "container": request.container,
    }
    partial = _PartialFile(request)
    # Created before ssh starts, so a directory that does not take the video
    # fails here rather than after the node's whole run; a file that was
    # never created leaves nothing to remove.
    partial.open()
    try:
        ran = run_remote(
            function, call.placement, sent, expected, record, None, sink=partial
        )
        partial.close()
    except BaseException:
        # A stream that broke after its first bytes has written them. The
        # error that stopped the run is the one raised: closing or removing
        # the file after it may fail too (a full disk), and would hide it.
        with contextlib.suppress(OSError, VideoEncoderError):
            partial.discard()
        raise
    if ran is None:
        partial.discard()
        return None
    settle(partial.path, request.path)
    return result(call.run, record, ran)


class _FrameWhere(TypedDict):
    """What the first frame of either kind of run is drawn from alike."""

    dx: float
    shape: tuple[int, int]
    probe_positions: NDArray[np.float64]
    obstacle_mask: NDArray[np.bool_] | None
    decimation: int
    color_limit: float
    time_s: float
    last_time_s: float
    language: Language


def _probe_positions(checks: _AcousticChecks | _ElasticChecks) -> NDArray[np.float64]:
    """The probes' cell centres ``(x, y)`` in metres, as the simulation functions give them."""
    return (checks.probe_ix.astype(np.float64) + 0.5) * checks.dx


def _render_run[R: (FDTDRun, ElasticRun)](
    call: _Call[R],
    encoding: _Encoding,
    frames: Generator[DeviceArray, None, None],
    backend: Backend,
    *,
    limit: float,
    draw: Callable[[Axes, NDArray[np.float64], _FrameWhere], AxesImage],
    title: Callable[[float], str],
) -> None:
    """Draw *frames*, one at t = 0 and one every ``call.every`` steps, into the video.

    Through :func:`_render`: *draw* draws the first frame, the kind's own
    snapshot plot laid out for the whole run, from what either kind's frame
    takes alike, and *title* names the time of each later one. The last
    frame's time is the one :func:`_render` gives it, so the layout makes
    room for every title the run shows.
    """
    checks = call.run._checked
    n_frames = checks.steps // call.every + 1
    frame_dt = call.every * checks.dt
    where = _FrameWhere(
        dx=checks.dx,
        shape=checks.grid,
        probe_positions=_probe_positions(checks),
        obstacle_mask=checks.obstacle,
        decimation=checks.snapshot_decimation,
        color_limit=limit,
        time_s=0.0,
        last_time_s=_last_frame_time(checks, call.every),
        language=call.drawn.language,
    )
    _render(
        call.request,
        encoding,
        call.drawn,
        frames=frames,
        backend=backend,
        n_frames=n_frames,
        frame_dt=frame_dt,
        setup=lambda ax, field: draw(ax, field, where),
        title=title,
    )


class _RecordFields(TypedDict):
    """What the record of either kind of run holds alike once its field went into a video."""

    times: NDArray[np.float64]
    probes: NDArray[np.int_]
    probe_positions: NDArray[np.float64]
    dx: float
    dt: float
    shape: tuple[int, int]
    snapshots: None
    snapshot_times: None
    obstacle_mask: NDArray[np.bool_] | None
    snapshot_decimation: int
    provenance: RunProvenance


def _record_fields(
    checks: _AcousticChecks | _ElasticChecks, provenance: RunProvenance
) -> _RecordFields:
    """The times, the probes and the grid of a run whose field went into a video; no snapshots.

    Built from what the run checked, as the simulation functions build their
    own, so the record is the same whether the run stepped here or on a node.
    """
    return _RecordFields(
        times=np.arange(checks.steps + 1, dtype=np.float64) * checks.dt,
        probes=checks.probe_ix,
        probe_positions=_probe_positions(checks),
        dx=checks.dx,
        dt=checks.dt,
        shape=checks.grid,
        snapshots=None,
        snapshot_times=None,
        obstacle_mask=checks.obstacle,
        snapshot_decimation=checks.snapshot_decimation,
        provenance=provenance,
    )


def _driven_cells(
    source: AnySource, ny: int, nx: int
) -> tuple[int | slice, int | slice]:
    """The cells a source writes into: its own, or its whole injection line."""
    if not isinstance(source, PlaneWaveSource):
        return int(source.iy), int(source.ix)
    offset = int(source.offset)
    rows = {"down": offset, "up": ny - 1 - offset}
    if source.direction in rows:
        return rows[source.direction], slice(None)
    columns = {"right": offset, "left": nx - 1 - offset}
    return slice(None), columns[source.direction]


def _acoustic_keep(run: FDTDRun) -> NDArray[np.bool_]:
    """True where the pressure may set the colour scale, false where it is driven or damped.

    Cut to the cells a frame keeps.

    :raises ValueError: when the sources, their lines and the absorbing layer
        cover every one of them, asking for ``AnimationFrame(color_limit=...)``.
    """
    checks = run._checked
    ny, nx = checks.grid
    driven = (_driven_cells(source, ny, nx) for source in run.sources)
    return _kept(checks, driven, _ACOUSTIC_COVERING)


def _acoustic_scale(
    run: FDTDRun, color_limit: float | None
) -> float | NDArray[np.bool_]:
    """The colour limit given, or else the cells a first pass reads.

    :raises ValueError: when there is no limit and no cell to read.
    """
    if color_limit is not None:
        return color_limit
    return _acoustic_keep(run)


def _acoustic_limit(
    run: FDTDRun, compute: Compute | None, keep: NDArray[np.bool_]
) -> tuple[float, Compute]:
    """The first pass: the colour limit, and where the run really stepped."""
    checks = run._checked
    sim = _acoustic_engine(run, compute)
    no_probes = np.zeros((0, 2), dtype=np.int_)
    unrecorded = np.zeros((0, checks.steps + 1))
    frames = _march(
        sim,
        checks.steps,
        no_probes,
        checks.snapshot_every,
        checks.snapshot_decimation,
        unrecorded,
    )
    return _found_limit(sim, frames, keep, _ACOUSTIC_COVERING)


def _acoustic_result(
    run: FDTDRun, pressures: NDArray[np.float64], provenance: RunProvenance
) -> FDTDResult:
    """The record of a run whose field went into a video: its probes and times, no snapshots.

    As :func:`fdtd_simulation` builds its own, from what the run checked
    (:func:`_record_fields`).
    """
    return FDTDResult(
        # Copied by the record: a probe history is small next to the field
        # the video never stores.
        pressures=pressures,
        sources=tuple(run.sources),
        **_record_fields(run._checked, provenance),
    )


def write_fdtd_animation(
    path: str | os.PathLike[str],
    run: FDTDRun,
    *,
    compute: Compute | None = None,
    frame: AnimationFrame | None = None,
    video: VideoOptions | None = None,
) -> FDTDResult:
    """Step an acoustic FDTD run and write its pressure field to a video.

    The run is the one :func:`~phonometry.simulation.fdtd_simulation` steps,
    checked when the :class:`~phonometry.simulation.FDTDRun` was built. A
    frame or video record of another type, a path whose container rules out
    the options, an option ffmpeg could not honour (an encoder that does not
    run here, a raw encoder this ffmpeg lacks), or a missing ffmpeg is
    refused before the first step. One frame is drawn at t = 0 and one every
    ``run.recording.snapshot_every`` steps; the video shows what the
    snapshot plot of :func:`~phonometry.simulation.fdtd_simulation`'s result
    shows, laid out once for the whole run and updated in place, under
    matplotlib's default style. See the module documentation for how
    the frame is laid out and the colour scale fixed.

    :param path: Where to write the video; ``.webm``, ``.mp4`` or ``.gif``,
        as :func:`phonometry.io.write_video` writes them.
    :param run: The run (:class:`~phonometry.simulation.FDTDRun`). Its
        recording's ``snapshot_every`` is required and is the frame cadence,
        its ``snapshot_decimation`` the cells a frame keeps, and its probes
        are recorded in the result.
    :param compute: Where the run steps (:class:`Compute`); ``None`` follows
        :func:`use`, then ``PHONOMETRY_COMPUTE``, then NumPy; with a
        ``host`` the run is computed, drawn and encoded on that node, named
        in the hosts file (see the guide on remote nodes), and only the
        result and the video's bytes come back.
    :param frame: How each frame is drawn (:class:`AnimationFrame`); ``None``
        (default) is ``AnimationFrame()``: 960 by 540 pixels, English labels
        and a colour limit, in pascals, found in a first pass.
    :param video: How the video is encoded
        (:class:`phonometry.io.VideoOptions`); ``None`` (default) is
        ``VideoOptions()``, which plays at 30 frames per second unless its
        ``fps`` says otherwise.
    :return: The run's :class:`FDTDResult`, with its probes and times and no
        snapshots.
    :raises TypeError: If ``run`` is not an :class:`FDTDRun`, ``frame`` not
        an :class:`AnimationFrame`, ``video`` not a
        :class:`~phonometry.io.VideoOptions`, ``compute`` not a
        :class:`Compute`, or ``path`` neither a text nor a path; or, when
        ``compute`` names a host, a part of the run that cannot travel to a
        node: a waveform other than the ``value`` of a
        :class:`GaussianPulse`, :class:`CWSource` or :class:`SignalSource`.
    :raises ValueError: If the run records no snapshots
        (``run.recording`` is ``None``, or its ``snapshot_every`` is), the
        frame is narrower than the title of the run's last frame needs (a
        run of ten seconds or more; the message gives the width), the path's
        suffix is not one of the three or its container rules out the
        options, ``PHONOMETRY_COMPUTE`` is malformed, there is nothing to find
        the colour scale by (the message asks for
        ``AnimationFrame(color_limit=...)``), or the hosts file is malformed.
    :raises FileNotFoundError: If the directory of ``path`` does not exist
        or cannot be reached (it sits inside a directory this process
        cannot search); before any step, and before ssh starts.
    :raises FFmpegNotFoundError: If ffmpeg is not found, or on Windows is
        found only in the working directory; before any step.
    :raises VideoEncoderError: If no encoder can write the video, a raw
        ``ffmpeg_encoder`` is not in this ffmpeg (both before any step), or
        the directory of ``path`` does not take a file (before any step, and
        before ssh starts; the message names ``path``); if ffmpeg cannot be
        started or fails while writing it (the message names the encoder and
        quotes ffmpeg; ``ffmpeg_options`` it refuses fail at the first
        frames), this machine's disk does not take the bytes of a node's
        video as they arrive (it is full, say), or the finished video cannot
        take the place of ``path`` (the message says where it was left).
    :raises ComputeImportError: When the device's library is not installed
        or does not import.
    :raises ComputeDeviceError: When the device is not present or not
        usable; with ``fallback=True`` the run warns once with
        :class:`ComputeFallbackWarning` and steps on NumPy instead.
    :raises KeyError: For a ``host`` the hosts file does not name.
    :raises ComputeRemoteError: For a failure of the connection or of the
        node (one without matplotlib or the font every frame is drawn in,
        without ffmpeg, without an encoder that writes this video or the raw
        ``ffmpeg_encoder``, or whose ffmpeg refuses the ``ffmpeg_options``), or
        video bytes back that are more than the frames can take, too few to
        be a video, or not the container ``path`` names; with
        ``fallback=True`` the run warns once with
        :class:`ComputeFallbackWarning` and writes the video here on NumPy
        instead.
    :raises ImportError: If matplotlib is not installed, for a video written
        here.
    """
    call = _checked_call(
        path,
        run,
        FDTDRun,
        compute=compute,
        frame=frame,
        video=video,
        scale=_acoustic_scale,
    )
    checks = run._checked
    history = (checks.probe_ix.shape[0], checks.steps + 1)
    if call.placement.host is not None:
        there = _node_video(
            "write_fdtd_animation", call, ("pressures", history), _acoustic_result
        )
        if there is not None:
            return there
        # The node failed and the request asked to write here instead.
        compute = _placement_here(call.placement)
    encoding, limit, compute = _encoding_and_limit(call, compute, _acoustic_limit)
    sim = _acoustic_engine(run, compute)
    pressures = np.zeros(history, dtype=np.float64)
    frames = _march(
        sim,
        checks.steps,
        checks.probe_ix,
        call.every,
        checks.snapshot_decimation,
        pressures,
    )

    def draw(ax: Axes, field: NDArray[np.float64], where: _FrameWhere) -> AxesImage:
        from .._plot.simulation import fdtd_frame

        return fdtd_frame(ax, field, sources=run.sources, **where)

    def title(time_s: float) -> str:
        from .._plot.simulation import fdtd_snapshot_title

        return fdtd_snapshot_title(time_s, call.drawn.language)

    _render_run(
        call, encoding, frames, sim._backend, limit=limit, draw=draw, title=title
    )
    return _acoustic_result(run, pressures, sim.provenance)


def _elastic_driven_cells(source: ElasticSource) -> tuple[int | slice, int | slice]:
    """The cells a source writes into: an explosion's own, or the two either side of a force's face."""
    iy, ix = int(source.iy), int(source.ix)
    if isinstance(source, ExplosionSource):
        return iy, ix
    if source.direction == "x":
        return iy, slice(ix, ix + 2)
    return slice(iy, iy + 2), ix


def _elastic_keep(run: ElasticRun) -> NDArray[np.bool_]:
    """True where the drawn field may set the colour scale, false where it is driven or damped.

    A free surface is not driven and stays in. Cut to the cells a frame keeps.

    :raises ValueError: when the sources and the absorbing layer cover every
        one of them, asking for ``AnimationFrame(color_limit=...)``.
    """
    driven = map(_elastic_driven_cells, run.sources)
    return _kept(run._checked, driven, _ELASTIC_COVERING)


def _elastic_scale(
    run: ElasticRun, color_limit: float | None
) -> float | NDArray[np.bool_]:
    """The colour limit given, or else the cells a first pass reads.

    :raises ValueError: when there is no limit and no cell to read.
    """
    if color_limit is not None:
        return color_limit
    return _elastic_keep(run)


def _elastic_limit(
    run: ElasticRun, compute: Compute | None, keep: NDArray[np.bool_]
) -> tuple[float, Compute]:
    """The first pass: the colour limit, and where the run really stepped."""
    checks = run._checked
    sim = _elastic_engine(run, compute)
    no_probes = np.zeros((0, 2), dtype=np.int_)
    unrecorded = np.zeros((0, len(checks.fields), checks.steps + 1))
    frames = _elastic_march(
        sim,
        checks.steps,
        no_probes,
        checks.fields,
        checks.snapshot_every,
        checks.snapshot_field,
        checks.snapshot_decimation,
        unrecorded,
    )
    return _found_limit(sim, frames, keep, _ELASTIC_COVERING)


def _elastic_result(
    run: ElasticRun, signals: NDArray[np.float64], provenance: RunProvenance
) -> ElasticFDTDResult:
    """The record of an elastic run whose field went into a video, as :func:`_acoustic_result`."""
    checks = run._checked
    return ElasticFDTDResult(
        # Copied by the record: the probe histories are small next to the
        # field the video never stores.
        signals=signals,
        probe_fields=checks.fields,
        sources=tuple(run.sources),
        snapshot_field=checks.snapshot_field,
        free_sides=checks.free_sides,
        **_record_fields(checks, provenance),
    )


def write_elastic_fdtd_animation(
    path: str | os.PathLike[str],
    run: ElasticRun,
    *,
    compute: Compute | None = None,
    frame: AnimationFrame | None = None,
    video: VideoOptions | None = None,
) -> ElasticFDTDResult:
    """Step an elastic FDTD run and write one of its fields to a video.

    The run is the one :func:`~phonometry.simulation.elastic_fdtd_simulation`
    steps, checked when the :class:`~phonometry.simulation.ElasticRun` was
    built; a frame or video record of another type, a path whose container
    rules out the options, an option ffmpeg could not honour, or a missing
    ffmpeg is refused before the first step. The video draws the field
    ``run.recording.snapshot_field`` names at the cell centres (the
    synthetic pressure, or one velocity component), one frame at t = 0 and
    one every ``run.recording.snapshot_every`` steps, as the snapshot plot
    of :func:`~phonometry.simulation.elastic_fdtd_simulation`'s result draws
    it, laid out once for the whole run. See the module
    documentation for how the frame is laid out and the colour scale fixed.

    :param path: Where to write the video; ``.webm``, ``.mp4`` or ``.gif``.
    :param run: The run (:class:`~phonometry.simulation.ElasticRun`). Its
        recording's ``snapshot_every`` is required and is the frame cadence,
        its ``snapshot_field`` the field drawn, its ``snapshot_decimation``
        the cells a frame keeps, and its probes are recorded in the result.
    :param compute: Where the run steps (:class:`Compute`); ``None`` follows
        :func:`use`, then ``PHONOMETRY_COMPUTE``, then NumPy; with a
        ``host`` the run is computed, drawn and encoded on that node, named
        in the hosts file (see the guide on remote nodes), and only the
        result and the video's bytes come back.
    :param frame: How each frame is drawn (:class:`AnimationFrame`); ``None``
        (default) is ``AnimationFrame()``: 960 by 540 pixels, English labels
        and a colour limit found in a first pass. Its ``color_limit`` is in
        the unit of the field drawn: pascals for ``"p"``, metres per second
        for ``"vx"`` and ``"vy"``.
    :param video: How the video is encoded
        (:class:`phonometry.io.VideoOptions`); ``None`` (default) is
        ``VideoOptions()``, which plays at 30 frames per second unless its
        ``fps`` says otherwise.
    :return: The run's :class:`ElasticFDTDResult`, with its probes and times
        and no snapshots.
    :raises TypeError: If ``run`` is not an :class:`ElasticRun`, ``frame``
        not an :class:`AnimationFrame`, ``video`` not a
        :class:`~phonometry.io.VideoOptions`, ``compute`` not a
        :class:`Compute`, or ``path`` neither a text nor a path; or, when
        ``compute`` names a host, a part of the run that cannot travel to a
        node: an :class:`ExplosionSource` or a :class:`ForceSource` whose
        waveform is a callable other than the ``value`` of a
        :class:`~phonometry.simulation.GaussianPulse`,
        :class:`~phonometry.simulation.CWSource` or
        :class:`~phonometry.simulation.SignalSource`.
    :raises ValueError: If the run records no snapshots
        (``run.recording`` is ``None``, or its ``snapshot_every`` is), the
        frame is narrower than the title of the run's last frame needs (a
        run of ten seconds or more; the message gives the width), the path's
        suffix is not one of the three or its container rules out the
        options, ``PHONOMETRY_COMPUTE`` is malformed, there is nothing to find
        the colour scale by (the message asks for
        ``AnimationFrame(color_limit=...)``), or the hosts file is malformed.
    :raises FileNotFoundError: If the directory of ``path`` does not exist
        or cannot be reached (it sits inside a directory this process
        cannot search); before any step, and before ssh starts.
    :raises FFmpegNotFoundError: If ffmpeg is not found, or on Windows is
        found only in the working directory; before any step.
    :raises VideoEncoderError: If no encoder can write the video, a raw
        ``ffmpeg_encoder`` is not in this ffmpeg (both before any step), or
        the directory of ``path`` does not take a file (before any step, and
        before ssh starts; the message names ``path``); if ffmpeg cannot be
        started or fails while writing it (the message names the encoder and
        quotes ffmpeg; ``ffmpeg_options`` it refuses fail at the first
        frames), this machine's disk does not take the bytes of a node's
        video as they arrive (it is full, say), or the finished video cannot
        take the place of ``path`` (the message says where it was left).
    :raises ComputeImportError: When the device's library is not installed
        or does not import.
    :raises ComputeDeviceError: When the device is not present or not
        usable; with ``fallback=True`` the run warns once with
        :class:`ComputeFallbackWarning` and steps on NumPy instead.
    :raises KeyError: For a ``host`` the hosts file does not name.
    :raises ComputeRemoteError: For a failure of the connection or of the
        node (one without matplotlib or the font every frame is drawn in,
        without ffmpeg, without an encoder that writes this video or the raw
        ``ffmpeg_encoder``, or whose ffmpeg refuses the ``ffmpeg_options``), or
        video bytes back that are more than the frames can take, too few to
        be a video, or not the container ``path`` names; with
        ``fallback=True`` the run warns once with
        :class:`ComputeFallbackWarning` and writes the video here on NumPy
        instead.
    :raises ImportError: If matplotlib is not installed, for a video written
        here.
    """
    call = _checked_call(
        path,
        run,
        ElasticRun,
        compute=compute,
        frame=frame,
        video=video,
        scale=_elastic_scale,
    )
    checks = run._checked
    history = (checks.probe_ix.shape[0], len(checks.fields), checks.steps + 1)
    if call.placement.host is not None:
        there = _node_video(
            "write_elastic_fdtd_animation", call, ("signals", history), _elastic_result
        )
        if there is not None:
            return there
        # The node failed and the request asked to write here instead.
        compute = _placement_here(call.placement)
    encoding, limit, compute = _encoding_and_limit(call, compute, _elastic_limit)
    sim = _elastic_engine(run, compute)
    signals = np.zeros(history, dtype=np.float64)
    frames = _elastic_march(
        sim,
        checks.steps,
        checks.probe_ix,
        checks.fields,
        call.every,
        checks.snapshot_field,
        checks.snapshot_decimation,
        signals,
    )

    def draw(ax: Axes, field: NDArray[np.float64], where: _FrameWhere) -> AxesImage:
        from .._plot.simulation import elastic_frame

        return elastic_frame(
            ax,
            field,
            sources=run.sources,
            snapshot_field=checks.snapshot_field,
            **where,
        )

    def title(time_s: float) -> str:
        from .._plot.simulation import elastic_snapshot_title

        return elastic_snapshot_title(
            time_s, checks.snapshot_field, call.drawn.language
        )

    _render_run(
        call, encoding, frames, sim._backend, limit=limit, draw=draw, title=title
    )
    return _elastic_result(run, signals, sim.provenance)
