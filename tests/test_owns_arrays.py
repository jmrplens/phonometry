#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every public record keeps a read-only copy of its own of the arrays it holds.

``phonometry._internal.frozen.OwnsArrays`` makes the copy when the record is
built, so it holds whoever builds the record: a function of the library, or a
caller who writes ``SomeResult(levels_db=levels, ...)`` by hand. The first
half of this file fixes what the mechanism does, on records written for the
purpose; the second builds public records of the library by hand with an
array the caller can still write into, writes into it, and checks that the
record did not move.
"""

from __future__ import annotations

import dataclasses
import importlib
import pkgutil
from collections import ChainMap, OrderedDict, defaultdict
from collections.abc import Iterator, Mapping
from types import MappingProxyType
from typing import TYPE_CHECKING, NamedTuple

import numpy as np
import pytest
from numpy.lib.stride_tricks import sliding_window_view

import phonometry
from phonometry import io
from phonometry._internal import frozen
from phonometry._internal.frozen import OwnsArrays, read_only

if TYPE_CHECKING:
    from collections.abc import Callable

# ---------------------------------------------------------------------------
# The mechanism, on records written for the purpose
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class _Plain(OwnsArrays):
    levels_db: np.ndarray
    label: str = ""
    gain: float = 1.0


class _Pair(NamedTuple):
    frequencies: np.ndarray
    weight: float


@dataclasses.dataclass(frozen=True)
class _Containers(OwnsArrays):
    pair: tuple[np.ndarray, float]
    many: list[np.ndarray]
    columns: dict[str, np.ndarray]
    frozen_columns: MappingProxyType[str, np.ndarray]
    named: _Pair
    nested: tuple[tuple[str, np.ndarray], ...] = ()
    numbers: tuple[float, ...] = ()


@dataclasses.dataclass(frozen=True)
class _Validated(OwnsArrays):
    levels_db: np.ndarray
    doubled_db: np.ndarray = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        # The class's own hook runs on the record's copy, never the caller's.
        if self.levels_db.flags.writeable:
            msg = "the hook saw an array the caller can still write into"
            raise AssertionError(msg)
        object.__setattr__(self, "doubled_db", read_only(2.0 * self.levels_db))


@dataclasses.dataclass(frozen=True)
class _Unsealed(OwnsArrays):
    levels_db: np.ndarray
    centred_db: np.ndarray = dataclasses.field(init=False)

    def __post_init__(self) -> None:
        # Stored writeable on purpose: the record copies it after the hook.
        object.__setattr__(self, "centred_db", self.levels_db - 1.0)


@dataclasses.dataclass(frozen=True)
class _Inherits(_Validated):
    extra_db: np.ndarray = dataclasses.field(default_factory=lambda: np.zeros(2))


@dataclasses.dataclass(frozen=True)
class _CallsSuper(_Validated):
    seen: list[object] = dataclasses.field(default_factory=list)

    def __post_init__(self) -> None:
        self.seen.append(self.levels_db)
        super().__post_init__()


class _Hooked:
    def __post_init__(self) -> None:
        pass


@dataclasses.dataclass(frozen=True)
class _WithInitVar(OwnsArrays):
    levels_db: np.ndarray
    offset_db: dataclasses.InitVar[np.ndarray]
    shifted_db: np.ndarray = dataclasses.field(init=False)

    def __post_init__(self, offset_db: np.ndarray) -> None:
        # Seals the argument it keeps, as a hook does with an array of its own.
        object.__setattr__(self, "shifted_db", read_only(offset_db))


class _CallerMapping(Mapping[str, np.ndarray]):
    """A mapping of the caller's own, neither a dict nor a proxy of one."""

    def __init__(self, items: dict[str, np.ndarray]) -> None:
        self._items = items

    def __getitem__(self, key: str) -> np.ndarray:
        return self._items[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)


