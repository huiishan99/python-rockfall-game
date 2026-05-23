import argparse
import json
import os
from collections import Counter

from compare_models import (
    build_comparison_payload,
    evaluate_model_path,
    format_comparison_lines,
    score_delta,
    validate_model_paths,
)
from data_quality import (
    DEFAULT_MAX_SKIPPED_RATIO,
    DEFAULT_MIN_BALANCE_RATIO,
    DEFAULT_MIN_SAMPLES,
    action_balance_payload,
    data_quality_summary,
    inspect_variant_coverage_file,
)
from data_store import GAME_DATA_FILE, ensure_parent_dir
from difficulty import DEFAULT_DIFFICULTY_PRESET, difficulty_preset_names
from evaluate_model import DEFAULT_GAMES, DEFAULT_MAX_FRAMES, DEFAULT_RANDOM_SEED
from features import FEATURE_NAMES
from play_with_model import MODEL_FILE
from settings import DEFAULT_VARIANT_PROFILE, INITIAL_LIVES, PLAYER_SPEED, variant_profile_names
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
    parser.add_argument("--min-samples", type=int, default=DEFAULT_MIN_SAMPLES, help="Recommended minimum valid samples.")
    parser.add_argument(
        "--min-balance-ratio",
        type=float,
        default=DEFAULT_MIN_BALANCE_RATIO,
        help="Recommended minimum minority-action ratio.",
    )
    parser.add_argument(
        "--max-skipped-ratio",
        type=float,
        default=DEFAULT_MAX_SKIPPED_RATIO,
        help="Recommended maximum skipped-entry ratio.",
    )
    parser.add_argument("--games", type=int, default=DEFAULT_GAMES, help="Evaluation games per model.")
    parser.add_argument("--max-frames", type=int, default=DEFAULT_MAX_FRAMES, help="Frame limit per game.")
    parser.add_argument("--eval-random-seed", type=int, default=DEFAULT_RANDOM_SEED, help="Evaluation base seed.")
    parser.add_argument(
        "--difficulty",
        choices=difficulty_preset_names(),
        default=DEFAULT_DIFFICULTY_PRESET,
        help="Difficulty preset for model comparison.",
    )
    parser.add_argument("--player-speed", type=int, default=PLAYER_SPEED, help="Player movement speed in pixels.")
    parser.add_argument("--lives", type=int, default=INITIAL_LIVES, help="Initial player lives.")
    parser.add_argument(
        "--variant-profile",
        choices=variant_profile_names(),
        default=DEFAULT_VARIANT_PROFILE,
        help="Rock variant spawn profile for model comparison.",
    )
    parser.add_argument("--report", help="Optional JSON report file to write.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text.")
    return parser.parse_args(argv)


def validate_experiment_paths(baseline_path, candidate_path):
    if os.path.abspath(baseline_path) == os.path.abspath(candidate_path):
        raise ValueError("--candidate must be different from --baseline to avoid overwriting the baseline model.")


def train_candidate_model(
    data_path,
    model_path,
    estimators,
    test_size,
    random_state,
    min_samples=DEFAULT_MIN_SAMPLES,
    min_balance_ratio=DEFAULT_MIN_BALANCE_RATIO,
    max_skipped_ratio=DEFAULT_MAX_SKIPPED_RATIO,
):
    X, y, skipped_entries = load_data(data_path)
    if len(X) < 2:
        raise ValueError("Need at least 2 valid training samples.")

    action_counts = Counter(y)
    if len(action_counts) < 2:
        raise ValueError("Need both left and right samples to train a useful model.")
    quality = data_quality_summary(
        len(X),
        skipped_entries,
        action_counts,
        min_samples,
        min_balance_ratio,
        max_skipped_ratio,
    )

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
        "action_balance": action_balance_payload(action_counts),
        "variant_coverage": inspect_variant_coverage_file(data_path),
        "validation_accuracy": validation_accuracy,
        "estimators": estimators,
        "test_size": test_size,
        "random_state": random_state,
        "data_quality": quality,
    }


def evaluate_models(
    model_paths,
    games,
    max_frames,
    random_seed,
    difficulty_preset=DEFAULT_DIFFICULTY_PRESET,
    player_speed=PLAYER_SPEED,
    initial_lives=INITIAL_LIVES,
    variant_profile=DEFAULT_VARIANT_PROFILE,
):
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame

    from settings import SCREEN_HEIGHT, SCREEN_WIDTH

    pygame.font.init()
    screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    try:
        return [
            evaluate_model_path(
                model_path,
                games,
                max_frames,
                random_seed,
                screen,
                difficulty_preset=difficulty_preset,
                player_speed=player_speed,
                initial_lives=initial_lives,
                variant_profile=variant_profile,
            )
            for model_path in model_paths
        ]
    finally:
        pygame.quit()


