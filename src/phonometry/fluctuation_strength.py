#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Fluctuation strength after Fastl & Zwicker / Osses et al.

Fluctuation strength ``F`` (unit: vacil) rates the slow loudness fluctuations of
a sound. It has a band-pass dependence on modulation frequency peaking near
4 Hz, and its fixed point is defined (Fastl & Zwicker, *Psychoacoustics: Facts
and Models*, Chapter 10) as **1 vacil** for a 1 kHz tone at 60 dB, 100 %
amplitude-modulated at 4 Hz. There is no ISO standard for fluctuation strength.

Two routes are provided:

* :func:`fluctuation_strength_am_noise` -- the closed form (Fastl & Zwicker
  Eq. 10.2) for a sinusoidally amplitude-modulated broadband noise, exact in the
  modulation factor, level and modulation frequency.
* :func:`fluctuation_strength` -- the signal model of Osses, García &
  Kohlrausch (2016), which estimates ``F`` from an arbitrary calibrated pressure
  signal. It sums specific contributions over 47 auditory filters,
  ``F = C_FS·Σ (m*_i)^p_m·|k_{i-2}·k_i|^p_k·g(z_i)^p_g`` (Osses 2016 Eq. 1),
  where ``m*`` is a generalised modulation depth, ``k`` a cross-covariance
  between neighbouring bands and ``g(z)`` a frequency weighting.

The closed form and the 1-vacil calibration are exact. The signal model has no
normative oracle; it is implemented clean-room from the Osses 2016 paper and
cross-checked against the literature fluctuation-strength values of Fastl &
Zwicker (Osses 2016 Table 1) and the open SQAT reference implementation. Like
the ECMA-418-2 roughness, the model reproduces the reference trends and the
1-vacil anchor within a documented tolerance rather than to the last digit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import NDArray

# --------------------------------------------------------------------------- #
# Closed form: AM broadband noise (Fastl & Zwicker Eq. 10.2)
# --------------------------------------------------------------------------- #
#: Numerator scale of the AM-noise fluctuation strength (Eq. 10.2), in vacil.
_BBN_SCALE = 5.8
#: Modulation-factor slope/offset of Eq. 10.2.
_BBN_M_SLOPE = 1.25
_BBN_M_OFFSET = 0.25
#: Level slope/offset of Eq. 10.2 (per dB).
_BBN_L_SLOPE = 0.05
_BBN_L_OFFSET = 1.0
#: Denominator constants of the band-pass shape in Eq. 10.2.
_BBN_FMOD_LP = 5.0
_BBN_FMOD_HP = 4.0
_BBN_DENOM_OFFSET = 1.5


def fluctuation_strength_am_noise(
    level_db: float, modulation_factor: float, mod_frequency: float
) -> float:
    """Fluctuation strength of AM broadband noise (Fastl & Zwicker Eq. 10.2).

    ``F = 5.8·(1.25·m − 0.25)·[0.05·(L/dB) − 1] / [(fmod/5Hz)² + (4Hz/fmod) +
    1.5]`` vacil, the closed form for a sinusoidally amplitude-modulated
    broadband noise of level ``L``, modulation factor ``m`` and modulation
    frequency ``fmod``. Exact; the result is clamped at ``0`` (the formula goes
    negative below ~20 dB or ``m < 0.2`` where the sensation vanishes).

    :param level_db: Broadband-noise level ``L``, in dB.
    :param modulation_factor: Modulation factor ``m`` (0..1).
    :param mod_frequency: Modulation frequency ``fmod``, in Hz.
    :return: Fluctuation strength, in vacil (>= 0).
    :raises ValueError: If ``modulation_factor`` is outside [0, 1] or
        ``mod_frequency`` is not positive/finite, or the level is not finite.
    """
    m = float(modulation_factor)
    fmod = float(mod_frequency)
    lvl = float(level_db)
    if not np.isfinite(m) or not 0.0 <= m <= 1.0:
        raise ValueError("'modulation_factor' must be in [0, 1].")
    if not np.isfinite(fmod) or fmod <= 0.0:
        raise ValueError("'mod_frequency' must be positive and finite.")
    if not np.isfinite(lvl):
        raise ValueError("'level_db' must be finite.")
    numerator = (
        _BBN_SCALE
        * (_BBN_M_SLOPE * m - _BBN_M_OFFSET)
        * (_BBN_L_SLOPE * lvl - _BBN_L_OFFSET)
    )
    denominator = (
        (fmod / _BBN_FMOD_LP) ** 2 + (_BBN_FMOD_HP / fmod) + _BBN_DENOM_OFFSET
    )
    return float(max(0.0, numerator / denominator))


