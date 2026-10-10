#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""The subscript-slope gate, held against the shapes this corpus writes.

``scripts/check_subscript_slope.py`` reads mathematics as it is typed rather
than as it renders, and the two ways of writing an upright subscript are the
whole difficulty: the command may wrap the whole comma-separated run
(``L_\mathrm{n,w,eq}``) or one component of it (``\alpha_{\mathrm{s},i}``).
A first version read the wrapped run component by component, decided that its
``w`` was italic, and reported four pages that were correctly set. These tests
fix both readings, the silence between files that the file scope depends on,
and the exclusions the gate claims.
"""

from __future__ import annotations

import pathlib
import sys

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_subscript_slope as css
import pytest

# The figure, diagram and badge tooling is tied to the pinned figure stack its
# artefacts are drawn with, so the minimum-versions job deselects this module.
pytestmark = pytest.mark.pinned_stack


def _write(tmp_path: pathlib.Path, name: str, text: str) -> pathlib.Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_one_symbol_two_slopes_in_one_file_fails(tmp_path: pathlib.Path) -> None:
    """The defect the gate exists for, with both lines named."""
    path = _write(
        tmp_path,
        "guide.md",
        "Positions average as $\\sum_i 10^{L_i/10}$.\n"
        "\n"
        "The impact level $L_\\mathrm{i}$ is normalised.\n",
    )
    read, failures = css.check([path])
    assert read == 1
    assert len(failures) == 1
    assert "L_i" in failures[0]
    assert "italic on line 1" in failures[0]
    assert "upright on line 3" in failures[0]


def test_two_files_may_disagree(tmp_path: pathlib.Path) -> None:
    """The silence the file scope depends on: D_z is both, one per module."""
    outdoor = _write(tmp_path, "outdoor.md", "Screening $D_z$ from the path.\n")
    shock = _write(tmp_path, "shock.md", "Dose $D_\\mathrm{z}$ up the spine.\n")
    _, failures = css.check([outdoor, shock])
    assert failures == []


def test_component_of_a_compound_subscript_is_read(tmp_path: pathlib.Path) -> None:
    """Half of one formula upright and half italic is the same defect."""
    path = _write(
        tmp_path,
        "theory.md",
        "$$\nA = \\sum_i \\alpha_{\\mathrm{s},i} S_i + \\sum_k \\alpha_{s,k} S_k\n$$\n",
    )
    _, failures = css.check([path])
    assert len(failures) == 1
    assert "\\alpha_s" in failures[0]


def test_a_run_inside_one_wrapper_is_upright_throughout(tmp_path: pathlib.Path) -> None:
    r"""``L_\mathrm{n,w,eq}`` sets three upright components, not one."""
    path = _write(
        tmp_path,
        "impact.md",
        "$L'_\\mathrm{n,w} = L_\\mathrm{n,w,eq} - \\Delta L_\\mathrm{w} + K$\n",
    )
    _, failures = css.check([path])
    assert failures == []


def test_an_index_beside_an_upright_run_is_not_a_collision(
    tmp_path: pathlib.Path,
) -> None:
    """The index keeps its own slope where the wrapper does not cover it."""
    path = _write(
        tmp_path,
        "flanking.md",
        "$D_{\\mathrm{v},ij}$ and $K_{ij}$ over junction $ij$.\n",
    )
    _, failures = css.check([path])
    assert failures == []


def test_a_wrapped_run_after_an_index_is_upright_throughout(
    tmp_path: pathlib.Path,
) -> None:
    r"""``D_{I,\mathrm{n,e}}`` sets the n and the e upright beside an italic I.

    Split on every comma, the wrapped run came apart into ``\mathrm{n`` and
    ``e}``: the n went unread and the e was taken for an italic letter, so the
    page that writes ``D_\mathrm{n,e}`` beside it failed with a collision it
    does not have.
    """
    path = _write(
        tmp_path,
        "intensity.md",
        "$D_{I,\\mathrm{n,e}}$ is the counterpart of $D_\\mathrm{n,e}$.\n",
    )
    found = css.sightings(path.read_text(encoding="utf-8"), ".md")
    assert dict(found[("D", "I")]) == {"italic": [1]}
    assert dict(found[("D", "e")]) == {"upright": [1, 1]}
    assert dict(found[("D", "n")]) == {"upright": [1, 1]}
    _, failures = css.check([path])
    assert failures == []


def test_a_translation_pattern_is_not_a_label(tmp_path: pathlib.Path) -> None:
    """A regex spells a backslash twice; nothing in it is mathematics."""
    path = _write(
        tmp_path,
        "i18n.py",
        "PATTERNS = [\n"
        '    (r"^\\$f_\\\\mathrm\\{c\\}\\$ = (\\d+) Hz$",'
        ' r"$f_c$ = \\1 Hz"),\n'
        "]\n",
    )
    _, failures = css.check([path])
    assert failures == []


def test_docstring_mathematics_is_read(tmp_path: pathlib.Path) -> None:
    """A module states its formulae in ``:math:`` roles and ``.. math::``."""
    path = _write(
        tmp_path,
        "module.py",
        'r"""Impact insulation.\n'
        "\n"
        "The average is :math:`\\sum_i 10^{L_i/10}`.\n"
        "\n"
        ".. math::\n"
        "   L'_\\mathrm{n} = L_\\mathrm{i} + 10 \\log_{10}(A/A_0)\n"
        "\n"
        '"""\n',
    )
    _, failures = css.check([path])
    assert len(failures) == 1
    assert "L_i" in failures[0]


