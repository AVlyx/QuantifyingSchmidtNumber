import math
import numpy as np
from SDP_utils.combinatorics import occupation_index, nu_set_iterator, multinomial, nu_iterator, dim_sym_kd, isotopyc_I_perm
from SDP_utils.isotopic_proj import isotypic_projector
from scipy import sparse


def V_builder(k: int, d: int):
    V = np.zeros((math.comb(k + d - 1, k), d**k))
    for nu in nu_iterator(k, d):
        fact = 1.0 / math.sqrt(multinomial(k, nu))
        nu_index = occupation_index(nu, k, d)
        V[nu_index, list(nu_set_iterator(nu))] = fact
    return V


def V_l_V_kl_builder(k: int, d: int, l: int):
    Vl = V_builder(l, d)
    Vkl = V_builder(k - l, d)
    return sparse.csr_matrix(np.kron(Vl, Vkl))


def W_l_builder(k: int, d: int, l: int):
    dl, dkl = dim_sym_kd(l, d), dim_sym_kd(k - l, d)
    rows, cols, vals = [], [], []
    for mu in nu_iterator(l, d):
        i_mu = occupation_index(mu, l, d)
        m_mu = multinomial(l, mu)
        for nu in nu_iterator(k - l, d):
            tau = [a + b for a, b in zip(mu, nu)]
            rows.append(i_mu * dkl + occupation_index(nu, k - l, d))
            cols.append(occupation_index(tau, k, d))
            vals.append(math.sqrt(m_mu * multinomial(k - l, nu) / multinomial(k, tau)))
    return sparse.csr_matrix((vals, (rows, cols)), shape=(dl * dkl, dim_sym_kd(k, d)))


def isotypic_ot_I(m, n, k, lam):

    Pi_lambda = isotypic_projector(lam, m, k)
    I = np.identity(n**k)
    M = np.kron(Pi_lambda, I)  # ordered A_1..A_k B_1..B_k

    perm = np.asarray(isotopyc_I_perm(m, n, k))
    inv = np.argsort(perm)
    return M[np.ix_(inv, inv)]  # now ordered A_1 B_1 ... A_k B_k


def alpha_dag_j_builder(k: int, d: int, j: int):
    alpha_dag_j = np.zeros((dim_sym_kd(k, d), dim_sym_kd(k - 1, d)))
    for nu_darrow in nu_iterator(k - 1, d):
        index_V_darrow = occupation_index(nu_darrow, k - 1, d)
        nu_darrow[j] += 1
        index_V_darrow_e_j = occupation_index(nu_darrow, k, d)
        alpha_dag_j[index_V_darrow_e_j, index_V_darrow] = math.sqrt(nu_darrow[j])
    return alpha_dag_j
