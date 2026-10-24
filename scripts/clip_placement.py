#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Where a clip's wave field is computed: on NumPy here, or on a GPU.

Each clip that steps an FDTD engine has its device recorded in
``figures.registry._ANIM_DEVICES``, measured once per clip: a small grid
steps faster on NumPy than it can be sent to a GPU and back, a large one is
the reverse. ``PHONOMETRY_COMPUTE`` names the GPU this machine has, or the
one of the node a render was sent to; with none named, every clip steps on
NumPy and only takes longer. A clip's GPU is a CuPy one: the engines'
stepping is bit for bit NumPy's there (the CuPy proof in
``gpu-parity.lock``), and each GPU clip's field was measured against its
NumPy field, the scene's own device arithmetic included. Its index is 0;
another GPU is chosen with ``CUDA_VISIBLE_DEVICES``, because a scene's own
arithmetic runs on CuPy's current device. The clips are always computed in
float64.

This module sits outside the figures package on purpose: it decides where a
field is computed, not what the field is or how it is drawn, so neither it
nor the device table enters a clip's fingerprint (``animation_fingerprint``).
The registry is read when a scene asks, not when this module is imported,
because the scenes are imported by the registry.

It also says how a GPU and the RAM are shared when clips render side by
side, on a node (``scripts/clip_node.py``) or on this machine's GPU
(``figures.registry``): two at a time, each with half of what is free when
the render starts, and a clip whose recorded needs do not fit half runs
alone.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from collections.abc import Callable

    from phonometry.simulation import Compute

#: Where a clip's field is computed: ``"cpu"`` on NumPy; ``"gpu"`` on the GPU
#: ``PHONOMETRY_COMPUTE`` names, sharing it with one other render lane;
#: ``"gpu-whole"`` on that GPU with all the memory free on it, alone on the node.
ClipDevice = Literal["cpu", "gpu", "gpu-whole"]

#: The bytes of GPU memory a render lane may hold. The node sets it for each
#: lane (``scripts/clip_node.py``); unset, CuPy's pool is left unbounded.
GPU_BYTES_ENV = "PHONOMETRY_CLIP_GPU_BYTES"

#: The bytes of RAM a render lane may hold. The node sets it for each lane;
#: unset, a render takes what this machine has available (:func:`host_bytes`).
HOST_BYTES_ENV = "PHONOMETRY_CLIP_HOST_BYTES"

#: Where Linux says how much RAM is available, and where a container's own
#: limit is (cgroup v2); module names so a test can point them elsewhere.
_MEMINFO = pathlib.Path("/proc/meminfo")
_CGROUP_LIMIT = pathlib.Path("/sys/fs/cgroup/memory.max")


def device_of(clip: str) -> ClipDevice:
    """The device recorded for *clip*.

    :raises KeyError: for a clip with no recorded device.
    """
    from figures.registry import _ANIM_DEVICES

    if clip not in _ANIM_DEVICES:
        msg = f"{clip} has no device in figures.registry._ANIM_DEVICES"
        raise KeyError(msg)
    return _ANIM_DEVICES[clip]


def compute_for(clip: str) -> Compute:
    """The placement *clip*'s field steps on, in float64.

    :raises KeyError: for a clip with no recorded device.
    :raises ValueError: when ``PHONOMETRY_COMPUTE`` is malformed, asks for
        float32, names a GPU library other than CuPy or a GPU other than the
        first, or when the lane budget is not a positive count of bytes.
    """
    from phonometry.simulation import Compute
    from phonometry.simulation.compute import _requested

    if device_of(clip) == "cpu":
        return Compute(device="cpu")
    ambient = _requested(None)
    if ambient.device not in ("cpu", "cupy"):
        msg = (
            f"PHONOMETRY_COMPUTE names {ambient.device!r}; a clip steps on NumPy "
            "or CuPy, the GPU its field was measured on"
        )
        raise ValueError(msg)
    if ambient.dtype != "float64":
        msg = (
            f"PHONOMETRY_COMPUTE asks for {ambient.dtype}; the clips are "
            "computed in float64"
        )
        raise ValueError(msg)
    if ambient.device == "cpu":
        return Compute(device="cpu")
    if ambient.device_index:
        msg = (
            f"PHONOMETRY_COMPUTE names GPU {ambient.device_index}; the clips step "
            "on GPU 0, so choose that GPU with "
            f"CUDA_VISIBLE_DEVICES={ambient.device_index} and name cupy"
        )
        raise ValueError(msg)
    limit_device_memory(ambient)
    return ambient


def limit_device_memory(compute: Compute) -> None:
    """Hold CuPy's memory pool on *compute*'s GPU to this lane's budget.

    :raises ValueError: when ``PHONOMETRY_CLIP_GPU_BYTES`` is set to anything
        but a positive count of bytes.
    """
    text = os.environ.get(GPU_BYTES_ENV, "").strip()
    if not text or compute.device != "cupy":
        return
    budget = _positive_bytes(GPU_BYTES_ENV, text)
    import cupy

    with cupy.cuda.Device(compute.device_index):
        cupy.get_default_memory_pool().set_limit(size=budget)


def _positive_bytes(name: str, text: str) -> int:
    """The count of bytes *text* gives the variable *name*.

    :raises ValueError: when *text* is not a positive whole number.
    """
    try:
        count = int(text)
    except ValueError:
        count = 0
    if count <= 0:
        msg = f"{name} must be a positive number of bytes; got {text!r}"
        raise ValueError(msg)
    return count


