#  Copyright (c) 2026. Jose Manuel Requena Plens
"""At most N encodes hold an NVENC session, across processes that share a directory."""

from __future__ import annotations

import multiprocessing as mp
import os
import pathlib
import stat
import sys
import time

import child_process
import pytest

fcntl = pytest.importorskip("fcntl")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

import encode_slots

#: How long the holder keeps its slot [s].
_HOLD_S = 1.5
#: How long a spawned holder may take to start and take its slot [s].
_START_S = 60.0
#: How long the holder may take to end once its slot is released [s].
_END_S = 60.0


def _hold(directory: str, seconds: float, started: str) -> None:
    os.environ[encode_slots.SLOTS_ENV] = f"{directory}:1"
    with encode_slots.slot("av1_nvenc"):
        pathlib.Path(started).write_text(str(time.monotonic()), encoding="utf-8")
        time.sleep(seconds)


def _holder(slots: pathlib.Path, started: pathlib.Path) -> mp.process.BaseProcess:
    """A process holding the one slot of *slots* for :data:`_HOLD_S`, once it holds it."""
    holder = mp.get_context("spawn").Process(
        target=_hold, args=(str(slots), _HOLD_S, str(started))
    )
    holder.start()
    deadline = time.monotonic() + _START_S
    while not started.exists():
        if time.monotonic() > deadline:
            holder.kill()
            child_process.join(holder, timeout=_END_S)
            pytest.fail(f"the holder took no slot within {_START_S:g} s")
        time.sleep(0.05)
    return holder


def _no_lock_taken(monkeypatch: pytest.MonkeyPatch) -> list[object]:
    """Record every lock the code asks for; a slot is a lock."""
    taken: list[object] = []
    monkeypatch.setattr(fcntl, "flock", lambda *args: taken.append(args))
    return taken


def test_without_the_variable_no_slot_is_taken(monkeypatch: pytest.MonkeyPatch) -> None:
    taken = _no_lock_taken(monkeypatch)
    monkeypatch.delenv(encode_slots.SLOTS_ENV, raising=False)
    with encode_slots.slot("av1_nvenc"):
        pass
    assert taken == []


