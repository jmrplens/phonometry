#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""NPD data for a non-reference atmosphere (ECAC Doc 29 Vol. 2 Appendix D).

The noise-power-distance (NPD) curves of the ANP database are normalised to
the **SAE AIR-1845 atmosphere**: the arithmetic mean of the attenuation rates
measured in European and US certification tests (Table D-1), a notional
atmosphere that no single temperature and humidity produce. Where the air of a
study differs, Appendix D recalculates the NPD data from the spectral class of
the NPD, the unweighted reference spectrum at 1 000 ft, in three steps:

1. the AIR-1845 attenuation over the reference distance
   :math:`d_\mathrm{ref}` = 1 000 ft is added back (Eq. D-1);
2. the corrected spectrum is taken to each NPD distance :math:`d_i` with
   spherical spreading and, in turn, the AIR-1845 attenuation (Eq. D-2) and
   the attenuation of the specified atmosphere (Eq. D-3), by SAE ARP 5534 or
   by SAE ARP 866A;
3. both spectra are A-weighted and summed, and the difference of the two
   levels is the increment :math:`\Delta L(d_i)` (Eq. D-4), added to the
   ``Lmax`` and ``LE`` NPD levels alike.

* :data:`SAE_AIR1845_ATTENUATION_DB_PER_100M` -- Table D-1.
* :func:`npd_atmosphere_increment` -- the increment at each NPD distance, as an
  :class:`NpdAtmosphereIncrement` with ``.plot()`` (the increment against
  distance) and ``.plot_attenuation()`` (the attenuation of the two
  atmospheres against frequency).
* :func:`revise_npd_curves` -- an
  :class:`~phonometry.aircraft.anp_fleet.AnpNpdCurves` revised by that
  increment, as a :class:`RevisedNpdCurves` with ``.plot()``; its ``revised``
  curves feed :func:`~phonometry.aircraft.airport_noise.event_level` and
  :func:`~phonometry.aircraft.airport_noise.noise_contour` like any other NPD
  table.

The A-weighting of step 3 is the nominal one of IEC 61672-1, to 0.1 dB, in the
24 bands from 50 Hz to 10 kHz: Doc 29 names it :math:`A_n` without printing
it, and those are the values that reproduce Tables D-4 and D-5.

Source (clean-room, implemented from the document): ECAC.CEAC Doc 29, 5th ed.
(2026), Volume 2, Appendix D, Eqs. D-1 to D-4 and Table D-1, and G4.3 for the
spectral classes. Checked end to end against Tables D-2 to D-6c of the same
appendix.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final

import numpy as np

from .._internal.frozen import read_only
from .._internal.validation import (
    require_choice,
    require_finite_array,
    require_positive_array,
    require_ranks,
    require_same_length,
)
from ..filters.weighting_compliance import _WEIGHTING_TABLE3
from .anp_fleet import SpectralClass
from .atmospheric_absorption import (
    _arp5534_coefficient,
    _sae_band,
    arp866a_attenuation,
)
from .certification import NOY_BANDS

if TYPE_CHECKING:
    from collections.abc import Mapping

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

    from .anp_fleet import AnpNpdCurves

#: ECAC Doc 29 Vol. 2 Table D-1: the average atmospheric attenuation rates of
#: SAE AIR-1845 that normalise the ANP NPD data, in dB per 100 m, keyed by the
#: nominal one-third-octave-band centre frequency in Hz (50 Hz to 10 kHz).
SAE_AIR1845_ATTENUATION_DB_PER_100M: Final[Mapping[float, float]] = MappingProxyType(
    {
        50.0: 0.033,
        63.0: 0.033,
        80.0: 0.033,
        100.0: 0.066,
        125.0: 0.066,
        160.0: 0.098,
        200.0: 0.131,
        250.0: 0.131,
        315.0: 0.197,
        400.0: 0.230,
        500.0: 0.295,
        630.0: 0.361,
        800.0: 0.459,
        1000.0: 0.590,
        1250.0: 0.754,
        1600.0: 0.983,
        2000.0: 1.311,
        2500.0: 1.705,
        3150.0: 2.295,
        4000.0: 3.115,
        5000.0: 3.607,
        6300.0: 5.246,
        8000.0: 7.213,
        10000.0: 9.836,
    }
)


