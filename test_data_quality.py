import json
import os
import tempfile
import unittest

from data_quality import action_balance_payload, inspect_data_file, objective_coverage_summary, variant_coverage_summary
from data_store import ORE_TARGET_OBJECTIVE


class DataQualityTest(unittest.TestCase):
    def test_action_balance_payload_handles_missing_actions(self):
        payload = action_balance_payload({1: 3})

        self.assertEqual(payload, {"left": 0, "right": 3})

    def test_inspect_data_file_summarizes_valid_and_skipped_entries(self):
        entries = [
            {"state": {"player_x": 100, "obstacles": [[120, 40]]}, "action": "left"},
            {"state": {"player_x": 200, "obstacles": [[180, 50]]}, "action": "right"},
            {"state": {"player_x": 300, "obstacles": []}, "action": "left"},
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            data_path = os.path.join(temp_dir, "data.json")
            with open(data_path, "w") as data_file:
                json.dump(entries, data_file)

            summary = inspect_data_file(
                data_path,
                min_samples=2,
                min_balance_ratio=0.4,
                max_skipped_ratio=0.5,
            )

        self.assertEqual(summary["valid_samples"], 2)
        self.assertEqual(summary["skipped_entries"], 1)
        self.assertEqual(summary["action_balance"], {"left": 1, "right": 1})
        self.assertEqual(summary["variant_coverage"]["legacy_obstacle_samples"], 2)
        self.assertEqual(summary["variant_coverage"]["warnings"], ["no_recorded_variant_samples"])
        self.assertEqual(summary["objective_coverage"]["legacy_samples"], 2)
        self.assertEqual(summary["objective_coverage"]["warnings"], ["no_ore_target_samples"])
        self.assertEqual(summary["data_quality"]["status"], "ready")

    def test_variant_coverage_summarizes_recorded_nearest_variants(self):
        entries = [
            {"state": {"player_x": 100, "obstacles": [[120, 40, "ore"]]}, "action": "left"},
            {"state": {"player_x": 200, "obstacles": [[180, 50, "heavy"]]}, "action": "right"},
            {"state": {"player_x": 300, "obstacles": [[220, 20, "ore"], [260, 70, "swift"]]}, "action": "left"},
            {"state": {"player_x": 100, "obstacles": [[120, 40]]}, "action": "right"},
        ]

        coverage = variant_coverage_summary(entries)

        self.assertEqual(coverage["recorded_variant_samples"], 4)
        self.assertEqual(coverage["legacy_obstacle_samples"], 1)
        self.assertEqual(coverage["variant_counts"]["ore"], 2)
        self.assertEqual(coverage["variant_counts"]["heavy"], 1)
        self.assertEqual(coverage["variant_counts"]["swift"], 1)
        self.assertEqual(coverage["status"], "variant_ready")

    def test_objective_coverage_summarizes_ore_target_samples(self):
        entries = [
            {
                "state": {"player_x": 100, "obstacles": [[120, 40, "ore"]]},
                "action": "left",
                "objective": ORE_TARGET_OBJECTIVE,
                "source": "manual",
            },
            {
                "state": {"player_x": 200, "obstacles": [[180, 50, "normal"]]},
                "action": "right",
                "objective": ORE_TARGET_OBJECTIVE,
                "source": "policy:safe-rule",
            },
        ]

        coverage = objective_coverage_summary(entries)

        self.assertEqual(coverage["target_samples"], 2)
        self.assertEqual(coverage["legacy_samples"], 0)
        self.assertEqual(coverage["status"], "objective_ready")
        self.assertEqual(coverage["warnings"], [])
        self.assertEqual(coverage["source_counts"]["manual"], 1)

    def test_objective_coverage_warns_on_mixed_legacy_data(self):
        entries = [
            {
                "state": {"player_x": 100, "obstacles": [[120, 40, "ore"]]},
                "action": "left",
                "objective": ORE_TARGET_OBJECTIVE,
            },
            {"state": {"player_x": 200, "obstacles": [[180, 50, "normal"]]}, "action": "right"},
        ]

        coverage = objective_coverage_summary(entries)

        self.assertEqual(coverage["target_samples"], 1)
        self.assertEqual(coverage["legacy_samples"], 1)
        self.assertIn("mixed_legacy_and_ore_target_samples", coverage["warnings"])


if __name__ == "__main__":
    unittest.main()
