# Published catalogues: the baseline the fingerprint starts from

## What this folder contains

| File | Kind | Provenance |
| :--- | :--- | :--- |
| `baseline.json` | derived (the library's own output) | Every row of the 23 `PUBLISHED_*` mappings phonometry exported at commit `64deb4b1`, 1982 rows, dumped by `tests/catalogue_fingerprint.py`: each row as its fields, every float by its `repr`, one row per line. Fields that hold nothing are left out. |

Nothing here is copied from a document. The file is what the library built
from its own packaged tables (`src/phonometry/**/data/*.json` and the few
tables still written in Python) on the day it was taken, so it holds the
same transcriptions those tables hold, in the same words, and no more.

## Source and authorship

- The values are the library's transcriptions of the published tables each
  row cites in its `source` field; the books and papers themselves are
  listed on the bibliography page of the site (`site/src/content/docs/reference/bibliography.md`).
- The dump was written once with `tests/catalogue_fingerprint.py` and is
  never regenerated. A change that is meant to move a published cell is
  written as a step in that module instead, so that the file keeps saying
  what the catalogues held before the step and the step says what moved.

## Purpose and scope of use

`tests/test_published_catalogue_fingerprint.py` takes this baseline through
every listed step and asserts that the result is, field for field and digit
for digit, what the library builds today. It exists because the page
generator's `--check` only sees the numbers as the site prints them, and a
change in the last digit of a float, or a hedge moved from one field to
another, does not show there. The file is not part of the `phonometry`
package and is not installed with it.

Unlike the extracts elsewhere in `tests/data/`, this file **is covered by
this repository's MIT licence**, the same terms as the packaged tables it
was dumped from (`src/phonometry/**/data/*.json`), which the package already
distributes under that licence. What it takes from each cited work is the
transcribed numbers with the citation every row carries; no text, table
layout, figure or page of any work is reproduced, and nothing in it comes
from a file whose terms forbid redistribution.

## Removal policy

Removing the file removes the fingerprint and nothing else: the tests of
`tests/test_published_catalogue_fingerprint.py` that read it would have to
go with it, and every other test is independent of it.
