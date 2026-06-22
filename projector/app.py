from pathlib import Path
import json
import math
import subprocess
import sys
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

_DEFAULT_D = 2
_DEFAULT_DEPTH = 5
_MAX_FACTORS = 7  # |λ| above this makes pi_times_ket (O(k·k!) + Sage startup) take > a few seconds

# ── Custom component ────────────────────────────────────────────────────────────

_COMPONENT_DIR = Path(__file__).parent / "young_component"

_young_grid = components.declare_component(
    "young_frame_grid",
    path=str(_COMPONENT_DIR),
)


def young_grid(
    frame: list[int],
    rows: int,
    cols: int,
    key: str | None = None,
    labels: list[str] | None = None,
    color: str | None = None,
) -> tuple[int, int] | None:
    """Renders the interactive Young diagram; returns (row, col) on click."""
    kwargs: dict = dict(frame=frame, rows=rows, cols=cols, default=None)
    if labels is not None:
        kwargs["labels"] = labels
    if color is not None:
        kwargs["color"] = color
    if key is not None:
        kwargs["key"] = key
    result = _young_grid(**kwargs)
    if result is None:
        return None
    row, col, seq = result[0], result[1], result[2]
    seq_key = f"_young_seq_{key}"
    if st.session_state.get(seq_key) == seq:
        return None  # already processed this click
    st.session_state[seq_key] = seq
    return (row, col)


# ── State ───────────────────────────────────────────────────────────────────────


def init_state(d: int, max_depth: int, frame_key: str = "young_frame") -> None:
    frame = list(st.session_state.get(frame_key, [0] * max_depth))
    if len(frame) < max_depth:
        frame += [0] * (max_depth - len(frame))
    else:
        frame = frame[:max_depth]
    frame = [min(v, max_depth) for v in frame]
    st.session_state[frame_key] = frame


# ── Young-frame logic ───────────────────────────────────────────────────────────


def set_frame(i: int, j: int, max_depth: int, frame_key: str = "young_frame") -> None:
    frame: list[int] = st.session_state[frame_key][:]
    j = min(j, max_depth)

    while len(frame) <= i:
        frame.append(0)

    if frame[i] < j:
        for k in range(i + 1):
            frame[k] = max(frame[k], j)
    else:
        for k in range(i, len(frame)):
            frame[k] = min(frame[k], j - 1)

    st.session_state[frame_key] = frame


# ── Vector-frame state ──────────────────────────────────────────────────────────


def init_vector_state(k: int, num_factors: int) -> None:
    if st.session_state.get("vector_k") != k or st.session_state.get("vector_num_factors") != num_factors:
        st.session_state.vector_frame = [0] * k
        st.session_state.vector_k = k
        st.session_state.vector_num_factors = num_factors


def set_vector_frame(i: int, j: int) -> None:
    frame: list[int] = st.session_state.vector_frame[:]
    if frame[i] < j:
        frame[i] = j
    else:
        frame[i] = j - 1
    st.session_state.vector_frame = frame


# ── Hook-length computation ─────────────────────────────────────────────────────


def factorial(n: int) -> int:
    result = 1
    for k in range(2, n + 1):
        result *= k
    return result


def compute_hooks(frame: list[int]) -> list[list[int]]:
    return [[(cols - j - 1) + sum(1 for r in frame[i + 1 :] if r > j) + 1 for j in range(cols)] for i, cols in enumerate(frame)]


def hook_length_formula(frame: list[int]) -> tuple[int, int, int] | None:
    """Returns (total_boxes, product_of_hooks, number_of_SYT) or None if frame is empty."""
    active = [r for r in frame if r > 0]
    if not active:
        return None

    total = sum(active)
    hooks = compute_hooks(active)
    product = 1
    for row in hooks:
        for h in row:
            product *= h

    return total, product, factorial(total) // product


# ── Rendering ───────────────────────────────────────────────────────────────────


def render_grid(d: int, max_depth: int, frame_key: str = "young_frame", grid_key: str = "main_grid") -> None:
    click = young_grid(st.session_state[frame_key], rows=max_depth, cols=max_depth, key=grid_key)
    if click is not None:
        set_frame(*click, max_depth=max_depth, frame_key=frame_key)
        st.rerun()


def render_formula() -> None:
    result = hook_length_formula(st.session_state.young_frame)

    if result is None:
        st.info("Click cells in the grid to draw a Young diagram.")
        return

    total, product, n_syt = result
    st.latex(rf"f^{{\lambda}} = \dfrac{{k!}}{{\prod_{{u \in \lambda}} h(u)}}" rf" = \dfrac{{{total}!}}{{{product}}} = {n_syt}")


