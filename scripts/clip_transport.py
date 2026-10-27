#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The client side of the clip transport: render the clips on a node.

With a host in ``PHONOMETRY_COMPUTE`` (``cupy@nas``), ``make animations``
and ``make animation-audit`` send the clips to that node instead of
rendering them here. What travels is this checkout as ``git archive`` of
HEAD (the parts a render reads), so the node renders exactly the committed
code; a checkout with changes is refused rather than half sent, except for
the files a run writes itself (the stamps and the lock of the published
assets), which wait for a commit after it. The node renders each clip in a
lane of its own (``scripts/clip_node.py``) and sends its files back as soon
as it is done. This side trusts none of them until it has checked them: the
name is one a render of that clip writes, the size is under its cap, the
first bytes are the container's, and the fingerprint the node computed from
the archive is the one this checkout computes; what the node says (a log
tail, the reasons of a refusal, what it writes to its standard error) is
shown with its control characters escaped, and its other values only
through ``repr``. Only then are the files copied into the assets checkout
and the clip stamped, one clip at a time, so a run that stops half way
keeps every clip that arrived whole and nothing else, and the next run
picks up the rest. The fingerprints, those compared and those stamped, are
taken on the archive as it was sent, unpacked here, so an edit saved while
a clip is copied is never stamped as the code that rendered it; a clip that
arrives once the checkout has moved is not copied at all, and the node is
stopped there, since no clip it renders after that would be.
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import functools
import io
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import threading
from typing import TYPE_CHECKING, Any, BinaryIO

_SCRIPTS = pathlib.Path(__file__).resolve().parent
_ROOT = _SCRIPTS.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import animation_fingerprint
import assets_dir
import check_animation_freshness
import clip_frame_audit
import clip_link
import clip_node

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping, Sequence

    import clip_placement

    from phonometry.simulation import Compute
    from phonometry.simulation._remote.hosts import HostEntry

#: What the archive carries: the code a render runs and the files it reads.
#: ``VERSION`` is there because the node image installs the requirements and
#: not phonometry, which then reads its version from that file.
SHIPPED = (
    "src",
    "scripts",
    "pyproject.toml",
    "VERSION",
    "engine-digests.json",
    "requirements.txt",
    "requirements-figures.txt",
)

#: The tracked files a run writes itself: the stamps of the clips it copied,
#: and the lock of the assets commit it published. They wait for a commit
#: after the run, so neither stops the next clip or the next run.
RUN_WRITES = ("scripts/animation_fingerprints.txt", "assets.lock")

#: The most a file of each kind may weigh when it comes back: a cap against a
#: runaway, not a measurement. A published kind is capped at the next power of
#: two above four times its largest published file (read on the assets
#: checkout on 2026-10-21: WebM 5.27 MB, GIF 6.36 MB, poster 0.23 MB); a JSON
#: record (a language fragment or an audit finding) at 4 MiB, some fifty
#: times the largest language fragment seen (86 kB).
FILE_CAPS = {".webm": 32 << 20, ".gif": 32 << 20, ".webp": 1 << 20, ".json": 4 << 20}

#: How long the node has, once its input closes, to stop its lanes and
#: remove what it unpacked before the connection is killed.
EXIT_GRACE_S = 30.0

#: How long a git command here may take [s]: far past what one takes on this
#: checkout, so that only a git that hangs is stopped.
_GIT_S = 120.0
#: How long a killed connection, and the thread that relays its standard
#: error, may take to end [s]: a kill ends ssh at once.
_KILLED_S = 30.0
#: The most of one line of the node's standard error relayed at once [bytes].
_RELAY_BYTES = 8 << 10
#: A name the node may give a file it sends back: ASCII letters, digits,
#: ``_``, ``-`` and ``.``, no dot first, 128 characters at most. Every name a
#: render writes is one (``anim_x_es_dark_poster.webp``, a language record's
#: ``4242.json``).
_FILE_NAME = re.compile(r"[\w-][\w.-]{0,127}\Z", re.ASCII)


class DirtyTreeError(RuntimeError):
    """The checkout holds changes the archive would not carry."""


class NodeRunError(RuntimeError):
    """A node run that cannot go on, and why.

    The archive is larger than a node accepts, the digest file it carries
    does not hold the engines' digests, or the node sent a frame the run
    did not ask for. A ``RuntimeError``, as a refusal of the node's is.
    """


def _git(root: pathlib.Path, *args: str) -> bytes:
    """What ``git -C root <args>`` prints.

    :raises subprocess.CalledProcessError: when git fails, as it does
        outside a checkout.
    :raises subprocess.TimeoutExpired: when it does not finish in
        :data:`_GIT_S`.
    """
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        check=True,
        timeout=_GIT_S,
    ).stdout


