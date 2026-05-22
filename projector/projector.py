"""Sage-based isotropic projector computation (extracted from prjtcr.ipynb)."""
import itertools

import sage.all as sage
from sage.combinat.sf.sf import SymmetricFunctions
from sage.rings.rational_field import QQ

_Sym = SymmetricFunctions(QQ)
_s = _Sym.schur()
_p = _Sym.powersum()


def _Sn(n):
    for sigma in sage.SymmetricGroup(n):
        yield sigma


def _character(lam, sigma):
    mu = sage.Partition(sigma.cycle_type())
    return _p(_s(lam)).coefficient(mu) * mu.centralizer_size()


def isotropic_projector_fast(lam, d):
    """
    Isotypic projector Π_λ on (C^d)^⊗n, where n = sum(lam).

    lam : sage.Partition
    d   : local Hilbert-space dimension (number of qudit levels)
    """
    n = sum(lam)
    d_lambda = lam.dimension()
    dim = d ** n

    basis = list(itertools.product(range(d), repeat=n))
    basis_index = {b: i for i, b in enumerate(basis)}

    classes = {}
    for sigma in _Sn(n):
        mu = sage.Partition(sigma.cycle_type())
        classes.setdefault(mu, []).append(sigma)

    projector = sage.matrix(sage.QQ, dim, dim)
    for mu, sigmas in classes.items():
        chi = _character(lam, sigmas[0])
        if chi == 0:
            continue
        T_mu = sage.matrix(sage.ZZ, dim, dim)
        for sigma in sigmas:
            sigma_inv = sigma.inverse()
            for col, I in enumerate(basis):
                J = tuple(I[int(sigma_inv(k + 1)) - 1] for k in range(n))
                T_mu[basis_index[J], col] += 1
        projector += chi * T_mu

    return (d_lambda / sage.factorial(n)) * projector


def projector_to_json(P, lam_list, d):
    """Return (labels, matrix) where matrix entries are 'p/q' strings."""
    n = sum(lam_list)
    basis = list(itertools.product(range(d), repeat=n))
    labels = ["".join(str(x) for x in b) for b in basis]
    dim = len(basis)
    mat = [
        [str(P[i, j]) for j in range(dim)]
        for i in range(dim)
    ]
    return labels, mat
