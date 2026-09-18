#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The clips checkout and the step that publishes a render from it.

``scripts/assets_dir.py`` says where the clips are rendered into and
``scripts/publish_assets.py`` commits and pushes what a render left there.
Neither may touch the real checkout from a test, so these build a throwaway
repository with a bare ``origin`` and point the resolver at it.

Three things have to hold. A render is published as one commit whose message
names the clip and the code it came from, and the lock records that commit.
A checkout that is not safe to publish from is refused before anything is
committed, whether because it is on another branch or because it carries
changes that are not clips. And the refusal reads the path correctly: a
first version stripped the leading space of ``git status --porcelain`` and
so read ``images/x`` as ``mages/x``, refusing every render as a stray file.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import assets_dir
import publish_assets


def _git(cwd: pathlib.Path, *args: str) -> str:
    # rstrip and not strip, for the same reason the script does: the porcelain
    # status of an unstaged change begins with a space that is part of it.
    return subprocess.run(  # noqa: S603
        ["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True
    ).stdout.rstrip("\n")


@pytest.fixture
def checkout(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """A clone of a bare origin, on main, with one published clip."""
    origin = tmp_path / "origin.git"
    _git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    work = tmp_path / "phonometry-assets"
    _git(tmp_path, "clone", "-q", str(origin), str(work))
    _git(work, "config", "user.email", "t@example.invalid")
    _git(work, "config", "user.name", "t")
    _git(work, "checkout", "-q", "-b", "main")
    (work / "images").mkdir()
    (work / "images" / "anim_one.webm").write_bytes(b"v1")
    _git(work, "add", "-A")
    _git(work, "commit", "-q", "-m", "seed")
    _git(work, "push", "-q", "-u", "origin", "main")
    lock = tmp_path / "assets.lock"
    monkeypatch.setattr(assets_dir, "clips_dir", lambda: work / "images")
    monkeypatch.setattr(assets_dir, "LOCK", lock)
    monkeypatch.setattr(publish_assets, "_head_here", lambda: "abc1234")
    return work


def test_a_render_is_published_as_one_commit_and_locked(checkout: pathlib.Path) -> None:
    (checkout / "images" / "anim_one.webm").write_bytes(b"v2")
    (checkout / "images" / "anim_one_es_poster.webp").write_bytes(b"p")
    assert publish_assets.publish(dry_run=False) == 0
    head = _git(checkout, "rev-parse", "HEAD")
    assert _git(checkout, "rev-parse", "origin/main") == head
    assert assets_dir.LOCK.read_text() == head + "\n"
    subject = _git(checkout, "log", "-1", "--format=%s")
    assert subject == "Rendered anim_one from phonometry abc1234"
    body = _git(checkout, "log", "-1", "--format=%b")
    assert "anim_one.webm" in body
    assert "anim_one_es_poster.webp" in body


def test_nothing_to_publish_makes_no_commit(checkout: pathlib.Path) -> None:
    before = _git(checkout, "rev-parse", "HEAD")
    assert publish_assets.publish(dry_run=False) == 0
    assert _git(checkout, "rev-parse", "HEAD") == before
    assert not assets_dir.LOCK.exists()


def test_a_dry_run_commits_nothing_and_leaves_the_tree_as_it_was(
    checkout: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (checkout / "images" / "anim_one.webm").write_bytes(b"v2")
    before = _git(checkout, "rev-parse", "HEAD")
    assert publish_assets.publish(dry_run=True) == 0
    assert _git(checkout, "rev-parse", "HEAD") == before
    assert "would commit and push 1 file(s)" in capsys.readouterr().out
    assert _git(checkout, "status", "--porcelain") == " M images/anim_one.webm"


def test_a_changed_clip_is_a_clip_and_not_a_stray_file(checkout: pathlib.Path) -> None:
    """The porcelain line for an unstaged change starts with a space.

    Stripping it shifted the path by one column and the filter that keeps
    strays out read every rendered clip as ``mages/...``, outside ``images/``,
    and refused the render it was written to publish.
    """
    (checkout / "images" / "anim_one.webm").write_bytes(b"v2")
    publish_assets.refuse_unless_publishable(checkout)


def test_a_stray_file_outside_images_is_refused(checkout: pathlib.Path) -> None:
    (checkout / "notes.txt").write_text("x")
    with pytest.raises(RuntimeError, match="changes outside images/ \\(notes.txt\\)"):
        publish_assets.refuse_unless_publishable(checkout)


def test_a_checkout_off_main_is_refused(checkout: pathlib.Path) -> None:
    _git(checkout, "checkout", "-q", "-b", "scratch")
    with pytest.raises(RuntimeError, match="is on 'scratch', not main"):
        publish_assets.refuse_unless_publishable(checkout)


@pytest.mark.parametrize(
    ("names", "expected"),
    [
        (["anim_a.webm", "anim_a_es_dark.webm", "anim_a_poster.webp"], "anim_a"),
        (["anim_a.webm", "anim_b_dark.gif"], "anim_a, anim_b"),
        ([f"anim_{i}.webm" for i in range(5)], "5 clips"),
    ],
)
def test_the_message_names_what_was_rendered(names: list[str], expected: str) -> None:
    assert publish_assets.message(names, "abc1234").startswith(
        f"Rendered {expected} from phonometry abc1234"
    )


def test_the_resolver_honours_the_variable_and_falls_back_to_the_sibling(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    monkeypatch.setattr(assets_dir.fdtd_gpu_remote, "load_env", dict)
    monkeypatch.setenv(assets_dir.VARIABLE, str(tmp_path / "elsewhere"))
    assert assets_dir.clips_dir() == tmp_path / "elsewhere"
    monkeypatch.delenv(assets_dir.VARIABLE)
    assert assets_dir.clips_dir() == assets_dir.default_dir()
    assert assets_dir.default_dir().name == "images"
    assert assets_dir.default_dir().parent.name == "phonometry-assets"


def test_a_missing_checkout_is_named_before_anything_renders(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    monkeypatch.setattr(
        assets_dir, "clips_dir", lambda: tmp_path / "nowhere" / "images"
    )
    with pytest.raises(FileNotFoundError, match="Run `make assets`"):
        assets_dir.require_clips_dir()
