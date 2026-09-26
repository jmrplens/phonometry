#  Copyright (c) 2026. Jose Manuel Requena Plens
"""ECAC Doc 29 Vol. 2 Appendix D: NPD data for a non-reference atmosphere.

The oracle is the worked example of the appendix itself, transcribed in
``doc29_appendix_d_data``: the JETW SEL NPD data recalculated for 10 degC, 80 %
and 101.325 kPa with the spectral classes 103 and 205, through both absorption
routes. Every printed table is held at its printed precision: the source
spectra of Table D-2, the three attenuation tables D-3a to D-3c, the A-weighted
levels and increments of Tables D-4 and D-5, and the revised NPD data of Tables
D-6b and D-6c.
"""

from __future__ import annotations

import dataclasses
from types import MappingProxyType

import matplotlib as mpl
import numpy as np
import pytest

mpl.use("Agg")
import matplotlib.pyplot as plt
from doc29_appendix_d_data import (
    DISTANCES_FT,
    FREQUENCIES_HZ,
    TABLE_D2,
    TABLE_D3A,
    TABLE_D3B,
    TABLE_D3C,
    TABLE_D4,
    TABLE_D5,
    TABLE_D6A,
    TABLE_D6B,
    TABLE_D6C,
)
from reference_data import IEC61672_TABLE3

from phonometry.aircraft import (
    NOY_BANDS,
    SAE_AIR1845_ATTENUATION_DB_PER_100M,
    AerodromeAtmosphere,
    AnpDatabase,
    AnpNpdCurves,
    FlightSegmentState,
    NpdAtmosphereIncrement,
    RevisedNpdCurves,
    SpectralClass,
    arp866a_attenuation,
    event_level,
    load_anp_database,
    npd_atmosphere_increment,
    revise_npd_curves,
)
from phonometry.aircraft.npd_atmosphere import _A_WEIGHTING_DB

_DB = load_anp_database()
_FT_M = 0.3048
_DISTANCES_M = np.array(DISTANCES_FT) * _FT_M
#: The atmosphere of the worked example.
_AIR = {"temperature_c": 10.0, "relative_humidity_percent": 80.0}
#: Half a unit of the last printed digit, with a hair for binary rounding.
_HALF_MILLI = 0.0005 + 1e-9
_HALF_DECI = 0.05 + 1e-9


def _increment(class_id: int, absorption: str) -> NpdAtmosphereIncrement:
    return npd_atmosphere_increment(
        _DB.spectral_class(class_id), absorption=absorption, **_AIR
    )


def _curves(operation: str, table: tuple) -> AnpNpdCurves:
    rows = [r for r in table if r[0] == operation]
    return AnpNpdCurves(
        aircraft_id="JETW",
        npd_id="JETW",
        metric="SEL",
        operation=operation,
        power_parameter="CNT (lb)",
        powers=np.array([r[1] for r in rows]),
        distances=_DISTANCES_M,
        levels=np.array([r[2] for r in rows]),
    )


def test_table_d1_is_published_frozen_over_the_24_bands() -> None:
    assert isinstance(SAE_AIR1845_ATTENUATION_DB_PER_100M, MappingProxyType)
    assert tuple(SAE_AIR1845_ATTENUATION_DB_PER_100M) == FREQUENCIES_HZ
    assert SAE_AIR1845_ATTENUATION_DB_PER_100M[1000.0] == pytest.approx(0.590)
    assert SAE_AIR1845_ATTENUATION_DB_PER_100M[10000.0] == pytest.approx(9.836)


def test_spectral_classes_103_and_205_are_table_d2() -> None:
    printed = np.array(TABLE_D2)
    assert np.array_equal(_DB.spectral_class(103).levels_db, printed[:, 0])
    assert np.array_equal(_DB.spectral_class("205").levels_db, printed[:, 1])
    assert _DB.spectral_class(103).operation == "D"
    assert _DB.spectral_class(205).operation == "A"


@pytest.mark.parametrize(("class_id", "column"), [(103, 2), (205, 3)])
def test_source_spectrum_is_table_d2(class_id: int, column: int) -> None:
    got = _increment(class_id, "arp5534").source_spectrum_db
    assert np.all(np.abs(got - np.array(TABLE_D2)[:, column]) <= _HALF_DECI)


def test_air1845_attenuation_is_table_d3a() -> None:
    got = _increment(103, "arp5534").reference_attenuation_db
    assert np.all(np.abs(got - np.array(TABLE_D3A)) <= _HALF_MILLI)


