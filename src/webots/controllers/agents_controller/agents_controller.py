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
sys.path.append('../../../kafka-config/')

import numpy as np
import base64
import json

from kafka import KafkaConsumer, KafkaProducer
from constant import K_ROLL_P, K_PITCH_P, K_VERTICAL_P, K_VERTICAL_THRUST, K_VERTICAL_OFFSET
from consumer_config import webots_config as consumer_config
from producer_config import webots_config as producer_config

# You may need to import some classes of the controller module. Ex:
#  from controller import Robot, Motor, DistanceSensor
from controller import Robot

from controller import Keyboard

SIGN = lambda x : ((x) > 0) - ((x) < 0)
CLAMP = lambda value, low, high :  ((low) if (value) < (low) else ((high) if (value) > (high) else (value)))

# create the Robot instance.
robot = Robot()

# kafka API
producer = KafkaProducer(**producer_config)
consumer = KafkaConsumer('webots-mailbox', **consumer_config)

# get the time step of the current world.
timestep = int(robot.getBasicTimeStep())

# You should insert a getDevice-like function in order to get the
# instance of a device of the robot. Something like:
#  motor = robot.getDevice('motorname')
#  ds = robot.getDevice('dsname')
#  ds.enable(timestep)
camera = robot.getDevice('camera')
camera.enable(timestep)
front_left_led = robot.getDevice('front left led')
front_right_led = robot.getDevice('front right led')
imu = robot.getDevice('inertial unit')
imu.enable(timestep)
gps = robot.getDevice('gps')
gps.enable(timestep)
compass = robot.getDevice('compass')
compass.enable(timestep)
gyro = robot.getDevice('gyro')
gyro.enable(timestep)
keyboard = Keyboard()
keyboard.enable(timestep)
camera_roll_motor = robot.getDevice('camera roll')
camera_pitch_motor = robot.getDevice('camera pitch')
# camera_yaw_motor = robot.getDevice('camera yaw')  // Not used in this example.

# Get propeller motors and set them to velocity mode.
front_left_motor = robot.getDevice('front left propeller')
front_right_motor = robot.getDevice('front right propeller')
rear_left_motor = robot.getDevice('rear left propeller')
rear_right_motor = robot.getDevice('rear right propeller')
motors = [front_left_motor, front_right_motor, rear_left_motor, rear_right_motor]
for m in range(4):
    motors[m].setPosition(np.Inf)
    motors[m].setVelocity(1.0)

print('Start the drone...')

# Wait one second.
while robot.step(timestep) != -1:
    if robot.getTime() > 1.0:
        break

# Variables.
target_altitude = 1.0;  # The target altitude. Can be changed by the user.
started_simulation = False
movement = 'nop'

# Main loop:
# - perform simulation steps until Webots is stopping the controller
while robot.step(timestep) != -1:
    time = robot.getTime()

    # Read the sensors:
    # Enter here functions to read sensor data, like:
    #  val = ds.getValue()
    roll = imu.getRollPitchYaw()[0]
    pitch = imu.getRollPitchYaw()[1]
    altitude = gps.getValues()[2]
    roll_acceleration = gyro.getValues()[0]
    pitch_acceleration = gyro.getValues()[1]

    if (not started_simulation) and (altitude >= target_altitude):
      started_simulation = True
    
    if altitude < 0.05:
      break

    if started_simulation:
      # Send data to the model
      img = camera.getImage()
      state = json.dumps({
          "roll": roll,
          "pitch": pitch,
          "altitude": altitude,
          "roll_acceleration": roll_acceleration,
          "pitch_acceleration": pitch_acceleration,
          "camera_height": camera.getHeight(),
          "camera_width": camera.getWidth(),
          "ended": False
        })

      producer.send('agents-mailbox', key=b'image', value=img)
      producer.send('agents-mailbox', key=b'data', value=state.encode('utf-8'))
      producer.flush()

      # Get movement from the model
      msg_move = consumer.__next__()
      movement = msg_move.value.decode('utf-8')
      # print(movement)

    # Blink the front LEDs alternatively with a 1 second rate.
    led_state = (int(time)) % 2
    front_left_led.set(led_state)
    front_right_led.set(not led_state)

    # Stabilize the Camera by actuating the camera motors according to the gyro feedback.
    camera_roll_motor.setPosition(-0.115 * roll_acceleration)
    camera_pitch_motor.setPosition(-0.1 * pitch_acceleration)

    # Transform the keyboard input to disturbances on the stabilization algorithm.
    roll_disturbance = 0.0
    pitch_disturbance = 0.0
    yaw_disturbance = 0.0
    if movement != 'nop':
        if movement == 'up':
            pitch_disturbance = -2.0
        elif movement == 'down':
          pitch_disturbance = 2.0
        elif movement == 'right':
          yaw_disturbance = -1.3
        elif movement == 'left':
          yaw_disturbance = 1.3
        elif movement == 'shift + right':
          roll_disturbance = -1.0
        elif movement == 'shift + left':
          roll_disturbance = 1.0
        elif movement == 'shift + up':
          target_altitude += 0.05
          # print(f'target altitude: {target_altitude} [m]')
        elif movement == 'shift + down':
          target_altitude -= 0.05
          # print(f'target altitude: {target_altitude} [m]')

    # Process sensor data here.
    # Compute the roll, pitch, yaw and vertical inputs.
    roll_input = K_ROLL_P * CLAMP(roll, -1.0, 1.0) + roll_acceleration + roll_disturbance
    pitch_input = K_PITCH_P * CLAMP(pitch, -1.0, 1.0) + pitch_acceleration + pitch_disturbance
    yaw_input = yaw_disturbance
    clamped_difference_altitude = CLAMP(target_altitude - altitude + K_VERTICAL_OFFSET, -1.0, 1.0)
    vertical_input = K_VERTICAL_P * pow(clamped_difference_altitude, 3.0)

    # Enter here functions to send actuator commands, like:
    #  motor.setPosition(10.0)
    # Actuate the motors taking into consideration all the computed inputs.
    front_left_motor_input = K_VERTICAL_THRUST + vertical_input - roll_input + pitch_input - yaw_input
    front_right_motor_input = K_VERTICAL_THRUST + vertical_input + roll_input + pitch_input + yaw_input
    rear_left_motor_input = K_VERTICAL_THRUST + vertical_input - roll_input - pitch_input + yaw_input
    rear_right_motor_input = K_VERTICAL_THRUST + vertical_input + roll_input - pitch_input - yaw_input
    front_left_motor.setVelocity(front_left_motor_input)
    front_right_motor.setVelocity(-front_right_motor_input)
    rear_left_motor.setVelocity(-rear_left_motor_input)
    rear_right_motor.setVelocity(rear_right_motor_input)
    pass


state = json.dumps({
    "ended": True
  })
producer.send('agents-mailbox', key=b'image', value=b'')
producer.send('agents-mailbox', key=b'data', value=state.encode('utf-8'))
producer.flush()

# Enter here exit cleanup code.
robot.__del__()

producer.close()
consumer.close()