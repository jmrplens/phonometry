#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The gate on scripts that read a markdown fence without the shared reader.

``scripts/check_fence_readers.py`` refuses a toggle flipped on a fence, a
string test for a fence marker and a regular expression for one, anywhere in
``scripts/`` but ``scripts/markdown_fences.py``, and any marker spelled in the
site's own code but ``site/src/lib/markdown-fences.mjs``. The eight readers it
was written against are here in their own shapes: the slice compared with a
tuple of markers that read the headings of the overview pages, the three
regular expressions that blanked the code of a page or took its Python
examples out, and the four the site's code used to count words, find the
citation block, skip code in the maths check and in the figure check. So are
the other ways Python has of spelling the same reading, and the shapes the
gate must not refuse, because two generators write fences, a markdown check
looks for a line that would open one and two figure checks flip ``inside``.
"""

from __future__ import annotations

import pathlib
import sys
import textwrap

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_fence_readers as cfr


def _shapes(
    tmp_path: pathlib.Path, source: str, name: str = "reader.py"
) -> list[tuple[str, str]]:
    """``(function, shape)`` for each place a script written from ``source`` reads a fence."""
    path = tmp_path / name
    path.write_text(textwrap.dedent(source), encoding="utf-8")
    return [(f.function, f.shape) for f in cfr.findings(path)]


def test_a_toggle_on_a_fence_is_refused(tmp_path: pathlib.Path) -> None:
    """The shape every hand-written reader starts from."""
    assert _shapes(
        tmp_path,
        """
        def prose(lines):
            fenced = False
            for line in lines:
                if line.lstrip()[:3] == FENCE:
                    fenced = not fenced
        """,
    ) == [("prose", "a toggle")]


def test_a_toggle_on_something_else_is_not_a_fence(tmp_path: pathlib.Path) -> None:
    """Display maths and italics are toggled too, and are not this gate's business."""
    assert (
        _shapes(
            tmp_path,
            """
            def maths(lines):
                display = False
                for line in lines:
                    if line.strip() == "$$":
                        display = not display
            """,
        )
        == []
    )


def test_a_flag_flipped_with_xor_is_a_toggle(tmp_path: pathlib.Path) -> None:
    """``^= True`` and ``^ True`` flip a flag as ``not`` does."""
    assert _shapes(
        tmp_path,
        """
        def prose(lines):
            fenced = in_code = False
            for line in lines:
                fenced ^= True
                in_code = True ^ in_code
        """,
    ) == [("prose", "a toggle"), ("prose", "a toggle")]


def test_a_block_flag_is_a_fence_flag(tmp_path: pathlib.Path) -> None:
    """A flag named for the block it is inside says what it holds."""
    assert _shapes(
        tmp_path,
        """
        def prose(lines):
            in_block = False
            for line in lines:
                in_block = not in_block
        """,
    ) == [("prose", "a toggle")]


def test_the_even_odd_rule_is_not_a_fence(tmp_path: pathlib.Path) -> None:
    """The figure checks flip ``inside`` on every edge of an outline they cross."""
    assert (
        _shapes(
            tmp_path,
            """
            def filled(point, ring):
                inside = False
                for edge in ring:
                    if crosses(point, edge):
                        inside = not inside
                return inside
            """,
        )
        == []
    )


def test_the_overview_heading_reader_is_refused(tmp_path: pathlib.Path) -> None:
    """``scripts/mirror_overviews.py`` closed a fence on three of anything."""
    assert _shapes(
        tmp_path,
        """
        def _unfenced_lines(text):
            for line in text.splitlines():
                stripped = line.strip()
                if stripped[:3] in ("```", "~~~"):
                    pass
        """,
    ) == [("_unfenced_lines", "a test for a marker")]


def test_a_startswith_on_a_marker_is_refused(tmp_path: pathlib.Path) -> None:
    """The plainest test for an opening line, with the marker behind a name."""
    assert _shapes(
        tmp_path,
        """
        TICKS = "```"

        def opens(line):
            return line.startswith((TICKS, "~~~"))
        """,
    ) == [("opens", "a test for a marker")]


