#  Copyright (c) 2026. Jose Manuel Requena Plens
"""On NumPy, the engines give today's numbers, bit for bit, on every runner.

The engines learned to run on other array backends. The frozen copies under
``frozen/`` are the engines as they stood before; every scenario of
``scripts/engine_scenarios.py`` steps both in the same process and compares
every stored field, the recorded frames, the energy, the collocated fields
and the contour phasors with ``array_equal``. Comparing in one process, not
against digests, is what lets it run on every operating system and CPU the
matrix covers: libm and SIMD dispatch differ between machines, never between
two engines in one process. The elastic energy's fluid branch, which no
scenario reaches with pressure on a fluid cell, gets its own seeded check.
"""

from __future__ import annotations

import pathlib
import sys

import numpy as np
import pytest

_HERE = pathlib.Path(__file__).resolve().parent
_SCRIPTS = _HERE.parent.parent / "scripts"
for path in (str(_HERE), str(_SCRIPTS)):
    if path not in sys.path:
        sys.path.insert(0, path)

import engine_scenarios as es
from frozen import elastic_frozen, fdtd_frozen

from phonometry.simulation import elastic_fdtd, fdtd


@pytest.mark.parametrize("scenario", es.SCENARIOS, ids=lambda s: s.name)
def test_the_numpy_engine_matches_its_frozen_copy_bit_for_bit(
    scenario: es.Scenario,
) -> None:
    live, frozen = (
        (fdtd, fdtd_frozen)
        if scenario.kind == "acoustic"
        else (elastic_fdtd, elastic_frozen)
    )
    got = es.run(scenario, live)
    want = es.run(scenario, frozen)
    assert got.keys() == want.keys()
    for key in want:
        assert got[key].dtype == want[key].dtype, key
        assert np.array_equal(got[key], want[key]), f"{scenario.name}: {key} moved"


#: A solid at the bound c_p**2 = 2 c_s**2, just under it so that lambda is
#: clamped to exactly zero (the constructor admits a relative 1e-9 below).
_LAMBDA_ZERO_C_P = 2828.427124
_LAMBDA_ZERO_C_S = 2000.0


@pytest.mark.parametrize("seed", range(5))
def test_the_fluid_energy_matches_the_frozen_copy_bit_for_bit(seed: int) -> None:
    """The fluid branch of ``energy`` gives the frozen copy's number.

    No scenario weighs ``p**2 / (2 lam)`` enough to see a rounding in it, so
    the two engines take an all-fluid grid with a small ``lam = 0`` solid
    patch and the same random normal stresses, and their energies are equal.
    """
    ny, nx = 24, 30
    c_p = np.full((ny, nx), 1480.0)
    c_s = np.zeros((ny, nx))
    rho = np.full((ny, nx), 1000.0)
    c_p[9:15, 12:18] = _LAMBDA_ZERO_C_P
    c_s[9:15, 12:18] = _LAMBDA_ZERO_C_S
    rho[9:15, 12:18] = 2500.0
    live = elastic_fdtd.ElasticFDTD2D(c_p, c_s, 0.01, rho=rho)
    frozen = elastic_frozen.ElasticFDTD2D(c_p, c_s, 0.01, rho=rho)
    assert np.any((live.lam == 0.0) & (live.mu > 0.0))
    rng = np.random.default_rng(seed)
    txx = 1e3 * rng.standard_normal((ny, nx))
    tyy = 1e3 * rng.standard_normal((ny, nx))
    for sim in (live, frozen):
        sim.txx[...] = txx
        sim.tyy[...] = tyy
    got, want = live.energy(), frozen.energy()
    assert type(got) is float
    assert type(want) is float
    assert got == want
