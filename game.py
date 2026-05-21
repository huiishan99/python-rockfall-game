import argparse
import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

from data_store import GAME_DATA_FILE, append_game_data
from difficulty import DEFAULT_DIFFICULTY_PRESET, difficulty_preset_names
from game_audio import GameSoundPlayer
from game_core import (
    ACTION_LEFT,
    ACTION_RIGHT,
    SCREEN_GAME_OVER,
    SCREEN_HELP,
    SCREEN_PAUSED,
    SCREEN_PLAYING,
    SCREEN_START,
    RockfallGame,
)
from scores import get_high_score, record_high_score
from settings import FPS, INITIAL_LIVES, PLAYER_SPEED, SCREEN_HEIGHT, SCREEN_WIDTH, SOUND_ENABLED, VERSION

MODE_KEY = "manual"
MODE_NAME = "Data Collection"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Play Rockfall and collect training data.")
    parser.add_argument("--data", default=GAME_DATA_FILE, help="Gameplay data file to append.")
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


def read_manual_action():
    keys = pygame.key.get_pressed()
    left_pressed = keys[pygame.K_LEFT] or keys[pygame.K_a]
    right_pressed = keys[pygame.K_RIGHT] or keys[pygame.K_d]

    if left_pressed == right_pressed:
        return None
    if left_pressed:
        return ACTION_LEFT
    return ACTION_RIGHT


def main(argv=None):
    args = parse_args(argv)
    if args.player_speed <= 0:
        raise ValueError("--player-speed must be greater than zero.")
    if args.lives <= 0:
        raise ValueError("--lives must be greater than zero.")

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    mode_name = f"{MODE_NAME} ({args.difficulty})"
    pygame.display.set_caption(f"Rockfall {VERSION} - {mode_name}")

    game = RockfallGame(
        screen,
        high_score=get_high_score(MODE_KEY),
        difficulty_preset=args.difficulty,
        player_speed=args.player_speed,
        initial_lives=args.lives,
    )
    sound_player = GameSoundPlayer(enabled=SOUND_ENABLED and not args.mute)
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
                    if screen_state == SCREEN_HELP:
                        screen_state = SCREEN_START
                    else:
                        app_running = False
                elif screen_state == SCREEN_START and event.key == pygame.K_SPACE:
                    game.reset()
                    screen_state = SCREEN_PLAYING
                elif screen_state == SCREEN_START and event.key == pygame.K_h:
                    screen_state = SCREEN_HELP
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
                elif screen_state == SCREEN_HELP and game.help_back_button_rect().collidepoint(event.pos):
                    screen_state = SCREEN_START
                elif screen_state == SCREEN_HELP and game.help_start_button_rect().collidepoint(event.pos):
                    game.reset()
                    screen_state = SCREEN_PLAYING

        if screen_state == SCREEN_PLAYING:
            action = read_manual_action()
            if action:
                game_data.append({"state": game.snapshot(), "action": action})

            game.apply_action(action)
            game.update()
            sound_player.play_events(game.pop_events())
            if game.game_over:
                high_score, _ = record_high_score(MODE_KEY, game.score)
                game.set_high_score(high_score)
                screen_state = SCREEN_GAME_OVER

        if screen_state == SCREEN_START:
            game.draw_start_screen(mode_name)
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

    if game_data:
        try:
            previous_count, total_count = append_game_data(game_data, args.data)
        except ValueError as error:
            print(f"Could not save gameplay data: {error}")
        else:
            print(
                f"Saved {len(game_data)} new samples to {args.data} "
                f"({previous_count} -> {total_count})."
            )
    else:
        print("No gameplay data collected; existing data file was left unchanged.")

    pygame.quit()


if __name__ == "__main__":
    main()
