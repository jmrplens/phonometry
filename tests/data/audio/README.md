# Real measurement audio: functional oracles with published values

Third-party measurement recordings and series derived from them, included in
this repository **for validation**: each file comes with a value its authors
published, the test suite computes that value through the library's own
reading and measurement chain, and a few guides of the documentation work the
same computation through in front of the reader. They are test data, not part
of the `phonometry` package; they are not installed with it, and this
repository's MIT licence does **not** cover them: the licences named below
do. The general rules for committed oracle data are in `tests/data/README.md`.

## What this folder contains

| File | Kind | Consumed by |
| :--- | :--- | :--- |
| `xl2/calibration_113_7dB.wav` | byte-identical (renamed) | `tests/signals/test_xl2_passby_oracle.py`; the guide `io/audio-files` |
| `xl2/passby_*.wav` (5 files) | bit-exact 4 s extracts | `tests/signals/test_xl2_passby_oracle.py`; the guide `perception/psychoacoustics/loudness` |
| `sounddevices/A101_3.WAV` | byte-identical | `tests/io/test_io_real_bwf.py` |
| `libbw64/rect_24bit_rf64.wav` | byte-identical | `tests/io/test_io_real_rf64.py` |
| `nikolauskapelle/s1_do_r1_w.npz` | derived (one channel) | `tests/room/test_room_nikolauskapelle_oracle.py`; the guide `buildings/rooms/room-acoustics` and its figure `room_parameters_chapel` |
| `dublin/dcc_laeq_5min_2015.npz` | derived (level series) | `tests/environment/assessment/test_dublin_dcc_oracle.py`; the guide `environment/assessment/environmental-levels` |

A guide is named by its route: the English page is
`site/src/content/docs/<route>.mdx` and its Spanish twin
`site/src/content/docs/es/<route>.mdx`. Both read the file from a checkout and
print the attribution below, and so does the guide's GitHub copy under
`docs/`, which `make llms` writes from the English page.

## Source, licence and attribution, file by file

Each folder's attribution is the bold string after `Attribution:`, which every
English page that reads the folder prints as written, and, where a Spanish page
reads the folder, the bold string after `Atribución:`, which the Spanish page
prints. The page may set a link on a run of the words (the DOI, the licence)
and wrap the string over its lines; nothing else in it changes. `tests/test_data_attribution.py` holds every page
to it.

### `xl2/`: NTi XL2 pass-by campaign, University of Antwerp (CC BY 4.0)

Attribution: **"Pass-by excerpts from A. Grangeiro de Barros and C. Vuye,
'Psychoacoustic indicators of pass-by road traffic noise', Zenodo, 2023, DOI
10.5281/zenodo.7904680, licensed CC BY 4.0, recorded with an NTi Audio XL2.
Changes: 4-second extracts cut bit-exactly and recontainered."**

Atribución: **"Fragmentos de pasos de vehículos de A. Grangeiro de Barros y
C. Vuye, «Psychoacoustic indicators of pass-by road traffic noise», Zenodo,
2023, DOI 10.5281/zenodo.7904680, con licencia CC BY 4.0, grabados con un
sonómetro NTi Audio XL2. Cambios: extractos de 4 segundos cortados bit a bit y
guardados en un contenedor nuevo."**

Licence: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Retrieved
from the Zenodo deposit (version 2, published 2023-05-24) on 2026-08-18
(archive checksum verified against the record).

