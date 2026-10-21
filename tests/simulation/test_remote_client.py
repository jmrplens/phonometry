#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The client side of a remote run: what it takes from a node, and what it refuses.

The node's answers here are canned bytes behind a stand-in for the ssh
process; ``test_remote_simulation.py`` runs the whole conversation through a
stand-in for ssh itself.
"""

from __future__ import annotations

import io
import logging
import re
import sys
import threading
import types
import warnings
from typing import TYPE_CHECKING

import numpy as np
import pytest

from phonometry.simulation import Compute, ComputeFallbackWarning, ComputeRemoteError
from phonometry.simulation._remote import bootstrap, client
from phonometry.simulation._remote.hosts import HostEntry

if TYPE_CHECKING:
    from pathlib import Path

    from phonometry.simulation import RunProvenance

_DOCKER = HostEntry(
    name="nas",
    ssh="root@192.168.0.40",
    runner="docker",
    target="phonometry-node:gpu",
    label="the NAS",
    timeout_s=None,
)
_PYTHON = HostEntry(
    name="lab",
    ssh="lab",
    runner="python",
    target="/opt/my node's env/bin/python",
    label="the lab",
    timeout_s=None,
)
_RUN: dict[str, object] = {
    "host": None,
    "device": "cpu",
    "device_index": 0,
    "dtype": "float64",
    "numpy_version": np.__version__,
    "array_library": None,
    "cuda_runtime": None,
    "cuda_driver_api": None,
    "gpu": None,
    "package_digest": None,
}
_PRESSURES: dict[str, object] = {
    "name": "pressures",
    "dtype": "float64",
    "shape": [2, 5],
}
_EXPECTED = client.Expected(arrays=(client.ArraySpec("pressures", "float64", (2, 5)),))
_STREAMED = client.Expected(
    arrays=(client.ArraySpec("pressures", "float64", (2, 5)),),
    stream=client.StreamSpec("video", max_bytes=16),
)
#: An OSC 52 sequence, which some terminals take as a write to the clipboard.
_ESCAPE = "\x1b]52;c;ZXZpbA==\x07"
#: The longest a test waits on a thread of the session [s].
_WAIT_S = 5.0


# A session, its node's answers canned.


class _FakeSsh:
    """Stands in for the ssh process: what the node answers is canned bytes."""

    def __init__(
        self, stdout: bytes = b"", stderr: bytes = b"", returncode: int | None = 0
    ) -> None:
        self.stdin = io.BytesIO()
        self.stdout = io.BytesIO(stdout)
        self.stderr = io.BytesIO(stderr)
        self.returncode = returncode
        self.stopped = threading.Event()

    @property
    def killed(self) -> bool:
        return self.stopped.is_set()

    def poll(self) -> int | None:
        return self.returncode

    def wait(self, timeout: float | None = None) -> int | None:
        return self.returncode

    def kill(self) -> None:
        self.stopped.set()


def _session(
    stdout: bytes = b"",
    stderr: bytes = b"",
    returncode: int | None = 0,
    entry: HostEntry = _DOCKER,
) -> client.Session:
    return client.Session(_FakeSsh(stdout, stderr, returncode), entry, None)  # type: ignore[arg-type]


def _frame(header: dict[str, object], *buffers: bytes) -> bytes:
    out = io.BytesIO()
    bootstrap.write_frame(out, header, [memoryview(b) for b in buffers])
    return out.getvalue()


def test_bytes_that_are_no_frame_point_at_a_login_script() -> None:
    session = _session(stdout=b"Welcome to the node\n")
    with pytest.raises(
        ComputeRemoteError, match="does not start a frame.*login script"
    ):
        session.receive()


def test_ssh_that_cannot_log_in_says_so_with_the_node_s_words() -> None:
    session = _session(
        stderr=b"root@192.168.0.40: Permission denied (publickey).\n", returncode=255
    )
    with pytest.raises(
        ComputeRemoteError, match="ssh could not connect or log in.*refused the ssh key"
    ) as caught:
        session.receive()
    assert any("Permission denied" in note for note in caught.value.__notes__)


def test_a_node_without_the_image_asks_for_make_node_image() -> None:
    session = _session(
        stderr=b"docker: Error response from daemon: No such image: phonometry-node:gpu\n",
        returncode=125,
    )
    with pytest.raises(
        ComputeRemoteError, match="build it there with make node-image HOST=nas"
    ):
        session.receive()


@pytest.mark.parametrize(
    "words",
    [
        # Docker before 28 and after: the hint reads both, whatever the case.
        b"Got permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock\n",
        b"permission denied while trying to connect to the docker API at unix:///var/run/docker.sock\n",
    ],
)
def test_a_node_user_outside_the_docker_group_is_told_how_to_join_it(
    words: bytes,
) -> None:
    session = _session(stderr=words, returncode=1)
    with pytest.raises(ComputeRemoteError, match="add it to the docker group there"):
        session.receive()


@pytest.mark.parametrize(
    ("entry", "remedy"),
    [
        (_DOCKER, "rebuild the node image: make node-image HOST=nas"),
        (
            _PYTHON,
            "upgrade the Python environment of /opt/my node's env/bin/python on the node",
        ),
    ],
)
def test_a_node_below_its_floors_says_how_to_lift_them(
    entry: HostEntry, remedy: str
) -> None:
    error = _frame(
        {
            "type": "error",
            "stage": "floors",
            "message": "the node's numpy 1.26.4 is older than the 2.0.2 phonometry needs",
            "traceback": "",
        }
    )
    session = _session(stdout=error, returncode=2, entry=entry)
    with pytest.raises(ComputeRemoteError, match=re.escape(remedy)):
        session.receive()


def test_a_run_that_raised_on_the_node_carries_its_traceback() -> None:
    error = _frame(
        {
            "type": "error",
            "stage": "job",
            "message": "ComputeDeviceError: device 'cupy' index 1 is not present",
            "traceback": "Traceback (most recent call last):\nComputeDeviceError: device",
        }
    )
    session = _session(stdout=error, returncode=1)
    with pytest.raises(ComputeRemoteError, match="index 1 is not present") as caught:
        session.receive()
    assert caught.value.host == "nas"
    assert caught.value.node_traceback is not None


def test_a_session_past_its_timeout_says_so() -> None:
    process = _FakeSsh(returncode=None)
    session = client.Session(process, _DOCKER, 0.01)  # type: ignore[arg-type]
    assert process.stopped.wait(_WAIT_S), (
        f"the timeout did not stop ssh within {_WAIT_S} s"
    )
    with pytest.raises(ComputeRemoteError, match="did not finish within 0.01 s"):
        session.receive()
    assert process.killed
    session.close()


def test_progress_lines_go_to_the_log_and_the_rest_to_the_tail(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger="phonometry.simulation")
    session = _session(stderr=b"phonometry-progress 3 10\nsome note\n")
    session.close()
    assert (
        "phonometry.simulation",
        logging.INFO,
        "the NAS: step 3 of 10",
    ) in caplog.record_tuples
    assert (
        "phonometry.simulation",
        logging.DEBUG,
        "the NAS: some note",
    ) in caplog.record_tuples
    tail = "\n".join(session.failure("the stream ended").__notes__)
    assert "some note" in tail
    assert "phonometry-progress" not in tail


def test_a_progress_line_of_other_digits_is_a_line_like_any_other(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # "²" is a digit to str.isdigit and no number to int: the reader of the
    # node's standard error must not stop on it, or ssh blocks on a full pipe.
    caplog.set_level(logging.DEBUG, logger="phonometry.simulation")
    session = _session(
        stderr="phonometry-progress ² 10\nphonometry-progress 4 10\n".encode()
    )
    session.close()
    assert (
        "phonometry.simulation",
        logging.DEBUG,
        "the NAS: phonometry-progress ² 10",
    ) in caplog.record_tuples
    assert (
        "phonometry.simulation",
        logging.INFO,
        "the NAS: step 4 of 10",
    ) in caplog.record_tuples


# Text from a node reaches the caller's terminal, log and warnings escaped.


def _no_control(texts: list[str]) -> bool:
    return not any(character in text for text in texts for character in "\x1b\x07\r")


def test_control_characters_from_a_node_reach_the_caller_escaped(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger="phonometry.simulation")
    error = _frame(
        {
            "type": "error",
            "stage": "job",
            "message": f"ValueError: {_ESCAPE}",
            "traceback": f"Traceback\r{_ESCAPE}",
        }
    )
    session = _session(
        stdout=error, stderr=f"a line {_ESCAPE}\n".encode(), returncode=1
    )
    with pytest.raises(ComputeRemoteError) as caught:
        session.receive()
    assert _no_control(
        [str(caught.value), caught.value.node_traceback or "", *caught.value.__notes__]
    )
    assert "\\x1b]52" in str(caught.value)
    session.close()
    tail = session.failure("the stream ended")
    assert _no_control(
        [
            str(tail),
            *tail.__notes__,
            *(record.getMessage() for record in caplog.records),
        ]
    )
    assert any("\\x1b]52" in note for note in tail.__notes__)


# What a result must be before a byte of it is read.


def _result(
    arrays: list[object] | None = None,
    buffers: list[bytes] | None = None,
    provenance: dict[str, object] | None = None,
    caught: list[dict[str, str]] | None = None,
) -> bytes:
    header = {
        "type": "result",
        "provenance": _RUN if provenance is None else provenance,
        "warnings": caught or [],
        "arrays": [_PRESSURES] if arrays is None else arrays,
    }
    data = [np.arange(10.0).astype("<f8").tobytes()] if buffers is None else buffers
    return _frame(header, *data)


def _receive(
    stdout: bytes,
    first: np.ndarray | None = None,
    expected: client.Expected = _EXPECTED,
    sink: io.BytesIO | None = None,
) -> RunProvenance:
    target = np.empty((2, 5)) if first is None else first
    session = _session(stdout=stdout)
    return client._receive_result(
        session, Compute(host="nas"), "a" * 64, expected, target, None, sink
    )


def test_a_result_is_read_row_by_row_into_the_array_the_caller_made() -> None:
    target = np.empty((2, 5))
    provenance = _receive(_result(), first=target)
    assert np.array_equal(target, np.arange(10.0).reshape(2, 5))
    assert (provenance.host, provenance.package_digest) == ("nas", "a" * 64)


@pytest.mark.parametrize(
    ("arrays", "buffers", "match"),
    [
        (
            [{"name": "pressures", "dtype": "complex128", "shape": [2, 5]}],
            [b"\0" * 160],
            "'complex128', which the client does not take",
        ),
        (
            [{"name": "pressures", "dtype": "float64", "shape": [2, 6]}],
            [b"\0" * 96],
            r"the request implies float64 \[2, 5\]",
        ),
        (
            [_PRESSURES, {"name": "snapshots", "dtype": "float64", "shape": [1]}],
            [b"\0" * 80, b"\0" * 8],
            r"described \['pressures', 'snapshots'\] where the request implies \['pressures'\]",
        ),
        ([_PRESSURES], [b"\0" * 81], r"announced buffers of \[81\] bytes"),
        ([], [], r"described \[\] where the request implies \['pressures'\]"),
        (["pressures"], [b"\0" * 80], "'name' of a frame"),
    ],
)
def test_a_result_that_is_not_what_the_request_implies_is_refused_before_it_is_read(
    arrays: list[object], buffers: list[bytes], match: str
) -> None:
    stdout = _result(arrays=arrays, buffers=buffers)
    with pytest.raises(ComputeRemoteError, match=match):
        _receive(stdout)


@pytest.mark.parametrize(
    ("change", "match"),
    [
        (
            {"device": "cupy"},
            "reports a run on cupy in float64; the request was cpu in float64",
        ),
        ({"extra": 1}, "provenance holds"),
        ({"device_index": -1}, "not one a run could write"),
        (
            {"package_digest": "b" * 64},
            "names a host or a package, which only the client sets",
        ),
        (
            {"host": "elsewhere"},
            "names a host or a package, which only the client sets",
        ),
        ({"gpu": f"RTX {_ESCAPE}"}, "holds control characters"),
    ],
)
def test_a_provenance_no_run_on_the_node_could_write_is_refused(
    change: dict[str, object], match: str
) -> None:
    stdout = _result(provenance={**_RUN, **change})
    with pytest.raises(ComputeRemoteError, match=match):
        _receive(stdout)


# A stream of bytes after the arrays: capped, checked, written as it comes.


def _streamed(described: dict[str, object], data: bytes) -> bytes:
    return _result(
        arrays=[_PRESSURES, described],
        buffers=[np.arange(10.0).astype("<f8").tobytes(), data],
    )


def test_a_stream_within_its_cap_is_written_into_the_sink() -> None:
    sink = io.BytesIO()
    _receive(
        _streamed({"name": "video", "dtype": "uint8", "shape": [5]}, b"bytes"),
        expected=_STREAMED,
        sink=sink,
    )
    assert sink.getvalue() == b"bytes"


@pytest.mark.parametrize(
    ("described", "data", "match"),
    [
        (
            {"name": "video", "dtype": "uint8", "shape": [17]},
            b"x" * 17,
            "17 bytes of 'video', more than the 16",
        ),
        (
            {"name": "video", "dtype": "float64", "shape": [2]},
            b"x" * 16,
            "a stream of bytes",
        ),
        (
            {"name": "video", "dtype": "uint8", "shape": [4, 4]},
            b"x" * 16,
            "a stream of bytes",
        ),
        (
            {"name": "audio", "dtype": "uint8", "shape": [4]},
            b"x" * 4,
            "a stream of bytes",
        ),
    ],
)
def test_a_stream_that_is_not_what_the_request_allows_is_refused_before_the_sink_gets_a_byte(
    described: dict[str, object], data: bytes, match: str
) -> None:
    sink = io.BytesIO()
    stdout = _streamed(described, data)
    with pytest.raises(ComputeRemoteError, match=match):
        _receive(stdout, expected=_STREAMED, sink=sink)
    assert sink.getvalue() == b""


def test_a_stream_the_request_did_not_ask_for_is_refused() -> None:
    stdout = _streamed({"name": "video", "dtype": "uint8", "shape": [5]}, b"bytes")
    with pytest.raises(ComputeRemoteError, match=r"described \['pressures', 'video'\]"):
        _receive(stdout)


# What is refused before the hosts file is read.


def test_an_argument_that_cannot_travel_is_refused_before_the_hosts_file_is_read(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("PHONOMETRY_HOSTS_FILE", str(tmp_path / "absent.toml"))
    arguments = {"waveform": lambda t: 0.0 * t}  # and the host is in no file at all
    request = Compute(host="elsewhere")
    with pytest.raises(TypeError, match="waveform cannot travel to a node"):
        client.run_remote(
            "fdtd_simulation", request, arguments, _EXPECTED, np.empty((2, 5)), None
        )


def test_pyodide_is_refused_before_the_hosts_file_is_read(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("PHONOMETRY_HOSTS_FILE", str(tmp_path / "absent.toml"))
    monkeypatch.setattr(sys, "platform", "emscripten")
    request = Compute(host="elsewhere")
    with pytest.raises(ComputeRemoteError, match="Pyodide does not have"):
        client.run_remote(
            "fdtd_simulation", request, {}, _EXPECTED, np.empty((2, 5)), None
        )


def _lab(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A hosts file that names a Python node, and no session to open."""
    hosts = tmp_path / "hosts.toml"
    hosts.write_text(
        '[hosts.lab]\nssh = "lab"\nrunner = "python"\npython = "/usr/bin/python3"\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("PHONOMETRY_HOSTS_FILE", str(hosts))
    monkeypatch.setattr(
        client, "open_session", None
    )  # reaching it would be an error of its own


def test_a_package_no_node_would_take_is_a_remote_failure_before_ssh_starts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _lab(monkeypatch, tmp_path)

    def unshippable() -> object:
        msg = "'phonometry/draft copy.py' cannot travel to a node"
        raise ValueError(msg)

    monkeypatch.setattr(client, "installed_package", unshippable)
    request = Compute(host="lab")
    with pytest.raises(ComputeRemoteError, match="draft copy.py"):
        client.run_remote(
            "fdtd_simulation", request, {}, _EXPECTED, np.empty((2, 5)), None
        )


def test_a_package_not_on_disk_falls_back_here_when_asked(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # A phonometry imported from a zip or a frozen bundle has no files to send.
    _lab(monkeypatch, tmp_path)

    def zipped() -> object:
        msg = "/srv/app.zip/phonometry/__init__.py does not exist: /srv/app.zip/phonometry is not a package"
        raise FileNotFoundError(msg)

    monkeypatch.setattr(client, "installed_package", zipped)
    request = Compute(host="lab", fallback=True)
    with pytest.warns(
        ComputeFallbackWarning,
        match="app.zip/phonometry is not a package.*running on NumPy here instead",
    ):
        provenance = client.run_remote(
            "fdtd_simulation", request, {}, _EXPECTED, np.empty((2, 5)), None
        )
    assert provenance is None


def test_the_node_s_warnings_are_raised_here_with_their_class_at_the_caller_s_line() -> (
    None
):
    caught = [
        {
            "category": "phonometry.simulation.compute:ComputeFallbackWarning",
            "message": "from the node",
        },
        {"category": "builtins:RuntimeWarning", "message": "overflow"},
        {"category": "some.module.nobody.imported:Odd", "message": "strange"},
    ]
    stdout = _result(caught=caught)
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        _receive(stdout)
    assert [(w.category, str(w.message)) for w in record] == [
        (ComputeFallbackWarning, "from the node"),
        (RuntimeWarning, "overflow"),
        (RuntimeWarning, "some.module.nobody.imported:Odd: strange"),
    ]
    assert {w.filename for w in record} == {__file__}


def test_a_node_s_warning_class_is_looked_up_without_running_a_module_hook(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A lazy loader's __getattr__ imports what it is asked for: the node's
    # words must not reach it.
    asked: list[str] = []
    lazy = types.ModuleType("a_library_with_a_lazy_loader")

    def load(name: str) -> object:
        asked.append(name)
        return RuntimeWarning

    lazy.__getattr__ = load  # type: ignore[method-assign]
    monkeypatch.setitem(sys.modules, lazy.__name__, lazy)
    stdout = _result(
        caught=[{"category": f"{lazy.__name__}:submodule.Odd", "message": "strange"}]
    )
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        _receive(stdout)
    assert asked == []
    assert [(w.category, str(w.message)) for w in record] == [
        (RuntimeWarning, f"{lazy.__name__}:submodule.Odd: strange")
    ]


def test_a_node_s_warning_reaches_the_caller_escaped() -> None:
    stdout = _result(
        caught=[
            {"category": "builtins:RuntimeWarning", "message": f"overflow {_ESCAPE}"}
        ]
    )
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        _receive(stdout)
    assert _no_control([str(w.message) for w in record])
