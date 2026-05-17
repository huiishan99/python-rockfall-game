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
from difficulty import DEFAULT_DIFFICULTY_PRESET, difficulty_preset_names
from play_with_model import MODEL_FILE
from settings import INITIAL_LIVES, PLAYER_SPEED


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Compare Rockfall models with the same headless evaluation seeds.")
    parser.add_argument("models", nargs="*", default=[MODEL_FILE], help="Model files to compare.")
    parser.add_argument("--games", type=int, default=DEFAULT_GAMES, help="Number of games per model.")
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
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of a table.")
    return parser.parse_args(argv)


def validate_model_paths(model_paths):
    missing_paths = [model_path for model_path in model_paths if not os.path.exists(model_path)]
    if missing_paths:
        raise ValueError("Model file not found: " + ", ".join(missing_paths))


def evaluate_model_path(
    model_path,
    games,
    max_frames,
    random_seed,
    screen,
    difficulty_preset=DEFAULT_DIFFICULTY_PRESET,
    player_speed=PLAYER_SPEED,
    initial_lives=INITIAL_LIVES,
):
    import joblib

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

    return summarize_results(results)


def build_comparison_payload(
    model_paths,
    summaries,
    max_frames,
    random_seed,
    difficulty_preset=None,
    player_speed=None,
    initial_lives=None,
):
    baseline_summary = summaries[0]
    return {
        "max_frames": max_frames,
        "random_seed": random_seed,
        "difficulty": difficulty_preset,
        "player_speed": player_speed,
        "initial_lives": initial_lives,
        "best_model": comparison_winner(model_paths, summaries),
        "models": [
            {
                **build_summary_payload(
                    model_path,
                    summary,
                    difficulty_preset=difficulty_preset,
                    player_speed=player_speed,
                    initial_lives=initial_lives,
                ),
                "score_delta": score_delta(summary, baseline_summary),
            }
            for model_path, summary in zip(model_paths, summaries)
        ],
    }


def score_delta(summary, baseline_summary):
    return summary["average_score"] - baseline_summary["average_score"]


def comparison_winner(model_paths, summaries):
    best_index = max(
        range(len(summaries)),
        key=lambda index: (
            summaries[index]["average_score"],
            summaries[index]["average_best_combo"],
            summaries[index]["average_frames"],
        ),
    )
    return model_paths[best_index]


def format_comparison_table(model_paths, summaries):
    baseline_summary = summaries[0]
    rows = [
        (
            "Model",
            "Avg Score",
            "Score Delta",
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
                f"{score_delta(summary, baseline_summary):+.2f}",
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


def format_comparison_lines(model_paths, summaries):
    return (
        format_comparison_table(model_paths, summaries)
        + [f"Best model by average score: {comparison_winner(model_paths, summaries)}"]
    )


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
    validate_model_paths(args.models)

    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame

    from settings import SCREEN_HEIGHT, SCREEN_WIDTH

    pygame.font.init()
    screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    summaries = [
        evaluate_model_path(
            model_path,
            args.games,
            args.max_frames,
            args.random_seed,
            screen,
            difficulty_preset=args.difficulty,
            player_speed=args.player_speed,
            initial_lives=args.lives,
        )
        for model_path in args.models
    ]
    pygame.quit()

    if args.json:
        payload = build_comparison_payload(
            args.models,
            summaries,
            args.max_frames,
            args.random_seed,
            difficulty_preset=args.difficulty,
            player_speed=args.player_speed,
            initial_lives=args.lives,
        )
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Difficulty: {args.difficulty}")
        print(f"Player speed: {args.player_speed}")
        print(f"Initial lives: {args.lives}")
        for line in format_comparison_lines(args.models, summaries):
            print(line)

    return 0


def cli(argv=None):
    try:
        return main(argv)
    except ValueError as error:
        print(f"Error: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(cli())
