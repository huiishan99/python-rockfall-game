import unittest

from release_check import build_release_payload, parse_args
from settings import INITIAL_LIVES, PLAYER_SPEED, VERSION


class ReleaseCheckTest(unittest.TestCase):
    def test_parse_args_defaults(self):
        args = parse_args([])

        self.assertEqual(args.games, 3)
        self.assertEqual(args.max_frames, 1800)
        self.assertEqual(args.difficulty, "normal")
        self.assertEqual(args.player_speed, PLAYER_SPEED)
        self.assertEqual(args.lives, INITIAL_LIVES)

    def test_parse_args_overrides(self):
        args = parse_args(["--games", "5", "--max-frames", "600", "--model", "alt.pkl"])

        self.assertEqual(args.games, 5)
        self.assertEqual(args.max_frames, 600)
        self.assertEqual(args.model, "alt.pkl")

    def test_parse_args_accepts_difficulty(self):
        args = parse_args(["--difficulty", "hard"])

        self.assertEqual(args.difficulty, "hard")

    def test_parse_args_accepts_player_speed(self):
        args = parse_args(["--player-speed", "8"])

        self.assertEqual(args.player_speed, 8)

    def test_parse_args_accepts_lives(self):
        args = parse_args(["--lives", "3"])

        self.assertEqual(args.lives, 3)

    def test_parse_args_accepts_report_path(self):
        args = parse_args(["--report", "runs/release_check.json"])

        self.assertEqual(args.report, "runs/release_check.json")

    def test_build_release_payload_includes_version_tests_and_evaluation(self):
        summary = {
            "games": 1,
            "average_score": 8,
            "best_score": 8,
            "worst_score": 8,
            "average_best_combo": 6,
            "best_combo": 6,
            "average_frames": 300,
            "average_lives_left": 3,
            "best_lives_left": 3,
            "survival_rate": 1.0,
            "timeouts": 1,
        }

        payload = build_release_payload(
            "game_model.pkl",
            summary,
            max_frames=300,
            random_seed=42,
            difficulty_preset="normal",
            player_speed=8,
            initial_lives=3,
            tests_passed=True,
        )

        self.assertEqual(payload["version"], VERSION)
        self.assertTrue(payload["unit_tests"]["passed"])
        self.assertEqual(payload["evaluation"]["model"], "game_model.pkl")
        self.assertEqual(payload["evaluation"]["initial_lives"], 3)
        self.assertEqual(payload["evaluation"]["survival_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
