from notebook_utils.load_store_results import load_results_in_range, SdpResult, Separability, save_result
from notebook_utils.range_and_canonical import range_canonical
from tqdm import tqdm
from toqito.state_props import is_separable
from typing import Callable, Literal
import numpy as np
from SDP_utils.sdp import SDP, SDP_max
from SDP_utils.E_t import Et_lower, E_t_upperk2r2, max_Et


def run_sdp_on_range(
    filename: str,
    dims: tuple[int, int],
    lam: list[int],
    generator: Callable[[float], np.ndarray],
    range_: tuple[float, float, float],
    k_sym_depth=2,
    compute_upper=False,
    real=True,
    tol=10 ** (-7),
    solver: Literal["qics"] | Literal["mosek"] = "qics",
    early_stop=False,  # stop at the first zero
):
    SN_tested_for = len(lam)
    already_computed_results: list[SdpResult] = load_results_in_range(filename, range_)
    if early_stop and already_computed_results and sorted(already_computed_results)[-1].objective < tol:
        "already computed with early stop"
        return
    already_computed_points = [result.p for result in already_computed_results]

    range_can = range_canonical(range_)
    left_to_compute = [p for p in range_can if p not in already_computed_points]
    print(f"{len(left_to_compute)} points left to compute")

    for p in tqdm(left_to_compute):
        state = generator(p)

        # * Toqito check for separability
        sep, msg = is_separable(state, dim=[*dims], level=k_sym_depth)
        if sep:
            separability = Separability.separable
        elif msg.startswith("inconclusive"):
            separability = Separability.inconclusive
        else:
            separability = Separability.entangled

        # * Early continue if separable
        if separability == Separability.separable:
            save_result(
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
        obj_min, _ = SDP(lam, state, dims, solver=solver, real=real)
        if obj_min - tol <= 0:
            save_result(
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
            obj_max, _ = SDP_max(lam, state, dims, solver=solver, real=real)
            E1_upper: float | None = min(E_t_upperk2r2(obj_max), 1.0) if obj_max < 0.25 else 1.0
        else:
            obj_max = None
            E1_upper = None

        save_result(filename, p, separability, SN_tested_for, obj_min, Et_lower(lam, obj_min, SN_tested_for), obj_max, [E1_upper])
