from collections import Counter

from data_store import ORE_TARGET_OBJECTIVE, load_game_data
from features import FEATURE_NAMES, MAX_MODEL_OBSTACLES
from settings import DEFAULT_OBSTACLE_VARIANT, OBSTACLE_VARIANTS

DEFAULT_MIN_SAMPLES = 500
DEFAULT_MIN_BALANCE_RATIO = 0.35
DEFAULT_MAX_SKIPPED_RATIO = 0.10
LEGACY_OBJECTIVE = "legacy"


def entry_objective(entry):
    objective = entry.get("objective")
    if isinstance(objective, str) and objective:
        return objective
    return LEGACY_OBJECTIVE


def is_training_candidate(entry):
    state = entry.get("state", {})
    player_x = state.get("player_x")
    obstacles = state.get("obstacles", [])
    action = entry.get("action")

    try:
        int(player_x)
    except (TypeError, ValueError):
        return False
    return bool(obstacles) and action in ("left", "right")


def action_balance_payload(action_counts):
    return {
        "left": int(action_counts.get(0, 0)),
        "right": int(action_counts.get(1, 0)),
    }


def recorded_variant_for_obstacle(obstacle):
    try:
        if len(obstacle) < 3:
            return None
    except TypeError:
        return None

    variant_key = obstacle[2]
    if isinstance(variant_key, str) and variant_key in OBSTACLE_VARIANTS:
        return variant_key
    return None


def ranked_training_obstacle_variants(obstacles, limit=MAX_MODEL_OBSTACLES):
    valid_obstacles = []
    for obstacle in obstacles:
        try:
            if len(obstacle) < 2:
                continue
            int(obstacle[0])
            obstacle_y = int(obstacle[1])
        except (TypeError, ValueError):
            continue
        valid_obstacles.append((obstacle_y, recorded_variant_for_obstacle(obstacle)))

    return [
        variant_key
        for _, variant_key in sorted(valid_obstacles, key=lambda obstacle: obstacle[0], reverse=True)[:limit]
    ]


def variant_coverage_summary(entries):
    variant_counts = {variant_key: 0 for variant_key in OBSTACLE_VARIANTS}
    legacy_obstacle_samples = 0
    invalid_obstacle_samples = 0
    total_obstacle_samples = 0

    for entry in entries:
        if not is_training_candidate(entry):
            continue

        state = entry.get("state", {})
        obstacles = state.get("obstacles", [])

        variant_keys = ranked_training_obstacle_variants(obstacles)
        if not variant_keys:
            invalid_obstacle_samples += 1
            continue

        for variant_key in variant_keys:
            total_obstacle_samples += 1
            if variant_key is None:
                legacy_obstacle_samples += 1
            else:
                variant_counts[variant_key] += 1

    recorded_variant_samples = sum(variant_counts.values())
    variant_sample_ratio = recorded_variant_samples / total_obstacle_samples if total_obstacle_samples else 0
    warnings = []
    if recorded_variant_samples == 0:
        warnings.append("no_recorded_variant_samples")
    else:
        for variant_key in OBSTACLE_VARIANTS:
            if variant_key != DEFAULT_OBSTACLE_VARIANT and variant_counts[variant_key] == 0:
                warnings.append(f"missing_{variant_key}_samples")

    return {
        "status": "variant_ready" if not warnings else "needs_variant_data",
        "warnings": warnings,
        "variant_counts": variant_counts,
        "total_obstacle_samples": total_obstacle_samples,
        "recorded_variant_samples": recorded_variant_samples,
        "legacy_obstacle_samples": legacy_obstacle_samples,
        "invalid_obstacle_samples": invalid_obstacle_samples,
        "variant_sample_ratio": variant_sample_ratio,
    }


def inspect_variant_coverage_file(data_path):
    return variant_coverage_summary(load_game_data(data_path))


def objective_coverage_summary(entries, target_objective=ORE_TARGET_OBJECTIVE):
    objective_counts = Counter()
    source_counts = Counter()
    valid_training_samples = 0

    for entry in entries:
        if not is_training_candidate(entry):
            continue

        valid_training_samples += 1
        objective_counts[entry_objective(entry)] += 1
        source = entry.get("source")
        if isinstance(source, str) and source:
            source_counts[source] += 1

    target_samples = objective_counts.get(target_objective, 0)
    legacy_samples = objective_counts.get(LEGACY_OBJECTIVE, 0)
    other_samples = valid_training_samples - target_samples - legacy_samples
    target_ratio = target_samples / valid_training_samples if valid_training_samples else 0
    warnings = []

    if target_samples == 0:
        warnings.append("no_ore_target_samples")
    if legacy_samples > 0 and target_samples > 0:
        warnings.append("mixed_legacy_and_ore_target_samples")
    if other_samples > 0:
        warnings.append("unknown_objective_samples")

    return {
        "status": "objective_ready" if not warnings else "needs_objective_data",
        "warnings": warnings,
        "target_objective": target_objective,
        "target_samples": target_samples,
        "legacy_samples": legacy_samples,
        "other_samples": other_samples,
        "valid_training_samples": valid_training_samples,
        "target_ratio": target_ratio,
        "objective_counts": dict(objective_counts),
        "source_counts": dict(source_counts),
    }


def inspect_objective_coverage_file(data_path):
    return objective_coverage_summary(load_game_data(data_path))


def data_quality_summary(
    valid_samples,
    skipped_entries,
    action_counts,
    min_samples,
    min_balance_ratio,
    max_skipped_ratio,
):
    total_entries = valid_samples + skipped_entries
    skipped_ratio = skipped_entries / total_entries if total_entries else 0
    minority_count = min(action_counts.values()) if action_counts else 0
    balance_ratio = minority_count / valid_samples if valid_samples else 0
    warnings = []

    if valid_samples < min_samples:
        warnings.append(f"valid_samples_below_{min_samples}")
    if balance_ratio < min_balance_ratio:
        warnings.append(f"action_balance_below_{min_balance_ratio:.2f}")
    if skipped_ratio > max_skipped_ratio:
        warnings.append(f"skipped_ratio_above_{max_skipped_ratio:.2f}")

    return {
        "status": "ready" if not warnings else "needs_more_data",
        "warnings": warnings,
        "valid_samples": valid_samples,
        "skipped_entries": skipped_entries,
        "skipped_ratio": skipped_ratio,
        "balance_ratio": balance_ratio,
        "min_samples": min_samples,
        "min_balance_ratio": min_balance_ratio,
        "max_skipped_ratio": max_skipped_ratio,
    }


def inspect_data_file(
    data_path,
    min_samples=DEFAULT_MIN_SAMPLES,
    min_balance_ratio=DEFAULT_MIN_BALANCE_RATIO,
    max_skipped_ratio=DEFAULT_MAX_SKIPPED_RATIO,
):
    from train_model import load_data

    data = load_game_data(data_path)
    X, y, skipped_entries = load_data(data_path)
    action_counts = Counter(y)
    quality = data_quality_summary(
        len(X),
        skipped_entries,
        action_counts,
        min_samples,
        min_balance_ratio,
        max_skipped_ratio,
    )

    return {
        "data": data_path,
        "valid_samples": len(X),
        "skipped_entries": skipped_entries,
        "features": list(FEATURE_NAMES),
        "action_balance": action_balance_payload(action_counts),
        "variant_coverage": variant_coverage_summary(data),
        "objective_coverage": objective_coverage_summary(data),
        "data_quality": quality,
    }
