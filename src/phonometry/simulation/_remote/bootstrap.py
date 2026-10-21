#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The first code a node runs: receive the package, check it, hand over (private).

This file is all a node needs before phonometry is there. It lives in the
node image (docker/node/Dockerfile copies it to :data:`IMAGE_PATH`), and the
client sends it inline to a node that runs Python directly. It imports
nothing from phonometry and parses as Python 3.8, so that an old node can
say it is too old instead of failing to read it. What it speaks, the framing
and the first messages, does not change between releases: a change to it is
a new :data:`PROTOCOL`, and a node whose bootstrap speaks another one is
refused with a request to rebuild its image.

A frame is :data:`MAGIC`, the length of its header as four big-endian
bytes, the header as a UTF-8 JSON object with a text ``type`` and a
``buffers`` list of byte counts, then those buffers. The conversation:

1. client: ``hello``, with the protocol, the package digest and the Python
   and dependency floors of the package;
2. node: ``hello``, saying whether its cache holds that digest;
3. client, only when it does not: ``package``, every file of the package as
   one buffer, in the sorted order of its path; node: ``stored``;
4. node: ``ready``, once the floors are met and the package imports from
   the cache; from then on the shipped package's ``node.serve`` holds the
   stream.

A refusal is an ``error`` frame. Standard output carries frames only: the
first thing the node does is keep a duplicate of descriptor 1 for them and
point descriptor 1 at standard error, so a ``print`` anywhere below lands
in the log and cannot cut into a frame.

The cache is shared by every client of the node. A run holds its package
with a shared lock from before it looks for it to the end of the process,
and a prune removes only what it can lock alone, so a long run keeps its
package however many others come and go; installing and pruning take the
cache's own lock, briefly. A package enters the cache and leaves it in one
rename each, so a node stopped at any moment leaves either a whole package
under its digest or none.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import platform
import re
import shutil
import struct
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import IO, TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, Sequence

T = TypeVar("T")

#: The version of the conversation. A node that speaks another is refused.
PROTOCOL = 1
#: The four bytes every frame starts with.
MAGIC = b"PNF1"
#: The longest header a frame may announce [bytes].
MAX_HEADER = 1 << 20
#: The largest package a node takes [bytes].
MAX_PACKAGE = 512 << 20
#: How many packages, by digest, a node keeps in its cache.
KEEP = 5
#: Where the node image keeps this file.
IMAGE_PATH = "/usr/local/share/phonometry-node/bootstrap.py"
#: The environment variable that names the node's cache (the Docker volume).
CACHE_VAR = "PHONOMETRY_NODE_CACHE"
#: How a progress line on the node's standard error starts.
PROGRESS = "phonometry-progress"
#: What comes before a frame's header: the magic and the header's length [bytes].
_START = len(MAGIC) + 4
#: The most a single read asks for [bytes].
_CHUNK = 1 << 22
#: The longest error message and traceback an error frame carries [characters].
_MAX_MESSAGE = 1 << 12
_MAX_TRACE = 1 << 16
#: How old a cut-off upload is before the cache clears it [s].
_STALE_UPLOAD_S = 86400.0
#: How recently a package was used for no prune to remove it [s], whatever
#: else the cache holds: the five used last are kept besides.
_PRUNE_MARGIN_S = 600.0
#: How the cache's working directories start: an upload not yet checked, and
#: a package on its way out. Neither is ever a digest.
_INCOMING = ".incoming-"
_REMOVING = ".removing-"

_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_PATH = re.compile(r"phonometry(?:/[A-Za-z0-9_.-]+)+\Z")
_RELEASE = re.compile(r"\d+(?:\.\d+)*")


class FrameError(Exception):
    """A stream that breaks the framing: no frame, a foreign one, or a cut one."""


class Refused(Exception):
    """What the node was sent cannot run; the message says why.

    :ivar stage: Where the conversation stopped: ``"hello"``, ``"protocol"``,
        ``"package"``, ``"floors"``, ``"import"`` or ``"job"``.
    """

    def __init__(self, message: str, *, stage: str) -> None:
        super().__init__(message)
        self.stage = stage


def write_header(stream: IO[bytes], header: Mapping[str, object]) -> None:
    """Write a frame's start and *header*, whose ``buffers`` the caller writes next."""
    text = json.dumps(dict(header), separators=(",", ":"), allow_nan=False)
    data = text.encode("utf-8")
    stream.write(MAGIC + struct.pack(">I", len(data)) + data)


