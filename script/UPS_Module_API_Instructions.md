# Python Device API Documentation

## Device Class

### Basic Information
- `getVersion() -> int`  
  Gets device version number
- `getInfo() -> str`  
  Gets device information string

### Voltage/Current/Temperature
- `getOutputVoltage() -> int`  
  Returns output voltage (unit: mV)
- `getInputVoltage() -> int`  
  Returns input voltage (unit: mV)
- `getBatteryVoltage() -> int`  
  Returns battery voltage (unit: mV)
- `getMcuVoltage() -> int`  
  Returns MCU working voltage (unit: mV)
- `getOutputCurrent() -> int`  
  Returns output current (unit: mA)
- `getInputCurrent() -> int`  
  Returns input current (unit: mA)
- `getBatteryCurrent() -> int`  
  Returns battery current (unit: mA)
- `getTemperature() -> int`  
  Returns temperature (unit: °C, range: -40 to 85)

## TFTModule Class

# Graphics Primitive Functions

| Function | Purpose | Parameters |
|---------|---------|------------|
| `init` | Initialize/reset the display hardware and the library’s internal state.<br>Call once before any drawing operation. | *none* |
| `drawPixel` | Light up a single pixel | `x`, `y` – screen coordinates of the pixel<br>`color` – color value to paint |
| `drawLine` | Draw a straight line between two points | `x0`, `y0` – start-point coordinates<br>`x1`, `y1` – end-point coordinates<br>`color` – line color |
| `drawFastVLine` | Draw a vertical line optimized for speed | `x` – horizontal position (column)<br>`y` – top-most vertical position<br>`h` – height in pixels (line extends downward)<br>`color` – line color |
| `drawFastHLine` | Draw a horizontal line optimized for speed | `x` – left-most horizontal position<br>`y` – vertical position (row)<br>`w` – width in pixels (line extends rightward)<br>`color` – line color |
| `drawRect` | Draw the outline of a rectangle | `x`, `y` – top-left corner coordinates<br>`w` – width in pixels<br>`h` – height in pixels<br>`color` – outline color |
| `drawCircle` | Draw the outline of a circle | `x0`, `y0` – center coordinates<br>`r` – radius in pixels<br>`color` – outline color |
| `fillRect` | Draw a solid (filled) rectangle | Same as `drawRect`, but the interior is filled |
| `fillScreen` | Fill the entire display with one color | `color` – color to paint the whole screen |
| `drawTriangle` | Draw the outline of a triangle | `x0`, `y0` – vertex 0 coordinates<br>`x1`, `y1` – vertex 1 coordinates<br>`x2`, `y2` – vertex 2 coordinates<br>`color` – outline color |
| `fillTriangle` | Draw a solid (filled) triangle | Same vertex parameters as `drawTriangle`, but the interior is filled |
| `drawChar` | Draw a **single character** at the given position.<br>(Unless stated otherwise, this is the recommended character-drawing routine.) | `x`, `y` – top-left corner of the character cell<br>`c` – ASCII code of the character to draw (passed as `int`)<br>`color` – foreground color of the glyph<br>`bg` – background color that fills the cell behind the glyph<br>`size` – pixel scaling factor (1 = native 5×8, 2 = 10×16, …) |
| `drawString` | Draw a **null-terminated string** starting at the given position. | `x`, `y` – top-left corner of the first character<br>`c` – the text string to render (`str`)<br>`color` – foreground color for every glyph<br>`bg` – background color for every glyph<br>`size` – pixel scaling factor (same meaning as in `drawChar`) |

## NOTE：
-  `drawFast` series routines are **not recommended for external use**.
  These functions are **intended for internal device calls by default**.  
  When invoking them directly, **ensure all parameters stay within valid bounds**; exceeding the allowed range **will crash the Python runtime**.
- `drawFastVLine` and `drawFastHLine` performs no bounds checking—faster but generally unsafe.

## Demo Code

```python
from UPS import TFTModule as tft
from UPS import Device

# init TFT module
tft.init()

# test drawPixel function 
def test_drawPixel():
    tft.drawPixel(10, 10, 0xF800)  # draw red pixel on (10, 10) 
    Device.sleep(200)              # delay for a while
    tft.fillScreen(0x0000)  #  clear screen , fill it with black color

def test_drawLine():
    tft.drawLine(0, 0, 100, 100, 0x07E0)  # green cross line
    Device.sleep(200)
    tft.fillScreen(0x0000)

def test_drawFastVLine():
    tft.drawFastVLine(50, 0, 100, 0x001F)  #  blue vertical line
    Device.sleep(200)
    tft.fillScreen(0x0000)

def test_drawFastHLine():
    tft.drawFastHLine(0, 50, 100, 0xFFE0)  # yellow horizontal line
    Device.sleep(200)
    tft.fillScreen(0x0000)

def test_drawRect():
    tft.drawRect(20, 20, 60, 60, 0xF81F)  # pink rectangle
    Device.sleep(200)
    tft.fillScreen(0x0000)

def test_drawCircle():
    tft.drawCircle(50, 50, 30, 0x07FF)  # cyan circle
    Device.sleep(200)
    tft.fillScreen(0x0000)

def test_fillRect():
    tft.fillRect(30, 30, 40, 40, 0x7E0F)  # purple filled rectangle
    Device.sleep(200)
    tft.fillScreen(0x0000)

def test_drawTriangle():
    tft.drawTriangle(50, 10, 10, 90, 90, 90, 0x000F)  # deep blue trangle
    Device.sleep(200)
    tft.fillScreen(0x0000)

def test_fillTriangle():
    tft.fillTriangle(50, 10, 10, 90, 90, 90, 0xF0F0)  # light pink filled trangle
    Device.sleep(200)
    tft.fillScreen(0x0000)

def test_drawString():
    tft.drawString(10, 10, "Size 1", 0xF800, 0x0000, 1)  # red，size 1
    tft.drawString(10, 30, "Size 2", 0x07E0, 0x0000, 2)  # green，size 2
    tft.drawString(10, 60, "Size 3", 0x001F, 0x0000, 3)  # blue，size 3
    tft.drawString(10, 100, "Size 4", 0xFFE0, 0x0000, 4)  # yellow，size 4
    tft.drawString(10, 160, "FanSe 5", 0xFFFF, 0x07FF, 5)  # white，size 5

# run all test
while True:
    test_drawPixel()
    test_drawLine()
    test_drawFastVLine()
    test_drawFastHLine()
    test_drawRect()
    test_drawCircle()
    test_fillRect()
    test_drawTriangle()
    test_fillTriangle()
    test_drawString()
```
