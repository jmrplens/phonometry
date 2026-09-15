---
title: "room.workroom_prediction"
description: "Predicting sound propagation in a workroom (ISO 11690-3:1998)."
sidebar:
  label: "workroom_prediction"
---

Predicting sound propagation in a workroom (ISO 11690-3:1998).

Part 1 of ISO 11690 says what a low-noise workplace is and part 2 says what to
do about it. Part 3 is the part that answers "what will it be like before we
build it", and it is unusual among the standards this library implements: it
prints almost no arithmetic. What it prints instead is a way of choosing, and
the choice is between two families of method and four levels of detail of the
data they are fed.

**The two families.** A *diffuse field* method sums a direct field and a
reverberant field that is assumed to be the same everywhere, which is cheap,
needs almost no data, and overestimates the level in a room whose field is not
diffuse. A *geometrical* method traces the sound along straight lines, which
costs a model of the room and pays for it in accuracy. Table 4 splits the
second family into three by how finely the room has to be described, and
Table E.1 says which level of detail of Tables 1 to 3 each category needs.

**What it does compute.** Annex C answers one practical question with one
graph: by how much does the level at a machine's own workstation rise when the
machine is put in a room rather than measured in the open? The answer is the
environmental correction of ISO 3744,

$$
\Delta L_A = 10 \lg\left(1 + \frac{4S}{A}\right) \ \text{dB}, \qquad S = S_0 \, 10^{(L_{WA} - L_{pA})/10}
$$

because the difference between the two printed emission quantities is the
measurement surface itself, and the level in the room is the emission level
plus that correction. Figure C.1 is that expression drawn as a flow chart, and
Table C.2 works it for eight machines in a room of 195 m2.

Annex B then adds the contributions of several machines at one workstation on
an energy basis, which is what turns a curve into a decision about which
machine to buy.

**The eighth machine of Table C.2.** Figure C.1 stops at 10 dB, and M8 of the
worked example needs more than that: its 29 dB between the two emission values
gives 12,4 dB in a room of 195 m2, so the row that reports 10 dB is reporting
the top edge of the diagram rather than a reading. The closed form has no such
ceiling, and the errata registry records the row.

Read from BS EN ISO 11690-3:1999, which endorses EN ISO 11690-3:1998 without
modification. The document is dated 1998 in its own header and 1999 on the
British cover.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## detail_is_sufficient

```python
detail_is_sufficient(
    category: str,
    *,
    room_detail: int,
    fitting_detail: int,
    source_detail: int,
) -> DetailVerdict
```

Does the data in hand match what Table E.1 asks of this category?

The table reads in both directions and both are useful: a reader with a
room description of level 1 and fittings of level 1 is limited to the
diffuse-field method, and a reader who wants ray tracing over an actual
room shape has to go and gather a level-4 description of it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `category` | `"1"`, `"2a"`, `"2b"` or `"2c"`. |
| `room_detail` | The level of Table 1 the room is described at. |
| `fitting_detail` | The level of Table 2 the fittings are described at. |
| `source_detail` | The level of Table 3 the sources are described at. |

