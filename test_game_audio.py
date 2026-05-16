import unittest

from game_audio import GameSoundPlayer
from game_events import EVENT_AVOID, EVENT_HIT, EVENT_LEVEL_UP


class GameSoundPlayerTest(unittest.TestCase):
    def test_disabled_sound_player_is_noop(self):
        player = GameSoundPlayer(enabled=False)

        player.play_events([EVENT_AVOID, EVENT_HIT, EVENT_LEVEL_UP])

        self.assertFalse(player.available)


if __name__ == "__main__":
    unittest.main()
