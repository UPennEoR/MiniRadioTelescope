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
    ndata['azDeg'] = np.round(np.mod(-ndata['azDeg'] - azoff,360),3)
    ndata['elDeg'] = np.round(ndata['elDeg']-eloff, 3)
    return ndata

def parseState(buffer,state):
    """ Take the raw string returned by the Arduino ("buffer") for the current state,
    and parse it into the state dictionary defined by the state_vars """
    vars = buffer[0].split()
    #assert len(buf[0].split()) == len(state_vars)
    if len(vars) != len(mrtstate.state_vars):
        print('Cannot parse the returned state')
        FlushSerialBuffers(ser)
        state = mrtstate.state #initState()
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

# GODDAMMIT!  There are two places where I read data: readState and readStream
def readStream(ser):
    """ Generalize read_data to read an arbitrary list """
    data = initState()
    # Begin reading serial port
    buf = read_ser_buffer_to_eot(ser) #ser.readline()
    #print('1 BUFFER', buf[0])
    # Read anything you see until you see BDTX
    while (buf[0] != BDTX):
        buf = read_ser_buffer_to_eot(ser) #ser.readline()
        #print('2 BUFFER:', buf[0])
    # Then read states
    while(buf[0] != EDTX):
        buf = read_ser_buffer_to_eot(ser)
        if (buf[0] != EDTX):
            #print(buf[0])
            data = parseState(buf, data)
    ndata = numpyState(data)
    #StdCmd(ser,REPORT_STATE)
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
    #print('Writing',SCAN)
    ser.write(SCAN)
    # The round statement is necessary to prevent a problem with interpretation
    # by the Arduino when converted to an ASCII string.
    # Is it possible to send floats directly to the Arduino?
    deg_str = str.encode(str(np.round(deg,3)))
    #print('Writing',deg_str)
    ser.write(deg_str)
    data = readStream(ser)
    #StdCmd(ser,REPORT_STATE)
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
    if (azG >=0. and azG <= 360.):
        az_ok = True
    else:
        az_ok = False
        print ('Requested azimuth out of bounds')
    if (elG >= -eloff and elG <= 120.):
        el_ok = True
    else:
        el_ok = False
        print ('Requested elevation out of bounds')
        
    if (az_ok and el_ok):
        # Do the azimuth move
        StdCmd(ser,AZIMUTH)
        StdCmd(ser,ENABLE)
        print ('Azimuth move starting')
        PrintState()
        if d_az < 0:
            # If moving to a less positive azimuth, go CCW
            StdCmd(ser,FORWARD)
        else:
            StdCmd(ser,REVERSE)
        #print(str(np.abs(d_az)))
        Scan(ser,np.abs(d_az))
        #print('Azimuth move ended at')
        #PrintState()
        # Elevation move
        StdCmd(ser,ELEVATION)
        StdCmd(ser,ENABLE)
        print ('Elevation move starting')
        PrintState()
        if d_el < 0:
            StdCmd(ser,REVERSE)
        else:
            StdCmd(ser,FORWARD)
        Scan(ser,np.abs(d_el))
        StdCmd(ser,AZIMUTH)
        StdCmd(ser,ENABLE)
        print ('Final state')
        PrintState()
    return

def GoAz(azGa=None):
    if azGa == None:
        azGa = input("Az: ")
        azGa = float(azGa)
    d_azga = azGa - float(mrtstate.state['azDeg'][0])
    print ('d_az: ',d_azga)
    if (azGa >=0. and azGa <= 360.):
        StdCmd(ser,AZIMUTH)
        StdCmd(ser,ENABLE)
        print ('Azimuth move starting')
        PrintState()
        if d_azga < 0:
            # If moving to a less positive azimuth, go CCW
            StdCmd(ser,FORWARD)   
        else:
            StdCmd(ser,REVERSE)
        print(str(np.abs(d_azga)))
        Scan(ser,np.abs(d_azga))
        print('Azimuth move ended at')
        PrintState()
        print ('Final state')
        PrintState()
    else:
        print ('Requested azimuth out of bounds')
        azGa=None

def GoEl(elGe=None):
    if elGe == None:
        elGe = input("El: ")
        elGe = float(elGe)
    d_elge = elGe - float(mrtstate.state['elDeg'][0])
    print ('d_el: ',d_elge)
    if (elGe >= -eloff and elGe <= 120.):
        StdCmd(ser,ELEVATION)
        StdCmd(ser,ENABLE)
        print ('Elevation move starting')
        PrintState()
        if d_elge < 0:
            StdCmd(ser,REVERSE)   
        else:
            StdCmd(ser,FORWARD)
        print(str(np.abs(d_elge)))
        Scan(ser,np.abs(d_elge))
        print('Elevation move ended at')
        PrintState()
        print ('Final state')
        PrintState()
    else:
        print ('Requested elevation out of bounds')
        elGe=None
    
