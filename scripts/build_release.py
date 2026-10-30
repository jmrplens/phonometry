#!/usr/bin/env python3
#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Build the sdist and the wheel of the checked-out commit so that every build gives the same bytes.

The release workflow builds the files it publishes with this script and then
builds them again and refuses the release if the second build differs; after
publishing, a job on macOS clones the tag, runs it again and compares what it
gets with the files on PyPI; and SECURITY.md ("Rebuilding a release") gives
anyone the same commands. Everything that could make two builds of one commit
differ is settled here rather than left to the machine:

- the build back end is the setuptools that ``requirements-release.txt`` pins,
  used where it is installed (``--no-isolation``) instead of whatever release
  is newest on the day, and a setuptools plugin of another distribution that
  could change what is packed (a file finder, as setuptools-scm installs, or a
  hook that finalises the distribution's options) stops the build;
- every timestamp is the commit's (``SOURCE_DATE_EPOCH``), which setuptools
  writes into the wheel;
- the sdist, which setuptools stamps with the time of the build, the builder's
  user and group and whatever modes the checkout left, is written again with
  the commit's time, no owner, mode 644 for a file and 755 for a directory or
  an executable, its members in name order, and a gzip header that carries the
  commit's time and no file name;
- the wheel is built from that sdist, as pip builds one for anyone who
  installs from source, so a wheel that only builds from the checkout fails
  here and not on someone else's machine;
- the build runs under umask 022: setuptools writes each module into the
  wheel afresh rather than copying its mode, so under a umask of 002 the same
  commit gave a wheel whose modules were group-writable.

A release rebuilds on Linux and macOS, and on Windows only inside WSL, from a
clone made in WSL's own filesystem rather than under ``/mnt/c``, where the
files carry no Unix modes of their own and every one of them looks
executable. Among those platforms, what is left to the machine is the zlib
that Python is linked against, which writes the compressed bytes of both
files; the rebuild on macOS is there to show that it does not matter. On
Windows itself the operating system reaches the bytes whatever is settled
here: zipfile records the system that wrote each member of the wheel,
setuptools gives the wheel's modules the mode Windows reports, and it writes
the sdist's ``PKG-INFO`` and ``setup.cfg`` in text mode, with CRLF. The script
refuses to run there.

The checkout has to be the commit and nothing else: a modified or untracked
file would be packed into the build. ``--check`` then compares what was built
with a checksum file in the format ``sha256sum`` writes, the one the GitHub
Release carries, and ``--check-pypi`` with the digests PyPI publishes for the
version.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import pathlib
import subprocess  # nosec B404 - git and the build front end, with fixed arguments
import sys
import tarfile
import time
import urllib.parse
import urllib.request
from importlib import metadata
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_PACKAGE = "phonometry"
#: The entry-point groups through which another distribution can change what
#: setuptools packs or how it names it: a file finder adds every file it finds
#: to the sdist, a finalising hook can rewrite the version or the package list,
#: a command or an ``egg-info`` writer replaces one of setuptools' own. A
#: ``distutils.setup_keywords`` entry acts only on a ``setup()`` keyword this
#: project does not pass, so cffi's, which the release tooling brings, is left
#: alone.
PLUGIN_GROUPS = frozenset(
    {
        "setuptools.file_finders",
        "setuptools.finalize_distribution_options",
        "distutils.commands",
        "egg_info.writers",
    }
)
#: Where PyPI publishes the files of one version and their digests.
PYPI_JSON = "https://pypi.org/pypi/{package}/{version}/json"
#: How often, and how far apart, PyPI is asked for a version it has just
#: received, before the rebuild gives up: its JSON can lag the upload by a
#: few minutes, and ten tries thirty seconds apart cover that with room.
PYPI_ATTEMPTS = 10
PYPI_WAIT_S = 30.0
#: Mode bits of every member of the normalised sdist.
FILE_MODE = 0o644
EXECUTABLE_MODE = 0o755
#: The umask both builds run under, whatever the builder's own.
BUILD_UMASK = 0o022
#: How long a git query may take [s], and a build step [s]: a few seconds and
#: under a minute here, so either bound is only there to end a hang.
GIT_S = 60.0
BUILD_S = 900.0
#: How long one request to PyPI may take [s].
FETCH_S = 30.0
#: Why the script does not build on Windows, and where to build instead.
WINDOWS_REFUSAL = (
    "a release rebuilds on Linux and macOS, not on Windows, where zipfile, the "
    "modes setuptools gives the wheel's modules and the line endings of the "
    "PKG-INFO and setup.cfg it writes depend on the operating system; on "
    "Windows, rebuild inside WSL from a clone made in WSL's own filesystem, "
    "not under /mnt/c"
)


def built_names(version: str) -> tuple[str, str]:
    """The file names of the sdist and the wheel of *version*.

    :param version: The version in its PEP 440 normal form, as ``VERSION``
        holds it.
    :return: The sdist's name and the wheel's.
    """
    return f"{_PACKAGE}-{version}.tar.gz", f"{_PACKAGE}-{version}-py3-none-any.whl"


def commit_time(root: pathlib.Path = _ROOT) -> int:
    """The committer time of the checked-out commit, in seconds since the epoch.

    :param root: The repository checkout.
    :return: The value ``SOURCE_DATE_EPOCH`` takes for the build.
    """
    out = subprocess.run(  # nosec B603 B607 - fixed git invocation
        ["git", "-C", str(root), "log", "-1", "--format=%ct"],
        check=True,
        capture_output=True,
        text=True,
        timeout=GIT_S,
    ).stdout
    return int(out.strip())


def checkout_changes(root: pathlib.Path = _ROOT) -> list[str]:
    """Every way the checkout differs from its commit, one ``git status`` line each.

    Files git ignores are left out: the build's own output and leftovers
    (``build/``, ``dist/``, ``*.egg-info``) are among them, and setuptools
    packs none of them.

    :param root: The repository checkout.
    :return: The modified, added, deleted and untracked paths; empty when the
        checkout is the commit.
    """
    out = subprocess.run(  # nosec B603 B607 - fixed git invocation
        ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"],
        check=True,
        capture_output=True,
        text=True,
        timeout=GIT_S,
    ).stdout
    return [line for line in out.splitlines() if line.strip()]


def foreign_plugins(
    distributions: Iterable[metadata.Distribution] | None = None,
) -> list[str]:
    """The setuptools plugins installed by a distribution other than setuptools.

    :param distributions: The installed distributions; every one on the path
        when ``None``.
    :return: One sentence per plugin found in :data:`PLUGIN_GROUPS`; empty when
        setuptools is alone in deciding what is packed.
    """
    found = []
    for dist in metadata.distributions() if distributions is None else distributions:
        name = dist.metadata["Name"] or "an unnamed distribution"
        if name.lower() == "setuptools":
            continue
        found += [
            f"{name} installs the setuptools plugin {entry.name!r} "
            f"({entry.group}), which can change what the build packs"
            for entry in dist.entry_points
            if entry.group in PLUGIN_GROUPS
        ]
    return sorted(found)


def _normalised_member(member: tarfile.TarInfo, epoch: int) -> tarfile.TarInfo:
    """A copy of *member* that keeps its name, its kind and its size, and nothing else.

    A file is written as the regular-file type of the tar format, whichever of
    the three spellings of a file the builder's tar used.
    """
    if not (member.isfile() or member.isdir()):
        msg = f"the sdist holds {member.name}, which is neither a file nor a directory"
        raise ValueError(msg)
    info = tarfile.TarInfo(member.name)
    info.type = tarfile.DIRTYPE if member.isdir() else tarfile.REGTYPE
    info.size = member.size if member.isfile() else 0
    info.mtime = epoch
    executable = member.isdir() or bool(member.mode & 0o100)
    info.mode = EXECUTABLE_MODE if executable else FILE_MODE
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    return info


def normalise_sdist(path: pathlib.Path, epoch: int) -> None:
    """Write the sdist at *path* again so that its bytes depend on its contents alone.

    The members keep their names, types and contents; their order becomes the
    order of their names, every time stamp becomes *epoch*, the owner becomes
    user and group 0 with no names, and the mode becomes 644, or 755 for a
    directory or a file its owner can execute. The tar is written in the pax
    format setuptools writes, and gzipped at level 9 under a header that
    carries *epoch* and no file name.

    :param path: The ``.tar.gz`` setuptools wrote; it is replaced.
    :param epoch: The commit's time, in seconds since the epoch.
    :raises ValueError: When the sdist holds a member that is neither a file
        nor a directory, which has no normal form here.
    """
    tar = io.BytesIO()
    with (
        tarfile.open(path, "r:gz") as source,
        tarfile.open(fileobj=tar, mode="w", format=tarfile.PAX_FORMAT) as target,
    ):
        for member in sorted(source.getmembers(), key=lambda m: m.name):
            info = _normalised_member(member, epoch)
            data = source.extractfile(member) if member.isfile() else None
            target.addfile(info, data)
    with (
        path.open("wb") as raw,
        gzip.GzipFile(
            filename="", mode="wb", fileobj=raw, compresslevel=9, mtime=epoch
        ) as compressed,
    ):
        compressed.write(tar.getvalue())


def _build_command(*arguments: str) -> list[str]:
    return [sys.executable, "-m", "build", "--no-isolation", *arguments]


def build(
    outdir: pathlib.Path,
    *,
    version: str,
    epoch: int,
    root: pathlib.Path = _ROOT,
    run: Callable[..., object] = subprocess.run,
) -> list[pathlib.Path]:
    """Build the sdist, normalise it and build the wheel from it, into *outdir*.

    :param outdir: Where the two files go; it must be empty or absent.
    :param version: The version being built, which names the files.
    :param epoch: The commit's time, which stamps both files.
    :param root: The repository checkout.
    :param run: Runs a command; :func:`subprocess.run` by default.
    :return: The sdist and the wheel.
    :raises ValueError: When *outdir* already holds a file, or the build left
        anything but the two files of *version* there.
    """
    if outdir.exists() and any(outdir.iterdir()):
        msg = f"{outdir} already holds files; build into an empty directory"
        raise ValueError(msg)
    environment = {**os.environ, "SOURCE_DATE_EPOCH": str(epoch)}
    sdist_name, wheel_name = built_names(version)
    sdist = outdir / sdist_name
    umask = os.umask(BUILD_UMASK)
    try:
        run(
            _build_command("--sdist", "--outdir", str(outdir), str(root)),
            check=True,
            env=environment,
            timeout=BUILD_S,
        )
        if sdist.is_file():
            normalise_sdist(sdist, epoch)
        run(
            _build_command("--wheel", "--outdir", str(outdir), str(sdist)),
            check=True,
            env=environment,
            timeout=BUILD_S,
        )
    finally:
        os.umask(umask)
    found = sorted(path.name for path in outdir.iterdir()) if outdir.is_dir() else []
    if found != sorted([sdist_name, wheel_name]):
        msg = f"the build left {found} in {outdir}, not {sdist_name} and {wheel_name}"
        raise ValueError(msg)
    return [sdist, outdir / wheel_name]


def digests(paths: Iterable[pathlib.Path]) -> dict[str, str]:
    """The SHA-256 of each file, in hexadecimal, by file name.

    :param paths: The files.
    :return: ``{name: digest}``.
    """
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def read_checksums(text: str) -> dict[str, str]:
    """The digests a checksum file lists, by file name.

    :param text: Lines as ``sha256sum`` writes them: the digest, a space, a
        space or an asterisk, and the name.
    :return: ``{name: digest}``.
    :raises ValueError: On a line that is not a SHA-256 digest and a name.
    """
    listed = {}
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        digest, _, name = line.partition(" ")
        name = name.removeprefix(" ").removeprefix("*")
        if len(digest) != 64 or not name or digest.strip("0123456789abcdef"):
            msg = f"line {number} of the checksum file is not a SHA-256 digest and a file name: {line!r}"
            raise ValueError(msg)
        listed[name] = digest
    return listed


def _fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=FETCH_S) as response:  # nosec B310 - a fixed https URL
        body: bytes = response.read()
    return body


