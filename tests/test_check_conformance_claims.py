#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The conformance-count writer rewrites claims and nothing else.

``scripts/check_conformance_claims.py`` reads the ``counts`` of the generated
``docs/conformance.json`` and makes every sentence in the corpus that quotes a
count say the same thing. Two properties matter more than the happy path:

* it must move the number wherever it is quoted, in either language, in
  markdown prose, in the root ``README.md`` and the ``README_PYPI.md``
  published to PyPI, in the README the PyOctaveBand stub publishes there, in
  MDX frontmatter and in the ``.zenodo.json`` description;
* it must move *only* those numbers. A blind ``str.replace`` of the old count
  for the new one has already corrupted an unrelated figure in this repository
  (``replace("303", "316")`` also hit "303 operating days"), so the writer
  substitutes the span of the captured digits, and the fixture below plants
  decoys carrying the **stale** values in unrelated sentences, on the same
  line as a real claim and on lines of their own. A regression to textual
  replacement moves them and the tests fail.

The last test runs the scan over the real corpus and asserts the writer would
change nothing, which is the property CI gates on.
"""

from __future__ import annotations

import json
import pathlib
import sys

import child_process
import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_conformance_claims as ccc

#: What the generated artefact says: the authoritative counts.
TOTAL, DOMAINS, DESIGNATIONS, SOURCES = 501, 55, 107, 84
#: What the prose still says, one release behind, everywhere.
OLD_TOTAL, OLD_DOMAINS, OLD_DESIGNATIONS, OLD_SOURCES = 462, 53, 99, 71
#: The citation groups, which no sentence may state as a count of standards.
CITATION_GROUPS = 338

#: A miniature artefact carrying only what the writer reads out of it.
REPORT = (
    json.dumps(
        {
            "counts": {
                "checks": TOTAL,
                "passing": TOTAL,
                "failing": 0,
                "domains": DOMAINS,
                "citation_groups": CITATION_GROUPS,
                "citations": CITATION_GROUPS,
                "designations": DESIGNATIONS,
                "sources": SOURCES,
            }
        }
    )
    + "\n"
)

#: The claim as the corpus words it, with the stale counts.
OLD_SPLIT = (
    f"across {OLD_DOMAINS} domains, against {OLD_DESIGNATIONS} normative "
    f"designations and {OLD_SOURCES} further published sources"
)
#: The same claim once the writer has brought it into line.
SPLIT = (
    f"across {DOMAINS} domains, against {DESIGNATIONS} normative designations "
    f"and {SOURCES} further published sources"
)

#: Sentences using the stale counts for something that is not a conformance
#: count. They must survive the rewrite verbatim.
DECOY_LINES = (
    f"The campaign ran for {OLD_DESIGNATIONS} operating days at "
    f"{OLD_DOMAINS} sites, over {OLD_TOTAL} measurement positions.\n"
    f"Annex {OLD_DOMAINS} of ISO {OLD_SOURCES}-2 lists {OLD_TOTAL} rows.\n"
)


def _write(path: pathlib.Path, text: str) -> None:
    """Write a fixture file with exactly the bytes given, on every platform."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf8", newline="")


