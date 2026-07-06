from toqito.rand import random_density_matrix
from toqito.state_props import is_ppt
import numpy as np


def C2C2_random_mixed_entangled_state() -> np.ndarray:
    while True:
        rho = random_density_matrix(2 * 2)
        if not is_ppt(rho):
            return rho
