#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Reactive silencers by the four-pole (transmission-matrix) method.

A reactive silencer controls noise by *reflecting* it back to the source with
impedance discontinuities -- sudden area changes and side branches -- rather
than by dissipating it in absorptive material. The one-dimensional plane-wave
theory represents each acoustic element by a 2x2 **transfer (four-pole)
matrix** relating the sound pressure ``p`` and volume velocity ``S u`` at its
two ends, and a compound silencer is the ordered matrix product of its
elements (Bies, Hansen & Howard, *Engineering Noise Control* 5th ed., §8.8-8.9;
Munjal, *Acoustics of Ducts and Mufflers*).

**Transfer matrix** (Bies Eq. (8.133)), state vector ``[p, S u]`` with the
characteristic acoustic impedance ``Z = rho c / S``. The plane-wave element for
a straight duct of length ``L`` and area ``S`` is (Bies Eq. (8.143), no flow)

    [[ cos(kL),              j (rho c / S) sin(kL) ],
     [ j (S / rho c) sin(kL), cos(kL)              ]],    k = omega / c,

and a **side branch** of acoustic impedance ``Z_b`` is the shunt element
(Bies Eq. (8.144))

    [[ 1,       0 ],
     [ 1 / Z_b, 1 ]].

**Transmission loss** from the compound matrix ``T`` (Bies Eq. (8.141), no
flow; reduces to Eq. (8.148) for equal inlet/outlet areas):

    TL = 10 log10[ (Z1 / Zn) (1/4) | T11 + T12 / Zn + Z1 T21 + (Z1 / Zn) T22 |^2 ]

with ``Z1 = rho c / S_in`` and ``Zn = rho c / S_out``. ``TL`` is the intrinsic
attenuation for an anechoic termination. The **insertion loss** for a source of
internal impedance ``Z_s`` radiating into a termination impedance ``Z_r`` is
the extra attenuation of inserting the silencer in place of a direct
connection,

    IL = 20 log10 | (T11 Z_r + T12 + Z_s Z_r T21 + Z_s T22) / (Z_s + Z_r) |,

which is ``0`` when the silencer reduces to a through connection (``T = I``)
and equals the transmission loss for the anechoic reference
``Z_s = rho c / S_in``, ``Z_r = rho c / S_out``.

**Simple expansion chamber.** A chamber of area ``S_exp`` and length ``L``
between pipes of area ``S_duct`` has the closed-form transmission loss (Bies
Eq. (8.111)) with area ratio ``m = S_exp / S_duct``

    TL = 10 log10[ 1 + (1/4) (m - 1/m)^2 sin^2(kL) ],

peaking at ``10 log10[1 + (1/4)(m - 1/m)^2]`` when ``kL = pi/2, 3pi/2, ...`` and
dropping to ``0`` at ``kL = n pi`` (no dissipation). The four-pole product
reproduces this exactly, and the machinery extends to side-branch (Helmholtz,
quarter-wave) and extended-tube resonators that the closed form cannot cover.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .._internal.validation import require_non_negative, require_positive

if TYPE_CHECKING:
    from matplotlib.axes import Axes

#: Reference air properties at 20 degC, 101.325 kPa.
_C_AIR = 343.0
_RHO_AIR = 1.206

_Complex = NDArray[np.complex128]


def _frequencies(frequencies: ArrayLike) -> NDArray[np.float64]:
    """Validate a strictly positive, finite 1-D frequency grid (Hz)."""
    f = np.atleast_1d(np.asarray(frequencies, dtype=np.float64))
    if f.ndim != 1 or f.size == 0:
        raise ValueError("'frequencies' must be a non-empty 1-D array.")
    if np.any(f <= 0.0) or not np.all(np.isfinite(f)):
        raise ValueError("'frequencies' must be positive and finite.")
    return f


