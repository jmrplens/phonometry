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

import importlib
import os
import pathlib
import subprocess
import sys
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    import types
    from collections.abc import Callable

    from phonometry.simulation import Compute

#: Where a clip's field is computed: ``"cpu"`` on NumPy; ``"gpu"`` on the GPU
#: ``PHONOMETRY_COMPUTE`` names, sharing it with one other render lane;
#: ``"gpu-whole"`` on that GPU with all the memory free on it, alone on the node.
ClipDevice = Literal["cpu", "gpu", "gpu-whole"]

#: The bytes of GPU memory a render lane may hold. The node sets it for each
#: lane whose clip steps on its GPU (``scripts/clip_node.py``), and a render
#: on this machine's GPU for its workers; unset, CuPy's pool is left
#: unbounded.
GPU_BYTES_ENV = "PHONOMETRY_CLIP_GPU_BYTES"

#: The bytes of RAM a render lane may hold. The node sets it for each lane;
#: unset, a render takes what this machine has available (:func:`host_bytes`).
HOST_BYTES_ENV = "PHONOMETRY_CLIP_HOST_BYTES"

#: Where Linux says how much RAM is available, and where a container's own
#: limit, what it holds now and how much of that is page cache are (cgroup
#: v2); module names so a test can point them elsewhere.
_MEMINFO = pathlib.Path("/proc/meminfo")
_CGROUP_LIMIT = pathlib.Path("/sys/fs/cgroup/memory.max")
_CGROUP_USAGE = pathlib.Path("/sys/fs/cgroup/memory.current")
_CGROUP_STAT = pathlib.Path("/sys/fs/cgroup/memory.stat")

