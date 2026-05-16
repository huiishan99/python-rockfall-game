import argparse
import json
import os
import random

from evaluate_model import (
    DEFAULT_GAMES,
    DEFAULT_MAX_FRAMES,
    DEFAULT_RANDOM_SEED,
    build_summary_payload,
    run_game,
    summarize_results,
)
from play_with_model import MODEL_FILE


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Compare Rockfall models with the same headless evaluation seeds.")
    parser.add_argument("models", nargs="*", default=[MODEL_FILE], help="Model files to compare.")
    parser.add_argument("--games", type=int, default=DEFAULT_GAMES, help="Number of games per model.")
    parser.add_argument("--max-frames", type=int, default=DEFAULT_MAX_FRAMES, help="Frame limit per game.")
    parser.add_argument("--random-seed", type=int, default=DEFAULT_RANDOM_SEED, help="Base random seed.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of a table.")
    return parser.parse_args(argv)


def evaluate_model_path(model_path, games, max_frames, random_seed, screen):
    import joblib

    model = joblib.load(model_path)
    results = []
    for game_index in range(games):
        random.seed(random_seed + game_index)
        results.append(run_game(model, screen, max_frames))

    return summarize_results(results)


def build_comparison_payload(model_paths, summaries, max_frames, random_seed):
    return {
        "max_frames": max_frames,
        "random_seed": random_seed,
        "models": [
            build_summary_payload(model_path, summary)
            for model_path, summary in zip(model_paths, summaries)
        ],
    }


def format_comparison_table(model_paths, summaries):
    rows = [
        (
            "Model",
            "Avg Score",
            "Best",
            "Worst",
            "Avg Combo",
            "Best Combo",
            "Avg Frames",
            "Timeouts",
        )
    ]
    for model_path, summary in zip(model_paths, summaries):
        rows.append(
            (
                model_path,
                f"{summary['average_score']:.2f}",
                str(summary["best_score"]),
                str(summary["worst_score"]),
                f"{summary['average_best_combo']:.2f}",
                str(summary["best_combo"]),
                f"{summary['average_frames']:.1f}",
                str(summary["timeouts"]),
            )
        )

    widths = [max(len(row[index]) for row in rows) for index in range(len(rows[0]))]
    return [
        "  ".join(cell.ljust(widths[index]) for index, cell in enumerate(row))
        for row in rows
    ]


def main(argv=None):
    args = parse_args(argv)
    if args.games <= 0:
        raise ValueError("--games must be greater than zero.")
    if args.max_frames <= 0:
        raise ValueError("--max-frames must be greater than zero.")

    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame

    from settings import SCREEN_HEIGHT, SCREEN_WIDTH

    pygame.font.init()
    screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    summaries = [
        evaluate_model_path(model_path, args.games, args.max_frames, args.random_seed, screen)
        for model_path in args.models
    ]
    pygame.quit()

    if args.json:
        payload = build_comparison_payload(args.models, summaries, args.max_frames, args.random_seed)
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for line in format_comparison_table(args.models, summaries):
            print(line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