def test_arp5534_attenuation_is_table_d3c_to_the_last_digit() -> None:
    # All 240 cells, which the ISO 9613-1 Annex B saturation vapour pressure
    # does not give: ARP 5534 Eq. 6 is what makes the last digit.
    got = _increment(103, "arp5534").specified_attenuation_db
    assert np.all(np.abs(got - np.array(TABLE_D3C)) <= _HALF_MILLI)


def test_arp866a_attenuation_is_table_d3b_within_seven_ppm() -> None:
    # 208 cells to the last digit; the other 32 are the long high-frequency
    # paths, printed about 6 ppm below the ISO 3891 formula.
    got = _increment(103, "arp866a").specified_attenuation_db
    printed = np.array(TABLE_D3B)
    assert np.all(np.abs(got - printed) <= _HALF_MILLI + 7e-6 * printed)


def test_table_d3b_reads_eta_linearly_in_table_1() -> None:
    # ISO 3891 Table 1 asks for "a form of quadratic interpolation"; Table
    # D-3b is reproduced by a linear one, which is what the Appendix D route
    # asks arp866a_attenuation for. The 10 kHz band at 10 degC and 80 %
    # evaluates at f0 = 9 000 Hz with delta = 2.496, between the knots 2.30
    # (0.495) and 2.50 (0.450).
    res = arp866a_attenuation([10000.0], eta_interpolation="linear", **_AIR)
    delta = float(res.delta[0])
    assert 2.30 < delta < 2.50
    linear = 0.495 + (delta - 2.30) / 0.20 * (0.450 - 0.495)
    assert float(res.eta[0]) == pytest.approx(linear, abs=1e-12)
    assert float(res.path_attenuation_db(25000.0 * _FT_M)[0]) == pytest.approx(
        744.810, abs=0.005
    )
    # The quadratic of ISO 3891's own tables misses Table D-3b by more than a
    # decibel in the 4 kHz band at 25000 ft (204.355 dB printed).
    quadratic = arp866a_attenuation([4000.0], **_AIR)
    assert quadratic.eta_interpolation == "quadratic"
    far = float(quadratic.path_attenuation_db(25000.0 * _FT_M)[0])
    assert abs(far - TABLE_D3B[19][-1]) > 1.0


@pytest.mark.parametrize(
    ("absorption", "table"), [("arp5534", TABLE_D4), ("arp866a", TABLE_D5)]
)
def test_a_weighted_levels_and_increments_are_tables_d4_d5(
    absorption: str, table: tuple
) -> None:
    printed = np.array(table)
    for class_id, first in ((103, 0), (205, 3)):
        inc = _increment(class_id, absorption)
        got = np.column_stack(
            [inc.reference_levels_dba, inc.specified_levels_dba, inc.increment_db]
        )
        assert np.all(np.abs(got - printed[:, first : first + 3]) <= _HALF_DECI)


def test_revised_npd_data_is_table_d6b() -> None:
    for operation, class_id in (("A", 205), ("D", 103)):
        rev = revise_npd_curves(
            _curves(operation, TABLE_D6A), _DB.spectral_class(class_id), **_AIR
        )
        printed = np.array([r[2] for r in TABLE_D6B if r[0] == operation])
        assert np.all(np.abs(rev.revised.levels - printed) <= _HALF_DECI)


def test_revised_npd_data_is_table_d6c_but_its_misprinted_row() -> None:
    for operation, class_id in (("A", 205), ("D", 103)):
        rev = revise_npd_curves(
            _curves(operation, TABLE_D6A),
            _DB.spectral_class(class_id),
            absorption="arp866a",
            **_AIR,
        )
        printed = np.array([r[2] for r in TABLE_D6C if r[0] == operation])
        rows = slice(None) if operation == "A" else slice(0, -1)
        assert np.all(np.abs(rev.revised.levels[rows] - printed[rows]) <= _HALF_DECI)
    # Departure at 22 500 lb: the page prints the Table D-6b row again. The
    # Table D-6a levels plus the Table D-5 increments give this row instead.
    last = rev.revised.levels[-1]
    corrected = (109.9, 106.0, 103.2, 100.1, 94.9, 89.3, 85.2, 80.8, 76.1, 71.5)
    assert np.all(np.abs(last - np.array(corrected)) <= _HALF_DECI)
    assert TABLE_D6C[-1][2] == TABLE_D6B[-1][2]


