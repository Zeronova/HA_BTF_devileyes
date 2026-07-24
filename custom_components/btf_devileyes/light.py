"""Light platform for BTF Lighting Devil Eyes."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from . import BtfDevilEyesDevice

_LOGGER = logging.getLogger(__name__)

# Command: 01 00 02 06 05 [state] 03
CMD_ON = bytes([0x01, 0x00, 0x02, 0x06, 0x05, 0x02, 0x05, 0x03])
CMD_OFF = bytes([0x01, 0x00, 0x02, 0x06, 0x05, 0x00, 0x03])

# Brightness: 01 00 02 06 04 [value] 03
CMD_BRIGHTNESS_TEMPLATE = bytes([0x01, 0x00, 0x02, 0x06, 0x04, 0x00, 0x03])


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the light platform."""
    device: BtfDevilEyesDevice = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BtfDevilEyesLight(device)])


class BtfDevilEyesLight(LightEntity):
    """Representation of a BTF Lighting Devil Eyes light."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_assumed_state = True  # no feedback yet

    def __init__(self, device: BtfDevilEyesDevice) -> None:
        self._device = device
        self._attr_unique_id = f"{device.address}_light"
        self._attr_device_info = device.device_info
        self._attr_is_on = False
        self._attr_brightness = 255

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        success = False
        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            cmd = bytearray(CMD_BRIGHTNESS_TEMPLATE)
            cmd[5] = brightness
            success = await self._device.async_write(bytes(cmd))
            if success:
                self._attr_brightness = brightness
        else:
            success = await self._device.async_write(CMD_ON)

        if success:
            self._attr_is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        success = await self._device.async_write(CMD_OFF)
        if success:
            self._attr_is_on = False
            self.async_write_ha_state()
