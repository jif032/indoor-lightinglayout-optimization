"""Simulated annealing for maximizing the task-plane compliance fraction."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Callable

from lighting_optimization.lighting.model import clone_lights

ScoreFunction = Callable[[list[dict[str, Any]]], float]


@dataclass(frozen=True)
class AnnealingConfig:
    initial_temperature: float = 100.0
    final_temperature: float = 1.0
    cooling_rate: float = 0.6
    iterations_per_temperature: int = 20
    max_shift_m: float = 0.4

    def __post_init__(self) -> None:
        if self.initial_temperature <= 0 or self.final_temperature <= 0:
            raise ValueError("Temperatures must be positive")
        if self.initial_temperature < self.final_temperature:
            raise ValueError("initial_temperature must be >= final_temperature")
        if not 0 < self.cooling_rate < 1:
            raise ValueError("cooling_rate must be between 0 and 1")
        if self.iterations_per_temperature < 1 or self.max_shift_m < 0:
            raise ValueError("iterations_per_temperature must be positive and max_shift_m non-negative")


@dataclass
class AnnealingResult:
    best_lights: list[dict[str, Any]]
    best_score: float
    history: list[float]
    accepted_moves: int
    evaluated_moves: int


def perturb_lights(lights: list[dict[str, Any]], length: float, width: float,
                   max_shift: float = 0.4, rng: random.Random | Any = random) -> list[dict[str, Any]]:
    """Move one mirrored pair or the unpaired center luminaire.

    This keeps the original +/-0.4 m uniform coordinate perturbation and room
    clipping. The standalone lamp was present in the scene but omitted from
    the old neighbor selector; it is included here as a valid move.
    """
    if len(lights) != 7:
        raise ValueError("The study's neighborhood model expects seven luminaires")
    candidate = clone_lights(lights)
    group = rng.choice(("pair_1", "center", "pair_3", "pair_4"))
    dx, dy = rng.uniform(-max_shift, max_shift), rng.uniform(-max_shift, max_shift)
    if group == "center":
        index = 2
        x = max(0.0, min(width, candidate[index]["position"][0] + dx))
        y = max(0.0, min(length, candidate[index]["position"][1] + dy))
        candidate[index]["position"][0:2] = [x, y]
        return candidate

    indices = {"pair_1": (0, 1), "pair_3": (3, 4), "pair_4": (5, 6)}[group]
    x = max(0.0, min(width, candidate[indices[0]]["position"][0] + dx))
    y = max(0.0, min(length, candidate[indices[0]]["position"][1] + dy))
    candidate[indices[0]]["position"][0:2] = [x, y]
    candidate[indices[1]]["position"][0:2] = [width - x, y]
    return candidate


def _accept(candidate_score: float, current_score: float, temperature: float, rng: random.Random | Any) -> bool:
    """Metropolis rule for a maximization objective."""
    delta = candidate_score - current_score
    if delta >= 0:
        return True
    return rng.random() < math.exp(delta / temperature)


def simulated_annealing(initial_lights: list[dict[str, Any]], score: ScoreFunction,
                        length: float, width: float, config: AnnealingConfig | None = None,
                        rng: random.Random | Any = random) -> AnnealingResult:
    """Run one SA cycle and return its best layout, score, and history."""
    config = config or AnnealingConfig()
    current = clone_lights(initial_lights)
    current_score = score(current)
    best, best_score = clone_lights(current), current_score
    history = [best_score]
    accepted = evaluated = 0
    temperature = config.initial_temperature

    while temperature >= config.final_temperature:
        for _ in range(config.iterations_per_temperature):
            candidate = perturb_lights(current, length, width, config.max_shift_m, rng)
            candidate_score = score(candidate)
            evaluated += 1
            if _accept(candidate_score, current_score, temperature, rng):
                current, current_score = candidate, candidate_score
                accepted += 1
                if current_score > best_score:
                    best, best_score = clone_lights(current), current_score
        history.append(best_score)
        temperature *= config.cooling_rate

    return AnnealingResult(best, best_score, history, accepted, evaluated)