def dirty_paths(root: pathlib.Path) -> list[str]:
    """Changed tracked files anywhere, and untracked files under scripts/ and src/.

    The files a run writes itself (:data:`RUN_WRITES`) are left out.

    :raises subprocess.CalledProcessError: when *root* is not a checkout.
    :raises subprocess.TimeoutExpired: when git does not answer in time.
    """
    # Asked again for each clip that comes back, while the checkout may be in
    # use: without optional locks, the status never holds the index's lock
    # against a git command run there meanwhile.
    listing = os.fsdecode(
        _git(
            root,
            "--no-optional-locks",
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
        )
    )
    found: list[str] = []
    entries = iter(listing.split("\0"))
    for entry in entries:
        if not entry:
            continue
        status, path = entry[:2], entry[3:]
        if "R" in status or "C" in status:
            next(entries, None)  # the original path of a rename or a copy
        if path in RUN_WRITES:
            continue
        if status != "??" or path.startswith(("scripts/", "src/")):
            found.append(path)
    return found


def refuse_dirty_tree(root: pathlib.Path) -> None:
    """Refuse a checkout the archive would not carry whole.

    :raises DirtyTreeError: naming the changes, when there are any.
    :raises subprocess.CalledProcessError: when *root* is not a checkout.
    :raises subprocess.TimeoutExpired: when git does not answer in time.
    """
    paths = dirty_paths(root)
    if paths:
        shown = ", ".join(paths[:8]) + (", ..." if len(paths) > 8 else "")
        msg = f"the node renders the committed code; commit first ({len(paths)} changed: {shown})"
        raise DirtyTreeError(msg)


def _head(root: pathlib.Path) -> str:
    """The commit *root* has checked out.

    :raises subprocess.CalledProcessError: when *root* is not a checkout.
    :raises subprocess.TimeoutExpired: when git does not answer in time.
    """
    return _git(root, "rev-parse", "HEAD").decode("ascii").strip()


def unmoved(root: pathlib.Path, head: str) -> bool:
    """Whether the checkout is still the one a run began from: the same HEAD, no change but the run's own.

    :raises subprocess.CalledProcessError: when *root* is not a checkout.
    :raises subprocess.TimeoutExpired: when git does not answer in time.
    """
    return _head(root) == head and not dirty_paths(root)


def archive(root: pathlib.Path, *, ref: str = "HEAD") -> bytes:
    """The tree of the commit *ref*, HEAD unless named, the parts a render needs, as a gzip tar.

    :raises NodeRunError: when it is larger than a node accepts.
    :raises subprocess.CalledProcessError: when *root* is not a checkout,
        or has no commit *ref*.
    :raises subprocess.TimeoutExpired: when git does not answer in time.
    """
    data = _git(root, "archive", "--format=tar.gz", ref, "--", *SHIPPED)
    if len(data) > clip_node.ARCHIVE_LIMIT:
        msg = f"the archive is {len(data)} bytes, over the {clip_node.ARCHIVE_LIMIT} a node accepts"
        raise NodeRunError(msg)
    return data


def _unpack(data: bytes, directory: pathlib.Path) -> pathlib.Path:
    """*directory*, once the archive *data* is unpacked into it as the node unpacks it.

    :raises tarfile.TarError: for an archive that does not unpack.
    """
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        tar.extractall(directory, filter="data")
    return directory


def _fresh(
    clip: str,
    current: Mapping[str, str],
    stamped: Mapping[str, str],
    encoders: Mapping[str, str],
    present: set[str],
) -> bool:
    return (
        stamped.get(clip) == current[clip]
        and encoders.get(clip) in animation_fingerprint.CLIP_ENCODERS
        and all(name in present for name in check_animation_freshness.outputs(clip))
    )


def clips_to_render(
    requested: Sequence[str] | None,
    *,
    force: bool,
    current: Mapping[str, str],
    stamped: Mapping[str, str],
    encoders: Mapping[str, str],
    present: set[str],
    weights: Mapping[str, float],
) -> list[str]:
    """The clips a node run renders, heaviest first.

    Named clips are always rendered. Otherwise every clip is, unless it is
    fresh: stamped with the current fingerprint, an AV1 encoder recorded and
    all its files present; that is what lets a run that stopped pick up
    where it was.

    :raises ValueError: for a named clip that is not registered.
    """
    unknown = sorted(set(requested or ()) - current.keys())
    if unknown:
        msg = f"unknown animation(s) {unknown}"
        raise ValueError(msg)
    if requested:
        chosen = list(requested)
    else:
        chosen = [
            clip
            for clip in current
            if force or not _fresh(clip, current, stamped, encoders, present)
        ]
    return sorted(chosen, key=lambda clip: (-weights.get(clip, 0.0), clip))


def job_header(
    clips: Sequence[str],
    *,
    devices: Mapping[str, clip_placement.ClipDevice],
    gpu_bytes: Mapping[str, int],
    host_bytes: Mapping[str, int],
    compute: str,
    encoder: animation_fingerprint.ClipEncoder,
    audit_only: bool,
) -> dict[str, Any]:
    """The first frame the node reads: each clip with its device and recorded needs."""
    return {
        "type": "job",
        "version": clip_node.PROTOCOL,
        "clips": [
            {
                "name": clip,
                "device": devices.get(clip, "cpu"),
                "gpu_bytes": gpu_bytes.get(clip, 0),
                "host_bytes": host_bytes.get(clip, 0),
            }
            for clip in clips
        ],
        "compute": compute,
        "encoder": encoder,
        "audit_only": audit_only,
    }


