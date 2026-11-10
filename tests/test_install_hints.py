#  Copyright (c) 2026. Jose Manuel Requena Plens
"""What the library says when a feature needs a package that is not installed.

Every such message names the pip command that installs the extra and the
conda-forge packages that bring the same libraries, since the pip command
followed in a conda environment installs the extra's dependencies from PyPI
beside conda-forge's NumPy. The commands are written out here, not read from
the helper that builds them, so a change to the helper shows as a change to
what the user reads.
"""

from __future__ import annotations

import builtins
import sys
from typing import TYPE_CHECKING

import numpy as np
import pytest

from phonometry import building, filters, io
from phonometry._internal import extras
from phonometry.filters import design
from phonometry.simulation import _backends as bk
from phonometry.simulation.compute import Compute, ComputeImportError

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path
    from types import ModuleType

#: What each message ends with, as the user copies it.
PLOT = (
    'pip install "phonometry[plot]" '
    "(conda: conda install -c conda-forge matplotlib-base)"
)
REPORT = (
    'pip install "phonometry[report]" '
    "(conda: conda install -c conda-forge reportlab svglib)"
)
AUDIO = (
    'pip install "phonometry[audio]" (conda: conda install -c conda-forge pysoundfile)'
)
TORCH = (
    'pip install "phonometry[torch]" '
    "(conda: conda install -c conda-forge pytorch array-api-compat)"
)
TORCH_CPU = (
    "pip install torch --index-url https://download.pytorch.org/whl/cpu "
    'and then pip install "phonometry[torch]" '
    "(conda: conda install -c conda-forge pytorch array-api-compat)"
)
CUPY = "pip install cupy-cuda12x (conda: conda install -c conda-forge cupy)"

FS = 48000


