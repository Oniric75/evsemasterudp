"""Interrupteurs pour l'intégration EVSE EmProto"""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configurer les interrupteurs EVSE"""
    
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]
    client = data["client"]
    serial = data["serial"]
    base_name = data.get("base_name", f"EVSE {serial}")
    
    # Créer l'interrupteur de charge
    entities = [
        EVSEChargingSwitch(coordinator, client, serial, base_name),
    ]
    
    async_add_entities(entities)

class EVSEChargingSwitch(CoordinatorEntity, SwitchEntity):
    """Interrupteur pour démarrer/arrêter la charge"""
    
    def __init__(self, coordinator, client, serial: str, base_name: str):
        super().__init__(coordinator)
        self.client = client
        self.serial = serial
        self._attr_name = f"{base_name} Charge"
        self._attr_unique_id = f"{serial}_charging"
        self._attr_icon = "mdi:power"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, serial)},
            "name": base_name,
            "manufacturer": "Oniric75",
            "model": "EVSE Master UDP",
        }
    
    @property
    def evse_data(self):
        """Obtenir les données de l'EVSE"""
        return self.coordinator.data.get(self.serial, {})
    
    @property
    def is_on(self) -> bool | None:
        """Retourner si la charge est active"""
        data = self.evse_data
        return data.get("state") == "CHARGING"
    
    @property
    def available(self) -> bool:
        """Retourner si l'interrupteur est disponible"""
        data = self.evse_data
        return data.get("online", False) and data.get("logged_in", False)
    
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Démarrer la charge"""
        # Utiliser la logique de protection intégrée dans le client
        # (Fallback 16A au lieu de 32A si max_electricity pas encore lu)
        success = await self.client.start_charging(self.serial, amps=None, single_phase=False)
        if success:
            await self.coordinator.async_request_refresh()
    
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Arrêter la charge"""
        success = await self.client.stop_charging(self.serial)
        if success:
            await self.coordinator.async_request_refresh()