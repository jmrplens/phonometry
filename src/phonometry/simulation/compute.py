#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Where an FDTD simulation runs: the device, its dtype and what to do if absent.

A :class:`Compute` record is a request. Building one imports and probes
nothing, so a record naming a GPU can be written on a machine without one;
the engine checks the request when it is built. The request comes from the
``compute=`` argument, else from the innermost :func:`use` block, else from
the ``PHONOMETRY_COMPUTE`` environment variable, else it is NumPy in float64.

:func:`use` holds its record in a context variable. Whether a new thread or
process sees it depends on how it is started; give a worker its placement
through ``compute=`` or ``PHONOMETRY_COMPUTE``.

The environment variable is read when a computation resolves its placement,
never at import. Its grammar is ``device[:index][@host][,option...]`` with the
options ``float32``, ``float64`` and ``fallback``: ``cupy``, ``cupy:1``,
``torch:cuda:1,fallback``, ``torch:mps,float32``, ``cupy@nas``. A host is a
name in the hosts file (see the guide on remote nodes); only
:func:`~phonometry.simulation.fdtd_simulation` and
:func:`~phonometry.simulation.elastic_fdtd_simulation` run on one.
"""

from __future__ import annotations

import os
import re
import threading
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, Literal, cast, get_args

import numpy as np

from .._internal.display import RichDisplay
from .._internal.validation import require_choice, require_count, require_positive
from .._internal.warnings import PhonometryWarning

if TYPE_CHECKING:
    from collections.abc import Iterator

__all__ = [
    "Compute",
    "ComputeDeviceError",
    "ComputeFallbackWarning",
    "ComputeImportError",
    "ComputeRemoteError",
    "RunProvenance",
    "use",
]

#: A device an engine can step on, named with the library that drives it.
Device = Literal["cpu", "cupy", "torch:cpu", "torch:cuda", "torch:mps"]
#: The floating-point type of every field.
Dtype = Literal["float64", "float32"]

_DEVICES: tuple[Device, ...] = get_args(Device)
_DTYPES: tuple[Dtype, ...] = get_args(Dtype)
#: torch on the host's CPU, and on Apple silicon, which has no float64.
_TORCH_CPU: Final = "torch:cpu"
_TORCH_MPS: Final = "torch:mps"
#: Devices with one instance per machine, where an index means nothing.
_SINGLE: tuple[Device, ...] = ("cpu", _TORCH_CPU, _TORCH_MPS)

#: The environment variable that names a default placement.
_ENV_VAR = "PHONOMETRY_COMPUTE"
#: A host as the hosts file names it: letters, digits, ".", "_" and "-",
#: starting with a letter or a digit, up to 64 characters. Never an ssh
#: destination: ``user@address`` belongs in the file, not in the request.
_HOST_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
#: A package digest: the SHA-256 of a package's files, in lowercase hex.
_DIGEST = re.compile(r"[0-9a-f]{64}")
#: Where a placement came from, which a refusal names.
_Source = Literal["argument", "use", "environment", "default"]
#: The record of a whole simulation and the function that runs it, by
#: engine: what runs on a node.
_RUNS_THERE = MappingProxyType(
    {
        "FDTD2D": ("FDTDRun", "fdtd_simulation"),
        "ElasticFDTD2D": ("ElasticRun", "elastic_fdtd_simulation"),
    }
)


class ComputeImportError(ImportError):
    """The library a requested device needs is not installed, or does not import."""


class ComputeDeviceError(RuntimeError):
    """A requested device is not present or cannot be used."""


class ComputeFallbackWarning(PhonometryWarning):
    """A requested device was not available and the run went to NumPy."""


class ComputeRemoteError(RuntimeError):
    """A run sent to a node failed in the connection or on the node.

    Raised for a transport failure (no ssh client on ``PATH``, where on
    Windows one in the working directory does not count, a node that cannot
    be reached, a stream that breaks the protocol, a run past its timeout) and
    for a failure on the node (an image or a Python environment that cannot
    run the package, an exception raised by the run itself). A wrong
    argument is never one: it raises its own ``TypeError`` or ``ValueError``
    before anything connects.

    :ivar host: The node's name in the hosts file.
    :ivar node_traceback: The traceback the node printed, as text, when the
        run raised there; it is also attached as a note, so a traceback
        printed here shows it.
    """

    def __init__(
        self,
        message: str,
        *,
        host: str | None = None,
        node_traceback: str | None = None,
    ) -> None:
        super().__init__(message)
        self.host = host
        self.node_traceback = node_traceback
        if node_traceback:
            self.add_note(f"Traceback on node {host!r}:\n{node_traceback}")


def _placement_index(device: Device, dtype: Dtype, device_index: int) -> int:
    """The device index as an int, once the placement is one a run can step on.

    Shared by :class:`Compute`, the request, and :class:`RunProvenance`, the
    record of a run, so a record rebuilt by hand cannot hold a placement no
    request could have asked for. The index is held as an int, so a whole
    float or a NumPy integer reaches the array library as the plain index it
    takes.

    :raises TypeError: for a ``device_index`` that is not a number (a bool
        is not one).
    :raises ValueError: for an index that is not a whole number of 0 or
        more, ``"torch:mps"`` in float64, or an index other than 0 on a
        device that has one instance.
    """
    index = require_count(device_index, "device_index", at_least=0)
    if device == _TORCH_MPS and dtype == "float64":
        msg = "device 'torch:mps' needs dtype='float32': MPS has no float64"
        raise ValueError(msg)
    if device in _SINGLE and index != 0:
        msg = f"device {device!r} has no device index; leave device_index at 0"
        raise ValueError(msg)
    return index


@dataclass(frozen=True, kw_only=True)
class Compute(RichDisplay):
    """Where an FDTD simulation steps, in which dtype, and whether it may fall back.

    :param device: The array library and device: ``"cpu"`` (NumPy, the
        default), ``"cupy"`` (an NVIDIA GPU through CuPy), ``"torch:cpu"``,
        ``"torch:cuda"`` or ``"torch:mps"`` (Apple silicon, float32 only).
    :param device_index: Which GPU, for ``"cupy"`` and ``"torch:cuda"``.
    :param dtype: ``"float64"`` (default) or ``"float32"``.
    :param fallback: Run on NumPy, with a :class:`ComputeFallbackWarning`,
        when the device is not available, instead of raising.
    :param host: The node the run goes to, by its name in the hosts file, or
        ``None`` (default) to run on this machine. Only
        :func:`~phonometry.simulation.fdtd_simulation` and
        :func:`~phonometry.simulation.elastic_fdtd_simulation` run on a node;
        an engine built here refuses a host.
    :param timeout_s: The longest a remote run may take, from connecting to
        the result [s], or ``None`` for the hosts file's value (no limit when
        the file names none). Only with a ``host``.
    :raises TypeError: for a ``device`` or ``dtype`` that is not text, a
        ``device_index`` that is not a number (a bool is not one), a
        ``fallback`` that is not ``True`` or ``False``, a ``host`` that is
        neither text nor ``None``, or a ``timeout_s`` that is not one number.
    :raises ValueError: for an unknown device or dtype, ``"torch:mps"`` in
        float64, an index on a device that has one instance, an index that
        is not a whole number of 0 or more, a ``host`` that is not a name the
        hosts file can hold, a ``timeout_s`` without a host, not positive or
        longer than a timer here can wait (``threading.TIMEOUT_MAX``), or a
        fallback asked of ``"cpu"`` on this machine.
    """

    device: Device = "cpu"
    device_index: int = 0
    dtype: Dtype = "float64"
    fallback: bool = False
    host: str | None = None
    timeout_s: float | None = None

    def __post_init__(self) -> None:
        """Refuse a request that cannot mean anything, before any device is probed."""
        require_choice(self.device, "device", _DEVICES)
        require_choice(self.dtype, "dtype", _DTYPES)
        index = _placement_index(self.device, self.dtype, self.device_index)
        object.__setattr__(self, "device_index", index)
        if not isinstance(self.fallback, bool | np.bool_):
            # "no" is truthy: read as a flag it would turn on the fallback
            # the caller meant to refuse.
            msg = f"'fallback' must be True or False, got {self.fallback!r}."
            raise TypeError(msg)
        object.__setattr__(self, "fallback", bool(self.fallback))
        object.__setattr__(self, "host", _checked_host(self.host))
        object.__setattr__(
            self, "timeout_s", _checked_timeout(self.timeout_s, self.host)
        )
        if self.device == "cpu" and self.fallback and self.host is None:
            msg = "device 'cpu' is already the fallback; fallback=True means nothing there"
            raise ValueError(msg)


def _checked_host(host: object) -> str | None:
    """The ``host`` of a request: ``None``, or a name the hosts file can hold.

    :raises TypeError: for a host that is neither text nor ``None``.
    :raises ValueError: for a name the hosts file cannot hold, an ssh
        destination such as ``user@address`` among them.
    """
    if host is None:
        return None
    if not isinstance(host, str):
        msg = f"'host' must be a name from the hosts file or None, got {host!r}."
        raise TypeError(msg)
    if _HOST_NAME.fullmatch(host) is None:
        msg = (
            "'host' must be a name from the hosts file: letters, digits, '.', "
            f"'_' and '-', starting with a letter or a digit; got {host!r}."
        )
        raise ValueError(msg)
    return host


def _checked_timeout(timeout_s: object, host: str | None) -> float | None:
    """The ``timeout_s`` of a request, which only a remote run has.

    :raises TypeError: for a timeout that is not one number (a bool is not
        one).
    :raises ValueError: for a timeout without a host, one that is not
        positive and finite, or one longer than a timer here can wait
        (``threading.TIMEOUT_MAX``).
    """
    if timeout_s is None:
        return None
    if host is None:
        msg = "'timeout_s' bounds a remote run; it needs a host"
        raise ValueError(msg)
    if isinstance(timeout_s, bool | np.bool_):
        # float(True) is 1.0: read as a number it would bound the run to 1 s.
        msg = f"'timeout_s' must be one number, not a bool; got {timeout_s!r}."
        raise TypeError(msg)
    seconds = require_positive(cast("float", timeout_s), "timeout_s")
    if seconds > threading.TIMEOUT_MAX:
        # The timer that stops a remote run would die on a longer one, and
        # the run would have no timeout at all.
        msg = (
            f"'timeout_s' must be at most {int(threading.TIMEOUT_MAX)} s, the "
            f"longest a timer here waits; got {timeout_s!r}."
        )
        raise ValueError(msg)
    return seconds


@dataclass(frozen=True, kw_only=True)
class RunProvenance(RichDisplay):
    """Where a run actually stepped, recorded by the result.

    :ivar host: The node the run went to, or ``None`` for this machine.
    :ivar device: The device that stepped the fields.
    :ivar device_index: Which GPU, ``0`` where there is one.
    :ivar dtype: The dtype of the fields.
    :ivar numpy_version: NumPy's version where the run stepped.
    :ivar array_library: The array library and its version (``"cupy 14.2.0"``),
        or ``None`` for NumPy.
    :ivar cuda_runtime: The CUDA runtime the array library uses, as
        ``"major.minor"`` (``"13.2"``), or ``None`` off a CUDA device.
    :ivar cuda_driver_api: The CUDA version the GPU driver supports, as
        ``"major.minor"`` (``"13.3"``), where the array library reports it
        (CuPy), else ``None``. It is not the NVIDIA driver's own version.
    :ivar gpu: The GPU's name, or ``None``.
    :ivar package_sha256: The SHA-256 of the package the node ran, in
        lowercase hex, or ``None`` for a run on this machine.
    :raises TypeError: for a ``device`` or ``dtype`` that is not text, a
        ``device_index`` that is not a number (a bool is not one), a
        ``numpy_version`` that is not text, or a ``host``,
        ``array_library``, ``cuda_runtime``, ``cuda_driver_api``, ``gpu`` or
        ``package_sha256`` that is neither text nor ``None``.
    :raises ValueError: for an unknown device or dtype, ``"torch:mps"`` in
        float64, an index on a device that has one instance, an index that
        is not a whole number of 0 or more, or a ``package_sha256`` that is
        not 64 lowercase hexadecimal digits.
    """

    host: str | None
    device: Device
    device_index: int
    dtype: Dtype
    numpy_version: str
    array_library: str | None
    cuda_runtime: str | None
    cuda_driver_api: str | None
    gpu: str | None
    package_sha256: str | None

    def __post_init__(self) -> None:
        """Refuse a record no run could have written, as :class:`Compute` does."""
        require_choice(self.device, "device", _DEVICES)
        require_choice(self.dtype, "dtype", _DTYPES)
        index = _placement_index(self.device, self.dtype, self.device_index)
        object.__setattr__(self, "device_index", index)
        if not isinstance(self.numpy_version, str):
            msg = f"'numpy_version' must be a text, got {self.numpy_version!r}."
            raise TypeError(msg)
        for name in _OPTIONAL_TEXTS:
            value = getattr(self, name)
            if value is not None and not isinstance(value, str):
                msg = f"'{name}' must be a text or None, got {value!r}."
                raise TypeError(msg)
        if (
            self.package_sha256 is not None
            and _DIGEST.fullmatch(self.package_sha256) is None
        ):
            msg = f"'package_sha256' must be 64 lowercase hexadecimal digits, got {self.package_sha256!r}."
            raise ValueError(msg)


#: The fields of a :class:`RunProvenance` that hold a text, or ``None`` where
#: the run had nothing to record.
_OPTIONAL_TEXTS = (
    "host",
    "array_library",
    "cuda_runtime",
    "cuda_driver_api",
    "gpu",
    "package_sha256",
)


_AMBIENT: ContextVar[Compute | None] = ContextVar("phonometry_compute", default=None)


@contextmanager
def use(compute: Compute) -> Iterator[Compute]:
    """Make *compute* the placement of every simulation built in this block.

    The record lives in a context variable. Whether a new thread or process
    sees it depends on how it is started; give a worker its placement through
    ``compute=`` or ``PHONOMETRY_COMPUTE``.

    :param compute: The placement.
    :raises TypeError: for anything but a :class:`Compute`.
    """
    if not isinstance(compute, Compute):
        msg = f"use() takes a Compute record; got {type(compute).__name__}"
        raise TypeError(msg)
    token = _AMBIENT.set(compute)
    try:
        yield compute
    finally:
        _AMBIENT.reset(token)


def _requested_from(compute: Compute | None) -> tuple[Compute, _Source]:
    """The placement asked for and where it came from.

    The argument, else the innermost :func:`use` block, else the
    environment, else NumPy.
    """
    if compute is not None:
        if not isinstance(compute, Compute):
            msg = f"compute must be a Compute record or None; got {type(compute).__name__}"
            raise TypeError(msg)
        return compute, "argument"
    ambient = _AMBIENT.get()
    if ambient is not None:
        return ambient, "use"
    text = os.environ.get(_ENV_VAR, "").strip()
    if text:
        return _parse_environment(text), "environment"
    return Compute(), "default"


def _requested(compute: Compute | None) -> Compute:
    """The placement asked for: the argument, :func:`use`, the environment, NumPy."""
    return _requested_from(compute)[0]


def _local_request(compute: Compute | None, *, owner: str) -> Compute:
    """The placement of an engine built here, which cannot be on a node.

    An engine steps in the caller's process, and its fields are the caller's
    to read and write between steps; a node offers neither. Only the
    simulation functions run on a node.

    :param owner: The engine's class name, which the refusal names.
    :raises ValueError: when the placement names a host, saying where the
        host came from and what to do instead.
    """
    request, source = _requested_from(compute)
    if request.host is None:
        return request
    named = {
        "argument": "compute=",
        "use": "the use() block",
        "environment": _ENV_VAR,
    }.get(source, source)
    record, function = _RUNS_THERE.get(owner, ("a run", "its simulation function"))
    msg = (
        f"{owner} steps in this process and cannot run on a node, but "
        f"{named} names host {request.host!r}: pass "
        f"compute=Compute(device={request.device!r}) to step here, or call "
        f"{function}({record}(...), compute=...) to run the whole simulation there"
    )
    raise ValueError(msg)


def _strip_host(text: str) -> str:
    """A ``PHONOMETRY_COMPUTE`` value with its ``@host`` taken out.

    A node runs what it is sent on itself; a host left in its own
    environment would send a run there on to the node it names.
    """
    head, comma, options = text.partition(",")
    return head.partition("@")[0].strip() + comma + options


def _parse_environment(text: str) -> Compute:
    """Read a ``PHONOMETRY_COMPUTE`` value: ``device[:index][@host][,option...]``.

    :raises ValueError: naming the variable, for anything the grammar does
        not describe, an empty host, an option given twice, two dtypes, or a
        record :class:`Compute` refuses.
    """
    head, *options = [part.strip() for part in text.split(",")]
    device_text, at, host = head.partition("@")
    if at and not host.strip():
        msg = f"{_ENV_VAR}={text!r}: the host after '@' is empty"
        raise ValueError(msg)
    device, index = _parse_device(device_text.strip(), text)
    dtype, fallback = _parse_options(options, text)
    try:
        return Compute(
            device=device,
            device_index=index,
            dtype=dtype,
            fallback=fallback,
            host=host.strip() or None,
        )
    except ValueError as exc:
        msg = f"{_ENV_VAR}={text!r}: {exc}"
        raise ValueError(msg) from None


def _parse_device(head: str, text: str) -> tuple[Device, int]:
    """The device and index the first part of a ``PHONOMETRY_COMPUTE`` value names.

    :param head: The part before the first comma and the ``@``, ``cupy`` or
        ``cupy:1``.
    :param text: The whole value, which a refusal names.
    :raises ValueError: for a device the grammar does not name, or an index
        that is not a whole number.
    """
    # The loop variable is the device itself, typed as one, so the record is
    # built from a Device and not from the text that named it.
    for device in _DEVICES:
        if head == device:
            return device, 0
        prefix = f"{device}:"
        if head.startswith(prefix) and device not in _SINGLE:
            digits = head[len(prefix) :]
            # ASCII only: ``str.isdigit`` also accepts "²", which int() refuses.
            if not (digits.isascii() and digits.isdigit()):
                msg = f"{_ENV_VAR}={text!r}: the index after {device!r} must be a whole number"
                raise ValueError(msg)
            return device, int(digits)
    msg = f"{_ENV_VAR}={text!r}: the device must be one of {_DEVICES}, with an index for cupy and torch:cuda"
    raise ValueError(msg)


def _parse_options(options: list[str], text: str) -> tuple[Dtype, bool]:
    """The dtype and the fallback the options of a ``PHONOMETRY_COMPUTE`` value set.

    :param options: The parts after the first comma, stripped.
    :param text: The whole value, which a refusal names.
    :return: ``(dtype, fallback)``, float64 and no fallback by default.
    :raises ValueError: for an unknown option, an option given twice, or two
        dtypes.
    """
    dtype: Dtype | None = None
    fallback = False
    seen: set[str] = set()
    for option in options:
        if option in seen:
            msg = f"{_ENV_VAR}={text!r}: the option {option!r} is given twice"
            raise ValueError(msg)
        seen.add(option)
        if option in _DTYPES:
            # The last of two dtypes would win in silence: refuse the pair.
            if dtype is not None:
                msg = (
                    f"{_ENV_VAR}={text!r}: one dtype, {dtype!r} or {option!r}, not both"
                )
                raise ValueError(msg)
            dtype = require_choice(option, "dtype", _DTYPES)
        elif option == "fallback":
            fallback = True
        else:
            msg = f"{_ENV_VAR}={text!r}: unknown option {option!r}; the options are float32, float64 and fallback"
            raise ValueError(msg)
    return ("float64" if dtype is None else dtype), fallback
