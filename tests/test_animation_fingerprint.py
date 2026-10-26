#  Copyright (c) 2026. Jose Manuel Requena Plens
"""What the clip fingerprint has to notice, and what it has to ignore.

The clips are the one committed asset CI never regenerates, so the only thing
standing between "the code that draws this clip changed" and a clip that
quietly keeps its old frames is the fingerprint
(``scripts/animation_fingerprint.py``) and the check that compares it. These
tests pin both halves of that bargain, because either one failing makes the
gate worthless: a fingerprint that misses a real change lets the staleness
through, and a fingerprint that moves on a reflowed comment costs a
several-minute re-render for nothing and is switched off within a week.

The tree used here is a miniature of the real package written into a tmp
directory: the registry with its ``_ANIMATIONS`` map, a clip module, the
shared clip tail, the theme and the two translation tables. Building it from
source text rather than from the repo is what lets a test change one line and
ask what the fingerprint did about it.
"""

from __future__ import annotations

import ast
import json
import pathlib
import sys
from typing import TYPE_CHECKING, Self

import pytest

if TYPE_CHECKING:
    from types import ModuleType

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import animation_fingerprint as fp

# The figure, diagram and badge tooling is tied to the pinned figure stack its
# artefacts are drawn with, so the minimum-versions job deselects this module.
pytestmark = pytest.mark.pinned_stack

REGISTRY = """
from .schematics import animate_one, animate_two

_ANIMATIONS = {
    "anim_one": animate_one,
    "anim_two": animate_two,
}
"""

SCHEMATICS = '''
from .media import _render_clip, _translate_str
from .theme import COLOR_PRIMARY


def _shared_label(ax):
    """A helper both clips call."""
    ax.text(0.0, 0.0, _translate_str("shared caption"), color=COLOR_PRIMARY)


def animate_one(output_dir):
    """The first clip."""
    _shared_label(None)
    _translate_str("only in clip one")
    _translate_str(f"level {1.0:.1f} dB")
    _render_clip(None, None, output_dir, "anim_one")


def animate_two(output_dir):
    """The second clip, which shares nothing but the tail."""
    _translate_str("only in clip two")
    _render_clip(None, None, output_dir, "anim_two")
'''

MEDIA = """
from .i18n import _translate_figure

_ANIM_FPS = 20


def _translate_str(s):
    return s


def _render_clip(fig, update, output_dir, stem):
    _translate_figure(fig)
    return _ANIM_FPS
"""

THEME = '''
COLOR_PRIMARY = "#1f77b4"


def set_theme(dark):
    """The palette every frame is drawn with."""
    return COLOR_PRIMARY if dark else COLOR_PRIMARY
'''

I18N = """
_ES_EXACT = {
    "shared caption": "rótulo compartido",
    "only in clip one": "solo en el clip uno",
    "only in clip two": "solo en el clip dos",
    "some other figure": "otra figura cualquiera",
}

_ES_PATTERNS = [
    (r"^level (\\d+)\\.(\\d+) dB$", r"nivel \\1,\\2 dB"),
    (r"^unrelated (\\d+) thing$", r"cosa \\1 no relacionada"),
]


def _translate_figure(fig):
    return fig
"""


def _write_tree(root: pathlib.Path) -> pathlib.Path:
    """Write a miniature figures package under *root*, complete enough to fingerprint."""
    package = root / "scripts" / "figures"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    for name, body in (
        ("registry", REGISTRY),
        ("schematics", SCHEMATICS),
        ("media", MEDIA),
        ("theme", THEME),
        ("i18n", I18N),
    ):
        (package / f"{name}.py").write_text(body, encoding="utf-8")
    return root


@pytest.fixture
def tree(tmp_path: pathlib.Path) -> pathlib.Path:
    """A miniature figures package, complete enough to fingerprint."""
    return _write_tree(tmp_path)


def edit(tree: pathlib.Path, module: str, old: str, new: str) -> None:
    """Rewrite one fragment of a module of the miniature tree."""
    path = tree / "scripts" / "figures" / f"{module}.py"
    text = path.read_text(encoding="utf-8")
    assert text.count(old) == 1, old
    path.write_text(text.replace(old, new), encoding="utf-8")


def test_every_registered_clip_is_fingerprinted(tree: pathlib.Path) -> None:
    assert sorted(fp.fingerprints(tree)) == ["anim_one", "anim_two"]


def test_the_same_sources_give_the_same_fingerprint(tmp_path: pathlib.Path) -> None:
    """The same sources hash the same, read again and read from elsewhere.

    The stamp is written from a working copy and recomputed in CI out of a
    checkout at another absolute path, so a fingerprint carrying anything of
    where the files sit -- a path in the hash, an order the filesystem
    happened to hand back -- would mark all forty-two clips stale on every
    run and be switched off by the end of the week. ``tmp_path`` is a single
    directory, so the two absolute paths the property needs are two
    subdirectories of it rather than two pytest-managed roots: they are
    still distinct absolute paths on disk, which is all the property cares
    about.
    """
    import shutil

    here = _write_tree(tmp_path / "a")
    elsewhere = tmp_path / "b" / "checkout"
    shutil.copytree(here, elsewhere)

    first = fp.fingerprints(here)
    again = fp.fingerprints(here)
    copied = fp.fingerprints(elsewhere)

    assert again == first
    assert copied == first


@pytest.mark.parametrize(
    ("module", "old", "new", "moves"),
    [
        # The clip's own body: the whole point.
        ("schematics", '"only in clip one"', '"clip one, reworded"', {"anim_one"}),
        # A helper it calls, in its own module.
        ("schematics", "ax.text(0.0, 0.0", "ax.text(0.5, 0.0", {"anim_one"}),
        # The shared clip tail: both clips are drawn through it.
        ("media", "_ANIM_FPS = 20", "_ANIM_FPS = 25", {"anim_one", "anim_two"}),
        # The theme, which nothing in a clip calls and every frame carries.
        ("theme", '"#1f77b4"', '"#d62728"', {"anim_one", "anim_two"}),
        # The translation machinery (this is the shape of the Spanish
        # minus-sign repair that started all this).
        (
            "i18n",
            "def _translate_figure(fig):\n    return fig",
            "def _translate_figure(fig):\n    return str(fig)",
            {"anim_one", "anim_two"},
        ),
        # A translation the clip's own text selects, exact and by pattern.
        ("i18n", '"solo en el clip uno"', '"solo en el primer clip"', {"anim_one"}),
        ("i18n", '"rótulo compartido"', '"el rótulo compartido"', {"anim_one"}),
        ("i18n", r'r"nivel \1,\2 dB"', r'r"nivel de \1,\2 dB"', {"anim_one"}),
        # An import kept for what importing it does.
        (
            "media",
            "from .i18n import _translate_figure",
            "import mpl_toolkits.mplot3d\n\nfrom .i18n import _translate_figure",
            {"anim_one", "anim_two"},
        ),
        # Flattening the star must not flatten the defaults with it: a
        # parameter that gains one, loses one or changes it is a different
        # frame, and the canonical argument list keeps each default beside
        # the parameter it belongs to.
        (
            "theme",
            "def set_theme(dark):",
            "def set_theme(dark=True):",
            {"anim_one", "anim_two"},
        ),
    ],
)
def test_a_change_that_reaches_a_clip_moves_its_fingerprint(
    tree: pathlib.Path, module: str, old: str, new: str, moves: set[str]
) -> None:
    before = fp.fingerprints(tree)
    edit(tree, module, old, new)
    after = fp.fingerprints(tree)
    moved = {clip for clip in before if before[clip] != after[clip]}
    assert moved == moves


def test_a_helper_a_clip_imports_inside_its_function_is_followed(
    tree: pathlib.Path,
) -> None:
    """``from .theme import helper`` inside the clip's function reaches the helper as one at the top does."""
    edit(
        tree,
        "theme",
        'COLOR_PRIMARY = "#1f77b4"',
        'COLOR_PRIMARY = "#1f77b4"\n\n\ndef series_colors():\n    return ["#1f77b4"]',
    )
    edit(
        tree,
        "schematics",
        '    _translate_str("only in clip two")',
        "    from .theme import series_colors\n\n"
        '    _translate_str("only in clip two")\n    series_colors()',
    )
    before = fp.fingerprints(tree)
    edit(tree, "theme", 'return ["#1f77b4"]', 'return ["#d62728"]')
    after = fp.fingerprints(tree)
    assert {clip for clip in before if before[clip] != after[clip]} == {"anim_two"}


@pytest.mark.parametrize(
    ("module", "old", "new"),
    [
        # Comments and docstrings: the fingerprint is taken over the syntax
        # tree, so prose cannot cost a re-render.
        (
            "schematics",
            '"""The first clip."""',
            '"""The first clip, rewritten\n\n    with a longer explanation.\n    """',
        ),
        ("schematics", '"""A helper both clips call."""', "'''A helper.'''"),
        (
            "theme",
            '"""The palette every frame is drawn with."""',
            '"""The palette."""  # and a trailing comment',
        ),
        # A translation entry no clip of this tree writes, which is what the
        # per-clip selection of the tables buys: an unrelated figure gaining
        # or changing a Spanish string must not mark every clip stale.
        ("i18n", '"otra figura cualquiera"', '"una figura distinta"'),
        ("i18n", r'r"cosa \1 no relacionada"', r'r"otra cosa \1"'),
        # Annotations, in every position they take: a type checker reads them
        # and a frame never does, so typing a clip's helpers must not cost a
        # re-render. This is the hash's runtime view, not an accident of the
        # dump: parameters and returns are stripped, an annotated assignment
        # hashes as the plain one, and the imports that exist only to spell
        # the annotations go with them.
        (
            "schematics",
            "def _shared_label(ax):",
            "def _shared_label(ax: object) -> None:",
        ),
        ("media", "_ANIM_FPS = 20", "_ANIM_FPS: int = 20"),
        (
            "schematics",
            "from .media import _render_clip, _translate_str",
            "from __future__ import annotations\n\n"
            "from typing import TYPE_CHECKING\n"
            "from .media import _render_clip, _translate_str\n"
            "if TYPE_CHECKING:\n"
            "    from matplotlib.axes import Axes",
        ),
        # Where the keyword-only star sits. It decides how a caller may write
        # the call and not what the function computes, so it cannot move a
        # frame. Without this the flag sweep of #759 would have marked all
        # forty-three clips stale over one star in one shared helper.
        # Imports only a type checker reads: one an annotation alone reads,
        # at run time or moved under ``if TYPE_CHECKING:``, and the names of
        # ``typing`` an annotation reads.
        (
            "media",
            "from .i18n import _translate_figure\n\n_ANIM_FPS = 20\n\n\n"
            "def _translate_str(s):",
            "from matplotlib.axes import Axes\n\nfrom .i18n import _translate_figure"
            "\n\n_ANIM_FPS = 20\n\n\ndef _translate_str(s: Axes):",
        ),
        (
            "media",
            "from .i18n import _translate_figure\n\n_ANIM_FPS = 20\n\n\n"
            "def _translate_str(s):",
            "from typing import TYPE_CHECKING\n\nfrom .i18n import _translate_figure"
            "\n\nif TYPE_CHECKING:\n    from matplotlib.axes import Axes\n\n"
            "_ANIM_FPS = 20\n\n\ndef _translate_str(s: Axes):",
        ),
        (
            "media",
            "from .i18n import _translate_figure\n\n_ANIM_FPS = 20",
            "from typing import Any, Final\n\nfrom .i18n import _translate_figure"
            "\n\n_ANIM_FPS: Final[Any] = 20",
        ),
        # A name the module imports for others, which reach it through their
        # own imports: listed in ``__all__``, or imported from it elsewhere.
        (
            "media",
            "from .i18n import _translate_figure\n",
            "from .i18n import _translate_figure\nfrom .theme import COLOR_PRIMARY\n\n"
            '__all__ = ["COLOR_PRIMARY"]\n',
        ),
        ("theme", "def set_theme(dark):", "def set_theme(*, dark):"),
        (
            "schematics",
            "def _shared_label(ax):",
            "def _shared_label(ax, /):",
        ),
    ],
)
def test_a_change_that_cannot_reach_a_clip_leaves_it_alone(
    tree: pathlib.Path, module: str, old: str, new: str
) -> None:
    before = fp.fingerprints(tree)
    edit(tree, module, old, new)
    assert fp.fingerprints(tree) == before


#: The drawing code of the library a clip borrows its colours from, the
#: physics beside it, and the theme registering a map at import, as the
#: real ``figures.theme`` registers the dark field map.
_PLOT_COMMON = """
_DELTA = 12.0


def theme_fill(colour, ax):
    return (colour, ax, _DELTA)


def _register_dark_map():
    return "phonometry_field_dark"
"""

