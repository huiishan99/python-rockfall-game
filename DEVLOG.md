# Devlog

This file records meaningful project changes so bugs, design decisions, and model behavior changes can be traced later.

## Rules

- Add a new entry for every code, data, model, or documentation change.
- Keep entries newest first.
- Mention changed files, user-visible behavior, verification steps, and any known risks.
- When a bug is fixed, include the symptom and the likely cause.
- When `game_data.json` or `game_model.pkl` changes, describe how the data/model was produced.

## Entry Template

```md
## YYYY-MM-DD - Short title

- Changed: files or systems touched.
- Why: reason for the change.
- Behavior: what should be different for players or developers.
- Verification: commands/tests/manual checks run.
- Risks/Notes: known limitations, follow-ups, or rollback clues.
```

## 2026-05-24 - Make ore collection cost health

- Changed: updated ore scoring in `game_core.py` and `settings.py`; changed score summaries in `evaluate_model.py`, `compare_models.py`, and `model_report.py` to surface missed-ore penalties; moved the ore-target objective and default run paths to `ore_target_v2` in `data_store.py`; refreshed README and tests.
- Why: playtesting showed the old rule felt backwards: ore flashed `+ORE` when avoided, while catching it only behaved like a hit. The intended decision is more interesting if the player can take ore for reward while paying health, and misses lose ore score.
- Behavior: catching ore now awards +5 ore score plus any combo bonus, then costs 1 life and starts hit invincibility; missed ore subtracts up to 2 ore score without making score negative; ordinary stones remain survival/combo pressure; manual and policy data now tag new samples as `ore_target_v2` and write to v2 default paths.
- Verification: ran `python3 -m unittest test_game_core.py test_evaluate_model.py test_compare_models.py test_train_model.py test_run_model_experiment.py test_collect_policy_data.py test_model_report.py test_inspect_data.py`; ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile collect_policy_data.py compare_models.py data_quality.py data_store.py difficulty.py evaluate_model.py features.py game.py game_audio.py game_core.py game_events.py inspect_data.py model_report.py play_with_model.py policies.py release_check.py run_model_experiment.py scores.py settings.py spawning.py train_model.py test_collect_policy_data.py test_compare_models.py test_data_quality.py test_data_store.py test_difficulty.py test_evaluate_model.py test_features.py test_game.py test_game_audio.py test_game_core.py test_inspect_data.py test_model_report.py test_play_with_model.py test_policies.py test_release_check.py test_run_model_experiment.py test_scores.py test_spawning.py test_train_model.py`; ran `python3 inspect_data.py --data runs/ore_target_manual.json`; ran `python3 collect_policy_data.py --data /private/tmp/rockfall-ore-collect-policy-v2.json --games 2 --max-frames 240 --difficulty normal --player-speed 8 --lives 3 --variant-profile variant-rich --report /private/tmp/rockfall-ore-collect-policy-v2-report.json`; ran `python3 train_model.py --data /private/tmp/rockfall-ore-collect-policy-v2.json --model /private/tmp/rockfall-ore-collect-model-v2.pkl --estimators 5 --reward-weighting score --require-objective ore_target_v2`; ran `python3 run_model_experiment.py --data /private/tmp/rockfall-ore-collect-policy-v2.json --candidate /private/tmp/rockfall-ore-collect-candidate-v2.pkl --estimators 5 --reward-weighting score --require-objective ore_target_v2 --games 1 --max-frames 240 --difficulty normal --player-speed 8 --lives 3 --variant-profile variant-rich --report /private/tmp/rockfall-ore-collect-experiment-v2.json`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-ore-collect-release-check-v2.json`; ran `python3 model_report.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-ore-collect-model-report-v2.json`; ran `python3 -m json.tool /private/tmp/rockfall-ore-collect-policy-v2-report.json`; ran `python3 -m json.tool /private/tmp/rockfall-ore-collect-experiment-v2.json`; ran `python3 -m json.tool /private/tmp/rockfall-ore-collect-release-check-v2.json`; ran `python3 -m json.tool /private/tmp/rockfall-ore-collect-model-report-v2.json`; ran a stale-text scan for old ore-target/risk-bonus docs; ran `git diff --check`.
- Risks/Notes: the manual playtest produced 1798 ignored samples in `runs/ore_target_manual.json` under the old `ore_target_v1` semantics; after the objective bump, inspection correctly reports them as non-target data for `ore_target_v2`, so collect fresh v2 samples before retraining a real replacement model. The tiny policy smoke dataset trained successfully but still warned about sample count and missing swift examples.

## 2026-05-24 - Add ore-target training workflow

- Changed: added `ore_target_v1` data-entry metadata and ore-target default data paths in `data_store.py`, `game.py`, `inspect_data.py`, `train_model.py`, `collect_policy_data.py`, and `run_model_experiment.py`; added objective coverage checks in `data_quality.py`, `model_report.py`, training output, inspection output, policy collection output, and experiment output; bumped the dev version to `0.8.2-dev`; refreshed README and tests.
- Why: after making ore the main reward, new training data needs to be traceable as ore-target data instead of being silently mixed with legacy `game_data.json` samples from earlier scoring rules.
- Behavior: manual play now appends to `runs/ore_target_manual.json` by default and tags samples with `objective: ore_target_v1`; safe-rule collection writes `runs/policy_ore_target.json` by default; `inspect_data.py`, `train_model.py`, `model_report.py`, and experiment reports show objective coverage; `train_model.py` and `run_model_experiment.py` can fail fast with `--require-objective ore_target_v1` if the dataset is legacy or mixed.
- Verification: ran `python3 -m unittest test_data_store.py test_data_quality.py test_inspect_data.py test_train_model.py test_game.py test_collect_policy_data.py test_run_model_experiment.py test_model_report.py`; ran `python3 -m unittest`; ran `python3 collect_policy_data.py --data /private/tmp/rockfall-ore-target-policy.json --games 2 --max-frames 240 --difficulty normal --player-speed 8 --lives 3 --variant-profile variant-rich --report /private/tmp/rockfall-ore-target-policy-report.json`; ran `python3 inspect_data.py --data game_data.json`; ran `python3 train_model.py --data /private/tmp/rockfall-ore-target-policy.json --model /private/tmp/rockfall-ore-target-model.pkl --estimators 5 --reward-weighting score --require-objective ore_target_v1`; ran `python3 run_model_experiment.py --data /private/tmp/rockfall-ore-target-policy.json --candidate /private/tmp/rockfall-ore-target-candidate.pkl --estimators 5 --reward-weighting score --require-objective ore_target_v1 --games 1 --max-frames 240 --difficulty normal --player-speed 8 --lives 3 --variant-profile variant-rich --report /private/tmp/rockfall-ore-target-experiment.json`; ran `python3 -m json.tool /private/tmp/rockfall-ore-target-policy-report.json`; ran `python3 -m json.tool /private/tmp/rockfall-ore-target-experiment.json`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile collect_policy_data.py compare_models.py data_quality.py data_store.py difficulty.py evaluate_model.py features.py game.py game_audio.py game_core.py game_events.py inspect_data.py model_report.py play_with_model.py policies.py release_check.py run_model_experiment.py scores.py settings.py spawning.py train_model.py test_collect_policy_data.py test_compare_models.py test_data_quality.py test_data_store.py test_difficulty.py test_evaluate_model.py test_features.py test_game.py test_game_audio.py test_game_core.py test_inspect_data.py test_model_report.py test_play_with_model.py test_policies.py test_release_check.py test_run_model_experiment.py test_scores.py test_spawning.py test_train_model.py`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-ore-target-workflow-release-check.json`; ran `python3 model_report.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-ore-target-workflow-model-report.json`; ran `python3 -m json.tool /private/tmp/rockfall-ore-target-workflow-release-check.json`; ran `python3 -m json.tool /private/tmp/rockfall-ore-target-workflow-model-report.json`; ran `git diff --check`.
- Risks/Notes: this does not replace `game_model.pkl`; it creates the safer workflow for collecting and validating new ore-target data first. The short policy-generated smoke dataset still warned about missing swift samples, so real model replacement should wait for a larger manual or policy dataset with full variant coverage.

## 2026-05-24 - Make ore the main reward target

- Changed: updated scoring rules in `settings.py` and `game_core.py`; split HUD/game-over/help copy into ore score and dodge count; changed evaluation/comparison/model-report score breakdown keys to `survival`, `ore_bonus`, `combo_bonus`, and `risk_bonus`; adjusted reward weighting in `train_model.py`; separated local high score keys in `game.py` and `play_with_model.py`; refreshed README and tests.
- Why: dodging ordinary rocks should feel like surviving long enough to collect better ore opportunities, not like the main scoring objective itself.
- Behavior: normal/heavy/swift dodges now build `Dodges` and combo without directly increasing ore score; avoiding ore gives +5 ore score; close-dodging ore adds `RISK +2`; combo bonuses apply when an ore is successfully avoided; life recovery milestones now use dodge count; comparison tables show average dodges, ore bonus, and risk bonus.
- Verification: ran `python3 -m unittest test_game.py test_play_with_model.py test_game_core.py`; ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py game_core.py settings.py compare_models.py evaluate_model.py model_report.py train_model.py test_game.py test_play_with_model.py test_game_core.py`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-ore-score-release-check.json`; ran `python3 model_report.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-ore-score-model-report.json`; ran `python3 compare_models.py game_model.pkl --include-rule-baseline --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --variant-profile variant-rich --report /private/tmp/rockfall-ore-score-comparison.json`; ran `python3 -m json.tool /private/tmp/rockfall-ore-score-release-check.json`; ran `python3 -m json.tool /private/tmp/rockfall-ore-score-model-report.json`; ran `python3 -m json.tool /private/tmp/rockfall-ore-score-comparison.json`; ran `git diff --check`.
- Risks/Notes: the tracked `game_model.pkl` still runs through compatibility adapters, but it was trained before ore became the explicit main reward; collect fresh variant-rich data and retrain before judging model quality under the new objective. The local `game_data.json` has user play samples from the latest manual test and is intentionally not part of this code commit.

## 2026-05-24 - Release v0.8.0

- Changed: updated `settings.py` and `README.md` from `0.8.0-candidate` to `0.8.0`; added `RELEASE_NOTES.md`.
- Why: the requested v0.8 line now has the gameplay, UI, model visibility, training, evaluation, reporting, and release-check pieces needed for a complete local release.
- Behavior: window captions and release-check output identify the project as `0.8.0`, and README links to the v0.8 release summary.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile collect_policy_data.py compare_models.py data_quality.py data_store.py difficulty.py evaluate_model.py features.py game.py game_audio.py game_core.py game_events.py inspect_data.py model_report.py play_with_model.py policies.py release_check.py run_model_experiment.py scores.py settings.py spawning.py train_model.py test_collect_policy_data.py test_compare_models.py test_data_quality.py test_data_store.py test_difficulty.py test_evaluate_model.py test_features.py test_game.py test_game_audio.py test_game_core.py test_inspect_data.py test_model_report.py test_play_with_model.py test_policies.py test_release_check.py test_run_model_experiment.py test_scores.py test_spawning.py test_train_model.py`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-v080-release-check.json`; ran `python3 model_report.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-v080-model-report.json`; ran `python3 compare_models.py game_model.pkl --include-rule-baseline --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --variant-profile variant-rich --report /private/tmp/rockfall-v080-comparison.json`; ran `python3 -m json.tool /private/tmp/rockfall-v080-release-check.json`; ran `python3 -m json.tool /private/tmp/rockfall-v080-model-report.json`; ran `python3 -m json.tool /private/tmp/rockfall-v080-comparison.json`; opened a short pygame window smoke and saved `/private/tmp/rockfall-v080-window-smoke.png`; opened a variant render smoke and saved `/private/tmp/rockfall-v080-variant-window-smoke.png`; ran `git diff --check`.
- Risks/Notes: the tracked legacy model still works, but fresh variant-rich data should be collected before training a model expected to exploit ore/heavy/swift behavior.

