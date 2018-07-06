#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  2 15:20:55 2018

@author: oscartinney
"""

import serial
import numpy as np
import matplotlib.pyplot as plt
import time
import MRTtools as mrt
import mrtstate
#import MRT_PY3_temp as mrt3
from scipy.interpolate import griddata
#%%
# Don't yet have a good way of auto-detecting which port is Arduino
#port='/dev/cu.usbmodem1421'
#port='/dev/cu.usbmodem1411'
#port = '/dev/ttyACM0'
#port = '/dev/cu.usbmodem14521'
#port = '/dev/cu.usbmodem14431'
#port = '/dev/cu.usbmodem14421'
#port = '/dev/cu.usbmodem14611'
#port = '/dev/cu.usbmodem14631'
port = '/dev/cu.usbmodem14621'
#port = '/dev/cu.usbmodem14331'
baud = 115200
nIDBytes = 18
# Should remove this and do the initialization of the serial port in the main
# body of the program.  That will mean re-writing a lot of functions to explicitly
# accept `ser` as a variable.  :(
ser = serial.Serial(port, baud)
#%%
EOT = b'ZZZ\r\n'
#BTX = 'AAA\r\n'
BDTX = b'BDTX\r\n'
EDTX = b'EDTX\r\n'

# Arduino commands
REPORT_STATE = b'X'
ELEVATION = b'L'
AZIMUTH = b'A'
FORWARD = b'F'
REVERSE = b'R'
SCAN = b'S'
ENABLE = b'E'

# For the nominal mounting in the observatory
eloff = 35.5
azoff = -191.
# For a general setup facing south
#eloff = 35.5
#azoff = -180.

def WaitForInputBytes(timeout=10,nbytesExpected=1):
    """ Wait for bytes to appear on the input serial buffer up to the timeout
    specified, in seconds """
    bytesFound=False
    t0 = time.time()
    dt = time.time()-t0
    while (not bytesFound and dt < timeout):
        nbytes = ser.inWaiting()
        if nbytes == nbytesExpected:
            bytesFound = True
        dt = time.time()-t0
    return nbytes, dt

def ResetArduinoUno(ser,timeout=10,nbytesExpected=1):
    ser.setDTR(False)
    time.sleep(1)
    ser.setDTR(True)
    #time.sleep(3)
    nbytes,dt=WaitForInputBytes(nbytesExpected=nbytesExpected)
    print (nbytes,'bytes found after',dt,'seconds')
    return

def FlushSerialBuffers(ser):
    ser.flushInput()
    ser.flushOutput()
    return

# --------------------------------------------

def initState():
    """ Initialize a dictionary to hold the state """
    state = {}
    for state_var in mrtstate.state_vars:
        state[state_var] = []
    return state
        
def numpyState(state):
    ndata = {}
    for i in np.arange(len(mrtstate.state_vars)):
        ndata[mrtstate.state_vars[i]] = np.array(state[mrtstate.state_vars[i]],
                                        dtype=mrtstate.state_dtypes[i])
    ndata['pwr'] = mrt.zx47_60(ndata['voltage'])
    # Both readState and readStream run through here.
    # Apply offsets
    ndata['azDeg'] = np.mod(-ndata['azDeg'] - azoff,360)
    ndata['elDeg'] -= eloff 

    return ndata

def parseState(buffer,state):
    """ Take the raw string returned by the Arduino ("buffer") for the current state,
    and parse it into the state dictionary defined by the state_vars """
    vars = buffer[0].split()
    #assert len(buf[0].split()) == len(state_vars)
    if len(vars) != len(mrtstate.state_vars):
        print('Cannot parse the returned state')
        FlushSerialBuffers(ser)
        state = initState()
    else:
        for i,var in enumerate(vars):
            state[mrtstate.state_vars[i]].append(var)
    return state

def readState(ser,init=None):
    # Initialize the dictionary, unless a previous state is passed in
    if init == None:
        data = initState()
    else:
        data = init
    buf = read_ser_buffer_to_eot(ser)
    data = parseState(buf,data)
    ndata = numpyState(data)
    mrtstate.state = ndata
    return ndata

'''
def readState(ser,init=0):
    # Initialize the dictionary, unless a previous state is passed in
    if init == 0:
        data = initState()
    else:
        data = init
    buf = read_ser_buffer_to_eot(ser)
    data = parseState(buf,data)
    if data is not 0:
        mrtstate.state = numpyState(data)
    #else:
    #    ndata = mrtstate.state #None
    
    return #ndata

def readState(ser):
    # Initialize the dictionary, unless a previous state is passed in
    data = initState()
    buf = read_ser_buffer_to_eot(ser)
    data = parseState(buf,data)
    if data is not None:
        mrtstate.state = numpyState(data)
    #else:
    #    ndata = mrtstate.state #None
    
    return #ndata
'''
# GODDAMMIT!  There are two places where I read data: readState and readStream
def readStream(ser):
    """ Generalize read_data to read an arbitrary list """
    data = initState()
    # Begin reading serial port
    buf = read_ser_buffer_to_eot(ser) #ser.readline()
    #print '1 BUFFER', buf[0]
    # Read anything you see until you see BDTX
    while (buf[0] != BDTX):
        buf = read_ser_buffer_to_eot(ser) #ser.readline()
        #print '2 BUFFER:', buf[0]
    # Then read states
    while(buf[0] != EDTX):
        buf = read_ser_buffer_to_eot(ser)
        if (buf[0] != EDTX):
            data = parseState(buf, data)
    ndata = numpyState(data)
    return ndata

def StdCmd(ser,cmd):
    ser.write(cmd)
    return readState(ser)

def PrintState():
    """ Make a pretty version of the current state """
    print ('AZ:',mrtstate.state['azDeg'][0],'EL:',mrtstate.state['elDeg'][0])
    print ('Current axis:',mrtstate.state['axis'][0])
    return

def read_ser_buffer_to_eot(ser):
    output = []
    buf = ser.readline()
    while(buf != EOT):
        output.append(buf)
        #print(buf[:-1])
        buf = ser.readline()
    return output

