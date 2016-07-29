import serial
import numpy as np
import pylab as plt
import time
import MRTtools as mrt

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

port='/dev/cu.usbmodem1411'
baud = 9600 # 9600
EOT = 'ZZZ\r\n'
BTX = 'AAA\r\n'

# Open the port
ser = serial.Serial(port, baud)
operate = True

# Initially clear out the buffer
dummy = read_ser_buffer_to_eot() 
#clear_ser_buffer()
print ser.inWaiting()

while(operate):
    #print_ser_buffer()
    var = raw_input("Enter command to transmit, Q to quit: ")
    if not var == 'Q':
        print "Sending "+var
        ser.write(var)
        if (var == 'a'):
            dummy = read_ser_buffer_to_eot()
            for i,d in enumerate(dummy):
                dummy[i] = float(d.strip())
            toplot = np.array(dummy)
            plt.figure(1)
            plt.clf()
            plt.plot(toplot,'o')
            #plt.draw()
            plt.show(block=False)
        else:
        # Read back any reply
            dummy = read_ser_buffer_to_eot()
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
    else:
        operate = False

ser.close()
    
