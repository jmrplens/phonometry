#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Parity tests: ``scripts/fdtd_gpu.py`` versus the library FDTD engine.

``GpuFDTD2D`` is a backend-injectable replica of
:class:`phonometry.simulation.fdtd.FDTD2D` for the feature subset the
documentation animations use. These tests lock the replica to the library
step by step on small grids: with ``xp=numpy`` every recorded pressure
field must match the reference within 1e-12 of the field peak (in practice
the NumPy path is bit-identical because the update expressions share the
exact operation order). When CuPy and a CUDA device are available the same
scenarios run with ``xp=cupy`` under a looser (ULP-scale reassociation)
tolerance; on machines without a GPU those cases skip.

The job-packaging round trip of ``fdtd_gpu_remote.build_job`` through
``job_runner.run_job`` is covered too, since the remote runner feeds the
engine only through that path.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest

from phonometry.simulation.fdtd import (
    FDTD2D,
    CWSource,
    GaussianPulse,
    PlaneWaveSource,
)

if TYPE_CHECKING:
    from types import ModuleType

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import fdtd_dispatch
import fdtd_gpu
import fdtd_gpu_remote
import job_runner


def _cupy_or_none() -> ModuleType | None:
    """CuPy with a working CUDA device, else None."""
    try:
        import cupy

        cupy.cuda.runtime.getDeviceCount()
        cupy.arange(1).sum()
    except Exception:  # noqa: BLE001 - any import/CUDA failure means no GPU
        return None
    return cupy


_CUPY = _cupy_or_none()


def _remote_or_none() -> fdtd_gpu_remote.RemoteConfig | None:
    """The configured GPU host when it answers, else None.

    A CUDA card is not the only way to reach one. ``fdtd_gpu_remote`` already
    ships a job to a machine that has one, and that is the path the animation
    renders take, so the same parity can be proved on a workstation with no
    GPU of its own: what is under test is the engine, not the local hardware.
    """
    fdtd_gpu_remote.load_env()
    config = fdtd_gpu_remote.RemoteConfig.from_env()
    if not config.host or not fdtd_gpu_remote.remote_available(config):
        return None
    return config


_REMOTE = _remote_or_none()

#: Skip mark for the cases that need the remote GPU.
_needs_remote = pytest.mark.skipif(
    _REMOTE is None,
    reason="no PHONO_GPU_HOST answers (set it in .env to run the GPU parity here)",
)

BACKENDS = [
    pytest.param(np, 1e-12, id="numpy"),
    pytest.param(
        _CUPY,
        1e-10,
        id="cupy",
        marks=pytest.mark.skipif(
            _CUPY is None, reason="CuPy with a CUDA device is not available"
        ),
    ),
]

_NY, _NX = 60, 80
_DX = 0.01
_STEPS = 200

#: Relative to the run peak. The GPU reassociates the update sums, so the two
#: engines agree to ULP scale rather than bit for bit, as the local `cupy`
#: parameter above already allows.
_GPU_TOL = 1e-10

#: One remote job is an SSH round trip plus a Docker start, measured at about
#: six seconds for these grids. The ceiling is generous enough that a cold
#: image pull does not turn a slow run into a red one.
_REMOTE_TIMEOUT_S = 180.0


