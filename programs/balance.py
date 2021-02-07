from mindstorms import MSHub, Motor, MotorPair, ColorSensor, DistanceSensor, App
from mindstorms.control import wait_for_seconds, wait_until, Timer
from mindstorms.operator import greater_than, greater_than_or_equal_to, less_than, less_than_or_equal_to, equal_to, not_equal_to
import math
import time

# First experiments with a balancing robot... no yet finished.
# See https://medium.com/@janislavjankov/self-balancing-robot-with-lego-spike-prime-ac156af5c2b2 for a more
# complete example.

wheel_radius = 2.8

# Create your objects here.
hub = MSHub()

motor_pair = MotorPair('B', 'F')
motor_pair.set_default_speed(50)
motor_pair.set_motor_rotation(wheel_radius * 2 * math.pi, 'cm')

while True:
    r = hub.motion_sensor.get_roll_angle() + 90
    motor_pair.start(speed = - r*40)