- `calibration_113_7dB.wav` is byte-identical to `Calibration file 1Hz
  113.7 dB.wav` of the deposit (renamed here; the "1Hz" of the original
  name is the depositors' typo for the 1 kHz calibrator tone). PCM 24-bit
  mono 48 kHz, written by the meter itself: the `bext` chunk carries
  `Originator "NTi Audio XL2 A2A-17367-E0"` and `Description "0dBFS =
  129.3 dBSPL"`. Published value: the deposit names and describes it as
  the **113.7 dB** calibration recording of the campaign's sound level
  meter and microphone. **Change with respect to the original file: renamed;
  bytes unmodified.** A page that reads this file alone prints the folder's
  attribution and says the take is the deposit's own file, renamed.
- `passby_*.wav` are five 4-second pass-by excerpts (one per vehicle
  category and speed named in the file name), cut **bit-exactly** (whole
  24-bit sample codes, unmodified) from the campaign's hour-long session
  recordings at the sample ranges given by the deposit's timestamp
  workbooks, and repackaged in a minimal `fmt `+`data` RIFF container.
  The session `bext` chunks are deliberately not copied into the cuts, so
  no instrument metadata is misattributed to an excerpt the instrument
  did not write; each session's digital full scale (0 dBFS = 129.4 or
  129.5 dB SPL) is transcribed in the consuming test and the guide instead,
  next to the published values it calibrates. **Changes with respect to the
  original files: cut and recontainered as described; sample data
  unmodified.** Published values: the deposit's master workbook
  `Psychoacoustic indicators of pass-by road traffic noise.xlsx` lists, per
  pass-by, LA,eq, LA,max, L10 and the median Zwicker loudness N50 computed by
  the authors; the five rows used (indices 566, 571, 668, 960 and 1558) are
  transcribed in the consuming test and the guide.

### `sounddevices/`: wavinfo test file (MIT)

