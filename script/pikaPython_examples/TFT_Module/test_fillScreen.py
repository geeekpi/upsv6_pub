from UPS import TFTModule as tft
from UPS import Device

# init display
tft.init()

# loop
while True:
    # fill screen with White color
    tft.fillScreen(0xFFFF)

    # delay for 200 ms
    Device.sleep(200)

    # fill screen with Yellow color
    tft.fillScreen(0xFFE0)
    Device.sleep(200)

    # fill screen with Red color
    tft.fillScreen(0xF800)
    Device.sleep(200)

    # fill screen with Blue color 
    tft.fillScreen(0x01FC)
    Device.sleep(200)

    # fill screen with Green color
    tft.fillScreen(0x07E0)
    Device.sleep(200)
