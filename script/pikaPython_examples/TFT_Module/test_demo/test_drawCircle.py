from UPS import TFTModule as tft
from UPS import Device

tft.init()

while True:
    tft.fillScreen(0xFFFF)
    Device.sleep(500)
    
    for r in range(1, 120, 2):
        tft.drawCircle(120, 120, r, 0xFC5A)
    Device.sleep(200)

