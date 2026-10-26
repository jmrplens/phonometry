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
    from collections.abc import Callable
    from types import ModuleType

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
def _restore_language_and_theme(figure_theme: ModuleType) -> None:
    """Put the process back the way it was found, through ``figure_theme``.

    ``_render_anim_variant`` sets the language and the theme and never puts
    them back, which is right for it: the generator gives each variant a
    process, or ends the run. Called here it would leave the Spanish labels
    and the dark stylesheet in place for whatever test the worker picks up
    next, and the one that notices is a figure check measuring ink against a
    background that is suddenly black. The fixture puts back the language,
    the theme and every setting after each test.
    """


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
    draw: Callable[[str], None]
    if forkable:

        def write(output_dir: str) -> None:
            lang, dark = _variant()
            name = f"{lang}_{dark}"
            (pathlib.Path(output_dir) / name).write_text("", encoding="utf-8")

        draw = write
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
    builder stepped in, so the parent frees them first. A forked child holds
    a copy of the parent's memory as it stood at the fork, so each child
    reads the parent's events in its own copy and writes down whether the
    release was already among them; nothing the parent does after the fork
    can reach that copy.
    """
    if "fork" not in mp.get_all_start_methods():
        pytest.skip("this platform cannot fork")
    import clip_placement

    events: list[str] = []
    clip = "test_only_clip"
    parent = os.getpid()

    def draw(output_dir: str) -> None:
        lang, dark = _variant()
        forked = os.getpid() != parent
        name = f"{lang}_{dark}_{forked}_{'released' in events}"
        (pathlib.Path(output_dir) / name).write_text("", encoding="utf-8")

    monkeypatch.setitem(registry._ANIM_FIELDS, clip, lambda: events.append("field"))
    monkeypatch.setattr(
        clip_placement, "release_device", lambda: events.append("released")
    )
    monkeypatch.setitem(registry._ANIMATIONS, clip, draw)
    registry._render_anim_variants(clip, str(tmp_path))
    assert events == ["field", "released"]
    written = {path.name for path in tmp_path.iterdir()}
    assert written == {f"{lang}_{dark}_True_True" for lang, dark in EXPECTED}


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
    # The program is named, not looked for: no ffmpeg need be installed.
    monkeypatch.setattr(media, "find_ffmpeg", lambda: "ffmpeg")
    monkeypatch.setattr(media, "_svt_av1_version", lambda ffmpeg: "99.0.0")
    monkeypatch.delenv(media.CLIP_ENCODER_ENV, raising=False)
    with pytest.raises(SystemExit) as stop:
        registry.main(["--animations", "--anim", clip, "--jobs", "1"])
    assert stop.value.code != 0
    assert built == []


def test_a_render_with_no_ffmpeg_stops_with_its_reason_before_any_field(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An ffmpeg that is not there ends the run with the reason, never a traceback."""
    import assets_dir
    import matplotlib as mpl
    from figures import media

    clip = "test_only_clip"
    built: list[str] = []
    monkeypatch.setitem(registry._ANIM_FIELDS, clip, lambda: built.append("field"))
    monkeypatch.setitem(registry._ANIMATIONS, clip, lambda output_dir: None)
    monkeypatch.setattr(assets_dir, "require_clips_dir", lambda: tmp_path)
    monkeypatch.delenv(media.CLIP_ENCODER_ENV, raising=False)
    argv = ["--animations", "--anim", clip, "--jobs", "1"]
    missing = str(tmp_path / "no-ffmpeg-here")
    with (
        mpl.rc_context({"animation.ffmpeg_path": missing}),
        pytest.raises(SystemExit) as stop,
    ):
        registry.main(argv)
    assert stop.value.code == 2
    assert "ffmpeg was not found" in capsys.readouterr().err
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
    """An audit-only run on a node leaves its findings beside its clips, and stamps nothing."""
    import assets_dir
    import clip_frame_audit

    clip = "test_only_clip"
    walked: list[tuple[str, bool]] = []

    def refuse() -> None:
        msg = "a scratch audit reached the assets"
        raise AssertionError(msg)

    def walk(output_dir: str, names: list[str], *, variants: bool, stamp: bool) -> None:
        walked.append((output_dir, stamp))

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
    assert walked == [(str((tmp_path / "audit").resolve()), False)]


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
    import clip_link
    import clip_transport

    calls: list[dict[str, object]] = []

    def on_host(compute: object, **kwargs: object) -> int:
        calls.append({"host": getattr(compute, "host", None), **kwargs})
        return 0

    def refuse(_name: object) -> tuple[str, ...]:
        msg = "a node run checked this machine's encoder"
        raise AssertionError(msg)

    monkeypatch.setenv("PHONOMETRY_COMPUTE", placement)
    monkeypatch.setattr(clip_link, "host_entry", lambda name: name)
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
    # The NVENC sessions are counted in this user's own directory, on POSIX
    # (the slots are file locks there; elsewhere none is held).
    if os.name == "posix":
        assert os.environ[encode_slots.SLOTS_ENV] == (
            f"{encode_slots.shared_directory()}:{encode_slots.NVENC_SESSIONS}"
        )


