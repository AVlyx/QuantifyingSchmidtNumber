from functools import lru_cache
from itertools import permutations
from math import factorial
import numpy as np

# import sage.all as sage
# from sage.rings.rational_field import QQ
# from sage.combinat.sf.sf import SymmetricFunctions

# # Ring of symmetric functions over the rationals, with the two bases we need.
# _Sym = SymmetricFunctions(QQ)
# _s = _Sym.schur()  # Schur basis      s_lambda
# _p = _Sym.powersum()  # power-sum basis  p_lambda


# def permutation_matrix_on_tensor_power(sigma, n: int, k: int) -> np.ndarray:
#     """Matrix of a permutation sigma in S_k acting on (C^n)^{otimes k}.

#     The symmetric group permutes the k tensor factors:
#         sigma |e_{i_1}> (x) ... (x) |e_{i_k}>  =  |e_{i_{sigma^{-1}(1)}}> (x) ... .
#     The result is an (n^k) x (n^k) permutation matrix (a single 1 per column).

#     Parameters
#     ----------
#     sigma : element of Sage's SymmetricGroup(k).
#     n     : local dimension (single-factor space V = C^n).
#     k     : number of tensor factors.
#     """
#     basis = list(iproduct(range(n), repeat=k))  # all index tuples (i_1, ..., i_k)
#     index = {b: i for i, b in enumerate(basis)}  # tuple -> row/column position

#     sigma_inv = sigma.inverse()
#     dim = n**k
#     M = np.zeros((dim, dim), dtype=complex)

#     for col_idx, basis_vec in enumerate(basis):
#         # Output factor j reads input factor sigma^{-1}(j) (Sage is 1-indexed).
#         new_basis = tuple(basis_vec[sigma_inv(j + 1) - 1] for j in range(k))
#         row_idx = index[new_basis]
#         M[row_idx, col_idx] = 1.0

#     return M


# def isotypic_projector_sage(lam: list[int], n: int, k: int) -> np.ndarray:
#     """Isotypic projector Pi_lambda onto the lambda-component of (C^n)^{otimes k}.

#     Implements
#         Pi_lambda = (f^lambda / k!) * sum_{sigma in S_k} chi_lambda(sigma) sigma,
#     where f^lambda = chi_lambda(id) = dim V^lambda. Since chi_lambda is constant
#     on conjugacy classes, we read it once per class and reuse it for all members.

#     Parameters
#     ----------
#     lam : partition of k labelling the target irrep V^lambda.
#     n   : local dimension.
#     k   : number of tensor factors (must equal sum(lam)).
#     """
#     assert sum(lam) == k
#     lam = sorted(lam, reverse=True)

#     Sk = sage.SymmetricGroup(k)
#     char_table = Sk.character_table()
#     classes = Sk.conjugacy_classes()

#     # Locate the character-table row for lambda (reverse-lex ordering, as above).
#     partitions_ordered = list(reversed(sage.Partitions(k).list()))  # type: ignore
#     row_idx = partitions_ordered.index(lam)

#     # f^lambda = chi_lambda(identity) is the dimension of the irrep.
#     id_idx = next(j for j, cl in enumerate(classes) if cl.representative().is_one())
#     d_lam = int(char_table[row_idx][id_idx])

#     dim = n**k
#     Pi = np.zeros((dim, dim), dtype=complex)

#     # Accumulate chi_lambda(sigma) * sigma over the whole group, class by class.
#     for j, cl in enumerate(classes):
#         chi = complex(char_table[row_idx][j])  # character is constant on the class
#         for sigma in cl:
#             M = permutation_matrix_on_tensor_power(sigma, n, k)
#             Pi += chi * M

#     Pi *= d_lam / sage.factorial(k)  # overall prefactor f^lambda / k!
#     return Pi


# ---------------------------------------------------------------------------
# Partitions
# ---------------------------------------------------------------------------


def partitions(k: int, max_part: int | None = None):
    """Yield partitions of ``k`` as non-increasing tuples, in reverse-lex order.

    >>> list(partitions(4))
    [(4,), (3, 1), (2, 2), (2, 1, 1), (1, 1, 1, 1)]
    """
    if max_part is None:
        max_part = k
    if k == 0:
        yield ()
        return
    for j in range(min(k, max_part), 0, -1):
        for rest in partitions(k - j, j):
            yield (j,) + rest


