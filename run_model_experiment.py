import argparse
import json
import os
from collections import Counter

from compare_models import build_comparison_payload, evaluate_model_path, format_comparison_lines
from data_store import GAME_DATA_FILE
from evaluate_model import DEFAULT_GAMES, DEFAULT_MAX_FRAMES, DEFAULT_RANDOM_SEED
from features import FEATURE_NAMES
from play_with_model import MODEL_FILE
from train_model import (
    N_ESTIMATORS,
    RANDOM_STATE,
    TEST_SIZE,
    load_data,
    save_model,
    split_data,
    train_model,
)

DEFAULT_CANDIDATE_MODEL = "runs/candidate_model.pkl"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Train a candidate model and compare it with a baseline.")
    parser.add_argument("--data", default=GAME_DATA_FILE, help="Gameplay data JSON file.")
    parser.add_argument("--baseline", default=MODEL_FILE, help="Baseline model file to compare against.")
    parser.add_argument("--candidate", default=DEFAULT_CANDIDATE_MODEL, help="Candidate model output file.")
    parser.add_argument("--test-size", type=float, default=TEST_SIZE, help="Validation split size.")
    parser.add_argument("--random-state", type=int, default=RANDOM_STATE, help="Training random seed.")
    parser.add_argument("--estimators", type=int, default=N_ESTIMATORS, help="Random forest tree count.")
    parser.add_argument("--games", type=int, default=DEFAULT_GAMES, help="Evaluation games per model.")
    parser.add_argument("--max-frames", type=int, default=DEFAULT_MAX_FRAMES, help="Frame limit per game.")
    parser.add_argument("--eval-random-seed", type=int, default=DEFAULT_RANDOM_SEED, help="Evaluation base seed.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text.")
    return parser.parse_args(argv)


def train_candidate_model(data_path, model_path, estimators, test_size, random_state):
    X, y, skipped_entries = load_data(data_path)
    if len(X) < 2:
        raise ValueError("Need at least 2 valid training samples.")

    action_counts = Counter(y)
    if len(action_counts) < 2:
        raise ValueError("Need both left and right samples to train a useful model.")

    X_train, X_test, y_train, y_test = split_data(X, y, test_size, random_state)
    model = train_model(X_train, y_train, estimators, random_state)
    validation_accuracy = model.score(X_test, y_test)
    save_model(model, model_path)

    return {
        "data": data_path,
        "model": model_path,
        "valid_samples": len(X),
        "skipped_entries": skipped_entries,
        "features": list(FEATURE_NAMES),
        "action_balance": {
            "left": int(action_counts[0]),
            "right": int(action_counts[1]),
        },
        "validation_accuracy": validation_accuracy,
        "estimators": estimators,
        "test_size": test_size,
        "random_state": random_state,
    }


def evaluate_models(model_paths, games, max_frames, random_seed):
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame

    from settings import SCREEN_HEIGHT, SCREEN_WIDTH

    pygame.font.init()
    screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    try:
        return [
            evaluate_model_path(model_path, games, max_frames, random_seed, screen)
            for model_path in model_paths
        ]
    finally:
        pygame.quit()


def build_experiment_payload(training_summary, model_paths, comparison_summaries, max_frames, eval_random_seed):
    return {
        "training": training_summary,
        "comparison": build_comparison_payload(
            model_paths,
            comparison_summaries,
            max_frames=max_frames,
            random_seed=eval_random_seed,
        ),
    }


def format_training_lines(training_summary):
    return [
        f"Data: {training_summary['data']}",
        f"Candidate model: {training_summary['model']}",
        f"Valid samples: {training_summary['valid_samples']} ({training_summary['skipped_entries']} skipped)",
        "Features: " + ", ".join(training_summary["features"]),
        (
            "Action balance: "
            f"left={training_summary['action_balance']['left']}, "
            f"right={training_summary['action_balance']['right']}"
        ),
        f"Validation accuracy: {training_summary['validation_accuracy']:.3f}",
    ]


def format_experiment_lines(training_summary, model_paths, comparison_summaries):
    return (
        ["Training candidate model:"]
        + format_training_lines(training_summary)
        + [""]
        + ["Model comparison:"]
        + format_comparison_lines(model_paths, comparison_summaries)
    )


def main(argv=None):
    args = parse_args(argv)
    if args.games <= 0:
        raise ValueError("--games must be greater than zero.")
    if args.max_frames <= 0:
        raise ValueError("--max-frames must be greater than zero.")

    training_summary = train_candidate_model(
        args.data,
        args.candidate,
        args.estimators,
        args.test_size,
        args.random_state,
    )
    model_paths = [args.baseline, args.candidate]
    comparison_summaries = evaluate_models(model_paths, args.games, args.max_frames, args.eval_random_seed)

    if args.json:
        payload = build_experiment_payload(
            training_summary,
            model_paths,
            comparison_summaries,
            args.max_frames,
            args.eval_random_seed,
        )
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for line in format_experiment_lines(training_summary, model_paths, comparison_summaries):
            print(line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