def test_a_declared_page_is_left_alone(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The escape hatch, matched on the repository-relative tail of the path."""
    (tmp_path / "reference").mkdir()
    path = _write(
        tmp_path,
        "reference/glossary.md",
        "$L_N$ is a percentile; $L_\\mathrm{N}$ is sonar noise.\n",
    )
    assert css.check([path])[1], "undeclared, this page is a failure"
    monkeypatch.setitem(
        css.DECLARED,
        "reference/glossary.md",
        {("L", "N"): "the ambiguity table's own subject"},
    )
    _, failures = css.check([path])
    assert failures == []


def test_the_excluded_trees_are_not_collected(tmp_path: pathlib.Path) -> None:
    """Errata transcribe a source; drawing modules are filed by domain."""
    (tmp_path / "reference").mkdir()
    (tmp_path / "_plot").mkdir()
    for rel in ("reference/errata.md", "_plot/building.py", "guide.md"):
        _write(tmp_path, rel, "$L_i$ and $L_\\mathrm{i}$\n")
    collected = {p.name for p in css.collect([str(tmp_path)])}
    assert collected == {"guide.md"}


def _plate(
    directory: pathlib.Path,
    name: str,
    label: str,
    *,
    lang: str = "en",
    upright: tuple[str, ...] = (),
) -> pathlib.Path:
    """Draw *label* on a plate the way the generator does and write it."""
    from diagrams.canvas import LIGHT, SVG
    from generated_assets import compact_svg

    svg = SVG(900, 200, LIGHT, lang)
    svg.text(450, 100, label, 16, upright=upright)
    path = directory / f"{name}.svg"
    path.write_text(compact_svg(svg.render("A plate")), encoding="utf-8")
    return path


_EMBED = "![x](https://raw.githubusercontent.com/o/r/main/.github/images/{}.svg)\n"


def test_a_plate_sloped_against_its_page_fails(tmp_path: pathlib.Path) -> None:
    r"""The defect the plate reading exists for: L_i sloped beside L_\mathrm{i}."""
    images = tmp_path / "images"
    images.mkdir()
    _plate(images, "diagram_impact", "$L_i$ = energy-averaged")
    page = _write(
        tmp_path,
        "field.md",
        "The impact level $L_\\mathrm{i}$.\n" + _EMBED.format("diagram_impact"),
    )
    _, failures = css.check([page], images)
    assert len(failures) == 1
    assert "L_i: italic in diagram_impact.svg" in failures[0]
    assert "upright on line 1" in failures[0]


def test_a_plate_keyed_upright_agrees_with_its_page(tmp_path: pathlib.Path) -> None:
    """The per-call key the plates set the descriptive subscript with."""
    images = tmp_path / "images"
    images.mkdir()
    _plate(images, "diagram_impact", "$L_i$ = energy-averaged", upright=("L_i",))
    page = _write(
        tmp_path,
        "field.md",
        "The impact level $L_\\mathrm{i}$.\n" + _EMBED.format("diagram_impact"),
    )
    _, failures = css.check([page], images)
    assert failures == []


def test_a_plate_is_one_scope_with_every_page_that_embeds_it(
    tmp_path: pathlib.Path,
) -> None:
    """Two pages embedding one plate are each held against it."""
    images = tmp_path / "images"
    images.mkdir()
    _plate(images, "diagram_scan", "$I_n$ (normal intensity)", upright=("I_n",))
    upright = _write(
        tmp_path, "theory.md", "$I_\\mathrm{n}$\n" + _EMBED.format("diagram_scan")
    )
    sloped = _write(tmp_path, "guide.md", "$I_n$\n" + _EMBED.format("diagram_scan"))
    _, failures = css.check([upright, sloped], images)
    assert len(failures) == 1
    assert "guide.md" in failures[0]


def test_a_greek_letter_is_one_symbol_whichever_shape_the_page_writes(
    tmp_path: pathlib.Path,
) -> None:
    r"""A plate draws one epsilon; ``\varepsilon`` and ``\epsilon`` name it."""
    images = tmp_path / "images"
    images.mkdir()
    _plate(images, "diagram_spectra", "random error $ε_r$")
    page = _write(
        tmp_path,
        "spectra.md",
        "$\\varepsilon_\\mathrm{r}$\n" + _EMBED.format("diagram_spectra"),
    )
    _, failures = css.check([page], images)
    assert len(failures) == 1
    assert "\\epsilon_r" in failures[0]


def test_a_spanish_page_is_held_against_the_spanish_plate(
    tmp_path: pathlib.Path,
) -> None:
    """The site shows ``_es`` on a Spanish page, so that is the file read."""
    images = tmp_path / "images"
    images.mkdir()
    _plate(images, "diagram_impact", "$L_i$", upright=("L_i",))
    _plate(images, "diagram_impact_es", "$L_i$", lang="es")
    (tmp_path / "es").mkdir()
    page = _write(
        tmp_path, "es/campo.md", "$L_\\mathrm{i}$\n" + _EMBED.format("diagram_impact")
    )
    _, failures = css.check([page], images)
    assert len(failures) == 1
    assert "diagram_impact_es.svg" in failures[0]


def _figure(directory: pathlib.Path, name: str, *labels: str) -> pathlib.Path:
    """A matplotlib SVG as the figures write it: each text's source in a comment."""
    comments = "".join(f"<!-- {label} -->\n" for label in labels)
    path = directory / f"{name}.svg"
    path.write_text(
        '<?xml version="1.0" encoding="utf-8" standalone="no"?>\n'
        f"<svg>{comments}</svg>",
        encoding="utf-8",
    )
    return path


def test_a_figure_is_read_from_the_source_matplotlib_keeps(
    tmp_path: pathlib.Path,
) -> None:
    """mathtext sets the slope the source writes, and the comment holds it."""
    images = tmp_path / "images"
    images.mkdir()
    _figure(images, "levels", "Impact level $L_i$ [dB]")
    page = _write(tmp_path, "levels.md", "$L_\\mathrm{i}$\n" + _EMBED.format("levels"))
    _, failures = css.check([page], images)
    assert len(failures) == 1
    assert 'L_i: italic in levels.svg: "Impact level $L_i$ [dB]"' in failures[0]
    assert "upright on line 1" in failures[0]


def test_a_figure_that_agrees_with_its_page_passes(tmp_path: pathlib.Path) -> None:
    """An escaped comment reads back as the source it was written from."""
    images = tmp_path / "images"
    images.mkdir()
    _figure(images, "levels", "$L_\\mathrm{i}$ &lt; 60 dB")
    page = _write(tmp_path, "levels.md", "$L_\\mathrm{i}$\n" + _EMBED.format("levels"))
    _, failures = css.check([page], images)
    assert failures == []


def test_a_spanish_page_is_held_against_the_spanish_figure(
    tmp_path: pathlib.Path,
) -> None:
    """The figures carry an ``_es`` twin too, and that is what the page shows."""
    images = tmp_path / "images"
    images.mkdir()
    _figure(images, "levels", "$L_\\mathrm{i}$")
    _figure(images, "levels_es", "$L_i$")
    (tmp_path / "es").mkdir()
    page = _write(
        tmp_path, "es/niveles.md", "$L_\\mathrm{i}$\n" + _EMBED.format("levels")
    )
    _, failures = css.check([page], images)
    assert len(failures) == 1
    assert "levels_es.svg" in failures[0]


def test_a_letter_run_is_one_base() -> None:
    """``TL_n`` is a transmission loss, not a level L carrying a subscript."""
    found = css.sightings("$TL_\\mathrm{n}$ and $L_n$ and $KB_\\mathrm{F}$", ".md")
    assert found[("TL", "n")] == {"upright": [1]}
    assert found[("L", "n")] == {"italic": [1]}
    assert found[("KB", "F")] == {"upright": [1]}
    assert ("B", "F") not in found


def test_a_plate_reads_a_letter_run_as_one_base() -> None:
    """The plate reading names the same symbol the page reading does."""
    from diagrams.canvas import LIGHT, SVG

    svg = SVG(900, 200, LIGHT)
    svg.text(450, 100, "$SNR_x$ and $L_x$", 16)
    found, unreadable = css.plate_sightings(svg.render("A plate"))
    assert unreadable == []
    assert set(found) == {("SNR", "x"), ("L", "x")}


def test_a_subscript_inside_an_exponent_is_read_on_a_plate() -> None:
    """The level inside an energy sum's exponent hangs from its own base."""
    from diagrams.canvas import LIGHT, SVG

    svg = SVG(900, 200, LIGHT)
    svg.text(450, 100, "$10 lg Σ 10^{L_i/10}$ and $L_{Aeq}$", 16)
    found, unreadable = css.plate_sightings(svg.render("A plate"))
    assert unreadable == []
    assert found[("L", "i")]["italic"] == ["$10 lg Σ 10^{L_i/10}$ and $L_{Aeq}$"]


def test_a_ligature_in_a_script_is_read_through() -> None:
    """DejaVu draws the ff of "eff" as one glyph; the script is still read."""
    from diagrams.canvas import LIGHT, SVG

    svg = SVG(900, 200, LIGHT)
    svg.text(450, 100, "$m_{eff}$ and $L_i$", 16)
    found, unreadable = css.plate_sightings(svg.render("A plate"))
    assert unreadable == []
    assert found[("L", "i")]["italic"] == ["$m_{eff}$ and $L_i$"]


def test_a_label_whose_glyphs_do_not_line_up_is_reported(
    tmp_path: pathlib.Path,
) -> None:
    """A plate the gate cannot read fails it rather than passing unread."""
    images = tmp_path / "images"
    images.mkdir()
    path = _plate(images, "diagram_impact", "$L_i$")
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace("<!-- $L_i$ -->", "<!-- $L_i^2$ -->"), encoding="utf-8"
    )
    page = _write(tmp_path, "field.md", _EMBED.format("diagram_impact"))
    _, failures = css.check([page], images)
    assert len(failures) == 1
    assert "cannot line up the glyphs of diagram_impact.svg" in failures[0]


