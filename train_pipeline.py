import argparse
import json
import os
import shutil

from compare_models import build_comparison_payload, evaluate_model_path, evaluate_policy, format_comparison_lines
from data_store import ORE_TARGET_DATA_FILE, ORE_TARGET_OBJECTIVE, ensure_parent_dir
from difficulty import DEFAULT_DIFFICULTY_PRESET, difficulty_preset_names
from evaluate_model import DEFAULT_GAMES, DEFAULT_MAX_FRAMES, DEFAULT_RANDOM_SEED
from leaderboard import DEFAULT_LEADERBOARD_FILE, append_report_to_leaderboard
from policies import built_in_policy_names, policy_label
from play_with_model import MODEL_FILE
from run_model_experiment import train_candidate_model, validate_experiment_paths
from settings import DEFAULT_VARIANT_PROFILE, INITIAL_LIVES, PLAYER_SPEED, variant_profile_names
from train_model import (
    N_ESTIMATORS,
    RANDOM_STATE,
    REQUIRE_OBJECTIVE_CHOICES,
    REWARD_WEIGHTING_CHOICES,
    REWARD_WEIGHTING_SCORE,
    TEST_SIZE,
    format_sample_weight_line,
    format_objective_coverage_line,
)

DEFAULT_CANDIDATE_MODEL = "runs/pipeline_candidate.pkl"
DEFAULT_PIPELINE_REPORT = "runs/training_pipeline.json"
DEFAULT_MIN_SCORE_DELTA = 0.0


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run the full Rockfall model training pipeline.")
    parser.add_argument("--data", default=ORE_TARGET_DATA_FILE, help="Gameplay data JSON file.")
    parser.add_argument("--baseline", default=MODEL_FILE, help="Current baseline model.")
    parser.add_argument("--candidate", default=DEFAULT_CANDIDATE_MODEL, help="Candidate model output file.")
    parser.add_argument("--report", default=DEFAULT_PIPELINE_REPORT, help="JSON report file to write.")
    parser.add_argument(
        "--leaderboard",
        default=DEFAULT_LEADERBOARD_FILE,
        help="Model leaderboard JSON file to update after the pipeline run.",
    )
    parser.add_argument("--leaderboard-tag", help="Optional leaderboard label for this pipeline run.")
    parser.add_argument("--skip-leaderboard", action="store_true", help="Do not update the model leaderboard.")
    parser.add_argument("--test-size", type=float, default=TEST_SIZE, help="Validation split size.")
    parser.add_argument("--random-state", type=int, default=RANDOM_STATE, help="Training random seed.")
    parser.add_argument("--estimators", type=int, default=N_ESTIMATORS, help="Random forest tree count.")
    parser.add_argument(
        "--reward-weighting",
        choices=REWARD_WEIGHTING_CHOICES,
        default=REWARD_WEIGHTING_SCORE,
        help="Sample weighting mode for candidate training.",
    )
    parser.add_argument(
        "--require-objective",
        choices=REQUIRE_OBJECTIVE_CHOICES,
        default=ORE_TARGET_OBJECTIVE,
        help="Fail if training data does not cleanly match this objective.",
    )
    parser.add_argument("--games", type=int, default=DEFAULT_GAMES, help="Evaluation games per entry.")
    parser.add_argument("--max-frames", type=int, default=DEFAULT_MAX_FRAMES, help="Frame limit per game.")
    parser.add_argument("--eval-random-seed", type=int, default=DEFAULT_RANDOM_SEED, help="Evaluation base seed.")
    parser.add_argument(
        "--difficulty",
        choices=difficulty_preset_names(),
        default=DEFAULT_DIFFICULTY_PRESET,
        help="Difficulty preset for evaluation.",
    )
    parser.add_argument("--player-speed", type=int, default=PLAYER_SPEED, help="Player movement speed in pixels.")
    parser.add_argument("--lives", type=int, default=INITIAL_LIVES, help="Initial player lives.")
    parser.add_argument(
        "--variant-profile",
        choices=variant_profile_names(),
        default=DEFAULT_VARIANT_PROFILE,
        help="Rock variant spawn profile for evaluation.",
    )
    parser.add_argument(
        "--policy-baselines",
        nargs="+",
        choices=built_in_policy_names(),
        default=list(built_in_policy_names()),
        help="Built-in policy baselines to include in comparison.",
    )
    parser.add_argument(
        "--min-score-delta",
        type=float,
        default=DEFAULT_MIN_SCORE_DELTA,
        help="Required average-score gain before recommending promotion.",
    )
    parser.add_argument("--promote", action="store_true", help="Copy the candidate over the baseline when recommended.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text.")
    return parser.parse_args(argv)


