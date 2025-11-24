#!/bin/bash

# Define the I2C address and registers
I2C_DEVICE=0x17

WHO_AM_I=0x00
VERSION=0x01
UUID0=0x02
UUID1=0x06
UUID2=0x0A
OUTPUT_VOLTAGE=0x0E
INPUT_VOLTAGE=0x10
BATTERY_VOLTAGE=0x12
MCU_VOLTAGE=0x14
OUTPUT_CURRENT=0x16
INPUT_CURRENT=0x18
BATTERY_CURRENT=0x1A
TEMPERATURE=0x1C
CR1=0x1D
CR2=0x1E
SR1=0x1F
SR2=0x20
BATTERY_PROTECTION_VOLTAGE=0x21
SHUTDOWN_COUNTDOWN=0x23
AUTO_START_VOLTAGE=0x25
OTA_REQUEST=0x29
RUNTIME=0x2B
CHARGE_DETECT_INTERVAL_S=0x33
LED_CTL=0x35

read_register() {
    local address=$1
    local width=$2
    value=$(i2cget -y 1 $I2C_DEVICE $address $width)
    echo "$value"
}

write_register() {
    local address=$1
    local value=$2
    local width=$3
    i2cset -y 1 $I2C_DEVICE $address $value $width
    echo "Write to address $address: $value"
}

main_menu() {
    whiptail --title "UPS gen 6 I2C Register Control" --menu "Choose an option" 20 78 10 \
        "1" "Read WHO_AM_I Register" \
        "2" "Read Version Number" \
        "3" "Read UUID" \
        "4" "Read Voltage and Current Values" \
        "5" "Read Temperature" \
        "6" "Configure Control Registers" \
        "7" "Configure Battery Protection Voltage" \
        "8" "Configure Shutdown Countdown" \
        "9" "Configure Auto-Start Voltage" \
        "10" "Request OTA Mode" \
        "11" "Configure Charge Detect Interval" \
        "12" "Configure LED Control" \
        "13" "Exit" 3>&1 1>&2 2>&3  &1 > /tmp/menuitem
        menuitem=$(< /tmp/menuitem)
        if [ $? -ne 0 ]; then
		clear
                echo "User pressed Cancel or closed the dialog"
                exit 1
        fi
        menuitem=$(< /tmp/menuitem)
}


while true; do
        main_menu
        case $menuitem in
        1)
            value=$(read_register $WHO_AM_I b)
            echo "$value" > /tmp/whiptail_input
            whiptail --title "WHO_AM_I Register" --textbox /tmp/whiptail_input 8 78
            rm /tmp/whiptail_input
            ;;
        2)
            value=$(read_register $VERSION b)
            echo "$value" > /tmp/whiptail_input
            whiptail --title "Version Number" --textbox /tmp/whiptail_input 8 78
            rm /tmp/whiptail_input
            ;;
        3)
            uuid0=$(read_register $UUID0 w)
            uuid1=$(read_register $UUID1 w)
            uuid2=$(read_register $UUID2 w)
            echo "$uuid0\n$uuid1\n$uuid2\n" > /tmp/whiptail_input
            whiptail --title "UUID" --textbox /tmp/whiptail_input 8 78
            rm /tmp/whiptail_input
            ;;
        4)
            output_voltage=$(read_register $OUTPUT_VOLTAGE w)
            input_voltage=$(read_register $INPUT_VOLTAGE w)
            battery_voltage=$(read_register $BATTERY_VOLTAGE w)
            mcu_voltage=$(read_register $MCU_VOLTAGE w)
            output_current=$(read_register $OUTPUT_CURRENT w)
            input_current=$(read_register $INPUT_CURRENT w)
            battery_current=$(read_register $BATTERY_CURRENT w)

            echo "Output Voltage: $((output_voltage)) mV\nInput Voltage: $((input_voltage)) mV\nBattery Voltage: $((battery_voltage)) mV\nMCU Voltage: $((mcu_voltage)) mV\nOutput Current: $((output_current)) mA\nInput Current: $((input_current)) mA\nBattery Current: $((battery_voltage)) mA\n" > /tmp/whiptail_input
            whiptail --title "Voltage and Current Values" --textbox /tmp/whiptail_input 20 78
            rm /tmp/whiptail_input
            ;;
        5)
            temperature=$(read_register $TEMPERATURE b)
            echo "Temperature: $((temperature)) degree"> /tmp/whiptail_input
            whiptail --title "Temperature" --textbox /tmp/whiptail_input 8 78
            rm /tmp/whiptail_input
            ;;
        6)
            cr1=$(read_register $CR1 b)
            cr2=$(read_register $CR2 b)
            echo "CR1: $cr1\nCR2: $cr2\n" > /tmp/whiptail_input
            whiptail --title "Control Registers" --textbox /tmp/whiptail_input 8 78
            rm /tmp/whiptail_input
            ;;
        7)
            value=$(whiptail --title "Battery Protection Voltage" --inputbox "Enter value from 3300-3800 (unit: mV)" 8 78 3>&1 1>&2 2>&3)
            if [ $? -ne 0 ]; then
                echo "User pressed Cancel or closed the dialog"
                continue
            fi
            write_register $BATTERY_PROTECTION_VOLTAGE $value w
            ;;
        8)
            value=$(whiptail --title "Shutdown Countdown" --inputbox "Enter value (unit: seconds)" 8 78 3>&1 1>&2 2>&3)
            if [ $? -ne 0 ]; then
                echo "User pressed Cancel or closed the dialog"
                continue
            fi
            write_register $SHUTDOWN_COUNTDOWN $value w
            ;;
        9)
            value=$(whiptail --title "Auto-Start Voltage" --inputbox "Enter value (unit: mV)" 8 78 3>&1 1>&2 2>&3)
            if [ $? -ne 0 ]; then
                echo "User pressed Cancel or closed the dialog"
                continue
            fi
            write_register $AUTO_START_VOLTAGE $value w
            ;;
        10)
            write_register $OTA_REQUEST 0xA5A5 w
            whiptail --title "OTA Request" --msgbox "OTA mode requested" 8 78
            ;;
        11)
            value=$(whiptail --title "Charge Detect Interval" --inputbox "Enter value (unit: seconds)" 8 78 3>&1 1>&2 2>&3)
            if [ $? -ne 0 ]; then
                echo "User pressed Cancel or closed the dialog"
                continue
            fi
            write_register $CHARGE_DETECT_INTERVAL_S $value w
            ;;
        12)
            value=$(whiptail --title "LED Control" --inputbox "Enter value (0x00 to 0xFF)" 8 78 3>&1 1>&2 2>&3)
            if [ $? -ne 0 ]; then
                echo "User pressed Cancel or closed the dialog"
                continue
            fi
            write_register $LED_CTL $value b
            ;;
        13)
            exit 0
            ;;
    esac
done
