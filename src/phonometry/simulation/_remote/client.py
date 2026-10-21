#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A simulation run on a node over SSH (private).

:func:`run_remote` is the remote route of
:func:`~phonometry.simulation.fdtd_simulation` and
:func:`~phonometry.simulation.elastic_fdtd_simulation`. Everything that can
refuse the call does so before a connection opens: the hosts file names the
node, the arguments become data, the package is read from disk. Then one
``ssh`` process carries the conversation :mod:`.bootstrap` defines.

The client does not trust the bytes a node sends. Every header field is
checked for its type, and every array against the name, the dtype and the
shape the request implies, before a byte of it is read; the arrays are read
one row at a time into host arrays the caller allocated, and a stream after
them (a video) is checked against its cap and written to the caller's sink a
chunk at a time. Text the node sends reaches the caller's terminal, log and
warnings with its control characters escaped (:func:`_printable`). A
failure of the transport or of the node is a :class:`ComputeRemoteError`
carrying the node's traceback and the end of its standard error; with
``fallback=True`` it is a :class:`ComputeFallbackWarning` instead, and the
caller runs here on NumPy. Progress goes to the ``phonometry.simulation``
logger, which says nothing unless the caller configures it.
"""

from __future__ import annotations

import contextlib
import dataclasses
import importlib
import inspect
import logging
import math
import re
import subprocess  # nosec B404 - ssh is the transport: a remote run is ssh without a server
import sys
import threading
import warnings
from collections import deque
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from types import MappingProxyType
from typing import IO, TYPE_CHECKING, Any, Literal, cast

import numpy as np

from .._backends import _PACKAGE_PREFIX
from ..compute import ComputeFallbackWarning, ComputeRemoteError, RunProvenance
from . import bootstrap, command, hosts, wire
from .package import FLOORS, PYTHON_FLOOR, installed_package

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, Sequence

    from _typeshed import SupportsWrite
    from numpy.typing import NDArray

    from ..compute import Compute
    from .hosts import HostEntry
    from .package import Package

_LOG = logging.getLogger("phonometry.simulation")

#: The library functions that run on a node.
RemoteFunction = Literal["fdtd_simulation", "elastic_fdtd_simulation"]

#: The dtypes a node may send, with their size in bytes. ``uint8`` is the
#: dtype of a stream (:class:`StreamSpec`).
_ITEM_BYTES: Mapping[str, int] = MappingProxyType(
    {"float32": 4, "float64": 8, "int64": 8, "bool": 1, "uint8": 1}
)
#: The exit status of ssh that could not connect or log in.
_SSH_FAILED = 255
#: The standard-error lines a failure quotes, and the longest kept.
_TAIL_LINES = 40
_LINE_CHARS = 4096
#: The longest message and traceback taken from a node [characters]: as long
#: as an error frame carries them.
_MESSAGE_CHARS = bootstrap._MAX_MESSAGE
_TRACE_CHARS = bootstrap._MAX_TRACE
#: The most characters of what a node sent that a message quotes: a value's
#: ``repr``, which escapes it, or a text already escaped (a class path, the
#: refusal of a record built from the node's fields).
_QUOTE_CHARS = 80
_TEXT_CHARS = 200
#: How long the client waits for ssh to end once the conversation is over [s].
_EXIT_WAIT_S = 10.0
#: The most a stream's chunk holds on its way to the sink [bytes]: the chunk a
#: node copies it in.
_STREAM_CHUNK = bootstrap._CHUNK
#: C0 and C1 control characters, the newline and the tab apart: what a
#: terminal could take as an escape sequence.
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")
#: A node's progress line: the prefix, the steps done, the steps in the run.
#: ASCII digits only: ``str.isdigit`` takes a ``"²"`` that ``int`` refuses.
_PROGRESS_LINE = re.compile(
    rf"{re.escape(bootstrap.PROGRESS)}\s+([0-9]{{1,18}})\s+([0-9]{{1,18}})"
)
#: What to do about a node without docker, or without its interpreter: each
#: told by two wordings of its shell.
_NO_DOCKER = (
    "the node has no docker command: install Docker there, or name a Python "
    'environment with runner = "python"'
)
_NO_INTERPRETER = "the interpreter {target} is not on the node"
#: What a node's standard error says (matched without regard to case), for
#: which runner (``None`` for both), and what to do about it.
_HINTS: tuple[tuple[str, str | None, str], ...] = (
    (
        "No such image",
        "docker",
        "the node has no image {target}: build it there with make node-image HOST={name}",
    ),
    (
        "could not select device driver",
        "docker",
        "Docker on the node cannot reach the GPU: install the NVIDIA Container Toolkit there",
    ),
    (
        "permission denied while trying to connect to the docker",
        "docker",
        "the node's user cannot use Docker: add it to the docker group there "
        "(sudo usermod -aG docker <user>), then log in again",
    ),
    ("docker: not found", "docker", _NO_DOCKER),
    ("docker: command not found", "docker", _NO_DOCKER),
    ("No such file or directory", "python", _NO_INTERPRETER),
    ("not found", "python", _NO_INTERPRETER),
    (
        "Permission denied (publickey",
        None,
        "the node refused the ssh key: add your public key to its ~/.ssh/authorized_keys",
    ),
    (
        "Host key verification failed",
        None,
        "ssh does not know the node's host key yet: connect once with ssh by hand to accept it",
    ),
)


def _printable(text: str) -> str:
    """*text* from a node, every control character but newline and tab written as an escape.

    A node's words reach the caller's terminal through an exception, a log
    line or a warning; a compromised node must not write escape sequences
    there (an OSC 52 write to the clipboard, a line erased or overwritten).
    """
    return _CONTROL.sub(lambda match: f"\\x{ord(match.group()):02x}", text)


def _quoted(value: object) -> str:
    """A value the node sent, as a message quotes it: its ``repr``, cut short.

    The ``repr`` escapes the control characters of every text in it, and
    the cut comes after: a list of a million names from a node is not a
    message of a million names.
    """
    return f"{value!r:.{_QUOTE_CHARS}}"


def _cut(text: str) -> str:
    """A text built from what the node sent, escaped and then cut short."""
    return _printable(text)[:_TEXT_CHARS]


@dataclass(frozen=True)
class ArraySpec:
    """An array the node must send: its record field, its dtype and its shape."""

    name: str
    dtype: str
    shape: tuple[int, ...]

    @property
    def nbytes(self) -> int:
        """The bytes the array takes."""
        return math.prod(self.shape) * _ITEM_BYTES[self.dtype]


@dataclass(frozen=True)
class StreamSpec:
    """A stream of bytes the node may send after the arrays: a 1-D ``uint8`` up to a cap.

    Its length is the node's to say, since the request cannot know it (the
    size of an encoded video), but never more than ``max_bytes``: a longer
    one is refused before a byte of it is read.
    """

    name: str
    max_bytes: int


@dataclass(frozen=True)
class Expected:
    """What the request implies the node sends, in the order it is sent.

    :ivar arrays: The record's arrays, each read into an array the caller
        allocated: the first into ``first``, the second into ``second``
        (:func:`run_remote`).
    :ivar stream: The stream after them, written into the caller's sink, or
        ``None`` when the request asks for none.
    """

    arrays: tuple[ArraySpec, ...]
    stream: StreamSpec | None = None


class Session:
    """One ssh process to one node, and the frames on its standard streams."""

    def __init__(
        self,
        process: subprocess.Popen[bytes],
        entry: HostEntry,
        timeout_s: float | None,
    ) -> None:
        if process.stdin is None or process.stdout is None or process.stderr is None:
            msg = "the ssh process needs its three standard streams as pipes"
            raise ValueError(msg)
        self.entry = entry
        self.timeout_s = timeout_s
        self._process = process
        self._stdin: IO[bytes] = process.stdin
        self._stdout: IO[bytes] = process.stdout
        self._stderr: IO[bytes] = process.stderr
        self._tail: deque[str] = deque(maxlen=_TAIL_LINES)
        self._expired = threading.Event()
        self._reader = threading.Thread(
            target=self._read_stderr, name=f"phonometry-ssh-{entry.name}", daemon=True
        )
        self._reader.start()
        self._timer: threading.Timer | None = None
        if timeout_s is not None:
            self._timer = threading.Timer(timeout_s, self._expire)
            self._timer.daemon = True
            self._timer.start()

    # -- the conversation ------------------------------------------------
    def send(
        self, header: Mapping[str, object], buffers: Sequence[memoryview] = ()
    ) -> None:
        """Send one frame; a node that stopped reading answers with its refusal, if it sent one."""
        try:
            bootstrap.write_frame(self._stdin, header, buffers)
        except OSError:
            raise self._closed_while_sending() from None

    def send_raw(self, data: bytes) -> None:
        """Send bytes that are not a frame: the inline bootstrap of a Python node."""
        try:
            self._stdin.write(data)
            self._stdin.flush()
        except OSError:
            raise self._closed_while_sending() from None

    def receive(self) -> dict[str, object]:
        """The next header from the node; an ``error`` frame is raised as the node's failure."""
        try:
            header = bootstrap.read_header(self._stdout)
        except bootstrap.FrameError as exc:
            raise self.failure(_with_framing_hint(str(exc))) from None
        if header["type"] == "error":
            raise self.node_error(header)
        return header

    def read_exact(self, size: int) -> bytes:
        """Exactly *size* bytes of a buffer the node announced."""
        try:
            return bootstrap.read_exact(self._stdout, size)
        except bootstrap.FrameError as exc:
            raise self.failure(str(exc)) from None

    def field[T](self, header: Mapping[str, object], key: str, kind: type[T]) -> T:
        """A field of what the node sent, of type *kind*, or the node's failure."""
        try:
            return bootstrap.field(header, key, kind)
        except bootstrap.FrameError as exc:
            msg = f"the node sent a malformed frame: {exc}"
            raise self.failure(msg) from None

    # -- what went wrong -------------------------------------------------
    def failure(self, what: str) -> ComputeRemoteError:
        """The error of a broken conversation, with what the node said on standard error.

        *what* may quote the node; it is shown escaped (:func:`_printable`),
        as the standard-error lines already are.
        """
        code = self._exit_code()
        self._reader.join(timeout=2.0)
        parts = [f"node {self.entry.name!r} ({self.entry.label}): {_printable(what)}"]
        if self._expired.is_set():
            parts.append(
                f"the run did not finish within {self.timeout_s:g} s and was stopped"
            )
        elif code == _SSH_FAILED:
            parts.append("ssh could not connect or log in (status 255)")
        elif code is not None:
            parts.append(f"the remote command ended with status {code}")
        hint = _hint("\n".join(self._tail), self.entry)
        if hint is not None:
            parts.append(hint)
        error = ComputeRemoteError("; ".join(parts), host=self.entry.name)
        if self._tail:
            error.add_note(
                f"Standard error of node {self.entry.name!r}:\n" + "\n".join(self._tail)
            )
        return error

    def node_error(self, header: Mapping[str, object]) -> ComputeRemoteError:
        """The error of a node that refused or failed, as its ``error`` frame says, escaped."""
        stage = _printable(self.field(header, "stage", str)[:_QUOTE_CHARS])
        message = _printable(self.field(header, "message", str)[:_MESSAGE_CHARS])
        trace = _printable(self.field(header, "traceback", str)[-_TRACE_CHARS:])
        remedy = _remedy(stage, self.entry)
        text = f"node {self.entry.name!r} ({self.entry.label}) stopped at {stage}: {message}"
        if remedy is not None:
            text = f"{text}; {remedy}"
        return ComputeRemoteError(
            text, host=self.entry.name, node_traceback=trace or None
        )

    def _closed_while_sending(self) -> ComputeRemoteError:
        """The node stopped reading: its own refusal when it sent one, else what its output was."""
        try:
            header = bootstrap.read_header(self._stdout)
        except bootstrap.FrameError as exc:
            what = f"the connection closed while the client was sending; {exc}"
            return self.failure(_with_framing_hint(what))
        if header.get("type") == "error":
            return self.node_error(header)
        return self.failure("the connection closed while the client was sending")

    def _exit_code(self) -> int | None:
        try:
            return self._process.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            return None

    # -- the process -----------------------------------------------------
    def kill(self) -> None:
        """Stop ssh now: the node's input ends, and its run stops at the next step."""
        if self._process.poll() is None:
            self._process.kill()

    def close(self) -> None:
        """End the session: close the node's input, wait for ssh, stop it if it lingers."""
        if self._timer is not None:
            self._timer.cancel()
        with contextlib.suppress(OSError):
            self._stdin.close()
        try:
            self._process.wait(timeout=_EXIT_WAIT_S)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait()
        self._reader.join(timeout=_EXIT_WAIT_S)
        with contextlib.suppress(OSError):
            self._stdout.close()
        # A reader still blocked on standard error (a process of the node
        # that holds it open) holds the file's lock: closing it would wait.
        if not self._reader.is_alive():
            with contextlib.suppress(OSError):
                self._stderr.close()

    def _expire(self) -> None:
        self._expired.set()
        self.kill()

    def _read_stderr(self) -> None:
        for raw in iter(partial(self._stderr.readline, _LINE_CHARS), b""):
            line = _printable(raw.decode("utf-8", "replace").rstrip("\r\n"))
            progress = _progress(line)
            if progress is None:
                self._tail.append(line)
                _LOG.debug("%s: %s", self.entry.label, line)
            else:
                _LOG.info("%s: step %d of %d", self.entry.label, *progress)


