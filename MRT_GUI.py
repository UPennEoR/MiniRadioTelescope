import os
import sys
import tkinter as tk
from tkinter import ttk

import numpy as np
from matplotlib import pyplot as plt
from matplotlib import style
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import MaxNLocator

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


class mrtGUI(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.geometry('1280x800')
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


class tabControl(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)


class tabScan(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)

        frameScanControl = ttk.Frame(self)
        frameScanControl.pack(side='bottom')

        optionListScanDirection = ['Up', 'Down', 'Clockwise', 'Counterclockwise']

        varScanStartAzimuth = tk.StringVar()
        varScanStartElevation = tk.StringVar()
        varScanDirection = tk.StringVar()
        varScanAmount = tk.StringVar()
        labelScanStartAzimuth = ttk.Label(frameScanControl, text='Start Azimuth:').grid(row=0, column=0, sticky='nsew')
        labelScanStartElevation = ttk.Label(frameScanControl, text='Start Elevation:').grid(row=1, column=0,
                                                                                            sticky='nsew')
        labelScanDirection = ttk.Label(frameScanControl, text='Direction:').grid(row=0, column=2, sticky='nsew')
        labelScanAmount = ttk.Label(frameScanControl, text='Amount:').grid(row=1, column=2, sticky='nsew')
        entryScanStartAzimuth = ttk.Entry(frameScanControl, textvariable=varScanStartAzimuth).grid(row=0, column=1)
        entryScanStartElevation = ttk.Entry(frameScanControl, textvariable=varScanStartElevation).grid(row=1, column=1)
        entryScanAmount = ttk.Entry(frameScanControl, textvariable=varScanAmount).grid(row=1, column=3)
        optionMenuScanDirection = ttk.OptionMenu(frameScanControl, varScanDirection, optionListScanDirection[0],
                                                 *optionListScanDirection).grid(row=0, column=3, sticky='nsew')
        buttonScan = ttk.Button(frameScanControl, text='Scan').grid(row=0, column=4, rowspan=2)
        # progressBar = ttk.Progressbar(frameScanControl, orient='horizontal', length=100, mode='determinate').grid(row=2, column=0, columnspan=5, sticky='nsew')
        # sep = ttk.Separator(frameConnection, orient='horizontal')
        # sep.grid(row=2, column=0, columnspan=2, sticky='we')

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

        optionListScanDirection = ['Up', 'Down', 'Clockwise', 'Counterclockwise']

        ''' Variables '''
        varMapCenterAzimuth = tk.StringVar()
        varMapCenterElevation = tk.StringVar()
        varMapHeight = tk.StringVar()
        varMapWidth = tk.StringVar()

        ''' Label '''
        labelMapCenterAzimuth = ttk.Label(frameMapControl, text='Center Azimuth:').grid(row=0, column=0, sticky='nsew')
        labelMapCenterElevation = ttk.Label(frameMapControl, text='Center Elevation:').grid(row=1, column=0, sticky='nsew')
        labelMapDirection = ttk.Label(frameMapControl, text='Height:').grid(row=0, column=2, sticky='nsew')
        labelMapAmount = ttk.Label(frameMapControl, text='Width:').grid(row=1, column=2, sticky='nsew')

        ''' Entry '''
        entryMapStartAzimuth = ttk.Entry(frameMapControl, textvariable=varMapCenterAzimuth).grid(row=0, column=1)
        entryMapStartElevation = ttk.Entry(frameMapControl, textvariable=varMapCenterElevation).grid(row=1, column=1)
        entryMapHeight = ttk.Entry(frameMapControl, textvariable=varMapHeight).grid(row=0, column=3)
        entryMapWidth = ttk.Entry(frameMapControl, textvariable=varMapWidth).grid(row=1, column=3)

        ''' Button '''
        buttonMap = ttk.Button(frameMapControl, text='Map').grid(row=0, column=4, rowspan=2)

        ''' Other '''
        # progressBar = ttk.Progressbar(frameScanControl, orient='horizontal', length=100, mode='determinate').grid(row=2, column=0, columnspan=5, sticky='nsew')
        # sep = ttk.Separator(frameConnection, orient='horizontal')
        # sep.grid(row=2, column=0, columnspan=2, sticky='we')

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

        cf = plotMap.contourf(x[:-1, :-1] + dx/2., y[:-1, :-1] + dy/2., z, levels=levels, cmap=plt.cm.jet)

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
