#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the calibration sidecar: schema v1, auto-application, refusals."""

from __future__ import annotations

import json
import math
import os
import re
import stat
import sys
import types
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest
from special_files import (
    SPECIAL_KINDS,
    make_special,
    raised_within,
    size_says_nothing,
)

from phonometry._internal import json_input
from phonometry.io import (
    CalibrationSidecar,
    Signal,
    _sidecar,
    convert,
    read,
    read_sidecar,
    sidecar_path,
    write,
    write_sidecar,
)
from phonometry.io._sidecar import SIDECAR_SCHEMA, SIDECAR_VERSION

if TYPE_CHECKING:
    from pathlib import Path

FS = 48000


def test_sidecar_name_appends_to_the_full_audio_filename() -> None:
    # Appending keeps take1.wav and take1.flac from sharing a sidecar.
    assert sidecar_path("m/take1.wav").name == "take1.wav.phonometry.json"
    assert sidecar_path("m/take1.flac").name == "take1.flac.phonometry.json"


def test_every_field_round_trips_through_the_json(tmp_path: Path) -> None:
    audio = tmp_path / "meas.wav"
    written_to = write_sidecar(
        audio,
        0.0123,
        reference_spl=94.0,
        calibrator_frequency=1000.0,
        calibrator_model="B&K 4231",
        channel_labels=("mic A", "mic B"),
    )
    assert written_to == sidecar_path(audio)
    got = read_sidecar(audio)
    assert got is not None
    assert got.calibration_factor == 0.0123
    assert got.reference_spl == 94.0
    assert got.calibrator_frequency == 1000.0
    assert got.calibrator_model == "B&K 4231"
    assert got.channel_labels == ("mic A", "mic B")
    assert got.phonometry_version is not None
    # The on-disk shape is the documented schema: fixed keys, always there.
    payload = json.loads(written_to.read_text())
    assert payload["schema"] == SIDECAR_SCHEMA
    assert payload["schema_version"] == SIDECAR_VERSION
    assert set(payload) == {
        "schema",
        "schema_version",
        "phonometry_version",
        "calibration_factor",
        "reference_spl",
        "calibrator",
        "channel_labels",
    }


def test_missing_sidecar_is_none_not_an_error(tmp_path: Path) -> None:
    assert read_sidecar(tmp_path / "lonely.wav") is None


def test_read_applies_the_sidecar_calibration(tmp_path: Path) -> None:
    audio = tmp_path / "meas.wav"
    write(audio, np.full(16, 0.25), FS, subtype="DOUBLE")
    write_sidecar(audio, 2.5, channel_labels=("outdoor mic",))
    sig = read(audio)
    assert sig.calibration_factor == 2.5
    assert sig.channel_labels == ("outdoor mic",)


def test_explicit_calibration_argument_beats_the_sidecar(
    tmp_path: Path,
) -> None:
    audio = tmp_path / "meas.wav"
    write(audio, np.full(16, 0.25), FS)
    write_sidecar(audio, 2.5)
    assert read(audio, calibration_factor=7.0).calibration_factor == 7.0


def test_mismatched_label_count_fails_loudly(tmp_path: Path) -> None:
    audio = tmp_path / "stereo.wav"
    write(audio, np.zeros((2, 8)), FS)
    write_sidecar(audio, 1.0, channel_labels=("only one",))
    with pytest.raises(
        ValueError,
        match=r"Signal: .*'channel_labels' .* must each carry one value per channel",
    ):
        read(audio)


def test_foreign_json_at_the_reserved_name_is_refused(tmp_path: Path) -> None:
    audio = tmp_path / "meas.wav"
    write(audio, np.zeros(8), FS)
    sidecar_path(audio).write_text('{"unrelated": true}')
    with pytest.raises(ValueError, match=r"not a 'phonometry-calibration' sidecar"):
        read(audio)


def test_newer_schema_versions_are_refused_by_name(tmp_path: Path) -> None:
    audio = tmp_path / "meas.wav"
    write_sidecar(audio, 1.0)
    target = sidecar_path(audio)
    payload = json.loads(target.read_text())
    payload["schema_version"] = SIDECAR_VERSION + 1
    target.write_text(json.dumps(payload))
    with pytest.raises(
        ValueError,
        match=r"sidecar schema version .* is newer than the version .* this phonometry",
    ):
        read_sidecar(audio)


