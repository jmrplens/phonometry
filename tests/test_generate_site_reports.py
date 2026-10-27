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

import pathlib
import sys

import pytest

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


def test_a_family_page_is_ranked_by_the_register_and_shown_by_its_title() -> None:
    """A page about one document is ranked by the register's name, not its own.

    Its title is the document's designation, and the site search weights a
    title five times; ranked by it, the page would outrank the guides written
    to the document. The page of properties that are not errata names no
    document and keeps its own title.
    """
    pages = generate_site_reports.plan_families(
        [
            "VDI 2081 Blatt 2:2005-05, Table 1, element 2",
            generate_site_reports.NOT_ERRATA_HEADING,
        ]
    )
    by_slug = {page.family.slug: page for page in pages}
    vdi, plain = by_slug["vdi-2081"], by_slug["not-errata"]
    assert generate_site_reports.search_title(vdi, "en") == "Errata"
    assert generate_site_reports.search_title(vdi, "es") == "Erratas"
    assert generate_site_reports.search_title(plain, "en") is None
    edition = generate_site_reports.EDITIONS[0]
    registry = generate_site_reports.Registry(
        preamble="",
        entries=(
            ("VDI 2081 Blatt 2:2005-05, Table 1, element 2", "## VDI ...\n\nText."),
            (generate_site_reports.NOT_ERRATA_HEADING, "## Related ...\n\nText."),
        ),
    )
    text = generate_site_reports.render_family(vdi, edition, registry)
    assert 'title: "Errata in VDI 2081"\n' in text
    assert 'searchTitle: "Errata"\n' in text.split("---")[1]
    assert "searchTitle" not in generate_site_reports.render_family(
        plain, edition, registry
    )
