#!/usr/bin/env python3
#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Hold every frame of a clip to the gates the figures are held to.

The figures are read for what makes them hard to read: a label struck through
by a curve or a spine, or painted over by a later fill
(:mod:`check_figure_text_clearance`), anything drawn over a tick label
(:mod:`check_figure_tick_clearance`), a legend or the chip of a label over a
datum (:mod:`check_figure_legends`), two tick labels run together
(:mod:`figure_tick_audit`), a shaded region or a line the page swallows
(:mod:`check_figure_contrast`, :mod:`check_stroke_contrast`), a number signed
with a hyphen (:mod:`check_figure_minus_sign`) and a Spanish number written
with a point (:mod:`check_figure_decimal_point`). Each reads the committed SVG.
A clip has none: its frames exist only while the encoder pulls them, so none of
those gates ever saw one, and the EPNL flyover clip shipped its "microphone"
label struck through by the ground line. It was found by eye.

So the render reads its frames the way those gates read a figure, before a
byte is encoded. :func:`audit`, called by ``figures.media._render_clip``,
draws every frame of the clip as the SVG ``figures.theme.save_figure`` writes
(:func:`figures.theme.svg_text`) and runs on it the gates that apply to it. A
finding stops the render, naming the clip, the variant, the frame and the
finding, and nothing of the clip is encoded, stamped or published.

How a frame is drawn
--------------------
In a forked copy of the render process, by the clip's own ``FuncAnimation``
over its update function wrapped to note the frame it is asked for, saved with
a writer that writes each frame it is handed to SVG instead of piping it to
ffmpeg. That is what makes the frames inspected the frames encoded:

* **the order.** The animation drives the update exactly as it does when it
  encodes: once for the opening draw, then frames 0 to N-1 in turn. Several
  updates keep state between calls (the EPNL clip removes and redraws its
  window fill), and one driven out of order, or restarted after its last
  frame, draws something the video never shows;
* **the frame.** The same figure, the same canvas (``savefig.bbox`` standard,
  as the encoder sets it), the same ``savefig`` keywords;
* **the encode is untouched.** The copy is thrown away. The render process
  encodes from the state it was in before the audit, so the frames it encodes
  are the frames it would have encoded without one.

Two things in the copy differ from an encode, and neither reaches a frame.
The animation paints the canvas once more after each update
(``canvas.draw_idle``); that raster is never read, the SVG save draws the
same figure, so the copy skips it. And a raster inside a frame (the field of
an FDTD clip) is embedded at :data:`RASTER_DPI`: no gate reads the pixels of
an embedded image, and its placement does not depend on its resolution.

Which gates, on which variant
-----------------------------
The split the figure gates make. The geometry is read on the light frames, in
both languages (the dark twin is the same drawing in other colours, and a
Spanish label is wider): text clearance, tick clearance, legends and chips,
and the tick labels of an axis. What the page decides is read where it
applies: the contrast of a filled region on every variant, the contrast of a
stroke on the dark one, against the page the frame paints (black for a dark
clip). The minus sign on every variant, the decimal comma on the Spanish
ones.

A label drawn with a path effect, the halo the clips put round a caption over
a moving field, is read like any other: ``svg_text`` writes it as its string
and its glyphs with the halo's outline under them, where matplotlib would
write two bare outlines no gate can read. The halo is an opaque edge round the
letters, so a line painted before the label is hidden where the halo is, and
one painted after it is not.

A clip is encoded all or nothing
--------------------------------
:func:`audit` inspects one variant, and a finding can belong to one variant
alone: a line the dark page swallows, a Spanish label wider than the English
one. So the renderer (``figures.registry``) renders a clip twice. The first
pass, with :data:`GATE_ENV` set, inspects each of the four variants up to its
first finding and encodes nothing; :func:`verdict` reads the four results
and stops the clip if any of them failed. Only then does the second pass
encode the four, with :data:`AUDITED_ENV` naming the clip so its frames are
not drawn again. A clip function called directly for one variant is audited
the same way and refuses to encode that variant.