@pytest.fixture
def corpus(tmp_path: pathlib.Path) -> pathlib.Path:
    """A miniature repository quoting the counts everywhere the real one does.

    Every claim is deliberately stale, so a writer that silently did nothing
    would fail every assertion below.
    """
    root = tmp_path / "repo"
    _write(root / "docs" / "conformance.json", REPORT)
    # The two most-read pages of prose, and the two that were outside the walk
    # for as long as it started at docs/. README_PYPI.md is the PyPI long
    # description, which PyPI freezes at upload.
    _write(
        root / "README.md",
        f"The report runs {OLD_TOTAL} conformance checks {OLD_SPLIT}, each "
        "pinning a value.\n" + DECOY_LINES,
    )
    _write(
        root / "README_PYPI.md",
        f"The report runs {OLD_TOTAL} conformance checks {OLD_SPLIT}, each "
        "pinning a value.\n",
    )
    # The other page PyPI freezes at upload: the transition stub's, which
    # sells the project on the same counts.
    _write(
        root / "stub" / "README.md",
        f"The package now runs {OLD_TOTAL} conformance checks {OLD_SPLIT}.\n"
        + DECOY_LINES,
    )
    _write(
        root / "docs" / "start" / "getting-started.md",
        f"- [Conformance report](CONFORMANCE.md): the value of all "
        f"{OLD_TOTAL} checks\n"
        f"The suite runs {OLD_TOTAL} numerical conformance checks {OLD_SPLIT}, "
        f"one for each of the {OLD_TOTAL} rows of Annex {OLD_DOMAINS}.\n" + DECOY_LINES,
    )
    _write(
        root / "site" / "src" / "content" / "docs" / "index.mdx",
        f'description: "Toolkit: {OLD_TOTAL} conformance checks against '
        f"{OLD_DESIGNATIONS} normative designations and {OLD_SOURCES} further "
        f'published sources, measured over {OLD_DOMAINS} weeks."\n',
    )
    _write(
        root / "site" / "src" / "content" / "docs" / "es" / "index.mdx",
        f'description: "Kit: {OLD_TOTAL} comprobaciones de conformidad frente '
        f"a {OLD_DESIGNATIONS} designaciones normativas y {OLD_SOURCES} fuentes "
        'publicadas adicionales."\n'
        f"La batería ejecuta {OLD_TOTAL} comprobaciones numéricas de "
        f"conformidad sobre {OLD_DOMAINS} dominios, frente a "
        f"{OLD_DESIGNATIONS} designaciones normativas y {OLD_SOURCES} fuentes "
        f"publicadas adicionales, y las {OLD_TOTAL} comprobaciones se publican.\n",
    )
    _write(
        root / ".zenodo.json",
        json.dumps(
            {
                "description": (
                    f"{OLD_TOTAL} numerical conformance checks {OLD_SPLIT}, "
                    f"among them ISO {OLD_DESIGNATIONS}-2, "
                    f"IEC 616{OLD_DOMAINS}-1 and ITU-R BS.{OLD_TOTAL}."
                )
            },
            ensure_ascii=False,
        )
        + "\n",
    )
    # Excluded by name and by directory: the report itself, the changelog, the
    # errata registry and the gitignored scratch space all quote historical
    # counts on purpose, the changelog the old count of standards among them.
    _write(
        root / "CHANGELOG.md",
        f"- {OLD_TOTAL} conformance checks across {OLD_DOMAINS} domains and "
        f"{CITATION_GROUPS} standards in 1.0.\n",
    )
    _write(root / "docs" / "ERRATA.md", f"- covered by {OLD_TOTAL} checks.\n")
    _write(
        root / "docs" / "superpowers" / "notes.md",
        f"- a local plan quoting {OLD_TOTAL} conformance checks.\n",
    )
    # The root markdown is globbed, not walked: a README one level down belongs
    # to something else (the notes on the oracle data, say) and must not be
    # rewritten from this repository's report. The stub's is named, not walked.
    _write(
        root / "tests" / "data" / "README.md",
        f"- the oracle notes quote {OLD_TOTAL} conformance checks of their own.\n",
    )
    return root


def _run(root: pathlib.Path, *args: str) -> int:
    return ccc.main([*args, "--root", str(root)])


