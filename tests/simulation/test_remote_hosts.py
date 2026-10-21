#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The hosts file names each node once; a mistake in it names the file."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from phonometry.simulation._remote import hosts

_DOCKER = """
[hosts.nas]
ssh = "root@192.168.0.40"
runner = "docker"
image = "phonometry-node:gpu"
label = "RTX 4060 on the NAS"
timeout_s = 7200
"""

_PYTHON = """
[hosts.lab]
ssh = "lab-alias"
runner = "python"
python = "/opt/conda envs/node/bin/python"
"""


@pytest.fixture
def hosts_at(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A hosts file the variable points at, empty until a test writes it."""
    path = tmp_path / "hosts.toml"
    monkeypatch.setenv(hosts.HOSTS_FILE_VAR, str(path))
    return path


def test_the_variable_points_at_another_file(hosts_at: Path) -> None:
    assert hosts.hosts_file() == hosts_at


def test_on_linux_and_macos_the_file_follows_xdg(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv(hosts.HOSTS_FILE_VAR, raising=False)
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert hosts.hosts_file() == tmp_path / "phonometry" / "hosts.toml"
    monkeypatch.setenv("XDG_CONFIG_HOME", "relative/dir")
    assert hosts.hosts_file() == Path.home() / ".config" / "phonometry" / "hosts.toml"
    monkeypatch.delenv("XDG_CONFIG_HOME")
    assert hosts.hosts_file() == Path.home() / ".config" / "phonometry" / "hosts.toml"


def test_on_windows_the_file_is_under_appdata(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv(hosts.HOSTS_FILE_VAR, raising=False)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert hosts.hosts_file() == tmp_path / "phonometry" / "hosts.toml"


def test_a_docker_node_is_read_whole(hosts_at: Path) -> None:
    hosts_at.write_text(_DOCKER, encoding="utf-8")
    entry = hosts.load_host("nas")
    assert entry == hosts.HostEntry(
        name="nas",
        ssh="root@192.168.0.40",
        runner="docker",
        target="phonometry-node:gpu",
        label="RTX 4060 on the NAS",
        timeout_s=7200.0,
    )


def test_a_python_node_keeps_its_interpreter_path_and_takes_its_name_as_label(
    hosts_at: Path,
) -> None:
    hosts_at.write_text(_PYTHON, encoding="utf-8")
    entry = hosts.load_host("lab")
    assert (entry.runner, entry.target, entry.label, entry.timeout_s) == (
        "python",
        "/opt/conda envs/node/bin/python",
        "lab",
        None,
    )


def test_a_hosts_file_with_a_byte_order_mark_reads_normally(hosts_at: Path) -> None:
    hosts_at.write_bytes(b"\xef\xbb\xbf" + _DOCKER.encode("utf-8"))
    assert hosts.load_host("nas").ssh == "root@192.168.0.40"


def test_an_unknown_node_is_a_missing_key_that_names_the_file(hosts_at: Path) -> None:
    hosts_at.write_text(_DOCKER, encoding="utf-8")
    with pytest.raises(KeyError, match="no host 'gpu2' in .*hosts.toml"):
        hosts.load_host("gpu2")


def test_a_missing_file_is_a_missing_key_that_names_the_file(hosts_at: Path) -> None:
    with pytest.raises(KeyError, match="the hosts file .*hosts.toml does not exist"):
        hosts.load_host("nas")


@pytest.mark.parametrize(
    ("text", "match"),
    [
        ("[hosts.nas\n", "not a TOML file"),
        ("hosts = 3\n", "'hosts' must be a table"),
        ("[hosts]\nnas = 3\n", r"\[hosts.nas\] must be a table"),
        (_DOCKER.replace("image =", "imgae ="), "unknown key"),
        (_DOCKER.replace('ssh = "root@192.168.0.40"\n', ""), "'ssh' is missing"),
        (
            _DOCKER.replace("root@192.168.0.40", "-oProxyCommand=evil"),
            "'ssh' must be a destination",
        ),
        (
            _DOCKER.replace("root@192.168.0.40", "root@host extra"),
            "'ssh' must be a destination",
        ),
        (
            _DOCKER.replace('"docker"', '"podman"'),
            "'runner' must be 'docker' or 'python'",
        ),
        (_DOCKER.replace('image = "phonometry-node:gpu"\n', ""), "'image' is missing"),
        (
            _DOCKER.replace("phonometry-node:gpu", "bad image"),
            "'image' must be a Docker image reference",
        ),
        (
            _DOCKER + 'python = "/usr/bin/python3"\n',
            "'python' belongs to runner = \"python\"",
        ),
        (
            _PYTHON.replace('python = "/opt/conda envs/node/bin/python"\n', ""),
            "'python' is missing",
        ),
        (_PYTHON.replace("/opt/conda", "/opt/con\\nda"), "'python' must be one line"),
        (
            _DOCKER.replace("7200", "0"),
            "'timeout_s' must be a positive number of seconds",
        ),
        (
            _DOCKER.replace("7200", '"7200"'),
            "'timeout_s' must be a positive number of seconds",
        ),
        (
            _DOCKER.replace("7200", "true"),
            "'timeout_s' must be a positive number of seconds",
        ),
        # tomllib reads an integer of any size, past the range of a float.
        (
            _DOCKER.replace("7200", "9" * 400),
            "'timeout_s' must be a positive number of seconds",
        ),
        (
            _DOCKER.replace('label = "RTX 4060 on the NAS"', "label = 4"),
            "'label' must be a non-empty text",
        ),
    ],
)
def test_a_malformed_file_is_a_value_error_that_names_it(
    hosts_at: Path, text: str, match: str
) -> None:
    hosts_at.write_text(text, encoding="utf-8")
    # The entry the case is about: every _DOCKER case holds "label", so the
    # table's own header decides, not a substring of the text.
    name = "lab" if text.lstrip().startswith("[hosts.lab]") else "nas"
    with pytest.raises(ValueError, match=match) as caught:
        hosts.load_host(name)
    assert str(hosts_at) in str(caught.value)


def test_an_image_entry_on_a_python_node_names_where_it_belongs(hosts_at: Path) -> None:
    hosts_at.write_text(_PYTHON + 'image = "phonometry-node:gpu"\n', encoding="utf-8")
    with pytest.raises(ValueError, match="'image' belongs to runner = \"docker\""):
        hosts.load_host("lab")
