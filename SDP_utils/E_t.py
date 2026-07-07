import math


def E_t_lowerk2(r: int, t: int, P_lambda: float):
    etn = t + math.sqrt(t * (r - t) * (r - 2 * r * P_lambda - 1))
    return 1 - etn / r
