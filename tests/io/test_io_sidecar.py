#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the calibration sidecar: schema v1, auto-application, refusals."""

from __future__ import annotations

import decimal
import fractions
import json
import math
import os
import re
import stat
import sys
import types
import typing
from pathlib import Path
from typing import Any

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
    read_blocks,
    read_sidecar,
    sidecar_path,
    write,
    write_sidecar,
)
from phonometry.io._sidecar import SIDECAR_SCHEMA, SIDECAR_VERSION

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


def test_labels_that_do_not_fit_the_audio_are_refused_naming_the_sidecar(
    tmp_path: Path,
) -> None:
    """Written before the audio, the sidecar cannot be held to its channels.

    Every reader then refused it building the signal, in a message that named
    neither the sidecar nor the file.
    """
    audio = tmp_path / "stereo.wav"
    write_sidecar(audio, 1.0, channel_labels=("only one",))
    write(audio, np.zeros((2, 8)), FS)
    message = (
        f"{sidecar_path(audio)}: sidecar gives 1 channel label, and its audio has "
        "2 channels"
    )
    for reader in (read, lambda path: read_blocks(path, 4)):
        with pytest.raises(ValueError, match=re.escape(message)) as caught:
            reader(audio)
        assert str(caught.value) == message
    copy = tmp_path / "copy.wav"
    with pytest.raises(ValueError, match=re.escape(message)):
        convert(audio, copy)
    assert not copy.exists()
    assert not sidecar_path(copy).exists()


@pytest.mark.parametrize(
    ("labels", "given"),
    [(["left"], "1 label"), ([], "0 labels"), (["a", "b", "c"], "3 labels")],
    ids=["one", "none", "three"],
)
def test_labels_that_do_not_fit_the_audio_are_never_written(
    tmp_path: Path, labels: list[str], given: str
) -> None:
    """The good sidecar stays byte for byte, and the audio still reads."""
    audio = tmp_path / "stereo.wav"
    write(audio, np.zeros((2, 8)), FS)
    kept = write_sidecar(audio, 2.5, channel_labels=("left", "right"))
    before = kept.read_bytes()
    message = (
        f"channel_labels gives {given}, and {audio} has 2 channels: a sidecar "
        "gives one label to each channel of its audio"
    )
    with pytest.raises(ValueError, match=re.escape(message)) as caught:
        write_sidecar(audio, 2.5, channel_labels=labels)
    assert str(caught.value) == message
    assert kept.read_bytes() == before
    assert sorted(path.name for path in tmp_path.iterdir()) == [audio.name, kept.name]
    again = read(audio)
    assert again.calibration_factor == 2.5
    assert again.channel_labels == ("left", "right")


def test_labels_beside_a_file_no_reader_describes_are_written(tmp_path: Path) -> None:
    """A file that is not audio has no channels to hold the labels to."""
    audio = tmp_path / "notes.wav"
    audio.write_text("not audio", encoding="utf-8")
    write_sidecar(audio, 2.5, channel_labels=("left", "right", "centre"))
    got = read_sidecar(audio)
    assert got is not None
    assert got.channel_labels == ("left", "right", "centre")


def test_the_labels_a_writer_takes_are_annotated_as_it_documents() -> None:
    """A list of labels is taken, so a type checker takes it too.

    The annotation held a tuple alone, and a list passed as documented failed
    the type check of its caller. A text is still not labels, so the
    annotation names a list and not every sequence of texts.
    """
    for writer in (write_sidecar, _sidecar.sidecar_file):
        hint = typing.get_type_hints(writer)["channel_labels"]
        assert set(typing.get_args(hint)) == {tuple[str, ...], list[str], type(None)}


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


def _not_real(field: str, value: str, *, optional: bool = True) -> str:
    """The refusal of *value* for a numeric *field*, as the sidecar words it."""
    held = "a real number or None" if optional else "a real number"
    return (
        f"{field} must be {held}: an int or a float, or a NumPy integer or float, "
        f"0-d arrays included, and never a bool; got {value}"
    )


def _masked(field: str) -> str:
    """The refusal of a masked value for a numeric *field*."""
    return f"{field} is masked, and a masked value holds no number a sidecar can write"


