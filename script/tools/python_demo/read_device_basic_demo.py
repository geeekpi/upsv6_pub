from smbus2 import SMBus
import time 


# Device address  
DEVICE_ADDRESS = 0x17

# init SMBus
bus = SMBus(1)  # 1 means I2C no.1 bus


# Define registers address
# WHO_AM_I_REG = 0x00 // will always be 0xA6
VERSION_REG = 0x01
UID0_REG = 0x02
UID1_REG = 0x06
UID2_REG = 0x0A
OUTPUT_VOLTAGE_REG = 0x0E
INPUT_VOLTAGE_REG = 0x10
BATTERY_VOLTAGE_REG = 0x12
MCU_VOLTAGE_REG = 0x14
OUTPUT_CURRENT_REG = 0x16
INPUT_CURRENT_REG = 0x18
BATTERY_CURRENT_REG = 0x1A
TEMPERATURE_REG = 0x1C

# Define ANSI color
RED = '\033[95m'
GREEN = '\033[92m'
END_COLOR = '\033[0m'


# read 8bit register 
def read_byte_register(register_address):
    value = bus.read_byte_data(DEVICE_ADDRESS, register_address)
    if value > 127:
        value -= 256 
    return value

# read 16bit register 
def read_word_register(register_address):
    value = bus.read_word_data(DEVICE_ADDRESS, register_address)
    if value > 32767:
        value -= 65536
    return value

# read 32bit register 
def read_dword_register(register_address):
    low = bus.read_word_data(DEVICE_ADDRESS, register_address)
    high = bus.read_word_data(DEVICE_ADDRESS, register_address + 2)
    return (high << 16) | low

# read all registers data
def read_all_registers():
    registers = {
        "WHO_AM_I": "0xA6",
        "VERSION": read_byte_register(VERSION_REG),
        "UID0": read_dword_register(UID0_REG),
        "UID1": read_dword_register(UID1_REG),
        "UID2": read_dword_register(UID2_REG),
        "OUTPUT_VOLTAGE": read_word_register(OUTPUT_VOLTAGE_REG),
        "INPUT_VOLTAGE": read_word_register(INPUT_VOLTAGE_REG),
        "BATTERY_VOLTAGE": read_word_register(BATTERY_VOLTAGE_REG),
        "MCU_VOLTAGE": read_word_register(MCU_VOLTAGE_REG),
        "OUTPUT_CURRENT": read_word_register(OUTPUT_CURRENT_REG),
        "INPUT_CURRENT": read_word_register(INPUT_CURRENT_REG),
        "BATTERY_CURRENT": read_word_register(BATTERY_CURRENT_REG),
        "TEMPERATURE": read_byte_register(TEMPERATURE_REG)
    }
    return registers

# read and print out all registers data.
try:
    while True:
        print(f"{RED}=== 52Pi UPS V6 Raw Data Output ==={END_COLOR}")
        registers = read_all_registers()
        for key, value in registers.items():
            if "VOLTAGE" in key:
                print(f"* {key}: {GREEN}{value}mV{END_COLOR} ")
            elif "CURRENT" in key:
                print(f"* {key}: {RED}{value}mA{END_COLOR} ")
            elif "TEMPERATURE" in key:
                print(f"* {key}: {GREEN}{value}C{END_COLOR} ")
            elif "WHO_AM_I" in key:
                print(f"* {key}: {value}")
            else:
                print(f"* {key}: {value}")
        print("-"*80)
        print(" "*80)
        time.sleep(2)  # flush interval in 2 seconds
except KeyboardInterrupt:
    # Shutdown SMBus
    bus.close()
    print("Quit Demo")