def duct_matrix(
    frequencies: ArrayLike,
    length: float,
    area: float,
    *,
    speed_of_sound: float = _C_AIR,
    density: float = _RHO_AIR,
) -> _Complex:
    """Four-pole matrix of a straight duct (Bies Eq. (8.143), no flow).

    :param frequencies: Frequencies ``f``, Hz (1-D array).
    :param length: Duct length ``L``, m.
    :param area: Cross-sectional area ``S``, m2.
    :param speed_of_sound: Speed of sound ``c``, m/s.
    :param density: Air density ``rho``, kg/m3.
    :return: A ``(n_freq, 2, 2)`` complex transfer-matrix array.
    """
    f = _frequencies(frequencies)
    length = require_non_negative(length, "length")
    area = require_positive(area, "area")
    c = require_positive(speed_of_sound, "speed_of_sound")
    rho = require_positive(density, "density")
    k = 2.0 * np.pi * f / c
    z = rho * c / area
    cos = np.cos(k * length)
    sin = np.sin(k * length)
    t = np.empty((f.size, 2, 2), dtype=np.complex128)
    t[:, 0, 0] = cos
    t[:, 0, 1] = 1j * z * sin
    t[:, 1, 0] = 1j * sin / z
    t[:, 1, 1] = cos
    return t


def shunt_matrix(branch_impedance: ArrayLike) -> _Complex:
    """Four-pole matrix of a side branch of impedance ``Z_b`` (Bies Eq. (8.144)).

    :param branch_impedance: Acoustic impedance ``Z_b`` of the branch,
        Pa s/m3 (1-D complex array over frequency).
    :return: A ``(n_freq, 2, 2)`` complex transfer-matrix array.
    """
    zb = np.atleast_1d(np.asarray(branch_impedance, dtype=np.complex128))
    if zb.ndim != 1 or zb.size == 0:
        raise ValueError("'branch_impedance' must be a non-empty 1-D array.")
    t = np.zeros((zb.size, 2, 2), dtype=np.complex128)
    t[:, 0, 0] = 1.0
    # A lossless branch at exact resonance has Z_b -> 0 (it shorts the duct);
    # 1/Z_b -> infinity gives the ideal infinite attenuation there.
    with np.errstate(divide="ignore", invalid="ignore"):
        t[:, 1, 0] = 1.0 / zb
    t[:, 1, 1] = 1.0
    return t


def cascade(*matrices: _Complex) -> _Complex:
    """Cascade element four-pole matrices from inlet to outlet.

    The compound matrix is the ordered product ``T1 @ T2 @ ... @ Tn`` (the
    state at the inlet equals the compound matrix times the state at the
    outlet), broadcast over the frequency axis.

    :param matrices: One or more ``(n_freq, 2, 2)`` arrays sharing ``n_freq``.
    :return: The compound ``(n_freq, 2, 2)`` array.
    """
    if not matrices:
        raise ValueError("cascade() needs at least one matrix.")
    total = matrices[0]
    for m in matrices[1:]:
        total = np.matmul(total, m)
    return total


def transmission_loss(
    transfer_matrix: _Complex,
    *,
    inlet_area: float,
    outlet_area: float,
    speed_of_sound: float = _C_AIR,
    density: float = _RHO_AIR,
) -> NDArray[np.float64]:
    """Transmission loss of a four-pole element (Bies Eq. (8.141), no flow).

    :param transfer_matrix: A ``(n_freq, 2, 2)`` compound matrix.
    :param inlet_area: Inlet pipe area ``S_in``, m2.
    :param outlet_area: Outlet pipe area ``S_out``, m2.
    :param speed_of_sound: Speed of sound ``c``, m/s.
    :param density: Air density ``rho``, kg/m3.
    :return: The transmission loss per frequency, dB.
    """
    s_in = require_positive(inlet_area, "inlet_area")
    s_out = require_positive(outlet_area, "outlet_area")
    c = require_positive(speed_of_sound, "speed_of_sound")
    rho = require_positive(density, "density")
    z1 = rho * c / s_in
    zn = rho * c / s_out
    t11 = transfer_matrix[:, 0, 0]
    t12 = transfer_matrix[:, 0, 1]
    t21 = transfer_matrix[:, 1, 0]
    t22 = transfer_matrix[:, 1, 1]
    term = t11 + t12 / zn + z1 * t21 + (z1 / zn) * t22
    return np.asarray(
        10.0 * np.log10((z1 / zn) * 0.25 * np.abs(term) ** 2),
        dtype=np.float64,
    )