def _mixin_listed_first() -> type:
    class Wrong(OwnsArrays, _Hooked):
        pass

    return Wrong


def _writeable(values: list[float]) -> np.ndarray:
    array = np.array(values)
    assert array.flags.writeable
    return array


def test_the_record_keeps_a_read_only_copy_and_the_caller_keeps_writing() -> None:
    levels = _writeable([60.0, 61.0, 62.0])
    record = _Plain(levels_db=levels, label="hand", gain=2.0)
    levels[0] = 0.0
    np.testing.assert_array_equal(record.levels_db, [60.0, 61.0, 62.0])
    assert not np.shares_memory(record.levels_db, levels)
    assert not record.levels_db.flags.writeable
    assert levels.flags.writeable
    assert (record.label, record.gain) == ("hand", 2.0)


def test_a_view_of_the_caller_s_array_is_copied_too() -> None:
    grid = _writeable([1.0, 2.0, 3.0, 4.0]).reshape(2, 2)
    record = _Plain(levels_db=grid[:, 0])
    grid[:, 0] = -1.0
    np.testing.assert_array_equal(record.levels_db, [1.0, 3.0])
    assert record.levels_db.flags.c_contiguous


def test_a_read_only_array_of_the_caller_is_copied_as_well() -> None:
    """A read-only flag is the caller's to set back, so it is no promise."""
    levels = _writeable([1.0, 2.0])
    levels.flags.writeable = False
    record = _Plain(levels_db=levels)
    assert not np.shares_memory(record.levels_db, levels)
    levels.flags.writeable = True
    levels[0] = 9.0
    assert record.levels_db[0] == 1.0


def test_arrays_inside_containers_are_copied_and_the_rest_is_kept() -> None:
    a, b, c = _writeable([1.0]), _writeable([2.0]), _writeable([3.0])
    numbers = (1.0, 2.0)
    record = _Containers(
        pair=(a, 5.0),
        many=[b],
        columns={"c": c},
        frozen_columns=MappingProxyType({"a": a}),
        named=_Pair(b, 0.5),
        nested=(("c", c),),
        numbers=numbers,
    )
    for array in (a, b, c):
        array[0] = 0.0
    assert record.pair[0][0] == 1.0
    assert record.pair[1] == 5.0
    assert record.many[0][0] == 2.0
    assert record.columns["c"][0] == 3.0
    assert isinstance(record.frozen_columns, MappingProxyType)
    assert record.frozen_columns["a"][0] == 1.0
    assert isinstance(record.named, _Pair)
    assert record.named.frequencies[0] == 2.0
    assert record.nested[0][1][0] == 3.0
    # A tuple that holds no array comes back as it went in.
    assert record.numbers is numbers


@pytest.mark.parametrize(
    "kind",
    [
        OrderedDict,
        lambda items: defaultdict(float, items),
        ChainMap,
        _CallerMapping,
    ],
    ids=["OrderedDict", "defaultdict", "ChainMap", "own Mapping"],
)
def test_arrays_inside_any_mapping_are_copied(
    kind: Callable[[dict[str, np.ndarray]], Mapping[str, np.ndarray]],
) -> None:
    """Not only a dict: any mapping is rebuilt, as a plain dict, around copies."""
    mine = _writeable([1.0, 2.0])
    given = kind({"c": mine})
    record = _Containers(
        pair=(np.zeros(1), 0.0),
        many=[],
        columns=given,  # type: ignore[arg-type]
        frozen_columns=MappingProxyType({}),
        named=_Pair(np.zeros(1), 0.0),
    )
    assert mine.flags.writeable
    assert not np.shares_memory(record.columns["c"], mine)
    assert not record.columns["c"].flags.writeable
    assert record.columns is not given
    mine[0] = 99.0
    assert record.columns["c"][0] == 1.0


