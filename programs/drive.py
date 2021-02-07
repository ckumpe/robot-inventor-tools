from mindstorms import MSHub, Motor, MotorPair, ColorSensor, DistanceSensor, App
from mindstorms.control import wait_for_seconds, wait_until, Timer
from mindstorms.operator import greater_than, greater_than_or_equal_to, less_than, less_than_or_equal_to, equal_to, not_equal_to
import math

# driving with Tricky

wheel_radius = 2.8
pen_radius = 8.6
axis_radius = 5.6

line_length = 5

# Create your objects here.
hub = MSHub()


# Write your program here.
hub.speaker.beep()

motor = Motor('C')
motor.run_to_position(165)


def pen_up():
    motor.run_for_degrees(-90)


def pen_down():
    motor.run_for_degrees(90)


motor_pair = MotorPair('B', 'A')
motor_pair.set_default_speed(20)
motor_pair.set_motor_rotation(wheel_radius * 2 * math.pi, 'cm')

pen_down()

motor_pair.move_tank(axis_radius*math.pi * 2.05, 'cm',
                    left_speed=-25, right_speed=25)

#pen_up()
#pen_down()

motor_pair.move(-pen_radius * 2, 'cm')
pen_up()

motor_pair.move(pen_radius * 2, 'cm')

motor_pair.move_tank(axis_radius*math.pi * - 0.5, 'cm',
                    left_speed=-25, right_speed=25)

pen_down()
motor_pair.move(-pen_radius * 2, 'cm')

pen_up()

hub.speaker.beep()
hub.light_matrix.write('done')
