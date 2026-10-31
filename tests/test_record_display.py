#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every public record shows itself as a table in a notebook.

``phonometry._internal.display.RichDisplay`` gives a record the two answers
IPython asks for, ``_repr_html_`` and ``_repr_pretty_``: a table of its
fields, an array as one line of shape and range, the verdict of a record with
``passes`` as PASS or FAIL. These tests hold it to what the docstring of that
module promises: the HTML parses, every text in it is escaped, it stays small
for the largest results the library builds, it never prints an array value
but the extremes, it reads no property but ``passes`` and runs no plot, and
every verdict shows its outcome. They run on the real results of
``tests/result_factories.py`` (about two hundred, each built through the
public API) and on records written for the purpose.
"""

from __future__ import annotations

import collections.abc
import dataclasses
import functools
import importlib
import inspect
import numbers
import pathlib
import pkgutil
import types
import typing
import warnings
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, NamedTuple
from unittest import mock

import numpy as np
import numpy.typing as npt
import pytest
import result_factories

import phonometry
from phonometry import io
from phonometry._internal import display
from phonometry._internal.display import RichDisplay
from phonometry._internal.types import BandFraction, WindowSpec

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

#: The tags the table is written with, and nothing else.
_TAGS = frozenset(
    {
        "div",
        "table",
        "caption",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",
        "code",
        "strong",
        "span",
        "details",
        "summary",
    }
)


class _Printer:
    """IPython's pretty printer, as far as a record writes to it."""

    def __init__(self) -> None:
        self.written: list[str] = []

    def text(self, obj: str) -> None:
        self.written.append(obj)


def _pretty(record: object, *, cycle: bool = False) -> str:
    printer = _Printer()
    record._repr_pretty_(printer, cycle)  # type: ignore[attr-defined]
    return "".join(printer.written)


def _parsed(record: object) -> ET.Element:
    """The record's HTML, parsed as XML, its tags checked."""
    root = ET.fromstring(record._repr_html_())  # type: ignore[attr-defined]
    assert root.tag == "div"
    assert {element.tag for element in root.iter()} <= _TAGS
    return root


def _public_records() -> list[type]:
    found: dict[int, type] = {id(phonometry.ReportMetadata): phonometry.ReportMetadata}
    for module_info in pkgutil.walk_packages(phonometry.__path__, "phonometry."):
        if any(part.startswith("_") for part in module_info.name.split(".")):
            continue
        module = importlib.import_module(module_info.name)
        for name in getattr(module, "__all__", ()):
            obj = getattr(module, name, None)
            if isinstance(obj, type) and (
                dataclasses.is_dataclass(obj)
                or (issubclass(obj, tuple) and hasattr(obj, "_fields"))
            ):
                found[id(obj)] = obj
    return sorted(found.values(), key=lambda cls: f"{cls.__module__}.{cls.__name__}")


def _factories() -> list[tuple[str, Callable[[], object]]]:
    """Every factory of ``result_factories`` that builds a record unasked."""
    found = []
    for name, function in vars(result_factories).items():
        if not (
            inspect.isfunction(function)
            and function.__module__ == result_factories.__name__
            and name.startswith("_")
        ):
            continue
        parameters = inspect.signature(function).parameters.values()
        if any(p.default is p.empty and p.kind != p.VAR_KEYWORD for p in parameters):
            continue
        found.append((name, function))
    return found


@pytest.fixture(scope="module")
def real_results() -> dict[str, object]:
    """The records the factories build, by factory name."""
    built: dict[str, object] = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for name, factory in _factories():
            result = factory()
            if hasattr(result, "_repr_html_"):
                built[name] = result
    return built


# ---------------------------------------------------------------------------
# Every public record has it, and it is the one mechanism
# ---------------------------------------------------------------------------


def test_every_public_record_shows_itself_through_the_mechanism() -> None:
    records = _public_records()
    assert len(records) > 600
    named_tuples = [cls for cls in records if issubclass(cls, tuple)]
    others = [cls for cls in records if not issubclass(cls, tuple)]
    assert [
        cls.__name__
        for cls in others
        if cls._repr_html_ is not RichDisplay._repr_html_  # type: ignore[attr-defined]
        or cls._repr_pretty_ is not RichDisplay._repr_pretty_  # type: ignore[attr-defined]
    ] == []
    # A named tuple unpacks by position, the hazard a record is there to
    # close, so no public record is one.
    assert [cls.__name__ for cls in named_tuples] == []


def _ipython_prints_with(cls: type) -> str:
    """What IPython's pretty printer would print an instance of *cls* with.

    ``IPython.lib.pretty.RepresentationPrinter.pretty`` walks the class's
    bases in order and takes, in each, a ``_repr_pretty_`` or a ``__repr__``
    of the class's own, the first it meets; no printer of its own is
    registered for a class of the library.
    """
    for base in cls.__mro__:
        if "_repr_pretty_" in vars(base):
            return "_repr_pretty_"
        if base is not object and "__repr__" in vars(base):
            return "__repr__"
    return "default"


