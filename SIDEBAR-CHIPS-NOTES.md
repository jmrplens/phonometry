# Sidebar reference chips: classification and decisions

Experimental branch `exp/sidebar-standard-chips`. Every content item in the
sidebar carries a Starlight badge that states, at a glance, what governs the
page:

- `chip-standard` (colour A, teal): the page implements one or more published
  standards; the chip shows the short designation(s).
- `chip-theory` (colour B, amber): no governing standard; the chip shows the
  single most notable reference (author-year or short book/method tag).
- no chip: only navigational or overview items (see the list at the end).

Mechanism: guide items set `badge: { text, class }` on their sidebar entry in
`site/astro.config.mjs`; API-reference items get the same badge emitted by the
generator (`scripts/generate_api_docs.py`, dict `_API_CHIPS`) into
`site/src/generated/api-sidebar.mjs`. Styling is in
`site/src/styles/sidebar-chips.css` (unlayered, theme-aware, WCAG AA).

Attribution is sourced from each page's own material: guides from their
frontmatter `references` block (`type: standard` -> `designation`, or the
leading bibliography entry for theory); API modules from their docstring
(cited standard, or named author). Standard designations are truncated to the
family (no year/part suffix) for compactness; combined chips like
`ISO 16283 / 717` or `ISO 2631 / 5349` are used where two families jointly
govern a page and both read fine on mobile.

## Task 1: sidebar labels with the standard stripped

Set an explicit `label` (+ `translations.es`) on the sidebar entry so the chip
carries the designation and the label stays a clean topic name. The page H1 /
frontmatter title is untouched (reversible: delete the label to restore).

| Slug | Before (EN) | After (EN) | After (ES) |
|---|---|---|---|
| dynamic-stiffness | Dynamic stiffness of resilient materials (EN 29052-1) | Dynamic stiffness of resilient materials | Rigidez dinámica de materiales resilientes |
| enclosed-space-absorption | Sound absorption in enclosed spaces (EN 12354-6) | Sound absorption in enclosed spaces | Absorción sonora en recintos |
| impulse-prominence | Impulsive-sound prominence (NT ACOU 112) | Impulsive-sound prominence | Prominencia de sonidos impulsivos |
| installed-structure-borne | Installed structure-borne sound (EN 12354-5) | Installed structure-borne sound | Ruido estructural instalado |
| insulation-prediction | Predicting Sound Insulation (EN 12354) | Predicting Sound Insulation | Predicción del aislamiento acústico |
| mechanical-mobility | Mechanical mobility and the FRF family (ISO 7626-1) | Mechanical mobility and the FRF family | Movilidad mecánica y la familia de FRF |
| multiple-shock-vibration | Multiple-shock whole-body vibration (ISO 2631-5) | Multiple-shock whole-body vibration | Vibración con choques múltiples |
| noise-induced-hearing-loss | Noise-induced hearing loss (ISO 1999) | Noise-induced hearing loss | Pérdida auditiva inducida por ruido |
| occupational-exposure | Occupational Noise Exposure (ISO 9612) | Occupational Noise Exposure | Exposición al ruido en el trabajo |
| structure-borne-power | Structure-borne sound power of equipment (EN 15657) | Structure-borne sound power of equipment | Potencia sonora estructural de equipos |
| tone-audibility | Objective audibility of tones in noise (ISO/PAS 20065) | Objective audibility of tones in noise | Audibilidad objetiva de tonos en ruido |
| tone-prominence | Prominent Discrete Tones (ECMA-418-1) | Prominent Discrete Tones | Tonos discretos prominentes |
| transfer-stiffness | Transfer stiffness of resilient elements (ISO 10846) | Transfer stiffness of resilient elements | Rigidez dinámica de transferencia |
| vibration-sound-power | Sound power from surface vibration (ISO/TS 7849) | Sound power from surface vibration | Potencia acústica desde vibración |
| program-loudness | Programme loudness and true peak (BS.1770 / EBU R 128) | Programme loudness and true peak | Sonoridad de programa y pico verdadero |

## Task 2: full guide classification

Standard chips (teal), attribution = leading `type: standard` designation in
that guide's frontmatter:

| Guide | Chip | Guide | Chip |
|---|---|---|---|
| sound-level-meter | IEC 61672 | filter-banks | IEC 61260 |
| block-processing | IEC 61260 | multichannel | IEC 61260 |
| weighting | IEC 61672 | time-weighting | IEC 61672 |
| levels | IEC 61672 | calibration | IEC 60942 |
| gum-uncertainty | JCGM 100 | test-signals | IEC 60268-1 |
| loudness | ISO 532-1 | sound-quality | DIN 45692 |
| tone-prominence | ECMA-418-1 | tone-audibility | ISO/PAS 20065 |
| speech-transmission | IEC 60268-16 | speech-intelligibility | ANSI S3.5 |
| hearing-threshold | ISO 7029 | noise-induced-hearing-loss | ISO 1999 |
| occupational-exposure | ISO 9612 | room-acoustics | ISO 3382 |
| room-noise | ANSI S12.2 | enclosed-space-absorption | EN 12354-6 |
| insulation-field | ISO 16283 / 717 | insulation-lab | ISO 10140 |
| insulation-prediction | EN 12354 | dynamic-stiffness | EN 29052-1 |
| materials | ISO 11654 | surface-scattering | ISO 17497 |
| mechanical-mobility | ISO 7626 | transfer-stiffness | ISO 10846 |
| vibration-sound-power | ISO/TS 7849 | structure-borne-power | EN 15657 |
| installed-structure-borne | EN 12354-5 | human-vibration | ISO 2631 / 5349 |
| multiple-shock-vibration | ISO 2631-5 | outdoor-propagation | ISO 9613 |
| impulse-prominence | NT ACOU 112 | aircraft-noise | ICAO Annex 16 |
| wind-turbine-noise | IEC 61400-11 | underwater-acoustics | ISO 18405 |
| intensity | ISO 9614 | sound-power | ISO 3744 |
| electroacoustics | IEC 60268 | program-loudness | EBU R 128 |

Theory chips (amber), attribution = leading bibliography entry / named method
in that guide's frontmatter:

| Guide | Chip | Source |
|---|---|---|
| spectral-analysis | Welch 1967 | Welch overlapped-segment PSD |
| miso-coherence | Bendat & Piersol | Random Data, ch. 7 |
| time-frequency | Bendat & Piersol | Random Data, section 12.6 |
| cepstrum-echoes | Havelock et al. | Handbook of Signal Processing in Acoustics |
| synchronous-averaging | McFadden 1987 | revised TSA model |
| correlation-delay | Knapp & Carter | generalized correlation (GCC) |
| data-qualification | Bendat & Piersol | Random Data (stationarity, Rice) |
| system-measurement | Havelock et al. | Handbook of Signal Processing in Acoustics |
| psychoacoustic-annoyance | Fastl & Zwicker | Psychoacoustics: Facts and Models |
| objective-intelligibility | Taal et al. 2011 | STOI |
| room-image-sources | Kuttruff | Room Acoustics |
| reverberation-prediction | Sabine / Eyring | classical RT formulae |
| panel-sound-insulation | Bies & Hansen | Engineering Noise Control |
| porous-absorbers | Mechel | Formulas of Acoustics (ed.) |
| junction-transmission | Cremer & Heckl | Structure-Borne Sound |
| ground-barriers | Attenborough | Predicting Outdoor Sound |
| atmospheric-refraction | Salomons | Computational Atmospheric Acoustics |
| rotorcraft-noise | Olsen et al. | hemisphere method |
| underwater-propagation | Francois & Garrison | absorption / TL |
| swept-sine-distortion | Farina 2000 | exponential sweep |
| noise-control | Bies & Hansen | Engineering Noise Control |
| fdtd-simulation | Botteldooren 1995 | added: canonical 2D acoustic FDTD (page bibliography leads with a general outdoor-sound text) |

## Task 2: full API-reference classification (`_API_CHIPS`)