## 2026-05-24 - Mark v0.8 release candidate

- Changed: updated `settings.py` and `README.md` from `0.8.0-dev` to `0.8.0-candidate`.
- Why: the v0.8 development line now has gameplay variants, model visibility, reward-aware evaluation/training tools, policy data collection, and release-report coverage.
- Behavior: window captions and release-check output now identify the build as `0.8.0-candidate`.
- Verification: ran `python3 -m unittest`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-v08-candidate-release-check.json`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile settings.py release_check.py`; ran `python3 model_report.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-v08-candidate-model-report.json`; ran `python3 -m json.tool /private/tmp/rockfall-v08-candidate-release-check.json`; ran `python3 -m json.tool /private/tmp/rockfall-v08-candidate-model-report.json`; ran `git diff --check`.
- Risks/Notes: this is still a candidate marker; final `0.8.0` should wait for a real-window playtest and any hand-feel tweaks from that session.

## 2026-05-24 - Show reward columns in model comparison

- Changed: added average variant-bonus and risk-bonus columns to `compare_models.py` text tables; expanded comparison tests and README notes.
- Why: reward-aware behavior should be visible in normal terminal comparison output, not only in JSON reports or model-learning reports.
- Behavior: comparison tables now include `Var Bonus` and `Risk Bonus` averages for each model or policy.
- Verification: ran `python3 -m unittest test_compare_models.py`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile compare_models.py test_compare_models.py`; ran `python3 compare_models.py game_model.pkl --include-rule-baseline --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --variant-profile variant-rich --report /private/tmp/rockfall-reward-columns-comparison.json`; ran `python3 -m json.tool /private/tmp/rockfall-reward-columns-comparison.json`; ran `python3 -m unittest`; ran `git diff --check`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-reward-columns-release-check.json`; ran `python3 -m json.tool /private/tmp/rockfall-reward-columns-release-check.json`.
- Risks/Notes: old summaries without score breakdowns display `0.00`, preserving compatibility with pure summary fixtures.

## 2026-05-24 - Add safe-rule policy data collection

- Changed: added `collect_policy_data.py`, policy sample collection/report helpers, tests, and README usage.
- Why: the project needs a quick way to generate variant-rich supervised examples without waiting for a long manual play session, while keeping synthetic policy data separate from human play data.
- Behavior: `python3 collect_policy_data.py` records built-in safe-rule actions to `runs/policy_variant_rich.json` by default, summarizes the collected run, inspects variant coverage, and can save a JSON report.
- Verification: ran `python3 -m unittest test_collect_policy_data.py`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile collect_policy_data.py test_collect_policy_data.py`; ran `python3 collect_policy_data.py --data /private/tmp/rockfall-policy-samples.json --games 1 --max-frames 120 --difficulty normal --player-speed 8 --lives 3 --variant-profile variant-rich --report /private/tmp/rockfall-policy-collection-report.json`; ran `python3 collect_policy_data.py --data /private/tmp/rockfall-policy-samples-300.json --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --variant-profile variant-rich --report /private/tmp/rockfall-policy-collection-report-300.json`; ran `python3 -m json.tool /private/tmp/rockfall-policy-collection-report-300.json`; ran `python3 -m unittest test_collect_policy_data.py test_model_report.py test_run_model_experiment.py test_train_model.py`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile collect_policy_data.py test_collect_policy_data.py`; ran `python3 -m unittest`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-policy-data-release-check.json`; ran `python3 -m json.tool /private/tmp/rockfall-policy-data-release-check.json`; ran `git diff --check`.
- Risks/Notes: policy-generated samples are demonstrations from a deterministic baseline, not human skill; use them as an experiment source and compare against human-play models rather than mixing them blindly.

## 2026-05-24 - Add model learning report command

- Changed: added `model_report.py`, report formatting/writing helpers, recommendation rules, tests, and README usage.
- Why: the machine-learning loop needs one command that explains data quality, model-vs-baseline behavior, variant-rich stress performance, and reward capture without manually stitching together several tools.
- Behavior: `python3 model_report.py` evaluates the model on selected variant profiles, compares against `policy:safe-rule` by default, includes data-quality and variant-coverage context, and can save JSON reports.
- Verification: ran `python3 -m unittest test_model_report.py`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile model_report.py test_model_report.py`; ran `python3 model_report.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-model-learning-report.json`; ran `python3 -m unittest test_model_report.py test_compare_models.py test_evaluate_model.py test_data_quality.py`; ran `python3 -m json.tool /private/tmp/rockfall-model-learning-report.json`; ran `python3 -m unittest`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-model-report-release-check.json`; ran `python3 -m json.tool /private/tmp/rockfall-model-report-release-check.json`; ran `git diff --check`.
- Risks/Notes: the default report runs multiple headless evaluations, so larger `--games` and `--max-frames` values take longer than a single `evaluate_model.py` run.

## 2026-05-24 - Add reward-aware training weights

- Changed: added `train_model.py --reward-weighting score`, reward sample-weight helpers, candidate-experiment support, tests, and README guidance.
- Why: rare ore/heavy reward states should be able to influence retraining more strongly once fresh variant-rich data exists.
- Behavior: default training remains unweighted; `--reward-weighting score` increases sample weights for reward-bearing rocks and close ore opportunities, and reports min/max/average weights in training and experiment output.
- Verification: ran `python3 -m unittest test_train_model.py test_run_model_experiment.py`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile train_model.py run_model_experiment.py test_train_model.py test_run_model_experiment.py`; ran `python3 train_model.py --data game_data.json --model /private/tmp/rockfall-reward-weighted-model.pkl --estimators 20 --reward-weighting score`; ran `python3 run_model_experiment.py --help`; ran `python3 -m unittest`; ran `python3 train_model.py --help`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-reward-weighting-release-check.json`; ran `python3 run_model_experiment.py --data game_data.json --candidate /private/tmp/rockfall-reward-weighted-candidate.pkl --estimators 20 --reward-weighting score --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --variant-profile variant-rich --report /private/tmp/rockfall-reward-weighting-experiment.json`; ran `python3 -m json.tool /private/tmp/rockfall-reward-weighting-release-check.json`; ran `python3 -m json.tool /private/tmp/rockfall-reward-weighting-experiment.json`; ran `git diff --check`.
- Risks/Notes: existing tracked data predates rock variants, so reward weighting currently reports all weights as `1.00`; collect variant-rich data before expecting this to change model behavior.

## 2026-05-24 - Add variant-rich spawn profile

- Changed: added `standard` and `variant-rich` rock spawn profiles, threaded `--variant-profile` through manual play, model play, evaluation, comparison, experiments, and release checks, expanded entrypoint/core tests, and updated `README.md`.
- Why: training data needs enough heavy, swift, and ore examples for the model to learn variant-specific decisions without requiring very long manual collection sessions.
- Behavior: default runs keep the existing `standard` distribution; `--variant-profile variant-rich` increases non-normal rocks and records the profile in text/JSON evaluation and comparison outputs.
- Verification: ran `python3 -m unittest test_game.py test_play_with_model.py test_game_core.py test_evaluate_model.py test_compare_models.py test_run_model_experiment.py test_release_check.py`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile settings.py game_core.py game.py play_with_model.py evaluate_model.py compare_models.py run_model_experiment.py release_check.py test_game.py test_play_with_model.py test_game_core.py test_evaluate_model.py test_compare_models.py test_run_model_experiment.py test_release_check.py`; ran `python3 evaluate_model.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --variant-profile variant-rich --report /private/tmp/rockfall-variant-rich-eval.json`; ran `python3 -m unittest`; ran `python3 -m json.tool /private/tmp/rockfall-variant-rich-eval.json`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --variant-profile variant-rich --report /private/tmp/rockfall-variant-rich-release-check.json`; ran `python3 -m json.tool /private/tmp/rockfall-variant-rich-release-check.json`; ran `git diff --check`.
- Risks/Notes: variant-rich runs are intentionally not directly comparable to standard-profile score baselines unless the report's `variant_profile` matches.

## 2026-05-24 - Add evaluation score-source breakdowns

- Changed: added score-source tracking to `RockfallGame`, included score breakdown payloads in headless evaluation summaries, expanded evaluation and gameplay tests, and updated `README.md`.
- Why: model improvements should be explainable by source, especially now that ore and close-dodge risk rewards can affect score separately from survival.
- Behavior: evaluation text and JSON reports can show total and per-game average base dodge points, combo bonuses, variant bonuses, and risk bonuses.
- Verification: ran `python3 -m unittest test_game_core.py test_evaluate_model.py`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game_core.py evaluate_model.py test_game_core.py test_evaluate_model.py`; ran `python3 -m unittest test_game_core.py test_evaluate_model.py test_compare_models.py test_release_check.py`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game_core.py evaluate_model.py compare_models.py release_check.py test_game_core.py test_evaluate_model.py test_compare_models.py test_release_check.py`; ran `python3 -m unittest`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-score-breakdown-release-check.json`; ran `python3 -m json.tool /private/tmp/rockfall-score-breakdown-release-check.json`; ran `git diff --check`.
- Risks/Notes: old saved report files will not have `score_breakdown`; new reports include it automatically, including release-check artifacts.

## 2026-05-24 - Add ore close-dodge risk bonus

- Changed: added `near_miss_bonus` to rock variant settings, updated ore scoring in `game_core.py`, refreshed the help legend and README gameplay notes, and expanded gameplay tests.
- Why: ore should feel meaningfully different from a normal rock by offering a tempting risk/reward choice instead of only being a flat score bonus.
- Behavior: avoiding ore still awards +2 score, while close-dodging ore adds one more point and shows `RISK +1` alongside `CLOSE!`; normal close dodges remain feedback-only.
- Verification: ran `python3 -m unittest test_game_core.py`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile settings.py game_core.py test_game_core.py`; ran `python3 -m unittest`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-ore-risk-release-check.json`; ran `python3 -m json.tool /private/tmp/rockfall-ore-risk-release-check.json`; ran `git diff --check`.
- Risks/Notes: scoring baselines can shift after ore-rich fresh data; current tracked training data still predates the newest risk-reward behavior.

## 2026-05-24 - Add model play debug overlay

- Changed: added `play_with_model.py --debug-ai`, model prediction debug helpers, and `RockfallGame.draw_ai_debug_overlay`; expanded model-play and rendering tests; updated `README.md`.
- Why: the machine-learning behavior should be visible in the game window, not only in terminal reports, so players can see what action the model chose and what rock features it is using.
- Behavior: model play can show the predicted direction, adapted/raw feature counts, and nearest rock dx/y/speed/reward values while the run is active.
- Verification: ran `python3 -m unittest test_play_with_model.py test_game_core.py`; rendered pygame preview image to `/private/tmp/rockfall-ai-debug-overlay.png`; ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game_core.py play_with_model.py test_game_core.py test_play_with_model.py`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-ai-debug-release-check.json`; ran `python3 -m json.tool /private/tmp/rockfall-ai-debug-release-check.json`.
- Risks/Notes: the overlay is opt-in and does not change model predictions, gameplay rules, or collected training data.

## 2026-05-24 - Add safe-rule baseline policy comparison