def test_a_weighting_is_the_nominal_iec_61672_1_table_3() -> None:
    # Doc 29 names A_n without printing it; Tables D-4 and D-5 at 0.1 dB do
    # not pin every band (a 0.1 dB slip at 50 Hz or 10 kHz goes unseen there),
    # so the 24 values are held to the test suite's own transcription of
    # IEC 61672-1:2013 Table 3.
    nominal = {row[0]: row[1] for row in IEC61672_TABLE3}
    expected = np.array([nominal[band] for band in FREQUENCIES_HZ])
    assert np.array_equal(_A_WEIGHTING_DB, expected)
    assert not _A_WEIGHTING_DB.flags.writeable


def test_increment_does_not_depend_on_the_spectrum_level() -> None:
    sc = _DB.spectral_class(103)
    louder = npd_atmosphere_increment(sc.levels_db + 12.5, **_AIR)
    assert np.allclose(louder.increment_db, _increment(103, "arp5534").increment_db)


def test_arp866a_route_ignores_pressure_and_arp5534_does_not() -> None:
    sc = _DB.spectral_class(205)
    low = {"atmospheric_pressure_kpa": 80.0}
    a = npd_atmosphere_increment(sc, absorption="arp866a", **_AIR, **low)
    b = npd_atmosphere_increment(sc, absorption="arp866a", **_AIR)
    assert np.array_equal(a.increment_db, b.increment_db)
    c = npd_atmosphere_increment(sc, absorption="arp5534", **_AIR, **low)
    assert not np.allclose(c.increment_db, _increment(205, "arp5534").increment_db)


def test_standard_distances_are_the_ten_npd_distances() -> None:
    inc = _increment(103, "arp5534")
    assert np.allclose(inc.distances_m, _DISTANCES_M)
    assert inc.distance_column(1000.0 * _FT_M) == 3


def test_increment_inputs_are_refused_by_name() -> None:
    short = np.zeros(23)
    with pytest.raises(ValueError, match="'spectrum' must carry the 24"):
        npd_atmosphere_increment(short, **_AIR)
    sc = _DB.spectral_class(103)
    with pytest.raises(ValueError, match="'absorption' must be one of"):
        npd_atmosphere_increment(sc, absorption="iso9613", **_AIR)
    negative = [-1.0, 100.0]
    with pytest.raises(ValueError, match="'distances_m' must be strictly positive"):
        npd_atmosphere_increment(sc, distances_m=negative, **_AIR)
    inc = _increment(103, "arp5534")
    with pytest.raises(ValueError, match="'distance_m' must be one of the NPD"):
        inc.distance_column(500.0)


def test_increment_rejects_tables_off_its_axes() -> None:
    inc = _increment(103, "arp5534")
    transposed = inc.specified_attenuation_db.T
    with pytest.raises(ValueError, match="specified_attenuation_db"):
        dataclasses.replace(inc, specified_attenuation_db=transposed)
    short = inc.increment_db[:-1]
    with pytest.raises(ValueError, match="'increment_db' \\(9\\)"):
        dataclasses.replace(inc, increment_db=short)


def test_revised_curves_are_the_original_plus_the_increment() -> None:
    curves = _DB.npd_curves("747100", "departure", "SEL")
    rev = _DB.revised_npd_curves("747100", "departure", "SEL", **_AIR)
    assert isinstance(rev, RevisedNpdCurves)
    expected = curves.levels + rev.increment.increment_db[None, :]
    assert np.array_equal(rev.revised.levels, expected)
    assert not rev.revised.levels.flags.writeable
    assert rev.original is curves or np.array_equal(rev.original.levels, curves.levels)
    # The revised curves are an ordinary NPD table.
    assert rev.revised.level(float(curves.powers[0]), [304.8])[0] == pytest.approx(
        rev.revised.levels[0, 3]
    )


def test_revision_refuses_an_increment_from_other_distances() -> None:
    rev = _DB.revised_npd_curves("747100", "departure", "SEL", **_AIR)
    other = npd_atmosphere_increment(
        _DB.spectral_class(107), distances_m=[100.0, 200.0], **_AIR
    )
    with pytest.raises(ValueError, match="distances of the curves it revises"):
        dataclasses.replace(rev, increment=other)


