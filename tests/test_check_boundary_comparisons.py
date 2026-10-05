#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The boundary-comparison guard, and the defects it exists for.

``scripts/check_boundary_comparisons.py`` refuses a computed decimal compared
unsettled with a printed limit or with zero. These tests hold it to the two
defects that started the sweep it closes, reduced from the code before it, to
the settled sites of the tree with their settling taken out again, to the rule
case by case, the cases it must leave alone included, to its exemptions file
and to its exit status.
"""

from __future__ import annotations

import ast
import pathlib
import sys
import textwrap

import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_boundary_comparisons as cbc

_SOURCE = cbc.SOURCE


def _refused(source: str, tmp_path: pathlib.Path) -> list[cbc.Finding]:
    """The comparisons the guard refuses in one module written from ``source``."""
    path = tmp_path / "module.py"
    path.write_text(textwrap.dedent(source), encoding="utf-8")
    return list(cbc.Module(path, "module.py").findings())


def _texts(source: str, tmp_path: pathlib.Path) -> list[str]:
    return [finding.text for finding in _refused(source, tmp_path)]


# ---------------------------------------------------------------------------
# The two defects that started the sweep, reduced from the code at 9692e3596
# ---------------------------------------------------------------------------
# ``_linear_fit`` and ``_sti_crossing`` are copied as they were, less their
# annotations and docstrings; the public functions keep only the path to the
# comparison. The parametrized test further down runs the guard on the real
# functions of the tree with the fix taken out again.

#: room/open_plan.py at 9692e3596, reduced: a slope fitted to an STI that does
#: not change comes out a few units in the last place either side of zero, and
#: the distraction distance with it.
_OPEN_PLAN_BEFORE = """
import numpy as np

_STI_DISTRACTION = 0.50

def _linear_fit(x, y):
    slope, intercept = np.polyfit(x, y, 1)
    return float(slope), float(intercept)

def _sti_crossing(slope, intercept, threshold):
    if slope >= 0.0:
        return float("nan")
    distance = (threshold - intercept) / slope
    if distance <= 0.0:
        return float("nan")
    return distance

def open_plan_metrics(positions_m, spl_a_speech, sti_values):
    r = np.asarray(positions_m, dtype=float)
    sti = np.asarray(sti_values, dtype=float)
    sti_slope, sti_intercept = _linear_fit(r, sti)
    return _sti_crossing(sti_slope, sti_intercept, _STI_DISTRACTION)
"""

#: environment/propagation/noise_reducing_devices.py at 9692e3596, reduced: a
#: weighted mean of decimal absorption coefficients that is 0,99 in decimal
#: computes 0.989 999 999 999 999 8 and missed the limit.
_ABSORPTION_BEFORE = """
import numpy as np

from ..._internal.validation import require_finite_array

ABSORPTION_RATIO_LIMIT = 0.99
SPECTRA = {"road": (1.0, 2.0)}

def _weighted(values, name, spectrum):
    band_values = require_finite_array(values, name)
    return band_values, np.asarray(SPECTRA[spectrum], dtype=float)

def sound_absorption_rating(absorption_coefficients, *, spectrum="road"):
    alpha, weights = _weighted(absorption_coefficients, "absorption_coefficients", spectrum)
    energy = 10.0 ** (0.1 * weights)
    ratio = float(np.sum(alpha * energy) / np.sum(energy))
    if ratio >= ABSORPTION_RATIO_LIMIT:
        ratio = ABSORPTION_RATIO_LIMIT
    return -10.0 * float(np.log10(abs(1.0 - ratio)))
