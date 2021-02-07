#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
import base64
import json
import os
import socket
import sys
import traceback
from time import sleep

import bluetooth
import serial

from ansi import esc, color
import select

# for testing you can use a PTY:
# > socat -d -d pty,raw,echo=0 pty,raw,echo=0


class LineReader:
    def __init__(self, name):
        print(f"Creating {name}{esc:K}")
        self.buffer = bytes()
        self.name = name

    def data_ready(self):
        # appending incoming data
        data = self.read()
        self.buffer += data

        # extract all complete lines in buffer
        while len(self.buffer) > 0:
            pos_ln = self.buffer.find(b'\n')
            pos_cr = self.buffer.find(b'\r')
            if pos_ln == -1 and pos_cr == -1:
                return
            if pos_ln == -1 or pos_cr != -1 and pos_cr < pos_ln:
                pos = pos_cr
            else:
                pos = pos_ln

            # combine all subsequent line terminators
            size = 1
            while pos + size < len(self.buffer) and self.buffer[pos + size] in b'\n\r':
                size += 1

            # take out line and line terminators
            line = self.buffer[:pos]
            line_terminators = self.buffer[pos:pos + size]
            self.buffer = self.buffer[pos + size:]

            # forward extracted line
            self.read_line(line, line_terminators)

    def write_line(self, line, line_terminators):
        self.write(line + line_terminators)

    def __str__(self):
        return self.name

    def close(self):
        print(f"Closing {self}{esc:K}")


class HubConnection(LineReader):
    def __init__(self, clients, log, name):
        super().__init__(name)
        self.clients = clients
        self.log = log
        self.charging = False
        self.charged = 0

    def read(self):
        pass

    def write(self, data):
        pass

    def close(self):
        pass

    def read_line(self, line, line_terminators):
        self.log.input(line)
        self.parse_line(line.decode('utf-8', 'ignore'))
        closed_clients = []
        for client in self.clients:
            try:
                client.write_line(line, line_terminators)
            except:
                closed_clients.append(client)
                client.close()
        for client in closed_clients:
            self.clients.remove(client)

    def parse_line(self, line):
        try:
            message = json.loads(line)
            if 'i' in message and 'm' in message and 'p' in message:
                self.handle_request(message)
            elif 'i' not in message and 'm' in message and 'p' in message:
                self.handle_notification(message)
            elif 'i' in message and 'r' in message:
                self.handle_response(message)
            elif 'e' in message and 'i' in message:
                self.handle_error(message)
            elif 'i' in message and 'm' in message and 'p' in message:
                self.handle_user_program_print(message)
            else:
                self.print(line, f"{color:34}UNKOWN:")
        except json.JSONDecodeError:
            self.print(line, f"{color:31}JSON ERROR:", wrap=True)
        except Exception as e:
            traceback.print_exc()
            self.print(f"{color:2}{e}{color:0}: {line}", f"{color:31}FAILED:")

    def decode_base64(self, value):
        return base64.b64decode(value).decode('utf-8', 'ignore')

    def handle_request(self, message):
        i = message['i']
        m = message['m']
        p = message['p']
        self.print(f"{m}: {json.dumps(p)}", f"{color:33}REQUEST:", id=i)

    def handle_response(self, message):
        i = message['i']
        r = message['r']
        self.print(r, f"{color:33}RESPONSE:", id=i)

    def handle_user_program_print(self, message):
        i = message['i']
        m = message['m']
        p = message['p']
        if m != 'userProgram.print':
            raise AssertionError(f"m={m} but expected to be userProgram.print")
        self.print(self.decode_base64(p['value']), "{color:32}OUTPUT:", id=i, wrap=True)

    def handle_error(self, message):
        i = message['i']
        e = message['e']
        self.print(self.decode_base64(e), f'{color:31}ERROR:', id=i, wrap=True)

    def handle_notification(self, message):
        m = message['m']
        p = message['p']
        if m == 0:
            self.handle_sensor_notification(p[0:6], p[6], p[7], p[8], p[9], p[10])
        elif m == 1:
            self.handle_storage_notification(p)
        elif m == 2:
            self.handle_battery_notification(*p)
        elif m == 3:
            self.handle_button_notification(*p)
        elif m == 4:
            self.handle_gesture_notification(p)
        elif m == 5:
            self.handle_display_notification(p)
        elif m == 6:
            self.handle_firmware_notification(p)
        # 7 stack start
        # 8 stack top
        # 9 info status
        # 10 error
        # 11 vm state
        elif m == 12:
            self.handle_program_notification(p)
        # 13 linegraph timer reset
        # 14 orientation status
        elif m == 'runtime_error':
            self.handle_runtime_error(p)
        else:
            self.handle_unknown_notification(m, p)

    def handle_sensor_notification(self, ports, accelerometer, gyroscope, position, display, time):
        buf = f"{color:1} "
        for i in range(6):
            gadget = ports[i][0]
            buf += "ABCDEF"[i] + ":"
            if gadget == 0:  # Not connected
                buf += "-"
            # Stone gray motor medium [Speed, Diff, Pos, ?]
            elif gadget == 75:
                if len(ports[i][1]) == 4:
                    buf += f"{ports[i][1][2]:4}°{ports[i][1][0]:3}%"
                else:
                    buf += "?"
            elif gadget == 61:  # Color sensor
                # none: 255, red: 9, blue: 3, green: 5, yellow: 7: white: 10, black 0
                buf += f"C{ports[i][1][0]}"
            elif gadget == 62:  # Distance sensor
                buf += f"{ports[i][1][0]:3}cm " if ports[i][1][0] else "  cm "
            else:
                buf += f"{ports[i][1]}"
            buf += f"{color:0;2}| {color:0;1}"

        buf += f"a=({accelerometer[0]:5}{accelerometer[1]:5}{accelerometer[2]:5}) "
        buf += f"v=({gyroscope[0]:5}{gyroscope[1]:5}{gyroscope[2]:5}) "
        buf += f"p=({position[0]:5}{position[1]:5}{position[2]:5}) "
        buf += f"Bat:{self.charged:3}%{color:0;2}| {color:0;1}"
        buf += f"Display:{display}{color:0;2}| {color:0;1}"
        buf += f"Time:{time}"
        self.print(buf, end="\r")

    def handle_storage_notification(self, p):
        self.print(p, f"{color:34}STORAGE:")

    def handle_battery_notification(self, voltage, charge, charging):
        self.charged = charge
        # 0: not charging, 1: charging, 2: unknown
        self.charging = charging

    def handle_button_notification(self, button, duration):
        self.print(f"Button pressed: {button} {duration:4}", f"{color:34}INFO:")

    def handle_gesture_notification(self, action):
        self.print(f"Interaction: {action}", f"{color:34}INFO:")

    def handle_display_notification(self, p):
        self.print(p, f"{color:34}DISPLAY:")

    def handle_firmware_notification(self, p):
        self.print(p, f"{color:34}FIRMWARE:")

    def handle_program_notification(self, p):
        self.print(p, f"{color:34}PROGRAM:")

    def handle_runtime_error(self, p):
        def tryDecode(value):
            try:
                return self.decode_base64(value)
            except:
                return value
        p = list(map(tryDecode, p))
        self.print(p, f"{color:31}RUNTIME:", wrap=True)

    def handle_unknown_notification(self, m, p):
        self.print(p, f"{color:2}{m}")

    def print(self, data, prefix=None, wrap=False, end="\n", id=None):
        if not isinstance(data, str):
            data = json.dumps(data)
        if not wrap:
            data = f"{esc:?7l}{data}{esc:?7h}"
        if id:
            data = f"{color:2}{id}{color:0} {data}"
        if prefix:
            data = f"{prefix:17}{color:0}{data}"
        data = f"{data}{esc:K}{color:0}{end}"
        sys.stdout.write(data)


