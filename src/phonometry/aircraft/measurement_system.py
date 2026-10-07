#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Aircraft-noise measurement-system tolerances (IEC 61265:1995).

The certification levels of :mod:`phonometry.aircraft.certification` are only
worth what the chain that measured them is, and IEC 61265 is the standard that
says how good that chain has to be: microphone directional response, overall
frequency response, level linearity and the resolution of the reported level.
The one-third-octave filtering itself is covered by the IEC 61260 class 2
verification of :func:`phonometry.filters.verify_filter_class` (subclause 4.6)
and is not repeated here.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np

from .._internal.frozen import OwnsArrays

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "AircraftSystemComplianceResult",
    "verify_aircraft_noise_system",
]


#: Maximum system frequency-response deviation, in dB (§4.5.1).
_FREQUENCY_RESPONSE_LIMIT = 1.5

#: Maximum level non-linearity per level range, in dB (§4.5.2).
_LINEARITY_LIMITS = {"reference": 0.4, "other": 0.5}

#: Coarsest readout resolution the standard accepts, in dB (§4.7).
_RESOLUTION_LIMIT = 0.1

#: Tabulated depression/incidence angles (degrees) of IEC 61265 Table 1.
_IEC61265_ANGLES: tuple[float, ...] = (30.0, 60.0, 90.0, 120.0, 150.0)

#: IEC 61265:1995 Table 1: maximum permitted |sensitivity(0°) − sensitivity(θ)|
#: (dB) per one-third-octave band. Rows: (f_low, f_high, limits at the angles).
_IEC61265_DIRECTIONAL: tuple[tuple[float, float, tuple[float, ...]], ...] = (
    (50.0, 1600.0, (0.5, 0.5, 1.0, 1.0, 1.0)),
    (2000.0, 2000.0, (0.5, 0.5, 1.0, 1.0, 1.0)),
    (2500.0, 2500.0, (0.5, 0.5, 1.0, 1.5, 1.5)),
    (3150.0, 3150.0, (0.5, 1.0, 1.5, 2.0, 2.0)),
    (4000.0, 4000.0, (0.5, 1.0, 2.0, 2.5, 2.5)),
    (5000.0, 5000.0, (0.5, 1.5, 2.5, 3.0, 3.0)),
    (6300.0, 6300.0, (1.0, 2.0, 3.0, 4.0, 4.0)),
    (8000.0, 8000.0, (1.5, 2.5, 4.0, 5.5, 5.5)),
    (10000.0, 10000.0, (2.0, 3.5, 5.5, 6.5, 7.5)),
)


def _iec61265_directional_limit(frequency: float, angle: float) -> float:
    """The IEC 61265 Table 1 directional tolerance for a frequency and angle.

    Per subclause 4.4.2, an incidence angle between two tabulated angles takes
    the limit of the greater tabulated angle.
    """
    row = next(
        (lims for lo, hi, lims in _IEC61265_DIRECTIONAL if lo <= frequency <= hi),
        None,
    )
    if row is None:
        msg = (
            "'frequency' is not an IEC 61265 tabulated one-third-octave band "
            "(50 Hz-1.6 kHz, then 2, 2.5, 3.15, 4, 5, 6.3, 8, 10 kHz)."
        )
        raise ValueError(msg)
    if not np.isfinite(angle) or angle <= 0.0 or angle > _IEC61265_ANGLES[-1]:
        msg = "'angle' must lie in (0, 150] degrees."
        raise ValueError(msg)
    col = next(i for i, a in enumerate(_IEC61265_ANGLES) if a >= angle)
    return row[col]


