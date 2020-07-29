import os
import sys
#import tkinter as tk
#from tkinter import ttk, scrolledtext

from matplotlib import pyplot as plt
from matplotlib import style
#from matplotlib.backends._backend_tk import NavigationToolbar2Tk
#from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
#from matplotlib.ticker import MaxNLocator

import serial
import numpy as np
#import healpy as hp
import astropy as ap
import matplotlib.pyplot as plt
import time
from scipy.interpolate import griddata

debug = True


'''
Telescope Movement Commands
(Adapted from RepRap G-Code)
[] = Optional Parameters
G0 A### E### - Rapid Movement (Manual Control)
G1 A### E### F### S### - Programmed Movement (Scan/Map)
G28 [A E] (Select Axis to Home) - Home
G90 - Use Absolute Angles
G91 - Use Relative Angles
G92 A### E### - Set Current Position
M18 - Disable Motors
M84 S### - Disable after S seconds of inactivity
M105 - Report Current Readings
M114 - Report Current Position
M350 Ann Enn - Microstepping Mode (Full - 1/16) nn:(1, 2, 4, 8, 16)
N#### - Line Number of G-Code Sent
'''

baud = 115200
nIDBytes = 18

EOT = b'ZZZ\r\n'
# BTX = 'AAA\r\n'
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
DISABLE = b'D'

eloff = 0.
azoff = -180.

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
              'heading'
              ]

state_dtypes = ['<U16',  # 'string',
                'float64',
                'int64',
                'float64',
                'int64',
                '<U16',  # 'string',,
                '<U16',  # 'string',
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
                'float64'
                ]

state = {}
for state_var in state_vars:
    state[state_var] = []

offsets = {'azoff': 0.0,
           'eloff': 0.0}

offsets['eloff'] = 0.
offsets['azoff'] = -180.


def portList(portDirectory='/dev'):  # Finds possible ports for your OS
    linuxPortPrefix = 'tty'
    macOSPortPrefix = 'cu.usbmodem'
    ports = []

    # Functions
    def portSearch(portPrefix):
        for file in os.listdir(portDirectory):
            if file.startswith(portPrefix):
                ports.append(os.path.join(portDirectory, file))

    # Logic
    if sys.platform.startswith('linux'):
        portSearch(linuxPortPrefix)
    elif sys.platform.startswith('darwin'):
        portSearch(macOSPortPrefix)

    # Debug
    if debug:
        print('DEBUG: The following are possible Arduino ports: ')
        
        print('DEBUG: ' + str(ports))

    return ports


def serialConnect(port, baudrate):
    global ser
    ser = serial.Serial(port, baudrate)
    FlushSerialBuffers(ser)
    ResetArduinoUno(ser, timeout=15, nbytesExpected=nIDBytes)


def cmdMap():
    cs = StdCmd(ser, REPORT_STATE)
    # az,el,pwr,mp,azi,eli = mrtf.RasterMap()
    # Update the current state
    current_state = state
    # mrtf.PrintState()
    RasterMap()
    current_state = StdCmd(ser, REPORT_STATE)


def cmdGo():
    cs = StdCmd(ser, REPORT_STATE)
    current_state = state
    GoTo()
    current_state = StdCmd(ser, REPORT_STATE)


def cmdCurrentState():
    PrintState()


def cmdGoAzimuth():
    cs = StdCmd(ser, REPORT_STATE)
    current_state = state
    GoAz()
    current_state = StdCmd(ser, REPORT_STATE)


def cmdGoElevation():
    cs = StdCmd(ser, REPORT_STATE)
    current_state = state
    GoEl()
    current_state = StdCmd(ser, REPORT_STATE)


def cmdScan():
    ser.write(SCAN)
    deg = input("Enter number of degrees to turn: ")
    print("Sending " + deg)
    ser.write(str.encode(deg))
    print("Reading data")
    ndata = readStream(ser)
    current_state = readState(ser)
    PrintState()
    # Convert
    # ndata = numpyState(ndata)
    # Save
    np.savez(file=time.ctime().replace(' ', '_') + '.npz',
             ndata=ndata)
    # Plot
    PlotData(ndata)


def cmdEnable():
    ser.write(ENABLE)
    current_state = StdCmd(ser, REPORT_STATE)


def cmdDisable():
    ser.write(DISABLE)
    current_state = StdCmd(ser, REPORT_STATE)


