#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Building acoustic performance prediction (EN 12354-1/-2:2000).

This is the **prediction** counterpart of the measurement modules
(:mod:`phonometry.lab_insulation` for laboratory ``R``/``Ln`` and
:mod:`phonometry.insulation` for field ``R'``/``L'n``). EN 12354 estimates the
*in-situ* apparent performance of a building from the laboratory performance of
its elements, adding the flanking transmission that a field measurement would
capture but a laboratory measurement suppresses.

Both parts have a *detailed* per-band model and a *simplified* single-number
model. This module implements the **simplified single-number model** (Part 1
Clause 4.4, Part 2 Clause 4.3): it takes the weighted single-number ratings of
the elements (``Rw`` of walls/floors, ``ΔRw``/``ΔLw`` of linings/coverings and
the ``Kij`` vibration-reduction indices of the junctions) and predicts the
apparent weighted rating (``R'w`` airborne, ``L'n,w`` impact). The simplified
model is exact for ``RA`` and a good approximation for ``R'w`` (Part 1
Clause 4.4.1), with a reported standard deviation of about 2 dB (Clause 5).

**Airborne — Formula (26).** The apparent weighted sound reduction index is the
energetic sum of the direct path ``Dd`` and, for every flanking element, the
three flanking paths ``Ff``, ``Df`` and ``Fd``::

    R'w = -10 lg[ 10^(-RDd,w/10) + Σ 10^(-RFf,w/10)
                 + Σ 10^(-RDf,w/10) + Σ 10^(-RFd,w/10) ]

with the direct path ``RDd,w = Rs,w + ΔRDd,w`` (Formula 27) and each flanking
path (Formula 28a) ``Rij,w = (Ri,w + Rj,w)/2 + ΔRij,w + Kij + 10 lg(Ss/(l0·lf))``
where ``l0 = 1 m`` is the reference coupling length.

**Junctions — Annex E.** The vibration reduction index ``Kij`` of rigid cross
(E.3) and T (E.4) junctions, junctions with flexible interlayers (E.5) and
lightweight façade junctions (E.6) are empirical functions of the mass ratio
``M = lg(m'⊥,i / m'i)``. A minimum value ``Kij,min`` follows from Formula (29).

**Impact — Formula (21).** ``L'n,w = Ln,w,eq − ΔLw + K`` with the bare-floor
equivalent level ``Ln,w,eq`` (Annex B ``164 − 35 lg(m'/m'0)``), the covering
improvement ``ΔLw`` (ISO 717-2) and the flanking correction ``K`` from Table 1.

Clause citations refer to EN 12354-1:2000 (airborne) or EN 12354-2:2000 (impact).
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log10
from typing import Literal, Sequence

#: Reference coupling length ``l0`` in Formula (28a), in metres (Clause 4.4.1).
_L0 = 1.0

#: Reference frequency ``fref`` of Annex E, in hertz (Formula E.1).
_FREF = 1000.0

#: Frequency (Hz) at which the single-number ``Kij`` is read for the simplified
#: model (Clause 4.4.2): the 500 Hz value.
_K_FREQUENCY = 500.0

#: Default interlayer characteristic frequency ``f1`` of Formula (E.5), in hertz,
#: valid for ``E1/t1 ≈ 100 MN/m³``.
_F1_DEFAULT = 125.0

#: Reference mass per unit area ``m'0`` in ``Ln,w,eq = 164 − 35 lg(m'/m'0)``.
_M0 = 1.0

#: Constants of the bare-floor equivalent impact level (Part 2, Annex B).
_LN_EQ_A = 164.0
_LN_EQ_B = 35.0

#: Reference volume ``V0`` of Formula (3), in m³ (Part 2).
_V0_IMPACT = 30.0

JunctionType = Literal[
    "rigid_cross", "rigid_t", "flexible_t", "lightweight_facade"
]
PathKind = Literal["through", "corner"]

