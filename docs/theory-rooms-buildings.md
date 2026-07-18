← [Documentation index](README.md)

# Theory: Rooms and Buildings

This page collects the theory behind rooms and buildings: impulse-response measurement and the room-acoustic parameters, background-noise criteria, airborne and impact insulation with their single-number ratings and uncertainty, flanking and absorption prediction, surface scattering and diffusion, and acoustic material characterisation. It is part of the [theory reference](theory.md).

## Room noise criteria (ANSI S12.2)

ANSI/ASA S12.2-2019 rates steady background noise in rooms against families of octave-band curves (16 Hz – 8 kHz). The **NC rating** uses the tangency method on the Table 1 curves (NC-15 to NC-70): each measured band is interpolated against the tabulated curve values, the rating is the highest per-band index and the band that sets it is the governing band; the interpolation makes the rating continuous (an NC-42.5 is reported as such, not snapped to a curve). The **RC Mark II** contour (Annex D) is a pure −5 dB/octave line keyed to its 1000 Hz value with a low-frequency floor of $\max(\mathrm{RC} + 25,\ 55)$ dB at 16/31.5 Hz; the rating is the arithmetic mean of the 500/1000/2000 Hz levels rounded to an integer (clause D.4), and the spectral-quality tag compares the spectrum with the reference contour (clause D.3): rumble "R" when any band at or below 500 Hz exceeds it by more than 5 dB, hiss "H" when any band at or above 1 kHz exceeds it by more than 3 dB (both together "RH"), else neutral "N", reported as e.g. RC-35(N). The generated RC contours reproduce Table D.1 digit for digit, and feeding any Table 1 NC curve back returns its own rating. NCB, RNC (Annex A) and the QAI (clause D.5) are deliberately out of scope.

See the [Room Noise guide](room-noise.md) for usage.

## Room and building acoustics (ISO 18233, ISO 3382, ISO 16283, ISO 10140, EN 12354, ISO 12999, ISO 717, ISO 354)

### Deterministic-excitation impulse response (ISO 18233)

A room/transmission path is modelled as **linear time-invariant**, so its impulse response $h(t)$ carries everything. ISO 18233 replaces the classical noise-burst decay with a deterministic excitation that is **deconvolved** into $h(t)$, gaining 20–30 dB of effective signal-to-noise ratio. The exponential sine sweep (ESS, Annex B) has instantaneous frequency $f(t) = f_1 (f_2/f_1)^{t/T}$, so its phase is the closed-form integral of $2 \pi f(t)$:

$$
\varphi(t) = \frac{2 \pi f_1 T}{\ln(f_2/f_1)} \left[ \left( \frac{f_2}{f_1} \right)^{t/T} - 1 \right] .
$$

A constant time-per-octave makes the ESS spectrum pink (−3 dB/octave). Deconvolution is done by **linear** (non-circular, zero-padded) spectral division $H = Y\ \overline{X} / (|X|^2 + \varepsilon)$, the Tikhonov term $\varepsilon$ (a fraction of $\max |X|^2$) preventing noise blow-up at the band edges. Since a low-to-high sweep places harmonic-distortion products at negative arrival times, they fall in the wrapped tail and are removed by keeping the causal part (Farina). The MLS method (Annex A) instead exploits that the circular autocorrelation of a maximum-length sequence of length $2^N-1$ is a periodic delta, so $h = \operatorname{xcorr}_{\text{circ}}(\text{recorded}, \text{mls}) / 2^N$; synchronous averaging of $n$ periods adds $10 \log_{10} n$ dB.

### Schroeder backward integration (ISO 3382-1, 5.3.3)

The band decay curve is the **backward-integrated** squared IR (Schroeder):

$$
E(t) = \int_t^{\infty} p^2(\tau)\ d\tau = \int_0^{\infty} p^2\ d\tau - \int_0^t p^2\ d\tau , \qquad L(t) = 10 \log_{10} \frac{E(t)}{E(0)}\ \text{dB},
$$

i.e. a reversed cumulative sum in discrete time. Backward integration cancels the random fluctuation of a single squared IR: for a purely exponential energy decay $p^2(t) = e^{-a t}$ it gives $E(t) = e^{-a t}/a$, an exactly straight line $L(t) = -(10 a / \ln 10)\ t$. Background noise flattens $E(t)$, so integration is truncated at the crossing $t_1$ of the fitted decay line with the noise level and the missing tail is compensated by an exponential with the fitted rate; without that term the finite integral systematically **underestimates** $T$.

### Regression windows and validity (ISO 3382-2, Clause 6, Annex B/C)

