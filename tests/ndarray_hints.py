#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The ndarray an annotation names, read the same on every NumPy the package accepts.

``numpy.typing.NDArray`` is a generic alias of ``np.ndarray`` up to NumPy 2.4
and a ``type`` statement from NumPy 2.5 on. ``typing.get_origin`` of
``NDArray[np.bool_]`` is ``np.ndarray`` on the first and the statement on the
second, so a test that asks whether an annotation's origin is ``np.ndarray``
reads every such annotation at the dependency floors and none at the versions
the CI pins, the aliases of the package (``Real = NDArray[np.float64]``)
among them. :func:`ndarray_of` reads through a ``type`` statement, numpy's or
the package's, to the ``np.ndarray[...]`` it stands for, with the arguments
of its subscript put in.
"""

from __future__ import annotations

import typing

import numpy as np

#: How many ``type`` statements an annotation is read through before it is
#: taken to name no array: an alias of the package's over numpy's is two.
_DEPTH = 8


def ndarray_of(hint: object) -> object | None:
    """The ``np.ndarray`` or ``np.ndarray[...]`` *hint* names, or ``None``.

    A ``type`` statement, subscripted or not, is read through to its value,
    the arguments of the subscript put in its parameters. A statement whose
    value names a type only a type checker imports cannot be evaluated, and
    names no array; nor does a union, which is no array alone.
    """
    for _ in range(_DEPTH):
        origin = typing.get_origin(hint)
        if hint is np.ndarray or origin is np.ndarray:
            return hint
        alias = origin if isinstance(origin, typing.TypeAliasType) else hint
        if not isinstance(alias, typing.TypeAliasType):
            return None
        try:
            value = alias.__value__
        except NameError:
            return None
        arguments = typing.get_args(hint) if alias is origin else ()
        parameters = getattr(value, "__parameters__", ())
        hint = value[arguments] if arguments and parameters else value
    return None


def ndarray_scalar(hint: object) -> object | None:
    """The scalar type of the dtype the ndarray *hint* names, or ``None``.

    ``NDArray[np.complex128]`` gives ``np.complex128`` and
    ``NDArray[np.floating[Any]]`` gives ``np.floating[Any]``; a bare
    ``np.ndarray``, or an annotation that names no array, gives ``None``.
    """
    array = ndarray_of(hint)
    arguments = typing.get_args(array) if array is not None else ()
    if not arguments:
        return None
    dtype = typing.get_args(arguments[-1])
    return dtype[0] if dtype else None
