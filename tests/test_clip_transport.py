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
import threading
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
    from collections.abc import Callable, Mapping

# The client reads the frame audit and the registry: the figure stack.
pytestmark = pytest.mark.pinned_stack

_WEBM = b"\x1aE\xdf\xa3" + b"0" * 12
_GIF = b"GIF89a" + b"0" * 10
_WEBP = b"RIFF\x00\x00\x00\x00WEBP" + b"0" * 4


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
    with pytest.raises(RuntimeError, match=r"no av1_nvenc encoder"):
        clip_transport.receive_all(
            stream,
            expect=_EXPECT,
            places=_places(tmp_path),
            current={},
            still=lambda: True,
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
    with pytest.raises(RuntimeError, match=r"the node cannot render") as caught:
        clip_transport.receive_all(
            _stream((refused, [])),
            expect=_EXPECT,
            places=_places(tmp_path),
            current={},
            still=lambda: True,
        )
    assert "\x1b" not in str(caught.value)
    assert str(caught.value).endswith("encoder\\x1b]52;c;ZXZpbA==\\x07")


def test_a_refusal_whose_reasons_are_not_a_list_is_still_read(
    tmp_path: pathlib.Path,
) -> None:
    stream = _stream(({"type": "refused", "problems": 3}, []))
    with pytest.raises(RuntimeError, match=r"the node cannot render: 3"):
        clip_transport.receive_all(
            stream,
            expect=_EXPECT,
            places=_places(tmp_path),
            current={},
            still=lambda: True,
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
        "anim_y: the checkout moved during the run; the node was stopped before it sent it",
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
    clips, problems = clip_transport.render_on_host(
        Compute(host="here"),
        requested=None,
        force=False,
        audit_only=False,
        encoder="av1_nvenc",
        root=repo,
        spawn=_answering(_clip_frame("anim_x"), ({"type": "done"}, [])),
    )
    assert (clips, problems) == (["anim_x"], [])
    assert sorted(p.name for p in (tmp_path / "images").iterdir()) == sorted(
        check_animation_freshness.outputs("anim_x")
    )
    (tree,) = trees
    assert tree != repo
    assert stamped == [(["anim_x"], tree, "av1_nvenc", {"anim_x": "f00d"})]


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


def test_a_run_from_a_checkout_with_changes_starts_no_node(
    repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from phonometry.simulation import Compute

    (repo / "scripts" / "b.py").write_text("changed\n", encoding="utf-8")

    def spawn(argv: list[str], **kwargs: Any) -> subprocess.Popen[bytes]:
        pytest.fail("a node was started from a checkout with changes")

    with pytest.raises(clip_transport.DirtyTreeError, match=r"scripts/b\.py"):
        clip_transport.render_on_host(
            Compute(host="here"),
            requested=None,
            force=False,
            audit_only=False,
            encoder="av1_nvenc",
            root=repo,
            spawn=spawn,
        )


def _without_caches(info: tarfile.TarInfo) -> tarfile.TarInfo | None:
    return None if "__pycache__" in info.name else info


#: Run before the node's loader: this machine's Python with phonometry's
#: metadata hidden, as in the node image, where phonometry is not installed
#: and reads its version from the archive's VERSION file.
_NOT_INSTALLED = (
    "import importlib.metadata as m\n"
    "_found = m.version\n"
    "def _version(name):\n"
    "    if name == 'phonometry':\n"
    "        raise m.PackageNotFoundError(name)\n"
    "    return _found(name)\n"
    "m.version = _version\n"
)


@pytest.mark.skipif(sys.platform == "win32", reason="a render node is POSIX")
def test_the_road_through_the_loader_brings_the_nodes_refusal_back(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Client, loader, bootstrap and node, joined by real pipes on this machine.

    The archive is what a render ships (``SHIPPED``), taken from this working
    tree, and the node runs where phonometry is not installed.
    """
    from phonometry.simulation import Compute
    from phonometry.simulation._remote import command

    monkeypatch.setattr(command, "_SSH_PROGRAM", ("ssh",))
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w:gz") as tar:
        for name in clip_transport.SHIPPED:
            tar.add(_ROOT / name, arcname=name, filter=_without_caches)
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
        node = [sys.executable, "-I", "-c", _NOT_INSTALLED + clip_link.loader()]
        return subprocess.Popen(
            node, env={"PATH": str(no_ffmpeg), "TMPDIR": str(node_tmp)}, **kwargs
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
    expect = clip_transport.Expect(
        clips=frozenset(), encoder="libsvtav1", audit_only=False
    )

    def receive(stream: BinaryIO) -> list[str]:
        return clip_transport.receive_all(
            stream,
            expect=expect,
            places=_places(tmp_path),
            current={},
            still=lambda: True,
        )

    with pytest.raises(
        RuntimeError, match=r"the node cannot render: ffmpeg is not on PATH"
    ):
        clip_transport._talk(entry, compute, header, data.getvalue(), receive, spawn)
    # The node was let finish: it removed the tree it unpacked into its TMPDIR.
    assert list(node_tmp.iterdir()) == []
