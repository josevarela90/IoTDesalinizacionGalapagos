# Copy to config.py and edit for the deployed installation.

WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"
THINGSPEAK_WRITE_KEY = "YOUR_WRITE_KEY"
THINGSPEAK_UPDATE_S = 20

# Enter the real GPIOs connected to the low-voltage relay interface.
RELAY_INLET_PIN = -1
RELAY_LOW_PRESSURE_PIN = -1
RELAY_HIGH_PRESSURE_PIN = -1
RELAY_ACTIVE_LOW = True

# Optional digital input used to request RO operation.
RO_REQUEST_PIN = -1
RO_REQUEST_ACTIVE_LOW = True

FLOW_START_L_MIN = 4.0
FLOW_STOP_L_MIN = 1.0
FLOW_LOSS_CONFIRM_S = 120
LOW_PRESSURE_PRIME_S = 5
RAW_TANK_MIN_L = 300.0
RAW_TANK_MAX_L = 6000.0
PRODUCT_TANK_MAX_L = 1000.0

# Field mapping can be changed to match the deployed ThingSpeak channel.
FIELD_RAW_TANK = 1
FIELD_PRODUCT_TANK = 2
FIELD_FLOW = 3
FIELD_STATE = 6
