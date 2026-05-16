import random

from settings import (
    MAX_DIFFICULTY_LEVEL,
    OBSTACLE_WIDTH,
    SCREEN_WIDTH,
    SPAWN_LANE_COUNT,
)


def build_spawn_lanes(screen_width=SCREEN_WIDTH, obstacle_width=OBSTACLE_WIDTH, lane_count=SPAWN_LANE_COUNT):
    if lane_count <= 1:
        return [(screen_width - obstacle_width) // 2]

    max_x = screen_width - obstacle_width
    step = max_x / (lane_count - 1)
    return [round(step * lane_index) for lane_index in range(lane_count)]


def minimum_lane_gap_for_level(level):
    pressure = max(0, int(level) - 1)
    gap = 2 - (pressure // 4)
    return max(0, gap)


def choose_spawn_x(previous_x=None, level=1, rng=random):
    lanes = build_spawn_lanes()
    if previous_x is None:
        return rng.choice(lanes)

    lane_gap = minimum_lane_gap_for_level(level)
    if lane_gap <= 0 or int(level) >= MAX_DIFFICULTY_LEVEL:
        return rng.choice(lanes)

    nearest_previous_lane = min(range(len(lanes)), key=lambda index: abs(lanes[index] - previous_x))
    candidates = [
        lane
        for lane_index, lane in enumerate(lanes)
        if abs(lane_index - nearest_previous_lane) >= lane_gap
    ]
    return rng.choice(candidates or lanes)