def test_ipython_prints_every_public_record_with_the_table() -> None:
    """The dataclass writes a ``__repr__`` into each class, which IPython
    would take before a ``_repr_pretty_`` inherited from a base: the method
    has to be in each class's own namespace.
    """
    assert [
        cls.__name__
        for cls in _public_records()
        if _ipython_prints_with(cls) != "_repr_pretty_"
    ] == []


def test_the_fibre_records_show_the_same_table() -> None:
    from phonometry import materials

    fit = materials.FiberResistivityFit(
        k1=3.18e-9,
        k2=1.53,
        fiber_diameter_um=6.0,
        bulk_density_range_kg_m3=(10.0, 100.0),
        direction="lateral",
        source="test",
    )
    lengths = materials.fiber_characteristic_lengths(
        3e-6, bulk_density_kg_m3=20.0, fiber_density_kg_m3=2500.0
    )
    for record in (fit, lengths):
        assert record._repr_html_() == display.record_html(record)
        assert _pretty(record) == display.record_text(record)
        _parsed(record)
    assert "\N{MICRO SIGN}m" in _pretty(fit)
    assert "kg/m\N{SUPERSCRIPT THREE}" in _pretty(fit)
    assert "(10, 100)" in _pretty(fit)


def test_the_mechanism_leaves_repr_and_str_alone() -> None:
    assert not {"__repr__", "__str__"} & set(vars(RichDisplay))
    levels = np.array([60.0, 61.5])
    result = phonometry.filters.OctaveFilterResult(levels, (500.0, 1000.0), None)
    assert repr(result).startswith("OctaveFilterResult(levels=array([60. , 61.5])")


# ---------------------------------------------------------------------------
# On the real results of the library
# ---------------------------------------------------------------------------


def test_every_real_result_parses_and_stays_small(
    real_results: dict[str, object],
) -> None:
    assert len(real_results) > 180
    for name, result in real_results.items():
        html = result._repr_html_()  # type: ignore[attr-defined]
        assert len(html) < 32_000, name
        _parsed(result)
        text = _pretty(result)
        assert text.splitlines()[0].startswith(type(result).__name__), name


def test_every_real_verdict_shows_its_outcome(
    real_results: dict[str, object],
) -> None:
    verdicts = {
        name: result
        for name, result in real_results.items()
        if hasattr(type(result), "passes")
    }
    assert len(verdicts) > 40
    outcomes = set()
    for name, result in verdicts.items():
        outcome = "PASS" if result.passes else "FAIL"  # type: ignore[attr-defined]
        outcomes.add(outcome)
        caption = _parsed(result).find("table/caption")
        assert caption is not None
        assert "".join(caption.itertext()).endswith(outcome), name
        assert _pretty(result).splitlines()[0] == f"{type(result).__name__}: {outcome}"
    assert outcomes == {"PASS", "FAIL"}


@pytest.mark.parametrize(
    "cls",
    [cls for cls in _public_records() if hasattr(cls, "passes")],
    ids=lambda cls: cls.__name__,
)
@pytest.mark.parametrize("outcome", [True, False])
def test_every_verdict_class_shows_whichever_outcome_it_holds(
    cls: type, *, outcome: bool
) -> None:
    """The title carries ``passes`` for every class that has one.

    A stand-in of each class, its fields left empty, holds the outcome given;
    what is checked is that no class sets the table aside or hides its
    verdict from it. The real verdicts are checked above.
    """
    record = object.__new__(cls)
    for field in dataclasses.fields(cls):
        object.__setattr__(record, field.name, None)
    with mock.patch.object(cls, "passes", property(lambda _self: outcome)):
        label = "PASS" if outcome else "FAIL"
        assert _pretty(record).splitlines()[0] == f"{cls.__name__}: {label}"
        caption = _parsed(record).find("table/caption")
        assert caption is not None
        assert "".join(caption.itertext()).endswith(label)


@pytest.mark.parametrize(
    "build",
    [
        result_factories._sound_calibrator,
        result_factories._airborne_rating,
    ],
    ids=["nested-verdict", "rating"],
)
def test_a_record_held_in_a_field_is_a_folded_table_of_its_own(
    build: Callable[[], object],
) -> None:
    record = build()
    nested = [
        name for name, value in display._fields(record) if display._is_record(value)
    ]
    root = _parsed(record)
    assert len(root.findall(".//details")) == len(nested)
    assert len(root.findall(".//table")) == 1 + len(nested)


def _fdtd() -> object:
    from phonometry import simulation

    sim = simulation.FDTD2D(c=343.0, dx=0.02, shape=(100, 100))
    return simulation.fdtd_simulation(
        simulation.FDTDRun(
            c=343.0,
            dx=0.02,
            duration_s=100 * sim.dt,
            sources=[simulation.GaussianPulse(ix=50, iy=50, half_width_s=2e-4)],
            shape=(100, 100),
            recording=simulation.FDTDRecording(probes=[(10, 10)], snapshot_every=1),
        )
    )