_PHYSICS = """
def reverberation_time(volume, area):
    return 0.161 * volume / area
"""


def _library_tree(root: pathlib.Path) -> pathlib.Path:
    """The miniature package, its first clip filling with a library helper."""
    _write_tree(root)
    plot = root / "src" / "phonometry" / "_plot"
    plot.mkdir(parents=True)
    (root / "src" / "phonometry" / "__init__.py").write_text("", encoding="utf-8")
    (plot / "__init__.py").write_text("", encoding="utf-8")
    (plot / "common.py").write_text(_PLOT_COMMON, encoding="utf-8")
    (root / "src" / "phonometry" / "room.py").write_text(_PHYSICS, encoding="utf-8")
    edit(
        root,
        "schematics",
        "from .theme import COLOR_PRIMARY",
        "from phonometry._plot.common import theme_fill\n"
        "from phonometry.room import reverberation_time\n"
        "from .theme import COLOR_PRIMARY",
    )
    edit(
        root,
        "schematics",
        '    _translate_str("only in clip one")',
        '    _translate_str("only in clip one")\n    theme_fill(COLOR_PRIMARY, None)',
    )
    edit(
        root,
        "schematics",
        '    _translate_str("only in clip two")',
        '    _translate_str("only in clip two")\n    reverberation_time(100.0, 20.0)',
    )
    edit(
        root,
        "theme",
        'COLOR_PRIMARY = "#1f77b4"',
        "from phonometry._plot.common import _register_dark_map\n\n"
        'COLOR_PRIMARY = "#1f77b4"\n\n_register_dark_map()',
    )
    return root


_VIDEO = """
from ._video_quality import ENCODER_QUALITY, GIF_PALETTE


def _pipe(frames):
    return [frame for frame in frames]


def write_video(path, animation, *, quality="standard", ffmpeg_encoder=None):
    if path.endswith(".gif"):
        return GIF_PALETTE[quality], _pipe(animation)
    if ffmpeg_encoder is None:
        return ENCODER_QUALITY[quality], _pipe(animation)
    return _pipe(animation)
"""

_VIDEO_QUALITY = """
ENCODER_QUALITY = {"standard": ("-crf", "35")}
GIF_PALETTE = {"standard": (128, "bayer")}
"""


def _video_tree(root: pathlib.Path) -> pathlib.Path:
    """The miniature package, its first clip encoding through io with raw options."""
    _library_tree(root)
    io_package = root / "src" / "phonometry" / "io"
    io_package.mkdir()
    (io_package / "__init__.py").write_text("", encoding="utf-8")
    (io_package / "_video.py").write_text(_VIDEO, encoding="utf-8")
    (io_package / "_video_quality.py").write_text(_VIDEO_QUALITY, encoding="utf-8")
    edit(
        root,
        "schematics",
        "from .theme import COLOR_PRIMARY",
        "from phonometry.io._video import write_video\nfrom .theme import COLOR_PRIMARY",
    )
    edit(
        root,
        "schematics",
        '    _translate_str("only in clip one")',
        '    _translate_str("only in clip one")\n'
        '    write_video("one.webm", None, ffmpeg_encoder="av1_nvenc")',
    )
    return root


@pytest.mark.parametrize(
    ("path", "old", "new", "moves"),
    [
        # The encode path a clip's frames go through.
        (
            "_video.py",
            "return [frame for frame in frames]",
            "return list(frames)",
            {"anim_one"},
        ),
        # The encoder presets, which a clip's own encoder and options bypass.
        ("_video_quality.py", '("-crf", "35")', '("-crf", "30")', set()),
        # The GIF palette, which a GIF written with a quality reads.
        ("_video_quality.py", '(128, "bayer")', '(64, "bayer")', {"anim_one"}),
    ],
)
def test_the_encode_path_is_followed_and_the_presets_are_not(
    tmp_path: pathlib.Path, path: str, old: str, new: str, moves: set[str]
) -> None:
    tree = _video_tree(tmp_path)
    before = fp.fingerprints(tree)
    source = tree / "src" / "phonometry" / "io" / path
    text = source.read_text(encoding="utf-8")
    assert text.count(old) == 1, old
    source.write_text(text.replace(old, new), encoding="utf-8")
    after = fp.fingerprints(tree)
    assert {clip for clip in before if before[clip] != after[clip]} == moves


def test_every_ignored_symbol_is_in_the_tree() -> None:
    sources = fp.Sources(pathlib.Path(__file__).resolve().parent.parent)
    assert [symbol for symbol in fp._IGNORED if sources.node(symbol) is None] == []


@pytest.mark.parametrize(
    ("path", "old", "new", "moves"),
    [
        # A library helper a clip draws with, and the constant it reads.
        (
            "_plot/common.py",
            "return (colour, ax, _DELTA)",
            "return (ax, colour)",
            {"anim_one"},
        ),
        ("_plot/common.py", "_DELTA = 12.0", "_DELTA = 4.0", {"anim_one"}),
        # What a module the clips reach runs when it is imported.
        (
            "_plot/common.py",
            'return "phonometry_field_dark"',
            'return "phonometry_field_dark_2"',
            {"anim_one", "anim_two"},
        ),
        # The physics a clip calls moves the static figures, not the stamp.
        ("room.py", "0.161 * volume / area", "0.163 * volume / area", set()),
    ],
)
def test_the_drawing_code_of_the_library_is_followed_and_its_physics_is_not(
    tmp_path: pathlib.Path, path: str, old: str, new: str, moves: set[str]
) -> None:
    tree = _library_tree(tmp_path)
    before = fp.fingerprints(tree)
    source = tree / "src" / "phonometry" / path
    text = source.read_text(encoding="utf-8")
    assert text.count(old) == 1, old
    source.write_text(text.replace(old, new), encoding="utf-8")
    after = fp.fingerprints(tree)
    assert {clip for clip in before if before[clip] != after[clip]} == moves


#: A class, functions with and without a keyword default and a bare lambda:
#: every kind of empty list a node carries (``bases``, ``keywords``,
#: ``decorator_list``, ``posonlyargs``, ``kwonlyargs``, ``kw_defaults``,
#: ``defaults``, ``args``, ``type_ignores`` and, on 3.12, ``type_params``).
#: And the two kinds of ``None``: an optional field left unset (a step-only
#: slice, a ``**`` argument), which no interpreter prints, and a literal
#: (``return None``, ``case None``), which every one prints and must keep.
_EVERY_EMPTY_FIELD = """
class Panel:
    def draw(self, ax, *, label=None):
        ax.plot(x[::2], **style)
        return None

def pick(kind):
    match kind:
        case None:
            return lambda: 0
"""

#: What every interpreter from 3.11 to 3.14 prints for it. Measured on all
#: four; before the empty lists were dropped, 3.11 and 3.12 printed
#: ``decorator_list=[]``, ``bases=[]``, ``type_ignores=[]`` and the other
#: empty lists, and 3.12 ``type_params=[]`` as well, where 3.13 prints
#: nothing, and called every published clip stale.
_PRINTED = (
    "Module(body=[ClassDef(name='Panel', body=[FunctionDef(name='draw', "
    "args=arguments(args=[arg(arg='self'), arg(arg='ax'), arg(arg='label')], "
    "defaults=[Name(id='<no default>', ctx=Load()), Name(id='<no default>', "
    "ctx=Load()), Constant(value=None)]), body=[Expr(value=Call(func=Attribute("
    "value=Name(id='ax', ctx=Load()), attr='plot', ctx=Load()), "
    "args=[Subscript(value=Name(id='x', ctx=Load()), slice=Slice(step="
    "Constant(value=2)), ctx=Load())], keywords=[keyword(value=Name("
    "id='style', ctx=Load()))])), Return(value=Constant(value=None))])]), "
    "FunctionDef(name='pick', args=arguments(args=[arg(arg='kind')], "
    "defaults=[Name(id='<no default>', ctx=Load())]), body=[Match(subject="
    "Name(id='kind', ctx=Load()), cases=[match_case(pattern=MatchSingleton("
    "value=None), body=[Return(value=Lambda(args=arguments(), body=Constant("
    "value=0)))])])])])"
)


def test_the_tree_prints_the_same_on_every_interpreter() -> None:
    """The hash is over the printed tree, so the print may not vary.

    The freshness check runs wherever the sources are, a site build with an
    older system Python included, and stamps written on 3.13 have to hold
    there.
    """
    assert fp._dump(ast.parse(_EVERY_EMPTY_FIELD)) == _PRINTED


def test_no_empty_list_survives_to_be_printed() -> None:
    """What the line above cannot see from one interpreter: the rule itself.

    A field still holding ``[]`` would be printed by 3.11 and 3.12 and
    skipped by 3.13, so none may remain on the node.
    """
    tree = fp._drop_empty_lists(ast.parse(_EVERY_EMPTY_FIELD))
    for node in ast.walk(tree):
        held = vars(node)
        for name in node._fields:
            assert held.get(name) != [], f"{type(node).__name__}.{name} is empty"


def test_a_new_clip_is_reported_rather_than_ignored(tree: pathlib.Path) -> None:
    """A clip added to the registry has no stamp until it is rendered."""
    before = fp.fingerprints(tree)
    edit(
        tree,
        "registry",
        "from .schematics import animate_one, animate_two",
        "from .schematics import animate_one, animate_three, animate_two",
    )
    edit(
        tree,
        "registry",
        '    "anim_two": animate_two,',
        '    "anim_two": animate_two,\n    "anim_three": animate_three,',
    )
    edit(
        tree,
        "schematics",
        "def animate_two(output_dir):",
        'def animate_three(output_dir):\n    """A third clip."""\n'
        '    _render_clip(None, None, output_dir, "anim_three")\n\n\n'
        "def animate_two(output_dir):",
    )
    after = fp.fingerprints(tree)
    assert set(after) - set(before) == {"anim_three"}
    assert {c: after[c] for c in before} == before


# -- the renderer's half of the bargain -------------------------------------
#
# The stamp is only worth anything if it is written whenever the files it
# describes are, which is a claim about the renderer rather than about the
# hash: a batch of clips is minutes of work each, and it is the runs that do
# not finish that decide whether the manifest can be trusted.


@pytest.fixture
def registry() -> ModuleType:
    """The clip registry, with matplotlib's settings left as the test found them.

    Importing the registry imports ``figures.theme``, which sets the settings
    the generator draws with (the grid, the figure size, ``savefig.bbox``)
    for the whole process: what the generator wants in a process of its own,
    and what the first test of a worker to import it would otherwise leave to
    every test after it. So the import runs inside ``rc_context``, and the
    test after it does not: a setting the test itself leaves changed is
    still reported by the check in ``conftest.py``.
    """
    import matplotlib as mpl

    with mpl.rc_context():
        from figures import registry

    return registry


def _fake_batch(
    monkeypatch: pytest.MonkeyPatch, registry: ModuleType, fails: str | None
) -> list[list[str]]:
    """Run a three-clip batch with the rendering replaced, return the stamps."""
    import shutil

    stamped: list[list[str]] = []

    def render(clip: str, output_dir: str) -> None:
        if clip == fails:
            msg = "the encoder died"
            raise RuntimeError(msg)

    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/ffmpeg")
    monkeypatch.setattr(
        registry, "_ANIMATIONS", dict.fromkeys(("anim_one", "anim_two", "anim_three"))
    )
    monkeypatch.setattr(registry, "_render_anim_variants", render)
    monkeypatch.setattr(
        registry, "_stamp_clips", lambda clips, output_dir: stamped.append(list(clips))
    )
    if fails is None:
        registry.generate_animations("images", variants=True)
    else:
        with pytest.raises(RuntimeError, match=r"^the encoder died$"):
            registry.generate_animations("images", variants=True)
    return stamped


def test_a_finished_batch_stamps_every_clip_it_rendered(
    monkeypatch: pytest.MonkeyPatch, registry: ModuleType
) -> None:
    assert _fake_batch(monkeypatch, registry, fails=None) == [
        ["anim_one", "anim_two", "anim_three"]
    ]


def test_a_clip_that_dies_does_not_cost_the_stamps_of_the_ones_before_it(
    monkeypatch: pytest.MonkeyPatch, registry: ModuleType
) -> None:
    """The clips already on disk keep their fingerprints when a later one dies.

    Their four variants are written and complete; leaving with the error and
    no stamp would have the freshness check report them as unrendered, and
    the way to make it green again would be to render, at several minutes
    each, clips that are already correct.
    """
    assert _fake_batch(monkeypatch, registry, fails="anim_two") == [["anim_one"]]


