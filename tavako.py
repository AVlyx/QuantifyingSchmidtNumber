from toqito.states import max_entangled, basis
from bound_entangled.utils import ketbra


def tavakoli_morelli_state(q):
    zero_one = basis(3 * 3, 0 * 3 + 1)
    kb_01 = ketbra(zero_one)
    phi_plus = ketbra(max_entangled(3))  # type: ignore
    return q * phi_plus + (1 - q) * kb_01
