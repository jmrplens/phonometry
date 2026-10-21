#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A node runs the job it is sent and answers with what the client cannot rebuild."""

from __future__ import annotations

import dataclasses
import io
import os
import subprocess
import sys
import threading
import time
import warnings
from types import MappingProxyType, SimpleNamespace
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest

from phonometry.simulation import (
    ComputeFallbackWarning,
    ElasticRecording,
    ElasticRun,
    ExplosionSource,
    FDTDRecording,
    FDTDRun,
    GaussianPulse,
    RunProvenance,
    _observer,
    elastic_fdtd_simulation,
    fdtd_simulation,
)
from phonometry.simulation._remote import bootstrap, node, wire
from phonometry.simulation._remote.package import (
    FLOORS,
    PYTHON_FLOOR,
    installed_package,
)

if TYPE_CHECKING:
    from pathlib import Path

_CPU = {"device": "cpu", "device_index": 0, "dtype": "float64"}
_PROBES = [(30, 15), (5, 5)]
_ACOUSTIC = FDTDRun(
    343.0,
    0.01,
    2e-3,
    shape=(30, 40),
    sources=[GaussianPulse(ix=10, iy=15, half_width_s=4e-5)],
    recording=FDTDRecording(probes=_PROBES, snapshot_every=20, snapshot_decimation=2),
    boundaries="absorbing",
    absorbing_layer_cells=5,
)
#: What a job returns beside its record when it has bytes of its own to send.
_VIDEO = b"\x1aE\xdf\xa3 a video"


def _job(
    function: str, arguments: dict[str, Any], compute: dict[str, object] = _CPU
) -> bytes:
    tree, buffers = wire.encode_arguments(arguments)
    out = io.BytesIO()
    header = {
        "type": "job",
        "function": function,
        "compute": compute,
        "arguments": tree,
    }
    bootstrap.write_frame(out, header, buffers)
    return out.getvalue()


def _frames(data: bytes) -> list[tuple[dict[str, object], list[bytes]]]:
    stream = io.BytesIO(data)
    frames = []
    while stream.tell() < len(data):
        header = bootstrap.read_header(stream)
        buffers = [
            bootstrap.read_exact(stream, n)
            for n in bootstrap.field(header, "buffers", list)
        ]
        frames.append((header, buffers))
    return frames


def _serve(
    job: bytes, *, end_input_after_s: float | None = None
) -> tuple[int, list[tuple[dict[str, object], list[bytes]]]]:
    """Serve *job* in this process, the input open as a client keeps it.

    The input stays open until the node answers, as a client's does, or ends
    after *end_input_after_s* seconds, as when a client goes away.
    """
    read_end, write_end = os.pipe()
    out = io.BytesIO()
    with os.fdopen(read_end, "rb") as stream, os.fdopen(write_end, "wb") as feed:

        def client() -> None:
            feed.write(job)
            feed.flush()
            if end_input_after_s is not None:
                time.sleep(end_input_after_s)
                feed.close()

        sender = threading.Thread(target=client)
        sender.start()
        code = node.serve(stream, out)
        sender.join()
    return code, _frames(out.getvalue())


def _array(descriptor: dict[str, object], buffer: bytes) -> np.ndarray:
    dtype = np.dtype(str(descriptor["dtype"])).newbyteorder("<")
    return np.frombuffer(buffer, dtype=dtype).reshape(descriptor["shape"])  # type: ignore[arg-type]


def test_a_job_comes_back_as_the_run_here() -> None:
    here = fdtd_simulation(_ACOUSTIC)
    code, frames = _serve(_job("fdtd_simulation", {"run": _ACOUSTIC}))
    assert code == 0
    ((header, buffers),) = frames
    assert header["type"] == "result"
    pressures, snapshots = header["arrays"]  # type: ignore[misc]
    assert pressures == {
        "name": "pressures",
        "dtype": "float64",
        "shape": list(here.pressures.shape),
    }
    assert np.array_equal(_array(pressures, buffers[0]), here.pressures)
    assert np.array_equal(_array(snapshots, buffers[1]), here.snapshots)
    assert RunProvenance(**header["provenance"]) == here.provenance  # type: ignore[arg-type]


