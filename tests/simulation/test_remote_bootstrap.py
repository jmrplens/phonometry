#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The first code a node runs: its frames, the package digest, its cache and its floors.

The bootstrap is the one part of a remote run that does not come with the
package: it lives in the node image, or is sent inline, and it has to read
the client's frames before it knows what the client is. These tests hold its
framing and its digest to their definitions, written out again here, and
run it as a node runs it, in a process of its own.
"""

from __future__ import annotations

import ast
import contextlib
import hashlib
import importlib.metadata
import io
import os
import platform
import re
import selectors
import struct
import subprocess
import sys
import time
from pathlib import Path
from typing import NoReturn

import pytest

from phonometry.simulation._remote import bootstrap

_SOURCE = Path(bootstrap.__file__)
_FILES = (
    ("phonometry/__init__.py", b"VALUE = 1\n"),
    ("phonometry/sub/__init__.py", b""),
)


def _frame(header: dict[str, object], *buffers: bytes) -> bytes:
    out = io.BytesIO()
    bootstrap.write_frame(out, header, [memoryview(b) for b in buffers])
    return out.getvalue()


def _package(*files: tuple[str, bytes]) -> tuple[str, bytes]:
    """The digest of *files* and the package frame that carries them."""
    digest = bootstrap.PackageDigest()
    for path, data in files:
        digest.add(path, data)
    header = {
        "type": "package",
        "digest": digest.hexdigest(),
        "paths": [p for p, _ in files],
    }
    return digest.hexdigest(), _frame(header, *[data for _, data in files])


def _by_hand(files: list[tuple[str, bytes]]) -> str:
    """The package digest as its definition reads, written out again."""
    sha = hashlib.sha256()
    for path, data in files:
        name = path.encode("utf-8")
        sha.update(
            len(name).to_bytes(8, "big") + name + len(data).to_bytes(8, "big") + data
        )
    return sha.hexdigest()


# Frames.


def test_a_frame_reads_back_as_it_was_written() -> None:
    stream = io.BytesIO(_frame({"type": "job", "n": 3}, b"abc", b"") + b"tail")
    assert bootstrap.read_header(stream) == {"type": "job", "n": 3, "buffers": [3, 0]}
    assert bootstrap.read_exact(stream, 3) == b"abc"
    assert stream.read() == b"tail"


def test_a_frame_is_magic_then_length_then_json_then_buffers() -> None:
    text = b'{"type":"x","buffers":[2]}'
    assert (
        _frame({"type": "x"}, b"\x01\x02")
        == b"PNF1" + struct.pack(">I", len(text)) + text + b"\x01\x02"
    )


@pytest.mark.parametrize(
    ("data", "match"),
    [
        (b"", "ended before a frame"),
        (b"Welcome to the node\n", "does not start a frame: it starts b'Welcome '"),
        (b"PNF1" + struct.pack(">I", (1 << 20) + 1), "more than the 1048576 allowed"),
        (b"PNF1" + struct.pack(">I", 4) + b"nope", "not JSON"),
        (b"PNF1" + struct.pack(">I", 2) + b"[]", "not an object"),
        (b"PNF1" + struct.pack(">I", 2) + b"{}", "'type' of a frame"),
        (
            b"PNF1" + struct.pack(">I", 30) + b'{"type":"x","buffers":[-1]}   ',
            "not byte counts",
        ),
        (
            b"PNF1" + struct.pack(">I", 40) + b'{"type":"x"}',
            "ended 28 bytes short of the 40",
        ),
        # Within the size limit, but deeper than json can read: a RecursionError
        # would escape every handler a broken stream has.
        (
            b"PNF1" + struct.pack(">I", 400_000) + b"[" * 200_000 + b"]" * 200_000,
            "nested deeper",
        ),
    ],
)
def test_a_broken_stream_is_named_for_what_it_is(data: bytes, match: str) -> None:
    stream = io.BytesIO(data)
    with pytest.raises(bootstrap.FrameError, match=match):
        bootstrap.read_header(stream)


class _OneByteAtATime(io.BytesIO):
    """A stream that hands over one byte per read, as a pipe read unbuffered may."""

    def read(self, size: int | None = -1) -> bytes:
        return super().read(1 if size is None or size < 0 else min(size, 1))


def test_a_frame_that_arrives_a_byte_at_a_time_reads_whole() -> None:
    stream = _OneByteAtATime(_frame({"type": "job"}, b"abc"))
    assert bootstrap.read_header(stream) == {"type": "job", "buffers": [3]}
    assert bootstrap.read_exact(stream, 3) == b"abc"


def test_a_byte_count_that_is_not_a_whole_number_is_refused_by_name() -> None:
    stream = io.BytesIO(_frame({"type": "job"}, b"abc"))
    with pytest.raises(TypeError, match="'max_header'"):
        bootstrap.read_header(stream, max_header=1.5)
    with pytest.raises(TypeError, match="'size'"):
        bootstrap.read_exact(stream, 2.0)


def test_a_field_of_another_type_is_refused_and_a_bool_is_no_count() -> None:
    with pytest.raises(
        bootstrap.FrameError, match="'have' of a frame is 1, not a bool"
    ):
        bootstrap.field({"have": 1}, "have", bool)
    with pytest.raises(
        bootstrap.FrameError, match="'protocol' of a frame is True, not a int"
    ):
        bootstrap.field({"protocol": True}, "protocol", int)
    assert bootstrap.field({"protocol": 1}, "protocol", int) == 1
    # Where a node owes an object (an element of a list it sent, say), any
    # other JSON value is a broken frame too, never an AttributeError.
    for not_an_object in (5, "abc", [1, 2], None):
        with pytest.raises(bootstrap.FrameError, match="'name' of a frame is None"):
            bootstrap.field(not_an_object, "name", str)


# The package digest.


def test_the_digest_is_its_definition() -> None:
    files = [("phonometry/__init__.py", b"x = 1\n"), ("phonometry/data/a.json", b"{}")]
    digest = bootstrap.PackageDigest()
    for path, data in files:
        digest.add(path, data)
    assert digest.hexdigest() == _by_hand(files)


def test_the_digest_keeps_a_path_apart_from_its_content() -> None:
    one, two = bootstrap.PackageDigest(), bootstrap.PackageDigest()
    one.add("phonometry/ab", b"c")
    two.add("phonometry/a", b"bc")
    assert one.hexdigest() != two.hexdigest()


def test_the_digest_takes_its_files_sorted_and_once() -> None:
    digest = bootstrap.PackageDigest()
    digest.add("phonometry/b.py", b"")
    with pytest.raises(ValueError, match="sorted and once each"):
        digest.add("phonometry/a.py", b"")


@pytest.mark.parametrize(
    "path",
    [
        "phonometry/__init__.py",
        "phonometry/simulation/_remote/node.py",
        "phonometry/solids/data/a-b.json",
    ],
)
def test_a_path_inside_the_package_is_safe(path: str) -> None:
    assert bootstrap.is_safe_path(path)


@pytest.mark.parametrize(
    "path",
    [
        "../etc/passwd",
        "/etc/passwd",
        "phonometry/../x",
        "phonometry/./x",
        "phonometry\\x.py",
        "numpy/core.py",
        "phonometry",
        "phonometry/a b.py",
    ],
)
def test_a_path_outside_the_package_is_refused(path: str) -> None:
    assert not bootstrap.is_safe_path(path)


# The cache. Its lock files are plain files beside the packages: a listing
# of what the cache holds reads its directories.


def _packages(cache: Path) -> list[str]:
    return sorted(p.name for p in cache.iterdir() if p.is_dir())


def test_a_package_received_whole_is_stored_under_its_digest(tmp_path: Path) -> None:
    digest, frame = _package(*_FILES)
    bootstrap.receive_package(io.BytesIO(frame), tmp_path, digest)
    assert (
        tmp_path / digest / "phonometry" / "__init__.py"
    ).read_bytes() == b"VALUE = 1\n"
    assert bootstrap.is_stored(tmp_path / digest)
    assert _packages(tmp_path) == [digest]


def test_a_package_that_hashes_to_another_digest_is_refused_and_nothing_stays(
    tmp_path: Path,
) -> None:
    digest, frame = _package(*_FILES)
    lying = io.BytesIO(frame.replace(digest.encode(), b"f" * 64))
    with pytest.raises(
        bootstrap.Refused, match="hash to [0-9a-f]{64}, not to the digest f{64}"
    ):
        bootstrap.receive_package(lying, tmp_path, "f" * 64)
    assert _packages(tmp_path) == []


def test_a_package_with_a_path_outside_itself_is_refused(tmp_path: Path) -> None:
    digest, frame = _package(("../escape.py", b"x"))
    stream = io.BytesIO(frame)
    with pytest.raises(bootstrap.Refused, match="refuses to write '../escape.py'"):
        bootstrap.receive_package(stream, tmp_path, digest)
    assert not (tmp_path.parent / "escape.py").exists()


def test_a_package_stored_meanwhile_by_another_client_is_taken_as_it_is(
    tmp_path: Path,
) -> None:
    digest, frame = _package(*_FILES)
    bootstrap.receive_package(
        io.BytesIO(frame), tmp_path, digest
    )  # the other client's copy
    bootstrap.receive_package(
        io.BytesIO(frame), tmp_path, digest
    )  # this one finds it in place
    assert _packages(tmp_path) == [digest]


@pytest.mark.parametrize(
    "in_the_way", ["a prune stopped halfway", "a file of its name"]
)
def test_whatever_is_in_the_way_of_a_package_is_replaced(
    tmp_path: Path, in_the_way: str
) -> None:
    final = tmp_path / ("e" * 64)
    if in_the_way == "a file of its name":
        final.write_bytes(b"")
    else:
        (final / "phonometry" / "sub").mkdir(
            parents=True
        )  # its __init__.py already gone
    incoming = tmp_path / "incoming"
    (incoming / "phonometry").mkdir(parents=True)
    (incoming / "phonometry" / "__init__.py").write_bytes(b"VALUE = 1\n")
    bootstrap.install(incoming, final)
    assert bootstrap.is_stored(final)
    assert not incoming.exists()


def _aged(cache: Path, count: int, seconds_apart: float = 1000.0) -> list[str]:
    """*count* whole packages in *cache*, the first the oldest, the last *seconds_apart* old."""
    names = [f"{k:064x}" for k in range(count)]
    for age, name in enumerate(names):
        (cache / name / "phonometry").mkdir(parents=True)
        # Whole, so that touching one marks it used (an empty directory is no package).
        (cache / name / "phonometry" / "__init__.py").write_bytes(b"")
        stamp = time.time() - seconds_apart * (count - age)
        os.utime(cache / name, (stamp, stamp))
    return names


def test_the_cache_keeps_the_five_latest_packages_and_the_one_in_use(
    tmp_path: Path,
) -> None:
    names = _aged(tmp_path, 8)
    (tmp_path / "cupy-kernels").mkdir()
    bootstrap.touch_and_prune(tmp_path, names[0])
    assert _packages(tmp_path) == sorted([names[0], *names[4:], "cupy-kernels"])


def test_a_package_used_in_the_last_ten_minutes_is_not_pruned(tmp_path: Path) -> None:
    names = _aged(tmp_path, 8, seconds_apart=60.0)  # the oldest used eight minutes ago
    bootstrap.touch_and_prune(tmp_path, names[-1])
    assert _packages(tmp_path) == names


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="a node is POSIX; on Windows the bootstrap locks nothing",
)
def test_a_package_a_run_holds_is_never_pruned(tmp_path: Path) -> None:
    names = _aged(tmp_path, 8)
    held = bootstrap.hold(tmp_path, names[1])  # a run of an old package, still going
    try:
        bootstrap.touch_and_prune(tmp_path, names[-1])
    finally:
        held.close()
    assert _packages(tmp_path) == sorted([names[1], *names[3:]])


def test_touching_a_package_another_client_pruned_creates_nothing(
    tmp_path: Path,
) -> None:
    digest = "d" * 64
    bootstrap.touch_and_prune(tmp_path, digest)  # pruned by another client a moment ago
    assert not (tmp_path / digest).exists()


class _Stopped(Exception):
    """The node stopped (killed, its client gone) in the middle of a deletion."""


def test_a_prune_stopped_halfway_leaves_no_package_under_its_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    names = _aged(tmp_path, 6)  # one more than the cache keeps

    def stopped(path: object, **_options: object) -> None:
        msg = f"stopped while deleting {path}"
        raise _Stopped(msg)

    monkeypatch.setattr(bootstrap.shutil, "rmtree", stopped)
    with pytest.raises(_Stopped, match="stopped while deleting"):
        bootstrap.touch_and_prune(tmp_path, names[-1])
    monkeypatch.undo()
    # Off its digest before a file of it went: no run takes a part of it for whole.
    assert not (tmp_path / names[0]).exists()
    bootstrap.touch_and_prune(tmp_path, names[-1])  # the next prune clears what is left
    assert _packages(tmp_path) == names[1:]


def test_an_upload_cut_off_a_day_ago_is_cleared(tmp_path: Path) -> None:
    digest, frame = _package(*_FILES)
    bootstrap.receive_package(io.BytesIO(frame), tmp_path, digest)
    old, recent = tmp_path / ".incoming-old", tmp_path / ".incoming-recent"
    old.mkdir()
    recent.mkdir()
    stamp = time.time() - 2 * 86400.0
    os.utime(old, (stamp, stamp))
    bootstrap.touch_and_prune(tmp_path, digest)
    assert not old.exists()
    assert recent.exists()


def test_the_cache_is_the_variable_then_xdg_then_home(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(bootstrap.CACHE_VAR, str(tmp_path / "explicit"))
    assert bootstrap.cache_dir() == tmp_path / "explicit"
    monkeypatch.delenv(bootstrap.CACHE_VAR)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    assert bootstrap.cache_dir() == tmp_path / "phonometry" / "remote"
    monkeypatch.delenv("XDG_CACHE_HOME")
    assert bootstrap.cache_dir() == Path.home() / ".cache" / "phonometry" / "remote"


# The floors.


def test_this_environment_meets_low_floors() -> None:
    assert bootstrap.floors_problem("3.8", {"numpy": "1.0"}) is None


@pytest.mark.parametrize(
    ("python", "floors", "pattern"),
    [
        ("99.0", {}, r"the node's Python \S+ is older than the 99.0 phonometry needs"),
        (
            "3.8",
            {"numpy": "999.0"},
            r"the node's numpy \S+ is older than the 999.0 phonometry needs",
        ),
        ("3.8", {"not-a-package-xyz": "1.0"}, "the node has no not-a-package-xyz"),
    ],
)
def test_a_floor_not_met_says_which(
    python: str, floors: dict[str, str], pattern: str
) -> None:
    problem = bootstrap.floors_problem(python, floors)
    assert problem is not None
    assert re.search(pattern, problem)


def test_a_floor_written_with_more_zeros_is_the_same_release() -> None:
    python = platform.python_version()
    numpy = importlib.metadata.version("numpy")
    assert bootstrap.floors_problem(f"{python}.0", {"numpy": f"{numpy}.0.0"}) is None


# The bootstrap as a node runs it, in a process of its own.


def _hello(digest: str, **changes: object) -> bytes:
    header: dict[str, object] = {
        "type": "hello",
        "protocol": bootstrap.PROTOCOL,
        "digest": digest,
        "python_floor": "3.8",
        "floors": {},
    }
    return _frame({**header, **changes})


def _answers(data: bytes) -> list[dict[str, object]]:
    """Every frame in *data*, a node's standard output, by its header."""
    stream = io.BytesIO(data)
    answers = []
    while stream.tell() < len(data):
        header = bootstrap.read_header(stream)
        for size in bootstrap.field(header, "buffers", list):
            bootstrap.read_exact(stream, size)
        answers.append(header)
    return answers