Every frame
-----------
Every frame is inspected, none sampled, and that was measured rather than
assumed. The audit, run over every frame of the 43 clips as they were drawn
before it, in their four variants, counted how long each finding held (one
gate on one label, chip or stroke of one variant, whatever number matplotlib
gave its artist on the frame): of 314 runs of consecutive frames, 24 lasted
a single frame (in six clips) and 40 three frames or fewer. Any stride would
have let some of them through: a label that moves several points a frame is
clear on both sides of the one frame where it is struck. What a frame costs is cut
separately, without dropping one: the copy skips the raster the encode paints
and never reads; the geometry gates run on the light variants only, as for
the figures; a frame drawn like the one before it (a closing hold, a still
stretch), compared with the ids matplotlib hashes from float coordinates
taken out, takes that frame's findings instead of being measured again; and
on a one-clip render (``--anim``) the four variants are inspected in four
processes at once, while a full render spreads the clips over its pool and
inspects a clip's four variants in turn.

Exemptions
----------
The checkers' own tables, each keyed for a clip the way it keys a figure,
with the reason:

* ``check_figure_text_clearance.EXEMPTIONS``: the drawing, with its language
  suffix (``anim_epnl_flyover`` for the English frames,
  ``anim_epnl_flyover_es`` for the Spanish ones), or ``drawing: text``;
* ``check_figure_legends.EXEMPTIONS``: the clip, without a language suffix;
* ``check_figure_minus_sign.ALLOWED`` and
  ``check_figure_decimal_point.ALLOWED``: ``clip: text``, the clip without a
  language or theme suffix.

A gate that reads the committed drawings does not call such an entry stale,
since none carries a clip's name (``check_figure_legends.is_clip``);
:func:`report` does, once every variant of the clip has been inspected.

Running it
----------
A render runs it: ``python scripts/generate_graphs.py --animations --anim
<clip>``. To inspect without rendering, for a sweep or after a change to a
clip's drawing code::

    python scripts/generate_graphs.py --animations --audit-only [--anim CLIP]
    make animation-audit                    # every clip
    make animation-audit ANIM=anim_<name>   # one

which encodes nothing, stamps no fingerprint and publishes nothing; each
variant writes what it found under :data:`DEFAULT_DIR`, and :func:`report`
prints every finding with the frames it holds over and exits 1 on any.

There is no CI job: CI cannot render a clip. The freshness gate
(``scripts/check_animation_freshness.py``) fails a pull request whose code
moved a clip's fingerprint until the clip is rendered again, and the render
runs this audit. The fingerprint follows a clip's drawing code through
``scripts/figures`` and the drawing helpers of ``phonometry._plot`` it calls;
a change to this module or to a checker moves no fingerprint, so after one,
``make animation-audit`` over every clip is what shows the published clips
still pass.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import pathlib
import re
import sys
import tempfile
import time
import traceback
from typing import TYPE_CHECKING, Any, NamedTuple

_SCRIPTS = pathlib.Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import check_figure_contrast as fill_contrast
import check_figure_decimal_point as decimal_point
import check_figure_legends as legends
import check_figure_minus_sign as minus_sign
import check_figure_text_clearance as text_clearance
import check_figure_tick_clearance as tick_clearance
import check_stroke_contrast as stroke_contrast
import figure_tick_audit as tick_labels

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from matplotlib.animation import AbstractMovieWriter
    from matplotlib.artist import Artist
    from matplotlib.figure import Figure

#: Set by ``generate_graphs.py --audit-only`` to the directory each variant
#: writes what it found to. While it is set, a clip is inspected and never
#: encoded, and nothing is stamped or published.
AUDIT_ENV = "PHONOMETRY_CLIP_AUDIT"

#: Set by the renderer (``figures.registry``) for the first of the two passes
#: of a render, to the directory each of the clip's four variants writes what
#: it found to. While it is set a variant is inspected up to its first finding
#: and not encoded, and :func:`verdict` then reads the four results: the clip
#: is encoded only when every variant passed.
GATE_ENV = "PHONOMETRY_CLIP_GATE"

#: Set by the renderer for the second pass, to the clip whose four variants
#: the first pass of this render found clean: :func:`audit` lets that clip
#: through without drawing its frames again.
AUDITED_ENV = "PHONOMETRY_CLIP_AUDITED"

#: Where ``--audit-only`` writes, under ``build/``, which is gitignored.
DEFAULT_DIR = "build/clip-audit"

#: The resolution an embedded raster is drawn at in a frame's SVG. No gate
#: reads the pixels of an embedded image, and its place on the page does not
#: depend on how many it has; at the clip's own 300 dpi the field of an FDTD
#: frame costs a third more to write for nothing any gate looks at.
RASTER_DPI = 72

