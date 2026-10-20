#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every number published about where a simulation runs comes from its record.

Two files hold the numbers. ``backend_tolerance.json`` is the bound the
tolerance test holds each backend to, and ``gpu-parity.lock`` is the CuPy
proof: the GPU, the NVIDIA driver, CuPy, the CUDA versions and the energy
difference. The guide "Where a simulation runs" quotes them in English, in
Spanish (with a decimal comma) and in its ``docs/`` mirror; the module
docstrings of the two engines quote the energy bound, and the changelog entry
of the feature quotes the bounds and the versions.

A new measurement that changes a record and leaves a page behind fails here,
and so does a page edited to a number no record holds: each page has to
quote every value of the records, and every bound, CUDA version, CuPy
release, NVIDIA driver and GPU it does quote has to be the recorded one.
The only numbers in those forms that come from nowhere else are the
measured examples of a long run, in :data:`_MEASURED_EXAMPLES`.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from decimal import ROUND_CEILING, Decimal
from pathlib import Path
from typing import Any

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_HERE = Path(__file__).resolve().parent

_RECORD: dict[str, dict[str, Any]] = json.loads(
    (_HERE / "backend_tolerance.json").read_text(encoding="utf-8")
)
_LOCK: dict[str, Any] = json.loads(
    (_ROOT / "gpu-parity.lock").read_text(encoding="utf-8")
)

#: How many significant figures the documents give the CuPy energy bound,
#: rounded up so the quoted bound is never below the measured one.
_ENERGY_DIGITS = 3

#: The long float32 run the documents quote, measured outside the scenario
#: matrix on NumPy and on torch:cpu alike: the acoustic engine on a 200 by
#: 300 cell grid (``dx`` 0.01 m, ``c`` 343 m/s, rigid edges), source at cell
#: (60, 100), probe at (200, 100), 0.1 s or 8085 steps, float32 against
#: float64 at the probe, ``max|a - b| / max|b|``: 8.03e-06 with a 1 kHz
#: ``CWSource`` and 4.05e-06 with ``GaussianPulse(half_width_s=3e-4)``. They
#: illustrate how float32 rounding grows with the steps and bound nothing,
#: so no record holds them; they are written here with two significant
#: figures, as the documents give them.
_MEASURED_EXAMPLES = (Decimal("8.0e-06"), Decimal("4.0e-06"))

_SUPERSCRIPT = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def _ceiling(value: float, digits: int) -> Decimal:
    """*value* rounded up to *digits* significant figures."""
    exact = Decimal(repr(value))
    step = Decimal(1).scaleb(exact.adjusted() - digits + 1)
    rounded = exact.quantize(step, rounding=ROUND_CEILING)
    # 9.991 rounds up to 10.00: one digit too many, and a power of ten more.
    return rounded.quantize(Decimal(1).scaleb(rounded.adjusted() - digits + 1))


def _significant(number: Decimal) -> tuple[str, int]:
    """*number* as the mantissa it is printed with and its power of ten."""
    exponent = number.adjusted()
    return str(number.scaleb(-exponent)), exponent


def _on_page(number: Decimal, decimal_mark: str) -> str:
    """*number* as a page prints it: ``1.79×10⁻¹⁶``, ``3×10⁻⁶``."""
    mantissa, exponent = _significant(number)
    power = str(exponent).translate(_SUPERSCRIPT)
    return f"{mantissa.replace('.', decimal_mark)}×10{power}"


def _in_text(number: Decimal) -> str:
    """*number* as a docstring or the changelog prints it: ``1.79e-16``, ``3e-06``."""
    mantissa, exponent = _significant(number)
    return f"{mantissa}e{exponent:+03d}"


def _bounds() -> dict[str, Decimal | None]:
    """Each backend's published bound, ``None`` where none is published yet."""
    return {
        backend: None
        if entry["max_relative"] is None
        else Decimal(repr(entry["max_relative"]))
        for backend, entry in _RECORD.items()
    }


def _energy() -> Decimal:
    """The worst energy difference of the CuPy proof, as the documents quote it."""
    return _ceiling(max(_LOCK["reductions_max_relative"].values()), _ENERGY_DIGITS)


