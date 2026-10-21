#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Where a clip's wave field is computed, and what that must not touch.

A clip's device is a registry entry (``figures.registry._ANIM_DEVICES``) read
through ``scripts/clip_placement.py``. These tests hold the rules: a clip
measured to step faster on NumPy steps on NumPy whatever the environment
says; a GPU clip takes the CuPy GPU ``PHONOMETRY_COMPUTE`` names (the first
one; another is chosen with ``CUDA_VISIBLE_DEVICES``) and steps on NumPy
when none is named; any other GPU library is refused, as the clips' GPU
fields are measured on CuPy only; the clips are computed in float64; the
memory a render lane may hold is set on CuPy's pool, and the RAM it may
hold is read from its budget or from what the machine has available; and
the table is outside every clip's fingerprint, because where a field is
computed is held to the NumPy field by measurement, not by the fingerprint.
"""

from __future__ import annotations

import pathlib
import sys
import types

import pytest

_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_ROOT / "scripts"))

import animation_fingerprint as fp
import clip_placement

from phonometry.simulation import Compute

# The registry imports the whole figure stack, which the pinned job owns.
pytestmark = pytest.mark.pinned_stack


@pytest.fixture
def devices(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """A device table of three clips, one per kind."""
    from figures import registry

    table = {"anim_cpu": "cpu", "anim_gpu": "gpu", "anim_whole": "gpu-whole"}
    monkeypatch.setattr(registry, "_ANIM_DEVICES", table)
    monkeypatch.delenv("PHONOMETRY_COMPUTE", raising=False)
    monkeypatch.delenv(clip_placement.GPU_BYTES_ENV, raising=False)
    monkeypatch.delenv(clip_placement.HOST_BYTES_ENV, raising=False)
    return table


def test_a_cpu_clip_steps_on_numpy_whatever_the_environment_names(
    devices: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PHONOMETRY_COMPUTE", "cupy:1")
    assert clip_placement.compute_for("anim_cpu") == Compute(device="cpu")


@pytest.mark.parametrize("clip", ["anim_gpu", "anim_whole"])
def test_a_gpu_clip_takes_the_gpu_the_environment_names(
    devices: dict[str, str], monkeypatch: pytest.MonkeyPatch, clip: str
) -> None:
    """Building the record imports nothing, so this runs without CuPy."""
    monkeypatch.setenv("PHONOMETRY_COMPUTE", "cupy")
    assert clip_placement.compute_for(clip) == Compute(device="cupy")


def test_a_gpu_clip_with_no_gpu_named_steps_on_numpy(devices: dict[str, str]) -> None:
    assert clip_placement.compute_for("anim_gpu") == Compute(device="cpu")


@pytest.mark.parametrize("named", ["torch:cuda", "torch:cpu", "torch:mps,float32"])
def test_a_gpu_library_other_than_cupy_is_refused_for_a_clip(
    devices: dict[str, str], monkeypatch: pytest.MonkeyPatch, named: str
) -> None:
    """The clips' GPU fields are measured against NumPy's on CuPy only."""
    monkeypatch.setenv("PHONOMETRY_COMPUTE", named)
    with pytest.raises(ValueError, match=r"NumPy or CuPy"):
        clip_placement.compute_for("anim_gpu")


def test_a_gpu_other_than_the_first_is_refused_for_a_clip(
    devices: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A scene's own device arithmetic runs on CuPy's current device, GPU 0."""
    monkeypatch.setenv("PHONOMETRY_COMPUTE", "cupy:1")
    with pytest.raises(ValueError, match=r"CUDA_VISIBLE_DEVICES=1"):
        clip_placement.compute_for("anim_gpu")