def default_encoder(compute: Compute) -> animation_fingerprint.ClipEncoder:
    """The encoder a node run uses unless told: NVENC with a GPU, SVT-AV1 on a CPU.

    A ``cpu`` placement passes no GPU to the node's container, so NVENC
    would have no card to open.
    """
    return "libsvtav1" if compute.device == "cpu" else "av1_nvenc"


@dataclasses.dataclass(frozen=True)
class Expect:
    """What this run asked the node for.

    :ivar tree: The archive the node was sent, unpacked here: the
        fingerprints each clip is compared with and stamped with are taken on
        it, so a stamp records the code the clip was rendered from whatever
        the working tree holds by then; ``None`` stands for this checkout.
    """

    clips: frozenset[str]
    encoder: animation_fingerprint.ClipEncoder
    audit_only: bool
    tree: pathlib.Path | None = None


@dataclasses.dataclass(frozen=True)
class Places:
    """Where what comes back is written."""

    clips: pathlib.Path
    fragments: pathlib.Path | None
    audit: pathlib.Path


def _names(clip: str, expect: Expect) -> list[str]:
    if expect.audit_only:
        return [
            f"{clip_frame_audit.drawing_name(clip, lang, dark=dark)}.json"
            for lang, dark in clip_frame_audit.VARIANTS
        ]
    return check_animation_freshness.outputs(clip)


def _entries(header: Mapping[str, Any], key: str) -> list[Mapping[str, Any]]:
    """The *key* list of a clip frame, one object per file.

    :raises ValueError: when it is not a list of objects.
    """
    value = header.get(key, [])
    if not isinstance(value, list) or not all(
        isinstance(entry, dict) for entry in value
    ):
        msg = f"{header['clip']}: the node's {key} are a list of objects; got {value!r:.80}"
        raise ValueError(msg)
    return value


def _entry_size(entry: Mapping[str, Any]) -> int:
    """The byte count the node announces for one file, its name and size checked.

    :raises ValueError: for a name a render does not write in that form, a
        kind of file the clips do not have, or a size outside one byte to its
        kind's cap.
    """
    name, size = entry.get("name"), entry.get("size")
    if not isinstance(name, str) or _FILE_NAME.match(name) is None:
        msg = f"the node sent a file name it may not: {name!r:.80}"
        raise ValueError(msg)
    cap = FILE_CAPS.get(pathlib.PurePosixPath(name).suffix)
    if cap is None:
        msg = f"the node sent a kind of file it may not: {name!r}"
        raise ValueError(msg)
    if isinstance(size, bool) or not isinstance(size, int) or not 0 < size <= cap:
        msg = f"{name}: {size!r:.80} bytes is outside 1..{cap}"
        raise ValueError(msg)
    return size


def _check_fragments(clip: str, fragments: Sequence[Mapping[str, Any]]) -> None:
    """Hold a clip's language records, whose names are checked, to what a render writes.

    :raises ValueError: for a record that is not JSON, or one named twice.
    """
    names = [entry["name"] for entry in fragments]
    if any(not name.endswith(".json") for name in names):
        msg = f"{clip}: a language fragment is not JSON"
        raise ValueError(msg)
    if len(set(names)) != len(names):
        msg = f"{clip}: the node sent a language record twice"
        raise ValueError(msg)


def result_sizes(header: dict[str, Any], expect: Expect) -> list[int]:
    """Check a frame from the node; the byte count of each of its buffers.

    :raises ValueError: for anything this run did not ask for.
    """
    kind, clip = header.get("type"), header.get("clip")
    if kind in ("done", "refused"):
        return []
    if kind != "clip" or not isinstance(clip, str) or clip not in expect.clips:
        msg = f"the node sent a frame nobody asked for: {kind!r:.80}, {clip!r:.80}"
        raise ValueError(msg)
    if header.get("ok") is not True:
        return []
    files, fragments = _entries(header, "files"), _entries(header, "fragments")
    if len(fragments) > clip_node.MAX_FRAGMENTS:
        msg = f"{clip}: {len(fragments)} language records, more than a render writes"
        raise ValueError(msg)
    sizes = [_entry_size(entry) for entry in (*files, *fragments)]
    if sorted(entry["name"] for entry in files) != sorted(_names(clip, expect)):
        msg = f"{clip}: the node sent other files than a render writes"
        raise ValueError(msg)
    _check_fragments(clip, fragments)
    if not expect.audit_only and header.get("encoder") != expect.encoder:
        msg = f"{clip}: the encoder was {header.get('encoder')!r:.80}, not {expect.encoder!r}"
        raise ValueError(msg)
    return sizes


