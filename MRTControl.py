import serial
import numpy as np
import pylab as plt
import time
import MRTtools as mrt

port='/dev/cu.usbmodem1411'
baud = 115200

EOT = 'ZZZ\r\n'
BTX = 'AAA\r\n'
BDTX = 'BDTX\r\n'
EDTX = 'EDTX\r\n'

# Open the port
print 'Opening serial port',port
print 'with baud',baud
ser = serial.Serial(port, baud)
operate = True

# Don't know why this doesn't work
def clear_ser_buffer():
    buf = []
    while (ser.inWaiting() != 0):
        buf.append(ser.read())
    print buf
    return

def read_ser_buffer_to_eot():
    output = []
    buf = ser.readline()
    while(buf != EOT):
        output.append(buf)
        print buf
        buf = ser.readline()
    return output

def read_data():
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

""" Initially clear out the buffer.  There is a delay between the initial 
serial conection and when the Arduino outputs its opening message, so you have 
to wait """
dummy = read_ser_buffer_to_eot() 

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
            az,el,pwr = read_data()
            print "Reading remaining buffer"
            dummy = read_ser_buffer_to_eot()
            plt.figure(1)
            plt.clf()
            plt.plot(az,pwr)
            plt.show()#block=False)
        else:
            # Read back any reply
            print "Default readback"
            dummy = read_ser_buffer_to_eot()
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
