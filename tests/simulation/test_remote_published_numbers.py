#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every number the guide on remote nodes publishes comes from the code or the record that sets it.

The guide says how many packages a node keeps and for how long one is never
pruned, how soon a dead connection is noticed, how long ssh tries to
connect, how long a run may go on once its client has closed the
connection, the keep-alive a node's ssh server should use, the CuPy and
Python of the GPU image, and the Python, NumPy and SciPy a Python node needs,
in English, in Spanish and in its docs/ mirror. Each phrase is built here
from the constant or the lock entry that decides it, so a change to one
leaves the pages failing until they say the new number.

The dead connection is "about a minute", not "within": OpenSSH gives up
once more keep-alives than ``ServerAliveCountMax`` go unanswered, between
four and five intervals of 15 s, and its manual says "approximately".
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from phonometry.simulation._remote import bootstrap, command, node
from phonometry.simulation._remote.package import FLOORS, PYTHON_FLOOR

_ROOT = Path(__file__).resolve().parents[2]
_LOCK = json.loads((_ROOT / "gpu-parity.lock").read_text(encoding="utf-8"))
_NUMBERS_EN = {5: "five", 30: "30 seconds", 60: "a minute", 600: "ten minutes"}
_NUMBERS_ES = {5: "cinco", 30: "30 segundos", 60: "un minuto", 600: "diez minutos"}
#: How the pages write each dependency a Python node needs. A dependency the
#: package gains raises KeyError here: add it to this table and to the pages.
_DEPENDENCIES = {"numpy": "NumPy", "scipy": "SciPy"}
#: The pages and their language. The Spanish page joins this list when it
#: exists.
_PAGES = [
    ("site/src/content/docs/simulation/remote-node.mdx", "en"),
    ("docs/simulation/remote-node.md", "en"),
]


def _ssh_option(name: str) -> int:
    return int(
        next(
            word.partition("=")[2]
            for word in command.SSH_OPTIONS
            if word.startswith(f"{name}=")
        )
    )


def _phrases(numbers: dict[int, str], language: str) -> list[str]:
    interval, count = (
        _ssh_option("ServerAliveInterval"),
        _ssh_option("ServerAliveCountMax"),
    )
    keep = numbers[bootstrap.KEEP]
    margin = numbers[int(bootstrap._PRUNE_MARGIN_S)]
    dead = numbers[interval * count]
    connect = numbers[_ssh_option("ConnectTimeout")]
    grace = numbers[int(node._GRACE_S)]
    shared = [
        f"ClientAliveInterval {interval}",
        f"ClientAliveCountMax {count}",
        f"CuPy {_LOCK['cupy']}",
        "Python " + ".".join(_LOCK["python"].split(".")[:2]),
        # What a Python node needs, in the prose and in the install line.
        f"Python {PYTHON_FLOOR}",
        *(f"{_DEPENDENCIES[name]} {floor}" for name, floor in FLOORS.items()),
        *(f'"{name}>={floor}"' for name, floor in FLOORS.items()),
    ]
    if language == "en":
        return [
            f"keeps the {keep} packages used last",
            f"never one used in the last {margin}",
            f"notices a dead connection in about {dead}",
            f"gives up connecting after {connect}",
            f"ends at most {grace} after its client closes the connection",
            *shared,
        ]
    return [
        f"conserva los {keep} paquetes usados por última vez",
        f"nunca uno usado en los últimos {margin}",
        f"detecta una conexión muerta en aproximadamente {dead}",
        f"deja de intentar conectar a los {connect}",
        f"termina como mucho {grace} después de que su cliente cierre la conexión",
        *shared,
    ]


@pytest.mark.parametrize(("page", "language"), _PAGES)
def test_the_guide_quotes_the_numbers_the_code_sets(page: str, language: str) -> None:
    text = " ".join((_ROOT / page).read_text(encoding="utf-8").split())
    numbers = _NUMBERS_EN if language == "en" else _NUMBERS_ES
    missing = [phrase for phrase in _phrases(numbers, language) if phrase not in text]
    assert not missing, f"{page} does not say: {missing}"
