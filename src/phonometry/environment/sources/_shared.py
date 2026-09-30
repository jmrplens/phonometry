#  Copyright (c) 2026. Jose Manuel Requena Plens
"""What the railway modules share: the tolerance of their verdicts.

The rail roughness of EN 15610
(:mod:`~phonometry.environment.sources.acoustic_roughness`), the track decay
rates of EN 15461 (:mod:`~phonometry.environment.sources.track_decay`) and the
ISO 3095 type test that judges both
(:mod:`~phonometry.environment.sources.rolling_stock_noise`) compare values
computed from decimal readings, such as an energy mean, a level difference or
a ratio of lengths, against the limits their clauses print. Binary arithmetic
brings such a value back a few units in the last place either side of the
decimal it stands for, so every such comparison grants the same slack. The
three modules, and the renderer that marks their results, import it from here
rather than each carrying its own.
"""

from __future__ import annotations

#: How far a value may sit past a limit it reached through floating-point
#: arithmetic and still be on it: in decibels (or dB/m) for a level or a rate,
#: and as a fraction for a length stated in round numbers. A billionth is far
#: below any resolution the standards print and far above the rounding of any
#: value they involve.
_TOLERANCE = 1.0e-9
