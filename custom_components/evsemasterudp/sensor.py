"""Capteurs pour l'intégration EVSE EmProto"""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfEnergy,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configurer les capteurs EVSE"""
    
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]
    serial = data["serial"]
    
    # Créer les capteurs
    entities = [
        EVSEStateSensor(coordinator, serial),
        EVSEPowerSensor(coordinator, serial),
        EVSECurrentSensor(coordinator, serial),
        EVSEVoltageSensor(coordinator, serial),
        EVSEEnergySensor(coordinator, serial),
        EVSETemperatureSensor(coordinator, serial, "inner"),
        EVSETemperatureSensor(coordinator, serial, "outer"),
    ]
    
    async_add_entities(entities)

class EVSEBaseSensor(CoordinatorEntity, SensorEntity):
    """Capteur de base pour EVSE"""
    
    def __init__(self, coordinator, serial: str):
        super().__init__(coordinator)
        self.serial = serial
        self._attr_device_info = {
            "identifiers": {(DOMAIN, serial)},
            "name": f"EVSE {serial}",
            "manufacturer": "Oniric75",
            "model": "EVSE Master UDP",
        }
    
    @property
    def evse_data(self):
        """Obtenir les données de l'EVSE"""
        return self.coordinator.data.get(self.serial, {})

class EVSEStateSensor(EVSEBaseSensor):
    """Capteur d'état de l'EVSE"""
    
    def __init__(self, coordinator, serial: str):
        super().__init__(coordinator, serial)
        self._attr_name = f"EVSE {serial} État"
        self._attr_unique_id = f"{serial}_state"
        self._attr_icon = "mdi:ev-station"
    
    @property
    def native_value(self) -> str | None:
        """Retourner l'état de l'EVSE"""
        data = self.evse_data
        if not data.get("online"):
            return "offline"
        return data.get("state", "unknown").lower()
    
    @property
    def extra_state_attributes(self):
        """Attributs supplémentaires"""
        data = self.evse_data
        return {
            "online": data.get("online", False),
            "logged_in": data.get("logged_in", False),
            "ip": data.get("ip"),
            "last_seen": data.get("last_seen"),
        }

class EVSEPowerSensor(EVSEBaseSensor):
    """Capteur de puissance de l'EVSE"""
    
    def __init__(self, coordinator, serial: str):
        super().__init__(coordinator, serial)
        self._attr_name = f"EVSE {serial} Puissance"
        self._attr_unique_id = f"{serial}_power"
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_icon = "mdi:flash"
    
    @property
    def native_value(self) -> float | None:
        """Retourner la puissance actuelle"""
        data = self.evse_data
        return data.get("current_power", 0)

class EVSECurrentSensor(EVSEBaseSensor):
    """Capteur de courant de l'EVSE"""
    
    def __init__(self, coordinator, serial: str):
        super().__init__(coordinator, serial)
        self._attr_name = f"EVSE {serial} Courant"
        self._attr_unique_id = f"{serial}_current"
        self._attr_device_class = SensorDeviceClass.CURRENT
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
        self._attr_icon = "mdi:current-ac"
    
    @property
    def native_value(self) -> float | None:
        """Retourner le courant actuel"""
        data = self.evse_data
        return data.get("current_l1", 0)

class EVSEVoltageSensor(EVSEBaseSensor):
    """Capteur de tension de l'EVSE"""
    
    def __init__(self, coordinator, serial: str):
        super().__init__(coordinator, serial)
        self._attr_name = f"EVSE {serial} Tension"
        self._attr_unique_id = f"{serial}_voltage"
        self._attr_device_class = SensorDeviceClass.VOLTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
        self._attr_icon = "mdi:sine-wave"
    
    @property
    def native_value(self) -> float | None:
        """Retourner la tension actuelle"""
        data = self.evse_data
        return data.get("voltage_l1", 0)

class EVSEEnergySensor(EVSEBaseSensor):
    """Capteur d'énergie de l'EVSE"""
    
    def __init__(self, coordinator, serial: str):
        super().__init__(coordinator, serial)
        self._attr_name = f"EVSE {serial} Énergie"
        self._attr_unique_id = f"{serial}_energy"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_icon = "mdi:counter"
    
    @property
    def native_value(self) -> float | None:
        """Retourner l'énergie consommée"""
        data = self.evse_data
        return data.get("charge_kwh", 0)

class EVSETemperatureSensor(EVSEBaseSensor):
    """Capteur de température de l'EVSE"""
    
    def __init__(self, coordinator, serial: str, temp_type: str):
        super().__init__(coordinator, serial)
        self.temp_type = temp_type
        self._attr_name = f"EVSE {serial} Température {temp_type.title()}"
        self._attr_unique_id = f"{serial}_temperature_{temp_type}"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_icon = "mdi:thermometer"
    
    @property
    def native_value(self) -> float | None:
        """Retourner la température"""
        data = self.evse_data
        return data.get(f"temperature_{self.temp_type}", 0)