#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The scripts that run where NumPy is not installed, held to it.

Most CI jobs install the scientific stack, but a good third of them install
nothing at all: a checker that only reads text has no reason to wait a minute
for NumPy, SciPy and Matplotlib. Those jobs work only for as long as every
module their script reaches, sibling helpers included, imports the standard
library alone.

That broke once without any job noticing. ``assets_dir.py`` says where the
published clips are checked out, and it read ``.env`` through the GPU runner,
which imports NumPy at the top. ``check_animation_freshness.py`` asks
``assets_dir`` for that directory, so a check whose own docstring promises it
"rides in any job" died on ``import numpy`` in a container that only builds
the site. The one job that ran it in CI installs everything, so nothing there
could see it.

So the list is not kept by hand. :func:`_numpy_free_scripts` reads it from the
workflows: every script a job runs (directly or through a ``make`` target)
when that job installs nothing, or installs only named tools that are not the
project and not a requirements file. :data:`_DECLARED` adds the scripts that
promise the same outside CI. Each is imported in a fresh interpreter that
refuses NumPy. Where the job installs nothing, that interpreter also starts
with ``-S``, which leaves out site-packages entirely, so what is importable is
the standard library and the repository's own scripts, as on a bare runner.
Where the job installs tools, site-packages stays, because those tools live
there, and only NumPy is refused: that proves the script does not reach
NumPy, not that it reaches nothing beyond the tools its job installs.
"""

from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys

import pytest
import yaml

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
_WORKFLOWS = _ROOT / ".github" / "workflows"
_MAKEFILE = _ROOT / "Makefile"

if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import repo_env

#: Scripts that must run with nothing installed although no CI job proves it,
#: each with the call that exercises the path at stake. The clip freshness
#: check says it rides in any job, and without ``--manifest`` it asks
#: ``assets_dir`` where the clips are, which reads ``.env``. The resolver
#: itself is what ``make assets`` calls on a fresh clone, before anything is
#: installed.
_DECLARED = {
    "scripts/check_animation_freshness.py": "module.published(None)",
    "scripts/assets_dir.py": "module.clips_dir()",
}

#: A script invocation in a workflow step or a Makefile recipe.
_INVOCATION = re.compile(
    r"(?:\bpython3?|\$\(PYTHON\))\s+(?:-\S+\s+)*((?:\.github/)?scripts/[\w/.-]+\.py)"
)

#: A ``make`` call in a workflow step, for the targets a job runs.
_MAKE = re.compile(r"\bmake\s+([\w-]+)")

#: A ``pip install`` and what follows it on the line.
_PIP_INSTALL = re.compile(r"\bpip3?\s+install\s+([^\n]*)")

#: What in a ``pip install`` brings NumPy with it: a requirements file, the
#: project itself (editable or not, with or without extras) or NumPy by name.
_PULLS_NUMPY = re.compile(r"(?:^|\s)[\"']?(?:-r|-e|\.|phonometry|numpy)")

#: Imports one script by path, as ``__name__ != "__main__"`` so its entry
#: point does not run, with the scripts directory on the path as every
#: script arranges for itself, then runs *then* against it. NumPy is refused
#: outright, for the jobs that install tools and so keep site-packages.
_PROBE = """
import importlib.abc, importlib.util, pathlib, sys

target = pathlib.Path(sys.argv[1])


