import json
import os
import tempfile
import unittest

from data_quality import action_balance_payload, inspect_data_file


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
        self.assertEqual(summary["data_quality"]["status"], "ready")


if __name__ == "__main__":
    unittest.main()
