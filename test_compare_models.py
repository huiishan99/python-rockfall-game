import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO

from compare_models import (
    build_comparison_payload,
    cli,
    comparison_winner,
    format_comparison_lines,
    format_comparison_table,
    parse_args,
    score_delta,
    validate_model_paths,
)
from play_with_model import MODEL_FILE


SUMMARY_A = {
    "games": 2,
    "average_score": 5,
    "best_score": 7,
    "worst_score": 3,
    "average_best_combo": 4,
    "best_combo": 6,
    "average_frames": 150,
    "timeouts": 1,
}

SUMMARY_B = {
    "games": 2,
    "average_score": 8,
    "best_score": 10,
    "worst_score": 6,
    "average_best_combo": 5,
    "best_combo": 8,
    "average_frames": 180,
    "timeouts": 0,
}


class CompareModelsTest(unittest.TestCase):
    def test_parse_args_defaults_to_tracked_model(self):
        args = parse_args([])

        self.assertEqual(args.models, [MODEL_FILE])

    def test_parse_args_accepts_multiple_models_and_json(self):
        args = parse_args(["base.pkl", "candidate.pkl", "--json"])

        self.assertEqual(args.models, ["base.pkl", "candidate.pkl"])
        self.assertTrue(args.json)

    def test_parse_args_accepts_difficulty_preset(self):
        args = parse_args(["base.pkl", "--difficulty", "hard"])

        self.assertEqual(args.difficulty, "hard")

    def test_validate_model_paths_rejects_missing_model(self):
        with self.assertRaises(ValueError):
            validate_model_paths(["missing.pkl"])

    def test_validate_model_paths_accepts_existing_model(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = os.path.join(temp_dir, "model.pkl")
            with open(model_path, "w") as model_file:
                model_file.write("stub")

            validate_model_paths([model_path])

    def test_cli_reports_missing_model_without_traceback(self):
        output = StringIO()

        with redirect_stdout(output):
            status = cli(["missing.pkl", "--games", "1", "--max-frames", "300"])

        self.assertEqual(status, 1)
        self.assertIn("Error: Model file not found: missing.pkl", output.getvalue())

    def test_formats_comparison_table(self):
        lines = format_comparison_table(["base.pkl", "candidate.pkl"], [SUMMARY_A, SUMMARY_B])

        self.assertIn("Model", lines[0])
        self.assertIn("Avg Score", lines[0])
        self.assertIn("Score Delta", lines[0])
        self.assertIn("base.pkl", lines[1])
        self.assertIn("5.00", lines[1])
        self.assertIn("+0.00", lines[1])
        self.assertIn("candidate.pkl", lines[2])
        self.assertIn("8.00", lines[2])
        self.assertIn("+3.00", lines[2])

    def test_formats_comparison_lines_with_winner(self):
        lines = format_comparison_lines(["base.pkl", "candidate.pkl"], [SUMMARY_A, SUMMARY_B])

        self.assertEqual(lines[-1], "Best model by average score: candidate.pkl")

    def test_score_delta_compares_to_baseline(self):
        self.assertEqual(score_delta(SUMMARY_B, SUMMARY_A), 3)

    def test_comparison_winner_uses_average_score(self):
        self.assertEqual(comparison_winner(["base.pkl", "candidate.pkl"], [SUMMARY_A, SUMMARY_B]), "candidate.pkl")

    def test_builds_comparison_payload(self):
        payload = build_comparison_payload(
            ["base.pkl", "candidate.pkl"],
            [SUMMARY_A, SUMMARY_B],
            max_frames=300,
            random_seed=42,
            difficulty_preset="hard",
        )

        self.assertEqual(payload["max_frames"], 300)
        self.assertEqual(payload["random_seed"], 42)
        self.assertEqual(payload["difficulty"], "hard")
        self.assertEqual(payload["best_model"], "candidate.pkl")
        self.assertEqual(payload["models"][0]["model"], "base.pkl")
        self.assertEqual(payload["models"][0]["score_delta"], 0)
        self.assertEqual(payload["models"][1]["average_score"], 8)
        self.assertEqual(payload["models"][1]["score_delta"], 3)


if __name__ == "__main__":
    unittest.main()
