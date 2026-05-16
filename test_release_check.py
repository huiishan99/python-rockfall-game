import unittest

from release_check import parse_args


class ReleaseCheckTest(unittest.TestCase):
    def test_parse_args_defaults(self):
        args = parse_args([])

        self.assertEqual(args.games, 3)
        self.assertEqual(args.max_frames, 1800)

    def test_parse_args_overrides(self):
        args = parse_args(["--games", "5", "--max-frames", "600", "--model", "alt.pkl"])

        self.assertEqual(args.games, 5)
        self.assertEqual(args.max_frames, 600)
        self.assertEqual(args.model, "alt.pkl")


if __name__ == "__main__":
    unittest.main()
