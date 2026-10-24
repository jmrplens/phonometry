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
            cancel=threading.Event(),
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
            cancel=threading.Event(),
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
    cancel = threading.Event()
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
        cancel=threading.Event(),
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
    cancel = threading.Event()
    with clip_node.cancelled_by_signals(cancel):
        os.kill(os.getpid(), sig)
        assert cancel.wait(5.0)
    assert signal.getsignal(sig) == before


def test_the_bootstrap_hands_the_rest_of_stdin_to_the_node(
    tmp_path: pathlib.Path,
) -> None:
    """Sent through the node's loader, it unpacks the archive and loses nothing after it."""
    import clip_link

    stub = (
        "import os, pathlib, shutil, sys\n"
        "def main(argv):\n"
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
            cancel=threading.Event(),
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
            cancel=threading.Event(),
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
        cancel=threading.Event(),
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


def test_a_clip_encoder_is_read_by_name() -> None:
    assert clip_node._encoder("av1_nvenc") == "av1_nvenc"
    assert clip_node._encoder("libsvtav1") == "libsvtav1"
    with pytest.raises(ValueError, match=r"encoder"):
        clip_node._encoder("libvpx-vp9")
