#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The backend layer: what each device loads, and what happens when it cannot."""

from __future__ import annotations

import os
import subprocess
import sys
import types
import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest

from phonometry.simulation import (
    FDTD2D,
    WATER,
    Compute,
    ComputeDeviceError,
    ComputeFallbackWarning,
    ComputeImportError,
    ElasticFDTD2D,
    ElasticRecording,
    ElasticRun,
    ExplosionSource,
    FDTDRecording,
    FDTDRun,
    ForceSource,
    GaussianPulse,
    PlaneWaveSource,
    elastic_fdtd_simulation,
    fdtd_simulation,
)
from phonometry.simulation import _backends as bk

if TYPE_CHECKING:
    from collections.abc import Callable

    from numpy.typing import NDArray

    from phonometry.simulation.compute import Device, Dtype

#: The ``src`` this test module belongs to, so a subprocess imports the code
#: under test and not whatever an editable install points at.
_SRC = Path(__file__).resolve().parents[2] / "src"


#: What the probe cache holds: ``(process id, device, device_index)``.
Probed = set[tuple[int, str, int]]


@pytest.fixture(autouse=True)
def fresh_probes(monkeypatch: pytest.MonkeyPatch) -> Probed:
    """No device is known usable when a test starts, and none stays known after."""
    usable: Probed = set()
    monkeypatch.setattr(bk, "_USABLE", usable)
    return usable


def _here(device: str, index: int = 0) -> tuple[int, str, int]:
    """The cache key of *device* in this process."""
    return (os.getpid(), device, index)


class _FakeCupyArray:
    """Just enough of a CuPy array for the probe: add, sum and bring it home."""

    def __init__(self, values: NDArray[np.float64]) -> None:
        self.values = values

    def __add__(self, other: float) -> _FakeCupyArray:
        return _FakeCupyArray(self.values + other)

    def sum(self) -> _FakeCupyArray:
        return _FakeCupyArray(np.asarray(self.values.sum()))

    def get(self) -> NDArray[np.float64]:
        return self.values


def _cupy_ones(n: int, *, dtype: str) -> _FakeCupyArray:
    return _FakeCupyArray(np.ones(n, dtype=dtype))


class _FakeCupyDevice:
    """``cupy.cuda.Device``: makes its index the current one inside its block."""

    current = 0

    def __init__(self, index: int) -> None:
        self.index = index
        self.outer = 0

    def __enter__(self) -> None:
        self.outer, _FakeCupyDevice.current = _FakeCupyDevice.current, self.index

    def __exit__(self, *_exc: object) -> None:
        _FakeCupyDevice.current = self.outer


def _fake_cupy(
    *, count: int = 1, ones: Callable[..., object] = _cupy_ones
) -> types.SimpleNamespace:
    """A CuPy with *count* GPUs whose arrays come from *ones*."""
    runtime = types.SimpleNamespace(
        CUDARuntimeError=RuntimeError,
        getDeviceCount=lambda: count,
        getDeviceProperties=lambda _index: {"name": b"Some GPU"},
        runtimeGetVersion=lambda: 13020,
        driverGetVersion=lambda: 13030,
    )
    return types.SimpleNamespace(
        __version__="14.2.0",
        cuda=types.SimpleNamespace(runtime=runtime, Device=_FakeCupyDevice),
        asnumpy=np.asarray,
        ones=ones,
    )


def _torch_ones(n: int, *, device: object, dtype: str) -> NDArray[np.float64]:
    del device
    return np.ones(n, dtype=dtype)


def _fake_torch(
    *, ones: Callable[..., object] = _torch_ones
) -> tuple[types.SimpleNamespace, types.SimpleNamespace]:
    """A torch on a Mac that reports MPS, and the array-api-compat beside it."""
    torch = types.SimpleNamespace(
        __version__="2.14.1",
        version=types.SimpleNamespace(cuda=None),
        cuda=types.SimpleNamespace(is_available=lambda: False, device_count=lambda: 0),
        backends=types.SimpleNamespace(
            mps=types.SimpleNamespace(is_available=lambda: True)
        ),
        device=lambda kind: kind,
        ones=ones,
        # A dtype of the fake is its NumPy name.
        float32="float32",
        float64="float64",
    )
    return torch, types.SimpleNamespace(torch=torch)