#: Table 1 of EN 12354-2:2000 — flanking correction ``K`` (dB). Row key is the
#: separating-floor mass, column key the mean flanking-element mass (kg/m²).
_TABLE1_SEP = (100, 150, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 900)
_TABLE1_FLK = (100, 150, 200, 250, 300, 350, 400, 450, 500)
_TABLE1_K = (
    (1, 0, 0, 0, 0, 0, 0, 0, 0),
    (1, 1, 0, 0, 0, 0, 0, 0, 0),
    (2, 1, 1, 0, 0, 0, 0, 0, 0),
    (2, 1, 1, 1, 0, 0, 0, 0, 0),
    (3, 2, 1, 1, 1, 0, 0, 0, 0),
    (3, 2, 1, 1, 1, 1, 0, 0, 0),
    (4, 2, 2, 1, 1, 1, 1, 0, 0),
    (4, 3, 2, 2, 1, 1, 1, 1, 1),
    (4, 3, 2, 2, 1, 1, 1, 1, 1),
    (5, 4, 3, 2, 2, 1, 1, 1, 1),
    (5, 4, 3, 3, 2, 2, 1, 1, 1),
    (6, 4, 4, 3, 2, 2, 2, 1, 1),
    (6, 5, 4, 3, 3, 2, 2, 2, 2),
)


@dataclass(frozen=True)
class FlankingPath:
    """One flanking transmission path (Ff, Df or Fd) of the simplified model.

    :ivar label: Human-readable path name, e.g. ``"floor-Ff"``.
    :ivar kind: Path type, one of ``"Ff"``, ``"Df"``, ``"Fd"``.
    :ivar r_ij_w: Weighted flanking sound reduction index ``Rij,w`` of the path,
        in dB (EN 12354-1 Formula 28a).
    """

    label: str
    kind: Literal["Ff", "Df", "Fd"]
    r_ij_w: float


@dataclass(frozen=True)
class PathContribution:
    """A transmission path with its share of the total transmitted energy.

    :ivar label: Path name (``"Dd"`` for the direct path).
    :ivar kind: ``"Dd"``, ``"Ff"``, ``"Df"`` or ``"Fd"``.
    :ivar r_w: Weighted sound reduction index of the path, in dB.
    :ivar fraction: Fraction of the total transmitted sound energy carried by
        this path (0 to 1); the dominant path has the largest fraction.
    """

    label: str
    kind: str
    r_w: float
    fraction: float


@dataclass(frozen=True)
class AirbornePredictionResult:
    """Predicted apparent airborne insulation (EN 12354-1:2000, Formula 26).

    :ivar r_prime_w: Apparent weighted sound reduction index ``R'w``, in dB.
    :ivar r_direct_w: Direct-path weighted index ``RDd,w``, in dB (Formula 27).
    :ivar paths: Per-path contributions in input order (direct path first, then
        the flanking paths as supplied), each with its share of the energy.
    :ivar dominant: The path carrying the most energy (``PathContribution``).
    """

    r_prime_w: float
    r_direct_w: float
    paths: tuple[PathContribution, ...]
    dominant: PathContribution


@dataclass(frozen=True)
class ImpactPredictionResult:
    """Predicted apparent impact insulation (EN 12354-2:2000, Formula 21).

    :ivar l_prime_n_w: Apparent weighted normalized impact sound pressure level
        ``L'n,w``, in dB.
    :ivar ln_w_eq: Bare-floor equivalent weighted level ``Ln,w,eq``, in dB.
    :ivar delta_l_w: Weighted covering improvement ``ΔLw``, in dB.
    :ivar k_correction: Flanking correction ``K``, in dB (Table 1).
    """

    l_prime_n_w: float
    ln_w_eq: float
    delta_l_w: float
    k_correction: float


def _check_finite(value: float, name: str) -> float:
    """Return ``value`` as a float, raising if it is not finite."""
    v = float(value)
    if v != v or v in (float("inf"), float("-inf")):
        raise ValueError(f"'{name}' must be a finite number.")
    return v