def _looks_like(name: str, data: bytes) -> bool:
    suffix = pathlib.PurePosixPath(name).suffix
    if suffix == ".webm":
        return data.startswith(b"\x1a\x45\xdf\xa3")
    if suffix == ".gif":
        return data.startswith((b"GIF87a", b"GIF89a"))
    if suffix == ".webp":
        return data.startswith(b"RIFF") and data[8:12] == b"WEBP"
    return data.lstrip()[:1] in (b"{", b"[")


#: The signals that would end this process in the middle of a clip's moves:
#: Ctrl-C, a stop, and the terminal closing.
_HELD_SIGNALS = tuple(
    getattr(signal, name)
    for name in ("SIGINT", "SIGTERM", "SIGHUP")
    if hasattr(signal, name)
)


@contextlib.contextmanager
def _signals_held() -> Iterator[None]:
    """Hold Ctrl-C, SIGTERM and SIGHUP back while the block runs, and deliver them once it ends.

    However the block ends, each signal held is then taken by its own
    handler, set back first, as it would have been, Ctrl-C last: it raises
    ``KeyboardInterrupt`` over whatever the block raised. Only the main
    thread takes signals, and only it may set their handlers; in any other
    no signal can arrive, and the block runs as it is. A handler Python did
    not set, and so could not set back, is left alone.
    """
    if threading.current_thread() is not threading.main_thread():
        yield
        return
    held: list[int] = []
    previous = {}
    for sig in _HELD_SIGNALS:
        if signal.getsignal(sig) is not None:
            previous[sig] = signal.signal(
                sig, lambda signum, _frame: held.append(signum)
            )
    try:
        yield
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
        # Ctrl-C last: its handler raises, and no signal held after it is lost.
        for sig in sorted(set(held), key=lambda sig: sig == signal.SIGINT):
            signal.raise_signal(sig)


def _aside(path: pathlib.Path) -> pathlib.Path:
    """Where *path* is set aside while a clip's files move: beside it, hidden."""
    return path.with_name(f".{path.name}.previous")


def _move_in(
    partials: Sequence[tuple[pathlib.Path, pathlib.Path]],
    stale: Sequence[pathlib.Path],
) -> None:
    """Move each written file to its place, removing *stale*: all of them, or none.

    Every file in the way, a file of the clip or a stale record, is first
    set aside beside itself under a hidden name, then each written file
    moves in, and what was set aside goes only once all have. Each move is
    recorded once it is made, and nothing that would cut one in two arrives
    while they run (:func:`_signals_held`), so whatever stops them half way
    (a file that cannot be moved, an interrupt raised in their place) moves
    back every file that moved before it goes on, and nothing else. A run
    killed during its moves leaves its hidden files behind: they are removed
    first, for every file in the way, whether that file is there or not.

    :raises OSError: when a file cannot be moved, with every file put back
        that can be, or a hidden file left by an earlier run cannot be
        removed.
    """
    # A record of this run may have the name of a stale one: once is enough.
    in_the_way = list(dict.fromkeys([path for _, path in partials] + list(stale)))
    for path in in_the_way:
        _aside(path).unlink(missing_ok=True)
    present = [path for path in in_the_way if path.exists()]
    aside: list[tuple[pathlib.Path, pathlib.Path]] = []
    moved: list[pathlib.Path] = []
    try:
        for path in present:
            kept = _aside(path)
            path.replace(kept)
            aside.append((kept, path))
        for partial, path in partials:
            partial.replace(path)
            moved.append(path)
    except BaseException:
        # Each step goes on past one that fails, and what stopped the moves
        # is what is raised: a file the undo cannot remove is moved over by
        # the earlier run's, when there was one.
        for path in reversed(moved):
            with contextlib.suppress(OSError):
                path.unlink(missing_ok=True)
        for kept, path in reversed(aside):
            with contextlib.suppress(OSError):
                kept.replace(path)
        raise
    for kept, _ in aside:
        # Every file of the clip is in place: one left here stays hidden
        # until the next landing of the clip removes it.
        with contextlib.suppress(OSError):
            kept.unlink(missing_ok=True)


def _land(
    writes: Sequence[tuple[pathlib.Path, bytes]], stale: Sequence[pathlib.Path]
) -> None:
    """Write every file beside its place, then move them all in, removing *stale*, or none.

    The data, the slow part, is all on disk before the first file is
    replaced, so a copy that stops while writing leaves every file as it was.
    The moves run with Ctrl-C, SIGTERM and SIGHUP held back until they are
    done, and are undone if anything else stops them (:func:`_move_in`): a
    clip is never left with files of two runs.

    :raises OSError: when a file cannot be written or moved in, with every
        file as it was.
    """
    partials: list[tuple[pathlib.Path, pathlib.Path]] = []
    try:
        for path, data in writes:
            path.parent.mkdir(parents=True, exist_ok=True)
            partial = path.with_name(f".{path.name}.partial")
            partials.append((partial, path))
            partial.write_bytes(data)
        with _signals_held():
            _move_in(partials, stale)
    finally:
        for partial, _ in partials:
            partial.unlink(missing_ok=True)


