import unittest

from evaluate_model import format_summary_lines, summarize_results


class EvaluateModelTest(unittest.TestCase):
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
        self.assertEqual(summary["timeouts"], 1)

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
                "timeouts": 1,
            },
            games_label="Evaluation games",
        )

        self.assertEqual(lines[0], "Evaluation games: 2")
        self.assertIn("Average best combo: 4.00", lines)
        self.assertIn("Timed out games: 1", lines)


if __name__ == "__main__":
    unittest.main()
