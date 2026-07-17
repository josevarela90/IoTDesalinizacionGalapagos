"""Tank-level node using the M5Stack Ultrasonic-I2C unit."""

import math
import time
import network
import espnow
import ujson
from machine import I2C, Pin
import config
from ultrasonic_i2c import UltrasonicI2C

if config.TANK_ID not in ("raw", "product"):
    raise ValueError("TANK_ID must be 'raw' or 'product'")

bus = I2C(0, sda=Pin(config.I2C_SDA_PIN), scl=Pin(config.I2C_SCL_PIN), freq=400000)
sensor = UltrasonicI2C(bus, config.I2C_ADDRESS)

sta = network.WLAN(network.STA_IF)
sta.active(True)
radio = espnow.ESPNow()
radio.active(True)
radio.add_peer(config.CONTROLLER_MAC)


def tank_volume_l(distance_m):
    water_height = config.TANK_HEIGHT_M - distance_m + config.MOUNTING_OFFSET_M
    water_height = min(config.TANK_HEIGHT_M, max(0.0, water_height))
    volume_m3 = math.pi * config.TANK_RADIUS_M ** 2 * water_height
    return volume_m3 * 1000.0


while True:
    readings = []
    for _ in range(config.AVERAGE_SAMPLES):
        try:
            readings.append(sensor.distance_m())
        except OSError as exc:
            print("I2C read error", exc)
        time.sleep_ms(60)

    if readings:
        distance_m = sum(readings) / len(readings)
        volume_l = tank_volume_l(distance_m)
        packet = ujson.dumps({
            "type": "level",
            "tank": config.TANK_ID,
            "distance_m": round(distance_m, 4),
            "volume_l": round(volume_l, 1),
        })
        try:
            radio.send(config.CONTROLLER_MAC, packet)
        except OSError as exc:
            print("ESP-NOW send error", exc)

    time.sleep_ms(config.SAMPLE_INTERVAL_MS)
