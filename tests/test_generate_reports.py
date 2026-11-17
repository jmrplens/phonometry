#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The example-report generator keeps producing valid one-page fiches.

The rendered PDFs (and their WebP previews) under ``.github/reports/`` are not
byte-checked (their vector plot differs by ~1 ULP across CPUs, and the raster
inherits it); this test only guards that ``scripts/generate_reports.py`` still
runs and writes a valid single-page PDF plus a valid WebP preview for every
registered example. One test per registered example: each fiche is rendered
exactly once (PDF and preview asserted together on the same run) and the
examples spread across the xdist workers instead of forming one monolithic
test.
"""

from __future__ import annotations

import importlib.util
import itertools
import pathlib
import re
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType

    from reportlab.graphics.shapes import Drawing

pytest.importorskip("reportlab")
pytest.importorskip("svglib")
pytest.importorskip("pypdf")
pytest.importorskip("pypdfium2")
pytest.importorskip("PIL")

_SCRIPT = (
    pathlib.Path(__file__).resolve().parents[1] / "scripts" / "generate_reports.py"
)


def _load_generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("_generate_reports", _SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_MODULE = _load_generator()


def test_generator_registers_examples() -> None:
    assert _MODULE._EXAMPLES, "the generator registered no examples"
    # No factory is registered twice: a duplicate entry would render the
    # same fiche twice and hide a forgotten registration elsewhere. (The
    # filenames cannot collide, being the registry's own keys.)
    names = [factory.__name__ for factory in _MODULE._EXAMPLES]
    assert len(set(names)) == len(names)
    assert all(name.endswith(".pdf") for name in _MODULE._FICHES)


def test_every_registered_fiche_is_committed() -> None:
    """Registering a fiche and never committing it is a silent hole.

    One example was registered in the generator, documented, and left without
    its rendered PDF and preview in the tree for months: the documentation
    linked to files that were not there. The staleness job catches it too, but
    this needs no regeneration, so it fails in the same second as the commit
    that forgets it.

    Reads the filenames off the registry keys rather than calling each factory
    for the name it returns: the answer is a path lookup, and running all 67
    factories to get it would compute and plot every worked example first.
    ``test_each_example_writes_a_one_page_pdf_and_preview`` is what confirms a
    factory still writes the file it is registered under.
    """
    committed = pathlib.Path(_MODULE._DEFAULT_DIR)
    missing = [
        path.name
        for name in _MODULE._FICHES
        for path in (committed / name, committed / _MODULE.preview_path_for(name))
        if not path.is_file()
    ]
    assert not missing, (
        f"registered fiches with no committed render: {sorted(missing)} - "
        "run 'make reports' and commit the result"
    )


#: The plain ``opacity`` property in an SVG ``style``. matplotlib writes it for
#: an artist's alpha (``ax.axvspan(..., alpha=0.12)``, a bar, a patch), while a
#: colour that carries its own alpha comes out as ``fill-opacity`` or
#: ``stroke-opacity``.
_OPACITY = re.compile(r"(?:^|;)\s*opacity:\s*([0-9.eE+-]+)")


#: The id each legend's frame is drawn under while a fiche renders in
#: :func:`test_each_example_writes_a_one_page_pdf_and_preview`, numbered.
_LEGEND_FRAME = "legend-frame-"


def _mark_legend_frames(monkeypatch: pytest.MonkeyPatch) -> None:
    """Draw every legend's frame under an id that names it.

    matplotlib writes a legend's frame as a ``patch_N`` group like any other
    patch, and a legend without a frame (``frameon=False``) and without a title
    opens with the patch of its first entry instead: read by its place, a
    translucent proxy ``Patch`` would pass for the frame. The frame is the
    legend's ``legendPatch``; its ``gid`` becomes the group's id in the SVG.
    """
    try:
        import matplotlib.legend
    except ImportError:
        return
    init = matplotlib.legend.Legend.__init__
    numbers = itertools.count()

    def marking_init(
        self: matplotlib.legend.Legend, *args: object, **kwargs: object
    ) -> None:
        init(self, *args, **kwargs)  # type: ignore[arg-type]
        self.legendPatch.set_gid(f"{_LEGEND_FRAME}{next(numbers)}")

    monkeypatch.setattr(matplotlib.legend.Legend, "__init__", marking_init)


def _legend_frames(root: ET.Element) -> set[ET.Element]:
    """Every element of a legend's frame in an SVG drawn under :func:`_mark_legend_frames`."""
    frames: set[ET.Element] = set()
    for group in root.iter("{http://www.w3.org/2000/svg}g"):
        if group.get("id", "").startswith(_LEGEND_FRAME):
            frames.update(group.iter())
    return frames


