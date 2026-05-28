import argparse
import json
import os
import re

from data_store import ensure_parent_dir

DEFAULT_TRACE_STRIDE = 30
DEFAULT_OBSTACLE_LIMIT = 5


def sanitize_trace_label(label):
    clean_label = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(label)).strip("-")
    return clean_label or "run"


def build_trace_payload(label, game_index, seed, settings):
    return {
        "schema_version": 1,
        "label": label,
        "game_index": game_index,
        "seed": seed,
        "settings": dict(settings),
        "frames": [],
        "result": None,
    }


def obstacle_payload(game, limit=DEFAULT_OBSTACLE_LIMIT):
    obstacles = []
    for obstacle in game.obstacles[:limit]:
        obstacles.append(
            {
                "x": obstacle[0],
                "y": obstacle[1],
                "variant": game.obstacle_variant(obstacle),
            }
        )
    return obstacles


def trace_frame_payload(game, frame, action, events=None, obstacle_limit=DEFAULT_OBSTACLE_LIMIT):
    return {
        "frame": frame,
        "action": action,
        "player_x": game.player_x,
        "score": game.score,
        "lives": game.lives,
        "combo": game.combo,
        "best_combo": game.best_combo,
        "dodges": game.dodges,
        "level": game.difficulty_level,
        "events": list(events or []),
        "obstacles": obstacle_payload(game, limit=obstacle_limit),
    }


def should_record_frame(frame, stride, events=None):
    if frame <= 1:
        return True
    if events:
        return True
    return frame % stride == 0


def record_trace_frame(trace, game, frame, action, events=None, stride=DEFAULT_TRACE_STRIDE):
    if not should_record_frame(frame, stride, events=events):
        return False

    trace["frames"].append(trace_frame_payload(game, frame, action, events=events))
    return True


def finalize_trace(trace, result):
    trace["result"] = {
        "score": result["score"],
        "best_combo": result["best_combo"],
        "frames": result["frames"],
        "lives": result["lives"],
        "timed_out": result["timed_out"],
        "variant_stats": result.get("variant_stats", {}),
        "score_breakdown": result.get("score_breakdown", {}),
    }
    return trace


def trace_file_name(trace):
    label = sanitize_trace_label(trace.get("label", "run"))
    game_index = trace.get("game_index", 0)
    seed = trace.get("seed", "seed")
    return f"{label}-game-{game_index + 1}-seed-{seed}.json"


def write_trace(trace, trace_dir):
    os.makedirs(trace_dir, exist_ok=True)
    trace_path = os.path.join(trace_dir, trace_file_name(trace))
    with open(trace_path, "w") as trace_file:
        json.dump(trace, trace_file, indent=2, sort_keys=True)
    return trace_path


def load_trace(trace_path):
    with open(trace_path, "r") as trace_file:
        trace = json.load(trace_file)
    if not isinstance(trace, dict):
        raise ValueError(f"{trace_path} must contain a trace object.")
    return trace


def write_trace_report(trace, report_path):
    ensure_parent_dir(report_path)
    with open(report_path, "w") as report_file:
        json.dump(trace, report_file, indent=2, sort_keys=True)


def event_summary(trace):
    counts = {}
    for frame in trace.get("frames", []):
        for event in frame.get("events", []):
            counts[event] = counts.get(event, 0) + 1
    return counts


def format_trace_lines(trace, limit=20):
    result = trace.get("result") or {}
    settings = trace.get("settings", {})
    event_counts = event_summary(trace)
    lines = [
        "Rockfall replay trace",
        f"Label: {trace.get('label')}",
        f"Game: {trace.get('game_index', 0) + 1}  Seed: {trace.get('seed')}",
        (
            "Settings: "
            f"difficulty={settings.get('difficulty')}, "
            f"variant_profile={settings.get('variant_profile')}, "
            f"speed={settings.get('player_speed')}, "
            f"lives={settings.get('initial_lives')}, "
            f"max_frames={settings.get('max_frames')}"
        ),
        (
            "Result: "
            f"score={result.get('score')}, "
            f"frames={result.get('frames')}, "
            f"lives={result.get('lives')}, "
            f"timed_out={result.get('timed_out')}"
        ),
    ]
    if event_counts:
        lines.append(
            "Events: "
            + ", ".join(f"{event}={count}" for event, count in sorted(event_counts.items()))
        )

    frames = trace.get("frames", [])
    shown_frames = frames[:limit]
    if shown_frames:
        lines.append("")
        lines.append(f"Frames shown: {len(shown_frames)} of {len(frames)}")
        for frame in shown_frames:
            obstacle_text = ", ".join(
                f"{obstacle['variant']}@({obstacle['x']},{obstacle['y']})"
                for obstacle in frame.get("obstacles", [])[:2]
            )
            if not obstacle_text:
                obstacle_text = "none"
            event_text = ",".join(frame.get("events", [])) or "-"
            lines.append(
                f"  f={frame['frame']:>4} "
                f"act={frame['action']:<5} "
                f"x={frame['player_x']:>3} "
                f"score={frame['score']:>3} "
                f"lives={frame['lives']} "
                f"combo={frame['combo']:>2} "
                f"events={event_text} "
                f"rocks={obstacle_text}"
            )
    if len(frames) > limit:
        lines.append(f"... {len(frames) - limit} more recorded frames")
    return lines


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Inspect a Rockfall replay trace JSON file.")
    parser.add_argument("trace", help="Trace JSON file created by evaluate_model.py --trace-dir.")
    parser.add_argument("--limit", type=int, default=20, help="Maximum recorded frames to print.")
    parser.add_argument("--json", action="store_true", help="Print the trace JSON instead of a text summary.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.limit <= 0:
        raise ValueError("--limit must be greater than zero.")

    trace = load_trace(args.trace)
    if args.json:
        print(json.dumps(trace, indent=2, sort_keys=True))
    else:
        for line in format_trace_lines(trace, limit=args.limit):
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
