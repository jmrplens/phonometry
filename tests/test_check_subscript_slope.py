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
from typing import TYPE_CHECKING

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_subscript_slope as css

if TYPE_CHECKING:
    import pytest


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


def test_a_figure_beside_the_plates_is_not_read_as_one(tmp_path: pathlib.Path) -> None:
    """matplotlib writes an XML declaration first; a plate never does."""
    images = tmp_path / "images"
    images.mkdir()
    (images / "levels.svg").write_text(
        '<?xml version="1.0"?><svg><!-- $L_i$ --><g transform="translate(1 2) '
        'scale(0.1 -0.1)"><use href="#DejaVuSans-Oblique-2f"/></g></svg>',
        encoding="utf-8",
    )
    page = _write(tmp_path, "levels.md", "$L_\\mathrm{i}$\n" + _EMBED.format("levels"))
    _, failures = css.check([page], images)
    assert failures == []


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


def test_the_tree_it_ships_with_passes() -> None:
    """The gate is green on this repository, which is what CI asserts."""
    root = pathlib.Path(__file__).resolve().parent.parent
    paths = css.collect([str(root / r) for r in css.DEFAULT_ROOTS])
    _, failures = css.check(paths, root / css.PLATES)
    assert failures == []