def test_malformed_fields_are_refused(tmp_path: Path) -> None:
    audio = tmp_path / "meas.wav"
    target = sidecar_path(audio)
    base = {
        "schema": SIDECAR_SCHEMA,
        "schema_version": 1,
        "phonometry_version": None,
        "calibration_factor": 1.0,
        "reference_spl": None,
        "calibrator": None,
        "channel_labels": None,
    }
    for corruption, message in (
        ({"calibration_factor": "loud"}, "must be a number"),
        ({"schema_version": "1"}, "schema_version must be an integer"),
        ({"calibrator": 5}, "calibrator must be an object or null"),
        ({"calibrator": {"model": 5}}, "calibrator model must be a string or null"),
        (
            {"calibration_factor": -1.0},
            "calibration_factor must be finite and positive",
        ),
        ({"channel_labels": [1, 2]}, "array of strings"),
        ({"reference_spl": "94"}, "must be a number"),
    ):
        target.write_text(json.dumps(base | corruption))
        with pytest.raises(ValueError, match=message):
            read_sidecar(audio)
    target.write_text("{not json")
    with pytest.raises(ValueError, match="not valid JSON"):
        read_sidecar(audio)


def _sidecar_text(audio: Path, text: str | bytes) -> None:
    """Put *text* at the sidecar's name of *audio*."""
    target = sidecar_path(audio)
    if isinstance(text, bytes):
        target.write_bytes(text)
    else:
        target.write_text(text, encoding="utf-8")


def _valid_with(written: str) -> str:
    """The text of a valid sidecar, with the member *written* names as written."""
    key = written.partition(":")[0]
    held = f"{key}: {json.dumps(_valid()[json.loads(key)])}"
    text = json.dumps(_valid())
    assert held in text
    return text.replace(held, written)


def _valid() -> dict[str, Any]:
    return {
        "schema": SIDECAR_SCHEMA,
        "schema_version": 1,
        "phonometry_version": None,
        "calibration_factor": 1.0,
        "reference_spl": None,
        "calibrator": None,
        "channel_labels": None,
    }


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("[" * 100_000, "nests deeper than 64 levels at line 1, column 65"),
        (
            json.dumps(_valid()).replace(
                '"calibration_factor": 1.0', '"calibration_factor": 1' + "0" * 400
            ),
            "calibration_factor is an integer too large for a float",
        ),
        (
            json.dumps(_valid()).replace(
                '"reference_spl": null', '"reference_spl": 1' + "0" * 400
            ),
            "reference_spl is an integer too large for a float",
        ),
        (
            json.dumps(_valid()).replace(
                '"reference_spl": null', '"reference_spl": 1' + "0" * 5000
            ),
            "sidecar holds a number too long to read",
        ),
        (b'{"schema": "phonometry-calibration", "model": "Bru\xe9l"}', "not UTF-8"),
    ],
    ids=["nested", "factor-past-floats", "spl-past-floats", "digits", "latin-1"],
)
def test_a_sidecar_no_decoder_takes_is_refused_as_a_value_error(
    tmp_path: Path, text: str | bytes, message: str
) -> None:
    audio = tmp_path / "meas.wav"
    _sidecar_text(audio, text)
    with pytest.raises(ValueError, match=message) as caught:
        read_sidecar(audio)
    assert str(caught.value).count(str(sidecar_path(audio))) == 1


def test_a_decoder_out_of_stack_is_a_value_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A caller already deep in its own stack can still run the decoder out."""

    def out_of_stack(text: str) -> object:
        raise RecursionError(text[:10])

    decoder = types.SimpleNamespace(
        loads=out_of_stack, JSONDecodeError=json.JSONDecodeError
    )
    monkeypatch.setattr(_sidecar, "json", decoder)
    audio = tmp_path / "meas.wav"
    _sidecar_text(audio, "{}")
    with pytest.raises(ValueError, match="nests deeper than the decoder follows"):
        read_sidecar(audio)


def test_a_sidecar_past_one_mebibyte_is_refused(tmp_path: Path) -> None:
    audio = tmp_path / "meas.wav"
    text = json.dumps(_valid())
    _sidecar_text(audio, text + " " * (1024 * 1024 - len(text)))
    assert read_sidecar(audio) is not None
    _sidecar_text(audio, text + " " * (1024 * 1024 + 1 - len(text)))
    with pytest.raises(ValueError, match="sidecar is 1048577 bytes"):
        read_sidecar(audio)


def test_a_sidecar_that_holds_more_than_its_size_says_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A file of /proc says it holds nothing, and a file may grow as it is read."""
    audio = tmp_path / "meas.wav"
    _sidecar_text(audio, " " * (1024 * 1024 + 1))
    size_says_nothing(monkeypatch)
    with pytest.raises(ValueError, match="sidecar runs past 1048576 bytes"):
        read_sidecar(audio)