- Changed: added `policies.py` with a deterministic `safe-rule` dodging policy; refactored `evaluate_model.py` so evaluation can run models or built-in policies; added `compare_models.py --include-rule-baseline`; added policy and comparison tests; updated `README.md`.
- Why: model scores need a simple non-ML baseline so future training runs can prove they beat more than random guessing or human imitation artifacts.
- Behavior: `python3 compare_models.py game_model.pkl --include-rule-baseline` compares the trained model against `policy:safe-rule` with the same seeds, settings, survival metrics, and variant outcome JSON.
- Verification: ran `python3 -m unittest test_policies.py test_compare_models.py test_evaluate_model.py`; ran `python3 compare_models.py game_model.pkl --include-rule-baseline --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-rule-baseline-comparison.json`; ran `python3 -m json.tool /private/tmp/rockfall-rule-baseline-comparison.json`; ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile policies.py evaluate_model.py compare_models.py test_policies.py test_evaluate_model.py test_compare_models.py`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-rule-baseline-release-check.json`; ran `python3 -m json.tool /private/tmp/rockfall-rule-baseline-release-check.json`.
- Risks/Notes: `safe-rule` is deliberately simple and deterministic; it is a baseline for comparison, not intended to be the final game AI.

## 2026-05-24 - Add multi-rock features and variant outcome metrics

- Changed: expanded `features.py` from one nearest rock to the nearest three rocks while keeping four-feature and six-feature model compatibility; updated `data_quality.py` to measure variant coverage across the same nearest-three rocks; added per-variant spawned, avoided, hit, and avoid-rate metrics in `game_core.py` and `evaluate_model.py`; expanded feature, gameplay, prediction, training, data-quality, and evaluation tests; updated `README.md`.
- Why: models need more than one rock to learn competing threats, and evaluation needs per-variant outcomes to show whether ore, heavy, and swift rocks are actually handled well.
- Behavior: newly trained models now receive player x-position plus three ranked rock feature groups; evaluation JSON/text summaries include variant outcome counts and avoid rates.
- Verification: ran `python3 -m unittest test_features.py test_game_core.py test_play_with_model.py test_train_model.py`; ran `python3 -m unittest test_evaluate_model.py test_game_core.py test_features.py test_play_with_model.py test_train_model.py`; ran `python3 -m unittest test_data_quality.py test_features.py test_game_core.py test_evaluate_model.py test_play_with_model.py test_train_model.py`; ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile features.py data_quality.py game_core.py evaluate_model.py play_with_model.py train_model.py test_features.py test_data_quality.py test_game_core.py test_evaluate_model.py test_play_with_model.py test_train_model.py`; ran `python3 inspect_data.py --data game_data.json`; ran `python3 train_model.py --data game_data.json --model /private/tmp/rockfall-multirock-model.pkl --estimators 20`; ran `python3 evaluate_model.py --model /private/tmp/rockfall-multirock-model.pkl --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --json`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-multirock-release-check.json`; ran `python3 -m json.tool /private/tmp/rockfall-multirock-release-check.json`.
- Risks/Notes: old `game_model.pkl` and six-feature candidate models still run through feature adaptation, but newly trained 16-feature models should be compared only against reports that record this feature version.

## 2026-05-23 - Report rock variant coverage in data tools

- Changed: added rock-variant coverage summaries to `data_quality.py`, `inspect_data.py`, `train_model.py`, and `run_model_experiment.py`; expanded data inspection, training, and experiment tests; updated `README.md`.
- Why: after adding variant-aware features, old datasets can still train successfully while containing no recorded ore, heavy, or swift rocks, so the tools need to make that gap visible before model iteration.
- Behavior: inspection, training, and experiment output now reports recorded variant samples, legacy samples, per-variant counts, and warnings such as `no_recorded_variant_samples`.
- Verification: ran `python3 -m unittest test_data_quality.py test_inspect_data.py test_train_model.py test_run_model_experiment.py`; ran `python3 inspect_data.py --data game_data.json`; ran `python3 train_model.py --data game_data.json --model /private/tmp/rockfall-coverage-model.pkl --estimators 20`; ran `python3 run_model_experiment.py --data game_data.json --candidate /private/tmp/rockfall-coverage-candidate.pkl --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-coverage-experiment.json`; ran `python3 -m json.tool /private/tmp/rockfall-coverage-experiment.json`; ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile data_quality.py inspect_data.py train_model.py run_model_experiment.py test_data_quality.py test_inspect_data.py test_train_model.py test_run_model_experiment.py`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-variant-coverage-release-check.json`; ran `python3 -m json.tool /private/tmp/rockfall-variant-coverage-release-check.json`.
- Risks/Notes: this does not change gameplay, model predictions, or existing data; it only makes dataset coverage visible.

## 2026-05-23 - Add rock variant features for model training

- Changed: updated `features.py` so model inputs include the nearest rock's fall-speed modifier and score bonus; updated `game_core.py` snapshots to record rock type; added old-model feature adaptation in `play_with_model.py`; expanded feature, gameplay, prediction, and training tests; updated `README.md`.
- Why: ore already awards +2 score in gameplay, but the machine-learning model could only see obstacle positions, so it could not distinguish ore, heavy, swift, or normal rocks in newly collected samples.
- Behavior: new training data includes obstacle variants, newly trained models use six features, and old four-feature models still run by receiving the legacy position-only feature subset.
- Verification: ran `python3 -m unittest test_features.py test_game_core.py test_play_with_model.py test_train_model.py`; ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile features.py game_core.py play_with_model.py train_model.py test_features.py test_game_core.py test_play_with_model.py test_train_model.py`; ran `python3 inspect_data.py --data game_data.json`; ran `python3 train_model.py --data game_data.json --model /private/tmp/rockfall-variant-features-model.pkl --estimators 20`; ran `python3 evaluate_model.py --model /private/tmp/rockfall-variant-features-model.pkl --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --json`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-variant-features-release-check.json`; ran `python3 -m json.tool /private/tmp/rockfall-variant-features-release-check.json`.
- Risks/Notes: existing `game_data.json` entries do not contain variants, so they default to normal for feature extraction; collect fresh data before expecting a retrained model to learn variant-specific behavior.

## 2026-05-23 - Add rock variant legend to help screen

- Changed: added a four-card rock variant legend to the `HOW IT WORKS` screen in `game_core.py`; added a small font for compact card labels; expanded rendering tests; updated `README.md`.
- Why: variant rocks are easier to understand when players can see each shape and effect in-game instead of relying on external documentation.
- Behavior: the help screen now shows Stone, Heavy, Swift, and Ore cards with their visuals and effects while preserving the machine-learning explanation.
- Verification: ran `python3 -m unittest test_game_core.py`; rendered pygame preview image to `/private/tmp/rockfall-help-rock-legend.png`; ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game_core.py test_game_core.py`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-help-legend-release-check.json`; ran `python3 -m json.tool /private/tmp/rockfall-help-legend-release-check.json`.
- Risks/Notes: this is a tutorial/UI change only; gameplay rules, data format, and model behavior are unchanged.

## 2026-05-23 - Add latest GUI smoke-test gameplay samples

- Changed: updated `game_data.json` with 412 new manual-play samples collected while opening the current GUI build for smoke testing.
- Why: real-window checks continue to produce useful left/right examples, and tracked data changes should be searchable separately from gameplay code changes.
- Behavior: the dataset now has 3,314 valid samples and 3 skipped entries; action balance remains close, with left=1,656 and right=1,658.
- Verification: ran `python3 inspect_data.py --data game_data.json`.
- Risks/Notes: this is data-only and was collected before the rock-variant gameplay change, so it does not include variant-specific player behavior.

## 2026-05-23 - Add rock variants with distinct effects

- Changed: added normal, heavy, swift, and ore obstacle variants in `settings.py` and `game_core.py`; gave variants different colors, markings, fall-speed modifiers, and score bonuses; added a help-screen line for variant effects; expanded core gameplay/rendering tests; updated `README.md`.
- Why: Rockfall's obstacles now read as rocks, so the next step is to make them mechanically interesting instead of all behaving the same.
- Behavior: normal stones keep the baseline behavior, heavy stones fall more slowly and award +1 score when avoided, swift stones fall faster, and ore stones award +2 score when avoided. Training snapshots still record only obstacle x/y positions, keeping existing model-data shape compatible.
- Verification: ran `python3 -m unittest test_game_core.py`; rendered pygame preview image to `/private/tmp/rockfall-rock-variants.png`; ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile settings.py game_core.py test_game_core.py`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-variant-release-check.json`; ran `python3 -m json.tool /private/tmp/rockfall-variant-release-check.json`.
- Risks/Notes: the active model does not receive rock variant labels as features, so variant speed changes may affect model play quality until fresh data is collected and the model is compared again.

## 2026-05-23 - Add rock-art smoke-test gameplay samples

- Changed: updated `game_data.json` with 144 new manual-play samples collected while opening the rock-art build for a smoke test.
- Why: real-window checks can produce useful data samples, and keeping them logged makes dataset changes traceable.
- Behavior: the dataset now has 2,902 valid samples and 3 skipped entries; action balance remains close, with left=1,444 and right=1,458.
- Verification: ran `python3 inspect_data.py --data game_data.json`.
- Risks/Notes: this is data-only; no gameplay rules, model features, or trained model artifact changed.

## 2026-05-23 - Replace warning strip and square player art

- Changed: removed the yellow top-edge incoming-rock warning strip; redrew the player as a small mine cart with a rim, angled body, shaded side, and wheels; expanded rendering tests; updated `README.md`.
- Why: the warning strip read like a confusing yellow line, and the square player shape did not fit the Rockfall theme.
- Behavior: rocks now simply enter from above as partially clipped stones, and the player is visually a cart while collision bounds and controls stay unchanged.
- Verification: ran `python3 -m unittest test_game_core.py`; ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile settings.py game_core.py test_game_core.py`; rendered pygame preview image to `/private/tmp/rockfall-cart-no-warning.png`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-cart-release-check.json`; ran `python3 -m json.tool /private/tmp/rockfall-cart-release-check.json`.
- Risks/Notes: this is visual-only, but the removed warning strip reduces early lane telegraphing slightly; playtesting should confirm the rock entry timing still feels readable.

## 2026-05-23 - Draw falling rocks as irregular stones

- Changed: replaced rectangular obstacle rendering with irregular rock polygons, offset shadows, warm stone colors, highlight facets, dark facets, and crack lines; expanded rendering tests; updated `README.md`.
- Why: the game is called Rockfall, but the old obstacles still read as colored blocks rather than falling rocks.
- Behavior: obstacle collision boxes and model features are unchanged; only the visual rendering now looks like faceted stones.
- Verification: ran `python3 -m unittest test_game_core.py`; ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile settings.py game_core.py test_game_core.py`; rendered pygame preview image to `/private/tmp/rockfall-rock-obstacles.png`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-rock-release-check.json`; ran `python3 -m json.tool /private/tmp/rockfall-rock-release-check.json`.
- Risks/Notes: tests now sample specific rock facet pixels, so future art tweaks should update those samples intentionally.

## 2026-05-21 - Add model-to-training launcher

- Changed: added a `TRAIN MANUALLY` button and T hotkey to the model-play start screen; launches `game.py` with the current difficulty, player speed, lives, and mute settings; added command/rendering tests; updated `README.md`.
- Why: when the model performs poorly, players need a visible path back to manual data collection instead of quitting to the terminal.
- Behavior: from model play, `TRAIN MANUALLY` exits the model window and opens data-collection mode with the same tuning settings.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game_core.py play_with_model.py test_game_core.py test_play_with_model.py`; rendered pygame preview image to `/private/tmp/rockfall-train-manually-start.png`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-training-launcher-release-check.json`; ran `python3 -m json.tool /private/tmp/rockfall-training-launcher-release-check.json`.
- Risks/Notes: like the model launcher, this starts a separate Python process and exits the current pygame window.

## 2026-05-21 - Add start-screen model play launcher