def _kernel_that_does_not_compile(*_args: object, **_kwargs: object) -> object:
    msg = "nvrtc: error: failed to open libnvrtc-builtins.so"
    raise RuntimeError(msg)


def test_the_numpy_backend_hands_numpy_arrays_back_without_a_copy() -> None:
    b = bk.backend_for(Compute())
    assert b.xp is np
    host = np.arange(6.0).reshape(2, 3)
    dev = b.asarray(host)
    assert dev.dtype == np.float64
    assert b.to_host(dev) is dev
    assert b.provenance.device == "cpu"
    assert b.provenance.array_library is None


@pytest.mark.parametrize(
    ("code", "text"), [(13030, "13.3"), (13020, "13.2"), (12090, "12.9")]
)
def test_a_cuda_version_reads_as_major_dot_minor(code: int, text: str) -> None:
    assert bk.cuda_version(code) == text


def test_cupy_records_its_cuda_versions_decoded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The driver API level is recorded as a CUDA version, never as the driver's."""
    monkeypatch.setitem(sys.modules, "cupy", _fake_cupy())
    provenance = bk.backend_for(Compute(device="cupy")).provenance
    assert (provenance.cuda_runtime, provenance.cuda_driver_api) == ("13.2", "13.3")
    assert (provenance.gpu, provenance.array_library) == ("Some GPU", "cupy 14.2.0")


def test_float32_on_numpy_casts_once() -> None:
    b = bk.backend_for(Compute(dtype="float32"))
    assert b.asarray(np.ones(3)).dtype == np.float32
    assert b.host_dtype == np.float32


def test_a_missing_library_is_an_import_error_with_the_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def absent(_c: Compute) -> bk.Backend:
        msg = "CuPy is not installed; pip install cupy-cuda12x"
        raise ComputeImportError(msg)

    monkeypatch.setitem(bk.LOADERS, "cupy", absent)
    request = Compute(device="cupy")
    with pytest.raises(ComputeImportError, match="pip install"):
        bk.backend_for(request)


def test_fallback_warns_once_and_records_numpy(monkeypatch: pytest.MonkeyPatch) -> None:
    def absent(_c: Compute) -> bk.Backend:
        msg = "no CUDA device"
        raise ComputeDeviceError(msg)

    monkeypatch.setitem(bk.LOADERS, "cupy", absent)
    request = Compute(device="cupy", fallback=True, dtype="float32")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        b = bk.backend_for(request)
    assert [w.category for w in caught] == [ComputeFallbackWarning]
    assert "no CUDA device" in str(caught[0].message)
    assert b.provenance.device == "cpu"
    assert b.provenance.dtype == "float32"


#: Every public way to ask for a device, each asking for a GPU that is absent.
_ABSENT_GPU = Compute(device="cupy", fallback=True)
_ROUTES: dict[str, Callable[[], object]] = {
    "backend_for": lambda: bk.backend_for(_ABSENT_GPU),
    "FDTD2D": lambda: FDTD2D(343.0, 0.01, shape=(8, 8), compute=_ABSENT_GPU),
    "ElasticFDTD2D": lambda: ElasticFDTD2D(
        4000.0, 2300.0, 0.01, rho=2500.0, shape=(8, 8), compute=_ABSENT_GPU
    ),
    "ElasticFDTD2D.from_regions": lambda: ElasticFDTD2D.from_regions(
        (8, 8), 0.01, background=WATER, compute=_ABSENT_GPU
    ),
    "fdtd_simulation": lambda: fdtd_simulation(
        FDTDRun(
            343.0,
            0.01,
            1e-4,
            shape=(8, 8),
            sources=[GaussianPulse(ix=4, iy=4, half_width_s=4e-5)],
        ),
        compute=_ABSENT_GPU,
    ),
    "elastic_fdtd_simulation": lambda: elastic_fdtd_simulation(
        ElasticRun(
            4000.0,
            2300.0,
            0.01,
            1e-5,
            rho=2500.0,
            shape=(8, 8),
            sources=[ExplosionSource(ix=4, iy=4, waveform=lambda t: t)],
        ),
        compute=_ABSENT_GPU,
    ),
}


