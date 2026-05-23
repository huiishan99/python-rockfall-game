from settings import DEFAULT_OBSTACLE_VARIANT, OBSTACLE_VARIANTS

LEGACY_FEATURE_NAMES = (
    "player_x",
    "nearest_obstacle_x",
    "nearest_obstacle_y",
    "nearest_obstacle_dx",
)
FEATURE_NAMES = LEGACY_FEATURE_NAMES + (
    "nearest_obstacle_speed_delta",
    "nearest_obstacle_score_bonus",
)


def obstacle_variant_key(obstacle):
    try:
        has_variant = len(obstacle) >= 3
    except TypeError:
        return DEFAULT_OBSTACLE_VARIANT

    if has_variant and isinstance(obstacle[2], str) and obstacle[2] in OBSTACLE_VARIANTS:
        return obstacle[2]
    return DEFAULT_OBSTACLE_VARIANT


def normalize_obstacle(obstacle):
    try:
        if len(obstacle) < 2:
            return None
    except TypeError:
        return None

    x, y = obstacle[0], obstacle[1]
    try:
        return (int(x), int(y), obstacle_variant_key(obstacle))
    except (TypeError, ValueError):
        return None


def select_nearest_obstacle(obstacles):
    valid_obstacles = []
    for obstacle in obstacles:
        normalized_obstacle = normalize_obstacle(obstacle)
        if normalized_obstacle is not None:
            valid_obstacles.append(normalized_obstacle)

    if not valid_obstacles:
        return None

    return max(valid_obstacles, key=lambda obstacle: obstacle[1])


def build_model_features(player_x, obstacles):
    player_x = int(player_x)
    nearest_obstacle = select_nearest_obstacle(obstacles)

    if nearest_obstacle is None:
        obstacle_x = player_x
        obstacle_y = 0
        variant_key = DEFAULT_OBSTACLE_VARIANT
    else:
        obstacle_x, obstacle_y, variant_key = nearest_obstacle

    variant = OBSTACLE_VARIANTS[variant_key]

    return [
        player_x,
        obstacle_x,
        obstacle_y,
        obstacle_x - player_x,
        variant["speed_delta"],
        variant["score_bonus"],
    ]


def adapt_features_for_model(features, model):
    expected_feature_count = getattr(model, "n_features_in_", None)
    if expected_feature_count is None or expected_feature_count == len(features):
        return features

    if expected_feature_count == len(LEGACY_FEATURE_NAMES):
        return features[:expected_feature_count]

    supported_counts = ", ".join(str(count) for count in (len(LEGACY_FEATURE_NAMES), len(FEATURE_NAMES)))
    raise ValueError(
        f"Model expects {expected_feature_count} features, "
        f"but Rockfall supports {supported_counts} feature inputs."
    )
