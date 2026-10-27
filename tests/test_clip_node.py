#  Copyright (c) 2026. Jose Manuel Requena Plens
"""What a render node does with a clip job, without a GPU or a real render.

The node (``scripts/clip_node.py``) unpacks the archive it is sent, refuses
a job it cannot render before drawing a frame, renders the clips in at most
two lanes, each a process group of its own, and sends each clip back as it
finishes. The renders are stood in for by small Python processes here; what
is under test is the scheduling, the refusal, the failure of one lane, the
end of every lane however the run stops (a cancel, a broken frames pipe, a
signal), and a node that exits cleanly while its client still holds the
connection open, not the drawing.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import pathlib
import re
import signal
import subprocess
import sys
import tarfile
import threading
import time
import types
from typing import TYPE_CHECKING, Any

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))

import check_animation_freshness
import clip_node
import clip_placement
import encode_slots
from figures import media

from phonometry.simulation._remote import bootstrap

if TYPE_CHECKING:
    from collections.abc import Callable

pytestmark = [
    # The node reads the frame audit, which brings in the figure stack.
    pytest.mark.pinned_stack,
    pytest.mark.skipif(sys.platform == "win32", reason="a render node is POSIX"),
]

_FREE = 6 << 30
_RAM = 12 << 30


def _job(
    *clips: tuple[Any, ...],
    encoder: str = "av1_nvenc",
    audit: bool = False,
    compute: str = "cupy:0",
) -> clip_node.Job:
    """A job of ``(name, device)`` or ``(name, device, gpu_bytes, host_bytes)`` clips."""
    keys = ("name", "device", "gpu_bytes", "host_bytes")
    return clip_node.Job.from_header(
        {
            "type": "job",
            "version": clip_node.PROTOCOL,
            "clips": [
                dict(zip(keys, (*clip, 0, 0)[:4], strict=True)) for clip in clips
            ],
            "compute": compute,
            "encoder": encoder,
            "audit_only": audit,
        }
    )


@pytest.mark.parametrize(
    ("change", "match"),
    [
        ({"type": "result"}, r"not a clip job"),
        ({"version": 99}, r"not a clip job"),
        ({"compute": "cupy@nas"}, r"names no host"),
        ({"encoder": "libvpx-vp9"}, r"encoder"),
        ({"clips": [{"name": "anim_x", "device": "tpu"}]}, r"device"),
        (
            {"clips": [{"name": "anim_x", "device": "gpu", "gpu_bytes": -1}]},
            r"gpu_bytes",
        ),
        ({"compute": "torch:cuda"}, r"cpu or cupy"),
        ({"clips": "anim_x"}, r"list of objects"),
        ({"clips": [{"name": "../anim_x", "device": "cpu"}]}, r"name"),
        ({"clips": [{"name": "anim_x", "device": "cpu"}] * 2}, r"each clip once"),
        ({"audit_only": "no"}, r"audit_only"),
    ],
)
def test_a_job_header_that_is_not_a_job_is_refused(
    change: dict[str, Any], match: str
) -> None:
    header = {
        "type": "job",
        "version": clip_node.PROTOCOL,
        "clips": [{"name": "anim_x", "device": "gpu", "gpu_bytes": 1, "host_bytes": 0}],
        "compute": "cupy:0",
        "encoder": "av1_nvenc",
        "audit_only": False,
    }
    with pytest.raises(ValueError, match=match):
        clip_node.Job.from_header({**header, **change})


class _Run:
    """A stand-in for subprocess.run that answers ffmpeg's listings and its trial encodes."""

    def __init__(
        self,
        encoders: str,
        decoders: str,
        *,
        trial_fails: bool = False,
        svt: str = "4.2.0",
    ) -> None:
        self.calls: list[list[str]] = []
        self._encoders, self._decoders = encoders, decoders
        self._fails, self._svt = trial_fails, svt

    def __call__(
        self, argv: list[str], **_: object
    ) -> subprocess.CompletedProcess[str]:
        self.calls.append(argv)
        if "-encoders" in argv:
            return subprocess.CompletedProcess(argv, 0, self._encoders, "")
        if "-decoders" in argv:
            return subprocess.CompletedProcess(argv, 0, self._decoders, "")
        if "libsvtav1" in argv:
            message = f"Svt[info]: SVT [version]:\tSVT-AV1 Encoder Lib v{self._svt}\n"
            return subprocess.CompletedProcess(argv, 0, "", message)
        return subprocess.CompletedProcess(
            argv, 1 if self._fails else 0, "", "no NVENC capable devices found"
        )


_ALL_ENCODERS = " V....D av1_nvenc   NVIDIA NVENC av1\n V....D libsvtav1   SVT-AV1\n V....D libwebp   WebP\n"
_ALL_DECODERS = " V....D libdav1d   dav1d AV1 decoder\n"
_FFMPEG = "/usr/bin/ffmpeg"


def _pinned_root(
    tmp_path: pathlib.Path, *, matplotlib: str | None = None
) -> pathlib.Path:
    import importlib.metadata

    version = matplotlib or importlib.metadata.version("matplotlib")
    (tmp_path / "requirements-figures.txt").write_text(
        f"# figure stack\nmatplotlib=={version}\n", encoding="utf-8"
    )
    return tmp_path


def test_a_node_without_what_a_clip_needs_refuses_before_rendering(
    tmp_path: pathlib.Path,
) -> None:
    run = _Run(" V....D libsvtav1   SVT-AV1\n", " V....D h264   H.264\n")
    problems = clip_node.preflight(
        _pinned_root(tmp_path, matplotlib="0.0.1"),
        _job(("anim_x", "gpu")),
        run=run,
        which=lambda name: _FFMPEG,
    )
    text = "\n".join(problems)
    assert "no av1_nvenc encoder" in text
    assert "no libwebp encoder" in text
    assert "no software AV1 decoder" in text
    assert "matplotlib" in text
    assert all("rebuild the node image" in problem for problem in problems)
    assert not any("-c:v" in call for call in run.calls), (
        "no trial encode before the listings pass"
    )


def test_ffmpeg_s_own_av1_decoder_is_not_enough(tmp_path: pathlib.Path) -> None:
    """It decodes only through a hardware accelerator; the posters need a software one."""
    run = _Run(_ALL_ENCODERS, " V....D av1   Alliance for Open Media AV1\n")
    problems = clip_node.preflight(
        _pinned_root(tmp_path),
        _job(("anim_x", "gpu")),
        run=run,
        which=lambda name: _FFMPEG,
    )
    assert len(problems) == 1
    assert "no software AV1 decoder (libdav1d or libaom-av1)" in problems[0]


def test_a_node_without_ffmpeg_says_so(tmp_path: pathlib.Path) -> None:
    problems = clip_node.preflight(
        _pinned_root(tmp_path),
        _job(("anim_x", "cpu")),
        run=_Run("", ""),
        which=lambda name: None,
    )
    assert problems == [f"ffmpeg is not on PATH{clip_node._REBUILD}"]


def test_a_node_with_everything_tries_one_nvenc_frame(tmp_path: pathlib.Path) -> None:
    run = _Run(_ALL_ENCODERS, _ALL_DECODERS)
    assert (
        clip_node.preflight(
            _pinned_root(tmp_path),
            _job(("anim_x", "gpu")),
            run=run,
            which=lambda name: _FFMPEG,
        )
        == []
    )
    assert any("av1_nvenc" in call and "-frames:v" in call for call in run.calls)


def test_a_failed_nvenc_frame_is_a_refusal(tmp_path: pathlib.Path) -> None:
    run = _Run(_ALL_ENCODERS, _ALL_DECODERS, trial_fails=True)
    problems = clip_node.preflight(
        _pinned_root(tmp_path),
        _job(("anim_x", "gpu")),
        run=run,
        which=lambda name: _FFMPEG,
    )
    assert problems == [
        "a one-frame av1_nvenc encode failed: no NVENC capable devices found"
    ]


def test_an_svt_av1_the_clips_were_not_calibrated_for_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """CRF and presets change meaning between SVT-AV1 majors."""
    job = _job(("anim_x", "cpu"), encoder="libsvtav1")
    stale = _Run(_ALL_ENCODERS, _ALL_DECODERS, svt="99.0.0")
    (problem,) = clip_node.preflight(
        _pinned_root(tmp_path), job, run=stale, which=lambda name: _FFMPEG
    )
    assert "SVT-AV1 is 99.0.0" in problem
    assert "rebuild the node image" in problem
    major = min(media._SVT_AV1_CALIBRATED)
    calibrated = _Run(_ALL_ENCODERS, _ALL_DECODERS, svt=f"{major}.0.0")
    assert (
        clip_node.preflight(
            _pinned_root(tmp_path), job, run=calibrated, which=lambda name: _FFMPEG
        )
        == []
    )


