import picos

if __name__ == "__main__":
    print(picos.available_solvers())

import numpy as np
from SDP_utils.SDP_matrices import V_builder, alpha_dag_j_builder, isotypic_ot_I, W_l_builder
from SDP_utils.combinatorics import dim_sym_kd


def SDP(lam: list[int], rho: np.ndarray, m: int, n: int, solver="qics", verbose=False):
    k = sum(lam)
    d, _ = rho.shape
    assert d == m * n

    sym_d: int = dim_sym_kd(k, d)
    V = V_builder(k, d)
    a_dag = [alpha_dag_j_builder(k, d, j) for j in range(d)]
    AdA = [[picos.Constant(Ad @ A.T) for A in a_dag] for Ad in a_dag]
    VPi = picos.Constant(V @ isotypic_ot_I(m, n, k, lam) @ V.T)
    Wls = [(picos.Constant(W_l_builder(k, d, l)), dim_sym_kd(l, d), dim_sym_kd(k - l, d)) for l in range(1, k // 2 + 1)]

    P = picos.Problem(verbose=verbose)
    omega_sym = picos.HermitianVariable("omega_sym", sym_d)

    # objective:  min tr( (V Pi^lam(x)I V^dag) omega_sym )
    P.set_objective("min", picos.trace(VPi * omega_sym).real)  # type: ignore

    # (1) PSD
    P.add_constraint(omega_sym >> 0)

    # (2) marginal:  tr_{!=1}(omega)_{j,j'} = (1/k) tr( a_{j'}^dag a_j  omega ) = rho
    marg = picos.block([[(1 / k) * picos.trace(AdA[jp][j] * omega_sym) for jp in range(d)] for j in range(d)])  # type: ignore
    P.add_constraint(marg == picos.Constant("rho", rho))

    # (3) PPT on the l | k-l cuts,  l = 1 .. floor(k/2)
    for Wl, dl, dkl in Wls:
        B = Wl * omega_sym * Wl.T
        P.add_constraint(B.partial_transpose(subsystems=0, dimensions=(dl, dkl)) >> 0)  # type: ignore

    P.solve(solver=solver)
    return P.value, omega_sym.value


def SDP_full(lam: list[int], rho: np.ndarray, m: int, n: int, solver="qics"):
    """Schmidt-number SDP on the full (C^d)^{ot k} space — no symmetric reduction.

    Variable: omega_{1..k} in C^{d^k x d^k}, d = m*n (each copy is one A_iB_i system).
    """
    k = sum(lam)
    d, _ = rho.shape
    assert d == m * n

    Dk = d**k
    PiI = picos.Constant("PiI", isotypic_ot_I(m, n, k, lam))  # Pi^lam (x) I, order A_1B_1...A_kB_k
    Pi_sym = picos.Constant("Pi_sym", V_builder(k, d).T @ V_builder(k, d))  # = V^dag V
    rho_c = picos.Constant("rho", rho)

    P = picos.Problem()
    omega = picos.HermitianVariable("omega", Dk)

    # objective:  min tr( (Pi^lam (x) I) omega )
    P.set_objective("min", picos.trace(PiI * omega).real)  # type: ignore

    # (1) PSD
    P.add_constraint(omega >> 0)

    # (2) supported on the symmetric subspace:  Pi_sym omega Pi_sym = omega
    P.add_constraint(Pi_sym * omega * Pi_sym == omega)

    # (3) marginal:  tr_{!=1}(omega) = rho   (keep copy 0, trace out copies 1..k-1)
    P.add_constraint(omega.partial_trace(subsystems=list(range(1, k)), dimensions=[d] * k) == rho_c)  # type: ignore

    # (4) PPT on the cuts S = {1,...,l},  l = 1 .. floor(k/2)
    for l in range(1, k // 2 + 1):
        P.add_constraint(omega.partial_transpose(subsystems=list(range(l)), dimensions=[d] * k) >> 0)  # type: ignore

    P.solve(solver=solver)
    return P.value, omega.value
