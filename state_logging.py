import json
import numpy as np


def complex_matrix_to_json(mat):
    """Serialize a complex numpy matrix as nested [real, imag] lists."""
    mat = np.asarray(mat)
    return {
        "real": mat.real.tolist(),
        "imag": mat.imag.tolist(),
    }


def complex_vector_to_json(vec):
    """Serialize a complex numpy vector as [real, imag] lists."""
    vec = np.asarray(vec)
    return {
        "real": vec.real.tolist(),
        "imag": vec.imag.tolist(),
    }


def log_failed_state(filepath, state):
    """
    Append a JSON Lines record for a state that the SDP failed to identify.

    Stores: the density matrix, its eigenvalues, its eigenvectors, and its
    purity Tr(rho^2).
    """
    state = np.asarray(state)

    eigvals, eigvecs = np.linalg.eigh(state)  # state is Hermitian
    purity = float(np.real(np.trace(state @ state)))

    record = {
        "state": complex_matrix_to_json(state),
        "eigenvalues": eigvals.tolist(),  # eigh returns real eigenvalues already
        "eigenvectors": complex_matrix_to_json(eigvecs),  # columns are eigenvectors
        "purity": purity,
    }

    with open(filepath, "a") as f:
        f.write(json.dumps(record) + "\n")


def load_failed_states(filepath):
    """Load all logged records back into a list of dicts."""
    records = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def record_to_complex_matrix(entry):
    """Reconstruct a complex numpy matrix from a serialized {real, imag} entry."""
    return np.array(entry["real"]) + 1j * np.array(entry["imag"])
