from toqito.states import max_entangled
import numpy as np
from math import sqrt


def psi_ij(d: int, i: int, j: int):
    ket = np.zeros(d * d)
    ket[i * d + j] = 1
    ket[j * d + i] = -1
    return ket


def teta_d_gen(d: int):
    Teta_d = [
        np.array([0.0, 1.0] + [0.0] * (d - 2)),
        np.array([0.0, -1.0] + [0.0] * (d - 2)),
    ]
    for di in range(3, d + 1):
        ket_dm1 = np.zeros(d, dtype=np.float64)
        ket_dm1[di - 1] = 1.0
        sqrtddm2 = sqrt(di * (di - 2))
        Teta_d_new = [(sqrtddm2 * teta_p - ket_dm1) / (di - 1) for teta_p in Teta_d]
        Teta_d = Teta_d_new + [ket_dm1]
    return Teta_d


def phi_k(d: int, k: int):
    ret = np.zeros(d**2, dtype=np.float64)
    for teta_p in teta_d_gen(d):
        innerprod = teta_p[k]
        ret += np.kron(teta_p, teta_p) * innerprod
    ret *= ((d - 1) ** (3 / 2)) / (d * sqrt(d - 2))
    return ret


def psi_k(d: int, k: int, x: float, y: float, z: float):
    ret: np.ndarray = np.zeros(d**2)
    ret[k] = x
    ret[k * d] = y
    ret += z * phi_k(d, k)
    return ret


def yu_oh(d: int, x: float, y: float):
    assert x**2 + y**2 <= 1
    z = sqrt(1 - x**2 - y**2)
    delta = z**2 / (d - 2) - x * y
    assert delta > 0
    R = d * x * y + (d - 1) * (d - 2) * delta + d - 1

    max_ent_ket: np.ndarray = max_entangled(d) * sqrt(d)  # type: ignore
    ret = x * y / R * np.outer(max_ent_ket, max_ent_ket)

    psi_ij_sum = np.zeros((d**2, d**2))
    for j in range(1, d - 1):
        for i in range(j + 1, d):
            psi_ij_val = psi_ij(d, i, j)
            psi_ij_sum += np.outer(psi_ij_val, psi_ij_val)
    ret += delta / R * psi_ij_sum

    psi_k_sum = np.zeros((d**2, d**2))
    for k in range(1, d):
        psi_k_val = psi_k(d, k, x, y, z)
        psi_k_sum += np.outer(psi_k_val, psi_k_val)
    ret += psi_k_sum / R
    return ret


def yu_oh_gen(d: int, start: float, end: float, step: float):
    assert start < end
    assert step > 0
    steps = np.arange(start, end + step, step)
    for x in steps:
        for y in steps:
            if x**2 + y**2 > 1:
                continue
            z = sqrt(1 - x**2 - y**2)
            delta = z**2 / (d - 2) - x * y
            if delta <= 0:
                continue

            yield (x, y), yu_oh(d, x, y)


if __name__ == "__main__":
    print(np.trace(yu_oh(3, 0.2, 0.3)))
    print(yu_oh(3, 0.2, 0.3))
