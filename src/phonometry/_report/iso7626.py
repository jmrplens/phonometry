#  Copyright (c) 2026. Jose Manuel Requena Plens
"""ISO 7626 mechanical-mobility fiche (reportlab renderer).

Renders a
:class:`~phonometry.vibration.structural.mechanical_mobility.MobilityResult` to a one-page
PDF laid out like a mechanical-mobility measurement report (ISO 7626-1:2011 for
the frequency-response-function definitions, ISO 7626-2:2015 for the
measurement):

* a title and the standard-basis line, naming whether the mobility is a
  driving-point FRF (response and force co-located) or a transfer FRF;
* an optional metadata header grid (client, manufacturer, the tested structure,
  test facility, instrumentation, date, temperature);
* a two-panel body with a compact table of the FRF's characteristic points on
  the left (the FRF type, the frequency range, the peak frequency, the peak
  mobility magnitude and the phase there) beside the mobility magnitude spectrum
  ``|Y(f)|`` drawn by the result's own ``plot(ax=...)``;
* a boxed representative value, the peak mobility ``|Y|`` and the frequency it
  occurs at (for a driving-point FRF this is a resonance, where ``|Y| = 1/c``
  measures the damping); and
* a footer identity/disclaimer block.

Mechanical mobility is a continuous frequency-response function over a fine
frequency axis, not an octave-band quantity, so the fiche presents it honestly
as a spectrum plot plus a small table of characteristic points; it carries no
per-band table and no pass/fail verdict (a mobility measurement is a
characterisation). The shared FRF skeleton lives in :mod:`._frf_fiche`; this
module only holds the mobility specifics. reportlab, matplotlib and svglib are
soft dependencies imported lazily (reportlab and svglib ship in the
``phonometry[report]`` extra, matplotlib in ``phonometry[plot]``); each is
guarded with an actionable :class:`ImportError`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from ._frf_fiche import frequency_range, frf_metadata_pairs, render_frf_fiche
from ._i18n import format_number, t

if TYPE_CHECKING:
    from ..vibration.structural.impact_mobility import ImpactMobilityResult
    from ..vibration.structural.mechanical_mobility import MobilityResult
    from .metadata import ReportMetadata

#: The mobility unit, m/(N.s), as reportlab markup (a middle dot, not a hyphen).
_MOBILITY_UNIT = "m/(N&#183;s)"


def _kind(result: MobilityResult, language: str = "en") -> str:
    """The FRF-type phrase: driving-point (i = j) or transfer."""
    key = "driving-point" if result.driving_point else "transfer"
    return t(key, language)


def _basis(result: MobilityResult, language: str = "en") -> str:
    """The standard-basis line naming the FRF type and the ISO 7626 parts."""
    return t(
        "Measurement of the {kind} mechanical mobility Y = v/F over frequency "
        "(ISO 7626-1:2011 frequency-response function; measurement per "
        "ISO 7626-2:2015).",
        language,
    ).format(kind=_kind(result, language))


def _peak(result: MobilityResult) -> tuple[int, float, float]:
    """Return the peak index, peak magnitude and peak frequency of ``|Y|``."""
    magnitude = np.asarray(result.magnitude, dtype=np.float64)
    index = int(np.argmax(magnitude))
    return index, float(magnitude[index]), float(result.frequencies[index])


def _sig(value: float, language: str = "en") -> str:
    """A magnitude to three significant figures (mobility spans many decades)."""
    from ._i18n import decimal_comma

    return decimal_comma(f"{value:.3g}", language)


def _deg(value_rad: float, language: str = "en") -> str:
    """A phase angle in degrees, to the nearest degree."""
    return format_number(np.degrees(value_rad), language, decimals=0)


def _metric_rows(result: MobilityResult, language: str = "en") -> list[tuple[str, str]]:
    """The characteristic points shown in the left-hand table.

    The FRF type, the measured frequency range, the peak (resonance for a
    driving-point FRF) frequency, the peak mobility magnitude and the phase of
    the mobility there (near zero at a driving-point resonance, where the
    mobility is real).
    """
    index, peak_mag, peak_freq = _peak(result)
    phase = float(np.asarray(result.phase, dtype=np.float64)[index])
    return [
        (t("FRF type", language), _kind(result, language)),
        (
            t("Frequency range f [Hz]", language),
            frequency_range(np.asarray(result.frequencies, dtype=np.float64), language),
        ),
        (
            t("Peak frequency f [Hz]", language),
            format_number(peak_freq, language, decimals=1),
        ),
        (
            t("Peak mobility |Y| [{unit}]", language).format(unit=_MOBILITY_UNIT),
            _sig(peak_mag, language),
        ),
        (t("Phase at peak [&#176;]", language), _deg(phase, language)),
    ]


def _statement(result: MobilityResult, language: str = "en") -> str:
    """The boxed representative value: the peak mobility and its frequency."""
    _, peak_mag, peak_freq = _peak(result)
    return t("Peak mobility |Y| = <b>{value} {unit}</b> at {freq} Hz", language).format(
        value=_sig(peak_mag, language),
        unit=_MOBILITY_UNIT,
        freq=format_number(peak_freq, language, decimals=1),
    )


def _extended_terms(result: MobilityResult, language: str = "en") -> list[str]:
    """The FRF type, the frequency range and the peak phase shown beside the box."""
    index, _, _ = _peak(result)
    phase = float(np.asarray(result.phase, dtype=np.float64)[index])
    return [
        t("FRF type: {kind}", language).format(kind=_kind(result, language)),
        t("Frequency range: {range} Hz", language).format(
            range=frequency_range(
                np.asarray(result.frequencies, dtype=np.float64), language
            )
        ),
        t("Phase at peak: {value}&#176;", language).format(value=_deg(phase, language)),
    ]


def render_mobility_report(
    result: MobilityResult,
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    verbose: bool = False,
    language: str = "en",
) -> str:
    """Render an ISO 7626 mechanical-mobility fiche to a PDF at ``path``.

    :param result: A
        :class:`~phonometry.vibration.structural.mechanical_mobility.MobilityResult`
        carrying the complex mobility ``Y(f)`` and whether it is a driving-point
        FRF.
    :param path: Destination path of the PDF file.
    :param metadata: Optional :class:`ReportMetadata`; ``None`` produces a
        body-and-disclaimer fiche. The ``requirement`` field is ignored (a
        mobility measurement is a characterisation, so there is no verdict).
    :param verbose: Accepted for a uniform ``.report()`` signature; the mobility
        fiche has a single body layout, so it has no effect.
    :param language: ``"en"`` (default) or ``"es"``.
    :return: The written ``path`` as a :class:`str`.
    :raises ImportError: If reportlab or matplotlib is not installed. The fiche
        always embeds the mobility spectrum, so both are required
        (``pip install "phonometry[report,plot]"``).
    """
    del verbose  # uniform signature; the mobility fiche has one body layout
    header_pairs = (
        frf_metadata_pairs(metadata, [], language)
        if metadata is not None and not metadata.is_empty()
        else []
    )
    return render_frf_fiche(
        result,
        path,
        title=t("Mechanical mobility measurement", language),
        basis=_basis(result, language),
        caption=t("Mobility FRF characteristics", language),
        header_pairs=header_pairs,
        metric_rows=_metric_rows(result, language),
        statement=_statement(result, language),
        extended=_extended_terms(result, language),
        metadata=metadata,
        language=language,
    )


def _impact_basis(result: ImpactMobilityResult, language: str = "en") -> str:
    """The standard-basis line of an impact measurement, naming ISO 7626-5."""
    kind = _kind(result.mobility_result, language)
    if result.impacts == 1:
        return t(
            "Measurement of the {kind} mechanical mobility Y = v/F by impact "
            "excitation, from a single impact (ISO 7626-5:2019; "
            "frequency-response function of ISO 7626-1:2011).",
            language,
        ).format(kind=kind)
    return t(
        "Measurement of the {kind} mechanical mobility Y = v/F by impact "
        "excitation, averaged over {n} impacts (ISO 7626-5:2019, 8.6; "
        "frequency-response function of ISO 7626-1:2011).",
        language,
    ).format(kind=kind, n=result.impacts)


def _window_reading(result: ImpactMobilityResult, language: str = "en") -> str:
    """The exponential window's decay rate, or the word for none."""
    if result.exponential_decay_rate_per_s > 0.0:
        return format_number(result.exponential_decay_rate_per_s, language, decimals=1)
    return t("none", language)


