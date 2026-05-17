import argparse
import json
import os
import random
from statistics import mean

from play_with_model import MODEL_FILE
from difficulty import DEFAULT_DIFFICULTY_PRESET, difficulty_preset_names

DEFAULT_GAMES = 10
DEFAULT_MAX_FRAMES = 3600
DEFAULT_RANDOM_SEED = 42


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Evaluate a Rockfall model without opening a game window.")
    parser.add_argument("--model", default=MODEL_FILE, help="Model file to load.")
    parser.add_argument("--games", type=int, default=DEFAULT_GAMES, help="Number of games to simulate.")
    parser.add_argument("--max-frames", type=int, default=DEFAULT_MAX_FRAMES, help="Frame limit per game.")
    parser.add_argument("--random-seed", type=int, default=DEFAULT_RANDOM_SEED, help="Base random seed.")
    parser.add_argument(
        "--difficulty",
        choices=difficulty_preset_names(),
        default=DEFAULT_DIFFICULTY_PRESET,
        help="Difficulty preset.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text.")
    return parser.parse_args(argv)


def run_game(model, screen, max_frames, difficulty_preset=DEFAULT_DIFFICULTY_PRESET):
    from game_core import RockfallGame
    from play_with_model import predict_action

    game = RockfallGame(screen, difficulty_preset=difficulty_preset)
    frames = 0

    while not game.game_over and frames < max_frames:
        game.apply_action(predict_action(model, game))
        game.update()
        frames += 1

    return {
        "score": game.score,
        "best_combo": game.best_combo,
        "frames": frames,
        "lives": game.lives,
        "timed_out": not game.game_over,
    }


def summarize_results(results):
    scores = [result["score"] for result in results]
    best_combos = [result["best_combo"] for result in results]
    frames = [result["frames"] for result in results]
    timeouts = sum(1 for result in results if result["timed_out"])

    return {
        "games": len(results),
        "average_score": mean(scores),
        "best_score": max(scores),
        "worst_score": min(scores),
        "average_best_combo": mean(best_combos),
        "best_combo": max(best_combos),
        "average_frames": mean(frames),
        "timeouts": timeouts,
    }


def format_summary_lines(summary, games_label="Games"):
    return [
        f"{games_label}: {summary['games']}",
        f"Average score: {summary['average_score']:.2f}",
        f"Best score: {summary['best_score']}",
        f"Worst score: {summary['worst_score']}",
        f"Average best combo: {summary['average_best_combo']:.2f}",
        f"Best combo: {summary['best_combo']}",
        f"Average frames: {summary['average_frames']:.1f}",
        f"Timed out games: {summary['timeouts']}",
    ]


def build_summary_payload(model_path, summary, max_frames=None, random_seed=None, difficulty_preset=None):
    payload = {"model": model_path, **summary}
    if max_frames is not None:
        payload["max_frames"] = max_frames
    if random_seed is not None:
        payload["random_seed"] = random_seed
    if difficulty_preset is not None:
        payload["difficulty"] = difficulty_preset
    return payload


def main(argv=None):
    args = parse_args(argv)
    if args.games <= 0:
        raise ValueError("--games must be greater than zero.")
    if args.max_frames <= 0:
        raise ValueError("--max-frames must be greater than zero.")

    import joblib

    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame

    from settings import SCREEN_HEIGHT, SCREEN_WIDTH

    pygame.font.init()
    screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    model = joblib.load(args.model)

    results = []
    for game_index in range(args.games):
        random.seed(args.random_seed + game_index)
        results.append(run_game(model, screen, args.max_frames, difficulty_preset=args.difficulty))

    summary = summarize_results(results)
    if args.json:
        payload = build_summary_payload(
            args.model,
            summary,
            max_frames=args.max_frames,
            random_seed=args.random_seed,
            difficulty_preset=args.difficulty,
        )
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Model: {args.model}")
        print(f"Difficulty: {args.difficulty}")
        for line in format_summary_lines(summary):
            print(line)

    pygame.quit()


if __name__ == "__main__":
    main()
