#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The platform whose C library is the routine the pinned transcendentals spell.

``phonometry.filters._pinned_exp`` and ``_pinned_log`` spell glibc's ``exp``,
``pow`` and ``log`` (ARM's optimized-routines) in the variant glibc selects on
an x86-64 processor with a fused multiply-add unit, and ``pinned_log10`` is
glibc's SunPro ``log10`` on top of that ``log``. On that platform the
bit-for-bit tests of those routines must hold, and a mismatch is a red build;
anywhere else the local library is a different routine and they skip.

glibc ships those routines from 2.29 on. They and their tables
(``e_exp_data.c``, ``e_log_data.c`` and ``e_pow_log_data.c`` in
``sysdeps/ieee754/dbl-64``) came in with commits e70c17682518 ("Add new exp
and exp2 implementations"), f41b0a43e426 ("Add new log implementation") and
424c4f60ed61 ("Add new pow implementation"), committed after the 2.28
release, whose ``exp``, ``log`` and ``pow`` are still those of IBM's Accurate
Mathematical Library. RHEL 8's glibc 2.28 carries IBM's as well: none of its
patches touches those files. So glibc 2.28, on Debian 10 and RHEL 8 alike, is
a different routine, and its version, which the running C library reports,
says so.

The platform is decided from what it is, never from whether the routines
happen to agree on a probe: a probe that skipped on disagreement would turn a
broken routine into a skipped test on the one machine where it is proved.

glibc built for the x86-64 baseline, as Debian's and Ubuntu's generic
``amd64`` packages are, carries ``exp``, ``log``, ``pow``, ``sin``, ``tan``
and ``atan`` twice and picks its FMA variant when the processor reports both
FMA and AVX2 as usable, so masking FMA or AVX2 through ``GLIBC_TUNABLES``
hands the same process the other variant. Masking AVX alone does not: the
mask clears only the feature it names, and FMA and AVX2 stay usable. glibc
built for x86-64-v3, as Ubuntu's ``amd64v3`` packages are (the ones the
``ubuntu-26.04`` runner image installs), carries no other variant: it
compiles those routines for a processor with FMA and AVX2, and glibc's
multiarch sources build the variants without them only below that level
(``MINIMUM_X86_ISA_LEVEL < AVX2_X86_ISA_LEVEL`` in
``sysdeps/x86_64/fpu/multiarch`` of glibc 2.43), so no mask hands a process
anything but the FMA routines there.

The mask is read by the dynamic loader, and glibc has spelt it three ways.
Up to 2.28 the tunable is ``glibc.tune.hwcaps``, renamed ``glibc.cpu.hwcaps``
in 2.29 (commit dce452dc5278, "Rename the glibc.tune namespace to
glibc.cpu"). Up to 2.31 FMA's usable bit, the one the selector reads, is
masked as ``-FMA_Usable``, and ``-FMA`` clears only the bit the processor
reported; from 2.32 ``-FMA`` clears the usable bit and the ``_Usable`` names
are gone (commit 107e6a3c2212, "x86: Support usable check for all CPU
features"). No release reads both. A distribution's backport moves the
spelling off the version, though: RHEL 8's glibc 2.28 reads
``glibc.cpu.hwcaps=-FMA``. So which one a process's glibc reads is decided
from its loader: the parser compares the mask with names the loader carries
as strings in its image, and from 2.39 on the loader also carries the warning
with which it drops a whole ``GLIBC_TUNABLES`` that holds an ill-formed
entry, where an earlier one applies what it can read. Every glibc reads the
mask as written, spaces included, matches a name as it is spelt, case
included, and of several settings of the tunable keeps the last.

Which of the two a process runs is decided from what its ``libm`` is, by the
same rule. That ``libm`` is the object that defines ``exp`` where the
process's default namespace resolves it, the one :mod:`math` calls: the file
the loader names through ``dladdr``, or the file the kernel maps at that
address where the loader names it by a relative path. The first ``libm``
mapped may be one that ``dlmopen`` loaded into another namespace, so it is
read only where ``exp`` cannot be looked up. What is read is the ISA level the
object declares it needs, in the
``GNU_PROPERTY_X86_ISA_1_NEEDED`` property of its ``.note.gnu.property``.
glibc writes that property from the same ``MINIMUM_X86_ISA_LEVEL``
(``sysdeps/x86/isa-level.c``), and its loader checks it against the
processor when it loads the object, before relocating or running it
(``sysdeps/x86/dl-prop.h``, called from ``elf/rtld.c`` and
``elf/dl-open.c``). An object that declares no level is taken, as the loader
takes it, to need the baseline.

A ``libm`` or a loader that cannot be named or read is neither build and
reads the mask in no known way: it comes back as an :class:`Unread` that says
what could not be read, whose truth cannot be tested, so a test that asks for
the baseline build, for the build for x86-64-v3 or for the loader's own
reading skips by that name instead of checking a build it guessed.

The tests start children of their own through :func:`run_child`, which skips
where the system refuses to start the program, as one whose file or whose
loader sits on a mount made ``noexec`` once this process started: such a
child never runs, so there is nothing of it to read.
"""

from __future__ import annotations

import dataclasses
import importlib
import os
import platform
import re
import struct
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn

import pytest

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

#: The processor features glibc asks to be usable before it picks its FMA
#: variant (``ifunc-fma.h``, ``ifunc-fma4.h`` and ``ifunc-avx-fma4.h`` in
#: ``sysdeps/x86_64/fpu/multiarch``), so that masking one takes glibc off it
#: wherever glibc carries another variant. AVX is not one: the mask clears
#: only the feature it names (``sysdeps/x86/cpu-tunables.c``).
_FMA_VARIANT_FEATURES = frozenset({"FMA", "AVX2"})

#: The tunables through which glibc masks processor features:
#: ``glibc.cpu.hwcaps`` from glibc 2.29, ``glibc.tune.hwcaps`` before.
_HWCAPS_TUNABLES = ("glibc.cpu.hwcaps", "glibc.tune.hwcaps")

#: The suffix of the name under which glibc 2.26 to 2.31 mask a feature's
#: usable bit, ``FMA_Usable``; glibc 2.32 masks that bit under the feature's
#: own name.
_USABLE_SUFFIX = "_Usable"

#: The start of the warning with which glibc's loader, from 2.39 on, drops a
#: whole ``GLIBC_TUNABLES`` that holds an ill-formed entry (commits
#: 680c597e9c36, "elf: Do not parse ill-formatted strings", and eb9291aaa6ff,
#: "elf: Emit warning if tunable is ill-formatted"); a loader without it
#: applies every entry it can read.
_ILL_FORMED_WARNING = b"invalid GLIBC_TUNABLES `"

#: The first glibc that ships ARM's ``exp``, ``log`` and ``pow``: the commits
#: that put them in place of IBM's (e70c17682518, f41b0a43e426 and
#: 424c4f60ed61) came after the 2.28 release, so 2.28 runs IBM's routines.
_FIRST_GLIBC = (2, 29)

#: The environment variable through which glibc masks processor features.
TUNABLES = "GLIBC_TUNABLES"

#: The value that makes glibc built for the x86-64 baseline take its variants
#: without FMA, in every spelling glibc has read the mask in, so that every
#: glibc reads it: each one ignores a tunable and a name it does not know.
WITHOUT_FMA = (
    "glibc.cpu.hwcaps=-AVX2,-FMA,-FMA4,-AVX,"
    "-AVX2_Usable,-FMA_Usable,-FMA4_Usable,-AVX_Usable"
    ":glibc.tune.hwcaps=-AVX2_Usable,-FMA_Usable,-FMA4_Usable,-AVX_Usable"
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

#: The file name of glibc's dynamic loader as ``/proc/self/maps`` names it:
#: ``ld-linux-x86-64.so.2`` since glibc 2.34 and ``ld-2.31.so`` before.
_LOADER_FILE_NAME = re.compile(r"ld-linux-x86-64\.so\.2|ld-\d+(?:\.\d+)+\.so")


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


@dataclasses.dataclass(frozen=True)
class Unread:
    """An object of this process's glibc that cannot be named or read, and why.

    It stands for a build or a reading of the mask that cannot be told, which
    is neither the baseline build nor the build for x86-64-v3, nor any
    reading: a truth test of it raises, so that no caller takes it for one.

    :ivar reason: What could not be read, as a skip names it.
    """

    reason: str

    def __bool__(self) -> NoReturn:
        """Refuse a truth test: what cannot be read is neither answer."""
        msg = f"what cannot be read is neither true nor false: {self.reason}"
        raise TypeError(msg)


@dataclasses.dataclass(frozen=True)
class MaskReading:
    """How a glibc's dynamic loader reads a mask of processor features.

    :ivar tunables: The tunables it reads the mask from.
    :ivar fma_variant_names: The names that, masked, take glibc off its FMA
        variant: ``FMA_Usable`` and ``AVX2_Usable`` up to glibc 2.31, ``FMA``
        and ``AVX2`` from 2.32.
    :ivar drops_ill_formed: Whether an ill-formed entry anywhere in
        ``GLIBC_TUNABLES`` makes it ignore the whole variable, as glibc does
        from 2.39 on.
    """

    tunables: frozenset[str]
    fma_variant_names: frozenset[str]
    drops_ill_formed: bool


#: The reading of a loader that cannot be read: a mask counts in any spelling,
#: in either tunable, so that a process that may run another variant is not
#: held to the pins.
ANY_READING = MaskReading(
    tunables=frozenset(_HWCAPS_TUNABLES),
    fma_variant_names=frozenset(
        feature + suffix
        for feature in _FMA_VARIANT_FEATURES
        for suffix in ("", _USABLE_SUFFIX)
    ),
    drops_ill_formed=False,
)


def _named(name: str, image: bytes) -> bool:
    """Whether ``image`` holds ``name`` as a string of its own."""
    return name.encode("ascii") + b"\0" in image


def mask_reading(loader: bytes) -> MaskReading | None:
    """How the dynamic loader whose bytes are ``loader`` reads the mask.

    The loader's parser compares the tunable's name and each feature's name
    with strings the loader carries, so they are read from its image: a
    ``_Usable`` name there is the one that masks that feature's usable bit,
    and the feature's own name otherwise.

    :param loader: The bytes of glibc's dynamic loader.
    :return: The reading, or ``None`` when the image names no tunable that
        masks processor features.
    """
    tunables = frozenset(name for name in _HWCAPS_TUNABLES if _named(name, loader))
    if not tunables:
        return None
    return MaskReading(
        tunables=tunables,
        fma_variant_names=frozenset(
            feature + _USABLE_SUFFIX
            if _named(feature + _USABLE_SUFFIX, loader)
            else feature
            for feature in _FMA_VARIANT_FEATURES
        ),
        drops_ill_formed=_ILL_FORMED_WARNING in loader,
    )


def _ill_formed(entries: list[str]) -> bool:
    """Whether glibc 2.39's parser refuses ``GLIBC_TUNABLES`` cut at its colons.

    It refuses a value that holds an ``=`` and a last entry without one
    (``parse_tunables_string`` in ``elf/dl-tunables.c``); an entry without one
    before a colon it skips.
    """
    return "=" not in entries[-1] or any(entry.count("=") > 1 for entry in entries)


def masks_the_fma_variant(tunables: str, reading: MaskReading) -> bool:
    """Whether a ``GLIBC_TUNABLES`` value takes glibc off its FMA variant.

    :param tunables: The value of ``GLIBC_TUNABLES``.
    :param reading: How the loader reads it.
    :return: ``True`` when, of a tunable the loader reads, the last setting
        masks, as written, a name that takes glibc off its FMA variant;
        ``False`` otherwise, and for a value the loader drops whole. Each
        tunable keeps its own last setting: a loader reads one of them, so a
        reading that names both counts a mask in either, whatever setting of
        the other follows it.
    """
    if not tunables:
        return False
    entries = tunables.split(":")
    if reading.drops_ill_formed and _ill_formed(entries):
        return False
    settings: dict[str, str] = {}
    for entry in entries:
        name, equals, value = entry.partition("=")
        if equals and name in reading.tunables:
            settings[name] = value
    masked = (
        {part[1:] for part in setting.split(",") if part.startswith("-")}
        for setting in settings.values()
    )
    return any(not names.isdisjoint(reading.fma_variant_names) for names in masked)


def glibc_on_x86_64_with_fma() -> bool:
    """glibc 2.29 or later on an x86-64 processor that reports FMA and AVX2.

    2.29 is the first glibc whose ``exp``, ``log`` and ``pow`` are the routines
    the pins spell (:data:`_FIRST_GLIBC`).
    """
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


def _segments(image: bytes) -> list[tuple[int, int, int, int]] | None:
    """The segments of a whole little-endian 64-bit x86-64 ELF image, or ``None``.

    The image is whole where its header, its program header table and the
    bytes each segment takes from the file all lie within it.

    :return: Each segment's type, file offset, size in the file and
        alignment, in the order of the table; ``None`` for any other image.
    """
    if image[:6] != b"\x7fELF\x02\x01" or len(image) < 64:
        return None
    (machine,) = struct.unpack_from("<H", image, 18)
    if machine != _EM_X86_64:
        return None
    (table,) = struct.unpack_from("<Q", image, 32)
    entry_size, entries = struct.unpack_from("<HH", image, 54)
    segments: list[tuple[int, int, int, int]] = []
    for index in range(entries):
        start = table + index * entry_size
        if start + 56 > len(image):
            return None
        kind, _, offset, _, _, size, _, alignment = struct.unpack_from(
            "<IIQQQQQQ", image, start
        )
        if offset + size > len(image):
            return None
        segments.append((kind, offset, size, alignment))
    return segments


def x86_isa_levels_needed(image: bytes) -> int | None:
    """The ISA levels a 64-bit x86-64 ELF object declares it needs.

    The value is the ``GNU_PROPERTY_X86_ISA_1_NEEDED`` property of the
    object's ``NT_GNU_PROPERTY_TYPE_0`` note, one bit per level from bit 0,
    the x86-64 baseline: ``0b111`` is a build for x86-64-v3. It is read from
    the segments glibc's loader reads it from, ``PT_GNU_PROPERTY`` first and
    then ``PT_NOTE``, in each the 8-byte aligned notes a 64-bit object carries.

    :param image: The bytes of the object file.
    :return: The property's bits, or ``None`` when the image is no whole
        little-endian 64-bit x86-64 ELF object (:func:`_segments`) or
        declares no level.
    """
    segments = _segments(image)
    if segments is None:
        return None
    # False sorts first, so PT_GNU_PROPERTY is read before PT_NOTE.
    notes = sorted(
        (kind != _PT_GNU_PROPERTY, offset, size)
        for kind, offset, size, alignment in segments
        if kind in (_PT_GNU_PROPERTY, _PT_NOTE) and alignment == 8
    )
    for _, offset, size in notes:
        needed = _needed_in_notes(image[offset : offset + size])
        if needed is not None:
            return needed
    return None


def _resolved(symbol: str) -> tuple[int, Path | None] | None:
    """Where this process's default namespace resolves ``symbol``, or ``None``.

    The symbol is looked up as the default namespace resolves it, the
    namespace :mod:`math` and the interpreter are linked in, and glibc's
    loader names the object that holds its address through ``dladdr``, by the
    path it found that object by.

    :return: The symbol's address and the file ``dladdr`` names, the file
        ``None`` where ``dladdr`` cannot be found or names none; ``None`` off
        Linux, without :mod:`ctypes` or where the symbol cannot be found.
    """
    if platform.system() != "Linux":
        return None
    try:
        # Imported here: an interpreter built without libffi has no ctypes,
        # and the caller then reads /proc/self/maps instead.
        import ctypes  # noqa: PLC0415
    except ImportError:
        return None

    class DlInfo(ctypes.Structure):
        _fields_ = (
            ("dli_fname", ctypes.c_char_p),
            ("dli_fbase", ctypes.c_void_p),
            ("dli_sname", ctypes.c_char_p),
            ("dli_saddr", ctypes.c_void_p),
        )

    try:
        address = ctypes.cast(getattr(ctypes.CDLL(None), symbol), ctypes.c_void_p)
    except (AttributeError, OSError):
        return None
    if address.value is None:
        return None
    # dladdr is in libc from glibc 2.34 and in libdl before.
    for library in (None, "libdl.so.2"):
        try:
            dladdr = ctypes.CDLL(library).dladdr
        except (AttributeError, OSError):
            continue
        dladdr.argtypes = (ctypes.c_void_p, ctypes.POINTER(DlInfo))
        dladdr.restype = ctypes.c_int
        info = DlInfo()
        if not dladdr(address, ctypes.byref(info)) or not info.dli_fname:
            return address.value, None
        return address.value, Path(os.fsdecode(info.dli_fname))
    return address.value, None


def _mappings() -> list[tuple[int, int, Path]]:
    """The files ``/proc/self/maps`` lists, each with the range it is mapped at.

    The kernel names each file by its absolute path, wherever the process is.

    :return: The mappings in the order listed.
    :raises OSError: where ``/proc/self/maps`` cannot be read.
    """
    maps = Path("/proc/self/maps").read_text(encoding="utf-8", errors="replace")
    mapped = []
    for line in maps.splitlines():
        fields = line.split(maxsplit=5)
        if len(fields) == 6 and fields[5].startswith("/"):
            start, _, end = fields[0].partition("-")
            mapped.append((int(start, 16), int(end, 16), Path(fields[5])))
    return mapped


def _first_mapped(
    file_name: re.Pattern[str], mapped: list[tuple[int, int, Path]]
) -> Path | None:
    """The first file of *mapped* whose name matches, or ``None``."""
    for _, _, file in mapped:
        if file_name.fullmatch(file.name):
            return file
    return None


def _mapped_at(address: int, mapped: list[tuple[int, int, Path]]) -> Path | None:
    """The file of *mapped* at ``address``, or ``None``."""
    for start, end, file in mapped:
        if start <= address < end:
            return file
    return None


def _unnamed(symbol: str, resolved: tuple[int, Path | None] | None) -> str:
    """How looking ``symbol`` up left its object without an absolute name."""
    if resolved is None:
        return f"{symbol} cannot be looked up here"
    if resolved[1] is None:
        return f"dladdr names no file for the object that defines {symbol}"
    return (
        f"dladdr names the object that defines {symbol} by the relative path "
        f"{resolved[1]}"
    )


def _object_defining(
    symbol: str, file_name: re.Pattern[str], kind: str
) -> Path | Unread:
    """The file of the object that defines ``symbol`` for this process.

    It is the file ``dladdr`` names, where it names it by an absolute path.
    glibc's loader names an object by the path it found it by, so a relative
    entry of ``LD_LIBRARY_PATH``, or the loader run by a relative path, gives a
    name relative to the directory the process was in, which names another
    file or none once it changes directory. The object is then the file the
    kernel maps at the symbol's address, and never a file found by its name:
    the first one ``/proc/self/maps`` lists may be one that ``dlmopen`` loaded
    into another namespace. Only where the symbol cannot be looked up
    (:func:`_resolved`) is it the first file listed whose name matches
    ``file_name``.

    :param kind: What the object is, as a reason names it.
    :return: The object's file, or what could not be read where nothing
        names it: ``/proc/self/maps``, or the file at the address or of the
        name it does not list.
    """
    resolved = _resolved(symbol)
    if resolved is not None and resolved[1] is not None and resolved[1].is_absolute():
        return resolved[1]
    how = _unnamed(symbol, resolved)
    try:
        mapped = _mappings()
    except OSError as error:
        return Unread(
            f"{how}, and /proc/self/maps cannot be read ({error.strerror or error})"
        )
    if resolved is None:
        file = _first_mapped(file_name, mapped)
        missing = f"lists no {kind} of glibc's"
    else:
        file = _mapped_at(resolved[0], mapped)
        missing = f"lists no file at its address {resolved[0]:#x}"
    if file is None:
        return Unread(f"{how}, and /proc/self/maps {missing}")
    return file


def loaded_libm() -> Path | Unread:
    """The file of the ``libm`` whose routines :mod:`math` calls.

    It is the object that defines ``exp`` where this process's default
    namespace resolves it (:func:`_object_defining`), so a ``libm`` another
    namespace mapped first is not taken for it. :mod:`math` is imported first,
    so that library is mapped whether the interpreter links it or the module
    does.

    :return: The file, or what could not be read where nothing names it.
    """
    importlib.import_module("math")
    return _object_defining("exp", _LIBM_FILE_NAME, "libm")


def loaded_loader() -> Path | Unread:
    """The file of the dynamic loader this process runs.

    It is the object that defines ``__tls_get_addr``, which glibc's loader
    exports, where the default namespace resolves it
    (:func:`_object_defining`).

    :return: The file, or what could not be read where nothing names it.
    """
    return _object_defining("__tls_get_addr", _LOADER_FILE_NAME, "dynamic loader")


def loader_reading() -> MaskReading | Unread:
    """How this process's loader reads the mask, or what could not be read.

    :return: The reading of the loader's image; an :class:`Unread` where the
        loader cannot be named or read, or names no tunable that masks
        processor features, as glibc's before 2.26 and one built without
        tunables do.
    """
    loader = loaded_loader()
    if isinstance(loader, Unread):
        return loader
    try:
        image = loader.read_bytes()
    except OSError as error:
        return Unread(
            f"the dynamic loader {loader} cannot be read ({error.strerror or error})"
        )
    reading = mask_reading(image)
    if reading is None:
        return Unread(
            f"the dynamic loader {loader} names no tunable that masks processor "
            "features"
        )
    return reading


def mask_reading_here() -> MaskReading:
    """How this process's loader reads the mask, or :data:`ANY_READING`.

    :return: :func:`loader_reading`'s reading, or :data:`ANY_READING` where
        that is an :class:`Unread`, so that a process whose loader reads the
        mask in a way that cannot be told is not held to the pins under one.
    """
    reading = loader_reading()
    return ANY_READING if isinstance(reading, Unread) else reading


def glibc_built_for_x86_64_v3() -> bool | Unread:
    """Whether this process runs a glibc built for x86-64-v3 or above.

    Such a glibc compiles ``exp``, ``log``, ``pow``, ``sin``, ``tan`` and
    ``atan`` for a processor with FMA and AVX2 and carries no variant without
    them for ``GLIBC_TUNABLES`` to select. It is read from the ISA level the
    ``libm`` :mod:`math` calls (:func:`loaded_libm`) declares it needs, never
    from whether a masked process's routines agree with this one's.

    :return: ``True`` when the ``libm`` of glibc on x86-64 Linux names
        x86-64-v3 or a higher level as needed; ``False`` for a build for a
        lower level, for an object that names none, and on any other
        platform; an :class:`Unread` where that ``libm`` cannot be named or
        read, or the file read is no whole x86-64 ELF object, so that its
        build is taken for neither.
    """
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        return False
    if _glibc_version() is None:
        return False
    library = loaded_libm()
    if isinstance(library, Unread):
        return library
    try:
        image = library.read_bytes()
    except OSError as error:
        return Unread(f"the libm {library} cannot be read ({error.strerror or error})")
    if _segments(image) is None:
        return Unread(f"the libm {library} is no whole 64-bit x86-64 ELF object")
    needed = x86_isa_levels_needed(image)
    return needed is not None and needed >= _X86_ISA_1_V3


#: Why a test of a pinned routine skips on a C library that is not the one the
#: pins spell.
_NOT_THE_PINNED_LIBM = (
    "the C library here is not the glibc FMA variant the pinned routines "
    "spell; their bits are the contract, the local library's are not"
)


def why_off_the_pinned_routines() -> str | None:
    """Why this process's ``math`` module is not known to call the pinned routines.

    A mask takes glibc off its FMA variant only where glibc carries another:
    a process on a glibc built for x86-64-v3 runs the FMA routines under any
    mask. Elsewhere it does when this process's loader reads it so. A mask
    that may count, on a glibc whose build or whose loader's reading cannot
    be told, leaves the process off the pins by what could not be read.

    :return: ``None`` where this process runs the routines the pins spell;
        otherwise why it is not known to.
    """
    if not glibc_on_x86_64_with_fma():
        return _NOT_THE_PINNED_LIBM
    build = glibc_built_for_x86_64_v3()
    if build is True:
        return None
    if not masks_the_fma_variant(os.environ.get(TUNABLES, ""), mask_reading_here()):
        return None
    if isinstance(build, Unread):
        return (
            f"{TUNABLES} may take glibc here off its FMA variant, and the build "
            f"of glibc here cannot be told: {build.reason}"
        )
    reading = loader_reading()
    if isinstance(reading, Unread):
        return (
            f"{TUNABLES} may mask FMA or AVX2, and how this process's loader reads "
            f"a mask cannot be told: {reading.reason}"
        )
    return _NOT_THE_PINNED_LIBM


def runs_the_pinned_routines() -> bool:
    """Whether this process's ``math`` module calls the routines the pins spell.

    It does where :func:`why_off_the_pinned_routines` finds no reason why not.
    """
    return why_off_the_pinned_routines() is None


def run_child(
    args: Sequence[str],
    *,
    timeout: float,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> str:
    """The output of a child these tests start, run to a status of 0.

    A system that refuses to start the program, as one whose file or whose
    loader sits on a mount made ``noexec`` once this process started, raises
    :class:`PermissionError` before the child runs, and the test skips,
    naming the program and the refusal. Whatever the child does once it
    runs, its status included, is the test's.

    :raises subprocess.CalledProcessError: for a status other than 0.
    """
    try:
        # Fixed argv, no shell: the tests' own programs and arguments
        finished = subprocess.run(  # nosec B603
            list(args),
            check=False,
            capture_output=True,
            text=True,
            cwd=cwd,
            env=env,
            timeout=timeout,
        )
    except PermissionError as refused:
        where = "" if cwd is None else f" from {cwd}"
        pytest.skip(
            f"this system refuses to start {args[0]}{where} "
            f"({refused.strerror or refused}), so the child that would be read "
            "never runs"
        )
    finished.check_returncode()
    return finished.stdout


#: Why the tests of the pinned routines skip here, or ``None`` where they run.
_OFF_THE_PINS = why_off_the_pinned_routines()

#: Marks a test that compares a pinned routine bit for bit with :mod:`math`.
on_the_pinned_libm = pytest.mark.skipif(
    _OFF_THE_PINS is not None, reason=_OFF_THE_PINS or ""
)
