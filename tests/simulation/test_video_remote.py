#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A video written on a node: the run here, the bytes checked, nothing started on a bad argument.

The node is this machine, reached through the stand-in for ssh
(``tests/simulation/fake_ssh.py``) by the ``node`` fixture; ffmpeg is the fake
of ``tests/fake_ffmpeg.py``, which the node's own process finds on PATH.
"""

from __future__ import annotations

import contextlib
import dataclasses
import errno
import inspect
import pathlib
import shutil
import subprocess
import sys
import warnings
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest

pytest.importorskip("matplotlib")
import child_process
import fake_ffmpeg
import matplotlib as mpl
import refusing_disk

from phonometry import io
from phonometry.io import VideoOptions
from phonometry.io._video import video_request
from phonometry.simulation import (
    AnimationFrame,
    Compute,
    ComputeFallbackWarning,
    ComputeRemoteError,
    ElasticRecording,
    ElasticRun,
    ExplosionSource,
    FDTDRecording,
    FDTDRun,
    GaussianPulse,
    _video_job,
    elastic_fdtd_simulation,
    fdtd_simulation,
    use,
    write_elastic_fdtd_animation,
    write_fdtd_animation,
)
from phonometry.simulation import video as video_module
from phonometry.simulation._remote import client, package

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path
    from typing import BinaryIO

    from _typeshed import SupportsWrite

pytestmark = pytest.mark.xdist_group("remote-node")

_WEBM = b"\x1a\x45\xdf\xa3"
_SOURCE = GaussianPulse(ix=20, iy=15, half_width_s=4e-5)
_EXPLOSION = ExplosionSource(
    ix=12, iy=10, waveform=GaussianPulse(ix=0, iy=0, half_width_s=2e-5).value
)
_RUN = FDTDRun(
    c=343.0,
    dx=0.01,
    duration_s=1e-3,
    shape=(30, 40),
    sources=[_SOURCE],
    recording=FDTDRecording(probes=[(5, 5)], snapshot_every=10),
)
#: An elastic run of 471 steps, a frame every 50 of them: ten frames, which
#: the node draws one at a time. A frame every fifth step, 95 of them, made
#: the two tests that write it take about 17 s, against 5 s, and tested no
#: more: neither counts the frames.
_ELASTIC = ElasticRun(
    c_p=4000.0,
    c_s=2300.0,
    dx=0.01,
    duration_s=5e-4,
    rho=2500.0,
    shape=(20, 24),
    sources=[_EXPLOSION],
    recording=ElasticRecording(probes=[(4, 4)], snapshot_every=50),
)
_FRAME = AnimationFrame(size=(480, 246), color_limit=1.0)


def _partials(directory: Path) -> list[str]:
    return [p.name for p in directory.iterdir() if p.name.endswith(".partial")]


def test_a_node_writes_the_video_and_this_machine_the_file(
    node: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    target = tmp_path / "remote.webm"
    res = write_fdtd_animation(target, _RUN, compute=Compute(host=node), frame=_FRAME)
    here = fdtd_simulation(_RUN)
    assert np.array_equal(res.pressures, here.pressures)
    assert np.array_equal(res.times, here.times)
    assert res.snapshots is None
    assert res.provenance.host == node
    # The rest of the provenance is the run's here, the node's package aside.
    assert res.provenance.package_sha256 == package.installed_package().digest
    assert (
        dataclasses.replace(res.provenance, host=None, package_sha256=None)
        == here.provenance
    )
    assert target.read_bytes().startswith(_WEBM)
    # The node encoded into a scratch directory of its own, not into `target`.
    assert "phonometry-video-" in fake.encodes()[0]["argv"][-1]
    assert _partials(tmp_path) == []


def test_a_node_encodes_vaapi_on_the_device_named(
    node: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The device is the node's: it travels with the options and is used there."""
    fake = fake_ffmpeg.install(
        tmp_path, monkeypatch, encoders=["av1_vaapi"], working=["av1_vaapi"]
    )
    video = VideoOptions(encoder="vaapi", vaapi_device="/dev/dri/renderD129")
    target = tmp_path / "vaapi.webm"
    res = write_fdtd_animation(
        target, _RUN, compute=Compute(host=node), frame=_FRAME, video=video
    )
    assert res.provenance.host == node
    (trial,) = fake.trials()
    (encode,) = fake.encodes()
    assert "phonometry-video-" in encode["argv"][-1]
    for argv in (trial["argv"], encode["argv"]):
        assert argv[argv.index("-vaapi_device") + 1] == "/dev/dri/renderD129"
    assert target.read_bytes().startswith(_WEBM)


