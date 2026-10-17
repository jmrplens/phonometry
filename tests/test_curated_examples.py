#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The one-line examples of the curated API table and the guides still run.

The fenced blocks of the guides are executed by ``scripts/check_doc_snippets.py``;
the examples written inline, in a table cell or a sentence, are not, and they
went stale silently when a record became keyword-only or stopped unpacking:
``PorousLayer(0.05, med)`` raised a ``TypeError`` and ``t, lpaf =
sound_pressure_level_history(...)`` a ``cannot unpack``, with every gate green.
These tests read every inline code span that parses as Python and check the
two shapes that broke against the package itself: a record built with more
positional arguments than its constructor takes, and the result of a function
unpacked like a tuple when the function returns a record that does not
iterate. The migration guide is left out: its left column is the 3.3.0 call,
which is meant not to run any more.
"""

from __future__ import annotations

import ast
import dataclasses
import functools
import importlib
import inspect
import pathlib
import pkgutil
import re
import typing
import warnings

import phonometry

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SPAN = re.compile(r"`([^`\n]+)`")
_BY_POSITION = (
    inspect.Parameter.POSITIONAL_ONLY,
    inspect.Parameter.POSITIONAL_OR_KEYWORD,
)


def _pages() -> list[pathlib.Path]:
    """The curated table, every guide under docs/ and every site guide.

    The site's API pages are generated from the docstrings, which are the
    package's own, so the guides are the ``.mdx`` pages alone.
    """
    pages = sorted((_ROOT / "docs").rglob("*.md"))
    pages += sorted((_ROOT / "site" / "src" / "content" / "docs").rglob("*.mdx"))
    return [page for page in pages if page.stem != "upgrading"]


@functools.cache
def _public() -> dict[str, list[object]]:
    """Every public function and record of the package, by its bare name."""
    found: dict[str, list[object]] = {}
    for info in pkgutil.walk_packages(phonometry.__path__, "phonometry."):
        if any(part.startswith("_") for part in info.name.split(".")[1:]):
            continue
        module = importlib.import_module(info.name)
        for name in getattr(module, "__all__", ()):
            obj = getattr(module, name, None)
            if inspect.isfunction(obj) or (
                inspect.isclass(obj) and dataclasses.is_dataclass(obj)
            ):
                bucket = found.setdefault(name, [])
                if obj not in bucket:
                    bucket.append(obj)
    return found


def _called(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _positional_limit(record: type) -> int:
    signature = inspect.signature(record)
    return sum(1 for p in signature.parameters.values() if p.kind in _BY_POSITION)


def _returns_a_record(function: object) -> type | None:
    """The record *function* returns, if it returns one that does not iterate."""
    try:
        returned = typing.get_type_hints(function).get("return")
    except (NameError, TypeError, AttributeError):
        # A hint naming a TYPE_CHECKING-only import cannot be resolved, and a
        # function whose return cannot be read is not judged.
        return None
    if (
        inspect.isclass(returned)
        and dataclasses.is_dataclass(returned)
        and not hasattr(returned, "__iter__")
    ):
        return returned
    return None


def stale_examples(pages: list[pathlib.Path]) -> list[str]:
    """Every inline example of *pages* that builds or reads a record wrongly."""
    public = _public()
    found: list[str] = []
    for page in pages:
        for lineno, line in enumerate(page.read_text(encoding="utf-8").splitlines(), 1):
            for span in _SPAN.findall(line):
                try:
                    with warnings.catch_warnings():
                        # A span of prose with a backslash is not code either.
                        warnings.simplefilter("ignore", SyntaxWarning)
                        tree = ast.parse(span)
                except SyntaxError:
                    continue
                where = f"{page.name}:{lineno}: {span[:90]}"
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        candidates = public.get(_called(node) or "", [])
                        records = [c for c in candidates if inspect.isclass(c)]
                        # ``...`` stands for arguments the sentence leaves out.
                        written = [
                            a
                            for a in node.args
                            if not (isinstance(a, ast.Constant) and a.value is Ellipsis)
                        ]
                        if (
                            records
                            and len(records) == len(candidates)
                            and len(written) > max(map(_positional_limit, records))
                        ):
                            found.append(f"{where} (builds a record by position)")
                    if (
                        isinstance(node, ast.Assign)
                        and isinstance(node.targets[0], ast.Tuple)
                        and isinstance(node.value, ast.Call)
                    ):
                        candidates = public.get(_called(node.value) or "", [])
                        records = [_returns_a_record(c) for c in candidates]
                        if candidates and all(records):
                            found.append(f"{where} (unpacks a record)")
    return found


def test_no_inline_example_builds_a_record_by_position_or_unpacks_one() -> None:
    """Every inline example of the API table and the guides runs as written."""
    assert stale_examples(_pages()) == []


def test_the_reader_catches_both_shapes(tmp_path: pathlib.Path) -> None:
    """A positional record and an unpacked record are both reported."""
    page = tmp_path / "page.md"
    page.write_text(
        "| `materials.PorousLayer(0.05, med)` |\n"
        "| `t, lpaf = environment.sound_pressure_level_history(sig, fs)` |\n"
        "| `materials.PorousLayer(thickness_m=0.05, medium=med)` |\n",
        encoding="utf-8",
    )
    found = stale_examples([page])
    assert len(found) == 2
    assert "builds a record by position" in found[0]
    assert "unpacks a record" in found[1]
