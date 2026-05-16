import unittest

from features import build_model_features, select_nearest_obstacle


class ModelFeatureTest(unittest.TestCase):
    def test_selects_obstacle_closest_to_player_by_y_position(self):
        self.assertEqual(select_nearest_obstacle([(100, 20), (250, 300), (400, 120)]), (250, 300))

    def test_ignores_invalid_obstacles(self):
        self.assertEqual(select_nearest_obstacle([(100, 20), ("bad", 300), (400, "bad")]), (100, 20))

    def test_builds_distance_features(self):
        features = build_model_features(200, [(100, 20), (260, 300)])

        self.assertEqual(features, [200, 260, 300, 60])

    def test_no_obstacle_uses_neutral_position(self):
        features = build_model_features(200, [])

        self.assertEqual(features, [200, 200, 0, 0])


if __name__ == "__main__":
    unittest.main()