def _block(monkeypatch: pytest.MonkeyPatch, *roots: str) -> None:
    """Make every import of a module under *roots* fail as a missing package does."""
    real_import = builtins.__import__

    def blocked(name: str, *args: object, **kwargs: object) -> ModuleType:
        if name.split(".")[0] in roots:
            msg = f"No module named {name!r}"
            raise ModuleNotFoundError(msg, name=name)
        return real_import(name, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(builtins, "__import__", blocked)


def _message(call: Callable[[], object], error: type[Exception] = ImportError) -> str:
    with pytest.raises(error) as caught:
        call()
    return str(caught.value)


def _tone() -> np.ndarray:
    return np.sin(2 * np.pi * 1000.0 * np.arange(FS // 10) / FS)


def test_a_plot_without_matplotlib_names_pip_and_conda(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bank = filters.octave_filter(_tone(), fs=FS, fraction=1)
    _block(monkeypatch, "matplotlib")
    assert (
        _message(bank.plot) == f"Plotting requires matplotlib. Install it with: {PLOT}"
    )


def test_the_filter_response_view_without_matplotlib_names_pip_and_conda(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block(monkeypatch, "matplotlib")
    message = _message(
        lambda: design._showfilter(
            [],
            [1000.0],
            [1122.0],
            [891.0],
            FS,
            np.array([1]),
            show=True,
            plot_file=None,
        )
    )
    assert message == f"Plotting requires matplotlib. Install it with: {PLOT}"


def _airborne() -> building.AirborneInsulationResult:
    return building.airborne_insulation(
        np.full(16, 95.0), np.full(16, 50.0), np.full(16, 1.0), area=10.0, volume=50.0
    )


def test_a_report_without_reportlab_names_pip_and_conda(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    rating = _airborne()
    _block(monkeypatch, "reportlab")
    message = _message(lambda: rating.report(tmp_path / "rating.pdf"))
    assert (
        message == f"Rendering a report requires reportlab. Install it with: {REPORT}"
    )


def test_a_report_figure_without_matplotlib_names_pip_and_conda(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pytest.importorskip("reportlab")
    rating = _airborne()
    _block(monkeypatch, "matplotlib")
    message = _message(lambda: rating.report(tmp_path / "rating.pdf"))
    assert message == (
        f"Rendering the report figure requires matplotlib. Install it with: {PLOT}"
    )


def test_a_report_figure_without_svglib_names_pip_and_conda(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pytest.importorskip("reportlab")
    pytest.importorskip("matplotlib")
    rating = _airborne()
    _block(monkeypatch, "svglib")
    message = _message(lambda: rating.report(tmp_path / "rating.pdf"))
    assert message == (
        "Embedding the report figure as vector graphics requires svglib. "
        f"Install it with: {REPORT}"
    )


def test_reading_without_soundfile_names_pip_and_conda(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    mp3 = tmp_path / "note.mp3"
    mp3.write_bytes(b"ID3\x04\x00\x00\x00\x00\x00\x00" + bytes(64))
    _block(monkeypatch, "soundfile")
    assert _message(lambda: io.read(mp3)) == (
        f"Reading MPEG audio (MP3) requires python-soundfile. Install it with: {AUDIO}"
    )


def test_writing_flac_without_soundfile_says_writing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Writing a FLAC file, or converting one to FLAC, is no reading of one."""
    wav = tmp_path / "tone.wav"
    io.write(wav, 0.5 * _tone(), FS)
    _block(monkeypatch, "soundfile")
    expected = f"Writing FLAC requires python-soundfile. Install it with: {AUDIO}"
    assert _message(lambda: io.write(tmp_path / "x.flac", 0.5 * _tone(), FS)) == (
        expected
    )
    assert (
        _message(lambda: io.convert(wav, tmp_path / "y.flac", subtype="PCM_24"))
        == expected
    )


def _soundfile_without_its_library(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make ``import soundfile`` fail as it does where libsndfile is missing.

    soundfile 0.14.0 from PyPI in Pyodide, or a wheel whose platform carries no
    packaged libsndfile, raises the OSError of its loader while it imports.
    """
    real_import = builtins.__import__

    def broken(name: str, *args: object, **kwargs: object) -> ModuleType:
        if name.split(".")[0] == "soundfile":
            msg = "sndfile library not found using ctypes.util.find_library"
            raise OSError(msg)
        return real_import(name, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.delitem(sys.modules, "soundfile", raising=False)
    monkeypatch.setattr(builtins, "__import__", broken)


def test_a_soundfile_without_libsndfile_reads_as_the_missing_extra(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _soundfile_without_its_library(monkeypatch)
    message = _message(lambda: io.write(tmp_path / "x.flac", 0.5 * _tone(), FS))
    assert message == (
        "Writing FLAC requires python-soundfile with its libsndfile library, "
        "which did not load (sndfile library not found using "
        f"ctypes.util.find_library). Install it with: {AUDIO}"
    )


@pytest.mark.parametrize(
    ("device", "expected"),
    [("torch:cpu", TORCH_CPU), ("torch:cuda", TORCH), ("torch:mps", TORCH)],
)
def test_a_missing_torch_names_pip_and_conda(
    monkeypatch: pytest.MonkeyPatch, device: str, expected: str
) -> None:
    monkeypatch.setitem(sys.modules, "torch", None)
    dtype = "float32" if device == "torch:mps" else "float64"
    message = _message(
        lambda: bk.backend_for(Compute(device=device, dtype=dtype)),  # type: ignore[arg-type]
        ComputeImportError,
    )
    assert message.endswith(f"; {expected}")


def test_a_missing_cupy_names_pip_and_conda(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "cupy", None)
    message = _message(
        lambda: bk.backend_for(Compute(device="cupy")), ComputeImportError
    )
    assert message.endswith(f"; install the wheel for your CUDA version, e.g. {CUPY}")


def test_every_extra_has_its_conda_forge_packages() -> None:
    """Each extra pyproject declares maps to the packages conda-forge names it by."""
    assert extras.install_hint("plot", "report") == (
        'pip install "phonometry[plot,report]" '
        "(conda: conda install -c conda-forge matplotlib-base reportlab svglib)"
    )
    assert extras.install_hint("perf") == (
        'pip install "phonometry[perf]" (conda: conda install -c conda-forge numba)'
    )
