"""Radiance scene export and point-grid illuminance calculation."""

from __future__ import annotations

import itertools
import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Sequence


class RadianceError(RuntimeError):
    """Raised when Radiance is missing or a simulation command fails."""


class RadianceCalculator:
    """Run oconv and rtrace for the supplied room and luminaire layout."""

    def __init__(self, lights: list[dict[str, Any]], walls: list[dict[str, Any]], materials: dict[str, dict[str, Any]], ambient_bounces: int = 2):
        self.lights = lights
        self.walls = walls
        self.materials = materials
        self.ambient_bounces = ambient_bounces

    def _write_materials(self, path: Path) -> None:
        with path.open("w", encoding="utf-8") as stream:
            for name, props in self.materials.items():
                if props["type"] == "plastic":
                    r, g, b = props["reflectance"]
                    roughness = props["roughness"]
                    stream.write(f"void plastic {name}\n0\n0\n5 {r} {g} {b} {roughness} 0\n\n")

    def _write_geometry(self, path: Path) -> None:
        with path.open("w", encoding="utf-8") as stream:
            for wall in self.walls:
                stream.write(f"{wall['material']} polygon {wall['name']}\n0\n0\n{3 * len(wall['vertices'])}")
                for vertex in wall["vertices"]:
                    stream.write(" " + " ".join(str(value) for value in vertex))
                stream.write("\n\n")

    def _write_lights(self, path: Path) -> None:
        with path.open("w", encoding="utf-8") as stream:
            for index, light in enumerate(self.lights, 1):
                name = f"{light['name']}_{index}"
                x, y, z = light["position"]
                red, green, blue = (value / 179.0 for value in light["flux"])
                half = light["size"] / 2.0
                stream.write(f"void light {name}_src\n0\n0\n3 {red} {green} {blue}\n\n")
                stream.write(f"{name}_src polygon {name}\n0\n0\n12")
                for dx, dy in ((-half, -half), (half, -half), (half, half), (-half, half)):
                    stream.write(f" {x + dx} {y + dy} {z}")
                stream.write("\n\n")

    @staticmethod
    def _run(args: Sequence[str], *, input_text: str | None = None) -> str:
        try:
            result = subprocess.run(args, input=input_text, capture_output=True, text=True, check=True)
        except FileNotFoundError as error:
            raise RadianceError(f"Radiance command not found: {args[0]}. Install Radiance and add it to PATH.") from error
        except subprocess.CalledProcessError as error:
            raise RadianceError(f"Radiance command failed ({' '.join(args)}):\n{error.stderr.strip()}") from error
        return result.stdout

    @staticmethod
    def _grid_values(start: float, stop: float, step: float) -> list[float]:
        if step <= 0 or stop < start:
            raise ValueError("Grid bounds must be ordered and grid_step must be positive")
        count = math.floor((stop - start + 1e-9) / step)
        return [round(start + index * step, 6) for index in range(count + 1)]

    def calculate_illuminance(self, height: float = 0.75, grid_step: float = 0.25,
                              xmin: float = 0, xmax: float = 3.9,
                              ymin: float = 0, ymax: float = 4.5) -> tuple[list[tuple[float, float, float, int, int, int]], list[float]]:
        """Return points and illuminance in lux, using the original 0.25 m grid."""
        points = [
            (x, y, height, 0, 0, 1)
            for x, y in itertools.product(
                self._grid_values(xmin, xmax, grid_step),
                self._grid_values(ymin, ymax, grid_step),
            )
        ]
        point_text = "".join(" ".join(map(str, point)) + "\n" for point in points)
        with tempfile.TemporaryDirectory(prefix="lighting-radiance-") as temp_dir:
            work = Path(temp_dir)
            material_file, geometry_file, light_file = work / "materials.mat", work / "scene.rad", work / "lights.rad"
            octree_file = work / "scene.oct"
            self._write_materials(material_file)
            self._write_geometry(geometry_file)
            self._write_lights(light_file)
            with octree_file.open("wb") as octree:
                result = subprocess.run(["oconv", str(material_file), str(geometry_file), str(light_file)], stdout=octree, stderr=subprocess.PIPE, text=True)
            if result.returncode:
                raise RadianceError(f"Radiance command failed (oconv):\n{result.stderr.strip()}")
            output = self._run(["rtrace", "-I", "-h", "-ab", str(self.ambient_bounces), str(octree_file)], input_text=point_text)

        illuminance = []
        for line_number, line in enumerate(output.splitlines(), 1):
            fields = line.split()
            if len(fields) != 3:
                raise RadianceError(f"rtrace returned malformed RGB output on line {line_number}: {line!r}")
            red, green, blue = map(float, fields)
            illuminance.append(round(179 * (0.265 * red + 0.670 * green + 0.065 * blue), 4))
        if len(illuminance) != len(points):
            raise RadianceError(f"rtrace returned {len(illuminance)} samples for {len(points)} grid points")
        return points, illuminance

    @staticmethod
    def analyze_results(illuminance: Sequence[float]) -> dict[str, float]:
        if not illuminance:
            raise ValueError("Cannot analyze an empty illuminance set")
        mean = sum(illuminance) / len(illuminance)
        minimum, maximum = min(illuminance), max(illuminance)
        return {"mean": mean, "min": minimum, "max": maximum, "uniformity": minimum / mean if mean else 0.0}