def _available_bytes() -> int | None:
    """``MemAvailable``, capped by a container's own limit; None off Linux."""
    if not _MEMINFO.exists():
        return None
    available: int | None = None
    for line in _MEMINFO.read_text(encoding="utf-8").splitlines():
        if line.startswith("MemAvailable:"):
            available = int(line.split()[1]) * 1024
    if available is None:
        return None
    if _CGROUP_LIMIT.exists():
        limit = _CGROUP_LIMIT.read_text(encoding="utf-8").strip()
        if limit.isdigit():
            available = min(available, int(limit))
    return available


def host_bytes() -> int | None:
    """The RAM this render may hold: its lane's budget, else what is available.

    A node gives each lane a share of the RAM it has free
    (``PHONOMETRY_CLIP_HOST_BYTES``); elsewhere the render may take what this
    machine has available, within a container's limit when there is one.
    None when neither can be read, off Linux.

    :raises ValueError: when ``PHONOMETRY_CLIP_HOST_BYTES`` is set to anything
        but a positive count of bytes.
    """
    text = os.environ.get(HOST_BYTES_ENV, "").strip()
    if text:
        return _positive_bytes(HOST_BYTES_ENV, text)
    return _available_bytes()


def release_device() -> None:
    """Give CuPy's pooled blocks back, when CuPy is loaded in this process.

    A field builder returns host arrays; the device arrays it stepped are
    garbage by then, but CuPy keeps their blocks in its pools. The renderer
    calls this after a field is computed and before the four variants of the
    clip fork, so no child inherits a claim on them.
    """
    cupy = sys.modules.get("cupy")
    if cupy is None:
        return
    cupy.get_default_memory_pool().free_all_blocks()
    cupy.get_default_pinned_memory_pool().free_all_blocks()


#: Clips rendered at once on one GPU: a node's lanes, or the workers of a
#: render on this machine's GPU.
LANES = 2

#: Room left beside each lane's pool for its CUDA context, which CuPy's pool
#: limit does not count: about a hundred MiB on the node's RTX 4060, with
#: room for a driver that takes more.
CONTEXT_BYTES = 256 << 20

#: How long CuPy may take to say how much memory is free on a GPU [s]: an
#: import and a CUDA context, long past what either takes on a working card.
_FREE_GPU_PROBE_S = 120


def _share(free: int, *, alone: bool) -> int:
    return free if alone else free // LANES


def gpu_budget(free: int, *, alone: bool) -> int:
    """The bytes one lane's CuPy pool may hold, of *free* on its GPU.

    Half of what is free when the render starts, or all of it for a clip
    that runs alone, less the room for the lane's CUDA context. What other
    processes hold is never the lanes' to take.
    """
    return _share(free, alone=alone) - CONTEXT_BYTES


def host_share(available: int, *, alone: bool) -> int:
    """The bytes of RAM one lane may hold, of *available*: half, or all of it alone."""
    return _share(available, alone=alone)


def free_gpu_bytes(index: int = 0, *, run: Callable[..., Any] = subprocess.run) -> int:
    """The memory free on CUDA GPU *index*, asked of CuPy in a process of its own.

    So the asking process never holds a CUDA context while the lanes, or the
    pool workers of a render here, need the card.

    :raises subprocess.CalledProcessError: when CuPy cannot say (not
        installed, no GPU, a CUDA error).
    :raises subprocess.TimeoutExpired: when it does not answer in time.
    :raises ValueError: when its answer is not a count of bytes.
    """
    probe = f"import cupy; print(cupy.cuda.Device({index}).mem_info[0])"
    out = run(
        [sys.executable, "-c", probe],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=True,
        timeout=_FREE_GPU_PROBE_S,
    ).stdout
    words = str(out).split()
    if not words or not words[-1].isdigit():
        msg = f"CuPy did not name the free memory of GPU {index}: {str(out).strip()!r}"
        raise ValueError(msg)
    return int(words[-1])


def lane_fit(
    clip: str,
    device: ClipDevice,
    *,
    gpu_need: int,
    host_need: int,
    free_gpu: int,
    available: int | None,
) -> tuple[bool, list[str]]:
    """Whether *clip* runs alone, and why it cannot run at all (empty when it can).

    A clip shares the GPU and the RAM with one other lane when its recorded
    needs fit a lane's share of what is free, runs alone when they fit only
    all of it, and cannot run when they do not fit that either. A
    ``"gpu-whole"`` clip always runs alone. The GPU need counts where the
    clip steps on a GPU; with no GPU free to share (no GPU named) a GPU clip
    steps on NumPy, and its RAM need counts instead, which is what its field
    takes on NumPy. With the RAM unknown (off Linux), the RAM need does not.
    """
    alone = device == "gpu-whole"
    reasons: list[str] = []
    on_gpu = device != "cpu" and free_gpu > 0
    if on_gpu:
        need = max(gpu_need, 1)
        if need > gpu_budget(free_gpu, alone=True):
            reasons.append(
                f"{clip} needs {need >> 20} MiB of GPU memory; {free_gpu >> 20} MiB is free on the GPU"
            )
        alone = alone or need > gpu_budget(free_gpu, alone=False)
    if host_need > 0 and available is not None and not on_gpu:
        if host_need > available:
            reasons.append(
                f"{clip} needs {host_need >> 20} MiB of RAM; {available >> 20} MiB is available"
            )
        alone = alone or host_need > host_share(available, alone=False)
    return alone, reasons