def _node_run_error(message: str) -> Exception:
    """A :class:`clip_transport.NodeRunError` saying *message*."""
    import clip_transport

    return clip_transport.NodeRunError(message)


@pytest.mark.parametrize(
    ("where", "stop", "said"),
    [
        (
            "run",
            RuntimeError(
                "the node renders the committed code; commit first (1 changed: src/x.py)"
            ),
            "the node renders the committed code; commit first (1 changed: src/x.py)",
        ),
        (
            "run",
            RuntimeError("the node refused the job: no GPU 1 here"),
            "the node refused the job: no GPU 1 here",
        ),
        (
            "run",
            FileNotFoundError(2, "No such file or directory", "ssh"),
            "[Errno 2] No such file or directory: 'ssh'",
        ),
        (
            "run",
            _node_run_error(
                "the archive is 300000000 bytes, over the 268435456 a node accepts"
            ),
            "the archive is 300000000 bytes, over the 268435456 a node accepts",
        ),
        (
            "hosts",
            KeyError("no host 'nas' in hosts.toml; it names none"),
            "no host 'nas' in hosts.toml; it names none",
        ),
        (
            "hosts",
            ValueError("hosts.toml does not parse: expected '=' at line 3"),
            "hosts.toml does not parse: expected '=' at line 3",
        ),
    ],
    ids=["changes", "refused", "no-ssh", "too-large", "no-host", "hosts-file"],
)
def test_what_stops_a_node_run_is_named_in_one_line(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    where: str,
    stop: Exception,
    said: str,
) -> None:
    """A checkout with changes, a refusal, no ssh or a host the file does not name is a sentence, not a traceback.

    An error of the operating system is named by its message, never by its
    number alone.
    """
    import clip_link
    import clip_transport

    def fail(*_: object, **__: object) -> int:
        raise stop

    def unreached(*_: object, **__: object) -> int:
        msg = "the run was sent to a node whose host is not in the hosts file"
        raise AssertionError(msg)

    monkeypatch.setenv("PHONOMETRY_COMPUTE", "cupy@nas")
    monkeypatch.setattr(
        clip_link, "host_entry", fail if where == "hosts" else lambda name: name
    )
    monkeypatch.setattr(
        clip_transport, "main_on_host", fail if where == "run" else unreached
    )
    with pytest.raises(SystemExit) as ended:
        registry.main(["--animations"])
    assert ended.value.code == 2
    assert f"error: {said}\n" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("where", "fault", "said"),
    [
        ("main_on_host", KeyError("clip"), r"^'clip'$"),
        (
            "render_on_host",
            ValueError("not enough values to unpack (expected 2, got 1)"),
            r"^not enough values to unpack \(expected 2, got 1\)$",
        ),
    ],
    ids=["key", "value"],
)
def test_a_fault_inside_the_node_run_keeps_its_traceback(
    monkeypatch: pytest.MonkeyPatch, where: str, fault: Exception, said: str
) -> None:
    """Only the errors the node run documents are cut to one line; a fault inside it is not hidden.

    The value errors the node run documents are checked before it starts
    (an unknown clip or encoder, a float32 placement, a missing host), so
    one that comes out of it is a fault.
    """
    import clip_link
    import clip_transport

    def fail(*_: object, **__: object) -> int:
        raise fault

    monkeypatch.setenv("PHONOMETRY_COMPUTE", "cupy@nas")
    monkeypatch.setattr(clip_link, "host_entry", lambda name: name)
    monkeypatch.setattr(clip_transport, where, fail)
    with pytest.raises(type(fault), match=said):
        registry.main(["--animations"])


def test_a_float32_placement_is_refused_before_a_node_is_asked(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The clips are float64 on a node too; nothing is looked up or sent first."""
    reached = _nothing_runs(monkeypatch, tmp_path)
    monkeypatch.setenv("PHONOMETRY_COMPUTE", "cupy@nas,float32")
    with pytest.raises(SystemExit) as ended:
        registry.main(["--animations"])
    assert ended.value.code == 2
    assert (
        "the clips are computed in float64; PHONOMETRY_COMPUTE asks for float32"
        in capsys.readouterr().err
    )
    assert reached == []


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


def _probe_cannot_start(index: int = 0, **_: object) -> int:
    """CuPy's probe on a machine that has no memory left to start a process."""
    raise OSError(12, "Cannot allocate memory")


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
        (
            _probe_cannot_start,
            1 << 20,
            r"GPU 0 could not be read through CuPy: \[Errno 12\] Cannot allocate memory\n",
        ),
        (lambda index=0, **_: 1 << 30, 2 << 30, r"anim_a needs 2048 MiB of GPU memory"),
    ],
    ids=["unreadable", "hangs", "cannot-start", "too-large"],
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


