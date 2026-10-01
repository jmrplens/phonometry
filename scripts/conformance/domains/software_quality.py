#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Quality assurance of outdoor sound software, by ISO 17534-1 itself.

ISO 17534-1 prints three things a program can be checked against. Table C.1
gives the ranking positions of the 0,1- and 0,9-quantiles for samples of 20 to
50 values, and Formulas (C.1) and (C.2) take over above 50; the example that
follows sorts 25 level differences and reads the two quantiles off them.
Table B.2 is the worked Test Case Results Comparison form of a test case
"T XX": nine results, each beside the limits of its certified result, all
answered "yes".

Table C.1 is symmetric in every row and Formula (C.2) is not the rule it
follows, so the two do not join at 50 values; Formula (C.1) continues the
table's first column and the break is in (C.2) alone. DIN 45687:2006-05,
Annex F.4, from which ISO 17534-1 Annex C was taken, prints the same table
and the same two formulas, the formulas as a supplement to VDI 3723 Blatt 1,
the source of the table; neither document says whether the seam is
deliberate. VDI 3723 Blatt 1 prints the same ranks in its Tables 5 and 6,
symmetric, and stops at 50 values with no formula of its own. Both standards
print (C.2) the same way, so the seam is kept as printed, and the rows below
hold the library to the table up to 50, in both its printings, and to the
formulas above.

