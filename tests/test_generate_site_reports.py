#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The parity gate between the errata registry and its Spanish edition.

``scripts/generate_site_reports.py`` refuses to render while
``docs/ERRATA.es.md`` drifts from ``docs/ERRATA.md``: same number of ``##``
entries, same order, and each pair of headings naming the same source
document through its first designation token. These tests pin the three
failure modes, the pass, and the one blind spot the token deliberately
accepts.
"""

from __future__ import annotations

import dataclasses
import functools
import hashlib
import pathlib
import sys

import pytest
import yaml

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import generate_site_reports

_ENGLISH = """## ISO 717-2:2020, Annex C, example C.1 (bare floor)

body

## Commission Directive (EU) 2015/996, Annex II 2.2.1 (road source)

body

## IEC 60268-16:2011, Table M.1 (the beta row)

body

## IEC 60268-16:2011, Table M.1 (step 3 at 250 Hz)

body
"""

_SPANISH = """## ISO 717-2:2020, Anexo C, ejemplo C.1 (suelo desnudo)

cuerpo

## Directiva (UE) 2015/996 de la Comisión, Anexo II 2.2.1 (fuente de carretera)

cuerpo

## IEC 60268-16:2011, Table M.1 (la fila beta)

cuerpo

## IEC 60268-16:2011, Table M.1 (paso 3 a 250 Hz)

