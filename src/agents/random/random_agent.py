import sys
sys.path.append('../../kafka-config')

import random
import numpy as np
import base64
import json
import cv2

from PIL import Image
from kafka import KafkaConsumer, KafkaProducer
from consumer_config import agents_config as consumer_config
from producer_config import agents_config as producer_config


class RandomAgent():
    def __init__(self):
        self.producer = KafkaProducer(**producer_config)
        self.consumer = KafkaConsumer('agents-mailbox', **consumer_config)

    def policy(self):
        # msg_img = self.consumer.__next__()
        msg_json = self.consumer.__next__()
        # if msg_img.key.decode() != 'image':
        #     msg_img = msg_json
        env_json = json.loads(msg_json.value.decode('utf-8'))

        if env_json['done']:
            self.__del__()
            return

        movements = ['nop', 'up', 'down', 'right', 'left', 'shift + up', 'shift + down', 'shift + right', 'shift + left']
        movement = random.choice(movements)

        self.producer.send('trainer-mailbox', key=b'movement', value=movement.encode('utf-8'))
        self.producer.flush()
    
    def __del__(self):
        self.producer.close()
        self.consumer.close()

agent = RandomAgent()
while True:
    agent.policy()