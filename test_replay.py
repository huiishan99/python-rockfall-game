import json
import os
import tempfile
import unittest

from replay import (
    build_trace_payload,
    event_summary,
    finalize_trace,
    format_trace_lines,
    sanitize_trace_label,
    should_record_frame,
    trace_file_name,
    write_trace,
)


class ReplayTest(unittest.TestCase):
    def test_sanitize_trace_label_for_file_names(self):
        self.assertEqual(sanitize_trace_label("runs/model v1.pkl"), "runs-model-v1.pkl")
        self.assertEqual(sanitize_trace_label("///"), "run")

    def test_should_record_first_stride_and_event_frames(self):
        self.assertTrue(should_record_frame(1, 30))
        self.assertTrue(should_record_frame(30, 30))
        self.assertTrue(should_record_frame(7, 30, events=["hit"]))
        self.assertFalse(should_record_frame(7, 30))

    def test_finalize_trace_keeps_summary_result(self):
        trace = build_trace_payload("model.pkl", 0, 42, {"difficulty": "normal"})
        result = {
            "score": 5,
            "best_combo": 2,
            "frames": 300,
            "lives": 1,
            "timed_out": True,
            "variant_stats": {"ore": {"hits": 1}},
            "score_breakdown": {"ore_bonus": 5},
        }

        finalize_trace(trace, result)

        self.assertEqual(trace["result"]["score"], 5)
        self.assertEqual(trace["result"]["variant_stats"]["ore"]["hits"], 1)

    def test_write_trace_uses_sanitized_name(self):
        trace = build_trace_payload("runs/model v1.pkl", 1, 43, {})

        with tempfile.TemporaryDirectory() as temp_dir:
            path = write_trace(trace, temp_dir)

            self.assertTrue(path.endswith("runs-model-v1.pkl-game-2-seed-43.json"))
            with open(path, "r") as trace_file:
                self.assertEqual(json.load(trace_file)["seed"], 43)

    def test_trace_file_name_includes_game_and_seed(self):
        trace = build_trace_payload("model.pkl", 2, 44, {})

        self.assertEqual(trace_file_name(trace), "model.pkl-game-3-seed-44.json")

    def test_event_summary_counts_recorded_frame_events(self):
        trace = {
            "frames": [
                {"events": ["hit", "avoid"]},
                {"events": ["avoid"]},
            ]
        }

        self.assertEqual(event_summary(trace), {"avoid": 2, "hit": 1})

    def test_format_trace_lines_includes_key_frames(self):
        trace = build_trace_payload(
            "model.pkl",
            0,
            42,
            {
                "difficulty": "normal",
                "variant_profile": "variant-rich",
                "player_speed": 8,
                "initial_lives": 3,
                "max_frames": 300,
            },
        )
        trace["frames"].append(
            {
                "frame": 1,
                "action": "left",
                "player_x": 300,
                "score": 0,
                "lives": 3,
                "combo": 0,
                "events": ["avoid"],
                "obstacles": [{"variant": "ore", "x": 100, "y": 50}],
            }
        )
        finalize_trace(
            trace,
            {
                "score": 0,
                "best_combo": 0,
                "frames": 1,
                "lives": 3,
                "timed_out": True,
            },
        )

        lines = format_trace_lines(trace)

        self.assertIn("Rockfall replay trace", lines)
        self.assertTrue(any("Events: avoid=1" in line for line in lines))
        self.assertTrue(any("ore@(100,50)" in line for line in lines))


if __name__ == "__main__":
    unittest.main()
