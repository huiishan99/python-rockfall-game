import unittest

from compare_models import build_comparison_payload, format_comparison_table, parse_args
from play_with_model import MODEL_FILE


SUMMARY_A = {
    "games": 2,
    "average_score": 5,
    "best_score": 7,
    "worst_score": 3,
    "average_best_combo": 4,
    "best_combo": 6,
    "average_frames": 150,
    "timeouts": 1,
}

SUMMARY_B = {
    "games": 2,
    "average_score": 8,
    "best_score": 10,
    "worst_score": 6,
    "average_best_combo": 5,
    "best_combo": 8,
    "average_frames": 180,
    "timeouts": 0,
}


class CompareModelsTest(unittest.TestCase):
    def test_parse_args_defaults_to_tracked_model(self):
        args = parse_args([])

        self.assertEqual(args.models, [MODEL_FILE])

    def test_parse_args_accepts_multiple_models_and_json(self):
        args = parse_args(["base.pkl", "candidate.pkl", "--json"])

        self.assertEqual(args.models, ["base.pkl", "candidate.pkl"])
        self.assertTrue(args.json)

    def test_formats_comparison_table(self):
        lines = format_comparison_table(["base.pkl", "candidate.pkl"], [SUMMARY_A, SUMMARY_B])

        self.assertIn("Model", lines[0])
        self.assertIn("Avg Score", lines[0])
        self.assertIn("base.pkl", lines[1])
        self.assertIn("5.00", lines[1])
        self.assertIn("candidate.pkl", lines[2])
        self.assertIn("8.00", lines[2])

    def test_builds_comparison_payload(self):
        payload = build_comparison_payload(
            ["base.pkl", "candidate.pkl"],
            [SUMMARY_A, SUMMARY_B],
            max_frames=300,
            random_seed=42,
        )

        self.assertEqual(payload["max_frames"], 300)
        self.assertEqual(payload["random_seed"], 42)
        self.assertEqual(payload["models"][0]["model"], "base.pkl")
        self.assertEqual(payload["models"][1]["average_score"], 8)


if __name__ == "__main__":
    unittest.main()
