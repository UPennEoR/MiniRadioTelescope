# verified 1 April 2017: working

import serial
import numpy as np
import matplotlib.pyplot as plt
import time
import MRTtools as mrt

# Don't yet have a good way of auto-detecting which port is Arduino
#port='/dev/cu.usbmodem1421'
port='/dev/cu.usbmodem1411'
#port = '/dev/ttyACM0'
baud = 115200
nIDBytes = 18

EOT = 'ZZZ\r\n'
#BTX = 'AAA\r\n'
BDTX = 'BDTX\r\n'
EDTX = 'EDTX\r\n'

def StdCmd(ser,cmd):
    ser.write(cmd)
    return readState(ser)

def Scan(ser,deg):
    ser.write('S')
    ser.write(deg)
    data = readStream(ser)
    current_state = readState(ser)
    return data

def RasterMap():
    """ Super hard coded to get something going.  Start where you are, and
    make a 20 x 20 degree map """
    plt.figure(1)
    plt.clf()
    map = np.zeros([20,20])
    az = np.array([])
    el = np.array([])
    pwr = np.array([])
    for i in np.arange(10):
        cs = StdCmd(ser,'A')
        cs = StdCmd(ser,'R')
        d = Scan(ser,'20')
        plt.subplot(10,1,i+1)
        plt.plot(d['azDeg'],d['pwr'])
        az = np.append(az,d['azDeg'])
        el = np.append(el,d['elDeg'])
        pwr = np.append(pwr,d['pwr'])
        cs = StdCmd(ser,'L')
        cs = StdCmd(ser,'R')
        d = Scan(ser,'1')
        cs = StdCmd(ser,'A')
        cs = StdCmd(ser,'F')
        d = Scan(ser,'20')
        plt.subplot(10,1,i+1)
        plt.plot(d['azDeg'],d['pwr'])
        az = np.append(az,d['azDeg'])
        el = np.append(el,d['elDeg'])
        pwr = np.append(pwr,d['pwr'])
        cs = StdCmd(ser,'L')
        cs = StdCmd(ser,'R')
        d = Scan(ser,'1')
    plt.show()
    return (az,el,pwr)
        
# Best practices for opening the serial port with reset
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
    print nbytes,'bytes found after',dt,'seconds'
    return

def FlushSerialBuffers(ser):
    ser.flushInput()
    ser.flushOutput()
    return

""" This will be the fundamental list of returned values that has to be kept
in sync with the Arduino.  Can't build a dictionary, because need to preserve 
the order of items read """
state_vars = ['lastCMDvalid',
              'elDeg',
              'elSteps',
              'azDeg',
              'azSteps',
              'axis',
              'mode',
              'sense',
              'elEnable',
              'azEnable',
              'voltage',
              'ax',
              'ay',
              'az',
              'mx',
              'my',
              'mz',
              'pitch',
              'roll',
              'heading']

state_dtypes=['string',
              'float64',
              'int64',
              'float64',
              'int64',
              'string',
              'string',
              'int64',
              'int',
              'int',
              'float64',
              'float64',
              'float64',
              'float64',
              'float64',
              'float64',
              'float64',
              'float64',
              'float64',
              'float64']
              
def read_ser_buffer_to_eot(ser):
    output = []
    buf = ser.readline()
    while(buf != EOT):
        output.append(buf)
        #print buf[:-1]
        buf = ser.readline()
    return output

def initState():
    """ Initialize a dictionary to hold the state """
    state = {}
    for state_var in state_vars:
        state[state_var] = []
    return state
        
def parseState(buf,data):
    vars = buf[0].split()
    assert len(buf[0].split()) == len(state_vars)
    for i,var in enumerate(vars):
         data[state_vars[i]].append(var)
    return data

def readState(ser,init=None):
    # Initialize the dictionary, unless a previous state is passed in
    if init == None:
        data = initState()
#        data = {}
#        for state_var in state_vars:
#            data[state_var] = []
    else:
        data = init
    buf = read_ser_buffer_to_eot(ser)
    #print buf
    #print len(state_vars)
    #print len(buf[0].split())
    #vars = buf[0].split()
    #assert len(buf[0].split()) == len(state_vars)
    #for i,var in enumerate(vars):
    #     data[state_vars[i]].append(var)
    data = parseState(buf,data)
    return data

def numpyState(state):
    ndata = {}
    for i in np.arange(len(state_vars)):
        ndata[state_vars[i]] = np.array(state[state_vars[i]],
                                        dtype=state_dtypes[i])
    ndata['pwr'] = mrt.zx47_60(ndata['voltage'])
    return ndata

