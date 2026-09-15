#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Behaviour of the room-to-room chain: closed forms, options and validation.

Oracles: the closed form of Norton & Karczub 2e Equation (4.101),
``NR = TL - 10 lg[S_w / (S_2 alpha_2 + tau S_w)]``, evaluated here with plain
arithmetic; the identity ``NR = TL`` when the receiving-room absorption equals
the partition area; and the exact ``10 lg Q`` of the sound power models of
Table 4.5. The published worked answers of Norton live in
``test_room_to_room_norton.py``; the one of Barron (2003) for a receiver near
the partition, Example 7-6, lives here beside the closed forms of its two
branches.
"""

from __future__ import annotations

import dataclasses
import math
from typing import TYPE_CHECKING

import numpy as np
import pytest
from reference_data import workroom_prediction as barron

from phonometry import noise_control, room

if TYPE_CHECKING:
    from phonometry.noise_control.room_to_room import RoomToRoomResult

_BANDS = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0])
_SOURCE = np.array([90.0, 88.0, 86.0, 84.0, 82.0, 80.0])
#: A flat receiving-room absorption equal to the partition area, so the
#: logarithm of Eq. (4.101) vanishes and NR is exactly TL.
_ABSORPTION = np.full(6, 20.0)
_NAN_SPECTRUM = np.full(6, np.nan)
_NO_ABSORPTION = np.zeros(6)
_FLAT_SOURCE = np.full(6, 95.0)
_NAN = float("nan")


def _chain(**kwargs: object) -> RoomToRoomResult:
    """A plain six-band chain with round numbers, for the option tests."""
    defaults: dict[str, object] = {
        "source": noise_control.SourceRoom(level=_SOURCE),
        "criterion": noise_control.DesignCriterion(family="NC"),
    }
    defaults.update(kwargs)
    return noise_control.room_to_room_transmission(
        _BANDS,
        40.0,
        20.0,
        _ABSORPTION,
        **defaults,  # type: ignore[arg-type]
    )


def _powered_chain() -> RoomToRoomResult:
    """A chain with every spectrum filled in, for the band-axis tests.

    ``source_power_level`` is only carried when the source room was described
    by its sound power level, and the criterion rows only exist with a target,
    so the rows that have to agree are all present here at once.
    """
    return noise_control.room_to_room_transmission(
        _BANDS,
        40.0,
        20.0,
        _ABSORPTION,
        source=noise_control.SourceRoom(
            power_level=np.full(6, 100.0), room_constant=50.0
        ),
        criterion=noise_control.DesignCriterion(target=45.0),
    )


def test_noise_reduction_equals_transmission_loss_when_areas_match() -> None:
    """``S_2 alpha_2 = S_w`` makes the logarithm vanish, so ``NR = TL`` exactly."""
    result = _chain()
    assert np.allclose(result.noise_reduction, 40.0)
    assert np.allclose(result.received_level, result.source_level - 40.0)


def test_noise_reduction_closed_form() -> None:
    """Equation (4.101) reproduced band by band with plain arithmetic."""
    absorption = np.array([5.0, 10.0, 20.0, 40.0, 60.0, 80.0])
    tl = np.array([20.0, 25.0, 30.0, 35.0, 40.0, 45.0])
    result = noise_control.room_to_room_transmission(
        _BANDS,
        tl,
        12.0,
        absorption,
        source=noise_control.SourceRoom(level=100.0),
    )
    expected = [
        t - 10.0 * math.log10(12.0 / a) for t, a in zip(tl, absorption, strict=True)
    ]
    assert np.allclose(result.noise_reduction, expected)


def test_partition_transmission_term_adds_absorption() -> None:
    """``include_partition_transmission`` adds ``tau S_w`` to the denominator."""
    plain = _chain()
    with_term = _chain(include_partition_transmission=True)
    tau = 10.0 ** (-40.0 / 10.0)
    expected = 40.0 - 10.0 * math.log10(20.0 / (20.0 + 20.0 * tau))
    assert np.allclose(with_term.noise_reduction, expected)
    assert np.all(with_term.noise_reduction > plain.noise_reduction)


def test_flanking_penalty_is_a_straight_debit() -> None:
    """The penalty comes off the noise reduction and lands on the received level."""
    plain = _chain()
    penalised = _chain(criterion=noise_control.DesignCriterion(flanking_penalty=3.0))
    assert np.allclose(penalised.noise_reduction, plain.noise_reduction - 3.0)
    assert np.allclose(penalised.received_level, plain.received_level + 3.0)
    assert penalised.flanking_penalty == pytest.approx(3.0)
    kinds = [row["kind"] for row in penalised.table()]
    assert "flanking" in kinds
    assert "flanking" not in [row["kind"] for row in plain.table()]


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        ("constant_power", 0.0),
        ("constant_volume", 6.0206),
        ("constant_pressure", -6.0206),
    ],
)
def test_source_power_models_scale_by_ten_lg_q(model: str, expected: float) -> None:
    """Norton Table 4.5: the radiated power goes as ``Q^0``, ``Q^1``, ``Q^-1``."""
    result = noise_control.room_to_room_transmission(
        _BANDS,
        40.0,
        20.0,
        _ABSORPTION,
        source=noise_control.SourceRoom(
            power_level=100.0, room_constant=50.0, directivity=4.0, model=model
        ),
    )
    reverberant = 100.0 + 10.0 * math.log10(4.0 / 50.0)
    assert np.allclose(result.source_level, reverberant + expected, atol=1e-3)
    assert result.source_power_level is not None
    assert np.allclose(result.source_power_level, 100.0)


def test_required_transmission_loss_closes_the_gap() -> None:
    """The required ``TL`` is the current one plus the criterion exceedance."""
    result = _chain(criterion=noise_control.DesignCriterion(target=45.0))
    required = result.required_transmission_loss
    excess = result.exceedance
    assert required is not None
    assert excess is not None
    assert np.allclose(required - result.transmission_loss, excess)
    # Re-running with that TL lands exactly on the criterion curve.
    tightened = noise_control.room_to_room_transmission(
        _BANDS,
        required,
        20.0,
        _ABSORPTION,
        source=noise_control.SourceRoom(level=result.source_level),
        criterion=noise_control.DesignCriterion(target=45.0),
    )
    assert np.allclose(tightened.received_level, result.criterion_curve)
    assert tightened.meets_target is True


def test_no_target_leaves_the_verdicts_undefined() -> None:
    """Without a target there is no curve, no exceedance and no verdict."""
    result = _chain()
    assert result.criterion_curve is None
    assert result.exceedance is None
    assert result.meets_target is None
    assert result.required_transmission_loss is None
    assert "criterion" not in [row["kind"] for row in result.table()]


def test_rc_criterion_family() -> None:
    """``family="RC"`` rates against the RC Mark II curves of Annex D."""
    result = _chain(criterion=noise_control.DesignCriterion(family="RC", target=35.0))
    assert result.criterion == "RC"
    assert result.criterion_curve is not None
    # The six bands of this chain are short of the 31.5 Hz to 4 kHz span
    # clause D.4 asks for, which the rating reports as a warning.
    with pytest.warns(UserWarning, match=r"clause D\.4 rates a spectrum that includes"):
        assert result.rating.__class__.__name__ == "RCResult"


def test_nc_rating_of_the_received_spectrum() -> None:
    """``rating`` is the ANSI S12.2 rating of the received spectrum."""
    result = noise_control.room_to_room_transmission(
        _BANDS,
        [50.0, 55.0, 60.0, 62.0, 62.0, 62.0],
        20.0,
        _ABSORPTION,
        source=noise_control.SourceRoom(level=_FLAT_SOURCE),
        criterion=noise_control.DesignCriterion(target=30.0),
    )
    assert result.rating.__class__.__name__ == "NCResult"
    assert np.isfinite(result.rating.rating)


def test_source_description_is_exclusive() -> None:
    """Exactly one of ``source.level`` / ``source.power_level`` is required.

    The refusal belongs to :class:`SourceRoom` itself, so it arrives when the
    bundle is built rather than when it is used. The call with no source at
    all still raises, because the empty default is built here and rejects
    itself for the same reason.
    """
    with pytest.raises(
        ValueError, match=r"give exactly one of 'level'.*or 'power_level'"
    ):
        noise_control.room_to_room_transmission(_BANDS, 40.0, 20.0, _ABSORPTION)
    with pytest.raises(
        ValueError, match=r"give exactly one of 'level'.*or 'power_level'"
    ):
        noise_control.SourceRoom(level=90.0, power_level=100.0)
    with pytest.raises(
        ValueError, match=r"'room_constant' is required with 'power_level'"
    ):
        noise_control.SourceRoom(power_level=100.0)


def test_validation() -> None:
    """Malformed bands, spectra, areas, absorption and options are rejected."""
    source = noise_control.SourceRoom(level=90.0)
    with pytest.raises(
        ValueError, match=r"'frequencies' must be a non-empty 1-D array"
    ):
        noise_control.room_to_room_transmission([], 40.0, 20.0, 20.0, source=source)
    with pytest.raises(
        ValueError,
        match=r"'transmission_loss' must be a scalar or have one value per band",
    ):
        noise_control.room_to_room_transmission(
            _BANDS, [40.0, 41.0], 20.0, _ABSORPTION, source=source
        )
    with pytest.raises(ValueError, match=r"'transmission_loss' must be finite"):
        noise_control.room_to_room_transmission(
            _BANDS, _NAN_SPECTRUM, 20.0, _ABSORPTION, source=source
        )
    with pytest.raises(ValueError, match=r"'partition_area' must be positive"):
        noise_control.room_to_room_transmission(
            _BANDS, 40.0, 0.0, _ABSORPTION, source=source
        )
    with pytest.raises(ValueError, match=r"'receiving_absorption' must be positive"):
        noise_control.room_to_room_transmission(
            _BANDS, 40.0, 20.0, _NO_ABSORPTION, source=source
        )
    negative_flanking = noise_control.DesignCriterion(flanking_penalty=-1.0)
    with pytest.raises(
        ValueError, match=r"'criterion\.flanking_penalty' must be non-negative"
    ):
        _chain(criterion=negative_flanking)
    unknown_family = noise_control.DesignCriterion(family="NR")
    with pytest.raises(ValueError, match=r"'criterion' must be one of"):
        _chain(criterion=unknown_family)
    unknown_model = noise_control.SourceRoom(level=_SOURCE, model="constant_energy")
    with pytest.raises(ValueError, match=r"'source\.model' must be one of"):
        _chain(source=unknown_model)
    nan_target = noise_control.DesignCriterion(target=_NAN)
    with pytest.raises(ValueError, match=r"'target' must be a finite criterion value"):
        _chain(criterion=nan_target)


# --------------------------------------------------------------------------
# Rows that do not run over the analysis bands
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "field_name",
    [
        "frequencies",
        "source_level",
        "transmission_loss",
        "receiving_absorption",
        "noise_reduction",
        "received_level",
        "source_power_level",
    ],
)
@pytest.mark.parametrize("trim", [True, False], ids=["short", "long"])
def test_a_spectrum_off_the_band_axis_is_refused(
    field_name: str, *, trim: bool
) -> None:
    """A chain cannot carry a row that runs over other bands than the header.

    :meth:`RoomToRoomResult.table` writes the chain out as one row per link
    under a single band header and neither pads nor trims: a six-band chain
    whose transmission loss ran five bands prints a five-number row beside
    six-number ones, and the reader lays a receiving-room level against a
    source-room level of other bands. The two directions are equally quiet, and
    the flanking and criterion rows are built to the length of ``frequencies``
    alone, so they go on printing at full width whichever row ran short.
    ``frequencies``, ``source_level`` and ``receiving_absorption`` do stop a
    sheet that declares a target, because the required row reads them, but on a
    bare ``operands could not be broadcast together`` that names neither the
    field nor the result.
    """
    result = _powered_chain()
    row = np.asarray(getattr(result, field_name))
    wrong = row[:-1] if trim else np.append(row, row[-1])
    # The guard names every field of the result, so the identifier alone would
    # match whichever row was short. The count is the test's own: it is what
    # this test made wrong, and it is the only thing that says so.
    with pytest.raises(ValueError, match=rf"'{field_name}' \({wrong.size}\)"):
        dataclasses.replace(result, **{field_name: wrong})


def test_a_single_absorption_number_is_refused() -> None:
    """One number for the receiving room is broadcast, not caught.

    :attr:`RoomToRoomResult.required_transmission_loss` divides the partition
    area by the receiving-room absorption band by band, so an absorption given
    as a single number where the bands needed several is stretched over the
    whole spectrum without a murmur: the property then specifies the partition
    against the absorption the room has in one band. With the graded room below
    replaced by its 125 Hz value the requirement comes out 43 dB at 4 kHz where
    the room really asks for 31, and only the 125 Hz band the number came from
    is right. The sheet shows the same number as a bare scalar under the band
    header.
    """
    graded = np.array([5.0, 10.0, 20.0, 40.0, 60.0, 80.0])
    result = noise_control.room_to_room_transmission(
        _BANDS,
        40.0,
        20.0,
        graded,
        source=noise_control.SourceRoom(level=_SOURCE),
        criterion=noise_control.DesignCriterion(target=45.0),
    )
    one_number = float(graded[0])
    with pytest.raises(ValueError, match=r"'receiving_absorption' must have one axis"):
        dataclasses.replace(result, receiving_absorption=one_number)


def test_a_spectrum_with_an_extra_axis_is_refused() -> None:
    """Counting the bands is not enough: an extra axis passes every count.

    Two columns of six bands still count six entries along the first axis, so
    a length check alone lets the pair into the sheet, where the row prints as
    six pairs under a band header of six single numbers.
    """
    result = _powered_chain()
    two_columns = np.column_stack([result.transmission_loss, result.transmission_loss])
    with pytest.raises(ValueError, match="'transmission_loss' must have one axis"):
        dataclasses.replace(result, transmission_loss=two_columns)


# --------------------------------------------------------------------------
# A receiver near the partition (Barron 2003, 7.5.2)
# --------------------------------------------------------------------------
#: Barron (2003), Industrial Noise Control and Acoustics, Example 7-6, folio 298
#: (PDF page 310): the refiner room, the operator's room and the wall between
#: them, as ``tests/reference_data/workroom_prediction.py`` carries them. The
#: example carries one number rather than a spectrum, so one band stands for it.
_BARRON_BAND = [1000.0]
_BARRON_SOURCE_SURFACE_M2 = barron.BARRON_EXAMPLE_7_6_SOURCE_SURFACE_M2
_BARRON_SOURCE_ALPHA = barron.BARRON_EXAMPLE_7_6_SOURCE_ABSORPTION
_BARRON_POWER_LEVEL_DB = barron.BARRON_EXAMPLE_7_6_POWER_LEVEL_DB
_BARRON_DIRECTIVITY = barron.BARRON_EXAMPLE_7_6_DIRECTIVITY
_BARRON_RECEIVING_SURFACE_M2 = barron.BARRON_EXAMPLE_7_6_RECEIVING_SURFACE_M2
_BARRON_RECEIVING_ALPHA = barron.BARRON_EXAMPLE_7_6_RECEIVING_ABSORPTION
_BARRON_TL_DB = barron.BARRON_EXAMPLE_7_6_TRANSMISSION_LOSS_DB
_BARRON_WALL_M2 = barron.BARRON_EXAMPLE_7_6_WALL_M2
_BARRON_OPERATOR_DISTANCE_M = barron.BARRON_EXAMPLE_7_6_OPERATOR_DISTANCE_M
#: The ``10 lg(rho_0 c W_ref / p_ref^2)`` Barron adds to every level, folio 295
#: (PDF page 307); the library leaves it out, as ``room.steady_state_spl`` does.
_BARRON_IMPEDANCE_TERM_DB = barron.BARRON_IMPEDANCE_TERM_DB


def _near_wall_threshold_m(partition_area: float) -> float:
    """``r* = (S_w / 2 pi)^(1/2)``, where Barron's two branches meet."""
    return math.sqrt(partition_area / (2.0 * math.pi))


