#  Copyright (c) 2026. Jose M. Requena-Plens
"""Local-only oracle: the EBU loudness test set's authentic programme cases.

EBU Tech 3341 cases 7-8 and EBU Tech 3342 cases 5-6 use authentic programme
material (narration and a movie/drama segment) that cannot be synthesized
from the specifications. The EBU distributes the exact WAV files as the
'EBU loudness test set' (v04), free for technical testing, so these cases
run only where that set is present under ``plan/dsp-sources/`` (gitignored;
``EBU_LOUDNESS_TEST_SET`` overrides the location). The synthesizable cases
of both specifications are covered with generated signals in
``test_program_loudness.py``.
"""

import os
import pathlib

import numpy as np
import pytest
from scipy.io import wavfile

from phonometry import broadcast

DATA = pathlib.Path(
    os.environ.get(
        "EBU_LOUDNESS_TEST_SET",
        str(
            pathlib.Path(__file__).parents[2]
            / "plan"
            / "dsp-sources"
            / "ebu-loudness-test-set"
        ),
    )
)
_NLR = "seq-3341-7_seq-3342-5-24bit.wav"
_WLR = "seq-3341-2011-8_seq-3342-6-24bit-v02.wav"

pytestmark = pytest.mark.skipif(
    not (DATA / _NLR).is_file(),
    reason="EBU loudness test set absent (local-only oracle; download the "
    "free set from tech.ebu.ch into plan/dsp-sources/ebu-loudness-test-set/ "
    "or point EBU_LOUDNESS_TEST_SET at it)",
)


def _load(name: str) -> tuple[np.ndarray, float]:
    """Read a test-set WAV as float64 ``[channels, samples]`` in [-1, 1)."""
    fs, x = wavfile.read(DATA / name)
    assert x.ndim == 2, f"{name}: expected a stereo programme file"
    if x.dtype == np.int32:  # 24-bit PCM arrives left-justified in int32
        y = x.astype(np.float64) / 2147483648.0
    elif x.dtype == np.int16:
        y = x.astype(np.float64) / 32768.0
    else:
        y = np.asarray(x, dtype=np.float64)
    # A silent file means a corrupt download; fail loudly instead of gating
    # everything away and "passing" on noise.
    assert float(np.sqrt(np.mean(y**2))) > 1e-4, f"{name}: silent file"
    return y.T, float(fs)


@pytest.mark.parametrize(
    ("name", "case"),
    [(_NLR, "Tech 3341 case 7 (NLR)"), (_WLR, "Tech 3341 case 8 (WLR)")],
)
def test_authentic_programme_integrated_loudness(name: str, case: str) -> None:
    x, fs = _load(name)
    res = broadcast.program_loudness(x, fs)
    assert res.integrated == pytest.approx(-23.0, abs=0.1), case


@pytest.mark.parametrize(
    ("name", "expected", "case"),
    [
        (_NLR, 5.0, "Tech 3342 case 5 (NLR)"),
        (_WLR, 15.0, "Tech 3342 case 6 (WLR)"),
    ],
)
def test_authentic_programme_loudness_range(
    name: str, expected: float, case: str
) -> None:
    x, fs = _load(name)
    res = broadcast.program_loudness(x, fs)
    assert res.loudness_range == pytest.approx(expected, abs=1.0), case