def _fake_parallel_batch(
    monkeypatch: pytest.MonkeyPatch, registry: ModuleType, fails: str | None
) -> list[list[str]]:
    """Run a three-clip *parallel* batch with the pool replaced, return the stamps.

    The pool is faked rather than run for real: ``_generate_animations_parallel``
    submits a picklable worker entry point to a spawn-context process pool, and
    a monkeypatch on the parent process cannot reach code that runs in a freshly
    spawned child. What is under test here is not the render but the bookkeeping
    around the futures -- which of them get stamped -- so a fake pool that runs
    each task synchronously, in submission order, on a single simulated worker
    is enough: once one task raises, later submissions are left un-started
    (``PENDING``) exactly as a real pool leaves queued-but-not-yet-picked-up
    tasks, so ``future.cancel()`` on them succeeds the same way it would for
    the real thing.
    """
    import concurrent.futures as cf

    stamped: list[list[str]] = []

    class _FakePool:
        def __init__(self, *, max_workers: int, mp_context: object) -> None:
            del max_workers, mp_context
            self._stopped = False

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *exc_info: object) -> None:
            del exc_info

        def submit(self, fn: object, clip: str, img_dir: str) -> cf.Future[str]:
            del fn, img_dir
            future: cf.Future[str] = cf.Future()
            if self._stopped:
                return future  # queued behind the failure: never started
            if clip == fails:
                future.set_exception(RuntimeError("the encoder died"))
                self._stopped = True
            else:
                future.set_result(clip)
            return future

    monkeypatch.setattr(cf, "ProcessPoolExecutor", _FakePool)
    monkeypatch.setattr(
        registry, "_stamp_clips", lambda clips, output_dir: stamped.append(list(clips))
    )
    clips = ["anim_one", "anim_two", "anim_three"]
    if fails is None:
        registry._generate_animations_parallel("images", clips, jobs=1)
    else:
        with pytest.raises(
            RuntimeError, match=r"(?s)animation generation failed.*the encoder died"
        ):
            registry._generate_animations_parallel("images", clips, jobs=1)
    return stamped


def test_a_finished_parallel_batch_stamps_every_clip_it_rendered(
    monkeypatch: pytest.MonkeyPatch, registry: ModuleType
) -> None:
    assert _fake_parallel_batch(monkeypatch, registry, fails=None) == [
        ["anim_one", "anim_two", "anim_three"]
    ]


def test_a_parallel_task_that_dies_does_not_cost_the_stamps_of_the_ones_before_it(
    monkeypatch: pytest.MonkeyPatch, registry: ModuleType
) -> None:
    """A task still queued when another dies is cancelled, and stays unstamped.

    ``anim_one`` has already finished, ``anim_two`` is the one that dies, and
    ``anim_three`` is still queued behind it and gets cancelled rather than
    started. Both facts -- that ``anim_one`` is stamped and that the caller
    still sees the aggregate ``RuntimeError`` -- have to hold from the same
    call, because ``_stamp_clips`` runs before the ``raise``: catching the
    error with ``pytest.raises`` and then inspecting ``stamped`` is what pins
    the stamp as happening before the failure propagates, not after.
    """
    assert _fake_parallel_batch(monkeypatch, registry, fails="anim_two") == [
        ["anim_one"]
    ]


def test_re_extracting_the_posters_stamps_the_clips_they_belong_to(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path, registry: ModuleType
) -> None:
    """The poster extractor is inside the fingerprint, so `make posters` stamps.

    A change to how a poster is cut marks every clip stale, and re-extracting
    is the answer that renders nothing. It has to stamp the way a render
    does, once per clip and not once per variant, or the check would keep
    asking for a re-render of frames that did not change.
    """
    for name in (
        "anim_one",
        "anim_one_dark",
        "anim_one_es",
        "anim_one_es_dark",
        "anim_two",
    ):
        (tmp_path / f"{name}.webm").write_bytes(b"")
    cut: list[str] = []
    stamped: list[tuple[list[str], bool]] = []
    monkeypatch.setattr(
        registry, "_extract_poster", lambda webm, ss: cut.append(webm) or webm
    )
    monkeypatch.setattr(registry, "_poster_ss_for", lambda webm: None)
    monkeypatch.setattr(
        registry,
        "_stamp_clips",
        lambda clips, output_dir, *, keep_encoder=False: stamped.append(
            (list(clips), keep_encoder)
        ),
    )
    registry.generate_posters(str(tmp_path))
    assert len(cut) == 5
    # The posters are cut from the WebM already there, so the encoder that
    # wrote it stays the one recorded.
    assert stamped == [(["anim_one", "anim_two"], True)]


# -- what the check says ----------------------------------------------------


def _check(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    committed: list[str],
    stamps: dict[str, str],
    *,
    encoder: str | None = "libsvtav1",
) -> int:
    """Run the freshness check over a made-up clips directory and manifest.

    Each stamp is a manifest line that names *encoder* as the one that wrote
    the clip, or names none when *encoder* is None.
    """
    import check_animation_freshness as check

    images = tmp_path / "images"
    images.mkdir()
    for name in committed:
        (images / name).write_bytes(b"")
    manifest = tmp_path / "manifest.txt"
    manifest.write_text(
        "".join(
            f"{clip} {digest}" + (f" {encoder}" if encoder is not None else "") + "\n"
            for clip, digest in stamps.items()
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(check.assets_dir, "clips_dir", lambda: images)
    monkeypatch.setattr(check.fp, "fingerprints", lambda root: {"anim_one": "1"})
    monkeypatch.setattr(check.fp, "MANIFEST", manifest)
    return check.main([])


def test_a_complete_and_stamped_clip_passes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import check_animation_freshness as check

    code = _check(monkeypatch, tmp_path, check.outputs("anim_one"), {"anim_one": "1"})
    assert code == 0
    assert "1 published clips" in capsys.readouterr().out


def test_a_fresh_clip_with_no_encoder_recorded_is_asked_for_again(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A stamp that does not say which encoder wrote the WebM is not enough.

    Every file is there and the fingerprint matches, but the manifest line is
    the clip and its fingerprint with nothing after them: nothing says the
    clip is AV1, so the check asks for the clip again.
    """
    import check_animation_freshness as check

    code = _check(
        monkeypatch,
        tmp_path,
        check.outputs("anim_one"),
        {"anim_one": "1"},
        encoder=None,
    )
    assert code == 1
    out = capsys.readouterr().out
    assert "anim_one: no AV1 encoder recorded (none); re-render the clip" in out
    assert "drawn by code that has changed" not in out


@pytest.mark.parametrize(
    "dropped", ["anim_one_es.webm", "anim_one_es_dark_poster.webp", "anim_one_dark.gif"]
)
def test_every_file_a_render_writes_is_asked_for(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    dropped: str,
) -> None:
    """A poster or a GIF left behind is as broken as a missing WebM.

    They are written by the same render and embedded by the same pages: the
    site defers the video behind the poster and the GitHub documentation
    shows the GIF, so either one missing is a hole in the docs that the four
    WebM files being there says nothing about.
    """
    import check_animation_freshness as check

    committed = [name for name in check.outputs("anim_one") if name != dropped]
    code = _check(monkeypatch, tmp_path, committed, {"anim_one": "1"})
    assert code == 1
    out = capsys.readouterr().out
    assert f"1 of its 10 files are missing ({dropped})" in out


def test_a_half_rendered_clip_is_not_called_uncommitted(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The clip is there; only some of its files are, and only that is said."""
    import check_animation_freshness as check

    committed = check.outputs("anim_one")[:2]
    assert _check(monkeypatch, tmp_path, committed, {}) == 1
    out = capsys.readouterr().out
    assert "published half-rendered, 8 of its 10 files are missing" in out
    assert "no clip committed" not in out
    assert "no fingerprint recorded; re-render the clip to stamp it" in out


def test_a_clip_with_no_files_at_all_says_so(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert _check(monkeypatch, tmp_path, [], {}) == 1
    out = capsys.readouterr().out
    assert "registered but not published at all" in out
    assert "half-rendered" not in out


FIELD_SCENE = '''
from .media import _render_clip


def _field():
    """A field builder: it steps an engine."""
    from phonometry.simulation import FDTD2D

    return FDTD2D


def animate_field(output_dir):
    """A clip of a simulated field."""
    _field()
    _render_clip(None, None, output_dir, "anim_field")
'''

MATERIAL_SCENE = '''
from phonometry.simulation import ALUMINUM

from .media import _render_clip


def animate_material(output_dir):
    """A clip that names a material of the simulation package at import."""
    _render_clip(ALUMINUM, None, output_dir, "anim_material")
'''

_DIGESTS = {
    "environment": {"system": "Linux", "machine": "x86_64", "python": "3.13"},
    "measured_on": {"cpu": "AMD EPYC 7763 64-Core Processor"},
    "scenarios": {"sponge": {"p": "aa", "vx": "bb"}},
    "fluid_energy": {"0": "0x1.0000000000000p+0"},
}


def _engine_tree(root: pathlib.Path) -> pathlib.Path:
    """The miniature tree plus two clips that use the simulation package."""
    tree = _write_tree(root)
    package = tree / "scripts" / "figures"
    (package / "fields.py").write_text(FIELD_SCENE, encoding="utf-8")
    (package / "materials.py").write_text(MATERIAL_SCENE, encoding="utf-8")
    registry = REGISTRY.replace(
        "from .schematics import animate_one, animate_two",
        "from .fields import animate_field\n"
        "from .materials import animate_material\n"
        "from .schematics import animate_one, animate_two",
    ).replace(
        '"anim_two": animate_two,',
        '"anim_two": animate_two,\n'
        '    "anim_field": animate_field,\n'
        '    "anim_material": animate_material,',
    )
    (package / "registry.py").write_text(registry, encoding="utf-8")
    (tree / fp.ENGINE_DIGESTS).write_text(json.dumps(_DIGESTS), encoding="utf-8")
    return tree


def _rewrite_digests(tree: pathlib.Path, key: str, value: object) -> None:
    path = tree / fp.ENGINE_DIGESTS
    data = json.loads(path.read_text(encoding="utf-8"))
    data[key] = value
    path.write_text(json.dumps(data), encoding="utf-8")


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("scenarios", {"sponge": {"p": "aa", "vx": "cc"}}),
        ("fluid_energy", {"0": "0x1.0000000000001p+0"}),
    ],
)
def test_a_clip_that_steps_an_engine_follows_its_golden_digests(
    tmp_path: pathlib.Path, key: str, value: object
) -> None:
    """A moved digest and a moved fluid-energy record are both a moved number."""
    tree = _engine_tree(tmp_path)
    before = fp.fingerprints(tree)
    _rewrite_digests(tree, key, value)
    after = fp.fingerprints(tree)
    assert {clip for clip in before if before[clip] != after[clip]} == {
        "anim_field",
        "anim_material",
    }


#: A drawing helper of the library that steps an engine itself, through a
#: relative import of the simulation package, and one that only names a
#: sibling of it.
_PLOT_FIELDS = '''
def field_panel(ax):
    """A panel that steps the field it draws."""
    from ..simulation import FDTD2D

    return FDTD2D


def decay_panel(ax):
    """A panel that only reads the room package."""
    from ..room import reverberation_time

    return reverberation_time


def package_panel(ax):
    """A panel that imports the simulation package itself, relatively."""
    from .. import simulation

    return simulation.FDTD2D
'''

#: A drawing helper one package deeper, three levels below the package root.
_PLOT_NESTED = '''
def nested_panel(ax):
    """A panel of a sub-package that steps the field it draws."""
    from ...simulation import FDTD2D

    return FDTD2D
'''

#: Each way a clip reaches the simulation package other than by a plain
#: ``from phonometry.simulation import ...``, and two that reach a sibling
#: package the same ways; the clip is ``anim_reach``.
_REACHES = {
    "relative-import-in-the-library": (
        "from phonometry._plot.fields import field_panel\n",
        "field_panel(None)",
    ),
    "package-attribute": ("import phonometry\n", "phonometry.simulation.FDTD2D"),
    "aliased-package-attribute": (
        "import phonometry as ph\n",
        "ph.simulation.fdtd.FDTD2D",
    ),
    "package-attribute-imported-in-the-function": (
        "",
        "import phonometry\n    phonometry.simulation.FDTD2D",
    ),
    "relative-import-of-a-sibling": (
        "from phonometry._plot.fields import decay_panel\n",
        "decay_panel(None)",
    ),
    "sibling-package-attribute": ("import phonometry\n", "phonometry.room.T60"),
    "relative-package-import-in-the-library": (
        "from phonometry._plot.fields import package_panel\n",
        "package_panel(None)",
    ),
    "level-three-import-in-a-sub-package": (
        "from phonometry._plot.geometry.fields import nested_panel\n",
        "nested_panel(None)",
    ),
    "dotted-import-of-another-package": (
        "import phonometry.io\n",
        "phonometry.simulation.FDTD2D",
    ),
    "dotted-import-of-the-engines": (
        "import phonometry.simulation\n",
        "phonometry.room.T60",
    ),
    "package-named-like-the-engines": (
        "from phonometry.simulations import T60\n",
        "T60",
    ),
    "library-helper-imported-in-the-function": (
        "",
        "from phonometry._plot.fields import field_panel\n    field_panel(None)",
    ),
}


def _reaching_tree(root: pathlib.Path, reach: str) -> pathlib.Path:
    """The engine tree plus ``anim_reach``, which reaches a package the way *reach* names."""
    tree = _engine_tree(root)
    plot = tree / "src" / "phonometry" / "_plot"
    plot.mkdir(parents=True)
    (tree / "src" / "phonometry" / "__init__.py").write_text("", encoding="utf-8")
    (plot / "__init__.py").write_text("", encoding="utf-8")
    (plot / "fields.py").write_text(_PLOT_FIELDS, encoding="utf-8")
    (plot / "geometry").mkdir()
    (plot / "geometry" / "__init__.py").write_text("", encoding="utf-8")
    (plot / "geometry" / "fields.py").write_text(_PLOT_NESTED, encoding="utf-8")
    header, call = _REACHES[reach]
    package = tree / "scripts" / "figures"
    (package / "reach.py").write_text(
        f"{header}\nfrom .media import _render_clip\n\n\n"
        f"def animate_reach(output_dir):\n    {call}\n"
        '    _render_clip(None, None, output_dir, "anim_reach")\n',
        encoding="utf-8",
    )
    edit(
        tree,
        "registry",
        "from .materials import animate_material\n",
        "from .materials import animate_material\nfrom .reach import animate_reach\n",
    )
    edit(
        tree,
        "registry",
        '    "anim_material": animate_material,',
        '    "anim_material": animate_material,\n    "anim_reach": animate_reach,',
    )
    return tree


@pytest.mark.parametrize(
    ("reach", "steps"),
    [
        ("relative-import-in-the-library", True),
        ("package-attribute", True),
        ("aliased-package-attribute", True),
        ("package-attribute-imported-in-the-function", True),
        ("relative-import-of-a-sibling", False),
        ("sibling-package-attribute", False),
        ("relative-package-import-in-the-library", True),
        ("level-three-import-in-a-sub-package", True),
        ("dotted-import-of-another-package", True),
        ("dotted-import-of-the-engines", False),
        ("package-named-like-the-engines", False),
        ("library-helper-imported-in-the-function", True),
    ],
)
def test_every_way_of_reaching_the_simulation_package_ties_a_clip_to_the_digests(
    tmp_path: pathlib.Path, reach: str, *, steps: bool
) -> None:
    """A clip steps an engine however its code names the simulation package.

    A relative import inside a library helper the walk reaches, and the
    package's own attributes after ``import phonometry``, reach it as surely
    as ``from phonometry.simulation import``, from a sub-package too; a
    sibling package reached the same ways does not, nor does one whose name
    only starts like it. ``import phonometry.io`` binds ``phonometry``, the
    package, as Python binds it: the engines stay reachable through it, and
    ``import phonometry.simulation`` does not make every ``phonometry.X``
    an engine.
    """
    tree = _reaching_tree(tmp_path, reach)
    expected = {"anim_field", "anim_material"} | ({"anim_reach"} if steps else set())
    assert fp.engine_clips(tree) == expected


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("environment", {"system": "Darwin"}),
        ("measured_on", {"cpu": "Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz"}),
    ],
)
def test_where_the_digests_were_measured_moves_no_clip(
    tmp_path: pathlib.Path, key: str, value: object
) -> None:
    """The environment and the CPU the file records are not what the engines compute."""
    tree = _engine_tree(tmp_path)
    before = fp.fingerprints(tree)
    _rewrite_digests(tree, key, value)
    assert fp.fingerprints(tree) == before