#: The gates, as a finding names them.
TEXT = "text clearance"
TICK = "tick clearance"
LEGEND = "legend or chip"
TICK_LABELS = "tick labels"
FILL = "fill contrast"
STROKE = "stroke contrast"
MINUS = "minus sign"
DECIMAL = "decimal comma"

#: Where each gate's rule is written, for the line under a failure.
RULES = {
    TEXT: "F46",
    TICK: "F45",
    LEGEND: "F47",
    TICK_LABELS: "F35",
    FILL: "F48",
    STROKE: "F49",
    MINUS: "F30",
    DECIMAL: "F28",
}

#: The four variants of a clip: language and theme, as the renderer runs them.
VARIANTS = (("en", False), ("en", True), ("es", False), ("es", True))


class Hit(NamedTuple):
    """One finding on one frame, exempt or not."""

    gate: str
    #: What the finding is about, without its measurement or the numbers its
    #: text reads: the same finding on the next frame has the same subject,
    #: so a run of frames reads as one even while a readout counts up.
    subject: str
    #: The checker's own line for it.
    detail: str
    #: The exemption key that covers it, as ``"<table>: <key>"``, or ``None``.
    exempt_by: str | None


class ClipFrameError(RuntimeError):
    """A frame of a clip failed a gate, so the clip was not encoded."""


def drawing_name(clip: str, language: str, *, dark: bool) -> str:
    """The name a frame is saved and keyed under, as the clip's file would be."""
    return (
        clip + ("" if language == "en" else f"_{language}") + ("_dark" if dark else "")
    )


def variant_name(language: str, *, dark: bool) -> str:
    """``"en light"``, ``"es dark"``: how a report names a variant."""
    return f"{language} {'dark' if dark else 'light'}"


def audit_dir() -> pathlib.Path | None:
    """The directory of an audit-only run, or ``None`` when the render encodes."""
    value = os.environ.get(AUDIT_ENV)
    return pathlib.Path(value) if value else None


def gate_dir() -> pathlib.Path | None:
    """The directory of the first pass of a render, or ``None`` outside it."""
    value = os.environ.get(GATE_ENV)
    return pathlib.Path(value) if value else None


def audit_only() -> bool:
    """Whether this pass inspects the clips without encoding them.

    True in an audit-only run, and in the first pass of a render, which
    inspects the four variants of a clip before any of them is encoded.
    """
    return audit_dir() is not None or gate_dir() is not None


# -- one frame ---------------------------------------------------------------


#: A number in running text, as a readout writes it; not the digits of an
#: artist's id (``line2d_23``), which name what is drawn over a label.
_NUMBER = re.compile(r"(?<![A-Za-z_\d])[-+\u2212]?\d+(?:[.,]\d+)?")

#: The ids matplotlib hashes for a clipping path (``p`` and ten hex digits)
#: and for a marker glyph (``m``), with every reference to them. They are
#: hashed from the clip rectangle and the marker path at full float
#: precision, and the tick-label measure lays the figure out once more, which
#: moves the axes by about 1e-10 pt: the ids change while the drawing, written
#: to two decimals, does not. A frame is compared with the one before it
#: with them taken out.
_HASHED_ID = re.compile(r"\b[pm][0-9a-f]{10}\b")


def _subject(*parts: object) -> str:
    """What a finding is about, with the numbers its text reads taken out."""
    return _NUMBER.sub("#", "|".join(str(part) for part in parts))


def _exempt(table: str, mapping: Iterable[str], *keys: str) -> str | None:
    """The first of *keys* the exemption table *mapping* holds, named for the report."""
    held = set(mapping)
    return next((f"{table}: {key}" for key in keys if key in held), None)