def test_a_mapping_with_no_array_comes_back_as_it_went_in() -> None:
    given = OrderedDict(a=1.0)
    record = _Containers(
        pair=(np.zeros(1), 0.0),
        many=[],
        columns=given,  # type: ignore[arg-type]
        frozen_columns=MappingProxyType({}),
        named=_Pair(np.zeros(1), 0.0),
    )
    assert record.columns is given


def test_every_copy_is_c_ordered_whatever_it_was_made_from() -> None:
    """A broadcast row and a transposed grid come out C-ordered, values kept."""
    row = _writeable([1.0, 2.0, 3.0])
    broadcast = np.broadcast_to(row, (4, 3))
    record = _Plain(levels_db=broadcast)
    assert record.levels_db.flags.c_contiguous
    np.testing.assert_array_equal(record.levels_db, broadcast)
    grid = _writeable([1.0, 2.0, 3.0, 4.0, 5.0, 6.0]).reshape(2, 3)
    transposed = _Plain(levels_db=grid.T)
    assert transposed.levels_db.flags.c_contiguous
    np.testing.assert_array_equal(transposed.levels_db, grid.T)


def test_a_record_held_in_a_field_is_left_as_it_is() -> None:
    """Composition: the inner record answers for its own arrays."""

    @dataclasses.dataclass(frozen=True)
    class Outer(OwnsArrays):
        inner: _Plain
        steps: tuple[_Plain, ...]

    inner = _Plain(levels_db=_writeable([1.0]))
    outer = Outer(inner=inner, steps=(inner,))
    assert outer.inner is inner
    assert outer.steps[0] is inner


def test_the_argument_of_an_init_var_is_copied_before_the_hook() -> None:
    """The hook seals the argument it keeps; the caller's array keeps its flag."""
    offset = _writeable([0.5, 0.25])
    record = _WithInitVar(levels_db=_writeable([1.0, 2.0]), offset_db=offset)
    assert offset.flags.writeable
    assert not np.shares_memory(record.shifted_db, offset)
    offset[0] = 9.0
    assert record.shifted_db[0] == 0.5


def test_the_class_s_own_post_init_runs_on_the_copy() -> None:
    levels = _writeable([1.0, 2.0])
    record = _Validated(levels_db=levels)
    levels[:] = 0.0
    np.testing.assert_array_equal(record.doubled_db, [2.0, 4.0])
    assert not record.doubled_db.flags.writeable


def test_an_array_the_hook_left_writeable_is_copied_after_it() -> None:
    record = _Unsealed(levels_db=_writeable([3.0, 4.0]))
    assert not record.centred_db.flags.writeable
    np.testing.assert_array_equal(record.centred_db, [2.0, 3.0])


def test_a_read_only_view_of_an_array_someone_can_write_is_copied() -> None:
    owner = _writeable([1.0, 2.0, 3.0])

    @dataclasses.dataclass(frozen=True)
    class Borrowing(OwnsArrays):
        window: np.ndarray = dataclasses.field(init=False)

        def __post_init__(self) -> None:
            view = owner[1:]
            view.flags.writeable = False
            object.__setattr__(self, "window", view)

    record = Borrowing()
    owner[1] = -5.0
    np.testing.assert_array_equal(record.window, [2.0, 3.0])


def test_a_strided_view_of_an_array_someone_can_write_is_copied() -> None:
    """``sliding_window_view`` hides its array behind a stand-in; walked too."""
    owner = _writeable([1.0, 2.0, 3.0, 4.0])

    @dataclasses.dataclass(frozen=True)
    class Windows(OwnsArrays):
        frames: np.ndarray = dataclasses.field(init=False)

        def __post_init__(self) -> None:
            object.__setattr__(self, "frames", sliding_window_view(owner, 2))

    record = Windows()
    assert not np.shares_memory(record.frames, owner)
    owner[1] = -5.0
    assert record.frames[0, 1] == 2.0


