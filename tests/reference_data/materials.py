#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Acoustic materials: absorption, airflow resistance, scattering, diffusion.

What a surface does to sound that arrives at it. The absorption side runs
from the impedance tube (ISO 10534-1) and the airflow resistance
(ISO 9053-2) through the empirical porous models (Delany-Bazley, Miki) and
the microperforated panel of Maa to the single-number rating of ISO 11654
and its uncertainty in ISO 12999-2; the in-situ method of ISO 13472 sits
beside them because it measures the same quantity on a road surface.

The scattering side is the same surface answered differently: the random
incidence scattering coefficient of ISO 17497-1, the directional diffusion
coefficient of ISO 17497-2 and the quadratic-residue diffuser that Cox and
D'Antonio work through in Appendix B of the third edition.
"""

from __future__ import annotations

from phonometry.fluids import Fluid

# ---------------------------------------------------------------------------
# ISO 11654:1997 rating of sound absorption — the two normative worked examples
# of Annex A. Both use the same practical-coefficient spectrum except at 500 Hz;
# A.1 gives alpha_w = 0,60 with no shape indicator, A.2 (500 Hz raised to 1,00)
# gives alpha_w = 0,60(M). Bands are 250/500/1000/2000/4000 Hz. Mirrors
# tests/materials/absorbers/test_absorption_rating.py.
# ---------------------------------------------------------------------------
ISO11654_ANNEX_A1_ALPHA_P: tuple[float, ...] = (0.35, 0.70, 0.65, 0.60, 0.55)
ISO11654_ANNEX_A1_ALPHA_W = 0.60
ISO11654_ANNEX_A1_CLASS = "C"
ISO11654_ANNEX_A1_INDICATOR = ""
ISO11654_ANNEX_A2_ALPHA_P: tuple[float, ...] = (0.35, 1.00, 0.65, 0.60, 0.55)
ISO11654_ANNEX_A2_ALPHA_W = 0.60
ISO11654_ANNEX_A2_INDICATOR = "M"

# ---------------------------------------------------------------------------
# ISO 9053-2:2020 alternating-method airflow resistance — the Annex A.3 worked
# example of the effective ratio of specific heats. A closed cylinder 100 mm x
# 100 mm gives V = 7,854e-4 m3 and S = 0,0471 m2; at f = 2 Hz the standard
# prints the wavelength 172,9 m, the thermal boundary layer b = 1,83e-3 m and
# the heat-conduction-corrected kappa' = kappa*0,978 = 1,370. Mirrors
# tests/materials/absorbers/test_airflow_resistance.py.
#
# The five air properties below are the ones Annex A.3 PRINTS, on printed folios
# 13 and 14. The worked example is computed from them, so they are the inputs
# the conformance rows pass. They are not the library defaults: Annex A.3
# credits all five to IEC 61094-2:2009, and two of them cannot be found there.
# See docs/ERRATA.md.
# ---------------------------------------------------------------------------
ISO9053_2_ANNEX_A_SURFACE = 0.0471  # S (m2)
ISO9053_2_ANNEX_A_VOLUME = 7.854e-4  # V (m3)
ISO9053_2_ANNEX_A_FREQUENCY = 2.0  # f (Hz)
ISO9053_2_ANNEX_A_WAVELENGTH = 172.9  # lambda = c0/f (m)
ISO9053_2_ANNEX_A_BOUNDARY_LAYER = 1.83e-3  # b (m)
ISO9053_2_ANNEX_A_KAPPA_PRIME = 1.370  # kappa' = kappa*0,978

#: The air properties as printed in Annex A.3, folios 13 and 14, as the `Fluid`
#: the two helpers now take. Transcribed here rather than imported from the
#: library, so that the rows built on it stay an independent oracle.
ISO9053_2_ANNEX_A_PRINTED_AIR = Fluid(
    temperature_c=23.0,
    static_pressure_pa=101_325.0,
    composition={"relative_humidity_percent": 50.0},
    model="ISO 9053-2:2020 Annex A.3 as printed, folios 13 and 14",
    validity="",
    properties={
        "speed_of_sound": 345.9,  # c0 (m/s)
        "density": 1.186,  # rho0 (kg/m3)
        "heat_capacity_ratio": 1.4008,  # kappa, adiabatic
        "specific_heat_capacity": 938.7,  # C_P (J/(kg*K))
        "thermal_conductivity": 0.02355,  # k_a (J/(s*m*K))
    },
)

# ---------------------------------------------------------------------------
# ISO 10534-1:1996 standing-wave-ratio method — closed-form physics oracle from
# Eqs (13)/(14)/(9): a standing-wave ratio s = 3 gives |r| = (s-1)/(s+1) = 0,5
# and absorption alpha = 1 - |r|^2 = 0,75.
# ---------------------------------------------------------------------------
ISO10534_1_SWR = 3.0
ISO10534_1_REFLECTION_MAGNITUDE = 0.5
ISO10534_1_ABSORPTION = 0.75

# ---------------------------------------------------------------------------
# ISO 17497-1:2004 random-incidence scattering coefficient. Eq (2) fixes the
# reference speed of sound c = 343,2 m/s at 20 C. The synthetic worked chain
# (T1..T4 = 8,0/6,0/7,5/5,0 s, V/S from V = 200 m3, S = 10 m2) exercises the
# Sabine absorptions Eq (1)/(4) and the scattering Eq (5). Mirrors
# tests/materials/diffusers/test_scattering_diffusion.py.
# ---------------------------------------------------------------------------
ISO17497_1_SPEED_OF_SOUND_20C = 343.2  # Eq (2) reference condition (m/s)
ISO17497_1_CHAIN_V = 200.0  # chamber volume V (m3)
ISO17497_1_CHAIN_S = 10.0  # sample area S (m2)
ISO17497_1_CHAIN_C = 343.2  # speed of sound used throughout (m/s)
ISO17497_1_CHAIN_T: tuple[float, float, float, float] = (8.0, 6.0, 7.5, 5.0)
ISO17497_1_CHAIN_ALPHA_S = 0.1342754467754468  # random-incidence absorption
ISO17497_1_CHAIN_ALPHA_SPEC = 0.21484071484071485  # specular absorption
ISO17497_1_CHAIN_SCATTERING = 0.09306108711505018  # s = (a_spec-a_s)/(1-a_s)
# Annex A.5 combined uncertainty of the scattering coefficient. For
# a_spec = 0,6, a_s = 0,3 with u(a_spec) = 0,02 and u(a_s) = 0,01 the
# error-propagation form gives u(s) = 0,0297.
ISO17497_1_A5_ALPHA_SPEC = 0.6
ISO17497_1_A5_ALPHA_S = 0.3
ISO17497_1_A5_U_ALPHA_SPEC = 0.02
ISO17497_1_A5_U_ALPHA_S = 0.01
ISO17497_1_A5_U_SCATTERING = 0.0297147342419613  # combined u(s)

# ---------------------------------------------------------------------------
# ISO 17497-2:2012 directional diffusion coefficient d_theta, Formula (5).
# Arithmetic oracle on the standard single-plane semicircular receiver arc
# (37 receivers at 5 deg spacing, -90..+90 deg): the committed levels are
# GENERATED BY THIS LIBRARY'S OWN Fraunhofer far-field phase-grating model
# (materials/diffusers/design.py, Cox & D'Antonio Eq. (5.8)/(9.32)) for a
# published diffuser geometry; they are model output, not third-party data.
# The independent external anchor against published third-party BEM values is
# the Cox & D'Antonio Appendix B comparison further below.
#
# Geometry (published): an N = 7 quadratic-residue diffuser, 6 periods,
# 3.6 m total width, 0.2 m maximum well depth - the "N = 7 QRD, 6 periods,
# 0.2 m deep" row of Cox & D'Antonio, "Acoustic Absorbers and Diffusers",
# 3rd ed. (2017), Appendix B section 7 (Schroeder diffusers, 3.6 m wide).
# The commercial single-plane QRD measured by Hargreaves, Cox, Lam & D'Antonio,
# J. Acoust. Soc. Am. 108(4), 1710-1720 (2000), Table I is the same diffuser
# family (N = 7, 0.2 m maximum well depth). Period 3.6/6 = 0.6 m, well width
# 3.6/42 m; well depths d_n = s_n lambda0 / (2 N) (Eq. (10.3), s_n = n^2 mod 7)
# with design frequency f0 = 490 Hz (c = 343 m/s), so the deepest well
# (s_max = 4) is exactly 0.2 m: depths = (0, 0.05, 0.2, 0.1, 0.1, 0.2, 0.05) m.
# Prediction at 1000 Hz, normal incidence. The flat reference is the model's
# own normalisation pathway: the same 3.6 m footprint with all wells at zero
# depth (Hargreaves et al. used a 0.57 m plane panel; the Fraunhofer model
# normalises against the equal-footprint flat panel instead, as
# predicted_diffusion_spectrum does).
#
# Levels are peak-referenced (0 dB at the maximum; Formula (5) is invariant
# to a constant level shift), rounded to 1e-3 dB; the coefficients below are
# recomputed from the rounded committed levels, so the conformance/test
# tolerance is a tight 1e-6 (exact arithmetic on the committed levels). Six
# periods of a periodic QRD concentrate the reflected energy into grating
# lobes, so d_theta is modest - consistent with the low published Appendix B
# values for periodic arrays (Cox & D'Antonio section 5.2.5).
ISO17497_2_QRD_N = 7  # quadratic-residue prime N
ISO17497_2_QRD_PERIODS = 6  # periods across the 3.6 m array
ISO17497_2_QRD_TOTAL_WIDTH = 3.6  # m, published total array width
ISO17497_2_QRD_WELL_WIDTH = 3.6 / 42  # m, period 0.6 m / N = 7 wells
ISO17497_2_QRD_MAX_DEPTH = 0.2  # m, published maximum well depth
ISO17497_2_QRD_DESIGN_FREQUENCY = 490.0  # Hz, gives the 0.2 m deepest well
ISO17497_2_SPEED_OF_SOUND = 343.0  # m/s, used throughout the prediction
ISO17497_2_PREDICTION_FREQUENCY = 1000.0  # Hz, single-frequency arc below
ISO17497_2_QRD_LEVELS: tuple[float, ...] = (
    -19.337,
    -18.867,
    -19.798,
    -26.178,
    -26.347,
    -18.811,
    -29.685,
    -18.212,
    -34.309,
    -13.850,
    -11.212,
    -1.191,
    -12.143,
    -16.334,
    -21.342,
    -25.559,
    -24.896,
    -22.567,
    0.000,
    -19.414,
    -18.483,
    -17.966,
    -17.789,
    -16.949,
    -13.506,
    -1.146,
    -9.559,
    -10.912,
    -30.481,
    -13.875,
    -25.163,
    -14.346,
    -22.085,
    -22.176,
    -16.038,
    -15.275,
    -15.804,
)
ISO17497_2_FLAT_LEVELS: tuple[float, ...] = (
    -36.385,
    -35.709,
    -36.065,
    -41.617,
    -40.861,
    -32.474,
    -42.750,
    -31.127,
    -47.771,
    -28.995,
    -30.520,
    -50.381,
    -28.015,
    -23.478,
    -21.660,
    -20.958,
    -20.753,
    -20.733,
    0.000,
    -20.733,
    -20.753,
    -20.958,
    -21.660,
    -23.478,
    -28.015,
    -50.381,
    -30.520,
    -28.995,
    -47.771,
    -31.127,
    -42.750,
    -32.474,
    -40.861,
    -41.617,
    -36.065,
    -35.709,
    -36.385,
)
ISO17497_2_QRD_DIFFUSION = 0.10985146785866741  # d_theta of the QRD arc, Formula (5)
ISO17497_2_FLAT_DIFFUSION = 0.004871959138901796  # d_theta of the flat reference arc
ISO17497_2_NORMALIZED_DIFFUSION = 0.10549346858814809  # d_theta_n, Formula (7)
# ---------------------------------------------------------------------------
# External anchor: Cox & D'Antonio, "Acoustic Absorbers and Diffusers",
# 3rd ed. (2017), Appendix B "Normalized diffusion coefficient table"
# (pp. 481-485), section 7, row "N = 7 QRD, 6 periods, 0.2 m deep", normal
# incidence. Third-party published data: 2D BEM predictions (thin-panel
# extrusions, source at 100 m, receiver arc at 50 m; each one-third-octave
# polar response is the average of seven single-frequency responses -
# section 5.2.5). Our Fraunhofer model reproduces the published normalised
# diffusion coefficient d_n in the 200-400 Hz one-third-octave bands within
# 0.01 (asserted at +/-0.015). CAVEAT: this is a low-band anchor, not
# full-band conformance - across the full published 100-5000 Hz range at
# normal incidence the model-vs-BEM mean absolute deviation is ~0.09 (the
# far-field phase-grating model ignores the edge diffraction and near-grazing
# effects the BEM resolves).
# ---------------------------------------------------------------------------
COX3E_APPENDIX_B_QRD_BANDS: tuple[float, ...] = (200.0, 250.0, 315.0, 400.0)
COX3E_APPENDIX_B_QRD_DN: tuple[float, ...] = (0.00, 0.01, 0.01, 0.01)
COX3E_APPENDIX_B_TOLERANCE = 0.015  # |model d_n - published BEM d_n| bound
# Formula (8) area factors use RADIANS internally, so the zenith weight is
# N0 = (4*pi/dphi)*sin^2(dtheta/4) / A_min with dtheta = dphi = 5 deg.
ISO17497_2_AREA_FACTOR_ZENITH = 1.571045588794762  # N0, radians convention

# ---------------------------------------------------------------------------
# Diffuser-design far-field prediction (Cox & D'Antonio, Fraunhofer model).
# Analytic anchors for the QRD-vs-flat behaviour of the design predictor.
#
# Geometry: an N = 7 quadratic residue diffuser (Eq. (10.2), s_n = n^2 mod N,
# so s = {0,1,4,2,2,4,1}) with design frequency f0 = 500 Hz and c = 343 m/s
# has design wavelength lambda0 = 0,686 m. The deepest well (s_max = 4) has,
# by Eq. (10.3) d_n = s_n*lambda0/(2N), depth 4*0,686/14 = 0,196 m exactly.
DIFFUSER_QRD7_MAX_DEPTH = 0.196  # m, closed form d_max = s_max*c/(2 N f0)
# A flat panel (all wells zero depth) normalises against itself, so Formula (7)
# gives (d - d_ref)/(1 - d_ref) = 0 identically: the exact zero anchor.
DIFFUSER_FLAT_NORMALIZED_DIFFUSION = 0.0
# The same N = 7 QRD (10 cm wells, five periods) predicted at 2 kHz: the
# normalised diffusion is well above the flat-panel zero, as a diffuser must be.
# The value is the far-field model prediction, committed as a regression guard.
DIFFUSER_QRD7_NORMALIZED_DIFFUSION_2K = 0.20802829817091092

# ---------------------------------------------------------------------------
# ISO 13472-1:2002 in-situ road-surface absorption. The mandatory geometry
# ds = 1,25 m, dm = 0,25 m gives the geometrical-spreading factor Kr = 2/3
# (Clause 4.2). The Annex A worked example (c = 340 m/s, 5 ms flat window)
# gives a maximum-sampled-area radius r ~ 1,34 m. Mirrors
# tests/materials/surfaces/test_road_absorption.py.
# ---------------------------------------------------------------------------
ISO13472_1_KR = 2.0 / 3.0  # geometrical-spreading factor
ISO13472_1_MSA_WINDOW = 5.0e-3  # reflected-wave window width Tw (s)
ISO13472_1_MSA_RADIUS = 1.3425466996067585  # Annex A worked example (m)

# ---------------------------------------------------------------------------
# ISO 13472-2:2010 spot method. The upper usable (plane-wave) frequency of a
# circular tube is f_u = 0,58 c0/d (Clause 5.4.1); a 100 mm tube at
# c0 = 343 m/s gives f_u = 1989,4 Hz.
# ---------------------------------------------------------------------------
ISO13472_2_SPOT_DIAMETER = 0.100  # tube diameter d (m)
ISO13472_2_SPOT_SPEED = 343.0  # speed of sound c0 (m/s)
ISO13472_2_SPOT_FU = 1989.4  # upper usable frequency (Hz)

# ---------------------------------------------------------------------------
# ISO 12999-2:2020 - measurement uncertainty for sound absorption.
# The standard's own worked examples are the oracle: Table 4 (sound absorption
# coefficient alpha_s and expanded uncertainty +/-U at k=2, reproducibility,
# one-third-octave 63-5000 Hz) and Table 5 (practical coefficient alpha_p,
# octave 250-4000 Hz). Example 1: alpha_w = 0,70 (MH) +/- 0,07 (k=2);
# Example 2: DLalpha,NRD = (8,1 +/- 1,6) dB (k=2).
# ---------------------------------------------------------------------------
ISO12999_2_TABLE4_FREQ = [
    63,
    80,
    100,
    125,
    160,
    200,
    250,
    315,
    400,
    500,
    630,
    800,
    1000,
    1250,
    1600,
    2000,
    2500,
    3150,
    4000,
    5000,
]
ISO12999_2_TABLE4_ALPHA_S = [
    0.33,
    0.35,
    0.39,
    0.38,
    0.37,
    0.36,
    0.36,
    0.36,
    0.43,
    0.49,
    0.58,
    0.63,
    0.68,
    0.71,
    0.73,
    0.75,
    0.77,
    0.79,
    0.81,
    0.81,
]
ISO12999_2_TABLE4_U_K2 = [
    0.33,
    0.26,
    0.22,
    0.17,
    0.13,
    0.11,
    0.09,
    0.08,
    0.08,
    0.08,
    0.08,
    0.08,
    0.08,
    0.09,
    0.09,
    0.09,
    0.10,
    0.11,
    0.13,
    0.16,
]
ISO12999_2_TABLE5_FREQ = [250, 500, 1000, 2000, 4000]
ISO12999_2_TABLE5_ALPHA_P = [0.50, 0.65, 0.70, 0.85, 0.80]
ISO12999_2_TABLE5_U_K2 = [0.09, 0.08, 0.08, 0.08, 0.10]
ISO12999_2_ALPHA_W_EXAMPLE = 0.70
ISO12999_2_ALPHA_W_U_K2 = 0.07
ISO12999_2_DLALPHA_EXAMPLE = 8.1
ISO12999_2_DLALPHA_U_K2 = 1.6

# Porous materials & multilayer absorbers - published anchors.
#
# Delany-Bazley power law (Bies 5e Appendix D Table D.1 first row = Mechel 2e
# Sect. G.11 Eqs. (1)-(2) = Hopkins Eqs. (1.171)-(1.172)), evaluated by hand
# at the digitization point X = rho f / sigma = 0.1 (mid fit range):
#   Zc/(rho c) = 1 + 0.0571*0.1^-0.754 - j 0.087*0.1^-0.732
#   k/k0       = 1 + 0.0978*0.1^-0.700 - j 0.189*0.1^-0.595
# Miki (1990) Eqs. (30)-(34) evaluated by hand at f/sigma = 0.1:
#   Zc/(rho c) = 1 + 0.070*0.1^-0.632 - j 0.107*0.1^-0.632
#   k/k0       = 1 + 0.109*0.1^-0.618 - j 0.160*0.1^-0.618
# Mechel 2e Sect. D.5: the maximum possible statistical absorption
# coefficient of a locally reacting plane is the published 0.951.
# ---------------------------------------------------------------------------
POROUS_DB_X_POINT = 0.1
POROUS_DB_ZC_EXPECTED = 1.3240679696882804 - 0.46937424158816093j
POROUS_DB_K_EXPECTED = 1.4901611144874722 - 0.7438096426114194j
POROUS_MIKI_Y_POINT = 0.1
POROUS_MIKI_ZC_EXPECTED = 1.2999839642782076 - 0.4585469168252603j
POROUS_MIKI_K_EXPECTED = 1.4522999064714557 - 0.6639264682149806j
POROUS_STATISTICAL_ALPHA_MAX = 0.951

# ---------------------------------------------------------------------------
# Maa (1998), "Potential of microperforated panel absorber", JASA 104(5).
# Table I (printed): maximum absorption alpha0 = 4r/(1+r)^2 (Eq. (10)) and
# absorption-band frequency interval B = f2/f1 = pi/arccot(1+r) - 1
# (Eq. (21)) for r = 1..5 at k = 0.
# Fig. 5 design example (also Cox & D'Antonio 3e Fig. 7.28): d = t = 0.2 mm,
# hole separation b = 2.5 mm on a square lattice (sigma = (pi/4)(d/b)^2,
# Eq. (25)), cavity D = 6 cm; theory vs standing-wave-tube measurement.
# ---------------------------------------------------------------------------
MAA_TABLE_I_R = (1.0, 2.0, 3.0, 4.0, 5.0)
MAA_TABLE_I_ALPHA0 = (1.0, 0.89, 0.75, 0.64, 0.56)
MAA_TABLE_I_BANDWIDTH = (5.78, 8.76, 11.82, 14.91, 18.02)
MAA_FIG5_DIAMETER = 0.2e-3
MAA_FIG5_THICKNESS = 0.2e-3
MAA_FIG5_SEPARATION = 2.5e-3
MAA_FIG5_CAVITY = 0.06


# ---------------------------------------------------------------------------
# Allard & Atalla, Propagation of Sound in Porous Media 2e (2009): the two
# specimens the library publishes as PUBLISHED_POROUS_MATERIALS, transcribed in
# the units the book prints.
#
# Table 6.1 (PDF page 133, printed p. 124) gives the glass wool 'Domisol
# Coffrage' as tortuosity, frame density, flow resistivity, porosity, a complex
# shear modulus in N/cm2 and a Poisson coefficient. It prints NEITHER
# characteristic length. Those two are printed in the prose of Sect. 6.5.4 on
# the facing folio (PDF page 132, printed p. 123): a fibre diameter of 12e-6 m
# gives, through Eqs. (5.29) and (5.30), Lambda = 0,56e-4 m and
# Lambda' = 2 Lambda = 1,1e-4 m, the book rounding 1,12 to two figures in its
# own print. Table 11.8 (PDF page 281, printed p. 275) prints the same
# specimen a second time, in micrometres and with E instead of N: its 56 and
# 110 um corroborate folio 123 (and settle 110 against 112), and its
# E = 4,4e6 Pa at nu = 0 is the Table 6.1 shear modulus through
# N = E/(2(1+nu)). Table 11.2 (PDF page 260, printed p. 254) gives the soft
# fibrous material in full, seven columns in one row.
#
# There is one copy of each printed digit and it is here. The library stores
# the same specimens in its own units (the shear modulus in pascals rather than
# N/cm2), and tests/materials/absorbers/test_porous.py asserts the second is the
# first converted, which is what makes two representations one copy and pins the
# 1e4 and the 1e-6 that are the real risk.
# ---------------------------------------------------------------------------
ALLARD_TABLE_6_1_TORTUOSITY = 1.06
ALLARD_TABLE_6_1_FRAME_DENSITY = 130.0  # rho_1 (kg m-3)
ALLARD_TABLE_6_1_FLOW_RESISTIVITY = 40_000.0  # sigma (N m-4 s)
ALLARD_TABLE_6_1_POROSITY = 0.94
ALLARD_TABLE_6_1_SHEAR_MODULUS_N_PER_CM2 = 220.0 * (1.0 + 0.1j)  # N (N cm-2)
ALLARD_TABLE_6_1_POISSON_RATIO = 0.0
#: The columns Table 6.1 prints, in its own order, so a re-reading of folio 124
#: can be diffed against the transcription as a whole rather than name by name.
ALLARD_TABLE_6_1_ROW: tuple[complex, ...] = (
    ALLARD_TABLE_6_1_TORTUOSITY,
    ALLARD_TABLE_6_1_FRAME_DENSITY,
    ALLARD_TABLE_6_1_FLOW_RESISTIVITY,
    ALLARD_TABLE_6_1_POROSITY,
    ALLARD_TABLE_6_1_SHEAR_MODULUS_N_PER_CM2,
    ALLARD_TABLE_6_1_POISSON_RATIO,
)

# Sect. 6.5.4, printed p. 123, in prose and in the metres the book writes there.
ALLARD_SECT_6_5_4_FIBRE_DIAMETER = 12.0e-6  # d (m), from Eq. (5.C.7)
ALLARD_SECT_6_5_4_VISCOUS_LENGTH_M = 0.56e-4  # Lambda (m), from Eq. (5.29)
ALLARD_SECT_6_5_4_THERMAL_LENGTH_M = 1.1e-4  # Lambda' = 2 Lambda (m), Eq. (5.30)

# Table 11.2, the one row: h (mm), phi, sigma (N s/m4), alpha_inf, Lambda (um),
# Lambda' (um), rho_1 (kg/m3).
ALLARD_TABLE_11_2_THICKNESS_MM = 50.0
ALLARD_TABLE_11_2_POROSITY = 0.98
ALLARD_TABLE_11_2_FLOW_RESISTIVITY = 25.0e3
ALLARD_TABLE_11_2_TORTUOSITY = 1.02
ALLARD_TABLE_11_2_VISCOUS_LENGTH_UM = 90.0
ALLARD_TABLE_11_2_THERMAL_LENGTH_UM = 180.0
ALLARD_TABLE_11_2_FRAME_DENSITY = 30.0

# Table 11.8, the glass-wool row, in the same column order plus E (Pa), nu and
# eta_s. The two characteristic lengths are the ones Table 6.1 does not print.
ALLARD_TABLE_11_8_THICKNESS_MM = 3.8
ALLARD_TABLE_11_8_POROSITY = 0.94
ALLARD_TABLE_11_8_FLOW_RESISTIVITY = 40.0e3
ALLARD_TABLE_11_8_TORTUOSITY = 1.06
ALLARD_TABLE_11_8_VISCOUS_LENGTH_UM = 56.0
ALLARD_TABLE_11_8_THERMAL_LENGTH_UM = 110.0
ALLARD_TABLE_11_8_FRAME_DENSITY = 130.0
ALLARD_TABLE_11_8_YOUNGS_MODULUS = 4.4e6  # E (Pa)
ALLARD_TABLE_11_8_POISSON_RATIO = 0.0
ALLARD_TABLE_11_8_LOSS_FACTOR = 0.1  # eta_s

# ---------------------------------------------------------------------------
# Hopkins, Sound Insulation (2007), Table A3 (PDF page 637, printed p. 610):
# "Dynamic stiffness per unit area of resilient materials measured according to
# ISO 9052-1". All fifteen rows as
# (material, density in kg/m3, nominal uncompressed thickness in mm,
#  s' in MN/m3), in the printed order and the printed units. The heading prints
# s', which the book's List of symbols (PDF page 23, printed p. xxii) defines
# as the dynamic stiffness per unit area of the installed material, apart from
# the apparent s't of the test specimen.
#
# The page prints some densities once for a block and leaves the cell blank on
# the block's other rows: 36 on the 13 mm glass-wool row and not on the 25 mm
# row below it, 75 on the first 25 mm glass-wool row and not on the 40 mm row,
# and 64 on the 20 mm rebond row, level with the middle of the three rows it
# spans. The rows below hold the block's density on every row, and
# HOPKINS_TABLE_A3_BLANK_DENSITY names the four whose printed cell is blank.
# The library keys the rows by density and thickness because the printed table
# distinguishes them by position and a lookup name cannot.
#
# There is one copy of each printed digit and it is here. The library stores the
# same fifteen rows in N/m3 as PUBLISHED_RESILIENT_LAYERS, read from
# materials/resilient/data/hopkins-2007-table-a3.json, and
# tests/materials/resilient/test_dynamic_stiffness.py asserts that it is this
# table times 1e6, which is what makes two representations one copy and pins the
# conversion that is the real risk.
# ---------------------------------------------------------------------------
HOPKINS_TABLE_A3_MN_PER_M3: tuple[tuple[str, float, float, float], ...] = (
    ("Closed-cell polyethylene foam", 45.0, 5.0, 115.0),
    ("Expanded polystyrene", 14.0, 50.0, 78.0),
    ("Expanded polystyrene, pre-compressed", 10.0, 50.0, 68.0),
    ("Mineral wool, rock", 60.0, 30.0, 10.0),
    ("Mineral wool, rock", 80.0, 30.0, 11.0),
    ("Mineral wool, rock", 100.0, 30.0, 14.0),
    ("Mineral wool, rock", 140.0, 30.0, 19.0),
    ("Mineral wool, glass", 36.0, 13.0, 28.0),
    ("Mineral wool, glass", 36.0, 25.0, 11.0),
    ("Mineral wool, glass", 75.0, 25.0, 12.0),
    ("Mineral wool, glass", 75.0, 40.0, 7.0),
    ("Rebond foam (reconstituted open cell foam)", 64.0, 15.0, 12.0),
    ("Rebond foam (reconstituted open cell foam)", 64.0, 20.0, 9.0),
    ("Rebond foam (reconstituted open cell foam)", 64.0, 25.0, 7.0),
    ("Rebond foam (reconstituted open cell foam)", 96.0, 15.0, 16.0),
)

#: The rows of HOPKINS_TABLE_A3_MN_PER_M3 whose density cell the page prints
#: blank, by position, each to the position of the row of its block that prints
#: the figure.
HOPKINS_TABLE_A3_BLANK_DENSITY: dict[int, int] = {8: 7, 10: 9, 11: 12, 13: 12}

#: How many of the fifteen the book gives as its own measurements; the last four
#: it credits to Hopkins and Hall (2006) in the material cell.
HOPKINS_TABLE_A3_FIRST_HAND_ROWS = 11


# ---------------------------------------------------------------------------
# Every specimen Allard & Atalla 2e prints with all four Johnson-Champoux-Allard
# columns at once: the airflow resistivity, the open porosity, the tortuosity
# and the viscous characteristic length. The lengths are the point. Three of the
# four are measured routinely and the fourth almost never is, which is why the
# book gives Eq. (5.25) to estimate it from the other three, and why this table
# is the only honest way to say how far that estimate goes.
#
# Twenty-three rows, gathered from fourteen pages of the same edition, each
# carrying the table it was printed in, its PDF page and its printed folio, all
# read from the rendered page. Where a table prints Lambda and Lambda' in metres
# (Table 13.1) the micrometres here are that number times 1e6, which is the only
# arithmetic done to any of them. Rows whose length cell reads "model" instead
# of a number (the screen of Table 11.5) are not here, because a cell that names
# a model is not a measurement.
#
# Mirrors tests/materials/absorbers/test_porous_relations.py.
# ---------------------------------------------------------------------------
#: ``(material, table, PDF page, printed folio, sigma in Pa s/m2, porosity,
#: tortuosity, Lambda in um, Lambda' in um)``.
ALLARD_JCA_SPECIMENS: tuple[
    tuple[str, str, int, int, float, float, float, float, float], ...
] = (
    ("Material 1", "Table 8.1", 181, 174, 50_000.0, 0.98, 1.4, 50.0, 150.0),
    ("Material 2", "Table 8.1", 181, 174, 22_100.0, 0.97, 2.2, 39.0, 275.0),
    ("Soft fibrous", "Table 11.2", 260, 254, 25_000.0, 0.98, 1.02, 90.0, 180.0),
    ("Foam", "Table 11.3", 272, 266, 5_000.0, 0.98, 1.1, 150.0, 216.0),
    ("Glass wool", "Table 11.3", 272, 266, 1_100_000.0, 0.7, 1.0, 10.0, 20.0),
    ("Blanket (1)", "Table 11.4", 276, 270, 34_000.0, 0.98, 1.18, 60.0, 86.0),
    ("Screen (2)", "Table 11.4", 276, 270, 3_200_000.0, 0.8, 2.56, 6.0, 24.0),
    ("Foam (3)", "Table 11.4", 276, 270, 87_000.0, 0.97, 2.52, 36.0, 118.0),
    ("Foam (4)", "Table 11.4", 276, 270, 65_000.0, 0.99, 1.98, 37.0, 120.0),
    ("Felt (1)", "Table 11.5", 277, 271, 23_000.0, 0.99, 1.4, 64.0, 131.0),
    ("Foam (3)", "Table 11.5", 277, 271, 10_900.0, 0.99, 1.02, 100.0, 130.0),
    ("Carpet (1)", "Table 11.7", 280, 274, 5_000.0, 0.99, 1.0, 23.0, 28.0),
    ("Carpet (2)", "Table 11.7", 280, 274, 5_000.0, 0.99, 1.0, 23.0, 28.0),
    ("Fibrous layer", "Table 11.7", 280, 274, 33_000.0, 0.98, 1.1, 50.0, 110.0),
    ("Glass wool", "Table 11.8", 281, 275, 40_000.0, 0.94, 1.06, 56.0, 110.0),
    ("Foam", "Table 11.9", 282, 276, 6_600.0, 0.98, 1.03, 200.0, 380.0),
    ("Foam 1", "Table 12.1", 297, 292, 10_900.0, 0.99, 1.02, 100.0, 130.0),
    ("Mineral wool", "Table 12.2", 298, 293, 34_000.0, 0.95, 1.0, 40.0, 80.0),
    ("Limp foam", "Table 12.4", 304, 299, 10_900.0, 0.99, 1.02, 100.0, 130.0),
    ("Limp foam", "Table 12.5", 306, 301, 20_000.0, 0.9, 1.6, 12.0, 24.0),
    ("Foam", "Table 12.5", 306, 301, 10_900.0, 0.99, 1.02, 100.0, 130.0),
    ("Foam", "Table 13.1", 332, 328, 12_569.0, 0.99, 1.02, 78.0, 192.0),
    ("Rockwool", "Table 13.2", 341, 337, 135_000.0, 0.94, 2.1, 49.0, 166.0),
)

#: The two rows of :data:`ALLARD_JCA_SPECIMENS` that are floor coverings rather
#: than bulk absorbers. Eq. (5.25) treats the pore as a cylinder, and a carpet
#: pile is not one: these are the rows that measure how badly it can miss.
ALLARD_JCA_CARPET_ROWS = ("Carpet (1)", "Carpet (2)")

#: The dynamic viscosity of air Allard & Atalla 2e states, in Pa s: "for air in
#: standard conditions", PDF page 56 (printed p. 46), below Eq. (4.2). Eq. (5.25)
#: has it inside a square root, so which value is used moves the estimated length
#: by half of whatever it is changed by.
ALLARD_AIR_VISCOSITY_PA_S = 1.84e-5

# ---------------------------------------------------------------------------
# Hopkins (2007) on mineral wool: the fibre, the bulk density and what follows
# from them. Equation (1.160) on PDF page 107 (printed p. 80) makes the porosity
# from the two densities; Equation (1.165) on PDF page 108 (printed p. 81) makes
# the airflow resistivity from the bulk density and the fibre diameter, with the
# two coefficient sets printed on that same page for the rock wool of Fig. 1.49.
#
# The two equations check each other. Applying (1.160) to the ends of the
# bulk-density range that (1.165) was fitted over has to give back the porosity
# range Hopkins prints beside it, and it does, which is why both are here rather
# than in two places.
#
# Mirrors tests/materials/absorbers/test_porous_relations.py.
# ---------------------------------------------------------------------------
#: Density of the rock-wool fibre itself, in kg/m3.
HOPKINS_ROCK_WOOL_FIBRE_DENSITY = 2600.0
#: Average fibre diameter of the fitted material, in micrometres.
HOPKINS_ROCK_WOOL_FIBRE_DIAMETER_UM = 4.75
#: ``(k1, k2, low bulk density, high bulk density)`` in the plane of the sheet.
HOPKINS_ROCK_WOOL_LATERAL_FIT = (353.0, 0.63, 31.0, 155.0)
#: The same, through the sheet.
HOPKINS_ROCK_WOOL_LONGITUDINAL_FIT = (780.0, 0.59, 38.0, 162.0)
#: The porosity range Hopkins prints for this wool, lowest bulk density first.
HOPKINS_ROCK_WOOL_POROSITY_RANGE = (0.99, 0.94)


# ---------------------------------------------------------------------------
# Allard & Atalla 2e: the porous rows of the nineteen parameter tables the
# catalogue holds, read a second time off the rendered pages.
#
# One entry per catalogue key, and the value is the cells that page prints, in
# the units this library stores them in. Where the printed unit is not the
# stored one the factor is written into the literal rather than applied in the
# head, so the printed digit and the conversion are both visible here: the
# book's N/cm2 becomes ``220.0 * 1.0e4`` and its millimetres ``0.12 * 1000.0``.
#
# The complex shear moduli the book prints as ``N(1 + j eta)`` or ``75 + j15``
# are split the way the library stores them, into a real modulus and a
# structural loss factor, and the split is arithmetic on the printed digits:
# 15/75 is the 0,2 below, not a number read anywhere.
#
# Cells these pages print that are not porous parameters are not here, and
# neither are the rows that are not porous materials: each data file's
# ``about`` says which of its page's rows are absent and why.
# ---------------------------------------------------------------------------
ALLARD_POROUS_ROWS: tuple[tuple[str, dict[str, float]], ...] = (
    (
        "allard-2009-table-6-1/domisol_coffrage",
        {
            "flow_resistivity_pa_s_m2": 40_000.0,
            "porosity": 0.94,
            "tortuosity": 1.06,
            # Sect. 6.5.4, printed p. 123, in metres.
            "viscous_length_um": 0.56e-4 * 1.0e6,
            "thermal_length_um": 1.1e-4 * 1.0e6,
            "frame_density_kg_m3": 130.0,
            # N = 220(1 + j0,1) N/cm2, and 1 N/cm2 is 1e4 Pa.
            "shear_modulus_pa": 220.0 * 1.0e4,
            "structural_loss_factor": 0.1,
            "poisson_ratio": 0.0,
        },
    ),
    (
        "allard-2009-table-7-1/material_1",
        {
            "tortuosity": 1.1,
            "flow_resistivity_pa_s_m2": 20_000.0,
            "porosity": 0.96,
            "viscous_length_um": 100.0,
            "thermal_length_um": 300.0,
        },
    ),
    (
        "allard-2009-table-7-1/material_2",
        {
            "tortuosity": 1.32,
            "flow_resistivity_pa_s_m2": 5500.0,
            "porosity": 0.98,
            "viscous_length_um": 120.0,
            "thermal_length_um": 500.0,
        },
    ),
    (
        "allard-2009-table-8-1/material_1",
        {
            "frame_density_kg_m3": 25.0,
            "poisson_ratio": 0.3,
            # N = 75 + j15 kPa.
            "shear_modulus_pa": 75.0 * 1.0e3,
            "structural_loss_factor": 15.0 / 75.0,
            "tortuosity": 1.4,
            "porosity": 0.98,
            "flow_resistivity_pa_s_m2": 50_000.0,
            "viscous_length_um": 50.0,
            "thermal_length_um": 150.0,
        },
    ),
    (
        "allard-2009-table-8-1/material_2",
        {
            "frame_density_kg_m3": 24.5,
            "poisson_ratio": 0.44,
            # N = 80 + j12 kPa.
            "shear_modulus_pa": 80.0 * 1.0e3,
            "structural_loss_factor": 12.0 / 80.0,
            "tortuosity": 2.2,
            "porosity": 0.97,
            "flow_resistivity_pa_s_m2": 22_100.0,
            "viscous_length_um": 39.0,
            "thermal_length_um": 275.0,
        },
    ),
    (
        "allard-2009-table-9-1/m1",
        {
            "flow_resistivity_pa_s_m2": 5000.0,
            # Lambda and Lambda' in millimetres, thickness in centimetres.
            "viscous_length_um": 0.12 * 1000.0,
            "thermal_length_um": 0.27 * 1000.0,
            "tortuosity": 1.1,
            "porosity": 0.99,
            "thickness_mm": 0.1 * 10.0,
        },
    ),
    (
        "allard-2009-table-9-1/m2",
        {
            "flow_resistivity_pa_s_m2": 50_000.0,
            "viscous_length_um": 0.034 * 1000.0,
            "thermal_length_um": 0.13 * 1000.0,
            "tortuosity": 1.5,
            "porosity": 0.98,
            "thickness_mm": 1.9 * 10.0,
        },
    ),
    (
        "allard-2009-table-10-1/glass_wool_x",
        {
            "flow_resistivity_pa_s_m2": 4000.0,
            "porosity": 0.98,
            "tortuosity": 1.1,
            "thermal_permeability_m2": 6.0e-9,
            "viscous_length_um": 200.0,
            "thermal_length_um": 500.0,
            "frame_density_kg_m3": 32.0,
        },
    ),
    (
        "allard-2009-table-10-1/glass_wool_z",
        {
            "flow_resistivity_pa_s_m2": 8000.0,
            "porosity": 0.98,
            "tortuosity": 1.1,
            "thermal_permeability_m2": 6.0e-9,
            "viscous_length_um": 140.0,
            "thermal_length_um": 500.0,
            "frame_density_kg_m3": 32.0,
        },
    ),
    (
        "allard-2009-table-11-2/soft_fibrous",
        {
            "thickness_mm": 50.0,
            "porosity": 0.98,
            "flow_resistivity_pa_s_m2": 25.0e3,
            "tortuosity": 1.02,
            "viscous_length_um": 90.0,
            "thermal_length_um": 180.0,
            "frame_density_kg_m3": 30.0,
        },
    ),
    (
        "allard-2009-table-11-3/foam",
        {
            "thickness_mm": 38.0,
            "porosity": 0.98,
            "flow_resistivity_pa_s_m2": 5.0e3,
            "tortuosity": 1.1,
            "viscous_length_um": 150.0,
            "thermal_length_um": 216.0,
            "frame_density_kg_m3": 33.0,
            "youngs_modulus_pa": 130.0e3,
            "poisson_ratio": 0.3,
            "structural_loss_factor": 0.1,
        },
    ),
    (
        "allard-2009-table-11-3/glass_wool",
        {
            "thickness_mm": 0.45,
            "porosity": 0.7,
            "flow_resistivity_pa_s_m2": 1.1e6,
            "tortuosity": 1.0,
            "viscous_length_um": 10.0,
            "thermal_length_um": 20.0,
            "frame_density_kg_m3": 660.0,
            "youngs_modulus_pa": 2.6e6,
            "poisson_ratio": 0.3,
            "structural_loss_factor": 0.1,
        },
    ),
    (
        "allard-2009-table-11-4/blanket_1",
        {
            "thickness_mm": 4.0,
            "porosity": 0.98,
            "flow_resistivity_pa_s_m2": 34.0e3,
            "tortuosity": 1.18,
            "viscous_length_um": 60.0,
            "thermal_length_um": 86.0,
            "frame_density_kg_m3": 41.0,
            "youngs_modulus_pa": 286.0e3,
            "poisson_ratio": 0.3,
            "structural_loss_factor": 0.015,
        },
    ),
    (
        "allard-2009-table-11-4/screen_2",
        {
            "thickness_mm": 0.8,
            "porosity": 0.8,
            "flow_resistivity_pa_s_m2": 3.2e6,
            "tortuosity": 2.56,
            "viscous_length_um": 6.0,
            "thermal_length_um": 24.0,
            "frame_density_kg_m3": 125.0,
            "youngs_modulus_pa": 2.6e6,
            "poisson_ratio": 0.3,
            "structural_loss_factor": 0.1,
        },
    ),
    (
        "allard-2009-table-11-4/foam_3",
        {
            "thickness_mm": 5.0,
            "porosity": 0.97,
            "flow_resistivity_pa_s_m2": 87.0e3,
            "tortuosity": 2.52,
            "viscous_length_um": 36.0,
            "thermal_length_um": 118.0,
            "frame_density_kg_m3": 31.0,
            "youngs_modulus_pa": 143.0e6,
            "poisson_ratio": 0.3,
            "structural_loss_factor": 0.055,
        },
    ),
    (
        "allard-2009-table-11-4/foam_4",
        {
            "thickness_mm": 16.0,
            "porosity": 0.99,
            "flow_resistivity_pa_s_m2": 65.0e3,
            "tortuosity": 1.98,
            "viscous_length_um": 37.0,
            "thermal_length_um": 120.0,
            "frame_density_kg_m3": 16.0,
            "youngs_modulus_pa": 46.8e6,
            "poisson_ratio": 0.3,
            "structural_loss_factor": 0.1,
        },
    ),
    (
        "allard-2009-table-11-5/felt_1",
        {
            "thickness_mm": 19.0,
            "porosity": 0.99,
            "flow_resistivity_pa_s_m2": 23.0e3,
            "tortuosity": 1.4,
            "viscous_length_um": 64.0,
            "thermal_length_um": 131.0,
            "frame_density_kg_m3": 66.0,
        },
    ),
    (
        "allard-2009-table-11-5/screen_2",
        {
            "thickness_mm": 0.08,
            "porosity": 0.08,
            "flow_resistivity_pa_s_m2": 137.0e3,
        },
    ),
    (
        "allard-2009-table-11-5/foam_3",
        {
            "thickness_mm": 27.0,
            "porosity": 0.99,
            "flow_resistivity_pa_s_m2": 10.9e3,
            "tortuosity": 1.02,
            "viscous_length_um": 100.0,
            "thermal_length_um": 130.0,
            "frame_density_kg_m3": 8.8,
        },
    ),
    (
        "allard-2009-table-11-6/foam",
        {
            "thickness_mm": 20.0,
            "porosity": 0.98,
            "flow_resistivity_pa_s_m2": 22.0e3,
            "tortuosity": 1.9,
            "viscous_length_um": 87.0,
            "thermal_length_um": 146.0,
            "frame_density_kg_m3": 30.0,
            "youngs_modulus_pa": 294.0e3,
            "poisson_ratio": 0.2,
            "structural_loss_factor": 0.18,
        },
    ),
    (
        "allard-2009-table-11-7/carpet_1",
        {
            "thickness_mm": 3.5,
            "porosity": 0.99,
            "flow_resistivity_pa_s_m2": 5.0e3,
            "tortuosity": 1.0,
            "viscous_length_um": 23.0,
            "thermal_length_um": 28.0,
            "frame_density_kg_m3": 60.0,
            "youngs_modulus_pa": 20.0e3,
            "poisson_ratio": 0.0,
            "structural_loss_factor": 0.5,
        },
    ),
    (
        "allard-2009-table-11-7/carpet_2",
        {
            "thickness_mm": 3.5,
            "porosity": 0.99,
            "flow_resistivity_pa_s_m2": 5.0e3,
            "tortuosity": 1.0,
            "viscous_length_um": 23.0,
            "thermal_length_um": 28.0,
            "frame_density_kg_m3": 60.0,
            "youngs_modulus_pa": 20.0e3,
            "poisson_ratio": 0.0,
            "structural_loss_factor": 0.5,
        },
    ),
    (
        "allard-2009-table-11-7/fibrous_layer",
        {
            "thickness_mm": 1.25,
            "porosity": 0.98,
            "flow_resistivity_pa_s_m2": 33.0e3,
            "tortuosity": 1.1,
            "viscous_length_um": 50.0,
            "thermal_length_um": 110.0,
            "frame_density_kg_m3": 60.0,
            "youngs_modulus_pa": 100.0e3,
            "poisson_ratio": 0.0,
            "structural_loss_factor": 0.88,
        },
    ),
    (
        "allard-2009-table-11-8/glass_wool",
        {
            "thickness_mm": 3.8,
            "porosity": 0.94,
            "flow_resistivity_pa_s_m2": 40.0e3,
            "tortuosity": 1.06,
            "viscous_length_um": 56.0,
            "thermal_length_um": 110.0,
            "frame_density_kg_m3": 130.0,
            "youngs_modulus_pa": 4.4e6,
            "poisson_ratio": 0.0,
            "structural_loss_factor": 0.1,
        },
    ),
    (
        "allard-2009-table-11-9/foam",
        {
            "thickness_mm": 25.4,
            "porosity": 0.98,
            "flow_resistivity_pa_s_m2": 6.6e3,
            "tortuosity": 1.03,
            "viscous_length_um": 200.0,
            "thermal_length_um": 380.0,
            "frame_density_kg_m3": 11.2,
            "youngs_modulus_pa": 2.93e5,
            "poisson_ratio": 0.2,
            "structural_loss_factor": 0.06,
        },
    ),
    (
        "allard-2009-table-12-1/foam_1",
        {
            "porosity": 0.99,
            "flow_resistivity_pa_s_m2": 10.9e3,
            "tortuosity": 1.02,
            "viscous_length_um": 100.0,
            "thermal_length_um": 130.0,
            "frame_density_kg_m3": 8.8,
            "youngs_modulus_pa": 80.0e3,
            "poisson_ratio": 0.35,
            "structural_loss_factor": 0.14,
        },
    ),
    (
        "allard-2009-table-12-2/mineral_wool",
        {
            "thickness_mm": 30.0,
            "porosity": 0.95,
            "flow_resistivity_pa_s_m2": 34.0e3,
            "tortuosity": 1.0,
            "viscous_length_um": 40.0,
            "thermal_length_um": 80.0,
            "frame_density_kg_m3": 90.0,
            "youngs_modulus_pa": 40.0e3,
            "poisson_ratio": 0.0,
            "structural_loss_factor": 0.18,
        },
    ),
    (
        "allard-2009-table-12-4/limp_foam",
        {
            "thickness_mm": 30.0,
            "porosity": 0.99,
            "flow_resistivity_pa_s_m2": 10.9e3,
            "tortuosity": 1.02,
            "viscous_length_um": 100.0,
            "thermal_length_um": 130.0,
            "frame_density_kg_m3": 8.8,
        },
    ),
    (
        "allard-2009-table-12-5/limp_foam",
        {
            "thickness_mm": 25.4,
            "porosity": 0.9,
            "flow_resistivity_pa_s_m2": 20_000.0,
            "tortuosity": 1.6,
            "viscous_length_um": 12.0,
            "thermal_length_um": 24.0,
            "frame_density_kg_m3": 30.0,
            "youngs_modulus_pa": 1300.0,
            "poisson_ratio": 0.0,
            "structural_loss_factor": 0.4,
        },
    ),
    (
        "allard-2009-table-12-5/foam",
        {
            "thickness_mm": 25.4,
            "porosity": 0.99,
            "flow_resistivity_pa_s_m2": 10.9e3,
            "tortuosity": 1.02,
            "viscous_length_um": 100.0,
            "thermal_length_um": 130.0,
            "frame_density_kg_m3": 8.8,
            "youngs_modulus_pa": 80.0e3,
            "poisson_ratio": 0.35,
            "structural_loss_factor": 0.14,
        },
    ),
    (
        "allard-2009-table-13-1/foam",
        {
            "porosity": 0.99,
            "flow_resistivity_pa_s_m2": 12_569.0,
            "tortuosity": 1.02,
            # Lambda and Lambda' printed in metres on this page alone.
            "viscous_length_um": 0.000078 * 1.0e6,
            "thermal_length_um": 0.000192 * 1.0e6,
            "frame_density_kg_m3": 8.85,
            "youngs_modulus_pa": 93_348.0,
            "poisson_ratio": 0.44,
            "structural_loss_factor": 0.064,
        },
    ),
    (
        "allard-2009-table-13-2/rockwool",
        {
            "porosity": 0.94,
            "flow_resistivity_pa_s_m2": 135_000.0,
            "tortuosity": 2.1,
            "viscous_length_um": 49.0,
            "thermal_length_um": 166.0,
            "thermal_permeability_m2": 3.3e-9,
            "frame_density_kg_m3": 130.0,
            "youngs_modulus_pa": 4400.0,
            "poisson_ratio": 0.0,
            "structural_loss_factor": 0.1,
        },
    ),
)

#: The rows Cox credits to Mechel, paired with the rows Mechel prints, as the
#: two pages print them: Cox's name, Mechel's name, and the interval both
#: books give. Two transcriptions of two books by two readers, so an interval
#: that matches here matches the printed digits of both pages.
#:
#: Cox's foam row is not here. It reads 0,93 to 0,995 against Mechel's 0,95 to
#: 0,995, and it credits four studies rather than Mechel alone, so it is a
#: compilation of its own and not a copy.
COX_MECHEL_SHARED_POROSITY: tuple[tuple[str, str, tuple[float, float]], ...] = (
    ("mineral_wool", "mineral_fibre_materials", (0.92, 0.99)),
    ("wood_fibre_board", "wood_fibre_board", (0.65, 0.80)),
    ("wood_wool_board", "wood_wool_board", (0.50, 0.65)),
    ("gravel_and_stone_chip_fill", "gravel_and_stone_chip_fill", (0.25, 0.45)),
    ("pumice_concrete", "pumice_concrete", (0.25, 0.50)),
    ("pumice_fill", "pumice_fill", (0.65, 0.85)),
    ("sintered_metal", "sinter_metal", (0.10, 0.25)),
)

#: What the compiled tables print where a single number would go, keyed by
#: row, as each transcription flagged it after reading the rendered page.
#: These are the cells a reader of the text layer would get wrong.
COX_MECHEL_JUDGEMENT_CALLS: tuple[tuple[str, str, object], ...] = (
    # Table 6.8: three readings of a viscous length, comma separated, and two
    # of a thermal length joined by the word "and".
    ("cox-2017-table-6-8/plastic_foam", "viscous_length_um", (25.0, 207.0, 230.0)),
    ("cox-2017-table-6-8/plastic_foam", "thermal_length_um", (70.0, 690.0)),
    # Table 6.9: two intervals in one cell, comma separated.
    ("cox-2017-table-6-9/rubber_crumb", "tortuosity", ((1.13, 1.26), (1.38, 1.56))),
    ("cox-2017-table-6-9/vermiculite", "tortuosity", ((1.48, 1.58), (1.8, 2.46))),
    # Table 6.9: the two rows the PDF text layer does not contain at all.
    ("cox-2017-table-6-9/snow_new", "tortuosity", (1.5, 2.7)),
    ("cox-2017-table-6-9/snow_old_crusted", "tortuosity", 4.0),
    # Mechel G.11: a shot content printed as "< 1".
    ("mechel-2008-section-g11-table-1/glass_fibre", "shot_content_percent", (0.0, 1.0)),
    # Cox 6.5: a porosity printed as ">0.75", and one printed with a tilde.
    ("cox-2017-table-6-5/aerogel", "porosity", (0.75, 1.0)),
    ("cox-2017-table-6-5/marble", "porosity", 0.005),
)
