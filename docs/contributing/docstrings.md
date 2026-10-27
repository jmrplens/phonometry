← [Documentation index](../README.md)

# Docstrings and comments

This page governs how phonometry documents itself in its source: the module docstring and the document it names, the fields of a function or class docstring that the API reference is generated from, the mathematics those docstrings carry, the comments in the code, and how long a module may grow. Read it before you write or change a docstring or a comment, and before you split a module. D rules cover docstrings and modules, C rules cover comments.

## Module docstrings

<a id="d1"></a>
### D1. Name in a module docstring the document it implements, with its edition

**Why.** A reader checks a module against the document it implements, and a new edition changes the numbers. The docstring is where the designation lives, which is why the module name does not have to carry it ([N1](naming.md#n1)).

**Do**

```python
"""Spatial sound distribution curves in workrooms (ISO 14257:2001).

How the level falls with distance from a source in a workroom, and the two
quantities the standard derives from that curve.
"""
```

**Don't**

```py
"""Spatial decay helpers."""
```

**Enforced by:** review

**Exceptions.** A module that implements a book or a paper names it with its edition or year (Bies 5e, Allard & Atalla 2e). A draft is cited as [D2](#d2) says. A module whose standard prints no worked example says so, and says what its tests anchor on instead ([T4](tests.md#t4)).

<a id="d2"></a>
### D2. Cite a draft standard by its full dated designation, and say it is a draft

**Why.** Where no published edition covers a part, the draft is the source: Part 3 of DIN 45672 has never been published, so E DIN 45672-3:2023-02 is the only text of it. A reader must see from the citation that the text is a draft, and of which date.

**Do**

```python
"""Predicting railway vibration from third-octave spectra (E DIN 45672-3:2023-02).

Part 3 of DIN 45672 has never been published; the draft of February 2023 is
the only text of it.
"""
```

**Don't**

```py
"""Predicting railway vibration from third-octave spectra (DIN 45672-3)."""
```

**Enforced by:** review

**Exceptions.** The full designation goes in docstrings, conformance rows, references and the CHANGELOG, and the documentation guide says that the text is a draft and, where there is one, which published edition it revises. A figure title or label may shorten it (`ISO/DIS 16032` in the titles of `src/phonometry/_plot/building.py`).

<a id="d3"></a>
### D3. Say in the docstring which reading is the library's where the standard prints none

**Why.** Where a clause leaves a choice open, the code still has to make it. Marked as the library's reading, the choice can be told apart from what the clause prints, and a reviewer checks the clause instead of arguing with the code. The documentation guide that explains the choice says so too.

**Do**

```python
"""...By the NOTE of A.3.2, the sound power level is the mean of two
determinations. The NOTE says "mean value" and does not say which mean; the
library takes the arithmetic mean of the determinations.
"""
```

**Don't**

```py
"""...By the NOTE of A.3.2, the sound power level is the mean of two
determinations."""  # and the code takes the arithmetic mean without saying so
```

**Enforced by:** review

## Function and class docstrings

<a id="d4"></a>
### D4. Write docstring fields as a Sphinx field list: `:param`, `:return`, `:raises`, `:warns`, `:ivar`

**Why.** `scripts/generate_api_docs.py` builds the API reference from these fields, and the tree writes them everywhere, with no numpydoc section; a second shape would need a second parser.

**Do**

```python
def spherical_spreading_loss(distance_m: float) -> float:
    """Spherical spreading loss re 1 m.

    :param distance_m: Distance from the source, in m.
    :return: The loss, in dB.
    :raises ValueError: if ``distance_m`` is not positive.
    """
```

**Don't**

```py
def spherical_spreading_loss(distance_m):
    """Spherical spreading loss re 1 m.

    Parameters
    ----------
    distance_m : float
        Distance from the source, in m.
    """
```

**Enforced by:** review

**Exceptions.** Types come from the annotations, so `:type` and `:rtype` are not written, and `:return:` is the one spelling (never `:returns:`). A class documents its fields with `:ivar`.

<a id="d5"></a>
### D5. Document only the parameters the signature has

**Why.** Converting the visco-thermal models to take a `Fluid` left twenty-five `:param` entries for arguments that were gone: `johnson_champoux_allard` alone still documented six floats it no longer accepted, and a reader following its docstring got a `TypeError`.

**Do**

```python
from numpy.typing import ArrayLike

from phonometry import fluids


def effective_density(
    frequencies: ArrayLike, *, fluid: fluids.Fluid
) -> list[complex]:
    """Effective density of a rigid-frame porous layer, in kg/m3.

    :param frequencies: Band centers, in Hz.
    :param fluid: The fluid in the pores.
    """
```

**Don't**

```py
def effective_density(frequencies, *, fluid):
    """Effective density of a rigid-frame porous layer, in kg/m3.

    :param frequencies: Band centers, in Hz.
    :param air_density: Density of the air, in kg/m3.
    """
```

**Enforced by:** `tests/test_package_architecture.py::test_no_docstring_documents_a_parameter_that_is_gone`

**Exceptions.** The docstring of a `*args` function may name the collection (`:param fields:` for `*field`).

<a id="d6"></a>
### D6. Keep a docstring's field list unbroken: no prose between two fields

**Why.** Sphinx ends the list at the first line that is neither a field nor its indented continuation, so the parameters after the break vanish from the generated table and the prose is printed after **Returns**. `unlined_rectangular_duct_attenuation` lost `:param wrapped:` that way.

**Do**

```python
def duct_attenuation(frequencies: ArrayLike, *, wrapped: bool = False) -> list[float]:
    """Attenuation of an unlined rectangular duct, in dB.

    :param frequencies: Octave-band centers, in Hz.
    :param wrapped: The duct is externally wrapped with a fiberglass blanket,
        which doubles the attenuation from 63 Hz to 250 Hz.
    """
```

**Don't**

```py
def duct_attenuation(frequencies, *, wrapped=False):
    """Attenuation of an unlined rectangular duct, in dB.

    :param frequencies: Octave-band centers, in Hz.

    A wrapped duct doubles the attenuation from 63 Hz to 250 Hz.
    :param wrapped: Whether the duct is externally wrapped.
    """
```

**Enforced by:** `tests/test_package_architecture.py::test_no_docstring_breaks_its_own_field_list`

<a id="d7"></a>
### D7. State the unit of every numeric parameter, field and return, as the source prints it

**Why.** A unit the name does not carry is read from the docstring, and the reference page is generated from it. ICAO Annex 16 prints PNLT, PNLTM and the bandsharing adjustment in TPNdB, and the records said dB until they were read against the print.

**Do**

```python
def mean_free_path(volume: float, surface_area: float) -> float:
    """Mean free path of a diffuse field, 4V/S.

    :param volume: Room volume ``V``, in m3.
    :param surface_area: Total surface area ``S``, in m2.
    :return: The mean free path, in m.
    """
```

**Don't**

```py
def mean_free_path(volume, surface_area):
    """Mean free path of a diffuse field, 4V/S.

    :param volume: Room volume.
    :param surface_area: Total surface area.
    :return: The mean free path.
    """
```

**Enforced by:** review

**Exceptions.** A unit the name carries is not repeated by force, and a dimensionless quantity says so (a ratio, a fraction, a coefficient). A field that holds a quantity in decibels by definition (a level) may say dB once in the class docstring.

<a id="d8"></a>
### D8. Open a docstring with a noun phrase, on the line of its opening quotes

**Why.** The API reference shows the summary as the description of the name, and the house style opens with what the function returns, not with "Return the..." (ruff's D401 is off on purpose).

**Do**

```python
def band_levels(x: ArrayLike, fs: float) -> list[float]:
    """Band levels of ``x``, in dB, one per octave.

    :param x: The time signal, in Pa.
    :param fs: Sample rate, in Hz.
    """
```

**Don't**

```py
def band_levels(x, fs):
    """
    Return the band levels.
    """
```

**Enforced by:** `ruff D212`, review

**Exceptions.** An action opens with its verb, as its name does ([N7](naming.md#n7)): `plot` draws, `report` renders, `__post_init__` rejects, `__bool__` refuses. A judgment may open as a question, with its own family's verb, or with a verb of no judgment family other than `Return`, `Get`, `Calculate` or `Compute` ([D9](#d9)). A summary may run onto the next line as one sentence (ruff's D205 is off on purpose).

<a id="d9"></a>
### D9. Never open a judgment's summary with another judgment family's verb

**Why.** `verify_` judges an instrument against the requirements a standard sets for it, `assess_` a measured situation against limits or categories, and `check_` the arrangement a method needs ([N9](naming.md#n9)). `check_base_plate_scattering` began "Verify" and six of the ten `verify_` functions began "Check", which tells a reader the prefix was picked at random.

**Do**

```python
from numpy.typing import ArrayLike

from phonometry import noise_control


def check_band_flatness(
    third_octave_levels: ArrayLike, *, frequencies: ArrayLike
) -> noise_control.BandFlatnessCheck:
    """Is the driving spectrum flat enough inside each octave? 6.4 and 7.2.1."""
```

**Don't**

```py
def check_band_flatness(third_octave_levels, *, frequencies):
    """Verify that the driving spectrum is flat enough inside each octave."""
```

**Enforced by:** `tests/test_package_architecture.py::test_a_judgement_summary_does_not_open_with_another_family_verb`

**Exceptions.** A summary may open as a question, with its own family's verb, or with a verb of no judgment family; [D8](#d8) still refuses `Return`, `Get`, `Calculate` and `Compute`.

<a id="d10"></a>
### D10. Give a magic method a docstring

**Why.** A `__bool__` that raises or a `__getitem__` that keys by period changes what the object does, so it explains itself like any other method.

**Do**

```python
class RoomCheck:
    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = "a RoomCheck has no truth value; read its '.passes'"
        raise TypeError(msg)
```

**Don't**

```py
class RoomCheck:
    def __bool__(self) -> bool:
        msg = "a RoomCheck has no truth value; read its '.passes'"
        raise TypeError(msg)
```

**Enforced by:** `ruff D105`

**Exceptions.** D105 does not reach `__init__`, which is ruff's D107 and is not selected.

<a id="d11"></a>
### D11. Document every `TypeError` a function raises, naming each parameter it refuses

**Why.** `building.weighted_rating` refused a band set written as `"third"` with a class its reference page never named, and over a thousand functions and methods raised a shared check's `TypeError` without saying so. The API reference is generated from the `:raises` fields, so a refusal missing there is missing from the page.

**Do**

```python
def band_energy_mean(levels: ArrayLike, *, fraction: int = 3) -> float:
    """Energy mean of band levels, in dB.

    :param levels: Band levels, in dB.
    :param fraction: Bands per octave, 1 or 3.
    :raises TypeError: if ``levels`` is not a sequence of numbers, or
        ``fraction`` is not an integer.
    :raises ValueError: for a ``fraction`` other than 1 and 3.
    """
```

**Don't**

```py
def band_energy_mean(levels, *, fraction=3):
    """Energy mean of band levels, in dB.

    :raises ValueError: if ``fraction`` is not an integer.
    """
```

**Enforced by:** `tests/test_error_kinds.py::test_a_public_function_that_raises_type_error_documents_it`, `tests/test_error_kinds.py::test_a_type_error_a_shared_validator_raises_is_documented_too`, `tests/test_error_kinds.py::test_a_type_error_field_names_every_parameter_it_hands_on`, `tests/test_error_kinds.py::test_a_plot_is_followed_into_the_renderer_that_refuses_its_keywords`, `tests/test_error_kinds.py::test_the_keywords_are_followed_however_they_are_handed_on`, `tests/test_error_kinds.py::test_a_choice_handed_on_names_the_type_error_of_where_it_goes`, `tests/test_error_kinds.py::test_a_choice_is_followed_however_it_is_handed_on`

**Exceptions.** The rule covers a public function, a public method (`__init__`, `__post_init__`, `__getitem__` and `__call__` included), a constructor whose class docstring carries the field, and every parameter handed as given to a shared check that raises `TypeError` (`require_band_fraction`, `require_scalar`). A value read off a record before it reaches the check is not the caller's argument. A function that hands its `**kwargs` to a renderer of `phonometry._plot` (a `.plot`, `FDTD2D.plot_geometry`) documents every keyword the renderer refuses because it sets that one itself (`color_limit` with a snapshot, `yerr` on a margin bar), followed through the renderer's own helpers, a copy of the keywords (`dict(kwargs)`, `{**kwargs, ...}`) and a renderer called through the module it is imported with. It documents too every named parameter it hands on as given to a renderer that refuses it with `TypeError` (`frequency_index` of a piston's `plot_geometry`), unless it refuses every wrong value of that parameter first itself (`check_language`). A choice, a parameter typed with a `Literal`, handed as given to another public function, class or method of the package, to a helper of the module or imported from another, to a private method of its own class or to a method of an object the class holds, carries the `TypeError` that the callee documents for it, and the caller names it too (`fluids.sea_water(sound_speed_model=5)` raises the `TypeError` of `fluids.sea_water_sound_speed`). Which refusal is a `TypeError` and which a `ValueError` is [A42](api.md#a42).

<a id="d12"></a>
### D12. List a warning under `:warns`, never under `:raises`

**Why.** `:raises UserWarning:` put `HumanVibrationWarning` in the exceptions table of the API reference, under its base class, where a reader looking for what to filter found a class that filters every advisory. A warning is emitted, not raised, and `:warns` gives it a table of its own, by name.

**Do**

```python
def room_criterion_rating(levels: ArrayLike) -> str:
    """Room criterion rating of an octave-band spectrum.

    :param levels: Octave-band sound pressure levels, in dB.
    :warns NoiseCriterionWarning: if a band from 31.5 Hz to 4000 Hz is absent.
    """
```

**Don't**

```py
def room_criterion_rating(levels):
    """Room criterion rating of an octave-band spectrum.

    :raises NoiseCriterionWarning: if a band from 31.5 Hz to 4000 Hz is absent.
    """
```

**Enforced by:** `tests/test_package_architecture.py::test_a_docstring_lists_a_warning_under_warns`

<a id="d13"></a>
### D13. Cite a standard by clause, table or formula; a book also by PDF page and folio

**Why.** A citation is how the next reader opens the page a value came from. A standard numbers its own clauses, tables and formulae, and those numbers hold in every national edition that repaginates it, so the number is the citation. A book numbers nothing a reader can find without the page, and its PDF page and printed folio differ, so it takes both.

**Do**

```python
"""Reference floor curves of ISO 717-2:2020 Table 4, and the plateau data of
Norton & Karczub (2003) Table 3.1, PDF page 261 (printed p. 241).
"""
```

**Don't**

```py
"""Reference floor curves of ISO 717-2, and plateau data from Norton & Karczub."""
```

**Enforced by:** review

**Exceptions.** A standard may give its page as well where a value is read off a printed table (ISO 717-2:2020 Table 4, PDF page 13, printed folio 7). A table transcribed from a book carries its page in the comment above it ([C2](#c2)), and an errata entry cites the page of any document ([F57](docs-and-figures.md#f57)).

## Mathematics and subscripts

D14 and D15 keep a formula rendering; D16 to D21 set its letters, in docstrings, documentation pages and figures alike. The TeX below is what goes inside a `:math:` role or a pair of dollar signs.

<a id="d14"></a>
### D14. Write docstring mathematics with one backslash per command, in a raw docstring

**Why.** `scripts/generate_api_docs.py` copies a docstring's mathematics to the site verbatim. In a raw docstring a doubled backslash stays doubled, and KaTeX reads `\\mathrm` as a line break followed by the word mathrm, which it refuses: the page ships with an error in place of the formula, and the block after it may be swallowed. A plain docstring would need every backslash doubled, which is why ruff asks for the raw prefix.

**Do**

```python
def pressure_level(pressure_pa: float) -> float:
    r"""The level :math:`L_p = 20 \lg(p/p_0)`, in dB."""
```

**Don't**

```py
def pressure_level(pressure_pa):
    r"""The level :math:`L_p = 20 \\lg(p/p_0)`, in dB."""
```

**Enforced by:** `scripts/check_docstring_math.py`, `make docstring-math`, `CI: Docstring mathematics reaches the page intact`, `ruff D301`

**Exceptions.** A `\\` that ends a row of an `aligned` or `cases` block is followed by a newline, never a letter, and is not refused.

<a id="d15"></a>
### D15. Brace a TeX command used as a subscript or superscript

**Why.** KaTeX takes a single symbol or a font command bare as a script, but refuses a command that wants an argument of its own: `|dL_n|_\max` in the ISO 17534-1 pages rendered as an error in place of the formula. Braces render the same glyphs for every command.

**Do**

```python
def largest_deviation(deviations: ArrayLike) -> float:
    r"""The largest deviation :math:`|dL_n|_{\max}`, in dB."""
```

**Don't**

```py
def largest_deviation(deviations):
    r"""The largest deviation :math:`|dL_n|_\max`, in dB."""
```

**Enforced by:** `scripts/check_docstring_math.py`, `make docstring-math`, `CI: Docstring mathematics reaches the page intact`

**Exceptions.** The commands KaTeX takes bare (`BARE_SCRIPT_COMMANDS` in the checker: the Greek letters, `\circ`, `\mathrm` and the other font and text commands) may stay unbraced. The checker reads docstrings (`:math:` roles and `.. math::` blocks) and the prose of hand-written pages; the generated API reference is judged through its docstrings.

<a id="d16"></a>
### D16. Set a subscript upright for an abbreviated word, italic for a quantity or an index

**Why.** ISO 80000-2 makes the slope a claim about what the subscript is: the p of `L_p` is the pressure, a quantity, so italic; the w of `R_\mathrm{w}` abbreviates "weighted", so upright; a number is upright, and a running index is a variable, so italic. Setting a letter upright asserts that it abbreviates a word, so leave it italic unless the standard or this corpus expands it: an omission costs less than a wrong claim.

**Do**

```text
L_p    L_W    R_\mathrm{w}    \sum_i 10^{L_i/10}
```

**Don't**

```text
L_\mathrm{p}    R_w    \sum_\mathrm{i} 10^{L_\mathrm{i}/10}
```

**Enforced by:** `scripts/check_subscript_slope.py`, `make subscripts`, `CI: One meaning per subscript per file`, review

**Exceptions.** A Greek letter follows its case: lowercase italic, uppercase upright. The identifier of a symbol is never translated (the prose, operators and units around it are). The errata registers reproduce each print as it is. The checker holds a subscript to one slope per file; whether that slope is right for its standard is review. A plate sets its slopes through the composer ([F39](docs-and-figures.md#f39)).

<a id="d17"></a>
### D17. Follow the print letter by letter where a standard sets both slopes in one symbol

**Why.** A standard that sets some letters of a subscript italic and others upright has drawn the line itself: ISO 7235 prints the italic p and the upright I of `L_{p\mathrm{I}}`, and ISO 16283-1 the upright n and the italic T of `D_{\mathrm{n}T}`.

**Do**

```text
L_{p\mathrm{I}}  (ISO 7235)    D_{\mathrm{n}T}  (ISO 16283-1)
```

**Don't**

```text
L_{\mathrm{pI}}    D_{nT}
```

**Enforced by:** review

<a id="d18"></a>
### D18. Where a source prints every subscript in one slope, let ISO 80000-2 decide each letter

**Why.** UNE-EN 15657:2018 sets the index of `L_{\mathrm{v},i}` as upright as the v beside it, and EN 12354-5, IEC 60534-8-3, CNOSSOS-EU, RD 1367/2007 and NT ACOU 112 print their subscripts the same way. Such a print cannot tell an index from an abbreviation, so ISO 80000-2 decides, in every file and every image, the drawing modules included: a running index is a variable and italic, an abbreviation stays upright. ECAC Doc 29 prints the other way, every subscript italic, and there the start of roll is an abbreviation and upright (`d_\mathrm{SOR}`, `\Delta_\mathrm{SOR}`).

**Do**

```text
L_{\mathrm{v},i}    L_\mathrm{Fb,eq}    L_{\mathrm{Keq},Ti}    \Delta_\mathrm{SOR}
```

**Don't**

```text
L_\mathrm{v,i}    (UNE-EN 15657:2018 Formula (12) as printed)
\Delta_{SOR}     (ECAC Doc 29 as printed)
```

**Enforced by:** `scripts/check_subscript_slope.py`, `make subscripts`, `CI: One meaning per subscript per file`, review

**Exceptions.** An upright i that opens a subscript is not an index: it is the impact level `L_\mathrm{i}` of ISO 16283-2, which [D19](#d19) keeps apart from an index. The errata registers quote such prints as printed, index upright.

<a id="d19"></a>
### D19. Give each subscript one slope in a file and in the images it embeds

**Why.** Some glyphs honestly mean two things across standards (`D_z` is the screening of ISO 9613-2 and the acceleration dose of ISO 2631-5), so the unit of decision is the file: every module and guide opens with the standard it implements, and within it a subscript has one meaning. When an index collides with a quantity in one file, re-letter the index: the index is the library's, and the quantity's letter belongs to the standard that defines it.

**Do**

```python
def impact_level(position_levels: ArrayLike) -> float:
    r"""The impact level :math:`L_\mathrm{i} = 10 \lg(\frac{1}{n} \sum_j 10^{L_j/10})`, in dB."""
```

**Don't**

```py
def impact_level(position_levels):
    r"""The impact level :math:`L_\mathrm{i} = 10 \lg(\frac{1}{n} \sum_i 10^{L_i/10})`, in dB."""
```

**Enforced by:** `scripts/check_subscript_slope.py`, `make subscripts`, `CI: One meaning per subscript per file`, `tests/test_check_subscript_slope.py::test_the_tree_it_ships_with_passes`

**Exceptions.** Check what the source prints before renaming anything. A letter that keeps one meaning under several bases takes one slope across its family (`LINKED` in the checker: the r of "Beurteilung" in DIN 4150-2). A page whose subject is the collision itself is registered in `DECLARED` with both meanings named, and a symbol two standards print alike for two meanings goes in the ambiguity table of the glossary. `docs/ERRATA.md` and the drawing modules (`_plot`, `_report`, `scripts/`) are held only to the running index and the corpus-wide bases.

<a id="d20"></a>
### D20. Set KB, the weighted vibration severity, italic in every file and image

**Why.** The sources disagree: DIN 4150-2, its 2023 draft, DIN 45672-2 and E DIN 45672-3 print KB italic, and the list of symbols of DIN 45669-1 sets it upright. That is a choice between sources, not a meaning a file can state, so the corpus follows DIN 4150-2 in every file and image.

**Do**

```text
KB_\mathrm{Fmax}    KB_\mathrm{FTr}
```

**Don't**

```text
\mathrm{KB}_\mathrm{Fmax}
```

**Enforced by:** `scripts/check_subscript_slope.py`, `make subscripts`, `CI: One meaning per subscript per file`

**Exceptions.** `BASES` in the checker lists the letter runs held corpus-wide. A run inside a subscript is a word and stays upright (the KB filter of `H_\mathrm{KB}`). On a plate the composer sets a run of two or more letters upright, except the runs of `_ITALIC_BASE_RUNS` in `scripts/diagrams/canvas.py`.

<a id="d21"></a>
### D21. Set Euler's number upright: `\mathrm{e}`

**Why.** ISO 80000-2:2019, Clause 4 (PDF page 7, printed folio 1) and Table 9 (items 2-13.1 and 2-13.5), prints the constant e upright; an italic e is a variable, an eccentricity or an error. KaTeX and mathtext set a bare letter italic, and the corpus had both spellings, often a few lines apart.

**Do**

```text
p(t) = \hat{p}\,\mathrm{e}^{-t/\tau}    \ln x = \log_\mathrm{e} x
```

**Don't**

```text
p(t) = \hat{p}\,e^{-t/\tau}    \log_e x
```

**Enforced by:** `scripts/check_euler_number.py`, `make euler-number`, `CI: Euler's number is upright`

**Exceptions.** A plate label writes `exp(...)`, since the plate canvas sets every lone letter italic. An italic e stays where it is a variable (the strain of a Biot frame), declared in `DECLARED` of the checker. A subscript e takes the slope of what it names.

## Comments

<a id="c1"></a>
### C1. Write a comment for the why or the citation, never to restate the code

**Why.** The code already says what it does, and a comment that repeats it goes stale with the next edit. The reason for a choice and the page a number comes from are what the next reader cannot recover from the code.

**Do**

```python
import numpy as np

measured = np.array([41.5, 44.2, 47.5])
# ASTM E413 clause 5.2 rounds to the nearest integer and leaves a half open;
# floor(x + 0.5) rounds it up, where np.round would round it to even.
rounded = np.floor(measured + 0.5)
```

**Don't**

```py
# add 0.5 and take the floor
rounded = np.floor(measured + 0.5)
```

**Enforced by:** review

<a id="c2"></a>
### C2. Above a table transcribed from a book or a paper, cite its PDF page and folio

**Why.** The comment above a table is what lets the next reader open the same page and check the numbers. The first census of tables transcribed from books missed eight Long tables and two Cremer constants, because its list of surnames could not match a single-author book; the registry of the guard makes the rule hold for every such table, not only the ones a census finds.

**Do**

```python
#: Band-width factors ``B`` of Hopkins (2007) Eq. (3.91), PDF page 305
#: (printed p. 278): ``B = 0,23 f`` for one-third-octave bands and
#: ``B = 0,707 f`` for octave bands.
_BANDWIDTH_FACTOR: dict[int, float] = {3: 0.23, 1: 0.707}
```

**Don't**

```py
# Hopkins Eq. (3.91)
_BANDWIDTH_FACTOR: dict[int, float] = {3: 0.23, 1: 0.707}
```

**Enforced by:** `scripts/check_published_sources.py`, `make published-sources`, `CI: Every published value names its page`

**Exceptions.** A table transcribed from a standard is cited by the standard's table or clause number, which is the citation ([D13](#d13)); its page is optional. A table transcribed from a book or a paper is registered in `SOURCED` of the guard, keyed by module path and constant name, with the citation first. A comment that names a document only for its formula, while the values are arithmetic, is declared in `NOT_TRANSCRIBED` with the reason, and a table whose page cannot be established goes in `PAGE_UNKNOWN` with the reason; that list is meant to stay empty, and an entry in either that stops matching the tree fails the guard. Any comment block counts as the banner, and a data file the banner names must say its own page.

<a id="c3"></a>
### C3. Never commit commented-out code

**Why.** Code in a comment is not run, typed or tested, and it reads as a decision nobody made; the history keeps what was removed.

**Do**

```python
levels = [60.0, 52.0, 45.0]
loudest = max(levels)
```

**Don't**

```py
levels = [60.0, 52.0, 45.0]
# loudest = sorted(levels)[-1]
loudest = max(levels)
```

**Enforced by:** review

**Exceptions.** A formula written in a comment as the source prints it is a citation, not code.

<a id="c4"></a>
### C4. Give every suppression its reason, on the line above a `noqa` and after a `nosec`'s codes

**Why.** Ruff reads the codes of a `noqa` until it meets something that is not one. Prose after them is undefined ground: the static analyzer reports it as a malformed suppression, and a directive that silently stops applying is worse than the lint it hid. Thirteen had collected in three shapes, a dash, a double dash and a second hash.

**Do**

```python
import numpy as np

levels = np.zeros((2, 3))
# Bands by positions: a matrix, never a vector or a stack of them.
if levels.ndim != 2:  # noqa: PLR2004
    msg = "'levels' must be two-dimensional"
    raise ValueError(msg)
```

**Don't**

```py
if levels.ndim != 2:  # noqa: PLR2004 - bands by positions
    msg = "'levels' must be two-dimensional"
    raise ValueError(msg)
```

**Enforced by:** `tests/test_package_architecture.py::test_no_suppression_comment_hides_its_reason_from_the_parser`, review

**Exceptions.** Bandit reads its own codes, and a `nosec` carries its reason after them on the same line (`# nosec B105 - verdict label, not a password`). The test reads `src`, `scripts` and `tests` and refuses prose after a `noqa`'s codes; whether a reason is there at all is review. A number in a comparison is better named than suppressed ([X4](numerics.md#x4)).

<a id="c5"></a>
### C5. Fix a SonarCloud finding; never suppress it with NOSONAR

**Why.** A NOSONAR closes the warning without closing the issue. Across a reorganization that moved nearly every file it would have seeded suppressions for debt nobody looked at; an open issue is better than a hidden one.

**Do**

```python
import math


def require_positive_time(t: float) -> float:
    if math.isnan(t) or t <= 0.0:
        msg = "'t' must be positive."
        raise ValueError(msg)
    return t
```

**Don't**

```py
if not t > 0:  # NOSONAR
    msg = "'t' must be positive."
    raise ValueError(msg)
```

**Enforced by:** review

**Exceptions.** Where the analyzer's rule is right, change the code. Where it is wrong but the code can be written another way that satisfies it with the same meaning, write that: `math.isnan(t) or t <= 0.0` for `not t > 0`, which keeps the refusal of NaN. Where neither works, leave the issue open.

## Module length

<a id="d22"></a>
### D22. Judge a module's length by its subject, never by a line count

**Why.** No Python authority sets a file limit: PEP 8 limits the line, pylint's C0302 and Sonar's python:S104 both hedge theirs, and ruff has rejected the rule. A module that implements one standard end to end is not too long at 1800 lines when half of it is the prose that makes it auditable; it is too long when it holds several subjects someone would each look for by name.

**Do**

```text
Ask what the file is about. One sentence, and the length is what documenting
it costs: leave it. The answer needs "and", and each half has its own
constants, result types and callers: two modules.
```

**Don't**

```text
Split a 1500-line module at line 1000 because a linter's too-many-lines says so.
```

**Enforced by:** review

<a id="d23"></a>
### D23. Split a module as a pure move: names, docstrings, bodies and outputs unchanged

**Why.** Byte-identical artifacts are the proof that nothing changed, which is why the conformance report, the figures and the diagrams are regenerated and diffed after a split.

**Do**

```text
make conformance
make graphs
git diff --exit-code
```

**Don't**

```text
A split that also renames a public function, rewords its docstring or tidies a body.
```

**Enforced by:** `make conformance`, review

**Exceptions.** The one rename a split may carry is a private name that named nothing (the diagram builders `_d1` to `_d9`, already registered under their real names), as a separate, deliberate change that stops at names no caller outside the file can see.
