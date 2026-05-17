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


@dataclass(frozen=True)
class DifficultyPreset:
    name: str
    speed_multiplier: float
    frequency_multiplier: float


DIFFICULTY_PRESETS = {
    "easy": DifficultyPreset("easy", speed_multiplier=0.85, frequency_multiplier=1.25),
    "normal": DifficultyPreset("normal", speed_multiplier=1.0, frequency_multiplier=1.0),
    "hard": DifficultyPreset("hard", speed_multiplier=1.15, frequency_multiplier=0.85),
}
DEFAULT_DIFFICULTY_PRESET = "normal"


def difficulty_preset_names():
    return tuple(DIFFICULTY_PRESETS.keys())


def difficulty_preset_for_name(name):
    try:
        return DIFFICULTY_PRESETS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown difficulty preset: {name}") from exc


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


def apply_difficulty_preset(difficulty, preset_name=DEFAULT_DIFFICULTY_PRESET):
    preset = difficulty_preset_for_name(preset_name)
    obstacle_speed = max(1, round(difficulty.obstacle_speed * preset.speed_multiplier))
    obstacle_frequency = max(MIN_OBSTACLE_FREQUENCY, round(difficulty.obstacle_frequency * preset.frequency_multiplier))
    return DifficultyState(
        level=difficulty.level,
        obstacle_speed=obstacle_speed,
        obstacle_frequency=obstacle_frequency,
    )


def difficulty_for_time(game_time, preset_name=DEFAULT_DIFFICULTY_PRESET):
    level = difficulty_level_for_time(game_time)
    base_difficulty = DifficultyState(
        level=level,
        obstacle_speed=obstacle_speed_for_level(level),
        obstacle_frequency=obstacle_frequency_for_level(level),
    )
    return apply_difficulty_preset(base_difficulty, preset_name)
