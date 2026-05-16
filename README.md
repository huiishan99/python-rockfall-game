# Rockfall Game with Machine Learning
![屏幕截图 2024-04-24 141624](https://github.com/huiishan99/Python_Rockfall/assets/61934115/80c177e3-445b-4448-94b2-3b34a3a2ea08)


## Description
This project integrates a machine learning model into a simple pygame-based game, where the player's movements are controlled by the model's predictions based on the position of obstacles. The project includes scripts for collecting gameplay data, training a model on this data, and running the game with the trained model.

## Development Log

Every meaningful change should be recorded in [DEVLOG.md](DEVLOG.md). Add entries newest first and include what changed, why it changed, how it was verified, and any risks or follow-up notes. This is especially important when changing gameplay rules, collected data, or the trained model.

## Installation

### Prerequisites
To run this project, you'll need Python and several libraries installed, including pygame, numpy, scikit-learn, and joblib. You can install these dependencies via pip:

```pip install pygame numpy scikit-learn joblib```

### Clone the Repository
To get started with this project, clone this repository to your local machine:

```git clone https://github.com/yourusername/rockfall-ml.git```  
```cd rockfall-ml```

## Usage

### Data Collection
To collect data for training the machine learning model, run the `game.py` script. This will start the game, and player movements along with the obstacle positions will be recorded:

```python game.py```

### Train the Model
After collecting enough data, you can train the machine learning model using the `train_model.py` script. This will process the collected data and save a trained model to the disk:

```python train_model.py```

### Play the Game with the Model
Once the model is trained, you can run the game with the model controlling the player movements using the `play_with_model.py` script:

```python play_with_model.py```


## Contributing
Contributions to this project are welcome! Please fork the repository and submit a pull request with your improvements.






