import random
import unittest

from lighting_optimization.lighting.illuminance import RadianceCalculator
from lighting_optimization.lighting.model import build_scene
from lighting_optimization.optimization.objective import compliance_rate
from lighting_optimization.optimization.simulated_annealing import (
    AnnealingConfig,
    _accept,
    perturb_lights,
    simulated_annealing,
)


class CoreModelTests(unittest.TestCase):
    def test_compliance_uses_inclusive_lux_thresholds(self):
        self.assertEqual(compliance_rate([89.9, 90, 145, 200, 200.1]), 3 / 5)

    def test_default_sampling_grid_has_expected_point_count(self):
        lights, walls, materials = build_scene()
        calc = RadianceCalculator(lights, walls, materials)
        points = [
            (x, y, 0.75, 0, 0, 1)
            for x in calc._grid_values(0, 3.9, 0.25)
            for y in calc._grid_values(0, 4.5, 0.25)
        ]
        self.assertEqual(len(points), 304)
        self.assertEqual(points[0][:3], (0, 0, 0.75))

    def test_perturbation_does_not_mutate_input_and_preserves_pair(self):
        lights, _, _ = build_scene()
        original = [light["position"][:] for light in lights]
        class FixedRng:
            @staticmethod
            def choice(_values):
                return "pair_1"

            @staticmethod
            def uniform(_low, _high):
                return 0.1

        changed = perturb_lights(lights, 4.5, 3.9, rng=FixedRng())
        self.assertEqual([light["position"] for light in lights], original)
        # The fixed seed selects one of the mirrored pairs.
        self.assertAlmostEqual(changed[0]["position"][0] + changed[1]["position"][0], 3.9)
        self.assertAlmostEqual(changed[0]["position"][1], changed[1]["position"][1])

    def test_annealing_tracks_best_score_and_preserves_start_layout(self):
        lights, _, _ = build_scene()
        initial = [light["position"][:] for light in lights]
        seen = iter([0.0] + [0.25] * 2000)
        result = simulated_annealing(
            lights, lambda _: next(seen), 4.5, 3.9,
            AnnealingConfig(2, 1, 0.5, 2, 0.4), random.Random(2),
        )
        self.assertEqual(result.best_score, 0.25)
        self.assertEqual(result.evaluated_moves, 4)
        self.assertEqual(result.history, [0.0, 0.25, 0.25])
        self.assertEqual([light["position"] for light in lights], initial)

    def test_worse_move_uses_metropolis_probability_for_maximization(self):
        class FixedRandom:
            def __init__(self, value):
                self.value = value

            def random(self):
                return self.value

        self.assertTrue(_accept(0.25, 0.5, 1.0, FixedRandom(0.7)))
        self.assertFalse(_accept(0.25, 0.5, 1.0, FixedRandom(0.9)))


if __name__ == "__main__":
    unittest.main()
