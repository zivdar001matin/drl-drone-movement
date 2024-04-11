import sys
sys.path.append('./kafka-config/')

import numpy as np
import json
import cv2

from kafka import KafkaConsumer, KafkaProducer
from consumer_config import trainer_config as consumer_config
from producer_config import trainer_to_agents_config, trainer_to_webots_config

consumer = KafkaConsumer('trainer-mailbox', **consumer_config)

counter = 0
for msg in consumer:
    print(counter)
    counter += 1
    print(msg.key)