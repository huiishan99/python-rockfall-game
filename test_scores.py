import json
import os
import tempfile
import unittest

from scores import get_high_score, load_high_scores, record_high_score


class ScoreStorageTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.score_path = os.path.join(self.temp_dir.name, "high_scores.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_missing_file_returns_zero(self):
        self.assertEqual(get_high_score("manual", self.score_path), 0)

    def test_records_new_high_score(self):
        high_score, changed = record_high_score("manual", 12, self.score_path)

        self.assertTrue(changed)
        self.assertEqual(high_score, 12)
        self.assertEqual(get_high_score("manual", self.score_path), 12)

    def test_lower_score_does_not_overwrite_high_score(self):
        record_high_score("manual", 12, self.score_path)
        high_score, changed = record_high_score("manual", 8, self.score_path)

        self.assertFalse(changed)
        self.assertEqual(high_score, 12)
        self.assertEqual(get_high_score("manual", self.score_path), 12)

    def test_scores_are_tracked_per_mode(self):
        record_high_score("manual", 12, self.score_path)
        record_high_score("model", 6, self.score_path)

        self.assertEqual(get_high_score("manual", self.score_path), 12)
        self.assertEqual(get_high_score("model", self.score_path), 6)

    def test_invalid_score_file_is_ignored(self):
        with open(self.score_path, "w") as f:
            f.write("not-json")

        self.assertEqual(load_high_scores(self.score_path), {})

    def test_invalid_entries_are_skipped(self):
        with open(self.score_path, "w") as f:
            json.dump({"manual": "15", "model": "bad"}, f)

        self.assertEqual(load_high_scores(self.score_path), {"manual": 15})


if __name__ == "__main__":
    unittest.main()
