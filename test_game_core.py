import os
import unittest

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from game_events import EVENT_AVOID, EVENT_HIT, EVENT_LEVEL_UP
from game_core import RockfallGame
from settings import (
    BACKGROUND_COLOR,
    COMBO_BONUS_INTERVAL,
    DIFFICULTY_INTERVAL_FRAMES,
    INITIAL_LIVES,
    INVINCIBILITY_FRAMES,
    MESSAGE_DURATION_FRAMES,
    OBSTACLE_HIGHLIGHT_COLOR,
    OBSTACLE_SHADOW_COLOR,
    OBSTACLE_WIDTH,
    PLAYER_COLOR,
    PLAYER_HIT_COLOR,
    PLAYER_OUTLINE_COLOR,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)


class GameCoreHitFeedbackTest(unittest.TestCase):
    def setUp(self):
        pygame.font.init()
        self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    def tearDown(self):
        pygame.font.quit()

    def test_hit_reduces_life_and_starts_invincibility(self):
        game = RockfallGame(self.screen)

        game._handle_hit()

        self.assertEqual(game.lives, INITIAL_LIVES - 1)
        self.assertEqual(game.invincibility_frames, INVINCIBILITY_FRAMES)

    def test_invincibility_prevents_extra_life_loss(self):
        game = RockfallGame(self.screen)

        game._handle_hit()
        game._handle_hit()

        self.assertEqual(game.lives, INITIAL_LIVES - 1)

    def test_invincibility_ticks_down(self):
        game = RockfallGame(self.screen)
        game._handle_hit()

        game._tick_invincibility()

        self.assertEqual(game.invincibility_frames, INVINCIBILITY_FRAMES - 1)

    def test_player_flashes_while_invincible(self):
        game = RockfallGame(self.screen)
        self.assertEqual(game.player_color(), PLAYER_COLOR)

        game._handle_hit()

        self.assertIn(game.player_color(), (PLAYER_COLOR, PLAYER_HIT_COLOR))

    def test_hit_adds_message(self):
        game = RockfallGame(self.screen)

        game._handle_hit()

        self.assertEqual(game.messages[-1]["text"], "HIT!")
        self.assertEqual(game.pop_events(), [EVENT_HIT])

    def test_messages_tick_down_and_float(self):
        game = RockfallGame(self.screen)
        game._add_message("+1", (255, 255, 255), 10, 20)

        game._tick_messages()

        self.assertEqual(game.messages[0]["frames"], MESSAGE_DURATION_FRAMES - 1)
        self.assertEqual(game.messages[0]["y"], 19)

    def test_messages_expire(self):
        game = RockfallGame(self.screen)
        game._add_message("+1", (255, 255, 255), 10, 20, duration=1)

        game._tick_messages()

        self.assertEqual(game.messages, [])

    def test_game_over_lines_include_run_summary(self):
        game = RockfallGame(self.screen)
        game.score = 12
        game.difficulty_level = 3
        game.lives = 2

        lines = game.game_over_lines("Model Play")

        self.assertIn("Model Play", lines)
        self.assertIn("Final Score: 12", lines)
        self.assertIn("Level Reached: 3", lines)
        self.assertIn("Lives Left: 2", lines)

    def test_start_lines_include_controls(self):
        game = RockfallGame(self.screen)

        lines = game.start_lines("Data Collection")

        self.assertIn("Move: Left/Right or A/D", lines)
        self.assertIn("Pause: P", lines)
        self.assertIn("Press SPACE to start", lines)

    def test_pause_lines_include_controls(self):
        game = RockfallGame(self.screen)

        lines = game.pause_lines("Data Collection")

        self.assertIn("Move: Left/Right or A/D", lines)
        self.assertIn("Press P to resume", lines)
        self.assertIn("Press R to restart", lines)

    def test_avoiding_obstacles_builds_combo_and_score(self):
        game = RockfallGame(self.screen)

        game._handle_avoid(100)

        self.assertEqual(game.combo, 1)
        self.assertEqual(game.best_combo, 1)
        self.assertEqual(game.score, 1)
        self.assertEqual(game.pop_events(), [EVENT_AVOID])

    def test_combo_bonus_increases_score_after_interval(self):
        game = RockfallGame(self.screen)

        for _ in range(COMBO_BONUS_INTERVAL):
            game._handle_avoid(100)

        self.assertEqual(game.combo, COMBO_BONUS_INTERVAL)
        self.assertEqual(game.combo_points(), 2)
        self.assertEqual(game.score, COMBO_BONUS_INTERVAL + 1)

    def test_hit_resets_combo(self):
        game = RockfallGame(self.screen)
        game._handle_avoid(100)
        game._handle_avoid(100)

        game._handle_hit()

        self.assertEqual(game.combo, 0)
        self.assertEqual(game.best_combo, 2)

    def test_game_over_lines_include_best_combo(self):
        game = RockfallGame(self.screen)
        game.best_combo = 7

        lines = game.game_over_lines("Model Play")

        self.assertIn("Best Combo: 7", lines)

    def test_pop_events_clears_event_queue(self):
        game = RockfallGame(self.screen)
        game._handle_avoid(100)

        self.assertEqual(game.pop_events(), [EVENT_AVOID])
        self.assertEqual(game.pop_events(), [])

    def test_level_up_emits_event(self):
        game = RockfallGame(self.screen)
        game.game_time = DIFFICULTY_INTERVAL_FRAMES - 1

        game._increase_difficulty()

        self.assertEqual(game.pop_events(), [EVENT_LEVEL_UP])

    def test_draw_uses_styled_background(self):
        game = RockfallGame(self.screen)

        game.draw()

        self.assertEqual(self.screen.get_at((3, 3))[:3], BACKGROUND_COLOR)

    def test_draw_adds_player_outline(self):
        game = RockfallGame(self.screen)

        game.draw()

        self.assertEqual(self.screen.get_at(game.player_rect.topleft)[:3], PLAYER_OUTLINE_COLOR)

    def test_draw_adds_obstacle_highlight_and_shadow(self):
        game = RockfallGame(self.screen)
        game.obstacles = [[100, 100]]

        game.draw()

        self.assertEqual(self.screen.get_at((101, 101))[:3], OBSTACLE_HIGHLIGHT_COLOR)
        self.assertEqual(
            self.screen.get_at((100 + OBSTACLE_WIDTH + 1, 100 + OBSTACLE_WIDTH + 1))[:3],
            OBSTACLE_SHADOW_COLOR,
        )


if __name__ == "__main__":
    unittest.main()
