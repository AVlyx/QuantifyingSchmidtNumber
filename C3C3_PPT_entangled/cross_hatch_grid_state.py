# https://arxiv.org/pdf/2010.08372 page 24,
# ! the set E_ch on page 24 is indexed at 1 instead of 0
import numpy as np
from math import sqrt


def ket(i: int, j: int):
    z = np.zeros(3 * 3)
    z[i * 3 + j] = 1
    return z


def grid_component(i: int, j: int, k: int, l: int):
    return 1 / sqrt(2) * (ket(i, j) - ket(k, l))


def C2_C2_grid_state(*E_ch_i: tuple[int, int, int, int]):
    ret = np.zeros((3 * 3, 3 * 3))
    for i, j, k, l in E_ch_i:
        gc = grid_component(i, j, k, l)
        ret += np.outer(gc, gc)
    ret /= len(E_ch_i)
    return ret


def cross_hatch_state():
    return C2_C2_grid_state((0, 0, 1, 2), (1, 0, 2, 2), (0, 1, 2, 0), (0, 2, 2, 1))


if __name__ == "__main__":
    print(cross_hatch_state())
