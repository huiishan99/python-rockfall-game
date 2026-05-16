from dataclasses import dataclass

from settings import (
    DIFFICULTY_INTERVAL_FRAMES,
    INITIAL_DIFFICULTY_LEVEL,
    INITIAL_OBSTACLE_SPEED,
    MAX_DIFFICULTY_LEVEL,
    MIN_OBSTACLE_FREQUENCY,
    OBSTACLE_FREQUENCY,
    OBSTACLE_FREQUENCY_STEP,
)


@dataclass(frozen=True)
class DifficultyState:
    level: int
    obstacle_speed: int
    obstacle_frequency: int


def difficulty_level_for_time(game_time):
    safe_game_time = max(0, int(game_time))
    completed_intervals = safe_game_time // DIFFICULTY_INTERVAL_FRAMES
    return min(INITIAL_DIFFICULTY_LEVEL + completed_intervals, MAX_DIFFICULTY_LEVEL)


def obstacle_speed_for_level(level):
    level_offset = max(0, int(level) - INITIAL_DIFFICULTY_LEVEL)
    return INITIAL_OBSTACLE_SPEED + level_offset


def obstacle_frequency_for_level(level):
    level_offset = max(0, int(level) - INITIAL_DIFFICULTY_LEVEL)
    frequency = OBSTACLE_FREQUENCY - (level_offset * OBSTACLE_FREQUENCY_STEP)
    return max(MIN_OBSTACLE_FREQUENCY, frequency)


def difficulty_for_time(game_time):
    level = difficulty_level_for_time(game_time)
    return DifficultyState(
        level=level,
        obstacle_speed=obstacle_speed_for_level(level),
        obstacle_frequency=obstacle_frequency_for_level(level),
    )