@pytest.mark.parametrize("kind", SPECIAL_KINDS)
def test_a_sidecar_that_is_no_regular_file_is_refused_without_waiting(
    kind: str, tmp_path: Path
) -> None:
    """A pipe no one writes to would keep the open waiting, /dev/zero the read."""
    audio = tmp_path / "meas.wav"
    target = sidecar_path(audio)
    what = make_special(kind, target)
    error = raised_within(
        lambda: read_sidecar(audio), pipe=target if kind == "pipe" else None
    )
    assert isinstance(error, ValueError)
    assert str(error) == (
        f"{target}: sidecar is {what}, and a calibration sidecar is read only "
        "from a regular file"
    )


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX pipes")
def test_reading_audio_beside_a_pipe_at_the_sidecars_name_does_not_wait(
    tmp_path: Path,
) -> None:
    """The caller names the audio, never the sidecar the reader looks for."""
    audio = tmp_path / "meas.wav"
    write(audio, np.zeros(8), FS)
    target = sidecar_path(audio)
    make_special("pipe", target)
    error = raised_within(lambda: read(audio), pipe=target)
    assert isinstance(error, ValueError)
    assert "sidecar is a named pipe (FIFO)" in str(error)


@pytest.mark.skipif(sys.platform == "win32", reason="symbolic links")
def test_a_link_to_a_sidecar_is_read(tmp_path: Path) -> None:
    kept = write_sidecar(tmp_path / "kept.wav", 2.5, reference_spl=94.0)
    audio = tmp_path / "meas.wav"
    sidecar_path(audio).symlink_to(kept)
    got = read_sidecar(audio)
    assert got is not None
    assert (got.calibration_factor, got.reference_spl) == (2.5, 94.0)


@pytest.mark.parametrize("kind", SPECIAL_KINDS)
def test_a_sidecar_is_never_written_to_what_is_no_regular_file(
    kind: str, tmp_path: Path
) -> None:
    """A pipe opened for writing waits for a reader, which may never come."""
    audio = tmp_path / "meas.wav"
    target = sidecar_path(audio)
    what = make_special(kind, target)
    error = raised_within(
        lambda: write_sidecar(audio, 2.5), pipe=target if kind == "pipe" else None
    )
    assert isinstance(error, ValueError)
    assert str(error) == (
        f"{target}: sidecar is {what}, and a calibration sidecar is written "
        "only to a regular file"
    )
    assert sorted(path.name for path in tmp_path.iterdir()) == [target.name]


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX pipes")
def test_writing_audio_with_a_sidecar_beside_a_pipe_writes_neither(
    tmp_path: Path,
) -> None:
    """The sidecar's name is asked first, so no audio is left without its sidecar."""
    audio = tmp_path / "cal.wav"
    target = sidecar_path(audio)
    make_special("pipe", target)
    calibrated = Signal(data=np.zeros(8), fs=FS, calibration_factor=3.5)
    error = raised_within(lambda: write(audio, calibrated, sidecar=True), pipe=target)
    assert isinstance(error, ValueError)
    assert "sidecar is a named pipe (FIFO)" in str(error)
    assert not audio.exists()


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX pipes")
def test_converting_beside_a_pipe_at_the_destinations_sidecar_writes_nothing(
    tmp_path: Path,
) -> None:
    source = tmp_path / "a.wav"
    write(source, np.zeros(8), FS)
    write_sidecar(source, 2.5)
    destination = tmp_path / "b.wav"
    target = sidecar_path(destination)
    make_special("pipe", target)
    error = raised_within(lambda: convert(source, destination), pipe=target)
    assert isinstance(error, ValueError)
    assert "sidecar is a named pipe (FIFO)" in str(error)
    assert not destination.exists()


