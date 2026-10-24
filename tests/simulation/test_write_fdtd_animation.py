#  Copyright (c) 2026. Jose Manuel Requena Plens
"""An acoustic FDTD run written straight to a video, checked before it steps."""

from __future__ import annotations

import contextlib
import dataclasses
import errno
import pathlib
import re
import shutil
import subprocess
import sys
import warnings
from typing import TYPE_CHECKING, Any, NoReturn

import numpy as np
import pytest

pytest.importorskip("matplotlib")
import fake_ffmpeg
import matplotlib as mpl
import refusing_disk

from phonometry import io
from phonometry.io import VideoOptions
from phonometry.io._video import video_request
from phonometry.simulation import (
    FDTD2D,
    AnimationFrame,
    Compute,
    ComputeDeviceError,
    ComputeFallbackWarning,
    ElasticRun,
    ExplosionSource,
    FDTDBoundaries,
    FDTDRecording,
    FDTDRun,
    GaussianPulse,
    PlaneWaveSource,
    fdtd_simulation,
    use,
    write_fdtd_animation,
)
from phonometry.simulation import _backends as bk
from phonometry.simulation import fdtd as fd
from phonometry.simulation import video as video_module

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from matplotlib.image import AxesImage
    from numpy.typing import NDArray

_SOURCE = GaussianPulse(ix=20, iy=15, half_width_s=4e-5)
_PROBES = [(5, 5), (35, 25)]
_SMALL = AnimationFrame(size=(480, 246))
_SMALL_FIXED = AnimationFrame(size=(480, 246), color_limit=1.0)
# A run of 12 s on cells of 10 m: 970 steps, the last frame at 11.13 s.
_LONG = FDTDRun(
    c=343.0,
    dx=10.0,
    duration_s=12.0,
    shape=(30, 40),
    sources=[_SOURCE],
    recording=FDTDRecording(snapshot_every=900),
)


def _run(duration: float = 2e-3, **changes: Any) -> FDTDRun:
    arguments: dict[str, Any] = {
        "shape": (30, 40),
        "sources": [_SOURCE],
        "recording": FDTDRecording(probes=_PROBES, snapshot_every=10),
    }
    arguments.update(changes)
    return FDTDRun(c=343.0, dx=0.01, duration_s=duration, **arguments)


@pytest.fixture
def engines(monkeypatch: pytest.MonkeyPatch) -> list[FDTD2D]:
    """Every engine a writer builds, in order (they are built in fdtd._acoustic_engine)."""
    built: list[FDTD2D] = []

    def counted(*args: Any, **kwargs: Any) -> FDTD2D:
        sim = FDTD2D(*args, **kwargs)
        built.append(sim)
        return sim

    monkeypatch.setattr(fd, "FDTD2D", counted)
    return built


def test_one_frame_every_snapshot_every_steps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    target = tmp_path / "run.webm"
    res = write_fdtd_animation(target, _run(), frame=_SMALL_FIXED)
    steps = res.times.size - 1
    (encode,) = fake.encodes()
    assert encode["frames"] == steps // 10 + 1
    assert encode["argv"][encode["argv"].index("-s") + 1] == "480x246"
    assert encode["argv"][encode["argv"].index("-r") + 1] == "30/1"
    assert target.read_bytes().startswith(b"\x1a\x45\xdf\xa3")


def test_vaapi_is_tried_before_the_run_and_used_on_the_device_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(
        tmp_path, monkeypatch, encoders=["av1_vaapi"], working=["av1_vaapi"]
    )
    video = VideoOptions(encoder="vaapi", vaapi_device="/dev/dri/renderD129")
    write_fdtd_animation(
        tmp_path / "v.webm", _run(1e-3), frame=_SMALL_FIXED, video=video
    )
    (trial,) = fake.trials()
    (encode,) = fake.encodes()
    for argv in (trial["argv"], encode["argv"]):
        assert argv[argv.index("-vaapi_device") + 1] == "/dev/dri/renderD129"