# --------------------------------------------------------------------------- #
# Osses 2016 signal model
# --------------------------------------------------------------------------- #
_FS_SAMPLE_RATE = 44100  # model design rate (Osses 2016)
_N_FILTERS = 47  # auditory filters (Osses 2016 §2.1.2)
_BARK_SPACING = 0.5  # observation-point spacing, Bark
_S1 = 27.0  # lower excitation slope, dB/Bark (Osses 2016 §2.1.2)
_P_M = 1.7  # modulation-depth exponent p_m (Osses 2016 §3.1)
_P_K = 1.7  # cross-covariance exponent p_k (Osses 2016 §3.1)
_COMPRESSION_THRESHOLD = 0.7  # m* compression knee (Osses 2016 §2.1.3)
_COMPRESSION_RATIO = 3.0  # 3:1 compression above the knee
# Envelope band-pass H(fmod). The paper's 3.1-12 Hz cascade was fitted to its
# own 4096-tap FIR front-end and is too narrow for this FFT-based excitation
# front-end -- it collapses the 1-2 Hz and 16-32 Hz tails of the modulation
# sweep. Re-fitted clean-room against the literature trends (Osses 2016 Table 1;
# the open SQAT ``FluctuationStrength_Osses2016`` was consulted only as a numeric
# oracle for the sweep shape, its CC-BY-NC code was not copied), a broader
# 2-10 Hz band-pass (1st-order high-pass, 3rd-order low-pass) reproduces the
# AM-tone and AM-BBN sweeps with the sensation maximum at 4 Hz. See the
# acceptance tolerance documented on :func:`fluctuation_strength`.
_HP_LO = 2.0  # H(fmod) pass-band low edge, Hz
_LP_HI = 10.0  # H(fmod) pass-band high edge, Hz
_HP_ORDER = 1  # H(fmod) high-pass order (broad low-frequency tail)
_LP_ORDER = 3  # H(fmod) low-pass order (steep upper roll-off)

#: Calibration constant C_FS (Osses 2016 Eq. 1), derived once from the 1-vacil
#: reference stimulus through this implementation's own front-end and cached (see
#: :func:`_c_fs`), replacing the paper's front-end-specific literal 0.2490.
_C_FS: float | None = None


def _hz_to_bark(f: "NDArray[np.float64]") -> "NDArray[np.float64]":
    """Critical-band rate z(f) in Bark (Osses 2016 Eq. 3)."""
    return np.asarray(
        13.0 * np.arctan(0.76e-4 * f) + 3.5 * np.arctan((f / 7500.0) ** 2)
    )


def _terhardt_a0_db(f: "NDArray[np.float64]") -> "NDArray[np.float64]":
    """Outer/middle-ear transmission a0(f), in dB (Terhardt free-field model).

    The frequency-dependent gain from free field to the oval window used by the
    excitation-pattern front-end (Osses 2016 §2.1.1).
    """
    fk = np.asarray(f, dtype=np.float64) / 1000.0
    a0 = np.zeros_like(fk)
    pos = fk > 0.0
    a0[pos] = (
        -3.64 * fk[pos] ** (-0.8)
        + 6.5 * np.exp(-0.6 * (fk[pos] - 3.3) ** 2)
        - 1e-3 * fk[pos] ** 3.6
    )
    return a0


def _g_weight(z: "NDArray[np.float64]") -> "NDArray[np.float64]":
    """Frequency weighting g(z) (Osses 2016 §3.1): 1 up to 15 Bark, then a
    linear taper down to 0.5 at 23.5 Bark."""
    g = np.ones_like(z)
    high = z > 15.0
    g[high] = 1.0 - 0.5 * (z[high] - 15.0) / (23.5 - 15.0)
    return np.clip(g, 0.5, 1.0)


