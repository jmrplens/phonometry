#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""The acoustic roughness of a rail, measured directly on it (EN 15610:2009).

Rolling noise is excited by the unevenness of the wheel and rail running
surfaces, and the rail's share of it, its **acoustic roughness**
:math:`r(x)`, is the height of the running surface along the rail (3.1). EN
15610 measures it with a probe that follows a line on the rail head and turns
the record into a one-third octave band spectrum of wavelength, which is how
a test track is shown to be smooth enough for a vehicle type test (ISO 3095,
6.2.5, whose limit lives in
:data:`~phonometry.environment.sources.rolling_stock_noise.REFERENCE_TRACK_ROUGHNESS_LIMIT_DB`).

**Clause 7, the processing.** A record goes through three stages before its
spectrum is taken (7.1): the data of joints, welds and rail defects are edited
out by the operator (Annex A shows what is and is not a defect); narrow upward
spikes from particles on the rail are removed (7.2,
:func:`remove_roughness_spikes`); and every point is raised to where a wheel
of 0,375 m radius would stand on it, because the probe tip is far smaller than
a wheel and reaches into pits a wheel rolls over (7.3,
:func:`curvature_processed_roughness`).

**The spectrum.** Method A of 7.4.2 (:func:`acoustic_roughness_spectrum`)
cuts the record into segments at least 1 m long overlapping by half, removes
the mean and the linear trend of each, applies a Hanning window and averages
the squared magnitudes of their discrete Fourier transforms into a narrow band
spectrum. The one-third octave band value is the energy sum of the narrow
band lines, the two lines that straddle a band edge counted only for the
portion of their width inside the band (Annex C,
:func:`redistributed_band_energies`). The level is

.. math::

   L_r = 10 \lg \frac{r_\mathrm{RMS}^2}{r_0^2}\ \mathrm{dB}, \qquad r_0 = 1\ \mathrm{\mu m}

(3.3, Formula 1). A record of a given length only resolves wavelengths up to
a quarter of it (7.5), so a 1 m segment reports down to the 0,25 m band.

Method B of 7.4.3 (:func:`filtered_roughness_spectrum`) runs digital one-third
octave filters along the record itself and takes the mean square of each
band's output, once 2 m at either end have been discarded for the filter
transients; a record therefore needs at least 5 m (NOTE 1), and the records
of a line at least 15 m once those ends are gone. The filters "shall comply
with EN 61260", the 1995 edition the normative references date. The bank is
the library's own (:func:`roughness_filter_bank`, an
:class:`~phonometry.filters.OctaveFilterBank` running at so many samples per
metre): base-ten bands, the same ones Method A reports, of order 4
Butterworth sections, every band run at the record's own sampling rate, class
0 of EN 61260:1995 on its Table 1
(:func:`~phonometry.filters.verify_filter_class` with ``edition="1995"``, up
to the Nyquist wavenumber of the record), on the filter integrated response
of 4.5.3 and on the summation of outputs of 4.9.

**7.6, the average.** The spectra of the records of one line are averaged on
their mean squares, without weighting by where along the test section they
were taken (:func:`average_roughness_spectra`), and 6.4.3 sets how many lines
a rail needs by the width of its reference surface
(:func:`roughness_measurement_lines`). Clause 8 compares every average with the
limit and allows no band above it; that verdict, with the flexibility of ISO
3095 Annex C, is
:func:`~phonometry.environment.sources.rolling_stock_noise.check_reference_track`.

**Readings of the library.** The spike height :math:`h` of 7.2 is not
defined by the clause; it is read here, as the Annex B listing computes it, as
the height of the peak above the straight line the spike is replaced by. The
filters of Method B ring for a distance that grows with the wavelength of
their band, and 7.4.3 allows them 2 m to settle whatever the band: a band is
reported only when, over the length analysed, its filter has built up to
within 0,15 dB of its steady output, the class 0 tolerance of EN 61260:1995
4.5.3 on the integrated response. That is the reason for order 4, the lowest
whose bank is class 0: it settles soonest. The bank is not decimated band by
band, as the library's banks are by default: run at the record's own rate, a
band has no alias at all for 4.8 to bound, and what its response is graded on
up to the Nyquist wavenumber is exactly what a record goes through. The filters of the Annex B
listing do not comply with EN 61260 (see the errata register).

Read from BS EN 15610:2009, which is identical to EN 15610:2009 (its national
foreword).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from ..._internal.frozen import OwnsArrays, read_only
from ..._internal.validation import (
    require_choice,
    require_finite_array,
    require_positive,
)
from ._shared import _TOLERANCE

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Mapping, Sequence

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

    from ...filters import OctaveFilterBank

__all__ = [
    "AcousticRoughnessSpectrum",
    "acoustic_roughness_spectrum",
    "average_roughness_spectra",
    "curvature_processed_roughness",
    "filtered_roughness_spectrum",
    "redistributed_band_energies",
    "remove_roughness_spikes",
    "roughness_filter_bank",
    "roughness_measurement_lines",
]

#: 3.3: the reference roughness :math:`r_0` of the acoustic roughness level,
#: in micrometres.
_REFERENCE_ROUGHNESS_UM = 1.0

#: 7.2 c): a spike is where the second derivative falls below this, in
#: micrometres per square metre, with the first derivative changing sign.
_SPIKE_CURVATURE_UM_PER_M2 = -1.0e7