def test_barron_example_7_6_operator_near_the_wall() -> None:
    """The printed chain of Example 7-6, input to answer, folios 297 and 298.

    The operator stands 1,5 m from a 16 m2 wall, inside the 1,596 m where the
    wall still looks like a plane source, so Equation (7-71) applies and the
    direct field of the wall adds 2,65 dB to what the reverberant field alone
    delivers: the far-field chain gives 59,1 dB where Barron prints 61,7 dB.
    Barron writes the reverberant term over the room constant ``R2``, so the
    room constant is what goes in as the receiving absorption.
    """
    r1 = float(room.room_constant(_BARRON_SOURCE_SURFACE_M2, _BARRON_SOURCE_ALPHA))
    r2 = float(
        room.room_constant(_BARRON_RECEIVING_SURFACE_M2, _BARRON_RECEIVING_ALPHA)
    )
    assert r1 == pytest.approx(
        barron.BARRON_EXAMPLE_7_6_SOURCE_ROOM_CONSTANT_M2, abs=5e-3
    )
    assert r2 == pytest.approx(
        barron.BARRON_EXAMPLE_7_6_RECEIVING_ROOM_CONSTANT_M2, abs=5e-3
    )
    r_star = _near_wall_threshold_m(_BARRON_WALL_M2)
    assert r_star == pytest.approx(
        barron.BARRON_EXAMPLE_7_6_NEAR_WALL_DISTANCE_M, abs=5e-4
    )
    assert _BARRON_OPERATOR_DISTANCE_M < r_star
    # The two printed terms of the last line: -16,8 and +3,4.
    assert -10.0 * math.log10(r1) == pytest.approx(
        barron.BARRON_EXAMPLE_7_6_ROOM_TERM_DB, abs=0.05
    )
    assert 10.0 * math.log10(4.0 * _BARRON_WALL_M2 / r2 + 1.0) == pytest.approx(
        barron.BARRON_EXAMPLE_7_6_WALL_TERM_DB, abs=0.05
    )
    source = noise_control.SourceRoom(
        power_level=_BARRON_POWER_LEVEL_DB,
        room_constant=r1,
        directivity=_BARRON_DIRECTIVITY,
    )
    result = noise_control.room_to_room_transmission(
        _BARRON_BAND,
        _BARRON_TL_DB,
        _BARRON_WALL_M2,
        r2,
        source=source,
        receiver_distance_m=_BARRON_OPERATOR_DISTANCE_M,
    )
    assert result.receiver_distance_m == pytest.approx(_BARRON_OPERATOR_DISTANCE_M)
    printed = result.received_level[0] + _BARRON_IMPEDANCE_TERM_DB
    assert printed == pytest.approx(
        barron.BARRON_EXAMPLE_7_6_OPERATOR_LEVEL_DB, abs=0.05
    )
    reverberant = noise_control.room_to_room_transmission(
        _BARRON_BAND, _BARRON_TL_DB, _BARRON_WALL_M2, r2, source=source
    )
    far_field = reverberant.received_level[0] + _BARRON_IMPEDANCE_TERM_DB
    assert far_field == pytest.approx(59.1, abs=0.05)


