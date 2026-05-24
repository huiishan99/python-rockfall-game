import os
import json
import tempfile
import unittest

import joblib

from data_store import ORE_TARGET_DATA_FILE
from features import MAX_MODEL_OBSTACLES
from train_model import (
    MODEL_FILE,
    REQUIRE_OBJECTIVE_NONE,
    build_sample_weights,
    format_objective_coverage_line,
    format_sample_weight_line,
    format_variant_coverage_line,
    load_data,
    parse_args,
    reward_weight_for_features,
    sample_weight_summary,
    save_model,
    validate_required_objective,
)


class TrainModelTest(unittest.TestCase):
    def test_parse_args_defaults_to_tracked_model(self):
        args = parse_args([])

        self.assertEqual(args.data, ORE_TARGET_DATA_FILE)
        self.assertEqual(args.model, MODEL_FILE)
        self.assertEqual(args.reward_weighting, "none")
        self.assertEqual(args.require_objective, REQUIRE_OBJECTIVE_NONE)

    def test_parse_args_accepts_reward_weighting(self):
        args = parse_args(["--reward-weighting", "score"])

        self.assertEqual(args.reward_weighting, "score")

    def test_parse_args_accepts_required_objective(self):
        args = parse_args(["--require-objective", "ore_target_v2"])

        self.assertEqual(args.require_objective, "ore_target_v2")

    def test_save_model_creates_parent_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = os.path.join(temp_dir, "models", "experiment.pkl")

            save_model({"model": "stub"}, model_path)

            self.assertEqual(joblib.load(model_path), {"model": "stub"})

    def test_load_data_builds_variant_effect_features(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_path = os.path.join(temp_dir, "data.json")
            with open(data_path, "w") as data_file:
                json.dump(
                    [{"state": {"player_x": 100, "obstacles": [[120, 40, "ore"]]}, "action": "right"}],
                    data_file,
                )

            X, y, skipped_entries = load_data(data_path)

        self.assertEqual(X.tolist(), [[100, 120, 40, 20, 0, 5] + [100, 0, 0, 0, 0] * (MAX_MODEL_OBSTACLES - 1)])
        self.assertEqual(y.tolist(), [1])
        self.assertEqual(skipped_entries, 0)

    def test_format_variant_coverage_line_lists_variant_counts(self):
        line = format_variant_coverage_line(
            {
                "recorded_variant_samples": 3,
                "legacy_obstacle_samples": 1,
                "variant_counts": {"normal": 0, "heavy": 1, "swift": 1, "ore": 1},
            }
        )

        self.assertIn("recorded=3", line)
        self.assertIn("legacy=1", line)
        self.assertIn("ore=1", line)

    def test_format_objective_coverage_line_lists_target_samples(self):
        line = format_objective_coverage_line(
            {
                "target_objective": "ore_target_v2",
                "target_samples": 3,
                "legacy_samples": 1,
                "other_samples": 0,
                "target_ratio": 0.75,
            }
        )

        self.assertIn("target=ore_target_v2", line)
        self.assertIn("target_samples=3", line)
        self.assertIn("legacy=1", line)

    def test_validate_required_objective_rejects_warnings(self):
        objective_coverage = {
            "target_objective": "ore_target_v2",
            "warnings": ["mixed_legacy_and_ore_target_samples"],
        }

        with self.assertRaises(ValueError):
            validate_required_objective(objective_coverage, "ore_target_v2")

    def test_reward_weight_for_features_counts_reward_bearing_ore(self):
        features = [100, 120, 40, 20, 0, 5] + [100, 0, 0, 0, 0] * (MAX_MODEL_OBSTACLES - 1)

        self.assertEqual(reward_weight_for_features(features), 6)

    def test_build_sample_weights_can_disable_reward_weighting(self):
        self.assertIsNone(build_sample_weights([[100]], "none"))

    def test_build_sample_weights_scores_reward_bearing_rows(self):
        features = [
            [100, 120, 40, 20, 0, 5] + [100, 0, 0, 0, 0] * (MAX_MODEL_OBSTACLES - 1),
            [100, 120, 40, 200, 0, 0] + [100, 0, 0, 0, 0] * (MAX_MODEL_OBSTACLES - 1),
        ]

        self.assertEqual(build_sample_weights(features, "score"), [6, 1])

    def test_sample_weight_summary_formats_enabled_weights(self):
        summary = sample_weight_summary([1, 6], "score")

        self.assertEqual(summary["mode"], "score")
        self.assertEqual(summary["min"], 1)
        self.assertEqual(summary["max"], 6)
        self.assertEqual(summary["average"], 3.5)
        self.assertIn("avg=3.50", format_sample_weight_line(summary))


if __name__ == "__main__":
    unittest.main()