def _geometry(path: pathlib.Path, fig: Figure) -> list[Hit]:
    """What the light drawing's geometry fails: the gates read in both languages."""
    hits = [
        Hit(
            TEXT,
            _subject(found.over, found.text),
            found.describe(),
            _exempt(
                "check_figure_text_clearance.EXEMPTIONS",
                text_clearance.EXEMPTIONS,
                found.key,
                found.drawing,
            ),
        )
        for found in text_clearance.measure(path)
    ]
    hits += [
        Hit(
            TICK,
            _subject(cover.kind, cover.artist, cover.label),
            cover.describe(),
            None,
        )
        for cover in tick_clearance.measure(path)
    ]
    hits += [
        Hit(
            LEGEND,
            _subject(overlap.legend, overlap.artist),
            overlap.describe(),
            _exempt(
                "check_figure_legends.EXEMPTIONS",
                legends.EXEMPTIONS,
                overlap.drawing.removesuffix("_es"),
            ),
        )
        for overlap in legends.measure(path)
    ]
    for hit in tick_labels.measure(fig):
        labels = ", ".join(
            json.dumps(label, ensure_ascii=False) for label in hit["labels"]
        )
        stray = hit["kind"] == tick_labels.STRAY
        what = (
            "minor labels beside major ticks set by hand"
            if stray
            else f"tick labels run into each other ({hit['depth_pt']:.2f} pt)"
        )
        hits.append(
            Hit(
                TICK_LABELS,
                _subject(hit["kind"], hit["axis"], labels),
                f"{path.stem}: {hit['axis']}: {what}: {labels}",
                None,
            )
        )
    return hits


def _page(path: pathlib.Path, *, dark: bool) -> list[Hit]:
    """What the page fails: a fill on any page, a stroke on the dark one."""
    hits = [
        Hit(
            FILL,
            _subject(region.group, region.fill, region.opacity, region.background),
            region.describe(),
            None,
        )
        for region in fill_contrast.measure(path)
        if not region.ok
    ]
    if dark:
        hits += [
            Hit(STROKE, _subject(detail), f"{path.stem}: stroke {detail}", None)
            for _ratio, detail in stroke_contrast.faint_strokes(path)
        ]
    return hits


def _numbers(path: pathlib.Path, language: str) -> list[Hit]:
    """How the numbers are written: the sign everywhere, the decimal in Spanish."""
    figure = minus_sign.figure(path)
    hits = [
        Hit(
            MINUS,
            _subject(text),
            f"{path.stem}: draws {text!r}, whose sign is a hyphen-minus rather "
            "than the minus sign U+2212",
            _exempt(
                "check_figure_minus_sign.ALLOWED",
                minus_sign.ALLOWED,
                f"{figure}: {text}",
            ),
        )
        for text in minus_sign.hyphenated(path)
    ]
    if language == "en":
        return hits
    figure = decimal_point.stem(path)
    hits += [
        Hit(
            DECIMAL,
            _subject(label),
            f"{path.stem}: the Spanish frame draws {label!r}, which a reader of "
            "that page reads as a thousands separator",
            _exempt(
                "check_figure_decimal_point.ALLOWED",
                decimal_point.ALLOWED,
                f"{figure}: {label}",
            ),
        )
        for label in decimal_point.point_labels(path)
    ]
    hits += [
        Hit(
            DECIMAL,
            _subject("clause", citation),
            f"{path.stem}: the Spanish frame cites {citation!r}, a clause number "
            "written as a decimal",
            None,
        )
        for citation in decimal_point.comma_clauses(path)
    ]
    return hits


def inspect(path: pathlib.Path, fig: Figure, *, language: str, dark: bool) -> list[Hit]:
    """Every finding of the gates that apply to one frame, exempt or not.

    :param path: The frame, saved as :func:`figures.theme.svg_text` writes it,
        under its drawing name (:func:`drawing_name`).
    :param fig: The live figure the frame was drawn from, which the tick-label
        measure reads.
    :param language: ``"en"`` or ``"es"``.
    :param dark: Whether the frame is drawn on the dark page.
    """
    hits = [] if dark else _geometry(path, fig)
    return hits + _page(path, dark=dark) + _numbers(path, language)


# -- every frame, in a copy of the process -----------------------------------


class _Stop(Exception):
    """Raised from the writer to end the pass at the first failing frame."""


class _Tracked:
    """The clip's update function, noting the frame it was last asked for."""

    def __init__(self, update: Callable[..., Iterable[Artist] | None]) -> None:
        self.update = update
        self.frame = -1

    def __call__(self, frame: int, *args: Any) -> Iterable[Artist] | None:
        self.frame = frame
        return self.update(frame, *args)


