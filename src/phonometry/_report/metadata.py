#  Copyright (c) 2026. Jose M. Requena-Plens
"""Test-report metadata for the ISO 717 accredited-laboratory fiche.

:class:`ReportMetadata` is the shared, frozen container of the descriptive
fields an accredited sound-insulation report carries around the ISO 717 rating:
the specimen, the client, the room and climatic conditions, the laboratory
identity and, optionally, the requirement the result is checked against. It is
passed to a rating result's ``report(..., metadata=...)`` method; every field is
optional and only the supplied ones are rendered, so the same object drives both
a full accredited fiche and a lightweight prediction fiche.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, fields


@dataclass(frozen=True)
class ReportMetadata:
    """Descriptive metadata for the accredited ISO 717 report fiche.

    All fields are optional (default ``None``); the report renders only the
    fields that are supplied, so a partially populated instance is valid. The
    numeric fields are validated on construction by physical range: the
    dimension, mass, volume and pressure fields must be finite and strictly
    positive; the temperature and requirement fields need only be finite (0
    degrees Celsius or below is a valid test condition, and a programme-loudness
    target in LUFS is negative); and the relative-humidity fields must lie
    within 0..100 %. A violation raises :class:`ValueError`.

    :ivar specimen: Specimen description printed in the header (the tested
        element, e.g. ``"200 mm concrete wall"``).
    :ivar client: Client the test was carried out for.
    :ivar mounted_by: Who mounted the specimen in the test opening.
    :ivar manufacturer: Manufacturer of the tested element.
    :ivar area: Specimen area ``S``, in m^2 (the free test opening area).
    :ivar mass_per_area: Measured mass per unit area, in kg/m^2.
    :ivar source_volume: Source-room volume, in m^3.
    :ivar receiving_volume: Receiving-room volume, in m^3.
    :ivar temperature: Air temperature during the test, in degrees Celsius (a
        single representative value; use the per-room fields below when the
        source and receiving rooms are reported separately).
    :ivar relative_humidity: Relative humidity during the test, in %.
    :ivar source_temperature: Source-room air temperature, in degrees Celsius.
    :ivar source_relative_humidity: Source-room relative humidity, in %.
    :ivar receiving_temperature: Receiving-room air temperature, in degrees
        Celsius.
    :ivar receiving_relative_humidity: Receiving-room relative humidity, in %.
    :ivar pressure: Ambient (static) air pressure during the test, in kPa.
    :ivar test_room: Test-room / facility identification.
    :ivar mounting: Mounting condition of the specimen (e.g. the ISO 10140-1
        mounting code or a short description).
    :ivar measurement_standard: Measurement standard the spectrum was obtained
        under (e.g. ``"ISO 10140-2"`` or ``"ISO 16283-1"``); it forms the
        report's standard-basis line together with the ISO 717 rating part.
    :ivar test_date: Date of the test, as a free-form string.
    :ivar laboratory: Testing laboratory / institute name (footer).
    :ivar operator: Operator who carried out the test (footer signature line).
    :ivar report_id: Report / test number (footer).
    :ivar requirement: Target single-number value the verdict row compares the
        rating against, expressed in the rating's own unit (e.g. dB, a
        dimensionless absorption coefficient, sone, or a programme-loudness
        level in LUFS). It need only be finite (a loudness target in LUFS is
        negative), so its sign is not constrained. The pass direction is
        defined by each rating's ``report`` method: quantities where more is
        better (airborne insulation, absorption) pass at or above the
        requirement, and quantities where less is better (impact level,
        loudness, aircraft noise) pass at or below it; the programme-loudness
        fiche reads it as the target level and passes within a tolerance.
    :ivar notes: Free-form remarks printed in the footer.
    :raises ValueError: If a supplied dimension/mass/volume/pressure is not
        finite and strictly positive, a temperature or requirement is not
        finite, or a relative humidity is outside 0..100 %.
    """

    specimen: str | None = None
    client: str | None = None
    mounted_by: str | None = None
    manufacturer: str | None = None
    area: float | None = None
    mass_per_area: float | None = None
    source_volume: float | None = None
    receiving_volume: float | None = None
    temperature: float | None = None
    relative_humidity: float | None = None
    source_temperature: float | None = None
    source_relative_humidity: float | None = None
    receiving_temperature: float | None = None
    receiving_relative_humidity: float | None = None
    pressure: float | None = None
    test_room: str | None = None
    mounting: str | None = None
    measurement_standard: str | None = None
    test_date: str | None = None
    laboratory: str | None = None
    operator: str | None = None
    report_id: str | None = None
    requirement: float | None = None
    notes: str | None = None

    #: Numeric fields that must be finite and strictly positive.
    _POSITIVE_FIELDS = (
        "area",
        "mass_per_area",
        "source_volume",
        "receiving_volume",
        "pressure",
    )
    #: Fields that need only be finite, of any sign: the test temperatures (0 C
    #: or below is a valid condition, e.g. an unheated outdoor facade) and the
    #: requirement (a target such as a programme-loudness level in LUFS is
    #: legitimately negative, so only its finiteness is checked here; each
    #: rating's ``report`` gives it a physical meaning and pass direction).
    _FINITE_FIELDS = (
        "temperature",
        "source_temperature",
        "receiving_temperature",
        "requirement",
    )
    #: Relative-humidity fields: finite and within 0..100 %.
    _HUMIDITY_FIELDS = (
        "relative_humidity",
        "source_relative_humidity",
        "receiving_relative_humidity",
    )

    def _require(
        self, name: str, ok: "Callable[[float], bool]", description: str
    ) -> None:
        """Raise ``ValueError`` unless a supplied numeric field satisfies ``ok``."""
        value = getattr(self, name)
        if value is None:
            return
        if not ok(float(value)):
            raise ValueError(
                f"ReportMetadata.{name} must be {description} when given; "
                f"got {value!r}."
            )

    def __post_init__(self) -> None:
        """Validate the supplied numeric fields by physical range."""
        for name in self._POSITIVE_FIELDS:
            self._require(
                name, lambda x: math.isfinite(x) and x > 0.0,
                "a finite, positive number",
            )
        for name in self._FINITE_FIELDS:
            self._require(name, math.isfinite, "finite")
        for name in self._HUMIDITY_FIELDS:
            self._require(
                name, lambda x: math.isfinite(x) and 0.0 <= x <= 100.0,
                "a relative humidity in 0..100 %",
            )

    def is_empty(self) -> bool:
        """Return ``True`` when no field is set (an all-``None`` instance)."""
        return all(getattr(self, f.name) is None for f in fields(self))
