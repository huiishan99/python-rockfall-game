import argparse
import os
import subprocess
import sys

from settings import DEFAULT_VARIANT_PROFILE, NEAR_MISS_DISTANCE, SCREEN_HEIGHT

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

MODEL_FILE = "game_model.pkl"
MODE_KEY = "model_ore_score"
MODE_NAME = "Model Play"


def parse_args(argv=None):
    from difficulty import DEFAULT_DIFFICULTY_PRESET, difficulty_preset_names
    from settings import DEFAULT_VARIANT_PROFILE, INITIAL_LIVES, PLAYER_SPEED, variant_profile_names

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
    parser.add_argument(
        "--variant-profile",
        choices=variant_profile_names(),
        default=DEFAULT_VARIANT_PROFILE,
        help="Rock variant spawn profile.",
    )
    parser.add_argument("--mute", action="store_true", help="Disable generated sound effects.")
    parser.add_argument("--debug-ai", action="store_true", help="Show model action and feature debug overlay.")
    return parser.parse_args(argv)


def predict_action(model, game):
    action, _, _ = predict_action_with_debug(model, game)
    return action


def predict_action_with_debug(model, game):
    from game_core import ACTION_LEFT, ACTION_RIGHT
    from features import adapt_features_for_model

    raw_features = game.model_features()
    model_features = adapt_features_for_model(raw_features, model)
    predicted_action = model.predict([model_features])[0]
    if predicted_action == 1:
        return (ACTION_RIGHT, raw_features, model_features)
    return (ACTION_LEFT, raw_features, model_features)


def prediction_confidence(model, model_features, action):
    if model is None or not hasattr(model, "predict_proba"):
        return None

    try:
        probabilities = model.predict_proba([model_features])[0]
    except Exception:
        return None

    target_label = 1 if action == "right" else 0
    classes = list(getattr(model, "classes_", [0, 1]))
    if target_label not in classes:
        return None
    return float(probabilities[classes.index(target_label)])


def obstacle_debug_metrics(raw_features):
    metrics = []
    rock_labels = ("near", "second", "third")
    offset = 1
    for label in rock_labels:
        if len(raw_features) < offset + 5:
            break
        _, y, dx, speed_delta, score_bonus = raw_features[offset : offset + 5]
        if y != 0:
            metrics.append(
                {
                    "label": label,
                    "kind": "ORE" if score_bonus > 0 else "STONE",
                    "dx": dx,
                    "y": y,
                    "speed_delta": speed_delta,
                    "score_bonus": score_bonus,
                    "danger": obstacle_danger_pressure(dx, y, score_bonus),
                    "ore_pull": obstacle_ore_pull(dx, y, score_bonus),
                }
            )
        offset += 5
    return metrics


def obstacle_danger_pressure(dx, y, score_bonus):
    if score_bonus > 0:
        return 0
    horizontal_pressure = max(0, NEAR_MISS_DISTANCE - abs(dx)) / NEAR_MISS_DISTANCE
    vertical_pressure = max(0, min(SCREEN_HEIGHT, y)) / SCREEN_HEIGHT
    return horizontal_pressure * (0.35 + vertical_pressure)


def obstacle_ore_pull(dx, y, score_bonus):
    if score_bonus <= 0:
        return 0
    horizontal_pressure = max(0, NEAR_MISS_DISTANCE - abs(dx)) / NEAR_MISS_DISTANCE
    vertical_pressure = max(0, min(SCREEN_HEIGHT, y)) / SCREEN_HEIGHT
    return score_bonus * horizontal_pressure * (0.25 + vertical_pressure)


def model_debug_lines(action, raw_features, model_features, model=None):
    confidence = prediction_confidence(model, model_features, action)
    action_text = f"AI: {action.upper()}"
    if confidence is not None:
        action_text += f" {confidence:.0%}"

    obstacle_metrics = obstacle_debug_metrics(raw_features)
    total_danger = sum(metric["danger"] for metric in obstacle_metrics)
    total_ore_pull = sum(metric["ore_pull"] for metric in obstacle_metrics)
    lines = [
        action_text,
        f"Features: {len(model_features)}/{len(raw_features)}",
        f"Pressure: danger={total_danger:.2f} ore={total_ore_pull:.2f}",
    ]
    for metric in obstacle_metrics:
        focus = metric["ore_pull"] if metric["kind"] == "ORE" else metric["danger"]
        lines.append(
            f"{metric['label']} {metric['kind']}: "
            f"dx={metric['dx']} y={metric['y']} sp={metric['speed_delta']} "
            f"+{metric['score_bonus']} focus={focus:.2f}"
        )
    return lines


def model_mode_name(model_path, difficulty_preset=None, variant_profile=None):
    details = [os.path.basename(model_path)]
    if difficulty_preset:
        details.append(difficulty_preset)
    if variant_profile and variant_profile != DEFAULT_VARIANT_PROFILE:
        details.append(variant_profile)
    if details:
        return f"{MODE_NAME} ({', '.join(details)})"
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
        "--variant-profile",
        args.variant_profile,
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
    mode_name = model_mode_name(args.model, args.difficulty, args.variant_profile)
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
        variant_profile=args.variant_profile,
    )
    sound_player = GameSoundPlayer(enabled=SOUND_ENABLED and not args.mute)
    clock = pygame.time.Clock()
    screen_state = SCREEN_START
    debug_lines = []
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
            if args.debug_ai:
                action, raw_features, model_features = predict_action_with_debug(model, game)
                debug_lines = model_debug_lines(action, raw_features, model_features, model=model)
            else:
                action = predict_action(model, game)
            game.apply_action(action)
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
            if args.debug_ai:
                game.draw_ai_debug_overlay(debug_lines)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
