# Rockfall Game with Machine Learning
![屏幕截图 2024-04-24 141624](https://github.com/huiishan99/Python_Rockfall/assets/61934115/80c177e3-445b-4448-94b2-3b34a3a2ea08)


## Description
This project integrates a machine learning model into a simple pygame-based game, where the player's movements are controlled by the model's predictions based on the position of obstacles. The project includes scripts for collecting gameplay data, training a model on this data, and running the game with the trained model.

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

### Run Tests

Some tests use only the Python standard library and can run before installing pygame:

```bash
python3 -m unittest
```

### Data Collection
To collect data for training the machine learning model, run the `game.py` script. Press Space to start. Player movements along with obstacle positions will be appended to `game_data.json`:

```bash
python3 game.py
```

### Train the Model
After collecting enough data, you can train the machine learning model using the `train_model.py` script. This will process the collected data and save a trained model to the disk:

```bash
python3 train_model.py
```

The current model uses these features: player x-position, nearest obstacle x-position, nearest obstacle y-position, and horizontal distance to that obstacle.

You can also experiment with alternate data or model files:

```bash
python3 train_model.py --data game_data.json --model game_model.pkl --estimators 150
```

### Play the Game with the Model
Once the model is trained, you can run the game with the model controlling the player movements using the `play_with_model.py` script:

```bash
python3 play_with_model.py
```

To try a different model file:

```bash
python3 play_with_model.py --model game_model.pkl
```

### Evaluate the Model

Run headless simulations to compare model performance without opening a game window:

```bash
python3 evaluate_model.py --games 10 --max-frames 3600
```

### Runtime Files

High scores are saved locally in `high_scores.json`. This file is ignored by git because it contains local play history rather than source data.


## Contributing
Contributions to this project are welcome! Please fork the repository and submit a pull request with your improvements.
