import math
import itertools
from itertools import product as iproduct

import numpy as np

import sage.all as sage
from sage.rings.rational_field import QQ
from sage.combinat.sf.sf import SymmetricFunctions

# Ring of symmetric functions over the rationals, with the two bases we need.
_Sym = SymmetricFunctions(QQ)
_s = _Sym.schur()  # Schur basis      s_lambda
_p = _Sym.powersum()  # power-sum basis  p_lambda


def permutation_matrix_on_tensor_power(sigma, n: int, k: int) -> np.ndarray:
    """Matrix of a permutation sigma in S_k acting on (C^n)^{otimes k}.

    The symmetric group permutes the k tensor factors:
        sigma |e_{i_1}> (x) ... (x) |e_{i_k}>  =  |e_{i_{sigma^{-1}(1)}}> (x) ... .
    The result is an (n^k) x (n^k) permutation matrix (a single 1 per column).

    Parameters
    ----------
    sigma : element of Sage's SymmetricGroup(k).
    n     : local dimension (single-factor space V = C^n).
    k     : number of tensor factors.
    """
    basis = list(iproduct(range(n), repeat=k))  # all index tuples (i_1, ..., i_k)
    index = {b: i for i, b in enumerate(basis)}  # tuple -> row/column position

    sigma_inv = sigma.inverse()
    dim = n**k
    M = np.zeros((dim, dim), dtype=complex)

    for col_idx, basis_vec in enumerate(basis):
        # Output factor j reads input factor sigma^{-1}(j) (Sage is 1-indexed).
        new_basis = tuple(basis_vec[sigma_inv(j + 1) - 1] for j in range(k))
        row_idx = index[new_basis]
        M[row_idx, col_idx] = 1.0

    return M


def isotypic_projector(lam: list[int], n: int, k: int) -> np.ndarray:
    """Isotypic projector Pi_lambda onto the lambda-component of (C^n)^{otimes k}.

    Implements
        Pi_lambda = (f^lambda / k!) * sum_{sigma in S_k} chi_lambda(sigma) sigma,
    where f^lambda = chi_lambda(id) = dim V^lambda. Since chi_lambda is constant
    on conjugacy classes, we read it once per class and reuse it for all members.

    Parameters
    ----------
    lam : partition of k labelling the target irrep V^lambda.
    n   : local dimension.
    k   : number of tensor factors (must equal sum(lam)).
    """
    assert sum(lam) == k
    lam = sorted(lam, reverse=True)

    Sk = sage.SymmetricGroup(k)
    char_table = Sk.character_table()
    classes = Sk.conjugacy_classes()

    # Locate the character-table row for lambda (reverse-lex ordering, as above).
    partitions_ordered = list(reversed(sage.Partitions(k).list()))
    row_idx = partitions_ordered.index(lam)

    # f^lambda = chi_lambda(identity) is the dimension of the irrep.
    id_idx = next(j for j, cl in enumerate(classes) if cl.representative().is_one())
    d_lam = int(char_table[row_idx][id_idx])

    dim = n**k
    Pi = np.zeros((dim, dim), dtype=complex)

    # Accumulate chi_lambda(sigma) * sigma over the whole group, class by class.
    for j, cl in enumerate(classes):
        chi = complex(char_table[row_idx][j])  # character is constant on the class
        for sigma in cl:
            M = permutation_matrix_on_tensor_power(sigma, n, k)
            Pi += chi * M

    Pi *= d_lam / sage.factorial(k)  # overall prefactor f^lambda / k!
    return Pi
