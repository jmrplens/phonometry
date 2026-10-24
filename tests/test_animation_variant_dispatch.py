#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The fork path of a clip render, which nothing else was exercising.

``scripts/figures/registry.py`` renders the four language and theme variants
of a clip two ways: one after another in this process, or, when the platform
can fork, in four children, which share the field the parent computed when the
clip has a registered field builder. Only the second one is used for the
expensive clips, and only the first one was ever reached by a test.

They drifted. ``_render_anim_variant`` takes its ``dark`` flag keyword-only,
the way every boolean in this repository does, and the fork branch was passing
it positionally in ``Process(args=...)``. Nothing said so until a render was
asked for: the children raised ``TypeError`` inside ``multiprocessing``, the
parent saw four non-zero exit codes and reported "4 variant(s) failed", and
the clip that came out of it was the one already on disk.

So the test is the dispatch itself, with the drawing stubbed out: if the two
branches disagree about how the variant function is called, this fails in a
second rather than after a several-minute simulation.
"""

from __future__ import annotations

import multiprocessing as mp
import os
import pathlib
import re
import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

pytest.importorskip("matplotlib")
import matplotlib as mpl

mpl.use("Agg")

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

from figures import i18n, registry, theme

# The figure, diagram and badge tooling is tied to the pinned figure stack its
# artefacts are drawn with, so the minimum-versions job deselects this module.
pytestmark = pytest.mark.pinned_stack

#: The four variants every clip is rendered in.
EXPECTED = (("en", False), ("en", True), ("es", False), ("es", True))


@pytest.fixture(autouse=True)
def _no_frames_to_judge(monkeypatch: pytest.MonkeyPatch) -> None:
    """The stand-in clips here draw no frames, so there is nothing to judge.

    A render inspects all four variants before it encodes any
    (``registry._audited_first``) and stops a clip whose variants left no
    record of an inspection. These stand-ins never reach ``_render_clip``,
    which is what writes one; what this module tests is where each variant
    is rendered, and ``tests/test_clip_frame_audit.py`` tests the verdict.
    """
    import clip_frame_audit

    monkeypatch.setattr(clip_frame_audit, "verdict", lambda directory, clip: None)


@pytest.fixture(autouse=True)
def _restore_language_and_theme() -> Iterator[None]:
    """Put the process back the way it was found.

    ``_render_anim_variant`` sets the language and the theme and never puts
    them back, which is right for it: the generator gives each variant a
    process, or ends the run. Called here it would leave the Spanish labels
    and the dark stylesheet in place for whatever test the worker picks up
    next, and the one that notices is a figure check measuring ink against a
    background that is suddenly black.
    """
    yield
    i18n.set_lang("en")
    theme.set_theme(dark=False)


def test_the_four_variants_are_the_ones_the_registry_lists() -> None:
    """The oracle of the two tests below, so neither can pass vacuously."""
    assert set(registry._VARIANTS) == set(EXPECTED)


def _variant() -> tuple[str, bool]:
    """The language and theme the drawing code would see right now."""
    return i18n._LANG, theme._FILENAME_SUFFIX == "_dark"


def _record(written: list[tuple[str, bool]]) -> Callable[[str], None]:
    """A stand-in for a clip that records the variant it was asked for."""

    def draw(_output_dir: str) -> None:
        written.append(_variant())

    return draw


@pytest.mark.parametrize("forkable", [False, True])
def test_both_branches_render_the_same_four_variants(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path, *, forkable: bool
) -> None:
    """Sequential and forked have to agree, because only one of them is used.

    The forked branch cannot report back through a list, so it writes a file
    per variant instead: what is asserted is that four children ran and none
    of them raised, which is exactly what the positional ``dark`` broke.
    """
    if forkable and "fork" not in mp.get_all_start_methods():
        pytest.skip("this platform cannot fork")

    clip = "test_only_clip"
    if forkable:

        def draw(output_dir: str) -> None:
            lang, dark = _variant()
            name = f"{lang}_{dark}"
            (pathlib.Path(output_dir) / name).write_text("", encoding="utf-8")

        monkeypatch.setitem(registry._ANIM_FIELDS, clip, lambda: None)
    else:
        seen: list[tuple[str, bool]] = []
        draw = _record(seen)
        monkeypatch.setattr(mp, "get_all_start_methods", lambda: ["spawn"])

    monkeypatch.setitem(registry._ANIMATIONS, clip, draw)
    registry._render_anim_variants(clip, str(tmp_path))

    if forkable:
        written = {path.name for path in tmp_path.iterdir()}
        assert written == {f"{lang}_{dark}" for lang, dark in EXPECTED}
    else:
        assert set(seen) == set(EXPECTED)


def test_a_clip_without_a_field_forks_its_variants_too(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Every render audits its frames first, so a schematic clip forks as well.

    Four variants in four processes is what keeps the frame audit from
    multiplying the wall time of a schematic clip's render by four; nothing
    is simulated first, because there is no field to share.
    """
    if "fork" not in mp.get_all_start_methods():
        pytest.skip("this platform cannot fork")
    clip = "test_only_schematic"
    parent = os.getpid()

    def draw(output_dir: str) -> None:
        lang, dark = _variant()
        forked = os.getpid() != parent
        (pathlib.Path(output_dir) / f"{lang}_{dark}_{forked}").write_text(
            "", encoding="utf-8"
        )

    monkeypatch.delitem(registry._ANIM_FIELDS, clip, raising=False)
    monkeypatch.setitem(registry._ANIMATIONS, clip, draw)
    registry._render_anim_variants(clip, str(tmp_path))
    written = {path.name for path in tmp_path.iterdir()}
    assert written == {f"{lang}_{dark}_True" for lang, dark in EXPECTED}


