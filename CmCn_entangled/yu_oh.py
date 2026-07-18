import numpy as np
from bound_entangled.cd_otimes_cd import yu_oh, is_valid_yu_oh_input


def yu_oh_gen(d: int, start: float, end: float, step: float):
    assert start < end
    assert step > 0
    steps = np.arange(start, end + step, step)
    for x in steps:
        for y in steps:
            if not is_valid_yu_oh_input(d, x, y):
                continue

            yield (x, y), yu_oh(d, x, y)
