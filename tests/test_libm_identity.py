#  Copyright (c) 2026. Jose Manuel Requena Plens
"""glibc's build is read from the ISA level its ``libm`` declares it needs.

:func:`libm_identity.glibc_built_for_x86_64_v3` decides whether glibc carries
a variant without FMA from the ``GNU_PROPERTY_X86_ISA_1_NEEDED`` property of
the mapped ``libm``, so the tests below hand the reader minimal 64-bit ELF
objects whose note says x86-64-v3, the baseline or nothing, the way glibc
writes it, and hold the reading of the real library here to ``readelf``'s.
"""

from __future__ import annotations

import platform
import re
import shutil
import struct
import subprocess
from typing import TYPE_CHECKING

import libm_identity
import pytest

if TYPE_CHECKING:
    from pathlib import Path

#: ``PT_GNU_PROPERTY`` and ``PT_NOTE``, the segments the property is read from.
_PT_GNU_PROPERTY = 0x6474E553
_PT_NOTE = 4
#: ``PT_LOAD``, a segment that holds no note.
_PT_LOAD = 1

#: ``GNU_PROPERTY_X86_ISA_1_NEEDED`` and ``GNU_PROPERTY_X86_FEATURE_1_AND``,
#: the second the IBT and SHSTK marking that precedes it in glibc's note.
_ISA_1_NEEDED = 0xC0008002
_FEATURE_1_AND = 0xC0000002

#: The ISA bits ``readelf`` names, one per level from bit 0.
_LEVEL_BITS = {
    "x86-64-baseline": 1 << 0,
    "x86-64-v2": 1 << 1,
    "x86-64-v3": 1 << 2,
    "x86-64-v4": 1 << 3,
}

#: What glibc built for x86-64-v3 declares, and what its baseline build does.
_V3 = 0b0111
_BASELINE = 0b0001


def _padded(data: bytes, alignment: int) -> bytes:
    return data + b"\0" * (-len(data) % alignment)


def _note(name: bytes, kind: int, descriptor: bytes, alignment: int = 8) -> bytes:
    header = struct.pack("<III", len(name), len(descriptor), kind)
    return _padded(header + name, alignment) + _padded(descriptor, alignment)


def _property_note(*properties: tuple[int, int]) -> bytes:
    descriptor = b"".join(
        _padded(struct.pack("<III", kind, 4, value), 8) for kind, value in properties
    )
    return _note(b"GNU\0", 5, descriptor)


def _elf(
    *segments: tuple[int, bytes, int], machine: int = 62, elf_class: int = 2
) -> bytes:
    """A 64-bit little-endian ELF image holding each (type, data, alignment)."""
    table = 64
    data_start = table + 56 * len(segments)
    headers = b""
    contents = b""
    for kind, data, alignment in segments:
        offset = data_start + len(contents)
        headers += struct.pack(
            "<IIQQQQQQ",
            kind,
            4,
            offset,
            offset,
            offset,
            len(data),
            len(data),
            alignment,
        )
        contents += _padded(data, 8)
    ident = b"\x7fELF" + bytes([elf_class, 1, 1]) + b"\0" * 9
    header = struct.pack(
        "<16sHHIQQQIHHHHHH",
        ident,
        3,
        machine,
        1,
        0,
        table,
        0,
        0,
        64,
        56,
        len(segments),
        64,
        0,
        0,
    )
    return header + headers + contents


def _glibc_libm_note(needed: int) -> bytes:
    """The note glibc's ``libm.so.6`` carries, marking IBT and SHSTK first."""
    return _property_note((_FEATURE_1_AND, 0b11), (_ISA_1_NEEDED, needed))


def _build_id() -> bytes:
    return _note(b"GNU\0", 3, bytes(range(20)))


def test_a_build_for_x86_64_v3_declares_that_level() -> None:
    note = _glibc_libm_note(_V3)
    image = _elf((_PT_GNU_PROPERTY, note, 8), (_PT_NOTE, note, 8))
    assert libm_identity.x86_isa_levels_needed(image) == _V3


def test_a_build_for_the_baseline_declares_the_baseline() -> None:
    note = _glibc_libm_note(_BASELINE)
    image = _elf((_PT_GNU_PROPERTY, note, 8), (_PT_NOTE, note, 8))
    assert libm_identity.x86_isa_levels_needed(image) == _BASELINE


