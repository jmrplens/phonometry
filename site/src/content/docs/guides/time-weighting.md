---
title: "Time Weighting"
description: "Fast, Slow and Impulse ballistics per IEC 61672-1."
---

Accurate SPL measurement requires capturing energy over specific time windows.
phonometry implements exact time constants per **IEC 61672-1:2013**.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/time_weighting_analysis.png" alt="Fast, Slow and Impulse time weighting responses to a noise burst" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/time_weighting_analysis_dark.png" alt="Fast, Slow and Impulse time weighting responses to a noise burst" style="width:80%">

* **Fast (`fast`):** τ = 125 ms. Standard for noise fluctuations.
* **Slow (`slow`):** τ = 1000 ms. Standard for steady noise.
* **Impulse (`impulse`):** **Asymmetric** ballistics. 35 ms rise time for rapid
  onset capture, 1500 ms decay for readability.

```python
import numpy as np
from phonometry import time_weighting

# Calculate energy envelope (Mean Square)
energy_envelope = time_weighting(signal, fs, mode='fast')
# dB SPL relative to 20 μPa
spl_t = 10 * np.log10(energy_envelope / (2e-5)**2)
```

The asymmetric Impulse ballistics use two constants — a fast attack and a slow
decay — switching per sample on the sign of the change:

$$
y[n] = y[n-1] + \alpha \ (x^2[n] - y[n-1]), \qquad
\alpha = \begin{cases}1 - e^{-1/(f_s \cdot 0.035)} & x^2[n] > y[n-1]\\[2pt] 1 - e^{-1/(f_s \cdot 1.5)} & \text{otherwise}\end{cases}
$$

## The exponential detector

A sound level meter's needle cannot follow the pressure waveform — it shows a
running *mean square* with an exponential memory. Formally (IEC 61672-1, 3.8):

$$
\tau\ \frac{dy}{dt} + y = x^2(t)
\quad\Longleftrightarrow\quad
y(t) = \frac{1}{\tau} \int_{-\infty}^{t} x^2(\xi)\ e^{-(t-\xi)/\tau}\ d\xi
$$

a first-order low-pass on the squared signal. The time constant τ sets the
trade-off: **Fast** (125 ms) follows speech-like fluctuations, **Slow** (1 s)
steadies the readout for quasi-stationary noise. After a step onset the
envelope reaches 63 % of its final value in one τ and ~99.8 % after 8τ —
that is why level analyses discard the first instants of a recording.

### `time_weighting()` / `TimeWeighting` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `x` | 1D or 2D array | pressure (any scale) | non-empty | Squared internally; output is a mean-square envelope |
| `fs` | int | Hz | > 0 | |
| `mode` | str | — | `'fast'` (default), `'slow'`, `'impulse'` | τ = 125 ms / 1 s / 35 ms attack + 1.5 s decay |
| `TimeWeighting(fs, mode)` (class) | — | — | — | Stateful variant for streaming: `process(x)` carries the integrator state between blocks |

The output has the units of $x^2$: take `10*log10(y / p0**2)` for SPL or use
the level functions, which do it for you.

## Verified ballistics (IEC 61672-1 Table 4)

The Fast envelope's response to 4 kHz tonebursts lands exactly on the
standard's reference values — enforced in CI for burst durations from 1 s down
to 1 ms (F and S weightings, class 1 acceptance limits):

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tone_burst_iec.png" alt="Fast envelope responses to 200, 50 and 10 ms tone bursts peaking exactly at the IEC 61672-1 Table 4 reference values" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tone_burst_iec_dark.png" alt="Fast envelope responses to 200, 50 and 10 ms tone bursts peaking exactly at the IEC 61672-1 Table 4 reference values" style="width:80%">

## Initial state

By default, the exponential integrator starts from rest (`y[-1] = 0`). Passing
`initial_state=None` leaves this default unspecified, while `initial_state='zero'`
requests the same zero state explicitly. If the recorded segment begins after a
steady signal is already present, you can start from the first sample energy instead:

```python
energy_envelope = time_weighting(signal, fs, mode='fast', initial_state='first')
```

## Block processing

For block processing, pass the last output value from the previous block as the
next block's `initial_state` instead of resetting each block:

```python
state = None

for block in audio_blocks:
    energy_envelope = time_weighting(block, fs, mode='fast', initial_state=state)
    state = energy_envelope[-1]
```

For multichannel blocks with time on the last axis, carry one state per channel:
use `state = energy_envelope[..., -1]`. A scalar `initial_state` is applied to
every channel, while an array must match or broadcast to the non-time shape,
such as `(n_channels,)` for input shaped `(n_channels, n_samples)`.

Or let the `TimeWeighting` class carry the state for you:

```python
from phonometry import TimeWeighting

tw = TimeWeighting(fs, mode='fast')
for block in audio_blocks:
    energy_envelope = tw.process(block)
```

Concatenated block outputs are exactly equal to a single continuous call
(verified for all three modes, mono and multichannel). Call `tw.reset()` to
start from rest again.

## Performance note

The `impulse` mode uses an asymmetric kernel that is JIT-compiled when
[numba](https://numba.pydata.org/) is installed (`pip install phonometry[perf]`).
Without numba a pure-Python fallback produces identical results, just slower.

See [Integrated & Statistical Levels](/phonometry/guides/levels/) for Leq/LN metrics built on
these envelopes, and [Why phonometry](/phonometry/reference/why-phonometry/) for the IEC
61672-1 tone-burst verification.
