from UPS import TFTModule as tft
from UPS import Device

tft.init()

while True:
    tft.fillScreen(0xFFFF)
    Device.sleep(200)
    # print("""
    tft.drawString(10, 10, 'HELLO UPSv6', 0xFB00, 0xFFFF, 2)
    Device.sleep(20)
    tft.drawString(10, 30, 'To be', 0x017E, 0xFFFF, 2)
    Device.sleep(20)
    tft.drawString(10, 60, 'Or not to be', 0x07FF, 0xFFFF, 2)
    Device.sleep(20)
    tft.drawString(10, 90, 'That is a question', 0xFFE0, 0x0000, 2)
    Device.sleep(20)
    tft.drawString(10, 120, 'Do you like it?', 0xFB00, 0x0000, 2)
    Device.sleep(20)
    # """)
    Device.sleep(5000)
