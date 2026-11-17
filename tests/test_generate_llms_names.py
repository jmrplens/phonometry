#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A shard name the site has published keeps answering.

``llms.txt`` tells an agent which shard files to fetch, and the names are
copied into prompts, tools and indexes that are never refreshed. They used to
change as the site grew: an area past the budget of one fetch was cut into
``-1`` and ``-2`` parts and its own name answered 404 from the next deploy on.
Fourteen names went that way between the index of one week and the next, and
``llms-start.txt`` was about to follow. ``site/src/data/llms-shards.json``
records every name the site has published; a run writes each of them again,
an area published whole that comes to need parts keeps its name as the list
of its parts, an area published in parts is cut into at least as many, and a
name the run cannot write stops it unless the record redirects that name to a
file the run writes.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from llms_dump import Dump

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_llms as llms

if TYPE_CHECKING:
    from guard_caches import FreshCaches

#: A link to a shard file in an index, capturing the name ``llms-`` precedes.
_SHARD_LINK = re.compile(r"/llms/llms-([a-z0-9-]+)\.txt")

#: The names the index of 2026-11-07 and the deploys before it linked that
#: the 4.0.0 deploy no longer wrote: each area had outgrown one fetch and
#: was cut into parts, and its own name answered 404 from then on.
RETIRED_BEFORE_THE_RECORD = (
    "buildings-design",
    "buildings-insulation",
    "buildings-rooms",
    "devices-electroacoustics",
    "devices-noise-control",
    "environment-propagation",
    "environment-sources",
    "materials-absorbers",
    "signals-metrology",
    "signals-spectra",
    "simulation",
    "theory",
    "underwater",
    "upgrading",
    "vibration-structural",
)


