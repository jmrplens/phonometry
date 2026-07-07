#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Zwicker loudness (ISO 532-1:2017) conformance tests.

Expected values and tolerances come from the results workbooks of the
freely downloadable ISO 532-1:2017 electronic attachment (Annex B),
extracted to ``tests/data/iso532_1_annexB_expected.json``. Synthetic test
signals are regenerated per their normative Annex B descriptions (pure
tones at stated levels; 100 ms of silence before and after, as noted in
the workbooks). The recorded technical signals (B.5) are only exercised
when the ISO package is available locally (``ISO532_1_TESTDATA``).
"""

import json
import os
import pathlib

import numpy as np
import pytest

from phonometry import ZwickerLoudness, loudness_zwicker, loudness_zwicker_from_spectrum

FS = 48000
DATA = pathlib.Path(__file__).parent / "data"
EXPECTED = json.loads((DATA / "iso532_1_annexB_expected.json").read_text())


def _tone(freq: float, level_db: float, seconds: float = 1.0, pad_ms: float = 100.0) -> np.ndarray:
    """Pure tone at an SPL (dB re 20 uPa) with leading/trailing silence."""
    t = np.arange(int(FS * seconds)) / FS
    amp = np.sqrt(2.0) * 2e-5 * 10 ** (level_db / 20)
    x = amp * np.sin(2 * np.pi * freq * t)
    pad = np.zeros(int(FS * pad_ms / 1000))
    return np.concatenate([pad, x, pad])


def _levels_from_file() -> np.ndarray:
    levels = []
    for line in (DATA / "iso532_1_test_signal_1_levels.txt").read_text().splitlines():
        if ":" in line and not line.strip().startswith("#"):
            levels.append(float(line.split(":")[1]))
    return np.array(levels)


# ---------------------------------------------------------------------------
# Annex B.2 - stationary loudness from one-third-octave levels
# ---------------------------------------------------------------------------

def test_annex_b2_stationary_from_levels() -> None:
    exp = EXPECTED["Test signal 1.txt"]
    res = loudness_zwicker_from_spectrum(_levels_from_file(), field="free")
    assert exp["Nmin"] <= res.loudness <= exp["Nmax"]
    assert res.loudness == pytest.approx(exp["N"], rel=0.001)


def test_specific_loudness_shape_and_integral() -> None:
    res = loudness_zwicker_from_spectrum(_levels_from_file())
    assert res.specific.shape == (240,)
    # N equals the integral of N'(z) dz (dz = 0.1 Bark) up to the slope
    # method's fractional band-edge handling
    assert float(np.sum(res.specific) * 0.1) == pytest.approx(res.loudness, rel=0.02)


# ---------------------------------------------------------------------------
# Annex B.3 - stationary loudness from synthetic signals (regenerated per
# the normative descriptions: pure tones at the stated levels)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("case", "freq", "level"),
    [("Test signal 2", 250.0, 80.0), ("Test signal 3", 1000.0, 60.0),
     ("Test signal 4", 4000.0, 40.0)],
)
def test_annex_b3_stationary_tones(case: str, freq: float, level: float) -> None:
    exp = EXPECTED[case]
    x = _tone(freq, level, seconds=2.0, pad_ms=0.0)
    res = loudness_zwicker(x, FS, stationary=True)
    assert exp["Nmin"] <= res.loudness <= exp["Nmax"], (
        f"{case}: N={res.loudness:.4f} outside [{exp['Nmin']}, {exp['Nmax']}]"
    )


def test_1khz_60db_anchor() -> None:
    """Definitional anchor: a 1 kHz tone at 40 phon is 1 sone; 60 dB -> 4 sone
    (each 10 phon doubles loudness)."""
    res = loudness_zwicker(_tone(1000.0, 60.0, seconds=2.0, pad_ms=0.0), FS, stationary=True)
    assert res.loudness == pytest.approx(4.0, rel=0.05)
    assert res.loudness_level == pytest.approx(60.0, abs=0.5)


# ---------------------------------------------------------------------------
# Annex B.4 - time-varying loudness (synthetic, regenerated)
# ---------------------------------------------------------------------------

def _read_wav_pa(path: pathlib.Path, peak_rms_db: float) -> tuple[np.ndarray, int]:
    """Read a 16-bit ISO test WAV and calibrate its peak short-time RMS to
    the level stated in Annex B (the WAVs carry no absolute scale)."""
    import wave

    with wave.open(str(path)) as w:
        fs = w.getframerate()
        raw = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    x = raw.astype(np.float64) / 32768.0
    win = max(1, int(fs * 0.002))
    sq = np.convolve(x**2, np.ones(win) / win, mode="same")
    peak_rms = float(np.sqrt(sq.max()))
    target = 2e-5 * 10 ** (peak_rms_db / 20)
    return x * (target / peak_rms), fs


@pytest.mark.parametrize(
    ("case", "num", "level"),
    [("Test signal 10", 10, 70.0), ("Test signal 11", 11, 70.0),
     ("Test signal 12", 12, 70.0)],
)
def test_annex_b4_tone_pulses(case: str, num: int, level: float) -> None:
    """The normative 1 kHz tone-pulse WAVs (Annex B.4): the prose only
    states duration and peak rms level; the ramp shapes exist only in the
    signals themselves, so the small originals are used directly. The
    normative acceptance criterion is the per-sample tolerance band around
    the published N(t) trace (workbook columns Nmin/Nmax), which is what
    this test enforces sample by sample, plus the Nmax header value.
    (The workbook header N5 values are not reproducible from their own
    published traces with the Annex A percentile formula and are therefore
    not asserted.)"""
    exp = EXPECTED[case]
    x, fs = _read_wav_pa(DATA / f"iso532_1_test_signal_{num}.wav", level)
    res = loudness_zwicker(x, fs, stationary=False)
    assert res.n5 is not None and res.loudness_vs_time is not None
    assert res.loudness == pytest.approx(exp["Nmax"], rel=0.05), (
        f"{case}: Nmax={res.loudness:.4f} vs expected {exp['Nmax']}"
    )
    ref = np.load(DATA / "iso532_1_annexB4_traces.npz")[f"signal_{num}"]
    n = min(ref.shape[0], res.loudness_vs_time.shape[0])
    ours, lo, hi = res.loudness_vs_time[:n], ref[:n, 2], ref[:n, 3]
    inside = np.mean((ours >= lo) & (ours <= hi))
    assert inside >= 0.99, f"{case}: only {inside:.1%} of N(t) inside the tolerance band"


def test_time_varying_outputs() -> None:
    x = _tone(1000.0, 70.0, seconds=0.5)
    res = loudness_zwicker(x, FS)
    assert res.time is not None and res.loudness_vs_time is not None
    assert res.time.shape == res.loudness_vs_time.shape
    assert res.n5 is not None and res.n10 is not None and res.n5 >= res.n10


# ---------------------------------------------------------------------------
# Optional full validation against the recorded ISO signals
# ---------------------------------------------------------------------------

ISO_DIR = os.environ.get("ISO532_1_TESTDATA", "")


@pytest.mark.skipif(not ISO_DIR, reason="set ISO532_1_TESTDATA to the ISO 532-1 attachment dir")
@pytest.mark.parametrize("num", list(range(14, 26)))
def test_annex_b5_technical_signals(num: int) -> None:
    import glob

    import soundfile as sf

    matches = glob.glob(os.path.join(ISO_DIR, "Annex B.5", f"Test signal {num} *.wav"))
    if not matches:
        pytest.skip(f"signal {num} not found")
    x, fs = sf.read(matches[0])
    exp = EXPECTED[f"Test signal {num}"]
    res = loudness_zwicker(np.asarray(x, dtype=np.float64), int(fs))
    assert res.loudness == pytest.approx(exp["Nmax"], rel=0.05)
    assert res.n5 == pytest.approx(exp["N5"], rel=0.06)


# ---------------------------------------------------------------------------
# Validation and API behavior
# ---------------------------------------------------------------------------

def test_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="28"):
        loudness_zwicker_from_spectrum(np.zeros(10))
    with pytest.raises(ValueError, match="field"):
        loudness_zwicker_from_spectrum(np.full(28, 60.0), field="reverberant")
    with pytest.raises(ValueError, match="fs"):
        loudness_zwicker(np.ones(1000), 0)


def test_diffuse_field_differs() -> None:
    levels = np.full(28, 70.0)
    free = loudness_zwicker_from_spectrum(levels, field="free")
    diffuse = loudness_zwicker_from_spectrum(levels, field="diffuse")
    assert isinstance(free, ZwickerLoudness)
    assert free.loudness != diffuse.loudness
