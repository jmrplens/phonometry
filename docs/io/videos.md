← [Documentation index](../README.md)

# Writing animations and FDTD runs to video

`io.write_video` writes any matplotlib animation to a video file: a WebM or
an MP4 for a web page or a talk, or a GIF for a place where a video will not
play. The animation is any `matplotlib.animation.Animation`, a
`FuncAnimation` or an `ArtistAnimation` you built. Each frame is drawn with
Agg and piped straight into ffmpeg, which encodes a WebM or an MP4 on a GPU
encoder when one works on this machine and on the CPU when none does, and a
GIF on the CPU. `simulation.write_fdtd_animation` and
`simulation.write_elastic_fdtd_animation` write an acoustic or elastic FDTD
run straight to a video as it is computed, here or on a node, without storing
its snapshots (sections 4 and 5).

ffmpeg is a program, not a Python package, so it is installed apart from
phonometry: `conda install ffmpeg`, `apt install ffmpeg`,
`brew install ffmpeg` or `winget install ffmpeg`. phonometry runs the ffmpeg
matplotlib would run, the one `rcParams["animation.ffmpeg_path"]` names
(`"ffmpeg"`, looked up on `PATH`, unless you set it), and raises
`io.FFmpegNotFoundError` with those install commands when it is not there.
On Windows, which looks for a program in the working directory before
`PATH`, an ffmpeg found only there is refused: put it on `PATH`, or name it
by its full path in that rcParam. In Pyodide, which cannot start a program,
`write_video` raises the same error. matplotlib itself comes with
`pip install "phonometry[plot]"`.

## 1. Any animation: `io.write_video`

`write_video(path, anim, *, video=None)` takes the file to write, the
animation, and how to encode it (section 2). With no `video`, the first
encoder that works here writes the file (section 2 says in which order they
are tried), at the standard quality and at the animation's own frame rate:

```python
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.figure import Figure

from phonometry import io

fig = Figure(figsize=(3.2, 2.4), dpi=100)
ax = fig.add_subplot()
x = np.linspace(0.0, 2.0 * np.pi, 200)
(line,) = ax.plot(x, np.sin(x))


def update(k):
    line.set_ydata(np.sin(x - 0.2 * k))
    return (line,)


animation = FuncAnimation(fig, update, frames=30, interval=50)
io.write_video("wave.webm", animation)
io.write_video("wave.gif", animation, video=io.VideoOptions(quality="small"))
```

The suffix of the path is the container:

| Suffix | Holds, best first | Notes |
|---|---|---|
| `.webm` | AV1, VP9 | |
| `.mp4` | AV1, HEVC, H.264 | written to start playing before it has downloaded; HEVC is tagged so that Apple's players open it |
| `.gif` | a palette of up to 256 colours | written on the CPU only, with no codec to choose |

Any other suffix, or a path that names a directory, raises `ValueError`, and
a path whose directory does not exist raises `FileNotFoundError`, before
anything runs.

The file appears at the path only once ffmpeg has finished it. Until then
ffmpeg writes to a hidden file beside it, under a name of its own for each
write, and that file is removed whatever stops the encode: ffmpeg fails, the
disk fills, or your update function raises, which reaches you as its own
exception. So a failure leaves what was at the path before, a good video
included. A hidden file the system will not let go, as one a scanner holds
open on Windows, stays where it is, and what reaches you is still what
stopped the encode. A finished video that Windows will not let take the
old file's place, because a player holds the old file open, is not thrown
away: it is left beside it under its hidden name, and the
`io.VideoEncoderError` says where.

Each frame is the whole figure at its own size and in its own colours,
whatever your matplotlib settings say about saving figures: a `"tight"`
bounding box, which can change the size from one frame to the next, is set
aside for the write, and a transparent background is laid on white, since
these videos carry no transparency. In a WebM or an MP4, a figure whose
size in pixels is odd gets one more row or column of its own background
colour, because the pixel format browsers play needs even sides. A figure
that your update function resizes is held at the size it had when the write
began.

