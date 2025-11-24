#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pygame
import time
import math
from collections import deque
import smbus

# -----------------------------
# Register addresses (constants)
# -----------------------------
WHO_AM_I = 0x00
VERSION  = 0x01
UUID0    = 0x02  # 32-bit
UUID1    = 0x06  # 32-bit
UUID2    = 0x0A  # 32-bit
OUT_VOLT = 0x0E  # 16-bit mV
IN_VOLT  = 0x10  # 16-bit mV
BAT_VOLT = 0x12  # 16-bit mV
MCU_VOLT = 0x14  # 16-bit mV
OUT_CURR = 0x16  # 16-bit mA
IN_CURR  = 0x18  # 16-bit mA
BAT_CURR = 0x1A  # 16-bit signed mA
TEMP     = 0x1C  # 8-bit signed °C
CR1      = 0x1D  # 8-bit
CR2      = 0x1E  # 8-bit (reserved)
SR1      = 0x1F  # 8-bit (status 1)
SR2      = 0x20  # 8-bit (status 2)
BAT_PROT = 0x21  # 16-bit mV
SHDN_CTD = 0x23  # 16-bit seconds
AUTO_VTH = 0x25  # 16-bit mV
RSV_LEN  = 0x27  # 16-bit length (buffer length)
OTA_REQ  = 0x29  # 16-bit W only, write 0xA5A5 to request
RUNTIME  = 0x2B  # 64-bit microseconds
CHG_DET  = 0x33  # 16-bit seconds
LED_CTL  = 0x35  # 8-bit

# CR1 bits
CR1_AUTO_START = 0  # BIT0

# SR1 bits
SR1_SW_STATUS   = 0
SR1_FAST        = 1
SR1_CHARGE      = 2
SR1_INPUT_LOW   = 3
SR1_OUTPUT_LOW  = 4
SR1_BAT_LOW     = 5
SR1_ADC_MISM    = 6
SR1_BAT_FAIL    = 7

# LED control bits
LED_I2C_ACK     = 0
LED_BAT_CHG     = 1
LED_BAT_DISCHG  = 2
LED_FAULT       = 3
LED_OK          = 4

def clamp(x, lo, hi):
    """Clamp value x between lo and hi."""
    return max(lo, min(hi, x))

def to_twos_complement_16(n):
    """Convert n to 16-bit two's complement representation."""
    return n & 0xFFFF

def from_twos_complement_8(v):
    """Convert 8-bit two's complement value v to signed integer."""
    v &= 0xFF
    return v - 256 if v & 0x80 else v

def from_twos_complement_16(v):
    """Convert 16-bit two's complement value v to signed integer."""
    v &= 0xFFFF
    return v - 65536 if v & 0x8000 else v

# -------------------
# Minimal UI elements
# -------------------
class Button:
    """A simple button UI element."""
    def __init__(self, rect, text, on_click, font):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.on_click = on_click
        self.font = font
        self.enabled = True

    def handle(self, ev):
        """Handle mouse events."""
        if not self.enabled:
            return
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.rect.collidepoint(ev.pos):
                self.on_click()

    def draw(self, surf):
        """Draw the button on the surface."""
        color = (60, 120, 200) if self.enabled else (100, 100, 100)
        pygame.draw.rect(surf, color, self.rect, border_radius=10)
        pygame.draw.rect(surf, (20, 20, 30), self.rect, width=2, border_radius=10)
        txt = self.font.render(self.text, True, (255, 255, 255))
        surf.blit(txt, txt.get_rect(center=self.rect.center))

class Toggle:
    """A toggle switch UI element."""
    def __init__(self, rect, label, get_func, set_func, font):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.get_func = get_func
        self.set_func = set_func
        self.font = font

    def handle(self, ev):
        """Handle mouse events."""
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.rect.collidepoint(ev.pos):
                self.set_func(not self.get_func())

    def draw(self, surf):
        """Draw the toggle on the surface."""
        on = self.get_func()
        box = pygame.Rect(self.rect.x, self.rect.y, 22, 22)
        pygame.draw.rect(surf, (20, 20, 30), box, border_radius=4)
        pygame.draw.rect(surf, (200, 200, 200), box, width=2, border_radius=4)
        if on:
            pygame.draw.rect(surf, (80, 200, 120), box.inflate(-6, -6), border_radius=3)
        label_surf = self.font.render(self.label, True, (230, 230, 230))
        surf.blit(label_surf, (self.rect.x + 28, self.rect.y + 2))

