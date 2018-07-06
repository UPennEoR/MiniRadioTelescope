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
import MRT_FUNC_PY3 as mrtf
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
#%%

# Initialize the current state
ser.write(mrtf.REPORT_STATE)
mrtstate.state = mrtf.readState(ser)
mrtf.PrintState()

#%%

""" Basic mode of operation should be that the Python side handles the user 
interface and menu, and sends groups of atomic commands.  The Arduino always
reports its state in response to any command, including whether the last 
command was valid.  Because I don't think we want to command individual steps,
but rather scans, that command is special """

operate=True
while(operate):
    var = input("Enter command to transmit, Q to quit: ")
    if not var == 'Q':
        if (var == 'M'): # Make a map!
            cs = mrtf.StdCmd(ser,mrtf.REPORT_STATE)
            az,el,pwr,mp,azi,eli = mrtf.RasterMap(cs)
            # Update the current state
            current_state = mrtf.StdCmd(ser,mrtf.REPORT_STATE)
            mrtf.PrintState()
        elif (var == 'MS'): # Make a map!
            cs = mrtf.StdCmd(ser,mrtf.REPORT_STATE)
            az,el,pwr,mp,azi,eli = mrtf.ScanSouthSky(cs)
            # Update the current state
            current_state = mrtf.StdCmd(ser,mrtf.REPORT_STATE)
            mrtf.PrintState()
        elif (var == 'G'):
            cs = mrtf.StdCmd(ser,mrtf.REPORT_STATE)
            current_state = mrtstate.state
            mrtf.GoTo()
            current_state =  mrtf.StdCmd(ser,mrtf.REPORT_STATE)
        elif (var == 'GA'):
            cs = mrtf.StdCmd(ser,mrtf.REPORT_STATE)
            current_state = cs
            mrtf.GoAz(cs)
            current_state =  mrtf.StdCmd(ser,mrtf.REPORT_STATE)
        elif (var == 'GE'):
            cs = mrtf.StdCmd(ser,mrtf.REPORT_STATE)
            current_state = cs
            mrtf.GoEl(cs)
            current_state =  mrtf.StdCmd(ser,mrtf.REPORT_STATE)
        elif (var == 'S'):
            print ("Sending "+var)
            ser.write(mrtf.SCAN)
            deg = input("Enter number of degrees to turn: ")
            print ("Sending "+deg)
            ser.write(str.encode(deg))
            print ("Reading data")
            ndata = mrtf.readStream(ser)
            current_state = mrtf.readState(ser)
            mrtf.PrintState()
            # Convert
            #ndata = numpyState(ndata)
            # Save
            np.savez(file=time.ctime().replace(' ','_')+'.npz',
                     ndata=ndata)
            # Plot
            mrtf.PlotData(ndata)
        elif (var == 'X'):
            Ndatapts = input("Enter number of data points: ")
            ser.write(mrtf.REPORT_STATE)
            # Initialize the data variable
            data = mrtf.readState(ser)
            for i in np.arange(int(Ndatapts)-1):
                ser.write(mrtf.REPORT_STATE)
                current_state = mrtf.readState(ser)
                mrtf.PrintState()
                # Trick it by sending invalid commands and reading them back
                #ser.write(REPORT_STATE)
                #read_ser_buffer_to_eot(ser)
                #dummy = readState(ser)
                #for key in data.keys():
                #    data[key].append(dummy[key][0])
            #ndata = numpyState(data)
            #PlotData(ndata)
        else:
            # Commands that get passed along
            print ("Sending "+var)
            ser.write(str.encode(var))
            # Read back any reply
            #read_ser_buffer_to_eot(ser)
            current_state = mrtf.readState(ser)
            mrtf.PrintState()
    else:
        operate = False

ser.close()