def cmdDirection(direction):
    if direction == 'CCW':
        StdCmd(ser, AZIMUTH)
        StdCmd(ser, ENABLE)
        StdCmd(ser, FORWARD)
    elif direction == 'CW':
        StdCmd(ser, AZIMUTH)
        StdCmd(ser, ENABLE)
        StdCmd(ser, REVERSE)
    elif direction == 'UP':
        StdCmd(ser, ELEVATION)
        StdCmd(ser, ENABLE)
        StdCmd(ser, FORWARD)
    elif direction == 'DOWN':
        StdCmd(ser, ELEVATION)
        StdCmd(ser, ENABLE)
        StdCmd(ser, REVERSE)


def cmdSetPosition():
    PrintState()
    newaz = float(input("New azimuth: "))
    # print('Current azimuth', mrtstate.state['azDeg'])
    curr_azoff = offsets['azoff']
    # print('Current offset', curr_azoff)
    arduino_az = state['azDeg'] + curr_azoff
    offsets['azoff'] = arduino_az - newaz
    # print(mrtf.azoff)
    newel = float(input("New elevation: "))
    curr_eloff = offsets['eloff']
    arduino_el = state['elDeg'] + curr_eloff
    offsets['eloff'] = arduino_el - newel
    current_state = StdCmd(ser, REPORT_STATE)
    PrintState()


''' Functions '''


def WaitForInputBytes(timeout=10, nbytesExpected=1):
    """ Wait for bytes to appear on the input serial buffer up to the timeout
    specified, in seconds """
    bytesFound = False
    t0 = time.time()
    dt = time.time() - t0
    while (not bytesFound and dt < timeout):
        nbytes = ser.inWaiting()
        if nbytes == nbytesExpected:
            bytesFound = True
        dt = time.time() - t0
    return nbytes, dt


def ResetArduinoUno(ser, timeout=10, nbytesExpected=1):
    """Reset the Arduino to clear previous data"""
    ser.setDTR(False)
    time.sleep(1)
    ser.setDTR(True)
    nbytes, dt = WaitForInputBytes(nbytesExpected=nbytesExpected)
    print(nbytes, 'bytes found after', dt, 'seconds')
    return


def FlushSerialBuffers(ser):
    """Flush previous data out of the buffers"""
    ser.flushInput()
    ser.flushOutput()
    return


def initState():
    """ Initialize a dictionary to hold the state """
    state = {}
    for state_var in state_vars:
        state[state_var] = []
    return state


def numpyState(state):
    """Get the state going"""
    ndata = {}
    for i in np.arange(len(state_vars)):
        ndata[state_vars[i]] = np.array(state[state_vars[i]],
                                        dtype=state_dtypes[i])
    ndata['pwr'] = zx47_60(ndata['voltage'])
    # Both readState and readStream run through here.
    # Apply offsets
    ndata['azDeg'] = np.round(np.mod(-ndata['azDeg'] - offsets['azoff'], 360), 3)
    ndata['elDeg'] = np.round(ndata['elDeg'] - offsets['eloff'], 3)
    return ndata


def parseState(buffer, state):
    """ Take the raw string returned by the Arduino ("buffer") for the current state,
    and parse it into the state dictionary defined by the state_vars """
    vars = buffer[0].split()
    # assert len(buf[0].split()) == len(state_vars)
    if len(vars) != len(state_vars):
        print('Cannot parse the returned state')
        FlushSerialBuffers(ser)
        state = state  # initState()
    else:
        for i, var in enumerate(vars):
            state[state_vars[i]].append(var)
    return state


def readState(ser, init=None):
    """Initialize the dictionary, unless a previous state is passed in"""
    if init == None:
        data = initState()
    else:
        data = init
    buf = read_ser_buffer_to_eot(ser)
    data = parseState(buf, data)
    ndata = numpyState(data)
    state = ndata
    return ndata


def readStream(ser):
    """ Generalize read_data to read an arbitrary list """
    data = initState()
    # Begin reading serial port
    buf = read_ser_buffer_to_eot(ser)  # ser.readline()
    # print('1 BUFFER', buf[0])
    # Read anything you see until you see BDTX
    while (buf[0] != BDTX):
        buf = read_ser_buffer_to_eot(ser)  # ser.readline()
        # print('2 BUFFER:', buf[0])
    # Then read states
    while (buf[0] != EDTX):
        buf = read_ser_buffer_to_eot(ser)
        if (buf[0] != EDTX):
            # print(buf[0])
            data = parseState(buf, data)
    ndata = numpyState(data)
    # StdCmd(ser,REPORT_STATE)
    return ndata


