from notebook_utils.load_store_results import load_results_in_range, load_all_results, SdpResult, Separability, save_result
from notebook_utils.range_and_canonical import range_canonical
from tqdm import tqdm
from toqito.state_props import is_separable
from typing import Callable, Literal
import numpy as np
from SDP_utils.sdp import SDP, SDP_max
from SDP_utils.E_t import Et_lower, E_t_upperk2r2, max_Et
from itertools import pairwise


def run_sdp_on_range(
    filename: str,
    dims: tuple[int, int],
    lam: list[int],
    generator: Callable[[float], np.ndarray],
    range_: tuple[float, float, float],
    *,
    folder: str,
    k_sym_depth=2,
    compute_upper=False,
    real=False,
    tol=10 ** (-7),
    solver: Literal["qics"] | Literal["mosek"] = "qics",
    early_stop=False,  # stop at the first zero
):
    SN_tested_for = len(lam)
    already_computed_results: list[SdpResult] = load_results_in_range(folder, filename, range_)
    if early_stop and already_computed_results and sorted(already_computed_results)[-1].objective < tol:
        "already computed with early stop"
        return
    already_computed_points = [result.p for result in already_computed_results]

    range_can = range_canonical(range_)
    left_to_compute = [p for p in range_can if p not in already_computed_points]
    print(f"{len(left_to_compute)} points left to compute")

    for p in tqdm(left_to_compute):
        state = generator(p)
        separability = check_separability(dims, k_sym_depth, state)
        # * Early continue if separable
        if separability == Separability.separable:
            save_result(
                folder,
                filename,
                p,
                separability,
                1,
                0,
                [0] * (SN_tested_for - 1),
                1 if compute_upper else None,
                [max_Et(SN_tested_for, t) for t in range(1, SN_tested_for)] if compute_upper else [None],
            )
            if early_stop:
                return
            continue

        # * Early continue if objective shows separable
        obj_min, _ = SDP(len(lam), sum(lam), state, dims, solver=solver, real=real)
        if obj_min - tol <= 0:
            save_result(
                folder,
                filename,
                p,
                separability,
                1,
                obj_min,
                [0] * (SN_tested_for - 1),
                1 if compute_upper else None,
                [max_Et(SN_tested_for, t) for t in range(1, SN_tested_for)] if compute_upper else [None],
            )
            if early_stop:
                return
            continue

        # * At this point the state is entangled according to the sdp
        if sum(lam) >= 3:
            print("Compute upper not implemented for k >= 3")
            compute_upper = False
        if compute_upper:
            obj_max, _ = SDP_max(len(lam), sum(lam), state, dims, solver=solver, real=real)
            E1_upper: float | None = min(E_t_upperk2r2(obj_max), 1.0) if obj_max < 0.25 else 1.0
        else:
            obj_max = None
            E1_upper = None

        save_result(folder, filename, p, separability, SN_tested_for, obj_min, Et_lower(lam, obj_min, SN_tested_for), obj_max, [E1_upper])


def check_separability(dims: tuple[int, int], k_sym_depth: int, state: np.ndarray) -> Separability:
    # * Toqito check for separability
    sep, msg = is_separable(state, dim=[*dims], level=k_sym_depth)
    if sep:
        return Separability.separable
    elif msg.startswith("inconclusive"):
        return Separability.inconclusive
    else:
        return Separability.entangled


def find_bin_search_low_high(results: list[SdpResult], low_high: tuple[float, float], decreasing: bool) -> tuple[float, float]:
    if not results:
        return low_high
    low, high = low_high
    res_p_sep: list[tuple[float, bool]] = [(low, decreasing)] + [(r.p, r.Et_lower[0] == 0.0) for r in results] + [(high, not decreasing)]
    results.sort()
    return next(
        ((low_w, high_w) for (low_w, low_w_sep_bool), (high_w, high_w_sep_bool) in pairwise(res_p_sep) if (low_w_sep_bool != high_w_sep_bool)),
        low_high,
    )


def bin_search_sdp_vertex(
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
):
    """Find the point where the SN goes from undetected to detected. Assuming continuous and increasing.
    low_high are the lower bound and upper bound of the search
    precision is the number of windows uptates to the bounds"""

    low, high = low_high

    already_computed_results: list[SdpResult] = load_all_results(folder, filename)

    if not low in [res.p for res in already_computed_results]:
        bin_search_sdp_step(
            filename,
            dims,
            lam,
            generator,
            low,
            high,
            folder=folder,
            k_sym_depth=k_sym_depth,
            tol=tol,
            solver=solver,
            real=real,
            decreasing=decreasing,
        )
    if not high in [res.p for res in already_computed_results]:
        bin_search_sdp_step(
            filename,
            dims,
            lam,
            generator,
            low,
            high,
            folder=folder,
            k_sym_depth=k_sym_depth,
            tol=tol,
            solver=solver,
            real=real,
            decreasing=decreasing,
        )

    low, high = find_bin_search_low_high(already_computed_results, low_high, decreasing)
    computed = len(already_computed_results)

    for _ in tqdm(range(computed, precision)):
        low, high = bin_search_sdp_step(
            filename,
            dims,
            lam,
            generator,
            low,
            high,
            folder=folder,
            k_sym_depth=k_sym_depth,
            tol=tol,
            solver=solver,
            real=real,
            decreasing=decreasing,
        )


def bin_search_sdp_step(
    filename: str,
    dims: tuple[int, int],
    lam: list[int],
    generator: Callable[[float], np.ndarray],
    low: float,
    high: float,
    *,
    folder: str,
    k_sym_depth=2,
    tol=10 ** (-7),
    solver: Literal["qics"] | Literal["mosek"] = "qics",
    real=False,
    decreasing=False,
) -> tuple[float, float]:
    SN_tested_for = len(lam)
    p = (low + high) / 2
    state = generator(p)
    separability = check_separability(dims, k_sym_depth, state)
    if separability == Separability.separable:
        save_result(folder, filename, p, separability, 1, 0, [0] * (SN_tested_for - 1), None, [None])
        return (low, p) if decreasing else (p, high)

    obj_min, _ = SDP(len(lam), sum(lam), state, dims, solver=solver, real=real)
    if obj_min - tol <= 0:
        save_result(folder, filename, p, separability, 1, obj_min, [0] * (SN_tested_for - 1), None, [None])
        return (low, p) if decreasing else (p, high)

    save_result(folder, filename, p, separability, SN_tested_for, obj_min, Et_lower(lam, obj_min, SN_tested_for), None, [None])
    return (p, high) if decreasing else (low, p)