def pypi_digests(
    version: str,
    *,
    fetch: Callable[[str], bytes] = _fetch,
    sleep: Callable[[float], object] = time.sleep,
    attempts: int = PYPI_ATTEMPTS,
    wait_s: float = PYPI_WAIT_S,
) -> dict[str, str]:
    """The SHA-256 PyPI publishes for each file of *version*, by file name.

    PyPI's JSON can lag an upload, so a version it does not know yet, or one
    whose sdist or wheel it does not list yet, is asked for again.

    :param version: The version.
    :param fetch: Reads a URL; :mod:`urllib` by default.
    :param sleep: Waits between attempts; :func:`time.sleep` by default.
    :param attempts: How many times PyPI is asked.
    :param wait_s: How long to wait between two attempts, in seconds.
    :return: ``{name: digest}`` for every file PyPI lists.
    :raises RuntimeError: When PyPI has not listed both files after the last
        attempt.
    """
    url = PYPI_JSON.format(package=_PACKAGE, version=urllib.parse.quote(version))
    wanted = set(built_names(version))
    last = "nothing was asked"
    for attempt in range(1, attempts + 1):
        try:
            files = json.loads(fetch(url))["urls"]
            listed = {entry["filename"]: entry["digests"]["sha256"] for entry in files}
        # urllib's errors are OSErrors; a body that is no JSON, or JSON of
        # another shape, is a ValueError, a KeyError or a TypeError.
        except (OSError, ValueError, KeyError, TypeError) as error:
            last = f"{url} answered {error}"
        else:
            if wanted <= listed.keys():
                return listed
            last = f"{url} lists {sorted(listed)}"
        if attempt < attempts:
            sleep(wait_s)
    msg = f"PyPI does not list the sdist and the wheel of {version} after {attempts} attempts: {last}"
    raise RuntimeError(msg)