@pytest.mark.parametrize("route", sorted(_ROUTES))
def test_the_fallback_warning_points_at_the_callers_line(
    monkeypatch: pytest.MonkeyPatch, route: str
) -> None:
    """The warning names the line that asked for the device, not the library's.

    A warning filter by module, and the line a user is shown, both read the
    warning's file: through a classmethod or a simulation function a fixed
    stack level would land inside the library.
    """

    def absent(_c: Compute) -> bk.Backend:
        msg = "no CUDA device"
        raise ComputeDeviceError(msg)

    monkeypatch.setitem(bk.LOADERS, "cupy", absent)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _ROUTES[route]()
    assert [w.category for w in caught] == [ComputeFallbackWarning]
    assert caught[0].filename == __file__


def test_the_skipped_prefix_is_the_package_directory_as_imported() -> None:
    import phonometry
    from phonometry.simulation import fdtd

    prefix = bk._PACKAGE_PREFIX
    assert phonometry.__file__ == f"{prefix}__init__.py"
    assert fdtd.__file__.startswith(prefix)
    # The trailing separator keeps a sibling named like the package outside.
    assert not f"{prefix[:-1]}_extra{os.sep}module.py".startswith(prefix)


def _warns(prefix: str) -> None:
    warnings.warn("fell back", UserWarning, skip_file_prefixes=(prefix,))


def _hands_on(call: Callable[..., None], *args: object) -> None:
    call(*args)


def _read_from(function: Callable[..., None], filename: str) -> Callable[..., None]:
    """*function* as if the interpreter had read it from *filename*."""
    code = function.__code__.replace(co_filename=filename)
    return types.FunctionType(code, function.__globals__)


def test_a_dot_in_the_import_path_still_skips_the_whole_package() -> None:
    """A ``/./`` in a ``sys.path`` entry stays in every frame's file name.

    The warning is raised two frames deep in the package, as the fallback is
    (the backend, called from an engine), so the frame it skips by its file
    name is the outer one: a prefix normalised through ``Path`` loses the
    ``/./`` and leaves the warning on that library line.
    """
    root = f"{os.sep}site{os.sep}.{os.sep}"
    package = f"{root}phonometry{os.sep}simulation{os.sep}"
    backends, engine, script = (
        f"{package}_backends.py",
        f"{package}fdtd.py",
        f"{root}script.py",
    )
    prefix = bk._package_prefix(backends)
    assert prefix == f"{root}phonometry{os.sep}"
    warns = _read_from(_warns, backends)
    library = _read_from(_hands_on, engine)
    caller = _read_from(_hands_on, script)
    normalised = f"{Path(backends).parent.parent}{os.sep}"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        caller(library, warns, prefix)
        caller(library, warns, normalised)
    assert [w.filename for w in caught] == [script, engine]


def test_pyodide_refuses_every_device_but_numpy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(bk.sys, "platform", "emscripten")
    request = Compute(device="torch:cpu")
    with pytest.raises(ComputeDeviceError, match="Pyodide"):
        bk.backend_for(request)
    assert bk.backend_for(Compute()).xp is np


def test_pyodide_falls_back_to_numpy_when_asked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(bk.sys, "platform", "emscripten")
    request = Compute(device="cupy", fallback=True, dtype="float32")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        b = bk.backend_for(request)
    assert [w.category for w in caught] == [ComputeFallbackWarning]
    assert "Pyodide" in str(caught[0].message)
    assert b.xp is np
    assert b.provenance.device == "cpu"
    assert b.provenance.dtype == "float32"


def test_numpy_hands_over_the_host_array_itself() -> None:
    host = np.arange(3.0)
    assert bk.backend_for(Compute()).asarray(host) is host


def _strict() -> bk.Backend:
    pytest.importorskip("array_api_strict")
    return bk.strict_backend(Compute())


def _torch_cpu() -> bk.Backend:
    pytest.importorskip("torch")
    pytest.importorskip("array_api_compat")
    return bk.backend_for(Compute(device="torch:cpu"))


@pytest.mark.parametrize("load", [_strict, _torch_cpu], ids=["strict", "torch-cpu"])
def test_a_device_array_is_a_copy_of_the_host_array(
    load: Callable[[], bk.Backend],
) -> None:
    b = load()
    host = np.arange(3.0)
    dev = b.asarray(host)
    dev[0] = 5.0
    assert host.tolist() == [0.0, 1.0, 2.0]
    assert b.to_host(dev).tolist() == [5.0, 1.0, 2.0]


