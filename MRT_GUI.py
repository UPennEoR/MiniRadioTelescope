import tkinter as tk
from tkinter import ttk
from matplotlib import pyplot as plt
from matplotlib import style
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

mrtGUI = tk.Tk()
mrtGUI.title('Mini Radio Telescope')
mrtGUI.geometry('1280x800')

# # Figure # #
figScan = plt.figure()  # figsize=(5, 4), dpi=100
a = figScan.add_subplot(111)
style.use('ggplot')

# Notebooks
tab_main = ttk.Notebook(mrtGUI)
tab_info = ttk.Notebook(mrtGUI, width=300, height=250)
tab_files = ttk.Notebook(mrtGUI, width=300, height=300)

# # Frames # #
# Tabs
tabConnection = ttk.Frame(tab_info)
tabState = ttk.Frame(tab_info)
tabControl = ttk.Frame(tab_main)
tabScan = ttk.Frame(tab_main)
tabMap = ttk.Frame(tab_main)
tabTerminal = ttk.Frame(tab_main)
tabFiles = ttk.Frame(tab_files)
# Other
frameConnection = ttk.Frame(tabConnection)
frameConnection.grid(column=0, row=0, sticky='nsew')
# frameConnection.grid_rowconfigure(0, weight=1)
# frameConnection.grid_rowconfigure(1, weight=1)
# frameConnection.grid_rowconfigure(2, weight=1)
# frameConnection.grid_rowconfigure(3, weight=1)
# frameConnection.grid_rowconfigure(4, weight=1)
# frameConnection.grid_rowconfigure(5, weight=1)
# frameConnection.grid_columnconfigure(0, weight=1)
# frameConnection.grid_columnconfigure(1, weight=1)
frameScanControl = ttk.Frame(tabScan)
frameScanControl.pack(side='bottom')

# # Tabs # #
# Info
tab_info.add(tabConnection, text='Connection')
tab_info.add(tabState, text='State')
# Main
tab_main.add(tabControl, text='Control')
tab_main.add(tabScan, text='Scan')
tab_main.add(tabMap, text='Map')
tab_main.add(tabTerminal, text='Terminal')
# Files
tab_files.add(tabFiles, text='Files')

# # Grid # #
tab_info.grid_rowconfigure(0, weight=1)
tab_info.grid_columnconfigure(0, weight=1)

# # Variables # #
varSerialPort = tk.StringVar()
varBaudrate = tk.StringVar()
varScanStartAzimuth = tk.StringVar()
varScanStartElevation = tk.StringVar()
varScanDirection = tk.StringVar()
varScanAmount = tk.StringVar()
optionListSerialPort = ['AUTO']
optionListBaudrate = [9600, 14400, 19200, 28800, 38400, 56000, 57600, 115200]
optionListScanDirection = ['Up', 'Down', 'Clockwise', 'Counterclockwise']


# # Widgets # #
# Connection #
buttonRefresh = ttk.Button(frameConnection, text='Refresh')
# buttonRefresh.pack(side='right', anchor='n')
buttonRefresh.grid(row=0, column=1)
labelSerialPort = ttk.Label(frameConnection, text='Serial Port')
# labelSerialPort.pack(side='left', anchor='n', fill='x')
labelSerialPort.grid(row=0, column=0, sticky='nsew')
optionMenuSerialPort = ttk.OptionMenu(frameConnection, varSerialPort, optionListSerialPort[0], *optionListSerialPort)
# optionMenuSerialPort.pack(fill='x', anchor='w')
optionMenuSerialPort.grid(row=1, column=0, columnspan=2, sticky='nsew')
labelBaudrate = ttk.Label(frameConnection, text='Baudrate')
labelBaudrate.grid(row=3, column=0, sticky='nsew')
optionBaudrate = ttk.OptionMenu(frameConnection, varBaudrate, optionListBaudrate[0], *optionListBaudrate)
optionBaudrate.grid(row=4, column=0, columnspan=2, sticky='nsew')
buttonConnect = ttk.Button(frameConnection, text='Connect')
buttonConnect.grid(row=5, column=0, columnspan=2, sticky='nsew')

# Scan #
labelScanStartAzimuth = ttk.Label(frameScanControl, text='Start Azimuth:').grid(row=0, column=0, sticky='nsew')
labelScanStartElevation = ttk.Label(frameScanControl, text='Start Elevation:').grid(row=1, column=0, sticky='nsew')
labelScanDirection = ttk.Label(frameScanControl, text='Direction:').grid(row=0, column=2, sticky='nsew')
labelScanAmount = ttk.Label(frameScanControl, text='Amount:').grid(row=1, column=2, sticky='nsew')
entryScanStartAzimuth = ttk.Entry(frameScanControl, textvariable=varScanStartAzimuth).grid(row=0, column=1)
entryScanStartElevation = ttk.Entry(frameScanControl, textvariable=varScanStartElevation).grid(row=1, column=1)
entryScanAmount = ttk.Entry(frameScanControl, textvariable=varScanAmount).grid(row=1, column=3)
optionMenuScanDirection = ttk.OptionMenu(frameScanControl, varScanDirection, optionListScanDirection[0], *optionListScanDirection).grid(row=0, column=3, sticky='nsew')
buttonScan = ttk.Button(frameScanControl, text='Scan').grid(row=0, column=4, rowspan=2)
# progressBar = ttk.Progressbar(frameScanControl, orient='horizontal', length=100, mode='determinate').grid(row=2, column=0, columnspan=5, sticky='nsew')
# sep = ttk.Separator(frameConnection, orient='horizontal')
# sep.grid(row=2, column=0, columnspan=2, sticky='we')

# Plots
canvasScan = FigureCanvasTkAgg(figScan, tabScan)
canvasScan.draw()
canvasScan.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True, anchor=tk.S)

toolbarScan = NavigationToolbar2Tk(canvasScan, tabScan)
toolbarScan.update()
canvasScan.tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True, anchor=tk.S)

tab_main.pack(expand=1, fill='both', side='right')
tab_info.pack(side='top', anchor='w', fill='both')
tab_files.pack(side='top', anchor='w', fill='y', expand=1)

mrtGUI.resizable(False, False)
mrtGUI.mainloop()
