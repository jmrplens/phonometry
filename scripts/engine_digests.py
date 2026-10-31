#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The engines' NumPy numbers, reduced to SHA-256 digests and held still.

Before the FDTD engines could step on other array backends, a frozen copy of
them stood in the test suite, and every runner compared the refactored
engines with it bit for bit. That proved the refactor; it cannot keep
proving the next change, because the copy has to go some day. What stays is
this: every scenario of ``engine_scenarios`` stepped on NumPy in float64,
every array it returns reduced to a digest of its dtype, shape and bytes,
and the fluid branch of the elastic energy recorded exactly, all written to
``engine-digests.json`` at the root of the repository.

The bits depend on the platform (the C library's libm, and NumPy's SIMD
dispatch), so the file records the environment it was measured in, and the
one CI job that measures it is the one that checks it
(``tests/simulation/test_engine_golden_digests.py``); the committed file is
that job's measurement. NumPy's AVX-512 kernels are switched off there and
here (``NPY_DISABLE_CPU_FEATURES``, see :func:`avx512_features`), so a runner
with AVX-512 and one without compute the same bits. The engines step on
NumPy whatever ``use()`` or ``PHONOMETRY_COMPUTE`` ask for.

The documentation clips that step an FDTD engine (the walk of
``animation_fingerprint`` counts every clip whose code reaches
``phonometry.simulation``, which are the field clips) are tied to the
digests and the fluid-energy record of this file, not to the engines'
source and not to the environment the file records
(``animation_fingerprint.engine_digest``). Rewriting an engine so that it
computes the same numbers marks no clip stale; a change that moves a
recorded number fails the CI job until the file is recorded again, and the
new file marks every one of those clips stale.

Usage::

    python scripts/engine_digests.py                    # compare, exit 1 on a moved digest
    python scripts/engine_digests.py --write            # measure and write the file
    python scripts/engine_digests.py --output FILE      # compare, and keep the measurement
    python scripts/engine_digests.py --avx512-features  # what to switch off

A different environment is only reported, unless ``PHONOMETRY_ENGINE_DIGESTS``
is ``require`` (the CI job), where it fails too.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import pathlib
import platform
import sys
from typing import TYPE_CHECKING, Any

import numpy as np

_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_ROOT / "scripts"))

import engine_scenarios as es

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from phonometry.simulation.elastic_fdtd import ElasticFDTD2D

#: Where the digests live, beside ``gpu-parity.lock``.
DIGESTS_FILE = _ROOT / "engine-digests.json"

#: Set to ``require`` (the CI job) to fail on a different environment too.
REQUIRE_ENV = "PHONOMETRY_ENGINE_DIGESTS"

#: The seeds of the fluid-energy record (see :func:`fluid_energy`).
FLUID_SEEDS = (0, 1, 2, 3, 4)

#: A solid at the bound c_p**2 = 2 c_s**2, just under it, so that lambda is
#: clamped to exactly zero (the constructor admits a relative 1e-9 below).
_LAMBDA_ZERO_C_P = 2828.427124
_LAMBDA_ZERO_C_S = 2000.0


def array_digest(array: NDArray[Any]) -> str:
    """SHA-256 of *array*'s dtype, shape and C-ordered bytes."""
    contiguous = np.ascontiguousarray(array)
    digest = hashlib.sha256(f"{contiguous.dtype.str}|{contiguous.shape}|".encode())
    digest.update(contiguous.tobytes())
    return digest.hexdigest()


def fluid_grid() -> ElasticFDTD2D:
    """An all-fluid elastic grid with a small solid patch whose lambda is zero.

    Placed on NumPy whatever ``use()`` or ``PHONOMETRY_COMPUTE`` ask, as
    :func:`numpy_run` is, so its energy is NumPy's in a shell set up for the
    clips too.
    """
    from phonometry.simulation import Compute, elastic_fdtd

    ny, nx = 24, 30
    c_p = np.full((ny, nx), 1480.0)
    c_s = np.zeros((ny, nx))
    rho = np.full((ny, nx), 1000.0)
    c_p[9:15, 12:18] = _LAMBDA_ZERO_C_P
    c_s[9:15, 12:18] = _LAMBDA_ZERO_C_S
    rho[9:15, 12:18] = 2500.0
    return elastic_fdtd.ElasticFDTD2D(
        c_p=c_p, c_s=c_s, dx=0.01, rho=rho, compute=Compute()
    )


def fluid_energy(seed: int) -> float:
    """The energy of :func:`fluid_grid` under seeded random normal stresses.

    No scenario weighs ``p**2 / (2 lam)`` enough to see a rounding in it, so
    the fluid branch of ``energy`` gets a record of its own.
    """
    sim = fluid_grid()
    rng = np.random.default_rng(seed)
    shape = tuple(sim.txx.shape)
    sim.txx[...] = 1e3 * rng.standard_normal(shape)
    sim.tyy[...] = 1e3 * rng.standard_normal(shape)
    return sim.energy()


