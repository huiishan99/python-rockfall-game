import unittest

from data_store import ORE_TARGET_DATA_FILE
from game import MODE_KEY, manual_mode_name, model_play_command, parse_args
from play_with_model import MODEL_FILE


class GameEntrypointTest(unittest.TestCase):
    def test_parse_args_defaults_to_tracked_data_file(self):
        args = parse_args([])

        self.assertEqual(args.data, ORE_TARGET_DATA_FILE)

    def test_manual_high_score_key_tracks_ore_score_rules(self):
        self.assertEqual(MODE_KEY, "manual_ore_score")

    def test_parse_args_accepts_data_file_override(self):
        args = parse_args(["--data", "runs/experiment.json"])

        self.assertEqual(args.data, "runs/experiment.json")

    def test_parse_args_accepts_difficulty_preset(self):
        args = parse_args(["--difficulty", "hard"])

        self.assertEqual(args.difficulty, "hard")

    def test_parse_args_accepts_player_speed(self):
        args = parse_args(["--player-speed", "8"])

        self.assertEqual(args.player_speed, 8)

    def test_parse_args_accepts_lives(self):
        args = parse_args(["--lives", "3"])

        self.assertEqual(args.lives, 3)

    def test_parse_args_accepts_variant_profile(self):
        args = parse_args(["--variant-profile", "variant-rich"])

        self.assertEqual(args.variant_profile, "variant-rich")

    def test_manual_mode_name_shows_non_default_variant_profile(self):
        self.assertEqual(manual_mode_name("hard", "variant-rich"), "Data Collection (hard, variant-rich)")

    def test_model_play_command_preserves_tuning_args(self):
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

        command = model_play_command(args)

        self.assertIn("play_with_model.py", command)
        self.assertIn(MODEL_FILE, command)
        self.assertIn("hard", command)
        self.assertIn("8", command)
        self.assertIn("3", command)
        self.assertIn("variant-rich", command)
        self.assertIn("--mute", command)


if __name__ == "__main__":
    unittest.main()