cuerpo
"""


def _editions(
    tmp_path: pathlib.Path, english: str, spanish: str
) -> tuple[pathlib.Path, pathlib.Path]:
    en = tmp_path / "ERRATA.md"
    es = tmp_path / "ERRATA.es.md"
    en.write_text(english, encoding="utf8")
    es.write_text(spanish, encoding="utf8")
    return en, es


def test_matching_editions_pass(tmp_path: pathlib.Path) -> None:
    """Same count, same order, same designations: no complaint."""
    en, es = _editions(tmp_path, _ENGLISH, _SPANISH)
    generate_site_reports.check_edition_parity(en, es)


def test_a_missing_entry_fails_with_both_counts(tmp_path: pathlib.Path) -> None:
    """Dropping one Spanish entry names both counts in the refusal."""
    short = _SPANISH.replace(
        "## Directiva (UE) 2015/996 de la Comisión, Anexo II 2.2.1 "
        "(fuente de carretera)\n\ncuerpo\n\n",
        "",
    )
    en, es = _editions(tmp_path, _ENGLISH, short)
    with pytest.raises(SystemExit, match="3 entries against 4"):
        generate_site_reports.check_edition_parity(en, es)


def test_a_reordered_entry_fails_at_its_index(tmp_path: pathlib.Path) -> None:
    """Swapping entries about different documents is caught positionally."""
    swapped = _SPANISH.replace(
        "## ISO 717-2:2020, Anexo C, ejemplo C.1 (suelo desnudo)",
        "## MARK",
    ).replace(
        "## Directiva (UE) 2015/996 de la Comisión, Anexo II 2.2.1 "
        "(fuente de carretera)",
        "## ISO 717-2:2020, Anexo C, ejemplo C.1 (suelo desnudo)",
    )
    swapped = swapped.replace(
        "## MARK",
        "## Directiva (UE) 2015/996 de la Comisión, Anexo II 2.2.1 "
        "(fuente de carretera)",
    )
    en, es = _editions(tmp_path, _ENGLISH, swapped)
    with pytest.raises(SystemExit, match="entry 1 names '2015/996'"):
        generate_site_reports.check_edition_parity(en, es)


def test_a_mistranslated_designation_fails(tmp_path: pathlib.Path) -> None:
    """A digit slipping in a designation is a mistranslation, not a variant."""
    wrong = _SPANISH.replace("ISO 717-2:2020, Anexo", "ISO 717-3:2020, Anexo")
    en, es = _editions(tmp_path, _ENGLISH, wrong)
    with pytest.raises(SystemExit, match="'717-3:2020' where"):
        generate_site_reports.check_edition_parity(en, es)


def test_translated_issuer_words_do_not_fail_the_pair(
    tmp_path: pathlib.Path,
) -> None:
    """The issuer word moves and translates; the token must not require it.

    "Commission Directive (EU) 2015/996" pairs with "Directiva (UE) 2015/996
    de la Comisión": nothing about the issuer survives translation verbatim,
    which is why the token starts at the first digit-bearing word.
    """
    en, es = _editions(tmp_path, _ENGLISH, _SPANISH)
    generate_site_reports.check_edition_parity(en, es)


def test_the_accepted_blind_spot_is_within_one_document(
    tmp_path: pathlib.Path,
) -> None:
    """Swapping two entries of the same document passes, and may.

    The two IEC 60268-16:2011 Table M.1 entries share their designation
    token, so exchanging them is invisible to the gate. That is the accepted
    residual: both headings still name the source they describe, so no
    heading is paired with the wrong document; only the entry order within
    one document's run would be off, which the translation review reads, not
    this gate.
    """
    swapped = _SPANISH.replace(
        "## IEC 60268-16:2011, Table M.1 (la fila beta)", "## MARK"
    ).replace(
        "## IEC 60268-16:2011, Table M.1 (paso 3 a 250 Hz)",
        "## IEC 60268-16:2011, Table M.1 (la fila beta)",
    )
    swapped = swapped.replace(
        "## MARK", "## IEC 60268-16:2011, Table M.1 (paso 3 a 250 Hz)"
    )
    en, es = _editions(tmp_path, _ENGLISH, swapped)
    generate_site_reports.check_edition_parity(en, es)


def test_the_shipped_editions_pass_the_gate() -> None:
    """The committed registry and its Spanish edition satisfy the invariants."""
    root = pathlib.Path(generate_site_reports.__file__).resolve().parent.parent
    generate_site_reports.check_edition_parity(
        root / "docs" / "ERRATA.md", root / "docs" / "ERRATA.es.md"
    )


# ---------------------------------------------------------------------------
# One page per document family.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("heading", "slug", "name"),
    [
        ("ISO 3743-2:2018, 3.1 (the designation)", "iso-3743", "ISO 3743"),
        ("UNE-EN ISO 9614-1:2010, clause 9.1 (a sign)", "iso-9614", "ISO 9614"),
        ("ISO/TS 12913-3:2019, Formula (A.3) (a factor)", "iso-12913", "ISO/TS 12913"),
        ("IEC TS 61400-11-2:2024, Table 7 (a row)", "iec-61400", "IEC TS 61400"),
        ("E DIN 4150-2:2023-08, 6.3 (a rare event)", "din-4150", "DIN 4150"),
        ("ECMA-418-1:2024 (3rd edition), clause 4.1.1", "ecma-418", "ECMA-418"),
        ("ITU-R BS.468-4, Table 2, 5 ms upper limit", "itu-r-bs-468", "ITU-R BS.468"),
        ("ANSI S3.5-1997, Annex C worked examples", "ansi-s3-5", "ANSI S3.5"),
        ("VDI 2081 Blatt 2:2005-05, Table 1, element 2", "vdi-2081", "VDI 2081"),
        ("EN 12354-3:2000, Formula (5) (reduced form)", "iso-12354", "EN 12354"),
        ("EN 61260:1995, 3.2, NOTE 3 (base two)", "iec-61260", "EN 61260"),
        ("UNE-EN 61094-5:2017, Table D.1 (six values)", "iec-61094", "EN 61094"),
        ("EN 1793-5:2016, Formula (1) against Formula (4)", "en-1793", "EN 1793"),
        # Spellings no shipped heading opens with yet, each read as the series
        # it belongs to rather than stopping the run or landing among the books.
        ("DIN EN ISO 717-1:2021, Annex A (a term)", "iso-717", "ISO 717"),
        ("DIN ISO 9613-2:1999, 7.3 (a ground factor)", "iso-9613", "ISO 9613"),
        ("DIN EN 61260:1996, 4.2 (a band edge)", "iec-61260", "EN 61260"),
        ("DIN 4150-3:1999-02, Table 1 (a guide value)", "din-4150", "DIN 4150"),
        ("ANSI/ASA S1.11-2014, Table 1 (a class)", "ansi-s1-11", "ANSI/ASA S1.11"),
        ("IEC TR 61094-7:2006, Figure 3 (a correction)", "iec-61094", "IEC TR 61094"),
        ("CEN/TS 1793-5:2003, 4.1 (a window)", "en-1793", "CEN/TS 1793"),
    ],
)
def test_a_standard_lands_on_its_series_page(
    heading: str, slug: str, name: str
) -> None:
    """The designation a heading opens with names the page, adoptions folded in.

    A national adoption (``UNE-EN ISO``), a draft (``E DIN``) and a technical
    specification (``ISO/TS``) are the same series as the standard they
    adopt, draft or specify; EN 12354, EN 61260 and EN 61094 are the European
    line of the ISO and IEC series and share their page (``ALIASES``).
    """
    family = generate_site_reports.family_of(heading)
    assert (family.slug, family.group, family.name_en) == (slug, "standards", name)


@pytest.mark.parametrize(
    ("heading", "slug"),
    [
        ("Long, Architectural Acoustics 2e (2014), Eq. (18.24) (sign)", "long"),
        ("Allard & Atalla 2e (2009), Sect. 6.6.3 (thickness)", "allard-atalla"),
        (
            "Commission Directive (EU) 2015/996, Annex II 2.2.1 (range)",
            "directive-eu-2015-996",
        ),
        ("Directive (EU) 2015/996, Appendix G, band labels", "directive-eu-2015-996"),
        ("ICAO Annex 16, Volume I, 8th edition (2017), Appendix 2", "icao-annex-16"),
    ],
)
def test_any_other_source_lands_on_its_listed_page(heading: str, slug: str) -> None:
    """A book, a paper or a regulation goes to the page its SOURCES row names."""
    family = generate_site_reports.family_of(heading)
    assert (family.slug, family.group) == (slug, "other")


def test_an_unknown_source_stops_the_run_and_asks_for_a_row() -> None:
    """A heading naming neither a designation nor a listed source fails loudly.

    Guessing a page for it would publish a URL nobody chose, and a URL is
    never renamed once published.
    """
    with pytest.raises(SystemExit, match="Add a row to SOURCES"):
        generate_site_reports.family_of("Smith (2030), Table 1 (a new book)")


@pytest.mark.parametrize(
    "heading",
    ["ISO/IEC 17025:2017, 7.2 (a requirement)", "ASTM C423-17, 9.1 (a formula)"],
)
def test_an_unread_designation_asks_for_the_expression_not_a_row(heading: str) -> None:
    """A standard the expression does not read is not filed among the books.

    A row in SOURCES would put it under "Guidance, regulations, books and
    papers", so the run says to teach ``_DESIGNATION`` its prefix instead.
    """
    with pytest.raises(SystemExit, match="Teach _DESIGNATION its prefix"):
        generate_site_reports.family_of(heading)


def test_the_properties_that_are_not_errata_get_their_own_page() -> None:
    """The registry's closing list is not an entry of any family."""
    family = generate_site_reports.family_of(generate_site_reports.NOT_ERRATA_HEADING)
    assert (family.slug, family.group) == ("not-errata", "not-errata")