# ── Subprocess helpers ──────────────────────────────────────────────────────────

_SCRIPT = Path(__file__).parent / "compute_projector.py"
_GENERIC_SCRIPT = Path(__file__).parent / "compute_generic.py"
_SCHUR_SCRIPT = Path(__file__).parent / "compute_schur_naive.py"


@st.cache_data(show_spinner=False)
def cached_projector_matrix(lam_tuple: tuple[int, ...], k: int):
    result = subprocess.run(
        [sys.executable, str(_SCRIPT), json.dumps(list(lam_tuple)), str(k)],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    return data["labels"], data["matrix"]


@st.cache_data(show_spinner=False)
def cached_norm_sq_projected(lambda1: int, k: int, si_squared_tuple: tuple[float, ...]):
    result = subprocess.run(
        [sys.executable, str(_GENERIC_SCRIPT), str(lambda1), str(k), json.dumps(list(si_squared_tuple))],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


@st.cache_data(show_spinner=False)
def cached_norm_sq_schur_naive(lam_tuple: tuple[int, ...], si_squared_tuple: tuple[float, ...]):
    result = subprocess.run(
        [sys.executable, str(_SCHUR_SCRIPT), json.dumps(list(lam_tuple)), json.dumps(list(si_squared_tuple))],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


@st.cache_data(show_spinner=False)
def cached_vector_check(lam_tuple: tuple[int, ...], k: int, v_tuple: tuple[int, ...]):
    result = subprocess.run(
        [sys.executable, str(_SCRIPT), json.dumps(list(lam_tuple)), str(k), json.dumps(list(v_tuple))],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


# ── Generic vector helpers ──────────────────────────────────────────────────────


def compute_mkh(sis: list[float], degree_k: int, height_h: int, h_lambda: int) -> np.ndarray:
    sisq = [si**2 for si in sis]
    mkh_dp = np.zeros((degree_k + 1, height_h + 1))
    mkh_dp[0][0] = 1
    for siq in sisq:
        for d in range(degree_k, 0, -1):
            for h in range(min(d, height_h), 1, -1):
                mkh_dp[d][h] += sum(mkh_dp[r][h - 1] * siq ** (d - r) for r in range(0, d))
            mkh_dp[d][1] += siq**d
    return mkh_dp[degree_k][h_lambda:]


def norm_hook_generic(sis: list[float], lambda1: int, k: int) -> float:
    """Returns ‖Π^λ ψ_AB^{⊗k}‖² for hook partition λ=(lambda1,1,…,1)."""
    h_lambda = k - lambda1 + 1
    r = len(sis)
    binom = math.comb(k - 1, lambda1 - 1)
    mkh = compute_mkh(sis, k, r, h_lambda)
    return binom * sum(math.comb(h - 1, h_lambda - 1) * v for h, v in zip(range(h_lambda, r + 1), mkh))


# ── Generic vector tab ──────────────────────────────────────────────────────────


def render_generic_vector() -> None:
    st.subheader("Generic Schmidt-rank-r vector")
    st.caption(r"Hook-shaped Young frame: λ = (λ₁, 1, …, 1) with k − λ₁ ones.")

    col1, col2, col3 = st.columns(3)
    with col1:
        r = int(st.number_input("r (Schmidt rank)", min_value=1, max_value=8, value=2, step=1, key="gen_r"))
    with col2:
        k = int(st.number_input("k (cells in Young frame)", min_value=1, max_value=10, value=3, step=1, key="gen_k"))
    with col3:
        lambda1 = int(st.number_input("λ₁ (first row)", min_value=1, max_value=k, value=min(2, k), step=1, key="gen_lambda1"))

    st.markdown("**Schmidt coefficients squared** $s_i^2$ (must sum to 1)")

    si_squared: list[float] = []
    for row_start in range(0, r, 4):
        row_end = min(row_start + 4, r)
        cols = st.columns(row_end - row_start)
        for col_idx, i in enumerate(range(row_start, row_end)):
            with cols[col_idx]:
                val = float(st.number_input(
                    f"s²_{i}",
                    min_value=0.0,
                    max_value=1.0,
                    value=round(1.0 / r, 6),
                    step=0.01,
                    format="%.6f",
                    key=f"gen_si_sq_r{r}_{i}",
                ))
                si_squared.append(val)

    total = sum(si_squared)
    if abs(total - 1.0) > 1e-6:
        st.error(f"Values sum to {total:.6f} — must sum to 1 (off by {abs(total - 1.0):.2e}).")
        return

    st.success(f"Sum = {total:.6f} ✓")
    sis = [math.sqrt(sq) for sq in si_squared]

    norm_sq_formula = norm_hook_generic(sis, lambda1, k)
    st.latex(
        rf"\|\Pi^\lambda \psi_{{AB}}^{{\otimes {k}}}\|^2"
        rf"\;(\text{{formula, hook }}\lambda=({lambda1},{','.join(['1']*(k-lambda1))}))"
        rf"\;=\; {norm_sq_formula:.8f}"
    )

    st.divider()
    st.subheader("Ground truth via Sage isotypic projector")

    dim = r**k
    if dim > 4096:
        st.warning(f"r^k = {r}^{k} = {dim:,}: projector is {dim}×{dim} — computation may be very slow.")

    inputs_key = (lambda1, k, tuple(round(v, 8) for v in si_squared))
    if st.button("Compute ‖Πψ‖² (Sage)", key="gen_compute"):
        with st.spinner("Computing via Sage…"):
            try:
                data = cached_norm_sq_projected(lambda1, k, tuple(round(v, 8) for v in si_squared))
                st.session_state.generic_result = (inputs_key, data)
            except subprocess.CalledProcessError as e:
                st.error(f"Computation failed:\n{e.stderr}")
                return

    stored = st.session_state.get("generic_result")
    if stored is not None and stored[0] == inputs_key:
        norm_sq_gt = stored[1]["norm_sq_projected"]
        c1, c2 = st.columns(2)
        with c1:
            st.metric("‖Πψ‖² (Sage)", f"{norm_sq_gt:.8f}")
        with c2:
            st.metric("‖Πψ‖² (formula)", f"{norm_sq_formula:.8f}")
        diff = abs(norm_sq_formula - norm_sq_gt)
        if diff < 1e-6:
            st.success(f"Match ✓  (|Δ| = {diff:.2e})")
        else:
            st.warning(f"Mismatch  |Δ| = {diff:.2e}")


# ── Projector matrix display ────────────────────────────────────────────────────


def render_projector(k: int) -> None:
    active = [r for r in st.session_state.young_frame if r > 0]
    if not active:
        return

    num_factors = sum(active)
    lam = tuple(active)

    st.divider()
    st.subheader("Isotypic Projector")
    st.caption(rf"$\Pi^{{\lambda}}$ on $(\mathbb{{C}}^{{{k}}})^{{\otimes {num_factors}}}$, " rf"$\lambda = {list(lam)}$")

    dim = k**num_factors
    if num_factors > 5:
        st.warning(f"|λ| = {num_factors}: matrix would be {dim}×{dim} — too large to display.")
        return
    if dim > 256:
        st.warning(f"Matrix too large ({dim}×{dim}) for k = {k}, |λ| = {num_factors}.")
        return
    if num_factors >= 4:
        st.info(f"|λ| = {num_factors}: computing a {dim}×{dim} matrix, this may take a moment.")

    with st.spinner("Computing projector…"):
        labels, mat = cached_projector_matrix(lam, k)

    df = pd.DataFrame(mat, index=labels, columns=labels)
    st.dataframe(df, use_container_width=True)


# ── Vector check ────────────────────────────────────────────────────────────────


def render_vector_check(k: int) -> None:
    active = [r for r in st.session_state.young_frame if r > 0]
    if not active:
        return

    num_factors = sum(active)
    lam = tuple(active)

    st.subheader("v")
    st.caption(rf"Row $i$ = count of value $i$ in $v$. " rf"Total boxes must equal $|\lambda| = {num_factors}$.")

    init_vector_state(k, num_factors)

    click = young_grid(
        st.session_state.vector_frame,
        rows=k,
        cols=num_factors,
        # labels=[str(i) for i in range(k)],
        color="#a8c8f0",
        key="vector_young",
    )
    if click is not None:
        set_vector_frame(*click)
        st.rerun()

    total = sum(st.session_state.vector_frame)

    too_large = num_factors > _MAX_FACTORS
    if too_large:
        st.warning(
            f"|λ| = {num_factors} → {num_factors}! = {__import__('math').factorial(num_factors):,} permutations. "
            f"Computation would take too long (limit: |λ| ≤ {_MAX_FACTORS})."
        )

    btn_col, reset_col, _ = st.columns([1, 1, 4])
    with btn_col:
        calculate = st.button("Calculate", key="calc_vector", disabled=(total != num_factors or too_large))
    with reset_col:
        if st.button("Reset", key="reset_vector"):
            st.session_state.vector_frame = [0] * k
            st.session_state.pop("vector_result", None)
            st.rerun()

    if total != num_factors:
        if total == 0:
            st.info(f"Click cells to build v. Need {num_factors} boxes total.")
        else:
            st.warning(f"Total = {total}, need {num_factors}. Add or remove boxes to match |λ|.")
        return

    v = [i for i, count in enumerate(st.session_state.vector_frame) for _ in range(count)]
    st.caption(f"v = {v}")

    v_key = (lam, k, tuple(v))

    if calculate:
        with st.spinner("Computing…"):
            try:
                data = cached_vector_check(lam, k, tuple(v))
                st.session_state.vector_result = (v_key, data)
            except subprocess.CalledProcessError as e:
                st.error(f"Computation failed:\n{e.stderr}")
                return

    stored = st.session_state.get("vector_result")
    if stored is None or stored[0] != v_key:
        return
    data = stored[1]

    nuv = data["nuv"]
    majorized = data["majorized"]
    norm = data["pi_ket_norm"]
    is_zero = norm < 1e-6

    h_lam = len(lam)
    h_nu = len(nuv)
    height_predicts_zero = h_nu < h_lam

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("ν(v)", str(nuv))
        st.caption(f"h(ν) = {h_nu},  h(λ) = {h_lam}")
    with col2:
        height_label = f"Yes  (h(ν)={h_nu} < h(λ)={h_lam})" if height_predicts_zero else f"No  (h(ν)={h_nu} ≥ h(λ)={h_lam})"
        st.metric("Height: h(ν) < h(λ)?", height_label)
        st.caption("Predicts Π|v⟩ = 0 when Yes")
    with col3:
        maj_label = "Yes  (λ ≤ ν(v))" if majorized else "No  (λ ≰ ν(v))"
        st.metric("Majorization λ ≤ ν(v)?", maj_label)
        st.caption("Predicts Π|v⟩ = 0 when Yes")

    if is_zero:
        st.success(f"Π|v⟩ = **0**   (‖Π|v⟩‖ = {norm:.2e})")
    else:
        st.info(f"Π|v⟩ ≠ 0   (‖Π|v⟩‖ = {norm:.6f})")


# ── Schur polynomial helpers ────────────────────────────────────────────────────


def complete_homogeneous(x: list[float], max_k: int) -> list[float]:
    """[h_0, h_1, ..., h_max_k] via Newton's recurrence h_k = (1/k) Σ p_j h_{k-j}."""
    h = [0.0] * (max_k + 1)
    h[0] = 1.0
    p = [sum(xi**j for xi in x) for j in range(1, max_k + 1)]
    for k in range(1, max_k + 1):
        h[k] = sum(p[j - 1] * h[k - j] for j in range(1, k + 1)) / k
    return h


def schur_polynomial(lam: list[int], x: list[float]) -> float:
    """s_λ(x) via the Jacobi-Trudi identity: det(h_{λ_i - i + j})."""
    lam = sorted(lam, reverse=True)
    n = len(lam)
    if n == 0:
        return 1.0
    if n > len(x):
        return 0.0
    h = complete_homogeneous(x, lam[0] + n - 1)

    def hv(k: int) -> float:
        return 0.0 if k < 0 or k >= len(h) else h[k]

    mat = np.array([[hv(lam[i] - i + j) for j in range(n)] for i in range(n)])
    return float(np.linalg.det(mat))


def norm_schur_formula(lam: list[int], sis: list[float]) -> float:
    """‖Π_λ ψ_AB^{⊗k}‖² = f^λ · s_λ(s₁², …, s_r²)."""
    result = hook_length_formula(lam)
    if result is None:
        return 0.0
    _, _, f_lam = result
    return f_lam * schur_polynomial(lam, [si**2 for si in sis])


# ── Schur polynomial tab ────────────────────────────────────────────────────────


def render_schur_polynomial() -> None:
    st.subheader("Schur polynomial norm")
    st.caption(r"For any Young frame λ: $\|\Pi^\lambda \psi_{AB}^{\otimes k}\|^2 = f^\lambda \cdot s_\lambda(s_1^2,\ldots,s_r^2)$")

    col1, col2 = st.columns(2)
    with col1:
        r = int(st.number_input("r (Schmidt rank)", min_value=1, max_value=8, value=2, step=1, key="schur_r"))
    with col2:
        max_depth = st.slider("max rows / cols", min_value=1, max_value=10, value=_DEFAULT_DEPTH, key="schur_depth")

    init_state(0, max_depth, frame_key="schur_frame")

    st.subheader("λ")
    st.caption("Click to draw the Young frame.")
    render_grid(0, max_depth, frame_key="schur_frame", grid_key="schur_grid")

    active = [row for row in st.session_state.schur_frame if row > 0]
    if not active:
        st.info("Click cells in the grid to draw a Young diagram.")
        return

    k = sum(active)
    lam = tuple(sorted(active, reverse=True))
    st.caption(rf"λ = {list(lam)},  k = |λ| = {k}")

    result = hook_length_formula(list(lam))
    if result is not None:
        total, product, f_lam = result
        st.latex(
            rf"f^\lambda = \dfrac{{{total}!}}{{{product}}} = {f_lam}"
        )

    st.divider()
    st.markdown("**Schmidt coefficients squared** $s_i^2$ (must sum to 1)")

    si_squared: list[float] = []
    for row_start in range(0, r, 4):
        row_end = min(row_start + 4, r)
        cols = st.columns(row_end - row_start)
        for col_idx, i in enumerate(range(row_start, row_end)):
            with cols[col_idx]:
                val = float(st.number_input(
                    f"s²_{i}",
                    min_value=0.0,
                    max_value=1.0,
                    value=round(1.0 / r, 6),
                    step=0.01,
                    format="%.6f",
                    key=f"schur_si_sq_r{r}_{i}",
                ))
                si_squared.append(val)

    total_sq = sum(si_squared)
    if abs(total_sq - 1.0) > 1e-6:
        st.error(f"Values sum to {total_sq:.6f} — must sum to 1 (off by {abs(total_sq - 1.0):.2e}).")
        return

    st.success(f"Sum = {total_sq:.6f} ✓")
    sis = [math.sqrt(sq) for sq in si_squared]

    norm_sq_formula = norm_schur_formula(list(lam), sis)
    st.latex(
        rf"\|\Pi^\lambda \psi_{{AB}}^{{\otimes {k}}}\|^2"
        rf"\;(\lambda={list(lam)})"
        rf"\;=\; {norm_sq_formula:.8f}"
    )

    st.divider()
    st.subheader("Ground truth via Sage isotypic projector")

    dim = r**k
    if dim > 4096:
        st.warning(f"r^k = {r}^{k} = {dim:,}: projector is {dim}×{dim} — computation may be very slow.")

    inputs_key = (lam, k, tuple(round(v, 8) for v in si_squared))
    if st.button("Compute ‖Πψ‖² (Sage)", key="schur_compute"):
        with st.spinner("Computing via Sage…"):
            try:
                data = cached_norm_sq_schur_naive(lam, tuple(round(v, 8) for v in si_squared))
                st.session_state.schur_result = (inputs_key, data)
            except subprocess.CalledProcessError as e:
                st.error(f"Computation failed:\n{e.stderr}")
                return

    stored = st.session_state.get("schur_result")
    if stored is not None and stored[0] == inputs_key:
        norm_sq_gt = stored[1]["norm_sq_projected"]
        c1, c2 = st.columns(2)
        with c1:
            st.metric("‖Πψ‖² (Sage)", f"{norm_sq_gt:.8f}")
        with c2:
            st.metric("‖Πψ‖² (formula)", f"{norm_sq_formula:.8f}")
        diff = abs(norm_sq_formula - norm_sq_gt)
        if diff < 1e-6:
            st.success(f"Match ✓  (|Δ| = {diff:.2e})")
        else:
            st.warning(f"Mismatch  |Δ| = {diff:.2e}")


# ── Main ────────────────────────────────────────────────────────────────────────


def main() -> None:
    st.set_page_config(
        page_title="Young Diagram & Hook Length Formula",
        layout="centered",
    )
    st.title("Young Diagram")

    tab_basis, tab_generic, tab_schur = st.tabs(["basis vector", "generic vector", "Schur polynomial"])

    with tab_basis:
        col1, col2 = st.columns(2)
        with col1:
            d = st.slider("d — local dimension", min_value=2, max_value=10, value=_DEFAULT_D)
        with col2:
            max_depth = st.slider("max_depth — max rows", min_value=1, max_value=10, value=_DEFAULT_DEPTH)

        init_state(d, max_depth)

        st.subheader("λ")
        st.caption("Click to draw the partition.")
        render_grid(d, max_depth)
        render_vector_check(d)

    with tab_generic:
        render_generic_vector()

    with tab_schur:
        render_schur_polynomial()


if __name__ == "__main__":
    main()