def _impact_rows(
    result: ImpactMobilityResult, language: str = "en"
) -> list[tuple[str, str]]:
    """The characteristic points of the mobility, then the impact specifics."""
    mobility = result.mobility_result
    index, _, _ = _peak(mobility)
    coherence = float(np.asarray(result.coherence, dtype=np.float64)[index])
    return [
        *_metric_rows(mobility, language),
        (t("Impacts averaged", language), str(result.impacts)),
        (t("Exponential window a [1/s]", language), _window_reading(result, language)),
        (
            t("Coherence at peak", language),
            format_number(coherence, language, decimals=3),
        ),
    ]


def _impact_extended(result: ImpactMobilityResult, language: str = "en") -> list[str]:
    """The extended terms, with the window's effect on the peaks stated."""
    terms = _extended_terms(result.mobility_result, language)
    if result.exponential_decay_rate_per_s > 0.0:
        terms.append(
            t(
                "Exponential window a = {a} 1/s: the peaks carry its damping "
                "(ISO 7626-5 Annex A)",
                language,
            ).format(a=_window_reading(result, language))
        )
    return terms


def render_impact_mobility_report(
    result: ImpactMobilityResult,
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    verbose: bool = False,
    language: str = "en",
) -> str:
    """Render the ISO 7626 fiche for a mobility measured by impact (ISO 7626-5).

    The layout of :func:`render_mobility_report`; the basis line names
    ISO 7626-5:2019 and the averaging of 8.6, and the table adds the number of
    impacts, the exponential window and the coherence at the peak.

    :param result: An
        :class:`~phonometry.vibration.structural.impact_mobility.ImpactMobilityResult`.
    :param path: Destination path of the PDF file.
    :param metadata: Optional :class:`ReportMetadata`.
    :param verbose: Accepted for a uniform ``.report()`` signature; no effect.
    :param language: ``"en"`` (default) or ``"es"``.
    :return: The written ``path`` as a :class:`str`.
    :raises ImportError: If reportlab or matplotlib is not installed.
    """
    del verbose  # uniform signature; the mobility fiche has one body layout
    header_pairs = (
        frf_metadata_pairs(metadata, [], language)
        if metadata is not None and not metadata.is_empty()
        else []
    )
    return render_frf_fiche(
        result,
        path,
        title=t("Mechanical mobility by impact excitation", language),
        basis=_impact_basis(result, language),
        caption=t("Mobility FRF characteristics", language),
        header_pairs=header_pairs,
        metric_rows=_impact_rows(result, language),
        statement=_statement(result.mobility_result, language),
        extended=_impact_extended(result, language),
        metadata=metadata,
        language=language,
    )
