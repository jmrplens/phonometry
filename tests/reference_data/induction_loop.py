#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Audio-frequency induction-loop systems: IEC 60118-4 and IEC 62489-1.

Every value is read off the rasterised page. IEC 60118-4:2014 in BS EN
60118-4:2015 (PDF page = folio + 2); its Amendment 1:2017 in the Spanish
UNE-EN IEC 60118-4:2016/A1:2018 (PDF page = folio); IEC 62489-1:2010 with
Amendment 1:2014 in the consolidated BS EN 62489-1:2010+A1:2015 (PDF page =
folio + 2); the draft Amendment 2 in E DIN EN 62489-1/A2:2017-10, whose
English CDV text is printed from PDF page 6 (CDV folio 2) on (PDF page = CDV
folio + 4). Two figures are read off their curves at 300 dots per inch, against
the figure's own gridlines, and say so where they are kept.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# IEC 60118-4:2014 3.1 (folio 9) and 4.3 (folio 11): 0 dB is 400 mA/m, and a
# long-term average of -12 dB ref. 400 mA/m, "i.e. 100 mA/m", gives the output
# a 70 dB sound pressure level gives.
# ---------------------------------------------------------------------------
IEC60118_4_REFERENCE_A_PER_M = 0.4
IEC60118_4_LONG_TERM_LEVEL_DB = -12.0
IEC60118_4_LONG_TERM_A_PER_M = 0.1

# ---------------------------------------------------------------------------
# IEC 60118-4:2014 6.4 (folio 13): pink noise, peak-to-peak over RMS at least
# 18 dB ("crest factor = 4"), third-order Butterworth filters with -3 dB at
# 75 Hz and 6,5 kHz. NOTE 2 prints the theoretical responses as -0,8 dB at
# 100 Hz and -0,7 dB at 5 kHz, which the formula exchanges (see
# docs/ERRATA.md). IEC 62489-1:2010 5.4.8.2 b) (folio 11) prints the same
# note and asks for 18 dB plus or minus 2 dB.
# ---------------------------------------------------------------------------
IEC60118_4_NOISE_PEAK_TO_PEAK_DB = 18.0
IEC62489_1_NOISE_PEAK_TO_PEAK_TOL_DB = 2.0
IEC60118_4_BAND_LIMIT_HZ = (75.0, 6500.0)
IEC60118_4_BAND_LIMIT_PRINTED_DB = {100.0: -0.8, 5000.0: -0.7}
#: What the two third-order Butterworth filters give there, to three
#: decimals: 10 lg of 1/(1 + (75/f)^6) and of 1/(1 + (f/6500)^6).
IEC60118_4_BAND_LIMIT_COMPUTED_DB = {100.0: -0.711, 5000.0: -0.818}

# ---------------------------------------------------------------------------
# IEC 60118-4:2014 Table 2 (folio 14): the combi signal. Sine at 1 kHz with
# 5 ms rise and fall, 0 dB against the noise's -6 dB, at least 1 s against at
# least 4 s, the ratio of 4:1 never reduced; "the peaks of the sine wave
# signal are 3 dB below the maximum peak of pink noise having a crest factor
# of 4".
# ---------------------------------------------------------------------------
IEC60118_4_COMBI_SINE_HZ = 1000.0
IEC60118_4_COMBI_RAMP_MS = 5.0
IEC60118_4_COMBI_NOISE_RELATIVE_DB = -6.0
IEC60118_4_COMBI_MIN_SINE_S = 1.0
IEC60118_4_COMBI_MIN_NOISE_S = 4.0
IEC60118_4_COMBI_SINE_PEAK_BELOW_NOISE_PEAK_DB = 3.0

# ---------------------------------------------------------------------------
# IEC 60118-4:2014 Table 3 (folio 17): typical levels re 400 mA/m of an
# amplifier with peak-detecting AGC set to 400 mA/m on a sine, on the RMS
# meter of 6.1.3 and on the PPM of 6.1.4. The combi RMS cell reads "As
# sinusoidal and noise components".
# ---------------------------------------------------------------------------
IEC60118_4_TABLE3 = {
    "sinusoidal": (0.0, 0.0),
    "pink_noise": (-6.0, 0.0),
    "ists": (0.0, 0.0),
    "combi": (None, 0.0),
}

# ---------------------------------------------------------------------------
# IEC 60118-4:2014 7.2 (folio 15): reference signal-to-noise ratios.
# ---------------------------------------------------------------------------
IEC60118_4_SNR_IDEAL_DB = 47.0
IEC60118_4_SNR_MINIMUM_DB = 32.0
IEC60118_4_SNR_SHORT_PERIODS_DB = 22.0

