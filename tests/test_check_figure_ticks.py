#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The tick-label gate, measured on figures built to be measured.

``scripts/figure_tick_audit.py`` answers two questions about every axis of a
figure as it is saved: does it label its minor ticks in the scale's own
notation beside major ticks somebody set by hand, and do any two of the labels
it draws run into each other. Each figure below is one way of getting an
answer right or wrong, small enough that the expected answer is obvious by
construction: the band axis the gate was written for and its fix, the
helper the library already offers, matplotlib labelling a short log span on
its own, labels too close for their width, slanted labels whose boxes cross
where their words do not, the radial labels of a polar plot strung along one
ray, and a 3-D plate.

Then the property the design rests on: the measurement runs on the live
figure about to be written, so it must leave the written bytes alone.

``scripts/check_figure_ticks.py`` is the arithmetic on top: every recorded
hit fails, the recording has to cover the corpus in both languages, and the
command line refuses what it cannot answer about.
"""

from __future__ import annotations

import io
import json
import multiprocessing
import os
import pathlib
import sys
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest

pytest.importorskip("matplotlib")
import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_figure_annotations
import check_figure_ticks as check
import figure_tick_audit as audit

from phonometry._plot.common import format_frequency_axis

if TYPE_CHECKING:
    from collections.abc import Iterator

    from matplotlib.figure import Figure

#: The octave bands of EN 12354-6, the axis the gate was written for.
_BANDS = (125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0)
_BAND_LABELS = ("125", "250", "500", "1k", "2k", "4k", "8k")


@pytest.fixture(autouse=True)
def _isolate(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> Iterator[None]:
    """Stock matplotlib, recording on into this test's directory, empty tally.

    A test that reads where a label landed cannot share the rc a neighbour
    left behind: the font size and the figure size both move the answer.
    """
    monkeypatch.setenv(audit.AUDIT_ENV, str(tmp_path / "recording"))
    monkeypatch.setattr(audit, "_FOUND", {})
    with mpl.rc_context(mpl.rcParamsDefault):
        yield
    plt.close("all")


def _kinds(hits: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    """The recorded hits of one kind."""
    return [hit for hit in hits if hit["kind"] == kind]


def _band_axis(*, cleared: bool) -> Figure:
    """The reported figure in miniature: band labels set by hand on a log axis.

    The span holds exactly one decade boundary, which is what makes matplotlib
    label its minor ticks at 2, 3, 4 and 6 times the power of ten.
    """
    fig, ax = plt.subplots(figsize=(6.25, 5.4))
    ax.semilogx(_BANDS, np.linspace(0.0, 1.0, len(_BANDS)), marker="o")
    ax.set_xticks(_BANDS)
    ax.set_xticklabels(_BAND_LABELS)
    if cleared:
        ax.xaxis.set_minor_formatter(NullFormatter())
    return fig


# --------------------------------------------------------------------------
# Stray minor labels.


def test_band_labels_set_by_hand_on_a_log_axis_leave_stray_minor_labels() -> None:
    """The defect as it shipped: "2 × 10²50 4 × 10²500" under the band labels."""
    hits = audit.measure(_band_axis(cleared=False))

    (stray,) = _kinds(hits, audit.STRAY)
    assert stray["axis"] == "panel 1, x axis"
    assert "$\\mathdefault{2\\times10^{2}}$" in stray["labels"]
    assert "$\\mathdefault{3\\times10^{2}}$" in stray["labels"]
    overlaps = _kinds(hits, audit.OVERLAP)
    assert any("250" in hit["labels"] for hit in overlaps), (
        "the stray label at 200 Hz lands on the band label at 250 Hz"
    )


def test_clearing_the_minor_formatter_is_the_fix() -> None:
    """The same axis with the minor labels switched off measures clean."""
    assert audit.measure(_band_axis(cleared=True)) == []


def test_the_library_frequency_axis_is_clean() -> None:
    """``format_frequency_axis`` sets the majors by hand and clears the minors."""
    fig, ax = plt.subplots(figsize=(6.25, 5.4))
    ax.semilogx(_BANDS, np.linspace(0.0, 1.0, len(_BANDS)))
    format_frequency_axis(ax, _BANDS[0], _BANDS[-1])

    assert audit.measure(fig) == []


def test_a_major_formatter_set_by_hand_is_hand_set_too() -> None:
    """Taking over how the majors read is taking them over, like where they go."""
    fig, ax = plt.subplots(figsize=(6.25, 5.4))
    ax.semilogx(_BANDS, np.linspace(0.0, 1.0, len(_BANDS)))
    ax.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda v, _pos: f"{v:g}"))

    assert _kinds(audit.measure(fig), audit.STRAY)


def test_matplotlib_labelling_a_short_span_on_its_own_is_not_stray() -> None:
    """Under a decade, the scale labels its minor ticks by design.

    Nobody set the majors, so there is no hand-written scale for the minor
    labels to contradict: this is not the defect, and the overlap measure is
    what answers for it.
    """
    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    ax.semilogx([120.0, 900.0], [0.0, 1.0])

    drawn = audit._drawn_labels(fig)
    minors = [label for label in audit._labels_of(ax.xaxis, drawn) if label.minor]
    assert minors, "the premise: matplotlib does label these minor ticks"
    assert audit.measure(fig) == []


# --------------------------------------------------------------------------
# Overlaps.


def test_two_labels_too_close_for_their_width_overlap() -> None:
    """Hand-set labels on ticks closer together than the words are wide."""
    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    ax.set_xlim(0.0, 1.0)
    ax.set_xticks([0.40, 0.45], ["a long label", "another long label"])

    (hit,) = audit.measure(fig)

    assert hit["kind"] == audit.OVERLAP
    assert hit["labels"] == ["a long label", "another long label"]
    assert hit["depth_pt"] > 5.0


def test_the_same_labels_far_apart_do_not() -> None:
    """Moved to opposite ends of the axis, the same words clear each other."""
    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    ax.set_xlim(0.0, 1.0)
    ax.set_xticks([0.1, 0.9], ["a long label", "another long label"])

    assert audit.measure(fig) == []


def test_ordinary_stacked_labels_do_not_overlap() -> None:
    """A plain y axis, the most common axis in the corpus, measures clean."""
    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    ax.plot([0.0, 1.0], [-40.0, 40.0])

    assert audit.measure(fig) == []


def _slanted(count: int) -> Figure:
    """*count* long category labels turned 45 degrees along a 5 inch axis."""
    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    positions = np.arange(count)
    ax.bar(positions, np.ones(count))
    ax.set_xticks(positions, [f"category number {n}" for n in positions])
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    return fig


def test_slanted_labels_whose_boxes_cross_but_words_do_not_are_clean() -> None:
    """Measured in the labels' own frame, not by their page-aligned boxes.

    The page-aligned box of a label at 45 degrees is far larger than its
    letters, so on a category axis the boxes of neighbours cross where the
    words run parallel with room between them. The premise is checked on the
    boxes themselves, so the test cannot pass by the labels simply being far
    apart.
    """
    fig = _slanted(16)
    drawn = audit._drawn_labels(fig)
    labels = audit._labels_of(fig.axes[0].xaxis, drawn)
    one, other = labels[0], labels[1]
    boxes_cross = abs(other.centre[0] - one.centre[0]) < audit._page_size(one)[0]
    assert boxes_cross, "the premise: the page-aligned boxes do cross"

    assert audit.measure(fig) == []


def test_slanted_labels_packed_tighter_than_their_height_overlap() -> None:
    """The same axis with its words closer than a line apart does overlap."""
    hits = audit.measure(_slanted(60))

    assert _kinds(hits, audit.OVERLAP)


def _dipole(*, every_other: bool) -> Figure:
    """The horizontal dipole of CNOSSOS-EU, its rings labelled along one ray."""
    fig = plt.figure(figsize=(6.0, 6.0))
    ax: Any = fig.add_subplot(projection="polar")
    phi = np.radians(np.linspace(0.0, 360.0, 361))
    ax.plot(phi, 10.0 * np.log10(0.01 + 0.99 * np.sin(phi) ** 2))
    rings = np.arange(-20.0, 0.1, 2.5)
    if every_other:
        ax.set_rgrids(
            rings, [f"{r:.1f}" if i % 2 == 0 else "" for i, r in enumerate(rings)]
        )
    else:
        ax.set_rgrids(rings)
    return fig


def test_radial_labels_strung_along_one_ray_overlap() -> None:
    """Nine labels on the 22.5 degree ray, each running into the next."""
    hits = audit.measure(_dipole(every_other=False))

    overlaps = _kinds(hits, audit.OVERLAP)
    assert overlaps
    assert {hit["axis"] for hit in overlaps} == {"panel 1, y axis"}


def test_a_label_on_every_other_ring_clears_them() -> None:
    """The rings stay; the labels that remain are far enough apart to read."""
    assert audit.measure(_dipole(every_other=True)) == []


def test_a_label_outside_the_view_is_not_measured() -> None:
    """Only what the draw reached: a tick past the limits draws nothing."""
    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    ax.set_xticks([0.5, 5.0, 5.01], ["inside", "outside", "also outside"])
    ax.set_xlim(0.0, 1.0)

    assert audit.measure(fig) == []


def test_an_inset_is_an_axes_the_figure_does_not_list() -> None:
    """``inset_axes`` files its panel under the host, and it is measured all the same."""
    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    inset = ax.inset_axes((0.5, 0.5, 0.4, 0.4))
    inset.set_xlim(0.0, 1.0)
    inset.set_xticks([0.40, 0.45], ["a long label", "another long label"])
    assert inset not in fig.axes

    (hit,) = audit.measure(fig)

    assert hit["axis"] == "panel 2, x axis"


def test_a_three_dimensional_plate_is_measured_where_it_is_drawn() -> None:
    """A 3-D axis projects its labels inside its own draw; they are captured there."""
    fig = plt.figure(figsize=(6.4, 4.8))
    ax: Any = fig.add_subplot(projection="3d")
    ax.plot([0.0, 1.0], [0.0, 1.0], [0.0, 1.0])

    drawn = audit._drawn_labels(fig)
    width, height = fig.bbox.width, fig.bbox.height
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        labels = audit._labels_of(axis, drawn)
        assert labels
        for label in labels:
            x, y = label.centre
            assert 0.0 <= x <= width
            assert 0.0 <= y <= height
    assert audit.measure(fig) == []


def test_the_measurement_leaves_the_written_file_alone() -> None:
    """It runs on the figure about to be saved, so it must not move a byte."""

    def written(fig: Figure) -> bytes:
        buffer = io.BytesIO()
        fig.savefig(buffer, format="svg", metadata={"Date": None})
        return buffer.getvalue()

    with mpl.rc_context({"svg.hashsalt": "phonometry"}):
        fig = _dipole(every_other=False)
        before = written(fig)
        audit.measure(fig)
        after = written(fig)

    assert before == after


def test_the_spanish_pass_is_measured_and_says_so(tmp_path: pathlib.Path) -> None:
    """Measured through the saver, on both light passes and never the dark one."""
    from figures import i18n, theme

    saved = dict(mpl.rcParams)
    try:
        for lang, dark in (("en", False), ("es", False), ("es", True)):
            i18n.set_lang(lang)
            theme.set_theme(dark=dark)
            fig = _band_axis(cleared=False)
            theme.save_figure(str(tmp_path), "probe.svg")
            plt.close(fig)
    finally:
        i18n.set_lang("en")
        theme.set_theme(dark=False)
        mpl.rcParams.update(saved)

    assert _kinds(audit._FOUND["probe"], audit.STRAY)
    assert _kinds(audit._FOUND["probe_es"], audit.STRAY)
    assert "probe_es_dark" not in audit._FOUND, "the dark twin is the same drawing"


def test_recording_is_off_unless_asked_for(monkeypatch: pytest.MonkeyPatch) -> None:
    """A plain generation run measures nothing and writes nothing."""
    monkeypatch.delenv(audit.AUDIT_ENV)

    audit.audit(_band_axis(cleared=False), "probe")

    assert audit._FOUND == {}


def test_a_clean_drawing_is_recorded_as_drawn() -> None:
    """An empty list is how the checker tells "clean" from "never drawn"."""
    audit.audit(_band_axis(cleared=True), "probe")

    assert audit._FOUND == {"probe": []}


def _record_in_child(key: str) -> None:
    """A forked child's whole job: measure one figure and exit normally."""
    audit.audit(plt.figure(), key)


