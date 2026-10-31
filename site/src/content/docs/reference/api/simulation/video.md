---
title: "simulation.video"
description: "Writing an FDTD run straight to a video file."
sidebar:
  label: "video"
---

Writing an FDTD run straight to a video file.

[`write_fdtd_animation`](/phonometry/reference/api/simulation/video/#write_fdtd_animation) steps the run
[`fdtd_simulation`](/phonometry/reference/api/simulation/fdtd/#fdtd_simulation) steps, an
[`FDTDRun`](/phonometry/reference/api/simulation/fdtd/#fdtdrun) checked when it was built, and draws
the pressure into a video as it is computed, through the encoders of
[`phonometry.io.write_video`](/phonometry/reference/api/io/io/#write_video), and [`write_elastic_fdtd_animation`](/phonometry/reference/api/simulation/video/#write_elastic_fdtd_animation)
does the same for [`elastic_fdtd_simulation`](/phonometry/reference/api/simulation/elastic-fdtd/#elastic_fdtd_simulation) and
an [`ElasticRun`](/phonometry/reference/api/simulation/elastic-fdtd/#elasticrun), drawing the field
`ElasticRecording.snapshot_field` names, with the colour limit of
[`AnimationFrame`](/phonometry/reference/api/simulation/video/#animationframe) in that field's unit. No snapshot is stored: a long run on a
large grid writes a long video in the memory one frame takes here (a GIF
apart, whose palette ffmpeg computes from every frame it holds). The run's
result comes back with its probes and times and without snapshots.

How each frame is drawn is one record, [`AnimationFrame`](/phonometry/reference/api/simulation/video/#animationframe) (the labels'
language, the size in pixels, the colour limit); how the video is encoded is
another, [`phonometry.io.VideoOptions`](/phonometry/reference/api/io/io/#videooptions), the one
[`phonometry.io.write_video`](/phonometry/reference/api/io/io/#write_video) takes. Before the first step ffmpeg is
found and run, and the encoder that will write the video is chosen by a real
one-frame encode at the frame's size, so neither a missing ffmpeg nor an
encoder that cannot write the video costs a run.

The frames show what the snapshot plot of the simulation function's result
(`plot` with `kind="snapshot"`)
shows: the same field on the same colormap, symmetric about zero, with the
same marks and labels, the limit of the scale being the video's own (fixed
for the whole video, given or found, as the next paragraph says); a
writer's own result holds no snapshots to plot. A frame is laid
out once for the whole run, for the widest title it shows (the time of its
last frame) and the labels of its axes and colour scale, so that no text
leaves the frame and nothing moves from one frame to the next; the title is
centred over the frame. Every text keeps its own size: a frame is at least
479 by 245 pixels, the smallest in which every text, at its own size, stays
clear of the frame's margin and covers no other, with the field still in
view for a grid up to ten times longer one way than the other, on every
matplotlib version the library is tested with. An axis too short for the
numbers matplotlib would write along it keeps fewer of them, never one over
another: a tall grid's narrow field may show a single number under it. That
holds for a run whose last frame comes before ten seconds; a later one
writes more digits in its title's time, and needs a frame about 10.6 pixels
wider for each digit past four before the point in milliseconds: a narrower
one is refused before the run starts, with the width it needs. The frames are drawn
once and then updated in place, under matplotlib's default style whatever
the caller's settings say, so a video written here and one written on
another machine look alike. One frame is drawn every
`run.recording.snapshot_every` steps, at the decimation
`run.recording.snapshot_decimation` gives.

The colour scale is fixed for the whole video. With a limit given, each
frame is drawn as the run computes it. Without one the run steps twice: a
first pass, which stops at the last frame, finds, on the device, the largest
magnitude the drawn field reaches outside the source cells, the plane-wave
injection lines and the absorbing layer, where the field is what the source
or the sponge makes it rather than the wave the video shows, and the second
pass draws with that limit. Neither pass stores a snapshot.

With a `host` in `compute` the run is computed, drawn and encoded on
that node, named in the hosts file (see the guide on remote nodes), and only
the result and the video's bytes come back. Every argument is checked here
first, so a call refused here never starts ssh, and ffmpeg is found and run
on the node: this machine runs it only when a node that failed falls back
to it (`fallback=True`). The bytes go, as they arrive, into a partial file
beside `path`, whose name starts with a dot (hidden on Linux and macOS),
created before ssh starts so that a directory that does not take it fails
first: never more of them than the frames can take, and none that do not
begin as the container `path` names. That file takes `path`'s place once
the node's whole answer has been read and checked, and is removed if
anything fails before (or stays, under its own name, if the system does not
let it go, which hides no error).

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## AnimationFrame

```python
AnimationFrame(
    *,
    language: Literal['en', 'es'] = 'en',
    size: tuple[int | np.integer[Any], int | np.integer[Any]] | list[int | np.integer[Any]] = (960, 540),
    color_limit: float | None = None,
)
```

How each frame of a simulation video is drawn: in which language, at what size, on what scale.

**Parameters**

| Name | Description |
| :--- | :--- |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `size` | `(width, height)` of a frame in pixels, at least 479 by 245, the smallest frame in which every text, at its own size, stays clear of the frame's margin and the field still shows (for a grid up to ten times longer one way than the other), on every matplotlib version the library is tested with (default `(960, 540)`). That is for a run whose last frame comes before ten seconds: a later one needs a wider frame for the time its last title writes, which the writers ask for before the run starts. |
| `color_limit` | The value at either end of the colour scale, fixed for the whole video, in the unit of the field drawn: pascals for an acoustic run ([`write_fdtd_animation`](/phonometry/reference/api/simulation/video/#write_fdtd_animation)), and for an elastic one ([`write_elastic_fdtd_animation`](/phonometry/reference/api/simulation/video/#write_elastic_fdtd_animation)) the unit of `ElasticRecording.snapshot_field`, pascals for `"p"` and metres per second for `"vx"` and `"vy"`. `None` (default) finds it in a first pass over the run. |

**Raises**

| Exception | When |
| :--- | :--- |
| TypeError | for a `size` that is not a pair or holds something other than numbers, or a `color_limit` that is not one number (a bool is not one). |
| ValueError | for a `language` other than `"en"` and `"es"`, a `size` of more or fewer than two sides, with a side that is not a whole number, or narrower than 479 or lower than 245 pixels, or a `color_limit` that is not a positive finite number. |

## write_elastic_fdtd_animation

```python
write_elastic_fdtd_animation(
    path: str | os.PathLike[str],
    run: ElasticRun,
    *,
    compute: Compute | None = None,
    frame: AnimationFrame | None = None,
    video: VideoOptions | None = None,
) -> ElasticFDTDResult
```

Step an elastic FDTD run and write one of its fields to a video.

The run is the one [`elastic_fdtd_simulation`](/phonometry/reference/api/simulation/elastic-fdtd/#elastic_fdtd_simulation)
steps, checked when the [`ElasticRun`](/phonometry/reference/api/simulation/elastic-fdtd/#elasticrun) was
built; a frame or video record of another type, a path whose container
rules out the options, an option ffmpeg could not honour, or a missing
ffmpeg is refused before the first step. The video draws the field
`run.recording.snapshot_field` names at the cell centres (the
synthetic pressure, or one velocity component), one frame at t = 0 and
one every `run.recording.snapshot_every` steps, as the snapshot plot
of [`elastic_fdtd_simulation`](/phonometry/reference/api/simulation/elastic-fdtd/#elastic_fdtd_simulation)'s result draws
it, laid out once for the whole run. See the module
documentation for how the frame is laid out and the colour scale fixed.

**Parameters**

| Name | Description |
| :--- | :--- |
| `path` | Where to write the video; `.webm`, `.mp4` or `.gif`. |
| `run` | The run ([`ElasticRun`](/phonometry/reference/api/simulation/elastic-fdtd/#elasticrun)). Its recording's `snapshot_every` is required and is the frame cadence, its `snapshot_field` the field drawn, its `snapshot_decimation` the cells a frame keeps, and its probes are recorded in the result. |
| `compute` | Where the run steps ([`Compute`](/phonometry/reference/api/simulation/compute/#compute)); `None` follows [`use`](/phonometry/reference/api/simulation/compute/#use), then `PHONOMETRY_COMPUTE`, then NumPy; with a `host` the run is computed, drawn and encoded on that node, named in the hosts file (see the guide on remote nodes), and only the result and the video's bytes come back. |
| `frame` | How each frame is drawn ([`AnimationFrame`](/phonometry/reference/api/simulation/video/#animationframe)); `None` (default) is `AnimationFrame()`: 960 by 540 pixels, English labels and a colour limit found in a first pass. Its `color_limit` is in the unit of the field drawn: pascals for `"p"`, metres per second for `"vx"` and `"vy"`. |
| `video` | How the video is encoded ([`phonometry.io.VideoOptions`](/phonometry/reference/api/io/io/#videooptions)); `None` (default) is `VideoOptions()`, which plays at 30 frames per second unless its `fps` says otherwise. |

**Returns:** The run's [`ElasticFDTDResult`](/phonometry/reference/api/simulation/elastic-fdtd/#elasticfdtdresult), with its probes and times and no snapshots.

**Raises**

| Exception | When |
| :--- | :--- |
| TypeError | If `run` is not an [`ElasticRun`](/phonometry/reference/api/simulation/elastic-fdtd/#elasticrun), `frame` not an [`AnimationFrame`](/phonometry/reference/api/simulation/video/#animationframe), `video` not a [`VideoOptions`](/phonometry/reference/api/io/io/#videooptions), `compute` not a [`Compute`](/phonometry/reference/api/simulation/compute/#compute), or `path` neither a text nor a path; or, when `compute` names a host, a part of the run that cannot travel to a node: an [`ExplosionSource`](/phonometry/reference/api/simulation/elastic-fdtd/#explosionsource) or a [`ForceSource`](/phonometry/reference/api/simulation/elastic-fdtd/#forcesource) whose waveform is a callable other than the `value` of a [`GaussianPulse`](/phonometry/reference/api/simulation/fdtd/#gaussianpulse), [`CWSource`](/phonometry/reference/api/simulation/fdtd/#cwsource) or [`SignalSource`](/phonometry/reference/api/simulation/fdtd/#signalsource). |
| ValueError | If the run records no snapshots (`run.recording` is `None`, or its `snapshot_every` is), the frame is narrower than the title of the run's last frame needs (a run whose last frame comes at ten seconds or later; the message gives the width), the path's suffix is not one of the three, the path names a directory, or its container rules out the options, `PHONOMETRY_COMPUTE` is malformed, there is nothing to find the colour scale by (the message asks for `AnimationFrame(color_limit=...)`), or the hosts file is malformed. |
| FileNotFoundError | If the directory of `path` does not exist or cannot be reached (it sits inside a directory this process cannot search); before any step, and before ssh starts. |
| FFmpegNotFoundError | For a video written here (no `host`, or a node that failed with `fallback=True`), if ffmpeg is not found, or on Windows is found only in the working directory; before any step. |
| VideoEncoderError | If no encoder can write the video, a raw `ffmpeg_encoder` is not in this ffmpeg (both before any step), or the directory of `path` does not take a file (before any step, and before ssh starts; the message names `path`); if ffmpeg cannot be started or fails while writing it (the message names the encoder and quotes ffmpeg; `ffmpeg_options` it refuses fail at the first frames), this machine's disk does not take the bytes of a node's video as they arrive (it is full, say), or the finished video cannot take the place of `path` (the message says where it was left). |
| ComputeImportError | When the device's library is not installed or does not import. |
| ComputeDeviceError | When the device is not present or not usable; with `fallback=True` the run warns once with [`ComputeFallbackWarning`](/phonometry/reference/api/simulation/compute/#computefallbackwarning) and steps on NumPy instead. |
| KeyError | For a `host` the hosts file does not name. |
| ComputeRemoteError | For a failure of the connection or of the node (one without matplotlib or the font every frame is drawn in, without ffmpeg, without an encoder that writes this video or the raw `ffmpeg_encoder`, or whose ffmpeg refuses the `ffmpeg_options`), or video bytes back that are more than the frames can take, too few to be a video, or not the container `path` names; with `fallback=True` the run warns once with [`ComputeFallbackWarning`](/phonometry/reference/api/simulation/compute/#computefallbackwarning) and writes the video here on NumPy instead. |
| ImportError | If matplotlib is not installed, for a video written here. |

## write_fdtd_animation

```python
write_fdtd_animation(
    path: str | os.PathLike[str],
    run: FDTDRun,
    *,
    compute: Compute | None = None,
    frame: AnimationFrame | None = None,
    video: VideoOptions | None = None,
) -> FDTDResult
```

Step an acoustic FDTD run and write its pressure field to a video.

The run is the one [`fdtd_simulation`](/phonometry/reference/api/simulation/fdtd/#fdtd_simulation) steps,
checked when the [`FDTDRun`](/phonometry/reference/api/simulation/fdtd/#fdtdrun) was built. A
frame or video record of another type, a path whose container rules out
the options, an option ffmpeg could not honour (an encoder that does not
run here, a raw encoder this ffmpeg lacks), or a missing ffmpeg is
refused before the first step. One frame is drawn at t = 0 and one every
`run.recording.snapshot_every` steps; the video shows what the
snapshot plot of [`fdtd_simulation`](/phonometry/reference/api/simulation/fdtd/#fdtd_simulation)'s result
shows, laid out once for the whole run and updated in place, under
matplotlib's default style. See the module documentation for how
the frame is laid out and the colour scale fixed.

**Parameters**

| Name | Description |
| :--- | :--- |
| `path` | Where to write the video; `.webm`, `.mp4` or `.gif`, as [`phonometry.io.write_video`](/phonometry/reference/api/io/io/#write_video) writes them. |
| `run` | The run ([`FDTDRun`](/phonometry/reference/api/simulation/fdtd/#fdtdrun)). Its recording's `snapshot_every` is required and is the frame cadence, its `snapshot_decimation` the cells a frame keeps, and its probes are recorded in the result. |
| `compute` | Where the run steps ([`Compute`](/phonometry/reference/api/simulation/compute/#compute)); `None` follows [`use`](/phonometry/reference/api/simulation/compute/#use), then `PHONOMETRY_COMPUTE`, then NumPy; with a `host` the run is computed, drawn and encoded on that node, named in the hosts file (see the guide on remote nodes), and only the result and the video's bytes come back. |
| `frame` | How each frame is drawn ([`AnimationFrame`](/phonometry/reference/api/simulation/video/#animationframe)); `None` (default) is `AnimationFrame()`: 960 by 540 pixels, English labels and a colour limit, in pascals, found in a first pass. |
| `video` | How the video is encoded ([`phonometry.io.VideoOptions`](/phonometry/reference/api/io/io/#videooptions)); `None` (default) is `VideoOptions()`, which plays at 30 frames per second unless its `fps` says otherwise. |

**Returns:** The run's [`FDTDResult`](/phonometry/reference/api/simulation/fdtd/#fdtdresult), with its probes and times and no snapshots.

**Raises**

| Exception | When |
| :--- | :--- |
| TypeError | If `run` is not an [`FDTDRun`](/phonometry/reference/api/simulation/fdtd/#fdtdrun), `frame` not an [`AnimationFrame`](/phonometry/reference/api/simulation/video/#animationframe), `video` not a [`VideoOptions`](/phonometry/reference/api/io/io/#videooptions), `compute` not a [`Compute`](/phonometry/reference/api/simulation/compute/#compute), or `path` neither a text nor a path; or, when `compute` names a host, a part of the run that cannot travel to a node: a waveform other than the `value` of a [`GaussianPulse`](/phonometry/reference/api/simulation/fdtd/#gaussianpulse), [`CWSource`](/phonometry/reference/api/simulation/fdtd/#cwsource) or [`SignalSource`](/phonometry/reference/api/simulation/fdtd/#signalsource). |
| ValueError | If the run records no snapshots (`run.recording` is `None`, or its `snapshot_every` is), the frame is narrower than the title of the run's last frame needs (a run whose last frame comes at ten seconds or later; the message gives the width), the path's suffix is not one of the three, the path names a directory, or its container rules out the options, `PHONOMETRY_COMPUTE` is malformed, there is nothing to find the colour scale by (the message asks for `AnimationFrame(color_limit=...)`), or the hosts file is malformed. |
| FileNotFoundError | If the directory of `path` does not exist or cannot be reached (it sits inside a directory this process cannot search); before any step, and before ssh starts. |
| FFmpegNotFoundError | For a video written here (no `host`, or a node that failed with `fallback=True`), if ffmpeg is not found, or on Windows is found only in the working directory; before any step. |
| VideoEncoderError | If no encoder can write the video, a raw `ffmpeg_encoder` is not in this ffmpeg (both before any step), or the directory of `path` does not take a file (before any step, and before ssh starts; the message names `path`); if ffmpeg cannot be started or fails while writing it (the message names the encoder and quotes ffmpeg; `ffmpeg_options` it refuses fail at the first frames), this machine's disk does not take the bytes of a node's video as they arrive (it is full, say), or the finished video cannot take the place of `path` (the message says where it was left). |
| ComputeImportError | When the device's library is not installed or does not import. |
| ComputeDeviceError | When the device is not present or not usable; with `fallback=True` the run warns once with [`ComputeFallbackWarning`](/phonometry/reference/api/simulation/compute/#computefallbackwarning) and steps on NumPy instead. |
| KeyError | For a `host` the hosts file does not name. |
| ComputeRemoteError | For a failure of the connection or of the node (one without matplotlib or the font every frame is drawn in, without ffmpeg, without an encoder that writes this video or the raw `ffmpeg_encoder`, or whose ffmpeg refuses the `ffmpeg_options`), or video bytes back that are more than the frames can take, too few to be a video, or not the container `path` names; with `fallback=True` the run warns once with [`ComputeFallbackWarning`](/phonometry/reference/api/simulation/compute/#computefallbackwarning) and writes the video here on NumPy instead. |
| ImportError | If matplotlib is not installed, for a video written here. |
