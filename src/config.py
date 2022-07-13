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
