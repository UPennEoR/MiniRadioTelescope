# verified 1 April 2017: working

import serial
import numpy as np
import matplotlib.pyplot as plt
import time
import MRTtools as mrt

# Don't yet have a good way of auto-detecting which port is Arduino
port='/dev/cu.usbmodem1421'
#port='/dev/cu.usbmodem1411'
#port = '/dev/ttyACM0'
baud = 115200
nIDBytes = 18

EOT = 'ZZZ\r\n'
BTX = 'AAA\r\n'
BDTX = 'BDTX\r\n'
EDTX = 'EDTX\r\n'

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

""" This will be the fundamental list of returned values that has to be kept
in sync with the Arduino.  Can't build a dictionary, because need to preserve 
the order of items read """
state_vars = ['lastCMDvalid','elDeg','elSteps','azDeg','azSteps','axis','mode','sense','elEnable','azEnable','voltage','ax','ay','az','mx','my','mz','pitch','roll','heading']

def read_ser_buffer_to_eot(ser):
    output = []
    buf = ser.readline()
    while(buf != EOT):
        output.append(buf)
        print buf[:-1]
        buf = ser.readline()
    return output

# This may not be the best method, because it's so obnoxious to convert to numpy
def readState(ser):
    # Initialize the dictionary
    data = {}
    for state_var in state_vars:
        data[state_var] = []
    buf = read_ser_buffer_to_eot(ser)
    vars = buf[0].split()
    assert len(buf[0].split()) == len(state_vars)
    for i,var in enumerate(vars):
         data[state_vars[i]].append(var)
    return data

def readStream(ser):
    """ Generalize read_data to read an arbitrary list """
    # Initialize the dictionary
    for state_var in state_vars:
        data[state_var] = []
    # Begin reading serial port
    buf = ser.readline()
    #print buf
    while (buf != BDTX):
        buf = ser.readline()
    #    print buf
    while(buf != EDTX):
        buf = ser.readline()
        if (buf != EDTX):
            vars = buf.split()
            for i,var in enumerate(vars):
                # This deals with streaming data from scans
                data[state_vars[i]].append(var)
    return data


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
        if (var == 'S'):
            print "Sending "+var
            ser.write(var)
            deg = raw_input("Enter number of degrees to turn: ")
            print "Sending "+deg
            ser.write(deg)
            print "Reading data"
            az,el,pwr = read_data(ser)
            az = az + azoff
            el = el + eloff
            np.savez(file=time.ctime().replace(' ','_')+'.npz',az=az,el=el,pwr=pwr)
            plt.figure(1)
            plt.clf()
            if (current_axis == 'el'):
                x = el
            if (current_axis == 'az'):
                x = az
            plt.plot(x,pwr)
            plt.xlabel('Angle (degrees)')
            plt.ylabel(r'Power ($\mu$W)')
            #N = 10
            #plt.plot(x,np.convolve(pwr, np.ones((N,))/N, mode='same'),'r')
            plt.show()
            #print "Reading remaining buffer"
            #dummy = read_ser_buffer_to_eot(ser)
        elif (var == 'X'):
            ndata = raw_input("Enter number of data points: ")
            ser.write(var)
            data = readState(ser)
            for i in np.arange(int(ndata)-1):
                # Trick it by sending invalid commands and reading them back
                ser.write(var)
                #read_ser_buffer_to_eot(ser)
                dummy = readState(ser)
                for key in data.keys():
                    data[key].append(dummy[key][0])
        else:
            # Commands that get passed along
            print "Sending "+var
            ser.write(var)
            # Read back any reply
            #read_ser_buffer_to_eot(ser)
            data = readState(ser)
            print data
 #           data = {}
 #           for state_var in state_vars:
 #               data[state_var] = []
 #           buf = read_ser_buffer_to_eot(ser)
 #           vars = buf[0].split()
 #           print len(buf[0].split()) == len(state_vars)
 #           for i,var in enumerate(vars):
 #               data[state_vars[i]].append(var)
    else:
        operate = False

ser.close()
