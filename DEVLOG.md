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
