from toqito.states import horodecki
import numpy as np


def C3C3_horodecki(a) -> np.ndarray:
    """a in ]0,1["""
    assert a != 0 and a != 1
    return horodecki(a, [3, 3])