**Returns:** The verdict, as a [`DetailVerdict`](/phonometry/reference/api/rooms/workroom-prediction/#detailverdict).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an unknown category or a level no table prints. |

## DetailVerdict

```python
DetailVerdict(
    category: str,
    satisfied: bool,
    room_ok: bool,
    fittings_ok: bool,
    sources_ok: bool,
)
```

Whether the data in hand is what a category of method asks for.

**Parameters**

| Name | Description |
| :--- | :--- |
| `category` | The category asked about. |
| `satisfied` | Whether all three levels fall inside Table E.1. |
| `room_ok` | Whether the room description does. |
| `fittings_ok` | Whether the fitting description does. |
| `sources_ok` | Whether the source description does. |

## fitting_density

```python
fitting_density(surface_area_m2: float, volume_m3: float) -> float
```

The density of the fittings, NOTE 3 of 6.2.2.

$$
q = \frac{S}{4V} \ \text{m}^{-1}
$$

with $S$ the total surface area of the fittings and $V$ the
volume of the room or of the zone they stand in. It is the quantity a
geometrical method of category 2a or 2b takes instead of the fittings
themselves.

**Parameters**

| Name | Description |
| :--- | :--- |
| `surface_area_m2` | $S$, in square metres. |
| `volume_m3` | $V$, in cubic metres. |

**Returns:** $q$, in reciprocal metres.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive area or volume. |

## FITTING_DETAIL_LEVELS

*Constant* (`dict`).

```python
FITTING_DETAIL_LEVELS = {1: 'fittings are not taken into account', 2: 'one mean density and one mean absorption for the whole room', 3: 'one mean density and one mean absorption per part of the room', 4: 'the actual shape and location, with shielding and reflection'}
```

## prediction_method

```python
prediction_method(category: str) -> PredictionMethod
```

One category of Table 4, with the detail levels of Table E.1.

**Parameters**

| Name | Description |
| :--- | :--- |
| `category` | `"1"`, `"2a"`, `"2b"` or `"2c"`. |

**Returns:** The row, as a [`PredictionMethod`](/phonometry/reference/api/rooms/workroom-prediction/#predictionmethod).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a category Table 4 does not print. |

## PREDICTION_METHODS

*Constant* (`dict`).

```python
PREDICTION_METHODS = {'1': PredictionMethod(category='1', family='diffuse field', rooms='rooms whose field may be treated as diffuse', room_detail=(1,), fitting_detail=(1,), source_detail=(1, 2, 3)), '2a': PredictionMethod(category='2a', family='geometrical', rooms='rooms that can be approximated by one mean absorption coefficient for each wall and one mean density for the fittings', room_detail=(1, 2), fitting_detail=(1, 2), source_detail=(1, 2, 3)), '2b': PredictionMethod(category='2b', family='geometrical', rooms='rooms that can be approximated by one mean absorption coefficient for each room surface and one mean density for the fittings in each zone', room_detail=(1, 2, 3), fitting_detail=(1, 2, 3), source_detail=(1, 2, 3)), '2c': PredictionMethod(category='2c', family='geometrical', rooms='rooms for which the individual distribution of absorption and fittings has to be considered', room_detail=(1, 2, 3, 4), fitting_detail=(1, 2, 3, 4), source_detail=(1, 2, 3))}
```

## PredictionMethod

```python
PredictionMethod(
    category: str,
    family: str,
    rooms: str,
    room_detail: tuple[int, ...],
    fitting_detail: tuple[int, ...],
    source_detail: tuple[int, ...],
)
```

One row of Table 4, with what Table E.1 asks it to be fed.

**Parameters**

| Name | Description |
| :--- | :--- |
| `category` | `"1"`, `"2a"`, `"2b"` or `"2c"`. |
| `family` | `"diffuse field"` or `"geometrical"`. |
| `rooms` | The rooms the category is for, in the words of Table 4. |
| `room_detail` | The levels of Table 1 it may be fed. |
| `fitting_detail` | The levels of Table 2 it may be fed. |
| `source_detail` | The levels of Table 3 it may be fed. |

## RECOMMENDED_DETAIL

*Constant* (`dict`).

```python
RECOMMENDED_DETAIL = {'1': ((1,), (1,), (1, 2, 3)), '2a': ((1, 2), (1, 2), (1, 2, 3)), '2b': ((1, 2, 3), (1, 2, 3), (1, 2, 3)), '2c': ((1, 2, 3, 4), (1, 2, 3, 4), (1, 2, 3))}
```

## ROOM_DETAIL_LEVELS

*Constant* (`dict`).

```python
ROOM_DETAIL_LEVELS = {1: 'the volume and the mean absorption coefficient of the surfaces', 2: 'a box-like shape, one absorption coefficient per surface', 3: 'a box-like shape, surfaces subdivided by absorption coefficient', 4: 'the actual shape, with absorption and reflection distributed over it'}
```

## SOURCE_DETAIL_LEVELS

*Constant* (`dict`).

```python
SOURCE_DETAIL_LEVELS = {1: 'omnidirectional point sources', 2: 'point sources with a directivity pattern', 3: 'complex sources'}
```

## total_workstation_level

```python
total_workstation_level(
    contributions_db: ArrayLike,
    *,
    existing_level_db: float | None = None,
) -> float
```

What a workstation hears once the new machines are installed, Annex B.

The contributions are added on an energy basis, with whatever was already
there added the same way. Annex B reads each contribution off the spatial
sound distribution curve of the room at the distance between the machine
and the workstation, except at a machine's own workstation, where
[`workstation_level`](/phonometry/reference/api/rooms/workroom-prediction/#workstation_level) gives it from the declared emission values.

**Parameters**

| Name | Description |
| :--- | :--- |
| `contributions_db` | The level each new machine alone would give at this workstation, in decibels. |
| `existing_level_db` | The level already there, in decibels, which for a workstation with no machine is the background noise. |

**Returns:** The total, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For levels that are not finite. |

## typical_decay_range

```python
typical_decay_range(region: str) -> _Range
```

What 4.3 says `DL2` usually is in one region, in decibels.

**Parameters**

| Name | Description |
| :--- | :--- |
| `region` | `"near"`, `"middle"` or `"far"`. |

**Returns:** The lower bound and the upper one, which is `None` in the far region because the clause prints none.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a region 4.3 does not name. |

## TYPICAL_DECAY_RANGE_DB

*Constant* (`dict`).

```python
TYPICAL_DECAY_RANGE_DB = {'near': (5.0, 6.0), 'middle': (2.0, 5.0), 'far': (6.0, None)}
```

## typical_excess_range

```python
typical_excess_range(region: str) -> _Range
```

What 4.3 says `DLf` usually is in one region, in decibels.

The clause prints a range for the middle region alone, and adds that in
the far region `DLf` may be negative; the near region it leaves open.

**Parameters**

| Name | Description |
| :--- | :--- |
| `region` | `"near"`, `"middle"` or `"far"`. |

**Returns:** The lower bound and the upper one, either of which may be `None`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a region 4.3 does not name. |

## TYPICAL_EXCESS_RANGE_DB

*Constant* (`dict`).

```python
TYPICAL_EXCESS_RANGE_DB = {'near': (None, None), 'middle': (2.0, 10.0), 'far': (None, None)}
```

## workstation_level

```python
workstation_level(
    *,
    sound_power_level_db: float,
    emission_level_db: float,
    absorption_area_m2: float,
) -> float
```

The level at the machine's own workstation in the room, Annex C.

$L'_{pA} = L_{pA} + \Delta L_A$, the emission value the machine was
declared with plus what the room adds to it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `sound_power_level_db` | $L_{WA}$ of the machine, in decibels. |
| `emission_level_db` | $L_{pA}$ at its workstation, in decibels. |
| `absorption_area_m2` | $A$ of the room, in square metres. |

**Returns:** $L'_{pA}$, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | As [`workstation_level_increase`](/phonometry/reference/api/rooms/workroom-prediction/#workstation_level_increase). |

## workstation_level_increase

```python
workstation_level_increase(
    *,
    sound_power_level_db: float,
    emission_level_db: float,
    absorption_area_m2: float,
) -> float
```

How much the room adds at the machine's own workstation, Annex C.

$$
\Delta L_A = 10 \lg\left(1 + \frac{4S}{A}\right) \ \text{dB}, \qquad \frac{S}{S_0} = 10^{(L_{WA} - L_{pA})/10}
$$

The two emission quantities a machine is declared with differ by the
measurement surface: the sound power level is the emission sound pressure
level plus $10 \lg(S/S_0)$. Put the machine in a room and the
reverberant field adds the environmental correction of ISO 3744 on top,
which is what Figure C.1 draws against the equivalent absorption area with
$L_{WA} - L_{pA}$ as the parameter.

**Parameters**

| Name | Description |
| :--- | :--- |
| `sound_power_level_db` | $L_{WA}$ of the machine, in decibels. |
| `emission_level_db` | $L_{pA}$ at its workstation, in decibels. |
| `absorption_area_m2` | $A$ of the room, in square metres. |

**Returns:** $\Delta L_A$, in decibels.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-finite level, a non-positive absorption area, or an emission level above the sound power level, which would put the workstation inside a measurement surface smaller than a square metre. |
