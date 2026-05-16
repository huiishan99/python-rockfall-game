import os
import tempfile
import unittest

import joblib

from train_model import MODEL_FILE, parse_args, save_model


class TrainModelTest(unittest.TestCase):
    def test_parse_args_defaults_to_tracked_model(self):
        args = parse_args([])

        self.assertEqual(args.model, MODEL_FILE)

    def test_save_model_creates_parent_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = os.path.join(temp_dir, "models", "experiment.pkl")

            save_model({"model": "stub"}, model_path)

            self.assertEqual(joblib.load(model_path), {"model": "stub"})


if __name__ == "__main__":
    unittest.main()