Reverberation time is a least-squares fit $L = a + b t$ over a window, extrapolated to 60 dB via $T = -60/b$ (Annex C): **EDT** on 0 to −10 dB, **T20** on −5 to −25 dB, **T30** on −5 to −35 dB. A single-slope decay gives EDT = T20 = T30; a fast early / slow late double slope gives EDT < T30. Validity uses the dynamic-range rule of 5.3.3: the noise must sit at least 25 dB below the IR peak for EDT (evaluation span + 15 dB), tightened to 46 dB for T20 and 54 dB for T30 so the tail-compensation bias of a flagged-valid value stays within the 5 % JND. The **curvature** $C = 100\ (T_{30}/T_{20} - 1)$ % (Annex B) flags a non-straight decay above 10 %.

### Clarity, definition and centre time (ISO 3382-1, Annex A)

Splitting the energy at an early/late boundary $t_e$ gives the early-to-late index and the definition ratio:

$$
C_{te} = 10 \log_{10} \frac{\int_0^{t_e} p^2\ dt}{\int_{t_e}^{\infty} p^2\ dt}\ \text{dB}, \qquad D_{50} = \frac{\int_0^{0.05} p^2\ dt}{\int_0^{\infty} p^2\ dt}, \qquad C_{50} = 10 \log_{10} \frac{D_{50}}{1 - D_{50}},
$$

with $t_e = 50$ ms (C50, speech) or 80 ms (C80, music), and the **centre time** $T_s = \int_0^{\infty} t\ p^2\ dt / \int_0^{\infty} p^2\ dt$. For a pure exponential decay these have closed forms $C_{te} = 10 \log_{10}(e^{a t_e} - 1)$ and $T_s = 1/a$; at $T = 1$ s ($a = 13.8155$) they evaluate to C80 = 3.05 dB, C50 = −0.02 dB, D50 = 0.499 and Ts = 72.4 ms, the values the implementation reproduces. Table A.1 JNDs (EDT 5 %, C80 1 dB, D50 0.05, Ts 10 ms) bound how finely each is worth reporting.

### Open-plan spatial decay (ISO 3382-3, Clause 6)

The spatial decay rate of A-weighted speech is the ordinary least-squares slope of $L_{p,A,S}$ against $\lg(r/r_0)$ ($r_0 = 1$ m) over the 2–16 m positions, rescaled to a per-doubling figure, and the nominal level is read off the same line at 4 m:

$$
L = a + b\ \lg(r/r_0), \qquad D_{2,S} = -\lg(2)\ b, \qquad L_{p,A,S,4\text{m}} = a + b\ \lg(4/r_0).
$$

The distraction distance rD and privacy distance rP are the distances where a **linear** (not logarithmic) regression of STI against distance crosses 0.50 and 0.20; a non-negative fitted slope (STI not falling with distance) makes them undefined, realising the standard's "can prove impossible to determine" note.

### Field insulation and weighted rating (ISO 16283-1, ISO 717-1)

Per one-third-octave band the level difference $D = L_1 - L_2$ (energy-averaged over microphone positions, $L = 10 \log_{10}[(1/n) \sum_i 10^{L_i/10}]$) is normalised two ways: the standardized level difference $D_{nT} = D + 10 \log_{10}(T/T_0)$ with $T_0 = 0.5$ s (so $D_{nT} = D$ when $T = T_0$), and the apparent sound reduction index $R' = D + 10 \log_{10}(S/A)$ with the Sabine absorption area $A = 0.16\ V / T$, hence $R' = D + 10 \log_{10}[S T / (0.16\ V)]$.

The single-number rating (ISO 717-1, Clause 4.4) shifts the Table 3 **reference curve** in 1 dB steps toward the measured curve until the sum of *unfavourable* deviations $\sum_i \max(0, \text{ref}_i + k - \text{meas}_i)$ is maximal but $\le$ 32.0 dB (16 thirds) or 10.0 dB (5 octaves); the rating $R_w$ is the shifted reference at 500 Hz. The **spectrum adaptation terms** are $C = X_{A1} - X_w$ and $C_{tr} = X_{A2} - X_w$ with $X_{Aj} = -10 \log_{10} \sum_i 10^{(L_{ij} - X_i)/10}$ (Table 4 spectra No. 1 pink noise, No. 2 urban traffic), each rounded to an integer. The ISO 717-1 Annex C worked example ($R_w = 30$, $C = -2$, $C_{tr} = -3$, unfavourable sum 31.8 dB) is reproduced exactly.

### Impact insulation and absorption (ISO 16283-2, ISO 717-2, ISO 354)