def _writer(on_frame: Callable[[dict[str, Any]], None]) -> AbstractMovieWriter:
    """A movie writer that hands each frame to *on_frame* instead of encoding it."""
    from matplotlib.animation import AbstractMovieWriter

    class FrameWriter(AbstractMovieWriter):
        def setup(
            self, fig: Figure, outfile: str | pathlib.Path, dpi: float | None = None
        ) -> None:
            super().setup(fig, outfile, dpi)

        def grab_frame(self, **savefig_kwargs: Any) -> None:
            on_frame(savefig_kwargs)

        def finish(self) -> None:
            """Nothing was opened, so nothing is closed."""

        def _supports_transparency(self) -> bool:
            # The WebM writer the clips are encoded with does, so the
            # animation hands it the figure's own face colour, unflattened;
            # this hands the frame the same one.
            return True

    return FrameWriter(fps=20)


def _pass(
    fig: Figure,
    update: Callable[..., Iterable[Artist] | None],
    *,
    frames: int,
    interval_ms: float,
    drawing: str,
    language: str,
    dark: bool,
    stop_at_first: bool,
    workdir: pathlib.Path,
) -> dict[str, Any]:
    """Inspect every frame in the order the animation draws it; runs in the copy."""
    import matplotlib.pyplot as plt
    from figures.theme import svg_text
    from matplotlib.animation import FuncAnimation

    tracked = _Tracked(update)
    anim = FuncAnimation(fig, tracked, frames=frames, interval=interval_ms, blit=False)
    # The raster the animation paints after each update is never read here,
    # and the SVG save below draws the same figure; see the module docstring.
    fig.canvas.draw_idle = lambda *args, **kwargs: None  # type: ignore[method-assign]
    path = workdir / f"{drawing}.svg"
    runs: dict[tuple[str, str, str | None, int], dict[str, Any]] = {}
    state: dict[str, Any] = {"inspected": 0, "seen": 0, "failed": None, "last": None}

    def on_frame(savefig_kwargs: dict[str, Any]) -> None:
        frame = tracked.frame
        state["seen"] += 1
        text = svg_text(fig, dpi=RASTER_DPI, **savefig_kwargs)
        digest = hashlib.sha256(_HASHED_ID.sub("#", text).encode("utf-8")).digest()
        last = state["last"]
        if last is not None and last[0] == digest:
            hits = last[1]
        else:
            path.write_text(text, encoding="utf-8")
            hits = inspect(path, fig, language=language, dark=dark)
            state["inspected"] += 1
            state["last"] = (digest, hits)
        # Two findings alike but for the numbers their texts read (one line
        # through "63 Hz" and "125 Hz") are two findings: each keeps a run of
        # its own, told apart by its rank among its like on the frame, and a
        # run counts a frame once.
        rank: dict[tuple[str, str, str | None], int] = {}
        for hit in hits:
            alike = (hit.gate, hit.subject, hit.exempt_by)
            rank[alike] = rank.get(alike, -1) + 1
            run = runs.setdefault(
                (*alike, rank[alike]),
                {
                    "gate": hit.gate,
                    "detail": hit.detail,
                    "exempt_by": hit.exempt_by,
                    "frames": [],
                },
            )
            spans = run["frames"]
            if spans and spans[-1][1] == frame:
                continue
            if spans and spans[-1][1] == frame - 1:
                spans[-1][1] = frame
            else:
                spans.append([frame, frame])
        if stop_at_first and any(hit.exempt_by is None for hit in hits):
            state["failed"] = frame
            raise _Stop

    with plt.rc_context({"savefig.bbox": "standard"}), contextlib.suppress(_Stop):
        anim.save(
            str(workdir / f"{drawing}.frames"),
            writer=_writer(on_frame),
            savefig_kwargs={"facecolor": fig.get_facecolor()},
        )
    return {
        "frames": frames,
        "seen": state["seen"],
        "inspected": state["inspected"],
        "failed_at": state["failed"],
        "runs": list(runs.values()),
    }


