#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The hosts file names each node once; a mistake in it names the file."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import pytest
from special_files import SPECIAL_KINDS, make_special, raised_within

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
        pytest.param("[hosts.nas\n", "not a TOML file", id="not TOML"),
        pytest.param("hosts = 3\n", "'hosts' must be a table", id="hosts not a table"),
        pytest.param(
            "[hosts]\nnas = 3\n",
            r"\[hosts.nas\] must be a table",
            id="entry not a table",
        ),
        pytest.param(
            _DOCKER.replace("image =", "imgae ="), "unknown key", id="unknown key"
        ),
        pytest.param(
            _DOCKER.replace('ssh = "root@192.168.0.40"\n', ""),
            "'ssh' is missing",
            id="no ssh",
        ),
        pytest.param(
            _DOCKER.replace("root@192.168.0.40", "-oProxyCommand=evil"),
            "'ssh' must be a destination",
            id="ssh an option",
        ),
        pytest.param(
            _DOCKER.replace("root@192.168.0.40", "root@host extra"),
            "'ssh' must be a destination",
            id="ssh with a space",
        ),
        # A control character, which would reach the ssh command line: a NUL
        # stops ssh from starting with an error that names no file.
        pytest.param(
            _DOCKER.replace("root@192.168.0.40", "root@192.168.0.40\\u0000"),
            "'ssh' must be a destination",
            id="ssh with a NUL",
        ),
        pytest.param(
            _DOCKER.replace("root@192.168.0.40", "root@\\u001b[2Jhost"),
            "'ssh' must be a destination",
            id="ssh with an escape",
        ),
        pytest.param(
            _DOCKER.replace("root@192.168.0.40", "root@\\u009bhost"),
            "'ssh' must be a destination",
            id="ssh with a C1 control",
        ),
        # A mark that reorders text: a message would show one destination and
        # ssh would go to another.
        pytest.param(
            _DOCKER.replace("root@192.168.0.40", "root@\\u202e04.0.861.291"),
            "'ssh' must be a destination",
            id="ssh with a right-to-left override",
        ),
        pytest.param(
            _DOCKER.replace("root@192.168.0.40", "root@192.168.0.40\\u2066"),
            "'ssh' must be a destination",
            id="ssh with an isolate",
        ),
        pytest.param(
            _DOCKER.replace('"docker"', '"podman"'),
            "'runner' must be 'docker' or 'python'",
            id="unknown runner",
        ),
        pytest.param(
            _DOCKER.replace('image = "phonometry-node:gpu"\n', ""),
            "'image' is missing",
            id="no image",
        ),
        pytest.param(
            _DOCKER.replace("phonometry-node:gpu", "bad image"),
            "'image' must be a Docker image reference",
            id="image not a reference",
        ),
        pytest.param(
            _DOCKER + 'python = "/usr/bin/python3"\n',
            "'python' belongs to runner = \"python\"",
            id="python on a docker node",
        ),
        pytest.param(
            _PYTHON.replace('python = "/opt/conda envs/node/bin/python"\n', ""),
            "'python' is missing",
            id="no python",
        ),
        pytest.param(
            _PYTHON.replace("/opt/conda", "/opt/con\\nda"),
            "'python' must be one line",
            id="python of two lines",
        ),
        # The command quotes the path, so the node's shell never expands "~".
        pytest.param(
            _PYTHON.replace("/opt/conda envs", "~/conda envs"),
            "'python' starts with '~'.*absolute or relative to the home directory",
            id="python under a tilde",
        ),
        pytest.param(
            _DOCKER.replace("7200", "0"),
            "'timeout_s' must be a positive number of seconds",
            id="timeout zero",
        ),
        pytest.param(
            _DOCKER.replace("7200", '"7200"'),
            "'timeout_s' must be a positive number of seconds",
            id="timeout a text",
        ),
        pytest.param(
            _DOCKER.replace("7200", "true"),
            "'timeout_s' must be a positive number of seconds",
            id="timeout a bool",
        ),
        # tomllib reads an integer of any size, past the range of a float.
        pytest.param(
            _DOCKER.replace("7200", "9" * 400),
            "'timeout_s' must be a positive number of seconds",
            id="timeout of 400 digits",
        ),
        # The timer that stops a run would die on a longer one.
        pytest.param(
            _DOCKER.replace("7200", "1e300"),
            "'timeout_s' must be at most .* seconds, the longest a timer here waits",
            id="timeout past a timer",
        ),
        # Python refuses to read an integer longer than 4300 digits.
        pytest.param(
            _DOCKER.replace("7200", "9" * 5000),
            "not a TOML file",
            id="timeout of 5000 digits",
        ),
        # A value nested deeper than Python's recursion limit.
        pytest.param(
            _DOCKER + "x = " + "[" * 100_000 + "]" * 100_000 + "\n",
            "not a TOML file",
            id="nested 100000 deep",
        ),
        pytest.param(
            _DOCKER.replace('label = "RTX 4060 on the NAS"', "label = 4"),
            "'label' must be a non-empty text",
            id="label a number",
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


@pytest.mark.parametrize(
    ("kind", "error", "match"),
    [
        (
            "a directory",
            ValueError,
            "the hosts file is a directory, and it is read only from a regular file",
        ),
        # A path whose middle component is a file names no file there, on
        # every system: the KeyError of no hosts file at all.
        ("under a file", KeyError, "does not exist"),
    ],
)
def test_a_hosts_file_that_cannot_be_read_is_refused_naming_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
    error: type[Exception],
    match: str,
) -> None:
    if kind == "a directory":
        path = tmp_path / "hosts.toml"
        path.mkdir()
    else:
        (tmp_path / "not-a-directory").write_text("", encoding="utf-8")
        path = tmp_path / "not-a-directory" / "hosts.toml"
    monkeypatch.setenv(hosts.HOSTS_FILE_VAR, str(path))
    with pytest.raises(error, match=match) as caught:
        hosts.load_host("nas")
    # The message itself: a KeyError's text is the repr of its message,
    # which doubles every backslash of a Windows path.
    assert str(path) in caught.value.args[0]


