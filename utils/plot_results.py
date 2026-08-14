from matplotlib import pyplot as plt
import numpy as np

from utils.load_store_results import load_results_in_range, Separability


def plot_robustness(
    filename: str,
    title: str,
    range_: tuple[float, float, float],
    xlabel: str,
    plot_upper: bool = False,
    zero_at=1e-8,  # log scale does not have a real 0
):
    results = load_results_in_range(filename, range_)
    x_axis = np.asarray([r.p for r in results], dtype=np.float64)
    Et_lower_axis = np.asarray([r.Et_lower if r.Et_lower else 0.0 for r in results], dtype=np.float64)
    Et_lower_axis = np.where(Et_lower_axis <= 0, zero_at, Et_lower_axis)
    Et_upper_axis = np.asarray([r.Et_upper if r.Et_upper else 1.0 for r in results], dtype=np.float64)
    separability_ax = np.asarray([r.separability.value for r in results], dtype=np.int32)

    plt.figure(figsize=(7, 5))
    plt.plot(x_axis, Et_lower_axis, color="gray", linestyle="-", alpha=0.6, zorder=1, label="$E_t^{lower}$")
    mask = separability_ax == Separability.entangled.value
    plt.scatter(x_axis[mask], Et_lower_axis[mask], color="crimson", marker="o", s=50, label="entangled", zorder=2)
    mask = separability_ax == Separability.inconclusive.value
    plt.scatter(x_axis[mask], Et_lower_axis[mask], color="orange", marker="h", s=60, label="inconclusive", zorder=2)
    mask = separability_ax == Separability.separable.value
    plt.scatter(x_axis[mask], Et_lower_axis[mask], color="royalblue", marker="x", s=60, label="separable", zorder=2)

    if plot_upper:
        plt.plot(x_axis, Et_upper_axis, color="yellow", linestyle="-", alpha=0.6, zorder=1, label="$E_t^{lower}$")

    plt.yscale("log")
    plt.xlabel(xlabel)
    plt.ylabel("$E_{t}$ bound (log scale)")
    plt.title(title)
    plt.grid(True, which="both", ls="--", alpha=0.5)
    plt.legend(fontsize=8)
    plt.show()
