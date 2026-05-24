import argparse
import json
import os
import random

from data_quality import inspect_data_file
from data_store import append_game_data, ensure_parent_dir
from difficulty import DEFAULT_DIFFICULTY_PRESET, difficulty_preset_names
from evaluate_model import DEFAULT_RANDOM_SEED, format_summary_lines, summarize_results
from policies import POLICY_SAFE_RULE, built_in_policy_names, choose_policy_action
from settings import (
    INITIAL_LIVES,
    PLAYER_SPEED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    variant_profile_names,
)

DEFAULT_POLICY_DATA_FILE = "runs/policy_variant_rich.json"
DEFAULT_POLICY_GAMES = 3
DEFAULT_POLICY_MAX_FRAMES = 900
DEFAULT_POLICY_VARIANT_PROFILE = "variant-rich"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Collect Rockfall training samples from a built-in policy.")
    parser.add_argument("--data", default=DEFAULT_POLICY_DATA_FILE, help="Gameplay data JSON file to append.")
    parser.add_argument(
        "--policy",
        choices=built_in_policy_names(),
        default=POLICY_SAFE_RULE,
        help="Built-in policy to record.",
    )
    parser.add_argument("--games", type=int, default=DEFAULT_POLICY_GAMES, help="Games to collect.")
    parser.add_argument("--max-frames", type=int, default=DEFAULT_POLICY_MAX_FRAMES, help="Frame limit per game.")
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
        default=DEFAULT_POLICY_VARIANT_PROFILE,
        help="Rock variant spawn profile.",
    )
    parser.add_argument("--report", help="Optional JSON collection report file to write.")
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


def collect_game_samples(game, policy_name, max_frames):
    samples = []
    frames = 0
    while not game.game_over and frames < max_frames:
        action = choose_policy_action(policy_name, game)
        samples.append({"state": game.snapshot(), "action": action})
        game.apply_action(action)
        game.update()
        frames += 1

    return samples, {
        "score": game.score,
        "best_combo": game.best_combo,
        "frames": frames,
        "lives": game.lives,
        "timed_out": not game.game_over,
        "variant_stats": game.variant_stats_payload(),
        "score_breakdown": game.score_breakdown_payload(),
    }


def collect_policy_samples(
    policy_name,
    games,
    max_frames,
    random_seed,
    difficulty_preset=DEFAULT_DIFFICULTY_PRESET,
    player_speed=PLAYER_SPEED,
    initial_lives=INITIAL_LIVES,
    variant_profile=DEFAULT_POLICY_VARIANT_PROFILE,
):
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame

    from game_core import RockfallGame

    pygame.font.init()
    screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    samples = []
    results = []
    try:
        for game_index in range(games):
            random.seed(random_seed + game_index)
            game = RockfallGame(
                screen,
                difficulty_preset=difficulty_preset,
                player_speed=player_speed,
                initial_lives=initial_lives,
                variant_profile=variant_profile,
            )
            game_samples, result = collect_game_samples(game, policy_name, max_frames)
            samples.extend(game_samples)
            results.append(result)
    finally:
        pygame.quit()

    return samples, summarize_results(results)


def build_collection_payload(
    data_path,
    policy_name,
    samples_written,
    previous_count,
    total_count,
    summary,
    data_summary,
    games,
    max_frames,
    random_seed,
    difficulty_preset,
    player_speed,
    initial_lives,
    variant_profile,
):
    return {
        "data": data_path,
        "policy": policy_name,
        "samples_written": samples_written,
        "previous_samples": previous_count,
        "total_samples": total_count,
        "settings": {
            "games": games,
            "max_frames": max_frames,
            "random_seed": random_seed,
            "difficulty": difficulty_preset,
            "player_speed": player_speed,
            "initial_lives": initial_lives,
            "variant_profile": variant_profile,
        },
        "collection_summary": summary,
        "data_summary": data_summary,
    }


def format_collection_lines(payload):
    variant_coverage = payload["data_summary"]["variant_coverage"]
    lines = [
        "Policy data collection",
        f"Policy: {payload['policy']}",
        f"Data: {payload['data']}",
        (
            f"Samples written: {payload['samples_written']} "
            f"({payload['previous_samples']} -> {payload['total_samples']})"
        ),
        (
            "Variant coverage: "
            f"recorded={variant_coverage['recorded_variant_samples']}, "
            f"legacy={variant_coverage['legacy_obstacle_samples']}, "
            f"quality={variant_coverage['status']}"
        ),
    ]
    if variant_coverage["warnings"]:
        lines.append("Variant warnings: " + ", ".join(variant_coverage["warnings"]))
    lines.extend(format_summary_lines(payload["collection_summary"], games_label="Collected games"))
    return lines


def write_collection_report(payload, report_path):
    ensure_parent_dir(report_path)
    with open(report_path, "w") as report_file:
        json.dump(payload, report_file, indent=2, sort_keys=True)


def main(argv=None):
    args = parse_args(argv)
    validate_args(args)
    samples, summary = collect_policy_samples(
        args.policy,
        args.games,
        args.max_frames,
        args.random_seed,
        difficulty_preset=args.difficulty,
        player_speed=args.player_speed,
        initial_lives=args.lives,
        variant_profile=args.variant_profile,
    )
    previous_count, total_count = append_game_data(samples, args.data)
    data_summary = inspect_data_file(args.data)
    payload = build_collection_payload(
        args.data,
        args.policy,
        len(samples),
        previous_count,
        total_count,
        summary,
        data_summary,
        args.games,
        args.max_frames,
        args.random_seed,
        args.difficulty,
        args.player_speed,
        args.lives,
        args.variant_profile,
    )
    if args.report:
        write_collection_report(payload, args.report)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for line in format_collection_lines(payload):
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
