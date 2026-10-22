---
title: "simulation.fdtd"
description: "2D acoustic finite-difference time-domain (FDTD) simulation."
sidebar:
  label: "fdtd"
---

2D acoustic finite-difference time-domain (FDTD) simulation.

A staggered-grid (Yee-style) pressure-velocity leapfrog solver for the
linear acoustic equations in a non-moving medium, following the reference
formulation of Attenborough & Van Renterghem, *Predicting Outdoor Sound*
(2nd ed., CRC Press 2021), chapter 4:

* the governing first-order system in `p` and `v` (Eqs. 4.3-4.4);
* the staggered-in-place, staggered-in-time discretisation (Eqs. 4.11-4.12),
  with pressure at cell centres and velocity components on cell faces;
* the Courant stability condition $C_\mathrm{N} \le 1$ with
  $C_\mathrm{N} = c\,\Delta t \sqrt{1/\Delta x^2 + 1/\Delta y^2}$
  (Eqs. 4.13-4.14);
* rigid boundaries as zero normal face velocity (Eq. 4.32) and the
  frequency-independent real-impedance boundary update (Eqs. 4.33-4.35);
* absorbing edges as a graded sponge layer, the simple precursor of the
  perfectly-matched-layer treatment discussed in section 4.2.3.

Two API levels are exposed. [`fdtd_simulation`](/phonometry/reference/api/simulation/fdtd/#fdtd_simulation) is the result-object
entry point: it takes an [`FDTDRun`](/phonometry/reference/api/simulation/fdtd/#fdtdrun), the record of a simulation that
checks every argument when it is built, steps it deterministically and
returns a frozen [`FDTDResult`](/phonometry/reference/api/simulation/fdtd/#fdtdresult) with per-probe pressure histories,
optional field snapshots and a `.plot()` method. [`FDTD2D`](/phonometry/reference/api/simulation/fdtd/#fdtd2d) is the underlying
stepping engine (also used by the documentation animations) for callers that
need frame-by-frame access to the field.

The solver is deliberately deterministic: no random numbers, and every
operation in a fixed order. On NumPy in float64 identical inputs give
bit-identical outputs on the same platform. On CuPy in float64 the recorded
proof (`gpu-parity.lock`) found every field, snapshot and contour phasor
bit-identical to NumPy's over the scenarios of both engines, and the energy
within 1.79e-16 relative over them, because the GPU sums it in another
order; the guide on where a simulation runs names the hardware it was
measured on. Runs on torch's CPU device, and float32 runs on NumPy, agree
with NumPy in float64 within the tolerance that guide publishes for each
device and dtype. Each of these bounds is the worst over that scenario
matrix (grids of up to 64 by 48 cells, up to 120 steps), not a promise about
any run: float32 rounding grows with the number of steps. An acoustic run
of 8085 steps on a 200 by 300 cell grid, driven by a 1 kHz `CWSource`,
differed by 8.0e-06 relative at its probe (4.0e-06 with a Gaussian pulse),
on NumPy and on torch's CPU device alike. A float32 run on CuPy, and any run
on torch's CUDA device, is not measured yet.

Validated against analytic oracles: the eigenfrequencies of a rigid
rectangular box and of an effectively 1D tube, the numerical dispersion
relation of the leapfrog scheme (the discrete counterpart of Eq. 4.15),
free-field pulse arrival times and cylindrical $1/\sqrt{r}$ amplitude
decay, the image-source echo of a rigid wall, the normal-incidence
reflection coefficient $(Z - \rho c)/(Z + \rho c)$ of an impedance
edge, and second-order convergence under grid refinement.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## ContourProbe

```python
ContourProbe(
    sim: FDTD2D,
    ix0: int,
    ix1: int,
    iy0: int,
    iy1: int,
    frequencies: ArrayLike,
)
```

On-the-fly DFT of `p` and `v_n` on a closed rectangular contour.

Created by [`FDTD2D.add_contour_probe`](/phonometry/reference/api/simulation/fdtd/#fdtd2dadd_contour_probe). The contour is the closed
rectangle of cell faces around the cell block `ix0..ix1` x
`iy0..iy1` (inclusive); on each face the engine samples the outward
normal velocity (which lives exactly there on the staggered grid) and
the pressure averaged from the two adjacent cell centres, and folds
them into running DFT sums at each requested frequency, so a
continuous-wave run never stores full time histories.

After every step the sums gain $p\, \mathrm{e}^{-j \omega t}$ with
the fields' own leapfrog time stamps ($t = n\,\Delta t$ for
pressure, $t = (n - 1/2)\,\Delta t$ for velocity, so the half-step
stagger is handled
exactly). `phasors` scales the sums by `2 / n_samples` into the
steady-state complex amplitudes of the library's $\mathrm{e}^{+j \omega t}$
convention. Accumulate only over the steady state: run the transient
out, call `reset`, then integrate a window as close as possible
to a whole number of periods (the residual leakage falls as one over
the number of periods).

The sums are kept in float64 on every device that has it, also when the
fields step in float32: the rounding of a sum grows with the number of
steps, and in float32 it would soon outweigh the field's own. The
exception is `torch:mps`, which has no float64; there the sums are
float32 with Neumaier's compensated summation.

**Attributes**

| Name | Description |
| :--- | :--- |
| `positions` | Face-sample positions `(x, y)` [m], shape `(n_points, 2)`, ordered left, right, top, bottom face. |
| `normals` | Outward unit normals of each sample, same shape. |
| `frequencies` | The tracked frequencies [Hz]. |
| `samples` | Number of steps accumulated since the last reset. |

**Raises**

| Exception | When |
| :--- | :--- |
| TypeError | if `ix0`, `ix1`, `iy0` or `iy1` is a flag, a text or an array where a count goes. |

### ContourProbe.phasors()

```python
ContourProbe.phasors(frequency: float) -> ContourPhasors
```

The accumulated contour phasors at one tracked frequency.

**Parameters**

| Name | Description |
| :--- | :--- |
| `frequency` | One of the frequencies the probe was created with, in hertz. |

**Returns:** A [`ContourPhasors`](/phonometry/reference/api/simulation/ntff/#contourphasors) ready for [`far_field_from_contour`](/phonometry/reference/api/simulation/ntff/#far_field_from_contour).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the frequency is not tracked or nothing has been accumulated yet. |

### ContourProbe.reset()

```python
ContourProbe.reset() -> None
```

Clear the running sums (call once the field is steady).

## CWSource

```python
CWSource(
    *,
    ix: int,
    iy: int,
    frequency: float,
    amplitude: float = 1.0,
    ramp_cycles: float = 3.0,
)
```

A continuous sine drive with a smooth cosine-ramped onset.

The first `ramp_cycles` periods fade the amplitude in with a raised
cosine so the start does not splash a broadband transient over the field.

**Attributes**

| Name | Description |
| :--- | :--- |
| `ix` | Source column (x) index. |
| `iy` | Source row (y) index. |
| `frequency` | Drive frequency [Hz]. |
| `amplitude` | Steady-state source amplitude [Pa]. |
| `ramp_cycles` | Onset ramp length in periods of `frequency`. |

### CWSource.value()

```python
CWSource.value(t: float) -> float
```

Source waveform at time `t` (seconds).

## FDTD2D

```python
FDTD2D(
    c: float | NDArray[np.float64],
    dx: float,
    *,
    rho: float | NDArray[np.float64] = 1.2,
    cfl: float = 0.6,
    sponge_width: int = 0,
    sponge_sides: Literal['left', 'right', 'top', 'bottom'] | Iterable[Literal['left', 'right', 'top', 'bottom']] | None = None,
    sponge_reflection: float = 0.0001,
    damping: float | NDArray[np.float64] = 0.0,
    shape: tuple[int, int] | None = None,
    edge_impedance: Mapping[Literal['left', 'right', 'top', 'bottom'], float | NDArray[np.float64]] | None = None,
    obstacle_mask: NDArray[np.bool_] | None = None,
    compute: Compute | None = None,
)
```

2D acoustic FDTD stepping engine on a staggered grid.

Pressure `p` lives at cell centres, shape `(ny, nx)` (row = y,
column = x, the `imshow` convention); `vx` at interior x-faces,
shape `(ny, nx - 1)`; `vy` at interior y-faces, shape
`(ny - 1, nx)`. Because only interior faces are stored, the domain
boundary is perfectly rigid (zero normal velocity, Eq. 4.32) by
construction; sponge layers and per-cell real impedances turn selected
sides into absorbing or locally reacting boundaries. Sources are soft
(additive) pressure injections.

**Parameters**

| Name | Description |
| :--- | :--- |
| `c` | Sound-speed map [m/s], shape `(ny, nx)`. A scalar with an explicit `shape` is also accepted. |
| `dx` | Grid spacing [m] (square cells). |
| `rho` | Density map [kg/m3]; scalar or `(ny, nx)` array (default 1.2). |
| `cfl` | Courant number $C_\mathrm{N} = c_{\max}\, \Delta t \sqrt{2} / \Delta x$ (Eq. 4.13); the explicit scheme is stable for $C_\mathrm{N} \le 1$ (Eq. 4.14) and values in `(0, 1)` are accepted. The default 0.6 keeps a wide stability margin with moderate numerical dispersion. |
| `sponge_width` | Thickness of the absorbing layer in cells (0 = no absorbing sides). |
| `sponge_sides` | Which sides absorb: a single side name or an iterable drawn from `{"left", "right", "top", "bottom"}` (default: all four when `sponge_width > 0`). `left`/`right` are the low/high column edges and `top`/`bottom` the low/high row edges (the default `imshow` origin). |
| `sponge_reflection` | Target round-trip amplitude reflection of the sponge layer; sets the peak absorption rate. |
| `damping` | Bulk amplitude decay rate [1/s]: a scalar applied to the whole field (a simple stand-in for air/wall absorption; `6.91 / T60` gives a `T60` seconds reverberant decay) or an `(ny, nx)` map for locally lossy regions, e.g. an equivalent fluid modelling a porous sample (plane waves inside a uniform lossy region follow $k = (\omega - j \sigma) / c$ with the real characteristic impedance $\rho c$). |
| `shape` | Grid shape `(ny, nx)`, required only when `c` is a scalar. |
| `edge_impedance` | Locally reacting boundary sides: a mapping from side name to a real specific acoustic impedance [Pa s/m], either a scalar or a per-edge-cell 1D array (length `ny` for `left`/ `right`, `nx` for `top`/`bottom`). Implements Eqs. (4.33)-(4.35); $Z = \rho c$ is a normal-incidence matched (anechoic) edge. A side cannot be both a sponge and an impedance boundary. |
| `obstacle_mask` | Boolean map, shape `(ny, nx)`, of rigid cells: every face adjacent to a masked cell is closed (zero normal velocity, Eq. 4.32), rasterising arbitrary interior geometry. |
| `compute` | Where the engine steps ([`Compute`](/phonometry/reference/api/simulation/compute/#compute)); `None` follows [`use`](/phonometry/reference/api/simulation/compute/#use), then `PHONOMETRY_COMPUTE`, then NumPy. |

**Raises**

| Exception | When |
| :--- | :--- |
| TypeError | if `cfl`, `dx` or `sponge_reflection` is not a single number, `sponge_width` is a flag, a text or an array where a count goes, or `compute` is neither a [`Compute`](/phonometry/reference/api/simulation/compute/#compute) nor `None`. |
| ValueError | for an argument out of its range, and for a `compute` that names a host: an engine steps in this process, and only [`fdtd_simulation`](/phonometry/reference/api/simulation/fdtd/#fdtd_simulation) runs on a node. |
| ComputeImportError | when the library of the device `compute` asks for is not installed or does not import. |
| ComputeDeviceError | when that device is not present, or fails a first small computation; with `fallback=True` the engine warns with [`ComputeFallbackWarning`](/phonometry/reference/api/simulation/compute/#computefallbackwarning) and steps on NumPy instead. |

### FDTD2D.add_contour_probe()

```python
FDTD2D.add_contour_probe(
    ix0: int,
    ix1: int,
    iy0: int,
    iy1: int,
    *,
    frequencies: ArrayLike,
) -> ContourProbe
```

Record `p` and `v_n` phasors on a closed rectangular contour.

The contour is the rectangle of cell faces enclosing the cell
block `ix0..ix1` x `iy0..iy1` (both ends inclusive): its sides
lie on $x = i_{x0}\,\Delta x$, $x = (i_{x1}+1)\,\Delta x$,
$y = i_{y0}\,\Delta x$ and $y = (i_{y1}+1)\,\Delta x$. From
the step after registration the engine
folds the face pressures (averaged from the two adjacent cell
centres) and the outward face normal velocities into running DFT
sums at each requested frequency; see [`ContourProbe`](/phonometry/reference/api/simulation/fdtd/#contourprobe)
for the steady-state protocol and
[`far_field_from_contour`](/phonometry/reference/api/simulation/ntff/#far_field_from_contour) for the
far-field transformation of the captured phasors.

Place the contour in open air: strictly around the scatterer,
clear of sponge layers and of any source (point sources and
plane-wave injection lines must stay outside so the enclosed
region is source-free in a scattering run, or inside when the
radiated field itself is the quantity of interest).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ix0` | First cell column inside the contour. |
| `ix1` | Last cell column inside the contour. |
| `iy0` | First cell row inside the contour. |
| `iy1` | Last cell row inside the contour. |
| `frequencies` | Frequencies to track [Hz]. |

**Returns:** The registered [`ContourProbe`](/phonometry/reference/api/simulation/fdtd/#contourprobe).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a block without open faces on all sides or invalid frequencies. |

### FDTD2D.add_plane_wave()

```python
FDTD2D.add_plane_wave(
    direction: Literal['down', 'up', 'left', 'right'],
    *,
    center: float,
    width: float,
    amplitude: float = 1.0,
    wavelength: float | None = None,
) -> None
```

Superimpose a one-way plane wave packet as an initial condition.

A Gaussian envelope (optionally carrying a sine at `wavelength`)
is written onto the pressure field, and the leapfrog-consistent
particle velocity is written a half time step back, so the packet
propagates only toward `direction` (the axes of
`plot_geometry`: `"down"`/`"up"` along y,
`"right"`/`"left"` along x). The packet is uniform across the
transverse direction and adds to whatever fields are present.

Obstacles are not carved out of the initial condition: place the
packet in free field (its envelope clear of `obstacle_mask`
cells), as a physical incident wave would be.

**Parameters**

| Name | Description |
| :--- | :--- |
| `direction` | Travel direction, one of `"down"`, `"up"`, `"left"`, `"right"`. |
| `center` | Envelope centre along the travel axis, in metres. |
| `width` | Gaussian envelope width (the `1/e` half-width), in metres. |
| `amplitude` | Peak pressure of the envelope, in pascals. |
| `wavelength` | Optional carrier wavelength, in metres; `None` gives the pure Gaussian pulse. |

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an unknown direction, a non-positive or non-finite `width`/`wavelength`, or a non-finite `center`/`amplitude`. |
| TypeError | if `amplitude`, `center`, `wavelength` or `width` is not a single number. |

### FDTD2D.add_source()

```python
FDTD2D.add_source(
    source: GaussianPulse | CWSource | SignalSource | PlaneWaveSource,
) -> None
```

Register a source: a point injection or a plane-wave line.

Point sources ([`GaussianPulse`](/phonometry/reference/api/simulation/fdtd/#gaussianpulse), [`CWSource`](/phonometry/reference/api/simulation/fdtd/#cwsource),
[`SignalSource`](/phonometry/reference/api/simulation/fdtd/#signalsource)) inject additively at one cell. A
[`PlaneWaveSource`](/phonometry/reference/api/simulation/fdtd/#planewavesource) injects a sustained one-way plane wave on
a full line of cells near its launch edge.

### FDTD2D.energy()

```python
FDTD2D.energy() -> float
```

Total acoustic field energy [J per metre of depth].

### FDTD2D.host_field()

```python
FDTD2D.host_field(name: Literal['p', 'vx', 'vy']) -> NDArray[np.floating]
```

A NumPy copy of the stored field *name*, whatever the device.

**Parameters**

| Name | Description |
| :--- | :--- |
| `name` | `"p"` (cell centres), `"vx"` or `"vy"` (faces). |

**Raises**

| Exception | When |
| :--- | :--- |
| TypeError | if `name` is not a text. |
| ValueError | for a field the engine does not store. |

### FDTD2D.plot_geometry()

```python
FDTD2D.plot_geometry(
    ax: Axes | None = None,
    *,
    probes: ArrayLike | None = None,
    language: Literal['en', 'es'] = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the configured domain before running it.

Domain extent, obstacles, sponge layers, impedance and rigid edges
and the added sources, with optional probe positions previewed; no
time stepping happens. Requires matplotlib
(`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `probes` | Optional probe positions `(x, y)` in metres, shape `(N, 2)` (the [`fdtd_simulation`](/phonometry/reference/api/simulation/fdtd/#fdtd_simulation) convention). |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the obstacle `imshow`. |

### FDTD2D.provenance

*property*

Where this engine steps: device, dtype and library versions.

### FDTD2D.run()

```python
FDTD2D.run(
    n_steps: int,
    snapshot_every: int | None = None,
    snapshot_decimation: int = 1,
) -> NDArray[np.floating]
```

Advance `n_steps` steps, optionally recording pressure frames.

With `snapshot_every = k` a host copy of `p` is stored after
every `k`-th step (and one of the initial state), keeping every
`snapshot_decimation`-th cell along each axis; the stacked
`(n_frames, ny', nx')` array plugs straight into a `FuncAnimation`
`imshow` update. Without `snapshot_every` an empty array is
returned and only the final state is kept (read it with
`host_field`).

**Raises**

| Exception | When |
| :--- | :--- |
| TypeError | if `snapshot_decimation`, `n_steps` or `snapshot_every` is a flag, a text or an array where a count goes. |
| ValueError | if `n_steps` is not a whole number of 0 or more, or `snapshot_every` or `snapshot_decimation` is not a whole number of 1 or more. |

### FDTD2D.step()

```python
FDTD2D.step() -> None
```

Advance the leapfrog scheme by one time step.

### FDTD2D.time

*property*

Elapsed simulated time [s].

## fdtd_simulation

```python
fdtd_simulation(
    run: FDTDRun,
    *,
    compute: Compute | None = None,
) -> FDTDResult
```

Run a deterministic 2D acoustic FDTD simulation.

Builds the staggered-grid domain (Attenborough & Van Renterghem 2021,
Eqs. 4.11-4.12), applies the requested boundary conditions, injects the
sources and integrates for `duration` seconds, recording the pressure
at every probe each time step and, optionally, full-field snapshots.

The grid covers `(nx * dx, ny * dx)` metres; a cell index `(ix, iy)`
maps to the physical cell centre `((ix + 0.5) * dx, (iy + 0.5) * dx)`.
Resolve at least 10 cells per shortest wavelength using the smallest
sound speed of the domain ($\Delta x \le c_{\min} / (10 f)$), the
usual rule for
this lowest-order scheme: the worst-case (on-axis) numerical dispersion
error magnitude, $(k \Delta x)^2 / 24$ from the discrete counterpart
of
Eq. 4.15 (the modelled frequency under-reads, so the signed error is
negative), is then about 1.6 % (about 1.4 % at the default `cfl`;
in a heterogeneous domain the slower cells run at a lower local Courant
number and sit nearer the 1.6 % bound) and finer grids reduce it
quadratically. The
simulation is 2D, so a point source is
physically a line source with cylindrical $1/\sqrt{r}$ amplitude
spreading rather than the 3D spherical $1/r$.

**Parameters**

| Name | Description |
| :--- | :--- |
| `run` | The simulation ([`FDTDRun`](/phonometry/reference/api/simulation/fdtd/#fdtdrun)): the domain, its sources and what it records, every argument checked when the run was built. |
| `compute` | Where the run steps ([`Compute`](/phonometry/reference/api/simulation/compute/#compute)); `None` follows [`use`](/phonometry/reference/api/simulation/compute/#use), then `PHONOMETRY_COMPUTE`, then NumPy. With a `host` the whole run goes to that node, named in the hosts file, and comes back as this function's record (see the guide on remote nodes). |

**Returns:** A [`FDTDResult`](/phonometry/reference/api/simulation/fdtd/#fdtdresult).

**Raises**

| Exception | When |
| :--- | :--- |
| TypeError | For a `run` that is not an [`FDTDRun`](/phonometry/reference/api/simulation/fdtd/#fdtdrun), a `compute` that is neither a [`Compute`](/phonometry/reference/api/simulation/compute/#compute) nor `None`, or, when `compute` names a host, a run that cannot travel to a node: a source whose waveform is a callable other than the `value` of a [`GaussianPulse`](/phonometry/reference/api/simulation/fdtd/#gaussianpulse), [`CWSource`](/phonometry/reference/api/simulation/fdtd/#cwsource) or [`SignalSource`](/phonometry/reference/api/simulation/fdtd/#signalsource). |
| ValueError | For a `PHONOMETRY_COMPUTE` that does not parse, or a malformed hosts file. |
| KeyError | For a `host` the hosts file does not name. |
| ComputeImportError | When the device's library is not installed or does not import. |
| ComputeDeviceError | When the device is not present, or fails a first small computation; with `fallback=True` the run warns with [`ComputeFallbackWarning`](/phonometry/reference/api/simulation/compute/#computefallbackwarning) and steps on NumPy instead. |
| ComputeRemoteError | For a failure of the connection or of the node; with `fallback=True` the run warns with [`ComputeFallbackWarning`](/phonometry/reference/api/simulation/compute/#computefallbackwarning) and steps on NumPy here instead. |

## FDTDRecording

```python
FDTDRecording(
    *,
    probes: Sequence[tuple[int, int]] = (),
    snapshot_every: int | None = None,
    snapshot_decimation: int = 1,
)
```

What an acoustic run writes down: probe histories and field snapshots.

The two ways out of a running simulation. Probes record the pressure
history at named cells; snapshots record the whole pressure field every
`snapshot_every` steps. Recording nothing (the default) runs the
physics and keeps only the time axis.

**Parameters**

| Name | Description |
| :--- | :--- |
| `probes` | Pressure-probe cells as `(ix, iy)` index pairs. |
| `snapshot_every` | Record a full pressure-field snapshot every this many steps (and at $t = 0$); `None` records none. |
| `snapshot_decimation` | Keep every this many cells along each axis in a snapshot (default 1, every cell); the result records it. |

**Raises**

| Exception | When |
| :--- | :--- |
| TypeError | for a probe that is not a pair or has an index that is not a number, a `snapshot_every` that is a flag, a text, an array or anything else that is neither a number nor `None`, or a `snapshot_decimation` that is a flag, a text, an array or anything else that is not a number. |
| ValueError | for a probe of more or fewer than two indices or with an index that is not a whole number, or a `snapshot_every` or `snapshot_decimation` that is not a whole number of 1 or more. |

## FDTDResult

```python
FDTDResult(
    times: NDArray[np.float64],
    pressures: NDArray[np.float64],
    probes: NDArray[np.int_],
    probe_positions: NDArray[np.float64],
    dx: float,
    dt: float,
    shape: tuple[int, int],
    sources: tuple[GaussianPulse | CWSource | SignalSource | PlaneWaveSource, ...],
    snapshots: NDArray[np.floating] | None,
    snapshot_times: NDArray[np.float64] | None,
    obstacle_mask: NDArray[np.bool_] | None,
    snapshot_decimation: int,
    provenance: RunProvenance,
)
```

Frozen result of a [`fdtd_simulation`](/phonometry/reference/api/simulation/fdtd/#fdtd_simulation) run.

**Attributes**

| Name | Description |
| :--- | :--- |
| `times` | Time axis [s], length `n_steps + 1` (includes $t = 0$). |
| `pressures` | Pressure history at each probe [Pa], shape `(n_probes, n_steps + 1)`. |
| `probes` | Probe cell indices `(ix, iy)`, shape `(n_probes, 2)`. |
| `probe_positions` | Probe cell-centre positions `(x, y)` [m], shape `(n_probes, 2)`. |
| `dx` | Grid spacing [m]. |
| `dt` | Time step [s]. |
| `shape` | Grid shape `(ny, nx)`. |
| `sources` | The source definitions of the run. |
| `snapshots` | Recorded pressure fields, shape `(n_frames, ceil(ny / d), ceil(nx / d))` with `d` the `snapshot_decimation`, in the dtype the run stepped in, or `None` when no snapshots were requested. |
| `snapshot_times` | Time of each snapshot [s], or `None`. |
| `obstacle_mask` | Boolean map of rigid cells, or `None`. |
| `snapshot_decimation` | Every how many cells a snapshot keeps along each axis (1 keeps every cell). |
| `provenance` | Where the run stepped ([`RunProvenance`](/phonometry/reference/api/simulation/compute/#runprovenance)). |

### FDTDResult.plot()

```python
FDTDResult.plot(
    ax: Axes | None = None,
    *,
    kind: Literal['probes', 'snapshot'] = 'probes',
    frame: int = -1,
    language: Literal['en', 'es'] = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the probe histories or one recorded field snapshot.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `kind` | `"probes"` (default) draws the per-probe pressure time histories; `"snapshot"` renders one recorded pressure field with the geometry overlaid (`imshow` raster). |
| `frame` | Snapshot index for `kind="snapshot"` (default: the last recorded frame). |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the underlying `plot`/`imshow`. |

**Returns:** The axes.

### FDTDResult.size

*property*

Domain size `(lx, ly)` [m].

## FDTDRun

```python
FDTDRun(
    c: float | NDArray[np.float64],
    dx: float,
    duration: float,
    *,
    sources: Sequence[GaussianPulse | CWSource | SignalSource | PlaneWaveSource],
    shape: tuple[int, int] | None = None,
    rho: float | NDArray[np.float64] = 1.2,
    cfl: float = 0.6,
    recording: FDTDRecording | None = None,
    boundaries: Literal['rigid', 'absorbing'] | Mapping[Literal['left', 'right', 'top', 'bottom'], Literal['rigid', 'absorbing'] | float | NDArray[np.float64]] = 'rigid',
    absorbing_layer_cells: int = 20,
    obstacle_mask: NDArray[np.bool_] | None = None,
    damping: float = 0.0,
)
```

One acoustic FDTD simulation: the domain, its sources and what it records.

Every argument is checked when the run is built, the grid's included:
the time step, the density, the sponge and the damping, the impedance
edges, the obstacle, and the sources and the probes on the grid. A run
that builds is one [`fdtd_simulation`](/phonometry/reference/api/simulation/fdtd/#fdtd_simulation) can step, here or on a node,
and a bad argument raises where the run is written, with the class and
the words the function always raised. The sources are held as a tuple,
a mapping of boundaries as a read-only mapping, and each array as the
run's own read-only copy, so nothing the caller changes afterwards
reaches a checked run.

**Parameters**

| Name | Description |
| :--- | :--- |
| `c` | Sound-speed map [m/s], shape `(ny, nx)`, or a scalar with an explicit `shape`. |
| `dx` | Grid spacing [m] (square cells). |
| `duration` | Physical time to simulate [s]. |
| `sources` | One or more of [`GaussianPulse`](/phonometry/reference/api/simulation/fdtd/#gaussianpulse), [`CWSource`](/phonometry/reference/api/simulation/fdtd/#cwsource), [`SignalSource`](/phonometry/reference/api/simulation/fdtd/#signalsource) or [`PlaneWaveSource`](/phonometry/reference/api/simulation/fdtd/#planewavesource). |
| `shape` | Grid shape `(ny, nx)`, required when `c` is a scalar. |
| `rho` | Density map [kg/m3]; scalar or `(ny, nx)` array. |
| `cfl` | Courant number in `(0, 1)` (Eqs. 4.13-4.14); the time step is $\Delta t = C_\mathrm{N}\, \Delta x / (c_{\max} \sqrt{2})$. Default 0.6. |
| `recording` | What the run records ([`FDTDRecording`](/phonometry/reference/api/simulation/fdtd/#fdtdrecording)): the probe cells, and the snapshot cadence and decimation. `None` records nothing but the time axis. |
| `boundaries` | `"rigid"` (default), `"absorbing"`, or a mapping from side name (`left`/`right`/`top`/`bottom`) to `"rigid"`, `"absorbing"`, or a real specific impedance [Pa s/m] (scalar or per-edge-cell 1D array, Eqs. 4.33-4.35). |
| `absorbing_layer_cells` | Sponge-layer thickness for absorbing sides, in cells. |
| `obstacle_mask` | Boolean map, shape `(ny, nx)`, of rigid cells (rasterised interior geometry). |
| `damping` | Uniform bulk amplitude decay rate [1/s]. |

**Raises**

| Exception | When |
| :--- | :--- |
| TypeError | If an argument is of the wrong type: a `duration`, `cfl` or `dx` that is not one number, a `recording` that is neither an [`FDTDRecording`](/phonometry/reference/api/simulation/fdtd/#fdtdrecording) nor `None`, an `absorbing_layer_cells` that is not a number, a `shape` that is not a pair, a complex medium, or an `obstacle_mask` that is not boolean. |
| ValueError | If an argument is out of its range, or a source, a probe or the obstacle does not fit the grid. |

## GaussianPulse

```python
GaussianPulse(
    *,
    ix: int,
    iy: int,
    half_width_s: float,
    t0: float | None = None,
    amplitude: float = 1.0,
)
```

A soft Gaussian pressure pulse injected at one cell.

$s(t) = \text{amplitude} \cdot \mathrm{e}^{-((t - t_0)/w)^2}$, with $w$
the half-width `half_width_s` and `t0` defaulting to
`4 * half_width_s` so the pulse starts from (numerically) zero.

**Attributes**

| Name | Description |
| :--- | :--- |
| `ix` | Source column (x) index; the cell centre is at $x = (i_x + 0.5)\,\Delta x$. |
| `iy` | Source row (y) index. |
| `half_width_s` | Gaussian half-width $w$ [s]; it sets the pulse bandwidth. The name carries the unit because the perfectly matched layer of this same module measures its own width in cells. |
| `t0` | Pulse centre time [s] (default `4 * half_width_s`). |
| `amplitude` | Peak source amplitude [Pa]. |

### GaussianPulse.value()

```python
GaussianPulse.value(t: float) -> float
```

Source waveform at time `t` (seconds).

## PlaneWaveSource

```python
PlaneWaveSource(
    *,
    direction: str,
    waveform: Callable[[float], float],
    offset: int = 0,
    amplitude: float = 1.0,
)
```

A sustained one-way plane wave injected on a line near one edge.

A total-field/scattered-field style injection: each step the incident
wave is added simultaneously to the pressure on the injection line and
to the particle velocity on the adjacent face, so the wave launches
only toward `direction` and anything scattered back crosses the line
untouched (and can be absorbed by a sponge behind it).

`direction` is the travel direction (`"down"`, `"up"`,
`"left"`, `"right"` in the [`FDTD2D.plot_geometry`](/phonometry/reference/api/simulation/fdtd/#fdtd2dplot_geometry) axes) and
the line sits `offset` cells in from the opposite edge (place it just
inside the sponge layer when one is configured on that side).
`waveform` maps time in seconds to the incident pressure in pascals
(any callable, or reuse the `value` method of a point source).

**Attributes**

| Name | Description |
| :--- | :--- |
| `direction` | Travel direction of the launched wave. |
| `waveform` | Callable `t -> p_inc(t)` in pascals. |
| `offset` | Line position, in cells from the launch edge. |
| `amplitude` | Extra gain applied to `waveform`. |

## SignalSource

```python
SignalSource(
    *,
    ix: int,
    iy: int,
    samples: NDArray[np.float64],
    fs: float,
    amplitude: float = 1.0,
)
```

An arbitrary sampled waveform injected at one cell.

The samples are interpreted as the source signal at `fs` and
linearly interpolated onto the simulation time steps; outside the sampled
span the source is zero. `fs` therefore does not need to match
the simulation rate `1/dt`, although a rate well above the highest
frequency of interest avoids interpolation roll-off.

**Attributes**

| Name | Description |
| :--- | :--- |
| `ix` | Source column (x) index. |
| `iy` | Source row (y) index. |
| `samples` | Source signal samples [Pa] (stored as a read-only 1D float64 array). |
| `fs` | Sampling rate of `samples` [Hz]. |
| `amplitude` | Scale factor applied to the samples. |

### SignalSource.value()

```python
SignalSource.value(t: float) -> float
```

Source waveform at time `t` (seconds), zero outside the span.
