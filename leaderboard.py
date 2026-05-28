import argparse
import hashlib
import json
from datetime import datetime, timezone

from data_store import ensure_parent_dir

DEFAULT_LEADERBOARD_FILE = "runs/model_leaderboard.json"
LEADERBOARD_SCHEMA_VERSION = 1


def utc_now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json_file(path):
    with open(path, "r") as json_file:
        return json.load(json_file)


def empty_leaderboard():
    return {
        "schema_version": LEADERBOARD_SCHEMA_VERSION,
        "entries": [],
    }


def load_leaderboard(path=DEFAULT_LEADERBOARD_FILE):
    try:
        payload = load_json_file(path)
    except FileNotFoundError:
        return empty_leaderboard()
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a leaderboard object.")
    payload.setdefault("schema_version", LEADERBOARD_SCHEMA_VERSION)
    payload.setdefault("entries", [])
    if not isinstance(payload["entries"], list):
        raise ValueError(f"{path} leaderboard entries must be a list.")
    return payload


def save_leaderboard(payload, path=DEFAULT_LEADERBOARD_FILE):
    ensure_parent_dir(path)
    with open(path, "w") as leaderboard_file:
        json.dump(payload, leaderboard_file, indent=2, sort_keys=True)


def score_breakdown_average(model_result, key):
    return model_result.get("score_breakdown", {}).get(key, {}).get("average", 0)


def entry_identity(entry):
    identity_keys = (
        "source_report",
        "source_kind",
        "tag",
        "model",
        "difficulty",
        "variant_profile",
        "games",
        "max_frames",
        "random_seed",
        "player_speed",
        "initial_lives",
    )
    return {key: entry.get(key) for key in identity_keys}


def entry_id(entry):
    encoded = json.dumps(entry_identity(entry), sort_keys=True).encode("utf-8")
    return hashlib.sha1(encoded).hexdigest()[:12]


def build_entry(model_result, settings, source_kind, source_report=None, tag=None, created_at=None):
    entry = {
        "created_at": created_at or utc_now_iso(),
        "source_kind": source_kind,
        "source_report": source_report,
        "tag": tag,
        "model": model_result["model"],
        "difficulty": settings.get("difficulty"),
        "variant_profile": settings.get("variant_profile"),
        "games": model_result.get("games", settings.get("games")),
        "max_frames": settings.get("max_frames", model_result.get("max_frames")),
        "random_seed": settings.get("random_seed", model_result.get("random_seed")),
        "player_speed": settings.get("player_speed", model_result.get("player_speed")),
        "initial_lives": settings.get("initial_lives", model_result.get("initial_lives")),
        "average_score": model_result.get("average_score", 0),
        "best_score": model_result.get("best_score", 0),
        "worst_score": model_result.get("worst_score", 0),
        "average_frames": model_result.get("average_frames", 0),
        "average_lives_left": model_result.get("average_lives_left", 0),
        "survival_rate": model_result.get("survival_rate", 0),
        "average_best_combo": model_result.get("average_best_combo", 0),
        "best_combo": model_result.get("best_combo", 0),
        "timeouts": model_result.get("timeouts", 0),
        "score_delta": model_result.get("score_delta", 0),
        "average_dodges": score_breakdown_average(model_result, "survival"),
        "average_ore_bonus": score_breakdown_average(model_result, "ore_bonus"),
        "average_ore_penalty": score_breakdown_average(model_result, "ore_penalty"),
    }
    entry["id"] = entry_id(entry)
    return entry


def comparison_settings(payload):
    return {
        "games": payload.get("games"),
        "max_frames": payload.get("max_frames"),
        "random_seed": payload.get("random_seed"),
        "difficulty": payload.get("difficulty"),
        "player_speed": payload.get("player_speed"),
        "initial_lives": payload.get("initial_lives"),
        "variant_profile": payload.get("variant_profile"),
    }


def normalize_comparison_entries(payload, source_kind, source_report=None, tag=None, created_at=None):
    settings = comparison_settings(payload)
    return [
        build_entry(
            model_result,
            settings,
            source_kind,
            source_report=source_report,
            tag=tag,
            created_at=created_at,
        )
        for model_result in payload.get("models", [])
    ]


def normalize_model_report_entries(payload, source_report=None, tag=None, created_at=None):
    settings = dict(payload.get("settings", {}))
    entries = []
    for profile_name, profile_report in payload.get("profiles", {}).items():
        profile_settings = comparison_settings(profile_report)
        for key, value in settings.items():
            if profile_settings.get(key) is None:
                profile_settings[key] = value
        profile_settings["variant_profile"] = profile_name
        for model_result in profile_report.get("models", []):
            entries.append(
                build_entry(
                    model_result,
                    profile_settings,
                    "model_report",
                    source_report=source_report,
                    tag=tag,
                    created_at=created_at,
                )
            )
    return entries


