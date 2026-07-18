from bound_entangled.cm_otimes_cn import random_NPT, random_PPT


def CmCn_random_not_PPT(m, n):
    return random_NPT((m, n))


def CmCn_random_PPT(m, n):
    return random_PPT((m, n))


def random_not_PPT_gen(m: int, n: int):
    def gen(p):
        return CmCn_random_not_PPT(m, n)

    return gen


def random_PPT_gen(m: int, n: int):
    def gen(p):
        return CmCn_random_PPT(m, n)

    return gen
