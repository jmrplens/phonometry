#  Copyright (c) 2026. Jose Manuel Requena Plens
"""On NumPy, the engines give the numbers recorded in engine-digests.json.

The digests were taken from the engines as they stood before they could step
on any other backend, after a frozen copy of those engines had proven the
refactor bit for bit on every runner. The copy is gone; the digests stay.
Their bits depend on the C library's libm and on NumPy's SIMD dispatch, so
they are compared where they were measured, the environment the file
records: the ``engine-digests`` CI job, which also wrote the file. Elsewhere
the comparison skips and says why; that job sets
``PHONOMETRY_ENGINE_DIGESTS=require``, under which a mismatched environment
fails instead. The engines are always stepped on NumPy here, whatever
``use()`` or ``PHONOMETRY_COMPUTE`` ask for.
"""

from __future__ import annotations

import os
import pathlib
import platform
import sys
from typing import Any

import numpy as np
import pytest

_SCRIPTS = pathlib.Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import engine_digests as ed
import engine_scenarios as es

_REQUIRE = os.environ.get(ed.REQUIRE_ENV) == "require"


def _recorded_here() -> dict[str, Any]:
    """The recorded digests, when this is the environment they were measured in."""
    want = ed.recorded()
    here = ed.environment()
    if want["environment"] != here:
        msg = f"golden digests measured on {want['environment']}; this is {here}"
        if _REQUIRE:
            pytest.fail(msg)
        pytest.skip(msg)
    return want


@pytest.mark.parametrize("scenario", es.SCENARIOS, ids=lambda s: s.name)
def test_each_scenario_gives_its_recorded_numbers(scenario: es.Scenario) -> None:
    want = _recorded_here()["scenarios"][scenario.name]
    got = ed.numpy_run(scenario)
    assert sorted(got) == sorted(want)
    for key, array in got.items():
        assert ed.array_digest(array) == want[key], f"{scenario.name}: {key} moved"


def test_the_digests_are_taken_on_numpy_whatever_the_environment_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A shell set up for the clips names a GPU; the digests stay NumPy's.

    Unpinned, the engine would follow the variable and fail to find GPU 7
    (or step there), and the numbers recorded as NumPy's would not be.
    """
    scenario = es.SCENARIOS[0]
    monkeypatch.delenv("PHONOMETRY_COMPUTE", raising=False)
    here = {key: ed.array_digest(a) for key, a in ed.numpy_run(scenario).items()}
    monkeypatch.setenv("PHONOMETRY_COMPUTE", "cupy:7")
    there = {key: ed.array_digest(a) for key, a in ed.numpy_run(scenario).items()}
    assert there == here


def test_the_environment_names_the_c_library() -> None:
    """libm is the C library's, so two runners that differ there can differ in the bits."""
    name, version = platform.libc_ver()
    if not version:
        pytest.skip("this platform does not name its C library")
    assert ed.environment()["libc"] == f"{name} {version}"


@pytest.mark.parametrize("seed", ed.FLUID_SEEDS)
def test_the_fluid_energy_gives_its_recorded_number(seed: int) -> None:
    """The fluid branch of ``energy``, which no scenario weighs, exactly."""
    want = _recorded_here()["fluid_energy"][str(seed)]
    assert float.hex(ed.fluid_energy(seed)) == want


def test_the_fluid_energy_grid_holds_a_solid_with_lambda_zero() -> None:
    sim = ed.fluid_grid()
    assert np.any((sim.lam == 0.0) & (sim.mu > 0.0))


def test_every_scenario_and_seed_is_recorded() -> None:
    want = ed.recorded()
    assert sorted(want["scenarios"]) == sorted(s.name for s in es.SCENARIOS)
    assert sorted(want["fluid_energy"]) == sorted(str(s) for s in ed.FLUID_SEEDS)


def test_a_digest_sees_the_dtype_and_the_shape() -> None:
    flat = ed.array_digest(np.zeros(4))
    assert flat != ed.array_digest(np.zeros((2, 2)))
    assert flat != ed.array_digest(np.zeros(4, dtype=np.float32))
    assert flat == ed.array_digest(np.zeros(8)[::2])


def test_a_moved_appeared_or_vanished_digest_is_named() -> None:
    want = {"scenarios": {"a": {"p": "1", "vx": "2"}}, "fluid_energy": {"0": "x"}}
    got = {"scenarios": {"a": {"p": "9", "vy": "3"}}, "fluid_energy": {"0": "x"}}
    assert ed.differences(want, got) == ["a: p", "a: vx", "a: vy"]
