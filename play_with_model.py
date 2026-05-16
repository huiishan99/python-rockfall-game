import joblib
import pygame

from game_core import ACTION_LEFT, ACTION_RIGHT, RockfallGame
from settings import FPS, SCREEN_HEIGHT, SCREEN_WIDTH

MODEL_FILE = "game_model.pkl"


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

    while game.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False

        game.apply_action(predict_action(model, game))
        game.update()
        game.draw()

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
