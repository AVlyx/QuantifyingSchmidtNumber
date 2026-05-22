"""Subprocess worker — isotypic projector and vector check.

Usage:
  matrix only:   python compute_projector.py '<lam_json>' <n>
  vector check:  python compute_projector.py '<lam_json>' <n> '<v_json>'
"""
import sys
import json
import numpy as np
import sage.all as sage
from itertools import product as iproduct


# ── Core functions from prjtcr.ipynb ────────────────────────────────────────

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


def pi_times_ket(lam: list[int], n: int, v: list[int]) -> np.ndarray:
    """Compute Pi_lam @ ket(v) without building the full matrix."""
    k = len(v)
    lam = sorted(lam, reverse=True)
    Sk = sage.SymmetricGroup(k)
    ct = Sk.character_table()
    classes = Sk.conjugacy_classes()
    partitions_ordered = list(reversed(sage.Partitions(k).list()))
    row_idx = partitions_ordered.index(lam)
    id_idx = next(j for j, cl in enumerate(classes) if cl.representative().is_one())
    d_lam = int(ct[row_idx][id_idx])

    basis = list(iproduct(range(n), repeat=k))
    index = {b: i for i, b in enumerate(basis)}
    dim = n ** k
    result = np.zeros(dim, dtype=complex)

    for j, cl in enumerate(classes):
        chi = complex(ct[row_idx][j])
        if chi == 0:
            continue
        for sigma in cl:
            sigma_inv = sigma.inverse()
            new_v = tuple(v[sigma_inv(i + 1) - 1] for i in range(k))
            result[index[new_v]] += chi

    result *= d_lam / int(sage.factorial(k))
    return result


def nu(v: list[int], n: int) -> list[int]:
    ret = [0] * n
    for i in v:
        ret[i] += 1
    ret.sort(reverse=True)
    return [x for x in ret if x != 0]


def majorizes(nuv: list[int], lam: list[int]) -> bool:
    lams = 0
    vs = 0
    for i in range(min(len(lam), len(nuv))):
        lams += lam[i]
        vs += nuv[i]
        if vs > lams:
            return True
    return False


# ── Dispatch ─────────────────────────────────────────────────────────────────

lam_list = json.loads(sys.argv[1])
n = int(sys.argv[2])
v = json.loads(sys.argv[3]) if len(sys.argv) > 3 else None
k = sum(lam_list)

if v is None:
    Pi = isotypic_projector(lam_list, n, k)
    basis = list(iproduct(range(n), repeat=k))
    labels = ["".join(str(x) for x in b) for b in basis]
    mat = [[round(Pi[i, j].real, 8) for j in range(n ** k)] for i in range(n ** k)]
    print(json.dumps({"labels": labels, "matrix": mat}))
else:
    projected = pi_times_ket(lam_list, n, v)
    nuv = nu(v, n)
    print(json.dumps({
        "nuv": nuv,
        "majorized": majorizes(nuv, sorted(lam_list, reverse=True)),
        "pi_ket_norm": float(np.linalg.norm(projected)),
    }))
