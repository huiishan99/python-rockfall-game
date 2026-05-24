# train_model.py
import argparse
from collections import Counter

from data_quality import inspect_objective_coverage_file, inspect_variant_coverage_file
from data_store import ORE_TARGET_DATA_FILE, ORE_TARGET_OBJECTIVE, ensure_parent_dir, load_game_data
from features import FEATURE_NAMES, MAX_MODEL_OBSTACLES, build_model_features
from settings import NEAR_MISS_DISTANCE, OBSTACLE_VARIANTS

MODEL_FILE = "game_model.pkl"
RANDOM_STATE = 42
TEST_SIZE = 0.2
N_ESTIMATORS = 100
REWARD_WEIGHTING_NONE = "none"
REWARD_WEIGHTING_SCORE = "score"
REWARD_WEIGHTING_CHOICES = (REWARD_WEIGHTING_NONE, REWARD_WEIGHTING_SCORE)
OBSTACLE_FEATURE_WIDTH = 5
REQUIRE_OBJECTIVE_NONE = "none"
REQUIRE_OBJECTIVE_CHOICES = (REQUIRE_OBJECTIVE_NONE, ORE_TARGET_OBJECTIVE)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Train a Rockfall movement model.")
    parser.add_argument("--data", default=ORE_TARGET_DATA_FILE, help="Gameplay data JSON file.")
    parser.add_argument("--model", default=MODEL_FILE, help="Output model file.")
    parser.add_argument("--test-size", type=float, default=TEST_SIZE, help="Validation split size.")
    parser.add_argument("--random-state", type=int, default=RANDOM_STATE, help="Random seed.")
    parser.add_argument("--estimators", type=int, default=N_ESTIMATORS, help="Random forest tree count.")
    parser.add_argument(
        "--reward-weighting",
        choices=REWARD_WEIGHTING_CHOICES,
        default=REWARD_WEIGHTING_NONE,
        help="Give reward-bearing samples more weight during training.",
    )
    parser.add_argument(
        "--require-objective",
        choices=REQUIRE_OBJECTIVE_CHOICES,
        default=REQUIRE_OBJECTIVE_NONE,
        help="Fail if the training data does not cleanly match the requested objective.",
    )
    return parser.parse_args(argv)


def load_data(filepath):
    import numpy as np

    data = load_game_data(filepath)
    features = []
    labels = []
    skipped_entries = 0

    for entry in data:
        state = entry.get("state", {})
        player_x = state.get("player_x")
        obstacles = state.get("obstacles", [])
        action = entry.get("action")

        if player_x is None or not obstacles or action not in ("left", "right"):
            skipped_entries += 1
            continue

        try:
            features.append(build_model_features(player_x, obstacles))
        except (TypeError, ValueError):
            skipped_entries += 1
            continue

        labels.append(1 if action == "right" else 0)

    return np.array(features), np.array(labels), skipped_entries


def reward_weight_for_features(features):
    weight = 1.0
    for obstacle_index in range(MAX_MODEL_OBSTACLES):
        offset = 1 + obstacle_index * OBSTACLE_FEATURE_WIDTH
        if len(features) < offset + OBSTACLE_FEATURE_WIDTH:
            break

        obstacle_y = features[offset + 1]
        obstacle_dx = features[offset + 2]
        score_bonus = features[offset + 4]
        if obstacle_y == 0:
            continue
        weight += max(0, score_bonus)
        ore_reward = OBSTACLE_VARIANTS["ore"]
        if score_bonus >= ore_reward["score_bonus"] and abs(obstacle_dx) <= NEAR_MISS_DISTANCE:
            weight += ore_reward["near_miss_bonus"]
    return weight


def build_sample_weights(feature_rows, reward_weighting=REWARD_WEIGHTING_NONE):
    if reward_weighting == REWARD_WEIGHTING_NONE:
        return None
    return [reward_weight_for_features(features) for features in feature_rows]


def sample_weight_summary(sample_weights, reward_weighting=REWARD_WEIGHTING_NONE):
    if sample_weights is None:
        return {"mode": reward_weighting}
    return {
        "mode": reward_weighting,
        "min": min(sample_weights),
        "max": max(sample_weights),
        "average": sum(sample_weights) / len(sample_weights) if sample_weights else 0,
    }


def train_model(X, y, estimators, random_state, sample_weights=None):
    from sklearn.ensemble import RandomForestClassifier

    model = RandomForestClassifier(n_estimators=estimators, random_state=random_state)
    model.fit(X, y, sample_weight=sample_weights)
    return model


