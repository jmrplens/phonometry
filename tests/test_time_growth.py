#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The timing helper of the linear-time tests reads how time grows (``time_growth``).

The tests that time a reader hand the helper only readers that pass, so a
change that let quadratic work through, read a coarse clock one call at a
time, read one size every time before the other, kept a reading other
processes lengthened or left the garbage collector off would pass them all.
These tests hand it work whose cost they set, timed on a clock they drive:
:class:`_Clock` stands in for the CPU time of the process, each call of
:class:`_Work` moves it on by what its input costs, and it reads in steps, as
the system's clock does. Every cost and every step is a power of two, so every
reading is exact. Two tests read the clock of the process itself: a wait on
the wall is not charged to a reading, and the work of another thread is.
"""

from __future__ import annotations

import dataclasses
import gc
import math
import re
import threading
import time
from collections import Counter
from typing import TYPE_CHECKING

import pytest
import time_growth

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping

#: A step of the CPU-time clock as Windows counts it, the scheduler's tick of
#: 1/64 s [s].
_COARSE_STEP_S = 2.0**-6
#: A step as fine as Linux and macOS count it, about a microsecond [s].
_FINE_STEP_S = 2.0**-20
#: What a call over the smaller input costs, about a millisecond [s].
_COST_S = 2.0**-10
#: The size of the smaller input.
_SIZE = 16
#: The size of the larger input.
_LARGE = time_growth.FACTOR * _SIZE
#: What a call costs over each input of linear work [s].
_LINEAR_S = {_SIZE: _COST_S, _LARGE: time_growth.FACTOR * _COST_S}
#: How long a test waits on the wall for a thread that takes a twentieth of a
#: second of CPU time, long past what a busy machine takes to give it that [s].
_THREAD_WAIT_S = 30.0


@dataclasses.dataclass
class _Clock:
    """The CPU time of a process the test drives [s], read in steps of :attr:`step_s`."""

    #: The step the clock reads in [s].
    step_s: float
    #: The time the process has taken so far [s].
    now_s: float = 0.0

    def read(self) -> float:
        """The time taken so far, down to the step it falls in [s]."""
        return math.floor(self.now_s / self.step_s) * self.step_s


@dataclasses.dataclass
class _Work:
    """A reader whose calls cost what the test sets, on the test's clock.

    Its input is a size, and a call over it moves the clock on by what that
    size costs and returns the size and the place of the call among the calls
    over it, from 0. It keeps how many calls each size took and whether the
    garbage collector was on at each call.
    """

    clock: _Clock
    #: What one call costs, by the size of its input [s].
    costs_s: Mapping[int, float]
    #: What else a call costs, by the size of its input and the place of the
    #: call among the calls over that size, from 0 [s].
    extra_s: Mapping[tuple[int, int], float] = dataclasses.field(default_factory=dict)
    #: How many calls each size took.
    calls: Counter[int] = dataclasses.field(default_factory=Counter)
    #: Whether the garbage collector was on at each call, in turn.
    collecting: list[bool] = dataclasses.field(default_factory=list)

    def __call__(self, size: int) -> tuple[int, int]:
        """The size read and the place of the call, the clock moved on by what
        reading it cost.
        """
        place = self.calls[size]
        self.calls[size] += 1
        self.collecting.append(gc.isenabled())
        self.clock.now_s += self.costs_s[size] + self.extra_s.get((size, place), 0.0)
        return size, place


def _clock(monkeypatch: pytest.MonkeyPatch, step_s: float) -> _Clock:
    """A clock of *step_s* steps the helper reads for the CPU time of the process."""
    clock = _Clock(step_s)
    monkeypatch.setattr(time_growth, "_cpu_time", clock.read)
    monkeypatch.setattr(time_growth, "_clock_step", lambda: step_s)
    return clock


def _as_built(size: int) -> int:
    """The input of *size*: the size itself, which :class:`_Work` reads."""
    return size


def _spin(seconds: float) -> None:
    """Keep the calling thread at work until it has taken *seconds* of CPU time."""
    start = time.thread_time()
    while time.thread_time() - start < seconds:
        pass


@pytest.fixture(autouse=True)
def _collector_as_found() -> Iterator[None]:
    """The garbage collector left on or off as the test found it, whatever it did."""
    collecting = gc.isenabled()
    yield
    if collecting:
        gc.enable()
    else:
        gc.disable()


@pytest.mark.parametrize(
    ("assertion", "ratio"),
    [
        (time_growth.assert_linear_time, 8.0),
        (time_growth.assert_linear_time, 22.5),
        (time_growth.assert_time_does_not_grow, 1.0),
        (time_growth.assert_time_does_not_grow, 2.75),
    ],
)
def test_growth_under_the_bound_passes_and_hands_back_what_was_read(
    assertion: Callable[..., time_growth.Growth[tuple[int, int]]],
    ratio: float,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Linear work and work that does not grow pass, and so does work that grows
    just under the bound: 22.5 times against 8 ** 1.5 = 22.63, and 2.75 times
    against 8 ** 0.5 = 2.83. What is handed back is what the last call over the
    larger input returned, the fifth.
    """
    clock = _clock(monkeypatch, _FINE_STEP_S)
    work = _Work(clock, {_SIZE: _COST_S, _LARGE: ratio * _COST_S})
    growth = assertion(_as_built, work, _SIZE)
    assert (growth.size, growth.factor) == (_SIZE, time_growth.FACTOR)
    assert growth.result == (_LARGE, time_growth.REPEATS - 1)
    assert (growth.small_s, growth.large_s) == (_COST_S, ratio * _COST_S)
    assert growth.ratio == ratio


