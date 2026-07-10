← [Documentation index](README.md)

# Speech Intelligibility Index (SII)

The **Speech Intelligibility Index** predicts how much of a speech signal is
audible, and therefore intelligible, to a listener in a given noise and hearing
condition. It reduces a speech spectrum, a noise spectrum and a hearing
threshold to a single number in `[0, 1]`: `0` when nothing useful reaches the
listener, `1` when the whole speech-bearing spectrum is audible. This page
covers the **one-third-octave-band method** of **ANSI S3.5-1997 (R2017)** — 18
bands from 160 Hz to 8000 Hz.

> [!NOTE]
> **SII vs STI.** The SII predicts intelligibility from *audibility* — how much
> of the speech spectrum clears the noise and the hearing threshold at the
> listener's ear — while the STI characterises a *transmission channel*: how
> much of the speech modulation a room or sound system preserves. For the
> latter, see the [Speech Transmission Index guide](speech-transmission.md).

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_speech_intelligibility_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_speech_intelligibility.svg" alt="The SII computation flow: three equivalent-spectrum-level inputs (speech Ei', noise Ni', hearing threshold Ti') feed the self-speech masking and spread-of-masking stage (equivalent masking spectrum level Zi), then the equivalent disturbance Di, then the band-audibility function Ai clipped to [0, 1], and finally the band-importance-weighted sum SII = sum of Ii*Ai over the 18 one-third-octave bands" width="94%"></picture>

## 1. Inputs and the band-importance function

All three inputs are **equivalent spectrum levels** (ANSI S3.5-1997 clauses 3.11
and 3.55) sampled at the 18 one-third-octave band centres: the speech spectrum
level `Ei'`, the noise spectrum level `Ni'` (both in dB SPL) and the hearing
threshold `Ti'` (in dB HL). Each band `i` contributes to intelligibility in
proportion to its **band-importance function** `Ii` (ANSI S3.5-1997 Table 3,
average speech material), which sums to one across the 18 bands.

```python
import phonometry as ph

# The standard normal-effort speech spectrum (Table 3) in quiet, normal hearing.
result = ph.speech_intelligibility_index("normal")
print(round(result.sii, 3))          # 0.996  (nearly everything audible)
print(round(ph.sii.BAND_IMPORTANCE.sum(), 6))   # 1.0
```

With no noise and a normal hearing threshold the standard speech spectrum is
almost fully audible, so the index is close to one; the small deficit is the
listener's own **self-speech masking**.

## 2. Masking and the band-audibility function

The procedure (ANSI S3.5-1997 clause 5) turns the inputs into a per-band
audibility. Speech masks itself downward from each band (`Vi = Ei' - 24`); the
larger of that and the external noise, `Bi`, spreads **upward** in frequency
with a level-dependent slope to give the equivalent masking spectrum level `Zi`
(clause 5.4):

$$
Z_i = 10\log_{10}\!\left(10^{0.1 N_i'} + \sum_{k<i}
      10^{0.1\left(B_k + 3.32\,C_k\,\log_{10}(0.89\,f_i/f_k)\right)}\right).
$$

The masking is combined with the equivalent internal noise
(`Xi' = Xi + Ti'`, the reference internal noise shifted by the hearing loss)
into the **equivalent disturbance** `Di` (clause 5.6), and the **band-audibility
function** is the speech-to-disturbance ratio scaled into `[0, 1]` (clause 5.8):

$$
A_i = \operatorname{clip}\!\left(\frac{E_i' - D_i + 15}{30},\; 0,\; 1\right).
$$

At speech levels well above normal effort a **level-distortion factor** of
clause 5.7 — unity for the standard spectra used on this page — reduces $A_i$
further; phonometry applies it automatically.

## 3. The index in noise

The Speech Intelligibility Index is the band-importance-weighted sum of the band
audibilities (ANSI S3.5-1997 clause 6):

$$
\text{SII} = \sum_{i} I_i\, A_i .
$$

```python
import numpy as np
import phonometry as ph

speech = ph.standard_speech_spectrum("normal")
# A descending broadband masking noise (an office/ventilation-like spectrum).
noise = np.array([38.0, 37.0, 36.0, 34.0, 32.0, 30.0, 28.0, 26.0, 24.0,
                  22.0, 20.0, 18.0, 16.0, 14.0, 12.0, 10.0, 8.0, 6.0])

result = ph.speech_intelligibility_index(speech, noise)
print(round(result.sii, 2))                # 0.46
print(result.band_audibility.round(2))     # per-band Ai
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/speech_intelligibility_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/speech_intelligibility.svg" alt="Band audibility of the standard normal-effort speech spectrum in a descending broadband noise: the light bars are the per-band audibility Ai across the 18 one-third-octave bands from 160 Hz to 8000 Hz, the darker bars the importance-weighted contribution Ii*Ai (scaled), and the overall SII is 0.46" width="90%"></picture>

<details>
<summary>Show the code for this figure</summary>

```python
import numpy as np
import matplotlib.pyplot as plt
import phonometry as ph

speech = ph.standard_speech_spectrum("normal")
noise = np.array([38.0, 37.0, 36.0, 34.0, 32.0, 30.0, 28.0, 26.0, 24.0,
                  22.0, 20.0, 18.0, 16.0, 14.0, 12.0, 10.0, 8.0, 6.0])
result = ph.speech_intelligibility_index(speech, noise)

# One line:
result.plot()
plt.show()

# By hand, mirroring what SIIResult.plot() draws:
pos = np.arange(result.frequencies.size)
weighted = result.band_audibility * result.band_importance
fig, ax = plt.subplots()
ax.bar(pos, result.band_audibility, color="#c6dbef", label=r"Band audibility $A_i$")
ax.bar(pos, weighted / weighted.max(), width=0.5, color="#1f77b4",
       label=r"Importance-weighted $I_i A_i$ (scaled)")
ax.set_xticks(pos)
ax.set_xticklabels([f"{f:g}" for f in result.frequencies], rotation=45, ha="right")
ax.set_xlabel("One-third-octave band [Hz]")
ax.set_ylabel("Band audibility")
ax.set_title(f"SII = {result.sii:.2f}")
ax.legend()
plt.show()
```

</details>

A raised hearing threshold (`threshold=`) lifts the equivalent internal noise
and lowers the index, exactly as added masking noise does. The
`SIIResult` also carries the per-band masking `Zi`, disturbance `Di`, audibility
`Ai` and importance `Ii`, and its `.plot()` renders the figure above.

## 4. Vocal effort

Talkers raise their voice in noise, and the standard gives four **standard
speech spectra** for the vocal efforts *normal*, *raised*, *loud* and *shout*
(ANSI S3.5-1997 Table 3). Passing the effort name selects the corresponding
spectrum; speaking louder lifts the whole spectrum and, in a fixed noise, raises
the index.

```python
import numpy as np
import phonometry as ph

# The same broadband noise, four vocal efforts.
noise = np.array([48.0, 47.0, 46.0, 44.0, 42.0, 40.0, 38.0, 36.0, 34.0,
                  32.0, 30.0, 28.0, 26.0, 24.0, 22.0, 20.0, 18.0, 16.0])
for effort in ph.sii.VOCAL_EFFORTS:
    print(effort, round(ph.speech_intelligibility_index(effort, noise).sii, 2))
# normal 0.12 | raised 0.36 | loud 0.59 | shout 0.79

print(ph.standard_speech_spectrum("loud")[8])  # 42.16 dB SPL at 1 kHz
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sii_vocal_efforts_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sii_vocal_efforts.svg" alt="Two panels. Left: the four ANSI S3.5-1997 standard speech spectra — normal, raised, loud and shout — over the 18 one-third-octave bands from 160 Hz to 8000 Hz, each higher vocal effort lifting the whole spectrum. Right: the resulting Speech Intelligibility Index in a fixed broadband noise, rising from 0.12 (normal) through 0.36 and 0.59 to 0.79 (shout)" width="96%"></picture>

<details>
<summary>Show the code for this figure</summary>

```python
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter
import phonometry as ph

# The four ANSI S3.5-1997 Table 3 spectra and the fixed broadband noise above.
noise = np.array([48.0, 47.0, 46.0, 44.0, 42.0, 40.0, 38.0, 36.0, 34.0,
                  32.0, 30.0, 28.0, 26.0, 24.0, 22.0, 20.0, 18.0, 16.0])
efforts = ph.sii.VOCAL_EFFORTS         # ("normal", "raised", "loud", "shout")
freqs = ph.sii.BAND_CENTERS            # the 18 one-third-octave band centres

fig, (ax_s, ax_i) = plt.subplots(1, 2, figsize=(12, 5))

# Left: each higher vocal effort lifts the whole speech spectrum.
for effort in efforts:
    ax_s.plot(freqs, ph.standard_speech_spectrum(effort), "o-",
              label=effort.capitalize())
ax_s.set_xscale("log")
ax_s.set_xticks(list(freqs))
ax_s.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
ax_s.xaxis.set_minor_formatter(NullFormatter())
ax_s.set_xlabel("One-third-octave band [Hz]")
ax_s.set_ylabel("Speech spectrum level [dB SPL]")
ax_s.legend()

# Right: the SII each spectrum reaches in the fixed noise.
sii = [ph.speech_intelligibility_index(e, noise).sii for e in efforts]
pos = np.arange(len(efforts))
ax_i.bar(pos, sii)
ax_i.set_xticks(pos)
ax_i.set_xticklabels([e.capitalize() for e in efforts])
ax_i.set_ylim(0.0, 1.0)
ax_i.set_ylabel("Speech Intelligibility Index")
plt.show()
```

</details>

The vocal-effort names work anywhere a speech spectrum is expected, including as
the first argument to `speech_intelligibility_index`.

---

**Standards.** ANSI S3.5-1997 (R2017), *American National Standard Methods for
the Calculation of the Speech Intelligibility Index* — the one-third-octave-band
method (18 bands), band-importance function (Table 3), standard speech spectrum
level and reference internal noise (Table 3), and the masking, disturbance and
band-audibility procedure (clause 5) and the index (clause 6).
