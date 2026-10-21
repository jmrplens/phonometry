#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The CuPy proof in gpu-parity.lock was made on the engine as it stands.

No CI runner has a GPU, so the proof that CuPy steps the fields as NumPy
does is made on a GPU machine with ``make gpu-parity`` and written down in
``gpu-parity.lock`` with a fingerprint of the engine's code and of the
scenarios it is proven on. A change to either without a new proof fails
here; a contributor without a GPU leaves it red and the maintainer reruns
the proof.

The comparison helpers of ``scripts/gpu_parity.py`` and its refusals need no
GPU, and are checked here on every runner.
"""

from __future__ import annotations

import json
import math
import pathlib
import re
import sys
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_ROOT / "scripts"))

import engine_scenarios as es
import gpu_parity

from phonometry.simulation import FDTD2D, Compute, fdtd
from phonometry.simulation import _backends as bk

if TYPE_CHECKING:
    from collections.abc import Callable

    from phonometry.simulation.compute import Device

_RERUN = "run `make gpu-parity` on a machine with an NVIDIA GPU and commit the lock"


def _lock() -> dict[str, Any]:
    """The committed lock, read when a test asks, so a missing one says what to do."""
    path = _ROOT / "gpu-parity.lock"
    if not path.is_file():
        pytest.fail(f"gpu-parity.lock is missing; {_RERUN}")
    lock: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return lock


def test_the_cupy_proof_was_made_on_this_engine() -> None:
    assert _lock()["engine_fingerprint"] == gpu_parity.engine_fingerprint(), (
        "the FDTD engine or its scenarios changed since the CuPy proof in "
        f"gpu-parity.lock; {_RERUN}"
    )


def test_the_lock_summary_agrees_with_its_keys() -> None:
    """The verdicts at the top of the lock are the ones its key table gives."""
    lock = _lock()
    results = {
        scenario: {key: gpu_parity.KeyResult(**entry) for key, entry in keys.items()}
        for scenario, keys in lock["keys"].items()
    }
    summary = gpu_parity.summarise(results)
    assert {name: lock[name] for name in summary} == summary


def test_the_lock_names_where_it_was_measured() -> None:
    lock = _lock()
    for name in (
        "gpu",
        "nvidia_driver",
        "cuda_driver_api",
        "cupy",
        "cupy_cuda_runtime",
        "nvrtc",
        "numpy",
        "python",
        "measured_on",
    ):
        assert isinstance(lock[name], str), name
        assert lock[name], name
    base = lock["base_image"]
    assert base is None or "@sha256:" in base


def test_the_fingerprint_covers_the_scenario_matrix() -> None:
    covered = {path.relative_to(_ROOT).as_posix() for path in gpu_parity._COVERED}
    assert covered == {
        "src/phonometry/simulation/fdtd.py",
        "src/phonometry/simulation/elastic_fdtd.py",
        "src/phonometry/simulation/_backends.py",
        "scripts/engine_scenarios.py",
    }


def test_each_measured_module_is_paired_with_its_covered_file() -> None:
    for found, covered in gpu_parity.imported_sources():
        assert pathlib.Path(found).name == covered.name


def test_an_engine_imported_from_elsewhere_stops_the_proof(
    tmp_path: pathlib.Path,
) -> None:
    """Another checkout's ``phonometry`` would be measured under this fingerprint."""
    covered = gpu_parity._COVERED[0]
    gpu_parity.require_covered([(str(covered), covered)])
    elsewhere = tmp_path / "src" / "phonometry" / "simulation" / "fdtd.py"
    with pytest.raises(gpu_parity.ParityError, match=re.escape(str(elsewhere))):
        gpu_parity.require_covered([(str(elsewhere), covered)])