class SerialHubConnection(HubConnection):
    def __init__(self, port, clients, log):
        super().__init__(clients, log, f"SerialHubConnection ({port})")
        self.port = serial.Serial(port)

    def read(self):
        return self.port.read(1024)

    def write(self, data):
        self.port.write(data)

    def close(self):
        self.port.close()

    def fileno(self):
        return self.port.fileno()

    def __str__(self):
        return self.port.name


class BluetoothHubConnection(HubConnection):
    def __init__(self, device, clients, log):
        super().__init__(clients, log, f"BluetoothClientConnection ({device})")
        self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.socket.connect((device, 1))

    def read(self):
        return self.socket.recv(1024)

    def write(self, data):
        self.socket.sendall(data)

    def close(self):
        self.socket.close()

    def fileno(self):
        return self.socket.fileno()

    def __str__(self):
        return self.socket.getpeername()


class FileHubConnection(HubConnection):
    def __init__(self, path, clients, log):
        super().__init__(clients, log, f"FileHubConnection ({path})")
        self.file = open(path, 'rb')

    def read(self):
        data = b''
        while not data.startswith(b'< '):
            data = self.file.readline(1024*1024)
            if len(data) < 1:
                print("\nEOF")
                os._exit(1)
        data = data[2:]
        data = data.replace(b'\n', b'\r')
        sleep(0.001)
        return data

    def write(self, data):
        pass

    def close(self):
        pass

    def fileno(self):
        return self.file.fileno()

    def __str__(self):
        return self.file.name


