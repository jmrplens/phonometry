#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A clip is AV1 in WebM, written by the encoder the render names.

The encoder settings are the clip's own (``figures/media.py``); the encode is
``phonometry.io.write_video``'s. The last test writes a three-frame clip
through the real path and reads it back with ffprobe, where an ffmpeg with
SVT-AV1 4.x is installed.
"""

from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

pytest.importorskip("matplotlib")
import matplotlib as mpl

mpl.use("Agg")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from figures import media

if TYPE_CHECKING:
    from matplotlib.lines import Line2D

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


def test_nvenc_keeps_the_calibrated_constant_quality() -> None:
    options = media._clip_options("av1_nvenc")
    assert options[options.index("-cq") + 1] == "44"
    assert options[options.index("-preset") + 1] == "p6"


def test_the_svt_av1_setting_is_the_one_calibrated_on_svt_av1_4() -> None:
    """NVENC cq 44's quality in a smaller file: preset 6 at CRF 51, on SVT-AV1 4.x only."""
    assert media._SVT_AV1_CALIBRATED == {4: (51, 6)}
    options = media._svt_av1_options("4.2.0")
    assert options[options.index("-crf") + 1] == "51"
    assert options[options.index("-preset") + 1] == "6"


@pytest.mark.parametrize("version", ["1.7.0", "2.3.0", "99.0.0"])
def test_an_svt_av1_major_that_was_not_calibrated_is_refused(version: str) -> None:
    """Ubuntu 24.04's ffmpeg 6.1, Debian 13's 7.1.5, and a major still to come."""
    calibrated = r"calibrated: SVT-AV1 4\.x at preset 6 CRF 51"
    with pytest.raises(
        ValueError, match=rf"SVT-AV1 is {re.escape(version)}; {calibrated}"
    ):
        media._svt_av1_options(version)


def test_the_svt_av1_version_is_read_from_its_own_message() -> None:
    """As the pinned build names its library: a release and the commits after it."""

    def run(argv: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        assert "libsvtav1" in argv
        message = (
            "Svt[info]: SVT [version]:\tSVT-AV1 Encoder Lib v4.2.0-151-g5ed9ffbcb\n"
        )
        return subprocess.CompletedProcess(argv, 0, "", message)

    assert media.read_svt_av1_version("ffmpeg", run=run) == "4.2.0"


def test_the_svt_av1_asked_is_that_of_the_ffmpeg_that_encodes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """write_video runs the ffmpeg matplotlib's ``animation.ffmpeg_path`` names, so the probe asks that one.

    Any program stands in for it here: the probe that would run it is
    replaced, and only the program it is handed is looked at.
    """
    asked: list[str] = []

    def read(ffmpeg: str, **_: object) -> str:
        asked.append(ffmpeg)
        return "4.2.0"

    monkeypatch.setattr(media, "read_svt_av1_version", read)
    media._svt_av1_version.cache_clear()
    try:
        with mpl.rc_context({"animation.ffmpeg_path": sys.executable}):
            options = media._clip_options("libsvtav1")
    finally:
        media._svt_av1_version.cache_clear()
    assert asked == [shutil.which(sys.executable)]
    assert options[options.index("-crf") + 1] == "51"


def test_an_svt_av1_that_names_no_version_is_refused() -> None:
    def run(argv: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 1, "", "Unknown encoder 'libsvtav1'\n")

    with pytest.raises(RuntimeError, match=r"Unknown encoder"):
        media.read_svt_av1_version("ffmpeg", run=run)


def _can_write_a_clip() -> bool:
    """SVT-AV1 4.x to encode, a software AV1 decoder and WebP for the poster, and ffprobe.

    ffmpeg's own ``av1`` decoder decodes only through a hardware accelerator,
    so it does not count. An SVT-AV1 of another major would be refused, so
    such an ffmpeg skips the test rather than failing it.
    """
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None or shutil.which("ffprobe") is None:
        return False
    encoders, decoders = (
        subprocess.run(
            [ffmpeg, "-hide_banner", flag],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        ).stdout
        for flag in ("-encoders", "-decoders")
    )
    if not (
        "libsvtav1" in encoders
        and "libwebp" in encoders
        and ("libdav1d" in decoders or "libaom-av1" in decoders)
    ):
        return False
    try:
        media._svt_av1_options(media.read_svt_av1_version(ffmpeg))
    except (ValueError, RuntimeError):
        return False
    return True


@pytest.mark.skipif(
    not _can_write_a_clip(),
    reason=(
        "needs ffmpeg with libsvtav1 4.x, libwebp and libdav1d or libaom-av1, and ffprobe: "
        'PATH="$(make -s clip-ffmpeg):$PATH" puts the pinned build first'
    ),
)
def test_a_clip_is_written_as_av1_webm_at_its_figure_size(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation

    monkeypatch.delenv(media.CLIP_ENCODER_ENV, raising=False)
    fig = plt.figure(figsize=(1.6, 0.9), dpi=100)
    ax = fig.add_subplot()
    (line,) = ax.plot([0, 1], [0, 0])

    def update(k: int) -> tuple[Line2D]:
        line.set_ydata([0, k])
        return (line,)

    anim = FuncAnimation(fig, update, frames=3, interval=50)
    media._save_animation(anim, fig, str(tmp_path), "anim_probe", make_gif=False)
    webm = tmp_path / "anim_probe.webm"
    probe = json.loads(
        subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=codec_name,width,height",
                "-of",
                "json",
                str(webm),
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=True,
        ).stdout
    )["streams"][0]
    assert probe == {"codec_name": "av1", "width": 160, "height": 90}
    assert (tmp_path / "anim_probe_poster.webp").exists()
