import os
import sys
import serial

def arduinoPort(baudrate, auto = True, debug = False):
    # Returns the detected or selected port
    while True:
        # Variables
        status = False
        ports = []
        indexList = []

        # Functions
        def portList(portDirectory = '/dev'): # Finds possible ports for your OS
            # Variables
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

        def testPort(port): # Test serial capability
            try:
                ser = serial.Serial(port, baudrate)
                ser.close()
                return True
                if debug:
                    print('DEBUG: Serial device found on ' + port)
            except:
                return False
                if debug:
                    print('DEBUG: Unable to start ' + port)

        def manualPortEntry(): # Manually choose or enter port
            ports = []
            index = 0
            selectionIndex = -1
            print('Possible Ports: ')
            for port in portList():
                print(str(index)+ ' | ' + port)
                ports.append(port)
                index += 1
            print(str(index) + ' | [Manual Input]')
            while selectionIndex == -1:
                try:
                    selectionIndex = int(input('Please select port: '))
                    if selectionIndex == len(ports):
                        return input('Please manually enter port: ')
                    elif selectionIndex not in indexList:
                        raise ValueError
                except ValueError:
                    selection = -1
                    print('Please make a valid selection.')
            return ports[selectionIndex]

        def manualPortSelection(ports):
            index = 0
            selectionIndex = -1
            print('Detected Ports: ')
            for port in ports:
                print(str(index)+ ' | ' + port)
                indexList.append(index)
                index += 1
            while selectionIndex == -1:
                try:
                    selectionIndex = int(input('Please select port: '))
                    if selectionIndex not in indexList:
                        raise ValueError
                except ValueError:
                    selection = -1
                    print('Please make a valid selection.')
            return ports[selectionIndex]

        # Logic
        if auto:
            for port in portList():
                if testPort(port): # If port works, create list of ports.
                    ports.append(port)
                    if debug:
                        print('DEBUG: Verified port: ' + port)
            if len(ports) == 0:
                print('Please verify Arduino connection.')
                input("Press Enter to retry...")
            elif len(ports) > 1:
                if debug:
                    print('DEBUG: More than 1 possible port detected.')
                return manualPortSelection(ports)
                break
            else:
                return ports[0]
                break
        else:
            return manualPortEntry()
            break

