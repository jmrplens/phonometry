← [Documentation index](../../README.md)

# Suspended ceilings: the EN 16487 test code

EN ISO 354 measures the sound absorption of a specimen in a reverberation room
and leaves a good deal to the laboratory: how large the specimen is, how it is
mounted, how much air is behind it. For most materials those choices move the
answer by less than the measurement uncertainty. For a suspended ceiling they do
not: a tile absorbs partly by itself and partly through the plenum behind it, so
a laboratory that hangs it 400 mm below the ceiling has measured a different
product from one that hangs it at 150 mm. EN 16487 is a test code; it adds no
measurement of its own and fixes the arrangement so the one EN ISO 354 describes
gives the same answer everywhere.

## The specimen is a fixed size, and the mounting is the product

4.1.1.1.1 asks for a specimen as close to 10,80 m2 as the product allows, built
from test objects of 0,6 m by 0,6 m butted together with no seal in the joints,
the exposed face level with the top of the mounting fixture and the edges at
10 degrees or more to the nearest room wall. For the type E mounting a ceiling
actually uses, 4.1.1.2.3.1 fixes the overall depth of construction at 200 mm and
says that this is the depth the data for CE marking is compiled at.

```python
from phonometry import materials

check = materials.check_ceiling_specimen(area_m2=10.8, mounting="E", depth_mm=200.0)
print(check.satisfied)            # True
print(check.ce_marking_depth)     # True
print(materials.mounting_type("E"))
# suspended from a hard surface with an air space behind it
```

The area is a target and not a tolerance, so the check reports the difference
and leaves the judgement to the laboratory. A type E depth other than 200 mm
passes too, with a warning that says only that the result is not the CE marking
data. What the verdict judges is every limit of clause 4 that a dimension of the
arrangement can be held to: a substructure no more than 30 mm wide and 50 mm
deep, support units no larger than 50 mm by 50 mm at centre distances of at
least 1,2 m, a mounting fixture of at least 20 kg/m2, a deflection of no more
than 5 mm and, when `relative_humidity_percent` gives one value per measurement,
the 50 % of 4.2.2 in every one of them. Leaving one makes `satisfied` false and
raises a `SuspendedCeilingWarning` that says which. The 0,6 m test object, the
10 degree edge angle and the substructure pitch of about 0,6 m are targets the
clause asks to be aimed at, published as constants to build to and not judged.

```python
dry = materials.check_ceiling_specimen(
    area_m2=10.8, mounting="E", depth_mm=200.0,
    support_width_mm=40.0, support_height_mm=40.0, support_centre_distance_m=1.2,
    relative_humidity_percent=[41.0, 44.0],
)
print(dry.supports_ok, dry.humidity_ok, dry.satisfied)   # True False False
```

## How the measurement goes

Build the specimen to 10,80 m2 out of whole test objects, butted together, with
the joints unsealed and the perimeter covered by the mounting fixture. Hang it at
200 mm overall depth if the result is to support CE marking, on a substructure
inside the 30 mm by 50 mm section carried by supports inside 50 mm by 50 mm and
at least 1,2 m apart, and check the deflection at the worst point.
Set the specimen edges at an angle to the room walls. Measure the empty room and
then the room with the specimen in it as EN ISO 354 prescribes, holding
temperature and humidity steady between the two runs and the humidity at 50 % or
more in each: the correction below is
the difference between them, and it is a difference of days rather than of
ceilings.

## The air in the room is part of the answer

The absorption coefficient comes from two reverberation times measured on two
occasions, so a change of temperature or humidity between them shows up as
absorption the specimen never had. 4.2.1 caps the whole effect: the correction
`4V(m_2 - m_1)/S` shall not exceed 0,05 at any frequency, and 4.2.2 asks for at
least 50 % relative humidity.

```python
correction = materials.air_absorption_correction(
    volume_m3=200.0,
    specimen_area_m2=10.8,
    attenuation_with=[0.0011, 0.0013, 0.0018, 0.0028, 0.0055, 0.0170],
    attenuation_empty=[0.0010, 0.0012, 0.0016, 0.0025, 0.0050, 0.0160],
)
print(correction.round(3))     # [0.007 0.007 0.015 0.022 0.037 0.074]
```

That last band is over the cap and the library says so rather than returning it
quietly: the answer is a second measurement of the empty room, which is what 6.3
asks for.

## What the whole thing buys

Table 1 is the point of the exercise: the reproducibility between European
laboratories from the round robin of Annex A.

```python
print(materials.reproducibility_uncertainty().round(2))
# [0.23 0.23 0.11 0.1  0.1  0.13]
print(materials.WEIGHTED_UNCERTAINTY)       # 0.08
print(materials.EN16487_COVERAGE_FACTOR)    # 2.8
```

Two things are worth reading twice. The figures are an expanded uncertainty, with
the note under the table multiplying the ISO 5725-6 reproducibility standard
deviation by 2,8 rather than by the usual 2. And 6.2 says plainly that they hold
for a plane absorber with the type E mounting at 200 mm and that nothing has been
investigated for any other absorber or mounting, which leaves a baffle, a raft or
a free-hanging unit outside them.

## What this page does not cover

The measurement itself, which is EN ISO 354; discrete absorbers, baffles and
rafts measured as objects rather than as a plane; and the product requirements of
EN 13964 beyond the definitions and the CE marking depth this code refers to.

## See also

- [Measuring sound absorption](absorption-measurement.md): the reverberation-room
  method this code constrains, with the Sabine coefficient and its rating.
- [Spatial sound decay in workrooms](../../buildings/rooms/workroom-sound-decay.md):
  what an absorbing ceiling is bought for, measured in the finished hall.
- [Room-noise criteria](../../buildings/rooms/room-noise.md): the target the
  absorption is chosen against.
- API reference: [`materials.absorbers.suspended_ceilings`](https://jmrplens.github.io/phonometry/reference/api/materials/suspended-ceilings/).