def _underwater_pe() -> object:
    from phonometry import underwater

    return underwater.parabolic_equation(
        200.0,
        [0.0, 100.0],
        [1500.0, 1500.0],
        source_depth=40.0,
        max_range=10_000.0,
        range_step=2.0,
        n_depth_points=256,
    )


@pytest.mark.parametrize("run", [_fdtd, _underwater_pe], ids=["fdtd", "pe"])
def test_the_largest_results_display_in_a_few_kilobytes(
    run: Callable[[], object],
) -> None:
    """A million-value field is one line: its shape, its type, its range."""
    result = run()
    arrays = [
        value for _, value in display._fields(result) if isinstance(value, np.ndarray)
    ]
    assert max(array.size for array in arrays) >= 1_000_000
    html = result._repr_html_()  # type: ignore[attr-defined]
    assert len(html) < 8_000
    for array in arrays:
        shape = "\N{MULTIPLICATION SIGN}".join(str(n) for n in array.shape)
        assert f"array {shape} {array.dtype}" in html
    assert len(_pretty(result).splitlines()) < 20


def test_a_record_holding_signals_names_them() -> None:
    fs = 8000
    tone = np.sin(2 * np.pi * 500 * np.arange(fs) / fs)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = phonometry.filters.octave_filter(
            io.Signal(tone, fs), fraction=1, sigbands=True
        )
    assert "tuple of 8 Signal" in _pretty(result)
    _parsed(result)
    signal = io.Signal(np.vstack([tone, tone]), fs)
    text = _pretty(signal)
    assert "array 2\N{MULTIPLICATION SIGN}8000 float64" in text
    assert "Hz" in next(line for line in text.splitlines() if "fs" in line)


# ---------------------------------------------------------------------------
# On records written for the purpose
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class _Inner(RichDisplay):
    depth_m: float
    tag: str


@dataclasses.dataclass(frozen=True)
class _Middle(RichDisplay):
    inner: _Inner
    recording: io.Signal | None = None


@dataclasses.dataclass(frozen=True)
class _Outer(RichDisplay):
    middle: _Middle
    levels_db: np.ndarray
    note: str = ""

    @property
    def expensive(self) -> float:
        msg = "a display read a property"
        raise AssertionError(msg)

    def plot(self) -> None:
        msg = "a display drew a figure"
        raise AssertionError(msg)


@dataclasses.dataclass(frozen=True)
class _Verdict(RichDisplay):
    margin_db: float

    @property
    def passes(self) -> object:
        if self.margin_db < 0:
            msg = "no verdict below zero"
            raise ValueError(msg)
        return np.bool_(self.margin_db > 1)


def _outer(levels: np.ndarray, note: str = "") -> _Outer:
    signal = io.Signal(np.zeros(16), 8000)
    return _Outer(_Middle(_Inner(1.5, "x"), signal), levels, note)


def test_an_array_shows_its_extremes_and_no_other_value() -> None:
    levels = np.array([12.5, 123.456, 98.765, 77.125, 3.25])
    record = _outer(levels)
    text = _pretty(record)
    html = record._repr_html_()
    for shown in (text, html):
        assert "array 5 float64, 3.25 to 123.46" in shown
        for value in ("12.5", "98.7", "98.8", "77.1", "77.12"):
            assert value not in shown


def test_text_reaching_the_html_is_escaped() -> None:
    hostile = "<script>alert('x')</script> & <b>bold</b>"
    record = _outer(np.zeros(2), note=hostile)
    html = record._repr_html_()
    assert "<script>" not in html
    assert "<b>" not in html
    assert "&lt;script&gt;" in html
    assert "&amp;" in html
    note = _parsed(record).find("table/tbody/tr[3]/td[2]")
    assert note is not None
    assert note.text == repr(hostile)


def test_a_record_two_levels_down_is_named_not_expanded() -> None:
    record = _outer(np.zeros(2))
    root = _parsed(record)
    assert len(root.findall(".//table")) == 2
    assert "_Inner (2 fields)" in "".join(root.itertext())
    assert "Signal (6 fields)" in "".join(root.itertext())
    assert "_Middle (2 fields)" in _pretty(record)


def test_the_display_reads_no_property_and_draws_nothing() -> None:
    record = _outer(np.arange(4.0))
    record._repr_html_()
    _pretty(record)
    assert _pretty(record).splitlines()[-1] == "plot()"


@pytest.mark.parametrize(
    ("margin", "label"),
    [(2.0, "PASS"), (0.5, "FAIL"), (-1.0, "no verdict")],
)
def test_the_verdict_is_read_from_passes_and_never_raises(
    margin: float, label: str
) -> None:
    assert _pretty(_Verdict(margin)).splitlines()[0] == f"_Verdict: {label}"
    assert label in _Verdict(margin)._repr_html_()


