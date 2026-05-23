from settings import (
    NEAR_MISS_DISTANCE,
    OBSTACLE_HEIGHT,
    OBSTACLE_WIDTH,
    PLAYER_WIDTH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)

POLICY_SAFE_RULE = "safe-rule"
BUILTIN_POLICIES = (POLICY_SAFE_RULE,)


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
    raise ValueError(f"Unknown built-in policy: {policy_name}")


def choose_safe_rule_action(game):
    left_risk = action_risk(game, "left")
    right_risk = action_risk(game, "right")
    if left_risk < right_risk:
        return "left"
    if right_risk < left_risk:
        return "right"
    return center_seeking_action(game)


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
