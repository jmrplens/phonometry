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
    first = node_image.context_archive(_ROOT)
    second = node_image.context_archive(_ROOT)
    assert first == second


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


_HOSTS = """\
[hosts.nas]
ssh = "root@192.168.0.40"
runner = "docker"
image = "phonometry-node:gpu"

[hosts.lab]
ssh = "lab"
runner = "python"
python = "/usr/bin/python3"
"""
#: A stand-in for ssh: it reads the build context from its standard input and
#: exits with the number of files in it.
_COUNT_THE_CONTEXT = (
    "import io, sys, tarfile\n"
    "with tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read())) as archive:\n"
    "    sys.exit(len(archive.getnames()))\n"
)


@pytest.fixture
def hosts_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A hosts file with a Docker node and a Python node, read in place of the user's."""
    path = tmp_path / "hosts.toml"
    path.write_text(_HOSTS, encoding="utf-8")
    monkeypatch.setenv("PHONOMETRY_HOSTS_FILE", str(path))
    monkeypatch.setattr(command, "_SSH_PROGRAM", ("ssh",))
    return path


def test_the_build_needs_a_host(
    hosts_file: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit, match="^2$"):
        node_image.main(["--host", ""])
    assert "make node-image HOST=<name>" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("host", "refusal"),
    [
        ("nowhere", "no host 'nowhere' in .*hosts.toml; it names lab, nas"),
        ("lab", "host 'lab' runs Python, not Docker"),
    ],
)
def test_the_build_refuses_a_host_it_cannot_build_on(
    hosts_file: Path, host: str, refusal: str
) -> None:
    with pytest.raises(SystemExit, match=refusal):
        node_image.main(["--host", host])


def test_the_build_names_a_missing_hosts_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PHONOMETRY_HOSTS_FILE", str(tmp_path / "absent.toml"))
    with pytest.raises(SystemExit, match="absent.toml does not exist"):
        node_image.main(["--host", "nas"])


def test_the_build_names_a_missing_ssh(
    hosts_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(command, "_SSH_PROGRAM", None)
    monkeypatch.setenv("PATH", str(tmp_path / "no-programs-here"))
    with pytest.raises(SystemExit, match="no ssh client on PATH"):
        node_image.main(["--host", "nas"])


def test_the_build_pipes_the_context_to_ssh_and_returns_its_exit_status(
    hosts_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        command, "_SSH_PROGRAM", (sys.executable, "-c", _COUNT_THE_CONTEXT)
    )
    assert node_image.main(["--host", "nas", "--target", "cpu"]) == len(
        node_image.CONTEXT
    )
    assert capsys.readouterr().out.startswith(
        "building phonometry-node:gpu (cpu) on nas"
    )


def test_cupy_cannot_replace_the_pinned_numpy() -> None:
    """CuPy goes in without its requirements, and pip check stops a NumPy outside its range."""
    assert re.search(
        r"^RUN pip install --no-cache-dir --no-deps cupy-cuda13x==\S+ cuda-pathfinder==\S+ \\\n"
        r"\s+&& pip check$",
        _TEXT,
        flags=re.MULTILINE,
    )


def test_the_files_a_node_runs_keep_their_line_endings() -> None:
    """A CRLF checkout would break the provisioning script and the image's copy of the Dockerfile."""
    attributes = (_ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
    assert {"*.sh text eol=lf", "docker/node/Dockerfile text eol=lf"} <= set(attributes)
    for name in ("docker/node/Dockerfile", "docker/node/provision.sh"):
        assert b"\r" not in (_ROOT / name).read_bytes(), name
