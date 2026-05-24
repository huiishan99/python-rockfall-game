import argparse
import json
import os

from compare_models import (
    build_comparison_payload,
    evaluate_model_path,
    evaluate_policy,
    validate_model_paths,
)
from data_quality import (
    DEFAULT_MAX_SKIPPED_RATIO,
    DEFAULT_MIN_BALANCE_RATIO,
    DEFAULT_MIN_SAMPLES,
    inspect_data_file,
)
from data_store import GAME_DATA_FILE, ensure_parent_dir
from difficulty import DEFAULT_DIFFICULTY_PRESET, difficulty_preset_names
from evaluate_model import DEFAULT_GAMES, DEFAULT_MAX_FRAMES, DEFAULT_RANDOM_SEED
from play_with_model import MODEL_FILE
from policies import POLICY_SAFE_RULE, policy_label
from settings import DEFAULT_VARIANT_PROFILE, INITIAL_LIVES, PLAYER_SPEED, variant_profile_names


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Build a Rockfall model learning report.")
    parser.add_argument("--data", default=GAME_DATA_FILE, help="Gameplay data JSON file.")
    parser.add_argument("--model", default=MODEL_FILE, help="Model file to evaluate.")
    parser.add_argument("--games", type=int, default=DEFAULT_GAMES, help="Evaluation games per profile.")
    parser.add_argument("--max-frames", type=int, default=DEFAULT_MAX_FRAMES, help="Frame limit per game.")
    parser.add_argument("--random-seed", type=int, default=DEFAULT_RANDOM_SEED, help="Evaluation base seed.")
    parser.add_argument(
        "--difficulty",
        choices=difficulty_preset_names(),
        default=DEFAULT_DIFFICULTY_PRESET,
        help="Difficulty preset.",
    )
    parser.add_argument("--player-speed", type=int, default=PLAYER_SPEED, help="Player movement speed in pixels.")
    parser.add_argument("--lives", type=int, default=INITIAL_LIVES, help="Initial player lives.")
    parser.add_argument(
        "--profiles",
        nargs="+",
        choices=variant_profile_names(),
        default=list(variant_profile_names()),
        help="Variant profiles to evaluate.",
    )
    parser.add_argument(
        "--skip-rule-baseline",
        action="store_true",
        help="Only evaluate the model, without the built-in safe-rule baseline.",
    )
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
    parser.add_argument("--report", help="Optional JSON report file to write.")
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
    if args.min_samples <= 0:
        raise ValueError("--min-samples must be greater than zero.")
    if not 0 <= args.min_balance_ratio <= 1:
        raise ValueError("--min-balance-ratio must be between 0 and 1.")
    if not 0 <= args.max_skipped_ratio <= 1:
        raise ValueError("--max-skipped-ratio must be between 0 and 1.")
    if len(set(args.profiles)) != len(args.profiles):
        raise ValueError("--profiles must not contain duplicates.")


def evaluate_profile(
    model_path,
    profile,
    games,
    max_frames,
    random_seed,
    screen,
    difficulty_preset=DEFAULT_DIFFICULTY_PRESET,
    player_speed=PLAYER_SPEED,
    initial_lives=INITIAL_LIVES,
    include_rule_baseline=True,
):
    labels = [model_path]
    summaries = [
        evaluate_model_path(
            model_path,
            games,
            max_frames,
            random_seed,
            screen,
            difficulty_preset=difficulty_preset,
            player_speed=player_speed,
            initial_lives=initial_lives,
            variant_profile=profile,
        )
    ]
    if include_rule_baseline:
        labels.append(policy_label(POLICY_SAFE_RULE))
        summaries.append(
            evaluate_policy(
                POLICY_SAFE_RULE,
                games,
                max_frames,
                random_seed,
                screen,
                difficulty_preset=difficulty_preset,
                player_speed=player_speed,
                initial_lives=initial_lives,
                variant_profile=profile,
            )
        )

    return build_comparison_payload(
        labels,
        summaries,
        max_frames=max_frames,
        random_seed=random_seed,
        difficulty_preset=difficulty_preset,
        player_speed=player_speed,
        initial_lives=initial_lives,
        variant_profile=profile,
    )


def build_report_payload(
    model_path,
    data_summary,
    profile_reports,
    games,
    max_frames,
    random_seed,
    difficulty_preset=DEFAULT_DIFFICULTY_PRESET,
    player_speed=PLAYER_SPEED,
    initial_lives=INITIAL_LIVES,
):
    payload = {
        "model": model_path,
        "data": data_summary,
        "settings": {
            "games": games,
            "max_frames": max_frames,
            "random_seed": random_seed,
            "difficulty": difficulty_preset,
            "player_speed": player_speed,
            "initial_lives": initial_lives,
        },
        "profiles": profile_reports,
    }
    payload["recommendations"] = model_report_recommendations(payload)
    return payload


