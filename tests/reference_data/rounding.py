#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Printed rounding examples of ISO 80000-1:2009 Annex B.

Several standards ask for a result "rounded to the nearest integer" and name
no rule for a tie: ISO 10847:1997 10 c), ISO 11546-1:1995 and ISO 11546-2:1995
9.4 and ISO 11957:1996 11.4 e) among them. Annex B of ISO 80000-1:2009 names
two, and its printed examples are the oracle the library's rounding is held to.

Stdlib only, like every module of this package.
"""

from __future__ import annotations

#: ISO 80000-1:2009, Annex B "Rounding of numbers": B.2 and B.3 Rule A with
#: both its examples on PDF page 43, printed folio 35, and Rule B with the
#: remark that Rule A is generally preferable on PDF page 44, printed folio 36.
#: Each entry is a printed number, its printed rounding range and the number of
#: whole ranges it is rounded to. B.1 defines the rounding range as the
#: interval between the integral multiples being rounded to, so the number
#: over the range, rounded to the nearest integer, is that count.
#:
#: The two ties of Rule A at rounding range 10 are the pair that decides the
#: rule: 1 225,0 goes to 1 220 and 1 235,0 to 1 240, the even multiple in both
#: cases, where Rule B would give 1 230 and 1 240. Both are exact in binary. The
#: ties Rule A prints at rounding range 0,1 are deliberately left out: 12,35
#: has no exact double, so the tie is gone before any code sees it and a
#: comparison would test the binary representation rather than the rule.
ISO80000_1_ANNEX_B_ROUNDINGS: dict[str, tuple[float, float, int]] = {
    "B.2, 12,223 at range 0,1": (12.223, 0.1, 122),
    "B.2, 12,251 at range 0,1": (12.251, 0.1, 123),
    "B.2, 12,275 at range 0,1": (12.275, 0.1, 123),
    "B.2, 1 223,3 at range 10": (1223.3, 10.0, 122),
    "B.2, 1 225,1 at range 10": (1225.1, 10.0, 123),
    "B.2, 1 227,5 at range 10": (1227.5, 10.0, 123),
    "B.3 Rule A, 1 225,0 at range 10": (1225.0, 10.0, 122),
    "B.3 Rule A, 1 235,0 at range 10": (1235.0, 10.0, 124),
}

#: The two exact ties of Rule A among them, by their key above.
ISO80000_1_RULE_A_TIES: tuple[str, str] = (
    "B.3 Rule A, 1 225,0 at range 10",
    "B.3 Rule A, 1 235,0 at range 10",
)
