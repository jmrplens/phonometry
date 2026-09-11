#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Effects of vibration on structures (DIN 4150-3).

The standard is three tables and a handful of sentences carrying numbers, and
all of them are printed rather than derived, so every row here is a
transcription check: the library is asked for the guideline value, and the
answer is compared with what the page says.

Two rows are not transcriptions. Table 1 prints its foundation bands as
ranges, "5 bis 15" between 10 Hz and 50 Hz, and only Bild 1 says what a value
inside the band is: the corner values joined by straight lines on a linear
frequency axis. The midpoint rows pin that reading, which is the one thing in
this standard a reader can get wrong while copying the table correctly.

Oracle: DIN 4150-3:1999-02, Table 1 and Bild 1 on printed folio 4, Table 2 on
printed folio 5, Table 3 on printed folio 6, and Clauses 5.1, 5.2, 6.3 and
6.4 on the same three pages.
"""

from __future__ import annotations

import functools

import phonometry as ph

from ..registry import Outcome, numeric, register

_STRUCTURAL_DAMAGE = "Vibration effects on structures (DIN 4150-3)"

#: Table 1, foundation columns, on printed folio 4: the guideline peak
#: velocity in mm/s at 1 Hz, 10 Hz, 50 Hz and 100 Hz. Read against the
#: rendered page; the table prints two of the three bands as ranges, and
#: these are their ends.
_TABLE_1_FOUNDATION = {
    "commercial": (20.0, 20.0, 40.0, 50.0),
    "residential": (5.0, 5.0, 15.0, 20.0),
    "sensitive": (3.0, 3.0, 8.0, 10.0),
}
_TABLE_1_FREQUENCIES = (1.0, 10.0, 50.0, 100.0)

#: Table 1, last column: the topmost floor plane, horizontal, all frequencies.
_TABLE_1_TOP_FLOOR = {"commercial": 40.0, "residential": 15.0, "sensitive": 8.0}

#: Table 3 on printed folio 6: long-term vibration, topmost floor plane.
_TABLE_3 = {"commercial": 10.0, "residential": 5.0, "sensitive": 2.5}

#: Table 2 on printed folio 5: buried pipelines, by pipe material.
_TABLE_2 = {
    "welded_steel": 100.0,
    "concrete_or_flanged_metal": 80.0,
    "masonry_or_plastic": 50.0,
}

#: Bild 1 on printed folio 4, read at the middle of a band: a dwelling at
#: 30 Hz sits halfway up the 5 mm/s to 15 mm/s band, and a commercial
#: building at 75 Hz halfway up its 40 mm/s to 50 mm/s band.
_BILD_1_MIDPOINTS = {("residential", 30.0): 10.0, ("commercial", 75.0): 45.0}

#: The tables print whole millimetres per second, or one decimal for the
#: 2,5 of Table 3.
_TOLERANCE = 0.005

_CLASS_LABELS = {
    "commercial": "commercial and industrial buildings",
    "residential": "dwellings",
    "sensitive": "especially sensitive buildings",
}


def _chk_foundation(building_class: str, index: int) -> Outcome:
    """One printed corner of the foundation columns of Table 1."""
    frequency = _TABLE_1_FREQUENCIES[index]
    printed = _TABLE_1_FOUNDATION[building_class][index]
    computed = float(ph.vibration.guideline_velocity(building_class, frequency))
    return numeric(printed, computed, _TOLERANCE, unit="mm/s", places=3)


def _register_foundation() -> None:
    """Register the twelve foundation corner values of Table 1."""
    for building_class, label in _CLASS_LABELS.items():
        for index, frequency in enumerate(_TABLE_1_FREQUENCIES):
            register(
                _STRUCTURAL_DAMAGE,
                "DIN 4150-3:1999-02 Table 1",
                f"Short-term guideline vi at the foundation, {label}, {frequency:g} Hz",
            )(functools.partial(_chk_foundation, building_class, index))


_register_foundation()


def _chk_top_floor(building_class: str) -> Outcome:
    """The topmost floor plane column of Table 1, which has no frequency."""
    printed = _TABLE_1_TOP_FLOOR[building_class]
    computed = float(
        ph.vibration.guideline_velocity(building_class, location="top_floor")
    )
    return numeric(printed, computed, _TOLERANCE, unit="mm/s", places=3)


def _register_top_floor() -> None:
    """Register the three topmost-floor values of Table 1."""
    for building_class, label in _CLASS_LABELS.items():
        register(
            _STRUCTURAL_DAMAGE,
            "DIN 4150-3:1999-02 Table 1",
            f"Short-term guideline vi in the topmost floor plane, {label}",
        )(functools.partial(_chk_top_floor, building_class))


_register_top_floor()


def _chk_long_term(building_class: str) -> Outcome:
    """One row of Table 3."""
    printed = _TABLE_3[building_class]
    computed = float(
        ph.vibration.guideline_velocity(
            building_class, location="top_floor", duration="long_term"
        )
    )
    return numeric(printed, computed, _TOLERANCE, unit="mm/s", places=3)


def _register_long_term() -> None:
    """Register the three rows of Table 3."""
    for building_class, label in _CLASS_LABELS.items():
        register(
            _STRUCTURAL_DAMAGE,
            "DIN 4150-3:1999-02 Table 3",
            f"Long-term guideline vi in the topmost floor plane, {label}",
        )(functools.partial(_chk_long_term, building_class))


_register_long_term()


def _chk_pipeline(material: str) -> Outcome:
    """One row of Table 2."""
    printed = _TABLE_2[material]
    computed = ph.vibration.pipeline_guideline_velocity(material)
    return numeric(printed, computed, _TOLERANCE, unit="mm/s", places=3)


_PIPE_LABELS = {
    "welded_steel": "welded steel",
    "concrete_or_flanged_metal": "concrete and flanged metal",
    "masonry_or_plastic": "masonry and plastic",
}


def _register_pipelines() -> None:
    """Register the three rows of Table 2."""
    for material, label in _PIPE_LABELS.items():
        register(
            _STRUCTURAL_DAMAGE,
            "DIN 4150-3:1999-02 Table 2",
            f"Short-term guideline vi on a buried pipeline, {label}",
        )(functools.partial(_chk_pipeline, material))


_register_pipelines()


@register(
    _STRUCTURAL_DAMAGE,
    "DIN 4150-3:1999-02 Clause 6.3",
    "Long-term reduction of the pipeline guideline values",
)
def _chk_pipeline_long_term() -> Outcome:
    """Clause 6.3: Table 2 reduced to 50 % without further evidence."""
    short = ph.vibration.pipeline_guideline_velocity("welded_steel")
    long = ph.vibration.pipeline_guideline_velocity(
        "welded_steel", duration="long_term"
    )
    return numeric(0.5, long / short, 0.0005, places=4)


@register(
    _STRUCTURAL_DAMAGE,
    "DIN 4150-3:1999-02 Clause 5.1",
    "Massive engineering structures, factor on the row 1 values",
)
def _chk_massive_factor() -> Outcome:
    """Clause 5.1: row 1 raised to twice its value, recovered as a ratio."""
    plain = float(ph.vibration.guideline_velocity("commercial", 50.0))
    raised = float(
        ph.vibration.guideline_velocity("commercial", 50.0, massive_structure=True)
    )
    return numeric(2.0, raised / plain, 0.0005, places=4)


@register(
    _STRUCTURAL_DAMAGE,
    "DIN 4150-3:1999-02 Clause 5.2",
    "Vertical guideline vz for a ceiling or floor, mm/s",
)
def _chk_floor_vertical() -> Outcome:
    """Clause 5.2: 20 mm/s vertical at the point of largest vibration."""
    return numeric(
        20.0, ph.vibration.FLOOR_VERTICAL_MM_S, _TOLERANCE, unit="mm/s", places=3
    )


def _chk_bild_1(building_class: str, frequency: float) -> Outcome:
    """A value inside a band, which only Bild 1 decides."""
    printed = _BILD_1_MIDPOINTS[(building_class, frequency)]
    computed = float(ph.vibration.guideline_velocity(building_class, frequency))
    return numeric(printed, computed, _TOLERANCE, unit="mm/s", places=3)


def _register_bild_1() -> None:
    """Register the two midpoints read off Bild 1."""
    for building_class, frequency in _BILD_1_MIDPOINTS:
        register(
            _STRUCTURAL_DAMAGE,
            "DIN 4150-3:1999-02 Bild 1",
            f"Guideline vi inside a band, {_CLASS_LABELS[building_class]}, "
            f"{frequency:g} Hz",
        )(functools.partial(_chk_bild_1, building_class, frequency))


_register_bild_1()


@register(
    _STRUCTURAL_DAMAGE,
    "DIN 4150-3:1999-02 Clause 6.4",
    "Lowest horizontal natural frequency of a ten-storey building, Hz",
)
def _chk_storey_frequency() -> Outcome:
    """Clause 6.4: ``f_i ~ 10 / n``, at ten storeys."""
    return numeric(
        1.0,
        ph.vibration.storey_fundamental_frequency(10),
        0.0005,
        unit="Hz",
        places=4,
    )