#: Each value of a field no reader takes, and what the refusal says. A text
#: float() reads and a bool were written as a text and as true, and an integer
#: past every float escaped as an OverflowError; labels given as one text were
#: taken as one label for each character, and a number as labels escaped as a
#: TypeError. A Decimal, a Fraction, an array of one element that is not 0-d,
#: a complex number, a NumPy timedelta and an integer past 64 bits are not
#: real scalars Signal takes as a calibration factor, and Signal refuses a
#: masked value.
_NEVER_HELD = {
    "factor-text": (
        {"calibration_factor": "2.5"},
        _not_real("calibration_factor", "'2.5'", optional=False),
    ),
    "factor-bool": (
        {"calibration_factor": True},
        _not_real("calibration_factor", "True", optional=False),
    ),
    "factor-decimal": (
        {"calibration_factor": decimal.Decimal("2.5")},
        _not_real("calibration_factor", "Decimal('2.5')", optional=False),
    ),
    "factor-fraction": (
        {"calibration_factor": fractions.Fraction(5, 2)},
        _not_real("calibration_factor", "Fraction(5, 2)", optional=False),
    ),
    "factor-one-element-array": (
        {"calibration_factor": np.array([2.5])},
        _not_real("calibration_factor", "array([2.5])", optional=False),
    ),
    "factor-complex": (
        {"calibration_factor": np.complex128(2.5)},
        _not_real("calibration_factor", "np.complex128(2.5+0j)", optional=False),
    ),
    "factor-past-64-bits": (
        {"calibration_factor": 2**64},
        "calibration_factor is an integer past 64 bits, which no NumPy integer holds",
    ),
    "factor-past-floats": (
        {"calibration_factor": 10**400},
        "calibration_factor is an integer past 64 bits, which no NumPy integer holds",
    ),
    "factor-masked": (
        {"calibration_factor": np.ma.array(2.5, mask=True)},
        _masked("calibration_factor"),
    ),
    "spl-text": (
        {"reference_spl": "94"},
        _not_real("reference_spl", "'94'"),
    ),
    "spl-bool": (
        {"reference_spl": True},
        _not_real("reference_spl", "True"),
    ),
    "spl-decimal": (
        {"reference_spl": decimal.Decimal("94.5")},
        _not_real("reference_spl", "Decimal('94.5')"),
    ),
    "spl-past-floats": (
        {"reference_spl": 10**400},
        "reference_spl is an integer past 64 bits, which no NumPy integer holds",
    ),
    "spl-masked": (
        {"reference_spl": np.ma.masked},
        _masked("reference_spl"),
    ),
    "frequency-text": (
        {"calibrator_frequency": "1000"},
        _not_real("calibrator_frequency", "'1000'"),
    ),
    "frequency-bool": (
        {"calibrator_frequency": False},
        _not_real("calibrator_frequency", "False"),
    ),
    "frequency-timedelta": (
        {"calibrator_frequency": np.timedelta64(1000, "ms")},
        _not_real("calibrator_frequency", "np.timedelta64(1000,'ms')"),
    ),
    "frequency-past-floats": (
        {"calibrator_frequency": -(10**400)},
        "calibrator_frequency is an integer past 64 bits, which no NumPy integer holds",
    ),
    "frequency-masked": (
        {"calibrator_frequency": np.ma.array(1000.0, mask=True)},
        _masked("calibrator_frequency"),
    ),
    "labels-number": (
        {"channel_labels": 5},
        "channel_labels must be a tuple or a list of texts, or None; got 5",
    ),
    "labels-text": (
        {"channel_labels": "LR"},
        "channel_labels must be a tuple or a list of texts, or None; got 'LR'",
    ),
    "labels-set": (
        {"channel_labels": {"left"}},
        "channel_labels must be a tuple or a list of texts, or None; got {'left'}",
    ),
}


