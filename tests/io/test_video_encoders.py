#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Which encoder writes a video: a real one-frame trial at the real frame size."""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("matplotlib")

import fake_ffmpeg

from phonometry.io import _video_encoders as ve
from phonometry.io._video_quality import ENCODER_QUALITY, GIF_PALETTE


def test_every_encoder_name_has_its_three_presets() -> None:
    for name in ve.FFMPEG_NAMES.values():
        for quality in ("high", "standard", "small"):
            assert (name, quality) in ENCODER_QUALITY, (name, quality)
    assert set(GIF_PALETTE) == {"high", "standard", "small"}


def test_the_cpu_never_uses_libaom() -> None:
    assert "libaom-av1" not in ve.FFMPEG_NAMES.values()
    assert ve.FFMPEG_NAMES["cpu", "av1"] == "libsvtav1"


#: An option line of ffmpeg's help: its name, without the leading dash.
_OPTION_LINE = re.compile(r"^\s*-([A-Za-z0-9_-]+)")
#: The header of each block of AVOptions in ``ffmpeg -h full``.
_AVOPTIONS_HEADER = re.compile(r"^\S.*AVOptions:$")


def _help(ffmpeg: str, *topic: str) -> list[str]:
    """The lines of ``ffmpeg -h <topic>``: an argument list, no shell."""
    done = subprocess.run(
        [ffmpeg, "-hide_banner", "-h", *topic],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    return done.stdout.splitlines()


def _option_names(lines: list[str]) -> set[str]:
    return {match.group(1) for line in lines if (match := _OPTION_LINE.match(line))}


def _generic_options(full: list[str]) -> set[str]:
    """ffmpeg's own options and the AVCodecContext options every encoder takes.

    ffmpeg's own (``-q``, ``-b``) come before the first block of AVOptions:
    ffmpeg refuses one it does not know, so none of them can be dropped
    unread. The AVCodecContext block (``-b``, ``-global_quality``) is the one
    block of AVOptions every encoder reads from.
    """
    first = next(i for i, line in enumerate(full) if _AVOPTIONS_HEADER.match(line))
    start = full.index("AVCodecContext AVOptions:") + 1
    end = next(
        (i for i in range(start, len(full)) if _AVOPTIONS_HEADER.match(full[i])),
        len(full),
    )
    return _option_names(full[:first]) | _option_names(full[start:end])


def test_every_preset_flag_is_an_option_its_encoder_has() -> None:
    # ffmpeg drops an option the encoder lacks with a warning the writer's
    # "-loglevel error" never shows, so a wrong flag encodes at the
    # encoder's default quality whatever the preset says.
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        pytest.skip(
            "needs ffmpeg on PATH to read the encoders' options from; "
            "the CI video job installs it"
        )
    compiled = ve.describe(ffmpeg).encoders
    generic = _generic_options(_help(ffmpeg, "full"))
    own: dict[str, set[str]] = {}
    unknown: set[str] = set()
    for (name, _), row in ENCODER_QUALITY.items():
        if name not in compiled:
            continue
        if name not in own:
            own[name] = _option_names(_help(ffmpeg, f"encoder={name}"))
        flags = {token[1:].split(":")[0] for token in row if token.startswith("-")}
        unknown |= {f"{name} -{flag}" for flag in flags - own[name] - generic}
    assert not unknown, sorted(unknown)


def test_ffmpeg_is_found_where_matplotlib_looks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    assert ve.find_ffmpeg() == str(fake.launcher)


def test_a_missing_ffmpeg_names_the_rcparam_and_the_install(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import matplotlib as mpl

    monkeypatch.setitem(mpl.rcParams, "animation.ffmpeg_path", "no-such-ffmpeg-here")
    with pytest.raises(ve.FFmpegNotFoundError, match="animation.ffmpeg_path"):
        ve.find_ffmpeg()


def test_pyodide_says_why(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "emscripten")
    with pytest.raises(ve.FFmpegNotFoundError, match="Pyodide"):
        ve.find_ffmpeg()


def _windows_lookup(name: str) -> str | None:
    """What ``shutil.which`` does on Windows: a bare name in the working directory first, then on PATH."""
    given = Path(name)
    places = (
        [str(given.parent)]
        if given.name != name
        else [os.curdir, *os.environ["PATH"].split(os.pathsep)]
    )
    for place in places:
        for candidate in (given.name, f"{given.name}.exe"):
            if (Path(place) / candidate).is_file():
                # Windows writes the directory it searched, "." included.
                return f"{place}{os.sep}{candidate}"
    return None


@pytest.fixture
def windows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A Windows lookup of a bare ``"ffmpeg"`` from *tmp_path*, which holds a planted ``ffmpeg.exe``."""
    import matplotlib as mpl

    (tmp_path / "ffmpeg.exe").write_bytes(b"")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path / "elsewhere"))
    monkeypatch.setitem(mpl.rcParams, "animation.ffmpeg_path", "ffmpeg")
    monkeypatch.setattr(ve.shutil, "which", _windows_lookup)
    monkeypatch.setattr(sys, "platform", "win32")
    return tmp_path


def test_windows_does_not_run_an_ffmpeg_found_only_in_the_working_directory(
    windows: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import matplotlib as mpl

    with pytest.raises(
        ve.FFmpegNotFoundError,
        match=r"^ffmpeg was found only in the working directory \(\.[/\\]ffmpeg\.exe\)",
    ):
        ve.find_ffmpeg()
    # Named by its full path, the same file is the user's own choice.
    planted = str(windows / "ffmpeg.exe")
    monkeypatch.setitem(mpl.rcParams, "animation.ffmpeg_path", planted)
    assert ve.find_ffmpeg() == planted


def test_windows_runs_the_ffmpeg_on_path_past_one_in_the_working_directory(
    windows: Path, caplog: pytest.LogCaptureFixture
) -> None:
    installed = windows / "elsewhere" / "ffmpeg.exe"
    installed.parent.mkdir()
    installed.write_bytes(b"")
    with caplog.at_level(logging.INFO, logger="phonometry.io"):
        assert ve.find_ffmpeg() == str(installed)
    (record,) = caplog.records
    assert "ffmpeg.exe" in record.getMessage()
    assert str(installed) in record.getMessage()


def test_windows_runs_an_ffmpeg_from_a_working_directory_path_lists(
    windows: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(
        "PATH", os.pathsep.join([str(windows / "elsewhere"), str(windows)])
    )
    assert ve.find_ffmpeg() == f"{os.curdir}{os.sep}ffmpeg.exe"


def test_ffmpeg_runs_without_a_console_window(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    seen: list[object] = []
    real_run = ve.subprocess.run

    def run(*args: object, **kwargs: object) -> object:
        seen.append(kwargs.get("creationflags"))
        return real_run(*args, **kwargs)  # type: ignore[call-overload]

    monkeypatch.setattr(ve.subprocess, "run", run)
    ve.describe(str(fake.launcher))  # a launcher of this test's own: not read before
    assert seen
    assert set(seen) == {ve.NO_WINDOW}
    assert ve.NO_WINDOW == getattr(ve.subprocess, "CREATE_NO_WINDOW", 0)


def test_ffmpeg_never_inherits_this_process_s_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ffmpeg reads the frame it is given, or nothing, never this process's own input.

    On Windows a program started on a pipe another thread is reading (a
    node's input watcher, which reads the node's input until its client
    goes) blocks as it starts, so describing ffmpeg on a Windows node
    waited for good.
    """
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    seen: list[tuple[object, object]] = []
    real_run = ve.subprocess.run

    def run(*args: object, **kwargs: object) -> object:
        seen.append((kwargs.get("stdin"), kwargs.get("input")))
        return real_run(*args, **kwargs)  # type: ignore[call-overload]

    monkeypatch.setattr(ve.subprocess, "run", run)
    described = ve.describe(str(fake.launcher))
    choice = ve.EncoderChoice("cpu", "vp9", "libvpx-vp9")
    assert ve.trial(described, choice, width=64, height=64)
    assert seen[:2] == [(subprocess.DEVNULL, None)] * 2
    stdin, frame = seen[2]
    assert stdin is None
    assert frame == bytes(64 * 64 * 4)


def test_describe_reads_the_version_and_the_compiled_encoders(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    found = ve.describe(str(fake.launcher))
    assert found.version.startswith("ffmpeg version 7.1-fake")
    assert {"libsvtav1", "av1_nvenc"} <= found.encoders


def test_an_ffmpeg_that_has_gone_is_an_encoder_error_naming_it(tmp_path: Path) -> None:
    """A binary found a moment ago and removed since is refused as one that does not run."""
    gone = tmp_path / "ffmpeg"
    with pytest.raises(
        ve.VideoEncoderError, match=rf"^{re.escape(str(gone))} did not run: "
    ):
        ve.describe(str(gone))


def test_a_version_that_fails_is_reported_and_the_encoders_are_not_listed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(
        tmp_path,
        monkeypatch,
        said={"-version": "libavutil: version broke"},
        fails=["-version"],
    )
    with pytest.raises(
        ve.VideoEncoderError,
        match=r" did not run: libavutil: version broke \(-version exited with status 1\)$",
    ):
        ve.describe(str(fake.launcher))
    assert [call["kind"] for call in fake.calls()] == ["version"]


def test_a_listing_that_fails_is_reported_with_its_own_words(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The -version run's own stderr (a warning, on success) is not taken for the failure's."""
    fake = fake_ffmpeg.install(
        tmp_path,
        monkeypatch,
        said={
            "-version": "a library warns on every run",
            "-encoders": "the encoder list broke",
        },
        fails=["-encoders"],
    )
    with pytest.raises(
        ve.VideoEncoderError,
        match=r" did not run: the encoder list broke \(-encoders exited with status 1\)$",
    ):
        ve.describe(str(fake.launcher))


def test_auto_takes_the_first_encoder_that_passes_a_trial(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    ffmpeg = ve.describe(str(fake.launcher))
    choice = ve.choose(
        ffmpeg, encoder="auto", codec=None, container="webm", width=320, height=240
    )
    assert choice == ve.EncoderChoice("cpu", "av1", "libsvtav1")
    # NVENC is compiled in but fails its trial, so it is tried first and
    # passed over; the trial ran at the real frame size.
    tried = [t["argv"][t["argv"].index("-c:v") + 1] for t in fake.trials()]
    assert tried == ["av1_nvenc", "libsvtav1"]
    assert all(t["argv"][t["argv"].index("-s") + 1] == "320x240" for t in fake.trials())
    assert all(t["frames"] == 1 for t in fake.trials())


def test_vp9_when_svt_av1_is_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(
        tmp_path,
        monkeypatch,
        encoders=["libaom-av1", "libvpx-vp9"],
        working=["libaom-av1", "libvpx-vp9"],
    )
    ffmpeg = ve.describe(str(fake.launcher))
    choice = ve.choose(
        ffmpeg, encoder="cpu", codec=None, container="webm", width=64, height=64
    )
    assert choice.name == "libvpx-vp9"


def test_a_success_is_remembered_and_a_failure_is_not(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch, working=["libvpx-vp9"])
    ffmpeg = ve.describe(str(fake.launcher))
    for _ in range(2):
        ve.choose(
            ffmpeg, encoder="auto", codec=None, container="webm", width=32, height=32
        )
    names = [t["argv"][t["argv"].index("-c:v") + 1] for t in fake.trials()]
    # Both failures (NVENC, SVT-AV1) are tried again; the VP9 success is not.
    assert names == ["av1_nvenc", "libsvtav1", "libvpx-vp9", "av1_nvenc", "libsvtav1"]


def test_an_explicit_encoder_that_fails_lists_the_ones_that_work(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    ffmpeg = ve.describe(str(fake.launcher))
    with pytest.raises(ve.VideoEncoderError, match="libsvtav1"):
        ve.choose(
            ffmpeg, encoder="nvenc", codec=None, container="webm", width=32, height=32
        )


def test_no_encoder_at_all_says_what_was_tried(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch, encoders=["libx264"], working=[])
    ffmpeg = ve.describe(str(fake.launcher))
    with pytest.raises(ve.VideoEncoderError, match=r"\.webm"):
        ve.choose(
            ffmpeg, encoder="auto", codec=None, container="webm", width=32, height=32
        )


def test_mp4_prefers_av1_then_hevc_then_h264(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch, working=["libx265", "libx264"])
    ffmpeg = ve.describe(str(fake.launcher))
    choice = ve.choose(
        ffmpeg, encoder="cpu", codec=None, container="mp4", width=32, height=32
    )
    assert choice.name == "libx265"


def test_an_odd_frame_is_padded_and_hevc_in_mp4_is_tagged() -> None:
    choice = ve.EncoderChoice("cpu", "hevc", "libx265")
    video = ve.video_arguments(
        choice,
        quality="standard",
        options=("-threads", "2"),
        container="mp4",
        width=961,
        height=541,
        pad_color="#ffffff",
    )
    assert video.filters == ("pad=ceil(iw/2)*2:ceil(ih/2)*2:color=#ffffff",)
    assert video.codec_arguments[:2] == ("-c:v", "libx265")
    assert video.codec_arguments[-2:] == ("-threads", "2")
    assert video.codec_arguments[-4:-2] == ("-pix_fmt", "yuv420p")
    assert video.muxer_options == ("-tag:v", "hvc1", "-movflags", "+faststart")


def test_a_gif_is_one_palette_run() -> None:
    video = ve.gif_arguments(quality="small", options=())
    (graph,) = video.filters
    assert graph.startswith("split[a][b];[a]palettegen=max_colors=64")
    assert "paletteuse=dither=bayer:bayer_scale=3" in graph
    assert video.codec_arguments == ()
    assert video.muxer_options == ("-loop", "0")


def test_the_command_reads_raw_rgba_from_stdin() -> None:
    video = ve.raw_arguments(
        "av1_nvenc",
        options=("-cq", "44"),
        container="webm",
        width=960,
        height=540,
        pad_color="#000000",
    )
    command = ve.ffmpeg_command(
        "/usr/bin/ffmpeg",
        width=960,
        height=540,
        rate="20/1",
        video=video,
        muxer="webm",
        output="/tmp/x.webm",
    )
    assert command[:3] == ["/usr/bin/ffmpeg", "-hide_banner", "-nostats"]
    i = command.index("-i")
    assert command[i - 8 : i + 2] == [
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgba",
        "-s",
        "960x540",
        "-r",
        "20/1",
        "-i",
        "-",
    ]
    assert "-vf" not in command  # even size: nothing to pad
    assert command[-3:] == ["-f", "webm", "/tmp/x.webm"]
    assert command[command.index("-c:v") : command.index("-c:v") + 4] == [
        "-c:v",
        "av1_nvenc",
        "-cq",
        "44",
    ]
