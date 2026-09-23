#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Dump the published catalogues for the site to render.

The rows live in the package, as one data file per published table, and the
loader that reads them adds what follows from the cells a page printed: the
three wave speeds of a solid, the shear modulus of a frame whose page printed
a Young's modulus. A page of the site that imported the data files directly
would show the printed half and miss the derived one, and would have to
interpret the hedges (a range, a bound, a word where a number would be) in
JavaScript, which is a second implementation of a thing the library already
does.

So the site reads what the **library** holds, dumped here into one module it
imports at build time. The same arrangement as the conformance counts and the
API sidebar: Python writes, Astro imports, and CI fails if the artefact drifts
from a fresh run, which is what stops the page from still showing last
quarter's catalogue.

Every value arrives already formatted for reading. A row of a materials table
is not a row of floats: a density may be an interval the book declined to
collapse, a loss factor may be an upper bound, a tortuosity may be the word
"model". Formatting in Python keeps the rendering rules in the same place as
the rules about what a cell means, and leaves the component to place text.

Run through ``make catalogue-data``; ``--check`` exits non-zero when the
committed file differs from a fresh run, which is what CI does.
"""

from __future__ import annotations

import argparse
import decimal
import functools
import math
import pathlib
import statistics
import sys
from typing import TYPE_CHECKING, Any, NamedTuple

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from phonometry._internal.catalogue import read_table  # noqa: E402
from phonometry.building import (  # noqa: E402
    PUBLISHED_IMPACT_INSULATION,
    PUBLISHED_TRANSMISSION_LOSS,
    TRANSMISSION_LOSS_BANDS_HZ,
)
from phonometry.building.prediction.detailed_model import EN_12354_AIR  # noqa: E402
from phonometry.environment.propagation import PUBLISHED_GROUND  # noqa: E402
from phonometry.fluids import (  # noqa: E402
    PUBLISHED_FLUIDS,
    PUBLISHED_GASES,
    PUBLISHED_NONLINEARITY,
)
from phonometry.materials.absorbers import (  # noqa: E402
    ABSORPTION_BANDS_HZ,
    PUBLISHED_ABSORPTION,
    PUBLISHED_ABSORPTION_AREAS,
    PUBLISHED_CARPETS,
    PUBLISHED_FLOW_RESISTANCE,
    PUBLISHED_POROUS,
)
from phonometry.materials.absorbers.airflow_resistance import ANNEX_A_AIR  # noqa: E402
from phonometry.materials.absorbers.porous import PUBLISHED_AIR  # noqa: E402
from phonometry.materials.diffusers import (  # noqa: E402
    DIFFUSION_BANDS_HZ,
    PUBLISHED_DIFFUSION,
    PUBLISHED_PREDICTED_SCATTERING,
    PUBLISHED_SCATTERING,
    SCATTERING_BANDS_HZ,
)
from phonometry.materials.resilient import (  # noqa: E402
    PUBLISHED_RESILIENT_LAYERS,
    PUBLISHED_RESILIENT_MODULI,
)
from phonometry.noise_control import (  # noqa: E402
    DUCT_WALL_BANDS_HZ,
    PUBLISHED_DUCT_TRANSMISSION_LOSS,
)
from phonometry.room.enclosed_space_absorption import (  # noqa: E402
    AIR_ATTENUATION,
    OCTAVE_BANDS,
    PUBLISHED_AIR_CONDITION,
)
from phonometry.simulation.ntff import SIMULATION_AIR  # noqa: E402
from phonometry.solids import (  # noqa: E402
    PUBLISHED_DAMPING,
    PUBLISHED_DAMPING_TREATMENTS,
    PUBLISHED_ORTHOTROPIC_WOOD,
    PUBLISHED_PLATEAU_DATA,
    PUBLISHED_SOLID_NONLINEARITY,
    PUBLISHED_SOLIDS,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping

    from phonometry.io import CatalogueRow

#: Where the site imports the catalogues from.
OUTPUT = (
    pathlib.Path(__file__).resolve().parents[1] / "site/src/generated/catalogues.mjs"
)

#: The declaration file that gives ``OUTPUT`` its types. TypeScript pairs a
#: ``.mjs`` module with a sibling ``.d.mts`` of the same name automatically,
#: so a page that imports the module reads these types and not the giant
#: structural inference a JSON literal of this size would otherwise produce.
TYPES_OUTPUT = OUTPUT.with_suffix(".d.mts")

#: Every table :func:`render` writes, in the order it writes them, so
#: :func:`render_types` can declare one field per table without a second
#: dict to keep in step with the first.
_TABLE_KEYS = (
    "solids",
    "porous",
    "ground",
    "gases",
    "damping",
    "dampingTreatments",
    "orthotropicWood",
    "plateau",
    "nonlinearity",
    "solidNonlinearity",
    "flowResistance",
    "resilientLayers",
    "resilientModuli",
    "absorption",
    "carpets",
    "transmissionLoss",
    "impactInsulation",
    "ductTransmissionLoss",
    "scattering",
    "diffusion",
    "predictedScattering",
    "absorptionAreas",
    "fluids",
    "airAttenuation",
)

#: The columns each catalogue shows, as ``(field, heading, heading in Spanish,
#: unit)``. A unit of the empty string is a dimensionless quantity, which is
#: not the same as a quantity whose unit the heading already carries. The
#: headings travel in both languages because the site publishes the page in
#: both and a column called "Young's modulus" over a Spanish table is the one
#: string a reader cannot look up; the material names do not, because they are
#: what the book printed.
SOLID_COLUMNS = (
    ("density_kg_m3", "Density", "Densidad", "kg/m³"),
    ("youngs_modulus_pa", "Young's modulus", "Módulo de Young", "Pa"),
    ("shear_modulus_pa", "Shear modulus", "Módulo de cizalla", "Pa"),
    ("poisson_ratio", "Poisson ratio", "Coeficiente de Poisson", ""),
    ("longitudinal_speed_m_s", "Longitudinal speed", "Velocidad longitudinal", "m/s"),
    ("bar_longitudinal_speed_m_s", "Bar speed", "Velocidad de barra", "m/s"),
    ("plate_longitudinal_speed_m_s", "Plate speed", "Velocidad de placa", "m/s"),
    ("bulk_longitudinal_speed_m_s", "Bulk speed", "Velocidad de medio infinito", "m/s"),
    ("transverse_speed_m_s", "Transverse speed", "Velocidad transversal", "m/s"),
    ("loss_factor", "Loss factor", "Factor de pérdidas", ""),
    (
        "flexural_loss_factor",
        "Flexural loss factor",
        "Factor de pérdidas a flexión",
        "",
    ),
    (
        "longitudinal_loss_factor",
        "Longitudinal loss factor",
        "Factor de pérdidas longitudinal",
        "",
    ),
    ("in_situ_loss_factor", "In-situ loss factor", "Factor de pérdidas in situ", ""),
    (
        "thickness_critical_frequency_product_m_hz",
        "Thickness × critical frequency",
        "Espesor × frecuencia crítica",
        "m·Hz",
    ),
)

#: The damping treatments, where a loss factor is never one number. The peak
#: leads, because it is what the table is for, and the three temperatures
#: follow it immediately, because the peak is not a property of the material
#: until they are beside it: the same polymer at 10 Hz and at 1 kHz peaks
#: thirty degrees apart. The four moduli close the row, the transition one
#: being the only of the three storage moduli that applies where the loss
#: factor peaks.
DAMPING_COLUMNS = (
    ("max_loss_factor", "Maximum loss factor", "Factor de pérdidas máximo", ""),
    (
        "peak_temperature_at_10_hz_c",
        "Peak at 10 Hz",
        "Pico a 10 Hz",
        "°C",
    ),
    (
        "peak_temperature_at_100_hz_c",
        "Peak at 100 Hz",
        "Pico a 100 Hz",
        "°C",
    ),
    (
        "peak_temperature_at_1000_hz_c",
        "Peak at 1 kHz",
        "Pico a 1 kHz",
        "°C",
    ),
    (
        "youngs_modulus_max_pa",
        "Young's modulus, stiff end",
        "Módulo de Young, extremo rígido",
        "Pa",
    ),
    (
        "youngs_modulus_min_pa",
        "Young's modulus, soft end",
        "Módulo de Young, extremo blando",
        "Pa",
    ),
    (
        "youngs_modulus_transition_pa",
        "Young's modulus, transition",
        "Módulo de Young, en la transición",
        "Pa",
    ),
    ("loss_modulus_max_pa", "Maximum loss modulus", "Módulo de pérdidas máximo", "Pa"),
)


WOOD_COLUMNS = (
    ("density_kg_m3", "Density", "Densidad", "kg/m³"),
    (
        "plate_stiffness_d1_pa",
        "D1, along the grain",
        "D1, a lo largo de la fibra",
        "Pa",
    ),
    ("plate_stiffness_d2_pa", "D2, coupling", "D2, acoplamiento", "Pa"),
    ("plate_stiffness_d3_pa", "D3, across the grain", "D3, a través de la fibra", "Pa"),
    ("plate_stiffness_d4_pa", "D4, twisting", "D4, torsión", "Pa"),
    (
        "relative_scaling_factor",
        "Relative scaling factor",
        "Factor de escala relativo",
        "",
    ),
)

PLATEAU_COLUMNS = (
    (
        "surface_density_per_mm_kg_m2",
        "Surface density per mm",
        "Densidad superficial por mm",
        "kg/m² per mm",
    ),
    ("coincidence_height_db", "Coincidence height", "Altura de la coincidencia", "dB"),
    (
        "plateau_frequency_ratio",
        "Plateau frequency ratio B/A",
        "Razón de frecuencias B/A",
        "",
    ),
)

#: A damping treatment on the chapter's standard panel: the decay rate leads,
#: then what the treatment is and how it was laid.
DAMPING_TREATMENT_COLUMNS = (
    ("decay_rate_db_s", "Decay rate", "Tasa de decaimiento", "dB/s"),
    ("temperature_c", "Temperature", "Temperatura", "°C"),
    ("adhered_area_percent", "Area bonded", "Área adherida", "%"),
    ("surface_density_kg_m2", "Surface density", "Masa superficial", "kg/m²"),
)

#: A resilient material under a floating floor: the modulus it springs with,
#: the density it is sold by, and the load the modulus was measured under.
RESILIENT_MODULUS_COLUMNS = (
    (
        "dynamic_youngs_modulus_pa",
        "Dynamic modulus",
        "Módulo dinámico",
        "Pa",
    ),
    ("density_kg_m3", "Density", "Densidad", "kg/m³"),
    ("static_load_pa", "Static load", "Carga estática", "Pa"),
)

#: A carpet: its pile, then the one acoustic number the page gives it.
CARPET_COLUMNS = (
    ("pile_weight_kg_m2", "Pile weight", "Peso del pelo", "kg/m²"),
    ("pile_height_mm", "Pile height", "Altura del pelo", "mm"),
    (
        "noise_reduction_coefficient",
        "Noise reduction coefficient",
        "Coeficiente de reducción del ruido",
        "",
    ),
)

#: The nonlinearity parameter of a solid. The bonding is a word and has a
#: text column of its own, the way a duct's shape does.
SOLID_NONLINEARITY_COLUMNS = (
    ("nonlinearity_parameter", "β (averaged)", "β (promediado)", ""),
)

#: The nonlinearity parameter of a liquid, and the conditions it was
#: measured at. The value leads, because it is what a reader came for; the
#: temperature follows because most substances are printed at several, and
#: the pressure and the year are each printed by one table only and stay
#: empty on the rest.
NONLINEARITY_COLUMNS = (
    ("b_over_a", "B/A", "B/A", ""),
    ("temperature_c", "Temperature", "Temperatura", "°C"),
    ("static_pressure_pa", "Static pressure", "Presión estática", "Pa"),
    ("year", "Year", "Año", ""),
)

POROUS_COLUMNS = (
    (
        "flow_resistivity_pa_s_m2",
        "Flow resistivity",
        "Resistividad al flujo",
        "Pa·s/m²",
    ),
    ("porosity", "Porosity", "Porosidad", ""),
    ("tortuosity", "Tortuosity", "Tortuosidad", ""),
    ("viscous_length_um", "Viscous length", "Longitud viscosa", "µm"),
    ("thermal_length_um", "Thermal length", "Longitud térmica", "µm"),
    ("thermal_permeability_m2", "Thermal permeability", "Permeabilidad térmica", "m²"),
    ("fibre_diameter_um", "Fibre diameter", "Diámetro de fibra", "µm"),
    (
        "fibre_diameter_distribution_parameter",
        "Diameter distribution",
        "Distribución de diámetros",
        "",
    ),
    ("shot_content_percent", "Shot content", "Contenido de perdigón", "%"),
    ("binder_content_percent", "Binder content", "Contenido de ligante", "%"),
    ("frame_density_kg_m3", "Frame density", "Densidad del esqueleto", "kg/m³"),
    ("thickness_mm", "Thickness", "Espesor", "mm"),
    ("youngs_modulus_pa", "Young's modulus", "Módulo de Young", "Pa"),
    ("shear_modulus_pa", "Shear modulus", "Módulo de cizalla", "Pa"),
    ("poisson_ratio", "Poisson ratio", "Coeficiente de Poisson", ""),
    (
        "structural_loss_factor",
        "Structural loss factor",
        "Factor de pérdidas estructural",
        "",
    ),
)


#: The thin resistive facings, whose resistance is per unit **area**. The unit
#: says so and the heading cannot, which is why the prose of the page says it
#: too: the porous table above holds a resistivity per metre of bulk material
#: and the two are a thickness apart.
FLOW_RESISTANCE_COLUMNS = (
    (
        "specific_flow_resistance_pa_s_m",
        "Specific flow resistance",
        "Resistencia al flujo específica",
        "Pa·s/m",
    ),
    (
        "normalized_flow_resistance",
        "Normalized flow resistance",
        "Resistencia al flujo normalizada",
        "",
    ),
    ("wires_per_cm", "Wires per centimetre", "Hilos por centímetro", "1/cm"),
    ("wire_diameter_um", "Wire diameter", "Diámetro del hilo", "µm"),
    ("thickness_mm", "Thickness", "Espesor", "mm"),
    (
        "mass_per_area_kg_m2",
        "Mass per unit area",
        "Masa por unidad de área",
        "kg/m²",
    ),
    ("surface_density_g_m2", "Surface density", "Masa superficial", "g/m²"),
    ("nonlinearity_factor", "Nonlinearity factor", "Factor de no linealidad", ""),
)

#: The resilient layers of a floating floor. The stiffness is per unit area,
#: which is what the N/m³ of the heading says, and the density and the
#: thickness beside it are what tell four rows of one material apart. The
#: apparent stiffness of a test specimen is a column of its own, because it is
#: not the stiffness of the installed layer; no published table prints one
#: today, and a column no row fills is not shown.
RESILIENT_LAYER_COLUMNS = (
    (
        "dynamic_stiffness_n_m3",
        "Dynamic stiffness per unit area",
        "Rigidez dinámica por unidad de superficie",
        "N/m³",
    ),
    (
        "apparent_dynamic_stiffness_n_m3",
        "Apparent dynamic stiffness per unit area",
        "Rigidez dinámica aparente por unidad de superficie",
        "N/m³",
    ),
    ("density_kg_m3", "Density", "Densidad", "kg/m³"),
    ("thickness_mm", "Thickness", "Espesor", "mm"),
)

#: The impact insulation of a floor. Two ratings that are never both on one
#: row, and a density that three rows bury in their printed description.
IMPACT_INSULATION_COLUMNS = (
    (
        "impact_insulation_class",
        "Impact insulation class",
        "Clase de aislamiento al impacto",
        "",
    ),
    (
        "impact_insulation_class_improvement",
        "Improvement in the class",
        "Mejora de la clase",
        "",
    ),
    ("layer_density_kg_m3", "Density of one layer", "Densidad de una capa", "kg/m³"),
    (
        "impact_sound_improvement_db",
        "Average improvement",
        "Mejora media",
        "dB",
    ),
    ("added_load_pa", "Added load", "Carga adicional", "Pa"),
)


def _band_heading(band: int, *, spanish: bool = False) -> str:
    """How the site heads a band column: ``125 Hz``, ``1 kHz``, ``1.25 kHz``.

    The one-third octave bands put a decimal in the heading, and a decimal is
    the one part of a frequency that does translate: Spanish writes it with a
    comma.

    :param band: The band's centre frequency, in hertz.
    :param spanish: Whether to spell the decimal separator the Spanish way.
    :return: The heading.
    """
    if band < 1000:
        return f"{band} Hz"
    heading = f"{band / 1000:g} kHz"
    return heading.replace(".", ",") if spanish else heading


#: One column per octave band. The heading is the band itself, in both
#: languages, because a frequency does not translate.
ABSORPTION_COLUMNS = tuple(
    (
        f"absorption_coefficient_{band}",
        _band_heading(band),
        _band_heading(band),
        "",
    )
    for band in ABSORPTION_BANDS_HZ
)

ABSORPTION_AREA_COLUMNS = tuple(
    (
        f"absorption_area_{band}_m2",
        _band_heading(band),
        _band_heading(band),
        "m²",
    )
    for band in ABSORPTION_BANDS_HZ
)

#: The transmission loss table prints a thickness and a surface density
#: beside the description, and those two are what tell six windows of the same
#: name apart, so they lead the table rather than trailing the bands. The
#: rating follows them: seven of the tables print nothing else, and a column
#: of STC after eight empty bands would be the last thing a reader finds.
TRANSMISSION_LOSS_COLUMNS = (
    ("thickness_mm", "Thickness", "Espesor", "mm"),
    ("surface_density_kg_m2", "Surface density", "Masa superficial", "kg/m²"),
    ("block_mass_kg", "Mass of one block", "Masa de un bloque", "kg"),
    (
        "sound_transmission_class",
        "Sound transmission class",
        "Clase de transmisión del sonido",
        "",
    ),
    *(
        (
            f"transmission_loss_{band}_db",
            _band_heading(band),
            _band_heading(band),
            "dB",
        )
        for band in TRANSMISSION_LOSS_BANDS_HZ
    ),
)

#: A duct wall, whose size leads the row for the same reason the thickness
#: leads a partition: it is what tells two rows of one table apart. The
#: diameter is worth its own column although the row is labelled with it,
#: because two rows do not print one and carry it down from the merged cell
#: above, and only a column can show that those two were derived. The length
#: is printed by two of the six tables and empty on the other four, whose note
#: gives the 6,1 m they were all measured at.
DUCT_TRANSMISSION_LOSS_COLUMNS = (
    ("diameter_mm", "Diameter", "Diámetro", "mm"),
    ("first_side_mm", "First side", "Primer lado", "mm"),
    ("second_side_mm", "Second side", "Segundo lado", "mm"),
    ("duct_length_m", "Duct length", "Longitud del conducto", "m"),
    *(
        (
            f"transmission_loss_{band}_db",
            _band_heading(band),
            _band_heading(band),
            "dB",
        )
        for band in DUCT_WALL_BANDS_HZ
    ),
)

#: One column per octave band of the air attenuation table, whose rows are
#: conditions rather than materials. The coefficient is a power attenuation in
#: neper per metre, which is not the decibel per metre of an outdoor
#: propagation model, and the column style moves the standard's own factor of
#: a thousand into the heading.
AIR_ATTENUATION_COLUMNS = tuple(
    (
        f"air_attenuation_{int(band)}_np_m",
        _band_heading(int(band)),
        _band_heading(int(band)),
        "Np/m",
    )
    for band in OCTAVE_BANDS
)

#: One column per one-third octave band, which is where the decimal
#: separator of the heading starts to matter.
SCATTERING_COLUMNS = tuple(
    (
        f"scattering_coefficient_{band}",
        _band_heading(band),
        _band_heading(band, spanish=True),
        "",
    )
    for band in SCATTERING_BANDS_HZ
)

#: One column per one-third octave band, and one for the angle the row was
#: computed at, which is what tells three rows of one surface apart.
DIFFUSION_COLUMNS = (
    ("angle_of_incidence_deg", "Angle of incidence", "Ángulo de incidencia", "°"),
    *(
        (
            f"diffusion_coefficient_{band}",
            _band_heading(band),
            _band_heading(band, spanish=True),
            "",
        )
        for band in DIFFUSION_BANDS_HZ
    ),
)

#: The predicted tables add the angle they were computed at and the solver
#: that computed them, which is what a reader has to see before using a row.
PREDICTED_SCATTERING_COLUMNS = (
    ("angle_of_incidence_deg", "Angle of incidence", "Ángulo de incidencia", "°"),
    *SCATTERING_COLUMNS,
)

GAS_COLUMNS = (
    ("molar_mass_kg_mol", "Molar mass", "Masa molar", "kg/mol"),
    (
        "heat_capacity_ratio",
        "Ratio of specific heats",
        "Relación de calores específicos",
        "",
    ),
)

GROUND_COLUMNS = (
    (
        "flow_resistivity_pa_s_m2",
        "Effective flow resistivity",
        "Resistividad al flujo efectiva",
        "Pa·s/m²",
    ),
    ("porosity", "Porosity", "Porosidad", ""),
    ("porosity_percent", "Porosity", "Porosidad", "%"),
    ("water_content_percent", "Water content", "Contenido de agua", "%"),
    (
        "porosity_decay_rate_per_m",
        "Porosity decay",
        "Decaimiento de porosidad",
        "1/m",
    ),
    (
        "iso_9613_ground_factor",
        "ISO 9613-2 ground factor",
        "Factor de suelo ISO 9613-2",
        "",
    ),
    (
        "nmpb_ground_factor",
        "NMPB-2008 ground factor",
        "Factor de suelo NMPB-2008",
        "",
    ),
)

#: Significant figures a **derived** number is rounded to before it is shown.
#: Its inputs were printed to four at most, so a plate speed worked out of a
#: modulus and a density is not known to fifteen and must not be shown to
#: fifteen. A value the page itself printed is shown as stored, whatever its
#: length: the 345,866 52 m/s of the metrology annex is what that annex
#: prints, and rounding it here would erase what distinguishes it.
_DERIVED_FIGURES = 4

#: Where a column stops reading as digits. A modulus of 471 700 000 000 Pa is
#: twelve digits of a number nobody says out loud, and a permeability of
#: 0,0000000033 m2 is eight leading zeros. A column like that is rewritten:
#: first by moving the prefix into the heading, so the moduli are a column of
#: GPa, and where the unit takes no prefix, by a mantissa and a power of ten.
#: The test is made once per column and not per cell, because a column is what
#: a reader compares down.
#:
#: It is made on the median and not on the extremes, because one outlier must
#: not set the form of a whole column: the loss factors of the solids run from
#: 0,000003 to 0,3 around a median of 0,005, and writing that column in powers
#: of ten to spare its smallest cell would turn every ordinary 0,005 in it
#: into 5 x 10^-3.
_BIG = 1e7
_TINY = 1e-4

#: The prefixes a heading may take, as (exponent, symbol), largest first.
_PREFIXES = (
    (9, "G"),
    (6, "M"),
    (3, "k"),
    (0, ""),
    (-3, "m"),
    (-6, "µ"),
    (-9, "n"),
)

#: The units a prefix may be moved into. A unit that already carries one
#: (``kg/m3``), a squared one (``m2``, where a prefix would square with it) and
#: a compound of two quantities (``m.Hz``) are left alone, and a column in one
#: of those that still does not read as digits falls back on a power of ten.
#: The prefix goes on the first unit of the set and binds to that alone, which
#: is why a stiffness per unit volume takes one: ``MN/m3`` is a meganewton over
#: a cubic metre, and it is what the book that prints those rows prints.
_PREFIXABLE = frozenset({"N/m³", "Np/m", "Pa", "Pa·s", "Pa·s/m²"})

#: The superscript digits a power of ten is written with, so the exponent sets
#: as an exponent in a table cell, in the markdown twin of the page and in the
#: text a reader copies out of either.
_SUPERSCRIPT = str.maketrans(
    "-0123456789", "\u207b\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079"
)

#: The narrow no-break space this corpus groups thousands with, which is what
#: keeps a group from breaking across a line.
_GROUP = "\u202f"


def _plain(value: float, exponent: int = 0) -> str:
    """*value* as a decimal string: no exponent, no digit it does not carry.

    ``repr`` gives the shortest string that round-trips, which is the digits
    the number actually has, and :class:`~decimal.Decimal` turns that into
    positional notation without inventing any. ``format(value, "g")`` cannot
    be used: it drops into exponent form at 1e5, which is where the densities
    and the moduli of these tables live.

    The scaling is a decimal shift and not a division, because dividing
    143 000 000 by a thousand in binary floating point gives
    143 000,000 000 000 01 and the page would print it.

    :param value: The number.
    :param exponent: Powers of ten to take out of it, which is how a column
        moves its prefix into the heading: 3 writes 4 400 Pa as 4,4 in a
        column of kPa.
    :return: Its positional form, trailing zeros trimmed.
    """
    text = format(decimal.Decimal(repr(value)).scaleb(-exponent), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def number(
    value: float,
    *,
    exact: bool = True,
    exponent: int = 0,
    scientific: bool = False,
) -> str:
    """One number, written the way this corpus writes numbers.

    The decimal separator is the comma, as in every figure and every table of
    this documentation, and the thousands are separated by the narrow no-break
    space.

    :param value: The number.
    :param exact: Whether a page printed it, in which case every digit it
        carries is shown. A number this library derived is rounded to
        :data:`_DERIVED_FIGURES` significant figures first, because its inputs
        were printed to no more than that.
    :param exponent: Powers of ten this column moved into its heading, as a
        prefix: 3 writes 4 400 Pa as 4,4 under a heading of kPa.
    :param scientific: Whether this number's column is written as a mantissa
        and a power of ten, which is what a unit that takes no prefix falls
        back on. Decided once for the column by :func:`column_style`.
    :return: The number as the site should print it.
    """
    if value == 0:
        return "0"
    if not exact:
        value = round(value, _DERIVED_FIGURES - 1 - math.floor(math.log10(abs(value))))
    if scientific:
        mantissa, _, power = f"{value:e}".partition("e")
        written = str(int(power)).translate(_SUPERSCRIPT)
        return f"{_plain(float(mantissa)).replace('.', ',')} \u00d7 10{written}"
    whole, _, fraction = _plain(value, exponent).partition(".")
    grouped = f"{int(whole.lstrip('-')):,}".replace(",", _GROUP)
    if whole.startswith("-"):
        grouped = f"-{grouped}"
    return f"{grouped},{fraction}" if fraction else grouped


def values(catalogue: Mapping[str, CatalogueRow], field: str) -> Iterator[float]:
    """Every number a column holds, wherever in the row it is kept.

    :param catalogue: The catalogue.
    :param field: The quantity wanted.
    :return: The printed value, both ends of a range, and every reading of a
        cell that lists several.
    """
    for row in catalogue.values():
        value = getattr(row, field, None)
        if value is not None:
            yield value
        interval = row.ranges.get(field)
        if interval is not None:
            yield from (end for end in interval if end is not None)
        for entry in row.reported.get(field, ()):
            yield from entry if isinstance(entry, tuple) else (entry,)


def in_powers_of_ten(numbers: Iterable[float]) -> bool:
    """Whether a column of *numbers* is written as mantissa and power of ten.

    One decision for the whole column, so that a reader comparing down it
    compares like with like.

    :param numbers: Every number the column holds.
    :return: True when the middle of the column is at :data:`_BIG` or beyond,
        or below :data:`_TINY`, which is where digits stop being readable.
    """
    magnitudes = [abs(value) for value in numbers if value != 0]
    if not magnitudes:
        return False
    middle = statistics.median(magnitudes)
    return middle >= _BIG or middle < _TINY


def by_powers(catalogue: Mapping[str, CatalogueRow], field: str) -> bool:
    """Whether one catalogue column is written in powers of ten.

    :param catalogue: The catalogue.
    :param field: The quantity wanted.
    :return: What :func:`in_powers_of_ten` says about that column.
    """
    return in_powers_of_ten(values(catalogue, field))


class Style(NamedTuple):
    """How one column is written: its heading's unit and its cells' form.

    :ivar unit: The unit the heading carries, prefix included.
    :ivar exponent: Powers of ten taken out of every cell to match it.
    :ivar scientific: Whether the cells are a mantissa and a power of ten,
        which is where a unit that takes no prefix ends up.
    """

    unit: str
    exponent: int = 0
    scientific: bool = False


def column_style(unit: str, numbers: Iterable[float]) -> Style:
    """How to write a column of *numbers* whose quantity is in *unit*.

    A prefix in the heading beats a power of ten in every cell: a column of
    GPa reads as 62,11 and 23,17, where the same column in pascals reads as
    6,211 x 10^10 and 2,317 x 10^10, and a reader comparing two materials is
    comparing mantissas and exponents instead of numbers. So a unit that takes
    a prefix gets one, and only a unit that cannot (a squared metre, a unit
    that already carries a prefix, two quantities multiplied together) falls
    back on the power of ten.

    Which prefix is chosen by writing the whole column out under each one and
    keeping the shortest, which is what a reader means by the one that reads
    best: it is the prefix that leaves the fewest digits on the page, and it
    ties towards no prefix at all.

    :param unit: The unit of the quantity, as the heading has it.
    :param numbers: Every number the column holds.
    :return: The style that column is written in.
    """
    magnitudes = [value for value in numbers if value]
    if not magnitudes:
        return Style(unit)
    if unit not in _PREFIXABLE:
        return Style(unit, scientific=in_powers_of_ten(magnitudes))
    written = {
        exponent: sum(len(number(value, exponent=exponent)) for value in magnitudes)
        for exponent, _ in _PREFIXES
    }
    exponent = min(written, key=lambda power: (written[power], abs(power)))
    prefix = dict(_PREFIXES)[exponent]
    return Style(f"{prefix}{unit}", exponent)


#: The hedges that each give a served value a kind of its own, in the order
#: :func:`cell` asks for them.
_VALUE_HEDGES = ("derived", "converted", "carried", "approximate", "estimated")

#: The hedges :func:`cell` can show only on a single value. An interval, a
#: bound, a list of readings or a word reads with a kind of its own, and the
#: page has no way yet to say that one of those is also an estimate, a
#: conversion or carried from another row.
_SINGLE_VALUE_HEDGES = ("converted", "carried", "estimated")


def _hedges(row: CatalogueRow, field: str) -> list[str]:
    """The hedges of :data:`_VALUE_HEDGES` that *row* holds for *field*."""
    held = {
        "derived": row.is_derived(field),
        "converted": field in row.converted,
        "carried": field in row.carried,
        "approximate": row.is_approximate(field),
        "estimated": row.basis_of(field) == "estimated",
    }
    return [hedge for hedge in _VALUE_HEDGES if held[hedge]]


def _refuse_unshowable(row: CatalogueRow, field: str, value: object) -> None:
    """Refuse a cell whose hedges the page cannot show, rather than drop one.

    A cell has one kind, and the component styles and words it by that kind.
    Two hedges on one value, or a hedge that only a value can carry on a cell
    that holds an interval, a list or a word, would reach the page with one of
    them silently gone (a tilde on an interval or on a list of readings is
    written into its text, so ``approximate`` is refused only on a word): an estimated interval read as a plain range, or a
    converted bound whose note gives the converted number as what the page
    prints. No published cell does either today; the first one to do so stops
    the generator here, so that how it should read is decided rather than
    lost.

    :raises ValueError: naming the row, the field and the hedges.
    """
    hedges = _hedges(row, field)
    if value is not None:
        clash = hedges if len(hedges) > 1 else []
    else:
        spoken = (
            field in row.ranges or field in row.reported or field in row.unquantified
        )
        clash = [h for h in hedges if h in _SINGLE_VALUE_HEDGES] if spoken else []
        # An interval or a list of readings carries its tilde in the text; a
        # printed word has nowhere to put one.
        if field in row.unquantified and "approximate" in hedges:
            clash.append("approximate")
    if clash:
        what = "a value" if value is not None else "a cell with no single value"
        msg = (
            f"{row.name!r}: {field} is {' and '.join(clash)} on {what}, and a "
            "cell of the published page can show only one hedge, on a value"
        )
        raise ValueError(msg)


def cell(
    row: CatalogueRow, field: str, *, style: Style | None = None
) -> dict[str, Any]:
    """One cell, with the number and what the page said around it.

    :param row: The catalogue row.
    :param field: The quantity wanted.
    :param style: How the column is written, from :func:`column_style`. The
        default writes plain digits in the unit the quantity is stored in.
    :return: ``text`` to print, ``kind`` for the component to style by, and
        ``note`` for the hedge a reader needs to read the number correctly;
        a ``converted`` cell also carries ``printed``, the page's figure and
        its unit, which the component words in the reader's language.
    :raises ValueError: for a cell whose hedges the page cannot show, which
        :func:`_refuse_unshowable` describes.
    """
    style = style or Style("")
    written = functools.partial(
        number, exponent=style.exponent, scientific=style.scientific
    )
    value = getattr(row, field, None)
    # A year is a label and not a quantity: grouping its thousands would
    # print 1 989.
    if field == "year" and value is not None:
        return {"text": str(int(value)), "kind": "printed", "note": ""}
    _refuse_unshowable(row, field, value)
    if value is not None:
        # Three ways a served number is not simply what the cell printed, and
        # the row names each one in a mapping of its own: this library worked
        # it out (``derived``), the page gives it in another unit
        # (``converted``, with the page's figure and its unit), or the page
        # gives it by reference to another of its rows (``carried``). A
        # converted value is written like a derived one, to the figures its
        # inputs had, because the conversion is ours; a carried one is the
        # page's own number and keeps every digit. At most one of them, or of
        # the tilde and the estimate below, is on any cell that gets here.
        extra: dict[str, str] = {}
        kind, note = "printed", ""
        if row.is_derived(field):
            kind, note = "derived", row.derived[field]
        elif field in row.converted:
            figure, unit = row.converted[field]
            kind, extra = "converted", {"printed": f"{figure} {unit}"}
        elif field in row.carried:
            kind, note = "carried", row.carried[field]
        computed = kind in {"derived", "converted"}
        if row.is_approximate(field):
            kind, note = "approximate", "the page prints it with a tilde"
        # A number the source marks as its own estimate is served, so the
        # cell is not empty, and it is not a measurement, so it is not
        # "printed" either. What the source claims for a cell is its basis,
        # asked here the way every row answers it, so no catalogue can reach
        # the page with an estimate read as a reading. The note stays empty so
        # that the page reads the kind's own words, which it has in both
        # languages.
        if row.basis_of(field) == "estimated":
            kind, note, extra = "estimated", "", {}
        text = written(value, exact=not computed)
        # The plus-or-minus a page prints beside the value is written in the
        # cell, in the same unit, rather than left to a note nobody opens. It
        # is written the way every number here is, so a trailing zero the page
        # set (5.11 ± 0.20) is not carried: the row holds a float, not a string.
        spread = row.uncertainty.get(field)
        if spread is not None:
            text = f"{text} ± {written(spread)}"
        return {"text": text, "kind": kind, "note": note, **extra}
    interval = row.ranges.get(field)
    if interval is not None:
        low, high = interval
        if high is not None and field in row.bounded_above:
            text, kind = f"< {written(high)}", "bound"
        elif low is not None and field in row.bounded_below:
            # A lower bound reads as one. Before this branch existed a ">45"
            # was published as "45 to 1 000", a two-sided interval nobody
            # measured, and a bound whose open end is empty had no number to
            # print there at all.
            text, kind = f"> {written(low)}", "bound"
        else:
            text = " to ".join(written(end) for end in interval if end is not None)
            kind = "range"
        if row.is_approximate(field):
            # The page prints this interval with a tilde, as Cox Table 6.5 does
            # for the porosity of granular vermiculite. The range and bound
            # kinds have no mark of their own for it, so the tilde goes into
            # the text instead of being dropped.
            text = f"~{text}"
        return {"text": text, "kind": kind, "note": row.why_missing(field)}
    if field in row.reported:
        listed = ", ".join(
            f"{written(entry[0])} to {written(entry[1])}"
            if isinstance(entry, tuple)
            else written(entry)
            for entry in row.reported[field]
        )
        if row.is_approximate(field):
            # Same as an interval: the kind has no mark of its own for a tilde.
            listed = f"~{listed}"
        return {"text": listed, "kind": "reported", "note": row.why_missing(field)}
    if field in row.unquantified:
        return {
            "text": row.unquantified[field],
            "kind": "unquantified",
            "note": row.why_missing(field),
        }
    # A cell this library will not fill although the arithmetic would reach it
    # reads as empty, because the page is empty there; why it stays empty is
    # what the note says. A cell the page did fill and got wrong reads the same
    # way, and for the same reason: the table publishes what this library will
    # stand behind, and the note carries the printed number for a reader who is
    # checking the book rather than using it.
    if field in row.not_derivable or field in row.misprinted:
        return {"text": "", "kind": "absent", "note": row.why_missing(field)}
    return {"text": "", "kind": "absent", "note": ""}


def styles(
    catalogue: Mapping[str, CatalogueRow],
    columns: tuple[tuple[str, str, str, str], ...],
) -> dict[str, Style]:
    """How each column of *catalogue* is written.

    :param catalogue: The catalogue.
    :param columns: The columns to show, as ``(field, heading, heading in
        Spanish, unit)``.
    :return: The style of each column, by field name.
    """
    return {
        field: column_style(unit, values(catalogue, field))
        for field, _, _, unit in columns
    }


def printed_columns(
    catalogue: Mapping[str, CatalogueRow],
    columns: tuple[tuple[str, str, str, str], ...],
) -> tuple[tuple[str, str, str, str], ...]:
    """The columns at least one row of *catalogue* has something in.

    An absorption table declares a column for every octave band any book
    prints, and a given book prints six or seven of them; the site should not
    show a 63 Hz column of fifty-nine empty cells because two rows fill it in
    another table. A column stays when any row holds a value, a range, a
    listed cell, a word or a registered misprint in it, all of which the page
    printed something for.
    """

    def spoken(row: CatalogueRow, field: str) -> bool:
        return (
            getattr(row, field) is not None
            or field in row.ranges
            or field in row.reported
            or field in row.unquantified
            or field in row.misprinted
            or field in row.not_derivable
        )

    return tuple(
        column
        for column in columns
        if any(spoken(row, column[0]) for row in catalogue.values())
    )


def rows(
    catalogue: Mapping[str, CatalogueRow],
    columns: tuple[tuple[str, str, str, str], ...],
) -> Iterator[dict[str, Any]]:
    """Every row of a catalogue, formatted.

    :param catalogue: The catalogue.
    :param columns: The columns to show, as ``(field, heading, heading in
        Spanish, unit)``.
    :return: One record per row, in the catalogue's own order.
    """
    written = styles(catalogue, columns)
    for key, row in catalogue.items():
        table, _, _ = key.partition("/")
        yield {
            "key": key,
            "table": table,
            "name": row.name,
            "variant": row.variant,
            # The bold heading the row sits under, where the page prints one.
            # Four catalogues carry it and it is not decoration: a scattering
            # row reads "h = w = 10 cm, L = 2h" and means nothing without
            # "Periodic 1D battens" above it.
            "group": row.group,
            # Only the absorption tables carry a mounting, and only one book
            # prints one, so the field is empty on most rows and absent from
            # every other catalogue. The component shows the column when any
            # row of the catalogue fills it, the same rule the quantity
            # columns follow.
            "mounting": getattr(row, "mounting", ""),
            # An area row is an area per something, and which something is the
            # difference between a square metre of audience and a square metre
            # per cubic metre of air. The unit in the column heading cannot
            # say it, so the row carries it and the component gives it a
            # column of its own.
            "per": getattr(row, "per", ""),
            # Which solver produced a predicted row, or which model a fluid
            # state was closed with. It is text and not a quantity, so it
            # never goes through the cell formatter, and it has a column of
            # its own because a reader has to see it before using the number:
            # a coefficient a boundary element model computed and one a
            # reverberation room measured are not the same evidence.
            "model": getattr(row, "model", ""),
            # The words a row carries where another catalogue carries a
            # number, each one the thing that tells two otherwise identical
            # rows apart: which way the sound crossed a duct wall, what shape
            # that duct is, what gauge its sheet was, how a glass cloth is
            # woven. They follow the rule the mounting follows, which is that
            # the component shows the column when a row of the catalogue fills
            # it, so no catalogue pays for another's.
            "direction": getattr(row, "direction", ""),
            "shape": getattr(row, "shape", ""),
            "gauge": getattr(row, "sheet_metal_gauge", ""),
            "weave": getattr(row, "weave_construction", ""),
            # The bonding of a solid, which the nonlinearity table prints
            # beside each structure and which is a word, not a quantity.
            "bonding": getattr(row, "bonding", ""),
            "source": row.source,
            "note": row.note,
            "attributedTo": dict(row.attributed_to),
            "cells": [
                cell(row, field, style=written[field]) for field, _, _, _ in columns
            ],
        }


#: The named air of this library that does not live in the fluids catalogue,
#: keyed the way the catalogue keys its own rows. Each sits beside the model or
#: the standard that fixes it, which is where it belongs: ``fluids`` is part of
#: the transverse toolbox, so a catalogue there that imported ``materials``,
#: ``building`` and ``simulation`` to gather them would make the medium depend
#: on three of the domains that stand on it. A script is free to import the
#: whole tree, so the comparison a reader wants is assembled here, where it
#: costs the library nothing.
IN_TREE_FLUIDS = {
    "iec-61094-2-annex-f/air": ANNEX_A_AIR,
    "en-12354-annex-a/air": EN_12354_AIR,
    "allard-2009-jca/air": PUBLISHED_AIR,
    "phonometry-solver/air": SIMULATION_AIR,
}


def fluids() -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    """The fluid states, which are not rows of a table and do not format alike.

    A :class:`~phonometry.fluids.Fluid` carries a temperature, a pressure and
    whatever properties its model fixed, which differ from one state to the
    next: the metrology annex's air knows its thermal conductivity and the
    building standard's air knows a density and a speed and nothing else. So
    the columns are the union of what the states carry, and a state that does
    not determine a quantity leaves the cell empty rather than borrowing one.

    The states read from a page come first, then the four the tree carries
    elsewhere, which is the order that puts the airs of the four documents
    next to each other where their disagreement is visible.

    :return: The columns, headings and units included, and one record per
        state.
    """
    quantities = (
        ("speed_of_sound", "Speed of sound", "Velocidad del sonido", "m/s"),
        ("density", "Density", "Densidad", "kg/m³"),
        ("viscosity", "Viscosity", "Viscosidad", "Pa·s"),
        (
            "heat_capacity_ratio",
            "Heat capacity ratio",
            "Relación de calores específicos",
            "",
        ),
    )
    states = {**PUBLISHED_FLUIDS, **IN_TREE_FLUIDS}
    # The same decision the material columns take, made the same way: a
    # viscosity of 0,0000184 Pa s is a column of leading zeros, and moving the
    # prefix into the heading makes it 18,4 µPa·s.
    written = {
        name: column_style(
            unit,
            [
                state.properties[name]
                for state in states.values()
                if name in state.properties
            ],
        )
        for name, _, _, unit in quantities
    }
    columns = [
        {
            "field": name,
            "heading": heading,
            "headingEs": spanish,
            "unit": written[name].unit,
        }
        for name, heading, spanish, _ in quantities
    ]
    # A state is a physical state and keeps neither the name the page prints
    # nor the row's note, so both are read back from the data file the state
    # came from. The name is the printed one: the key carries a temperature
    # to tell two rows of one substance apart, and "Hydrogen 0c" is not
    # anything a page printed. The temperature has a column of its own.
    printed: dict[str, dict[str, Any]] = {}
    for table in {key.partition("/")[0] for key in PUBLISHED_FLUIDS}:
        _, records = read_table("phonometry.fluids", f"{table}.json")
        printed.update({f"{table}/{record['key']}": record for record in records})
    out: list[dict[str, Any]] = []
    for key, state in states.items():
        # A state read from a table and a state a model fixes are different
        # kinds of number, and the cell says which: 343 m/s is what Bies
        # printed, where the 345,86652 m/s of the metrology annex is what its
        # closed form returns at the conditions that annex assumes.
        kind = "printed" if key in PUBLISHED_FLUIDS else "fixed"
        record = printed.get(key, {})
        note = record.get("note", "")
        # Every note a fluid row carries is about its density, the one column
        # a page has been caught repeating; a note about anything else has to
        # say which cell it belongs on before it can be placed.
        if note and "density" not in note:
            msg = f"{key}: a fluid row note has to name the cell it is about"
            raise ValueError(msg)
        out.append(
            {
                "key": key,
                "table": key.partition("/")[0],
                "name": record.get("name")
                or key.rpartition("/")[2].replace("_", " ").capitalize(),
                "temperature": number(state.temperature_c),
                "pressure": number(state.static_pressure_pa),
                "model": state.model,
                "validity": state.validity,
                "cells": [
                    {
                        "text": number(
                            state.properties[name],
                            exponent=written[name].exponent,
                            scientific=written[name].scientific,
                        )
                        if name in state.properties
                        else "",
                        "kind": kind if name in state.properties else "absent",
                        "note": note if name == "density" else "",
                    }
                    for name, _, _, _ in quantities
                ],
            }
        )
    return columns, out


#: Where the air attenuation was read, spelled the way a packaged data file of
#: that table would be named. Its rows are the six conditions the standard
#: tabulates rather than six materials, held as a mapping of arrays in the
#: module that computes with them, so they carry no table name to key them by
#: and the page needs one: the filter that picks a published table reads it,
#: and a row without one would be filed under the empty string.
AIR_ATTENUATION_TABLE = "en-12354-6-table-1"

#: Significant figures the air attenuation table prints, which is what its
#: coefficients are written back to here. The standard prints them in
#: thousandths of a neper per metre and the library holds them in neper per
#: metre, so each one reached the package through a multiplication by a
#: thousandth, and that multiplication does not round-trip in binary: the
#: 1,8 the page prints is held as 0,001 800 000 000 000 000 2. Every digit a
#: float carries is what a number read off a page earns, and those last
#: fifteen are not digits this page printed. Three is the most any cell of the
#: table has, so nothing printed is lost by writing them back to three.
_AIR_ATTENUATION_FIGURES = 3


def transcribed(
    records: list[dict[str, Any]],
    columns: tuple[tuple[str, str, str, str], ...],
) -> dict[str, Any]:
    """A catalogue whose cells are numbers and nothing else.

    Most of these catalogues are rows of
    :class:`~phonometry.io.CatalogueRow`, which carries the
    intervals, the bounds, the listed readings and the words a page can print
    where a number would go, and :func:`section` reads all of that back. One
    is not: the air attenuation is a mapping of arrays. Its page hedges
    nothing, so there is nothing for the hedges to carry, and what it needs is
    the column styles and the number formatting the rest of the page is
    written in. That is what this is, and it is why it is not a second set of
    rules: a cell here goes through the same :func:`column_style` and the same
    :func:`number` as every other cell on the page.

    :param records: One per row: its ``key``, the ``table`` it belongs to, its
        ``name``, its ``source``, the ``values`` it holds by field name, and
        optionally a ``note`` and an ``attributedTo``.
    :param columns: The columns, as ``(field, heading, heading in Spanish,
        unit)``.
    :return: The catalogue as the site's page wants it.
    """
    written = {
        field: column_style(
            unit,
            [
                record["values"][field]
                for record in records
                if field in record["values"]
            ],
        )
        for field, _, _, unit in columns
    }
    return {
        "columns": [
            {
                "field": field,
                "heading": heading,
                "headingEs": spanish,
                "unit": written[field].unit,
            }
            for field, heading, spanish, _ in columns
        ],
        "rows": [
            {
                "key": record["key"],
                "table": record["table"],
                "name": record["name"],
                "variant": "",
                "group": "",
                "mounting": "",
                "per": "",
                "model": "",
                "direction": "",
                "shape": "",
                "gauge": "",
                "weave": "",
                "bonding": "",
                "source": record["source"],
                "note": record.get("note", ""),
                "attributedTo": record.get("attributedTo", {}),
                "cells": [
                    {
                        "text": number(
                            record["values"][field],
                            exponent=written[field].exponent,
                            scientific=written[field].scientific,
                        ),
                        "kind": "printed",
                        "note": "",
                    }
                    if field in record["values"]
                    else {"text": "", "kind": "absent", "note": ""}
                    for field, _, _, _ in columns
                ],
            }
            for record in records
        ],
    }


def air_conditions() -> list[dict[str, Any]]:
    """The six air conditions of the room standard's own attenuation table.

    The name is read off the key rather than written out again, because the
    key is how the library spells the condition and a second spelling of
    ``20C_50-70`` would be a second thing to keep in step with the first.

    :return: One record per condition, in the order the table prints them.
    """
    records = []
    for key, coefficients in AIR_ATTENUATION.items():
        temperature, _, humidity = key.partition("_")
        recommended = key == PUBLISHED_AIR_CONDITION
        records.append(
            {
                "key": f"{AIR_ATTENUATION_TABLE}/{key}",
                "table": AIR_ATTENUATION_TABLE,
                "name": f"{temperature.removesuffix('C')} °C, {humidity} %",
                "source": "EN 12354-6:2003 Table 1",
                "note": "The condition clause 4.3 recommends when the room's "
                "own temperature and humidity are not known."
                if recommended
                else "",
                "values": {
                    f"air_attenuation_{int(band)}_np_m": float(
                        f"{coefficient:.{_AIR_ATTENUATION_FIGURES}g}"
                    )
                    for band, coefficient in zip(
                        OCTAVE_BANDS, coefficients, strict=True
                    )
                },
            }
        )
    return records


def section(
    catalogue: Mapping[str, CatalogueRow],
    columns: tuple[tuple[str, str, str, str], ...],
) -> dict[str, Any]:
    """One catalogue as the site's page wants it: its columns and its rows."""
    shown = printed_columns(catalogue, columns)
    written = styles(catalogue, shown)
    return {
        "columns": [
            {
                "field": field,
                "heading": heading,
                "headingEs": spanish,
                "unit": written[field].unit,
            }
            for field, heading, spanish, _ in shown
        ],
        "rows": list(rows(catalogue, shown)),
    }


