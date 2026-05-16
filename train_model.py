# train_model.py
import argparse
from collections import Counter

from data_store import GAME_DATA_FILE, load_game_data
from features import FEATURE_NAMES, build_model_features

MODEL_FILE = "game_model.pkl"
RANDOM_STATE = 42
TEST_SIZE = 0.2
N_ESTIMATORS = 100


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Train a Rockfall movement model.")
    parser.add_argument("--data", default=GAME_DATA_FILE, help="Gameplay data JSON file.")
    parser.add_argument("--model", default=MODEL_FILE, help="Output model file.")
    parser.add_argument("--test-size", type=float, default=TEST_SIZE, help="Validation split size.")
    parser.add_argument("--random-state", type=int, default=RANDOM_STATE, help="Random seed.")
    parser.add_argument("--estimators", type=int, default=N_ESTIMATORS, help="Random forest tree count.")
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


def train_model(X, y, estimators, random_state):
    from sklearn.ensemble import RandomForestClassifier

    model = RandomForestClassifier(n_estimators=estimators, random_state=random_state)
    model.fit(X, y)
    return model


def split_data(X, y, test_size, random_state):
    from sklearn.model_selection import train_test_split

    action_counts = Counter(y)
    stratify = y if min(action_counts.values()) >= 2 else None
    return train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify,
    )


def main(argv=None):
    args = parse_args(argv)

    import joblib

    X, y, skipped_entries = load_data(args.data)
    if len(X) < 2:
        raise ValueError("Need at least 2 valid training samples.")

    action_counts = Counter(y)
    if len(action_counts) < 2:
        raise ValueError("Need both left and right samples to train a useful model.")

    X_train, X_test, y_train, y_test = split_data(X, y, args.test_size, args.random_state)
    model = train_model(X_train, y_train, args.estimators, args.random_state)
    accuracy = model.score(X_test, y_test)
    joblib.dump(model, args.model)

    print(f"Loaded {len(X)} valid samples from {args.data} ({skipped_entries} skipped).")
    print(f"Features: {', '.join(FEATURE_NAMES)}.")
    print(f"Action balance: left={action_counts[0]}, right={action_counts[1]}.")
    print(f"Validation accuracy: {accuracy:.3f}.")
    print(f"Model saved to {args.model}.")


if __name__ == "__main__":
    main()
