# train_model.py
from collections import Counter
import json

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

DATA_FILE = "game_data.json"
MODEL_FILE = "game_model.pkl"
RANDOM_STATE = 42
TEST_SIZE = 0.2


def load_data(filepath):
    with open(filepath, "r") as f:
        data = json.load(f)

    features = []
    labels = []
    skipped_entries = 0

    for entry in data:
        obstacles = entry["state"].get("obstacles", [])
        action = entry.get("action")

        if not obstacles or action not in ("left", "right"):
            skipped_entries += 1
            continue

        features.append([entry["state"]["player_x"], obstacles[0][0]])
        labels.append(1 if action == "right" else 0)

    return np.array(features), np.array(labels), skipped_entries


def train_model(X, y):
    model = RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE)
    model.fit(X, y)
    return model


def split_data(X, y):
    action_counts = Counter(y)
    stratify = y if min(action_counts.values()) >= 2 else None
    return train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=stratify,
    )


def main():
    X, y, skipped_entries = load_data(DATA_FILE)
    if len(X) < 2:
        raise ValueError("Need at least 2 valid training samples.")

    action_counts = Counter(y)
    if len(action_counts) < 2:
        raise ValueError("Need both left and right samples to train a useful model.")

    X_train, X_test, y_train, y_test = split_data(X, y)
    model = train_model(X_train, y_train)
    accuracy = model.score(X_test, y_test)
    joblib.dump(model, MODEL_FILE)

    print(f"Loaded {len(X)} valid samples from {DATA_FILE} ({skipped_entries} skipped).")
    print(f"Action balance: left={action_counts[0]}, right={action_counts[1]}.")
    print(f"Validation accuracy: {accuracy:.3f}.")
    print(f"Model saved to {MODEL_FILE}.")


if __name__ == "__main__":
    main()
