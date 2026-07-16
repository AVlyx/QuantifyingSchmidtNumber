from toqito.rand import random_density_matrix
from toqito.state_props import is_ppt
import numpy as np


def CmCn_random_not_PPT(m, n) -> np.ndarray:
    while True:
        rho = random_density_matrix(m * n)
        if not is_ppt(rho, dim=[m, n]):
            return rho


def CmCn_random_PPT(m, n) -> np.ndarray:
    while True:
        rho = random_density_matrix(m * n)
        if is_ppt(rho, dim=[m, n]):
            return rho


def random_not_PPT_gen(m: int, n: int):
    def gen(p):
        return CmCn_random_not_PPT(m, n)

    return gen


def random_PPT_gen(m: int, n: int):
    def gen(p):
        return CmCn_random_PPT(m, n)

    return gen
