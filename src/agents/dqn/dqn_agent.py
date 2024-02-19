import sys
sys.path.append('../../')
sys.path.append('../../kafka-config')

import numpy as np
import json
import tensorflow as tf
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Dense

from kafka import KafkaConsumer, KafkaProducer
from config import ACTIONS
from config import E_GREEDY, LEARNING_RATE, LOSS, INPUT_SIZE, OUTPUT_SIZE
from consumer_config import agents_config as consumer_config
from producer_config import agents_config as producer_config

class DqnAgent:
  def __init__(self):
    print(consumer_config)
    self.producer = KafkaProducer(**producer_config)
    self.consumer = KafkaConsumer('agents-mailbox', **consumer_config)

    self.q_net = self._build_dqn_model()
    self.target_q_net = self._build_dqn_model()
    self.checkpoint = tf.train.Checkpoint(step=tf.Variable(0), net=self.q_net)
    self.checkpoint_manager = tf.train.CheckpointManager(self.checkpoint, 'checkpoints', max_to_keep=10)
    self.load_checkpoint()
  
  def run(self):
    while True:
      msg = self.consumer.__next__()
      command = msg.key.decode()
      print(f'2-get-{command}')
      if command == 'policy':
        # msg_json = self.consumer.__next__()
        env_json = json.loads(msg.value.decode('utf-8'))
        state = np.array(list(env_json['state'].values()))
        movement = self.collect_policy(state)
        self.producer.send('trainer-mailbox', key=b'movement', value=str(movement).encode('utf-8'))
        self.producer.flush()
        print(f'5-send-{ACTIONS[movement]}')
      elif command == 'train':
        pass
      else:
        continue
        # raise RuntimeError()


  def collect_policy(self, state):
    if np.random.random() > E_GREEDY:
      return np.random.randint(len(ACTIONS), size=1)[0]
    return self.policy(state)

  """
  DQN Agent: the agent that explores the game and
  should eventually learn how to play the game.
  """
  def policy(self, state):
    """
    Takes a state from the game environment and returns
    a action that should be taken given the current game
    environment.
    """
    state_input = tf.convert_to_tensor(state[None, :], dtype=tf.float32)
    action_q = self.q_net(state_input)
    action = np.argmax(action_q.numpy()[0], axis=0)
    return action

  def train(self, batch):
    """
    Takes a batch of gameplay experiences from replay
    buffer and train the underlying model with the batch
    """
    state_batch, next_state_batch, action_batch, reward_batch, done_batch = batch
    current_q = self.q_net(state_batch)
    target_q = np.copy(current_q)
    next_q = self.target_q_net(next_state_batch)
    max_next_q = np.amax(next_q, axis=1)
    for i in range(state_batch.shape[0]):
      target_q[i][action_batch[i]] = reward_batch[i] if done_batch[i] else reward_batch[i] + 0.95 * max_next_q[i]
    result = self.q_net.fit(x=state_batch, y=target_q)
    return result.history['loss']

  @staticmethod
  def _build_dqn_model():
    """
    Builds a deep neural net which predicts the Q values for all possible
    actions given a state. The input should have the shape of the state
    (which is 4 in CartPole), and the output should have the same shape as
    the action space (which is 2 in CartPole) since we want 1 Q value per
    possible action.
    
    :return: the Q network
    """
    q_net = Sequential()
    q_net.add(Dense(64, input_dim=INPUT_SIZE, activation='relu', kernel_initializer='he_uniform'))
    q_net.add(Dense(32, activation='relu', kernel_initializer='he_uniform'))
    q_net.add(Dense(OUTPUT_SIZE, activation='linear', kernel_initializer='he_uniform'))
    q_net.compile(optimizer=tf.optimizers.Adam(learning_rate=LEARNING_RATE), loss=LOSS)
    return q_net
  
  def update_target_network():
    pass
  
  def save_checkpoint(self):
    self.checkpoint_manager.save()

  def load_checkpoint(self):
    self.checkpoint.restore(self.checkpoint_manager.latest_checkpoint)
  
  def save_model(self):
    tf.saved_model.save(self.q_net, self.model_location)
  
  def load_model(self):
    self.q_net = tf.saved_model.load(self.model_location)

agent = DqnAgent()
agent.run()