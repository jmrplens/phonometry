#  Copyright (c) 2026. Jose Manuel Requena Plens
"""glibc's build and its reading of a mask are read from what its objects are.

:func:`libm_identity.glibc_built_for_x86_64_v3` decides whether glibc carries
a variant without FMA from the ``GNU_PROPERTY_X86_ISA_1_NEEDED`` property of
the ``libm`` :mod:`math` calls, so the tests below hand the reader minimal
64-bit ELF objects whose note says x86-64-v3, the baseline or nothing, the
way glibc writes it, hold the reading of the real library here to
``readelf``'s wherever ``readelf`` knows the property note, and hold the
``libm`` and the loader read to the objects that define ``exp`` and
``__tls_get_addr``, found by absolute paths and by relative ones, with
planted ones of the other build mapped ahead of them. Only the tests that
look a symbol up need :mod:`ctypes`; on an interpreter without it the others
run, as :mod:`libm_identity` does there.
:func:`libm_identity.mask_reading` reads how a loader reads
``GLIBC_TUNABLES`` from the names its parser carries, so the tests hand it
loader images spelt as each glibc spells them and hold the reading of this
process's loader to what each mask does to a child's ``exp``.
"""

from __future__ import annotations

import contextlib
import functools
import os
import platform
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import libm_identity
import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

#: ``PT_GNU_PROPERTY`` and ``PT_NOTE``, the segments the property is read from.
_PT_GNU_PROPERTY = 0x6474E553
_PT_NOTE = 4
#: ``PT_LOAD``, a segment that holds no note.
_PT_LOAD = 1

#: ``GNU_PROPERTY_X86_ISA_1_NEEDED`` and ``GNU_PROPERTY_X86_FEATURE_1_AND``,
#: the second the IBT and SHSTK marking that precedes it in glibc's note.
_ISA_1_NEEDED = 0xC0008002
_FEATURE_1_AND = 0xC0000002
#: ``GNU_PROPERTY_X86_FEATURE_2_USED`` and ``GNU_PROPERTY_X86_ISA_1_USED``,
#: which Fedora's and AlmaLinux's libms carry after the needed levels.
_FEATURE_2_USED = 0xC0010001
_ISA_1_USED = 0xC0010002
#: ``NT_GNU_PROPERTY_TYPE_0``, the type of the GNU note that carries them.
_NT_GNU_PROPERTY_TYPE_0 = 5

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
    return _note(b"GNU\0", _NT_GNU_PROPERTY_TYPE_0, descriptor)


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
    ("name", "is_loader"),
    [
        ("ld-linux-x86-64.so.2", True),
        ("ld-2.31.so", True),
        ("ld-2.28.so", True),
        ("ld-linux.so.2", False),
        ("ld-musl-x86_64.so.1", False),
        ("libdl.so.2", False),
    ],
)
def test_the_loader_file_name(*, name: str, is_loader: bool) -> None:
    assert bool(libm_identity._LOADER_FILE_NAME.fullmatch(name)) is is_loader


def _loader(*, tunable: str, usable: bool, drops: bool) -> bytes:
    """The strings a glibc loader's mask parser carries, among some it does not."""
    names = [b"glibc.malloc.check", tunable.encode(), b"AVX", b"FMA", b"AVX2", b"FMA4"]
    if usable:
        names += [b"AVX_Usable", b"FMA_Usable", b"AVX2_Usable", b"FMA4_Usable"]
    if drops:
        names.append(b"WARNING: ld.so: invalid GLIBC_TUNABLES `%s': ignored.\n")
    return b"\x7fELF" + b"\0".join(names) + b"\0"


#: Loader images spelt as each glibc's: 2.28 as Debian 10 builds it, 2.31 as
#: Ubuntu 20.04 does, 2.35 as Ubuntu 22.04 does (and RHEL 8's 2.28, which
#: carries the 2.32 parser), and 2.39 as Ubuntu 24.04 does, as every later
#: one reads it.
_LOADERS = {
    "2.28": _loader(tunable="glibc.tune.hwcaps", usable=True, drops=False),
    "2.31": _loader(tunable="glibc.cpu.hwcaps", usable=True, drops=False),
    "2.35": _loader(tunable="glibc.cpu.hwcaps", usable=False, drops=False),
    "2.39": _loader(tunable="glibc.cpu.hwcaps", usable=False, drops=True),
}


def _reading(glibc: str) -> libm_identity.MaskReading:
    """How the loader of *glibc* reads the mask, or any spelling for ``any``."""
    if glibc == "any":
        return libm_identity.ANY_READING
    reading = libm_identity.mask_reading(_LOADERS[glibc])
    assert reading is not None
    return reading


@pytest.mark.parametrize(
    ("glibc", "tunable", "names", "drops"),
    [
        ("2.28", "glibc.tune.hwcaps", {"FMA_Usable", "AVX2_Usable"}, False),
        ("2.31", "glibc.cpu.hwcaps", {"FMA_Usable", "AVX2_Usable"}, False),
        ("2.35", "glibc.cpu.hwcaps", {"FMA", "AVX2"}, False),
        ("2.39", "glibc.cpu.hwcaps", {"FMA", "AVX2"}, True),
    ],
)
def test_the_loader_says_how_it_reads_the_mask(
    *, glibc: str, tunable: str, names: set[str], drops: bool
) -> None:
    assert libm_identity.mask_reading(_LOADERS[glibc]) == libm_identity.MaskReading(
        tunables=frozenset({tunable}),
        fma_variant_names=frozenset(names),
        drops_ill_formed=drops,
    )


@pytest.mark.parametrize(
    "image",
    [b"", b"\x7fELF", b"glibc.cpu.hwcap_mask\0", b"glibc.cpu.hwcapsx\0FMA_Usable\0"],
    ids=["empty", "header-only", "another-tunable", "a-longer-name"],
)
def test_a_loader_that_names_no_mask_tunable_says_nothing(image: bytes) -> None:
    assert libm_identity.mask_reading(image) is None


