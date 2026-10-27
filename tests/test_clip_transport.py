#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The client of the clip transport trusts nothing the node sends.

A node renders the committed code (``git archive`` of HEAD), so a checkout
with changes is refused before anything is sent, but the files a run writes
itself (the stamps in the tracked manifest, the lock of the published
assets) stop neither the next clip nor the next run. What comes back is
checked before a byte of it is written: the name is one a render of that
clip writes, the size is under its cap, the first bytes are the container's,
and the fingerprint the node computed is this checkout's. A run that stops
half way keeps the clips that arrived whole and nothing else, a node
that dies before it answers is named with its exit status, and what a
node says reaches the terminal with its control characters escaped.
"""

from __future__ import annotations

import io
import os
import pathlib
import signal
import subprocess
import sys
import tarfile
import tempfile
import threading
import types
from typing import TYPE_CHECKING, Any, BinaryIO

import child_process
import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))

import check_animation_freshness
import clip_link
import clip_node
import clip_transport

# A run reads the registry, whose import sets the figure theme; imported here,
# it is set before any test's matplotlib settings are compared.
import figures.registry  # noqa: F401

from phonometry.simulation._remote.hosts import HostEntry

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping

# The client reads the frame audit and the registry: the figure stack.
pytestmark = pytest.mark.pinned_stack

#: The moves and removals of files as pathlib makes them, for a test that
#: stood them in for to set back while the rest of what it patched stays.
_REPLACE = pathlib.Path.replace
_UNLINK = pathlib.Path.unlink

_WEBM = b"\x1aE\xdf\xa3" + b"0" * 12
_GIF = b"GIF89a" + b"0" * 10
_WEBP = b"RIFF\x00\x00\x00\x00WEBP" + b"0" * 4


@pytest.fixture(autouse=True)
def _manifest_of_its_own(
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[None]:
    """A stamp a test lets through goes to a manifest of the test's, never the checkout's.

    Its own patch, which a test that sets its own patches back leaves alone.
    """
    import animation_fingerprint

    manifest = tmp_path_factory.mktemp("manifest") / "animation_fingerprints.txt"
    with pytest.MonkeyPatch.context() as own:
        own.setattr(animation_fingerprint, "MANIFEST", manifest)
        yield


def _git(repo: pathlib.Path, *args: str) -> str:
    return child_process.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    ).stdout


@pytest.fixture
def repo(tmp_path: pathlib.Path) -> pathlib.Path:
    """A committed checkout: the paths a render ships, one it does not, and the files a run writes."""
    root = tmp_path / "repo"
    names = (
        "src/pkg/a.py",
        "scripts/b.py",
        "docs/c.md",
        "pyproject.toml",
        "VERSION",
        "engine-digests.json",
        "requirements.txt",
        "requirements-figures.txt",
        *clip_transport.RUN_WRITES,
    )
    for name in names:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x\n", encoding="utf-8")
    # As in the repository: the manifest's lock is never tracked.
    (root / ".gitignore").write_text(
        "scripts/animation_fingerprints.lock\n", encoding="utf-8"
    )
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    _git(
        root,
        "-c",
        "user.name=t",
        "-c",
        "user.email=t@t",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "-qm",
        "c",
    )
    return root


def _here() -> HostEntry:
    return HostEntry(
        name="here",
        ssh="localhost",
        runner="python",
        target=sys.executable,
        label="this machine",
        timeout_s=None,
    )


def test_a_clean_checkout_is_carried(repo: pathlib.Path) -> None:
    clip_transport.refuse_dirty_tree(repo)


def test_a_change_to_a_tracked_file_is_refused(repo: pathlib.Path) -> None:
    (repo / "docs" / "c.md").write_text("changed\n", encoding="utf-8")
    with pytest.raises(clip_transport.DirtyTreeError, match=r"docs/c\.md"):
        clip_transport.refuse_dirty_tree(repo)


@pytest.mark.parametrize("where", ["scripts/new.py", "src/pkg/new.py"])
def test_an_untracked_file_under_scripts_or_src_is_refused(
    repo: pathlib.Path, where: str
) -> None:
    (repo / where).write_text("y\n", encoding="utf-8")
    with pytest.raises(clip_transport.DirtyTreeError, match=where.replace(".", r"\.")):
        clip_transport.refuse_dirty_tree(repo)


def test_an_untracked_file_elsewhere_is_carried_on(repo: pathlib.Path) -> None:
    (repo / "notes.txt").write_text("y\n", encoding="utf-8")
    clip_transport.refuse_dirty_tree(repo)


def test_a_staged_rename_is_named_once(repo: pathlib.Path) -> None:
    _git(repo, "mv", "scripts/b.py", "scripts/b2.py")
    assert clip_transport.dirty_paths(repo) == ["scripts/b2.py"]


def test_a_run_starts_after_one_that_stamped_and_published(repo: pathlib.Path) -> None:
    """The stamps and the lock of the published assets are the run's own, left for a commit."""
    for name in clip_transport.RUN_WRITES:
        (repo / name).write_text("written by the last run\n", encoding="utf-8")
    clip_transport.refuse_dirty_tree(repo)
    assert clip_transport.unmoved(repo, clip_transport._head(repo))
    (repo / "docs" / "c.md").write_text("changed\n", encoding="utf-8")
    with pytest.raises(clip_transport.DirtyTreeError, match=r"docs/c\.md"):
        clip_transport.refuse_dirty_tree(repo)


def test_the_archive_carries_head_and_only_what_a_render_needs(
    repo: pathlib.Path,
) -> None:
    with tarfile.open(
        fileobj=io.BytesIO(clip_transport.archive(repo)), mode="r:gz"
    ) as tar:
        names = {m.name for m in tar.getmembers() if m.isfile()}
    assert "docs/c.md" not in names
    # VERSION: the node image does not install phonometry, which reads its
    # version from that file at the archive's root.
    assert {"src/pkg/a.py", "scripts/b.py", "engine-digests.json", "VERSION"} <= names


def test_a_fresh_clip_is_skipped_and_a_named_one_is_not() -> None:
    current = {"anim_fresh": "f1", "anim_stale": "s2", "anim_heavy": "h3"}
    stamped = {"anim_fresh": "f1", "anim_stale": "old", "anim_heavy": "h3"}
    encoders = {"anim_fresh": "av1_nvenc", "anim_stale": "av1_nvenc"}
    present = set(check_animation_freshness.outputs("anim_fresh")) | set(
        check_animation_freshness.outputs("anim_heavy")
    )
    weights = {"anim_heavy": 900.0}
    kwargs: dict[str, Any] = {
        "current": current,
        "stamped": stamped,
        "encoders": encoders,
        "present": present,
        "weights": weights,
    }
    assert clip_transport.clips_to_render(None, force=False, **kwargs) == [
        "anim_heavy",
        "anim_stale",
    ]
    assert clip_transport.clips_to_render(["anim_fresh"], force=False, **kwargs) == [
        "anim_fresh"
    ]
    assert clip_transport.clips_to_render(None, force=True, **kwargs) == [
        "anim_heavy",
        "anim_fresh",
        "anim_stale",
    ]
    with pytest.raises(ValueError, match=r"anim_nowhere"):
        clip_transport.clips_to_render(["anim_nowhere"], force=False, **kwargs)


def test_the_job_carries_each_clip_s_device_and_recorded_needs() -> None:
    header = clip_transport.job_header(
        ["anim_meta", "anim_room"],
        devices={"anim_meta": "cpu", "anim_room": "gpu"},
        gpu_bytes={"anim_room": 3 << 30},
        host_bytes={"anim_meta": 7 << 30},
        compute="cupy",
        encoder="av1_nvenc",
        audit_only=False,
    )
    assert header["clips"] == [
        {"name": "anim_meta", "device": "cpu", "gpu_bytes": 0, "host_bytes": 7 << 30},
        {"name": "anim_room", "device": "gpu", "gpu_bytes": 3 << 30, "host_bytes": 0},
    ]
    assert clip_node.Job.from_header(header).clips[0].host_bytes == 7 << 30


