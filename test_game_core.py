import os
import unittest

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from game_events import EVENT_AVOID, EVENT_HIT, EVENT_LEVEL_UP
from game_core import ACTION_LEFT, ACTION_RIGHT, RockfallGame
from settings import (
    BACKGROUND_COLOR,
    COMBO_BONUS_INTERVAL,
    DEFAULT_OBSTACLE_VARIANT,
    DIFFICULTY_INTERVAL_FRAMES,
    HUD_COMBO_COLOR,
    HUD_COLOR,
    HUD_PANEL_BORDER_COLOR,
    HUD_PANEL_COLOR,
    HUD_PROGRESS_BACK_COLOR,
    HUD_WARNING_COLOR,
    INITIAL_LIVES,
    INVINCIBILITY_FRAMES,
    HIT_OVERLAY_MAX_ALPHA,
    LANE_HIGHLIGHT_COLOR,
    LIFE_RESTORE_INTERVAL,
    LIFE_RESTORE_MESSAGE_COLOR,
    MENU_ACCENT_COLOR,
    MENU_PANEL_BORDER_COLOR,
    MENU_PANEL_COLOR,
    MENU_SECONDARY_COLOR,
    MESSAGE_DURATION_FRAMES,
    NEAR_MISS_MESSAGE_COLOR,
    LOW_LIVES_THRESHOLD,
    OBSTACLE_COLOR,
    OBSTACLE_CRACK_COLOR,
    OBSTACLE_HIGHLIGHT_COLOR,
    OBSTACLE_SHADOW_COLOR,
    OBSTACLE_VARIANTS,
    PLAYER_COLOR,
    PLAYER_HIT_COLOR,
    PLAYER_OUTLINE_COLOR,
    PLAYER_RIM_COLOR,
    PLAYER_SHADOW_COLOR,
    PLAYER_WHEEL_COLOR,
    PLAYER_WIDTH,
    PROMPT_BACK_COLOR,
    PROMPT_BORDER_COLOR,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)