def test_editions_list_each_printed_edition_once() -> None:
    """A designation written bare beside its dated form is listed once, dated.

    The other family's designation in a parenthesis is not this page's.
    """
    headings = [
        "IEC 60268-1:1985, Appendix A, Figure A1 (a capacitor)",
        "IEC 60268-7:2010, 8.3.4.2 NOTE 1 (a crest factor credited to IEC 60268-1)",
        "IEC 60268-7:2010, Table 1 (six clause numbers credited to ISO 3744)",
    ]
    (page,) = generate_site_reports.plan_families(headings)
    assert page.family.slug == "iec-60268"
    assert page.editions == ("IEC 60268-1:1985", "IEC 60268-7:2010")
    assert page.positions == (0, 1, 2)


def test_families_are_ordered_standards_first_then_by_number() -> None:
    """Standards by issuer and number, other sources after them, the list last."""
    headings = [
        "Rossing (2014), Table 6.5 (a spelling)",
        generate_site_reports.NOT_ERRATA_HEADING,
        "ISO 12999-1:2020, Table 4 (missing row)",
        "IEC 61063:1991, 8.3 (a symbol)",
        "ISO 717-2:2020, Annex C, example C.1 (bare floor)",
        "Bies 5e (2017), Table C.1 (three speeds)",
    ]
    slugs = [page.family.slug for page in generate_site_reports.plan_families(headings)]
    assert slugs == [
        "iso-717",
        "iso-12999",
        "iec-61063",
        "bies-hansen-howard",
        "rossing",
        "not-errata",
    ]


def test_spanish_names_take_their_article_and_conjunction() -> None:
    """A regulation reads "del"/"de la" in Spanish, and ISO is joined by "e"."""
    pages = generate_site_reports.plan_families(
        [
            "ICAO Annex 16, Volume I, 8th edition (2017), Appendix 2",
            "Directive (EU) 2015/996, Annex II 2.3.2 (roughness)",
            "ISO 3743-1:2010, Table 3 (a range)",
            "ISO 3743-2:2018, 3.1 (the designation)",
        ]
    )
    titles = {
        page.family.slug: generate_site_reports.page_title(page, "es") for page in pages
    }
    assert titles == {
        "iso-3743": "Erratas de ISO 3743",
        "directive-eu-2015-996": "Erratas de la Directiva (UE) 2015/996",
        "icao-annex-16": "Erratas del Anexo 16 de la OACI",
    }
    iso = next(page for page in pages if page.family.slug == "iso-3743")
    assert "ISO 3743-1:2010 e ISO 3743-2:2018" in generate_site_reports.page_intro(
        iso, "es"
    )
    assert "ISO 3743-1:2010 and ISO 3743-2:2018" in generate_site_reports.page_intro(
        iso, "en"
    )


def test_a_family_of_two_series_is_named_with_the_spanish_conjunction() -> None:
    """Spanish joins a second series that starts with /i/ with "e", not "y"."""
    (page,) = generate_site_reports.plan_families(
        ["ISO/PAS 1996-3:2022, Clause 5 (a range)", "ISO 1996-2:2017, Annex A (a term)"]
    )
    assert page.name("en") == "ISO 1996 and ISO/PAS 1996"
    assert page.name("es") == "ISO 1996 e ISO/PAS 1996"
    assert (
        generate_site_reports.page_title(page, "es")
        == "Erratas de ISO 1996 e ISO/PAS 1996"
    )


def test_every_shipped_page_fits_the_site_limits() -> None:
    """Every title and description the registry produces is one the site keeps.

    Titles at most 57 characters, descriptions at most 155 and unique in their
    language, which is what the site's description check holds every page to.
    """
    registry = generate_site_reports.read_registry(generate_site_reports.EDITIONS[0])
    pages = generate_site_reports.plan_families(
        [heading for heading, _ in registry.entries]
    )
    generate_site_reports.check_page_metadata(pages)
    for lang in ("en", "es"):
        descriptions = [
            generate_site_reports.page_description(page, lang) for page in pages
        ]
        titles = [generate_site_reports.page_title(page, lang) for page in pages]
        assert len(set(descriptions)) == len(descriptions)
        assert len(set(titles)) == len(titles)