#: Receiver distances as fractions of ``r*``, on either side of it and close
#: enough to it that a threshold placed anywhere else puts one of them on the
#: wrong branch: the two branches differ by 0,02 dB at 0,99 ``r*`` and more
#: beyond, far above the tolerance of the closed forms below.
_INSIDE_FRACTIONS = (0.1, 0.5, 0.99)
_OUTSIDE_FRACTIONS = (1.01, 1.5, 4.0)


@pytest.mark.parametrize("fraction", _INSIDE_FRACTIONS)
def test_near_wall_branch_closed_form(fraction: float) -> None:
    """Equation (7-71) over Norton's variables: ``NR = TL - 10 lg(S_w/A + 1/4)``."""
    absorption = np.array([5.0, 10.0, 20.0, 40.0, 60.0, 80.0])
    result = noise_control.room_to_room_transmission(
        _BANDS,
        40.0,
        20.0,
        absorption,
        source=noise_control.SourceRoom(level=_SOURCE),
        receiver_distance_m=fraction * _near_wall_threshold_m(20.0),
    )
    expected = 40.0 - 10.0 * np.log10(20.0 / absorption + 0.25)
    assert np.allclose(result.noise_reduction, expected, rtol=0.0, atol=1e-12)
    assert np.allclose(result.received_level, _SOURCE - expected, rtol=0.0, atol=1e-12)