def read_data(ser):
    # Read what comes back until you see the "begin data transmission"
    az = []
    el = []
    pwr = []
    buf = ser.readline()
    print buf
    while (buf != BDTX):
        buf = ser.readline()
        print buf
    while(buf != EDTX):
        buf = ser.readline()
        if (buf != EDTX):
            a,e,p = buf.split()
            az.append(a)
            el.append(e)
            pwr.append(p)
        #output.append(buf)
        print buf
    #output.pop()
    az = np.array(az,dtype='float64')
    el = np.array(el,dtype='float64')
    pwr = np.array(pwr,dtype='float64')
    pwr = mrt.zx47_60(pwr)
    return (az,el,pwr)

def readStream(ser):
    """ Generalize read_data to read an arbitrary list """
    data = initState()
#    data = {}
#    for state_var in state_vars:
#        data[state_var] = []
    # Begin reading serial port
    buf = read_ser_buffer_to_eot(ser) #ser.readline()
    print '1 BUFFER', buf[0]
    # Read anything you see until you see BDTX
    while (buf[0] != BDTX):
        buf = read_ser_buffer_to_eot(ser) #ser.readline()
        print '2 BUFFER:', buf[0]
    # Then read states
    while(buf[0] != EDTX):
        buf = read_ser_buffer_to_eot(ser)
        if (buf[0] != EDTX):
            data = parseState(buf,data)
    ndata = numpyState(data)
    return ndata

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

def PrintState(state):
    """ Make a pretty version of the current state """
    print 'AZ:',state['azDeg'][0],'EL:',state['elDeg'][0]
    print 'Current axis:',state['axis'][0]
    return

# ----------------------------------------------------------------------------
# Begin
# ----------------------------------------------------------------------------
# Notify the user
print 'Opening serial port',port
print 'with baud',baud
""" For reasons unclear, the Mac appears to assert DTR on serial connection,
whereas the Pi does not.  So we will be super explicit. """
# Open the port
ser = serial.Serial(port, baud)
print 'Before flushing buffers'
print 'Bytes in waiting', ser.inWaiting()
FlushSerialBuffers(ser)
print 'After flushing buffers'
print 'Bytes in waiting', ser.inWaiting()
print
print 'Resetting Arduino'
print 'Before reset'
print 'Bytes in waiting', ser.inWaiting()
ResetArduinoUno(ser,timeout=15,nbytesExpected=nIDBytes)
# I don't understand why ARDUINO MRT is 18 bytes ...
print 'After reset'
print 'Bytes in waiting', ser.inWaiting()
print ser.inWaiting()
read_ser_buffer_to_eot(ser)

# Initialize the axis
"""
ser.write('L')
ser.write('E')
ser.write('M')
ser.write('A')
current_axis = 'az'
dummy = read_ser_buffer_to_eot(ser)
ser.write('E')
ser.write('M')
"""

eloff = 0.
azoff = 0.

""" Basic mode of operation should be that the Python side handles the user 
interface and menu, and sends groups of atomic commands.  The Arduino always
reports its state in response to any command, including whether the last 
command was valid.  Because I don't think we want to command individual steps,
but rather scans, that command is special """

operate=True
while(operate):
    var = raw_input("Enter command to transmit, Q to quit: ")
    if not var == 'Q':
        if (var == 'M'): # Make a map!
            az,el,pwr = RasterMap()
        elif (var == 'S'):
            print "Sending "+var
            ser.write(var)
            deg = raw_input("Enter number of degrees to turn: ")
            print "Sending "+deg
            ser.write(deg)
            print "Reading data"
            ndata = readStream(ser)
            current_state = readState(ser)
            PrintState(current_state)
            # Convert
            #ndata = numpyState(data)
            # Save
            #np.savez(file=time.ctime().replace(' ','_')+'.npz',az=ndata=ndata)
            # Plot
            PlotData(ndata)
        elif (var == 'X'):
            Ndatapts = raw_input("Enter number of data points: ")
            ser.write(var)
            # Initialize the data variable
            data = readState(ser)
            for i in np.arange(int(Ndatapts)-1):
                # Trick it by sending invalid commands and reading them back
                ser.write(var)
                #read_ser_buffer_to_eot(ser)
                dummy = readState(ser)
                for key in data.keys():
                    data[key].append(dummy[key][0])
            ndata = numpyState(data)
            PlotData(ndata)
        else:
            # Commands that get passed along
            print "Sending "+var
            ser.write(var)
            # Read back any reply
            #read_ser_buffer_to_eot(ser)
            current_state = readState(ser)
            PrintState(current_state)
    else:
        operate = False

ser.close()
