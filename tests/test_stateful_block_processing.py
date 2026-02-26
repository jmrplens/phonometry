import numpy as np
import pytest

from pyoctaveband import OctaveFilterBank


from matplotlib import pyplot as plt

def test_block_processing_matches_full_signal():
    """
    Ensure that block-wise processing with preserved filter state
    produces the same result as filtering the full signal at once.
    """

    rng = np.random.default_rng(42)

    fs = 48000
    duration = 2.0
    n_samples = int(fs * duration)

    # Random signal (deterministic via seed)
    signal = rng.standard_normal(n_samples)

    # --- Full signal processing (reference) ---
    full_filter = OctaveFilterBank(fs=fs, resample=False)
    full_output_spl, _, full_output_signal = full_filter.filter(signal, sigbands=True, detrend=False)

    # --- Block-wise processing ---
    block_filter = OctaveFilterBank(fs=fs, resample=False, stateful=True, steady_ic=False)

    block_size = 1024
    outputs = []

    for start in range(0, n_samples, block_size):
        block = signal[start:start + block_size]
        block_output_spl, _, block_output_signal = block_filter.filter(block, sigbands=True, detrend=False)
        outputs.append(block_output_signal)

    block_output_signal = np.concatenate(outputs, axis=-1)
    full_output_signal = np.array(full_output_signal)

    # --- Comparison ---
    # Use tight tolerance; sosfilt should be numerically identical
    np.testing.assert_allclose(
        block_output_signal,
        full_output_signal,
        rtol=1e-10,
        atol=1e-12,
    )
