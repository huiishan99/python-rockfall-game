import random

import pygame

from difficulty import DEFAULT_DIFFICULTY_PRESET, difficulty_for_time
from features import build_model_features
from game_events import EVENT_AVOID, EVENT_HIT, EVENT_LEVEL_UP
from settings import (
    BACKGROUND_ACCENT_COLOR,
    BACKGROUND_COLOR,
    COMBO_BONUS_INTERVAL,
    COMBO_MESSAGE_COLOR,
    HUD_COLOR,
    HUD_COMBO_COLOR,
    HUD_PANEL_BORDER_COLOR,
    HUD_PANEL_COLOR,
    HUD_PANEL_SHADOW_COLOR,
    HUD_PROGRESS_BACK_COLOR,
    HUD_WARNING_COLOR,
    INITIAL_DIFFICULTY_LEVEL,
    INITIAL_LIVES,
    INITIAL_OBSTACLE_SPEED,
    INVINCIBILITY_FRAMES,
    HIT_FLASH_INTERVAL,
    HIT_OVERLAY_COLOR,
    HIT_OVERLAY_MAX_ALPHA,
    HIT_MESSAGE_COLOR,
    LEVEL_MESSAGE_COLOR,
    LIFE_RESTORE_INTERVAL,
    LIFE_RESTORE_MESSAGE_COLOR,
    LOW_LIVES_THRESHOLD,
    MAX_DIFFICULTY_LEVEL,
    MAX_COMBO_BONUS,
    MESSAGE_DURATION_FRAMES,
    NEAR_MISS_DISTANCE,
    NEAR_MISS_MESSAGE_COLOR,
    OBSTACLE_COLOR,
    OBSTACLE_HEIGHT,
    OBSTACLE_HIGHLIGHT_COLOR,
    OBSTACLE_SHADOW_COLOR,
    OBSTACLE_WARNING_COLOR,
    OBSTACLE_WARNING_HEIGHT,
    OBSTACLE_WIDTH,
    LANE_COLOR,
    LANE_HIGHLIGHT_COLOR,
    MENU_ACCENT_COLOR,
    MENU_PANEL_BORDER_COLOR,
    MENU_PANEL_COLOR,
    MENU_SECONDARY_COLOR,
    MENU_TITLE_COLOR,
    MENU_TITLE_SHADOW_COLOR,
    PLAYER_COLOR,
    PLAYER_HIT_COLOR,
    PLAYER_HEIGHT,
    PLAYER_OUTLINE_COLOR,
    PLAYER_SHADOW_COLOR,
    PLAYER_SPEED,
    PLAYER_WIDTH,
    PROMPT_BACK_COLOR,
    PROMPT_BORDER_COLOR,
    PROGRESS_BAR_HEIGHT,
    PROGRESS_BAR_LENGTH,
    PROGRESS_COLOR,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SCORE_MESSAGE_COLOR,
)
from spawning import build_spawn_lanes, choose_spawn_x

ACTION_LEFT = "left"
ACTION_RIGHT = "right"

SCREEN_START = "start"
SCREEN_HELP = "help"
SCREEN_MODEL_MISSING = "model_missing"
SCREEN_PLAYING = "playing"
SCREEN_PAUSED = "paused"
SCREEN_GAME_OVER = "game_over"


