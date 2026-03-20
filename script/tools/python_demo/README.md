# **Battery Voltage and Current Monitoring with Shutdown Trigger for 52Pi UPS Gen 6 Using systemd**

Here is the modified code, rewritten as a systemd service to monitor only the battery voltage and current. When the battery voltage drops below 7400mV(each battery 3700mV), it triggers a shutdown operation. The code has been optimized by removing unnecessary parts and adding detailed English comments. The monitoring interval is set to check every 2 minutes.

### Modified Code
```python
#!/usr/bin/env python3
"""
This script monitors the battery voltage and current of a 52Pi UPS Gen 6 device.
If the battery voltage drops below 7400mV, it triggers a shutdown process.
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
    logging.info(f"Battery Voltage: {battery_voltage}mV, Current: {battery_current}mA")

    check_times = 0
    for i in range(3):
        if battery_voltage < BATTERY_VOLTAGE_THRESHOLD:
            logging.info(f"Battery voltage is below {BATTERY_VOLTAGE_THRESHOLD}mV. Initiating shutdown")
            logging.info(f"Battery voltage is below {BATTERY_VOLTAGE_THRESHOLD}mV. Initiating shutdown")
            check_times +=1
    if check_times >= 3:
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
```

### Code Explanation
1. **Optimization**:
   - Removed unnecessary `read_byte_register` and `read_dword_register` functions, as only the battery voltage and current are monitored, both of which are 16-bit registers.
   - Removed the redundant `read_all_registers` function and directly read the battery voltage and current in `check_battery_status`.
   - Removed excess print statements, retaining only those for battery voltage and current.

2. **Monitoring Logic**:
   - Checks the battery voltage and current every 2 minutes.
   - If the battery voltage falls below 3700mV, it calls `subprocess.run` to execute the shutdown command.

3. **Comments**:
   - Added detailed English comments to explain the purpose of each function and the main logic.

### Creating a systemd Service
To run this script as a systemd service, you need to create a systemd service file.

1. **Create the Service File**:
   Create a service file in the `/etc/systemd/system/` directory, for example, `battery_monitor.service`.

   ```bash
   sudo nano /etc/systemd/system/battery_monitor.service
   ```

2. **Edit the Service File**:
   Add the following content to the file:

   ```ini
   [Unit]
   Description=Battery Monitor Service
   After=network.target

   [Service]
   ExecStart=/usr/bin/python3 /path/to/your/script/battery_monitor.py
   Restart=always
   RestartSec=4
   User=pi

   [Install]
   WantedBy=multi-user.target
   ```

   - `ExecStart` specifies the path to the script.
   - `Restart=always` ensures the service restarts automatically if it fails.
   - `User=pi` specifies that the script runs as the `pi` user.

3. **Create log file and grant permissions**:

```bash
sudo touch /var/log/battery_monitor.log
sudo chown pi:pi /var/log/battery_monitor.log
sudo chmod 664 /var/log/battery_monitor.log
```

4. **Start the Service**:
   After saving the file, run the following commands to start the service and enable it to start on boot:

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable battery_monitor.service
   sudo systemctl start battery_monitor.service
   ```

5. **Check Service Status**:
   Use the following command to check the service status:

   ```bash
   sudo systemctl status battery_monitor.service
   ```

With this setup, the script will run as a systemd service, checking the battery voltage and current every 2 minutes and triggering a shutdown operation when the voltage falls below 7400mV.
