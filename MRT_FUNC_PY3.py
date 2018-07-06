#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 26 12:35:20 2018

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

def Scan(ser,deg):
    ser.write(SCAN)
    ser.write(str.encode(deg))
    data = readStream(ser)
    mrtstate.state = readState(ser)
    return data

def PlotData(ndata):
    plt.figure(1,figsize=(10,7))
    plt.clf()
    plt.subplot(311)
    if (ndata['axis'][0] == 'L'):
        x = ndata['elDeg']
    if (ndata['axis'][0] == 'A'):
        x = ndata['azDeg']
    plt.plot(x,ndata['pwr'])
    plt.xlabel('Angle (degrees)')
    plt.ylabel(r'Power ($\mu$W)')
    plt.subplot(312)
    plt.plot(ndata['ax'],label='ax')
    plt.plot(ndata['ay'],label='ay')
    plt.plot(ndata['az'],label='az')
    plt.legend()
    plt.subplot(313)
    plt.plot(ndata['mx'],label='mx')
    plt.plot(ndata['my'],label='my')
    plt.plot(ndata['mz'],label='mz')
    plt.legend()
    #N = 10
    #plt.plot(x,np.convolve(pwr, np.ones((N,))/N, mode='same'),'r')
    plt.show()
    return

'''
def GoTo(current_state,azG=None,elG=None):
    if azG == None:
        azG = input("Az: ")
        azG = float(azG)
    if elG == None:
        elG = input("El: ")
        elG = float(elG)
    
    """ I just chose the wrong convention for azimuth rotation.  
    I picked that F is CCW and increasing numbers, and the astronomical
    convention would be that CW from above is increasing (N through E).
    So we have to do a sign flip on the AZ and a counterintuitive 
    direction for the motion.  Idiot.  """
    # Should find a way to encode these limits elsewhere
    if ((azG >=0. and azG <= 360.) and (elG >= -eloff and elG <= 120.)):
        # Deltas are defined as desired minus current position
        d_az = azG - float(current_state['azDeg'][0])
        d_el = elG - float(current_state['elDeg'][0])
        print ('d_az',d_az)
        print ('d_el',d_el)
        current_state = StdCmd(ser,AZIMUTH)
        current_state = StdCmd(ser,ENABLE)
        if d_az < 0:
            # If moving to a less positive azimuth, go CCW
            current_state = StdCmd(ser,FORWARD)
        else:
            # If moving to a more positive azimuth, go CW
            current_state = StdCmd(ser,REVERSE)
            print ('Starting from')
            PrintState()
            d,current_state = Scan(ser,str(np.abs(d_az)))
            current_state = StdCmd(ser,ELEVATION)
            current_state = StdCmd(ser,ENABLE)
        if d_el < 0:
            current_state = StdCmd(ser,REVERSE)
        else:
            current_state = StdCmd(ser,FORWARD)
            d,current_state = Scan(ser,str(np.abs(d_el)))
            print ('Ending at')
            PrintState()
    else:
        print ('Requested az/el out of bounds')
'''

def GoTo(azG=None,elG=None):
    if azG == None:
        azG = input("Az: ")
        azG = float(azG)
    if elG == None:
        elG = input("El: ")
        elG = float(elG)
    d_az = azG - float(mrtstate.state['azDeg'][0])
    d_el = elG - float(mrtstate.state['elDeg'][0])
    print ('d_az: ',d_az)
    print ('d_el: ',d_el)
    "THIS IS A NEW ATTEMP"
    if (azG >=0. and azG <= 360.):
        mrtstate.state = StdCmd(ser,AZIMUTH)
        #print(mrtstate.state)
        mrtstate.state = StdCmd(ser,ENABLE)
        if d_az < 0:
            # If moving to a less positive azimuth, go CCW
            mrtstate.state = StdCmd(ser,FORWARD)
            print ('Starting from')
            PrintState()
            #d = Scan(ser,str(np.abs(d_az)))
            ser.write(SCAN(ser,str(np.abs(d_az))))
            mrtstate.state = readState(ser)
            azG=None
            print('hi1')
        else:
            # If moving to a more positive azimuth, go CW
            mrtstate.state = StdCmd(ser,AZIMUTH)
            print('hi1')
            mrtstate.state = StdCmd(ser,REVERSE)
            print('hi3')
            print ('Starting from')
            print('hi4')
            PrintState()
            print('hi5')
            #d = Scan(ser,str(np.abs(d_az)))
            SCAN(ser,(np.abs(d_az)))
            #ser.write(str.encode(np.abs(d_az)))
            print('hi6')
            mrtstate.state = readState(ser)
            print('hi7')
            azG=None
            print('hi8')
    else:
        print ('Requested az/el out of bounds')
        azG=None
        elG=None
    if (elG >= -eloff and elG <= 120.):
        mrtstate.state = StdCmd(ser,ELEVATION)
        mrtstate.state = StdCmd(ser,ENABLE)
        if d_el < 0:
            mrtstate.state = StdCmd(ser,REVERSE)
            #d = Scan(ser,str(np.abs(d_el)))
            ser.write(SCAN(ser,str(np.abs(d_el))))
            mrtstate.state = readState(ser)
            print ('Ending at')
            PrintState()
            elG=None
            print('hi3')
        else:
            mrtstate.state = StdCmd(ser,FORWARD)
            #d = Scan(ser,str(np.abs(d_el)))
            ser.write(SCAN(ser,str(np.abs(d_el))))
            mrtstate.state = readState(ser)
            print ('Ending at')
            PrintState()
            elG=None
            print('hi4')
    else:
        print ('Requested az/el out of bounds')
        azG=None
        elG=None
    return #(current_state)

