#  Copyright (c) 2026. Jose Manuel Requena Plens
"""What a node does with a video job, and the ceiling the client holds its bytes to."""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest

pytest.importorskip("matplotlib")
import fake_ffmpeg
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from phonometry import io
from phonometry.io import VideoOptions
from phonometry.io._video_encoders import FFMPEG_NAMES
from phonometry.simulation import (
    FDTD2D,
    AnimationFrame,
    Compute,
    ElasticRecording,
    ElasticRun,
    ExplosionSource,
    FDTDRecording,
    FDTDRun,
    GaussianPulse,
    _observer,
    elastic_fdtd_simulation,
    fdtd_simulation,
)
from phonometry.simulation import _video_job as job
from phonometry.simulation import fdtd as fd

if TYPE_CHECKING:
    from collections.abc import Callable

    from matplotlib.image import FigureImage

    from phonometry.io._video_encoders import Container

#: The ``src`` this test module belongs to, so a subprocess imports the code
#: under test and not whatever an editable install points at.
_SRC = Path(__file__).resolve().parents[2] / "src"

_RUN = FDTDRun(
    343.0,
    0.01,
    1e-3,
    shape=(30, 40),
    sources=[GaussianPulse(ix=20, iy=15, half_width_s=4e-5)],
    recording=FDTDRecording(probes=[(5, 5)], snapshot_every=10),
)
_FRAME = AnimationFrame(size=(480, 240), color_limit=1.0)


def _on_node(container: object = "webm", **changes: Any) -> tuple[Any, tuple[str, Any]]:
    arguments: dict[str, Any] = {
        "run": _RUN,
        "frame": _FRAME,
        "video": VideoOptions(),
        "compute": Compute(),
    }
    arguments.update(changes)
    return job.write_fdtd_animation_on_node(container=container, **arguments)  # type: ignore[arg-type]


