import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO

from run_model_experiment import (
    DEFAULT_CANDIDATE_MODEL,
    build_experiment_payload,
    candidate_result,
    cli,
    data_quality_summary,
    format_experiment_lines,
    parse_args,
    validate_experiment_paths,
    write_experiment_report,
)


TRAINING_SUMMARY = {
    "data": "game_data.json",
    "model": "runs/candidate_model.pkl",
    "valid_samples": 100,
    "skipped_entries": 3,
    "features": ["player_x", "nearest_obstacle_x"],
    "action_balance": {"left": 45, "right": 55},
    "validation_accuracy": 0.875,
    "estimators": 100,
    "test_size": 0.2,
    "random_state": 42,
    "data_quality": {
        "status": "ready",
        "warnings": [],
        "valid_samples": 100,
        "skipped_entries": 3,
        "skipped_ratio": 0.02912621359223301,
        "balance_ratio": 0.45,
        "min_samples": 50,
        "min_balance_ratio": 0.35,
        "max_skipped_ratio": 0.10,
    },
}

BASELINE_SUMMARY = {
    "games": 2,
    "average_score": 5,
    "best_score": 7,
    "worst_score": 3,
    "average_best_combo": 4,
    "best_combo": 6,
    "average_frames": 150,
    "timeouts": 1,
}

CANDIDATE_SUMMARY = {
    "games": 2,
    "average_score": 8,
    "best_score": 10,
    "worst_score": 6,
    "average_best_combo": 5,
    "best_combo": 8,
    "average_frames": 180,
    "timeouts": 0,
}


class RunModelExperimentTest(unittest.TestCase):
    def test_parse_args_defaults_to_candidate_model(self):
        args = parse_args([])

        self.assertEqual(args.candidate, DEFAULT_CANDIDATE_MODEL)

    def test_parse_args_accepts_experiment_overrides(self):
        args = parse_args(
            [
                "--data",
                "runs/playtest.json",
                "--baseline",
                "game_model.pkl",
                "--candidate",
                "runs/v02.pkl",
                "--report",
                "runs/v02_report.json",
                "--difficulty",
                "hard",
                "--json",
            ]
        )

        self.assertEqual(args.data, "runs/playtest.json")
        self.assertEqual(args.candidate, "runs/v02.pkl")
        self.assertEqual(args.report, "runs/v02_report.json")
        self.assertEqual(args.difficulty, "hard")
        self.assertTrue(args.json)

    def test_validate_experiment_paths_rejects_baseline_overwrite(self):
        with self.assertRaises(ValueError):
            validate_experiment_paths("game_model.pkl", "game_model.pkl")

    def test_validate_experiment_paths_allows_separate_candidate(self):
        validate_experiment_paths("game_model.pkl", "runs/candidate.pkl")

    def test_data_quality_summary_is_ready_when_thresholds_pass(self):
        quality = data_quality_summary(
            valid_samples=1000,
            skipped_entries=10,
            action_counts={0: 450, 1: 550},
            min_samples=500,
            min_balance_ratio=0.35,
            max_skipped_ratio=0.10,
        )

        self.assertEqual(quality["status"], "ready")
        self.assertEqual(quality["warnings"], [])
        self.assertAlmostEqual(quality["balance_ratio"], 0.45)

    def test_data_quality_summary_warns_on_small_or_unbalanced_data(self):
        quality = data_quality_summary(
            valid_samples=51,
            skipped_entries=20,
            action_counts={0: 5, 1: 46},
            min_samples=500,
            min_balance_ratio=0.35,
            max_skipped_ratio=0.10,
        )

        self.assertEqual(quality["status"], "needs_more_data")
        self.assertIn("valid_samples_below_500", quality["warnings"])
        self.assertIn("action_balance_below_0.35", quality["warnings"])
        self.assertIn("skipped_ratio_above_0.10", quality["warnings"])

    def test_cli_reports_baseline_overwrite_without_traceback(self):
        output = StringIO()

        with redirect_stdout(output):
            status = cli(["--baseline", "game_model.pkl", "--candidate", "game_model.pkl"])

        self.assertEqual(status, 1)
        self.assertIn("Error: --candidate must be different from --baseline", output.getvalue())

    def test_cli_reports_missing_baseline_before_training(self):
        output = StringIO()

        with redirect_stdout(output):
            status = cli(["--baseline", "missing.pkl", "--candidate", "runs/candidate.pkl"])

        self.assertEqual(status, 1)
        self.assertIn("Error: Model file not found: missing.pkl", output.getvalue())

    def test_builds_experiment_payload(self):
        payload = build_experiment_payload(
            TRAINING_SUMMARY,
            ["game_model.pkl", "runs/candidate_model.pkl"],
            [BASELINE_SUMMARY, CANDIDATE_SUMMARY],
            max_frames=300,
            eval_random_seed=42,
            difficulty_preset="hard",
        )

        self.assertEqual(payload["training"]["validation_accuracy"], 0.875)
        self.assertEqual(payload["candidate_result"], "candidate_outperformed_baseline")
        self.assertEqual(payload["comparison"]["difficulty"], "hard")
        self.assertEqual(payload["comparison"]["max_frames"], 300)
        self.assertEqual(payload["comparison"]["best_model"], "runs/candidate_model.pkl")
        self.assertEqual(payload["comparison"]["models"][1]["model"], "runs/candidate_model.pkl")

    def test_candidate_result_compares_average_score(self):
        self.assertEqual(candidate_result(BASELINE_SUMMARY, CANDIDATE_SUMMARY), "candidate_outperformed_baseline")
        self.assertEqual(candidate_result(CANDIDATE_SUMMARY, BASELINE_SUMMARY), "candidate_underperformed_baseline")
        self.assertEqual(candidate_result(BASELINE_SUMMARY, BASELINE_SUMMARY), "candidate_matched_baseline")

    def test_formats_experiment_lines(self):
        lines = format_experiment_lines(
            TRAINING_SUMMARY,
            ["game_model.pkl", "runs/candidate_model.pkl"],
            [BASELINE_SUMMARY, CANDIDATE_SUMMARY],
        )

        self.assertIn("Training candidate model:", lines)
        self.assertIn("Validation accuracy: 0.875", lines)
        self.assertIn("Data quality: ready", lines)
        self.assertIn("Model comparison:", lines)
        self.assertIn("Best model by average score: runs/candidate_model.pkl", lines)
        self.assertIn("Candidate result: candidate_outperformed_baseline", lines)
        self.assertTrue(any("runs/candidate_model.pkl" in line for line in lines))

    def test_write_experiment_report_creates_parent_directory(self):
        payload = {"training": {"model": "candidate.pkl"}}
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = os.path.join(temp_dir, "reports", "experiment.json")

            write_experiment_report(payload, report_path)

            with open(report_path, "r") as report_file:
                self.assertEqual(json.load(report_file), payload)


if __name__ == "__main__":
    unittest.main()