@dataclass(frozen=True)
class _Page:
    """One version of the guide and how it words what it quotes."""

    path: str
    decimal_mark: str
    #: What a backend without a bound shows in the table's bound column.
    unpublished: str
    #: The sentences that name each version, ``{}`` standing for the value.
    versions: tuple[str, ...]
    #: The sentences that describe the scenario matrix, from :func:`_matrix`.
    matrix: tuple[str, ...]


_ENGLISH_VERSIONS = (
    "{gpu} with NVIDIA driver {nvidia_driver}",
    "CuPy {cupy}",
    "CUDA runtime {cupy_cuda_runtime}",
    "driver API {cuda_driver_api}",
    "and Python {python_minor},",
)
_SPANISH_VERSIONS = (
    "{gpu} con el controlador de NVIDIA {nvidia_driver}",
    "CuPy {cupy}",
    "runtime de CUDA {cupy_cuda_runtime}",
    "API del controlador {cuda_driver_api}",
    "y Python {python_minor},",
)
_ENGLISH_MATRIX = (
    "{count_en} small runs",
    "on grids of {low} to {high} cells stepped {fewest} to {most} times",
    "of the {count_en} scenarios",
    "over those {count_en} runs",
)
_SPANISH_MATRIX = (
    "{count_es} ejecuciones pequeñas",
    "sobre mallas de {low_es} a {high_es} celdas avanzadas entre {fewest} y {most} pasos",
    "de los {count_es} escenarios",
    "en esas {count_es} ejecuciones",
)
#: How a docstring and the changelog entry bound the matrix.
_TEXT_MATRIX = "grids of up to {high} cells, up to {most} steps"
#: What every page's provenance example prints, in any language.
_PROVENANCE_EXAMPLE = (
    "array_library='cupy {cupy}'",
    "cuda_runtime='{cupy_cuda_runtime}'",
    "cuda_driver_api='{cuda_driver_api}'",
    "gpu='{gpu}'",
)

_PAGES = (
    _Page(
        "site/src/content/docs/simulation/compute.mdx",
        ".",
        "not published yet",
        _ENGLISH_VERSIONS + _PROVENANCE_EXAMPLE,
        _ENGLISH_MATRIX,
    ),
    _Page(
        "site/src/content/docs/es/simulation/compute.mdx",
        ",",
        "aún sin publicar",
        _SPANISH_VERSIONS + _PROVENANCE_EXAMPLE,
        _SPANISH_MATRIX,
    ),
    _Page(
        "docs/simulation/compute.md",
        ".",
        "not published yet",
        _ENGLISH_VERSIONS + _PROVENANCE_EXAMPLE,
        _ENGLISH_MATRIX,
    ),
)
_PAGE_IDS = [page.path for page in _PAGES]

#: The engine modules whose docstrings quote the CuPy proof.
_DOCSTRINGS = (
    "src/phonometry/simulation/fdtd.py",
    "src/phonometry/simulation/elastic_fdtd.py",
)

#: The title the changelog entry of the feature opens with.
_CHANGELOG_TITLE = "- **The FDTD engines step on an NVIDIA GPU through CuPy"


def _flat(text: str) -> str:
    """*text* with every run of white space as one space, line breaks included."""
    return " ".join(text.split())


def _read(path: str) -> str:
    return (_ROOT / path).read_text(encoding="utf-8")


def _docstring(path: str) -> str:
    return ast.get_docstring(ast.parse(_read(path))) or ""


def _changelog_entry() -> str:
    """The changelog entry of the feature, from its title to the next entry."""
    lines = _read("CHANGELOG.md").splitlines()
    starts = [k for k, line in enumerate(lines) if line.startswith(_CHANGELOG_TITLE)]
    assert len(starts) == 1, f"one changelog entry opens with {_CHANGELOG_TITLE!r}"
    entry = [lines[starts[0]]]
    for line in lines[starts[0] + 1 :]:
        if line.startswith(("- ", "#")):
            break
        entry.append(line)
    return "\n".join(entry)


def _table_bounds(text: str) -> dict[str, str]:
    """The bound column of the guide's table, by ``device/dtype``.

    A row may name several dtypes (``float64, float32``); each gets the row's
    bound.
    """
    rows = re.findall(
        r"^\| `([a-z:]+)`(?: \(NumPy\))? \| (float\d+(?:, float\d+)*) \| ([^|]+?) \|",
        text,
        re.MULTILINE,
    )
    return {
        f"{device}/{dtype}": bound
        for device, dtypes, bound in rows
        for dtype in dtypes.split(", ")
    }


