import random
import unittest

from settings import SCREEN_WIDTH, SPAWN_LANE_COUNT
from spawning import build_spawn_lanes, choose_spawn_x, minimum_lane_gap_for_level


class SpawningTest(unittest.TestCase):
    def test_builds_configured_lane_count(self):
        lanes = build_spawn_lanes()

        self.assertEqual(len(lanes), SPAWN_LANE_COUNT)
        self.assertEqual(lanes[0], 0)
        self.assertLessEqual(lanes[-1], SCREEN_WIDTH)

    def test_low_difficulty_keeps_gap_from_previous_lane(self):
        lanes = build_spawn_lanes()
        previous_x = lanes[3]
        rng = random.Random(1)

        for _ in range(20):
            spawn_x = choose_spawn_x(previous_x, level=1, rng=rng)
            previous_lane = min(range(len(lanes)), key=lambda index: abs(lanes[index] - previous_x))
            spawn_lane = lanes.index(spawn_x)
            self.assertGreaterEqual(abs(spawn_lane - previous_lane), 2)

    def test_high_difficulty_allows_adjacent_pressure(self):
        self.assertEqual(minimum_lane_gap_for_level(10), 0)

    def test_first_spawn_uses_a_lane(self):
        rng = random.Random(2)

        self.assertIn(choose_spawn_x(rng=rng), build_spawn_lanes())


if __name__ == "__main__":
    unittest.main()