@pytest.mark.parametrize(
    ("assertion", "ratio", "said"),
    [
        (
            time_growth.assert_linear_time,
            64.0,
            "an input 8 times as large took 64.0 times as long (0.98 ms for size "
            "16, 62.50 ms for size 128), past 22.6: work that grows as the size "
            "to the power 1 takes about 8 times as long, and to the power 2 about "
            "64 times",
        ),
        (
            time_growth.assert_linear_time,
            22.75,
            "an input 8 times as large took 22.8 times as long (0.98 ms for size "
            "16, 22.22 ms for size 128), past 22.6: work that grows as the size "
            "to the power 1 takes about 8 times as long, and to the power 2 about "
            "64 times",
        ),
        (
            time_growth.assert_time_does_not_grow,
            8.0,
            "an input 8 times as large took 8.0 times as long (0.98 ms for size "
            "16, 7.81 ms for size 128), past 2.8: work that grows as the size to "
            "the power 0 takes about 1 times as long, and to the power 1 about 8 "
            "times",
        ),
        (
            time_growth.assert_time_does_not_grow,
            2.875,
            "an input 8 times as large took 2.9 times as long (0.98 ms for size "
            "16, 2.81 ms for size 128), past 2.8: work that grows as the size to "
            "the power 0 takes about 1 times as long, and to the power 1 about 8 "
            "times",
        ),
    ],
)
def test_growth_past_the_bound_fails_the_test(
    assertion: Callable[..., time_growth.Growth[tuple[int, int]]],
    ratio: float,
    said: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Quadratic work fails a test of linear time and linear work a test that the
    time does not grow, and so does work that grows just past the bound, the
    test told the two readings, the two sizes and what each power of growth
    would take.
    """
    clock = _clock(monkeypatch, _FINE_STEP_S)
    work = _Work(clock, {_SIZE: _COST_S, _LARGE: ratio * _COST_S})
    with pytest.raises(pytest.fail.Exception, match=f"^{re.escape(said)}$"):
        assertion(_as_built, work, _SIZE)


@pytest.mark.parametrize(
    ("assertion", "growing", "past", "said"),
    [
        (
            time_growth.assert_linear_time,
            4.0,
            8.5,
            "an input 4 times as large took 8.5 times as long (0.98 ms for size "
            "16, 8.30 ms for size 64), past 8.0: work that grows as the size to "
            "the power 1 takes about 4 times as long, and to the power 2 about "
            "16 times",
        ),
        (
            time_growth.assert_time_does_not_grow,
            1.0,
            2.25,
            "an input 4 times as large took 2.2 times as long (0.98 ms for size "
            "16, 2.20 ms for size 64), past 2.0: work that grows as the size to "
            "the power 0 takes about 1 times as long, and to the power 1 about 4 "
            "times",
        ),
    ],
)
def test_the_factor_and_the_repeats_a_test_asks_for_are_the_ones_read(
    assertion: Callable[..., time_growth.Growth[tuple[int, int]]],
    growing: float,
    past: float,
    said: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A test that asks for an input four times as large, read three times, has
    the larger input built four times as large, each size read three times, and
    its growth held under 4 ** 1.5 = 8 or 4 ** 0.5 = 2: work that grows as the
    bound allows passes, and work that grows just past it fails, where it would
    pass under the bounds of a factor of 8.
    """
    clock = _clock(monkeypatch, _FINE_STEP_S)
    larger = 4 * _SIZE
    work = _Work(clock, {_SIZE: _COST_S, larger: growing * _COST_S})
    growth = assertion(_as_built, work, _SIZE, factor=4, repeats=3)
    assert (growth.size, growth.factor, growth.ratio) == (_SIZE, 4, growing)
    assert work.calls == {_SIZE: 1 + 3, larger: 3}
    work = _Work(clock, {_SIZE: _COST_S, larger: past * _COST_S})
    with pytest.raises(pytest.fail.Exception, match=f"^{re.escape(said)}$"):
        assertion(_as_built, work, _SIZE, factor=4, repeats=3)


def test_the_shortest_reading_of_each_size_is_kept(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """What else the process does only ever lengthens a reading: with four of the
    five readings of each size four times as long, as other processes would make
    them, the helper still sees what the work costs, and linear work passes.

    On a fine clock the first call over the smaller input counts how many calls
    make a reading, and its five readings are the calls after it; the larger
    input is not counted, so its readings are its first five calls.
    """
    clock = _clock(monkeypatch, _FINE_STEP_S)
    lengthened = {(_SIZE, place): 3 * _COST_S for place in (1, 2, 4, 5)} | {
        (_LARGE, place): 3 * _LINEAR_S[_LARGE] for place in (0, 1, 3, 4)
    }
    work = _Work(clock, _LINEAR_S, extra_s=lengthened)
    growth = time_growth.assert_linear_time(_as_built, work, _SIZE)
    assert (growth.small_s, growth.large_s) == (_COST_S, _LINEAR_S[_LARGE])


def test_a_load_that_starts_partway_lengthens_both_sizes_alike(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The two sizes are read in turn, so a load that starts partway through the
    readings and stays lengthens the readings of both alike. Here it starts after
    the third call, the untimed first one and a reading of each size, and makes
    every call after it four times as long: one short reading of each is left,
    and linear work passes. Were all the readings of one size taken before those
    of the other, the larger input would read as 32 times as long as the smaller
    and fail, or the smaller as four times as long as it costs.
    """
    clock = _clock(monkeypatch, _FINE_STEP_S)
    sizes_read: list[int] = []

    def loaded(size: int) -> int:
        sizes_read.append(size)
        clock.now_s += (4.0 if len(sizes_read) > 3 else 1.0) * _LINEAR_S[size]
        return size

    growth = time_growth.assert_linear_time(_as_built, loaded, _SIZE)
    assert (growth.small_s, growth.large_s) == (_COST_S, _LINEAR_S[_LARGE])


def test_on_a_coarse_clock_a_reading_calls_the_work_over_ten_steps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Read one call at a time, a call of a millisecond on a clock that counts in
    steps of 15.6 ms reads as no time or as a whole step. A call over the smaller
    input is a sixteenth of a step, so ten steps take 160 calls, and one over the
    larger input half a step, so they take 20: each size is counted once, then
    read five times, and each reading is the time of one call. What is handed
    back is what the last of the 120 calls over the larger input returned.
    """
    clock = _clock(monkeypatch, _COARSE_STEP_S)
    work = _Work(clock, _LINEAR_S)
    growth = time_growth.measure_growth(_as_built, work, _SIZE)
    assert (growth.small_s, growth.large_s) == (_COST_S, _LINEAR_S[_LARGE])
    readings = 1 + time_growth.REPEATS
    assert work.calls == {_SIZE: 160 * readings, _LARGE: 20 * readings}
    assert growth.result == (_LARGE, 20 * readings - 1)


def test_on_a_fine_clock_one_call_is_a_reading(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Where one call over the smaller input spans the ten steps, one call is a
    reading, and the larger input, which takes no less, is not counted at all.
    """
    clock = _clock(monkeypatch, _FINE_STEP_S)
    work = _Work(clock, _LINEAR_S)
    time_growth.measure_growth(_as_built, work, _SIZE)
    assert work.calls == {_SIZE: 1 + time_growth.REPEATS, _LARGE: time_growth.REPEATS}


def test_neither_the_build_nor_the_first_call_is_charged_to_a_reading(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each input is built before the readings start, and the first call of the
    work, which may load or compile what it reads, counts the calls of a reading
    and is not timed: read once each, neither size is charged a build of a second
    or a first call a quarter of a second longer.
    """
    clock = _clock(monkeypatch, _FINE_STEP_S)

    def built(size: int) -> int:
        clock.now_s += 1.0
        return size

    work = _Work(clock, _LINEAR_S, extra_s={(_SIZE, 0): 0.25})
    growth = time_growth.measure_growth(built, work, _SIZE, repeats=1)
    assert (growth.small_s, growth.large_s) == (_COST_S, _LINEAR_S[_LARGE])


def test_the_collector_is_held_off_while_the_work_runs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A collection the larger input sets off is not charged to it alone: the
    collector is off at every call, and on again once the readings end.
    """
    gc.enable()
    work = _Work(_clock(monkeypatch, _FINE_STEP_S), _LINEAR_S)
    time_growth.measure_growth(_as_built, work, _SIZE)
    assert set(work.collecting) == {False}
    assert gc.isenabled()


def test_the_collector_is_on_again_when_the_work_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A reader that fails leaves the collector on for the tests after it."""
    gc.enable()
    clock = _clock(monkeypatch, _FINE_STEP_S)

    def failing(size: int) -> int:
        if size == _LARGE:
            msg = f"the reader failed on the input of size {size}"
            raise RuntimeError(msg)
        clock.now_s += _COST_S
        return size

    with pytest.raises(RuntimeError, match="the reader failed"):
        time_growth.measure_growth(_as_built, failing, _SIZE)
    assert gc.isenabled()


def test_a_collector_off_before_the_readings_stays_off(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The helper puts the collector back as it found it, never on regardless."""
    gc.disable()
    work = _Work(_clock(monkeypatch, _FINE_STEP_S), _LINEAR_S)
    time_growth.measure_growth(_as_built, work, _SIZE)
    assert not gc.isenabled()


@pytest.mark.parametrize(("factor", "repeats"), [(1, 5), (8, 0)])
def test_a_factor_below_two_or_no_repeat_is_refused_before_anything_is_read(
    factor: int, repeats: int
) -> None:
    """A factor of one cannot tell linear work from quadratic, and no repeat reads
    nothing: both are refused before the work is called.
    """
    work = _Work(_Clock(_FINE_STEP_S), _LINEAR_S)
    with pytest.raises(ValueError, match="needs a factor of 2 or more and a repeat"):
        time_growth.measure_growth(
            _as_built, work, _SIZE, factor=factor, repeats=repeats
        )
    assert not work.calls


def test_a_smaller_input_read_in_no_time_the_clock_counts_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Work slow once, as a reader that loads what it reads on its first call, and
    quicker than a step of the clock after: that first call spans the ten steps
    alone, so a reading is one call, and every reading of the smaller input reads
    as no time. A call over the larger input takes two whole steps, so only the
    smaller input reads as no time, and the helper refuses it rather than divide
    by it.
    """
    clock = _clock(monkeypatch, _COARSE_STEP_S)
    costs_s = {_SIZE: 2.0**-12, _LARGE: 2 * _COARSE_STEP_S}
    work = _Work(clock, costs_s, extra_s={(_SIZE, 0): 0.25})
    with pytest.raises(ValueError, match="was read in no time the clock counts"):
        time_growth.measure_growth(_as_built, work, _SIZE)


def test_the_clock_step_is_the_smallest_of_three_seen(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Another process that runs while the clock is watched only lengthens the
    step it is seen to take: watched three times, the clock moves on by three
    steps, one and two, and the step is one.
    """
    step = _COARSE_STEP_S
    readings = iter(
        [0.0, 0.0, 3 * step, 3 * step, 4 * step, 4 * step, 4 * step, 6 * step]
    )
    monkeypatch.setattr(time_growth, "_cpu_time", readings.__next__)
    assert time_growth._clock_step.__wrapped__() == step
    assert next(readings, None) is None


def test_a_wait_on_the_wall_is_not_charged_to_a_reading() -> None:
    """The helper reads the CPU time of the process, never the time on the wall: a
    fifth of a second the process spends waiting, as one that other processes
    keep off the cores waits, adds next to nothing to it.
    """
    start = time_growth._cpu_time()
    time.sleep(0.2)
    assert time_growth._cpu_time() - start < 0.1


def test_the_work_of_another_thread_is_charged_to_a_reading() -> None:
    """The CPU time is that of the whole process, all its threads together: the
    twentieth of a second another thread works while this one waits for it is
    counted, as the work of a reader that hands some of it to a thread would be.
    """
    start = time_growth._cpu_time()
    worker = threading.Thread(target=_spin, args=(0.05,))
    worker.start()
    worker.join(_THREAD_WAIT_S)
    assert not worker.is_alive()
    assert time_growth._cpu_time() - start >= 0.025
