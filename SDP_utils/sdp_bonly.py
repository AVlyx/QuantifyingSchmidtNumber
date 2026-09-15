"""One-sided ("Bob-copies-only") version of the weak-Schur convex-roof SDP.

Systems are ordered  A, B_1, ..., B_k  (dims m, n, ..., n).

    min  tr( (I_A (x) Pi_{B_1..B_k}) sigma )
    s.t. sigma >= 0
         tr_{B_2..B_k} sigma = rho
         sigma invariant under S_{k-1} permuting B_2..B_k
         tr_A sigma invariant under S_k permuting B_1..B_k      (needed for height >= 2,
                                                                 otherwise Phi (x) |0><0|^{k-1} has objective 0)
         sigma^{T_S} >= 0 for S = {B_{k-j+1}..B_k}, j = 1..k-1   (cuts never separating A from B_1)
         optional: sigma <= r (tr_{B_1} sigma) (x) I_{B_1}      (reduction-type, valid for SN <= r = height-1)
         optional: sigma^{T_{B_1..B_k}} >= 0                     (extra cut, valid for r = 1 only)

Pi is the isotypic projector on B^{(x)k} onto the shapes of height >= `height` when
`exact_height=False` (nested, monotone hierarchy), or of height == `height` when
`exact_height=True` (same convention as SDP_utils.sdp.SDP).

For a pure state of Schmidt rank <= r the roof extension psi_{AB_1} (x) psi_B^{(x)(k-1)}
satisfies every constraint and has objective 0 whenever height >= r + 1.
"""
import itertools
import numpy as np
import picos
from schur_weyl import isotypic_proj, partitions


def _perm_matrix(dims: list[int], perm: list[int]) -> np.ndarray:
    """Permutation operator sending tensor factor i to position perm[i]:
    P |i_0 ... i_{k-1}> = |j_0 ... j_{k-1}>  with  j_{perm[i]} = i_i."""
    N = int(np.prod(dims))
    P = np.zeros((N, N))
    for idx in itertools.product(*[range(x) for x in dims]):
        new = [0] * len(dims)
        for i, p in enumerate(perm):
            new[p] = idx[i]
        P[np.ravel_multi_index(new, dims), np.ravel_multi_index(idx, dims)] = 1
    return P


def height_projector(n: int, k: int, height: int, exact_height: bool) -> np.ndarray:
    parts = partitions(k, height=height) if exact_height else partitions(k, min_height=height)
    Pi = np.zeros((n**k, n**k))
    for lam in parts:
        Pi += isotypic_proj(lam, n)
    return Pi


def SDP_bonly(
    height: int,
    k: int,
    rho: np.ndarray,
    dims: tuple[int, int],
    solver="qics",
    verbose=False,
    real=False,
    *,
    exact_height=False,
    marginal_symmetry=True,
    reduction=False,
    extra_cut=False,
) -> tuple[float, np.ndarray]:
    m, n = dims
    d = m * n
    assert rho.shape == (d, d)
    N = m * n**k
    sysdims = [m] + [n] * k

    P = picos.Problem(verbosity=verbose)
    sigma = picos.SymmetricVariable("sigma", N) if real else picos.HermitianVariable("sigma", N)

    Pi = picos.Constant("Pi", np.kron(np.identity(m), height_projector(n, k, height, exact_height)))
    P.set_objective("min", picos.trace(Pi * sigma).real)  # type: ignore

    P.add_constraint(sigma >> 0)

    # marginal on A B_1
    P.add_constraint(sigma.partial_trace(subsystems=1, dimensions=(d, n ** (k - 1))) == picos.Constant("rho", rho))

    # S_{k-1} on B_2..B_k (adjacent transpositions generate it)
    for i in range(2, k):
        perm = list(range(k + 1))
        perm[i], perm[i + 1] = perm[i + 1], perm[i]
        Pm = picos.Constant(f"P{i}", _perm_matrix(sysdims, perm))
        P.add_constraint(Pm * sigma * Pm.T == sigma)

    # tr_A sigma S_k-invariant: with the above, the transposition (B_1 B_2) suffices
    if marginal_symmetry and k >= 2:
        sB = sigma.partial_trace(subsystems=0, dimensions=(m, n**k))
        P12 = picos.Constant("P12", _perm_matrix([n] * k, [1, 0] + list(range(2, k))))
        P.add_constraint(P12 * sB * P12.T == sB)

    # PPT: transpose the last j copies of B
    for j in range(1, k):
        P.add_constraint(sigma.partial_transpose(subsystems=1, dimensions=(m * n ** (k - j), n**j)) >> 0)  # type: ignore

    if extra_cut:  # A | B_1..B_k, valid for height == 2 (r = 1) only
        assert height == 2
        P.add_constraint(sigma.partial_transpose(subsystems=1, dimensions=(m, n**k)) >> 0)  # type: ignore

    if reduction:
        r = height - 1
        red = sigma.partial_trace(subsystems=1, dimensions=(m, n, n ** (k - 1)))  # on A B_2..B_k
        big = red @ picos.Constant("I_n", np.identity(n))  # A B_2..B_k B_1
        Pr = picos.Constant("Pred", _perm_matrix([m] + [n] * k, [0] + list(range(2, k + 1)) + [1]))
        P.add_constraint(r * (Pr * big * Pr.T) - sigma >> 0)

    P.solve(solver=solver)
    return P.value, sigma.value


if __name__ == "__main__":
    from toqito.states import bell

    b = bell(0)
    B = np.real(b @ b.conj().T)
    print("bell height=2 k=2:", SDP_bonly(2, 2, B, (2, 2), real=True)[0], "expect 0.25")
    print("bell height=2 k=3:", SDP_bonly(2, 3, B, (2, 2), real=True)[0], "expect 0.5")
    print("bell height=3 k=3:", SDP_bonly(3, 3, B, (2, 2), real=True)[0], "expect 0")
