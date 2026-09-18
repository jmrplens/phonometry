#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Generate README_PYPI.md, the PyPI long description, from README.md.

Two rewrites, for two things a package page does that a repository page
does not.

**Images.** PyPI's readme renderer strips ``<picture>``/``<source>``
elements, so the GitHub README's theme-aware images would degrade there.
Each ``<picture>`` element collapses down to its plain light-theme ``<img>``
fallback, and animated GIFs are swapped for their static ``_poster.jpg``
stills so the package page stays light to load.

**Links.** A PyPI description is frozen at upload and can never be edited
again, while ``main`` keeps moving under it. Every ``blob/main`` and
``raw.githubusercontent.com/.../main`` URL the README carries therefore
resolves against a tree that no longer matches the release the reader is
looking at, and the whole guide map rots the first time the documentation
is reorganised: the description published with 3.3.0 pointed at a flat
``docs/`` layout and 34 of its 38 repository links were dead within one
release. So the links are pinned here, at generation time, to ``blob/v``
plus the contents of the repository-root ``VERSION`` file: the published
page points at the tree it was published from, and stays right forever
because that tree never changes again.

That pin is right on the page PyPI serves and wrong on the copy committed
here, which is a build input rather than a page to read from ``main``. The
release workflow cuts the tag from the commit that lands the ``VERSION`` bump,
so the committed file is always in one of two states:

* **At the release commit, and only there.** ``VERSION`` has just been bumped,
  the pinned tag does not exist yet, and the paths behind it are right because
  this tree is what the tag is about to point at. The URLs 404 for the minutes
  it takes the workflow to create it.
* **For the whole rest of the cycle**, which is where ``main`` sits almost
  always. ``VERSION`` still names the last release, so the pinned tag exists
  and its tree is older than the README the page was generated from, and every
  path added or moved since that release 404s. ``v3.3.0`` predates the
  documentation reorganisation: measured against ``git ls-tree -r v3.3.0``, 86
  of the 95 paths on today's page are absent from it, the banner at the top of
  the page included.

Neither state ever reaches PyPI, because the page is regenerated at the
release commit and the tag is cut from that same commit. That is the property
the packaging tests hold, and it is why they resolve the pinned paths against
**this checkout** rather than over the network: the working tree is the tree
the tag will be cut from, so it answers the only question that decides whether
the published page is right. It says nothing about the tag already on the
remote, and the second state above is therefore ungated by design. Anything
that checks these URLs over HTTP has to skip this file in both states.

