← [Documentation index](../README.md)

# Vibration and structure-borne sound

Vibration matters to acoustics three times over. First as a **source of
sound**: a pump or fan bolted to a building injects structure-borne power that
travels through walls and floors and re-radiates as audible noise rooms away.
Second as a **human exposure** in its own right: vibration transmitted to a
standing, seated or hand-gripping person is measured, weighted and limited much
like noise, with its own metrics and legal action values. Third as a
**diagnosis of the machine itself**: the same spectrum that feeds the first two
questions also names the bearing, gear or blade that produced it, because every
periodicity in it belongs to something that turns, meshes or passes, at a
frequency fixed by the geometry.

The **structure-borne sources** pages follow the source chain in order. The
frequency-response-function family of ISO 7626 (receptance, mobility,
accelerance) is the vocabulary; the wave-approach transmission coefficients of
a plate junction describe the structure the power then runs through; the
transfer stiffness of ISO 10846 characterises the resilient elements that
interrupt that path; ISO/TS 7849 estimates the airborne power a vibrating
surface radiates directly; EN 15657 measures the structure-borne power a
machine injects into a reception plate; and EN 12354-5 assembles all of it into
the sound pressure level predicted in a receiving room. That final prediction
is also where this section hands over to the [sound
insulation](../buildings/insulation/index.md) models of the buildings section.
The same group holds the one question that is not about sound at all: whether
the shaking damages the building, which DIN 4150-3 answers with guideline
values for the peak particle velocity, read at the dominant frequency of the
measured vibration. ISO 4866 Annex D estimates a different frequency, the
building's own, from its height or its number of storeys when no modal
measurement was made; the two meet only where the response is the building
answering at that frequency, which is what the topmost floor plane and the
floor of Clause 5.2 are about.

The **human vibration** pages share the measurement philosophy of a sound
level meter, applied to acceleration: frequency weightings that reflect body
response, running and integrated averages, and dose quantities compared
against the action and limit values of Directive 2002/44/EC, plus the
dedicated spinal-response model for vibration containing repeated shocks.
They also cover the one piece of hardware between the machine and the person:
the seat, measured by the laboratory method of ISO 10326-1, which answers with
a single ratio whether the seat attenuates what it is given or amplifies it.

Start with
[Mechanical mobility and the FRF family](structural/mechanical-mobility.md)
if you care about the noise a machine causes in a building, with
[Human Vibration](human/human-vibration.md) if you care
about the dose a person receives, or with [Machine fault
frequencies](machinery/machine-diagnostics.md) if you care
about the condition of the machine itself.

## [Structure-borne sources](structural/index.md)

From FRF vocabulary to the predicted level in a receiving room.

- [Mechanical mobility and the FRF family (ISO 7626-1)](structural/mechanical-mobility.md):
  receptance, mobility and accelerance with their reciprocals, and the SDOF
  reference resonator.
- [Bending-wave transmission at plate junctions (Cremer/Craik/Hopkins)](structural/junction-transmission.md):
  the frequency-independent wave-approach coefficients for rigid X, T, L and
  in-line junctions, their angular average and the derived coupling loss factor
  and Kij, and the experimental route that measures the same coupling loss
  factors by power injection.
- [Transfer stiffness of resilient elements (ISO 10846)](structural/transfer-stiffness.md):
  the dynamic transfer stiffness of vibration isolators by the direct and
  indirect methods.
- [Sound power from surface vibration (ISO/TS 7849)](../devices/emission/vibration-sound-power.md):
  radiated airborne power from surface velocity and a radiation factor.
- [Structure-borne sound power of equipment (EN 15657)](../buildings/design/structure-borne-power.md):
  the reception-plate method and the plate-independent source quantities.
- [Installed structure-borne sound (EN 12354-5)](../buildings/design/installed-structure-borne.md):
  the receiving-room sound pressure level predicted from source and receiver
  mobilities.

## [Human vibration](human/index.md)

Vibration transmitted to the human body, from daily exposure to spinal injury
risk.

- [Human Vibration](human/human-vibration.md): whole-body and
  hand-arm weightings (ISO 8041-1), r.m.s. and dose measures (ISO 2631-1),
  daily exposure A(8) (ISO 5349) and the Directive 2002/44/EC values.