def test_a_subclass_copies_its_own_fields_and_its_base_s() -> None:
    levels, extra = _writeable([1.0]), _writeable([7.0, 8.0])
    record = _Inherits(levels_db=levels, extra_db=extra)
    levels[0] = extra[0] = 0.0
    assert record.levels_db[0] == 1.0
    assert record.extra_db[0] == 7.0
    assert record.doubled_db[0] == 2.0


def test_a_hook_that_calls_super_copies_once() -> None:
    """``super().__post_init__()`` reaches the base's hook, not a second copy:
    the array the subclass's hook saw is the one the record keeps.
    """
    seen: list[object] = []
    record = _CallsSuper(levels_db=_writeable([1.0]), seen=seen)
    assert len(seen) == 1
    assert seen[0] is record.levels_db
    assert record.doubled_db[0] == 2.0


def test_listing_the_mixin_before_a_base_with_a_hook_is_refused() -> None:
    """The base's hook would never run, so the class is refused outright."""
    with pytest.raises(TypeError, match="list OwnsArrays last"):
        _mixin_listed_first()


def test_a_replaced_record_owns_what_it_was_given() -> None:
    record = _Plain(levels_db=_writeable([1.0]))
    levels = _writeable([5.0])
    replaced = dataclasses.replace(record, levels_db=levels)
    levels[0] = 0.0
    assert replaced.levels_db[0] == 5.0
    assert not np.shares_memory(replaced.levels_db, record.levels_db)


def test_none_and_numbers_go_through_untouched() -> None:
    @dataclasses.dataclass(frozen=True)
    class Optional(OwnsArrays):
        levels_db: np.ndarray | None = None
        level_db: float | np.ndarray = 0.0

    record = Optional()
    assert record.levels_db is None
    assert record.level_db == 0.0


# ---------------------------------------------------------------------------
# Every public record of the library
# ---------------------------------------------------------------------------


def _public_classes() -> list[type]:
    found: dict[int, type] = {}
    for module_info in pkgutil.walk_packages(phonometry.__path__, "phonometry."):
        if any(part.startswith("_") for part in module_info.name.split(".")):
            continue
        module = importlib.import_module(module_info.name)
        for name in getattr(module, "__all__", ()):
            obj = getattr(module, name, None)
            if isinstance(obj, type):
                found[id(obj)] = obj
    return sorted(found.values(), key=lambda cls: f"{cls.__module__}.{cls.__name__}")


def test_every_public_record_that_copies_composes_its_own_hook() -> None:
    """The copy is wrapped around every class's ``__post_init__``, none lost.

    A class whose own hook replaced the composed one would build without
    copying; the composed hooks are the ones the mechanism registered.
    """
    records = [cls for cls in _public_classes() if issubclass(cls, OwnsArrays)]
    assert len(records) > 400
    lost = [
        cls.__name__ for cls in records if cls.__post_init__ not in frozen._COMPOSED
    ]
    assert lost == []
    assert all(dataclasses.is_dataclass(cls) for cls in records)


