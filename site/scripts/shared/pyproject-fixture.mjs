// The `[project]` lines the site's tests read pyproject.toml through.
//
// Two shapes of the same table: one that gives every requirement one floor,
// as pyproject.toml did before each Python had its own, and the lines copied
// from pyproject.toml, which give each Python a floor of its own behind a
// `python_version` marker. The reader and the structured-data check are
// built for both. The tests of src/lib/pyproject.mjs compare their reading
// with Python's own, and the tests of the requirements check hold a sentence
// to each, so both suites test the same lines.
//
// Nothing here imports a package, nor do the reader and the check these lines
// are handed to.

/**
 * A `[project]` table that gives every requirement one floor and no marker, as
 * pyproject.toml did before each Python had a floor of its own.
 */
export const ONE_FLOOR = `[project]
name = "phonometry"
dynamic = ["version"]
authors = [
  { name="José Manuel Requena Plens", email="mail@jmrp.io" },
]
requires-python = ">=3.12"
dependencies = [
    "numpy>=2.0.2",
    "scipy>=1.14.0",
]

[project.optional-dependencies]
perf = ["numba>=0.60.0"]
plot = ["matplotlib>=3.10.7"]
report = ["reportlab>=4.0.4", "svglib>=0.9.0"]
# The base install already reads the whole linear WAV family (PCM, float,
# EXTENSIBLE, BWF, RF64) through scipy; the extra adds the remaining
# containers and codecs (FLAC, AIFF, Ogg/Opus, MP3, compressed WAV) via
# python-soundfile, whose wheel bundles libsndfile (LGPL-2.1, dynamically
# linked).
audio = ["soundfile>=0.12.0"]
torch = ["torch>=2.3.0", "array-api-compat>=1.5.1"]
full = ["numba>=0.60.0", "matplotlib>=3.10.7", "reportlab>=4.0.4", "svglib>=0.9.0", "soundfile>=0.12.0"]

[project.urls]
"Homepage" = "https://docs.jmrp.io/phonometry/"
`;

/**
 * The `[project]` lines the site reads, copied from pyproject.toml: a floor of
 * its own for each Python behind \`python_version\` markers, and an exclusion
 * beside a floor.
 */
export const PER_PYTHON = `[project]
name = "phonometry"
requires-python = ">=3.12"
dependencies = [
    "numpy>=2.0.2; python_version<'3.13'",
    "numpy>=2.1.0; python_version=='3.13'",
    "numpy>=2.3.2; python_version>='3.14'",
    "scipy>=1.14.0; python_version<'3.13'",
    "scipy>=1.14.1; python_version=='3.13'",
    "scipy>=1.16.1; python_version>='3.14'",
]

[project.optional-dependencies]
perf = [
    "numba>=0.60.0; python_version<'3.13'",
    "numba>=0.61.0; python_version=='3.13'",
    "numba>=0.63.0; python_version>='3.14'",
]
plot = ["matplotlib>=3.10.7"]
report = ["reportlab>=4.3.0", "svglib>=0.9.1,!=1.4.0"]
audio = ["soundfile>=0.12.0"]
torch = [
    "torch>=2.3.0; python_version<'3.13'",
    "torch>=2.5.0; python_version=='3.13'",
    "torch>=2.9.0; python_version>='3.14'",
    "array-api-compat>=1.5.1",
]
full = [
    "numba>=0.60.0; python_version<'3.13'",
    "numba>=0.61.0; python_version=='3.13'",
    "numba>=0.63.0; python_version>='3.14'",
    "matplotlib>=3.10.7",
    "reportlab>=4.3.0",
    "svglib>=0.9.1,!=1.4.0",
    "soundfile>=0.12.0",
]
`;