#: A number in the form a page prints a bound: ``3×10⁻⁶``, ``1,79×10⁻¹⁶``.
_PAGE_NUMBER = re.compile(r"\d+(?:[.,]\d+)?×10[⁻⁰¹²³⁴⁵⁶⁷⁸⁹]+")
#: A number in the form a docstring or the changelog prints one: ``9e-16``.
_TEXT_NUMBER = re.compile(r"(?<![\w.])\d+(?:\.\d+)?e-\d+\b")


#: Each wording that names a version, as ``(what it names, pattern)``; the
#: pattern's group is the value. The general ``CUDA x.y`` stands for either
#: CUDA version; the wordings around it say which one.
_VERSION_WORDINGS: tuple[tuple[str, str], ...] = (
    ("CUDA runtime", r"CUDA runtime (\d+\.\d+)"),
    ("CUDA runtime", r"runtime de CUDA (\d+\.\d+)"),
    ("CUDA runtime", r"CUDA (\d+\.\d+) runtime"),
    ("CUDA runtime", r"cuda_runtime='([^']*)'"),
    ("CUDA driver API", r"driver API (\d+\.\d+)"),
    ("CUDA driver API", r"API del controlador (\d+\.\d+)"),
    ("CUDA driver API", r"(?:supports|admite) CUDA (\d+\.\d+)"),
    ("CUDA driver API", r"cuda_driver_api='([^']*)'"),
    ("CUDA", r"CUDA (\d+\.\d+)"),
    ("CuPy", r"(?:CuPy|cupy|`cupy-cuda\d+x`) (\d+\.\d+\.\d+)"),
    ("NVIDIA driver", r"(?<![\d.])(\d{3}\.\d+\.\d+)(?![\d.])"),
    ("GPU", r"\b((?:RTX|GTX) \d{3,4})\b"),
    ("Python", r"Python (\d+\.\d+)"),
)


def _versions_quoted(text: str) -> list[str]:
    """Every CUDA version, CuPy release, NVIDIA driver, GPU and Python *text* names.

    Each as ``"<what>: <value>"``, for comparison with the lock.
    """
    return [
        f"{what}: {value}"
        for what, pattern in _VERSION_WORDINGS
        for value in re.findall(pattern, text)
    ]


def _python_minor() -> str:
    """The lock's Python as ``major.minor``, the precision the documents give."""
    return ".".join(_LOCK["python"].split(".")[:2])


def _recorded_versions() -> set[str]:
    runtime, driver_api = _LOCK["cupy_cuda_runtime"], _LOCK["cuda_driver_api"]
    return {
        f"CUDA runtime: {runtime}",
        f"CUDA driver API: {driver_api}",
        f"CUDA: {runtime}",
        f"CUDA: {driver_api}",
        f"CuPy: {_LOCK['cupy']}",
        f"NVIDIA driver: {_LOCK['nvidia_driver']}",
        f"Python: {_python_minor()}",
        *(f"GPU: {m}" for m in re.findall(r"(?:RTX|GTX) \d{3,4}", _LOCK["gpu"])),
    }


def _lock_words() -> dict[str, str]:
    """The lock's values a version sentence names, by the name it uses."""
    return {**_LOCK, "python_minor": _python_minor()}


#: The scenario count as each language writes it (two to twelve).
_COUNT_WORDS = {
    "en": dict(
        enumerate(
            (
                "two",
                "three",
                "four",
                "five",
                "six",
                "seven",
                "eight",
                "nine",
                "ten",
                "eleven",
                "twelve",
            ),
            start=2,
        )
    ),
    "es": dict(
        enumerate(
            (
                "dos",
                "tres",
                "cuatro",
                "cinco",
                "seis",
                "siete",
                "ocho",
                "nueve",
                "diez",
                "once",
                "doce",
            ),
            start=2,
        )
    ),
}


