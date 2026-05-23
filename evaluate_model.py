import argparse
import json
import os
import random
from statistics import mean

from data_store import ensure_parent_dir
from play_with_model import MODEL_FILE
from difficulty import DEFAULT_DIFFICULTY_PRESET, difficulty_preset_names
from policies import choose_policy_action
from settings import (
    DEFAULT_VARIANT_PROFILE,
    INITIAL_LIVES,
    OBSTACLE_VARIANTS,
    PLAYER_SPEED,
    variant_profile_names,
)

DEFAULT_GAMES = 10
DEFAULT_MAX_FRAMES = 3600
DEFAULT_RANDOM_SEED = 42
SCORE_BREAKDOWN_KEYS = ("base", "combo_bonus", "variant_bonus", "risk_bonus")


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
    parser.add_argument("--player-speed", type=int, default=PLAYER_SPEED, help="Player movement speed in pixels.")
    parser.add_argument("--lives", type=int, default=INITIAL_LIVES, help="Initial player lives.")
    parser.add_argument(
        "--variant-profile",
        choices=variant_profile_names(),
        default=DEFAULT_VARIANT_PROFILE,
        help="Rock variant spawn profile.",
    )
    parser.add_argument("--report", help="Optional JSON report file to write.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text.")
    return parser.parse_args(argv)


def run_game(
    model,
    screen,
    max_frames,
    difficulty_preset=DEFAULT_DIFFICULTY_PRESET,
    player_speed=PLAYER_SPEED,
    initial_lives=INITIAL_LIVES,
    variant_profile=DEFAULT_VARIANT_PROFILE,
):
    from play_with_model import predict_action

    return run_game_with_action_provider(
        lambda game: predict_action(model, game),
        screen,
        max_frames,
        difficulty_preset=difficulty_preset,
        player_speed=player_speed,
        initial_lives=initial_lives,
        variant_profile=variant_profile,
    )


def run_policy(
    policy_name,
    screen,
    max_frames,
    difficulty_preset=DEFAULT_DIFFICULTY_PRESET,
    player_speed=PLAYER_SPEED,
    initial_lives=INITIAL_LIVES,
    variant_profile=DEFAULT_VARIANT_PROFILE,
):
    return run_game_with_action_provider(
        lambda game: choose_policy_action(policy_name, game),
        screen,
        max_frames,
        difficulty_preset=difficulty_preset,
        player_speed=player_speed,
        initial_lives=initial_lives,
        variant_profile=variant_profile,
    )


def run_game_with_action_provider(
    action_provider,
    screen,
    max_frames,
    difficulty_preset=DEFAULT_DIFFICULTY_PRESET,
    player_speed=PLAYER_SPEED,
    initial_lives=INITIAL_LIVES,
    variant_profile=DEFAULT_VARIANT_PROFILE,
):
    from game_core import RockfallGame

    game = RockfallGame(
        screen,
        difficulty_preset=difficulty_preset,
        player_speed=player_speed,
        initial_lives=initial_lives,
        variant_profile=variant_profile,
    )
    frames = 0

    while not game.game_over and frames < max_frames:
        game.apply_action(action_provider(game))
        game.update()
        frames += 1

    return {
        "score": game.score,
        "best_combo": game.best_combo,
        "frames": frames,
        "lives": game.lives,
        "timed_out": not game.game_over,
        "variant_stats": game.variant_stats_payload(),
        "score_breakdown": game.score_breakdown_payload(),
    }


def empty_variant_stats():
    return {
        variant_key: {"spawned": 0, "avoided": 0, "hits": 0, "encounters": 0, "avoid_rate": 0}
        for variant_key in OBSTACLE_VARIANTS
    }


def summarize_variant_stats(results):
    variant_stats = empty_variant_stats()
    for result in results:
        for variant_key, stats in result.get("variant_stats", {}).items():
            if variant_key not in variant_stats:
                continue
            for stat_key in ("spawned", "avoided", "hits"):
                variant_stats[variant_key][stat_key] += stats.get(stat_key, 0)

    for stats in variant_stats.values():
        encounters = stats["avoided"] + stats["hits"]
        stats["encounters"] = encounters
        stats["avoid_rate"] = stats["avoided"] / encounters if encounters else 0

    return variant_stats