def insertion_loss(
    transfer_matrix: _Complex,
    *,
    source_impedance: ArrayLike,
    radiation_impedance: ArrayLike,
) -> NDArray[np.float64]:
    """Insertion loss of a four-pole element for given end impedances.

    The attenuation from inserting the element in place of a direct (zero
    length) connection between a source of internal impedance ``Z_s`` and a
    radiation (termination) impedance ``Z_r``:

        IL = 20 log10 | (T11 Z_r + T12 + Z_s Z_r T21 + Z_s T22) /
                        (Z_s + Z_r) |.

    :param transfer_matrix: A ``(n_freq, 2, 2)`` compound matrix.
    :param source_impedance: Source internal acoustic impedance ``Z_s``,
        Pa s/m3 (scalar or per-frequency, real or complex).
    :param radiation_impedance: Termination/radiation acoustic impedance
        ``Z_r``, Pa s/m3 (scalar or per-frequency).
    :return: The insertion loss per frequency, dB.
    """
    n = transfer_matrix.shape[0]
    zs = np.broadcast_to(
        np.asarray(source_impedance, dtype=np.complex128), (n,)
    )
    zr = np.broadcast_to(
        np.asarray(radiation_impedance, dtype=np.complex128), (n,)
    )
    t11 = transfer_matrix[:, 0, 0]
    t12 = transfer_matrix[:, 0, 1]
    t21 = transfer_matrix[:, 1, 0]
    t22 = transfer_matrix[:, 1, 1]
    num = t11 * zr + t12 + zs * zr * t21 + zs * t22
    return np.asarray(
        20.0 * np.log10(np.abs(num / (zs + zr))), dtype=np.float64
    )


def helmholtz_impedance(
    frequencies: ArrayLike,
    neck_area: float,
    neck_length: float,
    cavity_volume: float,
    *,
    resistance: float = 0.0,
    speed_of_sound: float = _C_AIR,
    density: float = _RHO_AIR,
) -> _Complex:
    """Acoustic impedance of a Helmholtz side branch (Bies Eq. (8.152)).

    ``Z = R + j( rho omega l_e / S_neck - rho c^2 / (omega V) )`` with acoustic
    mass ``rho l_e / S_neck`` and compliance ``V / (rho c^2)``; the resonance
    ``f_0 = (c / 2 pi) sqrt(S_neck / (l_e V))`` (Bies Eq. (8.46)) is where the
    reactance vanishes and the branch shorts the duct.

    :param frequencies: Frequencies ``f``, Hz (1-D array).
    :param neck_area: Neck cross-sectional area ``S_neck``, m2.
    :param neck_length: Effective neck length ``l_e`` (with end corrections), m.
    :param cavity_volume: Cavity volume ``V``, m3.
    :param resistance: Acoustic resistance ``R``, Pa s/m3 (default 0, lossless).
    :param speed_of_sound: Speed of sound ``c``, m/s.
    :param density: Air density ``rho``, kg/m3.
    :return: The complex branch impedance per frequency, Pa s/m3.
    """
    f = _frequencies(frequencies)
    s_neck = require_positive(neck_area, "neck_area")
    le = require_positive(neck_length, "neck_length")
    vol = require_positive(cavity_volume, "cavity_volume")
    r = require_non_negative(resistance, "resistance")
    c = require_positive(speed_of_sound, "speed_of_sound")
    rho = require_positive(density, "density")
    omega = 2.0 * np.pi * f
    reactance = rho * omega * le / s_neck - rho * c**2 / (omega * vol)
    return np.asarray(r + 1j * reactance, dtype=np.complex128)


