import json
import os
import tempfile
import unittest

from leaderboard import empty_leaderboard, save_leaderboard
from ml_dashboard import (
    build_dashboard_payload,
    dashboard_recommendations,
    format_dashboard_lines,
    parse_args,
    validate_args,
    write_dashboard_report,
)


READY_DATA = {
    "data": "runs/data.json",
    "valid_samples": 600,
    "skipped_entries": 0,
    "data_quality": {"status": "ready", "warnings": []},
    "variant_coverage": {
        "status": "ready",
        "warnings": [],
        "recorded_variant_samples": 600,
    },
    "objective_coverage": {
        "status": "ready",
        "warnings": [],
        "target_samples": 600,
        "target_objective": "ore_target_v2",
    },
}


class MLDashboardTest(unittest.TestCase):
    def test_parse_args_uses_defaults(self):
        args = parse_args([])

        self.assertEqual(args.top, 5)
        self.assertTrue(args.report.endswith("ml_dashboard.json"))

    def test_validate_args_rejects_bad_top(self):
        args = parse_args(["--top", "0"])

        with self.assertRaises(ValueError):
            validate_args(args)

    def test_dashboard_recommends_pipeline_when_leaderboard_empty(self):
        recommendations = dashboard_recommendations(READY_DATA, empty_leaderboard())

        self.assertIn("run_training_pipeline", recommendations)

    def test_dashboard_recommends_training_when_policy_leads(self):
        leaderboard = {
            "entries": [
                {
                    "model": "policy:ore-hunter",
                    "average_score": 9,
                    "average_ore_bonus": 5,
                    "survival_rate": 1,
                    "average_lives_left": 1,
                    "average_frames": 300,
                }
            ]
        }

        recommendations = dashboard_recommendations(READY_DATA, leaderboard)

        self.assertIn("train_model_that_beats_policy_baseline", recommendations)

    def test_build_dashboard_payload_reads_data_and_leaderboard(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_path = os.path.join(temp_dir, "data.json")
            leaderboard_path = os.path.join(temp_dir, "leaderboard.json")
            with open(data_path, "w") as data_file:
                json.dump(
                    [
                        {"state": {"player_x": 1, "obstacles": []}, "action": "left", "objective": "ore_target_v2"},
                        {"state": {"player_x": 2, "obstacles": []}, "action": "right", "objective": "ore_target_v2"},
                    ],
                    data_file,
                )
            save_leaderboard(
                {
                    "schema_version": 1,
                    "entries": [
                        {
                            "id": "abc",
                            "model": "game_model.pkl",
                            "average_score": 5,
                            "average_ore_bonus": 0,
                            "survival_rate": 0.5,
                            "average_lives_left": 1,
                            "average_frames": 100,
                        }
                    ],
                },
                leaderboard_path,
            )

            payload = build_dashboard_payload(
                data_path,
                leaderboard_path,
                min_samples=1,
                min_balance_ratio=0,
                top=1,
            )

            self.assertEqual(payload["leaderboard"]["entry_count"], 1)
            self.assertEqual(payload["leaderboard"]["top_entries"][0]["model"], "game_model.pkl")

    def test_format_dashboard_lines_includes_data_and_leaderboard(self):
        payload = {
            "data": READY_DATA,
            "leaderboard": {"path": "runs/model_leaderboard.json", "entry_count": 0, "top_entries": []},
            "recommendations": ["run_training_pipeline"],
        }

        lines = format_dashboard_lines(payload)

        self.assertIn("Rockfall ML dashboard", lines)
        self.assertTrue(any("Leaderboard:" in line for line in lines))
        self.assertTrue(any("Recommendations:" in line for line in lines))

    def test_write_dashboard_report_creates_parent_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = os.path.join(temp_dir, "reports", "dashboard.json")

            write_dashboard_report({"ok": True}, report_path)

            with open(report_path, "r") as report_file:
                self.assertEqual(json.load(report_file), {"ok": True})


if __name__ == "__main__":
    unittest.main()
