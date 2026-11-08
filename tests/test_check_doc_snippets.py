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
import time
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


def test_a_skipped_page_runs_to_show_it_fails_and_its_comments_are_not_held(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A page of the skip list is run, since one that starts running has to
    leave the list, but only that it still fails is read of the run: a wrong
    comment before the line it fails at is not reported.
    """
    ran = tmp_path / "ran.txt"
    page = _page(
        tmp_path,
        f"import pathlib\npathlib.Path({str(ran)!r}).write_text('ran')\n"
        "print(2)  # 3\nraise SystemExit('still fails')",
        name="fine.md",
    )
    monkeypatch.setitem(check_doc_snippets._SKIP, "fine", "reason")
    assert check_doc_snippets.check_execution([page]) == []
    assert ran.read_text(encoding="utf-8") == "ran"


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


def _failures(script: str, outputs: dict[int, str]) -> list[str]:
    """What the output check reports for *script*, run as an English page,
    whose prints wrote *outputs*, keyed by the line each print stands on.
    """
    page = check_doc_snippets._SITE / "page.mdx"
    lines = {number: number for number in range(1, script.count("\n") + 2)}
    # Each print wrote once, in the order of the lines they stand on.
    written = {line: [(line, (" ", [text], "\n"))] for line, text in outputs.items()}
    found: list[str] = check_doc_snippets.output_disagreements(
        page, script, lines, written
    )
    return found


def _held_against(script: str, line: int, texts: list[str]) -> list[str]:
    """What the output check reports for *script*, run as an English page,
    whose print on *line* wrote *texts*, one for each of its arguments.
    """
    page = check_doc_snippets._SITE / "page.mdx"
    lines = {number: number for number in range(1, script.count("\n") + 2)}
    written = {line: [(0, (" ", texts, "\n"))]}
    found: list[str] = check_doc_snippets.output_disagreements(
        page, script, lines, written
    )
    return found


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


def _lost(value: str) -> str:
    return f"the comment's {value} after its ellipsis is never printed"


def test_the_values_after_an_ellipsis_are_promised_where_the_print_stops() -> None:
    """An ellipsis says the print goes on to the values after it, so a print
    that stops before the ellipsis has lost them, as one that goes on and
    never writes them has.
    """
    said = "[99.8 ... 87.7] dB, three thirds summed per octave"
    assert _disagreement(said, "[99.8]") == _lost("87.7")
    assert _disagreement(said, "[99.8 95.0]") == _lost("87.7")
    assert _disagreement(said, "[99.8 87.7]") == ""
    assert _disagreement(said, "[99.8 95.0 87.7]") == ""
    loop = "63 Hz: 45.2 ... 8000 Hz: 30.1"
    assert _disagreement(loop, "63 Hz: 45.2") == _lost("8000")
    assert _disagreement("45.2 dB ... 30.1 dB", "45.2") == _lost("30.1")
    assert _disagreement("[1 ... 9 ... 20]", "[1 5 9]") == _lost("20")
    # An ellipsis with no value after it promises none.
    assert _disagreement("[99.8 ...] dB", "[99.8]") == ""
    assert _disagreement("[0 1 2 ...]", "[0 1 2]") == ""


def test_an_ellipsis_goes_on_over_a_second_one_to_the_values_after_both() -> None:
    """Two ellipses with only words between them leave out one stretch, and
    the values after the second are still the last ones of the output.
    """
    assert _disagreement("[1 ... ... 9]", "[1 2 3]") == _lost("9")
    assert _disagreement("[1 ... ... 9]", "[1 2 9]") == ""
    said = "1 ... one line a band ... 9"
    assert _disagreement(said, ["1", "2", "3"]) == _lost("9")
    assert _disagreement(said, ["1", "2", "9"]) == ""
    arrays = "[0.1 0.2 ...] ... [0.9]"
    assert _disagreement(arrays, "[0.1 0.2 0.3]") == _lost("0.9")
    assert _disagreement(arrays, "[0.1 0.2]") == _lost("0.9")
    assert _disagreement(arrays, ["[0.1 0.2 0.3]", "[0.5 0.9]"]) == ""


def test_a_note_before_an_ellipsis_does_not_end_what_it_promises() -> None:
    """A note between the last printed value and an ellipsis is still a note,
    and the ellipsis after it still says the print goes on to the value after
    it, so a print that stops at the note has lost that value.
    """
    said = "99.8 dB at 125 Hz ... 87.7 dB at 8000 Hz"
    assert _disagreement(said, "99.8 dB") == _lost("87.7")
    assert _disagreement("45.2 dB at 63 Hz ... 30.1 dB at 8000 Hz", "45.2") == _lost(
        "30.1"
    )
    assert _disagreement("[99.8] dB at 1 m ... 87.7", "[99.8] dB") == _lost("87.7")
    brackets = "[99.8] dB at 1 m ... [87.7] dB at 8 m"
    assert _disagreement(brackets, "[99.8]") == _lost("87.7")
    loop = ["99.8 dB at 125 Hz", "97.1 dB at 250 Hz", "87.7 dB at 8000 Hz"]
    assert _disagreement(said, loop) == ""
    assert _disagreement(brackets, ["[99.8] dB at 1 m", "[87.7] dB at 8 m"]) == ""
    # A note with no ellipsis after it keeps its numbers.
    assert _disagreement("0.358  (0.458 with normal hearing)", "0.358") == ""
    assert _disagreement("4.606 1/s", "4.606") == ""
    # A note that writes an ellipsis before a number of its own reads that
    # number as promised; after an arrow it is a note whatever it writes.
    full = "[99.8 97.1 95.0 93.2 91.0 89.4 87.7]"
    octaves = "[99.8 ... 87.7] dB, 7 octaves ... 3 thirds each"
    assert _disagreement(octaves, full) == _lost("3")
    assert _disagreement(octaves.replace(",", " ->"), full) == ""


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


def test_two_numbers_that_share_a_float_are_still_two_numbers() -> None:
    """Equality is decided on the digits too, not on the float they round to.

    2**53 + 1 and 2**53 are one float, and a comment written to the last digit
    of either is held to that digit; so is a number beyond the range of floats,
    which is not the infinity it overflows to.
    """
    assert "9007199254740993" in _disagreement("9007199254740993", "9007199254740992")
    assert _disagreement("9007199254740993", "9007199254740993") == ""
    assert _disagreement("1e400", "inf") != ""
    assert _disagreement("inf", "inf") == ""
    assert _disagreement("-inf", "inf") != ""
    assert _disagreement("-0.0", "0.0") == ""
    # Nor is the gap between them rounded to the 28 digits of the default
    # context: one digit past those, 2**53 + 0.5 and a little more rounds to
    # ...993 at the comment's last digit, and 1.2999...9 still begins with 1.2.
    long_half = "9007199254740992.5000000000000000000000000000001"
    assert "9007199254740992 where" in _disagreement("9007199254740992", long_half)
    assert _disagreement("1", "1.5000000000000000000000000000001") != ""
    assert _disagreement("1.2...", "1.2999999999999999999999999999999") == ""
    assert "1e1000000" in _disagreement("1e1000000", "5")


def test_the_bounds_of_a_number_hold_at_every_exponent() -> None:
    """The bounds a comment's number sets are exact whatever its exponent.

    The exponents of the default context stop near a million, past which the
    step of the last digit overflowed, or underflowed to zero and passed any
    print; a number written with an exponent no decimal holds is held to its
    text, and is reported, not raised.
    """
    assert _disagreement("1e1000000", "1.4e1000000") == ""
    assert _disagreement("1e-1000030", "1.4e-1000030") == ""
    assert _disagreement("1e-1000030", "1.6e-1000030") != ""
    huge = "1e9999999999999999999999"
    assert huge in _disagreement(huge, "5")
    assert _disagreement(huge, huge) == ""
    assert _disagreement("9e999999999999999999", "9e999999999999999999") == ""
    # A bound past the largest exponent is held to the text, not rounded.
    assert _disagreement("~9e999999999999999999", "9e999999999999999999") == ""
    assert _disagreement("~9e999999999999999999", "8.5e999999999999999999") != ""
    # A cut-short value keeps the sign it writes, a negative zero's too.
    assert _disagreement("-0.0...", "-0.0123") == ""
    assert _disagreement("0.0...", "-0.0123") != ""


def test_a_complex_number_holds_at_the_decimals_of_each_part() -> None:
    assert _disagreement("(1.23+4.57j)", "(1.234+4.567j)") == ""
    assert _disagreement("4.57j", "4.567j") == ""
    assert "1.23+4.58j" in _disagreement("(1.23+4.58j)", "(1.234+4.567j)")
    assert "1.24+4.57j" in _disagreement("(1.24+4.57j)", "(1.234+4.567j)")
    # A part the comment does not write is zero, and exactly zero.
    assert _disagreement("4.57j", "(0.001+4.567j)") != ""
    assert _disagreement("1.23", "(1.234+0.5j)") != ""
    assert _disagreement("1.23", "(1.234+0j)") == ""
    # Given roughly, each part is held that way.
    assert _disagreement("~1.2+4.6j", "(1.28+4.52j)") == ""
    assert _disagreement("~1.2+4.6j", "(1.31+4.52j)") != ""
    # An ellipsis cuts short only the digits it follows, those of the last
    # part; a real part the sign closes is written in full and rounds.
    assert _disagreement("1.23+4.56j...", "(1.2345+4.5678j)") == ""
    assert _disagreement("1.23+4.57j...", "(1.2345+4.5678j)") != ""
    assert _disagreement("1.23+4.56j...", "(1.2296+4.5678j)") == ""
    assert _disagreement("1.23+4.56j...", "(1.2391+4.5678j)") != ""
    assert _disagreement("-1.23-4.56j...", "(-1.2296-4.5678j)") == ""
    assert _disagreement("-1.23-4.56j...", "(-1.2391-4.5678j)") != ""
    assert _disagreement("4.56j...", "4.5678j") == ""


def test_a_complex_number_numpy_pads_is_one_value() -> None:
    """NumPy pads the real part of each element to the width of the others."""
    assert _disagreement("1+1j", "1.        +1.j") == ""
    assert _disagreement("1+2j", "1.        +1.j") != ""
    assert _disagreement("[1+1j 1.25-2j]", "[1.  +1.j 1.25-2.j]") == ""
    assert "1.25-3j" in _disagreement("[1+1j 1.25-3j]", "[1.  +1.j 1.25-2.j]")
    # A comment may space the sign out the same way.
    assert _disagreement("1.23 + 4.57j", "(1.234+4.567j)") == ""
    assert _disagreement("1.23 + 4.58j", "(1.234+4.567j)") != ""


def test_a_minus_sign_reads_as_a_hyphen() -> None:
    assert _disagreement("\u22128.27 dB", "-8.27") == ""


def test_a_minus_sign_the_print_writes_reads_as_a_hyphen() -> None:
    """A formatted text that signs a value with U+2212 prints a negative value."""
    assert _disagreement("-8.27 dB", "\u22128.27 dB") == ""
    assert _disagreement("\u22128.27 dB", "\u22128.27 dB") == ""
    assert "8.27" in _disagreement("8.27 dB", "\u22128.27 dB")


def test_a_sign_the_page_writes_before_a_value_is_the_values() -> None:
    """``f"\u2212{x:.2f}"`` prints a negative number, and the hyphen of a
    range, after the value before it, stays the text's.
    """
    script = 'x = 8.27\nprint(f"\u2212{x:.2f} dB")  # \u22128.27 dB\n'
    assert _held_against(script, 2, ["\u22128.27 dB"]) == []
    positive = script.replace("# \u2212", "# ")
    (failure,) = _held_against(positive, 2, ["\u22128.27 dB"])
    assert "the comment says 8.27 where the print wrote -8.27" in failure
    script = 'x = 8.27\nprint(f"dL = -{x:.2f} dB")  # dL = -8.27 dB\n'
    assert _held_against(script, 2, ["dL = -8.27 dB"]) == []
    script = 'a, b = 50, 80\nprint(f"{a}-{b} Hz")  # 50 to 80 Hz\n'
    assert _held_against(script, 2, ["50-80 Hz"]) == []


def test_a_sign_after_a_digit_or_a_letter_joins_in_the_comment_too(
    tmp_path: pathlib.Path,
) -> None:
    """A hyphen right after a digit, a letter, a point or a closing bracket
    joins what stands either side of it wherever it stands, so a comment that
    writes a range or a name as the print writes it is held to the values the
    print wrote, whether its text, its separator or its code wrote the hyphen.
    """
    script = 'a, b = 50, 80\nprint(f"{a}-{b} Hz")  # 50-80 Hz\n'
    assert _held_against(script, 2, ["50-80 Hz"]) == []
    (failure,) = _held_against(script.replace("50-80", "50-90"), 2, ["50-80 Hz"])
    assert "the comment says 90 where the print wrote 80" in failure
    script = 'n = 35\nprint(f"NC-{n}")  # NC-35\n'
    assert _held_against(script, 2, ["NC-35"]) == []
    script = 'n = -35\nprint(f"NC{n}")  # NC-35\n'
    assert _held_against(script, 2, ["NC-35"]) == []
    script = 'x = 0.5\nprint(f"[{x}]-{x}")  # [0.5]-0.5\n'
    assert _held_against(script, 2, ["[0.5]-0.5"]) == []
    # The same text computed whole reads the same way.
    assert _disagreement("50 to 80 Hz", "50-80 Hz") == ""
    assert _disagreement("NC 35", "NC-35") == ""
    # After a space, an opening bracket or an equals sign the sign is the
    # value's, in the comment as in the print.
    assert "-80 where the print wrote 80" in _disagreement("50 -80 Hz", "50 80 Hz")
    assert "-8.27 where the print wrote 8.27" in _disagreement("x=-8.27", "x=8.27")
    assert "-1 where the print wrote 1" in _disagreement("[-1]", "[1]")
    # A sign the page writes before an infinity it formats is the infinity's.
    script = 'x = float("inf")\nprint(f"-{x}")  # -inf\n'
    assert _held_against(script, 2, ["-inf"]) == []
    (failure,) = _held_against(script.replace("# -inf", "# inf"), 2, ["-inf"])
    assert "the comment says inf where the print wrote -inf" in failure
    code = (
        "a, b = 50, 80\nprint(a, b, sep='-')  # 50-80\nprint(a, -b, sep='')  # 50-80\n"
    )
    assert check_doc_snippets.check_execution([_page(tmp_path, code)]) == []


def test_a_spanish_comment_may_write_a_decimal_comma() -> None:
    assert _disagreement("35,9 m", "35.9", decimal_comma=True) == ""
    assert _disagreement("35,9 m", "35.9") != ""


def test_a_spanish_comment_may_write_a_container_without_spaces() -> None:
    """A comma between two digits is a decimal point, or the comma of a list."""
    assert _disagreement("[1,2]", "[1, 2]", decimal_comma=True) == ""
    assert _disagreement("[1,2]", "[1 2]", decimal_comma=True) == ""
    assert _disagreement("[1,2]", "[1, 3]", decimal_comma=True) != ""
    assert _disagreement("1,2", "1.2", decimal_comma=True) == ""
    assert _disagreement("1,2", "1.3", decimal_comma=True) != ""


def test_a_spanish_comma_outside_a_bracket_is_only_a_decimal_point() -> None:
    """Read as a list's, the comma of ``0,5 dB`` would leave a ``0`` that
    rounds the printed ``0.4`` and a ``5`` that the unit after it makes a
    note, so a wrong value would pass.
    """
    assert "0.5 where the print wrote 0.4" in _disagreement(
        "0,5 dB", "0.4 dB", decimal_comma=True
    )
    assert _disagreement("35,9 m", "35.5 m", decimal_comma=True) != ""
    assert _disagreement("36,1 m", "35.6 m", decimal_comma=True) != ""
    assert _disagreement("35,9 m", "35.9 m", decimal_comma=True) == ""
    # A bracket opened on one line goes on over the next, and a decimal
    # comma outside it is still read as a point beside the list.
    assert _disagreement(["[1,2,", " 3,4]"], "[1, 2, 3, 4]", decimal_comma=True) == ""
    assert _disagreement("3,2 dB [1,2]", "3.2 dB [1, 2]", decimal_comma=True) == ""
    assert _disagreement("3,2 dB [1,2]", "3.4 dB [1, 2]", decimal_comma=True) != ""


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


def test_a_zero_cut_short_begins_only_a_zero_of_its_own_sign() -> None:
    """``-0.0...`` does not begin ``0.00``, nor ``0.0...`` a printed ``-0.00``."""
    assert _disagreement("-0.0...", "0.00") != ""
    assert _disagreement("0.0...", "-0.00") != ""
    assert _disagreement("-0.0...", "-0.00") == ""
    assert _disagreement("0.0...", "0.00") == ""
    assert _disagreement("-0.0...", "-0.0123") == ""
    assert _disagreement("0.0...", "0.0123") == ""


def test_an_ellipsis_meets_the_last_line_of_a_long_loop_in_linear_time() -> None:
    """The values before each line end are counted on, not counted again.

    Each line end counted the stated values before it from the first one, so
    the time grew with the square of the lines: 1.4 s for 5,000, 27.5 s for
    20,000 and about a minute for these 30,000.
    """
    loop = [str(n) for n in range(30_000)]
    start = time.perf_counter()
    found = _disagreement("0 ... 29999", loop)
    # Ten seconds against the minute the quadratic count took, and the
    # second the linear one takes: wide enough for a loaded runner.
    assert time.perf_counter() - start < 10.0
    assert found == ""
    assert "30000" in _disagreement("0 ... 30000", loop)


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


def test_a_label_the_print_writes_is_no_quotation_of_a_message() -> None:
    """``Levels: 1`` beside ``print('Levels:', left, right)`` leaves out the 2.

    A comment that quotes a computed message may stop where its quotation
    does; repeating the print's own label quotes nothing, so the values after
    it are still to be stated.
    """
    script = "left, right = 1, 2\nprint('Levels:', left, right)  # Levels: 1\n"
    (failure,) = _held_against(script, 2, ["Levels:", "1", "2"])
    assert "stops before the printed 2" in failure
    full = script.replace("# Levels: 1", "# Levels: 1 2")
    assert _held_against(full, 2, ["Levels:", "1", "2"]) == []


def test_a_quoted_message_does_not_stand_for_a_value_printed_apart() -> None:
    """A quotation may stop inside its message, not before the next argument."""
    script = "print(message, code)  # takes 1 positional argument\n"
    texts = ["takes 1 positional argument but 2 were given", "5"]
    (failure,) = _held_against(script, 1, texts)
    assert "stops before the printed 5" in failure
    assert _held_against(script, 1, texts[:1]) == []


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
    # A comment that opens on any other word is prose about the line, unless
    # the run shows the print writes that word first; this one writes "SEL".
    prose = 'print(f"SEL {1}")  # the level\n'
    (promise,) = check_doc_snippets.promised_outputs(prose)
    assert promise.word == "the"
    assert _failures(prose, {1: "SEL 1"}) == []


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


def test_a_comment_that_names_its_value_is_read_from_after_the_last_equals() -> None:
    """``LWA = 89.7 dB(A)`` states 89.7; arithmetic before the value is read past."""
    script = "x = 89.7\nprint(x)  # LWA = 89.7 dB(A)\n"
    (promise,) = check_doc_snippets.promised_outputs(script)
    assert promise.lines == ("LWA = 89.7 dB(A)",)
    assert _disagreement("LWA = 89.7 dB(A)", "89.7") == ""
    assert "99.9" in _disagreement("LWA = 99.9 dB(A)", "89.7")
    assert _disagreement("C3,4 = 2.31 dB at 1 kHz", "2.31") == ""
    assert "2.32" in _disagreement("C3,4 = 2.32 dB at 1 kHz", "2.31")
    assert _disagreement("Ld = 12 - 10 = 2.0 dB", "2.0") == ""
    assert "2.1" in _disagreement("Ld = 12 - 10 = 2.1 dB", "2.0")


def test_a_named_formula_with_no_value_is_not_read() -> None:
    """``T_B = nperseg/fs`` names what the line computes; it states no output."""
    assert _failures("print(2)  # T_B = nperseg/fs, in s\n", {1: "0.064"}) == []
    assert _failures("print(2)  # Tw = K + C\n", {1: "179.13"}) == []


def test_a_value_offered_as_an_example_is_held_like_any_other() -> None:
    script = "print(90.9)  # e.g. 90.9 dB\nprint(0.73)  # p. ej. 0,73\n"
    first, second = check_doc_snippets.promised_outputs(script)
    assert (first.first, second.first) == (1, 2)
    assert _disagreement("e.g. 90.9 dB re 1 pW", "90.9") == ""
    assert "89.4" in _disagreement("e.g. 89.4 dB re 1 pW", "90.9")
    assert _disagreement("p. ej. 0,73 (A)", "0.73", decimal_comma=True) == ""
    assert _disagreement("p. ej. 0,62 (D)", "0.73", decimal_comma=True) != ""


def test_a_comment_aligned_under_a_second_hash_is_read(tmp_path: pathlib.Path) -> None:
    """``#            # [ 6.57 23.28] dB`` lines its output up under the code."""
    code = "import numpy as np\nprint(np.array([6.57, 23.28]))\n#          # {} dB"
    right = _page(tmp_path, code.format("[ 6.57 23.28]"), name="right.md")
    assert check_doc_snippets.check_execution([right]) == []
    wrong = _page(tmp_path, code.format("[ 9.99 23.28]"), name="wrong.md")
    (failure,) = check_doc_snippets.check_execution([wrong])
    assert "9.99" in failure


def test_a_comment_may_open_on_the_formula_a_print_writes_first() -> None:
    """``(A.4) -0.638 0.035``: the print writes the formula's reference first."""
    script = "print('(A.4)', -0.638, 0.035)  # (A.4) -0.638 0.035\n"
    (promise,) = check_doc_snippets.promised_outputs(script)
    assert promise.text == "(A.4) -0.638 0.035"
    assert _disagreement("(A.4) -0.638 0.035", "(A.4) -0.638 0.035") == ""
    assert "-0.640" in _disagreement("(A.4) -0.640 0.035", "(A.4) -0.638 0.035")
    assert _disagreement("(A.5) -0.638 0.035", "(A.4) -0.638 0.035") != ""


def test_an_empty_container_is_an_output() -> None:
    script = "print(())  # ()\nprint((), [17])  # () [17]\n"
    first, second = check_doc_snippets.promised_outputs(script)
    assert (first.text, second.text) == ("()", "() [17]")
    assert _disagreement("()", "()") == ""
    assert "17" in _disagreement("()", "('17',)")
    assert "19" in _disagreement("() [17]", "() [19]")


def test_a_reference_row_beside_a_print_is_not_read() -> None:
    """A row quoted from the source, opening on its name, is not the output."""
    script = "print([52.0, 42.0])  # Long: 52 42 30 18\n"
    assert _failures(script, {1: "[52. 41.]"}) == []


def test_an_array_the_print_writes_short_is_reported() -> None:
    """A value right after the last one printed is promised, not annotation."""
    why = _disagreement("[0.52 0.7  0.8  0.89]", "[0.52 0.7  0.8 ]")
    assert "0.89" in why
    assert "3" in _disagreement("2 3 4", "2")
    assert "40.0" in _disagreement("True 0.12 (40.0, 315.0)", "True 0.12")
    # After the array closes, a number is annotation again.
    said = "[0.52 0.7  0.8  0.89]  150 mm on the wall"
    assert _disagreement(said, "[0.52 0.7  0.8  0.89]") == ""


def test_a_tuple_the_print_writes_short_is_reported() -> None:
    """A value inside a bracket still open at the last printed one is promised."""
    assert "59225" in _disagreement("(5, 59225)", "(5,)")
    assert "59225" in _disagreement("(5 bands, 59225 samples)", "(5,)")
    assert _disagreement("(5 bands, 59225 samples)", "(5, 59225)") == ""


def test_a_value_a_word_follows_after_the_printed_ones_is_annotation() -> None:
    """A note in brackets or a unit with a figure in it is not a lost value."""
    assert _disagreement("0.358  (0.458 with normal hearing)", "0.358") == ""
    assert _disagreement("4.606 1/s", "4.606") == ""
    assert _disagreement("1479.6, 0.03 % below water", "1479.6") == ""
    # The value a comment opens on is promised whatever follows it.
    assert "3" in _disagreement("3 rooms", "none")


def test_a_value_right_after_the_words_the_print_wrote_is_promised() -> None:
    """The words a comment repeats from the print are the print's, not a note
    of the comment's, so the value right after them is promised as the value
    a comment opens on is, or as one right after the last printed value is.
    """
    none = "the comment says 12.6 where the print wrote no value"
    assert _disagreement("Bands: [12.6, 15.8]", "Bands: []") == none
    assert _disagreement("[12.6, 15.8]", "[]") == none
    bands = "Bands: [12.6, 15.8, ..., 19952.6]  (33 bands)"
    assert _disagreement(bands, "Bands: []") == none
    assert _disagreement(bands, "Bands: [12.6 15.8 16.0 19952.6]") == ""
    two = "Lp: 99.8 Bands: [12.6 15.8]"
    stops = "the print stops before the comment's 12.6"
    assert _disagreement(two, "Lp: 99.8 Bands: []") == stops
    assert _disagreement(two, "Lp: 99.8 Bands: [12.6 15.8]") == ""
    # A word of the comment's own starts a note, and so does a word after
    # a value that follows the printed ones.
    assert _disagreement("engineering (Table 2 class 3)", "engineering") == ""
    assert _disagreement("12.3 s, 5 bands", "12.3 s") == ""


def test_a_value_right_after_the_print_s_own_label_is_promised() -> None:
    """A number of the print's string literal is its label, not a value it
    bore out, so the value after it is the comment's opening one.
    """
    script = 'bands = []\nprint(f"Band 1: {bands}")  # Band 1: [0.5]\n'
    (failure,) = _failures(script, {2: "Band 1: []"})
    assert "the comment says 0.5 where the print wrote no value" in failure
    assert _failures(script, {2: "Band 1: [0.5]"}) == []


def test_a_spanish_page_reads_a_decimal_comma_from_its_path() -> None:
    """The page's path, under the Spanish site, decides the decimal comma."""
    script = "print(35.9)  # 35,9 m\n"
    lines = {1: 1}
    written = {1: [(0, (" ", ["35.9"], "\n"))]}
    spanish = check_doc_snippets._SITE_ES / "page.mdx"
    english = check_doc_snippets._SITE / "page.mdx"
    assert (
        check_doc_snippets.output_disagreements(spanish, script, lines, written) == []
    )
    (failure,) = check_doc_snippets.output_disagreements(
        english, script, lines, written
    )
    assert "35" in failure


def test_the_spanish_pages_run_with_the_english_and_the_mirror() -> None:
    root = check_doc_snippets._ROOT
    pages = [
        check_doc_snippets._SITE / "start" / "page.mdx",
        check_doc_snippets._SITE_ES / "start" / "page.mdx",
        check_doc_snippets._DOCS / "start" / "page.md",
        root / "llms-full.txt",
    ]
    runnable = check_doc_snippets._runnable(pages)
    assert pages[0] in runnable
    assert pages[1] in runnable
    assert pages[2] in runnable
    assert pages[3] not in runnable


def test_a_comment_that_opens_on_the_word_the_print_writes_is_held(
    tmp_path: pathlib.Path,
) -> None:
    """A rating, a class name or a message the code writes is an output."""
    code = 'name, value = "Wk", 15.9\nprint(name, value)  # {}'
    right = _page(tmp_path, code.format("Wk 15.9"), name="right.md")
    assert check_doc_snippets.check_execution([right]) == []
    wrong = _page(tmp_path, code.format("Wk 16.9"), name="wrong.md")
    (failure,) = check_doc_snippets.check_execution([wrong])
    assert "16.9" in failure


def test_a_comment_on_a_word_the_print_does_not_write_is_prose(
    tmp_path: pathlib.Path,
) -> None:
    """The run settles it: a print that writes a number has no word to quote."""
    page = _page(
        tmp_path, "level = 2.5\nprint(level)  # the level of the room, 3 dB up"
    )
    assert check_doc_snippets.check_execution([page]) == []
    (promise,) = check_doc_snippets.promised_outputs("print(x)  # the level\n")
    assert promise.word == "the"


def test_prints_share_lines_that_open_on_a_word_one_line_each(
    tmp_path: pathlib.Path,
) -> None:
    """Three prints, three lines: the last one the rating the third print writes."""
    code = 'grade = "engineering"\nprint(3.7)\nprint(1.8)\nprint(grade)\n# {}\n# 1.8\n# engineering'
    right = _page(tmp_path, code.format("3.7"), name="right.md")
    assert check_doc_snippets.check_execution([right]) == []
    wrong = _page(tmp_path, code.format("3.8"), name="wrong.md")
    (failure,) = check_doc_snippets.check_execution([wrong])
    assert "wrong.md:5: " in failure
    assert "3.8" in failure


def test_a_message_quoted_over_more_lines_than_prints_goes_to_the_last() -> None:
    """Lines that open on a word are not shared out unless one is left per print."""
    script = (
        "print(True)\n"
        "print(message)\n"
        "# Supply: 6 of 8 frequencies are above\n"
        "# (188 Hz), where higher-order modes propagate\n"
        "# describes the plane-wave mode only.\n"
    )
    (promise,) = check_doc_snippets.promised_outputs(script)
    assert promise.first == 2
    assert promise.word == "Supply"
    # The bracket line opens like an output and goes on with the quotation;
    # the line that opens on a word of its own is prose and ends it.
    assert promise.lines == (
        "Supply: 6 of 8 frequencies are above",
        "(188 Hz), where higher-order modes propagate",
    )
    message = (
        "Supply: 6 of 8 frequencies are above the first duct cut-on frequency "
        "(188 Hz), where higher-order modes propagate and so on"
    )
    assert _disagreement(list(promise.lines), message) == ""
    wrong = [promise.lines[0], promise.lines[1].replace("188", "189")]
    assert "189" in _disagreement(wrong, message)


def test_what_follows_an_arrow_may_be_a_note() -> None:
    """``-> moderate (10 % < risk < 50 %)`` notes the line; it is not read."""
    loop = ["male 1.62 1.22 37", "female 1.4 0.96 64"]
    said = "male   1.62 1.22 37   -> moderate  (10 % < risk < 50 %)"
    assert _disagreement(said, loop) == ""
    assert "1.23" in _disagreement(said.replace("1.22", "1.23"), loop)
    # An arrow between two printed values is read past like any punctuation.
    assert _disagreement("4.9 -> 1.6 %", "4.9 1.6") == ""
    assert _disagreement("4.9 -> 1.7 %", "4.9 1.6") != ""
    # When the print writes the arrow, the comment quotes it.
    assert _disagreement("1e-02 -> 6.7 dB", "1e-02 -> 6.7 dB") == ""
    assert _disagreement("1e-02 -> 6.8 dB", "1e-02 -> 6.7 dB") != ""


def test_a_symbol_before_an_approximately_sign_is_read_past() -> None:
    """``ΔLta ≈ 11.1 dB`` opens on its value, given roughly by the ``≈``."""
    script = "print(11.125, 6.0)  # \u0394Lta \u2248 11.1 dB -> Kt = 6 dB\n"
    (promise,) = check_doc_snippets.promised_outputs(script)
    assert promise.word is None
    assert _failures(script, {1: "11.125 6.0"}) == []
    assert _failures(script.replace("11.1 dB", "11.3 dB"), {1: "11.125 6.0"}) != []


def test_a_print_converts_each_argument_once_and_is_held_to_what_it_wrote(
    tmp_path: pathlib.Path,
) -> None:
    """An argument whose text changes each time it is read is read once.

    The recorder converted every argument itself and then let ``print``
    convert it again, so it kept a text the print never wrote and ran the
    conversion a second time in the page's own code.
    """
    code = (
        "class Count:\n"
        "    calls = 0\n"
        "    def __str__(self):\n"
        "        Count.calls += 1\n"
        "        return str(Count.calls)\n"
        "print(Count())  # 1\n"
        "print(Count.calls)  # 1\n"
    )
    assert check_doc_snippets.check_execution([_page(tmp_path, code)]) == []
    wrong = _page(tmp_path, code.replace("# 1\nprint", "# 2\nprint"), name="w.md")
    (failure,) = check_doc_snippets.check_execution([wrong])
    assert "the comment says 2 where the print wrote 1" in failure


def test_a_print_is_held_to_what_it_wrote_before_it_failed(
    tmp_path: pathlib.Path,
) -> None:
    """A print to a closed file wrote nothing, and one whose second argument
    fails to convert wrote the first.
    """
    code = (
        "import io\n"
        "closed = io.StringIO()\n"
        "closed.close()\n"
        "try:\n"
        "    print(2, file=closed)  # 2\n"
        "except ValueError:\n"
        "    pass\n"
    )
    (failure,) = check_doc_snippets.check_execution([_page(tmp_path, code)])
    assert "never runs this print" in failure
    partial = (
        "class Unwritten:\n"
        "    def __str__(self):\n"
        "        raise RuntimeError('no text')\n"
        "try:\n"
        "    print(7, Unwritten())  # 7\n"
        "except RuntimeError:\n"
        "    pass\n"
    )
    page = _page(tmp_path, partial, name="partial.md")
    assert check_doc_snippets.check_execution([page]) == []


def test_a_print_is_read_with_the_separator_and_the_ending_it_was_given(
    tmp_path: pathlib.Path,
) -> None:
    """``sep=""`` joins the values, an ending is written, and a line ends only
    where the print ends one.
    """
    code = (
        "print(1, 2, sep='')  # 12\n"
        "print(1, end=' 2\\n')  # 1 2\n"
        "for x in range(3):\n"
        "    print(x, end=' ')  # 0 1 2\n"
        "print()\n"
    )
    assert check_doc_snippets.check_execution([_page(tmp_path, code)]) == []
    joined = _page(tmp_path, code.replace("# 12", "# 1 2"), name="joined.md")
    (failure,) = check_doc_snippets.check_execution([joined])
    assert "the comment says 1 where the print wrote 12" in failure
    # A loop that writes one line is not stated by its first value alone.
    short = _page(tmp_path, code.replace("# 0 1 2", "# 0"), name="short.md")
    (failure,) = check_doc_snippets.check_execution([short])
    assert "stops before the printed 1" in failure
    # The page's own text and a value it formats into it stay apart.
    script = 'x = 5\nprint(f"A{x}")  # 5\n'
    assert _held_against(script, 2, ["A5"]) == []


def test_a_print_inside_another_statement_is_held() -> None:
    """A call of ``print`` in an assignment or a comprehension writes too."""
    script = "result = print(2)  # 3\n"
    (promise,) = check_doc_snippets.promised_outputs(script)
    assert promise.lines == ("3",)
    (failure,) = _failures(script, {1: "2"})
    assert "the comment says 3 where the print wrote 2" in failure
    spread = "values = [\n    print(x) for x in (1, 2)\n]  # 1\n"
    (promise,) = check_doc_snippets.promised_outputs(spread)
    assert (promise.first, promise.last, promise.lines) == (1, 3, ("1",))
    # The header of a compound statement closes on the call's own line.
    header = "if print(4) is None:  # 4\n    pass\n"
    (promise,) = check_doc_snippets.promised_outputs(header)
    assert (promise.first, promise.last) == (1, 1)


def test_two_prints_in_one_statement_share_its_comment() -> None:
    """Each is held to what both wrote, as two prints on one line are."""
    script = "data = [\n    print(1),\n    print(2),\n]  # 1 2\n"
    promises = check_doc_snippets.promised_outputs(script)
    assert [(p.first, p.last, p.lines) for p in promises] == [(1, 4, ("1 2",))] * 2
    assert _failures(script, {2: "1", 3: "2"}) == []
    (failure, _) = _failures(script.replace("# 1 2", "# 1 3"), {2: "1", 3: "2"})
    assert "the comment says 3 where the print wrote 2" in failure


def test_prints_of_one_statement_are_held_in_the_order_they_wrote(
    tmp_path: pathlib.Path,
) -> None:
    """Two prints of a comprehension, on two lines, take turns: the record
    keeps the calls in the order they came, not gathered line by line.
    """
    code = (
        "data = [\n"
        "    (print(x, end=' '),\n"
        "     print(x + 10, end=' '))\n"
        "    for x in range(2)\n"
        "]  # 0 10 1 11\n"
        "print()\n"
    )
    assert check_doc_snippets.check_execution([_page(tmp_path, code)]) == []
    wrong = code.replace("# 0 10 1 11", "# 0 1 10 11")
    failures = check_doc_snippets.check_execution([_page(tmp_path, wrong, name="w.md")])
    assert len(failures) == 2  # one for each print the comment stands for
    assert all("the comment says 1 where the print wrote 10" in f for f in failures)
    # The calls of the lines of a statement are read by their order.
    script = "data = [\n    print(0),\n    print(10),\n]  # 0 10 1 11\n"
    page = check_doc_snippets._SITE / "page.mdx"
    lines = {number: number for number in range(1, 6)}
    written = {
        2: [(0, (" ", ["0"], " ")), (2, (" ", ["1"], " "))],
        3: [(1, (" ", ["10"], " ")), (3, (" ", ["11"], " "))],
    }
    assert check_doc_snippets.output_disagreements(page, script, lines, written) == []


def test_a_print_inside_a_statement_is_held_to_the_comment_on_its_own_lines() -> None:
    """A comment at the end of the print's own last line, or on the comment
    line under it, inside the statement, is the print's own; the statement's
    comment holds the prints left to it.
    """
    script = "result = (\n    print(2)  # 3\n)\n"
    (promise,) = check_doc_snippets.promised_outputs(script)
    assert (promise.first, promise.last, promise.lines) == (2, 2, ("3",))
    (failure,) = _failures(script, {2: "2"})
    assert "the comment says 3 where the print wrote 2" in failure
    under = "result = (\n    print(2)\n    # 3\n)\n"
    (failure,) = _failures(under, {2: "2"})
    assert "the comment says 3 where the print wrote 2" in failure
    shared = "data = [\n    print(1),  # 1\n    print(2),\n]  # 2\n"
    promises = check_doc_snippets.promised_outputs(shared)
    assert [(p.first, p.last, p.lines) for p in promises] == [
        (1, 4, ("2",)),
        (2, 2, ("1",)),
    ]
    assert _failures(shared, {2: "1", 3: "2"}) == []
    assert _failures(shared.replace("# 2", "# 1 2"), {2: "1", 3: "2"}) != []
    # A note on an argument's line is not the print's output: the
    # statement's comment still holds the print.
    noted = "total = sum([\n    print(2) or 1,  # counted once\n    2,\n])  # 3\n"
    (failure,) = _failures(noted, {2: "2"})
    assert "the comment says 3 where the print wrote 2" in failure


def test_a_print_is_held_to_what_its_file_took(tmp_path: pathlib.Path) -> None:
    """A file that takes part of a write says how much it took, by the count
    its write returns or, when it blocks, on the error it raises.
    """
    code = (
        "import errno\n"
        "class Short:\n"
        "    def write(self, text):\n"
        "        return min(len(text), 1)\n"
        "class Full:\n"
        "    def write(self, text):\n"
        "        raise BlockingIOError(errno.EAGAIN, 'full', 1)\n"
        "print(123, file=Short())  # 1\n"
        "try:\n"
        "    print(456, file=Full())  # 4\n"
        "except BlockingIOError:\n"
        "    pass\n"
    )
    assert check_doc_snippets.check_execution([_page(tmp_path, code)]) == []
    wrong = code.replace("# 1\n", "# 123\n").replace("# 4\n", "# 456\n")
    failures = check_doc_snippets.check_execution([_page(tmp_path, wrong, name="w.md")])
    assert len(failures) == 2
    assert "the comment says 123 where the print wrote 1" in failures[0]
    assert "the comment says 456 where the print wrote 4" in failures[1]


def test_a_long_spanish_comment_is_read_in_linear_time() -> None:
    """The brackets before each comma between two digits are counted on, not
    counted again from the start of the line.

    Counted again, a comment of 40,000 values took about 40 s on this machine.
    """
    count = 40_000
    said = "[" + " ".join(f"{n},5" for n in range(count)) + "]"
    wrote = "[" + " ".join(f"{n}.5" for n in range(count)) + "]"
    start = time.perf_counter()
    found = _disagreement(said, wrote, decimal_comma=True)
    assert time.perf_counter() - start < 10.0
    assert found == ""


def test_a_comment_over_many_lines_is_read_in_linear_time() -> None:
    """The brackets a comment leaves open are counted on as each line joins
    it, not counted again over all of it for each line.

    Counted again, a comment of 40,000 lines took about 23 s on this machine.
    """
    count = 40_000
    rows = "".join(f"#  {n},\n" for n in range(1, count - 1))
    script = f"print(list(range({count})))\n# [0,\n{rows}#  {count - 1}]\n"
    start = time.perf_counter()
    (promise,) = check_doc_snippets.promised_outputs(script)
    assert time.perf_counter() - start < 10.0
    assert len(promise.lines) == count


def test_a_spanish_comment_writes_the_commas_of_its_brackets_one_way() -> None:
    """A comment that writes a decimal comma inside one bracket has said what
    its commas are, so ``[1,2]`` in another bracket of it is 1.2, as a reader
    takes it: the list is written ``[1, 2]`` or ``[1; 2]`` beside it.
    """
    mixed = "[0,5; 1,5] [1,2]"
    assert "the comment says 1.2 where the print wrote 1" in _disagreement(
        mixed, "[0.5, 1.5] [1, 2]", decimal_comma=True
    )
    assert _disagreement(mixed, "[0.5, 1.5] [1.2]", decimal_comma=True) == ""
    for written_out in ("[0,5; 1,5] [1, 2]", "[0,5; 1,5] [1; 2]"):
        assert _disagreement(written_out, "[0.5, 1.5] [1, 2]", decimal_comma=True) == ""


def test_a_page_that_runs_past_its_time_reports_what_it_wrote_on_stderr(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The last line the stopped page wrote on stderr says where it was.

    The page runs without the harness's own imports, which take about a
    second, so that a limit of a few seconds stops it in its sleep.
    """

    def bare(page: pathlib.Path, fixture: str = "") -> tuple[str, dict[int, int]]:
        return page.read_text("utf-8"), {}

    monkeypatch.setattr(check_doc_snippets, "_script", bare)
    monkeypatch.setattr(check_doc_snippets, "_TIMEOUT_S", 3)
    stuck = tmp_path / "stuck.md"
    stuck.write_text(
        "import sys, time\n"
        "print('meshing the room', file=sys.stderr, flush=True)\n"
        "print('solving the 315 Hz band', file=sys.stderr, flush=True)\n"
        "time.sleep(60)\n",
        encoding="utf-8",
    )
    _, error, _ = check_doc_snippets._run_page(stuck)
    assert (
        error == "timed out after 3 s; its last line on stderr: solving the 315 Hz band"
    )
    silent = tmp_path / "silent.md"
    silent.write_text("import time\ntime.sleep(60)\n", encoding="utf-8")
    _, error, _ = check_doc_snippets._run_page(silent)
    assert error == "timed out after 3 s"


def test_a_page_that_writes_bytes_its_streams_cannot_decode_is_still_reported(
    tmp_path: pathlib.Path,
) -> None:
    """A page, or a library it calls, can write raw bytes on stdout or stderr
    that the encoding of its streams does not decode; such a byte is read as
    a replacement character, so the page that fails is reported with its last
    line on stderr and the page that runs is held to its comments, rather
    than the check stopping on the byte. ``0x81`` decodes neither as UTF-8
    nor in code page 1252, the encodings the streams take on the runners.
    """
    fails = _page(
        tmp_path,
        "import sys\nsys.stderr.buffer.write(b'bad\\x81\\n')\nsys.stderr.flush()\n"
        "raise SystemExit(1)",
        name="fails.md",
    )
    runs = _page(
        tmp_path,
        "import sys\nsys.stdout.buffer.write(b'bad\\x81\\n')\nsys.stdout.flush()\n"
        "print(2)  # 2",
        name="runs.md",
    )
    assert check_doc_snippets.check_execution([fails, runs]) == [
        f"{check_doc_snippets._rel(fails)}: bad\ufffd"
    ]
