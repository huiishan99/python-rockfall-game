import unittest

from evaluate_model import summarize_results


class EvaluateModelTest(unittest.TestCase):
    def test_summarizes_scores_and_timeouts(self):
        summary = summarize_results(
            [
                {"score": 3, "frames": 100, "lives": 0, "timed_out": False},
                {"score": 7, "frames": 200, "lives": 2, "timed_out": True},
            ]
        )

        self.assertEqual(summary["games"], 2)
        self.assertEqual(summary["average_score"], 5)
        self.assertEqual(summary["best_score"], 7)
        self.assertEqual(summary["worst_score"], 3)
        self.assertEqual(summary["average_frames"], 150)
        self.assertEqual(summary["timeouts"], 1)


if __name__ == "__main__":
    unittest.main()
