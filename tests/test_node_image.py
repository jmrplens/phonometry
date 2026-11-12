#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The node image: its two stages, its pins, and the bootstrap where the client runs it."""

from __future__ import annotations

import base64
import hashlib
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
_PROVISION = (_ROOT / "docker" / "node" / "provision.sh").read_text(encoding="utf-8")
#: The PPA's signing key as the repository keeps it, and where each stage
#: copies it, beside the provisioning script.
_KEY_FILE = _ROOT / "docker" / "node" / "deadsnakes.asc"
_COPIED_KEY = "/tmp/node/deadsnakes.asc"
#: The keyring the PPA's source names in its Signed-By.
_KEYRING = "/etc/apt/keyrings/deadsnakes.asc"
#: The fingerprint of the deadsnakes PPA's signing key, as the PPA's page on
#: Launchpad gives it (https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa).
_DEADSNAKES = "F23C5A6CF475977595C89F51BA6932366A755776"
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
    assert "sha256sum -c" in _PROVISION
    for packages in re.findall(
        r"apt-get install -y --no-install-recommends((?:\\\n|[^\n])*)", _PROVISION
    ):
        assert "ffmpeg" not in packages.split()


def _split(line: str) -> list[str]:
    """One line of shell, cut into its simple commands.

    The line is cut at ``;``, ``&``, ``&&``, ``|`` and ``||`` outside quotes
    and parentheses, so that a subshell or a substitution stays whole in the
    command that holds it, and a ``#`` that starts a word ends the line.
    """
    parts = []
    start = depth = at = 0
    quote = ""
    while at < len(line):
        char = line[at]
        if quote == "'":
            quote = "" if char == "'" else quote
        elif char == "\\":
            at += 1
        elif quote == '"':
            quote = "" if char == '"' else quote
        elif char in "'\"":
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth = max(depth - 1, 0)
        elif depth == 0 and char == "#" and (at == 0 or line[at - 1] in " \t;&|"):
            break
        elif depth == 0 and char in ";&|" and not _redirects(line, at):
            parts.append(line[start:at])
            # The second character of &&, || and ;;, and the & of |&.
            at += 2 if line[at + 1 : at + 2] in (";", "&", "|") else 1
            start = at
            continue
        at += 1
    parts.append(line[start:at])
    return [part.strip() for part in parts if part.strip()]


def _redirects(line: str, at: int) -> bool:
    """Whether the ``&`` or ``|`` at *at* belongs to a redirection (2>&1, &>, >|)."""
    return line[at - 1 : at] in ("<", ">") or line[at : at + 2] == "&>"


def _commands(text: str) -> list[str]:
    """The simple commands of a shell script or a Dockerfile, in order.

    Comments are dropped, a line continued with a backslash is joined to the
    next, and each line is cut into its simple commands.
    """
    joined = text.replace("\\\n", " ")
    return [command for line in joined.splitlines() for command in _split(line)]


#: What opens a compound command or negates one, before the program it runs.
_LEADING = frozenset({"if", "then", "else", "elif", "while", "until", "do", "!", "{"})


def _run_words(simple_command: str) -> list[str]:
    """The words of *simple_command* from the program it runs on.

    A Dockerfile's RUN and its flags go, and so do the shell's keywords and
    the assignments before the program.
    """
    words = shlex.split(simple_command)
    at = 0
    if words[:1] == ["RUN"]:
        at = 1
        while at < len(words) and words[at].startswith("--"):
            at += 1
    while at < len(words) and (
        words[at] in _LEADING or re.fullmatch(r"\w+=.*", words[at])
    ):
        at += 1
    return words[at:]


#: The programs a build could download a file with.
_DOWNLOADERS = frozenset({"curl", "wget"})
#: curl or wget as a word of its own, wherever a command holds it: its
#: program, by name or by path, or one it runs (timeout, xargs, sh -c, a
#: substitution).
_DOWNLOADER = re.compile(r"(?<![\w.-])(?:curl|wget)(?![\w.-])")
#: The programs whose words name packages, curl and wget among them.
_PACKAGE_MANAGERS = frozenset({"apt", "apt-get"})


