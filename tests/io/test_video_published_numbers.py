#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every number the video guide, the CHANGELOG and the docstrings print is a default of the code."""

from __future__ import annotations

import inspect
import logging
from pathlib import Path

import pytest

from phonometry import io
from phonometry.io import _video_encoders as ve
from phonometry.io._video import video_request
from phonometry.io._video_quality import GIF_PALETTE
from phonometry.simulation import (
    AnimationFrame,
    _video_job,
    video,
    write_elastic_fdtd_animation,
    write_fdtd_animation,
)

_ROOT = Path(__file__).resolve().parents[2]

#: The most colours a GIF's palette takes, at any preset.
_COLOURS = max(colours for colours, _ in GIF_PALETTE.values())
_WIDTH, _HEIGHT = AnimationFrame().size
_FPS = f"{video._DEFAULT_FPS:g}"
_FLOOR = f"{video._MIN_WIDTH} by {video._MIN_HEIGHT}"
_FLOOR_ES = f"{video._MIN_WIDTH} por {video._MIN_HEIGHT}"
_DIGIT_WIDTH = f"{float(video._DIGIT_WIDTH):g}"
_VAAPI_DEVICE = f"`{io.VideoOptions().vaapi_device}`"
_VAAPI_DEFAULT = f'`"{io.VideoOptions().vaapi_device}"`'

