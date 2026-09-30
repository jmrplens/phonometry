---
title: "emission.free_field_qualification"
description: "Qualification of an anechoic or hemi-anechoic room by the inverse square law: ISO 26101:2017, with the criteria of ISO 3745:2012 Annex A as Amendment 1:2017 rewrote it."
sidebar:
  label: "free_field_qualification"
---

Qualification of an anechoic or hemi-anechoic room by the inverse square
law: ISO 26101:2017, with the criteria of ISO 3745:2012 Annex A as
Amendment 1:2017 rewrote it.

A free field is judged by how the level falls away from a small source. Along
each straight microphone traverse the measured level $L_{pi}$ at the
distance $r_i$ from the mathematical origin of the traverse is compared
with the inverse square law

$$
L_p(r_i) = b - 20 \lg\frac{r_i}{r_0}\ \mathrm{dB}, \qquad r_0 = 1\ \mathrm{m} \tag{ISO 26101 Formula (2)}
$$

and the deviation at every point is

$$
\Delta L_{pi} = L_{pi} - L_p(r_i) \tag{ISO 26101 Formula (4)}
$$

where $L_{pi}$ has been corrected for the stability of the source with
the monitor microphone,
$L_{pi} = L'_{pi} - L_{p,\mathrm{ref},i} + L_{p,\mathrm{ref},0}$
(Formula (1)). The room is qualified out to the largest distance from the
origin at which every deviation, on every traverse and at every frequency,
stays inside the limits of Table A.1 (the same table in ISO 26101 Annex A and
in the amended ISO 3745 Annex A): $\pm 1{,}5$, $\pm 1{,}0$ and
$\pm 1{,}5$ dB in an anechoic room for the one-third octave bands up to
630 Hz, from 800 Hz to 5 000 Hz and from 6 300 Hz up, and $\pm 2{,}5$,
$\pm 2{,}0$ and $\pm 3{,}0$ dB in a hemi-anechoic one.

**The fit of b.** Formula (2) leaves the source strength $b$ free: it
"is adjusted to optimize the fit of the measured sound pressure levels into
the tolerance range, to maximize the qualified distance from the test sound
source". Note 1 offers the mean of $L_{pi} + 20 \lg(r_i/r_0)$ as a
starting value for an iterative search (Formula (3)); no source prints the
search. This module does not iterate, because the problem it poses has an
exact answer. Write $y_i = L_{pi} + 20 \lg(r_i/r_0)$, so that
$\Delta L_{pi} = y_i - b$. The points out to a distance $R$ fit
inside $\pm t$ for *some* $b$ exactly when the spread of their
$y_i$ is at most $2t$, and the spread over the points nearer than
$R$ can only grow with $R$. So, for one traverse and one
frequency, the qualified distance is the distance of the last point of the
longest run from the origin whose $y$ spread stays within $2t$,
and every $b$ in $[\max y - t,\ \min y + t]$ over that run
qualifies it. Of those the module takes the midpoint,
$b = (\max y + \min y)/2$, the one that leaves the same margin to both
limits and so the smallest largest deviation. A qualified distance cannot be
extended by any other $b$, and no search can find a longer one.

**The mathematical origin.** ISO 26101:2017 5.1.3.2 and the amended ISO 3745
A.3.3 require every traverse to share one mathematical origin, and that origin
to lie within the physical volume the test source occupies; the 2012 annex
had instead fitted a collinear acoustic-centre offset per traverse. Given a
fixed origin, the distances follow from the measured positions. Given the box
the source occupies, the origin is searched inside it for the largest radius
of A.2.4, the smallest qualified distance over every traverse and every
frequency, since that is the distance Formula (2) asks $b$ to maximize
and A.2.4 defines from the origin. A qualified distance ends either where a
deviation leaves Table A.1, which the room decides, or at the last point
measured, which the measurement decides; moving the origin inside the box
moves the distance to that last point by as much as the origin moves, which
says nothing about the room. So the search ranks origins by that smallest
distance with every run that reaches its last point counted at the distance
of that point from the centre of the box, the same for every origin: radii
then differ only where the room ends a run, and radii within the 1 mm to
which the search resolves the origin count as equal. Ties are broken by how
much of the Table A.1 band the curves fill on average (the mean over every
traverse and frequency of the half spread of $y_i$ as a share of its
limit), then by the nearer point to the centre of the box; the mean, rather
than the worst band, keeps one band from dragging the origin to the edge of
the source at the others' expense when nothing else separates two origins.
In an exact inverse-square field every run reaches its last point, the
curves are flattest seen from the point the field diverges from, and the
search returns that point. The radius reported is always the distance from
the origin returned. The search is a regular lattice of five points per axis
followed by a compass search that halves its step down to 1 mm; it is
deterministic, stays inside the box by construction and never returns a
worse origin than the best lattice point.

