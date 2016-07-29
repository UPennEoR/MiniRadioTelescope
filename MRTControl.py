import serial
#import arduinoserial
import time
import MRTtools as mrt

port='/dev/cu.usbmodem1411'
baud = 9600 # 9600
EOT = 'ZZZ\r\n'
BTX = 'AAA\r\n'
#EOT = '\r\n'

#arduino = arduinoserial.SerialPort(port,baud)

# Open the port
ser = serial.Serial(port, baud)

operate = True

def print_ser_buffer_to_eot():
    buffer = ""
    buffer = ser.readline()
    while(buffer != EOT):
        print buffer
        buffer = ser.readline()
    return

def read_ser_buffer_to_eot():
    output = []
    buffer = ser.readline()
    while(buffer != EOT):
        output.append(buffer)
        print buffer
        buffer = ser.readline()
    return output
    
def read_tel_data():
    az = []
    el = []
    pw = []
    buf = ser.readline()
    # Clear initial stuff
    while(buf != BTX):
        buf=ser.readline()
    while(buf != EOT):
        buf=ser.readline()
        a,e,p = buf.split()
        az.append(a)
        el.append(e)
        pw.append(p)
    az = np.array(az,dtype='float64')
    el = np.array(el,dtype='float64')
    pw = np.array(p,dtype='float64')
    pw = mrt.zx47_60(pw)
    return (az,el,pw)

def print_ser_buffer():
    while (ser.inWaiting() != 0):
        print ser.readline()
    return

while(operate):
    #if (ser.inWaiting() != 0):
    dummy = read_ser_buffer_to_eot() # Supposedly, clear out the buffer
    #print_ser_buffer()
    var = raw_input("Enter command to transmit, Q to quit: ")
    if not var == 'Q':
        if var == 'C':
            axis = raw_input("First, enter axis: ")
            print "Sending "+axis
            time.sleep(1)
            print "Sending "+"S"
            ser.write('S')
            deg = raw_input("Enter number of degrees: ")
            print "Sending "+deg
            ser.write(deg)
            #az,el,pw = read_tel_data()
            az = []
            el = []
            pw = []
            buf = ser.readline()
            print buf
            # Clear initial stuff
            while(buf != BTX):
                buf=ser.readline()
                print buf
            while(buf != EOT):
                buf=ser.readline()
                a,e,p = buf.split()
                az.append(a)
                el.append(e)
                pw.append(p)
            az = np.array(az,dtype='float64')
            el = np.array(el,dtype='float64')
            pw = np.array(p,dtype='float64')
            pw = mrt.zx47_60(pw)
            #print values
        else:
            print "Sending "+var
            ser.write(var)
            # Read back any reply
            dummy = read_ser_buffer_to_eot()
    else:
        operate = False

ser.close()
    
