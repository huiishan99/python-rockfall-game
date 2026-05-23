# Rockfall Game with Machine Learning
![屏幕截图 2024-04-24 141624](https://github.com/huiishan99/Python_Rockfall/assets/61934115/80c177e3-445b-4448-94b2-3b34a3a2ea08)


## Description
This project integrates a machine learning model into a simple pygame-based game, where the player's movements are controlled by the model's predictions based on the position of obstacles. The project includes scripts for collecting gameplay data, training a model on this data, and running the game with the trained model.

## Project Status

Current version: `0.8.0-dev`.

This is now in v0.8 development after the playable v0.1 release:

- Manual play collects training data.
- AI play uses a trained Random Forest model.
- Headless evaluation reports model score baselines.
- Runtime hand-feel tuning for difficulty, player speed, and initial lives is implemented across play, evaluation, comparison, experiments, and release checks.
- Evaluation and comparison reports include survival metrics and can be saved as JSON artifacts.
- Data inspection can check collected samples before training and save quality reports.
- Score milestone life recovery gives damaged runs a comeback path without changing controls.
- Variant rocks add different fall speeds and score rewards while keeping the model feature format compatible.
- Release checks can save versioned JSON artifacts for candidate builds.
- Difficulty, lane-based spawning, high scores, hit feedback, visual polish, styled menu screens, pause, restart, game-over summary, and release checks are implemented.
- Unit tests cover storage, feature extraction, difficulty, spawning, evaluation summaries, and core behavior/rendering.

## Current Features

- Manual play for data collection, with left/right or A/D movement, pause, restart, and local high scores.
- AI play with a trained Random Forest model, selectable model path, visible active model filename, optional mute, and clear model-load failures.
- Model play can jump back to manual data collection when the model feels weak, keeping the same tuning settings.
- Dynamic difficulty with `easy`, `normal`, and `hard` presets, faster falling speed, tighter spawn frequency, and lane-based rock spawning.
- Gameplay feedback for score gains, combos, score-milestone life recovery, close dodges, hits, level-ups, low lives, hit screen tint, variant rock-shaped obstacles, a mine-cart player, panel-based HUD, and styled menu prompts.
- Start-screen `HOW IT WORKS` help that explains the game rules and the machine-learning loop from manual data collection to model play.
- Start-screen `PLAY WITH MODEL` button that launches AI play when `game_model.pkl` exists, or shows a training prompt when no model has been trained.
- Headless model evaluation, model comparison, candidate-model experiments, and standalone data inspection with data-quality checks and text or JSON output, including score, best combo, survival frames, remaining lives, survival rate, timeouts, random seed, frame limit, difficulty, player speed, and initial lives.
- Release verification through `release_check.py`, plus unit tests for data storage, feature extraction, spawning, difficulty, audio, evaluation, release checks, and rendering behavior.

## Development Log

Every meaningful change should be recorded in [DEVLOG.md](DEVLOG.md). Add entries newest first and include what changed, why it changed, how it was verified, and any risks or follow-up notes. This is especially important when changing gameplay rules, collected data, or the trained model.

## Installation

### Prerequisites
To run this project, you'll need Python and the dependencies listed in `requirements.txt`. You can install them with:

```bash
python3 -m pip install -r requirements.txt
```

### Clone the Repository
To get started with this project, clone this repository to your local machine:

```git clone https://github.com/yourusername/rockfall-ml.git```  
```cd rockfall-ml```

## Usage

### Gameplay

Difficulty rises over time: obstacle speed increases and rocks spawn more frequently as the level bar fills. Rocks spawn from readable lanes, with early levels avoiding repeated nearby lanes and later levels allowing tighter pressure. Rocks now enter as clipped falling stones instead of showing a separate warning strip. Falling rocks have variants: normal stones behave as the baseline, heavy stones fall more slowly and award +1 score when avoided, swift stones fall faster, and ore stones award +2 score when avoided. Consecutive avoided rocks build combo, which adds score bonuses until the next hit, and score milestones can restore a lost life up to the run's starting lives. Close dodges show a `CLOSE!` feedback message without changing the score. Hits now add a short red screen tint while invincibility fades. The HUD now sits in framed panels with a cleaner progress display, while the playfield and menu screens draw lane guides, panel-backed prompts, a mine-cart player, and irregular rock obstacles with facets, shadows, cracks, and variant markings.

Controls:

- Move left/right with arrow keys or A/D.
- Press P to pause or resume.
- Press R to restart from pause or game over.
- Click `HOW IT WORKS` on the start screen, or press H, to see how gameplay data becomes a trained model.
- Click `PLAY WITH MODEL` on the start screen, or press M, to switch into model-controlled play after training.
- In model play, click `TRAIN MANUALLY` on the start screen, or press T, to return to data collection with the same tuning settings.
- Press Esc to quit.
- Add `--mute` to manual or model play commands to disable generated sound effects.
- Add `--difficulty easy`, `--difficulty normal`, or `--difficulty hard` to manual play, model play, evaluation, comparison, and experiment commands.
- Add `--player-speed 8` to tune movement speed during manual play, model play, evaluation, comparison, and experiment commands.
- Add `--lives 3` to tune initial lives during manual play, model play, evaluation, comparison, and experiment commands.

The pause screen shows the current score, best score, level, lives, and combo so a run can be reviewed mid-game.
The help screen explains that manual play records state/action samples, `train_model.py` learns left/right decisions from that data, and `play_with_model.py` uses `game_model.pkl` to predict movement every frame.

### Run Tests

Some tests use only the Python standard library and can run before installing pygame:

```bash
python3 -m unittest
```

Full verification after installing dependencies:

```bash
python3 release_check.py
```

This runs the unit tests and a short headless model evaluation. Use `--report runs/release_check.json` to save the version, unit-test result, evaluation settings, and evaluation summary as a release-check artifact.

### Data Collection
To collect data for training the machine learning model, run the `game.py` script. Press Space to start. Player movements along with obstacle positions will be appended to `game_data.json`:

```bash
python3 game.py
```

To collect an experiment dataset without touching the default tracked file:

```bash
python3 game.py --data runs/experiment.json
```

Missing parent directories for the selected data file are created automatically.

Inspect collected data before training:

```bash
python3 inspect_data.py --data game_data.json
```

The inspection command reports valid samples, skipped entries, feature names, action balance, skipped ratio, balance ratio, and data-quality warnings. Use `--report runs/data_report.json` to save the same payload, or `--json` for machine-readable output.

### Train the Model
After collecting enough data, you can train the machine learning model using the `train_model.py` script. This will process the collected data and save a trained model to the disk:

```bash
python3 train_model.py
```

The current model uses these features: player x-position, nearest obstacle x-position, nearest obstacle y-position, and horizontal distance to that obstacle. Rock variants are kept inside the live game state and are not written into the training feature vector, so existing datasets and models remain structurally compatible.

You can also experiment with alternate data or model files:

```bash
python3 train_model.py --data game_data.json --model game_model.pkl --estimators 150
```

Missing parent directories for the selected model output are created automatically.

### Run a Model Experiment

Train a candidate model and compare it against the current baseline with the same evaluation seeds:

```bash
python3 run_model_experiment.py --data runs/experiment.json --candidate runs/v02_model.pkl --games 10 --max-frames 3600
```

Use `--report runs/v02_report.json` to save the training summary, data-quality status, candidate result, and comparison metrics, or `--json` to print the same structured payload.
The experiment command refuses to use the same path for `--baseline` and `--candidate`, so the baseline model is not overwritten accidentally.

### Play the Game with the Model
Once the model is trained, you can run the game with the model controlling the player movements using the `play_with_model.py` script:

```bash
python3 play_with_model.py
```

To try a different model file:

```bash
python3 play_with_model.py --model game_model.pkl
```

Model play screens and the window title show the active model filename.
If the model file cannot be loaded, the command prints a concise error and exits nonzero.

### Evaluate the Model

Run headless simulations to compare model performance without opening a game window:

```bash
python3 evaluate_model.py --games 10 --max-frames 3600
```

The evaluation summary reports score, best combo, frame survival, remaining lives, survival rate, and timeout counts.

For scripts or future charts, emit machine-readable JSON with the evaluation settings and summary metrics:

```bash
python3 evaluate_model.py --games 10 --max-frames 3600 --json
```

Use `--report runs/eval.json` to save the same evaluation payload while still printing the normal text summary.

Compare multiple models with the same random seeds:

```bash
python3 compare_models.py game_model.pkl runs/v02_model.pkl --games 10 --max-frames 3600
```

Comparison output includes score deltas, average remaining lives, survival rate, and the best model by average score. Missing model paths fail with a concise error. Add `--json` to produce structured comparison output or `--report runs/comparison.json` to save it.

### Runtime Files

High scores are saved locally in `high_scores.json`. This file is ignored by git because it contains local play history rather than source data.

Local experiment outputs under `runs/` are also ignored by git.

## Next Steps

- Do a real-window playtest and tune player speed, initial lives, and difficulty presets together.
- Collect fresh lane-based gameplay data.
- Retrain and compare the model with `evaluate_model.py`.
- Tune rock variant spawn rates and rewards after more real-window playtesting.
- Continue collecting fresh play data and compare future models with `evaluate_model.py`.


## Contributing
Contributions to this project are welcome! Please fork the repository and submit a pull request with your improvements.
