#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Fail on a public flag a caller can still pass as a bare ``True``.

``bank.filter(x, True)`` says nothing about which of five flags was set, and
the reader of that call site has to open the signature to find out. Worse, a
flag that moves position, or a new one inserted before it, changes what the
same call means without changing a character of it: ``True`` fits every slot.

The rule is one line: a public parameter annotated ``bool`` is keyword-only.
Not "should be documented", not "should be last": the call site has to carry
the name, because the name is the only thing that says which switch was
thrown.

The surface is the one a caller reaches, and it is walked by importing the
package rather than by reading the source tree, for the reason
:mod:`check_parameter_units` gives: a public name can be defined in a private
module, and a scan by file path never sees it. This guard borrows that
walker rather than writing a second one.

ruff has a rule family for this (``FBT001`` and ``FBT002``), and it is
deliberately not selected in ``pyproject.toml``: it reads the source tree, so
it also holds every private helper to a rule that is about the shape of a
published call. The count today is 154 findings inside ``src`` against the
handful that were actually reachable from outside.

:data:`EXEMPT` is the escape hatch, keyed by module, qualified name and
parameter, and each entry carries the reason it is one.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

_SCRIPTS = pathlib.Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from check_parameter_units import Parameter, public_parameters

#: Public boolean parameters that keep their positional slot, with the reason.
#: The bar is a signature a caller cannot reach any other way, not a call site
#: that would be tedious to update.
EXEMPT: dict[tuple[str, str, str], str] = {}


def is_a_flag(parameter: Parameter) -> bool:
    """Whether the parameter is annotated as a boolean.

    The annotation is matched as a word so that ``bool`` is caught inside
    ``bool | None`` and ``Literal[True]`` (the discriminator of an overload
    set) without also catching a name that merely contains the letters.
    """
    tokens = set(
        parameter.annotation.replace("|", " ")
        .replace("[", " ")
        .replace("]", " ")
        .split()
    )
    return bool(tokens & {"bool", "True", "False"})


def offenders() -> tuple[list[Parameter], list[tuple[str, str, str]]]:
    """The flags a caller can still pass by position, and the stale exemptions."""
    loose: list[Parameter] = []
    used: set[tuple[str, str, str]] = set()
    for parameter in public_parameters():
        if not parameter.positional or not is_a_flag(parameter):
            continue
        key = (parameter.module, parameter.qualname, parameter.name)
        if key in EXEMPT:
            used.add(key)
            continue
        loose.append(parameter)
    stale = [key for key in EXEMPT if key not in used]
    return loose, stale


def main() -> int:
    """Report every public flag that can be thrown without naming it."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    loose, stale = offenders()
    if not loose and not stale:
        print("Every public flag has to be named at the call site.")
        return 0
    if loose:
        print("::error::a public flag can be passed as a bare True")
        print(f"{len(loose)} flag(s) keep a positional slot:")
        for parameter in sorted(loose):
            where = f" ({parameter.where})" if parameter.where else ""
            print(f"  {parameter.module}.{parameter.qualname}({parameter.name}){where}")
        print("Move the bare '*' above them, or add a reasoned entry to EXEMPT.")
    if stale:
        print("::error::an exemption names a parameter that is no longer there")
        for module, qualname, name in sorted(stale):
            print(f"  {module}.{qualname}({name})")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
