import argparse
import os
import random
import unittest

from evaluate_model import DEFAULT_RANDOM_SEED, MODEL_FILE, run_game, summarize_results
from settings import VERSION

DEFAULT_GAMES = 3
DEFAULT_MAX_FRAMES = 1800


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run the v0.1 release readiness checks.")
    parser.add_argument("--model", default=MODEL_FILE, help="Model file to evaluate.")
    parser.add_argument("--games", type=int, default=DEFAULT_GAMES, help="Number of evaluation games.")
    parser.add_argument("--max-frames", type=int, default=DEFAULT_MAX_FRAMES, help="Frame limit per game.")
    parser.add_argument("--random-seed", type=int, default=DEFAULT_RANDOM_SEED, help="Base random seed.")
    return parser.parse_args(argv)


def run_unittests():
    suite = unittest.defaultTestLoader.discover(".")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    return result.wasSuccessful()


def run_evaluation(model_path, games, max_frames, random_seed):
    import joblib

    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame

    from settings import SCREEN_HEIGHT, SCREEN_WIDTH

    pygame.font.init()
    screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    model = joblib.load(model_path)

    results = []
    for game_index in range(games):
        random.seed(random_seed + game_index)
        results.append(run_game(model, screen, max_frames))

    pygame.quit()
    return summarize_results(results)


def print_evaluation_summary(summary):
    print(f"Evaluation games: {summary['games']}")
    print(f"Average score: {summary['average_score']:.2f}")
    print(f"Best score: {summary['best_score']}")
    print(f"Worst score: {summary['worst_score']}")
    print(f"Average frames: {summary['average_frames']:.1f}")
    print(f"Timed out games: {summary['timeouts']}")


def main(argv=None):
    args = parse_args(argv)
    if args.games <= 0:
        raise ValueError("--games must be greater than zero.")
    if args.max_frames <= 0:
        raise ValueError("--max-frames must be greater than zero.")

    print(f"Rockfall {VERSION} release check")
    print("Running unit tests...")
    tests_ok = run_unittests()
    if not tests_ok:
        print("Release check failed: unit tests failed.")
        return 1

    print("Running model evaluation...")
    summary = run_evaluation(args.model, args.games, args.max_frames, args.random_seed)
    print_evaluation_summary(summary)

    print("Release check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