def GoAz(current_state,azGa=None):
    if azGa == None:
        azGa = input("Az: ")
        azGa = float(azGa)
    d_azga = azGa - float(current_state['azDeg'][0])
    print ('d_az: ',d_azga)
    if (azGa >=0. and azGa <= 360.):
        current_state = StdCmd(ser,AZIMUTH)
        current_state = StdCmd(ser,ENABLE)
        if d_azga < 0:
            # If moving to a less positive azimuth, go CCW
            current_state = StdCmd(ser,FORWARD)
            print ('Starting from')
            PrintState()
            Scan(ser,np.abs(d_azga))
            #d,current_state = Scan(ser,str(np.abs(d_azga)))
            #current_state = readState(ser)
            print ('Ending at')
            PrintState()
        else:
            # If moving to a more positive azimuth, go CW
            current_state = StdCmd(ser,AZIMUTH)
            current_state = StdCmd(ser,REVERSE)
            print ('Starting from')
            PrintState()
            ser.write(SCAN)
            deg = np.abs(d_azga)
            ser.write(str.encode(deg))
            #d,current_state = Scan(ser,str(np.abs(d_azga)))
            #current_state = readState(ser)
            print ('Ending at')
            PrintState()
    else:
        print ('Requested az out of bounds')
        azGa=None
    #current_state = readState(ser)
    #return (current_state)

def GoEl(current_state, elGe=None):
    if elGe == None:
        elGe = input("El: ")
        elGe = float(elGe)
    d_elge = elGe - float(current_state['elDeg'][0])
    print ('d_el: ',d_elge)
    if (elGe >= -eloff and elGe <= 120.):
        current_state = StdCmd(ser,ELEVATION)
        current_state = StdCmd(ser,ENABLE)
        if d_elge < 0:
            # If moving to a less positive azimuth, go CCW
            current_state = StdCmd(ser,REVERSE)
            print ('Starting from')
            PrintState()
            d,current_state = Scan(ser,str(np.abs(d_elge)))
            current_state = readState(ser)
            print ('Ending at')
            PrintState()
        else:
            # If moving to a more positive azimuth, go CW
            current_state = StdCmd(ser,ELEVATION)
            current_state = StdCmd(ser,FORWARD)
            print ('Starting from')
            PrintState()
            d,current_state = Scan(ser,str(np.abs(d_elge)))
            current_state = readState(ser)
            print ('Ending at')
            PrintState()
    else:
        print ('Requested az out of bounds')
        elGe=None
    current_state = readState(ser)
    return (current_state)
    
