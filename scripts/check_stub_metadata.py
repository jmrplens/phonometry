#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Hold the built PyOctaveBand stub to its pin and to the licence it declares.

``stub/`` builds the final ``PyOctaveBand`` release: a shim that installs
``phonometry`` and re-exports it under the old ``pyoctaveband`` module name.
Its whole promise is that ``pip install -U PyOctaveBand`` keeps existing code
working and that renaming the import is the entire migration. That holds only
while the resolved ``phonometry`` still exports the names the last release
under the old name exported, and a major release is exactly where those go, so
the requirement has to be capped below the next major.

The same files carry the licence. PEP 639 writes the SPDX expression into the
metadata as ``License-Expression`` and each licence file as ``License-File``,
and puts the file itself under ``.dist-info/licenses/`` in the wheel and at the
root of the sdist. PyOctaveBand 2.2.0 shipped neither: a licence classifier
and no text, in a package whose licence asks that its text travel with every
copy.

``tests/test_transition_stub.py`` asserts the cap in ``stub/pyproject.toml`` and
that ``stub/LICENSE`` is the repository's ``LICENSE``. This asserts both in the
artifact, because ``pyproject.toml`` is not what a resolver or a user reads:
pip reads ``Requires-Dist`` out of the built metadata, the licence is read out
of the files that were uploaded, and a build backend or a packaging config can
put something else in either. The two checks are deliberately at opposite ends
of the build.

Run after ``python -m build stub/``::

    python scripts/check_stub_metadata.py

