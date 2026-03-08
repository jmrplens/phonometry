import numpy as np
import pytest

@pytest.mark.parametrize("block_size", [8, 256, 1024])
@pytest.mark.parametrize("filter_type", ["A", "C", "Z"])
def test_weighting_filter_block_processing_matches_full_signal(block_size: int, filter_type: str):
    from pyoctaveband import WeightingFilter
    """
    Ensure that block-wise processing with preserved filter state
    produces the same result as filtering the full signal at once.
    """

    rng = np.random.default_rng(42)

    fs = 48000
    duration = 0.2
    n_samples = int(fs * duration)

    # Random signal (deterministic via seed)
    signal = rng.standard_normal(n_samples)

    stateless_wf = WeightingFilter(fs, filter_type)
    stateless_output = stateless_wf.filter(signal)

    stateful_wf = WeightingFilter(fs, filter_type, stateful=True)

    outputs = []
    for start in range(0, n_samples, block_size):
        block = signal[start:start + block_size]
        block_output = stateful_wf.filter(block)
        outputs.append(block_output)

    stateful_output = np.concatenate(outputs, axis=0)

    np.testing.assert_allclose(
        stateful_output,
        stateless_output,
        rtol=1e-10,
        atol=1e-12,
    )

def test_weighting_filter_steady_ic_initialization():
    from pyoctaveband import WeightingFilter
    # Create a stateful weighting filter with steady_ic=True
    wf = WeightingFilter(fs=48000, stateful=True, steady_ic=True)

    # Check that zi has the expected shape
    n_sections = wf.sos.shape[0]
    assert wf.zi.shape[0] == n_sections
    assert wf.zi.shape[1] == 2

