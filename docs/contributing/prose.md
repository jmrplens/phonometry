← [Documentation index](../README.md)

# Prose, commits and pull requests

This page governs the words phonometry publishes and how they are written: which language each surface is in and the Spanish terms it settles on; the characters a text may hold (no em dash, no stray control character, digit grouping, the decimal point of an error message); how a text cites a page it read; the CHANGELOG; and the commit messages and pull request text that go out under the project's name. Read it before you write or translate a guide, a figure label, a catalogue string or an error message, before you add a CHANGELOG entry, and before you write a commit message or open a pull request. The decimal comma of a Spanish figure is [F28](docs-and-figures.md#f28), the typography of an errata entry is [F57 to F59](docs-and-figures.md#f57), and where a renamed name that shipped is recorded is [A14](api.md#a14).

## Language

<a id="p1"></a>
### P1. Write code, docs/ and the English site in English, the Spanish site in Spanish

**Why.** Each reader gets one language per page: the API, its docstrings and its messages, the English site and the GitHub edition `make llms` writes from it under `docs/` are English; the Spanish site and the Spanish editions of the figures are Spanish; and the two twins teach the same code. `check-i18n-parity.mjs` holds the pairing (every English page has its Spanish twin at the same path, and the other way round); the language of each sentence is review.

**Do**

```text
site/src/content/docs/buildings/rooms/reverberation-prediction.mdx      English
site/src/content/docs/es/buildings/rooms/reverberation-prediction.mdx   Spanish
docs/contributing/prose.md                                              English
```

**Don't**

```text
a Spanish sentence left in the English page, or an English paragraph on its
Spanish twin
```

**Enforced by:** `site/scripts/check-i18n-parity.mjs`, review

**Exceptions.** A quotation keeps its language, and an identifier is never translated. The API reference (`reference/api/`) is English on both sites: it is generated from the docstrings, and the Spanish site serves it with a notice that says so. The Spanish errata register, `docs/ERRATA.es.md`, is the one Spanish page under `docs/`. The Spanish text a figure or a fiche draws is held in code, in the translation tables (`scripts/figures/i18n.py`, `scripts/diagrams/i18n.py`, the `_STRINGS` of the renderers). This guide is English only.

<a id="p2"></a>
### P2. Write every Spanish string with its accents and eñes

**Why.** A translation typed without the Spanish keyboard layout reads fine to every other gate: twenty-nine labels of the building-acoustics figures shipped as "Correccion", "medicion" and "aqui", and the RD 1367/2007 example fiche printed "Maquina ruidosa activa", with every gate green. The check reads the translation tables of the figures, the diagrams and the renderers, the `language == "es"` branches of the renderers, the builders of the Spanish example fiches and the labels of every committed Spanish figure, and fails on a form that is never correct Spanish without its mark: its `NEEDS_MARK` list and every singular in -ción, -sión, -xión or -gión written without its accent. A builder of a Spanish example fiche names its language among the keywords it returns (`{"language": "es"}`), even where Spanish is the renderer's default, or the check cannot find the text it writes.

**Do**

```text
"Corrección por ruido de fondo", "medición", "aquí", "señal", "límite"
```

**Don't**

```text
"Correccion por ruido de fondo", "medicion", "aqui"
```

**Enforced by:** `scripts/check_spanish_accents.py`, `make spanish-accents`, `CI: Markdown renders the way it reads`, `tests/test_check_spanish_accents.py::test_the_published_tables_carry_every_accent`

**Exceptions.** A listed form that really is another word (the verb "limite" in "que limite la banda") goes in `ALLOWED` of the script, keyed by the Spanish value and the word, with its reason; an entry that no longer matches fails. Pairs a list cannot decide (si and sí, aun and aún, mas and más) stay with the author.

<a id="p3"></a>
### P3. Use the glossary's Spanish terms: sinusoide, diezmado, valor cuadrático medio, balance

**Why.** A word the glossary replaced reads as correct Spanish to every other gate: "seno" for the waveform shipped in about fifty places and "incertidumbre extendida" in a report fiche; "media cuadrática" and "cuadrado medio" stood for the mean square in diagrams, figures, renderers, guides and an erratum; and "presupuesto", which is money, named a budget of decibels in sixteen pages and a diagram. The rulings a script can hold are in `scripts/check_spanish_accents.py` (`GLOSSARY_TERMS`, `GLOSSARY_PHRASES` and the sense tables below), which reads them in the translation tables, the figures and the Spanish pages: the Spanish site, its strings, data, components and generated modules, and the Spanish pages under `docs/`.

