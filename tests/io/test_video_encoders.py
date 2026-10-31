#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Which encoder writes a video: a real one-frame trial at the real frame size."""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

pytest.importorskip("matplotlib")

import fake_ffmpeg
import windows_lookup

from phonometry.io import _video_encoders as ve
from phonometry.io._video_quality import ENCODER_QUALITY, GIF_PALETTE

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


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
    """The lines of ``ffmpeg -h <topic>``: an argument list, no shell.

    Read as UTF-8 whatever the console's code page, a byte it cannot read
    replaced: an option's name is ASCII, and its description is not read.
    """
    done = subprocess.run(
        [ffmpeg, "-hide_banner", "-h", *topic],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
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
    checked = sorted({name for name, _ in ENCODER_QUALITY} & compiled)
    if not checked:
        pytest.skip(
            "this ffmpeg has none of the encoders the presets name, so no "
            "flag of theirs can be read"
        )
    generic = _generic_options(_help(ffmpeg, "full"))
    own: dict[str, set[str]] = {}
    unknown: set[str] = set()
    for (name, _), row in ENCODER_QUALITY.items():
        if name not in checked:
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


@pytest.fixture
def windows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A Windows lookup of a bare ``"ffmpeg"`` from *tmp_path*, which holds a planted ``ffmpeg.exe``."""
    import matplotlib as mpl

    (tmp_path / "ffmpeg.exe").write_bytes(b"")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path / "elsewhere"))
    monkeypatch.setitem(mpl.rcParams, "animation.ffmpeg_path", "ffmpeg")
    monkeypatch.setattr(ve.shutil, "which", windows_lookup.which)
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


def test_windows_names_the_ffmpeg_it_passes_over_and_runs_by_their_escapes(
    windows: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The working directory, the program's name and ``PATH`` are the caller's, so are the names."""
    import matplotlib as mpl

    (windows / "ff‮mpeg.exe").write_bytes(b"")
    monkeypatch.setitem(mpl.rcParams, "animation.ffmpeg_path", "ff‮mpeg")
    with pytest.raises(ve.FFmpegNotFoundError) as caught:
        ve.find_ffmpeg()
    message = str(caught.value)
    assert "‮" not in message
    assert f"working directory ({os.curdir}{os.sep}ff\\u202empeg.exe)" in message
    installed = windows / "else‮where" / "ff‮mpeg.exe"
    installed.parent.mkdir()
    installed.write_bytes(b"")
    monkeypatch.setenv("PATH", str(installed.parent))
    with caplog.at_level(logging.INFO, logger="phonometry.io"):
        assert ve.find_ffmpeg() == str(installed)
    (record,) = caplog.records
    logged = record.getMessage()
    assert "‮" not in logged
    assert f"{windows}{os.sep}else\\u202ewhere{os.sep}ff\\u202empeg.exe" in logged


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
    assert ve.trial(
        described, choice, width=64, height=64, vaapi_device=ve.DEFAULT_VAAPI_DEVICE
    )
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


def test_what_a_failing_ffmpeg_wrote_is_quoted_with_its_control_characters_escaped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ffmpeg's words reach the caller's terminal, so they cannot clear it."""
    fake = fake_ffmpeg.install(
        tmp_path,
        monkeypatch,
        said={"-version": "\x1b[2Jlibavutil: version broke"},
        fails=["-version"],
    )
    with pytest.raises(ve.VideoEncoderError) as caught:
        ve.describe(str(fake.launcher))
    message = str(caught.value)
    assert "\x1b" not in message
    assert message.endswith(
        " did not run: \\x1b[2Jlibavutil: version broke (-version exited with status 1)"
    )


def test_an_ffmpeg_with_no_encoder_for_the_video_is_named_by_its_escapes() -> None:
    """The path of the ffmpeg is the caller's or ``PATH``'s, and its version line is its own."""
    ffmpeg = ve.FFmpeg(
        path="/opt/ff‮mpeg/bin/ffmpeg",
        version="ffmpeg version 7.1\x1b[2J",
        encoders=frozenset(),
    )
    with pytest.raises(
        ve.VideoEncoderError, match=r"^encoder='auto' cannot write"
    ) as caught:
        ve.choose(
            ffmpeg,
            encoder="auto",
            codec=None,
            container="webm",
            width=32,
            height=32,
            vaapi_device=ve.DEFAULT_VAAPI_DEVICE,
        )
    message = str(caught.value)
    assert "‮" not in message
    assert "\x1b" not in message
    assert (
        "with /opt/ff\\u202empeg/bin/ffmpeg (ffmpeg version 7.1\\x1b[2J); " in message
    )


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


def _not_a_program(tmp_path: Path) -> Path:
    """A file where an ffmpeg would be that no system starts: text, and not executable.

    Named ``ffmpeg.exe`` on Windows, which then refuses it as no Win32
    application rather than look for an ``ffmpeg.exe`` beside it.
    """
    path = tmp_path / ("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
    path.write_text("not a program\n", encoding="utf-8")
    return path


def test_an_ffmpeg_that_does_not_start_is_an_encoder_error_naming_it(
    tmp_path: Path,
) -> None:
    """A file that is there but is no program is refused as an ffmpeg that does not run."""
    broken = _not_a_program(tmp_path)
    with pytest.raises(
        ve.VideoEncoderError, match=rf"^{re.escape(str(broken))} did not run: "
    ) as raised:
        ve.describe(str(broken))
    assert isinstance(raised.value.__cause__, OSError)


def test_an_ffmpeg_that_does_not_answer_in_time_is_an_encoder_error_naming_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    # No program starts and answers -version within a millisecond.
    monkeypatch.setattr(ve, "_RUN_TIMEOUT_S", 1e-3)
    with pytest.raises(
        ve.VideoEncoderError, match=rf"^{re.escape(str(fake.launcher))} did not run: "
    ) as raised:
        ve.describe(str(fake.launcher))
    assert isinstance(raised.value.__cause__, subprocess.TimeoutExpired)


def test_auto_takes_the_first_encoder_that_passes_a_trial(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    ffmpeg = ve.describe(str(fake.launcher))
    choice = ve.choose(
        ffmpeg,
        encoder="auto",
        codec=None,
        container="webm",
        width=320,
        height=240,
        vaapi_device=ve.DEFAULT_VAAPI_DEVICE,
    )
    assert choice == ve.EncoderChoice("cpu", "av1", "libsvtav1")
    # NVENC is compiled in but fails its trial, so it is tried first and
    # passed over; the trial ran at the real frame size.
    tried = [t["argv"][t["argv"].index("-c:v") + 1] for t in fake.trials()]
    assert tried == ["av1_nvenc", "libsvtav1"]
    assert all(t["argv"][t["argv"].index("-s") + 1] == "320x240" for t in fake.trials())
    assert all(t["frames"] == 1 for t in fake.trials())


def test_a_failed_trial_logs_what_ffmpeg_said_at_debug(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Why NVENC was passed over is on the phonometry.io logger, for whoever turns DEBUG on."""
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    ffmpeg = ve.describe(str(fake.launcher))
    with caplog.at_level(logging.DEBUG, logger="phonometry.io"):
        ve.choose(
            ffmpeg,
            encoder="auto",
            codec=None,
            container="webm",
            width=32,
            height=32,
            vaapi_device=ve.DEFAULT_VAAPI_DEVICE,
        )
    failed = [r for r in caplog.records if r.levelno == logging.DEBUG]
    assert [r.getMessage() for r in failed] == [
        "av1_nvenc failed its trial at 32x32 (status 1): "
        "fake ffmpeg: Error while opening encoder av1_nvenc"
    ]
    assert {r.name for r in failed} == {"phonometry.io"}


def _failed_trial(ffmpeg: ve.FFmpeg, caplog: pytest.LogCaptureFixture) -> BaseException:
    """The error a failed VP9 trial at 32x32 quotes in what it logs at DEBUG on phonometry.io."""
    choice = ve.EncoderChoice("cpu", "vp9", "libvpx-vp9")
    with caplog.at_level(logging.DEBUG, logger="phonometry.io"):
        passed = ve.trial(
            ffmpeg, choice, width=32, height=32, vaapi_device=ve.DEFAULT_VAAPI_DEVICE
        )
    assert not passed
    [record] = [r for r in caplog.records if r.levelno == logging.DEBUG]
    assert record.name == "phonometry.io"
    assert record.getMessage().startswith("libvpx-vp9 failed its trial at 32x32: ")
    assert isinstance(record.args, tuple)
    error = record.args[-1]
    assert isinstance(error, BaseException)
    assert record.getMessage().endswith(f": {error}")
    return error


def test_a_trial_whose_ffmpeg_does_not_start_fails_and_logs_why_at_debug(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """An ffmpeg gone bad since it was described fails the trial, which says why."""
    broken = ve.FFmpeg(
        path=str(_not_a_program(tmp_path)),
        version="ffmpeg version 7.1-fake",
        encoders=frozenset({"libvpx-vp9"}),
    )
    assert isinstance(_failed_trial(broken, caplog), OSError)


def test_a_trial_that_does_not_finish_in_time_fails_and_logs_why_at_debug(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """An encoder that hangs (a GPU one as it opens, say) is passed over like one that fails."""
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    ffmpeg = ve.describe(str(fake.launcher))
    # No program starts and encodes a frame within a millisecond.
    monkeypatch.setattr(ve, "_RUN_TIMEOUT_S", 1e-3)
    assert isinstance(_failed_trial(ffmpeg, caplog), subprocess.TimeoutExpired)


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
        ffmpeg,
        encoder="cpu",
        codec=None,
        container="webm",
        width=64,
        height=64,
        vaapi_device=ve.DEFAULT_VAAPI_DEVICE,
    )
    assert choice.name == "libvpx-vp9"


def test_a_success_is_remembered_and_a_failure_is_not(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch, working=["libvpx-vp9"])
    ffmpeg = ve.describe(str(fake.launcher))
    for _ in range(2):
        ve.choose(
            ffmpeg,
            encoder="auto",
            codec=None,
            container="webm",
            width=32,
            height=32,
            vaapi_device=ve.DEFAULT_VAAPI_DEVICE,
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
            ffmpeg,
            encoder="nvenc",
            codec=None,
            container="webm",
            width=32,
            height=32,
            vaapi_device=ve.DEFAULT_VAAPI_DEVICE,
        )


def test_no_encoder_at_all_says_what_was_tried(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch, encoders=["libx264"], working=[])
    ffmpeg = ve.describe(str(fake.launcher))
    with pytest.raises(
        ve.VideoEncoderError,
        match=r"^encoder='auto' cannot write av1/vp9 into \.webm with .*; "
        r"tried nothing it has\. Install an ffmpeg built with SVT-AV1",
    ):
        ve.choose(
            ffmpeg,
            encoder="auto",
            codec=None,
            container="webm",
            width=32,
            height=32,
            vaapi_device=ve.DEFAULT_VAAPI_DEVICE,
        )


@pytest.mark.parametrize(
    ("container", "codec", "libraries"),
    [
        ("webm", None, "SVT-AV1 or libvpx"),
        ("mp4", None, "SVT-AV1, x265 or x264"),
        ("webm", "vp9", "libvpx"),
        ("mp4", "h264", "x264"),
    ],
)
def test_the_install_hint_names_what_the_container_holds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    container: ve.Container,
    codec: ve.Codec | None,
    libraries: str,
) -> None:
    """With no encoder working, the hint names the CPU encoders that write what was asked, in that container."""
    fake = fake_ffmpeg.install(tmp_path, monkeypatch, working=[])
    ffmpeg = ve.describe(str(fake.launcher))
    with pytest.raises(
        ve.VideoEncoderError,
        match=rf"\. Install an ffmpeg built with {libraries}\.$",
    ):
        ve.choose(
            ffmpeg,
            encoder="auto",
            codec=codec,
            container=container,
            width=32,
            height=32,
            vaapi_device=ve.DEFAULT_VAAPI_DEVICE,
        )


def test_encoders_that_fail_their_trials_are_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch, working=[])
    ffmpeg = ve.describe(str(fake.launcher))
    with pytest.raises(
        ve.VideoEncoderError, match=r"; tried av1_nvenc, libsvtav1, libvpx-vp9\."
    ):
        ve.choose(
            ffmpeg,
            encoder="auto",
            codec=None,
            container="webm",
            width=32,
            height=32,
            vaapi_device=ve.DEFAULT_VAAPI_DEVICE,
        )


