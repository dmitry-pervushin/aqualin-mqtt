from bluepy import btle
import time

class Aqualin:

    def __init__(self, mac):
        self.mac = mac

    def __delay(self):
        time.sleep(5)

    def state(self, read_status = True, read_battery = False):
        timer = None
        valve = None
        percent = None
        dev = btle.Peripheral(self.mac)
        status = dev.readCharacteristic(0x73) if read_status else ([None] * 5)
        battery = dev.readCharacteristic(0x81) if read_battery else [None]
        try:
            timer = status[4]
            valve = status[2]
        except:
            pass
        try:
            percent = battery[0]
        except:
            pass
        self.__delay()
        dev.disconnect()
        return {'timer': timer, 'state': valve, 'battery': percent}

    def __command(self, minutes):
        on = 1 if minutes else 0
        command = [0x7b, 0x03, on, 00, minutes if on else 0]
        return command

    def on(self, minutes = 1):
        dev = btle.Peripheral(self.mac) 
        dev.writeCharacteristic(0x73, bytes(self.__command(minutes)))
        time.sleep(5)
        dev.disconnect()

    def off(self):
        dev = btle.Peripheral(self.mac) 
        dev.writeCharacteristic(0x73, bytes(self.__command(None)))
        self.__delay()
        dev.disconnect()