@pytest.mark.parametrize(
    ("placement", "encoder"), [("cupy@nas", "av1_nvenc"), ("cpu@nas", "libsvtav1")]
)
def test_a_node_without_a_gpu_encodes_on_its_cpu_by_default(
    monkeypatch: pytest.MonkeyPatch, placement: str, encoder: str
) -> None:
    """NVENC needs the GPU a cpu placement does not pass to the container."""
    from phonometry.simulation.compute import _requested

    monkeypatch.setenv("PHONOMETRY_COMPUTE", placement)
    assert clip_transport.default_encoder(_requested(None)) == encoder


_EXPECT = clip_transport.Expect(
    clips=frozenset({"anim_x"}), encoder="av1_nvenc", audit_only=False
)


def _clip_frame(
    clip: str = "anim_x", **change: Any
) -> tuple[dict[str, Any], list[bytes]]:
    names = check_animation_freshness.outputs(clip)
    data = {".webm": _WEBM, ".gif": _GIF, ".webp": _WEBP}
    buffers = [data[pathlib.PurePosixPath(n).suffix] for n in names] + [b'{"a": 1}']
    header: dict[str, Any] = {
        "type": "clip",
        "clip": clip,
        "ok": True,
        "fingerprint": "f00d",
        "encoder": "av1_nvenc",
        "files": [
            {"name": n, "size": len(b)} for n, b in zip(names, buffers, strict=False)
        ],
        "fragments": [{"name": "4242.json", "size": len(buffers[-1])}],
    }
    header.update(change)
    return header, buffers


@pytest.mark.parametrize(
    ("change", "match"),
    [
        ({"clip": "anim_other"}, r"nobody asked for"),
        ({"files": [{"name": "../anim_x.webm", "size": 4}]}, r"may not"),
        ({"files": [{"name": "anim_x.webm", "size": 1 << 30}]}, r"outside"),
        ({"files": [{"name": "anim_x.exe", "size": 4}]}, r"kind of file"),
        ({"encoder": "libsvtav1"}, r"encoder"),
        (
            {
                "fragments": [
                    {"name": f"{k}.json", "size": 8}
                    for k in range(clip_node.MAX_FRAGMENTS + 1)
                ]
            },
            r"language records",
        ),
    ],
)
def test_a_frame_the_client_did_not_ask_for_is_refused(
    change: dict[str, Any], match: str
) -> None:
    header, _ = _clip_frame(**change)
    with pytest.raises(ValueError, match=match):
        clip_transport.result_sizes(header, _EXPECT)


def test_a_frame_missing_one_of_the_ten_files_is_refused() -> None:
    header, _ = _clip_frame()
    header["files"] = header["files"][1:]
    with pytest.raises(ValueError, match=r"other files"):
        clip_transport.result_sizes(header, _EXPECT)


@pytest.mark.parametrize(
    ("change", "match"),
    [
        ({"clip": ["anim_x"]}, r"nobody asked for"),
        ({"files": "anim_x.webm"}, r"files are a list"),
        ({"fragments": {"name": "1.json", "size": 8}}, r"fragments are a list"),
        ({"fragments": ["1.json"]}, r"fragments are a list"),
        ({"fragments": [{"name": "1.json", "size": 8}] * 2}, r"twice"),
    ],
)
def test_a_frame_of_another_shape_is_refused_as_one(
    change: dict[str, Any], match: str
) -> None:
    """A field of the wrong kind is a refused frame, never a crash on the node's data."""
    header, _ = _clip_frame(**change)
    with pytest.raises(ValueError, match=match):
        clip_transport.result_sizes(header, _EXPECT)


def test_a_file_name_the_node_made_up_is_shown_escaped() -> None:
    header, _ = _clip_frame(
        files=[{"name": "anim_x\x1b]52;c;ZXZpbA==\x07.webm", "size": 1 << 30}]
    )
    with pytest.raises(ValueError, match=r"may not") as caught:
        clip_transport.result_sizes(header, _EXPECT)
    assert "\x1b" not in str(caught.value)


def _places(tmp_path: pathlib.Path) -> clip_transport.Places:
    return clip_transport.Places(
        clips=tmp_path / "images",
        fragments=tmp_path / "language",
        audit=tmp_path / "audit",
    )


@pytest.fixture
def stamps(monkeypatch: pytest.MonkeyPatch) -> list[tuple[list[str], str | None]]:
    import animation_fingerprint

    seen: list[tuple[list[str], str | None]] = []
    monkeypatch.setattr(
        animation_fingerprint,
        "stamp",
        lambda clips, root=None, *, encoder, current=None: seen.append(
            (list(clips), encoder)
        ),
    )
    return seen


def test_a_good_clip_is_copied_stamped_and_its_fragments_kept(
    tmp_path: pathlib.Path, stamps: list[tuple[list[str], str | None]]
) -> None:
    header, buffers = _clip_frame()
    reason = clip_transport.accept(
        header,
        buffers,
        current={"anim_x": "f00d"},
        expect=_EXPECT,
        places=_places(tmp_path),
    )
    assert reason is None
    assert sorted(p.name for p in (tmp_path / "images").iterdir()) == sorted(
        check_animation_freshness.outputs("anim_x")
    )
    assert (tmp_path / "language" / "node-anim_x-4242.json").exists()
    assert stamps == [(["anim_x"], "av1_nvenc")]


def test_a_clip_s_language_records_replace_an_earlier_run_s(
    tmp_path: pathlib.Path, stamps: list[tuple[list[str], str | None]]
) -> None:
    """Records left by an earlier run of the clip would be merged into the language check."""
    places = _places(tmp_path)
    assert places.fragments is not None
    places.fragments.mkdir(parents=True)
    (places.fragments / "node-anim_x-1111.json").write_text("{}", encoding="utf-8")
    (places.fragments / "node-anim_y-2222.json").write_text("{}", encoding="utf-8")
    header, buffers = _clip_frame()
    assert (
        clip_transport.accept(
            header, buffers, current={"anim_x": "f00d"}, expect=_EXPECT, places=places
        )
        is None
    )
    assert sorted(p.name for p in places.fragments.iterdir()) == [
        "node-anim_x-4242.json",
        "node-anim_y-2222.json",
    ]


def test_a_clip_whose_node_fingerprint_differs_is_not_stamped(
    tmp_path: pathlib.Path, stamps: list[tuple[list[str], str | None]]
) -> None:
    header, buffers = _clip_frame()
    reason = clip_transport.accept(
        header,
        buffers,
        current={"anim_x": "beef"},
        expect=_EXPECT,
        places=_places(tmp_path),
    )
    assert reason is not None
    assert "other code" in reason
    assert not (tmp_path / "images").exists()
    assert stamps == []


def test_a_webm_without_its_first_bytes_is_not_copied(
    tmp_path: pathlib.Path, stamps: list[tuple[list[str], str | None]]
) -> None:
    header, buffers = _clip_frame()
    buffers[0] = b"<html>" + b"0" * 10
    reason = clip_transport.accept(
        header,
        buffers,
        current={"anim_x": "f00d"},
        expect=_EXPECT,
        places=_places(tmp_path),
    )
    assert reason is not None
    assert "does not start like" in reason
    assert stamps == []


def test_a_clip_with_no_fingerprint_on_either_side_is_not_stamped(
    tmp_path: pathlib.Path, stamps: list[tuple[list[str], str | None]]
) -> None:
    """Two missing fingerprints are not two equal ones."""
    header, buffers = _clip_frame()
    del header["fingerprint"]
    reason = clip_transport.accept(
        header, buffers, current={}, expect=_EXPECT, places=_places(tmp_path)
    )
    assert reason is not None
    assert "other code" in reason
    assert stamps == []


def test_a_copy_that_stops_part_way_replaces_none_of_the_clip_s_files(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    stamps: list[tuple[list[str], str | None]],
) -> None:
    """The clip's files on disk stay the earlier run's, whole, and it is not stamped."""
    places = _places(tmp_path)
    places.clips.mkdir(parents=True)
    names = check_animation_freshness.outputs("anim_x")
    for name in names:
        (places.clips / name).write_bytes(b"earlier run")
    written = pathlib.Path.write_bytes
    calls: list[pathlib.Path] = []

    def write_bytes(path: pathlib.Path, data: bytes) -> int:
        calls.append(path)
        if len(calls) == 3:
            msg = "disk full"
            raise OSError(msg)
        return written(path, data)

    monkeypatch.setattr(pathlib.Path, "write_bytes", write_bytes)
    header, buffers = _clip_frame()
    with pytest.raises(OSError, match=r"disk full"):
        clip_transport.accept(
            header, buffers, current={"anim_x": "f00d"}, expect=_EXPECT, places=places
        )
    assert sorted(p.name for p in places.clips.iterdir()) == sorted(names)
    assert all((places.clips / name).read_bytes() == b"earlier run" for name in names)
    assert stamps == []


