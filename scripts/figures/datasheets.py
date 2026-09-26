#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Figures for the guide on reading a material datasheet.

Each is a row read from the kind of document the guide describes, rated
again from its bands, and drawn by the rating's own ``.plot()``: what a user
gets back after typing a test report into a catalogue of their own. The
bands are the worked examples of the standards, the same ones the tests and
the guide use: ISO 11654 Annex C for the one-third-octave absorption, ISO
717-1 Annex C for the sound reduction index over 50 Hz to 5 kHz, and ISO
717-2 Annex C, Table C.2 for the reduction of impact sound pressure level.
Embedded by ``docs/materials/reading-a-datasheet.md`` and its site twins.
"""

from typing import Any

import matplotlib.pyplot as plt

from .i18n import _LANG
from .theme import save_figure

#: ISO 11654 Annex C: the one-third-octave coefficients of ISO 354.
_ABSORPTION_BANDS_HZ: tuple[int, ...] = (
    *(100, 125, 160, 200, 250, 315, 400, 500, 630, 800),
    *(1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000),
)
_ALPHA_S: tuple[float, ...] = (
    *(0.12, 0.15, 0.17, 0.21, 0.31, 0.51, 0.54, 0.80, 0.93, 1.05),
    *(1.10, 1.19, 1.20, 1.13, 1.02, 0.99, 0.94, 0.81),
)

#: ISO 717-1 Annex C, Tables C.1 and C.2: R from 50 Hz to 5 kHz.
_REDUCTION_BANDS_HZ: tuple[int, ...] = (
    50,
    63,
    80,
    *_ABSORPTION_BANDS_HZ[:-2],
    4000,
    5000,
)
_R_DB: tuple[float, ...] = (
    *(18.7, 19.2, 20.0, 20.4, 16.3, 17.7, 22.6, 22.4, 22.7, 24.8, 26.6),
    *(28.0, 30.5, 31.8, 32.5, 33.4, 33.0, 31.0, 25.5, 26.8, 29.2),
)

#: ISO 717-2 Annex C, Table C.2: Delta L from 100 Hz to 3.15 kHz.
_IMPROVEMENT_BANDS_HZ: tuple[int, ...] = _ABSORPTION_BANDS_HZ[:-2]
_DELTA_L_DB: tuple[float, ...] = (
    *(3.0, 3.7, 1.9, 3.0, 3.2, 3.5, 4.0, 6.1, 6.7, 7.0, 7.7, 10.8),
    *(15.2, 20.3, 25.4, 23.2),
)


def generate_datasheet_absorption_rating(output_dir: str) -> None:
    """A test report's one-third octaves rated to alpha_w (ISO 11654 Annex C)."""
    print("Generating datasheet_absorption_rating...")
    from phonometry import materials

    cells: dict[str, Any] = {
        f"absorption_coefficient_{band}": alpha
        for band, alpha in zip(_ABSORPTION_BANDS_HZ, _ALPHA_S, strict=True)
    }
    panel = materials.ThirdOctaveAbsorptionSpectrum(
        name="Panel 40", source="Sound absorption test report 26-015", **cells
    )
    _, ax = plt.subplots(figsize=(10, 6))
    # The rating's own .plot(): the practical coefficients of the five rating
    # octaves against the shifted reference curve, 0.65(MH), class C.
    panel.rating().plot(ax=ax, language=_LANG)
    plt.tight_layout()
    save_figure(output_dir, "datasheet_absorption_rating.svg")
    plt.close()


def generate_datasheet_sound_reduction_rating(output_dir: str) -> None:
    """A laboratory report's R rated to Rw(C; Ctr) with the Annex B terms."""
    print("Generating datasheet_sound_reduction_rating...")
    from phonometry import building

    cells: dict[str, Any] = {
        f"sound_reduction_index_{band}_db": r
        for band, r in zip(_REDUCTION_BANDS_HZ, _R_DB, strict=True)
    }
    partition = building.SoundReductionSpectrum(
        name="Glazed partition",
        source="Airborne sound insulation test report 26-021",
        **cells,
    )
    _, ax = plt.subplots(figsize=(10, 6))
    partition.rating().plot(ax=ax, language=_LANG)
    plt.tight_layout()
    save_figure(output_dir, "datasheet_sound_reduction_rating.svg")
    plt.close()


def generate_datasheet_impact_improvement_rating(output_dir: str) -> None:
    """A covering's Delta L rated to Delta Lw, CI,Delta and CI,r (ISO 717-2)."""
    print("Generating datasheet_impact_improvement_rating...")
    from phonometry import building

    cells: dict[str, Any] = {
        f"impact_improvement_{band}_db": delta_l
        for band, delta_l in zip(_IMPROVEMENT_BANDS_HZ, _DELTA_L_DB, strict=True)
    }
    covering = building.ImpactImprovementSpectrum(
        name="Floor covering",
        source="Impact sound insulation test report 26-022",
        **cells,
    )
    _, ax = plt.subplots(figsize=(10, 6))
    covering.rating().plot(ax=ax, language=_LANG)
    plt.tight_layout()
    save_figure(output_dir, "datasheet_impact_improvement_rating.svg")
    plt.close()
