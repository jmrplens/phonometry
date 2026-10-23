#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A stand-in for ffmpeg, run as a program, for the video writer's tests.

The video writer finds ffmpeg where matplotlib looks for it, runs it with an
argument list and streams raw frames into its stdin, so the honest stand-in
is a program too: a launcher (a shell script, or a ``.cmd`` file on Windows)
that runs this file with the test's own interpreter. What it does is set by a
JSON file the test writes and may rewrite between two calls:

* ``version``: the first line of ``-version``;
* ``encoders``: the encoder names ``-encoders`` lists (compiled in);
* ``working``: the ones an encode succeeds with (the others fail the way an
  NVENC encoder fails on a machine without the GPU);
* ``die_after_frames``: stop reading and fail after this many frames;
* ``first_frame``: a path the first frame's raw bytes are copied to.

Every run appends one line of JSON to the log the helper names: the argument
list, what kind of run it was and how many whole frames arrived on stdin. A
real encode writes the container's first bytes to its output, so a test can
tell a WebM from an MP4 from a GIF without a real encoder.

The ``.cmd`` launcher passes the arguments through ``%*``; the writer's
arguments carry no ``^``, ``&``, ``|``, ``<``, ``>`` or ``%``, the characters
``cmd.exe`` would read.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pytest

#: The environment variable that names the spec file.
SPEC_VARIABLE = "PHONOMETRY_FAKE_FFMPEG"

#: What a fresh fake does unless the test says otherwise.
DEFAULTS: dict[str, Any] = {
    "version": "ffmpeg version 7.1-fake Copyright (c) 2000-2026",
    "encoders": ["libsvtav1", "libvpx-vp9", "libx264", "libx265", "av1_nvenc"],
    "working": ["libsvtav1", "libvpx-vp9", "libx264", "libx265"],
    "die_after_frames": None,
    "first_frame": None,
}

#: The first bytes each muxer writes.
_MAGIC = {
    "webm": b"\x1a\x45\xdf\xa3fake-webm",
    "mp4": b"\x00\x00\x00\x18ftypisomfake-mp4",
    "gif": b"GIF89afake-gif",
}


def _value(argv: list[str], flag: str) -> str | None:
    """The argument after the last *flag* in *argv*, or ``None``."""
    found = None
    for index, item in enumerate(argv[:-1]):
        if item == flag:
            found = argv[index + 1]
    return found


def _log(spec: dict[str, Any], record: dict[str, Any]) -> None:
    with Path(spec["log"]).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def _encode(spec: dict[str, Any], argv: list[str]) -> int:
    width, height = (int(n) for n in (_value(argv, "-s") or "0x0").split("x"))
    frame_bytes = max(width * height * 4, 1)
    name = _value(argv, "-c:v")
    limit = spec.get("die_after_frames")
    received = 0
    first: bytes | None = None
    stdin = sys.stdin.buffer
    while True:
        if limit is not None and received >= limit * frame_bytes:
            break
        chunk = stdin.read(frame_bytes)
        if not chunk:
            break
        if first is None:
            first = chunk
        received += len(chunk)
    output = argv[-1]
    record = {
        "kind": "encode",
        "argv": argv,
        "frames": received // frame_bytes,
        "remainder": received % frame_bytes,
    }
    _log(spec, record)
    if first is not None and spec.get("first_frame"):
        Path(spec["first_frame"]).write_bytes(first)
    if limit is not None and received >= limit * frame_bytes:
        sys.stderr.write(
            "fake ffmpeg: the muxer failed after the frames it was allowed\n"
        )
        return 1
    if name is not None and name not in spec["working"]:
        sys.stderr.write(f"fake ffmpeg: Error while opening encoder {name}\n")
        return 1
    if output != "-":
        Path(output).write_bytes(_MAGIC[_value(argv, "-f") or "webm"])
    return 0


def main(argv: list[str]) -> int:
    """Behave as the spec file says; return the exit status."""
    spec = json.loads(Path(os.environ[SPEC_VARIABLE]).read_text(encoding="utf-8"))
    if "-version" in argv:
        _log(spec, {"kind": "version", "argv": argv, "frames": 0, "remainder": 0})
        sys.stdout.write(spec["version"] + "\n")
        return 0
    if "-encoders" in argv:
        _log(spec, {"kind": "encoders", "argv": argv, "frames": 0, "remainder": 0})
        sys.stdout.write("Encoders:\n V..... = Video\n ------\n")
        for name in spec["encoders"]:
            sys.stdout.write(f" V....D {name:<20} fake {name}\n")
        return 0
    return _encode(spec, argv)


@dataclass(frozen=True)
class FakeFFmpeg:
    """A fake ffmpeg installed for one test: where it is and what it saw."""

    launcher: Path
    spec_file: Path
    log: Path

    def calls(self) -> list[dict[str, Any]]:
        """Every run, in order."""
        if not self.log.exists():
            return []
        return [
            json.loads(line)
            for line in self.log.read_text(encoding="utf-8").splitlines()
            if line
        ]

    def trials(self) -> list[dict[str, Any]]:
        """The one-frame trial encodes (to ffmpeg's null muxer)."""
        return [
            c for c in self.calls() if c["kind"] == "encode" and c["argv"][-1] == "-"
        ]

    def encodes(self) -> list[dict[str, Any]]:
        """The encodes that wrote a file."""
        return [
            c for c in self.calls() if c["kind"] == "encode" and c["argv"][-1] != "-"
        ]

    def update(self, **spec: object) -> None:
        """Change what the fake does from its next run on."""
        current = json.loads(self.spec_file.read_text(encoding="utf-8"))
        current.update(spec)
        self.spec_file.write_text(json.dumps(current), encoding="utf-8")


def install(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, **spec: object
) -> FakeFFmpeg:
    """Write a fake ffmpeg into *tmp_path* and point matplotlib at it."""
    import matplotlib as mpl

    spec_file = tmp_path / "fake-ffmpeg.json"
    log = tmp_path / "fake-ffmpeg.log"
    spec_file.write_text(
        json.dumps({**DEFAULTS, **spec, "log": str(log)}), encoding="utf-8"
    )
    script = Path(__file__).resolve()
    if sys.platform == "win32":
        launcher = tmp_path / "ffmpeg.cmd"
        launcher.write_text(f'@"{sys.executable}" "{script}" %*\r\n', encoding="utf-8")
    else:
        launcher = tmp_path / "ffmpeg"
        launcher.write_text(
            f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n', encoding="utf-8"
        )
        launcher.chmod(0o755)
    monkeypatch.setenv(SPEC_VARIABLE, str(spec_file))
    # On PATH too, first, so that a child process (a node's runner started
    # by a fake ssh) that looks for plain "ffmpeg" finds the same fake.
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ.get('PATH', '')}")
    monkeypatch.setitem(mpl.rcParams, "animation.ffmpeg_path", str(launcher))
    return FakeFFmpeg(launcher=launcher, spec_file=spec_file, log=log)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
