import pygame
import random
import joblib
import numpy as np

from settings import (
    DIFFICULTY_INTERVAL_FRAMES,
    FPS,
    INITIAL_DIFFICULTY_LEVEL,
    INITIAL_LIVES,
    INITIAL_OBSTACLE_SPEED,
    MAX_DIFFICULTY_LEVEL,
    OBSTACLE_COLOR,
    OBSTACLE_FREQUENCY,
    OBSTACLE_HEIGHT,
    OBSTACLE_WIDTH,
    PLAYER_COLOR,
    PLAYER_HEIGHT,
    PLAYER_SPEED,
    PLAYER_WIDTH,
    PROGRESS_BAR_HEIGHT,
    PROGRESS_BAR_LENGTH,
    PROGRESS_COLOR,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)

# 初始化pygame
pygame.init()
screen_width = SCREEN_WIDTH
screen_height = SCREEN_HEIGHT
screen = pygame.display.set_mode((screen_width, screen_height))

# 加载模型
model = joblib.load('game_model.pkl')

# 玩家设置
player_width = PLAYER_WIDTH
player_height = PLAYER_HEIGHT
player_x = screen_width // 2 - player_width // 2
player_y = screen_height - player_height - 10
player_speed = PLAYER_SPEED

# 障碍物设置
obstacle_width = OBSTACLE_WIDTH
obstacle_height = OBSTACLE_HEIGHT
obstacles = []
obstacle_speed = INITIAL_OBSTACLE_SPEED
obstacle_frequency = OBSTACLE_FREQUENCY
frame_count = 0

# 游戏状态
game_time = 0
lives = INITIAL_LIVES
difficulty_level = INITIAL_DIFFICULTY_LEVEL
max_difficulty_level = MAX_DIFFICULTY_LEVEL

# HUD设置
font = pygame.font.Font(None, 36)
level_text = font.render("Level:", True, (255, 255, 255))
progress_bar_x = screen_width - 210
progress_bar_y = 10

# 游戏主循环控制
running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    game_time += 1
    if game_time % DIFFICULTY_INTERVAL_FRAMES == 0:
        obstacle_speed += 1
        difficulty_level = min(difficulty_level + 1, max_difficulty_level)

    # 障碍物生成逻辑
    frame_count += 1
    if frame_count % obstacle_frequency == 0:
        obstacles.append([random.randint(0, screen_width - obstacle_width), -obstacle_height])

    # 更新障碍物位置
    obstacles = [[ob[0], ob[1] + obstacle_speed] for ob in obstacles if ob[1] < screen_height]

    # 这里我们假设有一个障碍物，你需要根据实际游戏逻辑调整这里的代码
    if obstacles:
        input_features = np.array([[player_x, obstacles[0][0]]])
    else:
        input_features = np.array([[player_x, 0]])  # 如果没有障碍物，使用0作为占位符

    # 使用模型预测玩家的行动
    predicted_action = model.predict(input_features)[0]

    # 根据预测结果更新玩家位置
    if predicted_action == 1:  # 假设1代表向右
        player_x = min(player_x + player_speed, screen_width - player_width)
    elif predicted_action == 0:  # 假设0代表向左
        player_x = max(player_x - player_speed, 0)

    # 检测碰撞
    player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
    remaining_obstacles = []
    for ob in obstacles:
        obstacle_rect = pygame.Rect(ob[0], ob[1], obstacle_width, obstacle_height)
        if player_rect.colliderect(obstacle_rect):
            lives -= 1
            if lives == 0:
                running = False
        else:
            remaining_obstacles.append(ob)
    obstacles = remaining_obstacles

    # 清空屏幕
    screen.fill((0, 0, 0))

    # 绘制玩家
    pygame.draw.rect(screen, PLAYER_COLOR, player_rect)

    # 绘制障碍物
    for ob in obstacles:
        pygame.draw.rect(screen, OBSTACLE_COLOR, pygame.Rect(ob[0], ob[1], obstacle_width, obstacle_height))

    # 显示生命值和难度
    lives_text = font.render(f"Lives: {lives}", True, (255, 255, 255))
    screen.blit(lives_text, (10, 10))

    progress = (difficulty_level / max_difficulty_level) * PROGRESS_BAR_LENGTH
    pygame.draw.rect(screen, (255, 255, 255),
                     (progress_bar_x, progress_bar_y, PROGRESS_BAR_LENGTH, PROGRESS_BAR_HEIGHT), 1)
    pygame.draw.rect(screen, PROGRESS_COLOR, (progress_bar_x, progress_bar_y, progress, PROGRESS_BAR_HEIGHT))
    screen.blit(level_text, (progress_bar_x - level_text.get_width() - 10, progress_bar_y))

    # 更新屏幕显示
    pygame.display.flip()

    # 控制游戏更新速率
    clock.tick(FPS)

# 退出pygame
pygame.quit()
