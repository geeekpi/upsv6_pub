#!/usr/bin/env python3
"""
This script monitors the battery voltage and current of a 52Pi UPS V6 device.
If the battery voltage drops below 7400 mV, it triggers a shutdown process.
"""

from smbus2 import SMBus
import time
import subprocess
import logging 

#define log file path
LOG_FILE = "/var/log/battery_monitor.log"

# configure logging settings
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(message)s')

# Device address
DEVICE_ADDRESS = 0x17

# Define registers address
BATTERY_VOLTAGE_REG = 0x12
BATTERY_CURRENT_REG = 0x1A
INPUT_VOLTAGE_REG = 0x10
INPUT_CURRENT_REG = 0x18

# Threshold for battery voltage
BATTERY_VOLTAGE_THRESHOLD = 3700  # in mV (value for 1 (one) battery cell!)

# Shutdown command
SHUTDOWN_COMMAND = "sudo sync ; sudo init 0"

# Initialize SMBus
bus = SMBus(1)  # 1 means I2C no.1 bus

# Read 16-bit register
def read_word_register(register_address):
    """
    Read a 16-bit register from the device.
    """
    value = bus.read_word_data(DEVICE_ADDRESS, register_address)
    if value > 32767:
        value -= 65536
    return value

# Read battery voltage and current
def read_battery_status():
    """
    Read the battery voltage and current from the device.
    """
    battery_voltage = read_word_register(BATTERY_VOLTAGE_REG)
    battery_current = read_word_register(BATTERY_CURRENT_REG)
    return battery_voltage, battery_current

# Read charger voltage and current
def read_input_status():
    """
    Read the charger voltage and current from the device.
    """
    input_voltage = read_word_register(INPUT_VOLTAGE_REG)
    input_current = read_word_register(INPUT_CURRENT_REG)
    return input_voltage, input_current

# Check battery status and trigger shutdown if necessary
def check_battery_status():
    """
    Check the battery status and trigger shutdown if the voltage is below the threshold.
    """
    badBattery = 0                                                   # flag for bad battery state
    battery_voltage, battery_current = read_battery_status()
    logging.info(f"Battery Voltage: {battery_voltage}mV, Current: {battery_current}mA.")

    if battery_voltage < BATTERY_VOLTAGE_THRESHOLD * 2:              # check for double the threshold, we have 2 batteries in series!
        logging.info(f"Battery voltage is below {BATTERY_VOLTAGE_THRESHOLD}mV. Checking again...")

        for x in range (0, 3):
            battery_voltage, battery_current = read_battery_status() # reread battery voltage
            if battery_voltage < BATTERY_VOLTAGE_THRESHOLD * 2:      # check again
                logging.info(f"Battery voltage is still below {BATTERY_VOLTAGE_THRESHOLD}mV.")
                badBattery = badBattery + 1                            # still bad battery state, increment flag
            else:
                logging.info(f"Battery voltage is OK - Aborting shutdown.")
                badBattery = 0                                        # battery is OK, reset flag
                break
            sleep(1)                                                  # dont poll the registers too frequently

    if badBattery > 0:
        logging.info(f"Battery voltage is below {BATTERY_VOLTAGE_THRESHOLD}mV. Initiating shutdown.")
        subprocess.run(SHUTDOWN_COMMAND, shell=True)

# Check input status and trigger shutdown if necessary
def check_input_status():
    """
    Check the input status.
    """
    input_voltage, input_current = read_input_status()
    logging.info(f"- - Input Voltage: {input_voltage}mV, Current: {input_current}mA.")
    
# Main loop
def main():
    """
    Main loop to periodically check the battery status.
    """
    try:
        while True:
            check_battery_status()
            check_input_status()
            time.sleep(60)  # Check every 1 minutes
    except KeyboardInterrupt:
        print("Exiting battery monitor script.")
    finally:
        bus.close()

if __name__ == "__main__":
    main()
