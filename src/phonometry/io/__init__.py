#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Files: measurement audio, its calibration sidecar and catalogues of materials.

Every function here treats an audio file as a measurement record rather than
as material to be played back, which fixes the defaults: the native sample
rate is kept (no resampling on load), channels are never mixed down, samples
are never normalized, and integer PCM is scaled by exactly :math:`2^{B-1}`
into float64 -- a power of two, so the scaling is exact in binary floating
point, and a constant that cancels out of every calibrated level because the
calibrator tone is read through the same path (the derivation lives with the
WAV reader's source).

:func:`read` returns a :class:`Signal`: the samples as ``(channels, samples)``
float64 together with the sample rate, the calibration, the channel labels,
the ``bext`` broadcast provenance (EBU Tech 3285) and the origin record --
one immutable object that any ``(x, fs, ...)`` function of the library
accepts today via :func:`numpy.asarray`. The base install reads every linear
WAV a sound level meter or field recorder writes (PCM 16/24/32-bit, IEEE
float, ``WAVE_FORMAT_EXTENSIBLE``, RF64/BW64 past 4 GiB); the ``[audio]``
extra (python-soundfile, which bundles the LGPL libsndfile) adds FLAC, AIFF,
Ogg/Opus and MP3, and lossy sources raise :class:`LossyCompressionWarning`
because a level computed from a lossy codec is not metrologically defensible.

:func:`info` answers from the headers alone -- format, rate, channels, valid
bits, duration, ``bext``, cue points -- without decoding a single sample, so
it is safe on a 12-hour RF64. :func:`read_blocks` streams what :func:`read`
would return, one :class:`Signal` per block, into the library's stateful
filters. :func:`write` produces WAV/BWF (and FLAC with the extra) with exact
integer codes, loud clipping (:class:`ClippingWarning`), optional TPDF dither
at 16 bits, a ``bext`` chunk written field by field, and never a silent
normalization. :func:`convert` moves a measurement between lossless
containers with samples, provenance and sidecar intact, and the calibration
travels in a versioned JSON sidecar (:class:`CalibrationSidecar`) next to the
audio, where the audio formats themselves have no field for it.

The rows of the library's published tables of materials are data read from a
file too, and the type they share lives here: :class:`CatalogueRow`, with
:class:`BandedRow` for a row that prints one value per frequency band. Every
``PUBLISHED_*`` catalogue of every package hands out subclasses of it, so a
row keeps the same hedges (a range, a bound, a word, a value converted from
the unit the page prints, a cell carried from another row) and says what
its source claims for each cell through :meth:`CatalogueRow.basis_of`, one of
:data:`CATALOGUE_BASES`. A row checks itself when it is built, whether a
packaged table or a caller builds it, and :class:`CatalogueError` is what it
raises for a cell nothing downstream can read: a number that is not finite
or is text, a hedge on a field the row does not have, a value beside a hedge
that says there is none, a density below zero. A packaged table raises it
too for text that is not strict JSON or a table missing its citation.
:meth:`CatalogueRow.from_printed` builds a row from the cells its page prints
and fills what follows from them, which is how every packaged catalogue is
built; :meth:`CatalogueRow.printed_fields` gives those cells back, and
:meth:`BandedRow.values_at` reads a banded row at an array of frequencies.

The library publishes no manufacturer's data, so a caller's own data sheets,
declarations of performance and test reports live in a catalogue file of
their own, which :func:`read_catalogue` reads into rows of the same classes:
a versioned JSON document with its :class:`Provenance` (the kind of document,
its version, the day it was consulted, the laboratory and the report), each
cell named as the field it fills or in another unit of the same kind, and
every hedge the packaged tables use. What comes back is a :class:`Catalogue`,
a read-only mapping keyed like the packaged ones that joins a ``PUBLISHED_*``
catalogue with ``|`` and never lets one row replace another. Every problem in
a file is raised at once in one :class:`CatalogueError`, each
:class:`CatalogueIssue` with the JSON pointer to it, and what is only worth a
second look rides on the catalogue as a note with one
:class:`CatalogueWarning`. :func:`parse_catalogue` reads the same from text or
a mapping in memory, and :func:`write_catalogue` writes rows, a packaged
table among them, as a file that reads back into the same rows. Nothing the
file names is ever imported, and nothing it holds is kept anywhere but in the
objects handed back.
"""

from __future__ import annotations

from .._internal.catalogue import (
    CATALOGUE_BASES,
    PROVENANCE_KINDS,
    BandedRow,
    CatalogueError,
    CatalogueIssue,
    CatalogueRow,
    Provenance,
)
from ._backends import LossyCompressionWarning, info, read
from ._blocks import read_blocks
from ._catalogue import (
    Catalogue,
    CatalogueWarning,
    parse_catalogue,
    read_catalogue,
    write_catalogue,
)
from ._chunks import BroadcastMetadata, CuePoint
from ._convert import convert
from ._sidecar import (
    CalibrationSidecar,
    read_sidecar,
    sidecar_path,
    write_sidecar,
)
from ._signal import Signal, SignalOrigin
from ._wav import AudioFileInfo
from ._write import ClippingWarning, write

__all__ = [
    "CATALOGUE_BASES",
    "PROVENANCE_KINDS",
    "AudioFileInfo",
    "BandedRow",
    "BroadcastMetadata",
    "CalibrationSidecar",
    "Catalogue",
    "CatalogueError",
    "CatalogueIssue",
    "CatalogueRow",
    "CatalogueWarning",
    "ClippingWarning",
    "CuePoint",
    "LossyCompressionWarning",
    "Provenance",
    "Signal",
    "SignalOrigin",
    "convert",
    "info",
    "parse_catalogue",
    "read",
    "read_blocks",
    "read_catalogue",
    "read_sidecar",
    "sidecar_path",
    "write",
    "write_catalogue",
    "write_sidecar",
]
