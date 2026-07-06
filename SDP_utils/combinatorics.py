from math import comb, factorial, prod
from typing import Generator


def multinomial(k, nu) -> int:
    return factorial(k) // prod(factorial(n) for n in nu)


def dim_sym_kd(k: int, d: int) -> int:
    return comb(k + d - 1, d - 1)


def unrank(index: int, items: int, choose: int) -> list[int]:
    """Unrank index in combinatorial number system: choose items from range [0, items-1]."""
    result = []
    for i in range(choose, 0, -1):
        x = items - 1
        while comb(x, i) > index:
            x -= 1
        result.append(x)
        index -= comb(x, i)
    return result


def occupation_nu(index: int, k: int, d: int) -> list[int]:
    "Give the nu vector corresponding to that index"
    n_stars = k
    bars = d - 1
    total = n_stars + bars
    bar_positions = unrank(index, total, bars)
    bars_index = [total] + bar_positions + [-1]
    stars = [bars_index[i] - 1 - bars_index[i + 1] for i in range(bars + 1)]
    return stars


def rank(bar_positions, items):
    """Rank a descending list of bar positions in combinatorial number system."""
    index = 0
    for i, x in enumerate(bar_positions):
        choose = len(bar_positions) - i  # counts down from bars to 1
        index += comb(x, choose)
    return index


def occupation_index(stars, k, d):
    "Give the index corresponding to the nu vector"
    total = k + d - 1  # = n_stars + bars

    bars_index = [total]
    for s in stars[:-1]:
        bars_index.append(bars_index[-1] - 1 - s)

    bar_positions = bars_index[1:]
    return rank(bar_positions, total)


# assert tuple([occupation_index(occupation_nu(i, 6, 3), 6, 3) for i in range(dim_sym_kd(6, 3))]) == tuple(range(dim_sym_kd(6, 3)))


def nu_iterator(k: int, d: int) -> Generator[list[int]]:
    "iterate over all vector nu in C^d^k"
    ret = [0] * d

    def rec(bars_added, stars_remaining):
        if stars_remaining == 0:
            yield ret[:]
            return
        if bars_added >= d:
            return
        # place a star in current bin and recurse
        ret[bars_added] += 1
        yield from rec(bars_added, stars_remaining - 1)
        ret[bars_added] -= 1

        # move to next bin
        yield from rec(bars_added + 1, stars_remaining)

    yield from rec(0, k)


# k, d = 3,4
# for v in nu_iterator(k, d):
#     print(v, end=", ")
# print()


def nu_set_iterator(nu: list[int]) -> Generator[int]:
    "iterate over all the basis vector corresponding to nu"
    d = len(nu)
    k = sum(nu)

    def rec(j: int, ret: int) -> Generator[int]:
        if sum(nu) == 0:
            yield ret
        for i in range(len(nu)):
            if nu[i] == 0:
                continue
            ret_i = ret + d ** (k - j - 1) * i
            nu[i] -= 1
            yield from rec(j + 1, ret_i)
            nu[i] += 1

    yield from rec(0, 0)

    # # k, d = 3,4
    # # for v in nu_set_iterator([1,1,1]):
    # #     print(v, end=", ")
    # # print()
    # def schur_polynomial(lam: list[int], x: list[float]) -> float:
    #     lam = sorted(lam, reverse=True)
    #     r = len(x)
    #     poly = _s[lam].expand(r).change_ring(sage.RDF)
    #     return float(poly(*[sage.RDF(xi) for xi in x]))


def isotopyc_I_perm(m: int, n: int, k: int) -> list[int]:
    ret: list[int] = []

    def recA(new_index: int, dim_num: int):
        if dim_num >= k + 1:
            recB(new_index, 1)
            return
        stride = (n * m) ** (k - dim_num) * n
        for i in range(new_index, new_index + m * stride, stride):
            recA(i, dim_num + 1)

    def recB(new_index: int, dim_num: int):
        if dim_num >= k + 1:
            ret.append(new_index)
            return

        stride = (n * m) ** (k - dim_num)
        for i in range(new_index, new_index + n * stride, stride):
            recB(i, dim_num + 1)

    recA(0, 1)
    return ret