def stratify_labels(y):
    action_counts = Counter(y)
    return y if min(action_counts.values()) >= 2 else None


def split_data(X, y, test_size, random_state):
    from sklearn.model_selection import train_test_split

    return train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify_labels(y),
    )


def split_training_data(X, y, sample_weights, test_size, random_state):
    if sample_weights is None:
        X_train, X_test, y_train, y_test = split_data(X, y, test_size, random_state)
        return X_train, X_test, y_train, y_test, None

    from sklearn.model_selection import train_test_split

    X_train, X_test, y_train, y_test, train_weights, _ = train_test_split(
        X,
        y,
        sample_weights,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify_labels(y),
    )
    return X_train, X_test, y_train, y_test, train_weights


def save_model(model, path):
    import joblib

    ensure_parent_dir(path)
    joblib.dump(model, path)


def format_variant_coverage_line(variant_coverage):
    variant_counts = variant_coverage["variant_counts"]
    return (
        "Variant coverage: "
        f"recorded={variant_coverage['recorded_variant_samples']}, "
        f"legacy={variant_coverage['legacy_obstacle_samples']}, "
        f"normal={variant_counts['normal']}, "
        f"heavy={variant_counts['heavy']}, "
        f"swift={variant_counts['swift']}, "
        f"ore={variant_counts['ore']}."
    )


def format_objective_coverage_line(objective_coverage):
    return (
        "Objective coverage: "
        f"target={objective_coverage['target_objective']}, "
        f"target_samples={objective_coverage['target_samples']}, "
        f"legacy={objective_coverage['legacy_samples']}, "
        f"other={objective_coverage['other_samples']}, "
        f"ratio={objective_coverage['target_ratio']:.3f}."
    )


def format_sample_weight_line(sample_weights):
    if "average" not in sample_weights:
        return f"Reward weighting: {sample_weights['mode']}."
    return (
        f"Reward weighting: {sample_weights['mode']} "
        f"(min={sample_weights['min']:.2f}, "
        f"max={sample_weights['max']:.2f}, "
        f"avg={sample_weights['average']:.2f})."
    )


def validate_required_objective(objective_coverage, required_objective):
    if required_objective == REQUIRE_OBJECTIVE_NONE:
        return
    if objective_coverage["target_objective"] != required_objective:
        raise ValueError(f"Unsupported required objective: {required_objective}.")
    if objective_coverage["warnings"]:
        raise ValueError(
            "Training data does not cleanly match "
            f"{required_objective}: {', '.join(objective_coverage['warnings'])}."
        )


def main(argv=None):
    args = parse_args(argv)

    X, y, skipped_entries = load_data(args.data)
    variant_coverage = inspect_variant_coverage_file(args.data)
    objective_coverage = inspect_objective_coverage_file(args.data)
    validate_required_objective(objective_coverage, args.require_objective)
    if len(X) < 2:
        raise ValueError("Need at least 2 valid training samples.")

    action_counts = Counter(y)
    if len(action_counts) < 2:
        raise ValueError("Need both left and right samples to train a useful model.")

    sample_weights = build_sample_weights(X, args.reward_weighting)
    weight_summary = sample_weight_summary(sample_weights, args.reward_weighting)
    X_train, X_test, y_train, y_test, train_weights = split_training_data(
        X,
        y,
        sample_weights,
        args.test_size,
        args.random_state,
    )
    model = train_model(X_train, y_train, args.estimators, args.random_state, sample_weights=train_weights)
    accuracy = model.score(X_test, y_test)
    save_model(model, args.model)

    print(f"Loaded {len(X)} valid samples from {args.data} ({skipped_entries} skipped).")
    print(f"Features: {', '.join(FEATURE_NAMES)}.")
    print(f"Action balance: left={action_counts[0]}, right={action_counts[1]}.")
    print(format_variant_coverage_line(variant_coverage))
    print(format_objective_coverage_line(objective_coverage))
    print(format_sample_weight_line(weight_summary))
    if variant_coverage["warnings"]:
        print("Variant warnings: " + ", ".join(variant_coverage["warnings"]) + ".")
    if objective_coverage["warnings"]:
        print("Objective warnings: " + ", ".join(objective_coverage["warnings"]) + ".")
    print(f"Validation accuracy: {accuracy:.3f}.")
    print(f"Model saved to {args.model}.")


if __name__ == "__main__":
    main()