@pytest.mark.parametrize("found", ["none", "absent", "no-mask-tunable"])
def test_a_loader_that_cannot_be_read_counts_a_mask_in_any_spelling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, found: str
) -> None:
    planted = tmp_path / "ld-linux-x86-64.so.2"
    planted.write_bytes(b"\x7fELF\0glibc.cpu.hwcap_mask\0")
    loaders = {"none": None, "absent": tmp_path / "absent", "no-mask-tunable": planted}
    monkeypatch.setattr(libm_identity, "loaded_loader", lambda: loaders[found])
    assert libm_identity.mask_reading_here() == libm_identity.ANY_READING


@pytest.mark.parametrize(
    ("v3", "tunables", "pinned"),
    [
        (False, "", True),
        (False, libm_identity.WITHOUT_FMA, False),
        (False, "glibc.cpu.hwcaps=-AVX", True),
        (True, "", True),
        (True, libm_identity.WITHOUT_FMA, True),
    ],
)
def test_a_mask_leaves_a_build_for_v3_on_the_pinned_routines(
    monkeypatch: pytest.MonkeyPatch, *, v3: bool, tunables: str, pinned: bool
) -> None:
    monkeypatch.setattr(libm_identity, "glibc_on_x86_64_with_fma", lambda: True)
    monkeypatch.setattr(libm_identity, "glibc_built_for_x86_64_v3", lambda: v3)
    monkeypatch.setattr(libm_identity, "mask_reading_here", lambda: _reading("2.39"))
    monkeypatch.setenv(libm_identity.TUNABLES, tunables)
    assert libm_identity.runs_the_pinned_routines() is pinned


