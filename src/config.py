from dotenv import load_dotenv
import sys

sys.path.append("..") # Adds higher directory to python modules path.
load_dotenv()

# Rewarding constants
DESIRED_ALTITUED = 1.0
COEFFICIENT = 0.5

# Action constants
ACTIONS = {
    0: 'nop',
    1: 'up',
    2: 'down',
    3: 'right',
    4: 'left',
    5: 'shift + up',
    6: 'shift + down',
    7: 'shift + right',
    8: 'shift + left'
}

# RL hypyer-parameters
E_GREEDY = 0.9

BATCH_SIZE = 2
MEMORY_SIZE = 10000
INPUT_SIZE = 5  # state_size
OUTPUT_SIZE = len(ACTIONS)  # action_space_size
GAMMA = 0.99
LEARNING_RATE = 1e-3
LOSS = 'mse'

EPISODES = 6000