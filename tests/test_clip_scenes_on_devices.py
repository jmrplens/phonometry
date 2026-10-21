#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The clip scenes keep their fields on the engine's device between captures.

A scene that steps a public FDTD engine can be sent to a GPU
(``scripts/clip_placement.py``). What works on NumPy then fails or crawls
there: a host array added into a device field (CuPy refuses to mix them), a
field written into a host array or pulled out with ``float()`` on every turn
of the loop (a device sync and a copy per step, which can cost more than the
step), a NumPy function called on a device array. This reads every scene for
those, inside each loop that steps an engine one turn at a time (a ``while``
loop or a ``for`` over ``range``), knowing which names hold device arrays and
which hold host arrays from what each name is assigned anywhere in the
function. The way through is the backend: ``_host`` / ``to_host`` at a
capture, the engine's namespace (``xp``) for a reduction, and a host vector
moved to the device once, before the loop.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

_FIELDS_DIR = (
    pathlib.Path(__file__).resolve().parents[1] / "scripts" / "figures" / "fields"
)

#: The arrays an engine stores or derives, read as ``sim.p`` or ``sims[0].vx``.
_FIELD_NAMES = frozenset({"p", "vx", "vy", "txx", "tyy", "txy"})
#: Calls on a backend or an engine that return a device array.
_DEVICE_MAKERS = frozenset({"zeros", "asarray", "index", "collocated"})
#: Calls that return a host array.
_HOST_ARRAYS = frozenset({"_host", "_blanked", "to_host", "host_field"})
#: Calls that return a Python number.
_SCALARS = frozenset({"float", "int", "scalar", "len", "min", "max", "round", "abs"})

#: Scenes not yet moved onto the public engines. Each is taken out as it is.
_NOT_YET: frozenset[str] = frozenset(
    {
        "absorption_placement.py",
        "diffusion.py",
        "dispersion.py",
        "duct_modes.py",
        "ducting.py",
        "elastic.py",
        "expansion_chamber.py",
        "ground_effect.py",
        "halfspace.py",
        "metadiffuser.py",
        "mode_conversion.py",
        "open_end.py",
        "pillar_hall.py",
        "radiation_efficiency.py",
        "refraction.py",
        "room_modes.py",
        "seabed.py",
        "side_branch.py",
        "slit_absorber.py",
        "tubes.py",
    }
)


def _callee(call: ast.Call) -> tuple[str | None, str]:
    """The receiver name (None for a bare function) and the name called."""
    func = call.func
    if isinstance(func, ast.Name):
        return None, func.id
    if isinstance(func, ast.Attribute):
        receiver = func.value.id if isinstance(func.value, ast.Name) else ""
        return receiver, func.attr
    return None, ""


def _is_field(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr in _FIELD_NAMES
        and isinstance(node.value, ast.Name | ast.Subscript)
    )


def _call_kind(call: ast.Call) -> str | None:
    receiver, name = _callee(call)
    if name in _HOST_ARRAYS:
        return "host"
    if receiver == "np":
        return None if name == "errstate" else "host"
    if receiver == "xp" or (name in _DEVICE_MAKERS and receiver not in (None, "np")):
        return "device"
    return None


def _kind(node: ast.AST, device: set[str], host: set[str]) -> str | None:
    """``"device"``, ``"host"`` or None (a number, or something unknown)."""
    if _is_field(node):
        return "device"
    if isinstance(node, ast.Name):
        return "device" if node.id in device else "host" if node.id in host else None
    if isinstance(node, ast.Call):
        return _call_kind(node)
    kinds = {_kind(child, device, host) for child in ast.iter_child_nodes(node)}
    return "device" if "device" in kinds else "host" if "host" in kinds else None


def _assignments(func: ast.AST) -> list[tuple[list[ast.expr], ast.expr]]:
    found: list[tuple[list[ast.expr], ast.expr]] = []
    for node in ast.walk(func):
        if isinstance(node, ast.Assign):
            found.append((list(node.targets), node.value))
        elif isinstance(node, ast.AugAssign | ast.AnnAssign) and node.value is not None:
            found.append(([node.target], node.value))
    return found


