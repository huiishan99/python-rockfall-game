import argparse

MODEL_FILE = "game_model.pkl"
MODE_KEY = "model"
MODE_NAME = "Model Play"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run Rockfall with a trained model.")
    parser.add_argument("--model", default=MODEL_FILE, help="Model file to load.")
    parser.add_argument("--mute", action="store_true", help="Disable generated sound effects.")
    return parser.parse_args(argv)


def predict_action(model, game):
    from game_core import ACTION_LEFT, ACTION_RIGHT

    predicted_action = model.predict([game.model_features()])[0]
    if predicted_action == 1:
        return ACTION_RIGHT
    return ACTION_LEFT


def main(argv=None):
    args = parse_args(argv)

    import joblib
    import pygame

    from game_core import (
        SCREEN_GAME_OVER,
        SCREEN_PAUSED,
        SCREEN_PLAYING,
        SCREEN_START,
        RockfallGame,
    )
    from game_audio import GameSoundPlayer
    from scores import get_high_score, record_high_score
    from settings import FPS, SCREEN_HEIGHT, SCREEN_WIDTH, SOUND_ENABLED, VERSION

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(f"Rockfall {VERSION} - Model Play")

    model = joblib.load(args.model)
    game = RockfallGame(screen, high_score=get_high_score(MODE_KEY))
    sound_player = GameSoundPlayer(enabled=SOUND_ENABLED and not args.mute)
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
                elif screen_state == SCREEN_PLAYING and event.key == pygame.K_p:
                    screen_state = SCREEN_PAUSED
                elif screen_state == SCREEN_PAUSED and event.key == pygame.K_p:
                    screen_state = SCREEN_PLAYING
                elif screen_state == SCREEN_PAUSED and event.key == pygame.K_r:
                    game.reset()
                    screen_state = SCREEN_PLAYING
                elif screen_state == SCREEN_GAME_OVER and event.key == pygame.K_r:
                    game.reset()
                    screen_state = SCREEN_PLAYING

        if screen_state == SCREEN_PLAYING:
            game.apply_action(predict_action(model, game))
            game.update()
            sound_player.play_events(game.pop_events())
            if game.game_over:
                high_score, _ = record_high_score(MODE_KEY, game.score)
                game.set_high_score(high_score)
                screen_state = SCREEN_GAME_OVER

        if screen_state == SCREEN_START:
            game.draw_start_screen(MODE_NAME)
        elif screen_state == SCREEN_PAUSED:
            game.draw_pause_screen(MODE_NAME)
        elif screen_state == SCREEN_GAME_OVER:
            game.draw_game_over_screen(MODE_NAME)
        else:
            game.draw()

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
