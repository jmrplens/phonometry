#  Copyright (c) 2026. Jose Manuel Requena Plens
"""``io.write_video`` against a fake ffmpeg: what it runs, what it refuses, what it leaves."""

from __future__ import annotations

import gc
import logging
import os
import subprocess
import sys
import threading
from collections import deque
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest

pytest.importorskip("matplotlib")
import fake_ffmpeg
import matplotlib as mpl
import refusing_disk
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_svg import FigureCanvasSVG
from matplotlib.figure import Figure

from phonometry import io

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from typing import BinaryIO

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
    facecolor: str | tuple[float, float, float, float] = "white",
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


@pytest.mark.parametrize(
    ("facecolor", "colour"),
    [
        # 0.7 x 255 = 178.5: Agg rounds the half up to b3, as the pad must.
        ((0.2, 0.4, 0.6, 0.5), "99b3cc"),
        ((0.0, 0.0, 0.0, 0.5), "808080"),
        ((1.0, 0.0, 0.0, 0.25), "ffbfbf"),
    ],
)
def test_a_transparent_figure_is_padded_with_the_colour_its_frames_show(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    facecolor: tuple[float, float, float, float],
    colour: str,
) -> None:
    """The pad is the facecolor laid on white as Animation.save lays it, level for level."""
    first = tmp_path / "first.rgba"
    fake = fake_ffmpeg.install(tmp_path, monkeypatch, first_frame=str(first))
    io.write_video(
        tmp_path / "w.webm", _animation(pixels=(201, 151), facecolor=facecolor)
    )
    pad = _after(fake.encodes()[0]["argv"], "-vf")
    assert pad == f"pad=ceil(iw/2)*2:ceil(ih/2)*2:color=#{colour}"
    corner = np.frombuffer(first.read_bytes(), dtype=np.uint8)[:4]
    assert bytes(corner).hex() == f"{colour}ff"


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


class _OwnRGBACanvas(FigureCanvasAgg):
    """A canvas that writes RGBA its own way, as Cairo's does: here, every pixel black and clear."""

    def print_rgba(self, filename_or_obj: BinaryIO, **_kwargs: object) -> None:
        width, height = (int(side) for side in self.figure.bbox.size)
        filename_or_obj.write(bytes(width * height * 4))