def test_the_default_frame_is_960_by_540(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    write_fdtd_animation(
        tmp_path / "d.webm", _run(1e-3), frame=AnimationFrame(color_limit=1.0)
    )
    argv = fake.encodes()[0]["argv"]
    assert argv[argv.index("-s") + 1] == "960x540"
    assert AnimationFrame() == AnimationFrame(
        language="en", size=(960, 540), color_limit=None
    )


def test_the_result_is_the_simulation_s_without_snapshots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_ffmpeg.install(tmp_path, monkeypatch)
    run = _run()
    res = write_fdtd_animation(tmp_path / "run.webm", run, frame=_SMALL_FIXED)
    reference = fdtd_simulation(run)
    assert np.array_equal(res.pressures, reference.pressures)
    assert np.array_equal(res.times, reference.times)
    assert np.array_equal(res.probe_positions, reference.probe_positions)
    assert (res.dx, res.dt, res.shape) == (reference.dx, reference.dt, reference.shape)
    assert res.snapshots is None
    assert res.snapshot_times is None
    assert res.snapshot_decimation == 1
    assert res.provenance == reference.provenance


def test_the_snapshot_plot_of_the_writer_s_result_says_where_snapshots_come_from(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The run recorded snapshot_every, so "set it" would send the caller round in a circle."""
    fake_ffmpeg.install(tmp_path, monkeypatch)
    res = write_fdtd_animation(tmp_path / "s.webm", _run(1e-3), frame=_SMALL_FIXED)
    with pytest.raises(
        ValueError,
        match=r"^the result holds no snapshots; rerun fdtd_simulation with "
        r"run\.recording\.snapshot_every set \(a run that write_fdtd_animation "
        r"wrote to a video stores none\)$",
    ):
        res.plot(kind="snapshot")


@pytest.mark.parametrize("frame", [_SMALL, _SMALL_FIXED], ids=["found", "given"])
@pytest.mark.parametrize("decimation", [1, 3])
def test_the_probes_are_the_simulation_s_on_either_route_and_any_decimation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    frame: AnimationFrame,
    decimation: int,
) -> None:
    """Bit for bit, whether the colour limit is found in a first pass or given, whatever a frame keeps."""
    fake_ffmpeg.install(tmp_path, monkeypatch)
    recording = FDTDRecording(
        probes=_PROBES, snapshot_every=10, snapshot_decimation=decimation
    )
    run = _run(recording=recording)
    res = write_fdtd_animation(tmp_path / "p.webm", run, frame=frame)
    reference = fdtd_simulation(run)
    assert np.array_equal(res.pressures, reference.pressures)
    assert res.snapshot_decimation == decimation
    assert res.provenance == reference.provenance


def test_the_layout_is_made_for_the_time_of_the_last_frame(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The first frame is laid out for the title of the last, one drawn every snapshot_every steps."""
    from phonometry._plot import simulation as plot

    fake_ffmpeg.install(tmp_path, monkeypatch)
    seen: list[float] = []
    original = plot.fdtd_frame

    def recorded(*args: Any, **kwargs: Any) -> AxesImage:
        seen.append(kwargs["last_time_s"])
        return original(*args, **kwargs)

    monkeypatch.setattr(plot, "fdtd_frame", recorded)
    run = _run()
    write_fdtd_animation(tmp_path / "t.webm", run, frame=_SMALL_FIXED)
    checks = run._checked
    # 162 steps, a frame every 10: the last frame at step 160, not 162.
    assert checks.steps % 10 != 0
    assert seen == [(checks.steps // 10) * 10 * checks.dt]


@pytest.mark.parametrize(("frame", "builds"), [(_SMALL_FIXED, 1), (_SMALL, 2)])
def test_a_given_limit_steps_once_and_a_found_one_twice(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    engines: list[FDTD2D],
    frame: AnimationFrame,
    builds: int,
) -> None:
    fake_ffmpeg.install(tmp_path, monkeypatch)
    write_fdtd_animation(tmp_path / "r.webm", _run(), frame=frame)
    assert len(engines) == builds


def test_the_found_limit_leaves_out_the_driven_cells() -> None:
    pulse = GaussianPulse(ix=0, iy=0, half_width_s=5e-5)
    run = FDTDRun(
        c=343.0,
        dx=0.01,
        duration_s=2e-3,
        shape=(40, 50),
        sources=[
            _SOURCE,
            PlaneWaveSource(direction="down", waveform=pulse.value, offset=9),
        ],
        recording=FDTDRecording(snapshot_every=5),
        boundaries=FDTDBoundaries(sides={"top": "absorbing"}, absorbing_layer_cells=8),
    )
    keep = video_module._acoustic_keep(run)
    assert keep[15, 20] == 0.0  # the point source
    assert not keep[9].any()  # the injection line
    assert not keep[:8].any()  # the absorbing layer on top
    assert keep[30, 45] == 1.0
    limit, ran = video_module._acoustic_limit(run, None, keep)
    res = fdtd_simulation(run)
    assert res.snapshots is not None
    assert limit == float(np.max(np.abs(res.snapshots) * keep))
    # The driven cells did carry a field; the limit just did not read it.
    assert float(np.max(np.abs(res.snapshots) * (1.0 - keep))) > 0.0
    assert ran == Compute()


def test_the_peak_reads_only_the_cells_kept() -> None:
    """A cell left out is never read, however strong: the mask is applied to every frame."""
    keep = np.ones((4, 5), dtype=np.bool_)
    keep[1, 2] = False

    def frames() -> Generator[np.ndarray, None, None]:
        for strongest in (3.0, -7.0):
            field = np.full((4, 5), 0.5)
            field[1, 2] = 100.0
            field[3, 4] = strongest
            yield field

    assert video_module._peak(frames(), bk.backend_for(Compute()), keep) == 7.0


def test_on_the_strict_backend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, on_strict: None
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    res = write_fdtd_animation(tmp_path / "s.webm", _run(1e-3), frame=_SMALL)
    assert fake.encodes()[0]["frames"] == (res.times.size - 1) // 10 + 1


@pytest.mark.parametrize("asked", ["argument", "use", "environment"])
def test_a_fallback_warns_once_and_says_where_it_ran(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, asked: str
) -> None:
    def absent(_c: Compute) -> bk.Backend:
        msg = "no CUDA device"
        raise ComputeDeviceError(msg)

    monkeypatch.setitem(bk.LOADERS, "cupy", absent)
    monkeypatch.delenv("PHONOMETRY_COMPUTE", raising=False)
    fake_ffmpeg.install(tmp_path, monkeypatch)
    placement = Compute(device="cupy", fallback=True)
    with (
        contextlib.ExitStack() as stack,
        warnings.catch_warnings(record=True) as caught,
    ):
        warnings.simplefilter("always")
        if asked == "use":
            stack.enter_context(use(placement))
        if asked == "environment":
            monkeypatch.setenv("PHONOMETRY_COMPUTE", "cupy,fallback")
        # No colour limit: the run steps twice, and must warn once.
        res = write_fdtd_animation(
            tmp_path / "f.webm",
            _run(1e-3),
            compute=placement if asked == "argument" else None,
            frame=_SMALL,
        )
    fallbacks = [w for w in caught if issubclass(w.category, ComputeFallbackWarning)]
    assert len(fallbacks) == 1
    assert res.provenance.device == "cpu"


def test_a_covered_grid_has_nothing_to_scale_by(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, engines: list[FDTD2D]
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    covered = _run(
        1e-3,
        shape=(12, 12),
        sources=[GaussianPulse(ix=6, iy=6, half_width_s=4e-5)],
        recording=FDTDRecording(snapshot_every=10),
        boundaries=FDTDBoundaries(sides="absorbing", absorbing_layer_cells=6),
    )
    with pytest.raises(
        ValueError,
        match=r"^the sources, the injection lines and the absorbing layer cover "
        r"every cell a frame keeps.*AnimationFrame\(color_limit=\.\.\.\)$",
    ):
        write_fdtd_animation(tmp_path / "c.webm", covered, frame=_SMALL)
    assert engines == []
    assert fake.calls() == []


def test_a_field_that_never_leaves_the_source_has_nothing_to_scale_by(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    one_step = FDTD2D(343.0, 0.01, shape=(30, 40)).dt
    run = _run(one_step, recording=FDTDRecording(probes=_PROBES, snapshot_every=1))
    with pytest.raises(
        ValueError,
        match=r"^the field stays zero outside the sources, the injection lines and "
        r"the absorbing layer for the whole run.*AnimationFrame\(color_limit=\.\.\.\)$",
    ):
        write_fdtd_animation(tmp_path / "z.webm", run, frame=_SMALL)
    assert fake.encodes() == []


def test_a_field_that_is_not_finite_has_no_colour_scale() -> None:
    run = _run(1e-3)
    sim = fd._acoustic_engine(run, None)
    keep = np.ones(run._checked.grid, dtype=np.bool_)

    def frames() -> Generator[NDArray[np.float64], None, None]:
        yield np.zeros(run._checked.grid)
        yield np.full(run._checked.grid, np.nan)

    march = frames()
    covering = video_module._ACOUSTIC_COVERING
    with pytest.raises(
        ValueError,
        match=r"^the field is not finite in some frame.*AnimationFrame\(color_limit=\.\.\.\)$",
    ):
        video_module._found_limit(sim, march, keep, covering)


def test_a_directory_that_cannot_take_the_video_is_refused_before_a_step(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, engines: list[FDTD2D]
) -> None:
    # ffmpeg would find it only at the first frame, after a first pass had
    # stepped the whole run to find the colour limit.
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    real_open = pathlib.Path.open

    def refused(self: pathlib.Path, *args: Any, **kwargs: Any) -> object:
        if self.name.endswith(".partial"):
            raise PermissionError(errno.EACCES, "Permission denied", str(self))
        return real_open(self, *args, **kwargs)

    monkeypatch.setattr(pathlib.Path, "open", refused)
    target = tmp_path / "u.webm"
    run = _run(1e-3)
    with pytest.raises(
        io.VideoEncoderError, match="could not write the video"
    ) as caught:
        write_fdtd_animation(target, run, frame=_SMALL)
    assert str(target) in str(caught.value)
    # The caller's path, never the hidden file the probe tried.
    assert ".partial" not in str(caught.value)
    assert engines == []
    assert fake.encodes() == []
    assert list(tmp_path.glob("*.partial")) == []


def test_a_directory_this_process_cannot_search_is_refused_before_a_step(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, engines: list[FDTD2D]
) -> None:
    # Its own status reads; a name inside it does not, and no file goes in.
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    target = tmp_path / "s.webm"
    refusing_disk.refuse_status(monkeypatch, target)
    refusing_disk.refuse_partials(monkeypatch)
    run = _run(1e-3)
    with pytest.raises(
        io.VideoEncoderError, match="could not write the video"
    ) as caught:
        write_fdtd_animation(target, run, frame=_SMALL)
    assert f"for {target}: Permission denied" in str(caught.value)
    assert ".partial" not in str(caught.value)
    assert engines == []
    assert fake.encodes() == []


def test_a_probe_the_system_will_not_remove_does_not_stop_the_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The probe's file was created, so the directory takes the video; that
    # it stays (a scanner holds it on Windows, or the directory lets no file
    # go) refuses nothing.
    fake_ffmpeg.install(tmp_path, monkeypatch)
    refusing_disk.hold_partials(monkeypatch)
    target = tmp_path / "p.webm"
    write_fdtd_animation(target, _run(1e-3), frame=_SMALL_FIXED)
    assert target.read_bytes().startswith(b"\x1a\x45\xdf\xa3")
    # What stays is the probe's empty file, hidden; none of the video.
    assert refusing_disk.partial_sizes(tmp_path) == [0]


_ELASTIC = ElasticRun(
    c_p=4000.0,
    c_s=2300.0,
    dx=0.01,
    duration_s=1e-3,
    rho=2500.0,
    shape=(20, 24),
    sources=[ExplosionSource(ix=12, iy=10, waveform=_SOURCE.value)],
)


@pytest.mark.parametrize(
    ("changes", "error", "match"),
    [
        (
            {"run": _run(1e-3, recording=FDTDRecording(probes=_PROBES))},
            ValueError,
            "run.recording.snapshot_every",
        ),
        (
            {"run": _run(1e-3, recording=None)},
            ValueError,
            "run.recording.snapshot_every",
        ),
        ({"run": "a run"}, TypeError, "FDTDRun"),
        ({"run": _ELASTIC}, TypeError, "FDTDRun"),
        ({"frame": (480, 246)}, TypeError, "frame"),
        # The last frame at 11132.29 ms: five digits, whose title needs 490 pixels.
        (
            {"run": _LONG, "frame": AnimationFrame(size=(489, 246), color_limit=1.0)},
            ValueError,
            r"at least 490 pixels wide",
        ),
        ({"video": "fast"}, TypeError, "video"),
        ({"compute": "cupy"}, TypeError, "compute"),
        ({"video": VideoOptions(codec="vp9"), "path": "r.mp4"}, ValueError, "holds"),
        ({"path": "r.avi"}, ValueError, "webm"),
    ],
)
def test_a_bad_argument_starts_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    engines: list[FDTD2D],
    changes: dict[str, Any],
    error: type[Exception],
    match: str,
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    target = tmp_path / changes.pop("path", "r.webm")
    arguments: dict[str, Any] = {"run": _run(1e-3), "frame": _SMALL, **changes}
    with pytest.raises(error, match=match):
        write_fdtd_animation(target, **arguments)
    assert engines == []
    assert fake.calls() == []


def test_a_malformed_compute_variable_or_a_missing_directory_starts_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, engines: list[FDTD2D]
) -> None:
    """Neither runs ffmpeg nor builds an engine: both are refused with the arguments."""
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    run = _run(1e-3)
    monkeypatch.setenv("PHONOMETRY_COMPUTE", "gpu-please")
    with pytest.raises(ValueError, match="PHONOMETRY_COMPUTE='gpu-please'"):
        write_fdtd_animation(tmp_path / "e.webm", run, frame=_SMALL)
    monkeypatch.delenv("PHONOMETRY_COMPUTE")
    missing = tmp_path / "missing" / "m.webm"
    with pytest.raises(FileNotFoundError, match="does not exist or cannot be reached"):
        write_fdtd_animation(missing, run, frame=_SMALL)
    assert engines == []
    assert fake.calls() == []


@pytest.mark.parametrize(
    ("changes", "error", "match"),
    [
        # The run's kind first, before the path.
        ({"run": "a run", "path": "r.avi"}, TypeError, "FDTDRun"),
        # The frame's record before the compute record.
        ({"frame": (480, 246), "compute": "cupy"}, TypeError, "'frame'"),
        # The frame's width against the run before the path.
        (
            {
                "run": _LONG,
                "frame": AnimationFrame(size=(489, 246), color_limit=1.0),
                "path": "r.avi",
            },
            ValueError,
            "at least 490 pixels wide",
        ),
        # The path before the colour scale, which this grid leaves nothing
        # to find by.
        (
            {
                "path": "r.avi",
                "run": _run(
                    1e-3,
                    shape=(12, 12),
                    sources=[GaussianPulse(ix=6, iy=6, half_width_s=4e-5)],
                    recording=FDTDRecording(snapshot_every=10),
                    boundaries=FDTDBoundaries(
                        sides="absorbing", absorbing_layer_cells=6
                    ),
                ),
            },
            ValueError,
            "webm",
        ),
    ],
    ids=["run-path", "frame-compute", "width-path", "path-scale"],
)
def test_of_two_bad_arguments_the_first_checked_is_refused(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    changes: dict[str, Any],
    error: type[Exception],
    match: str,
) -> None:
    """The order :func:`_checked_call` states, the one every route checks in."""
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    target = tmp_path / changes.pop("path", "r.webm")
    arguments: dict[str, Any] = {"run": _run(1e-3), "frame": _SMALL, **changes}
    with pytest.raises(error, match=match):
        write_fdtd_animation(target, **arguments)
    assert fake.calls() == []


def test_a_frame_too_narrow_for_a_long_run_is_asked_for_at_the_width_it_needs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, engines: list[FDTD2D]
) -> None:
    """The message gives the caller's frame at that width, its language and colour limit kept."""
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    frame = AnimationFrame(language="es", size=(489, 300), color_limit=2.5)
    wider = (
        "at 11132,29 ms, needs a frame at least 490 pixels wide to stay clear of "
        "the frame's margin, and 'frame' is 489 pixels wide: give "
        "AnimationFrame(language='es', size=(490, 300), color_limit=2.5)"
    )
    with pytest.raises(ValueError, match=re.escape(wider) + "$"):
        write_fdtd_animation(tmp_path / "l.webm", _LONG, frame=frame)
    assert engines == []
    assert fake.calls() == []


@pytest.mark.parametrize(
    ("changes", "error", "match"),
    [
        ({"size": (480,)}, ValueError, "size"),
        ({"size": "large"}, TypeError, "size"),
        ({"size": (479, 244)}, ValueError, "at least 479 by 245"),
        ({"size": (480.5, 246)}, ValueError, "size"),
        ({"color_limit": -1.0}, ValueError, "color_limit"),
        ({"color_limit": float("nan")}, ValueError, "color_limit"),
        ({"color_limit": "1"}, TypeError, "color_limit"),
        # A flag is not a number: float(True) would draw the scale at ±1.
        (
            {"color_limit": True},
            TypeError,
            r"^'color_limit' must be one number, not a bool; got True\.$",
        ),
        ({"color_limit": np.True_}, TypeError, r"not a bool; got np\.True_\.$"),
        ({"language": "fr"}, ValueError, "language"),
    ],
)
def test_a_bad_frame_is_refused_when_the_record_is_built(
    changes: dict[str, Any], error: type[Exception], match: str
) -> None:
    with pytest.raises(error, match=match):
        AnimationFrame(**changes)


def test_a_frame_holds_what_it_was_given() -> None:
    # A list with a whole float, held as the pair of ints it names.
    frame = AnimationFrame(size=[640.0, 480], color_limit=2)  # type: ignore[arg-type]
    assert frame.size == (640, 480)
    assert frame.color_limit == 2.0
    with pytest.raises(AttributeError, match="size"):
        frame.size = (480, 246)  # type: ignore[misc]


def test_a_missing_ffmpeg_is_found_out_before_a_step(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, engines: list[FDTD2D]
) -> None:
    monkeypatch.setitem(mpl.rcParams, "animation.ffmpeg_path", "no-such-ffmpeg-here")
    run = _run(1e-3)
    with pytest.raises(io.FFmpegNotFoundError, match="animation.ffmpeg_path"):
        write_fdtd_animation(tmp_path / "m.webm", run, frame=_SMALL)
    assert engines == []


def test_an_encoder_that_cannot_run_is_found_out_before_a_step(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, engines: list[FDTD2D]
) -> None:
    # The fake has av1_nvenc compiled in and failing, as on a machine without the GPU.
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    # No colour limit: a first pass would step first.
    run = _run()
    video = VideoOptions(encoder="nvenc")
    with pytest.raises(io.VideoEncoderError, match="nvenc"):
        write_fdtd_animation(tmp_path / "n.webm", run, frame=_SMALL, video=video)
    assert engines == []
    assert fake.encodes() == []


def test_a_raw_encoder_this_ffmpeg_lacks_is_refused_before_a_step(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, engines: list[FDTD2D]
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    run = _run()
    video = VideoOptions(ffmpeg_encoder="libnothing")
    with pytest.raises(io.VideoEncoderError, match="has no encoder 'libnothing'"):
        write_fdtd_animation(tmp_path / "r.webm", run, frame=_SMALL, video=video)
    assert engines == []
    assert fake.encodes() == []


def test_the_encoder_is_tried_once_before_the_first_step(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    write_fdtd_animation(tmp_path / "o.webm", _run(), frame=_SMALL)
    tried = [t["argv"][t["argv"].index("-c:v") + 1] for t in fake.trials()]
    assert tried == ["av1_nvenc", "libsvtav1"]
    (encode,) = fake.encodes()
    assert encode["argv"][encode["argv"].index("-c:v") + 1] == "libsvtav1"


def test_a_failed_encode_closes_the_march(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_ffmpeg.install(tmp_path, monkeypatch, die_after_frames=2)
    closed: list[bool] = []

    def frames() -> Generator[np.ndarray, None, None]:
        try:
            for _ in range(8):
                yield np.zeros((8, 8))
        finally:
            closed.append(True)

    request = video_request(tmp_path / "c.webm", VideoOptions(encoder="cpu"))
    frame = AnimationFrame(size=(480, 246))
    encoding = video_module._preflight(request, frame.size)
    march = frames()
    backend = bk.backend_for(Compute())
    with pytest.raises(io.VideoEncoderError, match="muxer failed"):
        video_module._render(
            request,
            encoding,
            frame,
            frames=march,
            backend=backend,
            n_frames=8,
            frame_dt=1e-3,
            setup=lambda ax, field: ax.imshow(field),
            title=str,
        )
    assert closed == [True]


def test_a_drawing_that_fails_closes_the_march(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from phonometry._plot import simulation as plot

    fake_ffmpeg.install(tmp_path, monkeypatch)
    closed: list[bool] = []

    def frames() -> Generator[np.ndarray, None, None]:
        try:
            for _ in range(8):
                yield np.zeros((8, 8))
        finally:
            closed.append(True)

    def broken(*_args: object) -> None:
        msg = "the drawing failed"
        raise RuntimeError(msg)

    monkeypatch.setattr(plot, "_update_snapshot", broken)
    target = tmp_path / "f.webm"
    request = video_request(target, VideoOptions(encoder="cpu"))
    frame = AnimationFrame(size=(480, 246))
    encoding = video_module._preflight(request, frame.size)
    march = frames()
    backend = bk.backend_for(Compute())
    with pytest.raises(RuntimeError, match="the drawing failed") as caught:
        video_module._render(
            request,
            encoding,
            frame,
            frames=march,
            backend=backend,
            n_frames=8,
            frame_dt=1e-3,
            setup=lambda ax, field: ax.imshow(field),
            title=str,
        )
    # The drawing's own error, not one of the encoder's (a RuntimeError too).
    assert caught.type is RuntimeError
    assert closed == [True]
    assert not target.exists()
    # On Windows the fake runs behind cmd.exe, which a kill does not reach,
    # and the orphaned fake writes its output when its stdin closes.
    if sys.platform != "win32":
        assert [p.name for p in tmp_path.iterdir() if p.name.endswith(".partial")] == []


def test_a_run_that_fails_after_its_last_frame_leaves_the_old_video(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The steps after the last frame run before the video takes the path's place.

    A step there that fails (a source that raises, a run its client
    cancelled) fails the call, and what was at the path stays there, with
    no hidden file left beside it.
    """
    fake_ffmpeg.install(tmp_path, monkeypatch)

    def frames() -> Generator[np.ndarray, None, None]:
        for _ in range(3):
            yield np.zeros((8, 8))
        msg = "a step after the last frame failed"
        raise RuntimeError(msg)

    target = tmp_path / "old.webm"
    target.write_bytes(b"the video already there")
    request = video_request(target, VideoOptions(encoder="cpu"))
    frame = AnimationFrame(size=(480, 246))
    encoding = video_module._preflight(request, frame.size)
    backend = bk.backend_for(Compute())
    march = frames()
    with pytest.raises(RuntimeError, match="a step after the last frame failed"):
        video_module._render(
            request,
            encoding,
            frame,
            frames=march,
            backend=backend,
            n_frames=3,
            frame_dt=1e-3,
            setup=lambda ax, field: ax.imshow(field),
            title=str,
        )
    assert target.read_bytes() == b"the video already there"
    assert [p.name for p in tmp_path.iterdir() if p.name.endswith(".partial")] == []


def test_an_interrupted_first_pass_leaves_the_device_as_it_found_it() -> None:
    current = ["the caller's"]

    @contextlib.contextmanager
    def on_the_device() -> Generator[None, None, None]:
        # A device scope as CuPy's: leaving it makes current again the device
        # that was current when it was entered.
        before = current[0]
        current[0] = "the run's"
        try:
            yield
        finally:
            current[0] = before

    backend = dataclasses.replace(bk.backend_for(Compute()), _context=on_the_device)
    closed: list[bool] = []

    class Unreadable:
        def __abs__(self) -> NoReturn:
            msg = "the device failed"
            raise RuntimeError(msg)

    def frames() -> Generator[object, None, None]:
        # A march: the field at t = 0, then the steps inside the device scope.
        try:
            yield np.ones((2, 2))
            with backend.context():
                yield np.ones((2, 2))
                yield Unreadable()
                yield np.ones((2, 2))
        finally:
            closed.append(True)

    march = frames()
    keep = np.ones((2, 2), dtype=np.bool_)
    with pytest.raises(RuntimeError, match="the device failed"):
        video_module._peak(march, backend, keep)
    assert closed == [True]
    assert current == ["the caller's"]


def test_the_frames_speak_spanish(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from phonometry._plot import simulation as plot

    fake_ffmpeg.install(tmp_path, monkeypatch)
    titles: list[str] = []
    original = plot._update_snapshot

    def recorded(image: AxesImage, field: np.ndarray, title: str) -> None:
        titles.append(title)
        original(image, field, title)

    monkeypatch.setattr(plot, "_update_snapshot", recorded)
    write_fdtd_animation(
        tmp_path / "es.webm",
        _run(1e-3),
        frame=AnimationFrame(language="es", size=(480, 246), color_limit=1.0),
    )
    assert titles
    assert all(t.startswith("Campo de presión FDTD en $t$ =") for t in titles)
    assert all("," in t for t in titles)


def test_the_frames_use_the_default_style(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A caller's dark style does not reach the frames: pixel for pixel, the default style's.

    The writer draws under ``style.context("default")``, which sets every
    setting back, so the first frame written under ``dark_background`` is
    the one written under the default style, white page and all.
    """
    from matplotlib import style

    light, dark = tmp_path / "light.rgba", tmp_path / "dark.rgba"
    fake = fake_ffmpeg.install(tmp_path, monkeypatch, first_frame=str(light))
    write_fdtd_animation(tmp_path / "light.webm", _run(1e-3), frame=_SMALL_FIXED)
    fake.update(first_frame=str(dark))
    with style.context("dark_background"):
        write_fdtd_animation(tmp_path / "dark.webm", _run(1e-3), frame=_SMALL_FIXED)
    corner = np.frombuffer(light.read_bytes(), dtype=np.uint8)[:4]
    assert corner.tolist() == [255, 255, 255, 255]
    assert dark.read_bytes() == light.read_bytes()


@pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="needs ffmpeg and ffprobe on PATH; the CI video job installs them",
)
def test_a_real_video_has_every_frame(tmp_path: Path) -> None:
    target = tmp_path / "real.webm"
    res = write_fdtd_animation(
        target, _run(), frame=_SMALL_FIXED, video=VideoOptions(encoder="cpu")
    )
    shown = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-count_frames",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,nb_read_frames",
            "-of",
            "default=noprint_wrappers=1",
            str(target),
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    ).stdout
    probe = dict(line.split("=", 1) for line in shown.splitlines())
    assert (probe["width"], probe["height"]) == ("480", "246")
    assert int(probe["nb_read_frames"]) == (res.times.size - 1) // 10 + 1


@pytest.mark.skipif(
    shutil.which("ffmpeg") is None,
    reason="needs ffmpeg on PATH; the CI video job installs it",
)
def test_options_ffmpeg_refuses_fail_at_the_first_frames_of_the_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A raw encoder's options are not tried before the run; ffmpeg's refusal stops it at its first frames."""
    from phonometry._plot import simulation as plot

    listing = subprocess.run(
        ["ffmpeg", "-hide_banner", "-encoders"],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    ).stdout
    if " libvpx-vp9 " not in listing:
        pytest.skip("this ffmpeg has no libvpx-vp9")
    drawn: list[str] = []
    update = plot._update_snapshot

    def counted(image: AxesImage, field: NDArray[np.float64], title: str) -> None:
        drawn.append(title)
        update(image, field, title)

    monkeypatch.setattr(plot, "_update_snapshot", counted)
    target = tmp_path / "raw.webm"
    target.write_bytes(b"the video that was there")
    # About a hundred frames, a few of which ffmpeg reads before it gives up.
    run = _run(2e-2)
    n_frames = run._checked.steps // 10 + 1
    video = VideoOptions(ffmpeg_encoder="libvpx-vp9", ffmpeg_options=("-crf", "99"))
    with pytest.raises(io.VideoEncoderError, match="'crf' out of range") as caught:
        write_fdtd_animation(target, run, frame=_SMALL_FIXED, video=video)
    assert f"while writing {target} with the encoder libvpx-vp9" in str(caught.value)
    assert len(drawn) < n_frames // 2
    assert target.read_bytes() == b"the video that was there"
    assert list(tmp_path.glob("*.partial")) == []
