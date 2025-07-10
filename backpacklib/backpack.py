import serial.tools.list_ports
import serial
import threading
import time

from .incomingMessageManager import IncomingMessageManager
from .AskKnitSensorData import AskKnitSensorData
from .config import Config
import pickle

serial_port = serial.Serial()
selected_port = None

data_ready = False
cur_device_index = -1
last_read_index = -1

last_read_index_array = [{} for _ in range(Config.MAX_CONN_HANDLE)]

time_measurement_start = time.time()

for i in range(len(last_read_index_array)):
    last_read_index_array[i] = -1

BACKPACK_SENSOR_DISTANCE_F = 0
BACKPACK_SENSOR_DISTANCE_R = 1
BACKPACK_SENSOR_DISTANCE_L = 2
BACKPACK_SENSOR_MIC = 3
BACKPACK_SENSOR_HEART = 4
BACKPACK_SENSOR_THRMAL = 5
BACKPACK_SENSOR_TEMP_HUMID = 6
BACKPACK_SENSOR_NINEDOF = 7
BACKPACK_OUT_PWM1 = 8
BACKPACK_OUT_PWM2 = 9
BACKPACK_OUT_BIP1L = 10
BACKPACK_OUT_BIP1R = 11
BACKPACK_OUT_BIP2L = 12
BACKPACK_OUT_BIP2R = 13
BACKPACK_SENSOR_GLUCOSE = 14 # No use for this
BACKPACK_SENSOR_PRESSURE = 15

cur_sensers_stat_b_array = [{} for _ in range(Config.MAX_CONN_HANDLE)]
for i in range(len(cur_sensers_stat_b_array)):
    cur_sensers_stat_b_array[i] = -1


message_manager = IncomingMessageManager()

#file = open('read_from_serial_raw.txt', 'wb')


