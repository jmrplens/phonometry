#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every Environments page says when its commands were run, and on what.

The pages under ``start/environments/`` say that their commands were run
where they say, and they are the pages of the site that age fastest: which
extras micropip installs, which wheels an image has, which strict mode a
checker passes. ``environment_checks.json`` is the record of the last run of
those commands, the day, the phonometry release and the version of every tool
and image each page ran on, and each page, in English and in Spanish, carries
one paragraph that says so, opening "Checked on" or "Comprobado el". A page
whose commands were run again on their own, later than the rest, carries the
day and the release of that run in its own entry.

A new run that changes the record and leaves a page behind fails here, and so
does a page edited to a version no record holds: the paragraph has to quote
every value of its page's record, and every version number it quotes has to be
one of them. The GitHub edition under ``docs/`` and the llms files are written
from the English page, so holding the two site pages holds them.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_RECORD = json.loads(
    (Path(__file__).resolve().parent / "environment_checks.json").read_text(
        encoding="utf-8"
    )
)

#: The two copies of each page written by hand.
_COPIES = {
    "en": "site/src/content/docs/start/environments/{}.md",
    "es": "site/src/content/docs/es/start/environments/{}.md",
}

#: How the paragraph opens in each language.
_OPENING = {"en": "Checked on ", "es": "Comprobado el "}

_MONTHS_ES = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]

#: A version number as the paragraph writes one: ``3.13.18``, ``26.3``.
_VERSION = re.compile(r"(?<![\w.])\d+(?:\.\d+)+(?![\w.]*\w)")

#: A code span, whose text is a name (an image, a digest), not prose.
_CODE = re.compile(r"`([^`]*)`")


#: The keys of a page's entry that say when it was checked, not on what.
_WHEN = ("date", "phonometry")


#: The page that sums the section up, and quotes every run of its pages.
_OVERVIEW = "index"


def _release(page: str) -> str:
    """The phonometry release the page's commands were run with."""
    return str(_RECORD["pages"][page].get("phonometry", _RECORD["phonometry"]))


def _day(page: str, language: str) -> str:
    day = date.fromisoformat(_RECORD["pages"][page].get("date", _RECORD["date"]))
    if language == "en":
        return f"{day.day} {day:%B} {day.year}"
    return f"{day.day} de {_MONTHS_ES[day.month - 1]} de {day.year}"


def _values(page: str) -> list[str]:
    """Every value of a page's record, lists flattened.

    The overview (``index``) answers for the section, so it also names every
    release a page of it was checked with on its own, beside its own.
    """
    values: list[str] = []
    for key, value in _RECORD["pages"][page].items():
        if key in _WHEN:
            continue
        values.extend(value if isinstance(value, list) else [value])
    if page == _OVERVIEW:
        others = {_release(name) for name in _RECORD["pages"]} - {_release(page)}
        values.extend(sorted(others))
    return values


def _paragraphs(text: str) -> list[str]:
    """The page's paragraphs outside its fences, each joined into one line."""
    body = text.split("\n---\n", 1)[1]
    body = re.sub(r"^```.*?^```", "", body, flags=re.DOTALL | re.MULTILINE)
    return [" ".join(block.split()) for block in re.split(r"\n\s*\n", body)]


def _checked(page: str, language: str) -> str:
    text = (_ROOT / _COPIES[language].format(page)).read_text(encoding="utf-8")
    found = [p for p in _paragraphs(text) if p.startswith(_OPENING[language])]
    assert len(found) == 1, (
        f"{_COPIES[language].format(page)} carries {len(found)} paragraphs that "
        f'open "{_OPENING[language]}", not one'
    )
    return found[0]


def _missing(page: str, paragraph: str) -> list[str]:
    """The values of the page's record the paragraph does not quote."""
    return [value for value in _values(page) if value not in paragraph]


def _stray(page: str, paragraph: str) -> list[str]:
    """The version numbers the paragraph quotes that its record does not hold."""
    recorded = set(_values(page)) | {_release(page)}
    # A code span names an image or a digest the record holds whole; its
    # digits are no version of their own.
    prose = _CODE.sub(
        lambda span: "" if span.group(1) in recorded else span.group(0), paragraph
    )
    return [number for number in _VERSION.findall(prose) if number not in recorded]


_CASES = [(page, language) for page in _RECORD["pages"] for language in _COPIES]


def test_the_record_names_every_environments_page() -> None:
    written = {
        path.stem
        for path in (_ROOT / "site/src/content/docs/start/environments").glob("*.md")
    }
    assert set(_RECORD["pages"]) == written


@pytest.mark.parametrize(("page", "language"), _CASES)
def test_the_page_says_when_and_with_which_release_it_was_checked(
    page: str, language: str
) -> None:
    paragraph = _checked(page, language)
    assert _day(page, language) in paragraph, paragraph
    assert f"phonometry {_release(page)}" in paragraph, paragraph


@pytest.mark.parametrize(("page", "language"), _CASES)
def test_the_page_quotes_every_version_of_its_record(page: str, language: str) -> None:
    paragraph = _checked(page, language)
    missing = _missing(page, paragraph)
    assert not missing, f"{page} ({language}) leaves out {missing}: {paragraph}"


@pytest.mark.parametrize(("page", "language"), _CASES)
def test_every_version_the_page_quotes_is_one_its_record_holds(
    page: str, language: str
) -> None:
    stray = _stray(page, _checked(page, language))
    assert not stray, f"{page} ({language}) quotes {stray}, which no record holds"


def test_a_paragraph_that_drifts_from_its_record_is_caught() -> None:
    # The two failures the tests above exist for, on a paragraph written for
    # them: a version the run did not use, and so one the run did use left out.
    paragraph = (
        "Checked on 17 November 2026 with phonometry 4.0.0 from PyPI, in the "
        "`python:3.12-slim` and `python:3.14-slim` images, on Python 3.12.16 and "
        "3.14.10 with NumPy 2.5.5: mypy 2.4.0 and pyright 1.1.414."
    )
    assert _missing("type-checking", paragraph) == ["2.4.1"]
    assert _stray("type-checking", paragraph) == ["2.4.0"]
    # An image the record does not hold is prose, and its tag a version.
    unrecorded = paragraph.replace("python:3.14", "python:3.11")
    assert _stray("type-checking", unrecorded) == ["3.11", "2.4.0"]


def test_a_page_run_on_its_own_is_held_to_that_run() -> None:
    # The conda page was run again, on its own, after the rest: its paragraph
    # answers with that run's day and release, the record's release in its
    # place is a version the page's entry does not hold, and neither key is a
    # tool version the paragraph has to quote.
    assert _day("conda", "en") == "21 November 2026"
    assert _day("conda", "es") == "21 de noviembre de 2026"
    assert _release("conda") == "4.0.1"
    assert _day("type-checking", "en") == "17 November 2026"
    assert _release("type-checking") == "4.0.0"
    paragraph = _checked("conda", "en").replace("4.0.1", "4.0.0")
    assert _stray("conda", paragraph) == ["4.0.0"]
    assert not {"2026-11-21", "4.0.1"} & set(_values("conda"))