def _downloads(text: str) -> list[str]:
    """Each curl or wget of *text*, wherever it sits, in order.

    A curl or a wget that apt installs or removes is a package, not a
    download. A download that is its command's program is given by its last
    word, what it fetches, and any other by its whole command.
    """
    found = []
    for part in _commands(text):
        words = _run_words(part)
        program = Path(words[0]).name if words else ""
        packages = (
            sum(word in _DOWNLOADERS for word in words[1:])
            if program in _PACKAGE_MANAGERS
            else 0
        )
        named = len(_DOWNLOADER.findall(part)) - packages
        found += [words[-1] if program in _DOWNLOADERS else part] * named
    return found


#: What reaches a keyserver, a key's web directory or Launchpad for a key,
#: whatever runs it: gpg's options by their full names, its settings that
#: fetch a key while it checks a signature, its network daemon, and the tools
#: that add a PPA or its key.
_KEY_FETCH = re.compile(
    r"keyserver|hkps?://|dirmngr|gpg-wks-client"
    r"|--(?:recv|receive|fetch|search|refresh|send|locate(?:-external)?)-keys?\b"
    r"|(?<!no-)auto-key-(?:locate|retrieve)"
    r"|add-apt-repository|apt-key|\blaunchpad\.net"
)
#: gpg's options that reach a keyserver or a key's web directory
#: (gpg --dump-options, GnuPG 2.4.7). gpg takes any unambiguous abbreviation
#: of a long option, --recv for --recv-keys among them.
_GPG_NETWORK_OPTIONS = (
    "receive-keys",
    "recv-keys",
    "search-keys",
    "refresh-keys",
    "locate-keys",
    "locate-external-keys",
    "fetch-keys",
    "send-keys",
    "auto-key-locate",
    "auto-key-retrieve",
    "keyserver",
    "keyserver-options",
)
_GPG = re.compile(r"(?<![\w.-])gpg2?(?![\w.-])")
_LONG_OPTION = re.compile(r"(?<![^\s'\"])--([a-z][a-z-]*)")


def _gpg_reaches_the_network(simple_command: str) -> bool:
    """Whether a gpg of *simple_command* takes a network option, in full or abbreviated."""
    gpg = _GPG.search(simple_command)
    return gpg is not None and any(
        option.startswith(given)
        for given in _LONG_OPTION.findall(simple_command[gpg.end() :])
        for option in _GPG_NETWORK_OPTIONS
    )


def _key_fetches(text: str) -> list[str]:
    """Each command of *text* that would fetch a key over the network."""
    return [
        part
        for part in _commands(text)
        if _KEY_FETCH.search(part) or _gpg_reaches_the_network(part)
    ]


def test_the_build_downloads_ffmpeg_alone_and_fetches_no_key() -> None:
    """The PPA's key is a file of the repository: no build waits on a keyserver for it."""
    assert _downloads(_PROVISION) == ["$FFMPEG_URL"]
    assert _downloads(_TEXT) == []
    assert _key_fetches(_PROVISION) == []
    assert _key_fetches(_TEXT) == []
    assert not re.search(r"^ADD\s", _TEXT, flags=re.MULTILINE)


def test_the_ffmpeg_download_retries_any_failure_and_bounds_each_connection() -> None:
    """Five tries more after any failure, curl's doubling waits between them, 30 s per connection.

    provision.sh's header states what these give: a host that does not
    answer stops the build in about three and a half minutes.
    """
    (download,) = [
        words
        for words in map(_run_words, _commands(_PROVISION))
        if words[:1] == ["curl"]
    ]
    value = dict(zip(download, download[1:], strict=False))
    assert value["--retry"] == "5"
    assert "--retry-all-errors" in download
    assert value["--connect-timeout"] == "30"
    # --retry-delay would replace the doubling waits, and --retry-max-time
    # could cut the tries short.
    assert not {"--retry-delay", "--retry-max-time"} & set(download)


