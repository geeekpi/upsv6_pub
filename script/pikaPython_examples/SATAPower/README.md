# About SATA Power Board 
This board is an expansion board for UPSv6. It will connect to your UPSv6 via a FPC cable. 
It should connect the external power supply or a battery pack with at most 8.4v input. It will provide power monitor functions and can support SATA disk's power supply, it has the same form sock for the SATA drive. 
It can offer 12v, 5v, 3.3v power supply. 
* Ouput 12v@2A / 5V@4A /3.3V@4A
* Input 8.4V Max

## How to read the readings from PikaPython script? 
* Uploading `read_sataPower.py` by using `rpi.py` script file.
```bash
export PYTHONIOENCODING='utf-8'
python rpi.py -u read_sataPower.py
```

* Read the readings.
```bash
python rpi.py -r
```
🐥
