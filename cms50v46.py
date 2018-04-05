"""*************************************************************************
*                                                                          *
* Copyright (C) Nicolas Chaverou - All Rights Reserved.                    *
*                                                                          *
*************************************************************************"""

#**************************************************************************
#! @file cms50v46.py
#  @brief Driver for Oximeter CMS50D+ with firmware 4.6
#  @copyright  Copyright (c) 2016 Tommi Airikka <tommi@airikka.net>
#  @source https://gist.github.com/patrick-samy/df33e296885364f602f0c27f1eb139a8
#**************************************************************************

#!/usr/bin/env python3
import serial
import datetime

""" Live data point struct """
class LiveDataPoint():
    def __init__(self, time, data):

        self.time = time

        # 1st byte
        self.signalStrength = data[0] & 0x0f
        self.fingerOut = bool(data[0] & 0x10)
        self.droppingSpO2 = bool(data[0] & 0x20)
        self.beep = bool(data[0] & 0x40)

        # 4th byte
        self.pulseWaveform = data[3] & 0x7f

        # 3rd byte
        self.barGraph = data[2] & 0x0f
        self.probeError = bool(data[2] & 0x10)
        self.searching = bool(data[2] & 0x20)
        self.pulseRate = (data[2] & 0x40) << 1

        # 4th byte
        self.pulseRate = data[5] & 0x7f

        # 5th byte
        self.bloodSpO2 = data[6] & 0x7f

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
            self.conn = serial.Serial(port=self.port, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1, xonxoff=1)
            self.conn.write(b'\x7d\x81\xa1\x80\x80\x80\x80\x80\x80')  # handshake
        elif not self.isConnected():
            self.conn.open()
            self.conn.write(b'\x7d\x81\xa1\x80\x80\x80\x80\x80\x80')  # handshake

    def disconnect(self):
        if self.isConnected():
            self.conn.close()

    def getBytes(self):
        raw = list(self.conn.read(9))
        if len(raw) < 0:
            return None
        else:
            return raw

    def getLiveData(self):
        try:
            while True:
                packet = self.getBytes()
                if packet is None:
                    break
                yield LiveDataPoint(datetime.datetime.utcnow(), packet)
        except:
            self.disconnect()
