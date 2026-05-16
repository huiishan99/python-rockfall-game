import json
import os

GAME_DATA_FILE = "game_data.json"


def load_game_data(path=GAME_DATA_FILE):
    try:
        with open(path, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} is not valid JSON.") from exc

    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a list of gameplay entries.")

    return data


def append_game_data(new_entries, path=GAME_DATA_FILE):
    existing_entries = load_game_data(path)

    if not new_entries:
        current_count = len(existing_entries)
        return current_count, current_count

    previous_count = len(existing_entries)
    combined_entries = existing_entries + list(new_entries)
    parent_dir = os.path.dirname(path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    with open(path, "w") as f:
        json.dump(combined_entries, f)

    return previous_count, len(combined_entries)