class SerialReaderThread(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self._stop_event = threading.Event()
    
    def run(self):
        '''
        The method that actually gets data from the port
        '''
        global ser, datos
        while not self.stopped():
            readFromPort()
    
    def stop(self):
        self._stop_event.set()
        
    def stopped(self):
        return self._stop_event.is_set()

def start():
    if not startSerialThread():
        return 0
    return 1

def startSerialThread():
    if not portInit():
        return 0
    
    serial_thread = SerialReaderThread()
    serial_thread.start()

    return 1

def portInit():
    global serial_port  # Declare that you want to use the global serial_port variable
    # Get the currently available serial port names
    port_list = list(serial.tools.list_ports.comports())
    # Display the port names
    # for port in port_list:
    #     print("Serial Port:", port.device)
        
    with open('comPort.pkl', 'rb') as file:
    # Call load method to deserialze
        selected_port = pickle.load(file)

    # Prompt the user to select a serial port
    # selected_port = input("Enter the serial port name: ")

    # Create a SerialPort object
    serial_port = serial.Serial(selected_port, 115200)  # Replace 9600 with the appropriate baud rate
    
    if serial_port.is_open:
        return 1
    return 0


def readFromPort():
    #global file
    global message_manager
    global time_measurement_start
    time_measurement_current = time.time()

    if time_measurement_current - time_measurement_start >= 5:
        time_measurement_start = time_measurement_current

    if serial_port.in_waiting > 0:  # Check if there is data available in the buffer
        buffer = serial_port.read(serial_port.in_waiting)  # Read all available bytes from the buffer
        # Create an instance of the IncomingMessageManager class

        '''
        if buffer:
            file.write(buffer)
        '''

        global data_ready
        global cur_sensers_stat_b_array


        # Call the extractBuffer method on the instance
        message_manager.extractBuffer(buffer)
        message_manager.extractData()
        cur_sensers_stat_b_array = message_manager.sensorsStatusArray

        data_ready = True
        return

def writeToPort(buffer):
    if serial_port.is_open:

        # Convert the integer to a single byte (assuming a single byte length)
        byte_value = cur_device_index.to_bytes(1, byteorder='big')

        # Concatenate the original bytes and the new byte
        new_buffer = buffer + byte_value
        #buffer = bytes([0xFF, 0xFF])
        serial_port.write(new_buffer)

        return True
    return False

def portClose():
    # Close the serial port (this code will not be reached as the loop is infinite)
    serial_port.close()

def getLatestData():
    global last_read_index
    global message_manager

    if not data_ready:
        return None
    
    return message_manager.dataBank[0][message_manager.lastIndex[0]]

def getLatestDataWithCount(count):
    time.sleep(0.00001) ## DO NOT REMOVE THIS
    global last_read_index_array
    if not hasNewData():
        return None
    
    last_read_index_array[cur_device_index] = message_manager.lastIndex[cur_device_index]

    current_index = message_manager.getLastIndex(cur_device_index)
    new_array = []

    for i in range(current_index, current_index - count, -1):
        new_array.append(message_manager.dataBank[cur_device_index][i % len(message_manager.dataBank[cur_device_index])])

    #print(new_array[0].sequence)

    return new_array

def hasNewData():
    if last_read_index_array[cur_device_index] == message_manager.lastIndex[cur_device_index]:
        return False
    ##if not message_manager.ready:
    ##    return False
    return True

def printAllDataValueFormat(data):
    print("")
    print("Target Device Number : ", cur_device_index + 1)
    print(f"Sequence |  Distance L (mm) |  Distance F (mm) |  Distance R (mm) |   Mic Data   |  Heart Data  | Temperature Data (°C) | Humidity Data (%) | Pressure Data (kPa)")
    print("-" * len("Sequence |  Distance L (mm) |  Distance F (mm) |  Distance R (mm) |   Mic Data   |  Heart Data  | Temperature Data (°C) | Humidity Data (%) | Pressure Data (kPa)"))

    data_values = [
        data.sequence,
        data.distanceL_data,
        data.distanceF_data,
        data.distanceR_data,
        data.mic_data,
        round(data.heart_data, 5),
        round(data.temperature_data, 5),
        round(data.humid_data, 5),
        data.pressure_data
    ]

    print(" ".join(f"{value:<17}" for value in data_values))
    print("")

    print(f"Accelerometer Data (X/Y/Z)   | Gyroscope Data (X/Y/Z)   | Magnetometer Data (X/Y/Z)")
    print("-" * len("Accelerometer Data (X/Y/Z)   | Gyroscope Data (X/Y/Z)   | Magnetometer Data (X/Y/Z)"))

    accel_values = f"{round(data.accelX_data, 5):<28} | {round(data.gyroX_data, 5):<24} | {round(data.magX_data, 5):<28}"
    print(accel_values)

    accel_values = f"{round(data.accelY_data, 5):<28} | {round(data.gyroY_data, 5):<24} | {round(data.magY_data, 5):<28}"
    print(accel_values)

    accel_values = f"{round(data.accelZ_data, 5):<28} | {round(data.gyroZ_data, 5):<24} | {round(data.magZ_data, 5):<28}"
    print(accel_values)

    print("")

    cur_sensors_stat_b = format(data.sensors_status, '016b')
    print(f"Current sensors status: {cur_sensors_stat_b:<10}")

    

    #sensors_status = getCurrentSensorStatus()

    #if sensors_status[BACKPACK_SENSOR_THRMAL] == 1:
    thermal_grid = ""
    for i in range(32):
        for j in range(32):
            thermal_grid += "0" if data.thermal_array[i][j] >= 2990 else "1"
            #thermal_grid += str((data.thermal_array[i][j] - 2732) / 10.0)
            thermal_grid += "  "
        thermal_grid += "\n"

    print("Thermal Grid:")
    print(thermal_grid)

def printDataValueWithoutThermalFormat(data):
    print("")
    print("Target Device Number : ", cur_device_index + 1)
    print(f"Sequence |  Distance L (mm) |  Distance F (mm) |  Distance R (mm) |   Mic Data   |  Heart Data  | Temperature Data (°C) | Humidity Data (%) | Pressure Data (kPa)")
    print("-" * len("Sequence |  Distance L (mm) |  Distance F (mm) |  Distance R (mm) |   Mic Data   |  Heart Data  | Temperature Data (°C) | Humidity Data (%) | Pressure Data (kPa)"))

    data_values = [
        data.sequence,
        data.distanceL_data,
        data.distanceF_data,
        data.distanceR_data,
        data.mic_data,
        round(data.heart_data, 5),
        round(data.temperature_data, 5),
        round(data.humid_data, 5),
        data.pressure_data
    ]

    print(" ".join(f"{value:<17}" for value in data_values))
    print("")

    print(f"Accelerometer Data (X/Y/Z)   | Gyroscope Data (X/Y/Z)   | Magnetometer Data (X/Y/Z)")
    print("-" * len("Accelerometer Data (X/Y/Z)   | Gyroscope Data (X/Y/Z)   | Magnetometer Data (X/Y/Z)"))

    accel_values = f"{round(data.accelX_data, 5):<28} | {round(data.gyroX_data, 5):<24} | {round(data.magX_data, 5):<28}"
    print(accel_values)

    accel_values = f"{round(data.accelY_data, 5):<28} | {round(data.gyroY_data, 5):<24} | {round(data.magY_data, 5):<28}"
    print(accel_values)

    accel_values = f"{round(data.accelZ_data, 5):<28} | {round(data.gyroZ_data, 5):<24} | {round(data.magZ_data, 5):<28}"
    print(accel_values)

    print("")

    cur_sensors_stat_b = format(data.sensors_status, '016b')
    print(f"Current sensors status: {cur_sensors_stat_b:<10}")

def printThermalGrid(data):
    thermal_grid = ""
    for i in range(32):
        for j in range(32):
            if data.thermal_array[i][j] == -1:
                thermal_grid += "x"
            elif data.thermal_array[i][j] < 2990:
                thermal_grid += "1"
            elif data.thermal_array[i][j] >= 2990:
                thermal_grid += "0"
            #thermal_grid += str((data.thermal_array[i][j] - 2732) / 10.0)
            thermal_grid += "  "
        thermal_grid += "\n"

    print("Thermal Grid:")
    print(thermal_grid)

def printThermalGridCelsius (data):
    thermal_grid = ""
    for i in range(32):
        for j in range(32):
            if data.thermal_array[i][j] == -1:
                thermal_grid += "x"
            else:
                thermal_grid += str((data.thermal_array[i][j] - 2732) / 10.0) # Unit : °C
            thermal_grid += "  "
        thermal_grid += "\n"

    print("Thermal Grid:")
    print(thermal_grid)

def turnAllSensorOn():
    if not turnSensorOn([
        BACKPACK_SENSOR_DISTANCE_F, 
        BACKPACK_SENSOR_DISTANCE_L, 
        BACKPACK_SENSOR_DISTANCE_R, 
        BACKPACK_SENSOR_MIC, 
        BACKPACK_SENSOR_HEART, 
        BACKPACK_SENSOR_THRMAL, 
        BACKPACK_SENSOR_TEMP_HUMID, 
        BACKPACK_SENSOR_NINEDOF, 
        BACKPACK_OUT_PWM1,
        BACKPACK_OUT_PWM2,
        BACKPACK_OUT_BIP1L,
        BACKPACK_OUT_BIP1R,
        BACKPACK_OUT_BIP2L,
        BACKPACK_OUT_BIP2R,
        BACKPACK_SENSOR_PRESSURE
    ]):
        return False
    return True

def turnAllSensorOff():
    if not turnSensorOff([
        BACKPACK_SENSOR_DISTANCE_F, 
        BACKPACK_SENSOR_DISTANCE_L, 
        BACKPACK_SENSOR_DISTANCE_R, 
        BACKPACK_SENSOR_MIC, 
        BACKPACK_SENSOR_HEART, 
        BACKPACK_SENSOR_THRMAL, 
        BACKPACK_SENSOR_TEMP_HUMID, 
        BACKPACK_SENSOR_NINEDOF, 
        BACKPACK_OUT_PWM1,
        BACKPACK_OUT_PWM2,
        BACKPACK_OUT_BIP1L,
        BACKPACK_OUT_BIP1R,
        BACKPACK_OUT_BIP2L,
        BACKPACK_OUT_BIP2R,
        BACKPACK_SENSOR_PRESSURE
    ]):
        return False
    return True

def turnSensorOn(sensors_num_list):

    if not serial_port.is_open:
        return False

    if cur_sensers_stat_b_array[cur_device_index] == -1:
        return False
    
    cur_sensers_stat_b = cur_sensers_stat_b_array[cur_device_index]

    high_byte = (cur_sensers_stat_b >> 8) & 0xFF
    low_byte = cur_sensers_stat_b & 0xFF

    buffer = bytearray([high_byte, low_byte])

    for sensor_num in sensors_num_list:
        if sensor_num > 15:
            return False
        byte_index = sensor_num // 8
        bit_index = sensor_num % 8
        buffer[byte_index] = buffer[byte_index] | (1 << bit_index)

    '''
    '''
    return writeToPort(buffer)

# Before turning off any sensors (especially pressure sensor), 
# please ensure that the backpack device has been turned on and running for at least 15 seconds to ensure that the firmware has been initialized completely.
def turnSensorOff(sensors_num_list):

    if not serial_port.is_open:
        return False

    if cur_sensers_stat_b_array[cur_device_index] == -1:
        return False
    cur_sensers_stat_b = cur_sensers_stat_b_array[cur_device_index]

    high_byte = (cur_sensers_stat_b >> 8) & 0xFF
    low_byte = cur_sensers_stat_b & 0xFF

    buffer = bytearray([high_byte, low_byte])

    for sensor_num in sensors_num_list:
        if sensor_num > 15:
            return False
        byte_index = sensor_num // 8
        bit_index = sensor_num % 8
        buffer[byte_index] = buffer[byte_index] & ~(1 << bit_index)

    '''
    '''

    return writeToPort(buffer)

def getLinkCount():
    return message_manager.deviceLinkCount

def getCurrentDevice():
    return cur_device_index + 1

def changeTargetDevice(device_index):
    global cur_device_index
    cur_device_index = device_index - 1

'''
def getCurrentSensorStatus():

    sensors_status = [{} for _ in range(16)]

    for i in range(16):
        sensors_status[i] = -1

    if cur_sensers_stat_b_array[cur_device_index] == -1:
        return False
    cur_sensers_stat_b = cur_sensers_stat_b_array[cur_device_index]
    # getting bit at position 28 (counting from 0 from right)

    if (cur_sensers_stat_b >> BACKPACK_SENSOR_DISTANCE_F) & 1 == 1:
        sensors_status[BACKPACK_SENSOR_DISTANCE_F] = 1
    elif (cur_sensers_stat_b >> BACKPACK_SENSOR_DISTANCE_F) & 1 == 0:
        sensors_status[BACKPACK_SENSOR_DISTANCE_F] = 0

    if (cur_sensers_stat_b >> BACKPACK_SENSOR_DISTANCE_L) & 1 == 1:
        sensors_status[BACKPACK_SENSOR_DISTANCE_L] = 1
    elif (cur_sensers_stat_b >> BACKPACK_SENSOR_DISTANCE_L) & 1 == 0:
        sensors_status[BACKPACK_SENSOR_DISTANCE_L] = 0
    
    if (cur_sensers_stat_b >> BACKPACK_SENSOR_DISTANCE_R) & 1 == 1:
        sensors_status[BACKPACK_SENSOR_DISTANCE_R] = 1
    elif (cur_sensers_stat_b >> BACKPACK_SENSOR_DISTANCE_R) & 1 == 0:
        sensors_status[BACKPACK_SENSOR_DISTANCE_R] = 0
    
    if (cur_sensers_stat_b >> BACKPACK_SENSOR_MIC) & 1 == 1:
        sensors_status[BACKPACK_SENSOR_MIC] = 1
    elif (cur_sensers_stat_b >> BACKPACK_SENSOR_MIC) & 1 == 0:
        sensors_status[BACKPACK_SENSOR_MIC] = 0
    
    if (cur_sensers_stat_b >> BACKPACK_SENSOR_HEART) & 1 == 1:
        sensors_status[BACKPACK_SENSOR_HEART] = 1
    elif (cur_sensers_stat_b >> BACKPACK_SENSOR_HEART) & 1 == 0:
        sensors_status[BACKPACK_SENSOR_HEART] = 0

    if (cur_sensers_stat_b >> BACKPACK_SENSOR_THRMAL) & 1 == 1:
        sensors_status[BACKPACK_SENSOR_THRMAL] = 1
    elif (cur_sensers_stat_b >> BACKPACK_SENSOR_THRMAL) & 1 == 0:
        sensors_status[BACKPACK_SENSOR_THRMAL] = 0

    if (cur_sensers_stat_b >> BACKPACK_SENSOR_TEMP_HUMID) & 1 == 1:
        sensors_status[BACKPACK_SENSOR_TEMP_HUMID] = 1
    elif (cur_sensers_stat_b >> BACKPACK_SENSOR_TEMP_HUMID) & 1 == 0:
        sensors_status[BACKPACK_SENSOR_TEMP_HUMID] = 0

    if (cur_sensers_stat_b >> BACKPACK_SENSOR_NINEDOF) & 1 == 1:
        sensors_status[BACKPACK_SENSOR_NINEDOF] = 1
    elif (cur_sensers_stat_b >> BACKPACK_SENSOR_NINEDOF) & 1 == 0:
        sensors_status[BACKPACK_SENSOR_NINEDOF] = 0

    if (cur_sensers_stat_b >> BACKPACK_OUT_PWM1) & 1 == 1:
        sensors_status[BACKPACK_OUT_PWM1] = 1
    elif (cur_sensers_stat_b >> BACKPACK_OUT_PWM1) & 1 == 0:
        sensors_status[BACKPACK_OUT_PWM1] = 0

    if (cur_sensers_stat_b >> BACKPACK_OUT_PWM2) & 1 == 1:
        sensors_status[BACKPACK_OUT_PWM2] = 1
    elif (cur_sensers_stat_b >> BACKPACK_OUT_PWM2) & 1 == 0:
        sensors_status[BACKPACK_OUT_PWM2] = 0

    if (cur_sensers_stat_b >> BACKPACK_OUT_BIP1L) & 1 == 1:
        sensors_status[BACKPACK_OUT_BIP1L] = 1
    elif (cur_sensers_stat_b >> BACKPACK_OUT_BIP1L) & 1 == 0:
        sensors_status[BACKPACK_OUT_BIP1L] = 0

    if (cur_sensers_stat_b >> BACKPACK_OUT_BIP1R) & 1 == 1:
        sensors_status[BACKPACK_OUT_BIP1R] = 1
    elif (cur_sensers_stat_b >> BACKPACK_OUT_BIP1R) & 1 == 0:
        sensors_status[BACKPACK_OUT_BIP1R] = 0

    if (cur_sensers_stat_b >> BACKPACK_OUT_BIP2L) & 1 == 1:
        sensors_status[BACKPACK_OUT_BIP2L] = 1
    elif (cur_sensers_stat_b >> BACKPACK_OUT_BIP2L) & 1 == 0:
        sensors_status[BACKPACK_OUT_BIP2L] = 0

    if (cur_sensers_stat_b >> BACKPACK_OUT_BIP2R) & 1 == 1:
        sensors_status[BACKPACK_OUT_BIP2R] = 1
    elif (cur_sensers_stat_b >> BACKPACK_OUT_BIP2R) & 1 == 0:
        sensors_status[BACKPACK_OUT_BIP2R] = 0

    if (cur_sensers_stat_b >> BACKPACK_SENSOR_GLUCOSE) & 1 == 1:
        sensors_status[BACKPACK_SENSOR_GLUCOSE] = 1
    elif (cur_sensers_stat_b >> BACKPACK_SENSOR_GLUCOSE) & 1 == 0:
        sensors_status[BACKPACK_SENSOR_GLUCOSE] = 0

    if (cur_sensers_stat_b >> BACKPACK_SENSOR_PRESSURE) & 1 == 1:
        sensors_status[BACKPACK_SENSOR_PRESSURE] = 1
    elif (cur_sensers_stat_b >> BACKPACK_SENSOR_PRESSURE) & 1 == 0:
        sensors_status[BACKPACK_SENSOR_PRESSURE] = 0
    print(sensors_status)
    return sensors_status
'''