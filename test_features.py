import unittest

from features import (
    FEATURE_NAMES,
    LEGACY_FEATURE_NAMES,
    MAX_MODEL_OBSTACLES,
    SINGLE_OBSTACLE_FEATURE_NAMES,
    adapt_features_for_model,
    build_model_features,
    select_nearest_obstacle,
    select_nearest_obstacles,
)


class ModelFeatureTest(unittest.TestCase):
    def test_selects_obstacle_closest_to_player_by_y_position(self):
        self.assertEqual(select_nearest_obstacle([(100, 20), (250, 300), (400, 120)]), (250, 300, "normal"))

    def test_ignores_invalid_obstacles(self):
        self.assertEqual(select_nearest_obstacle([(100, 20), ("bad", 300), (400, "bad")]), (100, 20, "normal"))

    def test_selects_three_nearest_obstacles_by_y_position(self):
        obstacles = [(100, 20), (250, 300, "ore"), (400, 120, "swift"), (500, 40)]

        self.assertEqual(
            select_nearest_obstacles(obstacles),
            [(250, 300, "ore"), (400, 120, "swift"), (500, 40, "normal")],
        )

    def test_builds_distance_features(self):
        features = build_model_features(200, [(100, 20), (260, 300)])

        self.assertEqual(
            features,
            [
                200,
                260,
                300,
                60,
                0,
                0,
                100,
                20,
                -100,
                0,
                0,
                200,
                0,
                0,
                0,
                0,
            ],
        )

    def test_builds_variant_effect_features(self):
        features = build_model_features(200, [(260, 300, "ore")])

        self.assertEqual(features[: len(SINGLE_OBSTACLE_FEATURE_NAMES)], [200, 260, 300, 60, 0, 2])

    def test_builds_swift_speed_feature(self):
        features = build_model_features(200, [(260, 300, "swift")])

        self.assertEqual(features[: len(SINGLE_OBSTACLE_FEATURE_NAMES)], [200, 260, 300, 60, 2, 0])

    def test_unknown_variant_defaults_to_normal_features(self):
        features = build_model_features(200, [(260, 300, "mystery")])

        self.assertEqual(features[: len(SINGLE_OBSTACLE_FEATURE_NAMES)], [200, 260, 300, 60, 0, 0])

    def test_no_obstacle_uses_neutral_position(self):
        features = build_model_features(200, [])

        self.assertEqual(features, [200] + [200, 0, 0, 0, 0] * MAX_MODEL_OBSTACLES)

    def test_feature_names_include_variant_effects_after_legacy_position_features(self):
        self.assertEqual(FEATURE_NAMES[: len(LEGACY_FEATURE_NAMES)], LEGACY_FEATURE_NAMES)
        self.assertEqual(FEATURE_NAMES[: len(SINGLE_OBSTACLE_FEATURE_NAMES)], SINGLE_OBSTACLE_FEATURE_NAMES)
        self.assertIn("nearest_obstacle_score_bonus", FEATURE_NAMES)
        self.assertIn("third_obstacle_score_bonus", FEATURE_NAMES)

    def test_adapts_features_for_legacy_model(self):
        class LegacyModel:
            n_features_in_ = len(LEGACY_FEATURE_NAMES)

        features = [200] + [260, 300, 60, 0, 2] * MAX_MODEL_OBSTACLES

        self.assertEqual(adapt_features_for_model(features, LegacyModel()), [200, 260, 300, 60])

    def test_adapts_features_for_single_obstacle_model(self):
        class SingleObstacleModel:
            n_features_in_ = len(SINGLE_OBSTACLE_FEATURE_NAMES)

        features = [200] + [260, 300, 60, 0, 2] * MAX_MODEL_OBSTACLES

        self.assertEqual(adapt_features_for_model(features, SingleObstacleModel()), [200, 260, 300, 60, 0, 2])

    def test_adapts_features_for_current_model(self):
        class CurrentModel:
            n_features_in_ = len(FEATURE_NAMES)

        features = [200] + [260, 300, 60, 0, 2] * MAX_MODEL_OBSTACLES

        self.assertEqual(adapt_features_for_model(features, CurrentModel()), features)

    def test_rejects_unsupported_model_feature_count(self):
        class UnsupportedModel:
            n_features_in_ = 5

        with self.assertRaises(ValueError):
            adapt_features_for_model([200, 260, 300, 60, 0, 2], UnsupportedModel())


if __name__ == "__main__":
    unittest.main()