def _names(func: ast.AST) -> tuple[set[str], set[str]]:
    """The names a function ever binds to a device array, and to a host array."""
    device: set[str] = set()
    host: set[str] = set()
    pairs = _assignments(func)
    for _ in range(4):  # a few passes reach the fixed point of these scenes
        for targets, value in pairs:
            kind = _kind(value, device, host)
            names = {t.id for t in targets if isinstance(t, ast.Name)}
            (device if kind == "device" else host if kind == "host" else set()).update(
                names
            )
    return device, host


def _steps(node: ast.AST) -> bool:
    return any(
        isinstance(c, ast.Call)
        and isinstance(c.func, ast.Attribute)
        and c.func.attr == "step"
        for c in ast.walk(node)
    )


def _is_turn_loop(node: ast.AST) -> bool:
    if isinstance(node, ast.While):
        return True
    return (
        isinstance(node, ast.For)
        and isinstance(node.iter, ast.Call)
        and _callee(node.iter) == (None, "range")
    )


def _call_problem(node: ast.Call, device: set[str], host: set[str]) -> str | None:
    receiver, name = _callee(node)
    args = [*node.args, *(k.value for k in node.keywords)]
    if (
        receiver == "np"
        and name != "errstate"
        and any(_kind(a, device, host) == "device" for a in args)
    ):
        return f"np.{name} on a device array; use the engine's namespace"
    if (
        receiver is None
        and name in ("float", "int")
        and any(_kind(a, device, host) == "device" for a in node.args)
    ):
        return f"{name}() pulls a device value to the host on every turn"
    if name in ("astype", "copy") and isinstance(node.func, ast.Attribute):
        target = node.func.value
        if not isinstance(target, ast.Call) and _kind(target, device, host) == "device":
            return f".{name}() on a device array; bring it to the host with _host"
    return None


def _write_problem(
    target: ast.expr, value: ast.expr, device: set[str], host: set[str]
) -> str | None:
    kind = _kind(value, device, host)
    if isinstance(target, ast.Subscript):
        base = _kind(target.value, device, host)
        if base != "device" and kind == "device":
            return "a device value written into a host array; bring it to the host with _host"
        if base == "device" and kind == "host":
            return "a host array written into a device array; move it to the device once, before the loop"
    if isinstance(target, ast.Name) and target.id in host and kind == "device":
        return f"{target.id} is a host array and takes a device value; make it with the backend"
    return None


def _node_problem(node: ast.AST, device: set[str], host: set[str]) -> str | None:
    if isinstance(node, ast.Call):
        return _call_problem(node, device, host)
    if isinstance(node, ast.Assign | ast.AugAssign):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        reasons = (_write_problem(t, node.value, device, host) for t in targets)
        return next((r for r in reasons if r), None)
    return None


def _problems_in(func: ast.AST, label: str) -> list[str]:
    device, host = _names(func)
    found: set[str] = set()
    loops = (n for n in ast.walk(func) if _is_turn_loop(n) and _steps(n))
    for loop in loops:
        for node in ast.walk(loop):
            reason = _node_problem(node, device, host)
            if reason:
                found.add(f"{label}:{node.lineno}: {reason}")
    return sorted(found)


def problems(source: str, label: str) -> list[str]:
    """Every host round trip inside a stepping loop of *source*."""
    tree = ast.parse(source)
    found: list[str] = []
    for func in ast.walk(tree):
        if isinstance(func, ast.FunctionDef):
            found.extend(_problems_in(func, label))
    return sorted(set(found))


_SCENES = sorted(p for p in _FIELDS_DIR.glob("*.py") if p.name != "__init__.py")


@pytest.mark.parametrize("path", _SCENES, ids=lambda p: p.name)
def test_a_scene_keeps_its_fields_on_the_device_between_captures(
    path: pathlib.Path,
) -> None:
    found = problems(path.read_text(encoding="utf-8"), path.name)
    if path.name in _NOT_YET:
        assert found, (
            f"{path.name} keeps its fields on the device now; take it out of _NOT_YET"
        )
        return
    assert not found, "\n".join(found)