def mismatches(
    built: Mapping[str, str], expected: Mapping[str, str], source: str
) -> list[str]:
    """Every way the files built differ from the ones *source* lists.

    :param built: The digests of the files just built, by name.
    :param expected: The digests *source* lists, by name.
    :param source: What *expected* was read from, for the messages.
    :return: One sentence per difference; empty when every file built is
        listed with its digest and nothing else is listed.
    """
    problems = []
    for name, digest in sorted(built.items()):
        if name not in expected:
            problems.append(f"{source} does not list {name}")
        elif expected[name] != digest:
            problems.append(
                f"{name} rebuilds to SHA-256 {digest}, and {source} lists {expected[name]}"
            )
    problems += [
        f"{source} lists {name}, which the build did not make"
        for name in sorted(expected.keys() - built.keys())
    ]
    return problems


def _read_check_file(path: pathlib.Path) -> dict[str, str]:
    """The digests the checksum file at *path* lists, read before anything is built.

    :raises ValueError: When the file is not text in the format ``sha256sum``
        writes, or lists no file.
    :raises OSError: When it cannot be read.
    """
    listed = read_checksums(path.read_text(encoding="utf-8"))
    if not listed:
        msg = f"the checksum file {path} lists no file"
        raise ValueError(msg)
    return listed


