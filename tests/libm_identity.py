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

glibc picks its FMA variant of ``exp``, ``log``, ``pow``, ``sin``, ``tan`` and
``atan`` when the processor reports both FMA and AVX2 as usable, so masking
FMA, AVX2 or AVX through ``GLIBC_TUNABLES`` (``glibc.cpu.hwcaps=-FMA``) hands
the same process the other variant.
"""

from __future__ import annotations

import os
import platform
from pathlib import Path

import pytest

#: The processor features whose masking takes glibc off its FMA variant.
_FMA_VARIANT_FEATURES = frozenset({"FMA", "AVX2", "AVX"})

#: The first glibc that ships ARM's ``exp``, ``log`` and ``pow``.
_FIRST_GLIBC = (2, 28)

#: The environment variable through which glibc masks processor features.
TUNABLES = "GLIBC_TUNABLES"

#: The value that makes glibc on x86-64 take the variants without FMA.
WITHOUT_FMA = "glibc.cpu.hwcaps=-AVX2,-FMA,-FMA4,-AVX"


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
    """Whether a ``GLIBC_TUNABLES`` value takes glibc off its FMA variant."""
    for item in tunables.split(":"):
        name, _, value = item.partition("=")
        if name.strip() != "glibc.cpu.hwcaps":
            continue
        masked = {
            part.strip()[1:].upper().removesuffix("_USABLE")
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


def runs_the_pinned_routines() -> bool:
    """Whether this process's ``math`` module calls the routines the pins spell."""
    if not glibc_on_x86_64_with_fma():
        return False
    return not masks_the_fma_variant(os.environ.get(TUNABLES, ""))


#: Marks a test that compares a pinned routine bit for bit with :mod:`math`.
on_the_pinned_libm = pytest.mark.skipif(
    not runs_the_pinned_routines(),
    reason="the C library here is not the glibc FMA variant the pinned routines "
    "spell; their bits are the contract, the local library's are not",
)
