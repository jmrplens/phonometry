#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Build the node image on the node: ``make node-image HOST=<name> [TARGET=cpu]``.

Reads the host's entry from the hosts file with the library's own reader,
packs the build context (the Dockerfile, its provisioning script, the
requirements files and the node bootstrap) into a tar archive in memory,
and pipes it over ssh to ``docker build`` on the node, which tags the image
with the entry's ``image``. Nothing goes to a registry. The archive is the
same bytes for the same files, so a rebuild with nothing changed is all
cache.
"""

from __future__ import annotations

import argparse
import io
import shlex
import subprocess
import sys
import tarfile
from pathlib import Path

from phonometry.simulation._remote import command, hosts

ROOT = Path(__file__).resolve().parent.parent

#: The files the Dockerfile copies, and nothing else.
CONTEXT = (
    "docker/node/Dockerfile",
    "docker/node/provision.sh",
    "requirements.txt",
    "requirements-figures.txt",
    "src/phonometry/simulation/_remote/bootstrap.py",
)


def context_archive(root: Path) -> bytes:
    """The build context as a tar archive: the same bytes for the same files."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for name in CONTEXT:
            data = (root / name).read_bytes()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o755 if name.endswith(".sh") else 0o644
            info.mtime = 0
            archive.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def build_command(entry: hosts.HostEntry, target: str) -> list[str]:
    """The ssh command that runs ``docker build`` of *target* on *entry*."""
    if entry.runner != "docker":
        msg = f"host {entry.name!r} runs Python, not Docker: there is no image to build for it"
        raise SystemExit(msg)
    remote = shlex.join(
        [
            "docker",
            "build",
            "--target",
            target,
            "-t",
            entry.target,
            "-f",
            "docker/node/Dockerfile",
            "-",
        ]
    )
    return [*command.ssh_program(), *command.SSH_OPTIONS, "--", entry.ssh, remote]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build the node image on the node, over ssh."
    )
    parser.add_argument(
        "--host", required=True, help="the node's name in the hosts file"
    )
    parser.add_argument(
        "--target", choices=("gpu", "cpu"), default="gpu", help="the stage to build"
    )
    args = parser.parse_args(argv)
    if not args.host:
        parser.error("name the node: make node-image HOST=<name> [TARGET=cpu]")
    try:
        entry = hosts.load_host(args.host)
        build = build_command(entry, args.target)
    except (KeyError, ValueError, FileNotFoundError) as exc:
        # The message is the argument: a KeyError's str() wraps it in quotes.
        raise SystemExit(exc.args[0]) from None
    print(
        f"building {entry.target} ({args.target}) on {entry.label} through ssh {entry.ssh}",
        flush=True,
    )
    return subprocess.run(build, input=context_archive(ROOT), check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
