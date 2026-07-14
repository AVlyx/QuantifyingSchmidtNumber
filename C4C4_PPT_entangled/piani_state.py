from toqito.matrices import pauli
from toqito.states import max_entangled
from toqito.perms import permute_systems
import numpy as np


def P_ij(i: int, j: int):
    sigma_ij = np.kron(np.identity(4), np.kron(pauli(i), pauli(j)))  # type: ignore
    ket_ij = sigma_ij @ max_entangled(4)
    return np.outer(ket_ij, ket_ij)


def pianni():
    rho = np.zeros((16, 16), dtype=np.complex128)
    for i, j in [(0, 2), (1, 1), (2, 3), (3, 1), (3, 2), (3, 3)]:
        rho += P_ij(i, j)
    rho /= 6
    return permute_systems(rho, [0, 2, 1, 3])


if __name__ == "__main__":
    print(pianni())
