import sys
sys.path.append('../')
sys.path.append('../../../')
sys.path.append('../../../kafka-config/')

import numpy as np
import base64
import json

from kafka import KafkaConsumer, KafkaProducer
from config import DESIRED_ALTITUED, COEFFICIENT
from constant import K_ROLL_P, K_PITCH_P, K_VERTICAL_P, K_VERTICAL_THRUST, K_VERTICAL_OFFSET
from consumer_config import webots_config as consumer_config
from producer_config import webots_config as producer_config

consumer = KafkaConsumer('webots-mailbox', **consumer_config)

for message in consumer:
    print(message.key)