@dataclass(frozen=True)
class FluctuationStrengthResult:
    """Fluctuation strength of a signal (Osses 2016 model).

    :ivar fluctuation_strength: Overall fluctuation strength ``F``, in vacil
        (the median over the analysis frames).
    :ivar specific: Specific fluctuation strength ``f(z)`` per auditory filter,
        in vacil/Bark (averaged over frames), shape ``(47,)``.
    :ivar bark_axis: Centre critical-band rate ``z_i`` of each filter, in Bark,
        shape ``(47,)``.
    :ivar time_dependent: Fluctuation strength per analysis frame, in vacil.
    """

    fluctuation_strength: float
    specific: "NDArray[np.float64]"
    bark_axis: "NDArray[np.float64]"
    time_dependent: "NDArray[np.float64]"

    def plot(self, ax: "Axes | None" = None, **kwargs: Any) -> "Axes":
        """Plot the specific fluctuation strength against critical-band rate."""
        from ._plotting import plot_fluctuation_strength

        return plot_fluctuation_strength(self, ax=ax, **kwargs)


def _bandpass_envelope_filter(fs: float) -> Any:
    """H(fmod): band-pass on the envelope (Osses 2016 §2.1.3/3.1, re-fitted).

    A ``_LP_ORDER``-order low-pass and a ``_HP_ORDER``-order high-pass in cascade
    (pass-band ``_HP_LO``-``_LP_HI`` Hz), returned as SOS. The corners and orders
    are the re-fit described at the ``_HP_LO`` constant.
    """
    from scipy import signal as sp_signal

    lp = sp_signal.butter(_LP_ORDER, _LP_HI, btype="low", fs=fs, output="sos")
    hp = sp_signal.butter(_HP_ORDER, _HP_LO, btype="high", fs=fs, output="sos")
    return np.vstack([lp, hp])


def _cross_covariance(x: "NDArray[np.float64]", y: "NDArray[np.float64]") -> float:
    """Normalised cross covariance k (Osses 2016 Eq. 9)."""
    n = x.size
    sx = float(np.sum(x))
    sy = float(np.sum(y))
    num = float(np.sum(x * y)) - sx * sy / n
    dx = float(np.sum(x * x)) - sx * sx / n
    dy = float(np.sum(y * y)) - sy * sy / n
    denom = np.sqrt(dx * dy)
    if denom <= 0.0:
        return 0.0
    return float(num / denom)


def _validate_signal(x: "NDArray[np.float64]") -> "NDArray[np.float64]":
    sig = np.asarray(x, dtype=np.float64)
    if sig.ndim != 1:
        raise ValueError("'signal' must be one-dimensional.")
    if sig.size == 0:
        raise ValueError("'signal' must not be empty.")
    if not np.all(np.isfinite(sig)):
        raise ValueError("'signal' must be finite.")
    return sig


def _bark_center_hz(z: "NDArray[np.float64] | float") -> Any:
    """Approximate inverse of :func:`_hz_to_bark` for a band centre (Hz).

    Accepts a scalar or an array of critical-band rates and returns the matching
    frequencies by numerical inversion of Eq. 3 on a monotone grid.
    """
    grid = np.linspace(20.0, 20000.0, 20000)
    zz = _hz_to_bark(grid)
    return np.interp(z, zz, grid)


