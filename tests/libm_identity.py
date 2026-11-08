#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The platform whose C library is the routine the pinned transcendentals spell.

``phonometry.filters._pinned_exp`` and ``_pinned_log`` spell glibc's ``exp``,
``pow`` and ``log`` (ARM's optimized-routines) in the variant glibc selects on
an x86-64 processor with a fused multiply-add unit, and ``pinned_log10`` is
glibc's SunPro ``log10`` on top of that ``log``. On that platform the
bit-for-bit tests of those routines must hold, and a mismatch is a red build;
anywhere else the local library is a different routine and they skip.

The platform is decided from what it is, never from whether the routines
happen to agree on a probe: a probe that skipped on disagreement would turn a
broken routine into a skipped test on the one machine where it is proved.

glibc built for the x86-64 baseline, as Debian's and Ubuntu's generic
``amd64`` packages are, carries ``exp``, ``log``, ``pow``, ``sin``, ``tan``
and ``atan`` twice and picks its FMA variant when the processor reports both
FMA and AVX2 as usable, so masking FMA or AVX2 through ``GLIBC_TUNABLES``
(``glibc.cpu.hwcaps=-FMA``, or ``-FMA_Usable`` where glibc reads the older
spelling) hands the same process the other variant. Masking AVX alone does
not: the mask clears only the feature it names, and FMA and AVX2 stay
usable. glibc built for x86-64-v3, as Ubuntu's ``amd64v3`` packages are (the
ones the ``ubuntu-26.04`` runner image installs), carries no other variant:
it compiles those routines for a processor with FMA and AVX2, and glibc's
multiarch sources build the variants without them only below that level
(``MINIMUM_X86_ISA_LEVEL < AVX2_X86_ISA_LEVEL`` in
``sysdeps/x86_64/fpu/multiarch`` of glibc 2.43), so no mask hands a process
anything but the FMA routines there.

Which of the two a process runs is decided from what its ``libm`` is, by the
same rule: the ISA level the object declares it needs, in the
``GNU_PROPERTY_X86_ISA_1_NEEDED`` property of its ``.note.gnu.property``.
glibc writes that property from the same ``MINIMUM_X86_ISA_LEVEL``
(``sysdeps/x86/isa-level.c``), and its loader checks it against the
processor when it loads the object, before relocating or running it
(``sysdeps/x86/dl-prop.h``, called from ``elf/rtld.c`` and
``elf/dl-open.c``). An object that declares no level is taken, as the loader
takes it, to need the baseline, so a library this module cannot read keeps
every test that asks for the other variant running, and failing if that
variant is not there.
"""

from __future__ import annotations

import importlib
import os
import platform
import re
import struct
from pathlib import Path

import pytest

#: The processor features glibc asks to be usable before it picks its FMA
#: variant (``ifunc-fma.h``, ``ifunc-fma4.h`` and ``ifunc-avx-fma4.h`` in
#: ``sysdeps/x86_64/fpu/multiarch``), so that masking one takes glibc off it
#: wherever glibc carries another variant. AVX is not one: the mask clears
#: only the feature it names (``sysdeps/x86/cpu-tunables.c``).
_FMA_VARIANT_FEATURES = frozenset({"FMA", "AVX2"})

#: The suffix of the name under which an older glibc masks a feature's usable
#: bit, ``FMA_Usable``. glibc 2.31 as Ubuntu 20.04 builds it reads only those
#: names, and glibc 2.32 on, as RHEL 8's glibc 2.28 does, only the features'
#: own; each ignores the other spelling, and matches a name only as it is
#: spelt, case included. Which spelling a glibc reads is not in its version,
#: so a mask in either counts.
_USABLE_SUFFIX = "_Usable"

#: The first glibc that ships ARM's ``exp``, ``log`` and ``pow``.
_FIRST_GLIBC = (2, 28)

#: The environment variable through which glibc masks processor features.
TUNABLES = "GLIBC_TUNABLES"

#: The value that makes glibc built for the x86-64 baseline take its variants
#: without FMA, in both spellings of the mask, so that every glibc reads it.
WITHOUT_FMA = (
    "glibc.cpu.hwcaps=-AVX2,-FMA,-FMA4,-AVX,"
    "-AVX2_Usable,-FMA_Usable,-FMA4_Usable,-AVX_Usable"
)

#: ``EM_X86_64``, the machine whose processor-specific properties these are.
_EM_X86_64 = 62

#: ``PT_GNU_PROPERTY``, the segment glibc's loader reads the property from,
#: and ``PT_NOTE``, which holds the same note in an object without it.
_PT_GNU_PROPERTY = 0x6474E553
_PT_NOTE = 4

#: ``NT_GNU_PROPERTY_TYPE_0``, the type of the note that carries the property.
_NT_GNU_PROPERTY_TYPE_0 = 5

#: ``GNU_PROPERTY_X86_ISA_1_NEEDED``, the property in which an x86 object
#: names the ISA levels the processor must support to run it.
_GNU_PROPERTY_X86_ISA_1_NEEDED = 0xC0008002

#: ``GNU_PROPERTY_X86_ISA_1_V3``, the bit of that property that names
#: x86-64-v3, whose ISAs include AVX2 and FMA; a bit above it names a level
#: that includes this one.
_X86_ISA_1_V3 = 1 << 2

#: The file name of glibc's ``libm`` as ``/proc/self/maps`` names it:
#: ``libm.so.6`` since glibc 2.34 and ``libm-2.31.so`` before.
_LIBM_FILE_NAME = re.compile(r"libm(?:-\d+(?:\.\d+)*)?\.so(?:\.\d+)*")


def _cpu_flags() -> frozenset[str]:
    """The ``flags`` line of ``/proc/cpuinfo``, or nothing where there is none."""
    try:
        text = Path("/proc/cpuinfo").read_text(encoding="ascii", errors="replace")
    except OSError:
        return frozenset()
    for line in text.splitlines():
        key, _, value = line.partition(":")
        if key.strip() == "flags":
            return frozenset(value.split())
    return frozenset()


def _glibc_version() -> tuple[int, ...] | None:
    """glibc's version as numbers, or ``None`` if the C library is another."""
    library, version = platform.libc_ver()
    if library != "glibc":
        return None
    try:
        return tuple(int(part) for part in version.split(".")[:2])
    except ValueError:
        return None


