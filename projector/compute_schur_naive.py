"""Subprocess worker — naive norm_sq_projected for any Young partition.

Usage:
  python compute_schur_naive.py '<lam_json>' '<si_squared_json>'
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


def norm_sq_projected_general(lam: list[int], sis: list[float]) -> float:
    r = len(sis)
    sisq = [si**2 for si in sis]
    k = sum(lam)
    Pi = isotypic_projector(lam, n=r, k=k)
    basis = list(iproduct(range(r), repeat=k))
    basis_index = {b: i for i, b in enumerate(basis)}
    total = 0.0
    for idx_tuple in basis:
        weight = math.prod(sisq[i] for i in idx_tuple)
        if weight == 0:
            continue
        total += weight * Pi[basis_index[idx_tuple], basis_index[idx_tuple]].real
    return total


lam = json.loads(sys.argv[1])
si_squared = json.loads(sys.argv[2])
sis = [math.sqrt(sq) for sq in si_squared]
result = norm_sq_projected_general(lam, sis)
print(json.dumps({"norm_sq_projected": result}))