def test_a_gpu_that_cannot_be_read_is_a_refusal(tmp_path: pathlib.Path) -> None:
    """A node without CuPy, or whose CUDA fails, answers with a refusal, not a crash."""
    listings = _Run(_ALL_ENCODERS, _ALL_DECODERS)

    def run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if argv[1:2] == ["-c"]:
            raise subprocess.CalledProcessError(
                1,
                argv,
                output="",
                stderr="ModuleNotFoundError: No module named 'cupy'\n",
            )
        return listings(argv, **kwargs)

    problems, room, alone = clip_node.readiness(
        _pinned_root(tmp_path),
        _job(("anim_x", "gpu", 1 << 30, 0)),
        run=run,
        which=lambda name: _FFMPEG,
        available=lambda: _RAM,
    )
    assert problems == [
        "the free memory of GPU 0 could not be read through CuPy: "
        "ModuleNotFoundError: No module named 'cupy'"
    ]
    assert (room, alone) == (clip_node.Room(0, None), {})


def test_a_gpu_the_node_does_not_show_is_a_refusal(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A node whose CUDA_VISIBLE_DEVICES lists fewer GPUs than the index sent.

    With no clip on a GPU, nothing asks CuPy, and the lanes' environment
    would be the first to look: the job is refused before a lane starts.
    """
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "0")
    job = _job(("anim_x", "cpu"), compute="cupy:2")
    problems, room, alone = clip_node.readiness(
        _pinned_root(tmp_path),
        job,
        run=_Run(_ALL_ENCODERS, _ALL_DECODERS),
        which=lambda name: _FFMPEG,
        available=lambda: _RAM,
    )
    assert problems == [
        "the lanes are placed on GPU 2, and CUDA_VISIBLE_DEVICES shows this "
        "node only 1: '0'"
    ]
    assert (room, alone) == (clip_node.Room(0, None), {})
    lane, room = tmp_path / "lane", clip_node.Room(0, _RAM)
    with pytest.raises(ValueError, match=r"placed on GPU 2"):
        clip_node.lane_env(tmp_path, job.clips[0], lane, job, room=room, alone=False)


@pytest.mark.parametrize(
    "failure",
    [
        PermissionError(13, "Permission denied", "/sys/fs/cgroup/memory.current"),
        ValueError("/proc/meminfo has a MemAvailable line that is not a count of kB"),
    ],
    ids=["unreadable", "malformed"],
)
def test_ram_that_cannot_be_read_is_a_refusal(
    tmp_path: pathlib.Path, failure: Exception
) -> None:
    """A node whose memory files cannot be read answers with a refusal, not a crash."""

    def available() -> int | None:
        raise failure

    problems, room, alone = clip_node.readiness(
        _pinned_root(tmp_path),
        _job(("anim_x", "cpu")),
        run=_Run(_ALL_ENCODERS, _ALL_DECODERS),
        which=lambda name: _FFMPEG,
        available=available,
    )
    assert problems == [f"the RAM free on this node could not be read: {failure}"]
    assert (room, alone) == (clip_node.Room(0, None), {})


def test_a_node_with_no_ram_left_refuses_the_job_before_a_lane_has_a_budget(
    tmp_path: pathlib.Path,
) -> None:
    """A lane's RAM budget is never 0, which the lane would refuse as no budget at all."""
    job = _job(("anim_x", "cpu"), ("anim_y", "gpu", 1 << 30, 0))
    alone, problems = clip_node.plan(job, clip_node.Room(gpu=_FREE, host=0))
    assert problems == [
        "anim_x would hold no RAM: 0 MiB is available",
        "anim_y would hold no RAM: 0 MiB is available",
    ]
    alone, problems = clip_node.plan(job, clip_node.Room(gpu=_FREE, host=1))
    assert (alone, problems) == ({"anim_x": True, "anim_y": True}, [])
    room = clip_node.Room(gpu=_FREE, host=1)
    budgets = {
        clip.name: clip_node.lane_env(
            tmp_path, clip, tmp_path / clip.name, job, room=room, alone=alone[clip.name]
        )[clip_placement.HOST_BYTES_ENV]
        for clip in job.clips
    }
    assert budgets == {"anim_x": "1", "anim_y": "1"}


@pytest.mark.parametrize(
    ("device", "share", "gpu_budget", "host_budget"),
    [
        ("cpu", "half", None, str(_RAM // 2)),
        ("gpu", "half", str(_FREE // 2 - clip_placement.CONTEXT_BYTES), str(_RAM // 2)),
        ("gpu-whole", "all", str(_FREE - clip_placement.CONTEXT_BYTES), str(_RAM)),
    ],
)
def test_each_lane_gets_its_budget_its_slots_and_no_host(
    tmp_path: pathlib.Path,
    device: str,
    share: str,
    gpu_budget: str | None,
    host_budget: str,
) -> None:
    job = _job(("anim_x", device))
    env = clip_node.lane_env(
        tmp_path,
        job.clips[0],
        tmp_path / "lane",
        job,
        room=clip_node.Room(_FREE, _RAM),
        alone=share == "all",
    )
    assert env.get(clip_placement.GPU_BYTES_ENV) == gpu_budget
    assert env.get(clip_placement.HOST_BYTES_ENV) == host_budget
    assert env["PHONOMETRY_COMPUTE"] == "cupy:0"
    assert env[encode_slots.SLOTS_ENV].endswith(f":{encode_slots.NVENC_SESSIONS}")
    assert env["PYTHONHASHSEED"] == "0"


@pytest.mark.parametrize("compute", ["cupy:1", "cupy", "cupy:0,fallback"])
def test_an_empty_cuda_visible_devices_shows_the_lanes_no_gpu(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, compute: str
) -> None:
    """An empty list hides every GPU, as CUDA reads it: the job is refused before a lane starts."""
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "")
    job = _job(("anim_x", "cpu"), compute=compute)
    problems, _, _ = clip_node.readiness(
        _pinned_root(tmp_path),
        job,
        run=_Run(_ALL_ENCODERS, _ALL_DECODERS),
        which=lambda name: _FFMPEG,
        available=lambda: _RAM,
    )
    assert len(problems) == 1
    assert "CUDA_VISIBLE_DEVICES shows this node only 0: ''" in problems[0]
    lane, room = tmp_path / "lane", clip_node.Room(0, _RAM)
    with pytest.raises(ValueError, match=r"shows this node only 0"):
        clip_node.lane_env(tmp_path, job.clips[0], lane, job, room=room, alone=False)


@pytest.mark.parametrize("compute", ["cpu", "cupy:1"])
def test_no_cuda_visible_devices_leaves_every_gpu_shown(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, compute: str
) -> None:
    """Unset, it narrows nothing, and the index is the GPU's own."""
    monkeypatch.delenv("CUDA_VISIBLE_DEVICES", raising=False)
    job = _job(("anim_x", "cpu"), compute=compute)
    lane, room = tmp_path / "lane", clip_node.Room(0, _RAM)
    env = clip_node.lane_env(tmp_path, job.clips[0], lane, job, room=room, alone=False)
    assert env.get("CUDA_VISIBLE_DEVICES") == (None if compute == "cpu" else "1")


def test_a_lane_keeps_its_home_and_matplotlib_s_caches_in_the_job_s_tree(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nothing a render writes to its home outlives the job: the tree it is in is removed.

    CuPy's compiled kernels stay where they were kept, as a Docker node keeps
    them on its cache volume.
    """
    home = tmp_path / "user"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("MPLCONFIGDIR", str(home / ".config" / "matplotlib"))
    monkeypatch.delenv("CUPY_CACHE_DIR", raising=False)
    root = tmp_path / "phonometry-clips-x"
    job = _job(("anim_x", "gpu"))
    env = clip_node.lane_env(
        root,
        job.clips[0],
        root / "lanes" / "anim_x",
        job,
        room=clip_node.Room(_FREE, _RAM),
        alone=False,
    )
    assert root in pathlib.Path(env["HOME"]).parents
    assert root in pathlib.Path(env["MPLCONFIGDIR"]).parents
    assert env["CUPY_CACHE_DIR"] == str(home / ".cupy" / "kernel_cache")
    monkeypatch.setenv("CUPY_CACHE_DIR", "/cache/cupy-kernels")
    env = clip_node.lane_env(
        root,
        job.clips[0],
        root / "lanes" / "anim_x",
        job,
        room=clip_node.Room(_FREE, _RAM),
        alone=False,
    )
    assert env["CUPY_CACHE_DIR"] == "/cache/cupy-kernels"


def test_a_lane_on_a_node_with_no_home_keeps_cupy_s_kernels_in_its_own(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A user with no home and no password entry, as a container's may be, is no crash."""

    def no_home() -> pathlib.Path:
        msg = "Could not determine home directory."
        raise RuntimeError(msg)

    monkeypatch.delenv("CUPY_CACHE_DIR", raising=False)
    monkeypatch.setattr(pathlib.Path, "home", no_home)
    root = tmp_path / "phonometry-clips-x"
    job = _job(("anim_x", "gpu"))
    lane, room = root / "lanes" / "anim_x", clip_node.Room(_FREE, _RAM)
    env = clip_node.lane_env(root, job.clips[0], lane, job, room=room, alone=False)
    assert "CUPY_CACHE_DIR" not in env
    assert root in pathlib.Path(env["HOME"]).parents


@pytest.mark.parametrize(
    ("compute", "inherited", "placement", "visible"),
    [
        ("cupy:1", None, "cupy", "1"),
        ("cupy:1,fallback", "2,3", "cupy,fallback", "3"),
        ("cupy", None, "cupy", None),
        ("cpu", None, "cpu", None),
    ],
)
def test_a_lane_on_a_gpu_other_than_the_first_sees_it_as_the_first(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    compute: str,
    inherited: str | None,
    placement: str,
    visible: str | None,
) -> None:
    """A scene's own device arithmetic runs on CuPy's current device, GPU 0."""
    if inherited is None:
        monkeypatch.delenv("CUDA_VISIBLE_DEVICES", raising=False)
    else:
        monkeypatch.setenv("CUDA_VISIBLE_DEVICES", inherited)
    job = _job(("anim_x", "gpu"), compute=compute)
    env = clip_node.lane_env(
        tmp_path,
        job.clips[0],
        tmp_path / "lane",
        job,
        room=clip_node.Room(_FREE, _RAM),
        alone=False,
    )
    assert env["PHONOMETRY_COMPUTE"] == placement
    assert env.get("CUDA_VISIBLE_DEVICES") == (visible or inherited)


def test_a_clip_that_needs_more_than_a_lane_runs_alone_or_is_refused() -> None:
    """The node is shared: the lanes divide what is free when the job starts."""
    lane = clip_placement.gpu_budget(_FREE, alone=False)
    whole = clip_placement.gpu_budget(_FREE, alone=True)
    room = clip_node.Room(gpu=_FREE, host=_RAM)
    fits = _job(
        ("anim_small", "gpu", lane, 0),
        ("anim_large", "gpu", lane + 1, 0),
        ("anim_ram", "cpu", 0, _RAM // 2 + 1),
        ("anim_whole", "gpu-whole", 1, 0),
    )
    alone, problems = clip_node.plan(fits, room)
    assert problems == []
    assert alone == {
        "anim_small": False,
        "anim_large": True,
        "anim_ram": True,
        "anim_whole": True,
    }
    too_big = _job(
        ("anim_huge", "gpu", whole + 1, 0),
        ("anim_heavy", "cpu", 0, _RAM + 1),
        ("anim_small", "gpu", lane, 0),
    )
    _, problems = clip_node.plan(too_big, room)
    assert len(problems) == 2
    assert "anim_huge" in problems[0]
    assert "GPU memory" in problems[0]
    assert "anim_heavy" in problems[1]
    assert "RAM" in problems[1]


def test_the_lanes_ask_cupy_for_the_free_memory_of_their_device() -> None:
    seen: list[list[str]] = []

    def run(argv: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        seen.append(argv)
        return subprocess.CompletedProcess(argv, 0, stdout=f"{_FREE}\n", stderr="")

    assert clip_node.gpu_bytes(_job(("anim_x", "gpu")), run=run) == _FREE
    assert "Device(0).mem_info[0]" in seen[0][-1]
    assert clip_node.gpu_bytes(_job(("anim_x", "cpu")), run=run) == 0
    assert len(seen) == 1
    # A check is a job of no clips, and asks too: a GPU it cannot read is named then.
    assert clip_node.gpu_bytes(_job(), run=run) == _FREE
    assert len(seen) == 2


def _writer(files: list[str], *, exit_code: int = 0, sleep: float = 0.0) -> str:
    return (
        "import os, pathlib, sys, time\n"
        f"time.sleep({sleep})\n"
        "out = pathlib.Path(sys.argv[1]) / 'clips'\n"
        "out.mkdir(parents=True, exist_ok=True)\n"
        f"for name in {files!r}:\n"
        "    (out / name).write_bytes(b'\\x1aE\\xdf\\xa3' + b'0' * 16)\n"
        "print('rendering', flush=True)\n"
        f"sys.exit({exit_code})\n"
    )


def _forking(pidfile: pathlib.Path) -> str:
    """A render that forks a child of its own (as the variants do) and runs on."""
    return (
        "import os, sys, time\n"
        "pid = os.fork()\n"
        "if pid == 0:\n"
        "    time.sleep(60)\n"
        "    os._exit(0)\n"
        f"open({str(pidfile)!r}, 'w').write(str(pid))\n"
        "time.sleep(60)\n"
    )


def _orphaning(pidfile: pathlib.Path, ending: str) -> str:
    """A render that forks a child of its own, then ends by *ending* and leaves it."""
    return (
        "import os, signal, time\n"
        "pid = os.fork()\n"
        "if pid == 0:\n"
        "    time.sleep(60)\n"
        "    os._exit(0)\n"
        f"open({str(pidfile)!r}, 'w').write(str(pid))\n"
        f"{ending}\n"
    )


def _state(pid: int) -> str | None:
    """The state Linux gives process *pid* (``R``, ``S``, ``Z``...); None where /proc does not say."""
    try:
        stat = pathlib.Path(f"/proc/{pid}/stat").read_text(
            encoding="ascii", errors="replace"
        )
    except OSError:
        return None
    # "pid (name) state ...": the name may hold spaces and parentheses.
    fields = stat.rpartition(")")[2].split()
    return fields[0] if fields else None


def _gone(pid: int, *, within_s: float = 10.0) -> bool:
    """Whether process *pid* is gone within *within_s*; one that is not is killed here.

    A process that has ended and that nothing has reaped, a zombie, is gone:
    a signal still finds it, but it runs nothing. Linux says so in /proc;
    elsewhere only a process that no longer exists counts.
    """
    deadline = time.monotonic() + within_s
    while time.monotonic() < deadline:
        if _state(pid) in ("Z", "X"):
            return True
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.1)
    os.kill(pid, signal.SIGKILL)
    return False


@pytest.mark.skipif(
    not pathlib.Path("/proc/self/stat").is_file(),
    reason="Linux names a zombie in /proc",
)
def test_a_process_that_ended_but_was_never_reaped_is_gone() -> None:
    """A lane's child killed with its group is reparented, and stays a zombie where nothing reaps it.

    So it is in the node's container, whose first process reaps no orphans.
    """
    process = subprocess.Popen([sys.executable, "-c", "pass"])
    try:
        deadline = time.monotonic() + 30.0
        while _state(process.pid) != "Z" and time.monotonic() < deadline:
            time.sleep(0.05)
        assert _state(process.pid) == "Z"
        assert _gone(process.pid, within_s=1.0)
    finally:
        process.wait(timeout=30)


def _starter(scripts: dict[str, str]) -> Callable[..., subprocess.Popen[bytes]]:
    def start(
        argv: list[str], env: dict[str, str], cwd: pathlib.Path, log: pathlib.Path
    ) -> subprocess.Popen[bytes]:
        clip = argv[argv.index("--anim") + 1]
        lane = pathlib.Path(argv[argv.index("--scratch-dir") + 1])
        with log.open("wb") as sink:
            return subprocess.Popen(
                [sys.executable, "-c", scripts[clip], str(lane)],
                stdout=sink,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )

    return start


def test_a_lane_that_dies_fails_its_clip_and_not_the_other(
    tmp_path: pathlib.Path,
) -> None:
    good = check_animation_freshness.outputs("anim_good")
    job = _job(("anim_bad", "cpu"), ("anim_good", "cpu"))
    results = list(
        clip_node.run_lanes(
            tmp_path,
            job,
            cancel=clip_node.Cancel(),
            fingerprints={"anim_good": "f00d", "anim_bad": "dead"},
            start=_starter(
                {"anim_bad": _writer([], exit_code=3), "anim_good": _writer(good)}
            ),
        )
    )
    by_clip = {header["clip"]: (header, buffers) for header, buffers in results}
    bad, _ = by_clip["anim_bad"]
    assert bad["ok"] is False
    assert "exited with 3" in bad["error"]
    assert "rendering" in bad["error"]
    ok, buffers = by_clip["anim_good"]
    assert ok["ok"] is True
    assert ok["fingerprint"] == "f00d"
    assert [f["name"] for f in ok["files"]] == good
    assert len(buffers) == len(good)
    for header, _ in results:
        # What travels is data: every header the node sends survives JSON.
        assert json.loads(json.dumps(header)) == header


def test_lanes_run_two_at_a_time_and_a_clip_that_runs_alone_alone(
    tmp_path: pathlib.Path,
) -> None:
    names = ["anim_a", "anim_b", "anim_whole", "anim_c"]
    devices = {
        "anim_a": "gpu",
        "anim_b": "gpu",
        "anim_whole": "gpu-whole",
        "anim_c": "gpu",
    }
    running: set[str] = set()
    seen: list[set[str]] = []

    class _Fake:
        returncode: int | None

        def __init__(self, clip: str) -> None:
            # A pid no process group has: the node signals a finished
            # lane's group, and this stand-in's must reach nothing.
            self.clip, self.polls, self.pid, self.returncode = (
                clip,
                0,
                1 << 30,
                None,
            )
            running.add(clip)
            seen.append(set(running))

        def poll(self) -> int | None:
            self.polls += 1
            if self.polls > 2:
                running.discard(self.clip)
                self.returncode = 1
            return self.returncode

    def start(
        argv: list[str], env: dict[str, str], cwd: pathlib.Path, log: pathlib.Path
    ) -> _Fake:
        return _Fake(argv[argv.index("--anim") + 1])

    job = _job(*[(n, devices[n]) for n in names])
    room = clip_node.Room(_FREE, None)
    alone, _ = clip_node.plan(job, room)
    list(
        clip_node.run_lanes(
            tmp_path,
            job,
            cancel=clip_node.Cancel(),
            fingerprints={},
            room=room,
            alone=alone,
            start=start,
        )
    )
    assert max(len(s) for s in seen) == 2
    assert all(s == {"anim_whole"} for s in seen if "anim_whole" in s)


def test_cancelling_kills_the_whole_lane_group(tmp_path: pathlib.Path) -> None:
    pidfile = tmp_path / "child.pid"
    cancel = clip_node.Cancel()
    lanes = clip_node.run_lanes(
        tmp_path,
        _job(("anim_slow", "cpu")),
        cancel=cancel,
        fingerprints={},
        start=_starter({"anim_slow": _forking(pidfile)}),
    )
    threading.Timer(1.5, cancel.set).start()
    assert list(lanes) == []
    assert _gone(int(pidfile.read_text())), (
        "the forked child of a cancelled lane outlived it"
    )


class _BrokenPipe(io.RawIOBase):
    """A frames pipe whose reader is gone."""

    def writable(self) -> bool:
        return True

    def write(self, data: object) -> int:
        raise BrokenPipeError(32, "Broken pipe")


def test_a_broken_frames_pipe_ends_every_lane(tmp_path: pathlib.Path) -> None:
    """The client killed mid-send: the send fails, and the other lane goes with it."""
    pidfile = tmp_path / "child.pid"
    fast = check_animation_freshness.outputs("anim_fast")
    lanes = clip_node.run_lanes(
        tmp_path,
        _job(("anim_fast", "cpu"), ("anim_slow", "cpu")),
        cancel=clip_node.Cancel(),
        fingerprints={"anim_fast": "f00d"},
        start=_starter(
            {"anim_fast": _writer(fast, sleep=1.0), "anim_slow": _forking(pidfile)}
        ),
    )
    frames = _BrokenPipe()
    with pytest.raises(BrokenPipeError):
        clip_node.deliver(frames, lanes)
    assert _gone(int(pidfile.read_text())), "a lane outlived the broken frames pipe"


@pytest.mark.parametrize("name", ["SIGTERM", "SIGHUP"])
def test_a_term_or_hangup_signal_cancels_the_lanes(name: str) -> None:
    """A container stopped, or a session hung up: the lanes are cancelled, never orphaned."""
    sig = getattr(signal, name)
    before = signal.getsignal(sig)
    cancel = clip_node.Cancel()
    with clip_node.cancelled_by_signals(cancel):
        # Sent from the main thread, the signal is handled before this returns.
        signal.raise_signal(sig)
        assert cancel.is_set()
    assert cancel.signals == [sig]
    assert signal.getsignal(sig) == before


#: A signal that lands inside the wait of the lanes' loop, at the one point
#: where the main thread holds the lock of the condition it waits on: a
#: handler that took that lock again would wait on it for good.
_SIGNAL_INSIDE_THE_WAIT = """
import signal, sys, threading
sys.path.insert(0, {scripts!r})
import clip_node

landed = []
wait = threading.Condition.wait

def wait_with_a_signal(self, timeout=None):
    if not landed:
        landed.append(True)
        signal.raise_signal(signal.SIGTERM)
    return wait(self, timeout)

threading.Condition.wait = wait_with_a_signal
cancel = clip_node.Cancel()
with clip_node.cancelled_by_signals(cancel):
    ended = cancel.wait(0.05)
print(landed == [True], ended, cancel.is_set())
"""


def test_a_signal_inside_the_lanes_wait_cancels_them_and_never_hangs() -> None:
    """The handler records the signal and takes no lock, so the wait it lands in ends."""
    done = subprocess.run(
        [
            sys.executable,
            "-c",
            _SIGNAL_INSIDE_THE_WAIT.format(scripts=str(_ROOT / "scripts")),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout.split() == ["True", "True", "True"]


def test_a_signal_while_a_lane_runs_ends_it(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The loop sees the recorded signal at its next turn and stops the lane it runs."""
    sent: list[signal.Signals] = []
    monkeypatch.setattr(os, "killpg", lambda group, sig: sent.append(sig))

    class _Running:
        """A lane that runs until it is signalled; the signal comes at its second poll."""

        returncode: int | None

        def __init__(self) -> None:
            # A number past any pid Linux gives, so no signal reaches a process.
            self.pid, self.returncode, self.polls = 1 << 30, None, 0

        def poll(self) -> int | None:
            self.polls += 1
            if self.polls == 2:
                signal.raise_signal(signal.SIGTERM)
            elif sent:
                self.returncode = -signal.SIGTERM
            return self.returncode

        def wait(self, timeout: float) -> int | None:
            return self.poll()

    def start(
        argv: list[str], env: dict[str, str], cwd: pathlib.Path, log: pathlib.Path
    ) -> _Running:
        return _Running()

    cancel = clip_node.Cancel()
    with clip_node.cancelled_by_signals(cancel):
        results = list(
            clip_node.run_lanes(
                tmp_path,
                _job(("anim_x", "cpu")),
                cancel=cancel,
                fingerprints={},
                start=start,
            )
        )
    assert results == []
    assert cancel.signals == [signal.SIGTERM]
    assert sent == [signal.SIGTERM, signal.SIGKILL]


def test_the_bootstrap_hands_the_rest_of_stdin_to_the_node(
    tmp_path: pathlib.Path,
) -> None:
    """Sent through the node's loader, it unpacks the archive and loses nothing after it."""
    import clip_link

    stub = (
        "import os, pathlib, shutil, sys\n"
        "def main(argv, *, signals=None):\n"
        "    frames = os.fdopen(int(argv[argv.index('--frames-fd') + 1]), 'wb')\n"
        "    frames.write(sys.stdin.buffer.read(4))\n"
        "    frames.flush()\n"
        "    print('to stderr')\n"
        "    shutil.rmtree(pathlib.Path(__file__).resolve().parent.parent)\n"
        "    return 0\n"
    )
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w:gz") as tar:
        body = stub.encode()
        info = tarfile.TarInfo("scripts/clip_node.py")
        info.size = len(body)
        tar.addfile(info, io.BytesIO(body))
    archive = data.getvalue()
    program = io.BytesIO()
    clip_link.send_program(program, clip_node.BOOTSTRAP)
    done = subprocess.run(
        [sys.executable, "-I", "-c", clip_link.loader()],
        input=program.getvalue() + len(archive).to_bytes(8, "big") + archive + b"JOB!",
        capture_output=True,
        check=False,
        timeout=60,
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout == b"JOB!"
    assert b"to stderr" in done.stderr


def test_an_archive_over_the_limit_is_refused() -> None:
    import clip_link

    program = io.BytesIO()
    clip_link.send_program(program, clip_node.BOOTSTRAP)
    done = subprocess.run(
        [sys.executable, "-I", "-c", clip_link.loader()],
        input=program.getvalue() + (clip_node.ARCHIVE_LIMIT + 1).to_bytes(8, "big"),
        capture_output=True,
        check=False,
        timeout=60,
    )
    assert done.returncode != 0
    assert b"refused" in done.stderr


def test_an_archive_that_does_not_unpack_leaves_nothing_behind(
    tmp_path: pathlib.Path,
) -> None:
    import clip_link

    program = io.BytesIO()
    clip_link.send_program(program, clip_node.BOOTSTRAP)
    junk = b"not a gzip tar"
    done = subprocess.run(
        [sys.executable, "-I", "-c", clip_link.loader()],
        input=program.getvalue() + len(junk).to_bytes(8, "big") + junk,
        capture_output=True,
        check=False,
        timeout=60,
        env={**os.environ, "TMPDIR": str(tmp_path)},
    )
    assert done.returncode != 0
    assert list(tmp_path.iterdir()) == []


def test_every_cap_reaches_the_bootstrap_whole() -> None:
    """Each cap takes the place of its own placeholder, and nothing else of the program changes."""
    program = clip_node.bootstrap(unpacked_limit=12_345, member_limit=678)
    compile(program, "phonometry-bootstrap", "exec")
    assert "@" not in program
    assert "12345" in program
    assert "678" in program
    assert str(clip_node.MEMBER_LIMIT) in clip_node.BOOTSTRAP
    assert str(clip_node.ARCHIVE_LIMIT) in program
    assert str(clip_node.UNPACKED_LIMIT) in clip_node.BOOTSTRAP


#: Run before the loader: an archive that is unpacked at all stops the node.
_NOTHING_UNPACKED = """
import sys, tarfile

def extractall(*args, **kwargs):
    sys.exit("clip node test: something was unpacked")

tarfile.TarFile.extractall = extractall
tarfile.TarFile.extract = extractall
"""


def _member(
    name: str, body: bytes = b"", kind: bytes = tarfile.REGTYPE
) -> tuple[tarfile.TarInfo, bytes]:
    """One member of an archive: a file of *body*, or another *kind* with no data."""
    info = tarfile.TarInfo(name)
    info.type = kind
    info.size = len(body)
    if kind in (tarfile.LNKTYPE, tarfile.SYMTYPE):
        info.linkname = "scripts/clip_node.py"
    return info, body


def _archive(*members: tuple[tarfile.TarInfo, bytes]) -> bytes:
    """A gzip tar of the node that says its signals, then *members*."""
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w:gz") as tar:
        for info, body in (
            _member("scripts/clip_node.py", _NODE_THAT_SAYS_ITS_SIGNALS.encode()),
            *members,
        ):
            tar.addfile(info, io.BytesIO(body) if body else None)
    return data.getvalue()


def _read_to_the_end(archive: bytes) -> int:
    """Where reading *archive*'s members ends: every header and every member's data."""
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        for _ in tar:
            pass
        return tar.offset


#: Run before the loader: the furthest the decompressed archive is read or
#: skipped through, said on standard error as the node ends.
_HOW_FAR_IT_READS = """
import atexit, gzip, sys

reached = [0]

def watched(name):
    real = getattr(gzip.GzipFile, name)
    def call(self, *args, **kwargs):
        done = real(self, *args, **kwargs)
        # A seek says where it went; tell() itself seeks, so it is not asked then.
        where = done if name == "seek" else self.tell()
        reached[0] = max(reached[0], where)
        return done
    setattr(gzip.GzipFile, name, call)

for name in ("read", "read1", "seek"):
    watched(name)
atexit.register(lambda: sys.stderr.write("clip node test: read up to %d\\n" % reached[0]))
"""


def _unpack_on_a_node(
    archive: bytes,
    tmp_path: pathlib.Path,
    *,
    refused: bool,
    prelude: str = "",
    **caps: int,
) -> subprocess.CompletedProcess[bytes]:
    """The bootstrap, with *caps*, sent *archive*; when it is *refused*, nothing may be unpacked."""
    import clip_link

    program = io.BytesIO()
    clip_link.send_program(program, clip_node.bootstrap(**caps))
    prelude += _NOTHING_UNPACKED if refused else ""
    return subprocess.run(
        [sys.executable, "-I", "-c", prelude + clip_link.loader()],
        input=program.getvalue() + len(archive).to_bytes(8, "big") + archive,
        capture_output=True,
        check=False,
        timeout=60,
        env={**os.environ, "TMPDIR": str(tmp_path)},
    )


@pytest.mark.parametrize("over", [0, 1], ids=["at the cap", "a byte over"])
@pytest.mark.parametrize("load", ["data", "a long name"])
def test_an_archive_that_unpacks_past_the_cap_is_refused_before_anything_is_unpacked(
    tmp_path: pathlib.Path, load: str, over: int
) -> None:
    """A small archive can unpack to far more than it weighs: what it unpacks to is capped.

    Its headers count too: a long name takes header blocks of its own, and
    an archive of empty files with long names would cost no data at all.
    """
    member = (
        _member("padding.txt", b"0" * 1000)
        if load == "data"
        else _member("scripts/" + "n" * 200 + ".py")
    )
    archive = _archive(member)
    end = _read_to_the_end(archive)
    if load == "a long name":
        # The name's own header blocks are past two headers and the node's data.
        assert end > 3 * tarfile.BLOCKSIZE + len(_NODE_THAT_SAYS_ITS_SIGNALS)
    cap = end - over
    done = _unpack_on_a_node(archive, tmp_path, refused=bool(over), unpacked_limit=cap)
    assert list(tmp_path.iterdir()) == []
    if over:
        assert done.returncode == 1
        said = f"at least {end} bytes was refused, over the {cap} bytes a node unpacks"
        assert said.encode() in done.stderr
        assert done.stdout == b""
    else:
        assert done.returncode == 0, done.stderr
        assert done.stdout == b"[]"


def test_a_long_name_past_the_cap_is_refused_before_it_is_read(
    tmp_path: pathlib.Path,
) -> None:
    """A name two hundred thousand characters long takes a few hundred bytes of gzip, and a header past the cap.

    The header is refused before it is read: the archive is never read
    further than the cap and one block.
    """
    cap = 50_000
    archive = _archive(_member("scripts/" + "n" * 200_000 + ".py"))
    assert len(archive) < 1000
    done = _unpack_on_a_node(
        archive,
        tmp_path,
        refused=True,
        prelude=_HOW_FAR_IT_READS,
        unpacked_limit=cap,
    )
    assert list(tmp_path.iterdir()) == []
    assert done.returncode == 1
    assert f"was refused, over the {cap} bytes a node unpacks".encode() in done.stderr
    found = re.search(rb"clip node test: read up to (\d+)", done.stderr)
    assert found is not None, done.stderr
    assert int(found[1]) <= cap + tarfile.BLOCKSIZE


@pytest.mark.parametrize("over", [0, 1], ids=["at the cap", "one over"])
def test_an_archive_of_more_members_than_the_cap_is_refused_before_anything_is_unpacked(
    tmp_path: pathlib.Path, over: int
) -> None:
    """Each member is a file on the node: millions of empty ones cost a few bytes each to send."""
    archive = _archive(*(_member(f"empty-{n}.txt") for n in range(2 + over)))
    done = _unpack_on_a_node(archive, tmp_path, refused=bool(over), member_limit=3)
    assert list(tmp_path.iterdir()) == []
    if over:
        assert done.returncode == 1
        assert b"an archive of more than 3 members was refused" in done.stderr
    else:
        assert done.returncode == 0, done.stderr
        assert done.stdout == b"[]"


@pytest.mark.parametrize(
    "kind", [tarfile.LNKTYPE, tarfile.SYMTYPE], ids=["hard link", "symbolic link"]
)
def test_an_archive_holding_a_link_is_refused_before_anything_is_unpacked(
    tmp_path: pathlib.Path, kind: bytes
) -> None:
    """The shipped tree is files and folders; a hard link copies its target's data past the cap."""
    archive = _archive(_member("copy.py", kind=kind))
    done = _unpack_on_a_node(archive, tmp_path, refused=True)
    assert list(tmp_path.iterdir()) == []
    assert done.returncode == 1
    said = b"an archive holding 'copy.py', neither a file nor a folder, was refused"
    assert said in done.stderr


#: Run before the loader: SIGTERM is sent at the chosen step of the
#: bootstrap, from the main thread, so it is handled before that step goes on.
_SIGNAL_IN_THE_BOOTSTRAP = """
import signal, tarfile, tempfile

def signalled(call):
    def at(*args, **kwargs):
        signal.raise_signal(signal.SIGTERM)
        return call(*args, **kwargs)
    return at

if {where!r} == "mkdtemp":
    made = tempfile.mkdtemp
    def mkdtemp(*args, **kwargs):
        root = made(*args, **kwargs)
        signal.raise_signal(signal.SIGTERM)
        return root
    tempfile.mkdtemp = mkdtemp
else:
    tarfile.TarFile.extractall = signalled(tarfile.TarFile.extractall)
"""

#: The node the bootstrap hands over to, in place of the real one: it says
#: which signals it was handed and removes the tree, as the real one does.
_NODE_THAT_SAYS_ITS_SIGNALS = (
    "import os, pathlib, shutil\n"
    "def main(argv, *, signals=None):\n"
    "    frames = os.fdopen(int(argv[argv.index('--frames-fd') + 1]), 'wb')\n"
    "    frames.write(repr(signals).encode())\n"
    "    frames.flush()\n"
    "    shutil.rmtree(pathlib.Path(__file__).resolve().parent.parent)\n"
    "    return 130 if signals else 0\n"
)


#: What the bootstrap says when a signal ends it before it has its input.
_STOPPED_READING = b"stopped by signal 15 before it had read all its input"


@pytest.mark.parametrize(
    ("where", "returncode", "handed"),
    [("mkdtemp", 1, b""), ("extractall", 130, repr([signal.SIGTERM.value]).encode())],
)
def test_a_signal_while_the_bootstrap_unpacks_leaves_nothing_behind(
    tmp_path: pathlib.Path, where: str, returncode: int, handed: bytes
) -> None:
    """From before its temporary directory is made, the bootstrap records a signal, and the tree goes.

    Ended by the signal there, it would leave the unpacked tree behind. One
    that comes before the archive is read ends the bootstrap at the read,
    through its clean-up; one that comes after is handed to the node, which
    ends the run and removes the tree.
    """
    import clip_link

    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w:gz") as tar:
        body = _NODE_THAT_SAYS_ITS_SIGNALS.encode()
        info = tarfile.TarInfo("scripts/clip_node.py")
        info.size = len(body)
        tar.addfile(info, io.BytesIO(body))
    archive = data.getvalue()
    program = io.BytesIO()
    clip_link.send_program(program, clip_node.BOOTSTRAP)
    prelude = _SIGNAL_IN_THE_BOOTSTRAP.format(where=where)
    done = subprocess.run(
        [sys.executable, "-I", "-c", prelude + clip_link.loader()],
        input=program.getvalue() + len(archive).to_bytes(8, "big") + archive,
        capture_output=True,
        check=False,
        timeout=60,
        env={**os.environ, "TMPDIR": str(tmp_path)},
    )
    assert done.returncode == returncode, done.stderr
    assert done.stdout == handed
    assert (_STOPPED_READING in done.stderr) == (returncode == 1)
    assert list(tmp_path.iterdir()) == []


#: A node run through :func:`clip_node.main` on a tree of its own, with
#: nothing to render, and SIGTERM sent from the main thread at the step
#: chosen: the package check, the done frame, or the removal of the tree.
_SIGNAL_IN_THE_NODE = """
import os, pathlib, shutil, signal, sys, tempfile
sys.path.insert(0, {scripts!r})
import clip_link, clip_node

def no_lanes(*args, **kwargs):
    yield from ()

def signalled(call):
    def at(*args, **kwargs):
        signal.raise_signal(signal.SIGTERM)
        return call(*args, **kwargs)
    return at

clip_node.readiness = lambda root, job: ([], clip_node.Room(0, None), {{}})
clip_node.animation_fingerprint.fingerprints = lambda root: {{}}
clip_node.run_lanes = no_lanes
# The client's input closes once the job is read, which is a cancel of its
# own: no watcher here, so that only the signal says how the run ends.
clip_node._watch = lambda fd, cancel: None
clip_node._check_package = lambda: None
clip_node._ROOT = pathlib.Path(tempfile.mkdtemp(prefix="phonometry-clips-")).resolve()
where = {where!r}
if where == "package check":
    clip_node._check_package = signalled(clip_node._check_package)
elif where == "job read":
    clip_link.receive = signalled(clip_link.receive)
elif where == "before the job read":
    clip_node._read_job = signalled(clip_node._read_job)
elif where == "done frame":
    send = clip_link.send
    def send_done(stream, header, buffers=()):
        if header.get("type") == "done":
            signal.raise_signal(signal.SIGTERM)
        send(stream, header, buffers)
    clip_link.send = send_done
else:
    shutil.rmtree = signalled(shutil.rmtree)
sys.exit(clip_node.main(["--serve", "--frames-fd", str(os.dup(1)), "--remove-root"]))
"""


@pytest.mark.parametrize(
    ("where", "returncode", "answer"),
    [
        ("package check", 130, None),
        ("done frame", 0, "done"),
        ("removal of the tree", 0, "done"),
    ],
)
def test_a_signal_anywhere_in_the_node_leaves_nothing_behind(
    tmp_path: pathlib.Path, where: str, returncode: int, answer: str | None
) -> None:
    """The node's handlers hold from its first step to the removal of its tree.

    A signal before the lanes start ends the run with no frame; one that
    comes once the run is over is recorded and changes nothing. Neither ends
    the node before it has removed what it unpacked.
    """
    import clip_link

    job = io.BytesIO()
    clip_link.send(
        job,
        {
            "type": "job",
            "version": clip_node.PROTOCOL,
            "clips": [],
            "compute": "cpu",
            "encoder": "libsvtav1",
            "audit_only": False,
        },
    )
    done = subprocess.run(
        [
            sys.executable,
            "-c",
            _SIGNAL_IN_THE_NODE.format(scripts=str(_ROOT / "scripts"), where=where),
        ],
        input=job.getvalue(),
        capture_output=True,
        check=False,
        timeout=120,
        env={**os.environ, "TMPDIR": str(tmp_path)},
    )
    assert done.returncode == returncode, done.stderr
    assert list(tmp_path.iterdir()) == []
    if answer is None:
        assert done.stdout == b""
    else:
        header, _ = clip_link.receive(io.BytesIO(done.stdout), lambda _header: [])
        assert header["type"] == answer


def _held_open(program: list[str], tmp_path: pathlib.Path) -> int:
    """Run *program* with an input that stays open and brings nothing; its exit status.

    A program that waited on that input for good is killed after a minute,
    and the test fails.
    """
    process = subprocess.Popen(
        program,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        env={**os.environ, "TMPDIR": str(tmp_path)},
    )
    assert process.stdin is not None
    assert process.stderr is not None
    try:
        process.wait(timeout=60)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=30)
        pytest.fail("a signal did not end a node waiting on its input")
    finally:
        process.stdin.close()
        process.stderr.close()
    return process.returncode


def test_a_signal_the_bootstrap_recorded_ends_the_run_before_the_job_is_read(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The bootstrap hands its signals to the node, which takes them as its own."""

    def read(stdin: object, cancel: clip_node.Cancel) -> clip_node.Job:
        pytest.fail("the job was read after a signal")

    monkeypatch.setattr(clip_node, "_check_package", lambda: None)
    monkeypatch.setattr(clip_node, "_read_job", read)
    frames = tmp_path / "frames"
    with frames.open("wb") as sink:
        argv = ["--serve", "--frames-fd", str(os.dup(sink.fileno()))]
        status = clip_node.main(argv, signals=[signal.SIGTERM])
    assert status == 130
    assert frames.read_bytes() == b""


@pytest.mark.parametrize("where", ["job read", "before the job read"])
def test_a_signal_while_the_node_waits_for_its_job_ends_it(
    tmp_path: pathlib.Path, where: str
) -> None:
    """A client that holds the connection and sends nothing does not keep a stopped node.

    Nor does a signal that comes after the last look at the cancel and
    before the wait begins.
    """
    program = _SIGNAL_IN_THE_NODE.format(scripts=str(_ROOT / "scripts"), where=where)
    assert _held_open([sys.executable, "-c", program], tmp_path) == 130
    assert list(tmp_path.iterdir()) == []


def test_a_signal_before_the_bootstrap_waits_for_the_archive_ends_it(
    tmp_path: pathlib.Path,
) -> None:
    """A signal that comes after the last look at the signals and before the read begins.

    Here it comes as the temporary directory is made, and the archive never does.
    """
    import clip_link

    program = io.BytesIO()
    clip_link.send_program(program, clip_node.BOOTSTRAP)
    prelude = _SIGNAL_IN_THE_BOOTSTRAP.format(where="mkdtemp")
    process = subprocess.Popen(
        [sys.executable, "-I", "-c", prelude + clip_link.loader()],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        env={**os.environ, "TMPDIR": str(tmp_path)},
    )
    assert process.stdin is not None
    assert process.stderr is not None
    try:
        process.stdin.write(program.getvalue() + (1000).to_bytes(8, "big"))
        process.stdin.flush()
        process.wait(timeout=60)
        said = process.stderr.read()
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=30)
        pytest.fail("a signal did not end a bootstrap about to wait on the archive")
    finally:
        process.stdin.close()
        process.stderr.close()
    assert process.returncode == 1
    assert _STOPPED_READING in said
    assert list(tmp_path.iterdir()) == []


#: Run before the loader: the input as the loader and the bootstrap read it,
#: with SIGTERM sent as the bootstrap starts to read the archive.
_SIGNAL_AS_THE_ARCHIVE_IS_READ = """
import signal, sys

class _Buffer:
    def __init__(self, raw):
        self.raw, self.reads = raw, 0
    def readline(self, *args):
        return self.raw.readline(*args)
    def read(self, size=-1):
        self.reads += 1
        # The loader's program, the archive's size, then the archive.
        if self.reads == 3:
            signal.raise_signal(signal.SIGTERM)
        return self.raw.read(size)

class _Stdin:
    def __init__(self, buffer):
        self.buffer = buffer

sys.stdin = _Stdin(_Buffer(sys.stdin.buffer))
"""


def test_a_signal_while_the_bootstrap_waits_for_the_archive_ends_it(
    tmp_path: pathlib.Path,
) -> None:
    """The archive's size came and the archive does not: a signal ends the wait, and the tree goes."""
    import clip_link

    program = io.BytesIO()
    clip_link.send_program(program, clip_node.BOOTSTRAP)
    node = [
        sys.executable,
        "-I",
        "-c",
        _SIGNAL_AS_THE_ARCHIVE_IS_READ + clip_link.loader(),
    ]
    process = subprocess.Popen(
        node,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        env={**os.environ, "TMPDIR": str(tmp_path)},
    )
    assert process.stdin is not None
    assert process.stderr is not None
    try:
        process.stdin.write(program.getvalue() + (1000).to_bytes(8, "big"))
        process.stdin.flush()
        process.wait(timeout=60)
        said = process.stderr.read()
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=30)
        pytest.fail("a signal did not end a bootstrap waiting on the archive")
    finally:
        process.stdin.close()
        process.stderr.close()
    assert process.returncode == 1
    assert _STOPPED_READING in said
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    ("header", "problem"),
    [
        ({"type": "job", "version": 99}, "not a clip job"),
        (
            {
                "type": "job",
                "version": clip_node.PROTOCOL,
                "clips": [{"name": "anim_x", "device": "gpu"}],
                "compute": "cupy",
                "encoder": "av1_nvenc",
                "audit_only": False,
            },
            "no av1_nvenc encoder",
        ),
    ],
)
def test_a_job_the_node_cannot_read_or_render_is_answered_with_a_refusal(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    header: dict[str, Any],
    problem: str,
) -> None:
    """The client is told why, and no lane starts."""
    import clip_link

    def unready(
        root: pathlib.Path, job: clip_node.Job
    ) -> tuple[list[str], Any, dict[str, bool]]:
        return ["ffmpeg has no av1_nvenc encoder"], clip_node.Room(0, None), {}

    def no_lanes(*args: object, **kwargs: object) -> None:
        pytest.fail("a lane started for a refused job")

    monkeypatch.setattr(clip_node, "readiness", unready)
    monkeypatch.setattr(clip_node, "run_lanes", no_lanes)
    sent = io.BytesIO()
    clip_link.send(sent, header)
    sent.seek(0)
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(sent))
    frames = tmp_path / "frames"
    with frames.open("wb") as sink:
        assert clip_node.serve(os.dup(sink.fileno())) == 1
    with frames.open("rb") as stream:
        answer, _ = clip_link.receive(stream, lambda _header: [])
    assert answer["type"] == "refused"
    assert problem in answer["problems"][0]


#: A node that serves one job and renders nothing: what is under test is how
#: it ends while the client still holds its input open, as a client does for
#: the whole run (closing it cancels the run).
_SERVE_NOTHING = """
import sys
sys.path.insert(0, {scripts!r})
import clip_node

def no_lanes(*args, **kwargs):
    yield from ()

clip_node.readiness = lambda root, job: ([], clip_node.Room(0, None), {{}})
clip_node.animation_fingerprint.fingerprints = lambda root: {{}}
clip_node.run_lanes = no_lanes
sys.exit(clip_node.serve(clip_node.os.dup(1)))
"""


def test_the_node_exits_cleanly_while_the_client_holds_its_input(
    tmp_path: pathlib.Path,
) -> None:
    """The watcher on stdin never holds the stream the interpreter closes at exit.

    A daemon thread blocked inside ``sys.stdin.buffer`` holds its lock, and
    the interpreter aborts on that lock as it exits, after the last frame.
    """
    import clip_link

    job = io.BytesIO()
    header = {
        "type": "job",
        "version": clip_node.PROTOCOL,
        "clips": [{"name": "anim_x", "device": "cpu"}],
        "compute": "cpu",
        "encoder": "libsvtav1",
        "audit_only": False,
    }
    clip_link.send(job, header)
    errors = tmp_path / "stderr.txt"
    with errors.open("wb") as sink:
        node = subprocess.Popen(
            [
                sys.executable,
                "-c",
                _SERVE_NOTHING.format(scripts=str(_ROOT / "scripts")),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=sink,
        )
    assert node.stdin is not None
    assert node.stdout is not None
    try:
        node.stdin.write(job.getvalue())
        node.stdin.flush()
        returncode = node.wait(timeout=120)
        answer, _ = clip_link.receive(node.stdout, lambda _header: [])
    finally:
        node.kill()
        node.wait(timeout=30)
        node.stdin.close()
        node.stdout.close()
    assert returncode == 0, errors.read_text(encoding="utf-8", errors="replace")
    assert answer["type"] == "done"


@pytest.mark.parametrize(
    "ending",
    ["os._exit(0)", "os.kill(os.getpid(), signal.SIGKILL)"],
    ids=["exits", "is killed"],
)
def test_a_lane_whose_render_ends_takes_what_it_started_with_it(
    tmp_path: pathlib.Path, ending: str
) -> None:
    """A render killed (by the OOM killer, say) or gone leaves no process of its lane behind."""
    pidfile = tmp_path / "child.pid"
    results = list(
        clip_node.run_lanes(
            tmp_path,
            _job(("anim_dies", "cpu")),
            cancel=clip_node.Cancel(),
            fingerprints={},
            start=_starter({"anim_dies": _orphaning(pidfile, ending)}),
        )
    )
    assert [header["ok"] for header, _ in results] == [False]
    assert _gone(int(pidfile.read_text())), "a child outlived its lane's render"


def _unreaped(pid: int) -> bool:
    """Whether *pid* is a child of this process that is not reaped: running, or ended and not collected."""
    try:
        os.waitid(os.P_PID, pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
    except ChildProcessError:
        return False
    return True


def _signals(
    monkeypatch: pytest.MonkeyPatch,
) -> list[tuple[int, signal.Signals, bool]]:
    """Each signal sent to a process group: the group, the signal, and whether its leader was unreaped."""
    sent: list[tuple[int, signal.Signals, bool]] = []
    killpg = os.killpg

    def recorded(group: int, sig: signal.Signals) -> None:
        sent.append((group, sig, _unreaped(group)))
        killpg(group, sig)

    monkeypatch.setattr(clip_node.os, "killpg", recorded)
    return sent


_PEEKS = pytest.mark.skipif(
    not hasattr(os, "waitid") or not hasattr(os, "WNOWAIT"),
    reason="the platform cannot ask whether a child ended without reaping it",
)


@_PEEKS
def test_a_finished_lane_s_group_is_ended_before_its_leader_is_reaped(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A reaped leader's number may go to a new process, which a signal to its group would reach."""
    sent = _signals(monkeypatch)
    good = check_animation_freshness.outputs("anim_good")
    results = list(
        clip_node.run_lanes(
            tmp_path,
            _job(("anim_bad", "cpu"), ("anim_good", "cpu")),
            cancel=clip_node.Cancel(),
            fingerprints={},
            start=_starter(
                {"anim_bad": _writer([], exit_code=3), "anim_good": _writer(good)}
            ),
        )
    )
    assert len(results) == 2
    assert [sig for _, sig, _ in sent] == [signal.SIGKILL] * 2
    assert all(unreaped for _, _, unreaped in sent), sent


@_PEEKS
def test_a_stopped_lane_s_group_is_killed_before_its_leader_is_reaped(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A lane stopped while it runs: SIGTERM, SIGKILL once it has ended, and only then is it reaped."""
    sent = _signals(monkeypatch)
    process = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        start_new_session=True,
    )
    lane = clip_node._Lane(
        clip_node.ClipJob("anim_x", "cpu"), tmp_path, process, tmp_path / "log.txt"
    )
    try:
        clip_node.stop([lane], grace_s=10.0)
        assert [sig for _, sig, _ in sent] == [signal.SIGTERM, signal.SIGKILL]
        assert all(unreaped for _, _, unreaped in sent), sent
        assert process.returncode == -signal.SIGTERM
    finally:
        process.kill()
        process.wait(timeout=30)


def test_every_finished_lane_s_group_is_ended_before_a_clip_is_sent(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sending a clip takes seconds, which a lane that finished beside it would wait reaped."""
    sent: list[int] = []
    monkeypatch.setattr(clip_node.os, "killpg", lambda group, sig: sent.append(group))

    class _Ended:
        returncode: int | None

        # Numbers past any pid Linux gives, so no signal reaches a process.
        def __init__(self, pid: int) -> None:
            self.pid, self.returncode = pid, None

        def poll(self) -> int:
            self.returncode = 1
            return 1

        def wait(self, timeout: float) -> int:
            return self.poll()

    pids = iter([1 << 30, (1 << 30) + 1])

    def start(
        argv: list[str], env: dict[str, str], cwd: pathlib.Path, log: pathlib.Path
    ) -> _Ended:
        return _Ended(next(pids))

    lanes = clip_node.run_lanes(
        tmp_path,
        _job(("anim_a", "cpu"), ("anim_b", "cpu")),
        cancel=clip_node.Cancel(),
        fingerprints={},
        start=start,
    )
    with contextlib.closing(lanes):
        next(lanes)
        assert sorted(sent) == [1 << 30, (1 << 30) + 1]


@pytest.mark.parametrize("whose", ["zero", "init", "this process's"])
def test_no_signal_for_a_lane_reaches_this_process_s_group_or_init(
    monkeypatch: pytest.MonkeyPatch, whose: str
) -> None:
    sent: list[int] = []
    monkeypatch.setattr(clip_node.os, "killpg", lambda group, sig: sent.append(group))
    pid = {"zero": 0, "init": 1, "this process's": os.getpgrp()}[whose]
    clip_node._signal_group(types.SimpleNamespace(pid=pid), signal.SIGKILL)
    assert sent == []


@pytest.mark.parametrize(
    "char",
    ["x", "\x1b", "\u00e9", "\U0001f50a"],
    ids=["ascii", "control", "accent", "astral"],
)
def test_a_failing_lane_s_log_is_cut_to_what_a_frame_carries(
    tmp_path: pathlib.Path, char: str
) -> None:
    """Forty lines of 40 000 characters would make a header past the reader's limit.

    The limit is on the header as JSON writes it, where a control character
    takes six bytes and a character past the Basic Multilingual Plane twelve.
    """
    import clip_link

    log = tmp_path / "log.txt"
    lines = [f"{n} {char * 40_000}" for n in range(40)]
    log.write_text("\n".join([*lines, "the last words"]) + "\n", encoding="utf-8")
    failure = clip_node._failure("anim_x", "the render exited with 1", log)
    stream = io.BytesIO()
    clip_link.send(stream, failure)
    assert len(stream.getvalue()) < bootstrap.MAX_HEADER // 8
    stream.seek(0)
    header, _ = clip_link.receive(stream, lambda _header: [])
    error = header["error"].splitlines()
    assert error[0] == "the render exited with 1"
    assert error[-1] == "the last words"
    assert all(len(json.dumps(line)[1:-1]) <= clip_node._LINE_BYTES for line in error)


def test_only_the_end_of_a_lane_s_log_is_read(tmp_path: pathlib.Path) -> None:
    """A log of any size costs no more than its end: a render that wrote without end."""
    log = tmp_path / "log.txt"
    with log.open("wb") as sink:
        sink.truncate(64 << 20)
        sink.seek(0, os.SEEK_END)
        sink.write(b"\nthe last words\n")
    failure = clip_node._failure("anim_x", "the render exited with 1", log)
    assert len(json.dumps(failure)) < bootstrap.MAX_HEADER // 8
    assert failure["error"].splitlines()[-1] == "the last words"


def test_a_last_line_longer_than_what_is_read_is_still_sent(
    tmp_path: pathlib.Path,
) -> None:
    """A progress meter rewritten with a carriage return past the read window, then a kill.

    Its end is the only text the render left, and a log tail that dropped the
    line read in part would send none.
    """
    log = tmp_path / "log.txt"
    meter = "".join(f"\rframe {n:6d} of 999999" for n in range(5000))
    log.write_text(f"the render started\n{meter}\n", encoding="utf-8")
    assert len(meter) > clip_node._LOG_BYTES
    failure = clip_node._failure("anim_x", "the render exited with -9", log)
    error = failure["error"].splitlines()
    assert error[0] == "the render exited with -9"
    assert error[-1] == "frame   4999 of 999999"


def test_a_refusal_is_cut_to_what_a_frame_carries(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A node's words of any length or number (here CuPy's last line) still make a frame."""
    import clip_link

    said = "the last line " + "\x1b" * 400_000
    monkeypatch.setattr(
        clip_node,
        "readiness",
        lambda root, job: ([said] * 100, clip_node.Room(0, None), {}),
    )
    sent = io.BytesIO()
    clip_link.send(
        sent,
        {
            "type": "job",
            "version": clip_node.PROTOCOL,
            "clips": [{"name": "anim_x", "device": "gpu"}],
            "compute": "cupy",
            "encoder": "av1_nvenc",
            "audit_only": False,
        },
    )
    sent.seek(0)
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(sent))
    frames = tmp_path / "frames"
    with frames.open("wb") as sink:
        assert clip_node.serve(os.dup(sink.fileno())) == 1
    assert frames.stat().st_size < bootstrap.MAX_HEADER // 2
    with frames.open("rb") as stream:
        answer, _ = clip_link.receive(stream, lambda _header: [])
    *problems, more = answer["problems"]
    assert all(problem.startswith("the last line ") for problem in problems)
    assert more == f"and {100 - len(problems)} more"


def test_the_longest_refusal_stays_under_half_the_reader_s_limit() -> None:
    """The worst case: every problem lines that pack its 8 KiB exactly, and a count of the rest.

    A control character takes six bytes once escaped, so 341 of them make a
    line of 2046 bytes, and four such lines, with the escaped newlines
    between them, fill a problem's 8 KiB to the last two bytes.
    """
    import clip_link

    line = "\x1b" * 341
    problem = "\n".join([line] * 10)
    refusal = clip_node._refusal([problem] * 1_000_000)
    *problems, more = refusal["problems"]
    assert len(problems) == clip_node._MAX_PROBLEMS
    assert all(
        len(json.dumps(shown)) - 2 == clip_node._TEXT_BYTES - 2 for shown in problems
    )
    assert more == f"and {1_000_000 - clip_node._MAX_PROBLEMS} more"
    stream = io.BytesIO()
    clip_link.send(stream, refusal)
    start = len(bootstrap.MAGIC) + 4
    assert len(stream.getvalue()) - start < bootstrap.MAX_HEADER // 2


def test_a_clip_encoder_is_read_by_name() -> None:
    assert clip_node._encoder("av1_nvenc") == "av1_nvenc"
    assert clip_node._encoder("libsvtav1") == "libsvtav1"
    with pytest.raises(ValueError, match=r"encoder"):
        clip_node._encoder("libvpx-vp9")