# ---------------------------------------------------------------------------
# IEC 60118-4:2014 8.3.7 and 8.4.3 (folio 19): plus or minus 3 dB re 1 kHz
# from 100 Hz to 5 000 Hz, and plus or minus 3 dB of the 8.2.7 level.
# ---------------------------------------------------------------------------
IEC60118_4_RESPONSE_TOL_DB = 3.0
IEC60118_4_RESPONSE_BAND_HZ = (100.0, 5000.0)
IEC60118_4_FIELD_TOL_DB = 3.0

# ---------------------------------------------------------------------------
# IEC 60118-4:2014/A1:2017, as printed in UNE-EN IEC 60118-4:2016/A1:2018.
# 9.5 (folio 10): plus or minus 6 dB at every point, 0 dB at one at least,
# nowhere above +8 dB. 10.2 (folio 11): plus or minus 3 dB, "283 mA/m a
# 566 mA/m". 10.3.2 (folio 12): 7 dB below the required field; Table 4.
# 10.4.7 (folio 13): 47 dB, -47 dB and 1 dB.
# ---------------------------------------------------------------------------
IEC60118_4_A1_SMALL_VOLUME_RANGE_DB = 6.0
IEC60118_4_A1_STANDING_AREA_MAX_DB = 8.0
IEC60118_4_A1_COMMISSIONING_MA_PER_M = (283.0, 566.0)
IEC60118_4_A1_OVERLOAD_OFFSET_DB = -7.0
#: Table 4: programme, upper limit of the maximum power bandwidth, test
#: frequency, both in hertz.
IEC60118_4_A1_TABLE4 = (
    ("transient_speech", 1250.0, 2500.0),
    ("speech", 1600.0, 3150.0),
    ("music", 2000.0, 4000.0),
)
IEC60118_4_A1_SYSTEM_NOISE_CEILING_DB = -47.0
IEC60118_4_A1_SYSTEM_NOISE_RISE_DB = 1.0

# ---------------------------------------------------------------------------
# IEC 60118-4:2014/A1:2017 Figure 2 (folio 7) and Figure 3 (folio 9), in
# millimetres. Figure 2 a): inner radius l2 = 300, outer radius l2 + l3 = 500,
# at 0 and plus or minus 45 degrees. Figure 2 b): l2 = 300, l3 = 200, l4 = 424,
# l5 = 700. Figure 3 a): l1 = l2 = 300, l4 = l5 = 150; Figure 3 b): l3 = 1 200,
# l2 = l1 = 250, so the heights are 1,2 m, 1,45 m and 1,7 m. Refuge heights
# 1,2 m and 1,7 m (9.2, folio 8).
# ---------------------------------------------------------------------------
IEC60118_4_A1_FIGURE2A_MM = {"inner_radius": 300.0, "outer_radius": 500.0}
IEC60118_4_A1_FIGURE2B_MM = {"l2": 300.0, "l3": 200.0, "l4": 424.0, "l5": 700.0}
IEC60118_4_A1_FIGURE3_MM = {"radius": 300.0, "lateral": 150.0}
IEC60118_4_A1_REFUGE_HEIGHTS_M = (1.2, 1.7)
IEC60118_4_A1_COUNTER_HEIGHTS_M = (1.2, 1.45, 1.7)

# ---------------------------------------------------------------------------
# IEC 60118-4:2014 Annex E. E.1 (folio 36): H = 2 sqrt(2) I / (pi d) at the
# centre of a square loop. E.2 (folio 37): 3 dB down at 45 degrees and 9,3 dB
# down at 70 degrees. E.3 (folio 43): R = 4 rho d / a, L = 8d microhenries, the
# impedance "1,4 times the resistance" where 2 pi f L = R. E.6 (folio 44):
# 1 Oe = 79,58 A/m, "the magnetic induction due to a field strength of 1 A/m
# is 1,256 microtesla".
# ---------------------------------------------------------------------------
IEC60118_4_TELECOIL_DB = {45.0: -3.0, 70.0: -9.3}

#: IEC 60118-4:2014 Figure E.2 b) (PDF page 40, folio 38), read off the curves:
#: the level re the field at the centre of the 15 by 10 loop in its plane, 1,2
#: units above it, against the position in percent of the loop dimension.
#: (component, position in percent) -> dB. The curves are the traverse across
#: the 10-unit width, as E.1 describes them; panel a) of the figure draws the
#: vertical-field line along the 15-unit length (see docs/ERRATA.md). Read to
#: about 0,1 dB where the curve is flat; the vertical curve sits some 0,2 dB
#: to 0,3 dB below a filament's field throughout.
IEC60118_4_FIGURE_E2B_DB = {
    ("horizontal", 2.5): 4.2,
    ("horizontal", 30.0): -15.0,
    ("vertical", 12.5): 1.7,
    ("vertical", 50.0): -0.8,
}
IEC60118_4_FIGURE_E2B_LOOP = (15.0, 10.0, 1.2)

