import random

import pygame

from difficulty import difficulty_for_time
from features import build_model_features
from settings import (
    INITIAL_DIFFICULTY_LEVEL,
    INITIAL_LIVES,
    INITIAL_OBSTACLE_SPEED,
    INVINCIBILITY_FRAMES,
    HIT_FLASH_INTERVAL,
    MAX_DIFFICULTY_LEVEL,
    OBSTACLE_COLOR,
    OBSTACLE_HEIGHT,
    OBSTACLE_WIDTH,
    PLAYER_COLOR,
    PLAYER_HIT_COLOR,
    PLAYER_HEIGHT,
    PLAYER_SPEED,
    PLAYER_WIDTH,
    PROGRESS_BAR_HEIGHT,
    PROGRESS_BAR_LENGTH,
    PROGRESS_COLOR,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from spawning import choose_spawn_x

ACTION_LEFT = "left"
ACTION_RIGHT = "right"

SCREEN_START = "start"
SCREEN_PLAYING = "playing"
SCREEN_PAUSED = "paused"
SCREEN_GAME_OVER = "game_over"

BACKGROUND_COLOR = (0, 0, 0)
HUD_COLOR = (255, 255, 255)


class RockfallGame:
    def __init__(self, screen, high_score=0):
        self.screen = screen
        self.high_score = high_score
        self.font = pygame.font.Font(None, 36)
        self.title_font = pygame.font.Font(None, 72)
        self.level_text = self.font.render("Level:", True, HUD_COLOR)
        self.progress_bar_x = SCREEN_WIDTH - PROGRESS_BAR_LENGTH - 10
        self.progress_bar_y = 10

        self.reset()

    def set_high_score(self, high_score):
        self.high_score = max(0, int(high_score))

    def visible_high_score(self):
        return max(self.high_score, self.score)

    def reset(self):
        self.player_x = SCREEN_WIDTH // 2 - PLAYER_WIDTH // 2
        self.player_y = SCREEN_HEIGHT - PLAYER_HEIGHT - 10
        self.obstacles = []
        self.obstacle_speed = INITIAL_OBSTACLE_SPEED
        self.obstacle_frequency = difficulty_for_time(0).obstacle_frequency
        self.last_spawn_x = None
        self.frame_count = 0
        self.game_time = 0
        self.lives = INITIAL_LIVES
        self.invincibility_frames = 0
        self.score = 0
        self.difficulty_level = INITIAL_DIFFICULTY_LEVEL
        self.game_over = False

    def snapshot(self):
        return {
            "player_x": self.player_x,
            "obstacles": [(obstacle[0], obstacle[1]) for obstacle in self.obstacles],
        }

    def model_features(self):
        return build_model_features(self.player_x, self.obstacles)

    def apply_action(self, action):
        if action == ACTION_LEFT:
            self.player_x = max(self.player_x - PLAYER_SPEED, 0)
        elif action == ACTION_RIGHT:
            self.player_x = min(self.player_x + PLAYER_SPEED, SCREEN_WIDTH - PLAYER_WIDTH)

    def update(self):
        if self.game_over:
            return

        self._increase_difficulty()
        self._spawn_obstacle()
        self._move_obstacles_and_check_collisions()
        self._tick_invincibility()

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        pygame.draw.rect(self.screen, self.player_color(), self.player_rect)

        for obstacle in self.obstacles:
            pygame.draw.rect(self.screen, OBSTACLE_COLOR, self.obstacle_rect(obstacle))

        self._draw_hud()

    def draw_start_screen(self, mode_name):
        self._draw_message_screen(
            "ROCKFALL",
            [
                mode_name,
                f"High Score: {self.visible_high_score()}",
                "Press SPACE to start",
                "Press ESC to quit",
            ],
        )

    def draw_game_over_screen(self, mode_name):
        self._draw_message_screen(
            "GAME OVER",
            [
                mode_name,
                f"Final Score: {self.score}",
                f"High Score: {self.visible_high_score()}",
                "Press R to restart",
                "Press ESC to quit",
            ],
        )

    def draw_pause_screen(self, mode_name):
        self._draw_message_screen(
            "PAUSED",
            [
                mode_name,
                f"High Score: {self.visible_high_score()}",
                "Press P to resume",
                "Press R to restart",
                "Press ESC to quit",
            ],
        )

    @property
    def player_rect(self):
        return pygame.Rect(self.player_x, self.player_y, PLAYER_WIDTH, PLAYER_HEIGHT)

    def obstacle_rect(self, obstacle):
        return pygame.Rect(obstacle[0], obstacle[1], OBSTACLE_WIDTH, OBSTACLE_HEIGHT)

    def player_color(self):
        if self.invincibility_frames <= 0:
            return PLAYER_COLOR

        flash_phase = self.invincibility_frames // HIT_FLASH_INTERVAL
        if flash_phase % 2 == 0:
            return PLAYER_HIT_COLOR
        return PLAYER_COLOR

    def _increase_difficulty(self):
        self.game_time += 1
        difficulty = difficulty_for_time(self.game_time)
        self.obstacle_speed = difficulty.obstacle_speed
        self.obstacle_frequency = difficulty.obstacle_frequency
        self.difficulty_level = difficulty.level

    def _spawn_obstacle(self):
        self.frame_count += 1
        if self.frame_count % self.obstacle_frequency == 0:
            obstacle_x = choose_spawn_x(self.last_spawn_x, self.difficulty_level, random)
            self.obstacles.append([obstacle_x, -OBSTACLE_HEIGHT])
            self.last_spawn_x = obstacle_x

    def _move_obstacles_and_check_collisions(self):
        player_rect = self.player_rect
        remaining_obstacles = []

        for obstacle in self.obstacles:
            if obstacle[1] >= SCREEN_HEIGHT:
                self.score += 1
                continue

            obstacle[1] += self.obstacle_speed
            if player_rect.colliderect(self.obstacle_rect(obstacle)):
                self._handle_hit()
            else:
                remaining_obstacles.append(obstacle)

        self.obstacles = remaining_obstacles

    def _handle_hit(self):
        if self.invincibility_frames > 0:
            return

        self.lives -= 1
        self.invincibility_frames = INVINCIBILITY_FRAMES
        if self.lives <= 0:
            self.game_over = True

    def _tick_invincibility(self):
        if self.invincibility_frames > 0:
            self.invincibility_frames -= 1

    def _draw_message_screen(self, title, lines):
        self.screen.fill(BACKGROUND_COLOR)
        title_surface = self.title_font.render(title, True, HUD_COLOR)
        title_x = (SCREEN_WIDTH - title_surface.get_width()) // 2
        self.screen.blit(title_surface, (title_x, 170))

        for index, line in enumerate(lines):
            text_surface = self.font.render(line, True, HUD_COLOR)
            text_x = (SCREEN_WIDTH - text_surface.get_width()) // 2
            self.screen.blit(text_surface, (text_x, 270 + index * 42))

    def _draw_hud(self):
        lives_text = self.font.render(f"Lives: {self.lives}", True, HUD_COLOR)
        self.screen.blit(lives_text, (10, 10))

        score_text = self.font.render(f"Score: {self.score}", True, HUD_COLOR)
        self.screen.blit(score_text, (10, 45))

        high_score_text = self.font.render(f"Best: {self.visible_high_score()}", True, HUD_COLOR)
        self.screen.blit(high_score_text, (10, 80))

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
