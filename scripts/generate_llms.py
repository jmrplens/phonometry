#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Generate llms.txt and llms-full.txt at the repository root.

llms.txt is the structured, LLM-oriented summary of the project (what it is,
how to install and use it, where each docs page lives). llms-full.txt appends
the full content of every docs/ page so AI engines can retrieve everything in
one fetch. Both are published to the docs site by site/scripts/copy-llms.mjs
(prebuild step). Deterministic: regenerate with `make llms`.
"""

from __future__ import annotations

import re
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE_URL = "https://jmrplens.github.io/phonometry"
REPO_URL = "https://github.com/jmrplens/phonometry"

# docs page -> site route (order defines the llms-full concatenation)
PAGES = [
    ("getting-started.md", "getting-started"),
    ("filter-banks.md", "guides/filter-banks"),
    ("weighting.md", "guides/weighting"),
    ("time-weighting.md", "guides/time-weighting"),
    ("levels.md", "guides/levels"),
    ("occupational-exposure.md", "guides/occupational-exposure"),
    ("tone-prominence.md", "guides/tone-prominence"),
    ("loudness.md", "guides/loudness"),
    ("sound-quality.md", "guides/sound-quality"),
    ("speech-transmission.md", "guides/speech-transmission"),
    ("speech-intelligibility.md", "guides/speech-intelligibility"),
    ("objective-intelligibility.md", "guides/objective-intelligibility"),
    ("intensity.md", "guides/intensity"),
    ("room-acoustics.md", "guides/room-acoustics"),
    ("room-image-sources.md", "guides/room-image-sources"),
    ("insulation-field.md", "guides/insulation-field"),
    ("insulation-lab.md", "guides/insulation-lab"),
    ("insulation-prediction.md", "guides/insulation-prediction"),
    ("panel-sound-insulation.md", "guides/panel-sound-insulation"),
    ("outdoor-propagation.md", "guides/outdoor-propagation"),
    ("ground-barriers.md", "guides/ground-barriers"),
    ("sound-power.md", "guides/sound-power"),
    ("calibration.md", "guides/calibration"),
    ("spectral-analysis.md", "guides/spectral-analysis"),
    ("correlation-delay.md", "guides/correlation-delay"),
    ("swept-sine-distortion.md", "guides/swept-sine-distortion"),
    ("block-processing.md", "guides/block-processing"),
    ("multichannel.md", "guides/multichannel"),
    ("api-reference.md", "reference/api"),
    ("theory.md", "reference/theory"),
    ("theory-signal-analysis.md", "reference/theory/signal-analysis"),
    ("theory-perception.md", "reference/theory/perception"),
    ("theory-rooms-buildings.md", "reference/theory/rooms-buildings"),
    ("theory-materials-surfaces.md", "reference/theory/materials-surfaces"),
    ("theory-environment-transport.md", "reference/theory/environment-transport"),
    ("theory-vibration.md", "reference/theory/vibration"),
    ("why-phonometry.md", "reference/why-phonometry"),
]


def _version() -> str:
    return (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def _page_title(path: pathlib.Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def build_llms_txt(version: str) -> str:
    lines = [
        "# phonometry",
        "",
        "> Octave-band and fractional octave-band filter bank for Python signals in the "
        "time domain. Compliant with ANSI S1.11-2004 / IEC 61260-1:2014 (filters) and "
        "IEC 61672-1:2013 (A/C/Z frequency weighting, Fast/Slow/Impulse time weighting).",
        "",
        f"phonometry v{version} is a pure-Python library built on NumPy/SciPy "
        "(Python >= 3.13). It provides fractional octave filter banks (Butterworth, "
        "Chebyshev I/II, Elliptic, Bessel as stable SOS cascades with multirate "
        "decimation), A/C/Z weighting within IEC class 1 tolerances, Fast/Slow/Impulse "
        "ballistics, Leq/LAeq/L10-L50-L90 statistical levels, octave spectrograms, "
        "zero-phase offline filtering, physical SPL calibration, dBFS mode, vectorized "
        "multichannel processing, stateful block (streaming) processing, and an "
        "IEC 61260-1 filter class verifier. Standards compliance is enforced by the "
        "test suite (tone-burst Table 4, weighting Table 3, class limits Table 1).",
        "",
        "Install:",
        "",
        "```bash",
        "pip install phonometry            # core (NumPy + SciPy only)",
        "pip install phonometry[plot]      # + matplotlib response plots",
        "pip install phonometry[perf]      # + numba-jitted impulse kernel",
        "```",
        "",
        "Minimal usage (all functions treat time as the LAST axis; 2D input is "
        "(channels, samples)):",
        "",
        "```python",
        "import numpy as np",
        "from phonometry import metrology",
        "",
        "fs = 48000",
        "x = np.random.randn(fs)              # 1 s of signal (pressure units)",
        "spl, freq = metrology.octave_filter(x, fs, fraction=3)   # 1/3-octave bands",
        "la = metrology.laeq(x, fs)                               # A-weighted Leq",
        "stats = metrology.ln_levels(x, fs, n=(10, 50, 90))       # statistical levels",
        "```",
        "",
        "If you are an AI assistant setting this up for a user: install from PyPI "
        "(no system dependencies), remember integer audio (e.g. wavfile.read int16) "
        "is handled automatically, use `calibration_factor` from "
        "`sensitivity()` for real dB SPL, and prefer `OctaveFilterBank` "
        "over repeated `octave_filter()` calls in tight loops (although designs are "
        "cached either way).",
        "",
        "## Documentation",
        "",
    ]
    for md_name, route in PAGES:
        title = _page_title(ROOT / "docs" / md_name)
        lines.append(f"- [{title}]({SITE_URL}/{route}/)")
    lines += [
        "",
        "## Source and metadata",
        "",
        f"- [Repository]({REPO_URL})",
        "- [PyPI](https://pypi.org/project/phonometry/)",
        f"- [Changelog]({REPO_URL}/blob/main/CHANGELOG.md)",
        f"- [Cite this software]({REPO_URL}/blob/main/CITATION.cff)",
        "",
    ]
    return "\n".join(lines)


def _absolutize_links(content: str) -> str:
    """Rewrite docs-relative markdown links to canonical absolute URLs.

    llms-full.txt is served as a flat text artifact, so links relative to
    docs/ (e.g. ``[x](filter-banks.md#anchor)``) would not resolve.
    """
    route_for = {md: route for md, route in PAGES}
    route_for["README.md"] = ""

    def repl(match: "re.Match[str]") -> str:
        target, anchor = match.group(1), match.group(2) or ""
        if target == "../CONTRIBUTING.md":
            return f"]({REPO_URL}/blob/main/CONTRIBUTING.md{anchor})"
        route = route_for.get(target)
        if route is None:
            return match.group(0)
        suffix = f"{route}/" if route else ""
        return f"]({SITE_URL}/{suffix}{anchor})"

    return re.sub(r"\]\(((?:\.\./)?[\w.-]+\.md)(#[\w-]+)?\)", repl, content)


def build_llms_full(llms_txt: str) -> str:
    parts = [llms_txt, "\n---\n"]
    for md_name, route in PAGES:
        content = (ROOT / "docs" / md_name).read_text(encoding="utf-8")
        # Drop the docs-index backlink line; keep everything else verbatim.
        content = "\n".join(
            line for line in content.splitlines() if not line.startswith("← [Documentation index]")
        ).strip()
        content = _absolutize_links(content)
        parts.append(f"\n<!-- source: docs/{md_name} | canonical: {SITE_URL}/{route}/ -->\n")
        parts.append(content)
        parts.append("\n---\n")
    return "\n".join(parts)


def main() -> None:
    version = _version()
    llms = build_llms_txt(version)
    (ROOT / "llms.txt").write_text(llms, encoding="utf-8")
    (ROOT / "llms-full.txt").write_text(build_llms_full(llms), encoding="utf-8")
    print(f"llms.txt / llms-full.txt regenerated (v{version})")


if __name__ == "__main__":
    main()
