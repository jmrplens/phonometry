#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The arguments of a simulation, as data that travels to a node (private).

A remote run sends the library function's name and its arguments, never
code: numbers, texts, arrays, and the library's own records (the two runs,
the sources, the two recordings and the elastic boundaries) field by field,
rebuilt on the node through their constructors, so a run checks itself
again there. A waveform travels only as the bound ``.value`` of a
GaussianPulse, CWSource or SignalSource of exactly that type, which the
node rebuilds from the record; any other callable is refused with a
TypeError that names the argument, before a connection is opened.

The frame and the video options of a video job (AnimationFrame and
VideoOptions) are the library's own records too, and travel the same way:
rebuilt on the node, they check their fields again there.

The form is JSON with tagged objects, ``{"$": tag, ...}``, and a list of
raw buffers for the arrays, little-endian and in C order. Nothing is
pickled, so a node never runs code it was sent as data, and a number keeps
its type and every bit: a float travels as its hexadecimal form, a NumPy
scalar with its dtype.
"""

from __future__ import annotations

import dataclasses
import inspect
from collections.abc import Callable, Mapping, Sequence
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np

from ...io._video import VideoOptions
from .. import elastic_fdtd, fdtd
from ..video import AnimationFrame

if TYPE_CHECKING:
    from numpy.typing import NDArray

#: A tagged wire object, as ``json.loads`` gives it back.
_Form = dict[str, Any]
#: The widest float that travels bit for bit [bytes]: a ``long double`` is
#: refused rather than rounded.
_WIDEST_FLOAT_BYTES = 8

#: The records that travel, by name: exactly these classes, not subclasses.
_RECORDS: Mapping[str, type] = MappingProxyType(
    {
        cls.__name__: cls
        for cls in (
            fdtd.FDTDRun,
            elastic_fdtd.ElasticRun,
            fdtd.GaussianPulse,
            fdtd.CWSource,
            fdtd.SignalSource,
            fdtd.PlaneWaveSource,
            fdtd.FDTDRecording,
            elastic_fdtd.ExplosionSource,
            elastic_fdtd.ForceSource,
            elastic_fdtd.ElasticRecording,
            elastic_fdtd.ElasticBoundaries,
            AnimationFrame,
            VideoOptions,
        )
    }
)
#: The records whose bound ``value`` travels as a waveform.
_WAVEFORM_OWNERS: tuple[type, ...] = (
    fdtd.GaussianPulse,
    fdtd.CWSource,
    fdtd.SignalSource,
)
#: Marks a value :func:`_leaf` does not take.
_NOT_A_LEAF = object()
#: The integers that travel, those of an int64: JSON carries them whole,
#: where Python writes no integer of more than 4300 digits.
_INT64_MIN = -(2**63)
_INT64_MAX = 2**63 - 1


def encode_arguments(
    arguments: Mapping[str, object],
) -> tuple[dict[str, object], list[memoryview]]:
    """*arguments* as JSON-ready data, and the raw buffers of their arrays.

    :raises TypeError: naming the argument, for a value that cannot travel:
        a callable other than the ``value`` of a GaussianPulse, CWSource or
        SignalSource, a subclass of a library record, an integer outside
        the 64-bit range, an array of anything but booleans, integers or
        floats of up to 64 bits, a mapping with a key that is not text, or
        any other object a node could not rebuild.
    """
    buffers: list[memoryview] = []
    tree = {name: _encode(value, name, buffers) for name, value in arguments.items()}
    return tree, buffers


def _encode(value: object, where: str, buffers: list[memoryview]) -> object:
    leaf = _leaf(value, where, buffers)
    if leaf is not _NOT_A_LEAF:
        return leaf
    if _is_record(value, where):
        return _record(value, where, buffers)
    if callable(value):
        return _waveform(value, where, buffers)
    return _container(value, where, buffers)


def _leaf(value: object, where: str, buffers: list[memoryview]) -> object:
    """The wire form of a number, a text, ``None`` or an array, or :data:`_NOT_A_LEAF`."""
    if value is None or isinstance(value, bool | str):
        return value
    if isinstance(value, np.generic):
        return _scalar(value, where)
    if isinstance(value, float):
        return {"$": "float", "hex": value.hex()}
    if isinstance(value, int):
        if not _INT64_MIN <= value <= _INT64_MAX:
            # The value is not quoted: Python refuses to write an integer of
            # more than 4300 digits as text.
            msg = (
                f"{where} cannot travel to a node: the integer is outside the "
                f"int64 range a node takes, {_INT64_MIN} to {_INT64_MAX}"
            )
            raise TypeError(msg)
        return value
    if isinstance(value, np.ndarray):
        return _array(value, where, buffers)
    return _NOT_A_LEAF


def _travels(dtype: np.dtype[Any]) -> bool:
    """Whether numbers of *dtype* travel bit for bit: booleans, integers, floats up to 64 bits."""
    return dtype.kind in "biu" or (
        dtype.kind == "f" and dtype.itemsize <= _WIDEST_FLOAT_BYTES
    )


def _scalar(value: np.generic, where: str) -> _Form:
    if not _travels(value.dtype):
        msg = f"{where} cannot travel to a node: a {value.dtype} number is not one it can rebuild"
        raise TypeError(msg)
    if value.dtype.kind == "f":
        return {"$": "scalar", "dtype": value.dtype.name, "hex": float(value).hex()}
    return {"$": "scalar", "dtype": value.dtype.name, "value": value.item()}


def _array(value: NDArray[Any], where: str, buffers: list[memoryview]) -> _Form:
    if not _travels(value.dtype):
        msg = (
            f"{where} cannot travel to a node: an array of {value.dtype} "
            "is not one of numbers it can rebuild"
        )
        raise TypeError(msg)
    little = np.ascontiguousarray(value, dtype=value.dtype.newbyteorder("<"))
    # Flattened before the byte view: a view of another item size is refused
    # on an array of no dimension.
    buffers.append(memoryview(little.reshape(-1).view(np.uint8)))
    return {
        "$": "array",
        "dtype": little.dtype.str,
        "shape": list(value.shape),
        "buffer": len(buffers) - 1,
    }


def _is_record(value: object, where: str) -> bool:
    """Whether *value* is a library record that travels; a subclass of one is refused."""
    exact = _RECORDS.get(type(value).__name__)
    if exact is not None and type(value) is exact:
        return True
    for record in _RECORDS.values():
        if isinstance(value, record):
            msg = (
                f"{where} cannot travel to a node: {type(value).__name__} is a "
                f"subclass of {record.__name__}, and only the library's own records travel"
            )
            raise TypeError(msg)
    return False


def _record(value: object, where: str, buffers: list[memoryview]) -> _Form:
    fields = {
        f.name: _encode(getattr(value, f.name), f"{where}.{f.name}", buffers)
        for f in dataclasses.fields(value)  # type: ignore[arg-type]
        if f.init
    }
    return {"$": "record", "type": type(value).__name__, "fields": fields}


def _waveform(
    value: Callable[..., object], where: str, buffers: list[memoryview]
) -> _Form:
    owner = getattr(value, "__self__", None)
    if (
        inspect.ismethod(value)
        and type(owner) in _WAVEFORM_OWNERS
        and value.__func__ is getattr(type(owner), "value", None)
    ):
        return {"$": "waveform", "of": _record(owner, f"{where}.__self__", buffers)}
    msg = (
        f"{where} cannot travel to a node: only the .value of a GaussianPulse, "
        f"CWSource or SignalSource can, and {value!r} is not one; run it here, "
        "without a host"
    )
    raise TypeError(msg)


def _container(value: object, where: str, buffers: list[memoryview]) -> _Form:
    if isinstance(value, Mapping):
        items = []
        for key, item in value.items():
            if not isinstance(key, str):
                msg = f"{where} cannot travel to a node: its key {key!r} is not a text"
                raise TypeError(msg)
            items.append([key, _encode(item, f"{where}[{key!r}]", buffers)])
        return {"$": "dict", "items": items}
    if isinstance(value, Sequence) and not isinstance(
        value, bytes | bytearray | memoryview
    ):
        tag = "tuple" if isinstance(value, tuple) else "list"
        return {
            "$": tag,
            "items": [
                _encode(item, f"{where}[{k}]", buffers) for k, item in enumerate(value)
            ],
        }
    msg = (
        f"{where} cannot travel to a node: a {type(value).__name__} "
        "is not data a node can rebuild"
    )
    raise TypeError(msg)


def decode_arguments(
    tree: Mapping[str, object], buffers: Sequence[bytes | bytearray]
) -> dict[str, object]:
    """The arguments *tree* and *buffers* carry, as the caller passed them.

    :raises ValueError: for a value that is none of the tagged forms, or for
        numbers of a type that does not travel. A record rebuilt from its
        fields raises what its constructor raises for them.
    """
    return {name: _decode(node, buffers) for name, node in tree.items()}


def _decode(node: object, buffers: Sequence[bytes | bytearray]) -> object:
    if node is None or isinstance(node, bool | int | str):
        return node
    if (
        not isinstance(node, dict)
        or not isinstance(node.get("$"), str)
        or node["$"] not in _DECODERS
    ):
        msg = f"not a wire form: {node!r:.80}"
        raise ValueError(msg)
    return _DECODERS[node["$"]](node, buffers)


def _number_type(node: _Form) -> np.dtype[Any]:
    """The dtype *node* names, one of those the encoder sends."""
    dtype = np.dtype(node["dtype"])
    if not _travels(dtype):
        msg = f"not a wire form: numbers of {dtype} do not travel"
        raise ValueError(msg)
    return dtype


def _decode_scalar(node: _Form, _buffers: Sequence[bytes | bytearray]) -> object:
    kind = _number_type(node).type
    return kind(float.fromhex(node["hex"])) if "hex" in node else kind(node["value"])


def _decode_array(node: _Form, buffers: Sequence[bytes | bytearray]) -> object:
    dtype = _number_type(node)
    flat = np.frombuffer(buffers[node["buffer"]], dtype=dtype)
    return flat.reshape(node["shape"]).astype(dtype.newbyteorder("="), copy=False)


def _decode_record(node: _Form, buffers: Sequence[bytes | bytearray]) -> object:
    fields = {name: _decode(item, buffers) for name, item in node["fields"].items()}
    return _RECORDS[node["type"]](**fields)


_DECODERS: Mapping[str, Callable[[_Form, Sequence[bytes | bytearray]], object]] = (
    MappingProxyType(
        {
            "float": lambda node, _: float.fromhex(node["hex"]),
            "scalar": _decode_scalar,
            "array": _decode_array,
            "tuple": lambda node, b: tuple(_decode(item, b) for item in node["items"]),
            "list": lambda node, b: [_decode(item, b) for item in node["items"]],
            "dict": lambda node, b: {
                key: _decode(item, b) for key, item in node["items"]
            },
            "record": _decode_record,
            "waveform": lambda node, b: _decode(node["of"], b).value,  # type: ignore[attr-defined]
        }
    )
)
