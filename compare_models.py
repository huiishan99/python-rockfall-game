import argparse
import json
import os
import random

from evaluate_model import (
    DEFAULT_GAMES,
    DEFAULT_MAX_FRAMES,
    DEFAULT_RANDOM_SEED,
    build_summary_payload,
    run_policy,
    run_game,
    summarize_results,
    write_summary_report,
)
from leaderboard import append_report_to_leaderboard
from difficulty import DEFAULT_DIFFICULTY_PRESET, difficulty_preset_names
from policies import POLICY_ORE_HUNTER, POLICY_SAFE_RULE, policy_label
from play_with_model import MODEL_FILE
from settings import DEFAULT_VARIANT_PROFILE, INITIAL_LIVES, PLAYER_SPEED, variant_profile_names


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
    parser.add_argument(
        "--variant-profile",
        choices=variant_profile_names(),
        default=DEFAULT_VARIANT_PROFILE,
        help="Rock variant spawn profile.",
    )
    parser.add_argument(
        "--include-rule-baseline",
        action="store_true",
        help="Compare models against the built-in safe-rule baseline policy.",
    )
    parser.add_argument(
        "--include-ore-hunter-baseline",
        action="store_true",
        help="Compare models against a built-in ore-hunter policy that spends lives for ore.",
    )
    parser.add_argument("--report", help="Optional JSON report file to write.")
    parser.add_argument("--leaderboard", help="Optional model leaderboard JSON file to update.")
    parser.add_argument("--leaderboard-tag", help="Optional leaderboard label for this comparison.")
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
    variant_profile=DEFAULT_VARIANT_PROFILE,
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
                variant_profile=variant_profile,
            )
        )

    return summarize_results(results)


def evaluate_policy(
    policy_name,
    games,
    max_frames,
    random_seed,
    screen,
    difficulty_preset=DEFAULT_DIFFICULTY_PRESET,
    player_speed=PLAYER_SPEED,
    initial_lives=INITIAL_LIVES,
    variant_profile=DEFAULT_VARIANT_PROFILE,
):
    results = []
    for game_index in range(games):
        random.seed(random_seed + game_index)
        results.append(
            run_policy(
                policy_name,
                screen,
                max_frames,
                difficulty_preset=difficulty_preset,
                player_speed=player_speed,
                initial_lives=initial_lives,
                variant_profile=variant_profile,
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
    variant_profile=None,
):
    baseline_summary = summaries[0]
    return {
        "max_frames": max_frames,
        "random_seed": random_seed,
        "difficulty": difficulty_preset,
        "player_speed": player_speed,
        "initial_lives": initial_lives,
        "variant_profile": variant_profile,
        "best_model": comparison_winner(model_paths, summaries),
        "models": [
            {
                **build_summary_payload(
                    model_path,
                    summary,
                    difficulty_preset=difficulty_preset,
                    player_speed=player_speed,
                    initial_lives=initial_lives,
                    variant_profile=variant_profile,
                ),
                "score_delta": score_delta(summary, baseline_summary),
            }
            for model_path, summary in zip(model_paths, summaries)
        ],
    }


def score_delta(summary, baseline_summary):
    return summary["average_score"] - baseline_summary["average_score"]


def score_breakdown_average(summary, key):
    return summary.get("score_breakdown", {}).get(key, {}).get("average", 0)


def comparison_winner(model_paths, summaries):
    best_index = max(
        range(len(summaries)),
        key=lambda index: (
            summaries[index]["average_score"],
            summaries[index]["average_best_combo"],
            summaries[index]["survival_rate"],
            summaries[index]["average_lives_left"],
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
            "Avg Lives",
            "Survival",
            "Avg Dodges",
            "Ore Bonus",
            "Ore Penalty",
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
                f"{summary['average_lives_left']:.2f}",
                f"{summary['survival_rate']:.1%}",
                f"{score_breakdown_average(summary, 'survival'):.2f}",
                f"{score_breakdown_average(summary, 'ore_bonus'):.2f}",
                f"{score_breakdown_average(summary, 'ore_penalty'):.2f}",
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
    labels = list(args.models)
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
            variant_profile=args.variant_profile,
        )
        for model_path in args.models
    ]
    if args.include_rule_baseline:
        labels.append(policy_label(POLICY_SAFE_RULE))
        summaries.append(
            evaluate_policy(
                POLICY_SAFE_RULE,
                args.games,
                args.max_frames,
                args.random_seed,
                screen,
                difficulty_preset=args.difficulty,
                player_speed=args.player_speed,
                initial_lives=args.lives,
                variant_profile=args.variant_profile,
            )
        )
    if args.include_ore_hunter_baseline:
        labels.append(policy_label(POLICY_ORE_HUNTER))
        summaries.append(
            evaluate_policy(
                POLICY_ORE_HUNTER,
                args.games,
                args.max_frames,
                args.random_seed,
                screen,
                difficulty_preset=args.difficulty,
                player_speed=args.player_speed,
                initial_lives=args.lives,
                variant_profile=args.variant_profile,
            )
        )
    pygame.quit()

    payload = build_comparison_payload(
        labels,
        summaries,
        args.max_frames,
        args.random_seed,
        difficulty_preset=args.difficulty,
        player_speed=args.player_speed,
        initial_lives=args.lives,
        variant_profile=args.variant_profile,
    )
    if args.report:
        write_summary_report(payload, args.report)
    leaderboard_entries = []
    if args.leaderboard:
        _, leaderboard_entries = append_report_to_leaderboard(
            payload,
            leaderboard_path=args.leaderboard,
            source_report=args.report,
            tag=args.leaderboard_tag,
        )

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Difficulty: {args.difficulty}")
        print(f"Player speed: {args.player_speed}")
        print(f"Initial lives: {args.lives}")
        print(f"Variant profile: {args.variant_profile}")
        for line in format_comparison_lines(labels, summaries):
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
