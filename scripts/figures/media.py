#  Copyright (c) 2026. Jose Manuel Requena Plens
"""How an animation becomes files: the timeline, the encoders and the posters.

The clip builders in :mod:`figures.schematics` and :mod:`figures.fields` only
draw frames; this module decides how many there are and what they are written
to. It carries the two animation norms as constants (the 12 s schematic
timeline with its closing hold, the wider budget the wave-field clips size
themselves against), the AV1 settings of the two clip encoders, and
:func:`_save_animation`, which writes each clip in its four language x theme
variants as AV1 WebM (NVENC on a GPU, SVT-AV1 4 on a CPU, at the setting
calibrated on it) through ``phonometry.io.write_video``, extracts the
deferred-loading poster still and adds the English GIF for the GitHub docs.
"""

from __future__ import annotations

import functools
import os
import re
import subprocess
from typing import TYPE_CHECKING, Any

import animation_fingerprint
import clip_frame_audit
import encode_slots
import matplotlib.pyplot as plt

from phonometry import io as pm_io
from phonometry.io._video_encoders import find_ffmpeg

from .i18n import (
    _LANG,
    _LANG_SUFFIX,
    _translate_figure,
    audit_figure,
    lookup,
)
from .theme import _FILENAME_SUFFIX

if TYPE_CHECKING:
    from collections.abc import Callable

    from matplotlib.animation import FuncAnimation
    from matplotlib.figure import Figure

#: Names the ffmpeg encoder a render writes the WebM with, set from
#: ``generate_graphs.py --clip-encoder``, so the pool workers and the forked
#: variants of one render all read the same one.
CLIP_ENCODER_ENV = "PHONOMETRY_CLIP_ENCODER"


def _clip_encoder() -> animation_fingerprint.ClipEncoder:
    """The encoder this render writes its WebM with; SVT-AV1 unless told.

    :raises ValueError: for a name that is not one of the two clip encoders.
    """
    value = os.environ.get(CLIP_ENCODER_ENV, "libsvtav1")
    for encoder in animation_fingerprint.CLIP_ENCODERS:
        if value == encoder:
            return encoder
    msg = (
        f"{CLIP_ENCODER_ENV} must be one of "
        f"{', '.join(animation_fingerprint.CLIP_ENCODERS)}; got {value!r}"
    )
    raise ValueError(msg)


# ====================================================================# Animations (Tier 1 pilot)
# ---------------------------------------------------------------------------
# Deterministic FuncAnimation clips of the level-vs-time phenomena the library
# already computes. Each is rendered to WebM (site <video>) in all four
# language x theme variants, and to an animated GIF for the English GitHub
# docs (both themes). Every WebM also gets a JPEG poster frame (the held
# verdict state near the end of the clip) so the site can embed the video
# with ``preload="none"`` and still show a meaningful still while nothing is
# fetched. Posters are ``.jpg`` on purpose: `make graphs` clears only
# ``*.svg``/``*.png``/``*.webp`` and scripts/check_figures.py
# regenerates/compares only those, so the posters ride with the WebM/GIF
# outside the figure pipeline. Kept out of generate_all()/`make graphs` so
# ordinary figure regeneration stays fast; produced by `make animations` (or `make posters` to re-extract the
# stills from the committed WebMs without re-rendering).
# ====================================================================
_ANIM_FPS = 20
_ANIM_SECONDS = 12
_ANIM_FRAMES = _ANIM_FPS * _ANIM_SECONDS
# Closing hold appended to each schematic timeline: the settled verdict frame
# stays on screen ~2 s so it can be read before the loop restarts.
_ANIM_HOLD = 2 * _ANIM_FPS
# The wave-field clips run on their own frame budgets: on the shared 12 s
# timeline a wavefront advances several cells per frame and the field
# strobes. Each FDTD/elastic clip therefore sizes its own window from the
# two animation norms -- the captured span is 1.2 times the full round-trip
# flight (source to the deepest reflector, wells and cavities included, and
# on to the farthest visible point, at the slowest speed on the path) and
# the capture stride keeps at least 48 frames per period of the highest
# carrier -- and states that arithmetic next to its frame count. This 18 s
# value is the starting budget the older clips were sized against and the
# default for clips whose own note does not override it.
_FDTD_ANIM_FRAMES = 18 * _ANIM_FPS
_ANIM_FIGSIZE = (8.0, 4.5)  # inches at _ANIM_DPI -> 2400 x 1350 px
_ANIM_DPI = 300
# The GitHub-docs GIF is a compact fallback for the smooth site WebM: a lower
# frame rate, smaller frame and capped palette keep even the detail-dense
# clips (the p·u oscillations) near half a megabyte.
_GIF_FPS = 12
_GIF_SCALE = 640
_GIF_COLORS = 64
# Rounded box of the verdict/annotation pills drawn over the clips.
_ANIM_PILL_BOX = "round,pad=0.25"