def render() -> str:
    """The module the site imports.

    :return: Its whole text, ending in a newline.
    """
    import json

    solid_styles = styles(PUBLISHED_SOLIDS, SOLID_COLUMNS)
    porous_styles = styles(PUBLISHED_POROUS, POROUS_COLUMNS)
    ground_styles = styles(PUBLISHED_GROUND, GROUND_COLUMNS)
    gas_styles = styles(PUBLISHED_GASES, GAS_COLUMNS)
    fluid_columns, fluid_rows = fluids()
    document = {
        "solids": {
            "columns": [
                {
                    "field": field,
                    "heading": heading,
                    "headingEs": spanish,
                    "unit": solid_styles[field].unit,
                }
                for field, heading, spanish, _ in SOLID_COLUMNS
            ],
            "rows": list(rows(PUBLISHED_SOLIDS, SOLID_COLUMNS)),
        },
        "porous": {
            "columns": [
                {
                    "field": field,
                    "heading": heading,
                    "headingEs": spanish,
                    "unit": porous_styles[field].unit,
                }
                for field, heading, spanish, _ in POROUS_COLUMNS
            ],
            "rows": list(rows(PUBLISHED_POROUS, POROUS_COLUMNS)),
        },
        "ground": {
            "columns": [
                {
                    "field": field,
                    "heading": heading,
                    "headingEs": spanish,
                    "unit": ground_styles[field].unit,
                }
                for field, heading, spanish, _ in GROUND_COLUMNS
            ],
            "rows": list(rows(PUBLISHED_GROUND, GROUND_COLUMNS)),
        },
        "gases": {
            "columns": [
                {
                    "field": field,
                    "heading": heading,
                    "headingEs": spanish,
                    "unit": gas_styles[field].unit,
                }
                for field, heading, spanish, _ in GAS_COLUMNS
            ],
            "rows": list(rows(PUBLISHED_GASES, GAS_COLUMNS)),
        },
        "damping": section(PUBLISHED_DAMPING, DAMPING_COLUMNS),
        "dampingTreatments": section(
            PUBLISHED_DAMPING_TREATMENTS, DAMPING_TREATMENT_COLUMNS
        ),
        "orthotropicWood": section(PUBLISHED_ORTHOTROPIC_WOOD, WOOD_COLUMNS),
        "plateau": section(PUBLISHED_PLATEAU_DATA, PLATEAU_COLUMNS),
        "nonlinearity": section(PUBLISHED_NONLINEARITY, NONLINEARITY_COLUMNS),
        "solidNonlinearity": section(
            PUBLISHED_SOLID_NONLINEARITY, SOLID_NONLINEARITY_COLUMNS
        ),
        "flowResistance": section(PUBLISHED_FLOW_RESISTANCE, FLOW_RESISTANCE_COLUMNS),
        "resilientLayers": section(PUBLISHED_RESILIENT_LAYERS, RESILIENT_LAYER_COLUMNS),
        "resilientModuli": section(
            PUBLISHED_RESILIENT_MODULI, RESILIENT_MODULUS_COLUMNS
        ),
        "absorption": section(PUBLISHED_ABSORPTION, ABSORPTION_COLUMNS),
        "carpets": section(PUBLISHED_CARPETS, CARPET_COLUMNS),
        "transmissionLoss": section(
            PUBLISHED_TRANSMISSION_LOSS, TRANSMISSION_LOSS_COLUMNS
        ),
        "impactInsulation": section(
            PUBLISHED_IMPACT_INSULATION, IMPACT_INSULATION_COLUMNS
        ),
        "ductTransmissionLoss": section(
            PUBLISHED_DUCT_TRANSMISSION_LOSS, DUCT_TRANSMISSION_LOSS_COLUMNS
        ),
        "scattering": section(PUBLISHED_SCATTERING, SCATTERING_COLUMNS),
        "diffusion": section(PUBLISHED_DIFFUSION, DIFFUSION_COLUMNS),
        "predictedScattering": section(
            PUBLISHED_PREDICTED_SCATTERING, PREDICTED_SCATTERING_COLUMNS
        ),
        "absorptionAreas": section(PUBLISHED_ABSORPTION_AREAS, ABSORPTION_AREA_COLUMNS),
        "fluids": {"columns": fluid_columns, "rows": fluid_rows},
        "airAttenuation": transcribed(air_conditions(), AIR_ATTENUATION_COLUMNS),
    }
    body = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=False)
    return (
        "// Auto-generated by scripts/generate_catalogue_data.py "
        "(make catalogue-data).\n"
        "// Do not edit by hand.\n"
        f"export const catalogues = {body};\n"
    )


