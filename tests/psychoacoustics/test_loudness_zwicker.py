#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Zwicker loudness (ISO 532-1:2017) conformance tests.

Expected values and tolerances come from the results workbooks of the
freely downloadable ISO 532-1:2017 electronic attachment (Annex B),
extracted to ``tests/data/iso532_1/iso532_1_annexB_expected.json``.
Synthetic test signals are regenerated per their normative Annex B
descriptions (pure tones at stated levels; 100 ms of silence before and
after, as noted in the workbooks). The recorded technical signals (B.5)
ship in ``tests/data/iso532_1/`` (see its README for provenance and ISO
attribution); ``ISO532_1_TESTDATA`` overrides the location.
"""

import json
import os
import pathlib

import numpy as np
import pytest

from phonometry import ZwickerLoudness, loudness_zwicker, loudness_zwicker_from_spectrum

FS = 48000
# Single ISO 532-1 data root, honouring the ISO532_1_TESTDATA override so the
# presence gate, the expected-values JSON and the Annex B.5 recordings all
# resolve from the same directory. Defaults to the in-repo fixtures.
DATA = pathlib.Path(os.environ.get(
    "ISO532_1_TESTDATA", str(pathlib.Path(__file__).parent / "data" / "iso532_1")
))
# The ISO 532-1 Annex B validation data may be absent (its README documents a
# removal policy); the tests that need it then skip rather than crash on import.
_ISO_DATA_PRESENT = (DATA / "iso532_1_annexB_expected.json").is_file()
EXPECTED = (
    json.loads((DATA / "iso532_1_annexB_expected.json").read_text())
    if _ISO_DATA_PRESENT
    else {}
)
requires_iso_data = pytest.mark.skipif(
    not _ISO_DATA_PRESENT,
    reason="ISO 532-1 Annex B data absent (see tests/data/iso532_1/README.md)",
)


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

@requires_iso_data
def test_annex_b2_stationary_from_levels() -> None:
    exp = EXPECTED["Test signal 1.txt"]
    res = loudness_zwicker_from_spectrum(_levels_from_file(), field="free")
    assert exp["Nmin"] <= res.loudness <= exp["Nmax"]
    assert res.loudness == pytest.approx(exp["N"], rel=0.001)


@requires_iso_data
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
@requires_iso_data
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
    # Measured +0.97 % vs the 4.0 sone definitional value (the +0.5-0.8 %
    # Zwicker stationary bias); 0.02 keeps ~2x headroom (was 0.05).
    assert res.loudness == pytest.approx(4.0, rel=0.02)
    assert res.loudness_level == pytest.approx(60.0, abs=0.5)


# ---------------------------------------------------------------------------
# Annex B.4 - time-varying loudness (synthetic, regenerated)
# ---------------------------------------------------------------------------

def _read_wav_fullscale(path: str) -> tuple[np.ndarray, int]:
    """Read a 16-bit WAV as first-channel samples in [-1, 1) with its rate.

    WAV/RIFF is little-endian, so the sample dtype is fixed to ``<i2`` rather
    than the host-native ``int16``; a multi-channel file keeps only channel 0.
    """
    import wave

    with wave.open(path) as w:
        fs = w.getframerate()
        n_channels = w.getnchannels()
        raw = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
    if n_channels > 1:
        raw = raw.reshape(-1, n_channels)[:, 0]
    return raw.astype(np.float64) / 32768.0, int(fs)


def _read_wav_pa(path: pathlib.Path, peak_rms_db: float) -> tuple[np.ndarray, int]:
    """Read a 16-bit ISO test WAV and calibrate its peak short-time RMS to
    the level stated in Annex B (the WAVs carry no absolute scale)."""
    x, fs = _read_wav_fullscale(str(path))
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
@requires_iso_data
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
    # Nmax reproduces the workbook header to < 0.01 %; 1e-3 locks that in
    # (was 0.05, ~700x looser than the achieved accuracy).
    assert res.loudness == pytest.approx(exp["Nmax"], rel=1e-3), (
        f"{case}: Nmax={res.loudness:.4f} vs expected {exp['Nmax']}"
    )
    ref = np.load(DATA / "iso532_1_annexB4_traces.npz")[f"signal_{num}"]
    n = min(ref.shape[0], res.loudness_vs_time.shape[0])
    ours, lo, hi = res.loudness_vs_time[:n], ref[:n, 2], ref[:n, 3]
    inside = np.mean((ours >= lo) & (ours <= hi))
    assert inside >= 0.99, f"{case}: only {inside:.1%} of N(t) inside the tolerance band"


@requires_iso_data
def test_n5_n10_use_full_rate_series(monkeypatch) -> None:
    """N5/N10 must come from the full-rate 2000 Hz weighted-loudness series,
    not the 4x-decimated 500 Hz output trace. Decimation keeps only one of
    four phases, spreading N5 by up to ~3 % across the phases (Annex B
    TS 10, 0.7513..0.7752); the full-rate percentile (0.7628) is
    phase-unambiguous and sits inside that envelope. The 500 Hz
    ``loudness_vs_time`` output is unchanged (public contract)."""
    import sys

    from phonometry.psychoacoustics.loudness_zwicker import _SR_LEVEL, _SR_LOUDNESS

    # The package re-exports the *function* ``loudness_zwicker``, which shadows
    # the module attribute of the same name; go through sys.modules instead.
    L = sys.modules["phonometry.psychoacoustics.loudness_zwicker"]

    seen: dict[int, np.ndarray] = {}
    orig = L._percentile

    def spy(values: np.ndarray, pct: int) -> float:
        seen[pct] = np.asarray(values, dtype=float).copy()
        return orig(values, pct)

    monkeypatch.setattr(L, "_percentile", spy)
    x, fs = _read_wav_pa(DATA / "iso532_1_test_signal_10.wav", 70.0)
    res = loudness_zwicker(x, fs, stationary=False)
    assert res.n5 is not None and res.loudness_vs_time is not None

    full = seen[5]
    dec = _SR_LEVEL // _SR_LOUDNESS
    # (a) computed on the un-decimated series (~dec x longer than the trace).
    assert full.size >= (dec - 0.5) * res.loudness_vs_time.size
    # (b) the reported N5 is the phase-unambiguous full-rate percentile, and
    #     lies strictly inside the envelope of the four decimation phases.
    phase_n5 = [orig(full[p::dec], 5) for p in range(dec)]
    assert min(phase_n5) < res.n5 < max(phase_n5)
    assert res.n5 == pytest.approx(orig(full, 5))


def test_time_varying_outputs() -> None:
    x = _tone(1000.0, 70.0, seconds=0.5)
    res = loudness_zwicker(x, FS)
    assert res.time is not None and res.loudness_vs_time is not None
    assert res.time.shape == res.loudness_vs_time.shape
    assert res.n5 is not None and res.n10 is not None and res.n5 >= res.n10


# ---------------------------------------------------------------------------
# Full validation against the recorded ISO signals (Annex B.5), shipped in
# tests/data/iso532_1 (see its README) or the ISO532_1_TESTDATA override.
# ---------------------------------------------------------------------------


@requires_iso_data
@pytest.mark.parametrize("num", list(range(14, 26)))
def test_annex_b5_technical_signals(num: int) -> None:
    import glob

    matches = glob.glob(str(DATA / "Annex B.5" / f"Test signal {num} *.wav"))
    if not matches:
        pytest.skip(f"signal {num} not found")
    # Annex B.1: "0 dB (relative to full scale) shall correspond to a sound
    # pressure level of 100 dB" — a full-scale sine is 100 dB SPL (2 Pa RMS),
    # so one full-scale unit is 2*sqrt(2) Pa peak.
    fullscale, fs = _read_wav_fullscale(matches[0])
    x = fullscale * (2.0 * np.sqrt(2.0))
    exp = EXPECTED[f"Test signal {num}"]
    # Each B.5 signal is validated in the sound field its ISO results
    # workbook was computed in; signal 15 (vehicle interior) is diffuse.
    res = loudness_zwicker(np.asarray(x, dtype=np.float64), int(fs), field=exp["field"])
    # Nmax reproduces the ISO results workbook to < 0.01 % for all twelve
    # signals; 1e-3 locks that in. N5 is a percentile of the loudness-vs-time
    # trace, phase-sensitive on impulsive signals (e.g. the machine gun),
    # so it is held to the clause 6.1 +-5 % tolerance with a small margin.
    assert res.loudness == pytest.approx(exp["Nmax"], rel=1e-3)
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


def test_non_finite_inputs_rejected() -> None:
    levels = np.full(28, 60.0)
    levels[5] = np.nan
    with pytest.raises(ValueError, match="finite"):
        loudness_zwicker_from_spectrum(levels)
    x = np.ones(1000)
    x[3] = np.inf
    with pytest.raises(ValueError, match="finite"):
        loudness_zwicker(x, FS)


def test_pathological_resampling_ratio_rejected() -> None:
    """gcd(48000, 44101) = 1 would demand a 48000/44101 polyphase filter;
    reject instead of hanging."""
    with pytest.raises(ValueError, match="resampl"):
        loudness_zwicker(np.ones(1000), 44101)


def test_diffuse_field_differs() -> None:
    levels = np.full(28, 70.0)
    free = loudness_zwicker_from_spectrum(levels, field="free")
    diffuse = loudness_zwicker_from_spectrum(levels, field="diffuse")
    assert isinstance(free, ZwickerLoudness)
    assert free.loudness != diffuse.loudness


def test_minimal_length_validation() -> None:
    """Signals shorter than one 500 Hz output sample raise cleanly instead
    of crashing on an empty percentile buffer."""
    with pytest.raises(ValueError, match="too short"):
        loudness_zwicker(np.ones(48), FS)
    res = loudness_zwicker(np.ones(96 * 4), FS)  # exactly a few output samples
    assert res.loudness >= 0.0


def test_specific_pattern_matches_reported_max() -> None:
    """The returned pattern is taken at the same decimated instant as the
    reported Nmax. For a steady tone the temporal weighting converges, so
    the pattern integral must match Nmax there (for transients the
    instantaneous pattern legitimately exceeds the weighted maximum)."""
    res = loudness_zwicker(_tone(1000.0, 70.0, seconds=2.0, pad_ms=0.0), FS)
    assert float(np.sum(res.specific) * 0.1) == pytest.approx(res.loudness, rel=0.03)