def _analyze(sig: "NDArray[np.float64]") -> tuple["NDArray[np.float64]", "NDArray[np.float64]", "NDArray[np.float64]"]:
    """Un-calibrated Osses 2016 sum (``C_FS = 1``) of a model-rate signal.

    Runs the full front-end -- ear transmission, 47-band excitation filter bank,
    generalised modulation depth ``m*``, neighbour cross-covariance ``k`` and the
    weighted sum of Eq. (1) without the ``C_FS`` scale -- over 2 s frames with
    50 % overlap. Returns the per-frame raw sums, the frame-averaged raw specific
    pattern and the Bark axis. The public :func:`fluctuation_strength` multiplies
    these by :func:`_c_fs`; keeping the scale out here lets the calibration be
    derived from this same path without recursion.
    """
    from scipy import signal as sp_signal

    # Observation points (centre frequencies) of the 47 filters.
    z_axis = np.arange(1, _N_FILTERS + 1, dtype=np.float64) * _BARK_SPACING
    g_z = _g_weight(z_axis)
    band_center_hz = np.asarray(_bark_center_hz(z_axis), dtype=np.float64)

    env_sos = _bandpass_envelope_filter(float(_FS_SAMPLE_RATE))
    fs_v = float(_FS_SAMPLE_RATE)

    # 2 s frames, 50 % overlap.
    frame_len = int(round(2.0 * fs_v))
    if sig.size < frame_len:
        frame_len = sig.size
    hop = max(1, frame_len // 2)
    starts = list(range(0, max(1, sig.size - frame_len + 1), hop))
    if not starts:
        starts = [0]

    fs_frames: list[float] = []
    specific_accum = np.zeros(_N_FILTERS)

    p_ref = 2e-5
    for start in starts:
        frame = sig[start : start + frame_len]
        n = frame.size
        if n < 16:
            continue
        # Excitation patterns in the frequency domain.
        spec = np.fft.rfft(frame * np.hanning(n))
        freqs = np.fft.rfftfreq(n, d=1.0 / fs_v)
        mag = np.abs(spec) * 2.0 / n
        # Per-component level (dB SPL) after the ear transmission.
        with np.errstate(divide="ignore"):
            lvl = 20.0 * np.log10(np.maximum(mag, 1e-12) / p_ref)
        lvl = lvl + _terhardt_a0_db(freqs)
        z_comp = _hz_to_bark(freqs)

        # Only components above a floor contribute.
        active = np.where(mag > mag.max() * 1e-4)[0] if mag.size else np.array([], int)
        f_act = freqs[active]
        lvl_act = lvl[active]
        z_act = z_comp[active]
        spec_act = spec[active]
        inv_mag_act = 1.0 / np.maximum(mag[active], 1e-12)
        s2_act = 24.0 + 230.0 / np.maximum(f_act, 1.0) - 0.2 * lvl_act
        lvl_floor = lvl_act.max() - 60.0 if active.size else 0.0

        # Build the 47 band time signals from the triangular excitation,
        # vectorising the inverse FFT across all bands in one call.
        band_spec = np.zeros((_N_FILTERS, freqs.size), dtype=np.complex128)
        for i, zi in enumerate(z_axis):
            # Excitation contribution of each active component to band i.
            dz = zi - z_act
            contrib_db = np.where(
                f_act < band_center_hz[i],
                lvl_act - s2_act * dz,  # component below observation point
                lvl_act + _S1 * dz,  # component above (dz<0): -S1|dz|
            )
            weight = 10.0 ** (contrib_db / 20.0)
            weight[contrib_db < lvl_floor] = 0.0
            band_spec[i, active] = spec_act * (weight * inv_mag_act)
        band_env = np.abs(np.fft.irfft(band_spec, n=n, axis=1))

        # Generalised modulation depth m* per band.
        h0 = band_env.mean(axis=1)
        h_bp = sp_signal.sosfilt(env_sos, band_env, axis=1)
        rms_bp = np.sqrt(np.mean(h_bp**2, axis=1))
        with np.errstate(divide="ignore", invalid="ignore"):
            m_star = np.where(h0 > 0.0, rms_bp / h0, 0.0)
        # 3:1 compression above the knee.
        over = m_star > _COMPRESSION_THRESHOLD
        m_star[over] = _COMPRESSION_THRESHOLD + (m_star[over] - _COMPRESSION_THRESHOLD) / _COMPRESSION_RATIO

        # Cross covariance with the bands two indices away.
        k = np.ones(_N_FILTERS)
        for i in range(_N_FILTERS):
            lo = i - 2
            hi = i + 2
            k_lo = _cross_covariance(h_bp[lo], h_bp[i]) if lo >= 0 else 1.0
            k_hi = _cross_covariance(h_bp[i], h_bp[hi]) if hi < _N_FILTERS else 1.0
            k[i] = abs(k_lo * k_hi)

        f_specific = (m_star**_P_M) * (k**_P_K) * g_z
        specific_accum += f_specific
        fs_frames.append(float(np.sum(f_specific)))

    if not fs_frames:
        fs_frames = [0.0]
    time_dependent = np.asarray(fs_frames, dtype=np.float64)
    specific = specific_accum / len(fs_frames)
    return time_dependent, specific, z_axis


def _reference_signal(seconds: float = 2.0) -> "NDArray[np.float64]":
    """The 1-vacil reference stimulus (Osses 2016 §2.2), at the model rate.

    A 1 kHz tone 100 % amplitude-modulated at 4 Hz, calibrated to 60 dB SPL. The
    signal is fully deterministic (a pure AM sinusoid, no stochastic component),
    so it reproduces the calibration constant exactly on every run.
    """
    t = np.arange(int(round(seconds * _FS_SAMPLE_RATE))) / float(_FS_SAMPLE_RATE)
    x = (1.0 + np.sin(2.0 * np.pi * 4.0 * t)) * np.sin(2.0 * np.pi * 1000.0 * t)
    x = x / np.sqrt(np.mean(x**2)) * 2e-5 * 10.0 ** (60.0 / 20.0)
    return np.asarray(x, dtype=np.float64)


def _c_fs() -> float:
    """Calibration constant C_FS (Osses 2016 Eq. 1), derived and cached.

    Instead of the paper's front-end-specific literal 0.2490, C_FS is set so the
    1-vacil reference stimulus (:func:`_reference_signal`) returns exactly
    1.00 vacil through *this* implementation's front-end, following the pattern
    of :func:`sharpness._k_din`. It is computed once and cached module-level.
    """
    global _C_FS
    if _C_FS is None:
        raw = float(np.median(_analyze(_reference_signal())[0]))
        c = 1.0 / raw if raw > 0.0 else 0.0
        if not 0.15 <= c < 0.50:  # pragma: no cover - sanity guard
            raise RuntimeError(f"C_FS={c} outside the expected range")
        _C_FS = c
    return _C_FS


def fluctuation_strength(
    signal_in: "NDArray[np.float64]",
    fs: float,
) -> FluctuationStrengthResult:
    """Fluctuation strength of a calibrated signal (Osses 2016 model).

    Estimates ``F`` in vacil from an arbitrary calibrated sound-pressure signal
    by the model of Osses, García & Kohlrausch (2016): an outer/middle-ear
    transmission, a 47-band excitation-pattern filter bank, the generalised
    modulation depth ``m*`` from the band-pass-filtered envelope, the
    cross-covariance ``k`` between neighbouring bands and the weighted sum of
    Eq. (1). The signal is analysed in 2 s frames; the overall value is the
    median across frames. The Osses 2016 model is defined for the **free
    field** only (its ``a0`` transmission is the free-field characteristic);
    there is no diffuse-field variant, so this function takes no ``field``
    argument.

    .. note::
        No ISO standard defines fluctuation strength and no numeric oracle
        anchors this signal model. It is implemented clean-room from the Osses
        2016 paper and reproduces the literature reference values (Osses 2016
        Table 1) and the 1-vacil calibration point within a documented
        tolerance -- the reference method itself only agrees qualitatively for
        FM tones. For an exact figure on AM broadband noise use
        :func:`fluctuation_strength_am_noise`.

        **Calibration.** The constant ``C_FS`` (Eq. 1) is not the paper's literal
        0.2490 -- that was fitted to the paper's own 4096-tap FIR front-end. Here
        it is derived once from the 1-vacil reference stimulus (1 kHz, 60 dB,
        ``m = 1``, 4 Hz) run through this implementation's front-end, so the
        reference returns **exactly 1.00 vacil by construction** (``C_FS ≈ 0.30``;
        see :func:`_c_fs`).

        **Achieved tolerance** (against Osses 2016 Table 1 literature values):
        the reference tone is 1.00 vacil exactly; the AM-tone 70 dB sweep
        (``fmod = 1, 2, 4, 8, 16, 32`` Hz) has Pearson correlation ≈ 0.98 with
        the literature, peaks at 4 Hz and stays within a factor ≈ 1.9 at every
        point; the AM broadband-noise 60 dB sweep shows the correct band-pass
        shape (maximum at 4 Hz, monotone tails). FM-tone accuracy is *not*
        pursued -- the reference method itself overestimates it above 4 Hz.

    :param signal_in: Calibrated sound-pressure signal (1-D), in Pa.
    :param fs: Sample rate, in Hz (resampled to the model rate if needed).
    :return: A :class:`FluctuationStrengthResult`.
    :raises ValueError: If the signal is invalid or ``fs`` is not positive.
    """
    from scipy import signal as sp_signal

    sig = _validate_signal(signal_in)
    fs_v = float(fs)
    if not np.isfinite(fs_v) or fs_v <= 0.0:
        raise ValueError("'fs' must be positive and finite.")

    # Resample to the model design rate.
    if fs_v != _FS_SAMPLE_RATE:
        n_out = int(round(sig.size * _FS_SAMPLE_RATE / fs_v))
        sig = np.asarray(sp_signal.resample(sig, max(n_out, 1)), dtype=np.float64)

    time_dependent_raw, specific_raw, z_axis = _analyze(sig)
    c = _c_fs()
    time_dependent = c * time_dependent_raw
    specific = c * specific_raw
    overall = float(np.median(time_dependent))
    return FluctuationStrengthResult(
        fluctuation_strength=overall,
        specific=specific,
        bark_axis=z_axis,
        time_dependent=time_dependent,
    )
