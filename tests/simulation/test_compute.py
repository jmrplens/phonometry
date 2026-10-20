#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Where a simulation runs: the request, its defaults and its refusals."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from phonometry.simulation import (
    Compute,
    ComputeDeviceError,
    ComputeImportError,
    RunProvenance,
    use,
)
from phonometry.simulation import compute as cm

#: The ``src`` this test module belongs to, so the subprocess imports the
#: code under test and not whatever an editable install points at.
_SRC = Path(__file__).resolve().parents[2] / "src"
#: What a ``use`` block raises in the tests of what it restores on the way out.
_INSIDE = "raised inside the block"


def test_the_default_request_is_numpy_in_float64() -> None:
    c = Compute()
    assert (c.device, c.device_index, c.dtype, c.fallback) == (
        "cpu",
        0,
        "float64",
        False,
    )


def test_a_record_naming_a_gpu_is_built_without_touching_one() -> None:
    assert Compute(device="cupy", device_index=3).device_index == 3


def test_a_whole_float_index_is_held_as_an_int() -> None:
    index = Compute(device="cupy", device_index=2.0).device_index
    assert (index, type(index)) == (2, int)


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"device": "gpu"}, "'device' must be one of"),
        ({"dtype": "float16"}, "'dtype' must be one of"),
        ({"device": "torch:mps"}, "MPS has no float64"),
        ({"device": "cpu", "device_index": 1}, "has no device index"),
        ({"device": "torch:cpu", "device_index": 1}, "has no device index"),
        ({"device": "cpu", "fallback": True}, "already the fallback"),
        ({"device": "cupy", "device_index": -1}, "device_index"),
    ],
)
def test_a_request_that_cannot_mean_anything_is_refused(
    kwargs: dict, match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        Compute(**kwargs)


def test_a_device_that_is_not_text_is_the_wrong_type() -> None:
    with pytest.raises(TypeError, match="'device' must be one of"):
        Compute(device=3)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"device": "cupy", "fallback": "no"},
        {"fallback": 1},
        {"device": "torch:cuda", "fallback": None},
    ],
)
def test_a_fallback_that_is_not_a_bool_is_the_wrong_type(kwargs: dict) -> None:
    with pytest.raises(TypeError, match="'fallback' must be True or False"):
        Compute(**kwargs)


def test_a_numpy_bool_fallback_is_held_as_a_bool() -> None:
    fallback = Compute(device="cupy", fallback=np.True_).fallback  # type: ignore[arg-type]
    assert (fallback, type(fallback)) == (True, bool)


def test_an_index_that_is_not_a_number_is_the_wrong_type() -> None:
    with pytest.raises(TypeError, match="'device_index' must be a whole number"):
        Compute(device="cupy", device_index=True)


def test_the_argument_wins_over_use_and_use_over_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(cm._ENV_VAR, "cupy:2")
    assert cm._requested(None) == Compute(device="cupy", device_index=2)
    with use(Compute(device="torch:cpu")):
        assert cm._requested(None).device == "torch:cpu"
        assert cm._requested(Compute()).device == "cpu"
    assert cm._requested(None).device == "cupy"


def test_nothing_set_means_numpy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(cm._ENV_VAR, raising=False)
    assert cm._requested(None) == Compute()


@pytest.mark.parametrize(
    ("text", "want"),
    [
        ("cpu", Compute()),
        ("cupy", Compute(device="cupy")),
        ("cupy:1", Compute(device="cupy", device_index=1)),
        (
            "torch:cuda:1,fallback",
            Compute(device="torch:cuda", device_index=1, fallback=True),
        ),
        ("torch:mps,float32", Compute(device="torch:mps", dtype="float32")),
        (" cupy , float32 ", Compute(device="cupy", dtype="float32")),
    ],
)
def test_the_environment_grammar(text: str, want: Compute) -> None:
    assert cm._parse_environment(text) == want


@pytest.mark.parametrize(
    "text",
    [
        "gpu",
        "cupy:x",
        "cupy,fast",
        "torch:mps",
        "cupy:1:2",
        "cupy:\u00b2",
        "cupy,float32,float64",
        "cupy,float32,float32",
        "cupy,fallback,fallback",
    ],
)
def test_a_malformed_environment_value_names_the_variable(text: str) -> None:
    with pytest.raises(ValueError, match="PHONOMETRY_COMPUTE"):
        cm._parse_environment(text)