def test_torch_takes_a_read_only_reversed_host_array() -> None:
    b = _torch_cpu()
    host = np.arange(3.0)[::-1]
    host.flags.writeable = False
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        dev = b.asarray(host)
    assert b.to_host(dev).tolist() == [2.0, 1.0, 0.0]


def test_the_strict_backend_loads_when_installed() -> None:
    strict = pytest.importorskip("array_api_strict")
    b = bk.strict_backend(Compute())
    assert b.xp is strict
    assert isinstance(b.to_host(b.asarray(np.ones(2))), np.ndarray)


def test_torch_cpu_loads_when_installed() -> None:
    pytest.importorskip("torch")
    pytest.importorskip("array_api_compat")
    b = bk.backend_for(Compute(device="torch:cpu"))
    arr = b.asarray(np.arange(3.0))
    assert b.to_host(arr).tolist() == [0.0, 1.0, 2.0]
    assert b.provenance.array_library.startswith("torch ")


def _numpy_float32() -> bk.Backend:
    return bk.backend_for(Compute(dtype="float32"))


def _strict_float32() -> bk.Backend:
    pytest.importorskip("array_api_strict")
    return bk.strict_backend(Compute(dtype="float32"))


def _torch_cpu_float32() -> bk.Backend:
    pytest.importorskip("torch")
    pytest.importorskip("array_api_compat")
    return bk.backend_for(Compute(device="torch:cpu", dtype="float32"))


@pytest.mark.parametrize(
    "load",
    [_numpy_float32, _strict_float32, _torch_cpu_float32],
    ids=["numpy", "strict", "torch-cpu"],
)
def test_sums_are_float64_on_a_device_with_float64_whatever_the_fields(
    load: Callable[[], bk.Backend],
) -> None:
    b = load()
    assert b.accumulator_dtype == "float64"
    assert b.to_host(b.zeros((2,))).dtype == np.float32
    assert b.to_host(b.zeros((2,), dtype=b.accumulator_dtype)).dtype == np.float64
    assert b.to_host(b.asarray(np.ones(2))).dtype == np.float32
    host = np.array([0.1, 0.2])
    assert b.to_host(b.asarray(host, dtype="float64")).tolist() == [0.1, 0.2]


def test_numpy_hands_over_a_host_array_of_the_asked_dtype_itself() -> None:
    host = np.arange(3.0)
    assert _numpy_float32().asarray(host, dtype="float64") is host


def test_mps_sums_in_float32(
    monkeypatch: pytest.MonkeyPatch, fresh_probes: Probed
) -> None:
    torch = pytest.importorskip("torch")
    pytest.importorskip("array_api_compat")
    # MPS declared present and already proven usable, so a machine without
    # MPS can check what the backend declares: loading it allocates nothing
    # once the probe has passed.
    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: True)
    fresh_probes.add(_here("torch:mps"))
    b = bk.backend_for(Compute(device="torch:mps", dtype="float32"))
    assert b.accumulator_dtype == "float32"


# A device that says it is there but cannot compute.


def test_a_gpu_that_cannot_compile_a_kernel_is_a_device_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CuPy without NVRTC loads, then fails at its first kernel."""
    fake = _fake_cupy(ones=_kernel_that_does_not_compile)
    monkeypatch.setitem(sys.modules, "cupy", fake)
    request = Compute(device="cupy")
    with pytest.raises(ComputeDeviceError, match="failed a first small computation"):
        bk.backend_for(request)


def test_the_device_error_names_the_device_and_keeps_the_cause(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _fake_cupy(count=2, ones=_kernel_that_does_not_compile)
    monkeypatch.setitem(sys.modules, "cupy", fake)
    request = Compute(device="cupy", device_index=1)
    with pytest.raises(ComputeDeviceError) as caught:
        bk.backend_for(request)
    assert "device 'cupy:1'" in str(caught.value)
    assert "RuntimeError: nvrtc: error" in str(caught.value)
    assert isinstance(caught.value.__cause__, RuntimeError)


def test_an_mps_that_cannot_allocate_is_a_device_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MPS in a macOS virtual machine reports itself available."""
    torch, compat = _fake_torch(ones=_kernel_that_does_not_compile)
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setitem(sys.modules, "array_api_compat", compat)
    request = Compute(device="torch:mps", dtype="float32")
    with pytest.raises(ComputeDeviceError, match="device 'torch:mps' reports"):
        bk.backend_for(request)


