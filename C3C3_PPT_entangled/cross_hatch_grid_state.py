# https://arxiv.org/pdf/2010.08372 page 24,
# ! the set E_ch on page 24 is indexed at 1 instead of 0
import numpy as np
from math import sqrt


def ket(d: int, i: int, j: int):
    z = np.zeros(d * d)
    z[i * d + j] = 1
    return z


def grid_component(d: int, i: int, j: int, k: int, l: int):
    return 1 / sqrt(2) * (ket(d, i, j) - ket(d, k, l))


def grid_state(d: int, *E_ch_i: tuple[int, int, int, int]):
    ret = np.zeros((d * d, d * d))
    print(type(E_ch_i))
    for i, j, k, l in E_ch_i:
        gc = grid_component(d, i, j, k, l)
        ret += np.outer(gc, gc)
    ret /= len(E_ch_i)
    return ret


def cross_hatch_state():
    return grid_state(3, (0, 0, 1, 2), (1, 0, 2, 2), (0, 1, 2, 0), (0, 2, 2, 1))


if __name__ == "__main__":
    print(cross_hatch_state())