Impact insulation swaps the airborne source for a standardized **tapping
machine** and rates the receiving-room level, so the sign conventions flip. The
standardized and normalized impact levels are $L'_{nT} = L_i - 10 \log_{10}(T/T_0)$
(the reverberation term is *subtracted*, opposite to $D_{nT}$) and
$L'_n = L_i + 10 \log_{10}(A/A_0)$ with $A_0 = 10$ m² and $A = 0.16\ V/T$. The
ISO 717-2 rating shifts the Table 3 reference curve until $\sum_i \max(0, \text{meas}_i - (\text{ref}_i + k))$
is maximal but $\le$ 32.0 dB (16 thirds) or 10.0 dB (5 octaves); the
*unfavourable* deviation now counts where the **measurement exceeds** the
reference (impact noise is worse when louder), the mirror image of ISO 717-1.
The rating is the shifted reference at 500 Hz, reduced by a further 5 dB for
octave bands, and the adaptation term is $C_I = L_{n,\text{sum}} - 15 - L_{n,w}$
with the energetic sum $L_{n,\text{sum}} = 10 \log_{10} \sum_i 10^{L_i/10}$ over
100–2500 Hz (thirds) or 125–2000 Hz (octaves). The ISO 717-2 Annex C examples
are reproduced exactly (thirds $L_{n,w} = 79$, $C_I = -11$; octaves $54$, $0$),
via the same monotone shift search as ISO 717-1 run on the negated curves.

Sound absorption (ISO 354) measures the equivalent absorption area from
Sabine's relation applied to a reverberation room empty and with the specimen:
$A = 55.3\ V/(c\ T) - 4 V m$ (the $4 V m$ term is the air absorption, $m$ the
power attenuation coefficient in 1/m), so the specimen area is
$A_T = A_2 - A_1$ and its coefficient $\alpha_s = A_T/S$. With the speed of
sound from Eq. (6), $c = 331 + 0.6\ t$ (°C), and $m$ converted from an
ISO 9613-1 attenuation coefficient by $m = \alpha / (10 \lg e)$. Because
diffraction and edge scattering intercept more than the flat sample area,
$\alpha_s$ is left unclamped and may exceed 1.0 (Clause 3.7 NOTE 2).

### Laboratory vs field normalization (ISO 10140, ISO 16283)

