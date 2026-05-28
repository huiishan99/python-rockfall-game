import argparse
import json
import os
import tempfile
import unittest

from train_pipeline import (
    DEFAULT_CANDIDATE_MODEL,
    DEFAULT_PIPELINE_REPORT,
    build_pipeline_payload,
    format_pipeline_lines,
    parse_args,
    promotion_decision,
    validate_args,
    write_pipeline_report,
)


TRAINING_SUMMARY = {
    "data": "runs/data.json",
    "model": "runs/candidate.pkl",
    "valid_samples": 600,
    "skipped_entries": 0,
    "action_balance": {"left": 300, "right": 300},
    "variant_coverage": {
        "recorded_variant_samples": 1200,
        "legacy_obstacle_samples": 0,
        "warnings": [],
    },
    "objective_coverage": {
        "target_objective": "ore_target_v2",
        "target_samples": 600,
        "legacy_samples": 0,
        "other_samples": 0,
        "target_ratio": 1.0,
        "warnings": [],
    },
    "validation_accuracy": 0.75,
    "sample_weights": {"mode": "score", "min": 1, "max": 6, "average": 2.5},
    "data_quality": {"status": "ready", "warnings": []},
}

BASELINE_SUMMARY = {
    "games": 1,
    "average_score": 5,
    "best_score": 5,
    "worst_score": 5,
    "average_best_combo": 2,
    "best_combo": 2,
    "average_frames": 300,
    "average_lives_left": 2,
    "best_lives_left": 2,
    "survival_rate": 1.0,
    "timeouts": 1,
    "score_breakdown": {"survival": {"average": 5}, "ore_bonus": {"average": 0}, "ore_penalty": {"average": 0}},
}

CANDIDATE_SUMMARY = {
    **BASELINE_SUMMARY,
    "average_score": 9,
    "best_score": 9,
    "worst_score": 9,
    "score_breakdown": {"survival": {"average": 4}, "ore_bonus": {"average": 5}, "ore_penalty": {"average": 0}},
}


class TrainPipelineTest(unittest.TestCase):
    def test_parse_args_defaults_to_candidate_report_and_policy_baselines(self):
        args = parse_args([])

        self.assertEqual(args.candidate, DEFAULT_CANDIDATE_MODEL)
        self.assertEqual(args.report, DEFAULT_PIPELINE_REPORT)
        self.assertEqual(args.policy_baselines, ["safe-rule", "ore-hunter"])
        self.assertEqual(args.require_objective, "ore_target_v2")
        self.assertEqual(args.reward_weighting, "score")
        self.assertTrue(args.leaderboard.endswith("model_leaderboard.json"))
        self.assertFalse(args.skip_leaderboard)

    def test_validate_args_rejects_missing_baseline(self):
        args = parse_args(["--baseline", "missing.pkl"])

        with self.assertRaises(ValueError):
            validate_args(args)

    def test_validate_args_rejects_duplicate_policy_baselines(self):
        with tempfile.NamedTemporaryFile() as model_file:
            args = parse_args(
                [
                    "--baseline",
                    model_file.name,
                    "--policy-baselines",
                    "safe-rule",
                    "safe-rule",
                ]
            )

            with self.assertRaises(ValueError):
                validate_args(args)

    def test_promotion_decision_promotes_best_candidate(self):
        payload = build_payload(["game_model.pkl", "runs/candidate.pkl"], [BASELINE_SUMMARY, CANDIDATE_SUMMARY])

        decision = promotion_decision(payload, "runs/candidate.pkl")

        self.assertEqual(decision["action"], "promote_candidate")
        self.assertEqual(decision["score_delta"], 4)

    def test_promotion_decision_keeps_candidate_for_review_when_policy_wins(self):
        policy_summary = {**BASELINE_SUMMARY, "average_score": 12, "best_score": 12, "worst_score": 12}
        payload = build_payload(
            ["game_model.pkl", "runs/candidate.pkl", "policy:ore-hunter"],
            [BASELINE_SUMMARY, CANDIDATE_SUMMARY, policy_summary],
        )

        decision = promotion_decision(payload, "runs/candidate.pkl")

        self.assertEqual(decision["action"], "keep_candidate_for_review")

    def test_build_pipeline_payload_includes_decision_and_promotion_status(self):
        args = pipeline_args()

        payload = build_pipeline_payload(
            TRAINING_SUMMARY,
            ["game_model.pkl", "runs/candidate.pkl"],
            [BASELINE_SUMMARY, CANDIDATE_SUMMARY],
            args,
            promoted=True,
        )

        self.assertEqual(payload["comparison"]["best_model"], "runs/candidate.pkl")
        self.assertEqual(payload["decision"]["action"], "promote_candidate")
        self.assertTrue(payload["promotion"]["performed"])

    def test_format_pipeline_lines_includes_training_comparison_and_recommendation(self):
        payload = build_pipeline_payload(
            TRAINING_SUMMARY,
            ["game_model.pkl", "runs/candidate.pkl"],
            [BASELINE_SUMMARY, CANDIDATE_SUMMARY],
            pipeline_args(),
        )

        lines = format_pipeline_lines(payload)

        self.assertIn("Training pipeline", lines)
        self.assertIn("Comparison:", lines)
        self.assertTrue(any("Recommendation: promote_candidate" in line for line in lines))

    def test_write_pipeline_report_creates_parent_directory(self):
        payload = {"decision": {"action": "keep_baseline"}}
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = os.path.join(temp_dir, "reports", "pipeline.json")

            write_pipeline_report(payload, report_path)

            with open(report_path, "r") as report_file:
                self.assertEqual(json.load(report_file), payload)


def build_payload(labels, summaries):
    args = pipeline_args()
    return build_pipeline_payload(TRAINING_SUMMARY, labels, summaries, args)["comparison"]


def pipeline_args():
    return argparse.Namespace(
        baseline="game_model.pkl",
        candidate="runs/candidate.pkl",
        max_frames=300,
        eval_random_seed=42,
        difficulty="normal",
        player_speed=8,
        lives=3,
        variant_profile="variant-rich",
        min_score_delta=0.0,
        promote=False,
    )


if __name__ == "__main__":
    unittest.main()