def test_an_elastic_video_on_a_node(
    node: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_ffmpeg.install(tmp_path, monkeypatch)
    target = tmp_path / "elastic.webm"
    res = write_elastic_fdtd_animation(
        target,
        _ELASTIC,
        compute=Compute(host=node),
        frame=AnimationFrame(size=(480, 246), color_limit=1e-6),
    )
    assert np.array_equal(res.signals, elastic_fdtd_simulation(_ELASTIC).signals)
    assert res.provenance.host == node
    assert target.read_bytes().startswith(_WEBM)


#: A client process that cannot import matplotlib, writing a video on the node
#: the test's fixture names: argv is the stand-in for ssh, the path, the host.
_WITHOUT_MATPLOTLIB = """
import importlib.abc
import sys


class _Absent(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name.partition(".")[0] == "matplotlib":
            raise ImportError(f"{name} is not installed on this machine")
        return None


sys.meta_path.insert(0, _Absent())
from phonometry.simulation import (
    AnimationFrame, Compute, FDTDRecording, FDTDRun, GaussianPulse,
    write_fdtd_animation,
)
from phonometry.simulation._remote import command

command._SSH_PROGRAM = (sys.executable, sys.argv[1])
run = FDTDRun(
    c=343.0, dx=0.01, duration_s=1e-3, shape=(30, 40),
    sources=[GaussianPulse(ix=20, iy=15, half_width_s=4e-5)],
    recording=FDTDRecording(probes=[(5, 5)], snapshot_every=10),
)
res = write_fdtd_animation(
    sys.argv[2], run, compute=Compute(host=sys.argv[3]),
    frame=AnimationFrame(size=(480, 246)),
)
print(res.provenance.host, "matplotlib" in sys.modules)
"""


def test_a_client_without_matplotlib_writes_on_a_node(
    node: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only the node draws: this machine checks the frame and the path, and writes the bytes, with no matplotlib.

    The colour limit is found on the node too, by a first pass there.
    """
    fake_ffmpeg.install(tmp_path, monkeypatch)
    target = tmp_path / "remote.webm"
    fake_ssh = pathlib.Path(__file__).with_name("fake_ssh.py")
    done = child_process.run(
        [sys.executable, "-c", _WITHOUT_MATPLOTLIB, str(fake_ssh), str(target), node],
        timeout=300,
        capture_output=True,
        text=True,
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout.split() == [node, "False"]
    assert target.read_bytes().startswith(_WEBM)


def test_a_client_without_ffmpeg_writes_on_a_node(
    node: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_ffmpeg.install(tmp_path, monkeypatch)
    # This process cannot find ffmpeg; the node's, a process of its own, finds the fake on PATH.
    monkeypatch.setitem(mpl.rcParams, "animation.ffmpeg_path", "no-such-ffmpeg-here")
    target = tmp_path / "remote.webm"
    write_fdtd_animation(target, _RUN, compute=Compute(host=node), frame=_FRAME)
    assert target.read_bytes().startswith(_WEBM)


@pytest.mark.parametrize(
    ("function", "run", "frame", "asked"),
    [
        (write_fdtd_animation, _RUN, None, "argument"),
        (write_fdtd_animation, _RUN, _FRAME, "use"),
        (write_fdtd_animation, _RUN, _FRAME, "environment"),
        (
            write_elastic_fdtd_animation,
            _ELASTIC,
            AnimationFrame(size=(480, 246), color_limit=1e-6),
            "argument",
        ),
    ],
)
def test_the_ffmpeg_here_is_never_run_on_the_remote_route(
    function: Callable[..., object],
    run: object,
    frame: AnimationFrame | None,
    asked: str,
    node: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Two fakes, each with a log of its own: this process's, which rcParams
    # names, and the node's, which the node finds on PATH. A fake reads its
    # spec, and so its log, from the environment, and ssh starts with the
    # node's. A colour limit found in a first pass (frame=None) is found
    # there too. The host is named by the argument, by use() or by
    # PHONOMETRY_COMPUTE.
    (tmp_path / "node").mkdir()
    (tmp_path / "here").mkdir()
    there = fake_ffmpeg.install(tmp_path / "node", monkeypatch)
    here = fake_ffmpeg.install(tmp_path / "here", monkeypatch)
    real_popen = client._popen

    def ssh_with_the_node_s_fake(argv: list[str]) -> subprocess.Popen[bytes]:
        with monkeypatch.context() as started:
            started.setenv(fake_ffmpeg.SPEC_VARIABLE, str(there.spec_file))
            return real_popen(argv)

    monkeypatch.setattr(client, "_popen", ssh_with_the_node_s_fake)
    if asked == "environment":
        monkeypatch.setenv("PHONOMETRY_COMPUTE", f"cpu@{node}")
    request = Compute(host=node)
    target = tmp_path / "remote.webm"
    with use(request) if asked == "use" else contextlib.nullcontext():
        res = function(
            target, run, compute=request if asked == "argument" else None, frame=frame
        )
    assert res.provenance.host == node  # type: ignore[attr-defined]
    assert here.calls() == []
    assert len(there.encodes()) == 1
    assert target.read_bytes().startswith(_WEBM)


@pytest.mark.parametrize(
    ("changes", "error", "match"),
    [
        (
            {
                "run": FDTDRun(
                    c=343.0,
                    dx=0.01,
                    duration_s=1e-3,
                    shape=(30, 40),
                    sources=[_SOURCE],
                    recording=FDTDRecording(probes=[(5, 5)]),
                )
            },
            ValueError,
            "run.recording.snapshot_every",
        ),
        ({"run": _ELASTIC}, TypeError, "FDTDRun"),
        ({"frame": (480, 246)}, TypeError, "frame"),
        # The last frame at 11132.29 ms: five digits, whose title needs 490 pixels.
        (
            {
                "run": FDTDRun(
                    c=343.0,
                    dx=10.0,
                    duration_s=12.0,
                    shape=(30, 40),
                    sources=[_SOURCE],
                    recording=FDTDRecording(snapshot_every=900),
                ),
                "frame": AnimationFrame(size=(489, 246), color_limit=1.0),
            },
            ValueError,
            r"at least 490 pixels wide",
        ),
        ({"video": {"encoder": "cpu"}}, TypeError, "video"),
        ({"video": VideoOptions(codec="vp9"), "path": "r.mp4"}, ValueError, "holds"),
        ({"path": "r.avi"}, ValueError, "webm"),
    ],
)
def test_a_bad_argument_never_reaches_the_node(
    node: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    changes: dict[str, Any],
    error: type[Exception],
    match: str,
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    log = tmp_path / "ssh.log"
    monkeypatch.setenv("FAKE_SSH_LOG", str(log))
    target = tmp_path / changes.pop("path", "r.webm")
    arguments: dict[str, Any] = {"run": _RUN, "frame": _FRAME, **changes}
    request = Compute(host=node)
    with pytest.raises(error, match=match):
        write_fdtd_animation(target, compute=request, **arguments)
    assert not log.exists()
    assert fake.calls() == []
    assert _partials(tmp_path) == []


def test_a_directory_that_cannot_be_reached_never_reaches_the_node(
    node: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Refused as on this machine: the path's directory sits inside one this
    # process cannot search, so it may exist and still take nothing.
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    log = tmp_path / "ssh.log"
    monkeypatch.setenv("FAKE_SSH_LOG", str(log))
    target = tmp_path / "locked" / "sub" / "r.webm"
    target.parent.mkdir(parents=True)
    refusing_disk.refuse_status(monkeypatch, target.parent)
    request = Compute(host=node, fallback=True)
    with pytest.raises(FileNotFoundError, match="does not exist or cannot be reached"):
        write_fdtd_animation(target, _RUN, compute=request, frame=_FRAME)
    assert not log.exists()
    assert fake.calls() == []


def test_a_waveform_that_cannot_travel_is_refused_before_ssh_starts(
    node: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    log = tmp_path / "ssh.log"
    monkeypatch.setenv("FAKE_SSH_LOG", str(log))
    run = ElasticRun(
        c_p=4000.0,
        c_s=2300.0,
        dx=0.01,
        duration_s=1e-4,
        rho=2500.0,
        shape=(20, 24),
        sources=[ExplosionSource(ix=12, iy=10, waveform=lambda t: 0.0 * t)],
        recording=ElasticRecording(snapshot_every=5),
    )
    request = Compute(host=node)
    frame = AnimationFrame(size=(480, 246), color_limit=1e-6)
    with pytest.raises(
        TypeError, match=r"sources\[0\]\.waveform cannot travel to a node"
    ):
        write_elastic_fdtd_animation(
            tmp_path / "w.webm", run, compute=request, frame=frame
        )
    assert not log.exists()
    assert _partials(tmp_path) == []


def test_an_unknown_node_is_a_missing_key(node: str, tmp_path: Path) -> None:
    request = Compute(host="elsewhere")
    with pytest.raises(KeyError, match="no host 'elsewhere'"):
        write_fdtd_animation(tmp_path / "k.webm", _RUN, compute=request, frame=_FRAME)


@pytest.mark.parametrize(
    ("function", "run"),
    [(write_fdtd_animation, _RUN), (write_elastic_fdtd_animation, _ELASTIC)],
)
def test_the_remote_route_sends_every_parameter(
    function: Callable[..., object],
    run: object,
    node: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent: dict[str, object] = {}

    class Sent(Exception):
        pass

    def capture(
        name: str,
        request: Compute,
        arguments: dict[str, object],
        *rest: object,
        **options: object,
    ) -> None:
        sent.update(arguments)
        raise Sent

    monkeypatch.setattr(client, "run_remote", capture)
    request = Compute(host=node)
    with pytest.raises(Sent):
        function(tmp_path / "s.webm", run, compute=request)
    assert set(sent) == set(inspect.signature(function).parameters) - {
        "path",
        "compute",
    } | {"container"}
    assert sent["frame"] == AnimationFrame()
    assert sent["video"] == VideoOptions()
    assert _partials(tmp_path) == []


def test_bytes_that_are_not_the_container_never_reach_path(
    node: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_ffmpeg.install(tmp_path, monkeypatch)
    target = tmp_path / "kept.webm"
    target.write_bytes(b"the video that was there")
    # The client's view of what a WebM begins with; the node's file is a real (fake) WebM.
    monkeypatch.setattr(
        _video_job, "CONTAINER_HEADS", MappingProxyType({"webm": ((0, b"NOPE"),)})
    )
    request = Compute(host=node)
    with pytest.raises(
        ComputeRemoteError, match="does not begin as the file the request names"
    ):
        write_fdtd_animation(target, _RUN, compute=request, frame=_FRAME)
    assert target.read_bytes() == b"the video that was there"
    assert _partials(tmp_path) == []


@pytest.mark.parametrize(
    ("name", "value", "match"),
    [
        # The client's ceiling, below the 13 bytes the fake's WebM takes.
        ("video_byte_cap", lambda *_, **__: 4, "more than the 4 the request allows"),
        # A head the fake's WebM is too short to hold.
        (
            "CONTAINER_HEADS",
            MappingProxyType({"webm": ((64, _WEBM),)}),
            "too few to begin as the file",
        ),
    ],
)
def test_too_many_or_too_few_bytes_never_reach_path(
    name: str,
    value: object,
    match: str,
    node: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_ffmpeg.install(tmp_path, monkeypatch)
    target = tmp_path / "kept.webm"
    target.write_bytes(b"the video that was there")
    monkeypatch.setattr(_video_job, name, value)
    request = Compute(host=node)
    with pytest.raises(ComputeRemoteError, match=match):
        write_fdtd_animation(target, _RUN, compute=request, frame=_FRAME)
    assert target.read_bytes() == b"the video that was there"
    assert _partials(tmp_path) == []


@pytest.mark.parametrize("stop", ["remote", "fallback", "interrupt"])
def test_a_stream_that_breaks_after_its_first_bytes_leaves_nothing(
    stop: str, node: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_ffmpeg.install(tmp_path, monkeypatch)
    target = tmp_path / "kept.webm"
    target.write_bytes(b"the video that was there")
    real_drain = client._drain
    written: list[bool] = []

    def breaks(
        session: client.Session,
        spec: client.StreamSpec,
        length: int,
        sink: SupportsWrite[bytes],
    ) -> None:
        class Breaking:
            def write(self, data: bytes) -> None:
                # The first chunk passed its heads and is on disk; then the
                # connection drops, or the caller interrupts.
                sink.write(data)
                written.append(any(_partials(tmp_path)))
                if stop == "interrupt":
                    raise KeyboardInterrupt
                msg = "the connection dropped in the middle of the video"
                raise session.failure(msg)

        real_drain(session, spec, length, Breaking())

    monkeypatch.setattr(client, "_drain", breaks)
    request = Compute(host=node, fallback=stop == "fallback")
    if stop == "remote":
        with pytest.raises(ComputeRemoteError, match="dropped in the middle"):
            write_fdtd_animation(target, _RUN, compute=request, frame=_FRAME)
        assert target.read_bytes() == b"the video that was there"
    elif stop == "interrupt":
        with pytest.raises(KeyboardInterrupt):
            write_fdtd_animation(target, _RUN, compute=request, frame=_FRAME)
        assert target.read_bytes() == b"the video that was there"
    else:
        with pytest.warns(ComputeFallbackWarning, match="dropped in the middle"):
            res = write_fdtd_animation(target, _RUN, compute=request, frame=_FRAME)
        assert res.provenance.host is None
        assert np.array_equal(res.pressures, fdtd_simulation(_RUN).pressures)
        # The video written here, not the node's first bytes.
        assert target.read_bytes().startswith(_WEBM)
    assert written == [True]
    assert _partials(tmp_path) == []


def test_a_finished_video_that_cannot_take_path_s_place_says_where_it_is(
    node: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_ffmpeg.install(tmp_path, monkeypatch)
    target = tmp_path / "held.webm"
    target.write_bytes(b"the video that was there")
    real_replace = pathlib.Path.replace

    def held_open(self: pathlib.Path, other: object) -> pathlib.Path:
        if pathlib.Path(str(other)) == target:
            raise PermissionError(13, "the file is being used by another process")
        return real_replace(self, other)  # type: ignore[arg-type]

    monkeypatch.setattr(pathlib.Path, "replace", held_open)
    request = Compute(host=node)
    with pytest.raises(
        io.VideoEncoderError, match="could not take the place of"
    ) as caught:
        write_fdtd_animation(target, _RUN, compute=request, frame=_FRAME)
    assert target.read_bytes() == b"the video that was there"
    (left,) = [p for p in tmp_path.iterdir() if p.name.endswith(".partial")]
    assert str(left) in str(caught.value)
    assert left.read_bytes().startswith(_WEBM)


def test_a_refused_connection_is_a_remote_error(
    node: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    monkeypatch.setenv("FAKE_SSH_MODE", "refuse")
    target = tmp_path / "r.webm"
    request = Compute(host=node)
    with pytest.raises(ComputeRemoteError, match="refused the ssh key"):
        write_fdtd_animation(target, _RUN, compute=request, frame=_FRAME)
    assert not target.exists()
    assert _partials(tmp_path) == []
    assert fake.calls() == []


def test_a_failed_node_falls_back_here_once_when_asked(
    node: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_ffmpeg.install(tmp_path, monkeypatch)
    monkeypatch.setenv("FAKE_SSH_MODE", "refuse")
    target = tmp_path / "fallback.webm"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        res = write_fdtd_animation(
            target, _RUN, compute=Compute(host=node, fallback=True), frame=_FRAME
        )
    fallbacks = [w for w in caught if issubclass(w.category, ComputeFallbackWarning)]
    assert len(fallbacks) == 1
    assert fallbacks[0].filename == __file__
    assert (res.provenance.host, res.provenance.device) == (None, "cpu")
    assert np.array_equal(res.pressures, fdtd_simulation(_RUN).pressures)
    assert target.read_bytes().startswith(_WEBM)
    assert _partials(tmp_path) == []


def test_a_partial_file_the_system_will_not_remove_does_not_stop_a_fallback(
    node: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The file the node's bytes would have gone into, then the probe of the
    # video written here: both created, so the directory takes a video, and
    # neither removed (a scanner holds them on Windows, or the directory
    # lets no file go), which refuses nothing.
    fake_ffmpeg.install(tmp_path, monkeypatch)
    monkeypatch.setenv("FAKE_SSH_MODE", "refuse")
    refusing_disk.hold_partials(monkeypatch)
    target = tmp_path / "held.webm"
    request = Compute(host=node, fallback=True)
    with pytest.warns(ComputeFallbackWarning, match="refused the ssh key"):
        res = write_fdtd_animation(target, _RUN, compute=request, frame=_FRAME)
    assert res.provenance.host is None
    assert target.read_bytes().startswith(_WEBM)
    assert refusing_disk.partial_sizes(tmp_path) == [0, 0]


@pytest.mark.parametrize("directory", ["refusing", "unsearchable", "proc"])
def test_a_directory_that_cannot_take_the_video_is_refused_before_ssh_starts(
    directory: str, node: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = fake_ffmpeg.install(tmp_path, monkeypatch)
    log = tmp_path / "ssh.log"
    monkeypatch.setenv("FAKE_SSH_LOG", str(log))
    if directory == "proc":
        if not pathlib.Path("/proc/self").is_dir():
            pytest.skip("no /proc, the directory nobody can write a file into")
        target = pathlib.Path("/proc/out.webm")
    else:
        refusing_disk.refuse_partials(monkeypatch)
        target = tmp_path / "out.webm"
    if directory == "unsearchable":
        # A name inside it has no status to read, as well as taking no file.
        refusing_disk.refuse_status(monkeypatch, target)
    request = Compute(host=node, fallback=True)
    with pytest.raises(
        io.VideoEncoderError, match="could not write the video"
    ) as caught:
        write_fdtd_animation(target, _RUN, compute=request, frame=_FRAME)
    assert str(target) in str(caught.value)
    # The caller's path, never the hidden file that was refused.
    assert ".partial" not in str(caught.value)
    assert not log.exists()
    assert fake.calls() == []
    # Listed, not stat'ed: the name of an unsearchable directory has no status.
    assert target.name not in [p.name for p in target.parent.iterdir()]


class _FullDisk:
    """A partial file that takes the first bytes of a write and then finds the disk full.

    Closing it, which writes out what it still holds, fails too, with an
    error of its own.
    """

    def __init__(self, handle: BinaryIO, written: list[int]) -> None:
        self._handle = handle
        self._written = written

    def write(self, data: bytes) -> int:
        self._handle.write(data[:4])
        self._handle.flush()
        self._written.append(self._handle.tell())
        raise OSError(errno.ENOSPC, "No space left on device")

    def close(self) -> None:
        self._handle.close()
        raise OSError(errno.EIO, "Input/output error")


def _filling_disk(monkeypatch: pytest.MonkeyPatch, written: list[int]) -> None:
    """Give every partial file this process opens a disk that fills in the middle of a write."""
    real_open = pathlib.Path.open

    def opened(self: pathlib.Path, *args: Any, **kwargs: Any) -> object:
        handle = real_open(self, *args, **kwargs)
        if self.name.endswith(".partial"):
            return _FullDisk(handle, written)
        return handle

    monkeypatch.setattr(pathlib.Path, "open", opened)


def test_a_disk_that_fills_in_the_middle_of_a_node_s_video_leaves_nothing(
    node: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_ffmpeg.install(tmp_path, monkeypatch)
    target = tmp_path / "kept.webm"
    target.write_bytes(b"the video that was there")
    written: list[int] = []
    _filling_disk(monkeypatch, written)
    # A full disk here is not the node's failure: there is nothing to fall back from.
    request = Compute(host=node, fallback=True)
    with pytest.raises(io.VideoEncoderError, match="No space left on device") as caught:
        write_fdtd_animation(target, _RUN, compute=request, frame=_FRAME)
    # The write's error, not the one closing the file met after it.
    assert "Input/output error" not in str(caught.value)
    assert str(target) in str(caught.value)
    assert written == [4]
    assert target.read_bytes() == b"the video that was there"
    assert _partials(tmp_path) == []


def test_discarding_a_file_that_fails_to_close_removes_it_and_raises_that_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    written: list[int] = []
    _filling_disk(monkeypatch, written)
    request = video_request(tmp_path / "d.webm", VideoOptions())
    partial = video_module._PartialFile(request)
    partial.open()
    assert partial.path.exists()
    with pytest.raises(io.VideoEncoderError, match="Input/output error") as caught:
        partial.discard()
    assert str(request.path) in str(caught.value)
    assert not partial.path.exists()


@pytest.mark.skipif(
    shutil.which("ffmpeg") is None,
    reason="needs ffmpeg on PATH, which the node finds; the CI video job installs it",
)
@pytest.mark.parametrize(
    ("video", "said"),
    [
        (
            VideoOptions(ffmpeg_encoder="phonometry-no-such-encoder"),
            r"has no encoder 'phonometry-no-such-encoder'",
        ),
        (
            VideoOptions(ffmpeg_encoder="libvpx-vp9", ffmpeg_options=("-crf", "99")),
            r"(?s)with the encoder libvpx-vp9; ffmpeg said:.*'crf' out of range",
        ),
    ],
    ids=["unknown-encoder", "refused-option"],
)
def test_an_encoder_or_option_of_the_caller_s_that_the_node_s_ffmpeg_refuses(
    video: VideoOptions, said: str, node: str, tmp_path: Path
) -> None:
    """The node's real ffmpeg refuses: a failure of the node's, in ffmpeg's words, and nothing left here.

    A raw encoder the node lacks is refused before the node steps; options
    it refuses, at the first frames of its encode, as on this machine.
    """
    encoder = video.ffmpeg_encoder
    assert encoder is not None
    listing = subprocess.run(
        ["ffmpeg", "-hide_banner", "-encoders"],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    ).stdout
    if encoder.startswith("lib") and f" {encoder} " not in listing:
        pytest.skip(f"this ffmpeg has no {encoder}")
    target = tmp_path / "raw.webm"
    target.write_bytes(b"the video that was there")
    request = Compute(host=node)
    with pytest.raises(ComputeRemoteError, match=said):
        write_fdtd_animation(target, _RUN, compute=request, frame=_FRAME, video=video)
    assert target.read_bytes() == b"the video that was there"
    assert _partials(tmp_path) == []