def summarize_score_breakdown(results):
    totals = {key: 0 for key in SCORE_BREAKDOWN_KEYS}
    for result in results:
        score_breakdown = result.get("score_breakdown", {})
        for key in totals:
            totals[key] += score_breakdown.get(key, 0)

    game_count = len(results)
    return {
        key: {
            "total": totals[key],
            "average": totals[key] / game_count if game_count else 0,
        }
        for key in SCORE_BREAKDOWN_KEYS
    }


def summarize_results(results):
    scores = [result["score"] for result in results]
    best_combos = [result["best_combo"] for result in results]
    frames = [result["frames"] for result in results]
    lives_left = [result["lives"] for result in results]
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
        "average_lives_left": mean(lives_left),
        "best_lives_left": max(lives_left),
        "survival_rate": timeouts / len(results),
        "variant_stats": summarize_variant_stats(results),
        "score_breakdown": summarize_score_breakdown(results),
    }


def format_summary_lines(summary, games_label="Games"):
    lines = [
        f"{games_label}: {summary['games']}",
        f"Average score: {summary['average_score']:.2f}",
        f"Best score: {summary['best_score']}",
        f"Worst score: {summary['worst_score']}",
        f"Average best combo: {summary['average_best_combo']:.2f}",
        f"Best combo: {summary['best_combo']}",
        f"Average frames: {summary['average_frames']:.1f}",
        f"Average lives left: {summary['average_lives_left']:.2f}",
        f"Best lives left: {summary['best_lives_left']}",
        f"Survival rate: {summary['survival_rate']:.1%}",
        f"Timed out games: {summary['timeouts']}",
    ]
    variant_stats = summary.get("variant_stats")
    if variant_stats:
        lines.append("Variant outcomes:")
        for variant_key, stats in variant_stats.items():
            lines.append(
                f"  {variant_key}: "
                f"spawned={stats['spawned']}, "
                f"avoided={stats['avoided']}, "
                f"hits={stats['hits']}, "
                f"avoid_rate={stats['avoid_rate']:.1%}"
            )
    score_breakdown = summary.get("score_breakdown")
    if score_breakdown:
        lines.append("Score breakdown:")
        for key in SCORE_BREAKDOWN_KEYS:
            stats = score_breakdown.get(key, {"total": 0, "average": 0})
            lines.append(f"  {key}: total={stats['total']}, avg={stats['average']:.2f}")
    return lines


def build_summary_payload(
    model_path,
    summary,
    max_frames=None,
    random_seed=None,
    difficulty_preset=None,
    player_speed=None,
    initial_lives=None,
    variant_profile=None,
):
    payload = {"model": model_path, **summary}
    if max_frames is not None:
        payload["max_frames"] = max_frames
    if random_seed is not None:
        payload["random_seed"] = random_seed
    if difficulty_preset is not None:
        payload["difficulty"] = difficulty_preset
    if player_speed is not None:
        payload["player_speed"] = player_speed
    if initial_lives is not None:
        payload["initial_lives"] = initial_lives
    if variant_profile is not None:
        payload["variant_profile"] = variant_profile
    return payload


def write_summary_report(payload, report_path):
    ensure_parent_dir(report_path)
    with open(report_path, "w") as report_file:
        json.dump(payload, report_file, indent=2, sort_keys=True)


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
        results.append(
            run_game(
                model,
                screen,
                args.max_frames,
                difficulty_preset=args.difficulty,
                player_speed=args.player_speed,
                initial_lives=args.lives,
                variant_profile=args.variant_profile,
            )
        )

    summary = summarize_results(results)
    payload = build_summary_payload(
        args.model,
        summary,
        max_frames=args.max_frames,
        random_seed=args.random_seed,
        difficulty_preset=args.difficulty,
        player_speed=args.player_speed,
        initial_lives=args.lives,
        variant_profile=args.variant_profile,
    )
    if args.report:
        write_summary_report(payload, args.report)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Model: {args.model}")
        print(f"Difficulty: {args.difficulty}")
        print(f"Player speed: {args.player_speed}")
        print(f"Initial lives: {args.lives}")
        print(f"Variant profile: {args.variant_profile}")
        for line in format_summary_lines(summary):
            print(line)
        if args.report:
            print(f"Report saved to {args.report}")

    pygame.quit()


if __name__ == "__main__":
    main()