def _nominal_a_weighting_db(bands: NDArray[np.float64]) -> NDArray[np.float64]:
    """The nominal A-weighting of IEC 61672-1:2013 Table 3 at the given bands, in dB.

    Read from the one transcription of that table the library keeps, the one
    the weighting-class verifier uses, so the two cannot drift apart.
    """
    by_band = {row[0]: row[1] for row in _WEIGHTING_TABLE3}
    return read_only(np.array([by_band[float(band)] for band in bands]))


#: IEC 61672-1:2013 Table 3: the nominal A-weighting of the 24 bands from 50 Hz
#: to 10 kHz, in dB, the ``-A_n`` of Doc 29 Eq. D-4.
_A_WEIGHTING_DB = _nominal_a_weighting_db(NOY_BANDS)
#: Feet to metres: the NPD distances are defined in feet.
_FT_M = 0.3048
#: The reference distance ``d_ref`` of the spectral classes, 1 000 ft. The
#: page rounds it to 305 m; Table D-3a is 1 000 ft times Table D-1 exactly.
_REFERENCE_DISTANCE_M = 1000.0 * _FT_M
#: The ten standard NPD distances of Appendix D, footnote 40, in metres.
_NPD_DISTANCES_M = read_only(
    np.array(
        [200.0, 400.0, 630.0, 1000.0, 2000.0, 4000.0, 6300.0, 10000.0, 16000.0, 25000.0]
    )
    * _FT_M
)
#: The two absorption routes Appendix D offers for the specified atmosphere.
_ABSORPTION = ("arp5534", "arp866a")
#: Relative tolerance within which a distance names one of the table's own.
_DISTANCE_MATCH_RTOL = 1e-9


def _spectrum_levels(spectrum: SpectralClass | ArrayLike) -> NDArray[np.float64]:
    """The 24 band levels of a spectral class, or of a bare array of them."""
    raw = spectrum.levels_db if isinstance(spectrum, SpectralClass) else spectrum
    levels = require_finite_array(raw, "spectrum")
    if levels.size != NOY_BANDS.size:
        msg = (
            f"'spectrum' must carry the {NOY_BANDS.size} one-third-octave-band "
            f"levels from 50 Hz to 10 kHz of a spectral class; got {levels.size}."
        )
        raise ValueError(msg)
    return levels


def _a_weighted_sum(levels: NDArray[np.float64]) -> NDArray[np.float64]:
    """A-weighted level of each column of a ``(bands, distances)`` spectrum (Eq. D-4)."""
    weighted = levels + _A_WEIGHTING_DB[:, None]
    return np.asarray(
        10.0 * np.log10(np.sum(10.0 ** (weighted / 10.0), axis=0)), dtype=np.float64
    )