@pytest.mark.parametrize(
    ("fields", "message"), _NEVER_HELD.values(), ids=list(_NEVER_HELD)
)
def test_a_value_no_reader_takes_is_never_written(
    tmp_path: Path, fields: dict[str, Any], message: str
) -> None:
    """The good sidecar stays, and the audio beside it still reads calibrated."""
    audio = tmp_path / "meas.wav"
    write(audio, np.zeros(8), FS)
    kept = write_sidecar(audio, 2.5, reference_spl=94.0, channel_labels=("left",))
    before = kept.read_bytes()
    given: dict[str, Any] = {"calibration_factor": 2.5, **fields}
    with pytest.raises(ValueError, match=re.escape(message)) as caught:
        write_sidecar(audio, **given)
    assert str(caught.value) == message
    assert kept.read_bytes() == before
    assert sorted(path.name for path in tmp_path.iterdir()) == [audio.name, kept.name]
    assert read(audio).calibration_factor == 2.5
    with pytest.raises(ValueError, match=re.escape(message)):
        CalibrationSidecar(**given)


@pytest.mark.parametrize(
    "number",
    [
        94,
        94.0,
        np.float32(94.0),
        np.float16(94.0),
        np.int64(94),
        np.uint8(94),
        np.array(94.0),
        np.array(94),
        np.array(94.0, dtype=np.float32),
        np.ma.array(94.0),
    ],
    ids=[
        "int",
        "float",
        "float32",
        "float16",
        "int64",
        "uint8",
        "0-d-float-array",
        "0-d-int-array",
        "0-d-float32-array",
        "0-d-masked-array-with-nothing-masked",
    ],
)
def test_a_real_number_of_any_type_is_kept_as_a_float(
    tmp_path: Path, number: float
) -> None:
    """What a record holds is what JSON writes and the reader reads back.

    Each is a number Signal takes as a calibration factor, a masked array with
    nothing masked among them, and the 0-d arrays and the NumPy numbers were
    written before the fields were checked.
    """
    record = CalibrationSidecar(
        calibration_factor=number,
        reference_spl=number,
        calibrator_frequency=number,
        channel_labels=["left", "right"],
    )
    for value in (
        record.calibration_factor,
        record.reference_spl,
        record.calibrator_frequency,
    ):
        assert type(value) is float
        assert value == 94.0
    assert record.channel_labels == ("left", "right")
    hash(record)
    audio = tmp_path / "meas.wav"
    write_sidecar(
        audio,
        number,
        reference_spl=number,
        calibrator_frequency=number,
        channel_labels=["left", "right"],
    )
    got = read_sidecar(audio)
    assert got is not None
    assert (got.calibration_factor, got.reference_spl, got.calibrator_frequency) == (
        94.0,
        94.0,
        94.0,
    )
    assert got.channel_labels == ("left", "right")


@pytest.mark.parametrize(
    ("signal", "message"),
    [
        (
            Signal(data=np.zeros(8), fs=FS, calibration_factor=True),
            _not_real("calibration_factor", "True", optional=False),
        ),
        (
            Signal(data=np.zeros(8), fs=FS, calibration_factor=np.array([2.5])),
            _not_real("calibration_factor", "array([2.5])", optional=False),
        ),
        (
            Signal(
                data=np.zeros(8),
                fs=FS,
                calibration_factor=2.5,
                channel_labels=("x" * 2_000_000,),
            ),
            "the sidecar these fields make is 2000",
        ),
        (
            Signal(
                data=np.zeros(8),
                fs=FS,
                calibration_factor=2.5,
                channel_labels=(1,),  # type: ignore[arg-type]
            ),
            "channel_labels must be text; got 1",
        ),
    ],
    ids=["factor-bool", "factor-one-element-array", "past-a-mebibyte", "label-number"],
)
def test_a_signal_no_sidecar_holds_is_refused_before_its_audio_is_written(
    tmp_path: Path, signal: Signal, message: str
) -> None:
    """The audio is never left without the sidecar it was asked to carry."""
    with pytest.raises(ValueError, match=re.escape(message)):
        write(tmp_path / "meas.wav", signal, sidecar=True)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "factor",
    [np.array(2.5), np.float32(2.5), np.int64(3)],
    ids=["0-d-array", "float32", "int64"],
)
def test_a_signal_calibrated_by_a_numpy_number_writes_its_sidecar(
    tmp_path: Path, factor: float
) -> None:
    """Signal takes the factor, so the sidecar written with it takes it too."""
    audio = tmp_path / "meas.wav"
    write(audio, Signal(np.full(8, 0.25), FS, calibration_factor=factor), sidecar=True)
    again = read(audio)
    assert type(again.calibration_factor) is float
    assert again.calibration_factor == float(factor)