class ClientConnection(LineReader):
    def __init__(self, clients, hub, name, log):
        super().__init__(name)
        self.clients = clients
        self.hub = hub
        self.name = name
        self.log = log
        self.clients.append(self)

    def run(self):
        line = bytearray()
        try:
            while True:
                data = self.read()
                if not data:
                    break
                if data == b'\r':
                    self.log.output(line)
                    print(f"{color:33}REQUEST:{color:0} ", line.decode('utf-8', 'ignore'), end=f"{esc:K}\n")
                    line.clear()
                else:
                    line += data
                self.hub.write(data)
        finally:
            self.clients.remove(self)
            self.close()

    def read_line(self, line, line_terminators):
        print(f"{color:33}REQUEST:{color:0} ", line.decode('utf-8', 'ignore'), end=f"{esc:K}\n")
        self.log.output(line)
        self.hub.write_line(line, line_terminators)

    def read(self):
        pass

    def write(self, data):
        pass


class SocketClientConnection(ClientConnection):
    def __init__(self, client_socket, clients, hub, log):
        super().__init__(clients, hub, f"SocketClientConnection {client_socket.getpeername()}", log)
        self.client_socket = client_socket

    def read(self):
        return self.client_socket.recv(1024)

    def write(self, data):
        self.client_socket.sendall(data)

    def fileno(self):
        return self.client_socket.fileno()

    def close(self):
        super().close()
        self.client_socket.close()


class BluetoothClientConnection(SocketClientConnection):
    def __init__(self, clients, hub, log):
        self.server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.server_socket.bind(('', bluetooth.PORT_ANY))
        self.server_socket.listen(1)

        uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

        bluetooth.advertise_service(self.server_socket, "SampleServer", service_id=uuid, service_classes=[
                                    uuid, bluetooth.SERIAL_PORT_CLASS], profiles=[bluetooth.SERIAL_PORT_PROFILE])

        print("Waiting for connection on RFCOMM channel 1")

        client_socket, client_info = self.server_socket.accept()
        print("Accepted connection from", client_info)

        super().__init__(client_socket, clients, hub, log)

    def close(self):
        super().close()
        self.server_socket.close()

    def write(self,data):
        super().write(data)


class NoopLogger:
    def __init__(self):
        print("No Logging")

    def output(self, line):
        pass

    def input(self, line):
        pass


class FileLogger:
    def __init__(self, path):
        print(f"Logging to {path}")
        self.file = open(path, mode='wb', buffering=0)

    def output(self, line):
        self.file.write(b'> ' + line + b'\n')

    def input(self, line):
        self.file.write(b'< ' + line + b'\n')


class ServerSocket:
    def __init__(self, port, clients, hub, log):
        print(f"Listing on port localhost:{port}")
        self.server_socket = socket.create_server(('localhost', port))
        self.clients = clients
        self.hub = hub
        self.log = log

    def fileno(self):
        return self.server_socket.fileno()

    def data_ready(self):
        client_socket, client_address = self.server_socket.accept()
        client = SocketClientConnection(client_socket, self.clients, self.hub, self.log)

    def close(self):
        self.server_socket.close()


def start():
    parser = argparse.ArgumentParser(
        description="Tool for Monitoring Lego Mindstorms Roboter Inventor Hub and multiplexing connections.")
    parser.add_argument("--debug", help="Enable debug", action="store_true")
    parser.add_argument("-p", "--port", help="port to listen on localhost for replication (default: 8888)",
                        metavar="<port>", default=8888, type=int)
    parser.add_argument("-b", "--bluetooth", help="start blueooth server", action="store_true")

    log_group = parser.add_mutually_exclusive_group()
    log_group.add_argument("-l", "--log", help="log file (default: trace-Ymd-HMS.log", metavar="<path>")
    log_group.add_argument("-n", "--nolog", help="don't create log file", action="store_true")

    device_group = parser.add_mutually_exclusive_group(required=True)
    device_group.add_argument("-t", "--tty", help="device path", metavar="<path>")
    device_group.add_argument("-d", "--device", help="bluetooth device address", metavar="<bdaddr>")
    device_group.add_argument("-f", "--file", help="test data file", metavar="<path>")

    args = parser.parse_args()

    clients = []

    if args.nolog:
        log = NoopLogger()
    else:
        log = FileLogger(args.log)

    if args.tty:
        hub = SerialHubConnection(args.tty, clients, log)
    elif args.device:
        hub = BluetoothHubConnection(args.device, clients, log)
    elif args.file:
        hub = FileHubConnection(args.file, clients, log)

    if args.bluetooth:
        bluetooth_client = BluetoothClientConnection(clients, hub, log)

    server = ServerSocket(args.port, clients, hub, log)

    inputs = [server]

    try:
        while True:
            ready_inputs, _, _ = select.select(clients + [hub, server], [], [])
            for input in ready_inputs:
                input.data_ready()
    finally:
        for input in clients + [hub, server]:
            input.close()


if __name__ == "__main__":
    start()