#: AV1 NVENC's options for the clips, on an NVIDIA GPU: cq 44 was calibrated
#: against the VP9 crf-40 size on the metadiffuser clip (cq 42 = parity,
#: 46 = -22 %), at the same resolution. The quality table of ``io`` is not
#: used here; these raw options are what the clips' fingerprint covers.
_NVENC_OPTIONS = (
    "-b:v",
    "0",
    "-cq",
    "44",
    "-preset",
    "p6",
    "-pix_fmt",
    "yuv420p",
    "-an",
)

#: SVT-AV1's constant rate factor and preset for the clips, on a CPU, by the
#: major version of the SVT-AV1 library ffmpeg was built with. CRF and presets
#: change meaning from one major to the next, and the clips are calibrated on
#: one: SVT-AV1 4, the library in the ffmpeg build the node image pins
#: (docker/node/Dockerfile; make clip-ffmpeg fetches the same build here).
#: The row is the quality AV1 NVENC gives at cq 44 in a smaller file: on the
#: clip the NVENC setting above was calibrated on, drawn and never encoded
#: before, preset 6 at the highest CRF whose VMAF and SSIM are both at least
#: cq 44's (measured 2026-10-21 on SVT-AV1 4.2.0 in ffmpeg 9.0: CRF 51, VMAF
#: 96.27 and SSIM 0.99705 against 96.24 and 0.99646, a file 47 % smaller).
#: Another major gets a row only from the same measurement made on it.
_SVT_AV1_CALIBRATED: dict[int, tuple[int, int]] = {
    4: (51, 6),  # SVT-AV1 4.2.0, ffmpeg 9.0
}

#: How SVT-AV1 names itself when an encode starts.
_SVT_AV1_VERSION = re.compile(r"SVT-AV1 Encoder Lib v(\d+)\.(\d+)\.(\d+)")

#: How long the one-frame encode that reads SVT-AV1's version may take [s].
_SVT_AV1_PROBE_S = 120


