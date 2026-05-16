import os
import unittest

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from game_core import RockfallGame
from settings import (
    INITIAL_LIVES,
    INVINCIBILITY_FRAMES,
    MESSAGE_DURATION_FRAMES,
    PLAYER_COLOR,
    PLAYER_HIT_COLOR,
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


if __name__ == "__main__":
    unittest.main()
