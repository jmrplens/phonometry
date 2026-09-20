#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The fork path of a clip render, which nothing else was exercising.

``scripts/figures/registry.py`` renders the four language and theme variants
of a clip two ways: one after another in this process, or, when the clip has a
registered field builder and the platform can fork, in four children that
share the field the parent computed. Only the second one is used for the
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
import pathlib
import sys
from typing import TYPE_CHECKING

import pytest

pytest.importorskip("matplotlib")
import matplotlib as mpl

mpl.use("Agg")

if TYPE_CHECKING:
    from collections.abc import Callable

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from figures import i18n, registry, theme  # noqa: E402

#: The four variants every clip is rendered in.
EXPECTED = (("en", False), ("en", True), ("es", False), ("es", True))


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
        monkeypatch.delitem(registry._ANIM_FIELDS, clip, raising=False)

    monkeypatch.setitem(registry._ANIMATIONS, clip, draw)
    registry._render_anim_variants(clip, str(tmp_path))

    if forkable:
        written = {path.name for path in tmp_path.iterdir()}
        assert written == {f"{lang}_{dark}" for lang, dark in EXPECTED}
    else:
        assert set(seen) == set(EXPECTED)
