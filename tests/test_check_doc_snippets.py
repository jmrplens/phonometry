#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The documentation-snippet gate must fail on the defects it exists for.

A gate that only ever passes proves nothing, so each check is fed the defect
it was written for and asserted to report it, and then fed the correct page
and asserted to stay quiet. The shadowing case is the one that motivated the
script: ``from scipy import signal`` next to ``from phonometry import
signals`` is fine, but rebinding an imported name is not, and Python says
nothing either way.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest

_SCRIPT = (
    pathlib.Path(__file__).resolve().parent.parent / "scripts" / "check_doc_snippets.py"
)
# The script reads its fences through scripts/markdown_fences.py, which it
# imports as a sibling, the way it runs from the command line.
if str(_SCRIPT.parent) not in sys.path:
    sys.path.insert(0, str(_SCRIPT.parent))
_spec = importlib.util.spec_from_file_location("check_doc_snippets", _SCRIPT)
assert _spec is not None
assert _spec.loader is not None
check_doc_snippets = importlib.util.module_from_spec(_spec)
sys.modules["check_doc_snippets"] = check_doc_snippets
_spec.loader.exec_module(check_doc_snippets)


def _page(tmp_path: pathlib.Path, *blocks: str, name: str = "page.md") -> pathlib.Path:
    body = "\n".join(f"```python\n{b.strip()}\n```\n" for b in blocks)
    path = tmp_path / name
    path.write_text("Prose.\n\n" + body, encoding="utf-8")
    return path


def test_rebinding_an_imported_name_is_reported(tmp_path: pathlib.Path) -> None:
    page = _page(
        tmp_path,
        """
from phonometry import signals

signals = [1.0, 2.0]
""",
    )
    (failure,) = check_doc_snippets.check_shadowing([page])
    assert "'signals = ...' rebinds" in failure


def test_second_import_of_the_same_name_is_reported(tmp_path: pathlib.Path) -> None:
    page = _page(
        tmp_path,
        """
from phonometry import signals
from scipy import signals
""",
    )
    (failure,) = check_doc_snippets.check_shadowing([page])
    assert "rebinds the name imported from phonometry" in failure


def test_the_rebinding_is_caught_across_blocks(tmp_path: pathlib.Path) -> None:
    """A page is read top to bottom; the import of block 0 is still in scope."""
    page = _page(
        tmp_path,
        "from phonometry import signals\n\nx = signals.leq([1.0], 48000)",
        "signals = [1.0, 2.0]\nprint(signals)",
    )
    (failure,) = check_doc_snippets.check_shadowing([page])
    assert "block 1" in failure


def test_a_generated_dump_does_not_carry_imports_across_pages(
    tmp_path: pathlib.Path,
) -> None:
    """A dump glues unrelated pages: their blocks share no scope."""
    dump = _page(
        tmp_path,
        "from phonometry import envelope\n\nenvelope(x, fs)",
        "envelope = 2.0\nprint(envelope)",
        name="dump.txt",
    )
    assert check_doc_snippets.check_shadowing([dump]) != []
    assert check_doc_snippets.check_shadowing([dump], carry=False) == []


def test_a_different_name_next_to_scipy_is_fine(tmp_path: pathlib.Path) -> None:
    """The permitted arrangement: distinct names, so neither is shadowed."""
    page = _page(
        tmp_path,
        """
from scipy import signal
from phonometry import signals

b, a = signal.butter(2, 0.2)
level = signals.leq([1.0], 48000)
""",
    )
    assert check_doc_snippets.check_shadowing([page]) == []


def test_a_translation_that_drops_an_import_is_reported(tmp_path: pathlib.Path) -> None:
    en = _page(tmp_path, "from phonometry import leq, sel", name="en.md")
    es = _page(tmp_path, "from phonometry import leq", name="es.md")
    (failure,) = check_doc_snippets.check_translations([(en, es)])
    assert "missing phonometry.sel" in failure


def test_a_translation_that_only_changes_its_strings_is_fine(
    tmp_path: pathlib.Path,
) -> None:
    en = _page(tmp_path, 'from phonometry import leq\nprint("Level")', name="en.md")
    es = _page(
        tmp_path,
        'from phonometry import leq\nprint("Nivel")  # traducido',
        name="es.md",
    )
    assert check_doc_snippets.check_translations([(en, es)]) == []


