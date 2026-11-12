"""Research case geometry and luminaire layout."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def build_scene(
    length: float = 4.5,
    width: float = 3.9,
    height: float = 3.0,
    initial_coordinates: tuple[float, ...] = (0.45, 0.7, 1.95, 1.68, 0.45, 2.7, 1.25, 4.0),
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Build the paper's 4.5 m by 3.9 m room with seven 466 lm luminaires.

    Coordinates are ordered as x1, y1, x2, y2, x3, y3, x4, y4, matching
    the original source. Three coordinate groups are mirrored across the
    room's width; lamp 3 is a standalone luminaire.
    """
    if len(initial_coordinates) != 8:
        raise ValueError("initial_coordinates must contain eight values")
    x1, y1, x2, y2, x3, y3, x4, y4 = initial_coordinates
    lights = [
        {"name": "lamp1", "position": [x1, y1, 2.8], "flux": [466, 466, 466], "size": 0.5},
        {"name": "lamp2", "position": [width - x1, y1, 2.8], "flux": [466, 466, 466], "size": 0.5},
        {"name": "lamp3", "position": [x2, y2, 2.8], "flux": [466, 466, 466], "size": 0.5},
        {"name": "lamp4", "position": [x3, y3, 2.8], "flux": [466, 466, 466], "size": 0.5},
        {"name": "lamp5", "position": [width - x3, y3, 2.8], "flux": [466, 466, 466], "size": 0.5},
        {"name": "lamp6", "position": [x4, y4, 2.8], "flux": [466, 466, 466], "size": 0.5},
        {"name": "lamp7", "position": [width - x4, y4, 2.8], "flux": [466, 466, 466], "size": 0.5},
    ]
    walls = [
        {"name": "wall0", "vertices": [(0, 0, 0), (width, 0, 0), (width, 0, height), (0, 0, height)], "material": "wall_mat"},
        {"name": "wall1", "vertices": [(0, 0, 0), (0, length, 0), (0, length, height), (0, 0, height)], "material": "wall_mat"},
        {"name": "wall2", "vertices": [(width, 0, 0), (width, length, 0), (width, length, height), (width, 0, height)], "material": "wall_mat"},
        {"name": "wall3", "vertices": [(0, length, 0), (width, length, 0), (width, length, height), (0, length, height)], "material": "wall_mat"},
        {"name": "floor", "vertices": [(0, 0, 0), (width, 0, 0), (width, length, 0), (0, length, 0)], "material": "floor_mat"},
    ]
    materials = {
        "wall_mat": {"type": "plastic", "reflectance": [0.6, 0.6, 0.6], "roughness": 0},
        "floor_mat": {"type": "plastic", "reflectance": [0.3, 0.3, 0.3], "roughness": 0},
    }
    return lights, walls, materials


def clone_lights(lights: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return an independent copy, including nested position and flux lists."""
    return deepcopy(lights)
