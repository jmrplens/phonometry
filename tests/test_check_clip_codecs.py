#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every published clip is AV1, written by the encoder its manifest line names."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    import pytest

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_ROOT / "scripts"))

import check_animation_freshness
import check_clip_codecs


def _ffprobe(
    codec: str, encoder: str | None
) -> Callable[..., subprocess.CompletedProcess[str]]:
    """An ffprobe that reports one video stream of *codec*, tagged with *encoder*."""

    def run(argv: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        stream: dict[str, object] = {"codec_name": codec}
        if encoder is not None:
            stream["tags"] = {"ENCODER": encoder}
        return subprocess.CompletedProcess(
            argv, 0, json.dumps({"streams": [stream]}), ""
        )

    return run


def _clips(tmp_path: Path) -> Path:
    for name in check_animation_freshness.outputs("anim_x"):
        (tmp_path / name).write_bytes(b"x")
    return tmp_path


def test_an_av1_clip_from_its_recorded_encoder_passes(tmp_path: Path) -> None:
    run = _ffprobe("av1", "Lavc61.19.100 av1_nvenc")
    found = check_clip_codecs.problems(
        _clips(tmp_path), ["anim_x"], {"anim_x": "av1_nvenc"}, run=run
    )
    assert found == []


def test_a_vp9_clip_is_named(tmp_path: Path) -> None:
    run = _ffprobe("vp9", None)
    found = check_clip_codecs.problems(
        _clips(tmp_path), ["anim_x"], {"anim_x": "av1_nvenc"}, run=run
    )
    assert len(found) == 4
    assert all("not AV1" in line for line in found)


def test_a_clip_written_by_another_encoder_is_named(tmp_path: Path) -> None:
    run = _ffprobe("av1", "Lavc61.19.100 libsvtav1")
    found = check_clip_codecs.problems(
        _clips(tmp_path), ["anim_x"], {"anim_x": "av1_nvenc"}, run=run
    )
    assert len(found) == 4
    assert all("libsvtav1" in line and "av1_nvenc" in line for line in found)


def test_a_clip_with_no_encoder_recorded_is_named(tmp_path: Path) -> None:
    found = check_clip_codecs.problems(
        _clips(tmp_path), ["anim_x"], {}, run=_ffprobe("av1", None)
    )
    assert found == ["anim_x: no encoder recorded in the manifest"]


def test_a_clip_whose_stream_names_no_encoder_is_named(tmp_path: Path) -> None:
    """write_video keeps ffmpeg's ENCODER tag; a WebM without it was written some other way."""
    found = check_clip_codecs.problems(
        _clips(tmp_path), ["anim_x"], {"anim_x": "av1_nvenc"}, run=_ffprobe("av1", None)
    )
    assert len(found) == 4
    assert all("names no encoder" in line for line in found)


def test_a_missing_webm_is_named_and_the_others_are_read(tmp_path: Path) -> None:
    clips = _clips(tmp_path)
    (clips / "anim_x_es_dark.webm").unlink()
    run = _ffprobe("av1", "Lavc63.1.102 libsvtav1")
    found = check_clip_codecs.problems(
        clips, ["anim_x"], {"anim_x": "libsvtav1"}, run=run
    )
    assert found == ["anim_x_es_dark.webm: missing"]


def test_a_webm_ffprobe_cannot_read_is_named_with_what_ffprobe_said(
    tmp_path: Path,
) -> None:
    def run(argv: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.CalledProcessError(
            1, argv, "", "Invalid data found when processing input\n"
        )

    found = check_clip_codecs.problems(
        _clips(tmp_path), ["anim_x"], {"anim_x": "av1_nvenc"}, run=run
    )
    assert len(found) == 4
    assert all("Invalid data found when processing input" in line for line in found)


def test_a_webm_ffprobe_does_not_finish_is_named_and_the_check_goes_on(
    tmp_path: Path,
) -> None:
    """One file that holds ffprobe past its limit is named; it does not stop the check."""

    def run(argv: list[str], **options: object) -> subprocess.CompletedProcess[str]:
        if argv[-1].endswith("_dark.webm"):
            raise subprocess.TimeoutExpired(argv, check_clip_codecs.PROBE_TIMEOUT_S)
        return _ffprobe("av1", "Lavc63.1.102 av1_nvenc")(argv)

    found = check_clip_codecs.problems(
        _clips(tmp_path), ["anim_x"], {"anim_x": "av1_nvenc"}, run=run
    )
    assert found == [
        f"{name}: ffprobe cannot read it (ffprobe did not finish in 120 s)"
        for name in ("anim_x_dark.webm", "anim_x_es_dark.webm")
    ]


def test_what_ffprobe_said_over_several_lines_is_named_on_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Every line of the check is one ``::error::`` annotation, ffprobe's words included."""

    def unreadable(path: Path, **_: object) -> tuple[str, str]:
        raise subprocess.CalledProcessError(
            1,
            ["ffprobe", str(path)],
            "",
            "EBML header parsing failed\n\nInvalid data found\n",
        )

    monkeypatch.setattr(check_clip_codecs.fp, "fingerprints", lambda _: {"anim_x": "0"})
    monkeypatch.setattr(
        check_clip_codecs.fp, "read_encoders", lambda: {"anim_x": "av1_nvenc"}
    )
    monkeypatch.setattr(
        check_clip_codecs.assets_dir, "clips_dir", lambda: _clips(tmp_path)
    )
    monkeypatch.setattr(check_clip_codecs, "probe", unreadable)
    assert check_clip_codecs.main([]) == 1
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 4
    assert all(
        line.startswith("::error::anim_x")
        and line.endswith(
            ": ffprobe cannot read it (EBML header parsing failed; Invalid data found)"
        )
        for line in lines
    )


def test_a_stream_whose_encoder_tag_is_blank_names_no_encoder(tmp_path: Path) -> None:
    """A tag of spaces is no encoder, and is said so rather than failing the check."""
    run = _ffprobe("av1", "   ")
    assert check_clip_codecs.probe(tmp_path / "anim_x.webm", run=run) == ("av1", "")
    found = check_clip_codecs.problems(
        _clips(tmp_path), ["anim_x"], {"anim_x": "av1_nvenc"}, run=run
    )
    assert len(found) == 4
    assert all("names no encoder" in line for line in found)


def test_ffprobe_is_given_a_time_limit_and_the_path(tmp_path: Path) -> None:
    calls: list[tuple[list[str], dict[str, object]]] = []

    def run(argv: list[str], **options: object) -> subprocess.CompletedProcess[str]:
        calls.append((argv, options))
        return _ffprobe("av1", "Lavc63.1.102 av1_nvenc")(argv)

    path = tmp_path / "anim_x.webm"
    assert check_clip_codecs.probe(path, run=run) == ("av1", "Lavc63.1.102 av1_nvenc")
    ((argv, options),) = calls
    assert argv[0] == "ffprobe"
    assert argv[-1] == str(path)
    timeout = options["timeout"]
    assert isinstance(timeout, (int, float))
    assert 0 < timeout < 3600


def test_the_command_names_each_problem_and_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(check_clip_codecs.fp, "fingerprints", lambda _: {"anim_x": "0"})
    monkeypatch.setattr(
        check_clip_codecs.fp, "read_encoders", lambda: {"anim_x": "av1_nvenc"}
    )
    monkeypatch.setattr(
        check_clip_codecs.assets_dir, "clips_dir", lambda: _clips(tmp_path)
    )
    monkeypatch.setattr(check_clip_codecs, "probe", lambda *_, **__: ("vp9", ""))
    assert check_clip_codecs.main([]) == 1
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 4
    assert all(line.startswith("::error::anim_x") for line in lines)


def test_the_command_passes_when_every_clip_is_av1_from_its_encoder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(check_clip_codecs.fp, "fingerprints", lambda _: {"anim_x": "0"})
    monkeypatch.setattr(
        check_clip_codecs.fp, "read_encoders", lambda: {"anim_x": "av1_nvenc"}
    )
    monkeypatch.setattr(
        check_clip_codecs.assets_dir, "clips_dir", lambda: _clips(tmp_path)
    )
    monkeypatch.setattr(
        check_clip_codecs, "probe", lambda *_, **__: ("av1", "Lavc63.1.102 av1_nvenc")
    )
    assert check_clip_codecs.main([]) == 0
    assert capsys.readouterr().out == (
        "All 1 clips are AV1, from the encoder their manifest names.\n"
    )