def _run_node(frames: bytes, cache: Path) -> tuple[list[dict[str, object]], int]:
    """Run the bootstrap file as a node runs it and read every frame it answered."""
    env = {**os.environ, bootstrap.CACHE_VAR: str(cache)}
    done = subprocess.run(
        [sys.executable, "-I", str(_SOURCE)],
        input=frames,
        capture_output=True,
        env=env,
        check=False,
        timeout=120,
    )
    return _answers(done.stdout), done.returncode


def test_a_client_of_another_protocol_is_refused_by_name(tmp_path: Path) -> None:
    answers, code = _run_node(_hello("a" * 64, protocol=99), tmp_path)
    assert code == 2
    assert (answers[-1]["type"], answers[-1]["stage"]) == ("error", "protocol")


def test_a_node_asks_for_a_package_it_lacks_and_refuses_unmet_floors(
    tmp_path: Path,
) -> None:
    digest, package = _package(*_FILES)
    answers, code = _run_node(
        _hello(digest, floors={"numpy": "999.0"}) + package, tmp_path
    )
    assert [a["type"] for a in answers] == ["hello", "stored", "error"]
    assert answers[0]["have"] is False
    assert answers[2]["stage"] == "floors"
    assert "999.0" in str(answers[2]["message"])
    assert code == 2
    assert bootstrap.is_stored(tmp_path / digest)


