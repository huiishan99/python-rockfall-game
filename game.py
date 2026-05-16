import json

import pygame

from game_core import (
    ACTION_LEFT,
    ACTION_RIGHT,
    SCREEN_GAME_OVER,
    SCREEN_PLAYING,
    SCREEN_START,
    RockfallGame,
)
from settings import FPS, SCREEN_HEIGHT, SCREEN_WIDTH

DATA_FILE = "game_data.json"
MODE_NAME = "Data Collection"


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
    screen_state = SCREEN_START
    app_running = True

    while app_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                app_running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    app_running = False
                elif screen_state == SCREEN_START and event.key == pygame.K_SPACE:
                    game.reset()
                    screen_state = SCREEN_PLAYING
                elif screen_state == SCREEN_GAME_OVER and event.key == pygame.K_r:
                    game.reset()
                    screen_state = SCREEN_PLAYING

        if screen_state == SCREEN_PLAYING:
            action = read_manual_action()
            if action:
                game_data.append({"state": game.snapshot(), "action": action})

            game.apply_action(action)
            game.update()
            if game.game_over:
                screen_state = SCREEN_GAME_OVER

        if screen_state == SCREEN_START:
            game.draw_start_screen(MODE_NAME)
        elif screen_state == SCREEN_GAME_OVER:
            game.draw_game_over_screen(MODE_NAME)
        else:
            game.draw()

        pygame.display.flip()
        clock.tick(FPS)

    if game_data:
        with open(DATA_FILE, "w") as f:
            json.dump(game_data, f)
            print(f"Data has been saved to {DATA_FILE}")
    else:
        print("No gameplay data collected; existing data file was left unchanged.")

    pygame.quit()


if __name__ == "__main__":
    main()