def render_types() -> str:
    """The declarations for the module :func:`render` writes.

    ``catalogues.mjs`` is a JSON literal, and a structural type checker infers
    one type per table straight off the values that happen to be in it: two
    tables whose rows carry exactly the same fields still read as unrelated
    types the moment one of them lacks a row that fills every field, and a
    page reading a row generically then meets a union of a dozen near
    duplicates instead of the one shape it actually has. TypeScript pairs a
    ``.mjs`` module with a sibling ``.d.mts`` of the same name before it falls
    back to inferring one, so writing the shape here once is what a page
    reading the module sees instead.

    One row shape covers every table. :func:`rows` and :func:`transcribed`
    build the same fields for the twenty-three catalogues that are a table of
    materials or states with a name and a source; :func:`fluids` builds the
    physical properties of a state instead, which has no name for a variant
    or a group and carries a temperature and a pressure that no material
    table does. Every page that reads a row already treats these fields as
    present-or-not (``row.note &&`` ...), which is exactly what marking them
    optional here says: a table that never fills a field leaves the property
    off, the reader sees ``undefined``, and nothing here claims it is always
    there.

    :return: The declaration file's whole text, ending in a newline.
    """
    table_fields = "\n".join(f"\t{key}: CatalogueTable;" for key in _TABLE_KEYS)
    return (
        "// Auto-generated by scripts/generate_catalogue_data.py "
        "(make catalogue-data).\n"
        "// Do not edit by hand.\n"
        "\n"
        "/** What the page prints in a cell, and how it got there. */\n"
        "export type CatalogueCellKind =\n"
        "\t| 'printed'\n"
        "\t| 'fixed'\n"
        "\t| 'derived'\n"
        "\t| 'converted'\n"
        "\t| 'carried'\n"
        "\t| 'approximate'\n"
        "\t| 'estimated'\n"
        "\t| 'range'\n"
        "\t| 'bound'\n"
        "\t| 'reported'\n"
        "\t| 'unquantified'\n"
        "\t| 'absent';\n"
        "\n"
        "export interface CatalogueCell {\n"
        "\ttext: string;\n"
        "\tkind: CatalogueCellKind;\n"
        "\tnote: string;\n"
        "\t/** The figure and the unit the page prints, on a converted cell. */\n"
        "\tprinted?: string;\n"
        "}\n"
        "\n"
        "export interface CatalogueColumn {\n"
        "\tfield: string;\n"
        "\theading: string;\n"
        "\theadingEs: string;\n"
        "\tunit: string;\n"
        "}\n"
        "\n"
        "/**\n"
        " * One row of one published table. `key`, `table`, `name` and `cells`\n"
        " * are on every row of every table; everything else is a field only\n"
        " * some tables fill; `temperature`, `pressure` and `validity` are only\n"
        " * `fluids()`'s, and the rest are only `rows()`'s and `transcribed()`'s,\n"
        " * in generate_catalogue_data.py.\n"
        " */\n"
        "export interface CatalogueRow {\n"
        "\tkey: string;\n"
        "\ttable: string;\n"
        "\tname: string;\n"
        "\tcells: CatalogueCell[];\n"
        "\tvariant?: string;\n"
        "\tgroup?: string;\n"
        "\tmounting?: string;\n"
        "\tper?: string;\n"
        "\tmodel?: string;\n"
        "\tdirection?: string;\n"
        "\tshape?: string;\n"
        "\tgauge?: string;\n"
        "\tweave?: string;\n"
        "\tbonding?: string;\n"
        "\tsource?: string;\n"
        "\tnote?: string;\n"
        "\tattributedTo?: Record<string, string>;\n"
        "\ttemperature?: string;\n"
        "\tpressure?: string;\n"
        "\tvalidity?: string;\n"
        "}\n"
        "\n"
        "export interface CatalogueTable {\n"
        "\tcolumns: CatalogueColumn[];\n"
        "\trows: CatalogueRow[];\n"
        "}\n"
        "\n"
        "export interface Catalogues {\n"
        f"{table_fields}\n"
        "}\n"
        "\n"
        "export declare const catalogues: Catalogues;\n"
    )