@pytest.mark.parametrize(
    ("version", "pinned"),
    [((2, 17), False), ((2, 28), False), ((2, 29), True), ((2, 43), True)],
)
def test_the_pinned_routines_start_at_glibc_2_29(
    monkeypatch: pytest.MonkeyPatch, *, version: tuple[int, int], pinned: bool
) -> None:
    """glibc 2.29 is the first to ship ARM's ``exp``, ``log`` and ``pow``.

    The commits that put them in place of IBM's routines came after the 2.28
    release, so on an x86-64 processor with FMA and AVX2, unmasked, glibc 2.28
    does not run the routines the pins spell and 2.29 does.
    """
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    monkeypatch.setattr(platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(libm_identity, "_glibc_version", lambda: version)
    monkeypatch.setattr(
        libm_identity, "_cpu_flags", lambda: frozenset({"fma", "avx2", "sse2"})
    )
    monkeypatch.setattr(libm_identity, "glibc_built_for_x86_64_v3", lambda: False)
    monkeypatch.setattr(libm_identity, "mask_reading_here", lambda: _reading("2.39"))
    monkeypatch.delenv(libm_identity.TUNABLES, raising=False)
    assert libm_identity.glibc_on_x86_64_with_fma() is pinned
    assert libm_identity.runs_the_pinned_routines() is pinned


#: What each glibc did to a child's ``exp`` under a mask, as
#: ``(glibc, tunables, masks)``, and for ``any``, a loader that cannot be read,
#: whether the mask counts: wherever one of those glibcs reads it so.
_MASK_ROWS = (
    ("2.39", "", False),
    ("2.39", "glibc.malloc.check=3", False),
    ("2.39", "glibc.cpu.hwcaps=-FMA", True),
    ("2.39", "glibc.cpu.hwcaps=-AVX2", True),
    ("2.39", "glibc.cpu.hwcaps=-AVX,-FMA", True),
    ("2.39", "glibc.malloc.check=3:glibc.cpu.hwcaps=-AVX2", True),
    ("2.39", "glibc.cpu.hwcaps=-AVX", False),
    ("2.39", "glibc.cpu.hwcaps=-FMA4", False),
    ("2.39", "glibc.cpu.hwcaps=-AVX,-FMA4", False),
    ("2.39", "glibc.cpu.hwcaps=-fma", False),
    ("2.39", "glibc.cpu.hwcaps=-FMA_Usable", False),
    ("2.39", "glibc.cpu.hwcaps=-AVX2_Usable", False),
    ("2.39", "glibc.tune.hwcaps=-FMA", False),
    ("2.35", "glibc.cpu.hwcaps=-FMA", True),
    ("2.35", "glibc.cpu.hwcaps=-FMA_Usable", False),
    ("2.31", "glibc.cpu.hwcaps=-FMA_Usable", True),
    ("2.31", "glibc.cpu.hwcaps=-AVX2_Usable", True),
    ("2.31", "glibc.cpu.hwcaps=-FMA,-AVX2", False),
    ("2.31", "glibc.cpu.hwcaps=-AVX_Usable", False),
    ("2.31", "glibc.tune.hwcaps=-FMA_Usable", False),
    ("2.28", "glibc.tune.hwcaps=-FMA_Usable", True),
    ("2.28", "glibc.tune.hwcaps=-FMA", False),
    ("2.28", "glibc.cpu.hwcaps=-FMA_Usable", False),
    ("2.39", "glibc.cpu.hwcaps=-FMA:glibc.tune.hwcaps=-AVX", True),
    ("2.39", "glibc.tune.hwcaps=-FMA_Usable:glibc.cpu.hwcaps=-SSE4_1", False),
    ("2.28", "glibc.cpu.hwcaps=-FMA:glibc.tune.hwcaps=-AVX", False),
    ("2.28", "glibc.tune.hwcaps=-FMA_Usable:glibc.cpu.hwcaps=-SSE4_1", True),
    ("2.39", "glibc.cpu.hwcaps= -FMA", False),
    ("2.39", "glibc.cpu.hwcaps=-FMA ", False),
    ("2.39", " glibc.cpu.hwcaps=-FMA", False),
    ("2.39", "glibc.cpu.hwcaps =-FMA", False),
    ("2.39", "glibc.cpu.hwcaps=-FMA:glibc.cpu.hwcaps=-SSE4_1", False),
    ("2.39", "glibc.cpu.hwcaps=-SSE4_1:glibc.cpu.hwcaps=-FMA", True),
    ("2.31", "glibc.cpu.hwcaps=-FMA_Usable:glibc.cpu.hwcaps=-SSE4_1", False),
    ("2.39", "glibc.cpu.hwcaps=-FMA:junk", False),
    ("2.39", "glibc.cpu.hwcaps=-FMA,-X=1", False),
    ("2.39", "glibc.cpu.hwcaps=-FMA:glibc.malloc.check=3=1", False),
    ("2.39", "glibc.cpu.hwcaps=-FMA::", False),
    ("2.39", "junk:glibc.cpu.hwcaps=-FMA", True),
    ("2.35", "glibc.cpu.hwcaps=-FMA:junk", True),
    ("2.35", "glibc.cpu.hwcaps=-FMA,-X=1", True),
    ("2.31", "glibc.cpu.hwcaps=-FMA_Usable::", True),
    ("2.28", libm_identity.WITHOUT_FMA, True),
    ("2.31", libm_identity.WITHOUT_FMA, True),
    ("2.35", libm_identity.WITHOUT_FMA, True),
    ("2.39", libm_identity.WITHOUT_FMA, True),
    ("any", "glibc.cpu.hwcaps=-FMA_Usable", True),
    ("any", "glibc.tune.hwcaps=-FMA", True),
    ("any", "glibc.cpu.hwcaps=-FMA:junk", True),
    ("any", "glibc.cpu.hwcaps=-AVX,-AVX_Usable", False),
    ("any", "glibc.cpu.hwcaps=-FMA:glibc.tune.hwcaps=-AVX", True),
    ("any", "glibc.tune.hwcaps=-FMA_Usable:glibc.cpu.hwcaps=-SSE4_1", True),
    ("any", "glibc.cpu.hwcaps=-FMA:glibc.cpu.hwcaps=-SSE4_1", False),
)


@pytest.mark.parametrize(("glibc", "tunables", "masks"), _MASK_ROWS)
def test_a_mask_counts_as_the_glibc_reading_it_reads_it(
    *, glibc: str, tunables: str, masks: bool
) -> None:
    """Each row of a glibc is what it did to a child's ``exp`` under the mask.

    The rows were measured on Debian 10 (2.28), Ubuntu 20.04 (2.31), 22.04
    (2.35) and 24.04 (2.39); the test below holds the loader of this process
    to the same rule. A loader reads one tunable, so a mask in one stays a
    mask whatever setting of the other follows it, and a loader that cannot
    be read counts it in either.
    """
    assert libm_identity.masks_the_fma_variant(tunables, _reading(glibc)) is masks


def test_a_loader_that_cannot_be_read_counts_every_mask_a_glibc_reads() -> None:
    """No mask any glibc above reads leaves a process held to the pins.

    :data:`libm_identity.ANY_READING` stands for a loader whose spelling is
    not known, so of every value in the rows above that one of those glibcs
    reads as a mask, it reads the same.
    """
    missed = [
        tunables
        for _, tunables, _ in _MASK_ROWS
        if any(
            libm_identity.masks_the_fma_variant(tunables, _reading(glibc))
            for glibc in _LOADERS
        )
        and not libm_identity.masks_the_fma_variant(tunables, libm_identity.ANY_READING)
    ]
    assert missed == []


#: A child's :func:`math.exp` on a grid of the double range, whose digest
#: tells glibc's FMA variant from the others.
_EXP_DIGEST = (
    "import hashlib, math, struct\n"
    "values = [math.exp(-700.0 + 1400.0 * k / 20000) for k in range(20000)]\n"
    "print(hashlib.sha256(struct.pack('<20000d', *values)).hexdigest())\n"
)


@functools.cache
def _exp_digest_under(tunables: str) -> str:
    """The digest of the ``exp`` of a child started under *tunables*, or none."""
    environment = {
        key: value for key, value in os.environ.items() if key != libm_identity.TUNABLES
    }
    if tunables:
        environment[libm_identity.TUNABLES] = tunables
    # Fixed argv, no shell, no user input
    return subprocess.run(
        [sys.executable, "-I", "-c", _EXP_DIGEST],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
        timeout=60,
    ).stdout.strip()


@pytest.mark.parametrize(
    "tunables",
    [
        "glibc.cpu.hwcaps=-FMA",
        "glibc.cpu.hwcaps=-AVX2",
        "glibc.cpu.hwcaps=-FMA_Usable",
        "glibc.cpu.hwcaps=-AVX2_Usable",
        "glibc.tune.hwcaps=-FMA_Usable",
        "glibc.cpu.hwcaps=-AVX",
        "glibc.cpu.hwcaps=-FMA4",
        "glibc.cpu.hwcaps=-AVX_Usable",
        "glibc.cpu.hwcaps=-fma",
        "glibc.cpu.hwcaps= -FMA,-AVX2_Usable",
        "glibc.cpu.hwcaps=-FMA,-FMA_Usable:glibc.cpu.hwcaps=-SSE4_1",
        "glibc.cpu.hwcaps=-SSE4_1:glibc.cpu.hwcaps=-FMA,-FMA_Usable",
        "glibc.cpu.hwcaps=-FMA,-FMA_Usable:junk",
        "glibc.cpu.hwcaps=-FMA,-FMA_Usable:glibc.tune.hwcaps=-AVX",
        "glibc.tune.hwcaps=-FMA_Usable:glibc.cpu.hwcaps=-AVX",
        libm_identity.WITHOUT_FMA,
    ],
)
def test_a_mask_counts_where_it_moves_glibc_off_its_fma_variant(
    monkeypatch: pytest.MonkeyPatch, tunables: str
) -> None:
    """This process counts a mask as taking it off the pins when it does.

    A child started under the mask runs the same loader, which reads the mask
    in its own spelling and ignores the others, as written, keeping the last
    setting, and from glibc 2.39 drops the whole variable over an ill-formed
    entry. So the pinned routines count as running under the mask exactly
    when the child's ``exp`` is an unmasked child's: a mask this glibc does not
    read leaves the bit-for-bit tests running, and one it reads skips them.
    Read as a loader that cannot be read, a mask that moved the child skips
    them too.
    """
    if not libm_identity.glibc_on_x86_64_with_fma():
        pytest.skip(
            "needs glibc 2.29 or later, the routines the pins spell, on an x86-64 "
            "processor with FMA and AVX2"
        )
    if libm_identity.glibc_built_for_x86_64_v3():
        pytest.skip(
            "glibc here is built for x86-64-v3, so no mask moves it off its FMA variant"
        )
    moved = _exp_digest_under(tunables) != _exp_digest_under("")
    monkeypatch.setenv(libm_identity.TUNABLES, tunables)
    assert libm_identity.runs_the_pinned_routines() is not moved
    monkeypatch.setattr(
        libm_identity, "mask_reading_here", lambda: libm_identity.ANY_READING
    )
    assert not (moved and libm_identity.runs_the_pinned_routines())


def _on_x86_64_glibc() -> None:
    if platform.machine() != "x86_64" or platform.libc_ver()[0] != "glibc":
        pytest.skip("reads the objects glibc's loader maps on x86-64 Linux")


#: Why a test that looks up where a symbol resolves, or maps a file of its
#: own, skips: both go through ctypes.
_WITHOUT_CTYPES = (
    "needs ctypes to look up where the default namespace resolves a symbol and "
    "to map a file; an interpreter built without libffi has none"
)


def _mappings() -> list[tuple[int, int, Path]]:
    """The files ``/proc/self/maps`` lists, each with the range it is mapped at."""
    maps = Path("/proc/self/maps").read_text(encoding="utf-8", errors="replace")
    mapped = []
    for line in maps.splitlines():
        fields = line.split(maxsplit=5)
        if len(fields) == 6 and fields[5].startswith("/"):
            start, _, end = fields[0].partition("-")
            mapped.append((int(start, 16), int(end, 16), Path(fields[5])))
    return mapped


def _file_holding(symbol: str) -> Path:
    """The file the kernel maps where the default namespace resolves *symbol*."""
    try:
        # Imported here: without ctypes this module still loads, and only the
        # tests that look a symbol up skip.
        import ctypes  # noqa: PLC0415
    except ImportError:
        pytest.skip(_WITHOUT_CTYPES)
    address = ctypes.cast(getattr(ctypes.CDLL(None), symbol), ctypes.c_void_p).value
    assert address is not None
    for start, end, file in _mappings():
        if start <= address < end:
            return file
    msg = f"no file is mapped at {symbol}'s address {address:#x}"
    raise AssertionError(msg)


def _first_mapped(file_name: re.Pattern[str]) -> Path | None:
    for _, _, file in _mappings():
        if file_name.fullmatch(file.name):
            return file
    return None


def _first_libm_mapped() -> Path | None:
    return _first_mapped(libm_identity._LIBM_FILE_NAME)


def _declares_v3(library: Path) -> bool:
    """Whether *library* declares x86-64-v3 or a higher level, as readelf names them."""
    needed = libm_identity.x86_isa_levels_needed(library.read_bytes())
    return needed is not None and needed >= _LEVEL_BITS["x86-64-v3"]


def _libm_of_the_other_build(real: Path, directory: Path) -> Path:
    """A ``libm.so.6`` in *directory* that declares the build *real* is not.

    It declares x86-64-v3 where *real* is built for a lower level and the
    baseline where *real* is built for x86-64-v3, so that reading it in place
    of *real* changes the predicate on either build.
    """
    planted = directory / "libm.so.6"
    planted.parent.mkdir(parents=True, exist_ok=True)
    needed = _BASELINE if _declares_v3(real) else _V3
    planted.write_bytes(_elf((_PT_GNU_PROPERTY, _glibc_libm_note(needed), 8)))
    return planted


def _loader_read_otherwise(real: Path, directory: Path) -> Path:
    """A loader in *directory* spelt as a glibc that reads the mask unlike *real*."""
    reading = libm_identity.mask_reading(real.read_bytes())
    expected = reading if reading is not None else libm_identity.ANY_READING
    planted = directory / "ld-linux-x86-64.so.2"
    planted.parent.mkdir(parents=True, exist_ok=True)
    planted.write_bytes(
        next(
            image
            for image in _LOADERS.values()
            if libm_identity.mask_reading(image) != expected
        )
    )
    return planted


#: ``PROT_READ``, ``MAP_PRIVATE`` and ``MAP_FIXED_NOREPLACE`` (Linux 4.17),
#: which maps at the address asked or fails.
_PROT_READ = 0x1
_MAP_PRIVATE = 0x2
_MAP_FIXED_NOREPLACE = 0x100000


@contextlib.contextmanager
def _mapped_first(path: Path) -> Iterator[None]:
    """*path* mapped below every file this process maps, so maps lists it first."""
    try:
        # Imported here, as in _file_holding.
        import ctypes  # noqa: PLC0415
    except ImportError:
        pytest.skip(_WITHOUT_CTYPES)
    libc = ctypes.CDLL(None)
    mmap = libc.mmap
    mmap.argtypes = (
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_long,
    )
    mmap.restype = ctypes.c_void_p
    munmap = libc.munmap
    munmap.argtypes = (ctypes.c_void_p, ctypes.c_size_t)
    munmap.restype = ctypes.c_int
    size = path.stat().st_size
    wanted = min(start for start, _, _ in _mappings()) // 2 & ~0xFFF
    with path.open("rb") as file:
        flags = _MAP_PRIVATE | _MAP_FIXED_NOREPLACE
        address = mmap(wanted, size, _PROT_READ, flags, file.fileno(), 0)
    if address != wanted:
        if address not in (None, ctypes.c_void_p(-1).value):
            munmap(address, size)
        pytest.fail(f"could not map {path} at {wanted:#x}")
    try:
        yield
    finally:
        munmap(address, size)


def test_the_libm_read_is_the_one_that_defines_exp(tmp_path: Path) -> None:
    """A ``libm`` mapped ahead of the one :mod:`math` calls is not the one read.

    ``dlmopen`` maps a second ``libm`` into another namespace below the
    libraries already mapped, so ``/proc/self/maps`` lists it first. A planted
    one that declares the other build, mapped below every file here, stands in
    for it: the library read is still the file the kernel maps at the address
    the default namespace resolves for ``exp``, and the predicate is still
    that file's.
    """
    _on_x86_64_glibc()
    real = _file_holding("exp")
    planted = _libm_of_the_other_build(real, tmp_path)
    with _mapped_first(planted):
        first = _first_libm_mapped()
        assert first is not None
        assert first.samefile(planted)
        library = libm_identity.loaded_libm()
        assert library is not None
        assert library.samefile(real)
        assert libm_identity.glibc_built_for_x86_64_v3() is _declares_v3(real)


def test_the_loader_read_is_the_one_that_defines_tls_get_addr(tmp_path: Path) -> None:
    """A loader mapped ahead of this process's is not the one whose mask is read.

    A planted one, spelt as a glibc that reads the mask otherwise and mapped
    below every file here, stands in for a loader another namespace or a copy
    maps: the mask is still read as the loader the default namespace resolves
    ``__tls_get_addr`` in reads it, or in any spelling where that loader names
    no mask tunable, as glibc's before 2.26 and one built without tunables do.
    """
    _on_x86_64_glibc()
    real = _file_holding("__tls_get_addr")
    reading = libm_identity.mask_reading(real.read_bytes())
    expected = reading if reading is not None else libm_identity.ANY_READING
    with _mapped_first(_loader_read_otherwise(real, tmp_path)):
        loader = libm_identity.loaded_loader()
        assert loader is not None
        assert loader.samefile(real)
        assert libm_identity.mask_reading_here() == expected


#: A child that imports :mod:`math` and leaves the directory it started in,
#: then, with the file its command line names mapped ahead of every other,
#: prints the first ``libm`` listed, the ``libm`` read and the predicate, and
#: last the file mapped at ``exp``'s address.
_LIBM_READ_IN_A_CHILD = (
    "import math, os, sys\n"
    "from pathlib import Path\n"
    "sys.path.insert(0, sys.argv[1])\n"
    "import test_libm_identity as here\n"
    "os.chdir('/')\n"
    "with here._mapped_first(Path(sys.argv[2])):\n"
    "    print(here._first_libm_mapped())\n"
    "    print(here.libm_identity.loaded_libm())\n"
    "    print(here.libm_identity.glibc_built_for_x86_64_v3())\n"
    "print(here._file_holding('exp'))\n"
)


def test_a_libm_found_by_a_relative_path_is_the_file_mapped_at_exp(
    tmp_path: Path,
) -> None:
    """The ``libm`` read is the one :mod:`math` calls, by its absolute path.

    With ``LD_LIBRARY_PATH=lib`` the loader finds ``libm.so.6`` under the
    directory the process starts in, and ``dladdr`` names it as the loader
    found it, ``lib/libm.so.6``: after a change of directory that name is
    another file or none, and the first ``libm`` ``/proc/self/maps`` lists may
    be another namespace's. A copy of the ``libm`` mapped at ``exp``'s
    address, under ``lib/``, stands in for a library a relative path finds,
    and a planted ``libm`` of the other build, mapped ahead of every file, for
    one that ``dlmopen`` loaded: the library read is the copy, and the
    predicate is the copy's.
    """
    _on_x86_64_glibc()
    copy = tmp_path / "lib" / "libm.so.6"
    copy.parent.mkdir()
    shutil.copyfile(_file_holding("exp"), copy)
    planted = _libm_of_the_other_build(copy, tmp_path / "other")
    search = os.environ.get("LD_LIBRARY_PATH")
    environment = dict(os.environ, LD_LIBRARY_PATH=f"lib:{search}" if search else "lib")
    # Fixed argv, no shell; the paths are this module's directory and a file
    # this test wrote
    first, read, v3, mapped = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            _LIBM_READ_IN_A_CHILD,
            str(Path(__file__).parent),
            str(planted),
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=environment,
        timeout=60,
    ).stdout.splitlines()
    assert Path(mapped).samefile(copy)
    assert Path(first).samefile(planted)
    assert Path(read).is_absolute()
    assert Path(read).samefile(copy)
    assert v3 == str(_declares_v3(copy))