Python holds one frame at a time: each is drawn, sent through the pipe and
dropped, and no frame is written to disk. A GIF is the exception inside
ffmpeg. Its palette is computed from every frame in the same run of ffmpeg,
which keeps all of them until the last has arrived, so a long GIF at a large
size takes that much memory in ffmpeg. A long run is better written to WebM
or MP4.

## 2. How it is encoded: `io.VideoOptions`

One record says how a video is encoded, and it checks its fields when it is
built, so a misspelled encoder, or a raw encoder beside a codec of your own,
is refused before a frame is drawn. Build it once and pass the same record
to every video you write.

| Field | Values | Default |
|---|---|---|
| `encoder` | `"auto"`, `"cpu"`, `"nvenc"`, `"qsv"`, `"vaapi"`, `"videotoolbox"` | `"auto"` |
| `codec` | `"av1"`, `"vp9"`, `"hevc"`, `"h264"`, or `None` | `None`: the best the container holds that the encoder writes |
| `quality` | `"high"`, `"standard"`, `"small"` | `"standard"` |
| `fps` | frames per second, a positive number, or `None` | `None`: the animation's `interval` |
| `ffmpeg_encoder` | an ffmpeg encoder name, or `None` | `None` |
| `ffmpeg_options` | more ffmpeg output options, as separate texts | `()` |

Building the record raises `ValueError` (`TypeError` for a value of the
wrong type) for a choice outside its options, an `fps` that is not a
positive finite number, an `ffmpeg_encoder` together with an `encoder` or a
`codec` of your own, and a `codec` that the kind of encoder you named does
not write, such as `encoder="videotoolbox", codec="av1"`: VideoToolbox
writes HEVC and H.264 only. What depends on the file is checked when
`write_video` has the path, still before ffmpeg runs: the suffix, the
directory, a codec the container does not hold (VP9 in an `.mp4`), an
encoder that writes none of the codecs it holds (VideoToolbox in a
`.webm`), and for a GIF any codec, any raw encoder, and any encoder other
than `"auto"` or `"cpu"`.

```python
try:
    io.write_video("wave.mp4", animation, video=io.VideoOptions(codec="vp9"))
except ValueError as error:
    print(error)   # .mp4 holds av1, hevc, h264; got codec='vp9'
```

**Which encoder.** With `encoder="auto"`, the default, the kinds of encoder
are tried in this order: NVENC on an NVIDIA GPU, Quick Sync on an Intel
one, VAAPI on Linux (through `/dev/dri/renderD128`), VideoToolbox on a Mac,
and then the CPU. Within each kind the container's codecs are tried best
first, in the order of the table in section 1, so in an `.mp4` an NVENC
HEVC comes before a CPU AV1. On the CPU, AV1 is SVT-AV1 and never libaom.
Without SVT-AV1, a `.webm` gets VP9 from libvpx, and an `.mp4` HEVC from
x265, or H.264 from x264. A GIF has no encoder to choose: ffmpeg's palette
filter writes it on the CPU, with no trial.

An encoder is a candidate when this ffmpeg was built with it
(`ffmpeg -encoders` lists it), and that list says nothing about the
hardware: most Linux builds list NVENC whether or not the machine has an
NVIDIA GPU. So before the video starts, each candidate in turn encodes one
black frame of the video's size, a real encode, and the first that succeeds
writes the video. A success is remembered for the rest of the process, for
that ffmpeg, encoder and frame size, and is not tried again; a failure is
not remembered, since a GPU encoder that was busy a moment ago may work
now.

`encoder=` names one kind, and only that kind is tried: when it cannot
write the video, `io.VideoEncoderError` says so and lists the encoders that
can write it here. `codec=` names the codec, and nothing falls back to
another one: a `codec="av1"` that no encoder here can write raises
`io.VideoEncoderError` rather than write VP9.

The encoder that was chosen is logged at `INFO` on the `phonometry.io`
logger, which is silent unless you turn it on:

```python
import logging

logging.basicConfig()
logging.getLogger("phonometry.io").setLevel(logging.INFO)
h264 = io.VideoOptions(encoder="cpu", codec="h264")
io.write_video("wave.mp4", animation, video=h264)
```

Here it prints `INFO:phonometry.io:writing mp4 with libx264 (cpu, h264)`.
On a machine with an NVIDIA GPU and an ffmpeg built with NVENC, a call can
ask for the GPU by name:

```py
io.write_video("wave.webm", animation, video=io.VideoOptions(encoder="nvenc", codec="av1"))
```

NVENC, Quick Sync, VAAPI and VideoToolbox are tried and used, but they are
not tested in CI, which writes its videos on the CPU.

## 3. Quality, frame rate and raw ffmpeg

`quality=` takes one of three presets, `"high"`, `"standard"` (the default)
or `"small"`. On each encoder a preset sets that encoder's own
constant-quality option, on that encoder's own scale; for a GIF it sets the
size of the palette and the dither. `fps=` sets the frame rate in frames
per second; left at `None`, it is taken from the animation's `interval`,
the milliseconds between frames, as `Animation.save` takes it.

`ffmpeg_options=` adds ffmpeg output options, as separate texts, written
after the encoder's preset and pixel format, so an option you repeat wins
over them. The container's own options come after yours and stay: an MP4's
start before it has downloaded, the tag of an HEVC, and a GIF's endless
loop. `ffmpeg_encoder=` names an ffmpeg encoder to use as it is:

```python
raw = io.VideoOptions(
    ffmpeg_encoder="libvpx-vp9",
    ffmpeg_options=("-b:v", "0", "-crf", "40", "-pix_fmt", "yuv420p"),
)
io.write_video("wave_raw.webm", animation, video=raw)
```

A raw encoder name bypasses the trial, the preset, the container check and
the pixel format, so they are yours to get right: here VP9, which a `.webm`
holds, and `yuv420p`, which browsers play. Two things stay: the padding of
an odd size, and in an MP4 the layout that lets it start playing before it
has downloaded. An encoder this ffmpeg lacks, or an option it refuses,
fails in ffmpeg within the first frames, and the `io.VideoEncoderError`
names the encoder and carries the last lines ffmpeg wrote. A raw encoder
takes no `encoder=` or `codec=` beside it, and no GIF.

The presets are starting points, not calibrated settings. phonometry uses
the ffmpeg it finds and pins none, and the same CRF gives a different size
and quality from one SVT-AV1 major release to the next. A setting you have
calibrated goes through `ffmpeg_options`, with the ffmpeg you calibrated it
on.

## 4. An FDTD run straight to a video

`simulation.write_fdtd_animation(path, run)` steps an acoustic FDTD run and
draws its pressure field into a video as the run computes it:

```python
from phonometry import io, simulation

run = simulation.FDTDRun(
    343.0, 0.01, 4e-3,
    shape=(80, 120),
    sources=[simulation.GaussianPulse(ix=40, iy=40, half_width_s=5e-5)],
    recording=simulation.FDTDRecording(probes=[(100, 40)], snapshot_every=8),
    boundaries="absorbing", absorbing_layer_cells=15,
)
res = simulation.write_fdtd_animation(
    "pulse.webm", run, frame=simulation.AnimationFrame(size=(480, 320))
)
print(res.snapshots is None, res.pressures.shape[0])
# True 1
```

The run is the `FDTDRun` that `fdtd_simulation` takes, checked when it is
built, the medium included, so the same run can be simulated, written to a
video, or both. Its recording sets the frames: `snapshot_every` is the number
of steps between two frames and is required, so a run that records no
snapshots raises `ValueError` naming `run.recording.snapshot_every`;
`snapshot_decimation` sets the cells a frame keeps; and the probes are
recorded in the result, over every step of the run. One frame is drawn at
t = 0 and one every `snapshot_every` steps, and none is stored: the result
comes back with its probes and times and with no snapshots, and however long
the run, this machine holds one frame at a time (a GIF apart, whose palette
ffmpeg computes from every frame, as section 1 says). Before the first step
ffmpeg is found and run, the encoder of a WebM or an MP4 is chosen by the
trial encode of section 2 at the frame's size, and a raw `ffmpeg_encoder` is
looked for in this ffmpeg's list, so a missing ffmpeg, an encoder that fails
its trial or a raw encoder this ffmpeg lacks costs no run.