class RockfallGame:
    def __init__(
        self,
        screen,
        high_score=0,
        difficulty_preset=DEFAULT_DIFFICULTY_PRESET,
        player_speed=PLAYER_SPEED,
        initial_lives=INITIAL_LIVES,
    ):
        self.screen = screen
        self.high_score = high_score
        self.difficulty_preset = difficulty_preset
        self.player_speed = max(1, int(player_speed))
        self.initial_lives = max(1, int(initial_lives))
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 28)
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
        self.obstacle_frequency = difficulty_for_time(0, self.difficulty_preset).obstacle_frequency
        self.last_spawn_x = None
        self.frame_count = 0
        self.game_time = 0
        self.lives = self.initial_lives
        self.invincibility_frames = 0
        self.score = 0
        self.combo = 0
        self.best_combo = 0
        self.next_life_restore_score = LIFE_RESTORE_INTERVAL
        self.difficulty_level = INITIAL_DIFFICULTY_LEVEL
        self.messages = []
        self.events = []
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
            self.player_x = max(self.player_x - self.player_speed, 0)
        elif action == ACTION_RIGHT:
            self.player_x = min(self.player_x + self.player_speed, SCREEN_WIDTH - PLAYER_WIDTH)

    def update(self):
        if self.game_over:
            return

        self._increase_difficulty()
        self._spawn_obstacle()
        self._move_obstacles_and_check_collisions()
        self._tick_invincibility()
        self._tick_messages()

    def draw(self):
        self._draw_background()
        self._draw_player()

        for obstacle in self.obstacles:
            self._draw_obstacle(obstacle)

        self._draw_hit_overlay()
        self._draw_hud()
        self._draw_messages()

    def pop_events(self):
        events = self.events
        self.events = []
        return events

    def draw_start_screen(self, mode_name, show_model_button=True, show_training_button=False):
        self._draw_message_screen("ROCKFALL", self.start_lines(mode_name))
        self._draw_button(self.help_button_rect(), "HOW IT WORKS")
        if show_model_button:
            self._draw_button(self.model_button_rect(), "PLAY WITH MODEL")
        if show_training_button:
            self._draw_button(self.training_button_rect(), "TRAIN MANUALLY")

    def start_lines(self, mode_name):
        return [
            mode_name,
            f"High Score: {self.visible_high_score()}",
            "Move: Left/Right or A/D",
            "Pause: P",
            "Press SPACE to start",
            "Press ESC to quit",
        ]

    def draw_help_screen(self):
        self._draw_background()
        title_y = 90
        title_shadow = self.title_font.render("HOW IT WORKS", True, MENU_TITLE_SHADOW_COLOR)
        title_surface = self.title_font.render("HOW IT WORKS", True, MENU_TITLE_COLOR)
        self._blit_centered(title_shadow, title_y + 4)
        self._blit_centered(title_surface, title_y)
        pygame.draw.line(
            self.screen,
            MENU_ACCENT_COLOR,
            (SCREEN_WIDTH // 2 - 145, 166),
            (SCREEN_WIDTH // 2 + 145, 166),
            2,
        )

        panel_rect = self.help_panel_rect()
        self._draw_panel(panel_rect, MENU_PANEL_COLOR, MENU_PANEL_BORDER_COLOR)
        for index, line in enumerate(self.help_lines()):
            text_surface = self.small_font.render(line, True, self._help_line_color(index))
            self._blit_centered(text_surface, panel_rect.y + 24 + index * 30)

        self._draw_button(self.help_back_button_rect(), "BACK")
        self._draw_button(self.help_start_button_rect(), "START")

    def draw_model_missing_screen(self, model_path):
        self._draw_message_screen("MODEL NOT READY", self.model_missing_lines(model_path))
        self._draw_button(self.help_back_button_rect(), "BACK")

    def model_missing_lines(self, model_path):
        return [
            f"Missing model: {model_path}",
            "Collect manual play samples first.",
            "Run: python3 train_model.py",
            "Then reopen and use PLAY WITH MODEL.",
            "Press B or ESC to return",
        ]

    def help_lines(self):
        return [
            "Dodge falling rocks and survive as long as you can.",
            "Move with Left/Right or A/D. Avoid rocks to score.",
            "Combos add bonus points; score milestones restore lost lives.",
            "Manual play records state + action examples.",
            "train_model.py learns left/right choices.",
            "play_with_model.py predicts movement each frame.",
            "inspect/evaluate/compare check data and model quality.",
            "That loop is the machine-learning part of Rockfall.",
        ]

    def help_button_rect(self):
        return pygame.Rect(SCREEN_WIDTH // 2 - 270, 518, 250, 34)

    def model_button_rect(self):
        return pygame.Rect(SCREEN_WIDTH // 2 + 20, 518, 250, 34)

    def training_button_rect(self):
        return self.model_button_rect()

    def help_back_button_rect(self):
        return pygame.Rect(SCREEN_WIDTH // 2 - 190, 535, 150, 34)

    def help_start_button_rect(self):
        return pygame.Rect(SCREEN_WIDTH // 2 + 40, 535, 150, 34)

    def help_panel_rect(self):
        return pygame.Rect(85, 190, SCREEN_WIDTH - 170, 310)

    def draw_game_over_screen(self, mode_name):
        self._draw_message_screen("GAME OVER", self.game_over_lines(mode_name))

    def game_over_lines(self, mode_name):
        return [
            mode_name,
            f"Final Score: {self.score}",
            f"High Score: {self.visible_high_score()}",
            f"Level Reached: {self.difficulty_level}",
            f"Best Combo: {self.best_combo}",
            f"Lives Left: {self.lives}",
            "Press R to restart",
            "Press ESC to quit",
        ]

    def draw_pause_screen(self, mode_name):
        self._draw_message_screen("PAUSED", self.pause_lines(mode_name))

    def pause_lines(self, mode_name):
        return [
            mode_name,
            f"Score: {self.score}  Best: {self.visible_high_score()}",
            f"Level: {self.difficulty_level}  Lives: {self.lives}  Combo: {self.combo}",
            "Move: Left/Right or A/D",
            "Press P to resume",
            "Press R to restart",
            "Press ESC to quit",
        ]

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
        previous_level = self.difficulty_level
        difficulty = difficulty_for_time(self.game_time, self.difficulty_preset)
        self.obstacle_speed = difficulty.obstacle_speed
        self.obstacle_frequency = difficulty.obstacle_frequency
        self.difficulty_level = difficulty.level
        if self.difficulty_level > previous_level:
            self._add_message(f"LEVEL {self.difficulty_level}", LEVEL_MESSAGE_COLOR, SCREEN_WIDTH // 2 - 70, 120)
            self._emit_event(EVENT_LEVEL_UP)

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
                self._handle_avoid(obstacle[0])
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
        self.combo = 0
        self._add_message("HIT!", HIT_MESSAGE_COLOR, self.player_x - 5, self.player_y - 35)
        self._emit_event(EVENT_HIT)
        if self.lives <= 0:
            self.game_over = True

    def _handle_avoid(self, obstacle_x):
        self.combo += 1
        self.best_combo = max(self.best_combo, self.combo)
        points = self.combo_points()
        self.score += points
        self._add_message(f"+{points}", SCORE_MESSAGE_COLOR, obstacle_x, SCREEN_HEIGHT - 95)
        self._emit_event(EVENT_AVOID)
        self._maybe_restore_life()

        if points > 1:
            self._add_message(f"COMBO {self.combo}", COMBO_MESSAGE_COLOR, obstacle_x - 25, SCREEN_HEIGHT - 130)
        if self.is_near_miss(obstacle_x):
            self._add_message("CLOSE!", NEAR_MISS_MESSAGE_COLOR, obstacle_x - 25, SCREEN_HEIGHT - 165)

    def _maybe_restore_life(self):
        while self.score >= self.next_life_restore_score:
            if self.lives < self.initial_lives:
                self.lives += 1
                self._add_message("LIFE +1", LIFE_RESTORE_MESSAGE_COLOR, self.player_x - 20, self.player_y - 65)
            self.next_life_restore_score += LIFE_RESTORE_INTERVAL

    def combo_points(self):
        bonus = min(MAX_COMBO_BONUS, self.combo // COMBO_BONUS_INTERVAL)
        return 1 + bonus

    def is_near_miss(self, obstacle_x):
        player_center = self.player_x + PLAYER_WIDTH // 2
        obstacle_center = obstacle_x + OBSTACLE_WIDTH // 2
        return abs(player_center - obstacle_center) <= NEAR_MISS_DISTANCE

    def hit_overlay_alpha(self):
        if self.invincibility_frames <= 0:
            return 0
        return max(1, HIT_OVERLAY_MAX_ALPHA * self.invincibility_frames // INVINCIBILITY_FRAMES)

    def lives_color(self):
        if self.lives <= LOW_LIVES_THRESHOLD:
            return HUD_WARNING_COLOR
        return HUD_COLOR

    def combo_color(self):
        if self.combo > 0:
            return HUD_COMBO_COLOR
        return HUD_COLOR

    def _tick_invincibility(self):
        if self.invincibility_frames > 0:
            self.invincibility_frames -= 1

    def _add_message(self, text, color, x, y, duration=MESSAGE_DURATION_FRAMES):
        self.messages.append(
            {
                "text": text,
                "color": color,
                "x": x,
                "y": y,
                "frames": duration,
            }
        )

    def _emit_event(self, event):
        self.events.append(event)

    def _tick_messages(self):
        remaining_messages = []
        for message in self.messages:
            message["frames"] -= 1
            message["y"] -= 1
            if message["frames"] > 0:
                remaining_messages.append(message)
        self.messages = remaining_messages

    def _draw_background(self):
        self.screen.fill(BACKGROUND_COLOR)
        for y in range(48, SCREEN_HEIGHT, 72):
            pygame.draw.line(self.screen, BACKGROUND_ACCENT_COLOR, (0, y), (SCREEN_WIDTH, y), 1)

        lanes = build_spawn_lanes()
        for lane_index, lane_x in enumerate(lanes):
            center_x = lane_x + OBSTACLE_WIDTH // 2
            lane_color = LANE_HIGHLIGHT_COLOR if lane_index % 2 == 0 else LANE_COLOR
            pygame.draw.line(self.screen, lane_color, (center_x, 0), (center_x, SCREEN_HEIGHT), 1)

    def _draw_player(self):
        shadow_rect = self.player_rect.move(4, 5)
        pygame.draw.rect(self.screen, PLAYER_SHADOW_COLOR, shadow_rect)
        pygame.draw.rect(self.screen, self.player_color(), self.player_rect)
        pygame.draw.rect(self.screen, PLAYER_OUTLINE_COLOR, self.player_rect, 2)

    def _draw_obstacle(self, obstacle):
        obstacle_rect = self.obstacle_rect(obstacle)
        shadow_rect = obstacle_rect.move(4, 5)
        highlight_rect = pygame.Rect(obstacle_rect.x, obstacle_rect.y, obstacle_rect.width, 8)

        pygame.draw.rect(self.screen, OBSTACLE_SHADOW_COLOR, shadow_rect)
        pygame.draw.rect(self.screen, OBSTACLE_COLOR, obstacle_rect)
        pygame.draw.rect(self.screen, OBSTACLE_HIGHLIGHT_COLOR, highlight_rect)
        if obstacle_rect.y < 0:
            self._draw_obstacle_warning(obstacle_rect)

    def _draw_obstacle_warning(self, obstacle_rect):
        warning_rect = pygame.Rect(obstacle_rect.x, 0, obstacle_rect.width, OBSTACLE_WARNING_HEIGHT)
        pygame.draw.rect(self.screen, OBSTACLE_WARNING_COLOR, warning_rect)

    def _draw_hit_overlay(self):
        alpha = self.hit_overlay_alpha()
        if alpha <= 0:
            return

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*HIT_OVERLAY_COLOR, alpha))
        self.screen.blit(overlay, (0, 0))

    def _draw_message_screen(self, title, lines):
        self._draw_background()
        title_y = 145
        title_shadow = self.title_font.render(title, True, MENU_TITLE_SHADOW_COLOR)
        title_surface = self.title_font.render(title, True, MENU_TITLE_COLOR)
        self._blit_centered(title_shadow, title_y + 4)
        self._blit_centered(title_surface, title_y)
        pygame.draw.line(
            self.screen,
            MENU_ACCENT_COLOR,
            (SCREEN_WIDTH // 2 - 120, 220),
            (SCREEN_WIDTH // 2 + 120, 220),
            2,
        )

        panel_height = 40 + len(lines) * 38
        panel_rect = pygame.Rect(135, 235, SCREEN_WIDTH - 270, panel_height)
        self._draw_panel(panel_rect, MENU_PANEL_COLOR, MENU_PANEL_BORDER_COLOR)

        for index, line in enumerate(lines):
            text_surface = self.font.render(line, True, self._message_line_color(index, line))
            line_y = 255 + index * 38
            if line.startswith("Press "):
                self._draw_prompt_back(text_surface, line_y)
            self._blit_centered(text_surface, line_y)

    def _blit_centered(self, surface, y):
        x = (SCREEN_WIDTH - surface.get_width()) // 2
        self.screen.blit(surface, (x, y))

    def _draw_panel(self, rect, fill_color, border_color):
        shadow_rect = rect.move(6, 7)
        pygame.draw.rect(self.screen, HUD_PANEL_SHADOW_COLOR, shadow_rect)
        pygame.draw.rect(self.screen, fill_color, rect)
        pygame.draw.rect(self.screen, border_color, rect, 2)

    def _draw_prompt_back(self, text_surface, y):
        prompt_rect = pygame.Rect(
            (SCREEN_WIDTH - text_surface.get_width()) // 2 - 16,
            y - 4,
            text_surface.get_width() + 32,
            text_surface.get_height() + 8,
        )
        pygame.draw.rect(self.screen, PROMPT_BACK_COLOR, prompt_rect)
        pygame.draw.rect(self.screen, PROMPT_BORDER_COLOR, prompt_rect, 1)

    def _draw_button(self, rect, text):
        pygame.draw.rect(self.screen, PROMPT_BACK_COLOR, rect)
        pygame.draw.rect(self.screen, PROMPT_BORDER_COLOR, rect, 2)
        text_surface = self.font.render(text, True, HUD_COLOR)
        self.screen.blit(
            text_surface,
            (
                rect.x + (rect.width - text_surface.get_width()) // 2,
                rect.y + (rect.height - text_surface.get_height()) // 2,
            ),
        )

    def _message_line_color(self, index, line):
        if index == 0:
            return MENU_ACCENT_COLOR
        if line.startswith(("Move:", "Pause:", "Press ")):
            return MENU_SECONDARY_COLOR
        return HUD_COLOR

    def _help_line_color(self, index):
        if index in (3, 4, 5, 6):
            return MENU_ACCENT_COLOR
        return HUD_COLOR

    def _draw_hud(self):
        stats_panel = pygame.Rect(8, 8, 190, 142)
        self._draw_panel(stats_panel, HUD_PANEL_COLOR, HUD_PANEL_BORDER_COLOR)

        lives_text = self.font.render(f"Lives: {self.lives}", True, self.lives_color())
        self.screen.blit(lives_text, (22, 20))

        score_text = self.font.render(f"Score: {self.score}", True, HUD_COLOR)
        self.screen.blit(score_text, (22, 54))

        high_score_text = self.font.render(f"Best: {self.visible_high_score()}", True, HUD_COLOR)
        self.screen.blit(high_score_text, (22, 88))

        combo_text = self.font.render(f"Combo: {self.combo}", True, self.combo_color())
        self.screen.blit(combo_text, (22, 122))

        progress_panel = pygame.Rect(self.progress_bar_x - 92, 8, PROGRESS_BAR_LENGTH + 102, 44)
        self._draw_panel(progress_panel, HUD_PANEL_COLOR, HUD_PANEL_BORDER_COLOR)
        progress = (self.difficulty_level / MAX_DIFFICULTY_LEVEL) * PROGRESS_BAR_LENGTH
        pygame.draw.rect(
            self.screen,
            HUD_PROGRESS_BACK_COLOR,
            (self.progress_bar_x, self.progress_bar_y, PROGRESS_BAR_LENGTH, PROGRESS_BAR_HEIGHT),
        )
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

    def _draw_messages(self):
        for message in self.messages:
            text_surface = self.font.render(message["text"], True, message["color"])
            self.screen.blit(text_surface, (message["x"], message["y"]))