def test_check_reports_every_stale_claim(
    corpus: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The read-only mode is the CI gate: it lists them all and exits 1."""
    assert _run(corpus) == 1
    errors = capsys.readouterr().err
    for quoted in (
        "README.md",
        "README_PYPI.md",
        "stub/README.md",
        "docs/start/getting-started.md",
        "site/src/content/docs/index.mdx",
        "site/src/content/docs/es/index.mdx",
        ".zenodo.json",
    ):
        assert quoted in errors
    assert f"claims {OLD_TOTAL} total, report says {TOTAL}" in errors
    assert f"claims {OLD_DOMAINS} domains, report says {DOMAINS}" in errors
    assert (
        f"claims {OLD_DESIGNATIONS} designations, report says {DESIGNATIONS}" in errors
    )
    assert f"claims {OLD_SOURCES} sources, report says {SOURCES}" in errors


def test_write_moves_every_quoted_count(
    corpus: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Every place that quotes a count is brought into line in one run."""
    assert _run(corpus, "--write") == 0
    assert "Rewrote" in capsys.readouterr().out

    for readme in ("README.md", "README_PYPI.md", "stub/README.md"):
        text = (corpus / readme).read_text(encoding="utf8")
        assert f"{TOTAL} conformance checks {SPLIT}" in text, (
            f"{readme} was not brought into line"
        )

    started = (corpus / "docs" / "start" / "getting-started.md").read_text(
        encoding="utf8"
    )
    assert f"all {TOTAL} checks" in started
    assert f"{TOTAL} numerical conformance checks {SPLIT}" in started

    english = (corpus / "site/src/content/docs/index.mdx").read_text(encoding="utf8")
    assert (
        f"{TOTAL} conformance checks against {DESIGNATIONS} normative designations "
        f"and {SOURCES} further published sources" in english
    )

    spanish = (corpus / "site/src/content/docs/es/index.mdx").read_text(encoding="utf8")
    assert (
        f"{TOTAL} comprobaciones de conformidad frente a {DESIGNATIONS} "
        f"designaciones normativas y {SOURCES} fuentes publicadas adicionales"
        in spanish
    )
    assert f"sobre {DOMAINS} dominios, frente a {DESIGNATIONS}" in spanish
    assert f"las {TOTAL} comprobaciones" in spanish

    zenodo = json.loads((corpus / ".zenodo.json").read_text(encoding="utf8"))
    assert f"{TOTAL} numerical conformance checks {SPLIT}" in zenodo["description"]

    # And the corpus now passes the read-only gate.
    assert _run(corpus) == 0


def test_write_leaves_the_decoys_alone(corpus: pathlib.Path) -> None:
    """A number that is not a conformance count is never touched.

    The decoys carry the stale counts in unrelated sentences: on their own
    lines, on the same line as a real claim, and as part of a standard's
    designation. A textual replace of the old value for the new one rewrites
    all of them.
    """
    assert _run(corpus, "--write") == 0

    started = (corpus / "docs" / "start" / "getting-started.md").read_text(
        encoding="utf8"
    )
    assert started.endswith(DECOY_LINES)
    assert f"one for each of the {OLD_TOTAL} rows of Annex {OLD_DOMAINS}." in started

    for readme in ("README.md", "stub/README.md"):
        assert (corpus / readme).read_text(encoding="utf8").endswith(DECOY_LINES)

    english = (corpus / "site/src/content/docs/index.mdx").read_text(encoding="utf8")
    assert f"measured over {OLD_DOMAINS} weeks" in english

    zenodo = json.loads((corpus / ".zenodo.json").read_text(encoding="utf8"))
    for designation in (
        f"ISO {OLD_DESIGNATIONS}-2",
        f"IEC 616{OLD_DOMAINS}-1",
        f"ITU-R BS.{OLD_TOTAL}",
    ):
        assert designation in zenodo["description"]


#: Sentences that count domains for a reason of their own, with the stale
#: count. The domain count is read only where the claim goes on to what it was
#: checked against, so the writer leaves every one of them as it is.
UNRELATED_DOMAINS = (
    f"The same signal is drawn across {OLD_DOMAINS} domains, time and frequency.\n"
    f"La misma señal se representa en {OLD_DOMAINS} dominios, tiempo y "
    "frecuencia.\n"
    f"El ruido se reparte sobre {OLD_DOMAINS} dominios distintos.\n"
)


def test_write_leaves_a_count_of_domains_for_another_reason_alone(
    corpus: pathlib.Path,
) -> None:
    """Only the claim's own "across N domains, against" is a count to move.

    A bare "across N domains" or "en N dominios" read every sentence that
    draws a signal in two domains as a stale claim, and ``--write`` set it to
    the report's count and passed.
    """
    page = corpus / "docs" / "signals" / "time-frequency.md"
    _write(page, UNRELATED_DOMAINS)
    assert _run(corpus, "--write") == 0
    assert page.read_text(encoding="utf8") == UNRELATED_DOMAINS
    assert _run(corpus) == 0


def test_a_count_of_domains_wrapped_in_plain_prose_is_no_wrapped_claim() -> None:
    """The wrapped reading is anchored to the claim as the line reading is."""
    assert (
        ccc.wrapped_in(
            f"a signal drawn across\n{OLD_DOMAINS} domains, time and frequency.\n"
        )
        == []
    )
    assert (
        ccc.wrapped_in(
            f"una señal sobre\n{OLD_DOMAINS} dominios, tiempo y frecuencia.\n"
        )
        == []
    )
    assert ccc.wrapped_in(
        f"checks across\n{OLD_DOMAINS} domains, against {DESIGNATIONS} normative designations"
    ) == [(1, f"across {OLD_DOMAINS} domains, against")]


def test_write_is_idempotent(corpus: pathlib.Path) -> None:
    """A second run changes nothing, byte for byte."""
    assert _run(corpus, "--write") == 0
    first = {p: p.read_bytes() for p in ccc.sources(corpus)}
    assert _run(corpus, "--write") == 0
    assert {p: p.read_bytes() for p in ccc.sources(corpus)} == first


def test_write_touches_only_the_files_that_quote_a_count(corpus: pathlib.Path) -> None:
    """Excluded and count-free files come out byte-identical.

    ``tests/data/README.md`` is in the list for the same reason the root
    markdown is globbed rather than walked: it describes something else, and
    this report says nothing about it.
    """
    untouched = [
        corpus / "CHANGELOG.md",
        corpus / "docs" / "ERRATA.md",
        corpus / "docs" / "superpowers" / "notes.md",
        corpus / "docs" / "conformance.json",
        corpus / "tests" / "data" / "README.md",
    ]
    before = {p: p.read_bytes() for p in untouched}
    assert _run(corpus, "--write") == 0
    assert {p: p.read_bytes() for p in untouched} == before


def test_a_crlf_file_stays_crlf(tmp_path: pathlib.Path) -> None:
    """The writer changes digits, not the file's line endings."""
    _write(tmp_path / "docs" / "conformance.json", REPORT)
    page = tmp_path / "docs" / "getting-started.md"
    _write(
        page,
        f"Intro paragraph.\r\nThe suite runs {OLD_TOTAL} conformance checks.\r\n",
    )
    assert _run(tmp_path, "--write") == 0
    assert (
        page.read_bytes()
        == (
            f"Intro paragraph.\r\nThe suite runs {TOTAL} conformance checks.\r\n"
        ).encode()
    )


def test_line_endings_and_surrounding_prose_are_preserved() -> None:
    """Only the digits move: indentation, quoting and CRLF stay put."""
    expected = {
        "total": TOTAL,
        "domains": DOMAINS,
        "designations": DESIGNATIONS,
        "sources": SOURCES,
    }
    line = (
        f'  description: "…; {OLD_TOTAL} conformance checks against '
        f'{OLD_DESIGNATIONS} normative designations."\r\n'
    )
    corrected, fixed = ccc.rewrite_line(line, expected)
    assert corrected == (
        f'  description: "…; {TOTAL} conformance checks against '
        f'{DESIGNATIONS} normative designations."\r\n'
    )
    assert [claim.field for claim in fixed] == ["total", "designations"]


def test_a_claim_read_two_ways_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """Two patterns that disagree about a number are a bug, not a coin toss."""
    import re

    monkeypatch.setattr(
        ccc,
        "CLAIMS",
        (
            (re.compile(r"(\d+)\s+conformance checks"), "total"),
            (re.compile(r"(\d+)\s+conformance checks"), "designations"),
        ),
    )
    with pytest.raises(ValueError, match="ambiguous conformance claim"):
        ccc.claims_in(f"the suite runs {OLD_TOTAL} conformance checks")


def test_an_ambiguous_pattern_pair_reports_instead_of_crashing(
    corpus: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The command exits 1 with the diagnostic, not with a traceback."""
    import re

    monkeypatch.setattr(
        ccc,
        "CLAIMS",
        (
            (re.compile(r"(\d+)\s+conformance checks"), "total"),
            (re.compile(r"(\d+)\s+conformance checks"), "designations"),
        ),
    )
    assert _run(corpus, "--write") == 1
    assert "ambiguous conformance claim" in capsys.readouterr().err


def test_an_unreadable_artefact_is_an_error(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A missing or broken artefact must fail loudly, not rewrite to nothing."""
    _write(tmp_path / "docs" / "conformance.json", "{ not json\n")
    assert _run(tmp_path, "--write") == 1
    assert "cannot read the conformance counts" in capsys.readouterr().err


def test_an_artefact_missing_a_count_names_the_field(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A schema change fails on the field, not on the sentence that used it."""
    _write(tmp_path / "docs" / "conformance.json", json.dumps({"counts": {}}) + "\n")
    assert _run(tmp_path, "--write") == 1
    assert "counts is missing checks" in capsys.readouterr().err


def test_an_artefact_without_the_citation_groups_names_the_field(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The refusal reads the citation groups apart from the claims, and needs them."""
    counts = json.loads(REPORT)["counts"]
    del counts["citation_groups"]
    _write(
        tmp_path / "docs" / "conformance.json", json.dumps({"counts": counts}) + "\n"
    )
    assert _run(tmp_path) == 1
    assert "counts is missing citation_groups" in capsys.readouterr().err


def test_counts_that_are_not_an_object_are_an_error(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A ``counts`` the artefact writes as anything but an object is refused."""
    _write(tmp_path / "docs" / "conformance.json", json.dumps({"counts": [1]}) + "\n")
    assert _run(tmp_path) == 1
    assert "counts is not an object" in capsys.readouterr().err


def test_the_real_corpus_needs_no_rewriting() -> None:
    """The committed tree is already consistent, so the writer is a no-op.

    This is the same property the CI gate asserts, checked without touching
    the working tree: every source file is rewritten in memory and must come
    back unchanged.
    """
    expected = ccc.expected_counts()
    for path in ccc.sources():
        text = path.read_text(encoding="utf8")
        corrected, fixed = ccc.rewrite_text(text, expected)
        assert not fixed, f"{path} quotes a stale count: {fixed}"
        assert corrected == text


# --------------------------------------------------------------------------
# A count of standards is refused, wherever it is published
# --------------------------------------------------------------------------

#: What the refusal names in place of a count of standards, in each language.
ENGLISH_SPLIT = (
    f"{DESIGNATIONS} normative designations and {SOURCES} further published sources"
)
SPANISH_SPLIT = (
    f"{DESIGNATIONS} designaciones normativas y {SOURCES} fuentes publicadas "
    "adicionales"
)


@pytest.mark.parametrize(
    ("relative", "text", "phrase", "replacement"),
    [
        pytest.param(
            "README.md",
            f"runs {TOTAL} conformance checks across {DOMAINS} domains and "
            f"{CITATION_GROUPS} standards, each pinning a value.\n",
            f"{CITATION_GROUPS} standards",
            ENGLISH_SPLIT,
            id="the README sentence it used to be",
        ),
        pytest.param(
            ".zenodo.json",
            json.dumps(
                {
                    "description": (
                        f"{TOTAL} numerical conformance checks across {DOMAINS} "
                        f"domains against {CITATION_GROUPS} IEC, ISO, EN, ANSI, "
                        "ITU-R and VDI standards, each pinning a clause."
                    )
                }
            )
            + "\n",
            f"{CITATION_GROUPS} IEC, ISO, EN, ANSI, ITU-R and VDI standards",
            ENGLISH_SPLIT,
            id="a list of bodies between the count and its noun",
        ),
        pytest.param(
            "docs/start/index.md",
            f"It runs {TOTAL} numerical conformance checks across {DOMAINS} "
            f"domains against {CITATION_GROUPS} referenced standards.\n",
            f"{CITATION_GROUPS} referenced standards",
            ENGLISH_SPLIT,
            id="a word that says how the standards were counted",
        ),
        pytest.param(
            "site/src/content/docs/es/index.mdx",
            f'description: "Kit: {TOTAL} comprobaciones de conformidad frente a '
            f'{CITATION_GROUPS} normas."\n',
            f"{CITATION_GROUPS} normas",
            SPANISH_SPLIT,
            id="the Spanish landing description",
        ),
        pytest.param(
            "docs/start/why-phonometry.md",
            f"today the suite runs {TOTAL} numerical conformance checks across\n"
            f"{DOMAINS} domains and {CITATION_GROUPS}\nstandards, covering "
            "psychoacoustics.\n",
            f"{CITATION_GROUPS} standards",
            ENGLISH_SPLIT,
            id="a count wrapped away from its noun",
        ),
        pytest.param(
            "docs/CONFORMANCE.md",
            f"**{TOTAL}/{TOTAL} conformance checks pass** across {DOMAINS} "
            f"domains and {CITATION_GROUPS} standards - filters class 1.\n",
            f"{CITATION_GROUPS} standards",
            ENGLISH_SPLIT,
            id="the generated report, which the writer leaves alone",
        ),
        pytest.param(
            "llms.txt",
            f"> Acoustics, with {TOTAL} numerical conformance checks against "
            f"{CITATION_GROUPS} standards enforced in CI.\n",
            f"{CITATION_GROUPS} standards",
            ENGLISH_SPLIT,
            id="the agent file",
        ),
        pytest.param(
            ".github/badges/conformance-summary.svg",
            f'<svg aria-label="All {TOTAL} conformance checks pass, across '
            f'{DOMAINS} domains and {CITATION_GROUPS} standards"/>\n',
            f"{CITATION_GROUPS} standards",
            ENGLISH_SPLIT,
            id="the banner's words",
        ),
        pytest.param(
            "README.md",
            f"runs {TOTAL} conformance checks across {DOMAINS} domains and "
            f"**{CITATION_GROUPS}** standards, each pinning a value.\n",
            f"{CITATION_GROUPS} standards",
            ENGLISH_SPLIT,
            id="a count in bold",
        ),
        pytest.param(
            ".zenodo.json",
            json.dumps(
                {
                    "description": (
                        f"<p>{TOTAL} conformance checks against "
                        f"<strong>{CITATION_GROUPS}</strong> standards.</p>"
                    )
                }
            )
            + "\n",
            f"{CITATION_GROUPS} standards",
            ENGLISH_SPLIT,
            id="a count in an HTML tag",
        ),
        pytest.param(
            "README.md",
            f"runs {TOTAL} conformance checks across {DOMAINS} domains and "
            f"{CITATION_GROUPS} published standards, each pinning a value.\n",
            f"{CITATION_GROUPS} published standards",
            ENGLISH_SPLIT,
            id="a word that says what kind of standard",
        ),
        pytest.param(
            "docs/start/index.md",
            f"# {TOTAL} Conformance Checks against {CITATION_GROUPS} International "
            "Standards\n",
            f"{CITATION_GROUPS} International Standards",
            ENGLISH_SPLIT,
            id="a noun with a capital",
        ),
        pytest.param(
            ".zenodo.json",
            json.dumps(
                {
                    "description": (
                        f"<p>{TOTAL} conformance checks against "
                        f"{CITATION_GROUPS}&nbsp;standards.</p>"
                    )
                }
            )
            + "\n",
            f"{CITATION_GROUPS} standards",
            ENGLISH_SPLIT,
            id="an HTML no-break space",
        ),
        pytest.param(
            "docs/start/index.md",
            f"It runs {TOTAL} conformance checks against {CITATION_GROUPS}"
            "\u00a0standards.\n",
            f"{CITATION_GROUPS} standards",
            ENGLISH_SPLIT,
            id="a no-break space",
        ),
        pytest.param(
            "docs/start/index.md",
            f"Every value is verified against {CITATION_GROUPS} standards.\n",
            f"{CITATION_GROUPS} standards",
            ENGLISH_SPLIT,
            id="the citation-group figure with no conformance wording",
        ),
        pytest.param(
            "site/src/content/docs/es/index.mdx",
            f"Cada valor se verifica frente a {CITATION_GROUPS} Normas.\n",
            f"{CITATION_GROUPS} Normas",
            SPANISH_SPLIT,
            id="the citation-group figure in Spanish, with a capital",
        ),
    ],
)
def test_a_count_of_standards_is_refused_with_the_wording_that_replaces_it(
    corpus: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    relative: str,
    text: str,
    phrase: str,
    replacement: str,
) -> None:
    """The published figure counted citation groups, and it cannot come back.

    A citation group is the citation string up to its first colon or
    " Annex", so a book cited at seven clauses was seven standards: the
    project published 523 of them while its citations named 227 normative
    designations and 125 further published sources. No rewrite of digits
    mends the wording, so the writer fails on it too.
    """
    assert _run(corpus, "--write") == 0
    capsys.readouterr()
    _write(corpus / relative, text)
    for args in ((), ("--write",)):
        assert _run(corpus, *args) == 1
        errors = capsys.readouterr().err
        assert f"{relative}:" in errors
        assert f"counts standards in {phrase!r}" in errors
        assert repr(replacement) in errors


@pytest.mark.parametrize(
    "text",
    [
        pytest.param(
            "The ISO 3740 series has 7 standards for the sound power of a machine.\n",
            id="a count of standards for another reason",
        ),
        pytest.param(
            f"The suite runs {TOTAL} conformance checks. Twice the Table 1 "
            "standard deviation bounds the result.\n",
            id="the singular in a conformance sentence",
        ),
        pytest.param(
            "### La regla de conformidad del IEC TC 29\n\n"
            "Las normas de instrumentos de la IEC escritas desde 2013.\n",
            id="a heading that ends in a number, then a paragraph",
        ),
        pytest.param(
            "Every value is verified against 7 standards.\n",
            id="another count of standards with no conformance wording",
        ),
    ],
)
def test_a_sentence_that_counts_no_conformance_claim_is_left_alone(
    corpus: pathlib.Path, text: str
) -> None:
    """The refusal reads a count of standards only beside conformance wording."""
    assert _run(corpus, "--write") == 0
    _write(corpus / "docs" / "guide.md", text)
    assert ccc.refused_in(text) == []
    assert _run(corpus) == 0


def test_the_changelog_keeps_its_history(corpus: pathlib.Path) -> None:
    """The changelog says what was published, the old count of standards too."""
    assert _run(corpus, "--write") == 0
    changelog = (corpus / "CHANGELOG.md").read_text(encoding="utf8")
    assert f"{CITATION_GROUPS} standards" in changelog
    assert _run(corpus) == 0


def test_a_claim_wrapped_away_from_its_noun_is_reported(
    corpus: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The check reads a claim line by line, so a wrapped one would go unread.

    It would then go stale as silently as a count typed by hand, which is the
    defect the whole script exists to end.
    """
    assert _run(corpus, "--write") == 0
    capsys.readouterr()
    _write(
        corpus / "docs" / "start" / "why-phonometry.md",
        f"The suite runs {OLD_TOTAL} conformance checks across {DOMAINS} "
        f"domains, against {DESIGNATIONS} normative\ndesignations and "
        f"{SOURCES} further published sources.\n",
    )
    assert _run(corpus) == 1
    errors = capsys.readouterr().err
    assert "docs/start/why-phonometry.md:1:" in errors
    assert f"'{DESIGNATIONS} normative designations' wraps a count" in errors


def test_the_real_corpus_counts_no_standards() -> None:
    """Nothing the project publishes states a count of standards, or wraps one."""
    assert ccc.refusals(ccc.ROOT, ccc.expected_counts()) == []
    assert ccc.wrapped(ccc.ROOT) == []


def test_markup_moves_no_line() -> None:
    """The refusal reads through markup and still names the line of the file.

    Markup is deleted and every hard space read as one space, and no line
    break goes with either, so the line reported is the line to edit.
    """
    text = (
        "A **bold** word and a `code` span.\n"
        "Two&nbsp;words, <em>one</em> tag.\n"
        f"It runs {TOTAL} conformance checks against **{CITATION_GROUPS}**&nbsp;"
        "Standards.\n"
    )
    assert ccc.refused_in(text, CITATION_GROUPS) == [
        (3, f"{CITATION_GROUPS} Standards", ccc.FORBIDDEN[0][1])
    ]


def test_the_citation_group_figure_is_found_in_any_sentence() -> None:
    """:func:`figures_in` is the half of the refusal that needs no wording."""
    text = (
        f"The ISO 3740 series has 7 standards.\nVerified against "
        f"{CITATION_GROUPS}\nstandards.\n"
    )
    assert ccc.figures_in(text, {CITATION_GROUPS}) == [
        (2, f"{CITATION_GROUPS} standards")
    ]
    assert ccc.refused_in(text) == []
    assert ccc.refused_in(text, CITATION_GROUPS) == [
        (2, f"{CITATION_GROUPS} standards", ccc.FORBIDDEN[0][1])
    ]


#: The figure every surface gave as its count of standards up to 4.0.0rc1, the
#: citation groups of the report of that day.
RETIRED_FIGURE = 523


def test_the_retired_figure_is_published_nowhere() -> None:
    """The release gate: no tracked file states the figure as a count of standards.

    PyPI freezes the 4.0.0 long description at upload, and its badge and
    report links are pinned to the tag, so the figure is looked for over every
    tracked file and not only over the files the refusal reads, through the
    same markup and hard spaces, in any sentence. The figure is the retired
    one and the report's citation groups of today, the same number until a
    citation moves it.
    """
    listed = child_process.run(
        ["git", "-C", str(ccc.ROOT), "ls-files", "-z"],
        capture_output=True,
        check=True,
        timeout=120,
    )
    figures = {RETIRED_FIGURE, ccc.citation_groups()}
    found: list[str] = []
    for name in listed.stdout.decode("utf8").split("\0"):
        path = ccc.ROOT / name
        if not name or not path.is_file():
            continue
        data = path.read_bytes()
        if b"\0" in data:
            continue
        text = data.decode("utf8", errors="replace")
        found += [
            f"{name}:{lineno}: {phrase}"
            for lineno, phrase in ccc.figures_in(text, figures)
        ]
    assert found == []
