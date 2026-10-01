#  Copyright (c) 2026. Jose Manuel Requena Plens
"""ISO 3891:1978 Annex C: the worked example of the tone correction, as printed.

Transcribed from ISO 3891:1978, PDF page 26 (printed p. 23), "Example of
calculation procedure for tone correction". The example runs over the 22 bands
from 80 Hz to 10 kHz (``FREQUENCIES_HZ``). The page prints the smoothed
background (column 7) and the excess ``F`` (column 8) in whole decibels and
thirds of a decibel, so both are kept here in thirds, as integers: 67 2/3 dB
is 203. Column 8 prints a dash where the excess is not positive, kept as 0.

The test suite and the conformance report both read this one copy.
"""

FREQUENCIES_HZ = (
    80.0, 100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0, 500.0, 630.0, 800.0,
    1000.0, 1250.0, 1600.0, 2000.0, 2500.0, 3150.0, 4000.0, 5000.0, 6300.0,
    8000.0, 10000.0,
)  # fmt: skip

#: Column 3: the band levels ``L_i``, in dB.
LEVELS_DB = (
    70.0, 62.0, 70.0, 80.0, 82.0, 83.0, 76.0, 80.0, 80.0, 79.0, 78.0,
    80.0, 78.0, 76.0, 79.0, 85.0, 79.0, 78.0, 71.0, 60.0, 54.0, 45.0,
)  # fmt: skip

#: Column 7: the smoothed background of step 7, in thirds of a decibel.
BACKGROUND_THIRDS = (
    210, 203, 213, 233, 241, 237, 233, 234, 237, 237, 237,
    236, 234, 233, 234, 237, 236, 228, 209, 185, 159, 135,
)  # fmt: skip

#: Column 8: the excess ``F`` of step 8, in thirds of a decibel (0 for a dash).
EXCESS_THIRDS = (
    0, 0, 0, 7, 5, 12, 0, 6, 3, 0, 0,
    4, 0, 0, 3, 18, 1, 6, 4, 0, 3, 0,
)  # fmt: skip

#: Step 10: the tone correction ``C`` of the example, in dB.
TONE_CORRECTION_DB = 2.0