def test_a_doubled_brace_in_a_formatted_label_is_upright(
    tmp_path: pathlib.Path,
) -> None:
    r"""``rf"$f_\mathrm{{e}}$ = {f:g} Hz"`` renders an upright e."""
    path = _write(
        tmp_path,
        "railway.md",
        'label=rf"$f_\\mathrm{{e}}$ = {natural:g} Hz"\n\nThe floor $f_e$.\n',
    )
    _, failures = css.check([path])
    assert len(failures) == 1
    assert "upright on line 1" in failures[0]


def test_a_linked_letter_set_two_ways_on_one_page_fails(tmp_path: pathlib.Path) -> None:
    r"""The r of KB_FTr and of A_r is one letter, though the symbols are two."""
    path = _write(
        tmp_path,
        "people.md",
        "$KB_\\mathrm{FTr}$ is held to $A_r$ over $T_\\mathrm{r}$.\n",
    )
    _, failures = css.check([path])
    assert len(failures) == 1
    assert "Beurteilung" in failures[0]
    assert "italic: A_r on line 1" in failures[0]
    assert "KB_FTr on line 1" in failures[0]


def test_a_linked_letter_set_one_way_passes(tmp_path: pathlib.Path) -> None:
    """Every member upright, as DIN 4150-2 prints them, is no collision."""
    path = _write(
        tmp_path,
        "people.md",
        "$KB_{\\mathrm{FTr}} = \\sqrt{\\frac{1}{N_\\mathrm{r}} \\sum_j M_j}$ "
        "against $A_\\mathrm{r}$.\n",
    )
    _, failures = css.check([path])
    assert failures == []