def _matrix() -> dict[str, str]:
    """The scenario matrix as backend_tolerance.json describes it.

    The record is held to ``engine_scenarios`` by the tolerance test, so a
    sentence built from it is built from the matrix itself.
    """
    described = {
        (entry["scenarios"], entry["grids"], entry["steps"])
        for entry in _RECORD.values()
        if "scenarios" in entry
    }
    assert len(described) == 1, f"the record describes {len(described)} matrices"
    count, grids, steps = described.pop()
    grid_words = re.fullmatch(r"(\d+ by \d+) to (\d+ by \d+) cells", grids)
    step_words = re.fullmatch(r"(\d+) to (\d+)", steps)
    assert grid_words is not None, grids
    assert step_words is not None, steps
    low, high = grid_words.groups()
    return {
        "count_en": _COUNT_WORDS["en"][count],
        "count_es": _COUNT_WORDS["es"][count],
        "low": low,
        "high": high,
        "low_es": low.replace(" by ", " por "),
        "high_es": high.replace(" by ", " por "),
        "fewest": step_words[1],
        "most": step_words[2],
    }


# The guide, in each of its three versions.


@pytest.mark.parametrize("page", _PAGES, ids=_PAGE_IDS)
def test_the_guide_table_publishes_each_recorded_bound(page: _Page) -> None:
    table = _table_bounds(_read(page.path))
    for backend, bound in _bounds().items():
        assert backend in table, f"{page.path}: no table row for {backend}"
        want = page.unpublished if bound is None else _on_page(bound, page.decimal_mark)
        assert table[backend] == want, (
            f"{page.path}: {backend} shows {table[backend]!r}; "
            f"backend_tolerance.json publishes {want!r}"
        )


@pytest.mark.parametrize("page", _PAGES, ids=_PAGE_IDS)
def test_the_guide_table_publishes_no_bound_without_a_record(page: _Page) -> None:
    for backend, bound in _table_bounds(_read(page.path)).items():
        if _PAGE_NUMBER.fullmatch(bound):
            assert backend in _RECORD, (
                f"{page.path}: the row {backend} publishes {bound} and "
                "backend_tolerance.json has no entry for it"
            )


@pytest.mark.parametrize("page", _PAGES, ids=_PAGE_IDS)
def test_the_guide_quotes_the_cupy_energy_bound(page: _Page) -> None:
    want = _on_page(_energy(), page.decimal_mark)
    assert want in _read(page.path), (
        f"{page.path} does not quote the CuPy energy bound {want} of gpu-parity.lock"
    )


@pytest.mark.parametrize("page", _PAGES, ids=_PAGE_IDS)
def test_every_bound_the_guide_quotes_has_a_source(page: _Page) -> None:
    known = {_on_page(_energy(), page.decimal_mark)}
    known |= {_on_page(b, page.decimal_mark) for b in _bounds().values() if b}
    known |= {_on_page(e, page.decimal_mark) for e in _MEASURED_EXAMPLES}
    unknown = sorted(set(_PAGE_NUMBER.findall(_read(page.path))) - known)
    assert not unknown, (
        f"{page.path} quotes {unknown}, which neither backend_tolerance.json, "
        f"gpu-parity.lock nor the measured examples hold (known: {sorted(known)})"
    )


@pytest.mark.parametrize("page", _PAGES, ids=_PAGE_IDS)
def test_the_guide_names_the_versions_the_proof_ran_on(page: _Page) -> None:
    text = _flat(_read(page.path))
    missing = [
        phrase.format(**_lock_words())
        for phrase in page.versions
        if phrase.format(**_lock_words()) not in text
    ]
    assert not missing, f"{page.path} does not say {missing} (gpu-parity.lock)"


@pytest.mark.parametrize("page", _PAGES, ids=_PAGE_IDS)
def test_the_guide_describes_the_recorded_matrix(page: _Page) -> None:
    text = _flat(_read(page.path))
    missing = [
        phrase.format(**_matrix())
        for phrase in page.matrix
        if phrase.format(**_matrix()) not in text
    ]
    assert not missing, f"{page.path} does not say {missing} (backend_tolerance.json)"


@pytest.mark.parametrize("page", _PAGES, ids=_PAGE_IDS)
def test_every_version_the_guide_names_is_the_recorded_one(page: _Page) -> None:
    stale = sorted(
        set(_versions_quoted(_flat(_read(page.path)))) - _recorded_versions()
    )
    assert not stale, f"{page.path} names {stale}, which gpu-parity.lock does not"


