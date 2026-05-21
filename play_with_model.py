import argparse
import os
import subprocess
import sys

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

MODEL_FILE = "game_model.pkl"
MODE_KEY = "model"
MODE_NAME = "Model Play"


def parse_args(argv=None):
    from difficulty import DEFAULT_DIFFICULTY_PRESET, difficulty_preset_names
    from settings import INITIAL_LIVES, PLAYER_SPEED

    parser = argparse.ArgumentParser(description="Run Rockfall with a trained model.")
    parser.add_argument("--model", default=MODEL_FILE, help="Model file to load.")
    parser.add_argument(
        "--difficulty",
        choices=difficulty_preset_names(),
        default=DEFAULT_DIFFICULTY_PRESET,
        help="Difficulty preset.",
    )
    parser.add_argument("--player-speed", type=int, default=PLAYER_SPEED, help="Player movement speed in pixels.")
    parser.add_argument("--lives", type=int, default=INITIAL_LIVES, help="Initial player lives.")
    parser.add_argument("--mute", action="store_true", help="Disable generated sound effects.")
    return parser.parse_args(argv)


def predict_action(model, game):
    from game_core import ACTION_LEFT, ACTION_RIGHT

    predicted_action = model.predict([game.model_features()])[0]
    if predicted_action == 1:
        return ACTION_RIGHT
    return ACTION_LEFT


def model_mode_name(model_path, difficulty_preset=None):
    if difficulty_preset:
        return f"{MODE_NAME} ({os.path.basename(model_path)}, {difficulty_preset})"
    return f"{MODE_NAME} ({os.path.basename(model_path)})"


def model_load_error_message(model_path, error):
    return f"Could not load model '{model_path}': {error}"


def manual_play_command(args):
    command = [
        sys.executable,
        "game.py",
        "--difficulty",
        args.difficulty,
        "--player-speed",
        str(args.player_speed),
        "--lives",
        str(args.lives),
    ]
    if args.mute:
        command.append("--mute")
    return command


def launch_manual_play(args):
    subprocess.Popen(manual_play_command(args))


def main(argv=None):
    args = parse_args(argv)
    if args.player_speed <= 0:
        raise ValueError("--player-speed must be greater than zero.")
    if args.lives <= 0:
        raise ValueError("--lives must be greater than zero.")

    import joblib
    import pygame

    from game_core import (
        SCREEN_GAME_OVER,
        SCREEN_HELP,
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
    mode_name = model_mode_name(args.model, args.difficulty)
    pygame.display.set_caption(f"Rockfall {VERSION} - {mode_name}")

    try:
        model = joblib.load(args.model)
    except Exception as error:
        print(model_load_error_message(args.model, error))
        pygame.quit()
        return 1

    game = RockfallGame(
        screen,
        high_score=get_high_score(MODE_KEY),
        difficulty_preset=args.difficulty,
        player_speed=args.player_speed,
        initial_lives=args.lives,
    )
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
                    if screen_state == SCREEN_HELP:
                        screen_state = SCREEN_START
                    else:
                        app_running = False
                elif screen_state == SCREEN_START and event.key == pygame.K_SPACE:
                    game.reset()
                    screen_state = SCREEN_PLAYING
                elif screen_state == SCREEN_START and event.key == pygame.K_h:
                    screen_state = SCREEN_HELP
                elif screen_state == SCREEN_START and event.key == pygame.K_t:
                    pygame.quit()
                    launch_manual_play(args)
                    return 0
                elif screen_state == SCREEN_HELP and event.key == pygame.K_b:
                    screen_state = SCREEN_START
                elif screen_state == SCREEN_HELP and event.key == pygame.K_SPACE:
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
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if screen_state == SCREEN_START and game.help_button_rect().collidepoint(event.pos):
                    screen_state = SCREEN_HELP
                elif screen_state == SCREEN_START and game.training_button_rect().collidepoint(event.pos):
                    pygame.quit()
                    launch_manual_play(args)
                    return 0
                elif screen_state == SCREEN_HELP and game.help_back_button_rect().collidepoint(event.pos):
                    screen_state = SCREEN_START
                elif screen_state == SCREEN_HELP and game.help_start_button_rect().collidepoint(event.pos):
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
            game.draw_start_screen(mode_name, show_model_button=False, show_training_button=True)
        elif screen_state == SCREEN_HELP:
            game.draw_help_screen()
        elif screen_state == SCREEN_PAUSED:
            game.draw_pause_screen(mode_name)
        elif screen_state == SCREEN_GAME_OVER:
            game.draw_game_over_screen(mode_name)
        else:
            game.draw()

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
