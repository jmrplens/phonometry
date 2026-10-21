#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The node image: its two stages, its pins, and the bootstrap where the client runs it."""

from __future__ import annotations

import io
import json
import re
import shlex
import sys
import tarfile
from pathlib import Path

import pytest

from phonometry.simulation._remote import bootstrap, command
from phonometry.simulation._remote.hosts import HostEntry

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_ROOT / "scripts"))

import gpu_parity
import node_ffmpeg
import node_image

_TEXT = (_ROOT / "docker" / "node" / "Dockerfile").read_text(encoding="utf-8")
_STAGES = {
    stage: image
    for image, stage in re.findall(
        r"^FROM\s+(\S+)\s+AS\s+(\w+)\s*$", _TEXT, flags=re.MULTILINE
    )
}
_NAS = HostEntry(
    name="nas",
    ssh="root@192.168.0.40",
    runner="docker",
    target="phonometry-node:gpu",
    label="the NAS",
    timeout_s=None,
)


def test_the_image_has_a_gpu_and_a_cpu_stage_each_pinned_by_digest() -> None:
    assert sorted(_STAGES) == ["cpu", "gpu"]
    assert all("@sha256:" in image for image in _STAGES.values())
    assert _STAGES["gpu"].startswith("nvidia/cuda:13.3.1-runtime-ubuntu24.04@")
    assert _STAGES["cpu"].startswith("ubuntu:24.04@")


def test_the_proof_reads_the_base_of_the_gpu_stage() -> None:
    assert gpu_parity.base_image_of(_TEXT) == _STAGES["gpu"]


def test_each_stage_puts_the_bootstrap_where_the_client_runs_it() -> None:
    copies = re.findall(
        r"^COPY\s+src/phonometry/simulation/_remote/bootstrap\.py\s+(\S+)\s*$",
        _TEXT,
        flags=re.MULTILINE,
    )
    assert copies == [bootstrap.IMAGE_PATH, bootstrap.IMAGE_PATH]


def test_the_gpu_stage_reaches_the_video_encoder() -> None:
    assert re.search(r"NVIDIA_DRIVER_CAPABILITIES=\S*\bvideo\b", _TEXT)


def test_ffmpeg_is_a_static_build_pinned_by_url_and_sha256() -> None:
    pinned = node_ffmpeg.pin(_TEXT)
    assert pinned.url.startswith(
        "https://github.com/BtbN/FFmpeg-Builds/releases/download/autobuild-"
    )
    assert re.search(
        r"/ffmpeg-n\d+\.\d+[^/]*-linux64-gpl-\d+\.\d+\.tar\.xz$", pinned.url
    )
    assert re.fullmatch(r"[0-9a-f]{64}", pinned.sha256)


def test_each_stage_installs_the_pinned_ffmpeg_and_apt_installs_none() -> None:
    assert re.findall(
        r"^ARG (FFMPEG_URL|FFMPEG_SHA256)$", _TEXT, flags=re.MULTILINE
    ) == [
        "FFMPEG_URL",
        "FFMPEG_SHA256",
        "FFMPEG_URL",
        "FFMPEG_SHA256",
    ]
    provision = (_ROOT / "docker" / "node" / "provision.sh").read_text(encoding="utf-8")
    assert "sha256sum -c" in provision
    for packages in re.findall(
        r"apt-get install -y --no-install-recommends((?:\\\n|[^\n])*)", provision
    ):
        assert "ffmpeg" not in packages.split()


def test_the_cupy_of_the_image_is_the_cupy_of_the_proof() -> None:
    lock = json.loads((_ROOT / "gpu-parity.lock").read_text(encoding="utf-8"))
    assert f"cupy-cuda13x=={lock['cupy']}" in _TEXT


def test_the_build_context_holds_exactly_what_the_dockerfile_copies() -> None:
    copied = {
        word
        for line in re.findall(r"^COPY\s+(.+)$", _TEXT, flags=re.MULTILINE)
        for word in line.split()[:-1]
    }
    with tarfile.open(fileobj=io.BytesIO(node_image.context_archive(_ROOT))) as archive:
        names = set(archive.getnames())
    assert names == copied == set(node_image.CONTEXT)


def test_the_build_context_is_the_same_bytes_every_time() -> None:
    assert node_image.context_archive(_ROOT) == node_image.context_archive(_ROOT)


def test_the_build_runs_on_the_node_and_tags_the_entry_s_image(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(command, "_SSH_PROGRAM", ("ssh",))
    argv = node_image.build_command(_NAS, "gpu")
    assert argv[argv.index("--") + 1] == "root@192.168.0.40"
    assert shlex.split(argv[-1]) == [
        "docker",
        "build",
        "--target",
        "gpu",
        "-t",
        "phonometry-node:gpu",
        "-f",
        "docker/node/Dockerfile",
        "-",
    ]


def test_a_python_node_has_no_image_to_build() -> None:
    lab = HostEntry(
        name="lab",
        ssh="lab",
        runner="python",
        target="/usr/bin/python3",
        label="lab",
        timeout_s=None,
    )
    with pytest.raises(SystemExit, match="runs Python, not Docker"):
        node_image.build_command(lab, "gpu")
