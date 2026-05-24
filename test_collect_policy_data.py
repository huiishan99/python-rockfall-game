import json
import os
import tempfile
import unittest

from collect_policy_data import (
    DEFAULT_POLICY_DATA_FILE,
    build_collection_payload,
    collect_game_samples,
    format_collection_lines,
    parse_args,
    validate_args,
    write_collection_report,
)
from data_store import ORE_TARGET_OBJECTIVE, POLICY_ORE_TARGET_DATA_FILE


COLLECTION_SUMMARY = {
    "games": 1,
    "average_score": 2,
    "best_score": 2,
    "worst_score": 2,
    "average_best_combo": 2,
    "best_combo": 2,
    "average_frames": 2,
    "average_lives_left": 3,
    "best_lives_left": 3,
    "survival_rate": 1.0,
    "timeouts": 1,
    "variant_stats": {
        "ore": {"spawned": 1, "avoided": 1, "hits": 0, "avoid_rate": 1.0},
    },
    "score_breakdown": {
        "survival": {"total": 2, "average": 2},
        "ore_bonus": {"total": 5, "average": 5},
        "combo_bonus": {"total": 0, "average": 0},
        "ore_penalty": {"total": 0, "average": 0},
    },
}

DATA_SUMMARY = {
    "variant_coverage": {
        "recorded_variant_samples": 4,
        "legacy_obstacle_samples": 0,
        "status": "variant_ready",
        "warnings": [],
    },
    "objective_coverage": {
        "target_objective": ORE_TARGET_OBJECTIVE,
        "target_samples": 10,
        "legacy_samples": 0,
        "other_samples": 0,
        "status": "objective_ready",
        "warnings": [],
    },
}


class CollectPolicyDataTest(unittest.TestCase):
    def test_parse_args_defaults_to_runs_policy_ore_target_data(self):
        args = parse_args([])

        self.assertEqual(args.data, POLICY_ORE_TARGET_DATA_FILE)
        self.assertEqual(DEFAULT_POLICY_DATA_FILE, POLICY_ORE_TARGET_DATA_FILE)
        self.assertEqual(args.policy, "safe-rule")
        self.assertEqual(args.variant_profile, "variant-rich")

    def test_validate_args_rejects_nonpositive_games(self):
        args = parse_args(["--games", "0"])

        with self.assertRaises(ValueError):
            validate_args(args)

    def test_collect_game_samples_records_policy_actions(self):
        game = StubGame()

        samples, result = collect_game_samples(game, "safe-rule", max_frames=2)

        self.assertEqual(len(samples), 2)
        self.assertEqual(samples[0]["state"]["player_x"], 100)
        self.assertIn(samples[0]["action"], ("left", "right"))
        self.assertEqual(samples[0]["objective"], ORE_TARGET_OBJECTIVE)
        self.assertEqual(samples[0]["source"], "policy:safe-rule")
        self.assertEqual(result["frames"], 2)
        self.assertTrue(result["timed_out"])

    def test_build_collection_payload_includes_settings(self):
        payload = build_collection_payload(
            "runs/policy.json",
            "safe-rule",
            samples_written=10,
            previous_count=2,
            total_count=12,
            summary=COLLECTION_SUMMARY,
            data_summary=DATA_SUMMARY,
            games=1,
            max_frames=300,
            random_seed=42,
            difficulty_preset="normal",
            player_speed=8,
            initial_lives=3,
            variant_profile="variant-rich",
        )

        self.assertEqual(payload["samples_written"], 10)
        self.assertEqual(payload["settings"]["variant_profile"], "variant-rich")

    def test_format_collection_lines_mentions_variant_coverage(self):
        payload = build_collection_payload(
            "runs/policy.json",
            "safe-rule",
            samples_written=10,
            previous_count=2,
            total_count=12,
            summary=COLLECTION_SUMMARY,
            data_summary=DATA_SUMMARY,
            games=1,
            max_frames=300,
            random_seed=42,
            difficulty_preset="normal",
            player_speed=8,
            initial_lives=3,
            variant_profile="variant-rich",
        )

        lines = format_collection_lines(payload)

        self.assertIn("Policy data collection", lines)
        self.assertIn("Variant coverage: recorded=4, legacy=0, quality=variant_ready", lines)
        self.assertIn(
            "Objective coverage: target=ore_target_v2, target_samples=10, legacy=0, quality=objective_ready",
            lines,
        )
        self.assertIn("Collected games: 1", lines)

    def test_write_collection_report_creates_parent_directory(self):
        payload = {"policy": "safe-rule"}
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = os.path.join(temp_dir, "reports", "policy.json")

            write_collection_report(payload, report_path)

            with open(report_path, "r") as report_file:
                self.assertEqual(json.load(report_file), payload)


class StubGame:
    def __init__(self):
        self.player_x = 100
        self.player_speed = 8
        self.obstacles = []
        self.game_over = False
        self.score = 2
        self.best_combo = 2
        self.lives = 3
        self.frames = 0

    def snapshot(self):
        return {"player_x": self.player_x, "obstacles": []}

    def apply_action(self, action):
        if action == "right":
            self.player_x += self.player_speed
        elif action == "left":
            self.player_x -= self.player_speed

    def update(self):
        self.frames += 1

    def variant_stats_payload(self):
        return {"ore": {"spawned": 1, "avoided": 1, "hits": 0}}

    def score_breakdown_payload(self):
        return {"survival": 2, "ore_bonus": 5, "combo_bonus": 0, "ore_penalty": 0}


if __name__ == "__main__":
    unittest.main()
