#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Small internationalisation helpers shared by the ``.plot()`` and ``.report()``
renderers.

The library renders English by default. Passing ``language="es"`` to a result's
``plot`` or ``report`` method switches the fixed strings (titles, axis labels,
table headers, prose) to Spanish and the decimal separator to a comma, the way a
Spanish-language figure or report writes numbers. Only two things live here: the
:data:`Language` type and locale-aware number/axis formatting; the actual
translated strings live next to the renderers that use them (``_plot`` and
``_report`` each carry their own string tables).

Nothing here is a runtime dependency: :func:`localize_axes` imports matplotlib
lazily and is a no-op for English, so English plots are byte-for-byte unchanged.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from matplotlib.axes import Axes

#: Supported rendering languages. English is the default everywhere.
Language = Literal["en", "es"]

_VALID_LANGUAGES = ("en", "es")


def check_language(language: str) -> Language:
    """Return ``language`` if supported, else raise a clear :class:`ValueError`."""
    if language not in _VALID_LANGUAGES:
        msg = (
            f"Unknown language {language!r}; supported languages are "
            f"{_VALID_LANGUAGES}."
        )
        raise ValueError(msg)
    return language  # type: ignore[return-value]


def format_number(
    value: float,
    language: str = "en",
    *,
    decimals: int = 1,
    trim: bool = False,
) -> str:
    """Format ``value`` with a locale-aware decimal separator.

    :param value: The number to format.
    :param language: ``"en"`` (period) or ``"es"`` (comma).
    :param decimals: Digits after the decimal separator.
    :param trim: Drop a trailing ``.0`` / ``,0`` (and the separator) for a
        whole number, e.g. ``90.0 -> "90"``.
    :return: The formatted string. A negative value is signed with the
        typographic minus U+2212, the sign the axis tick labels beside it carry
        and the one a fiche's tables print; ``format`` writes an ASCII hyphen,
        which is a shorter, lower glyph and reads as a different mark next to
        them. A value that rounds to zero at the requested precision never keeps
        a sign at all: a tiny negative number (or a signed ``-0.0``) formats as
        ``"0.0"``, not the contradictory ``"-0.0"``.
    """
    text = f"{float(value):.{decimals}f}"
    # A formatted value whose digits are all zeros is a signed zero; strip the
    # sign by inspecting the text itself (no float equality involved).
    if text.startswith("-") and not text.strip("-0."):
        text = text[1:]
    if trim and decimals > 0:
        text = text.rstrip("0").rstrip(".")
    if language == "es":
        text = text.replace(".", ",")
    return _MINUS_RE.sub("\\1−", text, count=1)


#: The leading sign of a formatted number, and only that. The optional run in
#: front of it is the width padding of a spec like ``"8.2f"``, which puts the
#: sign after the spaces rather than at the start of the string; anchoring on
#: the string's first character alone would silently skip every padded reading,
#: which is how a readout column keeps its numbers aligned.
_MINUS_RE = re.compile(r"^([ \t]*)-")


def fmt_minus(value: float, spec: str = "") -> str:
    """Format ``value`` with ``spec``, signing it with the typographic minus.

    For the readings that are built with an explicit format spec rather than
    through :func:`format_number` -- a ``"+.1f"`` correction that must show its
    sign, a ``":g"`` that must not show trailing zeros.

    Only the leading sign is rewritten. The hyphen inside the number's own text
    (the exponent of ``1e-05``) is left alone, which is why this takes the value
    and its spec rather than the finished string: once a label is assembled
    there is no telling a minus from the hyphen of a standard designation such
    as "IEC 61672-1", of a compound name, or of a range.

    Localise afterwards, not before: :func:`decimal_comma` only touches the
    decimal point, so the order of the two is free, but the sign has to be
    settled before the string reaches a translation table keyed by the text as
    it is drawn.
    """
    return _MINUS_RE.sub("\\1−", format(value, spec), count=1)


def decimal_comma(value: str, language: str = "en") -> str:
    """Swap the decimal point of an already-formatted number for the locale.

    Useful when a number was produced by an ``f"{x:.2f}"`` literal and only its
    separator needs localising. English is returned unchanged.
    """
    return value.replace(".", ",") if language == "es" else value


def localize_axes(ax: Axes, language: str = "en") -> None:
    """Localise the tick-label decimal separator of ``ax`` for the language.

    For Spanish, every major tick label of ``ax`` is reformatted so decimals use
    a comma (e.g. ``2.5 -> 2,5``); labels that were written as text rather than
    computed from a number are left alone. English is a no-op, so English
    figures are unchanged. Call it at the end of a plot function, after the data
    is drawn, once per axes: a twin axis and a colorbar each carry their own,
    and a 3-D panel's ``z`` is reached here along with ``x`` and ``y``.
    """
    if language != "es":
        return
    from matplotlib.ticker import ScalarFormatter

    class _CommaScalarFormatter(ScalarFormatter):
        """Matplotlib's default numeric formatter with a comma separator.

        Installed as the axis formatter (not wrapped around a detached one, which
        renders blank labels), so matplotlib keeps its tick locations in sync and
        the decimal precision stays consistent, e.g. ``1,0`` and ``1,5`` rather
        than the ``1`` and ``1,5`` a bare ``{x:g}`` would produce.
        """

        def __call__(self, x: float, pos: int | None = None) -> str:
            return super().__call__(x, pos).replace(".", ",")

    axes = (ax.xaxis, ax.yaxis, getattr(ax, "zaxis", None))
    for axis in axes:
        if axis is None:
            continue
        # Only reformat an axis still using matplotlib's default auto numeric
        # formatter, which is the one that writes a decimal separator of its
        # own. The formatter is what decides this, not the scale: a log axis
        # given a plain ScalarFormatter (a decade axis of distances, say) writes
        # ``0.10 1.00 10.00`` and needs the comma exactly as a linear one does,
        # while a log axis left with its LogFormatter, a category axis whose
        # text was installed by ``set_xticklabels`` (a FuncFormatter mapping
        # positions to fixed strings) and a frequency axis whose octave centres
        # were pinned by ``format_frequency_axis`` all emit text the comma
        # formatter would overwrite with bare positions. Testing the exact type
        # also leaves an already localised axis alone.
        if type(axis.get_major_formatter()) is not ScalarFormatter:
            continue
        axis.set_major_formatter(_CommaScalarFormatter())