# ---------------------------------------------------------------------------
# Murnaghan-Nakayama rule (via beta-sets)
# ---------------------------------------------------------------------------


def _beta_set(lam: tuple[int, ...]) -> tuple[int, ...]:
    """First-column hook lengths: beta_i = lam_i + (m - i), m = len(lam)."""
    m = len(lam)
    return tuple(lam[i] + (m - 1 - i) for i in range(m))


def _from_beta(beta) -> tuple[int, ...]:
    """Invert ``_beta_set``: sort descending, subtract the staircase, drop zeros."""
    b = sorted(beta, reverse=True)
    m = len(b)
    return tuple(x for x in (b[i] - (m - 1 - i) for i in range(m)) if x > 0)


@lru_cache(maxsize=None)
def character(lam: tuple[int, ...], rho: tuple[int, ...]) -> int:
    """Irreducible character chi^lambda(rho) of S_k.

    ``lam`` -- partition of k labelling the irrep (non-increasing tuple)
    ``rho`` -- cycle type of the conjugacy class (partition of k, any order)

    Removing an r-rim-hook from lambda corresponds, in the beta-set picture, to
    picking b in B with b >= r and b - r not in B, then replacing b by b - r.
    The leg length (height) is the number of beta values strictly between them.

    >>> character((3, 2), (3, 1, 1))
    -1
    >>> character((2, 1), (1, 1, 1))
    2
    """
    if sum(lam) == 0:
        return 1

    r, rest = rho[0], rho[1:]
    bset = set(_beta_set(lam))

    total = 0
    for b in list(bset):
        if b >= r and (b - r) not in bset:
            height = sum(1 for x in bset if b - r < x < b)
            total += (-1) ** height * character(_from_beta((bset - {b}) | {b - r}), rest)
    return total


def specht_dim(lam) -> int:
    """f^lambda = dim V^lambda = chi^lambda(1^k), the S_k irrep dimension."""
    lam = tuple(sorted(lam, reverse=True))
    return character(lam, (1,) * sum(lam))


def weyl_dim(lam, n: int) -> int:
    """dim W_lambda for U(n)/GL(n), via the Weyl dimension formula.

    Returns 0 when lambda has more than n rows (that block is absent).
    """
    lam = tuple(sorted(lam, reverse=True))
    if len(lam) > n:
        return 0
    ext = list(lam) + [0] * (n - len(lam))
    num = den = 1
    for i in range(n):
        for j in range(i + 1, n):
            num *= ext[i] - ext[j] + j - i
            den *= j - i
    return num // den


def character_table(k: int):
    """Return ``(labels, table)`` -- the character table of S_k.

    ``table[i][j] = chi^{labels[i]}(labels[j])``, rows indexed by irrep and
    columns by conjugacy class, both in ``partitions(k)`` order.
    """
    parts = list(partitions(k))
    return parts, [[character(lam, rho) for rho in parts] for lam in parts]


# ---------------------------------------------------------------------------
# The S_k action on (C^n)^{otimes k}
# ---------------------------------------------------------------------------


def cycle_type(sigma) -> tuple[int, ...]:
    """Cycle type of a permutation in one-line form (0-based image list)."""
    k = len(sigma)
    seen = [False] * k
    ct = []
    for i in range(k):
        if not seen[i]:
            length, j = 0, i
            while not seen[j]:
                seen[j] = True
                j = sigma[j]
                length += 1
            ct.append(length)
    ct.sort(reverse=True)
    return tuple(ct)


def _flat_permutation_index(sigma, n: int) -> np.ndarray:
    k = len(sigma)
    idx = np.arange(n**k).reshape((n,) * k)
    inv = np.argsort(np.asarray(sigma))  # sigma^{-1}
    return np.transpose(idx, axes=inv).ravel()


