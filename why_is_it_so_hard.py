#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  2 15:19:46 2018

@author: oscartinney
"""

#import serial
import numpy as np
#import matplotlib.pyplot as plt
import time
#import MRTtools as mrt
import mrtstate
import mrtf_test as mrtf
#from scipy.interpolate import griddata

#%%
# ----------------------------------------------------------------------------
# Begin
# ----------------------------------------------------------------------------
# Notify the user
print ('Opening serial port',mrtf.port)
print ('with baud',mrtf.baud)
""" For reasons unclear, the Mac appears to assert DTR on serial connection,
whereas the Pi does not.  So we will be super explicit. """
# Open the port
ser = mrtf.serial.Serial(mrtf.port, mrtf.baud)
#%
print ('Before flushing buffers')
print ('Bytes in waiting', ser.inWaiting())
mrtf.FlushSerialBuffers(ser)
print ('After flushing buffers')
print ('Bytes in waiting', ser.inWaiting())
#%
print ('Resetting Arduino')
print ('Before reset')
print ('Bytes in waiting', ser.inWaiting())
mrtf.ResetArduinoUno(ser,timeout=15,nbytesExpected=mrtf.nIDBytes)
# I don't understand why ARDUINO MRT is 18 bytes ...
print ('After reset')
print ('Bytes in waiting', ser.inWaiting())
print (ser.inWaiting())

#%

output = mrtf.read_ser_buffer_to_eot(ser)
print(output)
#%

# Initialize the current state
ser.write(mrtf.REPORT_STATE)
mrtstate.state = mrtf.readState(ser)
mrtf.PrintState()