def test_ram_here_that_cannot_be_read_stops_the_run_before_any_field(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A memory file this machine will not let the run read is a sentence, not a traceback."""
    import clip_placement

    started = _a_gpu_here(
        monkeypatch, tmp_path, free=lambda index=0, **_: 6 << 30, need=1 << 30
    )

    def unreadable() -> int | None:
        raise PermissionError(13, "Permission denied", "/sys/fs/cgroup/memory.current")

    monkeypatch.setattr(clip_placement, "host_bytes", unreadable)
    with pytest.raises(SystemExit) as ended:
        registry.main(["--animations", "--anim", "anim_a"])
    assert ended.value.code == 2
    err = capsys.readouterr().err
    assert (
        "the RAM free here could not be read: "
        "[Errno 13] Permission denied: '/sys/fs/cgroup/memory.current'"
    ) in err
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


def _nothing_runs(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> list[str]:
    """Stand-ins for every part of a run that does work, each noting that it was reached.

    The figures, the clips, the posters, the audit and a node run are all
    replaced, and the run starts in *tmp_path*, so a check that fails to stop
    the run renders nothing and writes only there. The encoder and the
    placement are left to the test; the variables the run sets are put back.
    """
    import shutil

    import assets_dir
    import clip_link
    import clip_placement
    import clip_transport
    import encode_slots
    from figures import media

    reached: list[str] = []

    def note(name: str) -> Callable[..., int]:
        def stand_in(*_: object, **__: object) -> int:
            reached.append(name)
            return 0

        return stand_in

    for name in ("_render_figures", "_render_clips", "generate_posters"):
        monkeypatch.setattr(registry, name, note(name))
    monkeypatch.setattr(clip_transport, "main_on_host", note("node"))
    monkeypatch.setattr(clip_link, "host_entry", note("hosts"))
    monkeypatch.setattr(assets_dir, "require_clips_dir", lambda: tmp_path / "published")
    monkeypatch.setattr(registry, "_clip_options", lambda encoder: ())
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/ffmpeg")
    _unset(
        monkeypatch,
        "PHONOMETRY_COMPUTE",
        media.CLIP_ENCODER_ENV,
        clip_placement.GPU_BYTES_ENV,
        clip_placement.HOST_BYTES_ENV,
        encode_slots.SLOTS_ENV,
    )
    monkeypatch.chdir(tmp_path)
    return reached


def test_an_encoder_the_environment_names_that_writes_no_clip_stops_the_run_first(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A ``PHONOMETRY_CLIP_ENCODER`` set from outside is read before any clip renders."""
    from figures import media

    reached = _nothing_runs(monkeypatch, tmp_path)
    monkeypatch.setattr(registry, "_clip_options", media._clip_options)
    monkeypatch.setenv(media.CLIP_ENCODER_ENV, "libvpx-vp9")
    with pytest.raises(SystemExit) as ended:
        registry.main(["--animations", "--anim", "anim_schroeder", "--jobs", "1"])
    assert ended.value.code == 2
    err = capsys.readouterr().err
    assert "PHONOMETRY_CLIP_ENCODER must be one of av1_nvenc, libsvtav1" in err
    assert reached == []


@pytest.mark.parametrize(
    ("compute", "argv", "reason"),
    [
        (None, ["--clip-encoder", "libsvtav1"], "--clip-encoder requires --animations"),
        (
            None,
            ["--posters", "--clip-encoder", "av1_nvenc"],
            "--clip-encoder requires --animations",
        ),
        (None, ["--force"], "--force goes with --animations and a host"),
        (
            None,
            ["--animations", "--force"],
            "--force goes with --animations and a host",
        ),
        (
            "cupy@nas",
            ["--animations", "--force", "--scratch-dir", "lane"],
            "--force goes with --animations and a host",
        ),
        (
            "cupy@nas",
            ["--animations", "--jobs", "2"],
            "--jobs does not go with a host in PHONOMETRY_COMPUTE",
        ),
    ],
    ids=[
        "encoder-for-figures",
        "encoder-for-posters",
        "force-for-figures",
        "force-without-a-host",
        "force-in-a-node-lane",
        "jobs-for-a-node",
    ],
)
def test_an_option_the_run_would_not_use_is_refused(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    compute: str | None,
    argv: list[str],
    reason: str,
) -> None:
    """An option is never ignored in silence: one the run has no use for stops it, as ``--anim`` does."""
    reached = _nothing_runs(monkeypatch, tmp_path)
    if compute is not None:
        monkeypatch.setenv("PHONOMETRY_COMPUTE", compute)
    with pytest.raises(SystemExit) as ended:
        registry.main(argv)
    assert ended.value.code == 2
    assert reason in capsys.readouterr().err
    assert reached == []


@pytest.mark.parametrize(
    ("compute", "argv", "reason"),
    [
        ("cupy:1", ["--anim", "anim_a"], "names GPU 1; the clips step on GPU 0"),
        ("cupy:1", ["--jobs", "8"], "names GPU 1; the clips step on GPU 0"),
        ("cupy:1", ["--audit-only"], "names GPU 1; the clips step on GPU 0"),
        ("cupy,float32", ["--anim", "anim_a"], "asks for float32"),
        ("torch:cuda", ["--jobs", "8"], "names 'torch:cuda'"),
        (
            "cupy@nas",
            ["--anim", "anim_a", "--scratch-dir", "lane"],
            "names the host 'nas'",
        ),
    ],
    ids=[
        "second-gpu-one-clip",
        "second-gpu-pool",
        "second-gpu-audit",
        "float32",
        "another-library",
        "host-in-a-lane",
    ],
)
def test_a_placement_no_clip_could_step_on_stops_the_run_before_anything_starts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    compute: str,
    argv: list[str],
    reason: str,
) -> None:
    """What a clip's field would refuse is refused before a GPU is asked or a clip drawn."""
    import clip_frame_audit
    import clip_placement

    probes: list[int] = []

    def probe(index: int = 0, **_: object) -> int:
        probes.append(index)
        return 8 << 30

    started = _a_gpu_here(monkeypatch, tmp_path, free=probe, need=1 << 20)
    monkeypatch.setattr(clip_frame_audit, "DEFAULT_DIR", str(tmp_path / "audit"))
    monkeypatch.setattr(clip_frame_audit, "report", lambda directory, clips: 0)
    monkeypatch.setenv(clip_frame_audit.AUDIT_ENV, str(tmp_path / "elsewhere"))
    monkeypatch.setenv("PHONOMETRY_COMPUTE", compute)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as ended:
        registry.main(["--animations", *argv])
    assert ended.value.code == 2
    assert f"PHONOMETRY_COMPUTE {reason}" in capsys.readouterr().err
    assert probes == []
    assert started == []
    assert clip_placement.GPU_BYTES_ENV not in os.environ


