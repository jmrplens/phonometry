#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Executable payload of the remote GPU FDTD runner.

Runs inside the CuPy container (or on any plain Python with NumPy): loads a
job archive produced by ``fdtd_gpu_remote.py``, builds the backend-agnostic
:class:`fdtd_gpu.GpuFDTD2D` engine on CuPy when a GPU is reachable (NumPy
otherwise), steps the simulation and writes the requested pressure frames
back to a result archive.

Usage: ``python3 job_runner.py <job.npz> <frames.npz>``.

Job archive keys (all produced by ``fdtd_gpu_remote.build_job``):

* ``c``, ``rho``: float64 ``(ny, nx)`` maps.
* ``dx``, ``cfl``, ``sponge_reflection``: scalars.
* ``sponge_width``: int scalar; ``sponge_sides``: array of side names.
* ``damping``: scalar or ``(ny, nx)`` map.
* ``edge_sides``: array of side names; per side an ``edge_z_<side>`` array.
* ``obstacle``: boolean ``(ny, nx)`` map (all-False when unused).
* ``plane_waves``: JSON string, list of ``add_plane_wave`` keyword dicts,
  which lay down an *initial* front rather than driving one.
* ``sources``: JSON string, list of the *sustained* sources, each
  ``{"kind": "point", "ix", "iy", "waveform"}`` or ``{"kind": "plane",
  "direction", "offset", "amplitude", "waveform"}``. The waveform is the
  parameter dict ``fdtd_gpu.waveform_value`` reads, because a job archive
  cannot carry the callable the library's own source classes take. Absent
  in an archive packed before sources existed, which reads as none.
* ``init_scale_x`` (optional): 1D window of length ``nx``, multiplied into
  ``p`` and ``vy`` column-wise after the plane waves (``vx`` untouched).
* ``steps``: total leapfrog steps; ``sample_steps``: step counts at which
  the pressure field is recorded (0 records the initial state). The runner
  sorts them and drops duplicates, so the result carries one frame per
  unique step.
* ``sample_stride``: spatial subsampling of the recorded frames
  (``frame[::stride, ::stride]``); ``sample_dtype``: dtype of the returned
  frames (``"float64"`` or ``"float32"``). Both are applied on the compute
  device before the host transfer, so they shrink the shipped archive.

* ``rms_beta`` (optional): the pole of a running mean square over the
  squared pressure, updated after each step. Zero or absent switches the
  reduction off; a positive value adds ``rms_frames`` (on the same
  schedule and stride as ``frames``) and ``rms_final`` (the settled map at
  full resolution) to the result.
* ``envelopes`` (optional): JSON string, a list of
  ``{"name", "row"|"column", "from", "to", "start", "stop"}``. Each tracks
  the running maximum of ``|p|`` along one row or column between the
  ``start`` and ``stop`` steps, and comes back as ``envelope_<name>``.
* ``mean_squares`` (optional): JSON string, a list of ``{"name", "start",
  "stop"}``. Each accumulates the squared pressure over the whole grid
  between those steps and comes back as ``mean_square_<name>``, the root
  mean square over the window: the settled level a scene measures once the
  transient is out, without shipping a frame per step.

The three reductions exist so a scene that accumulates over *every* step
can still run remotely: shipping every step back would cost more than the
simulation.

Result archive keys: ``frames`` ``(n_frames, ceil(ny / stride),
ceil(nx / stride))`` in ``sample_dtype``, ``sample_steps``,
``sample_stride``, ``sample_dtype``, ``backend`` (``"cupy"`` or
``"numpy"``), ``elapsed`` (stepping wall time in seconds,
device-synchronised), ``steps`` and ``cells``, plus the reduction outputs
above when they were asked for.

