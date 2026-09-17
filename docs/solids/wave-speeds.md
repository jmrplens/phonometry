← [Documentation index](../README.md)

# Wave speeds of a solid

## The problem this solves

You have a table. It gives you a wave speed of 5 270 m/s for steel, a density
and a Poisson ratio, and no Young's modulus. Your function wants the modulus.
Another table gives you 200 GPa and no speed, and the function you are feeding
next wants the speed. A third gives you 12,3 m Hz and neither.

All three describe the same steel. Getting from one to another takes one line
of algebra, which is one line of algebra too many to be doing from memory,
because the answer depends on something the table often does not say: whether
its speed is the speed in a beam, in a plate, or in an unbounded solid.

## The three speeds

```python
from phonometry import solids

modulus, density, poisson = 2.0e11, 7800.0, 0.28

beam = solids.beam_longitudinal_speed(modulus, density_kg_m3=density)
plate = solids.plate_longitudinal_speed(
    modulus, density_kg_m3=density, poisson_ratio=poisson
)
bulk = solids.bulk_longitudinal_speed(
    modulus, density_kg_m3=density, poisson_ratio=poisson
)

print(f"{beam:.0f} {plate:.0f} {bulk:.0f}")  # 5064 5275 5725
```

The order is always the same, and it is the order of how much the material is
held: a beam can contract sideways freely, a plate is held across its width,
and an unbounded solid is held on every side.

$$
c_{\mathrm{L,b}} = \sqrt{\frac{E}{\rho}}
\qquad
c_{\mathrm{L,p}} = \sqrt{\frac{E}{\rho\,(1-\nu^2)}}
\qquad
c'_{\mathrm{L}} = \sqrt{\frac{E\,(1-\nu)}{\rho\,(1+\nu)(1-2\nu)}}
$$

The first two are Hopkins Eqs. (2.20) and (2.21), the third is Norton and
Karczub Eq. (1.225). At a Poisson ratio of zero the three collapse into one,
which is the quickest way to remember that the only thing between them is how
the lateral strain is paid for.

## Which one is in your table

Building acoustics prints the **plate** speed. EN 12354-1 Table B.3, Hopkins
Table A2 and Mechel Table 3 all tabulate it, and Hopkins says so in a footnote:
the values can be used as estimates for beams or plates, which is an admission
that the two differ and a statement that for these materials the difference is
inside the spread of the table.

A time-domain elastic solver integrates the **bulk** speed, because the
material it discretises is unbounded at the scale of a cell. Reading a plate
table into a solver is a documented trap: for the steel above the gap is eight
and a half per cent, and for aluminium fifteen.

A **beam** speed turns up where a bar was actually measured, which is where a
speed-of-sound table in a general acoustics text usually gets its solids.

## Going back to the modulus

Each speed has its inverse, and they are what let two books be compared:

```python
from phonometry import solids

# Hopkins Table A2, steel: a plate speed, a density and a Poisson ratio.
modulus = solids.youngs_modulus_from_plate_speed(
    5270.0, density_kg_m3=7800.0, poisson_ratio=0.28
)
print(f"{modulus / 1e9:.0f} GPa")  # 200 GPa
```

Two hundred gigapascals, which is what a structural steel has, and the number
Cremer and Mechel print in the column Hopkins leaves out.

## The column that checks the table

Hopkins, Long and Mechel each print the product of thickness and critical
frequency. It is a property of the material alone, because the thickness
cancels, and so it is the cheapest cross-check there is between books that
share no other column:

```python
from phonometry import solids

print(f"{solids.thickness_critical_frequency_product(5270.0):.2f}")  # 12.31
```

Hopkins Table A2 prints 12,3 m Hz for that steel and states in its heading that
the column assumes a speed of sound of 343 m/s.

$$
h f_\mathrm{c} = \frac{c_0^2 \sqrt{12}}{2 \pi\, c_{\mathrm{L,p}}}
$$

The constant matters. ISO 12354-1 writes the critical frequency with a rounded
1,8 in the denominator, which is 2π/√12 = 1,8138 to two figures. The rounded
form is the standard's own arithmetic and `phonometry.building.critical_frequency`
keeps it, because a measurement that claims to follow the standard has to. Here
the exact constant is the right one: it reproduces all twenty-five rows of
Table A2, and the rounded one misses the steel row by 0,8 per cent.

## The table, and what it does not say

`PUBLISHED_SOLIDS` is Hopkins Table A2, twenty-five materials with the page
they were read on, so a partition or a floor starts from a published number.

```python
from phonometry import solids

board = solids.PUBLISHED_SOLIDS["plasterboard_natural_gypsum"]
print(board.density_kg_m3, board.longitudinal_speed_m_s, board.loss_factor)
# 860.0 1490.0 0.0141
print(round(board.youngs_modulus_pa() / 1e9, 2))
# 1.74
```

The modulus is not in the table: it is the inverse above, run on the row's own
numbers.

A materials table is not a list of measurements, and this one says so. Most of
its Poisson ratios and loss factors carry a footnote whose whole text is
"Estimate", and only aluminium, glass, mortar and steel print a Poisson ratio
the book stands behind. The row keeps that in `estimated`, readable through
`is_estimate`.

Seven cells are not single values, and none of them is flattened: aircrete
and brick print a density **range** (400 to 800 and 1 500 to 2 000 kg/m³),
so `density_kg_m3` is `None`, the interval is in `ranges` and
`youngs_modulus_pa()` refuses rather than picking a midpoint; aluminium and
steel print a loss factor as an **upper bound** and glass prints one as a
**band**, so those three have `loss_factor` of `None` too; and two speeds
carry a spread beside the value, aircrete's 1 900 m/s typically 1 600 to
2 300, and OSB's 2 570 an effective figure for a material that runs 2 200 to
3 500 m/s with the direction.

Rows the book credits to another author keep the credit in `attributed_to`, and
the steel row keeps two of them: Fahy for the speed and Poisson ratio, Heckl
for the loss factor.

None of this is a specification. Block densities vary by manufacturer, which is
why the page prints ranges where it does.

## What the functions refuse

A Poisson ratio of 0,5 describes an incompressible material, and an
incompressible material has no pure longitudinal wave to have a speed, so
`bulk_longitudinal_speed` raises rather than dividing by zero. The plate form
is looser, since it only needs one minus the square of the ratio to stay
positive, but it refuses a ratio of 1 for the same reason. Both messages name
the ratio they were given and the term that would have vanished.