@pytest.mark.skipif(
    "fork" not in multiprocessing.get_all_start_methods(),
    reason="the inherited state this pins exists only where os.fork does",
)
def test_a_child_forked_after_the_parent_recorded_still_writes_its_own_fragment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A fork child records for itself, and only what it measured."""
    directory = pathlib.Path(os.environ[audit.AUDIT_ENV])
    monkeypatch.setattr(audit, "_REGISTERED", False)
    audit.audit(plt.figure(), "drawn_in_the_parent")
    assert audit._REGISTERED

    child = multiprocessing.get_context("fork").Process(
        target=_record_in_child, args=("drawn_in_the_child",)
    )
    child.start()
    child.join()

    assert child.exitcode == 0
    fragment = directory / f"{child.pid}.json"
    assert json.loads(fragment.read_text(encoding="utf-8")) == {
        "drawn_in_the_child": []
    }


# --------------------------------------------------------------------------
# The checker.


def _overlap(depth: float, *labels: str) -> dict[str, Any]:
    """One recorded overlap, as a fragment on disk holds it."""
    return {
        "kind": audit.OVERLAP,
        "axis": "panel 1, x axis",
        "labels": list(labels or ("250", "300")),
        "depth_pt": depth,
    }


def _stray(*labels: str) -> dict[str, Any]:
    """One recorded axis of stray minor labels."""
    return {
        "kind": audit.STRAY,
        "axis": "panel 1, x axis",
        "labels": list(labels or ("$\\mathdefault{2\\times10^{2}}$",)),
    }


def _fragment(
    directory: pathlib.Path, hits: dict[str, Any], name: str = "1.json"
) -> pathlib.Path:
    """A recording directory holding one fragment of *hits*, keyed by drawing."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(json.dumps(hits), encoding="utf-8")
    return directory


