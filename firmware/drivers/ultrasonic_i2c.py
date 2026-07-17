"""Minimal driver for the M5Stack Ultrasonic-I2C unit (default address 0x57)."""

import time


class UltrasonicI2C:
    def __init__(self, i2c, address=0x57):
        self.i2c = i2c
        self.address = address

    def distance_m(self):
        # Trigger one measurement, wait for conversion, then read 24-bit result.
        self.i2c.writeto(self.address, b"\x01")
        time.sleep_ms(50)
        raw = self.i2c.readfrom(self.address, 3)
        value = (raw[0] << 16) | (raw[1] << 8) | raw[2]
        distance_mm = value / 1000.0
        return distance_mm / 1000.0
