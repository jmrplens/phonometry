#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Generate the Starlight API reference from the phonometry docstrings.

Renders every public name as committed Markdown pages under
``site/src/content/docs/reference/api/`` (one page per public module, grouped
by the sections in ``scripts/api_taxonomy.py``) plus the sidebar fragment
``site/src/generated/api-sidebar.mjs``. English only by decision; Spanish
routes are served by the Starlight locale fallback.

Stdlib only (``inspect``, ``importlib``, ``ast``, ``re``) plus importing
phonometry itself. Output is byte-deterministic: members are sorted, nothing
is timestamped, and no environment-dependent text is embedded. CI fails when
the committed pages drift from source (see .github/workflows/python-app.yml).

Regenerate with ``make api-docs``.

The docstring dialect handled here is the repo's reST field-list style:
``:param:``/``:type:``/``:return:``/``:rtype:``/``:raises:``/``:warns:``/
``:ivar:``/``:vartype:`` fields, ``:class:``/``:func:``/etc. cross-reference
roles, ````literal```` double-backtick spans, ``.. note::`` directives,
``::`` literal blocks and math (the ``:math:`` role and the ``.. math::``
directive, emitted as ``$...$``/``$$...$$`` for the site's KaTeX pipeline;
blank lines inside one directive separate equations, as in Sphinx). A
docstring that does not parse cleanly is degraded to a verbatim block and
reported, never fatal.
"""

from __future__ import annotations

import ast
import dataclasses
import functools
import importlib
import importlib.util
import inspect
import itertools
import json
import re
import shutil
import sys
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, TypeAliasType, get_origin, get_overloads

from api_taxonomy import (
    OBJECT_MODULE_OVERRIDES,
    PRIVATE_MODULE_TOPICS,
    SECTIONS,
    Section,
    is_documented_module,
    is_private_module,
    module_section,
    public_names,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import ModuleType

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "site" / "src" / "content" / "docs" / "reference" / "api"
SIDEBAR_PATH = ROOT / "site" / "src" / "generated" / "api-sidebar.mjs"

#: Site base path (GitHub Pages project site); links validator checks against it.
SITE_BASE = "/phonometry"
API_BASE = f"{SITE_BASE}/reference/api"

BANNER = (
    "> Auto-generated from the source docstrings by "
    "`scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand."
)

_FIELD_NAMES = (
    "param",
    "type",
    "return",
    "returns",
    "rtype",
    "raises",
    "raise",
    "ivar",
    "vartype",
    "warns",
)
_FIELD_RE = re.compile(r"^:(" + "|".join(_FIELD_NAMES) + r")(\s+[^:]*)?:\s?(.*)$")
#: Any line that looks like a reST field (to detect unsupported field names).
_FIELD_LIKE_RE = re.compile(r"^:(\w+)(\s+[^:`]*)?:(\s|$)")
#: A supported field starting mid-line inside another field's description
#: (roles like ``:func:`` are excluded by the field-name alternation).
_MIDLINE_FIELD_RE = re.compile(
    r"(?<=\s):(" + "|".join(_FIELD_NAMES) + r")(\s+[^:`]*)?:(\s|$)"
)
ROLE_RE = re.compile(
    r":(?:class|func|meth|mod|attr|data|obj|exc|ref|term):"
    r"`(~?)([^`<]+?)(?:\s*<([^>]+)>)?`"
)
_NOTE_RE = re.compile(r"^(\s*)\.\. note::\s?(.*)$")
_MATH_DIRECTIVE_RE = re.compile(r"^(\s*)\.\. math::\s?(.*)$")
_MATH_ROLE_RE = re.compile(r":math:`([^`]+)`")
#: A rendered inline-math span, once the role has become ``$...$``.
_INLINE_MATH_RE = re.compile(r"\$[^$]+\$")
_DIRECTIVE_RE = re.compile(r"^\s*\.\. \w+::")
#: Any reST role that survived rendering. ``ROLE_RE`` and ``_MATH_ROLE_RE``
#: consume the ones this generator understands, so whatever still matches is a
#: role no converter claims and it reaches the published page as literal text.
_LEAKED_ROLE_RE = re.compile(r":[a-z]+:`")
_HEX_ADDR_RE = re.compile(r"0x[0-9a-fA-F]+")

_MAX_CONST_REPR = 1500
_MAX_SIGNATURE_LINE = 76


# --------------------------------------------------------------------------
# Docstring parsing (reST field lists)
# --------------------------------------------------------------------------


@dataclasses.dataclass
class ParsedDoc:
    """A docstring split into prose and field-list entries (raw reST text)."""

    description: str = ""
    epilogue: str = ""
    params: list[tuple[str, str]] = dataclasses.field(default_factory=list)
    types: dict[str, str] = dataclasses.field(default_factory=dict)
    returns: str = ""
    rtype: str = ""
    raises: list[tuple[str, str]] = dataclasses.field(default_factory=list)
    warns: list[tuple[str, str]] = dataclasses.field(default_factory=list)
    ivars: list[tuple[str, str]] = dataclasses.field(default_factory=list)
    vartypes: dict[str, str] = dataclasses.field(default_factory=dict)
    issues: list[str] = dataclasses.field(default_factory=list)


def parse_docstring(doc: str) -> ParsedDoc:
    """Parse a reST field-list docstring into prose and typed fields.

    Never raises on malformed input: problems are recorded in ``issues`` and
    the caller degrades the docstring to a verbatim block.
    """
    parsed = ParsedDoc()
    desc_lines: list[str] = []
    epi_lines: list[str] = []
    seen_field = False
    field: tuple[str, str] | None = None  # (field name, argument)
    body: list[str] = []

    def flush() -> None:
        nonlocal field, body
        if field is None:
            return
        name, arg = field
        text = " ".join(part.strip() for part in body if part.strip())
        jammed = _MIDLINE_FIELD_RE.search(text)
        if jammed:
            # A field started mid-line (e.g. two ``:param:`` entries jammed
            # on one line) would otherwise be published inside the previous
            # field's description; fail loudly instead.
            parsed.issues.append(
                f"field {jammed.group(1)!r} starts mid-line inside the"
                f" description of {name!r}"
            )
        if name == "param":
            parsed.params.append((arg, text))
        elif name == "type":
            parsed.types[arg] = text
        elif name in ("return", "returns"):
            parsed.returns = f"{parsed.returns} {text}".strip()
        elif name == "rtype":
            parsed.rtype = text
        elif name in ("raises", "raise"):
            parsed.raises.append((arg, text))
        elif name == "warns":
            parsed.warns.append((arg, text))
        elif name == "ivar":
            parsed.ivars.append((arg, text))
        elif name == "vartype":
            parsed.vartypes[arg] = text
        field = None
        body = []

    for line in doc.splitlines():
        match = _FIELD_RE.match(line)
        if match:
            flush()
            seen_field = True
            field = (match.group(1), (match.group(2) or "").strip())
            body = [match.group(3)]
            continue
        like = _FIELD_LIKE_RE.match(line)
        if like and like.group(1) not in _FIELD_NAMES:
            flush()
            parsed.issues.append(f"unsupported field {like.group(1)!r}")
            continue
        if field is not None:
            if not line.strip() or line[:1].isspace():
                body.append(line)
                continue
            flush()
        target = epi_lines if seen_field else desc_lines
        target.append(line)

    flush()
    parsed.description = "\n".join(desc_lines).strip("\n")
    parsed.epilogue = "\n".join(epi_lines).strip("\n")
    return parsed


# --------------------------------------------------------------------------
# reST -> Markdown rendering
# --------------------------------------------------------------------------


@dataclasses.dataclass
class RoleStats:
    """Counts of cross-reference roles resolved to links vs degraded."""

    resolved: int = 0
    degraded: int = 0


def rest_roles_to_links(
    text: str, xref: dict[str, str], stats: RoleStats | None = None
) -> str:
    """Rewrite reST roles to intra-site Markdown links.

    ``:func:`leq``` becomes ``[`leq`](<page>#leq)`` when ``leq`` is in the
    xref map; unknown targets degrade to plain inline code.
    """

    def lookup(name: str) -> str | None:
        candidates = [name]
        if name.startswith("phonometry."):
            candidates.append(name.removeprefix("phonometry."))
        for candidate in candidates:
            url = xref.get(candidate)
            if url is not None:
                return url
        url = xref.get(name.rsplit(".", 1)[-1])
        if url is not None:
            return url
        # Attribute references (Class.attr): fall back to the owner's anchor.
        for candidate in candidates:
            while "." in candidate:
                candidate = candidate.rsplit(".", 1)[0]
                if candidate == "phonometry":
                    break
                url = xref.get(candidate)
                if url is not None:
                    return url
        return None

    def sub(match: re.Match[str]) -> str:
        tilde, name, explicit = match.group(1), match.group(2), match.group(3)
        # Role targets wrapped across source lines contain interior whitespace.
        target_name = re.sub(r"\s+", "", explicit or name)
        if explicit:
            # ":role:`display <target>`" form: keep the display wording.
            display = re.sub(r"\s+", " ", name).strip()
        else:
            display = re.sub(r"\s+", "", name)
        if tilde:
            display = display.rsplit(".", 1)[-1]
        url = lookup(target_name)
        if url is None:
            if stats is not None:
                stats.degraded += 1
            return f"`{display}`"
        if stats is not None:
            stats.resolved += 1
        return f"[`{display}`]({url})"

    return ROLE_RE.sub(sub, text)


def _consume_indented(lines: list[str], start: int, indent: int) -> int:
    """Return the index just past the block indented deeper than ``indent``."""
    i = start
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if len(line) - len(line.lstrip()) > indent:
            i += 1
            continue
        break
    return i


def _dedent_block(lines: list[str]) -> list[str]:
    indents = [len(line) - len(line.lstrip()) for line in lines if line.strip()]
    if not indents:
        return [line.strip() for line in lines]
    cut = min(indents)
    return [line[cut:] if line.strip() else "" for line in lines]


def rest_blocks_to_markdown(text: str, code: list[str]) -> str:
    """Convert reST block constructs to Markdown structure.

    ``.. note::`` directives become Starlight ``:::note`` asides, ``::``
    literal blocks become fenced code blocks and ``.. math::`` directives
    become ``$$`` display-math blocks (one per blank-line-separated equation,
    the Sphinx convention). Fenced code and math are stored in ``code`` and
    replaced by placeholders so the inline pass (roles, escaping) cannot
    touch them; ``_restore_code`` swaps them back.
    """
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        math = _MATH_DIRECTIVE_RE.match(line)
        if math:
            indent = len(math.group(1))
            end = _consume_indented(lines, i + 1, indent)
            content = _dedent_block(lines[i + 1 : end])
            if math.group(2).strip():
                content = [math.group(2).strip(), *content]
            # A directive nested in a list item keeps that item's indent, or
            # the ``$$`` block would close the list and orphan the prose
            # that follows the equation.
            pad = " " * indent
            for chunk in _split_on_blanks(content):
                # remark-math needs the whole block in one paragraph, so
                # the equation's physical lines are joined (TeX ignores
                # source line breaks anyway).
                tex = " ".join(part.strip() for part in chunk)
                token = f"\x00CODE{len(code)}\x00"
                code.append(f"{pad}$$\n{pad}{tex}\n{pad}$$")
                out.extend(["", token, ""])
            i = end
            continue
        note = _NOTE_RE.match(line)
        if note:
            indent = len(note.group(1))
            end = _consume_indented(lines, i + 1, indent)
            content = _dedent_block(lines[i + 1 : end])
            if note.group(2).strip():
                content = [note.group(2).strip(), *content]
            inner = rest_blocks_to_markdown("\n".join(content).strip("\n"), code)
            out.extend(["", ":::note", inner, ":::", ""])
            i = end
            continue
        stripped = line.rstrip()
        if stripped.endswith("::") and not _DIRECTIVE_RE.match(line):
            indent = len(line) - len(line.lstrip())
            end = _consume_indented(lines, i + 1, indent)
            block = _dedent_block(lines[i + 1 : end])
            while block and not block[0].strip():
                block.pop(0)
            while block and not block[-1].strip():
                block.pop()
            lead = stripped[:-2].rstrip()
            if lead:
                out.append(f"{lead}:")
            fence = "\n".join(["```text", *block, "```"])
            token = f"\x00CODE{len(code)}\x00"
            code.append(fence)
            out.extend(["", token, ""])
            i = end
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


def _split_on_blanks(lines: list[str]) -> list[list[str]]:
    """Split ``lines`` into runs of non-blank lines."""
    chunks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.strip():
            current.append(line)
        elif current:
            chunks.append(current)
            current = []
    if current:
        chunks.append(current)
    return chunks


def _restore_code(text: str, code: list[str]) -> str:
    for index, fence in enumerate(code):
        text = text.replace(f"\x00CODE{index}\x00", fence)
    return text


def _inline_markdown(text: str, xref: dict[str, str], stats: RoleStats) -> str:
    """Inline pass: roles to links, literals to code spans, escaping."""
    tokens: list[str] = []

    def stash(rendered: str) -> str:
        tokens.append(rendered)
        return f"\x00T{len(tokens) - 1}\x00"

    # 1. Math roles -> KaTeX inline math, protected verbatim (a role wrapped
    #    across source lines carries interior newlines; TeX ignores them).
    def math_span(match: re.Match[str]) -> str:
        tex = re.sub(r"\s+", " ", match.group(1)).strip()
        return stash(f"${tex}$")

    text = _MATH_ROLE_RE.sub(math_span, text)
    # 2. Cross-reference roles (contain backticks; handle before code spans).
    text = ROLE_RE.sub(
        lambda m: stash(rest_roles_to_links(m.group(0), xref, stats)), text
    )
    # 3. reST ``literal`` spans -> Markdown code spans.
    text = re.sub(r"``(.+?)``", r"`\1`", text, flags=re.DOTALL)
    # 4. Protect code spans from escaping.
    text = re.sub(r"`[^`]+`", lambda m: stash(m.group(0)), text)
    # 5. Escape characters Markdown/HTML would misread in plain prose.
    text = text.replace("<", "\\<")
    # Intraword asterisks (unit notation "Pa*s/m", math "10*lg(x)") would
    # pair up into <em> spans; reST emphasis never sits between word
    # characters, so escaping exactly those is safe.
    text = re.sub(r"(?<=\w)\*(?=\w)", "\\\\*", text)
    # 6. Restore protected spans.
    return re.sub(r"\x00T(\d+)\x00", lambda m: tokens[int(m.group(1))], text)


def render_prose(text: str, xref: dict[str, str], stats: RoleStats) -> str:
    """Full reST -> Markdown pipeline for block prose."""
    code: list[str] = []
    text = rest_blocks_to_markdown(text, code)
    text = _inline_markdown(text, xref, stats)
    text = _restore_code(text, code)
    return re.sub(r"\n{3,}", "\n\n", text).strip("\n")


def render_inline(text: str, xref: dict[str, str], stats: RoleStats) -> str:
    """Inline reST -> Markdown collapsed to a single line (no pipe escaping)."""
    rendered = _inline_markdown(text, xref, stats)
    return rendered.replace("\n", " ").strip()


def _math_bars_to_commands(match: re.Match[str]) -> str:
    r"""Spell the vertical bars of a math span as TeX commands.

    GFM decodes the ``\|`` cell escape for prose and code spans but not
    inside math, where KaTeX would then read it as ``\|`` and typeset a
    double bar. ``\vert``/``\Vert`` are the same glyphs written without
    the character the table syntax claims, so they survive the escape.
    """
    span = match.group(0).replace("\\|", "\\Vert ")
    return span.replace("|", "\\vert ")


def render_cell(text: str, xref: dict[str, str], stats: RoleStats) -> str:
    r"""Inline reST -> Markdown for a table cell (single line, pipes escaped).

    The ``|`` escape is GFM table syntax: it is decoded back to a literal
    pipe only inside a table row, so it must never be applied to prose
    outside a table (a code span there would show the backslash literally).
    Math is exempt: its bars become ``\vert``/``\Vert`` first, so the
    escaping below cannot reach into a formula.
    """
    rendered = render_inline(text, xref, stats)
    return _INLINE_MATH_RE.sub(_math_bars_to_commands, rendered).replace("|", "\\|")


# --------------------------------------------------------------------------
# Introspection model
# --------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class MethodDoc:
    """One public method, property or nested callable of a class."""

    name: str  # qualified: "ClassName.method"
    kind: str  # "method", "classmethod", "staticmethod", "property"
    heading: str
    anchor: str
    signature: str | None
    doc: str


@dataclasses.dataclass(frozen=True)
class MemberDoc:
    """One public name documented on a module page."""

    name: str
    kind: str  # "function", "class", "constant"
    anchor: str
    signature: str | None
    doc: str
    init_doc: str = ""  # classes: docstring of an explicit __init__
    methods: tuple[MethodDoc, ...] = ()
    type_name: str = ""  # constants only
    value_repr: str = ""  # constants only


@dataclasses.dataclass(frozen=True)
class ModuleDoc:
    """One generated page: a public module and its members."""

    module: str  # full dotted name ("phonometry" for the top level)
    section: Section
    slug: str  # file/URL slug within the section
    title: str
    label: str
    intro: str
    members: tuple[MemberDoc, ...]
    #: The package a private module's names are imported from, which its page
    #: names before anything else; empty for a public module, whose title is
    #: already the address to import from.
    home: str = ""
    #: The names on a private module's page that another package publishes,
    #: each with that package, so the opening names them rather than send the
    #: reader to ``home`` for them (``plot_junction_geometry`` is drawn beside
    #: the vibration junctions and published by ``phonometry.building``).
    elsewhere: tuple[tuple[str, str], ...] = ()

    @property
    def url(self) -> str:
        return f"{API_BASE}/{self.section.key}/{self.slug}/"

    @property
    def relpath(self) -> str:
        return f"{self.section.key}/{self.slug}.md"


class _Slugger:
    """github-slugger-compatible anchors (what Astro assigns to headings)."""

    def __init__(self) -> None:
        self._seen: dict[str, int] = {}

    def slug(self, text: str) -> str:
        base = re.sub(r"[^\w\- ]", "", text.lower()).replace(" ", "-")
        count = self._seen.get(base, 0)
        self._seen[base] = count + 1
        return base if count == 0 else f"{base}-{count}"


def _sorted_names(names: list[str]) -> list[str]:
    return sorted(names, key=lambda n: (n.lower(), n))


def _is_public_module(module: str) -> bool:
    return not any(part.startswith("_") for part in module.split(".")[1:])


def inherited_ivars(obj: type) -> str:
    """The ``:ivar:`` lines a class inherits and does not restate.

    A catalogue row holds its quantities and inherits the hedges every
    published row carries, and a reader of the subclass needs both: the
    signature shows ``ranges`` whether or not the subclass wrote the line
    describing it. Without this, factoring a shared base out of two classes
    silently strips half the published attribute table, which is the kind of
    regression a documentation build should not be able to make.

    A base whose own description the subclass rewrote keeps its field lines
    all the same: the prose above and the attribute table below are separate
    things, and only the table is completed here. A name the subclass
    documents itself wins, and a name it does not carry at all is skipped,
    so a base can document more than any one subclass has.

    Membership is read from the dataclass fields rather than from
    ``hasattr``, because a field with no default and a field built by a
    ``default_factory`` both leave the class without an attribute of that
    name: reading it the obvious way published eleven of the eighteen
    inherited rows and dropped ``name``, ``source`` and every mapping.

    :param obj: The class being rendered.
    :return: The extra field lines, ready to append to its docstring, empty
        when it inherits nothing undocumented.
    """
    own = {name for name, _ in parse_docstring(inspect.getdoc(obj) or "").ivars}
    carried = (
        {declared.name for declared in dataclasses.fields(obj)}
        if dataclasses.is_dataclass(obj)
        else {name for name in dir(obj) if not name.startswith("__")}
    )
    lines: list[str] = []
    for base in obj.__mro__[1:]:
        base_doc = base.__doc__
        if not base_doc:
            continue
        parsed = parse_docstring(inspect.cleandoc(base_doc))
        for name, text in parsed.ivars:
            if name in own or name not in carried:
                continue
            own.add(name)
            lines.append(f":ivar {name}: {text}")
            vartype = parsed.vartypes.get(name)
            if vartype:
                lines.append(f":vartype {name}: {vartype}")
    return "\n".join(lines)


def attribute_module(name: str, obj: object) -> str:
    """Return the full module whose page documents public name ``name``.

    That is the module that defines it, when the reference has a page for that
    module: a public one, or a private one a section lists because a function
    of its package names it (``signals._correlation``).
    """
    override = OBJECT_MODULE_OVERRIDES.get(name)
    if override is not None:
        return override
    module = getattr(obj, "__module__", None)
    if isinstance(module, str):
        # A name a function or class carries: its module answers, or the
        # taxonomy has to say where it is documented.
        if _is_public_module(module) or is_documented_module(module):
            return module
        msg = (
            f"public name {name!r} is defined in private module {module!r}; "
            "add it to OBJECT_MODULE_OVERRIDES in scripts/api_taxonomy.py"
        )
        raise LookupError(msg)
    # Module-level constant: find the taxonomy module that defines it.
    hits: list[str] = []
    for section in SECTIONS.values():
        for candidate in section.modules:
            if candidate == "phonometry":
                continue
            mod = importlib.import_module(candidate)
            if getattr(mod, name, _SENTINEL) is obj:
                hits.append(candidate)
    if len(hits) == 1:
        return hits[0]
    msg = (
        f"constant {name!r} matches modules {hits!r}; add it to "
        "OBJECT_MODULE_OVERRIDES in scripts/api_taxonomy.py"
    )
    raise LookupError(msg)


_SENTINEL = object()


def _attribute_docstrings(module: ModuleType) -> dict[str, str]:
    """PEP 258 attribute docstrings (string literal after an assignment)."""
    try:
        source = inspect.getsource(module)
    except (OSError, TypeError):
        return {}
    tree = ast.parse(source)
    docs: dict[str, str] = {}
    body = tree.body
    for stmt, follower in itertools.pairwise(body):
        target: ast.expr | None = None
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
            target = stmt.targets[0]
        elif isinstance(stmt, ast.AnnAssign):
            target = stmt.target
        if (
            isinstance(target, ast.Name)
            and isinstance(follower, ast.Expr)
            and isinstance(follower.value, ast.Constant)
            and isinstance(follower.value.value, str)
        ):
            docs[target.id] = inspect.cleandoc(follower.value.value)
    return docs


# --------------------------------------------------------------------------
# Type aliases in signatures
# --------------------------------------------------------------------------

#: A quoted string inside an annotation (a ``Literal`` member), kept verbatim.
_QUOTED_RE = re.compile(r"""('(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")""")
#: An identifier that starts a name in an annotation: not an attribute
#: (``np.ndarray``), not the middle of a longer word.
_ANNOTATION_NAME_RE = re.compile(r"(?<![\w.])[A-Za-z_]\w*")
#: How deep one alias may name another before the expansion stops.
_MAX_ALIAS_DEPTH = 5


def _is_type_alias(obj: object) -> bool:
    """Whether ``obj`` is a typing alias (``Literal[...]``, a union, ``type X``)."""
    return get_origin(obj) is not None or isinstance(obj, TypeAliasType)


def _defining_module(obj: object) -> str | None:
    """The module whose namespace the annotations of ``obj`` were written in."""
    target = obj.__func__ if isinstance(obj, (staticmethod, classmethod)) else obj
    if not isinstance(target, type):
        target = inspect.unwrap(target)  # type: ignore[arg-type]
    module = getattr(target, "__module__", None)
    return module if isinstance(module, str) else None


@functools.cache
def _module_tree(module_name: str) -> ast.Module | None:
    try:
        source = inspect.getsource(importlib.import_module(module_name))
    except (OSError, TypeError, ImportError):
        return None
    return ast.parse(source)


@functools.cache
def _module_aliases(module_name: str) -> Mapping[str, str]:
    """The type aliases ``module_name`` assigns at top level, as written.

    The value is the right-hand side unparsed, so a multi-line ``Literal`` reads
    on one line and every alias reads the way its author spelled it
    (``NDArray[np.float64]``, not the generic alias numpy expands it into).
    """
    tree = _module_tree(module_name)
    if tree is None:
        return {}
    module = sys.modules[module_name]
    aliases: dict[str, str] = {}
    for statement in tree.body:
        name: str | None = None
        value: ast.expr | None = None
        if isinstance(statement, ast.TypeAlias) and isinstance(
            statement.name, ast.Name
        ):
            name, value = statement.name.id, statement.value
        elif (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        ):
            name, value = statement.targets[0].id, statement.value
        elif (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
            and statement.value is not None
        ):
            name, value = statement.target.id, statement.value
        if name and value and _is_type_alias(getattr(module, name, None)):
            aliases[name] = ast.unparse(value)
    return MappingProxyType(aliases)


@functools.cache
def _module_imports(module_name: str) -> Mapping[str, tuple[str, str]]:
    """``from X import name`` bindings at top level, ``TYPE_CHECKING`` included.

    An annotation may name an alias the module imports only for the type
    checker, so the runtime namespace does not hold it; the import does.
    """
    tree = _module_tree(module_name)
    if tree is None:
        return {}
    package = sys.modules[module_name].__package__ or module_name
    bindings: dict[str, tuple[str, str]] = {}
    statements = list(tree.body)
    while statements:
        statement = statements.pop(0)
        if isinstance(statement, ast.If):
            statements[:0] = [*statement.body, *statement.orelse]
        elif isinstance(statement, ast.ImportFrom):
            source = importlib.util.resolve_name(
                "." * statement.level + (statement.module or ""), package
            )
            for alias in statement.names:
                bindings[alias.asname or alias.name] = (source, alias.name)
    return MappingProxyType(bindings)


def _find_alias(module_name: str, name: str, depth: int = 0) -> tuple[str, str] | None:
    """``(defining module, definition)`` of the alias ``name`` reads as there."""
    if depth > _MAX_ALIAS_DEPTH or not module_name.startswith("phonometry"):
        return None
    definition = _module_aliases(module_name).get(name)
    if definition is not None:
        return module_name, definition
    imported = _module_imports(module_name).get(name)
    if imported is None:
        return None
    return _find_alias(imported[0], imported[1], depth + 1)


@functools.cache
def _published_ids() -> frozenset[int]:
    owners = public_names()
    return frozenset(id(getattr(owners[name], name)) for name in owners)


def expand_unpublished_aliases(text: str, module_name: str, depth: int = 0) -> str:
    """Replace every type alias the library does not publish by its definition.

    A signature is read on a page that links every published name, and
    ``form: DeclarationForm`` names something a reader can neither import nor
    look up: no type alias is public. So ``form: Literal['dual-number',
    'single-number']`` is what the page shows, the alias's definition as its
    author wrote it. An alias some package did publish would stay a name.

    :param text: The annotation as the source writes it.
    :param module_name: The module the annotation was written in, whose
        namespace (and type-checking imports) say what each name is.
    :param depth: Recursion guard for an alias whose definition names another.
    :return: The annotation with each unpublished alias spelled out.
    """
    if depth > _MAX_ALIAS_DEPTH:
        return text

    def substitute(match: re.Match[str]) -> str:
        found = _find_alias(module_name, match.group(0))
        if found is None:
            return match.group(0)
        home, definition = found
        alias_name = match.group(0)
        obj = getattr(sys.modules[home], alias_name, None)
        if obj is not None and id(obj) in _published_ids():
            return alias_name
        return expand_unpublished_aliases(definition, home, depth + 1)

    pieces = _QUOTED_RE.split(text)
    # Odd indices are the quoted strings the split kept; leave them as written.
    return "".join(
        piece if index % 2 else _ANNOTATION_NAME_RE.sub(substitute, piece)
        for index, piece in enumerate(pieces)
    )


def format_signature(
    name: str,
    obj: Callable[..., object],
    *,
    drop_first: bool = False,
    omit_return: bool = False,
) -> str:
    """Render the call forms of ``obj``, one per ``typing.overload`` head.

    A function that declares overloads has more than one way to be called, and
    the implementation signature is not one of them: it is the permissive union
    that accepts every head plus the combinations none of them allow. Publishing
    only that would document a contract the library refuses, so every head is
    rendered, separated by a blank line, the way a stub file shows them.

    Stringized annotations (PEP 563, the repo style) are emitted as written,
    except that a type alias the library does not publish is replaced by its
    definition (see :func:`expand_unpublished_aliases`). Multi-line when the
    one-line form would be hard to read.
    """
    heads = get_overloads(obj)
    if heads:
        return "\n\n".join(
            _format_one_signature(
                name, head, drop_first=drop_first, omit_return=omit_return
            )
            for head in heads
        )
    return _format_one_signature(
        name, obj, drop_first=drop_first, omit_return=omit_return
    )


def _format_one_signature(
    name: str,
    obj: Callable[..., object],
    *,
    drop_first: bool = False,
    omit_return: bool = False,
) -> str:
    """Render a single ``name(params) -> ret`` from ``inspect.signature``."""
    signature = inspect.signature(obj)
    module = _defining_module(obj)
    bounds = _type_parameter_bounds(obj, module)
    parameters = list(signature.parameters.values())
    if drop_first and parameters and parameters[0].name in ("self", "cls"):
        parameters = parameters[1:]

    parts: list[str] = []
    saw_positional_only = False
    star_emitted = False
    for parameter in parameters:
        if parameter.kind is inspect.Parameter.POSITIONAL_ONLY:
            saw_positional_only = True
        elif saw_positional_only:
            parts.append("/")
            saw_positional_only = False
        if parameter.kind is inspect.Parameter.KEYWORD_ONLY and not star_emitted:
            parts.append("*")
            star_emitted = True
        if parameter.kind is inspect.Parameter.VAR_POSITIONAL:
            star_emitted = True
        parts.append(_format_parameter(parameter, module, bounds))
    if saw_positional_only:
        parts.append("/")

    returns = ""
    if not omit_return and signature.return_annotation is not (inspect.Signature.empty):
        returns = (
            f" -> {_format_annotation(signature.return_annotation, module, bounds)}"
        )
    one_line = f"{name}({', '.join(parts)}){returns}"
    if len(one_line) <= _MAX_SIGNATURE_LINE or not parts:
        return one_line
    joined = ",\n    ".join(parts)
    return f"{name}(\n    {joined},\n){returns}"


def _type_parameter_bounds(
    obj: Callable[..., object], module: str | None
) -> Mapping[str, str]:
    """The bound of each type parameter ``obj`` names once, as its source writes it.

    An overload head of a function of a number or an array of them takes its
    argument as ``frequency: S`` with ``[S: RealScalar]``, so that a type
    checker matches an array whose shape it does not know to one head only;
    the page shows the bound in its place, which is what the head accepts. A
    type parameter the signature names more than once ties those places
    together (``row_type: type[R]`` and ``-> Catalogue[R]``), so it stays a
    name. Read from the module's source, because evaluating a bound would
    need the names the module imports only for the type checker.
    """
    target = inspect.unwrap(obj)
    if not getattr(target, "__type_params__", ()) or module is None:
        return {}
    tree = _module_tree(module)
    code = getattr(target, "__code__", None)
    if tree is None or code is None:
        return {}
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and node.name == target.__name__
            and code.co_firstlineno
            in {node.lineno, *(d.lineno for d in node.decorator_list[:1])}
        ):
            named = [
                child.id
                for annotation in (
                    *(argument.annotation for argument in _arguments(node)),
                    node.returns,
                )
                if annotation is not None
                for child in ast.walk(annotation)
                if isinstance(child, ast.Name)
            ]
            return {
                parameter.name: ast.unparse(parameter.bound)
                for parameter in node.type_params
                if isinstance(parameter, ast.TypeVar)
                and parameter.bound is not None
                and named.count(parameter.name) == 1
            }
    return {}


def _arguments(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.arg]:
    """Every parameter of a definition, in the order written."""
    arguments = node.args
    every = [*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs]
    every.extend(a for a in (arguments.vararg, arguments.kwarg) if a is not None)
    return every


def _format_annotation(
    annotation: object,
    module: str | None = None,
    bounds: Mapping[str, str] | None = None,
) -> str:
    if isinstance(annotation, str):
        # PEP 563 stringizes annotations; an annotation that was already a
        # string literal in the source keeps its quotes. Strip them.
        text = annotation.strip()
        if len(text) >= 2 and text[0] == text[-1] and text[0] in "'\"":
            text = text[1:-1]
    else:
        text = inspect.formatannotation(annotation)
    if bounds:
        text = _ANNOTATION_NAME_RE.sub(
            lambda match: bounds.get(match.group(0), match.group(0)), text
        )
    return expand_unpublished_aliases(text, module) if module else text


def _format_parameter(
    parameter: inspect.Parameter,
    module: str | None = None,
    bounds: Mapping[str, str] | None = None,
) -> str:
    text = parameter.name
    if parameter.kind is inspect.Parameter.VAR_POSITIONAL:
        text = f"*{text}"
    elif parameter.kind is inspect.Parameter.VAR_KEYWORD:
        text = f"**{text}"
    annotated = parameter.annotation is not inspect.Parameter.empty
    if annotated:
        text = f"{text}: {_format_annotation(parameter.annotation, module, bounds)}"
    if parameter.default is not inspect.Parameter.empty:
        if parameter.default is Ellipsis:
            # The placeholder an overload head uses for "whatever the
            # implementation defaults to"; `repr` would print `Ellipsis`.
            default = "..."
        elif type(parameter.default).__module__ not in ("builtins", "types"):
            # Third-party reprs (numpy arrays) are not pinned, so a repr here
            # would make the drift gate hostage to dependency upgrades; the
            # parameter description documents the effective default.
            default = "..."
        else:
            default = _HEX_ADDR_RE.sub("...", repr(parameter.default))
        text = f"{text} = {default}" if annotated else f"{text}={default}"
    return text


def _is_published(cls: type) -> bool:
    """Whether this class gets a page of its own in the reference.

    A base whose module is private has no page, so a reader who follows an
    inherited method has nowhere to land: the method has to be documented on
    the public class that carries it. A base that is published does have one,
    and repeating its methods on every subclass would be noise.

    :param cls: The base class.
    :return: ``True`` when the class lives in a module a reader can open.
    """
    module = getattr(cls, "__module__", "")
    return not any(part.startswith("_") for part in module.split("."))


def _method_names(cls: type) -> list[str]:
    """The methods a class's page documents, its own and the ones it carries.

    A class that inherits from a private base carries that base's methods into
    the public API without giving the reader anywhere else to read about them.
    The catalogue rows are the case that matters: ``bands()``, ``spectrum()``
    and ``why_missing()`` are the shape of every published table in this
    library, and they live on private bases so that five classes do not each
    keep their own copy.

    :param cls: The class being documented.
    :return: The attribute names to document on its page, its own first.
    """
    names = [n for n in vars(cls) if not n.startswith("_")]
    seen = set(names)
    for base in cls.__mro__[1:]:
        if base is object or _is_published(base):
            continue
        for attr_name in vars(base):
            if attr_name.startswith("_") or attr_name in seen:
                continue
            raw = inspect.getattr_static(cls, attr_name, None)
            if isinstance(
                raw, (staticmethod, classmethod, property)
            ) or inspect.isfunction(raw):
                seen.add(attr_name)
                names.append(attr_name)
    return names


def _class_methods(
    name: str, cls: type, slugger: _Slugger, issues: list[str]
) -> tuple[MethodDoc, ...]:
    methods: list[MethodDoc] = []
    for attr_name in _sorted_names(_method_names(cls)):
        raw = inspect.getattr_static(cls, attr_name)
        qualified = f"{name}.{attr_name}"
        kind: str
        func: Callable[..., object] | None
        if isinstance(raw, staticmethod):
            kind, func = "staticmethod", raw.__func__
        elif isinstance(raw, classmethod):
            kind, func = "classmethod", raw.__func__
        elif isinstance(raw, property):
            kind, func = "property", raw.fget
        elif inspect.isfunction(raw):
            kind, func = "method", raw
        else:
            continue  # class attributes, enum members: documented via :ivar:
        doc = inspect.getdoc(func) or ""
        signature: str | None = None
        if kind != "property" and func is not None:
            try:
                signature = format_signature(
                    qualified, func, drop_first=kind != "staticmethod"
                )
            except (ValueError, TypeError) as exc:
                issues.append(f"{qualified}: no signature ({exc})")
        heading = qualified if kind == "property" else f"{qualified}()"
        methods.append(
            MethodDoc(
                name=qualified,
                kind=kind,
                heading=heading,
                anchor=slugger.slug(heading),
                signature=signature,
                doc=doc,
            )
        )
    return tuple(methods)


def _plain(obj: object) -> object:
    """*obj* with every read-only mapping in it, at any depth, shown as a dict.

    A published table is a :class:`types.MappingProxyType`, and so are the
    tables nested in it; their repr wraps each level in ``mappingproxy(...)``,
    which says how the value is stored rather than what it holds.
    """
    if isinstance(obj, Mapping):
        return {key: _plain(value) for key, value in obj.items()}
    if type(obj) is tuple:
        return tuple(_plain(item) for item in obj)
    return obj


def _constant_repr(obj: object) -> str:
    if type(obj).__module__ not in ("builtins", "types"):
        return ""  # third-party reprs (numpy arrays) are not pinned; skip
    text = repr(_plain(obj))
    if len(text) > _MAX_CONST_REPR or _HEX_ADDR_RE.search(text):
        return ""
    return text


def _type_name(obj: object) -> str:
    cls = type(obj)
    shape = getattr(obj, "shape", None)
    if isinstance(shape, tuple):
        return f"{cls.__module__}.{cls.__qualname__}, shape {shape}"
    # Checked before the builtins branch: the class of a read-only mapping
    # reports itself as `builtins.mappingproxy`, a name nobody can import.
    if cls is MappingProxyType:
        return "mapping"
    if cls.__module__ == "builtins":
        return cls.__qualname__
    # A typing alias is its own documentation: `Literal["a", "b"]` says what
    # the name accepts, where the class behind it is a private implementation
    # detail (`typing._LiteralGenericAlias`) that tells a reader nothing and
    # names something they must not import.
    if cls.__module__ == "typing":
        return str(obj).replace("typing.", "")
    # A class defined in a private module is published by its package, and that
    # is the path a reader may import. `Fluid` lives in `phonometry.fluids._state`
    # and is `phonometry.fluids.Fluid`; printing the private path would offer an
    # import that works today and is not supported.
    return f"{_published_module(cls)}.{cls.__qualname__}"


def _published_module(cls: type) -> str:
    """The public module that exports *cls*, or its own if none does."""
    parts = cls.__module__.split(".")
    for cut in range(len(parts) - 1, 0, -1):
        if not parts[cut].startswith("_"):
            continue
        candidate = ".".join(parts[:cut])
        if any(segment.startswith("_") for segment in parts[:cut]):
            # A package nested under a private one is private too: publishing
            # `phonometry.x._private` would swap one unsupported import for
            # another.
            continue
        module = sys.modules.get(candidate)
        if module is not None and getattr(module, cls.__qualname__, None) is cls:
            return candidate
    return cls.__module__


def build_model() -> tuple[list[ModuleDoc], dict[str, str], list[str]]:
    """Introspect phonometry into pages, the xref map and parse issues."""
    issues: list[str] = []
    owners = public_names()
    names: list[str] = sorted(owners)

    by_module: dict[str, list[str]] = {}
    for name in names:
        module = attribute_module(name, getattr(owners[name], name))
        module_section(module)  # fails loudly for unmapped modules
        by_module.setdefault(module, []).append(name)

    mapped = {m for s in SECTIONS.values() for m in s.modules}
    stale = sorted(mapped - set(by_module))
    if stale:
        msg = f"taxonomy modules with no public names (remove or fix): {stale}"
        raise ValueError(msg)

    pages: list[ModuleDoc] = []
    xref: dict[str, str] = {}
    for section in SECTIONS.values():
        for module_name in section.modules:
            page = _build_page(
                module_name, section, by_module[module_name], issues, owners
            )
            pages.append(page)
            xref[module_name] = page.url
            # Both the bare name and the qualified one. A bare name is all most
            # references write, but it is ambiguous the moment two modules
            # export it (`transmission_loss` is both a silencer's and an
            # ocean's), and whichever module is walked last would otherwise
            # take every link to it. A reference that says which module it
            # means is then resolved by saying so, rather than falling through
            # to the bare name and landing wherever it lands.
            for member in page.members:
                anchored = f"{page.url}#{member.anchor}"
                xref[member.name] = anchored
                xref[f"{module_name}.{member.name}"] = anchored
                for method in member.methods:
                    anchored = f"{page.url}#{method.anchor}"
                    xref[method.name] = anchored
                    xref[f"{module_name}.{method.name}"] = anchored

    seen: dict[tuple[str, str], str] = {}
    for page in pages:
        slug = (page.section.key, page.slug)
        if slug in seen:
            msg = (
                f"slug collision between module pages: {page.module} and "
                f"{seen[slug]} both land on {page.slug!r} in section "
                f"{page.section.key!r}. Two modules of one section cannot share "
                f"a basename; rename one of them."
            )
            raise ValueError(msg)
        seen[slug] = page.module

    return pages, xref, issues


#: Counts the top-level page spells out in words.
_COUNT_WORDS = (
    "no",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
)


def _listed(items: list[str]) -> str:
    """``a``, ``a and b``, ``a, b and c``."""
    return ", ".join(items[:-1]) + (" and " if len(items) > 1 else "") + items[-1]


def top_level_intro(here: list[str]) -> str:
    """The opening of the top-level page: what it holds and where each is.

    The top level publishes the domain subpackages and a few objects of its
    own, and not every one of those is documented on its page: ``Signal`` is
    documented with :mod:`phonometry.io`, the module that defines it. Saying
    "documented here" of all of them would send a reader to the wrong page, so
    the sentence is written from where each one really is.

    :param here: The names the top-level page documents.
    :return: The page's opening paragraph.
    """
    import phonometry

    objects = [
        name
        for name in phonometry.__all__
        if not inspect.ismodule(getattr(phonometry, name))
    ]
    count = len(objects)
    counted = _COUNT_WORDS[count] if count < len(_COUNT_WORDS) else str(count)
    on_page = [f"`{name}`" for name in objects if name in here]
    elsewhere = [
        f"`{name}` with `{attribute_module(name, getattr(phonometry, name))}`"
        for name in objects
        if name not in here
    ]
    where = []
    if on_page:
        verb = "is" if len(on_page) == 1 else "are"
        where.append(f"{_listed(on_page)} {verb} documented here")
    where.extend(elsewhere)
    return (
        f"The top level publishes the domain subpackages and {counted} objects "
        f"that belong to no single domain. {_listed(where)}; every other name "
        "is imported from its subpackage."
    )


def _build_page(
    module_name: str,
    section: Section,
    names: list[str],
    issues: list[str],
    owners: Mapping[str, ModuleType],
) -> ModuleDoc:
    top_level = module_name == "phonometry"
    module = importlib.import_module(module_name)
    attribute_docs = _attribute_docstrings(module)
    relative = module_name.removeprefix("phonometry.")
    # A private module keeps the URL and the sidebar label it had while it was
    # public, so no link to its page breaks.
    basename = (
        relative.rsplit(".", 1)[-1].lstrip("_") if not top_level else "phonometry"
    )
    intro = (
        top_level_intro(names) if top_level else inspect.cleandoc(module.__doc__ or "")
    )

    slugger = _Slugger()
    members: list[MemberDoc] = []
    for name in _sorted_names(names):
        obj = getattr(owners[name], name)
        anchor = slugger.slug(name)
        if inspect.isclass(obj):
            # Warning/exception classes inherit object.__init__; a signature
            # block would be noise (and CPython refuses to introspect it).
            signature = (
                None
                if issubclass(obj, BaseException)
                else _try_signature(name, obj, issues, omit_return=True)
            )
            # Raw __doc__ (not inspect.getdoc): generated __init__ methods
            # have none, and getdoc would inherit object.__init__'s
            # "Initialize self" placeholder.
            init = vars(obj).get("__init__")
            init_raw = getattr(init, "__doc__", None) if init is not None else None
            init_doc = inspect.cleandoc(init_raw) if init_raw else ""
            members.append(
                MemberDoc(
                    name=name,
                    kind="class",
                    anchor=anchor,
                    signature=signature,
                    doc="\n".join(
                        part
                        for part in (inspect.getdoc(obj) or "", inherited_ivars(obj))
                        if part
                    ),
                    init_doc=init_doc,
                    methods=_class_methods(name, obj, slugger, issues),
                )
            )
        elif inspect.isroutine(obj):
            signature = _try_signature(name, obj, issues)
            members.append(
                MemberDoc(
                    name=name,
                    kind="function",
                    anchor=anchor,
                    signature=signature,
                    doc=inspect.getdoc(obj) or "",
                )
            )
        else:
            members.append(
                MemberDoc(
                    name=name,
                    kind="constant",
                    anchor=anchor,
                    signature=None,
                    doc=attribute_docs.get(name, ""),
                    type_name=_type_name(obj),
                    # __version__ changes every release; embedding its value
                    # would make the drift gate fail on each version bump.
                    value_repr="" if name == "__version__" else _constant_repr(obj),
                )
            )
    title = "phonometry" if top_level else relative
    home = ""
    elsewhere: tuple[tuple[str, str], ...] = ()
    if is_private_module(module_name):
        # Its names are published by the domain package, and its title says so
        # rather than claim a module address nobody can import.
        home = ".".join(module_name.split(".")[:2])
        title = (
            f"{home.removeprefix('phonometry.')}: {PRIVATE_MODULE_TOPICS[module_name]}"
        )
        elsewhere = tuple(
            (member.name, owners[member.name].__name__)
            for member in members
            if owners[member.name].__name__ != home
        )
    return ModuleDoc(
        module=module_name,
        section=section,
        slug=basename.replace("_", "-"),
        title=title,
        label=basename,
        intro=intro,
        members=tuple(members),
        home=home,
        elsewhere=elsewhere,
    )


def _try_signature(
    name: str,
    obj: Callable[..., object],
    issues: list[str],
    *,
    omit_return: bool = False,
) -> str | None:
    try:
        return format_signature(name, obj, omit_return=omit_return)
    except (ValueError, TypeError) as exc:
        issues.append(f"{name}: no signature ({exc})")
        return None


# --------------------------------------------------------------------------
# Page rendering
# --------------------------------------------------------------------------


def _heading_text(name: str) -> str:
    """Escape names Markdown would emphasize (dunders: ``__version__``)."""
    if name.startswith("_") or name.endswith("_"):
        return name.replace("_", "\\_")
    return name


#: The document title of the top-level page. Starlight titles a page
#: "<title> | <site title>", and the top level's title is the package name, so
#: the tab and the search result would read "phonometry | phonometry": the site
#: name twice and no word on what the page holds. The frontmatter title stays
#: the package name, which the page heading and the sidebar show; only the
#: document title is overridden, the way the home page does it
#: (site/src/content/docs/index.mdx). site/scripts/check-crawl.mjs fails a
#: title that names the site twice.
TOP_LEVEL_HEAD_TITLE = "Top-level API | phonometry"


def _frontmatter(title: str, description: str, label: str, head_title: str = "") -> str:
    lines = [
        "---",
        f"title: {json.dumps(title)}",
        f"description: {json.dumps(description)}",
        "sidebar:",
        f"  label: {json.dumps(label)}",
    ]
    if head_title:
        lines += ["head:", "  - tag: title", f"    content: {json.dumps(head_title)}"]
    return "\n".join([*lines, "---"])


def _field_table(
    heading: str,
    columns: tuple[str, str],
    rows: list[tuple[str, str]],
) -> list[str]:
    if not rows:
        return []
    out = [
        f"**{heading}**",
        "",
        f"| {columns[0]} | {columns[1]} |",
        "| :--- | :--- |",
    ]
    out.extend(f"| {left} | {right} |" for left, right in rows)
    out.append("")
    return out


def _render_docbody(
    owner: str,
    doc: str,
    xref: dict[str, str],
    stats: RoleStats,
    failures: list[str],
    *,
    param_note: str = "Parameters",
) -> list[str]:
    """Render one docstring (prose + field tables) to Markdown lines."""
    if not doc:
        return []
    parsed = parse_docstring(doc)
    if parsed.issues:
        failures.append(f"{owner}: {'; '.join(parsed.issues)}")
        return ["```text", doc, "```", ""]

    out: list[str] = []
    if parsed.description:
        out.extend([render_prose(parsed.description, xref, stats), ""])

    params = [
        (
            f"`{name}`",
            _with_type(parsed.types.get(name), desc, xref, stats),
        )
        for name, desc in parsed.params
    ]
    out.extend(_field_table(param_note, ("Name", "Description"), params))

    ivars = [
        (
            f"`{name}`",
            _with_type(parsed.vartypes.get(name), desc, xref, stats),
        )
        for name, desc in parsed.ivars
    ]
    out.extend(_field_table("Attributes", ("Name", "Description"), ivars))

    if parsed.returns:
        returns = render_inline(parsed.returns, xref, stats)
        if parsed.rtype:
            rtype = render_inline(parsed.rtype, xref, stats)
            returns = f"{returns} (*{rtype}*)" if returns else f"*{rtype}*"
        out.extend([f"**Returns:** {returns}", ""])

    raises = [
        (render_cell(exc, xref, stats), render_cell(desc, xref, stats))
        for exc, desc in parsed.raises
    ]
    out.extend(_field_table("Raises", ("Exception", "When"), raises))

    warns = [
        (render_cell(exc, xref, stats), render_cell(desc, xref, stats))
        for exc, desc in parsed.warns
    ]
    out.extend(_field_table("Warns", ("Warning", "When"), warns))

    if parsed.epilogue:
        out.extend([render_prose(parsed.epilogue, xref, stats), ""])
    return out


def _with_type(
    type_text: str | None,
    desc: str,
    xref: dict[str, str],
    stats: RoleStats,
) -> str:
    rendered = render_cell(desc, xref, stats)
    if type_text:
        rendered = f"(*{render_cell(type_text, xref, stats)}*) {rendered}"
    return rendered


#: Longest meta description a page emits. Bing's tools flag a description as
#: too long past a threshold they do not publish (160 characters in their
#: older guidelines), and Google cuts the snippet mid-sentence wherever it
#: needs to. site/scripts/check-descriptions.mjs holds every built page to
#: 160; this leaves a margin under it.
_MAX_DESCRIPTION = 155

#: Shortest opening sentence that may stand in for a lead paragraph too long
#: to be the description: below it the sentence says too little on its own.
_MIN_OPENING_SENTENCE = 70


def _page_description(page: ModuleDoc) -> str:
    """The page's meta description, taken from the module docstring.

    These pages used to describe themselves as "Public API of
    phonometry.building.measurement.insulation (auto-generated)", which says nothing a URL
    does not already say. The same page's body opens with a precise summary of
    what the module implements and which standards govern it, so that is what
    the description should be: it is what a search result shows and what an AI
    system reads when deciding whether the page answers a question.
    """
    lead = page.intro.strip().split("\n\n", 1)[0].replace("\n", " ").strip()
    # Drop reStructuredText roles and markdown emphasis so the description is
    # plain prose: `:func:`x`` and ``**x**`` render as noise in a meta tag.
    lead = re.sub(r":[a-z]+:`~?([^`]+)`", r"\1", lead)
    lead = re.sub(r"[*`]", "", lead).strip()

    if not lead:
        if page.module == "phonometry":
            return "Top-level convenience API of the phonometry package."
        return f"Public API of {page.home or page.module}."

    if len(lead) <= _MAX_DESCRIPTION:
        return lead
    # A lead too long to show whole gives way to its opening sentence, cut
    # where the API index cuts its summary. Nothing is ever cut mid-sentence:
    # when the opening sentence does not fit either, the whole lead comes back
    # and the run fails on it (_description_problem), because the fix is a
    # shorter opening sentence in the docstring, which is also the first line
    # of the page and its summary in the index.
    opening = _first_sentence(lead)
    if _MIN_OPENING_SENTENCE <= len(opening) <= _MAX_DESCRIPTION:
        return opening
    return lead


def _description_problem(page: ModuleDoc) -> str | None:
    """Why ``page`` has no description short enough to emit, or None."""
    description = _page_description(page)
    if len(description) <= _MAX_DESCRIPTION:
        return None
    opening = len(_first_sentence(description))
    return (
        f"{page.module}: the lead paragraph is {len(description)} characters and its "
        f"opening sentence {opening}; rewrite the opening sentence of the module "
        f"docstring to {_MIN_OPENING_SENTENCE}-{_MAX_DESCRIPTION} characters"
    )


def render_module_page(
    page: ModuleDoc,
    xref: dict[str, str],
    stats: RoleStats,
    failures: list[str],
) -> str:
    """Render one module page to Markdown."""
    description = _page_description(page)
    # The module's own summary leads, and the provenance note follows it.
    # The note used to be the first paragraph on all 120 of these pages, which
    # made "Do not edit by hand" both the search snippet and the target of the
    # `speakable` selector: a maintenance instruction standing in for what the
    # module actually does.
    out = [
        _frontmatter(
            page.title,
            description,
            page.label,
            TOP_LEVEL_HEAD_TITLE if page.module == "phonometry" else "",
        ),
        "",
    ]
    if page.home:
        out.extend([home_sentence(page), ""])
    if page.intro:
        out.extend([render_prose(page.intro, xref, stats), ""])
    out.extend([BANNER, ""])

    for member in page.members:
        out.extend([f"## {_heading_text(member.name)}", ""])
        if member.kind == "constant":
            out.append(f"*Constant* (`{member.type_name}`).")
            out.append("")
            if member.doc:
                out.extend([render_prose(member.doc, xref, stats), ""])
            if member.value_repr:
                out.extend(
                    ["```python", f"{member.name} = {member.value_repr}", "```", ""]
                )
            continue
        if member.signature:
            out.extend(["```python", member.signature, "```", ""])
        out.extend(
            _render_docbody(
                f"{page.module}.{member.name}",
                member.doc,
                xref,
                stats,
                failures,
                param_note="Parameters",
            )
        )
        if member.init_doc:
            out.extend(
                _render_docbody(
                    f"{page.module}.{member.name}.__init__",
                    member.init_doc,
                    xref,
                    stats,
                    failures,
                    param_note="Parameters",
                )
            )
        for method in member.methods:
            out.extend([f"### {method.heading}", ""])
            if method.kind != "method":
                out.extend([f"*{method.kind}*", ""])
            if method.signature:
                out.extend(["```python", method.signature, "```", ""])
            out.extend(
                _render_docbody(
                    f"{page.module}.{method.name}",
                    method.doc,
                    xref,
                    stats,
                    failures,
                )
            )
    text = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", text).strip("\n") + "\n"


def home_sentence(page: ModuleDoc) -> str:
    """The opening of a private module's page: the package to import from.

    A name on the page that another package publishes is named with that
    package, so the opening holds for every name on the page.

    :param page: A page whose module is private (``page.home`` is set).
    :return: The sentence naming the package, with the import it takes, and
        one more per name another package publishes.
    """
    package = page.home.removeprefix("phonometry.")
    but = "".join(
        f" but `{name}`" if i == 0 else f" and `{name}`"
        for i, (name, _) in enumerate(page.elsewhere)
    )
    sentence = (
        f"Every name on this page{but} is published by `{page.home}`: "
        f"`from phonometry import {package}`, then `{package}.<name>`."
    )
    return " ".join(
        [
            sentence,
            *(f"`{name}` is published by `{owner}`." for name, owner in page.elsewhere),
        ]
    )


def _index_link(page: ModuleDoc) -> str:
    """The first cell of a page's row on the index: its address, or its title.

    A public module's title is the address a reader imports, so it reads as
    code. A private module's page is titled by its domain and subject, and the
    code span is the domain alone.
    """
    if not page.home:
        return f"[`{page.title}`]({page.url})"
    package = page.home.removeprefix("phonometry.")
    topic = page.title.removeprefix(f"{package}: ")
    return f"[`{package}`: {topic}]({page.url})"


def render_index(
    pages: list[ModuleDoc],
    xref: dict[str, str],
    stats: RoleStats,
) -> str:
    """Render the API index page (one table per section)."""
    out = [
        "---",
        'title: "API Reference"',
        (
            'description: "Every public function, class and constant in '
            'phonometry, generated from the source docstrings."'
        ),
        "---",
        "",
        (
            "The complete public API, one page per module or subject. Import "
            "the domain subpackage and call through it:"
        ),
        "",
        BANNER,
        "",
        "```python",
        "from phonometry import filters, underwater",
        "",
        "r = filters.octave_filter(x, fs)",
        "snr = underwater.passive_sonar_equation(185.0, 60.0, 50.0)",
        "```",
        "",
        ":::note",
        (
            "The API reference is generated from the English source docstrings "
            "and is published in English only."
        ),
        "",
        (
            "La referencia de la API se genera a partir de los docstrings del "
            "código (en inglés) y se publica únicamente en inglés; las rutas en "
            "español muestran esta versión inglesa como alternativa."
        ),
        ":::",
        "",
    ]
    by_section: dict[str, list[ModuleDoc]] = {}
    for page in pages:
        by_section.setdefault(page.section.key, []).append(page)
    for section in SECTIONS.values():
        out.extend(
            [
                f"## {section.label_en}",
                "",
                "| Page | Summary |",
                "| :--- | :--- |",
            ]
        )
        for page in by_section[section.key]:
            # First sentence of the first paragraph (an opening sentence may
            # wrap across several physical source lines).
            paragraph = page.intro.strip().split("\n\n", 1)[0].replace("\n", " ")
            summary = _first_sentence(paragraph)
            cell = render_cell(summary, xref, stats)
            out.append(f"| {_index_link(page)} | {cell} |")
        out.append("")
    return "\n".join(out).strip("\n") + "\n"


def _first_sentence(paragraph: str) -> str:
    """The opening sentence of a paragraph, for the module's one-line summary.

    A full stop followed by a space ends the sentence only outside brackets
    and when the next word does not start with a lower-case letter or a
    digit, so an abbreviation in a citation ("ECAC Doc 29 Vol. 2",
    "Norton & Karczub Ch. 11") does not cut the summary off mid-parenthesis.
    """
    if not paragraph:
        return ""
    depth = 0
    for i, char in enumerate(paragraph):
        if char in "([":
            depth += 1
        elif char in ")]":
            depth = max(depth - 1, 0)
        elif char == "." and depth == 0 and paragraph[i + 1 : i + 2] == " ":
            following = paragraph[i + 2 : i + 3]
            if following and not (following.islower() or following.isdigit()):
                return paragraph[: i + 1]
    return paragraph.rstrip(".") + "."


def render_sidebar(pages: list[ModuleDoc]) -> str:
    """Render the sidebar fragment (ESM, imported by the topic tree).

    One group per section, keyed by section, because each domain topic mounts
    the sections of its own subpackages: after the taxonomy reorganisation an
    API section is a subpackage is a topic, so the guide and its API travel in
    the same sidebar. The global API topic is a link to the index page, which
    already carries the full table.
    """

    def js(text: str) -> str:
        return "'" + text.replace("\\", "\\\\").replace("'", "\\'") + "'"

    lines = [
        "// Auto-generated by scripts/generate_api_docs.py (make api-docs).",
        "// Do not edit by hand.",
        "export const apiSections = {",
    ]
    by_section: dict[str, list[ModuleDoc]] = {}
    for page in pages:
        by_section.setdefault(page.section.key, []).append(page)
    for section in SECTIONS.values():
        # A section of the taxonomy with no module in it yet. Emitting the group
        # anyway would crash here on the missing key, and emitting it empty
        # would put a disclosure in the sidebar that opens on nothing; leaving
        # it out makes any topic still asking for it fail by name, in
        # site/src/data/topics.mjs.
        section_pages = by_section.get(section.key)
        if not section_pages:
            continue
        lines.extend(
            [
                f"  {js(section.key)}: {{",
                f"    label: {js(section.label_en)},",
                f"    translations: {{ es: {js(section.label_es)} }},",
                "    collapsed: true,",
                "    items: [",
            ]
        )
        lines.extend(
            f"      {js(f'reference/api/{section.key}/{page.slug}')},"
            for page in section_pages
        )
        lines.extend(["    ],", "  },"])
    lines.extend(["};", ""])
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def leaked_roles(relpath: str, rendered: str) -> list[str]:
    """Report every reST role this generator left standing in one page.

    A role it does not convert reaches the published page verbatim, prefix
    and all, which is how ``:doc:`` and ``:sup:`` once shipped. Nothing but
    a docstring can put one there, so the fix is always in the docstring.
    """
    return [
        f"{relpath}:{number}: {line.strip()}"
        for number, line in enumerate(rendered.splitlines(), start=1)
        if _LEAKED_ROLE_RE.search(line)
    ]


@dataclasses.dataclass
class Report:
    """What a generation run produced (printed by main, asserted by tests)."""

    pages: int
    members: int
    stats: RoleStats
    failures: list[str]
    issues: list[str]
    leaked_roles: list[str]
    long_descriptions: list[str]


def generate(content_dir: Path, sidebar_path: Path) -> Report:
    """Generate all pages and the sidebar fragment into the given paths."""
    pages, xref, issues = build_model()
    stats = RoleStats()
    failures: list[str] = []

    leaked: list[str] = []
    long_descriptions: list[str] = []

    if content_dir.exists():
        shutil.rmtree(content_dir)
    content_dir.mkdir(parents=True)
    index = render_index(pages, xref, stats)
    leaked += leaked_roles("index.md", index)
    (content_dir / "index.md").write_text(index, encoding="utf-8", newline="\n")
    for page in pages:
        path = content_dir / page.relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        rendered = render_module_page(page, xref, stats, failures)
        leaked += leaked_roles(page.relpath, rendered)
        if (problem := _description_problem(page)) is not None:
            long_descriptions.append(problem)
        path.write_text(rendered, encoding="utf-8", newline="\n")
    sidebar_path.parent.mkdir(parents=True, exist_ok=True)
    sidebar_path.write_text(render_sidebar(pages), encoding="utf-8", newline="\n")
    members = sum(len(page.members) for page in pages)
    return Report(
        pages=len(pages) + 1,
        members=members,
        stats=stats,
        failures=failures,
        issues=issues,
        leaked_roles=leaked,
        long_descriptions=long_descriptions,
    )


def main() -> int:
    report = generate(CONTENT_DIR, SIDEBAR_PATH)
    print(f"API reference: {report.pages} pages, {report.members} public names.")
    print(
        f"Cross-references: {report.stats.resolved} linked, "
        f"{report.stats.degraded} degraded to inline code."
    )
    for issue in report.issues:
        print(f"note: {issue}")
    if report.failures:
        print("Docstrings degraded to verbatim blocks:")
        for failure in report.failures:
            print(f"  - {failure}")
    status = 0
    if report.leaked_roles:
        print("reST roles this generator does not convert, so they ship as text:")
        for leak in report.leaked_roles:
            print(f"  - {leak}")
        status = 1
    if report.long_descriptions:
        print(
            f"Pages with no description of {_MAX_DESCRIPTION} characters or fewer "
            "(the generator never cuts one mid-sentence):"
        )
        for problem in report.long_descriptions:
            print(f"  - {problem}")
        status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
