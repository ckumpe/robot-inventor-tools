from mindstorms import MSHub, LightMatrix, Button, StatusLight, ForceSensor, MotionSensor, Speaker, ColorSensor, App, DistanceSensor, Motor, MotorPair
from mindstorms.control import wait_for_seconds, wait_until, Timer
import time

motor_ports = ["B", "F"]
SET_POINT = -90.0
KP, KI, KD = 10, 120, 0.1
STOP_ANGLE = 20
DT = 0.02

assert len(motor_ports) == 2

hub = MSHub()
motors = MotorPair(*motor_ports)


class PID(object):
    def __init__(self, KP, KI, KD, max_integral: float = 100):
        self._KP = KP
        self._KI = KI
        self._KD = KD

        self._integral = 0.0
        self._max_integral = max_integral if KI == 0.0 else max_integral / KI
        self._start_time = self._now_ms()
        self._prev_error = None
        self._prev_response = None

    def act(self, set_point: float, state: float, dt: float = None):
        """
        :param set_point:
        :param state:
        :param dt: time since last interaction in seconds
        :return:
        """
        current_time = self._now_ms()
        if dt is None:
            dt = time.ticks_diff(current_time, self._start_time) / 1000
        if dt == 0 and self._prev_response is not None:
            return self._prev_response
        error = set_point - state
        if self._prev_error is None:
            self._prev_error = error
        self._integral += error * dt
        if self._max_integral and (abs(self._integral) > self._max_integral):
            self._integral = self._max_integral if self._integral > 0 else -self._max_integral
        d_error = (error - self._prev_error) / dt if dt > 0 else 0.0
        self._prev_error = error

        response = self._KP * error + self._KI * self._integral + self._KD * d_error
        self._prev_response = response
        self._start_time = current_time
        return response

    def _now_ms(self):
        return time.ticks_ms()


def balance(angle: float, pid: PID, dt):
    global motors, hub, STOP_ANGLE
    while True:
        state = hub.motion_sensor.get_roll_angle()
        if abs(state-SET_POINT) >= STOP_ANGLE:
            motors.stop()
            hub.speaker.beep()
            break
        response = pid.act(angle, state)
        motors.start_at_power(int(round(response)))
        wait_for_seconds(dt)


hub.light_matrix.show_image('YES')
wait_for_seconds(0.2)
pid = PID(KP=KP, KI=KI, KD=KD)
balance(SET_POINT, pid=pid, dt=DT)
hub.light_matrix.show_image('NO')