def _records(
    clip: str,
    fragments: Sequence[Mapping[str, Any]],
    buffers: Sequence[bytes],
    directory: pathlib.Path,
) -> tuple[list[tuple[pathlib.Path, bytes]], list[pathlib.Path]]:
    """Where the node's language records of *clip* go, and those an earlier run of it left there.

    An earlier record a run killed while it moved them had set aside is
    named by its own name, so that its hidden file goes too (:func:`_move_in`).
    """
    writes = [
        (directory / f"node-{clip}-{entry['name']}", data)
        for entry, data in zip(fragments, buffers, strict=True)
    ]
    left = set(directory.glob(f"node-{clip}-*.json"))
    left.update(
        hidden.with_name(hidden.name[1:].removesuffix(".previous"))
        for hidden in directory.glob(f".node-{clip}-*.json.previous")
    )
    return writes, sorted(left)


def accept(
    header: dict[str, Any],
    buffers: Sequence[bytes],
    *,
    current: Mapping[str, str],
    expect: Expect,
    places: Places,
) -> str | None:
    """Write one clip's files and stamp it; the reason it was not, otherwise.

    *header* is a frame :func:`result_sizes` took, and *buffers* its files.
    The clip's files are replaced together, its language records in place
    of those an earlier run of it left, and only then is it stamped, with
    the fingerprint in *current* it was compared with: those of
    ``expect.tree``, which nothing changes during the run, so they are not
    taken again.

    :raises OSError: when a file cannot be written or moved in, which
        leaves the clip's files on disk as they were; the clip is not
        stamped.
    :raises FileNotFoundError: when the stamp cannot read
        ``engine-digests.json``.
    """
    clip = header["clip"]
    if header.get("ok") is not True:
        # The log tail is the node's text: shown with its control characters escaped.
        return f"{clip}: the node failed it:\n{clip_link.printable(str(header.get('error', '')))}"
    here = current.get(clip)
    if here is None or header.get("fingerprint") != here:
        return (
            f"{clip}: the node rendered other code (fingerprint "
            f"{header.get('fingerprint')!r:.80}, here {here!r}); not copied"
        )
    files, fragments = header["files"], header.get("fragments", [])
    for entry, data in zip((*files, *fragments), buffers, strict=True):
        if not _looks_like(entry["name"], data):
            return f"{clip}: {entry['name']} does not start like its kind of file; not copied"
    target = places.audit if expect.audit_only else places.clips
    writes = [
        (target / entry["name"], data)
        for entry, data in zip(files, buffers[: len(files)], strict=True)
    ]
    stale: list[pathlib.Path] = []
    if places.fragments is not None:
        records, stale = _records(
            clip, fragments, buffers[len(files) :], places.fragments
        )
        writes += records
    _land(writes, stale)
    if not expect.audit_only:
        animation_fingerprint.stamp(
            [clip], expect.tree, encoder=expect.encoder, current=current
        )
    return None


def _refusal(header: Mapping[str, Any]) -> str:
    """Why the node refused the job, in its words with their control characters escaped."""
    reasons = header.get("problems", [])
    listed = reasons if isinstance(reasons, list) else [reasons]
    return "the node cannot render: " + "; ".join(
        clip_link.printable(str(reason)) for reason in listed
    )


def _moved(clip: str, remaining: set[str]) -> list[str]:
    """The problems of a run whose checkout moved as *clip* arrived, with *remaining* still to come.

    A clip still to come may be in the pipe already: it is not read, and the
    node is stopped.
    """
    moved = "the checkout moved during the run"
    return [f"{clip}: {moved}; not copied"] + [
        f"{other}: {moved}; not read; the node was stopped"
        for other in sorted(remaining)
    ]


def receive_all(
    stream: BinaryIO,
    *,
    expect: Expect,
    places: Places,
    current: Mapping[str, str],
    still: Callable[[], bool],
    accepted: Callable[[], None] | None = None,
) -> list[str]:
    """Take every frame the node sends; the problems, one per clip.

    ``still()`` says the checkout is as it was when the run began. A clip
    that arrives after it moved is not copied, and nor would any after it
    be, so the reading stops there: :func:`_talk` then closes the node's
    input, which stops its lanes. A node that stops before it says it is
    done is a problem even when no clip is missing: a check (a job of no
    clips), or a crash after the last clip. *accepted*, when given, is
    called once, when the node shows it took the job: at its first frame
    that is not a refusal, before anything of it is written.

    :raises RuntimeError: when the node refuses the job.
    :raises NodeRunError: for a frame this run did not ask for; the clips
        before it are kept, and the stream is not read further.
    :raises OSError: when a clip's files cannot be written.
    """
    problems: list[str] = []
    remaining = set(expect.clips)
    taken = False
    while True:
        try:
            header, buffers = clip_link.receive(
                stream, lambda h: result_sizes(h, expect)
            )
        except ValueError as exc:
            raise NodeRunError(str(exc)) from exc
        except EOFError:
            missing = [
                f"{c}: the node stopped before sending it" for c in sorted(remaining)
            ]
            return problems + (
                missing or ["the node stopped before it said it was done"]
            )
        if header["type"] == "refused":
            raise RuntimeError(_refusal(header))
        if not taken:
            taken = True
            if accepted is not None:
                accepted()
        if header["type"] == "done":
            return problems + [
                f"{c}: the node never sent it" for c in sorted(remaining)
            ]
        remaining.discard(header["clip"])
        if not still():
            return problems + _moved(header["clip"], remaining)
        reason = accept(header, buffers, current=current, expect=expect, places=places)
        if reason is None:
            sys.stderr.write(f"  {header['clip']}: received\n")
        else:
            problems.append(reason)


