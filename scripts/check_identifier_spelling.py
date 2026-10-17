#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Fail on a public identifier spelled the British way, or on ``insitu``.

The library is written in American English
(docs/contributing/naming.md#n32), and an identifier is the one place where
the spelling is not a matter of style: a caller types it, and a caller who
wrote ``center_frequency`` on one function and gets a ``TypeError`` from the
next one, which wanted ``centre_frequency``, has learned nothing about
acoustics. The names had drifted into both
spellings, ``acoustic_centre`` beside ``center_frequencies``, ``programme``
beside ``program_loudness``, ``normalised_difference`` beside
``NORMALIZED_IMPEDANCE_PA_S_M``, and nothing looked at the whole API. This
does.

The surface is the one a caller reaches, walked on the imported package for
the reason ``check_parameter_units.py`` gives: every public module path, every
name in the ``__all__`` of a public module, the methods, properties and
fields of the classes among them, the parameters of every callable, the
members and the string values of every published :class:`~enum.Enum`, and
the strings a caller types as values: every choice of a ``Literal`` a
parameter or a field is annotated with, every string a parameter defaults to
(a ``location="centre"`` is one of the choices, whatever its annotation),
every key of a published table, written as an identifier
(``IEC61094_3_TABLE_1["acoustic_centres"]``) or as words (``"boundary
centre"``), and every string of a published tuple or frozenset of strings
(``PERIOD_MODELS``, the list a ``model`` is checked against). The keys of a
catalogue (``"<table>/<row>"``) are the one exception: their row names are
the names a page prints, and are left to the page they transcribe.

A name is broken into its words (at underscores, spaces, hyphens, digits and
case changes, so ``AcousticCentre`` is ``Acoustic`` and ``Centre``), and a
word is read twice. It is reported when it holds one of the British forms of
:data:`STEMS` (``centre``, ``programme``, ``tyre``), and otherwise when it
takes a British ending of :data:`SHAPES`, which closes whole families no list
of words could: any ``-ise`` verb, any ``-yse`` verb, any ``-our`` noun and
any ``-tre`` or ``-bre`` noun, the American words of the same shape aside
(``noise``, ``contour``, ``timbre``). The fix is reported with each. The
words are looked at one by one, so ``SlitResonator`` does not read as a
``litre``. The same walk holds ``in situ`` to one spelling: the word
``insitu`` is reported as ``in_situ``, the form every other in-situ name of
the library already takes.

Two escape hatches, both small on purpose. :data:`SANCTIONED` holds the one
word whose British form is the library's spelling: ``catalogue``, an American
variant too, used the same way everywhere, and part of the file format a user
writes (the ``"catalogue"`` key, ``phonometry-catalogue`` and the schema URN
``urn:phonometry:schema:catalogue:1``), so renaming it would break every file
already written. :data:`EXEMPT` holds a value printed by a source, keyed by
module, qualified name and value, each with its reason: a string a reader
compares against the page it came from keeps the spelling of that page.
Either entry that no public name needs any more is reported as stale.
"""

from __future__ import annotations

import argparse
import ast
import dataclasses
import enum
import inspect
import re
import sys
import typing
from types import MappingProxyType
from typing import TYPE_CHECKING, NamedTuple

import check_parameter_units as walk

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping


class Stem(NamedTuple):
    """One British form, the pattern that finds it in a word, and its fix."""

    british: str
    pattern: str
    american: str


def _ise(stem: str) -> Stem:
    """A verb spelled ``-ise`` in British English and ``-ize`` in American.

    The endings are listed, rather than the bare stem, because the bare stem
    is often a word of its own in both spellings: ``realistic``, ``organism``
    and ``optimism`` are not ``realise``, ``organise`` and ``optimise``.
    """
    return Stem(
        f"{stem}is",
        rf"{stem}is(?:e|ed|er|ers|es|ing|ation|ations|able)",
        f"{stem}iz",
    )


def _ll(stem: str, american: str) -> Stem:
    """A verb ending in an unstressed ``-l`` that British English doubles.

    Only the inflections double (``modelled``, ``cancelling``,
    ``traveller``), so ``cancellation``, ``initially`` and ``totally``, which
    American English writes with two ``l`` as well, are left alone.
    """
    return Stem(f"{stem}ll", rf"{stem}ll(?:ed|ing|er|ers)", american)


#: The British forms a public identifier may not hold, with the American
#: spelling that replaces each, found anywhere in a word. The first twenty
#: are the ones the audit of the 4.0 surface found in published names; the
#: rest are single words whose British form is no ending :data:`SHAPES`
#: reads (``tyre``, ``aerofoil``, ``kerb``) or that the shapes would spell
#: wrong (``practise`` is ``practice``, not ``practize``).
STEMS: tuple[Stem, ...] = (
    # ``centring`` too, which is no ``-tre`` word at its end.
    Stem("centre", r"centr(?:e|ing)", "center"),
    # ``programmed`` and ``programmer`` are American spellings too.
    Stem("programme", r"programme(?![dr])", "program"),
    Stem("normalis", r"normalis", "normaliz"),
    Stem("fibre", r"fibre", "fiber"),
    Stem("storey", r"storey", "story (plural stories)"),
    Stem("vapour", r"vapour", "vapor"),
    _ll("mode", "model (modeling, modeled)"),
    Stem("behaviour", r"behaviour", "behavior"),
    Stem("neighbour", r"neighbour", "neighbor"),
    Stem("favour", r"favour", "favor"),
    Stem("colour", r"colour", "color"),
    Stem("urbanis", r"urbanis", "urbaniz"),
    Stem("draught", r"draught", "draft"),
    Stem("litre", r"litre", "liter"),
    Stem("metre", r"metre", "meter"),
    Stem("aluminium", r"aluminium", "aluminum"),
    _ise("optim"),
    # ``analysis`` and ``analyses`` are nouns in both spellings.
    Stem("analys", r"analys(?:ed|er|ers|ing|e(?!s))", "analyz"),
    _ise("real"),
    _ise("organ"),
    Stem("practis", r"practis(?:e|ed|es|ing)", "practic"),
    Stem("emphasis", r"emphasis(?:e|ed|es|ing)", "emphasiz"),
    Stem("labour", r"labour", "labor"),
    Stem("odour", r"odour", "odor"),
    Stem("harbour", r"harbour", "harbor"),
    Stem("humour", r"humour", "humor"),
    Stem("rigour", r"rigour", "rigor"),
    Stem("tumour", r"tumour", "tumor"),
    _ll("labe", "label (labeled, labeling)"),
    _ll("leve", "level (leveled, leveling)"),
    _ll("signa", "signal (signaled, signaling)"),
    _ll("trave", "travel (traveled, traveling)"),
    _ll("cance", "cancel (canceled, canceling)"),
    _ll("channe", "channel (channeled, channeling)"),
    _ll("fue", "fuel (fueled, fueling)"),
    _ll("tunne", "tunnel (tunneled, tunneling)"),
    _ll("tota", "total (totaled, totaling)"),
    _ll("dia", "dial (dialed, dialing)"),
    _ll("equa", "equal (equaled, equaling)"),
    _ll("funne", "funnel (funneled, funneling)"),
    _ll("pane", "panel (paneled, paneling)"),
    _ll("spira", "spiral (spiraled, spiraling)"),
    _ll("swive", "swivel (swiveled, swiveling)"),
    _ll("riva", "rival (rivaled, rivaling)"),
    _ll("initia", "initial (initialed, initialing)"),
    _ll("counse", "counsel (counseled, counseling)"),
    Stem("-lment", r"(?:enrol|instal|fulfil)ment", "-llment"),
    Stem("-lful", r"(?:skil|wil)ful", "-llful"),
    # At the start of a word, so ``polystyrene`` is not a ``tyre``.
    Stem("tyre", r"^tyre", "tire"),
    Stem("kerb", r"^kerb", "curb"),
    # The dog keeps its name in American English too.
    Stem("grey", r"grey(?!hound)", "gray"),
    Stem("defence", r"defence", "defense"),
    Stem("licence", r"licence", "license"),
    Stem("offence", r"offence", "offense"),
    Stem("pretence", r"pretence", "pretense"),
    Stem("ageing", r"ageing", "aging"),
    Stem("dgement", r"dgement", "dgment"),
    # ``dialogue``, ``prologue`` and ``monologue`` are American as well;
    # ``analog`` and ``catalog`` are the American forms of their two words,
    # and ``catalogue`` is sanctioned below.
    Stem("analogue", r"analogue", "analog"),
    Stem("artefact", r"artefact", "artifact"),
    Stem("manoeuvr", r"manoeuvr", "maneuver"),
    Stem("louvre", r"louvre", "louver"),
    Stem("meagre", r"meagre", "meager"),
    Stem("aeroplane", r"aeroplane", "airplane"),
    Stem("aerofoil", r"aerofoil", "airfoil"),
    Stem("sulph", r"sulph", "sulf"),
    Stem("mould", r"mould", "mold"),
    Stem("plough", r"plough", "plow"),
    Stem("sceptic", r"sceptic", "skeptic"),
    Stem("speciality", r"specialit(?:y|ies)", "specialty"),
    # The unit, so ``programme`` and ``diagrammed`` are not one.
    Stem("gramme", r"^(?:kilo|milli|micro|nano|centi|deci)?grammes?$", "gram"),
    Stem("maths", r"^maths$", "math"),
    Stem("anaesth", r"anaesth", "anesth"),
    Stem("haem", r"haem", "hem"),
    Stem("paed", r"paed", "ped"),
    Stem("oesoph", r"oesoph", "esoph"),
    Stem("oedem", r"oedem", "edem"),
    Stem("foet", r"foet", "fet"),
    # Not British, but the same class: one concept, two spellings in names.
    Stem("insitu", r"insitu", "in_situ"),
)

_COMPILED = tuple((stem, re.compile(stem.pattern)) for stem in STEMS)


class Shape(NamedTuple):
    """A British ending a whole family of words takes, and its American one.

    ``pattern`` matches a whole word that ends in the British form, inflected
    or not, and names the part before the ending ``root`` and the inflection
    ``suffix``; the American word is ``root + american`` followed by the
    inflection, rewritten by ``inflections`` where American English writes it
    differently (``centred`` is ``centered``). A word of the family that is
    American English too is listed in ``american_words`` (whole, or after a
    prefix of :data:`_PREFIXES`) or ends in one of ``american_endings``; either
    is read on the word as written and on its dictionary form.
    """

    british: str
    american: str
    pattern: re.Pattern[str]
    american_words: frozenset[str] = frozenset()
    american_endings: tuple[str, ...] = ()
    inflections: Mapping[str, str] = MappingProxyType({})


#: Prefixes an American word of a family keeps its spelling under
#: (``imprecise``, ``uncompromising``).
_PREFIXES = (
    "",
    "un",
    "re",
    "pre",
    "im",
    "in",
    "mis",
    "dis",
    "de",
    "non",
    "over",
    "under",
    "sub",
    "super",
    "counter",
    "self",
)

#: The British endings no list of words can close: any ``-ise`` verb (and
#: its ``-isation``), any ``-yse`` verb, any ``-our`` noun and any ``-tre``
#: or ``-bre`` noun is reported, unless it is one of the American words of
#: the same shape. The lists hold whole words on purpose: ``rise`` is an
#: American word, and ``polarise`` ends in it.
SHAPES: tuple[Shape, ...] = (
    Shape(
        "ise",
        "iz",
        # No ``-ises``: in a name it is the plural of an ``-is`` noun
        # (``metropolises``, ``trellises``), which is American English too,
        # and a British verb shows in its other forms (``-ise``, ``-ised``).
        re.compile(
            r"(?P<root>[a-z]+)is"
            r"(?P<suffix>e|ed|er|ers|ing|able|ation|ations)"
        ),
        frozenset(
            {
                "rise",
                "arise",
                "sunrise",
                "uprise",
                "moonrise",
                "enterprise",
                "surprise",
                "comprise",
                "reprise",
                "apprise",
                "precise",
                "concise",
                "excise",
                "incise",
                "exercise",
                "circumcise",
                "premise",
                "promise",
                "compromise",
                "demise",
                "chemise",
                "expertise",
                "advertise",
                "chastise",
                "treatise",
                "mortise",
                "despise",
                "merchandise",
                "paradise",
                "franchise",
                "enfranchise",
                "anise",
                "valise",
                "cerise",
                "surmise",
                "exorcise",
                "disable",
                # ``miser``.
                "mise",
            }
        ),
        ("aise", "oise", "uise", "vise", "wise"),
    ),
    Shape(
        "lyse",
        "lyz",
        # ``analyses`` and ``paralyses`` are plural nouns in both spellings.
        re.compile(r"(?P<root>[a-z]*)lys(?P<suffix>e|ed|er|ers|ing)"),
        frozenset({"lyse"}),
    ),
    Shape(
        "our",
        "or",
        re.compile(
            r"(?P<root>[a-z]*)our"
            r"(?P<suffix>|s|ed|ing|er|ers|able|ably|ite|ites|ful|less)"
        ),
        frozenset(
            {
                "our",
                "dour",
                "scour",
                "devour",
                "velour",
                "glamour",
                "troubadour",
                "pompadour",
                "parkour",
            }
        ),
        ("hour", "four", "pour", "tour", "your", "flour", "sour", "amour"),
    ),
    Shape(
        "tre",
        "ter",
        re.compile(r"(?P<root>[a-z]*)tre(?P<suffix>|s|d)"),
        frozenset({"hatred"}),
        inflections=MappingProxyType({"d": "ed"}),
    ),
    Shape(
        "bre",
        "ber",
        re.compile(r"(?P<root>[a-z]*)bre(?P<suffix>|s|d)"),
        # ``timbre`` is the American word of acoustics too, never ``timber``.
        frozenset({"timbre", "macabre"}),
        ("bred",),
        MappingProxyType({"d": "ed"}),
    ),
)


def _american(form: str, shape: Shape) -> bool:
    """Whether ``form`` is an American word of the family of ``shape``."""
    if form.endswith(shape.american_endings):
        return True
    return any(
        form.startswith(prefix) and form[len(prefix) :] in shape.american_words
        for prefix in _PREFIXES
    )


def shape_form(word: str) -> Stem | None:
    """The British ending a lowercase word ends in, as the word and its fix."""
    for shape in SHAPES:
        match = shape.pattern.fullmatch(word)
        if match is None:
            continue
        root, suffix = match["root"], match["suffix"]
        if _american(word, shape) or _american(root + shape.british, shape):
            return None
        inflected = shape.inflections.get(suffix, suffix)
        return Stem(word, shape.pattern.pattern, root + shape.american + inflected)
    return None


#: A word whose British form is the library's spelling, and why.
SANCTIONED: dict[str, str] = {
    "catalogue": (
        "the spelling of the versioned catalogue file format a user writes "
        "(the 'catalogue' key, phonometry-catalogue and the schema URN "
        "urn:phonometry:schema:catalogue:1); an American variant too, used "
        "the same way in every name"
    ),
}

#: Where a name breaks into words: runs of capitals before a capitalized
#: word (``EQ`` of ``EQFilter``), capitalized and lowercase words, runs of
#: capitals and runs of digits. Underscores, spaces and hyphens fall away.
_WORDS = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+")

_PRINTED_SURFACE = (
    "the road surface as Directive 2002/49/EC Annex II, Appendix F, Table F-4 "
    "prints it, as replaced by Commission Delegated Directive (EU) 2021/1226, "
    "Annex point (19)(b) (OJ L 269/97-98, 28.7.2021; the row 'Optimised "
    "brushed down concrete' is on L 269/98); the enum value is the row name a "
    "reader matches against that table, and the member name is American"
)

_PRINTED_MATERIAL = (
    "the material as Norton and Karczub (2003) Table 3.1 prints it (PDF page "
    "261, printed page 241: 'Aluminium'), lower-cased: the table is keyed by "
    "the row name of "
    "solids.PUBLISHED_PLATEAU_DATA['norton-karczub-2003-table-3-1/aluminium'], "
    "and a catalogue row keeps the name its page prints"
)

_PRINTED_REPORT_ITEM = (
    "item i) of the test report as ISO 3382-1:2009 Clause 9.2 prints it (BS "
    "EN ISO 3382-1:2009, PDF page 19, printed page 11: 'for theatres, whether "
    "the safety curtain or decorative curtains were up or down'); the tuple "
    "lists the items a) to o) a report is checked against, and this one keeps "
    "the words of the page"
)

_SURNAME = (
    "the surname of Doutres et al. (2007), after whom the criterion is named, "
    "as Allard and Atalla 2e Sect. 11.3.4 prints it (PDF page 259, printed "
    "page 253); a name, not a '-tre' word"
)

#: A string a published source prints, keyed by module, qualified name and
#: the string itself, with the reason it keeps the source's spelling.
EXEMPT: dict[tuple[str, str, str], str] = {
    (
        "phonometry.environment.sources.cnossos_road",
        "RoadSurface.OPTIMIZED_BRUSHED_DOWN_CONCRETE",
        "optimised brushed down concrete",
    ): _PRINTED_SURFACE,
    (
        "phonometry.building.prediction.panel_transmission",
        "PLATEAU_MATERIALS",
        "aluminium",
    ): _PRINTED_MATERIAL,
    (
        "phonometry.building.prediction.panel_transmission",
        "plateau_transmission_loss(material)",
        "aluminium",
    ): _PRINTED_MATERIAL,
    (
        "phonometry.environment.sources.cnossos_road",
        "road_surface_coefficients(surface)",
        "optimised brushed down concrete",
    ): _PRINTED_SURFACE,
    (
        "phonometry.environment.sources.cnossos_road",
        "road_rolling_noise(surface)",
        "optimised brushed down concrete",
    ): _PRINTED_SURFACE,
    (
        "phonometry.environment.sources.cnossos_road",
        "road_propulsion_noise(surface)",
        "optimised brushed down concrete",
    ): _PRINTED_SURFACE,
    (
        "phonometry.environment.sources.cnossos_road",
        "road_vehicle_sound_power(surface)",
        "optimised brushed down concrete",
    ): _PRINTED_SURFACE,
    (
        "phonometry.environment.sources.cnossos_road",
        "road_source_power(surface)",
        "optimised brushed down concrete",
    ): _PRINTED_SURFACE,
    (
        "phonometry.room.auditorium",
        "TEST_REPORT_ITEMS",
        "for theatres, whether the safety curtain or decorative curtains were "
        "up or down",
    ): _PRINTED_REPORT_ITEM,
    (
        "phonometry.materials.absorbers.porous",
        "LIMP_FRAME_CRITERIA",
        "doutres",
    ): _SURNAME,
    (
        "phonometry.materials.absorbers.porous",
        "check_limp_frame(criterion)",
        "doutres",
    ): _SURNAME,
    (
        "phonometry.materials.absorbers.porous",
        "LimpFrameCheck(criterion)",
        "doutres",
    ): _SURNAME,
}


class Finding(NamedTuple):
    """One public identifier or value, the British form it holds, and where."""

    module: str
    qualname: str
    name: str
    where: str
    kind: str


def words(name: str) -> list[str]:
    """The words of an identifier or a value, lowercase, in order."""
    return [word.lower() for word in _WORDS.findall(name)]


def sanctioned(word: str) -> str | None:
    """The entry of :data:`SANCTIONED` a lowercase word is, singular or plural."""
    for form in (word, word.removesuffix("s")):
        if form in SANCTIONED:
            return form
    return None


def british_forms(name: str, used: set[str] | None = None) -> list[Stem]:
    """The British forms ``name`` holds, word by word, sanctioned words aside.

    A word is read against :data:`STEMS` first, and against :data:`SHAPES`
    only when no stem names it, so ``centres`` is reported once.

    ``used`` collects the sanctioned words met on the way, so a sanctioned
    spelling no public name writes any more is reported as stale.
    """
    found: list[Stem] = []
    for word in words(name):
        allowed = sanctioned(word)
        if allowed is not None:
            if used is not None:
                used.add(allowed)
            continue
        stems = [stem for stem, pattern in _COMPILED if pattern.search(word)]
        shaped = None if stems else shape_form(word)
        for stem in (*stems, *([shaped] if shaped is not None else [])):
            if stem not in found:
                found.append(stem)
    return found


def _namespace(obj: object) -> Mapping[str, object]:
    """The globals an annotation of ``obj`` is written against."""
    namespace = getattr(obj, "__globals__", None)
    if namespace is not None:
        return typing.cast("Mapping[str, object]", namespace)
    module = sys.modules.get(getattr(obj, "__module__", "") or "")
    return vars(module) if module is not None else {}


def _is_literal(node: ast.expr) -> bool:
    """Whether an annotation node names ``Literal``."""
    return (isinstance(node, ast.Name) and node.id == "Literal") or (
        isinstance(node, ast.Attribute) and node.attr == "Literal"
    )


def literal_values(
    annotation: object,
    namespace: Mapping[str, object],
    seen: set[int] | None = None,
) -> Iterator[str]:
    """The strings a ``Literal`` inside ``annotation`` lets a caller write.

    An annotation is a string under ``from __future__ import annotations``,
    so it is parsed rather than evaluated, and a name in it that refers to an
    alias (``model: BuildingModel``) is followed to the alias it names.
    """
    seen = set() if seen is None else seen
    if id(annotation) in seen:
        return
    seen.add(id(annotation))
    if isinstance(annotation, str):
        try:
            tree = ast.parse(annotation, mode="eval")
        except SyntaxError:
            return
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript) and _is_literal(node.value):
                for value in ast.walk(node.slice):
                    if isinstance(value, ast.Constant) and isinstance(value.value, str):
                        yield value.value
            elif isinstance(node, ast.Name) and node.id in namespace:
                target = namespace[node.id]
                if not (inspect.isclass(target) or inspect.ismodule(target)):
                    yield from literal_values(target, namespace, seen)
        return
    alias = getattr(annotation, "__value__", None)
    if alias is not None:
        yield from literal_values(alias, namespace, seen)
        return
    if typing.get_origin(annotation) is typing.Literal:
        yield from (a for a in typing.get_args(annotation) if isinstance(a, str))
        return
    for argument in typing.get_args(annotation):
        yield from literal_values(argument, namespace, seen)


class _Slot(NamedTuple):
    """One public parameter or field: where it is, its annotation, its default."""

    qualname: str
    name: str
    annotation: object
    default: object
    owner: object


def _slots(name: str, obj: object) -> Iterator[_Slot]:
    """Every parameter of a callable and of the methods a class publishes, and
    every field of a dataclass or a named tuple.
    """
    empty = inspect.Parameter.empty
    for qualname, target in walk._members(name, obj):
        if not callable(target):
            continue
        try:
            signature = inspect.signature(target)
        except (TypeError, ValueError):
            continue
        for parameter in signature.parameters.values():
            yield _Slot(
                qualname,
                parameter.name,
                parameter.annotation,
                parameter.default,
                target,
            )
    if inspect.isclass(obj):
        if dataclasses.is_dataclass(obj):
            for field in dataclasses.fields(obj):
                yield _Slot(name, field.name, field.type, empty, obj)
        for field_name, annotation in getattr(obj, "__annotations__", {}).items():
            if field_name in getattr(obj, "_fields", ()):
                yield _Slot(name, field_name, annotation, empty, obj)


def _strings(value: object) -> tuple[str, ...]:
    """A string default, or the strings of a tuple of them, or nothing."""
    if isinstance(value, str):
        return (value,)
    if isinstance(value, tuple) and all(isinstance(item, str) for item in value):
        return value
    return ()


def table_keys(value: object, depth: int = 0) -> Iterator[str]:
    """The string keys of a published table, nested ones too.

    A key a caller types is held to the spelling whether it is written as an
    identifier (``"acoustic_centers"``) or as words (``"boundary center"``).
    A catalogue's ``"<table>/<row>"`` keys are the one exception: their row
    names are the names a page prints, and are left to it.
    """
    if depth > 3 or not isinstance(value, dict | MappingProxyType):
        return
    for key, item in value.items():
        if isinstance(key, str) and "/" not in key:
            yield key
        yield from table_keys(item, depth + 1)


def constant_items(value: object) -> tuple[str, ...]:
    """The strings of a published tuple or frozenset that holds only strings.

    Such a constant is the list of choices a parameter checks against
    (``PERIOD_MODELS``), or the phrases a source prints; a choice is typed by
    the caller, and a printed phrase that keeps a British spelling is exempt
    by location, like any other print.
    """
    if not isinstance(value, tuple | frozenset) or not value:
        return ()
    if not all(isinstance(item, str) for item in value):
        return ()
    return tuple(sorted(value)) if isinstance(value, frozenset) else value


def public_values() -> Iterator[Finding]:
    """Every string a caller types as a value.

    The choices of a ``Literal``, the strings a parameter defaults to, the
    values of an enum, the keys of a published table and the strings of a
    published tuple or frozenset of strings.
    """
    seen: set[tuple[str, str, str]] = set()

    def once(key: tuple[str, str, str], where: str, kind: str) -> Iterator[Finding]:
        if key not in seen:
            seen.add(key)
            yield Finding(*key, where, kind)

    for entry, constant in walk.public_constants():
        for name in table_keys(constant):
            yield from once((entry.module, entry.name, name), entry.where, "table key")
        for item in constant_items(constant):
            key = (entry.module, entry.name, item)
            yield from once(key, entry.where, "constant item")
    for module_name, module in walk.public_modules():
        for exported in getattr(module, "__all__", ()):
            obj = getattr(module, exported, None)
            if obj is None or inspect.ismodule(obj):
                continue
            home = getattr(obj, "__module__", module_name) or module_name
            if inspect.isclass(obj) and issubclass(obj, enum.Enum):
                for member in obj:
                    if isinstance(member.value, str):
                        member_key = (home, f"{exported}.{member.name}", member.value)
                        yield from once(member_key, walk._where(obj), "enum value")
            for slot in _slots(exported, obj):
                where = walk._where(slot.owner)
                owner_home = getattr(slot.owner, "__module__", home) or home
                qualname = f"{slot.qualname}({slot.name})"
                if slot.annotation is not inspect.Parameter.empty:
                    namespace = _namespace(slot.owner)
                    for choice in literal_values(slot.annotation, namespace):
                        choice_key = (owner_home, qualname, choice)
                        yield from once(choice_key, where, "Literal value")
                for default in _strings(slot.default):
                    default_key = (owner_home, qualname, default)
                    yield from once(default_key, where, "default value")


def public_identifiers(
    parameters: Iterable[walk.Parameter] | None = None,
) -> Iterator[Finding]:
    """Every public module path and every name a caller writes."""
    for module_name, _ in walk.public_modules():
        yield Finding(module_name, "", module_name, module_name, "module")
    for entry in walk.public_names(parameters):
        yield Finding(entry.module, entry.qualname, entry.name, entry.where, "name")


def misspelled(
    parameters: Iterable[walk.Parameter] | None = None,
) -> tuple[list[tuple[Finding, list[Stem]]], list[object]]:
    """The identifiers and values that hold a British form, and stale exemptions.

    An exemption is stale when the value it keys is gone or no longer holds a
    British form, and a sanctioned word is stale when no public name writes it.
    """
    found: list[tuple[Finding, list[Stem]]] = []
    used: set[tuple[str, str, str]] = set()
    words_met: set[str] = set()
    for entry in (*public_identifiers(parameters), *public_values()):
        forms = british_forms(entry.name, words_met)
        if not forms:
            continue
        key = (entry.module, entry.qualname, entry.name)
        if key in EXEMPT:
            used.add(key)
            continue
        found.append((entry, forms))
    stale: list[object] = [key for key in EXEMPT if key not in used]
    stale.extend(word for word in SANCTIONED if word not in words_met)
    return found, stale


def main() -> int:
    """Report every public identifier spelled the British way."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    found, stale = misspelled()
    if not (found or stale):
        print(
            "Every public identifier, and every value a caller types (a Literal "
            "choice, a default, an enum value, a table key, a string of a "
            "published tuple), is spelled in American English, and in situ is "
            "written in_situ."
        )
        return 0
    if found:
        print("::error::a public identifier is spelled the British way")
        print(f"{len(found)} public identifier(s) or value(s) hold a British form:")
        for entry, forms in sorted(found):
            if entry.kind == "module":
                dotted = entry.name
            elif entry.kind == "table key":
                dotted = f"{entry.qualname}[{entry.name!r}]"
            elif entry.kind == "constant item":
                dotted = f"{entry.qualname} holds {entry.name!r}"
            elif entry.kind != "name":
                dotted = f"{entry.qualname} = {entry.name!r}"
            else:
                dotted = ".".join(p for p in (entry.qualname, entry.name) if p)
            fixes = ", ".join(f"{s.british} -> {s.american}" for s in forms)
            print(f"  {dotted} [{entry.kind}] ({fixes})  <- {entry.where}")
        print(
            "  -> spell the identifier in American English and move every "
            "caller with it; a string a published source prints goes in "
            "EXEMPT at the top of scripts/check_identifier_spelling.py, keyed "
            "by where it is, with its reason."
        )
    for key in stale:
        print(
            "::error::an entry at the top of scripts/check_identifier_spelling.py "
            f"lists {key!r}, which no public name needs any more"
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