#: How each source of a placement is named when a clip refuses it.
_PLACED_BY = {"use": "the use() block", "environment": "PHONOMETRY_COMPUTE"}


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

    A refusal names where the placement came from: ``PHONOMETRY_COMPUTE``,
    or the ``simulation.use()`` block the clip is built in.

    :raises KeyError: for a clip with no recorded device.
    :raises ValueError: when ``PHONOMETRY_COMPUTE`` is malformed, when the
        placement names a host, asks for float32, names a GPU library other
        than CuPy or a GPU other than the first, or when the lane budget is
        not a positive count of bytes.
    :raises ComputeImportError: when a lane budget is set and CuPy is not
        installed or does not import.
    :raises ComputeDeviceError: when a lane budget is set and CUDA refuses
        the GPU.
    """
    from phonometry.simulation import Compute
    from phonometry.simulation.compute import _requested_from

    if device_of(clip) == "cpu":
        return Compute(device="cpu")
    ambient, source = _requested_from(None)
    refusal = _refusal(ambient, _PLACED_BY.get(source, source))
    if refusal:
        raise ValueError(refusal)
    if ambient.device == "cpu":
        return Compute(device="cpu")
    limit_device_memory(ambient)
    return ambient


def placement_refusal(placement: Compute) -> str | None:
    """Why a GPU clip could not step on *placement*, as ``PHONOMETRY_COMPUTE`` names it; None when it could.

    What :func:`compute_for` refuses in a GPU clip's field builder, for a
    render that draws a GPU clip to ask before it asks the GPU anything or
    draws a clip. A clip placed on ``"cpu"`` refuses nothing: its field
    steps on NumPy whatever the placement.
    """
    return _refusal(placement, _PLACED_BY["environment"])


def _refusal(placement: Compute, named: str) -> str | None:
    """Why a GPU clip cannot step on *placement*, set by what *named* names; None when it can."""
    if placement.host is not None:
        return (
            f"{named} names the host {placement.host!r}, and a clip's field "
            "steps where the clip is rendered; `make animations` sends the render there"
        )
    if placement.device not in ("cpu", "cupy"):
        return (
            f"{named} names {placement.device!r}; a clip steps on NumPy "
            "or CuPy, the GPU its field was measured on"
        )
    if placement.dtype != "float64":
        return f"{named} asks for {placement.dtype}; the clips are computed in float64"
    if placement.device == "cupy" and placement.device_index:
        return (
            f"{named} names GPU {placement.device_index}; the clips step "
            "on GPU 0, so choose that GPU with "
            f"CUDA_VISIBLE_DEVICES={placement.device_index} and name cupy"
        )
    return None


def limit_device_memory(compute: Compute) -> None:
    """Hold CuPy's memory pool on *compute*'s GPU to this lane's budget.

    :raises ValueError: when ``PHONOMETRY_CLIP_GPU_BYTES`` is set to anything
        but a positive count of bytes.
    :raises ComputeImportError: when a budget is set and CuPy is not
        installed or does not import, as the engine would refuse it.
    :raises ComputeDeviceError: when a budget is set and CUDA refuses the
        GPU (no device, a driver that does not match).
    """
    from phonometry.simulation import ComputeDeviceError

    text = os.environ.get(GPU_BYTES_ENV, "").strip()
    if not text or compute.device != "cupy":
        return
    budget = _positive_bytes(GPU_BYTES_ENV, text)
    cupy = _cupy_for_budget()
    try:
        with cupy.cuda.Device(compute.device_index):
            cupy.get_default_memory_pool().set_limit(size=budget)
    except cupy.cuda.runtime.CUDARuntimeError as exc:
        msg = (
            f"{GPU_BYTES_ENV} holds GPU {compute.device_index} to {budget} bytes, "
            f"and CUDA refused that GPU: {exc}"
        )
        raise ComputeDeviceError(msg) from exc


def _cupy_for_budget() -> types.ModuleType:
    """CuPy, imported to hold a lane's pool to its budget.

    :raises ComputeImportError: when CuPy is not installed, or is installed
        and does not import (its loader raises what it raises: an
        ``ImportError`` without its CUDA libraries, an ``OSError``).
    """
    from phonometry.simulation import ComputeImportError

    try:
        cupy = importlib.import_module("cupy")
    except Exception as exc:
        missing = isinstance(exc, ModuleNotFoundError) and (
            (exc.name or "").partition(".")[0] == "cupy"
        )
        state = "is not installed" if missing else "is installed but failed to import"
        msg = f"{GPU_BYTES_ENV} holds a lane's CuPy pool to a budget, and CuPy {state} ({exc})"
        raise ComputeImportError(msg) from exc
    return cupy


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


def _count(path: pathlib.Path, text: str, unit: str) -> int:
    """The whole number *text*, read from *path*.

    :raises ValueError: naming *path* when *text* is not one.
    """
    if not (text.isascii() and text.isdigit()):
        msg = f"{path} holds {text!r} where a count of {unit} belongs"
        raise ValueError(msg)
    return int(text)


def _mem_available() -> int | None:
    """``MemAvailable`` in bytes; None off Linux, or where the kernel does not say.

    :raises OSError: when ``/proc/meminfo`` is there and cannot be read.
    :raises ValueError: when its ``MemAvailable`` line holds no count of kB.
    """
    if not _MEMINFO.exists():
        return None
    for line in _MEMINFO.read_text(encoding="utf-8").splitlines():
        key, _, rest = line.partition(":")
        if key == "MemAvailable":
            words = rest.split()
            return _count(_MEMINFO, words[0] if words else "", "kB") * 1024
    return None


def _inactive_file() -> int:
    """The container's inactive page cache, which the kernel drops before it runs out.

    The ``inactive_file`` line of ``memory.stat``; 0 where the file or the
    line is not there.

    :raises OSError: when ``memory.stat`` is there and cannot be read.
    :raises ValueError: when its ``inactive_file`` line holds no count.
    """
    if not _CGROUP_STAT.exists():
        return 0
    for line in _CGROUP_STAT.read_text(encoding="utf-8").splitlines():
        key, _, value = line.partition(" ")
        if key == "inactive_file":
            return _count(_CGROUP_STAT, value.strip(), "bytes")
    return 0


def _container_free() -> int | None:
    """The RAM a cgroup v2 container has left: its limit less its working set.

    The working set is what container runtimes count (``docker stats``,
    cAdvisor's ``working_set_bytes``): ``memory.current`` less the inactive
    page cache in ``memory.stat``, which the kernel reclaims before it kills
    anything. ``memory.current`` alone counts that cache, the video files a
    render writes among it, and drifts towards the limit over a long render.
    None outside a container or with no limit (``max``); the limit alone
    where what the container holds cannot be read, and ``memory.current``
    itself where ``memory.stat`` does not say.

    :raises OSError: when a file is there and cannot be read.
    :raises ValueError: when ``memory.max`` holds neither ``max`` nor a
        count of bytes, or ``memory.current`` or the ``inactive_file`` line
        of ``memory.stat`` holds no count of bytes.
    """
    if not _CGROUP_LIMIT.exists():
        return None
    text = _CGROUP_LIMIT.read_text(encoding="utf-8").strip()
    if text == "max":
        return None
    limit = _count(_CGROUP_LIMIT, text, "bytes")
    if not _CGROUP_USAGE.exists():
        return limit
    usage = _count(
        _CGROUP_USAGE, _CGROUP_USAGE.read_text(encoding="utf-8").strip(), "bytes"
    )
    working_set = max(usage - _inactive_file(), 0)
    return max(limit - working_set, 0)


def _available_bytes() -> int | None:
    """``MemAvailable``, capped by what a container has left; None off Linux.

    :raises OSError: when a memory file is there and cannot be read.
    :raises ValueError: when one holds no count where a count belongs.
    """
    available = _mem_available()
    if available is None:
        return None
    left = _container_free()
    return available if left is None else min(available, left)


def host_bytes() -> int | None:
    """The RAM this render may hold: its lane's budget, else what is available.

    A node gives each lane a share of the RAM it has free
    (``PHONOMETRY_CLIP_HOST_BYTES``); elsewhere the render may take what this
    machine has available, and in a container what its limit leaves when
    that is less: ``memory.max`` less the working set, ``memory.current``
    less the inactive page cache ``memory.stat`` reports. None off Linux,
    where there is no ``/proc/meminfo``.

    :raises ValueError: when ``PHONOMETRY_CLIP_HOST_BYTES`` is set to anything
        but a positive count of bytes, or when ``/proc/meminfo`` or the
        container's ``memory.max``, ``memory.current`` or ``memory.stat``
        holds no count where a count belongs, naming the file.
    :raises OSError: when one of those files is there and cannot be read.
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
    :raises OSError: when its process cannot be started (no memory left to
        fork it, say).
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
    Every lane is given a share of the RAM when it is known, and a share of
    0 is no budget at all, so no clip runs where no RAM is left, and a clip
    runs alone where half of what is left is not a byte.
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
    if available is not None:
        ram_alone, why = _ram_fit(
            clip, host_need if not on_gpu else 0, available=available
        )
        alone = alone or ram_alone
        reasons.extend(why)
    return alone, reasons


def _ram_fit(clip: str, need: int, *, available: int) -> tuple[bool, list[str]]:
    """Whether *clip*'s lane runs alone for the RAM, and why it cannot run (empty when it can).

    *need* is the RAM need that counts, 0 for none. A lane whose share of
    *available* would be 0 has no budget at all: it runs alone where half of
    what is left is not a byte, and cannot run where nothing is.
    """
    if host_share(available, alone=True) <= 0:
        return True, [f"{clip} would hold no RAM: {available >> 20} MiB is available"]
    if need > available:
        return True, [
            f"{clip} needs {need >> 20} MiB of RAM; {available >> 20} MiB is available"
        ]
    shared = host_share(available, alone=False)
    return shared <= 0 or need > shared, []
