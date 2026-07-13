import numpy as np
from toqito.states import tile


def UPB():
    rho = np.identity(9)
    for i in range(5):
        rho -= np.outer(tile(i), tile(i))
    return rho / 4


if __name__ == "__main__":
    print(np.trace(UPB()))