def _built_by_hand() -> dict[str, tuple[Callable[[np.ndarray], object], str]]:
    """Public records, each built from one writeable array, and the field
    that keeps it.
    """
    from phonometry import (
        aircraft,
        building,
        emission,
        environment,
        materials,
        noise_control,
        room,
        simulation,
    )

    return {
        "AnpNpdCurves": (
            lambda a: aircraft.AnpNpdCurves(
                aircraft_id="A",
                npd_id="N",
                metric="SEL",
                operation="D",
                power_parameter="lbf",
                powers=np.array([1.0, 2.0]),
                distances=a,
                levels=np.zeros((2, 3)),
            ),
            "distances",
        ),
        "EPNLResult": (
            lambda a: aircraft.EPNLResult(
                frequencies=a,
                times=np.arange(3.0),
                pnl=np.zeros(3),
                tone_correction=np.zeros(3),
                pnlt=np.zeros(3),
                pnltm=0.0,
                bandsharing_adjustment=0.0,
                duration_correction=0.0,
                epnl=0.0,
                band_limits=(0, 2),
            ),
            "frequencies",
        ),
        "WeightedRatingResult": (
            lambda a: building.WeightedRatingResult(
                rating=50, c=-1, ctr=-4, unfavourable_sum=20.0, measured=a
            ),
            "measured",
        ),
        "ImpulseResponseResult": (
            lambda a: room.ImpulseResponseResult(ir=a, fs=48000, method="sweep"),
            "ir",
        ),
        "OpenPlanResult": (
            lambda a: room.OpenPlanResult(
                d2s=6.0, lp_as_4m=48.0, rd=5.0, rp=9.0, positions_m=a
            ),
            "positions_m",
        ),
        "DuctPathStage": (
            lambda a: noise_control.DuctPathStage(
                label="bend",
                code="B",
                attenuation=a,
                attenuated=np.zeros(3),
                self_noise=np.zeros(3),
                levels=np.zeros(3),
            ),
            "attenuation",
        ),
        "TransferMatrix": (
            lambda a: materials.TransferMatrix(
                t11=a, t12=np.ones(3), t21=np.ones(3), t22=np.ones(3)
            ),
            "t11",
        ),
        "MetadiffuserResult": (
            lambda a: materials.MetadiffuserResult(
                frequencies=a,
                reflection=np.ones(3, dtype=complex),
                absorption=np.zeros(3),
                well_absorption=np.zeros(3),
            ),
            "frequencies",
        ),
        "EmissionPressureResult": (
            lambda a: emission.EmissionPressureResult(
                level_db=a,
                measured_level_db=a,
                background_correction_db=0.0,
                local_correction_db=0.0,
                grade="engineering",
                background_margin_db=15.0,
                standard="ISO 11201",
            ),
            "level_db",
        ),
        "RailwayTrack": (
            lambda a: environment.RailwayTrack(
                rail_roughness=(a, np.zeros(3)), track_transfer=np.zeros(3)
            ),
            "rail_roughness",
        ),
        "FDTDResult": (
            lambda a: simulation.FDTDResult(
                times=np.arange(3.0),
                pressures=a.reshape(1, 3),
                probes=np.array([[0, 0]]),
                probe_positions=np.array([[0.0, 0.0]]),
                dx=0.01,
                dt=1e-5,
                shape=(4, 4),
                sources=(),
                snapshots=None,
                snapshot_times=None,
                obstacle_mask=None,
            ),
            "pressures",
        ),
    }


def _first_array(value: object) -> np.ndarray:
    if isinstance(value, tuple):
        value = value[0]
    assert isinstance(value, np.ndarray)
    return value


@pytest.mark.parametrize("name", sorted(_built_by_hand()))
def test_a_public_record_built_by_hand_does_not_follow_the_caller(name: str) -> None:
    build, field_name = _built_by_hand()[name]
    caller = _writeable([10.0, 20.0, 30.0])
    record = build(caller)
    kept = _first_array(getattr(record, field_name))
    before = kept.copy()
    caller[:] = -1.0
    np.testing.assert_array_equal(kept, before)
    assert not np.shares_memory(kept, caller)
    assert not kept.flags.writeable
    assert caller.flags.writeable


def _calibration_with(corrections: Mapping[str, np.ndarray]) -> dict[str, object]:
    """The two calibration records, each holding *corrections* as given."""
    from phonometry import metrology

    frequencies = np.array([250.0, 500.0, 1000.0])
    return {
        "ReciprocityCalibration": metrology.ReciprocityCalibration(
            frequencies_hz=frequencies,
            sensitivity_v_per_pa=np.ones((3, 3)),
            products_v2_per_pa2=np.ones((3, 3)),
            field="pressure",
            method="three_microphones",
            corrections_db=corrections,
        ),
        "ComparisonCalibration": metrology.ComparisonCalibration(
            frequencies_hz=frequencies,
            reference_sensitivity_level_db=np.full(3, -38.0),
            output_level_differences_db=np.zeros(3),
            pressure_level_difference_db=np.zeros(3),
            corrections_db=corrections,
            field="pressure",
            excitation="sequential",
        ),
    }


