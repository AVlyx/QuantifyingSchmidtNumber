from toqito.state_props import is_ppt
import numpy as np
from CmCn_entangled.random_PPT import CmCn_random_not_PPT, CmCn_random_PPT


def random_edge_PPT(m: int, n: int, precision: int) -> np.ndarray:
    ppt: np.ndarray = CmCn_random_PPT(m, n)
    not_ppt: np.ndarray = CmCn_random_not_PPT(m, n)

    for _ in range(precision):
        temp = (ppt + not_ppt) / 2
        if is_ppt(temp, dim=[m, n]):
            ppt = temp
        else:
            not_ppt = temp
    return ppt / np.trace(ppt)


def random_edge_PPT_gen(m: int, n: int, precision: int):
    def gen(p):
        return random_edge_PPT(m, n, precision)

    return gen