- Changed: added a `PLAY WITH MODEL` start-screen button and M hotkey in manual play; added a missing-model prompt that points players to `train_model.py`; launches `play_with_model.py` with the current difficulty, player speed, lives, and mute settings when `game_model.pkl` exists; hides the launcher on the model-play start screen; expanded rendering and command tests; updated `README.md`.
- Why: the machine-learning path should be visible from the GUI, and players should get a clear explanation when the model has not been trained yet.
- Behavior: from manual mode, clicking `PLAY WITH MODEL` switches to the model-controlled script if a model file is available; otherwise it opens an in-game `MODEL NOT READY` screen with next steps.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game_core.py game.py play_with_model.py test_game_core.py test_game.py`; rendered pygame preview images to `/private/tmp/rockfall-model-launch-start.png`, `/private/tmp/rockfall-model-missing.png`, and `/private/tmp/rockfall-model-start.png`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-model-launch-release-check.json`; ran `python3 -m json.tool /private/tmp/rockfall-model-launch-release-check.json`.
- Risks/Notes: launching model play starts a separate Python process and exits the manual window; this keeps manual data collection and model play logic separated.

## 2026-05-21 - Add GUI smoke-test gameplay samples

- Changed: updated `game_data.json` with 289 new manual-play samples collected while opening the polished GUI for a smoke test.
- Why: the manual data collection path should keep useful real-window samples, especially after checking the start screen and first-run flow.
- Behavior: the dataset now has 2,758 valid samples and 3 skipped entries; action balance remains close, with left=1,375 and right=1,383.
- Verification: ran `python3 inspect_data.py --data game_data.json`.
- Risks/Notes: this is data-only; no gameplay rules, model features, or trained model artifact changed.

## 2026-05-21 - Add start-screen machine learning help

- Changed: added a `HOW IT WORKS` start-screen button, a help screen explaining gameplay and the machine-learning loop, mouse/keyboard navigation for help in manual and model play, rendering tests, and README documentation.
- Why: the project is called a machine-learning game, but the running GUI did not explain how manual samples, training, model play, and evaluation connect.
- Behavior: players can click `HOW IT WORKS` or press H from the start screen; the help page explains manual data collection, `train_model.py`, `game_model.pkl`, model prediction, and inspection/evaluation scripts; Back/Start buttons or B/Esc/Space navigate from help.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game_core.py game.py play_with_model.py test_game_core.py`; rendered pygame preview images to `/private/tmp/rockfall-help-start.png` and `/private/tmp/rockfall-help-screen.png`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-help-release-check.json`; ran `python3 -m json.tool /private/tmp/rockfall-help-release-check.json`.
- Risks/Notes: the help screen is informational and does not change gameplay rules or model features.

## 2026-05-21 - Polish game HUD and menu styling

- Changed: updated the pygame color theme, added panel-backed HUD sections, panel-backed menu text, prompt button backgrounds, subtle background guide lines, and softer obstacle/progress colors; expanded rendering tests; updated `README.md`.
- Why: the old pure-rectangle UI looked too raw for the current gameplay loop, and v0.8 needs a cleaner first impression.
- Behavior: gameplay now has framed stats/progress panels, while start/pause/game-over screens present their text inside a centered panel with highlighted prompts.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile settings.py game_core.py test_game_core.py`; rendered pygame preview images to `/private/tmp/rockfall-ui-gameplay.png` and `/private/tmp/rockfall-ui-start.png`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-ui-release-check.json`; ran `python3 -m json.tool /private/tmp/rockfall-ui-release-check.json`.
- Risks/Notes: this is still asset-free pygame drawing; a live window playtest should check spacing on the actual display.

## 2026-05-17 - Advance to v0.8 development

- Changed: updated `settings.py` to `0.8.0-dev`; refreshed `README.md` project status to call out release-check JSON artifacts.
- Why: the project has reached the requested v0.8 development line after runtime tuning, report quality, data inspection, gameplay recovery, and release-report work.
- Behavior: window captions and release-check output now identify the build as `0.8.0-dev`.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile settings.py release_check.py`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-v08-release-check.json`; ran `python3 -m json.tool /private/tmp/rockfall-v08-release-check.json`.
- Risks/Notes: this is a development marker, not a release tag; a full hands-on playtest should precede any final `v0.8.0` tag.

## 2026-05-17 - Save release check reports

- Changed: added `--report` to `release_check.py`; added a structured release payload with version, unit-test pass status, evaluation settings, and evaluation summary; expanded release-check tests; updated `README.md`.
- Why: v0.8 release prep needs a durable artifact that proves which build, settings, and checks were used.
- Behavior: `python3 release_check.py --report runs/release_check.json` saves a JSON report after a passing check; if unit tests fail, the report still records the version and failed unit-test status.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile release_check.py test_release_check.py`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-release-check.json`; ran `python3 -m json.tool /private/tmp/rockfall-release-check.json`.
- Risks/Notes: the report reuses evaluation summary payloads, so new evaluation metrics will automatically appear in future release reports.

## 2026-05-17 - Advance to v0.7 development

- Changed: updated `settings.py` to `0.7.0-dev`; refreshed `README.md` project status to call out score milestone life recovery.
- Why: the project has moved from v0.6 data workflow into v0.7 gameplay improvements.
- Behavior: window captions and release-check output now identify the build as `0.7.0-dev`.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile settings.py release_check.py`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3`.
- Risks/Notes: this is a development marker, not a release tag.

## 2026-05-17 - Add score milestone life recovery

- Changed: added life-restore score milestones in `settings.py` and `game_core.py`; reset milestone state per run; added floating `LIFE +1` feedback; expanded gameplay tests; updated `README.md`.
- Why: v0.7 gameplay should create longer-run comeback moments without adding new controls or changing the training-data action space.
- Behavior: every 50 score, the game restores one lost life up to the run's starting lives; full-life runs advance the milestone without banking extra lives.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile settings.py game_core.py test_game_core.py`; ran `python3 evaluate_model.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3`.
- Risks/Notes: long-run score and survival baselines may improve for damaged runs, so model comparisons after this commit should not be mixed with older gameplay-rule baselines.

## 2026-05-17 - Advance to v0.6 development

- Changed: updated `settings.py` to `0.6.0-dev`; refreshed `README.md` project status to call out data inspection and quality reports.
- Why: the project has moved from v0.5 evaluation/reporting improvements into v0.6 data collection and training workflow.
- Behavior: window captions and release-check output now identify the build as `0.6.0-dev`.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile settings.py release_check.py`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3`.
- Risks/Notes: this is a development marker, not a release tag.

## 2026-05-17 - Add standalone data inspection

- Changed: added `data_quality.py` for shared data-quality thresholds and summaries; added `inspect_data.py` with text, JSON, and `--report` output; updated `run_model_experiment.py` to reuse the shared quality helpers; added tests for data inspection and report writing; updated `README.md`.
- Why: v0.6 data collection should have a quick pre-training check so weak datasets can be spotted before spending time on training and model comparison.
- Behavior: `python3 inspect_data.py --data game_data.json` reports valid samples, skipped entries, feature names, action balance, skipped ratio, balance ratio, and quality warnings.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile data_quality.py inspect_data.py run_model_experiment.py test_data_quality.py test_inspect_data.py test_run_model_experiment.py`; ran `python3 inspect_data.py --data game_data.json`; ran `python3 inspect_data.py --data game_data.json --report /private/tmp/rockfall-data-report.json --json`; ran `python3 -m json.tool /private/tmp/rockfall-data-report.json`; ran `python3 run_model_experiment.py --data game_data.json --candidate /private/tmp/rockfall-inspect-candidate.pkl --report /private/tmp/rockfall-inspect-experiment.json --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3`; ran `python3 -m json.tool /private/tmp/rockfall-inspect-experiment.json`.
- Risks/Notes: inspection uses the same feature extraction path as training, so changes to model features will affect both the inspector and trainer together.

## 2026-05-17 - Advance to v0.5 development

- Changed: updated `settings.py` to `0.5.0-dev`; refreshed `README.md` project status to call out survival metrics and JSON report artifacts.
- Why: the project has moved from v0.4 runtime tuning into v0.5 evaluation/reporting quality.
- Behavior: window captions and release-check output now identify the build as `0.5.0-dev`.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile settings.py release_check.py`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3`.
- Risks/Notes: this is a development marker, not a release tag.

## 2026-05-17 - Save evaluation and comparison reports

- Changed: added `--report` to `evaluate_model.py` and `compare_models.py`; added shared JSON report writing with parent-directory creation; expanded parser/report tests; updated `README.md`.
- Why: v0.5 tuning work needs durable evaluation artifacts without manually copying terminal output.
- Behavior: `evaluate_model.py --report runs/eval.json` and `compare_models.py --report runs/comparison.json` save the same structured payloads used by `--json`; text mode prints the report path after the summary.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile evaluate_model.py compare_models.py test_evaluate_model.py test_compare_models.py`; ran `python3 evaluate_model.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3 --report /private/tmp/rockfall-eval-report.json`; ran `python3 compare_models.py game_model.pkl --games 1 --max-frames 300 --difficulty hard --player-speed 8 --lives 3 --report /private/tmp/rockfall-comparison-report.json --json`; ran `python3 -m json.tool /private/tmp/rockfall-eval-report.json`; ran `python3 -m json.tool /private/tmp/rockfall-comparison-report.json`.
- Risks/Notes: `--json` output remains pure JSON even when `--report` is also supplied.

## 2026-05-17 - Add survival metrics to evaluation reports

- Changed: updated `evaluate_model.py` summaries with average remaining lives, best remaining lives, and survival rate; added those fields to text/JSON output and comparison tables; updated model-comparison tie-breaking to consider survival and remaining lives; expanded tests; updated `README.md`.
- Why: v0.5 reports should explain whether a model is barely surviving, comfortably surviving, or repeatedly reaching game over, not just its score.
- Behavior: `evaluate_model.py`, `compare_models.py`, `run_model_experiment.py`, and `release_check.py` now surface survival/lives metrics through their shared summary formatting.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile evaluate_model.py compare_models.py run_model_experiment.py release_check.py test_evaluate_model.py test_compare_models.py test_run_model_experiment.py`; ran `python3 evaluate_model.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3`; ran `python3 compare_models.py game_model.pkl --games 1 --max-frames 300 --difficulty hard --player-speed 8 --lives 3 --json`; ran `python3 compare_models.py game_model.pkl --games 1 --max-frames 300 --difficulty hard --player-speed 8 --lives 3`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3`.
- Risks/Notes: comparison winner rules changed only for ties after average score and combo; existing score-led comparisons remain stable.

## 2026-05-17 - Advance to v0.4 development

- Changed: updated `settings.py` to `0.4.0-dev`; refreshed `README.md` project status to call out runtime hand-feel tuning for difficulty, player speed, and initial lives.
- Why: the project has moved past the v0.3 experiment-safety foundation into v0.4 tuning work.
- Behavior: window captions and release-check output now identify the build as `0.4.0-dev`.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile settings.py game.py play_with_model.py release_check.py test_release_check.py`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3`.
- Risks/Notes: this is a development marker, not a release tag.

## 2026-05-17 - Add runtime initial lives tuning

- Changed: updated `game_core.py` to reset from configurable initial lives; wired `--lives` through manual play, AI play, evaluation, comparison, experiments, and release checks; included `initial_lives` in JSON reports; expanded tests across affected entrypoints; updated `README.md`.
- Why: v0.4 hand-feel tuning needs lives to be adjustable alongside difficulty and player speed without editing source constants.
- Behavior: commands can now use values like `--lives 3`; invalid non-positive values fail before running evaluation or experiments.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game_core.py game.py play_with_model.py evaluate_model.py compare_models.py run_model_experiment.py release_check.py test_game_core.py test_game.py test_play_with_model.py test_evaluate_model.py test_compare_models.py test_run_model_experiment.py test_release_check.py`; ran `python3 evaluate_model.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3`; ran `python3 compare_models.py game_model.pkl --games 1 --max-frames 300 --difficulty hard --player-speed 8 --lives 3 --json`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8 --lives 3`.
- Risks/Notes: score and survival baselines are sensitive to the initial lives setting, so comparisons should record and match it.