def test_every_entry_lands_on_exactly_one_page_in_both_languages() -> None:
    """Nothing is dropped or duplicated by the split, in either edition."""
    pages = generate_site_reports.rendered_pages()
    for edition in generate_site_reports.EDITIONS:
        registry = generate_site_reports.read_registry(edition)
        folder = generate_site_reports.CONTENT / edition.folder
        family_texts = [
            text
            for path, text in pages.items()
            if path.parent == folder and path.suffix == ".md"
        ]
        published = [
            line[3:].strip()
            for text in family_texts
            for line in text.splitlines()
            if line.startswith("## ")
        ]
        assert sorted(published) == sorted(heading for heading, _ in registry.entries)


@pytest.mark.whole_tree
def test_the_committed_pages_are_up_to_date() -> None:
    """The pages in the tree are what the generator writes now, none stale."""
    assert generate_site_reports.main(["--check"]) == 0


def test_the_index_is_mdx_safe_or_the_run_stops(tmp_path: pathlib.Path) -> None:
    """A brace in the registry's introduction would be read as code by MDX."""
    with pytest.raises(SystemExit, match="MDX would read as code"):
        generate_site_reports._mdx_safe("a set {1, 2} in prose\n", where="test")
    assert generate_site_reports._mdx_safe("a set `{1, 2}` in code\n", where="test")