def RasterMap(current_state):
    """ Super hard coded to get something going.  Start where you are, and
    make a 20 x 20 degree map """

    azG = input("Az: ")
    azG = float(azG)
    elG = input("El: ")
    elG = float(elG)
    azM = azG-10.
    elM = elG-10.
    GoTo(current_state,azG=azM,elG=elM)
    
    #plt.figure(1)
    #plt.clf()
    
    az = np.array([])
    el = np.array([])
    pwr = np.array([])
    for i in np.arange(10):
        print (i,'of 10')
        cs = StdCmd(ser,AZIMUTH)
        cs = StdCmd(ser,REVERSE)
        d,cs = Scan(ser,'20')
        #plt.subplot(10,1,i+1)
        #plt.plot(d['azDeg'],d['pwr'])
        az = np.append(az,d['azDeg'])
        el = np.append(el,d['elDeg'])
        pwr = np.append(pwr,d['pwr'])
        cs = StdCmd(ser,ELEVATION)
        cs = StdCmd(ser,REVERSE)
        d,cs= Scan(ser,'1')
        cs = StdCmd(ser,AZIMUTH)
        cs = StdCmd(ser,FORWARD)
        d,cs = Scan(ser,'20')
        #plt.subplot(10,1,i+1)
        #plt.plot(d['azDeg'],d['pwr'])
        az = np.append(az,d['azDeg'])
        el = np.append(el,d['elDeg'])
        pwr = np.append(pwr,d['pwr'])
        cs = StdCmd(ser,ELEVATION)
        cs = StdCmd(ser,REVERSE)
        d,cs = Scan(ser,'1')
    
    #plt.show()
    plt.figure(2,figsize=(8,8))
    plt.clf()
    eli = np.linspace(az.min(),az.max(),20)
    azi = np.linspace(el.min(),el.max(),20)
    # grid the data.
    zi = griddata((az, el), pwr, (eli[None,:], azi[:,None]), method='nearest')
    # contour the gridded data
    np.savez(file='map_'+time.ctime().replace(' ','_')+'.npz',
             az=az,el=el,pwr=pwr,zi=zi,azi=azi,eli=eli)

    
    plt.imshow(np.flipud(zi),aspect='auto',cmap=plt.cm.jet,
               extent=[eli.min(),eli.max(),azi.min(),azi.max()])
    plt.colorbar()
    #CS = plt.contour(zi,5,linewidths=1,colors='w')
    plt.contour(eli,azi,zi,5,linewidths=1,colors='w')
    #CS = plt.contourf(eli,azi,zi,10,cmap=plt.cm.jet)
    plt.axis('equal')
    plt.xlabel('Azimuth (degrees)')
    plt.ylabel('Elevation (degrees)')
    plt.savefig(time.ctime().replace(' ','_')+'.png')
    plt.show()
    
    return (az,el,pwr,zi,azi,eli)

def PrintMenu():
    """ Provide the user the available commands """
    return

def ScanSouthSky(current_state):
    
    Saz = float(current_state['azDeg'][0])
    Sel = float(current_state['elDeg'][0])
    
    if ((Saz >=89.5 and Saz <= 90.5) and (Sel >=79.5 and Sel<= 80.5)):
            az = np.array([])
            el = np.array([])
            pwr = np.array([])
            for i in np.arange(45):
                print (i,'of 50')
                cs = StdCmd(ser,AZIMUTH)
                cs = StdCmd(ser,REVERSE)
                d,cs = Scan(ser,'180')
                #plt.subplot(10,1,i+1)
                #plt.plot(d['azDeg'],d['pwr'])
                az = np.append(az,d['azDeg'])
                el = np.append(el,d['elDeg'])
                pwr = np.append(pwr,d['pwr'])
                cs = StdCmd(ser,ELEVATION)
                cs = StdCmd(ser,REVERSE)
                d,cs= Scan(ser,'1')
                cs = StdCmd(ser,AZIMUTH)
                cs = StdCmd(ser,FORWARD)
                d,cs = Scan(ser,'180')
                #plt.subplot(10,1,i+1)
                #plt.plot(d['azDeg'],d['pwr'])
                az = np.append(az,d['azDeg'])
                el = np.append(el,d['elDeg'])
                pwr = np.append(pwr,d['pwr'])
                cs = StdCmd(ser,ELEVATION)
                cs = StdCmd(ser,REVERSE)
                d,cs = Scan(ser,'1')
    
            #plt.show()
            plt.figure(2,figsize=(8,4))
            plt.clf()
            eli = np.linspace(az.min(),az.max(),90)
            azi = np.linspace(el.min(),el.max(),180)
            # grid the data.
            zi = griddata((az, el), pwr, (eli[None,:], azi[:,None]), method='nearest')
            # contour the gridded data
            np.savez(file='map_'+time.ctime().replace(' ','_')+'.npz',
                     az=az,el=el,pwr=pwr,zi=zi,azi=azi,eli=eli)

    
            plt.imshow(np.flipud(zi),aspect='auto',cmap=plt.cm.jet,
                       extent=[eli.min(),eli.max(),azi.min(),azi.max()])
            plt.colorbar()
            #CS = plt.contour(zi,5,linewidths=1,colors='w')
            plt.contour(eli,azi,zi,5,linewidths=1,colors='w')
            #CS = plt.contourf(eli,azi,zi,10,cmap=plt.cm.jet)
            plt.axis('equal')
            plt.xlabel('Azimuth (degrees)')
            plt.ylabel('Elevation (degrees)')
            plt.savefig(time.ctime().replace(' ','_')+'.png')
            plt.show()
    else:
        print('Telescope must be in position Az = 90 El = 90 for this function.')
                
    return (az,el,pwr,zi,azi,eli)