import json
import os
import tempfile
import unittest

from model_report import (
    build_report_payload,
    format_report_lines,
    model_report_recommendations,
    parse_args,
    validate_args,
    write_model_report,
)


DATA_SUMMARY = {
    "data": "game_data.json",
    "valid_samples": 100,
    "skipped_entries": 3,
    "data_quality": {
        "status": "ready",
        "warnings": [],
    },
    "variant_coverage": {
        "status": "needs_variant_data",
        "warnings": ["no_recorded_variant_samples"],
        "recorded_variant_samples": 0,
    },
    "objective_coverage": {
        "status": "needs_objective_data",
        "warnings": ["no_ore_target_samples"],
        "target_objective": "ore_target_v2",
        "target_samples": 0,
    },
}

MODEL_RESULT = {
    "model": "game_model.pkl",
    "average_score": 5,
    "score_delta": 0,
    "survival_rate": 0.5,
    "score_breakdown": {
        "survival": {"average": 8},
        "ore_bonus": {"average": 0},
        "ore_penalty": {"average": 0},
    },
}

RULE_RESULT = {
    "model": "policy:safe-rule",
    "average_score": 8,
    "score_delta": 3,
    "survival_rate": 1.0,
    "score_breakdown": {
        "survival": {"average": 12},
        "ore_bonus": {"average": 5},
        "ore_penalty": {"average": 0},
    },
}

PROFILE_REPORTS = {
    "standard": {
        "best_model": "policy:safe-rule",
        "models": [MODEL_RESULT, RULE_RESULT],
    },
    "variant-rich": {
        "best_model": "policy:safe-rule",
        "models": [MODEL_RESULT, RULE_RESULT],
    },
}


class ModelReportTest(unittest.TestCase):
    def test_parse_args_defaults_to_both_profiles(self):
        args = parse_args([])

        self.assertEqual(args.profiles, ["standard", "variant-rich"])
        self.assertEqual(args.policy_baselines, ["safe-rule", "ore-hunter"])

    def test_parse_args_accepts_policy_baselines(self):
        args = parse_args(["--policy-baselines", "ore-hunter"])

        self.assertEqual(args.policy_baselines, ["ore-hunter"])

    def test_validate_args_rejects_duplicate_profiles(self):
        args = parse_args(["--profiles", "standard", "standard"])

        with self.assertRaises(ValueError):
            validate_args(args)

    def test_validate_args_rejects_duplicate_policy_baselines(self):
        args = parse_args(["--policy-baselines", "safe-rule", "safe-rule"])

        with self.assertRaises(ValueError):
            validate_args(args)

    def test_build_report_payload_includes_recommendations(self):
        payload = build_report_payload(
            "game_model.pkl",
            DATA_SUMMARY,
            PROFILE_REPORTS,
            games=1,
            max_frames=300,
            random_seed=42,
        )

        self.assertEqual(payload["model"], "game_model.pkl")
        self.assertIn("collect_ore_target_data", payload["recommendations"])
        self.assertIn("collect_variant_rich_data", payload["recommendations"])
        self.assertIn("beat_baseline_on_standard", payload["recommendations"])
        self.assertIn("improve_reward_capture_on_variant-rich", payload["recommendations"])

    def test_model_report_recommendations_are_unique(self):
        payload = {
            "model": "game_model.pkl",
            "data": DATA_SUMMARY,
            "profiles": PROFILE_REPORTS,
        }

        recommendations = model_report_recommendations(payload)

        self.assertEqual(recommendations.count("collect_variant_rich_data"), 1)

    def test_format_report_lines_summarizes_profiles(self):
        payload = build_report_payload(
            "game_model.pkl",
            DATA_SUMMARY,
            PROFILE_REPORTS,
            games=1,
            max_frames=300,
            random_seed=42,
            difficulty_preset="hard",
            player_speed=8,
            initial_lives=3,
        )

        lines = format_report_lines(payload)

        self.assertIn("Model learning report", lines)
        self.assertIn("Variant warnings: no_recorded_variant_samples", lines)
        self.assertIn("Objective warnings: no_ore_target_samples", lines)
        self.assertIn("Profile: variant-rich", lines)
        self.assertTrue(any("policy:safe-rule" in line for line in lines))
        self.assertTrue(any("Recommendations:" in line for line in lines))

    def test_write_model_report_creates_parent_directory(self):
        payload = {"model": "game_model.pkl"}
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = os.path.join(temp_dir, "reports", "model_report.json")

            write_model_report(payload, report_path)

            with open(report_path, "r") as report_file:
                self.assertEqual(json.load(report_file), payload)


if __name__ == "__main__":
    unittest.main()