Run through ``make pypi-readme``; the packaging tests fail if the committed
file drifts from the README or from ``VERSION``.
"""

from __future__ import annotations

import pathlib
import re

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_HEADER = (
    "<!-- AUTO-GENERATED FILE - DO NOT EDIT BY HAND.\n"
    "  PyPI long description derived from README.md by\n"
    "  scripts/generate_pypi_readme.py (make pypi-readme): every picture\n"
    "  element collapses to its light-theme img fallback and animated\n"
    "  clips to their poster stills, because PyPI's readme renderer\n"
    "  strips the picture and source tags, and every link into this\n"
    "  repository is pinned to the release tag, because a published\n"
    "  description is frozen while main keeps moving. Edit README.md\n"
    "  instead, and follow its links rather than these: between\n"
    "  releases the pin names the last release, whose tree predates\n"
    "  these paths, so they do not resolve from main. -->\n\n"
)

_PICTURE = re.compile(r"<picture>.*?</picture>", re.DOTALL)
_IMG = re.compile(r"<img\b[^>]*>", re.DOTALL)

#: This repository, spelled once so the pattern below cannot drift from it.
_SLUG = "jmrplens/phonometry"

#: A URL into **this** repository at the ``main`` branch, in the forms the
#: README uses: ``github.com/<slug>/blob/main/...`` for a file rendered on
#: GitHub, ``github.com/<slug>/tree/main/...`` for a directory, and
#: ``raw.githubusercontent.com/<slug>/main/...`` for an image served raw.
#: Group 1 is everything up to and including the ref position, so
#: substituting the ref leaves the rest of the URL untouched.
#:
#: The owner and repository are matched literally rather than as wildcards.
#: A wildcard reads as harmless generality and is not: it would rewrite a
#: link to somebody else's repository to a tag of *ours*, which does not
#: exist over there, turning a working link into a 404 in the very file this
#: script exists to keep from rotting. The README has no third-party
#: ``main`` links today, so this is a guard on the next one added rather
#: than a fix to a live break.
_MAIN_REF = re.compile(
    rf"(https://github\.com/{_SLUG}/(?:blob|tree)/"
    rf"|https://raw\.githubusercontent\.com/{_SLUG}/)main/"
)

#: The animation posters are served from the assets repository (see
#: ``scripts/assets_dir.py``), which has no release tags: its ``main`` moves
#: whenever a clip is re-rendered. What does not move is the commit
#: ``assets.lock`` records, which is exactly the one the release's clips were
#: rendered into, so the PyPI page pins to that commit and keeps the poster it
#: was published with, the way it keeps every other link.
_ASSETS_MAIN_REF = re.compile(
    r"(https://raw\.githubusercontent\.com/jmrplens/phonometry-assets/)main/"
)


def version(root: pathlib.Path = _ROOT) -> str:
    """The version being published, from the repository-root VERSION file."""
    return (root / "VERSION").read_text(encoding="utf-8").strip()


def pin_to_tag(text: str, tag: str, assets_commit: str) -> str:
    """Point every ``main`` URL at something that will not move.

    :param text: Markdown carrying the README's absolute repository links.
    :param tag: The git tag to resolve links into this repository against,
        for example ``v3.3.0``.
    :param assets_commit: The commit of the assets repository to resolve the
        poster links against, from ``assets.lock``.
    :return: The same markdown with the branch refs replaced.
    """
    pinned = _MAIN_REF.sub(rf"\g<1>{tag}/", text)
    return _ASSETS_MAIN_REF.sub(rf"\g<1>{assets_commit}/", pinned)


def assets_commit(root: pathlib.Path = _ROOT) -> str:
    """The assets commit the release's clips live in, from ``assets.lock``."""
    return (root / "assets.lock").read_text(encoding="utf-8").strip()


def pypi_readme(readme: str, tag: str, assets_commit: str) -> str:
    """The PyPI long description derived from *readme* (README.md text).

    :param readme: The GitHub README's text.
    :param tag: Tag the repository links are pinned to, for example
        ``v3.3.0``.
    :param assets_commit: Commit of the assets repository the poster links
        are pinned to.
    """

    def collapse(match: re.Match[str]) -> str:
        imgs = _IMG.findall(match.group(0))
        if len(imgs) != 1:
            msg = (
                "expected exactly one <img> fallback inside each <picture> "
                "element of README.md"
            )
            raise ValueError(msg)
        img = imgs[0].replace(' loading="lazy"', "")
        swapped = re.sub(r'(src="[^"]+)\.gif"', r'\1_poster.jpg"', img)
        if swapped != img:
            # The still is no longer an animation; fix the alt prefix.
            swapped = re.sub(
                r'alt="Animation: (.)', lambda m: 'alt="' + m.group(1).upper(), swapped
            )
        return swapped

    return pin_to_tag(_HEADER + _PICTURE.sub(collapse, readme), tag, assets_commit)


def main() -> None:
    """Rewrite README_PYPI.md next to the repository README."""
    readme = (_ROOT / "README.md").read_text(encoding="utf-8")
    tag = f"v{version()}"
    assets = assets_commit()
    out = _ROOT / "README_PYPI.md"
    out.write_text(pypi_readme(readme, tag, assets), encoding="utf-8")
    print(
        f"wrote {out} (repository links pinned to {tag}, posters to "
        f"phonometry-assets@{assets[:12]})"
    )


if __name__ == "__main__":
    main()
