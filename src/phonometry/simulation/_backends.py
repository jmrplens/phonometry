#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The array backends the FDTD engines step on (private).

A :class:`Backend` turns a :class:`~phonometry.simulation.Compute` request
into an Array API namespace, a device and a dtype. The engines build every
map on the host in float64 and hand it over once with :meth:`Backend.asarray`;
after that they only use Array API standard operations, so one stepping code
serves NumPy, CuPy and torch. The NumPy backend copies nothing it does not
have to, which is what keeps the NumPy path bit for bit what it was.

The libraries are imported only when their device is asked for: the NumPy
path imports nothing new. Every other device is then proven usable with one
small computation, once per process.
"""

from __future__ import annotations

import os
import sys
import warnings
from contextlib import AbstractContextManager, contextmanager, nullcontext
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from .compute import (
    Compute,
    ComputeDeviceError,
    ComputeFallbackWarning,
    ComputeImportError,
    Dtype,
    RunProvenance,
    _requested,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from types import ModuleType

    from numpy.typing import NDArray

#: An array on a backend's device: a ``numpy.ndarray``, a ``cupy.ndarray``, a
#: ``torch.Tensor`` or an array-api-strict ``Array``. The Array API standard
#: has no array type to name here, so it is ``Any`` under a name that says
#: which arrays it stands for.
DeviceArray = Any


@dataclass(frozen=True)
class Backend:
    """One array library on one device in one dtype.

    The fields step in the backend dtype (``host_dtype``). A running sum over
    many steps, such as the DFT sums of a contour probe, keeps
    ``accumulator_dtype`` instead: ``"float64"`` on every device that has
    float64, also when the fields are float32, because the rounding of a sum
    grows with the number of terms; ``"float32"`` only on ``torch:mps``, which
    has no float64, where the caller compensates the sum itself.
    """

    xp: Any
    name: str
    host_dtype: np.dtype[Any]
    accumulator_dtype: Dtype
    provenance: RunProvenance
    _asarray: Callable[[NDArray[Any], str], DeviceArray]
    _to_host: Callable[[DeviceArray], NDArray[Any]]
    _zeros: Callable[[tuple[int, ...], str], DeviceArray]
    _index: Callable[[NDArray[Any]], DeviceArray]
    _context: Callable[[], AbstractContextManager[None]]

    def asarray(self, host: NDArray[Any], *, dtype: Dtype | None = None) -> DeviceArray:
        """The host array *host* on the device, in the backend dtype or *dtype*.

        On NumPy it is *host* itself when *host* already has that dtype, and a
        converted copy when it does not, so a caller that goes on to change a
        map copies it first. On every other backend it is a copy of its own.
        """
        return self._asarray(host, self.host_dtype.name if dtype is None else dtype)

    def zeros(
        self, shape: tuple[int, ...], *, dtype: Dtype | None = None
    ) -> DeviceArray:
        """A zero array of *shape* on the device, in the backend dtype or *dtype*."""
        return self._zeros(shape, self.host_dtype.name if dtype is None else dtype)

    def to_host(self, array: DeviceArray) -> NDArray[Any]:
        """*array* as a NumPy array (the array itself on NumPy)."""
        return self._to_host(array)

    def index(self, host: NDArray[Any]) -> DeviceArray:
        """The host integer array *host* as an int64 index array on the device."""
        return self._index(host)

    def scalar(self, array: DeviceArray) -> float:
        """A 0-d device array as a Python float."""
        return float(self._to_host(array))

    def context(self) -> AbstractContextManager[None]:
        """The scope the engine steps in (the CUDA device for CuPy)."""
        return self._context()


def cuda_version(code: int) -> str:
    """A CUDA version as CUDA encodes it, ``1000 major + 10 minor``, as ``"13.2"``.

    :param code: What ``cudaRuntimeGetVersion`` or ``cudaDriverGetVersion``
        return, ``13020`` for CUDA 13.2.
    """
    return f"{code // 1000}.{code % 1000 // 10}"


def _provenance(compute: Compute, **found: str | None) -> RunProvenance:
    return RunProvenance(
        host=None,
        device=compute.device,
        device_index=compute.device_index,
        dtype=compute.dtype,
        numpy_version=np.__version__,
        array_library=found.get("array_library"),
        cuda_runtime=found.get("cuda_runtime"),
        cuda_driver_api=found.get("cuda_driver_api"),
        gpu=found.get("gpu"),
        package_sha256=None,
    )


def _numpy(compute: Compute) -> Backend:
    dtype = np.dtype(compute.dtype)
    return Backend(
        xp=np,
        name="numpy",
        host_dtype=dtype,
        accumulator_dtype="float64",
        provenance=_provenance(compute),
        _asarray=lambda host, dtype: np.asarray(host, dtype=dtype),
        _to_host=np.asarray,
        _zeros=lambda shape, dtype: np.zeros(shape, dtype=dtype),
        _index=lambda host: np.asarray(host, dtype=np.int64),
        _context=nullcontext,
    )


#: The devices a first small computation has shown usable, as ``(process
#: id, device, device_index)``. The process id keeps "once per process" true
#: across a fork, whose child has a CUDA context of its own to prove. Only a
#: success is kept: a device that failed is probed again the next time it is
#: asked for.
_USABLE: set[tuple[int, str, int]] = set()


def _probe(compute: Compute, first_computation: Callable[[], object]) -> None:
    """Refuse a device that says it is there but cannot compute, once per process.

    A device can report itself available and still fail when it is used: MPS
    in a macOS virtual machine cannot allocate, and CuPy without NVRTC or the
    CUDA headers loads, then fails to compile its first kernel. The probe
    allocates, runs one elementwise kernel and one reduction and brings the
    scalar to the host, so such a device is refused here, like an absent one,
    and not by the engine's constructor or its first step.

    :param first_computation: That computation, inside the device's scope.
    :raises ComputeDeviceError: naming the device and what went wrong.
    """
    key = (os.getpid(), compute.device, compute.device_index)
    if key in _USABLE:
        return
    try:
        first_computation()
    except Exception as exc:
        where: str = compute.device
        if compute.device_index:
            where = f"{where}:{compute.device_index}"
        msg = (
            f"device {where!r} reports itself available but failed a first "
            f"small computation: {type(exc).__name__}: {exc}"
        )
        raise ComputeDeviceError(msg) from exc
    _USABLE.add(key)


def _import_error(
    compute: Compute,
    exc: Exception,
    *,
    needs: str,
    packages: tuple[str, ...],
    install: str,
    repair: str,
) -> ComputeImportError:
    """The error for a device whose library did not import, with the import's reason.

    A library that is not installed fails with a ``ModuleNotFoundError``
    naming one of its *packages*. One that is installed but cannot load what
    it links to fails with anything else: an ``ImportError`` from CuPy
    without its CUDA libraries, an ``OSError`` from the loader torch calls
    for ``libcudnn`` or ``c10.dll``, a ``ValueError`` from a binary built
    against another NumPy. "Not installed" would send its user to install
    what is already there.

    :param needs: What the device needs, as the message names it.
    :param packages: The top-level packages that are missing when it is not
        installed.
    :param install: How to install it.
    :param repair: What to check when it is installed and does not import.
    """
    missing = isinstance(exc, ModuleNotFoundError) and (
        (exc.name or "").partition(".")[0] in packages
    )
    state, remedy = (
        ("is not installed", install)
        if missing
        else ("is installed but failed to import", repair)
    )
    msg = f"device {compute.device!r} needs {needs}, which {state} ({exc}); {remedy}"
    return ComputeImportError(msg)


def _cupy(compute: Compute) -> Backend:
    # Imported here, when the device is asked for, and never at module import.
    # Any exception, not only ImportError: an installed library that fails
    # to load what it links to raises what its loader raises.
    try:
        import cupy
    except Exception as exc:
        raise _import_error(
            compute,
            exc,
            needs="CuPy",
            packages=("cupy",),
            install=(
                "install the wheel for your CUDA version, e.g. pip install cupy-cuda12x"
            ),
            repair=(
                "check that the CUDA libraries its wheel loads are present and "
                "match the wheel's CUDA version"
            ),
        ) from exc
    try:
        count = cupy.cuda.runtime.getDeviceCount()
    except cupy.cuda.runtime.CUDARuntimeError as exc:
        msg = f"device 'cupy' found no usable CUDA device: {exc}"
        raise ComputeDeviceError(msg) from exc
    if compute.device_index >= count:
        msg = f"device 'cupy' index {compute.device_index} asked for, but {count} CUDA device(s) present"
        raise ComputeDeviceError(msg)
    index = compute.device_index

    def first_computation() -> None:
        with cupy.cuda.Device(index):
            (cupy.ones(4, dtype=compute.dtype) + 1).sum().get()

    _probe(compute, first_computation)
    props = cupy.cuda.runtime.getDeviceProperties(index)

    @contextmanager
    def scope() -> Iterator[None]:
        with cupy.cuda.Device(index):
            yield

    def asarray(host: NDArray[Any], dtype: str) -> DeviceArray:
        with cupy.cuda.Device(index):
            return cupy.asarray(np.asarray(host, dtype=dtype))

    def zeros(shape: tuple[int, ...], dtype: str) -> DeviceArray:
        with cupy.cuda.Device(index):
            return cupy.zeros(shape, dtype=dtype)

    def as_index(host: NDArray[Any]) -> DeviceArray:
        with cupy.cuda.Device(index):
            return cupy.asarray(np.asarray(host, dtype=np.int64))

    return Backend(
        xp=cupy,
        name="cupy",
        host_dtype=np.dtype(compute.dtype),
        accumulator_dtype="float64",
        provenance=_provenance(
            compute,
            array_library=f"cupy {cupy.__version__}",
            cuda_runtime=cuda_version(cupy.cuda.runtime.runtimeGetVersion()),
            cuda_driver_api=cuda_version(cupy.cuda.runtime.driverGetVersion()),
            gpu=props["name"].decode(),
        ),
        _asarray=asarray,
        _to_host=cupy.asnumpy,
        _zeros=zeros,
        _index=as_index,
        _context=scope,
    )


def _torch_device(torch: ModuleType, compute: Compute) -> object:
    """The ``torch.device`` *compute* names, once torch says it is there.

    :raises ComputeDeviceError: for no CUDA device, an index past the CUDA
        devices present, or no MPS.
    """
    kind = compute.device.split(":", 1)[1]
    if kind == "cuda":
        if not torch.cuda.is_available():
            msg = "device 'torch:cuda' found no CUDA device"
            raise ComputeDeviceError(msg)
        count = torch.cuda.device_count()
        if compute.device_index >= count:
            msg = f"device 'torch:cuda' index {compute.device_index} asked for, but {count} present"
            raise ComputeDeviceError(msg)
        return torch.device(f"cuda:{compute.device_index}")
    if kind == "mps" and not torch.backends.mps.is_available():
        msg = "device 'torch:mps' is not available on this machine"
        raise ComputeDeviceError(msg)
    return torch.device(kind)


def _torch_install(compute: Compute) -> str:
    """How to install torch for *compute*'s device, as the compute guide says.

    For ``torch:cpu`` the CPU wheels first, then the extra, which keeps the
    torch it finds: the wheels PyPI serves for Linux bring gigabytes of CUDA
    libraries a CPU never uses. For a GPU device the extra alone. No
    punctuation touches the index URL, so the command copies as it reads.
    """
    if compute.device == "torch:cpu":
        return (
            "pip install torch --index-url https://download.pytorch.org/whl/cpu "
            'and then pip install "phonometry[torch]"'
        )
    return 'pip install "phonometry[torch]"'


def _torch(compute: Compute) -> Backend:
    # Imported here, when the device is asked for, and never at module import.
    # Any exception, as for CuPy: torch reports a missing CUDA or cuDNN
    # library with the OSError of the loader, not an ImportError.
    try:
        import torch
        from array_api_compat import torch as xp
    except Exception as exc:
        raise _import_error(
            compute,
            exc,
            needs="PyTorch with array-api-compat",
            packages=("torch", "array_api_compat"),
            install=_torch_install(compute),
            repair=(
                "check that the libraries PyTorch loads, CUDA's among them, "
                "are present and match its build"
            ),
        ) from exc
    kind = compute.device.split(":", 1)[1]
    device = _torch_device(torch, compute)
    # The run's dtype, never torch's default: after
    # torch.set_default_dtype(torch.float64) the default would be float64,
    # which MPS refuses. On MPS the run's dtype is always float32.
    run_dtype = getattr(torch, compute.dtype)
    _probe(
        compute,
        lambda: (torch.ones(4, device=device, dtype=run_dtype) + 1).sum().item(),
    )
    gpu: str | None = None
    if kind == "cuda":
        gpu = torch.cuda.get_device_name(compute.device_index)
    elif kind == "mps":
        gpu = "Apple MPS"
    return Backend(
        xp=xp,
        name=f"torch:{kind}",
        host_dtype=np.dtype(compute.dtype),
        # MPS has no float64.
        accumulator_dtype="float32" if kind == "mps" else "float64",
        provenance=_provenance(
            compute,
            array_library=f"torch {torch.__version__}",
            cuda_runtime=torch.version.cuda if kind == "cuda" else None,
            gpu=gpu,
        ),
        # A host copy of its own first: torch.as_tensor shares the memory
        # of a NumPy array of its dtype, warns on a read-only one and refuses
        # negative strides, and the copy settles all three.
        _asarray=lambda host, dtype: torch.as_tensor(
            np.array(host, dtype=dtype, copy=True), device=device
        ),
        _to_host=lambda array: array.detach().cpu().numpy(),
        _zeros=lambda shape, dtype: torch.zeros(
            shape, dtype=getattr(torch, dtype), device=device
        ),
        _index=lambda host: torch.as_tensor(
            np.array(host, dtype=np.int64, copy=True), device=device
        ),
        _context=nullcontext,
    )


def strict_backend(compute: Compute) -> Backend:
    """array-api-strict on its CPU device: the conformance backend of the tests."""
    # A development dependency: only the tests that ask for it import it.
    import array_api_strict as xp

    return Backend(
        xp=xp,
        name="array-api-strict",
        host_dtype=np.dtype(compute.dtype),
        accumulator_dtype="float64",
        provenance=_provenance(
            compute, array_library=f"array-api-strict {xp.__version__}"
        ),
        # array-api-strict wraps a NumPy array of its dtype without copying.
        _asarray=lambda host, dtype: xp.asarray(
            np.array(host, dtype=dtype, copy=True), dtype=getattr(xp, dtype)
        ),
        # Through DLPack, the standard's interchange, so a test can refuse
        # every other way into NumPy (__array__, the buffer protocol).
        _to_host=lambda array: np.from_dlpack(array),
        _zeros=lambda shape, dtype: xp.zeros(shape, dtype=getattr(xp, dtype)),
        _index=lambda host: xp.asarray(
            np.array(host, dtype=np.int64, copy=True), dtype=xp.int64
        ),
        _context=nullcontext,
    )


#: How each device is loaded; the tests swap an entry to reach a backend
#: that no Compute names (array-api-strict) or one that is absent.
LOADERS: dict[str, Callable[[Compute], Backend]] = {
    "cpu": _numpy,
    "cupy": _cupy,
    "torch:cpu": _torch,
    "torch:cuda": _torch,
    "torch:mps": _torch,
}


def _load(request: Compute) -> Backend:
    """The backend *request* names, or the error that says why it is absent."""
    if sys.platform == "emscripten" and request.device != "cpu":
        msg = f"device {request.device!r} is not available in Pyodide; only 'cpu' is"
        raise ComputeDeviceError(msg)
    return LOADERS[request.device](request)


def _package_prefix(module_file: str) -> str:
    """The package directory of *module_file*, ``phonometry/simulation/x.py``.

    Cut from the string as it is, never through :class:`~pathlib.Path`: a
    frame's ``co_filename`` keeps the path the import system built from the
    ``sys.path`` entry, a ``/./`` or a ``..`` included, and a normalised
    prefix would not match it. The trailing separator stays, so that a
    sibling named like the package (``phonometry_extra/``) does not match.
    """
    return f"{module_file.rsplit(os.sep, 2)[0]}{os.sep}"


#: The package's own directory as the import system wrote it. A fallback
#: warning skips every frame in it.
_PACKAGE_PREFIX = _package_prefix(__file__)


def backend_for(compute: Compute | None) -> Backend:
    """The backend *compute* asks for, after the precedence rules and the fallback.

    A fallback warning points at the first line outside phonometry, the one
    that built the engine or called the simulation function: a fixed stack
    level would count the frames of whichever route led here, a classmethod
    or a simulation function among them, and land inside the library.

    :param compute: The ``compute=`` argument the caller passed.
    :raises ComputeImportError: when the device's library is missing or does
        not import, with the import's own reason.
    :raises ComputeDeviceError: when the device is absent, reports itself
        available but fails a first small computation, or is not ``"cpu"``
        in Pyodide. With ``fallback=True`` neither is raised: the run warns
        with :class:`ComputeFallbackWarning` and goes to NumPy.
    :raises ValueError: when the request names a host: a backend is always
        this machine's.
    """
    request = _requested(compute)
    if request.host is not None:
        msg = (
            f"host {request.host!r} reached the backend of an engine built here; "
            "only fdtd_simulation and elastic_fdtd_simulation run on a node"
        )
        raise ValueError(msg)
    try:
        return _load(request)
    except (ComputeImportError, ComputeDeviceError) as exc:
        if not request.fallback:
            raise
        warnings.warn(
            f"{exc}; running on NumPy instead (fallback=True)",
            ComputeFallbackWarning,
            skip_file_prefixes=(_PACKAGE_PREFIX,),
        )
        return LOADERS["cpu"](Compute(dtype=request.dtype))
