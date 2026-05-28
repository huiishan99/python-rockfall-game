import argparse
import json

from data_quality import (
    DEFAULT_MAX_SKIPPED_RATIO,
    DEFAULT_MIN_BALANCE_RATIO,
    DEFAULT_MIN_SAMPLES,
    inspect_data_file,
)
from data_store import ORE_TARGET_DATA_FILE, ensure_parent_dir
from leaderboard import DEFAULT_LEADERBOARD_FILE, format_leaderboard_lines, load_leaderboard, ranked_entries

DEFAULT_DASHBOARD_REPORT = "runs/ml_dashboard.json"


def dashboard_recommendations(data_summary, leaderboard):
    recommendations = []
    data_quality = data_summary.get("data_quality", {})
    variant_coverage = data_summary.get("variant_coverage", {})
    objective_coverage = data_summary.get("objective_coverage", {})

    if data_quality.get("status") != "ready":
        recommendations.append("collect_more_balanced_samples")
    if objective_coverage and objective_coverage.get("warnings"):
        recommendations.append("collect_fresh_ore_target_v2_data")
    if variant_coverage.get("warnings"):
        recommendations.append("collect_variant_rich_examples")

    entries = ranked_entries(leaderboard.get("entries", []))
    if not entries:
        recommendations.append("run_training_pipeline")
    else:
        top_model = entries[0].get("model", "")
        if str(top_model).startswith("policy:"):
            recommendations.append("train_model_that_beats_policy_baseline")
        if entries[0].get("average_ore_bonus", 0) <= 0:
            recommendations.append("improve_ore_collection_behavior")

    return sorted(set(recommendations))


def build_dashboard_payload(
    data_path,
    leaderboard_path,
    min_samples=DEFAULT_MIN_SAMPLES,
    min_balance_ratio=DEFAULT_MIN_BALANCE_RATIO,
    max_skipped_ratio=DEFAULT_MAX_SKIPPED_RATIO,
    top=5,
):
    data_summary = inspect_data_file(
        data_path,
        min_samples=min_samples,
        min_balance_ratio=min_balance_ratio,
        max_skipped_ratio=max_skipped_ratio,
    )
    leaderboard = load_leaderboard(leaderboard_path)
    top_entries = ranked_entries(leaderboard.get("entries", []))[:top]
    payload = {
        "data": data_summary,
        "leaderboard": {
            "path": leaderboard_path,
            "entry_count": len(leaderboard.get("entries", [])),
            "top_entries": top_entries,
        },
    }
    payload["recommendations"] = dashboard_recommendations(data_summary, leaderboard)
    return payload


def format_dashboard_lines(payload, top=5):
    data = payload["data"]
    data_quality = data["data_quality"]
    variant_coverage = data["variant_coverage"]
    objective_coverage = data.get("objective_coverage", {})
    lines = [
        "Rockfall ML dashboard",
        f"Data: {data['data']}",
        f"Data quality: {data_quality['status']} ({data['valid_samples']} valid, {data['skipped_entries']} skipped)",
        f"Variant quality: {variant_coverage['status']} ({variant_coverage['recorded_variant_samples']} recorded)",
    ]
    if objective_coverage:
        lines.append(
            "Objective quality: "
            f"{objective_coverage['status']} "
            f"({objective_coverage['target_samples']} {objective_coverage['target_objective']} samples)"
        )
    for label, warnings in (
        ("Data warnings", data_quality.get("warnings", [])),
        ("Variant warnings", variant_coverage.get("warnings", [])),
        ("Objective warnings", objective_coverage.get("warnings", [])),
    ):
        if warnings:
            lines.append(f"{label}: " + ", ".join(warnings))

    leaderboard_payload = {
        "entries": payload["leaderboard"]["top_entries"],
    }
    lines.append("")
    lines.append(f"Leaderboard: {payload['leaderboard']['path']} ({payload['leaderboard']['entry_count']} entries)")
    lines.extend(format_leaderboard_lines(leaderboard_payload, limit=top))

    if payload["recommendations"]:
        lines.append("")
        lines.append("Recommendations: " + ", ".join(payload["recommendations"]))
    return lines


def write_dashboard_report(payload, report_path):
    ensure_parent_dir(report_path)
    with open(report_path, "w") as report_file:
        json.dump(payload, report_file, indent=2, sort_keys=True)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Show a Rockfall ML data and model dashboard.")
    parser.add_argument("--data", default=ORE_TARGET_DATA_FILE, help="Gameplay data JSON file to inspect.")
    parser.add_argument("--leaderboard", default=DEFAULT_LEADERBOARD_FILE, help="Model leaderboard JSON file.")
    parser.add_argument("--report", default=DEFAULT_DASHBOARD_REPORT, help="Optional dashboard JSON report file.")
    parser.add_argument("--top", type=int, default=5, help="Leaderboard rows to include.")
    parser.add_argument("--min-samples", type=int, default=DEFAULT_MIN_SAMPLES, help="Recommended minimum valid samples.")
    parser.add_argument(
        "--min-balance-ratio",
        type=float,
        default=DEFAULT_MIN_BALANCE_RATIO,
        help="Recommended minimum minority-action ratio.",
    )
    parser.add_argument(
        "--max-skipped-ratio",
        type=float,
        default=DEFAULT_MAX_SKIPPED_RATIO,
        help="Recommended maximum skipped-entry ratio.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text.")
    return parser.parse_args(argv)


def validate_args(args):
    if args.top <= 0:
        raise ValueError("--top must be greater than zero.")
    if args.min_samples <= 0:
        raise ValueError("--min-samples must be greater than zero.")
    if not 0 <= args.min_balance_ratio <= 1:
        raise ValueError("--min-balance-ratio must be between 0 and 1.")
    if not 0 <= args.max_skipped_ratio <= 1:
        raise ValueError("--max-skipped-ratio must be between 0 and 1.")


def main(argv=None):
    args = parse_args(argv)
    validate_args(args)
    payload = build_dashboard_payload(
        args.data,
        args.leaderboard,
        min_samples=args.min_samples,
        min_balance_ratio=args.min_balance_ratio,
        max_skipped_ratio=args.max_skipped_ratio,
        top=args.top,
    )
    if args.report:
        write_dashboard_report(payload, args.report)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for line in format_dashboard_lines(payload, top=args.top):
            print(line)
        if args.report:
            print(f"Dashboard saved to {args.report}")
    return 0


def cli(argv=None):
    try:
        return main(argv)
    except ValueError as error:
        print(f"Error: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(cli())
