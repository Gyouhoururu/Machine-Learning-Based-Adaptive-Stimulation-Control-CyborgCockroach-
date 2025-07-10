from typing import List, Dict
import time

from .config import Config
from .block_message import BlockMessage, BlockMessageFragment
from .AskKnitSensorData import AskKnitSensorData


class IncomingMessageManager:
    def __init__(self):
        self.deviceLinkCount = 0
        self.remainingUnreadBuffer = bytearray(Config.INCOMING_MESSAGE_BUFFER)
        self.remainingUnreadBufferLength = 0
        self.blockMessages = []
        self.syncIndex = [0, 0, 0, 0, 0, 0, 0]
        self.lastIndex = [0, 0, 0, 0, 0, 0, 0]
        self.dataBank = [{} for _ in range(Config.MAX_CONN_HANDLE)]
        self.firstPosition = [0, 0, 0, 0, 0, 0, 0]
        self.lostPacketCount = [0, 0, 0, 0, 0, 0, 0]
        self.totalPacketCount = [0, 0, 0, 0, 0, 0, 0]
        self.historyDatas = []
        self.ready = False
        self.sensorsStatusArray = [{} for _ in range(Config.MAX_CONN_HANDLE)]
        self.fileToWrite = open('testprint.txt', 'w')
        self.performaceTestLastTime = time.time()
        self.performaceTestCurrentTime = 0
        self.performaceTestSpeed = 1
        self.firstData = True
        self.dataCount = 0

        for deviceIndex in range(Config.MAX_CONN_HANDLE):
            for key in range(Config.MAX_INDEX_NUMBER):
                self.dataBank[deviceIndex][key] = AskKnitSensorData.generate_empty_data()
        
        for deviceIndex in range(Config.MAX_CONN_HANDLE):
            self.sensorsStatusArray[deviceIndex] = -1

    def getDeviceData(self, deviceIndex, key):
        deviceDataDict = self.dataBank[deviceIndex]
        safeKey = (key + Config.MAX_INDEX_NUMBER) % Config.MAX_INDEX_NUMBER
        if safeKey not in deviceDataDict or deviceDataDict[safeKey].ticks < int(time.time() * 10000000) - Config.DATA_INVALID_AFTER_US * 10:
            deviceDataDict[safeKey] = AskKnitSensorData.generate_lost_packet()
        return self.dataBank[deviceIndex][safeKey]

    def getLastIndex(self, deviceIndex):
        return self.lastIndex[deviceIndex]

    def getFirstPosition(self, deviceIndex):
        return self.firstPosition[deviceIndex]

    def isValidBlock(self, bufferToExtract, position):
        # ord('h') : Return the integer that represents the character "h":
        if bufferToExtract[position + Config.MESSAGE_HEADER_HEAD_POSITION] != ord('{'):
            return False

        if bufferToExtract[position + Config.MESSAGE_HEADER_SPLITTER_1_POSITION] != ord('-'):
            return False

        if bufferToExtract[position + Config.MESSAGE_HEADER_SPLITTER_2_POSITION] != ord('-'):
            return False

        if bufferToExtract[position + Config.MESSAGE_HEADER_TAIL_POSITION] != ord(':'):
            return False
            

        if bufferToExtract[position + Config.MESSAGE_FOOTER_HEAD_POSITION_SHORT] != ord('}') and bufferToExtract[position + Config.MESSAGE_FOOTER_HEAD_POSITION_LONG] != ord('}'):
            return False

        if bufferToExtract[position + Config.MESSAGE_FOOTER_TAIL_POSITION_SHORT] != ord(',') and bufferToExtract[position + Config.MESSAGE_FOOTER_TAIL_POSITION_LONG] != ord(','):
            return False
        
        return True

    def lookForBlockPosition(self, bufferToExtract, startingPosition):
        currentPosition = startingPosition
        while not self.isValidBlock(bufferToExtract, currentPosition):
            currentPosition += 1

        return currentPosition

    def readLinkCount(self, bufferToExtract, position):
        return int(chr(bufferToExtract[position + Config.MESSAGE_HEADER_LINK_COUNT_POSITION])) - 0

    def readConnHandle(self, bufferToExtract, position):
        return int(chr(bufferToExtract[position + Config.MESSAGE_HEADER_CONN_HANDLE_POSITION])) - 1

    def readMessageLength(self, bufferToExtract, position):
        hundred = int(chr(bufferToExtract[position + Config.MESSAGE_HEADER_LENGTH_POSITION])) - 0
        tenth = int(chr(bufferToExtract[position + Config.MESSAGE_HEADER_LENGTH_POSITION + 1])) - 0
        one = int(chr(bufferToExtract[position + Config.MESSAGE_HEADER_LENGTH_POSITION + 2])) - 0
        return hundred * 100 + tenth * 10 + one

    def readMessageData(self, bufferToExtract, position, lengthToExtract):
        messageBytes = bytearray(Config.INCOMING_MESSAGE_READ_BUFFER)

        messageBytes[:lengthToExtract] = bufferToExtract[position + Config.MESSAGE_DATA_HEAD_POSITION:position + Config.MESSAGE_DATA_HEAD_POSITION + lengthToExtract]

        return messageBytes

    def extractBuffer(self, incomingBuffer):
        bufferToExtract = bytearray(self.remainingUnreadBufferLength + len(incomingBuffer))

        bufferToExtract[:self.remainingUnreadBufferLength] = self.remainingUnreadBuffer[:self.remainingUnreadBufferLength] # Bugfix
        bufferToExtract[self.remainingUnreadBufferLength:] = incomingBuffer

        #self.remainingUnreadBufferLength = 0

        blockStartingPosition = self.lookForBlockPosition(bufferToExtract, 0)

        '''
        if self.remainingUnreadBufferLength != 0:
            if blockStartingPosition + (Config.MESSAGE_BLOCK_TOTAL_LENGTH * 15) > len(bufferToExtract):
                blockStartingPosition = 0
        '''


        self.remainingUnreadBufferLength = 0

        fragments = []

        while blockStartingPosition + (Config.MESSAGE_BLOCK_TOTAL_LENGTH_LONG) <= len(bufferToExtract):
            self.deviceLinkCount = self.readLinkCount(bufferToExtract, blockStartingPosition)
            deviceIndex = self.readConnHandle(bufferToExtract, blockStartingPosition)
            messageLength = self.readMessageLength(bufferToExtract, blockStartingPosition)
            blockMessageFragment = BlockMessageFragment()
            blockMessageFragment.deviceIndex = deviceIndex
            blockMessageFragment.deviceMessage = self.readMessageData(bufferToExtract, blockStartingPosition, messageLength)
            blockMessageFragment.messageLength = messageLength
            fragments.append(blockMessageFragment)

            blockStartingPosition += messageLength + Config.MESSAGE_HEADER_LENGTH + Config.MESSAGE_FOOTER_LENGTH

        remainingLength = len(bufferToExtract) - blockStartingPosition
        self.remainingUnreadBufferLength = remainingLength
        if remainingLength > 0:
            self.remainingUnreadBuffer[:remainingLength] = bufferToExtract[blockStartingPosition:]

        for fragment in fragments:
            blockMessage = next((dblockMessageItem for dblockMessageItem in self.blockMessages if dblockMessageItem.deviceIndex == fragment.deviceIndex), None)
            if blockMessage is not None:
                blockMessage.oneMessageLength = fragment.messageLength
                #print("blockMessage.oneMessageLength", blockMessage.oneMessageLength)
                blockMessage.append_buffer(fragment.deviceMessage, fragment.messageLength)
            else:
                blockMessage = BlockMessage()
                blockMessage.deviceIndex = fragment.deviceIndex
                blockMessage.oneMessageLength = fragment.messageLength
                #print("blockMessage.oneMessageLength", blockMessage.oneMessageLength)
                blockMessage.append_buffer(fragment.deviceMessage, fragment.messageLength)
                self.blockMessages.append(blockMessage)

    def extractData(self):
        for blockMessage in self.blockMessages:
            deviceDatas = blockMessage.read_buffer(self.syncIndex[blockMessage.deviceIndex])

            self.historyDatas.extend(deviceDatas)
            
            for c in deviceDatas:   

                writeTofileStr = ""
                fmt = "{:<5}\t{:<5}\t{:<20}\t{:<20}\t{:<20}\t{:<20}\t{:<20}\t{:<20}"
                targetDeviceAndSeq = "Target device : " + str(blockMessage.deviceIndex) + "    Seq:  " + str(c.sequence)
                distanceData = "  distanceL_data : " + str(c.distanceL_data) + "  distanceF_data : " + str(c.distanceF_data) + "  distanceR_data : " + str(c.distanceR_data)
                micData = "  mic_data : " + str(c.mic_data)
                preesureData = "  pressure_data : " + str(c.pressure_data)
                heartData = "  heart_data : " + str(c.heart_data)
                tempAndHumidData = "  temperature_data : " + str(round(c.temperature_data, 5)) + "  humid_data : " + str(round(c.humid_data, 5))

                writeTofileStr = targetDeviceAndSeq + distanceData + preesureData
                fmt.format("Target device : ", str(blockMessage.deviceIndex), "    Seq:  ", str(c.sequence), "  Accelerometer X: ", str(round(c.accelX_data, 13)), "  Accelerometer Y: ", str(round(c.accelY_data, 13)))
                formatted_str = fmt.format(
                    #"Target device : ",
                    #str(blockMessage.deviceIndex),
                    "Seq:  ",
                    str(c.sequence),
                    "Accelerometer X: ",
                    str(round(c.accelX_data, 13)),
                    "Accelerometer Y: ",
                    str(round(c.accelY_data, 13)),
                    "Accelerometer Z: ",
                    str(round(c.accelZ_data, 13))
                ) + "\n"


                fmt1 = "{:<10}\t{:<5}\t{:<5}\t{:<5}\t{:<15}\t{:<20}\t{:<15}\t{:<20}\t{:<15}\t{:<15}"
                formatted_str = fmt1.format(
                    "Target device : ",
                    str(blockMessage.deviceIndex),
                    "Seq:  ",
                    str(c.sequence),
                    "temperature_data : ",
                    str(round(c.temperature_data, 13)),
                    "humid_data : ",
                    str(round(c.humid_data, 13)),
                    "distanceL_data: ",
                    str(c.distanceL_data)
                )

                if self.firstData:
                    self.performaceTestLastTime = time.time()

                self.performaceTestCurrentTime = time.time()
                timePass = self.performaceTestCurrentTime - self.performaceTestLastTime
                #print(timePass)
                if timePass <= 30:
                    self.fileToWrite = open('testprint.txt', 'a')
                    self.fileToWrite.write(writeTofileStr + "\n")
                    self.fileToWrite.close()
                    self.dataCount += 1
                    #print(self.dataCount)

                #print(writeTofileStr)

                #print(writeTofileStr)                
                self.firstData = False              
                '''
                '''

                # This is the location where all the data will pass through.
                self.dataBank[blockMessage.deviceIndex][c.sequence] = c
                self.lastIndex[blockMessage.deviceIndex] = c.sequence
                self.firstPosition[blockMessage.deviceIndex] = c.sequence
                self.sensorsStatusArray[blockMessage.deviceIndex] = c.sensors_status
            

    def updateSynchronizeIndex(self):
        for i in range(len(self.lastIndex)):
            self.syncIndex[i] = self.lastIndex[i]

        return True