def build_experiment_payload(
    training_summary,
    model_paths,
    comparison_summaries,
    max_frames,
    eval_random_seed,
    difficulty_preset=DEFAULT_DIFFICULTY_PRESET,
    player_speed=PLAYER_SPEED,
    initial_lives=INITIAL_LIVES,
    variant_profile=DEFAULT_VARIANT_PROFILE,
):
    return {
        "training": training_summary,
        "comparison": build_comparison_payload(
            model_paths,
            comparison_summaries,
            max_frames=max_frames,
            random_seed=eval_random_seed,
            difficulty_preset=difficulty_preset,
            player_speed=player_speed,
            initial_lives=initial_lives,
            variant_profile=variant_profile,
        ),
        "candidate_result": candidate_result(comparison_summaries[0], comparison_summaries[1]),
    }


def candidate_result(baseline_summary, candidate_summary):
    delta = score_delta(candidate_summary, baseline_summary)
    if delta > 0:
        return "candidate_outperformed_baseline"
    if delta < 0:
        return "candidate_underperformed_baseline"
    return "candidate_matched_baseline"


def write_experiment_report(payload, report_path):
    ensure_parent_dir(report_path)
    with open(report_path, "w") as report_file:
        json.dump(payload, report_file, indent=2, sort_keys=True)


def format_training_lines(training_summary):
    lines = [
        f"Data: {training_summary['data']}",
        f"Candidate model: {training_summary['model']}",
        f"Valid samples: {training_summary['valid_samples']} ({training_summary['skipped_entries']} skipped)",
        "Features: " + ", ".join(training_summary["features"]),
        (
            "Action balance: "
            f"left={training_summary['action_balance']['left']}, "
            f"right={training_summary['action_balance']['right']}"
        ),
        (
            "Variant coverage: "
            f"recorded={training_summary['variant_coverage']['recorded_variant_samples']}, "
            f"legacy={training_summary['variant_coverage']['legacy_obstacle_samples']}"
        ),
        f"Validation accuracy: {training_summary['validation_accuracy']:.3f}",
        f"Data quality: {training_summary['data_quality']['status']}",
    ]
    variant_warnings = training_summary["variant_coverage"]["warnings"]
    if variant_warnings:
        lines.append("Variant warnings: " + ", ".join(variant_warnings))
    warnings = training_summary["data_quality"]["warnings"]
    if warnings:
        lines.append("Data quality warnings: " + ", ".join(warnings))
    return lines


def format_experiment_lines(training_summary, model_paths, comparison_summaries):
    return (
        ["Training candidate model:"]
        + format_training_lines(training_summary)
        + [""]
        + ["Model comparison:"]
        + format_comparison_lines(model_paths, comparison_summaries)
        + [f"Candidate result: {candidate_result(comparison_summaries[0], comparison_summaries[1])}"]
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
    validate_experiment_paths(args.baseline, args.candidate)
    validate_model_paths([args.baseline])

    training_summary = train_candidate_model(
        args.data,
        args.candidate,
        args.estimators,
        args.test_size,
        args.random_state,
        min_samples=args.min_samples,
        min_balance_ratio=args.min_balance_ratio,
        max_skipped_ratio=args.max_skipped_ratio,
    )
    model_paths = [args.baseline, args.candidate]
    comparison_summaries = evaluate_models(
        model_paths,
        args.games,
        args.max_frames,
        args.eval_random_seed,
        difficulty_preset=args.difficulty,
        player_speed=args.player_speed,
        initial_lives=args.lives,
        variant_profile=args.variant_profile,
    )
    payload = build_experiment_payload(
        training_summary,
        model_paths,
        comparison_summaries,
        args.max_frames,
        args.eval_random_seed,
        difficulty_preset=args.difficulty,
        player_speed=args.player_speed,
        initial_lives=args.lives,
        variant_profile=args.variant_profile,
    )

    if args.report:
        write_experiment_report(payload, args.report)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Difficulty: {args.difficulty}")
        print(f"Player speed: {args.player_speed}")
        print(f"Initial lives: {args.lives}")
        print(f"Variant profile: {args.variant_profile}")
        for line in format_experiment_lines(training_summary, model_paths, comparison_summaries):
            print(line)
        if args.report:
            print(f"Report saved to {args.report}")

    return 0


def cli(argv=None):
    try:
        return main(argv)
    except ValueError as error:
        print(f"Error: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(cli())