#: The provisioning script's download of the key before the repository kept
#: it, and the other ways a build could fetch one: each of gpg's options that
#: reaches a keyserver or a key's web directory, by its name and abbreviated
#: (gpg takes any unambiguous abbreviation of a long option), wherever the
#: command sits.
_KEY_DOWNLOADS = {
    "curl": (
        "curl -fsSL --proto '=https' --retry 3 -o /etc/apt/keyrings/deadsnakes.asc \\\n"
        '    "https://keyserver.ubuntu.com/pks/lookup?op=get&options=mr&search=0x$key"\n'
    ),
    "gpg": 'gpg --keyserver hkps://keyserver.ubuntu.com --recv-keys "$key"\n',
    "add-apt-repository": "RUN apt-get update && add-apt-repository -y ppa:deadsnakes/ppa\n",
    "receive-keys": 'gpg --batch --receive-keys "$key"\n',
    "search-keys": 'gpg --search-keys "$key"\n',
    "refresh-keys": "gpg --refresh-keys\n",
    "locate-external-keys": "gpg --locate-external-keys ppa@deadsnakes.example\n",
    "locate-keys": "gpg --locate-keys ppa@deadsnakes.example\n",
    "fetch-keys": 'gpg --fetch-keys "https://example.org/deadsnakes.asc"\n',
    "send-keys": 'gpg --send-keys "$key"\n',
    "recv abbreviated": 'gpg --batch --recv "$key"\n',
    "refresh abbreviated": "gpg --refresh\n",
    "locate-ext abbreviated": "gpg --locate-ext ppa@deadsnakes.example\n",
    "fetch abbreviated": 'gpg --fetch "https://example.org/deadsnakes.asc"\n',
    "auto-key-retrieve": "gpg --auto-key-retrieve --verify InRelease.gpg InRelease\n",
    "gpg.conf": "echo auto-key-retrieve >> /root/.gnupg/gpg.conf\n",
    "dirmngr": "gpg-connect-agent --dirmngr 'KS_GET -- 0x$key' /bye\n",
    "apt-key": 'apt-key adv --recv-keys "$key"\n',
    "after a semicolon": 'cd /tmp; gpg --recv-keys "$key"\n',
    "inside an if": 'if ! gpg --receive-keys "$key"; then exit 1; fi\n',
    "in a shell's script": "sh -c 'gpg --batch --recv \"$key\"'\n",
}


@pytest.mark.parametrize("text", _KEY_DOWNLOADS.values(), ids=_KEY_DOWNLOADS.keys())
def test_a_key_the_build_would_fetch_is_seen(text: str) -> None:
    assert len(_key_fetches(text)) == 1


#: A curl or a wget wherever a shell runs it: after an operator, in an if, at
#: either end of a pipe, behind another program, in a substitution, in a
#: subshell, in a shell's script, by its path and in a Dockerfile's exec form.
_SECOND_DOWNLOADS = {
    "after a semicolon": (
        "cd /tmp; curl -fsSL -o /etc/apt/keyrings/deadsnakes.asc"
        ' "https://keys.openpgp.org/vks/v1/by-fingerprint/$key"\n'
    ),
    "inside an if": 'if ! curl -fsSL -o k "https://example.org/k"; then exit 1; fi\n',
    "after ||": "true || wget -qO k https://example.org/k\n",
    "background": "curl -fsSLO https://example.org/k &\n",
    "into a pipe": "curl -fsSL https://example.org/k | gpg --dearmor > k.gpg\n",
    "out of a pipe": "echo https://example.org/k | xargs curl -fsSLO\n",
    "behind another program": "timeout 60 wget -q https://example.org/k\n",
    "by its path": "/usr/bin/curl -fsSLO https://example.org/k\n",
    "in a substitution": 'key="$(curl -fsSL https://example.org/k)"\n',
    "in backquotes": "key=`wget -qO- https://example.org/k`\n",
    "in a subshell": "(cd /tmp && curl -fsSLO https://example.org/k)\n",
    "in a shell's script": "sh -c 'curl -fsSLO https://example.org/k'\n",
    "beside apt's packages": (
        "apt-get install -y curl $(curl -fsSL https://example.org/packages)\n"
    ),
    "exec form": 'RUN ["curl", "-fsSLO", "https://example.org/k"]\n',
}


@pytest.mark.parametrize(
    "text", _SECOND_DOWNLOADS.values(), ids=_SECOND_DOWNLOADS.keys()
)
def test_a_download_is_seen_wherever_it_sits(text: str) -> None:
    assert len(_downloads(text)) == 1


