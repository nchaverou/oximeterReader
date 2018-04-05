"""*************************************************************************
*                                                                          *
* Copyright (C) Nicolas Chaverou - All Rights Reserved.                    *
*                                                                          *
*************************************************************************"""

#**************************************************************************
#! @file cms50v45.py
#  @brief Driver for Oximeter CMS50D+ with firmware 4.5
#  @copyright Copyright (c) 2015, Asbjørn Brask - - All Rights Reserved.
#  @source https://github.com/atbrask/CMS50Dplus
#**************************************************************************

#!/usr/bin/env python3
import serial
import datetime

""" Live data point struct """
class LiveDataPoint():
    def __init__(self, time, data):
        if [d & 0x80 != 0 for d in data] != [True, False, False, False, False]:
            raise ValueError("Invalid data packet.")

        self.time = time

        # 1st byte
        self.signalStrength = data[0] & 0x0f
        self.fingerOut = bool(data[0] & 0x10)
        self.droppingSpO2 = bool(data[0] & 0x20)
        self.beep = bool(data[0] & 0x40)

        # 2nd byte
        self.pulseWaveform = data[1]

        # 3rd byte
        self.barGraph = data[2] & 0x0f
        self.probeError = bool(data[2] & 0x10)
        self.searching = bool(data[2] & 0x20)
        self.pulseRate = (data[2] & 0x40) << 1

        # 4th byte
        self.pulseRate |= data[3] & 0x7f

        # 5th byte
        self.bloodSpO2 = data[4] & 0x7f

    def __str__(self):
        return ", ".join(["Time = {0}", "Signal Strength = {1}", "Finger Out = {2}", "Dropping SpO2 = {3}", "Beep = {4}", "Pulse waveform = {5}", "Bar Graph = {6}", "Probe Error = {7}", "Searching = {8}", "Pulse Rate = {9} bpm", "SpO2 = {10}%"]).format(self.time, self.signalStrength, self.fingerOut, self.droppingSpO2, self.beep, self.pulseWaveform, self.barGraph, self.probeError, self.searching, self.pulseRate, self.bloodSpO2)

    @staticmethod
    def getCsvColumns():
        return ["Time", "PulseRate", "SpO2", "PulseWaveform", "BarGraph", "SignalStrength", "Beep", "FingerOut", "Searching", "DroppingSpO2", "ProbeError"]

    def getCsvData(self):
        return [self.time, self.pulseRate, self.bloodSpO2, self.pulseWaveform, self.barGraph, self.signalStrength, self.beep, self.fingerOut, self.searching, self.droppingSpO2, self.probeError]

    def getDictData(self):
        ret = dict()
        for n, d in zip(self.getCsvColumns(), self.getCsvData()):
            ret[n] = d
        return ret


class CMS50DDriver():
    def __init__(self):
        self.port = ''
        self.conn = None

    def isConnected(self):
        return type(self.conn) is serial.Serial and self.conn.isOpen()

    def connect(self, port):
        self.port = port
        if self.conn is None:
            self.conn = serial.Serial(port=self.port, baudrate=19200, parity=serial.PARITY_ODD, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=5, xonxoff=1)
        elif not self.isConnected():
            self.conn.open()

    def disconnect(self):
        if self.isConnected():
            self.conn.close()

    def getByte(self):
        char = self.conn.read()
        if len(char) == 0:
            return None
        else:
            return ord(char)

    def getLiveData(self):
        try:
            packet = [0] * 5
            idx = 0
            while True:
                byte = self.getByte()
                if byte is None:
                    break

                if byte & 0x80:
                    if idx == 5 and packet[0] & 0x80:
                        yield LiveDataPoint(datetime.datetime.utcnow(), packet)
                    packet = [0] * 5
                    idx = 0

                if idx < 5:
                    packet[idx] = byte
                    idx += 1
        except:
            self.disconnect()
