#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A simulation sent to a node comes back as the run here, through a stand-in for ssh.

The node is this machine: a Python node whose interpreter is the one running
the tests, reached through ``fake_ssh.py``, which runs the remote command
here as a shell would split it and relays its streams as ssh does. The rest
of the conversation is real: the bootstrap sent inline, the package shipped
into a cache of the module's own, the job carrying the run, the arrays and
the warnings. It runs on Linux, macOS and Windows; on Windows the stand-in
enters through the module's hook, since a batch file on PATH cannot carry
the remote command intact. Every run on the node is bounded by the hosts
file's timeout: the client kills the stand-in, which closes the pipes it
reads and the node's input with them, so a node that stops answering fails
its test instead of holding the suite.
"""

from __future__ import annotations

import contextlib
import dataclasses
import inspect
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

import numpy as np
import pytest

from phonometry.simulation import (
    FDTD2D,
    Compute,
    ComputeFallbackWarning,
    ComputeRemoteError,
    CWSource,
    ElasticFDTD2D,
    ElasticRecording,
    ElasticRun,
    ExplosionSource,
    FDTDBoundaries,
    FDTDRecording,
    FDTDRun,
    GaussianPulse,
    PlaneWaveSource,
    RunProvenance,
    elastic_fdtd_simulation,
    fdtd_simulation,
    use,
)
from phonometry.simulation._remote import bootstrap, client, command, package

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

pytestmark = pytest.mark.xdist_group("remote-node")

_FAKE_SSH = Path(__file__).with_name("fake_ssh.py")
_SRC = Path(package.__file__).resolve().parents[3]
#: The longest the import check's own interpreter may take [s].
_SUBPROCESS_TIMEOUT_S = 120
#: The longest the stand-in for ssh may take to write the node's process
#: id once the node has answered [s].
_PIDFILE_WAIT_S = 30.0


def _acoustic() -> FDTDRun:
    mask = np.zeros((40, 50), dtype=bool)
    mask[18:22, 30:33] = True
    return FDTDRun(
        c=343.0,
        dx=0.01,
        duration_s=2e-3,
        shape=(40, 50),
        sources=[
            GaussianPulse(ix=10, iy=20, half_width_s=4e-5),
            PlaneWaveSource(
                direction="right",
                waveform=CWSource(ix=0, iy=0, frequency=3000.0).value,
                offset=7,
            ),
        ],
        recording=FDTDRecording(
            probes=[(40, 20), (25, 10)], snapshot_every=10, snapshot_decimation=3
        ),
        boundaries=FDTDBoundaries(
            sides={"left": "absorbing", "top": 413.0}, absorbing_layer_cells=6
        ),
        obstacle_mask=mask,
    )


def _small(duration: float = 1e-3) -> FDTDRun:
    return FDTDRun(
        c=343.0,
        dx=0.01,
        duration_s=duration,
        shape=(20, 20),
        sources=[GaussianPulse(ix=10, iy=10, half_width_s=4e-5)],
        recording=FDTDRecording(probes=[(5, 5)]),
    )


def _elastic(**changes: object) -> ElasticRun:
    source = ExplosionSource(
        ix=6, iy=6, waveform=GaussianPulse(ix=0, iy=0, half_width_s=1e-5).value
    )
    fields: dict[str, object] = {
        "rho": 2500.0,
        "shape": (12, 12),
        "sources": [source],
        **changes,
    }
    return ElasticRun(c_p=4000.0, c_s=2300.0, dx=0.01, duration_s=1e-4, **fields)  # type: ignore[arg-type]


def _run_for(function: Callable[..., object]) -> FDTDRun | ElasticRun:
    """A small run of the engine *function* steps."""
    return _small() if function is fdtd_simulation else _elastic()


def _assert_same_result(there: object, here: object) -> None:
    """Every field of the record equal, arrays bit for bit; the provenance apart."""
    for f in dataclasses.fields(here):  # type: ignore[arg-type]
        if f.name == "provenance":
            continue
        got, want = getattr(there, f.name), getattr(here, f.name)
        if isinstance(want, np.ndarray):
            assert isinstance(got, np.ndarray), f.name
            assert got.dtype == want.dtype, f.name
            assert np.array_equal(got, want), f.name
        else:
            assert got == want, f.name


def _alive(pid: int) -> bool:
    """Whether process *pid* still runs; a zombie waiting for its parent does not."""
    stat = Path(f"/proc/{pid}/stat")
    if stat.exists():
        return stat.read_text(encoding="utf-8").rsplit(") ", 1)[1][:1] != "Z"
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def _written(pidfile: Path) -> bool:
    """Whether *pidfile* holds a whole process id: a file just opened for writing is empty."""
    try:
        return pidfile.read_text(encoding="utf-8").strip().isdigit()
    except FileNotFoundError:
        return False


# A run there is the run here.


def test_a_run_on_a_node_equals_the_run_here(node: str) -> None:
    # One run for both: the plane wave's waveform is a bound method, and two
    # CWSource objects make two unequal waveforms.
    run = _acoustic()
    here = fdtd_simulation(run)
    there = fdtd_simulation(run, compute=Compute(host=node))
    _assert_same_result(there, here)
    assert there.provenance.host == node
    assert there.provenance.package_sha256 == package.installed_package().digest
    assert (
        dataclasses.replace(there.provenance, host=None, package_sha256=None)
        == here.provenance
    )


def test_an_elastic_float32_run_on_a_node_equals_the_run_here(node: str) -> None:
    run = ElasticRun(
        c_p=4000.0,
        c_s=2300.0,
        dx=0.01,
        duration_s=2e-4,
        rho=2500.0,
        shape=(30, 31),
        sources=[
            ExplosionSource(
                ix=15,
                iy=14,
                waveform=GaussianPulse(ix=0, iy=0, half_width_s=1e-5).value,
            )
        ],
        recording=ElasticRecording(
            probes=[(5, 5), (20, 10)],
            probe_fields=("p", "vx", "vy"),
            snapshot_every=5,
            snapshot_field="vy",
            snapshot_decimation=2,
        ),
    )
    here = elastic_fdtd_simulation(run, compute=Compute(dtype="float32"))
    there = elastic_fdtd_simulation(run, compute=Compute(host=node, dtype="float32"))
    _assert_same_result(there, here)
    assert there.snapshots is not None
    assert there.snapshots.dtype == np.float32


def test_a_run_with_no_probes_and_no_snapshots_comes_back_whole(node: str) -> None:
    run = FDTDRun(
        c=343.0,
        dx=0.01,
        duration_s=1e-3,
        shape=(20, 20),
        sources=[GaussianPulse(ix=10, iy=10, half_width_s=4e-5)],
    )
    here = fdtd_simulation(run)
    there = fdtd_simulation(run, compute=Compute(host=node))
    assert there.pressures.shape == (0, here.times.size)
    assert there.snapshots is None
    _assert_same_result(there, here)


def test_a_node_that_holds_the_package_is_not_sent_it_again(
    node: str, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger="phonometry.simulation")
    fdtd_simulation(_small(), compute=Compute(host=node))
    caplog.clear()
    fdtd_simulation(_small(), compute=Compute(host=node))
    messages = [record.getMessage() for record in caplog.records]
    assert not any("sending the package" in m for m in messages)
    assert any(m.startswith("this machine: step ") for m in messages)


@pytest.mark.parametrize("function", [fdtd_simulation, elastic_fdtd_simulation])
def test_the_remote_route_sends_every_parameter(
    function: Callable[..., object], node: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent: dict[str, object] = {}

    def capture(
        name: str,
        request: Compute,
        arguments: dict[str, object],
        *rest: object,
        **sink: object,
    ) -> RunProvenance:
        sent.update(arguments)
        return RunProvenance(
            host=request.host,
            device="cpu",
            device_index=0,
            dtype="float64",
            numpy_version=np.__version__,
            array_library=None,
            cuda_runtime=None,
            cuda_driver_api=None,
            gpu=None,
            package_sha256="0" * 64,
        )

    monkeypatch.setattr(client, "run_remote", capture)
    run = _run_for(function)
    function(run, compute=Compute(host=node))
    assert set(sent) == set(inspect.signature(function).parameters) - {"compute"}
    assert sent["run"] is run


def test_a_run_here_imports_nothing_of_the_remote_route() -> None:
    code = (
        "import sys; from phonometry.simulation import FDTDRun, GaussianPulse, fdtd_simulation; "
        "fdtd_simulation(FDTDRun(c=343.0, dx=0.01, duration_s=1e-4, shape=(8, 8), "
        "sources=[GaussianPulse(ix=4, iy=4, half_width_s=4e-5)])); "
        "print(sorted(m for m in sys.modules if m.startswith('phonometry.simulation._remote')))"
    )
    env = {k: v for k, v in os.environ.items() if k != "PHONOMETRY_COMPUTE"}
    env["PYTHONPATH"] = os.pathsep.join(
        filter(None, (str(_SRC), os.environ.get("PYTHONPATH")))
    )
    done = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=_SUBPROCESS_TIMEOUT_S,
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == "[]"


# A host goes to the node wherever the request came from; only the fallback
# builds an engine here.

_Where = Literal["argument", "use", "environment"]


@contextlib.contextmanager
def _asked(
    where: _Where, request: Compute, monkeypatch: pytest.MonkeyPatch
) -> Iterator[Compute | None]:
    """Make *request* the placement through *where*; yields the ``compute=`` to pass."""
    if where == "argument":
        yield request
    elif where == "use":
        with use(request):
            yield None
    else:
        text = f"{request.device}@{request.host}" + (
            ",fallback" if request.fallback else ""
        )
        monkeypatch.setenv("PHONOMETRY_COMPUTE", text)
        yield None


def _engines_built(monkeypatch: pytest.MonkeyPatch) -> list[object]:
    """The placement of every engine built in this process from now on."""
    built: list[object] = []
    for engine in (FDTD2D, ElasticFDTD2D):

        def spy(
            self: object,
            *args: object,
            _original: Callable[..., None] = engine.__init__,
            **kwargs: object,
        ) -> None:
            built.append(kwargs.get("compute"))
            _original(self, *args, **kwargs)

        monkeypatch.setattr(engine, "__init__", spy)
    return built


@pytest.mark.parametrize("where", ["argument", "use", "environment"])
@pytest.mark.parametrize("function", [fdtd_simulation, elastic_fdtd_simulation])
def test_a_host_sends_the_run_to_the_node_and_builds_no_engine_here(
    function: Callable[..., object],
    where: _Where,
    node: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = _run_for(function)
    built = _engines_built(monkeypatch)
    with _asked(where, Compute(host=node), monkeypatch) as compute:
        there = function(run, compute=compute)
    assert built == []
    assert there.provenance.host == node  # type: ignore[attr-defined]


@pytest.mark.parametrize("where", ["argument", "use", "environment"])
@pytest.mark.parametrize("function", [fdtd_simulation, elastic_fdtd_simulation])
def test_a_node_that_fails_falls_back_to_one_engine_on_numpy_here(
    function: Callable[..., object],
    where: _Where,
    node: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FAKE_SSH_MODE", "refuse")
    run = _run_for(function)
    built = _engines_built(monkeypatch)
    with (
        _asked(where, Compute(host=node, fallback=True), monkeypatch) as compute,
        pytest.warns(ComputeFallbackWarning, match="running on NumPy here instead"),
    ):
        here = function(run, compute=compute)
    assert built == [Compute()]
    assert here.provenance.host is None  # type: ignore[attr-defined]


# What is refused here, before ssh starts.


@pytest.mark.parametrize("host", ["here", "elsewhere"])
def test_a_waveform_that_cannot_travel_is_refused_before_ssh_starts(
    node: str, host: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # "elsewhere" is in no hosts file: the run is refused before the file is read.
    log = tmp_path / "ssh.log"
    monkeypatch.setenv("FAKE_SSH_LOG", str(log))
    run = _elastic(sources=[ExplosionSource(ix=6, iy=6, waveform=lambda t: 0.0 * t)])
    request = Compute(host=host)
    with pytest.raises(
        TypeError, match=r"run\.sources\[0\]\.waveform cannot travel to a node"
    ):
        elastic_fdtd_simulation(run, compute=request)
    assert not log.exists()


def test_a_run_of_the_other_engine_is_refused_here_before_ssh_starts(
    node: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # A bad argument cannot reach this far: the run refused it when it was
    # built. What is left to refuse here is a run of the other engine.
    log = tmp_path / "ssh.log"
    monkeypatch.setenv("FAKE_SSH_LOG", str(log))
    run = _elastic()
    request = Compute(host=node)
    with pytest.raises(TypeError, match="'run' must be an FDTDRun, got ElasticRun"):
        fdtd_simulation(run, compute=request)  # type: ignore[arg-type]
    assert not log.exists()


def test_an_unknown_node_is_a_missing_key(node: str) -> None:
    run, request = _small(), Compute(host="elsewhere")
    with pytest.raises(KeyError, match="no host 'elsewhere'"):
        fdtd_simulation(run, compute=request)


# What the connection or the node can do wrong.


def test_a_login_banner_on_standard_output_is_named(
    node: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FAKE_SSH_MODE", "banner")
    run, request = _small(), Compute(host=node)
    with pytest.raises(ComputeRemoteError, match="b'Welcome .*a login script"):
        fdtd_simulation(run, compute=request)


@pytest.mark.parametrize(
    ("mode", "match"),
    [
        ("refuse", "ssh could not connect or log in.*refused the ssh key"),
        ("garbage", "does not start a frame"),
    ],
)
def test_a_broken_connection_is_a_remote_error_that_says_why(
    node: str, monkeypatch: pytest.MonkeyPatch, mode: str, match: str
) -> None:
    monkeypatch.setenv("FAKE_SSH_MODE", mode)
    run, request = _small(), Compute(host=node)
    with pytest.raises(ComputeRemoteError, match=match):
        fdtd_simulation(run, compute=request)


def test_a_node_that_never_answers_is_stopped_at_the_timeout(
    node: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FAKE_SSH_MODE", "hang")
    run, request = _small(), Compute(host=node, timeout_s=2.0)
    started = time.monotonic()
    with pytest.raises(ComputeRemoteError, match="did not finish within 2 s"):
        fdtd_simulation(run, compute=request)
    assert time.monotonic() - started < 30.0


def test_a_run_still_going_at_the_timeout_is_stopped_there_and_the_node_with_it(
    node: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The timeout ends the conversation, not only ssh: the client stops waiting, and the node stops.

    Killing ssh closes the pipes the client reads, and the node's input
    with them, as a connection that goes down does.
    """
    pidfile = tmp_path / "node.pid"
    monkeypatch.setenv("FAKE_SSH_PIDFILE", str(pidfile))
    # Thirty seconds of sound on a 200 by 200 grid take hours on any runner;
    # on the 20 by 20 grid of the other tests a fast macOS runner finished
    # them inside the limit. The limit is well past the node's start, 2 to
    # 4.6 s on the Windows runners and 31 s once, so the clock runs out on a
    # run that has begun, and the test holds the watcher to a client gone in
    # the middle of the job.
    run = FDTDRun(
        c=343.0,
        dx=0.01,
        duration_s=30.0,
        shape=(200, 200),
        sources=[GaussianPulse(ix=100, iy=100, half_width_s=4e-5)],
        recording=FDTDRecording(probes=[(50, 50)]),
    )
    request = Compute(host=node, timeout_s=45.0)
    started = time.monotonic()
    with pytest.raises(ComputeRemoteError, match="did not finish within 45 s"):
        fdtd_simulation(run, compute=request)
    elapsed = time.monotonic() - started
    assert elapsed < 90.0, f"the run came back {elapsed:.0f} s after it began"
    if os.name == "posix":
        assert _written(pidfile), "the stand-in for ssh never started the node"
        pid = int(pidfile.read_text(encoding="utf-8"))
        deadline = time.monotonic() + 30.0
        while _alive(pid) and time.monotonic() < deadline:
            time.sleep(0.1)
        assert not _alive(pid), "the node went on after its client was gone"