def test_a_cycle_prints_the_name_alone() -> None:
    assert _pretty(_Verdict(2.0), cycle=True) == "_Verdict(...)"


def test_an_array_too_large_to_read_is_not_read() -> None:
    """Above the limit the range is not read: a broadcast view of one value
    stands for an array of that size without holding it.
    """
    huge = np.broadcast_to(np.float64(42.5), (display.RANGE_LIMIT + 1,))
    summary = display.array_summary(huge)
    assert summary == (
        f"array {display.RANGE_LIMIT + 1} float64, "
        f"range not read above {display.RANGE_LIMIT} values"
    )


@pytest.mark.parametrize(
    ("values", "summary"),
    [
        (np.array([]), "array 0 float64, empty"),
        (np.array([np.nan, np.nan]), "array 2 float64, all NaN"),
        (np.array([1.0, np.nan, 3.0]), "array 3 float64, 1 to 3, with NaN"),
        (np.array([-np.inf, 2.0]), "array 2 float64, -inf to 2"),
        (np.array([3, -4, 5]), "array 3 int64, -4 to 5"),
        (np.array([True, False, True]), "array 3 bool, 2 true"),
        (np.array([3 + 4j, 1j]), "array 2 complex128, |z| 1 to 5"),
        (np.array(["a", "b"]), "array 2 <U1"),
        (np.zeros((2, 3)), "array 2\N{MULTIPLICATION SIGN}3 float64, 0 to 0"),
    ],
)
def test_each_kind_of_array_has_its_summary(values: np.ndarray, summary: str) -> None:
    assert display.array_summary(values) == summary


def test_a_long_table_stops_and_says_how_many_rows_it_left_out() -> None:
    cls = dataclasses.make_dataclass(
        "Wide",
        [(f"value_{i}_db", float) for i in range(display.MAX_ROWS + 20)],
        bases=(RichDisplay,),
        frozen=True,
    )
    record = cls(*range(display.MAX_ROWS + 20))
    assert (
        _pretty(record).splitlines()[-1] == "  \N{HORIZONTAL ELLIPSIS} 20 more fields"
    )
    rows = _parsed(record).findall("table/tbody/tr")
    assert len(rows) == display.MAX_ROWS + 1


def test_the_worst_case_stays_bounded() -> None:
    """The most a table can hold: every row as long a value as is kept, every
    character of it one that escaping makes four, every record it can expand
    as wide. Nothing a record holds takes the display past this.
    """
    keys = {"<" * 1000 + str(i): i for i in range(20)}
    inner = dataclasses.make_dataclass(
        "Inner",
        [(f"f{i}", dict) for i in range(200)],
        bases=(RichDisplay,),
        frozen=True,
    )
    outer = dataclasses.make_dataclass(
        "Outer",
        [(f"r{i}", object) for i in range(200)],
        bases=(RichDisplay,),
        frozen=True,
    )
    record = outer(*[inner(*[keys] * 200) for _ in range(200)])
    html = record._repr_html_()
    assert len(html) < 300_000
    assert len(_parsed(record).findall(".//table")) == 1 + display.MAX_NESTED
    assert max(len(line) for line in _pretty(record).splitlines()) < 200


@pytest.mark.parametrize(
    ("name", "unit"),
    [
        ("levels_db", "dB"),
        ("frequency_hz", "Hz"),
        ("fs", "Hz"),
        ("length_m", "m"),
        ("x_m", "m"),
        ("static_pressure_pa", "Pa"),
        ("wind_speed_m_s", "m/s"),
        ("density_kg_m3", "kg/m\N{SUPERSCRIPT THREE}"),
        ("decay_rates_db_per_m", "dB/m"),
        ("temperature_coefficient_db_per_k", "dB/K"),
        ("temperature_c", "\N{DEGREE SIGN}C"),
        ("peak_temperature_at_10_hz_c", "\N{DEGREE SIGN}C"),
        ("inlet_temperature_k", "K"),
        ("load_current_a", "A"),
        ("fiber_diameter_um", "\N{MICRO SIGN}m"),
        ("relative_humidity_percent", "%"),
        ("thickness_critical_frequency_product_m_hz", "m\N{MIDDLE DOT}Hz"),
        ("burst_s", "s"),
        ("molar_mass_kg_mol", "kg/mol"),
        ("power_hp", "hp"),
        ("wind_speed_kt", "kt"),
        ("speed_kt", "kt"),
        ("volume_mm3", "mm\N{SUPERSCRIPT THREE}"),
        ("signal_fs", "Hz"),
        ("original_fs", "Hz"),
        ("attenuation_db_per_wavelength", "dB/\N{GREEK SMALL LETTER LAMDA}"),
        ("inductance_h", "H"),
        ("curing_time_hours", "h"),
        # A symbol and its subscript, not a unit.
        ("a_atm", ""),
        ("a_bar", ""),
        ("alpha_s", ""),
        ("third_octave_alpha_s", ""),
        ("c_s", ""),
        ("r_tr_s", ""),
        ("r_direct_w", ""),
        ("m", ""),
        ("r_squared", ""),
        ("peak_temperature_c", "\N{DEGREE SIGN}C"),
        # A level or a level difference, in decibels by its head noun.
        ("delta_rw_c", "dB"),
        ("sound_power_level_a", "dB"),
        ("insertion_loss", "dB"),
        ("band_levels", "dB"),
        ("sound_reduction_index_1000", "dB"),
        ("background_corrections", "dB"),
        ("levels_before", "dB"),
        ("band_levels_at_characteristic", "dB"),
        ("spectrum_adaptation_term", "dB"),
        ("l_i_fmax_0", "dB"),
        ("max_spl", "dB"),
        # A statistic of a level, or a word that only ends like one.
        ("sigma_level", ""),
        ("level_uncertainty_db", "dB"),
        ("standard_deviation", ""),
        # The axes the vocabulary names by the bare concept, in their one unit.
        ("frequencies", "Hz"),
        ("octave_frequencies", "Hz"),
        ("levels", "dB"),
        ("background_levels", "dB"),
        ("times", "s"),
        ("distances", "m"),
        ("depths", "m"),
        ("volume", "m\N{SUPERSCRIPT THREE}"),
        ("speeds_of_sound", "m/s"),
    ],
)
def test_the_unit_is_read_from_the_end_of_the_name(name: str, unit: str) -> None:
    assert display.unit_of(name) == unit