def read_svt_av1_version(
    ffmpeg: str, *, run: Callable[..., Any] = subprocess.run
) -> str:
    """The SVT-AV1 library *ffmpeg* encodes with, as ``"4.2.0"``.

    SVT-AV1 names itself when an encode starts, so one black frame is encoded
    and its message read.

    :raises RuntimeError: when the encode names no version (no libsvtav1, or
        a build that does not say), with ffmpeg's last line, or when *ffmpeg*
        does not run or does not finish.
    """
    try:
        done = run(
            [
                ffmpeg,
                "-hide_banner",
                "-f",
                "lavfi",
                "-i",
                "color=c=black:s=64x64:d=0.04",
                "-frames:v",
                "1",
                "-c:v",
                "libsvtav1",
                "-f",
                "null",
                "-",
            ],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=_SVT_AV1_PROBE_S,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        msg = f"{ffmpeg} did not encode a frame with libsvtav1: {exc}"
        raise RuntimeError(msg) from exc
    match = _SVT_AV1_VERSION.search(done.stderr)
    if match is None:
        last = (done.stderr.strip().splitlines() or ["no message"])[-1]
        msg = f"ffmpeg's libsvtav1 named no SVT-AV1 version: {last}"
        raise RuntimeError(msg)
    return ".".join(match.groups())


@functools.cache
def _svt_av1_version(ffmpeg: str) -> str:
    """:func:`read_svt_av1_version` of *ffmpeg*, asked once per program and process.

    :raises RuntimeError: as :func:`read_svt_av1_version` does.
    """
    return read_svt_av1_version(ffmpeg)


def _svt_av1_options(version: str) -> tuple[str, ...]:
    """SVT-AV1's options for the clips, at the calibration of *version*'s major.

    :raises ValueError: for a major version the clips were not calibrated on.
    """
    major = int(version.split(".", 1)[0])
    if major not in _SVT_AV1_CALIBRATED:
        calibrated = ", ".join(
            f"SVT-AV1 {known}.x at preset {preset} CRF {crf}"
            for known, (crf, preset) in sorted(_SVT_AV1_CALIBRATED.items())
        )
        msg = (
            f"ffmpeg's SVT-AV1 is {version}; calibrated: {calibrated}, and no other "
            "major: encode with the ffmpeg build docker/node/Dockerfile pins (make "
            "clip-ffmpeg fetches it on Linux x86_64) or on a node"
        )
        raise ValueError(msg)
    crf, preset = _SVT_AV1_CALIBRATED[major]
    return ("-crf", str(crf), "-preset", str(preset), "-pix_fmt", "yuv420p", "-an")


def _clip_options(encoder: animation_fingerprint.ClipEncoder) -> tuple[str, ...]:
    """The ffmpeg options *encoder* writes a clip's WebM with: AV1 either way.

    The SVT-AV1 asked for its version is that of the ffmpeg
    ``phonometry.io.write_video`` runs, found the way it finds it (matplotlib's
    ``animation.ffmpeg_path`` on ``PATH``), so the setting is the one
    calibrated for the program that encodes.

    :raises ValueError: for an SVT-AV1 whose major version was not calibrated.
    :raises RuntimeError: when ffmpeg's SVT-AV1 does not say its version.
    :raises phonometry.io.FFmpegNotFoundError: when that ffmpeg is not found.
    """
    if encoder == "av1_nvenc":
        return _NVENC_OPTIONS
    return _svt_av1_options(_svt_av1_version(find_ffmpeg()))


def _translate_str(s: str) -> str:
    """Translate one label to the active language (exact + pattern + comma).

    Mirrors :func:`_translate_figure` for a single string, so animation labels
    -- which are rewritten every frame and never pass through ``save_figure``
    -- can be localised at creation time instead.
    """
    import re as _re

    if _LANG == "en" or not s:
        return s
    out = lookup(s)
    if "$" not in out and _re.search(r"\d\.\d", out):
        out = _re.sub(r"(?<![\d.A-Za-z])(\d+)\.(\d+)(?![.\d])", r"\1,\2", out)
    return out


def _anim_path(output_dir: str, stem: str, ext: str) -> str:
    """Animation output path with the active language + theme suffixes."""
    # The code that draws the clips is hashed into
    # scripts/animation_fingerprints.txt, so rewriting this asks for a
    # re-render that would draw the very same frames.
    return os.path.join(output_dir, f"{stem}{_LANG_SUFFIX}{_FILENAME_SUFFIX}.{ext}")  # noqa: PTH118


def _anim_figure() -> Figure:
    """A fixed-size themed figure for a clip (constant canvas across frames)."""
    return plt.figure(figsize=_ANIM_FIGSIZE, dpi=_ANIM_DPI, layout="constrained")


def _render_clip(
    fig: Figure,
    update: Callable[[int], tuple[Any, ...]],
    output_dir: str,
    stem: str,
    *,
    frames: int | None = None,
    fps: float | None = None,
    gif_fps: int | None = None,
    poster_ss: float | None = None,
    measure: Callable[[], None] | None = None,
) -> None:
    """Shared clip tail: drive *update* through FuncAnimation and encode.

    Static artists (tick labels included) get the same Spanish pass as the
    figures; per-frame labels are translated by ``_translate_str`` inside
    each clip's update function. ``frames``/``fps`` override the shared
    timeline for clips that need their own budget (the FDTD room modes);
    ``gif_fps`` is forwarded to the GitHub-GIF palette pass.

    ``measure`` runs after the figure is in its final language and before
    the first frame is built. A clip that fits a label against the geometry
    of its axes (``fields._core``) has to read the canvas the frames are
    drawn on, and the Spanish pass can still resize that canvas here: it
    swaps the tick formatters for versions that write a decimal comma and a
    typographic minus, and under constrained layout a tick label that
    changes width moves the axes it belongs to. Measuring from this hook
    reads the settled geometry. Whatever the callback measures must already
    be in its final text, sign included -- these helpers measure the box of
    a rendered string, so a number whose ASCII hyphen is swapped for U+2212
    after the fit was measured against a glyph that is not the one drawn.
    A clip that blanks a pre-translated label until its reveal frame blanks
    it inside this callback too, after the fit.

    Before a frame is encoded, every frame is drawn to SVG in a copy of this
    process and held to the gates the figures pass
    (``scripts/clip_frame_audit.py``). A render through the registry runs
    this twice, so the four variants of a clip are encoded all or none: the
    first pass inspects each and encodes nothing, the second encodes them
    once every one has passed. Called directly for one variant, a finding
    raises ``clip_frame_audit.ClipFrameError`` naming the clip, the variant,
    the frame and the finding, and that variant is not encoded. In an
    audit-only run (``generate_graphs.py --animations --audit-only``) the
    clip is inspected and not encoded at all. The ``FuncAnimation`` that
    encodes is made after the audit, so the copy's draws cannot reach it.
    """
    from matplotlib.animation import FuncAnimation

    audit_figure(stem)
    _translate_figure(fig)
    if measure is not None:
        measure()
    n_frames = _ANIM_FRAMES if frames is None else frames
    rate = _ANIM_FPS if fps is None else fps
    clip_frame_audit.audit(
        fig,
        update,
        stem,
        frames=n_frames,
        interval_ms=1000 / rate,
        language=_LANG,
        dark=bool(_FILENAME_SUFFIX),
    )
    if clip_frame_audit.audit_only():
        plt.close(fig)
        return
    anim = FuncAnimation(fig, update, frames=n_frames, interval=1000 / rate, blit=False)
    _save_animation(
        anim, fig, output_dir, stem, fps=rate, gif_fps=gif_fps, poster_ss=poster_ss
    )


#: WebP quality of the poster stills. Measured against the JPEG the pipeline
#: used to write (``-q:v 3``): 85 gives 46 per cent of its size at 44 to 48 dB
#: PSNR, which is past where a difference can be seen, and the frame is taken
#: from the WebM directly rather than through a JPEG, so nothing is encoded
#: twice.
POSTER_QUALITY = 85


def _extract_poster(webm: str, poster_ss: float | None = None) -> str:
    """Extract the deferred-loading poster still from a rendered WebM.

    The frame is grabbed half a second before the end of the clip, i.e.
    inside the closing hold, so the poster shows the settled verdict state.
    The output sits next to the WebM as ``<stem>_poster.webp``, in the
    assets repository with the clip, so it never meets the figure pipeline's
    deletion glob or its regeneration compare. A ``<stem>_poster.jpg`` left
    by the pipeline before it wrote WebP is removed, so a re-extraction does
    not leave two posters of one clip behind.
    """
    import subprocess
    from pathlib import Path

    stem = webm.removesuffix(".webm")
    poster = stem + "_poster.webp"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error"]
        + (["-ss", f"{poster_ss:.2f}"] if poster_ss is not None else ["-sseof", "-0.5"])
        + [
            "-i",
            webm,
            "-frames:v",
            "1",
            "-c:v",
            "libwebp",
            "-quality",
            str(POSTER_QUALITY),
        ]
        + ["-compression_level", "6", "-update", "1", poster],
        check=True,
    )
    Path(stem + "_poster.jpg").unlink(missing_ok=True)
    return poster