def main(argv: list[str] | None = None) -> int:
    """Write the module, or check that the committed one is current.

    :param argv: Command line, for the tests.
    :return: The process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero when the committed file differs from a fresh run",
    )
    args = parser.parse_args(argv)
    fresh = render()
    fresh_types = render_types()
    if args.check:
        stale = [
            path
            for path, text in ((OUTPUT, fresh), (TYPES_OUTPUT, fresh_types))
            if (path.read_text(encoding="utf-8") if path.is_file() else "") != text
        ]
        if stale:
            for path in stale:
                print(
                    f"{path.relative_to(path.parents[3])} is stale; "
                    "run `make catalogue-data`.",
                    file=sys.stderr,
                )
            return 1
        print(f"{OUTPUT.name} is current.")
        return 0
    OUTPUT.write_text(fresh, encoding="utf-8")
    TYPES_OUTPUT.write_text(fresh_types, encoding="utf-8")
    counts = {
        "solids": len(PUBLISHED_SOLIDS),
        "damping materials": len(PUBLISHED_DAMPING),
        "orthotropic woods": len(PUBLISHED_ORTHOTROPIC_WOOD),
        "plateau materials": len(PUBLISHED_PLATEAU_DATA),
        "damping treatments": len(PUBLISHED_DAMPING_TREATMENTS),
        "resilient moduli": len(PUBLISHED_RESILIENT_MODULI),
        "carpets": len(PUBLISHED_CARPETS),
        "nonlinearity values": len(PUBLISHED_NONLINEARITY),
        "solid nonlinearity": len(PUBLISHED_SOLID_NONLINEARITY),
        "ground": len(PUBLISHED_GROUND),
        "porous": len(PUBLISHED_POROUS),
        "resistive facings": len(PUBLISHED_FLOW_RESISTANCE),
        "resilient layers": len(PUBLISHED_RESILIENT_LAYERS),
        "gases": len(PUBLISHED_GASES),
        "absorption": len(PUBLISHED_ABSORPTION),
        "transmission loss": len(PUBLISHED_TRANSMISSION_LOSS),
        "impact insulation": len(PUBLISHED_IMPACT_INSULATION),
        "duct walls": len(PUBLISHED_DUCT_TRANSMISSION_LOSS),
        "scattering": len(PUBLISHED_SCATTERING),
        "diffusion": len(PUBLISHED_DIFFUSION),
        "predicted scattering": len(PUBLISHED_PREDICTED_SCATTERING),
        "absorption areas": len(PUBLISHED_ABSORPTION_AREAS),
        "fluids": len(PUBLISHED_FLUIDS) + len(IN_TREE_FLUIDS),
        "air conditions": len(AIR_ATTENUATION),
    }
    print(f"{OUTPUT.name}: " + ", ".join(f"{n} {k}" for k, n in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
