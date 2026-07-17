"""Turbine-flow sensing node for MicroPython/ESP32."""

import time
import network
import espnow
import ujson
from machine import Pin, disable_irq, enable_irq
import config

if config.FLOW_INPUT_PIN < 0:
    raise ValueError("Configure FLOW_INPUT_PIN in config.py")

pulse_count = 0


def on_pulse(_):
    global pulse_count
    pulse_count += 1


sensor = Pin(config.FLOW_INPUT_PIN, Pin.IN, Pin.PULL_UP)
sensor.irq(trigger=Pin.IRQ_RISING, handler=on_pulse)

sta = network.WLAN(network.STA_IF)
sta.active(True)
radio = espnow.ESPNow()
radio.active(True)
radio.add_peer(config.CONTROLLER_MAC)

while True:
    time.sleep_ms(config.SAMPLE_INTERVAL_MS)
    irq_state = disable_irq()
    pulses = pulse_count
    pulse_count = 0
    enable_irq(irq_state)

    interval_s = config.SAMPLE_INTERVAL_MS / 1000.0
    flow_l_min = pulses * 60.0 / (config.FLOW_PULSES_PER_LITER * interval_s)
    packet = ujson.dumps({"type": "flow", "value": round(flow_l_min, 3)})
    try:
        radio.send(config.CONTROLLER_MAC, packet)
    except OSError as exc:
        print("ESP-NOW send error", exc)