"""


def test_the_open_plan_slope_before_the_fix_is_refused(tmp_path: pathlib.Path) -> None:
    findings = _refused(_OPEN_PLAN_BEFORE, tmp_path)
    assert [(f.scope, f.text) for f in findings] == [
        ("_sti_crossing", "slope >= 0.0"),
        ("_sti_crossing", "distance <= 0.0"),
    ]
    assert {f.reason for f in findings} == {"a fitted value compared with zero"}


def test_the_absorption_ratio_before_the_fix_is_refused(tmp_path: pathlib.Path) -> None:
    findings = _refused(_ABSORPTION_BEFORE, tmp_path)
    assert [(f.scope, f.text) for f in findings] == [
        ("sound_absorption_rating", "ratio >= ABSORPTION_RATIO_LIMIT"),
    ]


def test_the_two_defects_as_fixed_pass(tmp_path: pathlib.Path) -> None:
    # The fixes as they are in the tree: a named threshold under the settled
    # grain for the slope, the settled intercept for the crossing, and a
    # named slack for the ratio.
    fixed = (
        _OPEN_PLAN_BEFORE.replace(
            "_STI_DISTRACTION = 0.50",
            "_STI_DISTRACTION = 0.50\n_NO_DECREASE_STI_PER_M = -1e-9",
        )
        .replace("if slope >= 0.0:", "if slope >= _NO_DECREASE_STI_PER_M:")
        .replace(
            "distance = (threshold - intercept) / slope\n    if distance <= 0.0:",
            "if settled(intercept - threshold) <= 0.0:",
        )
        .replace(
            "    return distance\n", "    return (threshold - intercept) / slope\n"
        )
    )
    assert _texts(fixed, tmp_path) == []
    slacked = _ABSORPTION_BEFORE.replace(
        "ABSORPTION_RATIO_LIMIT = 0.99",
        "ABSORPTION_RATIO_LIMIT = 0.99\n_RATIO_SLACK = 1e-12",
    ).replace(
        "ratio >= ABSORPTION_RATIO_LIMIT:",
        "ratio >= ABSORPTION_RATIO_LIMIT - _RATIO_SLACK:",
    )
    assert _texts(slacked, tmp_path) == []


# ---------------------------------------------------------------------------
# Settled sites of the tree with their settling taken out again
# ---------------------------------------------------------------------------


class _Unsettle(ast.NodeTransformer):
    """Undo the fix inside one function: unwrap the settling helpers, or drop a slack."""

    def __init__(self, function: str, slack: str | None) -> None:
        self.function = function
        self.slack = slack
        self.inside = 0
        self.changes = 0

    def _scope(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> ast.AST:
        entered = node.name == self.function
        self.inside += entered
        self.generic_visit(node)
        self.inside -= entered
        return node

    visit_FunctionDef = _scope
    visit_AsyncFunctionDef = _scope

    def visit_Call(self, node: ast.Call) -> ast.AST:
        self.generic_visit(node)
        name = node.func.id if isinstance(node.func, ast.Name) else ""
        if not self.inside or not node.args:
            return node
        if name == "settled":
            self.changes += 1
            return node.args[0]
        if name == "settled_ratio":
            self.changes += 1
            return ast.BinOp(left=node.args[0], op=ast.Div(), right=node.args[1])
        if name == "settled_net_share":
            self.changes += 1
            func = ast.Attribute(
                value=ast.Name("np", ast.Load()), attr="sum", ctx=ast.Load()
            )
            return ast.Call(func=func, args=node.args, keywords=node.keywords)
        return node

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        self.generic_visit(node)
        right = node.right
        if self.inside and isinstance(right, ast.Name) and right.id == self.slack:
            self.changes += 1
            return node.left
        return node

    def visit_Name(self, node: ast.Name) -> ast.AST:
        # A named threshold under the settled grain read as the zero it stands for.
        if self.inside and node.id == self.slack and isinstance(node.ctx, ast.Load):
            self.changes += 1
            return ast.Constant(0.0)
        return node


@pytest.mark.parametrize(
    ("relative", "function", "slack"),
    [
        ("room/open_plan.py", "_sti_crossing", "_NO_DECREASE_STI_PER_M"),
        (
            "environment/propagation/noise_reducing_devices.py",
            "sound_absorption_rating",
            "_RATIO_SLACK",
        ),
        (
            "building/measurement/floor_covering_improvement.py",
            "background_corrected_level",
            None,
        ),
        ("emission/sound_power_intensity_points.py", "_test_conditions_met", None),
        ("noise_control/cabin_insulation.py", "uncertainty_conditions", None),
        ("emission/sound_power_in_situ.py", "_background_correction", None),
        ("hearing/real_ear_attenuation.py", "uniform", None),
        ("electroacoustics/headphones.py", "requirements", None),
        ("metrology/reciprocity_coupler.py", "_within", None),
        # The limit is a field of a row of ISO 3382-1 Table A.1.
        ("room/auditorium.py", "perceptibly_different", None),
    ],
)
def test_a_settled_site_unsettled_again_is_refused(
    relative: str, function: str, slack: str | None
) -> None:
    path = (_SOURCE / relative).resolve()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    mutation = _Unsettle(function, slack)
    mutated = ast.unparse(ast.fix_missing_locations(mutation.visit(tree)))
    assert mutation.changes, f"nothing to unsettle in {relative} {function}"
    assert function not in _refused_scopes(cbc.Package(_SOURCE).module(path))
    assert function in _refused_scopes(
        cbc.Package(_SOURCE, {path: mutated}).module(path)
    )


def _refused_scopes(module: cbc.Module | None) -> set[str]:
    """The functions of a module the guard refuses a comparison in."""
    assert module is not None
    return {finding.scope.rsplit(".", 1)[-1] for finding in module.findings()}


def test_the_tree_passes(capsys: pytest.CaptureFixture[str]) -> None:
    status = cbc.main([])
    assert status == 0, capsys.readouterr().out


# ---------------------------------------------------------------------------
# The rule, case by case
# ---------------------------------------------------------------------------


def test_a_margin_of_two_readings_against_a_printed_limit_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    source = """
    _MARGIN_DB = 6.0
    def correct(signal, background):
        margin = signal - background
        return margin >= _MARGIN_DB
    """
    assert _texts(source, tmp_path) == ["margin >= _MARGIN_DB"]


@pytest.mark.parametrize(
    "judged",
    [
        "settled(margin) >= _MARGIN_DB",
        "settled(margin - _MARGIN_DB) >= 0.0",
        "margin >= _MARGIN_DB - _MARGIN_SLACK",
        "margin + _MARGIN_SLACK >= _MARGIN_DB",
        "margin * (1.0 + _MARGIN_SLACK) >= _MARGIN_DB",
        "round(margin, 1) >= _MARGIN_DB",
        "signal >= _MARGIN_DB",
    ],
)
def test_a_settled_slacked_rounded_or_raw_side_is_left_alone(
    judged: str, tmp_path: pathlib.Path
) -> None:
    source = f"""
    _MARGIN_DB = 6.0
    _MARGIN_SLACK = 1e-9
    def correct(signal, background):
        margin = signal - background
        return {judged}
    """
    assert _texts(source, tmp_path) == []


@pytest.mark.parametrize(
    "judged",
    [
        # Settling the limit leaves the margin as it was.
        "margin >= float(settled(_MARGIN_DB))",
        # An epsilon that keeps a divisor off zero moves the ratio by an amount
        # the divisor decides, nothing once it is large: no slack.
        "margin / (background + 1e-12) >= _MARGIN_DB",
        "margin / (background + _DIVISOR_EPS) >= _MARGIN_DB",
        # A percentile interpolates between readings.
        "np.percentile([signal, background], 90) >= _MARGIN_DB",
    ],
)
def test_a_slack_or_a_settling_in_the_wrong_place_is_refused(
    judged: str, tmp_path: pathlib.Path
) -> None:
    source = f"""
    import numpy as np
    _MARGIN_DB = 6.0
    _DIVISOR_EPS = 1e-12
    def correct(signal, background):
        margin = signal - background
        return {judged}
    """
    assert _texts(source, tmp_path) == [judged]


@pytest.mark.parametrize(
    ("header", "slack"),
    [
        # Above the micro-unit, so a slack by its name alone.
        ("_SPREAD_TOL = 0.01", "_SPREAD_TOL"),
        ("_SPREAD_EPS = 0.01", "_SPREAD_EPS"),
        # Imported, so its value is not known here.
        ("from .tolerances import _MARGIN_SLACK", "_MARGIN_SLACK"),
        ("from . import tolerances", "tolerances.SPREAD_RTOL"),
    ],
)
def test_a_slack_is_known_by_its_name(
    header: str, slack: str, tmp_path: pathlib.Path
) -> None:
    source = f"""
    {header}
    _MARGIN_DB = 6.0
    def correct(signal, background):
        margin = signal - background
        return margin >= _MARGIN_DB - {slack}
    """
    assert _texts(source, tmp_path) == []


def test_a_constant_named_otherwise_is_no_slack(tmp_path: pathlib.Path) -> None:
    source = """
    _SPREAD_DB = 0.01
    _MARGIN_DB = 6.0
    def correct(signal, background):
        margin = signal - background
        return margin >= _MARGIN_DB - _SPREAD_DB
    """
    assert _texts(source, tmp_path) == ["margin >= _MARGIN_DB - _SPREAD_DB"]


@pytest.mark.parametrize(
    ("expression", "verdict"),
    [
        ("signal - background > 0.0", "kept"),
        ("np.mean(levels) > 0.0", "refused"),
        ("np.sum(levels * levels) > 0.0", "kept"),
        ("np.polyfit(x, levels, 1)[0] >= 0.0", "refused"),
        ("(signal - background) - _MARGIN_DB >= 0.0", "refused"),
        (
            "np.sqrt((signal - background) ** 2 - (x - background) * 2.0) > 0.0",
            "refused",
        ),
    ],
)
def test_against_zero_only_a_sign_that_can_be_wrong_is_refused(
    expression: str, verdict: str, tmp_path: pathlib.Path
) -> None:
    source = f"""
    import numpy as np
    _MARGIN_DB = 6.0
    def judge(signal, background, levels, x):
        return {expression}
    """
    assert ("refused" if _texts(source, tmp_path) else "kept") == verdict


def test_a_transcendental_quantity_or_a_count_is_left_alone(
    tmp_path: pathlib.Path,
) -> None:
    source = """
    import numpy as np
    LIMIT = 6.0
    def judge(energies, values):
        level = 10.0 * np.log10(np.mean(energies))
        share = len(values) / 3
        return level >= LIMIT, share > LIMIT
    """
    assert _texts(source, tmp_path) == []


def test_a_private_helper_is_judged_by_what_its_callers_pass(
    tmp_path: pathlib.Path,
) -> None:
    source = """
    _LIMIT_DB = 10.0
    def _exceeds(margin):
        return margin > _LIMIT_DB
    def public(signal, background):
        return _exceeds(signal - background)
    """
    assert _texts(source, tmp_path) == ["margin > _LIMIT_DB"]
    raw_only = source.replace("_exceeds(signal - background)", "_exceeds(signal)")
    assert _texts(raw_only, tmp_path) == []


def test_a_converting_helper_is_read_per_call(tmp_path: pathlib.Path) -> None:
    # Read once for all its callers, _as_float would make the reading look
    # computed because another caller passes it a difference.
    source = """
    _LIMIT_DB = 10.0
    def _as_float(value):
        return float(value)
    def reading(signal):
        return _as_float(signal) > _LIMIT_DB
    def margin(signal, background):
        return _as_float(signal - background) > _LIMIT_DB
    """
    assert [f.scope for f in _refused(source, tmp_path)] == ["margin"]


def test_a_field_is_what_the_module_builds_it_from(tmp_path: pathlib.Path) -> None:
    source = """
    from dataclasses import dataclass
    _TOLERANCE_DB = 0.5
    @dataclass(frozen=True)
    class Check:
        deviation_db: float
        @property
        def passes(self):
            return abs(self.deviation_db) <= _TOLERANCE_DB
    def check(measured, nominal):
        return Check(deviation_db=measured - nominal)
    """
    assert _texts(source, tmp_path) == ["abs(self.deviation_db) <= _TOLERANCE_DB"]


@pytest.mark.parametrize(
    "built", ["Check(measured - nominal)", "Check(deviation_db=measured - nominal)"]
)
def test_a_field_of_an_instance_built_in_place_is_followed(
    built: str, tmp_path: pathlib.Path
) -> None:
    source = f"""
    from dataclasses import dataclass
    _TOLERANCE_DB = 0.5
    @dataclass(frozen=True)
    class Check:
        deviation_db: float
    def check(measured, nominal):
        result = {built}
        return abs(result.deviation_db) <= _TOLERANCE_DB
    """
    assert _texts(source, tmp_path) == ["abs(result.deviation_db) <= _TOLERANCE_DB"]


@pytest.mark.parametrize(
    "limit", ["_TABLE[symbol].tolerance_db", "_row(symbol).tolerance_db"]
)
def test_a_field_of_a_row_of_a_published_table_is_a_limit(
    limit: str, tmp_path: pathlib.Path
) -> None:
    source = f"""
    _TABLE = {{"T30": None}}
    def _row(symbol):
        return _TABLE[symbol]
    def different(a, b, symbol):
        limit = {limit}
        return abs(a - b) >= limit
    """
    assert _texts(source, tmp_path) == ["abs(a - b) >= limit"]


def test_a_transpose_is_what_it_transposes(tmp_path: pathlib.Path) -> None:
    # ``.T`` is no upper-case constant: a length set against a tolerance that
    # scales with the drawing is a computed value against a computed one.
    source = """
    import numpy as np
    _GEOMETRY_TOLERANCE = 1e-9
    def touch(points, scale):
        tol = _GEOMETRY_TOLERANCE * scale
        return np.min(np.hypot(*points.T)) <= tol
    """
    assert _texts(source, tmp_path) == []


def test_a_chained_comparison_is_one_comparison(tmp_path: pathlib.Path) -> None:
    source = """
    _LOW_DB = 1.0
    _HIGH_DB = 3.0
    def within(signal, background):
        return _LOW_DB <= signal - background < _HIGH_DB
    """
    assert _texts(source, tmp_path) == ["_LOW_DB <= signal - background < _HIGH_DB"]


def test_the_validation_predicates_are_comparisons(tmp_path: pathlib.Path) -> None:
    source = """
    _LIMIT = 0.6
    def judge(a, b):
        return is_at_most(a / b, _LIMIT), is_positive(sum([a, -b, a]))
    """
    assert _texts(source, tmp_path) == [
        "is_at_most(a / b, _LIMIT)",
        "is_positive(sum([a, -b, a]))",
    ]


def test_a_value_computed_in_a_sibling_module_is_followed(
    tmp_path: pathlib.Path,
) -> None:
    package = tmp_path / "package"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "helpers.py").write_text(
        "def spread(levels):\n    return max(levels) - min(levels)\n", encoding="utf-8"
    )
    (package / "verdict.py").write_text(
        "from .helpers import spread\n"
        "_SPREAD_DB = 3.0\n"
        "def judge(levels):\n"
        "    return spread(levels) <= _SPREAD_DB\n",
        encoding="utf-8",
    )
    found = cbc.scan(package)
    assert [(f.path, f.text) for f in found] == [
        ("verdict.py", "spread(levels) <= _SPREAD_DB")
    ]


# ---------------------------------------------------------------------------
# The exemptions file
# ---------------------------------------------------------------------------


def test_the_exemptions_file_gives_every_entry_a_reason() -> None:
    exemptions = cbc.read_exemptions()
    assert exemptions
    assert all(reason.strip() for reasons in exemptions.values() for reason in reasons)


def test_an_exemption_without_a_reason_is_refused(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "exemptions.tsv"
    path.write_text("# header\nroom/x.py\tf\ta > 0.0\t\n", encoding="utf-8")
    with pytest.raises(ValueError, match="tab-separated"):
        cbc.read_exemptions(path)


def test_an_exemption_line_excuses_one_comparison(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "exemptions.tsv"
    line = "room/x.py\tf\ta > 0.0\tbecause\n"
    path.write_text(line + line, encoding="utf-8")
    exempt = cbc.read_exemptions(path)
    assert exempt == {("room/x.py", "f", "a > 0.0"): ["because", "because"]}
    copies = [cbc.Finding("room/x.py", line, "f", "a > 0.0", "r") for line in (3, 5, 7)]
    assert cbc.classify(copies[:2], exempt) == ([], [])
    # A third copy of an exempted comparison is refused, all three named.
    assert cbc.classify(copies, exempt) == (copies, [])
    # One copy left of the two listed: the second line is stale.
    assert cbc.classify(copies[:1], exempt) == (
        [],
        [(("room/x.py", "f", "a > 0.0"), 2, 1)],
    )


def test_an_exemption_that_covers_nothing_is_stale() -> None:
    finding = cbc.Finding("room/x.py", 3, "f", "a > 0.0", "a reason")
    gone = ("room/x.py", "g", "b > 0.0")
    refused, stale = cbc.classify([finding], {finding.key: ["kept"], gone: ["kept"]})
    assert refused == []
    assert stale == [(gone, 1, 0)]
    refused, stale = cbc.classify([finding], {})
    assert refused == [finding]
    assert stale == []


def test_a_third_copy_of_an_exempted_comparison_in_the_tree_is_refused() -> None:
    # _segment_angles writes ``z_foot >= 0.0`` twice and the file lists it
    # twice; a third copy is not covered by either line.
    relative = "aircraft/airport_noise.py"
    path = (_SOURCE / relative).resolve()
    source = path.read_text(encoding="utf-8")
    anchor = "    eq_angle = eq_angle if z_foot >= 0.0 else -eq_angle\n"
    assert source.count(anchor) == 1
    copied = source.replace(anchor, anchor * 2)
    exempt = {
        key: reasons
        for key, reasons in cbc.read_exemptions().items()
        if key[0] == relative
    }
    before = list(cbc.Package(_SOURCE).module(path).findings())
    after = list(cbc.Package(_SOURCE, {path: copied}).module(path).findings())
    assert cbc.classify(before, exempt) == ([], [])
    refused, stale = cbc.classify(after, exempt)
    assert {finding.text for finding in refused} == {"z_foot >= 0.0"}
    assert len(refused) == 3
    assert stale == []


# ---------------------------------------------------------------------------
# The exit status
# ---------------------------------------------------------------------------

_MARGIN_MODULE = """
_MARGIN_DB = 6.0
def correct(signal, background):
    margin = signal - background
    return margin >= _MARGIN_DB