def quarter_wave_impedance(
    frequencies: ArrayLike,
    length: float,
    area: float,
    *,
    speed_of_sound: float = _C_AIR,
    density: float = _RHO_AIR,
) -> _Complex:
    """Acoustic impedance of a closed quarter-wave side branch (Bies Eq. (8.146)).

    ``Z = -j (rho c / S) cot(k l_e)``; the reactance vanishes at
    ``l_e = lambda / 4`` (``f = c / 4 l_e``), where the closed tube presents a
    pressure node and shorts the duct.

    :param frequencies: Frequencies ``f``, Hz (1-D array).
    :param length: Effective tube length ``l_e`` (with end correction), m.
    :param area: Tube cross-sectional area ``S``, m2.
    :param speed_of_sound: Speed of sound ``c``, m/s.
    :param density: Air density ``rho``, kg/m3.
    :return: The complex branch impedance per frequency, Pa s/m3.
    """
    f = _frequencies(frequencies)
    le = require_positive(length, "length")
    area = require_positive(area, "area")
    c = require_positive(speed_of_sound, "speed_of_sound")
    rho = require_positive(density, "density")
    k = 2.0 * np.pi * f / c
    z = rho * c / area
    # At the half-wave frequencies (k l_e = n pi) the closed tube is transparent
    # (Z -> infinity); the divide-by-zero is expected and its shunt 1/Z is 0.
    with np.errstate(divide="ignore", invalid="ignore"):
        zb = -1j * z / np.tan(k * le)
    return np.asarray(zb, dtype=np.complex128)


