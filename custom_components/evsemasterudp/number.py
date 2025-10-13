"""Contrôles numériques pour l'intégration EVSE EmProto"""
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
    """Configurer les contrôles numériques EVSE"""
    
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]
    client = data["client"]
    serial = data["serial"]
    base_name = data.get("base_name", f"EVSE {serial}")
    
    # Créer les contrôles numériques
    entities = [
        EVSECurrentControl(coordinator, client, serial, base_name),
        EVSEFastChangeProtection(coordinator, client, serial, base_name),
    ]
    
    async_add_entities(entities)

class EVSECurrentControl(CoordinatorEntity, NumberEntity):
    """Contrôle du courant maximum de l'EVSE"""
    
    def __init__(self, coordinator, client, serial: str, base_name: str):
        super().__init__(coordinator)
        self.client = client
        self.serial = serial
        self._attr_name = f"{base_name} Courant Max"
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
        """Obtenir les données de l'EVSE"""
        return self.coordinator.data.get(self.serial, {})
    
    @property
    def native_value(self) -> float | None:
        """Retourner la valeur actuelle du courant maximum configuré"""
        data = self.evse_data
        return data.get("configured_max_electricity", 6)
    
    @property
    def available(self) -> bool:
        """Retourner si le contrôle est disponible"""
        data = self.evse_data
        return data.get("online", False) and data.get("logged_in", False)
    
    async def async_set_native_value(self, value: float) -> None:
        """Définir le courant maximum"""
        success = await self.client.set_max_current(self.serial, int(value))
        if success:
            await self.coordinator.async_request_refresh()


class EVSEFastChangeProtection(CoordinatorEntity, NumberEntity):
    """Contrôle de protection contre les changements rapides"""
    
    def __init__(self, coordinator, client, serial: str, base_name: str):
        """Initialiser le contrôle de protection"""
        super().__init__(coordinator)
        self.client = client
        self.serial = serial
        self._attr_name = f"{base_name} Protection Changements Rapides"
        self._attr_unique_id = f"{serial}_fast_change_protection"
        self._attr_icon = "mdi:shield-alert"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 60
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = UnitOfTime.MINUTES
        self._attr_device_class = None

        # Stocker la valeur localement (pas liée aux données EVSE)
        # Valeur par défaut ajustée: 1 minute (au lieu de 5) pour répondre
        # à la demande de réduction du cooldown tout en évitant le spam.
        self._protection_minutes = 1  # Défaut: 1 minute
    
    @property
    def evse_data(self) -> dict:
        """Données de l'EVSE depuis le coordinateur"""
        return self.coordinator.data.get(self.serial, {})
    
    @property
    def native_value(self) -> float | None:
        """Retourner la valeur actuelle de protection (en minutes)"""
        return self._protection_minutes
    
    @property
    def available(self) -> bool:
        """Retourner si le contrôle est disponible"""
        data = self.evse_data
        return data.get("online", False)
    
    async def async_set_native_value(self, value: float) -> None:
        """Définir la protection (en minutes)"""
        self._protection_minutes = int(value)
        # Stocker dans le client pour utilisation par la logique de protection
        await self.client.set_fast_change_protection(self.serial, self._protection_minutes)
        # Pas besoin de refresh car c'est un paramètre local