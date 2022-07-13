import sys
sys.path.append('../../')
sys.path.append('../../kafka-config')

import numpy as np
import json
import cv2

from PIL import Image
from kafka import KafkaConsumer, KafkaProducer
from config import ACTIONS
from consumer_config import agents_config as consumer_config
from producer_config import agents_config as producer_config


class RandomAgent():
    def __init__(self):
        self.producer = KafkaProducer(**producer_config)
        self.consumer = KafkaConsumer('agents-mailbox', **consumer_config)

    def policy(self):
        # msg_img = self.consumer.__next__()
        print('4-get-data')
        msg_json = self.consumer.__next__()
        # if msg_img.key.decode() != 'image':
        #     msg_img = msg_json
        env_json = json.loads(msg_json.value.decode('utf-8'))

        # if env_json['done']:
        #     self.__del__()
        #     return

        movement = np.random.randint(len(ACTIONS), size=1)[0]

        self.producer.send('trainer-mailbox', key=b'movement', value=str(movement).encode('utf-8'))
        self.producer.flush()
        print(f'5-send-{movement}')
    
    def __del__(self):
        self.producer.close()
        self.consumer.close()

agent = RandomAgent()
while True:
    agent.policy()