def model_report_recommendations(payload):
    recommendations = []
    variant_warnings = payload["data"].get("variant_coverage", {}).get("warnings", [])
    if "no_recorded_variant_samples" in variant_warnings:
        recommendations.append("collect_variant_rich_data")
    elif variant_warnings:
        recommendations.append("fill_missing_variant_samples")

    for profile_name, profile_report in payload["profiles"].items():
        model_result = profile_report["models"][0]
        if profile_report["best_model"] != payload["model"]:
            recommendations.append(f"beat_baseline_on_{profile_name}")
        score_breakdown = model_result.get("score_breakdown", {})
        variant_bonus = score_breakdown.get("variant_bonus", {}).get("average", 0)
        risk_bonus = score_breakdown.get("risk_bonus", {}).get("average", 0)
        if profile_name != DEFAULT_VARIANT_PROFILE and variant_bonus + risk_bonus == 0:
            recommendations.append(f"improve_reward_capture_on_{profile_name}")

    return sorted(set(recommendations))


def format_model_row(model_result):
    score_breakdown = model_result.get("score_breakdown", {})
    variant_bonus = score_breakdown.get("variant_bonus", {}).get("average", 0)
    risk_bonus = score_breakdown.get("risk_bonus", {}).get("average", 0)
    return (
        f"  {model_result['model']}: "
        f"avg_score={model_result['average_score']:.2f}, "
        f"delta={model_result.get('score_delta', 0):+.2f}, "
        f"survival={model_result['survival_rate']:.1%}, "
        f"variant_bonus={variant_bonus:.2f}, "
        f"risk_bonus={risk_bonus:.2f}"
    )


def format_report_lines(payload):
    data = payload["data"]
    data_quality = data["data_quality"]
    variant_coverage = data["variant_coverage"]
    settings = payload["settings"]
    lines = [
        "Model learning report",
        f"Model: {payload['model']}",
        f"Data: {data['data']}",
        f"Data quality: {data_quality['status']} ({data['valid_samples']} valid, {data['skipped_entries']} skipped)",
        f"Variant quality: {variant_coverage['status']} ({variant_coverage['recorded_variant_samples']} recorded)",
        (
            "Settings: "
            f"games={settings['games']}, "
            f"max_frames={settings['max_frames']}, "
            f"difficulty={settings['difficulty']}, "
            f"player_speed={settings['player_speed']}, "
            f"lives={settings['initial_lives']}"
        ),
    ]
    if variant_coverage["warnings"]:
        lines.append("Variant warnings: " + ", ".join(variant_coverage["warnings"]))
    if data_quality["warnings"]:
        lines.append("Data warnings: " + ", ".join(data_quality["warnings"]))

    for profile_name, profile_report in payload["profiles"].items():
        lines.append("")
        lines.append(f"Profile: {profile_name}")
        for model_result in profile_report["models"]:
            lines.append(format_model_row(model_result))
        lines.append(f"  Best: {profile_report['best_model']}")

    if payload["recommendations"]:
        lines.append("")
        lines.append("Recommendations: " + ", ".join(payload["recommendations"]))
    return lines


def write_model_report(payload, report_path):
    ensure_parent_dir(report_path)
    with open(report_path, "w") as report_file:
        json.dump(payload, report_file, indent=2, sort_keys=True)


def build_model_report(args):
    validate_model_paths([args.model])
    data_summary = inspect_data_file(
        args.data,
        min_samples=args.min_samples,
        min_balance_ratio=args.min_balance_ratio,
        max_skipped_ratio=args.max_skipped_ratio,
    )

    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame

    from settings import SCREEN_HEIGHT, SCREEN_WIDTH

    pygame.font.init()
    screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    try:
        profile_reports = {
            profile: evaluate_profile(
                args.model,
                profile,
                args.games,
                args.max_frames,
                args.random_seed,
                screen,
                difficulty_preset=args.difficulty,
                player_speed=args.player_speed,
                initial_lives=args.lives,
                include_rule_baseline=not args.skip_rule_baseline,
            )
            for profile in args.profiles
        }
    finally:
        pygame.quit()

    return build_report_payload(
        args.model,
        data_summary,
        profile_reports,
        args.games,
        args.max_frames,
        args.random_seed,
        difficulty_preset=args.difficulty,
        player_speed=args.player_speed,
        initial_lives=args.lives,
    )


def main(argv=None):
    args = parse_args(argv)
    validate_args(args)
    payload = build_model_report(args)
    if args.report:
        write_model_report(payload, args.report)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for line in format_report_lines(payload):
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