def _save_animation(
    anim: FuncAnimation,
    fig: Figure,
    output_dir: str,
    stem: str,
    *,
    make_gif: bool = True,
    fps: float | None = None,
    gif_fps: int | None = None,
    poster_ss: float | None = None,
) -> None:
    """Write *anim* to AV1 WebM (always), its poster still and, for English, a GIF.

    The WebM is AV1 (NVENC on a GPU, SVT-AV1 4 on a CPU, at the setting
    calibrated on it, :func:`_clip_options`) through
    ``phonometry.io.write_video``, by the encoder ``PHONOMETRY_CLIP_ENCODER``
    names (:func:`_clip_encoder`). The GIF is derived from the just-written
    WebM with an ffmpeg palette pass so the GitHub docs get a compact,
    self-contained loop; the site embeds the WebM directly. Every WebM
    variant also gets a ``_poster.webp`` still (see :func:`_extract_poster`)
    so the site ``<video>`` embeds can defer loading (``preload="none"``)
    behind a meaningful frame. ``fps`` overrides the shared WebM rate and
    ``gif_fps`` the GIF sampling rate (long clips drop GIF frames to stay
    within GitHub-friendly file sizes).

    :raises ValueError: for an encoder that is not a clip encoder, an SVT-AV1
        whose major version was not calibrated, or a malformed
        ``PHONOMETRY_ENCODE_SLOTS``.
    :raises RuntimeError: when ffmpeg's SVT-AV1 does not say its version.
    :raises phonometry.io.FFmpegNotFoundError: when ffmpeg is not on PATH.
    :raises phonometry.io.VideoEncoderError: when ffmpeg cannot write the WebM.
    :raises subprocess.CalledProcessError: when ffmpeg cannot cut the poster
        or the GIF from it.
    """
    webm = _anim_path(output_dir, stem, "webm")
    rate = _ANIM_FPS if fps is None else fps
    encoder = _clip_encoder()
    # write_video draws the figure at its own size and dpi (2400 x 1350 for a
    # clip), with its facecolor and the standard bbox, so every frame keeps
    # one canvas. A GPU encode waits for a free NVENC session on a node.
    with encode_slots.slot(encoder):
        pm_io.write_video(
            webm,
            anim,
            video=pm_io.VideoOptions(
                fps=float(rate),
                ffmpeg_encoder=encoder,
                ffmpeg_options=_clip_options(encoder),
            ),
        )
    _extract_poster(webm, poster_ss)
    made_gif = False
    if make_gif and _LANG == "en":
        gif = _anim_path(output_dir, stem, "gif")
        # The code that draws the clips is hashed into
        # scripts/animation_fingerprints.txt, so rewriting this asks for a
        # re-render that would draw the very same frames.
        palette = os.path.join(output_dir, f".{stem}{_FILENAME_SUFFIX}_pal.png")  # noqa: PTH118
        vf = (
            f"fps={_GIF_FPS if gif_fps is None else gif_fps},"
            f"scale={_GIF_SCALE}:-1:flags=lanczos"
        )
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                webm,
                "-vf",
                f"{vf},palettegen=max_colors={_GIF_COLORS}:stats_mode=diff",
                "-update",
                "1",
                palette,
            ],
            check=True,
        )
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                webm,
                "-i",
                palette,
                "-lavfi",
                f"{vf}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3",
                "-loop",
                "0",
                gif,
            ],
            check=True,
        )
        # The code that draws the clips is hashed into
        # scripts/animation_fingerprints.txt, so rewriting this asks for a
        # re-render that would draw the very same frames.
        os.remove(palette)  # noqa: PTH107
        made_gif = True
    plt.close(fig)
    theme = "dark" if _FILENAME_SUFFIX else "light"
    print(
        f"  {stem} [{_LANG} {theme}] -> webm + poster" + (" + gif" if made_gif else "")
    )