@dataclass(frozen=True)
class AircraftSystemComplianceResult(OwnsArrays):
    """IEC 61265:1995 verdict on an aircraft-noise measurement chain.

    What :func:`verify_aircraft_noise_system` returns: the measurements it
    was given, each as a read-only copy. The checks are read from them and
    the limits the standard prints, and the verdict from the checks, so
    neither is a field: a result cannot state a limit or a pass its
    measurements do not reach.

    :ivar directional: The microphone directional response,
        ``{frequency_hz: {angle_deg: |Δsensitivity| dB}}`` (Table 1,
        4.4.2), or ``None`` when it was not measured.
    :ivar frequency_response: The system response deviations
        ``{frequency_hz: deviation_db}`` (4.5.1), or ``None``.
    :ivar linearity: The level non-linearity ``{"reference": dB, "other":
        dB}`` (4.5.2), or ``None``.
    :ivar resolution: The readout resolution, in dB (4.7), or ``None``.
    """

    directional: Mapping[float, Mapping[float, float]] | None = None
    frequency_response: Mapping[float, float] | None = None
    linearity: Mapping[str, float] | None = None
    resolution: float | None = None

    def __post_init__(self) -> None:
        """Hold the measurements as read-only copies and refuse one no table covers.

        :raises ValueError: If a frequency or angle is out of the tabulated
            range, or a linearity key is neither ``"reference"`` nor
            ``"other"``.
        """
        if self.directional is not None:
            object.__setattr__(
                self,
                "directional",
                MappingProxyType(
                    {
                        float(freq): MappingProxyType(
                            {float(a): float(v) for a, v in per_angle.items()}
                        )
                        for freq, per_angle in self.directional.items()
                    }
                ),
            )
        if self.frequency_response is not None:
            object.__setattr__(
                self,
                "frequency_response",
                MappingProxyType(
                    {float(f): float(v) for f, v in self.frequency_response.items()}
                ),
            )
        if self.linearity is not None:
            object.__setattr__(
                self,
                "linearity",
                MappingProxyType({str(k): float(v) for k, v in self.linearity.items()}),
            )
        if self.resolution is not None:
            object.__setattr__(self, "resolution", float(self.resolution))
        # Every check is read once here, so a measurement no table covers is
        # refused where the result is built.
        self.__dict__["_checks"] = self._read_checks()

    def _read_checks(self) -> tuple[Mapping[str, Any], ...]:
        checks: list[dict[str, Any]] = []
        if self.directional is not None:
            checks += _directional_checks(self.directional)
        if self.frequency_response is not None:
            checks += _frequency_response_checks(self.frequency_response)
        if self.linearity is not None:
            checks += _linearity_checks(self.linearity)
        if self.resolution is not None:
            checks.append(_resolution_check(self.resolution))
        return tuple(MappingProxyType(check) for check in checks)

    @property
    def checks(self) -> tuple[Mapping[str, Any], ...]:
        """One read-only row per checked quantity, ``{"quantity", "limit", "value", "ok", ...}``.

        The ``limit`` is the one the standard prints for the quantity (Table 1
        by frequency and angle, 1,5 dB, 0,4 dB or 0,5 dB, 0,1 dB) and ``ok``
        whether the measured ``value`` is within it.
        """
        checks: tuple[Mapping[str, Any], ...] = self.__dict__["_checks"]
        return checks

    @property
    def passes(self) -> bool:
        """Whether every supplied measurement met its limit.

        The chain is qualified by the conjunction of what was actually
        measured. A result that holds no measurement carries no check and
        does not pass: nothing was measured, so nothing was qualified.
        """
        return bool(self.checks) and all(bool(check["ok"]) for check in self.checks)

    def __reduce__(self) -> tuple[Any, tuple[type, dict[str, Any]]]:
        """Travel with plain dictionaries, which pickle; they are frozen again on arrival."""
        return _rebuilt_result, (
            type(self),
            {
                "directional": None
                if self.directional is None
                else {f: dict(row) for f, row in self.directional.items()},
                "frequency_response": None
                if self.frequency_response is None
                else dict(self.frequency_response),
                "linearity": None if self.linearity is None else dict(self.linearity),
                "resolution": self.resolution,
            },
        )


def _rebuilt_result(
    cls: type[AircraftSystemComplianceResult], kwargs: dict[str, Any]
) -> AircraftSystemComplianceResult:
    return cls(**kwargs)