def test_a_plate_setting_the_linked_letter_two_ways_fails(
    tmp_path: pathlib.Path,
) -> None:
    """On a plate the roman FTr beside an unkeyed A_r is the same split."""
    images = tmp_path / "images"
    images.mkdir()
    _plate(images, "diagram_people", "$KB_{FTr}$ ≤ $A_r$ ?")
    page = _write(tmp_path, "people.md", _EMBED.format("diagram_people"))
    _, failures = css.check([page], images)
    assert len(failures) == 1
    assert 'italic: A_r in diagram_people.svg: "$KB_{FTr}$ ≤ $A_r$ ?"' in failures[0]


def test_a_plate_keying_the_linked_letter_upright_passes(
    tmp_path: pathlib.Path,
) -> None:
    """The ``upright`` key brings the A_r of the plate into line with its FTr."""
    images = tmp_path / "images"
    images.mkdir()
    _plate(images, "diagram_people", "$KB_{FTr}$ ≤ $A_r$ ?", upright=("A_r",))
    page = _write(tmp_path, "people.md", _EMBED.format("diagram_people"))
    _, failures = css.check([page], images)
    assert failures == []


def test_the_tree_it_ships_with_passes() -> None:
    """The gate is green on this repository, which is what CI asserts."""
    root = pathlib.Path(__file__).resolve().parent.parent
    paths = css.collect([str(root / r) for r in css.DEFAULT_ROOTS])
    _, failures = css.check(paths, root / css.PLATES)
    assert failures == []


