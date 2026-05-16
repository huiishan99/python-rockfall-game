import unittest

from play_with_model import MODEL_FILE, model_mode_name, parse_args


class PlayWithModelTest(unittest.TestCase):
    def test_parse_args_defaults_to_tracked_model(self):
        args = parse_args([])

        self.assertEqual(args.model, MODEL_FILE)

    def test_model_mode_name_uses_basename(self):
        mode_name = model_mode_name("experiments/alt_model.pkl")

        self.assertEqual(mode_name, "Model Play (alt_model.pkl)")


if __name__ == "__main__":
    unittest.main()