def verify_aircraft_noise_system(
    *,
    directional: Mapping[float, Mapping[float, float]] | None = None,
    frequency_response: Mapping[float, float] | None = None,
    linearity: Mapping[str, float] | None = None,
    resolution: float | None = None,
) -> AircraftSystemComplianceResult:
    """Verify measured performance against IEC 61265:1995 tolerances.

    Each supplied measurement is checked against the standard's limit; the
    one-third-octave filtering itself is covered by the IEC 61260 class-2
    verification (subclause 4.6) and is not repeated here.

    :param directional: Microphone directional response as
        ``{frequency_hz: {angle_deg: |Δsensitivity| dB}}`` (Table 1, §4.4.2).
    :param frequency_response: System response deviations
        ``{frequency_hz: deviation_db}`` against the ±1.5 dB limit (§4.5.1).
    :param linearity: Level non-linearity ``{"reference": dB, "other": dB}``
        against the ±0.4/±0.5 dB limits (§4.5.2).
    :param resolution: Readout resolution, in dB, against the 0.1 dB limit (§4.7).
    :return: An :class:`AircraftSystemComplianceResult`, whose ``passes`` is
        the conjunction of every check and ``False`` when no measurement was
        supplied.
    :raises ValueError: If a frequency or angle is out of the tabulated range.
    """
    return AircraftSystemComplianceResult(
        directional=directional,
        frequency_response=frequency_response,
        linearity=linearity,
        resolution=resolution,
    )


def _directional_checks(
    directional: Mapping[float, Mapping[float, float]],
) -> list[dict[str, Any]]:
    """Directional-response checks against Table 1 (§4.4.2).

    :param directional: ``{frequency_hz: {angle_deg: |Δsensitivity| dB}}``.
    :return: One check per frequency and angle.
    :raises ValueError: If a frequency or angle is out of the tabulated range.
    """
    checks: list[dict[str, Any]] = []
    for freq, per_angle in directional.items():
        for angle, value in per_angle.items():
            limit = _iec61265_directional_limit(float(freq), float(angle))
            checks.append(
                {
                    "quantity": "directional_response",
                    "frequency": float(freq),
                    "angle": float(angle),
                    "limit": limit,
                    "value": float(value),
                    "ok": abs(float(value)) <= limit,
                }
            )
    return checks


def _frequency_response_checks(
    frequency_response: Mapping[float, float],
) -> list[dict[str, Any]]:
    """System frequency-response checks against the ±1.5 dB limit (§4.5.1).

    :param frequency_response: ``{frequency_hz: deviation_db}``.
    :return: One check per frequency.
    """
    return [
        {
            "quantity": "frequency_response",
            "frequency": float(freq),
            "limit": _FREQUENCY_RESPONSE_LIMIT,
            "value": float(dev),
            "ok": abs(float(dev)) <= _FREQUENCY_RESPONSE_LIMIT,
        }
        for freq, dev in frequency_response.items()
    ]


def _linearity_checks(linearity: Mapping[str, float]) -> list[dict[str, Any]]:
    """Level non-linearity checks against the ±0.4/±0.5 dB limits (§4.5.2).

    :param linearity: ``{"reference": dB, "other": dB}``.
    :return: One check per supplied level range.
    :raises ValueError: For a key other than ``"reference"`` or ``"other"``.
    """
    checks: list[dict[str, Any]] = []
    for kind, dev in linearity.items():
        if kind not in _LINEARITY_LIMITS:
            msg = "linearity keys must be 'reference' or 'other'."
            raise ValueError(msg)
        limit = _LINEARITY_LIMITS[kind]
        checks.append(
            {
                "quantity": f"linearity_{kind}",
                "limit": limit,
                "value": float(dev),
                "ok": abs(float(dev)) <= limit,
            }
        )
    return checks


def _resolution_check(resolution: float) -> dict[str, Any]:
    """Readout-resolution check against the 0.1 dB limit (§4.7).

    :param resolution: Readout resolution, in dB.
    :return: The single check.
    """
    res = float(resolution)
    return {
        "quantity": "resolution",
        "limit": _RESOLUTION_LIMIT,
        "value": res,
        "ok": bool(np.isfinite(res)) and 0.0 <= res <= _RESOLUTION_LIMIT,
    }