def _places_audit() -> pathlib.Path:
    return pathlib.Path(clip_frame_audit.DEFAULT_DIR).resolve()


def _places(*, audit_only: bool) -> Places:
    """Where this run writes what comes back.

    :raises FileNotFoundError: for a render without a checkout of the assets.
    """
    fragments = os.environ.get("PHONOMETRY_FIGURE_LANGUAGE_AUDIT", "").strip()
    audit = _places_audit()
    clips = audit if audit_only else assets_dir.require_clips_dir()
    return Places(
        clips=clips,
        fragments=pathlib.Path(fragments) if fragments else None,
        audit=audit,
    )


def _empty(directory: pathlib.Path) -> None:
    """Remove what *directory* holds, leaving it there and empty."""
    shutil.rmtree(directory, ignore_errors=True)
    directory.mkdir(parents=True)


def _entry(compute: Compute) -> HostEntry:
    """The hosts-file entry of the node *compute* names.

    :raises ValueError: when *compute* names no host, or the hosts file
        does not parse.
    :raises KeyError: for a host the hosts file does not name, or no hosts
        file.
    """
    if compute.host is None:
        msg = "a node run needs a host in PHONOMETRY_COMPUTE"
        raise ValueError(msg)
    return clip_link.host_entry(compute.host)


def _relay(stream: BinaryIO) -> None:
    """Copy the node's standard error here line by line, its control characters escaped.

    ssh brings back what the node writes there (the bootstrap's and the
    node's messages, a traceback); left to reach this terminal as it is, a
    node could write escape sequences to it.
    """
    with contextlib.suppress(OSError, ValueError):
        for raw in iter(functools.partial(stream.readline, _RELAY_BYTES), b""):
            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            sys.stderr.write(f"{clip_link.printable(line)}\n")


def _end(process: subprocess.Popen[bytes], relay: threading.Thread) -> None:
    """Close the node's input, give it :data:`EXIT_GRACE_S` to end, and kill it if it does not.

    Closing its input is how the node is told to stop: it ends every lane's
    process group and removes what it unpacked. Its output is closed first,
    as nothing reads it any more: a node in the middle of sending a clip
    learns it at once, instead of waiting out its grace. ssh leads a session
    of its own, which an interrupt at the terminal does not reach, so it is
    killed here whatever ends the wait, a second interrupt included, or an
    interrupt as the output is closed. Every wait here is bounded.
    """
    try:
        if process.stdout is not None:
            process.stdout.close()
        if process.stdin is not None:
            with contextlib.suppress(OSError):
                process.stdin.close()
        with contextlib.suppress(subprocess.TimeoutExpired):
            process.wait(timeout=EXIT_GRACE_S)
    finally:
        if process.poll() is None:
            process.kill()
            with contextlib.suppress(subprocess.TimeoutExpired):
                process.wait(timeout=_KILLED_S)
        relay.join(timeout=_KILLED_S)
        # A relay still blocked on the stream (held open by a process ssh
        # started) holds its lock: closing it would wait as long.
        if process.stderr is not None and not relay.is_alive():
            process.stderr.close()