**Do**

```text
"sinusoide" (the waveform), "diezmado" (decimation),
"valor cuadrático medio", "presión cuadrática media" (a mean square),
"balance de incertidumbre" (an uncertainty budget), "incertidumbre expandida"
```

**Don't**

```text
"senoide", "semiseno", "decimación", "media cuadrática" for a mean square,
"presupuesto de incertidumbre", "incertidumbre extendida"
```

**Enforced by:** `scripts/check_spanish_accents.py`, `make spanish-accents`, `CI: Markdown renders the way it reads`, `tests/test_check_spanish_accents.py`

**Exceptions.** Where the word really is the other sense (the sine of an angle, a quadratic mean, money), its context goes in `TRIGONOMETRIC`, `QUADRATIC_MEAN` or `MONEY` of the script with its reason, written on the words of the one sentence it exempts; a context that exempts nothing fails. "cuadrado medio" passes only in a sentence of an analysis of variance (`ANALYSIS_OF_VARIANCE`). An identifier such as `presupuesto_ruido` is code and is left alone. A "presupuesto" that is a premise ("los presupuestos del modelo") is reworded ("los supuestos", "las hipótesis").

<a id="p4"></a>
### P4. Settle a Spanish term on three independent sources, never on the corpus's majority

**Why.** Two rounds of translation passed every parity check and still used calques the trade does not use. A count of what earlier translations wrote looks like evidence and is not: it measures those translations, not the trade, and it gave *tira de base* where the trade writes *franja* and *hoja de datos* where it writes *ficha técnica*, both revoked. A source is read in context, not counted: "Solver" appears 52 times in Chapra, and all 52 are Excel's Solver.

**Do**

```text
three independent sources of different kinds, each read in its context:
a UNE standard, the Spanish edition of an international document,
a Spanish textbook of the field
```

**Don't**

```text
"hoja de datos", because most of our own Spanish pages already write it
```

**Enforced by:** review

<a id="p5"></a>
### P5. Translate every catalogue string you add or change, in `catalogue-es.json`

**Why.** The Spanish catalogues page is served in Spanish (decided 2026-09-24): material names, variants, groups, row and cell notes, word columns and sources. `scripts/generate_catalogue_data.py` refuses a printed string with no Spanish and an entry no longer printed, and a new column needs its `headingEs`.

**Do**

```text
site/src/data/catalogue-es.json:   "1 cm deep": "1 cm de profundidad"
python scripts/generate_catalogue_data.py --untranslated   (the missing strings, as a stub to fill)
```

**Don't**

```text
a new catalogue row note committed in English only
```

**Enforced by:** `scripts/generate_catalogue_data.py`, `make catalogue-data`, `CI: Every published value names its page`

**Exceptions.** The book's name inside a source stays as printed ("Allard & Atalla 2e", "ASHRAE (2019) HVAC Applications Handbook"); the words around it are translated, so `Allard & Atalla 2e Table 10.1, PDF page 229 (printed p. 222)` reads `Allard & Atalla 2e Tabla 10.1, página 229 del PDF (p. 222 impresa)`.

## Characters and numbers

<a id="p6"></a>
### P6. Write no em dash anywhere

