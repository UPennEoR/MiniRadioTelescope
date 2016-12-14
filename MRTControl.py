# Working version as of 14 December 2016

import serial
import numpy as np
import pylab as plt
import time
import MRTtools as mrt

# Don't yet have a good way of auto-detecting which port is Arduino
port='/dev/cu.usbmodem1421'
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

def read_ser_buffer_to_eot(ser):
    output = []
    buf = ser.readline()
    while(buf != EOT):
        output.append(buf)
        print buf
        buf = ser.readline()
    return output

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

def read_data_handshake(ser):
    # Read what comes back until you see the "begin data transmission"
    val = []
    buf = ser.readline()
    print buf
    while(buf != EOT):
        while (buf != BDTX):
            buf = ser.readline()
            print buf
        while(buf != EDTX):
            buf = ser.readline()
            if (buf != EDTX):
                v = buf.strip()
                val.append(float(v))
            print buf
        print 'Got data', v
        ser.write('R')
        buf = ser.readline()
        print buf
    val = np.array(val)
    return val

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

operate=True
while(operate):
    #print_ser_buffer()
    var = raw_input("Enter command to transmit, Q to quit: ")
    if not var == 'Q':
        print "Sending "+var
        ser.write(var)
        if (var == 'S'):
            deg = raw_input("Enter number of degrees to turn: ")
            print "Sending "+deg
            ser.write(deg)
            print "Reading data"
            az,el,pwr = read_data(ser)
            print "Reading remaining buffer"
            dummy = read_ser_buffer_to_eot(ser)
            plt.figure(1)
            plt.clf()
            plt.plot(az,pwr)
            plt.show()#block=False)
#        if (var == 'n'):
#            npts = raw_input("Enter number of data points: ")
#            print "Sending "+npts
#            ser.write(npts)
#            print "Reading data"
#            val = read_data_handshake(ser)
#            print "Reading remaining buffer"
#            dummy = read_ser_buffer_to_eot()
        else:
            # Read back any reply
            print "Default readback"
            dummy = read_ser_buffer_to_eot(ser)
    else:
        operate = False

ser.close()
    
#        if var == 'C':
#            axis = raw_input("First, enter axis: ")
#            print "Sending "+axis
#            time.sleep(1)
#            print "Sending "+"S"
#            ser.write('S')
#            deg = raw_input("Enter number of degrees: ")
#            print "Sending "+deg
#            ser.write(deg)
#            #az,el,pw = read_tel_data()
#            az = []
#            el = []
#            pw = []
#            buf = ser.readline()
#            print buf
#            # Clear initial stuff
#            while(buf != BTX):
#                buf=ser.readline()
#                print buf
#            while(buf != EOT):
#                buf=ser.readline()
#                a,e,p = buf.split()
#                az.append(a)
#                el.append(e)
#                pw.append(p)
#            az = np.array(az,dtype='float64')
#            el = np.array(el,dtype='float64')
#            pw = np.array(p,dtype='float64')
#            pw = mrt.zx47_60(pw)
#            #print values
#        else:
