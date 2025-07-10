from .config import Config
# block_message.py

import time
import struct
from .AskKnitSensorData import AskKnitSensorData

class BlockMessage:
    def __init__(self):
        self.deviceIndex = -1
        self.messageLength = 0
        self.deviceMessage = bytearray(Config.DEVICE_MESSAGE_BUFFER)
        self.oneMessageLength = 0

    def is_valid_block(self, buffer_to_extract, position):
        return (chr(buffer_to_extract[position + Config.SAMPLE_BLOCK_HEADER_HEAD_POSITION]) == Config.SAMPLE_BLOCK_HEADER_HEAD_CHAR and
                chr(buffer_to_extract[position + Config.SAMPLE_BLOCK_HEADER_TAIL_POSITION]) == Config.SAMPLE_BLOCK_HEADER_TAIL_CHAR and
                chr(buffer_to_extract[position + Config.SAMPLE_BLOCK_FOOTER_HEAD_POSITION]) == Config.SAMPLE_BLOCK_FOOTER_HEAD_CHAR and
                chr(buffer_to_extract[position + Config.SAMPLE_BLOCK_FOOTER_TAIL_POSITION]) == Config.SAMPLE_BLOCK_FOOTER_TAIL_CHAR)
    
    def is_valid_short_header(self, buffer_to_extract, position):
        return (chr(buffer_to_extract[position + Config.SAMPLE_BLOCK_HEADER_HEAD_POSITION]) == Config.SAMPLE_BLOCK_HEADER_HEAD_CHAR and
                chr(buffer_to_extract[position + Config.SAMPLE_BLOCK_HEADER_KEY_POSITION]) == Config.SAMPLE_BLOCK_HEADER_KEY_SHORT and
                chr(buffer_to_extract[position + Config.SAMPLE_BLOCK_HEADER_TAIL_POSITION]) == Config.SAMPLE_BLOCK_HEADER_TAIL_CHAR and
                chr(buffer_to_extract[position + Config.SAMPLE_BLOCK_FOOTER_HEAD_POSITION_SHORT]) == Config.SAMPLE_BLOCK_FOOTER_HEAD_CHAR and
                chr(buffer_to_extract[position + Config.SAMPLE_BLOCK_FOOTER_TAIL_POSITION_SHORT]) == Config.SAMPLE_BLOCK_FOOTER_TAIL_CHAR)
    
    def is_valid_short_footer(self, buffer_to_extract, position):
        return (chr(buffer_to_extract[position + Config.SAMPLE_BLOCK_FOOTER_HEAD_POSITION_SHORT]) == Config.SAMPLE_BLOCK_FOOTER_HEAD_CHAR and
                chr(buffer_to_extract[position + Config.SAMPLE_BLOCK_FOOTER_TAIL_POSITION_SHORT]) == Config.SAMPLE_BLOCK_FOOTER_TAIL_CHAR)

    def is_valid_long_header(self, buffer_to_extract, position):
        return (chr(buffer_to_extract[position + Config.SAMPLE_BLOCK_HEADER_HEAD_POSITION]) == Config.SAMPLE_BLOCK_HEADER_HEAD_CHAR and
                chr(buffer_to_extract[position + Config.SAMPLE_BLOCK_HEADER_KEY_POSITION]) == Config.SAMPLE_BLOCK_HEADER_KEY_LONG and
                chr(buffer_to_extract[position + Config.SAMPLE_BLOCK_HEADER_TAIL_POSITION]) == Config.SAMPLE_BLOCK_HEADER_TAIL_CHAR and
                chr(buffer_to_extract[position + Config.SAMPLE_BLOCK_FOOTER_HEAD_POSITION_LONG]) == Config.SAMPLE_BLOCK_FOOTER_HEAD_CHAR and
                chr(buffer_to_extract[position + Config.SAMPLE_BLOCK_FOOTER_TAIL_POSITION_LONG]) == Config.SAMPLE_BLOCK_FOOTER_TAIL_CHAR)
    
    def is_valid_long_footer(self, buffer_to_extract, position):
        return (chr(buffer_to_extract[position + Config.SAMPLE_BLOCK_FOOTER_HEAD_POSITION_LONG]) == Config.SAMPLE_BLOCK_FOOTER_HEAD_CHAR and
                chr(buffer_to_extract[position + Config.SAMPLE_BLOCK_FOOTER_TAIL_POSITION_LONG]) == Config.SAMPLE_BLOCK_FOOTER_TAIL_CHAR)

    def look_for_block_starting_position(self, buffer_to_extract, starting_position):
        current_position = starting_position

        if self.oneMessageLength == Config.MESSAGE_CONTENT_LENGTH_SHORT:
            while (current_position + Config.SAMPLE_BLOCK_LENGTH_SHORT) < self.messageLength and not self.is_valid_short_header(buffer_to_extract, current_position): # Bugfix
                current_position += 1
            return current_position, "SHORT"
        elif self.oneMessageLength == Config.MESSAGE_CONTENT_LENGTH_LONG:
            while (current_position + Config.SAMPLE_BLOCK_LENGTH_LONG) < self.messageLength and not self.is_valid_long_header(buffer_to_extract, current_position): # Bugfix
                current_position += 1
            return current_position, "LONG"


    def read_u_int24(self, buffer_to_extract, position):
        return (buffer_to_extract[position + 2] << 16) | (buffer_to_extract[position + 1] << 8) | buffer_to_extract[position]
    
    def read_u_int32(self, buffer_to_extract, position):
        return (buffer_to_extract[position + 3] << 24) | (buffer_to_extract[position + 2] << 16) | (buffer_to_extract[position + 1] << 8) | buffer_to_extract[position]

    def read_u_short(self, buffer_to_extract, position):
        return (buffer_to_extract[position + 1] << 8) | buffer_to_extract[position]

    def read_float(self, buffer_to_extract, position):
        source = buffer_to_extract[position:position + 4]
        return struct.unpack('f', source)[0]

    def detect_negative_number(self, num_of_bit, val):
        max_val = 2 ** num_of_bit - 1
        half = max_val / 2

        if val <= half:
            return val

        val ^= max_val  # XOR
        val += 1
        val *= -1

        return val

    def append_buffer(self, buffer, length):
        self.deviceMessage[self.messageLength:self.messageLength + length] = buffer[:length]
        self.messageLength += length

    def read_buffer(self, sync_index_value):
        debug = 0
        read_out_datas = []

        data_starting_position, block_length_type = self.look_for_block_starting_position(self.deviceMessage, 0)

        if block_length_type == "SHORT":
            block_length = Config.SAMPLE_BLOCK_LENGTH_SHORT
        elif block_length_type == "LONG":
            block_length = Config.SAMPLE_BLOCK_LENGTH_LONG
        else:
            block_length = 0

        while data_starting_position + block_length <= self.messageLength:
            if block_length_type == "UNKNOWN":
                break

            ask_knit_sensor_data = AskKnitSensorData()
            current_read_position = data_starting_position

            invalid_header = (
                chr(self.deviceMessage[current_read_position + Config.SAMPLE_BLOCK_HEADER_HEAD_POSITION]) != Config.SAMPLE_BLOCK_HEADER_HEAD_CHAR
                or chr(self.deviceMessage[current_read_position + Config.SAMPLE_BLOCK_HEADER_TAIL_POSITION]) != Config.SAMPLE_BLOCK_HEADER_TAIL_CHAR
            )

            if block_length == Config.SAMPLE_BLOCK_LENGTH_SHORT:
                invalid_footer = (
                    chr(self.deviceMessage[current_read_position + Config.SAMPLE_BLOCK_FOOTER_HEAD_POSITION_SHORT]) != Config.SAMPLE_BLOCK_FOOTER_HEAD_CHAR
                    or chr(self.deviceMessage[current_read_position + Config.SAMPLE_BLOCK_FOOTER_TAIL_POSITION_SHORT]) != Config.SAMPLE_BLOCK_FOOTER_TAIL_CHAR
                )
            if block_length == Config.SAMPLE_BLOCK_LENGTH_LONG:
                invalid_footer = (
                    chr(self.deviceMessage[current_read_position + Config.SAMPLE_BLOCK_FOOTER_HEAD_POSITION_LONG]) != Config.SAMPLE_BLOCK_FOOTER_HEAD_CHAR
                    or chr(self.deviceMessage[current_read_position + Config.SAMPLE_BLOCK_FOOTER_TAIL_POSITION_LONG]) != Config.SAMPLE_BLOCK_FOOTER_TAIL_CHAR
                )

            if invalid_header or invalid_footer: # Try to find the next header[0] char

                '''
                if invalid_header:
                    print("Invalid header detected")
                if invalid_footer:
                    print("Invalid footer detected")
                '''
                #print("Try to find the next header[0] char")

                number_of_char_to_skip = 1
                for i in range(1, block_length):
                    number_of_char_to_skip = i
                    if self.deviceMessage[current_read_position + i] == Config.SAMPLE_BLOCK_HEADER_HEAD_POSITION:
                        break
                data_starting_position += number_of_char_to_skip
                continue

            current_read_position += Config.SAMPLE_BLOCK_HEADER_TAIL_POSITION + 1

            # Parse data come from serial port (dongle).
            ask_knit_sensor_data.distanceF_data = self.read_u_short(self.deviceMessage, current_read_position + 2)
            ask_knit_sensor_data.distanceR_data = self.read_u_short(self.deviceMessage, current_read_position + 4)
            ask_knit_sensor_data.distanceL_data = self.read_u_short(self.deviceMessage, current_read_position + 6)
            ask_knit_sensor_data.mic_data = self.read_u_short(self.deviceMessage, current_read_position + 8)
            ask_knit_sensor_data.heart_data = self.read_u_short(self.deviceMessage, current_read_position + 10)

            thermal_array = [[0] * 32 for _ in range(32)]
            offset = 0

            ask_knit_sensor_data.highest_thermal_pixel = self.read_u_short(self.deviceMessage, current_read_position + 10 + 2)
            ask_knit_sensor_data.lowest_thermal_pixel = self.read_u_short(self.deviceMessage, current_read_position + 10 + 2)

            thermal_grid = ""


            if block_length != 70:
                for i in range(32):
                    for j in range(32):
                        offset += 2
                        thermal_array[i][j] = self.read_u_short(self.deviceMessage, current_read_position + 10 + offset)
                        ask_knit_sensor_data.thermal_array[i][j] = thermal_array[i][j]

                        if ask_knit_sensor_data.highest_thermal_pixel < ask_knit_sensor_data.thermal_array[i][j]:
                            ask_knit_sensor_data.highest_thermal_pixel = ask_knit_sensor_data.thermal_array[i][j]
                        if ask_knit_sensor_data.lowest_thermal_pixel > ask_knit_sensor_data.thermal_array[i][j]:
                            ask_knit_sensor_data.lowest_thermal_pixel = ask_knit_sensor_data.thermal_array[i][j]
            

            ask_knit_sensor_data.temperature_data = self.read_float(self.deviceMessage, current_read_position + 10 + offset + 2)
            ask_knit_sensor_data.humid_data = self.read_float(self.deviceMessage, current_read_position + 10 + offset + 2 + 4)
            ask_knit_sensor_data.accelX_data = self.read_float(self.deviceMessage, current_read_position + 10 + offset + 2 + 8)
            ask_knit_sensor_data.accelY_data = self.read_float(self.deviceMessage, current_read_position + 10 + offset + 2 + 12)
            ask_knit_sensor_data.accelZ_data = self.read_float(self.deviceMessage, current_read_position + 10 + offset + 2 + 16)
            ask_knit_sensor_data.gyroX_data = self.read_float(self.deviceMessage, current_read_position + 10 + offset + 2 + 20)
            ask_knit_sensor_data.gyroY_data = self.read_float(self.deviceMessage, current_read_position + 10 + offset + 2 + 24)
            ask_knit_sensor_data.gyroZ_data = self.read_float(self.deviceMessage, current_read_position + 10 + offset + 2 + 28)
            ask_knit_sensor_data.magX_data = self.read_float(self.deviceMessage, current_read_position + 10 + offset + 2 + 32)
            ask_knit_sensor_data.magY_data = self.read_float(self.deviceMessage, current_read_position + 10 + offset + 2 + 36)
            ask_knit_sensor_data.magZ_data = self.read_float(self.deviceMessage, current_read_position + 10 + offset + 2 + 40)
            
            ask_knit_sensor_data.pressure_data = self.read_float(self.deviceMessage, current_read_position + 10 + offset + 2 + 44)
            ask_knit_sensor_data.sensors_status = self.read_u_short(self.deviceMessage, current_read_position + 10 + offset + 2 + 48)

            ask_knit_sensor_data.sequence = self.read_u_short(self.deviceMessage, current_read_position)
            ask_knit_sensor_data.sync_sequence = (
                ask_knit_sensor_data.sequence - sync_index_value + Config.MAX_INDEX_NUMBER
            ) % Config.SAMPLE_BLOCK_MAX_LOGIC_SEQUENCE
            current_read_position += 2
            current_read_position += 2

            data1 = self.read_u_short(self.deviceMessage, current_read_position)
            ask_knit_sensor_data.data1 = data1
            current_read_position += 2

            data2 = self.read_u_short(self.deviceMessage, current_read_position)
            ask_knit_sensor_data.data2 = data2

            ask_knit_sensor_data.ticks = int(time.time() * 10000000)

            read_out_datas.append(ask_knit_sensor_data)

            data_starting_position += block_length

        
        remaining_length = self.messageLength - data_starting_position
        if remaining_length >= 0:
            self.messageLength = remaining_length
            #self.deviceMessage[:remaining_length] = self.deviceMessage[data_starting_position:]
            self.deviceMessage = self.deviceMessage[data_starting_position:data_starting_position + remaining_length] + self.deviceMessage[remaining_length:]
        
        return read_out_datas

class BlockMessageFragment:
    def __init__(self):
        self.deviceIndex = -1
        self.messageLength = 0
        self.deviceMessage = bytearray(Config.BLOCK_MESSAGE_FRAGMENT_BUFFER)