@pytest.mark.parametrize(
    "build",
    [
        lambda c: FDTD2D(343.0, 0.01, shape=(8, 8), compute=c),
        lambda c: ElasticFDTD2D(
            4000.0, 2300.0, 0.01, rho=2500.0, shape=(8, 8), compute=c
        ),
    ],
    ids=["acoustic", "elastic"],
)
def test_a_device_that_cannot_compute_falls_back_when_asked(
    monkeypatch: pytest.MonkeyPatch, build: Callable[[Compute], FDTD2D | ElasticFDTD2D]
) -> None:
    """The engine warns and steps on NumPy, in the dtype that was asked for."""
    monkeypatch.setitem(
        sys.modules, "cupy", _fake_cupy(ones=_kernel_that_does_not_compile)
    )
    request = Compute(device="cupy", fallback=True, dtype="float32")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        sim = build(request)
    sim.step()
    assert [w.category for w in caught] == [ComputeFallbackWarning]
    assert "failed a first small computation" in str(caught[0].message)
    assert caught[0].filename == __file__
    assert (sim.provenance.device, sim.provenance.dtype) == ("cpu", "float32")
    assert sim.host_field("vx").dtype == np.float32


def test_a_device_is_probed_once_per_process(
    monkeypatch: pytest.MonkeyPatch, fresh_probes: Probed
) -> None:
    calls: list[int] = []

    def ones(n: int, *, dtype: str) -> _FakeCupyArray:
        calls.append(n)
        return _cupy_ones(n, dtype=dtype)

    monkeypatch.setitem(sys.modules, "cupy", _fake_cupy(ones=ones))
    request = Compute(device="cupy")
    bk.backend_for(request)
    bk.backend_for(request)
    assert calls == [4]
    assert fresh_probes == {_here("cupy")}


def test_a_forked_child_probes_its_device_again(
    monkeypatch: pytest.MonkeyPatch, fresh_probes: Probed
) -> None:
    """A fork's child shares the parent's memory but not its CUDA context."""
    calls: list[int] = []

    def ones(n: int, *, dtype: str) -> _FakeCupyArray:
        calls.append(n)
        return _cupy_ones(n, dtype=dtype)

    monkeypatch.setitem(sys.modules, "cupy", _fake_cupy(ones=ones))
    request = Compute(device="cupy")
    bk.backend_for(request)
    parent = os.getpid()
    child = parent + 1
    monkeypatch.setattr(bk, "os", types.SimpleNamespace(getpid=lambda: child))
    bk.backend_for(request)
    bk.backend_for(request)
    assert calls == [4, 4]
    assert fresh_probes == {(parent, "cupy", 0), (child, "cupy", 0)}