def test_a_page_the_generator_no_longer_writes_is_deleted(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A family that lost its last entry loses its page; a hand page stays."""
    folder = tmp_path / "reference" / "errata"
    folder.mkdir(parents=True)
    generated = folder / "gone.md"
    generated.write_text(
        "<!-- Generated from docs/ERRATA.md by ... -->\n", encoding="utf8"
    )
    by_hand = folder / "notes.md"
    by_hand.write_text("written by hand\n", encoding="utf8")
    kept = folder / "kept.md"
    kept.write_text("<!-- Generated from docs/ERRATA.md by ... -->\n", encoding="utf8")
    monkeypatch.setattr(generate_site_reports, "CONTENT", tmp_path)
    assert generate_site_reports.stale_pages([kept]) == [generated]


def test_a_family_page_is_ranked_by_no_title_and_shown_by_its_own() -> None:
    """A page about one document is ranked by an empty title, not its own.

    Its title is the document's designation with the register's word, and the
    site search weights a title five times; ranked by it, the page would
    outrank the guides written to the document, and the registry's index on a
    search for the registry. The page of properties that are not errata names
    no document, keeps its own title and is indexed at a lower weight instead.
    """
    pages = generate_site_reports.plan_families(
        [
            "VDI 2081 Blatt 2:2005-05, Table 1, element 2",
            generate_site_reports.NOT_ERRATA_HEADING,
        ]
    )
    by_slug = {page.family.slug: page for page in pages}
    vdi, plain = by_slug["vdi-2081"], by_slug["not-errata"]
    assert generate_site_reports.search_title(vdi) == ""
    assert generate_site_reports.search_title(plain) is None
    assert generate_site_reports.search_weight(vdi) is None
    assert (
        generate_site_reports.search_weight(plain)
        == generate_site_reports.SEARCH_WEIGHT
    )
    edition = generate_site_reports.EDITIONS[0]
    registry = generate_site_reports.Registry(
        preamble="",
        entries=(
            ("VDI 2081 Blatt 2:2005-05, Table 1, element 2", "## VDI ...\n\nText."),
            (generate_site_reports.NOT_ERRATA_HEADING, "## Related ...\n\nText."),
        ),
    )
    frontmatter = generate_site_reports.render_family(vdi, edition, registry).split(
        "---"
    )[1]
    assert 'title: "Errata in VDI 2081"\n' in frontmatter
    assert 'searchTitle: ""\n' in frontmatter
    assert "searchWeight" not in frontmatter
    plain_frontmatter = generate_site_reports.render_family(
        plain, edition, registry
    ).split("---")[1]
    assert "searchTitle" not in plain_frontmatter
    assert f"searchWeight: {generate_site_reports.SEARCH_WEIGHT}\n" in plain_frontmatter


def test_an_escaped_backtick_hides_no_brace_from_the_mdx_check() -> None:
    """The index page is MDX, which reads a brace in prose as code.

    The check took every backtick for a code marker, so a brace between two
    escaped backticks, which the page shows as prose, passed it and broke
    the page it is written into.
    """
    with pytest.raises(SystemExit, match="carries a brace"):
        generate_site_reports._mdx_safe(r"An escaped \`{x}\` brace.", where="t")
    with pytest.raises(SystemExit, match="carries a brace"):
        generate_site_reports._mdx_safe("A bare {x} brace.", where="t")
    kept = "A `{x}` in code and ``a ` {b}`` in a longer run."
    assert generate_site_reports._mdx_safe(kept, where="t") == kept


def test_a_brace_in_a_code_span_across_a_line_break_is_code() -> None:
    """A code span runs over the lines of its paragraph, braces and all.

    The spans were dropped one line at a time, so a brace in a span that
    crossed a line break stopped the run as a brace of prose.
    """
    text = "A set `{1,\n2}` in code.\n"
    assert generate_site_reports._mdx_safe(text, where="t") == text


def test_an_empty_introduction_is_mdx_safe() -> None:
    """An empty text read as one empty line against no lines, and the zip of
    the two raised a ``ValueError`` where nothing is unsafe.
    """
    assert generate_site_reports._mdx_safe("", where="test") == ""


# ---------------------------------------------------------------------------
# The index: its own introduction, then what only the registry's says.
# ---------------------------------------------------------------------------


def _index_text(lang: str) -> str:
    """The index page of one language as the generator writes it, as a reader reads it."""
    edition = next(e for e in generate_site_reports.EDITIONS if e.lang == lang)
    pages = generate_site_reports.rendered_pages()
    text = pages[generate_site_reports.CONTENT / edition.index]
    return " ".join(text.replace("*", "").split()).lower()


@pytest.mark.parametrize(
    ("lang", "claim"),
    [
        ("en", "a defect of the method"),
        ("en", "clean-room"),
        ("en", "covers every kind of published source"),
        ("en", "the authoritative one"),
        ("en", "same entries in the same order"),
        ("es", "un defecto del método"),
        ("es", "sala limpia"),
        ("es", "todos los tipos de fuente publicada"),
        ("es", "la redacción autoritativa es la inglesa"),
        ("es", "mismas entradas"),
    ],
)
def test_the_index_says_each_thing_of_its_introduction_once(
    lang: str, claim: str
) -> None:
    """The index's introduction and the registry's are not printed one after the other.

    Both used to be: the index opened with its own introduction, written for
    the site, and the generator transplanted the registry's below it, so the
    page said twice that the registry comes from a clean-room implementation
    and that a defect listed is not a defect of the method, and the Spanish
    page twice that the English wording is the authoritative one and that the
    two editions hold the same entries in the same order.
    """
    assert _index_text(lang).count(claim) == 1


def test_the_index_keeps_what_only_the_registry_says() -> None:
    """The status legend and the evidence rule, which every family page points to."""
    english, spanish = _index_text("en"), _index_text("es")
    assert "status legend: unreported" in english
    assert "verified against the page as printed" in english
    assert "a spanish edition of this registry" in english
    assert "leyenda de estados: sin notificar" in spanish
    assert "contra la página tal como está impresa" in spanish


def _edition(
    said: tuple[generate_site_reports.SaidOnIndex, ...],
) -> generate_site_reports.Edition:
    return generate_site_reports.Edition(
        lang="en",
        source=generate_site_reports.DOCS / "ERRATA.md",
        start=generate_site_reports.EDITIONS[0].start,
        said_on_index=said,
    )


_PREAMBLE = generate_site_reports.Registry(
    preamble=(
        "The registry records each case.\nIt is long.\n\n"
        "Status legend: unreported.\n\n"
        "A new paragraph nobody listed."
    ),
    entries=(),
)

#: The first paragraph of :data:`_PREAMBLE` as a reader sees it, hashed here
#: rather than by the function under test.
_PINNED = hashlib.sha256(b"The registry records each case. It is long.").hexdigest()


def _said(
    opening: str = "The registry records",
    digest: str = _PINNED,
    words: str = "records each case",
) -> generate_site_reports.SaidOnIndex:
    return generate_site_reports.SaidOnIndex(opening, digest, words)


def test_only_a_paragraph_the_index_says_is_left_out() -> None:
    """A paragraph is left out while the index says it; one added later is kept."""
    kept = generate_site_reports.index_preamble(
        _edition((_said(),)), _PREAMBLE, "The index\nrecords each case, wrapped."
    )
    assert kept == "Status legend: unreported.\n\nA new paragraph nobody listed."


def test_a_paragraph_rewrapped_still_reads_as_pinned() -> None:
    """The digest is of the words, so wrapping the lines otherwise changes nothing."""
    rewrapped = dataclasses.replace(
        _PREAMBLE,
        preamble=_PREAMBLE.preamble.replace("case.\nIt is", "case. It\nis"),
    )
    kept = generate_site_reports.index_preamble(
        _edition((_said(),)), rewrapped, "records each case"
    )
    assert kept.startswith("Status legend")


def test_a_paragraph_listed_by_words_it_no_longer_opens_with_stops_the_run() -> None:
    """A reworded paragraph would be transplanted again in silence."""
    edition = _edition((_said(opening="The register records"),))
    with pytest.raises(SystemExit, match="no paragraph of the registry's introduction"):
        generate_site_reports.index_preamble(edition, _PREAMBLE, "records each case")


def test_a_paragraph_the_index_no_longer_says_stops_the_run() -> None:
    """Left out while the index said it, the paragraph would be said nowhere."""
    edition = _edition((_said(),))
    with pytest.raises(SystemExit, match="no longer says 'records each case'"):
        generate_site_reports.index_preamble(edition, _PREAMBLE, "says something else")


def test_an_edit_inside_a_paragraph_left_out_stops_the_run() -> None:
    """An edit to a paragraph the index leaves out would reach no page.

    The paragraph still opens with the words it is listed by, and the index
    still says them, so neither of the other two stops would fire: a rule
    added to the registry's introduction would stay on GitHub, and the site's
    introduction would disagree with it without anything saying so.
    """
    edited = dataclasses.replace(
        _PREAMBLE,
        preamble=_PREAMBLE.preamble.replace(
            "It is long.",
            "It is long. A NEW RULE: every entry is reported within 30 days.",
        ),
    )
    edition = _edition((_said(),))
    with pytest.raises(
        SystemExit,
        match=r"opening 'The registry records' changed\..*index\.mdx says it in its own words",
    ):
        generate_site_reports.index_preamble(edition, edited, "records each case")


@pytest.mark.parametrize(
    "edition", generate_site_reports.EDITIONS, ids=lambda e: e.lang
)
def test_every_paragraph_left_out_is_pinned_as_the_registry_reads(
    edition: generate_site_reports.Edition,
) -> None:
    """Each paragraph the index leaves out is the registry's paragraph, word for word.

    Three in English and four in Spanish: the clean-room paragraph, what the
    registry covers and what an entry describes, and in Spanish the note that
    the English wording is the authoritative one.
    """
    registry = generate_site_reports.read_registry(edition)
    paragraphs = [
        " ".join(part.split()) for part in registry.preamble.split("\n\n") if part
    ]
    assert len(edition.said_on_index) == {"en": 3, "es": 4}[edition.lang]
    for item in edition.said_on_index:
        (paragraph,) = [text for text in paragraphs if text.startswith(item.opening)]
        assert hashlib.sha256(paragraph.encode()).hexdigest() == item.digest


# ---------------------------------------------------------------------------
# The works a family corrects, in the site's bibliography.
# ---------------------------------------------------------------------------


def _iso(designation: str) -> dict[str, object]:
    return {
        "type": "standard",
        "organization": "International Organization for Standardization",
        "designation": designation,
        "title": f"Title of {designation}",
    }


@pytest.mark.whole_tree
def test_the_reader_reads_every_page_as_a_yaml_parser_does() -> None:
    """The stdlib reader and PyYAML agree on every page's references.

    The generator runs with the standard library alone (the CI job installs
    nothing), so it reads the frontmatter with a narrow reader of its own. This
    holds the reader to a real YAML parser over the whole site, so a page
    written in a shape it would misread fails here and not as a silently
    missing bibliography entry.
    """
    content = generate_site_reports.CONTENT
    pages = sorted([*content.rglob("*.md"), *content.rglob("*.mdx")])
    cited = 0
    for path in pages:
        text = path.read_text(encoding="utf8")
        expected: list[dict[str, object]] = []
        if text.startswith("---\n"):
            frontmatter = yaml.safe_load(text[4 : text.find("\n---", 3)]) or {}
            expected = frontmatter.get("references") or []
        assert generate_site_reports.read_references(path) == expected, path
        cited += len(expected)
    assert cited > 0


@pytest.mark.parametrize(
    "line",
    [
        "    note: >",
        "    title: 'single quoted'",
        "  - {type: standard}",
        "      - nested item",
        "- type: book",
        "# a comment at the margin\n  - type: book",
    ],
)
def test_the_reader_stops_on_a_line_it_cannot_follow(
    tmp_path: pathlib.Path, line: str
) -> None:
    """A references line in any other shape stops the run, naming the line."""
    page = tmp_path / "page.md"
    page.write_text(
        f'---\ntitle: "A page"\nreferences:\n  - type: standard\n{line}\n---\n',
        encoding="utf8",
    )
    with pytest.raises(SystemExit, match="page.md:5"):
        generate_site_reports.read_references(page)


@pytest.mark.parametrize(
    ("frontmatter", "line"),
    [
        # A list written at the margin, valid YAML the reader would read as empty.
        (
            'references:\n- type: book\n  authors: ["Rossing, T. D. (Ed.)"]\n'
            "  year: 2014\n",
            4,
        ),
        # A list written on the line of its key.
        ("references: [{type: book, year: 2014}]\n", 3),
    ],
)
def test_the_reader_stops_on_a_list_it_would_read_as_empty(
    tmp_path: pathlib.Path, frontmatter: str, line: int
) -> None:
    """A references list in a shape the reader does not follow is never no list."""
    page = tmp_path / "page.md"
    page.write_text(f'---\ntitle: "A page"\n{frontmatter}---\n', encoding="utf8")
    assert yaml.safe_load(frontmatter)["references"]
    with pytest.raises(SystemExit, match=f"page.md:{line}"):
        generate_site_reports.read_references(page)


def test_the_reader_reads_on_past_a_blank_line_and_stops_at_the_next_key(
    tmp_path: pathlib.Path,
) -> None:
    """A blank line between entries is no end of the list; the next key is."""
    page = tmp_path / "page.md"
    frontmatter = (
        'references:\n  - type: standard\n    designation: "ISO 1:2002"\n\n'
        '  - type: book\n    year: 2014\nsidebar:\n  label: "x"\n'
    )
    page.write_text(f'---\ntitle: "A page"\n{frontmatter}---\n', encoding="utf8")
    expected = yaml.safe_load(frontmatter)["references"]
    assert generate_site_reports.read_references(page) == expected
    assert len(expected) == 2


@pytest.mark.whole_tree
def test_every_corrected_work_has_one_bibliography_entry() -> None:
    """Every work a family corrects is named once in each language's bibliography.

    The shipped registry against the shipped pages: the guard that the CI job
    runs through ``--check``.
    """
    pages = generate_site_reports.family_pages()
    assert generate_site_reports.check_bibliography(pages) == []
    corrected = [
        work for page in pages for work in generate_site_reports.corrected_works(page)
    ]
    assert len(corrected) > len(pages) // 2


def test_every_family_but_the_closing_list_corrects_a_work() -> None:
    """A family that named no work would pass the guard by naming nothing."""
    for page in generate_site_reports.family_pages():
        works = generate_site_reports.corrected_works(page)
        assert bool(works) == (page.family.group != "not-errata"), page.family.slug


def test_a_work_no_page_cites_is_listed_in_both_languages() -> None:
    """A designation the bibliography does not hold is listed once per language."""
    pages = generate_site_reports.plan_families(
        ["ISO 9613-2:1996, 7.3 (a ground factor)", "Rossing (2014), Table 8.1 (a year)"]
    )
    bibliography: list[dict[str, object]] = [_iso("ISO 9613-2:1996")]
    unmatched = generate_site_reports.unmatched_works(
        pages, {"en": bibliography, "es": []}
    )
    assert [(item.family, item.lang, item.found) for item in unmatched] == [
        ("iso-9613", "es", 0),
        ("rossing", "en", 0),
        ("rossing", "es", 0),
    ]
    assert str(unmatched[1]) == (
        "rossing (en): book by Rossing (2014) has no bibliography entry"
    )


def test_a_work_two_entries_match_is_listed_as_ambiguous() -> None:
    """Two distinct works under one description would make the page point at either."""
    page = generate_site_reports.plan_families(["Jarvis (1996), Appendix B (a unit)"])
    reports: list[dict[str, object]] = [
        {"type": "report", "authors": ["Jarvis, D. R."], "year": 1996, "title": t}
        for t in ("First report", "Second report")
    ]
    unmatched = generate_site_reports.unmatched_works(
        page, {"en": reports, "es": reports}
    )
    assert [item.found for item in unmatched] == [2, 2]
    assert "matches 2 bibliography entries" in str(unmatched[0])


def test_one_work_cited_on_many_pages_is_one_match() -> None:
    """The same entry repeated on every page that cites it is still one work."""
    page = generate_site_reports.plan_families(
        ["Long, Architectural Acoustics 2e (2014), Eq. (1)"]
    )
    long = {
        "type": "book",
        "authors": ["Long, M."],
        "year": 2014,
        "title": "Architectural acoustics",
        "doi": "10.1016/C2012-0-03257-5",
    }
    assert (
        generate_site_reports.unmatched_works(page, {"en": [long, long], "es": [long]})
        == []
    )


def test_a_registry_spelling_is_read_as_the_guides_spell_it() -> None:
    """An alias names the bibliography's designation, in each language."""
    page = generate_site_reports.plan_families(
        ["ITU-R BS.468-4, Table 2, 5 ms upper limit (a cell)"]
    )[0]
    (work,) = generate_site_reports.corrected_works(page)
    english = _iso("Recommendation ITU-R BS.468-4")
    spanish = _iso("Recomendación UIT-R BS.468-4")
    assert work.matches(english, "en")
    assert not work.matches(spanish, "en")
    assert work.matches(spanish, "es")
    assert not work.matches(english, "es")


def test_every_alias_names_a_designation_the_registry_prints() -> None:
    """An alias for a spelling no heading uses any more is dead and goes."""
    printed = {
        edition
        for page in generate_site_reports.family_pages()
        for edition in page.editions
    }
    assert set(generate_site_reports.DESIGNATED_AS) <= printed


def test_list_unmatched_prints_the_works_and_fails(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """``--list-unmatched`` prints one line per work and exits 1 while any is left."""
    missing = generate_site_reports.Unmatched(
        "randi",
        "en",
        generate_site_reports.Work(kind="report", who="Breeding", year=1996),
        0,
    )
    monkeypatch.setattr(
        generate_site_reports,
        "check_bibliography",
        lambda pages, bibliographies=None: [missing],
    )
    assert generate_site_reports.main(["--list-unmatched"]) == 1
    out = capsys.readouterr().out
    assert "randi (en): report by Breeding (1996) has no bibliography entry" in out
    assert generate_site_reports.main(["--check"]) == 1
    assert "randi (en)" in capsys.readouterr().err
    monkeypatch.setattr(
        generate_site_reports,
        "check_bibliography",
        lambda pages, bibliographies=None: [],
    )
    assert generate_site_reports.main(["--list-unmatched"]) == 0


@pytest.mark.parametrize(
    ("ref", "fragment"),
    [
        (_iso("ISO 3743-1:2010"), "std-iso-3743-1-2010"),
        (
            {"type": "standard", "designation": "Recomendación UIT-R BS.468-4"},
            "std-recomendacion-uit-r-bs-468-4",
        ),
        (
            {"type": "book", "doi": "10.1002/9780470747339", "title": "Propagation"},
            "doi-10-1002-9780470747339",
        ),
        (
            {
                "type": "book",
                "authors": ["Harris, C. M."],
                "year": 1995,
                "title": "Manual de medidas acústicas y control del ruido",
            },
            "book-harris-1995-manual-de-medidas-acusticas-y-control-del-ruido",
        ),
        (
            {
                "type": "report",
                "organization": "National Marine Fisheries Service",
                "year": 2024,
                "title": "Technical guidance (version 3.0)",
            },
            "report-national-marine-fisheries-service-2024-technical-guidance-version-3-0",
        ),
        ({"type": "web", "title": "A page"}, "web-nd-a-page"),
    ],
)
def test_a_fragment_is_the_one_the_site_gives_the_work(
    ref: dict[str, object], fragment: str
) -> None:
    """The fragment is ``referenceId``'s in ``site/src/lib/citations.mjs``.

    The site stops the build on a fragment its bibliography does not define,
    which holds the two to each other on every page; these pin the cases that
    differ: a translated designation with an accent, a DOI, a first author
    written with initials, an organization, a work with no year.
    """
    assert generate_site_reports.reference_fragment(ref) == fragment


def _frontmatter(text: str) -> dict[str, object]:
    loaded = yaml.safe_load(text.split("---\n")[1])
    assert isinstance(loaded, dict)
    return loaded


@functools.cache
def _corrects() -> dict[tuple[str, str], tuple[str, ...]]:
    """Each family page's ``corrects`` as the generator writes it, by language and slug."""
    rendered = generate_site_reports.rendered_pages()
    out: dict[tuple[str, str], tuple[str, ...]] = {}
    for edition in generate_site_reports.EDITIONS:
        for page in generate_site_reports.family_pages():
            path = (
                generate_site_reports.CONTENT
                / edition.folder
                / f"{page.family.slug}.md"
            )
            front = _frontmatter(rendered[path])
            assert "references" not in front, path.name
            corrects = front.get("corrects", [])
            assert isinstance(corrects, list), path.name
            out[edition.lang, page.family.slug] = tuple(map(str, corrects))
    return out


def test_every_family_page_names_the_works_it_corrects() -> None:
    """Each family page carries ``corrects``, one fragment per work it corrects.

    The site names them in the page's structured data, so a search engine
    reads an errata page as about the documents it corrects; and only there,
    not in ``references``, which would rank it with the guides. The count is
    of the distinct works the page corrects, not of what wrote the field: two
    headings that print one edition twice (``VDI 2081 Blatt 1:2001`` and
    ``VDI 2081 Blatt 1:2001-07``) name it once.
    """
    bibliographies: dict[generate_site_reports.Lang, list[dict[str, object]]] = {
        "en": generate_site_reports.read_bibliography("en"),
        "es": generate_site_reports.read_bibliography("es"),
    }
    corrects = _corrects()
    for edition in generate_site_reports.EDITIONS:
        for page in generate_site_reports.family_pages():
            named = corrects[edition.lang, page.family.slug]
            where = f"{edition.lang}/{page.family.slug}"
            works = set(generate_site_reports.corrected_works(page))
            assert len(named) == len(works), where
            assert len(set(named)) == len(named), where
            assert named == generate_site_reports.corrected_fragments(
                page, edition.lang, bibliographies[edition.lang]
            ), where
            assert bool(named) == (page.family.group != "not-errata"), where


@pytest.mark.parametrize(
    ("lang", "slug", "fragments"),
    [
        ("en", "iso-3743", ("std-iso-3743-1-2010", "std-iso-3743-2-2018")),
        ("es", "iso-3743", ("std-iso-3743-1-2010", "std-iso-3743-2-2018")),
        *[
            (
                lang,
                "iso-12354",
                (
                    "std-en-12354-1-2000",
                    "std-iso-12354-1-2017",
                    "std-en-12354-2-2000",
                    "std-en-12354-3-2000",
                    "std-en-12354-5-2009",
                    "std-iso-12354-2-2017",
                ),
            )
            for lang in ("en", "es")
        ],
        ("en", "icao-annex-16", ("std-icao-annex-16-vol-i-8th-ed",)),
        ("es", "icao-annex-16", ("std-icao-annex-16-vol-i-8-ed",)),
        *[
            (
                lang,
                "harris",
                ("book-harris-1995-manual-de-medidas-acusticas-y-control-del-ruido",),
            )
            for lang in ("en", "es")
        ],
        ("en", "iec-62489", ("std-iec-62489-1-2010-amd1-2014",)),
        (
            "en",
            "vdi-2081",
            ("std-vdi-2081-blatt-1-2001-07", "std-vdi-2081-blatt-2-2005-05"),
        ),
        ("en", "not-errata", ()),
    ],
)
def test_a_family_page_names_these_works(
    lang: str, slug: str, fragments: tuple[str, ...]
) -> None:
    """The works of a few families, written out, so a regression cannot pass as itself.

    Every edition of a family on one page and in the order the registry
    names them (ISO 12354, six); a designation the Spanish bibliography
    translates (ICAO Annex 16, "8.ª ed."); a book with no DOI (Harris); and
    the two families whose headings print one edition under two spellings,
    each named once: IEC 62489-1:2010 and the amendment the guides cite it
    with, and VDI 2081 Blatt 1 with and without the month.
    """
    assert _corrects()[lang, slug] == fragments


@pytest.mark.parametrize("lang", ["en", "es"])
def test_the_family_pages_of_a_language_name_133_works(lang: str) -> None:
    """In each language, 95 family pages name 133 works in all."""
    named = {
        slug: works
        for (language, slug), works in _corrects().items()
        if language == lang
    }
    assert sum(1 for works in named.values() if works) == 95
    assert sum(len(works) for works in named.values()) == 133