def _padded_model(size: int) -> str:
    """A calibrator model that makes the sidecar of factor 2.5 *size* bytes long."""
    base = len(_sidecar.sidecar_file(2.5, calibrator_model=""))
    return "x" * (size - base)


@pytest.mark.parametrize(
    "fields",
    [
        {"calibrator_model": "x" * 2_000_000},
        {"calibrator_model": "\u00e9" * 600_000},
        {"channel_labels": ("x" * 2_000_000,)},
    ],
    ids=["model", "model-of-two-byte-letters", "label"],
)
def test_a_sidecar_past_what_a_reader_takes_is_never_written(
    tmp_path: Path, fields: dict[str, Any]
) -> None:
    """Written over a good one, it would stop every read of the audio beside it.

    The limit counts the bytes of the file, so a letter UTF-8 writes in two
    bytes counts twice.
    """
    audio = tmp_path / "meas.wav"
    write(audio, np.zeros(8), FS)
    kept = write_sidecar(audio, 2.5, channel_labels=("left",))
    before = kept.read_bytes()
    with pytest.raises(ValueError, match="the sidecar these fields make is") as caught:
        write_sidecar(audio, 2.5, **fields)
    assert str(caught.value).endswith(
        "bytes, and a calibration sidecar is at most 1048576 bytes (1 MiB), past "
        "which read_sidecar refuses it"
    )
    assert kept.read_bytes() == before
    assert sorted(path.name for path in tmp_path.iterdir()) == [audio.name, kept.name]
    assert read(audio).calibration_factor == 2.5


def test_a_sidecar_of_exactly_what_a_reader_takes_is_written_and_read_back(
    tmp_path: Path,
) -> None:
    """Whatever the writer writes, the reader reads back, and one byte more is refused."""
    audio = tmp_path / "meas.wav"
    model = _padded_model(_sidecar._MAX_BYTES)
    kept = write_sidecar(audio, 2.5, calibrator_model=model)
    assert kept.stat().st_size == _sidecar._MAX_BYTES
    got = read_sidecar(audio)
    assert got is not None
    assert got.calibrator_model == model
    before = kept.read_bytes()
    with pytest.raises(ValueError, match="is 1048577 bytes, and a calibration sidecar"):
        write_sidecar(audio, 2.5, calibrator_model=model + "x")
    assert kept.read_bytes() == before


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


def _is_read_only(path: str | os.PathLike[str]) -> bool:
    """Whether the file at *path* has lost its write bit, as Windows's flag does."""
    try:
        return not Path(path).stat().st_mode & stat.S_IWRITE
    except FileNotFoundError:
        return False


def _as_on_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    """Files as Windows keeps them: a read-only one is not replaced or removed."""
    monkeypatch.setattr(json_input, "_WINDOWS", True)
    replace, unlink = os.replace, os.unlink

    def windows_replace(source: str, target: str) -> None:
        if _is_read_only(target):
            raise PermissionError(13, "Access is denied", str(target))
        replace(source, target)

    def windows_unlink(path: str, *, dir_fd: int | None = None) -> None:
        if _is_read_only(path):
            raise PermissionError(13, "Access is denied", str(path))
        unlink(path, dir_fd=dir_fd)

    monkeypatch.setattr(os, "replace", windows_replace)
    monkeypatch.setattr(os, "unlink", windows_unlink)


def test_a_read_only_sidecar_is_replaced_and_stays_read_only(tmp_path: Path) -> None:
    """On POSIX by its bits, and on Windows by its read-only flag."""
    audio = tmp_path / "meas.wav"
    kept = write_sidecar(audio, 2.5)
    kept.chmod(stat.S_IREAD)
    write_sidecar(audio, 4.0)
    got = read_sidecar(audio)
    assert got is not None
    assert got.calibration_factor == 4.0
    assert _is_read_only(kept)
    assert sorted(path.name for path in tmp_path.iterdir()) == [kept.name]
    kept.chmod(stat.S_IREAD | stat.S_IWRITE)


