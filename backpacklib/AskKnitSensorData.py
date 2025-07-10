import time

class AskKnitSensorData:
    def __init__(self):
        # Add on
        self.ticks = 0
        self.isLostPacket = False
        self.isLostPacketCounted = False
        self.isPlaceHolderPacket = False
        self.isPlaceHolderPacketCounted = False

        # デバイスの毎回のサンプリングデータ（１セットのデータ）
        self.sequence = 0
        self.sync_sequence = 0
        self.data1 = 0
        self.data2 = 0
        self.distanceF_data = 0
        self.distanceR_data = 0
        self.distanceL_data = 0
        self.mic_data = 0
        self.heart_data = 0
        self.temperature_data = 0
        self.humid_data = 0
        self.accelX_data = 0
        self.accelY_data = 0
        self.accelZ_data = 0
        self.gyroX_data = 0
        self.gyroY_data = 0
        self.gyroZ_data = 0
        self.magX_data = 0
        self.magY_data = 0
        self.magZ_data = 0
        self.thermal_array = [[-1 for _ in range(32)] for _ in range(32)]
        self.highest_thermal_pixel = 0
        self.lowest_thermal_pixel = 0
        self.pressure_data = 0
        self.sensors_status = 0

    @staticmethod
    def generate_lost_packet():
        new_instance = AskKnitSensorData()
        new_instance.isLostPacket = True
        new_instance.ticks = int(time.time() * 1_000_000)

        return new_instance

    @staticmethod
    def generate_empty_data():
        new_instance = AskKnitSensorData()
        new_instance.isLostPacket = False
        new_instance.isLostPacketCounted = True
        new_instance.isPlaceHolderPacket = True
        new_instance.ticks = int(time.time() * 1_000_000) - 1_000 * 10000

        return new_instance

    def packet_lost_int_for_graph(self):
        return -100 if self.isLostPacket else -50

    def __str__(self):
        return f"sequence: {self.sequence} | syncSequence: {self.syncSequence} | data1: {self.data1} | data2: {self.data2}"
