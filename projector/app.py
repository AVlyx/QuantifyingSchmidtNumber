from pathlib import Path
import json
import subprocess
import sys
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


def init_state(d: int, max_depth: int) -> None:
    frame = list(st.session_state.get("young_frame", [0] * max_depth))
    # resize rows
    if len(frame) < max_depth:
        frame += [0] * (max_depth - len(frame))
    else:
        frame = frame[:max_depth]
    # clip column values to max_depth
    frame = [min(v, max_depth) for v in frame]
    st.session_state.young_frame = frame


# ── Young-frame logic ───────────────────────────────────────────────────────────


def set_frame(i: int, j: int, max_depth: int) -> None:
    frame: list[int] = st.session_state.young_frame[:]
    j = min(j, max_depth)

    while len(frame) <= i:
        frame.append(0)

    if frame[i] < j:
        for k in range(i + 1):
            frame[k] = max(frame[k], j)
    else:
        for k in range(i, len(frame)):
            frame[k] = min(frame[k], j - 1)

    st.session_state.young_frame = frame


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


def render_grid(d: int, max_depth: int) -> None:
    click = young_grid(st.session_state.young_frame, rows=max_depth, cols=max_depth)
    if click is not None:
        set_frame(*click, max_depth=max_depth)
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
def cached_vector_check(lam_tuple: tuple[int, ...], k: int, v_tuple: tuple[int, ...]):
    result = subprocess.run(
        [sys.executable, str(_SCRIPT), json.dumps(list(lam_tuple)), str(k), json.dumps(list(v_tuple))],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


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


# ── Main ────────────────────────────────────────────────────────────────────────


def main() -> None:
    st.set_page_config(
        page_title="Young Diagram & Hook Length Formula",
        layout="centered",
    )
    st.title("Young Diagram")

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

    # st.divider()
    # st.subheader("Hook-Length Formula")
    # st.caption("Number of standard Young tableaux of shape λ")
    # render_formula()

    # render_projector(d)


if __name__ == "__main__":
    main()
