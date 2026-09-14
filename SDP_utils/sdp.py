import picos

if __name__ == "__main__":
    print(picos.available_solvers())

import numpy as np
from SDP_utils.SDP_matrices import V_builder, alpha_dag_j_builder, isotypic_ot_I, W_l_builder
from SDP_utils.combinatorics import dim_sym_kd


def SDP(
    height: int,
    k: int,
    rho: np.ndarray,
    dims: tuple[int, int],
    solver="qics",
    verbose=False,
    real=False,
) -> tuple[float, np.ndarray]:
    d, _ = rho.shape
    m, n = dims
    assert d == m * n

    sym_d: int = dim_sym_kd(k, d)
    V = V_builder(k, d)
    a_dag = [alpha_dag_j_builder(k, d, j) for j in range(d)]
    AdA = [[picos.Constant(Ad @ A.T) for A in a_dag] for Ad in a_dag]
    VPi = picos.Constant(V @ isotypic_ot_I(m, n, k, height) @ V.T)
    Wls = [(picos.Constant(W_l_builder(k, d, l)), dim_sym_kd(l, d), dim_sym_kd(k - l, d)) for l in range(1, k // 2 + 1)]

    P = picos.Problem(verbosity=verbose)
    omega_sym = picos.SymmetricVariable("omega_sym", sym_d) if real else picos.HermitianVariable("omega_sym", sym_d)

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


def SDP_max(
    height: int,
    k: int,
    rho: np.ndarray,
    dims: tuple[int, int],
    solver="qics",
    verbose=False,
    real=False,
):
    d, _ = rho.shape
    m, n = dims
    assert d == m * n

    sym_d: int = dim_sym_kd(k, d)
    V = V_builder(k, d)
    a_dag = [alpha_dag_j_builder(k, d, j) for j in range(d)]
    AdA = [[picos.Constant(Ad @ A.T) for A in a_dag] for Ad in a_dag]
    VPi = picos.Constant(V @ isotypic_ot_I(m, n, k, height) @ V.T)
    Wls = [(picos.Constant(W_l_builder(k, d, l)), dim_sym_kd(l, d), dim_sym_kd(k - l, d)) for l in range(1, k // 2 + 1)]

    P = picos.Problem(verbosity=verbose)
    omega_sym = picos.SymmetricVariable("omega_sym", sym_d) if real else picos.HermitianVariable("omega_sym", sym_d)

    # objective:  max tr( (V Pi^lam(x)I V^dag) omega_sym )
    P.set_objective("max", picos.trace(VPi * omega_sym).real)  # type: ignore

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
