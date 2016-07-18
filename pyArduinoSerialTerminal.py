import serial
import arduinoserial

port='/dev/cu.usbmodem1451'
baud = 115200 # 9600
#EOT = 'XXX\r\n'
EOT = '\r\n'

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
        buffer = ser.readline()
    return output
    
while(operate):
    if (ser.inWaiting() != 0):
        print_ser_buffer_to_eot() # Clear out the buffer
    var = raw_input("Enter command to transmit, Q to quit: ")
    if not var == 'Q':
        if var == 'C':
            read_ser_buffert_to_eot()
        else:
            print "Sending "+var
            ser.write(var)
            print_ser_buffer_to_eot()
    else:
        operate = False

ser.close()
    
