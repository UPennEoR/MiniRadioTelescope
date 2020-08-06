import os
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext

from matplotlib import pyplot as plt, animation
from matplotlib import style
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import MaxNLocator

import serial
import numpy as np
# import healpy as hp
import astropy as ap
import matplotlib.pyplot as plt
import time
from GUI import MRT_FUNC_PY4_GUI as mrtf
import mrtstate
from scipy.interpolate import griddata

from GUI.MRT_FUNC_PY4_GUI import portList

debug = True

'''
Telescope Movement Commands
(Adapted from RepRap G-Code)
[] = Optional Parameters
G0 A### E### - Rapid Movement (Manual Control)
G1 A### E### F### S### - Programmed Movement (Scan/Map) (S is endstops)
F### - Feedrate
S### - Endstops
G28 [A E] (Select Axis to Home) - Home
G30 - Start Position
G90 - Use Absolute Angles
G91 - Use Relative Angles
G92 A### E### - Set Current Position
M17 - Enable Motors
M18 - Disable Motors
M84 S### - Disable after S seconds of inactivity
M105 - Report Current Readings
M114 - Report Current Position
M350 Ann Enn - Microstepping Mode (Full - 1/16) nn:(1, 2, 4, 8, 16)
N#### - Line Number of G-Code Sent
'''

print('Opening serial port', mrtf.portList()[0])
print('with baud', mrtf.baud)
ser = mrtf.serial.Serial(mrtf.portList()[0], mrtf.baud)
print('Before flushing buffers')
print('Bytes in waiting', ser.inWaiting())
mrtf.FlushSerialBuffers(ser)
print('After flushing buffers')
print('Bytes in waiting', ser.inWaiting())
print('Resetting Arduino')
print('Before reset')
print('Bytes in waiting', ser.inWaiting())
mrtf.ResetArduinoUno(ser, timeout=15, nbytesExpected=mrtf.nIDBytes)
print('After reset')
print('Bytes in waiting', ser.inWaiting())
print(ser.inWaiting())

output = mrtf.read_ser_buffer_to_eot(ser)
print(output)

mrtstate.offsets['eloff'] = 0.
mrtstate.offsets['azoff'] = -180.

print(mrtstate.offsets)

ser.write(mrtf.REPORT_STATE)
mrtstate.state = mrtf.readState(ser)

mrtf.PrintState()

def cmdConnect(port):
    mrtf.connectToArduino(port)


def cmdMap(azimuth, elevation, height, width, message):
    if azimuth.isdigit() & elevation.isdigit() & height.isdigit() & width.isdigit():
        mrtf.RasterMap(ser, azimuth, elevation, height, width)
    else:
        message.config(text='Check Values')


def cmdGo(azimuth, elevation):
    print(azimuth)
    print(elevation)
    # mrtf.GoTo(azimuth, elevation)


def cmdCurrentRefresh(labelAzimuth, labelElevation, labelPower):
    labelAzimuth.config(text='Azimuth:  ' + str(mrtstate.state['azDeg'][0]) + ' deg')
    labelElevation.config(text='Elevation:  ' + str(mrtstate.state['elDeg'][0]) + ' deg')


def cmdCurrentState():
    mrtf.PrintState()


def cmdQuickMove(direction, increment):
    if direction == 'UP':
        mrtf.GoTo(ser, float(mrtstate.state['azDeg'][0]), float(mrtstate.state['elDeg'][0]) + increment)
    elif direction == 'DOWN':
        mrtf.GoTo(ser, float(mrtstate.state['azDeg']), float(mrtstate.state['elDeg']) - increment)
    elif direction == 'CCW':
        mrtf.GoTo(ser, float(mrtstate.state['azDeg']) + increment, float(mrtstate.state['elDeg']))
    elif direction == 'CW':
        mrtf.GoTo(ser, float(mrtstate.state['azDeg']) - increment, float(mrtstate.state['elDeg']))


def cmdScan(azimuth, elevation, direction, amount, message):
    if azimuth.isdigit() & elevation.isdigit() & amount.isdigit():
        mrtf.GoTo(ser, azimuth, elevation)
        mrtf.Direction(ser, direction)
        mrtf.Scan(amount)
    else:
        message.config(text='Check Values')


def cmdEnable():
    mrtf.ser.write(mrtf.ENABLE)
    mrtf.current_state = mrtf.StdCmd(mrtf.ser, mrtf.REPORT_STATE)


def cmdDisable():
    mrtf.ser.write(mrtf.DISABLE)
    current_state = mrtf.StdCmd(mrtf.ser, mrtf.REPORT_STATE)


