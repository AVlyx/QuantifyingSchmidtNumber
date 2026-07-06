from toqito.rand import random_density_matrix
from toqito.state_props import is_ppt
import numpy as np


def C2C2_random_mixed_entangled_state() -> np.ndarray:
    while True:
        rho = random_density_matrix(2 * 2)
        if not is_ppt(rho):
            return rho


def C2C2_random_mixed_entangled_state_tiny_eigen_value() -> np.ndarray:
    while True:
        rho = random_density_matrix(2 * 2)
        if is_ppt(rho):
            continue
        eigvals, _ = np.linalg.eigh(rho)
        if eigvals[0] > 0.01:
            continue
        return rho
