---
title: "fluids.catalogue"
description: "Fluid states read from a printed page."
sidebar:
  label: "catalogue"
---

Fluid states read from a printed page.

A density and a speed of sound stand behind every level this library computes,
and most of them are computed: [`air`](/phonometry/reference/api/fluids/air/),
[`ideal_gas`](/phonometry/reference/api/fluids/gas/#ideal_gas) and [`sea_water`](/phonometry/reference/api/fluids/water/#sea_water)
take the conditions that were measured and return the state that follows. A
few are not. Some books print a table of fluids the way they print a table of
solids, a density and a speed of sound at a stated temperature, and those are
read rather than derived. This is where they live.

The distinction is carried in [`model`](/phonometry/reference/api/fluids/fluids/#fluid), which
every state already uses to say what produced it. A computed state names the
closed form, the annex or the fit; a state from here names the table, with its
PDF page and its printed folio, because the table is what produced it and a
reader checking the number needs the page rather than the name of an equation
that was never used. The citation lives once, in the data file beside the
rows, the same shape the solid and porous catalogues use.

Not every named air in this library is here
-------------------------------------------
Four more sit elsewhere in the tree, each beside the model or the standard
that fixes it, and they disagree: the absorber models propagate through
343 m/s at 1,205 kg/m3, the airflow-resistance annex through 345,87 at 1,186,
EN/ISO 12354 through 340 at 1,29, and the acoustic solver defaults to 343 at
1,2. None of them is wrong. Each is the air its own document assumes, and
substituting one for another would change a number that document prints, which
is why each stays with the clause that prints it rather than being gathered
here.

Gathering them would also invert the dependency this package exists at the
bottom of: `fluids` is part of the transverse toolbox precisely so that any
domain may import it, and a catalogue here that imported `materials`,
`building` and `simulation` to reach them would make the medium depend on
three of the domains that stand on it. The comparison a reader wants is a
documentation artefact, and it is built as one: the published-catalogues page
of the site lists all of them side by side, gathered by a script that is free
to see the whole tree.

What it is not
--------------
It is not a table of fluid properties to look values up in. Air at 23 degC and
50 per cent relative humidity is [`air`](/phonometry/reference/api/fluids/air/), which computes
it from the conditions that were measured; sea water is
[`sea_water`](/phonometry/reference/api/fluids/water/#sea_water). Use a row here to reproduce a book's own
number.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## PUBLISHED_FLUIDS

*Constant* (`mappingproxy`).

```python
PUBLISHED_FLUIDS = {'bies-2017-table-c1-fluids/air': Fluid(temperature_c=20.0, static_pressure_pa=101325.0, composition=mappingproxy({}), model='Air as printed in Bies 5e Table C.1, PDF page 746 (printed p. 717)', validity="Bies 5e says of Table C.1 that its values 'should be used with caution and should be considered as representative only'.", properties=mappingproxy({'speed_of_sound': 343.0, 'density': 1.206})), 'bies-2017-table-c1-fluids/fresh_water': Fluid(temperature_c=20.0, static_pressure_pa=101325.0, composition=mappingproxy({}), model='Fresh water as printed in Bies 5e Table C.1, PDF page 746 (printed p. 717)', validity="Bies 5e says of Table C.1 that its values 'should be used with caution and should be considered as representative only'.", properties=mappingproxy({'speed_of_sound': 1497.0, 'density': 998.0})), 'bies-2017-table-c1-fluids/sea_water': Fluid(temperature_c=13.0, static_pressure_pa=101325.0, composition=mappingproxy({}), model='Sea water as printed in Bies 5e Table C.1, PDF page 746 (printed p. 717)', validity="Bies 5e says of Table C.1 that its values 'should be used with caution and should be considered as representative only'.", properties=mappingproxy({'speed_of_sound': 1530.0, 'density': 1025.0}))}
```
