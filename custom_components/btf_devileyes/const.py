"""Constants for the BTF Lighting Devil Eyes integration."""

DOMAIN = "btf_devileyes"
MANUFACTURER = "BTF Lighting"
DEVICE_MODEL = "Devil Eyes Matrix Panel"

# BLE GATT UUIDs
SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"

# BLE connection
CONNECT_TIMEOUT = 20
SCAN_TIMEOUT = 30

# --- Command Protocol ---
# Format: 01 00 [len] [cmd] [data...] 03
# cmd 0x06 = control sub-commands

CONTROL_CMD = 0x06

# Sub-commands (data byte after CONTROL_CMD)
SUBCMD_BRIGHTNESS = 0x04  # followed by value (0x00-0xFF)
SUBCMD_POWER = 0x05       # followed by 0x00=off, 0x02=on
SUBCMD_MEMORY = 0x08      # memory/preset slot
SUBCMD_FLIP = 0x0C        # flip/orientation

# Flip mode options
FLIP_NONE = "none"
FLIP_XY = "xy"
FLIP_X = "x"
FLIP_Y = "y"

FLIP_OPTIONS = {
    FLIP_NONE: 0x00,
    FLIP_XY: 0x01,
    FLIP_X: 0x02,
    FLIP_Y: 0x03,
}

# Human-readable flip labels
FLIP_LABELS = {
    FLIP_NONE: "Kein Flip",
    FLIP_XY: "XY Flip",
    FLIP_X: "X Flip",
    FLIP_Y: "Y Flip",
}
