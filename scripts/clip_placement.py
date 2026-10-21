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
"""

from __future__ import annotations

import os
import pathlib
import sys
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
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
