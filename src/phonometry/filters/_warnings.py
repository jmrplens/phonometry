#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The filter bank's warning, defined where both of its emitters can import it.

The bank designs its bands from :mod:`phonometry.filters.frequencies`, which
drops a band above the Nyquist frequency with this warning, and
:mod:`phonometry.filters.core` imports that module; the class lives here so
neither has to import the other to name it. It is published by
:mod:`phonometry.filters` and documented with the bank.
"""

from __future__ import annotations

from .._internal.warnings import PhonometryWarning, published_by

__all__ = ["FilterBankWarning"]


@published_by("phonometry.filters")
class FilterBankWarning(PhonometryWarning):
    """A fractional-octave filter bank asked for something it cannot honour.

    Emitted when limits the caller gave hold a band above the Nyquist
    frequency of the sample rate, which is dropped from the bank, and when a
    stateful bank is asked to detrend its blocks, which introduces a step
    between them.
    """
