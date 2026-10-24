#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The clip transport speaks the remote frames and runs its own program on a node.

``scripts/clip_link.py`` is the one file that names the remote machinery's
private pieces. These tests hold what the clip transport relies on: a frame
comes back as it was sent and frames follow one another on one stream; a
header the reader refuses, or whose announced sizes disagree with what the
reader expects, costs no read of its buffers; a stream that breaks says so; a
node's text is shown with its control characters escaped; a node's Python
runs the program it is sent and leaves the rest of the input to it; a Docker
node runs that program in the image instead of the image's own bootstrap, and
sees its one GPU as index 0.
"""

from __future__ import annotations

import io
import pathlib
import shlex
import subprocess
import sys
from typing import Any

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

import clip_link

from phonometry.simulation import Compute
from phonometry.simulation._remote import bootstrap, command
from phonometry.simulation._remote.hosts import HostEntry

_DOCKER = HostEntry(
    name="nas",
    ssh="root@192.168.0.40",
    runner="docker",
    target="phonometry-node:gpu",
    label="the NAS",
    timeout_s=None,
)
_PYTHON = HostEntry(
    name="lab",
    ssh="lab",
    runner="python",
    target="/opt/env/bin/python",
    label="the lab",
    timeout_s=None,
)
#: The longest the loader may take to run a program of one line [s].
_LOADER_TIMEOUT_S = 60


def _sizes(header: dict[str, Any]) -> list[int]:
    return [int(size) for size in header["buffers"]]


def test_a_frame_comes_back_as_it_was_sent() -> None:
    stream = io.BytesIO()
    clip_link.send(stream, {"type": "clip"}, [b"abc", b"", b"hello"])
    stream.seek(0)
    header, buffers = clip_link.receive(stream, _sizes)
    assert header["type"] == "clip"
    assert buffers == [b"abc", b"", b"hello"]


def test_frames_follow_one_another() -> None:
    stream = io.BytesIO()
    clip_link.send(stream, {"type": "a"}, [b"x"])
    clip_link.send(stream, {"type": "b"})
    stream.seek(0)
    assert clip_link.receive(stream, _sizes)[0]["type"] == "a"
    assert clip_link.receive(stream, _sizes)[0]["type"] == "b"


def test_a_refused_header_reads_none_of_its_buffers() -> None:
    stream = io.BytesIO()
    clip_link.send(stream, {"type": "clip"}, [b"data"])
    stream.seek(0)

    def refuse(header: dict[str, Any]) -> list[int]:
        msg = "not this one"
        raise ValueError(msg)

    with pytest.raises(ValueError, match=r"not this one"):
        clip_link.receive(stream, refuse)
    assert b"data" in stream.read()


def test_sizes_that_disagree_with_the_frame_are_refused() -> None:
    stream = io.BytesIO()
    clip_link.send(stream, {"type": "clip"}, [b"data"])
    stream.seek(0)
    with pytest.raises(ValueError, match=r"announces"):
        clip_link.receive(stream, lambda header: [3])
    assert stream.read() == b"data"


def test_a_stream_that_breaks_says_so() -> None:
    stream = io.BytesIO()
    clip_link.send(stream, {"type": "clip"}, [b"0123456789"])
    cut = io.BytesIO(stream.getvalue()[:-4])
    with pytest.raises(EOFError, match=r"4 bytes short"):
        clip_link.receive(cut, _sizes)


def test_a_stream_that_is_not_a_frame_says_so() -> None:
    stream = io.BytesIO(b"Traceback (most recent call last)")
    with pytest.raises(EOFError, match=r"does not start a frame"):
        clip_link.receive(stream, _sizes)


def test_a_node_s_text_is_shown_with_its_control_characters_escaped() -> None:
    """An OSC 52 sequence in a log tail would write to the clipboard of some terminals."""
    shown = clip_link.printable("line one\n\tline two\x1b]52;c;ZXZpbA==\x07")
    assert shown == "line one\n\tline two\\x1b]52;c;ZXZpbA==\\x07"


def test_a_node_runs_the_program_it_is_sent_and_leaves_it_the_rest() -> None:
    sent = io.BytesIO()
    clip_link.send_program(
        sent, "import sys; sys.stderr.write(sys.stdin.buffer.read().decode())"
    )
    done = subprocess.run(
        [sys.executable, "-I", "-c", clip_link.loader()],
        input=sent.getvalue() + b"the frames",
        capture_output=True,
        check=False,
        timeout=_LOADER_TIMEOUT_S,
    )
    assert (done.returncode, done.stderr) == (0, b"the frames")


def test_a_docker_node_runs_the_loader_for_a_clip_job(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(command, "_SSH_PROGRAM", ("ssh",))
    argv = clip_link.node_command(
        _DOCKER, Compute(device="cupy", device_index=1, host="nas")
    )
    _, _, script = shlex.split(argv[-1])
    docker = shlex.split(script)
    assert docker[docker.index("--gpus") + 1] == "device=1"
    # The container's entrypoint is the image's Python, whatever the image
    # names, and the image is given the loader in place of the bootstrap.
    assert docker[docker.index("--entrypoint") + 1] == "python"
    assert docker[-4:] == ["phonometry-node:gpu", "-I", "-c", command.LOADER]
    assert bootstrap.IMAGE_PATH not in script


def test_the_image_s_own_bootstrap_is_still_the_default() -> None:
    script = command.remote_command(_DOCKER, Compute(device="cupy", host="nas"))
    assert bootstrap.IMAGE_PATH in script


def test_a_python_node_runs_the_loader_either_way() -> None:
    request = Compute(host="lab")
    assert command.remote_command(
        _PYTHON, request, loader=True
    ) == command.remote_command(_PYTHON, request)


def test_the_lanes_see_the_gpu_the_node_shows_them_and_never_the_host() -> None:
    request = Compute(device="cupy", device_index=1, host="nas")
    assert clip_link.lane_placement(_DOCKER, request) == "cupy"
    assert (
        clip_link.lane_placement(
            _PYTHON, Compute(device="cupy", device_index=1, host="lab")
        )
        == "cupy:1"
    )
    assert (
        clip_link.lane_placement(
            _DOCKER, Compute(device="cupy", fallback=True, host="nas")
        )
        == "cupy,fallback"
    )
    assert clip_link.lane_placement(_DOCKER, Compute(host="nas")) == "cpu"