def test_a_rewrite_of_the_engine_source_moves_no_clip(tmp_path: pathlib.Path) -> None:
    """The walk never reads the engines; their digests stand for them."""
    tree = _engine_tree(tmp_path)
    engine = tree / "src" / "phonometry" / "simulation" / "fdtd.py"
    engine.parent.mkdir(parents=True)
    engine.write_text("def step(p):\n    return p + 1\n", encoding="utf-8")
    before = fp.fingerprints(tree)
    engine.write_text("def step(p):\n    return 1 + p\n", encoding="utf-8")
    assert fp.fingerprints(tree) == before


def test_a_missing_digest_file_is_named(tmp_path: pathlib.Path) -> None:
    tree = _engine_tree(tmp_path)
    (tree / fp.ENGINE_DIGESTS).unlink()
    with pytest.raises(FileNotFoundError, match=r"engine-digests\.json is missing"):
        fp.fingerprints(tree)


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ('{"scenarios": {', r"not JSON: .+"),
        (json.dumps({"scenarios": _DIGESTS["scenarios"]}), r"no fluid_energy record"),
        (
            json.dumps({"fluid_energy": _DIGESTS["fluid_energy"]}),
            r"no scenarios record",
        ),
        ("{}", r"no scenarios and no fluid_energy record"),
        (json.dumps([_DIGESTS]), r"an array where an object belongs"),
        ('"scenarios fluid_energy"', r"a string where an object belongs"),
        ("3", r"a number where an object belongs"),
        ("true", r"true or false where an object belongs"),
        ("null", r"null where an object belongs"),
    ],
    ids=[
        "not-json",
        "no-fluid-energy",
        "no-scenarios",
        "no-record",
        "array",
        "string",
        "number",
        "boolean",
        "null",
    ],
)
def test_a_digest_file_that_holds_no_digests_is_named_with_its_remedy(
    tmp_path: pathlib.Path, text: str, reason: str
) -> None:
    """A file cut short, one that lost a record, or one that is no object says why, in JSON's words."""
    tree = _engine_tree(tmp_path)
    (tree / fp.ENGINE_DIGESTS).write_text(text, encoding="utf-8")
    with pytest.raises(
        ValueError,
        match=rf"engine-digests\.json does not hold the engines' digests "
        rf"\({reason}\); record them again with `make engine-digests`$",
    ):
        fp.fingerprints(tree)


def test_the_digest_file_named_here_is_the_one_the_digests_are_written_to() -> None:
    """The fingerprint reads the file ``scripts/engine_digests.py`` writes.

    The fingerprint module stays on the standard library, so it names the
    file itself rather than importing the writer, which needs NumPy.
    """
    import engine_digests

    assert fp.ENGINE_DIGESTS == engine_digests.DIGESTS_FILE.name


def test_the_engine_clips_of_the_repository_are_the_field_clips() -> None:
    from figures import registry

    root = pathlib.Path(__file__).resolve().parents[1]
    assert fp.engine_clips(root) == set(registry._ANIM_FIELDS)


