#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A video written on a real node: the result equals the local run, the file decodes.

Runs only where ``PHONOMETRY_TEST_NODE`` names a node in the hosts file: the
CI job "Remote simulation on a localhost node", which serves the cpu stage of
the node image (with its pinned ffmpeg build and the figure stack) built
with the pins of the job, so the run steps the same numbers, and installs
the ffprobe that decodes the video here.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import TYPE_CHECKING

import numpy as np
import pytest

from phonometry.io import VideoOptions
from phonometry.simulation import (
    AnimationFrame,
    Compute,
    FDTDRecording,
    FDTDRun,
    GaussianPulse,
    fdtd_simulation,
    write_fdtd_animation,
)

if TYPE_CHECKING:
    from pathlib import Path

_NODE = os.environ.get("PHONOMETRY_TEST_NODE", "")

pytestmark = [
    pytest.mark.skipif(
        not _NODE or shutil.which("ffprobe") is None,
        reason="needs a node named by PHONOMETRY_TEST_NODE and ffprobe here; the remote-node CI job has both",
    ),
    pytest.mark.xdist_group("localhost-node"),
]


def test_a_node_s_video_and_result(tmp_path: Path) -> None:
    run = FDTDRun(
        c=343.0,
        dx=0.01,
        duration_s=2e-3,
        shape=(60, 80),
        sources=[GaussianPulse(ix=40, iy=30, half_width_s=4e-5)],
        recording=FDTDRecording(probes=[(10, 10), (70, 50)], snapshot_every=10),
    )
    target = tmp_path / "node.webm"
    res = write_fdtd_animation(
        target,
        run,
        compute=Compute(host=_NODE),
        frame=AnimationFrame(size=(480, 246)),
        video=VideoOptions(encoder="cpu"),
    )
    local = fdtd_simulation(run)
    assert np.array_equal(res.pressures, local.pressures)
    assert np.array_equal(res.times, local.times)
    assert res.snapshots is None
    assert res.provenance.host == _NODE
    shown = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-count_frames",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name,width,height,nb_read_frames",
            "-of",
            "default=noprint_wrappers=1",
            str(target),
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    ).stdout
    probe = dict(line.split("=", 1) for line in shown.splitlines())
    # The node image's pinned ffmpeg carries SVT-AV1, so the CPU writes AV1.
    assert probe["codec_name"] == "av1"
    assert (probe["width"], probe["height"]) == ("480", "246")
    assert int(probe["nb_read_frames"]) == (res.times.size - 1) // 10 + 1
