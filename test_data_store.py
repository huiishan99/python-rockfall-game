import json
import os
import tempfile
import unittest

from data_store import ORE_TARGET_OBJECTIVE, build_game_data_entry, append_game_data, load_game_data


class GameDataStoreTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_path = os.path.join(self.temp_dir.name, "game_data.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_missing_file_loads_as_empty_list(self):
        self.assertEqual(load_game_data(self.data_path), [])

    def test_append_creates_new_file(self):
        entry = {"state": {"player_x": 10, "obstacles": []}, "action": "left"}

        previous_count, total_count = append_game_data([entry], self.data_path)

        self.assertEqual(previous_count, 0)
        self.assertEqual(total_count, 1)
        self.assertEqual(load_game_data(self.data_path), [entry])

    def test_build_game_data_entry_tags_ore_target_objective(self):
        entry = build_game_data_entry({"player_x": 10, "obstacles": []}, "left", source="manual")

        self.assertEqual(entry["objective"], ORE_TARGET_OBJECTIVE)
        self.assertEqual(entry["source"], "manual")

    def test_append_creates_parent_directory(self):
        nested_path = os.path.join(self.temp_dir.name, "runs", "experiment.json")
        entry = {"state": {"player_x": 10, "obstacles": []}, "action": "left"}

        previous_count, total_count = append_game_data([entry], nested_path)

        self.assertEqual(previous_count, 0)
        self.assertEqual(total_count, 1)
        self.assertEqual(load_game_data(nested_path), [entry])

    def test_append_preserves_existing_entries(self):
        old_entry = {"state": {"player_x": 10, "obstacles": []}, "action": "left"}
        new_entry = {"state": {"player_x": 20, "obstacles": []}, "action": "right"}
        with open(self.data_path, "w") as f:
            json.dump([old_entry], f)

        previous_count, total_count = append_game_data([new_entry], self.data_path)

        self.assertEqual(previous_count, 1)
        self.assertEqual(total_count, 2)
        self.assertEqual(load_game_data(self.data_path), [old_entry, new_entry])

    def test_invalid_json_raises_without_overwrite(self):
        with open(self.data_path, "w") as f:
            f.write("not-json")

        with self.assertRaises(ValueError):
            append_game_data([{"action": "left"}], self.data_path)

        with open(self.data_path, "r") as f:
            self.assertEqual(f.read(), "not-json")

    def test_non_list_json_raises(self):
        with open(self.data_path, "w") as f:
            json.dump({"not": "a list"}, f)

        with self.assertRaises(ValueError):
            load_game_data(self.data_path)


if __name__ == "__main__":
    unittest.main()