def test_the_guide_promises_bit_identical_fields_only_as_measured() -> None:
    """The three pages say the CuPy fields came out bit for bit; the lock must too."""
    assert _LOCK["fields_bit_identical"] is True, (
        "gpu-parity.lock no longer finds the CuPy fields bit-identical: rewrite the "
        "CuPy promise of the guide (section 6 and the quick answers) to the bound"
    )
    assert _LOCK["phasors_bit_identical"] is True


# The module docstrings and the changelog.


@pytest.mark.parametrize("path", _DOCSTRINGS)
def test_each_engine_docstring_quotes_the_recorded_numbers(path: str) -> None:
    text = _docstring(path)
    want = _in_text(_energy())
    assert want in text, f"{path}: the module docstring does not quote {want}"
    known = {want, *(_in_text(e) for e in _MEASURED_EXAMPLES)}
    unknown = sorted(set(_TEXT_NUMBER.findall(text)) - known)
    assert not unknown, f"{path}: the module docstring quotes {unknown}"
    matrix = _TEXT_MATRIX.format(**_matrix())
    assert matrix in _flat(text), (
        f"{path}: the module docstring does not say {matrix!r}"
    )


def test_the_changelog_entry_quotes_the_recorded_numbers() -> None:
    text = _flat(_changelog_entry())
    published = {_in_text(_energy()), *(_in_text(b) for b in _bounds().values() if b)}
    missing = sorted(n for n in published if n not in text)
    assert not missing, f"the changelog entry does not quote {missing}"
    unknown = sorted(
        set(_TEXT_NUMBER.findall(text))
        - published
        - {_in_text(e) for e in _MEASURED_EXAMPLES}
    )
    assert not unknown, f"the changelog entry quotes {unknown}, which no record holds"
    for phrase in (f"CuPy {_LOCK['cupy']}", _LOCK["gpu"]):
        assert phrase in text, f"the changelog entry does not name {phrase!r}"
    stale = sorted(set(_versions_quoted(text)) - _recorded_versions())
    assert not stale, f"the changelog entry names {stale}, which the lock does not"
    matrix = _TEXT_MATRIX.format(**_matrix())
    assert matrix in text, f"the changelog entry does not say {matrix!r}"


# The formats, on their own.


@pytest.mark.parametrize(
    ("value", "mark", "page", "text"),
    [
        (Decimal("3e-06"), ".", "3×10⁻⁶", "3e-06"),
        (Decimal("9e-16"), ".", "9×10⁻¹⁶", "9e-16"),
        (Decimal("1.79e-16"), ",", "1,79×10⁻¹⁶", "1.79e-16"),
        (Decimal("8.0e-06"), ",", "8,0×10⁻⁶", "8.0e-06"),
    ],
)
def test_a_number_is_printed_as_each_document_prints_it(
    value: Decimal, mark: str, page: str, text: str
) -> None:
    assert (_on_page(value, mark), _in_text(value)) == (page, text)


@pytest.mark.parametrize(
    ("measured", "quoted"),
    [
        (1.7891035517065168e-16, "1.79e-16"),
        (1.7801e-16, "1.79e-16"),
        (1.78e-16, "1.78e-16"),
        (9.991e-16, "1.00e-15"),
    ],
)
def test_the_energy_bound_is_rounded_up(measured: float, quoted: str) -> None:
    assert _in_text(_ceiling(measured, _ENERGY_DIGITS)) == quoted


def test_each_wording_reads_the_version_it_names() -> None:
    text = (
        "with the CUDA 13.2 runtime, on a driver that supports CUDA 13.3; CUDA "
        "runtime 13.2, driver API 13.3, runtime de CUDA 13.2, API del "
        "controlador 13.3, cuda_runtime='13.2', cuda_driver_api='13.3', "
        "Python 3.13"
    )
    found = set(_versions_quoted(text))
    assert {
        "CUDA runtime: 13.2",
        "CUDA driver API: 13.3",
        "Python: 3.13",
    } <= found
    assert "CUDA driver API: 13.2" not in found
    assert "CUDA runtime: 13.3" not in found


def test_the_table_reader_finds_every_row_of_the_guide() -> None:
    rows = _table_bounds(_read(_PAGES[0].path))
    assert set(_RECORD) <= set(rows)
    assert rows["torch:cuda/float64"] == rows["torch:cuda/float32"] == "not measured"
