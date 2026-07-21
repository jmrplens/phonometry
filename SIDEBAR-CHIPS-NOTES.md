# Sidebar reference chips: trial mapping

Experimental branch `exp/sidebar-standard-chips`. Each chipped sidebar item
carries a Starlight badge via its `badge: { text, class }` slot in
`astro.config.mjs`. Two custom classes, both defined in
`src/styles/sidebar-chips.css` and wired through `customCss`:

- `chip-standard` (colour A, teal): the page implements published standards;
  the chip shows the standard number(s), kept short.
- `chip-theory` (colour B, amber): the page is theoretical/experimental with
  no governing standard; the chip shows the single most notable reference.

Text is language-neutral, so EN and ES share the same chip (the config array
is not localised per item, so both locales get it automatically).

## Standard-backed items (teal)

| Sidebar item | Chip | Attribution source |
|---|---|---|
| Build a sound level meter | `IEC 61672` | `guides/sound-level-meter` frontmatter: IEC 61672-1:2013 |
| Filter Banks | `IEC 61260` | `guides/filter-banks` frontmatter: IEC 61260-1:2014 |
| Frequency Weighting | `IEC 61672` | `guides/weighting` frontmatter: IEC 61672-1:2013 (A/C/Z) |
| Loudness | `ISO 532-1` | `guides/loudness` frontmatter/title: ISO 532-1 (Zwicker) |
| Occupational Noise Exposure | `ISO 9612` | `guides/occupational-exposure` frontmatter: ISO 9612:2009 |
| Room Acoustics | `ISO 3382` | `guides/room-acoustics` frontmatter: ISO 3382-1/2/3 |
| Sound absorption in enclosed spaces | `EN 12354-6` | `guides/enclosed-space-absorption` title/frontmatter: EN 12354-6 |
| Acoustic Materials | `ISO 11654` | `guides/materials` frontmatter: ISO 11654 weighted absorption |
| Field Insulation | `ISO 16283 / 717` | `guides/insulation-field` frontmatter: ISO 16283-1/2/3 + ISO 717-1/2 |
| Laboratory Insulation | `ISO 10140` | `guides/insulation-lab` frontmatter: ISO 10140-2 |
| Human Vibration | `ISO 2631 / 5349` | `guides/human-vibration` frontmatter: ISO 2631-1 (whole-body) + ISO 5349 (hand-arm) |
| Programme loudness and true peak | `EBU R 128` | `guides/program-loudness` frontmatter: EBU R 128 (with ITU-R BS.1770-5) |

Standard numbers are truncated to the family (no year/part suffix) for
compactness; combined chips (`ISO 16283 / 717`, `ISO 2631 / 5349`) are used
where two families jointly govern the page and both read fine on mobile.

## Theory / experimental items (amber)

All in the "Signals and spectra" group. Each chip is the single most notable
reference from the page's own frontmatter bibliography.

| Sidebar item | Chip | Attribution source |
|---|---|---|
| Calibrated spectral analysis | `Welch 1967` | `guides/spectral-analysis` frontmatter: Welch (1967) overlapped-segment PSD |
| Multiple and partial coherence | `Bendat & Piersol` | `guides/miso-coherence` frontmatter: Bendat & Piersol, Random Data, ch. 7 |
| Time-frequency analysis | `Bendat & Piersol` | `guides/time-frequency` frontmatter: Bendat & Piersol, §12.6 spectrograms |
| Cepstrum, echoes and the envelope spectrum | `Havelock et al.` | `guides/cepstrum-echoes` frontmatter: Havelock, Kuwano & Vorlander (eds.), Handbook of Signal Processing in Acoustics |
| Time synchronous averaging | `McFadden 1987` | `guides/synchronous-averaging` frontmatter: McFadden, revised TSA model |
| Correlation, time delay and envelope | `Knapp & Carter` | `guides/correlation-delay` frontmatter: Knapp & Carter, generalized correlation (GCC) |

## Colours (theme-aware)

Defined as CSS custom properties, dark values on `:root` (the default the
maintainer browses in) and light values on `:root[data-theme='light']`.

- Standard (teal): dark bg `#0e3b35` / text `#7ee8d5`; light bg `#d3f4ec` / text `#0c5c52`.
- Theory (amber): dark bg `#3c2e0c` / text `#f4c04e`; light bg `#fbeecd` / text `#855107`.

Both text-on-fill pairs clear WCAG AA.

## Starlight note

The badge config accepts `{ text, class }`; the local `SidebarSublist.astro`
already forwards `badge.class` to the `Badge` component, which renders
`<span class="sl-badge default small chip-...">`. Starlight's preset badge
colours live in `@layer starlight.core`, so the chip rules are kept
**unlayered** to win without a specificity fight (no `!important` needed).

## Extending to all pages later

Mechanical: turn any `'guides/x'` string entry into
`{ slug: 'guides/x', badge: { text: '<ref>', class: 'chip-standard' | 'chip-theory' } }`.
The standard number for each page is already in that page's frontmatter
`references` block (`type: standard` -> `designation`), so a generator could
read it straight from source instead of hand-listing.