class Refuse(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.partition(".")[0] == "numpy":
            raise ImportError(f"{{fullname}} is not installed where this runs")
        return None


sys.meta_path.insert(0, Refuse())
sys.path[:0] = [str(target.parent), {scripts!r}]
spec = importlib.util.spec_from_file_location("_probe", target)
module = importlib.util.module_from_spec(spec)
sys.modules["_probe"] = module
spec.loader.exec_module(module)
{then}
"""


def _recipe_scripts(target: str) -> set[str]:
    """The scripts the Makefile recipe of *target* runs."""
    found: set[str] = set()
    inside = False
    for line in _MAKEFILE.read_text(encoding="utf-8").splitlines():
        if re.match(rf"^{re.escape(target)}\s*:", line):
            inside = True
        elif inside and line.startswith("\t"):
            found.update(_INVOCATION.findall(line))
        elif inside:
            break
    return found


def _numpy_free_scripts() -> dict[str, bool]:
    """Every script a NumPy-free job runs, and whether that job installs nothing.

    The value is ``True`` when some job running the script installs nothing at
    all (only the standard library may be imported) and ``False`` when every
    such job installs tools that are not NumPy (NumPy alone is refused).
    """
    scripts: dict[str, bool] = {}
    for workflow in sorted(_WORKFLOWS.glob("*.yml")):
        parsed = yaml.safe_load(workflow.read_text(encoding="utf-8"))
        for job in (parsed.get("jobs") or {}).values():
            text = "\n".join(
                str(step.get("run", ""))
                for step in job.get("steps", [])
                if isinstance(step, dict)
            )
            installs = _PIP_INSTALL.findall(text)
            if any(_PULLS_NUMPY.search(arguments) for arguments in installs):
                continue
            ran = set(_INVOCATION.findall(text))
            for target in _MAKE.findall(text):
                ran |= _recipe_scripts(target)
            for script in ran:
                scripts[script] = scripts.get(script, False) or not installs
    return scripts


def _probe(
    script: str, *, bare: bool, then: str = ""
) -> subprocess.CompletedProcess[str]:
    """Import *script*, and run *then*, with NumPy refused.

    *bare* also starts the interpreter with ``-S``: no site-packages at all,
    the standard library and the repository's scripts only. Without it the
    development environment stays visible, NumPy apart.
    """
    program = _PROBE.format(scripts=str(_SCRIPTS), then=then)
    flags = ["-S", "-E"] if bare else ["-E"]
    return subprocess.run(  # noqa: S603 - the interpreter running this suite
        [sys.executable, *flags, "-c", program, str(_ROOT / script)],
        capture_output=True,
        text=True,
        check=False,
        cwd=_ROOT,
        env={**os.environ, "PHONOMETRY_ASSETS_DIR": str(_ROOT / "no-clips-here")},
    )


_FOUND = _numpy_free_scripts()


def test_the_workflows_are_read_and_not_found_empty() -> None:
    """A derivation that silently found nothing would pass every case below.

    One script from each kind of job: one that installs nothing, the docs
    build that runs the system ``python3``, and the stub check whose job
    installs packaging tools and no NumPy. And one it must leave out.
    """
    assert _FOUND.get("scripts/check_errata_evidence.py") is True
    assert _FOUND.get("scripts/generate_llms.py") is True
    assert _FOUND.get("scripts/check_stub_metadata.py") is False
    assert "scripts/check_figures.py" not in _FOUND


@pytest.mark.parametrize("script", sorted(_FOUND))
def test_a_script_a_numpy_free_job_runs_imports_without_numpy(script: str) -> None:
    result = _probe(script, bare=_FOUND[script])
    assert result.returncode == 0, (
        f"{script} needs more than its job has:\n{result.stderr}"
    )


@pytest.mark.parametrize("script", sorted(_DECLARED))
def test_a_script_that_promises_to_run_anywhere_does(script: str) -> None:
    result = _probe(script, bare=True, then=_DECLARED[script])
    assert result.returncode == 0, f"{script} needs more than nothing:\n{result.stderr}"


def test_the_real_environment_wins_over_the_env_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """An exported variable beats ``.env``; the ones it leaves unset are loaded."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        '# comment line\nPHONO_GPU_HOST=file-host\nPHONO_GPU_NAME="lab GPU"\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("PHONO_GPU_HOST", "env-host")
    # Guarantee the variable is absent and restored either way.
    monkeypatch.setenv("PHONO_GPU_NAME", "sentinel")
    monkeypatch.delenv("PHONO_GPU_NAME")
    values = repo_env.load_env(env_file)
    assert values == {"PHONO_GPU_HOST": "file-host", "PHONO_GPU_NAME": "lab GPU"}
    assert os.environ["PHONO_GPU_HOST"] == "env-host"  # real env wins
    assert os.environ["PHONO_GPU_NAME"] == "lab GPU"  # quotes stripped


def _worktree_of(main: pathlib.Path, worktree: pathlib.Path, *, relative: bool) -> None:
    """Lay out *main* as a checkout and *worktree* as a worktree linked to it."""
    common = main / ".git" / "worktrees" / "x"
    common.mkdir(parents=True)
    worktree.mkdir()
    pointer = os.path.relpath(common, worktree) if relative else str(common)
    (worktree / ".git").write_text(f"gitdir: {pointer}\n", encoding="utf-8")


@pytest.mark.parametrize("pointer", ["absolute", "relative"])
def test_a_worktree_reads_the_env_file_of_its_main_checkout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path, pointer: str
) -> None:
    """``.env`` is untracked, so a worktree has none and must read its checkout's.

    If this fallback broke, a render started from a worktree would find no GPU
    settings and encode VP9 on the CPU, and the GPU parity tests, which skip
    when no ``.env`` is found, would skip rather than fail. The pointer is
    resolved against the worktree, so the directory the run starts in must not
    matter either.
    """
    main, worktree = tmp_path / "main", tmp_path / "worktree"
    _worktree_of(main, worktree, relative=pointer == "relative")
    (main / ".env").write_text("PHONO_GPU_HOST=main-host\n", encoding="utf-8")
    monkeypatch.setattr(repo_env, "_REPO_ROOT", worktree)
    monkeypatch.chdir(tmp_path)
    assert repo_env.env_file() == (main / ".env").resolve()


def test_an_env_file_beside_the_checkout_wins(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """A worktree that does carry a ``.env`` reads its own, not its checkout's."""
    main, worktree = tmp_path / "main", tmp_path / "worktree"
    _worktree_of(main, worktree, relative=False)
    (main / ".env").write_text("PHONO_GPU_HOST=main-host\n", encoding="utf-8")
    (worktree / ".env").write_text("PHONO_GPU_HOST=own-host\n", encoding="utf-8")
    monkeypatch.setattr(repo_env, "_REPO_ROOT", worktree)
    assert repo_env.env_file() == worktree / ".env"


def test_a_checkout_without_an_env_file_reads_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """A main checkout with no ``.env`` names its own absent file, read as empty."""
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr(repo_env, "_REPO_ROOT", tmp_path)
    assert repo_env.env_file() == tmp_path / ".env"
    assert repo_env.load_env(repo_env.env_file()) == {}