class BitLamp:
    """A small indicator light for a single bit."""
    def __init__(self, pos, label, font):
        self.pos = pos
        self.label = label
        self.font = font
        self.state = False

    def set(self, v: bool):
        """Set the state of the lamp."""
        self.state = bool(v)

    def draw(self, surf):
        """Draw the lamp on the surface."""
        x, y = self.pos
        r = 8
        color = (80, 200, 120) if self.state else (60, 60, 60)
        pygame.draw.circle(surf, color, (x, y), r)
        pygame.draw.circle(surf, (20, 20, 30), (x, y), r, width=2)
        label_surf = self.font.render(self.label, True, (230, 230, 230))
        surf.blit(label_surf, (x + 14, y - 10))

class NumberField:
    """A numeric input field with validation."""
    def __init__(self, rect, get_func, set_func, font, suffix="", hit_inflate=(180, 10)):
        self.rect = pygame.Rect(rect)
        self.get_func = get_func
        self.set_func = set_func
        self.font = font
        self.suffix = suffix
        self.active = False
        self.buffer = ""
        self.hit_inflate = hit_inflate
        self.hit_rect = self.rect.inflate(*hit_inflate)

    def move_to(self, x, y):
        """Move the field to a new position."""
        self.rect.topleft = (x, y)
        self.hit_rect = self.rect.inflate(*self.hit_inflate)

    def handle(self, ev):
        """Handle keyboard and mouse events."""
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            self.active = self.hit_rect.collidepoint(ev.pos)
            if self.active:
                self.buffer = str(self.get_func())
        if self.active and ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                self.active = False
            elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                try:
                    val = int(self.buffer.strip())
                    self.set_func(val)
                except ValueError:
                    pass
                self.active = False
            elif ev.key == pygame.K_BACKSPACE:
                self.buffer = self.buffer[:-1]
            else:
                if ev.unicode and (ev.unicode.isdigit() or (ev.unicode == '-' and len(self.buffer) == 0)):
                    self.buffer += ev.unicode

    def draw(self, surf):
        """Draw the field on the surface."""
        border = (120, 200, 255) if self.active else (90, 90, 110)
        pygame.draw.rect(surf, (30, 30, 40), self.rect, border_radius=6)
        pygame.draw.rect(surf, border, self.rect, width=2, border_radius=6)
        text_val = self.buffer if self.active else str(self.get_func())
        label = f"{text_val}{self.suffix}"
        txt = self.font.render(label, True, (240, 240, 240))
        surf.blit(txt, txt.get_rect(center=self.rect.center))
        if self.active and (pygame.time.get_ticks() // 500) % 2 == 0:
            caret = self.font.render("|", True, (240, 240, 240))
            cr = caret.get_rect()
            cr.midleft = (txt.get_rect(center=self.rect.center).right + 3, self.rect.centery - cr.h//2 + caret.get_height()//2)
            surf.blit(caret, cr)

# -----------------
# Tiny line charts
# -----------------
class TinyChart:
    """A small line chart for displaying sensor data."""
    def __init__(self, rect, title, series, font, maxlen=240):
        self.rect = pygame.Rect(rect)
        self.title = title
        self.series = series
        self.font = font
        self.maxlen = maxlen
        self.data = {name: deque(maxlen=maxlen) for name, _ in series}

    def push(self, device):
        """Push new data from the device."""
        for name, getter in self.series:
            try:
                v = getter(device)
            except Exception:
                v = 0
            self.data[name].append(v)

    def _minmax(self):
        """Calculate the min and max values for scaling."""
        vals = [v for seq in self.data.values() for v in seq]
        if not vals:
            return 0, 1
        lo, hi = min(vals), max(vals)
        if hi - lo < 1e-6:
            hi = lo + 1.0
        pad = (hi - lo) * 0.1 + 1e-6
        return lo - pad, hi + pad

    def draw(self, surf):
        """Draw the chart on the surface."""
        pygame.draw.rect(surf, (35, 45, 60), self.rect, border_radius=10)
        pygame.draw.rect(surf, (25, 30, 45), self.rect, width=2, border_radius=10)

        title_s = self.font.render(self.title, True, (240, 240, 240))
        surf.blit(title_s, (self.rect.x + 10, self.rect.y + 6))

        plot = self.rect.inflate(-16, -28)
        plot.y += 16
        pygame.draw.rect(surf, (18, 18, 24), plot, border_radius=8)

        lo, hi = self._minmax()
        rng = (hi - lo) or 1.0

        for i in range(1, 3):
            y = plot.y + int(i * plot.h / 3)
            pygame.draw.line(surf, (55, 55, 70), (plot.x, y), (plot.right, y), width=1)

        colors = [(200, 200, 230), (120, 200, 140), (200, 160, 120)]
        for idx, (name, _getter) in enumerate(self.series):
            seq = self.data[name]
            if len(seq) < 2:
                continue
            pts = []
            for i, v in enumerate(seq):
                x = plot.x + int(i * (plot.w-1) / (self.maxlen-1))
                y = plot.bottom - int((v - lo) / rng * (plot.h-1))
                pts.append((x, y))
            pygame.draw.lines(surf, colors[idx % len(colors)], False, pts, 2)
            leg = self.font.render(name, True, colors[idx % len(colors)])
            surf.blit(leg, (plot.right - 100, self.rect.y + 6 + 18*idx))

# -----------------
# Helper formatting
# -----------------
def fmt_mv(v): return f"{v} mV"
def fmt_ma(v): return f"{v} mA"
def fmt_temp(s8): return f"{s8} °C"
def fmt_hex8(v): return f"0x{v & 0xFF:02X}"
def fmt_hex16(v): return f"0x{v & 0xFFFF:04X}"
def fmt_hex32(v): return f"0x{v & 0xFFFFFFFF:08X}"
def fmt_runtime_us(us):
    sec = us / 1_000_000.0
    h = int(sec // 3600); sec -= h * 3600
    m = int(sec // 60); sec -= m * 60
    return f"{h:02d}:{m:02d}:{sec:05.2f}"

# ----------------------
# Device read & behavior
# ----------------------
class ReadDevice:
    """A class representing the device with I2C communication."""
    def __init__(self, i2c_address):
        self.bus = smbus.SMBus(1)  # I2C-1
        self.i2c_address = i2c_address

        self.reg8  = {}
        self.reg16 = {}
        self.reg32 = {}
        self.reg64 = {}

        # Initialize registers
        self.reg8[WHO_AM_I] = self.read8(WHO_AM_I)
        self.reg8[VERSION]  = self.read8(VERSION)
        self.reg8[CR1]      = self.read8(CR1)
        self.reg8[CR2]      = self.read8(CR2)
        self.reg8[SR1]      = self.read8(SR1)
        self.reg8[SR2]      = self.read8(SR2)
        self.reg8[LED_CTL]  = self.read8(LED_CTL)

        self.reg32[UUID0] = self.read32(UUID0)
        self.reg32[UUID1] = self.read32(UUID1)
        self.reg32[UUID2] = self.read32(UUID2)

        self.reg64[RUNTIME] = self.read64(RUNTIME)

        self.reg16[BAT_PROT] = self.read16(BAT_PROT)
        self.reg16[AUTO_VTH] = self.read16(AUTO_VTH)
        self.reg16[SHDN_CTD] = self.read16(SHDN_CTD)
        self.reg16[CHG_DET]  = self.read16(CHG_DET)
        self.reg16[RSV_LEN]  = self.read16(RSV_LEN)

        self.reg16[OUT_VOLT] = self.read16(OUT_VOLT)
        self.reg16[IN_VOLT]  = self.read16(IN_VOLT)
        self.reg16[BAT_VOLT] = self.read16(BAT_VOLT)
        self.reg16[MCU_VOLT] = self.read16(MCU_VOLT)
        self.reg16[OUT_CURR] = self.read16(OUT_CURR)
        self.reg16[IN_CURR]  = self.read16(IN_CURR)
        self.reg16[BAT_CURR] = self.read16(BAT_CURR)
        self.reg8[TEMP] = self.read8(TEMP)

    def read8(self, addr):
        """Read an 8-bit value from the device."""
        return self.bus.read_byte_data(self.i2c_address, addr)

    def read16(self, addr):
        """Read a 16-bit value from the device."""
        return self.bus.read_word_data(self.i2c_address, addr)

    def read32(self, addr):
        """Read a 32-bit value from the device."""
        data = self.bus.read_i2c_block_data(self.i2c_address, addr, 4)
        return (data[3] << 24) | (data[2] << 16) | (data[1] << 8) | data[0]

    def read64(self, addr):
        """Read a 64-bit value from the device."""
        data = self.bus.read_i2c_block_data(self.i2c_address, addr, 8)
        return (data[7] << 56) | (data[6] << 48) | (data[5] << 40) | (data[4] << 32) | \
               (data[3] << 24) | (data[2] << 16) | (data[1] << 8) | data[0]

    def write8(self, addr, value):
        """Write an 8-bit value to the device."""
        self.bus.write_byte_data(self.i2c_address, addr, value & 0xFF)

    def write16(self, addr, value):
        """Write a 16-bit value to the device."""
        self.bus.write_word_data(self.i2c_address, addr, value & 0xFFFF)

    def write32(self, addr, value):
        """Write a 32-bit value to the device."""
        self.bus.write_i2c_block_data(self.i2c_address, addr, [(value >> 24) & 0xFF, (value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF])

    def write64(self, addr, value):
        """Write a 64-bit value to the device."""
        self.bus.write_i2c_block_data(self.i2c_address, addr, [(value >> 56) & 0xFF, (value >> 48) & 0xFF, (value >> 40) & 0xFF, (value >> 32) & 0xFF, 
                                                               (value >> 24) & 0xFF, (value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF])

    def update_sensors(self, dt):
        """Update sensor values."""
        dt = min(dt, 1.0)  # Limit the maximum time step to 1 second
        self.reg64[RUNTIME] = (self.reg64[RUNTIME] + int(dt * 1_000_000)) & 0xFFFFFFFFFFFFFFFF

        self.reg16[IN_VOLT] = self.read16(IN_VOLT)
        self.reg16[OUT_VOLT] = self.read16(OUT_VOLT)
        self.reg16[MCU_VOLT] = self.read16(MCU_VOLT)

        bat_mv = self.reg16[BAT_VOLT]
        self.reg16[BAT_VOLT] = self.read16(BAT_VOLT)

        self.reg16[OUT_CURR] = self.read16(OUT_CURR)
        self.reg16[IN_CURR]  = self.read16(IN_CURR)

        self.reg16[BAT_CURR] = from_twos_complement_16(self.read16(BAT_CURR))

        self.reg8[TEMP] = from_twos_complement_8(self.read8(TEMP))

        sr1 = 0
        if self.reg16[OUT_VOLT] > 100: sr1 |= (1 << SR1_SW_STATUS)
        if self.reg16[IN_VOLT] > 10500: sr1 |= (1 << SR1_FAST)
        if self.reg16[BAT_CURR] > 0: sr1 |= (1 << SR1_CHARGE)
        if self.reg16[IN_VOLT] < 9500: sr1 |= (1 << SR1_INPUT_LOW)
        if self.reg16[OUT_VOLT] < 4900: sr1 |= (1 << SR1_OUTPUT_LOW)
        if self.reg16[BAT_VOLT] < self.reg16[BAT_PROT]: sr1 |= (1 << SR1_BAT_LOW)
        if (pygame.time.get_ticks() // 17000) % 2 == 0: sr1 |= (1 << SR1_ADC_MISM)
        self.reg8[SR1] = sr1 & 0xFF

# --------------
# Main UI screen
# --------------
class PanelApp:
    """The main application class for the UI."""
    def __init__(self, device):
        pygame.init()
        pygame.display.set_caption("52Pi UPS Gen 6 Management UI Panel V1.0")
        self.screen = pygame.display.set_mode((1200, 740))
        self.clock = pygame.time.Clock()
        self.font  = pygame.font.SysFont("consolas,menlo,monospace", 18)
        self.font_small = pygame.font.SysFont("consolas,menlo,monospace", 16)
        self.device = device
        self.running = True
        self.last_snapshot = None
        self._build_widgets()

    def _get_bit(self, v, bit): return ((v >> bit) & 1) != 0
    def _set_bit(self, v, bit, on): return (v | (1 << bit)) if on else (v & ~(1 << bit))

    def _build_widgets(self):
        """Build UI widgets."""
        f = self.font
        # CR1 toggle
        def get_auto(): return self._get_bit(self.device.read8(CR1), CR1_AUTO_START)
        def set_auto(on):
            v = self.device.read8(CR1)
            v = self._set_bit(v, CR1_AUTO_START, on)
            self.device.write8(CR1, v)
        self.cr1_toggle = Toggle((30, 420, 240, 26), "CR1.auto_start_mode", get_auto, set_auto, f)

        # LED toggles (2 columns)
        def led_get(bit): return self._get_bit(self.device.read8(LED_CTL), bit)
        def led_set(bit, on):
            v = self.device.read8(LED_CTL)
            v = self._set_bit(v, bit, on)
            self.device.write8(LED_CTL, v)
        self.led_toggles = []
        labels_bits = [("i2c_ack",LED_I2C_ACK),("bat_charge",LED_BAT_CHG),
                       ("bat_discharge",LED_BAT_DISCHG),("fault_report",LED_FAULT),
                       ("ok_report",LED_OK)]
        for i, (label, bit) in enumerate(labels_bits):
            row = i // 2
            col = i % 2
            x = 30 + col*170
            y = 456 + row*28
            t = Toggle((x, y, 160, 26),
                       f"LED.{label}",
                       lambda b=bit: led_get(b),
                       lambda on, b=bit: led_set(b, on),
                       f)
            self.led_toggles.append(t)

        # Editable fields
        self.num_fields = []
        def NF(rect, getf, setf, suffix):
            return NumberField(rect, getf, setf, self.font_small, suffix, hit_inflate=(180, 10))
        self.num_fields.append(("battery_protection_voltage", NF((30, 640, 260, 28),
            lambda: self.device.read16(BAT_PROT),
            lambda v: self.device.write16(BAT_PROT, clamp(v, 6000, 8400)), " mV")))
        self.num_fields.append(("auto_start_voltage", NF((30, 672, 260, 28),
            lambda: self.device.read16(AUTO_VTH),
            lambda v: self.device.write16(AUTO_VTH, clamp(v, 6000, 8400)), " mV")))
        self.num_fields.append(("shutdown_countdown", NF((300, 640, 260, 28),
            lambda: self.device.read16(SHDN_CTD),
            lambda v: self.device.write16(SHDN_CTD, clamp(v, 0, 3600)), " s")))
        self.num_fields.append(("charge_detect_interval_s", NF((300, 672, 260, 28),
            lambda: self.device.read16(CHG_DET),
            lambda v: self.device.write16(CHG_DET, clamp(v, 1, 600)), " s")))

        # Buttons
        self.btn_sync = Button((820, 700, 160, 30), "Sync Setting", self.sync_settings, self.font_small)
        self.btn_ota  = Button((990, 700, 160, 30), "Request OTA", lambda: self.device.write16(OTA_REQ, 0xA5A5), self.font_small)

        # Charts
        self.chart_v = TinyChart(pygame.Rect(570, 270, 600, 140), "Voltages (mV)",
                                 [("V-out", lambda d: d.read16(OUT_VOLT)),
                                  ("V-in",  lambda d: d.read16(IN_VOLT))],
                                 self.font_small, maxlen=260)
        self.chart_c = TinyChart(pygame.Rect(570, 430, 600, 140), "Currents (mA)",
                                 [("I-out", lambda d: d.read16(OUT_CURR)),
                                  ("I-bat", lambda d: from_twos_complement_16(d.read16(BAT_CURR)))],
                                 self.font_small, maxlen=260)

    def draw_section_title(self, x, y, title, w=540):
        """Draw a section title."""
        bar = pygame.Rect(x, y, w, 28)
        pygame.draw.rect(self.screen, (45, 60, 90), bar, border_radius=10)
        pygame.draw.rect(self.screen, (25, 30, 45), bar, width=2, border_radius=10)
        txt = self.font.render(title, True, (250, 250, 250))
        self.screen.blit(txt, (x + 12, y + 4))
        return bar.bottom + 10

    def draw_kv(self, x, y, name, value):
        """Draw a key-value pair."""
        name_s = self.font.render(name, True, (200, 200, 210))
        val_s  = self.font.render(value, True, (240, 240, 240))
        self.screen.blit(name_s, (x, y))
        self.screen.blit(val_s,  (x + 210, y))

    def sync_settings(self):
        """Capture current settings as a snapshot."""
        led = self.device.read8(LED_CTL)
        self.last_snapshot = {
            "auto_start_mode": 1 if (self.device.read8(CR1) & (1 << CR1_AUTO_START)) else 0,
            "LED_CTL_raw": fmt_hex8(led),
            "LED.bits": {
                "i2c_ack":     1 if (led & (1<<LED_I2C_ACK)) else 0,
                "bat_charge":  1 if (led & (1<<LED_BAT_CHG)) else 0,
                "bat_discharge":1 if (led & (1<<LED_BAT_DISCHG)) else 0,
                "fault_report":1 if (led & (1<<LED_FAULT)) else 0,
                "ok_report":   1 if (led & (1<<LED_OK)) else 0,
            },
            "battery_protection_voltage": self.device.read16(BAT_PROT),
            "auto_start_voltage": self.device.read16(AUTO_VTH),
            "shutdown_countdown": self.device.read16(SHDN_CTD),
            "charge_detect_interval_s": self.device.read16(CHG_DET),
        }

    def _layout_inputs(self, cfg_title_y):
        """Layout input fields."""
        base_y = cfg_title_y + 32   # First input field's top edge
        row_h  = 52                 # Row spacing

        positions = [
            (30,  base_y + 0*row_h),   # battery_protection_voltage
            (30,  base_y + 1*row_h),   # auto_start_voltage
            (300, base_y + 0*row_h),   # shutdown_countdown
            (300, base_y + 1*row_h),   # charge_detect_interval_s
        ]
        for (_, nf), (x, yy) in zip(self.num_fields, positions):
            nf.move_to(x, yy)

    def draw_snapshot_panel(self, x, y, w=600, h=90):
        """Draw the snapshot panel."""
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, (35, 45, 60), rect, border_radius=10)
        pygame.draw.rect(self.screen, (25, 30, 45), rect, width=2, border_radius=10)
        title = self.font_small.render("Synced Settings (snapshot)", True, (240, 240, 240))
        self.screen.blit(title, (x + 10, y + 6))
        if not self.last_snapshot:
            hint = self.font_small.render("Press 'Sync Setting' to capture current values.", True, (200, 200, 210))
            self.screen.blit(hint, (x + 10, y + 28))
            return
        yy = y + 26
        kv = self.last_snapshot
        lines = [
            f"auto_start_mode: {kv['auto_start_mode']}   LED_CTL: {kv['LED_CTL_raw']}",
            f"LED bits: i2c_ack={kv['LED.bits']['i2c_ack']} charge={kv['LED.bits']['bat_charge']} discharge={kv['LED.bits']['bat_discharge']} fault={kv['LED.bits']['fault_report']} ok={kv['LED.bits']['ok_report']}",
            f"bat_prot: {kv['battery_protection_voltage']} mV   auto_start: {kv['auto_start_voltage']} mV   shutdown: {kv['shutdown_countdown']} s",
        ]
        for line in lines:
            s = self.font_small.render(line, True, (230, 230, 235))
            self.screen.blit(s, (x + 10, yy))
            yy += 18

    def draw(self):
        """Draw the entire UI."""
        self.screen.fill((16, 18, 24))
        #self.screen.fill((220, 230, 240))

        # --- Left: Live readings ---
        y = self.draw_section_title(20, 16, "Live Readings", w=540)
        self.draw_kv(30, y, "WHO_AM_I", fmt_hex8(self.device.read8(WHO_AM_I))); y += 24
        self.draw_kv(30, y, "version",  fmt_hex8(self.device.read8(VERSION))); y += 24

        # UUID lines (wrap; filter empty to avoid first-line blank)
        u0 = self.device.read32(UUID0); u1 = self.device.read32(UUID1); u2 = self.device.read32(UUID2)
        uuid_str = f"{u2:08X}-{u1:08X}-{u0:08X}"
        lines = [uuid_str[i:i+22] for i in range(0, len(uuid_str), 22) if uuid_str[i:i+22]]
        self.draw_kv(30, y, "uuid", lines[0]); y += 22
        for line in lines[1:]:
            s = self.font.render(line, True, (240, 240, 240))
            self.screen.blit(s, (30 + 210, y))
            y += 20

        for label, val in [
            ("output_voltage", fmt_mv(self.device.read16(OUT_VOLT))),
            ("input_voltage",  fmt_mv(self.device.read16(IN_VOLT))),
            ("battery_voltage",fmt_mv(self.device.read16(BAT_VOLT))),
            ("mcu_voltage",    fmt_mv(self.device.read16(MCU_VOLT))),
            ("output_current", fmt_ma(self.device.read16(OUT_CURR))),
            ("input_current",  fmt_ma(self.device.read16(IN_CURR))),
            ("battery_current",fmt_ma(from_twos_complement_16(self.device.read16(BAT_CURR)))),
            ("temperature",    fmt_temp(from_twos_complement_8(self.device.read8(TEMP)))),
        ]:
            self.draw_kv(30, y, label, val); y += 22
        run_us = self.device.read64(RUNTIME)
        self.draw_kv(30, y, "runtime", f"{fmt_runtime_us(run_us)}"); y += 22

        # --- Left middle: CR1 & LED ---
        y = self.draw_section_title(20, y + 6, "CR1 & LED Control", w=540)
        self.cr1_toggle.rect.topleft = (30, y + 6)
        self.cr1_toggle.draw(self.screen)

        base_y = y + 36
        for i, t in enumerate(self.led_toggles):
            row = i // 2; col = i % 2
            t.rect.topleft = (30 + col*240, base_y + row*28)
            t.draw(self.screen)

        # LED raw
        led_raw_y = base_y + ((len(self.led_toggles)+1)//2)*28 + 8
        self.draw_kv(20, led_raw_y, "LED_CTL (raw)", fmt_hex8(self.device.read8(LED_CTL)))

        # --- Left bottom: Config (2 columns) ---
        cfg_title_y = self.draw_section_title(20, led_raw_y + 28, "Config (editable)", w=540)
        self._layout_inputs(cfg_title_y)
        for (name, nf) in self.num_fields:
            lab = self.font_small.render(name, True, (220, 220, 230))
            # label is drawn 16px above each field; we already set positions in _layout_inputs
            self.screen.blit(lab, (nf.rect.x, nf.rect.y - 16))
            nf.draw(self.screen)

        # --- Right: Status & Charts ---
        y = self.draw_section_title(570, 16, "Status & Control", w=600)
        sr1 = self.device.read8(SR1)
        lamps = [
            (SR1_SW_STATUS,   "5V on"),
            (SR1_FAST,        "12V fast"),
            (SR1_CHARGE,      "discharging"),
            (SR1_INPUT_LOW,   "input_low"),
            (SR1_OUTPUT_LOW,  "output_low"),
            (SR1_BAT_LOW,     "battery_low"),
            (SR1_ADC_MISM,    "adc_mismatch"),
            (SR1_BAT_FAIL,    "battery_fail"),
        ]
        x0 = 580; y0 = y
        colx = [x0, x0+300]
        for i, (bit, label) in enumerate(lamps):
            col = i % 2
            row = i // 2
            lamp = BitLamp((colx[col], y0 + row*26), label, self.font_small)
            lamp.set(((sr1 >> bit) & 1) != 0)
            lamp.draw(self.screen)

        # Charts
        self.chart_v.draw(self.screen)
        self.chart_c.draw(self.screen)

        # Snapshot + Buttons
        self.draw_snapshot_panel(570, 580, w=600, h=90)
        self.btn_sync.draw(self.screen)
        self.btn_ota.draw(self.screen)

        pygame.display.flip()

    def handle_events(self):
        """Handle events."""
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.running = False
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_q and (ev.mod & pygame.KMOD_CTRL):
                self.running = False

            # Inputs first (positions already updated in draw() within this frame)
            for _name, nf in self.num_fields:
                nf.handle(ev)
            self.cr1_toggle.handle(ev)
            for t in self.led_toggles:
                t.handle(ev)
            self.btn_sync.handle(ev)
            self.btn_ota.handle(ev)

    def run(self):
        """Run the application."""
        last = time.time()
        # first draw once to place widgets before any clicks
        self.draw()
        while self.running:
            now = time.time()
            dt = now - last
            last = now
            # update device & charts first so draw reflects newest data
            self.device.update_sensors(dt)
            self.chart_v.push(self.device)
            self.chart_c.push(self.device)
            # draw first so hit-rects match positions, THEN handle events
            self.draw()
            self.handle_events()
            self.clock.tick(30)

def main():
    """Main function."""
    dev = ReadDevice(0x17)  # Replace with actual I2C address
    app = PanelApp(dev)
    app.run()
    pygame.quit()

if __name__ == "__main__":
    main()