def test_a_stamp_records_the_encoder_and_a_poster_stamp_keeps_it(
    tree: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = tree / "manifest.txt"
    monkeypatch.setattr(fp, "MANIFEST", manifest)
    fp.stamp(["anim_one"], tree, encoder="av1_nvenc")
    assert fp.read_encoders() == {"anim_one": "av1_nvenc"}
    fp.stamp(["anim_one"], tree, encoder=None)
    assert fp.read_encoders() == {"anim_one": "av1_nvenc"}


def test_a_stamp_given_the_fingerprints_of_its_tree_records_them_as_given(
    tree: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A caller that has taken them on the tree already passes them, and they are not taken again.

    Only the clips named are stamped: the rest of the mapping is left out.
    """

    def again(root: pathlib.Path) -> dict[str, str]:
        pytest.fail("the stamp took the fingerprints it was given")

    monkeypatch.setattr(fp, "MANIFEST", tree / "manifest.txt")
    monkeypatch.setattr(fp, "fingerprints", again)
    taken = {"anim_one": "0123456789abcdef", "anim_two": "fedcba9876543210"}
    fp.stamp(["anim_one"], tree, encoder="libsvtav1", current=taken)
    assert fp.read_manifest() == {"anim_one": "0123456789abcdef"}
    assert fp.read_encoders() == {"anim_one": "libsvtav1"}


def test_a_poster_stamp_of_a_clip_with_no_encoder_is_refused(
    tree: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(fp, "MANIFEST", tree / "manifest.txt")
    with pytest.raises(ValueError, match=r"anim_one has no encoder recorded"):
        fp.stamp(["anim_one"], tree, encoder=None)


def test_a_poster_stamp_of_two_clips_one_without_an_encoder_writes_nothing(
    tree: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Clips stamped together are stamped all or none.

    ``anim_one`` has its encoder recorded and ``anim_two`` has none, so the
    poster stamp of the two is refused; the stamp ``anim_one`` would have
    taken is not written either, and the manifest is left byte for byte.
    """
    manifest = tree / "manifest.txt"
    manifest.write_text(
        "anim_one 0000000000000000 av1_nvenc\nanim_two 1111111111111111\n",
        encoding="utf-8",
    )
    before = manifest.read_bytes()
    monkeypatch.setattr(fp, "MANIFEST", manifest)
    taken = {"anim_one": "aaaaaaaaaaaaaaaa", "anim_two": "bbbbbbbbbbbbbbbb"}
    with pytest.raises(ValueError, match=r"^anim_two has no encoder recorded"):
        fp.stamp(["anim_one", "anim_two"], tree, encoder=None, current=taken)
    assert manifest.read_bytes() == before


def test_a_manifest_line_without_an_encoder_still_reads_its_fingerprint(
    tree: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = tree / "manifest.txt"
    manifest.write_text("anim_one 0123456789abcdef\n", encoding="utf-8")
    monkeypatch.setattr(fp, "MANIFEST", manifest)
    assert fp.read_manifest() == {"anim_one": "0123456789abcdef"}
    assert fp.read_encoders() == {}


def test_a_render_told_not_to_stamp_stamps_nothing_one_clip_or_a_pool_at_a_time(
    monkeypatch: pytest.MonkeyPatch, registry: ModuleType
) -> None:
    """A node's lane renders into a scratch directory, which is never a statement about what is published."""
    import concurrent.futures as cf
    import shutil

    def refuse(*_: object, **__: object) -> None:
        pytest.fail("a render told not to stamp stamped")

    class _Pool:
        def __init__(self, *, max_workers: int, mp_context: object) -> None:
            del max_workers, mp_context

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *exc_info: object) -> None:
            del exc_info

        def submit(self, fn: object, clip: str, img_dir: str) -> cf.Future[str]:
            del fn, img_dir
            future: cf.Future[str] = cf.Future()
            future.set_result(clip)
            return future

    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/ffmpeg")
    monkeypatch.setattr(
        registry, "_ANIMATIONS", dict.fromkeys(("anim_one", "anim_two"))
    )
    monkeypatch.setattr(
        registry, "_render_anim_variants", lambda clip, output_dir: None
    )
    monkeypatch.setattr(registry, "_stamp_clips", refuse)
    monkeypatch.setattr(cf, "ProcessPoolExecutor", _Pool)
    registry.generate_animations("images", variants=True, stamp=False)
    registry._generate_animations_parallel(
        "images", ["anim_one", "anim_two"], jobs=1, stamp=False
    )


@pytest.mark.parametrize(
    ("module", "statement", "resolved"),
    [
        ("figures.schematics", "from .theme import X", "figures.theme"),
        ("figures.schematics", "from .. import x", ""),
        ("figures.schematics", "from ...theme import X", ""),
        ("figures", "from . import media", "figures"),
        ("figures", "from ..theme import X", ""),
    ],
    ids=[
        "sibling",
        "past-the-top",
        "far-past-the-top",
        "package",
        "package-past-the-top",
    ],
)
def test_a_relative_import_deeper_than_its_package_resolves_to_no_module(
    tree: pathlib.Path, module: str, statement: str, resolved: str
) -> None:
    """Python refuses an import that climbs past the top package; the walk reads it as naming nothing."""
    sources = fp.Sources(tree)
    node = ast.parse(statement).body[0]
    assert isinstance(node, ast.ImportFrom)
    assert sources.modules[module]._resolve_import(node) == resolved


def _write_media(tree: pathlib.Path, header: str, body: str) -> None:
    """The miniature clip tail with *header* at its top and *body* as ``_translate_str``'s."""
    text = MEDIA.replace(
        "def _translate_str(s):\n    return s\n", f"def _translate_str(s):\n{body}\n"
    )
    (tree / "scripts" / "figures" / "media.py").write_text(
        header + text, encoding="utf-8"
    )


#: Import tidies: two spellings of the same code, which must hash alike.
_TIDIES = {
    "alias-renamed": (
        ("import re as _re\n", '    return _re.sub("a", "b", s)'),
        ("import re\n", '    return re.sub("a", "b", s)'),
    ),
    "redundant-local-import-dropped": (
        ("import re\n", '    import re as _re\n\n    return _re.sub("a", "b", s)'),
        ("import re\n", '    return re.sub("a", "b", s)'),
    ),
    "import-moved-to-the-top": (
        ("", '    import re\n\n    return re.sub("a", "b", s)'),
        ("import re\n", '    return re.sub("a", "b", s)'),
    ),
    "imported-by-name-or-through-its-module": (
        ("from re import sub\n", '    return sub("a", "b", s)'),
        ("import re\n", '    return re.sub("a", "b", s)'),
    ),
    # Prose above an import kept for its side effect is still prose.
    "docstring-above-a-side-effect-import-dropped": (
        (
            "",
            '    """Load the 3D axes."""\n    import mpl_toolkits.mplot3d\n\n    return s',
        ),
        ("", "    import mpl_toolkits.mplot3d\n\n    return s"),
    ),
}


@pytest.mark.parametrize("tidy", sorted(_TIDIES))
def test_an_import_tidy_moves_no_fingerprint(tree: pathlib.Path, tidy: str) -> None:
    """How a name is imported cannot change a frame; what it is bound to can.

    Each name an import binds is hashed as the dotted name it is bound to, so
    ``_re.sub`` after ``import re as _re`` and ``re.sub`` after ``import re``
    hash alike, wherever the import stands.
    """
    (header, body), (tidied_header, tidied_body) = _TIDIES[tidy]
    _write_media(tree, header, body)
    before = fp.fingerprints(tree)
    _write_media(tree, tidied_header, tidied_body)
    assert fp.fingerprints(tree) == before


@pytest.mark.parametrize(
    ("before", "after", "moves"),
    [
        (
            ("import matplotlib.pyplot as plt\n", "    return plt.close(s)"),
            ("import matplotlib.pylab as plt\n", "    return plt.close(s)"),
            {"anim_one", "anim_two"},
        ),
        (
            ("from re import sub\n", '    return sub("a", "b", s)'),
            ("from re import subn as sub\n", '    return sub("a", "b", s)'),
            {"anim_one", "anim_two"},
        ),
        # An import nothing uses imports for what importing it does.
        (
            ("import mpl_toolkits.mplot3d\n", "    return s"),
            ("import mpl_toolkits.axisartist\n", "    return s"),
            {"anim_one", "anim_two"},
        ),
        # The same inside a function, as its first statement, where a string
        # would be a docstring.
        (
            ("", "    import mpl_toolkits.mplot3d\n\n    return s"),
            ("", "    import mpl_toolkits.axisartist\n\n    return s"),
            {"anim_one", "anim_two"},
        ),
        # A name two imports bind under a condition, in a function and at the
        # top of the module: the target of either, and the condition, count.
        (
            (
                "",
                "    if s:\n        import json as _codec\n    else:\n"
                "        import pickle as _codec\n    return _codec.dumps(s)",
            ),
            (
                "",
                "    if s:\n        import marshal as _codec\n    else:\n"
                "        import pickle as _codec\n    return _codec.dumps(s)",
            ),
            {"anim_one", "anim_two"},
        ),
        (
            (
                "",
                "    try:\n        from json import dumps as _enc\n"
                "    except ImportError:\n        from pickle import dumps as _enc\n"
                "    return _enc(s)",
            ),
            (
                "",
                "    try:\n        from marshal import dumps as _enc\n"
                "    except ImportError:\n        from pickle import dumps as _enc\n"
                "    return _enc(s)",
            ),
            {"anim_one", "anim_two"},
        ),
        (
            (
                "try:\n    from json import dumps as _enc\nexcept ImportError:\n"
                "    from pickle import dumps as _enc\n",
                "    return _enc(s)",
            ),
            (
                "try:\n    from json import dumps as _enc\nexcept ImportError:\n"
                "    from marshal import dumps as _enc\n",
                "    return _enc(s)",
            ),
            {"anim_one", "anim_two"},
        ),
        (
            (
                'import sys\n\nif sys.platform == "linux":\n    import json as _codec\n'
                "else:\n    import pickle as _codec\n",
                "    return _codec.dumps(s)",
            ),
            (
                'import sys\n\nif sys.platform == "linux":\n    import marshal as _codec\n'
                "else:\n    import pickle as _codec\n",
                "    return _codec.dumps(s)",
            ),
            {"anim_one", "anim_two"},
        ),
        (
            (
                'import sys\n\nif sys.platform == "linux":\n    import json as _codec\n'
                "else:\n    import pickle as _codec\n",
                "    return _codec.dumps(s)",
            ),
            (
                'import sys\n\nif sys.platform != "linux":\n    import json as _codec\n'
                "else:\n    import pickle as _codec\n",
                "    return _codec.dumps(s)",
            ),
            {"anim_one", "anim_two"},
        ),
        # One import under a condition: the condition counts too.
        (
            (
                'import sys\n\nif sys.platform == "linux":\n    import json as _codec\n',
                "    return _codec.dumps(s)",
            ),
            (
                'import sys\n\nif sys.platform != "linux":\n    import json as _codec\n',
                "    return _codec.dumps(s)",
            ),
            {"anim_one", "anim_two"},
        ),
        # A guarded or rebound import whose name an annotation or __all__ also
        # names is still read at run time: its target counts.
        (
            (
                "try:\n    from json import JSONDecoder as _Dec\nexcept ImportError:\n"
                "    from pickle import Unpickler as _Dec\n\n\n"
                "def _annotated(x: _Dec) -> None:\n    return None\n",
                "    return _Dec(s)",
            ),
            (
                "try:\n    from marshal import JSONDecoder as _Dec\nexcept ImportError:\n"
                "    from pickle import Unpickler as _Dec\n\n\n"
                "def _annotated(x: _Dec) -> None:\n    return None\n",
                "    return _Dec(s)",
            ),
            {"anim_one", "anim_two"},
        ),
        (
            (
                "try:\n    from json import JSONDecoder as _Dec\nexcept Exception:\n"
                "    from pickle import Unpickler as _Dec\n\n\n"
                "def _annotated(x: _Dec) -> None:\n    return None\n",
                "    return _Dec(s)",
            ),
            (
                "try:\n    from marshal import JSONDecoder as _Dec\nexcept Exception:\n"
                "    from pickle import Unpickler as _Dec\n\n\n"
                "def _annotated(x: _Dec) -> None:\n    return None\n",
                "    return _Dec(s)",
            ),
            {"anim_one", "anim_two"},
        ),
        (
            (
                "try:\n    from json import dumps as _enc\nexcept ImportError:\n"
                '    from pickle import dumps as _enc\n\n__all__ = ["_enc"]\n',
                "    return _enc(s)",
            ),
            (
                "try:\n    from marshal import dumps as _enc\nexcept ImportError:\n"
                '    from pickle import dumps as _enc\n\n__all__ = ["_enc"]\n',
                "    return _enc(s)",
            ),
            {"anim_one", "anim_two"},
        ),
        (
            (
                "import json as _codec\n\n_codec = _codec\n\n\n"
                "def _annotated(x: _codec) -> None:\n    return None\n",
                "    return _codec.dumps(s)",
            ),
            (
                "import marshal as _codec\n\n_codec = _codec\n\n\n"
                "def _annotated(x: _codec) -> None:\n    return None\n",
                "    return _codec.dumps(s)",
            ),
            {"anim_one", "anim_two"},
        ),
        # An import only a function no clip reaches uses still runs on
        # import: what it imports counts.
        (
            (
                "import numpy as np\n",
                "    return s\n\n\ndef _unused():\n    return np.ones(1)",
            ),
            (
                "import numpy.random as np\n",
                "    return s\n\n\ndef _unused():\n    return np.ones(1)",
            ),
            {"anim_one", "anim_two"},
        ),
    ],
    ids=[
        "module-alias",
        "name-imported",
        "side-effect",
        "side-effect-in-a-function",
        "if-else-in-a-function",
        "try-except-in-a-function",
        "try-except-at-the-top",
        "if-else-at-the-top",
        "if-condition-at-the-top",
        "one-import-under-a-condition",
        "guarded-and-annotated",
        "guarded-any-exception-and-annotated",
        "guarded-and-in-all",
        "rebound-and-annotated",
        "unreached",
    ],
)
def test_a_changed_import_target_moves_the_clips_that_use_it(
    tree: pathlib.Path,
    before: tuple[str, str],
    after: tuple[str, str],
    moves: set[str],
) -> None:
    """``plt`` bound to ``matplotlib.pylab`` instead of ``matplotlib.pyplot`` is other code."""
    _write_media(tree, *before)
    first = fp.fingerprints(tree)
    _write_media(tree, *after)
    second = fp.fingerprints(tree)
    assert {clip for clip in first if first[clip] != second[clip]} == moves


def test_a_name_another_module_imports_from_a_clip_s_module_is_no_effect_there(
    tree: pathlib.Path,
) -> None:
    """A re-export is reached through the module that imports it, not hashed where it passes.

    Through the walk to where it is defined, or out of the walk to the dotted
    name it comes from.
    """
    before = fp.fingerprints(tree)
    edit(
        tree,
        "media",
        "from .i18n import _translate_figure\n",
        "from .i18n import _translate_figure\nfrom .theme import COLOR_PRIMARY\n",
    )
    edit(
        tree,
        "schematics",
        "from .theme import COLOR_PRIMARY",
        "from .media import COLOR_PRIMARY",
    )
    assert fp.fingerprints(tree) == before
    # A name re-exported from outside the walk is read as where it comes from,
    # so a changed target there moves the clips that call it.
    edit(
        tree,
        "theme",
        'COLOR_PRIMARY = "#1f77b4"',
        'from json import dumps as _reexp\n\nCOLOR_PRIMARY = "#1f77b4"',
    )
    edit(
        tree,
        "media",
        "from .theme import COLOR_PRIMARY\n",
        "from .theme import COLOR_PRIMARY, _reexp\n",
    )
    edit(
        tree,
        "media",
        "def _translate_str(s):\n    return s",
        "def _translate_str(s):\n    return _reexp(s)",
    )
    reexported = fp.fingerprints(tree)
    edit(
        tree,
        "theme",
        "from json import dumps as _reexp",
        "from pickle import dumps as _reexp",
    )
    moved = fp.fingerprints(tree)
    assert {clip for clip in moved if moved[clip] != reexported[clip]} == {
        "anim_one",
        "anim_two",
    }


#: Each name read where Python reads it: the scope that binds it.
_SCOPES = {
    # A nested function imports the name for itself; the outer one reads the
    # module's.
    "nested-function": (
        "import json as _codec\n",
        "import marshal as _codec\n",
        "    def inner():\n        import pickle as _codec\n\n"
        "        return _codec.loads(s)\n\n    return _codec.dumps(inner)",
        {"anim_one", "anim_two"},
    ),
    # A class body imports the name; its methods read the module's, which a
    # function no clip reaches reads too (so it is no side effect).
    "class-body": (
        "import json as _codec\n",
        "import marshal as _codec\n",
        "    return _Codec().dump(s)\n\n\nclass _Codec:\n"
        "    import pickle as _codec\n\n    def dump(self, s):\n"
        "        return _codec.dumps(s)\n\n\ndef _unused():\n    return _codec.loads",
        {"anim_one", "anim_two"},
    ),
    # The module rebinds the name it imported.
    "rebound-at-the-top": (
        "import json as _codec\n\n_codec = _codec\n",
        "import marshal as _codec\n\n_codec = _codec\n",
        "    return _codec.dumps(s)",
        {"anim_one", "anim_two"},
    ),
    # A local variable of the same name reads nothing the import binds.
    "local-variable-of-the-same-name": (
        "import mpl_toolkits.mplot3d\n",
        "import mpl_toolkits.axisartist\n",
        "    mpl_toolkits = s\n    return mpl_toolkits",
        {"anim_one", "anim_two"},
    ),
    # ``global`` sends a function's assignment to the module, which then
    # binds the name twice: its import stays in the hash.
    "global": (
        "import json as _codec\n",
        "import marshal as _codec\n",
        "    global _codec\n    _codec = s\n    return _codec\n\n\n"
        "def _unused():\n    return _codec.loads",
        {"anim_one", "anim_two"},
    ),
    # An ``except ... as`` name is the exception, not the import. Here and in
    # the next two cases the import binds a name of the walk, which keeps no
    # effect of its own whether or not a clip reads it, so only a read that
    # took the local for the import would move.
    "except-as": (
        "from .theme import COLOR_PRIMARY as json\n",
        "from .theme import set_theme as json\n",
        "    try:\n        return s\n    except ValueError as json:\n"
        "        return json.args\n\n\ndef _unused():\n    return json.loads",
        set(),
    ),
    # A capture pattern binds the name it captures.
    "match-capture": (
        "from .theme import COLOR_PRIMARY as json\n",
        "from .theme import set_theme as json\n",
        "    match s:\n        case json:\n            return json.args\n\n\n"
        "def _unused():\n    return json.loads",
        set(),
    ),
    # A comprehension's first iterable is read where the comprehension
    # stands, before its own target binds the name.
    "comprehension-first-iterable": (
        "import json\n",
        "import pickle as json\n",
        "    return [json for json in json.loads(s)]\n\n\n"
        "def _unused():\n    return json.loads",
        {"anim_one", "anim_two"},
    ),
    # A default is read where the function is defined, not in its body.
    "parameter-default": (
        "import json\n",
        "import pickle as json\n",
        "    return _helper(s)\n\n\ndef _helper(s, json=json.dumps):\n"
        "    return json\n\n\ndef _unused():\n    return json.loads",
        {"anim_one", "anim_two"},
    ),
    # So is a decorator, before the parameter of the same name binds.
    "decorator": (
        "import json\n",
        "import pickle as json\n",
        "    return _helper(s)\n\n\n@json.loads\ndef _helper(json):\n"
        "    return json\n\n\ndef _unused():\n    return json.loads",
        {"anim_one", "anim_two"},
    ),
    # A comprehension's target stays inside it.
    "comprehension-target": (
        "import json\n",
        "import pickle as json\n",
        "    [json for json in (s,)]\n    return json.dumps(s)\n\n\n"
        "def _unused():\n    return json.loads",
        {"anim_one", "anim_two"},
    ),
    # A parameter of the same name is the argument, not the module.
    "parameter-of-the-same-name": (
        "from .theme import COLOR_PRIMARY as np\n",
        "from .theme import set_theme as np\n",
        "    return _helper(s)\n\n\ndef _helper(np):\n    return np.ones\n\n\n"
        "def _unused():\n    return np.zeros(1)",
        set(),
    ),
}


@pytest.mark.parametrize("case", sorted(_SCOPES))
def test_a_name_is_read_from_the_scope_that_binds_it(
    tree: pathlib.Path, case: str
) -> None:
    """An import binds its name in its own scope; a parameter or a local shadows it there."""
    header, changed, body, moves = _SCOPES[case]
    _write_media(tree, header, body)
    before = fp.fingerprints(tree)
    _write_media(tree, changed, body)
    after = fp.fingerprints(tree)
    assert {clip for clip in before if before[clip] != after[clip]} == moves


#: A name the top of a module binds under a condition, or more than once:
#: ``(top, changed top, body)``; the change moves both clips.
_REBINDINGS = {
    "try-and-its-handler": (
        'try:\n    _MODE = "fast"\nexcept Exception:\n    _MODE = "safe"\n',
        'try:\n    _MODE = "quick"\nexcept Exception:\n    _MODE = "safe"\n',
        "    return _MODE",
    ),
    "if-condition": (
        'import sys\n\nif sys.platform == "linux":\n    _MODE = "fast"\nelse:\n'
        '    _MODE = "safe"\n',
        'import sys\n\nif sys.platform != "linux":\n    _MODE = "fast"\nelse:\n'
        '    _MODE = "safe"\n',
        "    return _MODE",
    ),
    "twice-unguarded": (
        '_MODE = "fast"\n_FIRST = _MODE\n_MODE = "safe"\n',
        '_MODE = "quick"\n_FIRST = _MODE\n_MODE = "safe"\n',
        "    return _FIRST",
    ),
}


@pytest.mark.parametrize("case", sorted(_REBINDINGS))
def test_every_binding_of_a_name_bound_under_a_condition_or_twice_counts(
    tree: pathlib.Path, case: str
) -> None:
    """The walk reaches one binding of a name; the others, and what guards them, are hashed with the module."""
    top, changed, body = _REBINDINGS[case]
    _write_media(tree, top, body)
    before = fp.fingerprints(tree)
    _write_media(tree, changed, body)
    after = fp.fingerprints(tree)
    assert {clip for clip in before if before[clip] != after[clip]} == {
        "anim_one",
        "anim_two",
    }


#: A read edited to read something else at run time: ``(top, body, edited
#: body)``; the two must not hash alike.
_READS = {
    # A walrus target inside a comprehension binds in the function around it
    # (PEP 572), so ``_codec`` after it is that local, not the import.
    "walrus-in-a-comprehension": (
        "import json\nimport json as _codec\n",
        "    [(_codec := x) for x in (s,)]\n    return _codec.dumps(s)",
        "    [(_codec := x) for x in (s,)]\n    return json.dumps(s)",
    ),
    # A nested function's ``nonlocal`` assignment rebinds the outer import.
    "nonlocal": (
        "import json\n",
        "    import json as _codec\n\n    def inner():\n        nonlocal _codec\n"
        "        _codec = s\n\n    inner()\n    return _codec.dumps(s), _codec",
        "    import json as _codec\n\n    def inner():\n        nonlocal _codec\n"
        "        _codec = s\n\n    inner()\n    return json.dumps(s), _codec",
    ),
}


@pytest.mark.parametrize("case", sorted(_READS))
def test_a_read_edited_to_read_something_else_moves_its_clips(
    tree: pathlib.Path, case: str
) -> None:
    """Two reads that differ at run time never hash alike."""
    top, body, edited = _READS[case]
    _write_media(tree, top, body)
    before = fp.fingerprints(tree)
    _write_media(tree, top, edited)
    after = fp.fingerprints(tree)
    assert {clip for clip in before if before[clip] != after[clip]} == {
        "anim_one",
        "anim_two",
    }


#: What the top of a module the clips reach holds, beyond names bound once:
#: ``(top, changed top, body, clips that move)``.
_TOP_LEVEL = {
    # What a binding other than the last calls is walked.
    "def-in-a-try-and-its-handler": (
        "def _ha():\n    return 1\n\n\ndef _hb():\n    return 2\n\n\n"
        "try:\n    def _f():\n        return _ha()\nexcept Exception:\n"
        "    def _f():\n        return _hb()\n",
        "def _ha():\n    return 3\n\n\ndef _hb():\n    return 2\n\n\n"
        "try:\n    def _f():\n        return _ha()\nexcept Exception:\n"
        "    def _f():\n        return _hb()\n",
        "    return _f()",
        {"anim_one", "anim_two"},
    ),
    "assignment-in-a-try-and-its-handler": (
        "def _ha():\n    return 1\n\n\ndef _hb():\n    return 2\n\n\n"
        "try:\n    _MODE = _ha()\nexcept Exception:\n    _MODE = _hb()\n",
        "def _ha():\n    return 3\n\n\ndef _hb():\n    return 2\n\n\n"
        "try:\n    _MODE = _ha()\nexcept Exception:\n    _MODE = _hb()\n",
        "    return _MODE",
        {"anim_one", "anim_two"},
    ),
    "first-of-two-unguarded-assignments": (
        'def _ha():\n    return 1\n\n\n_MODE = _ha()\n_FIRST = _MODE\n_MODE = "b"\n',
        'def _ha():\n    return 3\n\n\n_MODE = _ha()\n_FIRST = _MODE\n_MODE = "b"\n',
        "    return _FIRST",
        {"anim_one", "anim_two"},
    ),
    # A ``def`` the walk takes by name with every other ``def`` of its name.
    "first-of-two-defs": (
        "def _ha():\n    return 1\n\n\ndef _f():\n    return _ha()\n\n\n"
        "_g = _f\n\n\ndef _f():\n    return 2\n",
        "def _ha():\n    return 3\n\n\ndef _f():\n    return _ha()\n\n\n"
        "_g = _f\n\n\ndef _f():\n    return 2\n",
        "    return _g()",
        {"anim_one", "anim_two"},
    ),
    # A walrus binds a second name in an assignment the walk takes by name.
    "walrus-in-an-assignment": (
        "def _ha():\n    return 1\n\n\n_A = (_B := _ha())\n",
        "def _ha():\n    return 3\n\n\n_A = (_B := _ha())\n",
        "    return _B",
        {"anim_one", "anim_two"},
    ),
    # The ``else`` of an ``if TYPE_CHECKING:`` block runs.
    "type-checking-else": (
        "from typing import TYPE_CHECKING\n\nif TYPE_CHECKING:\n"
        "    import json as _c\nelse:\n    import pickle as _c\n",
        "from typing import TYPE_CHECKING\n\nif TYPE_CHECKING:\n"
        "    import json as _c\nelse:\n    import marshal as _c\n",
        "    return _c",
        {"anim_one", "anim_two"},
    ),
    # Statements that bind no name the walk could reach, or bind it in a
    # form it does not model, are hashed as written.
    "subscript-assignment": (
        'import matplotlib.pyplot as plt\n\nplt.rcParams["lines.linewidth"] = 3\n',
        'import matplotlib.pyplot as plt\n\nplt.rcParams["lines.linewidth"] = 4\n',
        "    return s",
        {"anim_one", "anim_two"},
    ),
    "augmented-assignment": (
        "_X = 1\n_X += 1\n",
        "_X = 1\n_X += 2\n",
        "    return _X",
        {"anim_one", "anim_two"},
    ),
    "with-target": (
        "import os\n\nwith open(os.devnull) as _X:\n    pass\n",
        "import os\n\nwith open(os.curdir) as _X:\n    pass\n",
        "    return _X",
        {"anim_one", "anim_two"},
    ),
    "for-target": (
        "for _X in (1, 2):\n    pass\n",
        "for _X in (1, 3):\n    pass\n",
        "    return _X",
        {"anim_one", "anim_two"},
    ),
    "starred-assignment": (
        "_A, *_B = (1, 2, 3)\n",
        "_A, *_B = (1, 2, 4)\n",
        "    return _B",
        {"anim_one", "anim_two"},
    ),
    # A kind of statement the collector knows nothing of is hashed too, run
    # at import as it is, whether or not anything reads what it binds.
    "while-loop": (
        "while False:\n    _X = 1\n",
        "while False:\n    _X = 2\n",
        "    return s",
        {"anim_one", "anim_two"},
    ),
    "match-statement": (
        "match 1:\n    case _:\n        _X = 1\n",
        "match 1:\n    case _:\n        _X = 2\n",
        "    return s",
        {"anim_one", "anim_two"},
    ),
    # The statements are hashed in the order they stand.
    "line-order": (
        '_MODE = "a"\nprint(_MODE)\n_MODE = "b"\n',
        'print(_MODE)\n_MODE = "a"\n_MODE = "b"\n',
        "    return _MODE",
        {"anim_one", "anim_two"},
    ),
    # And the module's docstring is not among them.
    "docstring-of-a-module-with-a-rebound-name": (
        '"""The clip tail."""\n\n_MODE = "a"\n_MODE = "b"\n',
        '"""The clip tail, reworded."""\n\n_MODE = "a"\n_MODE = "b"\n',
        "    return _MODE",
        set(),
    ),
}


@pytest.mark.parametrize("case", sorted(_TOP_LEVEL))
def test_the_top_of_a_reached_module_is_hashed_beyond_the_names_it_binds_once(
    tree: pathlib.Path, case: str
) -> None:
    """Only a ``def``, a ``class``, a name assigned once and an import bound once are left to the walk.

    Every other statement at the top of a module a clip reaches is hashed as
    written, in the order it stands, and what it reads is walked; so is
    every statement that binds a name the walk reaches.
    """
    top, changed, body, moves = _TOP_LEVEL[case]
    _write_media(tree, top, body)
    before = fp.fingerprints(tree)
    _write_media(tree, changed, body)
    after = fp.fingerprints(tree)
    assert {clip for clip in before if before[clip] != after[clip]} == moves


@pytest.mark.parametrize(
    ("guard", "changed"),
    [
        ("except ImportError:", "except ImportError:"),
        ("except ImportError:", "except Exception:"),
    ],
    ids=["handler-target", "handler-type"],
)
def test_a_guarded_name_another_module_imports_is_hashed_where_it_is_guarded(
    tree: pathlib.Path, guard: str, changed: str
) -> None:
    """A re-export a guard decides is followed to its module, whose guard is hashed."""
    reexporter = tree / "scripts" / "figures" / "_ra.py"
    source = (
        "try:\n    from json import dumps as _x\n{guard}\n"
        "    from pickle import dumps as _x\n"
    )
    reexporter.write_text(source.format(guard=guard), encoding="utf-8")
    _write_media(tree, "from ._ra import _x\n", "    return _x(s)")
    before = fp.fingerprints(tree)
    text = source.format(guard=changed)
    if guard == changed:
        text = text.replace("from json import", "from marshal import")
    reexporter.write_text(text, encoding="utf-8")
    after = fp.fingerprints(tree)
    assert {clip for clip in before if before[clip] != after[clip]} == {
        "anim_one",
        "anim_two",
    }


@pytest.mark.parametrize(
    ("top", "moves"),
    [
        ('"""some other figure"""\n', set()),
        (
            'try:\n    _LABEL = "some other figure"\nexcept Exception:\n'
            '    _LABEL = ""\n',
            {"anim_one", "anim_two"},
        ),
    ],
    ids=["module-docstring", "statement-at-the-top"],
)
def test_the_strings_at_the_top_of_a_module_select_translations_but_its_docstring_does_not(
    tree: pathlib.Path, top: str, moves: set[str]
) -> None:
    """A string a statement at the top runs with may be drawn; the module's docstring is not."""
    _write_media(tree, top, "    return s")
    before = fp.fingerprints(tree)
    edit(tree, "i18n", "otra figura cualquiera", "otra figura")
    after = fp.fingerprints(tree)
    assert {clip for clip in before if before[clip] != after[clip]} == moves


#: An rcParam set at the top of a module: what every frame drawn after the
#: module is imported is drawn with.
_RC_PARAM = 'import matplotlib as _mpl\n\n_mpl.rcParams["lines.linewidth"] = WIDTH\n'

#: Modules whose top runs although the walk reads none of their names:
#: ``(files under scripts/figures, media's top, _translate_str's body)``.
#: ``WIDTH`` in a file is the value the test changes.
_RUN_ON_IMPORT = {
    # A clean re-export: the name passes through ``_ra``, whose top still runs.
    "clean-re-export": (
        {"_ra.py": _RC_PARAM + "from json import dumps as _x\n"},
        "from ._ra import _x\n",
        "    return _x(s)",
    ),
    # A package above a module the walk reaches runs first.
    "package-above-a-reached-module": (
        {"__init__.py": _RC_PARAM},
        "",
        "    return s",
    ),
    "subpackage-above-a-reached-module": (
        {
            "sub/__init__.py": _RC_PARAM,
            "sub/helper.py": "def _h(s):\n    return s\n",
        },
        "from .sub.helper import _h\n",
        "    return _h(s)",
    ),
    # A module a guarded import names, whatever binds the name.
    "guarded-import-of-a-module": (
        {"_rb.py": _RC_PARAM},
        "try:\n    from . import _rb\nexcept ImportError:\n    _rb = None\n",
        "    return s",
    ),
    # An import in a function the walk reaches runs when the function does.
    "import-in-a-reached-function": (
        {"_ra.py": _RC_PARAM + "from json import dumps as _x\n"},
        "",
        "    from ._ra import _x\n\n    return _x(s)",
    ),
}


def _write_figures(tree: pathlib.Path, files: dict[str, str], width: str) -> None:
    """Write *files* under the miniature's ``scripts/figures``, ``WIDTH`` read as *width*."""
    for name, source in files.items():
        path = tree / "scripts" / "figures" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source.replace("WIDTH", width), encoding="utf-8")


@pytest.mark.parametrize("case", sorted(_RUN_ON_IMPORT))
def test_the_top_of_a_module_that_runs_on_import_is_hashed_though_no_name_of_it_is_read(
    tree: pathlib.Path, case: str
) -> None:
    """A module Python runs for a clip counts, whether or not the walk reads a name of it.

    A package above a module the walk reaches, and a module an import the
    walk reaches names, a re-export's included: their tops run on import.
    """
    files, top, body = _RUN_ON_IMPORT[case]
    _write_media(tree, top, body)
    _write_figures(tree, files, "3")
    before = fp.fingerprints(tree)
    _write_figures(tree, files, "4")
    after = fp.fingerprints(tree)
    assert {clip for clip in before if before[clip] != after[clip]} == {
        "anim_one",
        "anim_two",
    }


#: What runs when a module is imported though the walk never reaches it, and
#: what does not: ``(top, changed top, body, clips that move)``.
_IMPORT_TIME = {
    # An assignment the walk would take by name, but whose value calls
    # something impure, runs on import whether or not its name is read.
    "impure-assignment-unread": (
        'import matplotlib.pyplot as plt\n\n_UNREAD = plt.rcParams.update({"lines.linewidth": 3})\n',
        'import matplotlib.pyplot as plt\n\n_UNREAD = plt.rcParams.update({"lines.linewidth": 4})\n',
        "    return s",
        {"anim_one", "anim_two"},
    ),
    "impure-assignment-read-only-by-unreached-code": (
        'import matplotlib.pyplot as plt\n\n_UNREAD = plt.rcParams.update({"lines.linewidth": 3})\n\n\n'
        "def _unreached():\n    return _UNREAD\n",
        'import matplotlib.pyplot as plt\n\n_UNREAD = plt.rcParams.update({"lines.linewidth": 4})\n\n\n'
        "def _unreached():\n    return _UNREAD\n",
        "    return s",
        {"anim_one", "anim_two"},
    ),
    "call-of-something-not-pure": (
        '_UNREAD = print("a")\n',
        '_UNREAD = print("b")\n',
        "    return s",
        {"anim_one", "anim_two"},
    ),
    "pure-constructor-unread": (
        'import re\n\n_PATTERN = re.compile("a")\n',
        'import re\n\n_PATTERN = re.compile("b")\n',
        "    return s",
        set(),
    ),
    "call-inside-a-lambda": (
        '_LATER = lambda: print("a")\n',
        '_LATER = lambda: print("b")\n',
        "    return s",
        set(),
    ),
    # What a def or a class the walk never reaches runs when it is defined.
    "decorator": (
        "import matplotlib as _mpl\n\n\ndef _set_width(width):\n"
        '    _mpl.rcParams["lines.linewidth"] = width\n    return lambda function: function\n\n\n'
        "@_set_width(3)\ndef _unreached():\n    return 1\n",
        "import matplotlib as _mpl\n\n\ndef _set_width(width):\n"
        '    _mpl.rcParams["lines.linewidth"] = width\n    return lambda function: function\n\n\n'
        "@_set_width(4)\ndef _unreached():\n    return 1\n",
        "    return s",
        {"anim_one", "anim_two"},
    ),
    "class-body": (
        'import matplotlib as _mpl\n\n\nclass _Unreached:\n    _mpl.rcParams["lines.linewidth"] = 3\n',
        'import matplotlib as _mpl\n\n\nclass _Unreached:\n    _mpl.rcParams["lines.linewidth"] = 4\n',
        "    return s",
        {"anim_one", "anim_two"},
    ),
    "pure-constructor-in-a-class-body": (
        'import re\n\n\nclass _Unreached:\n    _PATTERN = re.compile("a")\n',
        'import re\n\n\nclass _Unreached:\n    _PATTERN = re.compile("b")\n',
        "    return s",
        set(),
    ),
    "method-body": (
        "class _Unreached(dict):\n    def method(self):\n        return 1\n",
        "class _Unreached(dict):\n    def method(self):\n        return 2\n",
        "    return s",
        set(),
    ),
    "default-with-a-call": (
        "import matplotlib as _mpl\n\n\n"
        'def _unreached(width=_mpl.rcParams.update({"lines.linewidth": 3})):\n    return width\n',
        "import matplotlib as _mpl\n\n\n"
        'def _unreached(width=_mpl.rcParams.update({"lines.linewidth": 4})):\n    return width\n',
        "    return s",
        {"anim_one", "anim_two"},
    ),
    "keyword-only-default-with-a-call": (
        "def _unreached(*, width=max(3, 1)):\n    return width\n",
        "def _unreached(*, width=max(4, 1)):\n    return width\n",
        "    return s",
        {"anim_one", "anim_two"},
    ),
    "default-without-a-call": (
        "def _unreached(width=3):\n    return width\n",
        "def _unreached(width=4):\n    return width\n",
        "    return s",
        set(),
    ),
    # An import runs on import whether or not a reached statement reads it.
    "import-read-only-by-unreached-code": (
        "import mpl_toolkits.mplot3d\n\n\ndef _unreached():\n    return mpl_toolkits.mplot3d\n",
        "import mpl_toolkits.axisartist\n\n\ndef _unreached():\n    return mpl_toolkits.axisartist\n",
        "    return s",
        {"anim_one", "anim_two"},
    ),
    "alias-of-an-import-read-only-by-unreached-code": (
        "import matplotlib.pyplot as _a\n\n\ndef _unreached():\n    return _a\n",
        "import matplotlib.pyplot as _b\n\n\ndef _unreached():\n    return _b\n",
        "    return s",
        set(),
    ),
    # Only a third-party module keeps it: the standard library changes
    # nothing a frame is drawn with, and the library outside the walk is its
    # physics, which the walk does not follow.
    "standard-library-import-read-only-by-unreached-code": (
        "import json as _codec\n\n\ndef _unreached():\n    return _codec\n",
        "import pickle as _codec\n\n\ndef _unreached():\n    return _codec\n",
        "    return s",
        set(),
    ),
    "library-import-read-only-by-unreached-code": (
        "import phonometry.room as _library\n\n\ndef _unreached():\n    return _library\n",
        "import phonometry.building as _library\n\n\n"
        "def _unreached():\n    return _library\n",
        "    return s",
        set(),
    ),
}


@pytest.mark.parametrize("case", sorted(_IMPORT_TIME))
def test_what_a_module_runs_on_import_is_hashed_whether_or_not_the_walk_reaches_it(
    tree: pathlib.Path, case: str
) -> None:
    """A decorator, a base, a class body, a default that calls, an impure assignment and an import run on import.

    What runs only later (a function or a method body, a lambda's body) or
    builds a value and does nothing else (a pure constructor) is left to the
    walk, as is the name an import binds.
    """
    top, changed, body, moves = _IMPORT_TIME[case]
    _write_media(tree, top, body)
    before = fp.fingerprints(tree)
    _write_media(tree, changed, body)
    after = fp.fingerprints(tree)
    assert {clip for clip in before if before[clip] != after[clip]} == moves


#: A side-effect decorator factory and a metaclass factory for the cases below.
_SET_WIDTH = (
    "import matplotlib as _mpl\n\n\ndef _set_width(width):\n"
    '    _mpl.rcParams["lines.linewidth"] = width\n    return lambda function: function\n\n\n'
)

#: Definitions whose decorators, bases and keywords run nothing worth hashing,
#: and ones that do: ``(top, changed top, body, clips that move)``.
_DEFINITIONS = {
    "property-added-to-an-unreached-dataclass": (
        'import dataclasses\n\n\n@dataclasses.dataclass\nclass _Header:\n    name: str = ""\n',
        'import dataclasses\n\n\n@dataclasses.dataclass\nclass _Header:\n    name: str = ""\n\n'
        "    @property\n    def label(self):\n        return self.name\n",
        "    return s",
        set(),
    ),
    "attribute-docstring-reworded": (
        'import dataclasses\n\n\n@dataclasses.dataclass\nclass _Header:\n    name: str = ""\n'
        '    """What the header says."""\n',
        'import dataclasses\n\n\n@dataclasses.dataclass\nclass _Header:\n    name: str = ""\n'
        '    """What the header reads."""\n',
        "    return s",
        set(),
    ),
    "exception-class-added": (
        "",
        "class _ProbeError(ValueError):\n    pass\n",
        "    return s",
        set(),
    ),
    "property-setter-added": (
        "class _Unreached:\n    @property\n    def width(self):\n        return 1\n",
        "class _Unreached:\n    @property\n    def width(self):\n        return 1\n\n"
        "    @width.setter\n    def width(self, value):\n        pass\n",
        "    return s",
        set(),
    ),
    # An accessor of a name no ``property`` defines is no property's.
    "accessor-of-a-name-that-is-no-property": (
        "class _Unreached:\n    def width(self):\n        return 1\n",
        "class _Unreached:\n    def width(self):\n        return 1\n\n"
        "    @width.setter\n    def width(self, value):\n        pass\n",
        "    return s",
        {"anim_one", "anim_two"},
    ),
    # A module that rebinds ``property`` decorates with something else.
    "rebound-property": (
        "def _register(function):\n    return function\n\n\nproperty = _register\n\n\n"
        "class _Unreached:\n    pass\n",
        "def _register(function):\n    return function\n\n\nproperty = _register\n\n\n"
        "class _Unreached:\n    @property\n    def width(self):\n        return 1\n",
        "    return s",
        {"anim_one", "anim_two"},
    ),
    "inert-decorator-argument-changed": (
        "import functools\n\n\n@functools.lru_cache(maxsize=1)\ndef _unreached():\n    return 1\n",
        "import functools\n\n\n@functools.lru_cache(maxsize=2)\ndef _unreached():\n    return 1\n",
        "    return s",
        set(),
    ),
    "generic-base-added": (
        "from collections.abc import Mapping\n",
        "from collections.abc import Mapping\n\n\nclass _Table(Mapping[str, int]):\n    pass\n",
        "    return s",
        set(),
    ),
    "inert-decorator-called-with-something-impure": (
        _SET_WIDTH
        + "import functools\n\n\n@functools.lru_cache(maxsize=_set_width(3))\n"
        "def _unreached():\n    return 1\n",
        _SET_WIDTH
        + "import functools\n\n\n@functools.lru_cache(maxsize=_set_width(4))\n"
        "def _unreached():\n    return 1\n",
        "    return s",
        {"anim_one", "anim_two"},
    ),
    "decorator-of-the-walk-added": (
        "def _deco(function):\n    return function\n\n\ndef _unreached():\n    return 1\n",
        "def _deco(function):\n    return function\n\n\n@_deco\ndef _unreached():\n    return 1\n",
        "    return s",
        {"anim_one", "anim_two"},
    ),
    "base-defined-in-the-walk": (
        "class _Base:\n    def method(self):\n        return 1\n\n\n"
        "class _Unreached(_Base):\n    pass\n",
        "class _Base:\n    def method(self):\n        return 2\n\n\n"
        "class _Unreached(_Base):\n    pass\n",
        "    return s",
        {"anim_one", "anim_two"},
    ),
    "method-decorator-in-an-unreached-class": (
        _SET_WIDTH
        + "class _Unreached:\n    @_set_width(3)\n    def method(self):\n        return 1\n",
        _SET_WIDTH
        + "class _Unreached:\n    @_set_width(4)\n    def method(self):\n        return 1\n",
        "    return s",
        {"anim_one", "anim_two"},
    ),
    "class-keyword": (
        _SET_WIDTH + "class _Unreached(metaclass=_set_width(3)):\n    pass\n",
        _SET_WIDTH + "class _Unreached(metaclass=_set_width(4)):\n    pass\n",
        "    return s",
        {"anim_one", "anim_two"},
    ),
    "inert-metaclass-added": (
        "import abc\n\n\nclass _Unreached:\n    pass\n",
        "import abc\n\n\nclass _Unreached(metaclass=abc.ABCMeta):\n    pass\n",
        "    return s",
        set(),
    ),
}


@pytest.mark.parametrize("case", sorted(_DEFINITIONS))
def test_a_definition_is_hashed_with_its_module_only_for_what_it_runs(
    tree: pathlib.Path, case: str
) -> None:
    """A decorator, a base or a keyword that only shapes what it is given adds nothing; any other one counts.

    ``property``, ``dataclass``, ``lru_cache``, a builtin exception, a
    generic base and the like run nothing a frame is drawn with, so an
    inert edit to a class or a function no clip reaches moves nothing; a
    decorator, a base or a keyword of the walk, or one called with
    something impure, is hashed, and what it reads is walked.
    """
    top, changed, body, moves = _DEFINITIONS[case]
    _write_media(tree, top, body)
    before = fp.fingerprints(tree)
    _write_media(tree, changed, body)
    after = fp.fingerprints(tree)
    assert {clip for clip in before if before[clip] != after[clip]} == moves


#: An unread import of a module the clip's reached code imports anyway runs
#: nothing more: ``(top, changed top, body, clips that move)``.
_ALREADY_IMPORTED = {
    "read-at-the-top": (
        "from matplotlib import pyplot as plt\n",
        "from matplotlib import pyplot as plt\nimport matplotlib as _unread\n",
        "    return plt.title(s)",
        set(),
    ),
    "imported-by-a-reached-function": (
        "",
        "import matplotlib as _unread\n",
        "    from matplotlib import pyplot as _plt\n\n    return _plt.title(s)",
        set(),
    ),
    # An import under a condition may never run, at the top or in a
    # function the clip reaches, so it leaves the other one counting.
    "imported-only-under-a-try": (
        "try:\n    from matplotlib import pyplot as _plt\nexcept ImportError:\n    _plt = None\n",
        "try:\n    from matplotlib import pyplot as _plt\nexcept ImportError:\n    _plt = None\n"
        "import matplotlib as _unread\n",
        "    return s",
        {"anim_one", "anim_two"},
    ),
    "imported-only-under-an-if-in-a-reached-function": (
        "import mpl_toolkits.mplot3d\n",
        "",
        '    if s == "\\x00":\n        import mpl_toolkits.mplot3d\n    return s',
        {"anim_one", "anim_two"},
    ),
    "imported-only-under-a-with-in-a-reached-function": (
        "import contextlib\nimport mpl_toolkits.mplot3d\n",
        "import contextlib\n",
        "    with contextlib.suppress(ImportError):\n"
        "        import mpl_toolkits.mplot3d\n    return s",
        {"anim_one", "anim_two"},
    ),
    "imported-only-in-a-loop-in-a-reached-function": (
        "import mpl_toolkits.mplot3d\n",
        "",
        "    for _ in s:\n        import mpl_toolkits.mplot3d\n    return s",
        {"anim_one", "anim_two"},
    ),
    "imported-only-under-a-match-in-a-reached-function": (
        "import mpl_toolkits.mplot3d\n",
        "",
        '    match s:\n        case "x":\n            import mpl_toolkits.mplot3d\n    return s',
        {"anim_one", "anim_two"},
    ),
    # A function the reached one defines and calls runs with it.
    "imported-in-a-function-the-reached-one-defines-and-calls": (
        "import functools\nimport mpl_toolkits.mplot3d\n",
        "import functools\n",
        "    @functools.lru_cache(maxsize=1)\n    def _now():\n"
        "        import mpl_toolkits.mplot3d\n\n        return s\n\n    return _now()",
        set(),
    ),
    # A function the reached one only defines may never be called.
    "imported-only-in-a-function-the-reached-one-defines": (
        "import mpl_toolkits.mplot3d\n",
        "",
        "    def _later():\n        import mpl_toolkits.mplot3d\n\n    return s",
        {"anim_one", "anim_two"},
    ),
    # A module the reached code does not import still counts.
    "side-effect-import-beside-one-reached-code-reads": (
        "from matplotlib import pyplot as plt\n",
        "from matplotlib import pyplot as plt\nimport mpl_toolkits.mplot3d\n",
        "    return plt.title(s)",
        {"anim_one", "anim_two"},
    ),
    "submodule-the-reached-code-does-not-import": (
        "import numpy as np\n",
        "import numpy as np\nimport numpy.random as _unread\n",
        "    return np.sqrt(s)",
        {"anim_one", "anim_two"},
    ),
}


@pytest.mark.parametrize("case", sorted(_ALREADY_IMPORTED))
def test_an_unread_import_of_a_module_the_reached_code_imports_adds_nothing(
    tree: pathlib.Path, case: str
) -> None:
    """Every module an unread import imports, the code a clip reaches imports already, so the import runs nothing more."""
    top, changed, body, moves = _ALREADY_IMPORTED[case]
    _write_media(tree, top, body)
    before = fp.fingerprints(tree)
    _write_media(tree, changed, body)
    after = fp.fingerprints(tree)
    assert {clip for clip in before if before[clip] != after[clip]} == moves


#: Calls that only look pure, and imports that only look third-party:
#: ``(top, changed top, body, clips that move)``.
_LOOKALIKES = {
    # A keyword-only default of a lambda is evaluated where the lambda is.
    "lambda-keyword-only-default": (
        "import matplotlib.pyplot as plt\n\n"
        '_F = lambda *, x=plt.rcParams.update({"lines.linewidth": 3}): x\n',
        "import matplotlib.pyplot as plt\n\n"
        '_F = lambda *, x=plt.rcParams.update({"lines.linewidth": 4}): x\n',
        "    return s",
        {"anim_one", "anim_two"},
    ),
    # A builtin's name the module rebinds is not the builtin.
    "rebound-builtin": (
        _SET_WIDTH + "tuple = _set_width\n_X = tuple(3)\n",
        _SET_WIDTH + "tuple = _set_width\n_X = tuple(4)\n",
        "    return s",
        {"anim_one", "anim_two"},
    ),
    "rebound-module": (
        _SET_WIDTH + "import re\n\nre = _set_width\n_P = re.compile(3)\n",
        _SET_WIDTH + "import re\n\nre = _set_width\n_P = re.compile(4)\n",
        "    return s",
        {"anim_one", "anim_two"},
    ),
    # A name imported from the standard library is of the standard library.
    "name-from-the-standard-library-read-only-by-unreached-code": (
        "from json import dumps\n\n\ndef _unreached():\n    return dumps\n",
        "from pickle import dumps\n\n\ndef _unreached():\n    return dumps\n",
        "    return s",
        set(),
    ),
    # ``getattr`` is as pure as ``module.name`` only with a written name.
    "getattr-with-a-written-name": (
        'import json\n\n_DUMP = getattr(json, "dumps")\n',
        'import json\n\n_DUMP = getattr(json, "loads")\n',
        "    return s",
        set(),
    ),
    "getattr-with-a-name-read-from-elsewhere": (
        'import json\n\n_NAME = "dumps"\n_DUMP = getattr(json, _NAME)\n',
        'import json\n\n_NAME = "loads"\n_DUMP = getattr(json, _NAME)\n',
        "    return s",
        {"anim_one", "anim_two"},
    ),
}


@pytest.mark.parametrize("case", sorted(_LOOKALIKES))
def test_what_only_looks_pure_or_standard_is_read_for_what_it_is(
    tree: pathlib.Path, case: str
) -> None:
    """A lambda's keyword-only default runs where the lambda stands; a rebound builtin or module is not the original; ``getattr`` with a computed name is no plain read."""
    top, changed, body, moves = _LOOKALIKES[case]
    _write_media(tree, top, body)
    before = fp.fingerprints(tree)
    _write_media(tree, changed, body)
    after = fp.fingerprints(tree)
    assert {clip for clip in before if before[clip] != after[clip]} == moves


def test_the_standard_library_is_read_alike_on_every_supported_python() -> None:
    """The frozen names hold this interpreter's standard library and builtin exceptions, so no machine reads an import or a base otherwise."""
    import builtins

    exceptions = {
        name
        for name, value in vars(builtins).items()
        if isinstance(value, type)
        and issubclass(value, BaseException)
        and not name.startswith("_")
    }
    assert sys.stdlib_module_names - fp._STANDARD_LIBRARY == set()
    assert exceptions - fp._BUILTIN_EXCEPTIONS == set()


class _FakeMsvcrt:
    """Stand-in for Windows' :mod:`msvcrt`: refuses the first lock with EDEADLOCK."""

    LK_LOCK = 1
    LK_UNLCK = 0

    def __init__(self, refusals: int) -> None:
        self.refusals = refusals
        self.calls: list[int] = []

    def locking(self, fd: int, mode: int, nbytes: int) -> None:
        import errno

        assert nbytes == 1
        self.calls.append(mode)
        if mode == self.LK_LOCK and self.refusals:
            self.refusals -= 1
            raise OSError(errno.EDEADLOCK, "Resource deadlock avoided")


def test_the_stamp_lock_waits_out_a_busy_lock_on_windows_and_releases_it(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Off POSIX the manifest lock retries msvcrt's give-up and always unlocks."""
    fake = _FakeMsvcrt(refusals=2)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "msvcrt", fake)
    with fp._locked(tmp_path / "manifest.lock"):
        assert fake.calls == [fake.LK_LOCK] * 3
    assert fake.calls == [fake.LK_LOCK] * 3 + [fake.LK_UNLCK]


def test_the_stamp_lock_on_windows_raises_what_is_not_a_busy_lock(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A lock failure other than EDEADLOCK is not retried for ever."""
    import errno

    class _Denied(_FakeMsvcrt):
        def locking(self, fd: int, mode: int, nbytes: int) -> None:
            raise OSError(errno.EACCES, "Permission denied")

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "msvcrt", _Denied(refusals=0))
    with (
        pytest.raises(OSError, match="Permission denied"),
        fp._locked(tmp_path / "m.lock"),
    ):
        pass
