#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Evaluating the vibration of a passing train (DIN 45672-2).

DIN 45672-2 prints no worked passage, so the rows are the numbers it does
print that code can reach: the start-up of the running r.m.s. Clause 4 quotes,
reached by running Formula (1) on a sine from rest; the block length Clause
7.3.2 derives from its recommended resolution, reached through the density
estimate; and the relative bandwidth Clause 7.1 gives the third-octave bands,
reached through the bank the passage is analysed with.

**The table that is not here.** Table 1 prints how many narrow-band lines each
third octave takes, and the library takes exactly those counts as its input,
so a row that added a flat density back into bands would compare the table
with a copy of itself. Which lines each band takes is the part the library
decides, and the test suite holds that choice against the nominal band edges
instead.

**What the Clause 4 rows show.** The sentence puts the shortfall of the
running r.m.s. at 14 % after two time constants and 2 % after four, and those
are the shortfalls of the mean square, :math:`e^{-2}` and :math:`e^{-4}`. The
rows compare the mean square, which is what reproduces the printed numbers;
the r.m.s. itself is short by about half as much, which is what Figure 3 of
the standard draws.

DIN 45672-1:2009-12, Clause 4.5, which the same module family implements,
prints no number to check its formulas against and is anchored in closed forms
in the test suite instead; two of its formulas are registered in
``docs/ERRATA.md``.

Oracle: DIN 45672-2:1995-07, Clause 4 on printed page 3, Clause 7.1 on page
5 and Clause 7.3.2 on page 7.
"""

from __future__ import annotations

import functools
import math

import numpy as np

import phonometry as ph

from ..registry import Outcome, numeric, register

_RAILWAY = "Railway vibration evaluation (DIN 45672)"
_EDITION = "DIN 45672-2:1995-07"

#: Clause 4 on printed page 3: the shortfall after 2 tau and after 4 tau, %.
_CLAUSE_4 = {2.0: 14.0, 4.0: 2.0}

#: Half a unit of the last printed place of an integer percentage.
_PERCENT_TOLERANCE = 0.5

#: A rate whose block at 1,25 Hz is a whole number of samples, so the block
#: length Clause 7.3.2 derives comes out exactly rather than rounded.
_FS_HZ = 2000.0


def _chk_clause_4(multiple: float) -> Outcome:
    freq_hz = 200.0
    fs = 8192.0
    tau = ph.vibration.KB_TIME_CONSTANT_S
    t = np.arange(round(fs)) / fs
    rms = ph.vibration.running_velocity_rms(np.sin(2.0 * math.pi * freq_hz * t), fs)
    at = round(multiple * tau * fs)
    half_period = round(fs / freq_hz / 2.0)
    mean_square = float(np.mean(rms[at - half_period : at + half_period] ** 2))
    shortfall = 100.0 * (1.0 - mean_square / 0.5)
    return numeric(
        _CLAUSE_4[multiple], shortfall, _PERCENT_TOLERANCE, unit="%", places=2
    )


@register(_RAILWAY, f"{_EDITION} 7.3.2", "Block length at 1,25 Hz resolution, s")
def _chk_block_length() -> Outcome:
    t = np.arange(round(4.0 * _FS_HZ)) / _FS_HZ
    spectrum = ph.vibration.narrowband_psd(np.sin(2.0 * math.pi * 40.0 * t), _FS_HZ)
    return numeric(0.8, spectrum.nperseg / _FS_HZ, 1e-12, unit="s", places=3)


@register(_RAILWAY, f"{_EDITION} 7.1", "Relative bandwidth of a third octave, %")
def _chk_bandwidth() -> Outcome:
    bank = ph.filters.OctaveFilterBank(2048, fraction=3, limits=[4.0, 315.0])
    width = (np.asarray(bank.freq_u) - np.asarray(bank.freq_d)) / np.asarray(bank.freq)
    return numeric(23.0, 100.0 * float(np.mean(width)), _PERCENT_TOLERANCE, unit="%")


def _register_clause_4() -> None:
    for multiple in _CLAUSE_4:
        register(
            _RAILWAY,
            f"{_EDITION} Clause 4",
            f"Shortfall of the running mean square after {multiple:g} tau, %",
        )(functools.partial(_chk_clause_4, multiple))


_register_clause_4()
