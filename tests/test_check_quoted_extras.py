#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every install command quotes the requirement that carries extras.

zsh reads the brackets of an extras requirement as a glob and stops with
"no matches found" before pip runs, so a command copied from the
documentation, a docstring or a message must quote it.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parents[1] / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_quoted_extras as cqe

# Joined at run time, so this file holds no command of its own to name.
_EXTRA = "[" + "torch" + "]"


@pytest.mark.parametrize(
    "line",
    [
        f"pip install phonometry{_EXTRA}",
        f"pip install -U phonometry{_EXTRA}",
        f"pip3 install phonometry{_EXTRA}",
        f"python -m pip install phonometry{_EXTRA}",
        f"uv pip install phonometry{_EXTRA}",
        f"uv add phonometry{_EXTRA}",
        f"pipx install phonometry{_EXTRA}",
        f"Install it with: ``pip install phonometry{_EXTRA}``",
        f"pip install -e .{_EXTRA}",
        f'pip install "phonometry{_EXTRA}" numpy{_EXTRA}',
        f"%pip install phonometry{_EXTRA}>=4",
        f'    "pip install phonometry{_EXTRA}      # + torch",',
        f'"text": "pip install phonometry{_EXTRA}"',
    ],
)
def test_an_unquoted_requirement_with_extras_is_named(line: str) -> None:
    (problem,) = cqe.problems(line + "\n", "page.md")
    assert problem.startswith("page.md:1: ")


@pytest.mark.parametrize(
    "line",
    [
        f'pip install "phonometry{_EXTRA}"',
        f"pip install 'phonometry{_EXTRA}'",
        f'pip install -e ".{_EXTRA}"',
        f'pip install "phonometry{_EXTRA}>=4"',
        f'python -m pip install --no-cache-dir "dist/phonometry-$VERSION-py3-none-any.whl{_EXTRA}"',
        f'"text": "pip install \\"phonometry{_EXTRA}\\""',
        "pip install phonometry",
        "pip install phonometry, then read [docs] for the rest",
        f"the phonometry{_EXTRA} extra brings torch",
        f"installs the `phonometry{_EXTRA}` extra",
        "pip install torch --index-url https://download.pytorch.org/whl/cpu",
        f"pip install phonometry{_EXTRA}   # zsh: no matches found: phonometry{_EXTRA}",
    ],
)
def test_a_quoted_requirement_or_no_command_passes(line: str) -> None:
    """The last line shows zsh's own refusal on purpose, as a rule's counterexample."""
    assert cqe.problems(line + "\n", "page.md") == []


def test_a_requirement_wrapped_after_pip_install_is_named_by_its_first_line() -> None:
    text = (
        "        Requires matplotlib (``pip install\n"
        f"        phonometry{_EXTRA}``); returns the axes.\n"
    )
    assert [p.split(": ", 1)[0] for p in cqe.problems(text, "a.py")] == ["a.py:1"]


def test_a_wrapped_requirement_that_is_quoted_passes() -> None:
    text = (
        "        Requires matplotlib (``pip install\n"
        f'        "phonometry{_EXTRA}"``); returns the axes.\n'
    )
    assert cqe.problems(text, "a.py") == []


@pytest.mark.parametrize(
    "text",
    [
        "pip install phonometry\n>>> levels[0]\n",
        'pip install numpy\npython -c "import sys; print(sys.argv[0])"\n',
    ],
)
def test_a_command_whole_on_its_line_takes_no_bracket_from_the_next(text: str) -> None:
    assert cqe.problems(text, "a.md") == []


def test_a_requirement_wrapped_after_an_option_is_named() -> None:
    text = f"python -m pip install -U\nphonometry{_EXTRA}\n"
    assert [p.split(": ", 1)[0] for p in cqe.problems(text, "a.md")] == ["a.md:1"]


def test_a_command_on_the_next_line_is_named_once_on_its_own_line() -> None:
    text = f"pip install phonometry\npip install phonometry{_EXTRA}\n"
    assert [p.split(": ", 1)[0] for p in cqe.problems(text, "a.md")] == ["a.md:2"]


def test_each_problem_names_its_line() -> None:
    text = f'pip install "phonometry{_EXTRA}"\n\npip install phonometry{_EXTRA}\n'
    assert [p.split(": ", 1)[0] for p in cqe.problems(text, "a.md")] == ["a.md:3"]


def test_tests_are_not_read() -> None:
    root = pathlib.Path(__file__).resolve().parents[1]
    assert not any(
        p.relative_to(root).as_posix().startswith("tests/")
        for p in cqe.tracked_files(root)
    )


def test_the_files_a_command_is_copied_from_are_read() -> None:
    root = pathlib.Path(__file__).resolve().parents[1]
    read = {p.relative_to(root).as_posix() for p in cqe.tracked_files(root)}
    assert {
        "README.md",
        "CHANGELOG.md",
        "llms.txt",
        "Makefile",
        "scripts/generate_llms.py",
        "site/src/data/home.ts",
        "src/phonometry/__init__.py",
        ".github/workflows/python-app.yml",
    } <= read


def test_main_names_each_command_and_fails(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "page.md").write_text(
        f"pip install phonometry{_EXTRA}\n", encoding="utf-8"
    )
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, timeout=60)
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "page.md"], check=True, timeout=60
    )
    assert cqe.main([str(tmp_path)]) == 1
    assert (
        capsys.readouterr().out
        == f"::error::page.md:1: pip install phonometry{_EXTRA}\n"
    )


def test_the_repository_quotes_every_install_command() -> None:
    root = pathlib.Path(__file__).resolve().parents[1]
    found = [
        problem
        for path in cqe.tracked_files(root)
        for problem in cqe.problems(
            path.read_text(encoding="utf-8", errors="replace"),
            path.relative_to(root).as_posix(),
        )
    ]
    assert not found, "\n".join(found)
