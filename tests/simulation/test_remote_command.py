#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The ssh command line a remote run starts, and the placement its node runs."""

from __future__ import annotations

import dataclasses
import io
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from phonometry.simulation import Compute
from phonometry.simulation._remote import bootstrap, command, node
from phonometry.simulation._remote.hosts import HostEntry

if TYPE_CHECKING:
    from phonometry.simulation.compute import Device, Dtype

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
    target="/opt/my node's env/bin/python",
    label="the lab",
    timeout_s=None,
)


#: A stand-in for a node's program: it writes each word it is given, ended by a NUL.
_WORDS_OUT = '#!/bin/sh\nfor word in "$@"; do printf \'%s\\0\' "$word"; done\n'

_posix_only = pytest.mark.skipif(
    sys.platform == "win32", reason="a node's login shell is a POSIX shell"
)


def _options(argv: list[str]) -> list[str]:
    """The options of an ssh command line: between the program and ``--``."""
    return argv[1 : argv.index("--")]


def _stand_in(path: Path) -> Path:
    """An executable at *path* that writes the words it is given."""
    path.parent.mkdir(parents=True)
    path.write_text(_WORDS_OUT, encoding="utf-8")
    path.chmod(0o755)
    return path


def _through_a_shell(remote: str, home: Path, path: str) -> list[str]:
    """The words the node's program is given when a POSIX shell runs *remote*, as sshd does."""
    done = subprocess.run(
        ["sh", "-c", remote],
        capture_output=True,
        check=True,
        cwd=home,
        env={"HOME": str(home), "PATH": path},
        timeout=60,
    )
    return done.stdout.decode().split("\0")[:-1]


