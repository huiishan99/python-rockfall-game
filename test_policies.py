import unittest

from policies import (
    POLICY_SAFE_RULE,
    choose_policy_action,
    choose_safe_rule_action,
    policy_label,
)


class PolicyTest(unittest.TestCase):
    def test_policy_label_marks_builtin_policy(self):
        self.assertEqual(policy_label(POLICY_SAFE_RULE), "policy:safe-rule")

    def test_safe_rule_moves_away_from_obstacle_on_right(self):
        game = StubGame(player_x=100, obstacles=[[140, 400, "normal"]])

        self.assertEqual(choose_safe_rule_action(game), "left")

    def test_safe_rule_moves_away_from_obstacle_on_left(self):
        game = StubGame(player_x=100, obstacles=[[70, 400, "normal"]])

        self.assertEqual(choose_safe_rule_action(game), "right")

    def test_safe_rule_moves_toward_center_when_risk_ties(self):
        game = StubGame(player_x=0, obstacles=[])

        self.assertEqual(choose_policy_action(POLICY_SAFE_RULE, game), "right")


class StubGame:
    def __init__(self, player_x, obstacles, player_speed=8):
        self.player_x = player_x
        self.obstacles = obstacles
        self.player_speed = player_speed


if __name__ == "__main__":
    unittest.main()
