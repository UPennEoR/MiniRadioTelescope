import os
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext

from matplotlib import pyplot as plt
from matplotlib import style
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import MaxNLocator

import serial
import numpy as np
import healpy as hp
import astropy as ap
import matplotlib.pyplot as plt
import time
from scipy.interpolate import griddata

debug = False

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

state_dtypes=['<U16', #'string',
              'float64',
              'int64',
              'float64',
              'int64',
              '<U16', #'string',,
              '<U16', #'string',
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


class mrtGUI(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        # self.geometry('1280x800')
        self.title('Mini Radio Telescope')

        mainTabList = (tabControl, tabScan, tabMap, tabTerminal, tabViewer)
        mainTabNames = ['Control', 'Scan', 'Map', 'Terminal', 'Viewer']
        infoTabList = (tabConnection, tabState)
        infoTabNames = ['Connection', 'State']
        filesTabList = (tabGraph, tabRawData)
        filesTabNames = ['Graphs', 'Raw Data']

        notebookMain = ttk.Notebook(self)
        notebookMain.pack(expand=1, fill='both', side='right')
        notebookInfo = ttk.Notebook(self, width=300, height=250)
        notebookInfo.pack(side='top', anchor='w', fill='both')
        notebookFiles = ttk.Notebook(self, width=300, height=300)
        notebookFiles.pack(side='top', anchor='w', fill='y', expand=1)

        for t in mainTabList:
            tab = t(notebookMain)
            notebookMain.add(tab, text=mainTabNames[mainTabList.index(t)])

        for t in infoTabList:
            tab = t(notebookInfo)
            notebookInfo.add(tab, text=infoTabNames[infoTabList.index(t)])

        for t in filesTabList:
            tab = t(notebookFiles)
            notebookFiles.add(tab, text=filesTabNames[filesTabList.index(t)])


class tabConnection(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)

        varSerialPort = tk.StringVar()
        varBaudrate = tk.StringVar()

        optionListSerialPort = ['AUTO']
        optionListBaudrate = [9600, 14400, 19200, 28800, 38400, 56000, 57600, 115200]

        frameConnection = ttk.Frame(self)
        frameConnection.grid(column=0, row=0, sticky='nsew')

        buttonRefresh = ttk.Button(frameConnection, text='Refresh')
        # buttonRefresh.pack(side='right', anchor='n')
        buttonRefresh.grid(row=0, column=1)
        labelSerialPort = ttk.Label(frameConnection, text='Serial Port')
        # labelSerialPort.pack(side='left', anchor='n', fill='x')
        labelSerialPort.grid(row=0, column=0, sticky='nsew')
        optionMenuSerialPort = ttk.OptionMenu(frameConnection, varSerialPort, optionListSerialPort[0],
                                              *optionListSerialPort)
        # optionMenuSerialPort.pack(fill='x', anchor='w')
        optionMenuSerialPort.grid(row=1, column=0, columnspan=2, sticky='nsew')
        labelBaudrate = ttk.Label(frameConnection, text='Baudrate')
        labelBaudrate.grid(row=3, column=0, sticky='nsew')
        optionBaudrate = ttk.OptionMenu(frameConnection, varBaudrate, optionListBaudrate[0], *optionListBaudrate)
        optionBaudrate.grid(row=4, column=0, columnspan=2, sticky='nsew')
        buttonConnect = ttk.Button(frameConnection, text='Connect')
        buttonConnect.grid(row=5, column=0, columnspan=2, sticky='nsew')


class tabState(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)

        frameState = ttk.Frame(self)
        frameState.pack(fill='both', expand=True)

        ''' Widgets '''
        # Label
        labelState = ttk.Label(frameState, text='State: Offline')
        labelEstimatedTotalTime = ttk.Label(frameState, text='Estimated Total Time: 0:00')
        labelElapsedTime = ttk.Label(frameState, text='Elapsed Time: 0:00')
        labelTimeLeft = ttk.Label(frameState, text='Time Left: 0:00')
        labelProgress = ttk.Label(frameState, text='Progress: 0%')

        # Separator
        separatorUpper = ttk.Separator(frameState, orient='horizontal')
        separatorLower = ttk.Separator(frameState, orient='horizontal')

        # Progress Bar
        progressbar = ttk.Progressbar(frameState)

        # Button
        buttonStart = ttk.Button(frameState, text='Start')
        buttonPause = ttk.Button(frameState, text='Pause')
        buttonCancel = ttk.Button(frameState, text='Cancel')

        ''' Grid Layout '''
        # Label
        labelState.grid(row=0, column=0, padx=10, pady=10, sticky='we', columnspan=3)
        labelEstimatedTotalTime.grid(row=2, column=0, padx=10, pady=10, sticky='we', columnspan=3)
        labelElapsedTime.grid(row=4, column=0, padx=10, pady=10, sticky='we', columnspan=3)
        labelTimeLeft.grid(row=5, column=0, padx=10, pady=10, sticky='we', columnspan=3)
        labelProgress.grid(row=6, column=0, padx=10, pady=10, sticky='we', columnspan=3)

        # Separator
        separatorUpper.grid(row=1, column=0, sticky='we', columnspan=3)
        separatorLower.grid(row=3, column=0, sticky='we', columnspan=3)

        # Progress Bar
        progressbar.grid(row=7, column=0, sticky='we', padx=10, columnspan=3)

        # Button
        buttonStart.grid(row=8, column=0)
        buttonPause.grid(row=8, column=1)
        buttonCancel.grid(row=8, column=2)


class tabControl(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)

        frameControl = ttk.Frame(self)
        frameControl.grid(row=0, column=0, sticky='nsew')

        labelframeCurrentReading = ttk.Labelframe(frameControl, text='Current Reading')
        labelframeQuickMove = ttk.Labelframe(frameControl, text='Quick Move')
        labelframeDegreesIncrement = ttk.Labelframe(labelframeQuickMove, text='Increment')

        varDegreeIncrement = tk.IntVar(self)

        ''' Widgets '''
        # Label
        labelCurrentAzimuth = ttk.Label(labelframeCurrentReading, text='Azimuth: 0.0°')
        labelCurrentElevation = ttk.Label(labelframeCurrentReading, text='Elevation: 0.0°')
        labelCurrentPower = ttk.Label(labelframeCurrentReading, text='Power: 0.0 μW')

        # Button
        buttonElevationUp = ttk.Button(labelframeQuickMove, text='↑')
        buttonElevationUp.grid(row=0, column=1)
        buttonElevationDown = ttk.Button(labelframeQuickMove, text='↓')
        buttonElevationDown.grid(row=2, column=1)
        buttonAzimuthCCW = ttk.Button(labelframeQuickMove, text='←')
        buttonAzimuthCCW.grid(row=1, column=0)
        buttonAzimuthCW = ttk.Button(labelframeQuickMove, text='→')
        buttonAzimuthCW.grid(row=1, column=2)
        buttonHome = ttk.Button(labelframeQuickMove, text='⌂')
        buttonHome.grid(row=1, column=1)

        # Radiobutton
        radiobutton1 = ttk.Radiobutton(labelframeDegreesIncrement, text='1°', variable=varDegreeIncrement, value=1)
        radiobutton5 = ttk.Radiobutton(labelframeDegreesIncrement, text='5°', variable=varDegreeIncrement, value=5)
        radiobutton10 = ttk.Radiobutton(labelframeDegreesIncrement, text='10°', variable=varDegreeIncrement, value=10)
        radiobutton20 = ttk.Radiobutton(labelframeDegreesIncrement, text='20°', variable=varDegreeIncrement, value=20)

        ''' Grid Layout '''
        # Labelframe
        labelframeCurrentReading.grid(row=0, column=0)
        labelframeQuickMove.grid(row=0, column=1)
        labelframeDegreesIncrement.grid(row=3, column=0, columnspan=3)

        # Label
        labelCurrentAzimuth.grid(row=0, column=0, sticky='we')
        labelCurrentElevation.grid(row=1, column=0, sticky='we')
        labelCurrentPower.grid(row=2, column=0, sticky='we')

        # Radiobutton
        radiobutton1.grid(row=0, column=0)
        radiobutton5.grid(row=0, column=1)
        radiobutton10.grid(row=0, column=2)
        radiobutton20.grid(row=0, column=3)


class tabScan(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)

        frameScanControl = ttk.Frame(self)
        frameScanControl.pack(side='bottom')

        optionListScanDirection = ['Up', 'Down', 'Clockwise', 'Counterclockwise']

        ''' Variables '''
        varScanStartAzimuth = tk.StringVar()
        varScanStartElevation = tk.StringVar()
        varScanDirection = tk.StringVar()
        varScanAmount = tk.StringVar()

        ''' Widgets '''
        # Label
        labelScanStartAzimuth = ttk.Label(frameScanControl, text='Start Azimuth:')
        labelScanStartElevation = ttk.Label(frameScanControl, text='Start Elevation:')
        labelScanDirection = ttk.Label(frameScanControl, text='Direction:')
        labelScanAmount = ttk.Label(frameScanControl, text='Amount:')

        # Entry
        entryScanStartAzimuth = ttk.Entry(frameScanControl, textvariable=varScanStartAzimuth)
        entryScanStartElevation = ttk.Entry(frameScanControl, textvariable=varScanStartElevation)
        entryScanAmount = ttk.Entry(frameScanControl, textvariable=varScanAmount)

        # OptionMenu
        optionMenuScanDirection = ttk.OptionMenu(frameScanControl, varScanDirection, optionListScanDirection[0],
                                                 *optionListScanDirection)

        # Button
        buttonScan = ttk.Button(frameScanControl, text='Scan')

        # Other
        # progressBar = ttk.Progressbar(frameScanControl, orient='horizontal', length=100, mode='determinate').grid(
        # row=2, column=0, columnspan=5, sticky='nsew') sep = ttk.Separator(frameConnection, orient='horizontal')
        # sep.grid(row=2, column=0, columnspan=2, sticky='we')

        ''' Grid Layout '''
        # Label
        labelScanStartAzimuth.grid(row=0, column=0, sticky='nsew')
        labelScanStartElevation.grid(row=1, column=0, sticky='nsew')
        labelScanDirection.grid(row=0, column=2, sticky='nsew')
        labelScanAmount.grid(row=1, column=2, sticky='nsew')

        # Entry
        entryScanStartAzimuth.grid(row=0, column=1)
        entryScanStartElevation.grid(row=1, column=1)
        entryScanAmount.grid(row=1, column=3)

        # OptionMenu
        optionMenuScanDirection.grid(row=0, column=3, sticky='nsew')

        # Button
        buttonScan.grid(row=0, column=4, rowspan=2)

        ''' Graph '''
        x = np.arange(0.0, 2.0, 0.01)
        y = 1 + np.sin(2 * np.pi * x)

        figureScan = plt.figure()

        plotScan = figureScan.add_subplot(111)
        plotScan.plot(x, y, '.-')

        plotScan.set_title('Yeet!')
        plotScan.set_xlabel('Azimuth (°)')
        plotScan.set_ylabel('Power (μW)')

        canvasScan = FigureCanvasTkAgg(figureScan, self)
        canvasScan.draw()
        canvasScan.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, anchor=tk.S)

        toolbarScan = NavigationToolbar2Tk(canvasScan, self)
        toolbarScan.update()
        canvasScan.tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True, anchor=tk.S)