def test_a_renamed_band_axis_keeps_its_unit_in_the_table() -> None:
    """``frequencies_hz`` became ``frequencies`` and still shows hertz."""
    check = phonometry.vibration.verify_weighting(
        "Wk", frequencies=[4.0, 8.0, 16.0], measured_factors=[1.0, 1.0, 1.0]
    )
    units = {row.name: row.unit for row in display._rows(check, depth=0)[0]}
    assert units["frequencies"] == "Hz"


def test_a_symbol_says_decibel_only_in_the_package_that_prints_it() -> None:
    """``r_s_w`` is a sound reduction index in ``building`` and nothing elsewhere.

    The R, D and C of the building standards are a distance, a directivity
    and a gain in other packages, so the record's module decides.
    """
    assert display.unit_of("r_s_w", "phonometry.building.measurement") == "dB"
    assert display.unit_of("ctr", "phonometry.building.measurement.ratings") == "dB"
    assert display.unit_of("r_direct", "phonometry.environment.propagation") == ""
    assert display.unit_of("c", "phonometry.underwater.bioacoustics") == ""


def test_a_renamed_level_keeps_its_unit_in_the_table() -> None:
    """``level_db`` became ``level`` and the table still shows decibels."""
    fs = 48_000.0
    record = phonometry.broadcast.quasi_peak_meter(
        np.sin(2.0 * np.pi * 1000.0 * np.arange(int(fs)) / fs), fs
    )
    units = {row.name: row.unit for row in display._rows(record, depth=0)[0]}
    assert units["level"] == "dB"
    assert units["reading"] == ""


def test_a_record_names_the_unit_of_a_bare_field_that_holds_another() -> None:
    """Crossing levels are in the units of the signal, not in decibels."""
    record = phonometry.metrology.level_crossing_rate(
        np.sin(np.linspace(0.0, 40.0 * np.pi, 4000)), fs=1000.0
    )
    units = {row.name: row.unit for row in display._rows(record, depth=0)[0]}
    assert units["levels"] == ""
    assert units["fs"] == "Hz"


@pytest.mark.parametrize(
    "name",
    ["loudness_level", "loudness_level_max", "short_term_loudness_level"],
)
def test_a_loudness_level_is_in_phon(name: str) -> None:
    """ISO 532-1:2017, 3.16, Note 1: a loudness level is expressed in phons."""
    assert display.unit_of(name, "phonometry.psychoacoustics.loudness") == "phon"


def test_the_table_shows_a_loudness_level_in_phon() -> None:
    fs = 48_000.0
    tone = (
        np.sqrt(2.0)
        * 20e-6
        * 10.0**3
        * np.sin(2.0 * np.pi * 1000.0 * np.arange(int(fs)) / fs)
    )
    record = phonometry.psychoacoustics.loudness_zwicker(tone, fs)
    units = {row.name: row.unit for row in display._rows(record, depth=0)[0]}
    assert units["loudness_level"] == "phon"


def test_an_ell_is_a_length_in_materials() -> None:
    """ASTM E2611's distances l1 and l2 are not the L of a level there."""
    module = "phonometry.materials.absorbers.four_microphone"
    assert not display.says_decibels("l1", module)
    assert display.says_decibels("l1", "phonometry.building.measurement")
    matrix = phonometry.materials.TransferMatrix(
        1.0, 0.0, 0.0, 1.0, l1=0.1, s1=0.05, l2=0.1, s2=0.05
    )
    units = {row.name: row.unit for row in display._rows(matrix, depth=0)[0]}
    assert units["l1"] == units["l2"] == units["s1"] == "m"


