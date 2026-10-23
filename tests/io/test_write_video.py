#  Copyright (c) 2026. Jose Manuel Requena Plens
"""``io.write_video`` against a fake ffmpeg: what it runs, what it refuses, what it leaves."""

from __future__ import annotations

import gc
import logging
import subprocess
import sys
import threading
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest

pytest.importorskip("matplotlib")
import fake_ffmpeg
import matplotlib as mpl
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_svg import FigureCanvasSVG
from matplotlib.figure import Figure

from phonometry import io

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path

    from matplotlib.lines import Line2D

# A test that is refused before the encode never saves the animation it built,
# and matplotlib says so when that animation is collected.
pytestmark = pytest.mark.filterwarnings(
    "ignore:Animation was deleted without rendering anything:UserWarning"
)


@pytest.fixture(autouse=True)
def _collect_the_animations() -> Iterator[None]:
    """Collect each test's animations while the filter above still applies.

    An animation holds a reference cycle, so only the garbage collector frees
    it, and left to itself it may do so during a test of another module.
    """
    yield
    gc.collect()


def _animation(
    *,
    frames: int = 6,
    pixels: tuple[int, int] = (200, 150),
    facecolor: str = "white",
    canvas: type = FigureCanvasAgg,
    on_frame: Callable[[int, Figure], None] | None = None,
    interval: float = 50.0,
) -> FuncAnimation:
    """A small line animation whose figure is exactly *pixels* at 100 dpi."""
    width, height = pixels
    fig = Figure(
        figsize=((width + 0.5) / 100, (height + 0.5) / 100),
        dpi=100,
        facecolor=facecolor,
    )
    canvas(fig)
    ax = fig.add_subplot()
    (line,) = ax.plot([0.0, 1.0], [0.0, 1.0])

    def update(k: int) -> tuple[Line2D]:
        if on_frame is not None:
            on_frame(k, fig)
        line.set_ydata([0.0, float(k)])
        return (line,)

    return FuncAnimation(
        fig,
        update,
        frames=frames,
        interval=interval,
        blit=False,
        cache_frame_data=False,
        repeat=False,
    )


def _after(argv: list[str], flag: str) -> str:
    return argv[argv.index(flag) + 1]


def test_a_webm_goes_through_the_chosen_encoder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    target = tmp_path / "wave.webm"
    io.write_video(target, _animation())
    assert target.read_bytes().startswith(b"\x1a\x45\xdf\xa3")
    (encode,) = fake.encodes()
    argv = encode["argv"]
    assert _after(argv, "-c:v") == "libsvtav1"
    assert _after(argv, "-s") == "200x150"
    assert _after(argv, "-pix_fmt") == "rgba"  # the input; the output follows
    assert argv[argv.index("-c:v") :].count("yuv420p") == 1
    assert _after(argv, "-f") == "rawvideo"
    assert argv[-3:-1] == ["-f", "webm"]
    assert encode["frames"] == 6
    assert encode["remainder"] == 0


