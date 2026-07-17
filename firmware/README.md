# Firmware

The firmware is organized by device:

- `central_controller/`: local state machine, relay commands, ESP-NOW reception, and ThingSpeak publishing.
- `flow_node/`: turbine-flow pulse counting and ESP-NOW transmission.
- `level_node/`: M5Stack Ultrasonic-I2C acquisition, tank-volume estimation, and ESP-NOW transmission.
- `drivers/`: small hardware drivers shared by the nodes.

## Deployment checklist

1. Copy each `config.example.py` to `config.py`.
2. Set the controller and peer MAC addresses.
3. Verify GPIO pins and active-high/active-low relay behavior.
4. Calibrate `FLOW_PULSES_PER_LITER` and tank geometry.
5. Test every protection with pumps electrically isolated before live commissioning.
6. Keep emergency stops and original motor protections independent of the microcontroller.