Oracle: BS ISO 17534-1:2015, the UK implementation of ISO 17534-1:2015,
whose pages carry the ISO 17534-1:2015(E) text: Table B.2 on printed folio 16
(PDF page 24); Table C.1, Formulas (C.1) and (C.2) and the example of C.4 on
printed folio 20 (PDF page 28). VDI 3723 Blatt 1:1993-05: Table 5 on Seite 7
and 8, Table 6 on Seite 8 (PDF pages 7 and 8).
"""

from __future__ import annotations

import reference_data as ref

from phonometry import environment

from ..registry import Outcome, count, record, register

_QA = "Outdoor sound software quality assurance (ISO 17534-1)"

#: The sample sizes the formulas are checked over: from the first one above
#: Table C.1 to a map of a thousand sample points.
_FORMULA_RANGE = range(51, 1001)


@register(
    _QA,
    "ISO 17534-1:2015 Table C.1",
    "Ranking position R(q0,1) of the 0,1-quantile, N = 20 to 50",
)
def _chk_table_c1_q01() -> Outcome:
    """The first column of Table C.1, row by row."""
    matching = sum(
        environment.ranking_positions(n)[0] == r01
        for n, r01, _ in ref.ISO17534_1_TABLE_C1
    )
    return count(matching, len(ref.ISO17534_1_TABLE_C1), subject="rows of Table C.1")


@register(
    _QA,
    "ISO 17534-1:2015 Table C.1",
    "Ranking position R(q0,9) of the 0,9-quantile, N = 20 to 50",
)
def _chk_table_c1_q09() -> Outcome:
    """The second column of Table C.1, row by row.

    Formula (C.2) gives one rank less than this column for N = 21 to 25, 31 to
    35 and 41 to 45, so this row passes only while the library reads the
    table, not the formula, up to 50 values.
    """
    matching = sum(
        environment.ranking_positions(n)[1] == r09
        for n, _, r09 in ref.ISO17534_1_TABLE_C1
    )
    return count(matching, len(ref.ISO17534_1_TABLE_C1), subject="rows of Table C.1")


@register(
    _QA,
    "VDI 3723 Blatt 1:1993-05 Tables 5 and 6",
    "Ranking positions of L_x,90 and L_x,10, the source of Table C.1, N = 20 to 50",
)
def _chk_vdi_3723_tables_5_and_6() -> Outcome:
    """Table C.1 read against the guideline DIN 45687 F.4 bases it on.

    Column k of Table 6 (L_x;90) is R(q0,1) and column k of Table 5 (L_x;10)
    is R(q0,9), both read on the guideline's own pages, so the ranks the
    library publishes rest on two printings of the table and not on one.
    """
    lx90 = dict(ref.VDI3723_1_TABLE_6_K)
    lx10 = dict(ref.VDI3723_1_TABLE_5_K)
    matching = sum(environment.ranking_positions(n) == (lx90[n], lx10[n]) for n in lx90)
    return count(matching, len(lx90), subject="rows of Tables 5 and 6")


@register(
    _QA,
    "ISO 17534-1:2015 Formulas (C.1) and (C.2)",
    "Ranking positions above 50 values, N = 51 to 1000",
)
def _chk_formulas_above_fifty() -> Outcome:
    """IP((N + 4)/10) and IP(9N/10) + 1, as printed, for every N from 51."""
    matching = sum(
        environment.ranking_positions(n) == ((n + 4) // 10, (9 * n) // 10 + 1)
        for n in _FORMULA_RANGE
    )
    return count(matching, len(_FORMULA_RANGE), subject="sample sizes")


def _example() -> environment.LevelDifferenceQuantiles:
    return environment.level_difference_quantiles(ref.ISO17534_1_EXAMPLE_DIFFERENCES_DB)


@register(
    _QA,
    "ISO 17534-1:2015 C.4, EXAMPLE",
    "Ranking positions of 25 level differences",
)
def _chk_example_ranks() -> Outcome:
    """The example prints "R(q0,1) = 2 and R(q0,9) = 24"."""
    result = _example()
    r01, r09 = ref.ISO17534_1_EXAMPLE_RANKS
    return record(
        {"R(q0,1)": r01, "R(q0,9)": r09},
        {"R(q0,1)": result.rank_q01, "R(q0,9)": result.rank_q09},
    )


@register(
    _QA,
    "ISO 17534-1:2015 C.4, EXAMPLE",
    "Quantiles q0,1 and q0,9 of 25 level differences, dB",
)
def _chk_example_quantiles() -> Outcome:
    """The example prints "q0,1 = -1 dB and q0,9 = 3 dB", two values of the sample."""
    result = _example()
    q01, q09 = ref.ISO17534_1_EXAMPLE_QUANTILES_DB
    return record(
        {"q0,1": q01, "q0,9": q09},
        {"q0,1": result.q01_db, "q0,9": result.q09_db},
        unit="dB",
    )


def _table_b2() -> environment.CalculationVerification:
    rows = ref.ISO17534_1_TABLE_B2
    return environment.verify_calculation_results(
        [row[3] for row in rows],
        [row[2] for row in rows],
        [row[1] for row in rows],
        labels=[row[0] for row in rows],
    )


@register(
    _QA,
    "ISO 17534-1:2015 Table B.2",
    "Result inside tolerances, eight octave bands and the total of test case T XX",
)
def _chk_table_b2_inside() -> Outcome:
    """Every row of the worked TRC form answers "yes"."""
    verdict = _table_b2()
    return count(
        sum(verdict.inside),
        len(verdict.inside),
        subject='rows answered "yes"',
    )


@register(
    _QA,
    "ISO 17534-1:2015 Table A.5, note a; Table B.2",
    "Width of each certified interval, twice the 0,05 dB tolerance",
)
def _chk_table_b2_tolerance() -> Outcome:
    """The limits of Table B.2 lie 0,05 dB either side of each certified result.

    Read against the tolerance the library publishes for Table A.5, so the
    constant a user builds limits with is the one the printed form was built
    with. Compared to the hundredth of a decibel the form prints.
    """
    width = round(2.0 * environment.CERTIFIED_RESULT_TOLERANCE_DB, 2)
    matching = sum(
        round(upper - lower, 2) == width
        for _, upper, lower, _ in ref.ISO17534_1_TABLE_B2
    )
    return count(matching, len(ref.ISO17534_1_TABLE_B2), subject="rows of Table B.2")