def test_a_page_that_does_not_run_is_reported(tmp_path: pathlib.Path) -> None:
    page = _page(tmp_path, "raise SystemExit('boom')")
    (failure,) = check_doc_snippets.check_execution([page])
    assert "boom" in failure


def test_a_sketch_of_a_call_is_read_but_not_run(tmp_path: pathlib.Path) -> None:
    """``f(...)`` shows the shape of a call; running it proves nothing."""
    page = _page(tmp_path, "from phonometry import leq\n\nlevel = leq(...)")
    assert check_doc_snippets.check_execution([page]) == []
    # A keyword placeholder is the same sketch written differently.
    kw = _page(
        tmp_path,
        "from phonometry import leq\n\nlevel = leq(x=...)",
        name="kw.md",
    )
    assert check_doc_snippets.check_execution([kw]) == []
    # It is still read: a rebinding in the same block is still a failure.
    bad = _page(
        tmp_path,
        "from phonometry import leq\n\nlevel = leq(...)\nleq = 3.0",
        name="bad.md",
    )
    assert check_doc_snippets.check_shadowing([bad]) != []


def test_a_stale_skip_entry_is_reported(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A page that starts running must leave the skip list."""
    page = _page(tmp_path, "print('runs fine')", name="fine.md")
    monkeypatch.setitem(check_doc_snippets._SKIP, "fine", "reason")
    (failure,) = check_doc_snippets.check_execution([page])
    assert "runs now" in failure


def test_a_skip_entry_stays_while_one_edition_still_fails(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An entry names a guide, and a guide is written twice.

    The site page and the hand-written mirror under ``docs/`` share a stem, so
    one entry covers both. Reporting it stale the moment either one runs would
    turn the report into a failing page on the next run.
    """
    site = _page(tmp_path, "print('runs fine')", name="fine.md")
    mirror_dir = tmp_path / "mirror"
    mirror_dir.mkdir()
    mirror = _page(mirror_dir, "raise SystemExit('still broken')", name="fine.md")
    monkeypatch.setitem(check_doc_snippets._SKIP, "fine", "reason")
    assert check_doc_snippets.check_execution([site, mirror]) == []
    # Once both editions run, the entry has to go, and it is reported once.
    mirror.write_text("```python\nprint('now fine too')\n```\n", encoding="utf-8")
    failures = check_doc_snippets.check_execution([site, mirror])
    assert len(failures) == 1
    assert "runs now" in failures[0]


def test_a_fixture_writes_the_file_a_page_reads(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A page that reads a file the reader brings runs on one the harness
    writes first, in the directory the page runs in; without it, it fails.
    """
    page = _page(tmp_path, "print(open('take.txt').read())", name="reads.md")
    (failure,) = check_doc_snippets.check_execution([page])
    assert "take.txt" in failure
    monkeypatch.setitem(
        check_doc_snippets._FIXTURES, "reads", "open('take.txt', 'w').write('x')\n"
    )
    assert check_doc_snippets.check_execution([page]) == []


_HOME_PAGE = """export const x = 1;
const RUNS_CODE = `values = [1, 2]  # the \\`values\\` a backtick quotes
total, = [sum(values)]`;

const FAILS_CODE = `from phonometry import filters
spl, freq = filters.octave_filter([0.0] * 4800, fs=48_000)`;
"""


def test_the_home_page_examples_are_read_from_its_data_module(
    tmp_path: pathlib.Path,
) -> None:
    """The home page prints its code from template literals, not fences."""
    page = tmp_path / "home.ts"
    page.write_text(_HOME_PAGE, encoding="utf-8")
    runs, fails = check_doc_snippets._blocks(page)
    assert runs.splitlines() == [
        "values = [1, 2]  # the `values` a backtick quotes",
        "total, = [sum(values)]",
    ]
    assert fails.startswith("from phonometry import filters")


def test_a_home_page_example_that_does_not_run_is_reported(
    tmp_path: pathlib.Path,
) -> None:
    """The landing page unpacked a result into two arrays for a release."""
    page = tmp_path / "home.ts"
    page.write_text(_HOME_PAGE, encoding="utf-8")
    (failure,) = check_doc_snippets.check_execution([page])
    assert "cannot unpack" in failure


def test_the_home_page_is_one_of_the_published_surfaces() -> None:
    assert check_doc_snippets._HOME in check_doc_snippets._published()
    assert check_doc_snippets._blocks(check_doc_snippets._HOME)


def test_an_output_comment_the_print_contradicts_is_reported(
    tmp_path: pathlib.Path,
) -> None:
    """The planted case: the comment promises 3, the print writes 2.

    The failure names the line of the page the print stands on (the fence
    opens on line 3, so its second line is line 5) and both texts.
    """
    page = _page(tmp_path, "total = 1 + 1\nprint(total)  # 3 rooms")
    (failure,) = check_doc_snippets.check_execution([page])
    assert failure.startswith(f"{page.as_posix()}:5: ")
    assert "'3 rooms'" in failure
    assert "'2'" in failure


def test_an_output_comment_the_print_bears_out_passes(tmp_path: pathlib.Path) -> None:
    page = _page(tmp_path, "total = 1 + 1\nprint(total)  # 2 rooms")
    assert check_doc_snippets.check_execution([page]) == []


def test_the_comment_on_the_line_after_the_print_is_its_output(
    tmp_path: pathlib.Path,
) -> None:
    wrong = _page(tmp_path, "print(2 * 3)\n# 7", name="wrong.md")
    (failure,) = check_doc_snippets.check_execution([wrong])
    assert "wrong.md:4: " in failure
    right = _page(tmp_path, "print(2 * 3)\n# 6", name="right.md")
    assert check_doc_snippets.check_execution([right]) == []


def test_a_comment_that_states_no_value_is_not_read(tmp_path: pathlib.Path) -> None:
    page = _page(tmp_path, "print(2 * 3)  # the count of rooms\n# Now the next step")
    assert check_doc_snippets.check_execution([page]) == []


def test_a_print_the_page_never_reaches_is_reported(tmp_path: pathlib.Path) -> None:
    """A promised output that no run writes is one no reader sees either."""
    page = _page(tmp_path, "if 1 > 2:\n    print(3)  # 3")
    (failure,) = check_doc_snippets.check_execution([page])
    assert "page.md:5: " in failure
    assert "never" in failure


def test_a_page_that_fails_reports_the_failure_and_no_output(
    tmp_path: pathlib.Path,
) -> None:
    """The comments of a page that stops are not read: the stop is the news."""
    page = _page(tmp_path, "print(2)  # 3\nraise SystemExit('boom')")
    (failure,) = check_doc_snippets.check_execution([page])
    assert "boom" in failure


def _disagreement(
    promised: str | list[str], written: str | list[str], **options: bool
) -> str:
    why: str = check_doc_snippets.output_disagreement(promised, written, **options)
    return why


def test_words_after_the_last_value_are_annotation() -> None:
    assert _disagreement("0.67 m and 5 s: the second room of 3", "0.67 5") == ""
    assert _disagreement("0.68 m and 5 s: the second room of 3", "0.67 5") != ""


def test_a_unit_between_two_values_is_read_past() -> None:
    assert _disagreement("78.2 Hz, 38.6 Hz -> valid here", "78.2 38.6") == ""
    assert "38.7" in _disagreement("78.2 Hz, 38.7 Hz", "78.2 38.6")


def test_a_comment_that_stops_before_the_print_does_is_reported() -> None:
    assert "stops before the printed 2" in _disagreement("1", "1 2")


def test_a_label_the_print_writes_need_not_be_repeated() -> None:
    """Words around the values, a label or a class name, are the print's own."""
    assert _disagreement("3.2 dB", "Leq: 3.2") == ""
    assert _disagreement("1.5", "[np.float64(1.5)]") == ""


def test_a_quoted_word_is_the_word_the_print_opens_with() -> None:
    assert _disagreement("'tangency'  (the NC-32 curve is exceeded)", "tangency") == ""
    assert "'highly'" in _disagreement("'highly impulsive'", "impulsive")


def test_constants_are_values() -> None:
    assert _disagreement("True False True", "True False True") == ""
    assert "False" in _disagreement("True True", "True False")
    assert _disagreement("None 13", "None 13") == ""
    assert _disagreement("nan", "nan") == ""


def test_an_ellipsis_stands_for_the_values_it_leaves_out() -> None:
    written = "[0 1 2 3 4 5 6 7 8 9]"
    assert _disagreement("[0, 1, ..., 9]", written) == ""
    assert _disagreement("[0 1 2 ...]", written) == ""
    assert "never printed" in _disagreement("[0, 1, ..., 8] dB", "[0 1 2 3 4 5 6 7 9]")


def test_a_number_holds_at_the_decimals_it_is_written_to() -> None:
    assert _disagreement("0.67", "0.6666666666666666") == ""
    assert _disagreement("126", "125.89254117941672") == ""
    assert _disagreement("1.50", "1.5") == ""
    assert _disagreement("2e-05", "2e-5") == ""
    assert "0.66" in _disagreement("0.66", "0.6666666666666666")
    assert "125" in _disagreement("125", "125.89254117941672")


def test_a_number_holds_at_its_last_digit_down_to_the_last_bit_of_a_float() -> None:
    """The rounding is decided on the digits as written, not on floats.

    Thirteen decimals of 410.22701513439057 round to 410.2270151343906, a
    difference smaller than the spacing of floats near 410; and a printed
    value exactly half a unit away from the comment's still rounds to it.
    """
    assert _disagreement("410.2270151343906", "410.22701513439057") == ""
    assert _disagreement("410.2270151343905", "410.22701513439057") != ""
    assert _disagreement("0.3", "0.35") == ""
    assert _disagreement("0.3", "0.3500000000000001") != ""
    assert _disagreement("55.350667...", "55.3506679999999999") == ""
    assert _disagreement("55.350667...", "55.350668") != ""


def test_a_minus_sign_reads_as_a_hyphen() -> None:
    assert _disagreement("\u22128.27 dB", "-8.27") == ""


def test_a_spanish_comment_may_write_a_decimal_comma() -> None:
    assert _disagreement("35,9 m", "35.9", decimal_comma=True) == ""
    assert _disagreement("35,9 m", "35.9") != ""


def test_a_comment_continues_while_its_brackets_are_open() -> None:
    script = "print({'a': 1, 'b': 2})\n# {'a': 1,\n#  'b': 3}\nx = 1\n# 5\n"
    (promise,) = check_doc_snippets.promised_outputs(script)
    assert promise.text == "{'a': 1, 'b': 3}"
    assert (promise.first, promise.last) == (1, 1)


def test_a_comment_beside_a_loop_states_its_first_lines() -> None:
    """A print in a loop writes a line each time; its comment states the first."""
    calls = ["1000000 0.288", "712426 0.267", "522582 0.236"]
    assert _disagreement("1000000 0.288", calls) == ""
    assert "0.289" in _disagreement("1000000 0.289", calls)
    # Stopping inside a line is still stopping short.
    assert "stops before" in _disagreement("1000000", calls)


def test_a_comment_over_several_lines_may_state_one_line_each() -> None:
    """Each line of the comment states a line of the output, with its own note."""
    said = [
        "0.6 2.61 3.34   over-damped: no longer resonant at 300 Hz",
        "1.0 1.0 -0.0    matched",
    ]
    calls = ["0.6 2.61 3.34", "1.0 1.0 -0.0", "1.7 0.52 -1.93"]
    assert _disagreement(said, calls) == ""
    said[1] = "1.0 1.1 -0.0    matched"
    assert _disagreement(said, calls) != ""


def test_an_ellipsis_ends_on_the_last_values_of_a_line() -> None:
    written = "[2.76 2.95 2.95 2.95 2.95 2.95]"
    assert _disagreement("[2.76 2.95 2.95 ... 2.95] m", written) == ""
    increments = "[0.1 0.3 0.4 0.7 1.2 3.6]"
    assert _disagreement("[0.1 0.3 ... 3.6] dB, 200 ft to 25000 ft", increments) == ""
    assert _disagreement("[0.1 0.3 ... 3.7] dB", increments) != ""
    loop = ["0.6 [0.18 0.53]", "1.0 [0.24 0.57]", "7.0 [0.45 0.65]"]
    assert _disagreement("0.6 [0.18 0.53]  ...  7.0 [0.45 0.65]", loop) == ""
    assert "0.44" in _disagreement("0.6 [0.18 0.53]  ...  7.0 [0.44 0.65]", loop)


def test_a_number_in_powers_of_ten_holds_at_its_last_digit() -> None:
    assert _disagreement("1.0012e6", "1001249.2197250392") == ""
    assert _disagreement("1.0013e6", "1001249.2197250392") != ""


def test_a_rough_value_holds_within_a_unit_of_its_last_digit() -> None:
    assert _disagreement("~1e-14", "1.840194663316197e-14") == ""
    assert _disagreement("~1e-14", "2.6e-14") != ""


def test_digits_cut_short_hold_as_the_start_of_the_printed_ones() -> None:
    assert _disagreement("55.350667... dB", "55.35066774343508") == ""
    assert _disagreement("55.350668... dB", "55.35066774343508") != ""


def test_a_unit_power_and_a_symbol_index_are_not_values() -> None:
    assert _disagreement("4.9 m/s^1.5 -> 1.6 % over 240 s", "4.9 1.6") == ""
    assert _disagreement("0.38, against A(8) = 0.38 m/s^2", "0.38") == ""


def test_a_quoted_message_may_stop_where_its_quotation_does() -> None:
    written = (
        "'integration_time' must be one of the time constants Tables 10 and 11 "
        "print (0.125, 1, 8 s)"
    )
    said = "'integration_time' must be one of the time constants Tables 10 and 11"
    assert _disagreement(said, written) == ""
    assert _disagreement(said.replace("11", "12"), written) != ""


def test_one_value_states_an_output_that_is_that_value_throughout() -> None:
    assert _disagreement("10.0 in every band", "[10. 10. 10.]") == ""
    assert _disagreement("10.0 in every band", "[10. 10. 9.9]") != ""


def test_a_bracket_around_words_is_not_an_output() -> None:
    script = "print((3, 4))  # (n_samples,) the broadband response\n"
    assert check_doc_snippets.promised_outputs(script) == []


def test_prints_one_under_another_share_the_comment_lines_under_them() -> None:
    script = "print(1.8)\nprint(2.9, 7)\n# 1.8\n# 2.9 7\n"
    first, second = check_doc_snippets.promised_outputs(script)
    assert (first.first, first.lines) == (1, ("1.8",))
    assert (second.first, second.lines) == (2, ("2.9 7",))


def test_a_number_the_print_s_own_text_writes_is_a_label(
    tmp_path: pathlib.Path,
) -> None:
    """Only the values the code computes are held; the label is the page's own."""
    code = (
        'x = 87.04\nprint(f"one-sided 95 % upper limit LEX,8h + U = {x:.1f} dB")  # {}'
    )
    right = _page(tmp_path, code.replace("{}", "87.0 dB"), name="right.md")
    assert check_doc_snippets.check_execution([right]) == []
    wrong = _page(tmp_path, code.replace("{}", "87.1 dB"), name="wrong.md")
    (failure,) = check_doc_snippets.check_execution([wrong])
    assert "87.1" in failure


def test_a_comment_may_open_on_the_word_the_print_s_label_opens_with() -> None:
    """A print that writes its label first has a comment that quotes it first."""
    script = (
        "x = 3.36\n"
        'print(f"10 dB-down window: {x:.2f} s")\n'
        'print(f"SEL over the window {-x:.2f} dBFS")\n'
        "# 10 dB-down window: 3.36 s\n"
        "# SEL over the window -3.36 dBFS\n"
    )
    first, second = check_doc_snippets.promised_outputs(script)
    assert first.lines == ("10 dB-down window: 3.36 s",)
    assert second.lines == ("SEL over the window -3.36 dBFS",)
    # A comment that opens on any other word is still prose about the line.
    assert check_doc_snippets.promised_outputs('print(f"SEL {1}")  # the level\n') == []


def test_a_run_that_leaves_no_record_of_its_prints_is_reported(
    tmp_path: pathlib.Path,
) -> None:
    """A page that ends the interpreter at once never saves what it printed."""
    page = _page(tmp_path, "import os\n\nprint(2)  # 2\nos._exit(0)")
    (failure,) = check_doc_snippets.check_execution([page])
    assert "without saving" in failure


def test_a_comma_the_print_itself_writes_is_read_as_written() -> None:
    """On a Spanish page a comma is a decimal point, or the print's own text."""
    row = "['01_pared_de_ladrillo', 'Pared de ladrillo', '', '', '0,025']"
    assert _disagreement(row, row, decimal_comma=True) == ""
    assert _disagreement("0,026", "0.025", decimal_comma=True) != ""