def test_an_elastic_job_without_snapshots_sends_only_its_signals() -> None:
    run = ElasticRun(
        4000.0,
        2300.0,
        0.01,
        1e-4,
        rho=2500.0,
        shape=(20, 21),
        sources=[
            ExplosionSource(
                ix=10, iy=9, waveform=GaussianPulse(ix=0, iy=0, half_width_s=1e-5).value
            )
        ],
        recording=ElasticRecording(probes=[(5, 5)], probe_fields=("p", "vy")),
    )
    here = elastic_fdtd_simulation(run)
    code, frames = _serve(_job("elastic_fdtd_simulation", {"run": run}))
    ((header, buffers),) = frames
    assert code == 0
    described: list[dict[str, object]] = header["arrays"]  # type: ignore[assignment]
    assert [item["name"] for item in described] == ["signals"]
    assert len(buffers) == 1
    assert np.array_equal(_array(described[0], buffers[0]), here.signals)


_SENT_STREAMS: list[io.BytesIO] = []


def _with_bytes(**arguments: Any) -> tuple[object, node.NodeStream]:
    """A simulation's record without snapshots, and the bytes of a video beside it."""
    here = fdtd_simulation(**arguments)
    record = SimpleNamespace(
        pressures=here.pressures, snapshots=None, provenance=here.provenance
    )
    video = io.BytesIO(_VIDEO)
    _SENT_STREAMS.append(video)
    return record, ("video", video)


def test_a_stream_a_job_returns_travels_after_its_arrays_and_is_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # What an animation job returns beside its record: the video's bytes,
    # whose length only the job knows.
    monkeypatch.setattr(
        node,
        "FUNCTIONS",
        MappingProxyType(
            {"fdtd_simulation": (_with_bytes, ("pressures", "snapshots"))}
        ),
    )
    code, frames = _serve(_job("fdtd_simulation", {"run": _ACOUSTIC}))
    ((header, buffers),) = frames
    assert code == 0
    described: list[dict[str, object]] = header["arrays"]  # type: ignore[assignment]
    assert [item["name"] for item in described] == ["pressures", "video"]
    assert described[1] == {"name": "video", "dtype": "uint8", "shape": [len(_VIDEO)]}
    assert buffers[1] == _VIDEO
    assert _SENT_STREAMS[-1].closed


def test_a_client_that_goes_away_stops_the_run_at_its_next_step() -> None:
    long_run = dataclasses.replace(
        _ACOUSTIC, duration=30.0, recording=FDTDRecording(probes=_PROBES)
    )
    started = time.monotonic()
    code, frames = _serve(
        _job("fdtd_simulation", {"run": long_run}), end_input_after_s=0.5
    )
    assert code == 3
    assert frames == []
    assert time.monotonic() - started < 20.0


def test_a_job_that_raises_sends_its_traceback() -> None:
    # The run was checked where it was built; what fails here is the device
    # the job asks for, a GPU index no machine has.
    absent = {"device": "cupy", "device_index": 99, "dtype": "float64"}
    code, frames = _serve(_job("fdtd_simulation", {"run": _ACOUSTIC}, compute=absent))
    ((header, _),) = frames
    assert code == 1
    assert (header["type"], header["stage"]) == ("error", "job")
    assert str(header["message"]).startswith(
        ("ComputeImportError", "ComputeDeviceError")
    )
    assert "Traceback" in str(header["traceback"])


def test_a_job_naming_another_function_is_refused() -> None:
    job = _job("fdtd_simulation", {"run": _ACOUSTIC}).replace(
        b'"fdtd_simulation"', b'"os_system______"'
    )
    with pytest.raises(bootstrap.Refused, match="the node runs"):
        _serve(job)


def _raw_job(
    arguments: dict[str, object], compute: dict[str, object] = _CPU, kind: str = "job"
) -> bytes:
    """A frame of *kind* whose arguments are the wire data given, with no buffers."""
    out = io.BytesIO()
    header = {
        "type": kind,
        "function": "fdtd_simulation",
        "compute": compute,
        "arguments": arguments,
    }
    bootstrap.write_frame(out, header)
    return out.getvalue()


def _nested(levels: int) -> dict[str, object]:
    """A list inside a list, *levels* deep: JSON reads it, and it rebuilds nothing."""
    tree: dict[str, object] = {"$": "list", "items": []}
    for _ in range(levels):
        tree = {"$": "list", "items": [tree]}
    return tree