@pytest.mark.parametrize(
    ("value", "holds"),
    [
        (1.5, True),
        (3, True),
        (np.float32(2.0), True),
        (np.array([1.0, 2.0]), True),
        ((None, 2.0), True),
        ({"a": 1.0}, True),
        ((), True),
        (None, False),
        (True, False),
        (np.False_, False),
        ("LK,x", False),
        (1.0 + 2.0j, False),
        (np.array([1.0 + 0.0j]), False),
        (np.array([True, False]), False),
        (("a", "b"), False),
        ({"a": "b"}, False),
    ],
)
def test_only_a_value_that_holds_a_number_is_in_a_unit(
    value: object, *, holds: bool
) -> None:
    assert display.holds_a_quantity(value) is holds


def test_a_truth_value_or_a_text_shows_no_unit_whatever_its_name() -> None:
    """A bool named for a level, or a text named for an index, is in no unit."""
    condition = phonometry.building.SERVICE_EQUIPMENT_OPERATING_CONDITIONS["water_tap"]
    units = {row.name: row.unit for row in display._rows(condition, depth=0)[0]}
    assert units["max_level"] == units["equivalent_level"] == ""
    limits = phonometry.environment.activity_limits("a")
    units = {row.name: row.unit for row in display._rows(limits, depth=0)[0]}
    assert units["index"] == ""


@functools.cache
def _annotation_names() -> dict[str, object]:
    """What a record's annotations name under ``TYPE_CHECKING`` only.

    The package imports ``NDArray``, ``Mapping`` and the records a field
    holds for the type checker alone, so :func:`typing.get_type_hints`
    reads them from here.
    """
    names: dict[str, object] = {"np": np, "numpy": np, "npt": npt}
    # The band set a record's ``fraction`` holds and the window a spectral
    # result stores, aliases of a private module the records import for the
    # type checker alone.
    names["BandFraction"] = BandFraction
    names["WindowSpec"] = WindowSpec
    for module in (typing, collections.abc, numbers, npt):
        names.update(
            (name, obj) for name, obj in vars(module).items() if name[:1].isupper()
        )
    for module_info in pkgutil.walk_packages(phonometry.__path__, "phonometry."):
        module = importlib.import_module(module_info.name)
        for name, obj in vars(module).items():
            if isinstance(obj, type) and obj.__module__.startswith("phonometry"):
                names.setdefault(name, obj)
    return names


def _arms(annotation: object) -> Iterator[object]:
    """The types a union names, one by one."""
    if typing.get_origin(annotation) in {typing.Union, types.UnionType}:
        for arm in typing.get_args(annotation):
            yield from _arms(arm)
    else:
        yield annotation


def _sample_of(annotation: object) -> object:
    """A value of the kind an annotation names when it holds no number, or None."""
    for arm in _arms(annotation):
        if arm is bool:
            return True
        if arm is str:
            return "a label"
        if arm is complex:
            return 1.0j
        if typing.get_origin(arm) is np.ndarray:
            scalar = (typing.get_args(typing.get_args(arm)[-1]) or (None,))[0]
            if isinstance(scalar, type) and issubclass(
                scalar, np.complexfloating | np.bool_
            ):
                return np.zeros(1, dtype=scalar)
        if isinstance(arm, type) and (
            dataclasses.is_dataclass(arm)
            or (issubclass(arm, tuple) and hasattr(arm, "_fields"))
        ):
            return _stub(arm)
    return None


def _stub(cls: type) -> object:
    """An instance of a record class that no constructor checked."""
    if issubclass(cls, tuple) and isinstance(getattr(cls, "_fields", None), tuple):
        return tuple.__new__(cls, [None] * len(cls._fields))  # type: ignore[attr-defined]
    return object.__new__(cls)


def test_no_public_field_that_holds_no_number_is_shown_in_a_unit() -> None:
    """No truth value, text, complex factor or record field is shown as a level.

    The decibel is read from the head noun of the field's name, and a name
    that says a level (``max_level``), an index (``index``) or a loss
    (``boundary_loss``) can hold a flag, a label, the complex factor
    :math:`F(w)` or a record of its own. Beside any of them the table shows
    only the unit the name spells (``pole_rad_s``, a record of boundaries in
    ``displacement_um``), if any.
    """
    shown = []
    read = 0
    for cls in _public_records():
        hints = typing.get_type_hints(cls, localns=_annotation_names())
        read += 1
        record = _stub(cls)
        for name in (
            [field.name for field in dataclasses.fields(cls)]
            if dataclasses.is_dataclass(cls)
            else list(cls._fields)  # type: ignore[attr-defined]
        ):
            sample = _sample_of(hints.get(name))
            if sample is None:
                continue
            unit = display._unit_in(record, name, sample)
            if unit != display._spelled_unit(name):
                shown.append(f"{cls.__name__}.{name}: {unit}")
    assert read == len(_public_records())
    assert shown == []