def test_every_kind_of_round_trip_is_seen() -> None:
    source = """
def build(sim, frames):
    taper = np.hanning(10)
    trace = np.empty(10)
    energy = np.zeros_like(sim.p)
    for i in range(10):
        sim.step()
        sim.vy[3] += taper * np.sin(i)
        trace[i] = sim.p[1, 2]
        level = float(sim.p[0, 0])
        frames.append(sim.p[::2, ::2].astype(np.float32))
        energy += sim.p**2
        np.maximum(trace, np.abs(sim.p[0]), out=trace)
"""
    reasons = [line.split(": ", 1)[1] for line in problems(source, "scene")]
    assert sorted(reasons) == sorted(
        [
            "a host array written into a device array; move it to the device once, before the loop",
            "a device value written into a host array; bring it to the host with _host",
            "float() pulls a device value to the host on every turn",
            ".astype() on a device array; bring it to the host with _host",
            "energy is a host array and takes a device value; make it with the backend",
            "np.abs on a device array; use the engine's namespace",
        ]
    )


def test_the_way_through_the_backend_is_clean() -> None:
    source = """
def build(sim, frames):
    backend = sim._backend
    xp = backend.xp
    taper = backend.asarray(np.hanning(10))
    history = backend.zeros((10,))
    energy = backend.zeros((4, 4))
    for i in range(10):
        sim.step()
        sim.vy[3] += taper * xp.sin(1.0 * i)
        history[i] = sim.p[1, 2]
        energy += sim.p**2
        if i % 2 == 0:
            frames.append(_host(sim, sim.p[::2, ::2]))
            with np.errstate(divide="ignore"):
                level = 10.0 * xp.log10(energy)
"""
    assert problems(source, "scene") == []


def test_a_loop_over_frequencies_is_not_a_stepping_turn() -> None:
    source = """
def build(make):
    for f in (100.0, 200.0):
        c = np.full((4, 4), 343.0)
        sim = make(c, f)
        for _ in range(10):
            sim.step()
"""
    assert problems(source, "scene") == []


#: The engines a figure may build, and the functions that build one; each is
#: told where to step.
_ENGINES = frozenset(
    {
        "FDTD2D",
        "ElasticFDTD2D",
        "fdtd_simulation",
        "elastic_fdtd_simulation",
        "write_fdtd_animation",
        "write_elastic_fdtd_animation",
    }
)
_FIGURE_MODULES = sorted(_FIELDS_DIR.parent.rglob("*.py"))


def unplaced_engines(source: str, label: str) -> list[str]:
    """Every engine *source* builds, or simulation it runs, without ``compute=``.

    Without it an engine follows ``use()`` and ``PHONOMETRY_COMPUTE``: a
    shell set up to render the clips on a GPU would send it there, past the
    registry (with a host in the variable, a static figure's simulation would
    even be sent to the node), and on a node lane it would open a CUDA
    context in a child forked from a parent that already holds one.
    """
    found: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        name = _callee(node)[1]
        if name in _ENGINES and not any(k.arg == "compute" for k in node.keywords):
            found.append(f"{label}:{node.lineno}: {name} without compute=")
    return sorted(found)


@pytest.mark.parametrize(
    "path", _FIGURE_MODULES, ids=lambda p: str(p.relative_to(_FIELDS_DIR.parent))
)
def test_every_engine_a_figure_builds_is_told_where_to_step(path: pathlib.Path) -> None:
    if path.parent == _FIELDS_DIR and path.name in _NOT_YET:
        return
    found = unplaced_engines(path.read_text(encoding="utf-8"), path.name)
    assert not found, "\n".join(found)


def test_an_engine_built_without_a_placement_is_seen() -> None:
    source = """
def poster(cp, cs, dx):
    a = FDTD2D(343.0, 0.01, shape=(3, 8)).dt
    b = fdtd2d.FDTD2D(343.0, 0.01, shape=(3, 8))
    c = simulation.ElasticFDTD2D(cp, cs, dx)
    d = FDTD2D(343.0, 0.01, shape=(3, 8), compute=Compute()).dt
    e = simulation.fdtd_simulation(run)
    f = simulation.fdtd_simulation(run, compute=Compute())
    g = simulation.write_elastic_fdtd_animation("x.webm", elastic_run)
"""
    assert [line.split(": ", 1)[1] for line in unplaced_engines(source, "scene")] == [
        "FDTD2D without compute=",
        "FDTD2D without compute=",
        "ElasticFDTD2D without compute=",
        "fdtd_simulation without compute=",
        "write_elastic_fdtd_animation without compute=",
    ]
