from smbus2 import SMBus
import time 
import paho.mqtt.client as mqtt 

# MQTT server configure 
MQTT_BROKER = "192.168.3.218"
MQTT_PORT = 1883
MQTT_USERNAME = "jacky"
MQTT_PASSWORD = "mypassword"
MQTT_TOPIC = "ups_status"


# Device address  
DEVICE_ADDRESS = 0x17

# init SMBus
bus = SMBus(1)  # 1 means I2C no.1 bus

# init mqtt client 
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USERNAME, password=MQTT_PASSWORD)

# connect to mqtt server 
def connect_mqtt():
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        print(f"{GREEN}Connected to MQTT Broker at {MQTT_BROKER}:{MQTT_PORT}{END_COLOR}")
    except Exception as e:
        print(f"{RED}Failed to connect to MQTT Broker: {e}{END_COLOR}")
        exit(1)


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

# send data to MQTT server 
def send_data_to_mqtt(data):
    try:
        for key, value in data.items():
            if key in ["OUTPUT_VOLTAGE", "INPUT_VOLTAGE", "BATTERY_VOLTAGE", "MCU_VOLTAGE"]:
                mqtt_client.publish(f"{MQTT_TOPIC}/{key}", value)
            elif key in ["OUTPUT_CURRENT", "INPUT_CURRENT", "BATTERY_CURRENT"]:
                mqtt_client.publish(f"{MQTT_TOPIC}/{key}", value)
            elif key == "TEMPERATURE":
                mqtt_client.publish(f"{MQTT_TOPIC}/{key}", value)
        print(f"{GREEN}Data sent to MQTT topic {MQTT_TOPIC}:{data}{END_COLOR}")
    except Exception as e:
        print(f"{RED}Failed to send data to MQTT broker:{e}{END_COLOR}")


# main loop
def main():
    connect_mqtt()
    mqtt_client.loop_start()  # start mqtt loop
    try:
        while True:
            print(f"{RED}===52Pi UPS v6 Raw data output ==={END_COLOR}")
            registers = read_all_registers()
            send_data_to_mqtt(registers)
            time.sleep(2)
    except KeyboardInterrupt:
        bus.close()
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("Quit Demo")


if __name__ == "__main__":
    main()
