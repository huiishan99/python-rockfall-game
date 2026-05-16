import random

import pygame

from settings import (
    DIFFICULTY_INTERVAL_FRAMES,
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

ACTION_LEFT = "left"
ACTION_RIGHT = "right"

BACKGROUND_COLOR = (0, 0, 0)
HUD_COLOR = (255, 255, 255)


class RockfallGame:
    def __init__(self, screen):
        self.screen = screen
        self.player_x = SCREEN_WIDTH // 2 - PLAYER_WIDTH // 2
        self.player_y = SCREEN_HEIGHT - PLAYER_HEIGHT - 10
        self.obstacles = []
        self.obstacle_speed = INITIAL_OBSTACLE_SPEED
        self.frame_count = 0
        self.game_time = 0
        self.lives = INITIAL_LIVES
        self.difficulty_level = INITIAL_DIFFICULTY_LEVEL
        self.running = True

        self.font = pygame.font.Font(None, 36)
        self.level_text = self.font.render("Level:", True, HUD_COLOR)
        self.progress_bar_x = SCREEN_WIDTH - PROGRESS_BAR_LENGTH - 10
        self.progress_bar_y = 10

    def snapshot(self):
        return {
            "player_x": self.player_x,
            "obstacles": [(obstacle[0], obstacle[1]) for obstacle in self.obstacles],
        }

    def model_features(self):
        if self.obstacles:
            first_obstacle_x = self.obstacles[0][0]
        else:
            first_obstacle_x = 0
        return [self.player_x, first_obstacle_x]

    def apply_action(self, action):
        if action == ACTION_LEFT:
            self.player_x = max(self.player_x - PLAYER_SPEED, 0)
        elif action == ACTION_RIGHT:
            self.player_x = min(self.player_x + PLAYER_SPEED, SCREEN_WIDTH - PLAYER_WIDTH)

    def update(self):
        self._increase_difficulty()
        self._spawn_obstacle()
        self._move_obstacles_and_check_collisions()

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        pygame.draw.rect(self.screen, PLAYER_COLOR, self.player_rect)

        for obstacle in self.obstacles:
            pygame.draw.rect(self.screen, OBSTACLE_COLOR, self.obstacle_rect(obstacle))

        self._draw_hud()

    @property
    def player_rect(self):
        return pygame.Rect(self.player_x, self.player_y, PLAYER_WIDTH, PLAYER_HEIGHT)

    def obstacle_rect(self, obstacle):
        return pygame.Rect(obstacle[0], obstacle[1], OBSTACLE_WIDTH, OBSTACLE_HEIGHT)

    def _increase_difficulty(self):
        self.game_time += 1
        if self.game_time % DIFFICULTY_INTERVAL_FRAMES == 0:
            self.obstacle_speed += 1
            self.difficulty_level = min(self.difficulty_level + 1, MAX_DIFFICULTY_LEVEL)

    def _spawn_obstacle(self):
        self.frame_count += 1
        if self.frame_count % OBSTACLE_FREQUENCY == 0:
            max_x = SCREEN_WIDTH - OBSTACLE_WIDTH
            self.obstacles.append([random.randint(0, max_x), -OBSTACLE_HEIGHT])

    def _move_obstacles_and_check_collisions(self):
        player_rect = self.player_rect
        remaining_obstacles = []

        for obstacle in self.obstacles:
            if obstacle[1] >= SCREEN_HEIGHT:
                continue

            obstacle[1] += self.obstacle_speed
            if player_rect.colliderect(self.obstacle_rect(obstacle)):
                self.lives -= 1
                if self.lives <= 0:
                    self.running = False
            else:
                remaining_obstacles.append(obstacle)

        self.obstacles = remaining_obstacles

    def _draw_hud(self):
        lives_text = self.font.render(f"Lives: {self.lives}", True, HUD_COLOR)
        self.screen.blit(lives_text, (10, 10))

        progress = (self.difficulty_level / MAX_DIFFICULTY_LEVEL) * PROGRESS_BAR_LENGTH
        pygame.draw.rect(
            self.screen,
            HUD_COLOR,
            (self.progress_bar_x, self.progress_bar_y, PROGRESS_BAR_LENGTH, PROGRESS_BAR_HEIGHT),
            1,
        )
        pygame.draw.rect(
            self.screen,
            PROGRESS_COLOR,
            (self.progress_bar_x, self.progress_bar_y, progress, PROGRESS_BAR_HEIGHT),
        )
        self.screen.blit(
            self.level_text,
            (self.progress_bar_x - self.level_text.get_width() - 10, self.progress_bar_y),
        )
