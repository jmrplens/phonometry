#  Copyright (c) 2026. Jose Manuel Requena Plens
"""How the time a reader takes grows with what it reads.

A test that a reader runs in linear time cannot hold one large input to a
number of seconds: a runner that is slower than the machine the number was
chosen on, or busy with other work, takes several times as long over the same
linear reading and fails it. What tells linear work from quadratic is how the
time grows. Read an input of some size, then one ``factor`` times as large:
linear work takes about ``factor`` times as long, quadratic work ``factor``
squared, and a slower machine stretches both readings alike, so their ratio
stays where it was.

:func:`assert_linear_time` holds the ratio under ``factor ** 1.5``, halfway
between linear and quadratic work on a logarithmic scale.
:func:`assert_time_does_not_grow` holds it under ``factor ** 0.5``, halfway
between work that does not grow with the input and linear work: a refusal
that must come before the input is read, whatever its size.

The time is the CPU time of the process, never the time on the wall. A machine
busy with more work than it has cores lets a short reading through between two
other processes and stops a long one again and again: with every core kept
busy by other processes, a linear reading of the snippet gate took 28 times as
long on the wall for an input eight times as large, and 7 times as long by the
CPU time of the process, as on an idle machine. Other processes lengthen the
CPU time of a reading too, since they share the caches and the cores, but they
lengthen both readings much alike, so their ratio stays well under the bound.
Where the system counts that time in coarse steps (Windows counts it in steps
of the scheduler's tick, some 16 ms), a reading calls the reader as many times
over as spans :data:`_STEPS_PER_READING` steps, counted once for each size
before the readings start, and takes the time of one call; where one call
spans them, as on Linux and macOS, one call is a reading.

Each size is read ``repeats`` times, the two in turn, and the shortest
reading of each is kept: what else the process does only ever lengthens a
reading, so the shortest is the nearest to the reader's own cost. The inputs
are built before they are timed, the reader runs untimed first (the calls
that count how many make a reading), so that what it loads or compiles on its
first call is not charged to the smaller size, and the garbage collector is
held off while the readings run, as :mod:`timeit` holds it, so that a
collection the larger input sets off is not charged to it alone.

A test of linear time chooses the smaller size so that its reading takes a
millisecond or more, and so that the quadratic reading the fix replaced, at
``factor`` times that size, still ends within a few minutes: a scratch copy
that restores it shows the test failing. A reading that is part linear and
part quadratic grows by a ratio between the two, and fails only once its
quadratic part is some three quarters of the larger reading, so the larger the
size, the smaller the constant of a quadratic term the test catches. A test
that the time does not grow cannot lengthen its reading by the size, and the
reading may stay under a millisecond; it chooses the sizes so that the work
the fix removed would be most of the larger reading.
"""

from __future__ import annotations

import dataclasses
import functools
import gc
import math
import time
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

#: How many times larger the second input is than the first.
FACTOR = 8

#: How many times each size is read; the shortest reading of each is kept.
REPEATS = 5

#: How many steps of the CPU-time clock a reading spans at least, so that a
#: step it misses or gains is a tenth of it at most.
_STEPS_PER_READING = 10


def _cpu_time() -> float:
    """The CPU time the process has taken, all its threads together [s]."""
    return time.process_time()


@functools.cache
def _clock_step() -> float:
    """The smallest of three steps :func:`_cpu_time` is seen to advance by
    [s]: another process that runs while one is watched only lengthens it.
    """
    steps: list[float] = []
    for _ in range(3):
        start = _cpu_time()
        now = start
        while now <= start:
            now = _cpu_time()
        steps.append(now - start)
    return min(steps)


@dataclasses.dataclass(frozen=True)
class Growth[R]:
    """The shortest readings of an input of :attr:`size` and of one
    :attr:`factor` times as large, and what the larger one gave.
    """

    #: The size of the smaller input.
    size: int
    #: How many times larger the second input is.
    factor: int
    #: The shortest reading of the smaller input [s].
    small_s: float
    #: The shortest reading of the larger input [s].
    large_s: float
    #: What the reader returned for the larger input, for the test to check.
    result: R

    @property
    def ratio(self) -> float:
        """How many times as long the larger input took."""
        return self.large_s / self.small_s


def _calls_per_reading[T](work: Callable[[T], object], case: T, step: float) -> int:
    """How many calls of *work* over *case* span :data:`_STEPS_PER_READING`
    steps of the clock, which advances by *step*; one at least.
    """
    calls = 0
    start = _cpu_time()
    while True:
        work(case)
        calls += 1
        if _cpu_time() - start >= _STEPS_PER_READING * step:
            return calls