def test_an_upright_vibration_severity_fails_on_a_page(tmp_path: pathlib.Path) -> None:
    r"""KB is italic everywhere, as DIN 4150-2 prints it, whatever the file."""
    path = _write(
        tmp_path,
        "meter.md",
        "The maximum $\\mathrm{KB}_\\mathrm{Fmax}$ and the r.m.s. $KB_\\mathrm{FTm}$.\n",
    )
    _, failures = css.check([path])
    assert len(failures) == 1
    assert "KB upright on line 1" in failures[0]
    assert "DIN 4150-2" in failures[0]


def test_an_italic_vibration_severity_passes_and_a_subscript_is_not_read(
    tmp_path: pathlib.Path,
) -> None:
    r"""The KB of :math:`L_{v,KB}` names a weighting, and is not a base."""
    path = _write(
        tmp_path,
        "prediction.md",
        "$KB_\\mathrm{F}(t)$, $L_{v,KB}$ and $H_{\\mathrm{KB}}(f)$.\n",
    )
    found = css.base_sightings(path.read_text(encoding="utf-8"), ".md")
    assert dict(found[("KB", "")]) == {"italic": [1]}
    _, failures = css.check([path])
    assert failures == []


def test_a_file_outside_the_file_scope_is_still_held_to_the_bases(
    tmp_path: pathlib.Path,
) -> None:
    """The errata register keeps its own subscripts but not an upright KB."""
    (tmp_path / "reference").mkdir()
    errata = _write(tmp_path, "reference/errata.md", "$\\text{KB}_\\mathrm{F}$\n")
    assert css.collect([str(tmp_path)]) == []
    assert css.collect([str(tmp_path)], everything=True) == [errata]
    _, failures = css.check([], bases_only=[errata])
    assert len(failures) == 1
    assert "KB upright on line 1" in failures[0]


