import math


def E_t_lowerk2(r: int, t: int, P_lambda: float):
    etn = t + math.sqrt(t * (r - t) * (r - 2 * r * P_lambda - 1))
    return 1 - etn / r


def E_t_upperk2r2(P_lambda: float):
    if P_lambda > 0.25:
        return 1
    return (1 - math.sqrt(1 - 4 * P_lambda)) / 2


##########################################
from math import factorial


def f_lambda(lambda_: list[int]) -> int:
    """Number of standard Young tableaux of shape lambda_, via the hook length formula."""
    lam = [p for p in lambda_ if p != 0]
    n = sum(lam)
    if n == 0:
        return 1

    rows = len(lam)
    # conjugate partition, to get column lengths
    cols = [sum(1 for r in lam if r > j) for j in range(lam[0])]

    hook_product = 1
    for i in range(rows):
        for j in range(lam[i]):
            arm = lam[i] - j - 1  # cells to the right in same row
            leg = cols[j] - i - 1  # cells below in same column
            hook_product *= arm + leg + 1

    return factorial(n) // hook_product


from itertools import permutations


def kostka_lambda_nu(lam: list[int], nu: list[int]) -> int:
    n = sum(lam)
    if sum(nu) != n:
        return 0

    # cell positions of the Young diagram, row by row
    cells = []
    for i, row_len in enumerate(lam):
        for j in range(row_len):
            cells.append((i, j))

    # multiset of entries: value v (1-indexed) appears nu[v-1] times
    values = []
    for v, cnt in enumerate(nu, start=1):
        values.extend([v] * cnt)

    count = 0
    for perm in set(permutations(values)):  # dedupe identical-value swaps
        grid = dict(zip(cells, perm))

        # rows weakly increasing
        valid = True
        for i, row_len in enumerate(lam):
            for j in range(row_len - 1):
                if grid[(i, j)] > grid[(i, j + 1)]:
                    valid = False
                    break
            if not valid:
                break

        # columns strictly increasing
        if valid:
            num_cols = lam[0] if lam else 0
            for j in range(num_cols):
                col_vals = [grid[(i, j)] for i in range(len(lam)) if j < lam[i]]
                for k in range(len(col_vals) - 1):
                    if col_vals[k] >= col_vals[k + 1]:
                        valid = False
                        break
                if not valid:
                    break

        if valid:
            count += 1

    return count


from itertools import permutations


def m_nu(nu: list[int], a_i: list[float]) -> float:
    n_vars = len(a_i)

    # drop zero parts (they don't affect the partition) and check it fits
    parts = [p for p in nu if p != 0]
    if len(parts) > n_vars:
        return 0.0  # not enough variables to support this many nonzero parts

    # pad with zeros to match number of variables
    exponents = parts + [0] * (n_vars - len(parts))

    total = 0.0
    for exp_perm in set(permutations(exponents)):  # dedupe identical arrangements
        term = 1.0
        for a, e in zip(a_i, exp_perm):
            term *= a**e
        total += term

    return total


def integer_partitions(k: int):
    """Yield all partitions of k as lists in weakly decreasing order."""
    if k == 0:
        yield []
        return

    def helper(remaining, max_part):
        if remaining == 0:
            yield []
            return
        for part in range(min(remaining, max_part), 0, -1):
            for rest in helper(remaining - part, part):
                yield [part] + rest

    yield from helper(k, k)


def expected_norm(lam: list[int], a_is: list[float]) -> float:
    lam = [p for p in lam if p != 0]
    k = sum(lam)

    total = 0.0
    for nu in integer_partitions(k):
        K = kostka_lambda_nu(lam, nu)
        if K == 0:
            continue
        total += K * m_nu(nu, a_is)

    return f_lambda(lam) * total


import numpy as np
from scipy.optimize import brentq


def roots_r_2(lam: list[int], P_lam: float, num_samples: int = 500, tol: float = 1e-12):
    """Find all x in [0.5, 1] such that expected_norm(lam, [x, 1-x]) - P_lam == 0."""

    def g(x):
        return expected_norm(lam, [x, 1 - x]) - P_lam

    xs = np.linspace(0.5, 1.0, num_samples + 1)
    gs = [g(x) for x in xs]

    roots = []

    for i, gv in enumerate(gs):
        if gv == 0.0:
            roots.append(1 - xs[i])

    for i in range(len(xs) - 1):
        x0, x1 = xs[i], xs[i + 1]
        g0, g1 = gs[i], gs[i + 1]

        if g0 == 0.0 or g1 == 0.0:
            continue  # already captured above

        if (g0 < 0) != (g1 < 0):  # sign change -> refine with brentq
            root = brentq(g, x0, x1, xtol=tol)
            roots.append(1 - root)  # type: ignore

    return sorted(roots)


def E_t_lower_lambda_r2(lam: list[int], P_lam: float) -> float:
    return roots_r_2(lam, P_lam)[0]
