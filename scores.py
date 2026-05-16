import json

HIGH_SCORES_FILE = "high_scores.json"


def load_high_scores(path=HIGH_SCORES_FILE):
    try:
        with open(path, "r") as f:
            raw_scores = json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

    if not isinstance(raw_scores, dict):
        return {}

    scores = {}
    for mode_key, score in raw_scores.items():
        try:
            scores[str(mode_key)] = max(0, int(score))
        except (TypeError, ValueError):
            continue
    return scores


def get_high_score(mode_key, path=HIGH_SCORES_FILE):
    return load_high_scores(path).get(mode_key, 0)


def record_high_score(mode_key, score, path=HIGH_SCORES_FILE):
    scores = load_high_scores(path)
    current_high_score = scores.get(mode_key, 0)

    if score <= current_high_score:
        return current_high_score, False

    scores[mode_key] = score
    with open(path, "w") as f:
        json.dump(scores, f, indent=2)

    return score, True