@pytest.mark.parametrize(
    ("run", "error"),
    [
        ({"$": "float"}, "KeyError"),
        ({"$": "array", "dtype": "<f8", "shape": [1], "buffer": 0}, "IndexError"),
        ({"$": "pickle", "data": "gASV"}, "ValueError"),
        ({"$": "record", "type": "FDTDRun", "fields": {"speed": 343}}, "TypeError"),
        (_nested(1000), "RecursionError"),
    ],
)
def test_arguments_that_do_not_rebuild_are_refused_by_name(
    run: dict[str, object], error: str
) -> None:
    frames = io.BytesIO()
    with pytest.raises(
        bootstrap.Refused, match=f"arguments do not rebuild: {error}"
    ) as refused:
        node.serve(io.BytesIO(_raw_job({"run": run})), frames)
    assert refused.value.stage == "job"
    assert frames.getvalue() == b""


@pytest.mark.parametrize(
    ("compute", "words"),
    [
        ({**_CPU, "host": "nas"}, "placement holds"),
        ({**_CPU, "fallback": True}, "placement holds"),
        ({"device": "cpu", "dtype": "float64"}, "placement holds"),
        ({**_CPU, "device": "abacus"}, "placement is refused: ValueError"),
        ({**_CPU, "device_index": "0"}, "placement is refused: TypeError"),
    ],
)
def test_a_placement_other_than_a_device_an_index_and_a_dtype_is_refused(
    compute: dict[str, object], words: str
) -> None:
    with pytest.raises(bootstrap.Refused, match=words) as refused:
        node.serve(
            io.BytesIO(_job("fdtd_simulation", {"run": _ACOUSTIC}, compute=compute)),
            io.BytesIO(),
        )
    assert refused.value.stage == "job"


def test_a_frame_that_is_no_job_is_refused() -> None:
    with pytest.raises(bootstrap.Refused, match="expected a job"):
        node.serve(io.BytesIO(_raw_job({}, kind="package")), io.BytesIO())


def _warns_and_returns(**arguments: object) -> tuple[object, None]:
    warnings.warn("device 'cupy' is absent", ComputeFallbackWarning, stacklevel=1)
    warnings.warn("overflow in a sum", RuntimeWarning, stacklevel=1)
    warnings.warn("overflow in a sum", RuntimeWarning, stacklevel=1)
    here = fdtd_simulation(_ACOUSTIC)
    return SimpleNamespace(
        pressures=here.pressures, snapshots=None, provenance=here.provenance
    ), None


def test_the_warnings_of_a_run_travel_once_each_with_their_class(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        node,
        "FUNCTIONS",
        MappingProxyType(
            {"fdtd_simulation": (_warns_and_returns, ("pressures", "snapshots"))}
        ),
    )
    code, frames = _serve(_job("fdtd_simulation", {"run": _ACOUSTIC}))
    ((header, _),) = frames
    assert code == 0
    assert header["warnings"] == [
        {
            "category": "phonometry.simulation.compute:ComputeFallbackWarning",
            "message": "device 'cupy' is absent",
        },
        {"category": "builtins:RuntimeWarning", "message": "overflow in a sum"},
    ]


def test_a_node_takes_the_host_out_of_its_own_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PHONOMETRY_COMPUTE", "cpu@nas,float32")
    _serve(_job("fdtd_simulation", {"run": _ACOUSTIC}))
    assert os.environ["PHONOMETRY_COMPUTE"] == "cpu,float32"


# The hook the simulation functions call after each step.


@pytest.mark.parametrize("function", ["fdtd", "elastic"])
def test_a_simulation_reports_each_step_to_its_watcher(function: str) -> None:
    seen: list[tuple[int, int]] = []
    with _observer.observing(lambda done, total: seen.append((done, total))):
        if function == "fdtd":
            res = fdtd_simulation(dataclasses.replace(_ACOUSTIC, duration=1e-4))
        else:
            res = elastic_fdtd_simulation(
                ElasticRun(
                    4000.0,
                    2300.0,
                    0.01,
                    1e-4,
                    rho=2500.0,
                    shape=(12, 12),
                    sources=[
                        ExplosionSource(
                            ix=6,
                            iy=6,
                            waveform=GaussianPulse(ix=0, iy=0, half_width_s=1e-5).value,
                        )
                    ],
                )
            )
    steps = res.times.size - 1
    assert seen == [(k, steps) for k in range(1, steps + 1)]