def write_frame(
    stream: IO[bytes],
    header: Mapping[str, object],
    buffers: Sequence[bytes | bytearray | memoryview] = (),
) -> None:
    """Write one frame: *header* with the byte count of each buffer, then the buffers."""
    views = [memoryview(buffer) for buffer in buffers]
    payload = dict(header)
    payload["buffers"] = [view.nbytes for view in views]
    write_header(stream, payload)
    stream.writelines(views)
    stream.flush()


def _read_up_to(stream: IO[bytes], size: int) -> bytes:
    """*size* bytes of *stream*, fewer only when it ends first.

    A pipe read without a buffer may return part of what was asked while
    the rest is still on its way, so one read is never taken for the end.
    """
    parts = []
    remaining = size
    while remaining > 0:
        chunk = stream.read(min(remaining, _CHUNK))
        if not chunk:
            break
        parts.append(chunk)
        remaining -= len(chunk)
    return b"".join(parts)


def read_exact(stream: IO[bytes], size: int) -> bytes:
    """Exactly *size* bytes of *stream*.

    :raises TypeError: for a *size* that is not a whole number.
    :raises FrameError: when the stream ends first.
    """
    if not isinstance(size, int):
        msg = f"'size' is a whole number of bytes, not {size!r:.80}"
        raise TypeError(msg)
    data = _read_up_to(stream, size)
    if len(data) < size:
        msg = f"the stream ended {size - len(data)} bytes short of the {size} announced"
        raise FrameError(msg)
    return data


def read_header(stream: IO[bytes], max_header: int = MAX_HEADER) -> dict[str, object]:
    """The header of the next frame; its buffers are left on the stream.

    :raises FrameError: for no frame at all, bytes that do not start one, a
        header longer than *max_header*, a header nested deeper than the JSON
        reader goes, or a header that is not a JSON object with a text
        ``type`` and a ``buffers`` list of byte counts.
    :raises TypeError: for a *max_header* that is not a whole number.
    """
    if not isinstance(max_header, int):
        msg = f"'max_header' is a whole number of bytes, not {max_header!r:.80}"
        raise TypeError(msg)
    start = _read_up_to(stream, _START)
    if not start:
        msg = "the stream ended before a frame"
        raise FrameError(msg)
    if len(start) < _START or start[: len(MAGIC)] != MAGIC:
        msg = f"the stream does not start a frame: it starts {start!r}"
        raise FrameError(msg)
    (length,) = struct.unpack(">I", start[len(MAGIC) :])
    if length > max_header:
        msg = f"a frame announced a header of {length} bytes, more than the {max_header} allowed"
        raise FrameError(msg)
    text = read_exact(stream, length)
    try:
        header = json.loads(text.decode("utf-8"))
    # A UnicodeDecodeError is a ValueError too.
    except ValueError as exc:
        msg = f"a frame header is not JSON: {exc}"
        raise FrameError(msg) from None
    except RecursionError:
        # A megabyte of "[" fits the size limit and is still no header.
        msg = "a frame header is nested deeper than a header can be read"
        raise FrameError(msg) from None
    if not isinstance(header, dict):
        msg = f"a frame header is not an object: {header!r:.80}"
        raise FrameError(msg)
    field(header, "type", str)
    counts = field(header, "buffers", list)
    if not all(_is_count(count) for count in counts):
        msg = f"a frame announces buffers that are not byte counts: {counts!r:.80}"
        raise FrameError(msg)
    return header


