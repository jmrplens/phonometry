#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Where a clip's wave field is computed, and what that must not touch.

A clip's device is a registry entry (``figures.registry._ANIM_DEVICES``) read
through ``scripts/clip_placement.py``. These tests hold the rules: a clip
measured to step faster on NumPy steps on NumPy whatever the environment
says; a GPU clip takes the CuPy GPU its placement names, through
``PHONOMETRY_COMPUTE`` or a ``simulation.use()`` block (the first GPU;
another is chosen with ``CUDA_VISIBLE_DEVICES``), and steps on NumPy when
none is named; any other GPU library is refused, as the clips' GPU fields
are measured on CuPy only, and a refusal names where the placement came
from; the clips are computed in float64; the memory a render lane may hold
is set on CuPy's pool, a CuPy that does not import or a GPU that CUDA
refuses being the compute errors the engines raise, and the RAM it may
hold is read from its budget or from what the machine, or its container,
has free; every GPU clip has the GPU memory its field was measured to need,
and each need is a count of bytes; and the tables are outside every clip's
fingerprint, because where a field is computed is held to the NumPy field
by measurement, not by the fingerprint.

The capture a field builder steps its engine through
(``figures.fields._core._step_and_capture``) is held here too: its frames
and reductions are those of a plain loop over the engine, its times are the
engine's own clock, and a sample step or a settle window outside the run is
refused. So are the share of a GPU and of the RAM each render lane takes,
and whether a clip shares them, runs alone or cannot run.
"""

from __future__ import annotations

import contextlib
import importlib.abc
import pathlib
import re
import subprocess
import sys
import threading
import types
from typing import TYPE_CHECKING, Any

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_ROOT / "scripts"))

import animation_fingerprint as fp
import clip_placement

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from multiprocessing.context import BaseContext
    from typing import Self

    from numpy.typing import NDArray

    from phonometry.simulation._backends import DeviceArray
    from phonometry.simulation.compute import Dtype

# The tests read the registry and the field builders, whose import sets the
# figure theme; imported here, it is set before any test's matplotlib
# settings are compared, whichever test of the worker imports it first.
import figures.registry  # noqa: F401

from phonometry import simulation
from phonometry.simulation import (
    FDTD2D,
    Compute,
    ComputeDeviceError,
    ComputeImportError,
    CWSource,
)

# The registry imports the whole figure stack, which the pinned job owns.
pytestmark = pytest.mark.pinned_stack


@pytest.fixture
def devices(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """A device table of three clips, one per kind."""
    from figures import registry

    table = {"anim_cpu": "cpu", "anim_gpu": "gpu", "anim_whole": "gpu-whole"}
    monkeypatch.setattr(registry, "_ANIM_DEVICES", table)
    monkeypatch.delenv("PHONOMETRY_COMPUTE", raising=False)
    monkeypatch.delenv(clip_placement.GPU_BYTES_ENV, raising=False)
    monkeypatch.delenv(clip_placement.HOST_BYTES_ENV, raising=False)
    return table


def test_a_cpu_clip_steps_on_numpy_whatever_the_environment_names(
    devices: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PHONOMETRY_COMPUTE", "cupy:1")
    assert clip_placement.compute_for("anim_cpu") == Compute(device="cpu")


@pytest.mark.parametrize("clip", ["anim_gpu", "anim_whole"])
def test_a_gpu_clip_takes_the_gpu_the_environment_names(
    devices: dict[str, str], monkeypatch: pytest.MonkeyPatch, clip: str
) -> None:
    """Building the record imports nothing, so this runs without CuPy."""
    monkeypatch.setenv("PHONOMETRY_COMPUTE", "cupy")
    assert clip_placement.compute_for(clip) == Compute(device="cupy")


def test_a_gpu_clip_with_no_gpu_named_steps_on_numpy(devices: dict[str, str]) -> None:
    assert clip_placement.compute_for("anim_gpu") == Compute(device="cpu")


@pytest.mark.parametrize("named", ["torch:cuda", "torch:cpu", "torch:mps,float32"])
def test_a_gpu_library_other_than_cupy_is_refused_for_a_clip(
    devices: dict[str, str], monkeypatch: pytest.MonkeyPatch, named: str
) -> None:
    """The clips' GPU fields are measured against NumPy's on CuPy only."""
    monkeypatch.setenv("PHONOMETRY_COMPUTE", named)
    with pytest.raises(ValueError, match=r"NumPy or CuPy"):
        clip_placement.compute_for("anim_gpu")


def test_a_gpu_other_than_the_first_is_refused_for_a_clip(
    devices: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A scene's own device arithmetic runs on CuPy's current device, GPU 0."""
    monkeypatch.setenv("PHONOMETRY_COMPUTE", "cupy:1")
    with pytest.raises(ValueError, match=r"CUDA_VISIBLE_DEVICES=1"):
        clip_placement.compute_for("anim_gpu")