def test_a_read_only_sidecar_is_replaced_as_windows_needs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The flag is cleared for the rename and set on the new file.

    Giving the new file the flag before the rename, as POSIX is given its
    bits, left Windows unable either to replace the old file or to remove the
    new one, which stayed beside it.
    """
    audio = tmp_path / "meas.wav"
    kept = write_sidecar(audio, 2.5)
    kept.chmod(stat.S_IREAD)
    _as_on_windows(monkeypatch)
    write_sidecar(audio, 4.0)
    got = read_sidecar(audio)
    assert got is not None
    assert got.calibration_factor == 4.0
    assert _is_read_only(kept)
    assert sorted(path.name for path in tmp_path.iterdir()) == [kept.name]
    kept.chmod(stat.S_IREAD | stat.S_IWRITE)


def test_a_rename_windows_refuses_leaves_the_old_sidecar_as_it_was(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Its bytes, its read-only flag, and no file beside it."""
    audio = tmp_path / "meas.wav"
    kept = write_sidecar(audio, 2.5)
    before = kept.read_bytes()
    kept.chmod(stat.S_IREAD)
    _as_on_windows(monkeypatch)

    def in_use(source: str, target: str) -> None:
        raise PermissionError(32, "The file is being used by another process", target)

    monkeypatch.setattr(os, "replace", in_use)
    with pytest.raises(PermissionError, match="used by another process"):
        write_sidecar(audio, 4.0)
    assert kept.read_bytes() == before
    assert _is_read_only(kept)
    assert sorted(path.name for path in tmp_path.iterdir()) == [kept.name]
    kept.chmod(stat.S_IREAD | stat.S_IWRITE)


def test_a_flag_windows_will_not_set_again_leaves_the_sidecar_replaced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The file is in place, so the write succeeded, and it is left writable.

    Raised, the failure told the caller the write had failed although the new
    sidecar had already replaced the old one.
    """
    audio = tmp_path / "meas.wav"
    kept = write_sidecar(audio, 2.5)
    kept.chmod(stat.S_IREAD)
    _as_on_windows(monkeypatch)
    chmod = os.chmod

    def read_only_refused(
        path: str, mode: int, *, follow_symlinks: bool = True
    ) -> None:
        if not mode & stat.S_IWRITE:
            raise PermissionError(5, "Access is denied", str(path))
        chmod(path, mode, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(os, "chmod", read_only_refused)
    assert write_sidecar(audio, 4.0) == kept
    got = read_sidecar(audio)
    assert got is not None
    assert got.calibration_factor == 4.0
    assert not _is_read_only(kept)
    assert sorted(path.name for path in tmp_path.iterdir()) == [kept.name]


def test_a_hard_link_to_a_read_only_sidecar_loses_its_flag_on_windows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The flag belongs to the file, and it is cleared on the file for the rename.

    The link keeps the old calibration, as on POSIX, and the sidecar itself
    stays read-only.
    """
    audio = tmp_path / "meas.wav"
    kept = write_sidecar(audio, 2.5)
    linked = tmp_path / "copy.json"
    try:
        os.link(kept, linked)
    except OSError:
        pytest.skip("this file system has no hard links")
    kept.chmod(stat.S_IREAD)
    _as_on_windows(monkeypatch)
    write_sidecar(audio, 4.0)
    assert json.loads(linked.read_text(encoding="utf-8"))["calibration_factor"] == 2.5
    assert not _is_read_only(linked)
    assert _is_read_only(kept)
    kept.chmod(stat.S_IREAD | stat.S_IWRITE)


def test_a_new_file_left_behind_is_named_on_the_error_that_stopped_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The failure of the write is raised, not the failure to clean up after it."""
    audio = tmp_path / "meas.wav"
    kept = write_sidecar(audio, 2.5)

    def full_disk(fd: int) -> None:
        raise OSError(28, "No space left on device", str(fd))

    def unremovable(path: str, *, dir_fd: int | None = None) -> None:
        raise PermissionError(13, "Access is denied", str(path))

    monkeypatch.setattr(os, "fsync", full_disk)
    monkeypatch.setattr(os, "unlink", unremovable)
    with pytest.raises(OSError, match="No space left on device") as caught:
        write_sidecar(audio, 4.0)
    monkeypatch.undo()
    (left,) = [path for path in tmp_path.iterdir() if path != kept]
    assert caught.value.__notes__ == [
        f"{left} could not be removed and is left behind: "
        f"[Errno 13] Access is denied: {str(left)!r}"
    ]


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
