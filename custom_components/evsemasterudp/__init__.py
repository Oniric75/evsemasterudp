"""
EVSE Master UDP integration for Home Assistant
Supports EVSE stations using the UDP EmProto protocol (Morec and compatibles)
"""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.components.persistent_notification import create

from .evse_client import get_evse_client, EVSEClient

_LOGGER = logging.getLogger(__name__)

DOMAIN = "evsemasterudp"
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON, Platform.NUMBER]

 # Update interval (in seconds)
UPDATE_INTERVAL = timedelta(seconds=60)

class EVSEDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to update EVSE data"""

    def __init__(self, hass: HomeAssistant, client: EVSEClient) -> None:
        """Initialize the coordinator"""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self):
        """Fetch EVSE data"""
        try:
            # Retrieve all EVSEs
            evses = self.client.get_all_evses()

            if not evses:
                _LOGGER.debug("No EVSE found during update")
                return {}

            _LOGGER.debug(f"EVSE data updated: {len(evses)} stations found")
            return evses
            
        except Exception as err:
            _LOGGER.warning(f"Error updating EVSE data: {err}")
            # Return previous data instead of raising exception
            return self.data if hasattr(self, 'data') and self.data else {}

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the EVSE integration from a config entry"""
    
    # Retrieve configuration parameters
    serial = entry.data.get("serial")
    password = entry.data.get("password")
    port = entry.data.get("port", 28376)

    _LOGGER.info(f"Configuring EVSE {serial} on port {port}")
    
    # Get the EVSE client
    client = get_evse_client()

    # Start the client if not already running
    if not client.running:
        try:
            await client.start()
        except Exception as err:
            _LOGGER.error(f"Unable to start EVSE client: {err}")
            return False
    
    # Wait a bit to discover EVSEs
    await asyncio.sleep(3)
    
    # Try to connect to the configured EVSE
    if serial and password:
        # Try login several times as the EVSE may not be immediately available
        for attempt in range(3):
            success = await client.login(serial, password)
            if success:
                _LOGGER.info(f"Successfully connected to EVSE {serial}")
                break
            else:
                _LOGGER.warning(f"Connection attempt {attempt + 1}/3 to EVSE {serial} failed")
                if attempt < 2:  # Wait before next attempt
                    await asyncio.sleep(2)
        else:
            _LOGGER.warning(f"Unable to connect to EVSE {serial} after 3 attempts")
    
    # Create the data coordinator
    coordinator = EVSEDataUpdateCoordinator(hass, client)

    # First data refresh
    await coordinator.async_config_entry_first_refresh()

    # Store the coordinator in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
        "serial": serial,
        "password": password,
        # Friendly base name for entity display
        "base_name": entry.data.get("name") or "EVSEMaster",
    }

    # Set up platforms (sensor, switch, number)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Notification recommending a restart after installation/update
    create(
        hass,
        f"EVSE Master UDP successfully configured for EVSE {serial}.\n\n"
        "It is recommended to restart Home Assistant for optimal operation.",
        title="EVSE Master UDP - Installation successful",
        notification_id=f"evsemasterudp_setup_{serial}"
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the EVSE integration"""
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Clean up data
        data = hass.data[DOMAIN].pop(entry.entry_id)

        # Stop the client if there are no other entries
        if not hass.data[DOMAIN]:
            client = data["client"]
            await client.stop()

    return unload_ok

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the EVSE integration"""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)