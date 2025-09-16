# UPS v6 Usage 

## ChangeLog
* Updata PikaPython interpreter version: pikascript-core==V1.13.4 / pikaStdLib == V1.13.4 / pikaStdDevice==V2.4.6 
* Update new firmware Rev1.1 and adding support for those two expansion board. 
* 2025/9/16 - adding SATA Power module power data reading function. It will read out the SATA Power board's (expansion board) 12V voltage, battery voltage, MCU voltage and current informations.
* 2025/8/16 - adding TFT module (240x240pixel RGB TFT display) for displaying the information of UPSv6 via PikaPython Scripts.

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

## More details 
* [Firmware](./firmware/README.md)
* [Script](./scirpt/README.md)
* [UPS_Module_API_Instructions](./script/UPS_Module_API_Instructions.md)
* [PikaPython_Examples_democodes](./script/pikaPython_examples/README.md)
* [TFT Module](./script/pikaPython_examples/TFT_Module/README.md)
* [SATA Power Module](./script/pikaPython_examples/SATAPower/README.md) 
## Have fun!
o(*￣▽￣*)ブ 