def test_an_image_entry_on_a_python_node_names_where_it_belongs(hosts_at: Path) -> None:
    hosts_at.write_text(_PYTHON + 'image = "phonometry-node:gpu"\n', encoding="utf-8")
    with pytest.raises(ValueError, match="'image' belongs to runner = \"docker\""):
        hosts.load_host("lab")


@pytest.mark.parametrize("kind", SPECIAL_KINDS)
def test_a_hosts_file_that_is_no_regular_file_is_refused_before_it_is_opened(
    hosts_at: Path, kind: str
) -> None:
    """A pipe at the name kept the read waiting for a writer, a device without end."""
    what = make_special(kind, hosts_at)
    error = raised_within(
        lambda: hosts.load_host("nas"), pipe=hosts_at if kind == "pipe" else None
    )
    assert isinstance(error, ValueError)
    assert str(error) == (
        f"{hosts_at}: the hosts file is {what}, and it is read only from a regular file"
    )


def test_a_hosts_file_past_one_mebibyte_is_refused_before_it_is_read(
    hosts_at: Path,
) -> None:
    hosts_at.write_text(_DOCKER, encoding="utf-8")
    with hosts_at.open("r+b") as handle:
        # A sparse file: the size is refused before a byte of it is read.
        handle.truncate(1024 * 1024 + 1)
    refusal = (
        f"{hosts_at}: the hosts file is 1048577 bytes, and a hosts file is at most "
        "1048576 bytes (1 MiB)"
    )
    with pytest.raises(ValueError, match=f"^{re.escape(refusal)}$"):
        hosts.load_host("nas")


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="a Windows file name is UTF-16, so no name fails UTF-8",
)
def test_a_hosts_file_name_that_is_not_utf8_is_named_by_its_escapes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The name went into the message as Python holds it, a lone surrogate no UTF-8 stream writes."""
    path = tmp_path / os.fsdecode(b"h\xffosts.toml")
    try:
        path.mkdir()
    except (OSError, UnicodeEncodeError):
        pytest.skip("this file system takes only names that are text")
    monkeypatch.setenv(hosts.HOSTS_FILE_VAR, str(path))
    with pytest.raises(ValueError, match="the hosts file is a directory") as caught:
        hosts.load_host("nas")
    message = str(caught.value)
    message.encode("utf-8")
    assert message == (
        f"{tmp_path}{os.sep}h\\udcffosts.toml: the hosts file is a directory, and it "
        "is read only from a regular file"
    )
    path.rmdir()
    path.write_text("[hosts", encoding="utf-8")
    with pytest.raises(
        ValueError, match=r"h\\udcffosts\.toml: not a TOML file"
    ) as caught:
        hosts.load_host("nas")
    str(caught.value).encode("utf-8")