def test_the_cupy_probe_runs_on_the_device_asked_for(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Index 1 is the current device while the probe allocates, and only then."""
    seen: list[int] = []

    def ones(n: int, *, dtype: str) -> _FakeCupyArray:
        seen.append(_FakeCupyDevice.current)
        return _cupy_ones(n, dtype=dtype)

    monkeypatch.setitem(sys.modules, "cupy", _fake_cupy(count=2, ones=ones))
    bk.backend_for(Compute(device="cupy", device_index=1))
    assert seen == [1]
    assert _FakeCupyDevice.current == 0


@pytest.mark.parametrize("dtype", ["float32", "float64"])
def test_the_cupy_probe_computes_in_the_run_dtype(
    monkeypatch: pytest.MonkeyPatch, dtype: Dtype
) -> None:
    asked: list[str] = []

    def ones(n: int, *, dtype: str) -> _FakeCupyArray:
        asked.append(dtype)
        return _cupy_ones(n, dtype=dtype)

    monkeypatch.setitem(sys.modules, "cupy", _fake_cupy(ones=ones))
    bk.backend_for(Compute(device="cupy", dtype=dtype))
    assert asked == [dtype]


def test_the_mps_probe_asks_for_float32_whatever_torch_defaults_to(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """After ``torch.set_default_dtype(torch.float64)`` a bare ``ones`` is float64.

    MPS refuses float64, so a probe that left the dtype to torch would turn a
    working Mac away; it asks for the run's dtype, float32 on MPS.
    """
    asked: list[object] = []

    def ones(n: int, *, device: object, dtype: object = "float64") -> object:
        asked.append(dtype)
        if dtype != "float32":
            msg = "Cannot convert a MPS Tensor to float64 dtype"
            raise TypeError(msg)
        return _torch_ones(n, device=device, dtype="float32")

    torch, compat = _fake_torch(ones=ones)
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setitem(sys.modules, "array_api_compat", compat)
    bk.backend_for(Compute(device="torch:mps", dtype="float32"))
    assert asked == ["float32"]


def test_a_failed_probe_is_not_remembered(
    monkeypatch: pytest.MonkeyPatch, fresh_probes: Probed
) -> None:
    """A device that failed once is probed again, and passes once it can."""
    outcomes = [_kernel_that_does_not_compile, _cupy_ones]

    def ones(n: int, *, dtype: str) -> object:
        return outcomes.pop(0)(n, dtype=dtype)

    monkeypatch.setitem(sys.modules, "cupy", _fake_cupy(ones=ones))
    request = Compute(device="cupy")
    with pytest.raises(ComputeDeviceError, match="first small computation"):
        bk.backend_for(request)
    assert fresh_probes == set()
    assert bk.backend_for(request).name == "cupy"
    assert outcomes == []


def test_each_torch_device_is_probed_on_its_own(
    monkeypatch: pytest.MonkeyPatch, fresh_probes: Probed
) -> None:
    devices: list[object] = []

    def ones(n: int, *, device: object, dtype: str) -> NDArray[np.float64]:
        devices.append(device)
        return np.ones(n, dtype=dtype)

    torch, compat = _fake_torch(ones=ones)
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setitem(sys.modules, "array_api_compat", compat)
    for device in ("torch:mps", "torch:cpu", "torch:mps"):
        bk.backend_for(Compute(device=device, dtype="float32"))
    assert devices == ["mps", "cpu"]
    assert fresh_probes == {_here("torch:mps"), _here("torch:cpu")}


# The loaders' own branches, without a stand-in loader.


def test_cupy_absent_is_an_import_error_that_says_so(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``None`` in ``sys.modules`` stops ``import cupy`` whether or not it is installed."""
    monkeypatch.setitem(sys.modules, "cupy", None)
    request = Compute(device="cupy")
    with pytest.raises(ComputeImportError, match="needs CuPy, which is not installed"):
        bk.backend_for(request)


def test_torch_absent_is_an_import_error_that_says_so(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "torch", None)
    request = Compute(device="torch:cpu")
    with pytest.raises(ComputeImportError, match="which is not installed"):
        bk.backend_for(request)


def _installed_but_broken(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    error: str,
    reason: str,
) -> None:
    """Put a package *name* first on the path whose import raises *error*."""
    package = tmp_path / name
    package.mkdir()
    (package / "__init__.py").write_text(
        f"raise {error}({reason!r})\n", encoding="utf-8"
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.delitem(sys.modules, name, raising=False)


@pytest.mark.parametrize(
    ("device", "name", "error", "reason"),
    [
        # CuPy wraps a CUDA library it cannot load in an ImportError.
        ("cupy", "cupy", "ImportError", "CuPy failed to load libnvrtc.so.13"),
        # torch's _load_global_deps lets the OSError of ctypes through.
        (
            "torch:cuda",
            "torch",
            "OSError",
            "libcudnn.so.9: cannot open shared object file: No such file or directory",
        ),
        # A binary built against another NumPy.
        (
            "cupy",
            "cupy",
            "ValueError",
            "numpy.dtype size changed, may indicate binary incompatibility",
        ),
    ],
    ids=["cupy-import-error", "torch-os-error", "cupy-value-error"],
)
def test_a_library_that_is_installed_but_does_not_import_does_not_read_as_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    device: Device,
    name: str,
    error: str,
    reason: str,
) -> None:
    """The import's own reason reaches the error and the fallback warning."""
    _installed_but_broken(tmp_path, monkeypatch, name, error, reason)
    request = Compute(device=device)
    with pytest.raises(ComputeImportError) as caught:
        bk.backend_for(request)
    message = str(caught.value)
    assert "is installed but failed to import" in message
    assert reason in message
    assert "not installed" not in message
    with warnings.catch_warnings(record=True) as warned:
        warnings.simplefilter("always")
        bk.backend_for(Compute(device=device, fallback=True))
    assert reason in str(warned[0].message)


def test_a_cupy_index_past_the_gpus_present_is_a_device_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "cupy", _fake_cupy(count=1))
    request = Compute(device="cupy", device_index=1)
    with pytest.raises(ComputeDeviceError, match="index 1 asked for"):
        bk.backend_for(request)