#: 7.2 d): the edges of a spike are where the magnitude of the first
#: derivative falls below this, in micrometres per metre.
_SPIKE_EDGE_SLOPE_UM_PER_M = 5.0e3

#: 7.2: the constant :math:`a` of the height criterion :math:`h > w^2/a`, in
#: metres.
_SPIKE_CRITERION_M = 3.0

#: 7.3: the radius of the circle the curvature processing rolls over the
#: record, in metres.
_CURVE_RADIUS_M = 0.375

#: 5.6 and 7.4.2: the shortest record, and the shortest segment a Fourier
#: transform may be taken over, in metres.
_MINIMUM_RECORD_M = 1.0

#: 5.5: the longest sampling interval, in metres.
_MAXIMUM_SAMPLING_INTERVAL_M = 1.0e-3

#: 7.5: a record resolves wavelengths up to this fraction of its length.
_RESOLVED_FRACTION = 0.25

#: 7.4.2: the overlap of successive segments.
_SEGMENT_OVERLAP = 0.5

#: 7.4.3: the length discarded at either end of a record after filtering, in
#: metres, "to remove the effects of filter transients".
_FILTER_TRANSIENT_M = 2.0

#: 7.4.3: the least length the records of one line must leave, in metres, once
#: the 2 m at either end of each have been discarded.
_MINIMUM_FILTERED_TOTAL_M = 15.0

#: The order of the Butterworth band filters of Method B: the lowest whose
#: bank, run at the record's own rate, is class 0 of EN 61260:1995 on Table 1,
#: 4.5.3 and 4.9 (order 3 misses Table 1 in the bands near the Nyquist
#: wavenumber), and the one that settles soonest inside the 2 m 7.4.3 allows
#: for it.
_FILTER_ORDER = 4

#: EN 61260:1995 4.5.3: the class 0 limit on the filter integrated response,
#: in decibels. A Method B band is reported only when the transient left after
#: the 2 m discarded moves its level by no more than this.
_SETTLING_TOLERANCE_DB = 0.15

#: Annex B, B.9.2: the longest wavelength the listing filters (``wl_max``),
#: in metres, the default reach of :func:`roughness_filter_bank`.
_LISTING_LONGEST_WAVELENGTH_M = 0.5

#: The labels of the two spectral analyses of 7.4.
_METHODS = ("A", "B")

#: 6.4.3: the reference widths, in millimetres, above which three lines are
#: measured 5 mm apart and then 10 mm apart.
_LINE_WIDTHS_MM = (20.0, 30.0)

#: The preferred numbers of the R10 series (ISO 3), the mantissas of the
#: nominal one-third octave wavelengths EN 15610 clause 9 labels its graphs
#: with (the preferred frequencies of EN ISO 266, read as wavelengths).
_R10 = (1.0, 1.25, 1.6, 2.0, 2.5, 3.15, 4.0, 5.0, 6.3, 8.0)

#: Half the width of a base-ten one-third octave band, as a power of ten:
#: the band edges lie :math:`10^{\pm 1/20}` either side of the centre.
_HALF_BAND_DECADES = 0.05


def _nominal_wavelength_m(band: int) -> float:
    """The nominal wavelength of wavenumber band ``band``, in metres.

    Band ``k`` is centred on the wavenumber :math:`10^{k/10}` per metre; its
    nominal wavelength is the R10 preferred number nearest :math:`10^{-k/10}`,
    so band 4 is 0,4 m and band 25 is 3,15 mm.
    """
    mantissa = (-band) % 10
    exponent = (-band - mantissa) // 10
    value = _R10[mantissa]
    return value * 10.0**exponent if exponent >= 0 else value / 10.0 ** (-exponent)


def _band_of_wavelength(wavelength_m: float) -> int:
    """The index of the one-third octave band a nominal wavelength names."""
    return round(-10.0 * math.log10(wavelength_m))