def junction_vibration_reduction(
    junction_type: JunctionType,
    path: PathKind,
    mass_ratio: float,
    *,
    frequency: float = _K_FREQUENCY,
    f1: float = _F1_DEFAULT,
) -> float:
    """Vibration reduction index ``Kij`` of a junction (EN 12354-1 Annex E).

    Empirical ``Kij`` for common junctions as a function of the mass ratio
    ``M = lg(mass_ratio)`` where ``mass_ratio = m'⊥,i / m'i`` is the mass per
    unit area of the perpendicular element over that of the element carrying the
    path (Formula E.2). ``path`` selects the *through* branch (in-line elements,
    ``K13``) or the *corner* branch (``K12 = K23``).

    Supported ``junction_type`` values and their formulas:

    - ``"rigid_cross"`` (E.3): through ``8,7 + 17,1 M + 5,7 M²``;
      corner ``8,7 + 5,7 M²``.
    - ``"rigid_t"`` (E.4): through ``5,7 + 14,1 M + 5,7 M²``;
      corner ``5,7 + 5,7 M²``.
    - ``"flexible_t"`` (E.5, wall junction with flexible interlayers): through
      ``5,7 + 14,1 M + 5,7 M² + 2·Δ1``; corner ``5,7 + 5,7 M² + Δ1`` with
      ``Δ1 = 10 lg(f/f1)`` for ``f > f1`` (else 0) and ``f1 = 125 Hz`` for the
      typical interlayer ``E1/t1 ≈ 100 MN/m³``.
    - ``"lightweight_facade"`` (E.6): through ``max(5 + 10 M, 5)``;
      corner ``10 + 10 |M|``.

    :param junction_type: Junction geometry (see above).
    :param path: ``"through"`` (K13) or ``"corner"`` (K12 = K23).
    :param mass_ratio: ``m'⊥,i / m'i`` (must be positive).
    :param frequency: Frequency at which ``Kij`` is evaluated, in Hz; only the
        ``"flexible_t"`` junction is frequency dependent. Defaults to 500 Hz, the
        value used by the simplified model (Clause 4.4.2).
    :param f1: Interlayer characteristic frequency for ``"flexible_t"``, in Hz.
    :return: ``Kij``, in dB.
    :raises ValueError: If ``mass_ratio`` is not positive, ``frequency``/``f1``
        are not positive, or an unknown ``junction_type``/``path`` is given.
    """
    ratio = _check_finite(mass_ratio, "mass_ratio")
    if ratio <= 0.0:
        raise ValueError("'mass_ratio' must be positive.")
    if _check_finite(frequency, "frequency") <= 0.0:
        raise ValueError("'frequency' must be positive.")
    if _check_finite(f1, "f1") <= 0.0:
        raise ValueError("'f1' must be positive.")
    if path not in ("through", "corner"):
        raise ValueError("'path' must be 'through' or 'corner'.")

    m = log10(ratio)
    delta1 = 10.0 * log10(frequency / f1) if frequency > f1 else 0.0

    if junction_type == "rigid_cross":
        if path == "through":
            return 8.7 + 17.1 * m + 5.7 * m * m
        return 8.7 + 5.7 * m * m
    if junction_type == "rigid_t":
        if path == "through":
            return 5.7 + 14.1 * m + 5.7 * m * m
        return 5.7 + 5.7 * m * m
    if junction_type == "flexible_t":
        if path == "through":
            return 5.7 + 14.1 * m + 5.7 * m * m + 2.0 * delta1
        return 5.7 + 5.7 * m * m + delta1
    if junction_type == "lightweight_facade":
        if path == "through":
            return max(5.0 + 10.0 * m, 5.0)
        return 10.0 + 10.0 * abs(m)
    raise ValueError(
        "'junction_type' must be one of 'rigid_cross', 'rigid_t', "
        "'flexible_t', 'lightweight_facade'."
    )


def junction_min_vibration_reduction(
    coupling_length: float, s_i: float, s_j: float
) -> float:
    """Minimum vibration reduction index ``Kij,min`` (EN 12354-1 Formula 29).

    ``Kij,min = 10 lg[ lf · l0 · (1/Si + 1/Sj) ]`` with the reference coupling
    length ``l0 = 1 m``. When the tabulated ``Kij`` is below this value, the
    minimum is used (Clause 4.4.2).

    :param coupling_length: Common coupling length ``lf`` of the junction, in m.
    :param s_i: Area of element ``i``, in m².
    :param s_j: Area of element ``j``, in m².
    :return: ``Kij,min``, in dB.
    :raises ValueError: If any argument is not positive.
    """
    lf = _check_finite(coupling_length, "coupling_length")
    si = _check_finite(s_i, "s_i")
    sj = _check_finite(s_j, "s_j")
    if lf <= 0.0 or si <= 0.0 or sj <= 0.0:
        raise ValueError("'coupling_length', 's_i' and 's_j' must be positive.")
    return 10.0 * log10(lf * _L0 * (1.0 / si + 1.0 / sj))