@dataclass(frozen=True)
class ReactiveSilencerResult:
    """Transmission and insertion loss of a reactive silencer over frequency.

    :ivar frequencies: Frequencies ``f``, Hz.
    :ivar transmission_loss: Transmission loss per frequency, dB.
    :ivar insertion_loss: Insertion loss per frequency, dB, or ``None`` when no
        source/radiation impedance was supplied.
    :ivar transfer_matrix: The compound ``(n_freq, 2, 2)`` four-pole matrix.
    :ivar kind: A short label of the device (e.g. ``"expansion chamber"``).
    :ivar resonances: Notable resonance frequencies, Hz (e.g. the resonator
        tuning frequency), or ``None``.
    """

    frequencies: np.ndarray
    transmission_loss: np.ndarray
    insertion_loss: np.ndarray | None
    transfer_matrix: np.ndarray
    kind: str
    resonances: np.ndarray | None = None

    def plot(self, ax: "Axes | None" = None, **kwargs: Any) -> "Axes":
        """Plot the transmission (and insertion) loss against frequency.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from .._plot.noise_control import plot_reactive_silencer

        return plot_reactive_silencer(self, ax=ax, **kwargs)


def _result(
    f: NDArray[np.float64],
    t: _Complex,
    *,
    inlet_area: float,
    outlet_area: float,
    c: float,
    rho: float,
    source_impedance: ArrayLike | None,
    radiation_impedance: ArrayLike | None,
    kind: str,
    resonances: NDArray[np.float64] | None = None,
) -> ReactiveSilencerResult:
    """Assemble a :class:`ReactiveSilencerResult` from a compound matrix."""
    tl = transmission_loss(
        t, inlet_area=inlet_area, outlet_area=outlet_area,
        speed_of_sound=c, density=rho,
    )
    il: NDArray[np.float64] | None = None
    if source_impedance is not None and radiation_impedance is not None:
        il = insertion_loss(
            t, source_impedance=source_impedance,
            radiation_impedance=radiation_impedance,
        )
    return ReactiveSilencerResult(
        frequencies=f,
        transmission_loss=tl,
        insertion_loss=il,
        transfer_matrix=t,
        kind=kind,
        resonances=resonances,
    )


def expansion_chamber(
    frequencies: ArrayLike,
    length: float,
    chamber_area: float,
    pipe_area: float,
    *,
    speed_of_sound: float = _C_AIR,
    density: float = _RHO_AIR,
    source_impedance: ArrayLike | None = None,
    radiation_impedance: ArrayLike | None = None,
) -> ReactiveSilencerResult:
    """Simple expansion-chamber silencer (Bies Eq. (8.111) / four-pole).

    :param frequencies: Frequencies ``f``, Hz (1-D array).
    :param length: Chamber length ``L``, m.
    :param chamber_area: Chamber cross-sectional area ``S_exp``, m2.
    :param pipe_area: Inlet/outlet pipe area ``S_duct``, m2.
    :param speed_of_sound: Speed of sound ``c``, m/s.
    :param density: Air density ``rho``, kg/m3.
    :param source_impedance: Optional source impedance ``Z_s`` for the
        insertion loss, Pa s/m3.
    :param radiation_impedance: Optional radiation impedance ``Z_r`` for the
        insertion loss, Pa s/m3.
    :return: A :class:`ReactiveSilencerResult` (its ``transmission_loss``
        equals the closed form ``10 log10[1 + (1/4)(m - 1/m)^2 sin^2(kL)]``).
    """
    f = _frequencies(frequencies)
    c = require_positive(speed_of_sound, "speed_of_sound")
    rho = require_positive(density, "density")
    require_positive(chamber_area, "chamber_area")
    require_positive(pipe_area, "pipe_area")
    t = duct_matrix(f, length, chamber_area, speed_of_sound=c, density=rho)
    return _result(
        f, t, inlet_area=pipe_area, outlet_area=pipe_area, c=c, rho=rho,
        source_impedance=source_impedance,
        radiation_impedance=radiation_impedance, kind="expansion chamber",
    )


def helmholtz_resonator(
    frequencies: ArrayLike,
    duct_area: float,
    neck_area: float,
    neck_length: float,
    cavity_volume: float,
    *,
    resistance: float = 0.0,
    speed_of_sound: float = _C_AIR,
    density: float = _RHO_AIR,
    source_impedance: ArrayLike | None = None,
    radiation_impedance: ArrayLike | None = None,
) -> ReactiveSilencerResult:
    """Side-branch Helmholtz resonator on a duct (Bies Eqs. (8.144), (8.152)).

    :param frequencies: Frequencies ``f``, Hz (1-D array).
    :param duct_area: Main-duct cross-sectional area ``S_d``, m2.
    :param neck_area: Resonator neck area ``S_neck``, m2.
    :param neck_length: Effective neck length ``l_e``, m.
    :param cavity_volume: Cavity volume ``V``, m3.
    :param resistance: Neck acoustic resistance ``R``, Pa s/m3 (default 0).
    :param speed_of_sound: Speed of sound ``c``, m/s.
    :param density: Air density ``rho``, kg/m3.
    :param source_impedance: Optional source impedance ``Z_s``, Pa s/m3.
    :param radiation_impedance: Optional radiation impedance ``Z_r``, Pa s/m3.
    :return: A :class:`ReactiveSilencerResult`; ``resonances`` holds
        ``f_0 = (c / 2 pi) sqrt(S_neck / (l_e V))``.
    """
    f = _frequencies(frequencies)
    c = require_positive(speed_of_sound, "speed_of_sound")
    rho = require_positive(density, "density")
    s_d = require_positive(duct_area, "duct_area")
    zb = helmholtz_impedance(
        f, neck_area, neck_length, cavity_volume, resistance=resistance,
        speed_of_sound=c, density=rho,
    )
    t = shunt_matrix(zb)
    f0 = c / (2.0 * np.pi) * np.sqrt(neck_area / (neck_length * cavity_volume))
    return _result(
        f, t, inlet_area=s_d, outlet_area=s_d, c=c, rho=rho,
        source_impedance=source_impedance,
        radiation_impedance=radiation_impedance,
        kind="Helmholtz resonator",
        resonances=np.array([f0], dtype=np.float64),
    )


def quarter_wave_resonator(
    frequencies: ArrayLike,
    duct_area: float,
    length: float,
    branch_area: float,
    *,
    speed_of_sound: float = _C_AIR,
    density: float = _RHO_AIR,
    source_impedance: ArrayLike | None = None,
    radiation_impedance: ArrayLike | None = None,
) -> ReactiveSilencerResult:
    """Closed quarter-wave side-branch tube on a duct (Bies Eqs. (8.144), (8.146)).

    :param frequencies: Frequencies ``f``, Hz (1-D array).
    :param duct_area: Main-duct cross-sectional area ``S_d``, m2.
    :param length: Effective branch length ``l_e``, m.
    :param branch_area: Branch tube area ``S``, m2.
    :param speed_of_sound: Speed of sound ``c``, m/s.
    :param density: Air density ``rho``, kg/m3.
    :param source_impedance: Optional source impedance ``Z_s``, Pa s/m3.
    :param radiation_impedance: Optional radiation impedance ``Z_r``, Pa s/m3.
    :return: A :class:`ReactiveSilencerResult`; ``resonances`` holds the odd
        multiples of ``f = c / (4 l_e)`` within the frequency range.
    """
    f = _frequencies(frequencies)
    c = require_positive(speed_of_sound, "speed_of_sound")
    rho = require_positive(density, "density")
    s_d = require_positive(duct_area, "duct_area")
    le = require_positive(length, "length")
    zb = quarter_wave_impedance(
        f, le, branch_area, speed_of_sound=c, density=rho
    )
    t = shunt_matrix(zb)
    f_fundamental = c / (4.0 * le)
    odds = np.arange(1, int(2.0 * f.max() / f_fundamental) + 2, 2)
    res = np.asarray(odds * f_fundamental, dtype=np.float64)
    res = res[res <= f.max()]
    if res.size == 0:
        res = np.array([f_fundamental], dtype=np.float64)
    return _result(
        f, t, inlet_area=s_d, outlet_area=s_d, c=c, rho=rho,
        source_impedance=source_impedance,
        radiation_impedance=radiation_impedance,
        kind="quarter-wave resonator",
        resonances=res,
    )


def extended_tube_chamber(
    frequencies: ArrayLike,
    length: float,
    chamber_area: float,
    pipe_area: float,
    *,
    inlet_extension: float = 0.0,
    outlet_extension: float = 0.0,
    speed_of_sound: float = _C_AIR,
    density: float = _RHO_AIR,
    source_impedance: ArrayLike | None = None,
    radiation_impedance: ArrayLike | None = None,
) -> ReactiveSilencerResult:
    """Extended-inlet/outlet expansion chamber (Bies §8.9.7).

    The inlet and outlet pipes extend a distance into the chamber, forming
    annular quarter-wave side branches (of area ``S_exp - S_duct`` and lengths
    equal to the extensions, Bies Eq. (8.156)) at the two junctions. Tuning the
    extensions (classically ``L/4`` and ``L/2``) places quarter-wave peaks that
    fill the ``kL = n pi`` troughs of the plain expansion chamber. With both
    extensions ``0`` the result reduces exactly to :func:`expansion_chamber`.

    :param frequencies: Frequencies ``f``, Hz (1-D array).
    :param length: Chamber length ``L``, m.
    :param chamber_area: Chamber cross-sectional area ``S_exp``, m2.
    :param pipe_area: Inlet/outlet pipe area ``S_duct``, m2.
    :param inlet_extension: Inlet pipe extension into the chamber ``L_a``, m.
    :param outlet_extension: Outlet pipe extension into the chamber ``L_b``, m.
    :param speed_of_sound: Speed of sound ``c``, m/s.
    :param density: Air density ``rho``, kg/m3.
    :param source_impedance: Optional source impedance ``Z_s``, Pa s/m3.
    :param radiation_impedance: Optional radiation impedance ``Z_r``, Pa s/m3.
    :return: A :class:`ReactiveSilencerResult`.
    """
    f = _frequencies(frequencies)
    c = require_positive(speed_of_sound, "speed_of_sound")
    rho = require_positive(density, "density")
    s_exp = require_positive(chamber_area, "chamber_area")
    s_duct = require_positive(pipe_area, "pipe_area")
    la = require_non_negative(inlet_extension, "inlet_extension")
    lb = require_non_negative(outlet_extension, "outlet_extension")
    if s_exp <= s_duct:
        raise ValueError("'chamber_area' must exceed 'pipe_area'.")
    annulus = s_exp - s_duct

    elements = []
    resonances = []
    if la > 0.0:
        elements.append(shunt_matrix(
            quarter_wave_impedance(f, la, annulus, speed_of_sound=c, density=rho)
        ))
        resonances.append(c / (4.0 * la))
    elements.append(duct_matrix(f, length, s_exp, speed_of_sound=c, density=rho))
    if lb > 0.0:
        elements.append(shunt_matrix(
            quarter_wave_impedance(f, lb, annulus, speed_of_sound=c, density=rho)
        ))
        resonances.append(c / (4.0 * lb))
    t = cascade(*elements)
    res = np.array(resonances, dtype=np.float64) if resonances else None
    return _result(
        f, t, inlet_area=s_duct, outlet_area=s_duct, c=c, rho=rho,
        source_impedance=source_impedance,
        radiation_impedance=radiation_impedance,
        kind="extended-tube chamber", resonances=res,
    )
