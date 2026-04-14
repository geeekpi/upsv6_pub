from UPS import TFTModule as tft
from UPS import Device

tft.init()

while True:
    tft.fillScreen(0xFFFF)
    Device.sleep(200)
    tft.drawString(10, 10, 'HELLO UPSv6', 0xFB00, 0xFFFF, 2)
    Device.sleep(20)
    tft.drawString(10, 30, 'To be', 0x017E, 0xFFFF, 3)
    Device.sleep(20)
    tft.drawString(10, 60, 'Or not to be', 0xFB00, 0xFFFF, 3)
    Device.sleep(20)
    tft.drawString(10, 90, 'It\'s a question', 0xFFE0, 0x0000, 2)
    Device.sleep(20)
    tft.drawString(10, 120, 'Do u like it?', 0xFB00, 0x0000, 2)
    Device.sleep(20)
    tft.drawString(10, 150, 'Are you ok?', 0xFFFF, 0x0000, 3)
    Device.sleep(20)
    tft.drawString(10, 180, 'UPS Gen 6', 0x001F, 0xFB00, 3)
    Device.sleep(20)
    tft.drawString(10, 210, 'Green Light', 0x07E0, 0xFFE0, 3)
    Device.sleep(20)
    Device.sleep(5000)