#: A child that, with the file its command line names mapped ahead of every
#: other, prints the loader read and whether the mask is read as the file
#: mapped at ``__tls_get_addr``'s address reads it, and last that file.
_LOADER_READ_IN_A_CHILD = (
    "import sys\n"
    "from pathlib import Path\n"
    "sys.path.insert(0, sys.argv[1])\n"
    "import test_libm_identity as here\n"
    "real = here._file_holding('__tls_get_addr')\n"
    "reading = here.libm_identity.mask_reading(real.read_bytes())\n"
    "expected = reading or here.libm_identity.ANY_READING\n"
    "with here._mapped_first(Path(sys.argv[2])):\n"
    "    print(here.libm_identity.loaded_loader())\n"
    "    print(here.libm_identity.mask_reading_here() == expected)\n"
    "print(real)\n"
)


def test_a_loader_run_by_a_relative_path_is_the_file_mapped_at_tls_get_addr(
    tmp_path: Path,
) -> None:
    """The loader read is the one this process runs, by its absolute path.

    Run as ``./ld-linux-x86-64.so.2`` from its own directory, the loader names
    itself through ``dladdr`` by that relative path. A planted loader spelt as
    a glibc that reads the mask otherwise, mapped ahead of every file, stands
    in for one another namespace maps: the loader read is the file mapped at
    ``__tls_get_addr``'s address, and the mask is read as it reads it.
    """
    _on_x86_64_glibc()
    real = _file_holding("__tls_get_addr")
    planted = _loader_read_otherwise(real, tmp_path)
    # Fixed argv, no shell; the loader is the one this process runs, the
    # paths this module's directory and a file this test wrote
    read, agrees, mapped = subprocess.run(
        [
            f"./{real.name}",
            sys.executable,
            "-I",
            "-c",
            _LOADER_READ_IN_A_CHILD,
            str(Path(__file__).parent),
            str(planted),
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=real.parent,
        timeout=60,
    ).stdout.splitlines()
    assert Path(mapped).samefile(real)
    assert Path(read).is_absolute()
    assert Path(read).samefile(real)
    assert agrees == "True"


def test_where_dladdr_names_no_file_the_file_at_the_address_is_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Where ``exp`` is looked up but ``dladdr`` finds no object, none is guessed.

    The library read is still the file mapped at ``exp``'s address, not the
    first ``libm`` listed, which is a planted one of the other build mapped
    ahead of every file.
    """
    _on_x86_64_glibc()
    real = _file_holding("exp")
    # Imported here, where _file_holding has not skipped for the want of it.
    import ctypes  # noqa: PLC0415

    class WithoutDladdr(ctypes.CDLL):
        """The libraries as ctypes opens them, with a ``dladdr`` that finds none."""

        @staticmethod
        def dladdr(address: object, info: object) -> int:
            return 0

    monkeypatch.setattr(ctypes, "CDLL", WithoutDladdr)
    resolved = libm_identity._resolved("exp")
    assert resolved is not None
    assert resolved[1] is None
    with _mapped_first(_libm_of_the_other_build(real, tmp_path)):
        library = libm_identity.loaded_libm()
        assert library is not None
        assert library.samefile(real)
        assert libm_identity.glibc_built_for_x86_64_v3() is _declares_v3(real)


def test_without_ctypes_the_first_mapped_files_are_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Where no symbol can be looked up, the first ``libm`` and loader listed are read.

    An interpreter built without libffi has no ctypes, and nothing there asks
    where the default namespace resolves a symbol: the files read are the
    first of their names that ``/proc/self/maps`` lists.
    """
    _on_x86_64_glibc()
    monkeypatch.setitem(sys.modules, "ctypes", None)
    assert libm_identity._resolved("exp") is None
    assert libm_identity.loaded_libm() == _first_libm_mapped()
    loader = libm_identity.loaded_loader()
    assert loader == _first_mapped(libm_identity._LOADER_FILE_NAME)
    assert loader is not None


#: A child whose ``_ctypes`` cannot be imported, as in an interpreter built
#: without libffi, that loads this module, runs one of its tests that reads
#: no object, and prints why a test that looks a symbol up skips.
_WITHOUT_CTYPES_CHILD = (
    "import sys\n"
    "sys.modules['_ctypes'] = None\n"
    "sys.path.insert(0, sys.argv[1])\n"
    "import pytest\n"
    "import test_libm_identity as here\n"
    "here.test_a_build_for_x86_64_v3_declares_that_level()\n"
    "try:\n"
    "    here._file_holding('exp')\n"
    "except pytest.skip.Exception as skipped:\n"
    "    print(skipped)\n"
)


def test_without_ctypes_only_the_tests_that_look_a_symbol_up_skip() -> None:
    """This module loads where ctypes cannot be imported.

    :mod:`libm_identity` reads ``/proc/self/maps`` there, so the tests of the
    note, of the mask and of that reading run on such an interpreter, and only
    those that look up where a symbol resolves, or map a file of their own,
    skip, saying why.
    """
    # Fixed argv, no shell; the directory is the one this module is in
    shown = subprocess.run(
        [sys.executable, "-I", "-c", _WITHOUT_CTYPES_CHILD, str(Path(__file__).parent)],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    ).stdout
    assert shown.splitlines() == [_WITHOUT_CTYPES]


def test_off_linux_no_symbol_is_looked_up(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    assert libm_identity._resolved("exp") is None


def _real_glibc_libm() -> Path:
    _on_x86_64_glibc()
    library = libm_identity.loaded_libm()
    assert library is not None, "glibc's libm is not mapped in this process"
    return library


def test_the_real_libm_is_found_and_read() -> None:
    library = _real_glibc_libm()
    assert library.is_file()
    assert libm_identity.glibc_built_for_x86_64_v3() is _declares_v3(library)


def _readelf_notes(library: Path) -> str:
    """What ``readelf --notes`` prints of *library*, in the C locale.

    Without ``--wide``, readelf prints each property of a note on a line of
    its own; with it, it joins them on one line with ", ", which also
    separates the levels of one property. The C locale keeps the words read
    below untranslated.
    """
    readelf = shutil.which("readelf")
    if readelf is None:
        pytest.skip("needs binutils' readelf to read the note independently")
    # Fixed argv, no shell; the path is a library this process mapped or wrote
    return subprocess.run(
        [readelf, "--notes", str(library)],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "LC_ALL": "C"},
        timeout=60,
    ).stdout


#: Why a readelf shows no ISA property: it prints the GNU property note as a
#: type it does not know, as binutils 2.27 and 2.28 do. binutils 2.29 to 2.35
#: know the note but not the x86-64 levels, and show the property by its
#: number and its bytes, which are read as the levels.
_AS_AN_UNKNOWN_NOTE = (
    "this readelf prints the GNU property note as a note type it does not "
    "know: it predates that note, as binutils 2.28 and earlier do"
)


def _why_readelf_shows_no_property(shown: str) -> str | None:
    """Why readelf, printing *shown*, shows no ISA property, or ``None``.

    It is read from what readelf prints, never from what the reader reads: a
    readelf that knows the GNU property note shows the property wherever the
    object carries it, by its levels' names or by its number and its bytes,
    so the levels it shows, none included, are the ones the reader is held
    to.
    """
    unknown = (
        r"^\s*GNU\s+0x[0-9a-f]+\s+"
        rf"Unknown note type: \({_NT_GNU_PROPERTY_TYPE_0:#010x}\)\s*$"
    )
    if re.search(unknown, shown, re.IGNORECASE | re.MULTILINE):
        return _AS_AN_UNKNOWN_NOTE
    return None


#: The word readelf names each ISA property by, from binutils 2.36 on.
_ISA_PROPERTY_WORDS = {_ISA_1_NEEDED: "needed", _ISA_1_USED: "used"}


def _levels_readelf_shows(shown: str, kind: int = _ISA_1_NEEDED) -> int | None:
    """The ISA levels ``readelf --notes`` shows in property *kind*, or ``None``.

    binutils 2.36 and later name the levels, on an ``x86 ISA needed:`` or
    ``x86 ISA used:`` line. binutils 2.29 to 2.35 know the note but not these
    property types, and print each by its number and its bytes, as ``type
    0xc0008002 data: 07 00 00 00``: the bytes are the bitmask the reader
    reads, least significant first.
    """
    line = re.search(rf"x86 ISA {_ISA_PROPERTY_WORDS[kind]}: ([^\n]*)", shown)
    if line is not None:
        return sum(_LEVEL_BITS[name.strip()] for name in line.group(1).split(","))
    data = re.search(rf"type {kind:#x} data: ((?:[0-9a-f]{{2}} )+)>", shown)
    if data is None:
        return None
    return int.from_bytes(bytes.fromhex(data.group(1)), "little")


@pytest.mark.parametrize(
    ("shown", "needed"),
    [
        pytest.param(
            "  GNU                  0x00000010\tNT_GNU_PROPERTY_TYPE_0\n"
            "      Properties: x86 ISA needed: x86-64-baseline\n",
            _BASELINE,
            id="debian-13-libm",
        ),
        pytest.param(
            "  GNU                  0x00000020\tNT_GNU_PROPERTY_TYPE_0\n"
            "      Properties: x86 feature: IBT, SHSTK\n"
            "\tx86 ISA needed: x86-64-baseline\n",
            _BASELINE,
            id="ubuntu-26.04-amd64-libm",
        ),
        pytest.param(
            "  GNU                  0x00000020\tNT_GNU_PROPERTY_TYPE_0\n"
            "      Properties: x86 feature: IBT, SHSTK\n"
            "\tx86 ISA needed: x86-64-baseline, x86-64-v2, x86-64-v3\n",
            _V3,
            id="ubuntu-26.04-amd64v3-libm",
        ),
        pytest.param(
            "  GNU                  0x00000040\tNT_GNU_PROPERTY_TYPE_0\n"
            "      Properties: x86 feature: IBT, SHSTK\n"
            "\tx86 ISA needed: x86-64-baseline\n"
            "\tx86 feature used: x86, x87, XMM, YMM\n"
            "\tx86 ISA used: x86-64-baseline, x86-64-v2, x86-64-v3\n",
            _BASELINE,
            id="fedora-45-libm",
        ),
        pytest.param(
            "  GNU                  0x00000040\tNT_GNU_PROPERTY_TYPE_0\n"
            "      Properties: x86 feature: IBT, SHSTK\n"
            "\tx86 ISA needed: x86-64-baseline, x86-64-v2, x86-64-v3\n"
            "\tx86 feature used: x86, x87, XMM, YMM\n"
            "\tx86 ISA used: x86-64-baseline, x86-64-v3\n",
            _V3,
            id="almalinux-10-libm",
        ),
        pytest.param(
            "  GNU                  0x00000010\tNT_GNU_PROPERTY_TYPE_0\n"
            "      Properties: x86 feature: IBT, SHSTK\n",
            None,
            id="debian-13-libnetfilter-conntrack",
        ),
    ],
)
def test_the_levels_readelf_prints_end_with_their_line(
    *, shown: str, needed: int | None
) -> None:
    """Each is the note as ``readelf --notes`` 2.44 printed it for that object."""
    assert _levels_readelf_shows(shown) == needed


def _hold_to_readelf(image: bytes, shown: str) -> None:
    """Hold the levels the reader reads in *image* to those readelf shows.

    It skips where readelf, printing *shown*, does not know the GNU property
    note, and fails wherever readelf shows other levels than the reader
    reads, by their names or by the property's bytes, none included.
    """
    reason = _why_readelf_shows_no_property(shown)
    if reason is not None:
        pytest.skip(reason)
    assert libm_identity.x86_isa_levels_needed(image) == _levels_readelf_shows(shown)


#: What ``readelf --notes`` printed, in the C locale, of a minimal object whose
#: note declares x86-64-v3 (``_glibc_libm_note``), and of the property notes
#: of real libms, by the binutils that printed it.
_READELF_PRINTED = {
    "2.27-planted": (
        "\nDisplaying notes found at file offset 0x00000078 with length 0x00000030:\n"
        "  Owner                 Data size\tDescription\n"
        "  GNU                  0x00000020\tUnknown note type: (0x00000005)\n"
    ),
    "2.27-ubuntu-26.04-amd64v3-libm": (
        "\nDisplaying notes found at file offset 0x000df610 with length 0x00000030:\n"
        "  Owner                 Data size\tDescription\n"
        "  GNU                  0x00000020\tUnknown note type: (0x00000005)\n"
    ),
    "2.27-other-owner": (
        "\nDisplaying notes found at file offset 0x00000078 with length 0x00000018:\n"
        "  Owner                 Data size\tDescription\n"
        "  XYZ                  0x00000008\tUnknown note type: (0x00000005)\n"
    ),
    "2.27-gnu-type-7": (
        "\nDisplaying notes found at file offset 0x00000078 with length 0x00000018:\n"
        "  Owner                 Data size\tDescription\n"
        "  GNU                  0x00000008\tUnknown note type: (0x00000007)\n"
    ),
    "2.30-ubuntu-26.04-amd64v3-libm": (
        "\nDisplaying notes found in: .note.gnu.property\n"
        "  Owner                 Data size\tDescription\n"
        "  GNU                  0x00000020\tNT_GNU_PROPERTY_TYPE_0\n"
        "      Properties: x86 feature: IBT, SHSTK\n"
        "\t<procesor-specific type 0xc0008002 data: 07 00 00 00 >\n"
    ),
    "2.30-almalinux-8-libm": (
        "\nDisplaying notes found in: .note.gnu.property\n"
        "  Owner                 Data size\tDescription\n"
        "  GNU                  0x00000010\tNT_GNU_PROPERTY_TYPE_0\n"
        "      Properties: x86 feature: IBT, SHSTK\n"
    ),
    "2.31.1-planted": (
        "\nDisplaying notes found at file offset 0x00000078 with length 0x00000030:\n"
        "  Owner                 Data size\tDescription\n"
        "  GNU                  0x00000020\tNT_GNU_PROPERTY_TYPE_0\n"
        "      Properties: x86 feature: IBT, SHSTK\n"
        "\t<procesor-specific type 0xc0008002 data: 07 00 00 00 >\n"
    ),
    "2.34-ubuntu-26.04-amd64-libm": (
        "\nDisplaying notes found in: .note.gnu.property\n"
        "  Owner                Data size \tDescription\n"
        "  GNU                  0x00000020\tNT_GNU_PROPERTY_TYPE_0\n"
        "      Properties: x86 feature: IBT, SHSTK\n"
        "\t<procesor-specific type 0xc0008002 data: 01 00 00 00 >\n"
    ),
    "2.46-planted": (
        "\nDisplaying notes found at file offset 0x00000078 with length 0x00000030:\n"
        "  Owner                Data size \tDescription\n"
        "  GNU                  0x00000020\tNT_GNU_PROPERTY_TYPE_0\n"
        "      Properties: x86 feature: IBT, SHSTK\n"
        "\tx86 ISA needed: x86-64-baseline, x86-64-v2, x86-64-v3\n"
    ),
    "2.46-ubuntu-26.04-amd64-libm": (
        "\nDisplaying notes found in: .note.gnu.property\n"
        "  Owner                Data size \tDescription\n"
        "  GNU                  0x00000020\tNT_GNU_PROPERTY_TYPE_0\n"
        "      Properties: x86 feature: IBT, SHSTK\n"
        "\tx86 ISA needed: x86-64-baseline\n"
    ),
}


@pytest.mark.parametrize(
    ("printed", "reason", "levels"),
    [
        ("2.27-planted", _AS_AN_UNKNOWN_NOTE, None),
        ("2.27-ubuntu-26.04-amd64v3-libm", _AS_AN_UNKNOWN_NOTE, None),
        ("2.27-other-owner", None, None),
        ("2.27-gnu-type-7", None, None),
        ("2.30-ubuntu-26.04-amd64v3-libm", None, _V3),
        ("2.30-almalinux-8-libm", None, None),
        ("2.31.1-planted", None, _V3),
        ("2.34-ubuntu-26.04-amd64-libm", None, _BASELINE),
        ("2.46-planted", None, _V3),
        ("2.46-ubuntu-26.04-amd64-libm", None, _BASELINE),
    ],
)
def test_readelf_shows_the_levels_unless_it_prints_an_unknown_note(
    *, printed: str, reason: str | None, levels: int | None
) -> None:
    """Only a note readelf does not know shows no ISA property.

    binutils 2.27 (CentOS 7) knows no GNU property note; 2.30 (AlmaLinux 8),
    2.31.1 (Debian 10) and 2.34 (Ubuntu 20.04) know the note but not the
    levels, and show the property by its number and its bytes; 2.46 names
    the levels. An unknown note of another owner or of another GNU type is not
    the property note, and a note that carries no ISA property, as AlmaLinux
    8's libm, is one readelf reads in full.
    """
    shown = _READELF_PRINTED[printed]
    assert _why_readelf_shows_no_property(shown) == reason
    assert _levels_readelf_shows(shown) == levels


def _held(image: bytes, printed: str) -> str:
    """What holding *image* to readelf printing *printed* comes to."""
    try:
        _hold_to_readelf(image, _READELF_PRINTED[printed])
    except AssertionError:
        return "fails"
    except pytest.skip.Exception as skipped:
        return f"skips: {skipped}"
    return "agrees"


def test_a_readelf_that_shows_the_property_holds_the_reader_to_its_levels() -> None:
    """Shown, the levels are compared, and a difference fails the cross-check.

    The object declares x86-64-v3: readelf naming x86-64-v3, or showing the
    property by its number with the bytes of x86-64-v3, agrees; readelf naming
    the baseline, showing the bytes of the baseline, or naming the note's
    properties without an ISA level disagrees with the reader and fails,
    never skips; readelf printing the note as an unknown type skips, whatever
    it would say.
    """
    image = _elf((_PT_NOTE, _glibc_libm_note(_V3), 8))
    printed = (
        "2.46-planted",
        "2.46-ubuntu-26.04-amd64-libm",
        "2.30-almalinux-8-libm",
        "2.31.1-planted",
        "2.30-ubuntu-26.04-amd64v3-libm",
        "2.34-ubuntu-26.04-amd64-libm",
        "2.27-planted",
    )
    assert {name: _held(image, name) for name in printed} == {
        "2.46-planted": "agrees",
        "2.46-ubuntu-26.04-amd64-libm": "fails",
        "2.30-almalinux-8-libm": "fails",
        "2.31.1-planted": "agrees",
        "2.30-ubuntu-26.04-amd64v3-libm": "agrees",
        "2.34-ubuntu-26.04-amd64-libm": "fails",
        "2.27-planted": f"skips: {_AS_AN_UNKNOWN_NOTE}",
    }


def test_readelf_and_the_reader_agree_past_the_needed_levels(tmp_path: Path) -> None:
    """A note that carries the used features and levels after, as Fedora's does.

    readelf shows the used levels after the needed ones, named or by the
    property's number, and neither reading takes them for the needed ones.
    """
    note = _property_note(
        (_FEATURE_1_AND, 0b11),
        (_ISA_1_NEEDED, _V3),
        (_FEATURE_2_USED, 0b11011),
        (_ISA_1_USED, 0b0101),
    )
    image = _elf((_PT_GNU_PROPERTY, note, 8), (_PT_NOTE, note, 8))
    library = tmp_path / "libm.so.6"
    library.write_bytes(image)
    shown = _readelf_notes(library)
    _hold_to_readelf(image, shown)
    assert _levels_readelf_shows(shown, _ISA_1_USED) == 0b0101
    assert libm_identity.x86_isa_levels_needed(image) == _V3
    assert _levels_readelf_shows(shown) == _V3


def test_the_real_libm_reads_as_readelf_reads_it() -> None:
    library = _real_glibc_libm()
    _hold_to_readelf(library.read_bytes(), _readelf_notes(library))