@pytest.mark.parametrize(
    "text",
    [
        "apt-get install -y --no-install-recommends ca-certificates curl gnupg\n",
        "apt-get purge -y curl wget\n",
        "make clean # curl https://example.org/k\n",
    ],
    ids=["apt installs it", "apt removes it", "a comment"],
)
def test_a_package_or_a_comment_is_no_download(text: str) -> None:
    assert _downloads(text) == []


def test_a_download_of_the_key_is_a_second_download() -> None:
    assert _downloads(_KEY_DOWNLOADS["curl"]) == [
        "https://keyserver.ubuntu.com/pks/lookup?op=get&options=mr&search=0x$key"
    ]


def test_each_stage_copies_the_ppa_key_beside_the_provisioning_script() -> None:
    copies = [
        line.split()[1:]
        for line in _TEXT.splitlines()
        if line.startswith("COPY ") and "docker/node/provision.sh" in line.split()
    ]
    assert len(copies) == len(_STAGES)
    for words in copies:
        assert "docker/node/deadsnakes.asc" in words[:-1]
        assert words[-1] + _KEY_FILE.name == _COPIED_KEY


def test_the_build_stops_unless_the_copied_key_is_the_pinned_one() -> None:
    """gpg reads the copy, and only a file holding the one pinned key reaches apt."""
    assert re.findall(r"^key=(\S+)$", _PROVISION, flags=re.MULTILINE) == [_DEADSNAKES]
    commands = _commands(_PROVISION)
    check = [
        f"gpg --show-keys --with-colons {_COPIED_KEY} > /tmp/deadsnakes.keys",
        "test \"$(grep -c '^pub:' /tmp/deadsnakes.keys)\" = 1",
        'test "$(grep \'^fpr:\' /tmp/deadsnakes.keys)" = "fpr:::::::::$key:"',
        "rm -rf /tmp/deadsnakes.keys /root/.gnupg",
        f"install -D -m 0644 {_COPIED_KEY} {_KEYRING}",
    ]
    assert check[0] in commands
    start = commands.index(check[0])
    assert commands[start : start + len(check)] == check
    # Nothing writes the keyring before the check, and apt reads the PPA after it.
    assert not [command for command in commands[:start] if _KEYRING in command]
    after = commands[start + len(check) :]
    assert "apt-get update" in after
    assert [command for command in after if f'"Signed-By: {_KEYRING}"' in command]


def _crc24(data: bytes) -> int:
    """The CRC-24 an armored OpenPGP block ends with (RFC 4880, 6.1)."""
    crc = 0xB704CE
    for byte in data:
        crc ^= byte << 16
        for _ in range(8):
            crc <<= 1
            if crc & 0x1000000:
                crc ^= 0x1864CFB
    return crc & 0xFFFFFF


def _dearmored(text: str) -> bytes:
    """The packets of a file that is one armored public key block, its checksum checked.

    RFC 4880, 6.2: a second block, or anything around the one, is refused.
    """
    begin, end = (
        "-----BEGIN PGP PUBLIC KEY BLOCK-----",
        "-----END PGP PUBLIC KEY BLOCK-----",
    )
    lines = text.splitlines()
    assert lines[:1] == [begin]
    assert lines[-1:] == [end]
    assert lines.count(begin) == lines.count(end) == 1
    body = lines[1:-1]
    # The armor's headers, if any, end at its first blank line.
    *data_lines, checksum = body[body.index("") + 1 :]
    data = base64.b64decode("".join(data_lines), validate=True)
    assert checksum == "=" + base64.b64encode(_crc24(data).to_bytes(3, "big")).decode()
    return data