@pytest.mark.parametrize(
    "record_name", ["ReciprocityCalibration", "ComparisonCalibration"]
)
@pytest.mark.parametrize(
    "kind",
    [dict, OrderedDict, lambda items: defaultdict(float, items)],
    ids=["dict", "OrderedDict", "defaultdict"],
)
def test_a_calibration_built_by_hand_copies_the_corrections_of_any_mapping(
    record_name: str,
    kind: Callable[[dict[str, np.ndarray]], Mapping[str, np.ndarray]],
) -> None:
    mine = _writeable([0.1, 0.2, 0.3])
    record = _calibration_with(kind({"wave_motion": mine}))[record_name]
    kept = record.corrections_db["wave_motion"]  # type: ignore[attr-defined]
    assert mine.flags.writeable
    assert not np.shares_memory(kept, mine)
    mine[0] = 99.0
    assert kept[0] == pytest.approx(0.1)


def test_a_signal_a_record_is_handed_is_held_whole() -> None:
    """Composition: a record keeps a Signal as it keeps any record it is given.

    The Signal answers for its own samples, which it copied when it was built
    and keeps writeable, as every Signal does; the record makes no copy of
    it. A bare array in the same field is copied as any other.
    """
    from phonometry.signals import ResampledSignalResult

    def build(signal: object) -> ResampledSignalResult:
        return ResampledSignalResult(
            signal=signal,  # type: ignore[arg-type]
            fs=16000.0,
            original_fs=48000.0,
            up=1,
            down=3,
            filter_taps=np.ones(5),
            passband_edge_hz=7000.0,
            stopband_edge_hz=8000.0,
            stopband_attenuation_db=60.0,
            transition_width=0.1,
        )

    signal = io.Signal(np.zeros(8), fs=16000)
    held = build(signal)
    assert held.signal is signal
    assert held.signal.data.flags.writeable
    samples = _writeable([0.0, 1.0, 2.0])
    copied = build(samples)
    assert not np.shares_memory(copied.signal, samples)
    assert not copied.signal.flags.writeable  # type: ignore[union-attr]


def test_a_signal_a_function_returns_in_a_result_is_its_own() -> None:
    """The library builds the Signal it returns, so it shares nothing with
    the input; its samples stay writeable, as every Signal's do.
    """
    from phonometry import signals

    given = io.Signal(np.sin(np.arange(480) * 0.1), fs=48000)
    result = signals.resample_signal(given, fs_new=24000)
    assert isinstance(result.signal, io.Signal)
    assert not np.shares_memory(result.signal.data, given.data)
    assert result.signal.data.flags.writeable
    assert not result.filter_taps.flags.writeable


def test_a_signal_handed_to_an_array_field_keeps_its_samples_writeable() -> None:
    """A record that seals what ``np.asarray`` gives it never seals a Signal's
    own samples, multichannel included, and keeps a copy of its own.
    """
    from phonometry.environment.sources.rolling_stock_noise import (
        PassByMeasurement,
    )

    signal = io.Signal(np.ones((2, 4)), fs=48000)
    record = PassByMeasurement(
        times_s=signal,  # type: ignore[arg-type]
        levels_db=np.zeros(3),
        start_s=0.0,
        end_s=1.0,
        equivalent_level_db=0.0,
        max_level_db=0.0,
        front_level_db=0.0,
        rear_level_db=0.0,
        record_start_level_db=0.0,
        record_end_level_db=0.0,
    )
    assert signal.data.flags.writeable
    assert not np.shares_memory(record.times_s, signal.data)
    signal.data[0, 0] = 5.0
    assert record.times_s[0, 0] == 1.0