def _scenarios() -> dict[str, dict[str, Any]]:
    """Constructor kwargs of every parity scenario (library names).

    An optional ``"c"`` entry replaces the default scalar sound speed.
    """
    rho_obstacle = np.full((_NY, _NX), 1.2)
    rho_obstacle[24:36, 30:44] = 6000.0  # dense block scatterer
    damping_map = np.zeros((_NY, _NX))
    damping_map[:, _NX - 16 :] = 35.0  # lossy slab at the right
    mask = np.zeros((_NY, _NX), dtype=np.bool_)
    mask[40:46, 10:70] = True  # rigid slat obstacle
    c_hetero = np.full((_NY, _NX), 343.0)  # air over a water layer
    c_hetero[_NY // 2 :, :] = 1500.0
    rho_hetero = np.full((_NY, _NX), 1.2)
    rho_hetero[_NY // 2 :, :] = 1000.0
    return {
        "rigid_box": {},
        "dense_rho_obstacle": {"rho": rho_obstacle},
        "heterogeneous_c": {"c": c_hetero, "rho": rho_hetero},
        "sponge": {
            "sponge_width": 12,
            "sponge_sides": ("left", "right", "bottom"),
            "sponge_reflection": 1e-3,
        },
        "sponge_side_string": {"sponge_width": 12, "sponge_sides": "top"},
        "impedance_edges": {
            "edge_impedance": {
                "top": 413.0,
                "left": np.linspace(200.0, 800.0, _NY),
            }
        },
        "impedance_right_bottom": {
            "edge_impedance": {
                "right": 620.0,
                "bottom": np.linspace(300.0, 900.0, _NX),
            }
        },
        "damping_scalar": {"damping": 25.0},
        "damping_map": {"damping": damping_map},
        "obstacle_mask": {"obstacle_mask": mask},
        "combined": {
            "rho": rho_obstacle,
            "sponge_width": 10,
            "sponge_sides": ("left", "right"),
            "damping": damping_map,
            "edge_impedance": {"top": 413.0},
        },
    }


_WAVES: dict[str, dict[str, Any]] = {
    "down": {"center": 0.12, "width": 0.05},
    "up": {"center": 0.45, "width": 0.05, "wavelength": 0.08},
    "left": {"center": 0.60, "width": 0.06, "amplitude": 0.7},
    "right": {"center": 0.20, "width": 0.05, "wavelength": 0.10},
}


def _split_c(kwargs: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    """Pop the optional ``"c"`` entry (default scalar 343) from *kwargs*."""
    rest = dict(kwargs)
    return rest.pop("c", 343.0), rest


def _reference(
    kwargs: dict[str, Any], wave: dict[str, Any], direction: str
) -> list[np.ndarray]:
    """Library-engine pressure fields every 50 steps."""
    c, rest = _split_c(kwargs)
    ref = FDTD2D(c, _DX, shape=(_NY, _NX), **rest)
    ref.add_plane_wave(direction, **wave)
    fields = []
    for i in range(_STEPS):
        ref.step()
        if (i + 1) % 50 == 0:
            fields.append(ref.p.copy())
    return fields


def _assert_parity(
    fields: list[np.ndarray], got: list[np.ndarray], rtol_peak: float
) -> None:
    """Every recorded field matches within *rtol_peak* of the run peak."""
    peak = max(float(np.max(np.abs(f))) for f in fields)
    assert peak > 0.0
    for ref_f, got_f in zip(fields, got, strict=True):
        np.testing.assert_allclose(got_f, ref_f, rtol=0.0, atol=rtol_peak * peak)


@pytest.mark.parametrize(("xp", "tol"), BACKENDS)
@pytest.mark.parametrize("direction", list(_WAVES))
def test_plane_wave_directions_match_library(
    xp: ModuleType, tol: float, direction: str
) -> None:
    """A plane packet in each travel direction reproduces the library."""
    wave = _WAVES[direction]
    fields = _reference({}, wave, direction)
    sim = fdtd_gpu.GpuFDTD2D(343.0, _DX, shape=(_NY, _NX), xp=xp)
    sim.add_plane_wave(direction, **wave)
    got = []
    for i in range(_STEPS):
        sim.step()
        if (i + 1) % 50 == 0:
            got.append(sim.pressure())
    _assert_parity(fields, got, tol)
    assert sim.n == _STEPS
    assert sim.dt == pytest.approx(0.6 * _DX / (343.0 * np.sqrt(2.0)))
    assert sim.time == pytest.approx(_STEPS * sim.dt)


@pytest.mark.parametrize(("xp", "tol"), BACKENDS)
@pytest.mark.parametrize("scenario", list(_scenarios()))
def test_scenarios_match_library(xp: ModuleType, tol: float, scenario: str) -> None:
    """Each engine feature (and their combination) reproduces the library."""
    kwargs = _scenarios()[scenario]
    wave = {"center": 0.15, "width": 0.06, "wavelength": 0.09}
    fields = _reference(kwargs, wave, "down")
    c, rest = _split_c(kwargs)
    sim = fdtd_gpu.GpuFDTD2D(c, _DX, shape=(_NY, _NX), xp=xp, **rest)
    sim.add_plane_wave("down", **wave)
    got = []
    for i in range(_STEPS):
        sim.step()
        if (i + 1) % 50 == 0:
            got.append(sim.pressure())
    _assert_parity(fields, got, tol)


def test_numpy_path_is_bit_identical() -> None:
    """With xp=numpy the replica is exactly the library, bit for bit."""
    kwargs = _scenarios()["combined"]
    wave = {"center": 0.15, "width": 0.06, "wavelength": 0.09}
    ref = FDTD2D(343.0, _DX, shape=(_NY, _NX), **kwargs)
    ref.add_plane_wave("down", **wave)
    sim = fdtd_gpu.GpuFDTD2D(343.0, _DX, shape=(_NY, _NX), xp=np, **kwargs)
    sim.add_plane_wave("down", **wave)
    for _ in range(_STEPS):
        ref.step()
        sim.step()
    assert np.array_equal(sim.p, ref.p)


def test_job_round_trip_matches_library() -> None:
    """build_job -> job_runner.run_job reproduces the library fields."""
    kwargs = _scenarios()["combined"]
    wave = {"center": 0.15, "width": 0.06, "wavelength": 0.09}
    fields = _reference(kwargs, wave, "down")
    job = fdtd_gpu_remote.build_job(
        343.0,
        _DX,
        shape=(_NY, _NX),
        steps=_STEPS,
        sample_steps=[50, 100, 150, 200],
        plane_waves=[{"direction": "down", **wave}],
        **kwargs,
    )
    result = job_runner.run_job(job)
    assert result["backend"] in ("numpy", "cupy")
    assert int(result["cells"]) == _NY * _NX
    tol = 1e-12 if result["backend"] == "numpy" else 1e-10
    _assert_parity(fields, list(np.asarray(result["frames"])), tol)


def test_job_round_trip_edge_array_and_obstacle() -> None:
    """Per-cell 1D edge impedance and a non-trivial obstacle survive the npz."""
    mask = np.zeros((_NY, _NX), dtype=np.bool_)
    mask[18:22, 8:36] = True  # horizontal slat
    mask[30:52, 44:48] = True  # vertical baffle
    kwargs = {
        "edge_impedance": {"left": np.linspace(220.0, 760.0, _NY)},
        "obstacle_mask": mask,
    }
    wave = {"center": 0.15, "width": 0.06, "wavelength": 0.09}
    fields = _reference(kwargs, wave, "down")
    job = fdtd_gpu_remote.build_job(
        343.0,
        _DX,
        shape=(_NY, _NX),
        steps=_STEPS,
        sample_steps=[50, 100, 150, 200],
        plane_waves=[{"direction": "down", **wave}],
        **kwargs,
    )
    result = job_runner.run_job(job)
    tol = 1e-12 if result["backend"] == "numpy" else 1e-10
    _assert_parity(fields, list(np.asarray(result["frames"])), tol)


def test_job_round_trip_empty_sponge_sides() -> None:
    """An explicit sponge_sides=() with sponge_width > 0 stays empty.

    The library treats the empty tuple as "no sponge anywhere" even when a
    width is given; the job archive must not turn it back into the
    all-four-sides default.
    """
    kwargs: dict[str, Any] = {"sponge_width": 12, "sponge_sides": ()}
    wave = {"center": 0.15, "width": 0.06, "wavelength": 0.09}
    fields = _reference(kwargs, wave, "down")
    job = fdtd_gpu_remote.build_job(
        343.0,
        _DX,
        shape=(_NY, _NX),
        steps=_STEPS,
        sample_steps=[50, 100, 150, 200],
        plane_waves=[{"direction": "down", **wave}],
        **kwargs,
    )
    assert job["sponge_sides"].size == 0
    result = job_runner.run_job(job)
    tol = 1e-12 if result["backend"] == "numpy" else 1e-10
    _assert_parity(fields, list(np.asarray(result["frames"])), tol)


def test_job_round_trip_init_scale_x() -> None:
    """A cosine taper on the initial front matches the manual scaling."""
    window = 0.5 * (1.0 - np.cos(2.0 * np.pi * np.arange(_NX) / (_NX - 1)))
    wave = {"center": 0.15, "width": 0.06, "wavelength": 0.09}
    sim = fdtd_gpu.GpuFDTD2D(343.0, _DX, shape=(_NY, _NX), xp=np)
    sim.add_plane_wave("down", **wave)
    sim.p *= window[np.newaxis, :]
    sim.vy *= window[np.newaxis, :]
    fields = []
    for i in range(_STEPS):
        sim.step()
        if (i + 1) % 50 == 0:
            fields.append(sim.pressure())
    job = fdtd_gpu_remote.build_job(
        343.0,
        _DX,
        shape=(_NY, _NX),
        steps=_STEPS,
        sample_steps=[50, 100, 150, 200],
        plane_waves=[{"direction": "down", **wave}],
        init_scale_x=window,
    )
    result = job_runner.run_job(job)
    tol = 1e-12 if result["backend"] == "numpy" else 1e-10
    _assert_parity(fields, list(np.asarray(result["frames"])), tol)


def test_job_round_trip_subsampled_frames() -> None:
    """sample_stride=4 + float32 equals the full frames subsampled locally."""
    kwargs = _scenarios()["combined"]
    wave = {"center": 0.15, "width": 0.06, "wavelength": 0.09}
    common: dict[str, Any] = dict(
        shape=(_NY, _NX),
        steps=_STEPS,
        sample_steps=[0, 100, 200],
        plane_waves=[{"direction": "down", **wave}],
        **kwargs,
    )
    full = job_runner.run_job(fdtd_gpu_remote.build_job(343.0, _DX, **common))
    sub = job_runner.run_job(
        fdtd_gpu_remote.build_job(
            343.0, _DX, sample_stride=4, sample_dtype="float32", **common
        )
    )
    full_frames = np.asarray(full["frames"])
    sub_frames = np.asarray(sub["frames"])
    assert full_frames.dtype == np.float64
    assert sub_frames.dtype == np.float32
    assert sub_frames.shape == (3, (_NY + 3) // 4, (_NX + 3) // 4)
    assert sub_frames.nbytes * 32 == full_frames.nbytes
    np.testing.assert_array_equal(
        sub_frames, full_frames[:, ::4, ::4].astype(np.float32)
    )


def test_build_job_validation() -> None:
    """build_job rejects inconsistent sampling and non-integer widths."""
    ok: dict[str, Any] = {"shape": (_NY, _NX), "steps": 100, "sample_steps": [50]}
    with pytest.raises(ValueError, match=r"cfl must lie in \(0, 1\)"):
        fdtd_gpu_remote.build_job(343.0, _DX, cfl=1.5, **ok)
    with pytest.raises(ValueError, match=r"damping must be non-negative and finite"):
        fdtd_gpu_remote.build_job(343.0, _DX, damping=-1.0, **ok)
    bad_damping = np.zeros((_NY + 1, _NX))
    with pytest.raises(
        ValueError, match=r"damping map shape .* does not match the grid"
    ):
        fdtd_gpu_remote.build_job(343.0, _DX, damping=bad_damping, **ok)
    with pytest.raises(ValueError, match=r"unknown impedance sides"):
        fdtd_gpu_remote.build_job(343.0, _DX, edge_impedance={"front": 413.0}, **ok)
    with pytest.raises(
        ValueError,
        match=r"side 'top' cannot be both absorbing and an impedance boundary",
    ):
        fdtd_gpu_remote.build_job(
            343.0, _DX, sponge_width=10, edge_impedance={"top": 413.0}, **ok
        )
    bad_profile = {"top": np.ones(_NX + 2)}
    with pytest.raises(
        ValueError, match=r"impedance for side 'top' must be a scalar or a 1D array"
    ):
        fdtd_gpu_remote.build_job(343.0, _DX, edge_impedance=bad_profile, **ok)
    bad_mask_shape = np.zeros((_NY + 1, _NX), np.bool_)
    with pytest.raises(ValueError, match=r"obstacle_mask must match the grid shape"):
        fdtd_gpu_remote.build_job(343.0, _DX, obstacle_mask=bad_mask_shape, **ok)
    bad_mask_dtype = np.zeros((_NY, _NX), np.int64)
    with pytest.raises(ValueError, match=r"obstacle_mask must be a boolean array"):
        fdtd_gpu_remote.build_job(343.0, _DX, obstacle_mask=bad_mask_dtype, **ok)
    with pytest.raises(ValueError, match=r"sample_steps must lie within \[0, steps\]"):
        fdtd_gpu_remote.build_job(
            343.0, _DX, shape=(_NY, _NX), steps=100, sample_steps=[50, 150]
        )
    with pytest.raises(ValueError, match=r"sample_steps must lie within \[0, steps\]"):
        fdtd_gpu_remote.build_job(
            343.0, _DX, shape=(_NY, _NX), steps=100, sample_steps=[-1, 50]
        )
    with pytest.raises(ValueError, match=r"sample_stride must be >= 1"):
        fdtd_gpu_remote.build_job(343.0, _DX, sample_stride=0, **ok)
    with pytest.raises(ValueError, match=r"sample_stride must be an integer"):
        fdtd_gpu_remote.build_job(343.0, _DX, sample_stride=2.0, **ok)
    with pytest.raises(ValueError, match=r"sample_dtype must be"):
        fdtd_gpu_remote.build_job(343.0, _DX, sample_dtype="int16", **ok)
    with pytest.raises(ValueError, match=r"sponge_width must be an integer"):
        fdtd_gpu_remote.build_job(343.0, _DX, sponge_width=True, **ok)
    with pytest.raises(ValueError, match=r"sponge_width must be an integer"):
        fdtd_gpu_remote.build_job(343.0, _DX, sponge_width=3.5, **ok)
    with pytest.raises(ValueError, match=r"sponge_width must be an integer"):
        fdtd_gpu.GpuFDTD2D(343.0, _DX, shape=(_NY, _NX), sponge_width=2.5)
    too_wide = min(_NY, _NX)
    with pytest.raises(ValueError, match="smallest grid side"):
        fdtd_gpu_remote.build_job(343.0, _DX, sponge_width=too_wide, **ok)
    with pytest.raises(
        ValueError, match=r"sponge_reflection must lie strictly between"
    ):
        fdtd_gpu_remote.build_job(
            343.0, _DX, sponge_width=4, sponge_reflection=1.5, **ok
        )
    bad_scale_length = np.ones(_NX + 1)
    with pytest.raises(ValueError, match=r"init_scale_x must be a 1D array of length"):
        fdtd_gpu_remote.build_job(343.0, _DX, init_scale_x=bad_scale_length, **ok)
    bad_scale_nan = np.full(_NX, np.nan)
    with pytest.raises(ValueError, match=r"init_scale_x must be finite everywhere"):
        fdtd_gpu_remote.build_job(343.0, _DX, init_scale_x=bad_scale_nan, **ok)


def test_sample_steps_deduplicated_local_and_remote_contract() -> None:
    """Repeated sample_steps collapse to one frame per unique step.

    build_job stores the unique ascending schedule and run_job dedups on
    its own too, so a hand-built archive with duplicates yields the same
    frames/sample_steps contract as the packed job.
    """
    job = fdtd_gpu_remote.build_job(
        343.0, _DX, shape=(_NY, _NX), steps=100, sample_steps=[100, 0, 50, 50, 0, 100]
    )
    np.testing.assert_array_equal(job["sample_steps"], [0, 50, 100])
    job["sample_steps"] = np.asarray([100, 0, 50, 50, 0, 100], dtype=np.int64)
    result = job_runner.run_job(job)
    np.testing.assert_array_equal(result["sample_steps"], [0, 50, 100])
    assert np.asarray(result["frames"]).shape[0] == 3


def test_submit_falls_back_to_local_numpy_run(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A reachable remote whose run fails degrades to a local NumPy run."""
    config = fdtd_gpu_remote.RemoteConfig(
        host="203.0.113.9",
        user="gpuuser",
        name="test GPU",
        image="cupy/cupy:v13.6.0",
        workdir="/tmp/phonometry-gpu",
    )
    monkeypatch.setattr(fdtd_gpu_remote, "remote_available", lambda config: True)

    def _boom(
        job: dict[str, Any],
        config: fdtd_gpu_remote.RemoteConfig,
        timeout: float = 0.0,
    ) -> dict[str, Any]:
        msg = "docker run failed"
        raise fdtd_gpu_remote.RemoteRunError(msg)

    monkeypatch.setattr(fdtd_gpu_remote, "run_remote", _boom)
    monkeypatch.setattr(job_runner, "_pick_backend", lambda: (np, "numpy"))
    job = fdtd_gpu_remote.build_job(
        343.0, _DX, shape=(20, 24), steps=10, sample_steps=[0, 10]
    )
    result = fdtd_gpu_remote.submit(job, config)
    assert result["backend"] == "numpy"
    assert int(result["steps"]) == 10
    assert np.asarray(result["frames"]).shape == (2, 20, 24)
    err = capsys.readouterr().err
    assert "docker run failed" in err
    assert "falling back to a local NumPy run" in err


def test_load_env_real_environment_wins(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """An exported variable beats the .env file; missing ones are loaded."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        '# comment line\nPHONO_GPU_HOST=file-host\nPHONO_GPU_NAME="lab GPU"\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("PHONO_GPU_HOST", "env-host")
    # Guarantee the variable is absent and restored either way.
    monkeypatch.setenv("PHONO_GPU_NAME", "sentinel")
    monkeypatch.delenv("PHONO_GPU_NAME")
    values = fdtd_gpu_remote.load_env(env_file)
    assert values == {"PHONO_GPU_HOST": "file-host", "PHONO_GPU_NAME": "lab GPU"}
    assert os.environ["PHONO_GPU_HOST"] == "env-host"  # real env wins
    assert os.environ["PHONO_GPU_NAME"] == "lab GPU"  # quotes stripped


def _remote_frames(
    kwargs: dict[str, Any], wave: dict[str, Any], direction: str
) -> list[np.ndarray]:
    """The same scenario, stepped on the remote GPU, frame by frame.

    ``run_remote`` rather than ``submit``: submitting falls back to a local
    NumPy run when anything goes wrong, which for a render is the right call
    and for a test is the wrong one. A silent fallback here would compare
    NumPy against NumPy and pass while proving nothing about the GPU.
    """
    c, rest = _split_c(kwargs)
    job = fdtd_gpu_remote.build_job(
        c,
        _DX,
        shape=(_NY, _NX),
        steps=_STEPS,
        sample_steps=[50, 100, 150, 200],
        plane_waves=[{"direction": direction, **wave}],
        **rest,
    )
    result = fdtd_gpu_remote.run_remote(job, _REMOTE, timeout=_REMOTE_TIMEOUT_S)
    # The backend the job actually ran on is the whole point of the exercise:
    # the runner picks NumPy when CuPy is missing on the far side, and that
    # result would satisfy every tolerance below without touching a GPU.
    assert result["backend"] == "cupy"
    assert int(result["cells"]) == _NY * _NX
    return list(np.asarray(result["frames"]))


@_needs_remote
@pytest.mark.parametrize("direction", list(_WAVES))
def test_plane_wave_directions_match_library_on_the_remote_gpu(direction: str) -> None:
    """A plane packet in each direction reproduces the library on the GPU."""
    wave = _WAVES[direction]
    fields = _reference({}, wave, direction)
    _assert_parity(fields, _remote_frames({}, wave, direction), _GPU_TOL)


@_needs_remote
@pytest.mark.parametrize("scenario", list(_scenarios()))
def test_scenarios_match_library_on_the_remote_gpu(scenario: str) -> None:
    """Each engine feature reproduces the library on the GPU."""
    kwargs = _scenarios()[scenario]
    wave = {"center": 0.15, "width": 0.06, "wavelength": 0.09}
    fields = _reference(kwargs, wave, "down")
    _assert_parity(fields, _remote_frames(kwargs, wave, "down"), _GPU_TOL)


# --- Sustained sources and the three reductions of the runner ----------------
#
# What the animation scenes need beyond a plane-wave initial condition: a
# drive that keeps injecting, and the accumulations they take off every
# step. Both are described in the job (a callable cannot be packed into an
# archive), so what is under test is that the description reproduces the
# library object it stands for, and that a reduction computed on the device
# equals the loop the scene used to run here.

#: Drive frequency of the source cases: fast enough to be several periods
#: into the run at :data:`_STEPS`, slow enough to be resolved by the mesh.
_SOURCE_F = 900.0

#: One Gaussian width, in steps of the reference engine's own time step.
_PULSE_WIDTH_S = 8.0e-5


def _source_cases() -> dict[str, tuple[list[dict[str, Any]], list[Any]]]:
    """Each sustained source, as the job describes it and as the library builds it."""
    return {
        "point_cw": (
            [fdtd_dispatch.point(20, 30, fdtd_dispatch.cw(_SOURCE_F, 0.7, 2.0))],
            [
                CWSource(
                    ix=20, iy=30, frequency=_SOURCE_F, amplitude=0.7, ramp_cycles=2.0
                )
            ],
        ),
        "point_gaussian": (
            [fdtd_dispatch.point(44, 18, fdtd_dispatch.gaussian(_PULSE_WIDTH_S))],
            [GaussianPulse(ix=44, iy=18, half_width_s=_PULSE_WIDTH_S)],
        ),
        "point_gaussian_shifted": (
            [
                fdtd_dispatch.point(
                    30, 30, fdtd_dispatch.gaussian(_PULSE_WIDTH_S, 5.0e-4, 0.4)
                )
            ],
            [
                GaussianPulse(
                    ix=30, iy=30, half_width_s=_PULSE_WIDTH_S, t0=5.0e-4, amplitude=0.4
                )
            ],
        ),
        "plane_cw": (
            [fdtd_dispatch.plane("right", fdtd_dispatch.cw(_SOURCE_F), offset=2)],
            [
                PlaneWaveSource(
                    "right", CWSource(0, 0, frequency=_SOURCE_F).value, offset=2
                )
            ],
        ),
        "plane_scaled": (
            [
                fdtd_dispatch.plane(
                    "down", fdtd_dispatch.cw(_SOURCE_F), offset=3, amplitude=0.5
                )
            ],
            [
                PlaneWaveSource(
                    "down",
                    CWSource(0, 0, frequency=_SOURCE_F).value,
                    offset=3,
                    amplitude=0.5,
                )
            ],
        ),
        "two_points": (
            [
                fdtd_dispatch.point(20, 20, fdtd_dispatch.cw(_SOURCE_F)),
                fdtd_dispatch.point(40, 40, fdtd_dispatch.cw(_SOURCE_F, -1.0)),
            ],
            [
                CWSource(ix=20, iy=20, frequency=_SOURCE_F),
                CWSource(ix=40, iy=40, frequency=_SOURCE_F, amplitude=-1.0),
            ],
        ),
    }


def _driven_reference(sources: list[Any], steps: int = _STEPS) -> FDTD2D:
    """The library engine driven by *sources*, stepped *steps* times."""
    ref = FDTD2D(343.0, _DX, shape=(_NY, _NX))
    for source in sources:
        ref.add_source(source)
    for _ in range(steps):
        ref.step()
    return ref


@pytest.mark.parametrize("case", list(_source_cases()))
def test_described_sources_match_the_library_objects(case: str) -> None:
    """A source packed as data drives exactly what the library object does."""
    described, built = _source_cases()[case]
    ref = _driven_reference(built)
    job = fdtd_gpu_remote.build_job(
        343.0,
        _DX,
        shape=(_NY, _NX),
        steps=_STEPS,
        sample_steps=[_STEPS],
        sources=described,
    )
    result = job_runner.run_job(job)
    assert float(np.max(np.abs(ref.p))) > 1e-6  # the drive reached the grid
    assert np.array_equal(np.asarray(result["frames"])[0], ref.p)


@_needs_remote
@pytest.mark.parametrize("case", list(_source_cases()))
def test_described_sources_match_the_library_on_the_remote_gpu(case: str) -> None:
    """The same drives, injected on the GPU."""
    described, built = _source_cases()[case]
    ref = _driven_reference(built)
    job = fdtd_gpu_remote.build_job(
        343.0,
        _DX,
        shape=(_NY, _NX),
        steps=_STEPS,
        sample_steps=[_STEPS],
        sources=described,
    )
    result = fdtd_gpu_remote.run_remote(job, _REMOTE, timeout=_REMOTE_TIMEOUT_S)
    assert result["backend"] == "cupy"
    _assert_parity([ref.p], list(np.asarray(result["frames"])), _GPU_TOL)


def test_waveform_value_rejects_an_unknown_type() -> None:
    """A waveform nobody implements fails where it is described."""
    with pytest.raises(ValueError, match=r"unknown waveform type 'square'"):
        fdtd_gpu.waveform_value({"type": "square", "frequency": 1.0}, 0.0)


def test_check_waveform_rejects_what_the_engine_cannot_drive() -> None:
    """The parameters are checked once, at registration, not every step.

    ``waveform_value`` runs inside the stepping loop, so it reads the
    parameters and does not police them. A NaN amplitude or a negative ramp
    would otherwise reach the field and poison it from the first step.
    """
    with pytest.raises(ValueError, match=r"unknown waveform type 'square'"):
        fdtd_gpu.check_waveform({"type": "square"})
    with pytest.raises(ValueError, match=r"amplitude must be finite"):
        fdtd_gpu.check_waveform({"type": "cw", "frequency": 1.0, "amplitude": np.nan})
    with pytest.raises(ValueError, match=r"frequency must be finite"):
        fdtd_gpu.check_waveform({"type": "cw", "frequency": np.inf})
    with pytest.raises(ValueError, match=r"frequency must be positive"):
        fdtd_gpu.check_waveform({"type": "cw", "frequency": 0.0})
    with pytest.raises(ValueError, match=r"ramp_cycles must be non-negative"):
        fdtd_gpu.check_waveform({"type": "cw", "frequency": 1.0, "ramp_cycles": -1.0})
    with pytest.raises(ValueError, match=r"width must be positive"):
        fdtd_gpu.check_waveform({"type": "gaussian", "width": 0.0})
    with pytest.raises(ValueError, match=r"t0 must be finite"):
        fdtd_gpu.check_waveform({"type": "gaussian", "width": 1e-4, "t0": np.nan})


def test_sources_are_checked_where_they_are_registered() -> None:
    """Both the engine and the packer refuse the same waveform."""
    sim = fdtd_gpu.GpuFDTD2D(343.0, _DX, shape=(_NY, _NX))
    bad = {"type": "cw", "frequency": _SOURCE_F, "ramp_cycles": -2.0}
    described = [fdtd_dispatch.point(10, 10, bad)]
    with pytest.raises(ValueError, match=r"ramp_cycles must be non-negative"):
        sim.add_point_source(10, 10, bad)
    with pytest.raises(ValueError, match=r"ramp_cycles must be non-negative"):
        sim.add_plane_source("down", bad)
    with pytest.raises(ValueError, match=r"ramp_cycles must be non-negative"):
        fdtd_gpu_remote.build_job(
            343.0,
            _DX,
            shape=(_NY, _NX),
            steps=100,
            sample_steps=[50],
            sources=described,
        )


def test_reduction_bounds_must_be_integers() -> None:
    """A bound that survives JSON as a string would fail mid-run instead.

    The runner compares the window against a step counter, so a spec built
    from parsed text has to be refused (or normalised) at packing time.
    """
    ok: dict[str, Any] = {"shape": (_NY, _NX), "steps": 100, "sample_steps": [50]}
    with pytest.raises(ValueError, match=r"mean_squares\[0\].start must be an integer"):
        fdtd_gpu_remote.build_job(
            343.0, _DX, mean_squares=[{"name": "s", "start": "0", "stop": 100}], **ok
        )
    line = {"name": "axis", "row": 0, "from": 0, "to": _NX, "start": 0, "stop": 100}
    with pytest.raises(ValueError, match=r"envelopes\[0\].row must be an integer"):
        fdtd_gpu_remote.build_job(343.0, _DX, envelopes=[{**line, "row": 1.5}], **ok)
    with pytest.raises(ValueError, match=r"envelopes\[0\].to must be an integer"):
        fdtd_gpu_remote.build_job(343.0, _DX, envelopes=[{**line, "to": "80"}], **ok)
    packed = fdtd_gpu_remote.build_job(
        343.0,
        _DX,
        envelopes=[{**line, "row": np.int64(3)}],
        mean_squares=[{"name": "s", "start": np.int64(0), "stop": np.int64(100)}],
        **ok,
    )
    stored = json.loads(str(packed["envelopes"]))[0]
    assert isinstance(stored["row"], int)
    assert json.loads(str(packed["mean_squares"]))[0]["stop"] == 100


def test_build_job_rejects_a_malformed_source() -> None:
    """A source off the grid, or with no waveform, fails at packing time."""
    ok: dict[str, Any] = {"shape": (_NY, _NX), "steps": 100, "sample_steps": [50]}
    with pytest.raises(ValueError, match=r"sources\[0\] needs a 'waveform' dict"):
        fdtd_gpu_remote.build_job(
            343.0, _DX, sources=[{"kind": "point", "ix": 1, "iy": 1}], **ok
        )
    off_grid = [fdtd_dispatch.point(_NX, 1, fdtd_dispatch.cw(_SOURCE_F))]
    with pytest.raises(ValueError, match=r"sources\[0\] drives cell \(1, 80\)"):
        fdtd_gpu_remote.build_job(343.0, _DX, sources=off_grid, **ok)
    sideways = [fdtd_dispatch.plane("sideways", fdtd_dispatch.cw(_SOURCE_F))]
    with pytest.raises(ValueError, match=r"sources\[0\] travels 'sideways'"):
        fdtd_gpu_remote.build_job(343.0, _DX, sources=sideways, **ok)
    unknown = [{"kind": "spiral", "waveform": fdtd_dispatch.cw(_SOURCE_F)}]
    with pytest.raises(ValueError, match=r"sources\[0\] kind 'spiral'"):
        fdtd_gpu_remote.build_job(343.0, _DX, sources=unknown, **ok)


def test_packed_sources_are_the_records_the_engine_takes() -> None:
    """What is serialised is normalised, not merely approved.

    JSON carries a NaN amplitude and a float cell index intact, and both
    would only be refused on the far side, after the transfer. The packer
    runs the engine's own helpers over each source and stores what they
    return, so the archive holds integers and finite amplitudes or the
    packing fails here.
    """
    ok: dict[str, Any] = {"shape": (_NY, _NX), "steps": 100, "sample_steps": [50]}
    wave = fdtd_dispatch.cw(_SOURCE_F)
    with pytest.raises(ValueError, match=r"sources\[0\] ix must be an integer"):
        fdtd_gpu_remote.build_job(
            343.0,
            _DX,
            sources=[{"kind": "point", "ix": 1.5, "iy": 1, "waveform": wave}],
            **ok,
        )
    nan_amplitude = [
        {
            "kind": "plane",
            "direction": "down",
            "offset": 0,
            "amplitude": float("nan"),
            "waveform": wave,
        }
    ]
    with pytest.raises(ValueError, match=r"sources\[0\] amplitude must be finite"):
        fdtd_gpu_remote.build_job(343.0, _DX, sources=nan_amplitude, **ok)
    packed = fdtd_gpu_remote.build_job(
        343.0,
        _DX,
        sources=[
            {"kind": "point", "ix": np.int64(10), "iy": np.int64(20), "waveform": wave},
            {
                "kind": "plane",
                "direction": "down",
                "offset": np.int64(2),
                "amplitude": np.float64(0.5),
                "waveform": wave,
            },
        ],
        **ok,
    )
    stored = json.loads(str(packed["sources"]))
    assert isinstance(stored[0]["ix"], int)
    assert stored[0]["iy"] == 20
    assert isinstance(stored[1]["offset"], int)
    assert stored[1]["amplitude"] == 0.5


def test_a_registered_waveform_is_a_snapshot() -> None:
    """Editing the mapping after registration cannot reach the stepping loop.

    ``check_waveform`` runs once, where the source is added; if the engine
    kept the caller's mapping, a later edit would drive the grid with
    parameters no check has ever seen.
    """
    live: dict[str, Any] = dict(fdtd_dispatch.cw(_SOURCE_F))
    sim = fdtd_gpu.GpuFDTD2D(343.0, _DX, shape=(_NY, _NX))
    sim.add_point_source(10, 20, live)
    sim.add_plane_source("down", live, offset=1)
    live["amplitude"] = float("nan")
    live["type"] = "spiral"
    for _ in range(20):
        sim.step()
    assert np.all(np.isfinite(np.asarray(sim.p)))
    assert float(np.max(np.abs(np.asarray(sim.p)))) > 0.0


def _reduction_job(**extra: Any) -> dict[str, Any]:
    """A driven job asking for whatever reduction *extra* names."""
    described, _ = _source_cases()["point_cw"]
    return fdtd_gpu_remote.build_job(
        343.0,
        _DX,
        shape=(_NY, _NX),
        steps=_STEPS,
        sample_steps=[100, _STEPS],
        sources=described,
        **extra,
    )


def _reduction_reference(
    beta: float, window: tuple[int, int], row: int
) -> dict[str, Any]:
    """The three accumulations, run the way a scene used to run them here."""
    _, built = _source_cases()["point_cw"]
    ref = FDTD2D(343.0, _DX, shape=(_NY, _NX))
    for source in built:
        ref.add_source(source)
    ms = np.zeros_like(ref.p)
    acc = np.zeros_like(ref.p)
    peak = np.zeros(_NX)
    frames = {}
    for i in range(_STEPS):
        ref.step()
        step = i + 1
        ms = beta * ms + (1.0 - beta) * ref.p**2
        if window[0] < step <= window[1]:
            acc += ref.p**2
            np.maximum(peak, np.abs(ref.p[row, :]), out=peak)
        if step in (100, _STEPS):
            frames[step] = np.sqrt(ms)
    return {
        "rms_frames": np.stack([frames[100], frames[_STEPS]]),
        "rms_final": np.sqrt(ms),
        "mean_square": np.sqrt(acc / (window[1] - window[0])),
        "envelope": peak,
    }


def test_running_mean_square_matches_the_scene_loop() -> None:
    """rms_beta reproduces the one-pole average the capture used to keep."""
    beta = 0.97
    expected = _reduction_reference(beta, (0, _STEPS), 0)
    result = job_runner.run_job(_reduction_job(rms_beta=beta))
    assert np.array_equal(result["rms_frames"], expected["rms_frames"])
    assert np.array_equal(result["rms_final"], expected["rms_final"])


def test_envelope_and_mean_square_windows_match_the_scene_loop() -> None:
    """The two windowed reductions equal the loops they replace."""
    window, row = (120, _STEPS), 30
    expected = _reduction_reference(0.0, window, row)
    result = job_runner.run_job(
        _reduction_job(
            envelopes=[
                {
                    "name": "axis",
                    "row": row,
                    "from": 0,
                    "to": _NX,
                    "start": window[0],
                    "stop": window[1],
                }
            ],
            mean_squares=[{"name": "settled", "start": window[0], "stop": window[1]}],
        )
    )
    assert np.array_equal(result["envelope_axis"], expected["envelope"])
    assert np.array_equal(result["mean_square_settled"], expected["mean_square"])


@_needs_remote
def test_reductions_match_the_scene_loop_on_the_remote_gpu() -> None:
    """The same three accumulations, computed on the device."""
    beta, window, row = 0.97, (120, _STEPS), 30
    expected = _reduction_reference(beta, window, row)
    job = _reduction_job(
        rms_beta=beta,
        envelopes=[
            {
                "name": "axis",
                "row": row,
                "from": 0,
                "to": _NX,
                "start": window[0],
                "stop": window[1],
            }
        ],
        mean_squares=[{"name": "settled", "start": window[0], "stop": window[1]}],
    )
    result = fdtd_gpu_remote.run_remote(job, _REMOTE, timeout=_REMOTE_TIMEOUT_S)
    assert result["backend"] == "cupy"
    peak = float(np.max(expected["rms_final"]))
    for key, ref in (
        ("rms_final", expected["rms_final"]),
        ("mean_square_settled", expected["mean_square"]),
        ("envelope_axis", expected["envelope"]),
    ):
        np.testing.assert_allclose(result[key], ref, rtol=0.0, atol=_GPU_TOL * peak)


def test_build_job_rejects_a_malformed_reduction() -> None:
    """An unusable reduction fails at packing time, not on the far side."""
    ok: dict[str, Any] = {"shape": (_NY, _NX), "steps": 100, "sample_steps": [50]}
    line = {"name": "axis", "row": 0, "from": 0, "to": _NX, "start": 0, "stop": 100}
    with pytest.raises(ValueError, match=r"rms_beta must lie in \[0, 1\)"):
        fdtd_gpu_remote.build_job(343.0, _DX, rms_beta=1.0, **ok)
    with pytest.raises(ValueError, match=r"envelopes\[1\] needs a 'name'"):
        fdtd_gpu_remote.build_job(343.0, _DX, envelopes=[line, dict(line)], **ok)
    with pytest.raises(ValueError, match=r"envelopes\[0\] takes exactly one"):
        fdtd_gpu_remote.build_job(343.0, _DX, envelopes=[{**line, "column": 3}], **ok)
    with pytest.raises(ValueError, match=r"envelopes\[0\] sits at 60, off a grid"):
        fdtd_gpu_remote.build_job(343.0, _DX, envelopes=[{**line, "row": _NY}], **ok)
    with pytest.raises(ValueError, match=r"envelopes\[0\] spans \[0, 200\)"):
        fdtd_gpu_remote.build_job(343.0, _DX, envelopes=[{**line, "to": 200}], **ok)
    with pytest.raises(ValueError, match=r"envelopes\[0\] accumulates over steps"):
        fdtd_gpu_remote.build_job(343.0, _DX, envelopes=[{**line, "stop": 101}], **ok)
    with pytest.raises(ValueError, match=r"mean_squares\[0\] accumulates over steps"):
        fdtd_gpu_remote.build_job(
            343.0, _DX, mean_squares=[{"name": "s", "start": 50, "stop": 50}], **ok
        )
    with pytest.raises(ValueError, match=r"mean_squares\[0\] needs a 'name'"):
        fdtd_gpu_remote.build_job(
            343.0, _DX, mean_squares=[{"name": "", "start": 0, "stop": 100}], **ok
        )


# --- The dispatch layer the scenes speak ------------------------------------


def test_scene_time_step_is_the_engines_own() -> None:
    """Scene.dt is known before anything is allocated, and it is exact."""
    c_map = np.full((_NY, _NX), 343.0)
    c_map[:10, :] = 1500.0  # the fastest cell sets the step
    scene = fdtd_dispatch.Scene(c_map, _DX, cfl=0.5)
    ref = FDTD2D(c_map, _DX, cfl=0.5)
    assert scene.dt == ref.dt


def test_scene_with_sources_keeps_the_geometry() -> None:
    """with_sources swaps the drive and nothing else."""
    mask = np.zeros((_NY, _NX), dtype=np.bool_)
    mask[10:12, 20:60] = True
    scene = fdtd_dispatch.Scene(
        343.0,
        _DX,
        shape=(_NY, _NX),
        sponge_width=6,
        sponge_sides=("left", "right"),
        obstacle_mask=mask,
        edge_impedance={"top": 413.0},
        sources=(fdtd_dispatch.point(10, 10, fdtd_dispatch.cw(_SOURCE_F)),),
    )
    other = scene.with_sources(fdtd_dispatch.point(20, 20, fdtd_dispatch.cw(500.0)))
    assert other.sources[0]["ix"] == 20
    assert other.sources[0]["waveform"]["frequency"] == 500.0
    assert other.shape == scene.shape
    assert other.sponge_sides == scene.sponge_sides
    assert other.edge_impedance == scene.edge_impedance
    assert other.obstacle_mask is scene.obstacle_mask
    assert other.dt == scene.dt


def test_dispatch_run_reproduces_the_library_run() -> None:
    """A scene run through the dispatcher is the library engine, driven."""
    described, built = _source_cases()["point_cw"]
    ref = _driven_reference(built)
    scene = fdtd_dispatch.Scene(343.0, _DX, shape=(_NY, _NX), sources=tuple(described))
    result = fdtd_dispatch.run(
        scene,
        steps=_STEPS,
        sample_steps=[_STEPS],
        sample_dtype="float64",
        timeout=_REMOTE_TIMEOUT_S,
    )
    np.testing.assert_allclose(
        np.asarray(result["frames"])[0],
        ref.p,
        rtol=0.0,
        atol=_GPU_TOL * float(np.max(np.abs(ref.p))),
    )
