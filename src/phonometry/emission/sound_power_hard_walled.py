#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Sound power and sound energy levels of a small movable source in a
hard-walled test room, by comparison with a reference sound source:
ISO 3743-1:2010 (engineering grade 2).

The room is an ordinary one: nearly empty, with smooth hard walls, no
surface anywhere absorbing more than 0,20 of the incident power (4.3), at
least 40 m³ and forty times the reference box (4.2). Such a room is not
diffuse enough to be read on its own the way ISO 3741 reads a qualified
reverberation room, so the room is not modelled at all: a calibrated
reference sound source (RSS) stands where the source under test (ST) stood
and the same microphones listen to both. The room then drops out of the
difference, and the octave-band sound power level of the source is the
calibrated power of the reference carried across by the difference of the
two mean levels, each corrected for background noise (8.1.4):

.. math::

   L_W = L_{W(\mathrm{RSS})} - \overline{L'_{p(\mathrm{RSS})}}
   + \overline{L'_{p(\mathrm{ST})}} + K_{1(\mathrm{RSS})} - K_1
   \tag{Eq. 14}

The mean levels are energy averages over the :math:`N_\mathrm{M}` microphone
positions or traverses (Eq. 10, 11, 12), and when the preliminary survey of
7.4 asked for more than one source location the levels at each position are
first energy-averaged over the :math:`N_\mathrm{S}` locations (Eq. 9).

Unlike ISO 3741 and ISO 3747, the background correction is taken once per
band from the two *means*, not position by position (8.1.3):

.. math::

   K_1 = -10 \log_{10}\!\left(1 - 10^{-0.1\,\Delta L_p}\right),
   \qquad \Delta L_p = \overline{L'_{p(\mathrm{ST})}} - \overline{L_{p(\mathrm{B})}}
   \tag{Eq. 13}

with three rules around it: above 15 dB there is nothing to correct, from
6 dB to 15 dB Eq. (13) applies, and below 6 dB the correction is fixed at
1,3 dB, "the value for :math:`\Delta L_p` = 6 dB", and the band becomes an
upper bound that the report has to flag. The same rule gives
:math:`K_{1(\mathrm{RSS})}` from the reference source's mean, but a band
where it is the reference source's margin that falls short is no upper bound:
:math:`K_{1(\mathrm{RSS})}` enters Eq. (14) with a plus sign, so the capped
correction pulls :math:`L_W` down, not up. 8.1.3 gives the upper-bound
reading to the margin of the source under test alone, and such a band only
fails the background requirement of 4.5, which is all the library says of it.

A source that emits bursts has a sound energy level instead (8.2): the
single event levels of each position are reduced to the level of one event
(Eq. 15 or Eq. 16), averaged over the source locations (Eq. 17) and the
positions (Eq. 18), corrected by the same rule (Eq. 19), and

.. math::

   L_J = L_{W(\mathrm{RSS})} - \overline{L'_{p(\mathrm{RSS})}}
   + \overline{L'_{E(\mathrm{ST})}} + K_{1(\mathrm{RSS})} - K_1
   \tag{Eq. 20}

Eq. (19) subtracts a time-averaged background level from a time-integrated
event level, exactly as ISO 3744:2010 Eq. (21) does, and asks only that both
be measured over one integration time :math:`T`. The library reads the
background as its exposure over that :math:`T`, :math:`L_{p(\mathrm{B})} +
10 \log_{10}(T/T_0)`, which is the reading under which the insistence on one
:math:`T` does any work (see ``docs/ERRATA.md``), so ``integration_time_s`` is
required with a background.

Annex A carries either level to the reference meteorological conditions of
101,325 kPa and 23,0 °C with the radiation-impedance correction
:math:`C_2 = -10 \log_{10}(p_\mathrm{s}/p_{\mathrm{s},0}) + 15 \log_{10}
[(273{,}15 + \theta)/\theta_1]`, :math:`\theta_1` = 296 K, the expression
ISO 3741:2010 and ISO 3747:2010 print digit for digit; the static pressure
follows from the altitude by Eq. (A.2), which is ISO 3747:2010 Eq. (C.2)
(:func:`~phonometry.emission.static_pressure_from_altitude`). The correction
is required above 500 m (8.1.4). Annex B forms the A-weighted totals from the
octave bands with the Table B.1 corrections, which are ISO 3744:2010 Table E.2
digit for digit, 63 Hz row included under its footnote.

Clause 9 estimates the uncertainty as :math:`\sigma_\mathrm{tot} =
\sqrt{\sigma_{R0}^2 + \sigma_\mathrm{omc}^2}` (Eq. 22) and :math:`U =
k\,\sigma_\mathrm{tot}` (Eq. 23), with :math:`k` = 2 (9.5), and Table 3 gives
the typical upper bound of :math:`\sigma_{R0}` per octave band: 3,0 dB at
125 Hz, 2,0 dB at 250 Hz, 1,5 dB from 500 Hz to 4 kHz, 2,5 dB at 8 kHz and
1,5 dB for the A-weighted level of a flat spectrum. The middle row of the
printed table reads "400 to 5 000" under an octave heading, which is a
one-third-octave range; the library reads it as the four octaves it spans
(see ``docs/ERRATA.md``).

The room itself is qualified in three steps, which
:func:`check_hard_walled_room` evaluates together: its volume against the
reference box (4.2), the absorption of its surfaces (4.3), and the acoustic
adequacy of 4.4, eight mean octave levels of a highly directional source
turned through four horizontal and four vertical orientations, whose largest
spread in each band from 125 Hz to 8 kHz may not exceed the Table 3 value.
The preliminary survey of 7.4, six microphone positions whose standard
deviation decides how many source locations the determination needs
(Table 2), is :func:`hard_walled_source_locations`.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from itertools import pairwise
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Mapping

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike

    from .._report.metadata import ReportMetadata
    from .reference_sound_source import ReferenceSourceCalibration

from .._internal.boundary import settled
from .._internal.levels_math import energy_mean, energy_sum
from .._internal.validation import (
    check_engine,
    require_choice,
    require_non_negative,
    require_positive,
    require_ranks,
    require_same_length,
)
from ._shared import (
    _CK_OCTAVE,
    SoundPowerWarning,
    _a_weighting_corrections,
    _background_exposure,
    _c2_correction,
    _reference_power_levels,
    _single_event_mean,
    _validate_meteorology,
)

#: The standard the determinations here implement, as the warnings cite it.
_STANDARD = "ISO 3743-1:2010"
#: Background margin at or above which the determination meets 4.5, and below
#: which K1 is fixed at 1,3 dB; a band where the source under test falls below
#: it is an upper bound (8.1.3).
_K1_VALID_DB = 6.0
#: Background margin above which K1 is zero (8.1.3).
_K1_NEGLIGIBLE_DB = 15.0
#: The K1 8.1.3 applies below the 6 dB margin, "the value for dLp = 6 dB"
#: rounded to one decimal as printed.
_K1_BELOW_VALID_DB = 1.3
#: Fewest fixed microphone positions (7.3).
_MIN_MICROPHONES = 3
#: Fewest microphone positions of the preliminary survey (7.4).
_MIN_PRELIMINARY_MICROPHONES = 6
#: Coverage factor of the two-sided 95 % interval the standard prescribes (9.5).
_COVERAGE_TWO_SIDED = 2.0
#: Table 3, typical upper bound of the standard deviation of reproducibility
#: per octave band, in decibels. The printed middle row reads "400 to 5 000"
#: under an octave heading; the octaves it spans are 500 Hz to 4 kHz.
_SIGMA_R0_DB: Mapping[int, float] = MappingProxyType(
    {125: 3.0, 250: 2.0, 500: 1.5, 1000: 1.5, 2000: 1.5, 4000: 1.5, 8000: 2.5}
)
#: Table 3, the A-weighted row (a source with a relatively flat spectrum).
_SIGMA_R0_A_DB = 1.5
#: 4.2: the room is at least 40 m³ and at least 40 times the reference box.
_MIN_ROOM_VOLUME_M3 = 40.0
_ROOM_TO_BOX_VOLUME_RATIO = 40.0
#: 4.2: the largest reference-box dimension is at most 1,0 m in a room of up to
#: 100 m³ and 2,0 m in a larger one.
_SMALL_ROOM_LIMIT_M3 = 100.0
_BOX_LIMIT_SMALL_ROOM_M = 1.0
_BOX_LIMIT_LARGE_ROOM_M = 2.0
#: 4.3: no portion of a boundary surface absorbs more than this.
_MAX_ABSORPTION_COEFFICIENT = 0.20
#: 4.4: the directional source is turned through four horizontal and four
#: vertical orientations.
_ORIENTATIONS = 8
#: 7.3: the reverberant-field distance d_min = 0,3 V^(1/3) from the source.
_REVERBERANT_DISTANCE_FACTOR = 0.3
#: Table 2: the standard deviation limits of the three rows, in decibels.
_TABLE2_ONE_LOCATION_DB = 2.5
_TABLE2_TWO_LOCATIONS_DB = 4.0
#: Table 2, bottom row: two locations in the same room plus two in another.
_TABLE2_OTHER_ROOM_LOCATIONS = 2


def _octave_frequencies(
    frequencies: ArrayLike, n_bands: int, table: str = f"{_STANDARD}, Table B.1"
) -> np.ndarray:
    """The nominal octave mid-band frequencies, one per band, all in Table B.1,
    distinct and ascending.

    ISO 3743-2:2018 Table F.1 is the same table, so Part 2 reads its bands
    here too and names its own table in the messages.

    :param frequencies: One mid-band frequency per band, in hertz.
    :param n_bands: The number of bands the levels carry.
    :param table: The table the messages cite.
    :return: The frequencies as a float array of their own, which a result
        keeps without sharing the caller's.
    :raises ValueError: if the count differs, a value is not a Table B.1
        octave centre, or the centres repeat or descend.
    """
    freqs = np.array(frequencies, dtype=np.float64)
    if freqs.shape != (n_bands,):
        msg = f"'frequencies' must carry one value per band ({n_bands})."
        raise ValueError(msg)
    if not np.all(np.isfinite(freqs)) or any(
        round(float(f)) not in _CK_OCTAVE for f in freqs
    ):
        msg = (
            "'frequencies' must be nominal octave mid-band frequencies from "
            f"63 Hz to 8 kHz ({table})."
        )
        raise ValueError(msg)
    nominal = [round(float(f)) for f in freqs]
    if any(b <= a for a, b in pairwise(nominal)):
        msg = (
            "'frequencies' must be distinct octave mid-band frequencies in "
            f"ascending order, one per k of {table}."
        )
        raise ValueError(msg)
    return freqs


def _finite(value: ArrayLike, name: str, ndims: tuple[int, ...]) -> np.ndarray:
    """A finite, non-empty float array of one of the admissible ranks.

    :raises ValueError: naming the argument, for any other rank or a
        non-finite entry.
    """
    arr = np.asarray(value, dtype=np.float64)
    if arr.ndim not in ndims or arr.size == 0:
        shapes = " or ".join(f"{d}D" for d in ndims)
        msg = f"'{name}' must be a non-empty {shapes} array of levels in decibels."
        raise ValueError(msg)
    if not np.all(np.isfinite(arr)):
        msg = f"'{name}' must be finite."
        raise ValueError(msg)
    return arr


def _k1_eq13(delta: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    r"""``K1`` from the background margin, with the three rules of 8.1.3.

    Above 15 dB the correction is zero, from 6 dB to 15 dB it is Eq. (13),
    and below 6 dB it is the 1,3 dB the clause fixes, "the value for
    :math:`\Delta L_p` = 6 dB" to one decimal; the second array says where
    the margin met the 6 dB of 4.5.

    :param delta: Margin of the mean level over the mean background, in dB.
    :return: ``(K1, margin at least 6 dB)``, elementwise.
    """
    margin = settled(delta)
    within = np.maximum(margin, _K1_VALID_DB)
    formula = -10.0 * np.log10(1.0 - 10.0 ** (-0.1 * within))
    k1 = np.where(
        margin > _K1_NEGLIGIBLE_DB,
        0.0,
        np.where(margin >= _K1_VALID_DB, formula, _K1_BELOW_VALID_DB),
    )
    return np.asarray(k1, dtype=np.float64), np.asarray(
        margin >= _K1_VALID_DB, dtype=bool
    )


def _table3_sigma(frequencies: np.ndarray) -> np.ndarray:
    """Table 3 per band; ``NaN`` at 63 Hz, which the table does not reach."""
    return np.array(
        [_SIGMA_R0_DB.get(round(float(f)), math.nan) for f in frequencies],
        dtype=np.float64,
    )


def _check_uncertainty_inputs(
    sigma_omc_db: float | None, coverage_factor: float
) -> float:
    """``sigma_omc`` as given (``NaN`` for none), after the two refusals.

    :raises ValueError: for a negative or non-finite ``sigma_omc_db`` or a
        coverage factor that is not positive.
    """
    require_positive(coverage_factor, "coverage_factor")
    if sigma_omc_db is None:
        return math.nan
    if not math.isfinite(sigma_omc_db) or sigma_omc_db < 0.0:
        msg = "'sigma_omc_db' must be finite and non-negative."
        raise ValueError(msg)
    return float(sigma_omc_db)


@dataclass(frozen=True)
class HardWalledSoundPowerResult:
    r"""Result of an ISO 3743-1:2010 determination in a hard-walled test room.

    ``quantity`` says which of the two determinations this is: ``'power'``
    carries the octave-band sound power level ``LW`` (Eq. 14) in
    ``sound_power_level`` with ``sound_energy_level`` all ``NaN``, and
    ``'energy'`` the sound energy level ``LJ`` (Eq. 20) in
    ``sound_energy_level`` with ``sound_power_level`` all ``NaN``. Both are at
    the meteorological conditions of the test; the ``..._ref`` properties add
    the Annex A correction ``c2``, which 8.1.4 requires above 500 m.

    ``mean_source_level`` is the uncorrected mean level of the source under
    test, :math:`\overline{L'_{p(\mathrm{ST})}}` (Eq. 10) or
    :math:`\overline{L'_{E(\mathrm{ST})}}` (Eq. 18), and
    ``mean_reference_level`` that of the reference sound source,
    :math:`\overline{L'_{p(\mathrm{RSS})}}` (Eq. 11); ``mean_background_level``
    is :math:`\overline{L_{p(\mathrm{B})}}` (Eq. 12), ``NaN`` where no
    background was measured, and ``reference_power_level`` the calibrated
    :math:`L_{W(\mathrm{RSS})}`. ``background_correction`` and
    ``background_correction_ref`` are :math:`K_1` and
    :math:`K_{1(\mathrm{RSS})}` per band, and ``background_requirement_met``
    is ``True`` only where a background was measured and both margins reached
    the 6 dB of 4.5. ``upper_bound`` marks the bands that 8.1.3 calls upper
    bounds: the margin of the source under test was measured and fell below
    6 dB while the reference source's margin met it, so the capped
    :math:`K_1` leaves the level too high. A band where the reference source's
    margin falls short is not one: the capped :math:`K_{1(\mathrm{RSS})}`
    pulls the level down, so it is flagged by ``background_requirement_met``
    alone, and so is every band when no background was measured.

    ``sigma_r0`` is the Table 3 value per band (``NaN`` at 63 Hz, which the
    table does not reach) and ``sigma_r0_a`` its A-weighted row; with
    ``sigma_omc`` the properties give ``sigma_tot`` (Eq. 22) and the expanded
    uncertainty (Eq. 23) for ``coverage_factor``, all ``NaN`` without it.
    ``microphone_positions`` is :math:`N_\mathrm{M}` (1 for a traverse),
    ``source_positions`` is :math:`N_\mathrm{S}`, and
    ``sound_power_level_a`` / ``sound_energy_level_a`` are the Annex B totals
    of the level that was determined (``NaN`` for the other).
    """

    frequencies: np.ndarray
    sound_power_level: np.ndarray
    sound_energy_level: np.ndarray
    mean_source_level: np.ndarray
    mean_reference_level: np.ndarray
    mean_background_level: np.ndarray
    reference_power_level: np.ndarray
    background_correction: np.ndarray
    background_correction_ref: np.ndarray
    background_requirement_met: np.ndarray
    upper_bound: np.ndarray
    c2: float
    sigma_r0: np.ndarray
    sigma_r0_a: float
    sigma_omc: float
    coverage_factor: float
    sound_power_level_a: float
    sound_energy_level_a: float
    quantity: str
    microphone_positions: int
    source_positions: int

    def __post_init__(self) -> None:
        """Reject a result whose per-band quantities disagree, or whose tags
        are not the ones the standard has.

        The plot draws one bar per ``frequencies`` entry from the level of the
        same index and hatches it by ``background_requirement_met``; an array
        one entry short raises a bare ``IndexError`` there and one entry long
        is silently dropped, so the lengths are pinned here.

        :raises ValueError: if ``quantity`` is neither ``'power'`` nor
            ``'energy'``, ``coverage_factor`` is not positive, a count is below
            one, or any per-band array disagrees with the rest.
        """
        require_choice(self.quantity, "quantity", ("power", "energy"))
        require_positive(self.coverage_factor, "coverage_factor")
        if self.microphone_positions < 1 or self.source_positions < 1:
            msg = (
                "HardWalledSoundPowerResult: 'microphone_positions' and "
                "'source_positions' must be at least 1."
            )
            raise ValueError(msg)
        bands = (
            "frequencies",
            "sound_power_level",
            "sound_energy_level",
            "mean_source_level",
            "mean_reference_level",
            "mean_background_level",
            "reference_power_level",
            "background_correction",
            "background_correction_ref",
            "background_requirement_met",
            "upper_bound",
            "sigma_r0",
        )
        require_ranks(self, **dict.fromkeys(bands, 1))
        require_same_length(self, *bands)

    @property
    def sigma_tot(self) -> np.ndarray:
        r""":math:`\sigma_\mathrm{tot} = \sqrt{\sigma_{R0}^2 +
        \sigma_\mathrm{omc}^2}` per band (Eq. 22), in decibels; ``NaN`` without
        ``sigma_omc`` and at 63 Hz.
        """
        return np.asarray(np.hypot(self.sigma_r0, self.sigma_omc), dtype=np.float64)

    @property
    def sigma_tot_a(self) -> float:
        """Eq. (22) with the A-weighted row of Table 3, in decibels."""
        return float(math.hypot(self.sigma_r0_a, self.sigma_omc))

    @property
    def expanded_uncertainty(self) -> np.ndarray:
        """``U = k sigma_tot`` per band (Eq. 23), in decibels."""
        return np.asarray(self.coverage_factor * self.sigma_tot, dtype=np.float64)

    @property
    def expanded_uncertainty_a(self) -> float:
        """``U = k sigma_tot`` of the A-weighted level (Eq. 23), in decibels.

        With ``sigma_omc`` = 2,0 dB and ``k`` = 2 this is the 5 dB of the 9.5
        EXAMPLE.
        """
        return float(self.coverage_factor * self.sigma_tot_a)

    @property
    def sound_power_level_ref(self) -> np.ndarray:
        """``LW + C2`` under the reference meteorological conditions (Eq. A.1);
        ``NaN`` for an energy determination.
        """
        return np.asarray(self.sound_power_level + self.c2, dtype=np.float64)

    @property
    def sound_energy_level_ref(self) -> np.ndarray:
        """``LJ + C2`` under the reference meteorological conditions (Eq. A.3);
        ``NaN`` for a power determination.
        """
        return np.asarray(self.sound_energy_level + self.c2, dtype=np.float64)

    @property
    def sound_power_level_a_ref(self) -> float:
        """The A-weighted total of :attr:`sound_power_level_ref`.

        ``C2`` is the same in every band, so it passes through Eq. (B.1)
        unchanged: the total moves by ``C2`` too.
        """
        return float(self.sound_power_level_a + self.c2)

    @property
    def sound_energy_level_a_ref(self) -> float:
        """The A-weighted total of :attr:`sound_energy_level_ref` (Eq. B.2)."""
        return float(self.sound_energy_level_a + self.c2)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the determined spectrum with the A-weighted total annotated.

        One bar per octave band of ``LW`` (or ``LJ``), a band that 8.1.3 makes
        an upper bound hatched and named as one, a band that fails the
        background requirement of 4.5 otherwise cross-hatched and named as
        that, and the expanded uncertainty as an error bar where ``sigma_omc``
        was given. Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the band bars.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.emission import plot_hard_walled_sound_power

        return plot_hard_walled_sound_power(
            self, ax=ax, language=check_language(language), **kwargs
        )

    def report(
        self,
        path: str,
        *,
        metadata: ReportMetadata | None = None,
        engine: str = "reportlab",
        verbose: bool = False,
        language: str = "en",
    ) -> str:
        """Render the ISO 3743-1 determination as a one-page test sheet.

        The sheet states the method and its accuracy grade (the comparison
        with a reference sound source in a hard-walled test room,
        ISO 3743-1:2010, grade 2), an optional metadata header, the per-band
        table of the mean level of the source, the mean level and the
        calibrated sound power level of the reference sound source and the
        determined ``LW`` (or ``LJ``), the spectrum, the boxed A-weighted level
        with the expanded uncertainty and its coverage factor, an optional
        verdict against a declared limit, and a basis strip with the Eq. 14
        (or Eq. 20) chain and its corrections. A band that is an upper bound
        is marked ``*`` and named one beneath the table, with the background
        requirement not fulfilled, which 8.1.3 asks a report to state in its
        tables; any other band whose background requirement was not met is
        marked ``†`` and named as not fulfilling it.

        :param path: Destination path of the PDF file.
        :param metadata: Optional :class:`~phonometry.ReportMetadata` for the
            header (``client``, ``specimen`` the noise source, ``test_room``,
            ``instrumentation``, the climate and ``test_date``), the footer
            identity and, via ``requirement``, a declared A-weighted limit the
            result is checked against (lower is better).
        :param engine: Rendering back end; only ``"reportlab"`` is supported.
        :param verbose: When ``True`` the table adds the mean background level
            and the background corrections ``K1`` and ``K1(RSS)``.
        :param language: Sheet language: ``"en"`` (default) or ``"es"``.
        :return: The written ``path`` as a :class:`str`.
        :raises ValueError: If ``engine`` is not ``"reportlab"`` or ``language``
            is unknown.
        :raises ImportError: If reportlab (or, for the figure, matplotlib) is
            not installed (``pip install phonometry[report]``).
        """
        from .._i18n import check_language

        check_language(language)
        check_engine(engine)
        from .._report.iso3743 import render_hard_walled_power_report

        return render_hard_walled_power_report(
            self, path, metadata=metadata, verbose=verbose, language=language
        )


def _source_grid(arr: np.ndarray) -> tuple[np.ndarray, bool]:
    """The levels as ``(NS, NM, NB)``, and whether they came from a traverse.

    A 1D spectrum is the time- and space-averaged level of one microphone
    traverse (NOTE to 8.1.2); a 2D array is one row per fixed microphone
    position; a 3D array adds the source locations of 7.4 on the first axis.
    """
    if arr.ndim == 1:
        return arr[None, None, :], True
    if arr.ndim == 2:  # noqa: PLR2004
        return arr[None, :, :], False
    return arr, False


def _position_mean(
    value: ArrayLike, name: str, n_positions: int, n_bands: int
) -> np.ndarray:
    """The energy mean over the microphone positions of a ``(NB,)`` spectrum
    already averaged, or of one ``(NM, NB)`` row per position (Eq. 11, 12).

    :raises ValueError: if the shape names other positions or bands.
    """
    arr = _finite(value, name, (1, 2))
    if arr.ndim == 1:
        if arr.shape != (n_bands,):
            msg = f"'{name}' must carry one value per band ({n_bands})."
            raise ValueError(msg)
        return arr
    if arr.shape != (n_positions, n_bands):
        msg = (
            f"'{name}' must be measured at the same {n_positions} microphone "
            f"position(s) and {n_bands} band(s) as the source under test (7.3), "
            "or be one averaged (bands,) spectrum."
        )
        raise ValueError(msg)
    return np.asarray(energy_mean(arr, axis=0), dtype=np.float64)


def _position_advisory(n_positions: int, *, traverse: bool, stacklevel: int) -> None:
    """Warn when fewer fixed microphone positions were used than 7.3 asks."""
    if not traverse and n_positions < _MIN_MICROPHONES:
        warnings.warn(
            f"{n_positions} microphone position(s) were supplied; the "
            f"determination uses at least {_MIN_MICROPHONES} ({_STANDARD}, 7.3).",
            SoundPowerWarning,
            stacklevel=stacklevel,
        )


def _background_advisory(
    met: np.ndarray, met_ref: np.ndarray, *, measured: bool, stacklevel: int
) -> None:
    """Warn when a band cannot be reported as meeting the criterion of 4.5.

    The two margins are told apart because 8.1.3 reads them apart: a short
    margin of the source under test makes the band an upper bound, a short
    margin of the reference sound source only fails 4.5, since its capped
    correction enters Eq. (14) with a plus sign and lowers the level.
    """
    if not measured:
        warnings.warn(
            "No background levels were supplied; the procedure measures them at "
            f"each microphone position ({_STANDARD}, 7.5), so no band can be "
            "reported as meeting 4.5.",
            SoundPowerWarning,
            stacklevel=stacklevel,
        )
        return
    if not np.all(met):
        warnings.warn(
            "The margin of the source under test over the background is below "
            "6 dB in one or more bands; K1 is 1,3 dB there and those levels are "
            f"upper bounds ({_STANDARD}, 4.5 and 8.1.3).",
            SoundPowerWarning,
            stacklevel=stacklevel,
        )
    if not np.all(met_ref):
        warnings.warn(
            "The margin of the reference sound source over the background is "
            "below 6 dB in one or more bands; K1(RSS) is 1,3 dB there, which "
            "lowers those levels, so they do not meet 4.5 and are not upper "
            f"bounds ({_STANDARD}, 4.5 and 8.1.4).",
            SoundPowerWarning,
            stacklevel=stacklevel,
        )


@dataclass(frozen=True)
class _Reference:
    """The reference sound source and the conditions of the test.

    Both determinations forward these unchanged to :func:`_determine`: they
    describe what the source under test is compared against and where, not
    the quantity under determination, which is how clauses 8.1.4 and 8.2.4
    read too.
    """

    levels_ref: ArrayLike
    lw_ref: ArrayLike | ReferenceSourceCalibration
    frequencies: ArrayLike
    background_levels: ArrayLike | None
    background_levels_ref: ArrayLike | None
    temperature_c: float
    static_pressure_kpa: float
    sigma_omc_db: float | None
    coverage_factor: float


def _determine(
    *,
    quantity: str,
    mean_source: np.ndarray,
    background_for_source: np.ndarray | None,
    n_positions: int,
    n_sources: int,
    traverse: bool,
    reference: _Reference,
) -> HardWalledSoundPowerResult:
    """The part both determinations share: Eq. (11) to (14) or (20), Annex A,
    Annex B and clause 9.

    :param background_for_source: The mean background the source under test is
        compared against, already carried to the event interval for an energy
        determination; ``None`` when none was measured.
    """
    n_bands = mean_source.shape[0]
    freqs = _octave_frequencies(reference.frequencies, n_bands)
    omc = _check_uncertainty_inputs(reference.sigma_omc_db, reference.coverage_factor)
    _validate_meteorology(reference.temperature_c, reference.static_pressure_kpa)
    ref_arr = _finite(reference.levels_ref, "levels_ref", (1, 2))
    if traverse and ref_arr.ndim != 1:
        msg = (
            "'levels_ref' must be the traverse level of the reference source, a "
            "(bands,) spectrum, when the source under test was measured on one."
        )
        raise ValueError(msg)
    mean_ref = _position_mean(ref_arr, "levels_ref", n_positions, n_bands)  # Eq. (11)
    # Eq. (14) and (20) give the level under the conditions of the test
    # (Annex A), so a calibration is read there, less its own C2.
    power = _finite(
        _reference_power_levels(
            reference.lw_ref,
            freqs,
            bandwidth="octave",
            temperature_c=reference.temperature_c,
            static_pressure_kpa=reference.static_pressure_kpa,
        ),
        "lw_ref",
        (1,),
    )
    if power.shape != (n_bands,):
        msg = f"'lw_ref' must carry one value per band ({n_bands})."
        raise ValueError(msg)

    nan_band = np.full(n_bands, np.nan, dtype=np.float64)
    source_background = reference.background_levels
    measured = source_background is not None
    mean_bg = nan_band.copy()
    k1 = np.zeros(n_bands, dtype=np.float64)
    met = np.zeros(n_bands, dtype=bool)
    if source_background is not None:
        mean_bg = _position_mean(
            source_background, "background_levels", n_positions, n_bands
        )  # Eq. (12)
        compared = mean_bg if background_for_source is None else background_for_source
        k1, met = _k1_eq13(mean_source - compared)  # Eq. (13) / (19)
    # One background reading serves both sources unless the reference
    # measurement brought its own (7.5).
    ref_background = (
        source_background
        if reference.background_levels_ref is None
        else reference.background_levels_ref
    )
    k1_ref = np.zeros(n_bands, dtype=np.float64)
    met_ref = np.zeros(n_bands, dtype=bool)
    if ref_background is not None:
        mean_bg_ref = _position_mean(
            ref_background, "background_levels_ref", n_positions, n_bands
        )
        k1_ref, met_ref = _k1_eq13(mean_ref - mean_bg_ref)
    requirement = met & met_ref
    # 8.1.3 reads the upper bound off the margin of the source under test; a
    # band where the reference source's margin is short as well is not one.
    upper = measured & ~met & met_ref
    _background_advisory(met, met_ref, measured=measured, stacklevel=4)

    level = np.asarray(power - mean_ref + mean_source + k1_ref - k1, dtype=np.float64)
    total = energy_sum(level + _a_weighting_corrections(freqs))  # Eq. (B.1) / (B.2)
    is_power = quantity == "power"
    return HardWalledSoundPowerResult(
        frequencies=freqs,
        sound_power_level=level if is_power else nan_band.copy(),
        sound_energy_level=nan_band.copy() if is_power else level,
        mean_source_level=np.asarray(mean_source, dtype=np.float64),
        mean_reference_level=np.asarray(mean_ref, dtype=np.float64),
        mean_background_level=np.asarray(mean_bg, dtype=np.float64),
        reference_power_level=np.asarray(power, dtype=np.float64).copy(),
        background_correction=k1,
        background_correction_ref=k1_ref,
        background_requirement_met=np.asarray(requirement, dtype=bool),
        upper_bound=np.asarray(upper, dtype=bool),
        c2=_c2_correction(reference.temperature_c, reference.static_pressure_kpa),
        sigma_r0=_table3_sigma(freqs),
        sigma_r0_a=_SIGMA_R0_A_DB,
        sigma_omc=omc,
        coverage_factor=float(reference.coverage_factor),
        sound_power_level_a=total if is_power else math.nan,
        sound_energy_level_a=math.nan if is_power else total,
        quantity=quantity,
        microphone_positions=n_positions,
        source_positions=n_sources,
    )


def sound_power_hard_walled(
    levels: ArrayLike,
    levels_ref: ArrayLike,
    lw_ref: ArrayLike | ReferenceSourceCalibration,
    frequencies: ArrayLike,
    *,
    background_levels: ArrayLike | None = None,
    background_levels_ref: ArrayLike | None = None,
    temperature_c: float = 23.0,
    static_pressure_kpa: float = 101.325,
    sigma_omc_db: float | None = None,
    coverage_factor: float = _COVERAGE_TWO_SIDED,
) -> HardWalledSoundPowerResult:
    r"""Sound power level of a small movable source in a hard-walled test room,
    by comparison with a reference sound source (ISO 3743-1:2010, 8.1).

    The octave-band time-averaged levels of the source under test are
    energy-averaged over the source locations, if the survey of 7.4 asked for
    more than one (Eq. 9), and over the microphone positions (Eq. 10); those of
    the reference source, placed where the source under test stood (7.2), over
    the same positions (Eq. 11), and the background likewise (Eq. 12). Each
    mean is corrected for background noise by the rule of 8.1.3 around
    Eq. (13), and

    .. math::

       L_W = L_{W(\mathrm{RSS})} - \overline{L'_{p(\mathrm{RSS})}}
       + \overline{L'_{p(\mathrm{ST})}} + K_{1(\mathrm{RSS})} - K_1
       \tag{Eq. 14}

    at the meteorological conditions of the test; ``sound_power_level_ref``
    adds the Annex A correction and ``sound_power_level_a`` is the Annex B
    total.

    :param levels: Measured (uncorrected) octave-band time-averaged levels of
        the source under test, in decibels: ``(bands,)`` for one microphone
        traverse (NOTE to 8.1.2), ``(NM, bands)`` for fixed positions, or
        ``(NS, NM, bands)`` for several source locations (Eq. 9).
    :param levels_ref: The same for the reference sound source at the same
        microphone positions, ``(NM, bands)``, or its traverse level
        ``(bands,)``.
    :param lw_ref: Calibrated octave-band sound power level of the reference
        source ``LW(RSS)``, ``(bands,)``, in decibels, under the
        meteorological conditions of the test, since Eq. (14) gives ``LW``
        there (Annex A); or the
        :class:`~phonometry.emission.ReferenceSourceCalibration` of ISO 6926,
        whose one-third octave bands are summed into the octaves at
        ``frequencies`` and carried from the reference conditions to those of
        the test by its own ``C2`` (ISO 6926:2016, 8.4).
    :param frequencies: Nominal octave mid-band frequencies, one per band,
        ascending, from 125 Hz to 8 kHz; 63 Hz is accepted where the room and
        the instrumentation are satisfactory there (3.11, Table B.1 footnote).
    :param background_levels: Octave-band background levels ``Lpi(B)``,
        ``(NM, bands)`` or one averaged ``(bands,)`` spectrum, in decibels.
        ``None`` applies no correction, warns and leaves
        ``background_requirement_met`` ``False`` throughout (4.5, 7.5).
    :param background_levels_ref: Background for the reference-source
        measurement, same shapes; ``None`` reuses ``background_levels``.
    :param temperature_c: Air temperature at the test, in degrees Celsius.
    :param static_pressure_kpa: Static pressure at the test, in kilopascals
        (Eq. A.2 gives it from the altitude,
        :func:`~phonometry.emission.static_pressure_from_altitude`).
    :param sigma_omc_db: Standard deviation of the operating and mounting
        conditions of the source (9.2, Eq. C.1), in decibels; ``None`` leaves
        ``sigma_tot`` and the expanded uncertainty ``NaN``.
    :param coverage_factor: ``k`` of Eq. (23), 2 by default as 9.5
        prescribes; 1,6 for a one-sided comparison with a limit (9.1).
    :return: :class:`HardWalledSoundPowerResult` with ``quantity='power'``.
    :raises ValueError: if a level array is not finite or of an admissible
        shape, the reference or background levels do not match the source's
        positions and bands, ``frequencies`` are not distinct ascending octave
        centres of Table B.1, the climate is out of range, ``sigma_omc_db`` is
        negative, ``coverage_factor`` is not positive, or a calibration does
        not cover the bands or used the manufacturer's ``C2``, whose value at
        the test only the manufacturer gives.
    """
    arr = _finite(levels, "levels", (1, 2, 3))
    grid, traverse = _source_grid(arr)
    n_sources, n_positions, _ = grid.shape
    _position_advisory(n_positions, traverse=traverse, stacklevel=3)
    per_position = energy_mean(grid, axis=0)  # Eq. (9)
    mean_source = np.asarray(energy_mean(per_position, axis=0), dtype=np.float64)
    return _determine(
        quantity="power",
        mean_source=mean_source,
        background_for_source=None,
        n_positions=n_positions,
        n_sources=n_sources,
        traverse=traverse,
        reference=_Reference(
            levels_ref=levels_ref,
            lw_ref=lw_ref,
            frequencies=frequencies,
            background_levels=background_levels,
            background_levels_ref=background_levels_ref,
            temperature_c=temperature_c,
            static_pressure_kpa=static_pressure_kpa,
            sigma_omc_db=sigma_omc_db,
            coverage_factor=coverage_factor,
        ),
    )


def _event_grid(arr: np.ndarray, events: int | None) -> tuple[np.ndarray, bool, int]:
    r"""The single event levels reduced to one event, as ``(NS, NM, NB)``.

    Measured one event at a time (``events`` ``None``) the events are on the
    first axis and Eq. (15) averages them; measured once over ``events``
    successive events, Eq. (16) subtracts :math:`10 \log_{10} N_\mathrm{e}`.
    The remaining axes read as for :func:`_source_grid`.

    :return: ``(levels of one event per location and position, traverse,
        events)``.
    :raises ValueError: for a rank that neither form admits.
    """
    if events is None:
        if arr.ndim not in (2, 3, 4):
            msg = (
                "'event_levels' measured one event at a time must be (Ne, bands), "
                "(Ne, NM, bands) or (Ne, NS, NM, bands)."
            )
            raise ValueError(msg)
        count = int(arr.shape[0])
        one_event = _single_event_mean(
            arr, None, name="event_levels", stacklevel=5, clause=f"{_STANDARD} 7.6"
        )
    else:
        if arr.ndim not in (1, 2, 3):
            msg = (
                "'event_levels' of one measurement over 'events' events must be "
                "(bands,), (NM, bands) or (NS, NM, bands)."
            )
            raise ValueError(msg)
        one_event = _single_event_mean(
            arr, events, name="event_levels", stacklevel=5, clause=f"{_STANDARD} 7.6"
        )
        count = int(events)
    grid, traverse = _source_grid(one_event)
    return grid, traverse, count


def sound_energy_hard_walled(
    event_levels: ArrayLike,
    levels_ref: ArrayLike,
    lw_ref: ArrayLike | ReferenceSourceCalibration,
    frequencies: ArrayLike,
    *,
    events: int | None = None,
    background_levels: ArrayLike | None = None,
    integration_time_s: float | None = None,
    background_levels_ref: ArrayLike | None = None,
    temperature_c: float = 23.0,
    static_pressure_kpa: float = 101.325,
    sigma_omc_db: float | None = None,
    coverage_factor: float = _COVERAGE_TWO_SIDED,
) -> HardWalledSoundPowerResult:
    r"""Sound energy level of a source emitting bursts, in a hard-walled test
    room, by comparison with a reference sound source (ISO 3743-1:2010, 8.2).

    The single event levels come in one of the two forms 7.6 admits. Measured
    one event at a time, the :math:`N_\mathrm{e}` events are on the first axis
    and Eq. (15) takes their energy mean; measured once over
    :math:`N_\mathrm{e}` successive events, Eq. (16) subtracts
    :math:`10 \log_{10} N_\mathrm{e}`. The level of one event is then
    averaged over the source locations (Eq. 17) and the positions (Eq. 18),
    corrected by the rule of 8.2.3 around Eq. (19), and

    .. math::

       L_J = L_{W(\mathrm{RSS})} - \overline{L'_{p(\mathrm{RSS})}}
       + \overline{L'_{E(\mathrm{ST})}} + K_{1(\mathrm{RSS})} - K_1
       \tag{Eq. 20}

    The reference source is steady and measured time-averaged over 30 s
    (7.6), so :math:`K_{1(\mathrm{RSS})}` follows 8.1.3 unchanged. For a
    source steady over the interval :math:`T` this gives
    :math:`L_J = L_W + 10 \log_{10}(T/T_0)`, :math:`T_0` = 1 s (3.4 NOTE 1).

    :param event_levels: Measured (uncorrected) octave-band single event
        levels, in decibels. With ``events`` ``None``: ``(Ne, bands)`` for a
        traverse, ``(Ne, NM, bands)`` or ``(Ne, NS, NM, bands)``, one entry
        per event on the first axis (Eq. 15). With ``events``: ``(bands,)``,
        ``(NM, bands)`` or ``(NS, NM, bands)``, one measurement encompassing
        ``events`` events (Eq. 16).
    :param levels_ref: Time-averaged levels of the reference sound source,
        ``(NM, bands)`` or ``(bands,)``, as in :func:`sound_power_hard_walled`.
    :param lw_ref: Calibrated sound power level of the reference source,
        ``(bands,)``, in decibels, under the meteorological conditions of the
        test, or its :class:`~phonometry.emission.ReferenceSourceCalibration`,
        as for :func:`sound_power_hard_walled`.
    :param frequencies: Nominal octave mid-band frequencies, one per band.
    :param events: The number :math:`N_\mathrm{e}` of events one measurement
        encompasses (Eq. 16); ``None`` when the events are on the first axis.
        Fewer than five warns (7.6).
    :param background_levels: Time-averaged background levels ``Lpi(B)``,
        ``(NM, bands)`` or ``(bands,)``, in decibels; requires
        ``integration_time_s``. ``None`` applies no correction, warns and
        leaves ``background_requirement_met`` ``False`` throughout.
    :param integration_time_s: The integration time ``T`` of the single event
        levels, in seconds. The background is compared as its exposure over
        the same ``T``, :math:`L_{p(\mathrm{B})} + 10 \log_{10}(T/T_0)`, so
        that Eq. (19) subtracts one energy from another.
    :param background_levels_ref: Background for the reference-source
        measurement; ``None`` reuses ``background_levels``, compared with the
        time-averaged reference level as it stands.
    :param temperature_c: Air temperature at the test, in degrees Celsius.
    :param static_pressure_kpa: Static pressure at the test, in kilopascals.
    :param sigma_omc_db: Operating-and-mounting standard deviation, in
        decibels.
    :param coverage_factor: ``k`` of Eq. (23), 2 by default.
    :return: :class:`HardWalledSoundPowerResult` with ``quantity='energy'``.
    :raises ValueError: for an ``event_levels`` rank neither form admits, a
        non-integer or non-positive ``events``, a background without its
        ``integration_time_s``, a non-positive ``integration_time_s``, or any
        refusal of :func:`sound_power_hard_walled`.
    """
    arr = np.asarray(event_levels, dtype=np.float64)
    if arr.size == 0 or not np.all(np.isfinite(arr)):
        msg = "'event_levels' must be a non-empty array of finite levels in decibels."
        raise ValueError(msg)
    grid, traverse, _ = _event_grid(arr, events)
    n_sources, n_positions, n_bands = grid.shape
    _position_advisory(n_positions, traverse=traverse, stacklevel=3)
    per_position = energy_mean(grid, axis=0)  # Eq. (17)
    mean_source = np.asarray(energy_mean(per_position, axis=0), dtype=np.float64)
    if integration_time_s is not None:
        require_positive(integration_time_s, "integration_time_s")
    exposure: np.ndarray | None = None
    if background_levels is not None:
        if integration_time_s is None:
            msg = (
                "'integration_time_s' (the interval T of the single event levels, "
                "in seconds) is required with 'background_levels': Eq. (19) "
                "compares the background as its exposure over the same T "
                f"({_STANDARD}, 8.2.3)."
            )
            raise ValueError(msg)
        bg = _finite(background_levels, "background_levels", (1, 2))
        carried = _background_exposure(bg, integration_time_s)
        exposure = _position_mean(carried, "background_levels", n_positions, n_bands)
    return _determine(
        quantity="energy",
        mean_source=mean_source,
        background_for_source=exposure,
        n_positions=n_positions,
        n_sources=n_sources,
        traverse=traverse,
        reference=_Reference(
            levels_ref=levels_ref,
            lw_ref=lw_ref,
            frequencies=frequencies,
            background_levels=background_levels,
            background_levels_ref=background_levels_ref,
            temperature_c=temperature_c,
            static_pressure_kpa=static_pressure_kpa,
            sigma_omc_db=sigma_omc_db,
            coverage_factor=coverage_factor,
        ),
    )


def reproducibility_from_round_robin(total_db: float, operating_db: float) -> float:
    r"""The standard deviation of reproducibility of the method from a round
    robin test (ISO 3743-1:2010 Eq. 24).

    .. math::

       \sigma'_{R0} = \sqrt{\sigma'^2_\mathrm{tot} - \sigma'^2_\mathrm{omc}}

    A round robin gives the total standard deviation :math:`\sigma'_\mathrm{tot}`
    of one source, which still carries the instability of that source's
    operating and mounting conditions; taking it out in quadrature leaves
    what the method itself contributes. ISO 3743-2:2018 prints the same
    relation as its Formula (14) with a plus sign, which would make the
    method's share larger than the total it is extracted from; the sentence
    after it (the result is imprecise when :math:`\sigma_\mathrm{tot}` is only
    slightly higher than :math:`\sigma_\mathrm{omc}`) holds only for the
    difference, and the library evaluates the difference for both parts (see
    ``docs/ERRATA.md``).

    The clause adds a condition on the inputs: to keep the result from being
    a small number of low accuracy, :math:`\sigma_\mathrm{omc}` should not
    exceed :math:`\sigma_\mathrm{tot}/\sqrt{2}`. Beyond it this warns; the
    value is still returned.

    :param total_db: :math:`\sigma'_\mathrm{tot}` of the round robin, in
        decibels.
    :param operating_db: :math:`\sigma'_\mathrm{omc}` of the source used in
        it, in decibels.
    :return: :math:`\sigma'_{R0}`, in decibels.
    :raises ValueError: if either is negative or not finite, or
        ``operating_db`` exceeds ``total_db``, which no round robin can
        produce.
    """
    total = require_non_negative(total_db, "total_db")
    operating = require_non_negative(operating_db, "operating_db")
    if not math.isfinite(total) or not math.isfinite(operating):
        msg = "'total_db' and 'operating_db' must be finite."
        raise ValueError(msg)
    if operating > total:
        msg = (
            f"'operating_db' ({operating:g} dB) exceeds 'total_db' ({total:g} dB): "
            "the total of a round robin includes the operating and mounting "
            f"conditions ({_STANDARD}, 9.3.2)."
        )
        raise ValueError(msg)
    if operating > total / math.sqrt(2.0):
        warnings.warn(
            "sigma_omc exceeds sigma_tot/sqrt(2); the reproducibility extracted "
            f"from this round robin is of low accuracy ({_STANDARD}, 9.3.2).",
            SoundPowerWarning,
            stacklevel=2,
        )
    return math.sqrt(total * total - operating * operating)


@dataclass(frozen=True)
class HardWalledRoomCheck:
    r"""Qualification of a hard-walled test room (ISO 3743-1:2010, 4.2 to 4.4).

    ``level_range_db`` is, per octave band, the largest difference between
    the mean levels of any two of the directional source's orientations
    (4.4), and ``limit_db`` the Table 3 value it may not exceed.
    ``volume_m3`` is the room, ``reference_box_volume_m3`` and
    ``largest_box_dimension_m`` the reference box of 4.1, and
    ``minimum_volume_m3`` / ``box_dimension_limit_m`` what 4.2 asks of them.
    ``max_absorption_coefficient`` is the largest sound absorption coefficient
    of any portion of the boundary surfaces, ``NaN`` when none was supplied,
    against the 0,20 of 4.3. ``minimum_microphone_distance_m`` is the
    :math:`d_\mathrm{min} = 0{,}3\,V^{1/3}` of 7.3 that keeps the microphones
    in the reverberant field, stated for the setup rather than judged.
    """

    frequencies: np.ndarray
    level_range_db: np.ndarray
    limit_db: np.ndarray
    orientations: int
    volume_m3: float
    reference_box_volume_m3: float
    largest_box_dimension_m: float
    minimum_volume_m3: float
    box_dimension_limit_m: float
    max_absorption_coefficient: float
    minimum_microphone_distance_m: float

    def __post_init__(self) -> None:
        """Reject a check whose per-band arrays disagree.

        :raises ValueError: if the three per-band arrays differ in length or
            rank, or fewer than two orientations are recorded.
        """
        require_ranks(self, frequencies=1, level_range_db=1, limit_db=1)
        require_same_length(self, "frequencies", "level_range_db", "limit_db")
        if self.orientations < 2:  # noqa: PLR2004
            msg = "HardWalledRoomCheck: 'orientations' must be at least 2."
            raise ValueError(msg)

    @property
    def band_adequate(self) -> np.ndarray:
        """Per band, whether the spread stays within Table 3 (4.4)."""
        return np.asarray(settled(self.level_range_db) <= self.limit_db, dtype=bool)

    @property
    def acoustically_adequate(self) -> bool:
        """The 4.4 criterion: every band within Table 3."""
        return bool(np.all(self.band_adequate))

    @property
    def volume_adequate(self) -> bool:
        """The volume criterion of 4.2: at least 40 m³ and 40 reference boxes.

        Both volumes are rounded to nine decimal places before they are
        compared: forty times a box measured in decimal metres can come out a
        last bit above a room volume that equals it, and 4.2 asks for "at
        least".
        """
        volume = float(settled(self.volume_m3))
        return volume >= float(settled(self.minimum_volume_m3))

    @property
    def box_fits(self) -> bool:
        """The size criterion of 4.2 on the largest reference-box dimension."""
        return self.largest_box_dimension_m <= self.box_dimension_limit_m

    @property
    def surfaces_hard(self) -> bool | None:
        """The 4.3 criterion, ``None`` when no absorption was supplied."""
        if math.isnan(self.max_absorption_coefficient):
            return None
        return self.max_absorption_coefficient <= _MAX_ABSORPTION_COEFFICIENT

    @property
    def passes(self) -> bool:
        """Whether the room qualifies on every criterion that was evaluated."""
        hard = self.surfaces_hard
        return (
            self.acoustically_adequate
            and self.volume_adequate
            and self.box_fits
            and (hard is None or hard)
        )

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = (
            "a HardWalledRoomCheck has no truth value; read its '.passes' "
            "for the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the orientation spread per band against the Table 3 limit.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the spread bars.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.emission import plot_hard_walled_room_check

        return plot_hard_walled_room_check(
            self, ax=ax, language=check_language(language), **kwargs
        )


def check_hard_walled_room(
    orientation_levels: ArrayLike,
    frequencies: ArrayLike,
    *,
    volume_m3: float,
    reference_box_m: ArrayLike,
    absorption_coefficients: ArrayLike | None = None,
) -> HardWalledRoomCheck:
    r"""Is this room a hard-walled test room? ISO 3743-1:2010, 4.2 to 4.4.

    The acoustic criterion of 4.4 turns a highly directional broadband source,
    directivity index at least 5 dB above 500 Hz, through four horizontal and
    four vertical orientations, each time taking the mean background-corrected
    octave level over the microphone positions. The room suits the method if
    in every band from 125 Hz to 8 kHz the largest difference between any two
    of the eight means stays within the standard deviation of reproducibility
    of Table 3. The NOTE allows a source of the type to be tested in place of
    the directional one, which then qualifies the room for that type only.

    4.2 adds the size: at least 40 m³ and forty times the reference box, whose
    largest dimension is at most 1,0 m in a room of up to 100 m³ and 2,0 m in
    a larger one. 4.3 adds the surfaces: no portion of any boundary absorbing
    more than 0,20 at any frequency of interest; Table 1 describes the rooms
    that meet it in words, and the coefficients are optional here.

    :param orientation_levels: Mean octave-band levels of the directional
        source, one row per orientation (eight in 4.4), ``(orientations,
        bands)``, in decibels.
    :param frequencies: Nominal octave mid-band frequencies from 125 Hz to
        8 kHz, one per band, ascending.
    :param volume_m3: Volume of the test room, in cubic metres.
    :param reference_box_m: The three dimensions of the reference box, in
        metres (4.1).
    :param absorption_coefficients: Sound absorption coefficients of the
        boundary surfaces, any shape (per surface and per band, say); only
        the largest is read. ``None`` leaves 4.3 unevaluated.
    :return: The verdict, as a :class:`HardWalledRoomCheck`.
    :raises ValueError: for levels that are not a finite 2D array of at least
        two orientations, frequencies outside 125 Hz to 8 kHz, a non-positive
        volume or box dimension, or an absorption coefficient outside [0, 1].
    """
    levels = _finite(orientation_levels, "orientation_levels", (2,))
    n_orientations, n_bands = levels.shape
    if n_orientations < 2:  # noqa: PLR2004
        msg = (
            "'orientation_levels' must hold at least two orientations (4.4 uses eight)."
        )
        raise ValueError(msg)
    freqs = _octave_frequencies(frequencies, n_bands)
    if any(round(float(f)) not in _SIGMA_R0_DB for f in freqs):
        msg = (
            "'frequencies' must lie in 125 Hz to 8 kHz, the bands 4.4 judges "
            f"against Table 3 ({_STANDARD})."
        )
        raise ValueError(msg)
    if n_orientations != _ORIENTATIONS:
        warnings.warn(
            f"{n_orientations} orientations were supplied; the procedure of 4.4 "
            f"uses {_ORIENTATIONS}, four horizontal and four vertical ({_STANDARD}).",
            SoundPowerWarning,
            stacklevel=2,
        )
    volume = require_positive(volume_m3, "volume_m3")
    box = np.asarray(reference_box_m, dtype=np.float64)
    if box.shape != (3,) or not np.all(np.isfinite(box)) or np.any(box <= 0.0):
        msg = "'reference_box_m' must be three positive, finite dimensions in metres."
        raise ValueError(msg)
    box_volume = float(np.prod(box))
    alpha_max = math.nan
    if absorption_coefficients is not None:
        alpha = np.asarray(absorption_coefficients, dtype=np.float64)
        if (
            alpha.size == 0
            or not np.all(np.isfinite(alpha))
            or np.any(alpha < 0.0)
            or np.any(alpha > 1.0)
        ):
            msg = "'absorption_coefficients' must be finite values in [0, 1]."
            raise ValueError(msg)
        alpha_max = float(np.max(alpha))
    return HardWalledRoomCheck(
        frequencies=freqs,
        level_range_db=np.asarray(np.ptp(levels, axis=0), dtype=np.float64),
        limit_db=_table3_sigma(freqs),
        orientations=n_orientations,
        volume_m3=volume,
        reference_box_volume_m3=box_volume,
        largest_box_dimension_m=float(np.max(box)),
        minimum_volume_m3=max(
            _MIN_ROOM_VOLUME_M3, _ROOM_TO_BOX_VOLUME_RATIO * box_volume
        ),
        box_dimension_limit_m=(
            _BOX_LIMIT_SMALL_ROOM_M
            if volume <= _SMALL_ROOM_LIMIT_M3
            else _BOX_LIMIT_LARGE_ROOM_M
        ),
        max_absorption_coefficient=alpha_max,
        minimum_microphone_distance_m=_REVERBERANT_DISTANCE_FACTOR * volume ** (1 / 3),
    )


@dataclass(frozen=True)
class SourceLocationPlan:
    r"""How many source locations a determination needs, from a preliminary
    survey of the room (ISO 3743-1:2010 7.4, Table 2; ISO 3743-2:2018 9.4,
    Table 3).

    ``standard_deviation_db`` is the estimated standard deviation
    :math:`s_\mathrm{M}` of the preliminary levels per band, and
    ``source_locations`` the minimum number :math:`N_\mathrm{S}` of source
    locations its table asks for, in the same room. Part 1 sends a band above
    4 dB to a second room as well: ``additional_room_locations`` counts the
    locations there, two in such a band and zero elsewhere, and always zero
    for Part 2. ``microphone_positions`` is the :math:`N_\mathrm{M}` the
    numbers are read for: the preliminary positions of Part 1, the column of
    Part 2's Table 3.

    ``spectral_character`` is Part 2's 9.5 reading of :math:`s_\mathrm{M}` per
    band, ``'broadband'``, ``'narrow-band'`` or ``'discrete tone'``, and
    ``None`` for Part 1, which draws no such conclusion. The ``a_weighted_...``
    fields are the same for the A-weighted row of Part 2 when A-weighted
    levels were surveyed, ``NaN``, 0 and ``None`` otherwise.
    """

    standard: str
    frequencies: np.ndarray
    standard_deviation_db: np.ndarray
    source_locations: np.ndarray
    additional_room_locations: np.ndarray
    microphone_positions: int
    spectral_character: tuple[str, ...] | None = None
    a_weighted_standard_deviation_db: float = math.nan
    a_weighted_source_locations: int = 0
    a_weighted_spectral_character: str | None = None

    def __post_init__(self) -> None:
        """Reject a plan whose per-band quantities disagree.

        :raises ValueError: if the per-band arrays differ in length or rank,
            the spectral character does not name one class per band, or the
            standard is not one of the two parts.
        """
        require_choice(
            self.standard, "standard", ("ISO 3743-1:2010", "ISO 3743-2:2018")
        )
        bands = (
            "frequencies",
            "standard_deviation_db",
            "source_locations",
            "additional_room_locations",
        )
        require_ranks(self, **dict.fromkeys(bands, 1))
        require_same_length(self, *bands)
        if self.spectral_character is not None and len(self.spectral_character) != len(
            self.frequencies
        ):
            msg = (
                "SourceLocationPlan: 'spectral_character' must name one class per band."
            )
            raise ValueError(msg)

    @property
    def required_source_locations(self) -> int:
        r"""The largest :math:`N_\mathrm{S}` any band (or the A-weighted row)
        asks for in the test room, which is the number a single determination
        covering them all has to use.
        """
        return int(max(np.max(self.source_locations), self.a_weighted_source_locations))

    @property
    def other_room_required(self) -> bool:
        """Whether a band of Part 1 sends the determination to a second room."""
        return bool(np.any(self.additional_room_locations > 0))

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        r"""Plot :math:`s_\mathrm{M}` per band against the table's class limits,
        with the number of source locations over each bar.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the standard-deviation bars.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.emission import plot_source_location_plan

        return plot_source_location_plan(
            self, ax=ax, language=check_language(language), **kwargs
        )


def hard_walled_source_locations(
    levels: ArrayLike, frequencies: ArrayLike
) -> SourceLocationPlan:
    r"""The number of source locations from the preliminary survey of
    ISO 3743-1:2010, 7.4 (Table 2).

    For a source with audible discrete tones or narrow bands of noise, at
    least six fixed microphone positions record the uncorrected level of the
    source under test, and their standard deviation per band

    .. math::

       s_\mathrm{M} = \left[ \frac{1}{N_\mathrm{M(pre)} - 1}
       \sum_{i=1}^{N_\mathrm{M(pre)}} \left( L'_{pi(\mathrm{pre})}
       - \overline{L'_{p(\mathrm{pre})}} \right)^2 \right]^{1/2}
       \tag{Eq. 7}

    about their arithmetic mean (Eq. 8) decides the number of source
    locations: one up to 2,5 dB, two in the same room up to 4,0 dB, and above
    that two in the same room plus two more in another room of different
    dimensions that still complies with 4.4.

    :param levels: Preliminary levels, ``(NM, bands)`` with at least six rows,
        in decibels.
    :param frequencies: Nominal octave mid-band frequencies, one per band.
    :return: The :class:`SourceLocationPlan`.
    :raises ValueError: for levels that are not a finite 2D array of at least
        two positions, or frequencies that are not octave centres.
    """
    arr = _finite(levels, "levels", (2,))
    n_positions, n_bands = arr.shape
    if n_positions < 2:  # noqa: PLR2004
        msg = "'levels' must hold at least two microphone positions for Eq. (7)."
        raise ValueError(msg)
    if n_positions < _MIN_PRELIMINARY_MICROPHONES:
        warnings.warn(
            f"{n_positions} microphone position(s) were supplied; the preliminary "
            f"survey uses at least {_MIN_PRELIMINARY_MICROPHONES} ({_STANDARD}, 7.4).",
            SoundPowerWarning,
            stacklevel=2,
        )
    freqs = _octave_frequencies(frequencies, n_bands)
    s_m = np.asarray(np.std(arr, axis=0, ddof=1), dtype=np.float64)  # Eq. (7), (8)
    row = settled(s_m)
    locations = np.where(row <= _TABLE2_ONE_LOCATION_DB, 1, 2).astype(np.int64)
    other = np.where(
        row > _TABLE2_TWO_LOCATIONS_DB, _TABLE2_OTHER_ROOM_LOCATIONS, 0
    ).astype(np.int64)
    return SourceLocationPlan(
        standard=_STANDARD,
        frequencies=freqs,
        standard_deviation_db=s_m,
        source_locations=locations,
        additional_room_locations=other,
        microphone_positions=n_positions,
    )