def RasterMap():
    """ Super hard coded to get something going.  Start where you are, and
    make a 20 x 20 degree map """

    azG = input("Az: ")
    azG = float(azG)
    elG = input("El: ")
    elG = float(elG)
    DIM = input("Azimuth Dimension: ")
    DIMF = float(DIM)
    ONE = 1.2
    ONEF = float(ONE)
    DIME = input("Elevation Dimension: ")
    DIMEF = float(DIME)
    DIMEI = int(DIME)/2
    azM = azG-DIMF/2.
    elM = elG+DIMEI
    #FIGX = 
    #FIGY = 
    GoTo(azG=azM,elG=elM)
    #DIMX = input("X length: ")
    #DIMX = float(DIMX)
    #DIMY = input("Y length: ")
    #DIMY = float(DIMY)
   
    
    #plt.figure(1)
    #plt.clf()
    
    az = np.array([])
    el = np.array([])
    pwr = np.array([])
    for i in np.arange(DIMEI):
        print (i,'of ',DIMEI)
        StdCmd(ser,AZIMUTH)
        StdCmd(ser,REVERSE)
        d = Scan(ser,DIMF)
        #plt.subplot(10,1,i+1)
        #plt.plot(d['azDeg'],d['pwr'])
        az = np.append(az,d['azDeg'])
        el = np.append(el,d['elDeg'])
        pwr = np.append(pwr,d['pwr'])
        StdCmd(ser,ELEVATION)
        StdCmd(ser,REVERSE)
        d= Scan(ser,ONEF)
        StdCmd(ser,AZIMUTH)
        StdCmd(ser,FORWARD)
        d = Scan(ser,DIMF)
        #plt.subplot(10,1,i+1)
        #plt.plot(d['azDeg'],d['pwr'])
        az = np.append(az,d['azDeg'])
        el = np.append(el,d['elDeg'])
        pwr = np.append(pwr,d['pwr'])
        StdCmd(ser,ELEVATION)
        StdCmd(ser,REVERSE)
        d = Scan(ser,ONEF)
    
    #plt.show()
    plt.figure(2,figsize=(8,8))
    plt.clf()
    eli = np.linspace(az.min(),az.max(),DIMF)
    azi = np.linspace(el.min(),el.max(),DIMEF)
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
    print('Final State')
    PrintState()
    
    return (az,el,pwr,zi,azi,eli)

def PrintMenu():
    """ Provide the user the available commands """
    print('A: Set Azimuth')
    print('L: Set Elevation')
    print('E: Enable')
    print('F: Set Forward Direction')
    print('R: Set Reverse Direction')
    print('S: Scan')
    print('G: Go to specific coordinates')
    print('GA: Go to specific Azimuth')
    print('GE: Go to specific Elevation')
    print('M: Map a grid around a specific coordinate with variable dimensions')
    print('MS: Map the entire south sky')
    print('CS: Get the full current state of the telescope')
    print('Q: Quit program')
    return

def ScanSouthSky():
        #DIMX = input("X length: ")
    #DIMX = float(DIMX)
    #DIMY = input("Y length: ")
    #DIMY = float(DIMY)
    DIM = 180
    DIMF = float(DIM)
    ONE = 1
    ONEF = float(ONE)
    Ac = 90
    Acf = float(Ac)
    Ec = 80
    Ecf = float(Ec)
    
    GoTo(azG=Acf,elG=Ecf)
    
    #Saz = float(mrtstate.state['azDeg'][0])
    #Sel = float(mrtstate.state['elDeg'][0])
    az = np.array([])
    el = np.array([])
    pwr = np.array([])
    #if ((Saz >=89.5 and Saz <= 90.5) and (Sel >=79.5 and Sel<= 80.5)):
            #az = np.array([])
            #el = np.array([])
            #pwr = np.array([])
    for i in np.arange(42):
        print (i,'of 42')
        StdCmd(ser,AZIMUTH)
        StdCmd(ser,REVERSE)
        d= Scan(ser,DIMF)
        #plt.subplot(10,1,i+1)
        #plt.plot(d['azDeg'],d['pwr'])
        az = np.append(az,d['azDeg'])
        el = np.append(el,d['elDeg'])
        pwr = np.append(pwr,d['pwr'])
        StdCmd(ser,ELEVATION)
        StdCmd(ser,REVERSE)
        d = Scan(ser,ONEF)
        StdCmd(ser,AZIMUTH)
        StdCmd(ser,FORWARD)
        d = Scan(ser,DIMF)
        #plt.subplot(10,1,i+1)
        #plt.plot(d['azDeg'],d['pwr'])
        az = np.append(az,d['azDeg'])
        el = np.append(el,d['elDeg'])
        pwr = np.append(pwr,d['pwr'])
        StdCmd(ser,ELEVATION)
        StdCmd(ser,REVERSE)
        d = Scan(ser, ONEF)

    #plt.show()
    plt.figure(2,figsize=(8,4))
    plt.clf()
    eli = np.linspace(az.min(),az.max(),180)
    azi = np.linspace(el.min(),el.max(),80)
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
    
    print('Final State')
    PrintState()
                
    return