def avx512_features() -> list[str]:
    """The AVX-512 dispatch targets NumPy would use on this machine, by name.

    Of the targets NumPy was built to dispatch to (``__cpu_dispatch__``),
    those that are AVX-512 and that this machine has (``__cpu_features__``):
    ``NPY_DISABLE_CPU_FEATURES`` switches off dispatch targets and nothing
    else, so a build without an AVX-512 kernel gives none, whatever the CPU
    has. From NumPy 2.4 on the x86 targets are named by microarchitecture
    level: ``X86_V3`` is AVX2 with FMA, and ``X86_V4`` and the ``AVX512_*``
    targets above it are AVX-512. Switching those off leaves an AVX-512
    runner on the kernels of one without. Before 2.4 the AVX-512 targets are
    named one by one (``AVX512F``, ``AVX512_SKX``). Measured under Intel SDE
    (``-skx``) on NumPy 2.5.3: with ``X86_V4`` on, 23 of the digests move;
    with it off, none does.
    """
    module = importlib.import_module("numpy._core._multiarray_umath")
    features: dict[str, bool] = module.__cpu_features__
    dispatch: list[str] = list(module.__cpu_dispatch__)
    return sorted(
        name
        for name in dispatch
        if (name == "X86_V4" or name.startswith("AVX512")) and features.get(name, False)
    )


def environment_required() -> bool:
    """Whether a different environment fails too: :data:`REQUIRE_ENV` is ``require``.

    The CI job that measures the file sets it; anywhere else a different
    environment is only reported, by this script and by the test.
    """
    return os.environ.get(REQUIRE_ENV) == "require"


def environment() -> dict[str, str]:
    """What decides the bits: the platform, its C library (libm), Python, NumPy and its AVX-512 kernels."""
    name, version = platform.libc_ver()
    return {
        "system": platform.system(),
        "machine": platform.machine(),
        "libc": f"{name} {version}" if version else "unknown",
        "python": ".".join(platform.python_version_tuple()[:2]),
        "numpy": np.__version__,
        "numpy_avx512": "on" if avx512_features() else "off",
    }


def cpu_model() -> str:
    """The CPU this measurement ran on, kept beside it and never compared.

    A hosted runner is an Intel or an AMD machine at random; with NumPy's
    AVX-512 kernels off both are expected to give the same bits, and this
    record is what tells the two apart if a digest ever moves between runs.
    """
    cpuinfo = pathlib.Path("/proc/cpuinfo")
    if cpuinfo.exists():
        for line in cpuinfo.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    return platform.processor() or "unknown"


def numpy_run(scenario: es.Scenario) -> dict[str, NDArray[Any]]:
    """*scenario* stepped on NumPy in float64, whatever ``use()`` or ``PHONOMETRY_COMPUTE`` ask.

    A shell set up to render the clips names a GPU in ``PHONOMETRY_COMPUTE``;
    the placement passed here wins over it, so the digests are NumPy's.
    """
    from phonometry.simulation import Compute, elastic_fdtd, fdtd

    module = fdtd if scenario.kind == "acoustic" else elastic_fdtd
    return es.run(scenario, module, compute=Compute())


def measure() -> dict[str, Any]:
    """Step every scenario on NumPy and digest everything it returns."""
    scenarios: dict[str, dict[str, str]] = {}
    for scenario in es.SCENARIOS:
        out = numpy_run(scenario)
        scenarios[scenario.name] = {key: array_digest(out[key]) for key in sorted(out)}
    return {
        "environment": environment(),
        "measured_on": {"cpu": cpu_model()},
        "scenarios": scenarios,
        "fluid_energy": {str(s): float.hex(fluid_energy(s)) for s in FLUID_SEEDS},
    }


def recorded() -> dict[str, Any]:
    """The digests in :data:`DIGESTS_FILE`."""
    data: dict[str, Any] = json.loads(DIGESTS_FILE.read_text(encoding="utf-8"))
    return data


def differences(want: dict[str, Any], got: dict[str, Any]) -> list[str]:
    """Every scenario key and seed whose digest moved, appeared or vanished."""
    problems: list[str] = []
    for name in sorted(want["scenarios"].keys() | got["scenarios"].keys()):
        old = want["scenarios"].get(name, {})
        new = got["scenarios"].get(name, {})
        problems.extend(
            f"{name}: {key}"
            for key in sorted(old.keys() | new.keys())
            if old.get(key) != new.get(key)
        )
    old_e, new_e = want["fluid_energy"], got["fluid_energy"]
    problems.extend(
        f"fluid_energy: seed {seed}"
        for seed in sorted(old_e.keys() | new_e.keys())
        if old_e.get(seed) != new_e.get(seed)
    )
    return problems


def main(argv: list[str] | None = None) -> int:
    """Each mode of the usage above; 1 when a digest moved, or the environment where it is required.

    :raises FileNotFoundError: when there is no :data:`DIGESTS_FILE` to
        compare with (``--write`` records one).
    """
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument(
        "--write", action="store_true", help="measure and write engine-digests.json"
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=None,
        help="also write the measurement here",
    )
    parser.add_argument(
        "--avx512-features",
        action="store_true",
        help="print the AVX-512 features to switch off",
    )
    args = parser.parse_args(argv)
    if args.avx512_features:
        sys.stdout.write(" ".join(avx512_features()) + "\n")
        return 0
    got = measure()
    text = json.dumps(got, indent=1, sort_keys=True) + "\n"
    if args.write:
        DIGESTS_FILE.write_text(text, encoding="utf-8")
        return 0
    if args.output is not None:
        args.output.write_text(text, encoding="utf-8")
    want = recorded()
    problems = [f"moved: {problem}" for problem in differences(want, got)]
    if want["environment"] != got["environment"]:
        note = f"environment: recorded {want['environment']}, here {got['environment']}"
        if environment_required():
            problems.insert(0, note)
        else:
            # Here the numbers may differ for that reason alone; the CI job decides.
            sys.stderr.write(f"note: {note}\n")
    for problem in problems:
        sys.stderr.write(f"{problem}\n")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
