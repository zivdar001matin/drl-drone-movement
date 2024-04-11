import sys
sys.path.append('../../')
sys.path.append('../../kafka-config')

import numpy as np
import base64
import json

from kafka import KafkaConsumer, KafkaProducer
from consumer_config import agents_config as consumer_config
from producer_config import agents_config as producer_config

consumer = KafkaConsumer('agents-mailbox', **consumer_config)

for message in consumer:
    print(message.key)