def StdCmd(ser, cmd):
    """Use instead of writing ser.write all the time"""
    ser.write(cmd)
    return readState(ser)


def PrintState():
    """ Make a pretty version of the current state """
    print('AZ:', state['azDeg'][0], 'EL:', state['elDeg'][0])
    print('Current axis:', state['axis'][0])
    return


def read_ser_buffer_to_eot(ser):
    output = []
    buf = ser.readline()
    while (buf != EOT):
        output.append(buf)
        # print(buf[:-1])
        buf = ser.readline()
    return output


def Scan(ser, deg):
    """Scan a specified number of degrees on the current axis in the current direction"""
    StdCmd(ser, ENABLE)
    ser.write(SCAN)
    # The round statement is necessary to prevent a problem with interpretation
    # by the Arduino when converted to an ASCII string.
    # Is it possible to send floats directly to the Arduino?
    deg_str = str.encode(str(np.round(deg, 3)))
    ser.write(deg_str)
    data = readStream(ser)
    # StdCmd(ser,REPORT_STATE)
    return data


def PlotData(ndata):
    """Plot the data for the Scan function"""
    plt.figure(1, figsize=(10, 7))
    plt.clf()
    # plt.subplot(311)
    if (ndata['axis'][0] == 'L'):
        x = ndata['elDeg']
    if (ndata['axis'][0] == 'A'):
        x = ndata['azDeg']
    plt.plot(x, ndata['pwr'])
    plt.xlabel('Angle (degrees)')
    plt.ylabel(r'Power ($\mu$W)')
    # plt.subplot(312)
    # plt.plot(ndata['ax'],label='ax')
    # plt.plot(ndata['ay'],label='ay')
    # plt.plot(ndata['az'],label='az')
    # plt.legend()
    # plt.subplot(313)
    # plt.plot(ndata['mx'],label='mx')
    # plt.plot(ndata['my'],label='my')
    # plt.plot(ndata['mz'],label='mz')
    # plt.legend()
    # plt.plot(x,np.convolve(pwr, np.ones((N,))/N, mode='same'),'r')
    plt.show()
    return


def GoTo(azG=None, elG=None):
    """Travel to a specified azimuth and elevation"""
    # user inputs for coordinates
    if azG == None:
        azG = input("Az: ")
        azG = float(azG)
    if elG == None:
        elG = input("El: ")
        elG = float(elG)
    d_az = azG - float(state['azDeg'][0])
    d_el = elG - float(state['elDeg'][0])
    print('d_az: ', d_az)
    print('d_el: ', d_el)
    # check to make sure it's clear to move
    if (azG >= 0. and azG <= 360.):
        az_ok = True
    else:
        print('Requested azimuth out of bounds')
        var = input("Are you sure? (Y/N) ")
        if var == 'Y':
            az_ok = True
        else:
            az_ok = False
    if (elG >= -offsets['eloff'] and elG <= 120.):
        el_ok = True
    else:
        print('Requested elevation out of bounds')
        var = input("Are you sure? (Y/N) ")
        if var == 'Y':
            el_ok = True
        else:
            el_ok = False

    # Move
    if (az_ok and el_ok):
        # Do the azimuth move
        StdCmd(ser, AZIMUTH)
        StdCmd(ser, ENABLE)
        print('Azimuth move starting')
        PrintState()
        if d_az < 0:
            # If moving to a less positive azimuth, go CCW
            StdCmd(ser, FORWARD)
        else:
            StdCmd(ser, REVERSE)
        Scan(ser, np.abs(d_az))
        # Elevation move
        StdCmd(ser, ELEVATION)
        StdCmd(ser, ENABLE)
        print('Elevation move starting')
        PrintState()
        if d_el < 0:
            StdCmd(ser, REVERSE)
        else:
            StdCmd(ser, FORWARD)
        Scan(ser, np.abs(d_el))
        StdCmd(ser, DISABLE)
        StdCmd(ser, AZIMUTH)
        StdCmd(ser, ENABLE)
        print('Final state')
        PrintState()
    return