CI runs it in the ``transition-stub`` job, right after ``twine check``, and
``publish-stub.yml`` runs it on the files it is about to upload.
"""

from __future__ import annotations

import argparse
import pathlib
import sys
import tarfile
import zipfile
from email import message_from_string
from typing import TYPE_CHECKING

from packaging.requirements import Requirement
from packaging.version import Version

if TYPE_CHECKING:
    from email.message import Message

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_DIST = _ROOT / "stub" / "dist"

#: The first version the stub must refuse. Everything below it is a release of
#: the line whose API the shim re-exports; this one may have retired a name.
_NEXT_MAJOR = Version("4.0.0")

#: Excluded as well, because pip will install a pre-release of the excluded
#: major when a specifier's upper bound admits one.
_NEXT_MAJOR_PRERELEASE = Version("4.0.0rc1")

#: The oldest release that carries the API the shim re-exports.
_OLDEST_SUPPORTED = Version("3.0.0")

#: A late 3.x, to catch a cap that shuts the door on the line it should keep
#: open (``==3.0.*``, say, or a stray ``<3.1``).
_LATEST_SUPPORTED_LINE = Version("3.99.0")

#: The SPDX expression the stub declares: the project's own licence.
_LICENSE_EXPRESSION = "MIT"

#: The licence files the stub declares, by the path PEP 639 records.
_LICENSE_FILES = ("LICENSE",)

#: The text each of them has to carry: the project's, at the repository root.
_PROJECT_LICENSE = _ROOT / "LICENSE"


class _Built:
    """One built file: its metadata, and its licence files where PEP 639 puts them.

    A ``License-File`` path is relative to the root of the sdist, and to
    ``.dist-info/licenses/`` in the wheel.
    """

    def __init__(self, path: pathlib.Path) -> None:
        self.label = path.name
        self._path = path
        self._wheel = path.suffix == ".whl"
        self.metadata, self._root = (
            self._read_wheel() if self._wheel else self._read_sdist()
        )

    def _read_wheel(self) -> tuple[Message, str]:
        with zipfile.ZipFile(self._path) as archive:
            names = [
                name
                for name in archive.namelist()
                if name.endswith(".dist-info/METADATA")
            ]
            if len(names) != 1:
                msg = f"{self.label}: expected one METADATA, found {names}"
                raise SystemExit(msg)
            metadata = message_from_string(archive.read(names[0]).decode("utf-8"))
        return metadata, names[0].removesuffix("METADATA") + "licenses/"

    def _read_sdist(self) -> tuple[Message, str]:
        with tarfile.open(self._path) as archive:
            names = [name for name in archive.getnames() if name.endswith("/PKG-INFO")]
            # The top-level PKG-INFO, not one belonging to a vendored tree.
            names = [name for name in names if name.count("/") == 1]
            if len(names) != 1:
                msg = f"{self.label}: expected one PKG-INFO, found {names}"
                raise SystemExit(msg)
            handle = archive.extractfile(names[0])
            if handle is None:
                msg = f"{self.label}: {names[0]} is not a regular file"
                raise SystemExit(msg)
            metadata = message_from_string(handle.read().decode("utf-8"))
        return metadata, names[0].removesuffix("PKG-INFO")

    def where(self, licence_file: str) -> str:
        """The member a ``License-File`` path names in this file."""
        return self._root + licence_file

    def licence_text(self, licence_file: str) -> bytes | None:
        """The bytes of the licence file *licence_file* names, or ``None``."""
        member = self.where(licence_file)
        if self._wheel:
            with zipfile.ZipFile(self._path) as archive:
                if member not in archive.namelist():
                    return None
                return archive.read(member)
        with tarfile.open(self._path) as archive:
            try:
                handle = archive.extractfile(member)
            except KeyError:
                return None
            return None if handle is None else handle.read()


def _phonometry_requirement(metadata: Message, label: str) -> Requirement:
    declared = [
        Requirement(str(value)) for value in metadata.get_all("Requires-Dist", [])
    ]
    named = [item for item in declared if item.name == "phonometry"]
    if len(named) != 1:
        msg = (
            f"{label}: expected exactly one phonometry requirement, "
            f"found {[str(item) for item in named]}"
        )
        raise SystemExit(msg)
    return named[0]


def _problems(requirement: Requirement, label: str) -> list[str]:
    specifier = requirement.specifier
    found: list[str] = []
    if not specifier.contains(_OLDEST_SUPPORTED):
        found.append(
            f"{label}: '{requirement}' excludes phonometry {_OLDEST_SUPPORTED}, "
            f"the oldest release that carries the API the shim re-exports."
        )
    if not specifier.contains(_LATEST_SUPPORTED_LINE):
        found.append(
            f"{label}: '{requirement}' excludes phonometry "
            f"{_LATEST_SUPPORTED_LINE}; every release of that line must stay "
            f"eligible."
        )
    for rejected, what in (
        (_NEXT_MAJOR, "the next major"),
        (_NEXT_MAJOR_PRERELEASE, "a pre-release of the next major"),
    ):
        if specifier.contains(rejected, prereleases=True):
            found.append(
                f"{label}: '{requirement}' admits phonometry {rejected} ({what}). "
                f"The stub would then re-export a phonometry that may have "
                f"retired names 'import pyoctaveband' promises, and user code "
                f"would raise AttributeError with nothing naming the cause. "
                f"Cap the requirement in stub/pyproject.toml."
            )
    return found


def _licence_problems(built: _Built, project_licence: bytes) -> list[str]:
    """What is wrong with the licence one built file declares and carries."""
    label = built.label
    found: list[str] = []
    expressions = [
        str(value) for value in built.metadata.get_all("License-Expression", [])
    ]
    if expressions != [_LICENSE_EXPRESSION]:
        found.append(
            f"{label}: License-Expression is {expressions or 'missing'}, expected "
            f"'{_LICENSE_EXPRESSION}'. Declare license = \"{_LICENSE_EXPRESSION}\" "
            f"in stub/pyproject.toml."
        )
    declared = [str(value) for value in built.metadata.get_all("License-File", [])]
    if declared != list(_LICENSE_FILES):
        found.append(
            f"{label}: License-File is {declared or 'missing'}, expected "
            f"{list(_LICENSE_FILES)}. Declare license-files = "
            f"{list(_LICENSE_FILES)} in stub/pyproject.toml, beside a copy of "
            f"the repository's LICENSE."
        )
    for licence_file in _LICENSE_FILES:
        text = built.licence_text(licence_file)
        if text is None:
            found.append(
                f"{label}: {built.where(licence_file)} is missing. The licence "
                f"asks that its text be included in every copy, and this file "
                f"would go out without it."
            )
        elif text != project_licence:
            found.append(
                f"{label}: {built.where(licence_file)} is not the repository's "
                f"LICENSE; copy it into stub/ again."
            )
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument(
        "--dist",
        type=pathlib.Path,
        default=_DIST,
        help="the directory python -m build stub/ wrote to (default: stub/dist)",
    )
    args = parser.parse_args(argv)
    dist: pathlib.Path = args.dist
    artifacts = sorted(dist.glob("*.whl")) + sorted(dist.glob("*.tar.gz"))
    if not artifacts:
        msg = f"no built artifacts in {dist}; run 'python -m build stub/' first"
        raise SystemExit(msg)
    project_licence = _PROJECT_LICENSE.read_bytes()

    problems: list[str] = []
    for artifact in artifacts:
        built = _Built(artifact)
        requirement = _phonometry_requirement(built.metadata, built.label)
        print(f"{built.label}: Requires-Dist: {requirement}")
        problems.extend(_problems(requirement, built.label))
        print(
            f"{built.label}: License-Expression: "
            f"{built.metadata.get('License-Expression', 'missing')}"
        )
        problems.extend(_licence_problems(built, project_licence))

    for problem in problems:
        print(f"::error::{problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
