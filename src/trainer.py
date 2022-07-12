import sys
sys.path.append('./kafka-config/')

import numpy as np
import json
import cv2

from kafka import KafkaConsumer, KafkaProducer
from consumer_config import trainer_config as consumer_config
from producer_config import trainer_to_agents_config, trainer_to_webots_config

from replay_buffer import ReplayBuffer

class Trainer():
  def __init__(self):
    self.consumer = KafkaConsumer('trainer-mailbox', **consumer_config)
    self.to_agents_producer = KafkaProducer(**trainer_to_agents_config)
    self.buffer = ReplayBuffer()

  def collect_gameplay_experience(self):
    """
    The collect_gameplay_experience function does the simulation "env" with the
    instructions produced by "agent" and stores the simulation experiences
    into "buffer" for later training.
    """
    #TODO reset env
    _, env_json = self.get_state_from_env()
    state = env_json['state']     #TODO change state from json to np.array

    done = False
    while not done:
      # action = agent.policy(state)
      action = self.get_action_from_agent_policy(json.dumps(env_json))
      self.send_action_to_env(action)   #TODO change action type from string to int
      # next_state, reward, done = env.step(action)
      _, env_json = self.get_state_from_env()
      next_state = env_json['state']
      reward = env_json['reward']
      done = env_json['done']
      # store gameplay experience
      self.buffer.store_gameplay_experience(state, next_state, reward, action, done)
      state = next_state
    
  def get_state_from_env(self):
    msg_img = self.consumer.__next__()
    msg_json = self.consumer.__next__()
    if msg_img.key.decode() != 'image':
      # swap
      msg_img = msg_json
    # convert binary encoded json to python dictionary
    env_json = json.loads(msg_json.value.decode('utf-8'))
    # convert image bytes data to numpy array of dtype uint8
    nparr = np.frombuffer(msg_img.value, np.uint8).reshape((env_json['info']['camera_height'], env_json['info']['camera_width'], 4), order='A')
    # convert BGRa -> RGB
    nparr = nparr[:, :, :3][:, :, ::-1]
    # img = Image.fromarray(nparr, 'RGB')
    # img.save('camera.png')
    # cv2.imshow('image', img)
    # cv2.waitKey(0)
    return nparr, env_json
  
  def send_action_to_env(self, action):
    self.to_webots_producer.send('webots-mailbox', key=b'movement', value=action.encode('utf-8'))
    self.to_webots_producer.flush()

  def get_action_from_agent_policy(self, env_json):
    self.to_agents_producer.send('agents-mailbox', key=b'data', value=env_json.encode('utf-8'))
    self.to_agents_producer.flush()
    # Get action from the model
    msg_action = self.consumer.__next__()
    return msg_action.value.decode('utf-8')

trainer = Trainer()
trainer.collect_gameplay_experience()