@dataclass(frozen=True)
class NpdAtmosphereIncrement:
    r"""The NPD increment for a specified atmosphere (ECAC Doc 29 Vol. 2 Appendix D).

    Every per-band array runs over the 24 bands of :attr:`frequencies_hz`, and
    every per-distance array over :attr:`distances_m`; the two attenuation
    tables are ``(bands, distances)``.

    :ivar frequencies_hz: Nominal one-third-octave-band centre frequencies, in
        Hz (50 Hz to 10 kHz).
    :ivar distances_m: The NPD slant distances :math:`d_i`, in metres.
    :ivar spectrum_db: The spectral class as given, :math:`L_{n,\mathrm{ref}}(d_\mathrm{ref})`
        at 1 000 ft in the AIR-1845 atmosphere, in dB.
    :ivar source_spectrum_db: :math:`L_n(d_\mathrm{ref})`, the same spectrum
        with the AIR-1845 attenuation added back (Eq. D-1), in dB.
    :ivar reference_attenuation_db:
        :math:`\alpha_{n,\mathrm{ref}} \, d_i / (100\,\mathrm{m})`, the
        AIR-1845 attenuation at each distance (Table D-3a), in dB.
    :ivar specified_attenuation_db:
        :math:`\delta_n(d_i) \, d_i / (100\,\mathrm{m})`, the attenuation of
        the specified atmosphere (Tables D-3b and D-3c), in dB.
    :ivar reference_levels_dba: :math:`L_{A,\mathrm{ref}}(d_i)`, in dB.
    :ivar specified_levels_dba: :math:`L_{A,\mathrm{atm}}(d_i)`, in dB.
    :ivar increment_db: :math:`\Delta L(d_i) = L_{A,\mathrm{atm}} - L_{A,\mathrm{ref}}`
        (Eq. D-4), in dB, to add to the NPD levels at the same distances.
    :ivar absorption: ``"arp5534"`` or ``"arp866a"``, the route taken for the
        specified atmosphere.
    :ivar temperature_c: Air temperature, in degrees Celsius.
    :ivar relative_humidity_percent: Relative humidity, in percent.
    :ivar atmospheric_pressure_kpa: Air pressure, in kPa. SAE ARP 866A does
        not use it.
    """

    frequencies_hz: NDArray[np.float64]
    distances_m: NDArray[np.float64]
    spectrum_db: NDArray[np.float64]
    source_spectrum_db: NDArray[np.float64]
    reference_attenuation_db: NDArray[np.float64]
    specified_attenuation_db: NDArray[np.float64]
    reference_levels_dba: NDArray[np.float64]
    specified_levels_dba: NDArray[np.float64]
    increment_db: NDArray[np.float64]
    absorption: str
    temperature_c: float
    relative_humidity_percent: float
    atmospheric_pressure_kpa: float

    def __post_init__(self) -> None:
        """Reject an increment whose tables do not share its bands and distances.

        The increment is added to an NPD table column by column, so a
        per-distance array one short would shift every level it is added to
        by one distance, and an attenuation table transposed would still be
        24 by 10 where the distances are ten: both axes are pinned.

        :raises ValueError: if an array disagrees with the bands or the
            distances, or carries an axis too many or too few.
        """
        require_ranks(
            self,
            frequencies_hz=1,
            distances_m=1,
            spectrum_db=1,
            source_spectrum_db=1,
            reference_attenuation_db=2,
            specified_attenuation_db=2,
            reference_levels_dba=1,
            specified_levels_dba=1,
            increment_db=1,
        )
        require_same_length(
            self,
            "frequencies_hz",
            "spectrum_db",
            "source_spectrum_db",
            "reference_attenuation_db",
            "specified_attenuation_db",
        )
        require_same_length(
            self,
            "distances_m",
            ("reference_attenuation_db", 1),
            ("specified_attenuation_db", 1),
            "reference_levels_dba",
            "specified_levels_dba",
            "increment_db",
            axis="NPD distance",
        )

    def distance_column(self, distance_m: float) -> int:
        """Column of the tables that holds one of :attr:`distances_m`.

        :param distance_m: One of the NPD distances, in metres.
        :return: Its index along the distance axis.
        :raises ValueError: if the distance is not one of the table's.
        """
        match = np.flatnonzero(
            np.isclose(self.distances_m, float(distance_m), rtol=_DISTANCE_MATCH_RTOL)
        )
        if match.size == 0:
            msg = (
                f"'distance_m' must be one of the NPD distances "
                f"{np.round(self.distances_m, 2).tolist()} m; got {distance_m!r}."
            )
            raise ValueError(msg)
        return int(match[0])

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the increment against slant distance."""
        from .._i18n import check_language
        from .._plot.aircraft import plot_npd_atmosphere_increment

        return plot_npd_atmosphere_increment(
            self, ax=ax, language=check_language(language), **kwargs
        )

    def plot_attenuation(
        self,
        ax: Axes | None = None,
        *,
        distance_m: float = _REFERENCE_DISTANCE_M,
        reference: bool = True,
        language: str = "en",
        **kwargs: Any,
    ) -> Axes:
        """Plot the attenuation of both atmospheres against frequency at one distance.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param distance_m: One of :attr:`distances_m` (default 1 000 ft).
        :param reference: Also draw the AIR-1845 attenuation. Pass ``False``
            to add a second route to axes that already carry it.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the specified-atmosphere ``plot`` call.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.aircraft import plot_npd_atmosphere_attenuation

        return plot_npd_atmosphere_attenuation(
            self,
            ax=ax,
            column=self.distance_column(distance_m),
            reference=reference,
            language=check_language(language),
            **kwargs,
        )