Attribution: **"A101_3.WAV from the wavinfo project
(https://github.com/iluvcapra/wavinfo), MIT License, Copyright (c)
2018-2023 Jamie Hardt."** Retrieved from the wavinfo repository on
2026-08-18.

A real BWF written by a Sound Devices 702T field recorder: `bext` version 1
with every string field populated by the machine, plus a 5.2 kB `iXML`
chunk. Byte-identical to `tests/test_files/sounddevices/A101_3.WAV` of the
wavinfo repository. The wavinfo documentation documents this recorder's
`bext` output on the sibling take `A101_1.WAV`; the expected field values
for this file are transcribed in the consuming test and were cross-read
with an independent reader (ffprobe) at import time.

### `libbw64/`: EBU libbw64 test file (Apache License 2.0)

Attribution: **"rect_24bit_rf64.wav from the EBU libbw64 project
(https://github.com/ebu/libbw64), Apache License 2.0
(https://www.apache.org/licenses/LICENSE-2.0)."** Retrieved from the
libbw64 repository on 2026-08-18.

A genuine RF64 file (`RF64` FourCC with a `ds64` chunk), PCM 24-bit
44.1 kHz stereo, byte-identical to `tests/test_data/rect_24bit_rf64.wav` of
the libbw64 repository. It is the small real-world RF64 the reader is
validated against; the expected sample codes of its rectangular wave are
asserted exactly.

### `nikolauskapelle/`: St. Nicholas Chapel RIR, FH Aachen (CC BY 4.0)

Attribution: **"Omnidirectional channel of the S1-Do_R1 impulse response from
M. Zerwas and S. Kayku, 'Room acoustic measurement and decay analysis data of
the St. Nicholas Chapel, Aachen Cathedral', Zenodo, 2026, DOI
10.5281/zenodo.20428705, licensed CC BY 4.0. Change: one channel of four
extracted and repackaged."**

Atribución: **"Canal omnidireccional de la respuesta al impulso S1-Do_R1 de
M. Zerwas y S. Kayku, «Room acoustic measurement and decay analysis data of
the St. Nicholas Chapel, Aachen Cathedral», Zenodo, 2026, DOI
10.5281/zenodo.20428705, con licencia CC BY 4.0. Cambio: se extrajo uno de los
cuatro canales y se volvió a empaquetar."**

Licence: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Retrieved
from the Zenodo deposit (version 1.0, published 2026-05-28) on 2026-08-18.
The title is the one the DOI carries today: on the day of retrieval this file
named the deposit "Room acoustic measurement and simulation data of the
St. Nicholas Chapel, Aachen Cathedral", and the record has since been
retitled, version 1.0 included, to the title above.

`s1_do_r1_w.npz` holds the W (omnidirectional) channel of the B-format
impulse response `S1-Do_R1.wav` from the deposit's
`impulse_responses.zip`, as `w` (float32 samples exactly as stored in the
original file) and `fs` (48000). **Changes with respect to the original
file: one channel of four extracted and repackaged as npz; sample data
unmodified.** Published values: the deposit's workbook
`Nikolauskapelle_Source1_Results_20260205.xlsx` tabulates the ISO 3382-1
room acoustic parameters (EDT, T20, T30, C80, C50, D50, Ts) of this
source-receiver pair per one-third-octave band; the rows used are
transcribed in the consuming test and the guide.

### `dublin/`: DCC Ambient Sound Monitoring Network (CC BY 4.0)

Attribution: **"Five-minute LAeq series from the Dublin City Council Ambient
Sound Monitoring Network (Ballymun and Ringsend, 2015), Smart Dublin /
data.gov.ie, licensed CC BY 4.0. Changes: daily logs concatenated, sorted and
de-duplicated; level values unmodified."**

Atribución: **"Serie de LAeq de cinco minutos de la Ambient Sound Monitoring
Network del Ayuntamiento de Dublín (Ballymun y Ringsend, 2015), Smart Dublin /
data.gov.ie, con licencia CC BY 4.0. Cambios: registros diarios concatenados,
ordenados y sin duplicados; valores de nivel sin modificar."**

Licence: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Retrieved
from data.gov.ie (dataset "Ambient Sound Monitoring Network DCC",
https://data.gov.ie/dataset/ambient-sound-monitoring-network) on 2026-08-18,
together with the annual report from dublincity.ie.

`dcc_laeq_5min_2015.npz` is a derived series, not audio: for each site,
`<site>_time0_s` (first interval-end stamp, in seconds since 2015-01-01
00:00 local time), `<site>_dt_s` (differences between consecutive stamps)
and `<site>_laeq_cdb` (the five-minute A-weighted Leq values in hundredths
of a dB, an exact transcription of the two-decimal source). **Changes with
respect to the original files: the daily text logs were concatenated,
sorted, de-duplicated (49 stamps re-measured around a monitor restart on
2015-05-15 keep their first value) and repacked as npz; the level values
are unmodified.** Published values: the DCC "Ambient Sound Monitoring
Network Annual Report For 2015" (dublincity.ie) tabulates each site's annual
Lday, Levening, Lnight and LDEN in whole decibels in its Fig. 3 (p. 11),
Ballymun **65, 63, 58 and 67 dB(A)** and Ringsend **59, 60, 59 and
65 dB(A)**, and its text on the same page quotes the night levels, 58 and
59 dB(A); it declares logarithmic (energetic) averaging (p. 8), the evening
as 19:00-23:00 and the night as 23:00-07:00 (p. 9).

## Purpose and scope of use

These files exist so that the reading chain (`phonometry.io`) and the
measurement functions can be validated end to end against **real recordings
with independently published values**, in CI, without any local download,
and so that a guide can show a reader the same computation on the same data.
Every licence above permits redistribution: two deposits and the Dublin
series under CC BY 4.0 (attribution given here and on every page that reads
them, changes indicated above), one file under MIT and one under Apache
License 2.0 (notices preserved here). What is deliberately **not** committed:
the campaigns' full recordings (13.2 GB of pass-by audio, the 271 MB
impulse-response set), the deposits' workbooks, and the four-channel version
of the RIR: the tests and the guides transcribe the handful of published
numbers they compare with instead.

## Removal policy

If you are an author or rights holder of any of these datasets and consider
that this redistribution exceeds the intended use, please open an issue or
contact the maintainer (see `CITATION.cff`) and the file will be removed
promptly, together with everything the table above lists for it: the test
module, and for the three CC BY folders the worked case of each guide that
reads it in both languages, the guide's reference to the deposit, and the
figure drawn from it (`room_parameters_chapel` for the chapel). Nothing else
in the repository depends on this folder.