#: The fields whose name reads as one unit and whose value is in another, or
#: in none: a sample position named an index, a ratio of energies named an
#: index or a correction, a decimal exponent named a correction, a linear
#: factor named a correction, a mean of an envelope named a level, a tube
#: length written as the ``l`` of ASTM E2611 and a class-number difference.
_MISLEADING_NAMES = (
    ("aircraft.rotorcraft_propagation", "TerrainScreeningResult", "path_difference", "m"),
    ("building.impact_catalogue", "ImpactInsulation", "impact_insulation_class_improvement", ""),
    ("emission.intensity", "IntensityResult", "bias_correction", ""),
    ("environment.propagation.barrier_reflection", "DirectSoundSubtraction", "peak_index", ""),
    ("environment.propagation.barrier_reflection", "ReflectionIndexResult", "reflection_index", ""),
    ("environment.propagation.barrier_reflection", "ReflectionIndexResult", "gain_corrections", ""),
    ("materials.absorbers.four_microphone", "TransferMatrix", "l1", "m"),
    ("materials.absorbers.four_microphone", "TransferMatrix", "s2", "m"),
    ("materials.absorbers.layered", "PerforatedPlateLayer", "end_correction", ""),
    ("materials.absorbers.layered", "MicroperforatedPlateLayer", "end_correction", ""),
    ("metrology.data_qualification", "LevelCrossingResult", "levels", ""),
    ("noise_control.valves", "AerodynamicValveNoise", "efficiency_correction", ""),
    ("noise_control.valves", "Expander", "efficiency_correction", ""),
    ("noise_control.valves", "ValveTrim", "efficiency_correction", ""),
    ("room.auditorium", "AuditoriumQuantity", "just_noticeable_difference", ""),
    ("signals._envelope", "EnvelopeSpectrumResult", "mean_level", ""),
    ("simulation.compute", "Compute", "device_index", ""),
    ("simulation.compute", "RunProvenance", "device_index", ""),
    ("vibration.structural._impact_mobility", "DoubleHitCheck", "impact_indices", ""),
)  # fmt: skip


@pytest.mark.parametrize(
    ("module", "name", "field", "unit"),
    _MISLEADING_NAMES,
    ids=[f"{name}.{field}" for _, name, field, _ in _MISLEADING_NAMES],
)
def test_a_number_its_name_misreads_shows_its_own_unit(
    module: str, name: str, field: str, unit: str
) -> None:
    cls = getattr(importlib.import_module(f"phonometry.{module}"), name)
    assert display._unit_in(_stub(cls), field, 1.0) == unit


def _overriding_records() -> list[type]:
    """Every class of the package that names the unit of a field of its own."""
    found: dict[int, type] = {}
    for module_info in pkgutil.walk_packages(phonometry.__path__, "phonometry."):
        module = importlib.import_module(module_info.name)
        for obj in vars(module).values():
            if isinstance(obj, type) and "_display_units" in vars(obj):
                found[id(obj)] = obj
    return sorted(found.values(), key=lambda cls: f"{cls.__module__}.{cls.__name__}")


@pytest.mark.parametrize("cls", _overriding_records(), ids=lambda cls: cls.__name__)
def test_every_unit_a_record_names_is_needed_and_shown(cls: type) -> None:
    """A ``_display_units`` entry names a field and says what the name does not.

    An entry the name already says would hide nothing if it were deleted; an
    entry for a field the record does not have is a typo that leaves the
    field it meant reading the wrong unit.
    """
    fields = (
        {field.name for field in dataclasses.fields(cls)}
        if dataclasses.is_dataclass(cls)
        else set(cls._fields)  # type: ignore[attr-defined]
    )
    record = object.__new__(cls)
    for name, unit in cls._display_units.items():  # type: ignore[attr-defined]
        assert name in fields
        assert display.unit_of(name, cls.__module__) != unit
        assert display._unit_in(record, name, 1.0) == unit


#: The words that spell a unit and nothing else, at the end of a field's name.
_UNIT_WORDS = frozenset(
    {
        "db", "dba", "hz", "khz", "fs",
        "mm", "um", "cm", "km", "ft", "m2", "m3", "mm2", "mm3",
        "seconds", "ms", "hours", "days",
        "deg", "rad",
        "pa", "kpa", "hpa", "inhg", "atm", "bar",
        "kg", "lb", "mol",
        "knots", "kt", "kmh", "mph",
        "hp", "ohm", "ma", "percent",
    }
)  # fmt: skip

#: Public fields whose name ends in one of those words as the subscript of a
#: symbol: the atmospheric absorption and barrier terms of ISO 9613-2.
_SYMBOL_NAMES = frozenset({"a_atm", "a_bar"})


