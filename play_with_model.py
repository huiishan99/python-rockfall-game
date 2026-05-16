import joblib
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

MODEL_FILE = "game_model.pkl"
MODE_NAME = "Model Play"


def predict_action(model, game):
    predicted_action = model.predict([game.model_features()])[0]
    if predicted_action == 1:
        return ACTION_RIGHT
    return ACTION_LEFT


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Rockfall - Model Play")

    model = joblib.load(MODEL_FILE)
    game = RockfallGame(screen)
    clock = pygame.time.Clock()
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
            game.apply_action(predict_action(model, game))
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

    pygame.quit()


if __name__ == "__main__":
    main()
