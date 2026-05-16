FEATURE_NAMES = (
    "player_x",
    "nearest_obstacle_x",
    "nearest_obstacle_y",
    "nearest_obstacle_dx",
)


def select_nearest_obstacle(obstacles):
    valid_obstacles = []
    for obstacle in obstacles:
        if len(obstacle) < 2:
            continue

        x, y = obstacle[0], obstacle[1]
        try:
            valid_obstacles.append((int(x), int(y)))
        except (TypeError, ValueError):
            continue

    if not valid_obstacles:
        return None

    return max(valid_obstacles, key=lambda obstacle: obstacle[1])


def build_model_features(player_x, obstacles):
    player_x = int(player_x)
    nearest_obstacle = select_nearest_obstacle(obstacles)

    if nearest_obstacle is None:
        obstacle_x = player_x
        obstacle_y = 0
    else:
        obstacle_x, obstacle_y = nearest_obstacle

    return [
        player_x,
        obstacle_x,
        obstacle_y,
        obstacle_x - player_x,
    ]
