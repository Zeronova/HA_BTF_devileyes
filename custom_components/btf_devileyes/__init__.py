"""BTF Lighting Devil Eyes integration."""

from __future__ import annotations

import asyncio
import logging

from bleak import BleakClient, BleakError
from bleak.backends.device import BLEDevice
from home_assistant_bluetooth import BluetoothServiceInfoBleak

from homeassistant.components.bluetooth import (
    async_ble_device_from_address,
    async_discovered_service_info,
    async_register_scanner,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import Event, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    CHARACTERISTIC_UUID,
    CONNECT_TIMEOUT,
    DEVICE_MODEL,
    DOMAIN,
    MANUFACTURER,
    SERVICE_UUID,
)

PLATFORMS = ["light", "select"]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BTF Devil Eyes from a config entry."""
    address = entry.data[CONF_ADDRESS]
    ble_device = async_ble_device_from_address(hass, address)

    if not ble_device:
        raise ConfigEntryNotReady(
            f"BLE device {address} not found. Make sure it's in range."
        )

    device = BtfDevilEyesDevice(hass, address)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = device

    async def _async_stop(_: Event) -> None:
        await device.disconnect()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_stop)
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    device = hass.data[DOMAIN].pop(entry.entry_id, None)
    if device:
        await device.disconnect()
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return unload_ok


class BtfDevilEyesDevice:
    """Manages BLE connection and communication with the panel."""

    def __init__(self, hass: HomeAssistant, address: str) -> None:
        self.hass = hass
        self.address = address
        self._client: BleakClient | None = None
        self._lock = asyncio.Lock()
        self._notify_callback = None
        self._device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            name="BTF Devil Eyes",
            manufacturer=MANUFACTURER,
            model=DEVICE_MODEL,
            sw_version="Jieli AC695X",
            connections={("bluetooth", address)},
        )

    @property
    def device_info(self) -> DeviceInfo:
        return self._device_info

    async def _ensure_connected(self) -> BleakClient:
        """Connect (or return existing connection)."""
        if self._client and self._client.is_connected:
            return self._client

        ble_device = async_ble_device_from_address(self.hass, self.address)
        if not ble_device:
            raise BleakError(f"Device {self.address} not available")

        self._client = BleakClient(
            ble_device,
            timeout=CONNECT_TIMEOUT,
        )
        await self._client.connect()

        if self._notify_callback:
            await self._client.start_notify(
                CHARACTERISTIC_UUID, self._notify_callback
            )

        return self._client

    async def disconnect(self) -> None:
        """Disconnect from the device."""
        async with self._lock:
            if self._client and self._client.is_connected:
                try:
                    await self._client.stop_notify(CHARACTERISTIC_UUID)
                except Exception:
                    pass
                await self._client.disconnect()
            self._client = None

    async def async_write(self, data: bytes) -> None:
        """Write command to the device (Write Without Response)."""
        async with self._lock:
            try:
                client = await self._ensure_connected()
                await client.write_gatt_char(
                    CHARACTERISTIC_UUID, data, response=False
                )
                _LOGGER.debug("Wrote: %s", data.hex())
            except BleakError as err:
                _LOGGER.error("BLE write failed: %s", err)
                raise

    def set_notify_callback(self, callback) -> None:
        """Set notification callback."""
        self._notify_callback = callback