def validate_args(args):
    if args.games <= 0:
        raise ValueError("--games must be greater than zero.")
    if args.max_frames <= 0:
        raise ValueError("--max-frames must be greater than zero.")
    if args.player_speed <= 0:
        raise ValueError("--player-speed must be greater than zero.")
    if args.lives <= 0:
        raise ValueError("--lives must be greater than zero.")
    if len(set(args.policy_baselines)) != len(args.policy_baselines):
        raise ValueError("--policy-baselines must not contain duplicates.")
    if not os.path.exists(args.baseline):
        raise ValueError(f"Baseline model not found: {args.baseline}.")
    validate_experiment_paths(args.baseline, args.candidate)


def evaluate_pipeline_entries(
    model_paths,
    policy_baselines,
    games,
    max_frames,
    random_seed,
    difficulty_preset,
    player_speed,
    initial_lives,
    variant_profile,
):
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame

    from settings import SCREEN_HEIGHT, SCREEN_WIDTH

    labels = list(model_paths)
    summaries = []
    pygame.font.init()
    screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    try:
        for model_path in model_paths:
            summaries.append(
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
            )
        for policy_name in policy_baselines:
            labels.append(policy_label(policy_name))
            summaries.append(
                evaluate_policy(
                    policy_name,
                    games,
                    max_frames,
                    random_seed,
                    screen,
                    difficulty_preset=difficulty_preset,
                    player_speed=player_speed,
                    initial_lives=initial_lives,
                    variant_profile=variant_profile,
                )
            )
    finally:
        pygame.quit()
    return labels, summaries


def promotion_decision(comparison_payload, candidate_path, min_score_delta=DEFAULT_MIN_SCORE_DELTA):
    baseline = comparison_payload["models"][0]
    candidate = next(
        (model for model in comparison_payload["models"] if model["model"] == candidate_path),
        None,
    )
    if candidate is None:
        return {
            "action": "inspect_pipeline",
            "reason": "candidate_missing_from_comparison",
            "score_delta": 0,
        }

    score_delta = candidate["average_score"] - baseline["average_score"]
    if comparison_payload["best_model"] == candidate_path and score_delta > min_score_delta:
        return {
            "action": "promote_candidate",
            "reason": "candidate_is_best_and_above_delta",
            "score_delta": score_delta,
        }
    if score_delta > min_score_delta:
        return {
            "action": "keep_candidate_for_review",
            "reason": "candidate_beats_baseline_but_not_policy_best",
            "score_delta": score_delta,
        }
    return {
        "action": "keep_baseline",
        "reason": "candidate_did_not_clear_score_delta",
        "score_delta": score_delta,
    }


def build_pipeline_payload(
    training_summary,
    labels,
    summaries,
    args,
    promoted=False,
):
    comparison = build_comparison_payload(
        labels,
        summaries,
        max_frames=args.max_frames,
        random_seed=args.eval_random_seed,
        difficulty_preset=args.difficulty,
        player_speed=args.player_speed,
        initial_lives=args.lives,
        variant_profile=args.variant_profile,
    )
    decision = promotion_decision(comparison, args.candidate, args.min_score_delta)
    return {
        "training": training_summary,
        "comparison": comparison,
        "decision": decision,
        "promotion": {
            "requested": args.promote,
            "performed": promoted,
            "baseline": args.baseline,
            "candidate": args.candidate,
        },
    }