def test_an_mp4_starts_fast_and_tags_hevc(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    io.write_video(
        tmp_path / "wave.mp4",
        _animation(),
        video=io.VideoOptions(encoder="cpu", codec="hevc"),
    )
    argv = fake.encodes()[0]["argv"]
    assert _after(argv, "-c:v") == "libx265"
    assert _after(argv, "-tag:v") == "hvc1"
    assert _after(argv, "-movflags") == "+faststart"


def test_a_gif_is_one_palette_run_on_the_cpu(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    target = tmp_path / "wave.gif"
    io.write_video(target, _animation(), video=io.VideoOptions(quality="high"))
    assert target.read_bytes().startswith(b"GIF89a")
    assert fake.trials() == []
    argv = fake.encodes()[0]["argv"]
    assert "-c:v" not in argv
    assert "palettegen=max_colors=256" in _after(argv, "-vf")
    assert _after(argv, "-loop") == "0"


def test_an_odd_figure_is_padded_with_its_own_colour(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    io.write_video(
        tmp_path / "w.webm", _animation(pixels=(201, 151), facecolor="#336699")
    )
    argv = fake.encodes()[0]["argv"]
    assert _after(argv, "-s") == "201x151"
    assert _after(argv, "-vf") == "pad=ceil(iw/2)*2:ceil(ih/2)*2:color=#336699"


def test_the_callers_settings_do_not_reach_the_frames(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = tmp_path / "first.rgba"
    fake = fake_ffmpeg.install(tmp_path, monkeypatch, first_frame=str(first))
    animation = _animation(facecolor="#336699", canvas=FigureCanvasSVG)
    with mpl.rc_context(
        {"savefig.bbox": "tight", "savefig.dpi": 300, "savefig.facecolor": "none"}
    ):
        io.write_video(tmp_path / "w.webm", animation)
    assert _after(fake.encodes()[0]["argv"], "-s") == "200x150"
    corner = np.frombuffer(first.read_bytes(), dtype=np.uint8)[:4]
    assert corner.tolist() == [0x33, 0x66, 0x99, 255]


def test_a_figure_resized_by_the_animation_keeps_its_size(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)

    def grow(k: int, fig: Figure) -> None:
        if k == 2:
            fig.set_size_inches(3.0, 3.0)

    io.write_video(tmp_path / "w.webm", _animation(on_frame=grow))
    (encode,) = fake.encodes()
    assert (encode["frames"], encode["remainder"]) == (6, 0)


def test_a_failed_encode_keeps_the_old_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_ffmpeg.install(tmp_path, monkeypatch, die_after_frames=3)
    target = tmp_path / "w.webm"
    target.write_bytes(b"the video that was there")
    animation = _animation(frames=8)
    with pytest.raises(io.VideoEncoderError, match="muxer failed"):
        io.write_video(target, animation)
    assert target.read_bytes() == b"the video that was there"
    assert [p.name for p in tmp_path.iterdir() if p.name.endswith(".partial")] == []


def test_a_finished_video_that_cannot_take_the_place_of_path_says_where_it_is(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import pathlib

    fake_ffmpeg.install(tmp_path, monkeypatch)
    target = tmp_path / "w.webm"
    target.write_bytes(b"the video that was there")

    def held_open(self: pathlib.Path, other: object) -> pathlib.Path:
        msg = "[WinError 32] the file is being used by another process"
        raise PermissionError(msg)

    monkeypatch.setattr(pathlib.Path, "replace", held_open)
    animation = _animation()
    with pytest.raises(
        io.VideoEncoderError, match="could not take the place of"
    ) as caught:
        io.write_video(target, animation)
    assert target.read_bytes() == b"the video that was there"
    (left,) = [p for p in tmp_path.iterdir() if p.name.endswith(".partial")]
    assert str(left) in str(caught.value)
    assert left.read_bytes().startswith(b"\x1a\x45\xdf\xa3")


def test_two_writes_to_one_path_never_share_a_partial_file(tmp_path: Path) -> None:
    from phonometry.io._video import video_request

    request = video_request(tmp_path / "w.webm", io.VideoOptions())
    first, second = request.new_partial(), request.new_partial()
    assert first != second
    for partial in (first, second):
        assert partial.parent == tmp_path
        assert partial.name.startswith(".w.webm.")
        assert partial.name.endswith(".partial")
        assert not partial.exists()


def test_an_ffmpeg_that_cannot_be_started_is_an_encoder_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from phonometry.io import _video as pipe_module
    from phonometry.io import _video_encoders as ve

    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    described = ve.describe(str(fake.launcher))

    def refused(*args: object, **kwargs: object) -> object:
        raise PermissionError(13, "Permission denied", str(fake.launcher))

    # Only the pipe starts a process now: the ffmpeg is described already and
    # a raw encoder has no trial.
    monkeypatch.setattr(pipe_module.subprocess, "Popen", refused)
    request = pipe_module.video_request(
        tmp_path / "w.webm", io.VideoOptions(ffmpeg_encoder="libvpx-vp9")
    )
    animation = _animation()
    with pytest.raises(io.VideoEncoderError, match="could not start"):
        pipe_module.encode(request, animation, ffmpeg=described)
    assert [p.name for p in tmp_path.iterdir() if p.name.endswith(".partial")] == []


def test_the_pipe_starts_ffmpeg_without_a_console_window(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import subprocess

    from phonometry.io import _video as pipe_module
    from phonometry.io import _video_encoders as ve

    fake_ffmpeg.install(tmp_path, monkeypatch)
    seen: list[object] = []
    real_popen = subprocess.Popen

    def popen(*args: object, **kwargs: object) -> object:
        seen.append(kwargs.get("creationflags"))
        return real_popen(*args, **kwargs)  # type: ignore[call-overload]

    # subprocess.run starts its process through Popen too, so the trials and
    # the -version run are seen here beside the pipe.
    monkeypatch.setattr(pipe_module.subprocess, "Popen", popen)
    io.write_video(tmp_path / "w.webm", _animation())
    assert seen
    assert set(seen) == {ve.NO_WINDOW}


def test_an_error_in_the_animation_is_its_own(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_ffmpeg.install(tmp_path, monkeypatch)

    def fail(k: int, _fig: Figure) -> None:
        if k == 3:
            msg = "drawing failed at frame 3"
            raise RuntimeError(msg)

    target = tmp_path / "w.webm"
    animation = _animation(on_frame=fail)
    with pytest.raises(RuntimeError, match="drawing failed") as caught:
        io.write_video(target, animation)
    assert caught.type is RuntimeError
    assert not target.exists()
    # On Windows the fake runs behind cmd.exe, which a kill does not reach,
    # and the orphaned fake writes its output when its stdin closes; a real
    # ffmpeg is not wrapped, and dies with the kill.
    if sys.platform != "win32":
        assert [p.name for p in tmp_path.iterdir() if p.name.endswith(".partial")] == []


def _unclosed(recorded: pytest.WarningsRecorder) -> list[str]:
    """What the garbage collector says was left open, a pipe or a process."""
    gc.collect()
    return [str(w.message) for w in recorded if issubclass(w.category, ResourceWarning)]


def test_a_finished_write_leaves_no_pipe_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, recwarn: pytest.WarningsRecorder
) -> None:
    fake_ffmpeg.install(tmp_path, monkeypatch)
    animation = _animation()
    gc.collect()
    recwarn.clear()
    io.write_video(tmp_path / "w.webm", animation)
    assert _unclosed(recwarn) == []


def test_a_failed_write_leaves_no_pipe_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, recwarn: pytest.WarningsRecorder
) -> None:
    fake_ffmpeg.install(tmp_path, monkeypatch, die_after_frames=3)
    animation = _animation(frames=8)
    gc.collect()
    recwarn.clear()
    with pytest.raises(io.VideoEncoderError, match="muxer failed"):
        io.write_video(tmp_path / "w.webm", animation)
    assert _unclosed(recwarn) == []


def test_ffmpeg_is_known_while_it_encodes_and_forgotten_once_it_exits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The ffmpeg of a video is tracked from its start until it has exited, whether it finished or failed."""
    from phonometry.io import _video as pipe_module

    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    running: list[int] = []

    def count(_frame: int, _fig: Figure) -> None:
        running.append(len(pipe_module._RUNNING))

    io.write_video(tmp_path / "w.webm", _animation(on_frame=count))
    assert running[-1] == 1
    assert pipe_module._RUNNING == set()
    fake.update(die_after_frames=3)
    longer = _animation(frames=8)
    with pytest.raises(io.VideoEncoderError, match="muxer failed"):
        io.write_video(tmp_path / "w.webm", longer)
    assert pipe_module._RUNNING == set()


def test_stopping_the_running_encoders_ends_each_of_them(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """What a process about to end at once calls: every ffmpeg still running is stopped, and waited for."""
    from phonometry.io import _video as pipe_module

    # Stands for an ffmpeg that has its last frame and goes on encoding.
    encoder = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    monkeypatch.setattr(pipe_module, "_RUNNING", {encoder})
    try:
        pipe_module.stop_running_encoders()
        assert encoder.poll() is not None
    finally:
        encoder.kill()
        encoder.wait(timeout=30)


def test_a_reader_of_ffmpeg_that_cannot_start_stops_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, recwarn: pytest.WarningsRecorder
) -> None:
    from phonometry.io import _video as pipe_module

    class Unstartable(threading.Thread):
        def start(self) -> None:
            msg = "can't start new thread"
            raise RuntimeError(msg)

    fake_ffmpeg.install(tmp_path, monkeypatch)
    # The module's own name only: no other thread of the process is touched.
    monkeypatch.setattr(pipe_module, "threading", SimpleNamespace(Thread=Unstartable))
    animation = _animation()
    gc.collect()
    recwarn.clear()
    with pytest.raises(io.VideoEncoderError, match="can't start new thread"):
        io.write_video(tmp_path / "w.webm", animation)
    assert _unclosed(recwarn) == []
    # On Windows the fake runs behind cmd.exe, which a kill does not reach,
    # and the orphaned fake writes its output when its stdin closes.
    if sys.platform != "win32":
        assert [p.name for p in tmp_path.iterdir() if p.name.endswith(".partial")] == []


@pytest.mark.parametrize(
    ("interval", "fps", "rate"),
    [
        (50.0, None, "20/1"),
        (50.0, 30000 / 1001, "30000/1001"),
        (40.0, 12.5, "25/2"),
        # Under one frame a second the rate stays positive: a frame an hour.
        (50.0, 1 / 3600, "1/3600"),
        (3_600_000.0, None, "1/3600"),
        (2500.0, None, "2/5"),
    ],
)
def test_the_frame_rate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    interval: float,
    fps: float | None,
    rate: str,
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    io.write_video(
        tmp_path / "w.webm",
        _animation(interval=interval),
        video=io.VideoOptions(fps=fps),
    )
    assert _after(fake.encodes()[0]["argv"], "-r") == rate


@pytest.mark.parametrize("interval", [0.0, -50.0, float("nan"), float("inf")])
def test_an_interval_that_is_not_a_positive_finite_number_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, interval: float
) -> None:
    """Zero, a negative interval, NaN and infinity are refused before ffmpeg runs."""
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    animation = _animation()
    # Set on the animation itself: matplotlib's timer refuses a NaN interval.
    monkeypatch.setattr(animation, "_interval", interval)
    with pytest.raises(ValueError, match="interval is not a positive finite number"):
        io.write_video(tmp_path / "w.webm", animation)
    assert fake.calls() == []


def test_an_interrupt_while_ffmpeg_finishes_stops_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An interrupt while ffmpeg finishes the file (a GIF's palette, a slow encoder) stops ffmpeg.

    The interrupt reaches the caller as it is, ffmpeg is stopped rather than
    left writing, and no hidden file is left beside the path.
    """
    from phonometry.io import _video as pipe_module

    fake_ffmpeg.install(tmp_path, monkeypatch)
    aborted: list[bool] = []
    abort = pipe_module._FramePipe.abort

    def interrupted(_pipe: object) -> None:
        raise KeyboardInterrupt

    def counted(pipe: pipe_module._FramePipe) -> None:
        aborted.append(True)
        abort(pipe)

    monkeypatch.setattr(pipe_module._FramePipe, "close", interrupted)
    monkeypatch.setattr(pipe_module._FramePipe, "abort", counted)
    animation = _animation()
    with pytest.raises(KeyboardInterrupt):
        io.write_video(tmp_path / "w.webm", animation)
    assert aborted == [True]
    assert not (tmp_path / "w.webm").exists()
    # On Windows the fake runs behind cmd.exe, which a kill does not reach,
    # and the orphaned fake writes its output when its stdin closes.
    if sys.platform != "win32":
        assert [p.name for p in tmp_path.iterdir() if p.name.endswith(".partial")] == []


def test_a_raw_encoder_passes_through(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    io.write_video(
        tmp_path / "w.webm",
        _animation(),
        video=io.VideoOptions(
            ffmpeg_encoder="libvpx-vp9", ffmpeg_options=("-crf", "44", "-b:v", "0")
        ),
    )
    assert fake.trials() == []
    argv = fake.encodes()[0]["argv"]
    start = argv.index("-c:v")
    assert argv[start : start + 6] == ["-c:v", "libvpx-vp9", "-crf", "44", "-b:v", "0"]
    assert "yuv420p" not in argv


@pytest.mark.parametrize(
    ("changes", "error", "match"),
    [
        ({"encoder": "cpu", "ffmpeg_encoder": "libx264"}, ValueError, "ffmpeg_encoder"),
        ({"codec": "h264", "ffmpeg_encoder": "libx264"}, ValueError, "ffmpeg_encoder"),
        ({"ffmpeg_encoder": "-c:v"}, ValueError, "ffmpeg_encoder"),
        ({"ffmpeg_encoder": 264}, TypeError, "ffmpeg_encoder"),
        ({"ffmpeg_options": "-crf 30"}, TypeError, "ffmpeg_options"),
        ({"ffmpeg_options": (30,)}, TypeError, "ffmpeg_options"),
        ({"fps": 0.0}, ValueError, "fps"),
        ({"fps": "30"}, TypeError, "fps"),
        ({"encoder": "gpu"}, ValueError, "encoder"),
        ({"codec": "mpeg2"}, ValueError, "codec"),
        ({"quality": 3}, TypeError, "quality"),
        (
            {"encoder": "videotoolbox", "codec": "av1"},
            ValueError,
            "encoder='videotoolbox' writes",
        ),
        ({"encoder": "nvenc", "codec": "vp9"}, ValueError, "encoder='nvenc' writes"),
    ],
)
def test_a_bad_option_is_refused_when_the_record_is_built(
    changes: dict[str, Any], error: type[Exception], match: str
) -> None:
    with pytest.raises(error, match=match):
        io.VideoOptions(**changes)


def test_the_options_hold_what_they_were_given() -> None:
    options = io.VideoOptions(
        fps=24, ffmpeg_encoder="libvpx-vp9", ffmpeg_options=["-crf", "40"]
    )
    assert options.ffmpeg_options == ("-crf", "40")
    assert options.fps == 24.0
    assert io.VideoOptions() == io.VideoOptions(encoder="auto", quality="standard")
    with pytest.raises(AttributeError, match="fps"):
        options.fps = 30.0  # type: ignore[misc]


@pytest.mark.parametrize(
    ("name", "video", "error", "match"),
    [
        ("w.avi", None, ValueError, "webm"),
        ("w.mp4", io.VideoOptions(codec="vp9"), ValueError, "holds"),
        ("w.gif", io.VideoOptions(codec="av1"), ValueError, "GIF"),
        ("w.gif", io.VideoOptions(encoder="nvenc"), ValueError, "CPU"),
        ("w.gif", io.VideoOptions(ffmpeg_encoder="libx264"), ValueError, "GIF"),
        (
            "w.webm",
            io.VideoOptions(encoder="videotoolbox"),
            ValueError,
            "encoder='videotoolbox' writes",
        ),
        ("w.webm", {"encoder": "cpu"}, TypeError, "video"),
        ("missing/w.webm", None, FileNotFoundError, "does not exist"),
    ],
)
def test_a_bad_path_or_combination_starts_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    video: object,
    error: type[Exception],
    match: str,
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    animation = _animation()
    with pytest.raises(error, match=match):
        io.write_video(tmp_path / name, animation, video=video)  # type: ignore[arg-type]
    assert fake.calls() == []


@pytest.mark.parametrize(
    ("name", "video"),
    [
        ("w.webm", io.VideoOptions(encoder="nvenc")),
        ("w.webm", io.VideoOptions(encoder="qsv", codec="vp9")),
        ("w.mp4", io.VideoOptions(encoder="videotoolbox")),
        ("w.mp4", io.VideoOptions(encoder="nvenc", codec="hevc")),
        ("w.gif", io.VideoOptions(encoder="cpu")),
    ],
)
def test_an_encoder_that_writes_a_codec_the_container_holds_is_accepted(
    tmp_path: Path, name: str, video: io.VideoOptions
) -> None:
    from phonometry.io._video import video_request

    assert video_request(tmp_path / name, video).video is video


def test_a_path_or_an_animation_of_another_type_starts_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    animation = _animation()
    with pytest.raises(TypeError, match="path"):
        io.write_video(5, animation)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="anim"):
        io.write_video(tmp_path / "w.webm", "frames")  # type: ignore[arg-type]
    assert fake.calls() == []


def test_a_missing_ffmpeg_is_its_own_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(mpl.rcParams, "animation.ffmpeg_path", "no-such-ffmpeg-here")
    animation = _animation()
    with pytest.raises(io.FFmpegNotFoundError, match="animation.ffmpeg_path"):
        io.write_video(tmp_path / "w.webm", animation)


def test_the_choice_is_logged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    fake_ffmpeg.install(tmp_path, monkeypatch)
    with caplog.at_level(logging.INFO, logger="phonometry.io"):
        io.write_video(tmp_path / "w.webm", _animation())
    assert any("libsvtav1" in r.getMessage() for r in caplog.records)
