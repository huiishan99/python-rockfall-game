import unittest

from run_model_experiment import (
    DEFAULT_CANDIDATE_MODEL,
    build_experiment_payload,
    format_experiment_lines,
    parse_args,
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
                "--json",
            ]
        )

        self.assertEqual(args.data, "runs/playtest.json")
        self.assertEqual(args.candidate, "runs/v02.pkl")
        self.assertTrue(args.json)

    def test_builds_experiment_payload(self):
        payload = build_experiment_payload(
            TRAINING_SUMMARY,
            ["game_model.pkl", "runs/candidate_model.pkl"],
            [BASELINE_SUMMARY, CANDIDATE_SUMMARY],
            max_frames=300,
            eval_random_seed=42,
        )

        self.assertEqual(payload["training"]["validation_accuracy"], 0.875)
        self.assertEqual(payload["comparison"]["max_frames"], 300)
        self.assertEqual(payload["comparison"]["models"][1]["model"], "runs/candidate_model.pkl")

    def test_formats_experiment_lines(self):
        lines = format_experiment_lines(
            TRAINING_SUMMARY,
            ["game_model.pkl", "runs/candidate_model.pkl"],
            [BASELINE_SUMMARY, CANDIDATE_SUMMARY],
        )

        self.assertIn("Training candidate model:", lines)
        self.assertIn("Validation accuracy: 0.875", lines)
        self.assertIn("Model comparison:", lines)
        self.assertTrue(any("runs/candidate_model.pkl" in line for line in lines))


if __name__ == "__main__":
    unittest.main()