def test_float32_in_the_environment_is_refused_for_a_clip(
    devices: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PHONOMETRY_COMPUTE", "cupy,float32")
    with pytest.raises(ValueError, match=r"clips are computed in float64"):
        clip_placement.compute_for("anim_gpu")


def test_a_clip_without_a_device_is_a_key_error(devices: dict[str, str]) -> None:
    with pytest.raises(KeyError, match=r"anim_nowhere"):
        clip_placement.device_of("anim_nowhere")


def test_every_field_clip_has_a_device_and_nothing_else_does() -> None:
    from figures import registry

    assert registry._ANIM_DEVICES.keys() == registry._ANIM_FIELDS.keys()
    assert set(registry._ANIM_DEVICES.values()) <= {"cpu", "gpu", "gpu-whole"}


def test_the_device_and_memory_tables_are_in_no_fingerprint() -> None:
    """Where a field is computed, and the memory it needs, are measured, not hashed."""
    sources = fp.Sources(_ROOT)
    tables = {
        ("figures.registry", name)
        for name in ("_ANIM_DEVICES", "_ANIM_GPU_BYTES", "_ANIM_HOST_BYTES")
    }
    for clip, entry in sources.clips().items():
        closure = sources.closure([entry, *fp._EXTRA_ROOTS])
        assert not tables & closure, clip


def test_each_gpu_clip_has_a_measured_peak_and_its_needs_are_bytes() -> None:
    from figures import registry

    on_gpu = {
        clip for clip, device in registry._ANIM_DEVICES.items() if device != "cpu"
    }
    assert registry._ANIM_GPU_BYTES.keys() == on_gpu
    assert registry._ANIM_HOST_BYTES.keys() <= registry._ANIM_DEVICES.keys()
    needs = [*registry._ANIM_GPU_BYTES.values(), *registry._ANIM_HOST_BYTES.values()]
    assert all(isinstance(n, int) and n > 0 for n in needs)


class _Pool:
    def __init__(self, log: list[str]) -> None:
        self._log = log

    def free_all_blocks(self) -> None:
        self._log.append("free")

    def set_limit(self, *, size: int) -> None:
        self._log.append(f"limit {size}")


class _CUDARuntimeError(RuntimeError):
    """CuPy's ``cupy.cuda.runtime.CUDARuntimeError``."""


def _fake_cupy(log: list[str], *, cuda_error: str | None = None) -> types.ModuleType:
    """A CuPy whose pools and device selection write to *log*.

    With *cuda_error*, selecting a GPU raises the runtime error CUDA gives
    for it (``cudaErrorNoDevice``, say).
    """
    module = types.ModuleType("cupy")
    pool = _Pool(log)
    module.get_default_memory_pool = lambda: pool  # type: ignore[attr-defined]
    module.get_default_pinned_memory_pool = lambda: pool  # type: ignore[attr-defined]

    class _Device:
        def __init__(self, index: int) -> None:
            log.append(f"device {index}")

        def __enter__(self) -> None:
            if cuda_error is not None:
                raise _CUDARuntimeError(cuda_error)

        def __exit__(self, *exc: object) -> None:
            return None

    runtime = types.SimpleNamespace(CUDARuntimeError=_CUDARuntimeError)
    module.cuda = types.SimpleNamespace(Device=_Device, runtime=runtime)  # type: ignore[attr-defined]
    return module


class _CupyImports(importlib.abc.MetaPathFinder):
    """Notes every import of CuPy this process starts, and can make it fail.

    :param failure: What the import raises, as a CuPy that is installed but
        cannot load its CUDA libraries would; None lets it go on.
    """

    def __init__(self, failure: ImportError | None = None) -> None:
        self.asked: list[str] = []
        self._failure = failure

    def find_spec(self, name: str, path: object = None, target: object = None) -> None:
        if name.partition(".")[0] == "cupy":
            self.asked.append(name)
            if self._failure is not None:
                # One record serves every test it is given to: each raise
                # starts its own traceback.
                raise self._failure.with_traceback(None)


def _watch_cupy(
    monkeypatch: pytest.MonkeyPatch, failure: ImportError | None = None
) -> _CupyImports:
    """No CuPy loaded, and every attempt to import one noted."""
    watch = _CupyImports(failure)
    monkeypatch.delitem(sys.modules, "cupy", raising=False)
    monkeypatch.setattr(sys, "meta_path", [watch, *sys.meta_path])
    return watch


def test_the_pools_are_freed_when_cupy_is_loaded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    log: list[str] = []
    monkeypatch.setitem(sys.modules, "cupy", _fake_cupy(log))
    clip_placement.release_device()
    assert log == ["free", "free"]


def test_nothing_is_freed_when_cupy_was_never_imported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Releasing never imports CuPy to free a pool nothing has filled."""
    watch = _watch_cupy(monkeypatch)
    clip_placement.release_device()
    assert watch.asked == []
    assert "cupy" not in sys.modules


def test_the_lane_budget_is_set_on_the_pool_of_the_named_gpu(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    log: list[str] = []
    monkeypatch.setitem(sys.modules, "cupy", _fake_cupy(log))
    monkeypatch.setenv(clip_placement.GPU_BYTES_ENV, "4000000000")
    clip_placement.limit_device_memory(Compute(device="cupy", device_index=1))
    assert log == ["device 1", "limit 4000000000"]


def test_a_gpu_clip_s_placement_holds_the_lane_budget(
    devices: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A scene asks for its placement and nothing else; the budget comes with it."""
    log: list[str] = []
    monkeypatch.setitem(sys.modules, "cupy", _fake_cupy(log))
    monkeypatch.setenv("PHONOMETRY_COMPUTE", "cupy")
    monkeypatch.setenv(clip_placement.GPU_BYTES_ENV, "4000000000")
    assert clip_placement.compute_for("anim_gpu") == Compute(device="cupy")
    assert log == ["device 0", "limit 4000000000"]


@pytest.mark.parametrize("text", ["four", "0", "-5"])
def test_a_lane_budget_that_is_not_a_positive_count_is_refused(
    monkeypatch: pytest.MonkeyPatch, text: str
) -> None:
    monkeypatch.setenv(clip_placement.GPU_BYTES_ENV, text)
    compute = Compute(device="cupy")
    with pytest.raises(ValueError, match=r"PHONOMETRY_CLIP_GPU_BYTES"):
        clip_placement.limit_device_memory(compute)


#: How an import of CuPy fails where it is not installed.
_NO_CUPY = ModuleNotFoundError("No module named 'cupy'", name="cupy")


@pytest.mark.parametrize(
    ("failure", "state"),
    [
        (_NO_CUPY, "is not installed"),
        (
            ImportError("libcudart.so.12: cannot open shared object file"),
            "is installed but failed to import",
        ),
    ],
    ids=["missing", "broken"],
)
def test_a_lane_budget_where_cupy_does_not_import_is_a_compute_import_error(
    monkeypatch: pytest.MonkeyPatch, failure: ImportError, state: str
) -> None:
    """Where the engine would refuse CuPy, the budget refuses it first, saying why."""
    _watch_cupy(monkeypatch, failure)
    monkeypatch.setenv(clip_placement.GPU_BYTES_ENV, "4000000000")
    compute = Compute(device="cupy")
    with pytest.raises(
        ComputeImportError, match=rf"{clip_placement.GPU_BYTES_ENV} .*CuPy {state}"
    ):
        clip_placement.limit_device_memory(compute)


def test_a_gpu_cuda_refuses_under_a_lane_budget_is_a_compute_device_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    log: list[str] = []
    cupy = _fake_cupy(
        log, cuda_error="cudaErrorNoDevice: no CUDA-capable device is detected"
    )
    monkeypatch.setitem(sys.modules, "cupy", cupy)
    monkeypatch.setenv(clip_placement.GPU_BYTES_ENV, "4000000000")
    compute = Compute(device="cupy", device_index=1)
    with pytest.raises(ComputeDeviceError, match=r"GPU 1 .*cudaErrorNoDevice"):
        clip_placement.limit_device_memory(compute)
    assert log == ["device 1"]


def test_a_gpu_clip_s_placement_brings_the_budget_s_refusal_with_it(
    devices: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _watch_cupy(monkeypatch, _NO_CUPY)
    monkeypatch.setenv("PHONOMETRY_COMPUTE", "cupy")
    monkeypatch.setenv(clip_placement.GPU_BYTES_ENV, "4000000000")
    with pytest.raises(ComputeImportError, match=r"CuPy is not installed"):
        clip_placement.compute_for("anim_gpu")


def test_a_budget_on_numpy_is_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(clip_placement.GPU_BYTES_ENV, "4000000000")
    monkeypatch.delitem(sys.modules, "cupy", raising=False)
    clip_placement.limit_device_memory(Compute(device="cpu"))
    assert "cupy" not in sys.modules


def test_a_lane_s_ram_budget_wins_over_what_the_machine_has(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(clip_placement.HOST_BYTES_ENV, "7000000000")
    assert clip_placement.host_bytes() == 7_000_000_000


def _memory_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    meminfo: str,
    limit: str | None = None,
    usage: str | None = None,
    stat: str | None = None,
) -> dict[str, pathlib.Path]:
    """``/proc/meminfo`` and a container's ``memory.max``, ``memory.current`` and ``memory.stat``.

    A file given as None is not there, as off a container.
    """
    paths = {
        "_MEMINFO": tmp_path / "meminfo",
        "_CGROUP_LIMIT": tmp_path / "memory.max",
        "_CGROUP_USAGE": tmp_path / "memory.current",
        "_CGROUP_STAT": tmp_path / "memory.stat",
    }
    texts = (meminfo, limit, usage, stat)
    for (name, path), text in zip(paths.items(), texts, strict=True):
        if text is not None:
            path.write_text(text, encoding="utf-8")
        monkeypatch.setattr(clip_placement, name, path)
    monkeypatch.delenv(clip_placement.HOST_BYTES_ENV, raising=False)
    return paths


def test_without_a_budget_the_ram_is_what_the_machine_has_available(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    _memory_files(
        monkeypatch, tmp_path, "MemTotal: 27000000 kB\nMemAvailable: 13000000 kB\n"
    )
    assert clip_placement.host_bytes() == 13_000_000 * 1024


#: A container's ``memory.stat``: 2 GiB of its usage is page cache the
#: kernel would drop before it ran out.
_STAT = "anon 1073741824\nactive_file 536870912\ninactive_file 2147483648\n"


@pytest.mark.parametrize(
    ("limit", "usage", "stat", "available"),
    [
        ("4294967296\n", "1073741824\n", None, 3 << 30),
        ("4294967296\n", "3221225472\n", _STAT, 3 << 30),
        ("4294967296\n", "3221225472\n", "anon 1073741824\n", 1 << 30),
        ("4294967296\n", "1073741824\n", _STAT, 4 << 30),
        ("4294967296\n", "5368709120\n", None, 0),
        ("max\n", "1073741824\n", _STAT, 13_000_000 * 1024),
        ("40000000000\n", "1073741824\n", None, 13_000_000 * 1024),
        ("4294967296\n", None, _STAT, 4 << 30),
    ],
    ids=[
        "no-stat",
        "cache-reclaimable",
        "stat-without-inactive-file",
        "cache-over-usage",
        "over-its-limit",
        "no-limit",
        "machine-has-less",
        "no-usage",
    ],
)
def test_in_a_container_the_ram_is_what_its_limit_leaves(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    limit: str,
    usage: str | None,
    stat: str | None,
    available: int,
) -> None:
    """``memory.max`` less the working set, as a container runtime counts it.

    The working set is ``memory.current`` less the inactive page cache that
    ``memory.stat`` reports (the video files a render writes are charged to
    its container, and the kernel drops them before it runs out), or
    ``memory.current`` itself where ``memory.stat`` does not say. The
    machine's ``MemAvailable`` (13 GB here) still caps it, and where the
    usage cannot be read the limit alone is the cap.
    """
    _memory_files(
        monkeypatch, tmp_path, "MemAvailable: 13000000 kB\n", limit, usage, stat
    )
    assert clip_placement.host_bytes() == available


@pytest.mark.parametrize(
    ("meminfo", "limit", "usage", "named"),
    [
        ("MemAvailable: lots kB\n", None, None, "meminfo"),
        ("MemAvailable:\n", None, None, "meminfo"),
        ("MemAvailable: 13000000 kB\n", "unlimited\n", None, "memory.max"),
        ("MemAvailable: 13000000 kB\n", "4294967296\n", "\n", "memory.current"),
    ],
    ids=["meminfo-word", "meminfo-empty", "limit-word", "usage-empty"],
)
def test_a_memory_file_that_holds_no_count_is_named(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    meminfo: str,
    limit: str | None,
    usage: str | None,
    named: str,
) -> None:
    paths = _memory_files(monkeypatch, tmp_path, meminfo, limit, usage, _STAT)
    shown = next(str(path) for path in paths.values() if path.name == named)
    with pytest.raises(ValueError, match=rf"^{re.escape(shown)} "):
        clip_placement.host_bytes()


def test_a_page_cache_count_that_is_not_a_count_is_named(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    paths = _memory_files(
        monkeypatch,
        tmp_path,
        "MemAvailable: 13000000 kB\n",
        "4294967296\n",
        "3221225472\n",
        "anon 1073741824\ninactive_file lots\n",
    )
    shown = re.escape(str(paths["_CGROUP_STAT"]))
    with pytest.raises(ValueError, match=rf"^{shown} holds 'lots'"):
        clip_placement.host_bytes()


def test_a_memory_file_that_cannot_be_read_is_an_os_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    paths = _memory_files(monkeypatch, tmp_path, "MemAvailable: 13000000 kB\n")
    paths["_CGROUP_LIMIT"].mkdir()
    with pytest.raises(OSError, match=r"memory\.max"):
        clip_placement.host_bytes()


@pytest.mark.parametrize("text", ["lots", "0", "-1"])
def test_a_ram_budget_that_is_not_a_positive_count_is_refused(
    monkeypatch: pytest.MonkeyPatch, text: str
) -> None:
    monkeypatch.setenv(clip_placement.HOST_BYTES_ENV, text)
    with pytest.raises(ValueError, match=r"PHONOMETRY_CLIP_HOST_BYTES"):
        clip_placement.host_bytes()


def _small_cw_run() -> FDTD2D:
    sim = FDTD2D(343.0, 0.05, shape=(40, 50), absorbing_layer_cells=6)
    sim.add_source(CWSource(ix=20, iy=20, frequency=300.0, ramp_cycles=1.0))
    return sim


def test_the_capture_is_a_plain_loop_over_the_engine() -> None:
    """The frames and reductions of a plain NumPy loop over the same run, term for term."""
    import numpy as np
    from figures.fields import _core

    sim, ref = _small_cw_run(), _small_cw_run()
    beta, steps, every = 0.9, 60, 10
    cap = _core._step_and_capture(
        sim,
        steps=steps,
        sample_steps=range(every, steps + 1, every),
        stride=2,
        rms_beta=beta,
        settle=(40, 60),
    )
    ms = np.zeros_like(ref.p)
    acc = np.zeros_like(ref.p)
    frames, rms = [], []
    for step in range(1, steps + 1):
        ref.step()
        ms *= beta
        ms += (1.0 - beta) * ref.p**2
        if 40 < step <= 60:
            acc += ref.p**2
        if step % every == 0:
            frames.append(ref.p[::2, ::2].astype(np.float32))
            rms.append(np.sqrt(ms)[::2, ::2].astype(np.float32))
    assert np.array_equal(cap.frames, np.stack(frames))
    assert np.array_equal(cap.rms_frames, np.stack(rms))
    assert np.array_equal(cap.rms_final, np.sqrt(ms))
    assert np.array_equal(cap.settled_rms, np.sqrt(acc / 20))
    assert np.array_equal(cap.times, np.arange(every, steps + 1, every) * ref.dt)


@pytest.mark.parametrize(
    "sample_steps", [[0, 5], [5, 11]], ids=["before-the-first", "past-the-last"]
)
def test_a_sample_step_outside_the_run_is_refused(sample_steps: list[int]) -> None:
    from figures.fields import _core

    sim = _small_cw_run()
    with pytest.raises(ValueError, match=r"sample steps must lie in 1\.\.10"):
        _core._step_and_capture(sim, steps=10, sample_steps=sample_steps, stride=1)


@pytest.mark.parametrize(
    "settle",
    [(5, 5), (6, 5), (-1, 5), (5, 11)],
    ids=["empty", "backwards", "before-the-run", "past-the-run"],
)
def test_a_settle_window_outside_the_run_is_refused(settle: tuple[int, int]) -> None:
    """An empty window divides by zero, and one past either end is not an RMS of the run."""
    from figures.fields import _core

    sim = _small_cw_run()
    with pytest.raises(ValueError, match=r"settle window .* 0 <= start < stop <= 10"):
        _core._step_and_capture(
            sim, steps=10, sample_steps=[5], stride=1, settle=settle
        )


def test_the_times_are_the_engine_s_own_clock() -> None:
    """An engine that stepped before the capture goes on counting from where it was."""
    import numpy as np
    from figures.fields import _core

    sim = _small_cw_run()
    sim.run(7)
    cap = _core._step_and_capture(sim, steps=10, sample_steps=[5, 10], stride=1)
    assert np.array_equal(cap.times, np.array([12, 17]) * sim.dt)
    assert sim.n == 17


def test_what_was_not_asked_for_comes_back_empty() -> None:
    from figures.fields import _core

    cap = _core._step_and_capture(_small_cw_run(), steps=5, sample_steps=[5], stride=1)
    assert cap.rms_frames.size == 0
    assert cap.rms_final.size == 0
    assert cap.settled_rms.size == 0


def test_a_blanked_frame_is_nan_where_asked_and_the_field_elsewhere() -> None:
    import numpy as np
    from figures.fields import _core

    sim = _small_cw_run()
    sim.run(5)
    blank = np.zeros(sim.p.shape, dtype=bool)
    blank[:, :3] = True
    frame = _core._blanked(sim, sim.p, blank)
    assert frame.dtype == np.float32
    assert np.isnan(frame[:, :3]).all()
    assert np.array_equal(frame[:, 3:], sim.p[:, 3:].astype(np.float32))


def test_the_settled_envelope_is_the_peak_of_the_last_period_of_the_settle() -> None:
    """The largest |p| each cell of the row reached over the last *period* steps."""
    import numpy as np
    from figures.fields import _core

    sim, ref = _small_cw_run(), _small_cw_run()
    settle, period, row, columns = 60, 12, 20, slice(None, 30, 2)
    envelope = _core._settled_envelope(
        sim, settle=settle, period=period, row=row, columns=columns
    )
    rows = []
    for _ in range(settle):
        ref.step()
        rows.append(np.abs(ref.p[row, columns]))
    assert np.array_equal(envelope, np.stack(rows[-period:]).max(axis=0))
    assert not np.array_equal(envelope, np.stack(rows).max(axis=0))
    assert sim.n == settle
    assert np.array_equal(sim.p, ref.p)


@pytest.mark.parametrize(
    ("available", "workers"),
    [(None, 3), (40 << 30, 3), (16 << 30, 2), (13 << 30, 1), (4 << 30, 1)],
)
def test_the_metadiffuser_steps_as_many_pairs_at_once_as_the_ram_holds(
    available: int | None, workers: int
) -> None:
    """Three pairs want about 26 GB; the node has about 13 GB free."""
    from figures.fields import metadiffuser

    assert metadiffuser._meta_workers(available) == workers


#: What a stand-in pair logs of each call, ``(kind, n_frames, compute)``, and
#: what a test logs beside it (``"release"``).
_PairLog = list[tuple[str, int, object] | str]


def _stand_in_pairs(
    calls: _PairLog,
) -> Callable[[str, int, object], tuple[Any, Any, Any]]:
    """A stand-in for one metadiffuser pair: frames at the kind's rank, its call logged."""
    import numpy as np

    def pair(kind: str, n_frames: int, compute: object) -> tuple[Any, Any, Any]:
        calls.append((kind, n_frames, compute))
        rank = float(("flat", "qrd", "meta").index(kind) + 1)
        frames = np.full((n_frames, 2, 3), rank, dtype=np.float32)
        return frames, frames, np.arange(n_frames, dtype=np.float64)

    return pair


@pytest.fixture
def fresh_metadiffuser_field() -> Iterator[None]:
    """The metadiffuser's field cache, empty before the test and after it."""
    from figures.fields import metadiffuser

    metadiffuser._metadiffuser_fields.cache_clear()
    yield
    metadiffuser._metadiffuser_fields.cache_clear()


@pytest.mark.usefixtures("fresh_metadiffuser_field")
def test_the_metadiffuser_on_a_gpu_steps_its_pairs_in_turn_freeing_each(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A pair is what the free GPU memory holds, and its blocks go back before the next."""
    from figures.fields import metadiffuser

    def host_bytes() -> int:
        pytest.fail("a GPU placement sized a pool by the RAM")

    placed = Compute(device="cupy")
    calls: _PairLog = []
    monkeypatch.setattr(clip_placement, "compute_for", lambda clip: placed)
    monkeypatch.setattr(clip_placement, "host_bytes", host_bytes)
    monkeypatch.setattr(
        clip_placement, "release_device", lambda: calls.append("release")
    )
    monkeypatch.setattr(metadiffuser, "_meta_pair", _stand_in_pairs(calls))
    tot, _, _ = metadiffuser._metadiffuser_fields(4)
    assert calls == [
        ("flat", 4, placed),
        "release",
        ("qrd", 4, placed),
        "release",
        ("meta", 4, placed),
        "release",
    ]
    # The placement itself, not one equal to it.
    assert all(call[2] is placed for call in calls if isinstance(call, tuple))
    assert tot[:, 0, 0, 0].tolist() == [1.0, 2.0, 3.0]


@pytest.mark.usefixtures("fresh_metadiffuser_field")
def test_the_metadiffuser_on_numpy_pools_as_many_pairs_as_the_ram_holds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """18 GiB holds two pairs of 8.55 GB: the pool is made of two spawned workers."""
    import concurrent.futures as cf

    from figures.fields import metadiffuser

    available = 18 << 30
    pools: list[tuple[int, str]] = []

    class _InTurn:
        """A process pool that maps in this process, keeping how it was made."""

        def __init__(self, *, max_workers: int, mp_context: BaseContext) -> None:
            pools.append((max_workers, mp_context.get_start_method()))

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *exc_info: object) -> None:
            del exc_info

        def map(self, fn: Callable[..., Any], *iterables: Any) -> Iterator[Any]:
            return map(fn, *iterables)

    placed = Compute(device="cpu")
    calls: _PairLog = []
    monkeypatch.setattr(cf, "ProcessPoolExecutor", _InTurn)
    monkeypatch.setattr(clip_placement, "compute_for", lambda clip: placed)
    monkeypatch.setattr(clip_placement, "host_bytes", lambda: available)
    monkeypatch.setattr(metadiffuser, "_meta_pair", _stand_in_pairs(calls))
    tot, _, _ = metadiffuser._metadiffuser_fields(4)
    assert pools == [(metadiffuser._meta_workers(available), "spawn")]
    assert pools[0][0] == 2
    assert calls == [("flat", 4, placed), ("qrd", 4, placed), ("meta", 4, placed)]
    # The placement itself, not one equal to it.
    assert all(call[2] is placed for call in calls if isinstance(call, tuple))
    assert tot[:, 0, 0, 0].tolist() == [1.0, 2.0, 3.0]


#: How long a pool of spawned stand-ins may take to see one of them die [s]:
#: the pool of three that runs here ends in 0.3 s on Linux, so a wait this long
#: is a pool that hangs.
_DEAD_POOL_S = 120.0


@pytest.mark.usefixtures("fresh_metadiffuser_field")
def test_a_metadiffuser_pair_whose_process_dies_ends_the_field_with_an_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A pair the kernel kills for its memory breaks the pool, which no longer waits for it."""
    from concurrent.futures.process import BrokenProcessPool

    import killed_worker
    from figures.fields import metadiffuser

    # A light stand-in for the placement, which the workers unpickle.
    monkeypatch.setattr(
        clip_placement, "compute_for", lambda clip: types.SimpleNamespace(device="cpu")
    )
    monkeypatch.setattr(clip_placement, "host_bytes", lambda: 40 << 30)
    monkeypatch.setattr(metadiffuser, "_meta_pair", killed_worker.killed)
    caught: list[pytest.ExceptionInfo[BrokenProcessPool]] = []
    failed: list[BaseException] = []

    def build() -> None:
        # The wait runs in a thread of its own, so that a pool that hangs is a
        # failure of this test and not a run that never ends; what the block
        # raises, a failed match included, is handed to the test's own thread.
        try:
            with pytest.raises(
                BrokenProcessPool,
                match=(
                    r"(?s)the metadiffuser's pairs stepped 3 at once.*"
                    r"killed for its memory.*8\.55 GB.*"
                    r"PHONOMETRY_CLIP_HOST_BYTES lower"
                ),
            ) as info:
                metadiffuser._metadiffuser_fields(1)
            caught.append(info)
        except BaseException as error:
            failed.append(error)

    builder = threading.Thread(target=build, daemon=True)
    builder.start()
    builder.join(_DEAD_POOL_S)
    assert not builder.is_alive(), (
        f"the field still waits on a dead pair after {_DEAD_POOL_S:g} s"
    )
    if failed:
        raise failed[0]
    # The standard library's own error stays attached as the cause.
    assert type(caught[0].value.__cause__) is BrokenProcessPool


def test_a_metadiffuser_pair_moves_its_taper_to_the_device_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Both engines of a pair step on one device, so one copy of the taper serves them."""
    import numpy as np
    from figures.fields import metadiffuser

    from phonometry.simulation import _backends

    # The scene's 1.6 m x 1.2 m box at 2.5 mm, a grid that steps in a moment.
    monkeypatch.setattr(metadiffuser, "_META_DX", 0.0025)
    monkeypatch.setattr(metadiffuser, "_META_NY", 480)
    monkeypatch.setattr(metadiffuser, "_META_NX", 640)
    taper = metadiffuser._meta_taper()[np.newaxis, :]
    uploads: list[bool] = []
    real = _backends.Backend.asarray

    def asarray(
        self: _backends.Backend, host: NDArray[Any], *, dtype: Dtype | None = None
    ) -> DeviceArray:
        uploads.append(np.shape(host) == taper.shape and np.array_equal(host, taper))
        return real(self, host, dtype=dtype)

    monkeypatch.setattr(_backends.Backend, "asarray", asarray)
    metadiffuser._meta_pair("flat", 1, Compute(device="cpu"))
    assert uploads.count(True) == 1


def test_a_lane_has_half_of_what_is_free_less_room_for_its_context() -> None:
    free, ram = 6 << 30, 12 << 30
    assert (
        clip_placement.gpu_budget(free, alone=False)
        == free // 2 - clip_placement.CONTEXT_BYTES
    )
    assert (
        clip_placement.gpu_budget(free, alone=True)
        == free - clip_placement.CONTEXT_BYTES
    )
    assert clip_placement.host_share(ram, alone=False) == ram // 2
    assert clip_placement.host_share(ram, alone=True) == ram


@pytest.mark.parametrize(
    ("device", "gpu_need", "host_need", "verdict"),
    [
        ("cpu", 0, 0, "shares"),
        ("gpu", 2 << 30, 0, "shares"),
        ("gpu", 4 << 30, 0, "alone"),
        ("gpu", 6 << 30, 0, "refused"),
        ("gpu-whole", 1 << 30, 0, "alone"),
        ("cpu", 0, 7 << 30, "alone"),
        ("cpu", 0, 13 << 30, "refused"),
        ("gpu", 2 << 30, 13 << 30, "shares"),
    ],
)
def test_a_clip_shares_runs_alone_or_cannot_run_by_its_recorded_needs(
    device: clip_placement.ClipDevice, gpu_need: int, host_need: int, verdict: str
) -> None:
    """6 GiB free on the GPU, 12 GiB of RAM available: a lane has half of each."""
    runs_alone, reasons = clip_placement.lane_fit(
        "anim_x",
        device,
        gpu_need=gpu_need,
        host_need=host_need,
        free_gpu=6 << 30,
        available=12 << 30,
    )
    assert ("refused" if reasons else "alone" if runs_alone else "shares") == verdict
    assert all("anim_x" in reason for reason in reasons)


@pytest.mark.parametrize("device", ["cpu", "gpu", "gpu-whole"])
def test_a_clip_is_refused_where_no_ram_is_left_for_its_lane(
    device: clip_placement.ClipDevice,
) -> None:
    """A lane given no RAM would be given a budget of 0, which it refuses as no budget."""
    _, reasons = clip_placement.lane_fit(
        "anim_x", device, gpu_need=1 << 30, host_need=0, free_gpu=6 << 30, available=0
    )
    assert reasons == ["anim_x would hold no RAM: 0 MiB is available"]


@pytest.mark.parametrize("device", ["cpu", "gpu"])
def test_a_clip_runs_alone_where_half_the_ram_left_is_no_byte(
    device: clip_placement.ClipDevice,
) -> None:
    """One byte cannot be shared between two lanes; all of it is still a positive budget."""
    runs_alone, reasons = clip_placement.lane_fit(
        "anim_x", device, gpu_need=1 << 30, host_need=0, free_gpu=6 << 30, available=1
    )
    assert (runs_alone, reasons) == (True, [])
    assert clip_placement.host_share(1, alone=runs_alone) > 0


def test_without_a_gpu_named_a_gpu_clip_needs_no_gpu_memory() -> None:
    """A GPU clip steps on NumPy when no GPU is named; its GPU peak does not count."""
    assert clip_placement.lane_fit(
        "anim_x", "gpu", gpu_need=9 << 30, host_need=0, free_gpu=0, available=None
    ) == (False, [])


def test_a_gpu_clip_on_numpy_needs_the_ram_its_field_takes_there() -> None:
    """The metadiffuser on a CPU render: its float64 pairs on NumPy, alone."""
    assert clip_placement.lane_fit(
        "anim_x",
        "gpu",
        gpu_need=6 << 30,
        host_need=7 << 30,
        free_gpu=0,
        available=12 << 30,
    ) == (True, [])


def test_the_free_gpu_memory_is_asked_of_cupy_in_a_process_of_its_own() -> None:
    seen: list[list[str]] = []

    def run(argv: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        seen.append(argv)
        return subprocess.CompletedProcess(argv, 0, stdout="6442450944\n", stderr="")

    assert clip_placement.free_gpu_bytes(1, run=run) == 6442450944
    assert seen[0][0] == sys.executable
    assert "Device(1).mem_info[0]" in seen[0][-1]


def test_an_answer_that_is_not_a_count_of_bytes_is_refused() -> None:
    def run(argv: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    with pytest.raises(ValueError, match=r"GPU 0"):
        clip_placement.free_gpu_bytes(0, run=run)


def test_a_host_in_the_environment_is_refused_where_a_field_steps(
    devices: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A field steps where its clip is rendered; `make animations` sends the render."""
    monkeypatch.setenv("PHONOMETRY_COMPUTE", "cupy@nas")
    with pytest.raises(ValueError, match=r"make animations"):
        clip_placement.compute_for("anim_gpu")


@pytest.mark.parametrize(
    ("environment", "placement", "refusal"),
    [
        ("cupy@nas", Compute(device="cupy", host="nas"), "names the host 'nas'"),
        ("torch:cuda", Compute(device="torch:cuda"), "names 'torch:cuda'"),
        ("cupy,float32", Compute(device="cupy", dtype="float32"), "asks for float32"),
        ("cupy:1", Compute(device="cupy", device_index=1), "names GPU 1"),
    ],
    ids=["host", "library", "float32", "second-gpu"],
)
@pytest.mark.parametrize("source", ["PHONOMETRY_COMPUTE", "the use() block"])
def test_a_refusal_names_where_the_placement_came_from(
    devices: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
    environment: str,
    placement: Compute,
    refusal: str,
    source: str,
) -> None:
    """A placement set by ``simulation.use()`` is not blamed on the environment."""
    placed: contextlib.AbstractContextManager[object] = contextlib.nullcontext()
    if source == "PHONOMETRY_COMPUTE":
        monkeypatch.setenv("PHONOMETRY_COMPUTE", environment)
    else:
        placed = simulation.use(placement)
    said = re.escape(f"{source} {refusal}")
    with placed, pytest.raises(ValueError, match=rf"^{said}"):
        clip_placement.compute_for("anim_gpu")
