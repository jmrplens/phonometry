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
never at import. Its grammar is ``device[:index][,option...]`` with the
options ``float32``, ``float64`` and ``fallback``: ``cupy``, ``cupy:1``,
``torch:cuda:1,fallback``, ``torch:mps,float32``.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, Literal, get_args

import numpy as np

from .._internal.display import RichDisplay
from .._internal.validation import require_choice, require_count
from .._internal.warnings import PhonometryWarning

if TYPE_CHECKING:
    from collections.abc import Iterator

__all__ = [
    "Compute",
    "ComputeDeviceError",
    "ComputeFallbackWarning",
    "ComputeImportError",
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


class ComputeImportError(ImportError):
    """The library a requested device needs is not installed, or does not import."""


class ComputeDeviceError(RuntimeError):
    """A requested device is not present or cannot be used."""


class ComputeFallbackWarning(PhonometryWarning):
    """A requested device was not available and the run went to NumPy."""


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
    :raises TypeError: for a ``device`` or ``dtype`` that is not text, a
        ``device_index`` that is not a number (a bool is not one), or a
        ``fallback`` that is not ``True`` or ``False``.
    :raises ValueError: for an unknown device or dtype, ``"torch:mps"`` in
        float64, an index on a device that has one instance, an index that
        is not a whole number of 0 or more, or a fallback asked of ``"cpu"``.
    """

    device: Device = "cpu"
    device_index: int = 0
    dtype: Dtype = "float64"
    fallback: bool = False

    def __post_init__(self) -> None:
        """Refuse a request that cannot mean anything, before any device is probed."""
        require_choice(self.device, "device", _DEVICES)
        require_choice(self.dtype, "dtype", _DTYPES)
        # Held as an int, so a whole float or a NumPy integer reaches the
        # array library as the plain index it takes.
        index = require_count(self.device_index, "device_index", at_least=0)
        object.__setattr__(self, "device_index", index)
        if not isinstance(self.fallback, bool | np.bool_):
            # "no" is truthy: read as a flag it would turn on the fallback
            # the caller meant to refuse.
            msg = f"'fallback' must be True or False, got {self.fallback!r}."
            raise TypeError(msg)
        object.__setattr__(self, "fallback", bool(self.fallback))
        if self.device == _TORCH_MPS and self.dtype == "float64":
            msg = "device 'torch:mps' needs dtype='float32': MPS has no float64"
            raise ValueError(msg)
        if self.device in _SINGLE and self.device_index != 0:
            msg = f"device {self.device!r} has no device index; leave device_index at 0"
            raise ValueError(msg)
        if self.device == "cpu" and self.fallback:
            msg = "device 'cpu' is already the fallback; fallback=True means nothing there"
            raise ValueError(msg)


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
    :raises TypeError: for a ``device`` or ``dtype`` that is not text, a
        ``device_index`` that is not a number (a bool is not one), a
        ``numpy_version`` that is not text, or a ``host``,
        ``array_library``, ``cuda_runtime``, ``cuda_driver_api`` or ``gpu``
        that is neither text nor ``None``.
    :raises ValueError: for an unknown device or dtype, or an index that is
        not a whole number of 0 or more.
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

    def __post_init__(self) -> None:
        """Refuse a record no run could have written, as :class:`Compute` does."""
        require_choice(self.device, "device", _DEVICES)
        require_choice(self.dtype, "dtype", _DTYPES)
        # Held as an int, as Compute holds it.
        index = require_count(self.device_index, "device_index", at_least=0)
        object.__setattr__(self, "device_index", index)
        if not isinstance(self.numpy_version, str):
            msg = f"'numpy_version' must be a text, got {self.numpy_version!r}."
            raise TypeError(msg)
        for name in _OPTIONAL_TEXTS:
            value = getattr(self, name)
            if value is not None and not isinstance(value, str):
                msg = f"'{name}' must be a text or None, got {value!r}."
                raise TypeError(msg)


#: The fields of a :class:`RunProvenance` that hold a text, or ``None`` where
#: the run had nothing to record.
_OPTIONAL_TEXTS = ("host", "array_library", "cuda_runtime", "cuda_driver_api", "gpu")


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


def _requested(compute: Compute | None) -> Compute:
    """The placement asked for: the argument, :func:`use`, the environment, NumPy."""
    if compute is not None:
        if not isinstance(compute, Compute):
            msg = f"compute must be a Compute record or None; got {type(compute).__name__}"
            raise TypeError(msg)
        return compute
    ambient = _AMBIENT.get()
    if ambient is not None:
        return ambient
    text = os.environ.get(_ENV_VAR, "").strip()
    return _parse_environment(text) if text else Compute()


def _parse_environment(text: str) -> Compute:
    """Read a ``PHONOMETRY_COMPUTE`` value: ``device[:index][,option...]``.

    :raises ValueError: naming the variable, for anything the grammar does
        not describe, an option given twice, two dtypes, or a record
        :class:`Compute` refuses.
    """
    head, *options = [part.strip() for part in text.split(",")]
    device, index = _parse_device(head, text)
    dtype, fallback = _parse_options(options, text)
    try:
        return Compute(
            device=device, device_index=index, dtype=dtype, fallback=fallback
        )
    except ValueError as exc:
        msg = f"{_ENV_VAR}={text!r}: {exc}"
        raise ValueError(msg) from None


def _parse_device(head: str, text: str) -> tuple[Device, int]:
    """The device and index the first part of a ``PHONOMETRY_COMPUTE`` value names.

    :param head: The part before the first comma, ``cupy`` or ``cupy:1``.
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
