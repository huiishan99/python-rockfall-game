import unittest

from difficulty import (
    difficulty_for_time,
    difficulty_level_for_time,
    obstacle_frequency_for_level,
    obstacle_speed_for_level,
)
from settings import (
    DIFFICULTY_INTERVAL_FRAMES,
    INITIAL_DIFFICULTY_LEVEL,
    INITIAL_OBSTACLE_SPEED,
    MAX_DIFFICULTY_LEVEL,
    MIN_OBSTACLE_FREQUENCY,
    OBSTACLE_FREQUENCY,
)


class DifficultyCurveTest(unittest.TestCase):
    def test_level_starts_at_initial_level(self):
        self.assertEqual(difficulty_level_for_time(0), INITIAL_DIFFICULTY_LEVEL)

    def test_level_increases_on_interval(self):
        self.assertEqual(
            difficulty_level_for_time(DIFFICULTY_INTERVAL_FRAMES),
            INITIAL_DIFFICULTY_LEVEL + 1,
        )

    def test_level_is_capped(self):
        self.assertEqual(difficulty_level_for_time(999999), MAX_DIFFICULTY_LEVEL)

    def test_obstacle_speed_increases_by_level(self):
        self.assertEqual(
            obstacle_speed_for_level(INITIAL_DIFFICULTY_LEVEL + 2),
            INITIAL_OBSTACLE_SPEED + 2,
        )

    def test_obstacle_frequency_gets_faster_but_is_capped(self):
        self.assertLess(
            obstacle_frequency_for_level(INITIAL_DIFFICULTY_LEVEL + 1),
            OBSTACLE_FREQUENCY,
        )
        self.assertEqual(obstacle_frequency_for_level(999), MIN_OBSTACLE_FREQUENCY)

    def test_difficulty_state_combines_curve_values(self):
        difficulty = difficulty_for_time(DIFFICULTY_INTERVAL_FRAMES)

        self.assertEqual(difficulty.level, INITIAL_DIFFICULTY_LEVEL + 1)
        self.assertEqual(difficulty.obstacle_speed, INITIAL_OBSTACLE_SPEED + 1)
        self.assertLess(difficulty.obstacle_frequency, OBSTACLE_FREQUENCY)


if __name__ == "__main__":
    unittest.main()