**Why.** It is not how the maintainer writes: a clause that would hang off one is its own sentence, a parenthesis, a colon or a comma. The guard reads everything a reader sees under the project's name, at its source: the files of `docs/` that are not the GitHub edition (the ones written by hand, and the conformance report, whose words no other file holds), the site's pages, the generated API pages among them, and its data modules, the `robots.txt` the site serves, the CHANGELOG, the READMEs, CONTRIBUTING, the docstrings the API reference is generated from, and the text the figure and diagram generators draw; the llms files are written from those and not read again, and neither is the GitHub edition under `docs/` ([F74](docs-and-figures.md#f74)). The double hyphen is the same dash spelt in ASCII, and it is refused too: Astro's smartypants publishes `--` in the text of a page as the em dash, so a docstring bullet written ``:func:`x` -- text`` reached the API reference as one in 92 list items and nearly five hundred other docstring lines, and `help()` shows it as the double hyphen it is. A list item's head is joined to its text by a colon, so a single hyphen between spaces is refused there too (``:func:`x` - text``), the one place where it cannot be a minus, unless the item sits in code or in a comment the page does not show. The entities `&mdash;`, `&#8212;` and `&#x2014;` and the escapes `\u2014` and `\N{EM DASH}` publish the character itself, and are read as it wherever they are decoded: in a string of a module, a data module or a JSON file, in a double-quoted value of a page's frontmatter, the one YAML value that decodes an escape, and in the JSON-LD its head carries under a `content` key. Any other single-quoted or plain value, block of text and escaped backslash (`\\u2014`) show it as written, and are not read. This page writes the dash as `<U+2014>`, never the character.

**Do**

```text
The level is energy-averaged: each band is summed in power, then converted back.
* :func:`npd_level`: the interpolated event level, linear in power.
* ``peaking``: the bell of a parametric EQ.
```

**Don't**

```text
The level is energy-averaged <U+2014> each band is summed in power.
* :func:`npd_level` -- the interpolated event level, linear in power.
* ``peaking`` - the bell of a parametric EQ.
```

**Enforced by:** `scripts/check_em_dashes.py`, `CI: Markdown renders the way it reads`, review

**Exceptions.** What is not prose keeps its dash, by position, with no exemption table: a standard's title reproduced as printed (in a frontmatter `title:`, an italic span, a bibliographic entry, a quotation, or right before a part number, `<U+2014> Part 3:`, each exempting its own dash and no other on the line, a value of the frontmatter being plain text the site shows as written, so only a quotation closed inside the value, over the lines it wraps, or a part number marks a title there and nothing it opens reaches the next value or the body, and a line of a data module quoting with curly quotes or guillemets alone, a straight quote there being the string's own; an italic span or a quotation that nothing closes in its block exempts nothing, since the site shows its mark as written), fenced and inline code, a string a test compares with, and a dash that fills a whole table cell or a whole slash-separated item of one (the empty-cell mark of the fiches), in a row of a table: a pipe with no delimiter row under it is text. A double hyphen is code in the same places, and also in a docstring's literal block after `::`, the body of a `.. math::` or `.. code-block::` directive, a doctest, math on a page (`$...$` and a `$$` block), a link destination or URL (a heading's slug may carry `--`), a comment the page does not show (an HTML comment, an MDX comment `{/* ... */}` on an MDX page, a comment of the frontmatter), an `href`, `src`, `style`, `id` or `class` value (`var(--sl-color-accent)`) and a line that is only a rule. In the frontmatter, an identifier field of a reference (`number`, `doi`, `isbn`, `url`) is no prose: the References section prints it as written, outside the text smartypants reads, or not at all, so a run of hyphens with no blank on either side is the identifier's own there (the Naval Research Laboratory numbers its RANDI report `NRL/FR/7176--95-9628`), while a spaced one, one at the edge of the value and one in any other field of the entry are read as everywhere else; the GitHub edition under `docs/` writes such a number in code. An em dash in maths is still read, because the site shows what maths holds, whatever quotation, italic span, reference or part number stands around it, but maths marks nothing around it: an asterisk between dollar signs is a superscript star (`$DI_i^*$`), not an italic marker, a quotation mark there opens no quotation, and four digits in parentheses there or in code (`$L(1000)$`) open no bibliographic entry. A `$$` block is read the same way whatever its lines open with, since `+ `, `|` or `>` on a line of it starts no block of markdown, as on a line of a fenced code block. Both are read behind the marks of a quotation or a list item as anywhere else, and each ends with what holds it. Every reading goes by one walk of the page, by its kind (`page_lines` of `scripts/markdown_fences.py`): what opens a block on a `.md` page need not on an `.mdx` one. A plain-text file the site serves (`robots.txt`) is shown as written, so a double hyphen there stays two hyphens. In a string that is not a page or a docstring only the spaced form ` -- ` is a dash, so an option of a command line (`--keep`) and a console banner (`--- Generating ---`) stand; a comment is published nowhere and keeps its double hyphens, and so does the docstring of a figure or diagram generator, which publishes only what it draws. A docstring and the API page made from it read the same, because the generator publishes a code directive's body and a doctest as fenced code, under a fence longer than any run of backticks the example shows, and the math as `$` and `$$` spans. Away from a list item's head, a single hyphen between spaces is also a minus (`32,3 - 26,3 dB`), and there the rule holds by review. Outside the guard's roots (commit messages, pull requests, tests and the other scripts) the rule holds by review.

<a id="p7"></a>
### P7. Use no control character but tab and newline in a tracked text file