def combine_linings(delta_a: float, delta_b: float) -> float:
    """Combine two lining improvements (EN 12354-1 Formulas 30/31).

    For two linings the total improvement is the larger value plus half the
    smaller: ``ΔR = max(a, b) + min(a, b)/2``. For a single lining pass the
    other as ``0``.

    :param delta_a: Improvement of the first lining, in dB.
    :param delta_b: Improvement of the second lining, in dB.
    :return: Combined ``ΔR``/``ΔRij``, in dB.
    """
    a = _check_finite(delta_a, "delta_a")
    b = _check_finite(delta_b, "delta_b")
    return max(a, b) + min(a, b) / 2.0


def _coupling_term(separating_area: float, coupling_length: float) -> float:
    """The ``10 lg(Ss/(l0·lf))`` term of Formula (28a)."""
    ss = _check_finite(separating_area, "separating_area")
    lf = _check_finite(coupling_length, "coupling_length")
    if ss <= 0.0 or lf <= 0.0:
        raise ValueError(
            "'separating_area' and 'coupling_length' must be positive."
        )
    return 10.0 * log10(ss / (_L0 * lf))


def flanking_path(
    *,
    label: str,
    kind: Literal["Ff", "Df", "Fd"],
    r_source: float,
    r_receive: float,
    k_ij: float,
    separating_area: float,
    coupling_length: float,
    delta_r: float = 0.0,
    kij_min: float | None = None,
) -> FlankingPath:
    """Build one flanking path ``Rij,w`` (EN 12354-1 Formula 28a).

    ``Rij,w = (r_source + r_receive)/2 + delta_r + k_ij + 10 lg(Ss/(l0·lf))``.
    The two element indices depend on the path: for ``Ff`` both are the flanking
    element (``RF,w``, ``Rf,w``); for ``Fd`` they are the flanking (source) and
    separating (receive) elements; for ``Df`` the separating (source) and
    flanking (receive) elements.

    When ``kij_min`` is given, ``k_ij`` is clamped up to it
    (``max(k_ij, kij_min)``) before the path is formed, enforcing the floor
    ``Kij ≥ Kij,min`` of Clause 4.4.2 (compute ``kij_min`` with
    :func:`junction_min_vibration_reduction`). Left as ``None`` the raw ``k_ij``
    is used unchanged.

    :param label: Human-readable path name.
    :param kind: ``"Ff"``, ``"Df"`` or ``"Fd"``.
    :param r_source: Weighted sound reduction index of the source-side element.
    :param r_receive: Weighted sound reduction index of the receive-side element.
    :param k_ij: Vibration reduction index of this path, in dB.
    :param separating_area: Area ``Ss`` of the separating element, in m².
    :param coupling_length: Junction coupling length ``lf``, in m.
    :param delta_r: Combined lining improvement ``ΔRij,w`` for this path, in dB.
    :param kij_min: Optional ``Kij,min`` floor (Clause 4.4.2); ``k_ij`` is
        raised to it when it lies below. ``None`` disables the clamp.
    :return: The :class:`FlankingPath`.
    :raises ValueError: If ``kind`` is unknown, areas/lengths are not positive,
        or any value is non-finite.
    """
    if kind not in ("Ff", "Df", "Fd"):
        raise ValueError("'kind' must be 'Ff', 'Df' or 'Fd'.")
    rs = _check_finite(r_source, "r_source")
    rr = _check_finite(r_receive, "r_receive")
    kij = _check_finite(k_ij, "k_ij")
    if kij_min is not None:
        kij = max(kij, _check_finite(kij_min, "kij_min"))
    dr = _check_finite(delta_r, "delta_r")
    r_ij = (rs + rr) / 2.0 + dr + kij + _coupling_term(
        separating_area, coupling_length
    )
    return FlankingPath(label=label, kind=kind, r_ij_w=r_ij)