def cmdSetPosition():
    # mrtf.PrintState()
    # newaz = float(input("New azimuth: "))
    # # print('Current azimuth', mrtstate.state['azDeg'])
    # curr_azoff = offsets['azoff']
    # # print('Current offset', curr_azoff)
    # arduino_az = state['azDeg'] + curr_azoff
    # offsets['azoff'] = arduino_az - newaz
    # # print(mrtf.azoff)
    # newel = float(input("New elevation: "))
    # curr_eloff = offsets['eloff']
    # arduino_el = state['elDeg'] + curr_eloff
    # offsets['eloff'] = arduino_el - newel
    # current_state = StdCmd(ser, REPORT_STATE)
    mrtf.PrintState()


def animationScan(plot):
    pullData = open('data.txt', 'r').read()
    dataArray = pullData.split('\n')
    xar = []
    yar = []
    for eachLine in dataArray:
        if len(eachLine) > 1:
            x, y = eachLine.split(',')
            xar.append(int(x))
            yar.append(int(y))
    plot.clear()
    plot.plot(xar, yar)


def animationMap(plot):
    return


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

        optionListSerialPort = portList()
        optionListBaudrate = [9600, 14400, 19200, 28800, 38400, 56000, 57600, 115200]

        frameConnection = ttk.Frame(self)
        frameConnection.grid(column=0, row=0, sticky='nsew')

        buttonRefresh = ttk.Button(frameConnection, text='Refresh')
        # buttonRefresh.pack(side='right', anchor='n')
        buttonRefresh.grid(row=0, column=1)
        labelSerialPort = ttk.Label(frameConnection, text='Serial Port')
        # labelSerialPort.pack(side='left', anchor='n', fill='x')
        labelSerialPort.grid(row=0, column=0, sticky='nsew')
        optionMenuSerialPort = ttk.OptionMenu(frameConnection, varSerialPort, 'Select port...',
                                              *optionListSerialPort)
        # optionMenuSerialPort.pack(fill='x', anchor='w')
        optionMenuSerialPort.grid(row=1, column=0, columnspan=2, sticky='nsew')
        labelBaudrate = ttk.Label(frameConnection, text='Baudrate')
        labelBaudrate.grid(row=3, column=0, sticky='nsew')
        optionBaudrate = ttk.OptionMenu(frameConnection, varBaudrate, optionListBaudrate[7], *optionListBaudrate)
        optionBaudrate.grid(row=4, column=0, columnspan=2, sticky='nsew')
        buttonConnect = ttk.Button(frameConnection, text='Connect', command=lambda: mrtf.connectToArduino())
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
        labelframeSetpoint = ttk.Labelframe(frameControl, text='Setpoint')

        ''' Variables '''
        varDegreeIncrement = tk.IntVar(self)
        varNewAzimuth = tk.IntVar()
        varNewElevation = tk.IntVar()

        ''' Widgets '''
        # Label
        labelCurrentAzimuth = ttk.Label(labelframeCurrentReading, text='Azimuth:  0.0 deg')
        labelCurrentElevation = ttk.Label(labelframeCurrentReading, text='Elevation:  0.0 deg')
        labelCurrentPower = ttk.Label(labelframeCurrentReading, text='Power:  0.0 muW')
        labelNewAzimuth = ttk.Label(labelframeSetpoint, text='New Azimuth:')
        labelNewElevation = ttk.Label(labelframeSetpoint, text='New Elevation:')

        # Entry
        entryNewAzimuth = ttk.Entry(labelframeSetpoint, textvariable=varNewAzimuth)
        entryNewElevation = ttk.Entry(labelframeSetpoint, textvariable=varNewElevation)

        # Button
        buttonElevationUp = ttk.Button(labelframeQuickMove, text='Up',
                                       command=lambda: cmdQuickMove('UP', varDegreeIncrement.get()))
        buttonElevationDown = ttk.Button(labelframeQuickMove, text='Down',
                                         command=lambda: cmdQuickMove('DOWN', varDegreeIncrement.get()))
        buttonAzimuthCCW = ttk.Button(labelframeQuickMove, text='Left',
                                      command=lambda: cmdQuickMove('CCW', varDegreeIncrement.get()))
        buttonAzimuthCW = ttk.Button(labelframeQuickMove, text='Right',
                                     command=lambda: cmdQuickMove('CW', varDegreeIncrement.get()))
        buttonHome = ttk.Button(labelframeQuickMove, text='Home')
        buttonGo = ttk.Button(labelframeSetpoint, text='Go',
                              command=lambda: cmdGo(varNewAzimuth.get(), varNewElevation.get()))
        buttonRefresh = ttk.Button(labelframeCurrentReading, text='Refresh',
                                   command=lambda: cmdCurrentRefresh(labelCurrentAzimuth, labelCurrentElevation,
                                                                     labelCurrentPower))

        # Radiobutton
        radiobutton1 = ttk.Radiobutton(labelframeDegreesIncrement, text='1 deg', variable=varDegreeIncrement, value=1)
        radiobutton5 = ttk.Radiobutton(labelframeDegreesIncrement, text='5 deg', variable=varDegreeIncrement, value=5)
        radiobutton10 = ttk.Radiobutton(labelframeDegreesIncrement, text='10 deg', variable=varDegreeIncrement,
                                        value=10)
        radiobutton20 = ttk.Radiobutton(labelframeDegreesIncrement, text='20 deg', variable=varDegreeIncrement,
                                        value=20)

        ''' Grid Layout '''
        # Labelframe
        labelframeCurrentReading.grid(row=0, column=0)
        labelframeQuickMove.grid(row=1, column=0)
        labelframeDegreesIncrement.grid(row=3, column=0, columnspan=3)
        labelframeSetpoint.grid(row=2, column=0)

        # Label
        labelCurrentAzimuth.grid(row=0, column=0, sticky='we')
        labelCurrentElevation.grid(row=1, column=0, sticky='we')
        labelCurrentPower.grid(row=2, column=0, sticky='we')
        labelNewAzimuth.grid(row=0, column=0, sticky='we')
        labelNewElevation.grid(row=1, column=0, sticky='we')

        # Entry
        entryNewAzimuth.grid(row=0, column=1)
        entryNewElevation.grid(row=1, column=1)

        # Button
        buttonElevationUp.grid(row=0, column=1)
        buttonElevationDown.grid(row=2, column=1)
        buttonAzimuthCCW.grid(row=1, column=0)
        buttonAzimuthCW.grid(row=1, column=2)
        buttonHome.grid(row=1, column=1)
        buttonGo.grid(row=2, column=0, columnspan=2)
        buttonRefresh.grid(row=0, column=1)

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
        labelScanMessage = ttk.Label(frameScanControl, text='Ready to Scan')

        # Entry
        entryScanStartAzimuth = ttk.Entry(frameScanControl, textvariable=varScanStartAzimuth)
        entryScanStartElevation = ttk.Entry(frameScanControl, textvariable=varScanStartElevation)
        entryScanAmount = ttk.Entry(frameScanControl, textvariable=varScanAmount)

        # OptionMenu
        optionMenuScanDirection = ttk.OptionMenu(frameScanControl, varScanDirection, optionListScanDirection[0],
                                                 *optionListScanDirection)

        # Button
        buttonScan = ttk.Button(frameScanControl, text='Scan',
                                command=lambda: cmdScan(varScanStartAzimuth.get(), varScanStartElevation.get(),
                                                        varScanDirection.get(), varScanAmount.get(), labelScanMessage))

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
        labelScanMessage.grid(row=2, column=0, columnspan=5)

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
        plotScan.set_xlabel(r'Azimuth ($^\circ$)')
        plotScan.set_ylabel(r'Power ($\mu$W)')

        canvasScan = FigureCanvasTkAgg(figureScan, self)
        canvasScan.draw()
        canvasScan.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, anchor=tk.S)

        toolbarScan = NavigationToolbar2Tk(canvasScan, self)
        toolbarScan.update()
        # Replacing .tkcanvas with .get_tk_widget seems to "just work" (TM) - JA 2020/04/04
        # canvasScan.tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True, anchor=tk.S)
        canvasScan.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True, anchor=tk.S)


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
        labelMapMessage = ttk.Label(frameMapControl, text='Ready to Map')

        ''' Entry '''
        entryMapStartAzimuth = ttk.Entry(frameMapControl, textvariable=varMapCenterAzimuth)
        entryMapStartElevation = ttk.Entry(frameMapControl, textvariable=varMapCenterElevation)
        entryMapHeight = ttk.Entry(frameMapControl, textvariable=varMapHeight)
        entryMapWidth = ttk.Entry(frameMapControl, textvariable=varMapWidth)

        ''' Button '''
        buttonMap = ttk.Button(frameMapControl, text='Map',
                               command=lambda: cmdMap(entryMapStartAzimuth.get(), entryMapStartElevation.get(),
                                                      entryMapHeight.get(), entryMapWidth.get(), labelMapMessage))

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
        labelMapMessage.grid(row=2, column=0, columnspan=5)

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

        plotMap.set_xlabel(r'Azimuth ($^\circ$)')
        plotMap.set_ylabel(r'Elevation ($^\circ$)')

        cb.minorticks_on()
        cb.set_label(r'Power ($\mu$W)')

        # Tkinter Matplotlib Graphing Code
        canvasMap = FigureCanvasTkAgg(figureMap, self)
        canvasMap.draw()
        canvasMap.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, anchor=tk.S)

        toolbarMap = NavigationToolbar2Tk(canvasMap, self)
        toolbarMap.update()
        # canvasMap.tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True, anchor=tk.S)
        canvasMap.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True, anchor=tk.S)


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

# *** Still need to figure out a global ser. ***
# ser.write(REPORT_STATE)
# state = readState(ser)

# PrintState()

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