class tabMap(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)

        frameMapControl = ttk.Frame(self)
        frameMapControl.pack(side='bottom')

        ''' Variables '''
        varMapCenterAzimuth = tk.StringVar()
        varMapCenterElevation = tk.StringVar()
        varMapHeight = tk.StringVar()
        varMapWidth = tk.StringVar()

        ''' Label '''
        labelMapCenterAzimuth = ttk.Label(frameMapControl, text='Center Azimuth:')
        labelMapCenterElevation = ttk.Label(frameMapControl, text='Center Elevation:')
        labelMapHeight = ttk.Label(frameMapControl, text='Height:')
        labelMapWidth = ttk.Label(frameMapControl, text='Width:')

        ''' Entry '''
        entryMapStartAzimuth = ttk.Entry(frameMapControl, textvariable=varMapCenterAzimuth)
        entryMapStartElevation = ttk.Entry(frameMapControl, textvariable=varMapCenterElevation)
        entryMapHeight = ttk.Entry(frameMapControl, textvariable=varMapHeight)
        entryMapWidth = ttk.Entry(frameMapControl, textvariable=varMapWidth)

        ''' Button '''
        buttonMap = ttk.Button(frameMapControl, text='Map')

        ''' Other '''
        # progressBar = ttk.Progressbar(frameScanControl, orient='horizontal', length=100, mode='determinate').grid(row=2, column=0, columnspan=5, sticky='nsew')
        # sep = ttk.Separator(frameConnection, orient='horizontal')
        # sep.grid(row=2, column=0, columnspan=2, sticky='we')

        ''' Grid Layout '''
        # Label
        labelMapCenterAzimuth.grid(row=0, column=0, sticky='nsew')
        labelMapCenterElevation.grid(row=1, column=0, sticky='nsew')
        labelMapHeight.grid(row=0, column=2, sticky='nsew')
        labelMapWidth.grid(row=1, column=2, sticky='nsew')

        # Entry
        entryMapStartAzimuth.grid(row=0, column=1)
        entryMapStartElevation.grid(row=1, column=1)
        entryMapHeight.grid(row=0, column=3)
        entryMapWidth.grid(row=1, column=3)

        # Button
        buttonMap.grid(row=0, column=4, rowspan=2)

        ''' Graph '''
        # make these smaller to increase the resolution
        dx, dy = 0.05, 0.05

        # generate 2 2d grids for the x & y bounds
        y, x = np.mgrid[slice(1, 5 + dy, dy), slice(1, 5 + dx, dx)]

        z = np.sin(x) ** 10 + np.cos(10 + y * x) * np.cos(x)

        z = z[:-1, :-1]

        # Colorbar Scaling
        levels = MaxNLocator(nbins=15).tick_values(z.min(), z.max())

        figureMap = plt.figure(2)
        plotMap = figureMap.add_subplot(111)

        cf = plotMap.contourf(x[:-1, :-1] + dx / 2., y[:-1, :-1] + dy / 2., z, levels=levels, cmap=plt.cm.jet)

        cb = figureMap.colorbar(cf, ax=plotMap)

        plotMap.set_title('Yoink!')

        plotMap.set_xlabel('Azimuth (°)')
        plotMap.set_ylabel('Elevation (°)')

        cb.minorticks_on()
        cb.set_label('Power (μW)')

        # Tkinter Matplotlib Graphing Code
        canvasMap = FigureCanvasTkAgg(figureMap, self)
        canvasMap.draw()
        canvasMap.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, anchor=tk.S)

        toolbarMap = NavigationToolbar2Tk(canvasMap, self)
        toolbarMap.update()
        canvasMap.tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True, anchor=tk.S)


class tabTerminal(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)

        scrolledText = scrolledtext.ScrolledText(self).pack()


class tabViewer(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)


class tabGraph(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)


class tabRawData(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)


# # Figure # #
# figsize=(5, 4), dpi=100

# a = figScan.add_subplot(111)
style.use('ggplot')

ser.write(REPORT_STATE)
state = readState(ser)

PrintState()

# def refreshSerialPorts():
#     optionListSerialPort.clear()
#     optionMenuSerialPort['menu'].delete(0, 'end')
#     optionMenuSerialPort['menu'].add_command(label='AUTO')
#     for i in portList():
#         optionMenuSerialPort['menu'].add_command(label=i)

# # Grid # #
# tab_info.grid_rowconfigure(0, weight=1)
# tab_info.grid_columnconfigure(0, weight=1)

# for i in portList():
#     optionListSerialPort.append(i)

mrtGUI().mainloop()
