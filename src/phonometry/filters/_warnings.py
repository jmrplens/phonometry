#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The filter bank's warning, defined where both of its emitters can import it.

The bank designs its bands from :mod:`phonometry.filters.frequencies`, which
drops a band above the Nyquist frequency with this warning, and
:mod:`phonometry.filters.core` imports that module; the class lives here so
neither has to import the other to name it. It is published by
:mod:`phonometry.filters` and documented with the bank.
"""

from __future__ import annotations

from .._internal.warnings import PhonometryWarning

__all__ = ["FilterBankWarning"]


class FilterBankWarning(PhonometryWarning):
    """A fractional-octave filter bank asked for something it cannot honour.

    Emitted when a band lies above the Nyquist frequency of the sample rate
    and is dropped from the bank, and when a stateful bank is asked to detrend
    its blocks, which introduces a step between them.
    """
