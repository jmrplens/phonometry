#  Copyright (c) 2026. Jose M. Requena-Plens
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

from typing import Any, Literal

#: Supported rendering languages. English is the default everywhere.
Language = Literal["en", "es"]

_VALID_LANGUAGES = ("en", "es")


def check_language(language: str) -> Language:
    """Return ``language`` if supported, else raise a clear :class:`ValueError`."""
    if language not in _VALID_LANGUAGES:
        raise ValueError(
            f"Unknown language {language!r}; supported languages are "
            f"{_VALID_LANGUAGES}."
        )
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
    :return: The formatted string.
    """
    text = f"{float(value):.{decimals}f}"
    if trim and decimals > 0:
        text = text.rstrip("0").rstrip(".")
    if language == "es":
        text = text.replace(".", ",")
    return text


def decimal_comma(value: str, language: str = "en") -> str:
    """Swap the decimal point of an already-formatted number for the locale.

    Useful when a number was produced by an ``f"{x:.2f}"`` literal and only its
    separator needs localising. English is returned unchanged.
    """
    return value.replace(".", ",") if language == "es" else value


def localize_axes(ax: Any, language: str = "en") -> None:
    """Localise the tick-label decimal separator of ``ax`` for the language.

    For Spanish, both axes' major tick labels are reformatted so decimals use a
    comma (e.g. ``2.5 -> 2,5``); logarithmic and category axes that already emit
    plain labels are left alone. English is a no-op, so English figures are
    unchanged. Call it at the end of a plot function, after the data is drawn.
    """
    if language != "es":
        return
    from matplotlib.ticker import FuncFormatter, NullFormatter

    def _comma(x: float, _pos: int) -> str:
        # Match matplotlib's default compact formatting, then swap the point.
        text = f"{x:g}"
        return text.replace(".", ",")

    for axis in (ax.xaxis, ax.yaxis):
        # Leave axes whose labels are not plain numbers (log/symlog with the
        # default LogFormatter, or fixed category labels) untouched.
        if axis.get_scale() != "linear":
            continue
        if isinstance(axis.get_major_formatter(), NullFormatter):
            continue
        axis.set_major_formatter(FuncFormatter(_comma))
