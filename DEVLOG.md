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