def test_the_node_returns_the_record_and_the_video(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_ffmpeg.install(tmp_path, monkeypatch)
    result, (name, stream) = _on_node()
    here = fdtd_simulation(_RUN)
    assert np.array_equal(result.pressures, here.pressures)
    assert result.snapshots is None
    assert result.provenance == here.provenance
    assert name == "video"
    scratch = Path(stream.name).parent
    assert stream.seekable()
    assert stream.read(4) == b"\x1a\x45\xdf\xa3"
    stream.close()
    assert not scratch.exists()


def test_the_elastic_node_returns_the_signals(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_ffmpeg.install(tmp_path, monkeypatch)
    run = ElasticRun(
        4000.0,
        2300.0,
        0.01,
        5e-4,
        rho=2500.0,
        shape=(20, 24),
        sources=[
            ExplosionSource(
                ix=12,
                iy=10,
                waveform=GaussianPulse(ix=0, iy=0, half_width_s=2e-5).value,
            )
        ],
        recording=ElasticRecording(probes=[(4, 4)], snapshot_every=60),
    )
    result, (_, stream) = job.write_elastic_fdtd_animation_on_node(
        run=run,
        frame=AnimationFrame(size=(480, 240), color_limit=1e-6),
        video=VideoOptions(),
        container="gif",
        compute=Compute(),
    )
    with stream:
        assert stream.read(6) == b"GIF89a"
    assert np.array_equal(result.signals, elastic_fdtd_simulation(run).signals)


def test_a_node_without_the_font_refuses_before_it_steps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    monkeypatch.setattr(job, "_FONT", "No Such Font Family")
    with pytest.raises(job.NodeCannotAnimateError, match="No Such Font Family"):
        _on_node()
    assert fake.calls() == []


def test_a_node_whose_encoders_all_fail_refuses_before_it_steps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    built: list[FDTD2D] = []

    def counted(*args: Any, **kwargs: Any) -> FDTD2D:
        built.append(FDTD2D(*args, **kwargs))
        return built[-1]

    monkeypatch.setattr(fd, "FDTD2D", counted)
    fake = fake_ffmpeg.install(tmp_path, monkeypatch, working=[])
    with pytest.raises(io.VideoEncoderError, match="webm"):
        _on_node()
    assert built == []
    assert fake.encodes() == []


@pytest.mark.parametrize("container", ["avi", "../video.webm", 3])
def test_a_container_outside_the_three_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, container: object
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    with pytest.raises((ValueError, TypeError), match="container"):
        _on_node(container)
    assert fake.calls() == []


def test_a_video_job_reports_each_step_and_stops_when_told(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    seen: list[tuple[int, int]] = []

    def watcher(done: int, total: int) -> None:
        seen.append((done, total))
        if done == 3:
            raise _observer.RunCancelled

    with _observer.observing(watcher), pytest.raises(_observer.RunCancelled):
        _on_node()
    total = seen[0][1]
    assert seen == [(1, total), (2, total), (3, total)]
    assert total == fdtd_simulation(_RUN).times.size - 1
    # The encode was stopped, not finished: nothing of it is left behind. (On
    # Windows the fake runs behind cmd.exe, which a kill does not reach.)
    assert fake.encodes() == [] or sys.platform == "win32"


def _cancel_at_the_third_step(done: int, _total: int) -> None:
    if done == 3:
        raise _observer.RunCancelled


@pytest.mark.parametrize(
    ("spec", "watcher", "error", "words"),
    [
        ({}, _cancel_at_the_third_step, _observer.RunCancelled, None),
        ({"working": []}, None, io.VideoEncoderError, "webm"),
        ({"die_after_frames": 2}, None, io.VideoEncoderError, "ffmpeg"),
    ],
    ids=["client-gone", "no-encoder", "ffmpeg-dies"],
)
def test_the_scratch_directory_goes_however_the_job_stops(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    spec: dict[str, object],
    watcher: Callable[[int, int], None] | None,
    error: type[BaseException],
    words: str | None,
) -> None:
    fake_ffmpeg.install(tmp_path, monkeypatch, **spec)
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(scratch))
    watching = (
        contextlib.nullcontext() if watcher is None else _observer.observing(watcher)
    )
    with watching, pytest.raises(error, match=words):
        _on_node()
    assert list(scratch.iterdir()) == []


#: A node's Python without matplotlib: it simulates, and refuses a video
#: before it steps.
_WITHOUT_MATPLOTLIB = """
import sys
sys.modules["matplotlib"] = None
from phonometry.io import VideoOptions
from phonometry.simulation import AnimationFrame, Compute, FDTDRecording, FDTDRun, GaussianPulse
from phonometry.simulation._remote import node
from phonometry.simulation._video_job import NodeCannotAnimateError
run = FDTDRun(
    343.0, 0.01, 1e-4, shape=(10, 12),
    sources=[GaussianPulse(ix=5, iy=5, half_width_s=4e-5)],
    recording=FDTDRecording(probes=[(2, 2)], snapshot_every=2),
)
simulate, _ = node.FUNCTIONS["fdtd_simulation"]
result, stream = simulate(run=run, compute=Compute())
print(stream is None, result.pressures.shape[1] == result.times.size)
animate, _ = node.FUNCTIONS["write_fdtd_animation"]
try:
    animate(run=run, frame=AnimationFrame(), video=VideoOptions(), container="webm", compute=Compute())
except NodeCannotAnimateError as exc:
    print(exc)
"""


def test_a_node_without_matplotlib_simulates_and_refuses_to_animate() -> None:
    done = subprocess.run(
        [sys.executable, "-c", _WITHOUT_MATPLOTLIB],
        env={**os.environ, "PYTHONPATH": str(_SRC)},
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert done.returncode == 0, done.stderr
    simulated, refusal = done.stdout.splitlines()
    assert simulated == "True True"
    assert refusal.startswith("this node has no matplotlib")


@pytest.mark.parametrize(
    "record",
    [
        AnimationFrame(language="es", size=(480, 240), color_limit=0.5),
        VideoOptions(
            encoder="cpu",
            codec="vp9",
            quality="small",
            fps=24.0,
            ffmpeg_options=("-row-mt", "1"),
        ),
        VideoOptions(ffmpeg_encoder="libvpx-vp9", ffmpeg_options=("-crf", "40")),
    ],
)
def test_the_video_records_travel_field_by_field(record: object) -> None:
    from phonometry.simulation._remote import wire

    tree, buffers = wire.encode_arguments({"record": record})
    back = wire.decode_arguments(
        json.loads(json.dumps(tree)), [bytes(b) for b in buffers]
    )["record"]
    assert type(back) is type(record)
    assert back == record


@pytest.mark.parametrize(
    ("video", "bytes_per_pixel"),
    [
        (VideoOptions(), 2),
        (VideoOptions(encoder="cpu", codec="h264", quality="high"), 2),
        (VideoOptions(ffmpeg_options=("-crf", "0")), 8),
        (VideoOptions(ffmpeg_encoder="libx264rgb"), 8),
    ],
    ids=["auto", "chosen", "options", "raw-encoder"],
)
def test_the_callers_options_widen_the_ceiling(
    video: VideoOptions, bytes_per_pixel: int
) -> None:
    """Two bytes a pixel when the library's presets alone decide the encode, eight when the caller's options do."""
    cap = job.video_byte_cap(10, 255, 191, video=video)
    assert cap == 10 * 256 * 192 * bytes_per_pixel + job._CONTAINER_SLACK


#: Options of the caller's that override the library's preset and pixel
#: format (they come after both): lossless 4:4:4 at 8 bits, the least an
#: 8-bit encode can compress.
_LOSSLESS_444 = ("-pix_fmt", "yuv444p", "-crf", "0")

#: The same frames encoded losslessly at 10 and 12 bits, which an 8-bit frame
#: gains nothing from and pays for in bytes, the most in planar RGB at 12
#: bits. A lossless VP9 also needs its CRF at 0, in place of the library's.
_HEVC_LOSSLESS_10 = ("-pix_fmt", "yuv444p10le", "-x265-params", "lossless=1")
_HEVC_LOSSLESS_12 = ("-pix_fmt", "yuv444p12le", "-x265-params", "lossless=1")
_HEVC_LOSSLESS_12_RGB = ("-pix_fmt", "gbrp12le", "-x265-params", "lossless=1")
_VP9_LOSSLESS_12 = ("-pix_fmt", "yuv444p12le", "-crf", "0", "-lossless", "1")


def _skip_unless_this_ffmpeg_takes(video: VideoOptions) -> None:
    """Skip a case whose options ask for a pixel format its encoder does not take in this ffmpeg.

    An ffmpeg without the encoder lists no format for it, so that case skips
    too.
    """
    options = video.ffmpeg_options
    if video.codec is None or "-pix_fmt" not in options:
        return
    encoder = FFMPEG_NAMES["cpu", video.codec]
    pixel_format = options[options.index("-pix_fmt") + 1]
    ffmpeg = shutil.which("ffmpeg")
    assert ffmpeg is not None
    described = subprocess.run(
        [ffmpeg, "-hide_banner", "-h", f"encoder={encoder}"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    if pixel_format not in described.split():
        pytest.skip(f"this ffmpeg has no {encoder} that takes {pixel_format}")


@pytest.mark.skipif(
    shutil.which("ffmpeg") is None,
    reason="needs ffmpeg on PATH; the CI video job installs it",
)
@pytest.mark.parametrize(
    ("suffix", "video", "bytes_per_pixel", "above"),
    [
        ("webm", VideoOptions(encoder="cpu", quality="high"), 2, 0),
        ("webm", VideoOptions(encoder="cpu", codec="vp9", quality="high"), 2, 0),
        ("mp4", VideoOptions(encoder="cpu", codec="hevc", quality="high"), 2, 0),
        ("mp4", VideoOptions(encoder="cpu", codec="h264", quality="high"), 2, 0),
        ("gif", VideoOptions(quality="high"), 2, 0),
        (
            "mp4",
            VideoOptions(encoder="cpu", codec="h264", ffmpeg_options=_LOSSLESS_444),
            8,
            2,
        ),
        (
            "webm",
            VideoOptions(encoder="cpu", codec="vp9", ffmpeg_options=_LOSSLESS_444),
            8,
            2,
        ),
        (
            "mp4",
            VideoOptions(encoder="cpu", codec="hevc", ffmpeg_options=_HEVC_LOSSLESS_10),
            8,
            4,
        ),
        (
            "mp4",
            VideoOptions(encoder="cpu", codec="hevc", ffmpeg_options=_HEVC_LOSSLESS_12),
            8,
            4,
        ),
        (
            "mp4",
            VideoOptions(
                encoder="cpu", codec="hevc", ffmpeg_options=_HEVC_LOSSLESS_12_RGB
            ),
            8,
            4,
        ),
        (
            "webm",
            VideoOptions(encoder="cpu", codec="vp9", ffmpeg_options=_VP9_LOSSLESS_12),
            8,
            4,
        ),
    ],
    ids=[
        "webm",
        "vp9",
        "hevc",
        "h264",
        "gif",
        "h264-lossless-8-bit",
        "vp9-lossless-8-bit",
        "hevc-lossless-10-bit",
        "hevc-lossless-12-bit",
        "hevc-lossless-12-bit-rgb",
        "vp9-lossless-12-bit",
    ],
)
def test_noise_at_the_highest_quality_stays_under_the_ceiling(
    tmp_path: Path,
    suffix: Container,
    video: VideoOptions,
    bytes_per_pixel: int,
    above: int,
) -> None:
    """The hardest frames there are, at the quality that compresses least: the ceiling's premise, measured.

    Two bytes a pixel when the library's presets alone decide the encode,
    eight when the caller's options do. ``above`` is what the encode is
    known to take more than: the lossless encodes of noise here take more
    than two bytes a pixel at 8 bits and more than four at 10 or 12, which
    is why the caller's part is eight.
    """
    _skip_unless_this_ffmpeg_takes(video)
    width, height, n_frames = 255, 191, 20  # odd sides: the padding counts too
    rng = np.random.default_rng(0)
    fig = Figure(figsize=((width + 0.5) / 100, (height + 0.5) / 100), dpi=100)
    FigureCanvasAgg(fig)
    image = fig.figimage(rng.integers(0, 256, (height, width, 3), dtype=np.uint8))

    def update(k: int) -> tuple[FigureImage]:
        image.set_data(rng.integers(0, 256, (height, width, 3), dtype=np.uint8))
        return (image,)

    animation = FuncAnimation(
        fig, update, frames=n_frames, interval=50, cache_frame_data=False
    )
    target = tmp_path / f"noise.{suffix}"
    io.write_video(target, animation, video=video)
    per_pixel_part = (
        job.video_byte_cap(n_frames, width, height, video=video) - job._CONTAINER_SLACK
    )
    assert per_pixel_part == n_frames * 256 * 192 * bytes_per_pixel
    assert n_frames * 256 * 192 * above < target.stat().st_size <= per_pixel_part
    # And a real encode begins as the client will hold the node's bytes to.
    first = target.read_bytes()[:16]
    heads = job.CONTAINER_HEADS[suffix]
    assert any(first[at : at + len(head)] == head for at, head in heads)