def audit(
    fig: Figure,
    update: Callable[..., Iterable[Artist] | None],
    clip: str,
    *,
    frames: int,
    interval_ms: float,
    language: str,
    dark: bool,
) -> None:
    """Inspect every frame of one variant of *clip* before it is encoded.

    Called by ``figures.media._render_clip`` with the figure in its final
    language and the update function it is about to encode, and before the
    ``FuncAnimation`` that encodes it is made. The frames are drawn in a
    forked copy of this process (see the module docstring); this process is
    left exactly as it was.

    What happens on a finding depends on the pass:

    * the first pass of a render (:data:`GATE_ENV`) inspects the variant up
      to its first finding and writes what it found for :func:`verdict`,
      which the renderer reads once all four variants are inspected;
    * an audit-only run (:data:`AUDIT_ENV`) inspects every frame and writes
      what it found for :func:`report`;
    * the second pass of a render returns at once for the clip the first
      pass found clean (:data:`AUDITED_ENV`);
    * anything else, a clip function called directly for one variant, raises
      :class:`ClipFrameError` at the first frame with a finding no exemption
      covers, naming the clip, the variant, the frame and every finding on
      it, and the caller encodes nothing of that variant.

    :raises ClipFrameError: on a finding outside the first pass and an
        audit-only run, or when the copy could not finish.
    :raises RuntimeError: where the platform cannot fork, since inspecting the
        frames in this process would leave the update's state at the last
        frame and the encode would start from there.
    """
    if os.environ.get(AUDITED_ENV) == clip:
        return
    if not hasattr(os, "fork"):
        msg = (
            "the clip frame audit needs os.fork: it draws the frames in a copy "
            "of the render process so the encode starts from the state the "
            "audit found"
        )
        raise RuntimeError(msg)
    every_frame = audit_dir()
    directory = every_frame or gate_dir()
    drawing = drawing_name(clip, language, dark=dark)
    variant = variant_name(language, dark=dark)
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="clip-frames-") as work:
        workdir = pathlib.Path(work)
        result_file = workdir / "result.json"
        sys.stdout.flush()
        sys.stderr.flush()
        pid = os.fork()
        if pid == 0:  # the copy: inspect, write what was found, leave at once
            code = 0
            try:
                result = _pass(
                    fig,
                    update,
                    frames=frames,
                    interval_ms=interval_ms,
                    drawing=drawing,
                    language=language,
                    dark=dark,
                    stop_at_first=every_frame is None,
                    workdir=workdir,
                )
                result_file.write_text(json.dumps(result), encoding="utf-8")
            except BaseException:
                code = 1
                with contextlib.suppress(BaseException):
                    result_file.write_text(
                        json.dumps({"error": traceback.format_exc()}), encoding="utf-8"
                    )
            finally:
                os._exit(code)
        _, status = os.waitpid(pid, 0)
        try:
            result = json.loads(result_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            result = {
                "error": f"the audit process ended with status {status} and wrote nothing"
            }
    if "error" in result:
        msg = (
            f"{clip} [{variant}]: the frame audit could not finish:\n{result['error']}"
        )
        raise ClipFrameError(msg)
    result.update(
        clip=clip,
        variant=variant,
        drawing=drawing,
        seconds=round(time.perf_counter() - started, 1),
    )
    if directory is not None:
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{drawing}.json").write_text(
            json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8"
        )
        return
    lines = _failure(result)
    if lines:
        lines[0] = f"{clip} {lines[0]}; this variant was not encoded"
        gates = {line.split(":", 1)[0].strip() for line in lines[1:]}
        raise ClipFrameError("\n".join([*lines, _advice(gates)]))


def _failure(result: dict[str, Any]) -> list[str]:
    """The lines that name a variant's first failing frame, or none if it passed.

    The first reads ``[variant] frame N of 0-M: K finding(s)``, each next
    one ``  gate: detail`` for a finding on that frame.
    """
    failed = result["failed_at"]
    if failed is None:
        return []
    on_frame = [
        run
        for run in result["runs"]
        if run["exempt_by"] is None and any(a <= failed <= b for a, b in run["frames"])
    ]
    lines = [
        f"[{result['variant']}] frame {failed} of 0-{result['frames'] - 1}: "
        f"{len(on_frame)} finding(s)"
    ]
    lines += [f"  {run['gate']}: {run['detail']}" for run in on_frame]
    return lines


def verdict(directory: pathlib.Path, clip: str) -> None:
    """Pass *clip* to its encode only if the first pass found all four variants clean.

    Reads what each variant wrote to *directory* in the first pass of a
    render (:data:`GATE_ENV`). A finding in any of them stops the whole
    clip, so a finding on the dark page or in Spanish alone does not leave
    the other variants encoded beside it.

    :raises ClipFrameError: naming every variant that failed, its first
        failing frame and the findings on it, or one that was not inspected.
    """
    failing: list[str] = []
    gates: set[str] = set()
    for language, dark in VARIANTS:
        drawing = drawing_name(clip, language, dark=dark)
        path = directory / f"{drawing}.json"
        if not path.exists():
            failing.append(f"[{variant_name(language, dark=dark)}] not inspected")
            continue
        lines = _failure(json.loads(path.read_text(encoding="utf-8")))
        failing += lines
        gates |= {line.split(":", 1)[0].strip() for line in lines[1:]}
    if not failing:
        return
    failed = sum(1 for line in failing if line.startswith("["))
    head = (
        f"{clip}: {failed} of {len(VARIANTS)} variants fail the frame audit, so "
        f"none of the {len(VARIANTS)} was encoded"
    )
    tail = [_advice(gates)] if gates else []
    raise ClipFrameError("\n".join([head, *(f"  {line}" for line in failing), *tail]))


