← [Documentation index](../README.md)

# Documentation and figures

This page governs what a reader of phonometry sees outside the code: the guides of the site, their Spanish twins and their plain-markdown mirror under `docs/`; the code fences those pages print; the figures, plates, fiches and clips the generators draw, and the `.plot()` code that draws them; how a record shows itself in a notebook; the published catalogues pages; the errata register; the frames of a clip, held to the figure gates before it is encoded, and the device its field steps on; the install commands a page prints; the description a search result shows for each page; and how much HTML a page may weigh. Read it before you add or change a guide, a figure or a renderer, an animation, an errata entry or an install command. The signature of `.plot()` and where a renderer imports matplotlib are API rules ([A28](api.md#a28), [A10](api.md#a10)); the slope of a subscript, in a docstring or on a plate, is set by [D16 to D21](docstrings.md#d16); the wording of the prose itself is in [prose.md](prose.md). Examples that import from `phonometry._plot`, `phonometry._i18n` or `phonometry._internal` stand for code inside the package, where the import is relative ([A11](api.md#a11)).

## Guides and the docs mirror

<a id="f1"></a>
### F1. Change a guide's English page, Spanish twin and docs/ mirror together

**Why.** `docs/` is the hand-written plain-markdown edition for GitHub and llms.txt, not a generated mirror; a guide edit that touches one copy leaves two readers behind.

**Do**

```text
one commit edits site/src/content/docs/<route>.mdx,
site/src/content/docs/es/<route>.mdx and docs/<route>.md
```

**Don't**

```text
the English page fixed now, the Spanish twin and the docs/ mirror later
```

**Enforced by:** `site/scripts/check-i18n-parity.mjs`, review

**Exceptions.** The docs/ mirror may carry fewer examples, but what it carries follows the same fence rules. The contributor guide (`docs/contributing/`) is repository-only: no site page, no Spanish twin. `check-i18n-parity.mjs` proves each English page has a twin at the same path, not that a change reached both.

<a id="f2"></a>
### F2. Write the docs mirror without frontmatter, and its figures as absolute `<picture>` links

**Why.** GitHub resolves nothing else: the mirror carries no frontmatter and no Astro component, and a figure is a plain `<picture>` with raw.githubusercontent.com URLs, where the site writes `<ThemeImage>`.

**Do**

```markdown
<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/workroom_spatial_decay_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/workroom_spatial_decay.svg" alt="The sound distribution value against distance" width="88%"></picture>
```

**Don't**

```markdown
<ThemeImage src="workroom_spatial_decay.svg" alt="The sound distribution value against distance" />
```

**Enforced by:** review

**Exceptions.** The docs/ mirror page keeps a hand-written references section (the site renders them from the frontmatter).

<a id="f3"></a>
### F3. Link every new guide from `docs/README.md`

**Why.** `docs/README.md` is the hand-kept front door of the mirror; a guide not linked from it fails the mirror check and the llms generator.

**Do**

```markdown
- [Spatial sound decay in workrooms (ISO 14257, ISO 11690-3)](buildings/rooms/workroom-sound-decay.md): the spatial sound distribution curve of a workroom, the rate of spatial decay ...
```

**Don't**

```text
docs/buildings/rooms/workroom-sound-decay.md added, docs/README.md unchanged
```

**Enforced by:** `scripts/mirror_overviews.py`, `scripts/generate_llms.py`

<a id="f4"></a>
### F4. Register a new guide in `topics.mjs` and the guides index, counted in figures and words

**Why.** The site sidebar is not automatic: without `topics.mjs` the Astro build fails the page ('Failed to find the topic'), and the guides index carries the count of guides in figures and in words, in both languages (#676 took two CI rounds for this).

**Do**

```text
site/src/data/topics.mjs: the slug under its topic (no es/ prefix)
site/src/content/docs/start/guides.md and es/: the link, its one-line summary,
the count in figures (description and body) and in words
```

**Don't**

```text
The new .mdx page added alone, the sidebar assumed to find it.
```

**Enforced by:** `site/scripts/check-guides-index.mjs`, `CI: Site builds and validates`

**Exceptions.** A guide that opens a new area also needs its `AREAS` entry in `scripts/generate_llms.py`, its section in `docs/README.md` and a 24x24 drawing in `site/src/data/icons.mjs` (look at the icon sheet at 16 px); renumber the guides index's JSON-LD positions top to bottom.

<a id="f5"></a>
### F5. Never edit a generated file by hand; change its source and regenerate it

**Why.** The section indexes of docs/ are mirrors of the site overviews written by `scripts/mirror_overviews.py`, and `docs/conformance.json` and `docs/CONFORMANCE.md` are written by `make conformance`: editing one by hand left the mirror stale and failed two CI jobs at once, and a hand edit of the artifact passes a byte diff on one machine and breaks the site build.

**Do**

```text
edit site/src/content/docs/<area>/index.mdx, then make llms
change a conformance script, then make conformance
```

**Don't**

```text
edit docs/<area>/index.md or docs/conformance.json directly
```

**Enforced by:** `scripts/mirror_overviews.py`, `scripts/check_conformance_artifact.py`, `make conformance`, `CI: Conformance report up to date`, `CI: llms artifacts up to date`

**Exceptions.** Guide pages in docs/ are hand-written twins; only the section indexes and `docs/reference/glossary.md` (`scripts/mirror_glossary.py`) are mirrored. `docs/README.md`, the indexes under `docs/reference/` and `docs/contributing/` are written by hand.

<a id="f6"></a>
### F6. Never type a conformance count in prose; `make conformance` writes it

**Why.** Pages that typed the counts fell a release behind (the landing page said 427 checks while Why phonometry said 371; the READMEs said 'more than 250 standards' against 365), and PyPI freezes a long description at upload. The check and the writer read one list of patterns, so a count in a matching sentence is rewritten in place.

**Do**

```bash
make conformance   # writes docs/CONFORMANCE.md, then the counts quoted from it
python scripts/check_conformance_claims.py
```

**Don't**

```text
Edit docs/CONFORMANCE.md, or type "1893 conformance checks" into a guide or .zenodo.json.
```

**Enforced by:** `scripts/check_conformance_claims.py`, `make conformance`, `CI: Conformance report up to date`

**Exceptions.** Site page bodies import the counts from `site/src/data/conformance-stats.mjs` at build time. A new place a count is quoted needs a pattern in `CLAIMS` of the script and nothing else. Generated and historical files (`docs/CONFORMANCE.md`, `CHANGELOG.md`, `docs/ERRATA.md`) are excluded.

<a id="f7"></a>
### F7. Put a site page's references in its frontmatter, never under a hand-written heading

**Why.** The layout renders the frontmatter `references:` with `id="references"`; a hand `## References` adds a second one and html-validate fails `no-dup-id`, on the English page only (the Spanish heading makes `id="referencias"`), and no local gate sees it short of building the site (#647).

**Do**

```markdown
---
references:
  - type: standard
    designation: ITU-R BS.468-4
    note: Clauses used: 2 and 3.
---
```

**Don't**

```markdown
## References

- ITU-R BS.468-4
```

**Enforced by:** `CI: Site builds and validates`

**Exceptions.** The docs/ mirror page, read on GitHub without the layout, keeps a hand references section. Clauses used go in each reference's `note:`.

<a id="f8"></a>
### F8. Give every `<ScopeClaim>` its `status`

**Why.** The component validates `status` at build time, so a bare `<ScopeClaim>` fails 'Build site' after twenty minutes of queue (three new guides, six pages, 2026-09-08).

**Do**

```markdown
<ScopeClaim status="covered" label="What this guide covers">...</ScopeClaim>
```

**Don't**

```markdown
<ScopeClaim>...</ScopeClaim>
```

**Enforced by:** `CI: Site builds and validates`

**Exceptions.** `label` is separate and optional: give it where the status varies in the panel (one of each in a guide's 'What this guide covers'), only on the first of a run of the same status, and omit it in an index's 'What this section does not cover'.

<a id="f9"></a>
### F9. Pass `<ThemeImage>` the plain figure name; it adds the language and theme suffixes

**Why.** The component appends `_es` and `_dark` from the page and refuses a source that already carries them ('would resolve to _es_es'), so a Spanish page copies the English `src` and translates only the `alt` (#763).

**Do**

```markdown
<ThemeImage src="workroom_spatial_decay.svg" alt="Decaimiento espacial del nivel..." />
```

**Don't**

```markdown
<ThemeImage src="workroom_spatial_decay_es.svg" alt="..." />
```

**Enforced by:** `CI: Site builds and validates`

<a id="f10"></a>
### F10. Link an API reference page by its hyphenated module slug

**Why.** `train_categories.py` publishes at `/reference/api/vibration/train-categories/`; a link written `train_categories` builds without a complaint and is a 404 on the site, and no gate sees it.

**Do**

```markdown
[train categories](/phonometry/reference/api/vibration/train-categories/)
```

**Don't**

```markdown
[train categories](/phonometry/reference/api/vibration/train_categories/)
```

**Enforced by:** review

**Exceptions.** The package folder keeps its own name (`reference/api/noise_control/...`); only the module segment is hyphenated. Check the slug against `ls site/src/content/docs/reference/api/<family>/`.

<a id="f11"></a>
### F11. Write only absolute URLs in README.md: it is the PyPI page

**Why.** PyPI renders the README and does not resolve relative links; images already use raw.githubusercontent.com URLs.

**Do**

```markdown
[Documentation](https://docs.jmrp.io/phonometry/)
```

**Don't**

```markdown
[Documentation](docs/README.md)
```

**Enforced by:** review

**Exceptions.** Keep a prominent Documentation section with absolute links near the top.

## Markdown that renders the way it reads

<a id="f12"></a>
### F12. Never let a hard-wrapped line start with `-`, `>`, `=` or `N.` in mid-sentence

**Why.** CommonMark reads such a line as a list item, a block quote or an ordered list and ends the paragraph: an inline `$...$` that wrapped onto `- K_{ij}` never closed and the MDX page failed with 'ReferenceError: n is not defined'; a wrapped `>` silently turned the tail of a sentence into a quote, three times. A wrapped line of nothing but `=` or `-` is a setext underline that makes the text above it a heading: a formula wrapped before its `=` gave the errata page a second h1 and rendered the rest of its list item inside out.

**Do**

```markdown
the sum of the paths, minus $K_{ij}$, gives
$L_{n,ij,w}$.
```

**Don't**

```markdown
the sum $L_{n,ij,w} = L_{n,w} - \Delta R_{j,w}
- K_{ij}$ gives ...
```

**Enforced by:** `scripts/check_markdown_hazards.py`, `make hazards`, `CI: Markdown renders the way it reads`

**Exceptions.** A list that follows its introducing line without a blank line is ordinary (3830 of them) and only reported when it interrupts an open `$`. A deliberate block quote, and a thematic break, are preceded by a blank line. A display block between two `$$` lines is maths, not markdown: a formula written one term per line may put `=` alone on a line.

<a id="f13"></a>
### F13. Link an accented heading through an ASCII `<span id>` placed above it

**Why.** Markdown percent-encodes non-ASCII in a URL, so a link to the fragment `#la-medición` ships as `#la-medici%C3%B3n` while the heading keeps its id unencoded; the accessibility check reports a dangling anchor, and five of six such links went unreported because it samples. A link into another page of the site breaks the same way: a search engine audit of the published site found 150 of them, all from one Spanish page to another.

**Do**

```markdown
<span id="la-medicion"></span>

## La medición

... ver [la medición](#la-medicion)
```

**Don't**

```markdown
... ver [la medición](#la-medición)
```

**Enforced by:** `scripts/check_markdown_hazards.py`, `make hazards`, `CI: Markdown renders the way it reads`, `site/scripts/check-crawl.mjs`, `CI: Check what a search engine reads on every page`

<a id="f14"></a>
### F14. Open and close a `$$` display block on lines of their own

**Why.** Display math is a fence: `$$\tau = ...` opens a block that ends only at the next line that is exactly `$$`, so it swallowed two hundred lines of prose and the build failed with 'Could not parse expression with acorn' two hundred lines from the cause. Closed on the same line, it parses silently as inline math.

**Do**

```markdown
$$
\tau = \frac{1}{2}
$$
```

**Don't**

```markdown
$$\tau = \frac{1}{2}$$
```

**Enforced by:** `scripts/check_markdown_hazards.py`, `make hazards`, `CI: Markdown renders the way it reads`

<a id="f15"></a>
### F15. Escape a `<` in MDX prose unless a space or a tag name follows it

**Why.** MDX reads `<` as the start of a JSX tag, so a quoted '<0,02 above 200 Hz' in the prose of an .mdx page fails the build with 'Unexpected character `0` before name', and only the site build sees it.

**Do**

```markdown
a deviation of \<0,02 dB above 200 Hz
```

**Don't**

```markdown
a deviation of <0,02 dB above 200 Hz
```

**Enforced by:** `scripts/check_markdown_hazards.py`, `make hazards`, `CI: Markdown renders the way it reads`

**Exceptions.** A `<` in inline code, in math, inside a quoted JSX attribute value, or in the YAML frontmatter is fine; a plain .md page is not read as MDX.

## Code fences

<a id="f16"></a>
### F16. Write a page's Python blocks to run in reading order, on this branch's names

**Why.** A guide is a narrative and an example that does not run teaches the wrong thing: every English page, its docs/ mirror, the README, llms.txt and the site home page run as one script per page. A guide used `fluids.sea_water` before the change that adds it had landed; the working tree had it, the reader of that pull request did not.

**Do**

```python
from phonometry import filters

bands = filters.nominal_frequencies(3)
```

**Don't**

```py
spl, freq = filters.octave_filter(x, fs)  # a tuple unpacking that is false in 4.0
```

**Enforced by:** `scripts/check_doc_snippets.py`, `make snippets`, `CI: Documentation snippets run`

**Exceptions.** `_SKIP` in `scripts/check_doc_snippets.py`, keyed by page slug with a specific reason ('needs a file the repository does not ship' is a fact, 'example' is not); a page that starts passing must leave it. A file the reader brings is written first by `_FIXTURES`. A block that passes `...` to a call is a sketch: read by the static checks, not run. `--static` runs nothing: run the full check (about five minutes) before pushing prose with snippets.

<a id="f17"></a>
### F17. Use in a fence only names that an earlier fence of the same page defined

**Why.** The blocks of a page form one sequential example. One page used `ir` and `fs` defined only in the figure block further down, and an `ir` from an earlier, different room was in scope, so reading the page top to bottom gave numbers that were not the annotated ones, with no visible error. The llms.txt shards inherit the fences verbatim.

**Do**

```markdown
(first fence)  volume = 200.0
(later fence)  room.sabine_reverberation_time(volume, [(120.0, 0.25)])
```

**Don't**

```markdown
(first fence)  room.sabine_reverberation_time(volume, surfaces)
(later fence)  volume = 200.0
```

**Enforced by:** `scripts/check_fence_names.py`, `make fence-names`, `CI: Documentation fences read in order`

**Exceptions.** Names the reader owns are registered placeholders ([F19](#f19)). Builtins and `_` are exempt.

<a id="f18"></a>
### F18. Define an annotated value in the fence that annotates it, or the one just before

**Why.** A value annotated a section away from where it is computed is the one a reader cannot check by reading down the page; no script can tell which values matter.

**Do**

```python
from phonometry import room

t60 = room.sabine_reverberation_time(200.0, [(120.0, 0.25)])  # 1.07 s
```

**Don't**

```py
print(t60)  # 1.07 s   (t60 computed three sections earlier)
```

**Enforced by:** review

<a id="f19"></a>
### F19. Register a name the reader owns in `PLACEHOLDERS`, and introduce it as theirs

**Why.** Inventing a value for the reader's measurement would replace their data with the page's, so the page never defines it; the registry tells the fence checker the name is deliberate.

**Do**

```text
scripts/check_fence_names.py, PLACEHOLDERS:
    "signals/levels/time-weighting": frozenset({"audio_blocks"}),
the page's fence:
    # audio_blocks: successive frames of your microphone recording
```

**Don't**

```py
audio_blocks = np.random.default_rng(0).normal(size=(10, 4800))  # the page's data posing as the reader's
```

**Enforced by:** `scripts/check_fence_names.py`, `make fence-names`, `CI: Documentation fences read in order`

**Exceptions.** Key the entry by the page's route with the es/ prefix stripped, so the Spanish twin is held to the same set. A docs/ mirror page is keyed `docs/<path>` (`docs/signals/levels/time-weighting`). A page that uses a placeholder cannot run, so it also goes in `_SKIP` of `scripts/check_doc_snippets.py` with its reason ([F16](#f16)). Binding the name to `...` (Ellipsis) with the same comment is the older idiom and also valid: it defines the name, needs no registry line, and makes the fence unrunnable.

<a id="f20"></a>
### F20. Never rebind a name imported from phonometry inside a documentation example

**Why.** When the package split, `from scipy import signal` next to `from phonometry import signal` rebound the name silently and the snippet crashed several lines further down with an `AttributeError` pointing nowhere near the import. Python gives no warning.

**Do**

```python
from scipy import signal as sp_signal

from phonometry import signals
```

**Don't**

```py
from phonometry import signals
from scipy import signal as signals
```

**Enforced by:** `scripts/check_doc_snippets.py`, `make snippets-static`, `CI: Documentation snippets run`

<a id="f21"></a>
### F21. Import exactly the same phonometry names on a Spanish page as on its English twin

**Why.** A Spanish page may translate comments and labels and ask for `plot(language="es")`, but it must teach the same API; comparing whole token streams was tried and failed on the language argument, which is the one difference the twins are meant to have.

**Do**

```text
guide.mdx and its Spanish twin both write: from phonometry import room
```

**Don't**

```text
English twin: from phonometry import room
Spanish twin: from phonometry.room import spatial_decay
```

**Enforced by:** `scripts/check_doc_snippets.py`, `make snippets-static`, `CI: Documentation snippets run`

**Exceptions.** The docs/ mirror is written by hand for GitHub and is not paired with anything.

<a id="f22"></a>
### F22. Fence an example that must not run as `py`; only a `python` fence runs

**Why.** The snippet gate and the fence-name gate read a fence as Python when the first word of its info string is `python`; a wrong example fenced `python` either fails the build or, worse, passes and teaches the wrong code as working.

**Do**

````markdown
```py
result = octave_filter(signal, sample_rate)  # the old spelling, shown as wrong
```
````

**Don't**

````markdown
```python
result = octave_filter(signal, sample_rate)  # runs, and fails the gate
```
````

**Enforced by:** `scripts/check_doc_snippets.py`, `tests/test_contributing_guide.py`

**Exceptions.** A non-Python example takes its own language (`text`, `markdown`, `json`, `bash`).

<a id="f23"></a>
### F23. Read a page's fences through `scripts/markdown_fences.py`, never by hand

**Why.** Each script that worked out fences its own way (a flag flipped on any line starting with three backticks, a three-character slice, a regex running to the next backticks) read a page with a fence inside another inside out, and one never saw a tilde fence. A fence closes only on its own marker, at least as long as the opener, with nothing after it (CommonMark 0.31.2, 4.5).

**Do**

```python
import pathlib
import sys

import phonometry

checkout = pathlib.Path(phonometry.__file__).resolve().parents[2]
sys.path.insert(0, str(checkout / "scripts"))  # a script in scripts/ has it already
from markdown_fences import python_fences

bodies = python_fences("Prose.\n\n~~~python\nx = 1\n~~~\n")  # ['x = 1\n']
```

**Don't**

```py
in_code = False
for line in text.splitlines():
    if line.startswith("```"):
        in_code = not in_code
```

**Enforced by:** `scripts/check_fence_readers.py`, `make fence-readers`, `CI: Markdown renders the way it reads`

**Exceptions.** The site's code reads fences through `site/src/lib/markdown-fences.mjs` (`codeLines()`, `prose()`, `fences()`), and a test holds the two readers to the same answer. A script that writes a fence is not reading one. `EXEMPT` of the check, keyed (file, function) with its reason, is empty.

## What a guide shows

<a id="f24"></a>
### F24. Show in a guide figure a realistic result through its `.plot()`, one concept each

**Why.** A figure of the standard's own curves (a printed limit table, the coordinates of a microphone array, a sweep of a constant) is reference, not a result: it teaches nothing the reader can reproduce with the library. A guide shows what a user's computation returns, drawn the way the user will draw it.

**Do**

```text
example data -> the real function -> its result record -> result.plot()
(one concept per figure; two concepts are two results and two figures)
```

**Don't**

```text
A figure of the standard's limit table, drawn by hand, with no result behind it.
```

**Enforced by:** review

**Exceptions.** Setup diagrams and infographics (`scripts/diagrams`) are schematics with no `.plot()`. Every snippet whose result has `.plot()` carries its figure beside it, in the site guides and the docs/ mirror alike.

<a id="f25"></a>
### F25. Give each figure its code in a `<details>`: the `.plot()` line and plain matplotlib

**Why.** The reader gets both the one line that reproduces the figure and the matplotlib that shows what it draws (decided 2026-07-08 with the `.plot()` convention).

**Do**

```markdown
<details>
<summary>Show the code for this figure</summary>

(one fence: result.plot())

(one fence: the same figure in plain matplotlib)

</details>
```

**Don't**

```markdown
<details>
<summary>Show the code for this figure</summary>

(one fence: result.plot())

</details>
```

**Enforced by:** review

<a id="f26"></a>
### F26. Give an example the real dimensions of a standard's or common equipment's setup

**Why.** Teaching figures with invented dimensions lose credibility; with the dimensions of real setups the reader recognizes the hardware (2026-07-27).

**Do**

```text
impedance tube: 100 mm (B&K 4206), microphone spacing 50 mm; p-p probe spacer
12 mm; ISO 13472-1 loudspeaker at 1.25 m and microphone at 0.25 m
```

**Don't**

```text
a 37 mm tube with microphones 21 mm apart
```

**Enforced by:** review

**Exceptions.** The source of the dimensions need not be cited in the prose. Adjust unrealistic published examples when you touch that area.

## The language of a figure

<a id="f27"></a>
### F27. Pass the caller's language on to every helper that takes one

**Why.** A figure is drawn in Spanish by handing `language="es"` from `.plot()` down to every helper that writes text, and every helper defaults to English. A call that forgets it raises nothing: the K-weighting response drew its lowest octave as 31.5 under `plot(language="es")`, and no later pass can repair a frequency axis `format_frequency_axis` already wrote as fixed strings.

**Do**

```python
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from phonometry._i18n import Language
from phonometry._plot.common import format_frequency_axis


def _label_band_axis(ax: Axes, *, language: Language = "en") -> None:
    format_frequency_axis(ax, 63.0, 8000.0, language=language)


fig, ax = plt.subplots()
_label_band_axis(ax, language="es")
plt.close(fig)
```

**Don't**

```py
def _label_band_axis(ax, *, language="en"):
    format_frequency_axis(ax, 63.0, 8000.0)                 # dropped
    format_frequency_axis(ax, 63.0, 8000.0, language="en")  # also dropped
```

**Enforced by:** `scripts/check_language_forwarding.py`, `make language-forwarding`, `CI: Every call passes the language on`

**Exceptions.** A call that must stay English on purpose goes in `EXEMPT` of the script, keyed by 'file:line::caller -> callee' with its reason (one entry), so one approved call cannot cover a second; a moved or fixed entry fails. `MIXED_NAMESAKES` and `FOREIGN_NAMESAKES` record method names shared by unrelated things (`plot` is also `Axes.plot`). A callable pulled out of a mapping, reached by `getattr` or passed in as a parameter is out of the gate's reach and is review.

<a id="f28"></a>
### F28. Write every number of a Spanish figure with a decimal comma

**Why.** Three machines put the comma there (`localize_axes`, `format_frequency_axis` given the language, and the save-time pass of `scripts/figures/i18n.py`), and a panel none reached shipped 31.5 next to 52,4 with every gate green: a frequency axis that did not get the language, a log distance axis, the z of a 3-D array, a zoom inset, a colorbar.

**Do**

```python
from phonometry._i18n import localize_axes

fig, ax = plt.subplots()
ax.plot([0.5, 1.5], [1.25, 2.5])
twin = ax.twinx()
twin.plot([0.5, 1.5], [0.1, 0.2])
for axes in (ax, twin):
    localize_axes(axes, "es")
plt.close(fig)
```

**Don't**

```py
twin = ax.twinx()
...
localize_axes(ax, language)  # the twin keeps 0.1 and 0.2
```

**Enforced by:** `tests/test_plot_localized_panels.py`, `scripts/check_figure_decimal_point.py`, `make figure-decimal-point`, `CI: Documentation figures up to date`

**Exceptions.** End a plot function with `localize_axes` on every axes it built (a twin, a colorbar, the z of a 3-D panel each carry their own formatter); a panel the save-time pass cannot reach (a zoom inset, a contour colorbar) is localized by the generator with `figures.i18n.localize_panel`. Write the clause word before a clause number a figure cites after a designation ('(ISO 7626-5, clause 6.4)'), or the pass turns it into a decimal. A clause number is not a measurement and keeps its point (`ALLOWED` of the check, keyed 'figure: label' with its reason).

<a id="f29"></a>
### F29. Format a number in a label beside mathtext through `format_number(value, language)`

**Why.** The Spanish figure is the English one rewritten at save time, and the decimal-comma pass skips any string containing `$` (a bare comma inside `$...$` sets with math spacing). So `'$L_\mathrm{eq}$ = 52.4 dB'` kept the English point in Spanish, and no other gate could see it.

**Do**

```python
from phonometry._i18n import format_number

label = f"$L_\\mathrm{{eq}}$ = {format_number(52.4, 'es')} dB"
```

**Don't**

```py
label = "$L_\\mathrm{eq}$ = 52.4 dB"
```

**Enforced by:** `scripts/check_decimal_comma.py`, `make decimal-comma`, `CI: Documentation figures up to date`

**Exceptions.** Numbers that are not measurements keep their point in both languages and are skipped by `_NOT_A_MEASUREMENT`: clause numbers (5.3.3), designations (S3.5, ISO 9613-2), and a pointer into a document (Eq., clause, table, figure, annex, note, in English and Spanish). Placeholders are ignored. The alternative fix the guard accepts is baking the comma into the Spanish value.

<a id="f30"></a>
### F30. Sign a negative number in a figure or plate with U+2212, never a hyphen

**Why.** The hyphen is shorter and sits lower, so a figure that mixes the two puts the short one wherever a label escaped the formatter: the polar `ThetaFormatter` wrote '-30°' under '−15', an f-string reading wrote '$c_3$ = -0.6', and a plate numbered a decay range '-10' to '-70'.

**Do**

```python
from phonometry._i18n import fmt_minus

label = fmt_minus(-3.5, ".1f")  # "−3.5", signed with U+2212
```

**Don't**

```py
label = f"{value:.1f} dB"  # -3.5 with a hyphen-minus
```

**Enforced by:** `scripts/check_figure_minus_sign.py`, `make figure-minus-sign`, `CI: Documentation figures up to date`

**Exceptions.** A hyphen that is not a sign (a part number after a slash, 'ISO 9053-1/-2'; code quoted as typed) goes in `ALLOWED` of the script with its reason; a stale entry fails. Generators use `_fmt_minus` from `scripts/figures/i18n.py`, plates sign from `scripts/diagrams/canvas.py`, and a polar angle grid below zero restates its labels. Mathtext in a matplotlib figure is not read (matplotlib sets U+2212 itself).

<a id="f31"></a>
### F31. Add every string a figure draws to the Spanish translation tables, in the same edit

**Why.** Figures are drawn in English and translated at save time by exact match or pattern (`scripts/figures/i18n.py`, `scripts/diagrams/i18n.py`); a string nobody added is written into `X_es.svg` in English and nothing downstream sees it. About two hundred figures reached the tree that way.

**Do**

```text
scripts/figures/i18n.py, _ES_EXACT:  "Scattering coefficient": "Coeficiente de dispersión"
```

**Don't**

```py
ax.set_ylabel("Scattering coefficient")  # and no entry added to _ES_EXACT or _ES_PATTERNS
```

**Enforced by:** `scripts/check_figure_language.py`, `make figure-language`, `CI: Documentation figures up to date`

**Exceptions.** When a drawn English label changes, change its Spanish key in the same edit: the language gate sees the old key only on a full run. Give each drawn label its own constant and Spanish twin; never derive one from another (a legend cut from the title at the dash breaks when a translation punctuates differently). `ENGLISH_BY_DESIGN` of the script holds a string that stays English with its reason (an API call quoted as typed); `scripts/figure_language_baseline.txt` is a ratchet of debt, empty, never added to by hand.

<a id="f32"></a>
### F32. Translate a label built from fixed numbers as an exact entry, not a pattern

**Why.** A pattern is selected for a clip when all its fixed spans appear in the clip's literals: `^(\d+\.\d+) to (\d+\.\d+) Hz$` has the spans ' to ' and ' Hz', present in nearly every clip, and marked all 43 clips stale (2026-09-07). Short generic exact keys (`height`, `short-term`) staled three clips each; longer, specific labels fixed both.

**Do**

```text
_ES_EXACT:    "0.56 to 1.19 Hz": "0,56 a 1,19 Hz"
```

**Don't**

```text
_ES_PATTERNS: (r"^(\d+\.\d+) to (\d+\.\d+) Hz$", r"\1 a \2 Hz")
```

**Enforced by:** `scripts/check_animation_freshness.py`, `make animation-freshness`

**Exceptions.** Keep patterns for labels that really vary at run time. Before adding a one-word key to `_ES_EXACT`, run `scripts/check_animation_freshness.py`: it takes seconds.

## Drawing code

<a id="f33"></a>
### F33. Default a matplotlib style through `style_default`, `style_get`, `style_pop` or `styled`

**Why.** Matplotlib aliases seven artist properties (color/c, linewidth/lw, linestyle/ls, markersize/ms and the three marker-edge and marker-face pairs) and refuses a call that receives both spellings. `kwargs.setdefault("color", ...)` therefore breaks every caller who wrote `c=`, `kwargs.pop("color", ...)` silently draws a second artist in the library's color, and `{"color": ..., **kwargs}` does the same as a literal. The defect reads exactly like the hundred lines around it.

**Do**

```python
from phonometry._plot.common import style_default, styled

kwargs = {"c": "red"}
style_default(kwargs, "color", "#1f77b4")  # the caller's c is kept
line_style = styled({"lw": 2.0}, color="#1f77b4", linewidth=1.5)  # {'lw': 2.0, 'color': '#1f77b4'}
```

**Don't**

```py
kwargs.setdefault("color", _C_PRIMARY)
color = kwargs.pop("color", _C_PRIMARY)
ax.plot(x, y, **{"color": _C_PRIMARY, "lw": 1.5, **kwargs})
```

**Enforced by:** `scripts/check_plot_style_defaults.py`, `make plot-style-defaults`, `CI: Every call passes the language on`, `tests/test_check_plot_style_defaults.py::test_the_package_is_clean`

**Exceptions.** Only the aliased properties are refused; `label`, `marker` and `zorder` have one name. A local dictionary the caller never sees may hold anything. The gate also fails if its alias table drifts from `_STYLE_ALIASES` in `src/phonometry/_plot/common.py`. It runs as a step of the CI job named 'Every call passes the language on'.

<a id="f34"></a>
### F34. Copy the keyword arguments per curve before setting a label inside a loop

**Why.** `dict.setdefault` mutates, so one `setdefault("label", ...)` on the shared kwargs inside a loop names every curve after the first; nothing crashes, the legend repeats one entry, and the only thing that noticed was a report preview drifting by 693 pixels.

**Do**

```python
from typing import Any


def draw(ax: Axes, curves: dict[str, list[float]], **kwargs: Any) -> None:
    for name, values in curves.items():
        style = {**kwargs}
        style.setdefault("label", name)
        ax.plot(values, **style)
```

**Don't**

```py
def draw(ax, curves, **kwargs):
    for name, values in curves.items():
        kwargs.setdefault("label", name)
        ax.plot(values, **kwargs)
```

**Enforced by:** `tests/test_result_plots.py::test_no_renderer_defaults_a_label_on_the_shared_kwargs_inside_a_loop`

<a id="f35"></a>
### F35. Label a frequency axis with `format_frequency_axis`, and clear hand-set log minor labels

**Why.** matplotlib's default log formatter writes 10^2 and 10^3, which reads badly in acoustics, and review kept finding it on new renderers (2026-07-21). The helper labels the nominal octave centers (below 1000 as the number, from 1000 as `1k`, `2k`) and writes them in the caller's language.

**Do**

```python
from matplotlib.ticker import NullFormatter

fig, (ax, ax_hand) = plt.subplots(1, 2)
format_frequency_axis(ax, 63.0, 8000.0, language="es")
ax_hand.set_xscale("log")
ax_hand.set_xticks([125, 250, 500], ["125", "250", "500"])
ax_hand.xaxis.set_minor_formatter(NullFormatter())
plt.close(fig)
```

**Don't**

```py
ax.set_xscale("log")
ax.set_xticks([125, 250, 500], ["125", "250", "500"])  # minor labels left to the scale
```

**Enforced by:** `scripts/check_figure_ticks.py`, `make figure-ticks`, `CI: Documentation figures up to date`, review

**Exceptions.** A categorical band axis uses `_band_axis`. A log axis that is not a frequency (distance, speed, wavelength, ka) takes `NullFormatter` for its minor ticks. A frequency axis that reaches below 1 Hz keeps a plain log axis, because the octave centers the helper labels start at 1 Hz (the whole-body vibration verifications, `plot_weighting_verification` and `plot_phase_verification`). The check catches stray minor labels beside hand-set major ticks and tick labels that touch, not a default formatter left on a frequency axis: that half is review.

## Mathematics and type in figures

<a id="f36"></a>
### F36. Wrap only mathematics in `$...$`; words, units and numbers stay text

**Why.** matplotlib routes any string with a `$` through mathtext, and review found titles and legends of plain words set as math in many new plots (`$Thomson multitaper density$`). Policy of 2026-08-13; the corpus was migrated in #540 to #545.

**Do**

```python
title = "Thomson multitaper density, $K$ = 5"
```

**Don't**

```py
title = "$Thomson multitaper density, K = 5$"
```

**Enforced by:** review

**Exceptions.** Inside the math: variables, Greek, sub- and superscripts, formulas. Outside: units, numbers in prose, prose acronyms and words. In the diagram canvas the math is a tspan composer, not LaTeX: a backslash there is an error.

<a id="f37"></a>
### F37. Write mathtext a figure label can parse; never chain two superscripts

**Why.** A label mathtext cannot parse raises and the figure is never written; the only gate that notices is check_figures, which calls the figure 'stale' and sends the reader after a data change. `^{\prime}^{\prime}` is a double superscript matplotlib rejects, and a mechanical substitution of a double prime produced it in three labels.

**Do**

```python
label = r"$x^{\prime\prime}$"
```

**Don't**

```py
label = r"$x^{\prime}^{\prime}$"
```

**Enforced by:** `scripts/check_mathtext.py`, `make mathtext`, `CI: Documentation figures up to date`

**Exceptions.** Strings that carry a dollar without being a label are recognized by shape, not listed: the `_ES_PATTERNS` regexes and their replacements, and the shell text of the GPU ffmpeg wrapper.

<a id="f38"></a>
### F38. Set figure titles in regular weight, never bold

**Why.** matplotlib does not carry the weight into `$...$`, so a bold title with a formula mixes two weights; the ISO 80000 argument for keeping them was false (ISO 80000 rules the slope of a symbol 'irrespective of the type used in the rest of the text', never its weight), and published figures carry no bold title (decided 2026-08-14; 551 sites changed).

**Do**

```python
fig, ax = plt.subplots()
ax.set_title("Spatial decay of the level, $DL_2$")
plt.close(fig)
```

**Don't**

```py
ax.set_title("Spatial decay of the level, $DL_2$", fontweight="bold")
```

**Enforced by:** review

<a id="f39"></a>
### F39. Name a plate's descriptive letter outside `_ROMAN_SCRIPTS` with `upright=`, a sloped one with `sloped=`

**Why.** The plate composer keys the slope on the letter run, and the runs that must stay italic somewhere (the i of an index, the p of $L_p$) are deliberately absent from `_ROMAN_SCRIPTS`, so the call that draws a descriptive one has to say so.

**Do**

```text
s.text(x, y, "$S_p$", 13, th.muted, upright=("S_p",))   # ISO 8297 plant area, upright on its plate
s.text(x, y, "$ΔL_f$", 12, th.fg, sloped=("ΔL_f",))     # ISO 3747 prints the f italic
```

**Don't**

```text
Add "p" to _ROMAN_SCRIPTS so one plate's S_p reads upright (every L_p of every plate turns upright with it).
```

**Enforced by:** `scripts/check_subscript_slope.py`, `make subscripts`

**Exceptions.** Extend `_ROMAN_SCRIPTS` only for a run that abbreviates a word and is never an index. A key no label of the plate uses is refused when the plate is written. Subscripts in figures and plates follow the slope rules of [D16 to D21](docstrings.md#d16). After changing a plate, regenerate it (`python scripts/generate_diagrams.py`) before running the check.

## Generating figures

<a id="f40"></a>
### F40. Generate every documentation image with `make graphs`, and commit exactly what it writes

**Why.** CI regenerates every figure on a pull request and compares it with the committed files (structure exactly, numbers within a tolerance), which is what catches an unintended change to a plotted result; an image made any other way cannot be regenerated or compared, and an added or orphaned file always fails.

**Do**

```bash
make graphs   # python scripts/generate_graphs.py && python scripts/generate_diagrams.py
make figures  # the same generation, then the legibility and staleness checks CI runs
git add .github/images/<the figures that changed> src/<the change>
```

**Don't**

```text
Export a chart from a notebook or an editor, drop it in .github/images and reference it from a guide.
```

**Enforced by:** `scripts/check_figures.py`, `make figures`, `CI: Documentation figures up to date`

**Exceptions.** Each figure ships as `<n>`, `<n>_dark`, `<n>_es` and `<n>_es_dark`, in SVG, except the figures named in `_RASTER_FIGURES` of `scripts/figures/theme.py`, which are lossless WebP. Example fiches are generated the same way (`make reports`) and compared by their preview within a tolerance (`scripts/check_reports.py`, CI 'Example report fiches up to date'); `make reports` rewrites every PDF, so judge drift with `check_reports.py`, never with `git status`. Clips are not committed here ([F51](#f51)).

<a id="f41"></a>
### F41. Register a figure, diagram or fiche builder in its package's registry

**Why.** `make graphs` walks the registry, so a builder added to the command-line script itself is never drawn.

**Do**

```text
A plot:     scripts/figures/<subject>.py, registered in _FIGURE_FUNCS (scripts/figures/registry.py)
A diagram:  scripts/diagrams/<domain>.py, registered in DIAGRAMS (scripts/diagrams/registry.py)
A fiche:    scripts/reports/<subject>.py, registered in _FICHES (scripts/generate_reports.py), then make reports
```

**Don't**

```text
def generate_my_figure(output_dir): ...   # added to scripts/generate_graphs.py
```

**Enforced by:** review

<a id="f42"></a>
### F42. Draw figure text as outlines and save every figure byte-stable

**Why.** With `svg.fonttype="none"` the viewer swapped DejaVu for a narrower sans while keeping DejaVu's advances, so every label with math shipped letter-spaced (1172 of 2296 figures); random ids and the date made every `make graphs` a noisy diff.

**Do**

```text
scripts/figures/theme.py, save_figure: svg.fonttype = "path", svg.hashsalt = "phonometry",
metadata={"Date": None}; a raster figure: lossless WebP from a PNG with no Software or Date chunk
```

**Don't**

```text
svg.fonttype = "none" and the font family normalized to a generic sans
```

**Enforced by:** `scripts/check_figures.py`, `make figures`, `CI: Documentation figures up to date`

**Exceptions.** Set the hash salt at save time, in `save_figure`: `set_theme()` runs `plt.style.use()`, which resets it. Generate with the pinned matplotlib, never a system one.

<a id="f43"></a>
### F43. Move a figure only on purpose, then look at it in light, dark and Spanish

**Why.** The gates check contrast, clearance, determinism and translation, not whether a figure reads well: `weighting_bs468` (#645) shipped with its annotations across the curves, hard to read, while every gate was green. A change that should move nothing (a rename, a refactor) leaves every figure byte-identical, so a figure it moves is a defect to find, not a figure to look at.

**Do**

```text
Rasterize, look at the region in doubt at a size that settles it (3200 px and
a crop, not a 1200 px thumbnail), in light and dark, and in Spanish where the
text changes length; a fiche: page 1 of the PDF.
```

**Don't**

```text
The generator finished and the gates passed, so the figure is done.
```

**Enforced by:** `scripts/check_figures.py`, `CI: Documentation figures up to date`, review

## Legibility

<a id="f44"></a>
### F44. Move a label off a curve, or chip it opaquely above the curves

**Why.** Letter strokes and a curve's stroke are the same weight and, on the dark page, nearly the same lightness, so a label with a curve behind it cannot be read; a translucent box loses its contrast on the dark page. A chip is opaque and hides any datum under it, so it is the second choice. Something painted over the letters needs a zorder, not a chip.

**Do**

```python
COLOR_PANEL, COLOR_GRID = "#f0f2f5", "#e0e0e0"  # the light theme of scripts/figures/theme.py
fig, ax = plt.subplots()
ax.plot([0, 1], [0, 1])
chip = {"boxstyle": "round,pad=0.5", "facecolor": COLOR_PANEL, "edgecolor": COLOR_GRID}
ax.text(0.5, 0.5, "$L_p$", zorder=5, bbox=chip)
plt.close(fig)
```

**Don't**

```py
ax.text(0.5, 0.5, "$L_p$", bbox={"boxstyle": "round", "facecolor": COLOR_GRID, "alpha": 0.6})  # across the curve
```

**Enforced by:** `scripts/check_figure_annotations.py`, `make figure-annotations`, `CI: Documentation figures up to date`

**Exceptions.** The chip's `pad` follows the neighbors (0.5 most, 0.4 tight, 0.3 a small label pinned to a point). The translucent box is for a note in an empty corner. `scripts/figure_annotation_exemptions.txt` takes an entry only when the fix would make the figure wrong, never because a chip is inconvenient (empty). The check reads a `make graphs` recording, so `make figure-annotations` needs `make graphs` first.

<a id="f45"></a>
### F45. Draw nothing over a tick label: legends, curves, markers and insets stay clear

**Why.** A legend wide enough reached back over the radial '15' and '−90°' of a half disc; a dipole lobe ran through the '−10.0' of a polar ray; a unit circle ran through the '1.0000' of a zoom inset. No other gate measures what is drawn over a tick label.

**Do**

```python
fig, ax = plt.subplots(subplot_kw={"projection": "polar"})
ax.plot([0.0, 1.0, 2.0], [1.0, 2.0, 1.5])
ax.set_rlabel_position(200.0)  # a ray no curve runs along
plt.close(fig)
```

**Don't**

```py
ax = fig.add_subplot(projection="polar")  # radial labels left on the default ray, under the curve
```

**Enforced by:** `scripts/check_figure_tick_clearance.py`, `make figure-tick-clearance`, `CI: Documentation figures up to date`

**Exceptions.** Fills, gridlines and tick marks are not counted. There is no exemption table.

<a id="f46"></a>
### F46. Place a hand-set label clear of tick labels, other text and strokes, in both languages

**Why.** A label placed by hand can land on a tick label ('$U$ = 1.0 dB' over the '90' of its axis), on another label (two notes apart in English, run together in Spanish), or under a stroke (a lane heading crossed by the impulse it names; a note struck through by the spine it runs past) while every other gate stays green.

**Do**

```python
fig, ax = plt.subplots()
ax.plot([0, 10], [0, 10])
ax.text(0.97, 0.05, "Banda de octava", transform=ax.transAxes, ha="right")
ax.axvline(5.0, ymin=0.0, ymax=0.8)  # stops short of the words above it
plt.close(fig)
```

**Don't**

```py
ax.text(0.85, 0.05, "Banda de octava", transform=ax.transAxes)  # runs out through the right spine in Spanish
```

**Enforced by:** `scripts/check_figure_text_clearance.py`, `make figure-text-clearance`, `CI: Documentation figures up to date`

**Exceptions.** `EXEMPTIONS` of the script, keyed by drawing with its reason, is empty; a stale entry fails. Gridlines, tick marks, legend frames, chips and an annotation's own leader are not counted as strokes. A fill or a chip under a label is its backing; one painted after the label over its letters (the chip of a later label, a legend plate) is counted. A label drawn with a halo (a path effect) is read as its string, and the halo hides what is painted before it, not what is painted after.

<a id="f47"></a>
### F47. Place a legend or a label's chip where it covers no plotted point, in English and in Spanish

**Why.** A legend's width is set by its longest label and a Spanish label is routinely half again as long, so a box that clears the data in one language covers it in the other; a point under an opaque legend is a datum the reader no longer has. The chip of a label is the same kind of plate: the image-source clip put its "source" chip over the first image of the source, and the two-room clip its caption chip over two microphones of the sphere.

**Do**

```python
fig, ax = plt.subplots()
ax.plot([1, 2, 3], [3, 2, 1], label="Nivel medido")
ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0))  # beside the axes
plt.close(fig)
```

**Don't**

```py
ax.legend(loc="lower right")  # over the last markers once the labels are Spanish
```

**Enforced by:** `scripts/check_figure_legends.py`, `make figure-legends`, `CI: Documentation figures up to date`

**Exceptions.** `EXEMPTIONS` in `scripts/check_figure_legends.py`, keyed by drawing with the reason it is a decision (a legend that is merely inconvenient to move does not belong); one entry, `true_peak_intersample` (a comb of identical grid ticks). Ratcheted both ways. A legend with `frameon=False` is not measured (its letters are the annotation check's business). A chip counts only over a point painted before it, and not when it is fainter than half opacity or filled with the point's own colour: a badge centred on the point it numbers stands in for it. A tick mark is the frame of the axes, not a plotted point, and is not counted.

<a id="f48"></a>
### F48. Shade a region so it clears CIEDE2000 10 against the page in both themes

**Why.** `alpha=0.10` of a mid-tone hue reads as a pale tint on the white page but collapses onto the near-black page of the dark theme; the staleness gate knows nothing about how a figure looks. A dE00 of 10 is where a difference is read at a glance, and a documentation figure is skimmed, not inspected.

**Do**

```python
fig, ax = plt.subplots()
ax.axvspan(500.0, 1000.0, color="C0", alpha=0.25)  # read on the white and the near-black page
plt.close(fig)
```

**Don't**

```py
ax.axvspan(f1, f2, color="tab:blue", alpha=0.10)  # invisible on the dark page
```

**Enforced by:** `scripts/check_figure_contrast.py`, `make figure-contrast`, `CI: Documentation figures up to date`

**Exceptions.** SVG only: raster figures (`_RASTER_FIGURES` in `scripts/figures/theme.py`) map color through the background-aware `_field_cmap` of `src/phonometry/_plot/common.py`. Regions below `MIN_AREA_FRACTION` of the axes are ignored. There is no exemption table.

<a id="f49"></a>
### F49. Keep every line legible on the dark page: 3:1 for hairlines, 2:1 for thicker strokes

**Why.** The contrast check measures filled regions, and a stroke is not a fill: the ISO 3745 microphone array shipped with its hemisphere in a half-opacity gray hairline that composited to 1.3:1 on the dark theme, present in the SVG and invisible to a reader.

**Do**

```python
fig, ax = plt.subplots()
ax.plot([0, 1], [0, 1], color="C0", linewidth=1.0)
plt.close(fig)
```

**Don't**

```py
ax.plot(x, y, color="#555555", alpha=0.5, linewidth=0.4)
```

**Enforced by:** `scripts/check_stroke_contrast.py`, `CI: Documentation figures up to date`

**Exceptions.** A hairline is a stroke under 0.6 pt. A stroke is read at the opacity it is painted with (its `stroke-opacity`, times the `opacity` matplotlib writes for a patch faded with `set_alpha`, times that of every group round it) against the page its drawing paints behind it: the axes or figure background (black for a dark matplotlib figure), a diagram's plate, else the site's dark ground. Grid and axis furniture is exempt by color (`SCAFFOLDING`: #555555, #e0e0e0, #b0b0b0) and the 3-D grid by group name (`grid3d`); strokes inside an axes covered by a filled contour or a mesh (`QuadContourSet`, `QuadMesh`) are read against that field, which `scripts/check_figure_contrast.py` judges. No other exemption.

<a id="f50"></a>
### F50. Color a fiche's bars by category with a legend; never rotate long tick labels

**Why.** On the vibration-exposure fiche (#298) long X labels rotated 45 degrees overlapped each other and the layout and squashed the chart.

**Do**

```text
one color per category + legend (ncol <= 3), X tick labels removed or
shortened, height reserved for the embedded chart
```

**Don't**

```text
ax.set_xticklabels(long_names, rotation=45)
```

**Enforced by:** review

## Animations

<a id="f51"></a>
### F51. Publish animation clips to phonometry-assets; never commit a clip to this repository

**Why.** A clip is binary and re-encoded whole whenever its drawing code changes, and every re-encode kept here stayed in the history every clone downloads. The render and publish procedure is in [CONTRIBUTING.md](../../CONTRIBUTING.md), with the rest of the generated media.

**Do**

```bash
make assets      # once: the checkout of phonometry-assets
make animations  # render, publish, and write assets.lock and scripts/animation_fingerprints.txt
git add assets.lock scripts/animation_fingerprints.txt
```

**Don't**

```text
git add .github/images/anim_reverberation.webm
```

**Enforced by:** `scripts/check_figures.py`, `scripts/check_animation_freshness.py`

<a id="f52"></a>
### F52. Re-render a clip whenever the code that draws it changes

**Why.** CI regenerates figures but cannot regenerate clips (FDTD plus four video encodes each), so a clip keeps whatever it was drawn with: after the Spanish minus-sign repair, twelve clips kept an ASCII hyphen in their Spanish tick labels for months with every gate green. Each render stamps a fingerprint of the code that drew it, and the guard recomputes it; a render also writes the poster still and the two English GIFs, and the guard fails when any of the ten files is missing from jmrplens/phonometry-assets at the commit `assets.lock` records.

**Do**

```bash
# with the ffmpeg build the clips are calibrated on, as CONTRIBUTING.md shows
ffmpeg_dir="$(make -s clip-ffmpeg)" && PATH="$ffmpeg_dir:$PATH" make animations ANIM=anim_epnl_flyover
```

**Don't**

```text
Change a scene in scripts/figures/ (or a phonometry._plot helper it draws with) and commit without re-rendering the clip: the fingerprint next to the clip no longer matches.
```

**Enforced by:** `scripts/check_animation_freshness.py`, `make animation-freshness`

**Exceptions.** The fingerprint (`scripts/animation_fingerprint.py`) follows a clip's code through `scripts/figures`, through the drawing helpers of `phonometry._plot` it calls (the colours of a fill or a quiet line, the frequency axis, the dark field map) and through the encode path of `phonometry.io`, and stops at the rest of the library: a change to the physics moves the static figures, where `scripts/check_figures.py` catches it. A clip that steps an FDTD engine is tied instead to what the engines compute, through their golden digests (`engine-digests.json`, which one CI job measures and checks, and `make engine-digests RUN=<run id>` takes from it): rewording an engine moves no clip, and a change that moves the engines' numbers moves the digests and makes every field clip stale. Each line of the manifest also names the encoder that wrote the clip's WebM (`av1_nvenc` or `libsvtav1`), and `make clip-codecs` (`scripts/check_clip_codecs.py`) reads every published WebM and checks that it is AV1 from that encoder; CI never fetches a clip, so it runs where the clips are, after a render and before publishing.

<a id="f53"></a>
### F53. Embed an animation lazily, with its space reserved

**Why.** Decided when the v2 animation style was approved (2026-07-15): always deferred, with its space reserved so the layout does not shift while it loads.

**Do**

```markdown
<img src="https://.../clip.gif" loading="lazy" width="960" height="540" alt="...">
```

**Don't**

```markdown
![clip](https://.../clip.gif)
```

**Enforced by:** review

**Exceptions.** On the site: `<video>` with `preload="none"`, a `poster` and `width`/`height` (or an aspect ratio); in the GitHub docs: `<img>`/`<picture>` with `loading="lazy"` and explicit `width`/`height`.

## Records in a notebook

<a id="f54"></a>
### F54. Let every public record inherit `RichDisplay`, and give it no display method of its own

**Why.** Jupyter, VS Code, Colab and IPython display the last expression whole, and a dataclass with no display of its own is its repr: every field, every array printed in full up to a thousand values, pages of numbers. Before the mechanism all 673 public records did this.

**Do**

```python
from dataclasses import dataclass

from phonometry._internal.display import RichDisplay


@dataclass(frozen=True)
class RoomVerdict(RichDisplay):
    volume_m3: float
    passes: bool
```

**Don't**

```py
@dataclass(frozen=True)
class RoomVerdict:
    volume_m3: float
    def _repr_html_(self):   # its own display
        ...
```

**Enforced by:** `scripts/check_record_display.py`, `make record-display`, `CI: Every public record shows itself as a table in a notebook`, `tests/test_check_record_display.py::test_the_package_shows_every_public_record_as_a_table`, `scripts/check_notebook.py`, `CI: phonometry runs in a notebook kernel`

**Exceptions.** A record that can hold an array has it already through `OwnsArrays`. A private record that cannot take a base (a named tuple) defines `_repr_html_` and `_repr_pretty_` as calls to `record_html` and `record_pretty`. `EXEMPT` of the script takes a record that must display otherwise, with its reason (empty). The display reads the fields and, on a verdict, `passes`, so keep `passes` cheap; `repr()` and `print()` keep the dataclass's.

<a id="f55"></a>
### F55. Let a record field's unit read from its name, or declare it in `_display_units`

**Why.** A renamed bare field (`frequencies`, `insertion_loss`) would have lost the unit its old suffix showed. A bare level shows dB, a loudness level phon, and a field whose name misreads its number declares `_display_units`.

**Do**

```python
from collections.abc import Mapping
from types import MappingProxyType
from typing import ClassVar


@dataclass(frozen=True)
class ReflectionResult(RichDisplay):
    _display_units: ClassVar[Mapping[str, str]] = MappingProxyType({"reflection_index": ""})  # a ratio of energies
    reflection_index: float
    distance_m: float
```

**Don't**

```py
@dataclass(frozen=True)
class ReflectionResult(RichDisplay):
    reflection_index: float   # shown in dB by the head-noun reading
```

**Enforced by:** `tests/test_record_display.py::test_every_unit_a_record_names_is_needed_and_shown`, `tests/test_record_display.py::test_no_public_field_that_holds_no_number_is_shown_in_a_unit`, `tests/test_record_display.py::test_every_public_field_ending_in_a_unit_shows_it`, `tests/test_record_display.py::test_a_number_its_name_misreads_shows_its_own_unit`

**Exceptions.** An entry must name a real field and say something the name does not. A truth value, a text, a complex factor or a nested record shows no unit. A bare axis name has its one unit (frequencies in Hz, levels in dB, times in s); a loudness level is in phon. A name that ends in a symbol's subscript rather than a unit goes in `_SYMBOL_NAMES` of `tests/test_record_display.py` (`a_atm`). A unit suffix the display does not spell yet goes in `_UNITS` of `phonometry._internal.display`, or a public field that ends in it shows no unit and `test_every_public_field_ending_in_a_unit_shows_it` fails.

## Catalogues

<a id="f56"></a>
### F56. Register every `PUBLISHED_` catalogue in the catalogues page generator

**Why.** A catalogue nobody can see is a catalogue nobody has. When the guard first ran it found six catalogues (two of them years old) that were written, tested and in the API reference, yet invisible on /reference/catalogues/, the only place a reader who does not read Python meets the rows.

**Do**

```text
scripts/generate_catalogue_data.py names every PUBLISHED_ mapping (PUBLISHED_SOLIDS ...) with its columns,
and a catalogue page shows it in both languages
```

**Don't**

```text
a new PUBLISHED_RESILIENT_LAYERS in src, absent from scripts/generate_catalogue_data.py
```

**Enforced by:** `scripts/check_published_catalogues_reach_the_page.py`, `make published-catalogues`, `CI: Every published value names its page`, `site/src/lib/catalogue-pages.ts`

**Exceptions.** A mapping deliberately kept off the page goes in `EXEMPT` with the reason, and only when showing it would mislead, never because registering it is work (empty). Registering means: the generator names it with its columns, a page under `site/src/content/docs/reference/catalogues/` renders it in both languages (a new catalogue gets a page of its own, listed in `catalogueSlugs` in `site/src/data/topics.mjs`; a table that belongs beside another, as the absorption areas belong beside the absorption coefficients, joins that page), and its key joins the union in `site/src/components/Catalogues.astro`. The guard sees only the generator; the site build fails on the rest, a catalogue the generator writes that no page of a language renders and a page under `reference/catalogues/` missing from `catalogueSlugs`.

## Errata entries

<a id="f57"></a>
### F57. Cite an errata entry's page by document, edition, PDF page and printed folio

**Why.** Text extraction silently deletes glyphs (most cited documents emit no radical at all), and an entry drafted from extracted text once accused an author of printing 2/(3 pi) where the page prints 2/(sqrt(3) pi). The entry states what the page prints, not how it was read ([P10](prose.md#p10)).

**Do**

```markdown
- **Evidence:** ... Verified on PDF page 31 (printed p. 25) of ISO 3744:2010.
```

**Don't**

```text
- **Evidence:** the extracted text of /home/me/iso9613.pdf reads ...
```

**Enforced by:** `scripts/check_errata_evidence.py`, `CI: Errata entries cite their page`

**Exceptions.** Cite the document, never a file path. A claimed ratio within 0.5 % of a familiar irrational (sqrt 2, sqrt 3, pi, 2 pi, ln 2) or a small integer is the signature of a lost glyph, and clears only when the same entry cites the page it read (`--ratios`). `PAGE_CITATION_ALLOWLIST` of the script holds, by entry title with its reason, the entries filed before the page rule or whose claim is not a reading of characters (24); it only shrinks.

<a id="f58"></a>
### F58. Quote a printed value, its symbols and its separator exactly as the source prints them

**Why.** The registry cites what is printed: if the standard prints a comma, the entry keeps the comma, though the prose is English (requested 2026-08-04), and so does any prose of ours that quotes a printed value. The site renders KaTeX and docs/ is a flat mirror, so the LaTeX has to work in both.

**Do**

```markdown
ISO 9613-1 prints $a = 2{,}2560 \times 10^{-5}$ per meter; the bandwidth of 20 kHz ...
```

**Don't**

```markdown
ISO 9613-1 prints a = 2.2560 × 10⁻⁵ m⁻¹ (`a = 2.256e-5`)
```

**Enforced by:** review

**Exceptions.** The decimal separator is the cited source's: a comma for ISO, EN, IEC, DIN, ECMA, UNE, the EU Official Journal and the BOE, a point for English books and papers; look at the page before assuming. A decimal comma in math is `{,}`; display math sits on its own lines; no Unicode superscripts, no `3.2e5`, no formula in backticks; a quantity in prose stays prose (`20 kHz`). The English wording is authoritative; the Spanish edition keeps the same quoted print. The errata registers are the case review reads first; a guide or a docstring that quotes a printed value follows the same rule ([P9](prose.md#p9)), while a value the library computes is written in its page's language.

<a id="f59"></a>
### F59. Add or remove an errata entry in docs/ERRATA.md and docs/ERRATA.es.md together

**Why.** The Spanish register is translated entry for entry, and the evidence pages are generated from both.

**Do**

```text
One commit adds the entry to docs/ERRATA.md and its translation, same position, same document named in the heading, to docs/ERRATA.es.md.
```

**Don't**

```text
A commit that adds the English entry and leaves the Spanish register for later.
```

**Enforced by:** `make site-reports`, `CI: Generated evidence pages up to date`

## Clip frames

<a id="f60"></a>
### F60. Hold every frame of a clip to the figure gates before it is encoded

**Why.** The figure gates read the committed SVGs, and a clip has none: its frames exist only while the encoder pulls them. The EPNL flyover clip shipped its "microphone" label struck through by the ground line in every frame, and it was found by eye. A render now draws each frame as the SVG the figures are saved as, in the order the animation draws it, and holds it to the gates that apply to a frame: text and tick clearance, legends and chips over a datum, and the tick labels of an axis on the light frames in both languages, the contrast of a fill on every frame and of a stroke on the dark ones, the minus sign everywhere and the decimal comma in Spanish. A label drawn with a halo is read like any other. The four variants of a clip are inspected before any is encoded, so a finding in one, the dark page or the Spanish text alone, stops the whole clip; it names the clip, the variant, the frame and the finding, and nothing is encoded, stamped or published.

**Do**

```bash
make animation-audit ANIM=anim_epnl_flyover   # every frame of its four variants, no video
# the render audits first, with the ffmpeg build the clips are calibrated on
ffmpeg_dir="$(make -s clip-ffmpeg)" && PATH="$ffmpeg_dir:$PATH" make animations ANIM=anim_epnl_flyover
```

**Don't**

```text
Place a clip's label by eye on the poster still and publish the clip: the
frames between the first and the poster are never looked at.
```

**Enforced by:** `scripts/clip_frame_audit.py`, `make animation-audit`, `tests/test_clip_frame_audit.py`

**Exceptions.** Every frame is inspected, none sampled: run over every frame of the 43 clips as they were drawn before the audit, 24 of the 314 runs of a finding held for a single frame (in six clips), which any stride would have let through. A finding that is a decision goes in the gate's own exemption table, with the reason, keyed for a clip the way that table keys a figure: `check_figure_text_clearance.EXEMPTIONS` by the drawing with its language suffix (`anim_epnl_flyover`, `anim_epnl_flyover_es`) or `drawing: text`; `check_figure_legends.EXEMPTIONS` by the clip alone; `check_figure_minus_sign.ALLOWED` and `check_figure_decimal_point.ALLOWED` by `clip: text`, with no language or theme suffix. The figure gates leave such an entry alone, and the audit-only run fails it once no frame fires it. No CI job runs the audit, because CI cannot render a clip: the freshness check ([F52](#f52)) fails a change to a clip's drawing code, in `scripts/figures`, in the `phonometry._plot` helpers it draws with or in the encode path of `phonometry.io`, until the clip is rendered again, and the render runs the audit. A change to the audit or to a checker moves no fingerprint, so after one, `make animation-audit` over every clip shows whether the published clips still pass.

## Clip fields

<a id="f61"></a>
### F61. Step a clip's field where the registry puts it, and keep it on that device between captures

**Why.** A scene steps `phonometry.simulation` on the device its clip is measured to want (`scripts/clip_placement.py`, `figures.registry._ANIM_DEVICES`), which is a GPU for the large fields. Code that works on NumPy breaks there: CuPy refuses a host array added into a device field, and a field read to the host on every step costs a copy and a sync per step, which can cost more than the step.

**Do**

```python
import clip_placement
import numpy as np
from figures.fields._core import _host

from phonometry.simulation import FDTD2D

sim = FDTD2D(..., compute=clip_placement.compute_for("anim_fdtd_open_end"))
xp = sim._backend.xp
row, omega, phase, beta, steps, every = 40, 2.0 * np.pi * 500.0, 0.0, 0.98, 600, 6
taper = sim._backend.asarray(np.hanning(sim.p.shape[1]))   # once, before the loop
ms = sim._backend.zeros(tuple(sim.p.shape))
frames = []
for i in range(steps):
    sim.step()
    sim.vy[row] += taper * xp.sin(omega * sim.time - phase)
    ms = beta * ms + (1.0 - beta) * sim.p**2
    if (i + 1) % every == 0:
        frames.append(_host(sim, sim.p[::2, ::2]))
```

**Don't**

```py
sim = FDTD2D(...)                     # no compute=: PHONOMETRY_COMPUTE decides
ms = np.zeros_like(sim.p)
for i in range(steps):
    sim.step()
    sim.vy[row] += np.hanning(sim.p.shape[1]) * np.sin(omega * sim.time - phase)
    level = float(sim.p[iy, ix])
    frames.append(sim.p[::2, ::2].astype(np.float32))
```

**Enforced by:** `tests/test_clip_scenes_on_devices.py`, `tests/test_clip_placement.py`

**Exceptions.** Code before the loop builds maps and drive vectors with any NumPy call; they go to the device once, through the engine's `asarray`. A capture brings its frame to the host with `_host`; a reduction over every step stays in the engine's namespace and crosses once, after the loop. A clip's device is measured, never guessed: it is the GPU only where the field was measured to save a fifth or more of its time there and to stay close to its NumPy field, output by output, with the NumPy reference run in the same container image as the GPU run (NumPy's float32 `log10` changed bits between 2.5.3 and 2.5.4 on the same CPU). Every output keeps its NaN and infinities in the same places; a float64 output stays within 1e-9 of its peak; a float32 output, a frame among them, within 1e-9 of its peak or within one float32 step (one unit in the last place) of every value, since a bound below a float32 value's own resolution would demand bit identity, and neither result is more accurate than the other. The fields step in float64 on every device.

## Install commands

<a id="f62"></a>
### F62. Quote the extras of every install command

**Why.** zsh, the default shell on macOS, reads the brackets of an extras requirement as a glob and stops with "no matches found" before pip runs. A command copied from a page, a docstring, a message the library raises or the README must run as written in every shell.

**Do**

```bash
pip install "phonometry[torch]"
pip install -e ".[full]"
pip install torch --index-url https://download.pytorch.org/whl/cpu   # a CPU-only Linux machine, first
```

**Don't**

```bash
pip install phonometry[torch]   # zsh: no matches found: phonometry[torch]
```

**Enforced by:** `scripts/check_quoted_extras.py`, `CI: Every install command quotes its extras`, `tests/test_check_quoted_extras.py`

**Exceptions.** A line that shows zsh's own "no matches found" is the failure shown on purpose. Tests are not published and are not read. A sentence that names an extra without installing it (the `[torch]` extra) is not a command. A requirement is one word of the command, so a quote that opens it quotes all of it, a path or a variable inside included.

## Page descriptions

<a id="f63"></a>
### F63. Give every page a description of 160 characters or fewer that no other page of its language repeats

**Why.** The frontmatter `description` is the line a search result shows under the title, and no reader of the page ever sees it. 461 of the 996 published pages carried one longer than 160 characters: Bing's tools flag "Meta Description too long or too short" (160 is the figure its older guidelines stated), Google cuts the snippet wherever it needs to, so the reader gets half a sentence, and Bing's Recommendations count "Too many pages with identical meta descriptions". A page with no description inherits the 319-character site description and fails as too long, and as a duplicate once a second page of its language forgets too. An API page takes its description from the opening of the module docstring ([D1](docstrings.md#d1)): the lead paragraph when it fits in 155 characters, otherwise its opening sentence, and `make api-docs` stops on a module where neither fits rather than cut one mid-sentence.

**Do**

```yaml
description: "Airport noise by ECAC Doc 29: the noise-power-distance engine, per-segment corrections of a single event and SEL contours on a ground grid."
```

**Don't**

```yaml
description: "The ECAC Doc 29 airport-noise method: the noise-power-distance engine, the per-segment corrections of the single-event calculation (impedance, lateral attenuation, engine installation, duration, noise fraction, start-of-roll directivity) and the ground-grid SEL contour."
```

**Enforced by:** `site/scripts/check-descriptions.mjs`, `CI: Check every page has a short meta description of its own`, `site/scripts/check-descriptions.test.mjs`, `CI: Test the build checks on small builds made to fail them`, `tests/test_api_docs_generator.py::test_every_api_page_has_a_description_short_enough_to_show_whole`

**Exceptions.** The Spanish API pages carry the English description of their twin and name that twin canonical (`site/src/lib/fallback-routes.mjs`), and the redirect stubs and the error page are not pages a search engine indexes; the check skips all three. A Spanish description is written for its page, not cut down from the English one, and the length counts characters, not bytes.

## Page size

<a id="f64"></a>
### F64. Keep every built page under 1 800 000 bytes of HTML

**Why.** Googlebot fetches the first 2 MB of a page, counted on the uncompressed HTML, and indexes nothing past it ([Googlebot](https://developers.google.com/search/docs/crawling-indexing/googlebot)). No console reports the cut: the page shows as indexed and its tail is simply never searchable. The published catalogues reached 4.7 MB in English and 5.2 MB in Spanish on one page, so about two thirds of their rows never reached the index, and the errata registry (4.9 MB) and the conformance report (2.5 MB) were past the limit as well. The cap is a tenth under 2 000 000 bytes, so a page is caught while a table can still grow by some rows. A page that outgrows it is split where its readers already think of it as parts (one page per catalogue, one per document family of the errata), or loses the markup every row repeats (a scoped class on each cell, a copy of the row's text, a per-cell attribute the client can work out from the column).

**Do**

```text
one page per catalogue under /reference/catalogues/, each well under 1 MB,
and a row that carries only what its position does not say
```

**Don't**

```text
every catalogue on one page, each of its 25 800 cells carrying a scoped
class, its column's heading and its unit
```

**Enforced by:** `site/scripts/check-page-size.mjs`, `CI: Check every page fits in what a search engine reads`

**Exceptions.** None. The redirect stubs and the error page are small and are counted like any other file; a page that cannot be split or slimmed below the cap is a design question to settle before it is published, not an entry here.