def test_every_cached_clip_field_is_registered() -> None:
    """A field cached inside its module but not registered is simulated once per variant.

    The variants fork, and a cache filled in a child dies with it: the banner's
    2.5 GB frame stack was being computed by each of the four children until
    its builder was registered, so the parent computes it once and they share
    it. Every cached ``_*_fields`` function of the field clips is registered.
    """
    import figures.fields

    registered = set(registry._ANIM_FIELDS.values())
    unregistered = sorted(
        f"{module.__name__}.{name}"
        for module in (
            sys.modules[name]
            for name in sorted(sys.modules)
            if name.startswith(f"{figures.fields.__name__}.")
        )
        for name, value in vars(module).items()
        if name.endswith("_fields")
        and hasattr(value, "cache_info")
        and value.__module__ == module.__name__
        and value not in registered
    )
    assert unregistered == []


def test_the_device_is_released_after_the_field_and_before_the_variants(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """The fields are host arrays when the builder returns; CuPy's pool is not.

    Four forked children would each inherit the claim on the blocks the
    builder stepped in, so the parent frees them first. The parent's own
    list cannot show that a child started after the release, so the release
    leaves a file behind and each child writes down whether it saw it.
    """
    if "fork" not in mp.get_all_start_methods():
        pytest.skip("this platform cannot fork")
    import clip_placement

    events: list[str] = []
    clip = "test_only_clip"
    marker = tmp_path / "parent" / "released"
    marker.parent.mkdir()
    out = tmp_path / "variants"
    out.mkdir()

    def release() -> None:
        events.append("released")
        marker.touch()

    def draw(output_dir: str) -> None:
        lang, dark = _variant()
        name = f"{lang}_{dark}_{marker.exists()}"
        (pathlib.Path(output_dir) / name).write_text("", encoding="utf-8")

    monkeypatch.setitem(registry._ANIM_FIELDS, clip, lambda: events.append("field"))
    monkeypatch.setattr(clip_placement, "release_device", release)
    monkeypatch.setitem(registry._ANIMATIONS, clip, draw)
    registry._render_anim_variants(clip, str(out))
    assert events == ["field", "released"]
    written = {path.name for path in out.iterdir()}
    assert written == {f"{lang}_{dark}_True" for lang, dark in EXPECTED}


def test_an_uncalibrated_svt_av1_stops_the_render_before_any_field(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """A field can take an hour; the encoder is asked about before it."""
    import assets_dir
    from figures import media

    clip = "test_only_clip"
    built: list[str] = []
    monkeypatch.setitem(registry._ANIM_FIELDS, clip, lambda: built.append("field"))
    monkeypatch.setitem(registry._ANIMATIONS, clip, lambda output_dir: None)
    monkeypatch.setattr(assets_dir, "require_clips_dir", lambda: tmp_path)
    monkeypatch.setattr(media, "_svt_av1_version", lambda: "99.0.0")
    monkeypatch.delenv(media.CLIP_ENCODER_ENV, raising=False)
    with pytest.raises(SystemExit) as stop:
        registry.main(["--animations", "--anim", clip, "--jobs", "1"])
    assert stop.value.code != 0
    assert built == []


def test_a_scratch_render_writes_there_and_stamps_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """The node renders into a directory of its own and never stamps."""
    import shutil

    import animation_fingerprint
    import assets_dir

    clip = "test_only_clip"

    def draw(output_dir: str) -> None:
        (pathlib.Path(output_dir) / f"{clip}.webm").write_bytes(b"x")

    def refuse(*_: object, **__: object) -> None:
        msg = "a scratch render reached the assets or the manifest"
        raise AssertionError(msg)

    monkeypatch.setitem(registry._ANIMATIONS, clip, draw)
    monkeypatch.setattr(registry, "_render_anim_variants", lambda c, d: draw(d))
    monkeypatch.setattr(assets_dir, "require_clips_dir", refuse)
    monkeypatch.setattr(animation_fingerprint, "stamp", refuse)
    # The SVT-AV1 check before any field would ask this machine's ffmpeg; the
    # registry calls the name it imported from figures.media.
    monkeypatch.setattr(registry, "_clip_options", lambda encoder: ())
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/ffmpeg")
    registry.main(
        ["--animations", "--anim", clip, "--jobs", "1", "--scratch-dir", str(tmp_path)]
    )
    assert (tmp_path / "clips" / f"{clip}.webm").exists()


def test_a_scratch_audit_writes_its_findings_there(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """An audit-only run on a node leaves its findings beside its clips."""
    import assets_dir
    import clip_frame_audit

    clip = "test_only_clip"
    walked: list[str] = []

    def refuse() -> None:
        msg = "a scratch audit reached the assets"
        raise AssertionError(msg)

    def walk(output_dir: str, names: list[str], *, variants: bool) -> None:
        walked.append(output_dir)

    monkeypatch.setitem(registry._ANIMATIONS, clip, lambda output_dir: None)
    monkeypatch.setattr(registry, "generate_animations", walk)
    monkeypatch.setattr(clip_frame_audit, "report", lambda directory, clips: 0)
    monkeypatch.setattr(assets_dir, "require_clips_dir", refuse)
    # Set here so that the variable the command sets is put back afterwards.
    monkeypatch.setenv(clip_frame_audit.AUDIT_ENV, str(tmp_path / "elsewhere"))
    argv = [
        "--animations",
        "--audit-only",
        "--anim",
        clip,
        "--scratch-dir",
        str(tmp_path),
    ]
    with pytest.raises(SystemExit, match=r"^0$"):
        registry.main(argv)
    assert walked == [str((tmp_path / "audit").resolve())]


def _unset(monkeypatch: pytest.MonkeyPatch, *names: str) -> None:
    """Unset *names* for the test and restore them after, even if the code sets them."""
    for name in names:
        monkeypatch.setenv(name, "")
        monkeypatch.delenv(name)


@pytest.mark.parametrize(
    ("placement", "encoder"), [("cupy@nas", "av1_nvenc"), ("cpu@nas", "libsvtav1")]
)
def test_a_host_in_the_placement_sends_the_render_to_the_node(
    monkeypatch: pytest.MonkeyPatch, placement: str, encoder: str
) -> None:
    """The node asks its own ffmpeg; this machine's encoder is never checked for a node run."""
    import clip_transport

    calls: list[dict[str, object]] = []

    def on_host(compute: object, **kwargs: object) -> int:
        calls.append({"host": getattr(compute, "host", None), **kwargs})
        return 0

    def refuse(_name: object) -> tuple[str, ...]:
        msg = "a node run checked this machine's encoder"
        raise AssertionError(msg)

    monkeypatch.setenv("PHONOMETRY_COMPUTE", placement)
    monkeypatch.setattr(clip_transport, "main_on_host", on_host)
    # The registry calls the name it imported from figures.media.
    monkeypatch.setattr(registry, "_clip_options", refuse)
    with pytest.raises(SystemExit) as stop:
        registry.main(["--animations", "--anim", "anim_schroeder"])
    assert stop.value.code == 0
    assert calls == [
        {
            "host": "nas",
            "requested": ["anim_schroeder"],
            "force": False,
            "audit_only": False,
            "encoder": encoder,
        }
    ]


def test_a_gpu_here_renders_two_clips_at_a_time_and_a_large_one_alone(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """A render on this machine's GPU keeps a node's rules: two lanes, a lane's budget, the NVENC slots."""
    import shutil

    import assets_dir
    import clip_placement
    import encode_slots

    free, ram = 6 << 30, 12 << 30
    lane = clip_placement.gpu_budget(free, alone=False)
    devices = {"anim_a": "gpu", "anim_b": "gpu", "anim_big": "gpu", "anim_c": "cpu"}
    seen: list[tuple[str, list[str], int, str | None]] = []

    def pool(img_dir: str, names: list[str], jobs: int) -> None:
        seen.append(
            ("pool", sorted(names), jobs, os.environ.get(clip_placement.GPU_BYTES_ENV))
        )

    def one_at_a_time(img_dir: str, names: list[str] | None, *, variants: bool) -> None:
        seen.append(
            (
                "alone",
                sorted(names or []),
                1,
                os.environ.get(clip_placement.GPU_BYTES_ENV),
            )
        )

    _unset(
        monkeypatch,
        clip_placement.GPU_BYTES_ENV,
        clip_placement.HOST_BYTES_ENV,
        encode_slots.SLOTS_ENV,
    )
    monkeypatch.setenv("PHONOMETRY_COMPUTE", "cupy")
    monkeypatch.setattr(
        registry, "_ANIMATIONS", dict.fromkeys(devices, lambda output_dir: None)
    )
    monkeypatch.setattr(registry, "_ANIM_DEVICES", devices)
    monkeypatch.setattr(
        registry,
        "_ANIM_GPU_BYTES",
        {"anim_a": 1 << 30, "anim_b": 1 << 30, "anim_big": lane + 1},
    )
    monkeypatch.setattr(registry, "_ANIM_HOST_BYTES", {})
    monkeypatch.setattr(registry, "_generate_animations_parallel", pool)
    monkeypatch.setattr(registry, "generate_animations", one_at_a_time)
    monkeypatch.setattr(clip_placement, "free_gpu_bytes", lambda index=0, **_: free)
    monkeypatch.setattr(clip_placement, "host_bytes", lambda: ram)
    monkeypatch.setattr(assets_dir, "require_clips_dir", lambda: tmp_path)
    monkeypatch.setattr(registry, "_clip_options", lambda encoder: ())
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/ffmpeg")
    registry.main(["--animations", "--jobs", "8"])
    assert seen == [
        ("pool", ["anim_a", "anim_b", "anim_c"], 2, str(lane)),
        ("alone", ["anim_big"], 1, str(clip_placement.gpu_budget(free, alone=True))),
    ]
    assert os.environ[encode_slots.SLOTS_ENV].endswith(
        f":{encode_slots.NVENC_SESSIONS}"
    )


@pytest.mark.parametrize(
    "stop",
    [
        RuntimeError(
            "the node renders the committed code; commit first (1 changed: src/x.py)"
        ),
        KeyError("no host 'nas' in hosts.toml; it names none"),
    ],
    ids=["changes", "no-host"],
)
def test_what_stops_a_node_run_is_named_in_one_line(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    stop: Exception,
) -> None:
    """A checkout with changes or a host the file does not name is a sentence, not a traceback."""
    import clip_transport

    def on_host(compute: object, **_: object) -> int:
        raise stop

    monkeypatch.setenv("PHONOMETRY_COMPUTE", "cupy@nas")
    monkeypatch.setattr(clip_transport, "main_on_host", on_host)
    with pytest.raises(SystemExit) as ended:
        registry.main(["--animations"])
    assert ended.value.code == 2
    assert f"error: {stop.args[0]}\n" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("compute", "argv", "reason"),
    [
        ("cupy@nas", ["--animations", "--all"], "goes with --animations alone"),
        ("cupy@nas", ["--animations", "--posters"], "goes with --animations alone"),
        ("cupy@nas", [], "goes with --animations alone"),
        ("warp", ["--animations"], "PHONOMETRY_COMPUTE='warp'"),
    ],
)
def test_a_placement_a_run_cannot_take_stops_it_before_anything_is_sent(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    compute: str,
    argv: list[str],
    reason: str,
) -> None:
    """A host goes with the clips alone, and a placement that does not parse is named."""
    import clip_transport

    def on_host(compute: object, **_: object) -> int:
        msg = "the run was sent to a node"
        raise AssertionError(msg)

    monkeypatch.setenv("PHONOMETRY_COMPUTE", compute)
    monkeypatch.setattr(clip_transport, "main_on_host", on_host)
    with pytest.raises(SystemExit) as ended:
        registry.main(argv)
    assert ended.value.code == 2
    assert reason in capsys.readouterr().err


def _a_gpu_here(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    *,
    free: Callable[..., int],
    need: int,
) -> list[tuple[str, list[str], str | None, str | None]]:
    """This machine with a GPU and one GPU clip that needs *need* bytes of it.

    Each entry of the list returned is a render the run started: the path
    (``pool`` or ``alone``), its clips, and the GPU and RAM budgets its
    workers were given.
    """
    import shutil

    import assets_dir
    import clip_placement
    import encode_slots

    started: list[tuple[str, list[str], str | None, str | None]] = []

    def record(path: str) -> Callable[..., None]:
        def render(
            img_dir: str, names: list[str] | None, *_: object, **__: object
        ) -> None:
            budgets = (clip_placement.GPU_BYTES_ENV, clip_placement.HOST_BYTES_ENV)
            gpu, ram = (os.environ.get(name) for name in budgets)
            started.append((path, sorted(names or []), gpu, ram))

        return render

    _unset(
        monkeypatch,
        clip_placement.GPU_BYTES_ENV,
        clip_placement.HOST_BYTES_ENV,
        encode_slots.SLOTS_ENV,
    )
    monkeypatch.setenv("PHONOMETRY_COMPUTE", "cupy")
    monkeypatch.setattr(registry, "_ANIMATIONS", {"anim_a": lambda output_dir: None})
    monkeypatch.setattr(registry, "_ANIM_DEVICES", {"anim_a": "gpu"})
    monkeypatch.setattr(registry, "_ANIM_GPU_BYTES", {"anim_a": need})
    monkeypatch.setattr(registry, "_ANIM_HOST_BYTES", {})
    monkeypatch.setattr(registry, "_generate_animations_parallel", record("pool"))
    monkeypatch.setattr(registry, "generate_animations", record("alone"))
    monkeypatch.setattr(clip_placement, "free_gpu_bytes", free)
    monkeypatch.setattr(clip_placement, "host_bytes", lambda: 12 << 30)
    monkeypatch.setattr(assets_dir, "require_clips_dir", lambda: tmp_path)
    monkeypatch.setattr(registry, "_clip_options", lambda encoder: ())
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/ffmpeg")
    return started


def _no_device(index: int = 0, **_: object) -> int:
    """CuPy's probe on a machine whose driver sees no GPU."""
    raise subprocess.CalledProcessError(
        1,
        ["python", "-c", "..."],
        stderr="Traceback (most recent call last):\n"
        "cupy_backends.cuda.api.runtime.CUDARuntimeError: cudaErrorNoDevice\n",
    )


def _probe_hangs(index: int = 0, **_: object) -> int:
    """CuPy's probe on a card that never answers; a timeout keeps its output as bytes."""
    raise subprocess.TimeoutExpired(
        ["python", "-c", "..."], 120, stderr=b"waiting for the CUDA driver\n"
    )


@pytest.mark.parametrize("argv", [["--jobs", "8"], ["--anim", "anim_a"]])
@pytest.mark.parametrize(
    ("free", "need", "reason"),
    [
        (
            _no_device,
            1 << 20,
            r"GPU 0 could not be read through CuPy: [\w.]+: cudaErrorNoDevice\n",
        ),
        (
            _probe_hangs,
            1 << 20,
            r"GPU 0 could not be read through CuPy: waiting for the CUDA driver\n",
        ),
        (lambda index=0, **_: 1 << 30, 2 << 30, r"anim_a needs 2048 MiB of GPU memory"),
    ],
    ids=["unreadable", "hangs", "too-large"],
)
def test_a_gpu_here_that_cannot_hold_a_clip_stops_the_run_before_any_field(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
    free: Callable[..., int],
    need: int,
    reason: str,
) -> None:
    """One clip at a time or on the pool, the GPU is asked before a field steps."""
    started = _a_gpu_here(monkeypatch, tmp_path, free=free, need=need)
    with pytest.raises(SystemExit) as ended:
        registry.main(["--animations", *argv])
    assert ended.value.code == 2
    assert re.search(reason, capsys.readouterr().err)
    assert started == []


def test_one_clip_at_a_time_on_a_gpu_here_has_all_of_what_is_free(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """A targeted re-render runs alone, so its lane is the whole GPU and RAM."""
    import clip_placement

    free = 6 << 30
    started = _a_gpu_here(
        monkeypatch, tmp_path, free=lambda index=0, **_: free, need=1 << 30
    )
    registry.main(["--animations", "--anim", "anim_a"])
    whole_gpu = clip_placement.gpu_budget(free, alone=True)
    whole_ram = clip_placement.host_share(12 << 30, alone=True)
    assert started == [("alone", ["anim_a"], str(whole_gpu), str(whole_ram))]


@pytest.mark.parametrize(
    ("scratch", "budget"),
    [("lane", "4026531840"), ("lane", None), (None, "4026531840")],
    ids=["node-lane", "cpu-clip-lane", "budget-given"],
)
def test_a_render_given_its_budget_keeps_it_and_asks_the_gpu_nothing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    scratch: str | None,
    budget: str | None,
) -> None:
    """A node's lane renders with the share its node gave it, not all of the card."""
    import clip_placement

    probes: list[int] = []

    def probe(index: int = 0, **_: object) -> int:
        probes.append(index)
        return 8 << 30

    started = _a_gpu_here(monkeypatch, tmp_path, free=probe, need=1 << 30)
    if budget is not None:
        monkeypatch.setenv(clip_placement.GPU_BYTES_ENV, budget)
    monkeypatch.setenv(clip_placement.HOST_BYTES_ENV, str(3 << 30))
    argv = ["--animations", "--anim", "anim_a", "--jobs", "1"]
    if scratch is not None:
        argv += ["--scratch-dir", str(tmp_path / scratch)]
    registry.main(argv)
    assert probes == []
    assert started == [("alone", ["anim_a"], budget, str(3 << 30))]