def _advice(gates: Iterable[str]) -> str:
    rules = ", ".join(sorted({RULES[gate] for gate in gates}))
    return (
        f"  -> fix the clip's drawing code (docs/contributing/docs-and-figures.md, "
        f"{rules}); a finding that is a decision goes in the gate's own exemption "
        "table, keyed by the clip, with the reason. "
        "python scripts/generate_graphs.py --animations --audit-only --anim <clip> "
        "lists every frame without encoding."
    )


# -- the audit-only run --------------------------------------------------------


def _clip_of(key: str) -> str:
    """The clip an exemption key names, its language suffix and text taken off."""
    drawing = key.partition(": ")[0]
    return drawing.removesuffix("_es")


def clip_exemptions() -> dict[str, list[str]]:
    """Every exemption keyed by a clip, as ``"<table>: <key>"``, by clip."""
    tables = {
        "check_figure_text_clearance.EXEMPTIONS": text_clearance.EXEMPTIONS,
        "check_figure_legends.EXEMPTIONS": legends.EXEMPTIONS,
        "check_figure_minus_sign.ALLOWED": minus_sign.ALLOWED,
        "check_figure_decimal_point.ALLOWED": decimal_point.ALLOWED,
    }
    found: dict[str, list[str]] = {}
    for table, mapping in tables.items():
        for key in mapping:
            if legends.is_clip(key):
                found.setdefault(_clip_of(key), []).append(f"{table}: {key}")
    return found


def _spans(frames: list[list[int]]) -> str:
    count = sum(b - a + 1 for a, b in frames)
    parts = [str(a) if a == b else f"{a}-{b}" for a, b in frames]
    shown = ", ".join(parts[:6]) + (
        f", ... ({len(parts)} runs)" if len(parts) > 6 else ""
    )
    return f"frame{'s' if count > 1 else ''} {shown} ({count})"


def report(directory: pathlib.Path, clips: Iterable[str]) -> int:
    """Print what an audit-only run found in *clips*; 0 when every frame passes.

    Fails on a finding no exemption covers, on a variant that was not
    inspected, and on an exemption keyed by one of these clips that none of
    its four variants fired.
    """
    clips = list(clips)
    failures = 0
    fired: set[str] = set()
    frames_seen = inspected = 0
    for clip in clips:
        for language, dark in VARIANTS:
            drawing = drawing_name(clip, language, dark=dark)
            variant = variant_name(language, dark=dark)
            path = directory / f"{drawing}.json"
            if not path.exists():
                print(f"::error::{clip} [{variant}]: not inspected (no {path.name})")
                failures += 1
                continue
            result = json.loads(path.read_text(encoding="utf-8"))
            frames_seen += result["seen"]
            inspected += result["inspected"]
            open_runs = [run for run in result["runs"] if run["exempt_by"] is None]
            fired.update(run["exempt_by"] for run in result["runs"] if run["exempt_by"])
            if not open_runs:
                continue
            failures += len(open_runs)
            print(
                f"::error::{clip} [{variant}]: {len(open_runs)} finding(s) over "
                f"{result['frames']} frames"
            )
            for run in open_runs:
                print(f"  {_spans(run['frames'])}: {run['gate']}: {run['detail']}")
    exemptions = clip_exemptions()
    stale = sorted(
        key for clip in clips for key in exemptions.get(clip, []) if key not in fired
    )
    for key in stale:
        print(
            f"::error::{key} no longer fires on any frame of its clip: delete the entry"
        )
    if failures or stale:
        print(
            f"\n{failures} finding(s) and {len(stale)} stale exemption(s) in "
            f"{len(clips)} clip(s)."
        )
        return 1
    print(
        f"Every frame of {len(clips)} clip(s) passes the figure gates: {frames_seen} "
        f"frames over four variants each, {inspected} distinct drawings measured."
    )
    return 0
