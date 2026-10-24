#  Copyright (c) 2026. Jose Manuel Requena Plens
"""An elastic FDTD run written straight to a video, in the unit of the field it draws."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

import numpy as np
import pytest

pytest.importorskip("matplotlib")

import fake_ffmpeg

from phonometry import io
from phonometry.io import VideoOptions
from phonometry.simulation import (
    AnimationFrame,
    ElasticBoundaries,
    ElasticFDTD2D,
    ElasticRecording,
    ElasticRun,
    ExplosionSource,
    FDTDRecording,
    FDTDRun,
    ForceSource,
    GaussianPulse,
    elastic_fdtd_simulation,
    write_elastic_fdtd_animation,
)
from phonometry.simulation import elastic_fdtd as ef
from phonometry.simulation import video as video_module

if TYPE_CHECKING:
    from pathlib import Path

_PULSE = GaussianPulse(ix=0, iy=0, half_width_s=4e-5)
_SMALL = AnimationFrame(size=(480, 246))
# Steps between two frames: a run of 1 or 2 ms (943 or 1886 steps) draws
# 16 or 32 frames, and steps on after its last one.
_EVERY = 60


def _run(duration: float = 2e-3, **changes: Any) -> ElasticRun:
    arguments: dict[str, Any] = {
        "rho": 2500.0,
        "shape": (30, 40),
        "sources": [
            ExplosionSource(ix=20, iy=15, waveform=_PULSE.value),
            ForceSource(ix=8, iy=4, direction="x", waveform=_PULSE.value),
        ],
        "recording": ElasticRecording(
            probes=[(5, 5), (30, 20)],
            probe_fields=("p", "vy"),
            snapshot_every=_EVERY,
            snapshot_field="vy",
        ),
        "boundaries": ElasticBoundaries(
            sides={"top": "free", "bottom": "absorbing"}, absorbing_layer_cells=5
        ),
    }
    arguments.update(changes)
    return ElasticRun(c_p=4000.0, c_s=2300.0, dx=0.01, duration_s=duration, **arguments)


@pytest.fixture
def engines(monkeypatch: pytest.MonkeyPatch) -> list[ElasticFDTD2D]:
    """Every elastic engine a writer builds, in order (they are built in elastic_fdtd._elastic_engine)."""
    built: list[ElasticFDTD2D] = []

    def counted(*args: Any, **kwargs: Any) -> ElasticFDTD2D:
        sim = ElasticFDTD2D(*args, **kwargs)
        built.append(sim)
        return sim

    monkeypatch.setattr(ef, "ElasticFDTD2D", counted)
    return built


def test_the_result_is_the_simulation_s_without_snapshots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    run = _run()
    res = write_elastic_fdtd_animation(
        tmp_path / "e.webm",
        run,
        frame=AnimationFrame(size=(480, 246), color_limit=1e-6),
    )
    reference = elastic_fdtd_simulation(run)
    assert np.array_equal(res.signals, reference.signals)
    assert np.array_equal(res.times, reference.times)
    assert res.free_sides == reference.free_sides
    assert res.snapshots is None
    assert res.snapshot_field == "vy"
    assert res.provenance == reference.provenance
    assert fake.encodes()[0]["frames"] == (res.times.size - 1) // _EVERY + 1


def test_the_found_limit_leaves_out_the_driven_cells() -> None:
    run = _run()
    keep = video_module._elastic_keep(run)
    assert keep[15, 20] == 0.0  # the explosion's cell
    assert keep[4, 8] == 0.0  # the two cells either side of the force's face
    assert keep[4, 9] == 0.0
    assert not keep[-5:].any()  # the absorbing layer at the bottom
    assert keep[0].all()  # a free surface is not driven
    limit, _ = video_module._elastic_limit(run, None, keep)
    res = elastic_fdtd_simulation(run)
    assert res.snapshots is not None
    assert limit == float(np.max(np.abs(res.snapshots) * keep))


@pytest.mark.parametrize(("limit", "builds"), [(1e-6, 1), (None, 2)])
def test_a_given_limit_steps_once_and_a_found_one_twice(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    engines: list[ElasticFDTD2D],
    limit: float | None,
    builds: int,
) -> None:
    fake_ffmpeg.install(tmp_path, monkeypatch)
    write_elastic_fdtd_animation(
        tmp_path / "r.webm",
        _run(1e-3),
        frame=AnimationFrame(size=(480, 246), color_limit=limit),
    )
    assert len(engines) == builds


def test_on_the_strict_backend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, on_strict: None
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    res = write_elastic_fdtd_animation(tmp_path / "s.webm", _run(1e-3), frame=_SMALL)
    assert fake.encodes()[0]["frames"] == (res.times.size - 1) // _EVERY + 1


def test_a_run_on_the_default_boundaries_is_drawn(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    run = _run(1e-3, boundaries=None)
    # Kept as given: the writer reads the resolved sides from run._checked.
    assert run.boundaries is None
    res = write_elastic_fdtd_animation(tmp_path / "b.webm", run, frame=_SMALL)
    reference = elastic_fdtd_simulation(run)
    assert res.free_sides == reference.free_sides
    assert np.array_equal(res.signals, reference.signals)
    assert fake.encodes()[0]["frames"] == (res.times.size - 1) // _EVERY + 1


def test_a_covered_grid_asks_for_the_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, engines: list[ElasticFDTD2D]
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    covered = _run(
        1e-3,
        shape=(10, 10),
        sources=[ExplosionSource(ix=5, iy=5, waveform=_PULSE.value)],
        recording=ElasticRecording(snapshot_every=2),
        boundaries=ElasticBoundaries(sides="absorbing", absorbing_layer_cells=5),
    )
    with pytest.raises(
        ValueError,
        match=r"^the sources and the absorbing layer cover every cell a frame keeps"
        r".*AnimationFrame\(color_limit=\.\.\.\)$",
    ):
        write_elastic_fdtd_animation(tmp_path / "c.webm", covered, frame=_SMALL)
    assert engines == []
    assert fake.calls() == []


@pytest.mark.parametrize("field", ["p", "vx", "vy"])
def test_a_field_that_never_leaves_the_sources_has_nothing_to_scale_by(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: Literal["p", "vx", "vy"]
) -> None:
    # One step: the engine has written only the cells the sources drive.
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    one_step = ElasticFDTD2D(4000.0, 2300.0, 0.01, rho=2500.0, shape=(30, 40)).dt
    recording = ElasticRecording(snapshot_every=1, snapshot_field=field)
    run = _run(one_step, recording=recording)
    # An elastic run has no injection lines: the message does not name any.
    with pytest.raises(
        ValueError,
        match=r"^the field stays zero outside the sources and the absorbing layer "
        r"for the whole run.*AnimationFrame\(color_limit=\.\.\.\)$",
    ):
        write_elastic_fdtd_animation(tmp_path / "z.webm", run, frame=_SMALL)
    assert fake.encodes() == []


@pytest.mark.parametrize(
    ("changes", "error", "match"),
    [
        (
            {"run": _run(1e-3, recording=ElasticRecording(probes=[(5, 5)]))},
            ValueError,
            "run.recording.snapshot_every",
        ),
        (
            {"run": _run(1e-3, recording=None)},
            ValueError,
            "run.recording.snapshot_every",
        ),
        (
            {
                "run": FDTDRun(
                    c=343.0,
                    dx=0.01,
                    duration_s=1e-3,
                    shape=(20, 20),
                    sources=[_PULSE],
                    recording=FDTDRecording(snapshot_every=2),
                )
            },
            TypeError,
            "ElasticRun",
        ),
        ({"frame": {"color_limit": 1e-6}}, TypeError, "frame"),
        # A run of 12 s on cells of 100 m, the last frame at 10606.60 ms: five
        # digits, whose title needs 490 pixels.
        (
            {
                "run": ElasticRun(
                    c_p=4000.0,
                    c_s=2300.0,
                    dx=100.0,
                    duration_s=12.0,
                    rho=2500.0,
                    shape=(20, 24),
                    sources=[ExplosionSource(ix=10, iy=10, waveform=_PULSE.value)],
                    recording=ElasticRecording(snapshot_every=1000),
                ),
                "frame": AnimationFrame(size=(489, 246), color_limit=1e-6),
            },
            ValueError,
            r"at least 490 pixels wide",
        ),
        ({"video": VideoOptions(codec="h264")}, ValueError, "holds"),
    ],
)
def test_a_bad_argument_starts_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    engines: list[ElasticFDTD2D],
    changes: dict[str, Any],
    error: type[Exception],
    match: str,
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    arguments: dict[str, Any] = {"run": _run(1e-3), "frame": _SMALL, **changes}
    with pytest.raises(error, match=match):
        write_elastic_fdtd_animation(tmp_path / "n.webm", **arguments)
    assert engines == []
    assert fake.calls() == []


def test_an_encoder_that_cannot_run_is_found_out_before_a_step(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, engines: list[ElasticFDTD2D]
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    # No colour limit: a first pass would step first.
    run = _run(1e-3)
    video = VideoOptions(encoder="nvenc")
    with pytest.raises(io.VideoEncoderError, match="nvenc"):
        write_elastic_fdtd_animation(
            tmp_path / "n.webm", run, frame=_SMALL, video=video
        )
    assert engines == []
    assert fake.encodes() == []