How each frame is drawn is one record, `simulation.AnimationFrame`, which
checks its fields when it is built: `language`, the labels' language, `"en"`
or `"es"` for Spanish; `size`, the frame's width and height in pixels, 960 by
540 pixels unless it says otherwise; and `color_limit`, the colour scale
(below). How the video is encoded is the same `io.VideoOptions` as in
section 2, passed as `video=`, and the path's suffix is the container, as in
section 1. A simulation video plays at 30 frames per second unless the `fps`
of its `io.VideoOptions` says otherwise.

The frames show what `simulation.fdtd_simulation(run).plot(kind="snapshot")`
shows for the same run: the same field on the same colormap, symmetric about
zero, with the same marks and labels, the limit of the scale being the video's
own, fixed for the whole video, given or found as the next paragraph says.
The writer's own result holds no snapshots: its `.plot()` draws the probes, as
any result's does, and `.plot(kind="snapshot")` raises `ValueError`. The
frames are drawn under matplotlib's default style, whatever your settings say,
so a video written here and one written on a node look alike. A frame is laid
out once for the whole run, for the widest title it will show and the labels
of its axes and colour scale, so nothing moves from one frame to the next, and
every text keeps its own size. The smallest frame in which every text, at its
own size, stays clear of the frame's margin and the field still shows, with
every matplotlib version the library is tested with, is 479 by 245 pixels, and
a smaller `size` raises `ValueError` when the record is built. That floor
holds for a run whose last frame comes before ten seconds. A longer run writes
more digits in its title's time, in milliseconds, so its floor is wider: the
writer refuses a frame narrower than the run needs before the run starts, and
its message gives the width.

The colour scale is fixed for the whole video.
`AnimationFrame(color_limit=...)` gives it, in pascals, as the value at either
end of the scale, and the run steps once. Without it the run steps twice: a
first pass finds, on the device the run steps on, the largest magnitude the
field reaches outside the source cells, the injection lines of plane-wave
sources and the absorbing layer, where the field is what the source or the
sponge makes it rather than the wave the video shows, and the second pass
draws with that limit. That limit is set by the strongest cells that remain,
which around a point source are the cells right beside it, so the default
video of a point source can look faint once its wave spreads out: a smaller
`AnimationFrame(color_limit=...)` brightens it, any cell beyond the limit
taking the colour at the end of the scale. Only that one number comes to this
machine from the first pass, which stores nothing. When the sources, their
lines and the absorbing layer cover every cell a frame keeps, the writer
raises `ValueError` before a single step; when the field stays zero there for
the whole run, or is not finite, it raises it after the first pass, before the
video's first frame is encoded. Each message asks for
`AnimationFrame(color_limit=...)`.

`simulation.write_elastic_fdtd_animation(path, run)` does the same for the
`ElasticRun` that `elastic_fdtd_simulation` takes, and draws the field its
recording's `snapshot_field` names, the pressure `"p"` or a velocity
component, `"vx"` or `"vy"`, as the snapshot plot of that function's result
draws it. Here a vertical force on the free surface of a solid, drawn as its
vertical velocity:

```python
waveform = simulation.GaussianPulse(ix=0, iy=0, half_width_s=4e-5).value
rayleigh = simulation.ElasticRun(
    4000.0, 2300.0, 0.01, 5e-4,
    rho=2500.0, shape=(60, 160),
    sources=[
        simulation.ForceSource(ix=80, iy=0, direction="y", waveform=waveform)
    ],
    recording=simulation.ElasticRecording(snapshot_every=8, snapshot_field="vy"),
    boundaries=simulation.ElasticBoundaries(
        sides={"top": "free", "left": "absorbing",
               "right": "absorbing", "bottom": "absorbing"},
        absorbing_layer_cells=12,
    ),
)
res = simulation.write_elastic_fdtd_animation(
    "rayleigh.webm", rayleigh,
    frame=simulation.AnimationFrame(size=(640, 320), color_limit=5e-7),
    video=io.VideoOptions(quality="small"),
)
```

The elastic writer's `color_limit` is in the unit of the field drawn: pascals
for `"p"`, metres per second for `"vx"` and `"vy"`. Without one, its first
pass leaves out the cells the sources drive and the absorbing layer; a free
surface is not driven, and stays in.

Both writers take the `compute=` of the simulation functions, so a run can
step on a GPU, as [Where a simulation runs](../simulation/compute.md)
explains. Only the cells a frame keeps then come to this machine to be drawn,
one frame at a time. With `fallback=True` and no GPU there, the run warns once
and steps on NumPy, both passes included:

```py
res = simulation.write_fdtd_animation(
    "pulse.webm", run,
    compute=simulation.Compute(device="cupy", fallback=True),
)
```

## 5. On a node

With a `host` in its `compute=`, a writer sends the whole job to a node, a
machine named in your hosts file as
[Sending a simulation to a remote node](../simulation/remote-node.md)
explains; `nas` is the node of that guide's hosts file:

```py
nas = simulation.Compute(device="cupy", host="nas")
res = simulation.write_fdtd_animation("pulse.webm", run, compute=nas)
res = simulation.write_elastic_fdtd_animation(
    "rayleigh.webm", rayleigh, compute=nas,
    frame=simulation.AnimationFrame(size=(640, 320), color_limit=5e-7),
)
print(res.provenance.host)   # nas
```

The node computes the run, draws its frames under the same default style and
encodes the video with its own ffmpeg, which the node image carries and a
Python node needs on its `PATH`, beside matplotlib. Only the result and the
video's bytes come back, so this machine needs neither ffmpeg nor matplotlib
for it, unless a failed run comes back to it through `fallback=True`. The run,
the frame and the video options are checked here first, the path's container
against the options included, so a call refused here never starts ssh; the
node checks them again when it builds them anew. A node that has no
matplotlib, or not the font every frame is drawn in, no ffmpeg, or no encoder
that writes the video at its size refuses before its first step, and
`simulation.ComputeRemoteError` says why.

The node's bytes are checked before they reach the disk here. They are no more
than the frames can take: two bytes a pixel of every frame, its sides padded
to even, when the library's presets decide the encode, or eight when an
`ffmpeg_encoder` or `ffmpeg_options` of yours do, plus 1 MiB for the
container; a longer video is refused before a byte of it is read. They must
begin as a file of the path's container begins, or none of them is kept, and
an empty video is refused. They are written to disk as they arrive, into a
hidden file beside the path, so that ceiling bounds the disk, not the memory,
and the file takes the path's place only once the node's whole answer has been
read and checked. Whatever stops the run before that, the node, the connection
or an interrupt, the hidden file is removed and the path is left as it was. A
hidden file the system will not let go, as one a scanner holds open on
Windows, stays where it is, and the run fails, or falls back, as it would
without it. Each refusal is a `simulation.ComputeRemoteError`; with
`fallback=True` in the request it is a `simulation.ComputeFallbackWarning`
instead, and the video is written here, on NumPy.

`io.write_video` itself runs on this machine only: an animation drawn here is
encoded here, and only the two simulation writers go to a node.

NVENC was checked on the maintainer's GPU node: a run stepped there on CuPy
and written to an AV1 video by NVENC came back with probes equal, bit for bit,
to those of the same run on NumPy here. That is one check on one card, not a
promise for every GPU.

## What this guide covers

