"""Config flow for the EVSE Master UDP integration"""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .evse_client import get_evse_client

_LOGGER = logging.getLogger(__name__)

DOMAIN = "evsemasterudp"

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("serial"): str,
        vol.Required("password"): str,
        vol.Optional("port", default=28376): int,
    # Default friendly base name (avoids huge serial in entity names)
    vol.Optional("name", default="EVSEMaster"): str,
    }
)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configuration flow manager for EVSE EmProto"""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial user configuration step"""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate configuration
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error")
                errors["base"] = "unknown"
            else:
                # Create the configuration entry
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate user input data"""
    
    serial = data["serial"]
    password = data["password"]
    port = data.get("port", 28376)
    
    # Get the EVSE client
    client = get_evse_client()
    
    # Start the client temporarily for testing
    was_running = client.running
    if not was_running:
        try:
            await client.start()
        except Exception as err:
            _LOGGER.error(f"Unable to start EVSE client: {err}")
            raise CannotConnect
    
    try:
    # Wait longer to discover EVSEs (like test_full.py)
        import asyncio
        await asyncio.sleep(5)
        
    # Check if EVSE is found - Retry on failure
        evse = client.get_evse(serial)
        if not evse:
            # Retry after 2 additional seconds
            _LOGGER.warning(f"EVSE {serial} not found, retrying...")
            await asyncio.sleep(2)
            evse = client.get_evse(serial)
            
        if not evse:
            _LOGGER.error(f"EVSE {serial} not found after 7 seconds")
            raise CannotConnect
        
        _LOGGER.info(f"EVSE {serial} found, attempting connection...")
        
    # Test connection with retry
        success = await client.login(serial, password)
        if not success:
            # Only one retry to avoid blocking the EVSE
            _LOGGER.warning(f"First auth attempt failed for {serial}, retrying...")
            await asyncio.sleep(2)
            success = await client.login(serial, password)
            
        if not success:
            raise InvalidAuth
        
        _LOGGER.info(f"Successfully connected to EVSE {serial}")
        
        return {
            "title": f"EVSE {serial}",
            "serial": serial,
        }
        
    finally:
    # Stop the client if it was not started before
        if not was_running:
            await client.stop()

class CannotConnect(HomeAssistantError):
    """Error indicating that connection could not be established"""

class InvalidAuth(HomeAssistantError):
    """Error indicating invalid authentication"""