Standard chips (teal): core `IEC 61260`, parametric-filters `IEC 61672`,
frequencies `ISO 266`, compliance `IEC 61260`; levels `IEC 61672`, calibration
`IEC 60942`; loudness-zwicker `ISO 532-1`, loudness-moore-glasberg `ISO 532-2`,
loudness-moore-glasberg-time `ISO 532-3`, loudness-ecma `ECMA-418-2`,
loudness-contours `ISO 226`, sharpness `DIN 45692`, roughness-ecma
`ECMA-418-2`, tonality `ECMA-418-1`, tonality-ecma `ECMA-418-2`, tone-audibility
`ISO/PAS 20065`, fluctuation-strength-ecma `ECMA-418-2`; sti `IEC 60268-16`,
sii `ANSI S3.5`; threshold `ISO 7029`, noise-induced-hearing-loss `ISO 1999`,
occupational-exposure `ISO 9612`; room-acoustics `ISO 3382`, room-ir
`ISO 18233`, room-noise `ANSI S12.2`, open-plan `ISO 3382-3`,
enclosed-space-absorption `EN 12354-6`; insulation `ISO 16283 / 717`,
panel-transmission `EN 12354-1`, lab-insulation `ISO 10140`, survey-insulation
`ISO 10052`, intensity-insulation `ISO 15186`, flanking-transmission
`ISO 10848`, facade-prediction `EN 12354-3`, building-prediction `EN 12354`,
building-uncertainty `ISO 12999-1`, floor-covering-improvement `ISO 16251-1`,
structure-borne-power `EN 15657`, installed-structure-borne `EN 12354-5`;
sound-absorption `ISO 354`, absorption-rating `ISO 11654`, absorption-uncertainty
`ISO 12999-2`, airflow-resistance `ISO 9053`, dynamic-stiffness `EN 29052-1`,
impedance-tube `ISO 10534`, scattering-diffusion `ISO 17497`, road-absorption
`ISO 13472`; mechanical-mobility `ISO 7626`, point-mobility `ISO 7626`,
radiation-efficiency `ISO/TS 7849`, transfer-stiffness `ISO 10846`,
human-vibration `ISO 2631 / 5349`, multiple-shock-vibration `ISO 2631-5`;
outdoor-propagation `ISO 9613`, ground-barriers `ISO 9613-2`, air-absorption
`ISO 9613-1`, impulse-prominence `NT ACOU 112`, impulsive-sound `ISO/PAS 1996-3`,
rating `ISO 1996-1`, measurement `ISO 1996-2`; aircraft-noise `ICAO Annex 16`,
atmospheric-absorption `SAE ARP 5534`, airport-noise `ECAC Doc 29`, anp-fleet
`ECAC Doc 29`, wind-turbine-noise `IEC 61400-11`; acoustics `ISO 18405`,
ship-radiated-noise `ISO 17208`, pile-driving-noise `ISO 18406`; sound-power
`ISO 3744`, sound-power-intensity `ISO 9614`, sound-power-reverberation
`ISO 3741`, intensity `ISO 9614`, vibration-sound-power `ISO/TS 7849`,
declaration `ISO 4871`; distortion `IEC 60268-3`, loudspeaker `IEC 60268-5`,
microphone `IEC 60268-4`; program-loudness `EBU R 128`; uncertainty `JCGM 100`.

Theory chips (amber): equalizer `RBJ Cookbook`; fluctuation-strength
`Fastl & Zwicker`, psychoacoustic-annoyance `Fastl & Zwicker`;
objective-intelligibility `Taal et al. 2011`; reverberation-prediction
`Sabine / Eyring`, image-source `Kuttruff`, steady-field `Kuttruff`;
aperture-transmission `Hopkins 2007`; porous-absorber `Mechel`;
junction-transmission `Cremer & Heckl`; atmospheric-refraction `Salomons`,
rotorcraft-noise `Olsen et al.`; propagation `Francois & Garrison`, sound-speed
`Mackenzie 1981` (+), sonar-equation `Urick`, ocean-ambient-noise `Wenz 1962`,
seabed-reflection `Jensen et al.` (+), ship-traffic-noise `JOMOPANS-ECHO`,
numerical-propagation `Jensen et al.` (+); frequency-response `Bendat & Piersol`,
swept-sine `Farina 2000`, piston `Beranek & Mellow`; silencers/hvac/enclosures
`Bies & Hansen`; random-data `Bendat & Piersol`; spectra `Welch 1967`, miso
`Bendat & Piersol`, time-frequency `Bendat & Piersol`, signals `Bendat & Piersol`,
phase `Farina 2000`, cepstrum `Havelock et al.`, synchronous-average
`McFadden 1987`, inversion `Farina 2000`; fdtd `Botteldooren 1995` (+);
correlation `Bendat & Piersol`, envelope `Bendat & Piersol`.

`(+)` marks a minimal canonical attribution added where the module docstring
names no source (underwater sound-speed / seabed / numerical solvers, and the
2D FDTD simulation). Everything else is quoted from the docstring's own cited
standard or named author.

## No chip (navigational / overview only)

- getting-started, reference/why-phonometry
- every group landing page `guides/sections/*` (Overview-first group links)
- API index `reference/api`, and `reference/api/filters/phonometry` (the package
  top level: only `__version__` and `PhonometryWarning`, no standard/reference)
- reference/theory landing and the six `reference/theory/*` cross-cutting
  overviews, reference/conformance, reference/bibliography

## Colours (theme-aware, WCAG AA)

Defined as CSS custom properties, dark values on `:root` (the default the
maintainer browses in) and light values on `:root[data-theme='light']`.

- Standard (teal): dark bg `#0e3b35` / text `#7ee8d5`; light bg `#d3f4ec` / text `#0c5c52`.
- Theory (amber): dark bg `#3c2e0c` / text `#f4c04e`; light bg `#fbeecd` / text `#855107`.

## Extending / regenerating

Guides: each entry in `astro.config.mjs` is `{ slug, badge: { text, class } }`
(plus `label`/`translations` where the title was stripped). API: edit
`_API_CHIPS` in `scripts/generate_api_docs.py` and run `make api-docs`
(`PYTHONPATH=src python3 scripts/generate_api_docs.py`) to regenerate
`api-sidebar.mjs`; the chip survives regeneration.