def test_float32_in_the_environment_is_refused_for_a_clip(
    devices: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PHONOMETRY_COMPUTE", "cupy,float32")
    with pytest.raises(ValueError, match=r"clips are computed in float64"):
        clip_placement.compute_for("anim_gpu")


def test_a_clip_without_a_device_is_a_key_error(devices: dict[str, str]) -> None:
    with pytest.raises(KeyError, match=r"anim_nowhere"):
        clip_placement.device_of("anim_nowhere")


def test_every_field_clip_has_a_device_and_nothing_else_does() -> None:
    from figures import registry

    assert registry._ANIM_DEVICES.keys() == registry._ANIM_FIELDS.keys()
    assert set(registry._ANIM_DEVICES.values()) <= {"cpu", "gpu", "gpu-whole"}


def test_the_device_table_is_in_no_fingerprint() -> None:
    """Where a field is computed is held to the NumPy field by measurement, not here."""
    sources = fp.Sources(_ROOT)
    for clip, entry in sources.clips().items():
        closure = sources.closure([entry, *fp._EXTRA_ROOTS])
        assert ("figures.registry", "_ANIM_DEVICES") not in closure, clip


class _Pool:
    def __init__(self, log: list[str]) -> None:
        self._log = log

    def free_all_blocks(self) -> None:
        self._log.append("free")

    def set_limit(self, *, size: int) -> None:
        self._log.append(f"limit {size}")


def _fake_cupy(log: list[str]) -> types.ModuleType:
    module = types.ModuleType("cupy")
    pool = _Pool(log)
    module.get_default_memory_pool = lambda: pool  # type: ignore[attr-defined]
    module.get_default_pinned_memory_pool = lambda: pool  # type: ignore[attr-defined]

    class _Device:
        def __init__(self, index: int) -> None:
            log.append(f"device {index}")

        def __enter__(self) -> None:
            return None

        def __exit__(self, *exc: object) -> None:
            return None

    module.cuda = types.SimpleNamespace(Device=_Device)  # type: ignore[attr-defined]
    return module


def test_the_pools_are_freed_when_cupy_is_loaded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    log: list[str] = []
    monkeypatch.setitem(sys.modules, "cupy", _fake_cupy(log))
    clip_placement.release_device()
    assert log == ["free", "free"]


def test_nothing_is_freed_when_cupy_was_never_imported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delitem(sys.modules, "cupy", raising=False)
    clip_placement.release_device()


def test_the_lane_budget_is_set_on_the_pool_of_the_named_gpu(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    log: list[str] = []
    monkeypatch.setitem(sys.modules, "cupy", _fake_cupy(log))
    monkeypatch.setenv(clip_placement.GPU_BYTES_ENV, "4000000000")
    clip_placement.limit_device_memory(Compute(device="cupy", device_index=1))
    assert log == ["device 1", "limit 4000000000"]


def test_a_gpu_clip_s_placement_holds_the_lane_budget(
    devices: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A scene asks for its placement and nothing else; the budget comes with it."""
    log: list[str] = []
    monkeypatch.setitem(sys.modules, "cupy", _fake_cupy(log))
    monkeypatch.setenv("PHONOMETRY_COMPUTE", "cupy")
    monkeypatch.setenv(clip_placement.GPU_BYTES_ENV, "4000000000")
    assert clip_placement.compute_for("anim_gpu") == Compute(device="cupy")
    assert log == ["device 0", "limit 4000000000"]


@pytest.mark.parametrize("text", ["four", "0", "-5"])
def test_a_lane_budget_that_is_not_a_positive_count_is_refused(
    monkeypatch: pytest.MonkeyPatch, text: str
) -> None:
    monkeypatch.setenv(clip_placement.GPU_BYTES_ENV, text)
    compute = Compute(device="cupy")
    with pytest.raises(ValueError, match=r"PHONOMETRY_CLIP_GPU_BYTES"):
        clip_placement.limit_device_memory(compute)


def test_a_budget_on_numpy_is_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(clip_placement.GPU_BYTES_ENV, "4000000000")
    monkeypatch.delitem(sys.modules, "cupy", raising=False)
    clip_placement.limit_device_memory(Compute(device="cpu"))
    assert "cupy" not in sys.modules


def test_a_lane_s_ram_budget_wins_over_what_the_machine_has(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(clip_placement.HOST_BYTES_ENV, "7000000000")
    assert clip_placement.host_bytes() == 7_000_000_000


def test_without_a_budget_the_ram_is_what_the_machine_has_available(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    meminfo = tmp_path / "meminfo"
    meminfo.write_text(
        "MemTotal: 27000000 kB\nMemAvailable: 13000000 kB\n", encoding="utf-8"
    )
    monkeypatch.delenv(clip_placement.HOST_BYTES_ENV, raising=False)
    monkeypatch.setattr(clip_placement, "_MEMINFO", meminfo)
    monkeypatch.setattr(clip_placement, "_CGROUP_LIMIT", tmp_path / "absent")
    assert clip_placement.host_bytes() == 13_000_000 * 1024


def test_a_container_limit_below_the_machine_s_ram_is_the_budget(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    meminfo = tmp_path / "meminfo"
    meminfo.write_text("MemAvailable: 13000000 kB\n", encoding="utf-8")
    limit = tmp_path / "memory.max"
    limit.write_text("4294967296\n", encoding="utf-8")
    monkeypatch.delenv(clip_placement.HOST_BYTES_ENV, raising=False)
    monkeypatch.setattr(clip_placement, "_MEMINFO", meminfo)
    monkeypatch.setattr(clip_placement, "_CGROUP_LIMIT", limit)
    assert clip_placement.host_bytes() == 4294967296


@pytest.mark.parametrize("text", ["lots", "0", "-1"])
def test_a_ram_budget_that_is_not_a_positive_count_is_refused(
    monkeypatch: pytest.MonkeyPatch, text: str
) -> None:
    monkeypatch.setenv(clip_placement.HOST_BYTES_ENV, text)
    with pytest.raises(ValueError, match=r"PHONOMETRY_CLIP_HOST_BYTES"):
        clip_placement.host_bytes()
