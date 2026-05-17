import unittest

from difficulty import (
    DEFAULT_DIFFICULTY_PRESET,
    difficulty_for_time,
    difficulty_level_for_time,
    difficulty_preset_for_name,
    difficulty_preset_names,
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

    def test_difficulty_presets_include_default(self):
        self.assertIn(DEFAULT_DIFFICULTY_PRESET, difficulty_preset_names())

    def test_unknown_difficulty_preset_raises(self):
        with self.assertRaises(ValueError):
            difficulty_preset_for_name("impossible")

    def test_hard_preset_increases_pressure(self):
        normal = difficulty_for_time(0, "normal")
        hard = difficulty_for_time(0, "hard")

        self.assertGreaterEqual(hard.obstacle_speed, normal.obstacle_speed)
        self.assertLessEqual(hard.obstacle_frequency, normal.obstacle_frequency)

    def test_easy_preset_reduces_pressure(self):
        normal = difficulty_for_time(0, "normal")
        easy = difficulty_for_time(0, "easy")

        self.assertLessEqual(easy.obstacle_speed, normal.obstacle_speed)
        self.assertGreaterEqual(easy.obstacle_frequency, normal.obstacle_frequency)


if __name__ == "__main__":
    unittest.main()
