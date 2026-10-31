#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The licence a built wheel or sdist declares and carries, read as PEP 639 lays it out.

PEP 639 writes the SPDX expression into the metadata as ``License-Expression``
and each licence file as ``License-File``, and puts the file itself under
``.dist-info/licenses/`` in the wheel and at the root of the sdist. Two
packages are built from this repository and uploaded to PyPI: phonometry, by
``release.yml``, and the PyOctaveBand bridge, by ``publish-stub.yml``. Each
one's files are held to the licence they have to declare and carry before the
upload, by ``check_release_artifacts.py`` and ``check_stub_metadata.py``. The
reading and the checks are the same for both, so they live here once.

What they catch is what PyOctaveBand 2.2.0 shipped: a licence classifier and
no licence text, in a package whose licence asks that its text travel with
every copy. ``pyproject.toml`` is not what anyone downloads, and a build
backend or a packaging change can put something else in the files, so the
files are read.
"""

from __future__ import annotations

import tarfile
import zipfile
from email import message_from_string
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Mapping
    from email.message import Message


class Built:
    """One built file: its metadata, and its licence files where PEP 639 puts them.

    A ``License-File`` path is relative to the root of the sdist, and to
    ``.dist-info/licenses/`` in the wheel.

    :param path: A wheel (``.whl``) or an sdist (``.tar.gz``).
    :raises ValueError: When the file does not hold exactly one metadata file
        where a wheel or an sdist keeps it.
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
                raise ValueError(msg)
            metadata = message_from_string(archive.read(names[0]).decode("utf-8"))
        return metadata, names[0].removesuffix("METADATA") + "licenses/"

    def _read_sdist(self) -> tuple[Message, str]:
        with tarfile.open(self._path) as archive:
            names = [name for name in archive.getnames() if name.endswith("/PKG-INFO")]
            # The top-level PKG-INFO, not one belonging to a vendored tree.
            names = [name for name in names if name.count("/") == 1]
            if len(names) != 1:
                msg = f"{self.label}: expected one PKG-INFO, found {names}"
                raise ValueError(msg)
            handle = archive.extractfile(names[0])
            if handle is None:
                msg = f"{self.label}: {names[0]} is not a regular file"
                raise ValueError(msg)
            metadata = message_from_string(handle.read().decode("utf-8"))
        return metadata, names[0].removesuffix("PKG-INFO")

    def where(self, license_file: str) -> str:
        """The member a ``License-File`` path names in this file."""
        return self._root + license_file

    def license_text(self, license_file: str) -> bytes | None:
        """The bytes of the licence file *license_file* names, or ``None``."""
        member = self.where(license_file)
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


def license_problems(
    built: Built, *, expression: str, files: Mapping[str, bytes], config: str
) -> list[str]:
    """What is wrong with the licence one built file declares and carries.

    :param built: The wheel or the sdist, read.
    :param expression: The SPDX expression its metadata has to declare.
    :param files: Each licence file its metadata has to declare, in the order
        declared, with the text of the repository's file it has to carry.
    :param config: The ``pyproject.toml`` that declares both, named in the
        fix each problem suggests.
    :return: One sentence per problem; empty when the licence is right.
    """
    label = built.label
    found: list[str] = []
    expressions = [
        str(value) for value in built.metadata.get_all("License-Expression", [])
    ]
    if expressions != [expression]:
        found.append(
            f"{label}: License-Expression is {expressions or 'missing'}, expected "
            f"'{expression}'. Declare license = \"{expression}\" in {config}."
        )
    declared = [str(value) for value in built.metadata.get_all("License-File", [])]
    if declared != list(files):
        found.append(
            f"{label}: License-File is {declared or 'missing'}, expected "
            f"{list(files)}. Declare license-files = {list(files)} in {config}."
        )
    for license_file, expected in files.items():
        text = built.license_text(license_file)
        if text is None:
            found.append(
                f"{label}: {built.where(license_file)} is missing. The licence "
                f"asks that its text be included in every copy, and this file "
                f"would go out without it."
            )
        elif text != expected:
            found.append(
                f"{label}: {built.where(license_file)} is not the repository's "
                f"{license_file}; the {license_file} beside {config} has to be a "
                f"copy of it."
            )
    return found
