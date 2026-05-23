import json
import os
import tempfile
import unittest

from inspect_data import format_inspection_lines, parse_args, validate_args, write_inspection_report


class InspectDataTest(unittest.TestCase):
    def test_parse_args_accepts_report_and_json(self):
        args = parse_args(["--data", "runs/playtest.json", "--report", "runs/data_report.json", "--json"])

        self.assertEqual(args.data, "runs/playtest.json")
        self.assertEqual(args.report, "runs/data_report.json")
        self.assertTrue(args.json)

    def test_validate_args_rejects_invalid_thresholds(self):
        with self.assertRaises(ValueError):
            validate_args(parse_args(["--min-samples", "0"]))
        with self.assertRaises(ValueError):
            validate_args(parse_args(["--min-balance-ratio", "1.5"]))
        with self.assertRaises(ValueError):
            validate_args(parse_args(["--max-skipped-ratio", "-0.1"]))

    def test_formats_inspection_lines_with_warnings(self):
        payload = {
            "data": "game_data.json",
            "valid_samples": 51,
            "skipped_entries": 2,
            "features": ["player_x", "nearest_obstacle_x"],
            "action_balance": {"left": 5, "right": 46},
            "data_quality": {
                "status": "needs_more_data",
                "warnings": ["valid_samples_below_500"],
                "skipped_ratio": 0.03773584905660377,
                "balance_ratio": 0.09803921568627451,
            },
            "variant_coverage": {
                "status": "needs_variant_data",
                "warnings": ["no_recorded_variant_samples"],
                "variant_counts": {"normal": 0, "heavy": 0, "swift": 0, "ore": 0},
                "recorded_variant_samples": 0,
                "legacy_obstacle_samples": 51,
                "variant_sample_ratio": 0,
            },
        }

        lines = format_inspection_lines(payload)

        self.assertIn("Data quality: needs_more_data", lines)
        self.assertIn("Data quality warnings: valid_samples_below_500", lines)
        self.assertIn("Variant quality: needs_variant_data", lines)
        self.assertIn("Variant warnings: no_recorded_variant_samples", lines)
        self.assertIn("Balance ratio: 0.098", lines)

    def test_write_inspection_report_creates_parent_directory(self):
        payload = {"data": "game_data.json", "valid_samples": 2}
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = os.path.join(temp_dir, "reports", "data.json")

            write_inspection_report(payload, report_path)

            with open(report_path, "r") as report_file:
                self.assertEqual(json.load(report_file), payload)


if __name__ == "__main__":
    unittest.main()
