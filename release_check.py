import argparse
import os
import random
import sys
import unittest

from evaluate_model import (
    DEFAULT_RANDOM_SEED,
    MODEL_FILE,
    build_summary_payload,
    format_summary_lines,
    run_game,
    summarize_results,
    write_summary_report,
)
from difficulty import DEFAULT_DIFFICULTY_PRESET, difficulty_preset_names
from settings import INITIAL_LIVES, PLAYER_SPEED, VERSION

DEFAULT_GAMES = 3
DEFAULT_MAX_FRAMES = 1800


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run Rockfall release readiness checks.")
    parser.add_argument("--model", default=MODEL_FILE, help="Model file to evaluate.")
    parser.add_argument("--games", type=int, default=DEFAULT_GAMES, help="Number of evaluation games.")
    parser.add_argument("--max-frames", type=int, default=DEFAULT_MAX_FRAMES, help="Frame limit per game.")
    parser.add_argument("--random-seed", type=int, default=DEFAULT_RANDOM_SEED, help="Base random seed.")
    parser.add_argument(
        "--difficulty",
        choices=difficulty_preset_names(),
        default=DEFAULT_DIFFICULTY_PRESET,
        help="Difficulty preset.",
    )
    parser.add_argument("--player-speed", type=int, default=PLAYER_SPEED, help="Player movement speed in pixels.")
    parser.add_argument("--lives", type=int, default=INITIAL_LIVES, help="Initial player lives.")
    parser.add_argument("--report", help="Optional JSON release-check report file to write.")
    return parser.parse_args(argv)


def run_unittests():
    suite = unittest.defaultTestLoader.discover(".")
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=1).run(suite)
    return result.wasSuccessful()


def run_evaluation(
    model_path,
    games,
    max_frames,
    random_seed,
    difficulty_preset=DEFAULT_DIFFICULTY_PRESET,
    player_speed=PLAYER_SPEED,
    initial_lives=INITIAL_LIVES,
):
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
        results.append(
            run_game(
                model,
                screen,
                max_frames,
                difficulty_preset=difficulty_preset,
                player_speed=player_speed,
                initial_lives=initial_lives,
            )
        )

    pygame.quit()
    return summarize_results(results)


def print_evaluation_summary(summary):
    for line in format_summary_lines(summary, games_label="Evaluation games"):
        print(line)


def build_release_payload(
    model_path,
    summary=None,
    max_frames=None,
    random_seed=None,
    difficulty_preset=None,
    player_speed=None,
    initial_lives=None,
    tests_passed=True,
):
    payload = {
        "version": VERSION,
        "unit_tests": {"passed": tests_passed},
    }
    if summary is not None:
        payload["evaluation"] = build_summary_payload(
            model_path,
            summary,
            max_frames=max_frames,
            random_seed=random_seed,
            difficulty_preset=difficulty_preset,
            player_speed=player_speed,
            initial_lives=initial_lives,
        )
    return payload


def main(argv=None):
    args = parse_args(argv)
    if args.games <= 0:
        raise ValueError("--games must be greater than zero.")
    if args.max_frames <= 0:
        raise ValueError("--max-frames must be greater than zero.")
    if args.player_speed <= 0:
        raise ValueError("--player-speed must be greater than zero.")
    if args.lives <= 0:
        raise ValueError("--lives must be greater than zero.")

    print(f"Rockfall {VERSION} release check")
    sys.stdout.flush()
    print("Running unit tests...")
    sys.stdout.flush()
    tests_ok = run_unittests()
    if not tests_ok:
        print("Release check failed: unit tests failed.")
        if args.report:
            write_summary_report(build_release_payload(args.model, tests_passed=False), args.report)
            print(f"Report saved to {args.report}")
        return 1

    print("Running model evaluation...")
    sys.stdout.flush()
    summary = run_evaluation(
        args.model,
        args.games,
        args.max_frames,
        args.random_seed,
        args.difficulty,
        args.player_speed,
        args.lives,
    )
    print(f"Difficulty: {args.difficulty}")
    print(f"Player speed: {args.player_speed}")
    print(f"Initial lives: {args.lives}")
    print_evaluation_summary(summary)
    if args.report:
        payload = build_release_payload(
            args.model,
            summary,
            max_frames=args.max_frames,
            random_seed=args.random_seed,
            difficulty_preset=args.difficulty,
            player_speed=args.player_speed,
            initial_lives=args.lives,
            tests_passed=True,
        )
        write_summary_report(payload, args.report)
        print(f"Report saved to {args.report}")

    print("Release check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
