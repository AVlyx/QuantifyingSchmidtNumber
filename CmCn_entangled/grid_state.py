# https://arxiv.org/pdf/2010.08372 page 24,
# ! the set E_ch on page 24 is indexed at 1 instead of 0
import numpy as np
from math import sqrt


def grid_component(d: int, *ij: tuple[int, int]):
    e = np.zeros(d * d)
    for i, j in ij:
        e[i * d + j] = 1
    return e


def grid_state(d: int, *hyperedges: list[tuple[int, int]]):
    rho = np.zeros((d * d, d * d))
    for edge in hyperedges:
        gc = grid_component(d, *edge)
        rho += np.outer(gc, gc)
    rho /= np.trace(rho)
    return rho


# def cross_hatch_state():
#     return grid_state(3, [(0, 0), (1, 2)], [(1, 0), (2, 2)], [(0, 1), (2, 0)], [(0, 2), (2, 1)])


def sn3_C5C5_grid_state():
    return grid_state(
        5,
        # loops
        [(0, 0)],
        [(1, 0)],
        [(0, 1)],
        [(4, 1)],
        [(4, 1)],
        # double loops
        [(3, 2)],
        [(2, 3)],
        [(3, 2)],
        [(2, 3)],
        # edges
        [(1, 2), (3, 4)],
        [(2, 1), (4, 3)],
        [(2, 2), (3, 3)],
        # hyperedge
        [(0, 2), (1, 1), (2, 0)],
    )


if __name__ == "__main__":
    print(sn3_C5C5_grid_state())
