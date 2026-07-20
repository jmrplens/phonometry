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
    numeric fields are validated on construction: when given they must be
    finite and strictly positive, otherwise :class:`ValueError` is raised.

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
    :ivar requirement: Target single-number value the rating is checked
        against for the verdict row, in dB. For an airborne rating the result
        passes when it is greater than or equal to the requirement; for an
        impact rating it passes when it is less than or equal to it (a lower
        impact level is better).
    :ivar notes: Free-form remarks printed in the footer.
    :raises ValueError: If a supplied dimension/mass/volume/pressure/requirement
        is not finite and strictly positive, a temperature is not finite, or a
        relative humidity is outside 0..100 %.
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
        "requirement",
    )
    #: Temperature fields: finite, but any sign (0 C or below is a valid test
    #: condition, e.g. an unheated outdoor facade measurement).
    _TEMPERATURE_FIELDS = (
        "temperature",
        "source_temperature",
        "receiving_temperature",
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
        for name in self._TEMPERATURE_FIELDS:
            self._require(name, math.isfinite, "finite")
        for name in self._HUMIDITY_FIELDS:
            self._require(
                name, lambda x: math.isfinite(x) and 0.0 <= x <= 100.0,
                "a relative humidity in 0..100 %",
            )

    def is_empty(self) -> bool:
        """Return ``True`` when no field is set (an all-``None`` instance)."""
        return all(getattr(self, f.name) is None for f in fields(self))
