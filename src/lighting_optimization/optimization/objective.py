"""Lighting-quality objective used in the published case study."""

from __future__ import annotations

from collections.abc import Sequence


def compliance_rate(illuminance_lux: Sequence[float], lower_lux: float = 90.0, upper_lux: float = 200.0) -> float:
    """Fraction of sampled task-plane points within the inclusive lux range.

    The manuscript defines F = A_qualified / A_total. Since the source code
    samples a uniform grid, this implementation evaluates the corresponding
    fraction of points. Thresholds are in lux, after the Radiance RGB-to-lux
    conversion.
    """
    if not illuminance_lux:
        raise ValueError("At least one illuminance sample is required")
    if lower_lux < 0 or upper_lux < lower_lux:
        raise ValueError("Illuminance bounds must satisfy 0 <= lower_lux <= upper_lux")
    qualified = sum(lower_lux <= value <= upper_lux for value in illuminance_lux)
    return qualified / len(illuminance_lux)
