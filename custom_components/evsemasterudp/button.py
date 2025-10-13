"""Boutons pour contrôle de charge EVSE"""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]
    client = data["client"]
    serial = data["serial"]
    base_name = data.get("base_name", f"EVSE {serial}")

    entities: list[ButtonEntity] = [
        EVSEStartChargeButton(coordinator, client, serial, base_name),
        EVSEStopChargeButton(coordinator, client, serial, base_name),
    ]
    async_add_entities(entities)


class EVSEBaseButton(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator, client, serial: str, base_name: str):
        super().__init__(coordinator)
        self.client = client
        self.serial = serial
        self.base_name = base_name
        self._attr_device_info = {
            "identifiers": {(DOMAIN, serial)},
            "name": base_name,
            "manufacturer": "Oniric75",
            "model": "EVSE Master UDP",
        }

    @property
    def evse_data(self):
        return self.coordinator.data.get(self.serial, {})

    @property
    def available(self) -> bool:
        data = self.evse_data
        return data.get("online", False) and data.get("logged_in", False)


class EVSEStartChargeButton(EVSEBaseButton):
    def __init__(self, coordinator, client, serial: str, base_name: str):
        super().__init__(coordinator, client, serial, base_name)
        self._attr_name = f"{base_name} Démarrer Charge"
        self._attr_unique_id = f"{serial}_start_charge"
        self._attr_icon = "mdi:play-circle"

    async def async_press(self) -> None:
        if await self.client.start_charging(self.serial, amps=None, single_phase=False):
            await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        # Hérite de base (online + logged_in) ET cooldown expiré
        if not super().available:
            return False
        remaining = self.client.get_cooldown_remaining(self.serial)
        return remaining.total_seconds() <= 0

    @property
    def extra_state_attributes(self):
        remaining = self.client.get_cooldown_remaining(self.serial)
        return {"cooldown_remaining_s": int(remaining.total_seconds())}


class EVSEStopChargeButton(EVSEBaseButton):
    def __init__(self, coordinator, client, serial: str, base_name: str):
        super().__init__(coordinator, client, serial, base_name)
        self._attr_name = f"{base_name} Arrêter Charge"
        self._attr_unique_id = f"{serial}_stop_charge"
        self._attr_icon = "mdi:stop-circle"

    async def async_press(self) -> None:
        if await self.client.stop_charging(self.serial):
            await self.coordinator.async_request_refresh()
