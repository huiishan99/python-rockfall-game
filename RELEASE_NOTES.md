# Release Notes

## v0.8.0

Rockfall v0.8.0 turns the original pygame machine-learning prototype into a more complete arcade/ML project. The game now has clearer rules, more readable visuals, richer rock behavior, and a traceable model-training workflow.

### Player-Facing Highlights

- Rock-shaped obstacles now have variants: stone, heavy, swift, and ore.
- Ore awards +2 when avoided, and close-dodging ore adds a `RISK +1` bonus.
- The player is drawn as a mine cart rather than a placeholder square.
- The start screen includes `HOW IT WORKS` and `PLAY WITH MODEL` buttons.
- Model play includes a `TRAIN MANUALLY` path back to data collection.
- Model play can show a debug overlay with predicted action and feature values.
- HUD, pause, game-over, help, hit feedback, combos, close dodges, and life recovery are implemented.

### Machine-Learning Workflow

- Manual samples include rock type so new models can learn variant behavior.
- Model features cover the nearest three rocks, with compatibility for older four- and six-feature models.
- `inspect_data.py` reports data quality and variant coverage.
- `evaluate_model.py` reports survival, variant outcomes, and score-source breakdowns.
- `compare_models.py` can compare models against `policy:safe-rule`, including variant and risk bonus columns.
- `collect_policy_data.py` can generate separate safe-rule demonstration data for experiments.
- `train_model.py --reward-weighting score` can emphasize reward-bearing samples after collecting variant-rich data.
- `model_report.py` ties data quality, standard evaluation, variant-rich stress testing, and baseline comparison into one report.

### Verification

The v0.8.0 release was verified with:

- `python3 -m unittest`
- `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-v08-candidate-release-check.json`
- `python3 model_report.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-v08-candidate-model-report.json`

### Known Notes

- The tracked `game_data.json` predates rock variants, so it is useful as legacy training data but not enough for ore/heavy/swift-specific learning.
- Use `python3 game.py --data runs/variant_rich.json --variant-profile variant-rich` or `python3 collect_policy_data.py --data runs/policy_variant_rich.json` before training new reward-aware candidates.
- The current tracked `game_model.pkl` remains compatible, but future models should be retrained and compared with the v0.8 reporting tools.