def test_the_proof_refuses_a_foreign_engine_before_it_needs_cupy(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The check runs first, so a machine without a GPU sees the refusal too.

    ``None`` in ``sys.modules`` makes ``import cupy`` fail whether or not
    CuPy is installed, so reaching it would raise ``ImportError`` instead.
    """
    elsewhere = tmp_path / "fdtd.py"
    monkeypatch.setitem(sys.modules, "cupy", None)
    monkeypatch.setattr(
        gpu_parity,
        "imported_sources",
        lambda: ((str(elsewhere), gpu_parity._COVERED[0]),),
    )
    with pytest.raises(gpu_parity.ParityError, match=re.escape(str(elsewhere))):
        gpu_parity.measure()
    lock = tmp_path / "gpu-parity.lock"
    monkeypatch.setattr(gpu_parity, "_LOCK", lock)
    assert gpu_parity.main(["--write"]) == 1
    assert not lock.exists()
    assert "nothing written" in capsys.readouterr().err


_IMPEDANCE = next(s for s in es.SCENARIOS if s.name == "impedance")


def _numpy_recorded_as(device: Device) -> Callable[[Compute], bk.Backend]:
    """A loader that steps on NumPy and records *device*, as a fake backend would."""
    return lambda compute: bk._numpy(Compute(device=device, dtype=compute.dtype))


def test_the_reference_runs_on_numpy_whatever_the_environment_asks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``PHONOMETRY_COMPUTE=cupy`` would otherwise make the proof CuPy against CuPy."""
    monkeypatch.setitem(bk.LOADERS, "cupy", _numpy_recorded_as("cupy"))
    monkeypatch.setenv("PHONOMETRY_COMPUTE", "cupy")
    assert FDTD2D(343.0, 0.01, shape=(8, 8)).provenance.device == "cupy"
    got = gpu_parity.run_on(_IMPEDANCE, fdtd, gpu_parity.REFERENCE)
    monkeypatch.delenv("PHONOMETRY_COMPUTE")
    want = es.run(_IMPEDANCE, fdtd)
    assert got.keys() == want.keys()
    for key, value in want.items():
        assert np.array_equal(got[key], value), key


def test_a_run_that_stepped_elsewhere_stops_the_proof(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(bk.LOADERS, "cpu", _numpy_recorded_as("cupy"))
    with pytest.raises(
        gpu_parity.ParityError,
        match=re.escape("impedance: a run asked for cpu float64 stepped on cupy"),
    ):
        gpu_parity.run_on(_IMPEDANCE, fdtd, gpu_parity.REFERENCE)


def test_the_gpu_run_asks_for_cupy_in_float64() -> None:
    assert (gpu_parity.GPU.device, gpu_parity.GPU.dtype) == ("cupy", "float64")
    assert gpu_parity.GPU.fallback is False
    assert gpu_parity.REFERENCE == Compute()


def test_the_base_image_is_read_from_the_node_dockerfile() -> None:
    text = (_ROOT / "docker" / "node" / "Dockerfile").read_text(encoding="utf-8")
    base = gpu_parity.base_image_of(text)
    assert base is not None
    assert base.startswith("nvidia/cuda:")
    assert "@sha256:" in base
    assert gpu_parity.base_image_of("# no image here\n") is None


def test_a_docstring_does_not_move_the_fingerprint() -> None:
    src = 'def f(x):\n    """One."""\n    return x + 1\n'
    other = 'def f(x):\n    """Two, longer."""\n    return x + 1\n'
    assert gpu_parity.source_fingerprint(src) == gpu_parity.source_fingerprint(other)
    assert gpu_parity.source_fingerprint(src) != gpu_parity.source_fingerprint(
        src.replace("+ 1", "+ 2")
    )


def test_a_comment_or_a_line_ending_does_not_move_the_fingerprint() -> None:
    src = "def f(x):\n    return x + 1\n"
    commented = "def f(x):\n    # One more.\n    return x + 1  # here\n"
    assert gpu_parity.source_fingerprint(src) == gpu_parity.source_fingerprint(
        commented
    )
    assert gpu_parity.source_fingerprint(src) == gpu_parity.source_fingerprint(
        src.replace("\n", "\r\n")
    )


def test_a_string_statement_that_is_not_a_docstring_moves_the_fingerprint() -> None:
    src = 'def f(x):\n    y = x + 1\n    "a"\n    return y\n'
    assert gpu_parity.source_fingerprint(src) != gpu_parity.source_fingerprint(
        src.replace('"a"', '"b"')
    )


#: The fingerprint of :data:`_SNIPPET`, the same on every Python the CI
#: matrix runs. ``ast.dump`` stopped printing empty fields in Python 3.13,
#: which would give 3.12 a fingerprint of its own and fail this file there;
#: the fingerprint walks the tree itself so that it does not.
_SNIPPET_FINGERPRINT = (
    "92d0da6d1c391e3d91e7603b2beeb7183b1649ceb2c67a7cfbfa472562f6188c"
)
_SNIPPET = (
    "from . import a\n"
    "class C:\n"
    '    """Doc."""\n'
    "    def m(self, x: int = 2, *args, k=None, **kw) -> float:\n"
    "        return [y ** 2.5 for y in range(x) if y][0] if x else -1j\n"
)


def test_the_fingerprint_is_the_same_on_every_python() -> None:
    assert gpu_parity.source_fingerprint(_SNIPPET) == _SNIPPET_FINGERPRINT


@pytest.mark.parametrize(
    ("key", "kind"),
    [
        ("p", "field"),
        ("txy", "field"),
        ("frames", "field"),
        ("collocated_vy", "field"),
        ("energy", "reduction"),
        ("contour0_3000_p", "phasor"),
        ("contour1_1500.5_v", "phasor"),
    ],
)
def test_every_key_has_a_kind(key: str, kind: str) -> None:
    assert gpu_parity.kind_of(key) == kind


def test_a_key_the_proof_does_not_know_stops_it() -> None:
    with pytest.raises(gpu_parity.ParityError, match=re.escape("'p_mean'")):
        gpu_parity.kind_of("p_mean")


def test_a_comparison_records_bit_identity_and_both_differences() -> None:
    want = np.array([1.0, -2.0, 4.0])
    same = gpu_parity.compare("s/p", want.copy(), want)
    assert same == gpu_parity.KeyResult(
        kind="field", bit_identical=True, max_abs=0.0, max_relative=0.0
    )
    moved = gpu_parity.compare("s/p", want + np.array([0.0, 1e-3, 0.0]), want)
    assert not moved.bit_identical
    assert moved.max_abs == pytest.approx(1e-3)
    assert moved.max_relative == pytest.approx(1e-3 / 4.0)


def test_a_zero_of_the_other_sign_is_not_bit_identical() -> None:
    """``array_equal`` calls -0.0 and +0.0 equal; their bits are not."""
    result = gpu_parity.compare("s/p", np.array([-0.0, 1.0]), np.array([0.0, 1.0]))
    assert not result.bit_identical
    assert result.max_abs == 0.0


def test_complex_phasors_compare_by_modulus() -> None:
    want = np.array([3.0 + 4.0j, 1.0 + 0.0j])
    got = want + np.array([0.0, 3e-6 + 4e-6j])
    result = gpu_parity.compare("s/contour0_3000_p", got, want)
    assert result.kind == "phasor"
    assert result.max_abs == pytest.approx(5e-6)
    assert result.max_relative == pytest.approx(1e-6)


@pytest.mark.parametrize("bad", [math.nan, math.inf])
def test_a_value_that_is_not_finite_stops_the_proof(bad: float) -> None:
    want = np.array([1.0, 2.0])
    with pytest.raises(gpu_parity.ParityError, match=re.escape("s/vx: the CuPy run")):
        gpu_parity.compare("s/vx", np.array([1.0, bad]), want)
    with pytest.raises(gpu_parity.ParityError, match=re.escape("s/vx: the NumPy run")):
        gpu_parity.compare("s/vx", want, np.array([bad, 2.0]))


def test_an_empty_run_stops_the_proof() -> None:
    with pytest.raises(
        gpu_parity.ParityError, match=re.escape("s/p: the NumPy run holds nothing")
    ):
        gpu_parity.compare("s/p", np.array([]), np.array([]))


def test_an_all_zero_reference_stops_the_proof() -> None:
    with pytest.raises(
        gpu_parity.ParityError, match=re.escape("s/p: the NumPy reference is all zero")
    ):
        gpu_parity.compare("s/p", np.zeros(3), np.zeros(3))


def test_a_shape_or_dtype_of_its_own_stops_the_proof() -> None:
    want = np.ones(3)
    with pytest.raises(gpu_parity.ParityError, match=re.escape("s/p: CuPy gave")):
        gpu_parity.compare("s/p", np.ones(3, dtype=np.float32), want)
    with pytest.raises(gpu_parity.ParityError, match=re.escape("s/p: CuPy gave")):
        gpu_parity.compare("s/p", np.ones(4), want)


def test_a_run_with_keys_of_its_own_stops_the_proof() -> None:
    want = {"p": np.ones(2), "energy": np.array(1.0)}
    got = {"p": np.ones(2)}
    with pytest.raises(gpu_parity.ParityError, match=re.escape("s: the CuPy run")):
        gpu_parity.compare_scenario("s", got, want)
