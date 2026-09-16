← [Documentation index](../README.md)

# Elastic solids

A plate transmits sound because it bends, and how it bends is decided by three
numbers: a density, a Young's modulus and a Poisson ratio. Fifteen public
functions in this library ask for one or two of them, and the tables that print
them, in Hopkins, in Cremer, in Mechel, in Bies, rarely print the same pair.
One book gives a wave speed and no modulus. The next gives a modulus and no
speed. A third gives the product of thickness and critical frequency and
neither.

`phonometry.solids` is where the conversions between them live, so that they
are written once instead of in each caller's head.

## Why it is not a domain

Sixteen of the twenty-one packages are domains of application: you go to
`building` because you are measuring a building, to `underwater` because you
are working in water. Nobody goes to `solids` because they are measuring a
solid. They go there because whatever they are measuring happens in one, or
through one.

So it sits beside `fluids` in the transverse toolbox with `filters`, `signals`
and `metrology`: any package may import it without an architecture edge,
because a material is not a subject some domains have and others do not.

## Three longitudinal waves, and only one of them is in your table

A solid carries a longitudinal wave differently depending on the shape it
travels in, and the three speeds are not interchangeable.

A **beam** is free to contract sideways as it is compressed, so the lateral
strains cost nothing and Poisson's ratio does not appear at all:
$c_{\mathrm{L,b}} = \sqrt{E/\rho}$.

A **plate** is held across its width. The material cannot get out of the way,
which stiffens it by $1/(1-\nu^2)$:
$c_{\mathrm{L,p}} = \sqrt{E/(\rho(1-\nu^2))}$. This is the one the
building-acoustics tables print, and the one a critical frequency is computed
from.

An **unbounded solid** holds the material on every side at once:
$c'_{\mathrm{L}} = \sqrt{E(1-\nu)/(\rho(1+\nu)(1-2\nu))}$. This is the fastest
of the three and the one a time-domain elastic solver integrates.

For the steel of Hopkins Table A2, with $\rho = 7800$ kg/m³, $\nu = 0{,}28$ and
a plate speed of 5 270 m/s, the three are 5 059, 5 270 and 5 720 m/s. Reading
one into another is a four to thirteen per cent error in whatever it feeds, and it
is an easy mistake to make, because a table that prints one of them often calls
it $c_\mathrm{L}$ with no qualifier at all.

## The inverses are the point

A catalogue of materials is built out of whatever its sources happened to
print. Hopkins Table A2 gives a plate speed, a density and a Poisson ratio, and
no Young's modulus anywhere. Cremer and Mechel give the modulus and no speed.
Neither table can be checked against the other until one of them is converted,
and that is what the six functions here are for: three speeds, three inverses,
and a seventh for the column two of those books share.

**No shear or bending waves.** The longitudinal family is what a materials
table prints and what the conversions need. The bending wave that actually
radiates from a wall is computed where it is used, in
`phonometry.vibration.structural` and `phonometry.building.prediction`, from
the bending stiffness of the plate rather than from a wave speed.

**No anisotropy.** Every relation here is for a homogeneous isotropic solid
with one modulus and one Poisson ratio. An orthotropic panel has two of each
and two critical frequencies, and that is `orthotropic_critical_frequencies`
in `phonometry.building`.

**No temperature or ageing.** The constants are the ones a source printed for
one specimen at one moment. Concrete stiffens for years and a polymer softens
with the room; neither is modelled here, and a table that holds a range says
so in its own entry.

## What is here

- [Wave speeds](wave-speeds.md): the three longitudinal
  speeds and their inverses, which one a printed table holds, and the
  thickness-critical-frequency product that lets two books be checked against
  each other for free.
