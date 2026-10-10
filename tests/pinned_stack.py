#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The test modules tied to the pinned figure stack, read without importing them.

The figure, diagram and badge tooling compares against artefacts drawn on the
pinned stack in ``requirements*.txt``, and some of it imports names an older
matplotlib does not have. Its test modules declare that at module level::

    pytestmark = pytest.mark.pinned_stack

The minimum-versions CI job runs ``pytest --without-pinned-stack`` at the
dependency floors. A mark alone cannot keep such a module out of that run: a
mark is read after the module is imported, and the import is what fails. So
``conftest.py`` reads the declaration from the source with :func:`declares`
and leaves the module out before it is imported.
"""

from __future__ import annotations

import ast

#: The mark a module carries, and the option that leaves those modules out.
MARK = "pinned_stack"
OPTION = "--without-pinned-stack"


def declares(source: str) -> bool:
    """Whether a module's own ``pytestmark`` names :data:`MARK`."""
    for node in ast.parse(source).body:
        if not isinstance(node, ast.Assign | ast.AnnAssign):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(isinstance(t, ast.Name) and t.id == "pytestmark" for t in targets):
            continue
        if node.value is not None and any(
            isinstance(sub, ast.Attribute) and sub.attr == MARK
            for sub in ast.walk(node.value)
        ):
            return True
    return False
