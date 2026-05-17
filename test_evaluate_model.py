import unittest

from evaluate_model import build_summary_payload, format_summary_lines, parse_args, summarize_results


class EvaluateModelTest(unittest.TestCase):
    def test_parse_args_supports_json_output(self):
        args = parse_args(["--json"])

        self.assertTrue(args.json)

    def test_parse_args_accepts_difficulty_preset(self):
        args = parse_args(["--difficulty", "hard"])

        self.assertEqual(args.difficulty, "hard")

    def test_parse_args_accepts_player_speed(self):
        args = parse_args(["--player-speed", "8"])

        self.assertEqual(args.player_speed, 8)

    def test_summarizes_scores_and_timeouts(self):
        summary = summarize_results(
            [
                {"score": 3, "best_combo": 2, "frames": 100, "lives": 0, "timed_out": False},
                {"score": 7, "best_combo": 6, "frames": 200, "lives": 2, "timed_out": True},
            ]
        )

        self.assertEqual(summary["games"], 2)
        self.assertEqual(summary["average_score"], 5)
        self.assertEqual(summary["best_score"], 7)
        self.assertEqual(summary["worst_score"], 3)
        self.assertEqual(summary["average_best_combo"], 4)
        self.assertEqual(summary["best_combo"], 6)
        self.assertEqual(summary["average_frames"], 150)
        self.assertEqual(summary["timeouts"], 1)

    def test_formats_summary_lines(self):
        lines = format_summary_lines(
            {
                "games": 2,
                "average_score": 5,
                "best_score": 7,
                "worst_score": 3,
                "average_best_combo": 4,
                "best_combo": 6,
                "average_frames": 150,
                "timeouts": 1,
            },
            games_label="Evaluation games",
        )

        self.assertEqual(lines[0], "Evaluation games: 2")
        self.assertIn("Average best combo: 4.00", lines)
        self.assertIn("Timed out games: 1", lines)

    def test_builds_summary_payload_with_model_path(self):
        payload = build_summary_payload(
            "model.pkl",
            {
                "games": 2,
                "average_score": 5,
                "best_score": 7,
                "worst_score": 3,
                "average_best_combo": 4,
                "best_combo": 6,
                "average_frames": 150,
                "timeouts": 1,
            },
            max_frames=300,
            random_seed=42,
            difficulty_preset="hard",
            player_speed=8,
        )

        self.assertEqual(payload["model"], "model.pkl")
        self.assertEqual(payload["max_frames"], 300)
        self.assertEqual(payload["random_seed"], 42)
        self.assertEqual(payload["difficulty"], "hard")
        self.assertEqual(payload["player_speed"], 8)
        self.assertEqual(payload["games"], 2)
        self.assertEqual(payload["best_combo"], 6)


if __name__ == "__main__":
    unittest.main()
