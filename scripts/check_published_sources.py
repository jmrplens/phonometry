#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Fail on a published value that does not say which page it was read on.

A number transcribed from a book is only checkable if the next reader can open
the same page. Nothing in CI used to require that: the convention lived in
review, and review is where it was quietly dropped, which is how one table came
to cite a folio that prints no such number and another attributed to a table two
columns it does not print. This is the guard for that class.

Three things are checked, and the third is what stops the first two being
vacuous.

1. **The grammar of a ``source`` field.** Every public record that carries one,
   and every mapping or sequence of such records, has to write it the way the
   errata registry writes its evidence (CONTRIBUTING.md "Filing an errata
   entry"): the document, the table or section, the PDF page and the printed
   folio, cited by designation and never by file path. A row whose columns come
   off two pages names both, separated by ``"; "``. :data:`FOLIO_FORMS` has the
   four spellings, including the one for a page that prints no folio at all,
   and each of them takes either a page number or the chapter-and-page form a
   handbook of independently paginated chapters prints.
   Nothing published here needs that fourth form yet; it is accepted from the
   start so that the first row that does cannot invent a second spelling for an
   unnumbered page. ``scripts/check_errata_evidence.py``, which reads the same
   grammar in the errata registry, has still to be taught it, and whoever files
   the first such entry there does it in that change.

2. **The document exists in the bibliography.** Each distinct document named is
   split and recomposed by :mod:`conformance.references`, character for
   character, and then has to have an entry in ``docs/reference/bibliography.md``.
   A book cited from ``src`` and missing from the bibliography is a source the
   reader cannot resolve; the sweep that added this guard found one.

3. **The registry, so the guard has something to be true of.**
   :data:`SOURCED` names every table in ``src`` transcribed from a book or a
   paper, and requires its banner to cite **both** a PDF page and a printed
   folio. The census that fills it is re-run here, over the banners themselves,
   so a table transcribed from a new book fails until it is registered: that is
   what closes the class rather than pinning today's instances of it.

   Closing it means the census has to catch a banner however it is written.
   Its first shape did not, and the review that found this counted the escapes:
   a surname whitelist that no single-author book could match, which left eight
   Long tables and the two constants of Cremer Table 5.1 uncited while the gate
   reported green; a banner reader that only looked at ``#:``, so two Bies
   tables left the census by dropping one character; and a locator pattern
   whose ``Fig.``, ``Eq.`` and ``Sect.`` alternatives closed with a word
   boundary after a literal ``.``, which needs a word character next and so
   matches nothing anybody writes.
   The surnames now come from the bibliography (:func:`bibliography_leads`),
   any comment block counts as a banner, and the abbreviated locators are
   matched without the trailing boundary.
   :data:`NOT_TRANSCRIBED` is the other side of a wider net: a banner that
   names a document for its *formula* while the values are arithmetic says so
   there rather than citing a page that prints nothing.

A standard is deliberately outside the registry. ISO, IEC, EN and DIN number
their own clauses and tables, and CONTRIBUTING.md asks for a citation by that
number; a PDF page would pin the reading to one copy of a document this project
does not redistribute. A book numbers nothing a reader can resolve without the
page, which is exactly why the errata rule demands one.

:data:`PAGE_UNKNOWN` is the escape hatch, and it is a ratchet in both
directions: an entry whose banner now cites its page fails until the line is
deleted, and a line naming a table that no longer exists fails too.
:data:`NOT_TRANSCRIBED` ratchets the same way.

Usage::

    python scripts/check_published_sources.py

Exit status 0 when every published value says where it was read; 1 otherwise,
naming the record, the field and the module.
"""

from __future__ import annotations

import argparse
import ast
import dataclasses
import importlib
import json
import pathlib
import pkgutil
import re
import sys
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, NamedTuple

from conformance import references

import phonometry

if TYPE_CHECKING:
    from collections.abc import Iterator
    from types import ModuleType

ROOT = pathlib.Path(__file__).resolve().parent.parent
PACKAGE = pathlib.Path(phonometry.__file__).resolve().parent
BIBLIOGRAPHY = ROOT / "docs" / "reference" / "bibliography.md"

#: The field a record uses to say where it was read.
SOURCE_FIELD = "source"

#: One citation: the document and its locator, the PDF page, and the folio in
#: parentheses. Several are joined by ``"; "``.
CITATION = re.compile(
    r"^(?P<cite>.+?), PDF pages? (?P<pages>\d+(?:-\d+)?) \((?P<folio>[^()]+)\)$"
)

#: The four ways a folio may be written. The last is for a page that prints no
#: folio of its own, which happens on the landscape plates of an appendix; it
#: names the folios either side rather than inventing one.
#: Several citations are joined by ``"; "``, and the fourth folio form carries a
#: semicolon of its own, so the split is only made after a closing parenthesis.
JOINER = re.compile(r"(?<=\)); ")

#: A folio as a page prints it. Most books print a page number and nothing
#: else, but a handbook whose chapters are paginated independently prints the
#: chapter with it, so the eighth page of Chapter 32 carries "32.8" and there
#: is no other number on it. That is a reading of the page, not a malformed
#: one, and the errata registry has accepted it from the start
#: (``scripts/check_errata_evidence.py``, PAGE_CITATION); this gate refused it
#: only because its first shape was written before the first such book landed.
FOLIO = r"\d+(?:\.\d+)?"

FOLIO_FORMS = (
    re.compile(rf"^printed p\. {FOLIO}$"),
    re.compile(rf"^printed pp\. {FOLIO}-{FOLIO}$"),
    re.compile(rf"^printed folio {FOLIO}$"),
    re.compile(rf"^no printed folio; between folios {FOLIO} and {FOLIO}$"),
)

#: Every table in ``src`` transcribed from a book or a paper, with what it holds.
#: A banner here must cite both the PDF page and the printed folio. Keyed by
#: module path relative to the package and the name of the constant.
#:
#: The value opens with the citation, up to its first comma, and that citation
#: is parsed and checked against the bibliography like any other: a book this
#: library transcribes a table from and does not list is a source the reader
#: cannot resolve.
SOURCED: dict[tuple[str, str], str] = {
    (
        "building/prediction/aperture_transmission.py",
        "_FIELD_M",
    ): "Hopkins (2007) Eq. 4.99, the incident-field constant m",
    (
        "building/prediction/aperture_transmission.py",
        "_POSITION_N",
    ): "Hopkins (2007) Eq. 4.99, the slit-position constant n",
    (
        "building/prediction/ceiling_plenum.py",
        "_SIDEWALLS",
    ): "Vigran (2008) Eqs. (9.18) and (9.19), the two sidewall cases",
    (
        "building/prediction/masonry_cavity_wall.py",
        "WALL_TIE_STIFFNESS",
    ): "Hopkins (2007) Table A4, four wall ties",
    (
        "building/prediction/panel_transmission.py",
        "PLATEAU_MATERIALS",
    ): "Norton & Karczub (2003) Table 3.1, eight plateau-method materials",
    (
        "building/prediction/panel_transmission.py",
        "_FIELD_CORRECTION",
    ): "Bies 5e Eq. 7.42, the field-incidence correction per band width",
    (
        "building/prediction/resilient_layers.py",
        "_BANDWIDTH_FACTOR",
    ): "Hopkins (2007) Eq. (3.91), the two band-width factors B",
    (
        "materials/absorbers/porous.py",
        "DELANY_BAZLEY_COEFFICIENTS",
    ): "Bies 5e Table D.1, four coefficient sets C1..C8",
    (
        "materials/absorbers/porous.py",
        "DELANY_BAZLEY_VALIDITY",
    ): "Hopkins (2007) Eq. (1.174), the stated range of X",
    (
        "materials/absorbers/porous.py",
        "LIMP_FRAME_CRITERIA",
    ): "Allard & Atalla 2e Sect. 11.3.4, two limp-frame criteria",
    (
        "materials/absorbers/porous.py",
        "MIKI_VALIDITY",
    ): "Miki (1990) Sect. 4.1, the lower limit of the fit range",
    (
        "environment/propagation/ground_surfaces.py",
        "PUBLISHED_GROUND",
    ): (
        "Bies 5e Table 5.1, thirty-four measured ground surfaces; "
        "Bies 5e Table 5.2, the eight ground classes A to H with the ISO "
        "9613-2 and NMPB-2008 ground factors; "
        "Cox & D'Antonio 3e Table 6.7, sixty-three effective flow "
        "resistivities over three model fits"
    ),
    (
        "fluids/catalogue.py",
        "PUBLISHED_FLUIDS",
    ): (
        "Bies 5e Table C.1, the three fluids it prints before its solids; "
        "Norton & Karczub (2003) Appendix 4 B and C, nine liquids and nine "
        "gases each at a stated temperature"
    ),
    (
        "solids/damping_treatments.py",
        "PUBLISHED_DAMPING_TREATMENTS",
    ): (
        "Harris (1977) Table 14.2, eight asphalt felt treatments rated by the "
        "decay rate of a standard steel panel"
    ),
    (
        "solids/nonlinearity.py",
        "PUBLISHED_SOLID_NONLINEARITY",
    ): (
        "Rossing (2014) Table 6.5, the ultrasonic nonlinearity parameter of "
        "eight solids at room temperature"
    ),
    (
        "materials/resilient/moduli.py",
        "PUBLISHED_RESILIENT_MODULI",
    ): (
        "Vigran (2008) Table 8.3, the dynamic modulus of six resilient "
        "materials under a static load of about 2 kPa"
    ),
    (
        "materials/absorbers/carpets.py",
        "PUBLISHED_CARPETS",
    ): (
        "Harris 3e Tables 30.2 and 30.3, nineteen carpets with their pile and "
        "noise reduction coefficient"
    ),
    (
        "fluids/nonlinearity.py",
        "PUBLISHED_NONLINEARITY",
    ): (
        "Rossing (2014) Tables 8.1 to 8.4, a hundred and sixty-four values of "
        "the nonlinearity parameter B/A, each credited to the paper it comes "
        "from"
    ),
    (
        "simulation/elastic_fdtd.py",
        "ALUMINIUM",
    ): (
        "Bies 5e Table C.1, the density of its aluminium sheet and the two "
        "bulk speeds its modulus and Poisson ratio give"
    ),
    (
        "simulation/elastic_fdtd.py",
        "CONCRETE",
    ): (
        "Bies 5e Table C.1, the density of its high-strength concrete and the "
        "two bulk speeds its modulus and Poisson ratio give"
    ),
    (
        "simulation/elastic_fdtd.py",
        "STEEL",
    ): (
        "Bies 5e Table C.1, the density of its mild steel and the two bulk "
        "speeds its modulus and Poisson ratio give"
    ),
    (
        "fluids/catalogue.py",
        "PUBLISHED_GASES",
    ): (
        "Bies 5e Table C.2, thirty-seven gases with a molar mass and a ratio "
        "of specific heats; "
        "Hopkins (2007) Table A1, the six gases it prints the same pair for"
    ),
    (
        "materials/absorbers/measured.py",
        "PUBLISHED_ABSORPTION",
    ): (
        "Bies 5e Table 6.2, the fifty-seven finishes it prints a Sabine "
        "absorption coefficient for, band by band; "
        "Long 2e Table 7.1, the hundred finishes it prints a coefficient and "
        "an ASTM C423 mounting for; "
        "Cox & D'Antonio 3e Appendix A, a hundred and sixty-one rows compiled "
        "from twenty-nine sources and credited row by row; "
        "Arau-Puchades (1999) Table 6.1, the ninety-six of its ninety-nine "
        "numbered rows that are an absorption coefficient; "
        "Everest 4e Appendix, forty-one rows with the source of each in a "
        "column of its own"
    ),
    (
        "materials/absorbers/measured.py",
        "PUBLISHED_ABSORPTION_AREAS",
    ): (
        "Bies 5e Table 6.2, the two audience rows it prints as an absorption "
        "area per person; "
        "Long 2e Table 7.1, the musician and the air, in sabins"
    ),
    (
        "building/catalogue.py",
        "PUBLISHED_TRANSMISSION_LOSS",
    ): (
        "Bies 5e Table 7.6, ninety-four constructions with a thickness, a "
        "surface density and eight octave bands of transmission loss; "
        "ASHRAE (2019) HVAC Applications Handbook Chapter 49 Table 40, nine "
        "machine equipment room walls, floors and ceilings with a sound "
        "transmission class and seven octave bands; Rossing (2014) Table "
        "11.4, twenty-three partitions with six octave bands and a sound "
        "transmission class; Harris 3e Tables 31.2, 31.3 and 31.5 to 31.9, "
        "a hundred and twenty-nine walls, doors, windows and floors with a "
        "sound transmission class and no band"
    ),
    (
        "noise_control/duct_walls.py",
        "PUBLISHED_DUCT_TRANSMISSION_LOSS",
    ): (
        "ASHRAE (2019) HVAC Applications Handbook Chapter 49 Tables 29 to 34, "
        "forty-six duct walls over six tables: the breakout and the break-in "
        "transmission loss of a rectangular, round and flat oval duct wall, "
        "band by band"
    ),
    (
        "building/impact_catalogue.py",
        "PUBLISHED_IMPACT_INSULATION",
    ): (
        "Harris 3e Tables 32.1 to 32.8, forty-two floor-ceiling constructions "
        "with an impact insulation class and six elastic surface treatments "
        "with the improvement each adds over a hard massive floor; Harris "
        "(1977) Tables 19.2 to 19.4, twenty-three floor treatments on bare "
        "concrete with the average improvement in impact sound insulation"
    ),
    (
        "materials/diffusers/measured_scattering.py",
        "PUBLISHED_SCATTERING",
    ): (
        "Cox & D'Antonio 3e Appendix D, forty-six surfaces whose random "
        "incidence scattering coefficient was measured according to "
        "ISO 17497-1, each credited to the paper it comes from"
    ),
    (
        "materials/diffusers/predicted_diffusion.py",
        "PUBLISHED_DIFFUSION",
    ): (
        "Cox & D'Antonio 3e Appendix B, twenty-nine surfaces at three angles "
        "of incidence each, whose normalized diffusion coefficient was "
        "computed with a two-dimensional boundary element model following "
        "ISO 17497-2"
    ),
    (
        "materials/diffusers/predicted_scattering.py",
        "PUBLISHED_PREDICTED_SCATTERING",
    ): (
        "Cox & D'Antonio 3e Table C.1 and Table C.2, forty rows of "
        "three-dimensional boundary element predictions at normal and at "
        "random incidence, credited to Lee and Sakuma (2015); "
        "Cox & D'Antonio 3e Table C.3, twenty-seven surfaces of "
        "two-dimensional predictions at three angles of incidence each"
    ),
    (
        "materials/absorbers/catalogue.py",
        "PUBLISHED_POROUS",
    ): (
        "Allard & Atalla 2e, the porous rows of nineteen parameter tables "
        "spread over eight chapters"
    ),
    (
        "materials/absorbers/resistive_sheets.py",
        "PUBLISHED_FLOW_RESISTANCE",
    ): (
        "Vér & Beranek 2e TABLE 8.5, five wire mesh cloths; "
        "Vér & Beranek 2e TABLE 8.6, thirteen glass fibre cloths; "
        "Vér & Beranek 2e TABLE 8.7, eleven sintered porous metal sheets"
    ),
    (
        "materials/absorbers/porous.py",
        "ROCK_WOOL_LATERAL_FIT",
    ): "Hopkins (2007) Eq. (1.165), the lateral k1 and k2 of the rock wool",
    (
        "materials/absorbers/porous.py",
        "ROCK_WOOL_LONGITUDINAL_FIT",
    ): "Hopkins (2007) Eq. (1.165), the longitudinal k1 and k2 of the rock wool",
    (
        "materials/resilient/dynamic_stiffness.py",
        "PUBLISHED_RESILIENT_LAYERS",
    ): "Hopkins (2007) Table A3, fifteen resilient layers",
    (
        "solids/catalogue.py",
        "PUBLISHED_SOLIDS",
    ): (
        "Hopkins (2007) Table A2, twenty-five solid materials; "
        "Cremer 3e Table 4.3, thirteen metals over fifteen rows; "
        "Mechel (2008) Table 3, thirty-eight construction materials, "
        "plastics and metals; "
        "Bies 5e Table C.1, one hundred and five metals, building materials, "
        "woods, plastics and honeycomb panels; "
        "Long 2e Table 12.1, eighteen common building materials; "
        "Arau-Puchades (1999) Table 4.1, seventeen materials over eighteen rows"
    ),
    (
        "noise_control/duct_modes.py",
        "CIRCULAR_EIGENVALUES",
    ): "Norton & Karczub (2003) Table 7.1, twelve circular-duct eigenvalues",
    (
        "noise_control/hvac.py",
        "_DAMPER_CORRECTION",
    ): (
        "ASHRAE (2019) HVAC Applications Handbook Chapter 49 Table 10, the "
        "decibels added to a diffuser sound rating for damper throttling, at "
        "three places a damper can sit"
    ),
    (
        "noise_control/hvac.py",
        "_DAMPER_PRESSURE_RATIOS",
    ): (
        "ASHRAE (2019) HVAC Applications Handbook Chapter 49 Table 10, the six "
        "damper pressure ratios those decibels are tabulated against"
    ),
    (
        "noise_control/hvac.py",
        "_EFFICIENCY_CORRECTION",
    ): "Long 2e Table 13.6, seven off-peak efficiency corrections",
    (
        "noise_control/hvac.py",
        "_ELBOW_WL_UPPER",
    ): "Bies 5e Table 8.11, elbow insertion loss over six W/lambda bands",
    (
        "noise_control/hvac.py",
        "_END_REFLECTION_BANDS",
    ): "Bies 5e Table 8.14, duct end reflection loss over twelve diameters",
    (
        "noise_control/hvac.py",
        "_FAN_CASING_ATTENUATION",
    ): "Long 2e Table 13.8, eight octave-band casing attenuations",
    (
        "noise_control/hvac.py",
        "_FAN_LEVEL_CORRECTION",
    ): "Long 2e Tables 13.5 and 13.7, the fan spectral constants",
    (
        "noise_control/hvac.py",
        "_FLEX_DIAMETERS_IN",
    ): "Long 2e Table 14.4, lined flexible duct insertion loss",
    (
        "noise_control/hvac.py",
        "_LINED_RECT_B",
    ): "Long 2e Table 14.2, the constants B, C and D",
    (
        "noise_control/hvac.py",
        "_LINED_ROUND_COEFFS",
    ): "Long 2e Table 14.3, the constants A to F",
    (
        "noise_control/hvac.py",
        "_SILENCER_SELF_NOISE_CORRECTION",
    ): "Long 2e Table 14.8, eight self-noise corrections",
    (
        "noise_control/hvac.py",
        "_TERMINAL_VELOCITY_LIMIT",
    ): (
        "ASHRAE (2019) HVAC Applications Handbook Chapter 49 Table 9, the "
        "maximum free-opening face velocity of a supply diffuser and a return "
        "register, over five design room criteria"
    ),
    (
        "noise_control/hvac.py",
        "_UNLINED_CIRCULAR_DB_PER_FT",
    ): "Long 2e Table 14.1, losses in unlined circular ducts",
    (
        "room/steady_field.py",
        "SOURCE_POWER_MODELS",
    ): "Norton & Karczub (2003) Table 4.5, three sound power models",
    (
        "underwater/bioacoustics/audiograms.py",
        "BEST_HEARING_FREQUENCY_KHZ",
    ): "Southall et al. (2019) Table 4, frequency of best hearing",
    (
        "underwater/bioacoustics/audiograms.py",
        "_AUDIOGRAM_NORMALIZED",
    ): "Southall et al. (2019) Table 3, the same fits normalised",
    (
        "underwater/bioacoustics/audiograms.py",
        "_AUDIOGRAM_ORIGINAL",
    ): "Southall et al. (2019) Table 2, seven group audiogram fits",
    (
        "underwater/bioacoustics/weighting.py",
        "_CRITERIA_SOUTHALL_CONTINUOUS",
    ): "Southall et al. (2019) Tables 6 and 7, TTS and PTS onset thresholds",
    (
        "underwater/bioacoustics/weighting.py",
        "_SOUTHALL_2019",
    ): "Southall et al. (2019) Table 5, the weighting-function parameters",
    (
        "underwater/propagation/weston_regimes.py",
        "WESTON_SEABEDS",
    ): "Ainslie (2010) Table 9.1, two characteristic seabeds",
    (
        "vibration/structural/junction_transmission.py",
        "_JUNCTIONS",
    ): "Hopkins (2007) Eqs. 5.12 and 5.13, four sets of junction constants",
    (
        "vibration/structural/point_mobility.py",
        "_BEAM_CONSTANT",
    ): "Cremer 3e Table 5.1, the two slender-beam constants",
    (
        "vibration/structural/point_mobility.py",
        "_PLATE_CONSTANT",
    ): "Cremer 3e Table 5.1, the two thin-plate constants",
    (
        "vibration/structural/radiation_efficiency.py",
        "_C_BC",
    ): "Hopkins (2007) Eq. 2.227, the boundary-condition constant",
    (
        "vibration/structural/radiation_efficiency.py",
        "_C_OB",
    ): "Hopkins (2007) Eq. 2.227, the baffle-orientation constant",
}

#: Tables whose page cannot be established, each with the reason. Empty, and
#: meant to stay that way: every source this repository transcribes from is a
#: document it can open. A line added here is a promise to come back.
PAGE_UNKNOWN: dict[tuple[str, str], str] = {}

#: Tables the census catches and that transcribe nothing: the banner names a
#: document because the **formula** is that document's, while the values are
#: arithmetic anybody can redo. A page would be a false citation, since no page
#: of the book prints them, so these say so here instead. Like
#: :data:`PAGE_UNKNOWN` this is a two-way ratchet: a line naming a table the
#: census no longer reaches fails as loudly as a transcription that is missing
#: one, and a table cannot be in this and in :data:`SOURCED` at once.
NOT_TRANSCRIBED: dict[tuple[str, str], str] = {
    (
        "vibration/structural/experimental_sea.py",
        "_BANDWIDTH_FACTOR",
    ): "sqrt(2) and sqrt(2 ** (1/3)), the band edges themselves; Norton is "
    "named for Eq. 6.29, which consumes them",
}

#: One bibliography entry: the lead surname, or the organisation, it opens
#: with. A person is written ``- Cremer, L., ...`` and a body that authors its
#: own handbook is written ``- ASHRAE (2019). ...``, which is the APA shape for
#: a corporate author and was invisible to the first version of this pattern:
#: it required a comma or a full stop straight after the lead, so every
#: organisation in the bibliography was missing from the ratchet and a table
#: transcribed from one of their handbooks could sit in ``src`` uncited while
#: the gate reported green. Found by ASHRAE Chapter 49.
_BIBLIOGRAPHY_ENTRY = re.compile(r"^- (?P<lead>[^\s,.]+)(?:[,.]| \()", re.MULTILINE)


def bibliography_leads() -> tuple[str, ...]:
    """Every lead surname ``docs/reference/bibliography.md`` lists.

    A hardcoded list of surnames was the first shape of this, and it ratcheted
    only over books someone had already thought to name: a single-author book,
    the commonest shape in this field, matched nothing, which is how eight Long
    tables and the two constants of Cremer Table 5.1 sat in ``src`` with no
    page while the gate reported green. Reading the bibliography closes that, because rule 2
    already requires a cited book to be listed there, so a book this tree
    transcribes a table from is either in this list or already failing.

    :return: The surnames, sorted, in the spelling the bibliography uses.
    """
    text = BIBLIOGRAPHY.read_text(encoding="utf-8")
    return tuple(
        sorted({match["lead"] for match in _BIBLIOGRAPHY_ENTRY.finditer(text)})
    )


def _book_or_paper() -> re.Pattern[str]:
    """How this tree spells a book or a paper in a banner.

    A banner that names one of these **and** a locator is a transcription from
    a document with pages, and belongs in :data:`SOURCED`.

    :return: The compiled pattern.
    """
    leads = "|".join(re.escape(lead) for lead in bibliography_leads())
    return re.compile(rf"\b(?:{leads})\b|[A-Z][a-z]+ et al\.?,? \(?\d{{4}}")


BOOK_OR_PAPER = _book_or_paper()

#: A locator inside a document: what makes a banner a transcription rather than
#: a sentence that happens to name a book. The abbreviated forms are matched
#: without a closing ``\b``, because a word boundary after a literal ``.``
#: needs a word character next and nobody writes "Eq.7": the first shape of
#: this pattern carried three alternatives that could never match.
LOCATOR = re.compile(
    r"\b(?:Table|Tables|Annex|Appendix|Figure|Figures)\b"
    r"|\b(?:Fig|Figs|Eq|Eqs|Sect|Sects)\."
)

#: What a registered banner has to carry.
BANNER_PDF_PAGE = re.compile(r"PDF pages? \d+")
BANNER_FOLIO = re.compile(rf"printed (?:p\.|pp\.|folio) {FOLIO}|no printed folio")


class Problem(NamedTuple):
    """One thing wrong, with where to look."""

    #: Where the offending value or banner lives.
    where: str
    #: What is wrong with it.
    detail: str


def _is_public(name: str) -> bool:
    return not name.startswith("_")


def public_modules() -> Iterator[tuple[str, ModuleType]]:
    """Every module a caller can import by a public path, imported."""
    yield "phonometry", phonometry
    for found in pkgutil.walk_packages(phonometry.__path__, "phonometry."):
        if not all(_is_public(part) for part in found.name.split(".")):
            continue
        try:
            yield found.name, importlib.import_module(found.name)
        except ImportError:  # pragma: no cover - an optional backend
            continue


def _sourced_records(obj: object) -> Iterator[object]:
    """Every record carrying a ``source`` field reachable from *obj*.

    A published table is a mapping or a sequence of records as often as it is
    one record, and the provenance rule is the same in all three shapes.

    ``source`` is a field name this tree also uses for things that are not a
    provenance claim: an ``(x, y, z)`` image-source coordinate, a ground factor
    in ``[0, 1]``, a :class:`~phonometry.io.SignalOrigin`. Only a string can be
    a citation, so only a string is held to the grammar; none of the others
    would reach here today, and this is what keeps it that way when one does.
    """
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        if any(
            field.name == SOURCE_FIELD for field in dataclasses.fields(obj)
        ) and isinstance(getattr(obj, SOURCE_FIELD, None), str):
            yield obj
        return
    if isinstance(obj, Mapping):
        for value in obj.values():
            yield from _sourced_records(value)
        return
    if isinstance(obj, Sequence) and not isinstance(obj, (str, bytes)):
        for value in obj:
            yield from _sourced_records(value)


def _published_names(module: ModuleType) -> tuple[str, ...]:
    """What a caller can reach in *module* by a public name.

    ``__all__`` when the module declares one, and every public attribute when
    it does not: 115 of this package's public modules declare none, and a
    record added to any of them would otherwise never be read.
    """
    exported = getattr(module, "__all__", None)
    if exported is not None:
        return tuple(exported)
    return tuple(name for name in vars(module) if _is_public(name))


def published_records() -> Iterator[tuple[str, str, object]]:
    """``(module, exported name, record)`` for every published sourced record."""
    seen: set[int] = set()
    for module_name, module in public_modules():
        for exported in _published_names(module):
            obj = getattr(module, exported, None)
            for record in _sourced_records(obj):
                if id(record) in seen:
                    continue
                seen.add(id(record))
                yield module_name, exported, record


def citation_problems(source: str) -> list[str]:
    """What is wrong with a ``source`` string, or an empty list.

    :param source: The field's value, one or more citations joined by ``"; "``.
    :return: One message per defect found.
    """
    problems: list[str] = []
    if not source.strip():
        return ["is empty; every published value names the page it was read on"]
    for citation in JOINER.split(source):
        match = CITATION.match(citation)
        if match is None:
            problems.append(
                f"{citation!r} is not '<Document> <Table>, PDF page N (printed p. M)'"
            )
            continue
        folio = match["folio"]
        if not any(form.match(folio) for form in FOLIO_FORMS):
            problems.append(
                f"{citation!r} writes the folio as {folio!r}; the four forms are "
                "'printed p. N', 'printed pp. N-M', 'printed folio N' and "
                "'no printed folio; between folios A and B'"
            )
            continue
        cite = match["cite"]
        try:
            parsed = references.parse(cite)
        except ValueError as error:
            problems.append(f"{cite!r} does not parse as a reference: {error}")
            continue
        if references.recompose(parsed) != cite:
            problems.append(
                f"{cite!r} does not recompose character for character; it reads back as "
                f"{references.recompose(parsed)!r}"
            )
            continue
        problems.extend(_bibliography_problems(cite, parsed))
    return problems


def _bibliography_problems(cite: str, parsed: references.Reference) -> list[str]:
    """Whether every document *cite* names has a bibliography entry."""
    text = BIBLIOGRAPHY.read_text(encoding="utf-8")
    problems = []
    for document in references.documents(parsed):
        designation = document.designation
        lead = re.split(r" (?:&|and) | et al\.?", designation)[0].strip()
        if not lead:
            continue
        # The same two shapes ``_BIBLIOGRAPHY_ENTRY`` accepts: a person,
        # written ``- Cremer, L., ...``, and an organisation that authors
        # its own handbook, written ``- ASHRAE (2019). ...``. A corporate
        # designation usually carries its year, so the lead ends up being
        # "ASHRAE (2019)" and the full stop follows it; one written without
        # a year would reach here as "ASHRAE" and be rejected against an
        # entry that does have one. Two patterns for one rule is how the
        # first of them came to be wrong on its own.
        if not re.search(rf"^- {re.escape(lead)}(?:[,.]| \()", text, re.MULTILINE):
            problems.append(
                f"{cite!r} names {designation!r}, which has no entry in "
                "docs/reference/bibliography.md"
            )
    return problems


def banner_above(lines: Sequence[str], index: int) -> str:
    """The comment block immediately above line *index* (0-based).

    Both spellings count. Reading only ``#:`` let a table leave the census by
    losing one character: ``noise_control/hvac.py`` documents Bies Table 8.14
    and Bies Table 8.11 under plain ``#`` rules, naming the book and the table
    and no page at all, and the census never saw either. The horizontal rules
    that open and close such a block carry nothing and are dropped.
    """
    out: list[str] = []
    cursor = index - 1
    while cursor >= 0:
        stripped = lines[cursor].lstrip()
        if not stripped.startswith("#"):
            break
        body = (stripped[2:] if stripped.startswith("#:") else stripped[1:]).strip()
        if body and set(body) != {"-"}:
            out.append(body)
        cursor -= 1
    return " ".join(reversed(out))


#: A banner that says which packaged data file its table was read from, so the
#: citation can live in the file with the rows instead of being copied into a
#: comment that then drifts away from them. A banner may instead name the
#: **directory** the files live in, with the trailing slash, which means every
#: ``.json`` in it: a catalogue that reads one file per published table names
#: nineteen of them today and thirty when the next book lands, and a comment
#: that lists them is a second copy of the contents to go stale, which is the
#: thing this gate exists to prevent.
DATA_FILE = re.compile(r"``([\w./-]+\.json)``")
DATA_DIRECTORY = re.compile(r"``([\w./-]+/data)/``")

#: Both references in one pass, so that a banner naming a file, then a
#: directory, then another file keeps that order. Scanning for one kind and
#: then the other put every named file before every expanded one, and the
#: order is what the reader of the report sees beside each citation.
_REFERENCE = re.compile(
    r"``(?:(?P<file>[\w./-]+\.json)|(?P<directory>[\w./-]+/data)/)``"
)


def data_files(banner: str) -> list[str]:
    """The packaged data files *banner* points at, named or by directory.

    :param banner: The comment above the constant.
    :return: Paths relative to the package, in the order the banner refers to
        them, with each directory expanded in place to the ``.json`` files in
        it, sorted among themselves.
    """
    names: list[str] = []
    for match in _REFERENCE.finditer(banner):
        named = match.group("file")
        if named:
            names.append(named)
            continue
        directory = match.group("directory")
        found = sorted(path.name for path in (PACKAGE / directory).glob("*.json"))
        names.extend(f"{directory}/{name}" for name in found)
    return names


def data_citation(banner: str) -> tuple[str, str | None]:
    """The data files *banner* names and the citations inside them.

    A table read out of a packaged file cites the page once, in the file, and
    the banner points at the file. Reading it back here is what lets the two
    stay one thing: there is no second copy of the citation to go stale. A
    constant built from several files names them all, or names the directory
    they live in, and every one of them has to say where it came from: the one
    that did not would otherwise hide behind the ones that did.

    :return: The files the banner names joined by ``"; "``, empty when it
        names none, and their citations joined the same way, or ``None`` when
        any of them is missing, unreadable or says nothing about a page.
    """
    names = data_files(banner)
    if not names:
        return "", None
    cites: list[str] = []
    for name in names:
        path = PACKAGE / name
        if not path.is_file():
            return "; ".join(names), None
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            # A file that cannot be read cannot vouch for a page. Saying so
            # through the same return the caller already reports beats a
            # traceback, which would stop the walk and leave every later
            # module unchecked.
            return "; ".join(names), None
        if not isinstance(document, dict):
            return "; ".join(names), None
        source = document.get("source")
        if not isinstance(source, str):
            return "; ".join(names), None
        cites.append(source)
    return "; ".join(names), "; ".join(cites)


def module_tables(path: pathlib.Path) -> Iterator[tuple[str, str, str, str | None]]:
    """``(name, banner, data file, its citation)`` per module-level table.

    The last two are empty and ``None`` for a table written out in the module,
    which is most of them.

    A table is a literal collection of more than one entry, a call that builds
    one, or a comprehension that reads one out of a packaged data file; a
    scalar is a cited number and the errata registry covers it.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    for node in ast.parse(text).body:
        names: list[str] = []
        value: ast.expr | None = None
        if isinstance(node, ast.Assign):
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names, value = [node.target.id], node.value
        if value is None:
            continue
        if isinstance(value, (ast.Tuple, ast.List, ast.Set)):
            size = len(value.elts)
        elif isinstance(value, ast.Dict):
            size = len(value.keys)
        elif isinstance(value, (ast.Call, ast.DictComp, ast.ListComp, ast.SetComp)):
            # A call or a comprehension builds its entries at import, so how
            # many there are cannot be counted here. Both are tables.
            size = 2
        else:
            continue
        if size < 2:
            continue
        for name in names:
            if not name.lstrip("_").isupper():
                continue
            banner = banner_above(lines, node.lineno - 1)
            data_file, cited = data_citation(banner)
            whole = f"{banner} {cited}".strip() if cited else banner
            yield name, whole, data_file, cited


def registry_problems() -> list[Problem]:
    """The registry against the tree: banners, the census, and stale entries."""
    problems: list[Problem] = []
    banners: dict[tuple[str, str], str] = {}
    census: set[tuple[str, str]] = set()
    for path in sorted(PACKAGE.rglob("*.py")):
        module = path.relative_to(PACKAGE).as_posix()
        for name, banner, data_file, cited in module_tables(path):
            banners[module, name] = banner
            if data_file and cited is None:
                problems.append(
                    Problem(
                        f"{module}::{name}",
                        f"names the data file {data_file!r}, which is either "
                        "not there or does not say which page it came from",
                    )
                )
            if banner and BOOK_OR_PAPER.search(banner) and LOCATOR.search(banner):
                census.add((module, name))

    for key, reason in SOURCED.items():
        registered = banners.get(key)
        where = f"{key[0]}::{key[1]}"
        # A constant built from several tables registers them joined by "; ",
        # and every one of them has to resolve: checking only the first would
        # let five of six designations into the tree unparsed and absent from
        # the bibliography, which is what happened while the solids catalogue
        # grew from one book to six.
        for entry in reason.split(";"):
            cite = entry.split(",")[0].strip()
            try:
                parsed = references.parse(cite)
            except ValueError as error:
                problems.append(
                    Problem(where, f"names {cite!r}, which does not parse: {error}")
                )
            else:
                problems.extend(
                    Problem(where, detail)
                    for detail in _bibliography_problems(cite, parsed)
                )
        if registered is None:
            problems.append(
                Problem(where, f"is registered as {reason!r} and no longer exists")
            )
            continue
        if key in PAGE_UNKNOWN:
            continue
        if not BANNER_PDF_PAGE.search(registered):
            problems.append(
                Problem(where, "cites no PDF page; a transcribed table names both")
            )
        if not BANNER_FOLIO.search(registered):
            problems.append(
                Problem(where, "cites no printed folio; a transcribed table names both")
            )

    for key, reason in PAGE_UNKNOWN.items():
        where = f"{key[0]}::{key[1]}"
        if key not in SOURCED:
            problems.append(
                Problem(
                    where, f"is allowed a missing page ({reason}) and is not in SOURCED"
                )
            )
            continue
        banner = banners.get(key, "")
        if BANNER_PDF_PAGE.search(banner) and BANNER_FOLIO.search(banner):
            problems.append(
                Problem(
                    where,
                    f"now cites its page, so the PAGE_UNKNOWN line ({reason}) must go",
                )
            )

    for key, reason in NOT_TRANSCRIBED.items():
        where = f"{key[0]}::{key[1]}"
        if key in SOURCED:
            problems.append(
                Problem(where, f"is in SOURCED and is also declared {reason!r}")
            )
        elif key not in census:
            problems.append(
                Problem(
                    where,
                    f"is declared to transcribe nothing ({reason}) and the census "
                    "no longer reaches it, so the line must go",
                )
            )

    problems.extend(
        Problem(
            f"{module}::{name}",
            "is transcribed from a book or a paper and is not in SOURCED",
        )
        for module, name in sorted(census - set(SOURCED) - set(NOT_TRANSCRIBED))
    )
    return problems


def record_problems() -> list[Problem]:
    """Every published record whose ``source`` does not say where it was read."""
    problems: list[Problem] = []
    for module_name, exported, record in published_records():
        source = getattr(record, SOURCE_FIELD, "")
        name = getattr(record, "name", type(record).__name__)
        where = f"{module_name}.{exported} -> {name!r}"
        problems.extend(
            Problem(where, detail) for detail in citation_problems(str(source))
        )
    return problems


def main() -> int:
    """Report every published value that does not name its page."""
    parser = argparse.ArgumentParser(
        description="Provenance gate for published values."
    )
    parser.parse_args()

    problems = record_problems() + registry_problems()
    if not problems:
        registered = len(SOURCED)
        records = sum(1 for _ in published_records())
        print(
            f"{records} published record(s) cite a page in the errata grammar, and "
            f"{registered} transcribed table(s) name their PDF page and printed folio."
        )
        return 0
    print("::error::a published value does not say which page it was read on")
    for problem in problems:
        print(f"  {problem.where}: {problem.detail}")
    print(
        "  -> write the source as '<Document> <Table>, PDF page N (printed p. M)', "
        "join several with '; ', and register a transcribed table in SOURCED at the "
        "top of scripts/check_published_sources.py."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