"""


def _package(tmp_path: pathlib.Path, source: str) -> pathlib.Path:
    """A one-module package written from ``source``."""
    package = tmp_path / "package"
    package.mkdir()
    (package / "verdict.py").write_text(source, encoding="utf-8")
    return package


def test_the_guard_fails_on_a_refused_comparison(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    package = _package(tmp_path, _MARGIN_MODULE)
    # ``read_exemptions`` binds the real file as its default, so the function
    # is replaced: with the real file every line would be stale here, and the
    # guard would fail for that reason alone.
    monkeypatch.setattr(cbc, "read_exemptions", dict)
    assert cbc.main(["--root", str(package)]) == 1
    output = capsys.readouterr().out
    assert "verdict.py:5 in correct: margin >= _MARGIN_DB" in output


def test_the_guard_passes_on_an_exempted_comparison(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = _package(tmp_path, _MARGIN_MODULE)
    key = ("verdict.py", "correct", "margin >= _MARGIN_DB")
    monkeypatch.setattr(cbc, "read_exemptions", lambda: {key: ["a reason"]})
    assert cbc.main(["--root", str(package)]) == 0


def test_the_guard_fails_on_a_stale_exemption(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    package = _package(tmp_path, _MARGIN_MODULE.replace("margin >=", "signal >="))
    key = ("verdict.py", "correct", "margin >= _MARGIN_DB")
    monkeypatch.setattr(cbc, "read_exemptions", lambda: {key: ["a reason"]})
    assert cbc.main(["--root", str(package)]) == 1
    assert (
        "'margin >= _MARGIN_DB' in verdict.py correct 1 time(s)"
        in capsys.readouterr().out
    )


def test_the_listing_exits_zero(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    package = _package(tmp_path, _MARGIN_MODULE)
    assert cbc.main(["--list", "--root", str(package)]) == 0
    assert "verdict.py:5 [correct] margin >= _MARGIN_DB" in capsys.readouterr().out