@pytest.mark.parametrize("fraction", _OUTSIDE_FRACTIONS)
def test_far_wall_branch_closed_form(fraction: float) -> None:
    """Equation (7-72): ``NR = TL - 10 lg(S_w/A + S_w/(8 pi r2^2))`` beyond ``r*``."""
    distance = fraction * _near_wall_threshold_m(20.0)
    result = _chain(receiver_distance_m=distance)
    expected = 40.0 - 10.0 * math.log10(
        20.0 / 20.0 + 20.0 / (8.0 * math.pi * distance**2)
    )
    assert np.allclose(result.noise_reduction, expected, rtol=0.0, atol=1e-12)


def test_the_two_branches_meet_at_the_threshold() -> None:
    """Barron's two branches give one level at ``r* = (S_w / 2 pi)^(1/2)``."""
    r_star = _near_wall_threshold_m(20.0)
    inside = _chain(receiver_distance_m=math.nextafter(r_star, 0.0))
    at = _chain(receiver_distance_m=r_star)
    outside = _chain(receiver_distance_m=math.nextafter(r_star, math.inf))
    assert np.allclose(inside.received_level, at.received_level, rtol=0.0, atol=1e-9)
    assert np.allclose(outside.received_level, at.received_level, rtol=0.0, atol=1e-9)