## 2026-05-17 - Add runtime player speed tuning

- Changed: updated `game_core.py` to use a configurable player speed; wired `--player-speed` through manual play, AI play, evaluation, comparison, experiments, and release checks; expanded tests across affected entrypoints; updated `README.md`.
- Why: v0.4 hand-feel tuning needs movement speed as a runtime parameter, not just a source constant.
- Behavior: commands can now use values like `--player-speed 8`; invalid non-positive values fail before running evaluation or experiments.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game_core.py game.py play_with_model.py evaluate_model.py compare_models.py run_model_experiment.py release_check.py test_game_core.py test_game.py test_play_with_model.py test_evaluate_model.py test_compare_models.py test_run_model_experiment.py test_release_check.py`; ran `python3 evaluate_model.py --games 1 --max-frames 300 --difficulty normal --player-speed 8`; ran `python3 compare_models.py game_model.pkl --games 1 --max-frames 300 --difficulty hard --player-speed 8 --json`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal --player-speed 8`.
- Risks/Notes: model performance can change with player speed, so comparisons should record and match this setting.

## 2026-05-17 - Add difficulty presets

- Changed: added `easy`, `normal`, and `hard` difficulty presets in `difficulty.py`; wired `--difficulty` through manual play, AI play, evaluation, comparison, experiments, and release checks; expanded tests across the affected entrypoints; updated `README.md`.
- Why: v0.4 hand-feel tuning needs runtime difficulty selection instead of changing constants in source code.
- Behavior: `--difficulty hard` increases pressure with faster rocks and tighter spawn frequency, while `--difficulty easy` reduces pressure.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile difficulty.py game_core.py game.py play_with_model.py evaluate_model.py compare_models.py run_model_experiment.py release_check.py test_difficulty.py test_game_core.py test_game.py test_play_with_model.py test_evaluate_model.py test_compare_models.py test_run_model_experiment.py test_release_check.py`; ran `python3 evaluate_model.py --games 1 --max-frames 300 --difficulty hard`; ran `python3 compare_models.py game_model.pkl --games 1 --max-frames 300 --difficulty easy --json`; ran `python3 release_check.py --games 1 --max-frames 300 --difficulty normal`.
- Risks/Notes: trained models are still tied to the data distribution they saw; comparing models across difficulty presets should be done explicitly.

## 2026-05-17 - Advance to v0.3 development

- Changed: updated `settings.py` version to `0.3.0-dev`; updated `README.md` project status and feature summary.
- Why: the model experiment workflow now includes comparison, reports, safety checks, and data-quality warnings, which completes the planned v0.3 foundation.
- Behavior: window titles and release checks now identify local builds as `0.3.0-dev`.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile settings.py release_check.py`; ran `python3 release_check.py --games 1 --max-frames 300`.
- Risks/Notes: this is a development version, not a release tag.

## 2026-05-17 - Add experiment data quality checks

- Changed: updated `run_model_experiment.py` with data-quality thresholds for valid sample count, action balance, and skipped-entry ratio; expanded `test_run_model_experiment.py`; updated `README.md`.
- Why: experiments should flag weak datasets before a high validation score creates false confidence.
- Behavior: experiment text and JSON reports now include `data_quality` status and warnings such as `valid_samples_below_500`.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile run_model_experiment.py test_run_model_experiment.py`; ran `python3 run_model_experiment.py --data runs/playtest_manual.json --candidate /private/tmp/rockfall-quality-model.pkl --games 1 --max-frames 300 --report /private/tmp/rockfall-quality-report.json`; ran `python3 -m json.tool /private/tmp/rockfall-quality-report.json`.
- Risks/Notes: quality warnings do not block training yet; they are decision support for v0.3 model iteration.

## 2026-05-17 - Run manual playtest experiment

- Changed: launched `python3 game.py --data runs/playtest_manual.json --mute`, completed a short real-window manual playtest, and generated 51 ignored local samples in `runs/playtest_manual.json`; trained a temporary candidate model at `/private/tmp/rockfall-playtest-model.pkl`; wrote a temporary report at `/private/tmp/rockfall-playtest-report.json`.
- Why: the v0.2 experiment workflow needed a real smoke test using data collected from the current playable build.
- Behavior: no tracked gameplay behavior changed. The short playtest dataset trained successfully but underperformed the baseline in a one-game smoke comparison: baseline average score 6.00, candidate average score 4.00, candidate result `candidate_underperformed_baseline`.
- Verification: ran `python3 run_model_experiment.py --data runs/playtest_manual.json --candidate /private/tmp/rockfall-playtest-model.pkl --report /private/tmp/rockfall-playtest-report.json --games 1 --max-frames 300`.
- Risks/Notes: 51 samples is far too small for a real replacement model; keep the default `game_model.pkl` until a larger playtest dataset beats the baseline.

## 2026-05-17 - Show run summary on pause

- Changed: updated `game_core.py` pause-screen lines to include current score, best score, level, lives, and combo; expanded `test_game_core.py`; updated `README.md`.
- Why: real-window playtesting showed the pause screen looked clean but did not expose enough current-run state for mid-run review.
- Behavior: pausing now shows compact run stats above the controls.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game_core.py test_game_core.py`.
- Risks/Notes: pause screen has more text; real-window spacing should be rechecked after future menu typography changes.

## 2026-05-17 - Report missing model paths cleanly

- Changed: updated `compare_models.py` with model path validation and concise CLI errors; updated `run_model_experiment.py` to validate the baseline before training; expanded `test_compare_models.py` and `test_run_model_experiment.py`; updated `README.md`.
- Why: model comparison and experiment commands should fail before expensive work when a model path is wrong.
- Behavior: missing model paths now print `Error: Model file not found: ...` and exit nonzero without a traceback.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile compare_models.py test_compare_models.py run_model_experiment.py test_run_model_experiment.py`; ran `python3 compare_models.py missing.pkl --games 1 --max-frames 300`; ran `python3 run_model_experiment.py --baseline missing.pkl --candidate /private/tmp/rockfall-missing-baseline.pkl --games 1 --max-frames 300`.
- Risks/Notes: this only checks path existence; invalid model contents still fail during load.

## 2026-05-17 - Protect baseline model experiments

- Changed: updated `run_model_experiment.py` to reject matching `--baseline` and `--candidate` paths; expanded `test_run_model_experiment.py`; updated `README.md`.
- Why: a model experiment should never accidentally overwrite the baseline model before comparing it.
- Behavior: passing the same path for baseline and candidate prints a concise error and exits nonzero.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile run_model_experiment.py test_run_model_experiment.py`; ran `python3 run_model_experiment.py --baseline game_model.pkl --candidate game_model.pkl --games 1 --max-frames 300` and confirmed it exits 1 with a concise error.
- Risks/Notes: path comparison uses absolute paths and does not resolve symlinks.

## 2026-05-17 - Add candidate experiment result

- Changed: updated `run_model_experiment.py` to classify the candidate model as outperforming, matching, or underperforming the baseline by average score; expanded `test_run_model_experiment.py`; updated `README.md`.
- Why: experiment output should state the conclusion directly instead of requiring manual interpretation of score deltas.
- Behavior: experiment text output and JSON reports now include a `candidate_result` value.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile run_model_experiment.py test_run_model_experiment.py`; ran `python3 run_model_experiment.py --candidate /private/tmp/rockfall-candidate-result.pkl --games 1 --max-frames 300 --report /private/tmp/rockfall-experiment-result.json`; ran `python3 -m json.tool /private/tmp/rockfall-experiment-result.json`.
- Risks/Notes: this is a conservative score-only conclusion; combo and frame metrics remain visible for human review.

## 2026-05-17 - Save model experiment reports

- Changed: updated `run_model_experiment.py` with a `--report` option that writes the structured experiment payload to JSON; expanded `test_run_model_experiment.py`; updated `README.md`.
- Why: model experiments should leave reproducible reports behind instead of only printing terminal output.
- Behavior: `python3 run_model_experiment.py --report runs/v02_report.json` saves training and comparison metrics while still printing the normal table unless `--json` is also used.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile run_model_experiment.py test_run_model_experiment.py`; ran `python3 run_model_experiment.py --candidate /private/tmp/rockfall-candidate-report.pkl --games 1 --max-frames 300 --report /private/tmp/rockfall-experiment-report.json`; ran `python3 -m json.tool /private/tmp/rockfall-experiment-report.json`.
- Risks/Notes: report files under `runs/` remain ignored by git unless explicitly moved elsewhere.

## 2026-05-17 - Add model comparison deltas

- Changed: updated `compare_models.py` to report score deltas against the first model and identify the best model by average score; updated `run_model_experiment.py` to include the same comparison conclusion; expanded `test_compare_models.py` and `test_run_model_experiment.py`; updated `README.md`.
- Why: model comparison should make candidate wins, ties, and losses obvious without hand-reading every metric.
- Behavior: comparison tables now include a `Score Delta` column and a `Best model by average score` line; JSON payloads include `best_model` and per-model `score_delta`.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile compare_models.py test_compare_models.py run_model_experiment.py test_run_model_experiment.py`; ran `python3 compare_models.py game_model.pkl --games 1 --max-frames 300`; ran `python3 compare_models.py game_model.pkl --games 1 --max-frames 300 --json`; ran `python3 run_model_experiment.py --candidate /private/tmp/rockfall-candidate-delta.pkl --games 1 --max-frames 300`.
- Risks/Notes: the winner rule is intentionally simple: average score first, then average best combo and average frames as tie-breakers.

## 2026-05-17 - Add model experiment pipeline

- Changed: added `run_model_experiment.py` to train a candidate model and compare it against a baseline with shared evaluation seeds; added `test_run_model_experiment.py`; ignored local `runs/` outputs in `.gitignore`; updated `README.md`.
- Why: v0.2 model iteration needs a single reproducible command for training and comparing candidates.
- Behavior: `python3 run_model_experiment.py --data runs/experiment.json --candidate runs/v02_model.pkl` trains a candidate model, saves it, and prints baseline-vs-candidate metrics; `--json` emits structured training and comparison output.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile run_model_experiment.py test_run_model_experiment.py compare_models.py train_model.py evaluate_model.py`; ran `python3 run_model_experiment.py --candidate /private/tmp/rockfall-candidate.pkl --games 1 --max-frames 300`; ran `python3 run_model_experiment.py --candidate /private/tmp/rockfall-candidate-json.pkl --games 1 --max-frames 300 --json`.
- Risks/Notes: compared models still must match the current feature shape; local experiment artifacts under `runs/` are intentionally untracked.

## 2026-05-16 - Add model comparison CLI

- Changed: added `compare_models.py` for evaluating one or more model files with shared seeds; added `test_compare_models.py`; updated `README.md`.
- Why: v0.2 experiments need a direct way to compare default and candidate models without manually running separate commands and aligning settings.
- Behavior: `python3 compare_models.py game_model.pkl runs/v02_model.pkl` prints a comparison table; `--json` prints structured comparison output.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile compare_models.py test_compare_models.py evaluate_model.py`; ran `python3 compare_models.py game_model.pkl --games 1 --max-frames 300`; ran `python3 compare_models.py game_model.pkl --games 1 --max-frames 300 --json`.
- Risks/Notes: all compared models must be compatible with the current feature shape.

## 2026-05-16 - Create model output directories

- Changed: extracted `ensure_parent_dir` in `data_store.py`; updated `train_model.py` to create missing parent directories before saving model files; added `test_train_model.py`; updated `README.md`; updated this devlog.
- Why: model experiments should support paths like `runs/model.pkl` without manual directory setup.
- Behavior: `python3 train_model.py --model runs/model.pkl` now creates `runs/` before writing the model.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile data_store.py train_model.py test_data_store.py test_train_model.py`; ran `python3 train_model.py --help`.
- Risks/Notes: no training behavior changed; this only affects output path preparation.

