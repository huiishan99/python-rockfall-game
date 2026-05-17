import unittest

from release_check import parse_args
from settings import PLAYER_SPEED


class ReleaseCheckTest(unittest.TestCase):
    def test_parse_args_defaults(self):
        args = parse_args([])

        self.assertEqual(args.games, 3)
        self.assertEqual(args.max_frames, 1800)
        self.assertEqual(args.difficulty, "normal")
        self.assertEqual(args.player_speed, PLAYER_SPEED)

    def test_parse_args_overrides(self):
        args = parse_args(["--games", "5", "--max-frames", "600", "--model", "alt.pkl"])

        self.assertEqual(args.games, 5)
        self.assertEqual(args.max_frames, 600)
        self.assertEqual(args.model, "alt.pkl")

    def test_parse_args_accepts_difficulty(self):
        args = parse_args(["--difficulty", "hard"])

        self.assertEqual(args.difficulty, "hard")

    def test_parse_args_accepts_player_speed(self):
        args = parse_args(["--player-speed", "8"])

        self.assertEqual(args.player_speed, 8)


if __name__ == "__main__":
    unittest.main()
