from smbus2 import SMBus
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

# Device address
DEVICE_ADDRESS = 0x17

# Define registers address
VERSION_REG = 0x01
OUTPUT_VOLTAGE_REG = 0x0E
INPUT_VOLTAGE_REG = 0x10
OUTPUT_CURRENT_REG = 0x16
INPUT_CURRENT_REG = 0x18

# Define ANSI color
RED = '\033[95m'
GREEN = '\033[92m'
END_COLOR = '\033[0m'

# Initialize SMBus
bus = SMBus(1)  # 1 means I2C no.1 bus

# Read 16-bit register
def read_word_register(register_address):
    value = bus.read_word_data(DEVICE_ADDRESS, register_address)
    if value > 32767:
        value -= 65536
    return value

# Calculate power
def calculate_power(voltage_mv, current_ma):
    voltage_v = voltage_mv / 1000.0
    current_a = current_ma / 1000.0
    return voltage_v * current_a  # Result in watts

# Initialize lists to store data
input_power_data = []
output_power_data = []
time_data = []

# Initialize time
start_time = time.time()

# Function to update the plot
def update(frame):
    global start_time

    # Read voltage and current values
    input_voltage_mv = read_word_register(INPUT_VOLTAGE_REG)
    input_current_ma = read_word_register(INPUT_CURRENT_REG)
    output_voltage_mv = read_word_register(OUTPUT_VOLTAGE_REG)
    output_current_ma = read_word_register(OUTPUT_CURRENT_REG)

    # Calculate input and output power
    input_power_w = calculate_power(input_voltage_mv, input_current_ma)
    output_power_w = calculate_power(output_voltage_mv, output_current_ma)

    # Append data
    current_time = time.time() - start_time
    time_data.append(current_time)
    input_power_data.append(input_power_w)
    output_power_data.append(output_power_w)

    # Limit the data to the last 100 points
    if len(time_data) > 100:
        time_data.pop(0)
        input_power_data.pop(0)
        output_power_data.pop(0)

    # Clear the previous plot
    ax.clear()

    # Plot input power
    ax.plot(time_data, input_power_data, label='Input Power (W)', color='blue')
    ax.set_ylabel('Power (W)')
    ax.set_xlabel('Time (s)')
    ax.legend(loc='upper left')

    # Plot output power
    ax.plot(time_data, output_power_data, label='Output Power (W)', color='red')
    ax.legend(loc='upper left')

    # Set title
    ax.set_title('Real-time Input and Output Power')

# Create a figure and axis
fig, ax = plt.subplots()

# Create the animation
ani = animation.FuncAnimation(fig, update, interval=2000)  # Update every 2 seconds

# Show the plot
plt.show()
