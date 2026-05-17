import unittest

from data_store import GAME_DATA_FILE
from game import parse_args


class GameEntrypointTest(unittest.TestCase):
    def test_parse_args_defaults_to_tracked_data_file(self):
        args = parse_args([])

        self.assertEqual(args.data, GAME_DATA_FILE)

    def test_parse_args_accepts_data_file_override(self):
        args = parse_args(["--data", "runs/experiment.json"])

        self.assertEqual(args.data, "runs/experiment.json")

    def test_parse_args_accepts_difficulty_preset(self):
        args = parse_args(["--difficulty", "hard"])

        self.assertEqual(args.difficulty, "hard")

    def test_parse_args_accepts_player_speed(self):
        args = parse_args(["--player-speed", "8"])

        self.assertEqual(args.player_speed, 8)


if __name__ == "__main__":
    unittest.main()
