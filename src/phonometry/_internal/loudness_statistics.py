#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""What a psychoacoustic metric reads off its trace over time, written once.

The percentile loudness of ISO 532-1:2017 as its reference program computes
it, and the opening frames that ECMA-418-2:2025 discards from the roughness
and the fluctuation strength before it reads them. The metrics of
:mod:`phonometry.psychoacoustics` take them from here, and so do the binaural
soundscape indicators of ISO/TS 12913-3 in :mod:`phonometry.environment`,
which report the same statistics of each ear without importing another
domain.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

#: Roughness frames discarded before the statistics, l50 in [0, 15]
#: (ECMA-418-2:2025 Clause 7.1.8).
ROUGHNESS_SETTLING_FRAMES = 16
#: Fluctuation-strength frames discarded before the statistics, l50 in
#: [0, 35] (ECMA-418-2:2025 Clause 9.1.12 and 9.1.14).
FLUCTUATION_SETTLING_FRAMES = 36


def _percentile(values: NDArray[np.float64], percentile: int) -> float:
    r"""Percentile loudness as computed by the reference implementation.

    NX is the loudness exceeded X % of the time: with the values sorted
    ascending and :math:`k = \lfloor (1 - X/100)\, n \rfloor`, the mean of
    the samples at positions k-1 and k (clause 6.4, Annex A main program).

    Provenance: this (k-1, k) mean comes from the electronic attachment's
    main program, not from a printed formula, and is supported by the
    Annex B.5 results (N5 within the clause 6.1 tolerance for all twelve
    technical signals, Nmax to < 0.01 %). Confirmed line by line against
    the attachment's Annex A.4 reference source (``f_calc_percentile``:
    the reference program truncates (1 - X/100)*n to an integer index and
    averages that sorted sample with its predecessor on the ascending
    sort). The workbooks' own B.5 N5 header values are not reproducible
    from their published traces with any Annex A percentile reading, so
    the headers are held to the 5-6 % tolerance only.
    """
    ordered = np.sort(values)
    n = ordered.size
    if percentile == 0:
        return float(ordered[-1])
    # The top of the percentile scale.
    if percentile == 100:  # noqa: PLR2004
        return float(ordered[0])
    k = int((1.0 - percentile / 100.0) * n)
    k = min(max(k, 1), n - 1)
    return float((ordered[k - 1] + ordered[k]) / 2.0)
