import math


def E_t_lowerk2(r: int, t: int, P_lambda: float):
    etn = t + math.sqrt(t * (r - t) * (r - 2 * r * P_lambda - 1))
    return 1 - etn / r


def E_t_upperk2r2(P_lambda: float):
    if P_lambda > 0.25:
        return 1
    return (1 - math.sqrt(1 - 4 * P_lambda)) / 2
