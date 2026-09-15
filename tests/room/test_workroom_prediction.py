#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for workroom noise prediction (ISO 11690-3:1998).

The oracle is Annex C: eight machines with their two declared emission values
in a room of 195 m2, with the level increase at each machine's own workstation
read off Figure C.1 and tabulated in Table C.2. Seven of the eight rows fall
inside the diagram and the library reproduces them within the half decibel the
diagram is drawn to; the eighth runs off the top of it.

Annex B is the second oracle, and the arithmetic one: a 20 m by 15 m by 7 m
workroom worked twice, first as two machines are installed and then as a third
is chosen between the two models on offer, with eight levels printed to a tenth
of a decibel. Its workstation labels contradict its own results, so everything
below anchors on the printed coordinates and never on W1 and W2. Three
published worked examples stand where neither annex reaches: a German data
sheet for the step from a reverberation time to an absorption area, Ver &
Beranek for the energy addition at a workstation with nine machines around it,
and Barron for the direct-plus-reverberant field each contribution is read
from. Every printed number is in ``tests/reference_data/workroom_prediction.py``
(Barron's Table 7-5 in ``enclosure_cabin_insulation.py``), with its folio and
page, and the conformance rows read it there too.
"""

from __future__ import annotations

import math

import pytest
from reference_data import enclosure_cabin_insulation as enclosure
from reference_data import workroom_prediction as oracle

from phonometry import room
from phonometry.room.workroom_prediction import (
    FITTING_DETAIL_LEVELS,
    PREDICTION_METHODS,
    ROOM_DETAIL_LEVELS,
    SOURCE_DETAIL_LEVELS,
)


@pytest.mark.parametrize("machine", sorted(oracle.ANNEX_C_MACHINES_DB))
def test_the_increase_reproduces_table_c2(machine: str) -> None:
    power, emission, printed_increase, printed_level = oracle.ANNEX_C_MACHINES_DB[
        machine
    ]
    increase = room.workstation_level_increase(
        sound_power_level_db=power,
        emission_level_db=emission,
        absorption_area_m2=oracle.ANNEX_C_ABSORPTION_M2,
    )
    level = room.workstation_level(
        sound_power_level_db=power,
        emission_level_db=emission,
        absorption_area_m2=oracle.ANNEX_C_ABSORPTION_M2,
    )
    assert increase == pytest.approx(printed_increase, abs=0.45)
    assert level == pytest.approx(printed_level, abs=0.45)


def test_the_eighth_machine_runs_off_the_top_of_figure_c1() -> None:
    """Table C.2 prints the edge of the diagram for M8 (see the errata)."""
    power, emission, printed_increase, _ = oracle.ANNEX_C_M8_DB
    increase = room.workstation_level_increase(
        sound_power_level_db=power,
        emission_level_db=emission,
        absorption_area_m2=oracle.ANNEX_C_ABSORPTION_M2,
    )
    assert increase == pytest.approx(12.4, abs=0.1)
    assert increase > printed_increase


def test_a_bigger_room_adds_less() -> None:
    small = room.workstation_level_increase(
        sound_power_level_db=100.0, emission_level_db=80.0, absorption_area_m2=50.0
    )
    large = room.workstation_level_increase(
        sound_power_level_db=100.0, emission_level_db=80.0, absorption_area_m2=5000.0
    )
    assert small > large
    assert large == pytest.approx(0.3, abs=0.1)


def test_an_emission_level_above_the_power_level_is_refused() -> None:
    with pytest.raises(ValueError, match="no surface at all"):
        room.workstation_level_increase(
            sound_power_level_db=90.0, emission_level_db=95.0, absorption_area_m2=200.0
        )


def test_the_contributions_add_on_an_energy_basis() -> None:
    total = room.total_workstation_level([80.0, 80.0])
    assert total == pytest.approx(83.0103, abs=1e-3)


def test_the_background_counts_as_one_more_contribution() -> None:
    with_background = room.total_workstation_level([80.0], existing_level_db=80.0)
    assert with_background == pytest.approx(83.0103, abs=1e-3)


def test_the_fitting_density_is_the_surface_over_four_volumes() -> None:
    assert room.fitting_density(400.0, 1000.0) == pytest.approx(0.1)


def test_the_four_categories_are_the_printed_ones() -> None:
    assert sorted(PREDICTION_METHODS) == ["1", "2a", "2b", "2c"]
    assert room.prediction_method("1").family == "diffuse field"
    assert room.prediction_method("2c").family == "geometrical"
    assert len(ROOM_DETAIL_LEVELS) == 4
    assert len(FITTING_DETAIL_LEVELS) == 4
    assert len(SOURCE_DETAIL_LEVELS) == 3


def test_an_unknown_category_is_refused() -> None:
    with pytest.raises(ValueError, match="Table 4"):
        room.prediction_method("3")


def test_the_diffuse_field_method_asks_for_the_least() -> None:
    verdict = room.detail_is_sufficient(
        "1", room_detail=1, fitting_detail=1, source_detail=1
    )
    assert verdict.satisfied is True


def test_a_room_described_too_coarsely_for_ray_tracing_is_reported() -> None:
    verdict = room.detail_is_sufficient(
        "1", room_detail=4, fitting_detail=1, source_detail=1
    )
    assert verdict.satisfied is False
    assert verdict.room_ok is False
    assert verdict.fittings_ok is True


def test_the_annex_d_example_matches_table_d1() -> None:
    """D.1 picks category 2a with room 2, fittings 1 and source 1."""
    verdict = room.detail_is_sufficient(
        "2a", room_detail=2, fitting_detail=1, source_detail=1
    )
    assert verdict.satisfied is True


def test_a_level_no_table_prints_is_refused() -> None:
    with pytest.raises(ValueError, match="Table 3"):
        room.detail_is_sufficient(
            "2a", room_detail=1, fitting_detail=1, source_detail=4
        )


def test_the_typical_ranges_are_the_printed_ones() -> None:
    assert room.typical_decay_range("near") == (5.0, 6.0)
    assert room.typical_decay_range("middle") == (2.0, 5.0)
    assert room.typical_decay_range("far") == (6.0, None)
    assert room.typical_excess_range("middle") == (2.0, 10.0)


def test_an_unknown_region_is_refused() -> None:
    with pytest.raises(ValueError, match="4.3"):
        room.typical_decay_range("close")


def test_the_regions_the_clause_leaves_open_stay_open() -> None:
    """4.3 prints no ceiling in the far region and no DLf outside the middle.

    ISO 11690-3:1998 in its BS EN ISO 11690-3:1999 printing, 4.3 on printed
    folios 2 and 3 (PDF pages 12 and 13).
    """
    assert room.typical_decay_range("far")[1] is None
    assert room.typical_excess_range("near") == (None, None)
    assert room.typical_excess_range("far") == (None, None)


@pytest.mark.parametrize("machine", sorted(oracle.ANNEX_C_MACHINES_DB))
def test_the_workstation_level_rounds_to_the_printed_integer(machine: str) -> None:
    """Table C.2 prints L'pA as a whole number, and all seven of them land.

    BS EN ISO 11690-3:1999, Table C.1 on printed folio 19 (PDF page 29) and
    Table C.2 on printed folio 20 (PDF page 30).
    """
    power, emission, _, printed_level = oracle.ANNEX_C_MACHINES_DB[machine]
    level = room.workstation_level(
        sound_power_level_db=power,
        emission_level_db=emission,
        absorption_area_m2=oracle.ANNEX_C_ABSORPTION_M2,
    )
    assert round(level) == printed_level


# --- Annex B, the example the technical report works itself ----------------
#
# ISO 11690-3:1998 Annex B as printed in BS EN ISO 11690-3:1999: Figure B.1
# and Tables B.2 and B.3 on printed folio 16 (PDF page 26), Table B.4 on
# printed folio 17 (PDF page 27), and Tables B.5 to B.9 on printed folio 18
# (PDF page 28).

#: C.1 reads a declared emission level as a free-field value measured with the
#: machine on a reflecting floor, and that half space is what the direct term
#: of Annex B radiates into.
ANNEX_B_DIRECTIVITY = 2.0

#: The three workstation positions and the four machines of Tables B.4 to B.8,
#: named by where they stand.
BESIDE_M2 = oracle.ANNEX_B_BESIDE_M2
FAR_CORNER = oracle.ANNEX_B_FAR_CORNER
BESIDE_THE_NEW_MACHINE = oracle.ANNEX_B_BESIDE_THE_NEW_MACHINE
ANNEX_B_M1 = oracle.ANNEX_B_MACHINES["M1"]
ANNEX_B_M2 = oracle.ANNEX_B_MACHINES["M2"]
ANNEX_B_M3 = oracle.ANNEX_B_MACHINES["M3"]
ANNEX_B_M4 = oracle.ANNEX_B_MACHINES["M4"]

#: Table B.9, the two "after" columns, keyed by the choice.
PRINTED_CASE_B = dict(
    zip(("first", "second"), oracle.ANNEX_B_PRINTED_CASE_B_DB.values(), strict=True)
)


def annex_b_absorption_m2() -> float:
    """A of the workroom, from the printed dimensions and coefficient."""
    length, width, height = oracle.ANNEX_B_ROOM_M
    faces = (
        length * width,
        length * width,
        length * height,
        length * height,
        width * height,
        width * height,
    )
    return float(
        room.equivalent_absorption_area(
            [(area, oracle.ANNEX_B_MEAN_ABSORPTION) for area in faces]
        )
    )


def annex_b_level(
    station: tuple[float, float, float],
    machines: tuple[tuple[float, float, tuple[float, ...], object], ...],
    *,
    existing_level_db: float | None = None,
) -> float:
    """What Annex B hears at one position once *machines* are running."""
    absorption = annex_b_absorption_m2()
    parts = []
    for power, emission, position, own_station in machines:
        if own_station == station:
            parts.append(
                room.workstation_level(
                    sound_power_level_db=power,
                    emission_level_db=emission,
                    absorption_area_m2=absorption,
                )
            )
        else:
            parts.append(
                float(
                    room.steady_state_spl(
                        power,
                        math.dist(position, station),
                        absorption_area=absorption,
                        directivity=ANNEX_B_DIRECTIVITY,
                    )
                )
            )
    return room.total_workstation_level(parts, existing_level_db=existing_level_db)


def annex_b_case_a() -> dict[str, float]:
    """The two levels of case A, by position."""
    return {
        "beside M2": annex_b_level(BESIDE_M2, (ANNEX_B_M1, ANNEX_B_M2)),
        "far corner": annex_b_level(
            FAR_CORNER,
            (ANNEX_B_M1, ANNEX_B_M2),
            existing_level_db=oracle.ANNEX_B_BACKGROUND_DB,
        ),
    }


def annex_b_case_b(
    new_machine: tuple[float, float, tuple[float, ...], object],
) -> dict[str, float]:
    """The three levels of case B, by position, for one machine on offer."""
    machines = (ANNEX_B_M1, ANNEX_B_M2, new_machine)
    return {
        "beside M2": annex_b_level(BESIDE_M2, machines),
        "far corner": annex_b_level(
            FAR_CORNER, machines, existing_level_db=oracle.ANNEX_B_BACKGROUND_DB
        ),
        "beside the new machine": annex_b_level(BESIDE_THE_NEW_MACHINE, machines),
    }


def test_the_printed_room_has_the_absorption_area_annex_b_works_with() -> None:
    """S = 1 090 m2 at a mean absorption of 0,15, so A = 163,5 m2."""
    assert annex_b_absorption_m2() == pytest.approx(163.5)


def test_the_two_kinds_of_contribution_of_annex_b() -> None:
    """A distant machine comes off the room curve, its own one from Annex C."""
    absorption = annex_b_absorption_m2()
    distant = float(
        room.steady_state_spl(
            95.0,
            math.dist((10.0, 3.0, 1.0), BESIDE_M2),
            absorption_area=absorption,
            directivity=ANNEX_B_DIRECTIVITY,
        )
    )
    own = room.workstation_level(
        sound_power_level_db=90.0, emission_level_db=77.0, absorption_area_m2=absorption
    )
    assert math.dist((10.0, 3.0, 1.0), BESIDE_M2) == pytest.approx(7.0965, abs=1e-4)
    assert distant == pytest.approx(79.413, abs=1e-3)
    assert own == pytest.approx(78.726, abs=1e-3)


@pytest.mark.parametrize("where", sorted(oracle.ANNEX_B_PRINTED_CASE_A_DB))
def test_case_a_reproduces_table_b6(where: str) -> None:
    """Table B.6: 82,1 dB beside M2 and 80,3 dB in the far corner."""
    assert annex_b_case_a()[where] == pytest.approx(
        oracle.ANNEX_B_PRINTED_CASE_A_DB[where], abs=0.05
    )


@pytest.mark.parametrize("choice", sorted(PRINTED_CASE_B))
@pytest.mark.parametrize("where", sorted(PRINTED_CASE_B["first"]))
def test_case_b_reproduces_table_b9(choice: str, where: str) -> None:
    """Table B.9, the six levels printed for the two machines on offer.

    Held to the half step of the tenth the table prints, with one exception
    named rather than absorbed into a wider tolerance for all six: the cell
    beside the new machine with the louder choice comes back 89,337 dB against
    a printed 89,4 dB, 0,063 dB under it. The annex prints no contribution that
    would locate that last hundredth, so the departure is pinned as it is.
    """
    machine = ANNEX_B_M3 if choice == "first" else ANNEX_B_M4
    got = annex_b_case_b(machine)[where]
    printed = PRINTED_CASE_B[choice][where]
    if (choice, where) == ("first", "beside the new machine"):
        assert got - printed == pytest.approx(-0.063, abs=0.001)
    else:
        assert got == pytest.approx(printed, abs=0.05)


def test_the_annex_b_results_belong_to_the_positions_not_to_the_labels() -> None:
    """Figure B.1 and Tables B.5 and B.8 disagree, and the results decide it.

    Tables B.5 and B.8 put W1 at (3, 12, 1,6) and W2 at (17, 4, 1,6); Figure
    B.1 draws W1 beside M2 and W2 alone in the far corner. The station beside
    M2 stands 1,2 m from a 90 dB machine and 7,1 m from a 95 dB one, so it
    cannot be the quieter of the two, and the printed levels only come back
    when they are read the way the figure draws them.
    """
    levels = annex_b_case_a()
    assert levels["beside M2"] > levels["far corner"]
    # What the tables' own coordinates would demand of each position.
    assert levels["beside M2"] != pytest.approx(80.3, abs=0.1)
    assert levels["far corner"] != pytest.approx(82.1, abs=0.1)
    assert abs(levels["far corner"] - 82.1) == pytest.approx(1.83, abs=0.01)


# --- The worked examples that stand where neither annex prints one ----------

#: IFA-LSA 01-234 (2020), Tab. 4.2: the volume and the boundary area the page
#: works out of the hall it prints.
IFA_LENGTH_M, IFA_BREADTH_M, IFA_HEIGHT_M = oracle.IFA_LSA_01_234_HALL_M
IFA_VOLUME_M3 = IFA_LENGTH_M * IFA_BREADTH_M * IFA_HEIGHT_M
IFA_SURFACE_M2 = 2.0 * (
    IFA_BREADTH_M * IFA_LENGTH_M
    + IFA_HEIGHT_M * IFA_LENGTH_M
    + IFA_HEIGHT_M * IFA_BREADTH_M
)


def test_the_printed_geometry_of_the_ifa_hall() -> None:
    """The sheet prints V = 6 000 m3 and S = 2 200 m2 for a 30 by 20 by 10 m hall."""
    assert IFA_VOLUME_M3 == pytest.approx(6000.0)
    assert IFA_SURFACE_M2 == pytest.approx(2200.0)


def test_the_ifa_hall_reproduces_tab_4_2() -> None:
    """Tab. 4.2: 279, 257, 296 and 391 m2, and 0,13, 0,12, 0,13 and 0,18."""
    areas = room.sabine_absorption_area(
        IFA_VOLUME_M3,
        oracle.IFA_LSA_01_234_REVERBERATION_S,
        speed_of_sound=oracle.IFA_LSA_01_234_SPEED_M_S,
    )
    assert [round(float(area)) for area in areas] == list(
        oracle.IFA_LSA_01_234_PRINTED_AREA_M2
    )
    assert [round(float(area) / IFA_SURFACE_M2, 2) for area in areas] == list(
        oracle.IFA_LSA_01_234_PRINTED_ABSORPTION
    )


def test_the_worked_500_hz_step_of_the_ifa_sheet() -> None:
    """A = 0,163 . 6000 / 3,5 m2, printed as approximately 279 m2."""
    area = float(
        room.sabine_absorption_area(
            IFA_VOLUME_M3, 3.5, speed_of_sound=oracle.IFA_LSA_01_234_SPEED_M_S
        )
    )
    assert area == pytest.approx(279.454, abs=1e-3)
    assert area / IFA_SURFACE_M2 == pytest.approx(0.127, abs=1e-3)


def test_the_energy_addition_reproduces_table_7_4() -> None:
    """Ver & Beranek 2e Table 7.4: nine machines around one assembly bench.

    I. L. Ver and L. L. Beranek (eds.), Noise and Vibration Control
    Engineering, 2nd edition, Wiley, 2006: Table 7.4 on printed folio 200 (PDF
    page 204) prints the nine contributions and the two totals, and the text
    on printed folio 199 (PDF page 203) prints the 3,7 dB benefit.

    The nine contributions are themselves printed to a tenth of a decibel, so
    their sum can only be recovered to half a step: 82,45 dB against a printed
    82,4 dB before the ceiling treatment. The total after it, and the 3,7 dB
    benefit the text draws from the pair, both round as printed.
    """
    before = room.total_workstation_level(list(oracle.VER_BERANEK_TABLE_7_4_BEFORE_DB))
    after = room.total_workstation_level(list(oracle.VER_BERANEK_TABLE_7_4_AFTER_DB))
    printed_before, printed_after = oracle.VER_BERANEK_TABLE_7_4_TOTALS_DB
    assert before == pytest.approx(82.450, abs=5e-3)
    assert after == pytest.approx(78.708, abs=5e-3)
    assert before - after == pytest.approx(
        oracle.VER_BERANEK_TREATMENT_BENEFIT_DB, abs=0.05
    )
    assert round(after, 1) == printed_after
    assert abs(before - printed_before) <= 0.06


# --- Barron (2003), the field each contribution is read from ----------------
#
# R. F. Barron, Industrial Noise Control and Acoustics, Marcel Dekker, New York,
# 2003: Example 7-8 on printed folios 307 to 309 (PDF pages 319 to 321), with
# Table 7-5 on folio 308 (PDF page 320), and Example 7-6 on folio 298 (PDF page
# 310). The book prints its folios only in the text layer of the electronic
# edition, so these are its own pagination.


def test_barron_example_7_8_reproduces_table_7_5() -> None:
    """The six printed octave-band levels, from the printed room constants."""
    levels = room.steady_state_spl(
        enclosure.BARRON_TABLE_7_5_LW_DB,
        enclosure.BARRON_EXAMPLE_7_8_OPERATOR_DISTANCE_M,
        enclosure.BARRON_TABLE_7_5_ROOM_CONSTANT_M2,
        directivity=1.0,
    )
    got = [round(float(level) + oracle.BARRON_IMPEDANCE_TERM_DB, 1) for level in levels]
    assert got == list(enclosure.BARRON_TABLE_7_5_LP_WITHOUT_DB)


def test_the_worked_500_hz_line_of_barron_example_7_8() -> None:
    """The book prints 114 + (-11,2) + 0,1 = 102,9 dB."""
    band = 2
    power = enclosure.BARRON_TABLE_7_5_LW_DB[band]
    level = float(
        room.steady_state_spl(
            power,
            enclosure.BARRON_EXAMPLE_7_8_OPERATOR_DISTANCE_M,
            enclosure.BARRON_TABLE_7_5_ROOM_CONSTANT_M2[band],
            directivity=1.0,
        )
    )
    assert level - power == pytest.approx(-11.2, abs=0.05)
    assert level + oracle.BARRON_IMPEDANCE_TERM_DB == pytest.approx(
        enclosure.BARRON_TABLE_7_5_LP_WITHOUT_DB[band], abs=0.05
    )


def test_the_2_khz_absorption_coefficient_of_table_7_5_is_not_its_room_constant() -> (
    None
):
    """The room constant row prints 47,88 m2, which is 0,041 and not 0,043."""
    assert float(
        room.room_constant(enclosure.BARRON_EXAMPLE_7_8_SURFACE_M2, 0.041)
    ) == pytest.approx(enclosure.BARRON_TABLE_7_5_ROOM_CONSTANT_M2[4], abs=5e-3)
    assert float(
        room.room_constant(
            enclosure.BARRON_EXAMPLE_7_8_SURFACE_M2,
            enclosure.BARRON_TABLE_7_5_ABSORPTION_AT_2_KHZ,
        )
    ) == pytest.approx(50.32, abs=5e-3)
    from_the_printed_coefficient = float(
        room.steady_state_spl(
            113.0,
            enclosure.BARRON_EXAMPLE_7_8_OPERATOR_DISTANCE_M,
            room.room_constant(
                enclosure.BARRON_EXAMPLE_7_8_SURFACE_M2,
                enclosure.BARRON_TABLE_7_5_ABSORPTION_AT_2_KHZ,
            ),
            directivity=1.0,
        )
    )
    assert (
        round(from_the_printed_coefficient + oracle.BARRON_IMPEDANCE_TERM_DB, 1)
        != 102.8
    )


def test_barron_example_7_6() -> None:
    """A Jordan refiner 4 m away in a room of 900 m2 at 0,05, printed 94,8 dB."""
    room_constant = float(
        room.room_constant(
            oracle.BARRON_EXAMPLE_7_6_SOURCE_SURFACE_M2,
            oracle.BARRON_EXAMPLE_7_6_SOURCE_ABSORPTION,
        )
    )
    assert round(room_constant, 2) == oracle.BARRON_EXAMPLE_7_6_SOURCE_ROOM_CONSTANT_M2
    level = (
        float(
            room.steady_state_spl(
                oracle.BARRON_EXAMPLE_7_6_POWER_LEVEL_DB,
                oracle.BARRON_EXAMPLE_7_6_SOURCE_DISTANCE_M,
                room_constant,
                directivity=oracle.BARRON_EXAMPLE_7_6_DIRECTIVITY,
            )
        )
        + oracle.BARRON_IMPEDANCE_TERM_DB
    )
    assert level == pytest.approx(94.849, abs=1e-3)
    assert round(level, 1) == oracle.BARRON_EXAMPLE_7_6_SOURCE_ROOM_LEVEL_DB