def _packets(data: bytes) -> list[tuple[int, bytes]]:
    """The tag and the body of each OpenPGP packet in *data* (RFC 4880, 4.2)."""
    packets = []
    at = 0
    while at < len(data):
        header = data[at]
        assert header & 0x80, f"no packet header at byte {at}"
        if header & 0x40:
            # The new format: the tag, then a one, two or five octet length.
            tag, first = header & 0x3F, data[at + 1]
            if first < 192:
                length, at = first, at + 2
            elif first < 224:
                length, at = ((first - 192) << 8) + data[at + 2] + 192, at + 3
            else:
                assert first == 255, "a partial body length"
                length, at = int.from_bytes(data[at + 2 : at + 6], "big"), at + 6
        else:
            # The old format: the tag and a length of one, two or four octets.
            tag, kind = (header >> 2) & 0x0F, header & 0x03
            assert kind != 3, "an indeterminate length"
            octets = 1 << kind
            length = int.from_bytes(data[at + 1 : at + 1 + octets], "big")
            at += 1 + octets
        packets.append((tag, data[at : at + length]))
        at += length
    return packets


#: The packet tags of a public key, a user ID and a public subkey (RFC 4880, 4.3).
_PUBLIC_KEY, _USER_ID, _PUBLIC_SUBKEY = 6, 13, 14


def test_the_key_in_the_repository_is_the_ppa_s_one_key() -> None:
    """The file holds one primary key, with no subkey, whose fingerprint is the PPA's."""
    packets = _packets(_dearmored(_KEY_FILE.read_text(encoding="utf-8")))
    keys = [body for tag, body in packets if tag == _PUBLIC_KEY]
    assert len(keys) == 1
    assert not [tag for tag, _ in packets if tag == _PUBLIC_SUBKEY]
    (key,) = keys
    # A version 4 key, named by the SHA-1 of its framed packet (RFC 4880,
    # 12.2): the name the PPA's page prints, compared, not a digest relied on.
    assert key[0] == 4
    framed = b"\x99" + len(key).to_bytes(2, "big") + key
    fingerprint = hashlib.sha1(framed, usedforsecurity=False).hexdigest().upper()
    assert fingerprint == _DEADSNAKES
    assert [body for tag, body in packets if tag == _USER_ID] == [
        b"Launchpad PPA for deadsnakes"
    ]


#: A key named the ways a file could name it: its fingerprint whole or in
#: gpg's groups of four, or its long key ID, the fingerprint's last 16 digits.
_KEY_NAME = re.compile(
    r"(?<![0-9A-Fa-f])"
    r"(?:(?:[0-9A-Fa-f]{4} {1,2}){9}[0-9A-Fa-f]{4}|[0-9A-Fa-f]{40}|[0-9A-Fa-f]{16})"
    r"(?![0-9A-Fa-f])"
)


def _key_names(text: str) -> list[str]:
    """Each fingerprint or long key ID *text* names, with gpg's spaces taken out."""
    return [name.replace(" ", "") for name in _KEY_NAME.findall(text)]


@pytest.mark.parametrize(
    ("text", "names"),
    [
        (f"# fingerprint {_DEADSNAKES}, kept here\n", [_DEADSNAKES]),
        (
            "#   F23C 5A6C F475 9775 95C8  9F51 BA69 3236 6A75 5776\n",
            [_DEADSNAKES],
        ),
        (f"# {_DEADSNAKES.lower()}\n", [_DEADSNAKES.lower()]),
        ("gpg --export 0xBA6932366A755776\n", ["BA6932366A755776"]),
        (f"ARG FFMPEG_SHA256={'73e29a56' * 8}\n", []),
    ],
    ids=["whole", "gpg's groups", "lower case", "long key ID", "a SHA-256"],
)
def test_a_key_is_seen_however_a_file_names_it(text: str, names: list[str]) -> None:
    assert _key_names(text) == names


def test_every_key_the_node_files_name_is_the_ppa_s() -> None:
    """A new PPA key moves every place that names the old one, comments included."""
    for text in (_TEXT, _PROVISION):
        assert _key_names(text)
        assert set(_key_names(text)) <= {_DEADSNAKES, _DEADSNAKES[-16:]}


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
    """A CRLF checkout would break the provisioning script, the image's copy of the Dockerfile and the key."""
    attributes = (_ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
    assert {
        "*.sh text eol=lf",
        "docker/node/Dockerfile text eol=lf",
        "docker/node/deadsnakes.asc text eol=lf",
    } <= set(attributes)
    for name in (
        "docker/node/Dockerfile",
        "docker/node/provision.sh",
        "docker/node/deadsnakes.asc",
    ):
        assert b"\r" not in (_ROOT / name).read_bytes(), name