#: IEC 60118-4:2014 Figure H.1 (PDF page 51, folio 49), read off the ends of
#: the curves at a shorter side of 10 m: the loop current in amperes that gives
#: 400 mA/m 1,4 m above the centre, against the aspect ratio. One pixel of the
#: read is 0,007 A; the lines are 3 to 5 pixels wide.
IEC60118_4_FIGURE_H1_AT_10_M_A = {1.0: 4.89, 1.5: 5.64, 2.0: 6.04, 3.0: 6.41, 5.0: 6.63}
IEC60118_4_E3_INDUCTANCE_UH_PER_M_SIDE = 8.0
IEC60118_4_E3_CORNER_FACTOR = 1.4
IEC60118_4_E6_OERSTED_A_PER_M = 79.58
IEC60118_4_E6_MICROTESLA_PER_A_PER_M = 1.256

# ---------------------------------------------------------------------------
# IEC 62489-1:2010+A1:2014. 5.2.2 (folio 9): standard measuring conditions at
# -10 dB re the rated output current. 5.4.10.2 (folio 13): the field at 1,4 m
# above the centre of a horizontal square loop. 5.4.13.4 (folio 14): an AGC
# input range of at least 32 dB for at most 3 dB of output change, THD+N at
# most 5 %. 5.4.14.1 (folio 15): "cos 85 degrees = 0,087, so the in-phase
# field is increased or decreased by 0,72 dB".
# ---------------------------------------------------------------------------
IEC62489_1_STANDARD_MEASURING_DB = -10.0
IEC62489_1_FIELD_HEIGHT_M = 1.4
IEC62489_1_AGC_RANGE_DB = 32.0
IEC62489_1_AGC_OUTPUT_CHANGE_DB = 3.0
IEC62489_1_QUADRATURE_EXAMPLE_DEG = 85.0
IEC62489_1_QUADRATURE_EXAMPLE_COS = 0.087
IEC62489_1_QUADRATURE_EXAMPLE_DB = 0.72

# ---------------------------------------------------------------------------
# IEC 62489-1:2010 Table B.1 (folio 22), "Typical loop characteristics":
# name, dimensions in m (a diameter for the neck loop), turns, printed
# perimeter in m, conductor area in mm2, resistance in ohm, inductance in
# microhenries, impedance at 2 kHz and at 5 kHz in ohm. The counter loop's
# perimeter is printed 1,5; its sides make it 1,6 (see docs/ERRATA.md).
# ---------------------------------------------------------------------------
IEC62489_1_TABLE_B1 = (
    ("neck loop", (0.22,), 10, 0.7, 0.5, 0.24, 85.0, 1.09, 2.67),
    ("counter loop", (0.35, 0.45), 10, 1.5, 0.75, 0.37, 189.0, 2.41, 5.96),
    ("home loop", (3.0, 4.0), 1, 14.0, 1.0, 0.24, 22.0, 0.37, 0.74),
    ("small room", (6.0, 8.0), 1, 28.0, 1.5, 0.32, 47.0, 0.67, 1.52),
    ("typical place of worship", (10.0, 20.0), 1, 60.0, 1.5, 0.69, 109.0, 1.54, 3.50),
    ("large place of worship", (15.0, 40.0), 1, 110.0, 2.5, 0.76, 218.0, 2.85, 6.89),
)
#: The rows whose inductance Grover's Formula (58), without the internal
#: term, reproduces to the printed microhenry.
IEC62489_1_TABLE_B1_INDUCTANCE_REPRODUCED = (
    "counter loop",
    "home loop",
    "small room",
    "typical place of worship",
)

# ---------------------------------------------------------------------------
# IEC 62489-1:2010+A1:2014 9.2.3 (folio 17): recommended rated input
# impedances of a neck loop. prEN 62489-1:2010/prA2:2017 D.1.2 and D.1.3 (a
# draft; CDV folio 5): type 1, 32 ohm plus or minus 5 %; type 2, at least
# 32 ohm; both 1,06 V for 400 mA/m on the jig.
# ---------------------------------------------------------------------------
IEC62489_1_NECK_LOOP_IMPEDANCES_OHM = (8.0, 16.0, 32.0)
IEC62489_1_A2_DRAFT_TYPE1_OHM = 32.0
IEC62489_1_A2_DRAFT_TYPE1_TOL_PERCENT = 5.0
IEC62489_1_A2_DRAFT_TYPE2_MIN_OHM = 32.0
IEC62489_1_A2_DRAFT_MAX_INPUT_V = 1.06

# ---------------------------------------------------------------------------
# IEC 60028:1925 (2nd edition), clause I (1) and (4) (PDF page 7, folio 5):
# standard annealed copper, 1/58 = 0,017241 ohm mm2/m at 20 degrees Celsius,
# temperature coefficient 0,00393 = 1/254,45 per degree.
# ---------------------------------------------------------------------------
IEC60028_COPPER_OHM_MM2_PER_M = 1.0 / 58.0
IEC60028_COPPER_ALPHA_PER_K = 0.00393
