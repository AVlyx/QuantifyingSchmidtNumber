import numpy as np
from math import sqrt


def steering_state(m1: float, m2: float):
    m3 = sqrt((1 - m1**2 - m2**2) / 2)

    psi_1 = np.zeros(9, dtype=np.float64)
    psi_2 = np.zeros(9, dtype=np.float64)
    psi_3 = np.zeros(9, dtype=np.float64)
    psi_t_3 = np.zeros(9, dtype=np.float64)

    psi_1[1 * 3 + 2], psi_1[2 * 3 + 1] = 1 / sqrt(2), 1 / sqrt(2)
    psi_2[0], psi_2[1 * 3 + 1], psi_2[2 * 3 + 2] = 1 / sqrt(3), 1 / sqrt(3), -1 / sqrt(3)
    psi_3[1], psi_3[1 * 3], psi_3[1 * 3 + 1], psi_3[2 * 3 + 2] = m1, m2, m3, m3
    psi_t_3[2], psi_t_3[2 * 3], psi_t_3[2 * 3 + 1], psi_t_3[1 * 3 + 2] = m1, -m2, m3, -m3

    lambda1 = 1 - (2 + 3 * m1 * m2) / (4 - 2 * m1**2 + m1 * m2 - 2 * m2**2)
    lambda3 = 1 / (4 - 2 * m1**2 + m1 * m2 - 2 * m2**2)
    lambda2 = 1 - lambda1 - 2 * lambda3

    return lambda1 * np.outer(psi_1, psi_1) + lambda2 * np.outer(psi_2, psi_2) + lambda3 * (np.outer(psi_3, psi_3) + np.outer(psi_t_3, psi_t_3))


def steering_state_gen(start: float, end: float, step: float):
    assert start < end
    assert step > 0
    steps = np.arange(start, end + step, step)
    for m1 in steps:
        if m1 <= 0:
            continue
        for m2 in steps:
            if m2 <= 0:
                continue
            lambda1 = 1 - (2 + 3 * m1 * m2) / (4 - 2 * m1**2 + m1 * m2 - 2 * m2**2)
            lambda3 = 1 / (4 - 2 * m1**2 + m1 * m2 - 2 * m2**2)
            lambda2 = 1 - lambda1 - 2 * lambda3
            if lambda1 <= -1e-10 or lambda2 <= -1e-10 or lambda3 <= -1e-10:
                continue

            yield (m1, m2), steering_state(m1, m2)
