"""BTF Lighting Devil Eyes integration."""

from __future__ import annotations

import asyncio
import logging

from bleak import BleakClient, BleakError

from homeassistant.components.bluetooth import (
    async_ble_device_from_address,
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
)

PLATFORMS = ["light", "select"]

_LOGGER = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 3.0


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
        self._reconnect_task: asyncio.Task | None = None
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

    async def _ensure_connected(self) -> BleakClient | None:
        """Connect (or return existing connection) with auto-retry."""
        if self._client and self._client.is_connected:
            return self._client

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                ble_device = async_ble_device_from_address(
                    self.hass, self.address
                )
                if not ble_device:
                    _LOGGER.warning(
                        "Device %s not found (attempt %d/%d)",
                        self.address, attempt, MAX_RETRIES,
                    )
                    await asyncio.sleep(RETRY_DELAY)
                    continue

                self._client = BleakClient(
                    ble_device,
                    timeout=CONNECT_TIMEOUT,
                )
                await self._client.connect()

                if self._notify_callback:
                    await self._client.start_notify(
                        CHARACTERISTIC_UUID, self._notify_callback
                    )

                _LOGGER.info("Connected to %s", self.address)
                return self._client

            except BleakError as err:
                _LOGGER.warning(
                    "BLE connect failed (attempt %d/%d): %s",
                    attempt, MAX_RETRIES, err,
                )
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY)

        _LOGGER.error(
            "Could not connect to %s after %d attempts",
            self.address, MAX_RETRIES,
        )
        return None

    async def disconnect(self) -> None:
        """Disconnect from the device."""
        async with self._lock:
            if self._reconnect_task and not self._reconnect_task.done():
                self._reconnect_task.cancel()
                self._reconnect_task = None
            await self._close_client()

    async def _close_client(self) -> None:
        """Close the current client connection."""
        if self._client and self._client.is_connected:
            try:
                await self._client.stop_notify(CHARACTERISTIC_UUID)
            except Exception:
                pass
            try:
                await self._client.disconnect()
            except Exception:
                pass
        self._client = None

    async def async_write(self, data: bytes) -> bool:
        """Write command to the device (Write Without Response).
        Returns True on success, False on failure.
        """
        async with self._lock:
            try:
                client = await self._ensure_connected()
                if not client:
                    _LOGGER.error(
                        "Cannot write %s — not connected",
                        data.hex(),
                    )
                    return False

                await client.write_gatt_char(
                    CHARACTERISTIC_UUID, data, response=False
                )
                _LOGGER.debug("Wrote: %s", data.hex())
                return True

            except BleakError as err:
                _LOGGER.error("BLE write failed: %s", err)
                # Reset client state so next write retries connect
                await self._close_client()
                return False

    def set_notify_callback(self, callback) -> None:
        """Set notification callback."""
        self._notify_callback = callback