def masks_the_fma_variant(tunables: str) -> bool:
    """Whether a ``GLIBC_TUNABLES`` value masks a feature glibc's FMA variant needs."""
    for item in tunables.split(":"):
        name, _, value = item.partition("=")
        if name.strip() != "glibc.cpu.hwcaps":
            continue
        masked = {
            part.strip()[1:].removesuffix(_USABLE_SUFFIX)
            for part in value.split(",")
            if part.strip().startswith("-")
        }
        if masked & _FMA_VARIANT_FEATURES:
            return True
    return False


def glibc_on_x86_64_with_fma() -> bool:
    """glibc 2.28 or later on an x86-64 processor that reports FMA and AVX2."""
    version = _glibc_version()
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        return False
    if version is None or version < _FIRST_GLIBC:
        return False
    return {"fma", "avx2"} <= _cpu_flags()


def _aligned(offset: int, alignment: int) -> int:
    """``offset`` rounded up to a multiple of ``alignment``."""
    return -(-offset // alignment) * alignment


def _needed_in_properties(descriptor: bytes) -> int | None:
    """The ISA levels a GNU property array names as needed, or ``None``."""
    offset = 0
    while offset + 8 <= len(descriptor):
        kind, size = struct.unpack_from("<II", descriptor, offset)
        offset += 8
        if kind == _GNU_PROPERTY_X86_ISA_1_NEEDED and size == 4:
            if offset + 4 > len(descriptor):
                return None
            (needed,) = struct.unpack_from("<I", descriptor, offset)
            return int(needed)
        offset += _aligned(size, 8)
    return None


def _needed_in_notes(notes: bytes) -> int | None:
    """The ISA levels the GNU property note of a note segment names, or ``None``."""
    offset = 0
    while offset + 12 <= len(notes):
        name_size, descriptor_size, kind = struct.unpack_from("<III", notes, offset)
        name_start = offset + 12
        descriptor_start = _aligned(name_start + name_size, 8)
        descriptor_end = descriptor_start + descriptor_size
        name = notes[name_start : name_start + name_size]
        if kind == _NT_GNU_PROPERTY_TYPE_0 and name == b"GNU\0":
            return _needed_in_properties(notes[descriptor_start:descriptor_end])
        offset = _aligned(descriptor_end, 8)
    return None


def x86_isa_levels_needed(image: bytes) -> int | None:
    """The ISA levels a 64-bit x86-64 ELF object declares it needs.

    The value is the ``GNU_PROPERTY_X86_ISA_1_NEEDED`` property of the
    object's ``NT_GNU_PROPERTY_TYPE_0`` note, one bit per level from bit 0,
    the x86-64 baseline: ``0b111`` is a build for x86-64-v3. It is read from
    the segments glibc's loader reads it from, ``PT_GNU_PROPERTY`` first and
    then ``PT_NOTE``, in each the 8-byte aligned notes a 64-bit object carries.

    :param image: The bytes of the object file.
    :return: The property's bits, or ``None`` when the image is no
        little-endian 64-bit x86-64 ELF object or declares no level.
    """
    if image[:6] != b"\x7fELF\x02\x01" or len(image) < 64:
        return None
    (machine,) = struct.unpack_from("<H", image, 18)
    if machine != _EM_X86_64:
        return None
    (table,) = struct.unpack_from("<Q", image, 32)
    entry_size, entries = struct.unpack_from("<HH", image, 54)
    segments: list[tuple[int, int, int]] = []
    for index in range(entries):
        start = table + index * entry_size
        if start + 56 > len(image):
            return None
        kind, _, offset, _, _, size, _, alignment = struct.unpack_from(
            "<IIQQQQQQ", image, start
        )
        if kind in (_PT_GNU_PROPERTY, _PT_NOTE) and alignment == 8:
            # False sorts first, so PT_GNU_PROPERTY is read before PT_NOTE.
            segments.append((kind != _PT_GNU_PROPERTY, offset, size))
    for _, offset, size in sorted(segments):
        needed = _needed_in_notes(image[offset : offset + size])
        if needed is not None:
            return needed
    return None


def loaded_libm() -> Path | None:
    """The file of the ``libm`` this process has mapped, or ``None``.

    :mod:`math` is imported first, so the library its routines call is mapped
    whether the interpreter links it or the module does.
    """
    importlib.import_module("math")
    try:
        maps = Path("/proc/self/maps").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for line in maps.splitlines():
        fields = line.split(maxsplit=5)
        if len(fields) == 6 and _LIBM_FILE_NAME.fullmatch(Path(fields[5]).name):
            return Path(fields[5])
    return None


def glibc_built_for_x86_64_v3() -> bool:
    """Whether this process runs a glibc built for x86-64-v3 or above.

    Such a glibc compiles ``exp``, ``log``, ``pow``, ``sin``, ``tan`` and
    ``atan`` for a processor with FMA and AVX2 and carries no variant without
    them for ``GLIBC_TUNABLES`` to select. It is read from the ISA level the
    mapped ``libm`` declares it needs, never from whether a masked process's
    routines agree with this one's.

    :return: ``True`` when the ``libm`` of glibc on x86-64 Linux names
        x86-64-v3 or a higher level as needed; ``False`` for a build for a
        lower level, for an object that names none, for one that cannot be
        read, and on any other platform.
    """
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        return False
    if _glibc_version() is None:
        return False
    library = loaded_libm()
    if library is None:
        return False
    try:
        needed = x86_isa_levels_needed(library.read_bytes())
    except OSError:
        return False
    return needed is not None and needed >= _X86_ISA_1_V3


def runs_the_pinned_routines() -> bool:
    """Whether this process's ``math`` module calls the routines the pins spell.

    A mask takes glibc off its FMA variant only where glibc carries another:
    a process on a glibc built for x86-64-v3 runs the FMA routines under any
    mask.
    """
    if not glibc_on_x86_64_with_fma():
        return False
    if glibc_built_for_x86_64_v3():
        return True
    return not masks_the_fma_variant(os.environ.get(TUNABLES, ""))


#: Marks a test that compares a pinned routine bit for bit with :mod:`math`.
on_the_pinned_libm = pytest.mark.skipif(
    not runs_the_pinned_routines(),
    reason="the C library here is not the glibc FMA variant the pinned routines "
    "spell; their bits are the contract, the local library's are not",
)
