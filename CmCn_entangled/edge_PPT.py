from bound_entangled.cm_otimes_cn import random_PPT_close_to_the_PPT_edge


def random_edge_PPT_gen(m: int, n: int, precision: int):
    def gen(p):
        return random_PPT_close_to_the_PPT_edge((m, n), precision)

    return gen
