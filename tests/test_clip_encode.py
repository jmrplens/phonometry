#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A clip is AV1 in WebM, written by the encoder the render names.

The encoder settings are the clip's own (``figures/media.py``); the encode is
``phonometry.io.write_video``'s. The last test writes a three-frame clip
through the real path and reads it back with ffprobe, where an ffmpeg with
SVT-AV1 4.x is installed.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

pytest.importorskip("matplotlib")
import matplotlib as mpl

mpl.use("Agg")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from figures import media

pytestmark = pytest.mark.pinned_stack


def test_the_cpu_encoder_is_the_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(media.CLIP_ENCODER_ENV, raising=False)
    assert media._clip_encoder() == "libsvtav1"


def test_the_encoder_comes_from_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(media.CLIP_ENCODER_ENV, "av1_nvenc")
    assert media._clip_encoder() == "av1_nvenc"


def test_an_encoder_that_is_not_a_clip_encoder_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(media.CLIP_ENCODER_ENV, "libvpx-vp9")
    with pytest.raises(ValueError, match=r"PHONOMETRY_CLIP_ENCODER"):
        media._clip_encoder()
