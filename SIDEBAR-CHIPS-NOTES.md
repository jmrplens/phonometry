# Sidebar reference chips: classification and decisions

Experimental branch `exp/sidebar-standard-chips`. Every content item in the
sidebar carries one or more small colour-coded chips (Starlight badges) that
state, at a glance, what governs the page:

- teal `chip-standard`: a published standard the page implements (short
  designation).
- amber `chip-theory`: a notable reference / investigator the method is
  attributed to (author-year or short book/method tag).
- an item may carry BOTH (mixed): the governing standard(s) plus the
  author(s) the method is named after.
- no chip: only navigation / overview items (list at the end).

## Multi-chip mechanism

Starlight's native `badge` slot is a single badge. To carry a LIST of
independent chips per item, the list is threaded through Starlight's
sanctioned `attrs` passthrough as a JSON string under `data-chips`.

- In `site/astro.config.mjs`: helpers `S(text)` (teal), `T(text)` (amber) and
  `chips(...)` build the entry, e.g.
  `{ slug: 'guides/room-acoustics', ...chips(S('ISO 3382'), S('ISO 18233'), T('Schroeder 1965')) }`.
  `chips(...)` returns `{ attrs: { 'data-chips': JSON.stringify(items) } }`.
- In the API generator `scripts/generate_api_docs.py`: `_API_CHIPS` maps each
  module to a tuple of `(text, kind)` pairs; `render_sidebar` emits the same
  `attrs.data-chips` JSON into `site/src/generated/api-sidebar.mjs`.
- `site/src/components/SidebarSublist.astro` parses `attrs['data-chips']`
  (`parseChips`), renders one `<Badge>` per chip inside a `.sidebar-chips`
  container, and drops the raw attribute from the `<a>` (`withoutChips`) so it
  is not echoed into the DOM.
- `site/src/styles/sidebar-chips.css`: `.sidebar-chips` is an
  `inline-flex; flex-wrap: wrap; gap: 0.25em` container, so several chips sit
  after the label and wrap onto a new line beneath it on narrow columns with
  no horizontal overflow. Chip colours are unlayered and theme-aware (dark
  values on `:root`, light on `:root[data-theme='light']`), both text-on-fill
  pairs clear WCAG AA.

Attribution stays sourced from each page's own material: guides from their
frontmatter `references` block (all relevant `type: standard` designations,
and the `type: article`/named-method entries for the author chips); API
modules from their docstrings. Standard designations are shortened to the
family; parts of one standard collapse to one chip (ISO 3382-1/-2/-3 ->
`ISO 3382`), distinct standards get separate chips.

## Stripped sidebar labels (chip carries the designation / author list)

Set via `label` + `translations.es` on the sidebar entry; page H1/frontmatter
titles are untouched (reversible). New this pass: `reverberation-prediction`
(the `(Sabine, Eyring, Arau)` author list moved into chips). The other 15 were
stripped in the earlier pass and are kept:

| Slug | After (EN) | After (ES) |
|---|---|---|
| reverberation-prediction | Reverberation-time prediction | Predicción del tiempo de reverberación |
| dynamic-stiffness | Dynamic stiffness of resilient materials | Rigidez dinámica de materiales resilientes |
| enclosed-space-absorption | Sound absorption in enclosed spaces | Absorción sonora en recintos |
| impulse-prominence | Impulsive-sound prominence | Prominencia de sonidos impulsivos |
| installed-structure-borne | Installed structure-borne sound | Ruido estructural instalado |
| insulation-prediction | Predicting Sound Insulation | Predicción del aislamiento acústico |
| mechanical-mobility | Mechanical mobility and the FRF family | Movilidad mecánica y la familia de FRF |
| multiple-shock-vibration | Multiple-shock whole-body vibration | Vibración con choques múltiples |
| noise-induced-hearing-loss | Noise-induced hearing loss | Pérdida auditiva inducida por ruido |
| occupational-exposure | Occupational Noise Exposure | Exposición al ruido en el trabajo |
| structure-borne-power | Structure-borne sound power of equipment | Potencia sonora estructural de equipos |
| tone-audibility | Objective audibility of tones in noise | Audibilidad objetiva de tonos en ruido |
| tone-prominence | Prominent Discrete Tones | Tonos discretos prominentes |
| transfer-stiffness | Transfer stiffness of resilient elements | Rigidez dinámica de transferencia |
| vibration-sound-power | Sound power from surface vibration | Potencia acústica desde vibración |
| program-loudness | Programme loudness and true peak | Sonoridad de programa y pico verdadero |