def test_an_endswith_on_a_marker_is_refused(tmp_path: pathlib.Path) -> None:
    """A closing line tested from its end is the same reading."""
    assert _shapes(
        tmp_path,
        """
        def closes(line):
            return line.rstrip().endswith("```")
        """,
    ) == [("closes", "a test for a marker")]


def test_a_marker_after_blanks_is_still_a_marker(tmp_path: pathlib.Path) -> None:
    """An indented marker opens a fence too."""
    assert _shapes(
        tmp_path,
        """
        def opens(stripped):
            return stripped == "   ```"
        """,
    ) == [("opens", "a test for a marker")]


def test_a_marker_built_by_repetition_is_refused(tmp_path: pathlib.Path) -> None:
    """Three backticks written as one backtick three times."""
    assert _shapes(
        tmp_path,
        """
        def opens(line):
            return line.lstrip().startswith("`" * 3)
        """,
    ) == [("opens", "a test for a marker")]


def test_a_marker_bound_inside_the_function_is_refused(tmp_path: pathlib.Path) -> None:
    """A local name hides the marker no better than a module constant."""
    assert _shapes(
        tmp_path,
        """
        def opens(line):
            marker = "```"
            return line.startswith(marker)
        """,
    ) == [("opens", "a test for a marker")]


def test_a_loop_over_the_markers_is_refused(tmp_path: pathlib.Path) -> None:
    """Each item of a tuple of markers is a marker."""
    assert _shapes(
        tmp_path,
        """
        MARKERS = ("```", "~~~")

        def opens(line):
            return any(line.startswith(marker) for marker in MARKERS)
        """,
    ) == [("opens", "a test for a marker")]


def test_a_count_of_markers_is_refused(tmp_path: pathlib.Path) -> None:
    """Whether a page is inside a fence by the parity of the markers above it."""
    assert _shapes(
        tmp_path,
        """
        def fenced(text):
            return text.count("```") % 2 == 1
        """,
    ) == [("fenced", "a test for a marker")]


def test_a_parameter_shadows_a_module_marker(tmp_path: pathlib.Path) -> None:
    """A name the function takes stands for whatever the caller passes."""
    assert (
        _shapes(
            tmp_path,
            """
            marker = "```"

            def opens(line, marker):
                return line.startswith(marker)
            """,
        )
        == []
    )


def test_the_regular_expressions_that_read_fences_are_refused(
    tmp_path: pathlib.Path,
) -> None:
    """The blanking of the digit check and the two extractors of Python examples."""
    assert _shapes(
        tmp_path,
        r"""
        import re
        from re import findall

        _FENCE = re.compile(r"^[ \t]*(```|~~~).*?^[ \t]*\1[ \t]*$", re.MULTILINE)
        _BLOCK = re.compile(pattern=r"```python\n(.*?)```")

        def blocks(text):
            return findall(r"^`{3,}python\n(.*?)^`{3,}", text)
        """,
    ) == [
        ("<module>", "a pattern for a marker"),
        ("<module>", "a pattern for a marker"),
        ("blocks", "a pattern for a marker"),
    ]


def test_a_pattern_behind_a_module_constant_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """Naming the pattern first does not hide what it looks for."""
    assert _shapes(
        tmp_path,
        r"""
        import re

        _OPENING = r"^\s*(~~~|```)"

        def opens(line):
            return re.match(_OPENING, line)
        """,
    ) == [("opens", "a pattern for a marker")]


def test_a_class_of_both_markers_is_refused(tmp_path: pathlib.Path) -> None:
    """The usual CommonMark pattern repeats a class of the two characters."""
    assert (
        _shapes(
            tmp_path,
            r"""
        import re

        FENCE = re.compile(r"^ {0,3}([`~]{3,})(.*)$")
        OPENING = re.compile(r"^\s*(?:`|~){3}")
        ESCAPED = re.compile(r"^\s*\`\`\`")
        """,
        )
        == [("<module>", "a pattern for a marker")] * 3
    )