def test_event_level_with_humidity_reads_the_revised_tables() -> None:
    observer = [6000.0, 0.0, 0.0]
    got = _DB.event_level(
        "747100",
        observer,
        "D",
        temperature_c=10.0,
        relative_humidity_percent=80.0,
        absorption="arp866a",
    )
    sel = _DB.revised_npd_curves(
        "747100", "D", "SEL", absorption="arp866a", **_AIR
    ).revised
    lmax = _DB.revised_npd_curves(
        "747100", "D", "LAmax", absorption="arp866a", **_AIR
    ).revised
    profile = _DB.profile("747100", "D")
    expected = event_level(
        profile.path,
        observer,
        sel.powers,
        sel.distances,
        sel.levels,
        lmax.levels,
        mounting="wing",
        atmosphere=AerodromeAtmosphere(temperature_c=10.0),
        segments=FlightSegmentState(
            ground_roll=profile.ground_roll, landing_roll=profile.landing_roll
        ),
    )
    assert got.level == pytest.approx(expected.level, abs=1e-9)
    reference = _DB.event_level("747100", observer, "D", temperature_c=10.0)
    assert got.level > reference.level


def test_event_level_with_humidity_reads_the_field_pressure() -> None:
    # SAE ARP 5534 depends on the pressure, so the recalculated tables of a
    # high field are not those of sea level: the event must read them at the
    # pressure it is given, not at the standard one.
    observer = [6000.0, 0.0, 0.0]
    air = {"temperature_c": 10.0, "relative_humidity_percent": 80.0}
    got = _DB.event_level("747100", observer, "D", atmospheric_pressure_kpa=80.0, **air)
    sel, lmax = (
        _DB.revised_npd_curves(
            "747100", "D", metric, atmospheric_pressure_kpa=80.0, **air
        ).revised
        for metric in ("SEL", "LAmax")
    )
    profile = _DB.profile("747100", "D")
    expected = event_level(
        profile.path,
        observer,
        sel.powers,
        sel.distances,
        sel.levels,
        lmax.levels,
        mounting="wing",
        atmosphere=AerodromeAtmosphere(
            temperature_c=10.0, atmospheric_pressure_kpa=80.0
        ),
        segments=FlightSegmentState(
            ground_roll=profile.ground_roll, landing_roll=profile.landing_roll
        ),
    )
    assert got.level == pytest.approx(expected.level, abs=1e-9)
    sea_level_tables = _DB.revised_npd_curves("747100", "D", "SEL", **air).revised
    assert not np.allclose(sel.levels, sea_level_tables.levels, atol=1e-3)


def test_aircraft_carries_its_two_spectral_classes() -> None:
    ac = _DB.aircraft("747100")
    assert ac.spectral_class("departure").class_id == ac.departure_spectral_class_id
    assert ac.spectral_class("A").class_id == ac.approach_spectral_class_id
    assert ac.spectral_class("D").operation == "D"
    rev = ac.revised_npd_curves("D", **_AIR)
    assert rev.original.aircraft_id == "747100"


def test_unknown_spectral_class_names_what_there_is() -> None:
    with pytest.raises(KeyError, match="spectral class '999'"):
        _DB.spectral_class(999)
    bare = AnpDatabase(aircraft={}, npd={}, distances=_DISTANCES_M, profiles={})
    with pytest.raises(KeyError, match="no spectral-class table"):
        bare.spectral_class(103)


def test_spectral_class_rejects_levels_off_its_bands() -> None:
    sc = _DB.spectral_class(103)
    assert isinstance(sc, SpectralClass)
    assert not sc.levels_db.flags.writeable
    short = sc.levels_db[:-1]
    with pytest.raises(ValueError, match="'levels_db' \\(23\\)"):
        dataclasses.replace(sc, levels_db=short)


def test_plots_en_es() -> None:
    inc5 = _increment(103, "arp5534")
    inc8 = _increment(103, "arp866a")
    ax = inc5.plot()
    inc8.plot(ax=ax)
    assert len(ax.get_legend().get_texts()) == 2
    ax = inc5.plot_attenuation(language="es")
    inc8.plot_attenuation(ax=ax, reference=False, language="es")
    assert "1000" in ax.get_title()
    assert len(ax.get_legend().get_texts()) == 3
    rev = _DB.revised_npd_curves("747100", "D", **_AIR)
    ax = rev.plot(language="es")
    assert ax.get_title().startswith("Curvas NPD recalculadas")
    ax = _DB.spectral_class(205).plot()
    assert "205" in ax.get_legend().get_texts()[0].get_text()
    plt.close("all")


def _ydata(ax: object, index: int) -> np.ndarray:
    return np.asarray(ax.lines[index].get_ydata(), dtype=np.float64)


def test_increment_plot_draws_the_increment() -> None:
    inc = _increment(205, "arp866a")
    ax = inc.plot()
    # The first line is the zero rule, the second the increment itself.
    assert np.array_equal(ax.lines[1].get_xdata(), inc.distances_m)
    assert np.array_equal(_ydata(ax, 1), inc.increment_db)
    plt.close("all")