Not stripped by choice: `weighting` keeps `(A, B, C, D, G, AU, Z)` and
`room-noise` keeps `(NC / RC Mark II)` because those are metric/curve names
that describe the topic, not standard designations or investigator names.

## Full guide chip sets

Format: item -> [teal standards] + [amber refs]. `S` = teal, `T` = amber.

- sound-level-meter: IEC 61672, IEC 61260, IEC 60942
- filter-banks: IEC 61260, ISO 266
- block-processing: IEC 61260, IEC 61672
- multichannel: IEC 61260, IEC 61672
- weighting: IEC 61672, ISO 7196, ISO 226 + Fletcher & Munson
- time-weighting: IEC 61672
- levels: IEC 61672, ISO 1996-1
- spectral-analysis: Welch 1967 + Harris 1978 + Thomson 1982
- miso-coherence: Bendat & Piersol
- time-frequency: Bendat & Piersol
- cepstrum-echoes: Havelock et al. + Bendat & Piersol
- synchronous-averaging: McFadden 1987
- correlation-delay: Knapp & Carter
- test-signals: IEC 60268-1 + Bendat & Piersol
- system-measurement: Golay 1961 + Kirkeby & Nelson + Müller & Massarani
- calibration: IEC 60942, IEC 61672-3
- gum-uncertainty: JCGM 100, JCGM 101
- data-qualification: Rice 1945 + Wald & Wolfowitz + Bendat & Piersol
- loudness: ISO 532, ISO 226, ECMA-418-2 + Fletcher & Munson
- sound-quality: DIN 45692, ECMA-418-2 + Fastl & Zwicker
- tone-prominence: ECMA-418-1, ECMA-74
- tone-audibility: ISO/PAS 20065, ISO 1996-2, DIN 45681
- psychoacoustic-annoyance: Fastl & Zwicker + Osses et al. 2016
- speech-transmission: IEC 60268-16 + Houtgast & Steeneken
- speech-intelligibility: ANSI S3.5 + French & Steinberg
- objective-intelligibility: Taal et al. 2011 + Jensen et al. 2016
- hearing-threshold: ISO 7029, ISO 389-7
- noise-induced-hearing-loss: ISO 1999 + Passchier-Vermeer
- occupational-exposure: ISO 9612
- room-acoustics: ISO 3382, ISO 18233 + Schroeder 1965
- room-image-sources: Allen & Berkley + Kuttruff
- room-noise: ANSI S12.2 + Beranek 1957 + Blazier 1997
- reverberation-prediction: EN 12354-6 + Sabine + Eyring + Arau
- enclosed-space-absorption: EN 12354-6, ISO 354
- insulation-field: ISO 16283, ISO 717, ISO 12999-1
- insulation-lab: ISO 10140, ISO 15186, ISO 10848, ISO 717
- insulation-prediction: EN 12354 + Hopkins
- panel-sound-insulation: Bies & Hansen + Cremer & Heckl
- dynamic-stiffness: EN 29052-1
- materials: ISO 11654, ISO 354, ISO 10534, ISO 9053
- porous-absorbers: Delany & Bazley + Miki + Johnson et al. + Maa
- surface-scattering: ISO 17497, ISO 13472 + Cox & D'Antonio
- mechanical-mobility: ISO 7626 + Cremer & Heckl
- junction-transmission: Cremer & Heckl + Craik
- transfer-stiffness: ISO 10846
- vibration-sound-power: ISO/TS 7849
- structure-borne-power: EN 15657, ISO 9611
- installed-structure-borne: EN 12354-5
- human-vibration: ISO 8041, ISO 2631, ISO 5349
- multiple-shock-vibration: ISO 2631-5
- outdoor-propagation: ISO 9613 + Maekawa 1968
- ground-barriers: Kurze & Anderson + Hadden & Pierce
- atmospheric-refraction: Salomons
- impulse-prominence: NT ACOU 112, ISO 1996-1
- aircraft-noise: ICAO Annex 16, IEC 61265, SAE ARP 5534
- rotorcraft-noise: Olsen et al. 2024 + Chien & Soroka
- wind-turbine-noise: IEC 61400-11, ISO 1996-2
- underwater-acoustics: ISO 18405, ISO 17208, ISO 18406
- underwater-propagation: Francois & Garrison + Wenz 1962 + Mackenzie 1981
- intensity: IEC 61043, ISO 9614
- sound-power: ISO 3744, ISO 3741, ISO 9614, ISO 4871
- electroacoustics: IEC 60268, AES17
- swept-sine-distortion: Farina 2000 + Novak et al. 2015
- noise-control: Bies & Hansen + Munjal
- program-loudness: ITU-R BS.1770, EBU R 128
- fdtd-simulation: Botteldooren 1995

