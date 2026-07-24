"""Select platform for BTF Lighting Devil Eyes (Flip Mode)."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    FLIP_LABELS,
    FLIP_NONE,
    FLIP_OPTIONS,
    FLIP_X,
    FLIP_XY,
    FLIP_Y,
)
from . import BtfDevilEyesDevice

_LOGGER = logging.getLogger(__name__)

# Flip command bytes
FLIP_COMMANDS = {
    FLIP_NONE: bytes([0x01, 0x00, 0x02, 0x06, 0x0C, 0x00, 0x03]),
    FLIP_XY: bytes([0x01, 0x00, 0x02, 0x06, 0x0C, 0x02, 0x05, 0x03]),
    FLIP_X: bytes([0x01, 0x00, 0x02, 0x06, 0x0C, 0x02, 0x06, 0x03]),
    FLIP_Y: bytes([0x01, 0x00, 0x02, 0x06, 0x0C, 0x02, 0x07, 0x03]),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the select platform."""
    device: BtfDevilEyesDevice = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BtfDevilEyesFlipSelect(device)])


class BtfDevilEyesFlipSelect(SelectEntity):
    """Flip mode selector."""

    _attr_has_entity_name = True
    _attr_name = "Flip-Modus"
    _attr_assumed_state = True
    _attr_current_option = FLIP_NONE

    def __init__(self, device: BtfDevilEyesDevice) -> None:
        self._device = device
        self._attr_unique_id = f"{device.address}_flip"
        self._attr_device_info = device.device_info
        self._attr_options = [FLIP_NONE, FLIP_XY, FLIP_X, FLIP_Y]
        self._attr_translation_key = "flip_mode"
        self._attr_icon = "mdi:rotate-3d-variant"

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option not in FLIP_COMMANDS:
            return

        cmd = FLIP_COMMANDS[option]
        await self._device.async_write(cmd)
        self._attr_current_option = option
        self.async_write_ha_state()
