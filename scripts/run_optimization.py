#!/usr/bin/env python3
"""Run the paper's seven-luminaire case study."""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lighting_optimization.lighting.illuminance import RadianceCalculator  # noqa: E402
from lighting_optimization.lighting.model import build_scene  # noqa: E402
from lighting_optimization.optimization.objective import compliance_rate  # noqa: E402
from lighting_optimization.optimization.simulated_annealing import (  # noqa: E402
    AnnealingConfig,
    simulated_annealing,
)

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "default.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "run")
    parser.add_argument("--runs", type=int, help="Override the configured number of independent SA cycles")
    args = parser.parse_args()

    config_data = json.loads(args.config.read_text(encoding="utf-8"))
    room, objective_config, annealing_data = (config_data[key] for key in ("room", "objective", "annealing"))
    run_count = args.runs if args.runs is not None else annealing_data["independent_runs"]
    if run_count < 1:
        parser.error("--runs must be positive")

    from lighting_optimization.visualization.plotting import plot_history, plot_illuminance

    lights, walls, materials = build_scene(
        room["length_m"], room["width_m"], room["height_m"],
        tuple(config_data["initial_coordinates"]),
    )
    def score(layout):
        _, illuminance = RadianceCalculator(layout, walls, materials).calculate_illuminance(
            room["task_plane_height_m"], room["grid_step_m"],
            room["x_min_m"], room["x_max_m"], room["y_min_m"], room["y_max_m"],
        )
        return compliance_rate(illuminance, objective_config["lower_illuminance_lux"], objective_config["upper_illuminance_lux"])

    annealing_config = AnnealingConfig(
        initial_temperature=annealing_data["initial_temperature"],
        final_temperature=annealing_data["final_temperature"],
        cooling_rate=annealing_data["cooling_rate"],
        iterations_per_temperature=annealing_data["iterations_per_temperature"],
        max_shift_m=annealing_data["max_shift_m"],
    )
    seed = config_data["random_seed"]
    histories, results = [], []
    for run_index in range(run_count):
        result = simulated_annealing(lights, score, room["length_m"], room["width_m"], annealing_config,
                                     random.Random(seed + run_index))
        histories.append(result.history)
        results.append(result)
        print(f"Run {run_index + 1}/{run_count}: best compliance = {result.best_score:.4f}; "
              f"accepted {result.accepted_moves}/{result.evaluated_moves} moves")

    best = max(results, key=lambda result: result.best_score)
    points, illuminance = RadianceCalculator(best.best_lights, walls, materials).calculate_illuminance(
        room["task_plane_height_m"], room["grid_step_m"], room["x_min_m"], room["x_max_m"], room["y_min_m"], room["y_max_m"]
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    plot_history(histories, args.output_dir / "convergence.png")
    plot_illuminance(points, illuminance, best.best_lights, args.output_dir / "best_illuminance.png",
                     objective_config["lower_illuminance_lux"], objective_config["upper_illuminance_lux"])
    report = {
        "best_compliance_fraction": best.best_score,
        "best_luminaires": best.best_lights,
        "illuminance_summary_lux": RadianceCalculator.analyze_results(illuminance),
        "run_best_scores": [result.best_score for result in results],
        "random_seed": seed,
        "config": config_data,
    }
    (args.output_dir / "summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Saved results to {args.output_dir}")


if __name__ == "__main__":
    main()