- [Multiple-shock whole-body vibration (ISO 2631-5)](human/multiple-shock-vibration.md):
  the spinal-response model and the probability of lumbar injury for vibration
  containing multiple shocks.
- [What a seat does to the vibration (ISO 10326-1)](human/seat-vibration.md):
  the SEAT factor of a laboratory seat test, the correction to the input the
  test intended, and the transmissibility at resonance of the damping test.
- [Verifying a human-vibration meter (ISO 8041-1)](human/meter-verification.md):
  the tolerance band on each frequency weighting, the characteristic phase
  deviation, the running r.m.s. decay and the saw-tooth burst indications a
  conforming meter has to reproduce.

## [Machinery](machinery/index.md)

Turning a vibration spectrum into a diagnosis of the machine that made it.

- [Machine fault frequencies](machinery/machine-diagnostics.md):
  the characteristic bearing, gear and shaft frequencies, and the envelope
  analysis that finds them under the broadband noise of a running machine.

## [Vibration immission](immission/index.md)

The instrument the German immission-control standards presuppose, and the
assessment it makes possible.

- [Measuring vibration immission (DIN 45669-1)](immission/vibration-meter.md):
  the KB weighting and the weighted vibration severity a DIN 4150 measurement
  is reported in, the tolerance bands a meter is graded by, and the Annex E
  assessment velocity that judges a building without a dominant frequency.

## What this section does not cover

**An instrument is graded on the clauses that can be computed.** Every
criterion of ISO 8041-1 that is arithmetic is implemented, on the [meter
verification](human/meter-verification.md) page: the
tolerance band around each frequency weighting, the band-limiting stage on its
own, the characteristic phase deviation, the running r.m.s. decay times and
the 228 saw-tooth burst indications the standard prints. The rest of that standard, the indication,
linearity, overload, temperature, humidity and electromagnetic clauses, is a
set of laboratory tests on hardware, so a pass here is a necessary condition
for conformity and never a certificate of it.

**No severity verdict is issued for a machine.** The machinery pages predict
*where* a line would be, never whether it is present or whether the machine is
in trouble: the amplitude criteria that turn a present line into an assessment
— crest-factor and kurtosis trending, and the velocity severity bands of ISO
10816 / ISO 20816 — are outside the library, as are rotor balancing (ISO 21940)
and order tracking.

**Nor is one issued for what people feel in a building.** The 2003 edition of
ISO 2631-2 deleted its predecessor's guidance values on purpose, so for the
human response to building vibration there are no acceptable magnitudes to
compare against; what the library gives is the weighted magnitude, and the
judgement stays with the assessor and the national code. The guideline values
of [DIN 4150-3](structural/structural-damage.md) are a
different question and are implemented: they are about damage to the structure,
and keeping to one is not a certificate any more than exceeding one is a
finding of damage.

Two structural predictions are idealisations rather than measurements. The
junction transmission coefficients are a closed-form result for a rigid,
simply supported junction — the *measured* vibration reduction index of ISO
10848 is [Laboratory flanking
transmission](../buildings/insulation/flanking-lab.md) — and the FRF
page returns element-wise free reciprocals, correct for a driving-point or
single-path use but not a full FRF matrix, with no impact-hammer processing
(ISO 7626-5) and no blocked matrix quantities. On the isolator page, parts 4
and 5 of ISO 10846 are not implemented, and two of the standard's validity
checks (the blocking-mass inequality and the clause 7.6 linearity criterion)
are described but not computed for you.

## Before and after these pages

Every quantity here starts from an acceleration record and a spectral estimate,
so the filtering, the weighting curves and the spectral estimators behind them
are in [Signal analysis](../signals/index.md), and [Spectral
analysis](../signals/spectra/spectral-analysis.md) is the page the
machinery diagnostics build on. The derivations are in [Vibration
theory](../reference/theory/vibration.md): the human-vibration weightings, the ISO 2631-5
shock model and the point mobilities and radiation efficiency.

If you arrived here from a search and want the shape of the whole library,
[What do you need to measure?](https://jmrplens.github.io/phonometry/start/tasks/) indexes it by the job
and [All guides](../README.md) lists every page with a line on
each.