def test_every_frame_is_drawn_with_agg_whatever_the_canvas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A canvas with its own RGBA writer (Cairo's) does not draw the frames: Agg does."""
    first = tmp_path / "first.rgba"
    fake_ffmpeg.install(tmp_path, monkeypatch, first_frame=str(first))
    animation = _animation(facecolor="#336699", canvas=_OwnRGBACanvas)
    io.write_video(tmp_path / "w.webm", animation)
    corner = np.frombuffer(first.read_bytes(), dtype=np.uint8)[:4]
    assert corner.tolist() == [0x33, 0x66, 0x99, 255]


@pytest.mark.skipif(
    sys.platform == "win32", reason="a Windows file name cannot hold a colon"
)
def test_ffmpeg_is_handed_the_absolute_path_of_the_file_it_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A relative ``x:y/w.webm`` would reach ffmpeg as the protocol ``x``."""
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    (tmp_path / "x:y").mkdir()
    monkeypatch.chdir(tmp_path)
    io.write_video("x:y/w.webm", _animation())
    written = Path(fake.encodes()[0]["argv"][-1])
    assert written.is_absolute()
    assert written.parent == tmp_path / "x:y"
    assert (tmp_path / "x:y" / "w.webm").read_bytes().startswith(b"\x1a\x45\xdf\xa3")


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


def test_a_failed_encode_names_the_encoder_that_ran(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The fake's NVENC fails its trial, so SVT-AV1 writes, and dies at frame 3.
    fake_ffmpeg.install(tmp_path, monkeypatch, die_after_frames=3)
    animation = _animation(frames=8)
    with pytest.raises(io.VideoEncoderError) as caught:
        io.write_video(tmp_path / "w.webm", animation)
    assert "with the encoder libsvtav1; ffmpeg said:" in str(caught.value)


def test_an_encoder_that_fails_once_every_frame_is_in_says_how_ffmpeg_exited(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ffmpeg read every frame and exited with an error while it finished the file."""
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    target = tmp_path / "w.webm"
    target.write_bytes(b"the video that was there")
    animation = _animation()
    aom = io.VideoOptions(ffmpeg_encoder="libaom-av1")
    with pytest.raises(
        io.VideoEncoderError,
        match=r"^ffmpeg exited with status 1 while writing .*w\.webm with the "
        r"encoder libaom-av1; ffmpeg said:\nfake ffmpeg: Error while opening "
        r"encoder libaom-av1$",
    ):
        io.write_video(target, animation, video=aom)
    assert fake.encodes()[0]["frames"] == 6
    assert target.read_bytes() == b"the video that was there"
    if sys.platform != "win32":
        assert [p.name for p in tmp_path.iterdir() if p.name.endswith(".partial")] == []


def test_a_partial_file_the_system_will_not_remove_does_not_hide_the_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_ffmpeg.install(tmp_path, monkeypatch, die_after_frames=3)
    target = tmp_path / "w.webm"
    target.write_bytes(b"the video that was there")
    refusing_disk.hold_partials(monkeypatch)
    animation = _animation(frames=8)
    # ffmpeg's failure, not the one removing its unfinished file met after it.
    with pytest.raises(io.VideoEncoderError, match="muxer failed"):
        io.write_video(target, animation)
    assert target.read_bytes() == b"the video that was there"


def test_a_name_whose_status_cannot_be_read_is_left_to_the_check_that_the_directory_takes_a_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Inside a directory without search permission the status of the name
    # cannot be read, so nothing can tell a directory from a file there; the
    # name is left to the check that the directory takes a file, which finds
    # what the directory allows before the first frame. Here it takes one, and
    # the fake runs in a process of its own, so the write goes through.
    fake_ffmpeg.install(tmp_path, monkeypatch)
    target = tmp_path / "w.webm"
    refusing_disk.refuse_status(monkeypatch, target)
    io.write_video(target, _animation())
    assert target.read_bytes().startswith(b"\x1a\x45\xdf\xa3")


def test_a_directory_that_cannot_be_reached_is_refused_before_anything_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The path's directory sits inside one this process cannot search: it
    # may exist, but nothing can be written into it, nor told about it.
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    target = tmp_path / "locked" / "sub" / "w.webm"
    target.parent.mkdir(parents=True)
    refusing_disk.refuse_status(monkeypatch, target.parent)
    animation = _animation()
    with pytest.raises(
        FileNotFoundError, match="does not exist or cannot be reached"
    ) as caught:
        io.write_video(target, animation)
    # The message quotes the directory as Python writes it, so on Windows
    # its backslashes are doubled.
    assert repr(str(target.parent)) in str(caught.value)
    assert fake.calls() == []


@pytest.mark.parametrize("directory", ["refusing", "proc"])
def test_a_directory_that_does_not_take_the_video_is_refused_before_a_frame_is_drawn(
    directory: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    if directory == "proc":
        if not Path("/proc/self").is_dir():
            pytest.skip("no /proc, the directory nobody can write a file into")
        target = Path("/proc/out.webm")
    else:
        refusing_disk.refuse_partials(monkeypatch)
        target = tmp_path / "out.webm"
        target.write_bytes(b"the video that was there")
    drawn: list[int] = []
    animation = _animation(on_frame=lambda k, _fig: drawn.append(k))
    with pytest.raises(
        io.VideoEncoderError, match="could not write the video for"
    ) as caught:
        io.write_video(target, animation)
    assert str(target) in str(caught.value)
    # The caller's path, never the hidden file that was refused.
    assert ".partial" not in str(caught.value)
    # ffmpeg is found and asked what it can do, as before any write, but
    # nothing is encoded, not even a trial frame.
    assert fake.trials() == []
    assert fake.encodes() == []
    assert drawn == []
    if directory == "refusing":
        assert target.read_bytes() == b"the video that was there"
        assert refusing_disk.partial_sizes(tmp_path) == []


def test_an_argument_error_in_a_directory_that_does_not_take_the_video_is_itself(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The arguments are checked before the directory is, as the simulation
    # writers do, so a missing rate is a TypeError wherever the video goes.
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    refusing_disk.refuse_partials(monkeypatch)
    animation = _animation()
    monkeypatch.setattr(animation, "_interval", None)
    with pytest.raises(TypeError, match="fps"):
        io.write_video(tmp_path / "out.webm", animation)
    assert fake.calls() == []
    assert refusing_disk.partial_sizes(tmp_path) == []


def test_a_missing_ffmpeg_in_a_directory_that_does_not_take_the_video_is_itself(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(mpl.rcParams, "animation.ffmpeg_path", "no-such-ffmpeg-here")
    refusing_disk.refuse_partials(monkeypatch)
    animation = _animation()
    with pytest.raises(io.FFmpegNotFoundError, match="animation.ffmpeg_path"):
        io.write_video(tmp_path / "out.webm", animation)
    assert refusing_disk.partial_sizes(tmp_path) == []


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


#: Marks a caller's file name can hold that no message prints as they are:
#: one that reorders text, the escape that opens a terminal's commands, and
#: the lone surrogate Python holds for a byte that is not UTF-8 (a Windows
#: file name is UTF-16, so no name holds one there).
_UNPRINTABLE_MARKS = [
    "\u202e",
    "\x1b",
    pytest.param(
        "\udcff",
        marks=pytest.mark.skipif(
            sys.platform == "win32",
            reason="a Windows file name is UTF-16, so no name fails UTF-8",
        ),
    ),
]


@pytest.mark.parametrize("mark", _UNPRINTABLE_MARKS)
def test_a_video_left_at_its_partial_name_is_named_by_its_escapes(
    tmp_path: Path, mark: str
) -> None:
    """The partial file is named after the caller's file, so it is escaped as that name is."""
    from phonometry.io import _video as pipe_module

    path = tmp_path / f"w{mark}.webm"
    partial = tmp_path / f".w{mark}.webm.0123.partial"
    with pytest.raises(
        io.VideoEncoderError, match="could not take the place of"
    ) as caught:
        pipe_module.settle(partial, path)
    message = str(caught.value)
    message.encode("utf-8")
    assert mark not in message
    escape = ascii(mark)[1:-1]
    assert message.endswith(f"it is at {tmp_path}{os.sep}.w{escape}.webm.0123.partial")


def test_what_ffmpeg_wrote_is_quoted_with_its_unprintable_characters_escaped(
    tmp_path: Path,
) -> None:
    """ffmpeg names the file it writes as it was given, the caller's name in it."""
    from phonometry.io import _video as pipe_module
    from phonometry.io._video_encoders import FFmpeg

    request = pipe_module.video_request(tmp_path / "w.webm", io.VideoOptions())
    ffmpeg = FFmpeg(path="ffmpeg", version="", encoders=frozenset())
    pipe = pipe_module._FramePipe(
        request, ffmpeg, "20/1", output=tmp_path / "p.webm", choice=None
    )
    pipe._tail.extend(
        [
            "Error opening output .w\u202e\x1b[2J.webm.partial: Permission denied",
            "\x9b31m\tthe end",
        ]
    )
    message = str(pipe._failure("ffmpeg exited with status 1"))
    for mark in ("\u202e", "\x1b", "\x9b"):
        assert mark not in message
    assert message.endswith(
        "ffmpeg said:\nError opening output .w\\u202e\\x1b[2J.webm.partial: "
        "Permission denied\n\\x9b31m\tthe end"
    )


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
    monkeypatch.setattr(
        pipe_module,
        "threading",
        SimpleNamespace(Thread=Unstartable, Lock=threading.Lock),
    )
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


def test_an_interrupt_before_the_reader_starts_stops_ffmpeg(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, recwarn: pytest.WarningsRecorder
) -> None:
    """An interrupt between ffmpeg's start and its reader's reaches the caller, and stops ffmpeg."""
    from phonometry.io import _video as pipe_module

    class Interrupted(threading.Thread):
        def start(self) -> None:
            raise KeyboardInterrupt

    fake_ffmpeg.install(tmp_path, monkeypatch)
    monkeypatch.setattr(
        pipe_module,
        "threading",
        SimpleNamespace(Thread=Interrupted, Lock=threading.Lock),
    )
    animation = _animation()
    gc.collect()
    recwarn.clear()
    with pytest.raises(KeyboardInterrupt):
        io.write_video(tmp_path / "w.webm", animation)
    assert pipe_module._RUNNING == set()
    assert _unclosed(recwarn) == []
    if sys.platform != "win32":
        assert [p.name for p in tmp_path.iterdir() if p.name.endswith(".partial")] == []


@pytest.mark.parametrize("reader", ["running", "not yet scheduled"])
def test_an_interrupt_as_the_reader_starts_never_closes_its_pipe_under_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, reader: str
) -> None:
    """An interrupt inside the reader's start() leaves its thread nothing to raise.

    The interrupt can come when the reader of stderr already runs, which is
    then waited for, or before the reader is scheduled, which then finds its
    pipe closed and stops.
    """
    from phonometry.io import _video as pipe_module

    entered, go = threading.Event(), threading.Event()
    readers: list[threading.Thread] = []
    read_stderr = pipe_module._FramePipe._read_stderr

    def held(pipe: pipe_module._FramePipe) -> None:
        entered.set()
        # Long enough for a pipe closed under the reader to be closed first.
        go.wait(timeout=1.0)
        read_stderr(pipe)

    class Interrupted(threading.Thread):
        def start(self) -> None:
            readers.append(self)
            if reader == "running":
                super().start()
                assert entered.wait(timeout=10.0)
            raise KeyboardInterrupt

    raised: list[object] = []
    monkeypatch.setattr(threading, "excepthook", raised.append)
    monkeypatch.setattr(pipe_module._FramePipe, "_read_stderr", held)
    fake_ffmpeg.install(tmp_path, monkeypatch)
    monkeypatch.setattr(
        pipe_module,
        "threading",
        SimpleNamespace(Thread=Interrupted, Lock=threading.Lock),
    )
    animation = _animation()
    with pytest.raises(KeyboardInterrupt):
        io.write_video(tmp_path / "w.webm", animation)
    (thread,) = readers
    if reader == "not yet scheduled":
        # Scheduled only after the interrupt.
        threading.Thread.start(thread)
    go.set()
    thread.join(timeout=10.0)
    assert not thread.is_alive()
    assert raised == []


def test_the_last_words_are_copied_whole_while_the_reader_still_reads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A reader of stderr that outlives its wait never breaks the error that quotes it.

    On Windows a program behind cmd.exe can hold ffmpeg's stderr open after
    ffmpeg is stopped, so the reader may still be appending a line while
    the error copies the last ones.
    """
    from phonometry.io import _video as pipe_module
    from phonometry.io._video_encoders import FFmpeg

    first_in, released, late_in = (
        threading.Event(),
        threading.Event(),
        threading.Event(),
    )

    class Stream:
        closed = False

        def __enter__(self) -> Stream:
            return self

        def __exit__(self, *_exc: object) -> None:
            return None

        def __iter__(self) -> Iterator[bytes]:
            yield b"first line\n"
            released.wait(timeout=10.0)
            yield b"late line\n"

    class Tail(deque[str]):
        def append(self, line: str) -> None:
            super().append(line)
            (first_in if line == "first line" else late_in).set()

        def __iter__(self) -> Iterator[str]:
            for line in super().__iter__():
                yield line
                # Halfway through the copy, the reader gets its next line.
                released.set()
                late_in.wait(timeout=0.5)

    class Exited:
        stdin = None
        stderr = Stream()

        def poll(self) -> int:
            return 0

        def wait(self, timeout: float | None = None) -> int:
            return 0

    request = pipe_module.video_request(tmp_path / "w.webm", io.VideoOptions())
    ffmpeg = FFmpeg(path="ffmpeg", version="", encoders=frozenset())
    pipe = pipe_module._FramePipe(
        request, ffmpeg, "20/1", output=tmp_path / "p.webm", choice=None
    )
    pipe._process = Exited()  # type: ignore[assignment]
    pipe._tail = Tail(maxlen=20)
    reader = threading.Thread(target=pipe._read_stderr, daemon=True)
    reader.start()
    assert first_in.wait(timeout=10.0)
    pipe._drain = reader
    monkeypatch.setattr(pipe_module, "_EXIT_TIMEOUT_S", 0.05)
    error = pipe._failure("ffmpeg exited with status 1")
    assert str(error).endswith("ffmpeg said:\nfirst line")
    reader.join(timeout=10.0)
    assert not reader.is_alive()


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
        # float(True) is 1.0: read as a number, it would be a frame a second.
        ({"fps": True}, TypeError, "^'fps' must be one number, not a bool; got True"),
        (
            {"fps": np.True_},
            TypeError,
            "^'fps' must be one number, not a bool; got np.True_",
        ),
        # No argument of a program can carry a NUL: Popen would refuse it,
        # for a simulation writer after the whole run.
        (
            {"ffmpeg_encoder": "libx264\x00"},
            ValueError,
            "^'ffmpeg_encoder' cannot hold a NUL character",
        ),
        (
            {"ffmpeg_options": ("-crf", "3\x000")},
            ValueError,
            "^'ffmpeg_options' cannot hold a NUL character",
        ),
        ({"vaapi_device": 128}, TypeError, "^'vaapi_device' must be a str"),
        (
            {"vaapi_device": ""},
            ValueError,
            "^'vaapi_device' must name the GPU device VAAPI encodes on",
        ),
        (
            {"vaapi_device": "/dev/dri/render\x00D128"},
            ValueError,
            "^'vaapi_device' cannot hold a NUL character",
        ),
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
    assert io.VideoOptions() == io.VideoOptions(
        encoder="auto", quality="standard", vaapi_device="/dev/dri/renderD128"
    )
    assert io.VideoOptions(vaapi_device="/dev/dri/renderD129").vaapi_device == (
        "/dev/dri/renderD129"
    )
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
    with pytest.raises(TypeError, match="'animation' must be a matplotlib"):
        io.write_video(tmp_path / "w.webm", "frames")  # type: ignore[arg-type]
    assert fake.calls() == []


def test_a_missing_ffmpeg_is_its_own_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(mpl.rcParams, "animation.ffmpeg_path", "no-such-ffmpeg-here")
    animation = _animation()
    with pytest.raises(io.FFmpegNotFoundError, match="animation.ffmpeg_path"):
        io.write_video(tmp_path / "w.webm", animation)


def test_vaapi_is_tried_and_used_on_the_device_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(
        tmp_path,
        monkeypatch,
        encoders=["av1_vaapi", "libsvtav1"],
        working=["av1_vaapi", "libsvtav1"],
    )
    video = io.VideoOptions(encoder="vaapi", vaapi_device="/dev/dri/renderD129")
    io.write_video(tmp_path / "w.webm", _animation(), video=video)
    (trial,) = fake.trials()
    (encode,) = fake.encodes()
    for argv in (trial["argv"], encode["argv"]):
        start = argv.index("-vaapi_device")
        assert argv[start : start + 2] == ["-vaapi_device", "/dev/dri/renderD129"]
        assert start < argv.index("-i")
    assert _after(encode["argv"], "-c:v") == "av1_vaapi"


def test_the_choice_is_logged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    fake_ffmpeg.install(tmp_path, monkeypatch)
    with caplog.at_level(logging.INFO, logger="phonometry.io"):
        io.write_video(tmp_path / "w.webm", _animation())
    assert any("libsvtav1" in r.getMessage() for r in caplog.records)