**What the verdict judges.** [`check_free_field`](/phonometry/reference/api/power/free-field-qualification/#check_free_field) holds the qualification
to the amended ISO 3745 Annex A and to the clauses of ISO 26101 it defers to:
the deviations of A.2.2 and the radius of A.2.4; the frequencies of A.2.3
(100 Hz to 10 000 Hz, one-third octave bands below 125 Hz and above 4 000 Hz
and octave mid-band frequencies between); five to eight traverses (A.3.3),
towards the five targets a) to e) of A.3.3 and in the working area, within
the angular limits of the source directionality in a hemi-anechoic room; at
least 10 points on each traverse and 50 in total within the radius, equally
spaced at each frequency, and spaced at most a tenth of a wavelength below
250 Hz and 100 mm above (A.4.3); the spatial resolution of ISO 26101 A.4.3
and the traverse length of ISO 26101 5.1.4.3, which A.2.4 cites; the 6 dB
above background of ISO 26101 5.1.2.2 c); the directionality of the test
source (ISO 26101 Annex B, [`verify_source_directionality`](/phonometry/reference/api/power/free-field-qualification/#verify_source_directionality)); and, in a
hemi-anechoic room, the reflecting plane of A.2.5. A requirement whose data
were not given is listed in [`FreeFieldCheck.not_judged`](/phonometry/reference/api/power/free-field-qualification/#freefieldcheck), and the
verdict does not pass until it is judged.

Two readings are this module's, since no source settles them. The spacing
rules of A.4.3 name a frequency below which a tenth of a wavelength applies
and above which a fixed length does (250 Hz and 100 mm in the amended
ISO 3745, 1 kHz and 25 mm in ISO 26101), and neither says which holds at the
edge itself; the one-third octave band that contains the edge frequency is
held to the stricter of the two. And "equally spaced" comes with no
tolerance: the points within the radius are equally spaced when, walking out
from the first, every next point of the grid lies within a tenth of the
median gap of where one step would put it. Points between two of them are
the additional measurements the last paragraph of A.4.3 recommends near a
peak deviation, and do not break the grid.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## check_free_field

```python
check_free_field(
    results: InverseSquareLawResult | Sequence[InverseSquareLawResult],
    *,
    bandwidth: QualificationBandwidth,
    source_directionality: SourceDirectionalityResult | Sequence[SourceDirectionalityResult | None] | None = None,
    measurement_radius_m: float | None = None,
    reflecting_plane_absorption_coefficient: float | None = None,
    reflecting_plane_margin_m: float | None = None,
    paths_in_working_area: bool | None = None,
    speed_of_sound: float = 343.0,
) -> FreeFieldCheck
```

Is this room anechoic or hemi-anechoic enough for ISO 3745? (Annex A as amended).

Judges the inverse-square-law analysis of one or more test sources
([`inverse_square_law_deviations`](/phonometry/reference/api/power/free-field-qualification/#inverse_square_law_deviations)) against the amended ISO 3745:2012
Annex A and the ISO 26101:2017 clauses it defers to (see the module
notes). The radius of A.2.4 is the smallest qualified distance over every
traverse and every evaluated frequency; the per-band requirements are
judged within it. When the full range fails, the widest contiguous range
that meets every requirement is reported as the reduced range A.2.3
allows, "in conformity" but not "in full conformity".

**Parameters**

| Name | Description |
| :--- | :--- |
| `results` | One [`InverseSquareLawResult`](/phonometry/reference/api/power/free-field-qualification/#inversesquarelawresult) per test source, their frequencies disjoint, all for the same room. |
| `bandwidth` | `"discrete-frequency"` (the default of A.4.1, tones or a narrow-band analysis) or `"broadband"` (noise in one-third octave bands, sufficient only for sources that radiate broadband noise). |
| `source_directionality` | The [`verify_source_directionality`](/phonometry/reference/api/power/free-field-qualification/#verify_source_directionality) result of each test source (one, or a sequence aligned with `results`); `None` leaves ISO 26101 Annex B unjudged. |
| `measurement_radius_m` | The radius of the measurement surface to be used, in metres; the room must be qualified at least that far. |
| `reflecting_plane_absorption_coefficient` | The largest sound absorption coefficient of the reflecting plane over the frequency range (A.2.5), hemi-anechoic only. |
| `reflecting_plane_margin_m` | How far the reflecting plane extends beyond the projection of the measurement surface, in metres (A.2.5), hemi-anechoic only. |
| `paths_in_working_area` | Whether the traverse paths lie in the working area of the room, the part normally used for measurements (A.3.3); a declaration, since the positions cannot tell. `None` leaves it unjudged. The targets of A.3.3 a) to e) are read from [`MicrophoneTraverse.targets`](/phonometry/reference/api/power/free-field-qualification/#microphonetraverse). |
| `speed_of_sound` | Speed of sound, in m/s, for the wavelengths of A.4.3, ISO 26101 5.1.4.3 and A.2.5 (default 343). |

**Returns:** [`FreeFieldCheck`](/phonometry/reference/api/power/free-field-qualification/#freefieldcheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for results of different rooms, a frequency given to two sources, directionality results that do not align with `results`, an unknown bandwidth, an absorption coefficient outside 0 to 1, a margin that is not finite, or a working-area declaration that is not `True`, `False` or `None`. |

## directionality_positions

```python
directionality_positions(
    room: FreeFieldRoom,
    *,
    radius_m: float = 1.5,
) -> np.ndarray
```

Microphone positions of the directionality test (ISO 26101 B.3.2).

The angle of elevation $\varphi$ is counted from the vertical above
the source (90 deg is the reflecting plane), the azimuth $\Theta$
from the `x` axis. The rows run $\varphi$ = 80, 60, 40 and 20 deg
(then 100, 120, 140 and 160 deg in an anechoic room), and within each
$\Theta$ = 0 to 315 deg in steps of 45 deg: 32 positions in a
hemi-anechoic room, 64 in an anechoic one (Figure B.1).

**Parameters**

| Name | Description |
| :--- | :--- |
| `room` | `"anechoic"` or `"hemi-anechoic"`. |
| `radius_m` | The radius, in metres; 1,5 m in B.3.2. |

**Returns:** `(32, 3)` or `(64, 3)` coordinates, in metres.

## directionality_tolerance_db

```python
directionality_tolerance_db(
    frequencies_hz: ArrayLike,
    *,
    room: FreeFieldRoom,
) -> np.ndarray
```

Allowable deviation of the test source directionality (ISO 26101 Table B.1).

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | One-third octave mid-band frequencies, in hertz. |
| `room` | `"anechoic"` or `"hemi-anechoic"`. |

**Returns:** The half-width of the tolerance band, in dB, per frequency.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an unknown room, a non-positive frequency or frequencies that are not one value or a 1-D array. |

## FreeFieldCheck

```python
FreeFieldCheck(
    room: str,
    bandwidth: str,
    results: tuple[InverseSquareLawResult, ...],
    frequencies_hz: np.ndarray,
    band_radius_m: np.ndarray,
    maximum_qualified_radius_m: float,
    measurement_radius_m: float | None,
    points_met: np.ndarray,
    equal_spacing_met: np.ndarray,
    spacing_met: np.ndarray,
    iso26101_spacing_met: np.ndarray,
    length_met: np.ndarray,
    background_met: np.ndarray | None,
    directionality_met: np.ndarray | None,
    traverse_count_met: bool,
    path_targets_met: bool | None,
    working_area_met: bool | None,
    path_angles_met: bool | None,
    reflecting_plane_met: bool | None,
    full_frequency_range: bool,
    conforming_range_hz: tuple[float, float] | None,
    conforming_radius_m: float,
    not_judged: tuple[str, ...],
)
```

Whether a room qualifies as anechoic or hemi-anechoic for ISO 3745.

The verdict of the amended ISO 3745:2012 Annex A over the frequencies
evaluated, with the ISO 26101:2017 clauses it defers to. Every per-band
array is aligned with `frequencies_hz` (ascending) and judged within
`maximum_qualified_radius_m`.

**Attributes**

| Name | Description |
| :--- | :--- |
| `room` | `"anechoic"` or `"hemi-anechoic"`. |
| `bandwidth` | `"discrete-frequency"` or `"broadband"` (A.4.1): a room qualified with broadband noise is qualified only for sources that radiate broadband noise. |
| `results` | The inverse-square-law analysis of each test source. |
| `frequencies_hz` | Every evaluated frequency, ascending, in hertz. |
| `band_radius_m` | The distance to which each frequency is qualified on every traverse, in metres. |
| `maximum_qualified_radius_m` | The A.2.4 radius over every evaluated frequency, in metres. |
| `measurement_radius_m` | The measurement radius to be used, if given. |
| `points_met` | At least 10 points on each traverse and 50 in total within the radius (A.4.3), per band. |
| `equal_spacing_met` | The points of every traverse within the radius equally spaced at the frequency (A.4.3, ISO 26101 5.1.4.3), points added between two of them near a peak deviation allowed (see the module notes for the tolerance), per band. |
| `spacing_met` | Spacing at most a tenth of a wavelength below 250 Hz and 100 mm above (amended ISO 3745 A.4.3), per band; the band that contains 250 Hz is held to the stricter of the two. |
| `iso26101_spacing_met` | Spacing at most a tenth of a wavelength below 1 kHz and 25 mm above (ISO 26101 A.4.3, cited by A.2.4), per band; the band that contains 1 kHz is held to the stricter of the two. |
| `length_met` | Traverse starting at most, and running at least, a quarter wavelength at the lowest frequency (ISO 26101 5.1.4.3), per band. |
| `background_met` | Levels at least 6 dB above the background at every point (ISO 26101 5.1.2.2 c)), per band, or `None` when a traverse came without background. |
| `directionality_met` | The test source within Table B.1 in the band, or `None` without a directionality result for its source. |
| `traverse_count_met` | Five to eight traverses for every source (A.3.3). |
| `path_targets_met` | Every source has traverses towards each of the five targets of A.3.3 a) to e), or `None` when a source names no target on any traverse. |
| `working_area_met` | The traverse paths lie in the working area of the room, the part normally used for measurements (A.3.3), as declared, or `None` when not declared. |
| `path_angles_met` | In a hemi-anechoic room, the direction of every traverse within the 20 deg to 80 deg from the vertical of the directionality test (A.3.3); `None` in an anechoic room, where A.3.3 sets no such limit. |
| `reflecting_plane_met` | A.2.5 in a hemi-anechoic room, `None` when not judged or in an anechoic room. |
| `full_frequency_range` | Whether every frequency A.2.3 requires from 100 Hz to 10 000 Hz was evaluated. |
| `conforming_range_hz` | The widest contiguous range (in the A.2.3 sense) over which every judged requirement is met, `(low, high)` in hertz, or `None`; with `not_judged` empty it is the reduced range A.2.3 lets a report state "in conformity". |
| `conforming_radius_m` | The radius qualified over that range, in metres, or `nan`. |
| `not_judged` | The requirements without data, by name. |

### FreeFieldCheck.band_met

*property*

Per band, whether every judged per-band requirement is met.

**Returns:** One boolean per evaluated frequency.

### FreeFieldCheck.discrete_frequency

*property*

Whether the qualification holds for tonal sources too (A.4.1).

**Returns:** `True` for a discrete-frequency qualification.

### FreeFieldCheck.passes

*property*

Whether the room is qualified in full conformity with ISO 3745.

Every requirement judged and met at every evaluated frequency, the
whole of 100 Hz to 10 000 Hz evaluated (A.2.3), and the measurement
radius, if given, within the qualified one.

**Returns:** `True` for a room in full conformity.

### FreeFieldCheck.plot()

```python
FreeFieldCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the qualified distance per frequency against the radius judged.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the radius bars. |

**Returns:** The axes.

## inverse_square_law_deviations

```python
inverse_square_law_deviations(
    traverses: Sequence[MicrophoneTraverse],
    *,
    frequencies_hz: ArrayLike,
    room: FreeFieldRoom,
    origin_m: ArrayLike | None = None,
    source_box_m: ArrayLike | None = None,
) -> InverseSquareLawResult
```

Deviations from the inverse square law along the traverses of one source.

Applies Formula (1) with the monitor microphone, then Formulae (2) and (4)
with the source strength $b$ that maximizes the qualified distance
under the Table A.1 limits of `room` (see the module notes: the midpoint
of the admissible interval, an exact rather than an iterative answer), and
reports the starting value of Formula (3) beside it.

One call covers one test source: ISO 26101 5.1.2.2 allows two or more to
span the frequency range, each with its own mathematical origin, and
[`check_free_field`](/phonometry/reference/api/power/free-field-qualification/#check_free_field) takes one result per source.

**Parameters**

| Name | Description |
| :--- | :--- |
| `traverses` | The straight traverses, all measured at `frequencies_hz`. |
| `frequencies_hz` | The test frequencies (tones or one-third octave mid-bands), in hertz, one per level column. |
| `room` | `"anechoic"` or `"hemi-anechoic"`, which selects the Table A.1 limits. |
| `origin_m` | The mathematical origin of every traverse, `(x, y, z)` in metres; `None` with no `source_box_m` takes the room frame's origin. |
| `source_box_m` | The box the test source physically occupies, as `((x_min, y_min, z_min), (x_max, y_max, z_max))` in metres; the origin is then searched inside it (ISO 26101 5.1.3.2, ISO 3745 A.3.3). A zero extent on an axis holds the origin on that coordinate. |

**Returns:** [`InverseSquareLawResult`](/phonometry/reference/api/power/free-field-qualification/#inversesquarelawresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if both `origin_m` and `source_box_m` are given, a traverse's level columns do not match the frequencies, a traverse has no level at a frequency, or a point coincides with the origin. |

## inverse_square_law_tolerance_db

```python
inverse_square_law_tolerance_db(
    frequencies_hz: ArrayLike,
    *,
    room: FreeFieldRoom,
) -> np.ndarray
```

Allowable deviation from the inverse square law per band (Table A.1).

ISO 26101:2017 Annex A and ISO 3745:2012/Amd.1:2017 A.2.2 print the same
table. A frequency is read in the one-third octave band that contains it,
so a tone at 794 Hz is held to the 800 Hz row.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | Test frequencies or band mid-frequencies, in hertz. |
| `room` | `"anechoic"` or `"hemi-anechoic"`. |

**Returns:** The half-width of the tolerance band, in dB, per frequency.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an unknown room, a non-positive frequency or frequencies that are not one value or a 1-D array. |

## InverseSquareLawResult

```python
InverseSquareLawResult(
    frequencies_hz: np.ndarray,
    room: str,
    origin_m: np.ndarray,
    origin_fitted: bool,
    source_box_m: np.ndarray | None,
    traverse_names: tuple[str, ...],
    traverse_targets: tuple[tuple[str, ...], ...],
    positions_m: tuple[np.ndarray, ...],
    distances_m: tuple[np.ndarray, ...],
    levels_db: tuple[np.ndarray, ...],
    background_margin_db: tuple[np.ndarray | None, ...],
    source_stability_db: tuple[np.ndarray, ...],
    source_strength_db: np.ndarray,
    initial_source_strength_db: np.ndarray,
    deviations_db: tuple[np.ndarray, ...],
    traverse_radius_m: np.ndarray,
    band_radius_m: np.ndarray,
    tolerance_db: np.ndarray,
)
```

Deviations from the inverse square law of one test source (ISO 26101 5.1.5).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The test frequencies, in hertz, as given. |
| `room` | `"anechoic"` or `"hemi-anechoic"`. |
| `origin_m` | The mathematical origin of the traverses, `(x, y, z)` in metres. |
| `origin_fitted` | `True` when the origin was searched inside `source_box_m`. |
| `source_box_m` | The box the test source occupies, `(2, 3)` rows of lower and upper corner, or `None` for a fixed origin. |
| `traverse_names` | The label of each traverse as given, `""` when none was. |
| `traverse_targets` | What each traverse was selected towards (A.3.3 a) to e)), as given. |
| `positions_m` | The measurement points of each traverse, `(N, 3)`. |
| `distances_m` | The distance $r_i$ of each point from the origin, in metres. |
| `levels_db` | $L_{pi}$ of each traverse after the stability correction of Formula (1), `(N, NF)`, `nan` where not measured. |
| `background_margin_db` | $L'_{pi}$ less the background at each point, `(N, NF)`, or `None` for a traverse without background. |
| `source_stability_db` | The largest excursion of the monitor microphone from its reading at point 0, per frequency, or `nan` without a monitor. |
| `source_strength_db` | $b$ of Formula (2) per traverse and frequency, `(NT, NF)`: the midpoint of the admissible interval over the points within `band_radius_m` (over the traverse's own qualified run when its first point lies beyond that radius). |
| `initial_source_strength_db` | The starting value of Formula (3), the mean of $L_{pi} + 20 \lg(r_i/r_0)$ over every point, `(NT, NF)`. |
| `deviations_db` | $\Delta L_{pi}$ of Formula (4) at every point, `(N, NF)` per traverse. |
| `traverse_radius_m` | The qualified distance of each traverse at each frequency, `(NT, NF)`, in metres. |
| `band_radius_m` | The distance to which each frequency is qualified on every traverse at once, `(NF,)`, in metres. |
| `tolerance_db` | The Table A.1 limit of each frequency, in dB. |

### InverseSquareLawResult.largest_deviation_db

*property*

The largest $|\Delta L_{pi}|$ within each band's radius.

**Returns:** One value per frequency, in dB.

### InverseSquareLawResult.maximum_qualified_radius_m

*property*

The largest radius every traverse meets at every frequency (A.2.4).

**Returns:** The smallest of `band_radius_m`, in metres.

### InverseSquareLawResult.plot()

```python
InverseSquareLawResult.plot(
    ax: Axes | None = None,
    *,
    frequency_hz: float | None = None,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the deviations along every traverse at one frequency.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `frequency_hz` | The test frequency to draw; `None` draws the one qualified to the shortest distance. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the deviation curves. |

**Returns:** The axes.

## MicrophoneTraverse

```python
MicrophoneTraverse(
    positions_m: np.ndarray,
    levels_db: np.ndarray,
    monitor_levels_db: np.ndarray | None = None,
    background_levels_db: np.ndarray | None = None,
    name: str = '',
    targets: tuple[str, ...] = (),
)
```

One straight microphone traverse of ISO 26101:2017 5.1.3.2.

**Attributes**

| Name | Description |
| :--- | :--- |
| `positions_m` | The measurement points, one row per point, as `(x, y, z)` coordinates in metres in the room frame: `z` points up and, in a hemi-anechoic room, the reflecting plane is `z = 0`. The mathematical origin of the traverse is given to [`inverse_square_law_deviations`](/phonometry/reference/api/power/free-field-qualification/#inverse_square_law_deviations) in the same frame. |
| `levels_db` | The measured sound pressure level $L'_{pi}$ at each point, one row per point and one column per test frequency, in dB. A `nan` marks a point not measured at that frequency, which is how a spacing that changes with frequency is written (ISO 3745 A.4.3 asks for equally spaced points *at each frequency*). Every other level is finite. |
| `monitor_levels_db` | The monitor microphone level $L_{p,\mathrm{ref},i}$ recorded with each point, same shape; the first row is the level for the initial point 0, which every point is corrected to. It is finite wherever a level was measured and in the first row of every frequency measured. `None` applies no stability correction. |
| `background_levels_db` | The background level at each point, same shape, or one row for the whole traverse, finite wherever a level was measured; `None` leaves the 6 dB requirement of ISO 26101 5.1.2.2 c) unjudged. |
| `name` | A label for the traverse (the path it follows: a dihedral corner, the nearest wall, a door). |
| `targets` | What the path is selected towards, among the five of the amended ISO 3745 A.3.3 a) to e): `"dihedral corner"`, `"trihedral corner"`, `"boundary centre"` (the centre of the most uniform boundary surface), `"closest boundary"` and `"unique features"` (a door, a window, a ventilation opening). One path may serve more than one target, as A.3.3 NOTE 1 allows for c) and d); an empty tuple names none. |

### MicrophoneTraverse.along()

*classmethod*

```python
MicrophoneTraverse.along(
    direction: ArrayLike,
    distances_m: ArrayLike,
    levels_db: ArrayLike,
    *,
    start_m: ArrayLike = (0.0, 0.0, 0.0),
    monitor_levels_db: ArrayLike | None = None,
    background_levels_db: ArrayLike | None = None,
    name: str = '',
    targets: Sequence[str] = (),
) -> MicrophoneTraverse
```

A traverse laid out along a straight line from `start_m`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `direction` | The direction of the path, any non-zero 3-vector. |
| `distances_m` | The distance of each point from `start_m` along the path, in metres. |
| `levels_db` | One row per point, one column per frequency, in dB. |
| `start_m` | The point the distances are counted from, in metres; the room frame's origin by default. |
| `monitor_levels_db` | As for the class. |
| `background_levels_db` | As for the class. |
| `name` | As for the class. |
| `targets` | As for the class. |

**Returns:** The traverse.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a direction that is zero or not finite. |

## qualification_frequencies_hz

```python
qualification_frequencies_hz(
    low_hz: float = 100.0,
    high_hz: float = 10000.0,
) -> np.ndarray
```

The frequencies ISO 3745:2012/Amd.1:2017 A.2.3 evaluates over a range.

Below 125 Hz and above 4 000 Hz every one-third octave band, between them
the octave mid-band frequencies 125, 250, 500, 1 000, 2 000 and 4 000 Hz.
The default range is the least A.2.3 allows, 100 Hz to 10 000 Hz: eleven
frequencies.

**Parameters**

| Name | Description |
| :--- | :--- |
| `low_hz` | Lowest band of the range, in hertz (read in its band). |
| `high_hz` | Highest band of the range, in hertz. |

**Returns:** The nominal frequencies to evaluate, ascending, in hertz.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if the range is empty. |

## SourceDirectionalityResult

```python
SourceDirectionalityResult(
    frequencies_hz: np.ndarray,
    room: str,
    mean_level_db: np.ndarray,
    maximum_positive_deviation_db: np.ndarray,
    maximum_negative_deviation_db: np.ndarray,
    tolerance_db: np.ndarray,
)
```

Whether a test source is uniform enough to qualify a room (ISO 26101 B.4).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | The one-third octave mid-band frequencies, in hertz. |
| `room` | The room type the source is to qualify. |
| `mean_level_db` | The arithmetic mean of the decibel levels per band. |
| `maximum_positive_deviation_db` | The largest level above the mean. |
| `maximum_negative_deviation_db` | The largest level below the mean, a negative number. |
| `tolerance_db` | The Table B.1 limit per band, in dB. |

### SourceDirectionalityResult.passes

*property*

Whether the directionality is within Table B.1 in every band.

**Returns:** `True` when every band is within its limit.

### SourceDirectionalityResult.plot()

```python
SourceDirectionalityResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the extreme deviations per band against Table B.1.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the deviation bars. |

**Returns:** The axes.

### SourceDirectionalityResult.within_tolerance

*property*

Per band, whether both extreme deviations are within Table B.1.

**Returns:** One boolean per band.

## verify_source_directionality

```python
verify_source_directionality(
    levels_db: ArrayLike,
    *,
    frequencies_hz: ArrayLike,
    room: FreeFieldRoom,
) -> SourceDirectionalityResult
```

May this source qualify an anechoic or hemi-anechoic room? (ISO 26101 Annex B).

The one-third octave band levels are measured at the 32 positions of a
hemisphere or the 64 of a sphere of radius 1,5 m
([`directionality_positions`](/phonometry/reference/api/power/free-field-qualification/#directionality_positions)). Per band, the arithmetic mean of the
decibel levels and the largest positive and negative deviations from it
are computed (B.3.2); the source is suitable when every deviation is within
Table B.1 (B.4). The amended ISO 3745 A.3.1 lets the measurement be made in
the room being qualified.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | One row per position (32 hemi-anechoic, 64 anechoic), one column per band, in dB; a 1-D array is one band. |
| `frequencies_hz` | The one-third octave mid-band frequencies, in hertz. |
| `room` | `"anechoic"` or `"hemi-anechoic"`. |

**Returns:** [`SourceDirectionalityResult`](/phonometry/reference/api/power/free-field-qualification/#sourcedirectionalityresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for the wrong number of positions, levels that are not finite, or bands that do not match. |