def write_pipeline_report(payload, report_path):
    ensure_parent_dir(report_path)
    with open(report_path, "w") as report_file:
        json.dump(payload, report_file, indent=2, sort_keys=True)


def promote_candidate(candidate_path, baseline_path):
    ensure_parent_dir(baseline_path)
    shutil.copyfile(candidate_path, baseline_path)


def format_training_block(training_summary):
    lines = [
        f"Data: {training_summary['data']}",
        f"Candidate model: {training_summary['model']}",
        f"Valid samples: {training_summary['valid_samples']} ({training_summary['skipped_entries']} skipped)",
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
        format_objective_coverage_line(training_summary["objective_coverage"]),
        f"Validation accuracy: {training_summary['validation_accuracy']:.3f}",
        format_sample_weight_line(training_summary["sample_weights"]),
        f"Data quality: {training_summary['data_quality']['status']}",
    ]
    for label, coverage in (
        ("Variant warnings", training_summary["variant_coverage"]["warnings"]),
        ("Objective warnings", training_summary["objective_coverage"]["warnings"]),
        ("Data quality warnings", training_summary["data_quality"]["warnings"]),
    ):
        if coverage:
            lines.append(f"{label}: " + ", ".join(coverage))
    return lines


def format_pipeline_lines(payload):
    labels = [model["model"] for model in payload["comparison"]["models"]]
    lines = ["Training pipeline"]
    lines.extend(format_training_block(payload["training"]))
    lines.append("")
    lines.append("Comparison:")
    lines.extend(format_comparison_lines(labels, payload["comparison"]["models"]))
    decision = payload["decision"]
    lines.append("")
    lines.append(
        "Recommendation: "
        f"{decision['action']} ({decision['reason']}, score_delta={decision['score_delta']:+.2f})"
    )
    if payload["promotion"]["performed"]:
        lines.append(f"Promoted {payload['promotion']['candidate']} -> {payload['promotion']['baseline']}")
    return lines


def run_pipeline(args):
    validate_args(args)
    training_summary = train_candidate_model(
        args.data,
        args.candidate,
        args.estimators,
        args.test_size,
        args.random_state,
        reward_weighting=args.reward_weighting,
        require_objective=args.require_objective,
    )
    labels, summaries = evaluate_pipeline_entries(
        [args.baseline, args.candidate],
        args.policy_baselines,
        args.games,
        args.max_frames,
        args.eval_random_seed,
        args.difficulty,
        args.player_speed,
        args.lives,
        args.variant_profile,
    )
    preview_payload = build_pipeline_payload(training_summary, labels, summaries, args)
    promoted = False
    if args.promote and preview_payload["decision"]["action"] == "promote_candidate":
        promote_candidate(args.candidate, args.baseline)
        promoted = True
    return build_pipeline_payload(training_summary, labels, summaries, args, promoted=promoted)


def main(argv=None):
    args = parse_args(argv)
    payload = run_pipeline(args)
    if args.report:
        write_pipeline_report(payload, args.report)
    leaderboard_entries = []
    if not args.skip_leaderboard:
        _, leaderboard_entries = append_report_to_leaderboard(
            payload,
            leaderboard_path=args.leaderboard,
            source_report=args.report,
            tag=args.leaderboard_tag,
        )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for line in format_pipeline_lines(payload):
            print(line)
        if args.report:
            print(f"Report saved to {args.report}")
        if leaderboard_entries:
            print(f"Leaderboard updated: {args.leaderboard} (+{len(leaderboard_entries)} entries)")
    return 0


def cli(argv=None):
    try:
        return main(argv)
    except ValueError as error:
        print(f"Error: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(cli())