def test_far_from_the_wall_is_the_reverberant_field_alone() -> None:
    """Norton's Equation (4.101) is the limit of Equation (7-72) as ``r2`` grows."""
    reverberant = _chain()
    distant = _chain(receiver_distance_m=1e4)
    assert np.allclose(
        distant.received_level, reverberant.received_level, rtol=0.0, atol=1e-6
    )
    assert np.all(distant.received_level > reverberant.received_level)


def test_no_receiver_distance_keeps_the_reverberant_chain() -> None:
    """``receiver_distance_m=None`` is the default and changes nothing."""
    default = _chain()
    explicit = _chain(receiver_distance_m=None)
    assert default.receiver_distance_m is None
    assert explicit.receiver_distance_m is None
    assert np.array_equal(default.noise_reduction, explicit.noise_reduction)
    assert np.allclose(default.noise_reduction, 40.0, rtol=0.0, atol=1e-12)


def test_partition_transmission_term_with_a_receiver_distance() -> None:
    """``tau S_w`` joins the absorption and the direct term stays outside it."""
    tau = 10.0 ** (-40.0 / 10.0)
    result = _chain(include_partition_transmission=True, receiver_distance_m=1.0)
    expected = 40.0 - 10.0 * math.log10(20.0 / (20.0 + 20.0 * tau) + 0.25)
    assert np.allclose(result.noise_reduction, expected, rtol=0.0, atol=1e-12)


