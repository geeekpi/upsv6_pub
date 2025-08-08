from UPS import TFTModule as tft
from UPS import Device

# init display 
tft.init()

# loop 
while True:
    # clean the screen and fill with white color
    tft.fillScreen(0xFFFF)
    
    # delay for 500 microseconds 
    Device.sleep(500)

    # call drawCircle function (int x, int y, int radius, int color(RGB565 format)
    tft.drawCircle(120, 120, 30, 0xF800)
    Device.sleep(500)
    tft.drawCircle(120, 120, 40,0x001F) 
    Device.sleep(500)
    tft.drawCircle(120, 120, 50, 0x07E0)
    Device.sleep(500)
    tft.drawCircle(120, 120, 50, 0x0000)
    Device.sleep(500)
    
