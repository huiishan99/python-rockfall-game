from settings import (
    DEFAULT_OBSTACLE_VARIANT,
    NEAR_MISS_DISTANCE,
    OBSTACLE_HEIGHT,
    OBSTACLE_VARIANTS,
    OBSTACLE_WIDTH,
    PLAYER_WIDTH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)

POLICY_SAFE_RULE = "safe-rule"
POLICY_ORE_HUNTER = "ore-hunter"
BUILTIN_POLICIES = (POLICY_SAFE_RULE, POLICY_ORE_HUNTER)
ORE_HUNTER_MIN_LIVES = 2
ORE_HUNTER_RISK_WEIGHT = 5


def built_in_policy_names():
    return BUILTIN_POLICIES


def policy_label(policy_name):
    return f"policy:{policy_name}"


def is_policy_label(label):
    return label.startswith("policy:")


def policy_name_from_label(label):
    if is_policy_label(label):
        return label.split(":", 1)[1]
    return label


def choose_policy_action(policy_name, game):
    if policy_name == POLICY_SAFE_RULE:
        return choose_safe_rule_action(game)
    if policy_name == POLICY_ORE_HUNTER:
        return choose_ore_hunter_action(game)
    raise ValueError(f"Unknown built-in policy: {policy_name}")


def choose_safe_rule_action(game):
    left_risk = action_risk(game, "left")
    right_risk = action_risk(game, "right")
    if left_risk < right_risk:
        return "left"
    if right_risk < left_risk:
        return "right"
    return center_seeking_action(game)


def choose_ore_hunter_action(game):
    left_value = ore_hunter_action_value(game, "left")
    right_value = ore_hunter_action_value(game, "right")
    if left_value > right_value:
        return "left"
    if right_value > left_value:
        return "right"
    return choose_safe_rule_action(game)


def ore_hunter_action_value(game, action):
    candidate_x = candidate_player_x(game, action)
    candidate_center = candidate_x + PLAYER_WIDTH / 2
    stone_risk = edge_pressure(candidate_x)
    ore_value = 0

    for obstacle in game.obstacles:
        if obstacle_variant(obstacle) == "ore":
            ore_value += ore_collection_value(game, candidate_center, obstacle)
        else:
            stone_risk += obstacle_collision_risk(candidate_center, obstacle)

    return ore_value - stone_risk * ORE_HUNTER_RISK_WEIGHT


def ore_collection_value(game, candidate_center, obstacle):
    if getattr(game, "lives", ORE_HUNTER_MIN_LIVES) < ORE_HUNTER_MIN_LIVES:
        return 0

    try:
        obstacle_x = int(obstacle[0])
        obstacle_y = int(obstacle[1])
    except (TypeError, ValueError, IndexError):
        return 0

    obstacle_center = obstacle_x + OBSTACLE_WIDTH / 2
    horizontal_gap = abs(candidate_center - obstacle_center)
    collect_radius = (PLAYER_WIDTH + OBSTACLE_WIDTH) / 2
    if horizontal_gap > collect_radius:
        return 0

    horizontal_alignment = (collect_radius - horizontal_gap) / collect_radius
    vertical_progress = max(0, min(SCREEN_HEIGHT, obstacle_y + OBSTACLE_HEIGHT)) / SCREEN_HEIGHT
    score_bonus = OBSTACLE_VARIANTS["ore"]["score_bonus"]
    combo_bonus = 0
    if hasattr(game, "combo_bonus_points"):
        combo_bonus = game.combo_bonus_points()
    return (score_bonus + combo_bonus) * horizontal_alignment * (0.25 + vertical_progress)


def center_seeking_action(game):
    player_center = game.player_x + PLAYER_WIDTH / 2
    if player_center < SCREEN_WIDTH / 2:
        return "right"
    return "left"


def action_risk(game, action):
    candidate_x = candidate_player_x(game, action)
    candidate_center = candidate_x + PLAYER_WIDTH / 2
    edge_risk = edge_pressure(candidate_x)
    obstacle_risk = sum(obstacle_collision_risk(candidate_center, obstacle) for obstacle in game.obstacles)
    return obstacle_risk + edge_risk


def candidate_player_x(game, action):
    if action == "left":
        return max(game.player_x - game.player_speed, 0)
    if action == "right":
        return min(game.player_x + game.player_speed, SCREEN_WIDTH - PLAYER_WIDTH)
    return game.player_x


def edge_pressure(candidate_x):
    margin = min(candidate_x, SCREEN_WIDTH - PLAYER_WIDTH - candidate_x)
    if margin >= PLAYER_WIDTH:
        return 0
    return (PLAYER_WIDTH - margin) / PLAYER_WIDTH


def obstacle_collision_risk(candidate_center, obstacle):
    try:
        obstacle_x = int(obstacle[0])
        obstacle_y = int(obstacle[1])
    except (TypeError, ValueError, IndexError):
        return 0

    obstacle_center = obstacle_x + OBSTACLE_WIDTH / 2
    horizontal_gap = abs(candidate_center - obstacle_center)
    danger_radius = (PLAYER_WIDTH + OBSTACLE_WIDTH) / 2
    near_radius = max(NEAR_MISS_DISTANCE, danger_radius)
    horizontal_pressure = max(0, near_radius - horizontal_gap) / near_radius
    if horizontal_pressure <= 0:
        return 0

    vertical_progress = max(0, min(SCREEN_HEIGHT, obstacle_y + OBSTACLE_HEIGHT)) / SCREEN_HEIGHT
    return horizontal_pressure * (1 + vertical_progress * 4)


def obstacle_variant(obstacle):
    try:
        variant_key = obstacle[2]
    except (TypeError, IndexError):
        return DEFAULT_OBSTACLE_VARIANT
    if variant_key in OBSTACLE_VARIANTS:
        return variant_key
    return DEFAULT_OBSTACLE_VARIANT
