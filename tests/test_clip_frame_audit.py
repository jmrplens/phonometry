#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every frame of a clip is held to the gates the figures are held to.

``scripts/clip_frame_audit.py`` draws each frame of a clip as the SVG the
figures are saved as, and runs the figure gates on it before a byte is
encoded. These tests show it failing where it must: on a label a line strikes
through, on the frame where that happens and no other; on the real defect it
was written for, the EPNL flyover's microphone label put back under the ground
line; and before the encoder is ever called. They also pin what makes the
frames it reads the frames the encoder gets: the animation's own order, and a
render process the audit leaves exactly as it found it.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import textwrap
from typing import TYPE_CHECKING

import pytest

pytest.importorskip("matplotlib")
import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import check_figure_decimal_point as decimal_point
import check_figure_legends as legends
import check_figure_minus_sign as minus_sign
import check_figure_text_clearance as text_clearance
import clip_frame_audit as cfa
from figures import media, registry

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from matplotlib.artist import Artist
    from matplotlib.figure import Figure

# The figure, diagram and badge tooling is tied to the pinned figure stack its
# artefacts are drawn with, so the minimum-versions job deselects this module.
# A test that stands in for the encoder never renders the animation it is
# handed, and matplotlib says so when that animation is collected.
pytestmark = [
    pytest.mark.pinned_stack,
    # The audit draws the frames in a forked copy of the render process and
    # refuses to run where it cannot fork, which the last test here checks on
    # a platform that can.
    pytest.mark.skipif(
        not hasattr(os, "fork"), reason="the frame audit runs only where os.fork does"
    ),
    pytest.mark.filterwarnings(
        "ignore:Animation was deleted without rendering anything:UserWarning"
    ),
]

#: Frames in the synthetic clips: enough for a run in the middle of the clip.
FRAMES = 10