def _earlier_run(places: clip_transport.Places) -> list[str]:
    """The files an earlier run of anim_x left: its ten files and one language record."""
    assert places.fragments is not None
    places.clips.mkdir(parents=True)
    places.fragments.mkdir(parents=True)
    names = check_animation_freshness.outputs("anim_x")
    for name in names:
        (places.clips / name).write_bytes(b"earlier run")
    (places.fragments / "node-anim_x-1111.json").write_bytes(b"earlier run")
    return names


def _left(places: clip_transport.Places) -> dict[str, bytes]:
    """Every file under the clips' and the records' directories, by name, with what it holds."""
    assert places.fragments is not None
    return {
        path.name: path.read_bytes()
        for folder in (places.clips, places.fragments)
        for path in folder.iterdir()
    }


#: The moves of a clip whose ten files and one record replace an earlier
#: run's: ten files and the old record set aside, then eleven moved in.
_MOVES = 22


@pytest.mark.parametrize("stop", [1, 2, 11, 12, 17, _MOVES])
@pytest.mark.parametrize("error", [KeyboardInterrupt, OSError])
def test_an_interrupt_between_a_clip_s_moves_leaves_the_earlier_run_s_files_whole(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    stamps: list[tuple[list[str], str | None]],
    stop: int,
    error: type[BaseException],
) -> None:
    """Every file moved before the stop is put back: no clip is left with files of both runs.

    The stop is an interrupt, or a file that cannot be moved.
    """
    places = _places(tmp_path)
    names = _earlier_run(places)
    before = _left(places)
    moved = pathlib.Path.replace
    calls: list[pathlib.Path] = []

    def replace(path: pathlib.Path, target: pathlib.Path) -> pathlib.Path:
        calls.append(path)
        if len(calls) == stop:
            msg = "a stop between two moves"
            raise error(msg)
        return moved(path, target)

    monkeypatch.setattr(pathlib.Path, "replace", replace)
    header, buffers = _clip_frame()
    with pytest.raises(error, match=r"between two moves"):
        clip_transport.accept(
            header, buffers, current={"anim_x": "f00d"}, expect=_EXPECT, places=places
        )
    monkeypatch.setattr(pathlib.Path, "replace", moved)
    assert _left(places) == before
    assert len(before) == len(names) + 1
    assert stamps == []


def test_a_ctrl_c_between_a_clip_s_moves_lands_the_clip_whole_first(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    stamps: list[tuple[list[str], str | None]],
) -> None:
    """Ctrl-C is held back while a clip's files move, and raised once they all have.

    The clip is not stamped, so the next run renders it again.
    """
    places = _places(tmp_path)
    names = _earlier_run(places)
    moved = pathlib.Path.replace
    calls: list[pathlib.Path] = []

    def replace(path: pathlib.Path, target: pathlib.Path) -> pathlib.Path:
        calls.append(path)
        if len(calls) == _MOVES // 2:
            # Sent from the main thread, it is handled before this goes on.
            signal.raise_signal(signal.SIGINT)
        return moved(path, target)

    monkeypatch.setattr(pathlib.Path, "replace", replace)
    header, buffers = _clip_frame()
    # The interpreter's own, raised by the handler the move held back: no message.
    with pytest.raises(KeyboardInterrupt, match=r"\A\Z"):
        clip_transport.accept(
            header, buffers, current={"anim_x": "f00d"}, expect=_EXPECT, places=places
        )
    monkeypatch.setattr(pathlib.Path, "replace", moved)
    assert len(calls) == _MOVES
    left = _left(places)
    assert sorted(left) == sorted([*names, "node-anim_x-4242.json"])
    assert all(data != b"earlier run" for data in left.values())
    assert stamps == []


def _moves(
    monkeypatch: pytest.MonkeyPatch, at: Mapping[int, Callable[[], None]]
) -> list[pathlib.Path]:
    """Every move a landing makes, with *at* run at the moves it numbers, before each is made."""
    moved = pathlib.Path.replace
    calls: list[pathlib.Path] = []

    def replace(path: pathlib.Path, target: pathlib.Path) -> pathlib.Path:
        calls.append(path)
        if len(calls) in at:
            at[len(calls)]()
        return moved(path, target)

    monkeypatch.setattr(pathlib.Path, "replace", replace)
    return calls


def _cannot_move() -> None:
    msg = "a file that cannot be moved"
    raise OSError(msg)


def test_a_ctrl_c_held_while_a_move_fails_is_still_delivered(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    stamps: list[tuple[list[str], str | None]],
) -> None:
    """The moves are undone for the failure, and the interrupt is not lost to it."""
    places = _places(tmp_path)
    _earlier_run(places)
    before = _left(places)
    _moves(
        monkeypatch,
        {5: lambda: signal.raise_signal(signal.SIGINT), 8: _cannot_move},
    )
    header, buffers = _clip_frame()
    with pytest.raises(KeyboardInterrupt, match=r"\A\Z"):
        clip_transport.accept(
            header, buffers, current={"anim_x": "f00d"}, expect=_EXPECT, places=places
        )
    monkeypatch.setattr(pathlib.Path, "replace", _REPLACE)
    assert _left(places) == before
    assert stamps == []


