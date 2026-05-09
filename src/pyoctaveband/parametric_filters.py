#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Weighting filters (A, C, Z) and time weighting utilities for audio analysis.
Implementation according to IEC 61672-1:2013.
"""

from __future__ import annotations

from typing import List, Tuple, cast

import numpy as np
from numba import jit
from scipy import signal

from .utils import _typesignal


class WeightingFilter:
    """
    Class-based frequency weighting filter (A, C, Z).
    Allows pre-calculating and reusing filter coefficients.
    """

    def __init__(self, fs: int, curve: str = "A",
                 stateful: bool = False, steady_ic: bool = False) -> None:
        """
        Initialize the weighting filter.

        :param fs: Sample rate in Hz.
        :param curve: 'A', 'C' or 'Z'.
        :param stateful: If True, the weighting filter is stateful. Useful for block processing.
        :param steady_ic: If True, calculate steady state initial conditions for filter.
        """
        if fs <= 0:
            raise ValueError("Sample rate 'fs' must be positive.")

        self.fs = fs
        self.curve = curve.upper()
        self.stateful = stateful

        if self.curve == "Z":
            self.sos = np.array([])
            if self.stateful:
                self.zi = np.array([])
            return

        if self.curve not in ["A", "C"]:
            raise ValueError("Weighting curve must be 'A', 'C' or 'Z'")

        # Analog ZPK for A and C weighting
        # f1, f2, f3, f4 constants as per IEC 61672-1
        f1 = 20.598997
        f4 = 12194.217

        if self.curve == "A":
            f2 = 107.65265
            f3 = 737.86223
            # Zeros at 0 Hz
            z = np.array([0, 0, 0, 0])
            # Poles
            p = np.array(
                [
                    -2 * np.pi * f1,
                    -2 * np.pi * f1,
                    -2 * np.pi * f4,
                    -2 * np.pi * f4,
                    -2 * np.pi * f2,
                    -2 * np.pi * f3,
                ]
            )
            # k chosen to give 0 dB at 1000 Hz
            k = 3.5174303309e13

        else:  # C weighting
            z = np.array([0, 0])
            p = np.array([-2 * np.pi * f1, -2 * np.pi * f1, -2 * np.pi * f4, -2 * np.pi * f4])
            k = 5.91797e8

        # Recalculate k to ensure 0dB at 1kHz
        w = 2 * np.pi * 1000
        h = k * np.prod(1j * w - z) / np.prod(1j * w - p)
        k = k / np.abs(h)

        zd, pd, kd = signal.bilinear_zpk(z, p, k, fs)
        self.sos = signal.zpk2sos(zd, pd, kd)

        # Initialize filter state for stateful block-wise processing.
        # Uses lazy allocation: zi is sized on first filter() call so that
        # the channel dimension matches the actual input shape.
        if self.stateful:
            self.zi = np.array([])
            self._steady_ic = steady_ic

    def _init_filter_state(self, x_proc: np.ndarray) -> None:
        """Allocate or reallocate ``zi`` to match the input shape."""
        n_sections = self.sos.shape[0]
        if x_proc.ndim == 1:
            if self._steady_ic:
                self.zi = signal.sosfilt_zi(self.sos)
            else:
                self.zi = np.zeros((n_sections, 2))
        else:
            n_channels = x_proc.shape[0]
            if self._steady_ic:
                zi_base = signal.sosfilt_zi(self.sos)
                self.zi = np.tile(zi_base[:, np.newaxis, :], (1, n_channels, 1))
            else:
                self.zi = np.zeros((n_sections, n_channels, 2))

    def _needs_zi_reinit(self, x_proc: np.ndarray) -> bool:
        """Check whether ``zi`` must be (re)allocated for *x_proc*."""
        if self.zi.size == 0:
            return True
        if x_proc.ndim == 1:
            return self.zi.ndim != 2
        return self.zi.ndim != 3 or self.zi.shape[1] != x_proc.shape[0]

    def filter(self, x: List[float] | np.ndarray) -> np.ndarray:
        """
        Apply the weighting filter to a signal.

        :param x: Input signal (1D or 2D [channels, samples]).
        :return: Weighted signal.
        """
        x_proc = _typesignal(x)
        if self.curve == "Z":
            return x_proc

        if self.stateful:
            if self._needs_zi_reinit(x_proc):
                self._init_filter_state(x_proc)
            y, self.zi = signal.sosfilt(self.sos, x_proc, axis=-1, zi=self.zi)
        else:
            y = signal.sosfilt(self.sos, x_proc, axis=-1)

        return cast(np.ndarray, y)


def weighting_filter(x: List[float] | np.ndarray, fs: int, curve: str = "A") -> np.ndarray:
    """
    Apply frequency weighting (A or C) to a signal.
    
    :param x: Input signal.
    :param fs: Sample rate.
    :param curve: 'A', 'C' or 'Z' (Z is zero weighting/bypass).
    :return: Weighted signal.
    """
    wf = WeightingFilter(fs, curve)
    return wf.filter(x)


def _prepare_time_weighting_initial_state(
    x_sq: np.ndarray,
    initial_state: str | float | np.ndarray | None,
) -> np.ndarray:
    """Return the previous output state ``y[-1]`` for time weighting."""
    state_shape = x_sq.shape[:-1]

    if initial_state is None:
        return np.zeros(state_shape, dtype=x_sq.dtype)

    if isinstance(initial_state, str):
        state_name = initial_state.lower()
        if state_name == "zero":
            return np.zeros(state_shape, dtype=x_sq.dtype)
        if state_name == "first":
            return np.asarray(np.take(x_sq, 0, axis=-1), dtype=x_sq.dtype).copy()
        raise ValueError("initial_state must be None, 'zero', 'first', a scalar, or an array")

    state = np.asarray(initial_state, dtype=x_sq.dtype)
    if state.shape == ():
        return np.full(state_shape, state.item(), dtype=x_sq.dtype)

    try:
        return np.broadcast_to(state, state_shape).astype(x_sq.dtype, copy=True)
    except ValueError as exc:
        raise ValueError(
            "initial_state must be scalar or broadcastable to the input shape without the time axis"
        ) from exc


@jit(nopython=True, cache=True)  # type: ignore
def _apply_impulse_kernel(
    x_t: np.ndarray,
    alpha_rise: float,
    alpha_fall: float,
    initial_state: np.ndarray,
) -> np.ndarray:
    """Numba-optimized kernel for asymmetric time weighting."""
    y_t = np.zeros_like(x_t)
    curr_y = initial_state.copy()
    
    for i in range(x_t.shape[0]):
        val = x_t[i]
        rising = val > curr_y
        
        diff = val - curr_y
        factor = np.where(rising, alpha_rise, alpha_fall)
        curr_y += factor * diff
        y_t[i] = curr_y
        
    return y_t

def time_weighting(
    x: List[float] | np.ndarray,
    fs: int,
    mode: str = "fast",
    initial_state: str | float | np.ndarray | None = None,
) -> np.ndarray:
    """
    Apply time weighting to a signal (Exponential averaging).
    
    :param x: Input signal (raw pressure/voltage). The function squares it internally.
    :param fs: Sample rate.
    :param mode: 'fast' (125ms), 'slow' (1000ms), 'impulse' (35ms rise, 1500ms fall).
    :param initial_state: Previous mean-square output state ``y[-1]``. Use None/'zero' for
        zero initialization (default), 'first' to initialize from the first input energy,
        or a scalar/array broadcastable to the input shape without the time axis.
    :return: Time-weighted squared signal (sound pressure level envelope).
    """
    x_proc = _typesignal(x)
    x_sq = x_proc**2
    initial = _prepare_time_weighting_initial_state(x_sq, initial_state)
    
    mode_lower = mode.lower()
    
    if mode_lower in ["fast", "slow"]:
        tau = 0.125 if mode_lower == "fast" else 1.0
        alpha = 1 - np.exp(-1 / (fs * tau))
        b = [alpha]
        a = [1, -(1 - alpha)]
        # We apply the weighting to the squared signal to get the Mean Square value
        zi = np.expand_dims((1 - alpha) * initial, axis=-1)
        y, _ = signal.lfilter(b, a, x_sq, axis=-1, zi=zi)
        return cast(np.ndarray, y)
        
    elif mode_lower == "impulse":
        # IEC 61672-1: 35ms for rising, 1500ms for falling
        tau_rise = 0.035
        tau_fall = 1.5
        
        alpha_rise = 1 - np.exp(-1 / (fs * tau_rise))
        alpha_fall = 1 - np.exp(-1 / (fs * tau_fall))
        
        # Move time axis to front for iteration
        x_t = np.moveaxis(x_sq, -1, 0)
        
        # Ensure contiguous array for Numba
        x_t = np.ascontiguousarray(x_t)
        initial_kernel = initial if initial.ndim == 0 else np.ascontiguousarray(initial)
        y_t = _apply_impulse_kernel(x_t, alpha_rise, alpha_fall, initial_kernel)
            
        # Move time axis back
        return np.moveaxis(y_t, 0, -1)

    else:
        raise ValueError("Invalid time weighting mode. Use ['fast', 'slow', 'impulse']")


def linkwitz_riley(
    x: List[float] | np.ndarray, 
    fs: int, 
    freq: float, 
    order: int = 4
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Linkwitz-Riley crossover filter (Butterworth squared).
    Splits signal into low and high bands with flat sum response.
    
    :param x: Input signal.
    :param fs: Sample rate.
    :param freq: Crossover frequency.
    :param order: Total order (must be even, typically 2 or 4).
    :return: (low_pass_signal, high_pass_signal)
    """
    x_proc = _typesignal(x)
    if order % 2 != 0:
        raise ValueError("Linkwitz-Riley order must be even (typically 2 or 4).")
    
    # A Linkwitz-Riley filter of order N is two Butterworth filters of order N/2 in series
    half_order = order // 2
    wn = freq / (fs / 2)
    
    sos_lp = signal.butter(half_order, wn, btype='low', output='sos')
    sos_hp = signal.butter(half_order, wn, btype='high', output='sos')
    
    # Pass twice
    lp = signal.sosfilt(sos_lp, x_proc)
    lp = signal.sosfilt(sos_lp, lp)
    
    hp = signal.sosfilt(sos_hp, x_proc)
    hp = signal.sosfilt(sos_hp, hp)
    
    return lp, hp
