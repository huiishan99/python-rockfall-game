import sys
import unittest

from features import FEATURE_NAMES, SINGLE_OBSTACLE_FEATURE_NAMES
from play_with_model import (
    MODEL_FILE,
    MODE_KEY,
    manual_play_command,
    model_load_error_message,
    model_debug_lines,
    model_mode_name,
    parse_args,
    predict_action,
    predict_action_with_debug,
)


class PlayWithModelTest(unittest.TestCase):
    def test_parse_args_defaults_to_tracked_model(self):
        args = parse_args([])

        self.assertEqual(args.model, MODEL_FILE)
        self.assertEqual(args.difficulty, "normal")

    def test_model_high_score_key_tracks_ore_score_rules(self):
        self.assertEqual(MODE_KEY, "model_ore_score")

    def test_parse_args_accepts_difficulty_preset(self):
        args = parse_args(["--difficulty", "easy"])

        self.assertEqual(args.difficulty, "easy")

    def test_parse_args_accepts_player_speed(self):
        args = parse_args(["--player-speed", "8"])

        self.assertEqual(args.player_speed, 8)

    def test_parse_args_accepts_lives(self):
        args = parse_args(["--lives", "3"])

        self.assertEqual(args.lives, 3)

    def test_parse_args_accepts_variant_profile(self):
        args = parse_args(["--variant-profile", "variant-rich"])

        self.assertEqual(args.variant_profile, "variant-rich")

    def test_parse_args_accepts_debug_ai(self):
        args = parse_args(["--debug-ai"])

        self.assertTrue(args.debug_ai)

    def test_model_mode_name_uses_basename(self):
        mode_name = model_mode_name("experiments/alt_model.pkl")

        self.assertEqual(mode_name, "Model Play (alt_model.pkl)")

    def test_model_mode_name_can_include_difficulty(self):
        mode_name = model_mode_name("experiments/alt_model.pkl", "hard")

        self.assertEqual(mode_name, "Model Play (alt_model.pkl, hard)")

    def test_model_mode_name_can_include_variant_profile(self):
        mode_name = model_mode_name("experiments/alt_model.pkl", "hard", "variant-rich")

        self.assertEqual(mode_name, "Model Play (alt_model.pkl, hard, variant-rich)")

    def test_model_load_error_message_includes_path_and_error(self):
        message = model_load_error_message("missing.pkl", FileNotFoundError("not found"))

        self.assertIn("missing.pkl", message)
        self.assertIn("not found", message)

    def test_manual_play_command_preserves_tuning_args(self):
        args = parse_args(
            [
                "--difficulty",
                "hard",
                "--player-speed",
                "8",
                "--lives",
                "3",
                "--variant-profile",
                "variant-rich",
                "--mute",
            ]
        )

        command = manual_play_command(args)

        self.assertEqual(command[0], sys.executable)
        self.assertIn("game.py", command)
        self.assertIn("hard", command)
        self.assertIn("8", command)
        self.assertIn("3", command)
        self.assertIn("variant-rich", command)
        self.assertIn("--mute", command)

    def test_predict_action_adapts_features_for_legacy_model(self):
        model = RecordingModel(n_features_in=4, prediction=1)
        game = StubGame([200, 260, 300, 60, 0, 5, 150, 100, -50, 0, 0, 200, 0, 0, 0, 0])

        action = predict_action(model, game)

        self.assertEqual(action, "right")
        self.assertEqual(model.seen_features, [200, 260, 300, 60])

    def test_predict_action_with_debug_returns_raw_and_model_features(self):
        features = [200, 260, 300, 60, 0, 5, 150, 100, -50, 0, 0, 200, 0, 0, 0, 0]
        model = RecordingModel(n_features_in=6, prediction=1)
        game = StubGame(features)

        action, raw_features, model_features = predict_action_with_debug(model, game)

        self.assertEqual(action, "right")
        self.assertEqual(raw_features, features)
        self.assertEqual(model_features, features[:6])

    def test_predict_action_adapts_features_for_single_obstacle_model(self):
        features = [200, 260, 300, 60, 0, 5, 150, 100, -50, 0, 0, 200, 0, 0, 0, 0]
        model = RecordingModel(n_features_in=len(SINGLE_OBSTACLE_FEATURE_NAMES), prediction=0)
        game = StubGame(features)

        action = predict_action(model, game)

        self.assertEqual(action, "left")
        self.assertEqual(model.seen_features, features[: len(SINGLE_OBSTACLE_FEATURE_NAMES)])

    def test_predict_action_uses_multi_obstacle_features_for_current_model(self):
        features = [200, 260, 300, 60, 0, 5, 150, 100, -50, 0, 0, 200, 0, 0, 0, 0]
        model = RecordingModel(n_features_in=len(FEATURE_NAMES), prediction=0)
        game = StubGame(features)

        action = predict_action(model, game)

        self.assertEqual(action, "left")
        self.assertEqual(model.seen_features, features)

    def test_model_debug_lines_show_action_feature_counts_and_rocks(self):
        lines = model_debug_lines("left", [200, 260, 300, 60, 0, 5, 150, 100, -50, 0, 0], [200, 260, 300, 60])

        self.assertEqual(lines[0], "AI: LEFT")
        self.assertEqual(lines[1], "Features: 4/11")
        self.assertIn("near: dx=60 y=300 sp=0 +5", lines)
        self.assertIn("second: dx=-50 y=100 sp=0 +0", lines)


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
