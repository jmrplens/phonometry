#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every number the guide on remote nodes publishes comes from the code or the record that sets it.

The guide says how many packages a node keeps and for how long one is never
pruned, how soon a dead connection is noticed on either side, how long ssh
tries to connect, how long a run may go on once its client has closed the
connection, the keep-alive a node's ssh server should use, the CuPy and
Python of the GPU image, and the Python, NumPy and SciPy a node needs, in
English, in Spanish and in its docs/ mirror. Each phrase is built here from
the constant or the lock entry that decides it, so a change to one leaves
the pages failing until they say the new number.

A phrase found once is not enough: a page may print the same number twice,
and a copy left behind would still read as the guide's word, or satisfy a
check meant for another number. So every copy is held too. A duration or a
count written in words appears only inside the phrases built here; every
version a page prints after "Python", "NumPy", "SciPy" or "CuPy", every
requirement of an install line and every keep-alive setting is the one the
code or the lock sets. A Python version followed by the language's "or
later" is the package's floor, and any other is the image's.

The dead connection is "about a minute", not "within": OpenSSH gives up
once more keep-alives than ``ServerAliveCountMax`` go unanswered, between
four and five intervals of 15 s, and its manual says "approximately".
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from phonometry.simulation._remote import bootstrap, command, node
from phonometry.simulation._remote.package import FLOORS, PYTHON_FLOOR

_ROOT = Path(__file__).resolve().parents[2]
_LOCK = json.loads((_ROOT / "gpu-parity.lock").read_text(encoding="utf-8"))
#: How each language writes the numbers the phrases quote. A constant moved
#: to a number a table does not hold raises KeyError: add its words to both
#: tables and to the pages.
_NUMBERS = {
    "en": {5: "five", 30: "30 seconds", 60: "a minute", 600: "ten minutes"},
    "es": {5: "cinco", 30: "30 segundos", 60: "un minuto", 600: "diez minutos"},
}
#: What follows a floor's version in each language.
_LATER = {"en": "or later", "es": "o posterior"}
#: How the pages write each dependency a node needs. A dependency the
#: package gains raises KeyError here: add it to this table and to the pages.
_DEPENDENCIES = {"numpy": "NumPy", "scipy": "SciPy"}
#: The pages and their language.
_PAGES = [
    ("site/src/content/docs/simulation/remote-node.mdx", "en"),
    ("docs/simulation/remote-node.md", "en"),
    ("site/src/content/docs/es/simulation/remote-node.mdx", "es"),
]


def _text(page: str) -> str:
    """The page with its whitespace joined, so a phrase may wrap across lines."""
    return " ".join((_ROOT / page).read_text(encoding="utf-8").split())


def _ssh_option(name: str) -> int:
    return int(
        next(
            word.partition("=")[2]
            for word in command.SSH_OPTIONS
            if word.startswith(f"{name}=")
        )
    )


def _keep_alive() -> tuple[int, int]:
    """The client's keep-alive interval [s] and count, which the node's server is told to use."""
    return _ssh_option("ServerAliveInterval"), _ssh_option("ServerAliveCountMax")


def _phrases(language: str) -> tuple[list[str], set[str]]:
    """The phrases a page in *language* says, and the number words they quote."""
    numbers = _NUMBERS[language]
    interval, count = _keep_alive()
    keep = numbers[bootstrap.KEEP]
    margin = numbers[int(bootstrap._PRUNE_MARGIN_S)]
    dead = numbers[interval * count]
    connect = numbers[_ssh_option("ConnectTimeout")]
    grace = numbers[int(node._GRACE_S)]
    words = {keep, margin, dead, connect, grace}
    if language == "en":
        return [
            f"keeps the {keep} packages used last",
            f"never one used in the last {margin}",
            f"notices a dead connection in about {dead}",
            f"notices a vanished client in about {dead}",
            f"gives up connecting after {connect}",
            f"ends at most {grace} after its client closes the connection",
        ], words
    return [
        f"conserva los {keep} paquetes usados por última vez",
        f"nunca uno usado en los últimos {margin}",
        f"detecta una conexión muerta en aproximadamente {dead}",
        f"detecta un cliente desaparecido en aproximadamente {dead}",
        f"deja de intentar conectar a los {connect}",
        f"termina como mucho {grace} después de que su cliente cierre la conexión",
    ], words


def _count(text: str, words: str) -> int:
    return len(re.findall(rf"\b{re.escape(words.lower())}\b", text.lower()))


def _loose_words(text: str, language: str) -> list[str]:
    """Each number word printed more often than the phrases built here print it."""
    phrases, words = _phrases(language)
    loose = []
    for word in sorted(words):
        tied = sum(
            text.lower().count(phrase.lower()) * _count(phrase, word)
            for phrase in phrases
        )
        if _count(text, word) != tied:
            loose.append(
                f"{word!r} {_count(text, word)} times, {tied} of them in a phrase built from the code"
            )
    return loose


def _wrong_versions(text: str, language: str) -> list[str]:
    """Each kind of version or setting a page prints that is not the code's or the lock's."""
    later = re.escape(_LATER[language])
    pythons = re.findall(rf"\bPython (\d+\.\d+)(?:\.\d+)*( {later})?", text)
    printed = {
        "Python floor": {version for version, after in pythons if after},
        "Python of the image": {version for version, after in pythons if not after},
        "CuPy": set(re.findall(r"\bCuPy (\d+(?:\.\d+)+)", text)),
        "ClientAliveInterval": set(re.findall(r"\bClientAliveInterval (\d+)", text)),
        "ClientAliveCountMax": set(re.findall(r"\bClientAliveCountMax (\d+)", text)),
    }
    interval, count = _keep_alive()
    expected = {
        "Python floor": {PYTHON_FLOOR},
        "Python of the image": {".".join(_LOCK["python"].split(".")[:2])},
        "CuPy": {_LOCK["cupy"]},
        "ClientAliveInterval": {str(interval)},
        "ClientAliveCountMax": {str(count)},
    }
    for name, floor in FLOORS.items():
        shown = _DEPENDENCIES[name]
        printed[shown] = set(re.findall(rf"\b{shown} (\d+(?:\.\d+)+)", text))
        printed[f"{name} install line"] = set(re.findall(rf'"{name}>=([^"\s]+)"', text))
        expected[shown] = expected[f"{name} install line"] = {floor}
    return [
        f"{kind}: {sorted(printed[kind])}, not {sorted(want)}"
        for kind, want in expected.items()
        if printed[kind] != want
    ]


@pytest.mark.parametrize(("page", "language"), _PAGES)
def test_the_guide_quotes_the_numbers_the_code_sets(page: str, language: str) -> None:
    text = _text(page)
    missing = [phrase for phrase in _phrases(language)[0] if phrase not in text]
    assert not missing, f"{page} does not say: {missing}"


@pytest.mark.parametrize(("page", "language"), _PAGES)
def test_every_copy_of_a_number_is_the_one_the_code_sets(
    page: str, language: str
) -> None:
    text = _text(page)
    problems = _loose_words(text, language) + _wrong_versions(text, language)
    assert not problems, f"{page} prints: {problems}"
