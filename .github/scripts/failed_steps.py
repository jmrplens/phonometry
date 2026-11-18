"""Name each step of a job that failed, as an annotation on the checks page.

A job that groups many guards stays one line in a pull request's checks,
and a red one used to say only that something in it failed: which guard
it was took opening the log and finding the red step among thirty. This
runs last in such a job, when an earlier step failed, and writes one
``::error`` annotation per failed step, titled by the step's id, so the
checks page names every guard that failed without opening anything.

It reads the job's ``steps`` context, handed to it as JSON in the
``STEPS`` variable (``${{ toJSON(steps) }}``). That context holds only the
steps that carry an ``id``, which is why every guard of a grouped job has
one; a failed step without one is reported as such, so a job never reads
as failed for no named reason.

Standard library only, and run as ``python3``: it has to work in the jobs
that install nothing, and after a setup step failed and left no other
Python on the path. A failed checkout is the one setup failure it never
sees: the step that runs it waits for the checkout, since without one there
is no script to run and the job would fail a second time.
"""

from __future__ import annotations

import json
import os
import sys

#: What the workflow sets the variable to; an empty context is ``{}``.
_VARIABLE = "STEPS"


def _escape_property(text: str) -> str:
    """Escape *text* for the property part of a workflow command."""
    return (
        text.replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
        .replace(":", "%3A")
        .replace(",", "%2C")
    )


def _escape_data(text: str) -> str:
    """Escape *text* for the message part of a workflow command."""
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def failed(steps: object) -> list[str]:
    """The ids of the steps whose outcome is ``failure``, in the job's order.

    *steps* is the parsed ``steps`` context: a mapping from each step's id
    to an object with its ``outcome`` and ``conclusion``. The outcome is
    read, not the conclusion, because a step allowed to fail
    (``continue-on-error``) concludes as a success and still failed.
    """
    if not isinstance(steps, dict):
        msg = f"the steps context is a {type(steps).__name__}, not a mapping"
        raise TypeError(msg)
    return [
        str(step_id)
        for step_id, step in steps.items()
        if isinstance(step, dict) and step.get("outcome") == "failure"
    ]


def workflow_commands(steps: object) -> list[str]:
    """The workflow commands that name each failed step of *steps*."""
    names = failed(steps)
    if not names:
        return [
            "::error title=Unnamed step::A step without an id failed, or the job "
            "failed outside its steps; its log says which."
        ]
    return [
        f"::error title={_escape_property(name)}::"
        + _escape_data(f"The step {name} failed; its log says why.")
        for name in names
    ]


def main(environ: dict[str, str] | None = None) -> int:
    """Print the annotations for the context in ``STEPS``; always exits 0.

    The job has already failed by the time this runs, so the exit status
    adds nothing; a context that cannot be read is said in a warning
    rather than turned into a second failure.
    """
    environ = dict(os.environ) if environ is None else environ
    raw = environ.get(_VARIABLE)
    if raw is None:
        print(f"::warning::{_VARIABLE} is not set, so no failed step can be named.")
        return 0
    try:
        lines = workflow_commands(json.loads(raw))
    except (ValueError, TypeError) as error:
        print(
            "::warning::"
            + _escape_data(f"{_VARIABLE} holds no steps context ({error}).")
        )
        return 0
    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
