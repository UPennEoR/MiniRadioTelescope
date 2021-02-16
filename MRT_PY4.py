'''This is the current working version of the MRT control as of 2/16/2021

It needs to work with MRTv2.ino, for which the last major update was
to add the shift register code.

'''

import numpy as np
#import healpy as hp
import astropy as ap
import time
import mrtstate
import MRT_FUNC_PY4 as mrtf

#%
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
print ('Before flushing buffers')
print ('Bytes in waiting', ser.inWaiting())
mrtf.FlushSerialBuffers(ser)
print ('After flushing buffers')
print ('Bytes in waiting', ser.inWaiting())
print ('Resetting Arduino')
print ('Before reset')
print ('Bytes in waiting', ser.inWaiting())
mrtf.ResetArduinoUno(ser,timeout=15,nbytesExpected=mrtf.nIDBytes)
# I don't understand why ARDUINO MRT is 18 bytes ...
print ('After reset')
print ('Bytes in waiting', ser.inWaiting())
print (ser.inWaiting())

output = mrtf.read_ser_buffer_to_eot(ser)
print(output)
#%%

# For the nominal mounting in the observatory
#eloff = 35.5
#azoff = -191.
# For a general setup facing south
#eloff = 35.5
#azoff = -180.
# Just start at zero
mrtstate.offsets['eloff'] = 0.
mrtstate.offsets['azoff'] = -180.

print(mrtstate.offsets)

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
    var = input("Enter command to transmit, H for help, Q to quit: ")
    if not var == 'Q':
        if (var == 'M'): # Make a map!
            cs = mrtf.StdCmd(ser,mrtf.REPORT_STATE)
            #az,el,pwr,mp,azi,eli = mrtf.RasterMap()
            # Update the current state
            current_state = mrtstate.state
            #mrtf.PrintState()
            mrtf.RasterMap()
            current_state =  mrtf.StdCmd(ser,mrtf.REPORT_STATE)
        elif (var == 'MS'): # Make a map of the South Sky
            cs = mrtf.StdCmd(ser,mrtf.REPORT_STATE)
            #az,el,pwr,mp,azi,eli = mrtf.ScanSouthSky(cs)
            # Update the current state
            current_state = mrtstate.state
            mrtf.ScanSouthSky()
            current_state =  mrtf.StdCmd(ser,mrtf.REPORT_STATE)
        elif (var == 'G'):
            cs = mrtf.StdCmd(ser,mrtf.REPORT_STATE)
            current_state = mrtstate.state
            mrtf.GoTo()
            current_state =  mrtf.StdCmd(ser,mrtf.REPORT_STATE)
        elif (var == 'H'):
            mrtf.PrintMenu()
        elif (var == 'CS'):
            #print(mrtstate.state)
            mrtf.PrintState()
        elif (var == 'GA'):
            cs = mrtf.StdCmd(ser,mrtf.REPORT_STATE)
            current_state = mrtstate.state
            mrtf.GoAz()
            current_state =  mrtf.StdCmd(ser,mrtf.REPORT_STATE)
        elif (var == 'GE'):
            cs = mrtf.StdCmd(ser,mrtf.REPORT_STATE)
            current_state = mrtstate.state
            mrtf.GoEl()
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
        elif (var == 'E'):
            print ("Sending "+var)
            ser.write(mrtf.ENABLE)
            current_state =  mrtf.StdCmd(ser,mrtf.REPORT_STATE)
        elif (var == 'D'):
            print ("Sending "+var)
            ser.write(mrtf.DISABLE)
            current_state =  mrtf.StdCmd(ser,mrtf.REPORT_STATE)
        elif (var == 'ETGOHOME'):
            print ("Sending "+var)
            mrtf.ETGOHOME()
            mrtf.PrintState()
            newel = float(0.0)
            curr_eloff = mrtstate.offsets['eloff']
            arduino_el = mrtstate.state['elDeg'] + curr_eloff
            mrtstate.offsets['eloff'] = arduino_el - newel
            current_state =  mrtf.StdCmd(ser,mrtf.REPORT_STATE)
            mrtf.PrintState()
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
        elif (var == 'CCW'):
            mrtf.StdCmd(ser, mrtf.AZIMUTH)
            mrtf.StdCmd(ser, mrtf.ENABLE)
            mrtf.StdCmd(ser, mrtf.FORWARD)
        elif (var == 'CW'):
            mrtf.StdCmd(ser, mrtf.AZIMUTH)
            mrtf.StdCmd(ser, mrtf.ENABLE)
            mrtf.StdCmd(ser, mrtf.REVERSE)
        elif (var == 'UP'):
            mrtf.StdCmd(ser, mrtf.ELEVATION)
            mrtf.StdCmd(ser, mrtf.ENABLE)
            mrtf.StdCmd(ser, mrtf.FORWARD)
        elif (var == 'DOWN'):
            mrtf.StdCmd(ser, mrtf.ELEVATION)
            mrtf.StdCmd(ser, mrtf.ENABLE)
            mrtf.StdCmd(ser, mrtf.REVERSE)
        elif (var == 'SETPOS'):
            mrtf.PrintState()
            newaz = float(input("New azimuth: "))
            #print('Current azimuth', mrtstate.state['azDeg'])
            curr_azoff = mrtstate.offsets['azoff']
            #print('Current offset', curr_azoff)
            arduino_az = mrtstate.state['azDeg'] + curr_azoff
            mrtstate.offsets['azoff'] = arduino_az - newaz 
            #print(mrtf.azoff)
            newel = float(input("New elevation: "))
            curr_eloff = mrtstate.offsets['eloff']
            arduino_el = mrtstate.state['elDeg'] + curr_eloff
            mrtstate.offsets['eloff'] = arduino_el - newel
            current_state =  mrtf.StdCmd(ser,mrtf.REPORT_STATE)
            mrtf.PrintState()
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
        else:
            # Commands that get passed along
            print("Sending command direct to Arduino")
            print ("Sending "+var)
            ser.write(str.encode(var))
            # Read back any reply
            #read_ser_buffer_to_eot(ser)
            current_state = mrtf.readState(ser)
            mrtf.PrintState()
    else:
        operate = False

ser.close()