def test_ssh_never_prompts_and_ends_its_options_before_the_destination(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(command, "_SSH_PROGRAM", ("ssh",))
    argv = command.ssh_argv(_DOCKER, Compute(device="cupy", host="nas"))
    assert argv[0] == "ssh"
    assert argv[argv.index("--") + 1] == "root@192.168.0.40"
    assert len(argv) == argv.index("--") + 3  # the destination, then the remote command
    options = _options(argv)
    for setting in (
        "BatchMode=yes",
        "ServerAliveInterval=15",
        "ServerAliveCountMax=4",
        "ConnectTimeout=30",
    ):
        assert options[options.index(setting) - 1] == "-o"


def test_ssh_asks_for_no_terminal_and_forwards_nothing_of_the_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A "RequestTTY force" or a "ForwardAgent yes" that ~/.ssh/config gives the
    # host must not reach a run: a pty rewrites the frames, and a node runs the
    # code it is sent. Options on the command line win over the file.
    monkeypatch.setattr(command, "_SSH_PROGRAM", ("ssh",))
    options = _options(command.ssh_argv(_DOCKER, Compute(host="nas")))
    assert {"-T", "-a", "-x"} <= set(options)
    for setting in ("RequestTTY=no", "ClearAllForwardings=yes"):
        assert options[options.index(setting) - 1] == "-o"


def test_a_docker_node_runs_the_image_s_bootstrap_cut_off_from_the_network() -> None:
    sh, flag, script = shlex.split(
        command.remote_command(
            _DOCKER, Compute(device="cupy", device_index=1, host="nas")
        )
    )
    assert (sh, flag) == ("sh", "-c")
    words = shlex.split(script)
    docker = words[words.index("exec") + 1 :]
    assert docker[:8] == [
        "docker",
        "run",
        "--rm",
        "-i",
        "--init",
        "--pull=never",
        "--network",
        "none",
    ]
    assert docker[docker.index("--gpus") + 1] == "device=1"
    assert docker[docker.index("--user") + 1] == "$(id -u):$(id -g)"
    assert docker[docker.index("-v") + 1] == "$cache:/cache"
    assert docker[-4:] == ["phonometry-node:gpu", "python", "-I", bootstrap.IMAGE_PATH]
    assert 'mkdir -p "$cache"' in script


def test_a_numpy_run_on_a_docker_node_asks_for_no_gpu() -> None:
    assert "--gpus" not in command.remote_command(_DOCKER, Compute(host="nas"))


def test_an_image_name_stays_one_word_whatever_it_holds() -> None:
    odd = dataclasses.replace(_DOCKER, target="reg.example:5000/team/node:gpu;rm -rf")
    _, _, script = shlex.split(command.remote_command(odd, Compute(host="nas")))
    assert "reg.example:5000/team/node:gpu;rm -rf" in shlex.split(script)


def test_a_python_node_runs_its_interpreter_isolated_on_the_loader() -> None:
    words = shlex.split(command.remote_command(_PYTHON, Compute(host="lab")))
    assert words == ["/opt/my node's env/bin/python", "-I", "-c", command.LOADER]


@_posix_only
def test_a_docker_node_s_shell_runs_no_word_of_the_hosts_file(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    _stand_in(bin_dir / "docker")
    odd = dataclasses.replace(
        _DOCKER, target="node:gpu;touch injected $(touch injected) `touch injected`"
    )
    remote = command.remote_command(
        odd, Compute(device="cupy", device_index=1, host="nas")
    )
    words = _through_a_shell(
        remote, tmp_path, f"{bin_dir}{os.pathsep}{os.environ['PATH']}"
    )
    cache = tmp_path / ".cache" / "phonometry" / "remote"
    assert words[-4:] == [odd.target, "python", "-I", bootstrap.IMAGE_PATH]
    assert words[words.index("--user") + 1] == f"{os.getuid()}:{os.getgid()}"
    assert words[words.index("-v") + 1] == f"{cache}:/cache"
    assert cache.is_dir()
    assert not (tmp_path / "injected").exists()


@_posix_only
def test_a_python_node_s_shell_runs_no_word_of_the_hosts_file(tmp_path: Path) -> None:
    interpreter = _stand_in(
        tmp_path / "my node's env $(touch injected)" / "bin" / "python"
    )
    entry = dataclasses.replace(_PYTHON, target=str(interpreter))
    words = _through_a_shell(
        command.remote_command(entry, Compute(host="lab")), tmp_path, os.environ["PATH"]
    )
    assert words == ["-I", "-c", command.LOADER]
    assert not (tmp_path / "injected").exists()


def test_the_loader_runs_what_it_is_sent_and_leaves_the_rest_of_the_input() -> None:
    source = b"import sys; sys.stderr.write(sys.stdin.buffer.read().decode())"
    done = subprocess.run(
        [sys.executable, "-I", "-c", command.LOADER],
        input=b"%d\n" % len(source) + source + b"the frames",
        capture_output=True,
        check=False,
    )
    assert (done.returncode, done.stderr) == (0, b"the frames")


def test_the_loader_runs_the_bootstrap_as_the_image_runs_its_copy(
    tmp_path: Path,
) -> None:
    # The bootstrap answers only when it runs as __main__: a hello of another
    # protocol is refused by name, from the node's standard output.
    source = Path(bootstrap.__file__).read_bytes()
    hello = io.BytesIO()
    bootstrap.write_frame(hello, {"type": "hello", "protocol": bootstrap.PROTOCOL + 1})
    done = subprocess.run(
        [sys.executable, "-I", "-c", command.LOADER],
        input=b"%d\n" % len(source) + source + hello.getvalue(),
        capture_output=True,
        env={**os.environ, bootstrap.CACHE_VAR: str(tmp_path)},
        check=False,
        timeout=120,
    )
    answer = bootstrap.read_header(io.BytesIO(done.stdout))
    assert done.returncode == 2, done.stderr
    assert (answer["type"], answer["stage"]) == ("error", "protocol")


def test_a_docker_node_sees_the_one_gpu_it_is_given_as_index_0() -> None:
    request = Compute(device="cupy", device_index=1, host="nas")
    assert command.node_placement(_DOCKER, request) == {
        "device": "cupy",
        "device_index": 0,
        "dtype": "float64",
    }
    assert (
        command.node_placement(_PYTHON, dataclasses.replace(request, host="lab"))[
            "device_index"
        ]
        == 1
    )


@pytest.mark.parametrize("entry", [_DOCKER, _PYTHON], ids=lambda entry: entry.runner)
@pytest.mark.parametrize(
    ("device", "index", "dtype"),
    [
        ("cpu", 0, "float64"),
        ("torch:cpu", 0, "float32"),
        ("torch:mps", 0, "float32"),
        ("cupy", 1, "float64"),
        ("torch:cuda", 2, "float32"),
    ],
)
def test_a_node_takes_the_placement_it_is_sent(
    entry: HostEntry, device: Device, index: int, dtype: Dtype
) -> None:
    # What the node rebuilds from the job, after the JSON of the frame.
    request = Compute(device=device, device_index=index, dtype=dtype, host=entry.name)
    placement = json.loads(json.dumps(command.node_placement(entry, request)))
    taken = node._placement({"compute": placement})
    on_one_gpu = entry.runner == "docker" and device in ("cupy", "torch:cuda")
    assert taken == Compute(
        device=device, device_index=0 if on_one_gpu else index, dtype=dtype
    )


def test_no_ssh_on_the_path_is_a_missing_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(command, "_SSH_PROGRAM", None)
    monkeypatch.setenv("PATH", str(tmp_path))
    with pytest.raises(FileNotFoundError, match="no ssh client on PATH"):
        command.ssh_program()
