← [Documentation index](../../README.md)

# Vibration immission

*Immission* is the German term for what arrives, as against *emission*, what
leaves: the vibration a building or the people in it actually receive, wherever
it came from. It is regulated on that side of the transmission path, and the
documents that do it are a set rather than a single standard. DIN 4150-2 fixes
what people in buildings may be exposed to; DIN 4150-3 fixes what the buildings
themselves may take; DIN 45669-1 specifies the **instrument** both of them
presuppose, and DIN 45669-2 the procedure it is used with.

This section is the instrument half of that set. The other half already has a
page: the guideline values of DIN 4150-3 are in [Vibration damage to
structures](../structural/structural-damage.md), and they used
to say, at the end, that the instrument requirements of DIN 45669 were not
implemented. They are now, which closes the loop: the quantity a guideline
value is compared against is defined by the meter, and the meter is defined by
its band limitation, its KB weighting and the running r.m.s. it averages them
with.

The section also carries the piece of DIN 45669-1 that reaches furthest into
practice. Annex E turns the frequency-dependent guideline curve of DIN 4150-3
into three filters, one per building class, and with them a short-term event is
judged against a single number instead of against a curve read at a frequency
two methods disagree about.

## Pages in this section

- [Measuring vibration immission (DIN 45669-1)](vibration-meter.md):
  the band limitation and KB weighting of Formulae (3) and (4), the weighted
  vibration severity and the clock maximum r.m.s. of Formulae (1) and (2), the
  tolerance bands of Tables 2 and 3, the printed check values of Tables 8 and
  9, and the assessment velocity of Annex E (DIN 45669-1:2010-09 with
  Corrigendum 1:2012-12).

## See also

- [Vibration damage to structures (DIN 4150-3)](../structural/structural-damage.md):
  the guideline values this chain produces the numbers for.
- [Verifying a human-vibration meter (ISO 8041-1)](../human/meter-verification.md):
  the same idea for the meter that measures vibration on people, with its own
  weightings and its own tolerance tables.
- [Building response and fundamental frequency (ISO 4866)](../structural/building-response.md):
  the frequency a building answers at, which is a different question from the
  frequency of the event.

## What this section does not cover

**No measurement procedure.** DIN 45669-2 fixes the measurement positions, the
coupling of a transducer to a floor or to the ground, the measurement duration
and the disturbances that have to be kept out. None of it is arithmetic and
none of it is here.

**No assessment of people in buildings.** DIN 4150-2 judges what the weighted
vibration severity means for the people who feel it, with its own tables of
reference values by time of day and use of the room. The quantity is computed
here; the judgement it feeds is not implemented.

**Nothing about railways yet.** DIN 45672 measures and evaluates vibration
next to railway lines, which is what the 4 Hz to 315 Hz working range of the
meter is for. Its evaluation method is not implemented.
