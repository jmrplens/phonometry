#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Hold the built PyOctaveBand stub to its pin and to the licence it declares.

``stub/`` builds the final ``PyOctaveBand`` release: a shim that installs
``phonometry`` and re-exports it under the old ``pyoctaveband`` module name.
Its whole promise is that ``pip install -U PyOctaveBand`` keeps existing code
working and that renaming the import is the entire migration. That holds only
while the resolved ``phonometry`` still exports the names the last release
under the old name exported, and a major release is exactly where those go, so
the requirement has to be capped below the next major.

The same files carry the licence: ``License-Expression`` and ``License-File``
in the metadata, and the text where PEP 639 puts it. PyOctaveBand 2.2.0
shipped neither, only a licence classifier. ``built_license.py`` reads the
files and checks the licence, as it does for phonometry's own release.

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
from typing import TYPE_CHECKING

from built_license import Built, license_problems
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

#: The licence files the stub declares, by the path PEP 639 records. Each has
#: to carry the text of the repository's file of the same name.
_LICENSE_FILES = ("LICENSE",)


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
    license_files = {name: (_ROOT / name).read_bytes() for name in _LICENSE_FILES}

    problems: list[str] = []
    for artifact in artifacts:
        try:
            built = Built(artifact)
        except ValueError as error:
            raise SystemExit(str(error)) from None
        requirement = _phonometry_requirement(built.metadata, built.label)
        print(f"{built.label}: Requires-Dist: {requirement}")
        problems.extend(_problems(requirement, built.label))
        print(
            f"{built.label}: License-Expression: "
            f"{built.metadata.get('License-Expression', 'missing')}"
        )
        problems.extend(
            license_problems(
                built,
                expression=_LICENSE_EXPRESSION,
                files=license_files,
                config="stub/pyproject.toml",
            )
        )

    for problem in problems:
        print(f"::error::{problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