def test_a_package_that_arrives_changed_is_refused(
    node: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(bootstrap.CACHE_VAR, str(tmp_path / "fresh-cache"))
    real = package.installed_package()
    forged = package.Package(files=real.files, digest="0" * 64)
    monkeypatch.setattr(client, "installed_package", lambda: forged)
    run, request = _small(), Compute(host=node)
    with pytest.raises(
        ComputeRemoteError, match="hash to [0-9a-f]{64}, not to the digest 0{64}"
    ):
        fdtd_simulation(run, compute=request)
    assert not (tmp_path / "fresh-cache" / ("0" * 64)).exists()


def test_a_node_below_the_floors_is_refused_with_its_remedy(
    node: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(client, "FLOORS", MappingProxyType({"numpy": "999.0"}))
    run, request = _small(), Compute(host=node)
    with pytest.raises(
        ComputeRemoteError,
        match="older than the 999.0 phonometry needs; upgrade the Python environment",
    ):
        fdtd_simulation(run, compute=request)


def test_a_node_that_fails_falls_back_here_when_asked_and_says_so(
    node: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FAKE_SSH_MODE", "refuse")
    run, request = _small(), Compute(host=node, fallback=True)
    with pytest.warns(
        ComputeFallbackWarning, match="running on NumPy here instead"
    ) as caught:
        res = fdtd_simulation(run, compute=request)
    here = fdtd_simulation(run)
    _assert_same_result(res, here)
    assert (res.provenance.host, res.provenance.device) == (None, "cpu")
    assert caught[0].filename == __file__


def test_an_interrupt_stops_ssh_and_the_node(
    node: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pidfile = tmp_path / "node.pid"
    monkeypatch.setenv("FAKE_SSH_PIDFILE", str(pidfile))
    sessions: list[client.Session] = []

    def interrupted(session: client.Session, *rest: object) -> RunProvenance:
        sessions.append(session)
        # The stand-in writes the node's process id once it has started it,
        # on a machine that may be busy: the interrupt waits for a whole id,
        # so the node it stops is one the test can name.
        deadline = time.monotonic() + _PIDFILE_WAIT_S
        while not _written(pidfile):
            if time.monotonic() > deadline:
                pytest.fail(
                    f"the stand-in for ssh wrote no process id to {pidfile} "
                    f"within {_PIDFILE_WAIT_S:g} s"
                )
            time.sleep(0.05)
        raise KeyboardInterrupt

    monkeypatch.setattr(client, "_receive_result", interrupted)
    # A fallback never swallows an interrupt.
    run, request = _small(duration=30.0), Compute(host=node, fallback=True)
    with pytest.raises(KeyboardInterrupt):
        fdtd_simulation(run, compute=request)
    assert sessions[0]._process.poll() is not None, "ssh outlived the interrupt"
    if os.name == "posix":
        pid = int(pidfile.read_text(encoding="utf-8"))
        deadline = time.monotonic() + 30.0
        while _alive(pid) and time.monotonic() < deadline:
            time.sleep(0.1)
        assert not _alive(pid), "the node went on after its client was gone"


def test_pyodide_has_no_ssh_and_says_so(
    node: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A host no file names: Pyodide, which has no hosts file either, hears
    # about Pyodide, not about the file.
    run, request = _small(), Compute(host="elsewhere")
    monkeypatch.setattr(sys, "platform", "emscripten")
    with pytest.raises(ComputeRemoteError, match="Pyodide does not have"):
        fdtd_simulation(run, compute=request)


def test_no_ssh_client_is_a_remote_error(
    node: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(command, "_SSH_PROGRAM", None)
    monkeypatch.setenv("PATH", str(tmp_path))
    run, request = _small(), Compute(host=node)
    with pytest.raises(ComputeRemoteError, match="no ssh client on PATH"):
        fdtd_simulation(run, compute=request)


# What only a POSIX shell shows.


@pytest.mark.skipif(
    os.name == "nt",
    reason="a batch file on PATH cannot carry the remote command intact; Windows reaches the stand-in through the module's hook",
)
def test_the_client_finds_ssh_on_its_path(
    node: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    shim = tmp_path / "bin" / "ssh"
    shim.parent.mkdir()
    shim.write_text(
        f'#!/bin/sh\nexec "{sys.executable}" "{_FAKE_SSH}" "$@"\n', encoding="utf-8"
    )
    shim.chmod(0o755)
    monkeypatch.setattr(command, "_SSH_PROGRAM", None)
    monkeypatch.setenv("PATH", f"{shim.parent}{os.pathsep}{os.environ['PATH']}")
    run = _small()
    _assert_same_result(
        fdtd_simulation(run, compute=Compute(host=node)), fdtd_simulation(run)
    )


@pytest.mark.skipif(
    os.name == "nt",
    reason="the interpreter here is a shell script, which Windows does not run",
)
def test_an_interpreter_path_with_spaces_and_a_quote_reaches_the_node(
    node: str, tmp_path: Path
) -> None:
    odd = tmp_path / "my node's env" / "python"
    odd.parent.mkdir()
    odd.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n', encoding="utf-8")
    odd.chmod(0o755)
    hosts = Path(os.environ["PHONOMETRY_HOSTS_FILE"])
    hosts.write_text(
        hosts.read_text(encoding="utf-8").replace(
            json.dumps(sys.executable), json.dumps(str(odd))
        ),
        encoding="utf-8",
    )
    run = _small()
    _assert_same_result(
        fdtd_simulation(run, compute=Compute(host=node)), fdtd_simulation(run)
    )