@pytest.mark.parametrize(
    ("needed", "v3"),
    [(0b0001, False), (0b0011, False), (0b0111, True), (0b1111, True)],
)
def test_the_predicate_says_v3_from_that_level_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, needed: int, v3: bool
) -> None:
    library = tmp_path / "libm.so.6"
    library.write_bytes(_elf((_PT_GNU_PROPERTY, _glibc_libm_note(needed), 8)))
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    monkeypatch.setattr(platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(libm_identity, "_glibc_version", lambda: (2, 43))
    monkeypatch.setattr(libm_identity, "loaded_libm", lambda: library)
    assert libm_identity.glibc_built_for_x86_64_v3() is v3


def test_the_note_is_read_from_pt_note_without_pt_gnu_property() -> None:
    notes = _build_id() + _glibc_libm_note(_V3)
    image = _elf((_PT_LOAD, b"\0" * 32, 4096), (_PT_NOTE, notes, 8))
    assert libm_identity.x86_isa_levels_needed(image) == _V3


def test_pt_gnu_property_is_read_before_pt_note() -> None:
    image = _elf(
        (_PT_NOTE, _glibc_libm_note(_BASELINE), 8),
        (_PT_GNU_PROPERTY, _glibc_libm_note(_V3), 8),
    )
    assert libm_identity.x86_isa_levels_needed(image) == _V3


def test_a_note_segment_a_64_bit_loader_skips_is_skipped() -> None:
    image = _elf((_PT_NOTE, _glibc_libm_note(_V3), 4))
    assert libm_identity.x86_isa_levels_needed(image) is None


@pytest.mark.parametrize(
    "image",
    [
        _elf((_PT_GNU_PROPERTY, _property_note((_FEATURE_1_AND, 0b11)), 8)),
        _elf((_PT_NOTE, _build_id(), 8)),
        _elf((_PT_NOTE, _note(b"XYZ\0", 5, b"\0" * 16), 8)),
        _elf(),
        _elf((_PT_GNU_PROPERTY, _glibc_libm_note(_V3), 8), machine=183),
        _elf((_PT_GNU_PROPERTY, _glibc_libm_note(_V3), 8), elf_class=1),
        _elf((_PT_GNU_PROPERTY, _glibc_libm_note(_V3), 8))[:100],
        b"#!/bin/sh\n",
        b"",
    ],
    ids=[
        "feature-only",
        "build-id-only",
        "other-owner",
        "no-segments",
        "aarch64",
        "elf32",
        "truncated",
        "script",
        "empty",
    ],
)
def test_an_object_that_declares_no_level_reads_as_none(image: bytes) -> None:
    assert libm_identity.x86_isa_levels_needed(image) is None


def test_an_unreadable_library_is_no_build_for_v3(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    monkeypatch.setattr(platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(libm_identity, "_glibc_version", lambda: (2, 43))
    monkeypatch.setattr(libm_identity, "loaded_libm", lambda: tmp_path / "absent")
    assert libm_identity.glibc_built_for_x86_64_v3() is False


@pytest.mark.parametrize(
    ("name", "is_libm"),
    [
        ("libm.so.6", True),
        ("libm-2.31.so", True),
        ("libm.so", True),
        ("libmvec.so.1", False),
        ("libmagic.so.1", False),
        ("libm.so.6 (deleted)", False),
    ],
)
def test_the_libm_file_name(*, name: str, is_libm: bool) -> None:
    assert bool(libm_identity._LIBM_FILE_NAME.fullmatch(name)) is is_libm


@pytest.mark.parametrize(
    ("v3", "tunables", "pinned"),
    [
        (False, "", True),
        (False, libm_identity.WITHOUT_FMA, False),
        (True, "", True),
        (True, libm_identity.WITHOUT_FMA, True),
    ],
)
def test_a_mask_leaves_a_build_for_v3_on_the_pinned_routines(
    monkeypatch: pytest.MonkeyPatch, *, v3: bool, tunables: str, pinned: bool
) -> None:
    monkeypatch.setattr(libm_identity, "glibc_on_x86_64_with_fma", lambda: True)
    monkeypatch.setattr(libm_identity, "glibc_built_for_x86_64_v3", lambda: v3)
    monkeypatch.setenv(libm_identity.TUNABLES, tunables)
    assert libm_identity.runs_the_pinned_routines() is pinned


def _real_glibc_libm() -> Path:
    if not libm_identity.glibc_on_x86_64_with_fma():
        pytest.skip("reads the libm of glibc on an x86-64 processor with FMA")
    library = libm_identity.loaded_libm()
    assert library is not None, "glibc's libm is not mapped in this process"
    return library


def test_the_real_libm_is_found_and_read() -> None:
    library = _real_glibc_libm()
    assert library.is_file()
    needed = libm_identity.x86_isa_levels_needed(library.read_bytes())
    built_for_v3 = needed is not None and needed >= _LEVEL_BITS["x86-64-v3"]
    assert libm_identity.glibc_built_for_x86_64_v3() is built_for_v3


def test_the_real_libm_reads_as_readelf_reads_it() -> None:
    library = _real_glibc_libm()
    readelf = shutil.which("readelf")
    if readelf is None:
        pytest.skip("needs binutils' readelf to read the note independently")
    # Fixed argv, no shell; the path is the library this process mapped
    shown = subprocess.run(
        [readelf, "--notes", "--wide", str(library)],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    ).stdout
    line = re.search(r"x86 ISA needed: ([^\n]*)", shown)
    expected = (
        None
        if line is None
        else sum(_LEVEL_BITS[name.strip()] for name in line.group(1).split(","))
    )
    assert libm_identity.x86_isa_levels_needed(library.read_bytes()) == expected