## Full API chip sets (`_API_CHIPS`, module -> chips)

Single-standard modules keep their one teal chip; the mixed / multiple ones:
- compliance: IEC 61260, IEC 61672
- loudness_zwicker: ISO 532-1 + Zwicker
- loudness_moore_glasberg: ISO 532-2 + Moore & Glasberg
- loudness_moore_glasberg_time: ISO 532-3 + Moore & Glasberg
- sti: IEC 60268-16 + Houtgast & Steeneken
- sii: ANSI S3.5 + French & Steinberg
- objective_intelligibility: Taal et al. 2011 + Jensen et al. 2016
- threshold: ISO 7029, ISO 389-7
- room_acoustics: ISO 3382, ISO 18233 + Schroeder 1965
- room_noise: ANSI S12.2 + Beranek 1957 + Blazier 1997
- reverberation_prediction: Sabine + Eyring + Arau
- insulation: ISO 16283, ISO 717 (split)
- impedance_tube: ISO 10534, ASTM E2611
- porous_absorber: Delany & Bazley + Miki + Johnson et al.
- scattering_diffusion: ISO 17497 + Cox & D'Antonio
- radiation_efficiency: ISO/TS 7849 + Cremer & Heckl
- human_vibration: ISO 2631, ISO 5349, ISO 8041 (split)
- outdoor_propagation: ISO 9613 + Maekawa 1968
- ground_barriers: ISO 9613-2 + Kurze & Anderson
- aircraft_noise: ICAO Annex 16, IEC 61265
- wind_turbine_noise: IEC 61400-11, ISO 1996-2
- sound_power: ISO 3744, ISO 3741
- intensity: IEC 61043, ISO 9614
- distortion: IEC 60268-3, AES17
- swept_sine: Farina 2000 + Novak et al. 2015
- silencers: Munjal + Bies & Hansen
- program_loudness: ITU-R BS.1770, EBU R 128
- random_data: Rice 1945 + Bendat & Piersol
- spectra: Welch 1967 + Thomson 1982
- cepstrum: Havelock et al. + Bendat & Piersol
- correlation: Knapp & Carter + Bendat & Piersol
- inversion: Kirkeby & Nelson

The remaining API modules keep a single chip (their governing standard, or a
single notable reference for the theory ones), matching the earlier pass. Only
`filters/phonometry` (package metadata) stays bare. Six theory chips are
minimal canonical attributions added where the docstring names no source
(underwater sound-speed / seabed / numerical solvers, 2D FDTD, image source,
steady field).

## No chip (navigation / overview only)

- getting-started, reference/why-phonometry
- every group landing page `guides/sections/*`
- API index `reference/api`, and `reference/api/filters/phonometry`
- reference/theory landing and the six `reference/theory/*` overviews,
  reference/conformance, reference/bibliography

## Colours (theme-aware, WCAG AA)

- Standard (teal): dark bg `#0e3b35` / text `#7ee8d5`; light bg `#d3f4ec` / text `#0c5c52`.
- Theory (amber): dark bg `#3c2e0c` / text `#f4c04e`; light bg `#fbeecd` / text `#855107`.

## Extending / regenerating

Guides: edit the `...chips(S(...), T(...))` list on the entry in
`astro.config.mjs`. API: edit `_API_CHIPS` in `scripts/generate_api_docs.py`
and run `PYTHONPATH=src python3 scripts/generate_api_docs.py` (`make api-docs`)
to regenerate `api-sidebar.mjs`; the chips survive regeneration.