## 2026-05-16 - Create data collection directories

- Changed: updated `data_store.py` so appending gameplay data creates missing parent directories; expanded `test_data_store.py`; clarified `README.md`; updated this devlog.
- Why: the new `game.py --data runs/experiment.json` workflow should work without manual directory setup.
- Behavior: when appending non-empty gameplay data to a nested path, missing parent directories are created before writing.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile data_store.py test_data_store.py game.py test_game.py`.
- Risks/Notes: empty data sessions still do not create files or directories.

## 2026-05-16 - Allow alternate data collection files

- Changed: updated `game.py` with a `--data` option for the append target; added `test_game.py`; documented experiment data collection in `README.md`; updated this devlog.
- Why: fresh playtest experiments should be able to write separate datasets without touching the default tracked `game_data.json`.
- Behavior: `python3 game.py` still appends to `game_data.json`; `python3 game.py --data runs/experiment.json` appends to the selected file.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py test_game.py`; ran `python3 game.py --help`.
- Risks/Notes: selected parent directories must already exist; this follows the existing data-store behavior.

## 2026-05-16 - Cover player movement bounds

- Changed: expanded `test_game_core.py` with tests for left-edge clamp, right-edge clamp, and missing-action movement behavior; updated this devlog.
- Why: player movement is a core hand-feel contract and should be protected before future speed or control tuning.
- Behavior: no gameplay behavior changed.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game_core.py test_game_core.py`.
- Risks/Notes: test-only change.

## 2026-05-16 - Document current feature set

- Changed: updated `README.md` with a `Current Features` section covering manual play, AI play, difficulty, feedback, evaluation, and verification; updated this devlog.
- Why: the v0.2 development line has accumulated enough small improvements that README needed a consolidated feature map.
- Behavior: no gameplay behavior changed.
- Verification: ran `python3 -m unittest`; ran `git diff --check`.
- Risks/Notes: documentation-only change; keep this section current as new systems land.

## 2026-05-16 - Generalize release-check wording

- Changed: updated `release_check.py` argparse text and the project-status bullet in `README.md`; updated this devlog.
- Why: the project is now on `0.2.0-dev`, so current release-check wording should not imply it is only for v0.1.
- Behavior: help text now describes generic Rockfall release readiness checks.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile release_check.py test_release_check.py`; ran `python3 release_check.py --help`.
- Risks/Notes: documentation/output wording only.

## 2026-05-16 - Hide pygame prompt in AI play

- Changed: updated `play_with_model.py` to set `PYGAME_HIDE_SUPPORT_PROMPT` before pygame is imported; updated this devlog.
- Why: AI play error output should focus on the actionable message, not pygame's support banner.
- Behavior: model-play startup and load-failure paths no longer print the pygame community prompt.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile play_with_model.py test_play_with_model.py`; ran `SDL_VIDEODRIVER=dummy python3 play_with_model.py --model missing.pkl --mute` and confirmed only the concise load error printed with exit status 1.
- Risks/Notes: no gameplay behavior changed.

## 2026-05-16 - Handle AI model load failures

- Changed: updated `play_with_model.py` to catch model loading errors, print a concise message, quit pygame, and return a nonzero exit code; expanded `test_play_with_model.py`; updated `README.md`.
- Why: missing or invalid model files should fail clearly instead of dumping a traceback after opening the game window.
- Behavior: `python3 play_with_model.py --model missing.pkl` now reports the load failure and exits with status 1.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py evaluate_model.py release_check.py settings.py difficulty.py game_core.py game_events.py game_audio.py scores.py data_store.py features.py spawning.py test_scores.py test_data_store.py test_features.py test_evaluate_model.py test_difficulty.py test_spawning.py test_game_core.py test_game_audio.py test_release_check.py test_play_with_model.py`; ran `SDL_VIDEODRIVER=dummy python3 play_with_model.py --model missing.pkl --mute` and confirmed it printed a concise error with exit status 1.
- Risks/Notes: the error handler is intentionally scoped around model loading; gameplay errors after a model loads still surface normally.

## 2026-05-16 - Show active model name in AI play

- Changed: updated `play_with_model.py` to derive a mode label from the selected model filename and use it in the window title plus start/pause/game-over screens; added `test_play_with_model.py`; updated `README.md`.
- Why: model experiments are easier to compare when the active model file is visible during playback.
- Behavior: `python3 play_with_model.py --model experiments/alt_model.pkl` displays `Model Play (alt_model.pkl)` in the UI.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py evaluate_model.py release_check.py settings.py difficulty.py game_core.py game_events.py game_audio.py scores.py data_store.py features.py spawning.py test_scores.py test_data_store.py test_features.py test_evaluate_model.py test_difficulty.py test_spawning.py test_game_core.py test_game_audio.py test_release_check.py test_play_with_model.py`; ran `python3 play_with_model.py --help`.
- Risks/Notes: very long model filenames may crowd the menu line; use shorter experiment filenames if needed.

## 2026-05-16 - Include evaluation settings in JSON

- Changed: updated `evaluate_model.py` JSON payloads to include `max_frames` and `random_seed`; expanded `test_evaluate_model.py`; clarified `README.md`.
- Why: stored JSON results need enough context to compare runs later.
- Behavior: `python3 evaluate_model.py --json` now includes the model path, frame limit, random seed, and summary metrics.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py evaluate_model.py release_check.py settings.py difficulty.py game_core.py game_events.py game_audio.py scores.py data_store.py features.py spawning.py test_scores.py test_data_store.py test_features.py test_evaluate_model.py test_difficulty.py test_spawning.py test_game_core.py test_game_audio.py test_release_check.py`; ran `python3 evaluate_model.py --games 1 --max-frames 300 --random-seed 42 --json`.
- Risks/Notes: text output is unchanged; only JSON consumers see the additional keys.

## 2026-05-16 - Add JSON model evaluation output

- Changed: updated `evaluate_model.py` with `--json` output and a summary payload helper; expanded `test_evaluate_model.py`; documented the flag in `README.md`.
- Why: future model comparisons and charts should consume structured metrics instead of parsing human-readable text.
- Behavior: `python3 evaluate_model.py --json` prints the model path and summary metrics as sorted, indented JSON; default text output is unchanged.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py evaluate_model.py release_check.py settings.py difficulty.py game_core.py game_events.py game_audio.py scores.py data_store.py features.py spawning.py test_scores.py test_data_store.py test_features.py test_evaluate_model.py test_difficulty.py test_spawning.py test_game_core.py test_game_audio.py test_release_check.py`; ran `python3 evaluate_model.py --games 3 --max-frames 1800`; ran `python3 evaluate_model.py --games 1 --max-frames 300 --json`.
- Risks/Notes: JSON output still runs the same pygame-surface simulation and depends on the model file loading successfully.

## 2026-05-16 - Share evaluation summary formatting

- Changed: updated `evaluate_model.py` with `format_summary_lines`; updated `release_check.py` to reuse it; expanded `test_evaluate_model.py`.
- Why: evaluation and release-check output had duplicated metric formatting after combo metrics were added.
- Behavior: CLI output content stays the same, but summary formatting now has one shared implementation.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py evaluate_model.py release_check.py settings.py difficulty.py game_core.py game_events.py game_audio.py scores.py data_store.py features.py spawning.py test_scores.py test_data_store.py test_features.py test_evaluate_model.py test_difficulty.py test_spawning.py test_game_core.py test_game_audio.py test_release_check.py`; ran `python3 evaluate_model.py --games 3 --max-frames 1800`; ran `python3 release_check.py --games 1 --max-frames 300`.
- Risks/Notes: output ordering is intentionally preserved; exact-output parsers should see the same metric lines as before.

## 2026-05-16 - Add incoming rock warnings

- Changed: updated `settings.py` and `game_core.py` with a top-of-screen warning strip for rocks that are still entering from above; expanded `test_game_core.py`; updated `README.md`.
- Why: lane pressure should be readable before a rock fully appears, especially as spawn frequency increases.
- Behavior: when a falling rock has a negative y-position, its lane shows a short warning strip at the top edge of the playfield.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py evaluate_model.py release_check.py settings.py difficulty.py game_core.py game_events.py game_audio.py scores.py data_store.py features.py spawning.py test_scores.py test_data_store.py test_features.py test_evaluate_model.py test_difficulty.py test_spawning.py test_game_core.py test_game_audio.py test_release_check.py`; ran `python3 evaluate_model.py --games 3 --max-frames 1800` with average score 78.67, average best combo 14.00, best combo 17.
- Risks/Notes: this is visual-only; real-window playtesting should confirm the warning is noticeable without looking like a separate obstacle.

## 2026-05-16 - Report combo in model evaluation

- Changed: updated `evaluate_model.py` to include per-run best combo and summary combo metrics; updated `release_check.py` output; expanded `test_evaluate_model.py`; updated `README.md`.
- Why: combo scoring is now part of gameplay quality, so model comparisons need to report more than score and survival frames.
- Behavior: `evaluate_model.py` and `release_check.py` now print average best combo and best combo alongside existing score/frame/timeout metrics.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py evaluate_model.py release_check.py settings.py difficulty.py game_core.py game_events.py game_audio.py scores.py data_store.py features.py spawning.py test_scores.py test_data_store.py test_features.py test_evaluate_model.py test_difficulty.py test_spawning.py test_game_core.py test_game_audio.py test_release_check.py`; ran `python3 evaluate_model.py --games 3 --max-frames 1800` with average score 78.67, average best combo 14.00, best combo 17; ran `python3 release_check.py --games 1 --max-frames 300`.
- Risks/Notes: this changes CLI output shape; scripts that parse exact evaluation text may need to account for the new lines.

## 2026-05-16 - Polish HUD state colors

- Changed: updated `settings.py` and `game_core.py` with low-life, active-combo, and progress-background HUD colors; expanded `test_game_core.py`; updated `README.md`.
- Why: important run state should be readable from the HUD without requiring careful text parsing.
- Behavior: low lives now use a warning color, active combo uses a combo color, and the difficulty progress bar has a visible dark background.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py evaluate_model.py release_check.py settings.py difficulty.py game_core.py game_events.py game_audio.py scores.py data_store.py features.py spawning.py test_scores.py test_data_store.py test_features.py test_evaluate_model.py test_difficulty.py test_spawning.py test_game_core.py test_game_audio.py test_release_check.py`; ran `python3 evaluate_model.py --games 3 --max-frames 1800` with average score 78.67, best 98, worst 66.
- Risks/Notes: color thresholds are intentionally simple; real-window playtesting should confirm they remain legible against hit tint and menu colors.

## 2026-05-16 - Add hit screen tint

- Changed: updated `settings.py` and `game_core.py` with a fading hit overlay color/alpha; expanded `test_game_core.py`; updated `README.md`.
- Why: the player flash helps, but hits should be visible even when the player is near the bottom and attention is on falling rocks.
- Behavior: after a hit, the gameplay screen receives a short red tint that fades with invincibility frames; scoring, collision rules, and model features are unchanged.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py evaluate_model.py release_check.py settings.py difficulty.py game_core.py game_events.py game_audio.py scores.py data_store.py features.py spawning.py test_scores.py test_data_store.py test_features.py test_evaluate_model.py test_difficulty.py test_spawning.py test_game_core.py test_game_audio.py test_release_check.py`; ran `python3 evaluate_model.py --games 3 --max-frames 1800` with average score 78.67, best 98, worst 66.
- Risks/Notes: the tint intensity is conservative and should be checked in a real window against the current dark background.

