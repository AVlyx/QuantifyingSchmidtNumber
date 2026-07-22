import numpy as np


def convex_combination(A: np.ndarray, B: np.ndarray, p_low: float, p_high: float, p_step: float):
    assert p_step > 0
    assert p_low >= 0
    assert p_high <= 1
    while p_low < p_high:
        yield (p_low, p_low * A + (1 - p_low) * B)
        p_low += p_step
