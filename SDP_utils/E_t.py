import math
from schur_weyl.sw_measure import schur_weyl_measure
from scipy.optimize import brentq, minimize_scalar


def max_Et(r: int, t: int):
    return 1 - (1 / r) * t


def E_t_lowerk2(r: int, t: int, P_lambda: float):
    etn = t + math.sqrt(t * (r - t) * (r - 2 * r * P_lambda - 1))
    return 1 - etn / r


def E_t_upperk2r2(P_lambda: float):
    if P_lambda > 0.25:
        return 1
    return (1 - math.sqrt(1 - 4 * P_lambda)) / 2


def E_t_lower_lambda_r2(lam: list[int], P_lam: float) -> float:
    # for all projectors if SN == 2
    if P_lam >= 0.25:
        return 1 / 2

    def g(x):
        return schur_weyl_measure([x, 1 - x], sum(lam))[tuple(lam)] - P_lam

    try:
        root: float = brentq(g, 1 / 2, 1, xtol=1e-10)  # type: ignore
    except ValueError:
        root: float = 1 / 2

    if not root:
        return 1 / 2
    return 1 - root


def E_t_upper_antisym(lam: list[int], P_lam: float, t: int, r: int):
    # all SN for antisym proj
    """r is the number of variables (the expected SN)"""
    assert all([li == 1 for li in lam])
    assert t < r
    k = len(lam)
    assert k <= r

    def ek(x: float):
        res: float = 0.0
        for i in range(k + 1):
            res += math.comb(t, i) * math.comb(r - t, k - i) * (x / t) ** i * ((1 - x) / (r - t)) ** (k - i)
        return res - P_lam

    try:
        root = brentq(ek, 1 / r * t, 1, xtol=1e-10)
    except ValueError:
        return max_Et(r, t)
    if not root:
        return max_Et(r, t)
    return 1 - root  # type: ignore


def E_t_lower_antisym(lam: list[int], P_lam: float, t: int, r: int):
    # all SN for antisym proj
    """r is the number of variables (the expected SN)"""
    assert all([li == 1 for li in lam])
    assert t < r
    k = len(lam)
    assert k <= r

    def ek(x: float):
        res = schur_weyl_measure([x] + [(1 - x) / (k - 1)] * (k - 1), k)[tuple(lam)]
        return res - P_lam

    # if ek(1 / r) < 0 and ek(1) < 0 and P_lam - ek(1 / r) < 1e-7:
    #     return 1 / r

    # print(f"f(a) f(b) {ek(1/r)}, {ek(1)}")
    root = brentq(ek, 1 / r, 1, xtol=1e-10)
    if not root:
        return -1
    return 1 - root + ((1 - root) / (r - t)) * t  # type: ignore


def Et_lower(lam: list[int], P_lam: float, r: int) -> list[float]:
    if len(lam) == 2:
        return [E_t_lower_lambda_r2(lam, P_lam)]
    elif all([li == 1 for li in lam]):
        return [E_t_lower_antisym(lam, P_lam, t, r) for t in range(1, r)]
    else:
        raise ValueError("Robustness calculation not supported for this lambda")
