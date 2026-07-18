import numpy as np
from bound_entangled.c3_otimes_c3 import steering_state


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