def test_a_placement_only_the_clips_refuse_does_not_stop_the_figures(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """The figures step their engines wherever PHONOMETRY_COMPUTE says."""
    reached = _nothing_runs(monkeypatch, tmp_path)
    monkeypatch.setenv("PHONOMETRY_COMPUTE", "cupy:1")
    registry.main(["--jobs", "1"])
    assert reached == ["_render_figures"]


def _probes_recorded(probes: list[int]) -> Callable[..., int]:
    """CuPy's probe of a GPU with 8 GiB free, noting each GPU it is asked about."""

    def probe(index: int = 0, **_: object) -> int:
        probes.append(index)
        return 8 << 30

    return probe


def test_an_unknown_clip_is_refused_before_the_gpu_is_asked(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The arguments are checked first; asking the GPU can take two minutes."""
    probes: list[int] = []
    started = _a_gpu_here(
        monkeypatch, tmp_path, free=_probes_recorded(probes), need=1 << 20
    )
    with pytest.raises(SystemExit) as ended:
        registry.main(["--animations", "--anim", "anim_nope"])
    assert ended.value.code == 2
    assert "unknown animation(s) ['anim_nope']; available: anim_a" in (
        capsys.readouterr().err
    )
    assert probes == []
    assert started == []


@pytest.mark.parametrize(
    "argv", [["--anim", "anim_a"], ["--jobs", "8"]], ids=["one-clip", "pool"]
)
def test_a_render_with_no_ffmpeg_is_refused_before_the_gpu_is_asked(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
) -> None:
    """NVENC is not asked for its version, so the posters' ffmpeg is looked for up front."""
    import shutil

    from figures import media

    probes: list[int] = []
    started = _a_gpu_here(
        monkeypatch, tmp_path, free=_probes_recorded(probes), need=1 << 20
    )
    monkeypatch.setattr(shutil, "which", lambda name: None)
    _unset(monkeypatch, media.CLIP_ENCODER_ENV)
    with pytest.raises(SystemExit) as ended:
        registry.main(["--animations", "--clip-encoder", "av1_nvenc", *argv])
    assert ended.value.code == 2
    assert "ffmpeg was not found on PATH" in capsys.readouterr().err
    assert probes == []
    assert started == []


@pytest.mark.parametrize(
    ("argv", "reason"),
    [
        (
            ["--animations", "--jobs", "0", "--scratch-dir", "scratch"],
            "--jobs must be >= 1",
        ),
        (["--jobs", "0"], "--jobs must be >= 1"),
        (
            ["--animations", "--audit-only", "--posters"],
            "--audit-only goes with --animations alone",
        ),
    ],
    ids=["jobs-of-a-scratch-render", "jobs-of-the-figures", "audit-with-posters"],
)
def test_nothing_is_written_before_the_arguments_are_checked(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
    reason: str,
) -> None:
    """A run that its arguments stop makes no directory first."""
    reached = _nothing_runs(monkeypatch, tmp_path)
    with pytest.raises(SystemExit) as ended:
        registry.main(argv)
    assert ended.value.code == 2
    assert reason in capsys.readouterr().err
    assert sorted(path.name for path in tmp_path.iterdir()) == []
    assert reached == []


def test_the_scratch_directory_s_help_says_an_audit_empties_its_findings_first() -> (
    None
):
    """What a run deletes is said where the option is described."""
    said = " ".join(registry._parser().format_help().split())
    assert "an audit-only run empties DIR/audit first" in said


def test_a_scratch_render_never_stamps_even_into_the_published_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """A node's lane never stamps, wherever its scratch directory is, and never reads ``.env``.

    Here the published clips directory is the scratch run's own ``clips``,
    so only the run's arguments can tell the two apart.
    """
    import shutil

    import animation_fingerprint
    import assets_dir
    import repo_env

    clip = "test_only_clip"

    def draw(output_dir: str) -> None:
        (pathlib.Path(output_dir) / f"{clip}.webm").write_bytes(b"x")

    def refuse(*_: object, **__: object) -> None:
        msg = "a scratch render stamped, or read .env to see whether to"
        raise AssertionError(msg)

    monkeypatch.setenv(assets_dir.VARIABLE, str(tmp_path / "clips"))
    _unset(monkeypatch, "PHONOMETRY_COMPUTE")
    monkeypatch.setitem(registry._ANIMATIONS, clip, draw)
    monkeypatch.setattr(registry, "_render_anim_variants", lambda c, d: draw(d))
    monkeypatch.setattr(animation_fingerprint, "stamp", refuse)
    monkeypatch.setattr(repo_env, "load_env", refuse)
    monkeypatch.setattr(registry, "_clip_options", lambda encoder: ())
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/ffmpeg")
    registry.main(
        ["--animations", "--anim", clip, "--jobs", "1", "--scratch-dir", str(tmp_path)]
    )
    assert (tmp_path / "clips" / f"{clip}.webm").exists()


def _four_clips_on_a_gpu_here(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> list[tuple[str, list[str], int, str | None]]:
    """This machine with a GPU of 6 GiB free, 12 GiB of RAM and four clips.

    Two GPU clips that fit a lane, one that needs more than a lane and so
    runs alone, and a clip that steps on NumPy. Each entry of the list
    returned is a render the run started: ``pool`` or ``alone``, its clips,
    its workers and the GPU budget they were given.
    """
    import shutil

    import assets_dir
    import clip_frame_audit
    import clip_placement
    import encode_slots

    lane = clip_placement.gpu_budget(6 << 30, alone=False)
    devices = {"anim_a": "gpu", "anim_b": "gpu", "anim_big": "gpu", "anim_c": "cpu"}
    seen: list[tuple[str, list[str], int, str | None]] = []

    def pool(img_dir: str, names: list[str], jobs: int, **_: object) -> None:
        budget = os.environ.get(clip_placement.GPU_BYTES_ENV)
        seen.append(("pool", sorted(names), jobs, budget))

    def one_at_a_time(img_dir: str, names: list[str] | None, **_: object) -> None:
        budget = os.environ.get(clip_placement.GPU_BYTES_ENV)
        seen.append(("alone", sorted(names or []), 1, budget))

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
    monkeypatch.setattr(clip_placement, "free_gpu_bytes", lambda index=0, **_: 6 << 30)
    monkeypatch.setattr(clip_placement, "host_bytes", lambda: 12 << 30)
    monkeypatch.setattr(assets_dir, "require_clips_dir", lambda: tmp_path)
    monkeypatch.setattr(registry, "_clip_options", lambda encoder: ())
    monkeypatch.setattr(shutil, "which", lambda name: "/usr/bin/ffmpeg")
    monkeypatch.setattr(clip_frame_audit, "DEFAULT_DIR", str(tmp_path / "audit"))
    monkeypatch.setattr(clip_frame_audit, "report", lambda directory, clips: 0)
    monkeypatch.setenv(clip_frame_audit.AUDIT_ENV, str(tmp_path / "elsewhere"))
    return seen


def test_an_audit_on_a_gpu_here_keeps_a_node_s_rules(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """An audit draws every frame as a render does, so it shares the GPU the same way.

    Two clips at a time with a lane's budget each, the large one after them
    with all of it, and the NVENC slots named, never eight pool workers with
    no budget at all.
    """
    import clip_placement
    import encode_slots

    seen = _four_clips_on_a_gpu_here(monkeypatch, tmp_path)
    with pytest.raises(SystemExit, match=r"^0$"):
        registry.main(["--animations", "--audit-only", "--jobs", "8"])
    assert seen == [
        (
            "pool",
            ["anim_a", "anim_b", "anim_c"],
            2,
            str(clip_placement.gpu_budget(6 << 30, alone=False)),
        ),
        ("alone", ["anim_big"], 1, str(clip_placement.gpu_budget(6 << 30, alone=True))),
    ]
    if os.name == "posix":
        assert encode_slots.SLOTS_ENV in os.environ


def test_an_audit_of_one_clip_on_a_gpu_here_has_all_of_what_is_free(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    import clip_placement

    seen = _four_clips_on_a_gpu_here(monkeypatch, tmp_path)
    with pytest.raises(SystemExit, match=r"^0$"):
        registry.main(["--animations", "--audit-only", "--anim", "anim_a"])
    whole = str(clip_placement.gpu_budget(6 << 30, alone=True))
    assert seen == [("alone", ["anim_a"], 1, whole)]


def test_a_render_on_a_gpu_here_says_how_many_clips_run_at_once(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Eight workers are asked for and two lanes run: the log says what runs."""
    _four_clips_on_a_gpu_here(monkeypatch, tmp_path)
    registry.main(["--animations", "--jobs", "8"])
    out = capsys.readouterr().out
    assert (
        f"--- Generating animations (3 clips x 4 variants, 2 at a time on the GPU, "
        f"then 1 alone) into {tmp_path} ---"
    ) in out
    assert "8 jobs" not in out


def _no_count(index: int = 0, **_: object) -> int:
    """CuPy's probe on a card whose CuPy answers something other than a count."""
    msg = f"CuPy did not name the free memory of GPU {index}: 'busy'"
    raise ValueError(msg)


@pytest.mark.parametrize(
    ("argv", "path"),
    [(["--anim", "anim_a"], "alone"), (["--jobs", "8"], "pool")],
    ids=["one-clip", "pool"],
)
@pytest.mark.parametrize(
    ("free", "reason"),
    [
        (_no_device, r"the free memory of GPU 0 could not be read through CuPy: .+"),
        (_no_count, r"CuPy did not name the free memory of GPU 0: 'busy'"),
    ],
    ids=["cupy-cannot-work", "no-count"],
)
def test_a_gpu_here_that_cannot_be_read_falls_back_to_numpy_when_the_placement_says_so(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    argv: list[str],
    path: str,
    free: Callable[..., int],
    reason: str,
) -> None:
    """``cupy,fallback`` on a machine whose CuPy does not work renders the clips on NumPy.

    With a warning saying why, as an engine falls back, and with no lane
    budget: nothing steps on the GPU, and every worker steps on NumPy. CuPy
    that does not import or that CUDA refuses, and a probe that answers no
    count, are a CuPy that does not work.
    """
    from phonometry.simulation import ComputeFallbackWarning

    started = _a_gpu_here(monkeypatch, tmp_path, free=free, need=1 << 20)
    monkeypatch.setenv("PHONOMETRY_COMPUTE", "cupy,fallback")
    with pytest.warns(
        ComputeFallbackWarning,
        match=rf"^{reason}; rendering the clips on NumPy instead \(fallback\)$",
    ):
        registry.main(["--animations", *argv])
    assert started == [(path, ["anim_a"], None, None)]
    assert os.environ["PHONOMETRY_COMPUTE"] == "cpu"


@pytest.mark.parametrize(
    ("free", "reason"),
    [
        (_probe_hangs, "waiting for the CUDA driver"),
        (_probe_cannot_start, "[Errno 12] Cannot allocate memory"),
    ],
    ids=["hangs", "cannot-start"],
)
def test_a_probe_that_hangs_or_cannot_start_stops_the_run_even_with_fallback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    free: Callable[..., int],
    reason: str,
) -> None:
    """Neither says CuPy cannot work here, so neither is taken for a reason to step on NumPy."""
    started = _a_gpu_here(monkeypatch, tmp_path, free=free, need=1 << 20)
    monkeypatch.setenv("PHONOMETRY_COMPUTE", "cupy,fallback")
    with pytest.raises(SystemExit) as ended:
        registry.main(["--animations", "--anim", "anim_a"])
    assert ended.value.code == 2
    assert (
        f"the free memory of GPU 0 could not be read through CuPy: {reason}\n"
        in capsys.readouterr().err
    )
    assert started == []
    assert os.environ["PHONOMETRY_COMPUTE"] == "cupy,fallback"


def _an_audit_here(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    """An audit-only run writes its findings under *tmp_path* and finds nothing."""
    import clip_frame_audit

    monkeypatch.setattr(clip_frame_audit, "DEFAULT_DIR", str(tmp_path / "audit"))
    monkeypatch.setattr(clip_frame_audit, "report", lambda directory, clips: 0)
    monkeypatch.setenv(clip_frame_audit.AUDIT_ENV, str(tmp_path / "elsewhere"))


@pytest.mark.parametrize(
    "argv", [["--jobs", "8"], ["--audit-only", "--jobs", "8"]], ids=["render", "audit"]
)
def test_a_gpu_budget_given_by_hand_to_a_pool_of_every_clip_is_refused(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
) -> None:
    """A lane's budget cannot hold a pool of workers on this machine's GPU to anything.

    The run divides the GPU itself, two clips at a time, when no budget is
    given; with one, it would take the plain pool, with no two-lane cap, no
    NVENC slots and no clip held back to run alone.
    """
    import clip_placement

    probes: list[int] = []
    started = _a_gpu_here(
        monkeypatch, tmp_path, free=_probes_recorded(probes), need=1 << 20
    )
    _an_audit_here(monkeypatch, tmp_path)
    monkeypatch.setenv(clip_placement.GPU_BYTES_ENV, "4026531840")
    with pytest.raises(SystemExit) as ended:
        registry.main(["--animations", *argv])
    assert ended.value.code == 2
    assert "PHONOMETRY_CLIP_GPU_BYTES is one lane's budget" in capsys.readouterr().err
    assert probes == []
    assert started == []


@pytest.mark.parametrize(
    ("compute", "scratch"),
    [("cupy", "lane"), ("cpu", None)],
    ids=["node-lane", "no-gpu-named"],
)
def test_a_gpu_budget_with_a_pool_is_kept_where_no_gpu_here_is_divided(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    compute: str,
    scratch: str | None,
) -> None:
    """A node's lane keeps what it was given, and without CuPy no budget is ever used."""
    import clip_placement

    probes: list[int] = []
    started = _a_gpu_here(
        monkeypatch, tmp_path, free=_probes_recorded(probes), need=1 << 20
    )
    monkeypatch.setenv("PHONOMETRY_COMPUTE", compute)
    monkeypatch.setenv(clip_placement.GPU_BYTES_ENV, "4026531840")
    argv = ["--animations", "--jobs", "8"]
    if scratch is not None:
        argv += ["--scratch-dir", str(tmp_path / scratch)]
    registry.main(argv)
    assert probes == []
    assert started == [("pool", ["anim_a"], "4026531840", None)]


def test_two_clip_tables_that_name_different_clips_say_which() -> None:
    """The import-time guards name the clips each table has and the other lacks."""
    devices = {"anim_a": "gpu", "anim_b": "cpu", "anim_c": "gpu-whole"}
    on_a_gpu = {clip for clip, device in devices.items() if device != "cpu"}
    peaks = {"anim_a": 1 << 20, "anim_b": 1 << 20}
    with pytest.raises(
        RuntimeError,
        match=r"^_ANIM_GPU_BYTES and the clips _ANIM_DEVICES puts on a GPU name "
        r"different clips: \['anim_b', 'anim_c'\]$",
    ):
        registry._require_the_same_clips(
            peaks, on_a_gpu, "_ANIM_GPU_BYTES and the clips _ANIM_DEVICES puts on a GPU"
        )


@pytest.mark.parametrize(
    ("compute", "argv"),
    [
        (None, ["--animations", "--anim", "anim_schroeder", "--jobs", "1"]),
        (None, ["--all", "--jobs", "1"]),
        (None, ["--posters"]),
        ("cupy@nas", ["--animations"]),
        ("cupy@nas", ["--animations", "--audit-only"]),
    ],
    ids=["render", "all", "posters", "node", "node-audit"],
)
@pytest.mark.parametrize(
    ("digests", "said"),
    [
        (
            '{"scenarios": {}}',
            "does not hold the engines' digests (no fluid_energy record); "
            "record them again with `make engine-digests`",
        ),
        (None, "is missing; record the engines' digests with `make engine-digests`"),
    ],
    ids=["no-digests", "missing"],
)
def test_a_run_that_stamps_clips_reads_the_engine_digests_before_anything_runs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    compute: str | None,
    argv: list[str],
    digests: str | None,
    said: str,
) -> None:
    """A digest file that cannot stamp a clip stops the run in one line, not after the render."""
    reached = _nothing_runs(monkeypatch, tmp_path)
    root = tmp_path / "checkout"
    root.mkdir()
    if digests is not None:
        (root / "engine-digests.json").write_text(digests, encoding="utf-8")
    monkeypatch.setattr(registry, "_REPO_ROOT", root, raising=False)
    if compute is not None:
        monkeypatch.setenv("PHONOMETRY_COMPUTE", compute)
    with pytest.raises(SystemExit) as ended:
        registry.main(argv)
    assert ended.value.code == 2
    assert f"engine-digests.json {said}\n" in capsys.readouterr().err
    assert reached == []


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["--animations", "--audit-only", "--anim", "anim_schroeder", "--jobs", "1"],
        ["--animations", "--anim", "anim_schroeder", "--scratch-dir", "lane"],
    ],
    ids=["figures", "audit", "scratch"],
)
def test_a_run_that_stamps_no_clip_does_not_read_the_engine_digests(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path, argv: list[str]
) -> None:
    """The figures, an audit here and a node's lane write no stamp."""
    import clip_frame_audit

    reached = _nothing_runs(monkeypatch, tmp_path)
    monkeypatch.setattr(registry, "_REPO_ROOT", tmp_path / "no-checkout", raising=False)
    monkeypatch.setattr(
        registry, "_audit_animations", lambda *_, **__: reached.append("audit")
    )
    monkeypatch.setenv(clip_frame_audit.AUDIT_ENV, str(tmp_path / "elsewhere"))
    registry.main(argv)
    assert reached in (["_render_figures"], ["audit"], ["_render_clips"])


@pytest.mark.parametrize("clip", ["anim_a", "anim_schematic"])
@pytest.mark.parametrize("compute", ["cupy,float32", "torch:cuda", "cupy:1"])
def test_a_placement_only_a_gpu_clip_refuses_does_not_stop_clips_that_step_on_numpy(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path, compute: str, clip: str
) -> None:
    """A clip placed on NumPy steps there whatever PHONOMETRY_COMPUTE names, so nothing refuses it.

    ``anim_a`` is placed on ``"cpu"``; ``anim_schematic`` has no field and no
    place in ``_ANIM_DEVICES`` at all.
    """
    started = _a_gpu_here(
        monkeypatch, tmp_path, free=lambda index=0, **_: 8 << 30, need=1 << 20
    )
    monkeypatch.setitem(registry._ANIMATIONS, "anim_schematic", lambda output_dir: None)
    monkeypatch.setattr(registry, "_ANIM_DEVICES", {"anim_a": "cpu"})
    monkeypatch.setenv("PHONOMETRY_COMPUTE", compute)
    registry.main(["--animations", "--anim", clip])
    assert [render[:2] for render in started] == [("alone", [clip])]


def test_a_placement_a_gpu_clip_refuses_stops_a_run_of_every_clip_with_one_among_them(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Every clip asked for, some on a GPU and one on NumPy: the GPU clips refuse a second GPU."""
    import clip_placement

    seen = _four_clips_on_a_gpu_here(monkeypatch, tmp_path)
    probes: list[int] = []
    monkeypatch.setattr(clip_placement, "free_gpu_bytes", _probes_recorded(probes))
    monkeypatch.setenv("PHONOMETRY_COMPUTE", "cupy:1")
    with pytest.raises(SystemExit) as ended:
        registry.main(["--animations", "--jobs", "8"])
    assert ended.value.code == 2
    assert "PHONOMETRY_COMPUTE names GPU 1" in capsys.readouterr().err
    assert probes == []
    assert seen == []


def test_an_audit_the_gpu_stops_leaves_the_findings_it_found_before(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The findings directory is emptied only once the GPU has been divided."""
    started = _a_gpu_here(monkeypatch, tmp_path, free=_no_device, need=1 << 20)
    _an_audit_here(monkeypatch, tmp_path)
    earlier = tmp_path / "audit" / "anim_a.json"
    earlier.parent.mkdir()
    earlier.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit) as ended:
        registry.main(["--animations", "--audit-only", "--anim", "anim_a"])
    assert ended.value.code == 2
    assert "could not be read through CuPy" in capsys.readouterr().err
    assert earlier.read_text(encoding="utf-8") == "{}"
    assert started == []


def test_a_gpu_budget_given_by_hand_to_one_clip_is_kept_whatever_the_default_jobs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """One clip at a time keeps the budget given, even where the default is a pool of workers."""
    import clip_placement

    probes: list[int] = []
    started = _a_gpu_here(
        monkeypatch, tmp_path, free=_probes_recorded(probes), need=1 << 20
    )
    monkeypatch.setattr(registry, "_default_jobs", lambda: 8)
    monkeypatch.setenv(clip_placement.GPU_BYTES_ENV, "4026531840")
    registry.main(["--animations", "--anim", "anim_a"])
    assert probes == []
    assert started == [("alone", ["anim_a"], "4026531840", None)]


@pytest.mark.parametrize("compute", ["cpu", "cupy"], ids=["pool", "gpu-here"])
def test_an_audit_on_a_pool_says_it_inspects_the_frames(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    compute: str,
) -> None:
    """An audit draws and inspects; its log never says it generates the clips."""
    _four_clips_on_a_gpu_here(monkeypatch, tmp_path)
    monkeypatch.setenv("PHONOMETRY_COMPUTE", compute)
    with pytest.raises(SystemExit, match=r"^0$"):
        registry.main(["--animations", "--audit-only", "--jobs", "8"])
    out = capsys.readouterr().out
    findings = (tmp_path / "audit").resolve()
    said = {
        "cpu": "4 clips x 4 variants, 8 jobs",
        "cupy": "3 clips x 4 variants, 2 at a time on the GPU, then 1 alone",
    }[compute]
    assert f"--- Inspecting the frames ({said}), findings into {findings} ---" in out
    assert "Generating animations" not in out
