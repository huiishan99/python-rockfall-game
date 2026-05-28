import json
import os
import tempfile
import unittest

from leaderboard import (
    append_report_to_leaderboard,
    build_entry,
    empty_leaderboard,
    format_leaderboard_lines,
    load_leaderboard,
    normalize_report_entries,
    ranked_entries,
    save_leaderboard,
    upsert_entries,
)


MODEL_RESULT = {
    "model": "game_model.pkl",
    "games": 2,
    "average_score": 5,
    "best_score": 7,
    "worst_score": 3,
    "average_frames": 200,
    "average_lives_left": 1,
    "survival_rate": 0.5,
    "average_best_combo": 3,
    "best_combo": 4,
    "timeouts": 1,
    "score_breakdown": {
        "survival": {"average": 12},
        "ore_bonus": {"average": 5},
        "ore_penalty": {"average": 2},
    },
}


class LeaderboardTest(unittest.TestCase):
    def test_build_entry_extracts_settings_and_score_breakdown(self):
        entry = build_entry(
            MODEL_RESULT,
            {
                "max_frames": 300,
                "random_seed": 42,
                "difficulty": "normal",
                "player_speed": 8,
                "initial_lives": 3,
                "variant_profile": "variant-rich",
            },
            "comparison",
            source_report="runs/comparison.json",
            tag="smoke",
            created_at="2026-05-28T00:00:00+00:00",
        )

        self.assertEqual(entry["model"], "game_model.pkl")
        self.assertEqual(entry["average_ore_bonus"], 5)
        self.assertEqual(entry["average_ore_penalty"], 2)
        self.assertEqual(entry["variant_profile"], "variant-rich")
        self.assertEqual(entry["tag"], "smoke")
        self.assertIn("id", entry)

    def test_normalizes_evaluation_report(self):
        payload = {
            **MODEL_RESULT,
            "max_frames": 300,
            "random_seed": 42,
            "difficulty": "hard",
            "player_speed": 9,
            "initial_lives": 4,
            "variant_profile": "standard",
        }

        entries = normalize_report_entries(payload, source_report="runs/eval.json")

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["source_kind"], "evaluation")
        self.assertEqual(entries[0]["difficulty"], "hard")

    def test_normalizes_comparison_report(self):
        payload = {
            "max_frames": 300,
            "random_seed": 42,
            "difficulty": "normal",
            "player_speed": 8,
            "initial_lives": 3,
            "variant_profile": "variant-rich",
            "models": [MODEL_RESULT, {**MODEL_RESULT, "model": "policy:ore-hunter", "average_score": 9}],
        }

        entries = normalize_report_entries(payload)

        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[1]["model"], "policy:ore-hunter")
        self.assertEqual(entries[1]["source_kind"], "comparison")

    def test_normalizes_training_pipeline_report(self):
        payload = {
            "comparison": {
                "max_frames": 300,
                "random_seed": 42,
                "difficulty": "normal",
                "player_speed": 8,
                "initial_lives": 3,
                "variant_profile": "variant-rich",
                "models": [MODEL_RESULT],
            }
        }

        entries = normalize_report_entries(payload)

        self.assertEqual(entries[0]["source_kind"], "training_pipeline")

    def test_normalizes_model_report_profiles(self):
        payload = {
            "settings": {
                "games": 2,
                "max_frames": 300,
                "random_seed": 42,
                "difficulty": "normal",
                "player_speed": 8,
                "initial_lives": 3,
            },
            "profiles": {
                "standard": {"models": [MODEL_RESULT]},
                "variant-rich": {"models": [{**MODEL_RESULT, "average_score": 9}]},
            },
        }

        entries = normalize_report_entries(payload)

        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["variant_profile"], "standard")
        self.assertEqual(entries[0]["max_frames"], 300)
        self.assertEqual(entries[1]["source_kind"], "model_report")

    def test_upsert_entries_replaces_matching_id_and_sorts(self):
        leaderboard = empty_leaderboard()
        low = build_entry({**MODEL_RESULT, "average_score": 3}, {}, "test", created_at="now")
        high = build_entry({**MODEL_RESULT, "model": "candidate.pkl", "average_score": 9}, {}, "test", created_at="now")

        upsert_entries(leaderboard, [low, high])
        upsert_entries(leaderboard, [{**low, "average_score": 4}])

        self.assertEqual(len(leaderboard["entries"]), 2)
        self.assertEqual(leaderboard["entries"][0]["model"], "candidate.pkl")
        self.assertEqual(leaderboard["entries"][1]["average_score"], 4)

    def test_ranked_entries_uses_score_first(self):
        entries = [
            {"model": "a", "average_score": 1, "survival_rate": 1},
            {"model": "b", "average_score": 2, "survival_rate": 0},
        ]

        self.assertEqual(ranked_entries(entries)[0]["model"], "b")

    def test_save_and_load_leaderboard(self):
        leaderboard = {"schema_version": 1, "entries": [{"id": "abc"}]}
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "nested", "leaderboard.json")

            save_leaderboard(leaderboard, path)

            self.assertEqual(load_leaderboard(path), leaderboard)

    def test_append_report_to_leaderboard_writes_entries(self):
        payload = {
            **MODEL_RESULT,
            "max_frames": 300,
            "random_seed": 42,
            "difficulty": "normal",
            "player_speed": 8,
            "initial_lives": 3,
            "variant_profile": "standard",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = os.path.join(temp_dir, "leaderboard.json")

            leaderboard, entries = append_report_to_leaderboard(
                payload,
                leaderboard_path=path,
                source_report="runs/eval.json",
                tag="smoke",
                created_at="2026-05-28T00:00:00+00:00",
            )

            self.assertEqual(len(entries), 1)
            self.assertEqual(len(leaderboard["entries"]), 1)
            with open(path, "r") as leaderboard_file:
                self.assertEqual(json.load(leaderboard_file)["entries"][0]["tag"], "smoke")

    def test_format_leaderboard_lines(self):
        leaderboard = empty_leaderboard()
        entry = build_entry(MODEL_RESULT, {"variant_profile": "standard"}, "evaluation", created_at="now")
        upsert_entries(leaderboard, [entry])

        lines = format_leaderboard_lines(leaderboard)

        self.assertIn("Model", lines[0])
        self.assertTrue(any("game_model.pkl" in line for line in lines))


if __name__ == "__main__":
    unittest.main()