def GoAz(azGa=None):
    """Go to a specific Azimuth without changing elevation"""
    if azGa == None:
        azGa = input("Az: ")
        azGa = float(azGa)
    d_azga = azGa - float(state['azDeg'][0])
    print('d_az: ', d_azga)
    if (azGa >= 0. and azGa <= 360.):
        az_ok = True
    else:
        print('Requested azimuth out of bounds')
        var = input("Are you sure? (Y/N) ")
        if var == 'Y':
            az_ok = True
        else:
            az_ok = False

    # move
    if (az_ok):
        StdCmd(ser, AZIMUTH)
        StdCmd(ser, ENABLE)
        print('Azimuth move starting')
        PrintState()
        if d_azga < 0:
            # If moving to a less positive azimuth, go CCW
            StdCmd(ser, FORWARD)
        else:
            StdCmd(ser, REVERSE)
        print(str(np.abs(d_azga)))
        Scan(ser, np.abs(d_azga))
        print('Azimuth move ended at')
        PrintState()
        print('Final state')
        PrintState()
    return


def GoEl(elGe=None):
    """Go to a specific elevation without changing azimuth"""
    if elGe == None:
        elGe = input("El: ")
        elGe = float(elGe)
    d_elge = elGe - float(state['elDeg'][0])
    print('d_el: ', d_elge)
    if (elGe >= -offsets['eloff'] and elGe <= 120.):
        el_ok = True
    else:
        print('Requested elevation out of bounds')
        var = input("Are you sure? (Y/N) ")
        if var == 'Y':
            el_ok = True
        else:
            el_ok = False
    # move
    if (el_ok):
        StdCmd(ser, ELEVATION)
        StdCmd(ser, ENABLE)
        print('Elevation move starting')
        PrintState()
        if d_elge < 0:
            StdCmd(ser, REVERSE)
        else:
            StdCmd(ser, FORWARD)
        print(str(np.abs(d_elge)))
        Scan(ser, np.abs(d_elge))
        StdCmd(ser, DISABLE)
        print('Elevation move ended at')
        PrintState()
        print('Final state')
        PrintState()
    return


def RasterMap():
    """Make a map centered at a given point, with given dimensions"""
    # center point input
    azG = input("Az: ")
    azG = float(azG)
    elG = input("El: ")
    elG = float(elG)
    # dimensions input
    DIMA = input("Azimuth Dimension: ")
    DIMAF = float(DIMA)
    ONE = 1.0
    ONEF = float(ONE)
    DIME = input("Elevation Dimension: ")
    DIMEF = float(DIME)
    DIMEI = int(DIME) / 2
    azM = azG - DIMAF / 2.
    elM = elG + DIMEI
    # determine figure size based on inputs
    if (DIMAF < DIMEF):
        x = 8
        y = (DIMEF / DIMAF) * 8
    elif (DIMAF > DIMEF):
        x = (DIMAF / DIMEF) * 8
        y = 8
    else:
        x = 8
        y = 8
    # Calculate approximate time to completion
    AZT = DIMAF * .35 * DIMEF
    ELT = DIMEF
    TT = (AZT + ELT) / 60

    # move to starting point
    GoTo(azG=azM, elG=elM)

    # plt.figure(1)
    # plt.clf()
    # collect data
    az = np.array([])
    el = np.array([])
    pwr = np.array([])
    print('Aproximate time to completion: ', TT, ' minutes')
    for i in np.arange(DIMEI):
        print(i, 'of ', DIMEI)
        StdCmd(ser, AZIMUTH)
        StdCmd(ser, REVERSE)
        d = Scan(ser, DIMAF)
        # plt.subplot(10,1,i+1)
        # plt.plot(d['azDeg'],d['pwr'])
        az = np.append(az, d['azDeg'])
        el = np.append(el, d['elDeg'])
        pwr = np.append(pwr, d['pwr'])
        StdCmd(ser, ELEVATION)
        StdCmd(ser, ENABLE)
        StdCmd(ser, REVERSE)
        d = Scan(ser, ONEF)
        StdCmd(ser, DISABLE)
        StdCmd(ser, AZIMUTH)
        StdCmd(ser, FORWARD)
        d = Scan(ser, DIMAF)
        # plt.subplot(10,1,i+1)
        # plt.plot(d['azDeg'],d['pwr'])
        az = np.append(az, d['azDeg'])
        el = np.append(el, d['elDeg'])
        pwr = np.append(pwr, d['pwr'])
        StdCmd(ser, ELEVATION)
        StdCmd(ser, ENABLE)
        StdCmd(ser, REVERSE)
        d = Scan(ser, ONEF)
        StdCmd(ser, DISABLE)

    # plot data
    plt.figure(2, figsize=(x, y))
    plt.clf()
    eli = np.linspace(az.min(), az.max(), DIMAF)
    azi = np.linspace(el.min(), el.max(), DIMEF)
    # grid the data.
    zi = griddata((az, el), pwr, (eli[None, :], azi[:, None]), method='nearest')
    # contour the gridded data
    np.savez(file='map_' + time.ctime().replace(' ', '_') + '.npz',
             az=az, el=el, pwr=pwr, zi=zi, azi=azi, eli=eli)

    plt.imshow(np.flipud(zi), aspect='auto', cmap=plt.cm.jet,
               extent=[eli.min(), eli.max(), azi.min(), azi.max()])
    plt.colorbar()
    # CS = plt.contour(zi,5,linewidths=1,colors='w')
    plt.contour(eli, azi, zi, 5, linewidths=1, colors='w')
    # CS = plt.contourf(eli,azi,zi,10,cmap=plt.cm.jet)
    plt.axis('equal')
    plt.xlabel('Azimuth (degrees)')
    plt.ylabel('Elevation (degrees)')
    plt.savefig(time.ctime().replace(' ', '_') + '.png')
    plt.show()
    print('Final State')
    PrintState()

    return (az, el, pwr, zi, azi, eli)