def test_a_node_that_holds_the_package_does_not_ask_for_it_again(
    tmp_path: Path,
) -> None:
    digest, package = _package(*_FILES)
    _run_node(_hello(digest, floors={"numpy": "999.0"}) + package, tmp_path)
    answers, _ = _run_node(_hello(digest, floors={"numpy": "999.0"}), tmp_path)
    assert answers[0]["have"] is True
    assert [a["type"] for a in answers] == ["hello", "error"]


#: The longest a test waits on a node it runs before failing [s].
_NODE_WAIT_S = 120.0


def _stop_and_fail(nodes: list[subprocess.Popen[bytes]], what: str) -> NoReturn:
    """Stop every node and fail with *what*, quoting each node's standard error."""
    for node in nodes:
        node.kill()
    said = [node.communicate(timeout=_NODE_WAIT_S)[1] for node in nodes]
    pytest.fail(f"{what}; the nodes wrote on standard error: {said!r}")


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="a node is POSIX; on Windows the bootstrap locks nothing",
)
def test_two_clients_that_send_one_package_at_once_both_store_it(
    tmp_path: Path,
) -> None:
    """Two notebooks on the first run of a new version, on one node at the same time.

    Every wait is bounded: a lock that is never released fails the test with
    what the nodes said, instead of holding the suite.
    """
    digest, package = _package(*_FILES)
    hello = _hello(digest, floors={"numpy": "999.0"})
    env = {**os.environ, bootstrap.CACHE_VAR: str(tmp_path)}
    with contextlib.ExitStack() as stack:
        nodes = [
            stack.enter_context(
                subprocess.Popen(
                    [sys.executable, "-I", str(_SOURCE)],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env,
                )
            )
            for _ in range(2)
        ]
        for node in nodes:
            assert node.stdin is not None
            node.stdin.write(hello)
            node.stdin.flush()
        # Both hold the digest and are asked for the package before either
        # has sent a byte of it, so both send it, and both store it.
        for node in nodes:
            assert node.stdout is not None
            with selectors.DefaultSelector() as selector:
                selector.register(node.stdout, selectors.EVENT_READ)
                if not selector.select(_NODE_WAIT_S):
                    _stop_and_fail(nodes, "a node did not answer its hello")
            assert bootstrap.read_header(node.stdout)["have"] is False
        for node in nodes:
            assert node.stdin is not None
            node.stdin.write(package)
            node.stdin.flush()  # left open: communicate closes it
        # A node says nothing after its hello until it has the package, so
        # none of what follows waits in the reader's buffer: communicate reads
        # all of it from the pipe.
        for node in nodes:
            try:
                out, err = node.communicate(timeout=_NODE_WAIT_S)
            except subprocess.TimeoutExpired:
                _stop_and_fail(nodes, "a node did not finish with its package")
            answers = _answers(out)
            assert node.returncode == 2, err
            assert [a["type"] for a in answers] == ["stored", "error"], err
            assert answers[1]["stage"] == "floors", err
    assert _packages(tmp_path) == [digest]
    assert bootstrap.is_stored(tmp_path / digest)


def test_a_stray_print_on_a_node_lands_on_standard_error() -> None:
    script = (
        f"import sys; sys.path.insert(0, {str(_SOURCE.parent)!r}); import bootstrap as b; "
        "out = b.claim_stdout(); print('stray'); b.write_frame(out, {'type': 'ok'})"
    )
    done = subprocess.run(
        [sys.executable, "-I", "-c", script], capture_output=True, check=False
    )
    assert bootstrap.read_header(io.BytesIO(done.stdout)) == {
        "type": "ok",
        "buffers": [],
    }
    assert b"stray" in done.stderr


def test_the_bootstrap_parses_as_python_3_8_and_loads_nothing_of_the_library() -> None:
    tree = ast.parse(_SOURCE.read_text(encoding="utf-8"), feature_version=(3, 8))
    loaded = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {node.module or "" for node in tree.body if isinstance(node, ast.ImportFrom)}
    assert not any(name.startswith(("phonometry", "numpy")) for name in loaded)