def _is_count(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def field(header: Mapping[str, object], key: str, kind: type[T]) -> T:
    """The field *key* of a frame header, or of an object inside one, of type *kind*.

    :raises FrameError: when *header* is not an object (a node may send any
        JSON value where one is expected), or the field is missing or of
        another type; a ``bool`` is not taken for an ``int``.
    """
    value = header.get(key) if isinstance(header, dict) else None
    if (isinstance(value, bool) and kind is not bool) or not isinstance(value, kind):
        msg = f"{key!r} of a frame is {value!r:.80}, not a {kind.__name__}"
        raise FrameError(msg)
    return value


def send_error(stream: IO[bytes], stage: str, message: str, trace: str = "") -> None:
    """Tell the client why the node stops."""
    header = {
        "type": "error",
        "stage": stage,
        "message": message[:_MAX_MESSAGE],
        "traceback": trace[-_MAX_TRACE:],
    }
    # A client that is gone has no one left to tell.
    with contextlib.suppress(OSError):
        write_frame(stream, header)


class PackageDigest:
    """SHA-256 over a package's files, path by path, in sorted order.

    Each file adds the length of its path, the path in UTF-8, the length of
    its content and the content, each length as eight big-endian bytes, so
    that two different packages never feed the same bytes. The paths come
    sorted and once each: the digest names a set of files, not an order.
    """

    def __init__(self) -> None:
        self._sha = hashlib.sha256()
        self._last: str | None = None

    def add(self, path: str, data: bytes) -> None:
        """Add one file.

        :raises ValueError: for a path that does not come after the last one.
        """
        if self._last is not None and path <= self._last:
            msg = f"the package's files must come sorted and once each: {path!r} after {self._last!r}"
            raise ValueError(msg)
        self._last = path
        name = path.encode("utf-8")
        self._sha.update(struct.pack(">Q", len(name)))
        self._sha.update(name)
        self._sha.update(struct.pack(">Q", len(data)))
        self._sha.update(data)

    def hexdigest(self) -> str:
        """The digest, 64 lowercase hexadecimal digits."""
        return self._sha.hexdigest()


def is_safe_path(path: str) -> bool:
    """Whether *path* is a relative POSIX path inside the ``phonometry`` package."""
    return _PATH.match(path) is not None and not any(
        part in (".", "..") for part in path.split("/")
    )


def cache_dir() -> Path:
    """The node's package cache: the variable, else XDG's cache, else ``~/.cache``."""
    explicit = os.environ.get(CACHE_VAR, "").strip()
    if explicit:
        return Path(explicit)
    base = os.environ.get("XDG_CACHE_HOME", "").strip()
    root = Path(base) if base and Path(base).is_absolute() else Path.home() / ".cache"
    return root / "phonometry" / "remote"


def is_stored(directory: Path) -> bool:
    """Whether *directory* holds a whole package."""
    return (directory / "phonometry" / "__init__.py").is_file()


def _lock(handle: IO[bytes], *, exclusive: bool, wait: bool) -> bool:
    """Lock the file of *handle*; ``False`` when *wait* is off and another holds it.

    The lock lasts until the handle is closed or the process ends, whichever
    comes first, so a run that dies frees its package. A node is Linux or
    macOS; on Windows, where only the tests run this file, nothing is locked.
    """
    if sys.platform == "win32":
        return True
    import fcntl

    operation = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
    if not wait:
        operation |= fcntl.LOCK_NB
    try:
        fcntl.flock(handle.fileno(), operation)
    except BlockingIOError:
        return False
    return True


@contextlib.contextmanager
def _cache_lock(cache: Path) -> Iterator[None]:
    """Hold *cache* to this process while it installs or prunes; never for a run."""
    cache.mkdir(parents=True, exist_ok=True)
    with (cache / ".lock").open("ab") as handle:
        _lock(handle, exclusive=True, wait=True)
        yield


def hold(cache: Path, digest: str) -> IO[bytes]:
    """Hold the package *digest* until this process ends: no prune removes it.

    A shared lock on ``<digest>.lock``, taken before the node looks for the
    package and kept, through the handle returned, for the whole run. The
    file is opened under the cache's lock, the only place a digest's lock
    file is opened, so a prune never holds it alone at the same moment.
    """
    with _cache_lock(cache):
        handle = (cache / f"{digest}.lock").open("ab")
        _lock(handle, exclusive=False, wait=True)
    return handle


def _discard(cache: Path, entry: Path) -> None:
    """Take *entry* out of the cache in one rename, then delete it.

    Under the cache's lock. A deletion cut off halfway leaves a directory
    named for no digest, which the next prune clears, never a package with
    some of its files gone under a digest a run would take for whole.
    """
    removing = Path(tempfile.mkdtemp(prefix=_REMOVING, dir=cache))
    entry.rename(removing / entry.name)
    shutil.rmtree(removing, ignore_errors=True)


def install(incoming: Path, final: Path) -> None:
    """Move a package received whole into its place, in one rename.

    Under the cache's lock. Another client may have stored the same digest
    meanwhile; its copy is the same files, so it is taken as it is. Anything
    else in the way (a directory that is not a whole package, a file of its
    name) is no package a run can hold, and is replaced.
    """
    with _cache_lock(final.parent):
        if is_stored(final):
            return
        if final.exists() or final.is_symlink():
            _discard(final.parent, final)
        incoming.rename(final)


def _check_listing(paths: list[object], sizes: list[object]) -> None:
    """Refuse a package listing before a byte of it is written."""
    if not paths or len(paths) != len(sizes):
        msg = "the package must list each of its files with its size"
        raise Refused(msg, stage="package")
    total = sum(size for size in sizes if isinstance(size, int))
    if total > MAX_PACKAGE:
        msg = f"a package of {total} bytes is more than the {MAX_PACKAGE} a node takes"
        raise Refused(msg, stage="package")
    for path in paths:
        if not isinstance(path, str) or not is_safe_path(path):
            msg = f"the node refuses to write {path!r}: a package holds phonometry/... paths only"
            raise Refused(msg, stage="package")


def _write_files(
    stream: IO[bytes], incoming: Path, paths: list[str], sizes: list[int]
) -> str:
    """Write the files of a package under *incoming*; the digest of what came."""
    received = PackageDigest()
    # Of one length, which _check_listing saw; zip's strict= is Python 3.10.
    for path, size in zip(paths, sizes):
        data = read_exact(stream, size)
        try:
            received.add(path, data)
        except ValueError as exc:
            raise Refused(str(exc), stage="package") from None
        target = incoming.joinpath(*path.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return received.hexdigest()


def receive_package(stream: IO[bytes], cache: Path, digest: str) -> None:
    """Receive the package of *digest*, check it, and store it in *cache*.

    :raises Refused: for a frame that is not that package, a path outside
        it, files out of order, or files that hash to another digest; nothing
        is left in the cache then.
    """
    header = read_header(stream)
    if (
        field(header, "type", str) != "package"
        or field(header, "digest", str) != digest
    ):
        msg = f"expected the files of package {digest}"
        raise Refused(msg, stage="package")
    paths = field(header, "paths", list)
    sizes = field(header, "buffers", list)
    _check_listing(paths, sizes)
    cache.mkdir(parents=True, exist_ok=True)
    incoming = Path(tempfile.mkdtemp(prefix=_INCOMING, dir=cache))
    try:
        received = _write_files(stream, incoming, paths, sizes)
        if received != digest:
            msg = (
                f"the files received hash to {received}, not to the "
                f"digest {digest} they were sent under"
            )
            raise Refused(msg, stage="package")
        install(incoming, cache / digest)
    finally:
        shutil.rmtree(incoming, ignore_errors=True)


def _age(entry: Path, now: float) -> float:
    """How long ago *entry* last changed [s]; zero for one gone meanwhile."""
    try:
        return now - entry.stat().st_mtime
    except FileNotFoundError:
        return 0.0


def touch_and_prune(cache: Path, digest: str, keep: int = KEEP) -> None:
    """Mark *digest* as used, then prune what no run holds, and clear old uploads.

    Kept: the *keep* packages used last, *digest* itself, any used in the
    last :data:`_PRUNE_MARGIN_S` seconds, and any a run holds (:func:`hold`).
    Nothing is created here: a package another client pruned a moment ago is
    not touched back into an empty file of its name.
    """
    package = cache / digest
    if is_stored(package):
        # Pruned by another client between the two calls: nothing to mark.
        with contextlib.suppress(FileNotFoundError):
            os.utime(package)
    with _cache_lock(cache):
        stored = [
            entry
            for entry in cache.iterdir()
            if _DIGEST.match(entry.name) and entry.is_dir()
        ]
        stored.sort(key=lambda entry: entry.stat().st_mtime, reverse=True)
        now = time.time()
        for old in stored[keep:]:
            if old.name != digest and _age(old, now) > _PRUNE_MARGIN_S:
                _prune(cache, old)
        _clear_leftovers(cache, now)


def _prune(cache: Path, package: Path) -> None:
    """Remove *package* unless a run holds it; called under the cache's lock.

    Its lock file stays, an empty file, so that a run of the same digest
    later locks the same file a prune would.
    """
    with (cache / f"{package.name}.lock").open("ab") as handle:
        if _lock(handle, exclusive=True, wait=False):
            _discard(cache, package)


def _clear_leftovers(cache: Path, now: float) -> None:
    """Clear the uploads cut off a day ago and every deletion cut off; under the cache's lock."""
    for upload in cache.glob(_INCOMING + "*"):
        if _age(upload, now) > _STALE_UPLOAD_S:
            shutil.rmtree(upload, ignore_errors=True)
    # A deletion runs under the cache's lock from start to end, so one found
    # here was stopped halfway.
    for removing in cache.glob(_REMOVING + "*"):
        shutil.rmtree(removing, ignore_errors=True)


def _release(version: str) -> tuple[int, ...]:
    """The release numbers of a version, trailing zeros dropped.

    ``"2.0.2rc1"`` reads as ``(2, 0, 2)``, and ``"2.0"`` and ``"2.0.0"`` both
    as ``(2,)``, so that the one release written two ways compares equal.
    """
    match = _RELEASE.match(version)
    numbers = [int(part) for part in match.group(0).split(".")] if match else []
    while numbers and numbers[-1] == 0:
        numbers.pop()
    return tuple(numbers)


def floors_problem(python_floor: str, floors: Mapping[str, str]) -> str | None:
    """Why this environment cannot run the package, or ``None`` when it can."""
    have = platform.python_version()
    if _release(have) < _release(python_floor):
        return f"the node's Python {have} is older than the {python_floor} phonometry needs"
    from importlib import metadata

    for name in sorted(floors):
        try:
            version = metadata.version(name)
        except metadata.PackageNotFoundError:
            return f"the node has no {name}; phonometry needs {name} {floors[name]} or later"
        if _release(version) < _release(floors[name]):
            return f"the node's {name} {version} is older than the {floors[name]} phonometry needs"
    return None


def claim_stdout() -> IO[bytes]:
    """Keep descriptor 1 for the frames and point it at standard error.

    Done before anything else is imported, so that a ``print`` anywhere
    below, in the library or in a dependency, lands in the log on standard
    error instead of cutting into a frame.
    """
    if sys.platform == "win32":
        import msvcrt

        for descriptor in (0, 1, 2):
            msvcrt.setmode(descriptor, os.O_BINARY)
    frames = os.fdopen(os.dup(1), "wb")
    os.dup2(2, 1)
    return frames


def _floors(hello: Mapping[str, object]) -> dict[str, str]:
    floors = field(hello, "floors", dict)
    if not all(isinstance(k, str) and isinstance(v, str) for k, v in floors.items()):
        msg = "the floors must map package names to versions"
        raise Refused(msg, stage="hello")
    return floors


def _hand_over(stream: IO[bytes], frames: IO[bytes], package: Path) -> int:
    """Import the package from the cache and give it the stream."""
    sys.path.insert(0, str(package))
    # Absolute on purpose: this file runs as a script, from the node image or
    # sent inline, outside the package it imports here from the cache.
    import phonometry

    location = Path(phonometry.__file__).resolve()
    if package.resolve() not in location.parents:
        msg = f"phonometry imported from {location}, not from the package sent ({package})"
        raise Refused(msg, stage="import")
    # The module that serves the stream is not in the tree yet: mypy reports
    # these two ignores as unused once it is, and they go then.
    from phonometry.simulation._remote import node  # type: ignore[attr-defined]

    write_frame(frames, {"type": "ready"})
    return node.serve(stream, frames)  # type: ignore[no-any-return]


def _converse(stream: IO[bytes], frames: IO[bytes]) -> int:
    hello = read_header(stream)
    if field(hello, "type", str) != "hello":
        msg = "the conversation must open with a hello"
        raise Refused(msg, stage="hello")
    protocol = field(hello, "protocol", int)
    if protocol != PROTOCOL:
        msg = f"this node speaks protocol {PROTOCOL} and the client {protocol}"
        raise Refused(msg, stage="protocol")
    digest = field(hello, "digest", str)
    if not _DIGEST.match(digest):
        msg = f"{digest!r:.80} is not a package digest"
        raise Refused(msg, stage="hello")
    python_floor = field(hello, "python_floor", str)
    floors = _floors(hello)
    cache = cache_dir()
    # Held before the node looks for the package and until the run ends: no
    # other client's prune can take it from under this run.
    held = hold(cache, digest)
    try:
        return _with_package(stream, frames, cache, digest, python_floor, floors)
    finally:
        held.close()


def _with_package(
    stream: IO[bytes],
    frames: IO[bytes],
    cache: Path,
    digest: str,
    python_floor: str,
    floors: Mapping[str, str],
) -> int:
    """Say whether the cache holds the package, take it if not, check the floors, hand over."""
    stored = is_stored(cache / digest)
    write_frame(
        frames,
        {
            "type": "hello",
            "protocol": PROTOCOL,
            "have": stored,
            "python": platform.python_version(),
        },
    )
    if not stored:
        receive_package(stream, cache, digest)
        write_frame(frames, {"type": "stored", "digest": digest})
    touch_and_prune(cache, digest)
    problem = floors_problem(python_floor, floors)
    if problem is not None:
        raise Refused(problem, stage="floors")
    return _hand_over(stream, frames, cache / digest)


def main() -> int:
    """The node's side of the conversation; the process's exit status.

    A refusal or a broken stream ends with status 2 and an ``error`` frame
    whose stage names it (``"frame"`` for the stream); anything else that
    fails ends with status 1 and the stage ``"node"``, its traceback sent.
    """
    frames = claim_stdout()
    stream = sys.stdin.buffer
    try:
        return _converse(stream, frames)
    except Refused as exc:
        send_error(frames, exc.stage, str(exc))
        return 2
    except FrameError as exc:
        send_error(frames, "frame", str(exc))
        return 2
    except Exception as exc:
        send_error(
            frames, "node", f"{type(exc).__name__}: {exc}", traceback.format_exc()
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
