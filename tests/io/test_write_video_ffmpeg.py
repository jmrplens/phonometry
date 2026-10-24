#  Copyright (c) 2026. Jose Manuel Requena Plens
"""``io.write_video`` with a real ffmpeg: the files decode, at the size and length drawn.

These run wherever ffmpeg and ffprobe are on PATH: the developer's machine
and the CI job that installs them. Elsewhere they skip and say why.
"""

from __future__ import annotations

import shutil
import subprocess
from typing import TYPE_CHECKING

import pytest

pytest.importorskip("matplotlib")
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from phonometry import io

if TYPE_CHECKING:
    from pathlib import Path

    from matplotlib.lines import Line2D

pytestmark = pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="needs ffmpeg and ffprobe on PATH; the CI video job installs them",
)


def _svt_av1() -> bool:
    if shutil.which("ffmpeg") is None:
        return False
    listing = subprocess.run(
        ["ffmpeg", "-hide_banner", "-encoders"],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    ).stdout
    return " libsvtav1 " in listing


def _animation(
    width: int, height: int, frames: int = 6, drawn: list[int] | None = None
) -> FuncAnimation:
    """A line animation exactly *width* by *height* pixels; each frame it draws goes into *drawn*."""
    fig = Figure(figsize=((width + 0.5) / 100, (height + 0.5) / 100), dpi=100)
    FigureCanvasAgg(fig)
    ax = fig.add_subplot()
    (line,) = ax.plot([0.0, 1.0], [0.0, 1.0])

    def update(k: int) -> tuple[Line2D]:
        if drawn is not None:
            drawn.append(k)
        line.set_ydata([0.0, float(k)])
        return (line,)

    return FuncAnimation(
        fig, update, frames=frames, interval=50, cache_frame_data=False
    )


def _probe(path: Path) -> dict[str, str]:
    shown = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-count_frames",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name,width,height,nb_read_frames",
            "-of",
            "default=noprint_wrappers=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    ).stdout
    return dict(line.split("=", 1) for line in shown.splitlines())


@pytest.mark.parametrize(
    ("name", "video", "codecs"),
    [
        ("w.webm", io.VideoOptions(encoder="cpu"), {"av1", "vp9"}),
        ("w.mp4", io.VideoOptions(encoder="cpu", codec="h264"), {"h264"}),
        ("w.gif", io.VideoOptions(), {"gif"}),
    ],
)
def test_the_file_decodes_at_the_size_and_length_drawn(
    tmp_path: Path, name: str, video: io.VideoOptions, codecs: set[str]
) -> None:
    target = tmp_path / name
    io.write_video(target, _animation(200, 150), video=video)
    probe = _probe(target)
    assert probe["codec_name"] in codecs
    assert (probe["width"], probe["height"]) == ("200", "150")
    assert probe["nb_read_frames"] == "6"


def test_an_odd_figure_comes_out_even(tmp_path: Path) -> None:
    target = tmp_path / "w.webm"
    io.write_video(target, _animation(201, 151), video=io.VideoOptions(encoder="cpu"))
    probe = _probe(target)
    assert (probe["width"], probe["height"]) == ("202", "152")


@pytest.mark.skipif(
    not _svt_av1(),
    reason="this ffmpeg has no SVT-AV1: the AV1-first CPU path is untested here",
)
def test_the_cpu_writes_av1_first(tmp_path: Path) -> None:
    target = tmp_path / "w.webm"
    io.write_video(target, _animation(200, 150), video=io.VideoOptions(encoder="cpu"))
    assert _probe(target)["codec_name"] == "av1"


def _compiled_in(encoder: str) -> bool:
    listing = subprocess.run(
        ["ffmpeg", "-hide_banner", "-encoders"],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    ).stdout
    return f" {encoder} " in listing


@pytest.mark.parametrize(
    ("name", "video", "said"),
    [
        (
            "w.webm",
            io.VideoOptions(ffmpeg_encoder="phonometry-no-such-encoder"),
            r"Unknown encoder 'phonometry-no-such-encoder'",
        ),
        (
            "w.webm",
            io.VideoOptions(ffmpeg_encoder="libvpx-vp9", ffmpeg_options=("-crf", "99")),
            r"'crf' out of range",
        ),
        (
            "w.mp4",
            io.VideoOptions(
                ffmpeg_encoder="libx264", ffmpeg_options=("-preset", "phonometry")
            ),
            r"invalid preset 'phonometry'",
        ),
    ],
    ids=["unknown-encoder", "refused-when-ffmpeg-starts", "refused-at-the-first-frame"],
)
def test_an_encoder_or_option_of_the_caller_s_that_ffmpeg_refuses_fails_at_once(
    tmp_path: Path, name: str, video: io.VideoOptions, said: str
) -> None:
    """Used as it is, with no trial: ffmpeg's own refusal, within the first frames, and nothing left."""
    encoder = video.ffmpeg_encoder
    assert encoder is not None
    if encoder.startswith("lib") and not _compiled_in(encoder):
        pytest.skip(f"this ffmpeg has no {encoder}")
    target = tmp_path / name
    target.write_bytes(b"the video that was there")
    n_frames = 60
    drawn: list[int] = []
    animation = _animation(200, 150, frames=n_frames, drawn=drawn)
    with pytest.raises(io.VideoEncoderError, match=said) as caught:
        io.write_video(target, animation, video=video)
    message = str(caught.value)
    assert f"while writing {target} with the encoder {encoder}" in message
    # ffmpeg reads ahead a few frames before it gives up, never the run.
    assert 0 < len(drawn) < n_frames // 2
    assert target.read_bytes() == b"the video that was there"
    assert [p.name for p in tmp_path.iterdir() if p.name.endswith(".partial")] == []
