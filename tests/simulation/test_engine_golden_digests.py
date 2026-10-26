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

import copy
import json
import pathlib
import platform
import sys
import types
from typing import Any

import numpy as np
import pytest

_SCRIPTS = pathlib.Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import engine_digests as ed
import engine_scenarios as es


def _recorded_here() -> dict[str, Any]:
    """The recorded digests, when this is the environment they were measured in."""
    want = ed.recorded()
    here = ed.environment()
    if want["environment"] != here:
        msg = f"golden digests measured on {want['environment']}; this is {here}"
        if ed.environment_required():
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


def test_a_moved_appeared_or_vanished_seed_is_named() -> None:
    want = {"scenarios": {}, "fluid_energy": {"0": "x", "1": "y", "3": "w"}}
    got = {"scenarios": {}, "fluid_energy": {"0": "x", "1": "z", "2": "v"}}
    assert ed.differences(want, got) == [
        "fluid_energy: seed 1",
        "fluid_energy: seed 2",
        "fluid_energy: seed 3",
    ]


@pytest.mark.parametrize(
    ("value", "required"),
    [("require", True), ("1", False), ("", False), (None, False)],
)
def test_only_require_makes_a_different_environment_fail(
    monkeypatch: pytest.MonkeyPatch, value: str | None, *, required: bool
) -> None:
    if value is None:
        monkeypatch.delenv(ed.REQUIRE_ENV, raising=False)
    else:
        monkeypatch.setenv(ed.REQUIRE_ENV, value)
    assert ed.environment_required() is required


def _numpy_targets(
    monkeypatch: pytest.MonkeyPatch, dispatch: list[str], features: dict[str, bool]
) -> None:
    """NumPy's dispatch targets and this machine's features, as *avx512_features* reads them."""
    module = types.SimpleNamespace(__cpu_dispatch__=dispatch, __cpu_features__=features)
    monkeypatch.setattr(
        ed, "importlib", types.SimpleNamespace(import_module=lambda _name: module)
    )


@pytest.mark.parametrize(
    ("dispatch", "features", "named"),
    [
        # NumPy 2.4 and later: the level, and the AVX-512 targets above it.
        (
            ["X86_V3", "X86_V4", "AVX512_ICL", "AVX512_SPR"],
            {"X86_V3": True, "X86_V4": True, "AVX512_ICL": True},
            ["AVX512_ICL", "X86_V4"],
        ),
        # Before 2.4: the AVX-512 features one by one.
        (
            ["AVX2", "AVX512F", "AVX512_SKX", "AVX512_ICL"],
            {"AVX2": True, "AVX512F": True, "AVX512_SKX": True},
            ["AVX512F", "AVX512_SKX"],
        ),
        # A machine without AVX-512.
        (["X86_V3", "X86_V4"], {"X86_V3": True}, []),
    ],
    ids=["levels", "features", "no-avx512"],
)
def test_the_avx512_targets_this_machine_has_are_named(
    monkeypatch: pytest.MonkeyPatch,
    dispatch: list[str],
    features: dict[str, bool],
    named: list[str],
) -> None:
    _numpy_targets(monkeypatch, dispatch, features)
    assert ed.avx512_features() == named


def test_a_feature_numpy_does_not_dispatch_to_is_never_named(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``NPY_DISABLE_CPU_FEATURES`` switches off dispatch targets, nothing else.

    A build with no AVX-512 kernel has nothing of the kind to switch off,
    whatever the CPU has.
    """
    _numpy_targets(
        monkeypatch, ["X86_V3"], {"X86_V3": True, "AVX512F": True, "AVX512_SKX": True}
    )
    assert ed.avx512_features() == []


# The script's modes, on a measurement that is never taken.

_MEASURED: dict[str, Any] = {
    "environment": {"system": "Linux", "numpy": "2.5.4", "numpy_avx512": "off"},
    "measured_on": {"cpu": "a CPU"},
    "scenarios": {"sponge": {"p": "aa", "vx": "bb"}},
    "fluid_energy": {"0": "0x1.0000000000000p+0"},
}


def _as_written(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=1, sort_keys=True) + "\n"


@pytest.fixture
def digests_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> pathlib.Path:
    """Where the script reads and writes its file; *measure* returns ``_MEASURED``."""
    path = tmp_path / "engine-digests.json"
    monkeypatch.setattr(ed, "DIGESTS_FILE", path)
    monkeypatch.setattr(ed, "measure", lambda: copy.deepcopy(_MEASURED))
    monkeypatch.delenv(ed.REQUIRE_ENV, raising=False)
    return path


def _recorded_as(path: pathlib.Path, **changes: dict[str, Any]) -> None:
    path.write_text(_as_written({**_MEASURED, **changes}), encoding="utf-8")


def test_write_records_the_measurement_and_compares_nothing(
    digests_file: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert ed.main(["--write"]) == 0
    assert digests_file.read_text(encoding="utf-8") == _as_written(_MEASURED)
    assert capsys.readouterr().err == ""


def test_output_keeps_the_measurement_beside_the_recorded_file(
    digests_file: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    _recorded_as(digests_file)
    before = digests_file.read_text(encoding="utf-8")
    kept = tmp_path / "measured.json"
    assert ed.main(["--output", str(kept)]) == 0
    assert kept.read_text(encoding="utf-8") == _as_written(_MEASURED)
    assert digests_file.read_text(encoding="utf-8") == before


def test_output_keeps_a_measurement_whose_digest_moved(
    digests_file: pathlib.Path,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The file a CI artifact carries is written before the comparison fails."""
    _recorded_as(digests_file, scenarios={"sponge": {"p": "aa", "vx": "cc"}})
    kept = tmp_path / "measured.json"
    assert ed.main(["--output", str(kept)]) == 1
    assert kept.read_text(encoding="utf-8") == _as_written(_MEASURED)
    assert capsys.readouterr().err == "moved: sponge: vx\n"


def test_a_different_environment_is_a_note_where_it_is_not_required(
    digests_file: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _recorded_as(
        digests_file, environment={**_MEASURED["environment"], "numpy": "2.4.0"}
    )
    assert ed.main([]) == 0
    err = capsys.readouterr().err
    assert err.startswith("note: environment: recorded ")
    assert err.count("\n") == 1


def test_a_different_environment_fails_where_it_is_required(
    digests_file: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _recorded_as(
        digests_file, environment={**_MEASURED["environment"], "numpy": "2.4.0"}
    )
    monkeypatch.setenv(ed.REQUIRE_ENV, "require")
    assert ed.main([]) == 1
    err = capsys.readouterr().err
    assert err.startswith("environment: recorded ")
    assert "note:" not in err


def test_a_moved_digest_fails_beside_the_note_on_the_environment(
    digests_file: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _recorded_as(
        digests_file,
        environment={**_MEASURED["environment"], "numpy": "2.4.0"},
        fluid_energy={"0": "0x1.0000000000001p+0"},
    )
    assert ed.main([]) == 1
    note, moved = capsys.readouterr().err.splitlines()
    assert note.startswith("note: environment: recorded ")
    assert moved == "moved: fluid_energy: seed 0"


def test_avx512_features_names_them_without_measuring(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def measure() -> dict[str, Any]:
        msg = "nothing is measured for --avx512-features"
        raise AssertionError(msg)

    monkeypatch.setattr(ed, "measure", measure)
    monkeypatch.setattr(ed, "avx512_features", lambda: ["AVX512_ICL", "X86_V4"])
    assert ed.main(["--avx512-features"]) == 0
    assert capsys.readouterr().out == "AVX512_ICL X86_V4\n"
