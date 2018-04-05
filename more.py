#!/usr/bin/env python3

# Copyright (c) 2016 Tommi Airikka <tommi@airikka.net>
# License: GPLv2

import sys, struct, serial, argparse
import datetime

#####################
##### Variables #####
#####################
parser = argparse.ArgumentParser(description='Download stored data from a CMS50D+ oximeter.')
parser.add_argument('-s', '--start-time', dest='starttime', type=str, help='start time (\"YYYY-MM-DD HH:MM:SS\")')

args = parser.parse_args()

device = 'COM3'
outfile = 'C:/out.txt'
starttime = args.starttime
ser = serial.Serial()

###################
##### Helpers #####
###################
# Pack little endian


#####################
##### Functions #####
#####################
def configure_serial(ser):
    ser.baudrate = 115200               # 115200
    ser.bytesize = serial.EIGHTBITS     # 8
    ser.parity = serial.PARITY_NONE     # N
    ser.stopbits = serial.STOPBITS_ONE  # 1
    ser.xonxoff = 1                     # XON/XOFF flow control
    ser.timeout = 1
    ser.port = device



def get_raw_data(ser):
    sys.stdout.write("Connecting to device...")
    sys.stdout.flush()
    ser.open()
    sys.stdout.write("reading...")
    sys.stdout.flush()
    ser.write(b'\x7d\x81\xa1\x80\x80\x80\x80\x80\x80')
    raw = list(ser.read(9))
    while len(raw) >= 9:
        printer = ''
        for i in raw:
            printer += str(i & 0x7f) + " - "
        print(printer)
        #print (str(raw[5] & 0x7f) + " - " + str(raw[6] & 0x7f))
        #print (ord(str(raw[6])) & 0x7f)
        #print(raw)
        raw = ser.read(9)
    ser.close()
    if len(raw) <= 1:
        print("no data received. Is the device on?")
        exit(43)
    print("done!")
    return raw


################
##### Main #####
################
configure_serial(ser)
data = get_raw_data(ser)

print("done!")