**Covered.** Writing any matplotlib animation to WebM (AV1, VP9), MP4 (AV1,
HEVC, H.264) or GIF through ffmpeg on this machine, with the options of one
record checked before anything runs; the encoder of a WebM or an MP4 chosen
by a real trial encode, GPU encoders first and the CPU last, SVT-AV1 before
VP9, x265 or x264, and a GIF written on the CPU; three quality presets and
raw ffmpeg options; and an acoustic or elastic FDTD run written straight to a
video, here or computed, drawn and encoded on a node, with the colour scale
given or found on the device, and the node's bytes checked before they are
written.

**Not covered.** Audio tracks, and encoding on another machine an animation
drawn on this one. Quick Sync, VAAPI and VideoToolbox are tried and used but
not tested in CI; NVENC is not tested in CI either, and was checked on the
maintainer's GPU node. A simulation video's frames are the snapshot plot
under matplotlib's default style, not a style or a figure of yours. The
quality presets are starting points, not calibrated settings: phonometry
uses the ffmpeg it finds, and the same CRF reads differently from one
SVT-AV1 major release to the next.

## See also

- [Where a simulation runs: NumPy, CuPy and torch](../simulation/compute.md):
  the devices the FDTD engines step on.
- [2D FDTD wave simulation](../simulation/fdtd-simulation.md): the
  acoustic engine and the field snapshots it records.
- [Elastic waves and fluid-solid coupling](../simulation/elastic-waves.md):
  the elastic engine and its snapshots.
- [Sending a simulation to a remote node](../simulation/remote-node.md):
  the hosts file that names a node, and how to set one up.
- [Reading and writing measurement audio](audio-files.md): the
  audio files `phonometry.io` reads and writes.
- API reference: [`phonometry.io`](https://docs.jmrp.io/phonometry/reference/api/io/io/),
  [`simulation.video`](https://docs.jmrp.io/phonometry/reference/api/simulation/video/).

## Quick answers

### Why did my video come out in VP9?

Because the first encoder that worked here writes VP9. In a `.webm`,
`"auto"` goes through the kinds of encoder in their order and tries AV1
before VP9 within each: a Quick Sync or VAAPI GPU that encodes VP9 but not
AV1 writes VP9 before the CPU is reached, and the CPU, which takes AV1 only
from SVT-AV1 and never from libaom, writes VP9 with libvpx when this ffmpeg
has no SVT-AV1. Turn on the `phonometry.io` logger (section 2) to see which
encoder wrote it. To get AV1, pass `codec="av1"`, which takes the first
encoder that writes AV1 here and raises `io.VideoEncoderError` rather than
write anything else; on the CPU that needs an ffmpeg that lists `libsvtav1`
in `ffmpeg -encoders`.

### Can I write a video without a GPU?

Yes. The CPU is the last kind of encoder `"auto"` tries, so on a machine
with no working GPU encoder every video is written there: SVT-AV1 or VP9 in
a `.webm`, SVT-AV1, x265 or x264 in an `.mp4`. A GIF is always written on
the CPU. Pass `encoder="cpu"` to skip the GPU trials altogether.

### Why does the simulation step twice?

Because no colour limit was given. The colour scale is fixed for the whole
video, so a first pass steps the run to find the largest magnitude the field
reaches outside the sources and the absorbing layer, and the second pass
draws the frames on that scale (section 4). Give the limit,
`frame=simulation.AnimationFrame(color_limit=...)`, in pascals or, for an
elastic run, in the unit of the field drawn, and the run steps once.

## References

- FFmpeg project. *FFmpeg codecs documentation*.
  [ffmpeg.org/ffmpeg-codecs.html](https://ffmpeg.org/ffmpeg-codecs.html).
  The encoders write_video chooses among and the constant-quality options
  each one takes.
- Alliance for Open Media. *SVT-AV1*.
  [gitlab.com/AOMediaCodec/SVT-AV1](https://gitlab.com/AOMediaCodec/SVT-AV1).
  The AV1 encoder write_video tries first on the CPU, before VP9 in a WebM
  and x265 or x264 in an MP4.