def _band_edges(
    bands: NDArray[np.int64],
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Lower and upper wavenumber edges of base-ten bands, in cycles per metre."""
    centre = 10.0 ** (bands / 10.0)
    ratio = 10.0**_HALF_BAND_DECADES
    return centre / ratio, centre * ratio


def _record(
    roughness_um: ArrayLike, sample_spacing_m: float
) -> tuple[NDArray[np.float64], float]:
    """Validate a roughness record and its sampling interval."""
    record = require_finite_array(roughness_um, "roughness_um")
    spacing = require_positive(sample_spacing_m, "sample_spacing_m")
    minimum_samples = 3
    if record.size < minimum_samples:
        msg = "'roughness_um' needs at least three samples to have a derivative."
        raise ValueError(msg)
    return record, spacing


def _derivatives(
    record: NDArray[np.float64], spacing: float
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """First and second derivatives by central differences.

    As the Annex B listing takes them: the end values of the first derivative
    repeat their neighbours and the second derivative is zero at the ends.
    """
    first = np.empty_like(record)
    first[1:-1] = (record[2:] - record[:-2]) / (2.0 * spacing)
    first[0] = first[1]
    first[-1] = first[-2]
    second = np.zeros_like(record)
    second[1:-1] = (record[:-2] - 2.0 * record[1:-1] + record[2:]) / spacing**2
    return first, second


def _spike_edges(first: NDArray[np.float64], centre: int) -> tuple[int, int]:
    """The samples either side of a spike where the slope has flattened (7.2 d)."""
    left = 1
    while centre - left > 0 and abs(first[centre - left]) >= _SPIKE_EDGE_SLOPE_UM_PER_M:
        left += 1
    right = 1
    last = first.size - 1
    while (
        centre + right < last
        and abs(first[centre + right]) >= _SPIKE_EDGE_SLOPE_UM_PER_M
    ):
        right += 1
    return centre - left, centre + right


def _remove_one_pass(record: NDArray[np.float64], spacing: float) -> int:
    """Remove, in place, every spike one sweep of 7.2 finds; return how many."""
    removed = 0
    first, second = _derivatives(record, spacing)
    for centre in range(1, record.size - 1):
        if second[centre] >= _SPIKE_CURVATURE_UM_PER_M2:
            continue
        if int(np.sign(first[centre - 1])) == int(np.sign(first[centre + 1])):
            continue
        start, stop = _spike_edges(first, centre)
        width_m = (stop - start) * spacing
        chord = record[start] + (record[stop] - record[start]) * (
            (centre - start) / (stop - start)
        )
        height_m = (record[centre] - chord) * 1.0e-6
        if height_m > width_m**2 / _SPIKE_CRITERION_M:
            record[start : stop + 1] = np.linspace(
                record[start], record[stop], stop - start + 1
            )
            removed += 1
            first, second = _derivatives(record, spacing)
    return removed


def remove_roughness_spikes(
    roughness_um: ArrayLike, *, sample_spacing_m: float
) -> NDArray[np.float64]:
    r"""The record with its narrow upward spikes replaced by straight lines (7.2).

    A spike is a sample where the second derivative of the roughness falls
    below :math:`-10^7\ \mathrm{\mu m/m^2}` and the first derivative changes
    sign; its edges are the samples either side of it where the magnitude of
    the first derivative falls below :math:`5 \times 10^3\ \mathrm{\mu m/m}`,
    and its width :math:`w` is the distance between them. It is removed, by
    linear interpolation between its edges, when its height :math:`h` above
    that line satisfies

    .. math::

       h > \frac{w^2}{a}, \qquad a = 3\ \mathrm{m},

    with :math:`h` and :math:`w` in metres, and the procedure is repeated
    until a sweep removes nothing. A narrow peak is taken for a particle of
    dirt; a broad one is roughness a wheel does feel, and stays.

    The derivatives are central differences, as in the Annex B listing. That
    listing repeats its sweep while any second derivative is below the
    threshold, change of sign or not, which never ends on a sharp bend with
    no extremum nor on a sharp peak the height test keeps; the sweep here
    stops when a pass removes no spike, which is what "until no further spike
    is detected" can mean for a peak that is detected and kept.

    :param roughness_um: The roughness record :math:`r(x)`, in micrometres,
        sampled at equal intervals, with joints, welds and defects already
        edited out (7.1 a) 1)).
    :param sample_spacing_m: The sampling interval, in metres.
    :return: A new array, the record with the spikes removed, in micrometres.
    :raises ValueError: For a record that is not a finite one-dimensional
        array of at least three samples, or a spacing that is not positive.
    """
    record, spacing = _record(roughness_um, sample_spacing_m)
    processed = record.copy()
    removed = _remove_one_pass(processed, spacing)
    while removed:
        removed = _remove_one_pass(processed, spacing)
    return processed


def curvature_processed_roughness(
    roughness_um: ArrayLike,
    *,
    sample_spacing_m: float,
    curve_radius_m: float = _CURVE_RADIUS_M,
) -> NDArray[np.float64]:
    r"""The record as a wheel of radius 0,375 m would ride it (7.3).

    At every sample :math:`x_i` a circle :math:`C_i(x)` of radius
    :math:`R` passes through :math:`r(x_i)` with its centre above the
    record, and the point is raised by the largest amount the record stands
    above that circle:

    .. math::

       r'(x_i) = \max_x \left[ r(x) - C_i(x) \right] + r(x_i)
               = \max_x \left[ r(x) - \left( R - \sqrt{R^2 - (x - x_i)^2}
                 \right) \right].

    A pit narrower than the circle is bridged at the height where the circle
    rests on its rims; a crest is unchanged, since the circle through it lies
    above its flanks. Only the samples whose circle height is within the range
    of the record can win the maximum, so the search is limited to them.

    :param roughness_um: The roughness record, in micrometres, usually after
        :func:`remove_roughness_spikes`.
    :param sample_spacing_m: The sampling interval, in metres.
    :param curve_radius_m: The radius :math:`R` of the circle, in metres; the
        0,375 m of 7.3 by default.
    :return: A new array :math:`r'(x)`, in micrometres.
    :raises ValueError: For an invalid record, spacing or radius.
    """
    record, spacing = _record(roughness_um, sample_spacing_m)
    radius_um = require_positive(curve_radius_m, "curve_radius_m") * 1.0e6
    spacing_um = spacing * 1.0e6
    span_um = float(np.ptp(record))
    # Beyond the offset where the circle has risen by the whole range of the
    # record, no sample can stand above it any more.
    reach_um = (
        radius_um
        if span_um >= radius_um
        else math.sqrt(span_um * (2.0 * radius_um - span_um))
    )
    offsets = int(math.ceil(reach_um / spacing_um)) + 1
    offsets = min(offsets, record.size - 1)
    processed = record.copy()
    for offset in range(1, offsets + 1):
        distance_um = offset * spacing_um
        if distance_um >= radius_um:
            break
        lift = radius_um - math.sqrt(radius_um**2 - distance_um**2)
        # The neighbour ``offset`` samples ahead and the one behind.
        np.maximum(processed[:-offset], record[offset:] - lift, out=processed[:-offset])
        np.maximum(processed[offset:], record[:-offset] - lift, out=processed[offset:])
    return processed


def redistributed_band_energies(
    source_lower: ArrayLike,
    source_upper: ArrayLike,
    energies: ArrayLike,
    target_lower: ArrayLike,
    target_upper: ArrayLike,
) -> NDArray[np.float64]:
    r"""Band energies moved onto other bands in proportion to their overlap (Annex C).

    EN 15610 Annex C builds a one-third octave band from narrow band lines of
    width :math:`\gamma`: every line wholly inside the band counts in full and
    the two lines that straddle its edges count for the portions
    :math:`\gamma_1` and :math:`\gamma_{n_k}` of their width that lie inside
    it,

    .. math::

       L_k = 10 \lg \left[ \frac{\gamma_1}{\gamma} S_1
             + \sum_{j=2}^{n_k - 1} S_j
             + \frac{\gamma_{n_k}}{\gamma} S_{n_k} \right]

    (Formula C.1). Written for source bands of any width, that is the energy of
    each source band shared among the target bands in proportion to how much
    of its width, on the linear axis, each target band covers, which is the
    form ISO 3095 Annex C asks for when the bands being shared are one-third
    octaves of wavelength carried onto frequency ("adapted to non-constant
    frequency bandwidths"). The energy of a source band outside every target
    band is dropped.

    :param source_lower: Lower edges of the source bands, on any linear axis
        (hertz, cycles per metre).
    :param source_upper: Their upper edges, on the same axis.
    :param energies: The energy of each source band: a mean square, not a
        level.
    :param target_lower: Lower edges of the target bands, on the same axis.
    :param target_upper: Their upper edges.
    :return: The energy of each target band.
    :raises ValueError: For edges that are not finite, not increasing within
        a band or not one per band, or a negative energy.
    """
    s_lo = require_finite_array(source_lower, "source_lower")
    s_hi = require_finite_array(source_upper, "source_upper")
    energy = require_finite_array(energies, "energies")
    t_lo = require_finite_array(target_lower, "target_lower")
    t_hi = require_finite_array(target_upper, "target_upper")
    if not s_lo.size == s_hi.size == energy.size or t_lo.size != t_hi.size:
        msg = "every band needs one lower edge, one upper edge and, for a source, one energy."
        raise ValueError(msg)
    if np.any(s_hi <= s_lo) or np.any(t_hi <= t_lo):
        msg = "every band's upper edge must lie above its lower edge."
        raise ValueError(msg)
    if np.any(energy < 0.0):
        msg = "'energies' are mean squares and cannot be negative."
        raise ValueError(msg)
    overlap = np.clip(
        np.minimum(s_hi[:, None], t_hi[None, :])
        - np.maximum(s_lo[:, None], t_lo[None, :]),
        0.0,
        None,
    )
    share = overlap / (s_hi - s_lo)[:, None]
    return np.asarray(energy @ share, dtype=np.float64)


@dataclass(frozen=True)
class AcousticRoughnessSpectrum(OwnsArrays):
    r"""A one-third octave band spectrum of acoustic rail roughness (EN 15610).

    Built by :func:`acoustic_roughness_spectrum` (Method A) or
    :func:`filtered_roughness_spectrum` (Method B) from a record, by
    :func:`average_roughness_spectra` from several, or directly from the band
    levels of a report, which is all the ISO 3095 checks need.

    :param wavelengths_m: The nominal band wavelengths, in metres, from the
        longest to the shortest as clause 9 draws them; each names the
        base-ten one-third octave band of wavenumber it is nominal for.
    :param levels_db: The acoustic roughness level :math:`L_r` of each band,
        dB re 1 µm.
    :param record_length_m: The length of roughness the spectrum was taken
        from, in metres: for Method B, what is left once the 2 m at either
        end of each record have been discarded (7.4.3); ``None`` when not
        known.
    :param segment_count: How many Fourier segments were averaged into it;
        ``None`` when not known, and for Method B, which has none.
    :param method: ``"A"`` for the Fourier analysis of 7.4.2, ``"B"`` for the
        digital filters of 7.4.3; ``None`` when not known or when an average
        mixes the two.
    """

    wavelengths_m: NDArray[np.float64]
    levels_db: NDArray[np.float64]
    record_length_m: float | None = None
    segment_count: int | None = None
    method: str | None = None

    def __post_init__(self) -> None:
        """Hold the bands as read-only arrays, one level per band, longest first.

        :raises ValueError: For wavelengths that are not positive, levels
            that are not finite, arrays of different lengths, bands that are
            not in decreasing order of wavelength, or a method that is
            neither ``"A"`` nor ``"B"``.
        """
        from ..._internal.validation import require_positive_array

        if self.method is not None:
            require_choice(self.method, "method", _METHODS)
        wavelengths = require_positive_array(self.wavelengths_m, "wavelengths_m")
        levels = require_finite_array(self.levels_db, "levels_db")
        if wavelengths.size != levels.size:
            msg = "'wavelengths_m' and 'levels_db' need one value per band each."
            raise ValueError(msg)
        bands = np.array([_band_of_wavelength(w) for w in wavelengths])
        if np.any(np.diff(bands) <= 0):
            msg = "'wavelengths_m' must name distinct bands from the longest wavelength down."
            raise ValueError(msg)
        object.__setattr__(self, "wavelengths_m", read_only(wavelengths))
        object.__setattr__(self, "levels_db", read_only(levels))

    @property
    def bands(self) -> tuple[int, ...]:
        r"""The band index :math:`k` of each wavelength, centred on :math:`10^{k/10}` per metre."""
        return tuple(_band_of_wavelength(float(w)) for w in self.wavelengths_m)

    def level_at(self, wavelength_m: float) -> float:
        """The level of the band a nominal wavelength names, dB re 1 µm.

        :param wavelength_m: A nominal band wavelength, in metres.
        :return: The level of that band.
        :raises KeyError: If the spectrum has no such band.
        """
        band = _band_of_wavelength(require_positive(wavelength_m, "wavelength_m"))
        try:
            index = self.bands.index(band)
        except ValueError:
            msg = f"the spectrum has no band at {wavelength_m:g} m."
            raise KeyError(msg) from None
        return float(self.levels_db[index])

    def plot(
        self,
        ax: Axes | None = None,
        *,
        limit_db: Mapping[float, float] | None = None,
        language: str = "en",
        **kwargs: Any,
    ) -> Axes:
        """Draw the spectrum as EN 15610 clause 9 presents it.

        Level against wavelength in decreasing order, one octave to 10 dB, with
        a limit curve when one is given.

        :param ax: Axes to draw on; a new figure is made when omitted.
        :param limit_db: A limit spectrum to draw with it, nominal wavelength
            in metres to level, such as
            :data:`~phonometry.environment.sources.rolling_stock_noise.REFERENCE_TRACK_ROUGHNESS_LIMIT_DB`.
        :param language: ``"en"`` or ``"es"``.
        :param kwargs: Passed to the spectrum line.
        :return: The axes drawn on.
        """
        from ..._i18n import check_language
        from ..._plot.rolling_stock import plot_roughness_spectrum

        check_language(language)
        return plot_roughness_spectrum(
            self, ax, limit_db=limit_db, language=language, **kwargs
        )


def _require_sampling_interval(spacing: float) -> None:
    """Refuse a sampling interval above the 1 mm of 5.5."""
    if spacing > _MAXIMUM_SAMPLING_INTERVAL_M * (1.0 + _TOLERANCE):
        msg = f"'sample_spacing_m' is {spacing:g} m; 5.5 asks for 1 mm or less."
        raise ValueError(msg)


def _longest_resolved_band(length_m: float) -> int:
    """The longest band whose nominal wavelength is at most a quarter of ``length_m`` (7.5)."""
    reach = length_m * _RESOLVED_FRACTION
    band = _band_of_wavelength(reach)
    if _nominal_wavelength_m(band) > reach * (1.0 + _TOLERANCE):
        band += 1
    return band


def _shortest_band(rate_per_m: float) -> int:
    """The shortest band whose upper edge lies below the Nyquist wavenumber."""
    return int(math.floor(10.0 * (math.log10(rate_per_m / 2.0) - _HALF_BAND_DECADES)))


def _segments(record: NDArray[np.float64], samples: int) -> NDArray[np.float64]:
    """The segments of 7.4.2, overlapping by half, one per row."""
    step = max(1, int(round(samples * (1.0 - _SEGMENT_OVERLAP))))
    starts = range(0, record.size - samples + 1, step)
    return np.stack([record[start : start + samples] for start in starts])


def acoustic_roughness_spectrum(
    roughness_um: ArrayLike,
    *,
    sample_spacing_m: float,
    spike_removal: bool = True,
    curvature_processing: bool = True,
    segment_length_m: float = _MINIMUM_RECORD_M,
) -> AcousticRoughnessSpectrum:
    r"""The one-third octave band acoustic roughness of a record (7.2 to 7.4, Method A).

    The record is processed as 7.1 asks, spikes first
    (:func:`remove_roughness_spikes`) and curvature next
    (:func:`curvature_processed_roughness`), then cut into segments of
    ``segment_length_m`` overlapping by half. Each has its mean and linear
    trend removed and a Hanning window applied; the squared magnitudes of
    their discrete Fourier transforms are averaged into a one-sided spectral
    density normalised by the window's energy, so that its sum over the lines
    is the mean square of the roughness. Each one-third octave band of
    wavenumber then collects the lines within it and the portions of the two
    straddling its edges (Annex C, :func:`redistributed_band_energies`), and
    the level is :math:`10 \lg (r^2_\mathrm{RMS} / r_0^2)` with
    :math:`r_0 = 1\ \mathrm{\mu m}` (Formula 1).

    The bands reported are those whose nominal wavelength is at most a
    quarter of the segment length (7.5) and whose upper edge lies below the
    Nyquist wavenumber of the sampling.

    :param roughness_um: The roughness record, in micrometres, at equal
        intervals, with joints, welds and defects already edited out.
    :param sample_spacing_m: The sampling interval, in metres; 5.5 asks for
        1 mm or less.
    :param spike_removal: Whether to apply 7.2 first.
    :param curvature_processing: Whether to apply 7.3 next.
    :param segment_length_m: The length of each Fourier segment, in metres;
        at least 1 m (7.4.2).
    :return: The spectrum, longest wavelength first, with the record length
        and the number of segments averaged.
    :raises ValueError: For a sampling interval above 1 mm, a segment shorter
        than 1 m, or a record shorter than one segment.
    """
    record, spacing = _record(roughness_um, sample_spacing_m)
    _require_sampling_interval(spacing)
    segment_m = require_positive(segment_length_m, "segment_length_m")
    if segment_m < _MINIMUM_RECORD_M * (1.0 - _TOLERANCE):
        msg = f"'segment_length_m' is {segment_m:g} m; 7.4.2 asks for at least 1 m."
        raise ValueError(msg)
    samples = int(round(segment_m / spacing))
    if samples > record.size:
        msg = (
            f"the record is {record.size * spacing:g} m long, shorter than one "
            f"{segment_m:g} m segment; 5.6 asks for records of at least 1 m."
        )
        raise ValueError(msg)
    if spike_removal:
        record = remove_roughness_spikes(record, sample_spacing_m=spacing)
    if curvature_processing:
        record = curvature_processed_roughness(record, sample_spacing_m=spacing)
    from scipy.signal import detrend
    from scipy.signal.windows import hann

    segments = detrend(_segments(record, samples), axis=1, type="linear")
    window = hann(samples, sym=False)
    spectra = np.abs(np.fft.rfft(segments * window, axis=1)) ** 2
    rate = 1.0 / spacing
    density = spectra.mean(axis=0) / (rate * float(np.sum(window**2)))
    density[1:] *= 2.0
    if samples % 2 == 0:
        density[-1] /= 2.0
    line_width = 1.0 / (samples * spacing)
    wavenumbers = np.arange(density.size) * line_width
    line_energy = density[1:] * line_width
    bands = np.arange(_longest_resolved_band(segment_m), _shortest_band(rate) + 1)
    if bands.size == 0:
        msg = "the segment and the sampling interval leave no whole band between them."
        raise ValueError(msg)
    lower, upper = _band_edges(bands)
    energies = redistributed_band_energies(
        wavenumbers[1:] - line_width / 2.0,
        wavenumbers[1:] + line_width / 2.0,
        line_energy,
        lower,
        upper,
    )
    floor = np.finfo(np.float64).tiny
    levels = 10.0 * np.log10(np.maximum(energies, floor) / _REFERENCE_ROUGHNESS_UM**2)
    return AcousticRoughnessSpectrum(
        wavelengths_m=np.array([_nominal_wavelength_m(int(b)) for b in bands]),
        levels_db=levels,
        record_length_m=float(record.size * spacing),
        segment_count=int(segments.shape[0]),
        method="A",
    )


def _samples_per_metre(spacing: float) -> int:
    """The sampling rate of a record, which the filter bank needs whole."""
    rate = round(1.0 / spacing)
    if rate < 1 or not math.isclose(rate, 1.0 / spacing, rel_tol=_TOLERANCE):
        msg = (
            f"'sample_spacing_m' is {spacing:g} m, which is not a whole number of "
            "samples per metre; the one-third octave filter bank of Method B runs "
            "at a whole number of them."
        )
        raise ValueError(msg)
    return int(rate)


def roughness_filter_bank(
    *,
    sample_spacing_m: float,
    longest_wavelength_m: float = _LISTING_LONGEST_WAVELENGTH_M,
) -> OctaveFilterBank:
    r"""The one-third octave filters Method B runs along a record (7.4.3).

    7.4.3 asks for digital one-third octave band filters that "shall comply
    with EN 61260", the 1995 edition (IEC 61260:1995) the normative
    references of EN 15610:2009 date. This is the library's own bank,
    :class:`~phonometry.filters.OctaveFilterBank`, run with the record's
    samples per metre for a sample rate, so that its frequencies are
    wavenumbers in cycles per metre: base-ten bands centred on
    :math:`10^{k/10}` per metre, the bands Method A reports, of order 4
    Butterworth sections, every band run at the record's own rate.
    Passed to :func:`~phonometry.filters.verify_filter_class` with
    ``edition="1995"`` it grades class 0 on Table 1 of EN 61260:1995 in every
    band, from the lowest wavenumbers up to the Nyquist wavenumber of the
    record, and its filter integrated response (4.5.3) and summation of
    outputs (4.9) are within the class 0 limits too. Order 4 is the lowest
    that is class 0, and the lowest settles soonest inside the 2 m 7.4.3
    discards for the filter transients.

    The bank is designed without the band-by-band decimation the library's
    banks use by default (``FilterDesign(resample=False)``). At the record's
    own rate a band has no alias at all for 4.8 to bound, and what the grade
    reads is exactly what a record goes through.

    :param sample_spacing_m: The sampling interval of the records, in metres;
        5.5 asks for 1 mm or less, and the bank needs a whole number of
        samples per metre.
    :param longest_wavelength_m: The longest band the bank holds, by its
        nominal wavelength, in metres; 0,5 m by default, where the Annex B
        listing stops (``wl_max``). The bank runs from that band to the
        shortest whose upper edge lies below the Nyquist wavenumber.
    :return: The filter bank.
    :raises ValueError: For a sampling interval above 1 mm or that is not a
        whole number of samples per metre, or a longest wavelength that leaves
        no band above the Nyquist band.
    """
    spacing = require_positive(sample_spacing_m, "sample_spacing_m")
    _require_sampling_interval(spacing)
    rate = _samples_per_metre(spacing)
    longest = require_positive(longest_wavelength_m, "longest_wavelength_m")
    first = _band_of_wavelength(longest)
    if _nominal_wavelength_m(first) > longest * (1.0 + _TOLERANCE):
        first += 1
    last = _shortest_band(rate)
    if first > last:
        msg = (
            f"no one-third octave band lies between {longest:g} m and the "
            f"Nyquist wavenumber of {rate / 2.0:g} per metre."
        )
        raise ValueError(msg)
    from ...filters import FilterDesign, OctaveFilterBank

    return OctaveFilterBank(
        rate,
        fraction=3,
        order=_FILTER_ORDER,
        limits=[10.0 ** (first / 10.0), 10.0 ** (last / 10.0)],
        design=FilterDesign(resample=False),
    )


def _settling_deficit_db(
    bank: OctaveFilterBank, index: int, start: int, stop: int
) -> float:
    r"""How far a band reads below its steady level over the samples analysed.

    A filter switched on at the start of a record builds its output up as
    the energy of its impulse response accumulates: for an input that is
    steady across the band, the mean square at :math:`x` is the steady one
    times :math:`E(x)/E(\infty)`, :math:`E` the running energy of the
    impulse response. The deficit is that ratio averaged over the samples
    from ``start`` to ``stop`` of the record, in decibels, computed on the
    band's sections at the rate the bank runs them at.
    """
    from scipy.signal import sosfilt

    factor = int(bank.factor[index])
    first = math.ceil(start / factor)
    last = max(first + 1, math.ceil(stop / factor))
    length = max(last, 64)
    # Double the impulse response until its second half carries nothing
    # measurable; a stable filter's tail falls geometrically after that.
    doublings = 24
    for _ in range(doublings):
        impulse = np.zeros(length)
        impulse[0] = 1.0
        energy = np.cumsum(sosfilt(bank.sos[index], impulse) ** 2)
        if energy[-1] - energy[length // 2] <= 1.0e-12 * energy[-1]:
            break
        length *= 2
    built = energy[first:last] / energy[-1]
    return float(10.0 * np.log10(np.mean(built)))


def filtered_roughness_spectrum(
    roughness_um: ArrayLike,
    *,
    sample_spacing_m: float,
    spike_removal: bool = True,
    curvature_processing: bool = True,
) -> AcousticRoughnessSpectrum:
    r"""The one-third octave band acoustic roughness of a record by digital filters (7.4.3, Method B).

    The record is processed as 7.1 asks, spikes first
    (:func:`remove_roughness_spikes`) and curvature next
    (:func:`curvature_processed_roughness`), and its mean and linear trend
    are removed, as the Annex B listing does before either analysis. It then
    runs through the one-third octave filters of
    :func:`roughness_filter_bank`, and 2 m of every band's output are
    discarded at either end "to remove the effects of filter transients"
    (7.4.3). The band level is the mean square of what is left,
    :math:`L_r = 10 \lg (r_\mathrm{RMS}^2 / r_0^2)` with
    :math:`r_0 = 1\ \mathrm{\mu m}` (Formula 1).

    The bands reported are those whose nominal wavelength is at most a
    quarter of the length analysed (7.5) and whose filter, over that length,
    has built up to within 0,15 dB of its steady output, the class 0
    tolerance of EN 61260:1995 4.5.3; the longest bands ring on past the 2 m
    allowed and are left out until the record is long enough to dilute what
    is left of their transient. A 5 m record reports from the 0,25 m band
    down, a 19 m one from the 0,5 m band, and the shortest band is the one
    whose upper edge lies below the Nyquist wavenumber.

    :param roughness_um: The roughness record, in micrometres, at equal
        intervals, with joints, welds and defects already edited out.
    :param sample_spacing_m: The sampling interval, in metres; 5.5 asks for
        1 mm or less, and the filter bank needs a whole number of samples per
        metre.
    :param spike_removal: Whether to apply 7.2 first.
    :param curvature_processing: Whether to apply 7.3 next.
    :return: The spectrum, longest wavelength first, with the length
        analysed (the record less 2 m at either end) as its record length and
        ``"B"`` as its method. The records of one line need at least 15 m
        analysed in total (7.4.3), which
        :func:`~phonometry.environment.sources.rolling_stock_noise.check_reference_track`
        judges on their average.
    :raises ValueError: For a sampling interval above 1 mm or that is not a
        whole number of samples per metre, or a record shorter than 5 m
        (7.4.3 NOTE 1: 1 m left once 2 m are discarded at either end).
    """
    record, spacing = _record(roughness_um, sample_spacing_m)
    _require_sampling_interval(spacing)
    rate = _samples_per_metre(spacing)
    discard = round(_FILTER_TRANSIENT_M * rate)
    analysed = record.size - 2 * discard
    minimum = round(_MINIMUM_RECORD_M * rate)
    if analysed < minimum:
        msg = (
            f"the record is {record.size * spacing:g} m long; 7.4.3 discards 2 m "
            "at either end and NOTE 1 asks for at least 5 m, leaving 1 m."
        )
        raise ValueError(msg)
    if spike_removal:
        record = remove_roughness_spikes(record, sample_spacing_m=spacing)
    if curvature_processing:
        record = curvature_processed_roughness(record, sample_spacing_m=spacing)
    from scipy.signal import detrend

    record = detrend(record, type="linear")
    analysed_m = analysed / rate
    stop = discard + analysed
    # Every band 7.5 allows, designed but not run; from the shortest up, the
    # bands whose filter settles within tolerance over the stretch analysed.
    candidates = roughness_filter_bank(
        sample_spacing_m=spacing,
        longest_wavelength_m=_nominal_wavelength_m(_longest_resolved_band(analysed_m)),
    )
    settled = 0
    for index in range(candidates.num_bands - 1, -1, -1):
        deficit = _settling_deficit_db(candidates, index, discard, stop)
        if abs(deficit) > _SETTLING_TOLERANCE_DB:
            break
        settled += 1
    if not settled:
        msg = "no band of the filter bank settles within the length analysed."
        raise ValueError(msg)
    first = round(10.0 * math.log10(float(candidates.freq[-settled])))
    bank = roughness_filter_bank(
        sample_spacing_m=spacing, longest_wavelength_m=_nominal_wavelength_m(first)
    )
    outputs = bank.filter(
        record, sigbands=True, calculate_level=False, detrend=False
    ).require_bands()
    levels = []
    for output in outputs:
        band = np.asarray(output, dtype=np.float64)[discard:stop]
        mean_square = max(float(np.mean(band**2)), np.finfo(np.float64).tiny)
        levels.append(10.0 * math.log10(mean_square / _REFERENCE_ROUGHNESS_UM**2))
    bands = [round(10.0 * math.log10(float(f))) for f in bank.freq]
    return AcousticRoughnessSpectrum(
        wavelengths_m=np.array([_nominal_wavelength_m(b) for b in bands]),
        levels_db=np.asarray(levels),
        record_length_m=float(analysed_m),
        segment_count=None,
        method="B",
    )


def average_roughness_spectra(
    spectra: Sequence[AcousticRoughnessSpectrum],
) -> AcousticRoughnessSpectrum:
    r"""The mean square average of roughness spectra of one line (7.6).

    .. math::

       L_r = 10 \lg \left( \frac{1}{N} \sum_{n=1}^{N} 10^{L_{r,n}/10} \right)

    band by band, with no weighting for where along the test section each
    record was taken. ISO 3095 C.2.1 averages the spectra of a test section
    the same way ("quadratically averaged") before comparing them with the
    limit. Only the bands every spectrum has are averaged.

    :param spectra: The spectra to average.
    :return: The average, with the record lengths and segment counts summed
        when every spectrum carries them, and the method of the spectra when
        they all share one.
    :raises ValueError: For no spectrum, or spectra with no band in common.
    """
    if not spectra:
        msg = "'spectra' holds no spectrum to average."
        raise ValueError(msg)
    common = set(spectra[0].bands)
    for spectrum in spectra[1:]:
        common &= set(spectrum.bands)
    if not common:
        msg = "the spectra have no band in common."
        raise ValueError(msg)
    bands = sorted(common)
    energies = np.zeros(len(bands))
    for spectrum in spectra:
        index = {band: i for i, band in enumerate(spectrum.bands)}
        energies += np.array(
            [10.0 ** (spectrum.levels_db[index[b]] / 10.0) for b in bands]
        )
    levels = 10.0 * np.log10(energies / len(spectra))
    lengths = [s.record_length_m for s in spectra]
    counts = [s.segment_count for s in spectra]
    methods = {s.method for s in spectra}
    return AcousticRoughnessSpectrum(
        wavelengths_m=np.array([_nominal_wavelength_m(b) for b in bands]),
        levels_db=levels,
        record_length_m=None
        if None in lengths
        else float(sum(x for x in lengths if x is not None)),
        segment_count=None
        if None in counts
        else int(sum(c for c in counts if c is not None)),
        method=methods.pop() if len(methods) == 1 else None,
    )


def roughness_measurement_lines(reference_width_mm: float) -> tuple[int, float]:
    r"""How many parallel lines a rail's reference surface is measured on (6.4.3).

    Up to 20 mm wide, one line on the centre line of the reference surface;
    above 20 mm and up to 30 mm, three lines 5 mm apart; above 30 mm, three
    lines 10 mm apart. More lines may be measured, but those compared with the
    acceptance criteria follow this rule (6.4.3 NOTE).

    :param reference_width_mm: The width :math:`w_\mathrm{ref}` of the
        reference surface, in millimetres.
    :return: The number of lines and the distance between neighbouring lines,
        in millimetres (0 for a single line).
    :raises ValueError: For a width that is not positive.
    """
    width = require_positive(reference_width_mm, "reference_width_mm")
    narrow, wide = _LINE_WIDTHS_MM
    if width <= narrow:
        return 1, 0.0
    if width <= wide:
        return 3, 5.0
    return 3, 10.0
