#!/usr/bin/env python3
"""
This script monitors the battery voltage and current of a 52Pi UPS V6 device.
If the battery voltage drops below 3700mV, it triggers a shutdown process.
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

# Threshold for battery voltage
BATTERY_VOLTAGE_THRESHOLD = 3700  # in mV

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

# Check battery status and trigger shutdown if necessary
def check_battery_status():
    """
    Check the battery status and trigger shutdown if the voltage is below the threshold.
    """
    battery_voltage, battery_current = read_battery_status()
    logging.info(f"Battery Voltage: {battery_voltage}mV, Current: {battery_current}mA.")
    
    if battery_voltage < BATTERY_VOLTAGE_THRESHOLD:
        logging.info(f"Battery voltage is below {BATTERY_VOLTAGE_THRESHOLD}mV. Initiating shutdown.")
        logging.info(f"Battery voltage is below {BATTERY_VOLTAGE_THRESHOLD}mV. Initiating shutdown.")
        subprocess.run(SHUTDOWN_COMMAND, shell=True)

# Main loop
def main():
    """
    Main loop to periodically check the battery status.
    """
    try:
        while True:
            check_battery_status()
            time.sleep(120)  # Check every 2 minutes
    except KeyboardInterrupt:
        print("Exiting battery monitor script.")
    finally:
        bus.close()

if __name__ == "__main__":
    main()
