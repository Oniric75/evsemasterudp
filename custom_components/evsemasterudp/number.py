"""Numeric controls for the EVSE EmProto integration"""
from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricCurrent, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EVSE numeric controls"""
    
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]
    client = data["client"]
    serial = data["serial"]
    base_name = data.get("base_name", f"EVSE {serial}")
    
    # Create numeric controls
    entities = [
        EVSECurrentControl(coordinator, client, serial, base_name),
        EVSEFastChangeProtection(coordinator, client, serial, base_name),
    ]
    
    async_add_entities(entities)

class EVSECurrentControl(CoordinatorEntity, NumberEntity):
    """Control for EVSE maximum current"""
    
    def __init__(self, coordinator, client, serial: str, base_name: str):
        super().__init__(coordinator)
        self.client = client
        self.serial = serial
        self._attr_name = f"{base_name} Max Current"
        self._attr_unique_id = f"{serial}_max_current"
        self._attr_icon = "mdi:current-ac"
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
        self._attr_native_min_value = 6
        self._attr_native_max_value = 32
        self._attr_native_step = 1

        self._attr_device_info = {
            "identifiers": {(DOMAIN, serial)},
            "name": base_name,
            "manufacturer": "Oniric75",
            "model": "EVSE Master UDP",
        }
    
    @property
    def evse_data(self):
        """Get EVSE data"""
        return self.coordinator.data.get(self.serial, {})
    
    @property
    def native_value(self) -> float | None:
        """Return the current configured maximum current value"""
        data = self.evse_data
        return data.get("configured_max_electricity", 6)
    
    @property
    def available(self) -> bool:
        """Return whether the control is available"""
        data = self.evse_data
        return data.get("online", False) and data.get("logged_in", False)
    
    async def async_set_native_value(self, value: float) -> None:
        """Set the maximum current"""
        success = await self.client.set_max_current(self.serial, int(value))
        if success:
            await self.coordinator.async_request_refresh()


class EVSEFastChangeProtection(CoordinatorEntity, NumberEntity):
    """Control for fast change protection"""
    
    def __init__(self, coordinator, client, serial: str, base_name: str):
        """Initialize the protection control"""
        super().__init__(coordinator)
        self.client = client
        self.serial = serial
        self._attr_name = f"{base_name} Fast Change Protection"
        self._attr_unique_id = f"{serial}_fast_change_protection"
        self._attr_icon = "mdi:shield-alert"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 60
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = UnitOfTime.MINUTES
        self._attr_device_class = None

        # Store the value locally (not linked to EVSE data)
        # Default value adjusted: 1 minute (instead of 5) to meet
        # the request to reduce cooldown while avoiding spam.
        self._protection_minutes = 1  # Default: 1 minute
    
    @property
    def evse_data(self) -> dict:
        """EVSE data from the coordinator"""
        return self.coordinator.data.get(self.serial, {})
    
    @property
    def native_value(self) -> float | None:
        """Return the current protection value (in minutes)"""
        return self._protection_minutes
    
    @property
    def available(self) -> bool:
        """Return whether the control is available"""
        data = self.evse_data
        return data.get("online", False)
    
    async def async_set_native_value(self, value: float) -> None:
        """Set the protection (in minutes)"""
        self._protection_minutes = int(value)
        # Stocker dans le client pour utilisation par la logique de protection
        await self.client.set_fast_change_protection(self.serial, self._protection_minutes)
        # Pas besoin de refresh car c'est un paramètre local