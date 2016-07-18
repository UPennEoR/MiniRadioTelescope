#!/usr/bin/env python
#
# Copyright 2007 John Wiseman <jjwiseman@yahoo.com>
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
A port of Tod E. Kurt's arduino-serial.c.
<http://todbot.com/blog/2006/12/06/arduino-serial-c-code-to-talk-to-arduino/>
"""
from __future__ import print_function

import termios
import os
import sys
import time
import getopt


# Map from the numbers to the termios constants (which are pretty much
# the same numbers).

BPS_SYMS = {
    4800: termios.B4800,
    9600: termios.B9600,
    19200: termios.B19200,
    38400: termios.B38400,
    57600: termios.B57600,
    115200: termios.B115200
}


# Indices into the termios tuple.

IFLAG = 0
OFLAG = 1
CFLAG = 2
LFLAG = 3
ISPEED = 4
OSPEED = 5
CC = 6


def bps_to_termios_sym(bps):
    return BPS_SYMS[bps]


class SerialPort(object):
    """Represents a serial port connected to an Arduino."""
    def __init__(self, serialport, bps):
        """Takes the string name of the serial port (e.g.
        "/dev/tty.usbserial","COM1") and a baud rate (bps) and connects to
        that port at that speed and 8N1. Opens the port in fully raw mode
        so you can send binary data.
        """
        self.fd = os.open(serialport, os.O_RDWR | os.O_NOCTTY | os.O_NDELAY)
        attrs = termios.tcgetattr(self.fd)
        bps_sym = bps_to_termios_sym(bps)
        # Set I/O speed.
        attrs[ISPEED] = bps_sym
        attrs[OSPEED] = bps_sym

        # 8N1
        attrs[CFLAG] &= ~termios.PARENB
        attrs[CFLAG] &= ~termios.CSTOPB
        attrs[CFLAG] &= ~termios.CSIZE
        attrs[CFLAG] |= termios.CS8
        # No flow control
        attrs[CFLAG] &= ~termios.CRTSCTS

        # Turn on READ & ignore contrll lines.
        attrs[CFLAG] |= termios.CREAD | termios.CLOCAL
        # Turn off software flow control.
        attrs[IFLAG] &= ~(termios.IXON | termios.IXOFF | termios.IXANY)

        # Make raw.
        attrs[LFLAG] &= ~(termios.ICANON |
                          termios.ECHO |
                          termios.ECHOE |
                          termios.ISIG)
        attrs[OFLAG] &= ~termios.OPOST

        # It's complicated--See
        # http://unixwiz.net/techtips/termios-vmin-vtime.html
        attrs[CC][termios.VMIN] = 0
        attrs[CC][termios.VTIME] = 20
        termios.tcsetattr(self.fd, termios.TCSANOW, attrs)

    def read_until(self, until):
        buf = ""
        done = False
        while not done:
            n = os.read(self.fd, 1)
            if n == '':
                # FIXME: Maybe worth blocking instead of busy-looping?
                time.sleep(0.01)
                continue
            buf = buf + n
            if n == until:
                done = True
        return buf

    def write(self, str):
        os.write(self.fd, str)

    def write_byte(self, byte):
        os.write(self.fd, chr(byte))


def main(args):
    port = None
    bps = 9600
    try:
        optlist, args = getopt.getopt(
            args[1:], 'hp:b:s:rn:d:',
            ['help', 'port=', 'baud=', 'send=', 'receive',
             'num=', 'delay='])
        for (o, v) in optlist:
            if o == '-d' or o == '--delay':
                n = float(v) / 1000.0
                time.sleep(n)
            elif o == '-h' or o == '--help':
                usage()
            elif o == '-b' or o == '--baud':
                bps = int(v)
            elif o == '-p' or o == '--port':
                port = SerialPort(v, bps)
            elif o == '-n' or o == '--num':
                n = int(v)
                port.write_byte(n)
            elif o == '-s' or o == '--send':
                port.write(v)
            elif o == '-r' or o == '--receive':
                print('Read %s' % (port.read_until('\n'),))
        sys.exit(0)
    except getopt.GetoptError as e:
        sys.stderr.write('%s: %s\n' % (args[0], e.msg))
        usage()
        sys.exit(1)


def usage():
    print("""Usage: arduino-serial.py -p <serialport> [OPTIONS]
Options:
  -h, --help                   Print this help message.
  -p, --port=SERIALPORT        Serial port Arduino is on.
  -b, --baud=BAUDRATE          Baudrate (bps) of Arduino.
  -s, --send=DATA              Send data to Arduino.
  -r, --receive                Receive data from Arduino & print it out.
  -n  --num=NUM                Send a number as a single byte.
  -d  --delay=MILLIS           Delay for specified milliseconds.

Note: Order is important. Set '-b' before doing '-p'.
      Used to make series of actions:  '-d 2000 -s hello -d 100 -r'
      means 'wait 2 seconds, send 'hello', wait 100 msec, get reply'.\n""")


if __name__ == '__main__':
    main(sys.argv)
