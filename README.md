# UPS v6 Usage 

## Step 1
* Download repository by using git command, open a terminal and typing following command:
```bash
cd ~
git clone https://github.com/geeekpi/upsv6_pub.git
cd upsv6_pub/
```

## Step 2
* Enable I2C function by using `raspi-config` command:
```bash
sudo raspi-config
```
Navigate to `3 Interface Options` -> `I2C` -> `YES` -> `OK` -> `Finished`: 
* Step 1.
<img width="1816" height="788" alt="image" src="https://github.com/user-attachments/assets/5db1e02f-86eb-4d7e-b16c-337b60073677" />
* Step 2.
<img width="1835" height="890" alt="image" src="https://github.com/user-attachments/assets/cb77999c-fbf4-49e9-8d5e-10621ea1af0f" />
* Step 3.
<img width="1822" height="881" alt="image" src="https://github.com/user-attachments/assets/d20aa7da-c6e1-477d-a514-247abcd43cbf" />

## Step 3 
* Compile the *.c to binary file.
```bash
cd upsv6_pub/script/
make
```
You will see following figure:
<img width="1861" height="499" alt="image" src="https://github.com/user-attachments/assets/0994195a-259e-4f8c-9ea1-92f649471a19" />
The files in rec rectangle are executable binaries. 
<img width="1897" height="299" alt="image" src="https://github.com/user-attachments/assets/be4e0367-3056-4bba-8be3-f782b9a1d641" />

### Description 
* 1. user_write_tool: This command is used to update the firmware. The officially released version can be found in the parent “firmware” directory.  Note: Before running this command, the UPS must first be switched into OTA mode.
Run it as:  

```
./user_write_tool  PATH_TO_Firmware_File_Name
```
For example: 
```bash
 ./user_write_tool ../firmware/rev1.0-final.bin
```

* 2. upload_pyscript: This is the tool for uploading PikaPython scripts; it transfers your code to the UPS.
 <img width="1865" height="352" alt="image" src="https://github.com/user-attachments/assets/62b7a6df-40dd-44e9-8474-a267a7a2cd88" />

```bash
./upload_pyscript main.py
```

* 3. Enable OTA Mode script: enable_ota.py 
```bash
python enable_ota.py
```
It will enable OTA mode on UPS v6, during OTA mode, the LED indicator may not work properly, and the push button will be disabled in OTA mode. 

* 4. get_py_output: Once your upload pikapython script to UPS v6, you can monitor upload status by using this command:
```bash
./get_py_output
```