def _translucent_shapes(svg: pathlib.Path) -> list[str]:
    """Styles of the shapes in ``svg`` drawn at an ``opacity`` below 1.

    The fiche renders its plot through svglib, and every svglib the report
    extra admits below 2.4 ignores ``opacity``, so a shape drawn with it comes
    out opaque in the PDF: the IEC 61400-11 tonality fiche showed a solid green
    block over the whole spectrum where the plot asked for a pale critical
    band. ``fill-opacity`` and ``stroke-opacity``, which every admitted svglib
    reads, are left alone, and so is a legend's frame: drawn opaque, it is the
    box ``framealpha=1`` draws, over the legend's own area.
    """
    root = ET.parse(svg).getroot()
    frames = _legend_frames(root)
    found = []
    for element in root.iter():
        if element in frames:
            continue
        style = element.get("style") or ""
        match = _OPACITY.search(style)
        value = match.group(1) if match else element.get("opacity")
        if value is not None and float(value) < 1.0:
            found.append(style or f"opacity={value}")
    return found


def _skip_where_the_figure_needs_matplotlib(error: ImportError) -> None:
    """Skip a fiche whose figure cannot be drawn because matplotlib is missing.

    A fiche with a figure stops on matplotlib's ``ModuleNotFoundError``, or on
    the library's install hint raised from it; a fiche without one, as the ISO
    4871 declaration, renders with the ``report`` extra alone and runs. Any
    other ``ImportError`` is left to fail.
    """
    for raised in (error, error.__cause__):
        if isinstance(raised, ImportError) and raised.name == "matplotlib":
            pytest.skip(str(error))


@pytest.mark.parametrize("frameon", [True, False])
def test_a_translucent_legend_entry_is_found_with_or_without_a_frame(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, *, frameon: bool
) -> None:
    """Only the frame a legend draws is let through, never an entry in its place.

    A legend without a frame and without a title opens with the patch of its
    first entry, where the frame would stand; a translucent proxy there is a
    shape svglib before 2.4 draws opaque like any other.
    """
    pytest.importorskip("matplotlib")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    _mark_legend_frames(monkeypatch)
    figure, axes = plt.subplots()
    try:
        axes.plot([0.0, 1.0])
        axes.legend(
            handles=[Patch(color="green", alpha=0.12, label="band")],
            frameon=frameon,
            framealpha=0.8,
        )
        path = tmp_path / "legend.svg"
        figure.savefig(path, format="svg")
    finally:
        plt.close(figure)
    assert [style for style in _translucent_shapes(path) if "0.12" in style]
    assert not [style for style in _translucent_shapes(path) if "0.8" in style]


@pytest.mark.parametrize(
    "factory", _MODULE._EXAMPLES, ids=lambda factory: factory.__name__.strip("_")
)
def test_each_example_writes_a_one_page_pdf_and_preview(
    factory: Callable[..., object],
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import svglib.svglib
    from PIL import Image
    from pypdf import PdfReader

    # Read each plot's SVG on its way into svglib, so the fiche is checked for
    # translucent shapes in the same render (see _translucent_shapes).
    translucent: list[str] = []
    convert = svglib.svglib.svg2rlg
    _mark_legend_frames(monkeypatch)

    def reading_svg2rlg(path: pathlib.Path) -> Drawing | None:
        translucent.extend(_translucent_shapes(path))
        return convert(path)

    monkeypatch.setattr(svglib.svglib, "svg2rlg", reading_svg2rlg)
    try:
        written = _MODULE.generate_reports(str(tmp_path), examples=[factory])
    except ImportError as error:
        _skip_where_the_figure_needs_matplotlib(error)
        raise
    assert not translucent, (
        "the fiche plot draws a shape through matplotlib's artist alpha, which "
        "svglib before 2.4 draws opaque: shade it with theme_fill (or a colour "
        f"with its own alpha) instead. Shapes: {translucent}"
    )
    assert len(written) == 1
    p = pathlib.Path(written[0])
    # The factory writes the file it is registered under. This is what lets
    # test_every_registered_fiche_is_committed trust the registry keys.
    assert _MODULE._FICHES.get(p.name) is factory
    assert p.is_file()
    assert p.stat().st_size > 0
    with p.open("rb") as handle:
        assert handle.read(4) == b"%PDF"
    assert len(PdfReader(str(p)).pages) == 1
    preview = pathlib.Path(_MODULE.preview_path_for(str(p)))
    assert preview.suffix == ".webp"
    assert preview.is_file()
    assert preview.stat().st_size > 0
    with Image.open(preview) as image:
        assert image.format == "WEBP"
        assert image.width == _MODULE._PREVIEW_WIDTH_PX
