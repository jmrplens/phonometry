#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every page that counts the package's import namespaces counts the ones it has.

The landing page and the getting-started guide, in English, in Spanish and
in the guide's docs/ mirror, say in words how many import namespaces the
documentation's areas group. Each is held here to the subpackages of
``phonometry`` an import can name, the public ones, so a namespace added or
retired leaves these pages failing until they say the new count. The landing
page had come to say nineteen and the English guide twenty where the package
has twenty-one.
"""

from __future__ import annotations

import pkgutil
import re
from pathlib import Path

import pytest

import phonometry

_ROOT = Path(__file__).resolve().parents[1]
#: How each language writes the count before its noun. A count the table does
#: not hold raises KeyError: add its words here and to the pages. Spanish
#: apocopates "veintiuno" before a masculine noun.
_WORDS = {"en": {21: "twenty-one"}, "es": {21: "veintiún"}}
#: Each page, its language, and the phrase that carries the count.
_PHRASES = [
    ("site/src/data/home.ts", "en", "over {} import namespaces"),
    ("site/src/data/home.ts", "es", "sobre {} espacios de nombres de importación"),
    (
        "site/src/content/docs/start/getting-started.mdx",
        "en",
        "one of {} import namespaces",
    ),
    (
        "site/src/content/docs/es/start/getting-started.mdx",
        "es",
        "uno de los {} espacios de nombres de importación",
    ),
    ("docs/start/getting-started.md", "en", "one of {} domain namespaces"),
]


def _namespaces() -> int:
    return sum(
        1
        for module in pkgutil.iter_modules(phonometry.__path__)
        if module.ispkg and not module.name.startswith("_")
    )


@pytest.mark.parametrize(("page", "language", "phrase"), _PHRASES)
def test_a_page_counts_the_import_namespaces_the_package_has(
    page: str, language: str, phrase: str
) -> None:
    text = " ".join((_ROOT / page).read_text(encoding="utf-8").split())
    expected = phrase.format(_WORDS[language][_namespaces()])
    pattern = re.escape(phrase).replace(re.escape("{}"), r"(\S+)")
    printed = re.findall(pattern, text)
    assert printed, f"{page} no longer says {phrase.format('N')!r}"
    assert all(phrase.format(word) == expected for word in printed), (
        f"{page} says {printed}, not {expected!r}"
    )
