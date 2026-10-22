#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Where a simulation runs: the request, its defaults and its refusals."""

from __future__ import annotations

import contextlib
import os
import pickle
import subprocess
import sys
import threading
from pathlib import Path

import numpy as np
import pytest

from phonometry.simulation import (
    Compute,
    ComputeDeviceError,
    ComputeImportError,
    ComputeRemoteError,
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
    "package_digest": None,
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
        (
            {"device": "torch:mps", "dtype": "float64"},
            ValueError,
            "'torch:mps' needs dtype='float32'",
        ),
        ({"device": "cpu", "device_index": 1}, ValueError, "'cpu' has no device index"),
        (
            {"device": "torch:cpu", "device_index": 2},
            ValueError,
            "'torch:cpu' has no device index",
        ),
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


# A request that names a node. Building one reaches nothing, as with a GPU.


def test_a_request_names_a_host_without_reaching_it() -> None:
    request = Compute(device="cupy", host="nas", timeout_s=600)
    assert (request.host, request.timeout_s) == ("nas", 600.0)
    assert Compute().host is None


def test_a_numpy_run_may_fall_back_from_a_node() -> None:
    # On this machine "cpu" is the fallback already; on a node it is not.
    assert Compute(host="nas", fallback=True).fallback is True


@pytest.mark.parametrize(
    ("kwargs", "error", "match"),
    [
        ({"host": ""}, ValueError, "'host' must be a name from the hosts file"),
        (
            {"host": "root@192.168.0.40"},
            ValueError,
            "'host' must be a name from the hosts file",
        ),
        (
            {"host": "-oProxyCommand=x"},
            ValueError,
            "'host' must be a name from the hosts file",
        ),
        ({"host": "a" * 65}, ValueError, "'host' must be a name from the hosts file"),
        ({"host": 7}, TypeError, "'host' must be a name from the hosts file or None"),
        ({"timeout_s": 60.0}, ValueError, "'timeout_s' bounds a remote run"),
        ({"host": "nas", "timeout_s": 0.0}, ValueError, "'timeout_s' must be positive"),
        (
            {"host": "nas", "timeout_s": "60"},
            TypeError,
            "'timeout_s' must be one number",
        ),
        (
            {"host": "nas", "timeout_s": True},
            TypeError,
            "'timeout_s' must be one number",
        ),
    ],
)
def test_a_host_or_a_timeout_that_cannot_mean_anything_is_refused(
    kwargs: dict[str, object], error: type[Exception], match: str
) -> None:
    with pytest.raises(error, match=match):
        Compute(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize("timeout_s", [threading.TIMEOUT_MAX * 2, 1e300])
def test_a_timeout_longer_than_a_timer_waits_is_refused_with_the_limit(
    timeout_s: float,
) -> None:
    # The timer that stops a remote run would die on it, and the run would
    # have no timeout at all.
    limit = int(threading.TIMEOUT_MAX)
    with pytest.raises(ValueError, match=rf"'timeout_s' must be at most {limit} s"):
        Compute(host="nas", timeout_s=timeout_s)


def test_the_longest_timeout_a_timer_waits_is_taken() -> None:
    longest = Compute(host="nas", timeout_s=threading.TIMEOUT_MAX)
    assert longest.timeout_s == threading.TIMEOUT_MAX


@pytest.mark.parametrize(
    ("text", "want"),
    [
        ("cupy@nas", Compute(device="cupy", host="nas")),
        (
            "cupy:1@nas,float32,fallback",
            Compute(
                device="cupy",
                device_index=1,
                dtype="float32",
                fallback=True,
                host="nas",
            ),
        ),
        ("cpu@node-2.lab", Compute(host="node-2.lab")),
        (
            " torch:cuda@nas , float32 ",
            Compute(device="torch:cuda", dtype="float32", host="nas"),
        ),
    ],
)
def test_the_environment_names_a_host_after_an_at(text: str, want: Compute) -> None:
    assert cm._parse_environment(text) == want


@pytest.mark.parametrize("text", ["cupy@", "cupy@bad host", "@nas", "cupy@nas@lab"])
def test_a_malformed_host_in_the_environment_names_the_variable(text: str) -> None:
    with pytest.raises(ValueError, match="PHONOMETRY_COMPUTE"):
        cm._parse_environment(text)


@pytest.mark.parametrize(
    ("text", "want"),
    [
        ("cupy:1@nas,float32", "cupy:1,float32"),
        ("cupy@nas", "cupy"),
        ("cupy", "cupy"),
        (" cpu@nas ", "cpu"),
    ],
)
def test_a_node_takes_the_host_out_of_its_environment(text: str, want: str) -> None:
    assert cm._strip_host(text) == want


@pytest.mark.parametrize(
    ("source", "match"),
    [
        ("argument", "compute= names host 'nas'"),
        ("use", "the use\\(\\) block names host 'nas'"),
        ("environment", "PHONOMETRY_COMPUTE names host 'nas'"),
    ],
)
def test_an_engine_built_here_refuses_a_host_and_says_where_it_came_from(
    source: str, match: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(cm._ENV_VAR, raising=False)
    request = Compute(device="cupy", host="nas")
    if source == "environment":
        monkeypatch.setenv(cm._ENV_VAR, "cupy@nas")
    argument = request if source == "argument" else None
    with (
        use(request) if source == "use" else contextlib.nullcontext(),
        pytest.raises(ValueError, match=match),
    ):
        cm._local_request(argument, owner="FDTD2D")


def test_the_refusal_tells_the_caller_how_to_step_here_or_run_there(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(cm._ENV_VAR, "cupy@nas")
    with pytest.raises(
        ValueError,
        match="pass compute=Compute\\(device='cupy'\\) to step here, or call fdtd_simulation",
    ):
        cm._local_request(None, owner="FDTD2D")


def test_a_request_without_a_host_passes_an_engine(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(cm._ENV_VAR, "cupy:1")
    assert cm._local_request(None, owner="FDTD2D") == Compute(
        device="cupy", device_index=1
    )


def test_the_placement_says_where_it_came_from(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(cm._ENV_VAR, raising=False)  # whatever the shell had
    assert cm._requested_from(None) == (Compute(), "default")
    monkeypatch.setenv(cm._ENV_VAR, "cupy")
    assert cm._requested_from(None)[1] == "environment"
    with use(Compute(device="torch:cpu")):
        assert cm._requested_from(None)[1] == "use"
    assert cm._requested_from(Compute())[1] == "argument"


def test_a_remote_error_refines_runtime_error_and_survives_a_process_boundary() -> None:
    error = ComputeRemoteError(
        "node 'nas' failed", host="nas", node_traceback="Traceback ...\nValueError: x"
    )
    assert isinstance(error, RuntimeError)
    back = pickle.loads(pickle.dumps(error))
    assert (str(back), back.host, back.node_traceback) == (
        str(error),
        "nas",
        error.node_traceback,
    )
    assert any("ValueError: x" in note for note in back.__notes__)


def test_a_provenance_names_the_package_that_ran() -> None:
    digest = "0123456789abcdef" * 4
    record = RunProvenance(**{**_RUN, "host": "nas", "package_digest": digest})  # type: ignore[arg-type]
    assert record.package_digest == digest


@pytest.mark.parametrize(
    ("value", "error"),
    [("abc", ValueError), ("0123456789ABCDEF" * 4, ValueError), (7, TypeError)],
)
def test_a_package_digest_is_sixty_four_lowercase_hex_digits(
    value: object, error: type[Exception]
) -> None:
    fields = {**_RUN, "package_digest": value}
    with pytest.raises(error, match="'package_digest'"):
        RunProvenance(**fields)  # type: ignore[arg-type]