@pytest.mark.skipif(sys.platform == "win32", reason="Windows has no SIGHUP")
@pytest.mark.parametrize("name", ["SIGTERM", "SIGHUP"])
def test_a_stop_or_a_hang_up_waits_until_the_clip_has_landed(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    stamps: list[tuple[list[str], str | None]],
    name: str,
) -> None:
    """A closed terminal or a stop ends the run as Ctrl-C does: after the moves, never between them."""
    sig = getattr(signal, name)
    places = _places(tmp_path)
    names = _earlier_run(places)
    calls = _moves(monkeypatch, {_MOVES // 2: lambda: signal.raise_signal(sig)})
    delivered: list[int] = []
    previous = signal.signal(sig, lambda signum, _frame: delivered.append(len(calls)))
    try:
        header, buffers = _clip_frame()
        reason = clip_transport.accept(
            header, buffers, current={"anim_x": "f00d"}, expect=_EXPECT, places=places
        )
    finally:
        signal.signal(sig, previous)
    monkeypatch.setattr(pathlib.Path, "replace", _REPLACE)
    assert reason is None
    assert delivered == [_MOVES]
    left = _left(places)
    assert sorted(left) == sorted([*names, "node-anim_x-4242.json"])
    assert all(data != b"earlier run" for data in left.values())


@pytest.mark.skipif(sys.platform == "win32", reason="Windows has no SIGHUP")
def test_a_hang_up_held_after_a_ctrl_c_is_delivered_too(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    stamps: list[tuple[list[str], str | None]],
) -> None:
    """Ctrl-C raises once it is delivered, so it goes last: a hang-up held after it is not lost."""
    places = _places(tmp_path)
    _earlier_run(places)
    calls = _moves(
        monkeypatch,
        {
            3: lambda: signal.raise_signal(signal.SIGINT),
            6: lambda: signal.raise_signal(signal.SIGHUP),
        },
    )
    delivered: list[int] = []
    previous = signal.signal(
        signal.SIGHUP, lambda signum, _frame: delivered.append(len(calls))
    )
    try:
        header, buffers = _clip_frame()
        with pytest.raises(KeyboardInterrupt, match=r"\A\Z"):
            clip_transport.accept(
                header,
                buffers,
                current={"anim_x": "f00d"},
                expect=_EXPECT,
                places=places,
            )
    finally:
        signal.signal(signal.SIGHUP, previous)
    monkeypatch.setattr(pathlib.Path, "replace", _REPLACE)
    assert delivered == [_MOVES]


def test_an_undo_that_meets_a_file_it_cannot_remove_puts_the_rest_back(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    stamps: list[tuple[list[str], str | None]],
) -> None:
    """Each step of the undo goes on past a failure, and the error that stopped the moves is the one raised.

    The moves stop at the sixth file moved in; undoing them, the fifth
    cannot be removed, and the earlier run's file is moved back over it.
    """
    places = _places(tmp_path)
    names = _earlier_run(places)
    before = _left(places)
    _moves(monkeypatch, {17: _cannot_move})
    refused: list[pathlib.Path] = []

    def unlink(path: pathlib.Path, *, missing_ok: bool = False) -> None:
        if path.name == names[4] and not refused:
            refused.append(path)
            msg = "a file the undo cannot remove"
            raise PermissionError(msg)
        _UNLINK(path, missing_ok=missing_ok)

    monkeypatch.setattr(pathlib.Path, "unlink", unlink)
    header, buffers = _clip_frame()
    with pytest.raises(OSError, match=r"a file that cannot be moved"):
        clip_transport.accept(
            header, buffers, current={"anim_x": "f00d"}, expect=_EXPECT, places=places
        )
    monkeypatch.setattr(pathlib.Path, "replace", _REPLACE)
    monkeypatch.setattr(pathlib.Path, "unlink", _UNLINK)
    assert refused == [places.clips / names[4]]
    assert _left(places) == before
    assert stamps == []


@pytest.mark.parametrize("stop", [1, 6, _MOVES // 2], ids=["first", "sixth", "last"])
def test_a_first_landing_stopped_part_way_leaves_none_of_the_clip_s_files(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    stamps: list[tuple[list[str], str | None]],
    stop: int,
) -> None:
    """With no earlier run to move back, the undo removes every file it had moved in.

    Nothing is in the way, so every move moves one of the clip's eleven
    files in.
    """
    places = _places(tmp_path)
    _moves(monkeypatch, {stop: _cannot_move})
    header, buffers = _clip_frame()
    with pytest.raises(OSError, match=r"a file that cannot be moved"):
        clip_transport.accept(
            header, buffers, current={"anim_x": "f00d"}, expect=_EXPECT, places=places
        )
    monkeypatch.setattr(pathlib.Path, "replace", _REPLACE)
    assert _left(places) == {}
    assert stamps == []


def test_a_stale_record_with_the_name_of_this_run_s_is_replaced(
    tmp_path: pathlib.Path,
    stamps: list[tuple[list[str], str | None]],
) -> None:
    """The record is in the way twice, as a file of this run and as a stale one: it is set aside once."""
    places = _places(tmp_path)
    assert places.fragments is not None
    _earlier_run(places)
    (places.fragments / "node-anim_x-4242.json").write_bytes(b"earlier run")
    header, buffers = _clip_frame()
    reason = clip_transport.accept(
        header, buffers, current={"anim_x": "f00d"}, expect=_EXPECT, places=places
    )
    assert reason is None
    assert sorted(p.name for p in places.fragments.iterdir()) == [
        "node-anim_x-4242.json"
    ]
    assert (places.fragments / "node-anim_x-4242.json").read_bytes() == b'{"a": 1}'


def test_a_handler_python_did_not_set_is_left_alone(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    stamps: list[tuple[list[str], str | None]],
) -> None:
    """Python could not set it back, and every later Ctrl-C would be held for good."""
    held = signal.SIGINT
    getsignal, setsignal = signal.getsignal, signal.signal

    def not_from_python(sig: int) -> object:
        return None if sig == held else getsignal(sig)

    def only_others(sig: int, handler: object) -> object:
        if sig == held:
            pytest.fail("a handler Python did not set was replaced")
        return setsignal(sig, handler)  # type: ignore[arg-type]

    monkeypatch.setattr(signal, "getsignal", not_from_python)
    monkeypatch.setattr(signal, "signal", only_others)
    header, buffers = _clip_frame()
    reason = clip_transport.accept(
        header,
        buffers,
        current={"anim_x": "f00d"},
        expect=_EXPECT,
        places=_places(tmp_path),
    )
    assert reason is None


def test_a_file_left_aside_by_a_killed_run_is_never_put_back(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    stamps: list[tuple[list[str], str | None]],
) -> None:
    """A move that failed was not made, so undoing it leaves the file where it is.

    A run killed between its moves leaves the file it had set aside under
    its hidden name; the next run's first move fails here, and the file of
    the earlier run stays, not the killed run's.
    """
    places = _places(tmp_path)
    names = _earlier_run(places)
    (places.clips / f".{names[0]}.previous").write_bytes(b"a killed run's")
    _moves(monkeypatch, {1: _cannot_move})
    header, buffers = _clip_frame()
    with pytest.raises(OSError, match=r"cannot be moved"):
        clip_transport.accept(
            header, buffers, current={"anim_x": "f00d"}, expect=_EXPECT, places=places
        )
    monkeypatch.setattr(pathlib.Path, "replace", _REPLACE)
    assert (places.clips / names[0]).read_bytes() == b"earlier run"


def test_a_set_aside_file_that_cannot_be_removed_does_not_fail_a_landed_clip(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    stamps: list[tuple[list[str], str | None]],
) -> None:
    """Every file of the clip is in place by then: what is left is a hidden file the next run moves over."""
    places = _places(tmp_path)
    names = _earlier_run(places)
    removed = pathlib.Path.unlink

    def unlink(path: pathlib.Path, *, missing_ok: bool = False) -> None:
        if path.name.endswith(".previous") and path.exists():
            msg = "a file that cannot be removed"
            raise OSError(msg)
        removed(path, missing_ok=missing_ok)

    monkeypatch.setattr(pathlib.Path, "unlink", unlink)
    header, buffers = _clip_frame()
    reason = clip_transport.accept(
        header, buffers, current={"anim_x": "f00d"}, expect=_EXPECT, places=places
    )
    monkeypatch.setattr(pathlib.Path, "unlink", _UNLINK)
    assert reason is None
    assert all((places.clips / name).read_bytes() != b"earlier run" for name in names)
    assert stamps == [(["anim_x"], "av1_nvenc")]
    assert (places.clips / f".{names[0]}.previous").exists()
    # The next landing of the clip removes what this one could not.
    reason = clip_transport.accept(
        header, buffers, current={"anim_x": "f00d"}, expect=_EXPECT, places=places
    )
    assert reason is None
    assert not any(path.name.startswith(".") for path in places.clips.iterdir())


def test_a_killed_run_s_hidden_files_go_with_the_next_landing(
    tmp_path: pathlib.Path,
    stamps: list[tuple[list[str], str | None]],
) -> None:
    """A run killed after it set the clip's files aside and moved two in leaves hidden files.

    The next landing of the clip removes every one of them: the assets
    checkout would otherwise publish them.
    """
    places = _places(tmp_path)
    assert places.fragments is not None
    names = _earlier_run(places)
    for name in names[2:]:
        (places.clips / name).rename(places.clips / f".{name}.previous")
    stale = places.fragments / "node-anim_x-1111.json"
    stale.rename(places.fragments / ".node-anim_x-1111.json.previous")
    header, buffers = _clip_frame()
    reason = clip_transport.accept(
        header, buffers, current={"anim_x": "f00d"}, expect=_EXPECT, places=places
    )
    assert reason is None
    hidden = [
        path.name
        for folder in (places.clips, places.fragments)
        for path in folder.iterdir()
        if path.name.startswith(".")
    ]
    assert hidden == []
    assert sorted(_left(places)) == sorted([*names, "node-anim_x-4242.json"])


def test_a_clip_is_stamped_with_the_fingerprint_it_was_compared_with(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The stamp takes the fingerprints the run took on the tree it sent, not every clip's again.

    Taking them all takes from twenty seconds to a minute, for each clip the
    run copies, and the tree they were taken on is the run's own, which
    nothing changes.
    """
    import animation_fingerprint

    def again(root: pathlib.Path) -> dict[str, str]:
        pytest.fail("the stamp took every clip's fingerprint again")

    monkeypatch.setattr(animation_fingerprint, "MANIFEST", tmp_path / "manifest.txt")
    monkeypatch.setattr(animation_fingerprint, "fingerprints", again)
    header, buffers = _clip_frame()
    reason = clip_transport.accept(
        header,
        buffers,
        current={"anim_x": "f00d"},
        expect=_EXPECT,
        places=_places(tmp_path),
    )
    assert reason is None
    assert animation_fingerprint.read_manifest() == {"anim_x": "f00d"}
    assert animation_fingerprint.read_encoders() == {"anim_x": "av1_nvenc"}


def _stream(*frames: tuple[dict[str, Any], list[bytes]], cut: int = 0) -> io.BytesIO:
    out = io.BytesIO()
    for header, buffers in frames:
        clip_link.send(out, header, buffers)
    data = out.getvalue()
    return io.BytesIO(data[: len(data) - cut] if cut else data)


def test_a_stream_that_ends_early_keeps_only_the_finished_clips(
    tmp_path: pathlib.Path, stamps: list[tuple[list[str], str | None]]
) -> None:
    expect = clip_transport.Expect(
        clips=frozenset({"anim_x", "anim_y"}), encoder="av1_nvenc", audit_only=False
    )
    stream = _stream(
        _clip_frame("anim_x"), _clip_frame("anim_y", fingerprint="f00e"), cut=20
    )
    problems = clip_transport.receive_all(
        stream,
        expect=expect,
        places=_places(tmp_path),
        current={"anim_x": "f00d", "anim_y": "f00e"},
        still=lambda: True,
    )
    assert problems == ["anim_y: the node stopped before sending it"]
    assert stamps == [(["anim_x"], "av1_nvenc")]
    assert not any(p.name.startswith("anim_y") for p in (tmp_path / "images").iterdir())


def test_the_runs_own_stamps_do_not_stop_the_next_clip(
    repo: pathlib.Path, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The manifest is tracked: the first stamp changes it, and the second clip still lands."""
    import animation_fingerprint

    monkeypatch.setattr(
        animation_fingerprint,
        "MANIFEST",
        repo / "scripts" / "animation_fingerprints.txt",
    )
    monkeypatch.setattr(
        animation_fingerprint,
        "fingerprints",
        lambda root: {"anim_x": "f00d", "anim_y": "f00e"},
    )
    head = clip_transport._head(repo)
    expect = clip_transport.Expect(
        clips=frozenset({"anim_x", "anim_y"}), encoder="av1_nvenc", audit_only=False
    )
    stream = _stream(
        _clip_frame("anim_x"),
        _clip_frame("anim_y", fingerprint="f00e"),
        ({"type": "done"}, []),
    )
    problems = clip_transport.receive_all(
        stream,
        expect=expect,
        places=_places(tmp_path),
        current={"anim_x": "f00d", "anim_y": "f00e"},
        still=lambda: clip_transport.unmoved(repo, head),
    )
    assert problems == []
    assert animation_fingerprint.read_manifest() == {"anim_x": "f00d", "anim_y": "f00e"}
    assert "scripts/animation_fingerprints.txt" in _git(repo, "status", "--porcelain")


def test_a_refusal_carries_the_nodes_reasons(tmp_path: pathlib.Path) -> None:
    stream = _stream(
        ({"type": "refused", "problems": ["ffmpeg has no av1_nvenc encoder"]}, [])
    )
    places = _places(tmp_path)
    with pytest.raises(RuntimeError, match=r"no av1_nvenc encoder"):
        clip_transport.receive_all(
            stream, expect=_EXPECT, places=places, current={}, still=lambda: True
        )


#: An OSC 52 sequence, which some terminals take as a write to the clipboard.
_ESCAPE = "\x1b]52;c;ZXZpbA==\x07"


def test_text_from_the_node_reaches_the_terminal_escaped(
    tmp_path: pathlib.Path,
) -> None:
    """A failed clip's log tail and a refusal's reasons are the node's words, shown escaped."""
    failed = {
        "type": "clip",
        "clip": "anim_x",
        "ok": False,
        "error": f"Traceback\n  boom{_ESCAPE}",
    }
    problems = clip_transport.receive_all(
        _stream((failed, []), ({"type": "done"}, [])),
        expect=_EXPECT,
        places=_places(tmp_path),
        current={"anim_x": "f00d"},
        still=lambda: True,
    )
    assert problems == [
        "anim_x: the node failed it:\nTraceback\n  boom\\x1b]52;c;ZXZpbA==\\x07"
    ]
    refused = {
        "type": "refused",
        "problems": [f"ffmpeg has no av1_nvenc encoder{_ESCAPE}"],
    }
    stream, places = _stream((refused, [])), _places(tmp_path)
    with pytest.raises(RuntimeError, match=r"the node cannot render") as caught:
        clip_transport.receive_all(
            stream, expect=_EXPECT, places=places, current={}, still=lambda: True
        )
    assert "\x1b" not in str(caught.value)
    assert str(caught.value).endswith("encoder\\x1b]52;c;ZXZpbA==\\x07")


def test_a_refusal_whose_reasons_are_not_a_list_is_still_read(
    tmp_path: pathlib.Path,
) -> None:
    stream = _stream(({"type": "refused", "problems": 3}, []))
    places = _places(tmp_path)
    with pytest.raises(RuntimeError, match=r"the node cannot render: 3"):
        clip_transport.receive_all(
            stream, expect=_EXPECT, places=places, current={}, still=lambda: True
        )


def test_a_checkout_that_moves_during_the_run_stops_the_copy(
    tmp_path: pathlib.Path, stamps: list[tuple[list[str], str | None]]
) -> None:
    stream = _stream(_clip_frame("anim_x"), ({"type": "done"}, []))
    problems = clip_transport.receive_all(
        stream,
        expect=_EXPECT,
        places=_places(tmp_path),
        current={"anim_x": "f00d"},
        still=lambda: False,
    )
    assert problems == ["anim_x: the checkout moved during the run; not copied"]
    assert stamps == []


def test_a_clip_the_node_never_sent_is_named(tmp_path: pathlib.Path) -> None:
    stream = _stream(({"type": "done"}, []))
    problems = clip_transport.receive_all(
        stream, expect=_EXPECT, places=_places(tmp_path), current={}, still=lambda: True
    )
    assert problems == ["anim_x: the node never sent it"]


def _talk_to(
    program: str, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> list[str]:
    """A check sent to a node that runs *program*, a Python one, and nothing else."""
    from phonometry.simulation import Compute
    from phonometry.simulation._remote import command

    monkeypatch.setattr(command, "_SSH_PROGRAM", ("ssh",))

    def spawn(argv: list[str], **kwargs: Any) -> subprocess.Popen[bytes]:
        return subprocess.Popen([sys.executable, "-c", program], **kwargs)

    header = clip_transport.job_header(
        [],
        devices={},
        gpu_bytes={},
        host_bytes={},
        compute="cpu",
        encoder="libsvtav1",
        audit_only=False,
    )
    expect = clip_transport.Expect(
        clips=frozenset(), encoder="libsvtav1", audit_only=False
    )
    return clip_transport._talk(
        _here(),
        Compute(host="here"),
        header,
        b"0" * 64,
        lambda stream: clip_transport.receive_all(
            stream,
            expect=expect,
            places=_places(tmp_path),
            current={},
            still=lambda: True,
        ),
        spawn,
    )


def test_a_node_that_dies_before_answering_is_named(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An import error or a crash on the node is a problem with its exit status, never a yes."""
    problems = _talk_to("import sys; sys.exit(3)", tmp_path, monkeypatch)
    assert problems == [
        "the node stopped before it said it was done",
        "the node exited with status 3",
    ]


def test_what_the_node_writes_to_its_standard_error_reaches_the_terminal_escaped(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    """ssh brings the node's standard error back too: a traceback, or what a node wants to write here."""
    program = f"import sys; sys.stderr.write('Traceback\\n  boom' + {_ESCAPE!r} + '\\n'); sys.exit(1)"
    problems = _talk_to(program, tmp_path, monkeypatch)
    assert problems[-1] == "the node exited with status 1"
    shown = capfd.readouterr().err
    assert "\x1b" not in shown
    assert "Traceback\n  boom\\x1b]52;c;ZXZpbA==\\x07\n" in shown


def test_a_checkout_that_moves_stops_the_node_at_the_first_clip_it_sends(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No clip rendered after the checkout moved would be copied, so the node is not left rendering them.

    The node here sends its first clip and gives the client ten seconds to
    close its input before it sends the next one.
    """
    from phonometry.simulation import Compute
    from phonometry.simulation._remote import command

    monkeypatch.setattr(command, "_SSH_PROGRAM", ("ssh",))
    first = _stream(_clip_frame("anim_x")).getvalue()
    rest = _stream(_clip_frame("anim_y"), ({"type": "done"}, [])).getvalue()
    program = (
        "import sys, threading\n"
        "closed = threading.Event()\n"
        "def drain():\n"
        "    sys.stdin.buffer.read()\n"
        "    closed.set()\n"
        "threading.Thread(target=drain, daemon=True).start()\n"
        f"sys.stdout.buffer.write({first!r})\n"
        "sys.stdout.buffer.flush()\n"
        "if not closed.wait(10):\n"
        f"    sys.stdout.buffer.write({rest!r})\n"
        "    sys.stdout.buffer.flush()\n"
        "    closed.wait(60)\n"
    )

    def spawn(argv: list[str], **kwargs: Any) -> subprocess.Popen[bytes]:
        return subprocess.Popen([sys.executable, "-c", program], **kwargs)

    expect = clip_transport.Expect(
        clips=frozenset({"anim_x", "anim_y"}), encoder="av1_nvenc", audit_only=False
    )
    problems = clip_transport._talk(
        _here(),
        Compute(host="here"),
        clip_transport.job_header(
            sorted(expect.clips),
            devices={},
            gpu_bytes={},
            host_bytes={},
            compute="cpu",
            encoder="av1_nvenc",
            audit_only=False,
        ),
        b"0" * 64,
        lambda stream: clip_transport.receive_all(
            stream,
            expect=expect,
            places=_places(tmp_path),
            current={"anim_x": "f00d", "anim_y": "f00d"},
            still=lambda: False,
        ),
        spawn,
    )
    assert problems == [
        "anim_x: the checkout moved during the run; not copied",
        "anim_y: the checkout moved during the run; not read; the node was stopped",
    ]


@pytest.mark.skipif(sys.platform == "win32", reason="a session is POSIX")
def test_the_connection_leads_a_session_of_its_own(
    repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ctrl-C at the terminal reaches this process and not ssh, so the node is told to stop, not cut off."""
    from phonometry.simulation import Compute
    from phonometry.simulation._remote import command

    monkeypatch.setattr(clip_link, "host_entry", lambda name: _here())
    monkeypatch.setattr(command, "_SSH_PROGRAM", ("ssh",))
    answer = _answering(({"type": "done"}, []))
    sessions: list[tuple[int, int]] = []

    def spawn(argv: list[str], **kwargs: Any) -> subprocess.Popen[bytes]:
        # Popen returns once the program runs, so its session is set by then.
        process = answer(argv, **kwargs)
        sessions.append((process.pid, os.getsid(process.pid)))
        return process

    found = clip_transport.check_node(
        Compute(host="here"), encoder="libsvtav1", root=repo, spawn=spawn
    )
    assert found == []
    ((pid, session),) = sessions
    assert session == pid


class _InterruptedInItsGrace(subprocess.Popen[bytes]):
    """ssh, and a second Ctrl-C at the terminal while the node is given its grace.

    The first wait is the grace; whatever waits after it is let through.
    """

    interrupted = False

    def wait(self, timeout: float | None = None) -> int:
        if not self.interrupted:
            self.interrupted = True
            raise KeyboardInterrupt
        return super().wait(timeout)


def _relayed(process: subprocess.Popen[bytes]) -> threading.Thread:
    relay = threading.Thread(
        target=clip_transport._relay, args=(process.stderr,), daemon=True
    )
    relay.start()
    return relay


def test_a_second_interrupt_while_the_node_is_given_its_grace_still_ends_ssh() -> None:
    """ssh leads a session of its own, which nothing else at the terminal ends: it is never left behind."""
    process = _InterruptedInItsGrace(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    relay = _relayed(process)
    try:
        with pytest.raises(KeyboardInterrupt):
            clip_transport._end(process, relay)
        assert process.poll() is not None, "ssh outlived a second interrupt"
    finally:
        process.kill()
        process.wait(timeout=30)
        relay.join(timeout=30)


def _sleeping(**kwargs: Any) -> subprocess.Popen[bytes]:
    """ssh, stood in for by a program that waits a minute for nothing."""
    return subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"], **kwargs
    )


def _ended(process: subprocess.Popen[bytes]) -> None:
    """Kill *process* if it is still there, reap it and close its pipes."""
    process.kill()
    process.wait(timeout=30)
    for stream in (process.stdin, process.stdout, process.stderr):
        if stream is not None:
            stream.close()


def test_an_interrupt_as_the_node_s_output_is_closed_still_ends_ssh(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Closing the node's output is the first step of ending it, and inside what kills ssh."""
    process = _sleeping(
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    relay = _relayed(process)
    output = process.stdout

    class _InterruptedAsItCloses:
        def close(self) -> None:
            msg = "an interrupt as the output closes"
            raise KeyboardInterrupt(msg)

    monkeypatch.setattr(process, "stdout", _InterruptedAsItCloses())
    try:
        with pytest.raises(KeyboardInterrupt, match=r"as the output closes"):
            clip_transport._end(process, relay)
        assert process.poll() is not None, "ssh outlived the interrupt"
    finally:
        monkeypatch.setattr(process, "stdout", output)
        _ended(process)
        relay.join(timeout=30)


def test_an_interrupt_before_the_node_is_talked_to_still_ends_ssh(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ssh leads a session of its own from the moment it starts, which an interrupt here does not reach."""
    from phonometry.simulation import Compute
    from phonometry.simulation._remote import command

    monkeypatch.setattr(command, "_SSH_PROGRAM", ("ssh",))
    started: list[subprocess.Popen[bytes]] = []

    def spawn(argv: list[str], **kwargs: Any) -> subprocess.Popen[bytes]:
        process = _sleeping(**kwargs)
        started.append(process)
        return process

    class _InterruptedAsItStarts(threading.Thread):
        def start(self) -> None:
            msg = "an interrupt as the relay starts"
            raise KeyboardInterrupt(msg)

    monkeypatch.setattr(
        clip_transport,
        "threading",
        types.SimpleNamespace(Thread=_InterruptedAsItStarts),
    )
    header = clip_transport.job_header(
        [],
        devices={},
        gpu_bytes={},
        host_bytes={},
        compute="cpu",
        encoder="libsvtav1",
        audit_only=False,
    )
    entry, compute = _here(), Compute(host="here")

    def receive(stream: BinaryIO) -> list[str]:
        pytest.fail("the node was read after an interrupt")

    try:
        with pytest.raises(KeyboardInterrupt, match=r"as the relay starts"):
            clip_transport._talk(entry, compute, header, b"0" * 64, receive, spawn)
        (process,) = started
        assert process.poll() is not None, "ssh outlived the interrupt"
    finally:
        for process in started:
            _ended(process)


@pytest.mark.skipif(sys.platform == "win32", reason="a kill on Windows says no signal")
def test_a_node_blocked_sending_ends_without_waiting_out_its_grace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Once the client stops reading, a node in the middle of a send learns it at once.

    Its output is closed before the grace begins, so the send fails and the
    node ends of itself instead of being killed when the grace runs out.
    """
    monkeypatch.setattr(clip_transport, "EXIT_GRACE_S", 20.0)
    sending = "import sys; sys.stdout.buffer.write(b'0' * (8 << 20)); sys.stdout.buffer.flush()"
    process = subprocess.Popen(
        [sys.executable, "-c", sending],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    relay = _relayed(process)
    try:
        clip_transport._end(process, relay)
        assert process.returncode is not None
        assert process.returncode != -signal.SIGKILL, (
            "the node was waited out and killed"
        )
    finally:
        process.kill()
        process.wait(timeout=30)
        relay.join(timeout=30)


def _answering(
    *frames: tuple[dict[str, Any], list[bytes]],
) -> Callable[..., subprocess.Popen[bytes]]:
    """A node that sends *frames* whatever it is sent, then reads its input to the end."""
    program = (
        "import sys\n"
        f"sys.stdout.buffer.write({_stream(*frames).getvalue()!r})\n"
        "sys.stdout.buffer.flush()\n"
        "sys.stdin.buffer.read()\n"
    )

    def spawn(argv: list[str], **kwargs: Any) -> subprocess.Popen[bytes]:
        return subprocess.Popen([sys.executable, "-c", program], **kwargs)

    return spawn


def test_a_run_stamps_each_clip_on_the_tree_it_sent(
    repo: pathlib.Path, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The fingerprints are taken on HEAD as the node was sent it, never on the working tree.

    An edit saved while a clip is copied would otherwise be stamped as the
    code that clip was rendered from. They are taken once: each stamp is
    handed those the clip was compared with.
    """
    import animation_fingerprint
    import assets_dir

    from phonometry.simulation import Compute
    from phonometry.simulation._remote import command

    trees: list[pathlib.Path] = []
    stamped: list[
        tuple[list[str], pathlib.Path | None, str | None, Mapping[str, str] | None]
    ] = []

    def fingerprints(root: pathlib.Path) -> dict[str, str]:
        # The archive's tree: what a render reads of HEAD, and nothing else.
        assert (root / "scripts" / "b.py").is_file()
        assert not (root / "docs").exists()
        trees.append(root)
        return {"anim_x": "f00d"}

    def stamp(
        clips: list[str],
        root: pathlib.Path | None = None,
        *,
        encoder: str | None,
        current: Mapping[str, str] | None = None,
    ) -> None:
        stamped.append((list(clips), root, encoder, current))

    monkeypatch.setattr(animation_fingerprint, "fingerprints", fingerprints)
    monkeypatch.setattr(animation_fingerprint, "stamp", stamp)
    monkeypatch.setattr(
        animation_fingerprint,
        "MANIFEST",
        repo / "scripts" / "animation_fingerprints.txt",
    )
    monkeypatch.setattr(check_animation_freshness, "published", lambda manifest: set())
    monkeypatch.setattr(clip_link, "host_entry", lambda name: _here())
    monkeypatch.setattr(assets_dir, "require_clips_dir", lambda: tmp_path / "images")
    monkeypatch.delenv("PHONOMETRY_FIGURE_LANGUAGE_AUDIT", raising=False)
    monkeypatch.setattr(command, "_SSH_PROGRAM", ("ssh",))
    run = clip_transport.render_on_host(
        Compute(host="here"),
        requested=None,
        force=False,
        audit_only=False,
        encoder="av1_nvenc",
        root=repo,
        spawn=_answering(_clip_frame("anim_x"), ({"type": "done"}, [])),
    )
    assert run == clip_transport.NodeRun(["anim_x"], [], accepted=True)
    assert sorted(p.name for p in (tmp_path / "images").iterdir()) == sorted(
        check_animation_freshness.outputs("anim_x")
    )
    (tree,) = trees
    assert tree != repo
    assert stamped == [(["anim_x"], tree, "av1_nvenc", {"anim_x": "f00d"})]


def _no_ssh(entry: HostEntry, compute: object) -> list[str]:
    msg = "no ssh client on PATH; install OpenSSH to run on a node"
    raise FileNotFoundError(msg)


def _dying(argv: list[str], **kwargs: Any) -> subprocess.Popen[bytes]:
    """A node that ends before it reads or says anything."""
    return subprocess.Popen([sys.executable, "-c", "import sys; sys.exit(3)"], **kwargs)


@pytest.mark.parametrize(
    ("answer", "error", "match"),
    [
        ("no ssh", FileNotFoundError, r"no ssh client"),
        ("refused", RuntimeError, r"the node cannot render"),
        ("dies", None, ""),
        ("done", None, ""),
    ],
)
def test_an_audit_only_run_empties_the_audit_only_once_the_node_takes_the_job(
    repo: pathlib.Path,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    answer: str,
    error: type[Exception] | None,
    match: str,
) -> None:
    """A run that never reaches the node, or that the node refuses or dies before taking, keeps the last audit."""
    import animation_fingerprint

    from phonometry.simulation import Compute
    from phonometry.simulation._remote import command

    audit = tmp_path / "audit"
    audit.mkdir()
    (audit / "anim_x_en_light.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(clip_transport, "_places_audit", lambda: audit)
    monkeypatch.setattr(
        animation_fingerprint, "fingerprints", lambda root: {"anim_x": "f00d"}
    )
    monkeypatch.setattr(clip_link, "host_entry", lambda name: _here())
    monkeypatch.setattr(command, "_SSH_PROGRAM", ("ssh",))
    monkeypatch.delenv("PHONOMETRY_FIGURE_LANGUAGE_AUDIT", raising=False)
    if answer == "no ssh":
        monkeypatch.setattr(clip_link, "node_command", _no_ssh)
    refused = {"type": "refused", "problems": ["ffmpeg is not on PATH"]}
    spawn = {
        "no ssh": _answering(),
        "refused": _answering((refused, [])),
        "dies": _dying,
        "done": _answering(({"type": "done"}, [])),
    }[answer]

    def run() -> clip_transport.NodeRun:
        return clip_transport.render_on_host(
            Compute(host="here"),
            requested=["anim_x"],
            force=False,
            audit_only=True,
            encoder="libsvtav1",
            root=repo,
            spawn=spawn,
        )

    if error is not None:
        with pytest.raises(error, match=match):
            run()
        assert [p.name for p in audit.iterdir()] == ["anim_x_en_light.json"]
        return
    outcome = run()
    taken = answer == "done"
    assert outcome.accepted is taken
    kept = [p.name for p in audit.iterdir()]
    assert kept == ([] if taken else ["anim_x_en_light.json"])


@pytest.mark.parametrize("node", ["took the job", "never took it"])
def test_an_audit_is_reported_only_when_the_node_took_the_job(
    monkeypatch: pytest.MonkeyPatch, node: str
) -> None:
    """The findings on disk are the last run's when the node never took this one."""
    import clip_frame_audit

    accepted = node == "took the job"

    from phonometry.simulation import Compute

    reported: list[list[str]] = []

    def report(directory: pathlib.Path, clips: list[str]) -> int:
        reported.append(list(clips))
        return 0

    def render_on_host(compute: Compute, **kwargs: Any) -> clip_transport.NodeRun:
        return clip_transport.NodeRun(
            ["anim_x"], ["anim_x: the node stopped before sending it"], accepted
        )

    monkeypatch.setattr(clip_frame_audit, "report", report)
    monkeypatch.setattr(clip_transport, "render_on_host", render_on_host)
    status = clip_transport.main_on_host(
        Compute(host="here"),
        requested=None,
        force=False,
        audit_only=True,
        encoder="libsvtav1",
    )
    assert status == 1
    assert reported == ([["anim_x"]] if accepted else [])


@pytest.mark.parametrize(
    ("answer", "problems"),
    [
        (({"type": "done"}, []), []),
        (
            ({"type": "refused", "problems": [f"ffmpeg is not on PATH{_ESCAPE}"]}, []),
            ["the node cannot render: ffmpeg is not on PATH\\x1b]52;c;ZXZpbA==\\x07"],
        ),
        (
            ({"type": "clip", "clip": "anim_x", "ok": False, "error": "boom"}, []),
            ["the node sent a frame nobody asked for: 'clip', 'anim_x'"],
        ),
    ],
    ids=["done", "refused", "a stray frame"],
)
def test_a_node_check_is_a_yes_only_when_the_node_says_it_is_done(
    repo: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    answer: tuple[dict[str, Any], list[bytes]],
    problems: list[str],
) -> None:
    from phonometry.simulation import Compute
    from phonometry.simulation._remote import command

    monkeypatch.setattr(clip_link, "host_entry", lambda name: _here())
    monkeypatch.setattr(command, "_SSH_PROGRAM", ("ssh",))
    found = clip_transport.check_node(
        Compute(host="here"), encoder="libsvtav1", root=repo, spawn=_answering(answer)
    )
    assert found == problems


def _digests_unread(root: pathlib.Path) -> dict[str, str]:
    msg = f"{root}/engine-digests.json is not JSON; record the engines' digests with `make engine-digests`"
    raise ValueError(msg)


@pytest.mark.parametrize(
    ("cause", "match"),
    [
        ("an archive too large", r"over the 10 a node accepts"),
        ("digests unread", r"engine-digests\.json is not JSON"),
        ("a stray frame", r"a frame nobody asked for: 'clip', 'anim_other'"),
    ],
)
def test_a_node_run_that_cannot_go_on_says_why_as_a_node_run_error(
    repo: pathlib.Path,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    cause: str,
    match: str,
) -> None:
    """What stops a run, from the archive to the frames, reaches the caller as one kind of error.

    A RuntimeError, as a refusal of the node's is, so whoever runs the clips
    on a node says it in a line rather than a traceback.
    """
    import animation_fingerprint
    import assets_dir

    from phonometry.simulation import Compute
    from phonometry.simulation._remote import command

    monkeypatch.setattr(
        animation_fingerprint, "fingerprints", lambda root: {"anim_x": "f00d"}
    )
    monkeypatch.setattr(check_animation_freshness, "published", lambda manifest: set())
    monkeypatch.setattr(clip_link, "host_entry", lambda name: _here())
    monkeypatch.setattr(assets_dir, "require_clips_dir", lambda: tmp_path / "images")
    monkeypatch.delenv("PHONOMETRY_FIGURE_LANGUAGE_AUDIT", raising=False)
    monkeypatch.setattr(command, "_SSH_PROGRAM", ("ssh",))
    stray = {"type": "clip", "clip": "anim_other", "ok": False, "error": "boom"}
    spawn = _answering((stray, []))
    if cause == "an archive too large":
        monkeypatch.setattr(clip_node, "ARCHIVE_LIMIT", 10)
    elif cause == "digests unread":
        monkeypatch.setattr(animation_fingerprint, "fingerprints", _digests_unread)
    # main_on_host renders this checkout through ssh; here, the test's own.
    defaults = clip_transport.render_on_host.__kwdefaults__
    assert defaults is not None
    monkeypatch.setitem(defaults, "root", repo)
    monkeypatch.setitem(defaults, "spawn", spawn)
    compute = Compute(host="here")
    with pytest.raises(clip_transport.NodeRunError, match=match) as raised:
        clip_transport.main_on_host(
            compute,
            requested=["anim_x"],
            force=False,
            audit_only=False,
            encoder="av1_nvenc",
        )
    assert isinstance(raised.value, RuntimeError)
    if cause != "an archive too large":
        assert isinstance(raised.value.__cause__, ValueError)


def test_a_run_from_a_checkout_with_changes_starts_no_node(
    repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from phonometry.simulation import Compute

    (repo / "scripts" / "b.py").write_text("changed\n", encoding="utf-8")

    def spawn(argv: list[str], **kwargs: Any) -> subprocess.Popen[bytes]:
        pytest.fail("a node was started from a checkout with changes")

    compute = Compute(host="here")
    with pytest.raises(clip_transport.DirtyTreeError, match=r"scripts/b\.py"):
        clip_transport.render_on_host(
            compute,
            requested=None,
            force=False,
            audit_only=False,
            encoder="av1_nvenc",
            root=repo,
            spawn=spawn,
        )


def _without_caches(info: tarfile.TarInfo) -> tarfile.TarInfo | None:
    return None if "__pycache__" in info.name else info


def _site_without_phonometry(where: pathlib.Path) -> list[str]:
    """This interpreter's site-packages, mirrored under *where* without phonometry.

    Each folder holds a link to every entry of one site-packages folder but
    phonometry's own (the package, its metadata, an editable install's
    finder) and the ``.pth`` files, which a Python started with ``-S`` never
    reads. So the node finds the figure stack where it is installed, and no
    phonometry but the archive's, as in the node image.
    """
    import site

    found = [*site.getsitepackages()]
    if site.ENABLE_USER_SITE:
        found.append(site.getusersitepackages())
    mirrors: list[str] = []
    for number, folder in enumerate(pathlib.Path(f) for f in found):
        if not folder.is_dir():
            continue
        mirror = where / f"site-{number}"
        mirror.mkdir(parents=True)
        for entry in folder.iterdir():
            own = entry.name.lower().startswith(("phonometry", "__editable__"))
            if not own and entry.suffix != ".pth":
                (mirror / entry.name).symlink_to(entry)
        mirrors.append(str(mirror))
    return mirrors


#: What the node's Python is told before its loader: the mirrored site
#: folders, after the standard library, which is all ``-I -S`` leaves it.
_SITE = "import sys\nsys.path.extend({folders!r})\n"

#: Asked of that Python first: whether it finds phonometry, its metadata,
#: and the figure stack.
_PROBE = """
import importlib.metadata, importlib.util
try:
    importlib.metadata.version("phonometry")
except importlib.metadata.PackageNotFoundError:
    metadata = False
else:
    metadata = True
print(
    importlib.util.find_spec("phonometry") is not None,
    metadata,
    all(importlib.util.find_spec(name) for name in ("numpy", "matplotlib")),
)
"""


@pytest.mark.skipif(sys.platform == "win32", reason="a render node is POSIX")
def test_the_road_through_the_loader_brings_the_nodes_refusal_back(
    repo: pathlib.Path, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Client, loader, bootstrap and node, joined by real pipes on this machine.

    The archive is what a render ships (``SHIPPED``), taken from this working
    tree, and the node's Python runs with no site of its own (``-I -S``) and
    this one's site-packages without phonometry: phonometry is not installed
    there, as in the node image, and reads its version from the archive's
    VERSION file. The client's unpacked copy of the archive is gone once
    the run is.
    """
    import animation_fingerprint
    import assets_dir

    from phonometry.simulation import Compute
    from phonometry.simulation._remote import command

    folders = _site_without_phonometry(tmp_path / "site")
    site = _SITE.format(folders=folders)
    probe = child_process.run(
        [sys.executable, "-I", "-S", "-c", site + _PROBE],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    ).stdout.split()
    if probe != ["False", "False", "True"]:
        pytest.skip(
            "this machine's Python cannot be run without phonometry and with the "
            f"figure stack (phonometry, its metadata, the stack: {probe})"
        )
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w:gz") as tar:
        for name in clip_transport.SHIPPED:
            tar.add(_ROOT / name, arcname=name, filter=_without_caches)
    archive = data.getvalue()
    sent = tmp_path / "client-tmp"
    sent.mkdir()
    trees: list[pathlib.Path] = []

    def fingerprints(root: pathlib.Path) -> dict[str, str]:
        trees.append(root)
        return {"anim_x": "f00d"}

    monkeypatch.setattr(clip_transport, "archive", lambda root, *, ref: archive)
    monkeypatch.setattr(animation_fingerprint, "fingerprints", fingerprints)
    monkeypatch.setattr(
        animation_fingerprint,
        "MANIFEST",
        repo / "scripts" / "animation_fingerprints.txt",
    )
    monkeypatch.setattr(check_animation_freshness, "published", lambda manifest: set())
    monkeypatch.setattr(clip_link, "host_entry", lambda name: _here())
    monkeypatch.setattr(assets_dir, "require_clips_dir", lambda: tmp_path / "images")
    monkeypatch.delenv("PHONOMETRY_FIGURE_LANGUAGE_AUDIT", raising=False)
    monkeypatch.setattr(command, "_SSH_PROGRAM", ("ssh",))
    monkeypatch.setattr(tempfile, "tempdir", str(sent))
    entry = _here()
    compute = Compute(host="here")
    no_ffmpeg = tmp_path / "bin"
    no_ffmpeg.mkdir()
    node_tmp = tmp_path / "node-tmp"
    node_tmp.mkdir()

    def spawn(argv: list[str], **kwargs: Any) -> subprocess.Popen[bytes]:
        # This machine's Python stands in for the node's, with no ffmpeg on
        # its PATH and a temporary directory of its own to unpack into.
        assert argv == clip_link.node_command(entry, compute)
        node = [sys.executable, "-I", "-S", "-c", site + clip_link.loader()]
        return subprocess.Popen(
            node, env={"PATH": str(no_ffmpeg), "TMPDIR": str(node_tmp)}, **kwargs
        )

    with pytest.raises(
        RuntimeError, match=r"the node cannot render: ffmpeg is not on PATH"
    ):
        clip_transport.render_on_host(
            compute,
            requested=["anim_x"],
            force=False,
            audit_only=False,
            encoder="libsvtav1",
            root=repo,
            spawn=spawn,
        )
    # The node was let finish: it removed the tree it unpacked into its TMPDIR.
    assert list(node_tmp.iterdir()) == []
    # And the client removed its own copy, which it took the fingerprints on.
    (tree,) = trees
    assert tree.parent == sent
    assert tree.name.startswith("phonometry-sent-")
    assert list(sent.iterdir()) == []