def flanking_element(
    *,
    label: str,
    r_flanking: float,
    r_separating: float,
    k_ff: float,
    k_fd: float,
    k_df: float,
    separating_area: float,
    coupling_length: float,
    delta_r_ff: float = 0.0,
    delta_r_fd: float = 0.0,
    delta_r_df: float = 0.0,
) -> tuple[FlankingPath, FlankingPath, FlankingPath]:
    """Build the three flanking paths (Ff, Df, Fd) of one flanking element.

    Convenience wrapper over :func:`flanking_path` for the common case where a
    flanking element is essentially the same on the source and receiving side
    (Clause 4.4.1). Returns the ``Ff``, ``Df`` and ``Fd`` paths that this element
    contributes across its junction with the separating element.

    .. note::
        Clause 4.4.2 requires ``Kij ≥ Kij,min``. This wrapper does not clamp
        (each of ``KFf``/``KFd``/``KDf`` has its own ``Kij,min`` from the two
        element areas of that junction). Compute the floor per path with
        :func:`junction_min_vibration_reduction` and pass already-clamped
        ``k_ff``/``k_fd``/``k_df`` here, or call :func:`flanking_path` directly
        with its ``kij_min`` argument, to avoid silent non-compliance.

    :param label: Base name; paths are labelled ``"<label>-Ff"`` etc.
    :param r_flanking: Weighted sound reduction index of the flanking element.
    :param r_separating: Weighted sound reduction index of the separating element.
    :param k_ff: ``KFf`` vibration reduction index, in dB.
    :param k_fd: ``KFd`` vibration reduction index, in dB.
    :param k_df: ``KDf`` vibration reduction index, in dB.
    :param separating_area: Separating-element area ``Ss``, in m².
    :param coupling_length: Junction coupling length ``lf``, in m.
    :param delta_r_ff: Combined lining improvement for the Ff path, in dB.
    :param delta_r_fd: Combined lining improvement for the Fd path, in dB.
    :param delta_r_df: Combined lining improvement for the Df path, in dB.
    :return: The ``(Ff, Df, Fd)`` :class:`FlankingPath` triple.
    """
    ff = flanking_path(
        label=f"{label}-Ff", kind="Ff", r_source=r_flanking,
        r_receive=r_flanking, k_ij=k_ff, separating_area=separating_area,
        coupling_length=coupling_length, delta_r=delta_r_ff,
    )
    df = flanking_path(
        label=f"{label}-Df", kind="Df", r_source=r_separating,
        r_receive=r_flanking, k_ij=k_df, separating_area=separating_area,
        coupling_length=coupling_length, delta_r=delta_r_df,
    )
    fd = flanking_path(
        label=f"{label}-Fd", kind="Fd", r_source=r_flanking,
        r_receive=r_separating, k_ij=k_fd, separating_area=separating_area,
        coupling_length=coupling_length, delta_r=delta_r_fd,
    )
    return ff, df, fd


def predicted_airborne_insulation(
    *,
    r_direct: float,
    flanking_paths: Sequence[FlankingPath] = (),
    delta_r_direct: float = 0.0,
) -> AirbornePredictionResult:
    """Predict the apparent airborne insulation ``R'w`` (EN 12354-1 Formula 26).

    Energetically combines the direct path ``RDd,w = r_direct + delta_r_direct``
    (Formula 27) with the supplied flanking paths::

        R'w = -10 lg[ 10^(-RDd,w/10) + Σ 10^(-Rij,w/10) ]

    With no flanking paths the result equals the direct path ``RDd,w``; each
    added path strictly lowers ``R'w``. The result exposes every path's share of
    the transmitted energy so the dominant path is visible.

    :param r_direct: Weighted sound reduction index of the separating element
        ``Rs,w``, in dB.
    :param flanking_paths: Flanking paths (see :func:`flanking_element`). May be
        empty for the direct-only case.
    :param delta_r_direct: Combined lining improvement ``ΔRDd,w`` on the
        separating element, in dB.
    :return: The :class:`AirbornePredictionResult`.
    :raises ValueError: If any input is non-finite.
    """
    r_dd = _check_finite(r_direct, "r_direct") + _check_finite(
        delta_r_direct, "delta_r_direct"
    )
    tau_direct = 10.0 ** (-r_dd / 10.0)
    tau_paths = [10.0 ** (-p.r_ij_w / 10.0) for p in flanking_paths]
    tau_total = tau_direct + sum(tau_paths)
    r_prime_w = -10.0 * log10(tau_total)

    contributions = [
        PathContribution(
            label="Dd", kind="Dd", r_w=r_dd, fraction=tau_direct / tau_total
        )
    ]
    contributions += [
        PathContribution(
            label=p.label, kind=p.kind, r_w=p.r_ij_w,
            fraction=tau / tau_total,
        )
        for p, tau in zip(flanking_paths, tau_paths)
    ]
    dominant = max(contributions, key=lambda c: c.fraction)
    return AirbornePredictionResult(
        r_prime_w=r_prime_w,
        r_direct_w=r_dd,
        paths=tuple(contributions),
        dominant=dominant,
    )