def test_a_clean_recording_passes(capsys: pytest.CaptureFixture[str]) -> None:
    """Every drawing measured and nothing found."""
    assert check.report({"probe": [], "probe_es": []}) == 0
    assert "No axis runs its tick labels together" in capsys.readouterr().out


def test_a_stray_label_fails_even_where_it_touches_nothing(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The labels nobody asked for are the defect, touching or not."""
    assert check.report({"probe": [_stray()]}) == 1
    printed = capsys.readouterr().out
    assert "::error::tick labels on a figure run into each other" in printed
    assert "set_minor_formatter(NullFormatter())" in printed
    assert "format_frequency_axis" in printed


def test_the_shallowest_overlap_on_record_fails(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Touching boxes are set as closely as the letters of one word."""
    assert check.report({"probe": [_overlap(0.01, "−10", "−15")]}) == 1
    printed = capsys.readouterr().out
    assert 'probe: panel 1, x axis: "−10", "−15" (0.01 pt)' in printed


def test_fragments_merge_keeping_each_hit_once_and_the_deeper_overlap(
    tmp_path: pathlib.Path,
) -> None:
    """A drawing measured twice can only be reported worse, never better."""
    directory = _fragment(tmp_path / "rec", {"probe": [_overlap(1.0), _stray()]})
    _fragment(directory, {"probe": [_overlap(2.5), _stray()]}, "2.json")

    merged = audit.load(str(directory))

    assert len(merged["probe"]) == 2
    assert _kinds(merged["probe"], audit.OVERLAP)[0]["depth_pt"] == 2.5


def test_no_recording_at_all_is_refused(
    capsys: pytest.CaptureFixture[str], tmp_path: pathlib.Path
) -> None:
    """The check answers about a generation run, so with none it says so."""
    assert check.main(["--audit", str(tmp_path / "never-written")]) == 1
    assert "no tick-label recording" in capsys.readouterr().out

    (tmp_path / "empty").mkdir()
    assert check.main(["--audit", str(tmp_path / "empty")]) == 1
    assert "no tick-label recording" in capsys.readouterr().out


def test_a_run_that_drew_only_some_figures_is_refused_without_the_flag(
    capsys: pytest.CaptureFixture[str], tmp_path: pathlib.Path
) -> None:
    """The recording has to cover every committed drawing in both languages."""
    directory = _fragment(tmp_path / "rec", {"g_weighting_response": []})

    assert check.main(["--audit", str(directory)]) == 1
    printed = capsys.readouterr().out
    assert "is not a full run" in printed
    assert "make graphs" in printed


def test_the_same_partial_run_is_accepted_with_the_flag(
    capsys: pytest.CaptureFixture[str], tmp_path: pathlib.Path
) -> None:
    """``--partial`` is for a run of some figures only: it checks what that run drew."""
    directory = _fragment(tmp_path / "rec", {"g_weighting_response": []})

    assert check.main(["--audit", str(directory), "--partial"]) == 0
    assert "No axis runs its tick labels together" in capsys.readouterr().out


def test_a_full_run_is_accepted_and_one_fragment_short_is_not(
    capsys: pytest.CaptureFixture[str], tmp_path: pathlib.Path
) -> None:
    """Coverage is what stands between a lost fragment and a green gate."""
    drawings = sorted(check_figure_annotations.committed_figures())
    assert "enclosed_space_absorption" in drawings
    assert "enclosed_space_absorption_es" in drawings
    half = len(drawings) // 2
    directory = tmp_path / "rec"
    _fragment(directory, dict.fromkeys(drawings[:half], []))
    _fragment(directory, dict.fromkeys(drawings[half:], []), "2.json")

    assert check.main(["--audit", str(directory)]) == 0
    capsys.readouterr()

    (directory / "2.json").unlink()

    assert check.main(["--audit", str(directory)]) == 1
    assert "is not a full run" in capsys.readouterr().out


def test_the_command_fails_on_the_reported_figure_and_names_it(
    capsys: pytest.CaptureFixture[str], tmp_path: pathlib.Path
) -> None:
    """The whole point, driven the way CI drives it, on the measured figure."""
    audit.audit(_band_axis(cleared=False), "enclosed_space_absorption")
    directory = tmp_path / "rec"
    _fragment(directory, audit._FOUND)

    assert check.main(["--audit", str(directory), "--partial"]) == 1
    printed = capsys.readouterr().out
    assert "enclosed_space_absorption: panel 1, x axis" in printed
    assert "beside major ticks set by hand" in printed
    assert "draw two tick labels into each other" in printed