def test_a_cpu_encoder_takes_no_slot(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    taken = _no_lock_taken(monkeypatch)
    monkeypatch.setenv(encode_slots.SLOTS_ENV, f"{tmp_path / 'slots'}:1")
    with encode_slots.slot("libsvtav1"):
        pass
    assert taken == []
    assert not (tmp_path / "slots").exists()


def test_a_held_slot_makes_the_next_encode_wait(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    slots, started = tmp_path / "slots", tmp_path / "started"
    holder = _holder(slots, started)
    monkeypatch.setenv(encode_slots.SLOTS_ENV, f"{slots}:1")
    t0 = time.monotonic()
    with encode_slots.slot("av1_nvenc"):
        waited = time.monotonic() - t0
    child_process.join(holder, timeout=_END_S)
    assert waited > 0.5


def test_a_second_slot_lets_a_second_encode_through(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    slots, started = tmp_path / "slots", tmp_path / "started"
    holder = _holder(slots, started)
    monkeypatch.setenv(encode_slots.SLOTS_ENV, f"{slots}:2")
    t0 = time.monotonic()
    with encode_slots.slot("av1_nvenc"):
        waited = time.monotonic() - t0
    child_process.join(holder, timeout=_END_S)
    assert waited < 0.5


@pytest.mark.parametrize("text", [":2", "slots:0", "slots:two", "slots"])
def test_a_malformed_variable_is_refused(
    monkeypatch: pytest.MonkeyPatch, text: str
) -> None:
    monkeypatch.setenv(encode_slots.SLOTS_ENV, text)
    with (
        pytest.raises(ValueError, match=r"PHONOMETRY_ENCODE_SLOTS"),
        encode_slots.slot("av1_nvenc"),
    ):
        pass


def _take_a_slot(monkeypatch: pytest.MonkeyPatch, slots: pathlib.Path) -> None:
    """Take and give back the one slot of *slots*, as a GPU encode does."""
    monkeypatch.setenv(encode_slots.SLOTS_ENV, f"{slots}:1")
    with encode_slots.slot("av1_nvenc"):
        pass


def test_the_slots_directory_is_made_private(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Nobody else may list it or plant anything in it."""
    slots = tmp_path / "slots"
    _take_a_slot(monkeypatch, slots)
    assert stat.S_IMODE(slots.stat().st_mode) == 0o700
    assert stat.S_IMODE((slots / "slot-0.lock").stat().st_mode) == 0o600


@pytest.mark.parametrize("mode", [0o777, 0o755, 0o720], ids=["777", "755", "720"])
def test_a_slots_directory_open_to_others_is_refused(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path, mode: int
) -> None:
    slots = tmp_path / "slots"
    slots.mkdir()
    slots.chmod(mode)
    with pytest.raises(PermissionError, match=rf"is open to others \(mode {mode:o}\)"):
        _take_a_slot(monkeypatch, slots)
    assert list(slots.iterdir()) == []


def test_a_slots_directory_of_another_user_is_refused(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Another user made it first: this run is not who the directory belongs to."""
    slots = tmp_path / "slots"
    slots.mkdir(mode=0o700)
    owner = slots.stat().st_uid
    monkeypatch.setattr(encode_slots.os, "geteuid", lambda: owner + 1)
    with pytest.raises(PermissionError, match=rf"belongs to user {owner}, not to"):
        _take_a_slot(monkeypatch, slots)
    assert list(slots.iterdir()) == []


def test_a_slots_directory_that_is_a_link_is_refused(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """A link planted where the directory goes would send the lock files elsewhere."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir(mode=0o700)
    slots = tmp_path / "slots"
    slots.symlink_to(elsewhere, target_is_directory=True)
    with pytest.raises(PermissionError, match=r"is a link or not a directory"):
        _take_a_slot(monkeypatch, slots)
    assert list(elsewhere.iterdir()) == []


def test_a_lock_file_that_is_a_link_is_refused_and_its_target_left_alone(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """A link where a lock file goes is never followed, so the file it names is not touched."""
    slots = tmp_path / "slots"
    slots.mkdir(mode=0o700)
    victim = tmp_path / "victim.txt"
    victim.write_text("kept\n", encoding="utf-8")
    (slots / "slot-0.lock").symlink_to(victim)
    with pytest.raises(PermissionError, match=r"slot-0\.lock is a link"):
        _take_a_slot(monkeypatch, slots)
    assert victim.read_text(encoding="utf-8") == "kept\n"


def test_this_machine_s_slots_are_this_user_s_own(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """A render on this machine's GPU keeps its slots in a directory of this user's."""
    monkeypatch.setattr(encode_slots.tempfile, "gettempdir", lambda: str(tmp_path))
    assert encode_slots.shared_directory() == (
        tmp_path / f"phonometry-encode-slots-{os.geteuid()}"
    )


@pytest.mark.parametrize("planted", ["file", "dangling-link", "link-to-a-file"])
def test_something_other_than_a_directory_where_the_slots_go_is_refused(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path, planted: str
) -> None:
    """A file, or a link to one or to nothing, is refused as such, not by the mkdir that meets it."""
    slots = tmp_path / "slots"
    target = tmp_path / "target.txt"
    if planted == "file":
        slots.write_text("kept\n", encoding="utf-8")
    else:
        if planted == "link-to-a-file":
            target.write_text("kept\n", encoding="utf-8")
        slots.symlink_to(target)
    with pytest.raises(PermissionError, match=r"slots is a link or not a directory$"):
        _take_a_slot(monkeypatch, slots)
    if planted != "dangling-link":
        assert slots.read_text(encoding="utf-8") == "kept\n"


def test_a_directory_swapped_for_a_link_once_checked_cannot_redirect_a_lock(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """The lock files are opened in the directory that was checked, not wherever its path leads now."""
    slots, moved, elsewhere = (
        tmp_path / "slots",
        tmp_path / "moved",
        tmp_path / "elsewhere",
    )
    elsewhere.mkdir(mode=0o700)
    checked = encode_slots._private

    def check_then_swap(directory: pathlib.Path) -> object:
        held = checked(directory)
        directory.rename(moved)
        directory.symlink_to(elsewhere, target_is_directory=True)
        return held

    monkeypatch.setattr(encode_slots, "_private", check_then_swap)
    _take_a_slot(monkeypatch, slots)
    assert list(elsewhere.iterdir()) == []
    assert (moved / "slot-0.lock").is_file()


def test_a_slot_never_truncates_the_lock_file_it_takes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """A lock file is opened, never rewritten: the bytes in it before survive the slot."""
    slots = tmp_path / "slots"
    slots.mkdir(mode=0o700)
    lock = slots / "slot-0.lock"
    lock.write_bytes(b"held before\n")
    lock.chmod(0o600)
    _take_a_slot(monkeypatch, slots)
    assert lock.read_bytes() == b"held before\n"
