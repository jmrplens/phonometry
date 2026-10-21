#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The fork path of a clip render, which nothing else was exercising.

``scripts/figures/registry.py`` renders the four language and theme variants
of a clip two ways: one after another in this process, or, when the platform
can fork, in four children, which share the field the parent computed when the
clip has a registered field builder. Only the second one is used for the
expensive clips, and only the first one was ever reached by a test.

They drifted. ``_render_anim_variant`` takes its ``dark`` flag keyword-only,
the way every boolean in this repository does, and the fork branch was passing
it positionally in ``Process(args=...)``. Nothing said so until a render was
asked for: the children raised ``TypeError`` inside ``multiprocessing``, the
parent saw four non-zero exit codes and reported "4 variant(s) failed", and
the clip that came out of it was the one already on disk.

So the test is the dispatch itself, with the drawing stubbed out: if the two
branches disagree about how the variant function is called, this fails in a
second rather than after a several-minute simulation.
"""

from __future__ import annotations

import multiprocessing as mp
import os
import pathlib
import sys
from typing import TYPE_CHECKING

import pytest

pytest.importorskip("matplotlib")
import matplotlib as mpl

mpl.use("Agg")

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from figures import i18n, registry, theme

# The figure, diagram and badge tooling is tied to the pinned figure stack its
# artefacts are drawn with, so the minimum-versions job deselects this module.
pytestmark = pytest.mark.pinned_stack

#: The four variants every clip is rendered in.
EXPECTED = (("en", False), ("en", True), ("es", False), ("es", True))


@pytest.fixture(autouse=True)
def _no_frames_to_judge(monkeypatch: pytest.MonkeyPatch) -> None:
    """The stand-in clips here draw no frames, so there is nothing to judge.

    A render inspects all four variants before it encodes any
    (``registry._audited_first``) and stops a clip whose variants left no
    record of an inspection. These stand-ins never reach ``_render_clip``,
    which is what writes one; what this module tests is where each variant
    is rendered, and ``tests/test_clip_frame_audit.py`` tests the verdict.
    """
    import clip_frame_audit

    monkeypatch.setattr(clip_frame_audit, "verdict", lambda directory, clip: None)


@pytest.fixture(autouse=True)
def _restore_language_and_theme() -> Iterator[None]:
    """Put the process back the way it was found.

    ``_render_anim_variant`` sets the language and the theme and never puts
    them back, which is right for it: the generator gives each variant a
    process, or ends the run. Called here it would leave the Spanish labels
    and the dark stylesheet in place for whatever test the worker picks up
    next, and the one that notices is a figure check measuring ink against a
    background that is suddenly black.
    """
    yield
    i18n.set_lang("en")
    theme.set_theme(dark=False)


def test_the_four_variants_are_the_ones_the_registry_lists() -> None:
    """The oracle of the two tests below, so neither can pass vacuously."""
    assert set(registry._VARIANTS) == set(EXPECTED)


def _variant() -> tuple[str, bool]:
    """The language and theme the drawing code would see right now."""
    return i18n._LANG, theme._FILENAME_SUFFIX == "_dark"


def _record(written: list[tuple[str, bool]]) -> Callable[[str], None]:
    """A stand-in for a clip that records the variant it was asked for."""

    def draw(_output_dir: str) -> None:
        written.append(_variant())

    return draw


@pytest.mark.parametrize("forkable", [False, True])
def test_both_branches_render_the_same_four_variants(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path, *, forkable: bool
) -> None:
    """Sequential and forked have to agree, because only one of them is used.

    The forked branch cannot report back through a list, so it writes a file
    per variant instead: what is asserted is that four children ran and none
    of them raised, which is exactly what the positional ``dark`` broke.
    """
    if forkable and "fork" not in mp.get_all_start_methods():
        pytest.skip("this platform cannot fork")

    clip = "test_only_clip"
    if forkable:

        def draw(output_dir: str) -> None:
            lang, dark = _variant()
            name = f"{lang}_{dark}"
            (pathlib.Path(output_dir) / name).write_text("", encoding="utf-8")

        monkeypatch.setitem(registry._ANIM_FIELDS, clip, lambda: None)
    else:
        seen: list[tuple[str, bool]] = []
        draw = _record(seen)
        monkeypatch.setattr(mp, "get_all_start_methods", lambda: ["spawn"])

    monkeypatch.setitem(registry._ANIMATIONS, clip, draw)
    registry._render_anim_variants(clip, str(tmp_path))

    if forkable:
        written = {path.name for path in tmp_path.iterdir()}
        assert written == {f"{lang}_{dark}" for lang, dark in EXPECTED}
    else:
        assert set(seen) == set(EXPECTED)


def test_a_clip_without_a_field_forks_its_variants_too(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Every render audits its frames first, so a schematic clip forks as well.

    Four variants in four processes is what keeps the frame audit from
    multiplying the wall time of a schematic clip's render by four; nothing
    is simulated first, because there is no field to share.
    """
    if "fork" not in mp.get_all_start_methods():
        pytest.skip("this platform cannot fork")
    clip = "test_only_schematic"
    parent = os.getpid()

    def draw(output_dir: str) -> None:
        lang, dark = _variant()
        forked = os.getpid() != parent
        (pathlib.Path(output_dir) / f"{lang}_{dark}_{forked}").write_text(
            "", encoding="utf-8"
        )

    monkeypatch.delitem(registry._ANIM_FIELDS, clip, raising=False)
    monkeypatch.setitem(registry._ANIMATIONS, clip, draw)
    registry._render_anim_variants(clip, str(tmp_path))
    written = {path.name for path in tmp_path.iterdir()}
    assert written == {f"{lang}_{dark}_True" for lang, dark in EXPECTED}


def test_every_cached_clip_field_is_registered() -> None:
    """A field cached inside its module but not registered is simulated once per variant.

    The variants fork, and a cache filled in a child dies with it: the banner's
    2.5 GB frame stack was being computed by each of the four children until
    its builder was registered, so the parent computes it once and they share
    it. Every cached ``_*_fields`` function of the field clips is registered.
    """
    import figures.fields

    registered = set(registry._ANIM_FIELDS.values())
    unregistered = sorted(
        f"{module.__name__}.{name}"
        for module in (
            sys.modules[name]
            for name in sorted(sys.modules)
            if name.startswith(f"{figures.fields.__name__}.")
        )
        for name, value in vars(module).items()
        if name.endswith("_fields")
        and hasattr(value, "cache_info")
        and value.__module__ == module.__name__
        and value not in registered
    )
    assert unregistered == []