@pytest.fixture(autouse=True)
def _render_mode(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Every test starts in a render, not an audit-only run, and closes its figures."""
    from figures import i18n, theme

    for name in (cfa.AUDIT_ENV, cfa.GATE_ENV, cfa.AUDITED_ENV):
        monkeypatch.delenv(name, raising=False)
    yield
    plt.close("all")
    # A render through the pool path sets the language and the theme of
    # this process and never puts them back; the next test reads ink against
    # the page it finds.
    i18n.set_lang("en")
    theme.set_theme(dark=False)


def _clip(
    *,
    strike_at: tuple[int, ...] = (),
    text: str = "microphone",
    log: pathlib.Path | None = None,
    color: str = "black",
) -> tuple[Figure, Callable[[int], tuple[Artist, ...]]]:
    """A clip whose line runs through its label on the frames in *strike_at*.

    The line rests along the top of the panel and drops onto the middle of
    the label's line on those frames, so the text clearance gate reads a
    stroke run across the label there and nowhere else. With *log*, the
    update appends every frame it is asked for to that file, one per line,
    so the order survives the copy of the process the audit draws in. The
    line is black unless *color* says otherwise, which the dark page reads
    as a faint stroke.
    """
    fig = plt.figure(figsize=(4.0, 3.0))
    ax = fig.add_subplot()
    ax.set_xlim(0.0, 10.0)
    ax.set_ylim(0.0, 10.0)
    ax.text(2.0, 5.0, text, fontsize=10, va="center")
    (line,) = ax.plot([0.0, 10.0], [9.0, 9.0], color=color, lw=1.2)

    def update(frame: int) -> tuple[Artist, ...]:
        if log is not None:
            with log.open("a", encoding="utf-8") as handle:
                handle.write(f"{frame}\n")
        y = 5.0 if frame in strike_at else 9.0
        line.set_ydata([y, y])
        return (line,)

    return fig, update


def _audit(
    fig: Figure,
    update: Callable[[int], tuple[Artist, ...]],
    *,
    clip: str = "anim_struck",
    language: str = "en",
    dark: bool = False,
) -> None:
    cfa.audit(
        fig,
        update,
        clip,
        frames=FRAMES,
        interval_ms=50.0,
        language=language,
        dark=dark,
    )


def _audit_only(
    monkeypatch: pytest.MonkeyPatch,
    directory: pathlib.Path,
    fig: Figure,
    update: Callable[[int], tuple[Artist, ...]],
    **variant: object,
) -> dict[str, object]:
    """Audit one variant the way ``--audit-only`` does and return what it wrote."""
    monkeypatch.setenv(cfa.AUDIT_ENV, str(directory))
    _audit(fig, update, **variant)  # type: ignore[arg-type]
    (fragment,) = directory.glob("*.json")
    return json.loads(fragment.read_text(encoding="utf-8"))


# -- the finding -------------------------------------------------------------


def test_a_line_struck_through_a_label_stops_the_render_on_that_frame() -> None:
    fig, update = _clip(strike_at=(4, 5))
    with pytest.raises(
        cfa.ClipFrameError, match=r"anim_struck \[en light\] frame 4 "
    ) as caught:
        _audit(fig, update)
    message = str(caught.value)
    assert "text clearance" in message
    assert "'microphone'" in message
    assert "this variant was not encoded" in message


def test_a_clip_whose_frames_are_clear_passes() -> None:
    fig, update = _clip()
    _audit(fig, update)


def test_a_platform_that_cannot_fork_is_refused_before_a_frame_is_drawn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Drawing the frames in this process would leave the clip on its last frame."""
    monkeypatch.delattr(os, "fork")
    fig, update = _clip()
    with pytest.raises(RuntimeError, match=r"the clip frame audit needs os\.fork"):
        _audit(fig, update)


def test_every_frame_is_inspected_and_the_run_names_the_frames_it_holds_over(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Not sampled: a strike on two frames out of ten is found on exactly those two."""
    fig, update = _clip(strike_at=(4, 5))
    result = _audit_only(monkeypatch, tmp_path, fig, update)
    assert result["seen"] == FRAMES
    (run,) = result["runs"]  # type: ignore[misc]
    assert run["gate"] == cfa.TEXT
    assert run["frames"] == [[4, 5]]
    assert run["exempt_by"] is None


def test_a_frame_drawn_like_the_one_before_it_is_not_measured_again(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """A still clip is one drawing measured once, and every frame still answers for it."""
    fig, update = _clip()
    result = _audit_only(monkeypatch, tmp_path, fig, update)
    assert result["seen"] == FRAMES
    assert result["inspected"] == 1


# -- the real defect -----------------------------------------------------------

#: The microphone label of the EPNL flyover clip as it shipped: centred under
#: the microphone, its baseline below the ground line drawn at y = 0.30, so the
#: line ran through its letters.
_OLD_MICROPHONE_LABEL = """    ax_v.text(
        2.35,
        0.05,
        T("microphone"),
        ha="center",
        va="bottom","""

_MICROPHONE_LABEL = re.compile(
    r"    ax_v\.text\(\n        [\d.]+,\n        [\d.]+,\n"
    r'        T\("microphone"\),\n        ha="\w+",\n        va="\w+",'
)

_RUN_EPNL = textwrap.dedent(
    """
    import sys
    sys.path[:0] = [sys.argv[1], sys.argv[2]]
    import figures
    assert figures.__file__.startswith(sys.argv[1]), figures.__file__
    import clip_frame_audit
    from figures import i18n, media, schematics, theme

    def encode(*args, **kwargs):
        raise SystemExit("the clip reached the encoder")

    media._save_animation = encode
    i18n.set_lang("en")
    theme.set_theme(dark=False)
    try:
        schematics.animate_epnl_flyover(sys.argv[3])
    except clip_frame_audit.ClipFrameError as error:
        print(error)
    else:
        raise SystemExit("the clip passed")
    """
)


def test_the_epnl_microphone_label_under_the_ground_line_fails(
    tmp_path: pathlib.Path,
) -> None:
    """The defect found by eye, put back in a copy of the clip code, is found by the audit."""
    copy = tmp_path / "scripts"
    shutil.copytree(_SCRIPTS / "figures", copy / "figures")
    schematics = copy / "figures" / "schematics.py"
    source, count = _MICROPHONE_LABEL.subn(
        _OLD_MICROPHONE_LABEL, schematics.read_text(encoding="utf-8")
    )
    assert count == 1, "the EPNL microphone label is no longer where this test looks"
    schematics.write_text(source, encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    env = {**os.environ, "PYTHONPATH": str(_ROOT / "src"), "MPLBACKEND": "Agg"}
    env.pop(cfa.AUDIT_ENV, None)
    done = subprocess.run(
        [sys.executable, "-c", _RUN_EPNL, str(copy), str(_SCRIPTS), str(out)],
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=600,
    )
    assert done.returncode == 0, done.stderr[-2000:]
    headline = next(
        line
        for line in done.stdout.splitlines()
        if line.startswith("anim_epnl_flyover [")
    )
    assert headline.startswith("anim_epnl_flyover [en light] frame 0 of 0-"), (
        done.stdout
    )
    assert "'microphone'" in done.stdout
    assert "text clearance" in done.stdout
    assert list(out.iterdir()) == []


# -- before the encoder, and without touching what it encodes -------------------


def test_render_clip_refuses_before_anything_is_encoded(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    encoded: list[str] = []
    monkeypatch.setattr(
        media, "_save_animation", lambda *args, **kwargs: encoded.append("encoded")
    )
    fig, update = _clip(strike_at=(7,))
    with pytest.raises(cfa.ClipFrameError, match=r"anim_struck \[en light\] frame 7 "):
        media._render_clip(fig, update, str(tmp_path), "anim_struck", frames=FRAMES)
    assert encoded == []
    assert list(tmp_path.iterdir()) == []


def test_render_clip_encodes_a_clip_whose_frames_pass(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    encoded: list[int] = []

    def save(
        anim: object, fig: Figure, output_dir: str, stem: str, **kwargs: object
    ) -> None:
        del anim, fig, output_dir, stem
        encoded.append(int(kwargs["fps"]))  # type: ignore[call-overload]

    monkeypatch.setattr(media, "_save_animation", save)
    fig, update = _clip()
    media._render_clip(fig, update, str(tmp_path), "anim_clear", frames=FRAMES)
    assert encoded == [media._ANIM_FPS]


def test_the_frames_are_inspected_in_the_order_the_animation_draws_them(
    tmp_path: pathlib.Path,
) -> None:
    """The opening draw, then every frame once and in turn, as the encoder asks for them."""
    log = tmp_path / "calls.txt"
    fig, update = _clip(log=log)
    _audit(fig, update)
    calls = [int(line) for line in log.read_text(encoding="utf-8").split()]
    assert calls == [0, *range(FRAMES)]


def test_the_audit_leaves_the_render_process_as_it_found_it(
    tmp_path: pathlib.Path,
) -> None:
    """Every update ran in the copy: this process never moved past its first state."""
    log = tmp_path / "calls.txt"
    fig, update = _clip(strike_at=(3,), log=log)
    (line,) = fig.axes[0].lines
    before = line.get_ydata().tolist()  # type: ignore[union-attr]
    artists = len(fig.axes[0].get_children())
    with pytest.raises(cfa.ClipFrameError, match=r"frame 3 "):
        _audit(fig, update)
    assert line.get_ydata().tolist() == before  # type: ignore[union-attr]
    assert len(fig.axes[0].get_children()) == artists
    assert log.read_text(encoding="utf-8").split() == ["0", "0", "1", "2", "3"]


def test_an_update_that_fails_in_the_copy_is_reported_rather_than_passed() -> None:
    fig, update = _clip()

    def broken(frame: int) -> tuple[Artist, ...]:
        if frame == 3:
            msg = "the field ran out"
            raise IndexError(msg)
        return update(frame)

    with pytest.raises(cfa.ClipFrameError, match=r"could not finish"):
        _audit(fig, broken)


# -- the gates of each variant -------------------------------------------------


def test_a_spanish_frame_is_read_for_its_decimal_comma(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    fig, update = _clip(text="0.5")
    result = _audit_only(monkeypatch, tmp_path, fig, update, language="es")
    gates = {run["gate"] for run in result["runs"]}  # type: ignore[attr-defined]
    assert gates == {cfa.DECIMAL}


def test_a_number_signed_with_a_hyphen_is_found(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    fig, update = _clip(text="-3 dB")
    result = _audit_only(monkeypatch, tmp_path, fig, update)
    gates = {run["gate"] for run in result["runs"]}  # type: ignore[attr-defined]
    assert gates == {cfa.MINUS}


def test_a_dark_frame_is_read_for_its_page_and_not_again_for_its_geometry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """The struck label is the light frame's to report; the faint stroke the dark one's."""
    from figures import theme

    # Drawn on the dark page, as the renderer draws a dark variant: the
    # stroke is read against the page the frame paints.
    theme.set_theme(dark=True)
    fig, update = _clip(strike_at=(2,), color="white")
    fig.axes[0].plot([0.0, 10.0], [1.0, 1.0], color="#20252b", lw=1.0)
    result = _audit_only(monkeypatch, tmp_path, fig, update, dark=True)
    gates = {run["gate"] for run in result["runs"]}  # type: ignore[attr-defined]
    assert gates == {cfa.STROKE}


def test_a_stroke_that_fades_frame_by_frame_is_one_finding(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """A trail dimmed a little more on every frame is one run, not one per opacity."""
    from figures import theme

    theme.set_theme(dark=True)
    fig, update = _clip(color="white")
    (trail,) = fig.axes[0].plot([0.0, 10.0], [1.0, 1.0], color="#7e57c2", lw=2.0)

    def fading(frame: int) -> tuple[Artist, ...]:
        trail.set_alpha(0.5 - 0.02 * frame)
        return (*update(frame), trail)

    result = _audit_only(monkeypatch, tmp_path, fig, fading, dark=True)
    (run,) = (
        run
        for run in result["runs"]  # type: ignore[attr-defined]
        if "#7e57c2" in run["detail"]
    )
    assert run["gate"] == cfa.STROKE
    assert run["frames"] == [[0, FRAMES - 1]]


# -- exemptions ------------------------------------------------------------------


def test_an_exemption_keyed_by_the_clip_lets_its_finding_through(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        text_clearance, "EXEMPTIONS", {"anim_struck: microphone": "a test decision"}
    )
    fig, update = _clip(strike_at=(4,))
    _audit(fig, update)


def _fragments(directory: pathlib.Path, clip: str, exempt_by: str | None) -> None:
    """Four clean variants of *clip*, as an audit-only run leaves them."""
    for language, dark in cfa.VARIANTS:
        runs = (
            [
                {
                    "gate": cfa.TEXT,
                    "detail": "d",
                    "exempt_by": exempt_by,
                    "frames": [[1, 1]],
                }
            ]
            if exempt_by and not dark
            else []
        )
        fragment = {
            "frames": 3,
            "seen": 3,
            "inspected": 3,
            "failed_at": None,
            "runs": runs,
        }
        name = cfa.drawing_name(clip, language, dark=dark)
        (directory / f"{name}.json").write_text(json.dumps(fragment), encoding="utf-8")


def test_a_clip_exemption_that_still_fires_passes_the_report(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(text_clearance, "EXEMPTIONS", {"anim_kept": "a decision"})
    _fragments(
        tmp_path, "anim_kept", "check_figure_text_clearance.EXEMPTIONS: anim_kept"
    )
    assert cfa.report(tmp_path, ["anim_kept"]) == 0
    assert "passes the figure gates" in capsys.readouterr().out


def test_a_clip_exemption_that_no_longer_fires_fails_the_report(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        text_clearance, "EXEMPTIONS", {"anim_mended: microphone": "old"}
    )
    _fragments(tmp_path, "anim_mended", None)
    assert cfa.report(tmp_path, ["anim_mended"]) == 1
    assert "anim_mended: microphone no longer fires" in capsys.readouterr().out


def test_a_variant_that_was_not_inspected_fails_the_report(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _fragments(tmp_path, "anim_half", None)
    (tmp_path / "anim_half_es_dark.json").unlink()
    assert cfa.report(tmp_path, ["anim_half"]) == 1
    assert "anim_half [es dark]: not inspected" in capsys.readouterr().out


def test_the_figure_gates_leave_a_clip_exemption_to_the_audit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """No committed drawing carries a clip's name, so its entry is never stale there."""
    monkeypatch.setattr(minus_sign, "ALLOWED", {"anim_x: -3 dB": "a decision"})
    monkeypatch.setattr(decimal_point, "ALLOWED", {"anim_x: 0.5": "a decision"})
    assert minus_sign.check(tmp_path) == ([], [])
    assert decimal_point.check(tmp_path) == ([], [])
    assert legends.is_clip("anim_x: -3 dB")
    assert not legends.is_clip("true_peak_intersample")


def test_every_clip_is_named_the_way_the_gates_key_a_clip() -> None:
    assert all(clip.startswith(legends.CLIP_PREFIX) for clip in registry._ANIMATIONS)


# -- the audit-only run ----------------------------------------------------------


def test_an_audit_only_run_encodes_nothing_and_stamps_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    import animation_fingerprint

    monkeypatch.setenv(cfa.AUDIT_ENV, str(tmp_path))
    monkeypatch.setattr(
        media, "_save_animation", lambda *args, **kwargs: pytest.fail("encoded")
    )
    monkeypatch.setattr(
        animation_fingerprint, "stamp", lambda *args, **kwargs: pytest.fail("stamped")
    )
    # The output directory is the published one, so the audit-only guard is
    # the only thing that can keep the stamp from being written.
    import assets_dir

    monkeypatch.setattr(assets_dir, "clips_dir", lambda: tmp_path)
    fig, update = _clip(strike_at=(1,))
    media._render_clip(fig, update, str(tmp_path), "anim_struck", frames=FRAMES)
    registry._stamp_clips(["anim_struck"], str(tmp_path))
    assert [path.name for path in tmp_path.iterdir()] == ["anim_struck.json"]
    assert not plt.fignum_exists(fig.number)  # type: ignore[attr-defined]
    # The same call stamps once the run encodes.
    stamped: list[list[str]] = []
    monkeypatch.setattr(
        animation_fingerprint,
        "stamp",
        lambda clips, root=None, *, encoder: stamped.append(list(clips)),
    )
    monkeypatch.delenv(cfa.AUDIT_ENV)
    registry._stamp_clips(["anim_struck"], str(tmp_path))
    assert stamped == [["anim_struck"]]


@pytest.mark.parametrize(("strike_at", "status"), [((2,), 1), ((), 0)])
def test_the_audit_only_command_inspects_every_variant_and_exits_with_its_verdict(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    strike_at: tuple[int, ...],
    status: int,
) -> None:
    """``--audit-only --anim``: four variants inspected, nothing encoded, one exit status."""

    def draw(output_dir: str) -> None:
        # Drawn in the ink of the variant's page, as a real clip's lines are.
        fig, update = _clip(strike_at=strike_at, color=plt.rcParams["text.color"])
        media._render_clip(fig, update, output_dir, "anim_fake", frames=FRAMES)

    monkeypatch.setitem(registry._ANIMATIONS, "anim_fake", draw)
    monkeypatch.setattr(cfa, "DEFAULT_DIR", str(tmp_path / "audit"))
    monkeypatch.setattr(
        media, "_save_animation", lambda *args, **kwargs: pytest.fail("encoded")
    )
    # Set here so that the variable the command sets is put back afterwards.
    monkeypatch.setenv(cfa.AUDIT_ENV, str(tmp_path / "audit"))
    with pytest.raises(SystemExit, match=f"^{status}$") as finished:
        registry._audit_animations(["anim_fake"], 1)
    assert finished.value.code == status
    fragments = sorted(path.name for path in (tmp_path / "audit").glob("*.json"))
    assert fragments == sorted(
        f"{cfa.drawing_name('anim_fake', lang, dark=dark)}.json"
        for lang, dark in cfa.VARIANTS
    )
    out = capsys.readouterr().out
    if status:
        assert "anim_fake [en light]: 1 finding(s)" in out
    else:
        assert "passes the figure gates" in out


# -- the gates a frame is held to, one by one ------------------------------------


def _still(
    draw: Callable[[Figure], None], *, layout: str | None = None
) -> tuple[Figure, Callable[[int], tuple[Artist, ...]]]:
    """A clip whose every frame is the drawing *draw* makes on a 4 x 3 panel."""
    fig = plt.figure(figsize=(4.0, 3.0), layout=layout)
    ax = fig.add_subplot()
    ax.set_xlim(0.0, 10.0)
    ax.set_ylim(0.0, 10.0)
    draw(fig)

    def update(frame: int) -> tuple[Artist, ...]:
        del frame
        return ()

    return fig, update


def _gates(result: dict[str, object]) -> set[str]:
    return {run["gate"] for run in result["runs"]}  # type: ignore[attr-defined]


def _legend_over_a_point(fig: Figure) -> None:
    ax = fig.axes[0]
    (point,) = ax.plot([5.0], [5.0], "o", ms=6, label="a reading")
    ax.legend(handles=[point], loc="center", bbox_to_anchor=(0.5, 0.5))


def _line_over_a_tick_label(fig: Figure) -> None:
    ax = fig.axes[0]
    ax.set_xticks([0.0, 4.0, 8.0])
    ax.plot([4.0, 4.0], [-1.2, 1.0], color="black", lw=1.5, clip_on=False)


def _pale_band(fig: Figure) -> None:
    fig.axes[0].axvspan(2.0, 6.0, color="#f4f4f4")


def _crowded_ticks(fig: Figure) -> None:
    ax = fig.axes[0]
    ax.set_xticks([1.0, 1.1, 1.2, 1.3, 1.4])
    ax.set_xticklabels(["1000", "1100", "1200", "1300", "1400"])


@pytest.mark.parametrize(
    ("draw", "gate"),
    [
        (_legend_over_a_point, cfa.LEGEND),
        (_line_over_a_tick_label, cfa.TICK),
        (_pale_band, cfa.FILL),
        (_crowded_ticks, cfa.TICK_LABELS),
    ],
)
def test_each_gate_of_a_light_frame_fires_on_its_own_defect(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    draw: Callable[[Figure], None],
    gate: str,
) -> None:
    fig, update = _still(draw)
    result = _audit_only(monkeypatch, tmp_path, fig, update)
    assert gate in _gates(result)


def _chip_over_a_point(
    *, zorder: float = 2.0, colour: str | None = None
) -> Callable[[Figure], None]:
    def draw(fig: Figure) -> None:
        ax = fig.axes[0]
        ax.plot([5.0], [5.0], "o", ms=6, color="#1f77b4", zorder=zorder)
        face = colour or plt.rcParams["figure.facecolor"]
        ax.text(
            5.0,
            5.0,
            "source",
            ha="center",
            va="center",
            zorder=6,
            bbox={"boxstyle": "round,pad=0.3", "facecolor": face, "edgecolor": "none"},
        )

    return draw


def test_a_chip_over_a_plotted_point_is_found(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """The image-source clip's "source" chip hid the first image under it."""
    fig, update = _still(_chip_over_a_point())
    result = _audit_only(monkeypatch, tmp_path, fig, update)
    (run,) = (run for run in result["runs"] if run["gate"] == cfa.LEGEND)  # type: ignore[attr-defined]
    assert "the chip of text_" in run["detail"]
    assert "'source'" in run["detail"]


@pytest.mark.parametrize(
    "draw",
    [
        # Painted after the chip, the point is drawn on top of it.
        _chip_over_a_point(zorder=7.0),
        # A badge in the point's own colour stands in for the point.
        _chip_over_a_point(colour="#1f77b4"),
    ],
    ids=["point-above", "badge"],
)
def test_a_point_the_reader_still_has_is_not_a_chip_finding(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    draw: Callable[[Figure], None],
) -> None:
    fig, update = _still(draw)
    result = _audit_only(monkeypatch, tmp_path, fig, update)
    assert cfa.LEGEND not in _gates(result)


def test_a_label_a_later_chip_covers_is_found(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """The absorption-placement clip's Sabine label went under a verdict pill."""

    def draw(fig: Figure) -> None:
        ax = fig.axes[0]
        ax.text(2.0, 5.0, "Sabine estimate", fontsize=10, zorder=3)
        ax.text(
            3.5,
            4.8,
            "verdict",
            fontsize=10,
            zorder=4,
            bbox={"boxstyle": "round,pad=0.5", "facecolor": "white"},
        )

    fig, update = _still(draw)
    result = _audit_only(monkeypatch, tmp_path, fig, update)
    details = [run["detail"] for run in result["runs"]]  # type: ignore[attr-defined]
    assert any(
        "is painted over the letters of 'Sabine estimate'" in detail
        for detail in details
    ), details


def _haloed(text: str, *, line_zorder: float | None = None) -> Callable[[Figure], None]:
    """A label drawn with the halo the clips give text over a moving field."""
    from matplotlib import patheffects

    def draw(fig: Figure) -> None:
        ax = fig.axes[0]
        ax.text(
            2.0,
            5.0,
            text,
            fontsize=10,
            va="center",
            zorder=3,
            path_effects=[patheffects.withStroke(linewidth=2.4, foreground="white")],
        )
        if line_zorder is not None:
            ax.plot([0.0, 10.0], [5.0, 5.0], color="black", lw=1.2, zorder=line_zorder)

    return draw


@pytest.mark.parametrize(
    ("text", "language", "gate"),
    [("-3 dB", "en", cfa.MINUS), ("0.5", "es", cfa.DECIMAL)],
)
def test_the_numbers_of_a_haloed_label_are_read(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    text: str,
    language: str,
    gate: str,
) -> None:
    """A halo used to hide its label's string from every gate that reads one."""
    fig, update = _still(_haloed(text))
    result = _audit_only(monkeypatch, tmp_path, fig, update, language=language)
    assert gate in _gates(result)


def test_a_line_drawn_over_a_haloed_label_is_found_and_one_under_it_is_not(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """The halo hides what is painted before the label, never what comes after."""
    under, update = _still(_haloed("microphone", line_zorder=1.0))
    assert cfa.TEXT not in _gates(
        _audit_only(monkeypatch, tmp_path / "under", under, update)
    )
    over, update = _still(_haloed("microphone", line_zorder=5.0))
    assert cfa.TEXT in _gates(_audit_only(monkeypatch, tmp_path / "over", over, update))


def test_a_patch_faded_with_set_alpha_is_measured_at_its_opacity(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """matplotlib writes a patch's alpha as ``opacity``: the wavefront arcs hid there."""
    from matplotlib.patches import Arc

    def draw(fig: Figure) -> None:
        arc = Arc((5.0, 5.0), 4.0, 4.0, edgecolor="#2ca02c", lw=1.6)
        arc.set_alpha(0.27)
        fig.axes[0].add_patch(arc)

    from figures import theme

    theme.set_theme(dark=True)
    fig, update = _still(draw)
    result = _audit_only(monkeypatch, tmp_path, fig, update, dark=True)
    (run,) = (run for run in result["runs"] if run["gate"] == cfa.STROKE)  # type: ignore[attr-defined]
    assert "#2ca02c alpha=0.27" in run["detail"]


def test_a_stroke_is_measured_against_the_page_its_drawing_paints(
    tmp_path: pathlib.Path,
) -> None:
    """A dark frame is drawn on black, not on the panel grey of the site."""
    import check_stroke_contrast as stroke_contrast
    from figures import theme

    theme.set_theme(dark=True)
    try:
        fig = plt.figure(figsize=(3.0, 3.0))
        ax = fig.add_subplot()
        # A white hairline at 34 %: 3.09:1 on the site's panel grey, which
        # passes the 3:1 a hairline needs, and 2.89:1 on the black page the
        # frame is actually drawn on, which does not.
        ax.plot([0.0, 1.0], [0.5, 0.5], color="white", alpha=0.34, lw=0.5)
        path = tmp_path / "anim_x_dark.svg"
        path.write_text(
            theme.svg_text(fig, dpi=72, facecolor=fig.get_facecolor()),
            encoding="utf-8",
        )
    finally:
        theme.set_theme(dark=False)
    ((ratio, detail),) = stroke_contrast.faint_strokes(path)
    assert "on #000000" in detail
    assert 2.8 < ratio < 3.0


def test_a_frame_drawn_like_the_one_before_it_but_for_hashed_ids_is_not_measured_again(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """The tick-label measure lays the figure out again, which renames its clip paths.

    The axes move by a hair, matplotlib hashes the clip rectangle at full
    precision, and the ids of the next frame differ from this one's while
    the drawing, written to two decimals, does not: a still constrained
    clip is one drawing all the same.
    """
    fig, update = _still(
        lambda fig: fig.axes[0].plot([1.0, 9.0], [2.0, 8.0], "o-"), layout="constrained"
    )
    result = _audit_only(monkeypatch, tmp_path, fig, update)
    assert result["seen"] == FRAMES
    assert result["inspected"] == 1


# -- one finding per thing found -------------------------------------------------


def test_two_labels_struck_on_the_same_frames_are_two_findings(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Alike but for their numbers, two struck labels keep a run each, a frame counted once."""
    fig = plt.figure(figsize=(4.0, 3.0))
    ax = fig.add_subplot()
    ax.set_xlim(0.0, 10.0)
    ax.set_ylim(0.0, 10.0)
    ax.text(1.0, 5.0, "63 Hz", fontsize=10, va="center")
    ax.text(6.0, 5.0, "125 Hz", fontsize=10, va="center")
    (line,) = ax.plot([0.0, 10.0], [9.0, 9.0], color="black", lw=1.2)

    def update(frame: int) -> tuple[Artist, ...]:
        y = 5.0 if frame in (1, 2) else 9.0
        line.set_ydata([y, y])
        return (line,)

    result = _audit_only(monkeypatch, tmp_path, fig, update)
    runs = [run for run in result["runs"] if run["gate"] == cfa.TEXT]  # type: ignore[attr-defined]
    assert sorted(run["frames"] for run in runs) == [[[1, 2]], [[1, 2]]]
    assert any("'63 Hz'" in run["detail"] for run in runs)
    assert any("'125 Hz'" in run["detail"] for run in runs)


# -- the exemption tables, each keyed as it keys a figure ------------------------


def test_a_legend_exemption_names_the_clip_without_its_language(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    monkeypatch.setattr(legends, "EXEMPTIONS", {"anim_x": "a test decision"})
    fig, update = _still(_legend_over_a_point)
    result = _audit_only(
        monkeypatch, tmp_path, fig, update, clip="anim_x", language="es"
    )
    (run,) = (run for run in result["runs"] if run["gate"] == cfa.LEGEND)  # type: ignore[attr-defined]
    assert run["exempt_by"] == "check_figure_legends.EXEMPTIONS: anim_x"


@pytest.mark.parametrize(
    ("table", "key", "text", "language", "gate"),
    [
        (minus_sign, "anim_x: -3 dB", "-3 dB", "es", cfa.MINUS),
        (decimal_point, "anim_x: 0.5", "0.5", "es", cfa.DECIMAL),
    ],
)
def test_a_number_exemption_names_the_clip_and_the_text(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    table: object,
    key: str,
    text: str,
    language: str,
    gate: str,
) -> None:
    """The figure tables key ``figure: text``, the figure without language or theme."""
    monkeypatch.setattr(table, "ALLOWED", {key: "a test decision"})
    fig, update = _clip(text=text)
    result = _audit_only(
        monkeypatch, tmp_path, fig, update, clip="anim_x", language=language
    )
    (run,) = (run for run in result["runs"] if run["gate"] == gate)  # type: ignore[attr-defined]
    assert run["exempt_by"] is not None
    assert run["exempt_by"].endswith(key)


@pytest.mark.parametrize("gate", [text_clearance, legends], ids=["text", "legends"])
def test_a_figure_gate_does_not_call_a_clip_exemption_stale(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path, gate: object
) -> None:
    """A clip has no committed drawing to fire on; its entry is the audit's to ratchet."""
    clean = tmp_path / "clean.svg"
    fig = plt.figure(figsize=(2.0, 2.0))
    fig.add_subplot().plot([0.0, 1.0], [0.0, 1.0])
    fig.savefig(clean, format="svg")
    monkeypatch.setattr(legends, "light_figures", lambda: [clean])
    monkeypatch.setattr(gate, "EXEMPTIONS", {"anim_x": "the audit's"})
    assert gate.main([]) == 0  # type: ignore[attr-defined]
    monkeypatch.setattr(gate, "EXEMPTIONS", {"some_figure": "stale"})
    assert gate.main([]) == 1  # type: ignore[attr-defined]


# -- a render encodes all four variants or none ----------------------------------


def _dark_only_clip(log: pathlib.Path | None = None) -> Callable[[str], None]:
    """A clip whose line is fine on the white page and lost on the black one."""

    def draw(output_dir: str) -> None:
        fig, update = _clip(color="#20252b", log=log)
        media._render_clip(fig, update, output_dir, "anim_variants", frames=3)

    return draw


def _writing_encoder(
    anim: object, fig: Figure, output_dir: str, stem: str, **kwargs: object
) -> None:
    """Stands in for the encoder: one file per variant it is asked to encode."""
    del anim, fig, kwargs
    variant = cfa.drawing_name(stem, media._LANG, dark=bool(media._FILENAME_SUFFIX))
    (pathlib.Path(output_dir) / f"{variant}.webm").write_text("", encoding="utf-8")


@pytest.mark.parametrize("path", ["fork", "pool"])
def test_a_finding_on_the_dark_variants_alone_encodes_none_of_the_four(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path, path: str
) -> None:
    monkeypatch.setitem(registry._ANIMATIONS, "anim_variants", _dark_only_clip())
    monkeypatch.setattr(media, "_save_animation", _writing_encoder)
    render = (
        registry._render_anim_variants if path == "fork" else registry._run_anim_task
    )
    with pytest.raises(cfa.ClipFrameError, match=r"2 of 4 variants") as caught:
        render("anim_variants", str(tmp_path))
    message = str(caught.value)
    assert "none of the 4 was encoded" in message
    assert "[en dark] frame 0" in message
    assert "[es dark] frame 0" in message
    assert "[en light]" not in message
    assert list(tmp_path.iterdir()) == []


def test_a_clip_whose_four_variants_pass_is_encoded_after_one_inspection_each(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """The second pass encodes from the same code without drawing the frames again."""
    log = tmp_path / "frames.txt"
    out = tmp_path / "out"
    out.mkdir()

    def draw(output_dir: str) -> None:
        fig, update = _clip(color=plt.rcParams["text.color"], log=log)
        media._render_clip(fig, update, output_dir, "anim_variants", frames=3)

    monkeypatch.setitem(registry._ANIMATIONS, "anim_variants", draw)
    monkeypatch.setattr(media, "_save_animation", _writing_encoder)
    registry._render_anim_variants("anim_variants", str(out))
    assert sorted(p.name for p in out.iterdir()) == sorted(
        f"anim_variants{cfa.drawing_name('', lang, dark=dark)}.webm"
        for lang, dark in cfa.VARIANTS
    )
    # The opening draw and three frames, once per variant, in the copies the
    # first pass inspected them in; the encoder here draws nothing.
    assert len(log.read_text(encoding="utf-8").split()) == 4 * (1 + 3)
