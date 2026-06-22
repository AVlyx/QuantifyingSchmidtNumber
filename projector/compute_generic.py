"""Subprocess worker — norm_sq_projected for generic Schmidt vector.

Usage:
  python compute_generic.py <lambda1> <k> '<si_squared_json>'
"""
import sys
import json
import math
import numpy as np
import sage.all as sage
from itertools import product as iproduct


def isotypic_projector(lam: list[int], n: int, k: int) -> np.ndarray:
    lam = sorted(lam, reverse=True)
    Sk = sage.SymmetricGroup(k)
    ct = Sk.character_table()
    classes = Sk.conjugacy_classes()
    partitions_ordered = list(reversed(sage.Partitions(k).list()))
    row_idx = partitions_ordered.index(lam)
    id_idx = next(j for j, cl in enumerate(classes) if cl.representative().is_one())
    d_lam = int(ct[row_idx][id_idx])

    basis = list(iproduct(range(n), repeat=k))
    basis_index = {b: i for i, b in enumerate(basis)}
    dim = n ** k
    Pi = np.zeros((dim, dim), dtype=complex)

    for j, cl in enumerate(classes):
        chi = complex(ct[row_idx][j])
        if chi == 0:
            continue
        for sigma in cl:
            sigma_inv = sigma.inverse()
            M = np.zeros((dim, dim), dtype=complex)
            for col_idx, bv in enumerate(basis):
                nb = tuple(bv[sigma_inv(j2 + 1) - 1] for j2 in range(k))
                M[basis_index[nb], col_idx] = 1.0
            Pi += chi * M

    Pi *= d_lam / int(sage.factorial(k))
    return Pi


def norm_sq_projected(sis: list[float], lambda1: int, k: int) -> float:
    r = len(sis)
    sisq = [si**2 for si in sis]

    lam = [lambda1] + [1] * (k - lambda1)
    Pi = isotypic_projector(lam, n=r, k=k)

    basis = list(iproduct(range(r), repeat=k))
    basis_index = {b: i for i, b in enumerate(basis)}

    total = 0.0
    for idx_tuple in basis:
        weight = math.prod(sisq[i] for i in idx_tuple)
        if weight == 0:
            continue
        row = basis_index[idx_tuple]
        total += weight * Pi[row, row].real

    return total


lambda1 = int(sys.argv[1])
k = int(sys.argv[2])
si_squared = json.loads(sys.argv[3])

sis = [math.sqrt(sq) for sq in si_squared]
result = norm_sq_projected(sis, lambda1, k)
print(json.dumps({"norm_sq_projected": result}))
