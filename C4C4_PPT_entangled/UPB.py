import numpy as np
from toqito.state_props import is_unextendible_product_basis, is_ppt, is_separable


def kron_cols(A, B):
    # A, B are 4xk arrays of local factors (columns) -> list of 16-dim product vecs
    return [np.kron(A[:, j], B[:, j]).reshape(-1, 1) for j in range(A.shape[1])]


# ---- Min4x4: minimal 8-state UPB in C^4 x C^4 (DiVincenzo et al.; QETLAB 'Min4x4') ----
s2 = np.sqrt(2)
A = np.zeros((4, 8))
B = np.zeros((4, 8))
A[:, 0] = [1, -3, 1, 1]
A[:, 0] /= np.sqrt(12)
B[:, 0] = np.array([0, 1, -3 - s2, -1 - s2]) / np.sqrt(15 + 8 * s2)
A[:, 1] = [1, 0, 0, 0]
B[:, 1] = [1, 0, 0, 0]
A[:, 2] = np.array([0, 1, 2, 1]) / np.sqrt(6)
B[:, 2] = np.array([1, 0, s2 - 1, 1]) / np.sqrt(5 - 2 * s2)
A[:, 3] = np.array([1, 0, 0, -1]) / s2
B[:, 3] = [0, 1, 0, 0]
A[:, 4] = [0, 1, 0, 0]
B[:, 4] = np.array([-1, 1 + s2, 0, 1]) / np.sqrt(5 + 2 * s2)
A[:, 5] = np.array([3, 1, -1, 1]) / np.sqrt(12)
B[:, 5] = [0, 0, 1, 0]
A[:, 6] = np.array([0, 1, 1, 0]) / s2
B[:, 6] = np.array([1, 1, 1, -s2]) / np.sqrt(5)
A[:, 7] = [0, 0, 1, 0]
B[:, 7] = np.array([-1, 1 + s2, 0, 1]) / np.sqrt(5 + 2 * s2)
min4x4 = kron_cols(A, B)


# ---- GenTiles1(n): non-minimal (n^2-2n+1)-state UPB in C^n x C^n, n even ----
def gen_tiles1(n):
    I = np.eye(n)
    w = np.exp(4j * np.pi / n)
    size = n * n - 2 * n + 1
    U1 = np.zeros((n, size), dtype=complex)
    U2 = np.zeros((n, size), dtype=complex)
    U1[:, -1] = U2[:, -1] = np.ones(n) / np.sqrt(n)  # the "stopper" state
    ct = 0
    for m in range(1, n // 2):
        wMat = np.zeros((n, n), dtype=complex)
        for k in range(n):
            for j in range(n // 2):
                wMat[(j + k) % n, k] += w ** (j * m)
        for k in range(n):
            U1[:, ct] = I[:, k]
            U2[:, ct] = wMat[:, (k + 1) % n] / np.sqrt(n / 2)
            U1[:, ct + 1] = wMat[:, k] / np.sqrt(n / 2)
            U2[:, ct + 1] = I[:, k]
            ct += 2
    return kron_cols(U1, U2)


gentiles1_4 = gen_tiles1(4)


# ---- verify + build the bound entangled states ----
def bound_entangled_state(upb, d=16):
    P = sum((v / np.linalg.norm(v)) @ (v / np.linalg.norm(v)).conj().T for v in upb)
    return (np.eye(d) - P) / (d - len(upb))  # rho as a 16x16 np.ndarray


if __name__ == "__main__":
    for name, upb in [("Min4x4", min4x4), ("GenTiles1(4)", gentiles1_4)]:
        is_upb, _ = is_unextendible_product_basis(np.array(upb), np.array([4, 4]))
        rho = bound_entangled_state(upb)
        print(
            name,
            "| #states:",
            len(upb),
            "| is_UPB:",
            is_upb,
            "| PPT:",
            is_ppt(rho, sys=2, dim=[4, 4]),
            "| separable:",
            is_separable(rho, dim=[4, 4])[0],
        )
