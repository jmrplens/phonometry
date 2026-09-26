#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""The calibration sidecar: a versioned JSON file beside the audio.

No audio container carries a microphone calibration. The equipment survey
behind this module found the same pattern everywhere: sound level meters
export linear WAV and keep the sensitivity in a proprietary companion
(NTi's report text, Svantek's .svl/.svt), and ``bext`` has no calibration
field -- its loudness values are EBU R 128 *programme* loudness, and
pressing them into service as a sensitivity would corrupt both meanings.
Seismology met the identical problem decades ago and settled it with a
standardised sidecar (the StationXML inventory beside the miniSEED
waveform, in obspy's model); this module is that answer at phonometry's
scale: a small versioned JSON written beside the audio file, so the one
number that turns digital full scale into pascals travels with the
recording through filesystems, archives and colleagues, in a format any
tool can read.

**Naming.** The sidecar of ``measurement.wav`` is
``measurement.wav.phonometry.json``: the full audio filename plus a
suffix that names the producing library. Appending (rather than swapping
the extension) keeps files that differ only by extension from sharing a
sidecar, and the ``.phonometry.json`` tail makes the file self-describing
in a directory listing and collision-proof against generic ``.json``
companions other tools drop beside recordings.

**Schema, version 1.** A single JSON object; every key is always present
(``null`` when unknown), so consumers parse one fixed shape:

======================  ======================================================
Key                     Meaning
======================  ======================================================
``schema``              The constant ``"phonometry-calibration"``; a reader
                        must refuse a file claiming anything else.
``schema_version``      Integer, this layout is ``1``. Readers accept equal
                        or older versions and refuse newer ones loudly (a
                        newer writer may have changed a key's meaning).
``phonometry_version``  The library version that wrote the file, a text or
                        ``null``, for forensics; never used to gate reading.
``calibration_factor``  The digital-to-pascal multiplier (0 dBFS = RMS
                        1.0 convention of ``signals.levels``), as derived
                        by :func:`phonometry.metrology.sensitivity` from a
                        calibrator recording read through the same reader.
                        Required, finite and positive.
``reference_spl``       The calibrator's known SPL the factor was derived
                        against (dB SPL, typically 94.0 per IEC 60942), or
                        ``null``.
``calibrator``          Object ``{"frequency": Hz | null, "model": str |
                        null}`` describing the calibrator tone (nominally
                        1000 Hz, where all IEC 61672 weightings are 0 dB).
``channel_labels``      Array of one label per channel, or ``null``. When
                        present it overrides labels derived from the
                        file's channel mask: the sidecar is curated by
                        whoever made the measurement, the mask by whatever
                        firmware wrote the file.
======================  ======================================================

:func:`phonometry.io.read` looks for the sidecar automatically and applies
its calibration when the caller did not pass one explicitly -- the
explicit argument always wins, because the person at the keyboard knows
more than a file on disk -- so the pair "WAV + sidecar" behaves as a
calibrated measurement with no ceremony at the call site.
"""

from __future__ import annotations

import json
import math
import numbers
import os
from dataclasses import dataclass
from pathlib import Path

from .._internal.json_input import (
    LONE_SURROGATE,
    MAX_NESTING,
    NotRegularError,
    TooLargeError,
    nesting_past,
    not_regular_at,
    read_at_most,
    text_location,
    write_beside,
)

#: The schema identifier and the layout version this module writes.
SIDECAR_SCHEMA = "phonometry-calibration"
SIDECAR_VERSION = 1

#: The tail appended to the full audio filename to name its sidecar.
_SIDECAR_TAIL = ".phonometry.json"

#: The largest sidecar read. One holds a few hundred bytes, and a label for
#: each of a thousand channels keeps it under a hundred kibibytes; the bound
#: keeps a file at the sidecar's name that grows while it is read from being
#: read without end on every read of the audio.
_MAX_BYTES = 1024 * 1024


@dataclass(frozen=True)
class CalibrationSidecar:
    """The calibration record of one audio file (schema v1, module docstring).

    ``calibration_factor`` is the digital-to-pascal multiplier and the
    only mandatory field; the rest document how it was obtained
    (``reference_spl``, ``calibrator_frequency``, ``calibrator_model``)
    and what the channels are (``channel_labels``). ``phonometry_version``
    records the writing library version. Every number is finite, as JSON
    writes no other, and the model, every label and the version are text
    UTF-8 can write, so that the record read from one sidecar can be written
    to another.
    """

    calibration_factor: float
    reference_spl: float | None = None
    calibrator_frequency: float | None = None
    calibrator_model: str | None = None
    channel_labels: tuple[str, ...] | None = None
    phonometry_version: str | None = None

    def __post_init__(self) -> None:
        factor = float(self.calibration_factor)
        if not (math.isfinite(factor) and factor > 0):
            msg = (
                f"calibration_factor must be finite and positive; got "
                f"{self.calibration_factor!r}"
            )
            raise ValueError(msg)
        for name in ("reference_spl", "calibrator_frequency"):
            value = getattr(self, name)
            # JSON has no NaN and no infinity: a sidecar that wrote one would
            # be read by no strict reader, this module's among them.
            if isinstance(value, numbers.Real) and not math.isfinite(value):
                msg = f"{name} must be finite or None; got {value!r}"
                raise ValueError(msg)
        texts = [
            ("calibrator_model", self.calibrator_model),
            ("phonometry_version", self.phonometry_version),
        ]
        texts += [("channel_labels", label) for label in self.channel_labels or ()]
        for name, text in texts:
            # A JSON escape spells half a UTF-16 pair alone, and a text that
            # holds it fails the write only once the old sidecar is emptied.
            lone = LONE_SURROGATE.search(text) if isinstance(text, str) else None
            if lone is not None:
                msg = (
                    f"{name} holds a lone surrogate, U+{ord(lone.group()):04X}, "
                    f"in {text!r}, which is not text UTF-8 can write"
                )
                raise ValueError(msg)


def sidecar_path(audio_path: str | Path) -> Path:
    """The sidecar filename of an audio file (see the module docstring)."""
    audio = Path(audio_path)
    return audio.with_name(audio.name + _SIDECAR_TAIL)


def writable_sidecar(audio_path: str | Path) -> Path:
    """The file a sidecar of *audio_path* is written to, refused if it cannot be.

    A link at the sidecar's name is followed, so that a sidecar kept once and
    linked beside several recordings is updated where it is kept. The file is
    a regular file or not there yet: anything else at the name is refused
    before a byte is written, since a pipe opened for writing waits for a
    reader, which may never come, and a device or a directory holds no
    sidecar. The writers of the audio ask first, so that the audio is not
    written beside a sidecar that cannot be.

    :raises ValueError: for a pipe, a device, a socket or a directory at the
        sidecar's name, behind a link or not.
    :raises OSError: as the file system raises it, untouched.
    """
    target = sidecar_path(audio_path)
    kind = not_regular_at(target)
    if kind is not None:
        msg = (
            f"{target}: sidecar is {kind}, and a calibration sidecar is "
            "written only to a regular file"
        )
        raise ValueError(msg)
    return Path(os.path.realpath(target)) if target.is_symlink() else target


def put_sidecar(audio_path: str | Path, data: bytes) -> Path:
    """Put the bytes of a sidecar at *audio_path*'s, never opening the name.

    The bytes go to a new file beside the sidecar's file, renamed into place,
    so that a reader finds the old sidecar or the new one whole.

    :return: The sidecar's name, :func:`sidecar_path` of *audio_path*.
    :raises ValueError: for what :func:`writable_sidecar` refuses.
    :raises OSError: as the file system raises it, untouched.
    """
    write_beside(writable_sidecar(audio_path), data)
    return sidecar_path(audio_path)


def write_sidecar(
    audio_path: str | Path,
    calibration_factor: float,
    *,
    reference_spl: float | None = None,
    calibrator_frequency: float | None = None,
    calibrator_model: str | None = None,
    channel_labels: tuple[str, ...] | None = None,
) -> Path:
    """Write the calibration sidecar beside an audio file.

    Serialises schema v1 with every key present (the module docstring's
    table); an existing sidecar is replaced, which is the update semantics
    a recalibration wants. The audio file itself is never touched. The
    sidecar is written to a new file beside it and renamed into place, so a
    reader finds the old sidecar or the new one whole and the name itself is
    never opened for writing; a link at the name is followed to the file it
    names.

    :param audio_path: The audio file the sidecar belongs to (it need not
        exist yet; writing the sidecar first is fine).
    :param calibration_factor: Digital-to-pascal multiplier (required,
        finite, positive).
    :param reference_spl: The calibrator's known SPL, dB (e.g. 94.0).
    :param calibrator_frequency: The calibrator tone's nominal frequency,
        Hz (e.g. 1000.0).
    :param calibrator_model: Free-text calibrator identification.
    :param channel_labels: One label per channel of the audio file.
    :return: The path the sidecar was written to.
    :raises ValueError: for a factor that is not finite and positive, a
        reference SPL or a calibrator frequency that is not finite, a model
        or a label that holds a lone surrogate, or a pipe, a device, a socket
        or a directory at the sidecar's name, behind a link or not, before the
        file at the sidecar's name is touched.
    """
    from .._version import __version__

    record = CalibrationSidecar(
        calibration_factor=float(calibration_factor),
        reference_spl=reference_spl,
        calibrator_frequency=calibrator_frequency,
        calibrator_model=calibrator_model,
        channel_labels=channel_labels,
        phonometry_version=__version__,
    )
    payload = {
        "schema": SIDECAR_SCHEMA,
        "schema_version": SIDECAR_VERSION,
        "phonometry_version": record.phonometry_version,
        "calibration_factor": record.calibration_factor,
        "reference_spl": record.reference_spl,
        "calibrator": {
            "frequency": record.calibrator_frequency,
            "model": record.calibrator_model,
        },
        "channel_labels": (
            None if record.channel_labels is None else list(record.channel_labels)
        ),
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False)
    return put_sidecar(audio_path, (text + "\n").encode("utf-8"))


def _as_float(value: float, key: str, path: Path) -> float:
    """*value* as a float, refusing a JSON integer past every float."""
    try:
        return float(value)
    except OverflowError:
        msg = f"{path}: {key} is an integer too large for a float"
        raise ValueError(msg) from None


def _optional_number(
    payload: dict[str, object], key: str, path: Path, *, name: str = ""
) -> float | None:
    """The number at *key*, or ``None`` for null; *name* says it in a message.

    The decoder reads ``NaN``, ``Infinity`` and ``-Infinity``, which are not
    JSON, and each is refused here as no number a calibration holds.
    """
    name = name or key
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float):
        msg = f"{path}: {name} must be a number or null; got {value!r}"
        # ValueError keeps the module validation errors uniform.
        raise ValueError(msg)  # noqa: TRY004
    number = _as_float(value, name, path)
    if not math.isfinite(number):
        msg = f"{path}: {name} must be a finite number or null; got {value!r}"
        raise ValueError(msg)
    return number


def _sidecar_bytes(source: Path) -> bytes:
    """The sidecar's bytes, read to :data:`_MAX_BYTES` at most."""
    try:
        return read_at_most(source, _MAX_BYTES)
    except NotRegularError as exc:
        msg = (
            f"{source}: sidecar is {exc.kind}, and a calibration sidecar is "
            "read only from a regular file"
        )
        raise ValueError(msg) from None
    except TooLargeError as exc:
        held = (
            f"is {exc.size} bytes"
            if exc.size is not None
            else f"runs past {_MAX_BYTES} bytes"
        )
        msg = (
            f"{source}: sidecar {held}, and a calibration sidecar is at most "
            f"{_MAX_BYTES} bytes (1 MiB)"
        )
        raise ValueError(msg) from None


def _load_sidecar_payload(source: Path, raw: bytes) -> dict[str, object]:
    """Parse the sidecar's JSON and check its schema declaration."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        msg = f"{source}: sidecar is not UTF-8 text (byte {exc.start})"
        raise ValueError(msg) from None
    deep = nesting_past(text)
    if deep is not None:
        msg = (
            f"{source}: sidecar is not a calibration record: it nests deeper "
            f"than {MAX_NESTING} levels at {text_location(text, deep)}"
        )
        raise ValueError(msg)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        msg = f"{source}: sidecar is not valid JSON"
        raise ValueError(msg) from exc
    except ValueError as exc:
        # An integer longer than Python reads (sys.get_int_max_str_digits).
        msg = f"{source}: sidecar holds a number too long to read"
        raise ValueError(msg) from exc
    except RecursionError:
        # The count above keeps every text within the decoder's reach, unless
        # the caller is already deep in its own stack.
        msg = f"{source}: sidecar nests deeper than the decoder follows"
        raise ValueError(msg) from None
    if not isinstance(payload, dict) or payload.get("schema") != SIDECAR_SCHEMA:
        msg = (
            f"{source}: not a {SIDECAR_SCHEMA!r} sidecar; refusing to "
            "guess at its meaning"
        )
        raise ValueError(msg)
    version = payload.get("schema_version")
    if not isinstance(version, int) or isinstance(version, bool):
        msg = f"{source}: schema_version must be an integer"
        # ValueError keeps the module validation errors uniform.
        raise ValueError(msg)  # noqa: TRY004
    if version > SIDECAR_VERSION:
        msg = (
            f"{source}: sidecar schema version {version} is newer than the "
            f"version {SIDECAR_VERSION} this phonometry understands; "
            "upgrade phonometry to read it"
        )
        raise ValueError(msg)
    return payload


def _required_factor(payload: dict[str, object], source: Path) -> float:
    """The mandatory calibration factor, validated as a number."""
    factor = payload.get("calibration_factor")
    if isinstance(factor, bool) or not isinstance(factor, int | float):
        msg = f"{source}: calibration_factor must be a number; got {factor!r}"
        # ValueError keeps the module validation errors uniform.
        raise ValueError(msg)  # noqa: TRY004
    return _as_float(factor, "calibration_factor", source)


def _calibrator_fields(
    payload: dict[str, object], source: Path
) -> tuple[dict[str, object], str | None]:
    """The calibrator object (``{}`` for null) and its validated model."""
    calibrator = payload.get("calibrator")
    if calibrator is None:
        calibrator = {}
    if not isinstance(calibrator, dict):
        msg = f"{source}: calibrator must be an object or null"
        # ValueError keeps the module validation errors uniform.
        raise ValueError(msg)  # noqa: TRY004
    model = calibrator.get("model")
    if model is not None and not isinstance(model, str):
        msg = f"{source}: calibrator model must be a string or null"
        raise ValueError(msg)
    return calibrator, model


def _channel_labels(payload: dict[str, object], source: Path) -> tuple[str, ...] | None:
    """The channel labels as a tuple, or ``None`` when absent or null."""
    labels = payload.get("channel_labels")
    if labels is None:
        return None
    if not isinstance(labels, list) or not all(
        isinstance(label, str) for label in labels
    ):
        msg = f"{source}: channel_labels must be an array of strings or null"
        raise ValueError(msg)
    return tuple(labels)


def _version(payload: dict[str, object], source: Path) -> str | None:
    """The version that wrote the sidecar, a text or ``None`` for null.

    A number is refused, a ``NaN`` or an ``Infinity`` among them, so that no
    version is made up from what the file holds.
    """
    version = payload.get("phonometry_version")
    if version is not None and not isinstance(version, str):
        msg = f"{source}: phonometry_version must be a string or null; got {version!r}"
        raise ValueError(msg)
    return version


def _record(source: Path, raw: bytes) -> CalibrationSidecar:
    """The calibration record the sidecar's bytes *raw* hold, every field checked."""
    payload = _load_sidecar_payload(source, raw)
    factor = _required_factor(payload, source)
    calibrator, model = _calibrator_fields(payload, source)
    labels = _channel_labels(payload, source)
    reference_spl = _optional_number(payload, "reference_spl", source)
    frequency = _optional_number(
        calibrator, "frequency", source, name="calibrator frequency"
    )
    version = _version(payload, source)
    try:
        return CalibrationSidecar(
            calibration_factor=factor,
            reference_spl=reference_spl,
            calibrator_frequency=frequency,
            calibrator_model=model,
            channel_labels=labels,
            phonometry_version=version,
        )
    except ValueError as exc:
        msg = f"{source}: {exc}"
        raise ValueError(msg) from exc


def sidecar_bytes(audio_path: str | Path) -> bytes | None:
    """The bytes of an audio file's sidecar, read and checked, or ``None``.

    Read once and checked as :func:`read_sidecar` checks them, so that a copy
    of the sidecar carries the bytes that were checked, byte for byte.

    :raises ValueError: for everything :func:`read_sidecar` refuses.
    """
    source = sidecar_path(audio_path)
    if not source.exists():
        return None
    raw = _sidecar_bytes(source)
    _record(source, raw)
    return raw


def read_sidecar(audio_path: str | Path) -> CalibrationSidecar | None:
    """Read an audio file's calibration sidecar, if one exists.

    Returns ``None`` when there is no sidecar -- the common case, never an
    error. A file *at the sidecar's reserved name* that is not a valid
    phonometry calibration record raises instead of being ignored: a
    corrupted or foreign file squatting on ``*.phonometry.json`` beside a
    measurement is a problem to surface, not to read past (silently
    dropping it would silently drop the calibration).

    :param audio_path: The audio file whose sidecar to look for.
    :return: The parsed record, or ``None`` when no sidecar exists.
    :raises ValueError: If the sidecar exists but is not a regular file (a
        pipe, a device, a socket or a directory, behind a link or not), is
        larger than 1 MiB, is not UTF-8 JSON, nests deeper than 64 levels,
        does not declare this schema, was written by a newer schema version,
        or carries malformed fields: a number that is not finite, a version
        that is not text, or a text with a lone surrogate, among them.
    """
    source = sidecar_path(audio_path)
    if not source.exists():
        return None
    return _record(source, _sidecar_bytes(source))
