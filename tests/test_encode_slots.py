#  Copyright (c) 2026. Jose Manuel Requena Plens
"""At most N encodes hold an NVENC session, across processes that share a directory."""

from __future__ import annotations

import multiprocessing as mp
import os
import pathlib
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