def test_a_source_sidecar_no_reader_takes_stops_a_conversion_before_it_writes(
    tmp_path: Path,
) -> None:
    source = tmp_path / "a.wav"
    write(source, np.zeros(8), FS)
    _sidecar_text(source, _valid_with('"reference_spl": NaN'))
    destination = tmp_path / "b.wav"
    with pytest.raises(ValueError, match="reference_spl must be a finite number"):
        convert(source, destination)
    assert not destination.exists()
    assert not sidecar_path(destination).exists()


@pytest.mark.skipif(sys.platform == "win32", reason="symbolic links")
def test_a_sidecar_written_through_a_link_updates_the_file_it_names(
    tmp_path: Path,
) -> None:
    """A sidecar kept once and linked beside several recordings stays shared."""
    kept = write_sidecar(tmp_path / "kept.wav", 2.5)
    audio = tmp_path / "meas.wav"
    sidecar_path(audio).symlink_to(kept.name)
    assert write_sidecar(audio, 4.0) == sidecar_path(audio)
    assert sidecar_path(audio).is_symlink()
    got = read_sidecar(tmp_path / "kept.wav")
    assert got is not None
    assert got.calibration_factor == 4.0


def test_a_sidecar_that_fails_to_be_written_leaves_the_old_one_whole(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The new text goes to a file beside it, removed when the write fails."""
    audio = tmp_path / "meas.wav"
    kept = write_sidecar(audio, 2.5)
    before = kept.read_bytes()

    def full_disk(fd: int) -> None:
        raise OSError(28, "No space left on device", str(fd))

    monkeypatch.setattr(json_input.os, "fsync", full_disk)
    with pytest.raises(OSError, match="No space left on device"):
        write_sidecar(audio, 4.0)
    assert kept.read_bytes() == before
    assert sorted(path.name for path in tmp_path.iterdir()) == [kept.name]


@pytest.mark.parametrize(
    ("written", "message"),
    [
        (
            '"reference_spl": NaN',
            "reference_spl must be a finite number or null; got nan",
        ),
        (
            '"reference_spl": Infinity',
            "reference_spl must be a finite number or null; got inf",
        ),
        (
            '"reference_spl": -Infinity',
            "reference_spl must be a finite number or null; got -inf",
        ),
        (
            '"calibrator": {"frequency": NaN, "model": null}',
            "calibrator frequency must be a finite number or null; got nan",
        ),
        (
            '"calibrator": {"frequency": Infinity, "model": null}',
            "calibrator frequency must be a finite number or null; got inf",
        ),
        (
            '"calibration_factor": NaN',
            "calibration_factor must be finite and positive; got nan",
        ),
        (
            '"calibration_factor": Infinity',
            "calibration_factor must be finite and positive; got inf",
        ),
        ('"schema_version": NaN', "schema_version must be an integer"),
    ],
    ids=[
        "spl-nan",
        "spl-infinity",
        "spl-minus-infinity",
        "frequency-nan",
        "frequency-infinity",
        "factor-nan",
        "factor-infinity",
        "version-nan",
    ],
)
def test_a_number_that_is_not_finite_is_refused_by_name(
    tmp_path: Path, written: str, message: str
) -> None:
    """The decoder reads NaN and Infinity, which JSON does not have."""
    audio = tmp_path / "meas.wav"
    _sidecar_text(audio, _valid_with(written))
    with pytest.raises(ValueError, match=re.escape(message)) as caught:
        read_sidecar(audio)
    assert str(caught.value) == f"{sidecar_path(audio)}: {message}"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("reference_spl", math.nan),
        ("reference_spl", math.inf),
        ("calibrator_frequency", -math.inf),
    ],
)
def test_a_number_that_is_not_finite_is_never_written(
    tmp_path: Path, field: str, value: float
) -> None:
    """JSON has no such number, and the sidecar already there is kept."""
    audio = tmp_path / "meas.wav"
    kept = write_sidecar(audio, 2.5)
    before = kept.read_bytes()
    with pytest.raises(ValueError, match=f"{field} must be finite or None"):
        write_sidecar(audio, 2.5, **{field: value})
    assert kept.read_bytes() == before
    with pytest.raises(ValueError, match=f"{field} must be finite or None"):
        CalibrationSidecar(calibration_factor=1.0, **{field: value})


@pytest.mark.parametrize(
    ("written", "message"),
    [
        (
            '"calibrator": {"frequency": null, "model": "B\\ud800K"}',
            "calibrator_model holds a lone surrogate, U+D800, in 'B\\ud800K'",
        ),
        (
            '"channel_labels": ["left", "right\\udfff"]',
            "channel_labels holds a lone surrogate, U+DFFF, in 'right\\udfff'",
        ),
    ],
    ids=["model", "label"],
)
def test_a_text_with_a_lone_surrogate_is_refused_by_name(
    tmp_path: Path, written: str, message: str
) -> None:
    """A JSON escape spells half a UTF-16 pair, and no sidecar can write it back."""
    audio = tmp_path / "meas.wav"
    _sidecar_text(audio, _valid_with(written))
    with pytest.raises(ValueError, match=re.escape(message)):
        read_sidecar(audio)


@pytest.mark.parametrize(
    "fields",
    [{"calibrator_model": "B\ud800K"}, {"channel_labels": ("left", "right\udfff")}],
    ids=["model", "label"],
)
def test_a_text_with_a_lone_surrogate_is_never_written(
    tmp_path: Path, fields: dict[str, Any]
) -> None:
    """Writing it would fail only after the sidecar already there was emptied."""
    audio = tmp_path / "meas.wav"
    kept = write_sidecar(audio, 2.5, channel_labels=("left", "right"))
    before = kept.read_bytes()
    with pytest.raises(ValueError, match="holds a lone surrogate"):
        write_sidecar(audio, 2.5, **fields)
    assert kept.read_bytes() == before


@pytest.mark.parametrize(
    ("written", "message"),
    [
        ('"phonometry_version": NaN', "got nan"),
        ('"phonometry_version": Infinity', "got inf"),
        ('"phonometry_version": -Infinity', "got -inf"),
        ('"phonometry_version": 1e400', "got inf"),
        ('"phonometry_version": 4', "got 4"),
        ('"phonometry_version": ["4.0"]', "got ['4.0']"),
    ],
    ids=["nan", "infinity", "minus-infinity", "past-floats", "integer", "list"],
)
def test_a_version_that_is_not_text_is_refused_by_name(
    tmp_path: Path, written: str, message: str
) -> None:
    """No version is made up from a number, as the text 'nan' once was."""
    audio = tmp_path / "meas.wav"
    _sidecar_text(audio, _valid_with(written))
    with pytest.raises(ValueError, match=re.escape(message)) as caught:
        read_sidecar(audio)
    assert str(caught.value) == (
        f"{sidecar_path(audio)}: phonometry_version must be a string or null; {message}"
    )


def test_a_version_with_a_lone_surrogate_is_refused_by_name(tmp_path: Path) -> None:
    audio = tmp_path / "meas.wav"
    _sidecar_text(audio, _valid_with('"phonometry_version": "4.0\\ud800"'))
    with pytest.raises(ValueError, match=re.escape("U+D800")) as caught:
        read_sidecar(audio)
    assert str(caught.value) == (
        f"{sidecar_path(audio)}: phonometry_version holds a lone surrogate, "
        "U+D800, in '4.0\\ud800', which is not text UTF-8 can write"
    )
    with pytest.raises(ValueError, match="phonometry_version holds a lone surrogate"):
        CalibrationSidecar(calibration_factor=1.0, phonometry_version="4.0\ud800")


def test_the_dataclass_itself_rejects_a_nonpositive_factor() -> None:
    with pytest.raises(
        ValueError, match=r"calibration_factor must be finite and positive"
    ):
        CalibrationSidecar(calibration_factor=0.0)


@pytest.mark.parametrize(
    ("fields", "message"),
    [
        (
            {"phonometry_version": math.nan},
            "phonometry_version must be text or None; got nan",
        ),
        (
            {"phonometry_version": float("1e400")},
            "phonometry_version must be text or None; got inf",
        ),
        (
            {"phonometry_version": 4.0},
            "phonometry_version must be text or None; got 4.0",
        ),
        (
            {"calibrator_model": 1000},
            "calibrator_model must be text or None; got 1000",
        ),
        ({"channel_labels": ("left", None)}, "channel_labels must be text; got None"),
    ],
    ids=[
        "version-nan",
        "version-past-floats",
        "version-number",
        "model-number",
        "label-none",
    ],
)
def test_the_dataclass_itself_refuses_a_text_that_is_not_text(
    fields: dict[str, Any], message: str
) -> None:
    """A version, a model and a label are text, as the reader takes them."""
    with pytest.raises(ValueError, match=re.escape(message)):
        CalibrationSidecar(calibration_factor=1.0, **fields)


def _not_utf8_audio(tmp_path: Path) -> Path:
    """An audio file whose name holds a byte UTF-8 has no character for."""
    audio = tmp_path / os.fsdecode(b"\xff-meas.wav")
    try:
        sidecar_path(audio).touch()
    except (OSError, UnicodeEncodeError):
        pytest.skip("this file system takes only names that are text")
    sidecar_path(audio).unlink()
    return audio


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX names are bytes")
@pytest.mark.parametrize("reader", ["read_sidecar", "read"])
def test_a_sidecar_beside_a_name_that_is_not_utf8_is_named_by_its_escape(
    tmp_path: Path, reader: str
) -> None:
    """The byte is decoded as a lone surrogate, which no refusal can print."""
    audio = _not_utf8_audio(tmp_path)
    if reader == "read":
        write(audio, np.zeros(8), FS)
    _sidecar_text(audio, "not json")
    call = read if reader == "read" else read_sidecar
    with pytest.raises(ValueError, match="sidecar is not valid JSON") as caught:
        call(audio)
    assert str(caught.value) == (
        f"{tmp_path}{os.sep}\\udcff-meas.wav.phonometry.json: sidecar is not valid JSON"
    )
    str(caught.value).encode("utf-8")


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX names and pipes")
def test_a_pipe_beside_a_name_that_is_not_utf8_is_named_by_its_escape(
    tmp_path: Path,
) -> None:
    audio = _not_utf8_audio(tmp_path)
    target = sidecar_path(audio)
    make_special("pipe", target)
    error = raised_within(lambda: write_sidecar(audio, 2.5), pipe=target)
    assert isinstance(error, ValueError)
    assert str(error) == (
        f"{tmp_path}{os.sep}\\udcff-meas.wav.phonometry.json: sidecar is a "
        "named pipe (FIFO), and a calibration sidecar is written only to a "
        "regular file"
    )
    str(error).encode("utf-8")


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permission bits")
def test_a_sidecar_written_again_keeps_its_permission_bits(tmp_path: Path) -> None:
    """A sidecar kept from other users stays so when it is recalibrated."""
    audio = tmp_path / "meas.wav"
    kept = write_sidecar(audio, 2.5)
    kept.chmod(0o640)
    write_sidecar(audio, 4.0)
    assert stat.S_IMODE(kept.stat().st_mode) == 0o640


def test_a_hard_link_to_a_sidecar_keeps_the_calibration_it_had(
    tmp_path: Path,
) -> None:
    """The sidecar is replaced rather than written into, as its docstring says."""
    audio = tmp_path / "meas.wav"
    kept = write_sidecar(audio, 2.5)
    linked = tmp_path / "copy.json"
    try:
        os.link(kept, linked)
    except OSError:
        pytest.skip("this file system has no hard links")
    write_sidecar(audio, 4.0)
    assert json.loads(linked.read_text(encoding="utf-8"))["calibration_factor"] == 2.5
    got = read_sidecar(audio)
    assert got is not None
    assert got.calibration_factor == 4.0


def test_write_sidecar_true_requires_a_calibrated_signal(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError, match=r"sidecar=True needs a Signal with a calibration_factor"
    ):
        write(tmp_path / "x.wav", np.zeros(8), FS, sidecar=True)
    uncalibrated = Signal(data=np.zeros(8), fs=FS)
    with pytest.raises(
        ValueError, match=r"sidecar=True needs a Signal with a calibration_factor"
    ):
        write(tmp_path / "x.wav", uncalibrated, sidecar=True)


def test_write_sidecar_true_writes_the_signals_calibration(
    tmp_path: Path,
) -> None:
    sig = Signal(
        data=np.full(16, 0.125),
        fs=FS,
        calibration_factor=3.5,
        channel_labels=("courtyard",),
    )
    audio = tmp_path / "cal.wav"
    write(audio, sig, subtype="DOUBLE", sidecar=True)
    assert sidecar_path(audio).exists()
    reread = read(audio)
    assert reread.calibration_factor == 3.5
    assert reread.channel_labels == ("courtyard",)