## 2026-05-16 - Add near-miss feedback

- Changed: updated `settings.py` and `game_core.py` with near-miss distance and message color; added near-miss detection and feedback message on close dodges; expanded `test_game_core.py`; updated `README.md`.
- Why: close dodges should feel intentional and readable without changing the scoring economy.
- Behavior: when a rock leaves the screen close to the player's horizontal center, the game shows `CLOSE!`; score, combo rules, events, and model features are unchanged.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py evaluate_model.py release_check.py settings.py difficulty.py game_core.py game_events.py game_audio.py scores.py data_store.py features.py spawning.py test_scores.py test_data_store.py test_features.py test_evaluate_model.py test_difficulty.py test_spawning.py test_game_core.py test_game_audio.py test_release_check.py`; ran `python3 evaluate_model.py --games 3 --max-frames 1800` with average score 78.67, best 98, worst 66.
- Risks/Notes: the distance threshold is a first-pass tuning value and should be judged during real-window playtesting.

## 2026-05-16 - Style menu screens

- Changed: updated `settings.py` and `game_core.py` with menu title/accent colors, shared background drawing on start/pause/game-over screens, centered text helper, and menu text color rules; expanded `test_game_core.py`; updated `README.md`.
- Why: after the playfield polish, the non-playing screens still looked like the old default pygame presentation.
- Behavior: start, pause, and game-over screens now use the same lane background, title shadow, accent divider, and clearer text hierarchy.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py evaluate_model.py release_check.py settings.py difficulty.py game_core.py game_events.py game_audio.py scores.py data_store.py features.py spawning.py test_scores.py test_data_store.py test_features.py test_evaluate_model.py test_difficulty.py test_spawning.py test_game_core.py test_game_audio.py test_release_check.py`; ran `python3 evaluate_model.py --games 3 --max-frames 1800` with average score 78.67, best 98, worst 66.
- Risks/Notes: this changes screen layout spacing only; real-window review should still verify that game-over text does not feel crowded.

## 2026-05-16 - Add playfield visual polish

- Changed: updated `settings.py` and `game_core.py` with shared visual colors, lane guide drawing, player shadow/outline, and obstacle shadow/highlight; expanded `test_game_core.py`; updated `README.md`.
- Why: v0.2 should look more like an intentional arcade game and less like debug rectangles while staying asset-free.
- Behavior: the playfield now has a darker background, readable lane lines, a clearer player silhouette, and falling rocks with simple depth cues.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py evaluate_model.py release_check.py settings.py difficulty.py game_core.py game_events.py game_audio.py scores.py data_store.py features.py spawning.py test_scores.py test_data_store.py test_features.py test_evaluate_model.py test_difficulty.py test_spawning.py test_game_core.py test_game_audio.py test_release_check.py`; ran `python3 evaluate_model.py --games 3 --max-frames 1800` with average score 78.67, best 98, worst 66.
- Risks/Notes: this is a lightweight pygame drawing pass; real-window visual spacing and color contrast should still be checked by hand.

## 2026-05-16 - Add optional sound feedback

- Changed: added `game_events.py` and `game_audio.py`; updated `game_core.py` to emit avoid/hit/level-up events; updated manual and model entrypoints to play generated tones; added `--mute`; added `test_game_audio.py` and expanded `test_game_core.py`; documented mute usage in `README.md`.
- Why: v0.2 should make score, hit, and level-up feedback feel more immediate.
- Behavior: avoided rocks, hits, and level-ups now trigger optional generated sound effects. If audio initialization fails, gameplay continues silently.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py evaluate_model.py release_check.py settings.py difficulty.py game_core.py game_events.py game_audio.py scores.py data_store.py features.py spawning.py test_scores.py test_data_store.py test_features.py test_evaluate_model.py test_difficulty.py test_spawning.py test_game_core.py test_game_audio.py test_release_check.py`; ran `python3 game.py --help`; ran `python3 play_with_model.py --help`; ran `python3 evaluate_model.py --games 3 --max-frames 1800`.
- Risks/Notes: generated tones depend on pygame mixer availability; real-window audio should be checked on the user's machine.

## 2026-05-16 - Add combo scoring

- Changed: updated `settings.py` and `game_core.py` with combo counters, combo score bonuses, combo HUD text, and game-over best combo; expanded `test_game_core.py`; documented combo behavior in `README.md`.
- Why: v0.2 should reward sustained clean movement, not only count avoided rocks one by one.
- Behavior: each avoided rock increases combo; every 5 combo adds one extra point per avoided rock up to a capped bonus; hits reset the active combo but preserve best combo for the run summary.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py evaluate_model.py release_check.py settings.py difficulty.py game_core.py scores.py data_store.py features.py spawning.py test_scores.py test_data_store.py test_features.py test_evaluate_model.py test_difficulty.py test_spawning.py test_game_core.py test_release_check.py`; ran `python3 evaluate_model.py --games 3 --max-frames 1800` with average score 78.67, best 98, worst 66.
- Risks/Notes: scoring baselines are no longer directly comparable to v0.1 because combo bonuses increase total score.

## 2026-05-16 - Start v0.2 development

- Changed: updated `settings.py` version to `0.2.0-dev`; updated `README.md` project status.
- Why: v0.1.0 has been tagged, so new changes should identify as the next development line.
- Behavior: window titles and release checks now identify local builds as `0.2.0-dev`.
- Verification: ran `python3 -m unittest`.
- Risks/Notes: this is a development version, not a release tag.

## 2026-05-16 - Release v0.1.0

- Changed: promoted `settings.py` version from `0.1.0-candidate` to `0.1.0`; updated `README.md` project status and next steps.
- Why: hands-on playtest feedback was good enough to mark the first playable release.
- Behavior: window titles and release checks now identify the build as `0.1.0`.
- Verification: ran `python3 release_check.py`.
- Risks/Notes: v0.1.0 is still a small pygame/ML project; future versions should focus on more fresh play data, model comparison, and visual/audio polish.

## 2026-05-16 - Polish release check output

- Changed: updated `release_check.py` so unit-test output writes to stdout and status headings flush before long-running checks.
- Why: the first release check output showed unittest results before the release-check heading, which made the command harder to read.
- Behavior: `python3 release_check.py` now prints the version header and step labels before test/evaluation output.
- Verification: ran `python3 release_check.py`; ran `python3 -m unittest`.
- Risks/Notes: output-only change.

## 2026-05-16 - Add release readiness check

- Changed: added `release_check.py`; added `test_release_check.py`; updated `README.md` full verification instructions.
- Why: v0.1 needs one memorable command that runs the release safety checks instead of requiring several commands.
- Behavior: `python3 release_check.py` prints the candidate version, runs the unit test suite, runs a short headless model evaluation, and exits nonzero if tests fail.
- Verification: ran `python3 release_check.py`; ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py evaluate_model.py release_check.py settings.py difficulty.py game_core.py scores.py data_store.py features.py spawning.py test_scores.py test_data_store.py test_features.py test_evaluate_model.py test_difficulty.py test_spawning.py test_game_core.py test_release_check.py`.
- Risks/Notes: release check is still headless; it does not replace final hands-on pygame window playtesting.

## 2026-05-16 - Mark v0.1 candidate version

- Changed: added `VERSION = "0.1.0-candidate"` in `settings.py`; updated manual and model window captions; documented the candidate version in `README.md`.
- Why: the project is close enough to v0.1 that builds should identify their current candidate version.
- Behavior: pygame window titles now show the v0.1 candidate version.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py evaluate_model.py settings.py difficulty.py game_core.py scores.py data_store.py features.py spawning.py test_scores.py test_data_store.py test_features.py test_evaluate_model.py test_difficulty.py test_spawning.py test_game_core.py`; ran `python3 evaluate_model.py --games 3 --max-frames 600`.
- Risks/Notes: this does not create a git tag; tag `v0.1.0` after a final hands-on playtest.

## 2026-05-16 - Playtest and retrain with fresh data

- Changed: appended 812 new manual playtest samples to `game_data.json`; retrained `game_model.pkl` from 2472 valid samples.
- Why: real-window playtesting produced fresh gameplay data, so the default model needed to stay aligned with the tracked dataset.
- Behavior: default AI play now uses the retrained model. Training reported left=1226, right=1246, validation accuracy=0.903.
- Verification: launched `python3 game.py`; ran `python3 train_model.py`; ran `python3 -m unittest`; ran `python3 evaluate_model.py --games 5 --max-frames 1800` with average score 53.40, best 65, worst 43, timed out games 2.
- Risks/Notes: Computer Use could not reliably inspect the pygame accessibility tree, so this was a launch/playtest plus metrics pass rather than a visual UI audit.

## 2026-05-16 - Document v0.1 project status

- Changed: updated `README.md` with current project status, full verification commands, and next steps toward v0.1.
- Why: the project now has enough functionality that future work needs a clear state summary and completion path.
- Behavior: no gameplay behavior changed.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py evaluate_model.py settings.py difficulty.py game_core.py scores.py data_store.py features.py spawning.py test_scores.py test_data_store.py test_features.py test_evaluate_model.py test_difficulty.py test_spawning.py test_game_core.py`.
- Risks/Notes: v0.1 should still wait for a real-window playtest.

## 2026-05-16 - Clarify controls on screens

- Changed: updated `game_core.py` so start and pause screens use reusable line builders with movement, pause, restart, and quit hints; expanded `test_game_core.py`; documented controls in `README.md`.
- Why: first-time players needed visible controls before starting the game.
- Behavior: start and pause screens now explain movement, pause/resume, restart, and quit controls.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py evaluate_model.py settings.py difficulty.py game_core.py scores.py data_store.py features.py spawning.py test_scores.py test_data_store.py test_features.py test_evaluate_model.py test_difficulty.py test_spawning.py test_game_core.py`; ran `python3 evaluate_model.py --games 3 --max-frames 1800`.
- Risks/Notes: the start screen has more text now; real-window visual spacing should be checked before tagging v0.1.

## 2026-05-16 - Expand game-over summary

- Changed: updated `game_core.py` so the game-over screen is built from reusable summary lines; expanded `test_game_core.py`.
- Why: the ending screen should summarize the run instead of only showing score and high score.
- Behavior: game over now shows mode, final score, high score, level reached, lives left, and restart/quit controls.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py evaluate_model.py settings.py difficulty.py game_core.py scores.py data_store.py features.py spawning.py test_scores.py test_data_store.py test_features.py test_evaluate_model.py test_difficulty.py test_spawning.py test_game_core.py`.
- Risks/Notes: the screen now has more text; if the visual style changes later, spacing should be reviewed in a real window.

## 2026-05-16 - Add transient gameplay messages

- Changed: updated `settings.py` and `game_core.py` to show short floating messages for score gains, hits, and level-ups; expanded `test_game_core.py`.
- Why: score, damage, and level changes should be visible without requiring the player to read the HUD constantly.
- Behavior: avoided rocks spawn a green `+1`, hits spawn a yellow `HIT!`, and level increases show a blue `LEVEL X` message.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py evaluate_model.py settings.py difficulty.py game_core.py scores.py data_store.py features.py spawning.py test_scores.py test_data_store.py test_features.py test_evaluate_model.py test_difficulty.py test_spawning.py test_game_core.py`; ran `python3 evaluate_model.py --games 3 --max-frames 1800`.
- Risks/Notes: messages are intentionally visual-only and do not affect model features, scoring, or collected training data.

## 2026-05-16 - Add hit feedback and invincibility frames