def PrintMenu():
    """ Provide the user the available commands """
    print('A: Set Azimuth')
    print('L: Set Elevation')
    print('E: Enable')
    print('D: Disable')
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
    """Scan the entire south sky, except between 80 and 90 degrees for elevation limited by telescope design"""
    # define and convert variables for input to the scan function
    DIM = 180
    DIMF = float(DIM)
    ONE = 1
    ONEF = float(ONE)
    # starting point of scan
    Ac = 90
    Acf = float(Ac)
    Ec = 80
    Ecf = float(Ec)
    GoTo(azG=Acf, elG=Ecf)

    # start data collection
    az = np.array([])
    el = np.array([])
    pwr = np.array([])

    for i in np.arange(42):
        print(i, 'of 42')
        StdCmd(ser, AZIMUTH)
        StdCmd(ser, REVERSE)
        d = Scan(ser, DIMF)
        az = np.append(az, d['azDeg'])
        el = np.append(el, d['elDeg'])
        pwr = np.append(pwr, d['pwr'])
        StdCmd(ser, ELEVATION)
        StdCmd(ser, REVERSE)
        d = Scan(ser, ONEF)
        StdCmd(ser, AZIMUTH)
        StdCmd(ser, FORWARD)
        d = Scan(ser, DIMF)
        az = np.append(az, d['azDeg'])
        el = np.append(el, d['elDeg'])
        pwr = np.append(pwr, d['pwr'])
        StdCmd(ser, ELEVATION)
        StdCmd(ser, REVERSE)
        d = Scan(ser, ONEF)

    # plot data
    plt.figure(2, figsize=(18, 8))
    plt.clf()
    eli = np.linspace(az.min(), az.max(), 180)
    azi = np.linspace(el.min(), el.max(), 80)
    # grid the data.
    zi = griddata((az, el), pwr, (eli[None, :], azi[:, None]), method='nearest')
    # contour the gridded data
    np.savez(file='map_' + time.ctime().replace(' ', '_') + '.npz',
             az=az, el=el, pwr=pwr, zi=zi, azi=azi, eli=eli)

    plt.imshow(np.flipud(zi), aspect='auto', cmap=plt.cm.jet,
               extent=[eli.min(), eli.max(), azi.min(), azi.max()])
    plt.colorbar()
    # CS = plt.contour(zi,5,linewidths=1,colors='w')
    plt.contour(eli, azi, zi, 5, linewidths=1, colors='w')
    # CS = plt.contourf(eli,azi,zi,10,cmap=plt.cm.jet)
    plt.axis('equal')
    plt.xlabel('Azimuth (degrees)')
    plt.ylabel('Elevation (degrees)')
    plt.savefig(time.ctime().replace(' ', '_') + '.png')
    plt.show()

    print('Final State')
    PrintState()

    return


def W2dBm(W):
    return 10. * np.log10(W / 1e-3)


def zx47_60(v):
    """ Calibration curve for the Mini-Circuits ZX47-60(LN)+ power detector"""
    dBm = -50 / (1.8 - 0.6) * (v - 0.6)
    W = np.power(10, dBm / 10.) * 1e-3
    return W * 1e6