def _reading[T, R](work: Callable[[T], R], case: T, calls: int) -> tuple[float, R]:
    """The CPU time [s] one of *calls* calls of *work* over *case* takes, and
    what the last returns.
    """
    start = _cpu_time()
    for _ in range(calls - 1):
        work(case)
    result = work(case)
    return (_cpu_time() - start) / calls, result


def measure_growth[T, R](
    build: Callable[[int], T],
    work: Callable[[T], R],
    size: int,
    *,
    factor: int = FACTOR,
    repeats: int = REPEATS,
) -> Growth[R]:
    """How the time *work* takes grows from the input of *size* to one
    *factor* times as large.

    :param build: The input of a size, built before it is timed.
    :param work: The reading timed, given the input.
    :param size: The size of the smaller input.
    :param factor: How many times larger the second input is.
    :param repeats: How many times each size is read.
    :return: The shortest reading of each size, and what the last reading of
        the larger input returned.
    :raises ValueError: for a *factor* below 2 or fewer than one repeat,
        and for a smaller input read in no time the clock can count, which
        tells nothing of how the time grows.
    """
    if factor < 2 or repeats < 1:
        msg = f"needs a factor of 2 or more and a repeat, got {factor}, {repeats}"
        raise ValueError(msg)
    small, large = build(size), build(factor * size)
    step = _clock_step()
    best_small = best_large = math.inf
    collecting = gc.isenabled()
    gc.disable()
    try:
        small_calls = _calls_per_reading(work, small, step)
        # A larger input takes no less than the smaller one: when one call of
        # the smaller spans the steps, one call of the larger does too.
        large_calls = 1 if small_calls == 1 else _calls_per_reading(work, large, step)
        for _ in range(repeats):
            best_small = min(best_small, _reading(work, small, small_calls)[0])
            elapsed, result = _reading(work, large, large_calls)
            best_large = min(best_large, elapsed)
    finally:
        if collecting:
            gc.enable()
    if best_small <= 0.0:
        msg = f"the input of size {size} was read in no time the clock counts"
        raise ValueError(msg)
    return Growth(size, factor, best_small, best_large, result)


def _assert_growth[T, R](
    build: Callable[[int], T],
    work: Callable[[T], R],
    size: int,
    *,
    power: int,
    factor: int,
    repeats: int,
) -> Growth[R]:
    """Fail the test unless the time of *work* grows as a power of the size
    no higher than *power*, and return what was measured.
    """
    growth = measure_growth(build, work, size, factor=factor, repeats=repeats)
    bound = factor ** (power + 0.5)
    if growth.ratio < bound:
        return growth
    pytest.fail(
        f"an input {factor} times as large took {growth.ratio:.1f} times as "
        f"long ({growth.small_s * 1e3:.2f} ms for size {size}, "
        f"{growth.large_s * 1e3:.2f} ms for size {factor * size}), past "
        f"{bound:.1f}: work that grows as the size to the power {power} "
        f"takes about {factor**power} times as long, and to the power "
        f"{power + 1} about {factor ** (power + 1)} times"
    )


def assert_linear_time[T, R](
    build: Callable[[int], T],
    work: Callable[[T], R],
    size: int,
    *,
    factor: int = FACTOR,
    repeats: int = REPEATS,
) -> Growth[R]:
    """Fail the test unless *work* takes less than ``factor ** 1.5`` times as
    long over an input *factor* times as large: linear work takes about
    *factor* times as long, quadratic work *factor* squared.

    :param build: The input of a size, built before it is timed.
    :param work: The reading timed, given the input.
    :param size: The size of the smaller input.
    :param factor: How many times larger the second input is.
    :param repeats: How many times each size is read.
    :return: What was measured, with what the larger input gave.
    """
    return _assert_growth(build, work, size, power=1, factor=factor, repeats=repeats)


def assert_time_does_not_grow[T, R](
    build: Callable[[int], T],
    work: Callable[[T], R],
    size: int,
    *,
    factor: int = FACTOR,
    repeats: int = REPEATS,
) -> Growth[R]:
    """Fail the test unless *work* takes less than ``factor ** 0.5`` times as
    long over an input *factor* times as large: work that does not grow with
    the input takes about as long, linear work *factor* times as long.

    :param build: The input of a size, built before it is timed.
    :param work: The reading timed, given the input.
    :param size: The size of the smaller input.
    :param factor: How many times larger the second input is.
    :param repeats: How many times each size is read.
    :return: What was measured, with what the larger input gave.
    """
    return _assert_growth(build, work, size, power=0, factor=factor, repeats=repeats)