def normalize_evaluation_entry(payload, source_report=None, tag=None, created_at=None):
    settings = {
        "games": payload.get("games"),
        "max_frames": payload.get("max_frames"),
        "random_seed": payload.get("random_seed"),
        "difficulty": payload.get("difficulty"),
        "player_speed": payload.get("player_speed"),
        "initial_lives": payload.get("initial_lives"),
        "variant_profile": payload.get("variant_profile"),
    }
    return [
        build_entry(
            payload,
            settings,
            "evaluation",
            source_report=source_report,
            tag=tag,
            created_at=created_at,
        )
    ]


def normalize_report_entries(payload, source_report=None, tag=None, created_at=None):
    if "comparison" in payload and isinstance(payload["comparison"], dict):
        return normalize_comparison_entries(
            payload["comparison"],
            "training_pipeline",
            source_report=source_report,
            tag=tag,
            created_at=created_at,
        )
    if "profiles" in payload and isinstance(payload["profiles"], dict):
        return normalize_model_report_entries(
            payload,
            source_report=source_report,
            tag=tag,
            created_at=created_at,
        )
    if "models" in payload and isinstance(payload["models"], list):
        return normalize_comparison_entries(
            payload,
            "comparison",
            source_report=source_report,
            tag=tag,
            created_at=created_at,
        )
    if "model" in payload and "average_score" in payload:
        return normalize_evaluation_entry(
            payload,
            source_report=source_report,
            tag=tag,
            created_at=created_at,
        )
    raise ValueError("Report payload is not a supported Rockfall evaluation report.")


def ranked_entries(entries):
    return sorted(
        entries,
        key=lambda entry: (
            entry.get("average_score", 0),
            entry.get("survival_rate", 0),
            entry.get("average_lives_left", 0),
            entry.get("average_frames", 0),
            entry.get("average_ore_bonus", 0),
        ),
        reverse=True,
    )


def upsert_entries(leaderboard, entries):
    by_id = {entry["id"]: entry for entry in leaderboard.get("entries", [])}
    for entry in entries:
        by_id[entry["id"]] = entry
    leaderboard["entries"] = ranked_entries(list(by_id.values()))
    return leaderboard


def append_report_to_leaderboard(
    report_payload,
    leaderboard_path=DEFAULT_LEADERBOARD_FILE,
    source_report=None,
    tag=None,
    created_at=None,
):
    entries = normalize_report_entries(
        report_payload,
        source_report=source_report,
        tag=tag,
        created_at=created_at,
    )
    leaderboard = load_leaderboard(leaderboard_path)
    upsert_entries(leaderboard, entries)
    save_leaderboard(leaderboard, leaderboard_path)
    return leaderboard, entries


def format_leaderboard_lines(leaderboard, limit=10):
    entries = ranked_entries(leaderboard.get("entries", []))[:limit]
    if not entries:
        return ["Model leaderboard is empty."]

    rows = [
        (
            "#",
            "Model",
            "Profile",
            "Avg",
            "Ore",
            "Penalty",
            "Survival",
            "Frames",
            "Lives",
            "Source",
        )
    ]
    for index, entry in enumerate(entries, start=1):
        rows.append(
            (
                str(index),
                entry["model"],
                str(entry.get("variant_profile") or "-"),
                f"{entry.get('average_score', 0):.2f}",
                f"{entry.get('average_ore_bonus', 0):.2f}",
                f"{entry.get('average_ore_penalty', 0):.2f}",
                f"{entry.get('survival_rate', 0):.1%}",
                f"{entry.get('average_frames', 0):.1f}",
                f"{entry.get('average_lives_left', 0):.2f}",
                entry.get("tag") or entry.get("source_kind") or "-",
            )
        )

    widths = [max(len(row[index]) for row in rows) for index in range(len(rows[0]))]
    return [
        "  ".join(cell.ljust(widths[index]) for index, cell in enumerate(row))
        for row in rows
    ]


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Append Rockfall reports to a model leaderboard.")
    parser.add_argument("--report", help="Evaluation, comparison, model-report, or training-pipeline JSON report.")
    parser.add_argument("--leaderboard", default=DEFAULT_LEADERBOARD_FILE, help="Leaderboard JSON file.")
    parser.add_argument("--tag", help="Optional label for this run, such as v0.8.5-smoke.")
    parser.add_argument("--limit", type=int, default=10, help="Rows to print.")
    parser.add_argument("--json", action="store_true", help="Print leaderboard JSON instead of a table.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.limit <= 0:
        raise ValueError("--limit must be greater than zero.")

    if args.report:
        report_payload = load_json_file(args.report)
        leaderboard, _ = append_report_to_leaderboard(
            report_payload,
            leaderboard_path=args.leaderboard,
            source_report=args.report,
            tag=args.tag,
        )
    else:
        leaderboard = load_leaderboard(args.leaderboard)

    if args.json:
        print(json.dumps(leaderboard, indent=2, sort_keys=True))
    else:
        for line in format_leaderboard_lines(leaderboard, limit=args.limit):
            print(line)
    return 0


def cli(argv=None):
    try:
        return main(argv)
    except ValueError as error:
        print(f"Error: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(cli())
