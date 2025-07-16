import smbus2
import time


I2C_DEV = 1 
I2C_ADDR = 0x17
OTA_REGISTER_ADDR = 0x29
DATA = 0xA5A5 

bus = smbus2.SMBus(I2C_DEV)

def write_i2c_register(address, register, data):
    """send data to register"""
    try:
        high_byte = (data >> 8) & 0xFF 
        low_byte = data & 0xFF 

        bus.write_word_data(address, register, (high_byte << 8) | low_byte)
        print(f"Write Successfull to 0x{data:04X} to register 0x{register:02X}, deviceaddress: 0x{address:02X}")
    except Exception as e:
        print(f"Writing failed to i2c register: {e}")

if __name__ == "__main__":
    write_i2c_register(I2C_ADDR, OTA_REGISTER_ADDR, DATA)
    print("Now, your UPS v6 entered OTA mode, please update your firmware by using user_wirte_tool. ")
