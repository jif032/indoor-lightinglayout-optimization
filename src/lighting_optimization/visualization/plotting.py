"""Plots for illuminance maps and annealing convergence."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import matplotlib.pyplot as plt


def plot_illuminance(points: Sequence[Sequence[float]], values: Sequence[float], lights: list[dict[str, Any]],
                     output: Path, lower_lux: float = 90.0, upper_lux: float = 200.0) -> None:
    """Draw sampled lux values and mark all luminaires."""
    x = [point[0] for point in points]
    y = [point[1] for point in points]
    fig, axis = plt.subplots(figsize=(8, 6))
    scatter = axis.scatter(x, y, c=values, s=28, cmap="viridis")
    fig.colorbar(scatter, ax=axis, label="Illuminance (lux)")
    for index, light in enumerate(lights):
        axis.scatter(light["position"][0], light["position"][1], marker="s", s=52,
                     c="black", label="Luminaire" if index == 0 else None, zorder=3)
    axis.set(title="Task-plane illuminance", xlabel="X (m)", ylabel="Y (m)", aspect="equal")
    axis.legend(loc="upper right")
    axis.text(0.01, 0.01, f"Compliance band: {lower_lux:g}-{upper_lux:g} lux", transform=axis.transAxes)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160)
    plt.close(fig)


def plot_history(histories: Sequence[Sequence[float]], output: Path) -> None:
    """Plot the best-so-far compliance fraction over temperature stages."""
    fig, axis = plt.subplots(figsize=(8, 4.5))
    for index, history in enumerate(histories, 1):
        axis.plot(range(len(history)), history, marker="o", markersize=3, label=f"Run {index}")
    axis.set(title="Best compliance fraction by temperature stage", xlabel="Temperature stage", ylabel="Compliance fraction")
    axis.set_ylim(0, 1.02)
    axis.grid(True, alpha=0.3)
    axis.legend()
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160)
    plt.close(fig)