def test_every_public_field_ending_in_a_unit_shows_it() -> None:
    """A public field whose name spells a unit at its end has that unit.

    The rule reads the end of the name, so the suffix it was not written
    for (``_knots``, ``_seconds``, ``_mm3`` once) shows no unit at all.
    """
    missing = sorted(
        f"{cls.__name__}.{name}"
        for cls in _public_records()
        for name in (
            [field.name for field in dataclasses.fields(cls)]
            if dataclasses.is_dataclass(cls)
            else list(cls._fields)  # type: ignore[attr-defined]
        )
        if name.rsplit("_", 1)[-1].lower() in _UNIT_WORDS
        and "_" in name
        and name not in _SYMBOL_NAMES
        and not display.unit_of(name)
    )
    assert missing == []


class _Opaque:
    """A ``passes`` that is no truth value: asking it for one raises."""

    def __bool__(self) -> bool:
        msg = "an opaque outcome has no truth value"
        raise TypeError(msg)


@dataclasses.dataclass(frozen=True)
class _Undecided(RichDisplay):
    outcome: object

    @property
    def passes(self) -> object:
        return self.outcome


@pytest.mark.parametrize(
    "outcome",
    [None, np.array([True, False]), _Opaque(), "yes", 1],
    ids=["none", "array", "opaque", "text", "int"],
)
def test_a_passes_that_is_no_bool_shows_no_verdict(outcome: object) -> None:
    """Only a bool is a verdict; anything else is shown as none, not read."""
    record = _Undecided(outcome)
    assert _pretty(record).splitlines()[0] == "_Undecided: no verdict"
    caption = _parsed(record).find("table/caption")
    assert caption is not None
    assert "".join(caption.itertext()) == "_Undecidedno verdict"


#: The three editions of the getting-started guide, which show the tables a
#: notebook displays for its two cells.
_GUIDES = tuple(
    pathlib.Path(__file__).resolve().parent.parent / path
    for path in (
        "docs/start/getting-started.md",
        "site/src/content/docs/start/getting-started.mdx",
        "site/src/content/docs/es/start/getting-started.mdx",
    )
)


def _guide_cells() -> tuple[object, object]:
    """The result and the verdict of the guide's two cells, built as it does."""
    from phonometry import building, filters

    fs = 48000
    t = np.arange(fs) / fs
    rng = np.random.default_rng(7)
    noise = np.cumsum(rng.standard_normal(fs))
    noise /= np.std(noise)
    x = 0.4 * np.sin(2 * np.pi * 1000.0 * t) + 0.05 * noise
    bank = filters.octave_filter(x, fs, fraction=3, limits=[20.0, 20000.0])
    check = building.check_lining_curing(curing_time_days=2.9, time_lag_days=1.0)
    return bank, check


@pytest.mark.parametrize("guide", _GUIDES, ids=["docs", "site", "site-es"])
def test_the_guide_shows_the_tables_the_display_writes(guide: pathlib.Path) -> None:
    """The HTML and the text on the page are what the two cells display."""
    bank, check = _guide_cells()
    page = guide.read_text(encoding="utf-8")
    tables = [
        line
        for line in page.splitlines()
        if line.startswith('<div class="phonometry-record">')
    ]
    assert tables == [display.record_html(bank), display.record_html(check)]
    text = f"{display.record_text(bank)}\n\n{display.record_text(check)}"
    assert f"```text\n{text}\n```" in page


def test_short_containers_are_shown_item_by_item() -> None:
    cls = dataclasses.make_dataclass(
        "Containers",
        [
            ("range_hz", tuple),
            ("labels", tuple),
            ("rows", dict),
            ("many", list),
            ("records", tuple),
            ("flags", frozenset),
            ("missing_db", object),
        ],
        bases=(RichDisplay,),
        frozen=True,
    )
    record = cls(
        (50.0, 5000.0),
        tuple(f"label {i}" for i in range(9)),
        {"a": 1, "b": None},
        list(range(100)),
        (_Verdict(2.0), _Verdict(0.0)),
        frozenset({"b", "a"}),
        None,
    )
    text = _pretty(record)
    assert "(50, 5000)  Hz" in text
    assert (
        "tuple of 9 strings: 'label 0', 'label 1', 'label 2', \N{HORIZONTAL ELLIPSIS}"
        in text
    )
    assert "{a: 1, b: None}" in text
    assert "list of 100 numbers, 0 to 99" in text
    assert "tuple of 2 _Verdict" in text
    assert "frozenset of 2: a, b" in text
    assert text.splitlines()[-1] == "  missing_db  None"


class _Pair(NamedTuple):
    first: float
    second_db: float


@dataclasses.dataclass(frozen=True)
class _HoldsPair(RichDisplay):
    pair: _Pair


def test_a_named_tuple_held_in_a_field_is_a_record() -> None:
    record = _HoldsPair(_Pair(1.0, 2.0))
    assert "_Pair (2 fields)" in _pretty(record)
    rows = _parsed(record).findall(".//details/table/tbody/tr")
    assert [tuple("".join(cell.itertext()) for cell in row) for row in rows] == [
        ("first", "1", ""),
        ("second_db", "2", "dB"),
    ]