def _talk(
    entry: HostEntry,
    compute: Compute,
    header: dict[str, Any],
    data: bytes,
    receive: Callable[[BinaryIO], list[str]],
    spawn: Callable[..., Any],
) -> list[str]:
    """Start the node, send it the bootstrap, the archive and the job, and take its answer.

    Its input stays open while *receive* reads, since closing it cancels
    the run. ssh is started in a session of its own: Ctrl-C at the terminal
    reaches this process alone, which then closes the node's input and
    gives it its grace (:func:`_end`), rather than cutting the connection
    under it. A node that exits before it has read everything leaves a
    broken pipe here; what it said, if anything, is still read, and an exit
    status other than 0 is named.

    :raises FileNotFoundError: when no ``ssh`` is on ``PATH``, or on Windows
        when it was found only in the working directory.
    :raises OSError: when the connection cannot be started; and whatever
        *receive* raises, once the node has ended.
    """
    process = spawn(
        clip_link.node_command(entry, compute),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        relay = threading.Thread(
            target=_relay, args=(process.stderr,), name="clip-node-stderr", daemon=True
        )
        relay.start()
    except BaseException:
        # An interrupt once ssh is handed back, before the try that ends it,
        # reaches this process alone: nothing was sent, so ssh is killed here.
        process.kill()
        with contextlib.suppress(subprocess.TimeoutExpired):
            process.wait(timeout=_KILLED_S)
        raise
    try:
        # The node's loader takes the program first, the program takes the
        # archive, and the unpacked node reads the job.
        with contextlib.suppress(BrokenPipeError):
            clip_link.send_program(process.stdin, clip_node.BOOTSTRAP)
            process.stdin.write(len(data).to_bytes(8, "big") + data)
            clip_link.send(process.stdin, header)
        problems = receive(process.stdout)
    finally:
        _end(process, relay)
    if process.returncode:
        problems.append(f"the node exited with status {process.returncode}")
    return problems


@dataclasses.dataclass(frozen=True)
class NodeRun:
    """What a node run asked for, what went wrong, and whether the node took the job.

    :ivar clips: The clips the node was asked for; empty when every clip
        was fresh and no node was started.
    :ivar problems: One line for each clip that did not land, and for each
        failure of the run.
    :ivar accepted: Whether the node took the job, which it shows by
        sending a clip or saying it is done. Only then does an audit-only
        run empty the audit directory: until it does, what that holds is
        the last run's.
    """

    clips: list[str]
    problems: list[str]
    accepted: bool


def render_on_host(
    compute: Compute,
    *,
    requested: Sequence[str] | None,
    force: bool,
    audit_only: bool,
    encoder: str,
    root: pathlib.Path = _ROOT,
    spawn: Callable[..., Any] = subprocess.Popen,
) -> NodeRun:
    """Render clips on the node *compute* names: what was sent, what went wrong.

    An audit-only run empties the audit directory once the node takes the
    job, and not before: a run that cannot start ssh, or that the node
    refuses or dies before taking, leaves the last audit as it was.

    :raises DirtyTreeError: when the checkout has changes.
    :raises ValueError: for an unknown clip or encoder, a float32
        placement, or a missing host.
    :raises NodeRunError: for an archive over the node's limit, a digest
        file in it that does not hold the engines' digests, or a frame this
        run did not ask for.
    :raises RuntimeError: when the node refuses the job.
    :raises KeyError: for a host the hosts file does not name.
    :raises FileNotFoundError: without a checkout of the assets or
        ``engine-digests.json``, when no ``ssh`` is on ``PATH``, or on
        Windows when it was found only in the working directory.
    :raises OSError: when a clip's files cannot be written.
    :raises tarfile.TarError: when the archive does not unpack here.
    :raises subprocess.CalledProcessError: when *root* is not a checkout.
    :raises subprocess.TimeoutExpired: when git does not answer in time.
    """
    from figures import registry

    if compute.dtype != "float64":
        msg = "the clips are computed in float64; PHONOMETRY_COMPUTE asks for float32"
        raise ValueError(msg)
    refuse_dirty_tree(root)
    head = _head(root)
    data = archive(root, ref=head)
    with tempfile.TemporaryDirectory(prefix="phonometry-sent-") as unpacked:
        # The fingerprints, here and in every stamp, are taken on what the
        # node is sent, which an edit saved during the run does not change.
        tree = _unpack(data, pathlib.Path(unpacked))
        try:
            current = animation_fingerprint.fingerprints(tree)
        except ValueError as exc:
            raise NodeRunError(str(exc)) from exc
        clips = clips_to_render(
            requested,
            force=force or audit_only,
            current=current,
            stamped=animation_fingerprint.read_manifest(),
            encoders=animation_fingerprint.read_encoders(),
            present=check_animation_freshness.published(None),
            weights=registry._ANIM_WEIGHTS,
        )
        if not clips:
            return NodeRun([], [], accepted=False)
        # Everything that can refuse the run is asked before anything of the
        # assets or the audit is deleted or created.
        entry = _entry(compute)
        expect = Expect(
            clips=frozenset(clips),
            encoder=clip_node._encoder(encoder),
            audit_only=audit_only,
            tree=tree,
        )
        header = job_header(
            clips,
            devices=registry._ANIM_DEVICES,
            gpu_bytes=registry._ANIM_GPU_BYTES,
            host_bytes=registry._ANIM_HOST_BYTES,
            compute=clip_link.lane_placement(entry, compute),
            encoder=expect.encoder,
            audit_only=audit_only,
        )
        places = _places(audit_only=audit_only)
        taken: list[bool] = []

        def accepted() -> None:
            if audit_only:
                _empty(places.audit)
            taken.append(True)

        problems = _talk(
            entry,
            compute,
            header,
            data,
            lambda stream: receive_all(
                stream,
                expect=expect,
                places=places,
                current=current,
                still=lambda: unmoved(root, head),
                accepted=accepted,
            ),
            spawn,
        )
    return NodeRun(clips, problems, accepted=bool(taken))


def check_node(
    compute: Compute,
    *,
    encoder: str,
    root: pathlib.Path = _ROOT,
    spawn: Callable[..., Any] = subprocess.Popen,
) -> list[str]:
    """What the node lacks to render clips with *encoder*; empty when it can.

    The node must answer that it is done: one that dies first (an import
    error, a GPU it cannot read) is named with its exit status, and one that
    refuses, or answers with a frame of no job's, is named by what it said;
    none is taken for a yes.

    :raises ValueError: for an encoder that is not a clip encoder, or a
        missing host.
    :raises NodeRunError: for an archive over the node's limit.
    :raises KeyError: for a host the hosts file does not name.
    :raises FileNotFoundError: when no ``ssh`` is on ``PATH``, or on Windows
        when it was found only in the working directory.
    :raises subprocess.CalledProcessError: when *root* is not a checkout.
    :raises subprocess.TimeoutExpired: when git does not answer in time.
    """
    entry = _entry(compute)
    expect = Expect(frozenset(), clip_node._encoder(encoder), audit_only=False)
    header = job_header(
        [],
        devices={},
        gpu_bytes={},
        host_bytes={},
        compute=clip_link.lane_placement(entry, compute),
        encoder=expect.encoder,
        audit_only=False,
    )

    def receive(stream: BinaryIO) -> list[str]:
        try:
            return receive_all(
                stream,
                expect=expect,
                places=Places(root, None, root),
                current={},
                still=lambda: True,
            )
        except (RuntimeError, ValueError) as exc:
            return [str(exc)]

    return _talk(entry, compute, header, archive(root), receive, spawn)


def main_on_host(
    compute: Compute,
    *,
    requested: Sequence[str] | None,
    force: bool,
    audit_only: bool,
    encoder: str,
) -> int:
    """``generate_graphs.py --animations`` with a host: 0 when every clip came back.

    :raises DirtyTreeError: when the checkout has changes.
    :raises ValueError: for an unknown clip or encoder, a float32
        placement, or a missing host.
    :raises NodeRunError: for an archive over the node's limit, a digest
        file in it that does not hold the engines' digests, or a frame this
        run did not ask for.
    :raises RuntimeError: when the node refuses the job.
    :raises KeyError: for a host the hosts file does not name.
    :raises FileNotFoundError: without a checkout of the assets or
        ``engine-digests.json``, when no ``ssh`` is on ``PATH``, or on
        Windows when it was found only in the working directory.
    :raises OSError: when a clip's files cannot be written.
    :raises tarfile.TarError: when the archive does not unpack here.
    :raises subprocess.CalledProcessError: when this is not a checkout.
    :raises subprocess.TimeoutExpired: when git does not answer in time.
    """
    run = render_on_host(
        compute,
        requested=requested,
        force=force,
        audit_only=audit_only,
        encoder=encoder,
    )
    for problem in run.problems:
        sys.stderr.write(f"::error::{problem}\n")
    if not run.clips:
        sys.stderr.write(
            "every clip is fresh; nothing to render (FORCE=1 renders them anyway)\n"
        )
        return 0
    # Until the node takes the job, the audit directory holds the last run's
    # findings, which are not this run's to report.
    reported = audit_only and run.accepted
    status = clip_frame_audit.report(_places_audit(), run.clips) if reported else 0
    return 1 if run.problems else status


def main(argv: list[str] | None = None) -> int:
    """Ask the node in ``PHONOMETRY_COMPUTE`` whether it can render the clips; 0 when it can.

    :raises SystemExit: for arguments this command does not take.
    :raises ValueError: for a ``PHONOMETRY_COMPUTE`` that does not parse or
        names no host.
    :raises NodeRunError: for an archive over the node's limit.
    :raises KeyError: for a host the hosts file does not name.
    :raises FileNotFoundError: when no ``ssh`` is on ``PATH``, or on Windows
        when it was found only in the working directory.
    :raises subprocess.CalledProcessError: when this is not a checkout.
    :raises subprocess.TimeoutExpired: when git does not answer in time.
    """
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        required=True,
        help="ask the node in PHONOMETRY_COMPUTE whether it can render clips",
    )
    parser.add_argument(
        "--clip-encoder",
        choices=animation_fingerprint.CLIP_ENCODERS,
        default=None,
        help="the encoder to ask about; by default NVENC with a GPU, SVT-AV1 on a CPU",
    )
    args = parser.parse_args(argv)
    from phonometry.simulation.compute import _requested

    compute = _requested(None)
    problems = check_node(
        compute, encoder=args.clip_encoder or default_encoder(compute)
    )
    for problem in problems:
        sys.stderr.write(f"{problem}\n")
    if not problems:
        sys.stderr.write("the node can render the clips\n")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