@pytest.mark.parametrize(
    ("text", "match"),
    [
        ("cupy,float32,float64", "one dtype, 'float32' or 'float64', not both"),
        ("torch:mps,float64,float32", "one dtype, 'float64' or 'float32', not both"),
        ("cupy,float32,float32", "the option 'float32' is given twice"),
        ("cupy,fallback,fallback", "the option 'fallback' is given twice"),
    ],
)
def test_an_environment_value_that_contradicts_itself_is_refused(
    text: str, match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        cm._parse_environment(text)


def test_a_bad_environment_value_does_not_break_the_import() -> None:
    done = subprocess.run(
        [sys.executable, "-c", "import phonometry.simulation"],
        env={**os.environ, "PHONOMETRY_COMPUTE": "gpu", "PYTHONPATH": str(_SRC)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, done.stderr


def test_use_does_not_leak_out_of_its_block(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(cm._ENV_VAR, raising=False)
    with use(Compute(device="cupy")):
        pass
    assert cm._AMBIENT.get() is None
    assert cm._requested(None) == Compute()


def test_use_restores_the_outer_placement_when_nested(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(cm._ENV_VAR, raising=False)
    outer = Compute(device="cupy")
    inner = Compute(device="torch:cpu")
    with use(outer):
        with use(inner):
            assert cm._requested(None) is inner
        assert cm._requested(None) is outer
    assert cm._AMBIENT.get() is None


def test_use_restores_the_outer_placement_when_its_block_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(cm._ENV_VAR, raising=False)
    outer = Compute(device="cupy")
    with use(outer):
        with pytest.raises(RuntimeError, match=_INSIDE), use(Compute()):
            raise RuntimeError(_INSIDE)
        assert cm._requested(None) is outer
    with pytest.raises(RuntimeError, match=_INSIDE), use(outer):
        raise RuntimeError(_INSIDE)
    assert cm._AMBIENT.get() is None


def test_use_takes_only_a_compute_record() -> None:
    with pytest.raises(TypeError, match="Compute"), use("cupy"):  # type: ignore[arg-type]
        pass


def test_the_errors_refine_the_builtin_they_name() -> None:
    assert issubclass(ComputeImportError, ImportError)
    assert issubclass(ComputeDeviceError, RuntimeError)


#: A record a CuPy run could have written.
_RUN: dict[str, object] = {
    "host": None,
    "device": "cupy",
    "device_index": 0,
    "dtype": "float64",
    "numpy_version": "2.5.3",
    "array_library": "cupy 14.2.0",
    "cuda_runtime": "13.2",
    "cuda_driver_api": "13.3",
    "gpu": "NVIDIA GeForce RTX 4060",
}


def test_a_run_provenance_holds_what_a_run_wrote() -> None:
    record = RunProvenance(**{**_RUN, "device_index": np.int64(1)})  # type: ignore[arg-type]
    assert (record.device_index, type(record.device_index)) == (1, int)
    assert record.gpu == "NVIDIA GeForce RTX 4060"


@pytest.mark.parametrize(
    ("changes", "error", "match"),
    [
        ({"device": "gpu"}, ValueError, "'device' must be one of"),
        ({"device": 1}, TypeError, "'device' must be one of"),
        ({"dtype": "float16"}, ValueError, "'dtype' must be one of"),
        ({"dtype": None}, TypeError, "'dtype' must be one of"),
        ({"device_index": -1}, ValueError, "'device_index' must be a whole number"),
        ({"device_index": 1.5}, ValueError, "'device_index' must be a whole number"),
        ({"device_index": True}, TypeError, "'device_index' must be a whole number"),
        ({"device_index": "0"}, TypeError, "'device_index' must be a whole number"),
        ({"numpy_version": None}, TypeError, "'numpy_version' must be a text"),
        ({"host": b"node"}, TypeError, "'host' must be a text or None"),
        ({"array_library": 14.2}, TypeError, "'array_library' must be a text or None"),
        ({"cuda_runtime": 13.2}, TypeError, "'cuda_runtime' must be a text or None"),
        ({"cuda_driver_api": 13030}, TypeError, "'cuda_driver_api' must be a text"),
        ({"gpu": 4060}, TypeError, "'gpu' must be a text or None"),
    ],
)
def test_a_run_provenance_no_run_could_write_is_refused(
    changes: dict[str, object], error: type[Exception], match: str
) -> None:
    fields = {**_RUN, **changes}
    with pytest.raises(error, match=match):
        RunProvenance(**fields)  # type: ignore[arg-type]