def test_a_plate_drawing_an_upright_vibration_severity_fails(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A plate is read from its glyphs: KB from the regular face is upright."""
    from diagrams import canvas

    images = tmp_path / "images"
    images.mkdir()
    page = _write(tmp_path, "people.md", _EMBED.format("diagram_people"))
    _plate(images, "diagram_people", "$KB_{Fmax}$ ≤ $A_u$ ?", upright=("A_u",))
    _, failures = css.check([page], images)
    assert failures == []
    monkeypatch.setattr(canvas, "_ITALIC_BASE_RUNS", frozenset())
    css._IMAGE_CACHE.clear()
    _plate(images, "diagram_people", "$KB_{Fmax}$ ≤ $A_u$ ?", upright=("A_u",))
    _, failures = css.check([page], images)
    assert len(failures) == 1
    assert 'KB upright in "$KB_{Fmax}$ ≤ $A_u$ ?"' in failures[0]


def test_every_image_is_read_for_the_bases_embedded_or_not(
    tmp_path: pathlib.Path,
) -> None:
    """An image no page embeds still ships, so its KB is read too."""
    images = tmp_path / "images"
    images.mkdir()
    _figure(images, "people_guide_values", "Guide value, $\\mathrm{KB}$")
    _, failures = css.check([], images)
    assert failures == []
    _, failures = css.check([], images, every_image=True)
    assert len(failures) == 1
    assert "people_guide_values.svg" in failures[0]


def test_an_upright_vibration_severity_in_a_cases_block_fails(
    tmp_path: pathlib.Path,
) -> None:
    r"""A row break ``\\`` is TeX, so the block around it is read."""
    path = _write(
        tmp_path,
        "categories.md",
        "$$\nA = \\begin{cases} \\mathrm{KB}_\\mathrm{Fmax} & a \\\\\n"
        "  KB_\\mathrm{FTr} & b \\end{cases}\n$$\n",
    )
    found = css.base_sightings(path.read_text(encoding="utf-8"), ".md")
    assert dict(found[("KB", "")]) == {"upright": [1], "italic": [1]}
    _, failures = css.check([path])
    assert len(failures) == 1
    assert "KB upright" in failures[0]


def test_an_upright_vibration_severity_after_a_wrapped_formula_fails(
    tmp_path: pathlib.Path,
) -> None:
    """A formula that wraps a line does not hide the one after it."""
    path = _write(
        tmp_path,
        "meter.md",
        "The clock $T = 30\\,\n\\mathrm{s}$ gives $\\mathrm{KB}_\\mathrm{FTm}$.\n",
    )
    found = css.base_sightings(path.read_text(encoding="utf-8"), ".md")
    assert dict(found[("KB", "")]) == {"upright": [2]}


def test_a_subscript_in_a_cases_block_is_read(tmp_path: pathlib.Path) -> None:
    """The file scope covers every row of a block, as it covers a line."""
    path = _write(
        tmp_path,
        "weighting.md",
        "$L_\\mathrm{s}$ and\n\n$$\n\\begin{cases} L_s & a \\\\ 0 & b \\end{cases}\n$$\n",
    )
    _, failures = css.check([path])
    assert len(failures) == 1


def test_an_upright_running_index_fails_on_a_page(tmp_path: pathlib.Path) -> None:
    r"""UNE-EN 15657 prints the i of :math:`L_{v,i}` upright; the corpus does not."""
    path = _write(
        tmp_path,
        "structure-borne-power.md",
        "$L_\\mathrm{v} = 10 \\lg(\\sum 10^{L_\\mathrm{v,i}/10})$\n",
    )
    _, failures = css.check([path])
    assert len(failures) == 1
    assert "L_\\mathrm{v,i}: the index i is upright on line 1" in failures[0]
    assert "ISO 80000-2" in failures[0]


def test_italic_running_indices_beside_upright_abbreviations_pass(
    tmp_path: pathlib.Path,
) -> None:
    """The settled shapes: an upright abbreviation, then an italic index."""
    path = _write(
        tmp_path,
        "installed.md",
        "$L_{\\mathrm{v},i}$, $D_{\\mathrm{C},i}$, $L_{\\mathrm{n,s},ij}$, "
        "$L_{\\mathrm{Ws,inst},i}$ and $\\sum_{i=1}^{N} 10^{L_i/10}$.\n",
    )
    assert css.index_slips(path.read_text(encoding="utf-8"), ".md") == []
    _, failures = css.check([path])
    assert failures == []


def test_an_upright_sum_index_fails_and_a_named_sum_passes(
    tmp_path: pathlib.Path,
) -> None:
    r"""The letter a sum runs over is an index; ``\sum_\mathrm{Zug}`` is a word."""
    path = _write(
        tmp_path,
        "sums.md",
        "$\\sum_\\mathrm{j} a_j$, $\\sum_{\\mathrm{i}=1}^{N} b_i$ and "
        "$\\sum_\\mathrm{Zug} n_\\mathrm{Zug}$.\n",
    )
    slips = css.index_slips(path.read_text(encoding="utf-8"), ".md")
    assert sorted(index for _, index, _ in slips) == ["i", "j"]


def test_an_upright_letter_opening_a_subscript_is_not_read_as_an_index(
    tmp_path: pathlib.Path,
) -> None:
    """The impact level of ISO 16283-2 opens its subscript with an upright i."""
    path = _write(
        tmp_path,
        "heavy-impact.md",
        "$L_\\mathrm{i}$, $L_\\mathrm{i,Fmax}$ and $L_\\mathrm{i,Fmax,0}$.\n",
    )
    _, failures = css.check([path])
    assert failures == []


def test_the_errata_register_may_quote_an_upright_index(
    tmp_path: pathlib.Path,
) -> None:
    """A transcription keeps the print; a drawing module is held to the rule."""
    (tmp_path / "reference").mkdir()
    (tmp_path / "_plot").mkdir()
    errata = _write(tmp_path, "reference/errata.md", "$D_\\mathrm{C,i}$\n")
    plot = _write(tmp_path, "_plot/building.py", 'LABEL = r"$L_\\mathrm{v,i}$"\n')
    _, failures = css.check([], bases_only=[errata, plot])
    assert len(failures) == 1
    assert "building.py" in failures[0]
    assert "the index i is upright on line 1" in failures[0]


def test_a_plate_drawing_an_upright_running_index_fails(
    tmp_path: pathlib.Path,
) -> None:
    """The reception plate keyed the index of Formula (12) upright, twice."""
    images = tmp_path / "images"
    images.mkdir()
    label = "$L_v = 10 lg[(1/N)·Σ_i 10^{L_{v,i}/10}]$"
    _plate(images, "diagram_plate", label, upright=("L_v", "L_i", "Σ_i"))
    _, failures = css.check([], images, every_image=True)
    assert len(failures) == 2
    assert any("L_{v,i}: the index i is upright" in f for f in failures)
    assert any("\\Sigma_{i}: the index i is upright" in f for f in failures)
    css._IMAGE_CACHE.clear()
    _plate(images, "diagram_plate", label, upright=("L_v",))
    _, failures = css.check([], images, every_image=True)
    assert failures == []


def test_a_figure_setting_an_upright_running_index_fails(
    tmp_path: pathlib.Path,
) -> None:
    """A figure label is read from the source matplotlib keeps."""
    images = tmp_path / "images"
    images.mkdir()
    _figure(images, "plate_levels", "Position level $L_\\mathrm{v,i}$ [dB]")
    _, failures = css.check([], images, every_image=True)
    assert len(failures) == 1
    assert "plate_levels.svg" in failures[0]
    css._IMAGE_CACHE.clear()
    _figure(images, "plate_levels", "Position level $L_{\\mathrm{v},i}$ [dB]")
    _, failures = css.check([], images, every_image=True)
    assert failures == []