def test_a_marker_spliced_into_an_f_string_pattern_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """A name bound to a marker counts wherever it is interpolated."""
    assert (
        _shapes(
            tmp_path,
            r"""
        import re

        TICKS = "```"

        def opens(line):
            return re.match(rf"^\s*{TICKS}", line) or re.match("^" + TICKS, line)
        """,
        )
        == [("opens", "a pattern for a marker")] * 2
    )


def test_a_script_that_writes_a_fence_is_not_reading_one(
    tmp_path: pathlib.Path,
) -> None:
    """The API reference and the llms generators put markers in their output."""
    assert (
        _shapes(
            tmp_path,
            """
            def signature(text, language):
                return ["```python", text, "```", f"~~~{language}", ""]
            """,
        )
        == []
    )


def test_a_marker_spliced_into_a_larger_pattern_is_not_a_fence_reader(
    tmp_path: pathlib.Path,
) -> None:
    """A wrapped line that would open a block is a hazard check, not a reader."""
    assert (
        _shapes(
            tmp_path,
            """
            import re

            _BLOCK_MARKER = r"[-*+]\\s|>|```|~~~"
            _WRAP = re.compile(rf"^\\s*(?:{_BLOCK_MARKER})")
            """,
        )
        == []
    )


def test_the_site_readers_are_refused(tmp_path: pathlib.Path) -> None:
    """The four places the site's code read fences for itself, as they were."""
    assert _shapes(
        tmp_path,
        r"""
        // A comment may say ``` freely.
        if (/^\s*(```|~~~)/.test(line)) inFence = !inFence;
        const source = text.replace(/^```[\s\S]*?^```/gm, "");
        const proseBody = rawBody.replace(/```[\s\S]*?```/g, ' ');
        const block = source.match(/```bibtex\n([\s\S]*?)```/);
        const ticks = '`'.repeat(3);
        """,
        name="reader.mjs",
    ) == [
        ("<script>", "a toggle"),
        ("<script>", "a marker in a script"),
        ("<script>", "a marker in a script"),
        ("<script>", "a marker in a script"),
        ("<script>", "a marker in a script"),
    ]


def test_the_site_code_is_read_and_its_build_is_not(tmp_path: pathlib.Path) -> None:
    """Installed packages and the built site are not the site's own code."""
    for part in ("src/lib", "node_modules/pkg", "dist", ".astro"):
        (tmp_path / part).mkdir(parents=True)
        (tmp_path / part / "a.mjs").write_text("x;\n", encoding="utf-8")
    (tmp_path / "src" / "Head.astro").write_text("x;\n", encoding="utf-8")
    read = [p.relative_to(tmp_path).as_posix() for p in cfr.files([str(tmp_path)])]
    assert read == ["src/Head.astro", "src/lib/a.mjs"]


def test_the_shared_readers_and_the_gate_are_not_read(tmp_path: pathlib.Path) -> None:
    """The owners of the reading have to spell the markers out, and so does the gate."""
    owners = [
        cfr.SCRIPTS / "markdown_fences.py",
        cfr.SITE / "src" / "lib" / "markdown-fences.mjs",
        pathlib.Path(cfr.__file__),
    ]
    found, stale, read = cfr.check(owners, {})
    assert (found, stale, read) == ([], [], 0)


def test_an_exemption_silences_one_function_and_goes_stale(
    tmp_path: pathlib.Path,
) -> None:
    """The hatch, keyed by file and function, reports itself once it covers nothing."""
    path = tmp_path / "reader.py"
    path.write_text("def opens(line):\n    return line.startswith('```')\n")
    key = (cfr.relative(path), "opens")
    found, stale, read = cfr.check([path], {key: "why it stays"})
    assert (found, stale, read) == ([], [], 1)
    path.write_text("def opens(line):\n    return bool(line)\n")
    found, stale, _ = cfr.check([path], {key: "why it stays"})
    assert (found, stale) == ([], [key])


def test_the_scripts_read_every_fence_through_the_shared_reader() -> None:
    """The tree itself, the Python scripts and the site's code."""
    assert cfr.main([]) == 0
