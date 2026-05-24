import json
import os
import tempfile
import unittest

from evaluate_model import (
    build_summary_payload,
    format_summary_lines,
    parse_args,
    summarize_results,
    summarize_score_breakdown,
    summarize_variant_stats,
    write_summary_report,
)


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

    def test_parse_args_accepts_lives(self):
        args = parse_args(["--lives", "3"])

        self.assertEqual(args.lives, 3)

    def test_parse_args_accepts_variant_profile(self):
        args = parse_args(["--variant-profile", "variant-rich"])

        self.assertEqual(args.variant_profile, "variant-rich")

    def test_parse_args_accepts_report_path(self):
        args = parse_args(["--report", "runs/eval.json"])

        self.assertEqual(args.report, "runs/eval.json")

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
        self.assertEqual(summary["average_lives_left"], 1)
        self.assertEqual(summary["best_lives_left"], 2)
        self.assertEqual(summary["survival_rate"], 0.5)
        self.assertEqual(summary["timeouts"], 1)
        self.assertIn("ore", summary["variant_stats"])
        self.assertIn("ore_bonus", summary["score_breakdown"])

    def test_summarizes_score_breakdown(self):
        score_breakdown = summarize_score_breakdown(
            [
                {"score_breakdown": {"survival": 3, "ore_bonus": 5, "combo_bonus": 1, "risk_bonus": 2}},
                {"score_breakdown": {"survival": 2, "ore_bonus": 5, "combo_bonus": 0, "risk_bonus": 0}},
            ]
        )

        self.assertEqual(score_breakdown["survival"]["total"], 5)
        self.assertEqual(score_breakdown["survival"]["average"], 2.5)
        self.assertEqual(score_breakdown["ore_bonus"]["total"], 10)
        self.assertEqual(score_breakdown["risk_bonus"]["total"], 2)

    def test_summarizes_variant_stats(self):
        variant_stats = summarize_variant_stats(
            [
                {"variant_stats": {"ore": {"spawned": 2, "avoided": 1, "hits": 1}}},
                {"variant_stats": {"ore": {"spawned": 1, "avoided": 1, "hits": 0}}},
            ]
        )

        self.assertEqual(variant_stats["ore"]["spawned"], 3)
        self.assertEqual(variant_stats["ore"]["avoided"], 2)
        self.assertEqual(variant_stats["ore"]["hits"], 1)
        self.assertEqual(variant_stats["ore"]["encounters"], 3)
        self.assertAlmostEqual(variant_stats["ore"]["avoid_rate"], 2 / 3)

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
                "average_lives_left": 1,
                "best_lives_left": 2,
                "survival_rate": 0.5,
                "timeouts": 1,
            },
            games_label="Evaluation games",
        )

        self.assertEqual(lines[0], "Evaluation games: 2")
        self.assertIn("Average best combo: 4.00", lines)
        self.assertIn("Average lives left: 1.00", lines)
        self.assertIn("Survival rate: 50.0%", lines)
        self.assertIn("Timed out games: 1", lines)

    def test_formats_variant_summary_lines(self):
        lines = format_summary_lines(
            {
                "games": 1,
                "average_score": 5,
                "best_score": 5,
                "worst_score": 5,
                "average_best_combo": 4,
                "best_combo": 4,
                "average_frames": 150,
                "average_lives_left": 1,
                "best_lives_left": 1,
                "survival_rate": 1,
                "timeouts": 1,
                "variant_stats": {
                    "ore": {"spawned": 2, "avoided": 1, "hits": 1, "avoid_rate": 0.5},
                },
            }
        )

        self.assertIn("Variant outcomes:", lines)
        self.assertIn("  ore: spawned=2, avoided=1, hits=1, avoid_rate=50.0%", lines)

    def test_formats_score_breakdown_lines(self):
        lines = format_summary_lines(
            {
                "games": 1,
                "average_score": 5,
                "best_score": 5,
                "worst_score": 5,
                "average_best_combo": 4,
                "best_combo": 4,
                "average_frames": 150,
                "average_lives_left": 1,
                "best_lives_left": 1,
                "survival_rate": 1,
                "timeouts": 1,
                "score_breakdown": {
                    "survival": {"total": 3, "average": 3},
                    "ore_bonus": {"total": 5, "average": 5},
                    "combo_bonus": {"total": 1, "average": 1},
                    "risk_bonus": {"total": 2, "average": 2},
                },
            }
        )

        self.assertIn("Run breakdown:", lines)
        self.assertIn("  ore_bonus: total=5, avg=5.00", lines)
        self.assertIn("  risk_bonus: total=2, avg=2.00", lines)

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
                "average_lives_left": 1,
                "best_lives_left": 2,
                "survival_rate": 0.5,
                "timeouts": 1,
            },
            max_frames=300,
            random_seed=42,
            difficulty_preset="hard",
            player_speed=8,
            initial_lives=3,
            variant_profile="variant-rich",
        )

        self.assertEqual(payload["model"], "model.pkl")
        self.assertEqual(payload["max_frames"], 300)
        self.assertEqual(payload["random_seed"], 42)
        self.assertEqual(payload["difficulty"], "hard")
        self.assertEqual(payload["player_speed"], 8)
        self.assertEqual(payload["initial_lives"], 3)
        self.assertEqual(payload["variant_profile"], "variant-rich")
        self.assertEqual(payload["games"], 2)
        self.assertEqual(payload["best_combo"], 6)
        self.assertEqual(payload["survival_rate"], 0.5)

    def test_write_summary_report_creates_parent_directory(self):
        payload = {"model": "model.pkl", "games": 1}
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = os.path.join(temp_dir, "reports", "eval.json")

            write_summary_report(payload, report_path)

            with open(report_path, "r") as report_file:
                self.assertEqual(json.load(report_file), payload)


if __name__ == "__main__":
    unittest.main()
