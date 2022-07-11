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

producer = KafkaProducer(**producer_config)
consumer = KafkaConsumer('agents-mailbox', **consumer_config)


while(True):
# for msg in consumer:
    msg_img = consumer.__next__()
    msg_json = consumer.__next__()
    if msg_img.key.decode() != 'image':
        msg_img = msg_json
    state_json = json.loads(msg_json.value.decode('utf-8-sig'))

    if state_json['ended']:
        break

    # convert image bytes data to numpy array of dtype uint8
    nparr = np.frombuffer(msg_img.value, np.uint8).reshape((state_json['camera_height'], state_json['camera_width'], 4), order='A')
    # convert BGRa -> RGB
    nparr = nparr[:, :, :3][:, :, ::-1]
    # img = Image.fromarray(nparr, 'RGB')
    # img.save('camera.png')
    # cv2.imshow('image', img)
    # cv2.waitKey(0)

    movements = ['nop', 'up', 'down', 'right', 'left', 'shift + up', 'shift + down', 'shift + right', 'shift + left']
    movement = random.choice(movements)

    producer.send('webots-mailbox', key=b'movement', value=movement.encode('utf-8'))
    producer.flush()

producer.close()
consumer.close()