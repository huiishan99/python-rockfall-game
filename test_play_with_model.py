import sys
import unittest

from play_with_model import (
    MODEL_FILE,
    manual_play_command,
    model_load_error_message,
    model_mode_name,
    parse_args,
    predict_action,
)


class PlayWithModelTest(unittest.TestCase):
    def test_parse_args_defaults_to_tracked_model(self):
        args = parse_args([])

        self.assertEqual(args.model, MODEL_FILE)
        self.assertEqual(args.difficulty, "normal")

    def test_parse_args_accepts_difficulty_preset(self):
        args = parse_args(["--difficulty", "easy"])

        self.assertEqual(args.difficulty, "easy")

    def test_parse_args_accepts_player_speed(self):
        args = parse_args(["--player-speed", "8"])

        self.assertEqual(args.player_speed, 8)

    def test_parse_args_accepts_lives(self):
        args = parse_args(["--lives", "3"])

        self.assertEqual(args.lives, 3)

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

    def test_manual_play_command_preserves_tuning_args(self):
        args = parse_args(["--difficulty", "hard", "--player-speed", "8", "--lives", "3", "--mute"])

        command = manual_play_command(args)

        self.assertEqual(command[0], sys.executable)
        self.assertIn("game.py", command)
        self.assertIn("hard", command)
        self.assertIn("8", command)
        self.assertIn("3", command)
        self.assertIn("--mute", command)

    def test_predict_action_adapts_features_for_legacy_model(self):
        model = RecordingModel(n_features_in=4, prediction=1)
        game = StubGame([200, 260, 300, 60, 0, 2])

        action = predict_action(model, game)

        self.assertEqual(action, "right")
        self.assertEqual(model.seen_features, [200, 260, 300, 60])

    def test_predict_action_uses_variant_features_for_current_model(self):
        features = [200, 260, 300, 60, 0, 2]
        model = RecordingModel(n_features_in=6, prediction=0)
        game = StubGame(features)

        action = predict_action(model, game)

        self.assertEqual(action, "left")
        self.assertEqual(model.seen_features, features)


class StubGame:
    def __init__(self, features):
        self.features = features

    def model_features(self):
        return self.features


class RecordingModel:
    def __init__(self, n_features_in, prediction):
        self.n_features_in_ = n_features_in
        self.prediction = prediction
        self.seen_features = None

    def predict(self, rows):
        self.seen_features = rows[0]
        return [self.prediction]


if __name__ == "__main__":
    unittest.main()