def equivalent_impact_level(mass_per_area: float) -> float:
    """Bare-floor equivalent weighted impact level ``Ln,w,eq`` (Part 2, Annex B).

    ``Ln,w,eq = 164 − 35 lg(m'/m'0)`` with ``m'0 = 1 kg/m²`` — the closed form
    used in the Annex E worked example for a homogeneous concrete floor.

    :param mass_per_area: Mass per unit area ``m'`` of the bare floor, in kg/m²
        (must be positive).
    :return: ``Ln,w,eq``, in dB.
    :raises ValueError: If ``mass_per_area`` is not positive.
    """
    m = _check_finite(mass_per_area, "mass_per_area")
    if m <= 0.0:
        raise ValueError("'mass_per_area' must be positive.")
    return _LN_EQ_A - _LN_EQ_B * log10(m / _M0)


def impact_flanking_correction(
    separating_mass: float, flanking_mass: float
) -> int:
    """Flanking correction ``K`` from Table 1 (EN 12354-2:2000).

    Looks up ``K`` (dB) for the separating-floor mass and the mean mass of the
    homogeneous flanking elements, selecting the nearest tabulated row/column
    (the table is discrete; masses outside 100–900 / 100–500 kg/m² clamp to the
    nearest edge).

    :param separating_mass: Mass per unit area of the separating floor, in kg/m².
    :param flanking_mass: Mean mass per unit area of the homogeneous flanking
        elements not covered by additional layers, in kg/m².
    :return: The correction ``K``, in dB (a non-negative integer).
    :raises ValueError: If a mass is not positive.
    """
    sm = _check_finite(separating_mass, "separating_mass")
    fm = _check_finite(flanking_mass, "flanking_mass")
    if sm <= 0.0 or fm <= 0.0:
        raise ValueError("'separating_mass' and 'flanking_mass' must be positive.")
    # Nearest-neighbour selection on the discrete Table 1 grid. Both mass axes
    # are ascending, and ``min`` returns the first index reaching the smallest
    # distance, so a mass exactly halfway between two tabulated values (e.g.
    # 125 kg/m² between 100 and 150) ties to the *lower* tabulated mass.
    row = min(range(len(_TABLE1_SEP)), key=lambda i: abs(_TABLE1_SEP[i] - sm))
    col = min(range(len(_TABLE1_FLK)), key=lambda j: abs(_TABLE1_FLK[j] - fm))
    return _TABLE1_K[row][col]


def predicted_impact_insulation(
    *,
    ln_w_eq: float,
    delta_l_w: float = 0.0,
    k_correction: float = 0.0,
) -> ImpactPredictionResult:
    """Predict the apparent impact insulation ``L'n,w`` (EN 12354-2 Formula 21).

    ``L'n,w = Ln,w,eq − ΔLw + K``. The bare-floor equivalent level may come from
    :func:`equivalent_impact_level` and the flanking correction from
    :func:`impact_flanking_correction`.

    :param ln_w_eq: Bare-floor equivalent weighted level ``Ln,w,eq``, in dB.
    :param delta_l_w: Weighted covering improvement ``ΔLw`` (ISO 717-2), in dB.
    :param k_correction: Flanking correction ``K`` (Table 1), in dB.
    :return: The :class:`ImpactPredictionResult`.
    :raises ValueError: If any input is non-finite.
    """
    ln_eq = _check_finite(ln_w_eq, "ln_w_eq")
    dl = _check_finite(delta_l_w, "delta_l_w")
    k = _check_finite(k_correction, "k_correction")
    return ImpactPredictionResult(
        l_prime_n_w=ln_eq - dl + k,
        ln_w_eq=ln_eq,
        delta_l_w=dl,
        k_correction=k,
    )


def standardized_impact_level(l_prime_n_w: float, volume: float) -> float:
    """Standardized apparent impact level ``L'nT,w`` (EN 12354-2 Formula 3).

    ``L'nT,w = L'n,w − 10 lg(V/V0)`` with the reference receiving-room volume
    ``V0 = 30 m³``.

    :param l_prime_n_w: Apparent weighted normalized impact level ``L'n,w``, dB.
    :param volume: Receiving-room volume ``V``, in m³ (must be positive).
    :return: ``L'nT,w``, in dB.
    :raises ValueError: If ``volume`` is not positive.
    """
    lnw = _check_finite(l_prime_n_w, "l_prime_n_w")
    v = _check_finite(volume, "volume")
    if v <= 0.0:
        raise ValueError("'volume' must be positive.")
    return lnw - 10.0 * log10(v / _V0_IMPACT)