def _progress(line: str) -> tuple[int, int] | None:
    """``(done, total)`` from a node's progress line, or ``None`` for any other line."""
    match = _PROGRESS_LINE.fullmatch(line.strip())
    if match is None:
        return None
    return int(match[1]), int(match[2])


def _with_framing_hint(message: str) -> str:
    if "does not start a frame" not in message:
        return message
    return (
        f"{message}: something on the node wrote to standard output before "
        "phonometry did, most likely a login script (.bashrc, .profile) that "
        "prints; make it print nothing when the shell is not interactive"
    )


def _hint(stderr: str, entry: HostEntry) -> str | None:
    said = stderr.lower()
    for text, runner, hint in _HINTS:
        if text.lower() in said and runner in (None, entry.runner):
            return hint.format(target=entry.target, name=entry.name)
    return None


def _remedy(stage: str, entry: HostEntry) -> str | None:
    """What to do about a node that stopped at *stage*."""
    if stage in ("protocol", "floors") and entry.runner == "docker":
        return f"rebuild the node image: make node-image HOST={entry.name}"
    if stage == "floors":
        return f"upgrade the Python environment of {entry.target} on the node"
    return None


def _popen(argv: list[str]) -> subprocess.Popen[bytes]:
    """Start ssh in a process group of its own: an interrupt reaches this process, which stops ssh."""
    if sys.platform == "win32":
        return subprocess.Popen(  # nosec B603 - the library's own argv, the destination after "--"
            argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    return subprocess.Popen(  # nosec B603 - the library's own argv, the destination after "--"
        argv,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )


def _inline_bootstrap() -> bytes:
    """The bootstrap as a Python node's loader reads it: its length on a line, then the file."""
    source = Path(bootstrap.__file__).read_bytes()
    return b"%d\n" % len(source) + source


def _refuse_pyodide(host: str) -> None:
    """Pyodide has no ssh client and no processes: say so before anything else.

    :raises ComputeRemoteError: in Pyodide.
    """
    if sys.platform == "emscripten":
        msg = f"node {host!r}: a remote run needs an ssh client, which Pyodide does not have"
        raise ComputeRemoteError(msg, host=host)


@contextlib.contextmanager
def open_session(entry: HostEntry, request: Compute) -> Iterator[Session]:
    """One ssh process to *entry*, stopped on the way out whatever happened.

    :raises ComputeRemoteError: in Pyodide, without an ssh client, or when
        ssh does not start.
    """
    _refuse_pyodide(entry.name)
    try:
        argv = command.ssh_argv(entry, request)
    except FileNotFoundError:
        msg = f"node {entry.name!r}: no ssh client on PATH; install OpenSSH to run on a node"
        raise ComputeRemoteError(msg, host=entry.name) from None
    timeout_s = request.timeout_s if request.timeout_s is not None else entry.timeout_s
    try:
        process = _popen(argv)
    except OSError as exc:
        msg = f"node {entry.name!r}: ssh did not start: {exc}"
        raise ComputeRemoteError(msg, host=entry.name) from exc
    try:
        session = Session(process, entry, timeout_s)
    except BaseException:
        # An interrupt between the start of ssh and the session's, which
        # would stop it: stop it here.
        process.kill()
        with contextlib.suppress(subprocess.TimeoutExpired):
            process.wait(timeout=_EXIT_WAIT_S)
        raise
    try:
        if entry.runner == "python":
            session.send_raw(_inline_bootstrap())
        yield session
    except BaseException:
        # An interrupt in a notebook reaches this process, not ssh's: stop ssh here.
        session.kill()
        raise
    finally:
        session.close()


def _expect(session: Session, header: Mapping[str, object], kind: str) -> None:
    found = session.field(header, "type", str)
    if found != kind:
        msg = f"the node sent a {_quoted(found)} frame where a {kind!r} one belongs"
        raise session.failure(msg)


def _handshake(session: Session, package: Package) -> None:
    """Hello, the package when the node lacks it, and the node's word that it is ready."""
    session.send(
        {
            "type": "hello",
            "protocol": bootstrap.PROTOCOL,
            "digest": package.digest,
            "python_floor": PYTHON_FLOOR,
            "floors": dict(FLOORS),
        }
    )
    hello = session.receive()
    _expect(session, hello, "hello")
    if session.field(hello, "protocol", int) != bootstrap.PROTOCOL:
        msg = "the node answered in another protocol"
        raise session.failure(msg)
    if not session.field(hello, "have", bool):
        _LOG.info(
            "%s: sending the package %s (%.1f MB)",
            session.entry.label,
            package.digest[:12],
            package.size / 1e6,
        )
        session.send(
            {
                "type": "package",
                "digest": package.digest,
                "paths": [path for path, _ in package.files],
            },
            [memoryview(data) for _, data in package.files],
        )
        _expect(session, session.receive(), "stored")
    _expect(session, session.receive(), "ready")


def _checked_stream(
    session: Session, described: tuple[str, str, list[object]], spec: StreamSpec
) -> int:
    """The length of the stream the node described, once it is the one *spec* allows."""
    name, dtype, shape = described
    if (
        name != spec.name
        or dtype != "uint8"
        or len(shape) != 1
        or not bootstrap._is_count(shape[0])
    ):
        msg = (
            f"the node sent {_quoted(name)} as {_quoted(dtype)} {_quoted(shape)}; "
            f"the request implies {spec.name!r}, "
            "a stream of bytes (uint8, one axis)"
        )
        raise session.failure(msg)
    length = cast("int", shape[0])
    if length > spec.max_bytes:
        msg = f"the node sent {_quoted(length)} bytes of {_quoted(name)}, more than the {spec.max_bytes} the request allows"
        raise session.failure(msg)
    return length


def _checked_item(session: Session, item: object, spec: ArraySpec | StreamSpec) -> int:
    """The bytes of one array or stream the node described, once it is what *spec* says."""
    described = cast("Mapping[str, object]", item)
    name = session.field(described, "name", str)
    dtype = session.field(described, "dtype", str)
    shape = session.field(described, "shape", list)
    if dtype not in _ITEM_BYTES:
        msg = f"the node sent {_quoted(name)} as {_quoted(dtype)}, which the client does not take"
        raise session.failure(msg)
    if isinstance(spec, StreamSpec):
        return _checked_stream(session, (name, dtype, shape), spec)
    if (name, dtype, shape) != (spec.name, spec.dtype, list(spec.shape)):
        msg = f"the node sent {_quoted(name)} as {_quoted(dtype)} {_quoted(shape)}; the request implies {spec.dtype} {list(spec.shape)}"
        raise session.failure(msg)
    return spec.nbytes


def _check_arrays(
    session: Session, header: Mapping[str, object], expected: Expected
) -> list[int]:
    """The byte count of each buffer of the result, once each is what the request implies.

    Refused before a byte of any is read: another list of arrays than the
    request implies, an array of another name, dtype or shape, a stream
    longer than its cap, or buffers that do not hold what was described.
    """
    described = session.field(header, "arrays", list)
    wanted: list[ArraySpec | StreamSpec] = [*expected.arrays]
    if expected.stream is not None:
        wanted.append(expected.stream)
    if len(described) != len(wanted):
        named = [
            item.get("name") if isinstance(item, dict) else item for item in described
        ]
        msg = f"the node described {_quoted(named)} where the request implies {[spec.name for spec in wanted]!r}"
        raise session.failure(msg)
    sizes = [
        _checked_item(session, item, spec)
        for item, spec in zip(described, wanted, strict=True)
    ]
    announced = session.field(header, "buffers", list)
    if announced != sizes:
        msg = f"the node announced buffers of {_quoted(announced)} bytes; the arrays it described take {sizes}"
        raise session.failure(msg)
    return sizes


def _provenance(
    session: Session, header: Mapping[str, object], request: Compute, digest: str
) -> RunProvenance:
    """The node's provenance, checked, with this run's host, index and package."""
    fields = session.field(header, "provenance", dict)
    names = {f.name for f in dataclasses.fields(RunProvenance)}
    if set(fields) != names:
        msg = f"the node's provenance holds {_quoted(sorted(fields))}, not {sorted(names)}"
        raise session.failure(msg)
    if any(
        isinstance(value, str) and _CONTROL.search(value) for value in fields.values()
    ):
        # The record goes back to the caller, who prints it: no run writes these.
        msg = "the node's provenance holds control characters, which no run writes"
        raise session.failure(msg)
    try:
        ran = RunProvenance(**cast("dict[str, Any]", fields))
    except (TypeError, ValueError) as exc:
        msg = f"the node's provenance is not one a run could write: {_cut(str(exc))}"
        raise session.failure(msg) from None
    if ran.host is not None or ran.package_digest is not None:
        msg = "the node's provenance names a host or a package, which only the client sets"
        raise session.failure(msg)
    if (ran.device, ran.dtype) != (request.device, request.dtype):
        msg = f"the node reports a run on {ran.device} in {ran.dtype}; the request was {request.device} in {request.dtype}"
        raise session.failure(msg)
    return dataclasses.replace(
        ran, host=request.host, device_index=request.device_index, package_digest=digest
    )


def _warning_class(path: str) -> type[Warning] | None:
    """The class a node's warning names, if this process has it; never an import of the node's choosing.

    A module of phonometry is imported if it is not yet; any other is looked
    in only if this process imported it already. The class is looked up
    statically, so the node's words run no module ``__getattr__`` on the way
    (a lazy loader would import what they name).
    """
    module_name, _, qualname = path.partition(":")
    module: object
    if module_name == "phonometry" or module_name.startswith("phonometry."):
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            return None
    else:
        module = sys.modules.get(module_name)
    found: object = module
    for part in qualname.split("."):
        found = inspect.getattr_static(found, part, None)
    return found if isinstance(found, type) and issubclass(found, Warning) else None


def _built(category: type[Warning], message: str) -> Warning | None:
    """*category* built on *message*, or ``None`` when it is not built that way.

    A class of a library the caller imported may want more than a message
    (a keyword its ``__init__`` requires) or show another text than the one
    it was given (its own ``__str__``), and may raise for either. It is
    tried here, before a byte of the result is read, so that the run never
    stops on it with another error than a ComputeRemoteError.
    """
    try:
        warning = category(message)
        text = str(warning)
    # Whatever such a class raises, the node's words still reach the caller,
    # as a RuntimeWarning.
    except Exception:
        return None
    return warning if text == message else None


def _warnings_of(session: Session, header: Mapping[str, object]) -> list[Warning]:
    """The node's warnings, each built as it is raised here.

    In its own class when this process has it and the class takes the
    message as its text; otherwise a RuntimeWarning led by the class path.
    """
    caught: list[Warning] = []
    for item in session.field(header, "warnings", list)[: bootstrap._MAX_WARNINGS]:
        entry = cast("Mapping[str, object]", item)
        path = session.field(entry, "category", str)
        message = _printable(session.field(entry, "message", str)[:_MESSAGE_CHARS])
        category = _warning_class(path)
        warning = None if category is None else _built(category, message)
        if warning is None:
            warning = RuntimeWarning(f"{_cut(path)}: {message}")
        caught.append(warning)
    return caught


def _relay(caught: Sequence[Warning]) -> None:
    """Raise again here, at the caller's line, each warning the node raised."""
    for warning in caught:
        warnings.warn(warning, skip_file_prefixes=(_PACKAGE_PREFIX,))


def _fill(session: Session, spec: ArraySpec, target: NDArray[Any]) -> None:
    """Read the array *spec* describes into *target*, one row of its first axis at a time.

    So a large result is never on the host twice: one row's bytes, then the
    row in *target*.
    """
    row_shape = spec.shape[1:]
    row_bytes = math.prod(row_shape) * _ITEM_BYTES[spec.dtype]
    little = np.dtype(spec.dtype).newbyteorder("<")
    for row in range(spec.shape[0]):
        target[row] = np.frombuffer(
            session.read_exact(row_bytes), dtype=little
        ).reshape(row_shape)


def _drain(session: Session, length: int, sink: SupportsWrite[bytes]) -> None:
    """Copy the *length* bytes of the stream into *sink*, a chunk at a time."""
    remaining = length
    while remaining > 0:
        chunk = session.read_exact(min(remaining, _STREAM_CHUNK))
        sink.write(chunk)
        remaining -= len(chunk)


def _receive_result(
    session: Session,
    request: Compute,
    digest: str,
    expected: Expected,
    first: NDArray[Any],
    second: NDArray[Any] | None,
    sink: SupportsWrite[bytes] | None,
) -> RunProvenance:
    """Check the result frame, read its arrays and stream, relay its warnings.

    The first array goes into *first*, the second (if any) into *second*,
    the stream (if any) into *sink*; nothing is read before every field of
    the frame has been checked.
    """
    header = session.receive()
    _expect(session, header, "result")
    sizes = _check_arrays(session, header, expected)
    provenance = _provenance(session, header, request, digest)
    caught = _warnings_of(session, header)
    _fill(session, expected.arrays[0], first)
    if second is not None:
        _fill(session, expected.arrays[1], second)
    if sink is not None:
        _drain(session, sizes[-1], sink)
    _relay(caught)
    return provenance


def _check_targets(
    expected: Expected,
    second: NDArray[Any] | None,
    sink: SupportsWrite[bytes] | None,
) -> None:
    """Refuse a call whose arrays and sink do not match what it expects (a mistake of the caller's code).

    :raises ValueError: for one or two arrays expected and not as many
        given, or a stream expected without a sink or a sink without one.
    """
    if len(expected.arrays) != (1 if second is None else 2):
        msg = f"{len(expected.arrays)} arrays expected; run_remote reads one into first and one into second"
        raise ValueError(msg)
    if (expected.stream is None) != (sink is None):
        msg = "a stream is read into a sink: give both or neither"
        raise ValueError(msg)


def _package(host: str) -> Package:
    """The package to ship; one no node would take is this run's failure, said before ssh starts.

    So is one that cannot be read from disk (a phonometry imported from a
    zip or a frozen bundle has no files to send): a fallback then runs here.
    """
    try:
        return installed_package()
    except ValueError as exc:
        msg = f"node {host!r}: {exc}"
        raise ComputeRemoteError(msg, host=host) from None
    except OSError as exc:
        msg = f"node {host!r}: the package cannot be read from disk to send it: {exc}"
        raise ComputeRemoteError(msg, host=host) from None


def run_remote(
    function: RemoteFunction,
    request: Compute,
    arguments: Mapping[str, object],
    expected: Expected,
    first: NDArray[Any],
    second: NDArray[Any] | None,
    *,
    sink: SupportsWrite[bytes] | None = None,
) -> RunProvenance | None:
    """Run *function* on the node *request* names, filling *first*, *second* and *sink*.

    In this order, before anything connects: the arguments become data (an
    argument that cannot travel is the caller's ``TypeError``, whatever the
    host), Pyodide is refused, the hosts file names the node, the package is
    read from disk.

    :return: The run's provenance, its host and package digest set; ``None``
        when the run failed, ``request.fallback`` asks to run here instead,
        and the :class:`ComputeFallbackWarning` was raised.
    :raises KeyError: for a host the hosts file does not name.
    :raises ValueError: for a malformed hosts file, or arrays and a sink
        that do not match *expected*.
    :raises TypeError: for an argument that cannot travel.
    :raises ComputeRemoteError: for a failure of the transport or of the
        node, without ``fallback``.
    :warns ComputeFallbackWarning: for such a failure with ``fallback``.
    """
    _check_targets(expected, second, sink)
    tree, buffers = wire.encode_arguments(arguments)
    host = cast("str", request.host)
    try:
        _refuse_pyodide(host)
        entry = hosts.load_host(host)
        package = _package(host)
        placement = command.node_placement(entry, request)
        job = {
            "type": "job",
            "function": function,
            "compute": placement,
            "arguments": tree,
        }
        _LOG.info(
            "%s: running %s on %s in %s",
            entry.label,
            function,
            request.device,
            request.dtype,
        )
        with open_session(entry, request) as session:
            _handshake(session, package)
            session.send(job, buffers)
            provenance = _receive_result(
                session, request, package.digest, expected, first, second, sink
            )
    except ComputeRemoteError as exc:
        if not request.fallback:
            raise
        warnings.warn(
            f"{exc}; running on NumPy here instead (fallback=True)",
            ComputeFallbackWarning,
            skip_file_prefixes=(_PACKAGE_PREFIX,),
        )
        return None
    _LOG.info("%s: %s done", entry.label, function)
    return provenance