**Why.** A form feed pasted into a raw docstring is one invisible byte that ate the backslash and the f of `\frac`: the API reference published a formula as `10 \log_{10} rac{...}`, with the fraction gone and no error anywhere. A vertical tab or a stray escape is the same defect, and a carriage return breaks the checks that read line ends: the tree is LF throughout. A bidirectional control (U+202E and its kin) reorders what an editor or a review shows without changing what a parser reads, so a test that needs one writes its escape, `"\u202e"`.

**Do**

```text
r"""... :math:`10 \log_{10} \frac{S_1}{S_2}` ..."""
```

**Don't**

```text
r"""... :math:`10 \log_{10} <FF>rac{S_1}{S_2}` ..."""   (<FF>: one form feed byte where \f was)
```

**Enforced by:** `scripts/check_control_characters.py`, `make control-characters`, `CI: No stray control character`

**Exceptions.** A file that is a copy of someone else's (a license, an oracle extracted as delivered) may keep its carriage returns: it goes in `AS_DELIVERED` of the script, keyed by path with its reason, and an entry whose file is gone or no longer carries one fails. Binary files and SVG are not read (`NOT_TEXT`).

<a id="p8"></a>
### P8. Group a long digit string in threes with U+202F, the narrow no-break space

**Why.** ISO 80000-1 and the SI Brochure group digits in threes on both sides of the decimal marker, and the corpus writes a number the way the printed table does (6.251 5 and 101 325). With an ordinary space a line break can fall inside the number and leave 6,251 at the end of one line and 5 at the start of the next, which reads as two numbers. The check runs as a step of the CI job named "Every call passes the language on".

**Do**

```text
6.251 5   0.647 829   101 325   (each gap inside a number is U+202F)
```

**Don't**

```text
6.251 5   0.647 829   101 325   (ordinary spaces: a line may break inside the number)
```

**Enforced by:** `scripts/check_digit_grouping.py`, `make digit-grouping`, `CI: Every call passes the language on`

**Exceptions.** A figure or diagram label, because an SVG text line does not reflow; inside `$...$` mathtext the separator is `\,` instead. In a Python file only docstrings and comments are prose: another string may be a data key (the CNOSSOS traction table is keyed `"diesel locomotive, c. 2 200 kW"`, which a caller passes in). Inline code and fences are literals and are not read.

<a id="p9"></a>
### P9. Write the decimal point in English text; only a literal transcription of a print keeps the comma

**Why.** English takes a point, and a reader of an English page, docstring or message reads a comma between digits as a thousands separator or a list, not as a decimal marker. The library used to keep the comma wherever a value came from a standard that prints one, and the convention spread from the errata registry to the guides, the docstrings, the comments, the conformance descriptions, the figure labels and the catalogue cells: some thirteen thousand decimal commas in English text, beside the points the same pages wrote for values of their own, with nothing to tell a reader which was which. The maintainer settled it on 2026-11-15: every decimal number an English text writes itself takes a point, a value it restates from a print among them, and the print's own separator survives only where the text reproduces the print character for character. A Spanish figure and a Spanish page are the other way round ([F28](docs-and-figures.md#f28)), and a printed value is quoted as [F58](docs-and-figures.md#f58) says.

**Do**

```text
ISO 9613-1 prints 2.2560 x 10^-5 for a, and the library returns 0.5 dB.
Clause 7.6 lists "0,5 m between any microphone position and the wall".
msg = "'temperature_c' must be a finite temperature above -273.15 degC."
```

**Don't**

```text
ISO 9613-1 prints 2,2560 x 10^-5 for a, and the library returns 0.5 dB.
The floor is at least 0,5 m from the wall, as Clause 7.6 lists.
msg = "'temperature_c' must be a finite temperature above -273,15 degC."
```

**Enforced by:** `scripts/check_decimal_comma.py`, `make decimal-comma`, `CI: English text writes the decimal point`, `tests/test_package_architecture.py::test_no_error_message_carries_a_comma_decimal`

**Exceptions.** The rule covers every English text: prose, docstrings, comments, error and warning messages, test docstrings and comments, the CHANGELOG, the English site pages and their frontmatter, the prose attributes of a tag (`alt`, `title`, `caption`), the text of English figures, diagrams, plates and fiches, and the generated English pages (their generator writes the point, and they are mended at their source). A value never changes on the way: `1,5` becomes `1.5`, `83,523 4` becomes `83.523 4`, `$2{,}256$` becomes `$2.256$`.

Where the comma stays, because the text transcribes the print:

- between quotation marks: `the page prints "0,5 m"`, `“1,256 µT”`, `‘2,2560’`, `«0,5»`, and a value written as one, `'1,5'`;
- in a block quote that reproduces the print (`> The value shall be 0,5 dB or less.`); a block quote that opens on a label, `> **Note.**` or `> [!NOTE]`, is a note of ours and takes the point;
- in the `**The print:**` field of an entry of `docs/ERRATA.md`, every line of it, its maths and its tables included; the other fields of the entry (the problem, the evidence, the library's behaviour) are the registry's own text and take the point, "the printed 75.2527 dB" among them;
- in the printed column of the conformance report, where a cell gives the printed values as the page prints them (`39,0 / 31,0 / 23,0 / 17,0 / 12,5 dB re 1 N`, a misprinted cell as printed): the `expected` and `printed` values of `scripts/conformance/`, the `expected` record of `docs/conformance.json` and the `Expected` column of `docs/CONFORMANCE.md`. A cell of that column that is a sentence of ours, a printed value restated in it among them (`0.0437 dB (printed 0.040, an erratum)`, `PNR84 = 22.5 dB; SNR84 = 21 dB; both report 82 dB`), takes the point, and so do the row's description and its computed column. The pass and the fail branch of a row write the same cell.

Spanish keeps its comma everywhere and is never read: a Spanish file (`es/`, `*.es.md`, `catalogue-es.json`), the Spanish value of a translation table, a branch taken for `language == "es"`, a value under an `es` or `…Es` key, a catalogue row transcribed from a Spanish edition, a paragraph that reads as Spanish.

A comma between digits that is no decimal marker is never changed: a thousands group (`91,658,333`, which the grouping rule [P8](#p8) holds and which is reported, not converted), a list (`1,2,3`), a pair of indices in brackets or braces or after a letter (`a[1,2]`, `(2,1)`, `{2,4}`, `k_{1,2}`, `k2,1`), a list of clauses (`5.2,5.3`), a chemical locant (`1,2-DHCP`), a list of coordinates (`(0,90), (45,135)`), and all code: inline code and fences (a `#` comment in a fence is prose), doctests, reStructuredText literals, regular expressions, the strings of the test suite, CSV and data files, SVG path data and dash patterns, version strings and numbers in code literals. An index has one or two digits and no leading zero, so `q_{0,1}`, `R(q0,9)` and `(0,05)` are decimals. A number such as `1,500`, which a thousands group writes too, is listed for a person to decide and never changed by a sweep; `--strict` refuses it as well.

## Citing what a page prints

<a id="p10"></a>
### P10. State what a page prints and where, never how the page was read

**Why.** It is taken for granted that a person read the page; naming a resolution, a rendering or a tool suggests nobody did, the opposite of what happened. Justify a reading by its evidence (a value that comes out exact, two printed sentences that contradict each other), never by its procedure. How an errata entry cites its page is [F57](docs-and-figures.md#f57).

**Do**

```text
Verified on PDF page 31 (printed p. 25) of ISO 3744:2010.
```

**Don't**

```text
Rendered at 600 dpi with pdftoppm and confirmed by two engines.
```

**Enforced by:** `scripts/check_errata_evidence.py`, `CI: Errata entries cite their page`, review

**Exceptions.** The guard reads `docs/ERRATA.md` and `docs/ERRATA.es.md` (a resolution in dpi anywhere, and the procedural "rendered at", "rendered from" or "render the page" in an Evidence bullet); pull request bodies, review replies, the CHANGELOG, the guides and the curated API table are review. Reading the page as an image stays the method ([CONTRIBUTING.md, "Filing an errata entry"](../../CONTRIBUTING.md)); only its narration goes. "render" in its ordinary sense is allowed, and so is how the site or a figure is rendered.

## The CHANGELOG

<a id="p11"></a>
### P11. Add a CHANGELOG entry under `[Unreleased]` for every new public name and user-visible break

**Why.** A user learns from the CHANGELOG what a release adds and what it breaks: #240 and #241 merged without their entries, and #242 and #243 had to recover them (2026-07-20). Each user-visible break gets its own entry, under Added, Changed, Removed or Fixed. Releases happen only on the maintainer's word, so `[Unreleased]` accumulates until then.

**Do**

```markdown
## [Unreleased]

### Added

- **The nonlinearity parameter of solids.** `solids.PUBLISHED_SOLID_NONLINEARITY`
  holds Rossing (2014) Table 6.5, the ultrasonic β of eight solids at room
  temperature, ...
```

**Don't**

```text
a new public function merged with no line in the CHANGELOG
```

**Enforced by:** review

<a id="p12"></a>
### P12. Open a CHANGELOG entry with a bold one-line title, then what changed for the user

**Why.** A reader upgrading scans the titles; the paragraph under each says what to do differently, not how the change was made.

**Do**

```markdown
- **An axis is written by name.** `building.energy_average_level` and
  `room.directivity_energy_average` take `axis=` keyword-only, as
  `vibration.passage_average_level` does, so a bare integer after the levels
  is refused instead of read as the axis. The default is unchanged.
```

**Don't**

```markdown
- misc renames
```

**Enforced by:** review

<a id="p13"></a>
### P13. Rename an unreleased name in its CHANGELOG entries; never add a rename line

**Why.** A name no release has shipped has no caller to migrate, and a rename line would describe a change nobody saw. So the entry that introduced the name is edited to the final one, and `[Unreleased]` reads as if the name had always been spelled that way.

**Do**

```text
The entry that added the ISO 11546 functions, edited where it stands:
- **ISO 11546-1:1995 and ISO 11546-2:1995**, ... `enclosure_sound_power_insulation`,
  `enclosure_sound_pressure_insulation`, ...
```

**Don't**

```text
- `sound_power_insulation` is renamed `enclosure_sound_power_insulation`.
```

**Enforced by:** review

**Exceptions.** A name that shipped in a release (3.3.0 or 4.0.0rc1) is recorded in the migration guide instead ([A14](api.md#a14)).

## Commits and pull requests

<a id="p14"></a>
### P14. Write a commit subject as what the user gets from the change

**Why.** The history is read by users deciding whether to upgrade: a subject that says what changed for them reads on its own, and a type prefix or a list of files does not.

**Do**

```text
phonometry installs on Python 3.12 and on the numpy, scipy and matplotlib it really needs
```

**Don't**

```text
chore: bump deps and fix tests
```

**Enforced by:** review

<a id="p15"></a>
### P15. Write commits and pull requests in your own voice, never about the maintainer in the third person

**Why.** Every published text reads as the author's own, and a third-person aside reads as somebody else's account: #171 said "(papers provided by the maintainer)" (2026-07-14). Name the material, not who supplied it ("from the original papers", "the newly obtained sources"), and credit no assistant: no co-author trailer, no generated-by line.

**Do**

```text
The newly obtained sources settle the two coefficients.
```

**Don't**

```text
The maintainer provided the papers that settle the two coefficients.
```

**Enforced by:** review

**Exceptions.** Describing a feature that concerns the maintainer ("the maintainer contact address") is not a third-person account of who did the work.

<a id="p16"></a>
### P16. Name no plan, phase, wave or task in a commit or pull request

**Why.** The plan is local organization of the work and does not belong to the public repository: #164 went in as "... (phase 2, wave E)", which tells a reader nothing about the change (2026-07-14). The same holds for a layer, a batch, an overhaul or a task number. Say what the change carries and what it is checked against.

**Do**

```text
Doc 29 levels behind the runway use the nearest-end ground-roll geometry, and the landing rollout is modeled
```

**Don't**

```text
Doc 29 ground-roll geometry, landing rollout and Annex 16 bandsharing (phase 2, wave E)
```

**Enforced by:** review

<a id="p17"></a>
### P17. Write each paragraph of a pull request body on one line

**Why.** GitHub renders pull request, issue and comment bodies with `breaks: true`, so every single line break inside a paragraph becomes a visible `<br>`: a body wrapped at 76 columns shows cut mid-sentence.

**Do**

```text
The filter bank returns a result record, so the two outputs have names and the call reads the same whatever the keyword.
```

**Don't**

```text
The filter bank returns a result record, so the two outputs have names
and the call reads the same whatever the keyword.
```

**Enforced by:** review

**Exceptions.** Code blocks, headings, list items, table rows and quotations keep their own lines. When rewriting a published body, cut before the first `<!--` and leave the generated part below it untouched. Commit messages stay wrapped.

<a id="p18"></a>
### P18. End a pull request that adds a guard with its red and green output

**Why.** The output on the base is the evidence that the guard catches the class, and the green run is the evidence that the change closes it ([T14](tests.md#t14)).

**Do**

```text
On the base, with the guard copied in, it fails:
    src/phonometry/<package>/<module>.py:<line>: <what it refuses>
On this branch it passes.
```

**Don't**

```text
Added a guard. All tests pass.
```

**Enforced by:** review
