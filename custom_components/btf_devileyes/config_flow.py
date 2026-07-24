"""Config flow for BTF Lighting Devil Eyes."""

from __future__ import annotations

import asyncio
from typing import Any

from bleak import BleakScanner
import voluptuous as vol

from homeassistant.components.bluetooth import (
    async_discovered_service_info,
    BluetoothServiceInfoBleak,
)
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CHARACTERISTIC_UUID,
    DOMAIN,
    SERVICE_UUID,
    SCAN_TIMEOUT,
)

# Known names that indicate a BTF/Jieli device
KNOWN_PREFIXES = ("BTF-LIGHTING", "ckc_")


def _is_btf_device(discovery: BluetoothServiceInfoBleak) -> bool:
    """Check if discovery matches a known BTF/Jieli device."""
    name = discovery.name or ""
    return name.startswith(KNOWN_PREFIXES)


class BtfDevilEyesConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BTF Devil Eyes."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered_devices: dict[str, BluetoothServiceInfoBleak] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            if user_input.get(CONF_ADDRESS) == "__manual__":
                return await self.async_step_manual()

            address = user_input[CONF_ADDRESS]
            discovery = self._discovered_devices[address]
            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=discovery.name or address,
                data={CONF_ADDRESS: address},
            )

        # Scan for BLE devices
        self._discovered_devices = {}
        for discovery in async_discovered_service_info(self.hass):
            if _is_btf_device(discovery):
                self._discovered_devices[discovery.address] = discovery

        if not self._discovered_devices:
            # Offer manual entry if nothing found
            return await self.async_step_manual()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(
                        {
                            **{
                                addr: f"{disc.name} ({addr})"
                                for addr, disc in self._discovered_devices.items()
                            },
                            "__manual__": "Manuelle Eingabe...",
                        }
                    ),
                }
            ),
        )

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manual MAC address entry."""
        errors = {}
        if user_input is not None:
            address = user_input[CONF_ADDRESS].strip().upper()
            # Basic MAC validation
            parts = address.split(":")
            if len(parts) != 6 or not all(len(p) == 2 for p in parts):
                errors["base"] = "invalid_mac"
            else:
                await self.async_set_unique_id(address)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=address,
                    data={CONF_ADDRESS: address},
                )

        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "name": "MAC-Adresse (z.B. D0:27:04:AE:73:40)",
            },
        )
