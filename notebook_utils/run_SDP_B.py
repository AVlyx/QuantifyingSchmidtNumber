"""Drivers for the one-sided (Bob-copies-only) SDP, mirroring run_SDP.py.

Same signatures as run_sdp_on_range / bin_search_sdp_vertex: `lam` is the partition
(height = len(lam) is the Schmidt number tested for, k = sum(lam) the number of copies of B),
and the objective uses the shapes of height == len(lam) (same convention as SDP_utils.sdp.SDP).
Results go to sdp_results/{folder}; pass e.g. folder="test_B" to keep them apart from the
two-sided sweeps.  No upper bound is computed (there is no SDP_max for the one-sided SDP).
"""
from typing import Callable, Literal
import numpy as np
from tqdm import tqdm

from notebook_utils.load_store_results import load_results_in_range, load_all_results, SdpResult, Separability, save_result
from notebook_utils.range_and_canonical import range_canonical
from notebook_utils.run_SDP import check_separability, find_bin_search_low_high
from SDP_utils.sdp_bonly import SDP_bonly
from SDP_utils.E_t import Et_lower


def _sdp_B(lam: list[int], state: np.ndarray, dims: tuple[int, int], solver: str, real: bool, **kw) -> float:
    obj, _ = SDP_bonly(len(lam), sum(lam), state, dims, solver=solver, real=real, exact_height=True, **kw)
    return obj


def run_sdp_on_range_B(
    filename: str,
    dims: tuple[int, int],
    lam: list[int],
    generator: Callable[[float], np.ndarray],
    range_: tuple[float, float, float],
    *,
    folder: str,
    k_sym_depth=2,
    compute_upper=False,  # ignored: no SDP_max for the one-sided SDP
    real=False,
    tol=10 ** (-7),
    solver: Literal["qics"] | Literal["mosek"] = "qics",
    early_stop=False,
    **sdp_kw,  # forwarded to SDP_bonly: marginal_symmetry, reduction, extra_cut
):
    SN_tested_for = len(lam)
    already_computed_results: list[SdpResult] = load_results_in_range(folder, filename, range_)
    if early_stop and already_computed_results and sorted(already_computed_results)[-1].objective < tol:
        return
    already_computed_points = [result.p for result in already_computed_results]
    left_to_compute = [p for p in range_canonical(range_) if p not in already_computed_points]
    print(f"{len(left_to_compute)} points left to compute")

    for p in tqdm(left_to_compute):
        state = generator(p)
        separability = check_separability(dims, k_sym_depth, state)
        if separability == Separability.separable:
            save_result(folder, filename, p, separability, 1, 0, [0] * (SN_tested_for - 1), None, [None])
            if early_stop:
                return
            continue

        obj_min = _sdp_B(lam, state, dims, solver, real, **sdp_kw)
        if obj_min - tol <= 0:
            save_result(folder, filename, p, separability, 1, obj_min, [0] * (SN_tested_for - 1), None, [None])
            if early_stop:
                return
            continue

        save_result(folder, filename, p, separability, SN_tested_for, obj_min, Et_lower(lam, obj_min, SN_tested_for), None, [None])


def bin_search_sdp_vertex_B(
    filename: str,
    dims: tuple[int, int],
    lam: list[int],
    generator: Callable[[float], np.ndarray],
    low_high: tuple[float, float],
    precision: int,
    *,
    folder: str,
    k_sym_depth=2,
    tol=10 ** (-7),
    solver: Literal["qics"] | Literal["mosek"] = "qics",
    real=False,
    decreasing=False,
    **sdp_kw,
):
    """Find the point where the SN goes from undetected to detected (assumes monotone)."""
    low, high = low_high
    already_computed_results: list[SdpResult] = load_all_results(folder, filename)
    computed_ps = [res.p for res in already_computed_results]
    for endpoint in (low, high):
        if endpoint not in computed_ps:
            _bin_step_B(filename, dims, lam, generator, endpoint, folder=folder, k_sym_depth=k_sym_depth, tol=tol, solver=solver, real=real, **sdp_kw)

    low, high = find_bin_search_low_high(already_computed_results, low_high, decreasing)
    for _ in tqdm(range(len(already_computed_results), precision)):
        p = (low + high) / 2
        detected = _bin_step_B(filename, dims, lam, generator, p, folder=folder, k_sym_depth=k_sym_depth, tol=tol, solver=solver, real=real, **sdp_kw)
        if detected:
            low, high = (p, high) if decreasing else (low, p)
        else:
            low, high = (low, p) if decreasing else (p, high)


def _bin_step_B(filename, dims, lam, generator, p, *, folder, k_sym_depth, tol, solver, real, **sdp_kw) -> bool:
    """Evaluate one point, save it, return True iff the SDP detects SN >= len(lam)."""
    SN_tested_for = len(lam)
    state = generator(p)
    separability = check_separability(dims, k_sym_depth, state)
    if separability == Separability.separable:
        save_result(folder, filename, p, separability, 1, 0, [0] * (SN_tested_for - 1), None, [None])
        return False
    obj_min = _sdp_B(lam, state, dims, solver, real, **sdp_kw)
    if obj_min - tol <= 0:
        save_result(folder, filename, p, separability, 1, obj_min, [0] * (SN_tested_for - 1), None, [None])
        return False
    save_result(folder, filename, p, separability, SN_tested_for, obj_min, Et_lower(lam, obj_min, SN_tested_for), None, [None])
    return True
