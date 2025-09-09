from UPS import TFTModule as tft 
from UPS import Device 

# init display
tft.init()

while True:
    tft.fillScreen(0xFFFF)
    Device.sleep(500)

    for x in range(0, 240, 10):
        tft.drawFastVLine(x, 20, x, 0xFFE0)
        Device.sleep(50)