def test_nobody_watches_outside_a_block() -> None:
    _observer.step_done(1, 2)  # nothing to call, nothing raised
    with _observer.observing(lambda done, total: None):
        pass
    assert _observer._WATCHER.get() is None


def test_the_node_s_watcher_stops_a_cancelled_run_and_writes_progress(
    capsys: pytest.CaptureFixture[str],
) -> None:
    cancelled = threading.Event()
    watcher = node._Watcher(cancelled)
    watcher(1, 100)
    watcher(2, 100)  # within the second: no line
    watcher(100, 100)  # the last step always writes
    lines = capsys.readouterr().err.splitlines()
    assert lines == [f"{bootstrap.PROGRESS} 1 100", f"{bootstrap.PROGRESS} 100 100"]
    cancelled.set()
    with pytest.raises(_observer.RunCancelled):
        watcher(3, 100)


# The bootstrap and the node together, in a process of their own.


def _through_a_node(
    tmp_path: Path, job: bytes
) -> tuple[list[object], dict[str, object], list[bytes], int, bytes]:
    """Send the package and *job* to a bootstrap in a process of its own.

    The input stays open until the node has exited, as a client still reading
    the answer keeps it. Returns the kinds of the frames, the last header and
    its buffers, the exit status and what the node wrote to standard error.
    """
    shipped = installed_package()
    hello = io.BytesIO()
    bootstrap.write_frame(
        hello,
        {
            "type": "hello",
            "protocol": bootstrap.PROTOCOL,
            "digest": shipped.digest,
            "python_floor": PYTHON_FLOOR,
            "floors": dict(FLOORS),
        },
    )
    package = io.BytesIO()
    bootstrap.write_frame(
        package,
        {
            "type": "package",
            "digest": shipped.digest,
            "paths": [path for path, _ in shipped.files],
        },
        [memoryview(data) for _, data in shipped.files],
    )
    env = {**os.environ, bootstrap.CACHE_VAR: str(tmp_path)}
    process = subprocess.Popen(
        [sys.executable, "-I", bootstrap.__file__],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    assert process.stderr is not None
    try:
        process.stdin.write(hello.getvalue() + package.getvalue() + job)
        process.stdin.flush()
        kinds = []
        while not kinds or kinds[-1] not in ("result", "error"):
            header = bootstrap.read_header(process.stdout)
            buffers = [
                bootstrap.read_exact(process.stdout, n)
                for n in bootstrap.field(header, "buffers", list)
            ]
            kinds.append(header["type"])
        code = process.wait(timeout=60)
        log = process.stderr.read()
    finally:
        process.kill()
        process.wait(timeout=60)
        process.stdin.close()
        process.stdout.close()
        process.stderr.close()
    return kinds, header, buffers, code, log


def test_the_bootstrap_hands_the_shipped_package_to_the_node_and_the_job_runs(
    tmp_path: Path,
) -> None:
    kinds, header, buffers, code, log = _through_a_node(
        tmp_path, _job("fdtd_simulation", {"run": _ACOUSTIC})
    )
    assert kinds == ["hello", "stored", "ready", "result"], log
    assert code == 0, log
    assert f"{bootstrap.PROGRESS} ".encode() in log
    here = fdtd_simulation(_ACOUSTIC)
    assert np.array_equal(_array(header["arrays"][0], buffers[0]), here.pressures)  # type: ignore[index]
    assert (
        tmp_path
        / installed_package().digest
        / "phonometry"
        / "simulation"
        / "_remote"
        / "node.py"
    ).is_file()


@pytest.mark.parametrize(
    ("job", "stage", "message"),
    [
        (
            _raw_job({"run": {"$": "float"}}),
            "job",
            "the job's arguments do not rebuild: KeyError",
        ),
        (b"NOPE\x00\x00\x00\x02{}", "frame", "the stream does not start a frame"),
    ],
)
def test_a_job_the_node_refuses_comes_back_as_an_error_frame_of_its_stage(
    tmp_path: Path, job: bytes, stage: str, message: str
) -> None:
    # The bootstrap runs as a script, the node's refusals come from the
    # package it imported: they still end as a refusal of their own stage.
    kinds, header, _, code, log = _through_a_node(tmp_path, job)
    assert kinds == ["hello", "stored", "ready", "error"], log
    assert code == 2, log
    assert header["stage"] == stage
    assert str(header["message"]).startswith(message)
