#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A node runs the job it is sent and answers with what the client cannot rebuild."""

from __future__ import annotations

import contextlib
import dataclasses
import errno
import io
import os
import subprocess
import sys
import threading
import time
import types
import warnings
from types import MappingProxyType, SimpleNamespace
from typing import IO, TYPE_CHECKING, Any

import numpy as np
import pytest

import phonometry
from phonometry.simulation import (
    ComputeFallbackWarning,
    ElasticRecording,
    ElasticRun,
    ExplosionSource,
    FDTDBoundaries,
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
    from collections.abc import Callable, Iterator
    from pathlib import Path

_CPU = {"device": "cpu", "device_index": 0, "dtype": "float64"}
_PROBES = [(30, 15), (5, 5)]
_ACOUSTIC = FDTDRun(
    c=343.0,
    dx=0.01,
    duration_s=2e-3,
    shape=(30, 40),
    sources=[GaussianPulse(ix=10, iy=15, half_width_s=4e-5)],
    recording=FDTDRecording(probes=_PROBES, snapshot_every=20, snapshot_decimation=2),
    boundaries=FDTDBoundaries(sides="absorbing", absorbing_layer_cells=5),
)
#: What a job returns beside its record when it has bytes of its own to send.
_VIDEO = b"\x1aE\xdf\xa3 a video"
#: The name of the thread that watches a node's input.
_WATCHER = "phonometry-node-input"
#: How long a test waits on a thread it started [s]: each ends within
#: milliseconds once its input does.
_THREAD_S = 30.0
#: How long a node in a process of its own may take, from the package it is
#: sent to its exit [s]. On a Windows runner, the slowest in CI, it takes 2 s
#: to 3.5 s, and took 31 s once, on Python 3.14: more than ten times that,
#: and short of the fifteen minutes pytest gives the test.
_NODE_S = 360.0


def _job(
    function: str,
    arguments: dict[str, Any],
    compute: dict[str, object] = _CPU,
    version: str = phonometry.__version__,
) -> bytes:
    tree, buffers = wire.encode_arguments(arguments)
    out = io.BytesIO()
    header = {
        "type": "job",
        "function": function,
        "compute": compute,
        "phonometry_version": version,
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


@contextlib.contextmanager
def _closed_quietly(file: IO[bytes]) -> Iterator[IO[bytes]]:
    """*file*, closed on the way out even when the flush of what it holds fails."""
    try:
        yield file
    finally:
        with contextlib.suppress(OSError):
            file.close()


def _serve(
    job: bytes,
    *,
    end_input_after_s: float | None = None,
    client_s: float = _THREAD_S,
) -> tuple[int, list[tuple[dict[str, object], list[bytes]]]]:
    """Serve *job* in this process, the input open as a client keeps it.

    The input stays open until the node answers, as a client's does, or ends
    after *end_input_after_s* seconds, as when a client goes away. The
    threads the client and the node start here have ended when it returns.
    The client has *client_s* seconds to send the job once the node is done.

    The client's end of the input is closed after the node's: a client still
    blocked writing a job the node stopped reading holds its file's lock, and
    closing that file first would wait for the write. With the node's end
    closed, the write fails, as it does when a connection drops.
    """
    read_end, write_end = os.pipe()
    out = io.BytesIO()
    before = set(threading.enumerate())
    with (
        _closed_quietly(os.fdopen(write_end, "wb")) as feed,
        os.fdopen(read_end, "rb") as stream,
    ):

        def client() -> None:
            with contextlib.suppress(OSError):
                feed.write(job)
                feed.flush()
                if end_input_after_s is not None:
                    time.sleep(end_input_after_s)
                    feed.close()

        sender = threading.Thread(target=client, daemon=True)
        sender.start()
        try:
            code = node.serve(stream, out)
        finally:
            sender.join(client_s)
        assert not sender.is_alive(), "the client never finished sending the job"
    # Both ends are closed, so the input has ended: the node's watcher ends
    # with it, and none outlives the test that started it.
    _join_watchers(before)
    return code, _frames(out.getvalue())


def _join_watchers(before: set[threading.Thread]) -> None:
    """Wait for every watcher started since *before* was taken; fail on one that does not end."""
    for thread in set(threading.enumerate()) - before:
        if thread.name == _WATCHER:
            thread.join(_THREAD_S)
            assert not thread.is_alive(), "a watcher outlived the input it watched"


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


#: A version no package here has, so that a record holding it can only have
#: come from the job.
_SENT_VERSION = "0.0.0.post7"


def test_a_node_records_the_version_the_job_was_sent_with() -> None:
    code, frames = _serve(
        _job("fdtd_simulation", {"run": _ACOUSTIC}, version=_SENT_VERSION)
    )
    ((header, _),) = frames
    assert code == 0
    assert header["provenance"]["phonometry_version"] == _SENT_VERSION  # type: ignore[index]


def test_a_node_never_reads_a_version_of_its_own(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A node runs the package it was sent from its cache, where neither
    # installed metadata nor the source tree's VERSION file names it: a read
    # of phonometry.__version__ there fails, as this stand-in does.
    monkeypatch.setitem(sys.modules, "phonometry._version", types.ModuleType("gone"))
    with pytest.raises(ImportError, match="__version__"):
        fdtd_simulation(_ACOUSTIC)
    code, frames = _serve(
        _job("fdtd_simulation", {"run": _ACOUSTIC}, version=_SENT_VERSION)
    )
    ((header, _),) = frames
    assert (code, header["type"]) == (0, "result"), header.get("message")
    assert header["provenance"]["phonometry_version"] == _SENT_VERSION  # type: ignore[index]


def test_a_job_that_names_no_version_breaks_the_frame() -> None:
    job = _job("fdtd_simulation", {"run": _ACOUSTIC}).replace(
        b'"phonometry_version"', b'"phonometry_versioN"'
    )
    with pytest.raises(bootstrap.FrameError, match="'phonometry_version' of a frame"):
        _serve(job)


def test_an_elastic_job_without_snapshots_sends_only_its_signals() -> None:
    run = ElasticRun(
        c_p=4000.0,
        c_s=2300.0,
        dx=0.01,
        duration_s=1e-4,
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
        _ACOUSTIC, duration_s=30.0, recording=FDTDRecording(probes=_PROBES)
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


def test_a_job_the_node_stops_reading_ends_the_helper_with_the_node_s_refusal() -> None:
    """The client of :func:`_serve` blocked writing the rest of a refused job holds nothing.

    The node refuses a frame by its first bytes and reads no further; the
    client is left writing far more than a pipe holds, and :func:`_serve`
    comes back once its time for the client is up, with the refusal.
    """
    job = b"NOPE" + bytes(4 << 20)
    started = time.monotonic()
    with pytest.raises(bootstrap.FrameError, match="does not start a frame"):
        _serve(job, client_s=1.0)
    elapsed = time.monotonic() - started
    assert elapsed < _THREAD_S, f"the helper came back after {elapsed:.0f} s"


def _raw_job(
    arguments: dict[str, object], compute: dict[str, object] = _CPU, kind: str = "job"
) -> bytes:
    """A frame of *kind* whose arguments are the wire data given, with no buffers."""
    out = io.BytesIO()
    header = {
        "type": kind,
        "function": "fdtd_simulation",
        "compute": compute,
        "phonometry_version": phonometry.__version__,
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
    job = io.BytesIO(_raw_job({"run": run}))
    frames = io.BytesIO()
    with pytest.raises(
        bootstrap.Refused, match=f"arguments do not rebuild: {error}"
    ) as refused:
        node.serve(job, frames)
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
    job = io.BytesIO(_job("fdtd_simulation", {"run": _ACOUSTIC}, compute=compute))
    frames = io.BytesIO()
    with pytest.raises(bootstrap.Refused, match=words) as refused:
        node.serve(job, frames)
    assert refused.value.stage == "job"


def test_a_frame_that_is_no_job_is_refused() -> None:
    job = io.BytesIO(_raw_job({}, kind="package"))
    frames = io.BytesIO()
    with pytest.raises(bootstrap.Refused, match="expected a job"):
        node.serve(job, frames)


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


def _warns_long_and_returns(**arguments: object) -> tuple[object, None]:
    # Two messages that differ only past the length an error frame carries.
    long = "x" * (2 * bootstrap._MAX_MESSAGE)
    warnings.warn(f"{long}a", UserWarning, stacklevel=1)
    warnings.warn(f"{long}b", UserWarning, stacklevel=1)
    here = fdtd_simulation(_ACOUSTIC)
    return SimpleNamespace(
        pressures=here.pressures, snapshots=None, provenance=here.provenance
    ), None


def test_a_long_warning_travels_cut_to_the_length_of_an_error_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # As many such warnings as a result carries still fit the header a
    # client reads.
    monkeypatch.setattr(
        node,
        "FUNCTIONS",
        MappingProxyType(
            {"fdtd_simulation": (_warns_long_and_returns, ("pressures", "snapshots"))}
        ),
    )
    code, frames = _serve(_job("fdtd_simulation", {"run": _ACOUSTIC}))
    ((header, _),) = frames
    assert code == 0
    assert header["warnings"] == [
        {"category": "builtins:UserWarning", "message": "x" * bootstrap._MAX_MESSAGE}
    ]


@pytest.mark.parametrize("value", ["cpu@nas,float32", "cpu@nas,fallback", "cupy:1@nas"])
def test_a_node_takes_the_variable_that_could_name_a_host_out_of_its_environment(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    # The job names the placement, so the variable decides nothing here; a
    # host left in it would send the run on, and a value without the host
    # ("cpu,fallback") is one the variable's reader refuses.
    monkeypatch.setenv("PHONOMETRY_COMPUTE", value)
    code, _ = _serve(_job("fdtd_simulation", {"run": _ACOUSTIC}))
    assert code == 0
    assert "PHONOMETRY_COMPUTE" not in os.environ


# The hook the simulation functions call after each step.


@pytest.mark.parametrize("function", ["fdtd", "elastic"])
def test_a_simulation_reports_each_step_to_its_watcher(function: str) -> None:
    seen: list[tuple[int, int]] = []
    with _observer.observing(lambda done, total: seen.append((done, total))):
        if function == "fdtd":
            res = fdtd_simulation(dataclasses.replace(_ACOUSTIC, duration_s=1e-4))
        else:
            res = elastic_fdtd_simulation(
                ElasticRun(
                    c_p=4000.0,
                    c_s=2300.0,
                    dx=0.01,
                    duration_s=1e-4,
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


# The thread that watches a node's input.


class _Scheduler:
    """The scheduler at its worst for the watcher: it takes the processor away once and gives it back when told."""

    def __init__(self) -> None:
        self.held = threading.Event()
        self.released = threading.Event()

    def hold(self) -> None:
        """Hold the calling thread until released, the first time the watcher calls."""
        if threading.current_thread().name == _WATCHER and not self.held.is_set():
            self.held.set()
            self.released.wait(_THREAD_S)


class _HeldThreading:
    """``threading`` as node.py sees it: the thread it starts is held before its first line."""

    def __init__(self, scheduler: _Scheduler) -> None:
        self._scheduler = scheduler

    # Whatever threading holds, of whatever type it has.
    def __getattr__(self, name: str) -> Any:  # noqa: ANN401
        return getattr(threading, name)

    # threading's own name, which node.py calls.
    def Thread(  # noqa: N802
        self, *, target: Callable[[], object], **options: Any
    ) -> threading.Thread:
        def held() -> None:
            self._scheduler.hold()
            target()

        return threading.Thread(target=held, **options)


class _HeldOs:
    """``os`` as node.py sees it: the watcher's first call into it is held.

    The call is held once its arguments are worked out, as a thread loses
    the processor between taking a number and using it.
    """

    def __init__(self, scheduler: _Scheduler) -> None:
        self._scheduler = scheduler

    # Whatever os holds, of whatever type it has.
    def __getattr__(self, name: str) -> Any:  # noqa: ANN401
        value = getattr(os, name)
        if not callable(value):
            return value

        def held(*args: object, **kwargs: object) -> object:
            self._scheduler.hold()
            return value(*args, **kwargs)

        return held


def _next_pipe_under(number: int) -> int:
    """Open the next pipe with its read end under *number*, which is free; return its write end.

    The lowest free number usually is *number* already. When a lower one is
    free, the read end is moved onto *number*, the write end first taken off
    it if it landed there.
    """
    next_read, next_write = os.pipe()
    if next_read != number:
        if next_write == number:
            moved = os.dup(next_write)
            os.close(next_write)
            next_write = moved
        os.dup2(next_read, number, inheritable=False)
        os.close(next_read)
    return next_write


@pytest.mark.parametrize("moment", ["before its first line", "at its first call to os"])
def test_the_watcher_reads_its_own_input_and_never_the_next_file_opened(
    moment: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The caller may close the stream as soon as serve returns.

    A watcher that took the stream's descriptor number in its own thread
    could lose the processor before it read, or before it copied the
    number, and then read whatever the process opened next under that
    number: in a worker that serves one job after another, the next job's
    pipe, whose job then never reaches its node. Here the watcher is held
    at the worst moment, before it runs at all or at its first call to
    ``os``, while the stream is closed and its number given to the next
    pipe; it must still read its own input, and only that.
    """
    scheduler = _Scheduler()
    if moment == "before its first line":
        monkeypatch.setattr(node, "threading", _HeldThreading(scheduler))
    else:
        monkeypatch.setattr(node, "os", _HeldOs(scheduler))
    read_end, write_end = os.pipe()
    stream = os.fdopen(read_end, "rb")
    opened = [write_end]
    cancelled, finished = threading.Event(), threading.Event()
    finished.set()  # the run is over: the watcher ends as soon as its input does
    before = set(threading.enumerate())
    try:
        node._watch_input(stream, cancelled, finished)
        assert scheduler.held.wait(_THREAD_S), "the watcher never ran"
        stream.close()
        # The next pipe the process opens, its read end under the number the
        # stream had, and a job waiting in it.
        next_write = _next_pipe_under(read_end)
        opened.append(read_end)
        os.write(next_write, b"the next job")
        os.close(next_write)
        scheduler.released.set()
        still_watching = not cancelled.wait(0.5)
        os.close(write_end)
        opened.remove(write_end)
        _join_watchers(before)
        left = os.read(read_end, 64)
    finally:
        scheduler.released.set()
        stream.close()
        for descriptor in opened:
            with contextlib.suppress(OSError):
                os.close(descriptor)
    assert left == b"the next job", "the watcher took the bytes of the next pipe"
    assert still_watching, "the watcher stopped before its own input ended"
    assert cancelled.is_set()


class _FailingOs:
    """``os`` as node.py sees it, the call it names failing with *code*; copies and closes are noted."""

    def __init__(self, call: str, code: int) -> None:
        self._call = call
        self._code = code
        self.copies: list[int] = []
        self.closing: list[int] = []
        self.closed: list[int] = []

    # Whatever os holds, of whatever type it has.
    def __getattr__(self, name: str) -> Any:  # noqa: ANN401
        return getattr(os, name)

    def _fail(self, call: str) -> None:
        if call == self._call:
            raise OSError(self._code, f"{call} failed on purpose")

    def dup(self, descriptor: int) -> int:
        self._fail("dup")
        copy = os.dup(descriptor)
        self.copies.append(copy)
        return copy

    def read(self, descriptor: int, size: int) -> bytes:
        self._fail("read")
        return os.read(descriptor, size)

    def close(self, descriptor: int) -> None:
        self.closing.append(descriptor)
        self._fail("close")
        os.close(descriptor)
        self.closed.append(descriptor)


def test_an_input_the_node_cannot_copy_is_an_error_and_not_a_client_gone(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With no descriptor left, the node says so; it does not stop the run as if the client had left."""
    monkeypatch.setattr(node, "os", _FailingOs("dup", errno.EMFILE))
    read_end, write_end = os.pipe()
    stream = os.fdopen(read_end, "rb")
    cancelled, finished = threading.Event(), threading.Event()
    # A watcher started all the same must not end this process once its
    # grace runs out: the run it would wait for is over.
    finished.set()
    before = set(threading.enumerate())
    try:
        with pytest.raises(OSError, match="dup failed on purpose") as raised:
            node._watch_input(stream, cancelled, finished)
    finally:
        stream.close()
        os.close(write_end)
    assert raised.value.errno == errno.EMFILE
    assert not cancelled.is_set()
    assert not any(t.name == _WATCHER for t in set(threading.enumerate()) - before)


@pytest.mark.parametrize(
    ("call", "code", "closes"),
    [
        pytest.param("read", errno.EIO, "its copy", id="read fails"),
        pytest.param("read", errno.EBADF, "nothing", id="read finds no descriptor"),
        pytest.param("close", errno.EIO, "its copy", id="close fails"),
    ],
)
def test_a_watcher_whose_input_fails_still_stops_the_run(
    call: str, code: int, closes: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A read or a close that fails ends the input too, and the run is told.

    The copy is closed unless the read found it closed already: by then its
    number may name another file, which is not the watcher's to close.
    """
    failing = _FailingOs(call, code)
    monkeypatch.setattr(node, "os", failing)
    read_end, write_end = os.pipe()
    cancelled, finished = threading.Event(), threading.Event()
    finished.set()  # the run is over: the watcher ends as soon as its input does
    before = set(threading.enumerate())
    try:
        with os.fdopen(read_end, "rb") as stream:
            node._watch_input(stream, cancelled, finished)
            os.close(write_end)
            write_end = -1
            assert cancelled.wait(_THREAD_S), "the run was never told its input ended"
            _join_watchers(before)
    finally:
        for descriptor in [write_end, *failing.copies]:
            if descriptor >= 0 and descriptor not in failing.closed:
                with contextlib.suppress(OSError):
                    os.close(descriptor)
    assert len(failing.copies) == 1
    assert failing.closing == (failing.copies if closes == "its copy" else [])


def test_an_input_that_is_no_file_has_ended() -> None:
    cancelled, finished = threading.Event(), threading.Event()
    finished.set()
    before = set(threading.enumerate())
    node._watch_input(io.BytesIO(b"sent after the job"), cancelled, finished)
    assert cancelled.wait(_THREAD_S)
    _join_watchers(before)


def test_a_node_whose_last_cleanup_fails_still_ends_its_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A run that does not stop once its client is gone ends the node, whatever the cleanup before the exit meets."""
    monkeypatch.setattr(node, "_GRACE_S", 0.0)
    codes: list[int] = []
    monkeypatch.setattr(os, "_exit", codes.append)

    def broken() -> None:
        msg = "the cleanup failed on purpose"
        raise RuntimeError(msg)

    monkeypatch.setattr(node, "remove_scratch_videos", broken)
    raised: list[type[BaseException]] = []
    monkeypatch.setattr(
        threading, "excepthook", lambda hook: raised.append(hook.exc_type)
    )
    cancelled, finished = threading.Event(), threading.Event()
    before = set(threading.enumerate())
    node._watch_input(io.BytesIO(b""), cancelled, finished)
    _join_watchers(before)
    assert codes == [130]
    assert raised == [RuntimeError]


# The bootstrap and the node together, in a process of their own.


def _through_a_node(
    tmp_path: Path, job: bytes
) -> tuple[list[object], dict[str, object], list[bytes], int, bytes]:
    """Send the package and *job* to a bootstrap in a process of its own.

    The input stays open until the node has exited, as a client still reading
    the answer keeps it. Returns the kinds of the frames, the last header and
    its buffers, the exit status and what the node wrote to standard error.

    Standard error is read as it comes, so a node never waits on a pipe this
    test is not reading; a node still running after :data:`_NODE_S` seconds
    is killed, which ends every read and write below, and the test fails
    saying so.
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
    stderr = process.stderr
    said: list[bytes] = []
    reader = threading.Thread(target=lambda: said.append(stderr.read()), daemon=True)
    reader.start()
    expired = threading.Event()

    def expire() -> None:
        expired.set()
        process.kill()

    killer = threading.Timer(_NODE_S, expire)
    killer.start()
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
        code = process.wait(timeout=_NODE_S)
    except (OSError, bootstrap.FrameError, subprocess.TimeoutExpired) as exc:
        if expired.is_set():
            pytest.fail(f"the node did not finish within {_NODE_S:g} s: {exc}")
        raise
    finally:
        killer.cancel()
        process.kill()
        process.wait(timeout=_NODE_S)
        reader.join(_THREAD_S)
        with contextlib.suppress(OSError):
            process.stdin.close()
        process.stdout.close()
        # A reader still blocked on standard error holds the file's lock:
        # closing it would wait as long as the reader does.
        if not reader.is_alive():
            stderr.close()
    # A node killed once its answer was in comes back with the kill's status
    # and no error above: the limit is what ended it, and the test says so.
    if expired.is_set():
        pytest.fail(f"the node did not finish within {_NODE_S:g} s")
    assert not reader.is_alive(), "standard error stayed open after the node ended"
    return kinds, header, buffers, code, b"".join(said)


def test_the_bootstrap_hands_the_shipped_package_to_the_node_and_the_job_runs(
    tmp_path: Path,
) -> None:
    kinds, header, buffers, code, log = _through_a_node(
        tmp_path,
        _job("fdtd_simulation", {"run": _ACOUSTIC}, version=_SENT_VERSION),
    )
    assert kinds == ["hello", "stored", "ready", "result"], log
    assert code == 0, log
    assert f"{bootstrap.PROGRESS} ".encode() in log
    here = fdtd_simulation(_ACOUSTIC)
    assert np.array_equal(_array(header["arrays"][0], buffers[0]), here.pressures)  # type: ignore[index]
    assert header["provenance"]["phonometry_version"] == _SENT_VERSION  # type: ignore[index]
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
