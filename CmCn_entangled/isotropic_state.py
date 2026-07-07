from toqito.states import isotropic as isotr
import numpy as np


def isotropic(m: int, alpha: float) -> np.ndarray:
    # assert alpha > 1 / (m + 1)
    return isotr(m, alpha)


if __name__ == "__main__":
    print(isotropic(2, 0.5))
