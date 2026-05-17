import unittest

from play_with_model import MODEL_FILE, model_load_error_message, model_mode_name, parse_args


class PlayWithModelTest(unittest.TestCase):
    def test_parse_args_defaults_to_tracked_model(self):
        args = parse_args([])

        self.assertEqual(args.model, MODEL_FILE)
        self.assertEqual(args.difficulty, "normal")

    def test_parse_args_accepts_difficulty_preset(self):
        args = parse_args(["--difficulty", "easy"])

        self.assertEqual(args.difficulty, "easy")

    def test_model_mode_name_uses_basename(self):
        mode_name = model_mode_name("experiments/alt_model.pkl")

        self.assertEqual(mode_name, "Model Play (alt_model.pkl)")

    def test_model_mode_name_can_include_difficulty(self):
        mode_name = model_mode_name("experiments/alt_model.pkl", "hard")

        self.assertEqual(mode_name, "Model Play (alt_model.pkl, hard)")

    def test_model_load_error_message_includes_path_and_error(self):
        message = model_load_error_message("missing.pkl", FileNotFoundError("not found"))

        self.assertIn("missing.pkl", message)
        self.assertIn("not found", message)


if __name__ == "__main__":
    unittest.main()
