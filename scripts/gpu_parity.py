#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Prove on a GPU what CuPy does with the FDTD engines, and write it down.

Runs every scenario of ``engine_scenarios`` on NumPy and on CuPy in this
process and compares every number ``engine_scenarios.run`` returns, key by
key: whether the two runs agree bit for bit, and the largest absolute and
relative difference. The stored fields, the snapshot frames and the
collocated velocities are stepped cell by cell, so they are held to bit for
bit. The energy is a sum over the cells, which a GPU adds in another order,
so its relative difference is reported apart. The contour phasors are
running sums kept cell by cell in float64; whether they agree bit for bit is
recorded too. A value that is not finite, or a NumPy reference that is all
zero, stops the run with nothing written.

The reference is NumPy in float64 whatever :func:`~phonometry.simulation.use`
or ``PHONOMETRY_COMPUTE`` say, and each run is refused unless its engine
recorded the device it was asked for. The engine measured has to be the one
fingerprinted, so a ``phonometry`` imported from anywhere but this checkout's
``src`` stops the run too: ``make gpu-parity`` puts ``src`` on the path.

``--write`` records the outcome in ``gpu-parity.lock`` with the NVIDIA
driver, the CUDA and CuPy versions, the base image when the run is in
``docker/node/Dockerfile``'s image, and a fingerprint of the engine's code
and its scenario matrix, which ``tests/simulation/test_gpu_parity_lock.py``
checks on every pull request. Run it with ``make gpu-parity`` on a machine
with CuPy and an NVIDIA GPU.
"""

from __future__ import annotations

import argparse
import ast
import datetime as dt
import hashlib
import json
import pathlib
import platform
import re
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, replace
from typing import TYPE_CHECKING, Any, Literal

import engine_scenarios as es
import numpy as np

from phonometry.simulation import Compute, elastic_fdtd, fdtd
from phonometry.simulation import _backends as bk

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from types import ModuleType

    from numpy.typing import NDArray

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_LOCK = _ROOT / "gpu-parity.lock"
#: The files the proof covers: the two engines, the backends they step on,
#: and the scenario matrix, since a changed scenario is a claim nobody has
#: measured yet. compute.py stays out: it only reads which device a run asks
#: for, and every run here is checked for the device it used. This script
#: stays out too: it is the instrument, held by its own tests, and covering it
#: would ask for a GPU at every edit of a message.
_COVERED = (
    _ROOT / "src/phonometry/simulation/fdtd.py",
    _ROOT / "src/phonometry/simulation/elastic_fdtd.py",
    _ROOT / "src/phonometry/simulation/_backends.py",
    _ROOT / "scripts/engine_scenarios.py",
)
#: Where docker/node/Dockerfile leaves a copy of itself in the image.
_IMAGE_DOCKERFILE = pathlib.Path("/usr/local/share/phonometry-node/Dockerfile")

#: What every reference run steps on: NumPy in float64, named outright so
#: that neither ``use()`` nor ``PHONOMETRY_COMPUTE`` can move it.
REFERENCE = Compute()
#: The run the proof is about.
GPU = Compute(device="cupy")

Kind = Literal["field", "reduction", "phasor"]

#: Stepped cell by cell: held to bit for bit.
_FIELDS = frozenset(
    {"p", "vx", "vy", "txx", "tyy", "txy", "frames", "collocated_vx", "collocated_vy"}
)
#: Summed over the cells, in whatever order the device adds.
_REDUCTIONS = frozenset({"energy"})
#: ``contour<k>_<frequency>_<p|v>``: running sums kept cell by cell.
_PHASOR = re.compile(r"contour\d+_[^_]+_[pv]")

#: The nodes whose first string statement is a docstring.
_DOCUMENTED = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


class ParityError(RuntimeError):
    """A run that cannot stand as a proof, so nothing is written."""


def _canonical(node: object) -> object:
    """*node* as nested lists, with every field that is ``None`` or empty left out.

    ``ast.dump`` prints those fields up to Python 3.12 and leaves them out
    from 3.13, so its text, and a hash of it, depend on the interpreter.
    Leaving them out here gives one form on every Python.
    """
    if isinstance(node, ast.AST):
        fields = [
            [name, _canonical(value)]
            for name, value in ast.iter_fields(node)
            if value is not None and not (isinstance(value, list) and not value)
        ]
        return [type(node).__name__, fields]
    if isinstance(node, list):
        return [_canonical(item) for item in node]
    return repr(node)


def source_fingerprint(text: str) -> str:
    """SHA-256 of *text*'s syntax tree with every docstring removed.

    Comments, blank lines, line endings and layout are not in the tree, so
    they do not move it either.
    """
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if (
            isinstance(node, _DOCUMENTED)
            and ast.get_docstring(node, clean=False) is not None
        ):
            node.body.pop(0)
    return hashlib.sha256(json.dumps(_canonical(tree)).encode()).hexdigest()


def engine_fingerprint() -> str:
    """The fingerprint of the files the proof covers, the engine and its scenarios."""
    parts = [source_fingerprint(path.read_text(encoding="utf-8")) for path in _COVERED]
    return hashlib.sha256("".join(parts).encode()).hexdigest()


def imported_sources() -> tuple[tuple[str, pathlib.Path], ...]:
    """Each module the run measures, where it was imported from and its covered file."""
    found = (fdtd.__file__, elastic_fdtd.__file__, bk.__file__, es.__file__)
    return tuple(zip(found, _COVERED, strict=True))


def require_covered(imported: Iterable[tuple[str, pathlib.Path]]) -> None:
    """Refuse a run whose modules are not the files the fingerprint covers.

    :param imported: ``(file a module was imported from, covered file)``.
    :raises ParityError: naming the first module imported from elsewhere,
        such as an installed ``phonometry`` that is another checkout's.
    """
    for found, covered in imported:
        if pathlib.Path(found).resolve() != covered.resolve():
            msg = (
                f"{found} was imported, not the fingerprinted {covered}; "
                "put this checkout's src first on the path (make gpu-parity does)"
            )
            raise ParityError(msg)


def base_image_of(dockerfile: str) -> str | None:
    """The image the ``gpu`` stage of *dockerfile* starts from, digest included."""
    match = re.search(
        r"^FROM\s+(\S+)\s+AS\s+gpu\s*$", dockerfile, flags=re.MULTILINE | re.IGNORECASE
    )
    return match.group(1) if match else None


def kind_of(key: str) -> Kind:
    """How the key *key* of an ``engine_scenarios.run`` result is compared.

    :raises ParityError: for a key this proof does not know, so that a new
        one is classed here before it is proven.
    """
    if key in _FIELDS:
        return "field"
    if key in _REDUCTIONS:
        return "reduction"
    if _PHASOR.fullmatch(key):
        return "phasor"
    msg = f"{key!r} is a key gpu_parity does not class; add it to scripts/gpu_parity.py"
    raise ParityError(msg)


@dataclass(frozen=True, kw_only=True)
class KeyResult:
    """One key of one scenario, CuPy against NumPy.

    :ivar kind: ``"field"``, ``"reduction"`` or ``"phasor"``.
    :ivar bit_identical: The same dtype, shape and bytes.
    :ivar max_abs: ``max|got - want|`` (the modulus, for a complex key).
    :ivar max_relative: ``max_abs / max|want|``.
    """

    kind: Kind
    bit_identical: bool
    max_abs: float
    max_relative: float


def _require_finite(where: str, run: str, values: NDArray[Any]) -> None:
    if values.size == 0:
        msg = f"{where}: the {run} run holds nothing to compare"
        raise ParityError(msg)
    if not np.all(np.isfinite(values)):
        msg = f"{where}: the {run} run holds a value that is not finite"
        raise ParityError(msg)


def compare(where: str, got: NDArray[Any], want: NDArray[Any]) -> KeyResult:
    """CuPy's *got* against NumPy's *want* at *where*, ``"<scenario>/<key>"``.

    :raises ParityError: if either run holds a value that is not finite or
        nothing at all, if CuPy gave another dtype or shape, or if the NumPy
        reference is all zero, which leaves a relative difference nothing to
        scale by.
    """
    kind = kind_of(where.rsplit("/", 1)[-1])
    _require_finite(where, "NumPy", want)
    _require_finite(where, "CuPy", got)
    if got.dtype != want.dtype or got.shape != want.shape:
        msg = (
            f"{where}: CuPy gave {got.dtype} {got.shape}, "
            f"NumPy {want.dtype} {want.shape}"
        )
        raise ParityError(msg)
    scale = float(np.abs(want).max())
    if scale <= 0.0:
        msg = (
            f"{where}: the NumPy reference is all zero, so a relative "
            "difference has nothing to scale by"
        )
        raise ParityError(msg)
    worst = float(np.abs(got - want).max())
    return KeyResult(
        kind=kind,
        bit_identical=got.tobytes() == want.tobytes(),
        max_abs=worst,
        max_relative=worst / scale,
    )


def compare_scenario(
    name: str, got: Mapping[str, NDArray[Any]], want: Mapping[str, NDArray[Any]]
) -> dict[str, KeyResult]:
    """Every key of scenario *name*, CuPy's *got* against NumPy's *want*."""
    if got.keys() != want.keys():
        msg = f"{name}: the CuPy run returns {sorted(got)}, NumPy {sorted(want)}"
        raise ParityError(msg)
    return {key: compare(f"{name}/{key}", got[key], want[key]) for key in sorted(want)}


def _worst(
    results: Mapping[str, Mapping[str, KeyResult]],
    kind: Kind,
    attribute: Literal["max_abs", "max_relative"],
) -> dict[str, float]:
    """The largest *attribute* over the *kind* keys, per scenario that has one."""
    worst: dict[str, float] = {}
    for scenario, keys in results.items():
        values = [getattr(r, attribute) for r in keys.values() if r.kind == kind]
        if values:
            worst[scenario] = max(values)
    return worst


def _all_identical(results: Mapping[str, Mapping[str, KeyResult]], kind: Kind) -> bool:
    return all(
        r.bit_identical
        for keys in results.values()
        for r in keys.values()
        if r.kind == kind
    )


def summarise(results: Mapping[str, Mapping[str, KeyResult]]) -> dict[str, object]:
    """The verdicts the lock opens with, from the key by key *results*."""
    return {
        "fields_bit_identical": _all_identical(results, "field"),
        "max_abs_difference": _worst(results, "field", "max_abs"),
        "fields_max_relative": _worst(results, "field", "max_relative"),
        "reductions_max_relative": _worst(results, "reduction", "max_relative"),
        "phasors_bit_identical": _all_identical(results, "phasor"),
        "phasors_max_relative": _worst(results, "phasor", "max_relative"),
    }


def run_on(
    scenario: es.Scenario, module: ModuleType, compute: Compute
) -> dict[str, NDArray[Any]]:
    """``engine_scenarios.run`` on *compute*, refused unless it stepped there.

    :raises ParityError: when the engine recorded another device or dtype
        than *compute* names.
    """
    built: list[es.Engine] = []

    def build(m: ModuleType, kwargs: dict[str, Any]) -> es.Engine:
        engine = scenario.build(m, kwargs)
        built.append(engine)
        return engine

    out = es.run(replace(scenario, build=build), module, compute=compute)
    used = built[0].provenance
    if (used.device, used.dtype) != (compute.device, compute.dtype):
        msg = (
            f"{scenario.name}: a run asked for {compute.device} {compute.dtype} "
            f"stepped on {used.device} {used.dtype}"
        )
        raise ParityError(msg)
    return out


def _timed_run(
    scenario: es.Scenario, module: ModuleType, compute: Compute
) -> tuple[dict[str, NDArray[Any]], float]:
    """:func:`run_on` and the seconds it took."""
    start = time.perf_counter()
    out = run_on(scenario, module, compute)
    return out, time.perf_counter() - start


def _nvidia_driver(index: int) -> str:
    """The NVIDIA driver version of GPU *index*, as ``nvidia-smi`` reports it."""
    smi = shutil.which("nvidia-smi")
    if smi is None:
        msg = "nvidia-smi is not on the path, so the NVIDIA driver cannot be recorded"
        raise ParityError(msg)
    query = [
        smi,
        "-i",
        str(index),
        "--query-gpu=driver_version",
        "--format=csv,noheader",
    ]
    done = subprocess.run(query, capture_output=True, text=True, check=False)
    if done.returncode != 0:
        msg = f"nvidia-smi failed ({done.returncode}): {done.stderr.strip()}"
        raise ParityError(msg)
    return done.stdout.strip()


def _platform_record() -> dict[str, object]:
    """Where the proof ran: GPU, driver, CUDA, CuPy, NVRTC, Python, base image."""
    # Imported here: only a machine with a GPU has it.
    import cupy

    provenance = bk.backend_for(GPU).provenance
    major, minor = cupy.cuda.nvrtc.getVersion()
    base = (
        base_image_of(_IMAGE_DOCKERFILE.read_text(encoding="utf-8"))
        if _IMAGE_DOCKERFILE.is_file()
        else None
    )
    return {
        "gpu": provenance.gpu,
        "nvidia_driver": _nvidia_driver(GPU.device_index),
        "cuda_driver_api": provenance.cuda_driver_api,
        "cupy": cupy.__version__,
        "cupy_cuda_runtime": provenance.cuda_runtime,
        "nvrtc": f"{major}.{minor}",
        "numpy": np.__version__,
        "python": platform.python_version(),
        "base_image": base,
    }


def measure() -> dict[str, object]:
    """Run every scenario on NumPy and CuPy and compare them.

    The timings go to standard error; the first CuPy scenario of a process
    also compiles its kernels.

    :raises ParityError: when a module measured is not the fingerprinted
        file, a run did not step where it was asked to, or a comparison
        cannot stand (:func:`compare`).
    """
    require_covered(imported_sources())
    record = _platform_record()
    results: dict[str, dict[str, KeyResult]] = {}
    for scenario in es.SCENARIOS:
        module = fdtd if scenario.kind == "acoustic" else elastic_fdtd
        want, on_numpy = _timed_run(scenario, module, REFERENCE)
        got, on_cupy = _timed_run(scenario, module, GPU)
        print(
            f"{scenario.name}: NumPy {on_numpy:.3f} s, CuPy {on_cupy:.3f} s",
            file=sys.stderr,
        )
        results[scenario.name] = compare_scenario(scenario.name, got, want)
    return {
        "engine_fingerprint": engine_fingerprint(),
        **record,
        "measured_on": dt.datetime.now(dt.UTC).date().isoformat(),
        **summarise(results),
        "keys": {
            name: {key: asdict(r) for key, r in keys.items()}
            for name, keys in results.items()
        },
    }


def main(argv: list[str] | None = None) -> int:
    """Measure, print the record, and with ``--write`` keep it in the lock."""
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--write", action="store_true", help="write gpu-parity.lock")
    args = parser.parse_args(argv)
    try:
        result = measure()
    except ParityError as exc:
        print(f"gpu_parity: {exc}; nothing written", file=sys.stderr)
        return 1
    text = json.dumps(result, indent=1, sort_keys=True) + "\n"
    sys.stdout.write(text)
    if args.write:
        _LOCK.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
