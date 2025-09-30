import smbus2
import time
import subprocess as sp


# device bus
I2C_DEV = 1 

# device address 
I2C_ADDR = 0x17

# ota register address 
OTA_REGISTER_ADDR = 0x29

# create ota request data 
DATA = 0xA5A5 

# create an instance of i2c bus
bus = smbus2.SMBus(I2C_DEV)


def write_i2c_register(address, register, data):
    """send data to register"""
    try:
        high_byte = (data >> 8) & 0xFF 
        low_byte = data & 0xFF 

        bus.write_word_data(address, register, (high_byte << 8) | low_byte)
        print(f"Write Successfull to 0x{data:04X} to register 0x{register:02X}, device address: 0x{address:02X}, please reboot your device after upload firmware to enter to normal mode!")
    except Exception as e:
        print(f"Writing failed to i2c register: {e}")

if __name__ == "__main__":
    try:
        write_i2c_register(I2C_ADDR, OTA_REGISTER_ADDR, DATA)
    except KeyboardInterrupt:
        pass 
    finally: 
        #sp.getoutput("echo system will be reboot!")
        #sp.getoutput("sudo init 0")
        print("OK, you can upload new firmware right now, use `firmware_uploader` tool")
