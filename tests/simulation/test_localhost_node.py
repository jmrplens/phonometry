#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A remote run on a real node, over a real ssh, equals the run here.

The CI job "Remote simulation on a localhost node" builds the cpu stage of
the node image with the pins it installs itself, serves it through sshd on
localhost, names it in a hosts file and sets PHONOMETRY_TEST_NODE to that
name. Without it this module skips: it needs Docker and an sshd that only
that job sets up. The run here and the run there share the pins, the C
library and the CPU, so they agree bit for bit.
"""

from __future__ import annotations

import dataclasses
import json
import logging
import os
from typing import TYPE_CHECKING

import numpy as np
import pytest
from test_remote_simulation import _assert_same_result

from phonometry.simulation import (
    Compute,
    ComputeRemoteError,
    ElasticRecording,
    ElasticRun,
    ExplosionSource,
    FDTDBoundaries,
    FDTDRecording,
    FDTDRun,
    GaussianPulse,
    elastic_fdtd_simulation,
    fdtd_simulation,
)
from phonometry.simulation._remote import hosts, package

if TYPE_CHECKING:
    from pathlib import Path

NODE = os.environ.get("PHONOMETRY_TEST_NODE", "")
pytestmark = [
    pytest.mark.skipif(
        not NODE,
        reason="PHONOMETRY_TEST_NODE names no node; the remote-node CI job sets one up",
    ),
    pytest.mark.xdist_group("localhost-node"),
]


def _acoustic(duration: float) -> FDTDRun:
    mask = np.zeros((120, 160), dtype=bool)
    mask[50:70, 90:95] = True
    return FDTDRun(
        c=343.0,
        dx=0.01,
        duration_s=duration,
        shape=(120, 160),
        sources=[GaussianPulse(ix=30, iy=60, half_width_s=4e-5)],
        recording=FDTDRecording(
            probes=[(120, 60), (80, 20)], snapshot_every=25, snapshot_decimation=2
        ),
        boundaries=FDTDBoundaries(sides="absorbing", absorbing_layer_cells=12),
        obstacle_mask=mask,
    )


def test_a_remote_acoustic_run_equals_the_run_here() -> None:
    # One run for both, as the tests over fake_ssh.py in
    # test_remote_simulation.py do: a record's sources are compared, and a
    # bound waveform built twice is two.
    run = _acoustic(4e-3)
    here = fdtd_simulation(run)
    there = fdtd_simulation(run, compute=Compute(host=NODE))
    _assert_same_result(there, here)
    assert there.provenance.host == NODE
    assert there.provenance.package_sha256 == package.installed_package().digest
    assert (
        dataclasses.replace(there.provenance, host=None, package_sha256=None)
        == here.provenance
    )


def test_a_remote_elastic_run_equals_the_run_here() -> None:
    run = ElasticRun(
        c_p=4000.0,
        c_s=2300.0,
        dx=0.01,
        duration_s=4e-4,
        rho=2500.0,
        shape=(60, 61),
        sources=[
            ExplosionSource(
                ix=30,
                iy=29,
                waveform=GaussianPulse(ix=0, iy=0, half_width_s=1e-5).value,
            )
        ],
        recording=ElasticRecording(
            probes=[(10, 10), (40, 20)], probe_fields=("p", "vy"), snapshot_every=10
        ),
    )
    here = elastic_fdtd_simulation(run)
    there = elastic_fdtd_simulation(run, compute=Compute(host=NODE))
    _assert_same_result(there, here)
    assert there.provenance.host == NODE


def test_the_second_run_finds_the_package_on_the_node(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="phonometry.simulation")
    fdtd_simulation(_acoustic(1e-3), compute=Compute(host=NODE))
    caplog.clear()
    fdtd_simulation(_acoustic(1e-3), compute=Compute(host=NODE))
    messages = [record.getMessage() for record in caplog.records]
    assert not any("sending the package" in m for m in messages)
    assert any(m.endswith("fdtd_simulation done") for m in messages)


def test_a_node_without_the_image_asks_for_make_node_image(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    entry = hosts.load_host(NODE)
    file = tmp_path / "hosts.toml"
    file.write_text(
        "[hosts.absent]\n"
        f"ssh = {json.dumps(entry.ssh)}\n"
        'runner = "docker"\n'
        'image = "phonometry-node:absent"\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("PHONOMETRY_HOSTS_FILE", str(file))
    run = _acoustic(1e-3)
    request = Compute(host="absent")
    with pytest.raises(ComputeRemoteError, match="make node-image HOST=absent"):
        fdtd_simulation(run, compute=request)