def permutation_operator(sigma, n: int) -> np.ndarray:
    """Dense permutation matrix R(sigma) on (C^n)^{otimes k}, k = len(sigma)."""
    D = n ** len(sigma)
    R = np.zeros((D, D))
    R[np.arange(D), _flat_permutation_index(sigma, n)] = 1.0
    return R


def isotypic_projector(lam: list[int], n: int, k: int) -> np.ndarray:
    assert sum(lam) == k, f"sum(lam) = {sum(lam)} != k = {k}"
    lam = sorted(lam, reverse=True)

    D = n**k
    if len(lam) > n:
        return np.zeros((D, D))

    # chi is a class function: evaluate once per cycle type, reuse per member.
    chi_of_class = {rho: character(tuple(lam), rho) for rho in partitions(k)}

    Pi = np.zeros((D, D))
    rows = np.arange(D)
    for sigma in permutations(range(k)):
        chi = chi_of_class[cycle_type(sigma)]
        if chi:
            Pi[rows, _flat_permutation_index(sigma, n)] += chi
    Pi *= specht_dim(lam) / factorial(k)
    return Pi


# ---------------------------------------------------------------------------
# A/B test against the Sage implementation
# ---------------------------------------------------------------------------

# if __name__ == "__main__":
#     # (lam, n) pairs; k is always sum(lam).  Includes len(lam) > n cases, where
#     # the block is absent and both implementations must give zero.
#     CASES = [
#         ([2], 2),
#         ([1, 1], 2),
#         ([1, 1], 3),
#         ([3], 2),
#         ([2, 1], 2),
#         ([2, 1], 3),
#         ([1, 1, 1], 2),
#         ([1, 1, 1], 3),
#         ([1, 1, 1], 4),
#         ([4], 2),
#         ([3, 1], 2),
#         ([2, 2], 2),
#         ([2, 1, 1], 2),
#         ([2, 1, 1], 3),
#         ([1, 1, 1, 1], 2),
#         ([1, 1, 1, 1], 4),
#         ([3, 2], 2),
#         ([3, 2], 3),
#         ([2, 2, 1], 3),
#         ([1, 2], 3),  # deliberately unsorted input
#     ]

#     print(f"{'lam':<14}{'n':>3}{'k':>3}{'D':>7}   vs Sage      self-check")
#     print("-" * 62)

#     all_match, all_self = True, True
#     for lam, n in CASES:
#         k = sum(lam)
#         P = isotypic_projector(lam, n, k)

#         # --- structural self-check (does not need Sage) --------------------
#         lam_s = tuple(sorted(lam, reverse=True))
#         checks = [
#             np.allclose(P @ P, P),  # idempotent
#             np.allclose(P, P.T),  # self-adjoint
#             abs(np.trace(P) - specht_dim(lam_s) * weyl_dim(lam_s, n)) < 1e-9,
#         ]
#         self_ok = all(checks)
#         all_self &= self_ok

#         # --- comparison against Sage ---------------------------------------
#         Q = np.asarray(isotypic_projector_sage(list(lam), n, k))
#         match = np.allclose(P, Q, atol=1e-10)
#         verdict = "MATCH" if match else f"DIFF {np.abs(P - Q).max():.2e}"
#         all_match &= match

#         print(f"{str(lam):<14}{n:>3}{k:>3}{n**k:>7}   {verdict:<12}" f"{'ok' if self_ok else 'FAILED'}")

#     # --- global identities, per (n, k) -------------------------------------
#     print("\nresolution of identity  sum_lambda Pi_lambda = I:")
#     for n, k in [(2, 2), (2, 3), (3, 3), (2, 4), (3, 4), (4, 3), (2, 5)]:
#         Pis = [isotypic_projector(list(l), n, k) for l in partitions(k)]
#         res = np.allclose(sum(Pis), np.eye(n**k))
#         orth = all(np.allclose(A @ B, 0) for i, A in enumerate(Pis) for B in Pis[i + 1 :])
#         print(f"  n={n}, k={k}, D={n**k:<5} sum=I: {res}   mutually orthogonal: {orth}")
#         all_self &= res and orth

#     print()
#     print("Sage agreement:", "ALL MATCH" if all_match else "MISMATCHES FOUND")
#     print("Self-consistency:", "all ok" if all_self else "FAILURES")
