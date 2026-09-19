← [Documentation index](../README.md)

# The medium

Every other area of this library measures something that happened *in* a
medium. This one is the medium. A density and a speed of sound stand behind
every sound power level, every absorption coefficient, every transmission
loss and every propagation calculation in the tree, and for most of the
library's life they arrived the same way: as a number somebody typed once.

That is what this area exists to stop. `phonometry.fluids` computes the state
of the fluid from the conditions that were actually measured, keeps the
conditions beside the result, and says which model produced it.

Three media are built here. Humid air has the most carefully stated model in
the acoustic literature and gets a guide of its own below. Sea water has four
rival sound-speed fits and carries the one it was asked for. Any other gas is
`fluids.ideal_gas`, which takes the ratio of specific heats and the molar mass
that a gas table prints and returns the speed and density that follow, with
how far that closure goes written into the result.

## The airs of this library, and why there are four of them

A density and a speed of sound stand behind every level the library computes,
and they do not all come from the same place. Four states sit in the tree, one
beside each model or standard that fixes it, and they disagree:

| Key | c (m/s) | rho (kg/m3) | What fixes it |
| --- | ---: | ---: | --- |
| `iec-61094-2-annex-f/air` | 345,87 | 1,186 | IEC 61094-2 Annex F at the ISO 9053-2 Annex A.3 reference state |
| `allard-2009-jca/air` | 343 | 1,205 | the constants the Johnson-Champoux-Allard model was published with |
| `en-12354-annex-a/air` | 340 | 1,29 | EN/ISO 12354, the Annex A speed and the Annex B density |
| `phonometry-solver/air` | 343 | 1,2 | this library's own default for the acoustic solver |

None of them is wrong. Each is the air its own document assumes, and
substituting one for another would change the number that document prints: the
1,7 per cent between the metrology annex and the building standard is a real
disagreement between two committees, not a rounding.

Each one stays where it is, beside the clause that prints it. Gathering them
into this package would invert the dependency it exists at the bottom of: any
domain may import `fluids` without an architecture edge, and a catalogue here
that reached into `materials`, `building` and `simulation` would make the
medium depend on three of the domains that stand on it. The comparison is a
documentation artefact instead, and the [published
catalogues](https://jmrplens.github.io/phonometry/reference/catalogues/) page lists all four side by
side.

What `fluids.PUBLISHED_FLUIDS` does hold is the states this library read from
a printed page: the three fluids Bies prints at the head of his Table C.1, air,
fresh water and sea water, each naming that page, with the printed folio, in
its `model`, because for a state that was read rather than computed the table
is what produced it.

It is not a table to look values up in. Air at conditions that were measured is
`fluids.air`, sea water is `fluids.sea_water`, and both compute the state
rather than recall it.

## Why it is not a domain

Sixteen of the twenty-one packages are domains of application: you go to
`building` because you are measuring a building, to `underwater` because you
are working in water. You never go to `fluids` because you are measuring a
fluid. You go there because whatever else you are measuring happens in one.

So it sits with `filters`, `signals` and `metrology` in the transverse
toolbox: any package may import it without an architecture edge, because a
medium is not a subject some domains have and others do not. It was the fourth
member of that set, the first added since the library split the original
toolbox in three, and `solids` is the fifth.

## Three kinds of number, deliberately kept apart

The reason a library ends up with a dozen different values for the density of
air is that three different things wear the same clothes.

**The physics of the fluid** is what lives here. It answers "what is this air,
at these conditions", and better physics is an improvement: when the model
gets more accurate, every caller who asked for air should get the more
accurate answer.

**A standard's own simplified formula** is not that. When ISO 10534-2 prints
$c_0 = 343{,}2\sqrt{T/293}$, that expression is part of the procedure, and a
measurement that claims to follow the standard has to use it. Those stay in
the module that implements their clause, with the citation beside them, and
they never move here.

**A constant frozen by a conformance row** is a third thing again. The
Johnson-Champoux-Allard model carries a Prandtl number of 0,71 as a published
constant of the model. The air at the reference state has 0,728. Substituting
the physical value into the model would not correct an error, it would change
the model, and it moves the impedance it computes by 1,5 parts in a thousand.
That constant stays frozen where it was published.

Keeping the three apart is what lets better physics reach a caller without a
single measurement silently ceasing to reproduce the standard it cites.

**No solids.** A `Fluid` carries no shear speed, and the elastic materials of
the wave solvers keep their own type with its own precondition. The two are
different quantities that happen to share the word "medium", and a solid's
properties are tabulated where a fluid's are computed: they live next door, in
`phonometry.solids`.

**No fields, only states.** A `Fluid` is one fluid at one point. The
stratified profiles that ray tracers march through stay in the packages that
own their marchers, in the ocean and in the atmosphere, because a profile is
a description of a place rather than of a substance.

**No frequency dependence.** The speed of sound here is the zero-frequency
one. Molecular relaxation makes sound speed depend on frequency, and the
model that describes it lives with the atmospheric absorption that needs it,
in `phonometry.environment`.

## What is here

- [Humid air](humid-air.md): the CIPM-2007 formulation of
  IEC 61094-2:2009 Annex F, what it fixes and what it does not, how much each
  condition is worth, and why the library asks for the temperature but assumes
  the pressure out loud.
