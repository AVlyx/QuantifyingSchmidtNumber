from toqito.rand import random_density_matrix
from toqito.state_props import is_ppt
import numpy as np


def CmCn_random_mixed_entangled_state(m, n) -> np.ndarray:
    while True:
        rho = random_density_matrix(m * n)
        if not is_ppt(rho, dim=[m, n]):
            return rho