def _page(dump: Dump, route: str, size: int) -> str:
    """A page of one section of about *size* bytes of prose."""
    sentence = "Prose written to fill the page to its size. "
    body = "An introduction.\n\n## Only\n\n" + (sentence * (size // len(sentence)))
    return dump.add(route, body.rstrip())


@pytest.fixture
def dump(tmp_path: Path, fresh_caches: FreshCaches) -> Dump:
    """An empty dump the generator reads its pages from, its caches kept to the test."""
    fresh_caches(llms, PAGES=tmp_path / "dump")
    return Dump(tmp_path / "dump")


def _record(
    path: Path, published: list[str], redirects: dict[str, str] | None = None
) -> Path:
    path.write_text(
        json.dumps({"published": published, "redirects": redirects or {}}),
        encoding="utf-8",
    )
    return path


# --- The committed record ---------------------------------------------------


def test_the_record_holds_every_shard_the_committed_index_links() -> None:
    """``make llms`` writes the index and the record together, so neither is behind."""
    record = llms._read_shard_names(llms.SHARD_NAMES)
    linked = set(_SHARD_LINK.findall((ROOT / "llms.txt").read_text(encoding="utf-8")))
    assert linked <= record.published, sorted(linked - record.published)
    assert linked >= record.published, (
        "the record holds names the committed index does not link, so the "
        f"index no longer writes them: {sorted(record.published - linked)}"
    )


def test_every_name_retired_before_the_record_is_redirected_to_its_first_part() -> None:
    """The names the 4.0.0 deploy stopped writing answer with their first part."""
    record = llms._read_shard_names(llms.SHARD_NAMES)
    assert dict(record.redirects) == {
        name: f"{name}-1" for name in RETIRED_BEFORE_THE_RECORD
    }
    assert {f"{name}-1" for name in RETIRED_BEFORE_THE_RECORD} <= record.published


# --- The guard ----------------------------------------------------------------


def test_a_published_name_the_run_does_not_write_stops_it_by_name() -> None:
    record = llms.ShardNames(frozenset({"area", "other"}), {})
    with pytest.raises(
        SystemExit,
        match=r"published llms-area\.txt and this run writes no such file.*redirects",
    ):
        llms._check_names_kept({"other", "area-1", "area-2"}, record)


def test_a_redirected_name_passes_while_its_target_is_written() -> None:
    record = llms.ShardNames(frozenset({"area-1", "area-2"}), {"area": "area-1"})
    llms._check_names_kept({"area-1", "area-2"}, record)
    moved = llms.ShardNames(frozenset({"area-2"}), {"area": "area-1"})
    with pytest.raises(
        SystemExit,
        match=r"redirect\(s\) to a file this run does not write: "
        r"llms-area\.txt -> llms-area-1\.txt",
    ):
        llms._check_names_kept({"area-2"}, moved)


def test_a_redirected_name_written_again_is_refused() -> None:
    """The edge answers a redirected name before the site does, so the file would never be read."""
    record = llms.ShardNames(frozenset({"area-1"}), {"area": "area-1"})
    with pytest.raises(SystemExit, match=r"llms-area\.txt is written again"):
        llms._check_names_kept({"area", "area-1"}, record)


def test_a_record_naming_one_name_both_ways_is_refused(tmp_path: Path) -> None:
    path = _record(tmp_path / "names.json", ["area"], {"area": "area-1"})
    with pytest.raises(SystemExit, match=r"both as published and as redirected"):
        llms._read_shard_names(path)


def test_a_record_of_another_shape_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "names.json"
    path.write_text(json.dumps({"published": "area"}), encoding="utf-8")
    with pytest.raises(SystemExit, match=r"is no record of shard names"):
        llms._read_shard_names(path)


# --- What the run writes to keep the names -----------------------------------


def test_an_area_published_whole_keeps_its_name_once_it_needs_parts(
    dump: Dump, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``llms-area.txt`` lists the parts the area now travels in, and the index links it."""
    routes = [_page(dump, f"area/page-{n}", 9_000) for n in range(3)]
    plan = [("area", "Area", routes)]
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", 25_000)

    shards = llms.build_shards(plan, kept={"area"})
    listing = llms._part_indexes(plan, shards, {"area"})

    assert len(shards["area"]) == 2
    assert set(listing) == {"area"}
    assert _SHARD_LINK.findall(listing["area"]) == ["area", "area-1", "area-2"]
    assert listing["area"].startswith("# phonometry: Area, in 2 parts\n")
    files = {"area": llms._part_names("area", 2)}
    section = "\n".join(llms._full_text_section(plan, files, listing))
    assert (
        f"- [Area, the list of its 2 parts]({llms.SITE_URL}/llms/llms-area.txt)\n"
        f"- [Area, part 1 of 2]({llms.SITE_URL}/llms/llms-area-1.txt)"
    ) in section
    written = {**llms._published(shards), **listing}
    llms._check_names_kept(written, llms.ShardNames(frozenset({"area"}), {}))


def test_an_area_never_published_whole_gets_no_list(
    dump: Dump, monkeypatch: pytest.MonkeyPatch
) -> None:
    routes = [_page(dump, f"area/page-{n}", 9_000) for n in range(3)]
    plan = [("area", "Area", routes)]
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", 25_000)

    shards = llms.build_shards(plan, kept=set())

    assert llms._part_indexes(plan, shards, set()) == {}


def test_an_area_published_in_parts_is_cut_into_as_many_after_it_shrinks(
    dump: Dump, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Three parts stay three when two would do, and every page stays whole."""
    routes = [_page(dump, f"area/page-{n}", 4_000) for n in range(4)]
    plan = [("area", "Area", routes)]
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", 25_000)
    assert len(llms.build_shards(plan, kept=set())["area"]) == 1

    kept = {"area-1", "area-2", "area-3"}
    parts = llms.build_shards(plan, kept=kept)["area"]

    assert len(parts) == 3
    assert set(llms._published({"area": parts})) == kept
    assert all(len(part.encode("utf-8")) <= llms.SHARD_LIMIT_BYTES for part in parts)
    assert [
        sum(llms._copy(route).text in part for part in parts) for route in routes
    ] == [1, 1, 1, 1]


def test_an_area_of_fewer_pages_than_its_parts_stops_the_run_by_name(
    dump: Dump, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One page that fits whole cannot fill two parts: the run says which names it lost."""
    route = _page(dump, "area/page", 6_000)
    plan = [("area", "Area", [route])]
    monkeypatch.setattr(llms, "SHARD_LIMIT_BYTES", 25_000)
    kept = frozenset({"area-1", "area-2"})

    shards = llms.build_shards(plan, kept=kept)

    assert set(llms._published(shards)) == {"area"}
    with pytest.raises(SystemExit, match=r"llms-area-1\.txt, llms-area-2\.txt"):
        llms._check_names_kept(llms._published(shards), llms.ShardNames(kept, {}))


def test_make_llms_adds_the_names_it_writes_and_takes_none_out(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _record(tmp_path / "names.json", ["old"], {"gone": "old"})
    monkeypatch.setattr(llms, "SHARD_NAMES", path)

    llms._write_shard_names({"old", "new"}, llms._read_shard_names(path))

    written = json.loads(path.read_text(encoding="utf-8"))
    assert written["published"] == ["new", "old"]
    assert written["redirects"] == {"gone": "old"}
    assert llms._read_shard_names(path).published == {"new", "old"}
