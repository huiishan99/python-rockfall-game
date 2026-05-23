import os
import json
import tempfile
import unittest

import joblib

from train_model import MODEL_FILE, load_data, parse_args, save_model


class TrainModelTest(unittest.TestCase):
    def test_parse_args_defaults_to_tracked_model(self):
        args = parse_args([])

        self.assertEqual(args.model, MODEL_FILE)

    def test_save_model_creates_parent_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = os.path.join(temp_dir, "models", "experiment.pkl")

            save_model({"model": "stub"}, model_path)

            self.assertEqual(joblib.load(model_path), {"model": "stub"})

    def test_load_data_builds_variant_effect_features(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_path = os.path.join(temp_dir, "data.json")
            with open(data_path, "w") as data_file:
                json.dump(
                    [{"state": {"player_x": 100, "obstacles": [[120, 40, "ore"]]}, "action": "right"}],
                    data_file,
                )

            X, y, skipped_entries = load_data(data_path)

        self.assertEqual(X.tolist(), [[100, 120, 40, 20, 0, 2]])
        self.assertEqual(y.tolist(), [1])
        self.assertEqual(skipped_entries, 0)


if __name__ == "__main__":
    unittest.main()