The file is self-contained next to ``fdtd_gpu.py``; both are copied into
the container work directory, so no package installation is needed.
"""

from __future__ import annotations

import json
import sys
import time
from typing import TYPE_CHECKING, Any

import fdtd_gpu
import numpy as np

if TYPE_CHECKING:
    from collections.abc import Mapping
    from types import ModuleType


def _pick_backend() -> tuple[ModuleType, str]:
    """Return (array module, name): CuPy with a usable GPU, else NumPy."""
    try:
        import cupy

        cupy.cuda.runtime.getDeviceCount()  # raises without a GPU
        cupy.arange(1).sum()  # force a real kernel launch
    except Exception:  # noqa: BLE001 - any CUDA/import failure means CPU
        return np, "numpy"
    return cupy, "cupy"


def _build_engine(job: Mapping[str, Any], xp: ModuleType) -> fdtd_gpu.GpuFDTD2D:
    """Instantiate the engine from the job archive on backend *xp*."""
    damping = job["damping"]
    edge_impedance: dict[str, Any] = {
        str(side): job[f"edge_z_{side}"] for side in job["edge_sides"]
    }
    obstacle = np.asarray(job["obstacle"], dtype=np.bool_)
    sim = fdtd_gpu.GpuFDTD2D(
        np.asarray(job["c"], dtype=np.float64),
        float(job["dx"]),
        xp=xp,
        rho=np.asarray(job["rho"], dtype=np.float64),
        cfl=float(job["cfl"]),
        sponge_width=int(job["sponge_width"]),
        # build_job stores the fully resolved sponge sides, so an empty
        # array is the library's explicit "()" (no sponge sides), never
        # "not given": pass the tuple through and keep None strictly as
        # the never-stored "not given" sentinel.
        sponge_sides=tuple(str(s) for s in job["sponge_sides"]),
        sponge_reflection=float(job["sponge_reflection"]),
        damping=(
            float(damping)
            if damping.ndim == 0
            else np.asarray(damping, dtype=np.float64)
        ),
        edge_impedance=edge_impedance or None,
        obstacle_mask=obstacle if bool(obstacle.any()) else None,
    )
    for spec in json.loads(str(job["sources"]) if "sources" in job else "[]"):
        if spec["kind"] == "point":
            sim.add_point_source(int(spec["ix"]), int(spec["iy"]), spec["waveform"])
        else:
            sim.add_plane_source(
                str(spec["direction"]),
                spec["waveform"],
                offset=int(spec.get("offset", 0)),
                amplitude=float(spec.get("amplitude", 1.0)),
            )
    for spec in json.loads(str(job["plane_waves"])):
        sim.add_plane_wave(
            spec["direction"],
            center=float(spec["center"]),
            width=float(spec["width"]),
            amplitude=float(spec.get("amplitude", 1.0)),
            wavelength=(
                None if spec.get("wavelength") is None else float(spec["wavelength"])
            ),
        )
    if "init_scale_x" in job:
        # Lateral taper of the initial front: column-wise window on the
        # pressure and the y-velocity (vx keeps its (ny, nx - 1) columns).
        w = xp.asarray(np.asarray(job["init_scale_x"], dtype=np.float64)[np.newaxis, :])
        sim.p *= w
        sim.vy *= w
    return sim


def _sample_frame(
    sim: fdtd_gpu.GpuFDTD2D, stride: int, dtype: np.dtype[Any]
) -> np.ndarray:
    """Subsample and cast the pressure on the device, then transfer it."""
    frame = sim.p[::stride, ::stride].astype(dtype, copy=True)
    if hasattr(frame, "get"):  # CuPy device array
        return np.asarray(frame.get())
    return np.asarray(frame)


def _transfer(array: fdtd_gpu.XPArray, dtype: np.dtype[Any]) -> np.ndarray:
    """Cast on the compute device, then bring the result to the host."""
    out = array.astype(dtype, copy=True)
    if hasattr(out, "get"):  # CuPy device array
        return np.asarray(out.get())
    return np.asarray(out)


def _reduction_specs(job: Mapping[str, Any], key: str) -> list[dict[str, Any]]:
    """The reductions of one kind the job asks for, or none.

    :param job: The job dict or loaded archive.
    :param key: ``"envelopes"`` or ``"mean_squares"``.
    """
    if key not in job:
        return []
    specs: list[dict[str, Any]] = json.loads(str(job[key]))
    return specs


def _line(sim: fdtd_gpu.GpuFDTD2D, spec: Mapping[str, Any]) -> fdtd_gpu.XPArray:
    """The 1D slice of the pressure field one envelope tracks."""
    start, stop = int(spec["from"]), int(spec["to"])
    if spec.get("row") is not None:
        return sim.p[int(spec["row"]), start:stop]
    return sim.p[start:stop, int(spec["column"])]


def _span(sim: fdtd_gpu.GpuFDTD2D, spec: Mapping[str, Any]) -> int:
    """How long that slice is."""
    return int(spec["to"]) - int(spec["from"])


def run_job(job: Mapping[str, Any]) -> dict[str, Any]:
    """Run one job dict/archive and return the result payload."""
    xp, backend = _pick_backend()
    sim = _build_engine(job, xp)
    steps = int(job["steps"])
    stride = int(job["sample_stride"]) if "sample_stride" in job else 1
    if stride < 1:
        msg = "sample_stride must be >= 1"
        raise ValueError(msg)
    dtype = np.dtype(str(job["sample_dtype"]) if "sample_dtype" in job else "float64")
    # Deduplicate defensively (build_job already stores unique steps, but
    # the archive may come from elsewhere): ascending order, one recorded
    # frame per reported step, so frames[i] always belongs to
    # sample_steps[i].
    sample_steps = sorted({int(s) for s in np.asarray(job["sample_steps"])})
    wanted = set(sample_steps)
    beta = float(job["rms_beta"]) if "rms_beta" in job else 0.0
    envelopes = _reduction_specs(job, "envelopes")
    squares = _reduction_specs(job, "mean_squares")
    ms = xp.zeros_like(sim.p) if beta > 0.0 else None
    peaks = [xp.zeros(_span(sim, spec), dtype=sim.p.dtype) for spec in envelopes]
    sums = [xp.zeros_like(sim.p) for _ in squares]
    frames: list[np.ndarray] = []
    rms_frames: list[np.ndarray] = []
    if 0 in wanted:
        frames.append(_sample_frame(sim, stride, dtype))
        if ms is not None:
            rms_frames.append(_transfer(xp.sqrt(ms)[::stride, ::stride], dtype))
    if backend == "cupy":
        xp.cuda.Stream.null.synchronize()
    t0 = time.perf_counter()
    for i in range(steps):
        sim.step()
        step = i + 1
        if ms is not None:
            # The running mean square of the library helper, term for term:
            # a one-pole average over the squared pressure, updated after
            # the step and before the frame is taken off it.
            ms *= beta
            ms += (1.0 - beta) * sim.p**2
        for peak, spec in zip(peaks, envelopes, strict=True):
            if spec["start"] < step <= spec["stop"]:
                xp.maximum(peak, xp.abs(_line(sim, spec)), out=peak)
        for acc, spec in zip(sums, squares, strict=True):
            if spec["start"] < step <= spec["stop"]:
                acc += sim.p**2
        if step in wanted:
            frames.append(_sample_frame(sim, stride, dtype))
            if ms is not None:
                rms_frames.append(_transfer(xp.sqrt(ms)[::stride, ::stride], dtype))
    if backend == "cupy":
        xp.cuda.Stream.null.synchronize()
    elapsed = time.perf_counter() - t0
    ny, nx = sim.p.shape
    result: dict[str, Any] = {
        "frames": (np.stack(frames) if frames else np.zeros((0, 0, 0), dtype=dtype)),
        "sample_steps": np.asarray(sample_steps, dtype=np.int64),
        "sample_stride": stride,
        "sample_dtype": str(dtype),
        "backend": backend,
        "elapsed": elapsed,
        "steps": steps,
        "cells": ny * nx,
    }
    if ms is not None:
        result["rms_frames"] = (
            np.stack(rms_frames) if rms_frames else np.zeros((0, 0, 0), dtype=dtype)
        )
        # The settled map at full resolution, which the physics probes read.
        result["rms_final"] = _transfer(xp.sqrt(ms), np.dtype("float64"))
    for peak, spec in zip(peaks, envelopes, strict=True):
        result[f"envelope_{spec['name']}"] = _transfer(peak, np.dtype("float64"))
    for acc, spec in zip(sums, squares, strict=True):
        window = int(spec["stop"]) - int(spec["start"])
        result[f"mean_square_{spec['name']}"] = _transfer(
            xp.sqrt(acc / window), np.dtype("float64")
        )
    return result


def main(argv: list[str]) -> int:
    """CLI entry point: ``job_runner.py <job.npz> <frames.npz>``."""
    if len(argv) != 3:
        print("usage: job_runner.py <job.npz> <frames.npz>", file=sys.stderr)
        return 2
    with np.load(argv[1], allow_pickle=False) as job:
        result = run_job(job)
    # Stored, not deflated: the frames are field data, which zlib shrinks
    # by about a twentieth for tens of seconds of CPU on both ends of the
    # wire. The job archive is compressed (constant maps, huge ratio); the
    # result is not.
    np.savez(argv[2], **result)
    print(
        f"backend={result['backend']} steps={result['steps']} "
        f"cells={result['cells']} elapsed={result['elapsed']:.3f}s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
