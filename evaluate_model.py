import argparse
import random
from statistics import mean

from play_with_model import MODEL_FILE

DEFAULT_GAMES = 10
DEFAULT_MAX_FRAMES = 3600
DEFAULT_RANDOM_SEED = 42


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Evaluate a Rockfall model without opening a game window.")
    parser.add_argument("--model", default=MODEL_FILE, help="Model file to load.")
    parser.add_argument("--games", type=int, default=DEFAULT_GAMES, help="Number of games to simulate.")
    parser.add_argument("--max-frames", type=int, default=DEFAULT_MAX_FRAMES, help="Frame limit per game.")
    parser.add_argument("--random-seed", type=int, default=DEFAULT_RANDOM_SEED, help="Base random seed.")
    return parser.parse_args(argv)


def run_game(model, screen, max_frames):
    from game_core import RockfallGame
    from play_with_model import predict_action

    game = RockfallGame(screen)
    frames = 0

    while not game.game_over and frames < max_frames:
        game.apply_action(predict_action(model, game))
        game.update()
        frames += 1

    return {
        "score": game.score,
        "frames": frames,
        "lives": game.lives,
        "timed_out": not game.game_over,
    }


def summarize_results(results):
    scores = [result["score"] for result in results]
    frames = [result["frames"] for result in results]
    timeouts = sum(1 for result in results if result["timed_out"])

    return {
        "games": len(results),
        "average_score": mean(scores),
        "best_score": max(scores),
        "worst_score": min(scores),
        "average_frames": mean(frames),
        "timeouts": timeouts,
    }


def main(argv=None):
    args = parse_args(argv)
    if args.games <= 0:
        raise ValueError("--games must be greater than zero.")
    if args.max_frames <= 0:
        raise ValueError("--max-frames must be greater than zero.")

    import joblib
    import pygame

    from settings import SCREEN_HEIGHT, SCREEN_WIDTH

    pygame.font.init()
    screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    model = joblib.load(args.model)

    results = []
    for game_index in range(args.games):
        random.seed(args.random_seed + game_index)
        results.append(run_game(model, screen, args.max_frames))

    summary = summarize_results(results)
    print(f"Model: {args.model}")
    print(f"Games: {summary['games']}")
    print(f"Average score: {summary['average_score']:.2f}")
    print(f"Best score: {summary['best_score']}")
    print(f"Worst score: {summary['worst_score']}")
    print(f"Average frames: {summary['average_frames']:.1f}")
    print(f"Timed out games: {summary['timeouts']}")

    pygame.quit()


if __name__ == "__main__":
    main()
