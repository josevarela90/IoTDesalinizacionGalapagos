"""Local-first desalination controller for MicroPython/ESP32.

This sanitized reference implementation mirrors the control logic documented
for the Galápagos deployment. Verify all GPIOs, interlocks, and relay polarity
before connecting power equipment.
"""

import time
import network
import espnow
import ujson
import urequests
from machine import Pin
import config

STATE_INLET_ON = 1
STATE_INLET_OFF = 2
STATE_LP_ON = 3
STATE_RO_OFF = 4
STATE_HP_ON = 6


def require_pin(value, name):
    if not isinstance(value, int) or value < 0:
        raise ValueError("Configure {} in config.py".format(name))
    return value


def make_output(pin_number):
    pin = Pin(require_pin(pin_number, "relay pin"), Pin.OUT)
    pin.value(1 if config.RELAY_ACTIVE_LOW else 0)
    return pin


class Relay:
    def __init__(self, pin):
        self.pin = pin
        self.enabled = False

    def set(self, enabled):
        self.enabled = bool(enabled)
        electrical = not self.enabled if config.RELAY_ACTIVE_LOW else self.enabled
        self.pin.value(1 if electrical else 0)


inlet = Relay(make_output(config.RELAY_INLET_PIN))
low_pressure = Relay(make_output(config.RELAY_LOW_PRESSURE_PIN))
high_pressure = Relay(make_output(config.RELAY_HIGH_PRESSURE_PIN))

if config.RO_REQUEST_PIN >= 0:
    ro_request_pin = Pin(config.RO_REQUEST_PIN, Pin.IN, Pin.PULL_UP)
else:
    ro_request_pin = None

sta = network.WLAN(network.STA_IF)
sta.active(True)
radio = espnow.ESPNow()
radio.active(True)

measurements = {
    "flow_l_min": 0.0,
    "raw_tank_l": None,
    "product_tank_l": None,
}
last_flow_ok_ms = time.ticks_ms()
low_pressure_started_ms = None
last_publish_ms = time.ticks_ms()
last_state = STATE_RO_OFF


def wifi_connect(timeout_s=15):
    if sta.isconnected():
        return True
    sta.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    deadline = time.ticks_add(time.ticks_ms(), timeout_s * 1000)
    while not sta.isconnected() and time.ticks_diff(deadline, time.ticks_ms()) > 0:
        time.sleep_ms(250)
    return sta.isconnected()


def set_state(code):
    global last_state
    if code != last_state:
        last_state = code
        print("state", code)


def stop_ro():
    global low_pressure_started_ms
    high_pressure.set(False)
    low_pressure.set(False)
    low_pressure_started_ms = None
    set_state(STATE_RO_OFF)


def ro_requested():
    if ro_request_pin is None:
        return False
    value = ro_request_pin.value()
    return (value == 0) if config.RO_REQUEST_ACTIVE_LOW else (value == 1)


def receive_sensor_messages():
    while True:
        host, payload = radio.irecv(0)
        if host is None:
            return
        try:
            msg = ujson.loads(payload)
            kind = msg.get("type")
            if kind == "flow":
                measurements["flow_l_min"] = max(0.0, float(msg["value"]))
            elif kind == "level":
                measurements[msg["tank"] + "_tank_l"] = max(0.0, float(msg["volume_l"]))
        except (ValueError, KeyError, TypeError) as exc:
            print("bad sensor packet", exc)


def update_control():
    global last_flow_ok_ms, low_pressure_started_ms
    now = time.ticks_ms()
    flow = measurements["flow_l_min"]
    raw_l = measurements["raw_tank_l"]
    product_l = measurements["product_tank_l"]

    raw_not_full = raw_l is None or raw_l < config.RAW_TANK_MAX_L
    if flow >= config.FLOW_START_L_MIN and raw_not_full:
        inlet.set(True)
        last_flow_ok_ms = now
        set_state(STATE_INLET_ON)
    elif inlet.enabled:
        flow_lost = time.ticks_diff(now, last_flow_ok_ms) >= config.FLOW_LOSS_CONFIRM_S * 1000
        tank_full = raw_l is not None and raw_l >= config.RAW_TANK_MAX_L
        if flow_lost or tank_full:
            inlet.set(False)
            set_state(STATE_INLET_OFF)

    raw_available = raw_l is None or raw_l > config.RAW_TANK_MIN_L
    product_not_full = product_l is None or product_l < config.PRODUCT_TANK_MAX_L
    safe_to_run = raw_available and product_not_full

    if not ro_requested() or not safe_to_run:
        stop_ro()
        return

    if not low_pressure.enabled:
        low_pressure.set(True)
        low_pressure_started_ms = now
        set_state(STATE_LP_ON)
        return

    flow_permissive = flow >= config.FLOW_START_L_MIN
    prime_elapsed = time.ticks_diff(now, low_pressure_started_ms) >= config.LOW_PRESSURE_PRIME_S * 1000
    if flow_permissive and prime_elapsed and not high_pressure.enabled:
        high_pressure.set(True)
        set_state(STATE_HP_ON)

    if high_pressure.enabled and flow <= config.FLOW_STOP_L_MIN:
        if time.ticks_diff(now, last_flow_ok_ms) >= config.FLOW_LOSS_CONFIRM_S * 1000:
            stop_ro()


def publish_thingspeak():
    if not config.THINGSPEAK_WRITE_KEY or config.THINGSPEAK_WRITE_KEY.startswith("YOUR_"):
        return
    if not wifi_connect():
        return

    params = ["api_key=" + config.THINGSPEAK_WRITE_KEY]
    mapping = (
        (config.FIELD_RAW_TANK, measurements["raw_tank_l"]),
        (config.FIELD_PRODUCT_TANK, measurements["product_tank_l"]),
        (config.FIELD_FLOW, measurements["flow_l_min"]),
        (config.FIELD_STATE, last_state),
    )
    for field, value in mapping:
        if value is not None:
            params.append("field{}={}".format(field, value))
    response = None
    try:
        response = urequests.get("https://api.thingspeak.com/update?" + "&".join(params))
        response.close()
    except Exception as exc:
        print("ThingSpeak error", exc)
        if response is not None:
            response.close()


wifi_connect()
print("controller ready")

while True:
    receive_sensor_messages()
    update_control()
    now = time.ticks_ms()
    if time.ticks_diff(now, last_publish_ms) >= config.THINGSPEAK_UPDATE_S * 1000:
        publish_thingspeak()
        last_publish_ms = now
    time.sleep_ms(100)
