import argparse
import json

from data_quality import (
    DEFAULT_MAX_SKIPPED_RATIO,
    DEFAULT_MIN_BALANCE_RATIO,
    DEFAULT_MIN_SAMPLES,
    inspect_data_file,
)
from data_store import GAME_DATA_FILE, ensure_parent_dir


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Inspect Rockfall training data quality.")
    parser.add_argument("--data", default=GAME_DATA_FILE, help="Gameplay data JSON file.")
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
    parser.add_argument("--report", help="Optional JSON report file to write.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text.")
    return parser.parse_args(argv)


def validate_args(args):
    if args.min_samples <= 0:
        raise ValueError("--min-samples must be greater than zero.")
    if not 0 <= args.min_balance_ratio <= 1:
        raise ValueError("--min-balance-ratio must be between 0 and 1.")
    if not 0 <= args.max_skipped_ratio <= 1:
        raise ValueError("--max-skipped-ratio must be between 0 and 1.")


def write_inspection_report(payload, report_path):
    ensure_parent_dir(report_path)
    with open(report_path, "w") as report_file:
        json.dump(payload, report_file, indent=2, sort_keys=True)


def format_inspection_lines(payload):
    quality = payload["data_quality"]
    lines = [
        f"Data: {payload['data']}",
        f"Valid samples: {payload['valid_samples']} ({payload['skipped_entries']} skipped)",
        "Features: " + ", ".join(payload["features"]),
        (
            "Action balance: "
            f"left={payload['action_balance']['left']}, "
            f"right={payload['action_balance']['right']}"
        ),
        f"Skipped ratio: {quality['skipped_ratio']:.3f}",
        f"Balance ratio: {quality['balance_ratio']:.3f}",
        f"Data quality: {quality['status']}",
    ]
    variant_coverage = payload.get("variant_coverage")
    if variant_coverage:
        variant_counts = variant_coverage["variant_counts"]
        lines.extend(
            [
                (
                    "Variant coverage: "
                    f"recorded={variant_coverage['recorded_variant_samples']}, "
                    f"legacy={variant_coverage['legacy_obstacle_samples']}, "
                    f"ratio={variant_coverage['variant_sample_ratio']:.3f}"
                ),
                (
                    "Variant counts: "
                    f"normal={variant_counts['normal']}, "
                    f"heavy={variant_counts['heavy']}, "
                    f"swift={variant_counts['swift']}, "
                    f"ore={variant_counts['ore']}"
                ),
                f"Variant quality: {variant_coverage['status']}",
            ]
        )
        if variant_coverage["warnings"]:
            lines.append("Variant warnings: " + ", ".join(variant_coverage["warnings"]))
    if quality["warnings"]:
        lines.append("Data quality warnings: " + ", ".join(quality["warnings"]))
    return lines


def main(argv=None):
    args = parse_args(argv)
    validate_args(args)
    payload = inspect_data_file(
        args.data,
        min_samples=args.min_samples,
        min_balance_ratio=args.min_balance_ratio,
        max_skipped_ratio=args.max_skipped_ratio,
    )
    if args.report:
        write_inspection_report(payload, args.report)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for line in format_inspection_lines(payload):
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