def test_torch_cuda_without_cuda_is_a_device_error() -> None:
    """The real loader on a CPU build of torch, as the array-api job has."""
    torch = pytest.importorskip("torch")
    pytest.importorskip("array_api_compat")
    if torch.cuda.is_available():
        pytest.skip("this machine has a CUDA device")
    request = Compute(device="torch:cuda")
    with pytest.raises(ComputeDeviceError, match="found no CUDA device"):
        bk.backend_for(request)


#: A NumPy run of both simulation functions, then the device libraries it
#: brought in, if any.
_NUMPY_RUN = """
import sys
from phonometry import simulation as s
s.fdtd_simulation(s.FDTDRun(
    343.0, 0.01, 1e-4, shape=(8, 8), recording=s.FDTDRecording(probes=[(4, 4)]),
    sources=[s.GaussianPulse(ix=4, iy=4, half_width_s=4e-5)],
))
s.elastic_fdtd_simulation(s.ElasticRun(
    4000.0, 2300.0, 0.01, 1e-5, rho=2500.0, shape=(8, 8),
    sources=[s.ExplosionSource(ix=4, iy=4, waveform=lambda t: t)],
))
libraries = {"cupy", "torch", "array_api_compat", "array_api_strict"}
print(sorted(libraries & {name.partition(".")[0] for name in sys.modules}))
"""