- Changed: updated `settings.py` and `game_core.py` with hit flash color, invincibility frames, and player flash rendering; added `test_game_core.py`.
- Why: collisions previously removed a life with no visual feedback and could punish the player too harshly during crowded frames.
- Behavior: after a hit, the player flashes briefly and cannot lose another life for 45 frames.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py evaluate_model.py settings.py difficulty.py game_core.py scores.py data_store.py features.py spawning.py test_scores.py test_data_store.py test_features.py test_evaluate_model.py test_difficulty.py test_spawning.py test_game_core.py`; ran `python3 evaluate_model.py --games 3 --max-frames 1800`.
- Risks/Notes: invincibility makes clustered collisions more forgiving, so future difficulty tuning should account for it.

## 2026-05-16 - Add lane-based rock spawning

- Changed: added `spawning.py`; updated `settings.py` and `game_core.py` so rocks spawn from fixed lanes and avoid nearby repeat lanes at lower difficulty; added `test_spawning.py`; updated README gameplay notes.
- Why: pure random x-position spawning made the game harder to read and could produce awkward repeated drops.
- Behavior: rocks now spawn on 8 readable lanes. Early levels keep at least a two-lane gap from the previous spawn; higher difficulty reduces that protection until maximum difficulty can repeat pressure anywhere.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py evaluate_model.py settings.py difficulty.py game_core.py scores.py data_store.py features.py spawning.py test_scores.py test_data_store.py test_features.py test_evaluate_model.py test_difficulty.py test_spawning.py`; ran `python3 evaluate_model.py --games 3 --max-frames 1800`.
- Risks/Notes: this changes obstacle distribution without retraining from newly collected lane-based data; future collection should refresh the dataset.

## 2026-05-16 - Add dynamic difficulty curve

- Changed: added `difficulty.py`; updated `settings.py` and `game_core.py` so each difficulty level increases obstacle speed and reduces spawn interval; added `test_difficulty.py`; documented the gameplay behavior in `README.md`.
- Why: the game previously increased falling speed over time but kept the same spawn cadence, which made progression feel flat.
- Behavior: difficulty now rises every 600 frames, obstacle speed increases by level, and obstacle spawn frequency tightens from 25 frames down to a 12-frame minimum.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py evaluate_model.py settings.py difficulty.py game_core.py scores.py data_store.py features.py test_scores.py test_data_store.py test_features.py test_evaluate_model.py test_difficulty.py`; ran `python3 evaluate_model.py --games 3 --max-frames 600`; ran `python3 evaluate_model.py --games 3 --max-frames 1800`.
- Risks/Notes: this changes gameplay pacing without retraining the model; evaluation scores may shift because later frames generate rocks more aggressively.

## 2026-05-16 - Add headless model evaluation

- Changed: added `evaluate_model.py` for repeated model simulations without opening a window; added `test_evaluate_model.py`; documented the evaluation command in `README.md`.
- Why: model changes need a numeric comparison path instead of relying only on visual observation.
- Behavior: `python3 evaluate_model.py --games 10 --max-frames 3600` reports average score, best/worst score, average frames, and timeout count.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py evaluate_model.py settings.py game_core.py scores.py data_store.py features.py test_scores.py test_data_store.py test_features.py test_evaluate_model.py`; ran `python3 evaluate_model.py --games 3 --max-frames 600`.
- Risks/Notes: evaluation uses the same random obstacle generator as the game and seeds each run for repeatability.

## 2026-05-16 - Use richer obstacle features for the model

- Changed: added `features.py`; updated `game_core.py` and `train_model.py` to share model feature extraction; added `test_features.py`; documented the current feature set in `README.md`; retrained `game_model.pkl`.
- Why: the model previously saw only player x-position and the first obstacle x-position, which ignored obstacle height and horizontal distance.
- Behavior: model training and model play now use player x-position, nearest obstacle x-position, nearest obstacle y-position, and horizontal distance to the nearest obstacle.
- Verification: installed dependencies with `python3 -m pip install -r requirements.txt`; ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py settings.py game_core.py scores.py data_store.py features.py test_scores.py test_data_store.py test_features.py`; ran `python3 train_model.py`; ran a model prediction smoke test against `game_model.pkl`; ran a pygame dummy-display smoke test.
- Risks/Notes: old two-feature model files are no longer compatible with the default AI play path; retraining is required for alternate model files.

## 2026-05-16 - Add model experiment CLI options

- Changed: updated `train_model.py` with argparse options for data path, model path, validation split, random seed, and tree count; updated `play_with_model.py` with a model path option; delayed heavy imports so help text is easier to access; documented examples in `README.md`.
- Why: model experiments should not require editing source code or overwriting `game_model.pkl`.
- Behavior: default commands still work, but alternate data/model files can now be passed from the command line.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py settings.py game_core.py scores.py data_store.py test_scores.py test_data_store.py`; ran `python3 train_model.py --help`; ran `python3 play_with_model.py --help`.
- Risks/Notes: full training execution still depends on installed `numpy`, `scikit-learn`, and `joblib`.

## 2026-05-16 - Append collected gameplay data safely

- Changed: added `data_store.py`; updated `game.py` to append new gameplay samples to `game_data.json`; added `test_data_store.py`; updated README wording for data collection.
- Why: data collection previously overwrote the full training dataset at the end of every session, which could erase useful samples.
- Behavior: new manual gameplay samples are appended to existing data. Empty sessions still leave the data file unchanged, and invalid existing data fails loudly instead of being overwritten.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py settings.py game_core.py scores.py data_store.py test_scores.py test_data_store.py`.
- Risks/Notes: no migration was needed because the existing `game_data.json` already stores a top-level list.

## 2026-05-16 - Add tests for high-score storage

- Changed: added `test_scores.py`; documented `python3 -m unittest` in `README.md`.
- Why: high-score persistence should be protected from regressions around missing files, invalid JSON, lower-score overwrites, and per-mode separation.
- Behavior: no gameplay behavior changed.
- Verification: ran `python3 -m unittest`; ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py settings.py game_core.py scores.py test_scores.py`.
- Risks/Notes: tests currently cover pure score storage only; pygame gameplay still needs an installed pygame environment for runtime checks.

## 2026-05-16 - Add local high scores

- Changed: added `scores.py`; updated `game.py`, `play_with_model.py`, and `game_core.py` to load, display, and record per-mode high scores; ignored local `high_scores.json`; documented the runtime file in `README.md`.
- Why: score is more useful when players and model runs can compare against a saved best result.
- Behavior: manual and model modes each display a saved high score, show a new best immediately during play, and persist it after game over.
- Verification: ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py settings.py game_core.py scores.py`; ran a `scores.py` helper smoke test with a temporary score file.
- Risks/Notes: high scores are local-only and intentionally untracked; corrupted score files reset to an empty score table.

## 2026-05-16 - Add pause support

- Changed: added a shared paused screen state in `game_core.py`; wired P-to-pause/resume and R-to-restart while paused in `game.py` and `play_with_model.py`.
- Why: repeated playtesting and data collection need a way to stop the action without closing the game.
- Behavior: both manual and AI modes can pause with P, resume with P, restart from pause with R, and quit with ESC.
- Verification: ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py settings.py game_core.py`.
- Risks/Notes: pause uses a simple full-screen message for now; later UI polish could draw it as an overlay on the frozen game state.

## 2026-05-16 - Add dependency file

- Changed: added `requirements.txt`; updated `README.md` installation and run commands to use `python3` and the dependency file.
- Why: the local smoke test found `pygame` missing, and the project needed a single source for Python dependencies.
- Behavior: no gameplay behavior changed; setup instructions are easier to follow on a fresh machine.
- Verification: ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py settings.py game_core.py`.
- Risks/Notes: dependencies are currently unpinned; future releases can add version ranges after testing on a clean environment.

## 2026-05-16 - Add start and game-over screens

- Changed: updated `game_core.py` with resettable game state plus shared start/game-over screens; updated `game.py` and `play_with_model.py` to use explicit screen states; prevented empty data-collection sessions from overwriting `game_data.json`.
- Why: dying previously ended the program immediately, which made the game feel abrupt and made repeated testing awkward.
- Behavior: both manual and AI modes now start after SPACE, show final score on game over, restart with R, and quit with ESC. Quitting data collection without moves leaves the existing data file unchanged.
- Verification: ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py settings.py game_core.py`; attempted a pygame smoke test, but the current Python environment does not have `pygame` installed.
- Risks/Notes: screen flow is keyboard-only for now; a future pass could add pause, mouse buttons, and a more polished visual style.

## 2026-05-16 - Make training output reproducible and visible

- Changed: updated `train_model.py` to skip invalid entries, require both actions, use a fixed random seed, stratify the train/test split when possible, and print sample counts plus validation accuracy.
- Why: training previously overwrote the model silently, making it hard to compare models or spot bad data.
- Behavior: training now reports how much data was used, action balance, validation accuracy, and where the model was saved.
- Verification: ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py settings.py game_core.py`.
- Risks/Notes: `game_model.pkl` was not retrained in this change; the feature shape remains compatible with the existing model.

## 2026-05-16 - Add score for avoided rocks

- Changed: updated `game_core.py` to track score and render it in the HUD.
- Why: the game needed a visible success metric, especially now that manual and AI modes share the same fail condition.
- Behavior: each obstacle that leaves the screen without colliding adds 1 point; both manual and AI modes show the score.
- Verification: ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py settings.py game_core.py`.
- Risks/Notes: scoring currently counts avoided obstacles only; future scoring could add survival time, combos, or difficulty multipliers.

## 2026-05-16 - Share the game engine between manual and AI modes

- Changed: added `game_core.py` with shared game state, movement, obstacle spawning, collision, difficulty, and HUD rendering; rewrote `game.py` and `play_with_model.py` as small entrypoints.
- Why: manual data collection and model-controlled play were maintaining duplicate game loops, which made behavior drift likely.
- Behavior: manual and AI modes now use the same gameplay rules. Manual data collection ignores simultaneous left/right input instead of recording conflicting actions.
- Verification: ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py settings.py game_core.py`.
- Risks/Notes: this is a structural refactor; visual/manual play should still be checked in a pygame window when convenient.

## 2026-05-16 - Give AI play mode lives and collision

- Changed: updated `play_with_model.py` so model-controlled play tracks lives, detects obstacle collisions, ends at zero lives, increases difficulty over time, and shows the same basic HUD as manual play.
- Why: AI play mode previously only moved and rendered the player, so it could not be used to judge whether the model was actually surviving the game.
- Behavior: model-controlled play now has a real fail condition and visible lives/difficulty feedback.
- Verification: ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py settings.py`.
- Risks/Notes: manual and AI modes still duplicate some game-loop logic; this should be unified in a future refactor.

## 2026-05-16 - Extract shared settings and clamp manual movement

- Changed: added `settings.py`; updated `game.py` and `play_with_model.py` to use shared constants; clamped manual player movement to the screen bounds.
- Why: the manual and model-driven game loops were duplicating core settings, and manual play allowed the player to move outside the visible screen.
- Behavior: human-controlled play now keeps the player within the window, matching the AI-controlled movement constraints.
- Verification: ran `python3 -X pycache_prefix=/private/tmp/rockfall-pycache -m py_compile game.py play_with_model.py train_model.py settings.py`.
- Risks/Notes: the two game loops still duplicate update/render logic and should eventually share a single game engine.

## 2026-05-16 - Add project devlog

- Changed: added `DEVLOG.md`; documented the devlog workflow in `README.md`.
- Why: future changes need a searchable history for debugging gameplay, training, and model behavior.
- Behavior: no gameplay behavior changed.
- Verification: documentation-only change; reviewed project files and current structure.
- Risks/Notes: future functional changes should add their own entry above this one.
