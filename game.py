import json

import pygame

from game_core import ACTION_LEFT, ACTION_RIGHT, RockfallGame
from settings import FPS, SCREEN_HEIGHT, SCREEN_WIDTH

DATA_FILE = "game_data.json"


def read_manual_action():
    keys = pygame.key.get_pressed()
    left_pressed = keys[pygame.K_LEFT] or keys[pygame.K_a]
    right_pressed = keys[pygame.K_RIGHT] or keys[pygame.K_d]

    if left_pressed == right_pressed:
        return None
    if left_pressed:
        return ACTION_LEFT
    return ACTION_RIGHT


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Rockfall - Data Collection")

    game = RockfallGame(screen)
    clock = pygame.time.Clock()
    game_data = []

    while game.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False

        action = read_manual_action()
        if action:
            game_data.append({"state": game.snapshot(), "action": action})

        game.apply_action(action)
        game.update()
        game.draw()

        pygame.display.flip()
        clock.tick(FPS)

    with open(DATA_FILE, "w") as f:
        json.dump(game_data, f)
        print(f"Data has been saved to {DATA_FILE}")

    pygame.quit()


if __name__ == "__main__":
    main()
