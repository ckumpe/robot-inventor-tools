# Tools for the LEGO® MINDSTORMS® Robot Inventor (51515)

This repo contains some tools and experiments with the LEGO® MINDSTORMS® Robot Inventor (51515) and its Hub.

Im using Linux (Ubuntu 20.04) on my system but hopefully the Python scripts should work on Mac an Windows, too.
Feel free to share your experience with diffrent plattforms.

This project is in a very early state of development, is not well tested and will probably will contain many bugs.

# The Tools

## The Gateway Tool

This tool is meant to maintain and monitor the connection to the Lego Hub. It currently has the following features:
* Connect the Lego Hub via
  * Bluetooth e.g. `-d AA:BB:CC:DD:EE:FF`
  * Serial Port (over USB) e.g. `-t /dev/ttyACM0`
  * Listen on `localhost` for clients to connect for forwarding the connection e.g. `-p 8888`
  * Listen as Bluetooth server to connect the "real" Robot Inventor App and sniff the communication (see below for more information)
* Write all communication to a trace log file.
* Simulate a Hub by reading data from a file. Mainly for developing and testen the Gateway itself.

```
tools$ ./gateway.py --help
usage: gateway.py [-h] [--debug] [-p <port>] [-b] [-l <path> | -n] (-t <path> | -d <bdaddr> | -f <path>)

Tool for Monitoring Lego Mindstorms Roboter Inventor Hub and multiplexing connections.

optional arguments:
  -h, --help            show this help message and exit
  --debug               Enable debug
  -p <port>, --port <port>
                        port to listen on localhost for replication (default: 8888)
  -b, --bluetooth       start blueooth server
  -l <path>, --log <path>
                        log file (default: trace-Ymd-HMS.log
  -n, --nolog           don't create log file
  -t <path>, --tty <path>
                        device path
  -d <bdaddr>, --device <bdaddr>
                        bluetooth device address
  -f <path>, --file <path>
                        test data file
```

## Sniff the communication from the Robot Inventor App with the Hub

At first you should pair your computer with the real Hub:
```
toosl$ bluetoothctl
...
# scan on
...
# pair AA:BB:CC:DD:EE:FF
...
# trust AA:BB:CC:DD:EE:FF
...
```

To find your computer as a Hub in the Robot Inventor App your system's name in Bluetooth has to start with `LEGO Hub` (its case sensitive). You can set a name like this:
```
tools$ bluetoothctl system-alias "LEGO Hub@gateway"
```

Start the Gateway with Bluetooth server enabled, where `AA:BB:CC:DD:EE:FF` is the Bluetooth device address of the
real Hub:
```
tools$ ./gateway.py -b -d AA:BB:CC:DD:EE:FF -l
```
To made the bluetooth server work, it may have to be startet as root.

Now you should discover the new `LEGO Hub@gateway` in your Robot Inventor App (e.g. on your tablet or phone).
Try to connect to it and watch the communication.

# Useful references
Other useful projects, mainly focused on LEGO® Education SPIKE™ Prime. But the Hub is mostly the same:
* https://github.com/sanjayseshan/spikeprime-tools
* https://github.com/sanjayseshan/spikeprime-vscode
* https://github.com/gpdaniels/spike-prime
* https://github.com/robmosca/robotinventor-vscode
* https://github.com/dwalton76/spikedev

Scripts for the Hub itself:
* A self balancing robot: https://medium.com/@janislavjankov/self-balancing-robot-with-lego-spike-prime-ac156af5c2b2