def test_a_gpu_encoder_of_a_lesser_codec_comes_before_the_cpu_s_av1_in_an_mp4(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The kinds of encoder go first, the codecs within each: NVENC's HEVC before SVT-AV1."""
    fake = fake_ffmpeg.install(
        tmp_path,
        monkeypatch,
        encoders=["av1_nvenc", "hevc_nvenc", "libsvtav1", "libx265"],
        working=["hevc_nvenc", "libsvtav1", "libx265"],
    )
    ffmpeg = ve.describe(str(fake.launcher))
    choice = ve.choose(
        ffmpeg,
        encoder="auto",
        codec=None,
        container="mp4",
        width=64,
        height=64,
        vaapi_device=ve.DEFAULT_VAAPI_DEVICE,
    )
    assert choice == ve.EncoderChoice("nvenc", "hevc", "hevc_nvenc")
    tried = [t["argv"][t["argv"].index("-c:v") + 1] for t in fake.trials()]
    assert tried == ["av1_nvenc", "hevc_nvenc"]


def test_mp4_prefers_av1_then_hevc_then_h264(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch, working=["libx265", "libx264"])
    ffmpeg = ve.describe(str(fake.launcher))
    choice = ve.choose(
        ffmpeg,
        encoder="cpu",
        codec=None,
        container="mp4",
        width=32,
        height=32,
        vaapi_device=ve.DEFAULT_VAAPI_DEVICE,
    )
    assert choice.name == "libx265"
    # SVT-AV1 is compiled in and fails here, so it is tried first; x264 never is.
    tried = [t["argv"][t["argv"].index("-c:v") + 1] for t in fake.trials()]
    assert tried == ["libsvtav1", "libx265"]


def test_vaapi_encodes_on_the_device_named_and_no_other_kind_takes_one() -> None:
    def arguments(choice: ve.EncoderChoice) -> ve.VideoArguments:
        return ve.video_arguments(
            choice,
            quality="standard",
            options=(),
            container="webm",
            width=960,
            height=540,
            pad_color="#ffffff",
            vaapi_device="/dev/dri/renderD129",
        )

    vaapi = arguments(ve.EncoderChoice("vaapi", "av1", "av1_vaapi"))
    assert vaapi.before_input == ("-vaapi_device", "/dev/dri/renderD129")
    assert vaapi.filters == ("format=nv12,hwupload",)
    assert "-pix_fmt" not in vaapi.codec_arguments
    nvenc = arguments(ve.EncoderChoice("nvenc", "av1", "av1_nvenc"))
    assert nvenc.before_input == ()
    assert ve.DEFAULT_VAAPI_DEVICE == "/dev/dri/renderD128"


def test_a_vaapi_success_is_remembered_for_its_device_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(
        tmp_path, monkeypatch, encoders=["av1_vaapi"], working=["av1_vaapi"]
    )
    ffmpeg = ve.describe(str(fake.launcher))
    choice = ve.EncoderChoice("vaapi", "av1", "av1_vaapi")
    for device in ("/dev/dri/renderD128", "/dev/dri/renderD128", "/dev/dri/renderD129"):
        assert ve.trial(ffmpeg, choice, width=32, height=32, vaapi_device=device)
    devices = [t["argv"][t["argv"].index("-vaapi_device") + 1] for t in fake.trials()]
    assert devices == ["/dev/dri/renderD128", "/dev/dri/renderD129"]


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
        vaapi_device=ve.DEFAULT_VAAPI_DEVICE,
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


@pytest.mark.parametrize(
    ("pixels", "filters"),
    [
        ((64, 64), ("format=nv12,hwupload",)),
        (
            (65, 64),
            ("pad=ceil(iw/2)*2:ceil(ih/2)*2:color=#ffffff", "format=nv12,hwupload"),
        ),
    ],
)
def test_vaapi_opens_its_device_and_uploads_the_frames(
    pixels: tuple[int, int], filters: tuple[str, ...]
) -> None:
    """The device the guide names, the frames handed to it in NV12, an odd frame padded first."""
    width, height = pixels
    video = ve.video_arguments(
        ve.EncoderChoice("vaapi", "h264", "h264_vaapi"),
        quality="standard",
        options=(),
        container="mp4",
        width=width,
        height=height,
        pad_color="#ffffff",
        vaapi_device=ve.DEFAULT_VAAPI_DEVICE,
    )
    assert video.before_input == ("-vaapi_device", "/dev/dri/renderD128")
    assert video.filters == filters
    # The upload sets the pixel format; a -pix_fmt after it would undo it.
    assert "-pix_fmt" not in video.codec_arguments
    assert video.codec_arguments[:2] == ("-c:v", "h264_vaapi")


def _described_by(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, answer: object
) -> Callable[[], ve.FFmpeg]:
    """describe() of a launcher of this test's own, with each run of ffmpeg answered by *answer*."""
    launcher = tmp_path / "ffmpeg"
    launcher.write_bytes(b"")

    def run(command: list[str], **_kwargs: object) -> object:
        if isinstance(answer, BaseException):
            raise answer
        return answer

    monkeypatch.setattr(ve, "_run", run)
    return lambda: ve.describe(str(launcher))


def test_an_ffmpeg_that_exits_with_an_error_does_not_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    failed = subprocess.CompletedProcess(
        ["ffmpeg"], 1, stdout=b"", stderr=b"error while loading shared libraries"
    )
    describe = _described_by(monkeypatch, tmp_path, failed)
    with pytest.raises(
        ve.VideoEncoderError, match=r"did not run: error while loading shared libraries"
    ):
        describe()


def test_an_ffmpeg_that_hangs_does_not_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    describe = _described_by(
        monkeypatch, tmp_path, subprocess.TimeoutExpired(["ffmpeg"], 60.0)
    )
    with pytest.raises(ve.VideoEncoderError, match=r"did not run: .*timed out"):
        describe()