#: The seconds a run's last frame comes before for the floor to hold: the
#: time, in milliseconds, of _FLOOR_DIGITS digits before the point. A floor
#: of another count of digits fails here, at collection, until the prose and
#: this map say the new time.
_FLOOR_SECONDS = {10: {"en": "ten", "es": "diez"}}[10**video._FLOOR_DIGITS // 1000]

#: The bytes a pixel a node's video may take, as the prose spells them. A
#: ceiling the map does not hold fails here, at collection, until the guide,
#: the docstring and this map say the new number.
_SPELLED = {"en": {2: "two", 8: "eight"}, "es": {2: "dos", 8: "ocho"}}
_PRESET_BYTES = _video_job._PRESET_BYTES_PER_PIXEL
_CALLER_BYTES = _video_job._CALLER_BYTES_PER_PIXEL
_SLACK_MIB = f"{_video_job._CONTAINER_SLACK / 2**20:g} MiB"

#: The phrases each language's guide prints, built from the code's own values.
_GUIDE_PHRASES: dict[str, tuple[str, ...]] = {
    "en": (
        f"{_WIDTH} by {_HEIGHT} pixels",
        f"{_FPS} frames per second",
        f"{_FLOOR} pixels",
        f"{_COLOURS} colours",
        f"{_SPELLED['en'][_PRESET_BYTES]} bytes a pixel",
        f"{_SPELLED['en'][_CALLER_BYTES]} when",
        f"plus {_SLACK_MIB}",
        f"| `vaapi_device` | the path of the GPU device VAAPI encodes on | {_VAAPI_DEFAULT} |",
        f"(through {_VAAPI_DEVICE}, the first GPU,",
        f"whose last frame comes before {_FLOOR_SECONDS['en']} seconds",
    ),
    "es": (
        f"{_WIDTH} por {_HEIGHT} píxeles",
        f"{_FPS} fotogramas por segundo",
        f"{_FLOOR_ES} píxeles",
        f"{_COLOURS} colores",
        f"{_SPELLED['es'][_PRESET_BYTES]} bytes por píxel",
        f"{_SPELLED['es'][_CALLER_BYTES]} cuando",
        f"más {_SLACK_MIB}",
        f"| `vaapi_device` | la ruta del dispositivo de GPU en el que codifica VAAPI | {_VAAPI_DEFAULT} |",
        f"(a través de {_VAAPI_DEVICE}, la primera GPU,",
        f"cuyo último fotograma llega antes de {_FLOOR_SECONDS['es']} segundos",
    ),
}

#: The guide's pages and their language.
_PAGES = {
    "site/src/content/docs/io/videos.mdx": "en",
    "docs/io/videos.md": "en",
    "site/src/content/docs/es/io/videos.mdx": "es",
}

#: What the CHANGELOG prints of the defaults.
_CHANGELOG_PHRASES: tuple[str, ...] = (
    f"up to {_COLOURS} colours",
    f"{_WIDTH} by {_HEIGHT} pixels by default",
    f"at least {_FLOOR} pixels",
    f"{_VAAPI_DEVICE}, the first one",
    f"whose last frame comes at {_FLOOR_SECONDS['en']} seconds or later",
)

#: What each documented object prints of its defaults: functions, records and
#: the writers' module, whose docstring the API reference publishes.
_DOCSTRING_PHRASES: list[tuple[object, tuple[str, ...]]] = [
    (io.write_video, (f"up to {_COLOURS} colours",)),
    (io.VideoOptions, (f'``"{io.VideoOptions().vaapi_device}"`` (default)',)),
    (
        write_fdtd_animation,
        (
            f"{_WIDTH} by {_HEIGHT} pixels",
            f"{_FPS} frames per second",
            f"comes at {_FLOOR_SECONDS['en']} seconds or later",
        ),
    ),
    (
        write_elastic_fdtd_animation,
        (
            f"{_WIDTH} by {_HEIGHT} pixels",
            f"{_FPS} frames per second",
            f"comes at {_FLOOR_SECONDS['en']} seconds or later",
        ),
    ),
    (
        AnimationFrame,
        (
            f"at least {_FLOOR},",
            f"(default ``({_WIDTH}, {_HEIGHT})``)",
            f"narrower than {video._MIN_WIDTH} or lower than {video._MIN_HEIGHT} pixels",
            f"comes before {_FLOOR_SECONDS['en']} seconds",
        ),
    ),
    (
        video,
        (
            f"at least {_FLOOR} pixels",
            f"about {_DIGIT_WIDTH} pixels wider",
            f"comes before {_FLOOR_SECONDS['en']} seconds",
        ),
    ),
    (
        _video_job.video_byte_cap,
        (
            f"{_SPELLED['en'][_PRESET_BYTES].capitalize()} bytes a pixel",
            f"{_SPELLED['en'][_CALLER_BYTES].capitalize()} when",
            f"Plus {_SLACK_MIB}",
        ),
    ),
]

#: What each row of the API table prints of the defaults.
_API_ROW_PHRASES: dict[str, tuple[str, ...]] = {
    "VideoOptions": (
        f"{_FPS} for a simulation video",
        f"(Default: `'{io.VideoOptions().vaapi_device}'`, the first GPU)",
    ),
    "write_fdtd_animation": (
        f"{_WIDTH} by {_HEIGHT} pixels",
        f"{_FPS} frames per second",
    ),
    "write_elastic_fdtd_animation": (
        f"{_WIDTH} by {_HEIGHT} pixels",
        f"{_FPS} frames per second",
    ),
    "AnimationFrame": (
        f"at least {_FLOOR},",
        f"about {_DIGIT_WIDTH} pixels a digit",
        f"(Default: `({_WIDTH}, {_HEIGHT})`)",
    ),
}


def _flat(text: str) -> str:
    """*text* with every run of whitespace made one space: the pages are hard-wrapped."""
    return " ".join(text.split())


@pytest.mark.parametrize(("page", "language"), sorted(_PAGES.items()))
def test_the_guide_prints_the_code_s_defaults(page: str, language: str) -> None:
    text = _flat((_ROOT / page).read_text(encoding="utf-8"))
    missing = [phrase for phrase in _GUIDE_PHRASES[language] if phrase not in text]
    assert missing == [], f"{page} does not print {missing}"


def test_the_changelog_prints_the_code_s_defaults() -> None:
    text = _flat((_ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))
    missing = [phrase for phrase in _CHANGELOG_PHRASES if phrase not in text]
    assert missing == [], f"CHANGELOG.md does not print {missing}"


@pytest.mark.parametrize(("documented", "phrases"), _DOCSTRING_PHRASES)
def test_the_docstrings_print_the_code_s_defaults(
    documented: object, phrases: tuple[str, ...]
) -> None:
    text = _flat(inspect.getdoc(documented) or "")
    missing = [phrase for phrase in phrases if phrase not in text]
    assert missing == [], (
        f"{getattr(documented, '__name__', documented)} does not print {missing}"
    )


@pytest.mark.parametrize(("name", "phrases"), sorted(_API_ROW_PHRASES.items()))
def test_the_api_rows_print_the_code_s_defaults(
    name: str, phrases: tuple[str, ...]
) -> None:
    rows = (
        (_ROOT / "docs/reference/api/index.md").read_text(encoding="utf-8").splitlines()
    )
    (row,) = [line for line in rows if line.startswith(f"| `{name}` |")]
    missing = [phrase for phrase in phrases if phrase not in row]
    assert missing == [], f"the API row of {name} does not print {missing}"


def _quoted() -> tuple[str, ...]:
    """What the guide quotes the code saying: the VAAPI device, a log line, an error.

    Each made by the code itself: the device from the arguments VAAPI gets,
    the log line from the choice of an encoder (its trial stood in for), the
    error from the refusal of a codec the container does not hold.
    """
    (device,) = [
        argument
        for argument in ve.video_arguments(
            ve.EncoderChoice("vaapi", "h264", "h264_vaapi"),
            quality="standard",
            options=(),
            container="mp4",
            width=64,
            height=64,
            pad_color="#ffffff",
        ).before_input
        if argument.startswith("/")
    ]
    vp9 = io.VideoOptions(codec="vp9")
    with pytest.raises(ValueError, match="codec='vp9'") as refused:
        video_request(_ROOT / "wave.mp4", vp9)
    return device, str(refused.value)


def _logged(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> str:
    """The line the guide's logging example prints, as logging.basicConfig() writes it."""
    monkeypatch.setattr(ve, "trial", lambda *_args, **_kwargs: True)
    ffmpeg = ve.FFmpeg(path="ffmpeg", version="", encoders=frozenset({"libx264"}))
    with caplog.at_level(logging.INFO, logger="phonometry.io"):
        ve.choose(
            ffmpeg, encoder="cpu", codec="h264", container="mp4", width=64, height=64
        )
    (record,) = caplog.records
    return f"{record.levelname}:{record.name}:{record.getMessage()}"


@pytest.mark.parametrize("page", sorted(_PAGES))
def test_the_guide_quotes_what_the_code_says(
    page: str, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    text = _flat((_ROOT / page).read_text(encoding="utf-8"))
    quoted = (*_quoted(), _logged(monkeypatch, caplog))
    assert quoted[-1] == "INFO:phonometry.io:writing mp4 with libx264 (cpu, h264)"
    missing = [phrase for phrase in quoted if phrase not in text]
    assert missing == [], f"{page} does not quote {missing}"
