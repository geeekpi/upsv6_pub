# How to upgrade firmware via OTA 

## Step 1. Enable OTA mode 
First, run `enable_ota.py`, which will put the UPS into OTA mode. This will cause the Power button to become unresponsive until the OTA update is complete. After the update, the button will work again. You can also observe the change in the register address on the Raspberry Pi using `i2cdetect -y 1`.

- `0x17` indicates normal operating mode.
- `0x18` indicates OTA mode.

## Step 2. Upload Firmware by using `firmware_uploader` executable binary file

Navigate to the `script/tools` directory of the repository and execute the `make` command to compile the source code. You will see the generated `firmware_uploader` file, which is the tool used for updating the firmware. When performing the update, simply provide the path to the firmware file.

For example:

```
./firmware_uploader ../../firmware/rev1.0-final.bin
```
