from collections import Counter

from features import FEATURE_NAMES

DEFAULT_MIN_SAMPLES = 500
DEFAULT_MIN_BALANCE_RATIO = 0.35
DEFAULT_MAX_SKIPPED_RATIO = 0.10


def action_balance_payload(action_counts):
    return {
        "left": int(action_counts.get(0, 0)),
        "right": int(action_counts.get(1, 0)),
    }


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
        "data_quality": quality,
    }