def _build_and_compare(args: argparse.Namespace) -> int:
    """What :func:`main` does once the platform and the arguments are settled."""
    expected = None if args.check is None else _read_check_file(args.check)
    version = (_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    problems = foreign_plugins() + [
        f"the checkout differs from its commit: {line}" for line in checkout_changes()
    ]
    for problem in problems:
        print(f"::error::{problem}", file=sys.stderr)
    if problems:
        return 1
    built = digests(build(args.outdir, version=version, epoch=commit_time()))
    for name, digest in built.items():
        print(f"{digest}  {name}")
    if expected is not None:
        source = args.check.name
    elif args.check_pypi:
        expected = pypi_digests(version)
        source = "PyPI"
    else:
        return 0
    problems = mismatches(built, expected, source)
    for problem in problems:
        print(f"::error::{problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"The sdist and the wheel of {version} rebuild to the files {source} lists.")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Build the commit's sdist and wheel; print their digests, and compare them if asked.

    Every failure the script expects ends as one ``::error::`` line and exit
    status 1: a platform it does not build on, a checksum file that is missing
    or malformed (found before anything is built), a checkout or an
    environment that would change what is packed, a build that fails, hangs
    or leaves other files, an output directory that is a file, and PyPI still
    not listing the files after the last attempt.
    """
    # First of all, before the arguments are read: on Windows nothing else
    # the script could say applies.
    if os.name == "nt":
        print(f"::error::{WINDOWS_REFUSAL}", file=sys.stderr)
        return 1
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--outdir",
        type=pathlib.Path,
        required=True,
        help="an empty or absent directory to build into",
    )
    compare = parser.add_mutually_exclusive_group()
    compare.add_argument(
        "--check",
        type=pathlib.Path,
        help="a checksum file, as sha256sum writes it, that both files must match",
    )
    compare.add_argument(
        "--check-pypi",
        action="store_true",
        help="compare both files with the digests PyPI publishes for the version",
    )
    args = parser.parse_args(argv)
    try:
        return _build_and_compare(args)
    # A ValueError is a malformed checksum file or a build that left other
    # files; a RuntimeError, PyPI giving up; an OSError, a file that cannot
    # be read or an output directory that is a file; a SubprocessError, a
    # build or a git query that failed or ran out of time.
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(f"::error::{error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
