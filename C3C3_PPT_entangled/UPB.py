import numpy as np
from toqito.states import tile


def C3C3_upb():

    # The 5 tile vectors that form the UPB in C^3 ⊗ C^3
    upb = [tile(i) for i in range(5)]

    # The bound entangled state is the projector onto the orthogonal complement
    # of the UPB, normalized
    d = 9  # dimension of C^3 ⊗ C^3

    # Sum of projectors onto the UPB
    P_upb = sum(v @ v.conj().T for v in upb)

    # Complement projector (projects onto the 4-dimensional orthogonal complement)
    P_complement = np.eye(d) - P_upb

    # Normalized bound entangled state
    return P_complement / np.trace(P_complement)