class GameCoreHitFeedbackTest(unittest.TestCase):
    def setUp(self):
        pygame.font.init()
        self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    def tearDown(self):
        pygame.font.quit()

    def test_hit_reduces_life_and_starts_invincibility(self):
        game = RockfallGame(self.screen)

        game._handle_hit()

        self.assertEqual(game.lives, INITIAL_LIVES - 1)
        self.assertEqual(game.invincibility_frames, INVINCIBILITY_FRAMES)

    def test_apply_action_clamps_player_to_left_edge(self):
        game = RockfallGame(self.screen)
        game.player_x = 0

        game.apply_action(ACTION_LEFT)

        self.assertEqual(game.player_x, 0)

    def test_apply_action_clamps_player_to_right_edge(self):
        game = RockfallGame(self.screen)
        game.player_x = SCREEN_WIDTH

        game.apply_action(ACTION_RIGHT)

        self.assertEqual(game.player_x, SCREEN_WIDTH - PLAYER_WIDTH)

    def test_apply_action_ignores_missing_action(self):
        game = RockfallGame(self.screen)
        starting_x = game.player_x

        game.apply_action(None)

        self.assertEqual(game.player_x, starting_x)

    def test_apply_action_uses_configured_player_speed(self):
        game = RockfallGame(self.screen, player_speed=8)
        starting_x = game.player_x

        game.apply_action(ACTION_RIGHT)

        self.assertEqual(game.player_x, starting_x + 8)

    def test_reset_uses_configured_initial_lives(self):
        game = RockfallGame(self.screen, initial_lives=3)
        game.lives = 1

        game.reset()

        self.assertEqual(game.lives, 3)

    def test_reset_resets_life_restore_threshold(self):
        game = RockfallGame(self.screen)
        game.next_life_restore_score = LIFE_RESTORE_INTERVAL * 2

        game.reset()

        self.assertEqual(game.next_life_restore_score, LIFE_RESTORE_INTERVAL)

    def test_difficulty_preset_changes_initial_pressure(self):
        normal_game = RockfallGame(self.screen, difficulty_preset="normal")
        hard_game = RockfallGame(self.screen, difficulty_preset="hard")

        self.assertLessEqual(hard_game.obstacle_frequency, normal_game.obstacle_frequency)

    def test_invincibility_prevents_extra_life_loss(self):
        game = RockfallGame(self.screen)

        game._handle_hit()
        game._handle_hit()

        self.assertEqual(game.lives, INITIAL_LIVES - 1)

    def test_invincibility_ticks_down(self):
        game = RockfallGame(self.screen)
        game._handle_hit()

        game._tick_invincibility()

        self.assertEqual(game.invincibility_frames, INVINCIBILITY_FRAMES - 1)

    def test_player_flashes_while_invincible(self):
        game = RockfallGame(self.screen)
        self.assertEqual(game.player_color(), PLAYER_COLOR)

        game._handle_hit()

        self.assertIn(game.player_color(), (PLAYER_COLOR, PLAYER_HIT_COLOR))

    def test_hit_overlay_alpha_fades_with_invincibility(self):
        game = RockfallGame(self.screen)

        game._handle_hit()
        initial_alpha = game.hit_overlay_alpha()
        game.invincibility_frames = 1

        self.assertEqual(initial_alpha, HIT_OVERLAY_MAX_ALPHA)
        self.assertLess(game.hit_overlay_alpha(), initial_alpha)
        game.invincibility_frames = 0
        self.assertEqual(game.hit_overlay_alpha(), 0)

    def test_hit_adds_message(self):
        game = RockfallGame(self.screen)

        game._handle_hit()

        self.assertEqual(game.messages[-1]["text"], "HIT!")
        self.assertEqual(game.pop_events(), [EVENT_HIT])

    def test_messages_tick_down_and_float(self):
        game = RockfallGame(self.screen)
        game._add_message("+1", (255, 255, 255), 10, 20)

        game._tick_messages()

        self.assertEqual(game.messages[0]["frames"], MESSAGE_DURATION_FRAMES - 1)
        self.assertEqual(game.messages[0]["y"], 19)

    def test_messages_expire(self):
        game = RockfallGame(self.screen)
        game._add_message("+1", (255, 255, 255), 10, 20, duration=1)

        game._tick_messages()

        self.assertEqual(game.messages, [])

    def test_game_over_lines_include_run_summary(self):
        game = RockfallGame(self.screen)
        game.score = 12
        game.difficulty_level = 3
        game.lives = 2

        lines = game.game_over_lines("Model Play")

        self.assertIn("Model Play", lines)
        self.assertIn("Final Score: 12", lines)
        self.assertIn("Level Reached: 3", lines)
        self.assertIn("Lives Left: 2", lines)

    def test_start_lines_include_controls(self):
        game = RockfallGame(self.screen)

        lines = game.start_lines("Data Collection")

        self.assertIn("Move: Left/Right or A/D", lines)
        self.assertIn("Pause: P", lines)
        self.assertIn("Press SPACE to start", lines)

    def test_model_missing_lines_explain_training_step(self):
        game = RockfallGame(self.screen)

        lines = game.model_missing_lines("game_model.pkl")

        self.assertIn("Missing model: game_model.pkl", lines)
        self.assertTrue(any("train_model.py" in line for line in lines))

    def test_help_lines_explain_machine_learning_loop(self):
        game = RockfallGame(self.screen)

        lines = game.help_lines()

        self.assertTrue(any("records state" in line for line in lines))
        self.assertTrue(any("train_model.py" in line for line in lines))
        self.assertTrue(any("predicts movement" in line for line in lines))

    def test_pause_lines_include_controls(self):
        game = RockfallGame(self.screen)

        lines = game.pause_lines("Data Collection")

        self.assertIn("Move: Left/Right or A/D", lines)
        self.assertIn("Press P to resume", lines)
        self.assertIn("Press R to restart", lines)

    def test_pause_lines_include_current_run_summary(self):
        game = RockfallGame(self.screen)
        game.score = 12
        game.high_score = 20
        game.difficulty_level = 3
        game.lives = 4
        game.combo = 5

        lines = game.pause_lines("Data Collection")

        self.assertIn("Score: 12  Best: 20", lines)
        self.assertIn("Level: 3  Lives: 4  Combo: 5", lines)

    def test_avoiding_obstacles_builds_combo_and_score(self):
        game = RockfallGame(self.screen)

        game._handle_avoid(100)

        self.assertEqual(game.combo, 1)
        self.assertEqual(game.best_combo, 1)
        self.assertEqual(game.score, 1)
        self.assertEqual(game.pop_events(), [EVENT_AVOID])

    def test_old_obstacles_default_to_normal_variant(self):
        game = RockfallGame(self.screen)

        self.assertEqual(game.obstacle_variant([100, 200]), DEFAULT_OBSTACLE_VARIANT)

    def test_snapshot_keeps_variant_out_of_training_state(self):
        game = RockfallGame(self.screen)
        game.obstacles = [[100, 200, "ore"]]

        self.assertEqual(game.snapshot()["obstacles"], [(100, 200)])

    def test_spawned_obstacles_include_variant_key(self):
        game = RockfallGame(self.screen)
        game.choose_obstacle_variant = lambda: "ore"
        game.frame_count = game.obstacle_frequency - 1

        game._spawn_obstacle()

        self.assertEqual(game.obstacles[0][2], "ore")

    def test_variant_speed_changes_fall_rate(self):
        game = RockfallGame(self.screen)
        game.obstacle_speed = 5

        normal_speed = game.obstacle_fall_speed([100, 0, "normal"])
        heavy_speed = game.obstacle_fall_speed([100, 0, "heavy"])
        swift_speed = game.obstacle_fall_speed([100, 0, "swift"])

        self.assertLess(heavy_speed, normal_speed)
        self.assertGreater(swift_speed, normal_speed)

    def test_ore_avoid_adds_score_bonus_message(self):
        game = RockfallGame(self.screen)

        game._handle_avoid(20, score_bonus=OBSTACLE_VARIANTS["ore"]["score_bonus"], variant_key="ore")

        messages = [message["text"] for message in game.messages]
        self.assertEqual(game.score, 3)
        self.assertIn("+3", messages)
        self.assertIn("ORE +2", messages)

    def test_combo_bonus_increases_score_after_interval(self):
        game = RockfallGame(self.screen)

        for _ in range(COMBO_BONUS_INTERVAL):
            game._handle_avoid(100)

        self.assertEqual(game.combo, COMBO_BONUS_INTERVAL)
        self.assertEqual(game.combo_points(), 2)
        self.assertEqual(game.score, COMBO_BONUS_INTERVAL + 1)

    def test_hit_resets_combo(self):
        game = RockfallGame(self.screen)
        game._handle_avoid(100)
        game._handle_avoid(100)

        game._handle_hit()

        self.assertEqual(game.combo, 0)
        self.assertEqual(game.best_combo, 2)

    def test_near_miss_detection_uses_horizontal_centers(self):
        game = RockfallGame(self.screen)
        game.player_x = 100

        self.assertTrue(game.is_near_miss(160))
        self.assertFalse(game.is_near_miss(300))

    def test_near_miss_adds_message_without_score_bonus(self):
        game = RockfallGame(self.screen)
        game.player_x = 100

        game._handle_avoid(160)

        messages = [message["text"] for message in game.messages]
        self.assertIn("CLOSE!", messages)
        self.assertEqual(game.messages[-1]["color"], NEAR_MISS_MESSAGE_COLOR)
        self.assertEqual(game.score, 1)

    def test_score_milestone_restores_life_when_damaged(self):
        game = RockfallGame(self.screen, initial_lives=3)
        game.lives = 2
        game.score = LIFE_RESTORE_INTERVAL - 1

        game._handle_avoid(100)

        self.assertEqual(game.lives, 3)
        self.assertEqual(game.next_life_restore_score, LIFE_RESTORE_INTERVAL * 2)
        self.assertEqual(game.messages[-1]["text"], "LIFE +1")
        self.assertEqual(game.messages[-1]["color"], LIFE_RESTORE_MESSAGE_COLOR)

    def test_score_milestone_does_not_exceed_initial_lives(self):
        game = RockfallGame(self.screen, initial_lives=3)
        game.score = LIFE_RESTORE_INTERVAL - 1

        game._handle_avoid(100)

        self.assertEqual(game.lives, 3)
        self.assertEqual(game.next_life_restore_score, LIFE_RESTORE_INTERVAL * 2)

    def test_lives_color_warns_when_low(self):
        game = RockfallGame(self.screen)
        self.assertEqual(game.lives_color(), HUD_COLOR)

        game.lives = LOW_LIVES_THRESHOLD

        self.assertEqual(game.lives_color(), HUD_WARNING_COLOR)

    def test_combo_color_highlights_active_combo(self):
        game = RockfallGame(self.screen)
        self.assertEqual(game.combo_color(), HUD_COLOR)

        game.combo = 1

        self.assertEqual(game.combo_color(), HUD_COMBO_COLOR)

    def test_game_over_lines_include_best_combo(self):
        game = RockfallGame(self.screen)
        game.best_combo = 7

        lines = game.game_over_lines("Model Play")

        self.assertIn("Best Combo: 7", lines)

    def test_pop_events_clears_event_queue(self):
        game = RockfallGame(self.screen)
        game._handle_avoid(100)

        self.assertEqual(game.pop_events(), [EVENT_AVOID])
        self.assertEqual(game.pop_events(), [])

    def test_level_up_emits_event(self):
        game = RockfallGame(self.screen)
        game.game_time = DIFFICULTY_INTERVAL_FRAMES - 1

        game._increase_difficulty()

        self.assertEqual(game.pop_events(), [EVENT_LEVEL_UP])

    def test_draw_uses_styled_background(self):
        game = RockfallGame(self.screen)

        game.draw()

        self.assertEqual(self.screen.get_at((3, 3))[:3], BACKGROUND_COLOR)

    def test_draw_adds_mine_cart_player_shape(self):
        game = RockfallGame(self.screen)

        game.draw()

        self.assertEqual(self.screen.get_at((game.player_x + 25, game.player_y + 15))[:3], PLAYER_RIM_COLOR)
        self.assertEqual(self.screen.get_at((game.player_x + 20, game.player_y + 28))[:3], PLAYER_COLOR)
        self.assertEqual(self.screen.get_at((game.player_x + 38, game.player_y + 28))[:3], PLAYER_SHADOW_COLOR)
        self.assertEqual(self.screen.get_at((game.player_x + 15, game.player_y + 42))[:3], PLAYER_WHEEL_COLOR)

    def test_draw_hit_overlay_tints_background_after_hit(self):
        game = RockfallGame(self.screen)
        game._handle_hit()

        game.draw()

        self.assertNotEqual(self.screen.get_at((3, 3))[:3], BACKGROUND_COLOR)

    def test_draw_adds_rock_highlight_shadow_and_cracks(self):
        game = RockfallGame(self.screen)
        game.obstacles = [[260, 180]]

        game.draw()

        self.assertEqual(self.screen.get_at((272, 188))[:3], OBSTACLE_HIGHLIGHT_COLOR)
        self.assertEqual(self.screen.get_at((286, 210))[:3], OBSTACLE_COLOR)
        self.assertEqual(self.screen.get_at((310, 205))[:3], OBSTACLE_SHADOW_COLOR)
        self.assertEqual(self.screen.get_at((290, 207))[:3], OBSTACLE_CRACK_COLOR)

    def test_draw_adds_ore_variant_marker(self):
        game = RockfallGame(self.screen)
        game.obstacles = [[260, 180, "ore"]]

        game.draw()

        self.assertEqual(self.screen.get_at((280, 206))[:3], OBSTACLE_VARIANTS["ore"]["mark"])

    def test_incoming_obstacle_draws_clipped_rock_without_warning_strip(self):
        game = RockfallGame(self.screen)
        game.obstacles = [[100, -30]]

        game.draw()

        self.assertNotEqual(self.screen.get_at((101, 1))[:3], MENU_ACCENT_COLOR)

    def test_message_line_colors_highlight_mode_and_controls(self):
        game = RockfallGame(self.screen)

        self.assertEqual(game._message_line_color(0, "Data Collection"), MENU_ACCENT_COLOR)
        self.assertEqual(game._message_line_color(2, "Press SPACE to start"), MENU_SECONDARY_COLOR)
        self.assertEqual(game._message_line_color(1, "High Score: 10"), HUD_COLOR)

    def test_start_screen_uses_styled_background_and_divider(self):
        game = RockfallGame(self.screen)

        game.draw_start_screen("Data Collection")

        self.assertEqual(self.screen.get_at((25, 3))[:3], LANE_HIGHLIGHT_COLOR)
        self.assertEqual(self.screen.get_at((SCREEN_WIDTH // 2, 220))[:3], MENU_ACCENT_COLOR)
        self.assertEqual(self.screen.get_at((SCREEN_WIDTH // 2, 235))[:3], MENU_PANEL_BORDER_COLOR)
        self.assertEqual(self.screen.get_at((SCREEN_WIDTH // 2, 240))[:3], MENU_PANEL_COLOR)

    def test_start_screen_draws_help_button(self):
        game = RockfallGame(self.screen)

        game.draw_start_screen("Data Collection")

        button_rect = game.help_button_rect()
        self.assertEqual(self.screen.get_at(button_rect.topleft)[:3], PROMPT_BORDER_COLOR)
        self.assertEqual(self.screen.get_at((button_rect.x + 3, button_rect.y + 3))[:3], PROMPT_BACK_COLOR)

    def test_start_screen_draws_model_button_when_enabled(self):
        game = RockfallGame(self.screen)

        game.draw_start_screen("Data Collection")

        button_rect = game.model_button_rect()
        self.assertEqual(self.screen.get_at(button_rect.topleft)[:3], PROMPT_BORDER_COLOR)
        self.assertEqual(self.screen.get_at((button_rect.x + 3, button_rect.y + 3))[:3], PROMPT_BACK_COLOR)

    def test_start_screen_can_hide_model_button(self):
        game = RockfallGame(self.screen)

        game.draw_start_screen("Model Play", show_model_button=False)

        button_rect = game.model_button_rect()
        self.assertNotEqual(self.screen.get_at(button_rect.topleft)[:3], PROMPT_BORDER_COLOR)

    def test_start_screen_draws_training_button_when_enabled(self):
        game = RockfallGame(self.screen)

        game.draw_start_screen("Model Play", show_model_button=False, show_training_button=True)

        button_rect = game.training_button_rect()
        self.assertEqual(self.screen.get_at(button_rect.topleft)[:3], PROMPT_BORDER_COLOR)
        self.assertEqual(self.screen.get_at((button_rect.x + 3, button_rect.y + 3))[:3], PROMPT_BACK_COLOR)

    def test_help_screen_draws_panel_and_action_buttons(self):
        game = RockfallGame(self.screen)

        game.draw_help_screen()

        panel_rect = game.help_panel_rect()
        back_rect = game.help_back_button_rect()
        start_rect = game.help_start_button_rect()
        self.assertEqual(self.screen.get_at(panel_rect.topleft)[:3], MENU_PANEL_BORDER_COLOR)
        self.assertEqual(self.screen.get_at((panel_rect.x + 3, panel_rect.y + 3))[:3], MENU_PANEL_COLOR)
        self.assertEqual(self.screen.get_at(back_rect.topleft)[:3], PROMPT_BORDER_COLOR)
        self.assertEqual(self.screen.get_at(start_rect.topleft)[:3], PROMPT_BORDER_COLOR)

    def test_help_screen_draws_rock_variant_legend(self):
        game = RockfallGame(self.screen)

        game.draw_help_screen()

        card_rects = game.rock_legend_card_rects()
        ore_card_rect = card_rects[3]
        self.assertEqual(self.screen.get_at(card_rects[0].topleft)[:3], PROMPT_BORDER_COLOR)
        self.assertEqual(
            self.screen.get_at((ore_card_rect.x + 27, ore_card_rect.y + 34))[:3],
            OBSTACLE_VARIANTS["ore"]["mark"],
        )

    def test_model_missing_screen_draws_back_button(self):
        game = RockfallGame(self.screen)

        game.draw_model_missing_screen("game_model.pkl")

        back_rect = game.help_back_button_rect()
        self.assertEqual(self.screen.get_at(back_rect.topleft)[:3], PROMPT_BORDER_COLOR)

    def test_hud_draws_progress_background(self):
        game = RockfallGame(self.screen)

        game.draw()

        progress_back_pixel = (game.progress_bar_x + 120, game.progress_bar_y + 5)
        self.assertEqual(self.screen.get_at(progress_back_pixel)[:3], HUD_PROGRESS_BACK_COLOR)

    def test_hud_draws_stats_panel(self):
        game = RockfallGame(self.screen)

        game.draw()

        self.assertEqual(self.screen.get_at((8, 8))[:3], HUD_PANEL_BORDER_COLOR)
        self.assertEqual(self.screen.get_at((12, 12))[:3], HUD_PANEL_COLOR)


if __name__ == "__main__":
    unittest.main()