def test_a_numpy_run_imports_no_device_library() -> None:
    """Not at import and not when it steps: they load only when a device asks."""
    env = {k: v for k, v in os.environ.items() if k != "PHONOMETRY_COMPUTE"}
    # The worktree's src first, the rest of the path after it, so a torch
    # that is installed is importable and the run still leaves it alone.
    env["PYTHONPATH"] = os.pathsep.join(
        filter(None, (str(_SRC), os.environ.get("PYTHONPATH")))
    )
    done = subprocess.run(
        [sys.executable, "-c", _NUMPY_RUN],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == "[]"


# An argument the engine refuses is refused before the device is asked for.


def _acoustic_run(compute: Compute, **changes: Any) -> object:
    """A small acoustic run, the bad argument of the case in *changes*."""
    arguments: dict[str, Any] = {
        "duration": 1e-4,
        "shape": (8, 8),
        "sources": [GaussianPulse(ix=4, iy=4, half_width_s=4e-5)],
        "recording": FDTDRecording(probes=[(4, 4)]),
        **changes,
    }
    duration = arguments.pop("duration")
    return fdtd_simulation(FDTDRun(343.0, 0.01, duration, **arguments), compute=compute)


def _elastic_run(compute: Compute, **changes: Any) -> object:
    """A small elastic run, the bad argument of the case in *changes*."""
    arguments: dict[str, Any] = {
        "duration": 1e-5,
        "shape": (8, 8),
        "sources": [ExplosionSource(ix=4, iy=4, waveform=_ramp)],
        "recording": ElasticRecording(probes=[(4, 4)]),
        **changes,
    }
    duration = arguments.pop("duration")
    return elastic_fdtd_simulation(
        ElasticRun(4000.0, 2300.0, 0.01, duration, rho=2500.0, **arguments),
        compute=compute,
    )


def _ramp(t: float) -> float:
    return t


#: An obstacle of one cell, at row 1, column 1.
_CELL_1_1 = np.zeros((8, 8), dtype=bool)
_CELL_1_1[1, 1] = True


_BAD_ARGUMENTS: dict[str, tuple[Callable[[Compute], object], str]] = {
    "acoustic run, probe off the grid": (
        lambda c: _acoustic_run(c, recording=FDTDRecording(probes=[(20, 4)])),
        "lies outside the grid",
    ),
    "acoustic run, probe in the obstacle": (
        lambda c: _acoustic_run(
            c, recording=FDTDRecording(probes=[(1, 1)]), obstacle_mask=_CELL_1_1
        ),
        r"probe \(1, 1\) lies inside an obstacle",
    ),
    "acoustic run, source off the grid": (
        lambda c: _acoustic_run(
            c, sources=[GaussianPulse(ix=20, iy=4, half_width_s=4e-5)]
        ),
        "source position lies outside the grid",
    ),
    "acoustic run, plane wave off the grid": (
        lambda c: _acoustic_run(
            c, sources=[PlaneWaveSource(direction="down", waveform=_ramp, offset=9)]
        ),
        "plane-wave offset lies outside the grid",
    ),
    "acoustic run, too short": (
        lambda c: _acoustic_run(c, duration=1e-9),
        "duration must cover at least one time step",
    ),
    "elastic run, probe off the grid": (
        lambda c: _elastic_run(c, recording=ElasticRecording(probes=[(4, 20)])),
        "lies outside the grid",
    ),
    "elastic run, explosion off the grid": (
        lambda c: _elastic_run(
            c, sources=[ExplosionSource(ix=8, iy=4, waveform=_ramp)]
        ),
        "source position lies outside the grid",
    ),
    "elastic run, force in the obstacle": (
        lambda c: _elastic_run(
            c,
            sources=[ForceSource(ix=1, iy=2, direction="x", waveform=_ramp)],
            obstacle_mask=np.eye(8, dtype=bool),
        ),
        "source position lies inside an obstacle",
    ),
    "elastic run, too short": (
        lambda c: _elastic_run(c, duration=1e-12),
        "duration must cover at least one time step",
    ),
    "acoustic cfl": (
        lambda c: FDTD2D(343.0, 0.01, shape=(8, 8), cfl=1.5, compute=c),
        "cfl must lie in",
    ),
    "acoustic impedance on a sponge": (
        lambda c: FDTD2D(
            343.0,
            0.01,
            shape=(8, 8),
            sponge_width=2,
            edge_impedance={"left": 413.0},
            compute=c,
        ),
        "cannot be both absorbing and an impedance",
    ),
    "acoustic obstacle": (
        lambda c: FDTD2D(
            343.0, 0.01, shape=(8, 8), obstacle_mask=np.zeros((4, 4), bool), compute=c
        ),
        "obstacle_mask must match",
    ),
    "elastic sides": (
        lambda c: ElasticFDTD2D(
            4000.0,
            2300.0,
            0.01,
            rho=2500.0,
            shape=(8, 8),
            sponge_width=2,
            free_sides="top",
            compute=c,
        ),
        "cannot be both free and absorbing",
    ),
    "elastic obstacle": (
        lambda c: ElasticFDTD2D(
            4000.0,
            2300.0,
            0.01,
            rho=2500.0,
            shape=(8, 8),
            obstacle_mask=np.ones((8, 8), bool),
            compute=c,
        ),
        "obstacle_mask must leave open cells",
    ),
}


@pytest.mark.parametrize("fallback", [False, True], ids=["raise", "fallback"])
@pytest.mark.parametrize("case", sorted(_BAD_ARGUMENTS))
def test_a_bad_argument_raises_its_own_error_before_the_device_is_asked_for(
    monkeypatch: pytest.MonkeyPatch, case: str, *, fallback: bool
) -> None:
    """Neither a missing library's error nor a fallback warning comes first."""
    asked: list[Compute] = []

    def absent(request: Compute) -> bk.Backend:
        asked.append(request)
        msg = "no CuPy here"
        raise ComputeImportError(msg)

    monkeypatch.setitem(bk.LOADERS, "cupy", absent)
    build, match = _BAD_ARGUMENTS[case]
    request = Compute(device="cupy", fallback=fallback)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with pytest.raises(ValueError, match=match):
            build(request)
    assert caught == []
    assert asked == []


def test_the_backend_of_an_engine_is_never_on_a_node() -> None:
    request = Compute(device="cupy", host="nas")
    with pytest.raises(
        ValueError, match="host 'nas' reached the backend of an engine built here"
    ):
        bk.backend_for(request)
