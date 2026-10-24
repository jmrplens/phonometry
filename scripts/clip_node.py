#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The node side of the clip transport: render clips here, send them back.

``make animations`` with a host in ``PHONOMETRY_COMPUTE`` sends this
checkout, as ``git archive`` of HEAD, to the node named in the hosts file
and runs it there; ``scripts/clip_transport.py`` is the other side. This is
what runs on the node, from the archive itself. A small bootstrap
(:data:`BOOTSTRAP`, standard library only, sent to the node's loader) reads
the archive from stdin, unpacks it into a fresh temporary directory and
hands over, in the same process, to :func:`serve`. That checks that the
node can render what was asked (:func:`readiness`: the encoder, a software
AV1 decoder for the posters and the GIFs, WebP, the pinned figure stack,
an SVT-AV1 the clips were calibrated for or one real NVENC frame, and the
GPU memory and the RAM the clips were measured to need), renders each clip
with ``generate_graphs.py --animations --scratch-dir`` in at most two
lanes, and sends each clip's files back the moment it is finished.

Each lane is a process group of its own, so a cancel reaches everything a
render started: the forked variants, a NumPy worker pool, ffmpeg. A run is
cancelled when the client closes the connection, when this process is sent
SIGTERM or SIGHUP, and when the frames pipe breaks under a send; every lane
is ended before this process goes. The node's GPU and RAM may be shared
with other services, so the lanes divide what is free when the job starts,
not the totals: a lane gets half of each (less room for its CUDA context on
the GPU), and a clip whose recorded needs do not fit half runs alone with
all of it (``clip_placement.lane_fit``); the lanes share the card's NVENC
sessions through ``encode_slots``.
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import importlib.metadata
import json
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
from typing import TYPE_CHECKING, Any, BinaryIO

_ROOT = pathlib.Path(__file__).resolve().parent.parent
for _path in (_ROOT / "scripts", _ROOT / "src"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import animation_fingerprint
import check_animation_freshness
import clip_frame_audit
import clip_link
import clip_placement
import encode_slots

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterator, Mapping, Sequence

#: The version of the job and result headers.
PROTOCOL = 1
#: The largest archive the bootstrap accepts.
ARCHIVE_LIMIT = 256 << 20
#: The most language records one clip's render may send back: one per
#: process that drew (the render, its four variants, a field's worker pool).
MAX_FRAGMENTS = 16

#: The most bytes, once escaped as JSON, of what the node says back: one line
#: of its words, one string (a reason, a problem), and the end of a lane's
#: log; and the most problems one refusal lists. Together they keep every
#: header under half the reader's limit of 1 MiB, where one control character
#: takes six bytes and a character past the Basic Multilingual Plane twelve.
_LINE_BYTES = 2 << 10
_TEXT_BYTES = 8 << 10
_LOG_BYTES = 64 << 10
_MAX_PROBLEMS = 64
#: What marks a line cut short.
_CUT = " [...]"

#: What a node that lacks something it needs is told to do about it.
_REBUILD = (
    "; rebuild the node image (make node-image) or update the node's Python environment"
)

#: ffmpeg's software AV1 decoders, which cut the posters and the GIFs from
#: the encoded WebM. Its own ``av1`` decoder works only through a hardware
#: accelerator, so it does not count.
_AV1_DECODERS = ("libdav1d", "libaom-av1")

#: How long ffmpeg may take to list its codecs, or to encode the one NVENC
#: frame that shows the card can [s]: far past what either takes on a working
#: node, so that only an ffmpeg that hangs is stopped.
_FFMPEG_S = 120

#: The encode that shows the card can: one black frame on NVENC, thrown away.
_NVENC_TRIAL = (
    "-loglevel",
    "error",
    "-f",
    "lavfi",
    "-i",
    "color=c=black:s=2400x1350:d=0.05",
    "-frames:v",
    "1",
    "-c:v",
    "av1_nvenc",
    "-f",
    "null",
    "-",
)

#: The placement the lanes are given: NumPy or a CuPy GPU, with its options.
#: The client sends the device as the node sees it, never a host.
_LANE_COMPUTE = re.compile(r"(?:cpu|cupy(?::\d+)?)(?:,\w+)*\Z", re.ASCII)

#: A clip's name, which names its lane directory and its files.
_CLIP_NAME = re.compile(r"\w+\Z", re.ASCII)

#: The signals that end a node run as a closed input does: a container being
#: stopped (SIGTERM) and a session hanging up (SIGHUP).
_CANCEL_SIGNALS = tuple(
    getattr(signal, name) for name in ("SIGTERM", "SIGHUP") if hasattr(signal, name)
)

#: The thread pools pinned and the hash seed fixed, as `make graphs` does.
_FIGURE_ENV = {
    "OMP_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "NUMBA_NUM_THREADS": "1",
    "VECLIB_MAXIMUM_THREADS": "1",
    "PYTHONHASHSEED": "0",
}

_DEVICES: tuple[clip_placement.ClipDevice, ...] = ("cpu", "gpu", "gpu-whole")

#: The program the client sends the node's loader. Standard library only:
#: it runs before the archive that holds the rest is unpacked. It reads from
#: the same buffered stdin the loader read it from and goes on in the same
#: process, so nothing the client sends after the archive is lost. An
#: archive that does not unpack, or a node that cannot import what it holds,
#: leaves nothing of it behind.
BOOTSTRAP = r"""
import io, os, shutil, sys, tarfile, tempfile
stdin = sys.stdin.buffer
def take(n):
    data = stdin.read(n)
    if len(data) != n:
        sys.exit("clip node: the input ended early")
    return data
frames = os.dup(1)
os.dup2(2, 1)
size = int.from_bytes(take(8), "big")
if not 0 < size <= LIMIT:
    sys.exit("clip node: an archive of %d bytes was refused" % size)
root = tempfile.mkdtemp(prefix="phonometry-clips-")
try:
    with tarfile.open(fileobj=io.BytesIO(take(size)), mode="r:gz") as tar:
        tar.extractall(root, filter="data")
    sys.path[:0] = [os.path.join(root, "scripts"), os.path.join(root, "src")]
    import clip_node
except BaseException:
    shutil.rmtree(root, ignore_errors=True)
    raise
sys.exit(clip_node.main(["--serve", "--frames-fd", str(frames), "--remove-root"]))
""".replace("LIMIT", str(ARCHIVE_LIMIT))


@dataclasses.dataclass(frozen=True)
class ClipJob:
    """One clip to render, where its field is computed, and what it was measured to need.

    :ivar gpu_bytes: The most bytes CuPy's pool held while its field was
        computed (``_ANIM_GPU_BYTES``); 0 when none is recorded.
    :ivar host_bytes: The least RAM its field steps in (``_ANIM_HOST_BYTES``);
        0 when none is recorded.
    """

    name: str
    device: clip_placement.ClipDevice
    gpu_bytes: int = 0
    host_bytes: int = 0


@dataclasses.dataclass(frozen=True)
class Job:
    """What the client asked this node to render."""

    clips: tuple[ClipJob, ...]
    compute: str
    encoder: animation_fingerprint.ClipEncoder
    audit_only: bool

    @classmethod
    def from_header(cls, header: Mapping[str, Any]) -> Job:
        """The job a header describes.

        :raises ValueError: for a header that is not a job of this protocol:
            another type or version, a placement that names a host or a
            device other than NumPy and CuPy, an encoder or a clip device
            the clips do not have, a clip named twice, or a field of the
            wrong kind.
        """
        if header.get("type") != "job" or header.get("version") != PROTOCOL:
            msg = f"not a clip job of version {PROTOCOL}: {header.get('type')!r}, {header.get('version')!r}"
            raise ValueError(msg)
        compute = str(header.get("compute", ""))
        if "@" in compute:
            msg = f"the lanes' placement names no host; got {compute!r}"
            raise ValueError(msg)
        if _LANE_COMPUTE.match(compute) is None:
            msg = f"the lanes' placement is cpu or cupy[:N], with its options; got {compute!r:.80}"
            raise ValueError(msg)
        clips = tuple(_clip(entry) for entry in _entries(header.get("clips")))
        names = [clip.name for clip in clips]
        if len(set(names)) != len(names):
            msg = f"a job names each clip once; got {names!r:.200}"
            raise ValueError(msg)
        audit_only = header.get("audit_only")
        if not isinstance(audit_only, bool):
            msg = f"a job's audit_only is true or false; got {audit_only!r:.80}"
            raise ValueError(msg)
        encoder = _encoder(header.get("encoder"))
        return cls(clips=clips, compute=compute, encoder=encoder, audit_only=audit_only)


def _entries(value: object) -> list[Mapping[str, Any]]:
    """The clips of a job header, one object each.

    :raises ValueError: when they are not a list of objects.
    """
    if not isinstance(value, list) or not all(
        isinstance(entry, dict) for entry in value
    ):
        msg = f"a job's clips are a list of objects; got {value!r:.200}"
        raise ValueError(msg)
    return value


def _clip(entry: Mapping[str, Any]) -> ClipJob:
    """One clip of a job header.

    :raises ValueError: for a name that is not a clip's, a device the clips
        do not have, or a need that is not a count of bytes.
    """
    name = entry.get("name")
    if not isinstance(name, str) or _CLIP_NAME.match(name) is None:
        msg = f"a clip's name is letters, digits and underscores; got {name!r:.80}"
        raise ValueError(msg)
    return ClipJob(
        name,
        _one_of(entry.get("device"), _DEVICES, "device"),
        _bytes(entry, "gpu_bytes"),
        _bytes(entry, "host_bytes"),
    )


def _bytes(entry: Mapping[str, Any], key: str) -> int:
    """The count of bytes *entry* gives *key*, 0 when it gives none.

    :raises ValueError: for anything but a whole number, 0 or more.
    """
    value = entry.get(key, 0)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        msg = f"a clip's {key} is a count of bytes, 0 or more; got {value!r:.80}"
        raise ValueError(msg)
    return value


def _one_of[T: str](value: object, choices: tuple[T, ...], what: str) -> T:
    """The one of *choices* that *value* names.

    :raises ValueError: when it names none of them.
    """
    for choice in choices:
        if value == choice:
            return choice
    msg = f"a clip {what} is one of {', '.join(choices)}; got {value!r:.80}"
    raise ValueError(msg)


def _encoder(value: object) -> animation_fingerprint.ClipEncoder:
    """The clip encoder *value* names.

    :raises ValueError: for a name that is not one of the clip encoders.
    """
    return _one_of(value, animation_fingerprint.CLIP_ENCODERS, "encoder")


def _escaped_size(text: str) -> int:
    """The bytes *text* takes in a frame header, which JSON escapes."""
    return len(json.dumps(text)) - 2


def _cut(line: str) -> str:
    """*line* whole, or its longest start that fits :data:`_LINE_BYTES`, marked."""
    if _escaped_size(line) <= _LINE_BYTES:
        return line
    room = _LINE_BYTES - len(_CUT)
    # Each character takes at least a byte, so no longer start can fit.
    low, high = 0, min(len(line), room)
    while low < high:
        middle = (low + high + 1) // 2
        if _escaped_size(line[:middle]) <= room:
            low = middle
        else:
            high = middle - 1
    return line[:low] + _CUT


def _sendable(text: str, *, limit: int = _TEXT_BYTES) -> str:
    """*text* cut to what a frame carries: each line to :data:`_LINE_BYTES`,
    and as many of its last lines as fit *limit* bytes, both once escaped.

    Every string of the node's own words goes through here before it is sent:
    a lane's log, an ffmpeg or CuPy message, a value echoed from the job.
    """
    kept: list[str] = []
    size = 0
    for whole in reversed(text.splitlines()):
        line = _cut(whole)
        # The newline that joins it to the next takes two bytes.
        size += _escaped_size(line) + 2
        if size > limit:
            break
        kept.append(line)
    return "\n".join(reversed(kept))


def _refusal(problems: Sequence[str]) -> dict[str, Any]:
    """The frame that refuses a job for *problems*, cut to what a frame carries."""
    shown = [_sendable(problem) for problem in problems[:_MAX_PROBLEMS]]
    if len(problems) > _MAX_PROBLEMS:
        shown.append(f"and {len(problems) - _MAX_PROBLEMS} more")
    return {"type": "refused", "problems": shown}


def _listed(listing: str, name: str) -> bool:
    return (
        re.search(rf"^\s*\S+\s+{re.escape(name)}\b", listing, re.MULTILINE) is not None
    )


def _last_line(text: object) -> str:
    """The last line *text* holds, or ``"no message"`` when it holds none."""
    return (str(text or "").strip().splitlines() or ["no message"])[-1]


def _ffmpeg(
    ffmpeg: str, arguments: Sequence[str], run: Callable[..., Any]
) -> subprocess.CompletedProcess[str]:
    """*ffmpeg* run on *arguments*, given :data:`_FFMPEG_S` to finish.

    :raises OSError: when it cannot be started.
    :raises subprocess.TimeoutExpired: when it does not finish in time.
    """
    done: subprocess.CompletedProcess[str] = run(
        [ffmpeg, "-hide_banner", *arguments],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        timeout=_FFMPEG_S,
    )
    return done


def _codec_problems(ffmpeg: str, job: Job, run: Callable[..., Any]) -> list[str]:
    """What the clips need of *ffmpeg* that it does not list.

    :raises OSError: when *ffmpeg* cannot be started.
    :raises subprocess.TimeoutExpired: when it does not list its codecs in time.
    """
    encoders = str(_ffmpeg(ffmpeg, ["-encoders"], run).stdout)
    decoders = str(_ffmpeg(ffmpeg, ["-decoders"], run).stdout)
    needed = ["libwebp"] if job.audit_only else [job.encoder, "libwebp"]
    problems = [
        f"ffmpeg has no {name} encoder{_REBUILD}"
        for name in needed
        if not _listed(encoders, name)
    ]
    if not any(_listed(decoders, name) for name in _AV1_DECODERS):
        problems.append(
            "ffmpeg has no software AV1 decoder (libdav1d or libaom-av1), which the "
            f"posters and the GIFs need{_REBUILD}"
        )
    return problems


def _stack_problems(root: pathlib.Path) -> list[str]:
    """Each package of the pinned figure stack this node has at another version.

    :raises OSError: when *root* has no readable ``requirements-figures.txt``.
    """
    problems: list[str] = []
    for line in (
        (root / "requirements-figures.txt").read_text(encoding="utf-8").splitlines()
    ):
        name, sep, pinned = line.split("#", 1)[0].strip().partition("==")
        if not sep:
            continue
        try:
            here = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            here = "not installed"
        if here != pinned:
            problems.append(f"{name} is {here} on the node, {pinned} pinned{_REBUILD}")
    return problems


def _svt_problems(ffmpeg: str, job: Job, run: Callable[..., Any]) -> list[str]:
    """An SVT-AV1 whose major version the clips' CRF and preset were not calibrated for."""
    if job.audit_only or job.encoder != "libsvtav1":
        return []
    # Imported here: the figure stack is checked first, and it is there.
    from figures import media

    try:
        media._svt_av1_options(media.read_svt_av1_version(ffmpeg, run=run))
    except (ValueError, RuntimeError) as exc:
        return [f"{exc}{_REBUILD}"]
    return []


def _trial_problems(ffmpeg: str, job: Job, run: Callable[..., Any]) -> list[str]:
    """One black frame encoded on NVENC, which only a card the container can use encodes."""
    if job.audit_only or job.encoder != "av1_nvenc":
        return []
    try:
        trial = _ffmpeg(ffmpeg, _NVENC_TRIAL, run)
    except (OSError, subprocess.TimeoutExpired) as exc:
        reason = str(exc)
    else:
        if trial.returncode == 0:
            return []
        reason = _last_line(trial.stderr)
    return [f"a one-frame av1_nvenc encode failed: {reason}"]


def preflight(
    root: pathlib.Path,
    job: Job,
    *,
    run: Callable[..., Any] = subprocess.run,
    which: Callable[[str], str | None] = shutil.which,
) -> list[str]:
    """What this node lacks to render *job*; empty when it can.

    Checked before a frame is drawn: a node that cannot encode would
    otherwise fail each clip after its field and its frame audit.

    :raises OSError: when *root* has no readable ``requirements-figures.txt``.
    """
    ffmpeg = which("ffmpeg")
    if ffmpeg is None:
        return [f"ffmpeg is not on PATH{_REBUILD}"]
    try:
        problems = _codec_problems(ffmpeg, job, run)
    except (OSError, subprocess.TimeoutExpired) as exc:
        problems = [f"ffmpeg did not list its codecs: {exc}{_REBUILD}"]
    problems += _stack_problems(root)
    if problems:
        return problems
    return _svt_problems(ffmpeg, job, run) + _trial_problems(ffmpeg, job, run)


def _device_index(compute: str) -> int:
    head = compute.split(",")[0]
    _, _, index = head.partition(":")
    return int(index or 0)


def gpu_bytes(job: Job, *, run: Callable[..., Any] = subprocess.run) -> int:
    """The memory free on the job's GPU as it starts; 0 when the job steps nothing on one.

    What other processes on the node hold is not the lanes' to take. A check
    (a job of no clips) asks too, so a node whose GPU cannot be read says so
    before a render is sent to it.

    :raises subprocess.CalledProcessError: when CuPy cannot say.
    :raises subprocess.TimeoutExpired: when it does not say in time.
    :raises ValueError: when its answer is not a count of bytes.
    """
    on_cpu = job.compute.split(",")[0].split(":")[0] == "cpu"
    if on_cpu or (job.clips and all(c.device == "cpu" for c in job.clips)):
        return 0
    return clip_placement.free_gpu_bytes(_device_index(job.compute), run=run)


@dataclasses.dataclass(frozen=True)
class Room:
    """What the node has free as the job starts, beside its other users.

    :ivar gpu: Bytes free on the job's GPU; 0 when no clip steps on one.
    :ivar host: Bytes of RAM available; None when they cannot be read.
    """

    gpu: int
    host: int | None


#: No GPU to share and the RAM unknown: every clip shares, nothing is capped.
_NO_ROOM = Room(gpu=0, host=None)


def plan(job: Job, room: Room) -> tuple[dict[str, bool], list[str]]:
    """Which clips run alone, and why any clip cannot run at all.

    A clip shares the GPU and the RAM with the other lane when its recorded
    needs fit half of what is free, runs alone when they fit only all of it,
    and is refused, with the whole job, when they do not fit that either.
    """
    alone: dict[str, bool] = {}
    problems: list[str] = []
    for clip in job.clips:
        alone[clip.name], reasons = clip_placement.lane_fit(
            clip.name,
            clip.device,
            gpu_need=clip.gpu_bytes,
            host_need=clip.host_bytes,
            free_gpu=room.gpu,
            available=room.host,
        )
        problems.extend(reasons)
    return alone, problems


def _unreadable(job: Job, exc: Exception) -> str:
    detail = exc.stderr if isinstance(exc, subprocess.CalledProcessError) else exc
    return (
        f"the free memory of GPU {_device_index(job.compute)} could not be read "
        f"through CuPy: {_last_line(detail)}"
    )


def readiness(
    root: pathlib.Path,
    job: Job,
    *,
    run: Callable[..., Any] = subprocess.run,
    which: Callable[[str], str | None] = shutil.which,
    available: Callable[[], int | None] = clip_placement.host_bytes,
) -> tuple[list[str], Room, dict[str, bool]]:
    """Why this node cannot render *job* now, what it has free, and which clips run alone.

    Asked before a frame is drawn. A GPU whose free memory cannot be read
    (CuPy missing on a Python node, a CUDA error, a probe that hangs) is a
    refusal like the rest, never a crash the client would have to guess at.

    :raises OSError: when *root* has no readable ``requirements-figures.txt``.
    :raises ValueError: when ``PHONOMETRY_CLIP_HOST_BYTES`` is set here to
        anything but a positive count of bytes.
    """
    problems = preflight(root, job, run=run, which=which)
    if problems:
        return problems, _NO_ROOM, {}
    try:
        free = gpu_bytes(job, run=run)
    except (subprocess.SubprocessError, OSError, ValueError) as exc:
        return [_unreadable(job, exc)], _NO_ROOM, {}
    room = Room(gpu=free, host=available())
    alone, problems = plan(job, room)
    return problems, room, alone


def lane_argv(
    root: pathlib.Path, clip: ClipJob, directory: pathlib.Path, job: Job
) -> list[str]:
    """The render of one clip, into its own scratch directory."""
    argv = [
        sys.executable,
        str(root / "scripts" / "generate_graphs.py"),
        "--animations",
        "--anim",
        clip.name,
        "--scratch-dir",
        str(directory),
        "--jobs",
        "1",
        "--clip-encoder",
        job.encoder,
    ]
    return [*argv, "--audit-only"] if job.audit_only else argv


def _first_gpu(compute: str, inherited: str | None) -> tuple[str, str | None]:
    """The lanes' placement on CuPy's GPU 0, and the ``CUDA_VISIBLE_DEVICES`` that makes it GPU *N*.

    A scene's own device arithmetic runs on CuPy's current device, GPU 0, so
    the clips step on index 0 (``clip_placement.compute_for`` refuses another);
    GPU *N* is made the first by showing a lane only that one. A Docker
    node already shows its one GPU as index 0. Where ``CUDA_VISIBLE_DEVICES``
    already narrows the GPUs, *N* counts among those.
    """
    head, sep, options = compute.partition(",")
    device, _, index = head.partition(":")
    if device != "cupy" or index in ("", "0"):
        return compute, None
    shown = inherited.split(",") if inherited else None
    return device + sep + options, shown[int(index)] if shown else index


def lane_env(
    root: pathlib.Path,
    clip: ClipJob,
    directory: pathlib.Path,
    job: Job,
    *,
    room: Room,
    alone: bool,
) -> dict[str, str]:
    """The environment one lane renders in: its placement, its budgets and the NVENC slots."""
    env = {**os.environ, **_FIGURE_ENV}
    env["PYTHONPATH"] = str(root / "src")
    env["PHONOMETRY_COMPUTE"], visible = _first_gpu(
        job.compute, os.environ.get("CUDA_VISIBLE_DEVICES")
    )
    if visible is not None:
        env["CUDA_VISIBLE_DEVICES"] = visible
    env["PHONOMETRY_FIGURE_LANGUAGE_AUDIT"] = str(directory / "fragments")
    env[encode_slots.SLOTS_ENV] = (
        f"{root / '.encode-slots'}:{encode_slots.NVENC_SESSIONS}"
    )
    env.pop(clip_placement.GPU_BYTES_ENV, None)
    env.pop(clip_placement.HOST_BYTES_ENV, None)
    if clip.device != "cpu" and room.gpu > 0:
        env[clip_placement.GPU_BYTES_ENV] = str(
            clip_placement.gpu_budget(room.gpu, alone=alone)
        )
    if room.host is not None:
        env[clip_placement.HOST_BYTES_ENV] = str(
            clip_placement.host_share(room.host, alone=alone)
        )
    return env


def _popen(
    argv: list[str], env: dict[str, str], cwd: pathlib.Path, log: pathlib.Path
) -> subprocess.Popen[bytes]:
    with log.open("wb") as sink:
        return subprocess.Popen(
            argv,
            env=env,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=sink,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )


@dataclasses.dataclass
class _Lane:
    clip: ClipJob
    directory: pathlib.Path
    process: Any
    log: pathlib.Path


def _admissible(
    clip: ClipJob, running: Sequence[_Lane], alone: Mapping[str, bool]
) -> bool:
    if len(running) >= clip_placement.LANES:
        return False
    if alone.get(clip.name, False):
        return not running
    return not any(alone.get(lane.clip.name, False) for lane in running)


# A lane's process is a Popen in a render and a stand-in in the scheduling test.
def _signal_group(process: Any, sig: signal.Signals) -> None:  # noqa: ANN401
    """Send *sig* to the process group *process* leads, and to nothing else.

    A lane leads a group of its own, so a pid of 0 or 1, or this process's
    own group, is never a lane's, and is left alone.
    """
    pid = process.pid
    if not isinstance(pid, int) or pid <= 1 or pid == os.getpgrp():
        return
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(pid, sig)


def stop(running: Sequence[_Lane], *, grace_s: float = 5.0) -> None:
    """End every running lane and everything it started.

    Each lane's process group is sent SIGTERM, and SIGKILL once its render
    has had *grace_s* to go, which also ends whatever it left behind. No
    wait is unbounded: a process the kernel cannot end at once (one held in
    the GPU driver) is left to it rather than waited for.
    """
    for lane in running:
        _signal_group(lane.process, signal.SIGTERM)
    for lane in running:
        with contextlib.suppress(subprocess.TimeoutExpired):
            lane.process.wait(timeout=grace_s)
        _signal_group(lane.process, signal.SIGKILL)
        with contextlib.suppress(subprocess.TimeoutExpired):
            lane.process.wait(timeout=grace_s)


def _outputs(directory: pathlib.Path, clip: str, job: Job) -> list[pathlib.Path]:
    if job.audit_only:
        return [
            directory
            / "audit"
            / f"{clip_frame_audit.drawing_name(clip, lang, dark=dark)}.json"
            for lang, dark in clip_frame_audit.VARIANTS
        ]
    return [
        directory / "clips" / name for name in check_animation_freshness.outputs(clip)
    ]


def _log_tail(log: pathlib.Path) -> str:
    """The end of *log*, at most :data:`_LOG_BYTES` of it; empty when there is none.

    Only the end is read: a byte read takes at least a byte once escaped, so
    more could never be sent. A first line read in part is left out.

    :raises OSError: when the log is there but cannot be read.
    """
    try:
        with log.open("rb") as stream:
            start = max(0, stream.seek(0, os.SEEK_END) - _LOG_BYTES)
            stream.seek(start)
            data = stream.read(_LOG_BYTES)
    except FileNotFoundError:
        return ""
    if start and b"\n" in data:
        data = data.split(b"\n", 1)[1]
    return data.decode("utf-8", errors="replace")


def _failure(clip: str, reason: str, log: pathlib.Path) -> dict[str, Any]:
    """The frame that says *clip* failed: why, and the end of its lane's log.

    :raises OSError: when the log is there but cannot be read.
    """
    tail = _sendable(_log_tail(log), limit=_LOG_BYTES)
    error = _sendable(reason)
    return {
        "type": "clip",
        "clip": clip,
        "ok": False,
        "error": f"{error}\n{tail}" if tail else error,
    }


def _why_failed(
    lane: _Lane, files: list[pathlib.Path], fragments: list[pathlib.Path], job: Job
) -> str | None:
    missing = [path.name for path in files if not path.is_file()]
    if lane.process.returncode != 0 and not (job.audit_only and not missing):
        return f"the render exited with {lane.process.returncode}"
    if missing:
        return f"the render left out {', '.join(missing)}"
    if len(fragments) > MAX_FRAGMENTS:
        return f"the render left {len(fragments)} language records, more than {MAX_FRAGMENTS}"
    return None


def collect(
    lane: _Lane, job: Job, fingerprints: Mapping[str, str]
) -> tuple[dict[str, Any], list[bytes]]:
    """The result of a finished lane, and its files; the lane's directory goes.

    :raises OSError: when a file the render left cannot be read.
    """
    name = lane.clip.name
    try:
        files = _outputs(lane.directory, name, job)
        fragments = sorted((lane.directory / "fragments").glob("*.json"))
        reason = _why_failed(lane, files, fragments, job)
        if reason is not None:
            return _failure(name, reason, lane.log), []
        header: dict[str, Any] = {
            "type": "clip",
            "clip": name,
            "ok": True,
            "fingerprint": fingerprints.get(name, ""),
            "encoder": job.encoder,
            "files": [{"name": p.name, "size": p.stat().st_size} for p in files],
            "fragments": [
                {"name": p.name, "size": p.stat().st_size} for p in fragments
            ],
        }
        return header, [path.read_bytes() for path in (*files, *fragments)]
    finally:
        shutil.rmtree(lane.directory, ignore_errors=True)


def _start(
    root: pathlib.Path,
    job: Job,
    clip: ClipJob,
    room: Room,
    start: Callable[..., Any],
    *,
    alone: bool,
) -> _Lane:
    directory = root / "lanes" / clip.name
    directory.mkdir(parents=True, exist_ok=True)
    log = directory / "log.txt"
    process = start(
        lane_argv(root, clip, directory, job),
        lane_env(root, clip, directory, job, room=room, alone=alone),
        root,
        log,
    )
    return _Lane(clip, directory, process, log)


def run_lanes(
    root: pathlib.Path,
    job: Job,
    *,
    cancel: threading.Event,
    fingerprints: Mapping[str, str],
    room: Room = _NO_ROOM,
    alone: Mapping[str, bool] | None = None,
    start: Callable[..., Any] = _popen,
) -> Generator[tuple[dict[str, Any], list[bytes]], None, None]:
    """Render the job's clips, two at a time, yielding each as it finishes.

    A clip that runs alone (*alone*, from :func:`plan`) starts only when no
    lane runs, and nothing starts beside it. However this ends (every clip
    done, *cancel* set, or the generator closed because a send failed), every
    lane still running is stopped, with everything it started, before it
    returns.

    :raises OSError: when a lane cannot be started, or a finished lane's
        files cannot be read; the other lanes are stopped first.
    """
    solo = alone or {}
    pending = list(job.clips)
    running: list[_Lane] = []
    try:
        while pending or running:
            if cancel.is_set():
                return
            while pending and _admissible(pending[0], running, solo):
                clip = pending.pop(0)
                running.append(
                    _start(
                        root, job, clip, room, start, alone=solo.get(clip.name, False)
                    )
                )
            done = [lane for lane in running if lane.process.poll() is not None]
            for lane in done:
                running.remove(lane)
                # What the render left running goes with it: a variant or a
                # worker of a render that was killed. Its group's id stays
                # taken while any of them lives.
                _signal_group(lane.process, signal.SIGKILL)
                yield collect(lane, job, fingerprints)
            if not done:
                cancel.wait(0.5)
    finally:
        stop(running)


def deliver(
    out: BinaryIO, results: Generator[tuple[dict[str, Any], list[bytes]], None, None]
) -> None:
    """Send each finished clip; whatever stops the sending stops the lanes too.

    A frames pipe that breaks under a send (the client killed mid-send)
    raises out of the loop, and closing the generator runs
    :func:`run_lanes`' ``finally``, which ends every lane's process group
    before the error goes on.

    :raises OSError: when a send fails (a ``BrokenPipeError`` for a reader
        that is gone), once every lane is ended.
    """
    with contextlib.closing(results):
        for result, buffers in results:
            clip_link.send(out, result, buffers)
            sys.stderr.write(
                f"clip node: {result['clip']} {'done' if result['ok'] else 'failed'}\n"
            )


@contextlib.contextmanager
def cancelled_by_signals(cancel: threading.Event) -> Iterator[None]:
    """While the block runs, SIGTERM and SIGHUP set *cancel* instead of ending this process.

    Ended outright, the node would leave its lanes running: each is a
    process group of its own, which a signal to this process does not reach.
    As a cancel, :func:`run_lanes` stops them first.
    """

    def _cancel(_signum: int, _frame: object) -> None:
        cancel.set()

    previous = {sig: signal.signal(sig, _cancel) for sig in _CANCEL_SIGNALS}
    try:
        yield
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def _watch(fd: int, cancel: threading.Event) -> None:
    """Set *cancel* when the client goes away, which closes its end of stdin.

    It reads the descriptor *fd*, not the buffered stream the job came
    through: a daemon thread blocked inside that stream holds its lock, and
    the interpreter aborts on that lock when it exits after the last frame.
    """
    with contextlib.suppress(OSError):
        while os.read(fd, 1 << 16):
            pass
    cancel.set()


def _job_sizes(header: dict[str, Any]) -> list[int]:
    """The buffers of the job frame: none.

    :raises ValueError: when the first frame is not a job.
    """
    if header.get("type") != "job":
        msg = f"the first frame is the job; got {header.get('type')!r}"
        raise ValueError(msg)
    return []


def _read_job(stdin: BinaryIO) -> Job:
    """The job the client sends first, after the archive.

    :raises EOFError: when the input breaks before the job frame is whole.
    :raises ValueError: when that frame is not a clip job this node can read.
    """
    header, _ = clip_link.receive(stdin, _job_sizes)
    return Job.from_header(header)


def serve(frames_fd: int) -> int:
    """Read the job, render it, send each clip back; 0 when every clip was sent.

    A job this node cannot read, or cannot render now, is answered with a
    refusal, and 1. A run that is cancelled (the client gone, SIGTERM or
    SIGHUP) ends every lane and returns 130 with no end frame.

    :raises EOFError: when the input breaks before the job frame is whole.
    :raises OSError: when the frames pipe breaks under a send, once every
        lane is ended, or when the archive lacks a file the node reads.
    """
    # Buffered, as the remote machinery's own frames are: a raw descriptor
    # may take part of a write and leave the rest of a frame unsent.
    with os.fdopen(frames_fd, "wb") as out:
        return _serve(out, sys.stdin.buffer)


def _serve(out: BinaryIO, stdin: BinaryIO) -> int:
    """:func:`serve` on the frames stream *out* and the client's *stdin*.

    :raises EOFError: when the input breaks before the job frame is whole.
    :raises OSError: when the frames pipe breaks under a send, once every
        lane is ended, or when the archive lacks a file the node reads.
    """
    try:
        job = _read_job(stdin)
    except ValueError as exc:
        clip_link.send(out, _refusal([str(exc)]))
        return 1
    cancel = threading.Event()
    with cancelled_by_signals(cancel):
        problems, room, alone = readiness(_ROOT, job)
        if problems:
            clip_link.send(out, _refusal(problems))
            return 1
        fingerprints = animation_fingerprint.fingerprints(_ROOT)
        threading.Thread(
            target=_watch, args=(stdin.fileno(), cancel), daemon=True
        ).start()
        deliver(
            out,
            run_lanes(
                _ROOT,
                job,
                cancel=cancel,
                fingerprints=fingerprints,
                room=room,
                alone=alone,
            ),
        )
    if cancel.is_set():
        return 130
    clip_link.send(out, {"type": "done"})
    return 0


def _check_package() -> None:
    """Stop unless ``phonometry`` comes from the archive.

    :raises SystemExit: when it was imported from anywhere else.
    """
    import phonometry

    where = pathlib.Path(phonometry.__file__).resolve()
    if _ROOT / "src" not in where.parents:
        sys.exit(
            f"clip node: phonometry was imported from {where}, not from the archive"
        )


def _removable(root: pathlib.Path) -> bool:
    return (
        root.name.startswith("phonometry-clips-")
        and root.parent == pathlib.Path(tempfile.gettempdir()).resolve()
    )


def main(argv: list[str] | None = None) -> int:
    """Serve one clip job on the descriptor the bootstrap kept for the frames.

    :raises SystemExit: for arguments that are not the bootstrap's, or when
        ``phonometry`` does not come from the archive.
    """
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--serve", action="store_true", required=True)
    parser.add_argument("--frames-fd", type=int, required=True)
    parser.add_argument(
        "--remove-root",
        action="store_true",
        help="remove the unpacked archive when done",
    )
    args = parser.parse_args(argv)
    try:
        _check_package()
        return serve(args.frames_fd)
    finally:
        if args.remove_root and _removable(_ROOT):
            shutil.rmtree(_ROOT, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
