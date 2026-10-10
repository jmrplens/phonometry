#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Run phonometry in a real notebook kernel and read what each cell put out.

Jupyter, JupyterLab, VS Code and Colab all run a notebook the same way: an
IPython kernel executes each cell, displays its last expression through the
object's ``_repr_html_`` and ``_repr_pretty_``, draws matplotlib figures
through the inline backend and sends warnings to the cell's stderr. None of
that happens in the test suite, which calls the methods directly, so this
executes ``tests/notebooks/smoke.ipynb`` with nbclient on an ipykernel and
then checks, cell by cell, by the tag on each cell:

* ``import``: the package imports in the kernel;
* ``rich-display``: a filter bank result is displayed as its table, in HTML
  and in plain text, not as the dataclass repr;
* ``inline-plot``: ``.plot()`` puts out a PNG through the inline backend;
* ``verdict``: a verdict is displayed with its outcome, FAIL here;
* ``report``: ``.report()`` writes a PDF to a temporary path;
* ``warning``: a :class:`~phonometry.PhonometryWarning` reaches the cell's
  stderr.

A cell that raises fails the run before any of this is read. The notebook is
committed without outputs; this never writes it back. It needs nbclient,
nbformat and ipykernel (``requirements-notebook.txt``), and phonometry with
its ``plot`` and ``report`` extras installed in the same environment.
"""

from __future__ import annotations

import argparse
import base64
import pathlib
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

ROOT = pathlib.Path(__file__).resolve().parent.parent

#: The notebook run by default.
NOTEBOOK = ROOT / "tests" / "notebooks" / "smoke.ipynb"

#: The seconds one cell may take; the slowest renders a PDF fiche.
CELL_TIMEOUT_S = 600

_PNG = b"\x89PNG\r\n\x1a\n"

Outputs = list[dict[str, Any]]


class NotebookError(Exception):
    """A cell did not put out what its tag asks for."""


def _data(outputs: Outputs, kind: str) -> list[dict[str, Any]]:
    """The ``data`` of every output of one type (``execute_result`` ...)."""
    return [output["data"] for output in outputs if output["output_type"] == kind]


def _result(outputs: Outputs) -> dict[str, Any]:
    results = _data(outputs, "execute_result")
    if len(results) != 1:
        msg = f"one displayed result expected, {len(results)} found"
        raise NotebookError(msg)
    return results[0]


def _imports(outputs: Outputs) -> str:
    version = _result(outputs)["text/plain"]
    return f"phonometry {version} imports in the kernel"


def _rich_display(outputs: Outputs) -> str:
    shown = _result(outputs)
    html = shown.get("text/html", "")
    if '<div class="phonometry-record">' not in html:
        msg = f"the result was not displayed as its table: {html[:200]!r}"
        raise NotebookError(msg)
    if "<strong>OctaveFilterResult</strong>" not in html:
        msg = "the table does not name OctaveFilterResult"
        raise NotebookError(msg)
    text = shown["text/plain"]
    if not text.startswith("OctaveFilterResult\n") or "array(" in text:
        msg = f"the plain text is not the table: {text[:200]!r}"
        raise NotebookError(msg)
    return f"a filter bank result is a {len(html)}-character table"


def _inline_plot(outputs: Outputs) -> str:
    images = [data["image/png"] for data in _data(outputs, "display_data")]
    if len(images) != 1:
        msg = f"one inline PNG expected, {len(images)} found"
        raise NotebookError(msg)
    png = base64.b64decode(images[0])
    if not png.startswith(_PNG):
        msg = "the inline figure is not a PNG"
        raise NotebookError(msg)
    return f".plot() renders inline, a {len(png)}-byte PNG"


def _verdict(outputs: Outputs) -> str:
    shown = _result(outputs)
    if ">FAIL</span>" not in shown.get("text/html", ""):
        msg = "the verdict does not show FAIL in its table"
        raise NotebookError(msg)
    first = shown["text/plain"].splitlines()[0]
    if first != "LiningCuringCheck: FAIL":
        msg = f"the plain text opens with {first!r}"
        raise NotebookError(msg)
    return "a verdict is displayed as FAIL"


def _report(outputs: Outputs) -> str:
    header = _result(outputs)["text/plain"]
    if header != "b'%PDF-'":
        msg = f"the fiche does not open as a PDF: {header!r}"
        raise NotebookError(msg)
    return ".report() writes a PDF"


def _warning(outputs: Outputs) -> str:
    stderr = "".join(
        output["text"]
        for output in outputs
        if output["output_type"] == "stream" and output["name"] == "stderr"
    )
    if "PhonometryWarning" not in stderr:
        msg = f"no PhonometryWarning on stderr: {stderr[:200]!r}"
        raise NotebookError(msg)
    return "a PhonometryWarning reaches the cell's stderr"


#: What each tagged cell must have put out, and how it is read.
CHECKS: dict[str, Callable[[Outputs], str]] = {
    "import": _imports,
    "rich-display": _rich_display,
    "inline-plot": _inline_plot,
    "verdict": _verdict,
    "report": _report,
    "warning": _warning,
}


def read(cells: Sequence[Mapping[str, Any]]) -> list[str]:
    """Read the outputs of executed *cells*: one line per check that passed.

    :raises NotebookError: On a check whose cell is missing, and on the first
        cell whose output is not what its tag asks for.
    """
    tagged = {
        tag: cell.get("outputs", [])
        for cell in cells
        for tag in cell.get("metadata", {}).get("tags", [])
    }
    missing = sorted(set(CHECKS) - set(tagged))
    if missing:
        msg = f"the notebook has no cell tagged {', '.join(missing)}"
        raise NotebookError(msg)
    return [check(tagged[tag]) for tag, check in CHECKS.items()]


def run(notebook: pathlib.Path) -> list[str]:
    """Execute *notebook* and return one line per check that passed.

    :raises NotebookError: On a cell that raised, and as :func:`read` does.
    """
    # Imported here: the notebook stack is this script's alone, and
    # tests/test_check_notebook.py imports the script without it.
    import nbformat
    from nbclient import NotebookClient
    from nbclient.exceptions import CellExecutionError

    # nbformat ships py.typed but leaves read() unannotated: reading it
    # through a typed name keeps the call checked under disallow_untyped_calls.
    read_notebook: Callable[..., Any] = nbformat.read
    nb = read_notebook(notebook, as_version=4)
    client = NotebookClient(
        nb,
        timeout=CELL_TIMEOUT_S,
        kernel_name="python3",
        resources={"metadata": {"path": str(notebook.parent)}},
    )
    try:
        client.execute()
    except CellExecutionError as error:
        raise NotebookError(str(error)) from error
    return read(nb.cells)


def main(argv: Sequence[str] | None = None) -> int:
    """Execute the smoke notebook and report what it showed."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "notebook",
        nargs="?",
        type=pathlib.Path,
        default=NOTEBOOK,
        help="the notebook to execute (default: tests/notebooks/smoke.ipynb)",
    )
    arguments = parser.parse_args(argv)
    try:
        lines = run(arguments.notebook)
    except NotebookError as error:
        print(f"::error::{arguments.notebook}: {error}")
        return 1
    for line in lines:
        print(f"ok  {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