def npd_atmosphere_increment(
    spectrum: SpectralClass | ArrayLike,
    *,
    temperature_c: float,
    relative_humidity_percent: float,
    atmospheric_pressure_kpa: float = 101.325,
    absorption: str = "arp5534",
    distances_m: ArrayLike | None = None,
) -> NpdAtmosphereIncrement:
    r"""NPD increment of a spectral class for a specified atmosphere (Doc 29 Appendix D).

    .. math::

       L_n(d_\mathrm{ref}) = L_{n,\mathrm{ref}}(d_\mathrm{ref})
       + \alpha_{n,\mathrm{ref}} \, \frac{d_\mathrm{ref}}{100\,\mathrm{m}}
       \qquad \text{(D-1)}

       L_{n,\mathrm{ref}}(d_i) = L_n(d_\mathrm{ref})
       - 20 \lg(d_i/d_\mathrm{ref})
       - \alpha_{n,\mathrm{ref}} \, \frac{d_i}{100\,\mathrm{m}}
       \qquad \text{(D-2)}

       L_{n,\mathrm{atm}}(d_i) = L_n(d_\mathrm{ref})
       - 20 \lg(d_i/d_\mathrm{ref})
       - \delta_n(d_i) \, \frac{d_i}{100\,\mathrm{m}}
       \qquad \text{(D-3)}

       \Delta L(d_i) = 10 \lg \sum_n 10^{(L_{n,\mathrm{atm}}(d_i) - A_n)/10}
       - 10 \lg \sum_n 10^{(L_{n,\mathrm{ref}}(d_i) - A_n)/10}
       \qquad \text{(D-4)}

    with the distances in metres, :math:`d_\mathrm{ref}` = 1 000 ft = 304.8 m,
    :math:`\alpha_{n,\mathrm{ref}}` the Table D-1 rate in dB per 100 m of path,
    the unit the table prints (Doc 29 writes the equations with the rates in
    dB/m instead), and
    :math:`\delta_n(d_i) \, d_i / (100\,\mathrm{m})` the band attenuation of
    the specified atmosphere over :math:`d_i`: the SAE Method of SAE ARP 5534
    (:func:`~phonometry.aircraft.atmospheric_absorption.sae_band_attenuation`),
    which depends on the path and the pressure, or SAE ARP 866A
    (:func:`~phonometry.aircraft.atmospheric_absorption.arp866a_attenuation`),
    which depends on neither, with ``η(δ)`` read linearly in Table 1 of ISO
    3891, as Tables D-3b and D-5 are computed. Doc 29 recommends ARP 5534 and
    keeps ARP 866A for transition. Nothing is rounded: Tables D-4 to D-6c are rounded for
    presentation only, and the increment is carried at full precision.

    The increment is a difference of two sums over the same spectrum, so it
    does not depend on the overall level of the spectral class, only on its
    shape; the spectral classes are normalised to 70 dB at 1 kHz (G4.3).

    :param spectrum: The spectral class of the NPD, a
        :class:`~phonometry.aircraft.anp_fleet.SpectralClass` or its 24
        one-third-octave-band levels from 50 Hz to 10 kHz at 1 000 ft, in dB.
    :param temperature_c: Air temperature ``T``, in degrees Celsius.
    :param relative_humidity_percent: Relative humidity, in percent.
    :param atmospheric_pressure_kpa: Air pressure ``pa``, in kPa (default
        101.325, sea level). Read by ARP 5534 only.
    :param absorption: ``"arp5534"`` (default) or ``"arp866a"``.
    :param distances_m: The NPD slant distances, in metres. ``None`` takes the
        ten standard ones of footnote 40, 200 ft to 25 000 ft.
    :return: An :class:`NpdAtmosphereIncrement`.
    :raises ValueError: for a spectrum that is not 24 finite levels, an unknown
        absorption route, a distance that is not positive, or an atmosphere
        the chosen route refuses.
    """
    levels = _spectrum_levels(spectrum)
    route = require_choice(absorption, "absorption", _ABSORPTION)
    d = (
        np.array(_NPD_DISTANCES_M)
        if distances_m is None
        else require_positive_array(distances_m, "distances_m")
    )
    frequencies = np.array(NOY_BANDS, dtype=np.float64)
    rates = np.array(
        [SAE_AIR1845_ATTENUATION_DB_PER_100M[float(f)] for f in frequencies]
    )
    source = levels + rates / 100.0 * _REFERENCE_DISTANCE_M
    reference_attenuation = np.multiply.outer(rates / 100.0, d)
    if route == "arp5534":
        alpha = _arp5534_coefficient(
            frequencies,
            float(temperature_c),
            float(relative_humidity_percent),
            float(atmospheric_pressure_kpa),
        )
        specified_attenuation = _sae_band(np.multiply.outer(alpha, d))
    else:
        # Table D-3b, and through it Tables D-5 and D-6c, read eta(delta)
        # linearly in Table 1 of ISO 3891 (see arp866a_attenuation).
        specified_attenuation = arp866a_attenuation(
            frequencies,
            temperature_c=temperature_c,
            relative_humidity_percent=relative_humidity_percent,
            eta_interpolation="linear",
        ).path_attenuation_db(d)
    spread = source[:, None] - 20.0 * np.log10(d / _REFERENCE_DISTANCE_M)[None, :]
    reference_levels = _a_weighted_sum(spread - reference_attenuation)
    specified_levels = _a_weighted_sum(spread - specified_attenuation)
    return NpdAtmosphereIncrement(
        frequencies_hz=frequencies,
        distances_m=d,
        spectrum_db=levels,
        source_spectrum_db=source,
        reference_attenuation_db=reference_attenuation,
        specified_attenuation_db=np.asarray(specified_attenuation, dtype=np.float64),
        reference_levels_dba=reference_levels,
        specified_levels_dba=specified_levels,
        increment_db=specified_levels - reference_levels,
        absorption=route,
        temperature_c=float(temperature_c),
        relative_humidity_percent=float(relative_humidity_percent),
        atmospheric_pressure_kpa=float(atmospheric_pressure_kpa),
    )


