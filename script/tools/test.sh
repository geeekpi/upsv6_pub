#!/bin/bash

I2C_DEVICE=0x17

WHO_AM_I=0x0E

read_register_and_convert() {
    local address=$1
    local width=$2
    hex_value=$(i2cget -y 1 $I2C_DEVICE $address $width 2>&1)
    if [ $? -ne 0 ]; then
        echo "Failed to read from address $address"
        return 1
    fi
    dec_value=$(perl -e "printf \"%d\", hex('$hex_value');")
    echo "dec_value: $dec_value"
}

main_menu() {
    while true; do
        choice=$(whiptail --title "UPS gen 6 I2C Register Control" --menu "Choose an option" 15 60 4 \
            "1" "Read Output Voltage(Decimal)" \
            "2" "Exit" 3>&1 1>&2 2>&3)
        exit_status=$?
        if [ $exit_status -ne 0 ]; then
            echo "User pressed Cancel or closed the dialog"
            exit 1
        fi
        case $choice in
            1)
                dec_value=$(read_register_and_convert $WHO_AM_I w)
                if [ $? -eq 0 ]; then
                    whiptail --title "Output Voltage" --msgbox "Decimal Value: $dec_value" 10 60
                else
                    whiptail --title "Error" --msgbox "Failed to read WHO_AM_I Register" 10 60
                fi
                ;;
            2)
                exit 0
                ;;
        esac
    done
}

main_menu
