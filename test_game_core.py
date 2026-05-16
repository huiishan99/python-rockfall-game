import os
import unittest

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from game_core import RockfallGame
from settings import (
    INITIAL_LIVES,
    INVINCIBILITY_FRAMES,
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


if __name__ == "__main__":
    unittest.main()