@dataclass(frozen=True)
class RevisedNpdCurves:
    """NPD curves recalculated for a specified atmosphere (Doc 29 Vol. 2 Appendix D).

    :ivar original: The curves as the ANP database gives them, in the AIR-1845
        atmosphere.
    :ivar revised: The same curves with :attr:`increment` added at every power
        setting, an :class:`~phonometry.aircraft.anp_fleet.AnpNpdCurves` that
        :meth:`~phonometry.aircraft.anp_fleet.AnpNpdCurves.level` and the Doc 29
        event chain read like any other.
    :ivar increment: The increment and everything it was computed from.
    """

    original: AnpNpdCurves
    revised: AnpNpdCurves
    increment: NpdAtmosphereIncrement

    def __post_init__(self) -> None:
        """Reject a revision whose increment was taken at other distances.

        :raises ValueError: if the increment does not run over the distances
            of the curves it revised.
        """
        if self.increment.distances_m.shape != self.original.distances.shape or not (
            np.allclose(
                self.increment.distances_m,
                self.original.distances,
                rtol=_DISTANCE_MATCH_RTOL,
                atol=0.0,
            )
        ):
            msg = (
                "RevisedNpdCurves: the increment must be taken at the distances "
                "of the curves it revises."
            )
            raise ValueError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the revised curves over the original ones against slant distance."""
        from .._i18n import check_language
        from .._plot.aircraft import plot_revised_npd_curves

        return plot_revised_npd_curves(
            self, ax=ax, language=check_language(language), **kwargs
        )


def revise_npd_curves(
    curves: AnpNpdCurves,
    spectrum: SpectralClass | ArrayLike,
    *,
    temperature_c: float,
    relative_humidity_percent: float,
    atmospheric_pressure_kpa: float = 101.325,
    absorption: str = "arp5534",
) -> RevisedNpdCurves:
    """NPD curves recalculated for a specified atmosphere (Doc 29 Vol. 2 Appendix D).

    Adds :func:`npd_atmosphere_increment`, taken at the curves' own distances,
    to the level of every power setting. The same increment applies to the
    ``Lmax`` and the ``LE`` curves of an operation, which assumes the
    atmosphere changes the reference spectrum and not the shape of the level
    time history (Appendix D, last paragraph of step 3).

    :param curves: The NPD curves, an
        :class:`~phonometry.aircraft.anp_fleet.AnpNpdCurves`.
    :param spectrum: The spectral class of the same aircraft and operation
        (see :meth:`~phonometry.aircraft.anp_fleet.AnpAircraft.spectral_class`).
    :param temperature_c: Air temperature, in degrees Celsius.
    :param relative_humidity_percent: Relative humidity, in percent.
    :param atmospheric_pressure_kpa: Air pressure, in kPa (default 101.325).
    :param absorption: ``"arp5534"`` (default) or ``"arp866a"``.
    :return: A :class:`RevisedNpdCurves`.
    :raises ValueError: as :func:`npd_atmosphere_increment` does.
    """
    increment = npd_atmosphere_increment(
        spectrum,
        temperature_c=temperature_c,
        relative_humidity_percent=relative_humidity_percent,
        atmospheric_pressure_kpa=atmospheric_pressure_kpa,
        absorption=absorption,
        distances_m=curves.distances,
    )
    levels = read_only(
        np.asarray(curves.levels, dtype=np.float64) + increment.increment_db[None, :]
    )
    return RevisedNpdCurves(
        original=curves,
        revised=dataclasses.replace(curves, levels=levels),
        increment=increment,
    )