@pytest.mark.parametrize("distance", [0.0, -1.5, _NAN])
def test_a_receiver_distance_that_is_not_a_distance_is_refused(
    distance: float,
) -> None:
    """Zero, a negative number and NaN are refused before any logarithm runs."""
    with pytest.raises(ValueError, match=r"'receiver_distance_m' must be positive"):
        _chain(receiver_distance_m=distance)


@pytest.mark.parametrize("distance", [0.5, 3.0])
def test_required_transmission_loss_with_a_receiver_distance(distance: float) -> None:
    """The inverse carries the direct term, so it still closes the chain."""
    result = _chain(
        criterion=noise_control.DesignCriterion(target=45.0, flanking_penalty=2.0),
        receiver_distance_m=distance,
    )
    required = result.required_transmission_loss
    curve = result.criterion_curve
    reverberant = _chain(
        criterion=noise_control.DesignCriterion(target=45.0, flanking_penalty=2.0)
    ).required_transmission_loss
    assert required is not None
    assert curve is not None
    assert reverberant is not None
    assert np.all(required > reverberant)
    tightened = noise_control.room_to_room_transmission(
        _BANDS,
        required,
        20.0,
        _ABSORPTION,
        source=noise_control.SourceRoom(level=result.source_level),
        criterion=noise_control.DesignCriterion(target=45.0, flanking_penalty=2.0),
        receiver_distance_m=distance,
    )
    assert np.allclose(tightened.received_level, curve, rtol=0.0, atol=1e-9)


def test_plot_smoke() -> None:
    """``.plot()`` draws the two spectra, the criterion curve and the NR axis."""
    import matplotlib as mpl

    mpl.use("Agg")
    result = _chain(
        criterion=noise_control.DesignCriterion(target=45.0, flanking_penalty=2.0)
    )
    ax = result.plot()
    assert ax.get_ylabel() == "Level [dB]"
    assert ax.get_title().startswith("Room-to-room transmission")
    ax_es = result.plot(language="es")
    assert ax_es.get_ylabel() == "Nivel [dB]"
    with pytest.raises(ValueError, match="Unknown language"):
        result.plot(language="fr")