def test_attenuation_plot_draws_the_column_of_its_distance() -> None:
    inc = _increment(103, "arp5534")
    column = inc.distance_column(_DISTANCES_M[6])
    ax = inc.plot_attenuation(distance_m=_DISTANCES_M[6])
    assert np.array_equal(_ydata(ax, 0), inc.reference_attenuation_db[:, column])
    assert np.array_equal(_ydata(ax, 1), inc.specified_attenuation_db[:, column])
    assert np.array_equal(ax.lines[1].get_xdata(), inc.frequencies_hz)
    plt.close("all")


def test_revised_plot_draws_revised_solid_over_original_dashed() -> None:
    rev = _DB.revised_npd_curves("747100", "D", **_AIR)
    ax = rev.plot()
    for i in range(rev.original.powers.size):
        solid, dashed = ax.lines[2 * i], ax.lines[2 * i + 1]
        assert solid.get_linestyle() == "-"
        assert dashed.get_linestyle() == "--"
        assert np.array_equal(solid.get_ydata(), rev.revised.levels[i])
        assert np.array_equal(dashed.get_ydata(), rev.original.levels[i])
    plt.close("all")


def test_spectral_class_plot_draws_its_levels() -> None:
    sc = _DB.spectral_class(205)
    ax = sc.plot()
    assert np.array_equal(ax.lines[0].get_xdata(), sc.frequencies_hz)
    assert np.array_equal(_ydata(ax, 0), sc.levels_db)
    plt.close("all")


def test_frequencies_are_a_copy_not_the_published_bands() -> None:
    inc = _increment(103, "arp5534")
    assert np.array_equal(inc.frequencies_hz, NOY_BANDS)
    assert inc.frequencies_hz is not NOY_BANDS


def test_noise_contour_with_humidity_reads_the_revised_tables() -> None:
    x = np.linspace(0.0, 8000.0, 5)
    y = np.linspace(-1000.0, 1000.0, 3)
    dry = _DB.noise_contour("747100", "D", x=x, y=y, temperature_c=10.0)
    humid = _DB.aircraft("747100").noise_contour(
        "D", x=x, y=y, temperature_c=10.0, relative_humidity_percent=80.0
    )
    # Close to the runway the two air masses give the same levels; far from it
    # the humid air, which absorbs less than the AIR-1845 average, is louder.
    assert humid.levels.shape == dry.levels.shape
    rise = humid.levels - dry.levels
    assert np.max(rise) > 1.0
    assert np.max(np.abs(rise)) < 4.0


def test_a_misspelt_absorption_route_is_refused_without_a_humidity() -> None:
    observer = [6000.0, 0.0, 0.0]
    with pytest.raises(ValueError, match="'absorption' must be one of"):
        _DB.event_level("747100", observer, "D", absorption="arp866")


def _export(root: object, spectral: str | None) -> AnpDatabase:
    """A CSV export of the three required tables, plus the spectral one given."""
    import pathlib
    from importlib.resources import files

    folder = pathlib.Path(str(root))
    source = files("phonometry.aircraft.data.anp")
    for name in ("Aircraft.csv", "NPD_data.csv", "Default_fixed_point_profiles.csv"):
        (folder / name).write_text(source.joinpath(name).read_text())
    if spectral is not None:
        (folder / "Spectral_classes.csv").write_text(spectral)
    return load_anp_database(folder)


def test_an_export_without_spectral_classes_still_loads(tmp_path: object) -> None:
    db = _export(tmp_path, None)
    assert db.spectral_class_ids == []
    jumbo = db.aircraft("747100")
    with pytest.raises(KeyError, match="no spectral-class table"):
        jumbo.spectral_class("D")


def test_a_spectral_table_off_the_24_bands_is_refused(tmp_path: object) -> None:
    from importlib.resources import files

    text = (
        files("phonometry.aircraft.data.anp")
        .joinpath("Spectral_classes.csv")
        .read_text()
    )
    truncated = "\n".join(line.rsplit(";", 1)[0] for line in text.splitlines())
    with pytest.raises(ValueError, match="must carry the 24 'L_<f>Hz' columns"):
        _export(tmp_path, truncated)


def test_an_empty_spectral_table_carries_no_class(tmp_path: object) -> None:
    header = "Spectral Class ID;Op Type;Description;L_50Hz\n"
    db = _export(tmp_path, header)
    assert db.spectral_class_ids == []