The field indices carry a prime because they include flanking transmission
around the partition; the laboratory indices do not, because a qualified
facility suppresses it. The algebra is otherwise identical, differing only in
which quantity is normalised. The airborne pair is the direct laboratory sound
reduction index $R = L_1 - L_2 + 10 \log_{10}(S/A)$ (ISO 10140-2) versus the
apparent field index $R' = L_1 - L_2 + 10 \log_{10}(S/A)$ (ISO 16283-1), the
same closed form evaluated with the facility's known $A$ or the room's measured
$A = 0.16\ V/T$. The impact pair is the normalized laboratory level
$L_n = L_i + 10 \log_{10}(A/A_0)$ (ISO 10140-3) versus the field $L'_n$
(ISO 16283-2), both referenced to $A_0 = 10$ m². Before either is formed the
receiving-room level is corrected for background noise by the energy
subtraction $L = 10 \log_{10}(10^{L_{sb}/10} - 10^{L_b/10})$ for a 6–15 dB
signal-to-background margin, capped at a fixed $1.3$ dB (the limit of
measurement) at or below 6 dB and omitted at or above 15 dB (ISO 10140-4,
Clause 4.3), the laboratory analogue of the 6/10 dB rule of ISO 16283-1. The
façade extension (ISO 16283-3) replaces the source-room level by the level 2 m
in front of the façade, $D_{2m} = L_{1,2m} - L_2$, and adds a fixed
angle-of-incidence correction to the element sound reduction index, $-1.5$ dB
for the 45° loudspeaker method ($R'_{45°}$) and $-3$ dB for the all-angle
road-traffic method ($R'_{tr,s}$); all three carry the ISO 717-1 airborne
single number.

### Flanking transmission prediction (EN 12354-1/2)

The apparent field index is the energetic sum of the direct path $Dd$ and, for
each flanking element $F=f$ across its junction with the separating element, the
three paths $Ff$, $Df$ and $Fd$ (EN 12354-1, simplified single-number model,
Formula 26):

$$
R'_w = -10 \log_{10}\Big[ 10^{-R_{Dd,w}/10}
       + \sum 10^{-R_{Ff,w}/10} + \sum 10^{-R_{Df,w}/10}
       + \sum 10^{-R_{Fd,w}/10} \Big].
$$

The direct path is $R_{Dd,w} = R_{s,w} + \Delta R_{Dd,w}$ (Formula 27), the
separating-element laboratory index plus any lining improvement. Each flanking
path (Formula 28a) is

$$
R_{ij,w} = \frac{R_{i,w} + R_{j,w}}{2} + \Delta R_{ij,w} + K_{ij}
         + 10 \log_{10}\frac{S_s}{l_0\ l_f},
$$

with $R_{i,w}$, $R_{j,w}$ the laboratory indices of the two elements meeting at
the junction ($i$ source side, $j$ receiving side), $\Delta R_{ij,w}$ the
combined lining improvement, $S_s$ the separating-element area, $l_f$ the
junction coupling length and $l_0 = 1$ m the reference coupling length. $K_{ij}$
is the junction **vibration reduction index** (Annex E), an empirical function of
the mass ratio $M = \log_{10}(m'_{\perp,i}/m'_i)$: for a rigid cross-junction
$K_{13} = 8.7 + 17.1 M + 5.7 M^2$ (through) and $K_{12} = 8.7 + 5.7 M^2$
(corner), read at 500 Hz, and floored at $K_{ij,\min} = 10 \log_{10}[l_f\ l_0
(1/S_i + 1/S_j)]$ (Formula 29). Two linings combine as $\max(a,b) + \min(a,b)/2$
(Formulas 30/31). The impact counterpart (EN 12354-2, Formula 21) is the direct
subtraction $L'_{n,w} = L_{n,w,eq} - \Delta L_w + K$, with the bare-floor
equivalent level $L_{n,w,eq} = 164 - 35 \log_{10}(m'/m'_0)$ (Annex B), the
covering improvement $\Delta L_w$ (ISO 717-2) and the flanking correction $K$
from Table 1. The EN 12354-1 Annex H.3 ($R'_w = 52$ dB) and EN 12354-2 Annex E.3
($L'_{n,w} = 45$ dB) worked examples are reproduced exactly; the simplified
model is stated to have about a 2 dB standard deviation (Clause 5).

### Absorption in enclosed spaces (EN 12354-6)

EN 12354-6:2003 predicts the equivalent absorption area of a room from its
parts (the normative Clause 4 model). The total (Formula 1) sums the surfaces,
the objects and the air:

$$
A = \sum_i \alpha_{s,i}\ S_i + \sum_j A_{obj,j} + \sum_k \alpha_{s,k}\ S_k + A_{air},
\qquad A_{air} = 4\ m\ V\ (1 - \psi),
$$

with $m$ the power attenuation coefficient of air (Formula 2; Table 1
tabulates it for six temperature/humidity climates over the octave bands
125 Hz – 8 kHz), $\psi = \sum V_{obj} / V$ the volume fraction occupied by
objects (Formula 3), and a hard irregular object approximated by
$A_{obj} = V_{obj}^{2/3}$ (Formula 4). The reverberation time follows from
Sabine applied to the free volume (clause 4.4, Formula 5):

$$
T = \frac{55.3}{c_0}\ \frac{V\ (1 - \psi)}{A},
$$

with $c_0 = 345.6$ m/s chosen so that $55.3/c_0$ is the familiar $0.16$
(clause 4.4 NOTE). The three Annex E worked cases are reproduced: the
bare 29.75 m³ room gives $A = 2.26$ m² and $T = 2.1$ s at 1 kHz, and adding
hard objects ($\psi \approx 0.072$) raises $A$ to 5.03 m² and drops $T$ to
0.9 s. The informative Annex D method for irregular spaces and unevenly
distributed absorption is out of scope.

See the [Enclosed-Space Absorption guide](enclosed-space-absorption.md) for usage.

### Measurement uncertainty (ISO 12999-1)

ISO 12999-1 supplies the uncertainty of the quantities above from
inter-laboratory (ISO 5725) reproducibility and repeatability rather than a
GUM functional model. Three **measurement situations** fix the standard
uncertainty $u$: situation **A** (laboratory characterisation) uses the
reproducibility standard deviation $\sigma_R$; situation **B** (same location,
different teams) the in-situ $\sigma_{situ}$; situation **C** (same location,
operator and equipment, repeated) the repeatability $\sigma_r$. The per-band and
single-number values are tabulated for airborne $R$/$R'$/$D_n$/$D_{nT}$
(Tables 2/3), impact $L_n$/$L'_n$ (Table 4 bands, situations B/C only; Table 5
ratings adding a situation-A estimate) and the
covering reduction $\Delta L$ (Tables 6/7, situation A only). The expanded
uncertainty is $U = k\ u$ (Formula 2) with the coverage factor $k$ of Table 8
(at 95 %, $k = 1.96$ two-sided, $k = 1.65$ one-sided; a minimum $k = 1$ is
enforced). A two-sided interval $Y = y \pm U$ reports a value (Formula 3); a
one-sided factor declares conformity, $y - U > $ requirement for a lower limit
(Formula 5) or $y + U <$ requirement for an upper limit (Formula 4).
Uncorrelated components combine in quadrature $u_c = \sqrt{\sum u_i^2}$
(Formula C.2), $m$ independent measurements reduce $u$ to $u/\sqrt{m}$
(Formula A.7), and the uncorrelated single-number uncertainty is the
energy-weighted quadrature sum of the band uncertainties (Formula B.2).

See the [Room Acoustics](room-acoustics.md) and
[Field Insulation Measurement and Ratings](insulation-field.md) guides for usage.

## Surface scattering and diffusion (ISO 17497-1, ISO 17497-2)

### Random-incidence scattering coefficient (ISO 17497-1)

A rough surface splits the reflected energy into a specular and a scattered
part; the scattering coefficient $s$ is the non-specular energy fraction.
ISO 17497-1:2004+A1:2014 measures it in a reverberation room with the test
sample on a turntable: four reverberation times, stationary and rotating,
each without and with the sample (Table 2), give the random-incidence
absorption $\alpha_s$ (clause 8.1.1, Formula 1) and the *specular* absorption
$\alpha_{spec}$ (clause 8.1.2, Formula 4). Rotation decorrelates the scattered
reflections between decays, so they average out and register as extra
"absorption", and the scattering coefficient follows (clause 8.1.3,
Formula 5):

$$
s = \frac{\alpha_{spec} - \alpha_s}{1 - \alpha_s},
$$

each $\alpha$ being a two-condition Sabine difference
$55.3 (V/S) [1/(c_b T_b) - 1/(c_a T_a)] - 4 (V/S)(m_b - m_a)$ with
$c = 343.2 \sqrt{(273.15 + t)/293.15}$ (Formula 2) and $m$ from ISO 9613-1
via $m = \alpha_{dB}/(10 \lg e)$ (Formula 3). The base plate itself must
scatter little: Table 1 caps its coefficient (Formula 6) at 0.05–0.25 across
100 Hz – 5 kHz (clause 6.2). Negative $s$ is truncated to zero for
presentation (clause 8.3), but values above 1 near grazing bands are kept
(clause 6.3.2). The Annex A uncertainty chain ($u_\alpha$, Formulae A.3/A.4;
$u_s$, Formula A.5; $U = 2 u_s$) is implemented. Since the standard prints no
worked example, the oracle is a synthetic end-to-end chain
($V = 200$ m³, $S = 10$ m², $T = 8.0/6.0/7.5/5.0$ s → $s = 0.093$) plus the
Formula A.5 hand value $u_s = 0.0297$.

### Directional diffusion coefficient (ISO 17497-2)

ISO 17497-2:2012 measures, in the free field, how uniformly a surface spreads
its reflected polar response over $n$ microphones. The autocorrelation-based
coefficient (clause 8.1, Formula 5) is

$$
d_\theta = \frac{\left( \sum_i p_i \right)^2 - \sum_i p_i^2}{(n - 1) \sum_i p_i^2},
\qquad p_i = 10^{L_i/10},
$$

1 for a perfectly uniform response and tending to 0 for a single specular
lobe; Formula 6 is the area-weighted form with $N_i = A_i / A_{min}$ from the
Formula 8 solid-angle factors ($A_i = (4\pi/\Delta\phi) \sin^2(\Delta\theta/4)$
at the zenith). Normalizing against a flat reference reflector of the same
size removes edge diffraction (clause 8.2, Formula 7):
$d_{\theta,n} = (d_\theta - d_{\theta,r})/(1 - d_{\theta,r})$. The
random-incidence value averages the source angles with weights 1:3:3:3:3 for
0°, ±30°, ±60° (clause 8.4). Anchors: levels (70, 74, 68, 72) dB →
$d = 0.7367$; zenith area factor 1.5710.

See the [Surface Scattering guide](surface-scattering.md) for usage.

## In-situ road surface absorption (ISO 13472-1, ISO 13472-2)

ISO 13472-1:2002 (extended surface method) recovers the normal-incidence
absorption of a road surface in place, from one microphone above it: the
direct and reflected components of an impulse response are separated by the
**subtraction technique** and the **Adrienne window** (clause 6.4: a sharp
leading edge, a mandated 5 ms flat top and a Blackman-Harris trailing edge),
and

$$
\alpha(f) = 1 - \frac{1}{K_r^2} \left| \frac{H_r(f)}{H_i(f)} \right|^2,
\qquad K_r = \frac{d_s - d_m}{d_s + d_m} = \frac{2}{3}
$$

for the mandatory geometry $d_s = 1.25$ m, $d_m = 0.25$ m (clause 4.2,
Annex C); $K_r$ is the spherical-spreading ratio between the direct and the
image path. Ratioing the road measurement against one on a highly reflective
reference surface cancels the entire electro-acoustic chain along with $K_r$
(Annex B). The 5 ms window bounds the sampled area (Annex A closed form:
radius ≈ 1.34 m for the standard geometry) and the valid range is
250 Hz – 4 kHz in one-third octaves. ISO 13472-2:2010 (spot method,
250–1600 Hz) instead couples a small impedance tube to the surface and defers
the mathematics to the ISO 10534-2 transfer-function method below (its
clauses 4/5.7/6.6); the implementation reuses that module, adding the Part 2
geometry and validity limits ($f_u = 0.58\ c_0/d$; microphone spacing bounds
$0.45\ c_0/f_{max}$ and $0.05\ c_0/f_{min}$, clause 5.4) and the Annex A
subtractive correction for internal system losses.

See the [Surface Scattering guide](surface-scattering.md) for usage.

## Acoustic material characterisation (ISO 11654, ISO 9053-1/2, ISO 10534-1/2, ASTM E2611)

### Weighted sound absorption (ISO 11654)

ISO 11654:1997 condenses an ISO 354 third-octave absorption curve into a
single number. The practical coefficient $\alpha_p$ averages the three thirds
of each octave 250 Hz – 4 kHz and rounds to steps of 0.05 (clause 4.1). The
reference curve (0.80, 1.00, 1.00, 1.00, 0.90 at 250–4000 Hz) is then shifted
downward in 0.05 steps until the sum of unfavourable deviations, counted only
where the measurement falls *below* the shifted curve, is $\le 0.10$;
$\alpha_w$ is the shifted curve at 500 Hz (clause 4.2). A shape indicator
flags excess absorption $\ge 0.25$ above the shifted curve: L at 250 Hz, M at
500/1000 Hz, H at 2000/4000 Hz (clause 4.3), and the informative Annex B maps
$\alpha_w$ to the absorption classes A–E. Because every quantity is a multiple
of 0.05, the implementation does the whole grid arithmetic in integer
twentieths, making the shift search and class boundaries exact and
float-safe. The two Annex A worked examples are reproduced:
$\alpha_p = (0.35, 0.70, 0.65, 0.60, 0.55)$ → $\alpha_w = 0.60$, class C; and
raising 500 Hz to 1.00 keeps $\alpha_w = 0.60$ but adds the indicator, "0.60(M)".

### Airflow resistance (ISO 9053-1/2)

Airflow resistivity $\sigma = R\,A/d$ is the key transport parameter of a
porous absorber. ISO 9053-1:2018 (static method) drives a steady flow through
the specimen and fits $\Delta p = a\,u + b\,u^2$ through the origin
(clause 7.5); since $R_s = \Delta p / u = a + b\,u$, the linear coefficient is
the zero-velocity specific resistance, reported at the reference velocity
$u = 0.5$ mm/s. ISO 9053-2:2020 (alternating method) replaces the flowmeter
with a ~2 Hz piston and a microphone in a closed cavity (clause 8.7,
Formula 2):

$$
R = \kappa'\ \frac{p_s}{2 \pi f V}\ \frac{h_t}{h_s}\ 10^{(L_{ps} - L_{pt})/20}
$$

Only a level *difference* enters, so the sound-level device needs no
absolute calibration. The effective exponent $\kappa'$ (Annex A,
Formula A.7) corrects the adiabatic $\kappa$ for wall heat conduction through
the thermal boundary layer $b = \sqrt{2 c_0 l_h / \omega}$ (Formulae A.4/A.5).
The Annex A.3 worked example (100 mm closed cylinder at 2 Hz: $b = 1.83$ mm,
$\kappa' = 1.370 = 0.978\,\kappa$) is reproduced, and the validity guards of
Formula 3 (transfer ratio < 0.3) and Formula 4 (10 dB background margin) are
enforced.

### Impedance tube (ISO 10534-1, ISO 10534-2, ASTM E2611)

A tube below its cut-on frequency ($f d < 0.58\ c_0$ circular,
$< 0.50\ c_0$ rectangular; microphone-spacing limits $f s < 0.45\ c_0$ and
$f > c_0/(20 s)$; clauses 4.2–4.5) carries only plane waves, so the surface
reflection factor of a sample is fully observable. ISO 10534-2
(transfer-function method) compares the measured two-microphone transfer
function $H_{12}$ with the analytic incident and reflected ones
$H_I = e^{-j k_0 s}$, $H_R = e^{+j k_0 s}$ (Annex D) to give (clause 7,
Eq. 17):

$$
r = \frac{H_{12} - H_I}{H_R - H_{12}}\ e^{2 j k_0 x_1}, \qquad
\alpha = 1 - |r|^2, \qquad \frac{Z}{\rho c_0} = \frac{1 + r}{1 - r},
$$

with the complex wavenumber's attenuation lower bound
$k_0'' = 1.94 \times 10^{-2} \sqrt{f}/(c_0 d)$ (Eq. A.18). ISO 10534-1
(standing-wave-ratio method) is the closed-form classic:
$|r| = (s - 1)/(s + 1)$ from the max/min ratio $s = 10^{\Delta L/20}$ and the
phase from the first-minimum position (Eqs. 12–26); an SWR of 3 gives exactly
$|r| = 0.5$ and $\alpha = 0.75$. ASTM E2611-19 adds transmission: four
microphones decompose the up- and downstream fields into the $A, B, C, D$
waves (Eqs. 17–20) and a two-load (or symmetric one-load) solve yields the
specimen's 2×2 **transfer matrix** $[p; u]_0 = T\,[p; u]_d$ (Eqs. 16/22–24),
from which the anechoic-backing normal-incidence transmission loss is
(Eqs. 25/26)

$$
TL = 20 \lg \frac{\left| T_{11} + T_{12}/\rho c + \rho c\ T_{21} + T_{22} \right|}{2},
$$

plus the hard-backed reflection
$R = (T_{11} - \rho c\,T_{21})/(T_{11} + \rho c\,T_{21})$ (Eq. 27), the
material wavenumber $\arccos(T_{11})/d$ (Eq. 29) and the characteristic
impedance $\sqrt{T_{12}/T_{21}}$ (Eq. 30). The three standards deliberately
keep their own sign ansatz and temperature units (ISO in kelvin, ASTM in
Celsius), and near-singular load solves raise a warning. Since neither
standard prints a numeric example, the oracles are physics identities: the
analytic air-layer matrix ($\det T = 1$, $T_{11} = T_{22}$, TL = 0 dB,
hard-backed $|R| = 1$), synthetic round-trips that recover a known $r$, and
two-load recovery of an asymmetric reciprocal specimen.

See the [Materials guide](materials.md) for usage.

## References

- Kuttruff, H. (2016). *Room acoustics* (6th ed.). CRC Press.
  [doi:10.1201/9781315372150](https://doi.org/10.1201/9781315372150).
  The statistical decay theory behind backward integration and the Sabine
  relations used throughout this page.
- Schroeder, M. R. (1965). New method of measuring reverberation time.
  *The Journal of the Acoustical Society of America*, 37(3), 409-412.
  [doi:10.1121/1.1909343](https://doi.org/10.1121/1.1909343).
  The backward-integration method of the decay-curve section.
- Hak, C. C. J. M., Wenmaekers, R. H. C., & van Luxemburg, L. C. J. (2012).
  Measuring room impulse responses: Impact of the decay range on derived
  room acoustic parameters. *Acta Acustica united with Acustica*, 98(6),
  907-915. [doi:10.3813/aaa.918574](https://doi.org/10.3813/aaa.918574).
  The INR decay-range analysis behind the tightened T20/T30 validity
  thresholds.
- Beranek, L. L. (1957). Revised criteria for noise in buildings. *Noise
  Control*, 3(1), 19-27.
  [doi:10.1121/1.2369239](https://doi.org/10.1121/1.2369239).
  The original NC curves rated by the tangency method of the room-noise
  section.
- Blazier, W. E. (1997). RC Mark II: A refined procedure for rating the
  noise of heating, ventilating, and air-conditioning (HVAC) systems in
  buildings. *Noise Control Engineering Journal*, 45(6), 243-250.
  [doi:10.3397/1.2828446](https://doi.org/10.3397/1.2828446).
  The RC Mark II contour and spectral-quality tag codified by ANSI/ASA
  S12.2 Annex D.
- Hopkins, C. (2007). *Sound insulation*. Butterworth-Heinemann.
  ISBN 978-0-7506-6526-1.
  [doi:10.4324/9780080550473](https://doi.org/10.4324/9780080550473).
  The measurement chains, flanking transmission and EN 12354 prediction
  framework of the insulation sections.
- Vigran, T. E. (2008). *Building acoustics*. CRC Press.
  ISBN 978-0-415-42853-8.
  [doi:10.1201/9781482266016](https://doi.org/10.1201/9781482266016).
  Sound transmission in buildings, from single and double constructions to
  floating floors.
- Cox, T. J., & D'Antonio, P. (2017). *Acoustic absorbers and diffusers:
  Theory, design and application* (3rd ed.). CRC Press.
  ISBN 978-1-4987-4099-9.
  [doi:10.1201/9781315369211](https://doi.org/10.1201/9781315369211).
  Absorber and diffuser measurement and design, by the authors behind the
  ISO 17497-2 diffusion-coefficient method.
- Allard, J. F., & Atalla, N. (2009). *Propagation of sound in porous media:
  Modelling sound absorbing materials* (2nd ed.). Wiley.
  ISBN 978-0-470-74661-5.
  [doi:10.1002/9780470747339](https://doi.org/10.1002/9780470747339).
  The porous-material theory linking the airflow-resistance and
  impedance-tube quantities of the characterisation section.
- Acoustical Society of America. (2019). *Criteria for evaluating room
  noise* (ANSI/ASA S12.2-2019).
  [ANSI webstore](https://webstore.ansi.org/standards/asa/ansiasas122019).
  The normative NC tangency method and the Annex D RC Mark II rating with
  its spectral tag.
- International Organization for Standardization. (2006). *Acoustics —
  Application of new measurement methods in building and room acoustics*
  (ISO 18233:2006).
  [iso.org catalogue](https://www.iso.org/standard/40408.html).
  The swept-sine and MLS deconvolution of the deterministic-excitation
  section.
- International Organization for Standardization. (2009). *Acoustics —
  Measurement of room acoustic parameters — Part 1: Performance spaces*
  (ISO 3382-1:2009).
  [iso.org catalogue](https://www.iso.org/standard/40979.html).
  Backward integration, the parameter definitions and the Annex A clarity
  family.
- International Organization for Standardization. (2008). *Acoustics —
  Measurement of room acoustic parameters — Part 2: Reverberation time in
  ordinary rooms* (ISO 3382-2:2008).
  [iso.org catalogue](https://www.iso.org/standard/36201.html).
  The regression windows, dynamic-range rules and curvature check of the
  validity section.
- International Organization for Standardization. (2012). *Acoustics —
  Measurement of room acoustic parameters — Part 3: Open plan offices*
  (ISO 3382-3:2012).
  [iso.org catalogue](https://www.iso.org/standard/46520.html).
  The open-plan spatial decay and the distraction and privacy distances.
- International Organization for Standardization. (2014). *Acoustics — Field
  measurement of sound insulation in buildings and of building elements —
  Part 1: Airborne sound insulation* (ISO 16283-1:2014).
  [iso.org catalogue](https://www.iso.org/standard/55997.html).
  The field level differences and normalizations of the insulation
  sections.
- International Organization for Standardization. (2020). *Acoustics —
  Rating of sound insulation in buildings and of building elements — Part 1:
  Airborne sound insulation* (ISO 717-1:2020).
  [iso.org catalogue](https://www.iso.org/standard/77435.html).
  The reference-curve shift and the spectrum adaptation terms C and Ctr.
- International Organization for Standardization. (2003). *Acoustics —
  Measurement of sound absorption in a reverberation room* (ISO 354:2003).
  [iso.org catalogue](https://www.iso.org/standard/34545.html).
  The reverberation-room absorption measurement and its air-absorption
  term.
- European Committee for Standardization. (2003). *Building acoustics —
  Estimation of acoustic performance of buildings from the performance of
  elements — Part 6: Sound absorption in enclosed spaces*
  (EN 12354-6:2003).
  [BSI Knowledge record (BS EN 12354-6:2003)](https://knowledge.bsigroup.com/products/building-acoustics-estimation-of-acoustic-performance-of-buildings-from-the-performance-of-elements-sound-absorption-in-enclosed-spaces).
  The Clause 4 absorption model and Annex E worked cases of the
  enclosed-space section.
- International Organization for Standardization. (2020). *Acoustics —
  Determination and application of measurement uncertainties in building
  acoustics — Part 1: Sound insulation* (ISO 12999-1:2020).
  [iso.org catalogue](https://www.iso.org/standard/73930.html).
  The measurement situations, tabulated uncertainties and coverage factors
  of the uncertainty section.
- International Organization for Standardization. (2004). *Acoustics —
  Sound-scattering properties of surfaces — Part 1: Measurement of the
  random-incidence scattering coefficient in a reverberation room*
  (ISO 17497-1:2004+A1:2014, the edition implemented here).
  [iso.org catalogue](https://www.iso.org/standard/31397.html).
  The turntable scattering-coefficient method and its Annex A uncertainty
  chain.
- International Organization for Standardization. (2012). *Acoustics —
  Sound-scattering properties of surfaces — Part 2: Measurement of the
  directional diffusion coefficient in a free field* (ISO 17497-2:2012).
  [iso.org catalogue](https://www.iso.org/standard/55293.html).
  The free-field directional diffusion coefficient and its solid-angle area
  weighting.
- International Organization for Standardization. (1998). *Acoustics —
  Determination of sound absorption coefficient and impedance in impedance
  tubes — Part 2: Transfer-function method* (ISO 10534-2:1998; adopted in
  Europe as EN ISO 10534-2:2001; since revised as
  [ISO 10534-2:2023](https://www.iso.org/standard/81294.html)).
  [iso.org catalogue](https://www.iso.org/standard/22851.html).
  The two-microphone transfer-function method of the impedance-tube
  section.
- ASTM International. (2019). *Standard test method for normal incidence
  determination of porous material acoustical properties based on the
  transfer matrix method* (ASTM E2611-19, the edition implemented here;
  since revised as [ASTM E2611-24](https://store.astm.org/e2611-24.html)).
  [ASTM store](https://store.astm.org/e2611-19.html).
  The four-microphone transfer-matrix decomposition and its transmission
  loss.
- International Organization for Standardization. (2018). *Acoustics —
  Determination of airflow resistance — Part 1: Static airflow method*
  (ISO 9053-1:2018).
  [iso.org catalogue](https://www.iso.org/standard/69869.html).
  The static airflow-resistance method and its reference velocity.
