#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The site's targets, as the Python generators read them.

``scripts/site_target.py`` reads ``site/src/data/site-targets.json``, the file
``site/src/data/site.mjs`` reads for the build, so the base path the API
reference, the errata pages and the llms files write is the one the site is
built under (``site/scripts/site-target.test.mjs`` holds the JavaScript side
to the same file).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_api_docs
import generate_site_reports
import site_target


def _write(path: Path, table: object) -> Path:
    path.write_text(json.dumps(table), encoding="utf-8")
    return path


def test_every_target_is_read_as_the_file_writes_it() -> None:
    table = json.loads(site_target.TARGETS.read_text(encoding="utf-8"))
    assert list(site_target.targets()) == list(table["targets"])
    for name, entry in table["targets"].items():
        assert site_target.site_url(name) == entry["siteUrl"]
        assert site_target.base_path(name) == entry["basePath"]
    default = table["default"]
    for unset in (None, ""):
        assert site_target.target(unset) == site_target.target(default)


def test_a_name_that_is_no_target_is_refused_as_the_build_refuses_it() -> None:
    with pytest.raises(
        ValueError, match=r"PHONOMETRY_SITE=phonometry\.org is not one of"
    ):
        site_target.target("phonometry.org")


def test_the_generators_write_the_base_the_default_build_serves() -> None:
    """The API reference and the errata pages link under the build's base path.

    They are committed once for every build, so every target serves its pages
    under that one base: a target under another would find every link broken.
    """
    base = site_target.base_path(None)
    assert generate_api_docs.SITE_BASE == base
    assert generate_api_docs.API_BASE == f"{base}/reference/api"
    assert generate_site_reports.SITE_BASE == base
    assert {target.base_path for target in site_target.targets().values()} == {base}


@pytest.mark.parametrize(
    ("entry", "problem"),
    [
        pytest.param(
            {"siteUrl": "https://example.org", "basePath": "/docs/"},
            "basePath of x is neither empty nor /segment",
            id="a base path ending in a slash",
        ),
        pytest.param(
            {"siteUrl": "https://example.org", "basePath": "docs"},
            "basePath of x is neither empty nor /segment",
            id="a base path without its leading slash",
        ),
        pytest.param(
            {"siteUrl": "https://example.org/docs", "basePath": ""},
            "siteUrl of x is not an https origin",
            id="an origin with a path",
        ),
        pytest.param(
            {"siteUrl": "http://example.org", "basePath": ""},
            "siteUrl of x is not an https origin",
            id="an origin without TLS",
        ),
        pytest.param(
            {"siteUrl": "https://example.org:8443", "basePath": ""},
            "siteUrl of x is not an https origin",
            id="an origin with a port, which site.mjs refuses too",
        ),
    ],
)
def test_a_target_of_the_wrong_shape_is_refused(
    tmp_path: Path, entry: dict[str, str], problem: str
) -> None:
    path = _write(
        tmp_path / "site-targets.json", {"default": "x", "targets": {"x": entry}}
    )
    with pytest.raises(ValueError, match=problem):
        site_target._table(path)


def test_a_default_that_names_no_target_is_refused(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "site-targets.json",
        {
            "default": "y",
            "targets": {"x": {"siteUrl": "https://x.org", "basePath": ""}},
        },
    )
    with pytest.raises(ValueError, match=r"the default y is not one of x"):
        site_target._table(path)


def test_the_root_is_a_base_path(tmp_path: Path) -> None:
    """An empty base path, the site at the root, is a target like any other."""
    path = _write(
        tmp_path / "site-targets.json",
        {
            "default": "x",
            "targets": {"x": {"siteUrl": "https://x.org", "basePath": ""}},
        },
    )
    assert site_target._table(path).targets["x"] == site_target.Target(
        "https://x.org", ""
    )
