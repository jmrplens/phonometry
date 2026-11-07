#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The quality presets of :func:`phonometry.io.write_video` (private).

``quality="high"``, ``"standard"`` and ``"small"`` name a constant-quality
setting on every encoder the writer can choose, and a palette size and a
dither for a GIF. Each row is set on that encoder's own scale (a CRF of 32
on libvpx-vp9 is not a CRF of 32 on libx264) for screen-like content: flat
fields, thin lines, text. They are starting points, not measurements, and
the guide does not print them. Quick Sync, VAAPI and VideoToolbox are not
exercised in CI: their rows follow those encoders' documentation and have
not met their hardware here.

No row is calibrated on an SVT-AV1 release. The writer runs whatever ffmpeg
it finds and pins none, and SVT-AV1's CRF scale differs between major
releases, so the ``libsvtav1`` rows give another size and quality with the
SVT-AV1 of another major. A caller who needs a calibrated setting passes it
through ``ffmpeg_options``, with the ffmpeg it was calibrated on.

The encoder table lives in a module of its own so that the clips'
fingerprint walk can leave it out (``scripts/animation_fingerprint.py``):
the documentation clips pass their own encoder and options, so these
presets never reach their encode, and editing one must not call every clip
stale. The GIF palette stays inside the walk, because a GIF written with a
``quality`` reads it.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING, Final, Literal

if TYPE_CHECKING:
    from collections.abc import Mapping

#: How hard the encoder compresses: a closed choice of three.
Quality = Literal["high", "standard", "small"]

_SVT = ("-preset", "8")
_VPX = ("-b:v", "0", "-row-mt", "1", "-deadline", "good", "-cpu-used", "4")
_X264 = ("-preset", "medium")
_X265 = ("-preset", "medium", "-x265-params", "log-level=error")
_NVENC = ("-preset", "p6", "-rc", "vbr", "-b:v", "0")
_VAAPI = ("-rc_mode", "CQP")


def _rows(
    name: str, flag: str, values: tuple[str, str, str], extra: tuple[str, ...]
) -> dict[tuple[str, Quality], tuple[str, ...]]:
    """The three presets of one encoder: *flag* set to each of *values*."""
    high, standard, small = values
    return {
        (name, "high"): (flag, high, *extra),
        (name, "standard"): (flag, standard, *extra),
        (name, "small"): (flag, small, *extra),
    }


#: ffmpeg options per (encoder name, quality), written after ``-c:v <name>``.
ENCODER_QUALITY: Final[Mapping[tuple[str, Quality], tuple[str, ...]]] = (
    MappingProxyType(
        {
            **_rows("libsvtav1", "-crf", ("28", "35", "45"), _SVT),
            **_rows("libvpx-vp9", "-crf", ("24", "32", "40"), _VPX),
            **_rows("libx264", "-crf", ("18", "23", "28"), _X264),
            **_rows("libx265", "-crf", ("20", "26", "32"), _X265),
            **_rows("av1_nvenc", "-cq", ("30", "38", "46"), _NVENC),
            **_rows("hevc_nvenc", "-cq", ("22", "28", "34"), _NVENC),
            **_rows("h264_nvenc", "-cq", ("20", "25", "30"), _NVENC),
            **_rows("av1_qsv", "-global_quality", ("90", "120", "160"), ()),
            **_rows("vp9_qsv", "-global_quality", ("90", "120", "160"), ()),
            **_rows("hevc_qsv", "-global_quality", ("22", "28", "34"), ()),
            **_rows("h264_qsv", "-global_quality", ("20", "25", "30"), ()),
            # VAAPI's AV1 and VP9 encoders have no -qp: in CQP mode they read
            # global_quality, on their 0-255 q-index scale.
            **_rows("av1_vaapi", "-global_quality", ("90", "120", "160"), _VAAPI),
            **_rows("vp9_vaapi", "-global_quality", ("90", "120", "160"), _VAAPI),
            **_rows("hevc_vaapi", "-qp", ("22", "28", "34"), _VAAPI),
            **_rows("h264_vaapi", "-qp", ("20", "25", "30"), _VAAPI),
            **_rows("hevc_videotoolbox", "-q:v", ("75", "60", "45"), ()),
            **_rows("h264_videotoolbox", "-q:v", ("75", "60", "45"), ()),
        }
    )
)

#: A GIF's palette size and ``paletteuse`` dither per quality.
GIF_PALETTE: Final[Mapping[Quality, tuple[int, str]]] = MappingProxyType(
    {
        "high": (256, "sierra2_4a"),
        "standard": (128, "bayer:bayer_scale=3"),
        "small": (64, "bayer:bayer_scale=3"),
    }
)
