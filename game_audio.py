import math
from array import array

from game_events import EVENT_AVOID, EVENT_HIT, EVENT_LEVEL_UP
from settings import SOUND_SAMPLE_RATE, SOUND_VOLUME


class GameSoundPlayer:
    def __init__(self, enabled=True):
        self.available = False
        self.sounds = {}

        if not enabled:
            return

        try:
            import pygame

            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SOUND_SAMPLE_RATE, size=-16, channels=1)

            self.sounds = {
                EVENT_AVOID: self._make_tone(pygame, 880, 70, SOUND_VOLUME),
                EVENT_HIT: self._make_tone(pygame, 180, 140, SOUND_VOLUME),
                EVENT_LEVEL_UP: self._make_tone(pygame, 660, 180, SOUND_VOLUME),
            }
            self.available = True
        except Exception:
            self.available = False
            self.sounds = {}

    def play_events(self, events):
        if not self.available:
            return

        for event in events:
            sound = self.sounds.get(event)
            if sound:
                sound.play()

    def _make_tone(self, pygame, frequency, duration_ms, volume):
        sample_count = int(SOUND_SAMPLE_RATE * duration_ms / 1000)
        amplitude = int(32767 * volume)
        samples = array("h")

        for sample_index in range(sample_count):
            sample = math.sin(2 * math.pi * frequency * sample_index / SOUND_SAMPLE_RATE)
            samples.append(int(amplitude * sample))

        return pygame.mixer.Sound(buffer=samples.tobytes())
