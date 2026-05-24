import unittest

from policies import (
    POLICY_ORE_HUNTER,
    POLICY_SAFE_RULE,
    built_in_policy_names,
    choose_policy_action,
    choose_ore_hunter_action,
    choose_safe_rule_action,
    policy_label,
)


class PolicyTest(unittest.TestCase):
    def test_policy_label_marks_builtin_policy(self):
        self.assertEqual(policy_label(POLICY_SAFE_RULE), "policy:safe-rule")

    def test_builtin_policies_include_ore_hunter(self):
        self.assertIn(POLICY_ORE_HUNTER, built_in_policy_names())

    def test_safe_rule_moves_away_from_obstacle_on_right(self):
        game = StubGame(player_x=100, obstacles=[[140, 400, "normal"]])

        self.assertEqual(choose_safe_rule_action(game), "left")

    def test_safe_rule_moves_away_from_obstacle_on_left(self):
        game = StubGame(player_x=100, obstacles=[[70, 400, "normal"]])

        self.assertEqual(choose_safe_rule_action(game), "right")

    def test_safe_rule_moves_toward_center_when_risk_ties(self):
        game = StubGame(player_x=0, obstacles=[])

        self.assertEqual(choose_policy_action(POLICY_SAFE_RULE, game), "right")

    def test_ore_hunter_moves_toward_collectable_ore_when_healthy(self):
        game = StubGame(player_x=100, obstacles=[[135, 400, "ore"]], lives=3)

        self.assertEqual(choose_ore_hunter_action(game), "right")

    def test_ore_hunter_avoids_ore_when_low_on_lives(self):
        game = StubGame(player_x=100, obstacles=[[135, 400, "ore"]], lives=1)

        self.assertEqual(choose_policy_action(POLICY_ORE_HUNTER, game), "left")

    def test_ore_hunter_prioritizes_stone_safety_over_ore(self):
        game = StubGame(
            player_x=100,
            obstacles=[
                [135, 400, "ore"],
                [150, 430, "normal"],
            ],
            lives=3,
        )

        self.assertEqual(choose_ore_hunter_action(game), "left")


class StubGame:
    def __init__(self, player_x, obstacles, player_speed=8, lives=3, combo=0):
        self.player_x = player_x
        self.obstacles = obstacles
        self.player_speed = player_speed
        self.lives = lives
        self.combo = combo

    def combo_bonus_points(self):
        return self.combo // 5


if __name__ == "__main__":
    unittest.main()
