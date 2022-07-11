"""base_controller controller."""

"""
   Description:  Simplistic drone control:
   - Stabilize the robot using the embedded sensors.
   - Use PID technique to stabilize the drone roll/pitch/yaw.
   - Use a cubic function applied on the vertical difference to stabilize the robot vertically.
   - Stabilize the camera.
   - Control the robot using the computer keyboard.
"""
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

# You may need to import some classes of the controller module. Ex:
#  from controller import Robot, Motor, DistanceSensor
from controller import Robot

from controller import Keyboard

SIGN = lambda x : ((x) > 0) - ((x) < 0)
CLAMP = lambda value, low, high :  ((low) if (value) < (low) else ((high) if (value) > (high) else (value)))

class Environment():
  def __init__(self):
    # create the Robot instance.
    self.robot = Robot()

    # kafka API
    self.producer = KafkaProducer(**producer_config)
    self.consumer = KafkaConsumer('webots-mailbox', **consumer_config)

    # get the time step of the current world.
    self.timestep = int(self.robot.getBasicTimeStep())

    # You should insert a getDevice-like function in order to get the
    # instance of a device of the robot. Something like:
    #  motor = robot.getDevice('motorname')
    #  ds = robot.getDevice('dsname')
    #  ds.enable(timestep)
    self.camera = self.robot.getDevice('camera')
    self.camera.enable(self.timestep)
    self.front_left_led = self.robot.getDevice('front left led')
    self.front_right_led = self.robot.getDevice('front right led')
    self.imu = self.robot.getDevice('inertial unit')
    self.imu.enable(self.timestep)
    self.gps = self.robot.getDevice('gps')
    self.gps.enable(self.timestep)
    self.compass = self.robot.getDevice('compass')
    self.compass.enable(self.timestep)
    self.gyro = self.robot.getDevice('gyro')
    self.gyro.enable(self.timestep)
    self.keyboard = Keyboard()
    self.keyboard.enable(self.timestep)
    self.camera_roll_motor = self.robot.getDevice('camera roll')
    self.camera_pitch_motor = self.robot.getDevice('camera pitch')
    # self.camera_yaw_motor = self.robot.getDevice('camera yaw')  // Not used in this example.

    # Get propeller motors and set them to velocity mode.
    self.front_left_motor = self.robot.getDevice('front left propeller')
    self.front_right_motor = self.robot.getDevice('front right propeller')
    self.rear_left_motor = self.robot.getDevice('rear left propeller')
    self.rear_right_motor = self.robot.getDevice('rear right propeller')
    self.motors = [self.front_left_motor, self.front_right_motor, self.rear_left_motor, self.rear_right_motor]
    for m in range(4):
        self.motors[m].setPosition(np.Inf)
        self.motors[m].setVelocity(1.0)

    print('Start the drone...')

    # Variables.
    self.target_altitude = 1.0;  # The target altitude. Can be changed by the user.
    self.started_simulation = False
    self.movement = 'nop'

    self.front_left_motor_input = 0.0
    self.front_right_motor_input = 0.0
    self.rear_left_motor_input = 0.0
    self.rear_right_motor_input = 0.0
  
  def reset(self):
    # Wait one second.
    while self.robot.step(self.timestep) != -1:
        if self.robot.getTime() > 1.0:
            break

    self.target_altitude = 1.0
    self.started_simulation = False
    self.movement = 'nop'

    self.front_left_motor_input = 0.0
    self.front_right_motor_input = 0.0
    self.rear_left_motor_input = 0.0
    self.rear_right_motor_input = 0.0

  def step(self):
    # Main loop:
    # - perform simulation steps until Webots is stopping the controller
    self.robot.step(self.timestep)
    time = self.robot.getTime()

    # Read the sensors:
    # Enter here functions to read sensor data, like:
    #  val = ds.getValue()
    roll = self.imu.getRollPitchYaw()[0]
    pitch = self.imu.getRollPitchYaw()[1]
    altitude = self.gps.getValues()[2]
    roll_acceleration = self.gyro.getValues()[0]
    pitch_acceleration = self.gyro.getValues()[1]

    if (not self.started_simulation) and (altitude >= self.target_altitude):
      self.started_simulation = True
    
    if altitude < 0.05:
      env_json = json.dumps({
          "state": {"ended": True}
        })
      self.producer.send('agents-mailbox', key=b'image', value=b'')
      self.producer.send('agents-mailbox', key=b'data', value=env_json.encode('utf-8'))
      self.producer.flush()
      return

    if self.started_simulation:
      # Calculate reward
      # Every timestep that the ant is alive, it gets a reward of 1
      survive_reward = 1
      # A reward of moving forward which is measured as drone x-coordinate velocity
      forward_reward = pitch * 10
      # A negative reward for penalising the drone if not in the particular altitude which is measured as difference between best altitude and current altitude.
      altitude_cost = np.abs(DESIRED_ALTITUED - altitude)
      # A negative reward for penalising the drone if it takes actions that are too large.
      ctrl_cost = COEFFICIENT *((self.front_left_motor_input  +
                                self.front_right_motor_input +
                                self.rear_left_motor_input   +
                                self.rear_right_motor_input +
                                roll_acceleration
                                )*0.01
                              )
      #TODO A negative reward for penalising the drone if the external contact force occurs.
      contact_cost = 0

      total_reward = survive_reward + forward_reward - (altitude_cost + ctrl_cost + contact_cost)

      # Send data to the model
      img = self.camera.getImage()
      env_json = json.dumps({
          "state": {
            "roll": roll,
            "pitch": pitch,
            "altitude": altitude,
            "roll_acceleration": roll_acceleration,
            "pitch_acceleration": pitch_acceleration,
            "camera_height": self.camera.getHeight(),
            "camera_width": self.camera.getWidth(),
            "ended": False
          },
          "reward": total_reward
        })

      self.producer.send('agents-mailbox', key=b'image', value=img)
      self.producer.send('agents-mailbox', key=b'data', value=env_json.encode('utf-8'))
      self.producer.flush()

      # Get movement from the model
      msg_move = self.consumer.__next__()
      self.movement = msg_move.value.decode('utf-8')
      # print(self.movement)

    # Blink the front LEDs alternatively with a 1 second rate.
    led_state = (int(time)) % 2
    self.front_left_led.set(led_state)
    self.front_right_led.set(not led_state)

    # Stabilize the Camera by actuating the camera motors according to the gyro feedback.
    self.camera_roll_motor.setPosition(-0.115 * roll_acceleration)
    self.camera_pitch_motor.setPosition(-0.1 * pitch_acceleration)

    # Transform the keyboard input to disturbances on the stabilization algorithm.
    roll_disturbance = 0.0
    pitch_disturbance = 0.0
    yaw_disturbance = 0.0
    if self.movement != 'nop':
        if self.movement == 'up':
            pitch_disturbance = -2.0
        elif self.movement == 'down':
          pitch_disturbance = 2.0
        elif self.movement == 'right':
          yaw_disturbance = -1.3
        elif self.movement == 'left':
          yaw_disturbance = 1.3
        elif self.movement == 'shift + right':
          roll_disturbance = -1.0
        elif self.movement == 'shift + left':
          roll_disturbance = 1.0
        elif self.movement == 'shift + up':
          self.target_altitude += 0.05
          # print(f'target altitude: {self.target_altitude} [m]')
        elif self.movement == 'shift + down':
          self.target_altitude -= 0.05
          # print(f'target altitude: {self.target_altitude} [m]')

    # Process sensor data here.
    # Compute the roll, pitch, yaw and vertical inputs.
    roll_input = K_ROLL_P * CLAMP(roll, -1.0, 1.0) + roll_acceleration + roll_disturbance
    pitch_input = K_PITCH_P * CLAMP(pitch, -1.0, 1.0) + pitch_acceleration + pitch_disturbance
    yaw_input = yaw_disturbance
    clamped_difference_altitude = CLAMP(self.target_altitude - altitude + K_VERTICAL_OFFSET, -1.0, 1.0)
    vertical_input = K_VERTICAL_P * pow(clamped_difference_altitude, 3.0)

    # Enter here functions to send actuator commands, like:
    #  motor.setPosition(10.0)
    # Actuate the motors taking into consideration all the computed inputs.
    self.front_left_motor_input = K_VERTICAL_THRUST + vertical_input - roll_input + pitch_input - yaw_input
    self.front_right_motor_input = K_VERTICAL_THRUST + vertical_input + roll_input + pitch_input + yaw_input
    self.rear_left_motor_input = K_VERTICAL_THRUST + vertical_input - roll_input - pitch_input + yaw_input
    self.rear_right_motor_input = K_VERTICAL_THRUST + vertical_input + roll_input - pitch_input - yaw_input
    self.front_left_motor.setVelocity(self.front_left_motor_input)
    self.front_right_motor.setVelocity(-self.front_right_motor_input)
    self.rear_left_motor.setVelocity(-self.rear_left_motor_input)
    self.rear_right_motor.setVelocity(self.rear_right_motor_input)
    return

  def close(self):
    # Enter here exit cleanup code.
    self.robot.__del__()

    self.producer.close()
    self.consumer.close()

env = Environment()
while True:
  env.step()